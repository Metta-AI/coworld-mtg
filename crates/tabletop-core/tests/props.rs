use proptest::prelude::*;
use serde_json::Value;
use std::collections::BTreeSet;
use tabletop_core::*;

fn card(name: &str) -> CardSpec {
    CardSpec {
        name: name.to_owned(),
        type_line: "Creature".to_owned(),
        mana_cost: Some("{1}".to_owned()),
        power_toughness: Some("2/2".to_owned()),
        oracle_text: String::new(),
        art_id: None,
    }
}

fn setup(seed: u64, turn_cap: u32, reaction_depth_cap: u8) -> GameSetup {
    let deck_a = DeckList {
        name: "A".to_owned(),
        cards: (0..16)
            .map(|index| card(&format!("A Hidden Name {index}")))
            .collect(),
    };
    let deck_b = DeckList {
        name: "B".to_owned(),
        cards: (0..16)
            .map(|index| card(&format!("B Hidden Name {index}")))
            .collect(),
    };
    GameSetup {
        seed,
        players: [
            PlayerSetup {
                name: "Alice".to_owned(),
                deck: deck_a,
            },
            PlayerSetup {
                name: "Bob".to_owned(),
                deck: deck_b,
            },
        ],
        starting_life: 20,
        turn_cap,
        reaction_depth_cap,
    }
}

fn hand_ids(game: &Game, seat: SeatId) -> Vec<CardId> {
    game.snapshot(Perspective::Seat(seat)).players[seat.index()]
        .hand
        .iter()
        .filter_map(|card| match card {
            CardRef::Known(view) => Some(view.id),
            CardRef::Hidden { .. } => None,
        })
        .collect()
}

fn keep_both(game: &mut Game) {
    game.submit(SeatId(0), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
    game.submit(SeatId(1), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
}

fn keep_or_mulligan(game: &mut Game, seat: SeatId, choice: u8) {
    let mulligan_count =
        game.snapshot(Perspective::Seat(seat)).players[seat.index()].mulligan_count;
    if choice.is_multiple_of(9) && mulligan_count < 2 {
        game.submit(seat, Action::MulliganAgain).unwrap();
        return;
    }
    let must_bottom = match game.expectation() {
        Expectation::Mulligan { must_bottom, .. } => usize::from(*must_bottom),
        _ => 0,
    };
    let bottom = hand_ids(game, seat).into_iter().take(must_bottom).collect();
    game.submit(seat, Action::MulliganKeep { bottom }).unwrap();
}

fn legal_step(game: &mut Game, choice: u8) {
    match game.expectation().clone() {
        Expectation::Mulligan { seat, .. } => keep_or_mulligan(game, seat, choice),
        Expectation::MainWindow { seat } => main_step(game, seat, choice),
        Expectation::ReactionWindow { seat, depth } => {
            if choice.is_multiple_of(4) && depth < 2 {
                game.submit(
                    seat,
                    Action::Say {
                        text: format!("response {choice}"),
                    },
                )
                .unwrap();
            } else {
                game.submit(seat, Action::Pass).unwrap();
            }
        }
        Expectation::GameOver { .. } => {}
    }
}

fn main_step(game: &mut Game, seat: SeatId, choice: u8) {
    match choice % 8 {
        0 => {
            game.submit(seat, Action::Pass).unwrap();
        }
        1 => {
            if game.snapshot(Perspective::Full).phase == Phase::End {
                game.submit(seat, Action::NextTurn).unwrap();
            } else {
                game.submit(seat, Action::NextPhase).unwrap();
            }
        }
        2 => {
            game.submit(seat, Action::RollDie { sides: 6 }).unwrap();
        }
        3 => {
            game.submit(
                seat,
                Action::Say {
                    text: format!("line {choice}"),
                },
            )
            .unwrap();
        }
        4 => {
            game.submit(seat, Action::Shuffle).unwrap();
        }
        5 => {
            let hand = hand_ids(game, seat);
            if let Some(card) = hand.first().copied() {
                game.submit(
                    seat,
                    Action::MoveCards {
                        moves: vec![CardMove {
                            card,
                            to_seat: seat,
                            to_zone: ZoneKind::Battlefield,
                            position: MovePosition::Battlefield {
                                x: i16::from(choice),
                                y: 0,
                            },
                            face_down: Some(choice.is_multiple_of(2)),
                            tapped: Some(false),
                        }],
                    },
                )
                .unwrap();
            } else {
                game.submit(seat, Action::Pass).unwrap();
            }
        }
        6 => {
            if game.snapshot(Perspective::Full).players[seat.index()].library_count > 0 {
                game.submit(seat, Action::Draw { count: 1 }).unwrap();
            } else if game.snapshot(Perspective::Full).phase == Phase::End {
                game.submit(seat, Action::NextTurn).unwrap();
            } else {
                game.submit(seat, Action::NextPhase).unwrap();
            }
        }
        _ => {
            game.submit(
                seat,
                Action::AddCounter {
                    target: CounterTarget::Player {
                        seat: seat.opponent(),
                    },
                    name: "life".to_owned(),
                    delta: -1,
                },
            )
            .unwrap();
        }
    }
}

fn drive(seed: u64, choices: &[u8]) -> Game {
    let (mut game, _) = Game::new(setup(seed, 4, 2));
    for choice in choices {
        if game.outcome().is_some() {
            break;
        }
        legal_step(&mut game, *choice);
    }
    game
}

fn hidden_ids_for(snapshot: &Snapshot, viewer: SeatId) -> BTreeSet<u64> {
    let mut hidden = BTreeSet::new();
    let opponent = viewer.opponent().index();
    for card in &snapshot.players[opponent].hand {
        hidden.insert(card_id_as_u64(card));
    }
    for player in &snapshot.players {
        for card in &player.battlefield {
            if let CardRef::Known(view) = card {
                if view.face_down && view.controller != viewer {
                    hidden.insert(u64::from(view.id.0));
                }
            }
        }
    }
    hidden
}

fn card_id_as_u64(card: &CardRef) -> u64 {
    match card {
        CardRef::Known(view) => u64::from(view.id.0),
        CardRef::Hidden { id } => u64::from(id.0),
    }
}

fn assert_hidden_ids_have_no_name(value: &Value, hidden_ids: &BTreeSet<u64>) {
    match value {
        Value::Object(map) => {
            if let Some(id) = map.get("id").and_then(Value::as_u64) {
                if hidden_ids.contains(&id) {
                    assert!(!contains_key_named_name(value));
                }
            }
            for child in map.values() {
                assert_hidden_ids_have_no_name(child, hidden_ids);
            }
        }
        Value::Array(values) => {
            for child in values {
                assert_hidden_ids_have_no_name(child, hidden_ids);
            }
        }
        _ => {}
    }
}

fn contains_key_named_name(value: &Value) -> bool {
    match value {
        Value::Object(map) => map.contains_key("name") || map.values().any(contains_key_named_name),
        Value::Array(values) => values.iter().any(contains_key_named_name),
        _ => false,
    }
}

fn max_reaction_depth(log: &[LoggedEvent]) -> u8 {
    log.iter()
        .filter_map(|event| match &event.event {
            Event::WindowOpened {
                expectation: Expectation::ReactionWindow { depth, .. },
            } => Some(*depth),
            _ => None,
        })
        .max()
        .unwrap_or(0)
}

fn first_moved_card_ref(event: LoggedEvent) -> CardRef {
    let Event::CardsMoved { moves } = event.event else {
        panic!("expected CardsMoved");
    };
    moves[0].card.clone()
}

fn attr_set_card_ref(event: LoggedEvent) -> CardRef {
    let Event::AttrSet { card, .. } = event.event else {
        panic!("expected AttrSet");
    };
    card
}

fn deck_index_from_name(name: &str) -> u32 {
    name.rsplit(' ').next().unwrap().parse().unwrap()
}

proptest! {
    #[test]
    fn deterministic_logs(seed in any::<u64>(), choices in proptest::collection::vec(any::<u8>(), 0..80)) {
        let first = drive(seed, &choices);
        let second = drive(seed, &choices);
        let first_json = serde_json::to_vec(first.log()).unwrap();
        let second_json = serde_json::to_vec(second.log()).unwrap();
        prop_assert_eq!(first_json, second_json);
    }

    #[test]
    fn redaction_does_not_leak_hidden_identity(seed in any::<u64>(), choices in proptest::collection::vec(any::<u8>(), 0..60)) {
        let game = drive(seed, &choices);
        for viewer in [SeatId(0), SeatId(1)] {
            let full = game.snapshot(Perspective::Full);
            let hidden = hidden_ids_for(&full, viewer);
            let snapshot = serde_json::to_value(game.snapshot(Perspective::Seat(viewer))).unwrap();
            assert_hidden_ids_have_no_name(&snapshot, &hidden);
            for event in game.log() {
                let redacted = event.redact(Perspective::Seat(viewer)).unwrap();
                let value = serde_json::to_value(redacted).unwrap();
                assert_hidden_ids_have_no_name(&value, &hidden);
            }
        }
    }

    #[test]
    fn turn_cap_and_reaction_depth_bound_execution(seed in any::<u64>(), turn_cap in 1_u32..6, reaction_cap in 1_u8..4) {
        let (mut game, _) = Game::new(setup(seed, turn_cap, reaction_cap));
        while matches!(game.expectation(), Expectation::Mulligan { .. }) {
            let seat = match game.expectation() {
                Expectation::Mulligan { seat, .. } => *seat,
                _ => unreachable!(),
            };
            game.submit(seat, Action::MulliganKeep { bottom: vec![] }).unwrap();
        }

        let mut response_budget = 0_u8;
        while game.outcome().is_none() {
            match game.expectation().clone() {
                Expectation::MainWindow { seat } => {
                    response_budget = reaction_cap;
                    if game.snapshot(Perspective::Full).phase == Phase::End {
                        game.submit(seat, Action::NextTurn).unwrap();
                    } else {
                        game.submit(seat, Action::NextPhase).unwrap();
                    }
                }
                Expectation::ReactionWindow { seat, depth } => {
                    if response_budget > 0 && depth < reaction_cap {
                        response_budget -= 1;
                        game.submit(
                            seat,
                            Action::Say {
                                text: "bounded response".to_owned(),
                            },
                        ).unwrap();
                    } else {
                        game.submit(seat, Action::Pass).unwrap();
                    }
                }
                Expectation::GameOver { .. } => break,
                Expectation::Mulligan { .. } => unreachable!(),
            }
            prop_assert!(max_reaction_depth(game.log()) <= reaction_cap);
        }
        prop_assert_eq!(game.outcome().unwrap().reason, EndReason::TurnCap);
        prop_assert!(game.outcome().unwrap().turns <= turn_cap);
    }
}

#[test]
fn different_seeds_produce_different_opening_logs() {
    let (first, _) = Game::new(setup(1, 4, 2));
    let (second, _) = Game::new(setup(2, 4, 2));
    let first_json = serde_json::to_vec(first.log()).unwrap();
    let second_json = serde_json::to_vec(second.log()).unwrap();
    assert_ne!(first_json, second_json);
}

#[test]
fn bounced_battlefield_card_stays_known_in_global_move_event() {
    let (mut game, _) = Game::new(setup(3, 4, 2));
    keep_both(&mut game);
    let card = hand_ids(&game, SeatId(0))[0];
    game.submit(
        SeatId(0),
        Action::MoveCards {
            moves: vec![CardMove {
                card,
                to_seat: SeatId(0),
                to_zone: ZoneKind::Battlefield,
                position: MovePosition::Battlefield { x: 0, y: 0 },
                face_down: Some(false),
                tapped: None,
            }],
        },
    )
    .unwrap();

    let events = game
        .submit(
            SeatId(0),
            Action::MoveCards {
                moves: vec![CardMove {
                    card,
                    to_seat: SeatId(0),
                    to_zone: ZoneKind::Hand,
                    position: MovePosition::Bottom,
                    face_down: None,
                    tapped: None,
                }],
            },
        )
        .unwrap();
    let redacted = events[0].redact(Perspective::Global).unwrap();
    assert!(matches!(first_moved_card_ref(redacted), CardRef::Known(_)));
}

#[test]
fn hand_to_library_move_is_hidden_from_opponent() {
    let (mut game, _) = Game::new(setup(4, 4, 2));
    keep_both(&mut game);
    let card = hand_ids(&game, SeatId(0))[0];

    let events = game
        .submit(
            SeatId(0),
            Action::MoveCards {
                moves: vec![CardMove {
                    card,
                    to_seat: SeatId(0),
                    to_zone: ZoneKind::Library,
                    position: MovePosition::Bottom,
                    face_down: None,
                    tapped: None,
                }],
            },
        )
        .unwrap();
    let redacted = events[0].redact(Perspective::Seat(SeatId(1))).unwrap();
    assert!(matches!(
        first_moved_card_ref(redacted),
        CardRef::Hidden { .. }
    ));
}

#[test]
fn face_down_attr_event_keeps_pre_action_public_identity() {
    let (mut game, _) = Game::new(setup(5, 4, 2));
    keep_both(&mut game);
    let card = hand_ids(&game, SeatId(0))[0];
    game.submit(
        SeatId(0),
        Action::MoveCards {
            moves: vec![CardMove {
                card,
                to_seat: SeatId(0),
                to_zone: ZoneKind::Battlefield,
                position: MovePosition::Battlefield { x: 0, y: 0 },
                face_down: Some(false),
                tapped: None,
            }],
        },
    )
    .unwrap();

    let events = game
        .submit(
            SeatId(0),
            Action::SetCardAttr {
                card,
                attr: CardAttr::FaceDown { value: true },
            },
        )
        .unwrap();
    let redacted = events[0].redact(Perspective::Global).unwrap();
    assert!(matches!(attr_set_card_ref(redacted), CardRef::Known(_)));
}

#[test]
fn randomized_card_ids_do_not_track_decklist_position_for_dealt_cards() {
    let mut observed_mismatch = false;
    for seed in 0..64 {
        let (_, events) = Game::new(setup(seed, 4, 2));
        for event in events {
            let Event::HandDealt { seat, cards } = event.event else {
                continue;
            };
            if seat != SeatId(0) {
                continue;
            }
            for card in cards {
                let CardRef::Known(view) = card else {
                    continue;
                };
                if view.id.0 != deck_index_from_name(&view.spec.name) {
                    observed_mismatch = true;
                    break;
                }
            }
        }
    }
    assert!(observed_mismatch);
}
