//! Inspect authentic card records through Phase's public Oracle parser.
//! This adapter supplies metadata and reports the engine's output; it does not
//! decide whether a parsed ability follows a rule or satisfies an expectation.
use crate::PHASE_REVISION;
use phase_engine::parser::oracle::parse_oracle_text;
use phase_engine::parser::oracle_util::parse_subtype;
use phase_engine::types::card_type::{CoreType, Supertype};
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Deserialize)]
pub struct OracleCardInput {
    pub id: String,
    pub oracle_id: String,
    pub name: String,
    pub layout: String,
    pub type_line: String,
    #[serde(default)]
    pub oracle_text: String,
    #[serde(default)]
    pub keywords: Vec<String>,
}

#[derive(Debug, Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum OracleInspection {
    Parsed {
        card_id: String,
        oracle_id: String,
        name: String,
        phase_revision: String,
        types: Vec<String>,
        subtypes: Vec<String>,
        parsed: Value,
    },
    Inconclusive {
        card_id: Option<String>,
        oracle_id: Option<String>,
        detail: String,
    },
}

/// Translate Scryfall's printed type line using Phase's own vocabulary.
/// Unknown metadata is reported instead of silently altering parser context.
fn type_context(line: &str) -> Result<(Vec<String>, Vec<String>), String> {
    let (left, right) = line.split_once('—').unwrap_or((line, ""));
    let mut types = Vec::new();
    for word in left.split_whitespace() {
        if let Ok(core) = word.parse::<CoreType>() {
            types.push(core.to_string());
        } else if word.parse::<Supertype>().is_err() {
            return Err(format!("type line contains an unknown Phase type: {word}"));
        }
    }
    if types.is_empty() {
        return Err("type line has no recognized core type".into());
    }
    let lowercase = right.trim().to_lowercase();
    let mut remaining = lowercase.as_str();
    let mut subtypes = Vec::new();
    while !remaining.is_empty() {
        let Some((subtype, consumed)) = parse_subtype(remaining) else {
            return Err(format!(
                "Phase cannot interpret this subtype suffix: {remaining}"
            ));
        };
        if consumed == 0 || !remaining.is_char_boundary(consumed) {
            return Err("Phase subtype parser returned an invalid boundary".into());
        }
        subtypes.push(subtype);
        remaining = remaining[consumed..].trim_start();
    }
    Ok((types, subtypes))
}

pub fn inspect_oracle_card(record: Value) -> OracleInspection {
    let card_id = record.get("id").and_then(Value::as_str).map(str::to_owned);
    let oracle_id = record
        .get("oracle_id")
        .and_then(Value::as_str)
        .map(str::to_owned);
    let run = || -> Result<OracleInspection, String> {
        let card: OracleCardInput =
            serde_json::from_value(record).map_err(|error| error.to_string())?;
        if card.layout != "normal" {
            return Err(format!(
                "the current parser adapter handles normal layouts; found {}",
                card.layout
            ));
        }
        if card.id.is_empty() || card.oracle_id.is_empty() || card.name.is_empty() {
            return Err("card identities and name must be nonempty".into());
        }
        let (types, subtypes) = type_context(&card.type_line)?;
        let parsed = parse_oracle_text(
            &card.oracle_text,
            &card.name,
            &card.keywords,
            &types,
            &subtypes,
        );
        Ok(OracleInspection::Parsed {
            card_id: card.id,
            oracle_id: card.oracle_id,
            name: card.name,
            phase_revision: PHASE_REVISION.into(),
            types,
            subtypes,
            parsed: serde_json::to_value(parsed).map_err(|error| error.to_string())?,
        })
    };
    match run() {
        Ok(result) => result,
        Err(detail) => OracleInspection::Inconclusive {
            card_id,
            oracle_id,
            detail,
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preserves_multiword_subtype_using_engine_vocabulary() {
        assert_eq!(
            type_context("Legendary Creature — Time Lord Doctor").unwrap(),
            (
                vec!["Creature".to_owned()],
                vec!["Time Lord".to_owned(), "Doctor".to_owned()]
            )
        );
    }

    #[test]
    fn unknown_type_context_is_explicitly_inconclusive() {
        assert!(type_context("Unrecognized Artifact").is_err());
        assert!(type_context("Creature — NotARealSubtype").is_err());
    }
}
