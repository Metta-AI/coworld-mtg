use cogatrice_harness::{
    aggregate_results, materialize_corpus, mine_17lands, replay_trace_file, run_shard,
    AggregateOptions, GameTerminal, GameTrace, MaterializeOptions, RunOptions,
};
use flate2::read::MultiGzDecoder;
use serde_json::json;
use std::fs;
use std::io::{BufRead, BufReader};
use std::path::{Path, PathBuf};
use tempfile::TempDir;

fn repo_path(path: &str) -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(path)
}

fn materialize_options(temp: &TempDir, output_name: &str) -> MaterializeOptions {
    MaterializeOptions {
        set: "FIXTURE".to_owned(),
        phase_card_data: repo_path("crates/phase-bridge/tests/fixtures/card-data.json")
            .to_string_lossy()
            .into_owned(),
        phase_sha256: None,
        mtgjson: None,
        mtgjson_sha256: None,
        mtgjson_version: None,
        scryfall: None,
        scryfall_sha256: None,
        scryfall_snapshot: None,
        lands17: None,
        lands17_sha256: None,
        lands17_dataset: None,
        output_dir: temp.path().join(output_name),
    }
}

#[tokio::test]
async fn corpus_manifest_is_content_addressed_and_cross_checks_scryfall() {
    let temp = TempDir::new().unwrap();
    let phase: serde_json::Value = serde_json::from_slice(
        &fs::read(repo_path(
            "crates/phase-bridge/tests/fixtures/card-data.json",
        ))
        .unwrap(),
    )
    .unwrap();
    let mountain = &phase["mountain"];
    let scryfall_path = temp.path().join("scryfall.json");
    fs::write(
        &scryfall_path,
        serde_json::to_vec(&json!([{
            "oracle_id": mountain["scryfall_oracle_id"],
            "name": mountain["name"],
            "oracle_text": mountain["oracle_text"],
            "layout": "normal",
            "legalities": mountain["legalities"]
        }]))
        .unwrap(),
    )
    .unwrap();

    let mut first_options = materialize_options(&temp, "corpus-a");
    first_options.scryfall = Some(scryfall_path.to_string_lossy().into_owned());
    first_options.scryfall_snapshot = Some("fixture-2026-07-13".to_owned());
    let first = materialize_corpus(&first_options).await.unwrap();
    assert_eq!(first.validation.phase_cards, 15);
    assert_eq!(first.validation.matched_oracle_ids, 1);
    assert_eq!(first.validation.matched_faces, 1);
    assert_eq!(first.validation.scryfall_layouts["normal"], 1);
    assert!(first.validation.name_mismatches.is_empty());
    assert!(first.validation.oracle_text_mismatches.is_empty());
    assert!(first.validation.legality_mismatches.is_empty());
    assert_eq!(first.validation.missing_scryfall_oracle_ids.len(), 14);

    let mut second_options = first_options.clone();
    second_options.output_dir = temp.path().join("corpus-b");
    let second = materialize_corpus(&second_options).await.unwrap();
    assert_eq!(first.manifest_id, second.manifest_id);
}

#[tokio::test]
async fn shard_replays_checkpoints_resumes_and_aggregates() {
    let temp = TempDir::new().unwrap();
    let corpus = materialize_corpus(&materialize_options(&temp, "corpus"))
        .await
        .unwrap();
    let manifest_path = temp.path().join("corpus/manifest.json");
    let run_dir = temp.path().join("run");
    let options = RunOptions {
        manifest_uri: manifest_path.to_string_lossy().into_owned(),
        deck_paths: [
            repo_path("decks/red_rush.json"),
            repo_path("decks/green_stompy.json"),
        ],
        output_dir: run_dir.clone(),
        run_id: "fixture-0-1".to_owned(),
        seed_start: 0,
        seed_count: 1,
        action_budget_per_game: 12,
        checkpoint_every: 4,
        max_trace_bytes: 20_000_000,
        resume: false,
    };
    let result = run_shard(&options).await.unwrap();
    assert_eq!(result.manifest_id, corpus.manifest_id);
    assert_eq!(result.terminal_status, "passed");
    assert_eq!(result.counts.attempted, 1);
    assert_eq!(result.counts.hard_failures, 0);

    let reader = BufReader::new(MultiGzDecoder::new(
        fs::File::open(run_dir.join("traces.jsonl.gz")).unwrap(),
    ));
    let line = reader.lines().next().unwrap().unwrap();
    let trace: GameTrace = serde_json::from_str(&line).unwrap();
    assert_eq!(trace.transitions.len(), 12);
    assert_eq!(
        trace
            .transitions
            .iter()
            .filter(|transition| transition.checkpoint.is_some())
            .count(),
        3
    );
    let trace_path = temp.path().join("trace.json");
    fs::write(&trace_path, serde_json::to_vec_pretty(&trace).unwrap()).unwrap();
    replay_trace_file(&options.manifest_uri, &trace_path)
        .await
        .unwrap();

    let mut rejected = trace.clone();
    let attempted = rejected.transitions.pop().unwrap();
    rejected.terminal = GameTerminal::HardFailure {
        signature: "offered_action_rejected".to_owned(),
        detail: "fixture rejection".to_owned(),
        attempted_seat: Some(attempted.seat),
        attempted_action: Some(Box::new(attempted.action.clone())),
    };
    let rejected_json = serde_json::to_value(&rejected).unwrap();
    assert_eq!(
        rejected_json["terminal"]["attempted_action"],
        serde_json::to_value(&attempted.action).unwrap()
    );
    fs::write(&trace_path, serde_json::to_vec_pretty(&rejected).unwrap()).unwrap();
    let error = replay_trace_file(&options.manifest_uri, &trace_path)
        .await
        .unwrap_err();
    assert!(error.to_string().contains("now accepted"));

    rejected.terminal = GameTerminal::HardFailure {
        signature: "offered_action_rejected".to_owned(),
        detail: "fixture rejection".to_owned(),
        attempted_seat: Some(1 - attempted.seat),
        attempted_action: Some(Box::new(attempted.action)),
    };
    fs::write(&trace_path, serde_json::to_vec_pretty(&rejected).unwrap()).unwrap();
    let error = replay_trace_file(&options.manifest_uri, &trace_path)
        .await
        .unwrap_err();
    assert!(error.to_string().contains("no longer offered"));

    let mut resume = options.clone();
    resume.resume = true;
    let resumed = run_shard(&resume).await.unwrap();
    assert_eq!(resumed.counts, result.counts);

    let scoreboard = aggregate_results(&AggregateOptions {
        run_dirs: vec![run_dir],
        output: temp.path().join("scoreboard.json"),
    })
    .unwrap();
    assert_eq!(scoreboard.runs, 1);
    assert_eq!(scoreboard.counts.attempted, 1);
    assert!(scoreboard.findings.is_empty());
}

#[tokio::test]
async fn lands17_mining_stays_in_the_soft_signal_lane() {
    let temp = TempDir::new().unwrap();
    let dataset = temp.path().join("17lands.csv");
    fs::write(
        &dataset,
        "event_type,card_name,drawn_cards,turn,damage\ncast,Mountain,\"[\"\"Goblin Piker\"\"]\",2,0\nattack,Raging Goblin,[],3,1\n",
    )
    .unwrap();
    let mut options = materialize_options(&temp, "corpus");
    options.lands17 = Some(dataset.to_string_lossy().into_owned());
    options.lands17_dataset = Some("fixture-replay-v1".to_owned());
    let manifest = materialize_corpus(&options).await.unwrap();
    let report = mine_17lands(
        &temp.path().join("corpus/manifest.json").to_string_lossy(),
        &temp.path().join("soft-signals.json"),
        None,
    )
    .await
    .unwrap();
    assert_eq!(report.manifest_id, manifest.manifest_id);
    assert_eq!(report.rows, 2);
    assert!(report.interpretation.contains("rules oracle"));
    assert_eq!(report.event_frequency[0].count, 1);
    assert!(report
        .card_frequency
        .iter()
        .any(|card| card.name == "Goblin Piker"));
    assert_eq!(report.numeric_summaries["turn"].mean, 2.5);
}
