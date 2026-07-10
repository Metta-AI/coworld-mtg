use crate::actions::{MovePosition, RevealTo};
use crate::cards::{CardAttr, CardRef};
use crate::expectation::{Expectation, GameOutcome};
use crate::ids::{CardId, SeatId, Seq};
use crate::zones::{Phase, ZoneRef};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct LoggedEvent {
    pub seq: Seq,
    pub turn: u32,
    pub phase: Phase,
    pub actor: Option<SeatId>,
    pub event: Event,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Event {
    GameStarted {
        players: [String; 2],
        starting_life: i32,
        turn_cap: u32,
        reaction_depth_cap: u8,
    },
    HandDealt {
        seat: SeatId,
        cards: Vec<CardRef>,
    },
    WindowOpened {
        expectation: Expectation,
    },
    Drew {
        seat: SeatId,
        cards: Vec<CardRef>,
    },
    CardsMoved {
        moves: Vec<CardMoveEvent>,
    },
    AttrSet {
        card: CardRef,
        zone: ZoneRef,
        was_face_down: bool,
        attr: CardAttr,
    },
    TokenCreated {
        card: CardRef,
        zone: ZoneRef,
    },
    TokenRemoved {
        card: CardRef,
        from: ZoneRef,
    },
    CounterChanged {
        target: CounterTargetRef,
        name: String,
        old: i32,
        new: i32,
        delta: i32,
    },
    Shuffled {
        seat: SeatId,
    },
    DieRolled {
        seat: SeatId,
        sides: u32,
        result: u32,
    },
    Revealed {
        seat: SeatId,
        cards: Vec<CardRef>,
        to: RevealTo,
    },
    Said {
        seat: SeatId,
        text: String,
    },
    Pointed {
        seat: SeatId,
        from: CardId,
        to: Option<CardId>,
    },
    Passed {
        seat: SeatId,
    },
    PhaseChanged {
        phase: Phase,
    },
    TurnChanged {
        turn: u32,
        active: SeatId,
    },
    MulliganResolved {
        seat: SeatId,
        kept: bool,
        mulligan_count: u8,
        bottomed: u8,
    },
    GameEnded {
        outcome: GameOutcome,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CardMoveEvent {
    pub card: CardRef,
    pub from: ZoneRef,
    pub to: ZoneRef,
    pub was_face_down: bool,
    pub position: MovePosition,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
#[allow(clippy::large_enum_variant)]
pub enum CounterTargetRef {
    Card { card: CardRef, zone: ZoneRef },
    Player { seat: SeatId },
}
