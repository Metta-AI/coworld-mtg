use crate::corpus::{load_manifest, load_manifest_artifact};
use crate::io::{decoded_json_bytes, write_json_atomic};
use crate::model::{NamedCount, NumericSummary, SoftSignalReport, SOFT_SIGNAL_SCHEMA};
use anyhow::{Context, Result};
use serde_json::Value;
use std::collections::BTreeMap;
use std::path::Path;

pub async fn mine_17lands(
    manifest_uri: &str,
    output: &Path,
    row_limit: Option<u64>,
) -> Result<SoftSignalReport> {
    let manifest = load_manifest(manifest_uri).await?;
    let artifact = manifest
        .artifacts
        .get("17lands")
        .context("manifest has no 17lands artifact")?;
    let raw = load_manifest_artifact(manifest_uri, &manifest, "17lands").await?;
    let decoded = decoded_json_bytes(&raw)?;

    let mut reader = csv::ReaderBuilder::new()
        .flexible(true)
        .from_reader(decoded.as_slice());
    let headers = reader
        .headers()?
        .iter()
        .map(|header| header.to_ascii_lowercase())
        .collect::<Vec<_>>();
    let mut cards = BTreeMap::<String, u64>::new();
    let mut events = BTreeMap::<String, u64>::new();
    let mut numeric = BTreeMap::<String, NumericAccumulator>::new();
    let mut rows = 0u64;

    for record in reader.records() {
        if row_limit.is_some_and(|limit| rows >= limit) {
            break;
        }
        let record = record?;
        rows += 1;
        for (index, value) in record.iter().enumerate() {
            let Some(header) = headers.get(index) else {
                continue;
            };
            if card_column(header) {
                collect_card_values(value, &mut cards);
            }
            if event_column(header) && !value.trim().is_empty() {
                *events.entry(value.trim().to_owned()).or_insert(0) += 1;
            }
            if numeric_column(header) {
                if let Ok(value) = value.parse::<f64>() {
                    numeric.entry(header.clone()).or_default().add(value);
                }
            }
        }
    }

    let report = SoftSignalReport {
        schema: SOFT_SIGNAL_SCHEMA.to_owned(),
        manifest_id: manifest.manifest_id,
        dataset_sha256: artifact.sha256.clone(),
        rows,
        card_frequency: ranked(cards),
        event_frequency: ranked(events),
        numeric_summaries: numeric
            .into_iter()
            .map(|(name, values)| (name, values.finish()))
            .collect(),
        interpretation: "Observational workload evidence only; no value in this report is a rules oracle or hard conformance gate.".to_owned(),
    };
    write_json_atomic(output, &report)?;
    Ok(report)
}

fn card_column(header: &str) -> bool {
    !header.ends_with("_id")
        && !header.ends_with("_hash")
        && !header.ends_with("_uri")
        && (header.contains("card")
            || header.contains("deck")
            || header.contains("opening_hand")
            || header.contains("drawn")
            || header.contains("sideboard"))
}

fn event_column(header: &str) -> bool {
    header == "event_type" || header == "action" || header == "event"
}

fn numeric_column(header: &str) -> bool {
    header.contains("turn")
        || header.contains("damage")
        || header.contains("mana_spent")
        || header.contains("game_length")
}

fn collect_card_values(raw: &str, counts: &mut BTreeMap<String, u64>) {
    let trimmed = raw.trim();
    if trimmed.is_empty() {
        return;
    }
    if let Ok(value) = serde_json::from_str::<Value>(trimmed) {
        collect_json_strings(&value, counts);
        return;
    }
    for value in trimmed.split(['|', ';']) {
        let value = value.trim().trim_matches('"');
        if plausible_card_name(value) {
            *counts.entry(value.to_owned()).or_insert(0) += 1;
        }
    }
}

fn collect_json_strings(value: &Value, counts: &mut BTreeMap<String, u64>) {
    match value {
        Value::String(value) if plausible_card_name(value) => {
            *counts.entry(value.clone()).or_insert(0) += 1;
        }
        Value::Array(values) => {
            for value in values {
                collect_json_strings(value, counts);
            }
        }
        Value::Object(values) => {
            if let Some(name) = values
                .get("name")
                .or_else(|| values.get("card_name"))
                .and_then(Value::as_str)
            {
                if plausible_card_name(name) {
                    let count = values.get("count").and_then(Value::as_u64).unwrap_or(1);
                    *counts.entry(name.to_owned()).or_insert(0) += count;
                }
                return;
            }
            for (key, value) in values {
                if plausible_card_name(key) && value.as_u64().is_some() {
                    let count = value.as_u64().unwrap_or(0);
                    *counts.entry(key.clone()).or_insert(0) += count;
                } else {
                    collect_json_strings(value, counts);
                }
            }
        }
        _ => {}
    }
}

fn plausible_card_name(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 200
        && value.chars().any(char::is_alphabetic)
        && !value.starts_with("http")
}

fn ranked(counts: BTreeMap<String, u64>) -> Vec<NamedCount> {
    let mut values = counts
        .into_iter()
        .map(|(name, count)| NamedCount { name, count })
        .collect::<Vec<_>>();
    values.sort_by(|left, right| {
        right
            .count
            .cmp(&left.count)
            .then_with(|| left.name.cmp(&right.name))
    });
    values
}

#[derive(Default)]
struct NumericAccumulator {
    observations: u64,
    sum: f64,
    min: f64,
    max: f64,
}

impl NumericAccumulator {
    fn add(&mut self, value: f64) {
        if self.observations == 0 {
            self.min = value;
            self.max = value;
        } else {
            self.min = self.min.min(value);
            self.max = self.max.max(value);
        }
        self.observations += 1;
        self.sum += value;
    }

    fn finish(self) -> NumericSummary {
        NumericSummary {
            observations: self.observations,
            mean: if self.observations == 0 {
                0.0
            } else {
                self.sum / self.observations as f64
            },
            min: self.min,
            max: self.max,
        }
    }
}
