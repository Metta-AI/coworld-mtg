//! Coworld-facing adapter for the Phase Magic rules engine.
//!
//! The Phase engine is the rules authority. This crate deliberately does not
//! reproduce Magic rules; it translates deck/configuration input and exposes
//! Phase's exact legal actions and viewer-filtered state to the host.

use phase_engine::ai_support::{legal_actions_for_viewer, LegalActionsFull};
use phase_engine::database::CardDatabase;
use phase_engine::game::deck_loading::{
    resolve_deck_list, DeckList as PhaseDeckList, PlayerDeckList,
};
use phase_engine::game::engine::{apply, start_game};
use phase_engine::game::{
    filter_events_for_viewer, filter_state_for_viewer, finalize_public_state,
    load_and_hydrate_decks, rehydrate_game_from_card_db,
};
use phase_engine::types::card_type::CoreType;
use phase_engine::types::format::FormatConfig;
use phase_engine::types::game_state::WaitingFor;
use phase_engine::types::identifiers::ObjectId;
use phase_engine::types::mana::{ManaCost, ManaPool};
use phase_engine::types::player::PlayerId;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;
use std::sync::Arc;
use thiserror::Error;

pub use phase_engine::types::actions::GameAction;
pub use phase_engine::types::events::GameEvent;
pub use phase_engine::types::game_state::{ActionResult, GameState};

/// The exact upstream Phase revision used by this adapter.
pub const PHASE_REVISION: &str = "f6fd1fca5c581bcd127d5b18742623e1298ae3c7";

pub const SPECTATOR_ID: u8 = u8::MAX;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CardSpec {
    pub name: String,
    pub type_line: String,
    pub mana_cost: Option<String>,
    pub power_toughness: Option<String>,
    pub oracle_text: String,
    pub art_id: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DeckList {
    pub name: String,
    pub cards: Vec<CardSpec>,
}

#[derive(Debug, Error)]
pub enum BridgeError {
    #[error("failed to load Phase card data: {0}")]
    CardData(#[from] serde_json::Error),
    #[error("deck {seat} contains cards absent from the Phase card database: {names:?}")]
    UnknownCards { seat: usize, names: Vec<String> },
    #[error("Phase rejected the action: {0}")]
    Action(String),
    #[error("invalid Phase checkpoint: {0}")]
    Checkpoint(String),
}

/// Immutable card corpus plus helpers for creating independent games.
#[derive(Clone)]
pub struct PhaseRuntime {
    cards: Arc<CardDatabase>,
}

impl PhaseRuntime {
    /// Load Phase's generated Oracle/card export.
    ///
    /// The export stores Scryfall Oracle IDs and parsed card rules. Keeping this
    /// corpus outside the executable lets the Coworld image update card data
    /// independently while the rules engine remains revision-pinned.
    pub fn from_card_data_json(json: &str) -> Result<Self, BridgeError> {
        Ok(Self {
            cards: Arc::new(CardDatabase::from_json_str(json)?),
        })
    }

    /// Compact Phase export containing every card in Cogatrice's bundled decks.
    pub fn bundled() -> Result<Self, BridgeError> {
        Self::from_card_data_json(include_str!("../tests/fixtures/card-data.json"))
    }

    pub fn card_count(&self) -> usize {
        self.cards.card_count()
    }

    /// Restore an authoritative game checkpoint produced by [`PhaseGame::checkpoint_json`].
    ///
    /// The immutable card database is deliberately supplied by the runtime rather than
    /// embedded in every checkpoint. Callers must pair checkpoints with the same corpus
    /// manifest that created them.
    pub fn restore_game(&self, checkpoint_json: &str) -> Result<PhaseGame, BridgeError> {
        let state = std::thread::scope(|scope| {
            std::thread::Builder::new()
                .name("phase-checkpoint-restore".to_owned())
                .stack_size(32 * 1024 * 1024)
                .spawn_scoped(scope, || {
                    let checkpoint: PhaseCheckpoint = serde_json::from_str(checkpoint_json)
                        .map_err(|error| BridgeError::Checkpoint(error.to_string()))?;
                    if checkpoint.schema != "phase-bridge-checkpoint-v1" {
                        return Err(BridgeError::Checkpoint(format!(
                            "unsupported schema {}",
                            checkpoint.schema
                        )));
                    }
                    let mut state = checkpoint.state;
                    state.rng = checkpoint.rng;
                    rehydrate_game_from_card_db(&mut state, &self.cards);
                    finalize_public_state(&mut state);
                    Ok(state)
                })
                .map_err(|error| BridgeError::Checkpoint(error.to_string()))?
                .join()
                .map_err(|_| BridgeError::Checkpoint("restore worker panicked".to_owned()))?
        })?;
        Ok(PhaseGame {
            state,
            cards: self.cards.clone(),
        })
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
        let initial = start_game(&mut state);
        Ok((
            PhaseGame {
                state,
                cards: self.cards.clone(),
            },
            initial,
        ))
    }
}

/// An authoritative Phase game owned by the Coworld episode runner.
pub struct PhaseGame {
    state: GameState,
    cards: Arc<CardDatabase>,
}

impl PhaseGame {
    pub fn state(&self) -> &GameState {
        &self.state
    }

    /// Serialize the complete authoritative Phase state for deterministic replay.
    pub fn checkpoint_json(&self) -> Result<String, BridgeError> {
        std::thread::scope(|scope| {
            std::thread::Builder::new()
                .name("phase-checkpoint-serialize".to_owned())
                .stack_size(32 * 1024 * 1024)
                .spawn_scoped(scope, || {
                    serde_json::to_string(&PhaseCheckpointRef {
                        schema: "phase-bridge-checkpoint-v1",
                        state: &self.state,
                        rng: &self.state.rng,
                    })
                })
                .map_err(|error| BridgeError::Checkpoint(error.to_string()))?
                .join()
                .map_err(|_| BridgeError::Checkpoint("serialization worker panicked".to_owned()))?
                .map_err(|error| BridgeError::Checkpoint(error.to_string()))
        })
    }

    pub fn viewer_state(&self, seat: u8) -> GameState {
        filter_state_for_viewer(&self.state, PlayerId(seat))
    }

    pub fn viewer_snapshot(&self, seat: u8) -> ViewerSnapshot {
        let filtered = self.viewer_state(seat);
        let (legal_actions, spell_costs, legal_actions_by_object) = self.legal_actions(seat);
        ViewerSnapshot::from_state(
            &filtered,
            &self.cards,
            legal_actions,
            spell_costs,
            legal_actions_by_object,
        )
    }

    pub fn spectator_snapshot(&self) -> ViewerSnapshot {
        self.viewer_snapshot(SPECTATOR_ID)
    }

    pub fn full_snapshot(&self) -> ViewerSnapshot {
        ViewerSnapshot::from_state(
            &self.state,
            &self.cards,
            Vec::new(),
            Default::default(),
            Default::default(),
        )
    }

    pub fn filter_events(&self, events: &[GameEvent], viewer: u8) -> Vec<GameEvent> {
        filter_events_for_viewer(events, &self.state, PlayerId(viewer))
    }

    /// Return only actions Phase authorizes this viewer to submit now.
    pub fn legal_actions(&self, seat: u8) -> LegalActionsFull {
        legal_actions_for_viewer(&self.state, PlayerId(seat))
    }

    pub fn pending_seats(&self) -> Vec<u8> {
        (0..self.state.players.len() as u8)
            .filter(|seat| !self.legal_actions(*seat).0.is_empty())
            .collect()
    }

    pub fn outcome(&self) -> Option<PhaseOutcome> {
        let WaitingFor::GameOver { winner } = self.state.waiting_for else {
            return None;
        };
        Some(PhaseOutcome {
            winner: winner.map(|player| player.0),
            final_life: [self.state.players[0].life, self.state.players[1].life],
            turns: self.state.turn_number,
        })
    }

    /// Apply an exact Phase action. Mana, timing, targets, combat, priority,
    /// triggers, replacement effects, and state-based actions are all resolved
    /// inside Phase rather than reconstructed by this adapter.
    pub fn submit(&mut self, seat: u8, action: GameAction) -> Result<ActionResult, BridgeError> {
        let is_concede = matches!(
            action,
            GameAction::Concede {
                player_id: PlayerId(player)
            } if player == seat
        );
        let (flat, _, by_object) = self.legal_actions(seat);
        let is_offered = action_is_offered(&action, &flat, &by_object);
        if !is_concede && !is_offered {
            return Err(BridgeError::Action(
                "action is not in this viewer's current Phase legal-action set".to_owned(),
            ));
        }
        apply(&mut self.state, PlayerId(seat), action)
            .map_err(|error| BridgeError::Action(error.to_string()))
    }

    pub fn concede(&mut self, seat: u8) -> Result<ActionResult, BridgeError> {
        self.submit(
            seat,
            GameAction::Concede {
                player_id: PlayerId(seat),
            },
        )
    }
}

#[derive(Serialize)]
struct PhaseCheckpointRef<'a> {
    schema: &'static str,
    state: &'a GameState,
    rng: &'a rand_chacha_phase::ChaCha20Rng,
}

#[derive(Deserialize)]
struct PhaseCheckpoint {
    schema: String,
    state: GameState,
    rng: rand_chacha_phase::ChaCha20Rng,
}

fn action_is_offered(
    action: &GameAction,
    flat: &[GameAction],
    by_object: &std::collections::HashMap<ObjectId, Vec<GameAction>>,
) -> bool {
    flat.contains(action) || by_object.values().any(|actions| actions.contains(action))
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PhaseOutcome {
    pub winner: Option<u8>,
    pub final_life: [i32; 2],
    pub turns: u32,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ViewerSnapshot {
    pub turn: u32,
    pub phase: String,
    pub active_player: u8,
    pub priority_player: u8,
    pub waiting_for: Value,
    pub players: Vec<PlayerView>,
    pub battlefield: Vec<CardView>,
    pub stack: Vec<StackView>,
    pub exile: Vec<CardView>,
    pub combat: Option<Value>,
    pub legal_actions: Vec<GameAction>,
    pub spell_costs: BTreeMap<String, ManaCost>,
    pub legal_actions_by_object: BTreeMap<String, Vec<GameAction>>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PlayerView {
    pub id: u8,
    pub life: i32,
    pub poison: u32,
    pub energy: u32,
    pub mana_pool: ManaPool,
    pub library_count: usize,
    pub hand: Vec<CardView>,
    pub graveyard: Vec<CardView>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CardView {
    pub object_id: u64,
    pub card_id: u64,
    pub owner: u8,
    pub controller: u8,
    pub zone: String,
    pub name: String,
    pub type_line: String,
    pub mana_cost: ManaCost,
    pub oracle_text: String,
    pub power: Option<i32>,
    pub toughness: Option<i32>,
    pub tapped: bool,
    pub face_down: bool,
    pub attacking: bool,
    pub blocking: Vec<u64>,
    pub counters: Value,
    pub scryfall_oracle_id: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StackView {
    pub id: u64,
    pub source_id: u64,
    pub controller: u8,
    pub source: Option<CardView>,
    pub kind: Value,
}

impl ViewerSnapshot {
    fn from_state(
        state: &GameState,
        cards: &CardDatabase,
        legal_actions: Vec<GameAction>,
        spell_costs: std::collections::HashMap<ObjectId, ManaCost>,
        legal_actions_by_object: std::collections::HashMap<ObjectId, Vec<GameAction>>,
    ) -> Self {
        let card = |id: ObjectId| card_view(state, cards, id);
        Self {
            turn: state.turn_number,
            phase: format!("{:?}", state.phase),
            active_player: state.active_player.0,
            priority_player: state.priority_player.0,
            waiting_for: serde_json::to_value(&state.waiting_for).unwrap_or(Value::Null),
            players: state
                .players
                .iter()
                .map(|player| PlayerView {
                    id: player.id.0,
                    life: player.life,
                    poison: player.poison_counters,
                    energy: player.energy,
                    mana_pool: player.mana_pool.clone(),
                    library_count: player.library.len(),
                    hand: player.hand.iter().filter_map(|id| card(*id)).collect(),
                    graveyard: player.graveyard.iter().filter_map(|id| card(*id)).collect(),
                })
                .collect(),
            battlefield: state
                .battlefield
                .iter()
                .filter_map(|id| card(*id))
                .collect(),
            stack: state
                .stack
                .iter()
                .map(|entry| StackView {
                    id: entry.id.0,
                    source_id: entry.source_id.0,
                    controller: entry.controller.0,
                    source: card(entry.source_id),
                    kind: serde_json::to_value(&entry.kind).unwrap_or(Value::Null),
                })
                .collect(),
            exile: state.exile.iter().filter_map(|id| card(*id)).collect(),
            combat: state
                .combat
                .as_ref()
                .and_then(|combat| serde_json::to_value(combat).ok()),
            legal_actions,
            spell_costs: spell_costs
                .into_iter()
                .map(|(id, cost)| (id.0.to_string(), cost))
                .collect(),
            legal_actions_by_object: legal_actions_by_object
                .into_iter()
                .map(|(id, actions)| (id.0.to_string(), actions))
                .collect(),
        }
    }
}

fn card_view(state: &GameState, cards: &CardDatabase, id: ObjectId) -> Option<CardView> {
    let object = state.objects.get(&id)?;
    let face = cards.get_face_by_name(&object.name);
    let attacking = state
        .combat
        .as_ref()
        .is_some_and(|combat| combat.attackers.iter().any(|entry| entry.object_id == id));
    let blocking = state
        .combat
        .as_ref()
        .and_then(|combat| combat.blocker_to_attacker.get(&id))
        .map(|ids| ids.iter().map(|id| id.0).collect())
        .unwrap_or_default();
    Some(CardView {
        object_id: object.id.0,
        card_id: object.card_id.0,
        owner: object.owner.0,
        controller: object.controller.0,
        zone: format!("{:?}", object.zone),
        name: object.name.clone(),
        type_line: type_line(object),
        mana_cost: object.mana_cost.clone(),
        oracle_text: face
            .and_then(|face| face.oracle_text.clone())
            .or_else(|| object.token_rules_text.clone())
            .unwrap_or_default(),
        power: object.power,
        toughness: object.toughness,
        tapped: object.tapped,
        face_down: object.face_down,
        attacking,
        blocking,
        counters: serde_json::to_value(&object.counters).unwrap_or(Value::Null),
        scryfall_oracle_id: object
            .printed_ref
            .as_ref()
            .map(|reference| reference.oracle_id.clone()),
    })
}

fn type_line(object: &phase_engine::game::game_object::GameObject) -> String {
    let mut left = object
        .card_types
        .supertypes
        .iter()
        .map(ToString::to_string)
        .chain(object.card_types.core_types.iter().map(CoreType::to_string))
        .collect::<Vec<_>>()
        .join(" ");
    if !object.card_types.subtypes.is_empty() {
        left.push_str(" — ");
        left.push_str(&object.card_types.subtypes.join(" "));
    }
    left
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
    fn accepts_actions_phase_groups_only_under_their_source_object() {
        let action = GameAction::PassPriority;
        let grouped = std::collections::HashMap::from([(ObjectId(9), vec![action.clone()])]);
        assert!(action_is_offered(&action, &[], &grouped));
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

    #[test]
    fn viewer_projection_redacts_hidden_cards_and_rejects_invented_actions() {
        let runtime = PhaseRuntime::bundled().unwrap();
        let decks = [
            deck(include_str!("../../../decks/red_rush.json")),
            deck(include_str!("../../../decks/green_stompy.json")),
        ];
        let (mut game, _) = runtime.new_limited_game(decks, 7).unwrap();

        let player = game.viewer_snapshot(0);
        assert!(player.players[0]
            .hand
            .iter()
            .all(|card| card.name != "Hidden Card"));
        assert!(player.players[1]
            .hand
            .iter()
            .all(|card| card.name == "Hidden Card" && card.face_down));

        let spectator = game.spectator_snapshot();
        assert!(spectator
            .players
            .iter()
            .flat_map(|player| &player.hand)
            .all(|card| card.name == "Hidden Card" && card.face_down));

        let error = game.submit(0, GameAction::PassPriority).unwrap_err();
        assert!(error.to_string().contains("legal-action set"));
    }

    #[test]
    fn checkpoint_restore_preserves_authoritative_state() {
        let runtime = PhaseRuntime::bundled().unwrap();
        let decks = [
            deck(include_str!("../../../decks/red_rush.json")),
            deck(include_str!("../../../decks/green_stompy.json")),
        ];
        let (game, _) = runtime.new_limited_game(decks, 99).unwrap();
        let checkpoint = game.checkpoint_json().unwrap();
        let restored = runtime.restore_game(&checkpoint).unwrap();
        let before: serde_json::Value = serde_json::from_str(&checkpoint).unwrap();
        let after: serde_json::Value =
            serde_json::from_str(&restored.checkpoint_json().unwrap()).unwrap();
        assert_eq!(before, after);
    }
}
