mod assets;
mod config;
mod corpus;
mod phase_delta;
mod uri;
pub mod wire;

use anyhow::{anyhow, Context, Result};
use assets::{client_asset, replay_client_asset};
use axum::extract::ws::{close_code, CloseFrame, Message, WebSocket, WebSocketUpgrade};
use axum::extract::{Query, State};
use axum::response::IntoResponse;
use axum::routing::get;
use axum::Router;
use config::EpisodeConfig;
use corpus::Corpus;
use futures::{Sink, SinkExt, StreamExt};
use phase_bridge::{DeckList, GameAction, GameEvent, PhaseGame, PhaseRuntime};
use phase_delta::{apply_phase_delta, phase_delta};
use serde_json::Value;
use std::collections::BTreeMap;
use std::future::{Future, IntoFuture};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use tokio::net::TcpListener;
use tokio::sync::{mpsc, oneshot};
use tokio::time::{sleep, Duration, Instant};
use wire::{
    reject_error, seat_to_slot, slot_to_seat, GameOutcome, GameSummary, GlobalFrame, MatchState,
    PlayerCommand, PlayerFrame, Replay, ReplayConnectionEvent, ReplayFrame, ReplayGame,
    ReplayGameSummary, ReplayStep, Results,
};

#[derive(Clone)]
struct AppState {
    config: Arc<EpisodeConfig>,
    cmd_tx: mpsc::UnboundedSender<ServerCommand>,
    next_conn_id: Arc<AtomicU64>,
}

#[derive(Clone)]
pub(crate) struct ReplayState {
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
        phase_client: bool,
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
        phase_client: bool,
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
    phase_client: bool,
}

struct CurrentContext<'a> {
    game: &'a PhaseGame,
    game_number: u32,
    slot_of_seat0: usize,
    clocks_ms: [u64; 2],
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
    let corpus = Corpus::from_env()?;
    let decks = Arc::new([
        corpus
            .load_deck(&config.decks[0])
            .context("failed to load slot 0 deck")?,
        corpus
            .load_deck(&config.decks[1])
            .context("failed to load slot 1 deck")?,
    ]);
    let runtime = corpus
        .phase_runtime()
        .context("failed to load private Phase card data")?;
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
    let mut runner = MatchRunner::new(config, decks, runtime, cmd_rx);
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
    let text = uri::read_replay_to_string(&replay_uri).await?;
    let replay = Arc::new(serde_json::from_str::<Replay>(&text)?);
    let (host, port) = config::host_port_from_env();
    let listener = TcpListener::bind(format!("{host}:{port}")).await?;
    let app = Router::new()
        .route("/healthz", get(healthz))
        .route("/client/replay", get(replay_client_asset))
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

async fn player_ws(
    State(state): State<AppState>,
    Query(params): Query<BTreeMap<String, String>>,
    ws: WebSocketUpgrade,
) -> impl IntoResponse {
    let slot = params
        .get("slot")
        .and_then(|value| value.parse::<usize>().ok());
    let token = params.get("token").cloned().unwrap_or_default();
    let phase_client = requests_phase_client(&params);
    match slot {
        Some(slot) if slot < 2 && token == state.config.tokens[slot] => {
            ws.on_upgrade(move |socket| player_socket(socket, state, slot, phase_client))
        }
        _ => ws.on_upgrade(policy_violation),
    }
}

async fn global_ws(
    State(state): State<AppState>,
    Query(params): Query<BTreeMap<String, String>>,
    ws: WebSocketUpgrade,
) -> impl IntoResponse {
    let phase_client = requests_phase_client(&params);
    ws.on_upgrade(move |socket| global_socket(socket, state, phase_client))
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

fn requests_phase_client(params: &BTreeMap<String, String>) -> bool {
    params.get("client").is_some_and(|value| value == "phase")
}

async fn player_socket(socket: WebSocket, state: AppState, slot: usize, phase_client: bool) {
    let id = state.next_conn_id.fetch_add(1, Ordering::Relaxed);
    let (tx, rx) = mpsc::unbounded_channel();
    state
        .cmd_tx
        .send(ServerCommand::PlayerConnected {
            slot,
            id,
            tx,
            phase_client,
        })
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

async fn global_socket(socket: WebSocket, state: AppState, phase_client: bool) {
    let id = state.next_conn_id.fetch_add(1, Ordering::Relaxed);
    let (tx, rx) = mpsc::unbounded_channel();
    state
        .cmd_tx
        .send(ServerCommand::GlobalConnected {
            id,
            tx,
            phase_client,
        })
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
            outgoing = rx.recv() => match outgoing {
                Some(SocketOut::Text(text)) => {
                    if sender.send(Message::Text(text.into())).await.is_err() { break; }
                }
                Some(SocketOut::Close) => {
                    sender.send(Message::Close(Some(CloseFrame {
                        code: close_code::NORMAL,
                        reason: "replaced".into(),
                    }))).await.ok();
                    break;
                }
                None => break,
            },
            incoming = receiver.next() => match incoming {
                Some(Ok(Message::Text(text))) => {
                    cmd_tx.send(text_command(text.to_string())).ok();
                }
                Some(Ok(Message::Close(_))) | None => break,
                Some(Ok(_)) => {}
                Some(Err(_)) => break,
            }
        }
    }
    cmd_tx.send(disconnect_command).ok();
}

async fn replay_socket(socket: WebSocket, state: ReplayState) {
    let (mut sender, mut receiver) = socket.split();
    let replay = state.replay;
    let summaries = replay
        .games
        .iter()
        .map(|game| ReplayGameSummary {
            game_number: game.game_number,
            slot_of_seat0: game.slot_of_seat0,
            steps: game.steps.len(),
            connection_events: game.connection_events.clone(),
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
    for game in &replay.games {
        let mut phase_client = None;
        let mut prior_ms = 0;
        for step in &game.steps {
            let delay = step.wall_ms.saturating_sub(prior_ms).min(50);
            if delay > 0 {
                sleep(Duration::from_millis(delay)).await;
            }
            prior_ms = step.wall_ms;
            let mut step = step.clone();
            if let Some(snapshot) = &step.state.phase_client {
                phase_client = serde_json::to_value(snapshot).ok();
            } else if let (Some(current), Some(delta)) =
                (phase_client.as_mut(), step.phase_client_delta.as_ref())
            {
                apply_phase_delta(current, delta);
                step.state.phase_client = serde_json::from_value(current.clone()).ok();
            }
            let frame = ReplayFrame::State {
                game_number: game.game_number,
                step: Box::new(step),
            };
            if send_ws_json(&mut sender, &frame).await.is_err() {
                return;
            }
        }
        if let Some(summary) = replay
            .results
            .games
            .iter()
            .find(|summary| summary.game_number == game.game_number)
        {
            let outcome = GameOutcome {
                winner_slot: summary.winner_slot,
                final_life: summary.final_life,
                turns: summary.turns,
                reason: summary.reason.clone(),
            };
            if send_ws_json(
                &mut sender,
                &ReplayFrame::GameEnd {
                    game_number: game.game_number,
                    outcome,
                    wins: replay.results.scores,
                },
            )
            .await
            .is_err()
            {
                return;
            }
        }
    }
    if send_ws_json(
        &mut sender,
        &ReplayFrame::MatchEnd {
            scores: replay.results.scores,
            games: replay.results.games.clone(),
        },
    )
    .await
    .is_err()
    {
        return;
    }
    while let Some(message) = receiver.next().await {
        if matches!(message, Ok(Message::Close(_)) | Err(_)) {
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
    runtime: PhaseRuntime,
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
        runtime: PhaseRuntime,
        cmd_rx: mpsc::UnboundedReceiver<ServerCommand>,
    ) -> Self {
        Self {
            config,
            decks,
            runtime,
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
            return self.finish_connect_timeout().await;
        }
        for game_index in 0..self.max_games() {
            let game_number = game_index + 1;
            self.play_game(game_number).await?;
            if self.match_is_over(game_number) {
                break;
            }
        }
        self.finish_match().await
    }

    async fn wait_for_players(&mut self) {
        let timer = sleep(seconds_duration(self.config.player_connect_timeout_s));
        tokio::pin!(timer);
        while !self.both_players_connected() {
            tokio::select! {
                _ = &mut timer => break,
                command = self.cmd_rx.recv() => {
                    let Some(command) = command else { break };
                    self.handle_connection_command(command, None);
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
        let deck_names = [
            self.decks[self.deck_index_for_slot(slot_of_seat0, game_number)]
                .cards
                .iter()
                .map(|card| card.name.clone())
                .collect(),
            self.decks[self.deck_index_for_slot(1 - slot_of_seat0, game_number)]
                .cards
                .iter()
                .map(|card| card.name.clone())
                .collect(),
        ];
        let (mut game, initial) = self.runtime.new_limited_game(deck_names, seed)?;
        let mut clocks_ms = [
            duration_ms(self.config.clock_s),
            duration_ms(self.config.clock_s),
        ];
        let started = Instant::now();
        let initial_state = game.phase_client_replay_snapshot_for(0);
        let mut replay_phase_client = serde_json::to_value(
            initial_state
                .phase_client
                .as_ref()
                .ok_or_else(|| anyhow!("Phase replay snapshot omitted Phase client state"))?,
        )?;
        let mut steps = vec![ReplayStep {
            wall_ms: 0,
            actor_slot: None,
            action: None,
            state: initial_state,
            events: initial.events.clone(),
            phase_client_delta: None,
        }];
        let mut connection_events = Vec::new();
        self.send_game_start(
            &game,
            &initial.events,
            game_number,
            slot_of_seat0,
            clocks_ms,
        );
        let mut end_reason = "phase_game_over".to_owned();
        let mut decision_clocks: [Option<Instant>; 2] = [None, None];

        while game.outcome().is_none() {
            let pending = game.pending_seats();
            sync_decision_clocks(&mut decision_clocks, &pending, Instant::now());
            let timeout_seat = next_timeout_seat(
                &pending,
                &decision_clocks,
                clocks_ms,
                slot_of_seat0,
                duration_ms(self.config.decision_cap_s),
                Instant::now(),
            )
            .ok_or_else(|| anyhow!("Phase game has no pending actor and is not over"))?;
            let timeout_slot = seat_to_slot(timeout_seat, slot_of_seat0);
            let wait_started =
                decision_clocks[usize::from(timeout_seat)].expect("decision clock initialized");
            let elapsed_ms = wait_started.elapsed().as_millis().min(u128::from(u64::MAX)) as u64;
            let wait_ms = clocks_ms[timeout_slot]
                .min(duration_ms(self.config.decision_cap_s))
                .saturating_sub(elapsed_ms);
            tokio::select! {
                _ = sleep(Duration::from_millis(wait_ms)) => {
                    subtract_elapsed(&mut clocks_ms[timeout_slot], wait_started.elapsed());
                    decision_clocks[usize::from(timeout_seat)] = None;
                    let (action, result) = if clocks_ms[timeout_slot] == 0 {
                        end_reason = "clock_flag".to_owned();
                        let action = concede_action(timeout_seat);
                        let result = game.concede(timeout_seat)?;
                        (action, result)
                    } else {
                        let action = default_action(&game, timeout_seat)
                            .ok_or_else(|| anyhow!("Phase supplied no timeout action"))?;
                        let result = game.submit(timeout_seat, action.clone())?;
                        (action, result)
                    };
                    self.record_and_broadcast(
                        &game,
                        &mut steps,
                        &mut replay_phase_client,
                        game_number,
                        slot_of_seat0,
                        clocks_ms,
                        started,
                        timeout_slot,
                        action,
                        result.events,
                    )?;
                }
                command = self.cmd_rx.recv() => {
                    let Some(command) = command else { break };
                    match command {
                        ServerCommand::PlayerMessage { slot, id, text } => {
                            if !self.player_id_matches(slot, id) { continue; }
                            let cmd_id = command_id(&text);
                            let command = match serde_json::from_str::<PlayerCommand>(&text) {
                                Ok(command) => command,
                                Err(error) => {
                                    self.send_reject(slot, cmd_id, "bad_request", error.to_string());
                                    continue;
                                }
                            };
                            let seat = slot_to_seat(slot, slot_of_seat0);
                            let clock_neutral = is_clock_neutral_preference(&command.action);
                            if !pending.contains(&seat)
                                && !is_self_concede(&command.action, seat)
                                && !clock_neutral
                            {
                                self.send_reject(
                                    slot,
                                    command.cmd_id,
                                    "not_your_decision",
                                    "Phase has no current legal action for this seat",
                                );
                                continue;
                            }
                            let action = command.action;
                            match game.submit(seat, action.clone()) {
                                Ok(result) => {
                                    if !clock_neutral {
                                        if let Some(actor_started) =
                                            take_decision_clock(&mut decision_clocks, seat)
                                        {
                                            subtract_elapsed(
                                                &mut clocks_ms[slot],
                                                actor_started.elapsed(),
                                            );
                                        }
                                    }
                                    let events = result.events;
                                    self.record_and_broadcast(
                                        &game,
                                        &mut steps,
                                        &mut replay_phase_client,
                                        game_number,
                                        slot_of_seat0,
                                        clocks_ms,
                                        started,
                                        slot,
                                        action,
                                        events,
                                    )?;
                                    self.send_ack(slot, command.cmd_id, game.state().turn_number);
                                }
                                Err(error) => {
                                    self.send_reject(
                                        slot,
                                        command.cmd_id,
                                        "illegal_action",
                                        error.to_string(),
                                    );
                                }
                            }
                        }
                        other => {
                            if let Some(event) = self.replay_connection_event(&other, started) {
                                connection_events.push(event);
                            }
                            let current = CurrentContext {
                                game: &game,
                                game_number,
                                slot_of_seat0,
                                clocks_ms,
                            };
                            self.handle_connection_command(other, Some(&current));
                        }
                    }
                }
            }
        }

        let phase_outcome = game
            .outcome()
            .ok_or_else(|| anyhow!("game ended without a Phase outcome"))?;
        let outcome = GameOutcome::from_phase(phase_outcome, slot_of_seat0, &end_reason);
        let summary = GameSummary {
            game_number,
            winner_slot: outcome.winner_slot,
            reason: outcome.reason.clone(),
            turns: outcome.turns,
            final_life: outcome.final_life,
            seed,
        };
        self.apply_game_score(&summary);
        self.broadcast_game_end(game_number, outcome, self.wins);
        self.summaries.push(summary);
        self.replay_games.push(ReplayGame {
            game_number,
            slot_of_seat0,
            steps,
            connection_events,
        });
        Ok(())
    }

    fn replay_connection_event(
        &self,
        command: &ServerCommand,
        started: Instant,
    ) -> Option<ReplayConnectionEvent> {
        let (slot, connected) = match command {
            ServerCommand::PlayerConnected { slot, .. } => (*slot, true),
            ServerCommand::PlayerDisconnected { slot, id }
                if self.player_id_matches(*slot, *id) =>
            {
                (*slot, false)
            }
            _ => return None,
        };
        Some(ReplayConnectionEvent {
            wall_ms: started.elapsed().as_millis().min(u128::from(u64::MAX)) as u64,
            slot: slot as u8,
            connected,
        })
    }

    #[allow(clippy::too_many_arguments)]
    fn record_and_broadcast(
        &self,
        game: &PhaseGame,
        steps: &mut Vec<ReplayStep>,
        replay_phase_client: &mut Value,
        game_number: u32,
        slot_of_seat0: usize,
        clocks_ms: [u64; 2],
        started: Instant,
        actor_slot: usize,
        action: GameAction,
        events: Vec<GameEvent>,
    ) -> Result<()> {
        let mut state =
            game.phase_client_replay_snapshot_for(slot_to_seat(actor_slot, slot_of_seat0));
        let current = serde_json::to_value(
            state
                .phase_client
                .take()
                .ok_or_else(|| anyhow!("Phase replay snapshot omitted Phase client state"))?,
        )?;
        let phase_client_delta = phase_delta(replay_phase_client, &current);
        *replay_phase_client = current;
        steps.push(ReplayStep {
            wall_ms: started.elapsed().as_millis().min(u128::from(u64::MAX)) as u64,
            actor_slot: Some(actor_slot as u8),
            action: Some(action),
            state,
            events: events.clone(),
            phase_client_delta: Some(phase_client_delta),
        });
        self.broadcast_state(game, &events, game_number, slot_of_seat0, clocks_ms);
        Ok(())
    }

    fn handle_connection_command(
        &mut self,
        command: ServerCommand,
        current: Option<&CurrentContext<'_>>,
    ) {
        match command {
            ServerCommand::PlayerConnected {
                slot,
                id,
                tx,
                phase_client,
            } => {
                if let Some(old) = self.players[slot].replace(Connection {
                    id,
                    tx,
                    phase_client,
                }) {
                    old.tx.send(SocketOut::Close).ok();
                }
                self.send_hello(slot, current);
                if let Some(current) = current {
                    self.send_state_to_slot(slot, current, &[]);
                }
            }
            ServerCommand::PlayerDisconnected { slot, id } => {
                if self.player_id_matches(slot, id) {
                    self.players[slot] = None;
                }
            }
            ServerCommand::GlobalConnected {
                id,
                tx,
                phase_client,
            } => {
                self.globals.insert(
                    id,
                    Connection {
                        id,
                        tx,
                        phase_client,
                    },
                );
                self.send_global_hello(id, current);
                if let Some(current) = current {
                    self.send_state_to_global(id, current, &[]);
                }
            }
            ServerCommand::GlobalDisconnected { id } => {
                self.globals.remove(&id);
            }
            ServerCommand::PlayerMessage { slot, text, .. } => self.send_reject(
                slot,
                command_id(&text),
                "not_started",
                "match has not started",
            ),
            ServerCommand::Ignore => {}
        }
    }

    fn send_game_start(
        &self,
        game: &PhaseGame,
        events: &[GameEvent],
        game_number: u32,
        slot_of_seat0: usize,
        clocks_ms: [u64; 2],
    ) {
        let current = CurrentContext {
            game,
            game_number,
            slot_of_seat0,
            clocks_ms,
        };
        for slot in 0..2 {
            self.send_hello(slot, Some(&current));
            self.send_state_to_slot(slot, &current, events);
        }
        for id in self.globals.keys().copied().collect::<Vec<_>>() {
            self.send_global_hello(id, Some(&current));
            self.send_state_to_global(id, &current, events);
        }
    }

    fn broadcast_state(
        &self,
        game: &PhaseGame,
        events: &[GameEvent],
        game_number: u32,
        slot_of_seat0: usize,
        clocks_ms: [u64; 2],
    ) {
        let current = CurrentContext {
            game,
            game_number,
            slot_of_seat0,
            clocks_ms,
        };
        for slot in 0..2 {
            self.send_state_to_slot(slot, &current, events);
        }
        for id in self.globals.keys().copied().collect::<Vec<_>>() {
            self.send_state_to_global(id, &current, events);
        }
    }

    fn send_hello(&self, slot: usize, current: Option<&CurrentContext<'_>>) {
        let Some(connection) = &self.players[slot] else {
            return;
        };
        let slot_of_seat0 = current.map(|ctx| ctx.slot_of_seat0).unwrap_or(0);
        let game_number = current.map(|ctx| ctx.game_number).unwrap_or(1);
        let seat = slot_to_seat(slot, slot_of_seat0);
        send_json(
            &connection.tx,
            &PlayerFrame::Hello {
                slot,
                seat,
                seat_name: self.config.players[slot].name.clone(),
                player_names: self.player_names_by_seat(slot_of_seat0),
                r#match: self.match_state(game_number),
                config: Box::new(self.config.public()),
                decklist: self.decks[self.deck_index_for_slot(slot, game_number)].clone(),
            },
        );
    }

    fn deck_index_for_slot(&self, slot: usize, game_number: u32) -> usize {
        if self.config.swap_decks_each_game && game_number.is_multiple_of(2) {
            1 - slot
        } else {
            slot
        }
    }

    fn send_global_hello(&self, id: u64, current: Option<&CurrentContext<'_>>) {
        let Some(connection) = self.globals.get(&id) else {
            return;
        };
        let slot_of_seat0 = current.map(|ctx| ctx.slot_of_seat0).unwrap_or(0);
        send_json(
            &connection.tx,
            &GlobalFrame::Hello {
                player_names: self.player_names_by_seat(slot_of_seat0),
                r#match: self.match_state(current.map(|ctx| ctx.game_number).unwrap_or(1)),
                config: self.config.public(),
            },
        );
    }

    fn send_state_to_slot(&self, slot: usize, current: &CurrentContext<'_>, events: &[GameEvent]) {
        let Some(connection) = &self.players[slot] else {
            return;
        };
        let seat = slot_to_seat(slot, current.slot_of_seat0);
        let state = if connection.phase_client {
            current.game.phase_client_snapshot(seat)
        } else {
            current.game.viewer_snapshot(seat)
        };
        send_json(
            &connection.tx,
            &PlayerFrame::State {
                game_number: current.game_number,
                state: Box::new(state),
                events: current.game.filter_events(events, seat),
                clocks_ms: current.clocks_ms,
                decision_cap_ms: duration_ms(self.config.decision_cap_s),
            },
        );
    }

    fn send_state_to_global(&self, id: u64, current: &CurrentContext<'_>, events: &[GameEvent]) {
        let Some(connection) = self.globals.get(&id) else {
            return;
        };
        let state = if connection.phase_client {
            current.game.phase_client_spectator_snapshot()
        } else {
            current.game.spectator_snapshot()
        };
        send_json(
            &connection.tx,
            &GlobalFrame::State {
                game_number: current.game_number,
                state: Box::new(state),
                events: current
                    .game
                    .filter_events(events, phase_bridge::SPECTATOR_ID),
                clocks_ms: current.clocks_ms,
            },
        );
    }

    fn send_ack(&self, slot: usize, cmd_id: u64, turn: u32) {
        if let Some(connection) = &self.players[slot] {
            send_json(&connection.tx, &PlayerFrame::Ack { cmd_id, turn });
        }
    }

    fn send_reject(&self, slot: usize, cmd_id: u64, kind: &str, detail: impl Into<String>) {
        if let Some(connection) = self.players.get(slot).and_then(Option::as_ref) {
            send_json(
                &connection.tx,
                &PlayerFrame::Reject {
                    cmd_id,
                    error: reject_error(kind, detail),
                },
            );
        }
    }

    fn broadcast_game_end(&self, game_number: u32, outcome: GameOutcome, wins: [f64; 2]) {
        for connection in self.players.iter().flatten() {
            send_json(
                &connection.tx,
                &PlayerFrame::GameEnd {
                    game_number,
                    outcome: outcome.clone(),
                    wins,
                },
            );
        }
        for connection in self.globals.values() {
            send_json(
                &connection.tx,
                &GlobalFrame::GameEnd {
                    game_number,
                    outcome: outcome.clone(),
                    wins,
                },
            );
        }
    }

    async fn finish_match(&mut self) -> Result<()> {
        let results = Results {
            scores: self.wins,
            games: self.summaries.clone(),
            seed: self.config.seed,
            policy_names: [
                self.config.players[0].name.clone(),
                self.config.players[1].name.clone(),
            ],
        };
        for connection in self.players.iter().flatten() {
            send_json(
                &connection.tx,
                &PlayerFrame::MatchEnd {
                    scores: results.scores,
                    games: results.games.clone(),
                },
            );
        }
        for connection in self.globals.values() {
            send_json(
                &connection.tx,
                &GlobalFrame::MatchEnd {
                    scores: results.scores,
                    games: results.games.clone(),
                },
            );
        }
        let replay = Replay {
            version: 3,
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

    fn log_summary(&self, results: &Results) -> String {
        let games = results
            .games
            .iter()
            .map(|game| {
                format!(
                    "game {} winner={:?} reason={} turns={} life={:?}",
                    game.game_number, game.winner_slot, game.reason, game.turns, game.final_life
                )
            })
            .collect::<Vec<_>>()
            .join("\n");
        format!("scores={:?}\n{games}\n", results.scores)
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

    fn player_names_by_seat(&self, slot_of_seat0: usize) -> [String; 2] {
        [
            self.config.players[slot_of_seat0].name.clone(),
            self.config.players[1 - slot_of_seat0].name.clone(),
        ]
    }

    fn match_state(&self, game_number: u32) -> MatchState {
        MatchState {
            games_to_win: self.config.games_to_win,
            game_number,
            wins: self.wins,
        }
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

fn default_action(game: &PhaseGame, seat: u8) -> Option<GameAction> {
    let actions = game.legal_actions(seat).0;
    for preferred in [
        "MulliganDecision",
        "PassPriority",
        "DeclareAttackers",
        "DeclareBlockers",
    ] {
        if let Some(action) = actions.iter().find(|action| {
            let value = serde_json::to_value(action).ok();
            value
                .as_ref()
                .and_then(|value| value.get("type"))
                .and_then(serde_json::Value::as_str)
                == Some(preferred)
                && (preferred != "MulliganDecision"
                    || value
                        .as_ref()
                        .and_then(|value| value.get("data"))
                        .and_then(|value| value.get("choice"))
                        .and_then(|value| value.get("type"))
                        .and_then(serde_json::Value::as_str)
                        == Some("Keep"))
        }) {
            return Some(action.clone());
        }
    }
    actions.into_iter().next()
}

fn concede_action(seat: u8) -> GameAction {
    serde_json::from_value(serde_json::json!({
        "type": "Concede",
        "data": { "player_id": seat }
    }))
    .expect("Phase Concede wire shape")
}

fn is_self_concede(action: &GameAction, seat: u8) -> bool {
    serde_json::to_value(action).is_ok_and(|value| {
        value.get("type").and_then(serde_json::Value::as_str) == Some("Concede")
            && value
                .get("data")
                .and_then(|value| value.get("player_id"))
                .and_then(serde_json::Value::as_u64)
                == Some(u64::from(seat))
    })
}

fn is_clock_neutral_preference(action: &GameAction) -> bool {
    matches!(
        action,
        GameAction::CancelAutoPass | GameAction::SetPhaseStops { .. }
    )
}

fn sync_decision_clocks(clocks: &mut [Option<Instant>; 2], pending: &[u8], now: Instant) {
    for seat in 0..2_u8 {
        if pending.contains(&seat) {
            clocks[usize::from(seat)].get_or_insert(now);
        } else {
            clocks[usize::from(seat)] = None;
        }
    }
}

fn take_decision_clock(clocks: &mut [Option<Instant>; 2], seat: u8) -> Option<Instant> {
    clocks.get_mut(usize::from(seat)).and_then(Option::take)
}

fn next_timeout_seat(
    pending: &[u8],
    decision_clocks: &[Option<Instant>; 2],
    clocks_ms: [u64; 2],
    slot_of_seat0: usize,
    decision_cap_ms: u64,
    now: Instant,
) -> Option<u8> {
    pending.iter().copied().min_by_key(|seat| {
        let slot = seat_to_slot(*seat, slot_of_seat0);
        let elapsed_ms = decision_clocks[usize::from(*seat)]
            .map(|started| now.saturating_duration_since(started).as_millis())
            .unwrap_or(0)
            .min(u128::from(u64::MAX)) as u64;
        clocks_ms[slot]
            .min(decision_cap_ms)
            .saturating_sub(elapsed_ms)
    })
}

fn send_json<T: serde::Serialize>(tx: &mpsc::UnboundedSender<SocketOut>, value: &T) {
    if let Ok(text) = serde_json::to_string(value) {
        tx.send(SocketOut::Text(text)).ok();
    }
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn phase_client_payload_requires_explicit_capability() {
        assert!(!requests_phase_client(&BTreeMap::new()));
        assert!(!requests_phase_client(&BTreeMap::from([(
            "client".to_owned(),
            "legacy".to_owned(),
        )])));
        assert!(requests_phase_client(&BTreeMap::from([(
            "client".to_owned(),
            "phase".to_owned(),
        )])));
    }

    #[test]
    fn simultaneous_decisions_keep_independent_clocks() {
        let started = Instant::now();
        let mut clocks = [None, None];
        sync_decision_clocks(&mut clocks, &[0, 1], started);

        assert_eq!(take_decision_clock(&mut clocks, 1), Some(started));
        assert_eq!(clocks[0], Some(started));
        assert_eq!(clocks[1], None);

        sync_decision_clocks(&mut clocks, &[0], started + Duration::from_secs(1));
        assert_eq!(clocks[0], Some(started));
        assert_eq!(clocks[1], None);
    }

    #[test]
    fn simultaneous_timeout_uses_the_earliest_effective_deadline() {
        let started = Instant::now();
        let decision_clocks = [Some(started), Some(started)];
        let seat = next_timeout_seat(
            &[0, 1],
            &decision_clocks,
            [30_000, 2_000],
            0,
            10_000,
            started + Duration::from_millis(500),
        );
        assert_eq!(seat, Some(1));
    }

    #[test]
    fn only_nonadvancing_preferences_are_clock_neutral() {
        assert!(is_clock_neutral_preference(&GameAction::CancelAutoPass));
        assert!(is_clock_neutral_preference(&GameAction::SetPhaseStops {
            stops: Vec::new(),
        }));
        assert!(!is_clock_neutral_preference(&GameAction::PassPriority));
    }
}
