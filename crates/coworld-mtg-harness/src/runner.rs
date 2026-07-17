use crate::corpus::{load_manifest, load_phase_runtime};
use crate::invariants::{invariant_failure_signature, validate_invariants};
use crate::io::{canonical_hash, write_json_atomic};
use crate::model::{
    Finding, FindingClassification, GameTerminal, GameTrace, RunCounts, RunLimits, RunResult,
    TraceTransition, RESULT_SCHEMA, TRACE_SCHEMA,
};
use anyhow::{bail, Context, Result};
use flate2::write::GzEncoder;
use flate2::Compression;
use phase_bridge::{GameAction, PhaseGame, PhaseRuntime};
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;
use serde::Deserialize;
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::path::{Path, PathBuf};
use std::time::Instant;

#[derive(Clone, Debug)]
pub struct RunOptions {
    pub manifest_uri: String,
    pub deck_paths: [PathBuf; 2],
    pub output_dir: PathBuf,
    pub run_id: String,
    pub seed_start: u64,
    pub seed_count: u64,
    pub action_budget_per_game: u64,
    pub checkpoint_every: u64,
    pub max_trace_bytes: u64,
    pub resume: bool,
}

#[derive(Deserialize)]
struct DeckFile {
    cards: Vec<DeckEntry>,
}

#[derive(Deserialize)]
struct DeckEntry {
    count: usize,
    spec: DeckSpec,
}

#[derive(Deserialize)]
struct DeckSpec {
    name: String,
}

pub async fn run_shard(options: &RunOptions) -> Result<RunResult> {
    if options.seed_count == 0 {
        bail!("seed count must be positive");
    }
    if options.action_budget_per_game == 0 {
        bail!("action budget must be positive");
    }
    fs::create_dir_all(&options.output_dir)?;
    let manifest = load_manifest(&options.manifest_uri).await?;
    let runtime = load_phase_runtime(&options.manifest_uri, &manifest).await?;
    let decks = [
        load_deck(&options.deck_paths[0])?,
        load_deck(&options.deck_paths[1])?,
    ];
    let limits = RunLimits {
        action_budget_per_game: options.action_budget_per_game,
        checkpoint_every: options.checkpoint_every,
        max_trace_bytes: options.max_trace_bytes,
    };

    let result_path = options.output_dir.join("result.json");
    let (mut counts, mut next_seed, prior_elapsed) = if options.resume && result_path.exists() {
        let previous: RunResult = serde_json::from_slice(&fs::read(&result_path)?)?;
        validate_resume(&previous, options, &manifest.manifest_id, &limits)?;
        (
            previous.counts,
            previous.next_seed,
            previous.elapsed_seconds,
        )
    } else {
        (RunCounts::default(), options.seed_start, 0.0)
    };

    let traces_path = options.output_dir.join("traces.jsonl.gz");
    let findings_path = options.output_dir.join("findings.jsonl.gz");
    let trace_file = append_file(&traces_path, options.resume)?;
    let finding_file = append_file(&findings_path, options.resume)?;
    let mut trace_writer = GzEncoder::new(trace_file, Compression::default());
    let mut finding_writer = GzEncoder::new(finding_file, Compression::default());
    let started = Instant::now();
    let end_seed = options.seed_start.saturating_add(options.seed_count);
    let mut trace_bytes = if options.resume {
        fs::metadata(&traces_path)
            .map(|metadata| metadata.len())
            .unwrap_or(0)
    } else {
        0
    };
    let mut resource_limited = false;

    while next_seed < end_seed {
        let mut trace = match catch_unwind(AssertUnwindSafe(|| {
            run_game(
                &runtime,
                &manifest.manifest_id,
                next_seed,
                decks.clone(),
                options.action_budget_per_game,
                options.checkpoint_every,
            )
        })) {
            Ok(Ok(trace)) => trace,
            Ok(Err(error)) => failure_trace(
                &manifest.manifest_id,
                next_seed,
                decks.clone(),
                "runner_error",
                error.to_string(),
            ),
            Err(payload) => failure_trace(
                &manifest.manifest_id,
                next_seed,
                decks.clone(),
                "phase_panic",
                panic_detail(payload),
            ),
        };

        if !trace.initial_state_hash.is_empty() {
            if let Err(error) = verify_trace(&runtime, &trace, true) {
                trace.terminal = GameTerminal::HardFailure {
                    signature: "deterministic_replay_mismatch".to_owned(),
                    detail: error.to_string(),
                    attempted_seat: None,
                    attempted_action: None,
                };
            }
        }

        let line = serde_json::to_vec(&trace)?;
        let projected = trace_bytes.saturating_add(line.len() as u64 + 1);
        if projected > options.max_trace_bytes {
            resource_limited = true;
            break;
        }
        trace_writer.write_all(&line)?;
        trace_writer.write_all(b"\n")?;
        trace_bytes = projected;

        counts.attempted += 1;
        counts.actions += trace.transitions.len() as u64;
        match &trace.terminal {
            GameTerminal::GameOver { .. } => counts.completed += 1,
            GameTerminal::ActionBudgetExhausted { .. } => counts.action_budget_exhausted += 1,
            GameTerminal::HardFailure {
                signature, detail, ..
            } => {
                counts.hard_failures += 1;
                let finding = Finding {
                    manifest_id: manifest.manifest_id.clone(),
                    run_id: options.run_id.clone(),
                    seed: next_seed,
                    signature: normalized_signature(signature, detail),
                    classification: classify_failure(signature),
                    detail: detail.clone(),
                    trace_line: counts.attempted,
                };
                serde_json::to_writer(&mut finding_writer, &finding)?;
                finding_writer.write_all(b"\n")?;
                let minimized_dir = options.output_dir.join("minimized");
                fs::create_dir_all(&minimized_dir)?;
                write_json_atomic(
                    &minimized_dir.join(format!("seed-{next_seed}.json")),
                    &trace,
                )?;
            }
        }

        next_seed += 1;
        let interim = result(
            options,
            &manifest.manifest_id,
            limits.clone(),
            counts.clone(),
            next_seed,
            prior_elapsed + started.elapsed().as_secs_f64(),
            "running",
        );
        write_json_atomic(&result_path, &interim)?;
    }
    trace_writer.finish()?;
    finding_writer.finish()?;

    let status = if resource_limited {
        "inconclusive_resource_limit"
    } else if counts.hard_failures > 0 {
        "failed"
    } else {
        "passed"
    };
    let final_result = result(
        options,
        &manifest.manifest_id,
        limits,
        counts,
        next_seed,
        prior_elapsed + started.elapsed().as_secs_f64(),
        status,
    );
    write_json_atomic(&result_path, &final_result)?;
    Ok(final_result)
}

fn run_game(
    runtime: &PhaseRuntime,
    manifest_id: &str,
    seed: u64,
    decks: [Vec<String>; 2],
    action_budget: u64,
    checkpoint_every: u64,
) -> Result<GameTrace> {
    let (mut game, initial) = runtime.new_limited_game(decks.clone(), seed)?;
    validate_invariants(&game)?;
    let initial_state_hash = game_state_hash(&game)?;
    let mut trace = GameTrace {
        schema: TRACE_SCHEMA.to_owned(),
        manifest_id: manifest_id.to_owned(),
        seed,
        decks,
        initial_events: initial.events,
        initial_state_hash,
        transitions: Vec::new(),
        terminal: GameTerminal::ActionBudgetExhausted { actions: 0 },
    };
    let mut policy_rng = ChaCha8Rng::seed_from_u64(seed ^ 0x0043_4f57_4f52_4c44);

    for index in 0..action_budget {
        if let Some(outcome) = game.outcome() {
            trace.terminal = GameTerminal::GameOver { outcome };
            return Ok(trace);
        }
        let pending = [0, 1]
            .into_iter()
            .filter_map(|seat| {
                let actions = ordered_legal_actions(&game, seat);
                (!actions.is_empty()).then_some((seat, actions))
            })
            .collect::<Vec<_>>();
        if pending.is_empty() {
            trace.terminal = GameTerminal::HardFailure {
                signature: "deadlock_no_legal_actions".to_owned(),
                detail: format!(
                    "Phase is not game-over but offers no legal action at transition {index}"
                ),
                attempted_seat: None,
                attempted_action: None,
            };
            return Ok(trace);
        }
        let (seat, candidates) = &pending[policy_rng.gen_range(0..pending.len())];
        let action = candidates[policy_rng.gen_range(0..candidates.len())].clone();
        let applied = match catch_unwind(AssertUnwindSafe(|| game.submit(*seat, action.clone()))) {
            Ok(Ok(applied)) => applied,
            Ok(Err(error)) => {
                trace.terminal = GameTerminal::HardFailure {
                    signature: "offered_action_rejected".to_owned(),
                    detail: error.to_string(),
                    attempted_seat: Some(*seat),
                    attempted_action: Some(Box::new(action)),
                };
                return Ok(trace);
            }
            Err(payload) => {
                trace.terminal = GameTerminal::HardFailure {
                    signature: "phase_panic".to_owned(),
                    detail: panic_detail(payload),
                    attempted_seat: Some(*seat),
                    attempted_action: Some(Box::new(action)),
                };
                return Ok(trace);
            }
        };
        let invariant_failure = validate_invariants(&game).err();
        let checkpoint = if checkpoint_every > 0 && (index + 1) % checkpoint_every == 0 {
            Some(game.checkpoint_json()?)
        } else {
            None
        };
        trace.transitions.push(TraceTransition {
            index,
            seat: *seat,
            action,
            events: applied.events,
            state_hash: game_state_hash(&game)?,
            checkpoint,
        });
        if let Some(error) = invariant_failure {
            let detail = error.to_string();
            trace.terminal = GameTerminal::HardFailure {
                signature: invariant_failure_signature(&detail).to_owned(),
                detail,
                attempted_seat: None,
                attempted_action: None,
            };
            return Ok(trace);
        }
    }

    trace.terminal = game
        .outcome()
        .map(|outcome| GameTerminal::GameOver { outcome })
        .unwrap_or(GameTerminal::ActionBudgetExhausted {
            actions: action_budget,
        });
    Ok(trace)
}

fn ordered_legal_actions(game: &PhaseGame, seat: u8) -> Vec<GameAction> {
    let (flat, _, grouped) = game.legal_actions(seat);
    let mut actions = flat;
    let mut grouped = grouped.into_iter().collect::<Vec<_>>();
    grouped.sort_by_key(|(id, _)| id.0);
    for (_, group) in grouped {
        for action in group {
            if !actions.contains(&action) {
                actions.push(action);
            }
        }
    }
    actions
}

fn verify_trace(
    runtime: &PhaseRuntime,
    trace: &GameTrace,
    verify_checkpoint_suffix: bool,
) -> Result<()> {
    if trace.schema != TRACE_SCHEMA {
        bail!("unsupported trace schema {}", trace.schema);
    }
    let (mut game, _) = runtime.new_limited_game(trace.decks.clone(), trace.seed)?;
    let initial = game_state_hash(&game)?;
    if initial != trace.initial_state_hash {
        bail!(
            "initial state hash mismatch: expected {}, got {initial}",
            trace.initial_state_hash
        );
    }
    validate_invariants(&game)?;
    let mut reproduced_invariant_failure = None;
    for (position, transition) in trace.transitions.iter().enumerate() {
        let applied = game.submit(transition.seat, transition.action.clone())?;
        let actual = game_state_hash(&game)?;
        if actual != transition.state_hash {
            bail!(
                "state hash mismatch at transition {}: expected {}, got {actual}",
                transition.index,
                transition.state_hash
            );
        }
        if canonical_hash(&applied.events)? != canonical_hash(&transition.events)? {
            bail!("event stream mismatch at transition {}", transition.index);
        }
        if let Err(error) = validate_invariants(&game) {
            let detail = error.to_string();
            let signature = invariant_failure_signature(&detail);
            let is_recorded_terminal = position + 1 == trace.transitions.len()
                && matches!(
                    &trace.terminal,
                    GameTerminal::HardFailure {
                        signature: expected,
                        detail: expected_detail,
                        attempted_action: None,
                        ..
                    } if expected == signature && expected_detail == &detail
                );
            if !is_recorded_terminal {
                bail!(
                    "unexpected invariant failure at transition {}: {detail}",
                    transition.index
                );
            }
            reproduced_invariant_failure = Some(signature.to_owned());
            break;
        }
    }
    match &trace.terminal {
        GameTerminal::GameOver { outcome } => {
            if game.outcome().as_ref() != Some(outcome) {
                bail!("terminal outcome mismatch");
            }
        }
        GameTerminal::ActionBudgetExhausted { actions } => {
            if game.outcome().is_some() || trace.transitions.len() as u64 != *actions {
                bail!("recorded action-budget exhaustion does not reproduce");
            }
        }
        GameTerminal::HardFailure {
            signature,
            detail,
            attempted_seat: Some(seat),
            attempted_action: Some(action),
        } => {
            if !ordered_legal_actions(&game, *seat).contains(action.as_ref()) {
                bail!("recorded failed action is no longer offered");
            }
            let reproduced = catch_unwind(AssertUnwindSafe(|| {
                game.submit(*seat, action.as_ref().clone())
            }));
            match signature.as_str() {
                "offered_action_rejected" => match reproduced {
                    Ok(Err(error)) if error.to_string() == *detail => {}
                    Ok(Err(error)) => {
                        bail!("recorded rejection detail changed: expected {detail}, got {error}")
                    }
                    Ok(Ok(_)) => bail!("recorded rejected action is now accepted"),
                    Err(_) => bail!("recorded rejected action now panics"),
                },
                "phase_panic" => match reproduced {
                    Err(payload) => {
                        let actual = panic_detail(payload);
                        if actual != *detail {
                            bail!("recorded panic detail changed: expected {detail}, got {actual}");
                        }
                    }
                    Ok(Ok(_)) => bail!("recorded panic action is now accepted"),
                    Ok(Err(_)) => bail!("recorded panic action now returns an error"),
                },
                _ => {
                    bail!("hard failure {signature} has an unexpected attempted action")
                }
            }
        }
        GameTerminal::HardFailure {
            signature,
            attempted_seat,
            attempted_action,
            ..
        } => {
            if attempted_seat.is_some() != attempted_action.is_some() {
                bail!("hard failure attempted seat/action must be recorded together");
            }
            match signature.as_str() {
                "deadlock_no_legal_actions" => {
                    let has_legal_action = [0, 1]
                        .into_iter()
                        .any(|seat| !ordered_legal_actions(&game, seat).is_empty());
                    if game.outcome().is_some() || has_legal_action {
                        bail!("recorded deadlock does not reproduce");
                    }
                }
                "zone_invariant" | "hidden_information_leak" | "invariant_failure" => {
                    if reproduced_invariant_failure.as_deref() != Some(signature.as_str()) {
                        bail!("recorded invariant failure does not reproduce");
                    }
                }
                "offered_action_rejected" | "phase_panic" => {
                    bail!("recorded action failure lacks attempted seat/action")
                }
                _ => bail!("hard failure {signature} has no replay verifier"),
            }
        }
    }

    if verify_checkpoint_suffix {
        if let Some((checkpoint_index, checkpoint)) =
            trace
                .transitions
                .iter()
                .enumerate()
                .find_map(|(index, transition)| {
                    transition.checkpoint.as_ref().map(|value| (index, value))
                })
        {
            let mut restored = runtime.restore_game(checkpoint)?;
            let checkpoint_hash = game_state_hash(&restored)?;
            if checkpoint_hash != trace.transitions[checkpoint_index].state_hash {
                bail!("checkpoint state mismatch at transition {checkpoint_index}");
            }
            for transition in trace.transitions.iter().skip(checkpoint_index + 1) {
                restored.submit(transition.seat, transition.action.clone())?;
                let actual = game_state_hash(&restored)?;
                if actual != transition.state_hash {
                    bail!(
                        "checkpoint suffix mismatch at transition {}",
                        transition.index
                    );
                }
            }
        }
    }
    Ok(())
}

pub async fn replay_trace_file(manifest_uri: &str, trace_path: &Path) -> Result<GameTrace> {
    let manifest = load_manifest(manifest_uri).await?;
    let runtime = load_phase_runtime(manifest_uri, &manifest).await?;
    let trace: GameTrace = serde_json::from_slice(&fs::read(trace_path)?)?;
    if trace.manifest_id != manifest.manifest_id {
        bail!("trace manifest does not match supplied corpus manifest");
    }
    verify_trace(&runtime, &trace, true)?;
    Ok(trace)
}

pub async fn minimize_trace(manifest_uri: &str, input: &Path, output: &Path) -> Result<GameTrace> {
    let manifest = load_manifest(manifest_uri).await?;
    let runtime = load_phase_runtime(manifest_uri, &manifest).await?;
    let mut trace: GameTrace = serde_json::from_slice(&fs::read(input)?)?;
    if verify_trace(&runtime, &trace, true).is_ok() {
        bail!("trace currently passes all hard gates and has no reproducible failure to minimize");
    }

    let (mut game, _) = runtime.new_limited_game(trace.decks.clone(), trace.seed)?;
    let mut keep = trace.transitions.len();
    for (index, transition) in trace.transitions.iter().enumerate() {
        match game.submit(transition.seat, transition.action.clone()) {
            Ok(_) if game_state_hash(&game)? == transition.state_hash => {}
            _ => {
                keep = index + 1;
                break;
            }
        }
    }
    trace.transitions.truncate(keep);
    write_json_atomic(output, &trace)?;
    Ok(trace)
}

fn load_deck(path: &Path) -> Result<Vec<String>> {
    let deck: DeckFile = serde_json::from_slice(
        &fs::read(path).with_context(|| format!("read deck {}", path.display()))?,
    )?;
    let cards = deck
        .cards
        .into_iter()
        .flat_map(|entry| std::iter::repeat_n(entry.spec.name, entry.count))
        .collect::<Vec<_>>();
    if cards.is_empty() {
        bail!("deck {} is empty", path.display());
    }
    Ok(cards)
}

fn append_file(path: &Path, append: bool) -> Result<File> {
    Ok(OpenOptions::new()
        .create(true)
        .write(true)
        .append(append)
        .truncate(!append)
        .open(path)?)
}

fn result(
    options: &RunOptions,
    manifest_id: &str,
    limits: RunLimits,
    counts: RunCounts,
    next_seed: u64,
    elapsed_seconds: f64,
    terminal_status: &str,
) -> RunResult {
    RunResult {
        schema: RESULT_SCHEMA.to_owned(),
        run_id: options.run_id.clone(),
        manifest_id: manifest_id.to_owned(),
        seed_start: options.seed_start,
        seed_count: options.seed_count,
        next_seed,
        terminal_status: terminal_status.to_owned(),
        counts,
        elapsed_seconds,
        limits,
    }
}

fn validate_resume(
    previous: &RunResult,
    options: &RunOptions,
    manifest_id: &str,
    limits: &RunLimits,
) -> Result<()> {
    if previous.run_id != options.run_id
        || previous.manifest_id != manifest_id
        || previous.seed_start != options.seed_start
        || previous.seed_count != options.seed_count
        || &previous.limits != limits
    {
        bail!("resume parameters do not match the existing result.json");
    }
    Ok(())
}

fn failure_trace(
    manifest_id: &str,
    seed: u64,
    decks: [Vec<String>; 2],
    signature: &str,
    detail: String,
) -> GameTrace {
    GameTrace {
        schema: TRACE_SCHEMA.to_owned(),
        manifest_id: manifest_id.to_owned(),
        seed,
        decks,
        initial_events: Vec::new(),
        initial_state_hash: String::new(),
        transitions: Vec::new(),
        terminal: GameTerminal::HardFailure {
            signature: signature.to_owned(),
            detail,
            attempted_seat: None,
            attempted_action: None,
        },
    }
}

fn classify_failure(signature: &str) -> FindingClassification {
    match signature {
        "runner_error" | "hidden_information_leak" | "deterministic_replay_mismatch" => {
            FindingClassification::CoworldIntegrationDefect
        }
        "phase_panic"
        | "deadlock_no_legal_actions"
        | "pending_seat_without_action"
        | "offered_action_rejected"
        | "zone_invariant" => FindingClassification::PhaseDefect,
        _ => FindingClassification::Inconclusive,
    }
}

fn normalized_signature(signature: &str, detail: &str) -> String {
    let stable_detail = detail
        .split_whitespace()
        .map(|word| {
            if word.chars().all(|character| character.is_ascii_digit()) {
                "#"
            } else {
                word
            }
        })
        .collect::<Vec<_>>()
        .join(" ");
    format!(
        "{signature}:{}",
        &crate::io::sha256(stable_detail.as_bytes())[..16]
    )
}

fn panic_detail(payload: Box<dyn std::any::Any + Send>) -> String {
    if let Some(message) = payload.downcast_ref::<&str>() {
        (*message).to_owned()
    } else if let Some(message) = payload.downcast_ref::<String>() {
        message.clone()
    } else {
        "non-string panic payload".to_owned()
    }
}

fn game_state_hash(game: &PhaseGame) -> Result<String> {
    let checkpoint = game.checkpoint_json()?;
    let value: serde_json::Value = serde_json::from_str(&checkpoint)?;
    canonical_hash(&value)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn invariant_failures_keep_stable_ownership_signatures() {
        assert_eq!(
            invariant_failure_signature("zone_invariant: object 39 appears in both hand and stack"),
            "zone_invariant"
        );
        assert_eq!(
            classify_failure("zone_invariant"),
            FindingClassification::PhaseDefect
        );
    }
}
