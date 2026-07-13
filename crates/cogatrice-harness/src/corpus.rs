use crate::io::{
    canonical_hash, decoded_json_bytes, read_resource, resolve_relative_resource,
    sanitized_resource_uri, sha256, verify_hash, write_json_atomic,
};
use crate::model::{Artifact, CorpusManifest, CorpusValidation, MANIFEST_SCHEMA};
use anyhow::{bail, Context, Result};
use phase_bridge::{PhaseRuntime, PHASE_REVISION};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Clone, Debug)]
pub struct MaterializeOptions {
    pub set: String,
    pub phase_card_data: String,
    pub phase_sha256: Option<String>,
    pub mtgjson: Option<String>,
    pub mtgjson_sha256: Option<String>,
    pub mtgjson_version: Option<String>,
    pub scryfall: Option<String>,
    pub scryfall_sha256: Option<String>,
    pub scryfall_snapshot: Option<String>,
    pub lands17: Option<String>,
    pub lands17_sha256: Option<String>,
    pub lands17_dataset: Option<String>,
    pub output_dir: PathBuf,
}

pub async fn materialize_corpus(options: &MaterializeOptions) -> Result<CorpusManifest> {
    require_label(
        "mtgjson",
        options.mtgjson.as_ref(),
        options.mtgjson_version.as_ref(),
    )?;
    require_label(
        "scryfall",
        options.scryfall.as_ref(),
        options.scryfall_snapshot.as_ref(),
    )?;
    require_label(
        "17lands",
        options.lands17.as_ref(),
        options.lands17_dataset.as_ref(),
    )?;
    fs::create_dir_all(options.output_dir.join("artifacts"))?;
    let mut artifacts = BTreeMap::new();

    let phase_raw = fetch_artifact(
        "phase_card_data",
        &options.phase_card_data,
        options.phase_sha256.as_deref(),
        &options.output_dir,
        &mut artifacts,
    )
    .await?;
    let phase_json = decoded_json_bytes(&phase_raw)?;
    let phase_text = std::str::from_utf8(&phase_json).context("Phase card data is not UTF-8")?;
    let runtime = PhaseRuntime::from_card_data_json(phase_text)
        .context("Phase rejected the generated card export")?;

    if let Some(uri) = &options.mtgjson {
        fetch_artifact(
            "mtgjson",
            uri,
            options.mtgjson_sha256.as_deref(),
            &options.output_dir,
            &mut artifacts,
        )
        .await?;
    }

    let scryfall_raw = if let Some(uri) = &options.scryfall {
        Some(
            fetch_artifact(
                "scryfall",
                uri,
                options.scryfall_sha256.as_deref(),
                &options.output_dir,
                &mut artifacts,
            )
            .await?,
        )
    } else {
        None
    };

    if let Some(uri) = &options.lands17 {
        fetch_artifact(
            "17lands",
            uri,
            options.lands17_sha256.as_deref(),
            &options.output_dir,
            &mut artifacts,
        )
        .await?;
    }

    let phase_value: Value = serde_json::from_slice(&phase_json)?;
    let validation = match scryfall_raw {
        Some(raw) => {
            let scryfall: Value = serde_json::from_slice(&decoded_json_bytes(&raw)?)
                .context("parse Scryfall bulk snapshot")?;
            validate_corpus(&phase_value, &scryfall, runtime.card_count())?
        }
        None => CorpusValidation {
            phase_cards: runtime.card_count(),
            phase_oracle_ids: phase_oracle_ids(&phase_value).len(),
            ..CorpusValidation::default()
        },
    };

    let validation_bytes = serde_json::to_vec_pretty(&validation)?;
    let validation_path = options.output_dir.join("validation.json");
    fs::write(&validation_path, &validation_bytes)?;
    let mut output_hashes =
        BTreeMap::from([("validation.json".to_owned(), sha256(&validation_bytes))]);
    for (name, artifact) in &artifacts {
        output_hashes.insert(name.clone(), artifact.sha256.clone());
    }

    let input_labels = [
        ("mtgjson_version", options.mtgjson_version.as_ref()),
        ("scryfall_snapshot", options.scryfall_snapshot.as_ref()),
        ("17lands_dataset", options.lands17_dataset.as_ref()),
    ]
    .into_iter()
    .filter_map(|(name, value)| value.map(|value| (name.to_owned(), value.clone())))
    .collect();
    let mut manifest = CorpusManifest {
        schema: MANIFEST_SCHEMA.to_owned(),
        manifest_id: String::new(),
        set: options.set.clone(),
        phase_revision: PHASE_REVISION.to_owned(),
        generator_schema: "phase-card-export-v1".to_owned(),
        input_labels,
        artifacts,
        output_hashes,
        validation,
    };
    manifest.manifest_id = canonical_hash(&manifest)?;
    let manifest_path = options.output_dir.join("manifest.json");
    write_json_atomic(&manifest_path, &manifest)?;
    write_json_atomic(
        &options
            .output_dir
            .join(format!("{}.manifest.json", manifest.manifest_id)),
        &manifest,
    )?;
    Ok(manifest)
}

fn require_label(name: &str, artifact: Option<&String>, label: Option<&String>) -> Result<()> {
    if artifact.is_some() && label.is_none() {
        bail!("{name} input requires an explicit immutable version/dataset label");
    }
    Ok(())
}

async fn fetch_artifact(
    name: &str,
    uri: &str,
    expected: Option<&str>,
    output_dir: &Path,
    artifacts: &mut BTreeMap<String, Artifact>,
) -> Result<Vec<u8>> {
    if (uri.starts_with("http://") || uri.starts_with("https://")) && expected.is_none() {
        let flag = name.replace('_', "-");
        bail!("remote {name} input requires an explicit --{flag}-sha256 hash");
    }
    let raw = read_resource(uri).await?;
    let hash = verify_hash(name, &raw, expected)?;
    let stored_path = format!("artifacts/{name}-{hash}.bin");
    let destination = output_dir.join(&stored_path);
    if destination.exists() {
        let existing = fs::read(&destination)?;
        verify_hash(name, &existing, Some(&hash))?;
    } else {
        fs::write(&destination, &raw)?;
    }
    artifacts.insert(
        name.to_owned(),
        Artifact {
            source: sanitized_resource_uri(uri),
            sha256: hash,
            bytes: raw.len() as u64,
            stored_path,
        },
    );
    Ok(raw)
}

pub async fn load_manifest(uri: &str) -> Result<CorpusManifest> {
    let bytes = read_resource(uri).await?;
    let manifest: CorpusManifest = serde_json::from_slice(&bytes)?;
    if manifest.schema != MANIFEST_SCHEMA {
        bail!("unsupported corpus manifest schema {}", manifest.schema);
    }
    let mut identity = manifest.clone();
    let expected = identity.manifest_id.clone();
    identity.manifest_id.clear();
    let actual = canonical_hash(&identity)?;
    if expected != actual {
        bail!("corpus manifest ID mismatch: declared {expected}, computed {actual}");
    }
    if manifest.phase_revision != PHASE_REVISION {
        bail!(
            "corpus uses Phase {}, but phase-bridge pins {}",
            manifest.phase_revision,
            PHASE_REVISION
        );
    }
    Ok(manifest)
}

pub async fn load_phase_runtime(
    manifest_uri: &str,
    manifest: &CorpusManifest,
) -> Result<PhaseRuntime> {
    let artifact = manifest
        .artifacts
        .get("phase_card_data")
        .context("manifest has no phase_card_data artifact")?;
    let uri = resolve_relative_resource(manifest_uri, &artifact.stored_path);
    let raw = read_resource(&uri).await?;
    verify_hash("phase_card_data", &raw, Some(&artifact.sha256))?;
    let decoded = decoded_json_bytes(&raw)?;
    let text = std::str::from_utf8(&decoded)?;
    Ok(PhaseRuntime::from_card_data_json(text)?)
}

pub async fn load_manifest_artifact(
    manifest_uri: &str,
    manifest: &CorpusManifest,
    name: &str,
) -> Result<Vec<u8>> {
    let artifact = manifest
        .artifacts
        .get(name)
        .with_context(|| format!("manifest has no {name} artifact"))?;
    let uri = resolve_relative_resource(manifest_uri, &artifact.stored_path);
    let raw = read_resource(&uri).await?;
    verify_hash(name, &raw, Some(&artifact.sha256))?;
    Ok(raw)
}

fn phase_oracle_ids(phase: &Value) -> BTreeSet<String> {
    phase
        .as_object()
        .into_iter()
        .flat_map(|cards| cards.values())
        .filter_map(|card| card.get("scryfall_oracle_id").and_then(Value::as_str))
        .map(str::to_owned)
        .collect()
}

fn validate_corpus(
    phase: &Value,
    scryfall: &Value,
    phase_count: usize,
) -> Result<CorpusValidation> {
    let phase_cards = phase
        .as_object()
        .context("Phase export must be an object")?;
    let scryfall_cards = scryfall
        .as_array()
        .or_else(|| scryfall.get("data").and_then(Value::as_array))
        .context("Scryfall snapshot must be an array or contain a data array")?;

    let mut by_oracle: BTreeMap<&str, Vec<&Value>> = BTreeMap::new();
    let mut layouts = BTreeMap::new();
    for card in scryfall_cards {
        if let Some(layout) = card.get("layout").and_then(Value::as_str) {
            *layouts.entry(layout.to_owned()).or_insert(0) += 1;
        }
        if let Some(id) = card.get("oracle_id").and_then(Value::as_str) {
            by_oracle.entry(id).or_default().push(card);
        }
    }

    let ids = phase_oracle_ids(phase);
    let mut validation = CorpusValidation {
        phase_cards: phase_count,
        phase_oracle_ids: ids.len(),
        scryfall_printings: scryfall_cards.len(),
        scryfall_layouts: layouts,
        ..CorpusValidation::default()
    };
    for id in &ids {
        if by_oracle.contains_key(id.as_str()) {
            validation.matched_oracle_ids += 1;
        } else {
            validation.missing_scryfall_oracle_ids.push(id.clone());
        }
    }

    for phase_card in phase_cards.values() {
        let Some(id) = phase_card.get("scryfall_oracle_id").and_then(Value::as_str) else {
            continue;
        };
        let Some(printings) = by_oracle.get(id) else {
            continue;
        };
        let phase_name = phase_card.get("name").and_then(Value::as_str).unwrap_or("");
        let candidates = printings
            .iter()
            .flat_map(|card| {
                std::iter::once(*card).chain(
                    card.get("card_faces")
                        .and_then(Value::as_array)
                        .into_iter()
                        .flatten(),
                )
            })
            .collect::<Vec<_>>();
        let matching_names = candidates
            .iter()
            .filter(|card| card.get("name").and_then(Value::as_str) == Some(phase_name))
            .copied()
            .collect::<Vec<_>>();
        if matching_names.is_empty() {
            validation
                .name_mismatches
                .push(format!("{id}: {phase_name}"));
            continue;
        }
        validation.matched_faces += 1;

        let phase_text = normalized_text(phase_card.get("oracle_text"));
        if !matching_names
            .iter()
            .any(|card| normalized_text(card.get("oracle_text")) == phase_text)
        {
            validation
                .oracle_text_mismatches
                .push(format!("{id}: {phase_name}"));
        }

        if let Some(phase_legalities) = phase_card.get("legalities").and_then(Value::as_object) {
            let compatible = printings.iter().any(|printing| {
                let Some(scryfall_legalities) =
                    printing.get("legalities").and_then(Value::as_object)
                else {
                    return false;
                };
                phase_legalities
                    .iter()
                    .all(|(format, status)| scryfall_legalities.get(format) == Some(status))
            });
            if !compatible {
                validation
                    .legality_mismatches
                    .push(format!("{id}: {phase_name}"));
            }
        }
    }

    validation.missing_scryfall_oracle_ids.sort();
    validation.name_mismatches.sort();
    validation.name_mismatches.dedup();
    validation.oracle_text_mismatches.sort();
    validation.oracle_text_mismatches.dedup();
    validation.legality_mismatches.sort();
    validation.legality_mismatches.dedup();
    Ok(validation)
}

fn normalized_text(value: Option<&Value>) -> String {
    value
        .and_then(Value::as_str)
        .unwrap_or("")
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}
