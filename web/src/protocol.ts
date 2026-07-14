export type SeatId = 0 | 1;
export type GameAction = { type: string; data?: Record<string, unknown> };

export interface ManaCost {
  type: string;
  shards?: string[];
  generic?: number;
}

export interface ManaPool {
  mana?: Array<{ color: string }>;
  [key: string]: unknown;
}

export interface CardView {
  object_id: number;
  card_id: number;
  owner: SeatId;
  controller: SeatId;
  zone: string;
  name: string;
  type_line: string;
  mana_cost: ManaCost;
  oracle_text: string;
  power: number | null;
  toughness: number | null;
  tapped: boolean;
  face_down: boolean;
  attacking: boolean;
  blocked: boolean;
  blocking: number[];
  counters: unknown;
  scryfall_oracle_id: string | null;
}

export interface PlayerView {
  id: SeatId;
  life: number;
  poison: number;
  energy: number;
  mana_pool: ManaPool;
  library_count: number;
  hand: CardView[];
  graveyard: CardView[];
}

export interface StackView {
  id: number;
  source_id: number;
  controller: SeatId;
  source: CardView | null;
  kind: unknown;
}

export interface CombatView {
  attackers: Array<{
    object_id: number;
    defending_player: SeatId;
    attack_target:
      | { type: "Player"; data: SeatId }
      | { type: "Planeswalker" | "Battle"; data: number };
    blocked: boolean;
  }>;
}

export interface ViewerSnapshot {
  turn: number;
  phase: string;
  active_player: SeatId;
  priority_player: SeatId;
  waiting_for: { type?: string; data?: unknown };
  players: [PlayerView, PlayerView];
  battlefield: CardView[];
  stack: StackView[];
  exile: CardView[];
  combat: CombatView | null;
  preference_player: SeatId | null;
  auto_pass_recommended: boolean;
  auto_pass_mode: { type: string; until?: string; initial_stack_len?: number } | null;
  phase_stops: Array<{ phase: string; scope: "AllTurns" | "OwnTurn" | "OpponentsTurns" }>;
  legal_actions: GameAction[];
  spell_costs: Record<string, ManaCost>;
  legal_actions_by_object: Record<string, GameAction[]>;
}

export interface PublicConfig {
  players: Array<{ name: string }>;
  seed: number;
  decks: string[];
  games_to_win: number;
  clock_s: number;
  decision_cap_s: number;
}

export interface GameOutcome {
  winner_slot: SeatId | null;
  reason: string;
  final_life: [number, number];
  turns: number;
}

export interface GameSummary extends GameOutcome {
  game_number: number;
  seed: number;
}

export type ServerFrame =
  | {
      type: "hello";
      slot?: SeatId;
      seat?: SeatId;
      seat_name?: string;
      player_names: [string, string];
      match: { games_to_win: number; game_number: number; wins: [number, number] };
      config: PublicConfig;
      decklist?: { name: string; cards: unknown[] };
    }
  | {
      type: "state";
      game_number: number;
      state?: ViewerSnapshot;
      step?: { state: ViewerSnapshot; events: unknown[]; actor_slot: SeatId | null; action: GameAction | null };
      events?: unknown[];
      clocks_ms?: [number, number];
      decision_cap_ms?: number;
    }
  | { type: "ack"; cmd_id: number; turn: number }
  | { type: "reject"; cmd_id: number; error: { kind: string; detail: string } }
  | { type: "game_end"; game_number: number; outcome: GameOutcome; wins: [number, number] }
  | { type: "match_end"; scores: [number, number]; games: GameSummary[] }
  | {
      type: "replay_meta";
      config: PublicConfig;
      results: { scores: [number, number] };
      games: Array<{ game_number: number; slot_of_seat0: number; steps: number }>;
    };
