use loop_contract::*;
use std::{
    fs,
    path::{Path, PathBuf},
    process::{Command, Output},
};
use tempfile::TempDir;

fn root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}
fn run(args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_coworld-mtg-harness"))
        .args(args)
        .output()
        .unwrap()
}

#[test]
fn execution_and_expectations_are_separate_and_evidence_is_append_only() {
    let temp = TempDir::new().unwrap();
    let output = temp.path().join("evaluation");
    let case = root().join("cases/cards/helix-resolves.json");
    let corpus = root().join("cases/corpus/corpus.json");
    let args = [
        "case",
        "evaluate",
        "--case",
        case.to_str().unwrap(),
        "--corpus",
        corpus.to_str().unwrap(),
        "--output-dir",
        output.to_str().unwrap(),
    ];
    let first = run(&args);
    assert!(
        first.status.success(),
        "{}",
        String::from_utf8_lossy(&first.stderr)
    );
    let receipt: EvaluationReceipt =
        serde_json::from_slice(&fs::read(output.join("receipt.json")).unwrap()).unwrap();
    assert_eq!(receipt.result, CheckResult::Satisfied);
    assert_eq!(receipt.repeatability, Repeatability::Verified);
    assert_eq!(receipt.evidence_sha256.len(), 2);
    let request = fs::read_to_string(output.join("request.json")).unwrap();
    assert!(!request.contains("assertions"));
    let original = fs::read(output.join("receipt.json")).unwrap();
    assert!(!run(&args).status.success());
    assert_eq!(original, fs::read(output.join("receipt.json")).unwrap());
    let mut changed: CaseSpec = serde_json::from_slice(&fs::read(&case).unwrap()).unwrap();
    changed.assertions[0].predicate = Predicate::Life {
        seat: Seat::Player,
        equals: 999,
    };
    let path = temp.path().join("wrong-expectation.json");
    fs::write(&path, serde_json::to_vec(&changed).unwrap()).unwrap();
    let wrong = temp.path().join("wrong");
    assert!(!run(&[
        "case",
        "evaluate",
        "--case",
        path.to_str().unwrap(),
        "--corpus",
        corpus.to_str().unwrap(),
        "--output-dir",
        wrong.to_str().unwrap()
    ])
    .status
    .success());
    let evidence0: ExecutionEvidence =
        serde_json::from_slice(&fs::read(output.join("execution-0.json")).unwrap()).unwrap();
    let evidence1: ExecutionEvidence =
        serde_json::from_slice(&fs::read(wrong.join("execution-0.json")).unwrap()).unwrap();
    assert_eq!(
        evidence0.outcome, evidence1.outcome,
        "changing expectations cannot change execution"
    );

    let receipt_path = output.join("receipt.json");
    let verify = [
        "case",
        "verify",
        "--receipt",
        receipt_path.to_str().unwrap(),
    ];
    assert!(run(&verify).status.success());
    let mut tampered = receipt.clone();
    tampered.result = CheckResult::Violated {
        assertion_ids: vec!["fabricated".into()],
    };
    fs::write(&receipt_path, serde_json::to_vec(&tampered).unwrap()).unwrap();
    assert!(
        !run(&verify).status.success(),
        "verdict must be derived from evidence"
    );
    fs::write(&receipt_path, &original).unwrap();
    let mut missing_steps = evidence0;
    if let ExecutionOutcome::Completed { steps, .. } = &mut missing_steps.outcome {
        steps.clear();
    }
    for index in 0..2 {
        fs::write(
            output.join(format!("execution-{index}.json")),
            serde_json::to_vec(&missing_steps).unwrap(),
        )
        .unwrap();
    }
    tampered = receipt;
    tampered.evidence_sha256 = vec![digest(&missing_steps).unwrap(); 2];
    fs::write(&receipt_path, serde_json::to_vec(&tampered).unwrap()).unwrap();
    assert!(
        !run(&verify).status.success(),
        "even rehashed evidence must account for every operation"
    );
}

#[test]
fn missing_card_is_inconclusive_and_corpus_tampering_is_rejected() {
    let temp = TempDir::new().unwrap();
    let output = temp.path().join("evaluation");
    let mut case: CaseSpec =
        serde_json::from_slice(&fs::read(root().join("cases/cards/helix-resolves.json")).unwrap())
            .unwrap();
    case.scenario.cards[0].name = "Unresolvable Card".into();
    let path = temp.path().join("case.json");
    fs::write(&path, serde_json::to_vec(&case).unwrap()).unwrap();
    let corpus = root().join("cases/corpus/corpus.json");
    assert!(!run(&[
        "case",
        "evaluate",
        "--case",
        path.to_str().unwrap(),
        "--corpus",
        corpus.to_str().unwrap(),
        "--output-dir",
        output.to_str().unwrap()
    ])
    .status
    .success());
    let receipt: EvaluationReceipt =
        serde_json::from_slice(&fs::read(output.join("receipt.json")).unwrap()).unwrap();
    assert!(matches!(receipt.result, CheckResult::Inconclusive { .. }));
    let mut request: ExecutionRequest =
        serde_json::from_slice(&fs::read(output.join("request.json")).unwrap()).unwrap();
    request.corpus_sha256 = hash_bytes(b"wrong bytes");
    let tampered = temp.path().join("tampered.json");
    fs::write(&tampered, serde_json::to_vec(&request).unwrap()).unwrap();
    assert!(!run(&[
        "case",
        "execute",
        "--request",
        tampered.to_str().unwrap(),
        "--output",
        temp.path().join("bad.json").to_str().unwrap()
    ])
    .status
    .success());
}

#[test]
fn setup_reduction_preserves_predicate_and_reachability() {
    let temp = TempDir::new().unwrap();
    let mut case: CaseSpec =
        serde_json::from_slice(&fs::read(root().join("cases/cards/helix-resolves.json")).unwrap())
            .unwrap();
    // Deliberately false expectation tests the reducer, not an alleged Magic defect.
    case.assertions = vec![Assertion {
        id: "wrong-life".into(),
        predicate: Predicate::Life {
            seat: Seat::Player,
            equals: 999,
        },
    }];
    case.scenario.cards.push(PlacedCard {
        label: "irrelevant".into(),
        name: "Forest".into(),
        owner: Seat::Player,
        zone: CardZone::Battlefield,
        tapped: false,
        plus_one_counters: 0,
    });
    let path = temp.path().join("case.json");
    fs::write(&path, serde_json::to_vec(&case).unwrap()).unwrap();
    let output = temp.path().join("reduced");
    let corpus = root().join("cases/corpus/corpus.json");
    let result = run(&[
        "case",
        "reduce",
        "--case",
        path.to_str().unwrap(),
        "--corpus",
        corpus.to_str().unwrap(),
        "--output-dir",
        output.to_str().unwrap(),
        "--predicate",
        "wrong-life",
        "--budget",
        "8",
    ]);
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let reduced: CaseSpec =
        serde_json::from_slice(&fs::read(output.join("reduced-case.json")).unwrap()).unwrap();
    assert_eq!(reduced.scenario.cards.len(), 1);
    assert_eq!(
        reduced.scenario.operations.len(),
        1,
        "removing the cast would fail the reachability guard"
    );
    assert_eq!(reduced.assertions, case.assertions);
}

#[cfg(unix)]
#[test]
fn worker_timeout_is_inconclusive_instead_of_a_rule_violation() {
    use std::os::unix::fs::PermissionsExt;
    let temp = TempDir::new().unwrap();
    let worker = temp.path().join("slow-worker");
    fs::write(&worker, "#!/bin/sh\nexec sleep 10\n").unwrap();
    fs::set_permissions(&worker, fs::Permissions::from_mode(0o700)).unwrap();
    let output = temp.path().join("timeout");
    let result = run(&[
        "case",
        "evaluate",
        "--case",
        root()
            .join("cases/cards/helix-resolves.json")
            .to_str()
            .unwrap(),
        "--corpus",
        root().join("cases/corpus/corpus.json").to_str().unwrap(),
        "--worker",
        worker.to_str().unwrap(),
        "--timeout-seconds",
        "1",
        "--output-dir",
        output.to_str().unwrap(),
    ]);
    assert!(!result.status.success());
    let receipt: EvaluationReceipt =
        serde_json::from_slice(&fs::read(output.join("receipt.json")).unwrap()).unwrap();
    assert_eq!(receipt.repeatability, Repeatability::Inconclusive);
    assert_eq!(
        receipt.result,
        CheckResult::Inconclusive {
            reason: IncompleteReason::WorkerBudget { seconds: 1 }
        }
    );
}
