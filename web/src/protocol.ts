export type SeatId = 0 | 1;
export type CardId = number;
export type Seq = number;
export type ZoneKind = "library" | "hand" | "battlefield" | "graveyard" | "exile";
export type Phase =
  | "untap"
  | "upkeep"
  | "draw"
  | "main1"
  | "begin_combat"
  | "declare_attackers"
  | "declare_blockers"
  | "combat_damage"
  | "end_combat"
  | "main2"
  | "end";

export interface CardSpec {
  name: string;
  type_line: string;
  mana_cost: string | null;
  power_toughness: string | null;
  oracle_text: string;
  art_id: string | null;
}

export interface CardView {
  id: CardId;
  owner: SeatId;
  controller: SeatId;
  spec: CardSpec;
  is_token: boolean;
  tapped: boolean;
  face_down: boolean;
  attacking: boolean;
  pt_override: string | null;
  annotation: string | null;
  counters: Record<string, number>;
  x: number | null;
  y: number | null;
}

export type CardRef = { known: CardView } | { hidden: { id: CardId } };

export interface ZoneRef {
  seat: SeatId;
  zone: ZoneKind;
}

export type MovePosition = "top" | "bottom" | { index: number } | { battlefield: { x: number; y: number } };

export type CounterTarget =
  | { type: "card"; card: CardId }
  | { type: "player"; seat: SeatId };

export type CounterTargetRef =
  | { type: "card"; card: CardRef; zone: ZoneRef }
  | { type: "player"; seat: SeatId };

export type CardAttr =
  | { type: "tapped"; value: boolean }
  | { type: "face_down"; value: boolean }
  | { type: "attacking"; value: boolean }
  | { type: "pt_override"; value: string | null }
  | { type: "annotation"; value: string };

export type Expectation =
  | { type: "mulligan"; seat: SeatId; keeping_hand_of: number; must_bottom: number }
  | { type: "main_window"; seat: SeatId }
  | { type: "reaction_window"; seat: SeatId; depth: number }
  | { type: "game_over"; outcome: GameOutcome };

export interface GameOutcome {
  winner: SeatId | null;
  reason: string;
  final_life: [number, number];
  turns: number;
}

export interface LoggedEvent {
  seq: Seq;
  turn: number;
  phase: Phase;
  actor: SeatId | null;
  event: Event;
}

export type Event =
  | {
      type: "game_started";
      players: [string, string];
      starting_life: number;
      turn_cap: number;
      reaction_depth_cap: number;
    }
  | { type: "hand_dealt"; seat: SeatId; cards: CardRef[] }
  | { type: "window_opened"; expectation: Expectation }
  | { type: "drew"; seat: SeatId; cards: CardRef[] }
  | { type: "cards_moved"; moves: CardMoveEvent[] }
  | { type: "attr_set"; card: CardRef; zone: ZoneRef; was_face_down: boolean; attr: CardAttr }
  | { type: "token_created"; card: CardRef; zone: ZoneRef }
  | { type: "token_removed"; card: CardRef; from: ZoneRef }
  | { type: "counter_changed"; target: CounterTargetRef; name: string; old: number; new: number; delta: number }
  | { type: "shuffled"; seat: SeatId }
  | { type: "die_rolled"; seat: SeatId; sides: number; result: number }
  | { type: "revealed"; seat: SeatId; cards: CardRef[]; to: "opponent" | "all" }
  | { type: "said"; seat: SeatId; text: string }
  | { type: "pointed"; seat: SeatId; from: CardId; to: CardId | null }
  | { type: "passed"; seat: SeatId }
  | { type: "phase_changed"; phase: Phase }
  | { type: "turn_changed"; turn: number; active: SeatId }
  | { type: "mulligan_resolved"; seat: SeatId; kept: boolean; mulligan_count: number; bottomed: number }
  | { type: "game_ended"; outcome: GameOutcome };

export interface CardMoveEvent {
  card: CardRef;
  from: ZoneRef;
  to: ZoneRef;
  was_face_down: boolean;
  position: MovePosition;
}

export interface PlayerSnapshot {
  seat: SeatId;
  name: string;
  counters: Record<string, number>;
  mulligan_count: number;
  library_count: number;
  hand: CardRef[];
  battlefield: CardRef[];
  graveyard: CardRef[];
  exile: CardRef[];
  arrows: Array<{ from: CardId; to: CardId | null }>;
}

export interface Snapshot {
  seq: Seq;
  turn: number;
  phase: Phase;
  active: SeatId;
  expectation: Expectation;
  players: [PlayerSnapshot, PlayerSnapshot];
}

export type Action =
  | { type: "draw"; count: number }
  | { type: "move_cards"; moves: CardMove[] }
  | {
      type: "move_top_of_library";
      count: number;
      to_seat: SeatId;
      to_zone: ZoneKind;
      position: MovePosition;
      face_down: boolean;
    }
  | { type: "set_card_attr"; card: CardId; attr: CardAttr }
  | { type: "add_counter"; target: CounterTarget; name: string; delta: number }
  | { type: "shuffle" }
  | { type: "roll_die"; sides: number }
  | { type: "reveal"; cards: CardId[]; to: "opponent" | "all" }
  | { type: "say"; text: string }
  | { type: "point"; from: CardId; to: CardId | null }
  | { type: "pass" }
  | { type: "next_phase" }
  | { type: "next_turn" }
  | { type: "mulligan_keep"; bottom: CardId[] }
  | { type: "mulligan_again" }
  | { type: "concede" };

export interface CardMove {
  card: CardId;
  to_seat: SeatId;
  to_zone: ZoneKind;
  position: MovePosition;
  face_down: boolean | null;
  tapped: boolean | null;
}

export type ServerFrame =
  | {
      type: "hello";
      slot?: SeatId;
      seat_name?: string;
      match: { games_to_win: number; game_number: number; wins: [number, number] };
      config: PublicConfig;
      decklist?: { name: string; cards: CardSpec[] };
    }
  | { type: "snapshot"; game_number: number; state: Snapshot }
  | { type: "events"; game_number: number; events: LoggedEvent[] }
  | {
      type: "window";
      game_number: number;
      expectation: Expectation;
      clock_ms_remaining?: number;
      clocks_ms?: [number, number];
      decision_cap_ms?: number;
    }
  | { type: "ack"; cmd_id: number; seq: Seq }
  | { type: "reject"; cmd_id: number; error: { kind: string; detail: string } }
  | { type: "game_end"; game_number: number; outcome: GameOutcome; wins: [number, number] }
  | { type: "match_end"; scores: [number, number]; games: GameSummary[] }
  | { type: "replay_meta"; config: PublicConfig; results: Results; games: Array<{ game_number: number; slot_of_seat0: number; events: number }> };

export interface PublicConfig {
  players: Array<{ name: string }>;
  seed: number;
  decks: [string, string] | string[];
  games_to_win: number;
  starting_life: number;
  turn_cap: number;
  clock_s: number;
  decision_cap_s: number;
  player_connect_timeout_s: number;
}

export interface GameSummary {
  game_number: number;
  winner_slot: SeatId | null;
  reason: string;
  turns: number;
  final_life: [number, number];
  seed: number;
}

export interface Results {
  scores: [number, number];
  games: GameSummary[];
  seed: number;
  policy_names: [string, string];
}

export function cardId(card: CardRef): CardId {
  return "known" in card ? card.known.id : card.hidden.id;
}

export function knownCard(card: CardRef): CardView | null {
  return "known" in card ? card.known : null;
}

export function battlefieldPosition(x: number, y: number): MovePosition {
  return { battlefield: { x, y } };
}
