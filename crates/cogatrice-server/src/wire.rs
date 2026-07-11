use phase_bridge::{DeckList, GameAction, GameEvent, PhaseOutcome, ViewerSnapshot};
use serde::{Deserialize, Serialize};

use crate::config::PublicEpisodeConfig;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PlayerCommand {
    pub cmd_id: u64,
    pub action: GameAction,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MatchState {
    pub games_to_win: u32,
    pub game_number: u32,
    pub wins: [f64; 2],
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GameSummary {
    pub game_number: u32,
    pub winner_slot: Option<u8>,
    pub reason: String,
    pub turns: u32,
    pub final_life: [i32; 2],
    pub seed: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Results {
    pub scores: [f64; 2],
    pub games: Vec<GameSummary>,
    pub seed: u64,
    pub policy_names: [String; 2],
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Replay {
    pub version: u32,
    pub config: PublicEpisodeConfig,
    pub games: Vec<ReplayGame>,
    pub results: Results,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ReplayGame {
    pub game_number: u32,
    pub slot_of_seat0: usize,
    pub steps: Vec<ReplayStep>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ReplayStep {
    pub wall_ms: u64,
    pub actor_slot: Option<u8>,
    pub action: Option<GameAction>,
    pub state: ViewerSnapshot,
    pub events: Vec<GameEvent>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GameOutcome {
    pub winner_slot: Option<u8>,
    pub final_life: [i32; 2],
    pub turns: u32,
    pub reason: String,
}

impl GameOutcome {
    pub fn from_phase(outcome: PhaseOutcome, slot_of_seat0: usize, reason: &str) -> Self {
        let mut final_life = [0, 0];
        final_life[slot_of_seat0] = outcome.final_life[0];
        final_life[1 - slot_of_seat0] = outcome.final_life[1];
        Self {
            winner_slot: outcome
                .winner
                .map(|seat| seat_to_slot(seat, slot_of_seat0) as u8),
            final_life,
            turns: outcome.turns,
            reason: reason.to_owned(),
        }
    }
}

#[derive(Clone, Debug, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum PlayerFrame {
    Hello {
        slot: usize,
        seat: u8,
        seat_name: String,
        player_names: [String; 2],
        r#match: MatchState,
        config: Box<PublicEpisodeConfig>,
        decklist: DeckList,
    },
    State {
        game_number: u32,
        state: Box<ViewerSnapshot>,
        events: Vec<GameEvent>,
        clocks_ms: [u64; 2],
        decision_cap_ms: u64,
    },
    Ack {
        cmd_id: u64,
        turn: u32,
    },
    Reject {
        cmd_id: u64,
        error: RejectError,
    },
    GameEnd {
        game_number: u32,
        outcome: GameOutcome,
        wins: [f64; 2],
    },
    MatchEnd {
        scores: [f64; 2],
        games: Vec<GameSummary>,
    },
}

#[derive(Clone, Debug, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum GlobalFrame {
    Hello {
        player_names: [String; 2],
        r#match: MatchState,
        config: PublicEpisodeConfig,
    },
    State {
        game_number: u32,
        state: Box<ViewerSnapshot>,
        events: Vec<GameEvent>,
        clocks_ms: [u64; 2],
    },
    GameEnd {
        game_number: u32,
        outcome: GameOutcome,
        wins: [f64; 2],
    },
    MatchEnd {
        scores: [f64; 2],
        games: Vec<GameSummary>,
    },
}

#[derive(Clone, Debug, Serialize)]
pub struct RejectError {
    pub kind: String,
    pub detail: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ReplayFrame {
    ReplayMeta {
        config: Box<PublicEpisodeConfig>,
        results: Box<Results>,
        games: Vec<ReplayGameSummary>,
    },
    State {
        game_number: u32,
        step: Box<ReplayStep>,
    },
    GameEnd {
        game_number: u32,
        outcome: GameOutcome,
        wins: [f64; 2],
    },
    MatchEnd {
        scores: [f64; 2],
        games: Vec<GameSummary>,
    },
}

#[derive(Clone, Debug, Serialize)]
pub struct ReplayGameSummary {
    pub game_number: u32,
    pub slot_of_seat0: usize,
    pub steps: usize,
}

pub fn reject_error(kind: impl Into<String>, detail: impl Into<String>) -> RejectError {
    RejectError {
        kind: kind.into(),
        detail: detail.into(),
    }
}

pub fn seat_to_slot(seat: u8, slot_of_seat0: usize) -> usize {
    if seat == 0 {
        slot_of_seat0
    } else {
        1 - slot_of_seat0
    }
}

pub fn slot_to_seat(slot: usize, slot_of_seat0: usize) -> u8 {
    if slot == slot_of_seat0 {
        0
    } else {
        1
    }
}
