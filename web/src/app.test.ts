import { describe, expect, it } from "vitest";
import { actionLabel, allActions } from "./app";
import type { ViewerSnapshot } from "./protocol";

describe("Phase action presentation", () => {
  it("deduplicates flat and per-object legal actions", () => {
    const play = { type: "PlayLand", data: { object_id: 7, card_id: 7 } };
    const snapshot = fixture();
    snapshot.legal_actions = [play];
    snapshot.legal_actions_by_object = { "7": [play] };
    expect(allActions(snapshot)).toEqual([play]);
  });

  it("labels actions with visible card names", () => {
    const snapshot = fixture();
    expect(actionLabel({ type: "PlayLand", data: { object_id: 7 } }, snapshot)).toBe("Play Mountain");
  });
});

function fixture(): ViewerSnapshot {
  const card = {
    object_id: 7,
    card_id: 7,
    owner: 0 as const,
    controller: 0 as const,
    zone: "Hand",
    name: "Mountain",
    type_line: "Basic Land — Mountain",
    mana_cost: { type: "NoCost" },
    oracle_text: "",
    power: null,
    toughness: null,
    tapped: false,
    face_down: false,
    attacking: false,
    blocking: [],
    counters: {},
    scryfall_oracle_id: null
  };
  return {
    turn: 1,
    phase: "PreCombatMain",
    active_player: 0,
    priority_player: 0,
    waiting_for: { type: "Priority", data: { player: 0 } },
    players: [
      { id: 0, life: 20, poison: 0, energy: 0, mana_pool: {}, library_count: 33, hand: [card], graveyard: [] },
      { id: 1, life: 20, poison: 0, energy: 0, mana_pool: {}, library_count: 33, hand: [], graveyard: [] }
    ],
    battlefield: [],
    stack: [],
    exile: [],
    combat: null,
    legal_actions: [],
    spell_costs: {},
    legal_actions_by_object: {}
  };
}
