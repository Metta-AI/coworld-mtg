//! Coworld-facing adapter for the Phase Magic rules engine.
//!
//! The Phase engine is the rules authority. This crate deliberately does not
//! reproduce Magic rules; it translates deck/configuration input and exposes
//! Phase's exact legal actions and viewer-filtered state to the host.

use phase_engine::ai_support::{legal_actions_for_viewer, LegalActionsFull};
use phase_engine::database::CardDatabase;
use phase_engine::game::deck_loading::{resolve_deck_list, DeckList, PlayerDeckList};
use phase_engine::game::engine::{apply, start_game};
use phase_engine::game::{filter_state_for_viewer, load_and_hydrate_decks};
use phase_engine::types::format::FormatConfig;
use phase_engine::types::player::PlayerId;
use thiserror::Error;

pub use phase_engine::types::actions::GameAction;
pub use phase_engine::types::events::GameEvent;
pub use phase_engine::types::game_state::{ActionResult, GameState};

/// The exact upstream Phase revision used by this adapter.
pub const PHASE_REVISION: &str = "f6fd1fca5c581bcd127d5b18742623e1298ae3c7";

#[derive(Debug, Error)]
pub enum BridgeError {
    #[error("failed to load Phase card data: {0}")]
    CardData(#[from] serde_json::Error),
    #[error("deck {seat} contains cards absent from the Phase card database: {names:?}")]
    UnknownCards { seat: usize, names: Vec<String> },
    #[error("Phase rejected the action: {0}")]
    Action(String),
}

/// Immutable card corpus plus helpers for creating independent games.
pub struct PhaseRuntime {
    cards: CardDatabase,
}

impl PhaseRuntime {
    /// Load Phase's generated Oracle/card export.
    ///
    /// The export stores Scryfall Oracle IDs and parsed card rules. Keeping this
    /// corpus outside the executable lets the Coworld image update card data
    /// independently while the rules engine remains revision-pinned.
    pub fn from_card_data_json(json: &str) -> Result<Self, BridgeError> {
        Ok(Self {
            cards: CardDatabase::from_json_str(json)?,
        })
    }

    pub fn card_count(&self) -> usize {
        self.cards.card_count()
    }

    /// Start a two-player 40-card Limited game from exact English card names.
    pub fn new_limited_game(
        &self,
        decks: [Vec<String>; 2],
        seed: u64,
    ) -> Result<(PhaseGame, ActionResult), BridgeError> {
        for (seat, names) in decks.iter().enumerate() {
            let unknown = names
                .iter()
                .filter(|name| self.cards.get_face_by_name(name).is_none())
                .cloned()
                .collect::<Vec<_>>();
            if !unknown.is_empty() {
                return Err(BridgeError::UnknownCards {
                    seat,
                    names: unknown,
                });
            }
        }

        let deck_list = DeckList {
            player: PlayerDeckList {
                main_deck: decks[0].clone(),
                ..PlayerDeckList::default()
            },
            opponent: PlayerDeckList {
                main_deck: decks[1].clone(),
                ..PlayerDeckList::default()
            },
            ..DeckList::default()
        };
        let payload = resolve_deck_list(&self.cards, &deck_list);
        let mut state = GameState::new(FormatConfig::limited(), 2, seed);
        load_and_hydrate_decks(&mut state, &payload, Some(&self.cards));
        state.all_card_names = self.cards.card_names().into();
        let initial = start_game(&mut state);
        Ok((PhaseGame { state }, initial))
    }
}

/// An authoritative Phase game owned by the Coworld episode runner.
pub struct PhaseGame {
    state: GameState,
}

impl PhaseGame {
    pub fn state(&self) -> &GameState {
        &self.state
    }

    pub fn viewer_state(&self, seat: u8) -> GameState {
        filter_state_for_viewer(&self.state, PlayerId(seat))
    }

    /// Return only actions Phase authorizes this viewer to submit now.
    pub fn legal_actions(&self, seat: u8) -> LegalActionsFull {
        legal_actions_for_viewer(&self.state, PlayerId(seat))
    }

    /// Apply an exact Phase action. Mana, timing, targets, combat, priority,
    /// triggers, replacement effects, and state-based actions are all resolved
    /// inside Phase rather than reconstructed by this adapter.
    pub fn submit(&mut self, seat: u8, action: GameAction) -> Result<ActionResult, BridgeError> {
        apply(&mut self.state, PlayerId(seat), action)
            .map_err(|error| BridgeError::Action(error.to_string()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn deck(json: &str) -> Vec<String> {
        let value: serde_json::Value = serde_json::from_str(json).unwrap();
        value["cards"]
            .as_array()
            .unwrap()
            .iter()
            .flat_map(|entry| {
                let count = entry["count"].as_u64().unwrap() as usize;
                let name = entry["spec"]["name"].as_str().unwrap().to_owned();
                std::iter::repeat_n(name, count)
            })
            .collect()
    }

    #[test]
    fn pins_a_reviewable_upstream_revision() {
        assert_eq!(PHASE_REVISION.len(), 40);
        assert!(PHASE_REVISION.chars().all(|ch| ch.is_ascii_hexdigit()));
    }

    #[test]
    fn bundled_decks_enter_phase_mulligan_with_exact_legal_actions() {
        let runtime =
            PhaseRuntime::from_card_data_json(include_str!("../tests/fixtures/card-data.json"))
                .unwrap();
        assert_eq!(runtime.card_count(), 15);

        let decks = [
            deck(include_str!("../../../decks/red_rush.json")),
            deck(include_str!("../../../decks/green_stompy.json")),
        ];
        let (mut game, initial) = runtime.new_limited_game(decks, 4242).unwrap();
        assert!(!initial.events.is_empty());
        assert_eq!(game.state().players[0].hand.len(), 7);
        assert_eq!(game.state().players[1].hand.len(), 7);

        // Phase models CR 103.5 as simultaneous decisions. Each seat receives
        // only its own exact legal action values from the same authoritative
        // state; Cogatrice does not synthesize a generic "keep" command.
        for seat in [0, 1] {
            let (actions, _, _) = game.legal_actions(seat);
            let keep = actions
                .into_iter()
                .find(|action| {
                    matches!(
                        action,
                        GameAction::MulliganDecision {
                            choice: phase_engine::types::actions::MulliganChoice::Keep
                        }
                    )
                })
                .expect("Phase must offer this seat a legal keep decision");
            game.submit(seat, keep).unwrap();
        }

        assert!(game.legal_actions(0).0.len() + game.legal_actions(1).0.len() > 0);
    }
}
