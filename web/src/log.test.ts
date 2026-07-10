import { describe, expect, it } from "vitest";
import { eventToLogLine } from "./log";
import { type CardRef, type LoggedEvent } from "./protocol";

describe("eventToLogLine", () => {
  it("renders chat as a named table sentence", () => {
    const logged: LoggedEvent = {
      seq: 12,
      turn: 3,
      phase: "main1",
      actor: 0,
      event: { type: "said", seat: 0, text: "casts Goblin Raider" }
    };

    expect(eventToLogLine(logged, { players: ["goldfish-0", "goldfish-1"] })).toEqual({
      seq: 12,
      kind: "chat",
      text: "goldfish-0: casts Goblin Raider"
    });
  });

  it("renders common game events without leaking hidden names", () => {
    const hidden: CardRef = { hidden: { id: 44 } };
    const logged: LoggedEvent = {
      seq: 8,
      turn: 1,
      phase: "draw",
      actor: 1,
      event: {
        type: "revealed",
        seat: 1,
        cards: [hidden],
        to: "all"
      }
    };

    expect(eventToLogLine(logged, { players: ["alice", "goldfish"], viewerSlot: 0 }).text).toBe("goldfish reveals card 44");
  });

  it("renders life changes with tabular human text", () => {
    const logged: LoggedEvent = {
      seq: 30,
      turn: 4,
      phase: "combat_damage",
      actor: 0,
      event: {
        type: "counter_changed",
        target: { type: "player", seat: 1 },
        name: "life",
        old: 20,
        new: 17,
        delta: -3
      }
    };

    expect(eventToLogLine(logged, { players: ["alice", "bob"] }).text).toBe("bob life 20 -> 17");
  });

  it("uses second person for the viewer's own actions", () => {
    const names = { players: ["alice", "goldfish"] as [string, string], viewerSlot: 0 as const };

    expect(
      eventToLogLine(
        {
          seq: 1,
          turn: 1,
          phase: "untap",
          actor: null,
          event: { type: "hand_dealt", seat: 0, cards: hiddenCards(1, 7) }
        },
        names
      ).text
    ).toBe("You draw 7");
    expect(
      eventToLogLine(
        {
          seq: 2,
          turn: 1,
          phase: "untap",
          actor: 0,
          event: { type: "shuffled", seat: 0 }
        },
        names
      ).text
    ).toBe("You shuffle");
    expect(
      eventToLogLine(
        {
          seq: 3,
          turn: 1,
          phase: "untap",
          actor: 0,
          event: { type: "mulligan_resolved", seat: 0, kept: true, mulligan_count: 0, bottomed: 0 }
        },
        names
      ).text
    ).toBe("You keep, bottoming 0");
  });

  it("marks window pass and phase lines as procedural", () => {
    const names = { players: ["alice", "goldfish"] as [string, string], viewerSlot: 0 as const };
    const lines = [
      eventToLogLine(
        {
          seq: 4,
          turn: 1,
          phase: "main1",
          actor: null,
          event: { type: "window_opened", expectation: { type: "main_window", seat: 1 } }
        },
        names
      ),
      eventToLogLine(
        {
          seq: 5,
          turn: 1,
          phase: "main1",
          actor: 1,
          event: { type: "passed", seat: 1 }
        },
        names
      ),
      eventToLogLine(
        {
          seq: 6,
          turn: 1,
          phase: "main1",
          actor: null,
          event: { type: "phase_changed", phase: "main2" }
        },
        names
      )
    ];

    expect(lines.map((line) => line.kind)).toEqual(["procedural", "procedural", "procedural"]);
    expect(lines.map((line) => line.text)).toEqual(["window: goldfish main", "goldfish passes", "phase: Main 2"]);
  });
});

function hiddenCards(start: number, count: number): CardRef[] {
  return Array.from({ length: count }, (_, index) => ({ hidden: { id: start + index } }));
}
