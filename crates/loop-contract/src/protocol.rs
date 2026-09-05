use crate::*;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub enum ProtocolVersion {
    #[serde(rename = "coworld-improvement-v1")]
    V1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ExecutionRequest {
    pub protocol: ProtocolVersion,
    pub corpus_path: String,
    pub corpus_sha256: ContentHash,
    pub scenario: Scenario,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct StepEvidence {
    pub operation_index: usize,
    pub state_sha256: ContentHash,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ExecutionOutcome {
    Completed {
        observation: Observation,
        steps: Vec<StepEvidence>,
    },
    Inconclusive {
        reason: IncompleteReason,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ExecutionEvidence {
    pub protocol: ProtocolVersion,
    pub request_id: ContentHash,
    pub binary_sha256: ContentHash,
    /// Workspace declaration only; overrides are identified by the binary and build record.
    pub declared_phase_revision: String,
    pub outcome: ExecutionOutcome,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum Repeatability {
    Verified,
    Diverged,
    Inconclusive,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct EvaluationReceipt {
    pub protocol: ProtocolVersion,
    pub case_id: ContentHash,
    pub corpus_sha256: ContentHash,
    pub worker_sha256: ContentHash,
    pub checker_sha256: ContentHash,
    pub evidence_sha256: Vec<ContentHash>,
    pub repeatability: Repeatability,
    pub result: CheckResult,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ReductionReceipt {
    pub original_case_id: ContentHash,
    pub reduced_case_id: ContentHash,
    pub predicate: String,
    pub original_cards: usize,
    pub reduced_cards: usize,
    pub original_operations: usize,
    pub reduced_operations: usize,
    pub evaluations: u32,
    pub budget: u32,
    pub search: ReductionSearch,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ReductionSearch {
    SingleDeletionFixedPoint,
    BudgetExhausted,
}

/// Freeze this plan before repair. Hold-outs are separately selected cases, not a pass count.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct AcceptancePlan {
    pub case_id: ContentHash,
    pub regression_case_ids: Vec<ContentHash>,
    pub holdout_case_ids: Vec<ContentHash>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ReviewDecision {
    Approve,
    Reject,
}

/// A review attestation, not a cryptographic identity claim. The operator owns reviewer trust.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ReviewRecord {
    pub plan_id: ContentHash,
    pub baseline_receipt_id: ContentHash,
    pub candidate_receipt_id: ContentHash,
    pub reviewer: String,
    pub rationale: String,
    pub decision: ReviewDecision,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum AcceptanceDecision {
    Accepted {
        plan_id: ContentHash,
        baseline_receipt_id: ContentHash,
        candidate_receipt_id: ContentHash,
        gate_receipt_ids: Vec<ContentHash>,
        review_id: ContentHash,
    },
    Rejected {
        reasons: Vec<String>,
    },
}

pub fn accept(
    case: &CaseSpec,
    plan: &AcceptancePlan,
    baseline: &EvaluationReceipt,
    candidate: &EvaluationReceipt,
    gates: &[EvaluationReceipt],
    review: &ReviewRecord,
) -> Result<AcceptanceDecision, serde_json::Error> {
    let mut reasons = Vec::new();
    let case_id = digest(case)?;
    let plan_id = digest(plan)?;
    let baseline_id = digest(baseline)?;
    let candidate_id = digest(candidate)?;
    if case.validate().is_err() {
        reasons.push("case is invalid".into());
    }
    if matches!(case.justification, Justification::Observation { .. }) {
        reasons.push("observational evidence is not a conformance expectation".into());
    }
    if plan.case_id != case_id || baseline.case_id != case_id || candidate.case_id != case_id {
        reasons.push("case or expectation changed between baseline and candidate".into());
    }
    if !matches!(baseline.result, CheckResult::Violated { .. })
        || baseline.repeatability != Repeatability::Verified
    {
        reasons.push("baseline does not reproduce a deterministic violation".into());
    }
    if candidate.result != CheckResult::Satisfied
        || candidate.repeatability != Repeatability::Verified
    {
        reasons.push("candidate did not satisfy the frozen expectation reproducibly".into());
    }
    if baseline.corpus_sha256 != candidate.corpus_sha256
        || baseline.checker_sha256 != candidate.checker_sha256
    {
        reasons.push("corpus or checker changed with the repair".into());
    }
    if baseline.worker_sha256 == candidate.worker_sha256 {
        reasons.push("baseline and candidate are the same worker".into());
    }
    if plan.regression_case_ids.is_empty() || plan.holdout_case_ids.is_empty() {
        reasons.push("plan requires both regression and held-out cases".into());
    }
    let mut accepted_gates = Vec::new();
    let mut distinct = BTreeSet::from([&plan.case_id]);
    for id in plan
        .regression_case_ids
        .iter()
        .chain(&plan.holdout_case_ids)
    {
        if !distinct.insert(id) {
            reasons.push("target, regressions and hold-outs must be disjoint".into());
        }
        if let Some(gate) = gates.iter().find(|g| {
            &g.case_id == id
                && g.result == CheckResult::Satisfied
                && g.repeatability == Repeatability::Verified
                && g.worker_sha256 == candidate.worker_sha256
                && g.checker_sha256 == candidate.checker_sha256
                && g.corpus_sha256 == candidate.corpus_sha256
        }) {
            accepted_gates.push(digest(gate)?);
        } else {
            reasons.push(format!("missing passing candidate gate for {id}"));
        }
    }
    if review.plan_id != plan_id
        || review.baseline_receipt_id != baseline_id
        || review.candidate_receipt_id != candidate_id
    {
        reasons.push("review is not bound to this plan and these evaluations".into());
    }
    if review.decision != ReviewDecision::Approve
        || review.reviewer.trim().is_empty()
        || review.reviewer == case.author
        || review.rationale.trim().is_empty()
    {
        reasons.push("independent approval and rationale are required".into());
    }
    Ok(if reasons.is_empty() {
        AcceptanceDecision::Accepted {
            plan_id,
            baseline_receipt_id: baseline_id,
            candidate_receipt_id: candidate_id,
            gate_receipt_ids: accepted_gates,
            review_id: digest(review)?,
        }
    } else {
        AcceptanceDecision::Rejected { reasons }
    })
}

/// One registry owns the exported schemas and the diagrams of process boundaries.
pub fn contract_artifacts() -> BTreeMap<String, String> {
    let mut files = BTreeMap::new();
    let mut graph = String::from("flowchart LR\n");
    let mut sequence = String::from("sequenceDiagram\n");
    macro_rules! boundary {
        ($ty:ty, $source:ident, $destination:ident) => {{
            let name = stringify!($ty);
            let schema = schemars::schema_for!($ty);
            files.insert(
                format!("{name}.schema.json"),
                serde_json::to_string_pretty(&schema).expect("schema serializes") + "\n",
            );
            graph.push_str(&format!(
                "    {} -->|{}| {}\n",
                stringify!($source),
                name,
                stringify!($destination)
            ));
            sequence.push_str(&format!(
                "    {}->>{}: {}\n",
                stringify!($source),
                stringify!($destination),
                name
            ));
        }};
    }
    boundary!(CaseSpec, Author, Coordinator);
    boundary!(ExecutionRequest, Coordinator, PhaseWorker);
    boundary!(ExecutionEvidence, PhaseWorker, Coordinator);
    boundary!(EvaluationReceipt, Coordinator, EvidenceStore);
    boundary!(ReductionReceipt, Reducer, EvidenceStore);
    boundary!(AcceptancePlan, Operator, Coordinator);
    boundary!(ReviewRecord, Reviewer, Coordinator);
    boundary!(AcceptanceDecision, Coordinator, EvidenceStore);
    boundary!(BuildRecord, Builder, Coordinator);
    boundary!(CaseAttribution, Coordinator, CaseLibrary);
    files.insert("architecture.mmd".into(), graph);
    files.insert("message-flow.mmd".into(), sequence);
    files
}
