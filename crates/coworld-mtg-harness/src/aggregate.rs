use crate::io::write_json_atomic;
use crate::model::{Finding, RunCounts, RunResult, Scoreboard, ScoreboardEntry, SCOREBOARD_SCHEMA};
use anyhow::{Context, Result};
use flate2::read::MultiGzDecoder;
use serde_json::json;
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, File};
use std::io::{BufRead, BufReader};
use std::path::PathBuf;

#[derive(Clone, Debug)]
pub struct AggregateOptions {
    pub run_dirs: Vec<PathBuf>,
    pub output: PathBuf,
}

pub fn aggregate_results(options: &AggregateOptions) -> Result<Scoreboard> {
    let mut manifests = BTreeSet::new();
    let mut counts = RunCounts::default();
    let mut entries: BTreeMap<String, ScoreboardEntry> = BTreeMap::new();
    let mut run_count = 0usize;

    for directory in &options.run_dirs {
        let result_path = directory.join("result.json");
        let result: RunResult = serde_json::from_slice(
            &fs::read(&result_path).with_context(|| format!("read {}", result_path.display()))?,
        )?;
        run_count += 1;
        manifests.insert(result.manifest_id);
        counts.attempted += result.counts.attempted;
        counts.completed += result.counts.completed;
        counts.action_budget_exhausted += result.counts.action_budget_exhausted;
        counts.hard_failures += result.counts.hard_failures;
        counts.actions += result.counts.actions;

        let findings_path = directory.join("findings.jsonl.gz");
        if findings_path.exists() {
            let reader = BufReader::new(MultiGzDecoder::new(File::open(&findings_path)?));
            for line in reader.lines() {
                let line = line?;
                if line.trim().is_empty() {
                    continue;
                }
                let finding: Finding = serde_json::from_str(&line)?;
                let entry =
                    entries
                        .entry(finding.signature.clone())
                        .or_insert_with(|| ScoreboardEntry {
                            signature: finding.signature,
                            classification: finding.classification,
                            occurrences: 0,
                            seeds: Vec::new(),
                            detail: finding.detail,
                        });
                entry.occurrences += 1;
                if entry.seeds.len() < 20 && !entry.seeds.contains(&finding.seed) {
                    entry.seeds.push(finding.seed);
                }
            }
        }
    }

    let mut findings = entries.into_values().collect::<Vec<_>>();
    findings.sort_by(|left, right| {
        right
            .occurrences
            .cmp(&left.occurrences)
            .then_with(|| left.signature.cmp(&right.signature))
    });
    let completion_rate = if counts.attempted == 0 {
        0.0
    } else {
        counts.completed as f64 / counts.attempted as f64
    };
    let budget_rate = if counts.attempted == 0 {
        0.0
    } else {
        counts.action_budget_exhausted as f64 / counts.attempted as f64
    };
    let scoreboard = Scoreboard {
        schema: SCOREBOARD_SCHEMA.to_owned(),
        manifest_ids: manifests.into_iter().collect(),
        runs: run_count,
        counts,
        findings,
        // These are operational signals, not semantic assertions. 17Lands
        // comparisons can be added under the same explicitly soft namespace.
        soft_signals: BTreeMap::from([
            ("game_completion_rate".to_owned(), json!(completion_rate)),
            ("action_budget_rate".to_owned(), json!(budget_rate)),
        ]),
    };
    write_json_atomic(&options.output, &scoreboard)?;
    Ok(scoreboard)
}
