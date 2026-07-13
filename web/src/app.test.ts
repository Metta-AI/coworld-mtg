import { describe, expect, it } from "vitest";
import {
  activeTurnLabel,
  actionLabel,
  allActions,
  matchingAttackAction,
  matchingBlockAction,
  matchingSelectCardsAction,
  shouldBufferReplayFrame,
  unavailableCardMessage
} from "./app";
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

  it("matches the exact Phase attacker declaration selected on the battlefield", () => {
    const none = { type: "DeclareAttackers", data: { attacks: [] } };
    const two = {
      type: "DeclareAttackers",
      data: { attacks: [[12, { type: "Player", data: 1 }], [8, { type: "Player", data: 1 }]] }
    };
    expect(matchingAttackAction([none, two], new Set([8, 12]))).toEqual(two);
    expect(matchingAttackAction([none, two], new Set())).toEqual(none);
  });

  it("matches blocker-to-attacker assignments independent of selection order", () => {
    const none = { type: "DeclareBlockers", data: { assignments: [] } };
    const blocks = { type: "DeclareBlockers", data: { assignments: [[3, 9], [4, 8]] } };
    expect(matchingBlockAction([none, blocks], new Map([[4, 8], [3, 9]]))).toEqual(blocks);
    expect(matchingBlockAction([none, blocks], new Map())).toEqual(none);
  });

  it("matches an exact Phase card-selection combination", () => {
    const one = { type: "SelectCards", data: { cards: [4] } };
    const two = { type: "SelectCards", data: { cards: [9, 4] } };
    expect(matchingSelectCardsAction([one, two], new Set([4, 9]))).toEqual(two);
  });

  it("stops buffering when a looping replay reaches its authoritative step count", () => {
    expect(shouldBufferReplayFrame(280, 281)).toBe(true);
    expect(shouldBufferReplayFrame(281, 281)).toBe(false);
    expect(shouldBufferReplayFrame(10, 0)).toBe(true);
  });

  it("makes the active turn explicit even when the viewer has priority", () => {
    const snapshot = fixture();
    snapshot.active_player = 1;
    snapshot.priority_player = 0;
    expect(activeTurnLabel(snapshot, ["Alice", "Bob"], 0)).toBe("Bob's turn");
  });

  it("explains why a land has no action outside its controller's turn", () => {
    const snapshot = fixture();
    const mountain = snapshot.players[0].hand[0];
    snapshot.active_player = 1;
    expect(unavailableCardMessage(mountain, snapshot)).toBe("Lands can only be played during your turn.");

    snapshot.active_player = 0;
    snapshot.phase = "Upkeep";
    expect(unavailableCardMessage(mountain, snapshot)).toBe("Lands can only be played during your main phase.");
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
