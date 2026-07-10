use crate::cards::CardAttr;
use crate::ids::{CardId, SeatId};
use crate::setup::CardSpec;
use crate::zones::ZoneKind;
use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Action {
    Draw {
        count: u32,
    },
    MoveCards {
        moves: Vec<CardMove>,
    },
    MoveTopOfLibrary {
        count: u32,
        to_seat: SeatId,
        to_zone: ZoneKind,
        position: MovePosition,
        face_down: bool,
    },
    SetCardAttr {
        card: CardId,
        attr: CardAttr,
    },
    CreateToken {
        spec: CardSpec,
        x: i16,
        y: i16,
    },
    AddCounter {
        target: CounterTarget,
        name: String,
        delta: i32,
    },
    Shuffle,
    RollDie {
        sides: u32,
    },
    Reveal {
        cards: Vec<CardId>,
        to: RevealTo,
    },
    Say {
        text: String,
    },
    Point {
        from: CardId,
        to: Option<CardId>,
    },
    Pass,
    NextPhase,
    NextTurn,
    MulliganKeep {
        bottom: Vec<CardId>,
    },
    MulliganAgain,
    Concede,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CardMove {
    pub card: CardId,
    pub to_seat: SeatId,
    pub to_zone: ZoneKind,
    pub position: MovePosition,
    pub face_down: Option<bool>,
    pub tapped: Option<bool>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MovePosition {
    Top,
    Bottom,
    Index(u32),
    Battlefield { x: i16, y: i16 },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum CounterTarget {
    Card { card: CardId },
    Player { seat: SeatId },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RevealTo {
    Opponent,
    All,
}

#[derive(Clone, Debug, PartialEq, Eq, Error)]
pub enum ActionError {
    #[error("not your window")]
    NotYourWindow,
    #[error("invalid in window")]
    InvalidInWindow,
    #[error("not your card")]
    NotYourCard,
    #[error("unknown card")]
    UnknownCard,
    #[error("wrong zone")]
    WrongZone,
    #[error("hidden zone addressing")]
    HiddenZoneAddressing,
    #[error("bad mulligan")]
    BadMulligan,
    #[error("game is over")]
    GameIsOver,
    #[error("invalid argument: {0}")]
    InvalidArgument(String),
}
