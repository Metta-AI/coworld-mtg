//! The offline improvement protocol. No engine, filesystem, network or agent dependency.
//! Workers receive setup and operations; only the coordinator receives expectations.

mod protocol;
pub use protocol::*;
mod attribution;
pub use attribution::*;

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct ContentHash(String);

impl JsonSchema for ContentHash {
    fn schema_name() -> std::borrow::Cow<'static, str> {
        "Sha256".into()
    }
    fn json_schema(_: &mut schemars::SchemaGenerator) -> schemars::Schema {
        schemars::json_schema!({"type": "string", "pattern": "^[0-9a-f]{64}$"})
    }
}

impl TryFrom<String> for ContentHash {
    type Error = String;
    fn try_from(value: String) -> Result<Self, Self::Error> {
        if value.len() == 64
            && value
                .bytes()
                .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
        {
            Ok(Self(value))
        } else {
            Err("expected a lowercase SHA-256 digest".into())
        }
    }
}
impl From<ContentHash> for String {
    fn from(value: ContentHash) -> Self {
        value.0
    }
}
impl std::fmt::Display for ContentHash {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.0.fmt(f)
    }
}
pub fn hash_bytes(bytes: &[u8]) -> ContentHash {
    ContentHash(hex::encode(Sha256::digest(bytes)))
}
pub fn digest(value: &impl Serialize) -> Result<ContentHash, serde_json::Error> {
    // serde_json's default Map is sorted. Array order is deliberately preserved.
    Ok(hash_bytes(&serde_json::to_vec(&serde_json::to_value(
        value,
    )?)?))
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum Seat {
    Player,
    Opponent,
}
impl Seat {
    pub fn index(self) -> usize {
        match self {
            Self::Player => 0,
            Self::Opponent => 1,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum CardZone {
    Hand,
    Library,
    Battlefield,
    Graveyard,
    Exile,
    Stack,
    Command,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum Mana {
    White,
    Blue,
    Black,
    Red,
    Green,
    Colorless,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct PlacedCard {
    pub label: String,
    pub name: String,
    pub owner: Seat,
    pub zone: CardZone,
    #[serde(default)]
    pub tapped: bool,
    #[serde(default)]
    pub plus_one_counters: u32,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Target {
    Player { seat: Seat },
    Object { label: String },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum CastFinish {
    Commit,
    Resolve,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Operation {
    Cast {
        card: String,
        targets: Vec<Target>,
        finish: CastFinish,
        #[serde(default)]
        x: Option<u32>,
    },
    PassPriority,
    ResolveStack,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Scenario {
    pub seed: u64,
    pub life: [i32; 2],
    pub mana: [Vec<Mana>; 2],
    pub cards: Vec<PlacedCard>,
    pub operations: Vec<Operation>,
}

impl Scenario {
    pub fn validate(&self) -> Result<(), String> {
        if self.cards.len() > 128
            || self.operations.len() > 128
            || self.mana.iter().any(|m| m.len() > 128)
        {
            return Err("scenario exceeds 128 cards, operations or mana per player".into());
        }
        let mut labels = BTreeSet::new();
        for card in &self.cards {
            if card.label.is_empty() || card.name.is_empty() || !labels.insert(&card.label) {
                return Err(
                    "card labels must be nonempty and unique; card names must be nonempty".into(),
                );
            }
        }
        for op in &self.operations {
            if let Operation::Cast { card, targets, .. } = op {
                if !labels.contains(card) {
                    return Err(format!("unknown cast label {card}"));
                }
                for target in targets {
                    if let Target::Object { label } = target {
                        if !labels.contains(label) {
                            return Err(format!("unknown target label {label}"));
                        }
                    }
                }
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Predicate {
    Life {
        seat: Seat,
        equals: i32,
    },
    Zone {
        object: String,
        equals: CardZone,
    },
    Tapped {
        object: String,
        equals: bool,
    },
    PlusOneCounters {
        object: String,
        equals: u32,
    },
    Prepared {
        object: String,
        equals: bool,
    },
    OfferedCastSpell {
        object: String,
        seat: Seat,
        equals: bool,
    },
    ZoneCount {
        seat: Seat,
        zone: CardZone,
        name: String,
        equals: u32,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Assertion {
    pub id: String,
    pub predicate: Predicate,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Citation {
    pub source: String,
    pub reference: String,
    pub statement: String,
}

/// Observation-only cases cannot enter the acceptance gate.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Justification {
    Rules {
        citations: Vec<Citation>,
    },
    Invariant {
        specification: String,
    },
    Observation {
        source_sha256: ContentHash,
        assumptions: Vec<String>,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct CaseSpec {
    pub title: String,
    pub author: String,
    #[serde(default, skip_serializing_if = "CaseOrigin::is_authored")]
    pub origin: CaseOrigin,
    pub justification: Justification,
    pub scenario: Scenario,
    /// Establish that the intended behavior was reached before judging its result.
    #[serde(default)]
    pub guards: Vec<Assertion>,
    pub assertions: Vec<Assertion>,
}
impl CaseSpec {
    pub fn validate(&self) -> Result<(), String> {
        self.scenario.validate()?;
        if self.title.trim().is_empty()
            || self.author.trim().is_empty()
            || self.assertions.is_empty()
        {
            return Err("a case requires title, author and at least one assertion".into());
        }
        let mut ids = BTreeSet::new();
        if !self.scenario.operations.is_empty() && self.guards.is_empty() {
            return Err("scenarios with operations require a reachability guard".into());
        }
        for assertion in self.guards.iter().chain(&self.assertions) {
            if assertion.id.is_empty() || !ids.insert(&assertion.id) {
                return Err("assertion IDs must be nonempty and unique".into());
            }
            let label = match &assertion.predicate {
                Predicate::Zone { object, .. }
                | Predicate::Tapped { object, .. }
                | Predicate::PlusOneCounters { object, .. }
                | Predicate::Prepared { object, .. }
                | Predicate::OfferedCastSpell { object, .. } => Some(object),
                Predicate::Life { .. } | Predicate::ZoneCount { .. } => None,
            };
            if label
                .is_some_and(|label| !self.scenario.cards.iter().any(|card| &card.label == label))
            {
                return Err("assertion refers to an unknown object label".into());
            }
        }
        match &self.origin {
            CaseOrigin::Evidence {
                artifacts,
                explanation,
            } if artifacts.is_empty() || explanation.trim().is_empty() => {
                return Err("evidence-derived cases require artifacts and an explanation".into())
            }
            CaseOrigin::Derived { transformation, .. } if transformation.trim().is_empty() => {
                return Err("derived cases require a transformation description".into())
            }
            _ => {}
        }
        match &self.justification {
            Justification::Rules { citations }
                if citations.is_empty()
                    || citations.iter().any(|c| {
                        c.source.is_empty() || c.reference.is_empty() || c.statement.is_empty()
                    }) =>
            {
                Err("rules cases require complete citations".into())
            }
            Justification::Invariant { specification } if specification.trim().is_empty() => {
                Err("invariant specification is empty".into())
            }
            _ => Ok(()),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ObjectObservation {
    pub object_id: u64,
    pub name: String,
    pub owner: Seat,
    pub zone: CardZone,
    pub tapped: bool,
    pub plus_one_counters: u32,
    pub prepared: bool,
    pub cast_spell_offered_to: Vec<Seat>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Observation {
    pub life: [i32; 2],
    /// Includes tokens and copies, sorted by engine object ID. JSON object keys remain strings.
    pub objects: Vec<ObjectObservation>,
    pub labels: BTreeMap<String, u64>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum IncompleteReason {
    UnresolvedCard { name: String },
    InvalidScenario { detail: String },
    DriverFailed { detail: String },
    WorkerBudget { seconds: u64 },
    WorkerFailed { detail: String },
    InvalidEvidence { detail: String },
    RepeatedExecutionDiverged,
    GuardNotReached { detail: String },
    MissingObservation { assertion_id: String },
}
impl From<String> for IncompleteReason {
    fn from(detail: String) -> Self {
        Self::DriverFailed { detail }
    }
}
impl From<&str> for IncompleteReason {
    fn from(detail: &str) -> Self {
        Self::DriverFailed {
            detail: detail.into(),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum CheckResult {
    Satisfied,
    Violated { assertion_ids: Vec<String> },
    Inconclusive { reason: IncompleteReason },
}

pub fn check(case: &CaseSpec, observation: &Observation) -> CheckResult {
    let ids = observation
        .objects
        .iter()
        .map(|o| o.object_id)
        .collect::<BTreeSet<_>>();
    let bound_ids = observation.labels.values().collect::<BTreeSet<_>>();
    if ids.len() != observation.objects.len()
        || bound_ids.len() != observation.labels.len()
        || observation
            .labels
            .keys()
            .any(|label| !case.scenario.cards.iter().any(|c| &c.label == label))
    {
        return CheckResult::Inconclusive {
            reason: IncompleteReason::InvalidEvidence { detail: "object IDs and label bindings must be unique and labels must belong to the scenario".into() },
        };
    }
    let guards = check_assertions(&case.guards, observation);
    if guards != CheckResult::Satisfied {
        return CheckResult::Inconclusive {
            reason: IncompleteReason::GuardNotReached {
                detail: format!("{guards:?}"),
            },
        };
    }
    check_assertions(&case.assertions, observation)
}

fn check_assertions(assertions: &[Assertion], observation: &Observation) -> CheckResult {
    let mut failures = Vec::new();
    for assertion in assertions {
        let result = measure(&assertion.predicate, observation)
            .map(|value| value == expected_value(&assertion.predicate));
        match result {
            None => {
                return CheckResult::Inconclusive {
                    reason: IncompleteReason::MissingObservation {
                        assertion_id: assertion.id.clone(),
                    },
                }
            }
            Some(false) => failures.push(assertion.id.clone()),
            Some(true) => {}
        }
    }
    if failures.is_empty() {
        CheckResult::Satisfied
    } else {
        CheckResult::Violated {
            assertion_ids: failures,
        }
    }
}
