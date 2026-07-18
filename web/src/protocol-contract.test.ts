import { describe, expect, it } from "vitest";
import framesFixture from "../../fixtures/wire/core-frames.json";
import type { ServerFrame } from "./protocol";

describe("server wire contract", () => {
  it("keeps the checked Rust frame fixtures consumable", () => {
    const observed: string[] = [];
    for (const raw of framesFixture) {
      const frame = raw as ServerFrame;
      observed.push(frame.type);
      switch (frame.type) {
        case "ack":
          expect(frame.cmd_id).toBe(7);
          expect(frame.turn).toBe(3);
          break;
        case "reject":
          expect(frame.error.kind).toBe("stale_action");
          break;
        case "game_end":
          expect(frame.outcome.winner_slot).toBe(1);
          expect(frame.wins).toEqual([0, 1]);
          break;
        case "match_end":
          expect(frame.games[0].seed).toBe(4242);
          expect(frame.scores).toEqual([0, 1]);
          break;
        default:
          throw new Error(`unexpected core fixture frame: ${JSON.stringify(frame)}`);
      }
    }
    expect(observed).toEqual(["ack", "reject", "game_end", "match_end"]);
  });
});
