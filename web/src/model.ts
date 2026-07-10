import {
  type CardId,
  type CardRef,
  type CardView,
  type Expectation,
  type Phase,
  type SeatId,
  type Snapshot,
  cardId,
  knownCard
} from "./protocol";

export const phases: Array<{ phase: Phase; short: string; label: string }> = [
  { phase: "untap", short: "U", label: "Untap" },
  { phase: "upkeep", short: "UK", label: "Upkeep" },
  { phase: "draw", short: "D", label: "Draw" },
  { phase: "main1", short: "M1", label: "Main 1" },
  { phase: "begin_combat", short: "BC", label: "Begin Combat" },
  { phase: "declare_attackers", short: "A", label: "Declare Attackers" },
  { phase: "declare_blockers", short: "B", label: "Declare Blockers" },
  { phase: "combat_damage", short: "CD", label: "Combat Damage" },
  { phase: "end_combat", short: "EC", label: "End Combat" },
  { phase: "main2", short: "M2", label: "Main 2" },
  { phase: "end", short: "E", label: "End" }
];

export type ViewMode = "player" | "global" | "replay";

export interface ClockState {
  ms: number | null;
}

export interface TableModel {
  mode: ViewMode;
  viewerSlot: SeatId | null;
  snapshot: Snapshot | null;
  top: PlayerModel | null;
  bottom: PlayerModel | null;
  players: [PlayerModel, PlayerModel] | null;
  hand: CardModel[];
  phase: Phase | null;
  active: SeatId | null;
  turn: number | null;
  expectation: Expectation | null;
  canAct: boolean;
  awaitingAck: boolean;
  banner: BannerModel;
  clocks: [ClockState, ClockState];
}

export interface BannerModel {
  tone: "mine" | "opponent" | "neutral" | "danger";
  text: string;
}

export interface PlayerModel {
  seat: SeatId;
  name: string;
  life: number;
  mulliganCount: number;
  libraryCount: number;
  handCount: number;
  graveyardCount: number;
  exileCount: number;
  battlefield: BattlefieldModel;
  arrows: Array<{ from: CardId; to: CardId | null }>;
}

export interface BattlefieldModel {
  lands: CardModel[];
  creatures: CardModel[];
}

export interface CardModel {
  id: CardId;
  ref: CardRef;
  known: boolean;
  view: CardView | null;
  name: string;
  typeLine: string;
  manaCost: string | null;
  oracleText: string;
  powerToughness: string | null;
  tapped: boolean;
  attacking: boolean;
  faceDown: boolean;
  counters: Record<string, number>;
  annotation: string | null;
  kind: "land" | "creature" | "other" | "hidden";
  x: number;
  y: number;
}

export interface ModelOptions {
  mode: ViewMode;
  viewerSlot?: SeatId | null;
  awaitingAck?: boolean;
  clocks?: [ClockState, ClockState];
}

export function snapshotToTableModel(snapshot: Snapshot | null, options: ModelOptions): TableModel {
  const viewerSlot = options.viewerSlot ?? null;
  const awaitingAck = options.awaitingAck ?? false;
  const clocks = options.clocks ?? [{ ms: null }, { ms: null }];
  if (!snapshot) {
    return {
      mode: options.mode,
      viewerSlot,
      snapshot,
      top: null,
      bottom: null,
      players: null,
      hand: [],
      phase: null,
      active: null,
      turn: null,
      expectation: null,
      canAct: false,
      awaitingAck,
      banner: { tone: "neutral", text: "Connecting..." },
      clocks
    };
  }

  const players = snapshot.players.map((player) => playerToModel(player)) as [PlayerModel, PlayerModel];
  const bottomSeat = viewerSlot ?? 0;
  const topSeat = bottomSeat === 0 ? 1 : 0;
  const hand =
    options.mode === "player" && viewerSlot !== null
      ? snapshot.players[viewerSlot].hand.map((card, index) => cardToModel(card, index))
      : [];
  const expectationSeat = actorSeat(snapshot.expectation);
  const isOwnWindow =
    options.mode === "player" &&
    viewerSlot !== null &&
    expectationSeat === viewerSlot &&
    snapshot.expectation.type !== "game_over";
  const canAct = isOwnWindow && !awaitingAck;

  return {
    mode: options.mode,
    viewerSlot,
    snapshot,
    top: players[topSeat],
    bottom: players[bottomSeat],
    players,
    hand,
    phase: snapshot.phase,
    active: snapshot.active,
    turn: snapshot.turn,
    expectation: snapshot.expectation,
    canAct,
    awaitingAck,
    banner: bannerFor(snapshot, options.mode, viewerSlot, awaitingAck),
    clocks
  };
}

export function nextBattlefieldPosition(snapshot: Snapshot, seat: SeatId, card: CardView | null): { x: number; y: number } {
  const row = card && isLand(card) ? 0 : 1;
  const xs = snapshot.players[seat].battlefield
    .map(knownCard)
    .filter((view): view is CardView => Boolean(view))
    .filter((view) => (isLand(view) ? 0 : 1) === row)
    .map((view) => view.x ?? 0);
  return { x: xs.length === 0 ? 0 : Math.max(...xs) + 1, y: row };
}

export function cardById(snapshot: Snapshot, id: CardId): CardModel | null {
  for (const player of snapshot.players) {
    for (const zone of [player.hand, player.battlefield, player.graveyard, player.exile]) {
      const ref = zone.find((card) => cardId(card) === id);
      if (ref) {
        return cardToModel(ref, 0);
      }
    }
  }
  return null;
}

export function allKnownBattlefieldCards(snapshot: Snapshot, seat: SeatId): CardView[] {
  return snapshot.players[seat].battlefield
    .map(knownCard)
    .filter((view): view is CardView => Boolean(view));
}

export function isLand(card: CardView): boolean {
  return /\bLand\b/.test(card.spec.type_line);
}

export function isCreature(card: CardView): boolean {
  return /\bCreature\b/.test(card.spec.type_line);
}

export function phaseLabel(phase: Phase | null): string {
  return phases.find((item) => item.phase === phase)?.label ?? "Waiting";
}

function playerToModel(player: Snapshot["players"][number]): PlayerModel {
  const battlefieldCards = player.battlefield.map((card, index) => cardToModel(card, index));
  const lands = battlefieldCards
    .filter((card) => card.kind === "land")
    .sort(cardSort);
  const creatures = battlefieldCards
    .filter((card) => card.kind !== "land")
    .sort(cardSort);
  return {
    seat: player.seat,
    name: player.name,
    life: player.counters.life ?? 0,
    mulliganCount: player.mulligan_count,
    libraryCount: player.library_count,
    handCount: player.hand.length,
    graveyardCount: player.graveyard.length,
    exileCount: player.exile.length,
    battlefield: { lands, creatures },
    arrows: player.arrows
  };
}

export function cardToModel(ref: CardRef, index: number): CardModel {
  const view = knownCard(ref);
  if (!view || view.face_down) {
    return {
      id: cardId(ref),
      ref,
      known: Boolean(view),
      view,
      name: "Face-down card",
      typeLine: "Hidden",
      manaCost: null,
      oracleText: "",
      powerToughness: null,
      tapped: view?.tapped ?? false,
      attacking: view?.attacking ?? false,
      faceDown: true,
      counters: view?.counters ?? {},
      annotation: view?.annotation ?? null,
      kind: "hidden",
      x: view?.x ?? index,
      y: view?.y ?? 1
    };
  }
  const kind = isLand(view) ? "land" : isCreature(view) ? "creature" : "other";
  return {
    id: view.id,
    ref,
    known: true,
    view,
    name: view.spec.name,
    typeLine: view.spec.type_line,
    manaCost: view.spec.mana_cost,
    oracleText: view.spec.oracle_text,
    powerToughness: view.pt_override ?? view.spec.power_toughness,
    tapped: view.tapped,
    attacking: view.attacking,
    faceDown: false,
    counters: view.counters,
    annotation: view.annotation,
    kind,
    x: view.x ?? index,
    y: view.y ?? (kind === "land" ? 0 : 1)
  };
}

function cardSort(left: CardModel, right: CardModel): number {
  return left.x - right.x || left.y - right.y || left.id - right.id;
}

function bannerFor(snapshot: Snapshot, mode: ViewMode, viewerSlot: SeatId | null, awaitingAck: boolean): BannerModel {
  const expectation = snapshot.expectation;
  if (expectation.type === "game_over") {
    return { tone: "danger", text: `Game over - ${expectation.outcome.reason.replaceAll("_", " ")}` };
  }
  const seat = actorSeat(expectation);
  const phase = phaseLabel(snapshot.phase);
  if (mode !== "player" || viewerSlot === null) {
    return seat === null
      ? { tone: "neutral", text: "Waiting for game state..." }
      : { tone: "neutral", text: `${snapshot.players[seat].name} acting - ${phase}` };
  }
  if (seat === viewerSlot) {
    if (awaitingAck) {
      return { tone: "mine", text: "Action sent - waiting for table" };
    }
    if (expectation.type === "reaction_window") {
      return { tone: "mine", text: `Reaction window: respond or pass - ${phase}` };
    }
    if (expectation.type === "mulligan") {
      return { tone: "mine", text: `Your mulligan decision - keep ${expectation.keeping_hand_of}` };
    }
    return { tone: "mine", text: `Your window - ${phase}` };
  }
  if (expectation.type === "reaction_window") {
    return { tone: "opponent", text: "Opponent responding..." };
  }
  if (expectation.type === "mulligan") {
    return { tone: "opponent", text: "Opponent choosing mulligan..." };
  }
  return { tone: "opponent", text: "Opponent acting..." };
}

function actorSeat(expectation: Expectation): SeatId | null {
  return expectation.type === "game_over" ? null : expectation.seat;
}
