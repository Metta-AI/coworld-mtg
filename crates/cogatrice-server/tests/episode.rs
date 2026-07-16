#![cfg(feature = "private-corpus-tests")]

use cogatrice_server::wire::{Replay, Results};
use futures::StreamExt;
use serde_json::{json, Value};
use std::future::Future;
use std::path::{Path, PathBuf};
use std::sync::OnceLock;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::{oneshot, Mutex};
use tokio::time::{sleep, timeout, Duration};
use tokio_tungstenite::tungstenite::Message;

static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
const WORKER_STACK_SIZE: usize = 4 * 1024 * 1024;

#[test]
fn goldfish_match_writes_results_and_replay() {
    run_episode_test(async {
        let _guard = env_lock().lock().await;
        let outcome = run_completed_match(
            "e2e",
            5.0,
            1.0,
            false,
            ["lorehold_excavation", "fractal_convergence"],
            1,
            false,
        )
        .await;

        assert_reports(&outcome.reports);
        assert_eq!(
            outcome.reports[0].hellos[0].deck_name,
            "Lorehold Excavation"
        );
        assert_eq!(
            outcome.reports[1].hellos[0].deck_name,
            "Fractal Convergence"
        );
        let results: Results =
            serde_json::from_str(&tokio::fs::read_to_string(&outcome.results).await.unwrap())
                .unwrap();
        assert_eq!(results.scores[0] + results.scores[1], 1.0);
        assert_eq!(results.games.len(), 1);
        assert!(matches!(
            results.games[0].reason.as_str(),
            "phase_game_over" | "clock_flag"
        ));

        let replay: Replay =
            serde_json::from_str(&tokio::fs::read_to_string(&outcome.replay).await.unwrap())
                .unwrap();
        assert_eq!(replay.version, 3);
        assert_eq!(replay.games.len(), 1);
        assert!(!replay.games[0].steps.is_empty());
        assert!(replay.games[0].steps[0].action.is_none());
        assert!(replay.games[0].steps[0].state.phase_client.is_some());
        assert!(replay.games[0]
            .steps
            .iter()
            .skip(1)
            .all(|step| step.state.phase_client.is_none() && step.phase_client_delta.is_some()));
    });
}

#[test]
fn replay_mode_serves_a_finite_recording() {
    run_episode_test(async {
        let _guard = env_lock().lock().await;
        let outcome = run_completed_match(
            "replay_source",
            5.0,
            1.0,
            false,
            ["lorehold_excavation", "fractal_convergence"],
            1,
            false,
        )
        .await;
        let port = free_port();
        set_common_env(port);
        std::env::set_var("COGAME_LOAD_REPLAY_URI", &outcome.replay);
        let (shutdown_tx, shutdown_rx) = oneshot::channel();
        let server = tokio::spawn(cogatrice_server::run_until_shutdown(async {
            shutdown_rx.await.ok();
        }));
        wait_healthz(port).await;

        let page = reqwest::get(format!("http://127.0.0.1:{port}/client/replay"))
            .await
            .unwrap();
        assert!(page.status().is_success());

        let (socket, _) = tokio_tungstenite::connect_async(format!("ws://127.0.0.1:{port}/replay"))
            .await
            .unwrap();
        let (_, mut read) = socket.split();
        assert_eq!(next_type(&mut read).await, "replay_meta");
        assert_eq!(next_type(&mut read).await, "state");
        let mut saw_match_end = false;
        for _ in 0..4096 {
            let kind = next_type(&mut read).await;
            if kind == "match_end" {
                saw_match_end = true;
                break;
            }
        }
        assert!(saw_match_end);
        assert!(timeout(Duration::from_millis(100), read.next())
            .await
            .is_err());

        shutdown_tx.send(()).ok();
        timeout(Duration::from_secs(5), server)
            .await
            .unwrap()
            .unwrap()
            .unwrap();
        std::env::remove_var("COGAME_LOAD_REPLAY_URI");
    });
}

#[test]
fn mute_player_times_out_but_match_finishes() {
    run_episode_test(async {
        let _guard = env_lock().lock().await;
        let outcome = run_completed_match(
            "timeout",
            1.0,
            0.05,
            true,
            ["lorehold_excavation", "fractal_convergence"],
            1,
            false,
        )
        .await;
        let results: Results =
            serde_json::from_str(&tokio::fs::read_to_string(&outcome.results).await.unwrap())
                .unwrap();
        assert_eq!(results.scores[0] + results.scores[1], 1.0);
        assert!(!results.games.is_empty());
    });
}

#[test]
fn reversed_single_game_matchup_exchanges_decks_between_players() {
    run_episode_test(async {
        let _guard = env_lock().lock().await;
        let outcome = run_completed_match(
            "reversed_single_game",
            10.0,
            1.0,
            false,
            ["fractal_convergence", "lorehold_excavation"],
            1,
            false,
        )
        .await;

        let results: Results =
            serde_json::from_str(&tokio::fs::read_to_string(&outcome.results).await.unwrap())
                .unwrap();
        assert_eq!(results.games.len(), 1);
        assert_eq!(
            outcome.reports[0].hellos[0].deck_name,
            "Fractal Convergence"
        );
        assert_eq!(
            outcome.reports[1].hellos[0].deck_name,
            "Lorehold Excavation"
        );
    });
}

fn run_episode_test(test: impl Future<Output = ()>) {
    tokio::runtime::Builder::new_multi_thread()
        .worker_threads(2)
        .thread_stack_size(WORKER_STACK_SIZE)
        .enable_all()
        .build()
        .unwrap()
        .block_on(test);
}

struct MatchOutcome {
    results: PathBuf,
    replay: PathBuf,
    reports: [goldfish::GoldfishReport; 2],
}

async fn run_completed_match(
    name: &str,
    clock_s: f64,
    decision_cap_s: f64,
    mute_slot_1: bool,
    decks: [&str; 2],
    games_to_win: u32,
    swap_decks_each_game: bool,
) -> MatchOutcome {
    let root = temp_root(name);
    let config = root.join("config.json");
    let results = root.join("results.json");
    let replay = root.join("replay.json");
    let log = root.join("log.txt");
    write_config(
        &config,
        clock_s,
        decision_cap_s,
        decks,
        games_to_win,
        swap_decks_each_game,
    )
    .await;
    let port = free_port();
    set_common_env(port);
    std::env::set_var("COGAME_CONFIG_URI", &config);
    std::env::set_var("COGAME_RESULTS_URI", &results);
    std::env::set_var("COGAME_SAVE_REPLAY_URI", &replay);
    std::env::set_var("COGAME_LOG_URI", &log);
    std::env::remove_var("COGAME_LOAD_REPLAY_URI");

    let server = tokio::spawn(cogatrice_server::run_until_shutdown(std::future::pending()));
    wait_healthz(port).await;
    let slot0 = format!("ws://127.0.0.1:{port}/player?slot=0&token=tokA");
    let slot1 = format!("ws://127.0.0.1:{port}/player?slot=1&token=tokB");
    let player0 = tokio::spawn(async move { goldfish::run_url(&slot0).await });
    let player1 = if mute_slot_1 {
        tokio::spawn(async move {
            run_mute_client(&slot1).await;
            Ok(goldfish::GoldfishReport::default())
        })
    } else {
        tokio::spawn(async move { goldfish::run_url(&slot1).await })
    };
    let report0 = timeout(Duration::from_secs(60), player0)
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    let report1 = timeout(Duration::from_secs(60), player1)
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    timeout(Duration::from_secs(5), server)
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    assert!(results.exists());
    assert!(replay.exists());
    MatchOutcome {
        results,
        replay,
        reports: [report0, report1],
    }
}

async fn write_config(
    path: &Path,
    clock_s: f64,
    decision_cap_s: f64,
    decks: [&str; 2],
    games_to_win: u32,
    swap_decks_each_game: bool,
) {
    let config = json!({
        "tokens": ["tokA", "tokB"],
        "players": [{"name": "goldfish-0"}, {"name": "goldfish-1"}],
        "seed": 4242,
        "decks": decks,
        "games_to_win": games_to_win,
        "swap_decks_each_game": swap_decks_each_game,
        "clock_s": clock_s,
        "decision_cap_s": decision_cap_s,
        "player_connect_timeout_s": 5.0
    });
    tokio::fs::write(path, serde_json::to_vec_pretty(&config).unwrap())
        .await
        .unwrap();
}

async fn run_mute_client(url: &str) {
    let (socket, _) = tokio_tungstenite::connect_async(url).await.unwrap();
    let (_, mut read) = socket.split();
    while let Some(message) = read.next().await {
        let Ok(Message::Text(text)) = message else {
            continue;
        };
        let value: Value = serde_json::from_str(&text).unwrap();
        if value.get("type").and_then(Value::as_str) == Some("match_end") {
            break;
        }
    }
}

async fn next_type(
    read: &mut futures::stream::SplitStream<
        tokio_tungstenite::WebSocketStream<
            tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>,
        >,
    >,
) -> String {
    let message = timeout(Duration::from_secs(5), read.next())
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    let Message::Text(text) = message else {
        panic!("expected text frame");
    };
    let value: Value = serde_json::from_str(&text).unwrap();
    value
        .get("type")
        .and_then(Value::as_str)
        .unwrap()
        .to_owned()
}

fn assert_reports(reports: &[goldfish::GoldfishReport; 2]) {
    for (slot, report) in reports.iter().enumerate() {
        assert!(!report.leaked_opponent_hand);
        assert!(report
            .hellos
            .iter()
            .any(|hello| hello.slot == slot && hello.deck_size == 40));
    }
}

async fn wait_healthz(port: u16) {
    for _ in 0..100 {
        if let Ok(response) = reqwest::get(format!("http://127.0.0.1:{port}/healthz")).await {
            if response.status().is_success() {
                return;
            }
        }
        sleep(Duration::from_millis(50)).await;
    }
    panic!("server did not become healthy");
}

fn set_common_env(port: u16) {
    std::env::set_var("COGAME_HOST", "127.0.0.1");
    std::env::set_var("COGAME_PORT", port.to_string());
    std::env::set_var(
        "COGAME_CORPUS_DIR",
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../.private/corpus"),
    );
}

fn free_port() -> u16 {
    std::net::TcpListener::bind("127.0.0.1:0")
        .unwrap()
        .local_addr()
        .unwrap()
        .port()
}

fn temp_root(name: &str) -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!(
        "cogatrice-m2-{name}-{}-{nonce}",
        std::process::id()
    ));
    std::fs::create_dir_all(&root).unwrap();
    root
}

fn env_lock() -> &'static Mutex<()> {
    ENV_LOCK.get_or_init(|| Mutex::new(()))
}
