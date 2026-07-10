use tabletop_core::*;

fn card(name: &str) -> CardSpec {
    CardSpec {
        name: name.to_owned(),
        type_line: "Creature".to_owned(),
        mana_cost: Some("{1}{R}".to_owned()),
        power_toughness: Some("2/2".to_owned()),
        oracle_text: String::new(),
        art_id: None,
    }
}

fn setup(seed: u64, deck_size: usize, turn_cap: u32) -> GameSetup {
    let deck_a = DeckList {
        name: "A".to_owned(),
        cards: (0..deck_size)
            .map(|index| card(&format!("A Card {index}")))
            .collect(),
    };
    let deck_b = DeckList {
        name: "B".to_owned(),
        cards: (0..deck_size)
            .map(|index| card(&format!("B Card {index}")))
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
        reaction_depth_cap: 2,
    }
}

fn keep_both(game: &mut Game) {
    game.submit(SeatId(0), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
    game.submit(SeatId(1), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
}

fn first_hand_id(game: &Game, seat: SeatId, perspective: Perspective) -> CardId {
    game.snapshot(perspective).players[seat.index()].hand[0]
        .clone()
        .id()
}

fn put_first_hand_card_on_library(seed: u64) -> (Game, CardId) {
    let (mut game, _) = Game::new(setup(seed, 10, 5));
    keep_both(&mut game);
    let card = first_hand_id(&game, SeatId(0), Perspective::Seat(SeatId(0)));
    game.submit(
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
    (game, card)
}

trait CardRefId {
    fn id(&self) -> CardId;
}

impl CardRefId for CardRef {
    fn id(&self) -> CardId {
        match self {
            CardRef::Known(view) => view.id,
            CardRef::Hidden { id } => *id,
        }
    }
}

#[test]
fn cannot_move_opponent_hand_cards() {
    let (mut game, _) = Game::new(setup(10, 10, 5));
    keep_both(&mut game);
    let opponent_card = first_hand_id(&game, SeatId(1), Perspective::Full);

    let err = game
        .submit(
            SeatId(0),
            Action::MoveCards {
                moves: vec![CardMove {
                    card: opponent_card,
                    to_seat: SeatId(0),
                    to_zone: ZoneKind::Battlefield,
                    position: MovePosition::Battlefield { x: 0, y: 0 },
                    face_down: None,
                    tapped: None,
                }],
            },
        )
        .unwrap_err();
    assert_eq!(err, ActionError::NotYourCard);
}

#[test]
fn tokens_are_removed_when_they_leave_the_battlefield() {
    let (mut game, _) = Game::new(setup(11, 10, 5));
    keep_both(&mut game);

    game.submit(
        SeatId(0),
        Action::CreateToken {
            spec: card("Goblin Token"),
            x: 3,
            y: 4,
        },
    )
    .unwrap();
    let token = game.snapshot(Perspective::Full).players[0]
        .battlefield
        .iter()
        .find_map(|card| match card {
            CardRef::Known(view) if view.is_token => Some(view.id),
            _ => None,
        })
        .unwrap();

    let events = game
        .submit(
            SeatId(0),
            Action::MoveCards {
                moves: vec![CardMove {
                    card: token,
                    to_seat: SeatId(0),
                    to_zone: ZoneKind::Graveyard,
                    position: MovePosition::Top,
                    face_down: None,
                    tapped: None,
                }],
            },
        )
        .unwrap();
    assert!(events
        .iter()
        .any(|event| matches!(event.event, Event::TokenRemoved { .. })));
    let snapshot = game.snapshot(Perspective::Full);
    assert!(!snapshot.players[0]
        .battlefield
        .iter()
        .chain(snapshot.players[0].graveyard.iter())
        .any(|card| card.id() == token));
}

#[test]
fn empty_library_draw_loses() {
    let (mut game, _) = Game::new(setup(12, 7, 5));
    keep_both(&mut game);
    assert_eq!(game.snapshot(Perspective::Full).players[0].library_count, 0);

    game.submit(SeatId(0), Action::Draw { count: 1 }).unwrap();
    let outcome = game.outcome().unwrap();
    assert_eq!(outcome.winner, Some(SeatId(1)));
    assert_eq!(outcome.reason, EndReason::DrewFromEmptyLibrary);
}

#[test]
fn life_zero_ends_game() {
    let (mut game, _) = Game::new(setup(13, 10, 5));
    keep_both(&mut game);

    game.submit(
        SeatId(0),
        Action::AddCounter {
            target: CounterTarget::Player { seat: SeatId(1) },
            name: "life".to_owned(),
            delta: -20,
        },
    )
    .unwrap();
    let outcome = game.outcome().unwrap();
    assert_eq!(outcome.winner, Some(SeatId(0)));
    assert_eq!(outcome.reason, EndReason::LifeZero);
}

#[test]
fn turn_cap_uses_life_comparison() {
    let (mut game, _) = Game::new(setup(14, 10, 1));
    keep_both(&mut game);
    game.submit(
        SeatId(0),
        Action::AddCounter {
            target: CounterTarget::Player { seat: SeatId(0) },
            name: "life".to_owned(),
            delta: 1,
        },
    )
    .unwrap();

    game.submit(SeatId(0), Action::NextTurn).unwrap();
    let outcome = game.outcome().unwrap();
    assert_eq!(outcome.winner, Some(SeatId(0)));
    assert_eq!(outcome.reason, EndReason::TurnCap);
    assert_eq!(outcome.turns, 1);
}

#[test]
fn library_cards_cannot_be_moved_by_id() {
    let (mut game, card) = put_first_hand_card_on_library(15);

    let err = game
        .submit(
            SeatId(0),
            Action::MoveCards {
                moves: vec![CardMove {
                    card,
                    to_seat: SeatId(0),
                    to_zone: ZoneKind::Battlefield,
                    position: MovePosition::Battlefield { x: 0, y: 0 },
                    face_down: None,
                    tapped: None,
                }],
            },
        )
        .unwrap_err();
    assert_eq!(err, ActionError::HiddenZoneAddressing);
}

#[test]
fn library_cards_cannot_have_attrs_set_by_id() {
    let (mut game, card) = put_first_hand_card_on_library(16);

    let err = game
        .submit(
            SeatId(0),
            Action::SetCardAttr {
                card,
                attr: CardAttr::Tapped { value: true },
            },
        )
        .unwrap_err();
    assert_eq!(err, ActionError::HiddenZoneAddressing);
}

#[test]
fn library_cards_cannot_have_counters_added_by_id() {
    let (mut game, card) = put_first_hand_card_on_library(17);

    let err = game
        .submit(
            SeatId(0),
            Action::AddCounter {
                target: CounterTarget::Card { card },
                name: "+1/+1".to_owned(),
                delta: 1,
            },
        )
        .unwrap_err();
    assert_eq!(err, ActionError::HiddenZoneAddressing);
}

#[test]
fn library_cards_cannot_be_pointed_from_by_id() {
    let (mut game, card) = put_first_hand_card_on_library(18);

    let err = game
        .submit(
            SeatId(0),
            Action::Point {
                from: card,
                to: None,
            },
        )
        .unwrap_err();
    assert_eq!(err, ActionError::HiddenZoneAddressing);
}

#[test]
fn move_top_of_library_mills_cards_face_up() {
    let (mut game, _) = Game::new(setup(19, 10, 5));
    keep_both(&mut game);

    let events = game
        .submit(
            SeatId(0),
            Action::MoveTopOfLibrary {
                count: 2,
                to_seat: SeatId(0),
                to_zone: ZoneKind::Graveyard,
                position: MovePosition::Top,
                face_down: false,
            },
        )
        .unwrap();

    let Event::CardsMoved { moves } = &events[0].event else {
        panic!("expected CardsMoved");
    };
    assert_eq!(moves.len(), 2);
    assert!(moves.iter().all(|move_event| {
        move_event.from
            == ZoneRef {
                seat: SeatId(0),
                zone: ZoneKind::Library,
            }
            && move_event.to
                == ZoneRef {
                    seat: SeatId(0),
                    zone: ZoneKind::Graveyard,
                }
            && move_event.was_face_down
    }));

    let redacted = events[0].redact(Perspective::Global).unwrap();
    let Event::CardsMoved { moves } = redacted.event else {
        panic!("expected CardsMoved");
    };
    assert!(moves
        .iter()
        .all(|move_event| matches!(move_event.card, CardRef::Known(_))));
    assert_eq!(
        game.snapshot(Perspective::Full).players[0].graveyard.len(),
        2
    );
}

#[test]
fn move_top_of_library_exiles_cards_face_down() {
    let (mut game, _) = Game::new(setup(20, 10, 5));
    keep_both(&mut game);

    let events = game
        .submit(
            SeatId(0),
            Action::MoveTopOfLibrary {
                count: 2,
                to_seat: SeatId(0),
                to_zone: ZoneKind::Exile,
                position: MovePosition::Bottom,
                face_down: true,
            },
        )
        .unwrap();
    let global = events[0].redact(Perspective::Global).unwrap();
    let Event::CardsMoved { moves } = global.event else {
        panic!("expected CardsMoved");
    };
    assert!(moves
        .iter()
        .all(|move_event| matches!(move_event.card, CardRef::Hidden { .. })));

    let actor = events[0].redact(Perspective::Seat(SeatId(0))).unwrap();
    let Event::CardsMoved { moves } = actor.event else {
        panic!("expected CardsMoved");
    };
    assert!(moves
        .iter()
        .all(|move_event| matches!(move_event.card, CardRef::Known(_))));
    assert_eq!(game.snapshot(Perspective::Full).players[0].exile.len(), 2);
}
