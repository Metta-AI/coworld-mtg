use tabletop_core::{
    Action, CardMove, CardMoveEvent, CardRef, CardView, CounterTarget, CounterTargetRef, Event,
    Expectation, GameOutcome, LoggedEvent, Perspective, PlayerSnapshot, SeatId, Snapshot, ZoneRef,
};

pub fn slot_to_seat(slot: usize, slot_of_seat0: usize) -> SeatId {
    if slot == slot_of_seat0 {
        SeatId(0)
    } else {
        SeatId(1)
    }
}

pub fn seat_to_slot(seat: SeatId, slot_of_seat0: usize) -> usize {
    if seat == SeatId(0) {
        slot_of_seat0
    } else {
        1 - slot_of_seat0
    }
}

pub fn perspective_for_slot(slot: usize, slot_of_seat0: usize) -> Perspective {
    Perspective::Seat(slot_to_seat(slot, slot_of_seat0))
}

pub fn action_to_core(action: Action, slot_of_seat0: usize) -> Action {
    match action {
        Action::MoveCards { moves } => Action::MoveCards {
            moves: moves
                .into_iter()
                .map(|card_move| CardMove {
                    to_seat: slot_to_seat(card_move.to_seat.index(), slot_of_seat0),
                    ..card_move
                })
                .collect(),
        },
        Action::MoveTopOfLibrary {
            count,
            to_seat,
            to_zone,
            position,
            face_down,
        } => Action::MoveTopOfLibrary {
            count,
            to_seat: slot_to_seat(to_seat.index(), slot_of_seat0),
            to_zone,
            position,
            face_down,
        },
        Action::AddCounter {
            target,
            name,
            delta,
        } => Action::AddCounter {
            target: match target {
                CounterTarget::Player { seat } => CounterTarget::Player {
                    seat: slot_to_seat(seat.index(), slot_of_seat0),
                },
                CounterTarget::Card { card } => CounterTarget::Card { card },
            },
            name,
            delta,
        },
        other => other,
    }
}

pub fn snapshot_to_slots(snapshot: Snapshot, slot_of_seat0: usize) -> Snapshot {
    let mut players = snapshot.players;
    players.sort_by_key(|player| seat_to_slot(player.seat, slot_of_seat0));
    Snapshot {
        active: seat_id_to_slot(snapshot.active, slot_of_seat0),
        expectation: expectation_to_slots(snapshot.expectation, slot_of_seat0),
        players: [
            player_snapshot_to_slots(players[0].clone(), slot_of_seat0),
            player_snapshot_to_slots(players[1].clone(), slot_of_seat0),
        ],
        ..snapshot
    }
}

pub fn events_to_slots(events: Vec<LoggedEvent>, slot_of_seat0: usize) -> Vec<LoggedEvent> {
    events
        .into_iter()
        .map(|event| event_to_slots(event, slot_of_seat0))
        .collect()
}

pub fn outcome_to_slots(outcome: GameOutcome, slot_of_seat0: usize) -> GameOutcome {
    let mut final_life = [0, 0];
    for seat in [SeatId(0), SeatId(1)] {
        final_life[seat_to_slot(seat, slot_of_seat0)] = outcome.final_life[seat.index()];
    }
    GameOutcome {
        winner: outcome.winner.map(|seat| seat_id_to_slot(seat, slot_of_seat0)),
        final_life,
        ..outcome
    }
}

fn event_to_slots(event: LoggedEvent, slot_of_seat0: usize) -> LoggedEvent {
    LoggedEvent {
        actor: event.actor.map(|seat| seat_id_to_slot(seat, slot_of_seat0)),
        event: event_payload_to_slots(event.event, slot_of_seat0),
        ..event
    }
}

fn event_payload_to_slots(event: Event, slot_of_seat0: usize) -> Event {
    match event {
        Event::GameStarted {
            players,
            starting_life,
            turn_cap,
            reaction_depth_cap,
        } => {
            let mut by_slot = players.clone();
            for (seat_index, name) in players.into_iter().enumerate() {
                by_slot[seat_to_slot(SeatId(seat_index as u8), slot_of_seat0)] = name;
            }
            Event::GameStarted {
                players: by_slot,
                starting_life,
                turn_cap,
                reaction_depth_cap,
            }
        }
        Event::HandDealt { seat, cards } => Event::HandDealt {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            cards: card_refs_to_slots(cards, slot_of_seat0),
        },
        Event::WindowOpened { expectation } => Event::WindowOpened {
            expectation: expectation_to_slots(expectation, slot_of_seat0),
        },
        Event::Drew { seat, cards } => Event::Drew {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            cards: card_refs_to_slots(cards, slot_of_seat0),
        },
        Event::CardsMoved { moves } => Event::CardsMoved {
            moves: moves
                .into_iter()
                .map(|move_event| card_move_event_to_slots(move_event, slot_of_seat0))
                .collect(),
        },
        Event::AttrSet {
            card,
            zone,
            was_face_down,
            attr,
        } => Event::AttrSet {
            card: card_ref_to_slots(card, slot_of_seat0),
            zone: zone_to_slots(zone, slot_of_seat0),
            was_face_down,
            attr,
        },
        Event::TokenCreated { card, zone } => Event::TokenCreated {
            card: card_ref_to_slots(card, slot_of_seat0),
            zone: zone_to_slots(zone, slot_of_seat0),
        },
        Event::TokenRemoved { card, from } => Event::TokenRemoved {
            card: card_ref_to_slots(card, slot_of_seat0),
            from: zone_to_slots(from, slot_of_seat0),
        },
        Event::CounterChanged {
            target,
            name,
            old,
            new,
            delta,
        } => Event::CounterChanged {
            target: counter_target_ref_to_slots(target, slot_of_seat0),
            name,
            old,
            new,
            delta,
        },
        Event::Shuffled { seat } => Event::Shuffled {
            seat: seat_id_to_slot(seat, slot_of_seat0),
        },
        Event::DieRolled {
            seat,
            sides,
            result,
        } => Event::DieRolled {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            sides,
            result,
        },
        Event::Revealed { seat, cards, to } => Event::Revealed {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            cards: card_refs_to_slots(cards, slot_of_seat0),
            to,
        },
        Event::Said { seat, text } => Event::Said {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            text,
        },
        Event::Pointed { seat, from, to } => Event::Pointed {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            from,
            to,
        },
        Event::Passed { seat } => Event::Passed {
            seat: seat_id_to_slot(seat, slot_of_seat0),
        },
        Event::TurnChanged { turn, active } => Event::TurnChanged {
            turn,
            active: seat_id_to_slot(active, slot_of_seat0),
        },
        Event::MulliganResolved {
            seat,
            kept,
            mulligan_count,
            bottomed,
        } => Event::MulliganResolved {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            kept,
            mulligan_count,
            bottomed,
        },
        Event::GameEnded { outcome } => Event::GameEnded {
            outcome: outcome_to_slots(outcome, slot_of_seat0),
        },
        other => other,
    }
}

fn player_snapshot_to_slots(player: PlayerSnapshot, slot_of_seat0: usize) -> PlayerSnapshot {
    PlayerSnapshot {
        seat: seat_id_to_slot(player.seat, slot_of_seat0),
        hand: card_refs_to_slots(player.hand, slot_of_seat0),
        battlefield: card_refs_to_slots(player.battlefield, slot_of_seat0),
        graveyard: card_refs_to_slots(player.graveyard, slot_of_seat0),
        exile: card_refs_to_slots(player.exile, slot_of_seat0),
        ..player
    }
}

fn card_move_event_to_slots(
    move_event: CardMoveEvent,
    slot_of_seat0: usize,
) -> CardMoveEvent {
    CardMoveEvent {
        card: card_ref_to_slots(move_event.card, slot_of_seat0),
        from: zone_to_slots(move_event.from, slot_of_seat0),
        to: zone_to_slots(move_event.to, slot_of_seat0),
        ..move_event
    }
}

fn counter_target_ref_to_slots(
    target: CounterTargetRef,
    slot_of_seat0: usize,
) -> CounterTargetRef {
    match target {
        CounterTargetRef::Card { card, zone } => CounterTargetRef::Card {
            card: card_ref_to_slots(card, slot_of_seat0),
            zone: zone_to_slots(zone, slot_of_seat0),
        },
        CounterTargetRef::Player { seat } => CounterTargetRef::Player {
            seat: seat_id_to_slot(seat, slot_of_seat0),
        },
    }
}

fn expectation_to_slots(expectation: Expectation, slot_of_seat0: usize) -> Expectation {
    match expectation {
        Expectation::Mulligan {
            seat,
            keeping_hand_of,
            must_bottom,
        } => Expectation::Mulligan {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            keeping_hand_of,
            must_bottom,
        },
        Expectation::MainWindow { seat } => Expectation::MainWindow {
            seat: seat_id_to_slot(seat, slot_of_seat0),
        },
        Expectation::ReactionWindow { seat, depth } => Expectation::ReactionWindow {
            seat: seat_id_to_slot(seat, slot_of_seat0),
            depth,
        },
        Expectation::GameOver { outcome } => Expectation::GameOver {
            outcome: outcome_to_slots(outcome, slot_of_seat0),
        },
    }
}

fn card_refs_to_slots(cards: Vec<CardRef>, slot_of_seat0: usize) -> Vec<CardRef> {
    cards
        .into_iter()
        .map(|card| card_ref_to_slots(card, slot_of_seat0))
        .collect()
}

fn card_ref_to_slots(card: CardRef, slot_of_seat0: usize) -> CardRef {
    match card {
        CardRef::Known(view) => CardRef::Known(card_view_to_slots(view, slot_of_seat0)),
        CardRef::Hidden { id } => CardRef::Hidden { id },
    }
}

fn card_view_to_slots(view: CardView, slot_of_seat0: usize) -> CardView {
    CardView {
        owner: seat_id_to_slot(view.owner, slot_of_seat0),
        controller: seat_id_to_slot(view.controller, slot_of_seat0),
        ..view
    }
}

fn zone_to_slots(zone: ZoneRef, slot_of_seat0: usize) -> ZoneRef {
    ZoneRef {
        seat: seat_id_to_slot(zone.seat, slot_of_seat0),
        zone: zone.zone,
    }
}

fn seat_id_to_slot(seat: SeatId, slot_of_seat0: usize) -> SeatId {
    SeatId(seat_to_slot(seat, slot_of_seat0) as u8)
}
