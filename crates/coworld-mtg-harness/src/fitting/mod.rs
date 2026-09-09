//! Bounded external-observation fitting. A witness covers only the declared projection;
//! failure under one reconstructed hidden state is an issue candidate, not a rules proof.
mod search;
mod source;

use crate::{
    corpus::{load_manifest, load_phase_runtime},
    io::{decoded_json_bytes, read_resource, sha256, verify_hash, write_json_atomic},
};
use anyhow::{bail, Result};
pub use search::search_game;
use serde::{Deserialize, Serialize};
use serde_json::Value;
pub use source::extract_game;
use std::{collections::BTreeMap, path::PathBuf};

pub const FIT_SCHEMA: &str = "coworld-17lands-guided-fit-v1";

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "snake_case")]
pub enum Boundary {
    EndOfTurn,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub struct MilestoneKey {
    pub turn_owner: u8,
    pub turn_index: u32,
    pub boundary: Boundary,
    pub observed_player: u8,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum FieldDisposition {
    Enforced,
    Informational,
    Unsupported,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SourceField {
    pub column: String,
    pub raw: String,
    pub milestone: Option<MilestoneKey>,
    pub disposition: FieldDisposition,
    pub reason: String,
    pub projection: Option<String>,
    pub expected: Option<Value>,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum IssueKind {
    InputMapping,
    UnsupportedInput,
    UnsupportedProjection,
    ProjectionContradiction,
    RuntimeIdentityGap,
    RuntimeSetup,
    OfferedActionFailure,
    InvariantFailure,
    BudgetExhausted,
    UnsupportedBoundary,
    NoWitnessUnderAssumptions,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum FitStatus {
    InputIssue,
    MatchedSupportedProjection,
    BudgetExhausted,
    UnsupportedBoundary,
    NoWitnessUnderAssumptions,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct IssueCandidate {
    pub kind: IssueKind,
    pub detail: String,
    pub source_columns: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub evidence: Option<Value>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FitInput {
    pub seed: u64,
    pub schema: String,
    pub game_index: u64,
    pub on_play: Option<bool>,
    pub mulligans: [Option<u32>; 2],
    pub source_sha256: String,
    pub cards_mapping_sha256: String,
    pub fields: Vec<SourceField>,
    pub milestones: Vec<MilestoneKey>,
    pub decks: [Vec<String>; 2],
    pub libraries: [Vec<String>; 2],
    pub assumptions: Vec<String>,
    pub issues: Vec<IssueCandidate>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FitLimits {
    pub nodes: u64,
    pub max_actions: usize,
}
impl Default for FitLimits {
    fn default() -> Self {
        Self {
            nodes: 10_000,
            max_actions: 128,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FitAction {
    pub seat: u8,
    pub action: phase_bridge::GameAction,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FitResult {
    pub seed: u64,
    pub schema: String,
    pub status: FitStatus,
    pub nodes: u64,
    pub matched_prefix_backtracks: u64,
    pub elapsed_millis: u128,
    pub milestones_fitted: usize,
    pub milestones_total: usize,
    pub fully_covered_milestones: usize,
    pub witness: Vec<FitAction>,
    pub issues: Vec<IssueCandidate>,
    pub limits: FitLimits,
    pub assumptions: Vec<String>,
    pub search: String,
    pub manifest_id: String,
    pub phase_revision: String,
    pub source_sha256: String,
    pub cards_mapping_sha256: String,
    pub input_sha256: String,
}

pub struct FitOptions {
    pub manifest_uri: String,
    pub replay_data: String,
    pub replay_sha256: String,
    pub cards_csv: String,
    pub cards_csv_sha256: String,
    pub game_index: u64,
    pub turn_pairs: u32,
    pub opponent_filler: String,
    pub output_dir: PathBuf,
    pub limits: FitLimits,
}

pub async fn fit_17lands(options: FitOptions) -> Result<FitResult> {
    if options.turn_pairs == 0
        || options.limits.nodes == 0
        || options.limits.max_actions == 0
        || options.limits.max_actions > 512
    {
        bail!("positive turn/node/action limits required; max-actions cannot exceed 512");
    }
    let source = read_resource(&options.replay_data).await?;
    verify_hash("17Lands replay", &source, Some(&options.replay_sha256))?;
    let mapping = read_resource(&options.cards_csv).await?;
    verify_hash(
        "official cards mapping",
        &mapping,
        Some(&options.cards_csv_sha256),
    )?;
    let mut input = extract_game(
        &decoded_json_bytes(&source)?,
        &mapping,
        options.game_index,
        options.turn_pairs,
        &options.opponent_filler,
    )?;
    input.source_sha256 = sha256(&source);
    input.cards_mapping_sha256 = sha256(&mapping);
    let manifest = load_manifest(&options.manifest_uri).await?;
    let runtime = load_phase_runtime(&options.manifest_uri, &manifest).await?;
    for name in input.decks.iter().flatten() {
        if runtime.canonical_card_name(name).as_deref() != Some(name) {
            input.issues.push(IssueCandidate {
                kind: IssueKind::RuntimeIdentityGap,
                detail: format!(
                    "official name {name:?} does not resolve to the exact runtime face name"
                ),
                source_columns: vec![],
                evidence: None,
            });
        }
    }
    write_json_atomic(&options.output_dir.join("constraints.json"), &input)?;
    let mut result = search_game(&runtime, &input, options.limits)?;
    result.manifest_id = manifest.manifest_id;
    result.input_sha256 = crate::io::canonical_hash(&input)?;
    write_json_atomic(&options.output_dir.join("result.json"), &result)?;
    Ok(result)
}

pub(crate) fn counts(names: &[String]) -> BTreeMap<String, usize> {
    let mut result = BTreeMap::new();
    for name in names {
        *result.entry(name.clone()).or_default() += 1;
    }
    result
}
