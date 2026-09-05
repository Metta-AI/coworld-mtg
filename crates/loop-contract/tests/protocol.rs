use loop_contract::*;
use std::collections::BTreeMap;

fn case() -> CaseSpec {
    CaseSpec {
        title: "life invariant".into(),
        author: "author".into(),
        origin: CaseOrigin::Authored,
        justification: Justification::Invariant {
            specification: "A new player has twenty life.".into(),
        },
        scenario: Scenario {
            seed: 7,
            life: [20, 20],
            mana: [vec![], vec![]],
            cards: vec![],
            operations: vec![],
        },
        guards: vec![],
        assertions: vec![Assertion {
            id: "life".into(),
            predicate: Predicate::Life {
                seat: Seat::Player,
                equals: 20,
            },
        }],
    }
}

fn receipt(case_id: ContentHash, binary: &[u8], result: CheckResult) -> EvaluationReceipt {
    EvaluationReceipt {
        protocol: ProtocolVersion::V1,
        case_id,
        corpus_sha256: hash_bytes(b"data"),
        worker_sha256: hash_bytes(binary),
        checker_sha256: hash_bytes(b"checker"),
        evidence_sha256: vec![hash_bytes(b"evidence"); 2],
        repeatability: Repeatability::Verified,
        result,
    }
}

#[test]
fn typed_input_rejects_unknown_fields_and_invalid_hashes() {
    let mut json = serde_json::to_value(case()).unwrap();
    json["pass_anyway"] = true.into();
    assert!(serde_json::from_value::<CaseSpec>(json).is_err());
    assert!(serde_json::from_str::<ContentHash>("\"not-a-hash\"").is_err());
    assert!(serde_json::from_str::<Seat>("\"spectator\"").is_err());
}

#[test]
fn missing_measurement_or_failed_guard_cannot_become_a_semantic_violation() {
    let mut case = case();
    let observation = Observation {
        life: [19, 20],
        objects: vec![],
        labels: BTreeMap::new(),
    };
    assert!(matches!(
        check(&case, &observation),
        CheckResult::Violated { .. }
    ));
    case.guards = vec![Assertion {
        id: "reach".into(),
        predicate: Predicate::Zone {
            object: "spell".into(),
            equals: CardZone::Graveyard,
        },
    }];
    assert!(matches!(
        check(&case, &observation),
        CheckResult::Inconclusive { .. }
    ));
}

#[test]
fn hashing_preserves_order_and_freezes_expectations() {
    assert_ne!(digest(&vec![1, 2]).unwrap(), digest(&vec![2, 1]).unwrap());
    assert_eq!(
        digest(&serde_json::json!({"a":1,"b":2})).unwrap(),
        digest(&serde_json::json!({"b":2,"a":1})).unwrap()
    );
    let original = case();
    let mut changed = original.clone();
    changed.assertions.clear();
    assert_ne!(digest(&original).unwrap(), digest(&changed).unwrap());
}

#[test]
fn acceptance_requires_frozen_expectations_independent_review_and_real_gates() {
    let case = case();
    let id = digest(&case).unwrap();
    let baseline = receipt(
        id.clone(),
        b"old",
        CheckResult::Violated {
            assertion_ids: vec!["life".into()],
        },
    );
    let candidate = receipt(id.clone(), b"new", CheckResult::Satisfied);
    let regression = receipt(hash_bytes(b"regression"), b"new", CheckResult::Satisfied);
    let holdout = receipt(hash_bytes(b"holdout"), b"new", CheckResult::Satisfied);
    let plan = AcceptancePlan {
        case_id: id,
        regression_case_ids: vec![regression.case_id.clone()],
        holdout_case_ids: vec![holdout.case_id.clone()],
    };
    let review = ReviewRecord {
        plan_id: digest(&plan).unwrap(),
        baseline_receipt_id: digest(&baseline).unwrap(),
        candidate_receipt_id: digest(&candidate).unwrap(),
        reviewer: "independent-reviewer".into(),
        rationale: "Checked specification, patch scope and discriminators.".into(),
        decision: ReviewDecision::Approve,
    };
    let gates = vec![regression, holdout];
    let accepted = accept(&case, &plan, &baseline, &candidate, &gates, &review).unwrap();
    let AcceptanceDecision::Accepted {
        gate_receipt_ids, ..
    } = accepted
    else {
        panic!("valid before/after experiment must be accepted");
    };
    assert_eq!(
        gate_receipt_ids,
        gates
            .iter()
            .map(|gate| digest(gate).unwrap())
            .collect::<Vec<_>>(),
        "acceptance binds the actual gate receipts, not just target evaluations"
    );
    assert!(matches!(
        accept(&case, &plan, &baseline, &candidate, &gates[..1], &review).unwrap(),
        AcceptanceDecision::Rejected { .. }
    ));
    let mut same_author = review.clone();
    same_author.reviewer = case.author.clone();
    assert!(matches!(
        accept(&case, &plan, &baseline, &candidate, &gates, &same_author).unwrap(),
        AcceptanceDecision::Rejected { .. }
    ));
    let mut changed = candidate.clone();
    changed.checker_sha256 = hash_bytes(b"weakened checker");
    assert!(matches!(
        accept(&case, &plan, &baseline, &changed, &gates, &review).unwrap(),
        AcceptanceDecision::Rejected { .. }
    ));
    changed = candidate.clone();
    changed.result = CheckResult::Inconclusive {
        reason: IncompleteReason::WorkerBudget { seconds: 30 },
    };
    assert!(matches!(
        accept(&case, &plan, &baseline, &changed, &gates, &review).unwrap(),
        AcceptanceDecision::Rejected { .. }
    ));
    changed = baseline.clone();
    changed.result = CheckResult::Satisfied;
    assert!(matches!(
        accept(&case, &plan, &changed, &candidate, &gates, &review).unwrap(),
        AcceptanceDecision::Rejected { .. }
    ));
    let mut observational = case.clone();
    observational.justification = Justification::Observation {
        source_sha256: hash_bytes(b"trace"),
        assumptions: vec![],
    };
    assert!(matches!(
        accept(
            &observational,
            &plan,
            &baseline,
            &candidate,
            &gates,
            &review
        )
        .unwrap(),
        AcceptanceDecision::Rejected { .. }
    ));
}

#[test]
fn worker_request_schema_excludes_expected_results() {
    let files = contract_artifacts();
    let schema = &files["ExecutionRequest.schema.json"];
    assert!(!schema.contains("assertions"));
    assert!(!schema.contains("equals"));
    for artifact in [
        "CaseSpec",
        "ExecutionRequest",
        "ExecutionEvidence",
        "EvaluationReceipt",
        "ReductionReceipt",
        "AcceptancePlan",
        "ReviewRecord",
        "AcceptanceDecision",
    ] {
        assert!(files["architecture.mmd"].contains(artifact));
        assert!(files["message-flow.mmd"].contains(artifact));
        assert!(files.contains_key(&format!("{artifact}.schema.json")));
    }
}

fn attributed_fixture() -> CaseAttribution {
    let case = case();
    let mut regression = case.clone();
    regression.title = "regression control".into();
    let mut holdout = case.clone();
    holdout.title = "held out control".into();
    let evidence = |binary: &[u8], life| ExecutionEvidence {
        protocol: ProtocolVersion::V1,
        request_id: hash_bytes(b"request"),
        binary_sha256: hash_bytes(binary),
        declared_phase_revision: "test fixture".into(),
        outcome: ExecutionOutcome::Completed {
            observation: Observation {
                life: [life, 20],
                objects: vec![],
                labels: BTreeMap::new(),
            },
            steps: vec![],
        },
    };
    let baseline_execution = evidence(b"old", 19);
    let candidate_execution = evidence(b"new", 20);
    let mut baseline = receipt(
        digest(&case).unwrap(),
        b"old",
        CheckResult::Violated {
            assertion_ids: vec!["life".into()],
        },
    );
    baseline.evidence_sha256 = vec![digest(&baseline_execution).unwrap(); 2];
    let mut candidate = receipt(digest(&case).unwrap(), b"new", CheckResult::Satisfied);
    candidate.evidence_sha256 = vec![digest(&candidate_execution).unwrap(); 2];
    let gates = [regression, holdout]
        .into_iter()
        .map(|case| AttributedGate {
            receipt: receipt(digest(&case).unwrap(), b"new", CheckResult::Satisfied),
            case,
        })
        .collect::<Vec<_>>();
    let plan = AcceptancePlan {
        case_id: baseline.case_id.clone(),
        regression_case_ids: vec![gates[0].receipt.case_id.clone()],
        holdout_case_ids: vec![gates[1].receipt.case_id.clone()],
    };
    let review = ReviewRecord {
        plan_id: digest(&plan).unwrap(),
        baseline_receipt_id: digest(&baseline).unwrap(),
        candidate_receipt_id: digest(&candidate).unwrap(),
        reviewer: "independent reviewer".into(),
        rationale: "Unit fixture only; no real repair is claimed.".into(),
        decision: ReviewDecision::Approve,
    };
    let acceptance = accept(
        &case,
        &plan,
        &baseline,
        &candidate,
        &gates
            .iter()
            .map(|gate| gate.receipt.clone())
            .collect::<Vec<_>>(),
        &review,
    )
    .unwrap();
    CaseAttribution {
        protocol: ProtocolVersion::V1,
        case,
        plan,
        baseline,
        candidate,
        baseline_execution,
        candidate_execution,
        gates,
        review,
        acceptance,
        repair: RepairProvenance {
            repository: "fixture".into(),
            base_revision: "a".repeat(40),
            revision: "b".repeat(40),
            patch_sha256: hash_bytes(b"patch"),
            baseline_build_sha256: hash_bytes(b"old build"),
            candidate_build_sha256: hash_bytes(b"new build"),
        },
    }
}

#[test]
fn case_note_reports_checked_measurements_and_rejects_unbound_edits() {
    let record = attributed_fixture();
    let note = render_case_note(&record).unwrap();
    assert_eq!(note, render_case_note(&record).unwrap());
    assert!(note.contains("| life | 20 | 19 | 20 |"));
    assert!(note.contains("Origin: an authored scenario."));
    assert!(note.contains("Held-out case"));
    let mut edited = record.clone();
    if let ExecutionOutcome::Completed { observation, .. } = &mut edited.baseline_execution.outcome
    {
        observation.life[0] = 18;
    }
    assert!(render_case_note(&edited).is_err());
    let mut edited = record.clone();
    edited.gates[0].case.title = "unearned attribution".into();
    assert!(render_case_note(&edited).is_err());
    let mut edited = record;
    edited.review.decision = ReviewDecision::Reject;
    assert!(render_case_note(&edited).is_err());
}

#[test]
fn origin_preserves_authored_ids_but_binds_derived_lineage() {
    let original = case();
    let json = serde_json::to_value(&original).unwrap();
    assert!(json.get("origin").is_none());
    assert_eq!(serde_json::from_value::<CaseSpec>(json).unwrap(), original);
    let mut derived = original.clone();
    derived.origin = CaseOrigin::Derived {
        parent_case_id: digest(&original).unwrap(),
        transformation: "Removed an irrelevant setup card.".into(),
    };
    assert_ne!(digest(&derived).unwrap(), digest(&original).unwrap());
}
