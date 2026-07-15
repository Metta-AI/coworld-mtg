import { beforeEach, describe, expect, it, vi } from "vitest";

import type { GameAction, GameState } from "../adapter/types";
import { WebSocketAdapter } from "./coworld-ws-adapter";

class MockWebSocket {
  static OPEN = 1;
  static last: MockWebSocket;
  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  send = vi.fn();
  close = vi.fn();

  constructor(public readonly url: string) {
    MockWebSocket.last = this;
  }

  frame(value: unknown) {
    this.onmessage?.({ data: JSON.stringify(value) });
  }
}

vi.stubGlobal("WebSocket", MockWebSocket);

const state = {
  turn_number: 1,
  active_player: 0,
  phase: "PreCombatMain",
  players: [],
  priority_player: 0,
  objects: {},
  battlefield: [],
  stack: [],
  exile: [],
  waiting_for: { type: "Priority", data: { player: 0 } },
  combat: null,
} as unknown as GameState;

const pass = { type: "PassPriority" } as GameAction;

function phaseStateFrame() {
  return {
    type: "state",
    state: {
      phase_client: {
        state,
        derived: {},
        legal_actions: [pass],
        auto_pass_recommended: false,
        spell_costs: {},
        legal_actions_by_object: {},
      },
    },
    events: [],
    clocks_ms: [12_000, 10_000],
  };
}

describe("Coworld Phase adapter", () => {
  beforeEach(() => {
    document.body.dataset.coworldRole = "player";
    window.history.replaceState({}, "", "/client/player?slot=1&token=secret");
  });

  it("negotiates rich state and sends Phase actions unchanged", async () => {
    const adapter = new WebSocketAdapter("ignored", "host", { main_deck: [], sideboard: [] });
    const initialized = adapter.initialize();
    const socket = MockWebSocket.last;

    expect(new URL(socket.url).pathname).toBe("/player");
    expect(new URL(socket.url).searchParams.get("client")).toBe("phase");
    expect(new URL(socket.url).searchParams.get("slot")).toBe("1");

    socket.onopen?.();
    socket.frame({ type: "hello", slot: 1, seat: 0, player_names: ["A", "B"] });
    socket.frame(phaseStateFrame());
    await initialized;

    expect((await adapter.getState()).turn_number).toBe(1);
    expect((await adapter.getLegalActions()).actions).toEqual([pass]);

    const submitted = adapter.submitAction(pass, 0);
    expect(JSON.parse(socket.send.mock.calls[0][0])).toEqual({ cmd_id: 1, action: pass });
    socket.frame(phaseStateFrame());
    socket.frame({ type: "ack", cmd_id: 1, turn: 1 });
    await expect(submitted).resolves.toEqual({ events: [] });
  });

  it("uses the read-only replay socket and accepts nested replay steps", async () => {
    document.body.dataset.coworldRole = "replay";
    const adapter = new WebSocketAdapter("ignored", "spectate", {
      main_deck: [],
      sideboard: [],
    });
    const initialized = adapter.initialize();
    const socket = MockWebSocket.last;
    expect(new URL(socket.url).pathname).toBe("/replay");

    const frame = phaseStateFrame();
    socket.frame({ type: "state", step: { state: frame.state, events: [] } });
    await initialized;
    await expect(adapter.submitAction(pass, 0)).rejects.toThrow("Spectators cannot submit actions");
  });
});
