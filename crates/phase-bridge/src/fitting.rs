//! Explicit hidden-state assumptions used by the partial-observation fitter.
//!
//! Setup fixes a complete initial ordering. Subsequent transitions, including
//! opening draws and mulligan decisions, are performed by the pinned engine.

use super::*;
use phase_engine::game::engine::start_game_with_starting_player;
use std::collections::BTreeMap;

impl PhaseRuntime {
    /// Resolve a known name to the exact face name used by the Phase corpus.
    pub fn canonical_card_name(&self, name: &str) -> Option<String> {
        self.cards
            .get_face_by_name(name)
            .map(|face| face.name.clone())
    }

    /// Start a fitting game with a fixed starter and complete initial orders.
    ///
    /// Each `libraries` entry is top-to-bottom *before the opening draw*, so
    /// its first seven cards become that player's initial hand. The order must
    /// contain the complete corresponding deck multiset. These fixed orders
    /// are reconstruction assumptions, not evidence about unobserved cards.
    ///
    /// Phase still offers its normal mulligan choices. A fitter constrained by
    /// recorded zero mulligans must admit only Phase's offered Keep decisions.
    /// Later shuffles and draws continue to use Phase's seeded RNG normally.
    pub fn new_limited_game_for_fitting(
        &self,
        decks: [Vec<String>; 2],
        libraries: [Vec<String>; 2],
        starting_player: u8,
        seed: u64,
    ) -> Result<(PhaseGame, ActionResult), BridgeError> {
        if starting_player > 1 {
            return Err(BridgeError::FittingSetup(format!(
                "starting player must be seat 0 or 1, received {starting_player}"
            )));
        }
        let mut requested_names: [Vec<String>; 2] = Default::default();
        for seat in 0..2 {
            let unknown = decks[seat]
                .iter()
                .filter(|name| self.canonical_card_name(name).is_none())
                .cloned()
                .collect::<Vec<_>>();
            if !unknown.is_empty() {
                return Err(BridgeError::UnknownCards {
                    seat,
                    names: unknown,
                });
            }
            let canonical_deck = decks[seat]
                .iter()
                .map(|name| self.canonical_card_name(name).expect("validated deck name"))
                .collect::<Vec<_>>();
            requested_names[seat] = libraries[seat]
                .iter()
                .map(|name| {
                    self.canonical_card_name(name).ok_or_else(|| {
                        BridgeError::FittingSetup(format!(
                            "seat {seat} library contains unknown card {name:?}"
                        ))
                    })
                })
                .collect::<Result<_, _>>()?;
            if name_counts(&canonical_deck) != name_counts(&requested_names[seat]) {
                return Err(BridgeError::FittingSetup(format!(
                    "seat {seat} library order must contain the complete deck multiset"
                )));
            }
        }

        let deck_list = PhaseDeckList {
            player: PlayerDeckList {
                main_deck: decks[0].clone(),
                ..PlayerDeckList::default()
            },
            opponent: PlayerDeckList {
                main_deck: decks[1].clone(),
                ..PlayerDeckList::default()
            },
            ..PhaseDeckList::default()
        };
        let payload = resolve_deck_list(&self.cards, &deck_list);
        let mut state = GameState::new(FormatConfig::limited(), 2, seed);
        load_and_hydrate_decks(&mut state, &payload, Some(&self.cards));
        state.all_card_names = self.cards.card_names().into();

        // Probe the shuffle's permutation on a clone of the exact pregame RNG
        // state. Reorder the original input by its inverse, then let Phase run
        // opening draws normally. Rewriting hand/library lists after starting
        // would leave zone-change events and object incarnation state stale.
        let mut probe = state.clone();
        start_game_with_starting_player(&mut probe, PlayerId(starting_player));
        let mut desired_orders: [Vec<ObjectId>; 2] = Default::default();
        for seat in 0..2 {
            let original = state.players[seat]
                .library
                .iter()
                .copied()
                .collect::<Vec<_>>();
            let shuffled = initial_order(&probe, seat);
            if original.len() != shuffled.len() || original.len() != requested_names[seat].len() {
                return Err(BridgeError::FittingSetup(format!(
                    "seat {seat} pregame setup changed the deck multiset"
                )));
            }
            let mut remaining = original.clone();
            for name in &requested_names[seat] {
                let index = remaining
                    .iter()
                    .position(|id| {
                        state
                            .objects
                            .get(id)
                            .is_some_and(|object| object.name == *name)
                    })
                    .ok_or_else(|| {
                        BridgeError::FittingSetup(format!(
                            "seat {seat} hydrated deck does not contain requested card {name:?}"
                        ))
                    })?;
                desired_orders[seat].push(remaining.remove(index));
            }
            let mut reordered = original.clone();
            for (position, id) in shuffled.iter().enumerate() {
                let source_position = original
                    .iter()
                    .position(|original_id| original_id == id)
                    .ok_or_else(|| {
                        BridgeError::FittingSetup(format!(
                            "seat {seat} pregame setup changed a card's object identity"
                        ))
                    })?;
                reordered[source_position] = desired_orders[seat][position];
            }
            state.players[seat].library = reordered.into_iter().collect();
        }
        let initial = start_game_with_starting_player(&mut state, PlayerId(starting_player));
        for (seat, expected) in desired_orders.iter().enumerate() {
            if initial_order(&state, seat) != *expected {
                return Err(BridgeError::FittingSetup(format!(
                    "seat {seat} pregame shuffle did not preserve the requested order"
                )));
            }
        }
        Ok((
            PhaseGame {
                state,
                cards: self.cards.clone(),
            },
            initial,
        ))
    }
}

impl PhaseGame {
    /// Branch an authoritative search state, including its current RNG stream.
    pub fn fork(&self) -> Self {
        Self {
            state: self.state.clone(),
            cards: self.cards.clone(),
        }
    }
}

fn initial_order(state: &GameState, seat: usize) -> Vec<ObjectId> {
    state.players[seat]
        .hand
        .iter()
        .chain(state.players[seat].library.iter())
        .copied()
        .collect()
}

fn name_counts(names: &[String]) -> BTreeMap<&str, usize> {
    let mut counts = BTreeMap::new();
    for name in names {
        *counts.entry(name.as_str()).or_insert(0) += 1;
    }
    counts
}

#[cfg(test)]
mod tests {
    use super::*;
    use phase_engine::types::actions::MulliganChoice;

    fn runtime() -> PhaseRuntime {
        let land = |name, oracle_id| {
            serde_json::json!({
                "name": name,
                "mana_cost": {"type": "NoCost"},
                "card_type": {"supertypes": ["Basic"], "core_types": ["Land"], "subtypes": ["Mountain"]},
                "power": null, "toughness": null, "loyalty": null, "defense": null,
                "oracle_text": "", "non_ability_text": null, "flavor_name": null,
                "keywords": [], "abilities": [], "triggers": [], "static_abilities": [],
                "replacements": [], "color_override": null, "color_identity": ["Red"],
                "scryfall_oracle_id": oracle_id, "legalities": {}, "printings": ["TST"]
            })
        };
        PhaseRuntime::from_card_data_json(
            &serde_json::json!({
                "alpha": land("Alpha", "00000000-0000-0000-0000-000000000001"),
                "beta": land("Beta", "00000000-0000-0000-0000-000000000002")
            })
            .to_string(),
        )
        .unwrap()
    }

    fn deck() -> Vec<String> {
        [vec!["Alpha".to_owned(); 20], vec!["Beta".to_owned(); 20]].concat()
    }

    #[test]
    fn fitting_setup_preserves_starter_order_and_opening_events() {
        let runtime = runtime();
        let ordered = [
            vec!["Beta".to_owned(); 7],
            vec!["Alpha".to_owned(); 20],
            vec!["Beta".to_owned(); 13],
        ]
        .concat();
        for starter in [0, 1] {
            for seed in [41, 42] {
                let (mut game, initial) = runtime
                    .new_limited_game_for_fitting(
                        [deck(), deck()],
                        [ordered.clone(), ordered.clone()],
                        starter,
                        seed,
                    )
                    .unwrap();
                assert_eq!(game.state().active_player.0, starter);
                assert_eq!(game.state().current_starting_player.0, starter);
                assert_eq!(game.state().seat_order[0].0, starter);
                assert!(initial.events.iter().any(|event| matches!(event,
                    GameEvent::TurnStarted { player_id, turn_number: 1 } if player_id.0 == starter
                )));
                assert!(!initial
                    .events
                    .iter()
                    .any(|event| matches!(event, GameEvent::StartingPlayerContest { .. })));
                for seat in 0..2 {
                    let state = game.state();
                    let names = initial_order(state, seat)
                        .iter()
                        .map(|id| state.objects[id].name.clone())
                        .collect::<Vec<_>>();
                    assert_eq!(names, ordered);
                    assert_eq!(state.players[seat].hand.len(), 7);
                    assert!(state.players[seat]
                        .hand
                        .iter()
                        .all(|id| state.objects[id].zone == Zone::Hand));
                    assert!(state.players[seat]
                        .library
                        .iter()
                        .all(|id| state.objects[id].zone == Zone::Library));
                }
                let opening_moves = initial
                    .events
                    .iter()
                    .filter(|event| {
                        matches!(
                            event,
                            GameEvent::ZoneChanged {
                                from: Some(Zone::Library),
                                to: Zone::Hand,
                                ..
                            }
                        )
                    })
                    .count();
                assert_eq!(opening_moves, 14);
                for event in &initial.events {
                    if let GameEvent::CardDrawn {
                        player_id,
                        object_id,
                        ..
                    } = event
                    {
                        assert!(game.state().players[usize::from(player_id.0)]
                            .hand
                            .contains(object_id));
                    }
                    if let GameEvent::ZoneChanged {
                        object_id,
                        from: Some(Zone::Library),
                        to: Zone::Hand,
                        ..
                    } = event
                    {
                        assert_eq!(game.state().objects[object_id].name, "Beta");
                        assert!(game
                            .state()
                            .players
                            .iter()
                            .any(|player| player.hand.contains(object_id)));
                    }
                }
                let before = game.fork();
                for seat in [0, 1] {
                    let keep = game
                        .legal_actions(seat)
                        .0
                        .into_iter()
                        .find(|action| {
                            matches!(
                                action,
                                GameAction::MulliganDecision {
                                    choice: MulliganChoice::Keep
                                }
                            )
                        })
                        .unwrap();
                    game.submit(seat, keep).unwrap();
                }
                assert_eq!(game.state().active_player.0, starter);
                assert!(matches!(
                    before.state().waiting_for,
                    WaitingFor::MulliganDecision { .. }
                ));
                assert!(!matches!(
                    game.state().waiting_for,
                    WaitingFor::MulliganDecision { .. }
                ));
            }
        }
    }

    #[test]
    fn fitting_setup_rejects_incomplete_or_different_multisets_and_invalid_starter() {
        let runtime = runtime();
        for invalid in [vec!["Alpha".to_owned(); 40], vec!["Alpha".to_owned(); 39]] {
            assert!(matches!(
                runtime.new_limited_game_for_fitting([deck(), deck()], [invalid, deck()], 0, 41),
                Err(BridgeError::FittingSetup(_))
            ));
        }
        assert!(matches!(
            runtime.new_limited_game_for_fitting([deck(), deck()], [deck(), deck()], 2, 41),
            Err(BridgeError::FittingSetup(_))
        ));
    }
}
