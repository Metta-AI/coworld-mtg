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

fn setup(seed: u64, deck_size: usize) -> GameSetup {
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
        turn_cap: 5,
        reaction_depth_cap: 2,
    }
}

fn hand_ids(game: &Game, seat: SeatId) -> Vec<CardId> {
    game.snapshot(Perspective::Seat(seat)).players[seat.index()]
        .hand
        .iter()
        .map(|card| match card {
            CardRef::Known(view) => view.id,
            CardRef::Hidden { .. } => panic!("own hand should be known"),
        })
        .collect()
}

fn keep_both(game: &mut Game) {
    game.submit(SeatId(0), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
    game.submit(SeatId(1), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
}

#[test]
fn wrong_seat_rejection() {
    let (mut game, _) = Game::new(setup(1, 10));
    let err = game
        .submit(SeatId(1), Action::MulliganKeep { bottom: vec![] })
        .unwrap_err();
    assert_eq!(err, ActionError::NotYourWindow);

    game.submit(SeatId(0), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
    let err = game
        .submit(SeatId(0), Action::MulliganKeep { bottom: vec![] })
        .unwrap_err();
    assert_eq!(err, ActionError::NotYourWindow);
}

#[test]
fn pass_and_reaction_handoff_transcript() {
    let (mut game, _) = Game::new(setup(2, 10));
    keep_both(&mut game);
    assert_eq!(
        game.expectation(),
        &Expectation::MainWindow { seat: SeatId(0) }
    );

    game.submit(SeatId(0), Action::Pass).unwrap();
    assert_eq!(
        game.expectation(),
        &Expectation::ReactionWindow {
            seat: SeatId(1),
            depth: 0
        }
    );

    game.submit(
        SeatId(1),
        Action::Say {
            text: "response".to_owned(),
        },
    )
    .unwrap();
    assert_eq!(
        game.expectation(),
        &Expectation::ReactionWindow {
            seat: SeatId(0),
            depth: 1
        }
    );

    game.submit(SeatId(0), Action::Pass).unwrap();
    assert_eq!(
        game.expectation(),
        &Expectation::ReactionWindow {
            seat: SeatId(1),
            depth: 0
        }
    );

    game.submit(SeatId(1), Action::Pass).unwrap();
    assert_eq!(
        game.expectation(),
        &Expectation::MainWindow { seat: SeatId(0) }
    );
}

#[test]
fn london_mulligan_flow_bottoms_in_order() {
    let (mut game, _) = Game::new(setup(3, 10));

    game.submit(SeatId(0), Action::MulliganAgain).unwrap();
    assert_eq!(
        game.expectation(),
        &Expectation::Mulligan {
            seat: SeatId(0),
            keeping_hand_of: 6,
            must_bottom: 1
        }
    );
    let bottom_0 = vec![hand_ids(&game, SeatId(0))[0]];
    game.submit(SeatId(0), Action::MulliganKeep { bottom: bottom_0 })
        .unwrap();

    game.submit(SeatId(1), Action::MulliganAgain).unwrap();
    game.submit(SeatId(1), Action::MulliganAgain).unwrap();
    assert_eq!(
        game.expectation(),
        &Expectation::Mulligan {
            seat: SeatId(1),
            keeping_hand_of: 5,
            must_bottom: 2
        }
    );
    let bottom_1 = hand_ids(&game, SeatId(1))[0..2].to_vec();
    game.submit(SeatId(1), Action::MulliganKeep { bottom: bottom_1 })
        .unwrap();

    let snapshot = game.snapshot(Perspective::Seat(SeatId(0)));
    assert_eq!(snapshot.players[0].mulligan_count, 1);
    assert_eq!(snapshot.players[0].hand.len(), 6);
    assert_eq!(snapshot.players[0].library_count, 4);
    assert_eq!(snapshot.players[1].mulligan_count, 2);
    assert_eq!(snapshot.players[1].hand.len(), 5);
    assert_eq!(snapshot.players[1].library_count, 5);
    assert_eq!(
        game.expectation(),
        &Expectation::MainWindow { seat: SeatId(0) }
    );
}

#[test]
fn concede_is_legal_from_any_window_and_postgame_only_allows_chat() {
    let (mut game, _) = Game::new(setup(4, 10));
    game.submit(SeatId(1), Action::Concede).unwrap();
    assert_eq!(game.outcome().unwrap().winner, Some(SeatId(0)),);
    assert_eq!(game.outcome().unwrap().reason, EndReason::Concession);

    game.submit(
        SeatId(1),
        Action::Say {
            text: "good game".to_owned(),
        },
    )
    .unwrap();
    let err = game
        .submit(SeatId(1), Action::Draw { count: 1 })
        .unwrap_err();
    assert_eq!(err, ActionError::GameIsOver);
}
