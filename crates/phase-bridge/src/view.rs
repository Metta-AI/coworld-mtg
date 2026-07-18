use phase_engine::game::combat::AttackTarget;
use phase_engine::types::actions::GameAction;
use phase_engine::types::game_state::AutoPassMode;
use phase_engine::types::mana::{ManaCost, ManaPool};
use phase_engine::types::phase::PhaseStop;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;

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
    pub combat: Option<CombatView>,
    #[serde(default)]
    pub preference_player: Option<u8>,
    #[serde(default)]
    pub auto_pass_recommended: bool,
    #[serde(default)]
    pub auto_pass_mode: Option<AutoPassMode>,
    #[serde(default)]
    pub phase_stops: Vec<PhaseStop>,
    pub legal_actions: Vec<GameAction>,
    pub spell_costs: BTreeMap<String, ManaCost>,
    pub legal_actions_by_object: BTreeMap<String, Vec<GameAction>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub phase_client: Option<PhaseClientSnapshot>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PhaseClientSnapshot {
    pub state: Value,
    pub derived: Value,
    pub legal_actions: Vec<GameAction>,
    pub auto_pass_recommended: bool,
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
    #[serde(default)]
    pub blocked: bool,
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

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CombatView {
    pub attackers: Vec<CombatAttackerView>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CombatAttackerView {
    pub object_id: u64,
    pub defending_player: u8,
    #[serde(default)]
    pub attack_target: AttackTargetView,
    #[serde(default)]
    pub blocked: bool,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum AttackTargetView {
    Player(u8),
    Planeswalker(u64),
    Battle(u64),
}

impl Default for AttackTargetView {
    fn default() -> Self {
        Self::Player(0)
    }
}

impl From<AttackTarget> for AttackTargetView {
    fn from(target: AttackTarget) -> Self {
        match target {
            AttackTarget::Player(player) => Self::Player(player.0),
            AttackTarget::Planeswalker(object) => Self::Planeswalker(object.0),
            AttackTarget::Battle(object) => Self::Battle(object.0),
        }
    }
}
