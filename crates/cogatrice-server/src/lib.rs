mod config;
mod decks;
mod translate;
mod uri;
pub mod wire;

use anyhow::{anyhow, Context, Result};
use axum::extract::ws::{close_code, CloseFrame, Message, WebSocket, WebSocketUpgrade};
use axum::extract::{Path as AxumPath, Query, State};
use axum::http::{header, StatusCode};
use axum::response::{Html, IntoResponse, Response};
use axum::routing::get;
use axum::Router;
use config::EpisodeConfig;
use decks::load_deck;
use futures::{FutureExt, Sink, SinkExt, StreamExt};
use std::collections::BTreeMap;
use std::future::{Future, IntoFuture};
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use tabletop_core::{
    Action, CardRef, DeckList, Event, Expectation, Game, GameOutcome, GameSetup, LoggedEvent,
    Perspective, PlayerSetup, SeatId, Seq,
};
use tokio::net::TcpListener;
use tokio::sync::{mpsc, oneshot};
use tokio::time::{sleep, Duration, Instant};
use wire::{
    action_error_kind, reject_error, GameSummary, GlobalFrame, MatchState, PlayerCommand,
    PlayerFrame, Replay, ReplayEvent, ReplayFrame, ReplayGame, ReplayGameSummary, Results,
};

#[derive(Clone)]
struct AppState {
    config: Arc<EpisodeConfig>,
    cmd_tx: mpsc::UnboundedSender<ServerCommand>,
    next_conn_id: Arc<AtomicU64>,
}

#[derive(Clone)]
struct ReplayState {
    replay: Arc<Replay>,
}

#[derive(Debug)]
enum SocketOut {
    Text(String),
    Close,
}

#[derive(Debug)]
enum ServerCommand {
    PlayerConnected {
        slot: usize,
        id: u64,
        tx: mpsc::UnboundedSender<SocketOut>,
    },
    PlayerMessage {
        slot: usize,
        id: u64,
        text: String,
    },
    PlayerDisconnected {
        slot: usize,
        id: u64,
    },
    GlobalConnected {
        id: u64,
        tx: mpsc::UnboundedSender<SocketOut>,
    },
    GlobalDisconnected {
        id: u64,
    },
    Ignore,
}

#[derive(Clone)]
struct Connection {
    id: u64,
    tx: mpsc::UnboundedSender<SocketOut>,
}

#[derive(Clone)]
struct CurrentContext<'a> {
    game: &'a Game,
    game_number: u32,
    slot_of_seat0: usize,
    clocks_ms: [u64; 2],
}

#[derive(Clone, Copy)]
struct LiveParams {
    game_number: u32,
    slot_of_seat0: usize,
    clocks_ms: [u64; 2],
    started: Instant,
}

struct LiveGame<'a> {
    game: &'a mut Game,
    replay_events: &'a mut Vec<ReplayEvent>,
    params: LiveParams,
}

pub async fn run() -> Result<()> {
    run_until_shutdown(std::future::pending::<()>()).await
}

pub async fn run_until_shutdown(shutdown: impl Future<Output = ()> + Send + 'static) -> Result<()> {
    tracing_subscriber::fmt::try_init().ok();
    if let Some(replay_uri) = config::load_replay_uri() {
        return run_replay_server(replay_uri, shutdown).await;
    }
    run_match_server(shutdown).await
}

async fn run_match_server(shutdown: impl Future<Output = ()> + Send + 'static) -> Result<()> {
    let config = Arc::new(EpisodeConfig::from_env().await?);
    let decks = Arc::new([
        load_deck(&config.decks[0]).context("failed to load slot 0 deck")?,
        load_deck(&config.decks[1]).context("failed to load slot 1 deck")?,
    ]);
    let (host, port) = config::host_port_from_env();
    let listener = TcpListener::bind(format!("{host}:{port}")).await?;
    let (cmd_tx, cmd_rx) = mpsc::unbounded_channel();
    let state = AppState {
        config: config.clone(),
        cmd_tx,
        next_conn_id: Arc::new(AtomicU64::new(1)),
    };
    let app = Router::new()
        .route("/healthz", get(healthz))
        .route("/client/{*path}", get(client_asset))
        .route("/player", get(player_ws))
        .route("/global", get(global_ws))
        .with_state(state);
    let (stop_tx, stop_rx) = oneshot::channel::<()>();
    let server = axum::serve(listener, app).with_graceful_shutdown(async {
        stop_rx.await.ok();
    });
    let server_task = tokio::spawn(server.into_future());
    let mut runner = MatchRunner::new(config, decks, cmd_rx);
    let mut match_task = tokio::spawn(async move { runner.run().await });

    let result = tokio::select! {
        value = &mut match_task => value.context("match task panicked")?,
        _ = shutdown => {
            match_task.abort();
            Ok(())
        },
    };
    stop_tx.send(()).ok();
    server_task
        .await
        .context("server task panicked")?
        .context("server failed")?;
    result
}

async fn run_replay_server(
    replay_uri: String,
    shutdown: impl Future<Output = ()> + Send + 'static,
) -> Result<()> {
    let text = uri::read_to_string(&replay_uri).await?;
    let replay = Arc::new(serde_json::from_str::<Replay>(&text)?);
    let (host, port) = config::host_port_from_env();
    let listener = TcpListener::bind(format!("{host}:{port}")).await?;
    let app = Router::new()
        .route("/healthz", get(healthz))
        .route("/client/{*path}", get(client_asset))
        .route("/replay", get(replay_ws))
        .with_state(ReplayState { replay });
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown)
        .into_future()
        .await?;
    Ok(())
}

async fn healthz() -> &'static str {
    "ok"
}

async fn client_asset(
    AxumPath(path): AxumPath<String>,
    Query(params): Query<BTreeMap<String, String>>,
) -> Response {
    let dist = web_dist_dir();
    if dist.is_dir() {
        return match resolve_client_asset(&dist, &path) {
            Some(file) => match tokio::fs::read(&file).await {
                Ok(bytes) => ([(header::CONTENT_TYPE, content_type(&file))], bytes).into_response(),
                Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                    (StatusCode::NOT_FOUND, "not found").into_response()
                }
                Err(_) => {
                    (StatusCode::INTERNAL_SERVER_ERROR, "failed to read asset").into_response()
                }
            },
            None => (StatusCode::NOT_FOUND, "not found").into_response(),
        };
    }
    if matches!(path.as_str(), "player" | "global" | "replay") {
        return client_placeholder(params).into_response();
    }
    (StatusCode::NOT_FOUND, "not found").into_response()
}

fn client_placeholder(params: BTreeMap<String, String>) -> Html<String> {
    let body = serde_json::to_string_pretty(&params).unwrap_or_else(|_| "{}".to_owned());
    Html(format!(
        "<!doctype html><html><body><pre>{}</pre></body></html>",
        escape_html(&body)
    ))
}

fn web_dist_dir() -> PathBuf {
    std::env::var_os("COGAME_WEB_DIST")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("web/dist"))
}

fn resolve_client_asset(dist: &Path, path: &str) -> Option<PathBuf> {
    let relative = match path {
        "player" | "global" | "replay" => PathBuf::from(format!("{path}.html")),
        _ => safe_relative_path(path)?,
    };
    Some(dist.join(relative))
}

fn safe_relative_path(path: &str) -> Option<PathBuf> {
    let mut out = PathBuf::new();
    for component in Path::new(path).components() {
        match component {
            Component::Normal(part) => out.push(part),
            _ => return None,
        }
    }
    if out.as_os_str().is_empty() {
        None
    } else {
        Some(out)
    }
}

fn content_type(path: &Path) -> &'static str {
    match path.extension().and_then(|extension| extension.to_str()) {
        Some("html") => "text/html; charset=utf-8",
        Some("js") => "text/javascript; charset=utf-8",
        Some("css") => "text/css; charset=utf-8",
        Some("json") => "application/json; charset=utf-8",
        Some("svg") => "image/svg+xml",
        Some("png") => "image/png",
        Some("ico") => "image/x-icon",
        Some("map") => "application/json; charset=utf-8",
        _ => "application/octet-stream",
    }
}

async fn player_ws(
    State(state): State<AppState>,
    Query(params): Query<BTreeMap<String, String>>,
    ws: WebSocketUpgrade,
) -> impl IntoResponse {
    let slot = params.get("slot").and_then(|value| value.parse::<usize>().ok());
    let token = params.get("token").cloned().unwrap_or_default();
    match slot {
        Some(slot) if slot < 2 && token == state.config.tokens[slot] => {
            ws.on_upgrade(move |socket| player_socket(socket, state, slot))
        }
        _ => ws.on_upgrade(policy_violation),
    }
}

async fn global_ws(State(state): State<AppState>, ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(move |socket| global_socket(socket, state))
}

async fn replay_ws(State(state): State<ReplayState>, ws: WebSocketUpgrade) -> impl IntoResponse {
    ws.on_upgrade(move |socket| replay_socket(socket, state))
}

async fn policy_violation(mut socket: WebSocket) {
    socket
        .send(Message::Close(Some(CloseFrame {
            code: close_code::POLICY,
            reason: "policy violation".into(),
        })))
        .await
        .ok();
}

async fn player_socket(socket: WebSocket, state: AppState, slot: usize) {
    let id = state.next_conn_id.fetch_add(1, Ordering::Relaxed);
    let (tx, rx) = mpsc::unbounded_channel();
    state
        .cmd_tx
        .send(ServerCommand::PlayerConnected { slot, id, tx })
        .ok();
    socket_loop(
        socket,
        rx,
        state.cmd_tx.clone(),
        move |text| ServerCommand::PlayerMessage { slot, id, text },
        ServerCommand::PlayerDisconnected { slot, id },
    )
    .await;
}

async fn global_socket(socket: WebSocket, state: AppState) {
    let id = state.next_conn_id.fetch_add(1, Ordering::Relaxed);
    let (tx, rx) = mpsc::unbounded_channel();
    state
        .cmd_tx
        .send(ServerCommand::GlobalConnected { id, tx })
        .ok();
    socket_loop(
        socket,
        rx,
        state.cmd_tx.clone(),
        |_| ServerCommand::Ignore,
        ServerCommand::GlobalDisconnected { id },
    )
    .await;
}

async fn socket_loop(
    socket: WebSocket,
    mut rx: mpsc::UnboundedReceiver<SocketOut>,
    cmd_tx: mpsc::UnboundedSender<ServerCommand>,
    text_command: impl Fn(String) -> ServerCommand,
    disconnect_command: ServerCommand,
) {
    let (mut sender, mut receiver) = socket.split();
    loop {
        tokio::select! {
            outgoing = rx.recv() => {
                match outgoing {
                    Some(SocketOut::Text(text)) => {
                        if sender.send(Message::Text(text.into())).await.is_err() {
                            break;
                        }
                    }
                    Some(SocketOut::Close) => {
                        sender.send(Message::Close(Some(CloseFrame {
                            code: close_code::NORMAL,
                            reason: "replaced".into(),
                        }))).await.ok();
                        break;
                    }
                    None => break,
                }
            }
            incoming = receiver.next() => {
                match incoming {
                    Some(Ok(Message::Text(text))) => {
                        cmd_tx.send(text_command(text.to_string())).ok();
                    }
                    Some(Ok(Message::Close(_))) | None => break,
                    Some(Ok(_)) => {}
                    Some(Err(_)) => break,
                }
            }
        }
    }
    cmd_tx.send(disconnect_command).ok();
}

async fn replay_socket(socket: WebSocket, state: ReplayState) {
    let (mut sender, mut receiver) = socket.split();
    let replay = state.replay;
    let summaries: Vec<_> = replay
        .games
        .iter()
        .map(|game| ReplayGameSummary {
            game_number: game.game_number,
            slot_of_seat0: game.slot_of_seat0,
            events: game.events.len(),
        })
        .collect();
    let meta = ReplayFrame::ReplayMeta {
        config: Box::new(replay.config.clone()),
        results: Box::new(replay.results.clone()),
        games: summaries,
    };
    if send_ws_json(&mut sender, &meta).await.is_err() {
        return;
    }
    loop {
        for game in &replay.games {
            for chunk in game.events.chunks(10) {
                let frame = ReplayFrame::Events {
                    game_number: game.game_number,
                    events: chunk.iter().map(|event| event.event.clone()).collect(),
                };
                if send_ws_json(&mut sender, &frame).await.is_err() {
                    return;
                }
                sleep(Duration::from_millis(100)).await;
            }
            let Some(outcome) = game.events.iter().rev().find_map(|event| match &event.event.event {
                Event::GameEnded { outcome } => Some(outcome.clone()),
                _ => None,
            }) else {
                continue;
            };
            let frame = ReplayFrame::GameEnd {
                game_number: game.game_number,
                outcome,
                wins: replay.results.scores,
            };
            if send_ws_json(&mut sender, &frame).await.is_err() {
                return;
            }
        }
        let frame = ReplayFrame::MatchEnd {
            scores: replay.results.scores,
            games: replay.results.games.clone(),
        };
        if send_ws_json(&mut sender, &frame).await.is_err() {
            return;
        }
        if matches!(receiver.next().now_or_never(), Some(Some(Ok(Message::Close(_)))) | Some(None)) {
            return;
        }
    }
}

async fn send_ws_json<S, T>(sender: &mut S, value: &T) -> Result<()>
where
    S: Sink<Message> + Unpin,
    T: serde::Serialize,
    S::Error: std::error::Error + Send + Sync + 'static,
{
    sender
        .send(Message::Text(serde_json::to_string(value)?.into()))
        .await?;
    Ok(())
}

struct MatchRunner {
    config: Arc<EpisodeConfig>,
    decks: Arc<[DeckList; 2]>,
    cmd_rx: mpsc::UnboundedReceiver<ServerCommand>,
    players: [Option<Connection>; 2],
    globals: BTreeMap<u64, Connection>,
    wins: [f64; 2],
    summaries: Vec<GameSummary>,
    replay_games: Vec<ReplayGame>,
}

impl MatchRunner {
    fn new(
        config: Arc<EpisodeConfig>,
        decks: Arc<[DeckList; 2]>,
        cmd_rx: mpsc::UnboundedReceiver<ServerCommand>,
    ) -> Self {
        Self {
            config,
            decks,
            cmd_rx,
            players: [None, None],
            globals: BTreeMap::new(),
            wins: [0.0, 0.0],
            summaries: Vec::new(),
            replay_games: Vec::new(),
        }
    }

    async fn run(&mut self) -> Result<()> {
        self.wait_for_players().await;
        if !self.both_players_connected() {
            self.finish_connect_timeout().await?;
            return Ok(());
        }
        let max_games = self.max_games();
        for game_index in 0..max_games {
            let game_number = game_index + 1;
            self.play_game(game_number).await?;
            if self.match_is_over(game_number) {
                break;
            }
        }
        self.finish_match().await
    }

    async fn wait_for_players(&mut self) {
        let timeout = seconds_duration(self.config.player_connect_timeout_s);
        let timer = sleep(timeout);
        tokio::pin!(timer);
        while !self.both_players_connected() {
            tokio::select! {
                _ = &mut timer => break,
                command = self.cmd_rx.recv() => {
                    let Some(command) = command else {
                        break;
                    };
                    self.handle_command(command, None);
                }
            }
        }
    }

    async fn finish_connect_timeout(&mut self) -> Result<()> {
        if self.players[0].is_some() && self.players[1].is_none() {
            self.wins[0] = f64::from(self.config.games_to_win);
        } else if self.players[1].is_some() && self.players[0].is_none() {
            self.wins[1] = f64::from(self.config.games_to_win);
        }
        self.finish_match().await
    }

    async fn play_game(&mut self, game_number: u32) -> Result<()> {
        let slot_of_seat0 = ((game_number - 1) % 2) as usize;
        let seed = self.config.seed + u64::from(game_number - 1);
        let (mut game, initial_events) = Game::new(self.game_setup(seed, slot_of_seat0));
        let mut clocks_ms = [duration_ms(self.config.clock_s), duration_ms(self.config.clock_s)];
        let mut replay_events = Vec::new();
        let started = Instant::now();
        self.send_game_start(&game, &initial_events, game_number, slot_of_seat0, clocks_ms);
        self.record_events(
            &mut replay_events,
            &initial_events,
            started,
            slot_of_seat0,
        );

        while game.outcome().is_none() {
            let expected_seat = expected_seat(game.expectation())
                .ok_or_else(|| anyhow!("game missing expected actor"))?;
            let expected_slot = translate::seat_to_slot(expected_seat, slot_of_seat0);
            let start = Instant::now();
            let wait_ms = clocks_ms[expected_slot].min(duration_ms(self.config.decision_cap_s));
            tokio::select! {
                _ = sleep(Duration::from_millis(wait_ms)) => {
                    subtract_elapsed(&mut clocks_ms[expected_slot], start.elapsed());
                    if clocks_ms[expected_slot] == 0 {
                        let first = game.log().len();
                        game.system_say(expected_seat, "clock expired".to_owned());
                        game.flag(expected_seat);
                        let events = game.log()[first..].to_vec();
                        self.record_events(&mut replay_events, &events, started, slot_of_seat0);
                        self.broadcast_events(game_number, &events, slot_of_seat0);
                        break;
                    }
                    let events = apply_default(&mut game, expected_seat);
                    self.record_events(&mut replay_events, &events, started, slot_of_seat0);
                    self.broadcast_events(game_number, &events, slot_of_seat0);
                    self.send_window_if_opened(&game, &events, game_number, slot_of_seat0, clocks_ms);
                }
                command = self.cmd_rx.recv() => {
                    subtract_elapsed(&mut clocks_ms[expected_slot], start.elapsed());
                    let Some(command) = command else {
                        break;
                    };
                    let params = LiveParams {
                        game_number,
                        slot_of_seat0,
                        clocks_ms,
                        started,
                    };
                    let mut live = LiveGame {
                        game: &mut game,
                        replay_events: &mut replay_events,
                        params,
                    };
                    self.handle_live_command(command, &mut live);
                }
            }
        }

        let outcome = game
            .outcome()
            .cloned()
            .ok_or_else(|| anyhow!("game ended without an outcome"))?;
        let summary = self.game_summary(game_number, seed, &outcome, slot_of_seat0);
        self.apply_game_score(&summary);
        self.broadcast_game_end(game_number, outcome, slot_of_seat0);
        self.summaries.push(summary);
        self.replay_games.push(ReplayGame {
            game_number,
            slot_of_seat0,
            events: replay_events,
        });
        Ok(())
    }

    fn handle_live_command(
        &mut self,
        command: ServerCommand,
        live: &mut LiveGame<'_>,
    ) {
        match command {
            ServerCommand::PlayerMessage { slot, id, text } => {
                if !self.player_id_matches(slot, id) {
                    return;
                }
                self.handle_player_text(slot, text, live);
            }
            other => {
                let current = CurrentContext {
                    game: live.game,
                    game_number: live.params.game_number,
                    slot_of_seat0: live.params.slot_of_seat0,
                    clocks_ms: live.params.clocks_ms,
                };
                self.handle_command(other, Some(current));
            }
        }
    }

    fn handle_player_text(&mut self, slot: usize, text: String, live: &mut LiveGame<'_>) {
        let cmd_id = command_id(&text);
        let command = match serde_json::from_str::<PlayerCommand>(&text) {
            Ok(command) => command,
            Err(error) => {
                self.send_reject(slot, cmd_id, "bad_request", error.to_string());
                return;
            }
        };
        let Some(expected_seat) = expected_seat(live.game.expectation()) else {
            self.send_reject(slot, command.cmd_id, "game_is_over", "game is over");
            return;
        };
        let expected_slot = translate::seat_to_slot(expected_seat, live.params.slot_of_seat0);
        if slot != expected_slot {
            self.send_reject(
                slot,
                command.cmd_id,
                "not_your_window",
                "that slot does not hold the current window",
            );
            return;
        }
        let action = translate::action_to_core(command.action, live.params.slot_of_seat0);
        let first = live.game.log().len();
        match live.game.submit(expected_seat, action) {
            Ok(events) => {
                let seq = events
                    .first()
                    .map(|event| event.seq)
                    .unwrap_or_else(|| Seq(live.game.snapshot(Perspective::Full).seq.0 + 1));
                self.record_events(
                    live.replay_events,
                    &events,
                    live.params.started,
                    live.params.slot_of_seat0,
                );
                self.broadcast_events(
                    live.params.game_number,
                    &events,
                    live.params.slot_of_seat0,
                );
                self.send_ack(slot, command.cmd_id, seq);
                self.send_window_if_opened(
                    live.game,
                    &events,
                    live.params.game_number,
                    live.params.slot_of_seat0,
                    live.params.clocks_ms,
                );
            }
            Err(error) => {
                let detail = error.to_string();
                let kind = action_error_kind(&error);
                self.send_reject(slot, command.cmd_id, kind, detail);
                debug_assert_eq!(first, live.game.log().len());
            }
        }
    }

    fn handle_command(&mut self, command: ServerCommand, current: Option<CurrentContext<'_>>) {
        match command {
            ServerCommand::PlayerConnected { slot, id, tx } => {
                if let Some(old) = self.players[slot].replace(Connection { id, tx }) {
                    old.tx.send(SocketOut::Close).ok();
                }
                self.send_hello(slot, current.as_ref());
                if let Some(current) = current {
                    self.send_snapshot_to_slot(slot, &current);
                    self.send_window_to_slot_if_current(slot, &current);
                }
            }
            ServerCommand::PlayerDisconnected { slot, id } => {
                if self.player_id_matches(slot, id) {
                    self.players[slot] = None;
                }
            }
            ServerCommand::GlobalConnected { id, tx } => {
                self.globals.insert(id, Connection { id, tx });
                self.send_global_hello(id, current.as_ref());
                if let Some(current) = current {
                    self.send_snapshot_to_global(id, &current);
                    self.send_window_to_global_if_current(id, &current);
                }
            }
            ServerCommand::GlobalDisconnected { id } => {
                self.globals.remove(&id);
            }
            ServerCommand::PlayerMessage { slot, text, .. } => {
                self.send_reject(slot, command_id(&text), "not_your_window", "match has not started");
            }
            ServerCommand::Ignore => {}
        }
    }

    fn send_game_start(
        &self,
        game: &Game,
        events: &[LoggedEvent],
        game_number: u32,
        slot_of_seat0: usize,
        clocks_ms: [u64; 2],
    ) {
        for slot in 0..2 {
            if self.players[slot].is_some() {
                self.send_hello(
                    slot,
                    Some(&CurrentContext {
                        game,
                        game_number,
                        slot_of_seat0,
                        clocks_ms,
                    }),
                );
                let current = CurrentContext {
                    game,
                    game_number,
                    slot_of_seat0,
                    clocks_ms,
                };
                self.send_snapshot_to_slot(slot, &current);
            }
        }
        for id in self.globals.keys().copied().collect::<Vec<_>>() {
            let current = CurrentContext {
                game,
                game_number,
                slot_of_seat0,
                clocks_ms,
            };
            self.send_global_hello(id, Some(&current));
            self.send_snapshot_to_global(id, &current);
        }
        self.broadcast_events(game_number, events, slot_of_seat0);
        let current = CurrentContext {
            game,
            game_number,
            slot_of_seat0,
            clocks_ms,
        };
        for slot in 0..2 {
            self.send_window_to_slot_if_current(slot, &current);
        }
        for id in self.globals.keys().copied().collect::<Vec<_>>() {
            self.send_window_to_global_if_current(id, &current);
        }
    }

    fn broadcast_events(&self, game_number: u32, events: &[LoggedEvent], slot_of_seat0: usize) {
        for slot in 0..2 {
            let Some(connection) = &self.players[slot] else {
                continue;
            };
            let redacted = redact_events(events, translate::perspective_for_slot(slot, slot_of_seat0));
            let frame = PlayerFrame::Events {
                game_number,
                events: translate::events_to_slots(redacted, slot_of_seat0),
            };
            send_json(&connection.tx, &frame);
        }
        let redacted = redact_events(events, Perspective::Global);
        let events = translate::events_to_slots(redacted, slot_of_seat0);
        for connection in self.globals.values() {
            let frame = GlobalFrame::Events {
                game_number,
                events: events.clone(),
            };
            send_json(&connection.tx, &frame);
        }
    }

    fn send_window_if_opened(
        &self,
        game: &Game,
        events: &[LoggedEvent],
        game_number: u32,
        slot_of_seat0: usize,
        clocks_ms: [u64; 2],
    ) {
        if !events
            .iter()
            .any(|event| matches!(event.event, Event::WindowOpened { .. }))
        {
            return;
        }
        let current = CurrentContext {
            game,
            game_number,
            slot_of_seat0,
            clocks_ms,
        };
        for slot in 0..2 {
            self.send_window_to_slot_if_current(slot, &current);
        }
        for id in self.globals.keys().copied().collect::<Vec<_>>() {
            self.send_window_to_global_if_current(id, &current);
        }
    }

    fn send_hello(&self, slot: usize, current: Option<&CurrentContext<'_>>) {
        let Some(connection) = &self.players[slot] else {
            return;
        };
        let frame = PlayerFrame::Hello {
            slot,
            seat_name: self.config.players[slot].name.clone(),
            r#match: self.match_state(current.map(|ctx| ctx.game_number).unwrap_or(1)),
            config: self.config.public(),
            decklist: self.decks[slot].clone(),
        };
        send_json(&connection.tx, &frame);
    }

    fn send_global_hello(&self, id: u64, current: Option<&CurrentContext<'_>>) {
        let Some(connection) = self.globals.get(&id) else {
            return;
        };
        let frame = GlobalFrame::Hello {
            r#match: self.match_state(current.map(|ctx| ctx.game_number).unwrap_or(1)),
            config: self.config.public(),
        };
        send_json(&connection.tx, &frame);
    }

    fn send_snapshot_to_slot(&self, slot: usize, current: &CurrentContext<'_>) {
        let Some(connection) = &self.players[slot] else {
            return;
        };
        let perspective = translate::perspective_for_slot(slot, current.slot_of_seat0);
        let state = translate::snapshot_to_slots(
            current.game.snapshot(perspective),
            current.slot_of_seat0,
        );
        let frame = PlayerFrame::Snapshot {
            game_number: current.game_number,
            state: Box::new(state),
        };
        send_json(&connection.tx, &frame);
    }

    fn send_snapshot_to_global(&self, id: u64, current: &CurrentContext<'_>) {
        let Some(connection) = self.globals.get(&id) else {
            return;
        };
        let state = translate::snapshot_to_slots(
            current.game.snapshot(Perspective::Global),
            current.slot_of_seat0,
        );
        let frame = GlobalFrame::Snapshot {
            game_number: current.game_number,
            state: Box::new(state),
        };
        send_json(&connection.tx, &frame);
    }

    fn send_window_to_slot_if_current(&self, slot: usize, current: &CurrentContext<'_>) {
        let Some(seat) = expected_seat(current.game.expectation()) else {
            return;
        };
        if translate::seat_to_slot(seat, current.slot_of_seat0) != slot {
            return;
        }
        let Some(connection) = &self.players[slot] else {
            return;
        };
        let frame = PlayerFrame::Window {
            game_number: current.game_number,
            expectation: translate_expectation(current.game.expectation(), current.slot_of_seat0),
            clock_ms_remaining: current.clocks_ms[slot],
            clocks_ms: current.clocks_ms,
            decision_cap_ms: duration_ms(self.config.decision_cap_s),
        };
        send_json(&connection.tx, &frame);
    }

    fn send_window_to_global_if_current(&self, id: u64, current: &CurrentContext<'_>) {
        if expected_seat(current.game.expectation()).is_none() {
            return;
        }
        let Some(connection) = self.globals.get(&id) else {
            return;
        };
        let frame = GlobalFrame::Window {
            game_number: current.game_number,
            expectation: translate_expectation(current.game.expectation(), current.slot_of_seat0),
            clocks_ms: current.clocks_ms,
        };
        send_json(&connection.tx, &frame);
    }

    fn send_ack(&self, slot: usize, cmd_id: u64, seq: Seq) {
        let Some(connection) = &self.players[slot] else {
            return;
        };
        send_json(&connection.tx, &PlayerFrame::Ack { cmd_id, seq });
    }

    fn send_reject(
        &self,
        slot: usize,
        cmd_id: u64,
        kind: impl Into<String>,
        detail: impl Into<String>,
    ) {
        let Some(connection) = &self.players[slot] else {
            return;
        };
        let frame = PlayerFrame::Reject {
            cmd_id,
            error: reject_error(kind, detail),
        };
        send_json(&connection.tx, &frame);
    }

    fn broadcast_game_end(
        &self,
        game_number: u32,
        outcome: GameOutcome,
        slot_of_seat0: usize,
    ) {
        let outcome = translate::outcome_to_slots(outcome, slot_of_seat0);
        for connection in self.players.iter().flatten() {
            let frame = PlayerFrame::GameEnd {
                game_number,
                outcome: outcome.clone(),
                wins: self.wins,
            };
            send_json(&connection.tx, &frame);
        }
        for connection in self.globals.values() {
            let frame = GlobalFrame::GameEnd {
                game_number,
                outcome: outcome.clone(),
                wins: self.wins,
            };
            send_json(&connection.tx, &frame);
        }
    }

    async fn finish_match(&mut self) -> Result<()> {
        let results = self.results();
        for connection in self.players.iter().flatten() {
            let frame = PlayerFrame::MatchEnd {
                scores: results.scores,
                games: results.games.clone(),
            };
            send_json(&connection.tx, &frame);
        }
        for connection in self.globals.values() {
            let frame = GlobalFrame::MatchEnd {
                scores: results.scores,
                games: results.games.clone(),
            };
            send_json(&connection.tx, &frame);
        }
        let replay = Replay {
            version: 1,
            config: self.config.public(),
            games: self.replay_games.clone(),
            results: results.clone(),
        };
        uri::write_json(&config::results_uri(), &results).await?;
        uri::write_json(&config::save_replay_uri(), &replay).await?;
        if let Some(uri) = config::log_uri() {
            uri::write_text(&uri, &self.log_summary(&results)).await?;
        }
        Ok(())
    }

    fn record_events(
        &self,
        replay_events: &mut Vec<ReplayEvent>,
        events: &[LoggedEvent],
        started: Instant,
        slot_of_seat0: usize,
    ) {
        let wall_ms = started.elapsed().as_millis().min(u128::from(u64::MAX)) as u64;
        let full = translate::events_to_slots(events.to_vec(), slot_of_seat0);
        replay_events.extend(full.into_iter().map(|event| ReplayEvent { wall_ms, event }));
    }

    fn game_setup(&self, seed: u64, slot_of_seat0: usize) -> GameSetup {
        let slot_of_seat1 = 1 - slot_of_seat0;
        GameSetup {
            seed,
            players: [
                PlayerSetup {
                    name: self.config.players[slot_of_seat0].name.clone(),
                    deck: self.decks[slot_of_seat0].clone(),
                },
                PlayerSetup {
                    name: self.config.players[slot_of_seat1].name.clone(),
                    deck: self.decks[slot_of_seat1].clone(),
                },
            ],
            starting_life: self.config.starting_life,
            turn_cap: self.config.turn_cap,
            reaction_depth_cap: 4,
        }
    }

    fn game_summary(
        &self,
        game_number: u32,
        seed: u64,
        outcome: &GameOutcome,
        slot_of_seat0: usize,
    ) -> GameSummary {
        let outcome = translate::outcome_to_slots(outcome.clone(), slot_of_seat0);
        GameSummary {
            game_number,
            winner_slot: outcome.winner.map(|seat| seat.0),
            reason: outcome.reason,
            turns: outcome.turns,
            final_life: outcome.final_life,
            seed,
        }
    }

    fn apply_game_score(&mut self, summary: &GameSummary) {
        match summary.winner_slot {
            Some(slot) => self.wins[usize::from(slot)] += 1.0,
            None => {
                self.wins[0] += 0.5;
                self.wins[1] += 0.5;
            }
        }
    }

    fn match_state(&self, game_number: u32) -> MatchState {
        MatchState {
            games_to_win: self.config.games_to_win,
            game_number,
            wins: self.wins,
        }
    }

    fn results(&self) -> Results {
        Results {
            scores: self.wins,
            games: self.summaries.clone(),
            seed: self.config.seed,
            policy_names: [
                self.config.players[0].name.clone(),
                self.config.players[1].name.clone(),
            ],
        }
    }

    fn log_summary(&self, results: &Results) -> String {
        format!(
            "seed={} scores={:?} games={}\n",
            results.seed,
            results.scores,
            results.games.len()
        )
    }

    fn both_players_connected(&self) -> bool {
        self.players.iter().all(Option::is_some)
    }

    fn player_id_matches(&self, slot: usize, id: u64) -> bool {
        self.players
            .get(slot)
            .and_then(Option::as_ref)
            .is_some_and(|connection| connection.id == id)
    }

    fn max_games(&self) -> u32 {
        self.config.games_to_win.saturating_mul(2).saturating_sub(1)
    }

    fn match_is_over(&self, games_played: u32) -> bool {
        let target = f64::from(self.config.games_to_win);
        if self.wins.iter().any(|wins| *wins >= target) {
            return true;
        }
        let remaining = f64::from(self.max_games().saturating_sub(games_played));
        self.wins[0] > self.wins[1] + remaining || self.wins[1] > self.wins[0] + remaining
    }
}

fn send_json<T: serde::Serialize>(tx: &mpsc::UnboundedSender<SocketOut>, value: &T) {
    if let Ok(text) = serde_json::to_string(value) {
        tx.send(SocketOut::Text(text)).ok();
    }
}

fn redact_events(events: &[LoggedEvent], perspective: Perspective) -> Vec<LoggedEvent> {
    events
        .iter()
        .filter_map(|event| event.redact(perspective))
        .collect()
}

fn translate_expectation(expectation: &Expectation, slot_of_seat0: usize) -> Expectation {
    let snapshot = tabletop_core::Snapshot {
        seq: Seq(0),
        turn: 0,
        phase: tabletop_core::Phase::Untap,
        active: SeatId(0),
        expectation: expectation.clone(),
        players: [
            empty_player_snapshot(SeatId(0)),
            empty_player_snapshot(SeatId(1)),
        ],
    };
    translate::snapshot_to_slots(snapshot, slot_of_seat0).expectation
}

fn empty_player_snapshot(seat: SeatId) -> tabletop_core::PlayerSnapshot {
    tabletop_core::PlayerSnapshot {
        seat,
        name: String::new(),
        counters: BTreeMap::new(),
        mulligan_count: 0,
        library_count: 0,
        hand: Vec::new(),
        battlefield: Vec::new(),
        graveyard: Vec::new(),
        exile: Vec::new(),
        arrows: Vec::new(),
    }
}

fn expected_seat(expectation: &Expectation) -> Option<SeatId> {
    match expectation {
        Expectation::Mulligan { seat, .. }
        | Expectation::MainWindow { seat }
        | Expectation::ReactionWindow { seat, .. } => Some(*seat),
        Expectation::GameOver { .. } => None,
    }
}

fn apply_default(game: &mut Game, seat: SeatId) -> Vec<LoggedEvent> {
    let action = match game.expectation().clone() {
        Expectation::Mulligan { must_bottom, .. } => {
            let mut hand: Vec<_> = game.snapshot(Perspective::Seat(seat)).players[seat.index()]
                .hand
                .iter()
                .filter_map(|card| match card {
                    CardRef::Known(view) => Some(view.id),
                    CardRef::Hidden { .. } => None,
                })
                .collect();
            hand.sort();
            Action::MulliganKeep {
                bottom: hand.into_iter().take(usize::from(must_bottom)).collect(),
            }
        }
        Expectation::ReactionWindow { .. } => Action::Pass,
        Expectation::MainWindow { .. } => {
            if game.snapshot(Perspective::Full).phase == tabletop_core::Phase::End {
                Action::NextTurn
            } else {
                Action::NextPhase
            }
        }
        Expectation::GameOver { .. } => return Vec::new(),
    };
    let first = game.log().len();
    game.system_say(seat, "decision timeout; applying default action".to_owned());
    game.submit(seat, action).ok();
    game.log()[first..].to_vec()
}

fn command_id(text: &str) -> u64 {
    serde_json::from_str::<serde_json::Value>(text)
        .ok()
        .and_then(|value| value.get("cmd_id").and_then(serde_json::Value::as_u64))
        .unwrap_or(0)
}

fn seconds_duration(seconds: f64) -> Duration {
    Duration::from_millis(duration_ms(seconds))
}

fn duration_ms(seconds: f64) -> u64 {
    if !seconds.is_finite() || seconds <= 0.0 {
        return 0;
    }
    (seconds * 1000.0).round().min(u64::MAX as f64) as u64
}

fn subtract_elapsed(remaining_ms: &mut u64, elapsed: Duration) {
    let elapsed_ms = elapsed.as_millis().min(u128::from(u64::MAX)) as u64;
    *remaining_ms = remaining_ms.saturating_sub(elapsed_ms);
}

fn escape_html(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}
