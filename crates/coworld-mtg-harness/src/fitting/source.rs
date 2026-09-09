use super::*;
use anyhow::{anyhow, bail};
use std::collections::{BTreeMap, BTreeSet};

fn integer(raw: &str) -> Option<u32> {
    let n = raw.parse::<f64>().ok()?;
    (n.is_finite() && n >= 0.0 && n <= u32::MAX as f64 && n.fract() == 0.0).then_some(n as u32)
}
fn issue(issues: &mut Vec<IssueCandidate>, kind: IssueKind, column: &str, detail: String) {
    issues.push(IssueCandidate {
        kind,
        detail,
        source_columns: vec![column.into()],
        evidence: None,
    });
}

/// Official mapping permits repeated identical IDs/names, but conflicting names remain ambiguous.
fn mapping(bytes: &[u8]) -> Result<BTreeMap<u32, BTreeSet<String>>> {
    let mut csv = csv::Reader::from_reader(bytes);
    let headers = csv.headers()?.clone();
    if headers.iter().collect::<BTreeSet<_>>().len() != headers.len() {
        bail!("duplicate cards.csv headers");
    }
    let id = headers
        .iter()
        .position(|s| s == "id")
        .ok_or_else(|| anyhow!("cards.csv lacks id"))?;
    let name = headers
        .iter()
        .position(|s| s == "name")
        .ok_or_else(|| anyhow!("cards.csv lacks name"))?;
    let card_types = headers.iter().position(|s| s == "types");
    let mut map = BTreeMap::<u32, BTreeSet<String>>::new();
    for row in csv.records() {
        let row = row?;
        let raw = &row[id];
        let id = raw
            .parse::<u32>()
            .ok()
            .filter(|n| *n > 0 && raw.bytes().all(|b| b.is_ascii_digit()))
            .ok_or_else(|| anyhow!("invalid official mapping ID {raw:?}"))?;
        if row[name].is_empty() {
            bail!("empty official name for ID {id}");
        }
        if card_types.is_some_and(|index| row[index].split_whitespace().any(|part| part == "Token"))
        {
            // Only explicit Token markers are detected here. Official rows can omit
            // that marker; this is not a complete token/face identity check. The
            // emitted assumptions therefore limit all matching to a name projection.
            map.entry(id).or_default();
        } else {
            map.entry(id).or_default().insert(row[name].to_owned());
        }
    }
    Ok(map)
}

fn names(
    raw: &str,
    column: &str,
    map: &BTreeMap<u32, BTreeSet<String>>,
    issues: &mut Vec<IssueCandidate>,
) -> Option<Vec<String>> {
    if raw.is_empty() {
        return None;
    }
    let mut result = Vec::new();
    let mut valid = true;
    for token in raw.split('|') {
        let id = token
            .parse::<u32>()
            .ok()
            .filter(|n| *n > 0 && token.bytes().all(|b| b.is_ascii_digit()));
        match id.and_then(|id| map.get(&id)) {
            Some(options) if options.len() == 1 => result.push(options.first().unwrap().clone()),
            Some(options) => {
                valid = false;
                issue(
                    issues,
                    IssueKind::InputMapping,
                    column,
                    format!("Arena ID {token:?} has ambiguous official names {options:?}"),
                );
            }
            None => {
                valid = false;
                issue(issues, IssueKind::InputMapping, column, format!("Arena ID token {token:?} is invalid or absent from the pinned official mapping"));
            }
        }
    }
    valid.then_some(result)
}

fn turn_column(column: &str) -> Option<(u8, u32, &str)> {
    let (owner, rest) = column
        .strip_prefix("user_turn_")
        .map(|s| (0, s))
        .or_else(|| column.strip_prefix("oppo_turn_").map(|s| (1, s)))?;
    let (index, suffix) = rest.split_once('_')?;
    Some((owner, index.parse().ok()?, suffix))
}

fn projection(owner: u8, suffix: &str) -> Option<(u8, &'static str, bool)> {
    let (seat, rest) = if let Some(rest) = suffix.strip_prefix("eot_user_") {
        (0, rest)
    } else if let Some(rest) = suffix.strip_prefix("eot_oppo_") {
        (1, rest)
    } else {
        return match suffix {
            "cards_drawn" => Some((owner, "drawn", true)),
            "cards_drawn_or_tutored" => Some((owner, "drawn_or_tutored_count", false)),
            "lands_played" => Some((owner, "land_played", true)),
            "creatures_cast" => Some((owner, "creature_cast", true)),
            // Official helper gives the type but not whether this family excludes instants/sorceries.
            "non_creatures_cast" => None,
            "user_instants_sorceries_cast" => Some((0, "instant_sorcery_cast", true)),
            "oppo_instants_sorceries_cast" => Some((1, "instant_sorcery_cast", true)),
            _ => None,
        };
    };
    match rest {
        "cards_in_hand" if seat == 0 => Some((seat, "hand", true)),
        "cards_in_hand" => Some((seat, "hand_count", false)),
        "lands_in_play" => Some((seat, "lands", true)),
        "creatures_in_play" => Some((seat, "creatures", true)),
        "non_creatures_in_play" => Some((seat, "non_creatures", true)),
        "life" => Some((seat, "life", false)),
        "library_count" => Some((seat, "library_count", false)),
        "graveyard_count" => Some((seat, "graveyard_count", false)),
        _ => None,
    }
}

pub fn extract_game(
    csv_bytes: &[u8],
    mapping_bytes: &[u8],
    game_index: u64,
    turn_pairs: u32,
    opponent_filler: &str,
) -> Result<FitInput> {
    let map = mapping(mapping_bytes)?;
    let mut csv = csv::Reader::from_reader(csv_bytes);
    let headers = csv.headers()?.clone();
    if headers.iter().collect::<BTreeSet<_>>().len() != headers.len() {
        bail!("duplicate replay headers");
    }
    let mut selected = None;
    for (index, row) in csv.records().enumerate() {
        let row = row?;
        if index == usize::try_from(game_index)? {
            selected = Some(row);
            break;
        }
    }
    let row = selected.ok_or_else(|| anyhow!("game index {game_index} absent"))?;
    let cells = headers.iter().zip(row.iter()).collect::<BTreeMap<_, _>>();
    let mut issues = Vec::new();
    let on_play = match cells.get("on_play").copied() {
        Some("True" | "true") => Some(true),
        Some("False" | "false") => Some(false),
        _ => None,
    };
    if on_play.is_none() {
        issue(
            &mut issues,
            IssueKind::UnsupportedInput,
            "on_play",
            "starting-player chronology is unknown".into(),
        );
    }
    let mulligans = [
        cells.get("num_mulligans").and_then(|s| integer(s)),
        cells.get("opp_num_mulligans").and_then(|s| integer(s)),
    ];
    if mulligans != [Some(0), Some(0)] {
        issue(
            &mut issues,
            IssueKind::UnsupportedInput,
            "num_mulligans/opp_num_mulligans",
            "first supported slice requires both recorded mulligan counts to be explicitly zero"
                .into(),
        );
    }
    let mut fields = Vec::new();
    let mut decks: [Vec<String>; 2] = Default::default();
    for (column, raw) in &cells {
        if let Some(name) = column.strip_prefix("deck_") {
            match integer(raw) {
                Some(n) if n <= 250 => {
                    decks[0].extend(std::iter::repeat_n(name.to_owned(), n as usize))
                }
                _ => issue(
                    &mut issues,
                    IssueKind::UnsupportedInput,
                    column,
                    "missing, invalid, or excessive deck count".into(),
                ),
            }
        }
    }
    if !(40..=250).contains(&decks[0].len()) {
        issue(
            &mut issues,
            IssueKind::UnsupportedInput,
            "deck_*",
            "recorded user deck must have 40 to 250 cards for this bounded Limited slice".into(),
        );
    }
    let opening = names(
        cells.get("opening_hand").copied().unwrap_or(""),
        "opening_hand",
        &map,
        &mut issues,
    )
    .unwrap_or_default();
    if opening.len() != 7 {
        issue(
            &mut issues,
            IssueKind::UnsupportedInput,
            "opening_hand",
            "zero-mulligan setup requires seven mapped opening cards".into(),
        );
    }
    let mut turns = BTreeSet::new();
    for (column, raw) in &cells {
        let parsed = turn_column(column);
        let selected = parsed.is_some_and(|(_, n, _)| n > 0 && n <= turn_pairs);
        let mut field = SourceField {
            column: (*column).into(),
            raw: (*raw).into(),
            milestone: None,
            disposition: FieldDisposition::Informational,
            reason: "not a selected trajectory constraint".into(),
            projection: None,
            expected: None,
        };
        if let Some((owner, index, suffix)) = parsed.filter(|_| selected) {
            turns.insert((owner, index));
            let inferred_seat = if suffix.contains("oppo_") {
                1
            } else if suffix.contains("user_") {
                0
            } else {
                owner
            };
            field.milestone = Some(MilestoneKey {
                turn_owner: owner,
                turn_index: index,
                boundary: Boundary::EndOfTurn,
                observed_player: inferred_seat,
            });
            if raw.is_empty() {
                field.reason =
                    "blank cell retained as unknown; no zero/empty constraint inferred".into();
            } else if let Some((seat, metric, is_names)) = projection(owner, suffix) {
                field.milestone.as_mut().unwrap().observed_player = seat;
                field.projection = Some(metric.into());
                field.expected = if is_names {
                    names(raw, column, &map, &mut issues).map(|n| serde_json::to_value(n).unwrap())
                } else if metric == "life" {
                    raw.parse::<f64>()
                        .ok()
                        .filter(|n| {
                            n.is_finite()
                                && n.fract() == 0.0
                                && *n >= i32::MIN as f64
                                && *n <= i32::MAX as f64
                        })
                        .map(|n| Value::from(n as i32))
                } else {
                    integer(raw).map(Value::from)
                };
                if field.expected.is_some() {
                    field.disposition = FieldDisposition::Enforced;
                    field.reason = "exact declared projection; card lists compared as multisets, not action order".into();
                } else {
                    field.disposition = FieldDisposition::Unsupported;
                    field.reason =
                        "unresolved identity or unsupported scalar representation".into();
                }
            } else {
                field.disposition = FieldDisposition::Unsupported;
                field.reason = "no implemented projection for this recorded field; ability IDs are not card IDs".into();
            }
        } else if *column == "opening_hand" {
            field.disposition = if opening.len() == 7 {
                FieldDisposition::Enforced
            } else {
                FieldDisposition::Unsupported
            };
            field.projection = Some("opening_hand_multiset".into());
            field.expected = (opening.len() == 7).then(|| serde_json::to_value(&opening).unwrap());
            field.reason =
                "supplied through production opening draw, exact multiset checked".into();
        } else if matches!(*column, "on_play" | "num_mulligans" | "opp_num_mulligans") {
            field.disposition = if (*column == "on_play" && on_play.is_some())
                || (*column != "on_play" && integer(raw) == Some(0))
            {
                FieldDisposition::Enforced
            } else {
                FieldDisposition::Unsupported
            };
            field.reason =
                "requires known starter and recorded zero mulligans; otherwise unsupported".into();
        } else if column.starts_with("deck_") {
            field.disposition = if integer(raw).is_some_and(|n| n <= 250) {
                FieldDisposition::Enforced
            } else {
                FieldDisposition::Unsupported
            };
            field.reason = "recorded user deck multiset".into();
        }
        fields.push(field);
    }
    let starter = u8::from(on_play == Some(false));
    let order = |owner: u8, index: u32| (index - 1) * 2 + u32::from(owner != starter);
    let mut milestones = fields
        .iter()
        .filter(|f| f.disposition == FieldDisposition::Enforced && f.expected.is_some())
        .filter_map(|f| f.milestone.clone())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();
    milestones.sort_by_key(|k| (order(k.turn_owner, k.turn_index), k.observed_player));
    if turns.is_empty() {
        issue(
            &mut issues,
            IssueKind::UnsupportedInput,
            "turn fields",
            "no selected owner-specific turn columns".into(),
        );
    }
    // Build one explicit hidden-state hypothesis. Counts use the maximum known simultaneous
    // multiplicity, not a sum of repeated snapshots. This is not recovery of the real deck.
    let mut opponent_minimum = BTreeMap::<String, usize>::new();
    for field in &fields {
        if field
            .milestone
            .as_ref()
            .is_some_and(|k| k.observed_player == 1)
        {
            if let Some(Value::Array(values)) = &field.expected {
                let names = values
                    .iter()
                    .filter_map(Value::as_str)
                    .map(str::to_owned)
                    .collect::<Vec<_>>();
                for (name, n) in counts(&names) {
                    opponent_minimum
                        .entry(name)
                        .and_modify(|m| *m = (*m).max(n))
                        .or_insert(n);
                }
            }
        }
    }
    for (name, n) in opponent_minimum {
        decks[1].extend(std::iter::repeat_n(name, n));
    }
    if decks[1].len() > 40 {
        issue(
            &mut issues,
            IssueKind::UnsupportedInput,
            "opponent setup",
            "observed minimum exceeds chosen forty-card setup".into(),
        );
    }
    decks[1].resize(decks[1].len().max(40), opponent_filler.into());
    let mut user_prefix = opening;
    for milestone in &milestones {
        for f in &fields {
            if f.milestone.as_ref() == Some(milestone)
                && f.projection.as_deref() == Some("drawn")
                && milestone.observed_player == 0
            {
                if let Some(Value::Array(v)) = &f.expected {
                    user_prefix.extend(v.iter().filter_map(Value::as_str).map(str::to_owned));
                }
            }
        }
    }
    let mut remaining = decks[0].clone();
    let mut library = Vec::new();
    for name in user_prefix {
        if let Some(index) = remaining.iter().position(|n| *n == name) {
            library.push(remaining.remove(index));
        } else {
            issue(&mut issues, IssueKind::ProjectionContradiction, "opening_hand/cards_drawn/deck_*", format!("requested initial/draw card {name:?} exceeds recorded deck multiset under the no-shuffle prefix hypothesis"));
        }
    }
    library.extend(remaining);
    let libraries = [library, decks[1].clone()];
    Ok(FitInput {
        seed: game_index,
        schema: FIT_SCHEMA.into(), game_index, on_play, mulligans, source_sha256: crate::io::sha256(csv_bytes), cards_mapping_sha256: crate::io::sha256(mapping_bytes), fields, milestones, decks, libraries, issues,
        assumptions: vec![
            "Official Arena IDs resolve to names in a pinned mapping; runtime matching is a name projection, not proof of unique token/face characteristics. One reconstructed hidden state: recorded user deck/opening multiset, chosen opening order and listed draw-prefix order, deterministic remaining library; no search over all shuffles.".into(),
            format!("Hypothetical opponent: maximum observed name multiplicities plus {opponent_filler} to forty cards, in deterministic order; neither opponent deck nor opening hand is source-confirmed."),
            "EOT fields project the last stable end-step state before a projection-neutral cleanup/turn transition; transitions with other pre-TurnStarted events are unsupported.".into(),
            "Runtime preflight checks names and setup only; it does not inventory every unsupported or unimplemented card effect. Blank cells are unknown. Nonblank card lists are multiset constraints; no global action order, targets, priority decisions, or hidden information is reconstructed as fact.".into(),
        ],
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    fn mapping_bytes() -> &'static [u8] {
        b"id,name\n1,Island\n2,Plains\n"
    }
    fn sample(extra: &str, value: &str, on_play: &str, mulligan: &str) -> Vec<u8> {
        format!("on_play,num_mulligans,opp_num_mulligans,opening_hand,deck_Island,user_turn_1_eot_oppo_cards_in_hand,oppo_turn_1_eot_oppo_cards_in_hand,{extra}\n{on_play},{mulligan},0,1|1|1|1|1|1|1,40,7.0,6.0,{value}\n").into_bytes()
    }
    #[test]
    fn distinct_owner_boundaries_keep_seven_and_six() {
        let input = extract_game(
            &sample("user_turn_1_user_abilities", "88024", "True", "0"),
            mapping_bytes(),
            0,
            1,
            "Plains",
        )
        .unwrap();
        let hand = input
            .fields
            .iter()
            .filter(|f| f.projection.as_deref() == Some("hand_count"))
            .collect::<Vec<_>>();
        assert_eq!(hand.len(), 2);
        assert_ne!(hand[0].milestone, hand[1].milestone);
        assert_eq!(input.milestones[0].turn_owner, 0);
        assert!(input
            .fields
            .iter()
            .any(|f| f.raw == "88024" && f.disposition == FieldDisposition::Unsupported));
        assert!(!input
            .issues
            .iter()
            .any(|i| i.kind == IssueKind::InputMapping));
        let reversed = extract_game(
            &sample("user_turn_1_cards_drawn", "", "False", "0"),
            mapping_bytes(),
            0,
            1,
            "Plains",
        )
        .unwrap();
        assert_eq!(reversed.milestones[0].turn_owner, 1);
    }
    #[test]
    fn retained_source_slice_preserves_actual_chronology_and_constraints() {
        let csv = include_bytes!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../fixtures/17lands/sos-first-turns/source/sos-first-turns-2-3-11.csv"
        ));
        let map = include_bytes!(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../fixtures/17lands/sos-first-turns/source/cards-selected.csv"
        ));
        assert_eq!(
            crate::io::sha256(csv),
            "dc93a2677e59b4b2b19900ff1ddafefb72533dce1be678b3493263709dec1215"
        );
        for (row, starter) in [(0, 0), (1, 1), (2, 0)] {
            let input = extract_game(csv, map, row, 1, "Plains").unwrap();
            assert!(input.issues.is_empty(), "{:#?}", input.issues);
            assert_eq!(input.decks[0].len(), 40);
            assert_eq!(input.mulligans, [Some(0), Some(0)]);
            assert_eq!(input.milestones[0].turn_owner, starter);
            assert_eq!(input.milestones.len(), 4);
            if row == 2 {
                for (column, owner, count) in [
                    ("user_turn_1_eot_oppo_cards_in_hand", 0, 7),
                    ("oppo_turn_1_eot_oppo_cards_in_hand", 1, 6),
                ] {
                    let field = input.fields.iter().find(|f| f.column == column).unwrap();
                    assert_eq!(field.expected, Some(Value::from(count)));
                    assert_eq!(field.milestone.as_ref().unwrap().turn_owner, owner);
                }
                let ability = input
                    .fields
                    .iter()
                    .find(|f| f.column == "oppo_turn_1_user_abilities")
                    .unwrap();
                assert_eq!(ability.disposition, FieldDisposition::Unsupported);
                assert_eq!(ability.raw, "88024");
            }
        }
    }

    #[test]
    fn unknown_and_positive_mulligans_are_not_zero() {
        for count in ["", "1", "-1", "NaN"] {
            let input = extract_game(
                &sample("user_turn_1_cards_drawn", "", "True", count),
                mapping_bytes(),
                0,
                1,
                "Plains",
            )
            .unwrap();
            assert!(input
                .issues
                .iter()
                .any(|i| i.detail.contains("explicitly zero")));
        }
    }
    #[test]
    fn ambiguous_mapping_and_blanks_remain_visible() {
        let bytes = sample("user_turn_1_cards_drawn", "999", "True", "0");
        let input = extract_game(&bytes, b"id,name\n1,Island\n1,Plains\n", 0, 1, "Plains").unwrap();
        assert!(input.issues.iter().any(|i| i.detail.contains("ambiguous")));
        assert!(input.issues.iter().any(|i| i.detail.contains("999")));
        let blank = extract_game(
            &sample("user_turn_1_cards_drawn", "", "True", "0"),
            mapping_bytes(),
            0,
            1,
            "Plains",
        )
        .unwrap();
        let field = blank
            .fields
            .iter()
            .find(|f| f.column == "user_turn_1_cards_drawn")
            .unwrap();
        assert_eq!(field.disposition, FieldDisposition::Informational);
        assert!(field.expected.is_none());
    }
}
