use phase_bridge::{GameAction, GameEvent, PhaseOutcome};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;

pub const MANIFEST_SCHEMA: &str = "coworld-mtg-harness-corpus-v1";
pub const TRACE_SCHEMA: &str = "coworld-mtg-trace-v1";
pub const RESULT_SCHEMA: &str = "coworld-mtg-result-v1";
pub const SCOREBOARD_SCHEMA: &str = "coworld-mtg-scoreboard-v1";
pub const SOFT_SIGNAL_SCHEMA: &str = "coworld-mtg-17lands-soft-signals-v1";

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Artifact {
    pub source: String,
    pub sha256: String,
    pub bytes: u64,
    pub stored_path: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct CorpusValidation {
    pub phase_cards: usize,
    pub phase_oracle_ids: usize,
    pub scryfall_printings: usize,
    pub matched_oracle_ids: usize,
    pub matched_faces: usize,
    pub scryfall_layouts: BTreeMap<String, usize>,
    pub missing_scryfall_oracle_ids: Vec<String>,
    pub name_mismatches: Vec<String>,
    pub oracle_text_mismatches: Vec<String>,
    pub legality_mismatches: Vec<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct CorpusManifest {
    pub schema: String,
    pub manifest_id: String,
    pub set: String,
    pub phase_revision: String,
    pub generator_schema: String,
    pub input_labels: BTreeMap<String, String>,
    pub artifacts: BTreeMap<String, Artifact>,
    pub output_hashes: BTreeMap<String, String>,
    pub validation: CorpusValidation,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraceTransition {
    pub index: u64,
    pub seat: u8,
    pub action: GameAction,
    pub events: Vec<GameEvent>,
    pub state_hash: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub checkpoint: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GameTrace {
    pub schema: String,
    pub manifest_id: String,
    pub seed: u64,
    pub decks: [Vec<String>; 2],
    pub initial_events: Vec<GameEvent>,
    pub initial_state_hash: String,
    pub transitions: Vec<TraceTransition>,
    pub terminal: GameTerminal,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum GameTerminal {
    GameOver {
        outcome: PhaseOutcome,
    },
    ActionBudgetExhausted {
        actions: u64,
    },
    HardFailure {
        signature: String,
        detail: String,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        attempted_seat: Option<u8>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        attempted_action: Option<Box<GameAction>>,
    },
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct Finding {
    pub manifest_id: String,
    pub run_id: String,
    pub seed: u64,
    pub signature: String,
    pub classification: FindingClassification,
    pub detail: String,
    pub trace_line: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "snake_case")]
pub enum FindingClassification {
    CoworldIntegrationDefect,
    PhaseDefect,
    DataDefect,
    ObservationalAnomaly,
    Inconclusive,
}

#[derive(Clone, Debug, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct RunCounts {
    pub attempted: u64,
    pub completed: u64,
    pub action_budget_exhausted: u64,
    pub hard_failures: u64,
    pub actions: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct RunResult {
    pub schema: String,
    pub run_id: String,
    pub manifest_id: String,
    pub seed_start: u64,
    pub seed_count: u64,
    pub next_seed: u64,
    pub terminal_status: String,
    pub counts: RunCounts,
    pub elapsed_seconds: f64,
    pub limits: RunLimits,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct RunLimits {
    pub action_budget_per_game: u64,
    pub checkpoint_every: u64,
    pub max_trace_bytes: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct ScoreboardEntry {
    pub signature: String,
    pub classification: FindingClassification,
    pub occurrences: u64,
    pub seeds: Vec<u64>,
    pub detail: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct Scoreboard {
    pub schema: String,
    pub manifest_ids: Vec<String>,
    pub runs: usize,
    pub counts: RunCounts,
    pub findings: Vec<ScoreboardEntry>,
    pub soft_signals: BTreeMap<String, Value>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub struct NamedCount {
    pub name: String,
    pub count: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct SoftSignalReport {
    pub schema: String,
    pub manifest_id: String,
    pub dataset_sha256: String,
    pub rows: u64,
    pub card_frequency: Vec<NamedCount>,
    pub event_frequency: Vec<NamedCount>,
    pub numeric_summaries: BTreeMap<String, NumericSummary>,
    pub interpretation: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, Default, PartialEq)]
pub struct NumericSummary {
    pub observations: u64,
    pub mean: f64,
    pub min: f64,
    pub max: f64,
}
