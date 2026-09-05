//! Coordinator for immutable case artifacts. The worker never receives assertions.
mod acceptance;
use anyhow::{bail, Context, Result};
use clap::{Args, Subcommand};
use loop_contract::*;
use phase_bridge::{PhaseRuntime, PHASE_REVISION};
use serde::{de::DeserializeOwned, Serialize};
use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
    process::{Command, Stdio},
    time::{Duration, Instant},
};

#[derive(Args)]
pub struct CaseArgs {
    #[command(subcommand)]
    command: CaseCommand,
}

#[derive(Subcommand)]
enum CaseCommand {
    /// Generate schemas and diagrams from the typed boundary registry.
    Contracts {
        #[arg(long)]
        output_dir: PathBuf,
        #[arg(long)]
        check: bool,
    },
    /// Freeze the target and independently selected gates before building a repair.
    Plan {
        #[arg(long)]
        case: PathBuf,
        #[arg(long = "regression", required = true)]
        regressions: Vec<PathBuf>,
        #[arg(long = "holdout", required = true)]
        holdouts: Vec<PathBuf>,
        #[arg(long)]
        output: PathBuf,
    },
    /// Worker protocol: execute setup/operations only, with no expected results.
    Execute {
        #[arg(long)]
        request: PathBuf,
        #[arg(long)]
        output: PathBuf,
    },
    /// Freeze, execute twice, and evaluate a case with this coordinator's checker.
    Evaluate(EvaluateArgs),
    /// Recompute a completed receipt using its retained inputs and evidence.
    Verify {
        #[arg(long)]
        receipt: PathBuf,
    },
    /// Run several independent cases; retain all failures and inconclusives.
    Campaign {
        #[arg(long = "case", required_unless_present = "case_dir")]
        cases: Vec<PathBuf>,
        #[arg(long, conflicts_with = "cases")]
        case_dir: Option<PathBuf>,
        #[arg(long)]
        corpus: PathBuf,
        #[arg(long)]
        worker: Option<PathBuf>,
        #[arg(long)]
        output_dir: PathBuf,
        #[arg(long, default_value_t = 30)]
        timeout_seconds: u64,
    },
    /// Delete setup cards and operations only while preserving a reproduced predicate.
    Reduce {
        #[command(flatten)]
        evaluation: EvaluateArgs,
        #[arg(long)]
        predicate: String,
        #[arg(long, default_value_t = 32)]
        budget: u32,
    },
    /// Accept a reviewed repair and generate its portable attribution bundle.
    Accept(AcceptanceArgs),
    /// Verify a preserved worker and its typed source manifest.
    BuildCheck {
        #[arg(long)]
        build: PathBuf,
    },
    /// Generate the blog attribution index and verify archived notes and patch bindings.
    Catalog {
        #[arg(long)]
        evidence_dir: PathBuf,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        check: bool,
    },
    /// Regenerate a case note from its typed attribution record.
    Note {
        #[arg(long)]
        attribution: PathBuf,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        check: bool,
    },
}

#[derive(Args)]
struct AcceptanceArgs {
    #[arg(long)]
    case: PathBuf,
    #[arg(long)]
    plan: PathBuf,
    #[arg(long)]
    baseline: PathBuf,
    #[arg(long)]
    candidate: PathBuf,
    #[arg(long = "gate")]
    gates: Vec<PathBuf>,
    #[arg(long)]
    review: PathBuf,
    #[arg(long)]
    baseline_build: PathBuf,
    #[arg(long)]
    candidate_build: PathBuf,
    #[arg(long)]
    output_dir: PathBuf,
}

#[derive(Args, Clone)]
struct EvaluateArgs {
    #[arg(long)]
    case: PathBuf,
    #[arg(long)]
    corpus: PathBuf,
    #[arg(long)]
    worker: Option<PathBuf>,
    #[arg(long)]
    output_dir: PathBuf,
    #[arg(long, default_value_t = 30)]
    timeout_seconds: u64,
}

pub fn dispatch(args: CaseArgs) -> Result<()> {
    match args.command {
        CaseCommand::Contracts { output_dir, check } => {
            for (name, content) in contract_artifacts() {
                let path = output_dir.join(name);
                if check {
                    if fs::read_to_string(&path)
                        .with_context(|| format!("read {}", path.display()))?
                        != content
                    {
                        bail!("generated contract is stale: {}", path.display());
                    }
                } else {
                    fs::create_dir_all(&output_dir)?;
                    fs::write(path, content)?;
                }
            }
        }
        CaseCommand::Execute { request, output } => execute_worker(&request, &output)?,
        CaseCommand::Plan {
            case,
            regressions,
            holdouts,
            output,
        } => {
            let case_id = |path: &Path| -> Result<ContentHash> {
                let case: CaseSpec = read_json(path)?;
                case.validate().map_err(anyhow::Error::msg)?;
                Ok(digest(&case)?)
            };
            let plan = AcceptancePlan {
                case_id: case_id(&case)?,
                regression_case_ids: regressions
                    .iter()
                    .map(|p| case_id(p))
                    .collect::<Result<_>>()?,
                holdout_case_ids: holdouts.iter().map(|p| case_id(p)).collect::<Result<_>>()?,
            };
            let mut ids = std::collections::BTreeSet::from([&plan.case_id]);
            if plan
                .regression_case_ids
                .iter()
                .chain(&plan.holdout_case_ids)
                .any(|id| !ids.insert(id))
            {
                bail!("target, regressions and holdouts must be distinct");
            }
            write_new(&output, &plan)?;
            println!("Plan: {}", digest(&plan)?);
        }
        CaseCommand::Evaluate(args) => {
            let case: CaseSpec = read_json(&args.case)?;
            let receipt = evaluate(&case, &args)?;
            println!("{}", serde_json::to_string_pretty(&receipt)?);
            require_satisfied(&receipt)?;
        }
        CaseCommand::Verify { receipt } => {
            println!(
                "{}",
                serde_json::to_string_pretty(&verified_receipt(&receipt)?)?
            );
        }
        CaseCommand::Campaign {
            mut cases,
            case_dir,
            corpus,
            worker,
            output_dir,
            timeout_seconds,
        } => {
            if let Some(directory) = case_dir {
                cases = fs::read_dir(directory)?
                    .map(|entry| entry.map(|entry| entry.path()))
                    .collect::<std::io::Result<Vec<_>>>()?;
                cases.retain(|path| {
                    path.extension()
                        .is_some_and(|extension| extension == "json")
                });
                cases.sort();
            }
            if cases.is_empty() {
                bail!("campaign requires at least one case");
            }
            reserve_dir(&output_dir)?;
            let mut receipts = Vec::new();
            for path in cases {
                let case: CaseSpec = read_json(&path)?;
                let args = EvaluateArgs {
                    case: path,
                    corpus: corpus.clone(),
                    worker: worker.clone(),
                    output_dir: output_dir.join(digest(&case)?.to_string()),
                    timeout_seconds,
                };
                let receipt = evaluate(&case, &args)?;
                println!("{}: {:?}", case.title, receipt.result);
                receipts.push(receipt);
            }
            write_new(&output_dir.join("campaign.json"), &receipts)?;
            if receipts.iter().any(|r| require_satisfied(r).is_err()) {
                bail!("campaign contains failed or inconclusive cases; all receipts retained");
            }
        }
        CaseCommand::Reduce {
            evaluation,
            predicate,
            budget,
        } => reduce(&evaluation, &predicate, budget)?,
        CaseCommand::Accept(args) => acceptance::run(args)?,
        CaseCommand::BuildCheck { build } => {
            let record: BuildRecord = read_json(&build.join("build.json"))?;
            acceptance::verified_build(&build, &record.binary_sha256)?;
            println!("Verified build {}", record.binary_sha256);
        }
        CaseCommand::Catalog {
            evidence_dir,
            output,
            check,
        } => acceptance::catalog(&evidence_dir, &output, check)?,
        CaseCommand::Note {
            attribution,
            output,
            check,
        } => {
            let note = render_case_note(&read_json(&attribution)?).map_err(anyhow::Error::msg)?;
            if check {
                if fs::read_to_string(&output)? != note {
                    bail!("generated case note is stale: {}", output.display());
                }
            } else {
                write_bytes_new(&output, note.as_bytes())?;
            }
        }
    }
    Ok(())
}

fn execute_worker(request_path: &Path, output: &Path) -> Result<()> {
    let request: ExecutionRequest = read_json(request_path)?;
    request.scenario.validate().map_err(anyhow::Error::msg)?;
    let raw = fs::read(&request.corpus_path)?;
    if hash_bytes(&raw) != request.corpus_sha256 {
        bail!("worker corpus digest mismatch");
    }
    let runtime = PhaseRuntime::from_card_data_json(std::str::from_utf8(&raw)?)?;
    let evidence = ExecutionEvidence {
        protocol: ProtocolVersion::V1,
        request_id: digest(&request)?,
        binary_sha256: hash_bytes(&fs::read(std::env::current_exe()?)?),
        declared_phase_revision: PHASE_REVISION.into(),
        outcome: runtime.execute_scenario(&request.scenario),
    };
    write_new(output, &evidence)
}

fn evaluate(case: &CaseSpec, args: &EvaluateArgs) -> Result<EvaluationReceipt> {
    case.validate().map_err(anyhow::Error::msg)?;
    if args.timeout_seconds == 0 {
        bail!("worker timeout must be positive");
    }
    reserve_dir(&args.output_dir)?;
    let corpus = fs::canonicalize(&args.corpus)?;
    let raw = fs::read(&corpus)?;
    let worker = fs::canonicalize(args.worker.clone().unwrap_or(std::env::current_exe()?))?;
    let worker_sha256 = hash_bytes(&fs::read(&worker)?);
    let request = ExecutionRequest {
        protocol: ProtocolVersion::V1,
        corpus_path: corpus.to_string_lossy().into_owned(),
        corpus_sha256: hash_bytes(&raw),
        scenario: case.scenario.clone(),
    };
    // A self-contained bundle includes the exact corpus, so it can be moved and rerun.
    write_bytes_new(&args.output_dir.join("corpus.json"), &raw)?;
    write_new(&args.output_dir.join("case.json"), case)?;
    write_new(&args.output_dir.join("request.json"), &request)?;
    let request_path = fs::canonicalize(args.output_dir.join("request.json"))?;
    let request_id = digest(&request)?;
    let mut evidence = Vec::new();
    let mut failure = None;
    for repeat in 0..2 {
        let output = args.output_dir.join(format!("execution-{repeat}.json"));
        let log = fs::File::create_new(args.output_dir.join(format!("worker-{repeat}.log")))?;
        let mut child = Command::new(&worker)
            .args(["case", "execute", "--request"])
            .arg(&request_path)
            .arg("--output")
            .arg(&output)
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(log)
            .spawn()?;
        let started = Instant::now();
        let status = loop {
            if let Some(status) = child.try_wait()? {
                break Some(status);
            }
            if started.elapsed() >= Duration::from_secs(args.timeout_seconds) {
                child.kill()?;
                child.wait()?;
                break None;
            }
            std::thread::sleep(Duration::from_millis(20));
        };
        match status {
            None => {
                failure = Some(IncompleteReason::WorkerBudget {
                    seconds: args.timeout_seconds,
                });
                break;
            }
            Some(status) if !status.success() => {
                failure = Some(IncompleteReason::WorkerFailed {
                    detail: status.to_string(),
                });
                break;
            }
            Some(_) => {}
        }
        let item: ExecutionEvidence = match read_json(&output) {
            Ok(item) => item,
            Err(error) => {
                failure = Some(IncompleteReason::InvalidEvidence {
                    detail: format!("{error:#}"),
                });
                break;
            }
        };
        if item.request_id != request_id || item.binary_sha256 != worker_sha256 {
            failure = Some(IncompleteReason::InvalidEvidence {
                detail: "worker evidence is bound to different inputs or binary".into(),
            });
            break;
        }
        if let Err(detail) = validate_steps(&request, &item) {
            failure = Some(IncompleteReason::InvalidEvidence { detail });
            break;
        }
        evidence.push(item);
    }
    let (repeatability, result) = match failure {
        Some(reason) => (
            Repeatability::Inconclusive,
            CheckResult::Inconclusive { reason },
        ),
        None if evidence[0] != evidence[1] => (
            Repeatability::Diverged,
            CheckResult::Inconclusive {
                reason: IncompleteReason::RepeatedExecutionDiverged,
            },
        ),
        None => match &evidence[0].outcome {
            ExecutionOutcome::Completed { observation, .. } => {
                (Repeatability::Verified, check(case, observation))
            }
            ExecutionOutcome::Inconclusive { reason } => (
                Repeatability::Inconclusive,
                CheckResult::Inconclusive {
                    reason: reason.clone(),
                },
            ),
        },
    };
    let receipt = EvaluationReceipt {
        protocol: ProtocolVersion::V1,
        case_id: digest(case)?,
        corpus_sha256: request.corpus_sha256,
        worker_sha256,
        checker_sha256: checker_digest()?,
        evidence_sha256: evidence.iter().map(digest).collect::<Result<_, _>>()?,
        repeatability,
        result,
    };
    write_new(&args.output_dir.join("receipt.json"), &receipt)?;
    Ok(receipt)
}

fn reduce(args: &EvaluateArgs, predicate: &str, budget: u32) -> Result<()> {
    if budget == 0 {
        bail!("reduction budget must be positive");
    }
    reserve_dir(&args.output_dir)?;
    let original: CaseSpec = read_json(&args.case)?;
    let mut case = original.clone();
    let mut iteration = args.clone();
    iteration.output_dir = args.output_dir.join("baseline");
    let baseline = evaluate(&case, &iteration)?;
    let CheckResult::Violated { assertion_ids } = &baseline.result else {
        bail!("reduction requires a reproduced violation");
    };
    if baseline.repeatability != Repeatability::Verified
        || !assertion_ids.iter().any(|id| id == predicate)
    {
        bail!("requested predicate does not reproduce deterministically");
    }
    let mut evaluations = 0;
    let mut complete = false;
    while evaluations < budget {
        let mut candidates = Vec::new();
        for index in 0..case.scenario.cards.len() {
            let mut candidate = case.clone();
            let removed = candidate.scenario.cards.remove(index);
            candidate.origin = CaseOrigin::Derived {
                parent_case_id: digest(&case)?,
                transformation: format!("Deleted setup card {}", removed.label),
            };
            candidates.push(candidate);
        }
        for index in 0..case.scenario.operations.len() {
            let mut candidate = case.clone();
            candidate.scenario.operations.remove(index);
            candidate.origin = CaseOrigin::Derived {
                parent_case_id: digest(&case)?,
                transformation: format!("Deleted operation {index}"),
            };
            candidates.push(candidate);
        }
        let mut improved = false;
        for candidate in candidates.into_iter().filter(|c| c.validate().is_ok()) {
            if evaluations == budget {
                break;
            }
            iteration.output_dir = args.output_dir.join(format!("attempt-{evaluations}"));
            evaluations += 1;
            let receipt = evaluate(&candidate, &iteration)?;
            if receipt.repeatability == Repeatability::Verified && receipt.result == baseline.result
            {
                case = candidate;
                improved = true;
                break;
            }
        }
        if !improved && evaluations < budget {
            complete = true;
            break;
        }
    }
    let receipt = ReductionReceipt {
        original_case_id: digest(&original)?,
        reduced_case_id: digest(&case)?,
        predicate: predicate.into(),
        original_cards: original.scenario.cards.len(),
        reduced_cards: case.scenario.cards.len(),
        original_operations: original.scenario.operations.len(),
        reduced_operations: case.scenario.operations.len(),
        evaluations,
        budget,
        search: if complete {
            ReductionSearch::SingleDeletionFixedPoint
        } else {
            ReductionSearch::BudgetExhausted
        },
    };
    write_new(&args.output_dir.join("reduced-case.json"), &case)?;
    write_new(&args.output_dir.join("reduction.json"), &receipt)?;
    println!("{}", serde_json::to_string_pretty(&receipt)?);
    Ok(())
}

fn require_satisfied(receipt: &EvaluationReceipt) -> Result<()> {
    if receipt.result != CheckResult::Satisfied || receipt.repeatability != Repeatability::Verified
    {
        bail!("case was not verified: {:?}", receipt.result);
    }
    Ok(())
}

fn checker_digest() -> Result<ContentHash> {
    // Includes compiled dependencies. Evaluate both workers with one preserved coordinator.
    Ok(hash_bytes(&fs::read(std::env::current_exe()?)?))
}

fn validate_steps(request: &ExecutionRequest, evidence: &ExecutionEvidence) -> Result<(), String> {
    if let ExecutionOutcome::Completed { steps, .. } = &evidence.outcome {
        if steps.len() != request.scenario.operations.len()
            || steps
                .iter()
                .enumerate()
                .any(|(i, s)| s.operation_index != i)
        {
            return Err(
                "completed execution must account for every scenario operation in order".into(),
            );
        }
    }
    Ok(())
}

/// Recompute an imported receipt from its retained evidence, rather than trusting its verdict.
fn verified_receipt(path: &Path) -> Result<EvaluationReceipt> {
    Ok(verified_bundle(path)?.receipt)
}

struct VerifiedBundle {
    case: CaseSpec,
    request: ExecutionRequest,
    evidence: Vec<ExecutionEvidence>,
    receipt: EvaluationReceipt,
    corpus: Vec<u8>,
}

fn verified_bundle(path: &Path) -> Result<VerifiedBundle> {
    retained_bundle(path, Some(&checker_digest()?))
}

// Archive audits recompute internal consistency without certifying a new checker identity.
fn retained_bundle(path: &Path, required_checker: Option<&ContentHash>) -> Result<VerifiedBundle> {
    let receipt: EvaluationReceipt = read_json(path)?;
    let dir = path.parent().context("receipt has no bundle directory")?;
    let case: CaseSpec = read_json(&dir.join("case.json"))?;
    case.validate().map_err(anyhow::Error::msg)?;
    let request: ExecutionRequest = read_json(&dir.join("request.json"))?;
    let corpus = fs::read(dir.join("corpus.json"))?;
    if receipt.case_id != digest(&case)?
        || request.scenario != case.scenario
        || receipt.corpus_sha256 != hash_bytes(&corpus)
        || request.corpus_sha256 != receipt.corpus_sha256
        || required_checker.is_some_and(|checker| *checker != receipt.checker_sha256)
    {
        bail!("receipt inputs or checker do not match retained artifacts");
    }
    let evidence: Vec<ExecutionEvidence> = (0..2)
        .map(|index| read_json(&dir.join(format!("execution-{index}.json"))))
        .collect::<Result<_>>()?;
    if evidence.iter().map(digest).collect::<Result<Vec<_>, _>>()? != receipt.evidence_sha256
        || evidence.iter().any(|e| {
            e.request_id != digest(&request).expect("serializable request")
                || e.binary_sha256 != receipt.worker_sha256
        })
    {
        bail!("receipt evidence hashes, request or worker identity do not match");
    }
    for item in &evidence {
        validate_steps(&request, item).map_err(anyhow::Error::msg)?;
    }
    let ExecutionOutcome::Completed { observation, .. } = &evidence[0].outcome else {
        bail!("inconclusive worker cannot be accepted");
    };
    if evidence[0] != evidence[1]
        || receipt.repeatability != Repeatability::Verified
        || receipt.result != check(&case, observation)
    {
        bail!("receipt verdict does not follow from repeated execution evidence");
    }
    Ok(VerifiedBundle {
        case,
        request,
        evidence,
        receipt,
        corpus,
    })
}

fn reserve_dir(path: &Path) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::create_dir(path).with_context(|| {
        format!(
            "reserve new artifact directory {} (existing evidence is never overwritten)",
            path.display()
        )
    })
}
fn read_json<T: DeserializeOwned>(path: &Path) -> Result<T> {
    if fs::metadata(path)?.len() > 16 * 1024 * 1024 {
        bail!("protocol artifact exceeds 16 MiB: {}", path.display());
    }
    serde_json::from_slice(&fs::read(path)?).with_context(|| format!("decode {}", path.display()))
}
fn write_new(path: &Path, value: &impl Serialize) -> Result<()> {
    let mut raw = serde_json::to_vec_pretty(value)?;
    raw.push(b'\n');
    write_bytes_new(path, &raw)
}
fn write_bytes_new(path: &Path, raw: &[u8]) -> Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let mut file = fs::File::create_new(path)?;
    file.write_all(raw)?;
    file.sync_all()?;
    Ok(())
}
