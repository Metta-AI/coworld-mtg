use super::*;
use phase_bridge::{GameAction, GameEvent, PhaseGame, PhaseRuntime, Zone};
use std::{collections::BTreeMap, time::Instant};

#[derive(Clone, Default)]
struct Progress {
    events: BTreeMap<String, Vec<String>>,
    turns: [u32; 2],
}
impl Progress {
    fn add(&mut self, seat: u8, kind: &str, name: String) {
        self.events
            .entry(format!("{seat}:{kind}"))
            .or_default()
            .push(name);
    }
    fn list(&self, seat: u8, kind: &str) -> Vec<String> {
        self.events
            .get(&format!("{seat}:{kind}"))
            .cloned()
            .unwrap_or_default()
    }
}
fn has_type(game: &PhaseGame, id: &phase_bridge::ObjectId, kind: &str) -> bool {
    game.state().objects.get(id).is_some_and(|o| {
        o.card_types
            .core_types
            .iter()
            .any(|t| t.to_string() == kind)
    })
}
fn observe(game: &PhaseGame, event: &GameEvent, progress: &mut Progress) {
    match event {
        GameEvent::CardDrawn {
            player_id,
            object_id,
            ..
        } => {
            if let Some(o) = game.state().objects.get(object_id) {
                progress.add(player_id.0, "drawn", o.name.clone());
            }
        }
        GameEvent::ZoneChanged {
            object_id,
            from: Some(Zone::Library),
            to: Zone::Hand,
            ..
        } => {
            if let Some(o) = game.state().objects.get(object_id) {
                progress.add(o.owner.0, "drawn_or_tutored_count", o.name.clone());
            }
        }
        GameEvent::LandPlayed {
            object_id,
            player_id,
            ..
        } => {
            if let Some(o) = game.state().objects.get(object_id) {
                progress.add(player_id.0, "land_played", o.name.clone());
            }
        }
        GameEvent::SpellCast {
            object_id,
            controller,
            ..
        } => {
            if let Some(o) = game.state().objects.get(object_id) {
                let kind = if has_type(game, object_id, "Creature") {
                    "creature_cast"
                } else if has_type(game, object_id, "Instant")
                    || has_type(game, object_id, "Sorcery")
                {
                    "instant_sorcery_cast"
                } else {
                    "non_creature_cast"
                };
                progress.add(controller.0, kind, o.name.clone());
            }
        }
        _ => {}
    }
}

fn actual(game: &PhaseGame, progress: &Progress, seat: u8, metric: &str) -> Option<Value> {
    let player = game.state().players.get(seat as usize)?;
    let names = |ids: Vec<phase_bridge::ObjectId>| -> Value {
        let names = ids
            .iter()
            .filter_map(|id| game.state().objects.get(id).map(|o| o.name.clone()))
            .collect::<Vec<_>>();
        serde_json::to_value(names).unwrap()
    };
    Some(match metric {
        "life" => Value::from(player.life),
        "hand_count" => Value::from(player.hand.len()),
        "library_count" => Value::from(player.library.len()),
        "graveyard_count" => Value::from(player.graveyard.len()),
        "hand" => names(player.hand.iter().copied().collect()),
        "lands" | "creatures" | "non_creatures" => names(
            game.state()
                .battlefield
                .iter()
                .copied()
                .filter(|id| {
                    game.state()
                        .objects
                        .get(id)
                        .is_some_and(|o| o.controller.0 == seat)
                        && match metric {
                            "lands" => has_type(game, id, "Land"),
                            "creatures" => has_type(game, id, "Creature"),
                            _ => !has_type(game, id, "Land") && !has_type(game, id, "Creature"),
                        }
                })
                .collect(),
        ),
        "drawn_or_tutored_count" => Value::from(progress.list(seat, metric).len()),
        "drawn"
        | "land_played"
        | "creature_cast"
        | "non_creature_cast"
        | "instant_sorcery_cast" => serde_json::to_value(progress.list(seat, metric)).unwrap(),
        _ => return None,
    })
}
fn equivalent(a: &Value, b: &Value) -> bool {
    if let (Some(a), Some(b)) = (a.as_array(), b.as_array()) {
        let mut a = a.iter().map(Value::to_string).collect::<Vec<_>>();
        let mut b = b.iter().map(Value::to_string).collect::<Vec<_>>();
        a.sort();
        b.sort();
        a == b
    } else {
        a == b
    }
}
fn boundary_matches(
    game: &PhaseGame,
    progress: &Progress,
    input: &FitInput,
    keys: &[MilestoneKey],
) -> bool {
    input
        .fields
        .iter()
        .filter(|f| {
            f.disposition == FieldDisposition::Enforced
                && f.milestone.as_ref().is_some_and(|k| keys.contains(k))
        })
        .all(|field| {
            let key = field.milestone.as_ref().unwrap();
            match (field.projection.as_deref(), &field.expected) {
                (Some(metric), Some(expected)) => {
                    actual(game, progress, key.observed_player, metric)
                        .is_some_and(|a| equivalent(&a, expected))
                }
                _ => false,
            }
        })
}

fn allowed_mulligan(action: &GameAction) -> bool {
    !matches!(action, GameAction::MulliganDecision { choice } if *choice != phase_bridge::MulliganChoice::Keep)
}

fn actions(game: &PhaseGame, progress: &Progress, input: &FitInput) -> Vec<FitAction> {
    let mut result = Vec::new();
    for seat in game.pending_seats() {
        let (mut flat, _, grouped) = game.legal_actions(seat);
        let mut grouped = grouped.into_iter().collect::<Vec<_>>();
        grouped.sort_by_key(|(id, _)| id.0);
        for (_, group) in grouped {
            for action in group {
                if !flat.contains(&action) {
                    flat.push(action);
                }
            }
        }
        for action in flat {
            if allowed_mulligan(&action)
                && serde_json::to_value(&action).unwrap()["type"] != "Concede"
            {
                result.push(FitAction { seat, action });
            }
        }
    }
    let owner = game.state().active_player.0;
    let index = progress.turns[owner as usize];
    let rank = |a: &FitAction| -> u8 {
        let object = match a.action {
            GameAction::PlayLand { object_id, .. } | GameAction::CastSpell { object_id, .. } => {
                game.state().objects.get(&object_id)
            }
            _ => None,
        };
        if let Some(o) = object {
            let wanted = input.fields.iter().any(|f| {
                f.milestone.as_ref().is_some_and(|k| {
                    k.turn_owner == owner && k.turn_index == index && k.observed_player == a.seat
                }) && matches!(
                    f.projection.as_deref(),
                    Some(
                        "land_played"
                            | "creature_cast"
                            | "non_creature_cast"
                            | "instant_sorcery_cast"
                    )
                ) && f
                    .expected
                    .as_ref()
                    .and_then(Value::as_array)
                    .is_some_and(|v| v.iter().any(|n| n.as_str() == Some(&o.name)))
            });
            if wanted {
                return 0;
            }
        }
        if matches!(
            a.action,
            GameAction::PassPriority | GameAction::MulliganDecision { .. }
        ) {
            1
        } else {
            2
        }
    };
    result.sort_by_cached_key(|action| {
        (
            rank(action),
            action.seat,
            serde_json::to_string(&action.action).expect("serializable Phase action"),
        )
    });
    result
}

struct Node {
    game: PhaseGame,
    progress: Progress,
    next: usize,
    trace: Vec<FitAction>,
    choices: Vec<FitAction>,
    cursor: usize,
}
impl Node {
    fn new(
        game: PhaseGame,
        progress: Progress,
        next: usize,
        trace: Vec<FitAction>,
        input: &FitInput,
    ) -> Self {
        let choices = actions(&game, &progress, input);
        Self {
            game,
            progress,
            next,
            trace,
            choices,
            cursor: 0,
        }
    }
}

pub fn search_game(
    runtime: &PhaseRuntime,
    input: &FitInput,
    limits: FitLimits,
) -> Result<FitResult> {
    if limits.nodes == 0 || limits.max_actions == 0 || limits.max_actions > 512 {
        bail!("positive node/action limits required; max-actions cannot exceed 512");
    }
    if input
        .milestones
        .iter()
        .any(|k| k.turn_owner > 1 || k.observed_player > 1 || k.turn_index == 0)
    {
        bail!("invalid milestone seat/index");
    }
    if let Some(on_play) = input.on_play {
        let starter = u8::from(!on_play);
        let order = |k: &MilestoneKey| {
            (
                (u64::from(k.turn_index) - 1) * 2 + u64::from(k.turn_owner != starter),
                k.observed_player,
            )
        };
        if input
            .milestones
            .windows(2)
            .any(|pair| order(&pair[0]) >= order(&pair[1]))
        {
            bail!("milestones must be unique and ordered by known starting player");
        }
    }
    if input.milestones.iter().any(|key| {
        !input.fields.iter().any(|f| {
            f.milestone.as_ref() == Some(key)
                && f.disposition == FieldDisposition::Enforced
                && f.expected.is_some()
        })
    }) {
        bail!("a counted milestone requires at least one enforced observation");
    }
    let start = Instant::now();
    let mut result = FitResult {
        seed: input.seed,
        schema: FIT_SCHEMA.into(), status: FitStatus::InputIssue, nodes: 0, matched_prefix_backtracks: 0, elapsed_millis: 0, milestones_fitted: 0, milestones_total: input.milestones.len(), fully_covered_milestones: 0,
        witness: vec![], issues: input.issues.clone(), limits: limits.clone(), assumptions: input.assumptions.clone(),
        search: "Depth-first exact offered actions with cross-milestone backtracking; node and path-length limits count forced actions too; no completeness claim over hidden setups.".into(),
        manifest_id: String::new(), phase_revision: phase_bridge::PHASE_REVISION.into(), source_sha256: input.source_sha256.clone(), cards_mapping_sha256: input.cards_mapping_sha256.clone(), input_sha256: String::new(),
    };
    if !input.issues.is_empty() {
        result.elapsed_millis = start.elapsed().as_millis();
        return Ok(result);
    }
    if input.mulligans != [Some(0), Some(0)]
        || input.on_play.is_none()
        || input.milestones.is_empty()
    {
        result.issues.push(IssueCandidate {
            kind: IssueKind::UnsupportedInput,
            detail:
                "explicit chronology, zero mulligans, and nonempty selected milestones are required"
                    .into(),
            source_columns: vec![],
            evidence: None,
        });
        result.elapsed_millis = start.elapsed().as_millis();
        return Ok(result);
    }
    for field in input
        .fields
        .iter()
        .filter(|f| f.disposition == FieldDisposition::Unsupported)
    {
        result.issues.push(IssueCandidate {
            kind: IssueKind::UnsupportedProjection,
            detail: field.reason.clone(),
            source_columns: vec![field.column.clone()],
            evidence: None,
        });
    }
    let starter = u8::from(!input.on_play.unwrap());
    let (game, _) = match runtime.new_limited_game_for_fitting(
        input.decks.clone(),
        input.libraries.clone(),
        starter,
        input.seed,
    ) {
        Ok(game) => game,
        Err(error) => {
            result.issues.push(IssueCandidate {
                kind: IssueKind::RuntimeSetup,
                detail: error.to_string(),
                source_columns: vec![],
                evidence: None,
            });
            result.elapsed_millis = start.elapsed().as_millis();
            return Ok(result);
        }
    };
    let mut progress = Progress::default();
    progress.turns[starter as usize] = 1;
    let mut stack = vec![Node::new(game, progress, 0, vec![], input)];
    let mut failure_count = 0;
    let mut truncated = false;
    let mut unsupported_boundary = false;
    while let Some(node) = stack.last_mut() {
        if result.nodes >= limits.nodes {
            truncated = true;
            break;
        }
        if node.trace.len() >= limits.max_actions {
            truncated = true;
            let leaving = node.next;
            stack.pop();
            if stack.last().is_some_and(|parent| parent.next < leaving) {
                result.matched_prefix_backtracks += 1;
            }
            continue;
        }
        if node.cursor == node.choices.len() {
            let leaving = node.next;
            stack.pop();
            if stack.last().is_some_and(|parent| parent.next < leaving) {
                result.matched_prefix_backtracks += 1;
            }
            continue;
        }
        let action = node.choices[node.cursor].clone();
        node.cursor += 1;
        result.nodes += 1;
        let mut candidate = node.game.fork();
        let submission = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            candidate.submit(action.seat, action.action.clone())
        }));
        let events = match submission {
            Ok(Ok(output)) => output.events,
            failure => {
                if failure_count < 16 {
                    failure_count += 1;
                    result.issues.push(IssueCandidate {
                        kind: IssueKind::OfferedActionFailure,
                        detail: match failure {
                            Ok(Err(error)) => error.to_string(),
                            _ => "Phase panicked while submitting an offered action".into(),
                        },
                        source_columns: vec![],
                        evidence: Some(serde_json::json!({"seed": input.seed, "predecessor_actions": node.trace, "failed_action": action})) ,
                    });
                }
                continue;
            }
        };
        if let Err(error) = crate::invariants::validate_invariants(&candidate) {
            if failure_count < 16 {
                failure_count += 1;
                result.issues.push(IssueCandidate { kind: IssueKind::InvariantFailure, detail: error.to_string(), source_columns: vec![], evidence: Some(serde_json::json!({"seed": input.seed, "predecessor_actions": node.trace, "failed_action": action})) });
            }
            continue;
        }
        let mut progress = node.progress.clone();
        let mut next = node.next;
        let mut reject = false;
        if let Some(transition) = events
            .iter()
            .position(|e| matches!(e, GameEvent::TurnStarted { .. }))
        {
            let owner = node.game.state().active_player.0;
            let index = progress.turns[owner as usize];
            let end = input.milestones[next..]
                .iter()
                .take_while(|k| k.turn_owner == owner && k.turn_index == index)
                .count()
                + next;
            let neutral = events
                .iter()
                .filter(|e| matches!(e, GameEvent::TurnStarted { .. }))
                .count()
                == 1
                && events[..transition].iter().all(|event| {
                    matches!(
                        event,
                        GameEvent::PriorityPassed { .. } | GameEvent::PhaseChanged { .. }
                    )
                });
            if !neutral || format!("{:?}", node.game.state().phase) != "End" {
                unsupported_boundary = true;
                reject = true;
            } else {
                for event in &events[..transition] {
                    observe(&candidate, event, &mut progress);
                }
                if end != next
                    && !boundary_matches(&node.game, &progress, input, &input.milestones[next..end])
                {
                    reject = true;
                } else {
                    next = end;
                }
            }
            if !reject {
                progress.events.clear();
                for event in &events[transition..] {
                    if let GameEvent::TurnStarted { player_id, .. } = event {
                        progress.turns[player_id.0 as usize] += 1;
                    } else {
                        observe(&candidate, event, &mut progress);
                    }
                }
            }
        } else {
            for event in &events {
                observe(&candidate, event, &mut progress);
            }
        }
        if reject {
            continue;
        }
        let mut trace = node.trace.clone();
        trace.push(action);
        if next > result.milestones_fitted {
            result.milestones_fitted = next;
            result.witness = trace.clone();
            result.fully_covered_milestones = input.milestones[..next]
                .iter()
                .filter(|key| {
                    !input.fields.iter().any(|f| {
                        f.milestone.as_ref() == Some(*key)
                            && f.disposition == FieldDisposition::Unsupported
                    })
                })
                .count();
        }
        if next == input.milestones.len() {
            result.status = FitStatus::MatchedSupportedProjection;
            break;
        }
        // All earlier matching branches remain on this stack until their alternatives
        // are exhausted. Neither state-only memoization nor first-anchor commitment
        // can discard a different observation history.
        stack.push(Node::new(candidate, progress, next, trace, input));
    }
    if result.status != FitStatus::MatchedSupportedProjection {
        result.status = if truncated {
            FitStatus::BudgetExhausted
        } else if unsupported_boundary {
            FitStatus::UnsupportedBoundary
        } else {
            FitStatus::NoWitnessUnderAssumptions
        };
        result.issues.push(IssueCandidate { kind: if truncated { IssueKind::BudgetExhausted } else if unsupported_boundary { IssueKind::UnsupportedBoundary } else { IssueKind::NoWitnessUnderAssumptions }, detail: "No complete supported-projection witness was found in the recorded bounded search and single reconstructed setup; this does not establish a rules discrepancy or global unreachability.".into(), source_columns: vec![], evidence: None });
    }
    result.elapsed_millis = start.elapsed().as_millis();
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn recorded_zero_mulligans_excludes_other_choices() {
        assert!(!allowed_mulligan(&GameAction::MulliganDecision {
            choice: phase_bridge::MulliganChoice::Mulligan
        }));
        assert!(allowed_mulligan(&GameAction::MulliganDecision {
            choice: phase_bridge::MulliganChoice::Keep
        }));
        assert!(allowed_mulligan(&GameAction::PassPriority));
    }
    #[test]
    fn list_comparison_preserves_multiplicity() {
        assert!(equivalent(
            &serde_json::json!(["Island", "Plains"]),
            &serde_json::json!(["Plains", "Island"])
        ));
        assert!(!equivalent(
            &serde_json::json!(["Island", "Island"]),
            &serde_json::json!(["Island"])
        ));
    }
}

#[cfg(test)]
mod witness_tests {
    use super::*;
    fn runtime() -> PhaseRuntime {
        let land = |name: &str, id: &str| {
            serde_json::json!({
                "name":name,"mana_cost":{"type":"NoCost"},"card_type":{"supertypes":["Basic"],"core_types":["Land"],"subtypes":["Island"]},
                "power":null,"toughness":null,"loyalty":null,"defense":null,"oracle_text":"","non_ability_text":null,"flavor_name":null,
                "keywords":[],"abilities":[],"triggers":[],"static_abilities":[],"replacements":[],"color_override":null,"color_identity":["Blue"],
                "scryfall_oracle_id":id,"legalities":{},"printings":["TST"]
            })
        };
        let mut uncastable = land("Gamma", "00000000-0000-0000-0000-000000000003");
        uncastable["card_type"] =
            serde_json::json!({"supertypes":[],"core_types":["Creature"],"subtypes":[]});
        PhaseRuntime::from_card_data_json(&serde_json::json!({"alpha":land("Alpha","00000000-0000-0000-0000-000000000001"),"beta":land("Beta","00000000-0000-0000-0000-000000000002"),"gamma":uncastable}).to_string()).unwrap()
    }
    fn input() -> FitInput {
        let deck = [
            vec!["Alpha".to_owned()],
            vec!["Beta".to_owned()],
            vec!["Gamma".to_owned(); 5],
            vec!["Alpha".to_owned(); 33],
        ]
        .concat();
        FitInput {
            seed: 0,
            schema: FIT_SCHEMA.into(),
            game_index: 0,
            on_play: Some(true),
            mulligans: [Some(0), Some(0)],
            source_sha256: String::new(),
            cards_mapping_sha256: String::new(),
            fields: vec![],
            milestones: vec![],
            decks: [deck.clone(), deck.clone()],
            libraries: [deck.clone(), deck],
            assumptions: vec!["synthetic production-action compatibility test only".into()],
            issues: vec![],
        }
    }
    fn field(key: MilestoneKey, metric: &str, expected: Value) -> SourceField {
        SourceField {
            column: format!("test_{key:?}_{metric}"),
            raw: expected.to_string(),
            milestone: Some(key),
            disposition: FieldDisposition::Enforced,
            reason: "projected from a recorded production Phase transition in this test".into(),
            projection: Some(metric.into()),
            expected: Some(expected),
        }
    }
    #[test]
    fn known_compatible_trace_requires_backtracking_across_first_match() {
        let runtime = runtime();
        let mut input = input();
        let (mut game, _) = runtime
            .new_limited_game_for_fitting(input.decks.clone(), input.libraries.clone(), 0, 0)
            .unwrap();
        let mut progress = Progress::default();
        progress.turns[0] = 1;
        let mut played = false;
        let mut opponent_played = false;
        let mut boundaries = 0;
        for _ in 0..100 {
            let choices = actions(&game, &progress, &input);
            let desired = choices.iter().find(|a| {
                ((!played && a.seat == 0) || (!opponent_played && a.seat == 1))
                    && match a.action {
                        GameAction::PlayLand { object_id, .. } => {
                            game.state().objects[&object_id].name
                                == if a.seat == 0 { "Beta" } else { "Alpha" }
                        }
                        _ => false,
                    }
            });
            let choice = desired
                .or_else(|| {
                    choices.iter().find(|a| {
                        matches!(
                            a.action,
                            GameAction::PassPriority | GameAction::MulliganDecision { .. }
                        )
                    })
                })
                .or(choices.first())
                .unwrap()
                .clone();
            if matches!(choice.action, GameAction::PlayLand { .. }) {
                if choice.seat == 0 {
                    played = true;
                } else {
                    opponent_played = true;
                }
            }
            let before = game.fork();
            let events = game.submit(choice.seat, choice.action).unwrap().events;
            if events
                .iter()
                .any(|e| matches!(e, GameEvent::TurnStarted { .. }))
            {
                let key = MilestoneKey {
                    turn_owner: before.state().active_player.0,
                    turn_index: 1,
                    boundary: Boundary::EndOfTurn,
                    observed_player: 0,
                };
                let metric = if boundaries == 0 {
                    "hand_count"
                } else {
                    "hand"
                };
                input.fields.push(field(
                    key.clone(),
                    metric,
                    actual(&before, &progress, 0, metric).unwrap(),
                ));
                input.milestones.push(key);
                if boundaries == 1 {
                    let opponent = MilestoneKey {
                        turn_owner: 1,
                        turn_index: 1,
                        boundary: Boundary::EndOfTurn,
                        observed_player: 1,
                    };
                    input.fields.push(field(
                        opponent.clone(),
                        "lands",
                        actual(&before, &progress, 1, "lands").unwrap(),
                    ));
                    input.milestones.push(opponent);
                }
                boundaries += 1;
                if boundaries == 2 {
                    break;
                }
                progress.turns[1] = 1;
            }
        }
        assert_eq!(boundaries, 2);
        assert!(played);
        let result = search_game(
            &runtime,
            &input,
            FitLimits {
                nodes: 3000,
                max_actions: 100,
            },
        )
        .unwrap();
        assert_eq!(
            result.status,
            FitStatus::MatchedSupportedProjection,
            "{result:#?}"
        );
        assert_eq!(result.milestones_fitted, 3);
        assert!(result.matched_prefix_backtracks > 0, "must abandon an earlier matching prefix, not just luckily pick the final witness first");
        assert!(
            result.nodes > result.witness.len() as u64,
            "first matching prefix must be revisited"
        );
        assert!(result
            .witness
            .iter()
            .any(|a| matches!(a.action, GameAction::PlayLand { .. })));
        assert!(result.witness.iter().all(|a| allowed_mulligan(&a.action)));
        // Replaying exact returned actions independently must satisfy the later named-hand field.
        let (mut replay, _) = runtime
            .new_limited_game_for_fitting(input.decks.clone(), input.libraries.clone(), 0, 0)
            .unwrap();
        let mut last_before = None;
        for a in result.witness {
            let before = replay.fork();
            let out = replay.submit(a.seat, a.action).unwrap();
            if out
                .events
                .iter()
                .any(|e| matches!(e, GameEvent::TurnStarted { .. }))
            {
                last_before = Some(before);
            }
        }
        assert!(equivalent(
            &actual(&last_before.unwrap(), &Progress::default(), 0, "hand").unwrap(),
            input.fields[1].expected.as_ref().unwrap()
        ));
    }
    #[test]
    fn search_limits_and_wrong_mulligans_fail_before_search() {
        let runtime = runtime();
        let mut input = input();
        assert!(search_game(
            &runtime,
            &input,
            FitLimits {
                nodes: 0,
                max_actions: 10
            }
        )
        .is_err());
        assert!(search_game(
            &runtime,
            &input,
            FitLimits {
                nodes: 1,
                max_actions: 513
            }
        )
        .is_err());
        input.mulligans[1] = None;
        let result = search_game(&runtime, &input, FitLimits::default()).unwrap();
        assert_eq!(result.status, FitStatus::InputIssue);
        assert_eq!(result.nodes, 0);
    }
}
