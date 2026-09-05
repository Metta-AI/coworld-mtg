//! Attribution is emitted by acceptance, and rendered without an LLM rewriting the facts.
use crate::*;

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum CaseOrigin {
    #[default]
    Authored,
    Evidence {
        artifacts: Vec<ContentHash>,
        explanation: String,
    },
    Derived {
        parent_case_id: ContentHash,
        transformation: String,
    },
}
impl CaseOrigin {
    pub fn is_authored(&self) -> bool {
        matches!(self, Self::Authored)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum PhaseBuild {
    Pinned {
        repository: String,
        revision: String,
    },
    Checkout {
        repository: String,
        checkout: String,
        base_revision: String,
        revision: String,
        source_files: BTreeMap<String, ContentHash>,
        dirty_patch_sha256: ContentHash,
        patch_sha256: ContentHash,
        worktree_clean: bool,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct BuildRecord {
    pub binary_sha256: ContentHash,
    pub harness_revision: String,
    pub harness_source_files: BTreeMap<String, ContentHash>,
    pub phase: PhaseBuild,
    pub cargo_lock_sha256: ContentHash,
    pub command: Vec<String>,
    pub builder_sha256: ContentHash,
    pub build_environment: BTreeMap<String, String>,
    pub compiler: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct RepairProvenance {
    pub repository: String,
    pub base_revision: String,
    pub revision: String,
    pub patch_sha256: ContentHash,
    pub baseline_build_sha256: ContentHash,
    pub candidate_build_sha256: ContentHash,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct AttributedGate {
    pub case: CaseSpec,
    pub receipt: EvaluationReceipt,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct CaseAttribution {
    pub protocol: ProtocolVersion,
    pub case: CaseSpec,
    pub plan: AcceptancePlan,
    pub baseline: EvaluationReceipt,
    pub candidate: EvaluationReceipt,
    pub baseline_execution: ExecutionEvidence,
    pub candidate_execution: ExecutionEvidence,
    pub gates: Vec<AttributedGate>,
    pub repair: RepairProvenance,
    pub review: ReviewRecord,
    pub acceptance: AcceptanceDecision,
}

/// One measurement function serves both checking and reporting.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(
    tag = "kind",
    content = "value",
    rename_all = "snake_case",
    deny_unknown_fields
)]
pub enum Measurement {
    Integer(i64),
    Boolean(bool),
    Zone(CardZone),
}

pub fn expected_value(predicate: &Predicate) -> Measurement {
    match predicate {
        Predicate::Life { equals, .. } => Measurement::Integer(i64::from(*equals)),
        Predicate::Zone { equals, .. } => Measurement::Zone(*equals),
        Predicate::Tapped { equals, .. }
        | Predicate::Prepared { equals, .. }
        | Predicate::OfferedCastSpell { equals, .. } => Measurement::Boolean(*equals),
        Predicate::PlusOneCounters { equals, .. } | Predicate::ZoneCount { equals, .. } => {
            Measurement::Integer(i64::from(*equals))
        }
    }
}
pub fn measure(predicate: &Predicate, observation: &Observation) -> Option<Measurement> {
    let object = |label: &String| {
        observation.labels.get(label).and_then(|id| {
            observation
                .objects
                .iter()
                .find(|object| object.object_id == *id)
        })
    };
    match predicate {
        Predicate::Life { seat, .. } => Some(Measurement::Integer(i64::from(
            observation.life[seat.index()],
        ))),
        Predicate::Zone { object: label, .. } => object(label).map(|o| Measurement::Zone(o.zone)),
        Predicate::Tapped { object: label, .. } => {
            object(label).map(|o| Measurement::Boolean(o.tapped))
        }
        Predicate::PlusOneCounters { object: label, .. } => {
            object(label).map(|o| Measurement::Integer(i64::from(o.plus_one_counters)))
        }
        Predicate::Prepared { object: label, .. } => {
            object(label).map(|o| Measurement::Boolean(o.prepared))
        }
        Predicate::OfferedCastSpell {
            object: label,
            seat,
            ..
        } => object(label).map(|o| Measurement::Boolean(o.cast_spell_offered_to.contains(seat))),
        Predicate::ZoneCount {
            seat, zone, name, ..
        } => i64::try_from(
            observation
                .objects
                .iter()
                .filter(|o| o.owner == *seat && o.zone == *zone && o.name == *name)
                .count(),
        )
        .ok()
        .map(Measurement::Integer),
    }
}

fn cell(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('|', "&#124;")
        .replace(['\n', '\r'], " ")
}
fn value_text(value: Option<Measurement>) -> String {
    match value {
        Some(Measurement::Integer(value)) => value.to_string(),
        Some(Measurement::Boolean(value)) => value.to_string(),
        Some(Measurement::Zone(value)) => format!("{value:?}").to_lowercase(),
        None => "unobserved".into(),
    }
}

pub fn render_case_note(record: &CaseAttribution) -> Result<String, String> {
    let receipts = record
        .gates
        .iter()
        .map(|g| g.receipt.clone())
        .collect::<Vec<_>>();
    let expected_acceptance = accept(
        &record.case,
        &record.plan,
        &record.baseline,
        &record.candidate,
        &receipts,
        &record.review,
    )
    .map_err(|e| e.to_string())?;
    if !matches!(expected_acceptance, AcceptanceDecision::Accepted { .. })
        || expected_acceptance != record.acceptance
    {
        return Err("attribution is not bound to a valid acceptance decision".into());
    }
    for gate in &record.gates {
        if digest(&gate.case).map_err(|e| e.to_string())? != gate.receipt.case_id {
            return Err("gate title and case do not match receipt".into());
        }
    }
    let mut observations = Vec::new();
    for (receipt, execution) in [
        (&record.baseline, &record.baseline_execution),
        (&record.candidate, &record.candidate_execution),
    ] {
        let hash = digest(execution).map_err(|e| e.to_string())?;
        let ExecutionOutcome::Completed { observation, .. } = &execution.outcome else {
            return Err("attribution requires completed execution".into());
        };
        if receipt.evidence_sha256 != vec![hash; 2]
            || execution.binary_sha256 != receipt.worker_sha256
            || check(&record.case, observation) != receipt.result
        {
            return Err("attribution observations do not support its receipt".into());
        }
        observations.push(observation);
    }
    let case_id = digest(&record.case).map_err(|e| e.to_string())?;
    let attribution_id = digest(record).map_err(|e| e.to_string())?;
    let acceptance_id = digest(&record.acceptance).map_err(|e| e.to_string())?;
    let mut note = format!("# {}\n\nGenerated from [attribution.json](attribution.json). Edit the source case or review in a new experiment; this note is generated.\n\nAccepted repair for case `{case_id}`.\n\n", cell(&record.case.title));
    match &record.case.origin {
        CaseOrigin::Authored => note.push_str("Origin: an authored scenario.\n\n"),
        CaseOrigin::Evidence {
            artifacts,
            explanation,
        } => note.push_str(&format!(
            "Origin: {}. Evidence artifacts: {}.\n\n",
            cell(explanation),
            artifacts
                .iter()
                .map(|id| format!("`{id}`"))
                .collect::<Vec<_>>()
                .join(", ")
        )),
        CaseOrigin::Derived {
            parent_case_id,
            transformation,
        } => note.push_str(&format!(
            "Origin: case `{parent_case_id}`. Transformation: {}.\n\n",
            cell(transformation)
        )),
    }
    note.push_str(&format!(
        "Cards: {}. The setup contains {} cards and {} operations.\n\n",
        record
            .case
            .scenario
            .cards
            .iter()
            .map(|card| cell(&card.name))
            .collect::<Vec<_>>()
            .join(", "),
        record.case.scenario.cards.len(),
        record.case.scenario.operations.len()
    ));
    note.push_str("## Observed result\n\nEach worker ran twice. Reachability guards passed before judging these assertions.\n\n| Assertion | Expected | Baseline | Candidate |\n| --- | --- | --- | --- |\n");
    for assertion in &record.case.assertions {
        note.push_str(&format!(
            "| {} | {} | {} | {} |\n",
            cell(&assertion.id),
            value_text(Some(expected_value(&assertion.predicate))),
            value_text(measure(&assertion.predicate, observations[0])),
            value_text(measure(&assertion.predicate, observations[1]))
        ));
    }
    note.push_str("\n## Basis for the expectation\n\n");
    match &record.case.justification {
        Justification::Rules { citations } => {
            for citation in citations {
                note.push_str(&format!(
                    "- {} — {}. Source: <{}>\n",
                    cell(&citation.reference),
                    cell(&citation.statement),
                    cell(&citation.source)
                ));
            }
        }
        Justification::Invariant { specification } => {
            note.push_str(&format!("{}\n", cell(specification)))
        }
        Justification::Observation { .. } => {
            return Err("observation-only cases cannot be accepted".into())
        }
    }
    note.push_str(&format!("\n## Repair and review\n\nRepository: <{}>. Commit `{}` from base `{}`. [Recorded patch](repair.patch), SHA-256 `{}`.\n\nReviewer: {}. {}\n\n", cell(&record.repair.repository), record.repair.revision, record.repair.base_revision, record.repair.patch_sha256, cell(&record.review.reviewer), cell(&record.review.rationale)));
    note.push_str(
        "## Accumulated regression evidence\n\n| Role | Case | Result |\n| --- | --- | --- |\n",
    );
    for gate in &record.gates {
        let role = if record.plan.holdout_case_ids.contains(&gate.receipt.case_id) {
            "Held-out case"
        } else {
            "Regression"
        };
        note.push_str(&format!(
            "| {role} | {} (`{}`) | {:?} |\n",
            cell(&gate.case.title),
            gate.receipt.case_id,
            gate.receipt.result
        ));
    }
    note.push_str(&format!("\n## Stable attribution\n\n- Case: `{case_id}`\n- Acceptance: `{acceptance_id}`\n- Attribution: `{attribution_id}`\n- Baseline worker: `{}`\n- Candidate worker: `{}`\n- Checker: `{}`\n- Corpus: `{}`\n\nThis records evidence for the stated scenarios. It does not establish correctness outside them.\n", record.baseline.worker_sha256, record.candidate.worker_sha256, record.candidate.checker_sha256, record.candidate.corpus_sha256));
    Ok(note)
}
