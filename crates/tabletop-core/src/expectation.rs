use crate::ids::SeatId;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Expectation {
    Mulligan {
        seat: SeatId,
        keeping_hand_of: u8,
        must_bottom: u8,
    },
    MainWindow {
        seat: SeatId,
    },
    ReactionWindow {
        seat: SeatId,
        depth: u8,
    },
    GameOver {
        outcome: GameOutcome,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct GameOutcome {
    pub winner: Option<SeatId>,
    pub reason: EndReason,
    pub final_life: [i32; 2],
    pub turns: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EndReason {
    Concession,
    LifeZero,
    DrewFromEmptyLibrary,
    TurnCap,
    ClockFlag,
}
