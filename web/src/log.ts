import { type CardAttr, type CardRef, type Expectation, type LoggedEvent, type SeatId, cardId, knownCard } from "./protocol";
import { phaseLabel } from "./model";

export interface LogLine {
  seq: number;
  text: string;
  kind: "event" | "chat" | "error" | "procedural";
}

export interface LogNames {
  players?: [string, string];
  viewerSlot?: SeatId | null;
}

interface Subject {
  text: string;
  viewer: boolean;
}

export function eventToLogLine(logged: LoggedEvent, names: LogNames = {}): LogLine {
  const event = logged.event;
  const actor = logged.actor === null ? tableSubject() : seatSubject(logged.actor, names);
  switch (event.type) {
    case "game_started":
      return line(logged, "event", `${event.players[0]} vs ${event.players[1]} - starting life ${event.starting_life}`);
    case "hand_dealt":
      return line(logged, "event", drawCountSentence(seatSubject(event.seat, names), event.cards.length));
    case "window_opened":
      return line(logged, "procedural", windowSentence(event.expectation, names));
    case "drew":
      return line(logged, "event", drawCardSentence(seatSubject(event.seat, names), event.cards.length));
    case "cards_moved":
      return line(logged, "event", moveSentence(actor, event.moves.map((move) => cardName(move.card)), event.moves[0]?.to.zone));
    case "attr_set":
      return line(logged, "event", attrSentence(actor, cardName(event.card), event.attr));
    case "token_created":
      return line(logged, "event", `${subjectVerb(actor, "create", "creates")} ${cardName(event.card)}`);
    case "token_removed":
      return line(logged, "event", `${subjectVerb(actor, "remove", "removes")} ${cardName(event.card)}`);
    case "counter_changed":
      return line(logged, "event", counterSentence(event, names));
    case "shuffled":
      return line(logged, "event", subjectVerb(seatSubject(event.seat, names), "shuffle", "shuffles"));
    case "die_rolled":
      return line(logged, "event", `die roll: ${event.result} on d${event.sides}`);
    case "revealed":
      return line(logged, "event", `${subjectVerb(seatSubject(event.seat, names), "reveal", "reveals")} ${cardList(event.cards)}`);
    case "said":
      return line(logged, "chat", `${seatSubject(event.seat, names).text}: ${event.text}`);
    case "pointed":
      return line(logged, "event", `${subjectVerb(seatSubject(event.seat, names), "point", "points")} ${event.from} at ${event.to ?? "nothing"}`);
    case "passed":
      return line(logged, "procedural", subjectVerb(seatSubject(event.seat, names), "pass", "passes"));
    case "phase_changed":
      return line(logged, "procedural", `phase: ${phaseLabel(event.phase)}`);
    case "turn_changed":
      return line(logged, "procedural", activeSentence(event.turn, seatSubject(event.active, names)));
    case "mulligan_resolved":
      return line(logged, "event", mulliganSentence(seatSubject(event.seat, names), event.kept, event.bottomed));
    case "game_ended":
      return line(logged, "event", `game ended: ${event.outcome.reason.replaceAll("_", " ")}`);
  }
}

export function seatName(seat: SeatId, names: LogNames = {}): string {
  return seatSubject(seat, names).text;
}

function seatSubject(seat: SeatId, names: LogNames = {}): Subject {
  if (names.viewerSlot === seat) {
    return { text: "You", viewer: true };
  }
  if (names.viewerSlot !== undefined && names.viewerSlot !== null && names.viewerSlot !== seat) {
    return { text: names.players?.[seat] ?? "opponent", viewer: false };
  }
  return { text: names.players?.[seat] ?? `slot ${seat}`, viewer: false };
}

function tableSubject(): Subject {
  return { text: "table", viewer: false };
}

function line(logged: LoggedEvent, kind: LogLine["kind"], text: string): LogLine {
  return { seq: logged.seq, kind, text };
}

function windowSentence(expectation: Expectation, names: LogNames): string {
  switch (expectation.type) {
    case "mulligan":
      return `window: ${seatName(expectation.seat, names)} mulligan`;
    case "main_window":
      return `window: ${seatName(expectation.seat, names)} main`;
    case "reaction_window":
      return `window: ${seatName(expectation.seat, names)} reaction`;
    case "game_over":
      return "window: game over";
  }
}

function moveSentence(actor: Subject, cards: string[], toZone: string | undefined): string {
  const names = cards.length === 0 ? "cards" : cards.length === 1 ? cards[0] : `${cards.length} cards`;
  if (toZone === "battlefield") {
    return `${subjectVerb(actor, "move", "moves")} ${names} to the battlefield`;
  }
  if (toZone === "graveyard") {
    return `${subjectVerb(actor, "move", "moves")} ${names} to graveyard`;
  }
  if (toZone === "exile") {
    return `${subjectVerb(actor, "exile", "exiles")} ${names}`;
  }
  if (toZone === "hand") {
    return `${subjectVerb(actor, "return", "returns")} ${names} to hand`;
  }
  if (toZone === "library") {
    return `${subjectVerb(actor, "put", "puts")} ${names} into library`;
  }
  return `${subjectVerb(actor, "move", "moves")} ${names}`;
}

function attrSentence(actor: Subject, card: string, attr: CardAttr): string {
  switch (attr.type) {
    case "tapped":
      return `${subjectVerb(actor, attr.value ? "tap" : "untap", attr.value ? "taps" : "untaps")} ${card}`;
    case "face_down":
      return `${subjectVerb(actor, "turn", "turns")} ${card} ${attr.value ? "face down" : "face up"}`;
    case "attacking":
      return `${subjectVerb(actor, attr.value ? "attack with" : "remove from combat", attr.value ? "attacks with" : "removes from combat")} ${card}`;
    case "pt_override":
      return `${subjectVerb(actor, "set", "sets")} ${card} P/T to ${attr.value ?? "printed"}`;
    case "annotation":
      return `${subjectVerb(actor, "annotate", "annotates")} ${card}`;
  }
}

function counterSentence(
  event: Extract<LoggedEvent["event"], { type: "counter_changed" }>,
  names: LogNames
): string {
  if (event.target.type === "player") {
    const target = targetName(event.target.seat, names);
    if (event.name === "life") {
      return `${target} life ${event.old} -> ${event.new}`;
    }
    return `${target} ${event.name} ${event.old} -> ${event.new}`;
  }
  return `${cardName(event.target.card)} ${event.name} ${event.old} -> ${event.new}`;
}

function cardList(cards: CardRef[]): string {
  return cards.map(cardName).join(", ") || "nothing";
}

function cardName(card: CardRef): string {
  const view = knownCard(card);
  if (!view || view.face_down) {
    return `card ${cardId(card)}`;
  }
  return view.spec.name;
}

function plural(count: number, singular: string): string {
  return count === 1 ? `1 ${singular}` : `${count} ${singular}s`;
}

function subjectVerb(subject: Subject, secondPerson: string, thirdPerson: string): string {
  return `${subject.text} ${subject.viewer ? secondPerson : thirdPerson}`;
}

function drawCountSentence(subject: Subject, count: number): string {
  return `${subjectVerb(subject, "draw", "draws")} ${count}`;
}

function drawCardSentence(subject: Subject, count: number): string {
  return `${subjectVerb(subject, "draw", "draws")} ${plural(count, "card")}`;
}

function mulliganSentence(subject: Subject, kept: boolean, bottomed: number): string {
  if (kept) {
    return `${subjectVerb(subject, "keep", "keeps")}, bottoming ${bottomed}`;
  }
  return subjectVerb(subject, "mulligan", "mulligans");
}

function activeSentence(turn: number, active: Subject): string {
  return active.viewer ? `turn ${turn}: You are active` : `turn ${turn}: ${active.text} active`;
}

function targetName(seat: SeatId, names: LogNames): string {
  const subject = seatSubject(seat, names);
  return subject.viewer ? "Your" : subject.text;
}
