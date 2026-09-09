//! Receipts from the original search transitions, not a second replay of the witness.
use super::*;
use phase_bridge::{GameEvent, ObjectId, PhaseGame};
use std::sync::Arc;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TracePathKind {
    CompleteWitness,
    LongestPrefix,
    NoExecution,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum FieldComparison {
    Matched,
    Mismatched,
    Unknown,
    Unsupported,
    NotReached,
    ProjectionUnavailable,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TraceStatePosition {
    BeforeTransition,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum FailurePathKind {
    SeparateSearchBranch,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TraceFailureKind {
    MilestoneMismatch,
    UnsupportedBoundary,
    NodeBudget,
    ActionBudget,
    OfferedActionFailure,
    InvariantFailure,
    NoAvailableAction,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraceObject {
    pub object_id: ObjectId,
    pub name: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TracePlayer {
    pub seat: u8,
    pub life: i32,
    pub hand: Vec<TraceObject>,
    pub library_count: usize,
    pub graveyard_count: usize,
    pub battlefield: Vec<TraceObject>,
}

/// Named objects and counts under the declared reconstructed setup. Hidden names
/// describe this search hypothesis, not knowledge of the observed opponent's hand.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraceState {
    pub turn_owner: u8,
    pub turn_number: u32,
    pub phase: String,
    pub players: Vec<TracePlayer>,
    pub stack_count: usize,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraceTransition {
    /// Zero-based index into this transition's own path.
    pub index: usize,
    pub seat: u8,
    pub action: phase_bridge::GameAction,
    pub before: TraceState,
    pub after: TraceState,
    /// Exact events returned by the original successful production submission.
    pub events: Vec<GameEvent>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraceDiagnostic {
    pub metric: TraceDiagnosticMetric,
    pub value: Value,
    pub limitation: String,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TraceDiagnosticMetric {
    NativeCombatDamageReceived,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraceField {
    pub source_field_id: String,
    pub raw: String,
    pub disposition: FieldDisposition,
    pub reason: String,
    pub projection: Option<String>,
    pub expected: Option<Value>,
    pub actual: Option<Value>,
    pub comparison: FieldComparison,
    pub diagnostic: Option<TraceDiagnostic>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraceMilestone {
    pub key: MilestoneKey,
    pub transition_index: Option<usize>,
    pub state_position: Option<TraceStatePosition>,
    pub fields: Vec<TraceField>,
}

/// One retained search context, not a certificate about all explored alternatives.
/// Its actions/index are independent of the main retained longest-prefix path.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TraceFailure {
    pub path_kind: FailurePathKind,
    pub kind: TraceFailureKind,
    pub detail: String,
    pub actions_before: Vec<FitAction>,
    pub attempted_action: Option<FitAction>,
    pub attempt: Option<TraceTransition>,
    pub state: TraceState,
    pub milestones: Vec<TraceMilestone>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FitTrace {
    pub schema: String,
    pub path_kind: TracePathKind,
    pub initial_state: Option<TraceState>,
    pub transitions: Vec<TraceTransition>,
    pub milestones: Vec<TraceMilestone>,
    pub failure: Option<TraceFailure>,
}

pub(super) fn project_state(game: &PhaseGame) -> TraceState {
    let state = game.state();
    let objects = |mut ids: Vec<ObjectId>| {
        ids.sort_by_key(|id| id.0);
        ids.into_iter()
            .filter_map(|id| {
                state.objects.get(&id).map(|o| TraceObject {
                    object_id: id,
                    name: o.name.clone(),
                })
            })
            .collect()
    };
    TraceState {
        turn_owner: state.active_player.0,
        turn_number: state.turn_number,
        phase: format!("{:?}", state.phase),
        players: state
            .players
            .iter()
            .enumerate()
            .map(|(seat, p)| TracePlayer {
                seat: seat as u8,
                life: p.life,
                hand: objects(p.hand.iter().copied().collect()),
                library_count: p.library.len(),
                graveyard_count: p.graveyard.len(),
                battlefield: objects(
                    state
                        .battlefield
                        .iter()
                        .copied()
                        .filter(|id| {
                            state
                                .objects
                                .get(id)
                                .is_some_and(|o| usize::from(o.controller.0) == seat)
                        })
                        .collect(),
                ),
            })
            .collect(),
        stack_count: state.stack.len(),
    }
}

pub(super) struct RecordedStep {
    pub previous: Option<Arc<RecordedStep>>,
    pub transition: TraceTransition,
    pub milestones: Vec<TraceMilestone>,
}

pub(super) fn materialize(
    path: &Option<Arc<RecordedStep>>,
) -> (Vec<TraceTransition>, Vec<TraceMilestone>) {
    let mut steps = Vec::new();
    let mut cursor = path.as_ref();
    while let Some(step) = cursor {
        steps.push(step);
        cursor = step.previous.as_ref();
    }
    steps.reverse();
    (
        steps.iter().map(|s| s.transition.clone()).collect(),
        steps.iter().flat_map(|s| s.milestones.clone()).collect(),
    )
}
