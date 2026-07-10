import {
  allKnownBattlefieldCards,
  cardById,
  isLand,
  nextBattlefieldPosition,
  snapshotToTableModel,
  type ClockState
} from "./model";
import {
  type Action,
  battlefieldPosition,
  type CardId,
  type CardMove,
  type CardView,
  type LoggedEvent,
  type SeatId,
  type ServerFrame,
  type Snapshot
} from "./protocol";
import { renderTable, type UiCommand, type UiState } from "./renderer";
import { applyLoggedEvents, snapshotFromEvents } from "./state";

interface LiveAppState {
  mode: "player" | "global";
  root: HTMLElement;
  socket: WebSocket | null;
  snapshot: Snapshot | null;
  logs: LoggedEvent[];
  viewerSlot: SeatId | null;
  nextCmdId: number;
  pendingCmdId: number | null;
  clocks: [ClockState, ClockState];
  ui: UiState;
}

interface ReplayAppState {
  root: HTMLElement;
  socket: WebSocket | null;
  buffers: Map<number, LoggedEvent[]>;
  snapshot: Snapshot | null;
  logs: LoggedEvent[];
  loopComplete: boolean;
  renderIndex: number;
  timer: number | null;
  ui: UiState;
}

export function startLiveApp(mode: "player" | "global"): void {
  const root = requiredRoot();
  const state: LiveAppState = {
    mode,
    root,
    socket: null,
    snapshot: null,
    logs: [],
    viewerSlot: mode === "player" ? querySeat() : null,
    nextCmdId: 1,
    pendingCmdId: null,
    clocks: [{ ms: null }, { ms: null }],
    ui: emptyUiState()
  };
  renderLive(state);
  connectLive(state);
}

export function startReplayApp(): void {
  const root = requiredRoot();
  const state: ReplayAppState = {
    root,
    socket: null,
    buffers: new Map(),
    snapshot: null,
    logs: [],
    loopComplete: false,
    renderIndex: 0,
    timer: null,
    ui: {
      ...emptyUiState(),
      replay: { playing: true, speed: 1, games: [], currentGame: null }
    }
  };
  renderReplay(state);
  connectReplay(state);
  startReplayTimer(state);
}

function connectLive(state: LiveAppState): void {
  const url =
    state.mode === "player"
      ? wsUrl("/player", { slot: String(state.viewerSlot ?? 0), token: new URLSearchParams(location.search).get("token") ?? "" })
      : wsUrl("/global");
  state.socket = new WebSocket(url);
  state.socket.addEventListener("open", () => {
    state.ui.toast = null;
    renderLive(state);
  });
  state.socket.addEventListener("message", (message) => {
    handleLiveFrame(state, JSON.parse(String(message.data)) as ServerFrame);
  });
  state.socket.addEventListener("close", () => {
    showToast(state.ui, "Connection closed");
    state.pendingCmdId = null;
    renderLive(state);
  });
  state.socket.addEventListener("error", () => {
    showToast(state.ui, "Connection error");
    renderLive(state);
  });
}

function connectReplay(state: ReplayAppState): void {
  state.socket = new WebSocket(wsUrl("/replay"));
  state.socket.addEventListener("message", (message) => {
    handleReplayFrame(state, JSON.parse(String(message.data)) as ServerFrame);
  });
  state.socket.addEventListener("close", () => {
    showToast(state.ui, "Replay stream closed");
    renderReplay(state);
  });
  state.socket.addEventListener("error", () => {
    showToast(state.ui, "Replay stream error");
    renderReplay(state);
  });
}

function handleLiveFrame(state: LiveAppState, frame: ServerFrame): void {
  switch (frame.type) {
    case "hello":
      if (state.mode === "player" && frame.slot !== undefined) {
        state.viewerSlot = frame.slot;
      }
      break;
    case "snapshot":
      state.snapshot = frame.state;
      break;
    case "events":
      state.logs.push(...frame.events);
      if (state.snapshot) {
        state.snapshot = applyLoggedEvents(state.snapshot, frame.events);
      }
      break;
    case "window":
      if (state.snapshot) {
        state.snapshot.expectation = frame.expectation;
      }
      if (frame.clocks_ms) {
        state.clocks = [{ ms: frame.clocks_ms[0] }, { ms: frame.clocks_ms[1] }];
      } else if (state.viewerSlot !== null && frame.clock_ms_remaining !== undefined) {
        state.clocks[state.viewerSlot] = { ms: frame.clock_ms_remaining };
      }
      break;
    case "ack":
      if (state.pendingCmdId === frame.cmd_id) {
        state.pendingCmdId = null;
      }
      break;
    case "reject":
      if (state.pendingCmdId === frame.cmd_id) {
        state.pendingCmdId = null;
      }
      showToast(state.ui, `${frame.error.kind}: ${frame.error.detail}`);
      break;
    case "game_end":
      if (state.snapshot) {
        state.snapshot.expectation = { type: "game_over", outcome: frame.outcome };
      }
      break;
    case "match_end":
      showToast(state.ui, `Match ended ${frame.scores[0]}-${frame.scores[1]}`);
      break;
    case "replay_meta":
      break;
  }
  renderLive(state);
}

function handleReplayFrame(state: ReplayAppState, frame: ServerFrame): void {
  if (frame.type === "replay_meta") {
    const games = frame.games.map((game) => game.game_number);
    state.ui.replay = {
      playing: true,
      speed: 1,
      games,
      currentGame: games[0] ?? null
    };
    renderReplay(state);
    return;
  }
  if (frame.type === "events") {
    if (state.loopComplete) {
      state.buffers.clear();
      state.renderIndex = 0;
      state.loopComplete = false;
    }
    const current = state.buffers.get(frame.game_number) ?? [];
    current.push(...frame.events);
    state.buffers.set(frame.game_number, current);
    if (state.ui.replay && state.ui.replay.currentGame === null) {
      state.ui.replay.currentGame = frame.game_number;
    }
    renderReplay(state);
    return;
  }
  if (frame.type === "match_end") {
    state.loopComplete = true;
  }
}

function handleLiveCommand(state: LiveAppState, command: UiCommand): void {
  switch (command.type) {
    case "open_hand":
      state.ui.popover = { kind: "hand", cardId: command.cardId };
      renderLive(state);
      break;
    case "open_battlefield":
      if (state.ui.pointFrom !== null && state.ui.pointFrom !== command.cardId) {
        sendAction(state, { type: "point", from: state.ui.pointFrom, to: command.cardId });
        state.ui.pointFrom = null;
      } else {
        state.ui.popover = { kind: "battlefield", cardId: command.cardId };
        renderLive(state);
      }
      break;
    case "close_popover":
      state.ui.popover = null;
      renderLive(state);
      break;
    case "hand_action":
      handleHandAction(state, command.cardId, command.action);
      break;
    case "battlefield_action":
      handleBattlefieldAction(state, command.cardId, command.action);
      break;
    case "counter":
      state.ui.popover = null;
      sendAction(state, { type: "add_counter", target: { type: "card", card: command.cardId }, name: command.name, delta: command.delta });
      break;
    case "annotation":
      state.ui.popover = null;
      sendAction(state, { type: "set_card_attr", card: command.cardId, attr: { type: "annotation", value: command.value } });
      break;
    case "life":
      sendAction(state, { type: "add_counter", target: { type: "player", seat: command.seat }, name: "life", delta: command.delta });
      break;
    case "library":
      handleLibraryAction(state, command.action);
      break;
    case "action_bar":
      handleActionBar(state, command.action);
      break;
    case "chat":
      sendAction(state, { type: "say", text: command.text });
      break;
    case "mulligan_toggle":
      toggleMulliganCard(state, command.cardId);
      break;
    case "mulligan_keep":
      sendAction(state, { type: "mulligan_keep", bottom: state.ui.mulliganBottom });
      state.ui.mulliganBottom = [];
      break;
    case "mulligan_again":
      sendAction(state, { type: "mulligan_again" });
      state.ui.mulliganBottom = [];
      break;
    case "replay":
      break;
  }
}

function handleReplayCommand(state: ReplayAppState, command: UiCommand): void {
  if (command.type !== "replay" || !state.ui.replay) {
    return;
  }
  if (command.action === "toggle") {
    state.ui.replay.playing = !state.ui.replay.playing;
  } else if (command.action === "speed" && command.speed) {
    state.ui.replay.speed = command.speed;
  } else if (command.action === "seek" && command.game !== undefined) {
    state.ui.replay.currentGame = command.game;
    state.renderIndex = 0;
    updateReplaySnapshot(state);
  }
  renderReplay(state);
}

function handleHandAction(state: LiveAppState, id: CardId, action: Extract<UiCommand, { type: "hand_action" }>["action"]): void {
  const snapshot = state.snapshot;
  const slot = state.viewerSlot;
  if (!snapshot || slot === null) {
    return;
  }
  const card = findCardView(snapshot, id);
  state.ui.popover = null;
  switch (action) {
    case "play":
      sendAction(state, moveCard(id, slot, "battlefield", battlefieldFor(snapshot, slot, card), false, false));
      break;
    case "play_face_down":
      sendAction(state, moveCard(id, slot, "battlefield", battlefieldFor(snapshot, slot, null), true, false));
      break;
    case "discard":
      sendAction(state, moveCard(id, slot, "graveyard", "bottom", null, null));
      break;
    case "reveal":
      sendAction(state, { type: "reveal", cards: [id], to: "all" });
      break;
    case "library_top":
      sendAction(state, moveCard(id, slot, "library", "top", null, null));
      break;
    case "library_bottom":
      sendAction(state, moveCard(id, slot, "library", "bottom", null, null));
      break;
  }
}

function handleBattlefieldAction(
  state: LiveAppState,
  id: CardId,
  action: Extract<UiCommand, { type: "battlefield_action" }>["action"]
): void {
  const snapshot = state.snapshot;
  const slot = state.viewerSlot;
  if (!snapshot || slot === null) {
    return;
  }
  const card = findCardView(snapshot, id);
  switch (action) {
    case "tap":
      state.ui.popover = null;
      sendAction(state, { type: "set_card_attr", card: id, attr: { type: "tapped", value: !(card?.tapped ?? false) } });
      break;
    case "attack":
      state.ui.popover = null;
      sendAction(state, { type: "set_card_attr", card: id, attr: { type: "attacking", value: !(card?.attacking ?? false) } });
      break;
    case "graveyard":
      state.ui.popover = null;
      sendAction(state, moveCard(id, slot, "graveyard", "bottom", null, null));
      break;
    case "exile":
      state.ui.popover = null;
      sendAction(state, moveCard(id, slot, "exile", "bottom", null, null));
      break;
    case "hand":
      state.ui.popover = null;
      sendAction(state, moveCard(id, slot, "hand", "bottom", null, null));
      break;
    case "point_start":
      state.ui.pointFrom = id;
      state.ui.popover = null;
      showToast(state.ui, "Click a battlefield card to complete the pointer");
      renderLive(state);
      break;
    case "point_clear":
      state.ui.popover = null;
      sendAction(state, { type: "point", from: id, to: null });
      break;
    case "point_here":
      if (state.ui.pointFrom !== null) {
        state.ui.popover = null;
        sendAction(state, { type: "point", from: state.ui.pointFrom, to: id });
        state.ui.pointFrom = null;
      }
      break;
  }
}

function handleLibraryAction(state: LiveAppState, action: Extract<UiCommand, { type: "library" }>["action"]): void {
  const slot = state.viewerSlot;
  if (slot === null) {
    return;
  }
  if (action === "draw") {
    sendAction(state, { type: "draw", count: 1 });
  } else if (action === "mill") {
    sendAction(state, {
      type: "move_top_of_library",
      count: 1,
      to_seat: slot,
      to_zone: "graveyard",
      position: "bottom",
      face_down: false
    });
  } else {
    sendAction(state, { type: "shuffle" });
  }
}

function handleActionBar(state: LiveAppState, action: Extract<UiCommand, { type: "action_bar" }>["action"]): void {
  switch (action) {
    case "draw":
      sendAction(state, { type: "draw", count: 1 });
      break;
    case "untap_all":
      sendUntapAll(state);
      break;
    case "next_phase":
      sendAction(state, { type: "next_phase" });
      break;
    case "next_turn":
      sendAction(state, { type: "next_turn" });
      break;
    case "pass":
      sendAction(state, { type: "pass" });
      break;
    case "concede":
      sendAction(state, { type: "concede" });
      break;
  }
}

function sendUntapAll(state: LiveAppState): void {
  const snapshot = state.snapshot;
  const slot = state.viewerSlot;
  if (!snapshot || slot === null) {
    return;
  }
  const moves = allKnownBattlefieldCards(snapshot, slot)
    .filter((card) => card.tapped)
    .map((card, index): CardMove => ({
      card: card.id,
      to_seat: slot,
      to_zone: "battlefield",
      position: battlefieldPosition(card.x ?? index, card.y ?? (isLand(card) ? 0 : 1)),
      face_down: null,
      tapped: false
    }));
  if (moves.length === 0) {
    showToast(state.ui, "No tapped cards to untap");
    renderLive(state);
    return;
  }
  sendAction(state, { type: "move_cards", moves });
}

function toggleMulliganCard(state: LiveAppState, id: CardId): void {
  const current = state.ui.mulliganBottom;
  const index = current.indexOf(id);
  if (index >= 0) {
    current.splice(index, 1);
  } else {
    current.push(id);
  }
  renderLive(state);
}

function sendAction(state: LiveAppState, action: Action): void {
  if (state.pendingCmdId !== null) {
    showToast(state.ui, "Waiting for previous action");
    renderLive(state);
    return;
  }
  if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
    showToast(state.ui, "Socket is not connected");
    renderLive(state);
    return;
  }
  const cmdId = state.nextCmdId++;
  state.pendingCmdId = cmdId;
  state.socket.send(JSON.stringify({ cmd_id: cmdId, action }));
  renderLive(state);
}

function moveCard(
  id: CardId,
  seat: SeatId,
  toZone: CardMove["to_zone"],
  position: CardMove["position"],
  faceDown: boolean | null,
  tapped: boolean | null
): Action {
  return {
    type: "move_cards",
    moves: [
      {
        card: id,
        to_seat: seat,
        to_zone: toZone,
        position,
        face_down: faceDown,
        tapped
      }
    ]
  };
}

function battlefieldFor(snapshot: Snapshot, seat: SeatId, card: CardView | null): CardMove["position"] {
  const position = nextBattlefieldPosition(snapshot, seat, card);
  return battlefieldPosition(position.x, position.y);
}

function findCardView(snapshot: Snapshot, id: CardId): CardView | null {
  const model = cardById(snapshot, id);
  return model?.view ?? null;
}

function renderLive(state: LiveAppState): void {
  const model = snapshotToTableModel(state.snapshot, {
    mode: state.mode,
    viewerSlot: state.viewerSlot,
    awaitingAck: state.pendingCmdId !== null,
    clocks: state.clocks
  });
  renderTable(state.root, model, state.logs, state.ui, (command) => handleLiveCommand(state, command));
}

function renderReplay(state: ReplayAppState): void {
  const model = snapshotToTableModel(state.snapshot, {
    mode: "replay",
    viewerSlot: null,
    awaitingAck: false,
    clocks: [{ ms: null }, { ms: null }]
  });
  renderTable(state.root, model, state.logs, state.ui, (command) => handleReplayCommand(state, command));
}

function startReplayTimer(state: ReplayAppState): void {
  state.timer = window.setInterval(() => {
    if (!state.ui.replay?.playing) {
      return;
    }
    const game = state.ui.replay.currentGame;
    if (game === null) {
      return;
    }
    const events = state.buffers.get(game) ?? [];
    const step = state.ui.replay.speed;
    if (state.renderIndex < events.length) {
      state.renderIndex = Math.min(events.length, state.renderIndex + step);
      updateReplaySnapshot(state);
      renderReplay(state);
    }
  }, 400);
}

function updateReplaySnapshot(state: ReplayAppState): void {
  const game = state.ui.replay?.currentGame;
  if (game === null || game === undefined) {
    return;
  }
  const events = (state.buffers.get(game) ?? []).slice(0, state.renderIndex);
  state.logs = events;
  state.snapshot = snapshotFromEvents(events);
}

function emptyUiState(): UiState {
  return {
    popover: null,
    pointFrom: null,
    mulliganBottom: [],
    toast: null
  };
}

function showToast(ui: UiState, text: string): void {
  ui.toast = text;
  window.setTimeout(() => {
    if (ui.toast === text) {
      ui.toast = null;
      requiredRoot().dispatchEvent(new CustomEvent("toast-expired"));
    }
  }, 3500);
}

function requiredRoot(): HTMLElement {
  const root = document.querySelector<HTMLElement>("#app");
  if (!root) {
    throw new Error("missing #app");
  }
  return root;
}

function querySeat(): SeatId {
  return new URLSearchParams(location.search).get("slot") === "1" ? 1 : 0;
}

function wsUrl(path: string, params: Record<string, string> = {}): string {
  const query = new URLSearchParams(location.search);
  const server = query.get("server");
  const base = server ? new URL(server, location.href) : new URL(location.href);
  const protocol = base.protocol === "https:" || base.protocol === "wss:" ? "wss:" : "ws:";
  const ws = new URL(`${protocol}//${base.host}${path}`);
  for (const [key, value] of Object.entries(params)) {
    ws.searchParams.set(key, value);
  }
  return ws.toString();
}
