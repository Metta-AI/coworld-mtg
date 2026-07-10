use tabletop_core::*;

fn mountain(index: usize) -> CardSpec {
    CardSpec {
        name: format!("Mountain {index}"),
        type_line: "Basic Land - Mountain".to_owned(),
        mana_cost: None,
        power_toughness: None,
        oracle_text: "{T}: Add {R}.".to_owned(),
        art_id: None,
    }
}

fn goblin(index: usize) -> CardSpec {
    CardSpec {
        name: format!("Goblin Raider {index}"),
        type_line: "Creature - Goblin Warrior".to_owned(),
        mana_cost: Some("{1}{R}".to_owned()),
        power_toughness: Some("2/2".to_owned()),
        oracle_text: String::new(),
        art_id: None,
    }
}

fn setup() -> GameSetup {
    let mut red_cards = Vec::new();
    for index in 0..10 {
        red_cards.push(mountain(index));
        red_cards.push(goblin(index));
    }
    let mut green_cards = Vec::new();
    for index in 0..10 {
        green_cards.push(CardSpec {
            name: format!("Forest {index}"),
            type_line: "Basic Land - Forest".to_owned(),
            mana_cost: None,
            power_toughness: None,
            oracle_text: "{T}: Add {G}.".to_owned(),
            art_id: None,
        });
        green_cards.push(CardSpec {
            name: format!("Bear Cub {index}"),
            type_line: "Creature - Bear".to_owned(),
            mana_cost: Some("{1}{G}".to_owned()),
            power_toughness: Some("2/2".to_owned()),
            oracle_text: String::new(),
            art_id: None,
        });
    }
    GameSetup {
        seed: 99,
        players: [
            PlayerSetup {
                name: "Red".to_owned(),
                deck: DeckList {
                    name: "Red Deck".to_owned(),
                    cards: red_cards,
                },
            },
            PlayerSetup {
                name: "Green".to_owned(),
                deck: DeckList {
                    name: "Green Deck".to_owned(),
                    cards: green_cards,
                },
            },
        ],
        starting_life: 20,
        turn_cap: 5,
        reaction_depth_cap: 2,
    }
}

fn keep_both(game: &mut Game) {
    game.submit(SeatId(0), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
    game.submit(SeatId(1), Action::MulliganKeep { bottom: vec![] })
        .unwrap();
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

fn advance_phase(game: &mut Game, active: SeatId) {
    game.submit(active, Action::NextPhase).unwrap();
    game.submit(active.opponent(), Action::Pass).unwrap();
}

#[test]
fn scripted_duel_reaches_life_zero() {
    let (mut game, _) = Game::new(setup());
    keep_both(&mut game);

    let hand = hand_ids(&game, SeatId(0));
    let land = hand[0];
    let creature = hand[1];

    advance_phase(&mut game, SeatId(0));
    advance_phase(&mut game, SeatId(0));
    advance_phase(&mut game, SeatId(0));
    assert_eq!(game.snapshot(Perspective::Full).phase, Phase::Main1);

    game.submit(
        SeatId(0),
        Action::MoveCards {
            moves: vec![CardMove {
                card: land,
                to_seat: SeatId(0),
                to_zone: ZoneKind::Battlefield,
                position: MovePosition::Battlefield { x: 0, y: 0 },
                face_down: None,
                tapped: Some(false),
            }],
        },
    )
    .unwrap();
    game.submit(
        SeatId(0),
        Action::SetCardAttr {
            card: land,
            attr: CardAttr::Tapped { value: true },
        },
    )
    .unwrap();
    game.submit(
        SeatId(0),
        Action::Say {
            text: "tap land, cast creature".to_owned(),
        },
    )
    .unwrap();
    game.submit(
        SeatId(0),
        Action::MoveCards {
            moves: vec![CardMove {
                card: creature,
                to_seat: SeatId(0),
                to_zone: ZoneKind::Battlefield,
                position: MovePosition::Battlefield { x: 1, y: 0 },
                face_down: None,
                tapped: Some(false),
            }],
        },
    )
    .unwrap();

    let global = game.snapshot(Perspective::Global);
    assert_eq!(global.players[0].battlefield.len(), 2);
    assert!(matches!(global.players[1].hand[0], CardRef::Hidden { .. }));

    advance_phase(&mut game, SeatId(0));
    advance_phase(&mut game, SeatId(0));
    assert_eq!(
        game.snapshot(Perspective::Full).phase,
        Phase::DeclareAttackers
    );

    game.submit(
        SeatId(0),
        Action::SetCardAttr {
            card: creature,
            attr: CardAttr::Attacking { value: true },
        },
    )
    .unwrap();
    advance_phase(&mut game, SeatId(0));
    advance_phase(&mut game, SeatId(0));
    assert_eq!(game.snapshot(Perspective::Full).phase, Phase::CombatDamage);

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
    assert_eq!(outcome.final_life, [20, 0]);
}
