use serde::{Deserialize, Serialize};
use tabletop_core::{Action, DeckList, Expectation, GameOutcome, LoggedEvent, Seq, Snapshot};

use crate::config::PublicEpisodeConfig;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PlayerCommand {
    pub cmd_id: u64,
    pub action: Action,
}

#[derive(Clone, Debug, Serialize)]
pub struct MatchState {
    pub games_to_win: u32,
    pub game_number: u32,
    pub wins: [f64; 2],
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GameSummary {
    pub game_number: u32,
    pub winner_slot: Option<u8>,
    pub reason: tabletop_core::EndReason,
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
    pub events: Vec<ReplayEvent>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ReplayEvent {
    pub wall_ms: u64,
    pub event: LoggedEvent,
}

#[derive(Clone, Debug, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum PlayerFrame {
    Hello {
        slot: usize,
        seat_name: String,
        r#match: MatchState,
        config: PublicEpisodeConfig,
        decklist: DeckList,
    },
    Snapshot {
        game_number: u32,
        state: Box<Snapshot>,
    },
    Events {
        game_number: u32,
        events: Vec<LoggedEvent>,
    },
    Window {
        game_number: u32,
        expectation: Expectation,
        clock_ms_remaining: u64,
        clocks_ms: [u64; 2],
        decision_cap_ms: u64,
    },
    Ack {
        cmd_id: u64,
        seq: Seq,
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
        r#match: MatchState,
        config: PublicEpisodeConfig,
    },
    Snapshot {
        game_number: u32,
        state: Box<Snapshot>,
    },
    Events {
        game_number: u32,
        events: Vec<LoggedEvent>,
    },
    Window {
        game_number: u32,
        expectation: Expectation,
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
    Events {
        game_number: u32,
        events: Vec<LoggedEvent>,
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
    pub events: usize,
}

pub fn reject_error(kind: impl Into<String>, detail: impl Into<String>) -> RejectError {
    RejectError {
        kind: kind.into(),
        detail: detail.into(),
    }
}

pub fn action_error_kind(error: &tabletop_core::ActionError) -> &'static str {
    match error {
        tabletop_core::ActionError::NotYourWindow => "not_your_window",
        tabletop_core::ActionError::InvalidInWindow => "invalid_in_window",
        tabletop_core::ActionError::NotYourCard => "not_your_card",
        tabletop_core::ActionError::UnknownCard => "unknown_card",
        tabletop_core::ActionError::WrongZone => "wrong_zone",
        tabletop_core::ActionError::HiddenZoneAddressing => "hidden_zone_addressing",
        tabletop_core::ActionError::BadMulligan => "bad_mulligan",
        tabletop_core::ActionError::GameIsOver => "game_is_over",
        tabletop_core::ActionError::InvalidArgument(_) => "invalid_argument",
    }
}
