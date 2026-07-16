import { beforeEach, describe, expect, it, vi } from "vitest";

import type { GameAction, GameState } from "../adapter/types";
import {
  type CoworldReplayController,
  type CoworldReplayState,
  WebSocketAdapter,
} from "./coworld-ws-adapter";

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
const concede = { type: "Concede", data: { player_id: 0 } } as GameAction;

function phaseStateFrame(turnNumber = 1) {
  return {
    type: "state",
    state: {
      phase_client: {
        state: { ...state, turn_number: turnNumber },
        derived: {},
        legal_actions: [pass, concede],
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
    vi.useRealTimers();
    document.body.dataset.coworldRole = "player";
    window.history.replaceState({}, "", "/client/player?slot=1&token=secret");
    delete (window as ReplayWindow).__coworldReplay;
    delete (window as ReplayWindow).__coworldReplayState;
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
    expect((await adapter.getLegalActions()).actions).toEqual([pass, concede]);

    const submitted = adapter.submitAction(pass, 0);
    expect(JSON.parse(socket.send.mock.calls[0][0])).toEqual({ cmd_id: 1, action: pass });
    socket.frame(phaseStateFrame());
    socket.frame({ type: "ack", cmd_id: 1, turn: 1 });
    await expect(submitted).resolves.toEqual({ events: [] });

    adapter.sendConcede();
    expect(JSON.parse(socket.send.mock.calls[1][0])).toEqual({ cmd_id: 2, action: concede });
  });

  it("buffers replay steps at the start and navigates by event, turn, game, and keyboard", async () => {
    vi.useFakeTimers();
    document.body.dataset.coworldRole = "replay";
    window.history.replaceState(
      {},
      "",
      "/api/observatory/v2/coworlds/replays/session/proxy/client/replay",
    );
    const adapter = new WebSocketAdapter("ignored", "spectate", {
      main_deck: [],
      sideboard: [],
    });
    const emitted: Array<{ type: string; [key: string]: unknown }> = [];
    adapter.onEvent((event) => emitted.push(event as unknown as { type: string; [key: string]: unknown }));
    const initialized = adapter.initialize();
    const socket = MockWebSocket.last;
    expect(new URL(socket.url).pathname).toBe(
      "/api/observatory/v2/coworlds/replays/session/proxy/replay",
    );

    socket.frame({
      type: "replay_meta",
      config: { clock_s: 480 },
      results: {
        policy_names: ["Nissa", "Chandra"],
        games: [{ game_number: 1, winner_slot: 0, reason: "clock_flag" }],
      },
      games: [
        {
          game_number: 1,
          slot_of_seat0: 0,
          steps: 3,
          connection_events: [{ wall_ms: 750, slot: 1, connected: false }],
        },
        { game_number: 2, slot_of_seat0: 1, steps: 2 },
      ],
    });
    replayFrame(socket, 1, 1, 0, null);
    await initialized;
    replayFrame(socket, 1, 1, 500, pass);
    replayFrame(socket, 1, 2, 1_000, pass, 1);
    replayFrame(socket, 2, 1, 0, null);
    replayFrame(socket, 2, 2, 500, pass);
    socket.frame({ type: "match_end", scores: [1, 1], games: [] });

    await expect(adapter.submitAction(pass, 0)).rejects.toThrow("Spectators cannot submit actions");

    const controller = (window as ReplayWindow).__coworldReplay!;
    expect((window as ReplayWindow).__coworldReplayState).toMatchObject({
      index: 0,
      count: 2,
      showPriorityPasses: false,
      playerNames: ["Nissa", "Chandra"],
      selectedPlayerSlot: 0,
    });
    controller.setShowPriorityPasses(true);
    expect((window as ReplayWindow).__coworldReplayState).toMatchObject({
      index: 0,
      count: 5,
      playing: false,
      complete: true,
      gameIndex: 0,
      gameCount: 2,
      turnIndex: 0,
      turnCount: 2,
      actionLabel: "Game start",
    });
    expect((await adapter.getState()).turn_number).toBe(1);

    controller.seek(2);
    const forwardSeq = lastStateChangedSeq(emitted);
    expect((window as ReplayWindow).__coworldReplayState).toMatchObject({
      index: 2,
      gameIndex: 0,
      turnIndex: 1,
      turnNumber: 2,
      actionLabel: "Chandra · Clock expired",
      outcome: {
        headline: "Nissa wins on time",
        detail: "Chandra disconnected and did not return before their 8:00 clock expired.",
      },
    });
    expect((window as ReplayWindow).__coworldReplayState?.logEntries).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ actorName: "Chandra", actionLabel: "Disconnected" }),
        expect.objectContaining({ actionLabel: "Clock expired" }),
      ]),
    );
    controller.seek(0);
    expect(lastStateChangedSeq(emitted)).toBeGreaterThan(forwardSeq);
    expect((await adapter.getState()).turn_number).toBe(1);
    controller.seek(2);

    controller.setPerspective(1);
    expect(lastIdentity(emitted)).toMatchObject({
      playerId: 1,
      playerNames: { 0: "Nissa", 1: "Chandra" },
    });
    controller.seekGame(1);
    expect((window as ReplayWindow).__coworldReplayState).toMatchObject({ index: 3, gameIndex: 1 });
    expect(lastIdentity(emitted)).toMatchObject({
      playerId: 0,
      playerNames: { 0: "Chandra", 1: "Nissa" },
    });
    controller.stepGame(-1);
    controller.seekTurn(1);
    expect((window as ReplayWindow).__coworldReplayState).toMatchObject({ index: 2, turnIndex: 1 });

    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft" }));
    expect((window as ReplayWindow).__coworldReplayState?.index).toBe(1);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", shiftKey: true }));
    expect((window as ReplayWindow).__coworldReplayState?.index).toBe(2);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "PageDown" }));
    expect((window as ReplayWindow).__coworldReplayState?.index).toBe(3);
    expect((window as ReplayWindow).__coworldReplayState?.actionLabel).toBe("Game start");
    window.dispatchEvent(new KeyboardEvent("keydown", { code: "Space", cancelable: true }));
    expect((window as ReplayWindow).__coworldReplayState?.playing).toBe(true);
    window.dispatchEvent(new KeyboardEvent("keydown", { code: "Space", cancelable: true }));
    expect((window as ReplayWindow).__coworldReplayState?.playing).toBe(false);

    controller.seek(0);
    controller.setRate(2);
    controller.play();
    expect((window as ReplayWindow).__coworldReplayState).toMatchObject({ playing: true, rate: 2 });
    await vi.advanceTimersByTimeAsync(250);
    expect((window as ReplayWindow).__coworldReplayState?.index).toBe(1);

    controller.seek(4);
    controller.play();
    expect((window as ReplayWindow).__coworldReplayState?.index).toBe(0);
    await vi.runAllTimersAsync();
    expect((window as ReplayWindow).__coworldReplayState).toMatchObject({ index: 4, playing: false });

    adapter.dispose();
  });
});

type ReplayWindow = Window & {
  __coworldReplay?: CoworldReplayController;
  __coworldReplayState?: CoworldReplayState;
};

function replayFrame(
  socket: MockWebSocket,
  gameNumber: number,
  turnNumber: number,
  wallMs: number,
  action: GameAction | null,
  actorSlot = 0,
) {
  const frame = phaseStateFrame(turnNumber);
  socket.frame({
    type: "state",
    game_number: gameNumber,
    step: {
      state: frame.state,
      events: [],
      wall_ms: wallMs,
      actor_slot: action ? actorSlot : null,
      action,
    },
  });
}

function lastStateChangedSeq(events: Array<{ type: string; [key: string]: unknown }>): number {
  const event = events.filter((candidate) => candidate.type === "stateChanged").at(-1) as {
    snapshot: { seq: number };
  };
  return event.snapshot.seq;
}

function lastIdentity(events: Array<{ type: string; [key: string]: unknown }>) {
  return events.filter((candidate) => candidate.type === "playerIdentity").at(-1);
}
