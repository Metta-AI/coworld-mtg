use anyhow::{anyhow, Result};
use futures::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeSet, VecDeque};
use tabletop_core::{
    Action, CardAttr, CardId, CardMove, CardRef, CardView, CounterTarget, Event, Expectation,
    LoggedEvent, MovePosition, Phase, SeatId, Snapshot, ZoneKind,
};
use tokio_tungstenite::tungstenite::Message;

#[derive(Clone, Debug, Default)]
pub struct GoldfishReport {
    pub hellos: Vec<HelloReport>,
    pub leaked_opponent_hand: bool,
    pub match_scores: Option<[f64; 2]>,
}

#[derive(Clone, Debug)]
pub struct HelloReport {
    pub slot: usize,
    pub deck_name: String,
    pub deck_size: usize,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
enum ServerFrame {
    Hello {
        slot: usize,
        decklist: tabletop_core::DeckList,
    },
    Snapshot {
        state: Box<Snapshot>,
    },
    Events {
        events: Vec<LoggedEvent>,
    },
    Window {
        expectation: Expectation,
    },
    Ack {
        cmd_id: u64,
    },
    Reject {
        cmd_id: u64,
        error: RejectError,
    },
    GameEnd,
    MatchEnd {
        scores: [f64; 2],
    },
}

#[derive(Debug, Deserialize)]
struct RejectError {
    kind: String,
    detail: String,
}

#[derive(Serialize)]
struct ClientCommand {
    cmd_id: u64,
    action: Action,
}

pub async fn run_url(url: &str) -> Result<GoldfishReport> {
    let (stream, _) = tokio_tungstenite::connect_async(url).await?;
    let (mut write, mut read) = stream.split();
    let mut bot = Bot::default();

    while let Some(message) = read.next().await {
        let message = message?;
        let Message::Text(text) = message else {
            continue;
        };
        let frame = serde_json::from_str::<ServerFrame>(&text)?;
        let actions = bot.handle_frame(frame)?;
        for action in actions {
            let text = bot.command_text(action)?;
            write.send(Message::Text(text.into())).await?;
        }
        if bot.done {
            return Ok(bot.report);
        }
    }
    Err(anyhow!("connection closed before match_end"))
}

pub fn mana_value(cost: Option<&str>) -> u32 {
    let Some(cost) = cost else {
        return 0;
    };
    let mut total = 0;
    for symbol in cost.split('{').skip(1).filter_map(|part| part.split('}').next()) {
        total += symbol.parse::<u32>().unwrap_or_else(|_| {
            if symbol.is_empty() || symbol == "X" {
                0
            } else {
                1
            }
        });
    }
    total
}

pub fn power(card: &CardView) -> i32 {
    card.pt_override
        .as_deref()
        .or(card.spec.power_toughness.as_deref())
        .and_then(|pt| pt.split('/').next())
        .and_then(|value| value.parse::<i32>().ok())
        .unwrap_or(0)
}

pub fn mulligan_bottom(hand: &[CardRef], must_bottom: u8) -> Vec<CardId> {
    let mut ids: Vec<_> = hand
        .iter()
        .filter_map(|card| match card {
            CardRef::Known(view) => Some(view.id),
            CardRef::Hidden { .. } => None,
        })
        .collect();
    ids.sort();
    ids.into_iter().take(usize::from(must_bottom)).collect()
}

pub fn select_attackers(cards: &[CardView], entered_this_turn: &BTreeSet<CardId>) -> Vec<CardId> {
    cards
        .iter()
        .filter(|card| is_creature(card) && !card.tapped && !entered_this_turn.contains(&card.id))
        .map(|card| card.id)
        .collect()
}

#[derive(Default)]
struct Bot {
    slot: Option<usize>,
    snapshot: Option<Snapshot>,
    entered_this_turn: BTreeSet<CardId>,
    pending: VecDeque<Action>,
    next_cmd_id: u64,
    awaiting_ack: bool,
    done: bool,
    last_phase_changed: Option<Phase>,
    damage_applied_for_combat: bool,
    phase_plan: Option<Phase>,
    land_played_this_phase: bool,
    report: GoldfishReport,
}

impl Bot {
    fn handle_frame(&mut self, frame: ServerFrame) -> Result<Vec<Action>> {
        match frame {
            ServerFrame::Hello { slot, decklist } => {
                self.slot = Some(slot);
                self.report.hellos.push(HelloReport {
                    slot,
                    deck_name: decklist.name,
                    deck_size: decklist.cards.len(),
                });
                Ok(Vec::new())
            }
            ServerFrame::Snapshot { state } => {
                self.report.leaked_opponent_hand |= opponent_hand_has_known(self.slot, &state);
                self.snapshot = Some(*state);
                Ok(Vec::new())
            }
            ServerFrame::Events { events } => {
                self.apply_events(&events);
                Ok(Vec::new())
            }
            ServerFrame::Window { expectation } => {
                if let Some(snapshot) = &mut self.snapshot {
                    snapshot.expectation = expectation;
                }
                self.plan_for_window();
                Ok(self.drain_ready_actions())
            }
            ServerFrame::Ack { cmd_id } => {
                let _ = cmd_id;
                self.awaiting_ack = false;
                self.plan_after_ack();
                Ok(self.drain_ready_actions())
            }
            ServerFrame::Reject { cmd_id, error } => {
                self.awaiting_ack = false;
                self.pending.clear();
                self.plan_reject_fallback(cmd_id, &error);
                Ok(self.drain_ready_actions())
            }
            ServerFrame::GameEnd => {
                self.snapshot = None;
                self.pending.clear();
                self.awaiting_ack = false;
                self.entered_this_turn.clear();
                self.phase_plan = None;
                self.damage_applied_for_combat = false;
                Ok(Vec::new())
            }
            ServerFrame::MatchEnd { scores } => {
                self.report.match_scores = Some(scores);
                self.done = true;
                Ok(Vec::new())
            }
        }
    }

    fn command_text(&mut self, action: Action) -> Result<String> {
        let cmd_id = self.next_cmd_id;
        self.next_cmd_id += 1;
        self.awaiting_ack = true;
        Ok(serde_json::to_string(&ClientCommand { cmd_id, action })?)
    }

    fn drain_ready_actions(&mut self) -> Vec<Action> {
        if self.awaiting_ack {
            return Vec::new();
        }
        self.pending.pop_front().into_iter().collect()
    }

    fn plan_for_window(&mut self) {
        if self.awaiting_ack || !self.pending.is_empty() {
            return;
        }
        let Some(snapshot) = &self.snapshot else {
            return;
        };
        let Some(slot) = self.slot else {
            return;
        };
        match &snapshot.expectation {
            Expectation::Mulligan {
                seat, must_bottom, ..
            } if seat.index() == slot => {
                self.pending.push_back(Action::MulliganKeep {
                    bottom: mulligan_bottom(&snapshot.players[slot].hand, *must_bottom),
                });
            }
            Expectation::MainWindow { seat } if seat.index() == slot => {
                self.plan_main_action();
            }
            Expectation::ReactionWindow { seat, .. } if seat.index() == slot => {
                self.plan_reaction_action();
            }
            _ => {}
        }
    }

    fn plan_after_ack(&mut self) {
        if self.pending.is_empty() {
            self.plan_for_window();
        }
    }

    fn plan_reject_fallback(&mut self, cmd_id: u64, error: &RejectError) {
        let Some(snapshot) = &self.snapshot else {
            return;
        };
        let detail = format!("reject {cmd_id}: {} {}", error.kind, error.detail);
        match snapshot.expectation {
            Expectation::ReactionWindow { .. } => self.pending.push_back(Action::Pass),
            Expectation::MainWindow { .. } => {
                self.pending.push_back(Action::Say { text: detail });
                self.pending.push_back(advance_action(snapshot.phase));
            }
            Expectation::Mulligan { must_bottom, .. } => {
                let Some(slot) = self.slot else {
                    return;
                };
                self.pending.push_back(Action::MulliganKeep {
                    bottom: mulligan_bottom(&snapshot.players[slot].hand, must_bottom),
                });
            }
            Expectation::GameOver { .. } => {}
        }
    }

    fn plan_main_action(&mut self) {
        let Some(snapshot) = &self.snapshot else {
            return;
        };
        if self.phase_plan != Some(snapshot.phase) {
            self.phase_plan = Some(snapshot.phase);
            self.land_played_this_phase = false;
        }
        match snapshot.phase {
            Phase::Untap => self.plan_untap(),
            Phase::Upkeep => self.pending.push_back(Action::NextPhase),
            Phase::Draw => self.plan_draw(),
            Phase::Main1 => self.plan_main1(),
            Phase::BeginCombat => self.pending.push_back(Action::NextPhase),
            Phase::DeclareAttackers => self.plan_attackers(),
            Phase::DeclareBlockers => self.pending.push_back(Action::NextPhase),
            Phase::CombatDamage => self.plan_combat_damage(),
            Phase::EndCombat => self.plan_end_combat(),
            Phase::Main2 => self.pending.push_back(Action::NextPhase),
            Phase::End => self.pending.push_back(Action::NextTurn),
        }
    }

    fn plan_untap(&mut self) {
        for card in self.own_battlefield().into_iter().filter(|card| card.tapped) {
            self.pending.push_back(Action::SetCardAttr {
                card: card.id,
                attr: CardAttr::Tapped { value: false },
            });
        }
        self.pending.push_back(Action::NextPhase);
    }

    fn plan_draw(&mut self) {
        let Some(snapshot) = &self.snapshot else {
            return;
        };
        if !(snapshot.turn == 1 && self.slot == Some(0)) {
            self.pending.push_back(Action::Draw { count: 1 });
        }
        self.pending.push_back(Action::NextPhase);
    }

    fn plan_main1(&mut self) {
        if !self.land_played_this_phase {
            if let Some(land) = self.own_hand().into_iter().find(is_land) {
                self.land_played_this_phase = true;
                let Some(slot) = self.slot else {
                    return;
                };
                self.pending
                    .push_back(move_to_battlefield(land.id, self.battlefield_x(), slot));
                self.pending.push_back(Action::Say {
                    text: format!("plays {}", land.spec.name),
                });
                return;
            }
            self.land_played_this_phase = true;
        }
        if self.plan_cast_creature() {
            return;
        }
        self.pending.push_back(Action::NextPhase);
    }

    fn plan_cast_creature(&mut self) -> bool {
        let lands: Vec<_> = self
            .own_battlefield()
            .into_iter()
            .filter(|card| is_land(card) && !card.tapped)
            .collect();
        let available = lands.len() as u32;
        let Some(creature) = self
            .own_hand()
            .into_iter()
            .filter(is_creature)
            .find(|card| mana_value(card.spec.mana_cost.as_deref()) <= available)
        else {
            return false;
        };
        let cost = mana_value(creature.spec.mana_cost.as_deref()) as usize;
        for land in lands.into_iter().take(cost) {
            self.pending.push_back(Action::SetCardAttr {
                card: land.id,
                attr: CardAttr::Tapped { value: true },
            });
        }
        let Some(slot) = self.slot else {
            return false;
        };
        self.pending
            .push_back(move_to_battlefield(creature.id, self.battlefield_x(), slot));
        self.pending.push_back(Action::Say {
            text: format!("casts {}", creature.spec.name),
        });
        true
    }

    fn plan_attackers(&mut self) {
        let attackers = select_attackers(&self.own_battlefield(), &self.entered_this_turn);
        for card in &attackers {
            self.pending.push_back(Action::SetCardAttr {
                card: *card,
                attr: CardAttr::Attacking { value: true },
            });
        }
        if !attackers.is_empty() {
            self.pending.push_back(Action::Say {
                text: format!("attacks with {}", attackers.len()),
            });
        }
        self.pending.push_back(Action::NextPhase);
    }

    fn plan_combat_damage(&mut self) {
        let total: i32 = self
            .own_battlefield()
            .iter()
            .filter(|card| card.attacking)
            .map(power)
            .sum();
        self.pending.push_back(Action::Say {
            text: format!("combat damage: {total}"),
        });
        self.pending.push_back(Action::NextPhase);
    }

    fn plan_end_combat(&mut self) {
        for card in self
            .own_battlefield()
            .into_iter()
            .filter(|card| card.attacking)
        {
            self.pending.push_back(Action::SetCardAttr {
                card: card.id,
                attr: CardAttr::Attacking { value: false },
            });
        }
        self.pending.push_back(Action::NextPhase);
    }

    fn plan_reaction_action(&mut self) {
        if self.last_phase_changed == Some(Phase::CombatDamage) && !self.damage_applied_for_combat {
            let damage: i32 = self
                .opponent_battlefield()
                .iter()
                .filter(|card| card.attacking)
                .map(power)
                .sum();
            if damage > 0 {
                self.damage_applied_for_combat = true;
                let Some(slot) = self.slot else {
                    return;
                };
                self.pending.push_back(Action::AddCounter {
                    target: CounterTarget::Player {
                        seat: SeatId(slot as u8),
                    },
                    name: "life".to_owned(),
                    delta: -damage,
                });
                return;
            }
        }
        self.pending.push_back(Action::Pass);
    }

    fn apply_events(&mut self, events: &[LoggedEvent]) {
        for event in events {
            self.apply_event(&event.event);
        }
    }

    fn apply_event(&mut self, event: &Event) {
        let Some(snapshot) = &mut self.snapshot else {
            return;
        };
        match event {
            Event::HandDealt { seat, cards } | Event::Drew { seat, cards } => {
                let player = &mut snapshot.players[seat.index()];
                player.library_count = player.library_count.saturating_sub(cards.len() as u32);
                player.hand.extend(cards.iter().cloned());
            }
            Event::CardsMoved { moves } => {
                for move_event in moves {
                    remove_card(snapshot, card_id(&move_event.card));
                    insert_card(snapshot, move_event.to, move_event.position.clone(), move_event.card.clone());
                    if move_event.to.zone == ZoneKind::Battlefield
                        && self.slot == Some(move_event.to.seat.index())
                    {
                        self.entered_this_turn.insert(card_id(&move_event.card));
                    }
                }
            }
            Event::AttrSet { card, attr, .. } => {
                apply_attr(snapshot, card_id(card), attr);
            }
            Event::CounterChanged {
                target: tabletop_core::CounterTargetRef::Player { seat },
                name,
                new,
                ..
            } => {
                snapshot.players[seat.index()].counters.insert(name.clone(), *new);
            }
            Event::PhaseChanged { phase } => {
                snapshot.phase = *phase;
                self.last_phase_changed = Some(*phase);
                if *phase != Phase::CombatDamage {
                    self.damage_applied_for_combat = false;
                }
            }
            Event::TurnChanged { turn, active } => {
                snapshot.turn = *turn;
                snapshot.active = *active;
                if self.slot == Some(active.index()) {
                    self.entered_this_turn.clear();
                }
            }
            Event::WindowOpened { expectation } => {
                snapshot.expectation = expectation.clone();
            }
            Event::MulliganResolved {
                seat,
                mulligan_count,
                ..
            } => {
                snapshot.players[seat.index()].mulligan_count = *mulligan_count;
            }
            Event::GameEnded { .. } => {}
            _ => {}
        }
        if self.slot.is_some() {
            self.report.leaked_opponent_hand |= opponent_hand_has_known(self.slot, snapshot);
        }
    }

    fn own_hand(&self) -> Vec<CardView> {
        self.slot_cards(|snapshot, slot| &snapshot.players[slot].hand)
    }

    fn own_battlefield(&self) -> Vec<CardView> {
        self.slot_cards(|snapshot, slot| &snapshot.players[slot].battlefield)
    }

    fn opponent_battlefield(&self) -> Vec<CardView> {
        let Some(slot) = self.slot else {
            return Vec::new();
        };
        let opponent = 1 - slot;
        self.snapshot
            .as_ref()
            .map(|snapshot| known_cards(&snapshot.players[opponent].battlefield))
            .unwrap_or_default()
    }

    fn slot_cards(&self, zone: impl Fn(&Snapshot, usize) -> &Vec<CardRef>) -> Vec<CardView> {
        let Some(slot) = self.slot else {
            return Vec::new();
        };
        self.snapshot
            .as_ref()
            .map(|snapshot| known_cards(zone(snapshot, slot)))
            .unwrap_or_default()
    }

    fn battlefield_x(&self) -> i16 {
        self.own_battlefield().len().min(i16::MAX as usize) as i16
    }
}

fn move_to_battlefield(card: CardId, x: i16, slot: usize) -> Action {
    Action::MoveCards {
        moves: vec![CardMove {
            card,
            to_seat: SeatId(slot as u8),
            to_zone: ZoneKind::Battlefield,
            position: MovePosition::Battlefield { x, y: 0 },
            face_down: Some(false),
            tapped: Some(false),
        }],
    }
}

fn advance_action(phase: Phase) -> Action {
    if phase == Phase::End {
        Action::NextTurn
    } else {
        Action::NextPhase
    }
}

fn known_cards(cards: &[CardRef]) -> Vec<CardView> {
    cards
        .iter()
        .filter_map(|card| match card {
            CardRef::Known(view) => Some(view.clone()),
            CardRef::Hidden { .. } => None,
        })
        .collect()
}

fn is_land(card: &CardView) -> bool {
    card.spec.type_line.contains("Land")
}

fn is_creature(card: &CardView) -> bool {
    card.spec.type_line.contains("Creature")
}

fn card_id(card: &CardRef) -> CardId {
    match card {
        CardRef::Known(view) => view.id,
        CardRef::Hidden { id } => *id,
    }
}

fn remove_card(snapshot: &mut Snapshot, id: CardId) {
    for player in &mut snapshot.players {
        remove_from_zone(&mut player.hand, id);
        remove_from_zone(&mut player.battlefield, id);
        remove_from_zone(&mut player.graveyard, id);
        remove_from_zone(&mut player.exile, id);
    }
}

fn remove_from_zone(cards: &mut Vec<CardRef>, id: CardId) {
    if let Some(index) = cards.iter().position(|card| card_id(card) == id) {
        cards.remove(index);
    }
}

fn insert_card(
    snapshot: &mut Snapshot,
    zone: tabletop_core::ZoneRef,
    position: MovePosition,
    card: CardRef,
) {
    let cards = match zone.zone {
        ZoneKind::Hand => &mut snapshot.players[zone.seat.index()].hand,
        ZoneKind::Battlefield => &mut snapshot.players[zone.seat.index()].battlefield,
        ZoneKind::Graveyard => &mut snapshot.players[zone.seat.index()].graveyard,
        ZoneKind::Exile => &mut snapshot.players[zone.seat.index()].exile,
        ZoneKind::Library => {
            snapshot.players[zone.seat.index()].library_count += 1;
            return;
        }
    };
    match position {
        MovePosition::Top => cards.insert(0, card),
        MovePosition::Bottom | MovePosition::Battlefield { .. } => cards.push(card),
        MovePosition::Index(index) => {
            let index = usize::try_from(index).unwrap_or(cards.len()).min(cards.len());
            cards.insert(index, card);
        }
    }
}

fn apply_attr(snapshot: &mut Snapshot, id: CardId, attr: &CardAttr) {
    for player in &mut snapshot.players {
        for zone in [
            &mut player.hand,
            &mut player.battlefield,
            &mut player.graveyard,
            &mut player.exile,
        ] {
            for card in zone.iter_mut() {
                let CardRef::Known(view) = card else {
                    continue;
                };
                if view.id != id {
                    continue;
                }
                match attr {
                    CardAttr::Tapped { value } => view.tapped = *value,
                    CardAttr::FaceDown { value } => view.face_down = *value,
                    CardAttr::Attacking { value } => view.attacking = *value,
                    CardAttr::PtOverride { value } => view.pt_override = value.clone(),
                    CardAttr::Annotation { value } => view.annotation = Some(value.clone()),
                }
            }
        }
    }
}

fn opponent_hand_has_known(slot: Option<usize>, snapshot: &Snapshot) -> bool {
    let Some(slot) = slot else {
        return false;
    };
    snapshot.players[1 - slot]
        .hand
        .iter()
        .any(|card| matches!(card, CardRef::Known(_)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;
    use tabletop_core::CardSpec;

    fn creature(id: u32, name: &str, cost: &str, pt: &str, tapped: bool) -> CardView {
        CardView {
            id: CardId(id),
            owner: SeatId(0),
            controller: SeatId(0),
            spec: CardSpec {
                name: name.to_owned(),
                type_line: "Creature".to_owned(),
                mana_cost: Some(cost.to_owned()),
                power_toughness: Some(pt.to_owned()),
                oracle_text: String::new(),
                art_id: None,
            },
            is_token: false,
            tapped,
            face_down: false,
            attacking: false,
            pt_override: None,
            annotation: None,
            counters: BTreeMap::new(),
            x: None,
            y: None,
        }
    }

    #[test]
    fn parses_mana_value() {
        assert_eq!(mana_value(Some("{2}{G}")), 3);
        assert_eq!(mana_value(Some("{G}{G}")), 2);
        assert_eq!(mana_value(Some("{10}")), 10);
        assert_eq!(mana_value(None), 0);
    }

    #[test]
    fn mulligan_bottoms_first_sorted_ids() {
        let hand = vec![
            CardRef::Known(creature(9, "A", "{1}", "1/1", false)),
            CardRef::Known(creature(2, "B", "{1}", "1/1", false)),
            CardRef::Known(creature(7, "C", "{1}", "1/1", false)),
        ];
        assert_eq!(mulligan_bottom(&hand, 2), vec![CardId(2), CardId(7)]);
    }

    #[test]
    fn attacker_selection_skips_summoning_sick_and_tapped() {
        let cards = vec![
            creature(1, "Ready", "{1}", "2/2", false),
            creature(2, "New", "{1}", "2/2", false),
            creature(3, "Tapped", "{1}", "2/2", true),
        ];
        let entered = BTreeSet::from([CardId(2)]);
        assert_eq!(select_attackers(&cards, &entered), vec![CardId(1)]);
    }
}
