import { describe, expect, it } from "vitest";
import { applyLoggedEvents } from "./state";
import { type CardRef, type LoggedEvent, type Snapshot } from "./protocol";

describe("applyLoggedEvents", () => {
  it("does not re-apply backlog events at or before the snapshot seq", () => {
    const snapshot = tableSnapshot(8, 33, hiddenCards(1, 7));
    const backlog: LoggedEvent[] = [
      {
        seq: 1,
        turn: 1,
        phase: "untap",
        actor: null,
        event: {
          type: "game_started",
          players: ["alice", "bob"],
          starting_life: 20,
          turn_cap: 20,
          reaction_depth_cap: 8
        }
      },
      {
        seq: 8,
        turn: 1,
        phase: "untap",
        actor: null,
        event: { type: "hand_dealt", seat: 0, cards: hiddenCards(1, 7) }
      }
    ];

    const unchanged = applyLoggedEvents(snapshot, backlog);

    expect(unchanged.players[0].library_count).toBe(33);
    expect(unchanged.players[0].hand).toHaveLength(7);
    expect(unchanged.seq).toBe(8);

    const advanced = applyLoggedEvents(unchanged, [
      ...backlog,
      {
        seq: 9,
        turn: 1,
        phase: "draw",
        actor: 0,
        event: { type: "drew", seat: 0, cards: hiddenCards(8, 1) }
      }
    ]);

    expect(advanced.players[0].library_count).toBe(32);
    expect(advanced.players[0].hand).toHaveLength(8);
    expect(advanced.seq).toBe(9);
    expect(advanced.phase).toBe("draw");
  });
});

function tableSnapshot(seq: number, libraryCount: number, hand: CardRef[]): Snapshot {
  return {
    seq,
    turn: 1,
    phase: "untap",
    active: 0,
    expectation: { type: "mulligan", seat: 0, keeping_hand_of: 7, must_bottom: 0 },
    players: [
      player(0, "alice", libraryCount, hand),
      player(1, "bob", 33, hiddenCards(101, 7))
    ]
  };
}

function player(seat: 0 | 1, name: string, libraryCount: number, hand: CardRef[]): Snapshot["players"][number] {
  return {
    seat,
    name,
    counters: { life: 20 },
    mulligan_count: 0,
    library_count: libraryCount,
    hand,
    battlefield: [],
    graveyard: [],
    exile: [],
    arrows: []
  };
}

function hiddenCards(start: number, count: number): CardRef[] {
  return Array.from({ length: count }, (_, index) => ({ hidden: { id: start + index } }));
}
