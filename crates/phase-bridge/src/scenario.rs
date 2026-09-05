//! Test setup and observation adapter. All transitions use Phase's scenario driver.
//! No card names, expected values, or repaired rules live at this boundary.

use super::*;
use loop_contract::{
    digest, CardZone, CastFinish, ExecutionOutcome, IncompleteReason, Mana, ObjectObservation,
    Observation, Operation, Scenario, Seat, StepEvidence, Target,
};
use phase_engine::game::scenario::GameScenario;
use phase_engine::game::scenario_db::GameScenarioDbExt;
use phase_engine::types::counter::CounterType;
use phase_engine::types::mana::{ManaType, ManaUnit};
use phase_engine::types::phase::Phase;
use std::collections::BTreeMap;

impl PhaseRuntime {
    pub fn execute_scenario(&self, scenario: &Scenario) -> ExecutionOutcome {
        let execute = || -> Result<_, IncompleteReason> {
            scenario
                .validate()
                .map_err(|detail| IncompleteReason::InvalidScenario { detail })?;
            let mut setup = GameScenario::new_n_player(2, scenario.seed);
            setup.at_phase(Phase::PreCombatMain);
            for seat in [Seat::Player, Seat::Opponent] {
                let player = PlayerId(seat.index() as u8);
                setup.with_life(player, scenario.life[seat.index()]);
                setup.with_mana_pool(
                    player,
                    scenario.mana[seat.index()]
                        .iter()
                        .map(|mana| {
                            let mana = match mana {
                                Mana::White => ManaType::White,
                                Mana::Blue => ManaType::Blue,
                                Mana::Black => ManaType::Black,
                                Mana::Red => ManaType::Red,
                                Mana::Green => ManaType::Green,
                                Mana::Colorless => ManaType::Colorless,
                            };
                            ManaUnit::new(mana, ObjectId(0), false, vec![])
                        })
                        .collect(),
                );
            }
            let mut labels = BTreeMap::new();
            for card in &scenario.cards {
                if self.cards.get_face_by_name(&card.name).is_none() {
                    return Err(IncompleteReason::UnresolvedCard {
                        name: card.name.clone(),
                    });
                }
                let id = setup.add_real_card(
                    PlayerId(card.owner.index() as u8),
                    &card.name,
                    to_phase_zone(card.zone),
                    &self.cards,
                );
                labels.insert(card.label.clone(), id.0);
            }
            let mut runner = setup.build();
            for card in &scenario.cards {
                let object = runner
                    .state_mut()
                    .objects
                    .get_mut(&ObjectId(labels[&card.label]))
                    .ok_or("setup object missing")?;
                object.tapped = card.tapped;
                if card.plus_one_counters > 0 {
                    object
                        .counters
                        .insert(CounterType::Plus1Plus1, card.plus_one_counters);
                }
            }
            rehydrate_game_from_card_db(runner.state_mut(), &self.cards);
            finalize_public_state(runner.state_mut());
            let mut steps = Vec::new();
            for (index, operation) in scenario.operations.iter().enumerate() {
                match operation {
                    Operation::Cast {
                        card,
                        targets,
                        finish,
                        x,
                    } => {
                        let mut cast = runner.cast(ObjectId(labels[card]));
                        for target in targets {
                            cast = match target {
                                Target::Player { seat } => {
                                    cast.target_player(PlayerId(seat.index() as u8))
                                }
                                Target::Object { label } => {
                                    cast.target_object(ObjectId(labels[label]))
                                }
                            };
                        }
                        if let Some(x) = x {
                            cast = cast.x(*x);
                        }
                        match finish {
                            CastFinish::Commit => {
                                cast.commit();
                            }
                            CastFinish::Resolve => {
                                cast.try_resolve()
                                    .map_err(|e| format!("operation {index}: {e}"))?;
                            }
                        }
                    }
                    Operation::PassPriority => {
                        runner
                            .act(GameAction::PassPriority)
                            .map_err(|e| format!("operation {index}: {e}"))?;
                    }
                    Operation::ResolveStack => {
                        runner.advance_until_stack_empty();
                    }
                }
                // These are scenario-operation checkpoints, not a claim of individual action tracing.
                let game = PhaseGame {
                    state: runner.state().clone(),
                    cards: self.cards.clone(),
                };
                let checkpoint: Value =
                    serde_json::from_str(&game.checkpoint_json().map_err(|e| e.to_string())?)
                        .map_err(|e| e.to_string())?;
                steps.push(StepEvidence {
                    operation_index: index,
                    state_sha256: digest(&checkpoint).map_err(|e| e.to_string())?,
                });
            }
            let game = PhaseGame {
                state: runner.state().clone(),
                cards: self.cards.clone(),
            };
            let observation = observe(&game, labels);
            Ok((observation, steps))
        };
        match std::panic::catch_unwind(std::panic::AssertUnwindSafe(execute)) {
            Ok(Ok((observation, steps))) => ExecutionOutcome::Completed { observation, steps },
            Ok(Err(reason)) => ExecutionOutcome::Inconclusive { reason },
            Err(payload) => {
                let detail = payload
                    .downcast_ref::<String>()
                    .cloned()
                    .or_else(|| payload.downcast_ref::<&str>().map(|s| s.to_string()))
                    .unwrap_or_else(|| "unknown panic".into());
                ExecutionOutcome::Inconclusive {
                    reason: IncompleteReason::DriverFailed { detail },
                }
            }
        }
    }
}

fn observe(game: &PhaseGame, labels: BTreeMap<String, u64>) -> Observation {
    let offers = [game.legal_actions(0), game.legal_actions(1)];
    let mut objects: Vec<_> = game
        .state
        .objects
        .iter()
        .map(|(id, object)| {
            let cast_spell_offered_to = [Seat::Player, Seat::Opponent]
                .into_iter()
                .filter(|seat| {
                    let (flat, _, grouped) = &offers[seat.index()];
                    flat.iter().chain(grouped.values().flatten()).any(|action|
                matches!(action, GameAction::CastSpell {object_id, ..} if object_id == id))
                })
                .collect();
            ObjectObservation {
                object_id: id.0,
                name: object.name.clone(),
                owner: if object.owner.0 == 0 {
                    Seat::Player
                } else {
                    Seat::Opponent
                },
                zone: from_phase_zone(object.zone),
                tapped: object.tapped,
                plus_one_counters: object
                    .counters
                    .get(&CounterType::Plus1Plus1)
                    .copied()
                    .unwrap_or(0),
                prepared: object.prepared.is_some(),
                cast_spell_offered_to,
            }
        })
        .collect();
    objects.sort_by_key(|object| object.object_id);
    Observation {
        life: [game.state.players[0].life, game.state.players[1].life],
        objects,
        labels,
    }
}

fn to_phase_zone(zone: CardZone) -> Zone {
    match zone {
        CardZone::Hand => Zone::Hand,
        CardZone::Library => Zone::Library,
        CardZone::Battlefield => Zone::Battlefield,
        CardZone::Graveyard => Zone::Graveyard,
        CardZone::Exile => Zone::Exile,
        CardZone::Stack => Zone::Stack,
        CardZone::Command => Zone::Command,
    }
}
fn from_phase_zone(zone: Zone) -> CardZone {
    match zone {
        Zone::Hand => CardZone::Hand,
        Zone::Library => CardZone::Library,
        Zone::Battlefield => CardZone::Battlefield,
        Zone::Graveyard => CardZone::Graveyard,
        Zone::Exile => CardZone::Exile,
        Zone::Stack => CardZone::Stack,
        Zone::Command => CardZone::Command,
    }
}
