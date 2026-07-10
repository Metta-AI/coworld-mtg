import { describe, expect, it } from "vitest";
import { snapshotToTableModel } from "./model";
import { type CardRef, type CardView, type Snapshot } from "./protocol";

describe("snapshotToTableModel", () => {
  it("places the viewer on the bottom and maps hand plus battlefield rows", () => {
    const snapshot: Snapshot = {
      seq: 3,
      turn: 1,
      phase: "main1",
      active: 0,
      expectation: { type: "main_window", seat: 0 },
      players: [
        player(0, "alice", [known(card(1, "Mountain", "Basic Land - Mountain", null))], [known(card(2, "Goblin Raider", "Creature - Goblin Warrior", "2/2"))]),
        player(1, "bob", [], [known(card(3, "Forest", "Basic Land - Forest", null)), { hidden: { id: 9 } }])
      ]
    };

    const model = snapshotToTableModel(snapshot, { mode: "player", viewerSlot: 0 });

    expect(model.bottom?.name).toBe("alice");
    expect(model.top?.name).toBe("bob");
    expect(model.canAct).toBe(true);
    expect(model.hand.map((handCard) => handCard.name)).toEqual(["Mountain"]);
    expect(model.bottom?.battlefield.creatures.map((battlefieldCard) => battlefieldCard.name)).toEqual(["Goblin Raider"]);
    expect(model.top?.battlefield.lands.map((battlefieldCard) => battlefieldCard.name)).toEqual(["Forest"]);
    expect(model.top?.battlefield.creatures.map((battlefieldCard) => battlefieldCard.name)).toEqual(["Face-down card"]);
  });

  it("disables player actions while an ack is pending", () => {
    const snapshot: Snapshot = {
      seq: 1,
      turn: 1,
      phase: "untap",
      active: 0,
      expectation: { type: "main_window", seat: 0 },
      players: [player(0, "alice", [], []), player(1, "bob", [], [])]
    };

    expect(snapshotToTableModel(snapshot, { mode: "player", viewerSlot: 0, awaitingAck: true }).canAct).toBe(false);
  });

  it("uses display names for global acting banners", () => {
    const snapshot: Snapshot = {
      seq: 1,
      turn: 1,
      phase: "main1",
      active: 0,
      expectation: { type: "main_window", seat: 0 },
      players: [player(0, "alice", [], []), player(1, "goldfish", [], [])]
    };

    const model = snapshotToTableModel(snapshot, { mode: "global" });

    expect(model.banner.text).toBe("alice acting - Main 1");
    expect(model.players?.[model.active ?? 0].name).toBe("alice");
  });
});

function player(seat: 0 | 1, name: string, hand: CardRef[], battlefield: CardRef[]): Snapshot["players"][number] {
  return {
    seat,
    name,
    counters: { life: 20 },
    mulligan_count: 0,
    library_count: 33,
    hand,
    battlefield,
    graveyard: [],
    exile: [],
    arrows: []
  };
}

function known(view: CardView): CardRef {
  return { known: view };
}

function card(id: number, name: string, typeLine: string, pt: string | null): CardView {
  return {
    id,
    owner: 0,
    controller: 0,
    spec: {
      name,
      type_line: typeLine,
      mana_cost: name === "Goblin Raider" ? "{1}{R}" : null,
      power_toughness: pt,
      oracle_text: "",
      art_id: null
    },
    is_token: false,
    tapped: false,
    face_down: false,
    attacking: false,
    pt_override: null,
    annotation: null,
    counters: {},
    x: id,
    y: null
  };
}
