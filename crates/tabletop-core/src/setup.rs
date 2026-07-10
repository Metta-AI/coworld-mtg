use serde::{Deserialize, Serialize};

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

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PlayerSetup {
    pub name: String,
    pub deck: DeckList,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct GameSetup {
    pub seed: u64,
    pub players: [PlayerSetup; 2],
    pub starting_life: i32,
    pub turn_cap: u32,
    pub reaction_depth_cap: u8,
}

impl GameSetup {
    pub const DEFAULT_STARTING_LIFE: i32 = 20;
    pub const DEFAULT_TURN_CAP: u32 = 25;
    pub const DEFAULT_REACTION_DEPTH_CAP: u8 = 4;

    pub fn normalized_starting_life(&self) -> i32 {
        if self.starting_life > 0 {
            self.starting_life
        } else {
            Self::DEFAULT_STARTING_LIFE
        }
    }

    pub fn normalized_turn_cap(&self) -> u32 {
        if self.turn_cap > 0 {
            self.turn_cap
        } else {
            Self::DEFAULT_TURN_CAP
        }
    }

    pub fn normalized_reaction_depth_cap(&self) -> u8 {
        if self.reaction_depth_cap > 0 {
            self.reaction_depth_cap
        } else {
            Self::DEFAULT_REACTION_DEPTH_CAP
        }
    }
}
