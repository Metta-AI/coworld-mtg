import {
  type CardAttr,
  type CardId,
  type CardRef,
  type CardView,
  type Event,
  type LoggedEvent,
  type MovePosition,
  type SeatId,
  type Snapshot,
  type ZoneRef,
  cardId,
  knownCard
} from "./protocol";

export function cloneSnapshot(snapshot: Snapshot): Snapshot {
  return JSON.parse(JSON.stringify(snapshot)) as Snapshot;
}

export function applyLoggedEvents(snapshot: Snapshot, events: LoggedEvent[]): Snapshot {
  const next = cloneSnapshot(snapshot);
  const snapshotSeq = snapshot.seq;
  for (const logged of events) {
    if (logged.seq <= snapshotSeq) {
      continue;
    }
    next.seq = logged.seq;
    next.turn = logged.turn;
    next.phase = logged.phase;
    applyEvent(next, logged.event);
  }
  return next;
}

export function snapshotFromEvents(events: LoggedEvent[], deckSize = 40): Snapshot | null {
  let snapshot: Snapshot | null = null;
  for (const logged of events) {
    if (!snapshot && logged.event.type !== "game_started") {
      continue;
    }
    if (!snapshot) {
      const event = logged.event;
      if (event.type !== "game_started") {
        continue;
      }
      snapshot = {
        seq: logged.seq,
        turn: logged.turn,
        phase: logged.phase,
        active: 0,
        expectation: { type: "main_window", seat: 0 },
        players: [
          emptyPlayer(0, event.players[0], event.starting_life, deckSize),
          emptyPlayer(1, event.players[1], event.starting_life, deckSize)
        ]
      };
    }
    snapshot.seq = logged.seq;
    snapshot.turn = logged.turn;
    snapshot.phase = logged.phase;
    applyEvent(snapshot, logged.event);
  }
  return snapshot;
}

export function applyEvent(snapshot: Snapshot, event: Event): void {
  switch (event.type) {
    case "game_started":
      snapshot.players[0].name = event.players[0];
      snapshot.players[1].name = event.players[1];
      snapshot.players[0].counters.life = event.starting_life;
      snapshot.players[1].counters.life = event.starting_life;
      break;
    case "hand_dealt":
    case "drew":
      moveDrawnCards(snapshot, event.seat, event.cards);
      break;
    case "cards_moved":
      for (const move of event.moves) {
        if (move.from.zone === "library") {
          snapshot.players[move.from.seat].library_count = Math.max(0, snapshot.players[move.from.seat].library_count - 1);
        } else {
          removeVisibleCard(snapshot, cardId(move.card));
        }
        insertCard(snapshot, move.to, move.position, move.card);
      }
      break;
    case "attr_set":
      updateCard(snapshot, cardId(event.card), (card) => applyAttr(card, event.attr));
      break;
    case "token_created":
      insertCard(snapshot, event.zone, { battlefield: { x: knownCard(event.card)?.x ?? 0, y: knownCard(event.card)?.y ?? 1 } }, event.card);
      break;
    case "token_removed":
      removeVisibleCard(snapshot, cardId(event.card));
      break;
    case "counter_changed":
      if (event.target.type === "player") {
        snapshot.players[event.target.seat].counters[event.name] = event.new;
      } else {
        updateCard(snapshot, cardId(event.target.card), (card) => {
          card.counters[event.name] = event.new;
        });
      }
      break;
    case "revealed":
      for (const card of event.cards) {
        replaceCard(snapshot, card);
      }
      break;
    case "pointed":
      snapshot.players[event.seat].arrows = snapshot.players[event.seat].arrows.filter((arrow) => arrow.from !== event.from);
      snapshot.players[event.seat].arrows.push({ from: event.from, to: event.to });
      break;
    case "phase_changed":
      snapshot.phase = event.phase;
      break;
    case "turn_changed":
      snapshot.turn = event.turn;
      snapshot.active = event.active;
      break;
    case "window_opened":
      snapshot.expectation = event.expectation;
      break;
    case "mulligan_resolved":
      snapshot.players[event.seat].mulligan_count = event.mulligan_count;
      break;
    case "game_ended":
      snapshot.expectation = { type: "game_over", outcome: event.outcome };
      break;
    case "shuffled":
    case "die_rolled":
    case "said":
    case "passed":
      break;
  }
}

function emptyPlayer(seat: SeatId, name: string, life: number, deckSize: number): Snapshot["players"][number] {
  return {
    seat,
    name,
    counters: { life },
    mulligan_count: 0,
    library_count: deckSize,
    hand: [],
    battlefield: [],
    graveyard: [],
    exile: [],
    arrows: []
  };
}

function moveDrawnCards(snapshot: Snapshot, seat: SeatId, cards: CardRef[]): void {
  const player = snapshot.players[seat];
  player.library_count = Math.max(0, player.library_count - cards.length);
  for (const card of cards) {
    removeVisibleCard(snapshot, cardId(card));
    player.hand.push(card);
  }
}

function insertCard(snapshot: Snapshot, zone: ZoneRef, position: MovePosition, card: CardRef): void {
  if (zone.zone === "library") {
    snapshot.players[zone.seat].library_count += 1;
    return;
  }
  const cards = zoneCards(snapshot, zone);
  if (!cards) {
    return;
  }
  if (position === "top") {
    cards.unshift(card);
  } else if (position === "bottom" || isBattlefieldPosition(position)) {
    cards.push(card);
  } else {
    cards.splice(Math.min(position.index, cards.length), 0, card);
  }
}

function isBattlefieldPosition(position: MovePosition): position is { battlefield: { x: number; y: number } } {
  return typeof position === "object" && "battlefield" in position;
}

function replaceCard(snapshot: Snapshot, card: CardRef): void {
  const id = cardId(card);
  for (const player of snapshot.players) {
    for (const zone of [player.hand, player.battlefield, player.graveyard, player.exile]) {
      const index = zone.findIndex((candidate) => cardId(candidate) === id);
      if (index >= 0) {
        zone[index] = card;
      }
    }
  }
}

function removeVisibleCard(snapshot: Snapshot, id: CardId): void {
  for (const player of snapshot.players) {
    for (const zone of [player.hand, player.battlefield, player.graveyard, player.exile]) {
      const index = zone.findIndex((card) => cardId(card) === id);
      if (index >= 0) {
        zone.splice(index, 1);
        return;
      }
    }
  }
}

function updateCard(snapshot: Snapshot, id: CardId, update: (card: CardView) => void): void {
  for (const player of snapshot.players) {
    for (const zone of [player.hand, player.battlefield, player.graveyard, player.exile]) {
      for (const ref of zone) {
        const card = knownCard(ref);
        if (card?.id === id) {
          update(card);
        }
      }
    }
  }
}

function zoneCards(snapshot: Snapshot, zone: ZoneRef): CardRef[] | null {
  const player = snapshot.players[zone.seat];
  switch (zone.zone) {
    case "hand":
      return player.hand;
    case "battlefield":
      return player.battlefield;
    case "graveyard":
      return player.graveyard;
    case "exile":
      return player.exile;
    case "library":
      return null;
  }
}

function applyAttr(card: CardView, attr: CardAttr): void {
  switch (attr.type) {
    case "tapped":
      card.tapped = attr.value;
      break;
    case "face_down":
      card.face_down = attr.value;
      break;
    case "attacking":
      card.attacking = attr.value;
      break;
    case "pt_override":
      card.pt_override = attr.value;
      break;
    case "annotation":
      card.annotation = attr.value;
      break;
  }
}
