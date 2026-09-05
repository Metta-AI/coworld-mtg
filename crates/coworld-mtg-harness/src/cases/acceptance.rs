//! Acceptance joins verified experiments to recorded source and emits attribution.
use super::*;
use std::collections::BTreeMap;

pub(super) fn run(args: AcceptanceArgs) -> Result<()> {
    let baseline = verified_bundle(&args.baseline)?;
    let candidate = verified_bundle(&args.candidate)?;
    let gates = args
        .gates
        .iter()
        .map(|path| verified_bundle(path))
        .collect::<Result<Vec<_>>>()?;
    let case: CaseSpec = read_json(&args.case)?;
    let plan: AcceptancePlan = read_json(&args.plan)?;
    let review: ReviewRecord = read_json(&args.review)?;
    let receipts = gates
        .iter()
        .map(|bundle| bundle.receipt.clone())
        .collect::<Vec<_>>();
    let decision = accept(
        &case,
        &plan,
        &baseline.receipt,
        &candidate.receipt,
        &receipts,
        &review,
    )?;
    let AcceptanceDecision::Accepted {
        gate_receipt_ids, ..
    } = &decision
    else {
        reserve_dir(&args.output_dir)?;
        write_new(&args.output_dir.join("acceptance.json"), &decision)?;
        bail!("acceptance rejected: {}", serde_json::to_string(&decision)?);
    };
    let baseline_build = verified_build(&args.baseline_build, &baseline.receipt.worker_sha256)?;
    let candidate_build = verified_build(&args.candidate_build, &candidate.receipt.worker_sha256)?;
    if baseline_build.harness_source_files != candidate_build.harness_source_files
        || baseline_build.compiler != candidate_build.compiler
        || baseline_build.build_environment != candidate_build.build_environment
        || baseline_build.builder_sha256 != candidate_build.builder_sha256
    {
        bail!("engine repair changed harness sources, compiler, flags or builder; separate that experiment");
    }
    let PhaseBuild::Pinned {
        repository: base_repository,
        revision: base_revision,
    } = &baseline_build.phase
    else {
        bail!("baseline build must use the pinned Phase source");
    };
    let PhaseBuild::Checkout {
        repository,
        base_revision: candidate_base,
        revision,
        patch_sha256,
        dirty_patch_sha256,
        worktree_clean,
        ..
    } = &candidate_build.phase
    else {
        bail!("candidate build needs a recorded Phase checkout and patch");
    };
    if repository != base_repository
        || candidate_base != base_revision
        || revision == base_revision
        || !worktree_clean
        || *dirty_patch_sha256 != hash_bytes(b"")
    {
        bail!("repair must be committed from the baseline source before certification");
    }
    let patch = fs::read(args.candidate_build.join("phase.patch"))?;
    if hash_bytes(&patch) != *patch_sha256 || patch.is_empty() {
        bail!("repair patch is missing or changed");
    }
    let chosen = gate_receipt_ids
        .iter()
        .map(|id| {
            gates
                .iter()
                .find(|bundle| digest(&bundle.receipt).ok().as_ref() == Some(id))
                .context("accepted gate absent")
        })
        .collect::<Result<Vec<_>>>()?;
    let record = CaseAttribution {
        protocol: ProtocolVersion::V1,
        case,
        plan,
        review,
        baseline: baseline.receipt.clone(),
        candidate: candidate.receipt.clone(),
        baseline_execution: baseline.evidence[0].clone(),
        candidate_execution: candidate.evidence[0].clone(),
        gates: chosen
            .iter()
            .map(|bundle| AttributedGate {
                case: bundle.case.clone(),
                receipt: bundle.receipt.clone(),
            })
            .collect(),
        repair: RepairProvenance {
            repository: repository.clone(),
            base_revision: base_revision.clone(),
            revision: revision.clone(),
            patch_sha256: patch_sha256.clone(),
            baseline_build_sha256: hash_bytes(&fs::read(args.baseline_build.join("build.json"))?),
            candidate_build_sha256: hash_bytes(&fs::read(args.candidate_build.join("build.json"))?),
        },
        acceptance: decision.clone(),
    };
    let note = render_case_note(&record).map_err(anyhow::Error::msg)?;
    reserve_dir(&args.output_dir)?;
    copy_bundle(
        &baseline,
        &args
            .output_dir
            .join("baseline")
            .join(baseline.receipt.case_id.to_string()),
    )?;
    copy_bundle(
        &candidate,
        &args
            .output_dir
            .join("candidate")
            .join(candidate.receipt.case_id.to_string()),
    )?;
    for bundle in chosen {
        copy_bundle(
            bundle,
            &args
                .output_dir
                .join("candidate")
                .join(bundle.receipt.case_id.to_string()),
        )?;
    }
    write_new(&args.output_dir.join("case.json"), &record.case)?;
    write_new(&args.output_dir.join("plan.json"), &record.plan)?;
    write_new(&args.output_dir.join("review.json"), &record.review)?;
    for (name, dir) in [
        ("baseline", &args.baseline_build),
        ("candidate", &args.candidate_build),
    ] {
        write_bytes_new(
            &args.output_dir.join(format!("{name}-build.json")),
            &fs::read(dir.join("build.json"))?,
        )?;
    }
    write_bytes_new(&args.output_dir.join("repair.patch"), &patch)?;
    write_new(&args.output_dir.join("attribution.json"), &record)?;
    write_bytes_new(&args.output_dir.join("case-note.md"), note.as_bytes())?;
    // Completion marker last: a partial filesystem write cannot look like a completed acceptance.
    write_new(&args.output_dir.join("acceptance.json"), &decision)?;
    println!(
        "Accepted {}; attribution and case note: {}",
        record.candidate.case_id,
        args.output_dir.display()
    );
    Ok(())
}

fn copy_bundle(bundle: &VerifiedBundle, output: &Path) -> Result<()> {
    reserve_dir(output)?;
    write_new(&output.join("case.json"), &bundle.case)?;
    write_new(&output.join("request.json"), &bundle.request)?;
    write_new(&output.join("receipt.json"), &bundle.receipt)?;
    write_bytes_new(&output.join("corpus.json"), &bundle.corpus)?;
    for (index, evidence) in bundle.evidence.iter().enumerate() {
        write_new(&output.join(format!("execution-{index}.json")), evidence)?;
    }
    Ok(())
}

fn valid_revision(revision: &str) -> bool {
    revision.len() == 40
        && revision
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}

pub(super) fn verified_build(dir: &Path, worker: &ContentHash) -> Result<BuildRecord> {
    let record: BuildRecord = read_json(&dir.join("build.json"))?;
    if record.binary_sha256 != *worker
        || hash_bytes(&fs::read(dir.join("worker"))?) != record.binary_sha256
        || !valid_revision(&record.harness_revision)
        || record.compiler.trim().is_empty()
    {
        bail!("build record does not identify the evaluated executable");
    }
    verify_sources(&dir.join("source"), &record.harness_source_files, true)?;
    if hash_bytes(&fs::read(dir.join("source/Cargo.lock"))?) != record.cargo_lock_sha256 {
        bail!("resolved Cargo.lock changed");
    }
    match &record.phase {
        PhaseBuild::Pinned { revision, .. } if !valid_revision(revision) => {
            bail!("invalid pinned revision")
        }
        PhaseBuild::Pinned { .. } => {}
        PhaseBuild::Checkout {
            revision,
            base_revision,
            source_files,
            ..
        } => {
            if !valid_revision(revision) || !valid_revision(base_revision) {
                bail!("invalid repair revision");
            }
            verify_sources(&dir.join("phase-source"), source_files, false)?;
        }
    }
    Ok(record)
}

fn verify_sources(
    root: &Path,
    expected: &BTreeMap<String, ContentHash>,
    original_lock: bool,
) -> Result<()> {
    for required in ["Cargo.toml", "Cargo.lock", "rust-toolchain.toml"] {
        if !expected.contains_key(required) {
            bail!("source record lacks {required}");
        }
    }
    for (name, hash) in expected {
        if Path::new(name)
            .components()
            .any(|component| !matches!(component, std::path::Component::Normal(_)))
        {
            bail!("source record must use relative file paths");
        }
        let path = root.join(if original_lock && name == "Cargo.lock" {
            "Cargo.lock.input"
        } else {
            name
        });
        if hash_bytes(&fs::read(&path)?) != *hash {
            bail!("recorded source changed: {}", path.display());
        }
    }
    fn visit(root: &Path, path: &Path, expected: &BTreeMap<String, ContentHash>) -> Result<()> {
        for entry in fs::read_dir(path)? {
            let entry = entry?;
            if entry.file_name() == "target" {
                continue;
            }
            let path = entry.path();
            if path.is_dir() {
                visit(root, &path, expected)?;
            } else if !expected
                .contains_key(&path.strip_prefix(root)?.to_string_lossy().to_string())
            {
                bail!("source file absent from manifest: {}", path.display());
            }
        }
        Ok(())
    }
    visit(root, &root.join("crates"), expected)
}

/// Archived bundles omit large executables; their bytes and source manifests remain
/// in the build archive. Here we check internal attribution and retained-file bindings.
pub(super) fn catalog(evidence_dir: &Path, output: &Path, check: bool) -> Result<()> {
    let mut directories = fs::read_dir(evidence_dir)?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<std::io::Result<Vec<_>>>()?;
    directories.retain(|path| path.is_dir());
    directories.sort();
    let mut index = String::from("# Accepted case library\n\nGenerated by `case catalog`. Each entry links the scenario that motivated a repair to measured results, source provenance and independent review.\n\n");
    for dir in directories {
        let record: CaseAttribution = read_json(&dir.join("attribution.json"))?;
        let note = render_case_note(&record).map_err(anyhow::Error::msg)?;
        if fs::read_to_string(dir.join("case-note.md"))? != note
            || read_json::<AcceptanceDecision>(&dir.join("acceptance.json"))? != record.acceptance
            || hash_bytes(&fs::read(dir.join("repair.patch"))?) != record.repair.patch_sha256
        {
            bail!("stale or altered attribution bundle: {}", dir.display());
        }
        if read_json::<CaseSpec>(&dir.join("case.json"))? != record.case
            || read_json::<AcceptancePlan>(&dir.join("plan.json"))? != record.plan
            || read_json::<ReviewRecord>(&dir.join("review.json"))? != record.review
        {
            bail!("archived case, plan or review changed");
        }
        for (role, case, receipt) in [
            ("baseline", &record.case, &record.baseline),
            ("candidate", &record.case, &record.candidate),
        ]
        .into_iter()
        .chain(
            record
                .gates
                .iter()
                .map(|gate| ("candidate", &gate.case, &gate.receipt)),
        ) {
            let bundle = retained_bundle(
                &dir.join(role)
                    .join(receipt.case_id.to_string())
                    .join("receipt.json"),
                None,
            )?;
            if bundle.case != *case || bundle.receipt != *receipt {
                bail!("archived experiment differs from attribution");
            }
        }
        for (name, expected, worker) in [
            (
                "baseline",
                &record.repair.baseline_build_sha256,
                &record.baseline.worker_sha256,
            ),
            (
                "candidate",
                &record.repair.candidate_build_sha256,
                &record.candidate.worker_sha256,
            ),
        ] {
            let raw = fs::read(dir.join(format!("{name}-build.json")))?;
            let build: BuildRecord = serde_json::from_slice(&raw)?;
            if hash_bytes(&raw) != *expected || build.binary_sha256 != *worker {
                bail!("archived build identity changed");
            }
            match &build.phase {
                PhaseBuild::Pinned {
                    repository,
                    revision,
                } if name == "baseline"
                    && *repository == record.repair.repository
                    && *revision == record.repair.base_revision => {}
                PhaseBuild::Checkout {
                    repository,
                    base_revision,
                    revision,
                    patch_sha256,
                    worktree_clean,
                    dirty_patch_sha256,
                    ..
                } if name == "candidate"
                    && *repository == record.repair.repository
                    && *base_revision == record.repair.base_revision
                    && *revision == record.repair.revision
                    && *patch_sha256 == record.repair.patch_sha256
                    && *worktree_clean
                    && *dirty_patch_sha256 == hash_bytes(b"") => {}
                _ => bail!("archived repair is not bound to its build records"),
            }
        }
        // The index lives beside the evidence subdirectories so links remain portable.
        if output.parent() != Some(evidence_dir) {
            bail!("catalog output must live in the evidence directory");
        }
        let name = dir
            .file_name()
            .context("bundle directory name")?
            .to_string_lossy();
        if !name
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || ch == '-' || ch == '_')
        {
            bail!("bundle directory requires a URL-safe name");
        }
        index.push_str(&format!(
            "- [{}]({name}/case-note.md) — case `{}`, repair `{}`.\n",
            record.case.title.replace(['[', ']', '\n', '\r'], " "),
            record.candidate.case_id,
            record.repair.revision
        ));
    }
    if check {
        if fs::read_to_string(output)? != index {
            bail!("generated case catalog is stale");
        }
    } else {
        fs::write(output, index)?;
    }
    Ok(())
}
