use super::trace::{materialize, project_state, RecordedStep};
use super::*;
use phase_bridge::{GameAction, GameEvent, PhaseGame, PhaseRuntime, Zone};
use std::{collections::BTreeMap, sync::Arc, time::Instant};

#[derive(Clone, Default)]
struct Progress {
    events: BTreeMap<String, Vec<String>>,
    turns: [u32; 2],
    combat_damage: [u64; 2],
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
    if let Some((seat, amount)) = phase_bridge::combat_damage_to_player(event) {
        if let Some(total) = progress.combat_damage.get_mut(usize::from(seat)) {
            *total += u64::from(amount);
        }
    }
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
fn compare_field(
    game: Option<&PhaseGame>,
    progress: Option<&Progress>,
    key: &MilestoneKey,
    field: &SourceField,
) -> TraceField {
    let actual_value = if field.disposition == FieldDisposition::Enforced {
        game.zip(progress).and_then(|(g, p)| {
            field
                .projection
                .as_deref()
                .and_then(|metric| actual(g, p, key.observed_player, metric))
        })
    } else {
        None
    };
    let comparison = match field.disposition {
        FieldDisposition::Informational => FieldComparison::Unknown,
        FieldDisposition::Unsupported => FieldComparison::Unsupported,
        FieldDisposition::Enforced if game.is_none() => FieldComparison::NotReached,
        FieldDisposition::Enforced => match (&field.expected, &actual_value) {
            (Some(e), Some(a)) if equivalent(e, a) => FieldComparison::Matched,
            (Some(_), Some(_)) => FieldComparison::Mismatched,
            _ => FieldComparison::ProjectionUnavailable,
        },
    };
    let diagnostic = if field.disposition == FieldDisposition::Unsupported
        && (field.column.ends_with("_user_combat_damage_taken")
            || field.column.ends_with("_oppo_combat_damage_taken"))
    {
        game.zip(progress).map(|(_,p)| TraceDiagnostic {
            metric: TraceDiagnosticMetric::NativeCombatDamageReceived,
            value: Value::from(p.combat_damage[usize::from(key.observed_player)]),
            limitation: "Sum of actual native combat DamageDealt events to this player during the complete turn interval. Source combat_damage_taken aggregation is unverified and includes negative recorded values; this diagnostic is not compared to the source and does not increase supported coverage.".into(),
        })
    } else {
        None
    };
    TraceField {
        source_field_id: field.column.clone(),
        raw: field.raw.clone(),
        disposition: field.disposition.clone(),
        reason: field.reason.clone(),
        projection: field.projection.clone(),
        expected: field.expected.clone(),
        actual: actual_value,
        comparison,
        diagnostic,
    }
}

fn comparisons(
    game: Option<&PhaseGame>,
    progress: Option<&Progress>,
    input: &FitInput,
    keys: &[MilestoneKey],
    transition_index: Option<usize>,
) -> Vec<TraceMilestone> {
    keys.iter()
        .map(|key| TraceMilestone {
            key: key.clone(),
            transition_index,
            state_position: transition_index.map(|_| TraceStatePosition::BeforeTransition),
            fields: input
                .fields
                .iter()
                .filter(|f| f.milestone.as_ref() == Some(key))
                .map(|field| compare_field(game, progress, key, field))
                .collect(),
        })
        .collect()
}

fn all_trace_keys(input: &FitInput) -> Vec<MilestoneKey> {
    let mut keys = input
        .fields
        .iter()
        .filter_map(|f| f.milestone.clone())
        .collect::<Vec<_>>();
    let starter = u8::from(input.on_play == Some(false));
    keys.sort_by_key(|k| (k.turn_index, k.turn_owner != starter, k.observed_player));
    keys.dedup();
    keys
}

fn matching(comparisons: &[TraceMilestone]) -> bool {
    comparisons.iter().all(|m| {
        m.fields
            .iter()
            .filter(|f| f.disposition == FieldDisposition::Enforced)
            .all(|f| f.comparison == FieldComparison::Matched)
    })
}

fn retain_failure(
    slot: &mut Option<(usize, TraceFailure)>,
    prefix: usize,
    kind: &TraceFailureKind,
    make: impl FnOnce() -> TraceFailure,
) {
    // Keep the first failure at the furthest matched prefix; never claim it explains
    // every explored branch. This bounds retained failure evidence independently of nodes.
    let priority = |kind: &TraceFailureKind| match kind {
        TraceFailureKind::OfferedActionFailure | TraceFailureKind::InvariantFailure => 3,
        TraceFailureKind::UnsupportedBoundary => 1,
        TraceFailureKind::MilestoneMismatch => 2,
        _ => 0,
    };
    if slot
        .as_ref()
        .is_none_or(|(p, f)| prefix > *p || (prefix == *p && priority(kind) > priority(&f.kind)))
    {
        *slot = Some((prefix, make()));
    }
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
    path: Option<Arc<RecordedStep>>,
    choices: Vec<FitAction>,
    cursor: usize,
}
impl Node {
    fn new(
        game: PhaseGame,
        progress: Progress,
        next: usize,
        trace: Vec<FitAction>,
        path: Option<Arc<RecordedStep>>,
        input: &FitInput,
    ) -> Self {
        let choices = actions(&game, &progress, input);
        Self {
            game,
            progress,
            next,
            trace,
            path,
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
        witness: vec![], trace: Some(FitTrace {schema:"coworld-17lands-fit-trace-v1".into(),path_kind:TracePathKind::NoExecution,initial_state:None,transitions:vec![],milestones:comparisons(None,None,input,&all_trace_keys(input),None),failure:None}), issues: input.issues.clone(), limits: limits.clone(), assumptions: input.assumptions.clone(),
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
        let diagnostic_code = if field.column.ends_with("combat_damage_taken") {
            "combat_source_aggregation_unverified"
        } else if field.column.ends_with("mana_spent") {
            "mana_payment_observation_incomplete"
        } else if field.column.ends_with("abilities") {
            "ability_identity_unbound"
        } else {
            "unsupported_source_projection"
        };
        result.issues.push(IssueCandidate {
            kind: IssueKind::UnsupportedProjection,
            // Existing factory issue identity includes detail. Keep this legacy
            // signature stable; the precise explanation belongs in evidence.
            detail: if field.projection.is_none() {
                "no implemented projection for this recorded field; ability IDs are not card IDs"
                    .into()
            } else {
                field.reason.clone()
            },
            source_columns: vec![field.column.clone()],
            evidence: Some(
                serde_json::json!({"diagnostic_code":diagnostic_code,"reason":field.reason}),
            ),
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
    result.trace.as_mut().unwrap().initial_state = Some(project_state(&game));
    result.trace.as_mut().unwrap().path_kind = TracePathKind::LongestPrefix;
    let mut best_path = None;
    let mut retained_failure = None;
    // A terminal boundary refusal needs its own context even when a different
    // branch at the same prefix has a useful mismatch comparison.
    let mut retained_boundary = None;
    let mut stack = vec![Node::new(game, progress, 0, vec![], None, input)];
    let mut failure_count = 0;
    let mut truncated = false;
    let mut unsupported_boundary = false;
    while let Some(node) = stack.last_mut() {
        if result.nodes >= limits.nodes {
            truncated = true;
            retain_failure(
                &mut retained_failure,
                node.next,
                &TraceFailureKind::NodeBudget,
                || {
                    TraceFailure {path_kind:FailurePathKind::SeparateSearchBranch,kind:TraceFailureKind::NodeBudget,detail:"Search stopped at its node budget. This is an unvisited frontier, not a mismatching observation.".into(),actions_before:node.trace.clone(),attempted_action:None,attempt:None,state:project_state(&node.game),milestones:vec![]}
                },
            );
            break;
        }
        if node.trace.len() >= limits.max_actions {
            truncated = true;
            retain_failure(
                &mut retained_failure,
                node.next,
                &TraceFailureKind::ActionBudget,
                || TraceFailure {
                    path_kind: FailurePathKind::SeparateSearchBranch,
                    kind: TraceFailureKind::ActionBudget,
                    detail: "This branch reached the action limit before a complete witness."
                        .into(),
                    actions_before: node.trace.clone(),
                    attempted_action: None,
                    attempt: None,
                    state: project_state(&node.game),
                    milestones: vec![],
                },
            );
            let leaving = node.next;
            stack.pop();
            if stack.last().is_some_and(|parent| parent.next < leaving) {
                result.matched_prefix_backtracks += 1;
            }
            continue;
        }
        if node.cursor == node.choices.len() {
            if node.choices.is_empty() {
                retain_failure(
                    &mut retained_failure,
                    node.next,
                    &TraceFailureKind::NoAvailableAction,
                    || TraceFailure {
                        path_kind: FailurePathKind::SeparateSearchBranch,
                        kind: TraceFailureKind::NoAvailableAction,
                        detail: "No remaining offered action in this retained state.".into(),
                        actions_before: node.trace.clone(),
                        attempted_action: None,
                        attempt: None,
                        state: project_state(&node.game),
                        milestones: vec![],
                    },
                );
            }
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
                let detail = match failure {
                    Ok(Err(error)) => error.to_string(),
                    _ => "Phase panicked while submitting an offered action".into(),
                };
                retain_failure(
                    &mut retained_failure,
                    node.next,
                    &TraceFailureKind::OfferedActionFailure,
                    || TraceFailure {
                        path_kind: FailurePathKind::SeparateSearchBranch,
                        kind: TraceFailureKind::OfferedActionFailure,
                        detail: detail.clone(),
                        actions_before: node.trace.clone(),
                        attempted_action: Some(action.clone()),
                        attempt: None,
                        state: project_state(&node.game),
                        milestones: vec![],
                    },
                );
                if failure_count < 16 {
                    failure_count += 1;
                    result.issues.push(IssueCandidate {
                        kind: IssueKind::OfferedActionFailure,
                        detail,
                        source_columns: vec![],
                        evidence: Some(serde_json::json!({"seed": input.seed, "predecessor_actions": node.trace, "failed_action": action})) ,
                    });
                }
                continue;
            }
        };
        if let Err(error) = crate::invariants::validate_invariants(&candidate) {
            retain_failure(
                &mut retained_failure,
                node.next,
                &TraceFailureKind::InvariantFailure,
                || TraceFailure {
                    path_kind: FailurePathKind::SeparateSearchBranch,
                    kind: TraceFailureKind::InvariantFailure,
                    detail: error.to_string(),
                    actions_before: node.trace.clone(),
                    attempted_action: Some(action.clone()),
                    attempt: Some(TraceTransition {
                        index: node.trace.len(),
                        seat: action.seat,
                        action: action.action.clone(),
                        before: project_state(&node.game),
                        after: project_state(&candidate),
                        events: events.clone(),
                    }),
                    state: project_state(&node.game),
                    milestones: vec![],
                },
            );
            if failure_count < 16 {
                failure_count += 1;
                result.issues.push(IssueCandidate { kind: IssueKind::InvariantFailure, detail: error.to_string(), source_columns: vec![], evidence: Some(serde_json::json!({"seed": input.seed, "predecessor_actions": node.trace, "failed_action": action})) });
            }
            continue;
        }
        let mut progress = node.progress.clone();
        let mut next = node.next;
        let mut reject = false;
        let mut milestone_receipts = vec![];
        let mut rejection_kind = TraceFailureKind::MilestoneMismatch;
        let mut rejection_detail="One rejected branch from the bounded search; these comparisons do not establish incompatibility of other hidden setups or unexplored actions.".to_owned();
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
                rejection_kind = TraceFailureKind::UnsupportedBoundary;
                let preceding = events[..transition]
                    .iter()
                    .map(|e| {
                        serde_json::to_value(e).expect("serializable native event")["type"]
                            .as_str()
                            .unwrap_or("unknown")
                            .to_owned()
                    })
                    .collect::<Vec<_>>();
                rejection_detail=format!("The selected EOT projection requires a last stable End state followed by exactly one TurnStarted and only neutral PriorityPassed/PhaseChanged events before it. This branch had phase {:?}, {} TurnStarted event(s), and preceding event kinds {:?}; no boundary field actuals are claimed.",node.game.state().phase,events.iter().filter(|e|matches!(e,GameEvent::TurnStarted{..})).count(),preceding);
                milestone_receipts =
                    comparisons(None, None, input, &input.milestones[next..end], None);
            } else {
                for event in &events[..transition] {
                    observe(&candidate, event, &mut progress);
                }
                milestone_receipts = comparisons(
                    Some(&node.game),
                    Some(&progress),
                    input,
                    &input.milestones[next..end],
                    Some(node.trace.len()),
                );
                if !matching(&milestone_receipts) {
                    reject = true;
                } else {
                    next = end;
                }
            }
            if !reject {
                progress.events.clear();
                progress.combat_damage = [0; 2];
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
        let transition = TraceTransition {
            index: node.trace.len(),
            seat: action.seat,
            action: action.action.clone(),
            before: project_state(&node.game),
            after: project_state(&candidate),
            events,
        };
        if reject {
            let make_failure = || TraceFailure {
                path_kind: FailurePathKind::SeparateSearchBranch,
                kind: rejection_kind.clone(),
                detail: rejection_detail.clone(),
                actions_before: node.trace.clone(),
                attempted_action: Some(action.clone()),
                attempt: Some(transition.clone()),
                state: project_state(&node.game),
                milestones: milestone_receipts.clone(),
            };
            retain_failure(
                &mut retained_failure,
                node.next,
                &rejection_kind,
                make_failure,
            );
            if rejection_kind == TraceFailureKind::UnsupportedBoundary {
                retain_failure(
                    &mut retained_boundary,
                    node.next,
                    &rejection_kind,
                    make_failure,
                );
            }
            continue;
        }
        let path = Some(Arc::new(RecordedStep {
            previous: node.path.clone(),
            transition,
            milestones: milestone_receipts,
        }));
        let mut trace = node.trace.clone();
        trace.push(action);
        if next > result.milestones_fitted {
            result.milestones_fitted = next;
            result.witness = trace.clone();
            best_path = path.clone();
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
        stack.push(Node::new(candidate, progress, next, trace, path, input));
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
    let (transitions, mut milestones) = materialize(&best_path);
    let reached = milestones.iter().map(|m| m.key.clone()).collect::<Vec<_>>();
    let missing = all_trace_keys(input)
        .into_iter()
        .filter(|k| !reached.contains(k))
        .collect::<Vec<_>>();
    milestones.extend(comparisons(None, None, input, &missing, None));
    let trace = result.trace.as_mut().unwrap();
    trace.transitions = transitions;
    trace.milestones = milestones;
    if result.status == FitStatus::MatchedSupportedProjection {
        trace.path_kind = TracePathKind::CompleteWitness;
    } else {
        trace.failure = if result.status == FitStatus::UnsupportedBoundary {
            retained_boundary.or(retained_failure)
        } else {
            retained_failure
        }
        .map(|(_, f)| f);
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
        let mut impossible_later = input.clone();
        impossible_later.fields[1].expected = Some(serde_json::json!(["Never in either deck"]));
        let partial = search_game(
            &runtime,
            &impossible_later,
            FitLimits {
                nodes: 100,
                max_actions: 100,
            },
        )
        .unwrap();
        assert_eq!(partial.milestones_fitted, 1);
        let partial_trace = partial.trace.unwrap();
        assert_eq!(partial_trace.path_kind, TracePathKind::LongestPrefix);
        assert_eq!(partial_trace.transitions.len(), partial.witness.len());
        assert_eq!(
            partial_trace.milestones[0].fields[0].comparison,
            FieldComparison::Matched
        );
        assert_eq!(
            partial_trace.milestones[1].fields[0].comparison,
            FieldComparison::NotReached
        );
        assert!(partial_trace.milestones[1].fields[0].actual.is_none());
        let failure = partial_trace.failure.unwrap();
        assert_eq!(failure.kind, TraceFailureKind::MilestoneMismatch);
        assert_eq!(
            failure.milestones[0].fields[0].comparison,
            FieldComparison::Mismatched
        );
        assert!(failure.actions_before.len() > partial.witness.len());
        // Replaying exact returned actions independently must satisfy the later named-hand field.
        let (mut replay, _) = runtime
            .new_limited_game_for_fitting(input.decks.clone(), input.libraries.clone(), 0, 0)
            .unwrap();
        let recorded = result
            .trace
            .as_ref()
            .expect("new results retain original transitions");
        assert_eq!(recorded.path_kind, TracePathKind::CompleteWitness);
        assert!(recorded.failure.is_none());
        assert_eq!(recorded.transitions.len(), result.witness.len());
        assert_eq!(recorded.milestones.len(), 3);
        for receipt in &recorded.milestones {
            assert_eq!(
                receipt.state_position,
                Some(TraceStatePosition::BeforeTransition)
            );
            let transition = &recorded.transitions[receipt.transition_index.unwrap()];
            assert_eq!(transition.before.turn_owner, receipt.key.turn_owner);
            assert!(transition
                .events
                .iter()
                .any(|e| matches!(e, GameEvent::TurnStarted { .. })));
            assert!(receipt
                .fields
                .iter()
                .all(|f| f.comparison == FieldComparison::Matched
                    && f.actual.is_some()
                    && f.expected.is_some()));
        }
        let mut last_before = None;
        for (index, a) in result.witness.iter().enumerate() {
            let before = replay.fork();
            let out = replay.submit(a.seat, a.action.clone()).unwrap();
            let transition = &recorded.transitions[index];
            assert_eq!(transition.index, index);
            assert_eq!(
                serde_json::to_value(&transition.before).unwrap(),
                serde_json::to_value(project_state(&before)).unwrap()
            );
            assert_eq!(
                serde_json::to_value(&transition.after).unwrap(),
                serde_json::to_value(project_state(&replay)).unwrap()
            );
            assert_eq!(
                serde_json::to_value(&transition.events).unwrap(),
                serde_json::to_value(&out.events).unwrap()
            );
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
    fn rejected_branch_retains_original_comparisons_separate_from_prefix() {
        let runtime = runtime();
        let mut input = input();
        let key = MilestoneKey {
            turn_owner: 0,
            turn_index: 1,
            boundary: Boundary::EndOfTurn,
            observed_player: 0,
        };
        input
            .fields
            .push(field(key.clone(), "life", Value::from(999)));
        let mut combat = field(key.clone(), "unused", Value::Null);
        combat.column = "user_turn_1_user_combat_damage_taken".into();
        combat.raw = "-9".into();
        combat.reason = "source aggregation unverified; negative source values retained".into();
        combat.disposition = FieldDisposition::Unsupported;
        combat.projection = None;
        combat.expected = None;
        input.fields.push(combat);
        let mut unknown = field(key.clone(), "hand_count", Value::Null);
        unknown.column = "user_turn_1_unknown".into();
        unknown.raw = String::new();
        unknown.disposition = FieldDisposition::Informational;
        unknown.expected = None;
        unknown.projection = None;
        input.fields.push(unknown);
        input.milestones.push(key.clone());
        let result = search_game(
            &runtime,
            &input,
            FitLimits {
                nodes: 100,
                max_actions: 40,
            },
        )
        .unwrap();
        assert_ne!(result.status, FitStatus::MatchedSupportedProjection);
        assert_eq!(result.milestones_fitted, 0);
        let diagnostic = result
            .issues
            .iter()
            .find(|i| i.kind == IssueKind::UnsupportedProjection)
            .unwrap();
        assert_eq!(
            diagnostic.detail,
            "no implemented projection for this recorded field; ability IDs are not card IDs"
        );
        assert_eq!(
            diagnostic.evidence.as_ref().unwrap()["diagnostic_code"],
            "combat_source_aggregation_unverified"
        );
        assert_eq!(
            diagnostic.evidence.as_ref().unwrap()["reason"],
            "source aggregation unverified; negative source values retained"
        );
        let trace = result.trace.unwrap();
        assert!(trace.transitions.is_empty());
        assert_eq!(
            trace.milestones[0].fields[0].comparison,
            FieldComparison::NotReached
        );
        assert!(trace.milestones[0].fields[0].actual.is_none());
        let failure = trace.failure.expect("a real rejected branch is retained");
        assert_eq!(failure.path_kind, FailurePathKind::SeparateSearchBranch);
        assert_eq!(failure.kind, TraceFailureKind::MilestoneMismatch);
        let transition = failure.attempt.unwrap();
        assert_eq!(transition.index, failure.actions_before.len());
        let receipt = &failure.milestones[0];
        assert_eq!(receipt.key, key);
        assert_eq!(receipt.transition_index, Some(transition.index));
        assert_eq!(receipt.fields[0].comparison, FieldComparison::Mismatched);
        assert_eq!(receipt.fields[0].actual, Some(Value::from(20)));
        assert_eq!(receipt.fields[0].expected, Some(Value::from(999)));
        assert_eq!(receipt.fields[1].comparison, FieldComparison::Unsupported);
        assert!(receipt.fields[1].actual.is_none());
        assert_eq!(
            receipt.fields[1].diagnostic.as_ref().unwrap().value,
            Value::from(0)
        );
        assert_eq!(receipt.fields[2].comparison, FieldComparison::Unknown);
        assert!(receipt.fields[2].actual.is_none());
        // The unsuccessful branch is independently reproducible, without indexing
        // into the empty main longest-prefix trace.
        let (mut replay, _) = runtime
            .new_limited_game_for_fitting(input.decks.clone(), input.libraries.clone(), 0, 0)
            .unwrap();
        for action in failure.actions_before {
            replay.submit(action.seat, action.action).unwrap();
        }
        assert_eq!(
            serde_json::to_value(project_state(&replay)).unwrap(),
            serde_json::to_value(&transition.before).unwrap()
        );
        let events = replay
            .submit(transition.seat, transition.action)
            .unwrap()
            .events;
        assert_eq!(
            serde_json::to_value(events).unwrap(),
            serde_json::to_value(transition.events).unwrap()
        );
    }

    #[test]
    fn budget_and_input_issue_never_fabricate_field_actuals() {
        let runtime = runtime();
        let mut input = input();
        let key = MilestoneKey {
            turn_owner: 0,
            turn_index: 1,
            boundary: Boundary::EndOfTurn,
            observed_player: 0,
        };
        input
            .fields
            .push(field(key.clone(), "life", Value::from(20)));
        input.milestones.push(key);
        let budget = search_game(
            &runtime,
            &input,
            FitLimits {
                nodes: 1,
                max_actions: 40,
            },
        )
        .unwrap();
        assert_eq!(budget.status, FitStatus::BudgetExhausted);
        let trace = budget.trace.unwrap();
        assert_eq!(trace.path_kind, TracePathKind::LongestPrefix);
        assert_eq!(trace.failure.unwrap().kind, TraceFailureKind::NodeBudget);
        assert_eq!(
            trace.milestones[0].fields[0].comparison,
            FieldComparison::NotReached
        );
        assert!(trace.milestones[0].fields[0].actual.is_none());
        input.mulligans[1] = None;
        let invalid = search_game(&runtime, &input, FitLimits::default()).unwrap();
        let trace = invalid.trace.unwrap();
        assert_eq!(trace.path_kind, TracePathKind::NoExecution);
        assert!(trace.initial_state.is_none());
        assert!(trace.transitions.is_empty());
        assert!(trace.failure.is_none());
        assert_eq!(
            trace.milestones[0].fields[0].comparison,
            FieldComparison::NotReached
        );
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
