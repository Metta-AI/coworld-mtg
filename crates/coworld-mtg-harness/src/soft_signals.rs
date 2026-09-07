use crate::corpus::{load_manifest, load_manifest_artifact};
use crate::io::{
    decoded_json_bytes, read_resource, sanitized_resource_uri, verify_hash, write_json_atomic,
};
use crate::model::{
    CardsMappingProvenance, CastResolution, NamedCount, NumericSummary, RecordedCast,
    RecordedCastKind, ReplayNormalization, ReplayPlayer, SoftSignalReport, SOFT_SIGNAL_SCHEMA,
};
use anyhow::{bail, Context, Result};
use clap::ValueEnum;
use serde::Deserialize;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, ValueEnum)]
pub enum Lands17InputSchema {
    #[default]
    Auto,
    #[value(name = "legacy-named-v1")]
    LegacyNamedV1,
    #[value(name = "public-replay-wide-v1")]
    PublicReplayWideV1,
}

#[derive(Clone, Debug)]
pub struct CardsCsvInput {
    pub source: String,
    pub sha256: String,
}

#[derive(Clone, Debug, Default)]
pub struct Mine17landsOptions {
    pub input_schema: Lands17InputSchema,
    pub cards_csv: Option<CardsCsvInput>,
}

/// Retain the named-card input API; real public replay rows require a mapping.
pub async fn mine_17lands(
    manifest_uri: &str,
    output: &Path,
    row_limit: Option<u64>,
) -> Result<SoftSignalReport> {
    mine_17lands_with_options(
        manifest_uri,
        output,
        row_limit,
        &Mine17landsOptions::default(),
    )
    .await
}

pub async fn mine_17lands_with_options(
    manifest_uri: &str,
    output: &Path,
    row_limit: Option<u64>,
    options: &Mine17landsOptions,
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
    let original_headers = reader.headers()?.clone();
    let looks_wide = original_headers.iter().any(looks_like_replay_column);
    let wide = match options.input_schema {
        Lands17InputSchema::Auto => auto_schema(&original_headers)?,
        Lands17InputSchema::PublicReplayWideV1 => true,
        Lands17InputSchema::LegacyNamedV1 if looks_wide => {
            bail!(
                "public replay turn columns require public-replay-wide-v1 and a cards CSV mapping"
            )
        }
        Lands17InputSchema::LegacyNamedV1 => false,
    };
    let headers = original_headers
        .iter()
        .map(|header| header.to_ascii_lowercase())
        .collect::<Vec<_>>();
    let cast_columns = if wide {
        Some(parse_replay_headers(&original_headers)?)
    } else {
        if options.cards_csv.is_some() {
            bail!("cards CSV mapping is only used with public-replay-wide-v1");
        }
        None
    };
    let mapping = if wide {
        let input = options
            .cards_csv
            .as_ref()
            .context("public-replay-wide-v1 requires --cards-csv and --cards-csv-sha256")?;
        let raw = read_resource(&input.source).await?;
        let hash = verify_hash("17Lands cards CSV", &raw, Some(&input.sha256))?;
        Some((
            parse_cards_mapping(&decoded_json_bytes(&raw)?)?,
            CardsMappingProvenance {
                source: sanitized_resource_uri(&input.source),
                sha256: hash,
                bytes: raw.len() as u64,
            },
        ))
    } else {
        None
    };
    let mut cards = BTreeMap::<String, u64>::new();
    let mut events = BTreeMap::<String, u64>::new();
    let mut numeric = BTreeMap::<String, NumericAccumulator>::new();
    let mut casts = Vec::new();
    let mut rows = 0u64;

    for record in reader.records() {
        if row_limit.is_some_and(|limit| rows >= limit) {
            break;
        }
        let record = record?;
        rows += 1;
        if let (Some(columns), Some((mapping, _))) = (&cast_columns, &mapping) {
            if record.len() != original_headers.len() {
                bail!("public replay data row {rows} has a different column count from its header");
            }
            for (index, column) in columns {
                let value = &record[*index];
                if value.is_empty() {
                    continue;
                }
                for (value_index, raw_id) in value.split('|').enumerate() {
                    let arena_id = arena_id(raw_id);
                    let resolution = match arena_id {
                        Some(id) => match mapping.get(&id) {
                            Some(name) => {
                                *cards.entry(name.clone()).or_default() += 1;
                                CastResolution::Mapped { name: name.clone() }
                            }
                            None => CastResolution::Unmapped {
                                reason: "unknown_arena_id".into(),
                            },
                        },
                        None => CastResolution::Invalid {
                            reason: "expected_positive_decimal_arena_id".into(),
                        },
                    };
                    casts.push(RecordedCast {
                        row: rows,
                        column: original_headers[*index].to_owned(),
                        value_index,
                        raw_id: raw_id.to_owned(),
                        arena_id,
                        turn_number: column.turn_number,
                        active_player: column.active_player,
                        casting_player: column.casting_player,
                        cast_kind: column.cast_kind,
                        resolution,
                    });
                }
            }
        }
        for (index, value) in record.iter().enumerate() {
            let Some(header) = headers.get(index) else {
                continue;
            };
            if !wide && card_column(header) {
                collect_card_values(value, &mut cards);
            }
            if event_column(header) && !value.trim().is_empty() {
                *events.entry(value.trim().to_owned()).or_insert(0) += 1;
            }
            let is_numeric = if wide {
                // Never reinterpret single card IDs or card-ID lists as measurements.
                header == "num_turns" || header.ends_with("_mana_spent")
            } else {
                numeric_column(header)
            };
            if is_numeric {
                if let Ok(value) = value.parse::<f64>() {
                    if value.is_finite() {
                        numeric.entry(header.clone()).or_default().add(value);
                    }
                }
            }
        }
    }
    let normalization = mapping.map(|(_, provenance)| normalization(casts, provenance));
    let interpretation = if wide {
        "Recorded cast occurrences normalized with the supplied Arena card mapping. Source column order is not game-action order. Mapping coverage is observable; these data are not a rules oracle or a gameplay conformance gate."
    } else {
        "Observational workload evidence only; no value in this report is a rules oracle or hard conformance gate."
    };
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
        normalization,
        interpretation: interpretation.to_owned(),
    };
    write_json_atomic(output, &report)?;
    Ok(report)
}

fn auto_schema(headers: &csv::StringRecord) -> Result<bool> {
    let wide = headers.iter().any(looks_like_replay_column);
    // These named-value columns belong to the supported legacy input family.
    // Public replay's opening_hand field contains Arena IDs, so it is not a
    // stand-alone named-schema marker.
    let named = headers.iter().any(|header| {
        matches!(
            header,
            "card_name"
                | "card_names"
                | "cards"
                | "deck"
                | "decklist"
                | "drawn_cards"
                | "sideboard"
                | "sideboard_cards"
        )
    });
    match (wide, named) {
        (true, true) => bail!(
            "ambiguous 17Lands input: both public turn columns and named-card columns; select an explicit --input-schema"
        ),
        (true, false) => Ok(true),
        (false, true) => Ok(false),
        (false, false) => bail!(
            "unknown 17Lands input schema: expected public replay turn columns or supported named-card columns; use --input-schema legacy-named-v1 only for known legacy named values"
        ),
    }
}

fn looks_like_replay_column(header: &str) -> bool {
    let lowercase = header.to_ascii_lowercase();
    lowercase.starts_with("user_turn_") || lowercase.starts_with("oppo_turn_")
}

fn arena_id(raw: &str) -> Option<u32> {
    if raw.is_empty() || !raw.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    raw.parse::<u32>().ok().filter(|value| *value > 0)
}

#[derive(Debug, Deserialize)]
struct CardMappingRow {
    id: String,
    name: String,
}

fn parse_cards_mapping(bytes: &[u8]) -> Result<BTreeMap<u32, String>> {
    let mut reader = csv::Reader::from_reader(bytes);
    let headers = reader.headers()?;
    let unique = headers.iter().collect::<BTreeSet<_>>();
    if unique.len() != headers.len() || !unique.contains("id") || !unique.contains("name") {
        bail!("cards CSV requires unique headers including id and name");
    }
    let mut result = BTreeMap::new();
    for (index, row) in reader.deserialize::<CardMappingRow>().enumerate() {
        let row = row.with_context(|| format!("invalid cards CSV data row {}", index + 1))?;
        let id = arena_id(&row.id)
            .with_context(|| format!("invalid Arena ID at cards CSV data row {}", index + 1))?;
        if row.name.trim().is_empty() {
            bail!("empty card name at cards CSV data row {}", index + 1);
        }
        if let Some(previous) = result.insert(id, row.name.clone()) {
            if previous != row.name {
                bail!("cards CSV gives conflicting names for Arena ID {id}");
            }
        }
    }
    if result.is_empty() {
        bail!("cards CSV contains no card mappings");
    }
    Ok(result)
}

#[derive(Clone, Copy, Debug)]
struct CastColumn {
    turn_number: u32,
    active_player: ReplayPlayer,
    casting_player: ReplayPlayer,
    cast_kind: RecordedCastKind,
}

fn parse_cast_column(header: &str) -> Option<CastColumn> {
    let (active_player, rest) = if let Some(rest) = header.strip_prefix("user_turn_") {
        (ReplayPlayer::User, rest)
    } else {
        let rest = header.strip_prefix("oppo_turn_")?;
        (ReplayPlayer::Oppo, rest)
    };
    let (turn, suffix) = rest.split_once('_')?;
    let turn_number = arena_id(turn)?;
    let (casting_player, cast_kind) = match suffix {
        "creatures_cast" => (active_player, RecordedCastKind::Creature),
        "non_creatures_cast" => (active_player, RecordedCastKind::NonCreature),
        "user_instants_sorceries_cast" => (ReplayPlayer::User, RecordedCastKind::InstantSorcery),
        "oppo_instants_sorceries_cast" => (ReplayPlayer::Oppo, RecordedCastKind::InstantSorcery),
        _ => return None,
    };
    Some(CastColumn {
        turn_number,
        active_player,
        casting_player,
        cast_kind,
    })
}

fn parse_replay_headers(headers: &csv::StringRecord) -> Result<Vec<(usize, CastColumn)>> {
    let unique = headers.iter().collect::<BTreeSet<_>>();
    if unique.len() != headers.len() {
        bail!("public replay CSV has duplicate column names");
    }
    for required in ["draft_id", "build_index", "match_number", "game_number"] {
        if !unique.contains(required) {
            bail!("public-replay-wide-v1 requires the {required} column");
        }
    }
    let mut columns = Vec::new();
    for (index, header) in headers.iter().enumerate() {
        if looks_like_replay_column(header) && header != header.to_ascii_lowercase() {
            bail!("public replay schema requires lowercase column names; found {header}");
        }
        if let Some(column) = parse_cast_column(header) {
            columns.push((index, column));
        } else if (header.starts_with("user_turn_") || header.starts_with("oppo_turn_"))
            && header.ends_with("_cast")
        {
            bail!("unsupported public replay cast column {header}");
        }
    }
    if columns.is_empty() {
        bail!("public-replay-wide-v1 has no supported per-turn cast columns");
    }
    Ok(columns)
}

fn normalization(
    casts: Vec<RecordedCast>,
    cards_mapping: CardsMappingProvenance,
) -> ReplayNormalization {
    let mut all_ids = BTreeSet::new();
    let mut mapped_ids = BTreeSet::new();
    let mut mapped = 0;
    let mut unmapped = 0;
    let mut invalid = 0;
    for cast in &casts {
        if let Some(id) = cast.arena_id {
            all_ids.insert(id);
        }
        match &cast.resolution {
            CastResolution::Mapped { .. } => {
                mapped += 1;
                if let Some(id) = cast.arena_id {
                    mapped_ids.insert(id);
                }
            }
            CastResolution::Unmapped { .. } => unmapped += 1,
            CastResolution::Invalid { .. } => invalid += 1,
        }
    }
    ReplayNormalization {
        schema: "17lands-public-replay-wide-v1".to_owned(),
        cards_mapping,
        cast_occurrences: casts.len() as u64,
        mapped_cast_occurrences: mapped,
        unmapped_cast_occurrences: unmapped,
        invalid_cast_occurrences: invalid,
        distinct_cast_arena_ids: all_ids.len() as u64,
        distinct_mapped_cast_arena_ids: mapped_ids.len() as u64,
        casts,
    }
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::io::{canonical_hash, sha256};
    use crate::model::{Artifact, CorpusManifest, CorpusValidation, MANIFEST_SCHEMA};
    use std::fs;
    use tempfile::TempDir;

    const OBSERVED_GAME: &[u8] =
        include_bytes!("../tests/fixtures/17lands-msh-replay-v1/observed-first-game.csv");
    const OFFICIAL_MAPPING_SUBSET: &[u8] =
        include_bytes!("../tests/fixtures/17lands-msh-replay-v1/cards-subset.csv");
    const EXPECTED_CASTS: &[u8] =
        include_bytes!("../tests/fixtures/17lands-msh-replay-v1/expected-casts.json");

    fn source_manifest(temp: &TempDir, bytes: &[u8]) -> String {
        fs::write(temp.path().join("observations.csv"), bytes).unwrap();
        let artifact = Artifact {
            source: "test-input:explicit-source-fixture".into(),
            sha256: sha256(bytes),
            bytes: bytes.len() as u64,
            stored_path: "observations.csv".into(),
        };
        // This manifest binds a miner input only; it asserts no Phase card corpus.
        let mut manifest = CorpusManifest {
            schema: MANIFEST_SCHEMA.into(),
            manifest_id: String::new(),
            set: "source-ingestion-test".into(),
            phase_revision: phase_bridge::PHASE_REVISION.into(),
            generator_schema: "miner-input-fixture".into(),
            input_labels: BTreeMap::from([("17lands_dataset".into(), "test-fixture".into())]),
            artifacts: BTreeMap::from([("17lands".into(), artifact)]),
            output_hashes: BTreeMap::new(),
            validation: CorpusValidation::default(),
        };
        manifest.manifest_id = canonical_hash(&manifest).unwrap();
        let path = temp.path().join("manifest.json");
        fs::write(&path, serde_json::to_vec(&manifest).unwrap()).unwrap();
        path.to_string_lossy().into_owned()
    }

    fn mapping_options(temp: &TempDir, bytes: &[u8]) -> Mine17landsOptions {
        let path = temp.path().join("cards.csv");
        fs::write(&path, bytes).unwrap();
        Mine17landsOptions {
            input_schema: Lands17InputSchema::PublicReplayWideV1,
            cards_csv: Some(CardsCsvInput {
                source: path.to_string_lossy().into_owned(),
                sha256: sha256(bytes),
            }),
        }
    }

    #[tokio::test]
    async fn authentic_observed_game_preserves_cast_counts_identity_and_provenance() {
        let temp = TempDir::new().unwrap();
        let manifest = source_manifest(&temp, OBSERVED_GAME);
        let options = mapping_options(&temp, OFFICIAL_MAPPING_SUBSET);
        let report =
            mine_17lands_with_options(&manifest, &temp.path().join("report.json"), None, &options)
                .await
                .unwrap();
        let expected: Value = serde_json::from_slice(EXPECTED_CASTS).unwrap();
        let normalized = report.normalization.as_ref().unwrap();
        assert_eq!(report.rows, 1);
        assert_eq!(report.dataset_sha256, sha256(OBSERVED_GAME));
        assert_eq!(normalized.cast_occurrences, 19);
        assert_eq!(normalized.mapped_cast_occurrences, 19);
        assert_eq!(normalized.distinct_cast_arena_ids, 15);
        assert_eq!(normalized.distinct_mapped_cast_arena_ids, 15);
        assert_eq!(normalized.unmapped_cast_occurrences, 0);
        assert_eq!(normalized.invalid_cast_occurrences, 0);
        assert_eq!(
            normalized.cards_mapping.sha256,
            sha256(OFFICIAL_MAPPING_SUBSET)
        );
        assert_eq!(
            normalized.cards_mapping.bytes,
            OFFICIAL_MAPPING_SUBSET.len() as u64
        );
        let actual_names = report
            .card_frequency
            .iter()
            .map(|entry| (entry.name.clone(), entry.count))
            .collect::<BTreeMap<_, _>>();
        let expected_names: BTreeMap<String, u64> =
            serde_json::from_value(expected["name_counts"].clone()).unwrap();
        assert_eq!(actual_names, expected_names);
        let projected = normalized
            .casts
            .iter()
            .map(|cast| {
                let CastResolution::Mapped { name } = &cast.resolution else {
                    panic!("known fixture must map")
                };
                serde_json::json!({
                    "row": cast.row, "column": cast.column, "value_index": cast.value_index,
                    "arena_id": cast.arena_id.unwrap(), "name": name,
                })
            })
            .collect::<Vec<_>>();
        assert_eq!(serde_json::json!(projected), expected["casts"]);
        assert!(!report
            .numeric_summaries
            .contains_key("user_turn_2_creatures_cast"));
        assert!(report.interpretation.contains("not game-action order"));
    }

    #[tokio::test]
    async fn unknown_invalid_and_repeated_ids_remain_visible_without_count_inflation() {
        // Structural protocol fixture; no claim these rows are observed gameplay.
        let input = b"draft_id,build_index,match_number,game_number,user_turn_1_creatures_cast,user_total_creatures_cast,user_turn_1_eot_user_creatures_in_play\nfixture,0,1,1,10|10|999||x,999,10|10|10\n";
        let temp = TempDir::new().unwrap();
        let manifest = source_manifest(&temp, input);
        let options = mapping_options(&temp, b"id,name\n10,Test Card\n");
        let report =
            mine_17lands_with_options(&manifest, &temp.path().join("report.json"), None, &options)
                .await
                .unwrap();
        assert_eq!(
            report.card_frequency,
            vec![NamedCount {
                name: "Test Card".into(),
                count: 2
            }]
        );
        let normalized = report.normalization.unwrap();
        assert_eq!(normalized.cast_occurrences, 5);
        assert_eq!(normalized.mapped_cast_occurrences, 2);
        assert_eq!(normalized.unmapped_cast_occurrences, 1);
        assert_eq!(normalized.invalid_cast_occurrences, 2);
        assert_eq!(normalized.distinct_cast_arena_ids, 2);
        assert_eq!(normalized.distinct_mapped_cast_arena_ids, 1);
        assert_eq!(normalized.casts[3].raw_id, "");
        assert_eq!(normalized.casts[3].value_index, 3);
        assert!(matches!(
            normalized.casts[2].resolution,
            CastResolution::Unmapped { .. }
        ));
        assert!(matches!(
            normalized.casts[4].resolution,
            CastResolution::Invalid { .. }
        ));
    }

    #[tokio::test]
    async fn missing_or_corrupt_mapping_refuses_output_and_preserves_existing_report() {
        let temp = TempDir::new().unwrap();
        let manifest = source_manifest(&temp, OBSERVED_GAME);
        let output = temp.path().join("report.json");
        fs::write(&output, b"retained-existing-report").unwrap();
        let error = mine_17lands(&manifest, &output, None).await.unwrap_err();
        assert!(error.to_string().contains("--cards-csv"));
        let mut options = mapping_options(&temp, OFFICIAL_MAPPING_SUBSET);
        options.cards_csv.as_mut().unwrap().sha256 = "0".repeat(64);
        let error = mine_17lands_with_options(&manifest, &output, None, &options)
            .await
            .unwrap_err();
        assert!(error.to_string().contains("sha256 mismatch"));
        assert_eq!(fs::read(output).unwrap(), b"retained-existing-report");
    }

    #[test]
    fn mapping_collisions_and_bad_identity_are_explicit_errors() {
        assert!(parse_cards_mapping(b"id,name\n10,A\n10,B\n").is_err());
        assert_eq!(
            parse_cards_mapping(b"id,name\n10,A\n10,A\n").unwrap().len(),
            1
        );
        assert!(parse_cards_mapping(b"id,name\n0,A\n").is_err());
        assert!(parse_cards_mapping(b"id,name\nx,A\n").is_err());
        assert!(parse_cards_mapping(b"id,name,name\n10,A,A\n").is_err());
        assert!(parse_cards_mapping(b"id,name\n10,\n").is_err());
        assert!(parse_cards_mapping(b"id,name\n").is_err());
        for value in ["-1", "1.0", " 10", "4294967296", ""] {
            assert_eq!(arena_id(value), None, "{value}");
        }
    }

    #[test]
    fn schema_rejects_ambiguous_headers_and_preserves_turn_player_roles() {
        let base = ["draft_id", "build_index", "match_number", "game_number"];
        for bad in ["user_turn_0_creatures_cast", "user_turn_2_mystery_cast"] {
            let mut headers = csv::StringRecord::from(base.to_vec());
            headers.push_field(bad);
            assert!(parse_replay_headers(&headers).is_err());
        }
        let headers = csv::StringRecord::from(vec![
            "draft_id",
            "build_index",
            "match_number",
            "game_number",
            "user_turn_1_creatures_cast",
            "user_turn_1_creatures_cast",
        ]);
        assert!(parse_replay_headers(&headers).is_err());
        let column = parse_cast_column("oppo_turn_7_user_instants_sorceries_cast").unwrap();
        assert_eq!(column.active_player, ReplayPlayer::Oppo);
        assert_eq!(column.casting_player, ReplayPlayer::User);
        assert_eq!(column.turn_number, 7);
        assert_eq!(column.cast_kind, RecordedCastKind::InstantSorcery);
        let column = parse_cast_column("user_turn_3_non_creatures_cast").unwrap();
        assert_eq!(column.cast_kind, RecordedCastKind::NonCreature);
        assert!(parse_cast_column("user_total_creatures_cast").is_none());
    }

    #[tokio::test]
    async fn row_limits_and_same_name_arena_aliases_keep_exact_occurrence_counts() {
        let input = b"draft_id,build_index,match_number,game_number,oppo_turn_1_creatures_cast\nfixture,0,1,1,10|11\nfixture,0,1,2,10\n";
        let temp = TempDir::new().unwrap();
        let manifest = source_manifest(&temp, input);
        let options = mapping_options(&temp, b"id,name\n10,Same Name\n11,Same Name\n");
        let report = mine_17lands_with_options(
            &manifest,
            &temp.path().join("report.json"),
            Some(1),
            &options,
        )
        .await
        .unwrap();
        assert_eq!(report.rows, 1);
        assert_eq!(report.card_frequency[0].count, 2);
        assert_eq!(
            report
                .normalization
                .as_ref()
                .unwrap()
                .distinct_mapped_cast_arena_ids,
            2
        );
        let empty = mine_17lands_with_options(
            &manifest,
            &temp.path().join("empty.json"),
            Some(0),
            &options,
        )
        .await
        .unwrap();
        assert_eq!(empty.rows, 0);
        assert_eq!(empty.normalization.unwrap().cast_occurrences, 0);
    }

    #[tokio::test]
    async fn malformed_public_row_is_rejected_instead_of_silently_skipping_columns() {
        let input = b"draft_id,build_index,match_number,game_number,user_turn_1_creatures_cast\nfixture,0,1,1\n";
        let temp = TempDir::new().unwrap();
        let manifest = source_manifest(&temp, input);
        let options = mapping_options(&temp, b"id,name\n10,Test Card\n");
        let output = temp.path().join("report.json");
        let error = mine_17lands_with_options(&manifest, &output, None, &options)
            .await
            .unwrap_err();
        assert!(error.to_string().contains("column count"));
        assert!(!output.exists());
    }

    #[tokio::test]
    async fn named_card_inputs_keep_existing_frequency_semantics() {
        let input = b"event_type,card_name,drawn_cards,turn,damage\ncast,Mountain,\"[\"\"Goblin Piker\"\"]\",2,0\nattack,Raging Goblin,[],3,1\n";
        let temp = TempDir::new().unwrap();
        let manifest = source_manifest(&temp, input);
        let report = mine_17lands(&manifest, &temp.path().join("report.json"), None)
            .await
            .unwrap();
        assert_eq!(report.rows, 2);
        assert!(report.normalization.is_none());
        assert_eq!(report.card_frequency.len(), 3);
        assert!(report
            .card_frequency
            .iter()
            .any(|card| card.name == "Goblin Piker"));
        assert_eq!(report.numeric_summaries["turn"].mean, 2.5);
    }
    #[tokio::test]
    async fn auto_rejects_unknown_case_changed_and_ambiguous_inputs_without_overwriting() {
        let inputs: [&[u8]; 3] = [
            b"unknown,value\nrecord,10\n",
            b"draft_id,build_index,match_number,game_number,User_Turn_1_creatures_cast\nfixture,0,1,1,10\n",
            b"draft_id,build_index,match_number,game_number,card_name,user_turn_1_creatures_cast\nfixture,0,1,1,Test Card,10\n",
        ];
        for input in inputs {
            let temp = TempDir::new().unwrap();
            let manifest = source_manifest(&temp, input);
            let output = temp.path().join("report.json");
            fs::write(&output, b"existing-report").unwrap();
            let error = mine_17lands(&manifest, &output, None).await.unwrap_err();
            assert!(
                error.to_string().contains("schema"),
                "expected an actionable schema error, got {error}"
            );
            assert_eq!(fs::read(output).unwrap(), b"existing-report");
        }
    }

    #[tokio::test]
    async fn auto_reaches_named_families_and_explicit_legacy_retains_broad_headers() {
        for header in ["cards", "deck", "sideboard_cards"] {
            let temp = TempDir::new().unwrap();
            let input = format!("{header}\nTest Card\n");
            let manifest = source_manifest(&temp, input.as_bytes());
            let report = mine_17lands(&manifest, &temp.path().join("report.json"), None)
                .await
                .unwrap();
            assert_eq!(
                report.card_frequency,
                vec![NamedCount {
                    name: "Test Card".into(),
                    count: 1
                }]
            );
            assert!(report.normalization.is_none());
        }
        let temp = TempDir::new().unwrap();
        let manifest = source_manifest(&temp, b"custom_deck_values\nTest Card\n");
        assert!(
            mine_17lands(&manifest, &temp.path().join("auto.json"), None)
                .await
                .is_err()
        );
        let options = Mine17landsOptions {
            input_schema: Lands17InputSchema::LegacyNamedV1,
            cards_csv: None,
        };
        let report =
            mine_17lands_with_options(&manifest, &temp.path().join("legacy.json"), None, &options)
                .await
                .unwrap();
        assert_eq!(report.card_frequency[0].name, "Test Card");
    }
}
