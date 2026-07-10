use crate::actions::{Action, ActionError, CardMove, CounterTarget, MovePosition, RevealTo};
use crate::cards::{CardInstance, CardRef};
use crate::events::{CardMoveEvent, CounterTargetRef, Event, LoggedEvent};
use crate::expectation::{EndReason, Expectation, GameOutcome};
use crate::ids::{CardId, SeatId, Seq};
use crate::redact::{card_ref_for_zone, Arrow, Perspective, PlayerSnapshot, Snapshot};
use crate::rng;
use crate::setup::GameSetup;
use crate::zones::{Phase, ZoneKind, ZoneRef};
use rand_chacha::ChaCha12Rng;
use std::collections::{BTreeMap, HashMap};

#[derive(Clone, Debug)]
pub struct Game {
    pub(crate) players: [PlayerState; 2],
    pub(crate) cards: HashMap<CardId, CardInstance>,
    pub(crate) rng: ChaCha12Rng,
    pub(crate) turn: u32,
    pub(crate) phase: Phase,
    pub(crate) active: SeatId,
    pub(crate) expectation: Expectation,
    pub(crate) seq: u64,
    pub(crate) log: Vec<LoggedEvent>,
    pub(crate) turn_cap: u32,
    pub(crate) reaction_depth_cap: u8,
    pub(crate) next_card_id: u32,
}

#[derive(Clone, Debug)]
pub(crate) struct PlayerState {
    pub name: String,
    pub counters: BTreeMap<String, i32>,
    pub mulligan_count: u8,
    pub library: Vec<CardId>,
    pub hand: Vec<CardId>,
    pub battlefield: Vec<CardId>,
    pub graveyard: Vec<CardId>,
    pub exile: Vec<CardId>,
    pub arrows: BTreeMap<CardId, Option<CardId>>,
}

impl Game {
    pub fn new(setup: GameSetup) -> (Game, Vec<LoggedEvent>) {
        let starting_life = setup.normalized_starting_life();
        let turn_cap = setup.normalized_turn_cap();
        let reaction_depth_cap = setup.normalized_reaction_depth_cap();
        let mut rng = rng::seeded(setup.seed);
        let mut cards = HashMap::new();
        let mut players = [
            PlayerState::new(setup.players[0].name.clone(), starting_life),
            PlayerState::new(setup.players[1].name.clone(), starting_life),
        ];
        let deck_positions: Vec<(SeatId, usize)> = setup
            .players
            .iter()
            .enumerate()
            .flat_map(|(seat_index, player_setup)| {
                let seat = SeatId(seat_index as u8);
                (0..player_setup.deck.cards.len()).map(move |deck_index| (seat, deck_index))
            })
            .collect();
        let mut ids: Vec<CardId> = (0..deck_positions.len() as u32).map(CardId).collect();
        rng::shuffle(&mut rng, &mut ids);
        let next_card_id = ids.len() as u32;

        for ((seat, deck_index), id) in deck_positions.into_iter().zip(ids) {
            if let Some(spec) = setup.players[seat.index()]
                .deck
                .cards
                .get(deck_index)
                .cloned()
            {
                cards.insert(id, CardInstance::new_deck_card(id, seat, spec));
                players[seat.index()].library.push(id);
            }
        }

        rng::shuffle(&mut rng, &mut players[0].library);
        rng::shuffle(&mut rng, &mut players[1].library);

        let mut game = Game {
            players,
            cards,
            rng,
            turn: 0,
            phase: Phase::Untap,
            active: SeatId(0),
            expectation: Expectation::Mulligan {
                seat: SeatId(0),
                keeping_hand_of: 7,
                must_bottom: 0,
            },
            seq: 0,
            log: Vec::new(),
            turn_cap,
            reaction_depth_cap,
            next_card_id,
        };

        game.emit(
            None,
            Event::GameStarted {
                players: [game.players[0].name.clone(), game.players[1].name.clone()],
                starting_life,
                turn_cap,
                reaction_depth_cap,
            },
        );
        game.emit(None, Event::Shuffled { seat: SeatId(0) });
        game.emit(None, Event::Shuffled { seat: SeatId(1) });
        let dealt_0 = game.deal_hand(SeatId(0), 7);
        game.emit(
            None,
            Event::HandDealt {
                seat: SeatId(0),
                cards: dealt_0,
            },
        );
        let dealt_1 = game.deal_hand(SeatId(1), 7);
        game.emit(
            None,
            Event::HandDealt {
                seat: SeatId(1),
                cards: dealt_1,
            },
        );
        game.emit(
            None,
            Event::WindowOpened {
                expectation: game.expectation.clone(),
            },
        );
        let events = game.log.clone();
        (game, events)
    }

    pub fn submit(
        &mut self,
        seat: SeatId,
        action: Action,
    ) -> Result<Vec<LoggedEvent>, ActionError> {
        if !seat.is_valid() {
            return Err(ActionError::InvalidArgument(
                "seat must be 0 or 1".to_owned(),
            ));
        }

        let start = self.log.len();
        if matches!(action, Action::Concede)
            && !matches!(self.expectation, Expectation::GameOver { .. })
        {
            self.concede(seat);
            return Ok(self.log[start..].to_vec());
        }

        match &self.expectation {
            Expectation::GameOver { .. } => {
                if let Action::Say { text } = action {
                    self.apply_say(seat, text)?;
                    return Ok(self.log[start..].to_vec());
                }
                return Err(ActionError::GameIsOver);
            }
            Expectation::Mulligan { seat: expected, .. }
            | Expectation::MainWindow { seat: expected }
            | Expectation::ReactionWindow { seat: expected, .. } => {
                if *expected != seat {
                    return Err(ActionError::NotYourWindow);
                }
            }
        }

        match self.expectation.clone() {
            Expectation::Mulligan { .. } => self.submit_mulligan(seat, action)?,
            Expectation::MainWindow { .. } => self.submit_main_window(seat, action)?,
            Expectation::ReactionWindow { depth, .. } => {
                self.submit_reaction_window(seat, depth, action)?;
            }
            Expectation::GameOver { .. } => unreachable!(),
        }

        Ok(self.log[start..].to_vec())
    }

    pub fn expectation(&self) -> &Expectation {
        &self.expectation
    }

    pub fn outcome(&self) -> Option<&GameOutcome> {
        match &self.expectation {
            Expectation::GameOver { outcome } => Some(outcome),
            _ => None,
        }
    }

    pub fn snapshot(&self, perspective: Perspective) -> Snapshot {
        Snapshot {
            seq: Seq(self.seq.saturating_sub(1)),
            turn: self.turn,
            phase: self.phase,
            active: self.active,
            expectation: self.expectation.clone(),
            players: [
                self.player_snapshot(SeatId(0), perspective),
                self.player_snapshot(SeatId(1), perspective),
            ],
        }
    }

    pub fn log(&self) -> &[LoggedEvent] {
        &self.log
    }

    pub fn flag(&mut self, seat: SeatId) {
        if !seat.is_valid() || matches!(self.expectation, Expectation::GameOver { .. }) {
            return;
        }
        self.end_game(Some(seat.opponent()), EndReason::ClockFlag);
    }

    pub fn system_say(&mut self, seat: SeatId, text: String) -> Vec<LoggedEvent> {
        if !seat.is_valid() || text.chars().count() > 2000 {
            return Vec::new();
        }
        let start = self.log.len();
        self.emit(None, Event::Said { seat, text });
        self.log[start..].to_vec()
    }

    fn submit_mulligan(&mut self, seat: SeatId, action: Action) -> Result<(), ActionError> {
        match action {
            Action::MulliganAgain => self.mulligan_again(seat),
            Action::MulliganKeep { bottom } => self.mulligan_keep(seat, bottom),
            Action::Say { text } => self.apply_say(seat, text),
            Action::Concede => unreachable!(),
            _ => Err(ActionError::InvalidInWindow),
        }
    }

    fn submit_main_window(&mut self, seat: SeatId, action: Action) -> Result<(), ActionError> {
        match action {
            Action::Pass => {
                self.emit(Some(seat), Event::Passed { seat });
                self.open_reaction(seat.opponent(), 0);
                Ok(())
            }
            Action::NextPhase => self.next_phase(seat),
            Action::NextTurn => self.next_turn(seat),
            Action::MulliganKeep { .. } | Action::MulliganAgain => {
                Err(ActionError::InvalidInWindow)
            }
            Action::Concede => unreachable!(),
            action => self.apply_game_action(seat, action),
        }
    }

    fn submit_reaction_window(
        &mut self,
        seat: SeatId,
        depth: u8,
        action: Action,
    ) -> Result<(), ActionError> {
        match action {
            Action::Pass => {
                self.emit(Some(seat), Event::Passed { seat });
                if depth == 0 {
                    self.open_main_window(self.active);
                } else {
                    self.open_reaction(seat.opponent(), depth - 1);
                }
                Ok(())
            }
            Action::NextPhase
            | Action::NextTurn
            | Action::MulliganKeep { .. }
            | Action::MulliganAgain => Err(ActionError::InvalidInWindow),
            Action::Concede => unreachable!(),
            action => {
                self.apply_game_action(seat, action)?;
                if self.outcome().is_none() && depth < self.reaction_depth_cap {
                    self.open_reaction(seat.opponent(), depth + 1);
                }
                Ok(())
            }
        }
    }

    fn apply_game_action(&mut self, seat: SeatId, action: Action) -> Result<(), ActionError> {
        match action {
            Action::Draw { count } => self.draw(seat, count),
            Action::MoveCards { moves } => self.move_cards(seat, moves),
            Action::MoveTopOfLibrary {
                count,
                to_seat,
                to_zone,
                position,
                face_down,
            } => self.move_top_of_library(seat, count, to_seat, to_zone, position, face_down),
            Action::SetCardAttr { card, attr } => self.set_card_attr(seat, card, attr),
            Action::CreateToken { spec, x, y } => {
                self.create_token(seat, spec, x, y);
                Ok(())
            }
            Action::AddCounter {
                target,
                name,
                delta,
            } => self.add_counter(seat, target, name, delta),
            Action::Shuffle => self.shuffle_library(seat),
            Action::RollDie { sides } => self.roll_die(seat, sides),
            Action::Reveal { cards, to } => self.reveal(seat, cards, to),
            Action::Say { text } => self.apply_say(seat, text),
            Action::Point { from, to } => self.point(seat, from, to),
            Action::Pass
            | Action::NextPhase
            | Action::NextTurn
            | Action::MulliganKeep { .. }
            | Action::MulliganAgain
            | Action::Concede => Err(ActionError::InvalidInWindow),
        }
    }

    fn mulligan_again(&mut self, seat: SeatId) -> Result<(), ActionError> {
        let player = &mut self.players[seat.index()];
        let hand = std::mem::take(&mut player.hand);
        for id in hand {
            player.library.push(id);
            if let Some(card) = self.cards.get_mut(&id) {
                card.location = ZoneRef {
                    seat,
                    zone: ZoneKind::Library,
                };
                card.tapped = false;
                card.attacking = false;
                card.x = None;
                card.y = None;
            }
        }
        rng::shuffle(&mut self.rng, &mut player.library);
        player.mulligan_count = player.mulligan_count.saturating_add(1);
        self.emit(Some(seat), Event::Shuffled { seat });
        let dealt = self.deal_hand(seat, 7);
        self.emit(Some(seat), Event::HandDealt { seat, cards: dealt });
        self.emit(
            Some(seat),
            Event::MulliganResolved {
                seat,
                kept: false,
                mulligan_count: self.players[seat.index()].mulligan_count,
                bottomed: 0,
            },
        );
        self.expectation = self.mulligan_expectation(seat);
        self.emit(
            None,
            Event::WindowOpened {
                expectation: self.expectation.clone(),
            },
        );
        Ok(())
    }

    fn mulligan_keep(&mut self, seat: SeatId, bottom: Vec<CardId>) -> Result<(), ActionError> {
        let mulligan_count = self.players[seat.index()].mulligan_count;
        if bottom.len() != usize::from(mulligan_count) {
            return Err(ActionError::BadMulligan);
        }
        for id in &bottom {
            if !self.players[seat.index()].hand.contains(id) {
                return Err(ActionError::BadMulligan);
            }
        }
        for id in bottom.iter().copied() {
            self.remove_from_zone(id)?;
            self.players[seat.index()].library.push(id);
            if let Some(card) = self.cards.get_mut(&id) {
                card.location = ZoneRef {
                    seat,
                    zone: ZoneKind::Library,
                };
                card.x = None;
                card.y = None;
                card.attacking = false;
            }
        }
        self.emit(
            Some(seat),
            Event::MulliganResolved {
                seat,
                kept: true,
                mulligan_count,
                bottomed: mulligan_count,
            },
        );
        if seat == SeatId(0) {
            self.expectation = self.mulligan_expectation(SeatId(1));
            self.emit(
                None,
                Event::WindowOpened {
                    expectation: self.expectation.clone(),
                },
            );
        } else {
            self.turn = 1;
            self.phase = Phase::Untap;
            self.active = SeatId(0);
            self.emit(
                None,
                Event::TurnChanged {
                    turn: self.turn,
                    active: self.active,
                },
            );
            self.open_main_window(self.active);
        }
        Ok(())
    }

    fn mulligan_expectation(&self, seat: SeatId) -> Expectation {
        let count = self.players[seat.index()].mulligan_count;
        Expectation::Mulligan {
            seat,
            keeping_hand_of: 7_u8.saturating_sub(count),
            must_bottom: count,
        }
    }

    fn draw(&mut self, seat: SeatId, count: u32) -> Result<(), ActionError> {
        let mut drawn = Vec::new();
        for _ in 0..count {
            let Some(id) = self.players[seat.index()].library.first().copied() else {
                if !drawn.is_empty() {
                    self.emit(Some(seat), Event::Drew { seat, cards: drawn });
                }
                self.end_game(Some(seat.opponent()), EndReason::DrewFromEmptyLibrary);
                return Ok(());
            };
            self.players[seat.index()].library.remove(0);
            self.players[seat.index()].hand.push(id);
            let card = self.cards.get_mut(&id).ok_or(ActionError::UnknownCard)?;
            card.location = ZoneRef {
                seat,
                zone: ZoneKind::Hand,
            };
            card.x = None;
            card.y = None;
            card.attacking = false;
            drawn.push(CardRef::Known(card.view()));
        }
        self.emit(Some(seat), Event::Drew { seat, cards: drawn });
        Ok(())
    }

    fn move_cards(&mut self, seat: SeatId, moves: Vec<CardMove>) -> Result<(), ActionError> {
        if moves.is_empty() {
            return Err(ActionError::InvalidArgument(
                "moves must not be empty".to_owned(),
            ));
        }
        let mut moved = Vec::new();
        let mut removed_tokens = Vec::new();
        for card_move in moves {
            self.validate_move(seat, &card_move)?;
            let id = card_move.card;
            let from = self.card(id)?.location;
            let was_face_down = self.card(id)?.face_down;
            let token_leaves_battlefield = {
                let card = self.card(id)?;
                card.is_token
                    && from.zone == ZoneKind::Battlefield
                    && card_move.to_zone != ZoneKind::Battlefield
            };
            if token_leaves_battlefield {
                let view = self.card(id)?.view();
                self.remove_from_zone(id)?;
                self.cards.remove(&id);
                removed_tokens.push((CardRef::Known(view), from));
                continue;
            }

            self.remove_from_zone(id)?;
            self.insert_into_zone(id, &card_move)?;
            let to = ZoneRef {
                seat: card_move.to_seat,
                zone: card_move.to_zone,
            };
            {
                let card = self.card_mut(id)?;
                card.location = to;
                if let Some(face_down) = card_move.face_down {
                    card.face_down = face_down;
                }
                if let Some(tapped) = card_move.tapped {
                    card.tapped = tapped;
                }
                if let MovePosition::Battlefield { x, y } = &card_move.position {
                    card.x = Some(*x);
                    card.y = Some(*y);
                } else {
                    card.x = None;
                    card.y = None;
                    card.attacking = false;
                }
            }
            moved.push(CardMoveEvent {
                card: CardRef::Known(self.card(id)?.view()),
                from,
                to,
                was_face_down,
                position: card_move.position,
            });
        }
        if !moved.is_empty() {
            self.emit(Some(seat), Event::CardsMoved { moves: moved });
        }
        for (card, from) in removed_tokens {
            self.emit(Some(seat), Event::TokenRemoved { card, from });
        }
        Ok(())
    }

    fn move_top_of_library(
        &mut self,
        seat: SeatId,
        count: u32,
        to_seat: SeatId,
        to_zone: ZoneKind,
        position: MovePosition,
        face_down: bool,
    ) -> Result<(), ActionError> {
        if count == 0 {
            return Err(ActionError::InvalidArgument(
                "count must be positive".to_owned(),
            ));
        }
        if !to_seat.is_valid() {
            return Err(ActionError::InvalidArgument(
                "seat must be 0 or 1".to_owned(),
            ));
        }
        Self::validate_destination(to_zone, &position)?;
        let limit = usize::try_from(count).unwrap_or(usize::MAX);
        let ids: Vec<CardId> = self.players[seat.index()]
            .library
            .iter()
            .copied()
            .take(limit)
            .collect();
        let mut moved = Vec::with_capacity(ids.len());
        for id in ids {
            let card_move = CardMove {
                card: id,
                to_seat,
                to_zone,
                position: position.clone(),
                face_down: Some(face_down),
                tapped: None,
            };
            let from = ZoneRef {
                seat,
                zone: ZoneKind::Library,
            };
            self.remove_from_zone(id)?;
            self.insert_into_zone(id, &card_move)?;
            let to = ZoneRef {
                seat: to_seat,
                zone: to_zone,
            };
            {
                let card = self.card_mut(id)?;
                card.location = to;
                card.face_down = face_down;
                if let MovePosition::Battlefield { x, y } = &position {
                    card.x = Some(*x);
                    card.y = Some(*y);
                } else {
                    card.x = None;
                    card.y = None;
                    card.attacking = false;
                }
            }
            moved.push(CardMoveEvent {
                card: CardRef::Known(self.card(id)?.view()),
                from,
                to,
                was_face_down: true,
                position: position.clone(),
            });
        }
        self.emit(Some(seat), Event::CardsMoved { moves: moved });
        Ok(())
    }

    fn set_card_attr(
        &mut self,
        seat: SeatId,
        card: CardId,
        attr: crate::cards::CardAttr,
    ) -> Result<(), ActionError> {
        self.ensure_not_in_library(card)?;
        self.ensure_can_touch(seat, card)?;
        let zone = self.card(card)?.location;
        let was_face_down = self.card(card)?.face_down;
        {
            let instance = self.card_mut(card)?;
            instance.apply_attr(&attr);
        }
        self.emit(
            Some(seat),
            Event::AttrSet {
                card: CardRef::Known(self.card(card)?.view()),
                zone,
                was_face_down,
                attr,
            },
        );
        Ok(())
    }

    fn create_token(&mut self, seat: SeatId, spec: crate::setup::CardSpec, x: i16, y: i16) {
        let id = CardId(self.next_card_id);
        self.next_card_id += 1;
        let token = CardInstance::new_token(id, seat, spec, x, y);
        self.players[seat.index()].battlefield.push(id);
        let view = token.view();
        self.cards.insert(id, token);
        self.emit(
            Some(seat),
            Event::TokenCreated {
                card: CardRef::Known(view),
                zone: ZoneRef {
                    seat,
                    zone: ZoneKind::Battlefield,
                },
            },
        );
    }

    fn add_counter(
        &mut self,
        seat: SeatId,
        target: CounterTarget,
        name: String,
        delta: i32,
    ) -> Result<(), ActionError> {
        if name.is_empty() {
            return Err(ActionError::InvalidArgument(
                "counter name must not be empty".to_owned(),
            ));
        }
        match target {
            CounterTarget::Player { seat: target_seat } => {
                if !target_seat.is_valid() {
                    return Err(ActionError::InvalidArgument(
                        "seat must be 0 or 1".to_owned(),
                    ));
                }
                let counters = &mut self.players[target_seat.index()].counters;
                let old = *counters.get(&name).unwrap_or(&0);
                let new = old.saturating_add(delta);
                counters.insert(name.clone(), new);
                self.emit(
                    Some(seat),
                    Event::CounterChanged {
                        target: CounterTargetRef::Player { seat: target_seat },
                        name: name.clone(),
                        old,
                        new,
                        delta,
                    },
                );
                if name == "life" {
                    self.check_life_zero();
                }
            }
            CounterTarget::Card { card } => {
                self.ensure_not_in_library(card)?;
                self.ensure_can_touch(seat, card)?;
                let zone = self.card(card)?.location;
                let (old, new) = {
                    let instance = self.card_mut(card)?;
                    let old = *instance.counters.get(&name).unwrap_or(&0);
                    let new = old.saturating_add(delta);
                    instance.counters.insert(name.clone(), new);
                    (old, new)
                };
                self.emit(
                    Some(seat),
                    Event::CounterChanged {
                        target: CounterTargetRef::Card {
                            card: CardRef::Known(self.card(card)?.view()),
                            zone,
                        },
                        name,
                        old,
                        new,
                        delta,
                    },
                );
            }
        }
        Ok(())
    }

    fn shuffle_library(&mut self, seat: SeatId) -> Result<(), ActionError> {
        rng::shuffle(&mut self.rng, &mut self.players[seat.index()].library);
        self.emit(Some(seat), Event::Shuffled { seat });
        Ok(())
    }

    fn roll_die(&mut self, seat: SeatId, sides: u32) -> Result<(), ActionError> {
        if sides == 0 {
            return Err(ActionError::InvalidArgument(
                "die sides must be positive".to_owned(),
            ));
        }
        let result = rng::roll_die(&mut self.rng, sides);
        self.emit(
            Some(seat),
            Event::DieRolled {
                seat,
                sides,
                result,
            },
        );
        Ok(())
    }

    fn reveal(
        &mut self,
        seat: SeatId,
        cards: Vec<CardId>,
        to: RevealTo,
    ) -> Result<(), ActionError> {
        if cards.is_empty() {
            return Err(ActionError::InvalidArgument(
                "cards must not be empty".to_owned(),
            ));
        }
        let mut refs = Vec::with_capacity(cards.len());
        for id in cards {
            self.ensure_visible_to_actor(seat, id)?;
            refs.push(CardRef::Known(self.card(id)?.view()));
        }
        self.emit(
            Some(seat),
            Event::Revealed {
                seat,
                cards: refs,
                to,
            },
        );
        Ok(())
    }

    fn apply_say(&mut self, seat: SeatId, text: String) -> Result<(), ActionError> {
        if text.chars().count() > 2000 {
            return Err(ActionError::InvalidArgument(
                "say text exceeds 2000 chars".to_owned(),
            ));
        }
        self.emit(Some(seat), Event::Said { seat, text });
        Ok(())
    }

    fn point(&mut self, seat: SeatId, from: CardId, to: Option<CardId>) -> Result<(), ActionError> {
        self.ensure_not_in_library(from)?;
        self.ensure_can_touch(seat, from)?;
        if let Some(target) = to {
            self.card(target)?;
            self.ensure_not_in_library(target)?;
        }
        self.players[seat.index()].arrows.insert(from, to);
        self.emit(Some(seat), Event::Pointed { seat, from, to });
        Ok(())
    }

    fn next_phase(&mut self, seat: SeatId) -> Result<(), ActionError> {
        let next = self.phase.next().ok_or(ActionError::InvalidInWindow)?;
        self.phase = next;
        self.emit(Some(seat), Event::PhaseChanged { phase: self.phase });
        self.open_reaction(self.active.opponent(), 0);
        Ok(())
    }

    fn next_turn(&mut self, seat: SeatId) -> Result<(), ActionError> {
        if self.turn >= self.turn_cap {
            let life = self.life_totals();
            let winner = match life[0].cmp(&life[1]) {
                std::cmp::Ordering::Greater => Some(SeatId(0)),
                std::cmp::Ordering::Less => Some(SeatId(1)),
                std::cmp::Ordering::Equal => None,
            };
            self.end_game(winner, EndReason::TurnCap);
            return Ok(());
        }
        self.active = self.active.opponent();
        self.turn += 1;
        self.phase = Phase::Untap;
        self.emit(
            Some(seat),
            Event::TurnChanged {
                turn: self.turn,
                active: self.active,
            },
        );
        self.emit(Some(seat), Event::PhaseChanged { phase: self.phase });
        self.open_reaction(self.active.opponent(), 0);
        Ok(())
    }

    fn concede(&mut self, seat: SeatId) {
        self.end_game(Some(seat.opponent()), EndReason::Concession);
    }

    fn end_game(&mut self, winner: Option<SeatId>, reason: EndReason) {
        if matches!(self.expectation, Expectation::GameOver { .. }) {
            return;
        }
        let outcome = GameOutcome {
            winner,
            reason,
            final_life: self.life_totals(),
            turns: self.turn,
        };
        self.expectation = Expectation::GameOver {
            outcome: outcome.clone(),
        };
        self.emit(None, Event::GameEnded { outcome });
    }

    fn check_life_zero(&mut self) {
        let life = self.life_totals();
        if life[0] > 0 && life[1] > 0 {
            return;
        }
        let winner = match (life[0] <= 0, life[1] <= 0) {
            (true, true) => None,
            (true, false) => Some(SeatId(1)),
            (false, true) => Some(SeatId(0)),
            (false, false) => None,
        };
        self.end_game(winner, EndReason::LifeZero);
    }

    fn open_reaction(&mut self, seat: SeatId, depth: u8) {
        self.expectation = Expectation::ReactionWindow { seat, depth };
        self.emit(
            None,
            Event::WindowOpened {
                expectation: self.expectation.clone(),
            },
        );
    }

    fn open_main_window(&mut self, seat: SeatId) {
        self.expectation = Expectation::MainWindow { seat };
        self.emit(
            None,
            Event::WindowOpened {
                expectation: self.expectation.clone(),
            },
        );
    }

    fn deal_hand(&mut self, seat: SeatId, count: u32) -> Vec<CardRef> {
        let mut dealt = Vec::new();
        for _ in 0..count {
            let Some(id) = self.players[seat.index()].library.first().copied() else {
                break;
            };
            self.players[seat.index()].library.remove(0);
            self.players[seat.index()].hand.push(id);
            if let Some(card) = self.cards.get_mut(&id) {
                card.location = ZoneRef {
                    seat,
                    zone: ZoneKind::Hand,
                };
                dealt.push(CardRef::Known(card.view()));
            }
        }
        dealt
    }

    fn validate_move(&self, seat: SeatId, card_move: &CardMove) -> Result<(), ActionError> {
        if !card_move.to_seat.is_valid() {
            return Err(ActionError::InvalidArgument(
                "seat must be 0 or 1".to_owned(),
            ));
        }
        self.ensure_not_in_library(card_move.card)?;
        self.ensure_can_touch(seat, card_move.card)?;
        Self::validate_destination(card_move.to_zone, &card_move.position)
    }

    fn validate_destination(to_zone: ZoneKind, position: &MovePosition) -> Result<(), ActionError> {
        match (position, to_zone) {
            (MovePosition::Battlefield { .. }, ZoneKind::Battlefield) => Ok(()),
            (MovePosition::Top | MovePosition::Bottom | MovePosition::Index(_), zone)
                if zone != ZoneKind::Battlefield =>
            {
                Ok(())
            }
            _ => Err(ActionError::WrongZone),
        }
    }

    fn ensure_not_in_library(&self, id: CardId) -> Result<(), ActionError> {
        if self.card(id)?.location.zone == ZoneKind::Library {
            return Err(ActionError::HiddenZoneAddressing);
        }
        Ok(())
    }

    fn ensure_can_touch(&self, seat: SeatId, id: CardId) -> Result<(), ActionError> {
        let card = self.card(id)?;
        if card.location.seat == seat || card.owner == seat {
            return Ok(());
        }
        Err(ActionError::NotYourCard)
    }

    fn ensure_visible_to_actor(&self, seat: SeatId, id: CardId) -> Result<(), ActionError> {
        let card = self.card(id)?;
        if card.location.seat == seat && card.location.zone != ZoneKind::Library {
            return Ok(());
        }
        if card.location.zone.is_public() && !card.face_down {
            return Ok(());
        }
        Err(ActionError::NotYourCard)
    }

    fn insert_into_zone(&mut self, id: CardId, card_move: &CardMove) -> Result<(), ActionError> {
        let zone = self.zone_mut(card_move.to_seat, card_move.to_zone);
        match &card_move.position {
            MovePosition::Top => zone.insert(0, id),
            MovePosition::Bottom => zone.push(id),
            MovePosition::Index(index) => {
                let index = usize::try_from(*index)
                    .map_err(|_| ActionError::InvalidArgument("index is too large".to_owned()))?;
                if index > zone.len() {
                    return Err(ActionError::WrongZone);
                }
                zone.insert(index, id);
            }
            MovePosition::Battlefield { .. } => zone.push(id),
        }
        Ok(())
    }

    fn remove_from_zone(&mut self, id: CardId) -> Result<(), ActionError> {
        let location = self.card(id)?.location;
        let zone = self.zone_mut(location.seat, location.zone);
        let index = zone
            .iter()
            .position(|candidate| *candidate == id)
            .ok_or(ActionError::WrongZone)?;
        zone.remove(index);
        Ok(())
    }

    fn zone_mut(&mut self, seat: SeatId, zone: ZoneKind) -> &mut Vec<CardId> {
        let player = &mut self.players[seat.index()];
        match zone {
            ZoneKind::Library => &mut player.library,
            ZoneKind::Hand => &mut player.hand,
            ZoneKind::Battlefield => &mut player.battlefield,
            ZoneKind::Graveyard => &mut player.graveyard,
            ZoneKind::Exile => &mut player.exile,
        }
    }

    fn zone(&self, seat: SeatId, zone: ZoneKind) -> &[CardId] {
        let player = &self.players[seat.index()];
        match zone {
            ZoneKind::Library => &player.library,
            ZoneKind::Hand => &player.hand,
            ZoneKind::Battlefield => &player.battlefield,
            ZoneKind::Graveyard => &player.graveyard,
            ZoneKind::Exile => &player.exile,
        }
    }

    fn card(&self, id: CardId) -> Result<&CardInstance, ActionError> {
        self.cards.get(&id).ok_or(ActionError::UnknownCard)
    }

    fn card_mut(&mut self, id: CardId) -> Result<&mut CardInstance, ActionError> {
        self.cards.get_mut(&id).ok_or(ActionError::UnknownCard)
    }

    fn life_totals(&self) -> [i32; 2] {
        [
            *self.players[0].counters.get("life").unwrap_or(&0),
            *self.players[1].counters.get("life").unwrap_or(&0),
        ]
    }

    fn player_snapshot(&self, seat: SeatId, perspective: Perspective) -> PlayerSnapshot {
        let player = &self.players[seat.index()];
        PlayerSnapshot {
            seat,
            name: player.name.clone(),
            counters: player.counters.clone(),
            mulligan_count: player.mulligan_count,
            library_count: player.library.len() as u32,
            hand: self.zone_refs(seat, ZoneKind::Hand, perspective),
            battlefield: self.zone_refs(seat, ZoneKind::Battlefield, perspective),
            graveyard: self.zone_refs(seat, ZoneKind::Graveyard, perspective),
            exile: self.zone_refs(seat, ZoneKind::Exile, perspective),
            arrows: player
                .arrows
                .iter()
                .map(|(from, to)| Arrow {
                    from: *from,
                    to: *to,
                })
                .collect(),
        }
    }

    fn zone_refs(&self, seat: SeatId, zone: ZoneKind, perspective: Perspective) -> Vec<CardRef> {
        self.zone(seat, zone)
            .iter()
            .filter_map(|id| self.cards.get(id))
            .map(|card| card_ref_for_zone(&card.view(), ZoneRef { seat, zone }, perspective))
            .collect()
    }

    fn emit(&mut self, actor: Option<SeatId>, event: Event) {
        self.log.push(LoggedEvent {
            seq: Seq(self.seq),
            turn: self.turn,
            phase: self.phase,
            actor,
            event,
        });
        self.seq += 1;
    }
}

impl PlayerState {
    fn new(name: String, starting_life: i32) -> Self {
        let mut counters = BTreeMap::new();
        counters.insert("life".to_owned(), starting_life);
        Self {
            name,
            counters,
            mulligan_count: 0,
            library: Vec::new(),
            hand: Vec::new(),
            battlefield: Vec::new(),
            graveyard: Vec::new(),
            exile: Vec::new(),
            arrows: BTreeMap::new(),
        }
    }
}
