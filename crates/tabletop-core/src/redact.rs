use crate::actions::RevealTo;
use crate::cards::{CardRef, CardView};
use crate::events::{CardMoveEvent, CounterTargetRef, Event, LoggedEvent};
use crate::ids::{CardId, SeatId, Seq};
use crate::zones::{Phase, ZoneKind, ZoneRef};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Perspective {
    Seat(SeatId),
    Global,
    Full,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Snapshot {
    pub seq: Seq,
    pub turn: u32,
    pub phase: Phase,
    pub active: SeatId,
    pub expectation: crate::expectation::Expectation,
    pub players: [PlayerSnapshot; 2],
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct PlayerSnapshot {
    pub seat: SeatId,
    pub name: String,
    pub counters: BTreeMap<String, i32>,
    pub mulligan_count: u8,
    pub library_count: u32,
    pub hand: Vec<CardRef>,
    pub battlefield: Vec<CardRef>,
    pub graveyard: Vec<CardRef>,
    pub exile: Vec<CardRef>,
    pub arrows: Vec<Arrow>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Arrow {
    pub from: CardId,
    pub to: Option<CardId>,
}

impl LoggedEvent {
    pub fn redact(&self, perspective: Perspective) -> Option<LoggedEvent> {
        Some(LoggedEvent {
            seq: self.seq,
            turn: self.turn,
            phase: self.phase,
            actor: self.actor,
            event: redact_event(&self.event, perspective),
        })
    }
}

pub(crate) fn card_ref_for_zone(
    card: &CardView,
    zone: ZoneRef,
    perspective: Perspective,
) -> CardRef {
    if card_visible_in_zone(card, zone, perspective) {
        CardRef::Known(card.clone())
    } else {
        CardRef::Hidden { id: card.id }
    }
}

pub(crate) fn hidden_card(card: &CardView) -> CardRef {
    CardRef::Hidden { id: card.id }
}

fn redact_event(event: &Event, perspective: Perspective) -> Event {
    match event {
        Event::GameStarted {
            players,
            starting_life,
            turn_cap,
            reaction_depth_cap,
        } => Event::GameStarted {
            players: players.clone(),
            starting_life: *starting_life,
            turn_cap: *turn_cap,
            reaction_depth_cap: *reaction_depth_cap,
        },
        Event::HandDealt { seat, cards } => Event::HandDealt {
            seat: *seat,
            cards: cards
                .iter()
                .map(|card| redact_drawn_or_dealt(*seat, card, perspective))
                .collect(),
        },
        Event::WindowOpened { expectation } => Event::WindowOpened {
            expectation: expectation.clone(),
        },
        Event::Drew { seat, cards } => Event::Drew {
            seat: *seat,
            cards: cards
                .iter()
                .map(|card| redact_drawn_or_dealt(*seat, card, perspective))
                .collect(),
        },
        Event::CardsMoved { moves } => Event::CardsMoved {
            moves: moves
                .iter()
                .map(|move_event| redact_move_event(move_event, perspective))
                .collect(),
        },
        Event::AttrSet {
            card,
            zone,
            was_face_down,
            attr,
        } => Event::AttrSet {
            card: redact_card_ref_for_transition(
                card,
                *zone,
                *was_face_down,
                *zone,
                post_face_down(card),
                perspective,
            ),
            zone: *zone,
            was_face_down: *was_face_down,
            attr: attr.clone(),
        },
        Event::TokenCreated { card, zone } => Event::TokenCreated {
            card: redact_card_ref_for_zone(card, *zone, perspective),
            zone: *zone,
        },
        Event::TokenRemoved { card, from } => Event::TokenRemoved {
            card: redact_card_ref_for_zone(card, *from, perspective),
            from: *from,
        },
        Event::CounterChanged {
            target,
            name,
            old,
            new,
            delta,
        } => Event::CounterChanged {
            target: redact_counter_target(target, perspective),
            name: name.clone(),
            old: *old,
            new: *new,
            delta: *delta,
        },
        Event::Shuffled { seat } => Event::Shuffled { seat: *seat },
        Event::DieRolled {
            seat,
            sides,
            result,
        } => Event::DieRolled {
            seat: *seat,
            sides: *sides,
            result: *result,
        },
        Event::Revealed { seat, cards, to } => Event::Revealed {
            seat: *seat,
            cards: cards
                .iter()
                .map(|card| redact_revealed(*seat, *to, card, perspective))
                .collect(),
            to: *to,
        },
        Event::Said { seat, text } => Event::Said {
            seat: *seat,
            text: text.clone(),
        },
        Event::Pointed { seat, from, to } => Event::Pointed {
            seat: *seat,
            from: *from,
            to: *to,
        },
        Event::Passed { seat } => Event::Passed { seat: *seat },
        Event::PhaseChanged { phase } => Event::PhaseChanged { phase: *phase },
        Event::TurnChanged { turn, active } => Event::TurnChanged {
            turn: *turn,
            active: *active,
        },
        Event::MulliganResolved {
            seat,
            kept,
            mulligan_count,
            bottomed,
        } => Event::MulliganResolved {
            seat: *seat,
            kept: *kept,
            mulligan_count: *mulligan_count,
            bottomed: *bottomed,
        },
        Event::GameEnded { outcome } => Event::GameEnded {
            outcome: outcome.clone(),
        },
    }
}

fn redact_drawn_or_dealt(seat: SeatId, card: &CardRef, perspective: Perspective) -> CardRef {
    match (card, perspective) {
        (CardRef::Known(view), Perspective::Full) => CardRef::Known(view.clone()),
        (CardRef::Known(view), Perspective::Seat(viewer)) if viewer == seat => {
            CardRef::Known(view.clone())
        }
        (CardRef::Known(view), _) => hidden_card(view),
        (CardRef::Hidden { id }, _) => CardRef::Hidden { id: *id },
    }
}

fn redact_revealed(
    seat: SeatId,
    to: RevealTo,
    card: &CardRef,
    perspective: Perspective,
) -> CardRef {
    match (card, perspective) {
        (CardRef::Known(view), Perspective::Full) => CardRef::Known(view.clone()),
        (CardRef::Known(view), Perspective::Seat(viewer)) if viewer == seat => {
            CardRef::Known(view.clone())
        }
        (CardRef::Known(view), Perspective::Seat(viewer))
            if matches!(to, RevealTo::Opponent) && viewer == seat.opponent() =>
        {
            CardRef::Known(view.clone())
        }
        (CardRef::Known(view), Perspective::Seat(_)) if matches!(to, RevealTo::All) => {
            CardRef::Known(view.clone())
        }
        (CardRef::Known(view), Perspective::Global) if matches!(to, RevealTo::All) => {
            CardRef::Known(view.clone())
        }
        (CardRef::Known(view), _) => hidden_card(view),
        (CardRef::Hidden { id }, _) => CardRef::Hidden { id: *id },
    }
}

fn redact_move_event(move_event: &CardMoveEvent, perspective: Perspective) -> CardMoveEvent {
    CardMoveEvent {
        card: redact_card_ref_for_transition(
            &move_event.card,
            move_event.from,
            move_event.was_face_down,
            move_event.to,
            post_face_down(&move_event.card),
            perspective,
        ),
        from: move_event.from,
        to: move_event.to,
        was_face_down: move_event.was_face_down,
        position: move_event.position.clone(),
    }
}

fn redact_counter_target(target: &CounterTargetRef, perspective: Perspective) -> CounterTargetRef {
    match target {
        CounterTargetRef::Card { card, zone } => CounterTargetRef::Card {
            card: redact_card_ref_for_zone(card, *zone, perspective),
            zone: *zone,
        },
        CounterTargetRef::Player { seat } => CounterTargetRef::Player { seat: *seat },
    }
}

fn redact_card_ref_for_zone(card: &CardRef, zone: ZoneRef, perspective: Perspective) -> CardRef {
    match card {
        CardRef::Known(view) => card_ref_for_zone(view, zone, perspective),
        CardRef::Hidden { id } => CardRef::Hidden { id: *id },
    }
}

fn redact_card_ref_for_transition(
    card: &CardRef,
    from: ZoneRef,
    was_face_down: bool,
    to: ZoneRef,
    is_face_down: bool,
    perspective: Perspective,
) -> CardRef {
    match card {
        CardRef::Known(view) => {
            if card_visible_in_state(view, from, was_face_down, perspective)
                || card_visible_in_state(view, to, is_face_down, perspective)
            {
                CardRef::Known(view.clone())
            } else {
                hidden_card(view)
            }
        }
        CardRef::Hidden { id } => CardRef::Hidden { id: *id },
    }
}

fn post_face_down(card: &CardRef) -> bool {
    match card {
        CardRef::Known(view) => view.face_down,
        CardRef::Hidden { .. } => true,
    }
}

fn card_visible_in_zone(card: &CardView, zone: ZoneRef, perspective: Perspective) -> bool {
    card_visible_in_state(card, zone, card.face_down, perspective)
}

fn card_visible_in_state(
    _card: &CardView,
    zone: ZoneRef,
    face_down: bool,
    perspective: Perspective,
) -> bool {
    match perspective {
        Perspective::Full => true,
        Perspective::Global => zone.zone.is_public() && !face_down,
        Perspective::Seat(seat) => {
            if zone.seat == seat && zone.zone != ZoneKind::Library {
                true
            } else {
                zone.zone.is_public() && !face_down
            }
        }
    }
}
