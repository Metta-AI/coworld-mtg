//! A recorded improvement run. This describes evidence and causality, not a scheduler.
//! JSON artifacts retain the existing `digest` identity; binary artifacts use `hash_bytes`.
use crate::*;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
pub enum FactoryVersion {
    #[serde(rename = "software-factory-v1")]
    V1,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ProgramTarget {
    pub name: String,
    pub repository: String,
    pub baseline_revision: String,
}

/// Domain build attestations (including MTG BuildRecord) remain separate artifacts.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct FactoryBuild {
    pub program: String,
    pub source_revision: String,
    pub binary_sha256: ContentHash,
    pub command: Vec<String>,
    pub environment: BTreeMap<String, String>,
    pub attestation_id: Option<ContentHash>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum FeedbackAdapter {
    Opaque,
    MtgEvaluationV1,
}

/// External policies are immutable artifacts. Their authority and semantic adequacy
/// belong to the operator; the shared validator verifies their recorded binding only.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum DecisionPolicy {
    MtgConformanceV1,
    External {
        policy_id: ContentHash,
        scope: String,
        attestation_id: ContentHash,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ExternalDecisionAttestation {
    pub policy_id: ContentHash,
    pub scope: String,
    pub decision_id: ContentHash,
    pub plan_id: ContentHash,
    pub change_id: ContentHash,
}

/// Imported evidence has logical replay order, not invented historical timestamps.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum ReplayRecording {
    Live,
    Imported { description: String },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum FactoryRunStatus {
    Running,
    Completed,
    Failed,
    Cancelled,
}

#[derive(
    Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize, JsonSchema,
)]
#[serde(rename_all = "snake_case")]
pub enum FactoryStage {
    Sources,
    Cases,
    Execute,
    Feedback,
    Reduce,
    Changes,
    Gates,
    Review,
    Decisions,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct FactoryStageSpec {
    pub id: FactoryStage,
    pub title: String,
    pub next: Vec<FactoryStage>,
}

/// The producer supplies this topology; viewers do not implement a competing lifecycle.
pub fn factory_stages() -> Vec<FactoryStageSpec> {
    use FactoryStage::*;
    [
        (Sources, "Source data", vec![Cases]),
        (Cases, "Cases", vec![Execute]),
        (Execute, "Execution", vec![Feedback]),
        (
            Feedback,
            "Feedback",
            vec![Reduce, Changes, Review, Decisions],
        ),
        (Reduce, "Reduction", vec![Execute]),
        (Changes, "Discrete changes", vec![Gates]),
        (Gates, "Frozen acceptance checks", vec![Execute, Review]),
        (Review, "Independent review", vec![Decisions]),
        (Decisions, "Recorded decisions", vec![]),
    ]
    .into_iter()
    .map(|(id, title, next)| FactoryStageSpec {
        id,
        title: title.into(),
        next,
    })
    .collect()
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ArtifactHashMode {
    CanonicalJson,
    Bytes,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct FactoryArtifact {
    /// A portable path relative to the directory containing replay.json.
    pub path: String,
    pub media_type: String,
    pub hash_mode: ArtifactHashMode,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct SourceProvenance {
    pub snapshot_id: ContentHash,
    pub provider: String,
    pub url: String,
    pub retrieved_at: String,
    pub description: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct SourceRecordSelection {
    pub source_id: ContentHash,
    pub record_id: String,
}

/// Authentic source records and generated scenarios are deliberately separate claims.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum CaseDerivation {
    Authored {
        author: String,
        description: String,
    },
    SourceDerived {
        source_ids: Vec<ContentHash>,
        source_records: Vec<SourceRecordSelection>,
        recipe: String,
        seed: Option<u64>,
    },
    Reduced {
        parent_case_id: ContentHash,
        reduction_receipt_id: ContentHash,
        recipe: String,
    },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum FactoryExecutionStatus {
    Completed,
    Inconclusive,
    Error,
    Cancelled,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum FeedbackStrength {
    Weak,
    Strong,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum FeedbackResult {
    Satisfied,
    Violated,
    Inconclusive,
}
impl From<&CheckResult> for FeedbackResult {
    fn from(result: &CheckResult) -> Self {
        match result {
            CheckResult::Satisfied => Self::Satisfied,
            CheckResult::Violated { .. } => Self::Violated,
            CheckResult::Inconclusive { .. } => Self::Inconclusive,
        }
    }
}

/// Strength is an evaluator's declaration about this bounded claim, never a voting weight.
/// It does not grant permission to bypass the existing frozen acceptance gate.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct FactoryFeedback {
    pub adapter: FeedbackAdapter,
    pub feedback_id: ContentHash,
    pub case_id: ContentHash,
    pub execution_ids: Vec<String>,
    pub evaluator: String,
    pub evaluator_version: String,
    pub declared_strength: FeedbackStrength,
    pub method: String,
    pub bounded_claim: String,
    pub result: FeedbackResult,
    pub summary: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ComputeMeasurement {
    Measured,
    Estimated,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ComputeUsage {
    pub execution_id: Option<String>,
    pub worker: String,
    pub measurement: ComputeMeasurement,
    /// Missing measurements are unknown, not zero. CPU can exceed wall time.
    pub wall_ms: Option<u64>,
    pub cpu_ms: Option<u64>,
    pub peak_memory_bytes: Option<u64>,
    pub input_tokens: Option<u64>,
    pub output_tokens: Option<u64>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum FactoryEventPayload {
    SourceImported {
        source: SourceProvenance,
    },
    CaseRegistered {
        case_id: ContentHash,
        title: String,
        derivation: CaseDerivation,
    },
    BuildRecorded {
        build_id: ContentHash,
        build: FactoryBuild,
    },
    ExecutionStarted {
        execution_id: String,
        case_id: ContentHash,
        request_id: ContentHash,
        build_id: ContentHash,
        change_id: Option<ContentHash>,
    },
    ExecutionFinished {
        execution_id: String,
        status: FactoryExecutionStatus,
        evidence_id: Option<ContentHash>,
        trace_ids: Vec<ContentHash>,
        detail: Option<String>,
    },
    FeedbackRecorded {
        feedback: FactoryFeedback,
    },
    /// The change ID is the patch artifact's existing content hash.
    ChangeProposed {
        change_id: ContentHash,
        description: String,
        base_revision: String,
        motivating_feedback_ids: Vec<ContentHash>,
    },
    AcceptancePlanFrozen {
        plan_id: ContentHash,
        plan: AcceptancePlan,
    },
    ReviewRecorded {
        review_id: ContentHash,
        review: ReviewRecord,
    },
    DecisionRecorded {
        policy: DecisionPolicy,
        decision_id: ContentHash,
        change_id: ContentHash,
        plan_id: ContentHash,
        decision: AcceptanceDecision,
    },
    ComputeRecorded {
        usage: ComputeUsage,
    },
}
impl FactoryEventPayload {
    /// Compute is attributed by its envelope to the stage consuming the resources.
    pub fn stage(&self) -> Option<FactoryStage> {
        use FactoryEventPayload::*;
        Some(match self {
            SourceImported { .. } => FactoryStage::Sources,
            CaseRegistered {
                derivation: CaseDerivation::Reduced { .. },
                ..
            } => FactoryStage::Reduce,
            CaseRegistered { .. } => FactoryStage::Cases,
            BuildRecorded { .. } | ExecutionStarted { .. } | ExecutionFinished { .. } => {
                FactoryStage::Execute
            }
            FeedbackRecorded { .. } => FactoryStage::Feedback,
            ChangeProposed { .. } => FactoryStage::Changes,
            AcceptancePlanFrozen { .. } => FactoryStage::Gates,
            ReviewRecorded { .. } => FactoryStage::Review,
            DecisionRecorded { .. } => FactoryStage::Decisions,
            ComputeRecorded { .. } => return None,
        })
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct FactoryEvent {
    pub sequence: u64,
    /// Null for imported events or when timing was not measured.
    pub elapsed_ms: Option<u64>,
    pub stage: FactoryStage,
    pub payload: FactoryEventPayload,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct FactoryReplay {
    pub version: FactoryVersion,
    pub run_id: String,
    pub title: String,
    pub target: ProgramTarget,
    pub recording: ReplayRecording,
    pub status: FactoryRunStatus,
    pub stages: Vec<FactoryStageSpec>,
    pub artifacts: BTreeMap<ContentHash, FactoryArtifact>,
    pub events: Vec<FactoryEvent>,
}

fn require(condition: bool, message: &str) -> Result<(), String> {
    if condition {
        Ok(())
    } else {
        Err(message.into())
    }
}
fn nonempty(value: &str) -> bool {
    !value.trim().is_empty()
}
fn identity(id: &ContentHash, record: &impl Serialize) -> Result<(), String> {
    require(
        &digest(record).map_err(|e| e.to_string())? == id,
        "record content hash does not match its identity",
    )
}

impl FactoryReplay {
    /// Validate a live prefix or a terminal run without requiring filesystem access.
    /// This verifies recording structure, not evaluator correctness or operator identity.
    pub fn validate(&self) -> Result<(), String> {
        require(
            nonempty(&self.run_id) && nonempty(&self.title),
            "run ID and title are required",
        )?;
        require(
            nonempty(&self.target.name)
                && nonempty(&self.target.repository)
                && nonempty(&self.target.baseline_revision),
            "target identity is incomplete",
        )?;
        if let ReplayRecording::Imported { description } = &self.recording {
            require(
                nonempty(description),
                "imported evidence requires its provenance description",
            )?;
        }
        require(
            self.stages == factory_stages(),
            "stage topology differs from the versioned contract",
        )?;
        let mut paths = BTreeSet::new();
        for artifact in self.artifacts.values() {
            require(
                !artifact.path.is_empty()
                    && !artifact.path.contains(['\\', ':', '?', '#', '%'])
                    && artifact
                        .path
                        .split('/')
                        .all(|p| !p.is_empty() && p != "." && p != "..")
                    && paths.insert(&artifact.path),
                "artifact paths must be unique, portable relative paths",
            )?;
            require(
                nonempty(&artifact.media_type),
                "artifact media type is required",
            )?;
        }
        let artifact = |id: &ContentHash| {
            require(
                self.artifacts.contains_key(id),
                "referenced artifact is absent from manifest",
            )
        };
        let mut sources = BTreeSet::new();
        let mut cases = BTreeSet::new();
        let mut builds = BTreeMap::new();
        let mut executions = BTreeMap::new();
        let mut finished = BTreeSet::new();
        let mut feedbacks = BTreeMap::new();
        let mut changes = BTreeSet::new();
        let mut plans = BTreeMap::new();
        let mut reviews = BTreeMap::new();
        let mut decisions = BTreeSet::new();
        let mut elapsed = None;
        for (index, event) in self.events.iter().enumerate() {
            require(
                event.sequence == index as u64,
                "event sequences must be contiguous and start at zero",
            )?;
            require(
                event
                    .payload
                    .stage()
                    .is_none_or(|stage| stage == event.stage),
                "event stage does not match its payload",
            )?;
            if let Some(value) = event.elapsed_ms {
                require(
                    elapsed.is_none_or(|previous| value >= previous),
                    "elapsed event time moved backwards",
                )?;
                require(
                    matches!(self.recording, ReplayRecording::Live),
                    "imported events cannot invent elapsed execution times",
                )?;
                elapsed = Some(value);
            }
            use FactoryEventPayload::*;
            match &event.payload {
                SourceImported { source } => {
                    artifact(&source.snapshot_id)?;
                    require(
                        sources.insert(&source.snapshot_id),
                        "source was imported twice",
                    )?;
                    require(
                        [
                            &source.provider,
                            &source.url,
                            &source.retrieved_at,
                            &source.description,
                        ]
                        .iter()
                        .all(|s| nonempty(s)),
                        "source provenance is incomplete",
                    )?;
                }
                CaseRegistered {
                    case_id,
                    title,
                    derivation,
                } => {
                    artifact(case_id)?;
                    require(
                        nonempty(title) && !cases.contains(case_id),
                        "case title is empty or case is duplicated",
                    )?;
                    match derivation {
                        CaseDerivation::Authored {
                            author,
                            description,
                        } => require(
                            nonempty(author) && nonempty(description),
                            "authored case provenance is incomplete",
                        )?,
                        CaseDerivation::SourceDerived {
                            source_ids,
                            source_records,
                            recipe,
                            ..
                        } => {
                            require(
                                !source_ids.is_empty() && nonempty(recipe),
                                "derived case requires sources and a recipe",
                            )?;
                            require(
                                source_ids.iter().all(|id| sources.contains(id)),
                                "case source must be imported before derivation",
                            )?;
                            require(
                                source_records.iter().all(|record| {
                                    source_ids.contains(&record.source_id)
                                        && nonempty(&record.record_id)
                                }),
                                "selected record must identify one of the case sources",
                            )?;
                        }
                        CaseDerivation::Reduced {
                            parent_case_id,
                            reduction_receipt_id,
                            recipe,
                        } => {
                            require(
                                cases.contains(parent_case_id) && nonempty(recipe),
                                "reduction must follow its parent case and identify its recipe",
                            )?;
                            artifact(reduction_receipt_id)?;
                        }
                    }
                    cases.insert(case_id);
                }
                BuildRecorded { build_id, build } => {
                    artifact(build_id)?;
                    identity(build_id, build)?;
                    require(
                        nonempty(&build.program)
                            && nonempty(&build.source_revision)
                            && !build.command.is_empty(),
                        "build identity and recipe are incomplete",
                    )?;
                    if let Some(id) = &build.attestation_id {
                        artifact(id)?;
                    }
                    require(
                        builds.insert(build_id, build).is_none(),
                        "build was recorded twice",
                    )?;
                }
                ExecutionStarted {
                    execution_id,
                    case_id,
                    request_id,
                    build_id,
                    change_id,
                } => {
                    artifact(request_id)?;
                    require(
                        nonempty(execution_id) && !executions.contains_key(execution_id),
                        "execution ID is empty or duplicated",
                    )?;
                    require(
                        cases.contains(case_id) && builds.contains_key(build_id),
                        "execution must follow its case and build",
                    )?;
                    if let Some(change_id) = change_id {
                        require(
                            changes.contains(change_id),
                            "candidate execution must follow its proposed change",
                        )?;
                    }
                    executions.insert(execution_id, (case_id, build_id, change_id, event.sequence));
                }
                ExecutionFinished {
                    execution_id,
                    status,
                    evidence_id,
                    trace_ids,
                    detail,
                } => {
                    require(
                        executions.contains_key(execution_id) && finished.insert(execution_id),
                        "execution must start before finishing exactly once",
                    )?;
                    if let Some(id) = evidence_id {
                        artifact(id)?;
                    }
                    for id in trace_ids {
                        artifact(id)?;
                    }
                    match status {
                        FactoryExecutionStatus::Completed
                        | FactoryExecutionStatus::Inconclusive => require(
                            evidence_id.is_some(),
                            "completed or inconclusive execution requires evidence",
                        )?,
                        FactoryExecutionStatus::Error | FactoryExecutionStatus::Cancelled => {
                            require(
                                detail.as_ref().is_some_and(|s| nonempty(s)),
                                "failed or cancelled execution requires an explanation",
                            )?
                        }
                    }
                }
                FeedbackRecorded { feedback } => {
                    artifact(&feedback.feedback_id)?;
                    require(
                        cases.contains(&feedback.case_id)
                            && !feedbacks.contains_key(&feedback.feedback_id),
                        "feedback case is absent or feedback is duplicated",
                    )?;
                    require(
                        [
                            &feedback.evaluator,
                            &feedback.evaluator_version,
                            &feedback.method,
                            &feedback.bounded_claim,
                            &feedback.summary,
                        ]
                        .iter()
                        .all(|s| nonempty(s)),
                        "feedback must identify evaluator, method, bounded claim and summary",
                    )?;
                    let mut distinct = BTreeSet::new();
                    for id in &feedback.execution_ids {
                        require(
                            distinct.insert(id)
                                && finished.contains(id)
                                && executions.get(id).is_some_and(|e| e.0 == &feedback.case_id),
                            "feedback executions must be distinct, finished and bound to its case",
                        )?;
                    }
                    feedbacks.insert(&feedback.feedback_id, feedback);
                }
                ChangeProposed {
                    change_id,
                    description,
                    base_revision,
                    motivating_feedback_ids,
                } => {
                    artifact(change_id)?;
                    require(
                        changes.insert(change_id)
                            && nonempty(description)
                            && base_revision == &self.target.baseline_revision,
                        "change must be unique and describe its target baseline",
                    )?;
                    require(
                        !motivating_feedback_ids.is_empty()
                            && motivating_feedback_ids
                                .iter()
                                .all(|id| feedbacks.contains_key(id)),
                        "change must identify previously recorded motivating feedback",
                    )?;
                }
                AcceptancePlanFrozen { plan_id, plan } => {
                    artifact(plan_id)?;
                    identity(plan_id, plan)?;
                    let ids = std::iter::once(&plan.case_id)
                        .chain(&plan.regression_case_ids)
                        .chain(&plan.holdout_case_ids)
                        .collect::<Vec<_>>();
                    require(
                        ids.iter().all(|id| cases.contains(id))
                            && ids.iter().collect::<BTreeSet<_>>().len() == ids.len(),
                        "plan must identify registered, disjoint cases",
                    )?;
                    require(
                        plans.insert(plan_id, (plan, event.sequence)).is_none(),
                        "acceptance plan was frozen twice",
                    )?;
                }
                ReviewRecorded { review_id, review } => {
                    artifact(review_id)?;
                    identity(review_id, review)?;
                    require(
                        plans.contains_key(&review.plan_id)
                            && feedbacks.contains_key(&review.baseline_receipt_id)
                            && feedbacks.contains_key(&review.candidate_receipt_id),
                        "review must follow its plan and both receipts",
                    )?;
                    require(
                        reviews.insert(review_id, review).is_none(),
                        "review was recorded twice",
                    )?;
                }
                DecisionRecorded {
                    policy,
                    decision_id,
                    change_id,
                    plan_id,
                    decision,
                } => {
                    artifact(decision_id)?;
                    identity(decision_id, decision)?;
                    if let DecisionPolicy::External {
                        policy_id,
                        scope,
                        attestation_id,
                    } = policy
                    {
                        artifact(policy_id)?;
                        artifact(attestation_id)?;
                        require(
                            nonempty(scope),
                            "external decision policy requires its bounded scope",
                        )?;
                    }
                    require(
                        changes.contains(change_id)
                            && plans.contains_key(plan_id)
                            && decisions.insert(change_id),
                        "decision requires its unique change and previously frozen plan",
                    )?;
                    if let AcceptanceDecision::Accepted {
                        plan_id: accepted_plan,
                        baseline_receipt_id,
                        candidate_receipt_id,
                        gate_receipt_ids,
                        review_id,
                    } = decision
                    {
                        require(
                            accepted_plan == plan_id,
                            "decision plan differs from its envelope",
                        )?;
                        let review = reviews
                            .get(review_id)
                            .ok_or("accepted decision must follow its recorded review")?;
                        require(
                            &review.plan_id == plan_id
                                && &review.baseline_receipt_id == baseline_receipt_id
                                && &review.candidate_receipt_id == candidate_receipt_id
                                && review.decision == ReviewDecision::Approve,
                            "accepted decision differs from its approving review",
                        )?;
                        let (plan, frozen_at) = plans[plan_id];
                        if matches!(policy, DecisionPolicy::MtgConformanceV1) {
                            for id in std::iter::once(baseline_receipt_id)
                                .chain(std::iter::once(candidate_receipt_id))
                                .chain(gate_receipt_ids)
                            {
                                require(feedbacks.get(id).is_some_and(|f| f.adapter == FeedbackAdapter::MtgEvaluationV1), "MTG acceptance requires explicitly identified MTG evaluation receipts")?;
                            }
                        }
                        let baseline = feedbacks
                            .get(baseline_receipt_id)
                            .ok_or("decision baseline feedback is absent")?;
                        let candidate = feedbacks
                            .get(candidate_receipt_id)
                            .ok_or("decision candidate feedback is absent")?;
                        require(
                            baseline.case_id == plan.case_id
                                && candidate.case_id == plan.case_id
                                && baseline.result == FeedbackResult::Violated
                                && candidate.result == FeedbackResult::Satisfied,
                            "decision feedback does not describe a repaired target violation",
                        )?;
                        let mut expected_cases = plan
                            .regression_case_ids
                            .iter()
                            .chain(&plan.holdout_case_ids)
                            .collect::<BTreeSet<_>>();
                        require(
                            gate_receipt_ids.len() == expected_cases.len()
                                && !plan.regression_case_ids.is_empty()
                                && !plan.holdout_case_ids.is_empty(),
                            "decision requires all regression and holdout gates",
                        )?;
                        for id in std::iter::once(candidate_receipt_id).chain(gate_receipt_ids) {
                            let feedback = feedbacks
                                .get(id)
                                .ok_or("decision gate feedback is absent")?;
                            require(
                                feedback.declared_strength == FeedbackStrength::Strong
                                    && feedback.result == FeedbackResult::Satisfied
                                    && !feedback.execution_ids.is_empty(),
                                "acceptance requires strong, satisfied execution feedback",
                            )?;
                            if id != candidate_receipt_id {
                                require(
                                    expected_cases.remove(&feedback.case_id),
                                    "decision gate is duplicated or outside the plan",
                                )?;
                            }
                            for execution_id in &feedback.execution_ids {
                                let execution = executions[execution_id];
                                require(execution.2.as_ref() == Some(change_id) && execution.3 > frozen_at, "accepted candidate and gate executions must follow the frozen plan and bind to this change")?;
                            }
                        }
                        require(baseline.declared_strength == FeedbackStrength::Strong && !baseline.execution_ids.is_empty() && baseline.execution_ids.iter().all(|id| executions[id].2.is_none()), "accepted baseline must be strong execution feedback without the candidate change")?;
                    }
                }
                ComputeRecorded { usage } => {
                    require(
                        nonempty(&usage.worker)
                            && usage
                                .execution_id
                                .as_ref()
                                .is_none_or(|id| executions.contains_key(id)),
                        "compute must identify its worker and an existing execution when specified",
                    )?;
                    require(
                        usage.wall_ms.is_some()
                            || usage.cpu_ms.is_some()
                            || usage.peak_memory_bytes.is_some()
                            || usage.input_tokens.is_some()
                            || usage.output_tokens.is_some(),
                        "compute record contains no measurements",
                    )?;
                }
            }
        }
        if self.status == FactoryRunStatus::Completed {
            require(
                executions.len() == finished.len(),
                "completed run contains unfinished executions",
            )?;
        }
        Ok(())
    }

    pub fn verify_artifact(&self, id: &ContentHash, bytes: &[u8]) -> Result<(), String> {
        let artifact = self
            .artifacts
            .get(id)
            .ok_or("artifact is absent from manifest")?;
        let actual = match artifact.hash_mode {
            ArtifactHashMode::Bytes => hash_bytes(bytes),
            ArtifactHashMode::CanonicalJson => digest(
                &serde_json::from_slice::<serde_json::Value>(bytes).map_err(|e| e.to_string())?,
            )
            .map_err(|e| e.to_string())?,
        };
        require(
            &actual == id,
            "artifact content does not match its recorded hash",
        )
    }
}

impl FactoryReplay {
    /// Verify a self-contained export. Missing files fail this full audit; `validate`
    /// remains suitable for live runs whose executions have not produced evidence yet.
    /// Only explicitly tagged MTG feedback/policies invoke the MTG semantic adapter.
    pub fn validate_artifacts(
        &self,
        contents: &BTreeMap<ContentHash, Vec<u8>>,
    ) -> Result<(), String> {
        self.validate()?;
        for id in self.artifacts.keys() {
            self.verify_artifact(
                id,
                contents
                    .get(id)
                    .ok_or("manifest artifact file is missing")?,
            )?;
        }
        let mut feedbacks = BTreeMap::new();
        let mut builds = BTreeMap::new();
        let mut starts = BTreeMap::new();
        let mut ends = BTreeMap::new();
        for event in &self.events {
            use FactoryEventPayload::*;
            match &event.payload {
                BuildRecorded { build_id, build } => {
                    let saved: FactoryBuild = artifact_json(contents, build_id)?;
                    require(
                        &saved == build,
                        "embedded build differs from retained artifact",
                    )?;
                    builds.insert(build_id, build);
                }
                ExecutionStarted {
                    execution_id,
                    case_id,
                    request_id,
                    build_id,
                    change_id,
                } => {
                    starts.insert(execution_id, (case_id, request_id, build_id, change_id));
                }
                ExecutionFinished {
                    execution_id,
                    status,
                    evidence_id,
                    ..
                } => {
                    ends.insert(execution_id, (status, evidence_id));
                }
                FeedbackRecorded { feedback } => {
                    feedbacks.insert(&feedback.feedback_id, feedback);
                }
                AcceptancePlanFrozen { plan_id, plan } => {
                    require(
                        artifact_json::<AcceptancePlan>(contents, plan_id)? == *plan,
                        "embedded plan differs from retained artifact",
                    )?;
                }
                ReviewRecorded { review_id, review } => {
                    require(
                        artifact_json::<ReviewRecord>(contents, review_id)? == *review,
                        "embedded review differs from retained artifact",
                    )?;
                }
                DecisionRecorded {
                    decision_id,
                    decision,
                    ..
                } => {
                    require(
                        artifact_json::<AcceptanceDecision>(contents, decision_id)? == *decision,
                        "embedded decision differs from retained artifact",
                    )?;
                }
                _ => {}
            }
        }
        for feedback in feedbacks
            .values()
            .filter(|f| f.adapter == FeedbackAdapter::MtgEvaluationV1)
        {
            let receipt: EvaluationReceipt = artifact_json(contents, &feedback.feedback_id)?;
            let case: CaseSpec = artifact_json(contents, &feedback.case_id)?;
            case.validate()?;
            identity(&feedback.case_id, &case)?;
            identity(&feedback.feedback_id, &receipt)?;
            require(
                receipt.case_id == feedback.case_id
                    && feedback.result == FeedbackResult::from(&receipt.result)
                    && feedback.evaluator_version == receipt.checker_sha256.to_string(),
                "MTG feedback summary differs from its original receipt or checker",
            )?;
            let corpus = contents
                .get(&receipt.corpus_sha256)
                .ok_or("MTG receipt requires retained corpus bytes")?;
            require(
                hash_bytes(corpus) == receipt.corpus_sha256,
                "MTG corpus bytes do not match receipt",
            )?;
            let mut evidence = Vec::new();
            let mut evidence_ids = Vec::new();
            for execution_id in &feedback.execution_ids {
                let (_, request_id, build_id, _) = starts[execution_id];
                let request: ExecutionRequest = artifact_json(contents, request_id)?;
                let build = builds[build_id];
                require(
                    request.scenario == case.scenario
                        && request.corpus_sha256 == receipt.corpus_sha256
                        && build.binary_sha256 == receipt.worker_sha256,
                    "MTG execution request, corpus or worker differs from its case receipt",
                )?;
                if let Some(attestation_id) = &build.attestation_id {
                    let attestation: BuildRecord = artifact_json(contents, attestation_id)?;
                    require(
                        attestation.binary_sha256 == build.binary_sha256,
                        "MTG build attestation identifies a different binary",
                    )?;
                }
                let (status, evidence_id) = ends[execution_id];
                if let Some(id) = evidence_id {
                    let item: ExecutionEvidence = artifact_json(contents, id)?;
                    require(
                        item.request_id == *request_id
                            && item.binary_sha256 == receipt.worker_sha256,
                        "MTG evidence request or worker identity differs from execution",
                    )?;
                    match &item.outcome {
                        ExecutionOutcome::Completed { steps, .. } => {
                            require(*status == FactoryExecutionStatus::Completed && steps.len() == request.scenario.operations.len() && steps.iter().enumerate().all(|(i, step)| step.operation_index == i), "MTG completion status or ordered steps do not account for the request")?;
                        }
                        ExecutionOutcome::Inconclusive { .. } => require(
                            *status == FactoryExecutionStatus::Inconclusive,
                            "MTG incomplete evidence cannot be reported as completed",
                        )?,
                    }
                    evidence_ids.push(id.clone());
                    evidence.push(item);
                }
            }
            require(
                receipt.evidence_sha256 == evidence_ids,
                "MTG receipt evidence differs from its recorded executions",
            )?;
            match receipt.repeatability {
                Repeatability::Verified => {
                    require(evidence.len() == 2 && evidence[0] == evidence[1], "verified MTG feedback requires two identical executions")?;
                    let ExecutionOutcome::Completed { observation, .. } = &evidence[0].outcome else { return Err("verified MTG feedback requires completed execution".into()); };
                    require(check(&case, observation) == receipt.result, "MTG receipt verdict does not follow from its observations and guards")?;
                }
                Repeatability::Diverged => require(evidence.len() == 2 && evidence[0] != evidence[1] && receipt.result == CheckResult::Inconclusive { reason: IncompleteReason::RepeatedExecutionDiverged }, "diverged MTG feedback must retain differing executions and an inconclusive result")?,
                Repeatability::Inconclusive => require(matches!(receipt.result, CheckResult::Inconclusive { .. }), "incomplete MTG execution cannot establish a behavioral verdict")?,
            }
        }
        for event in &self.events {
            if let FactoryEventPayload::DecisionRecorded {
                policy,
                decision_id,
                change_id,
                plan_id,
                decision,
            } = &event.payload
            {
                match policy {
                    DecisionPolicy::External {
                        policy_id,
                        scope,
                        attestation_id,
                    } => {
                        let attestation: ExternalDecisionAttestation =
                            artifact_json(contents, attestation_id)?;
                        require(attestation.policy_id == *policy_id && attestation.scope == *scope && attestation.decision_id == *decision_id && attestation.plan_id == *plan_id && attestation.change_id == *change_id, "external policy attestation does not bind this exact decision, scope, plan and change")?;
                    }
                    DecisionPolicy::MtgConformanceV1 => {
                        if let AcceptanceDecision::Accepted {
                            baseline_receipt_id,
                            candidate_receipt_id,
                            gate_receipt_ids,
                            review_id,
                            ..
                        } = decision
                        {
                            let plan: AcceptancePlan = artifact_json(contents, plan_id)?;
                            let case: CaseSpec = artifact_json(contents, &plan.case_id)?;
                            let baseline: EvaluationReceipt =
                                artifact_json(contents, baseline_receipt_id)?;
                            let candidate: EvaluationReceipt =
                                artifact_json(contents, candidate_receipt_id)?;
                            let gates = gate_receipt_ids
                                .iter()
                                .map(|id| artifact_json::<EvaluationReceipt>(contents, id))
                                .collect::<Result<Vec<_>, _>>()?;
                            let review: ReviewRecord = artifact_json(contents, review_id)?;
                            let recomputed =
                                accept(&case, &plan, &baseline, &candidate, &gates, &review)
                                    .map_err(|e| e.to_string())?;
                            require(recomputed == *decision, "recorded MTG acceptance does not follow from retained evidence and independent review")?;
                            for execution_id in &feedbacks[candidate_receipt_id].execution_ids {
                                let (_, _, build_id, _) = starts[execution_id];
                                let build = builds[build_id];
                                let attestation_id = build.attestation_id.as_ref().ok_or(
                                    "accepted MTG candidate requires a retained build attestation",
                                )?;
                                let attestation: BuildRecord =
                                    artifact_json(contents, attestation_id)?;
                                match &attestation.phase {
                                    PhaseBuild::Checkout { base_revision, revision, patch_sha256, .. } => require(base_revision == &self.target.baseline_revision && revision == &build.source_revision && patch_sha256 == change_id, "accepted MTG build does not attest to this baseline, source revision and patch")?,
                                    _ => return Err("accepted MTG candidate requires a checkout patch attestation".into()),
                                }
                            }
                        }
                    }
                }
            }
        }
        Ok(())
    }
}

fn artifact_json<T: serde::de::DeserializeOwned>(
    contents: &BTreeMap<ContentHash, Vec<u8>>,
    id: &ContentHash,
) -> Result<T, String> {
    serde_json::from_slice(
        contents
            .get(id)
            .ok_or("required artifact file is missing")?,
    )
    .map_err(|e| format!("artifact {id}: {e}"))
}
