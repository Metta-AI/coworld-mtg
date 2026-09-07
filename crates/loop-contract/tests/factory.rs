use loop_contract::*;
use serde_json::json;
use std::collections::BTreeMap;

type Contents = BTreeMap<ContentHash, Vec<u8>>;

fn artifact<T: serde::Serialize>(
    replay: &mut FactoryReplay,
    contents: &mut Contents,
    value: &T,
) -> ContentHash {
    let id = digest(value).unwrap();
    replay.artifacts.insert(
        id.clone(),
        FactoryArtifact {
            path: format!("artifacts/{id}.json"),
            media_type: "application/json".into(),
            hash_mode: ArtifactHashMode::CanonicalJson,
        },
    );
    contents.insert(id.clone(), serde_json::to_vec_pretty(value).unwrap());
    id
}
fn event(replay: &mut FactoryReplay, payload: FactoryEventPayload) {
    replay.events.push(FactoryEvent {
        sequence: replay.events.len() as u64,
        elapsed_ms: None,
        stage: payload.stage().unwrap(),
        payload,
    });
}
fn execute(
    replay: &mut FactoryReplay,
    contents: &mut Contents,
    case_id: ContentHash,
    build_id: ContentHash,
    change_id: Option<ContentHash>,
    name: &str,
    result: FeedbackResult,
) -> ContentHash {
    let request_id = artifact(
        replay,
        contents,
        &json!({"case_id":case_id,"operation":"parse"}),
    );
    event(
        replay,
        FactoryEventPayload::ExecutionStarted {
            execution_id: name.into(),
            case_id: case_id.clone(),
            request_id,
            build_id,
            change_id,
        },
    );
    let evidence_id = artifact(
        replay,
        contents,
        &json!({"case_id":case_id,"fields":2,"execution":name}),
    );
    event(
        replay,
        FactoryEventPayload::ExecutionFinished {
            execution_id: name.into(),
            status: FactoryExecutionStatus::Completed,
            evidence_id: Some(evidence_id.clone()),
            trace_ids: vec![],
            detail: None,
        },
    );
    let feedback_id = artifact(
        replay,
        contents,
        &json!({"case_id":case_id,"evidence_id":evidence_id,"result":result}),
    );
    event(
        replay,
        FactoryEventPayload::FeedbackRecorded {
            feedback: FactoryFeedback {
                adapter: FeedbackAdapter::Opaque,
                feedback_id: feedback_id.clone(),
                case_id,
                execution_ids: vec![name.into()],
                evaluator: "CSV fixture evaluator".into(),
                evaluator_version: "test-v1".into(),
                declared_strength: FeedbackStrength::Strong,
                method: "Compare the parsed field count with the case specification".into(),
                bounded_claim: "Field count for this one CSV input".into(),
                result,
                summary: "Retained evaluator report for this input".into(),
            },
        },
    );
    feedback_id
}
fn generic_run() -> (FactoryReplay, Contents) {
    let mut replay = FactoryReplay {
        version: FactoryVersion::V1,
        run_id: "csv-parser-example".into(),
        title: "CSV field count".into(),
        target: ProgramTarget {
            name: "CSV parser".into(),
            repository: "https://example.test/csv".into(),
            baseline_revision: "before".into(),
        },
        recording: ReplayRecording::Live,
        status: FactoryRunStatus::Completed,
        stages: factory_stages(),
        artifacts: BTreeMap::new(),
        events: vec![],
    };
    let mut contents = BTreeMap::new();
    let source_id = artifact(&mut replay, &mut contents, &json!({"rows":["a,b,c"]}));
    event(
        &mut replay,
        FactoryEventPayload::SourceImported {
            source: SourceProvenance {
                snapshot_id: source_id.clone(),
                provider: "Local test corpus".into(),
                url: "fixture://csv-corpus".into(),
                retrieved_at: "2026-09-07T00:00:00Z".into(),
                description: "Constructed non-MTG test fixture".into(),
            },
        },
    );
    let case_id = artifact(
        &mut replay,
        &mut contents,
        &json!({"input":"a,b,c","expected_fields":3}),
    );
    event(
        &mut replay,
        FactoryEventPayload::CaseRegistered {
            case_id: case_id.clone(),
            title: "Three comma-separated fields".into(),
            derivation: CaseDerivation::SourceDerived {
                source_ids: vec![source_id.clone()],
                source_records: vec![SourceRecordSelection {
                    source_id,
                    record_id: "row:0".into(),
                }],
                recipe: "Select row zero without constructing a game scenario".into(),
                seed: None,
            },
        },
    );
    let build = FactoryBuild {
        program: "CSV parser".into(),
        source_revision: "before".into(),
        binary_sha256: hash_bytes(b"baseline parser executable"),
        command: vec!["cc".into(), "parser.c".into()],
        environment: BTreeMap::from([("compiler".into(), "fixture compiler".into())]),
        attestation_id: None,
    };
    let build_id = artifact(&mut replay, &mut contents, &build);
    event(
        &mut replay,
        FactoryEventPayload::BuildRecorded {
            build_id: build_id.clone(),
            build,
        },
    );
    execute(
        &mut replay,
        &mut contents,
        case_id,
        build_id,
        None,
        "baseline",
        FeedbackResult::Violated,
    );
    (replay, contents)
}

fn accepted_external() -> (FactoryReplay, Contents) {
    let (mut replay, mut contents) = generic_run();
    let (case_id, baseline_receipt_id) = replay
        .events
        .iter()
        .find_map(|e| match &e.payload {
            FactoryEventPayload::FeedbackRecorded { feedback } => {
                Some((feedback.case_id.clone(), feedback.feedback_id.clone()))
            }
            _ => None,
        })
        .unwrap();
    let mut gate_cases = Vec::new();
    for name in ["regression", "holdout"] {
        let id = artifact(
            &mut replay,
            &mut contents,
            &json!({"input":name,"expected_fields":1}),
        );
        event(
            &mut replay,
            FactoryEventPayload::CaseRegistered {
                case_id: id.clone(),
                title: name.into(),
                derivation: CaseDerivation::Authored {
                    author: "fixture operator".into(),
                    description: "Separate fixture input".into(),
                },
            },
        );
        gate_cases.push(id);
    }
    let change_id = artifact(
        &mut replay,
        &mut contents,
        &json!({"patch":"count final field"}),
    );
    event(
        &mut replay,
        FactoryEventPayload::ChangeProposed {
            change_id: change_id.clone(),
            description: "Count the final CSV field".into(),
            base_revision: "before".into(),
            motivating_feedback_ids: vec![baseline_receipt_id.clone()],
        },
    );
    let plan = AcceptancePlan {
        case_id: case_id.clone(),
        regression_case_ids: vec![gate_cases[0].clone()],
        holdout_case_ids: vec![gate_cases[1].clone()],
    };
    let plan_id = artifact(&mut replay, &mut contents, &plan);
    event(
        &mut replay,
        FactoryEventPayload::AcceptancePlanFrozen {
            plan_id: plan_id.clone(),
            plan,
        },
    );
    let build = FactoryBuild {
        program: "CSV parser".into(),
        source_revision: "after".into(),
        binary_sha256: hash_bytes(b"candidate parser executable"),
        command: vec!["cc".into(), "parser.c".into()],
        environment: BTreeMap::new(),
        attestation_id: None,
    };
    let build_id = artifact(&mut replay, &mut contents, &build);
    event(
        &mut replay,
        FactoryEventPayload::BuildRecorded {
            build_id: build_id.clone(),
            build,
        },
    );
    let candidate_receipt_id = execute(
        &mut replay,
        &mut contents,
        case_id,
        build_id.clone(),
        Some(change_id.clone()),
        "candidate",
        FeedbackResult::Satisfied,
    );
    let mut gate_receipt_ids = Vec::new();
    for (i, id) in gate_cases.into_iter().enumerate() {
        gate_receipt_ids.push(execute(
            &mut replay,
            &mut contents,
            id,
            build_id.clone(),
            Some(change_id.clone()),
            &format!("gate-{i}"),
            FeedbackResult::Satisfied,
        ));
    }
    let review = ReviewRecord {
        plan_id: plan_id.clone(),
        baseline_receipt_id: baseline_receipt_id.clone(),
        candidate_receipt_id: candidate_receipt_id.clone(),
        reviewer: "fixture reviewer".into(),
        rationale: "Reviewed the CSV comparator reports".into(),
        decision: ReviewDecision::Approve,
    };
    let review_id = artifact(&mut replay, &mut contents, &review);
    event(
        &mut replay,
        FactoryEventPayload::ReviewRecorded {
            review_id: review_id.clone(),
            review,
        },
    );
    let decision = AcceptanceDecision::Accepted {
        plan_id: plan_id.clone(),
        baseline_receipt_id,
        candidate_receipt_id,
        gate_receipt_ids,
        review_id,
    };
    let decision_id = artifact(&mut replay, &mut contents, &decision);
    let policy_id = artifact(
        &mut replay,
        &mut contents,
        &json!({"policy":"CSV comparator policy fixture v1"}),
    );
    let scope = "These three CSV input fixtures only".to_string();
    let attestation = ExternalDecisionAttestation {
        policy_id: policy_id.clone(),
        scope: scope.clone(),
        decision_id: decision_id.clone(),
        plan_id: plan_id.clone(),
        change_id: change_id.clone(),
    };
    let attestation_id = artifact(&mut replay, &mut contents, &attestation);
    event(
        &mut replay,
        FactoryEventPayload::DecisionRecorded {
            policy: DecisionPolicy::External {
                policy_id,
                scope,
                attestation_id,
            },
            decision_id,
            change_id,
            plan_id,
            decision,
        },
    );
    (replay, contents)
}

#[test]
fn non_mtg_run_needs_no_game_case_or_phase_build() {
    let (replay, contents) = generic_run();
    replay.validate_artifacts(&contents).unwrap();
    let encoded = serde_json::to_string(&replay).unwrap();
    assert!(!encoded.contains("phase"));
    assert!(!encoded.contains("\"scenario\":"));
    assert!(!encoded.contains("cargo_lock_sha256"));
    let decoded: FactoryReplay = serde_json::from_str(&encoded).unwrap();
    assert_eq!(decoded, replay);
    assert!(contract_artifacts().contains_key("FactoryReplay.schema.json"));
}

#[test]
fn live_prefix_preserves_unfinished_execution_without_claiming_completion() {
    let (mut replay, _) = generic_run();
    replay.events.truncate(4);
    replay.status = FactoryRunStatus::Running;
    replay.validate().unwrap();
    replay.status = FactoryRunStatus::Completed;
    assert!(replay.validate().unwrap_err().contains("unfinished"));
    replay.status = FactoryRunStatus::Failed;
    replay.validate().unwrap();
}

#[test]
fn ordering_references_paths_and_artifact_hashes_are_checked() {
    let (replay, contents) = generic_run();
    let mut changed = replay.clone();
    changed.events.swap(3, 4);
    for (i, e) in changed.events.iter_mut().enumerate() {
        e.sequence = i as u64;
    }
    assert!(changed
        .validate()
        .unwrap_err()
        .contains("start before finishing"));
    changed = replay.clone();
    if let FactoryEventPayload::FeedbackRecorded { feedback } =
        &mut changed.events.last_mut().unwrap().payload
    {
        feedback.execution_ids = vec!["absent".into()];
    }
    assert!(changed.validate().is_err());
    changed = replay.clone();
    changed.artifacts.values_mut().next().unwrap().path = "../outside.json".into();
    assert!(changed.validate().is_err());
    let mut tampered = contents.clone();
    tampered.values_mut().next().unwrap().push(b'x');
    assert!(replay.validate_artifacts(&tampered).is_err());
    let mut missing = contents;
    missing.pop_first();
    assert!(replay
        .validate_artifacts(&missing)
        .unwrap_err()
        .contains("missing"));
}

#[test]
fn explicit_errors_cancellation_and_inconclusive_are_distinct() {
    for status in [
        FactoryExecutionStatus::Error,
        FactoryExecutionStatus::Cancelled,
    ] {
        let (mut replay, _) = generic_run();
        replay.events.truncate(5);
        if let FactoryEventPayload::ExecutionFinished {
            status: value,
            evidence_id,
            detail,
            ..
        } = &mut replay.events[4].payload
        {
            *value = status;
            *evidence_id = None;
            *detail = Some("fixture stopped".into());
        }
        replay.validate().unwrap();
        if let FactoryEventPayload::ExecutionFinished { detail, .. } = &mut replay.events[4].payload
        {
            *detail = None;
        }
        assert!(replay.validate().is_err());
    }
    let (mut replay, _) = generic_run();
    if let FactoryEventPayload::FeedbackRecorded { feedback } =
        &mut replay.events.last_mut().unwrap().payload
    {
        feedback.result = FeedbackResult::Inconclusive;
    }
    replay.validate().unwrap();
}

#[test]
fn decision_requires_frozen_order_strong_feedback_and_bound_policy_attestation() {
    let (replay, contents) = accepted_external();
    replay.validate_artifacts(&contents).unwrap();
    let mut changed = replay.clone();
    let plan_index = changed
        .events
        .iter()
        .position(|e| matches!(e.payload, FactoryEventPayload::AcceptancePlanFrozen { .. }))
        .unwrap();
    let candidate_end = changed.events.iter().position(|e| matches!(&e.payload, FactoryEventPayload::ExecutionFinished { execution_id, .. } if execution_id == "candidate")).unwrap();
    let plan = changed.events.remove(plan_index);
    changed.events.insert(candidate_end, plan);
    for (i, e) in changed.events.iter_mut().enumerate() {
        e.sequence = i as u64;
    }
    assert!(changed
        .validate()
        .unwrap_err()
        .contains("follow the frozen plan"));
    changed = replay.clone();
    for e in &mut changed.events {
        if let FactoryEventPayload::FeedbackRecorded { feedback } = &mut e.payload {
            feedback.declared_strength = FeedbackStrength::Weak;
        }
    }
    assert!(changed.validate().unwrap_err().contains("strong"));
    changed = replay.clone();
    if let FactoryEventPayload::DecisionRecorded {
        policy: DecisionPolicy::External { scope, .. },
        ..
    } = &mut changed.events.last_mut().unwrap().payload
    {
        *scope = "Every possible CSV input".into();
    }
    assert!(changed
        .validate_artifacts(&contents)
        .unwrap_err()
        .contains("attestation"));
}

#[test]
fn changing_embedded_plan_or_review_cannot_keep_its_old_identity() {
    let (replay, _) = accepted_external();
    for role in ["plan", "review", "decision"] {
        let mut changed = replay.clone();
        for e in &mut changed.events {
            match &mut e.payload {
                FactoryEventPayload::AcceptancePlanFrozen { plan, .. } if role == "plan" => {
                    plan.case_id = hash_bytes(b"different case")
                }
                FactoryEventPayload::ReviewRecorded { review, .. } if role == "review" => {
                    review.reviewer = "substituted reviewer".into()
                }
                FactoryEventPayload::DecisionRecorded { decision_id, .. } if role == "decision" => {
                    *decision_id = hash_bytes(b"different decision")
                }
                _ => {}
            }
        }
        assert!(changed.validate().is_err(), "tampered {role}");
    }
}

#[test]
fn mtg_policy_cannot_relabel_opaque_feedback_as_rule_conformance() {
    let (mut replay, _) = accepted_external();
    if let FactoryEventPayload::DecisionRecorded { policy, .. } =
        &mut replay.events.last_mut().unwrap().payload
    {
        *policy = DecisionPolicy::MtgConformanceV1;
    }
    assert!(replay
        .validate()
        .unwrap_err()
        .contains("explicitly identified MTG"));
}

#[test]
fn canonical_json_golden_preserves_unicode_and_array_order() {
    let value = json!({"z": [3, 1], "a": {"text": "café", "flag": true}});
    let bytes = serde_json::to_vec(&value).unwrap();
    assert_eq!(
        String::from_utf8(bytes.clone()).unwrap(),
        "{\"a\":{\"flag\":true,\"text\":\"café\"},\"z\":[3,1]}"
    );
    assert_eq!(digest(&value).unwrap(), hash_bytes(&bytes));
    assert_ne!(
        digest(&value).unwrap(),
        digest(&json!({"z":[1,3],"a":{"text":"café","flag":true}})).unwrap()
    );
}
