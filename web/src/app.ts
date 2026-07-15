import "./styles.css";
import {
  type CardView,
  type GameAction,
  type SeatId,
  type ServerFrame,
  type ViewerSnapshot
} from "./protocol";

interface AppState {
  mode: "player" | "global" | "replay";
  root: HTMLElement;
  socket: WebSocket | null;
  viewerSeat: SeatId | null;
  playerNames: [string, string];
  snapshot: ViewerSnapshot | null;
  events: unknown[];
  clocks: [number | null, number | null];
  nextCmdId: number;
  pendingCmdId: number | null;
  message: string;
  focusedObjectId: number | null;
  focusedBlockerId: number | null;
  selectedObjects: Set<number>;
  blockAssignments: Map<number, number>;
  decisionKey: string;
  logOpen: boolean;
  openZone: { seat: SeatId; kind: "graveyard" | "exile" } | null;
  replayFrames: StateFrame[];
  replayIndex: number;
  replayTotalSteps: number;
  replayPlaying: boolean;
  replayTimer: number | null;
  fullControl: boolean;
  holdFullControl: boolean;
  autoPassTimer: number | null;
  stackCollapsed: boolean;
  damageCues: DamageCue[];
  nextDamageCueId: number;
  blockPulseUntil: number;
}

type StateFrame = Extract<ServerFrame, { type: "state" }>;

interface Point {
  x: number;
  y: number;
}

interface DamageCue {
  id: number;
  sourceId: number;
  target: { type: "Object" | "Player"; id: number };
  amount: number;
  isCombat: boolean;
  sourcePoint?: Point;
  targetPoint?: Point;
}

const PHASES = [
  ["Untap", "Untap"],
  ["Upkeep", "Upkeep"],
  ["Draw", "Draw"],
  ["PreCombatMain", "Main"],
  ["BeginCombat", "Combat"],
  ["DeclareAttackers", "Attack"],
  ["DeclareBlockers", "Block"],
  ["CombatDamage", "Damage"],
  ["PostCombatMain", "Main"],
  ["End", "End"]
] as const;

export function startLiveApp(mode: "player" | "global"): void {
  const state = initialState(mode);
  connect(state, mode === "player" ? playerUrl() : wsUrl("/global"));
  if (mode === "player") bindKeyboardControls(state);
  render(state);
}

export function startReplayApp(): void {
  const state = initialState("replay");
  connect(state, wsUrl("/replay"));
  render(state);
}

function initialState(mode: AppState["mode"]): AppState {
  const root = document.querySelector<HTMLElement>("#app");
  if (!root) throw new Error("missing #app");
  return {
    mode,
    root,
    socket: null,
    viewerSeat: null,
    playerNames: ["Player 1", "Player 2"],
    snapshot: null,
    events: [],
    clocks: [null, null],
    nextCmdId: 1,
    pendingCmdId: null,
    message: "Connecting to the match…",
    focusedObjectId: null,
    focusedBlockerId: null,
    selectedObjects: new Set(),
    blockAssignments: new Map(),
    decisionKey: "",
    logOpen: false,
    openZone: null,
    replayFrames: [],
    replayIndex: -1,
    replayTotalSteps: 0,
    replayPlaying: true,
    replayTimer: null,
    fullControl: false,
    holdFullControl: false,
    autoPassTimer: null,
    stackCollapsed: false,
    damageCues: [],
    nextDamageCueId: 1,
    blockPulseUntil: 0
  };
}

function connect(state: AppState, url: string): void {
  const socket = new WebSocket(url);
  state.socket = socket;
  socket.addEventListener("open", () => {
    state.message = "Connected";
    render(state);
  });
  socket.addEventListener("message", message => {
    handleFrame(state, JSON.parse(String(message.data)) as ServerFrame);
  });
  socket.addEventListener("close", () => {
    state.message = "Connection closed";
    state.pendingCmdId = null;
    render(state);
  });
  socket.addEventListener("error", () => {
    state.message = "Connection error";
    render(state);
  });
}

function handleFrame(state: AppState, frame: ServerFrame): void {
  switch (frame.type) {
    case "hello":
      state.viewerSeat = frame.seat ?? null;
      state.playerNames = frame.player_names;
      state.message = `Game ${frame.match.game_number}`;
      break;
    case "state": {
      if (state.mode === "replay" && frame.step) {
        if (!shouldBufferReplayFrame(state.replayFrames.length, state.replayTotalSteps)) return;
        const wasFollowing = state.replayIndex === state.replayFrames.length - 1;
        state.replayFrames.push(frame);
        if (state.replayPlaying && wasFollowing) showReplayStep(state, state.replayFrames.length - 1);
        break;
      }
      const snapshot = frame.state ?? frame.step?.state;
      const events = frame.events ?? frame.step?.events ?? [];
      queueDamageCues(state, events);
      queueBlockPulse(state, events);
      if (snapshot) {
        const nextKey = snapshotDecisionKey(snapshot);
        if (nextKey !== state.decisionKey) {
          state.selectedObjects.clear();
          state.blockAssignments.clear();
          state.focusedBlockerId = null;
          state.focusedObjectId = null;
          state.decisionKey = nextKey;
        }
        state.snapshot = snapshot;
      }
      state.events.push(...events);
      if (frame.step?.action) state.events.push({ type: "Action", data: frame.step.action });
      if (frame.clocks_ms) state.clocks = frame.clocks_ms;
      break;
    }
    case "ack":
      if (state.pendingCmdId === frame.cmd_id) state.pendingCmdId = null;
      break;
    case "reject":
      if (state.pendingCmdId === frame.cmd_id) state.pendingCmdId = null;
      state.message = `${frame.error.kind}: ${frame.error.detail}`;
      break;
    case "game_end":
      state.message = frame.outcome.winner_slot === null
        ? `Draw · ${frame.outcome.reason}`
        : `Slot ${frame.outcome.winner_slot + 1} wins · ${frame.outcome.reason}`;
      break;
    case "match_end":
      state.message = `Match complete · ${frame.scores[0]}–${frame.scores[1]}`;
      if (state.mode === "replay" && state.replayFrames.length >= state.replayTotalSteps) {
        state.replayPlaying = false;
        stopReplayTimer(state);
      }
      break;
    case "replay_meta":
      state.playerNames = [frame.config.players[0]?.name ?? "Player 1", frame.config.players[1]?.name ?? "Player 2"];
      state.replayTotalSteps = frame.games.reduce((total, game) => total + game.steps, 0);
      state.message = `Replay · ${frame.games.length} game(s)`;
      break;
  }
  render(state);
  scheduleRecommendedPass(state);
}

function render(state: AppState): void {
  const snapshot = state.snapshot;
  if (!snapshot) {
    state.root.innerHTML = `<main class="loading"><div class="brand-mark">M</div><h1>Coworld MTG</h1><p>${escapeHtml(state.message)}</p></main>`;
    return;
  }

  const bottom = state.viewerSeat ?? 0;
  const top = bottom === 0 ? 1 : 0;
  const actions = allActions(snapshot);
  const mulliganPending = actions.some(action => action.type === "MulliganDecision");
  const attackActions = actions.filter(action => action.type === "DeclareAttackers");
  const attackable = new Set(attackActions.flatMap(attackObjectIds));
  const blockActions = actions.filter(action => action.type === "DeclareBlockers");
  const blockerIds = new Set(blockActions.flatMap(blockAssignments).map(([blocker]) => blocker));
  const blockTargetIds = new Set(blockActions.flatMap(blockAssignments).map(([, attacker]) => attacker));
  const targetActions = actions.filter(action => action.type === "ChooseTarget");
  const targetObjectIds = new Set(targetActions.map(targetObjectId).filter((id): id is number => id !== null));
  const targetPlayerIds = new Set(targetActions.map(targetPlayerId).filter((id): id is SeatId => id === 0 || id === 1));
  const selectActions = actions.filter(action => action.type === "SelectCards");
  const selectableCardIds = new Set(selectActions.flatMap(selectCardIds));
  const interactiveCombatObjects = new Set([
    ...attackable, ...blockerIds, ...blockTargetIds, ...targetObjectIds, ...selectableCardIds
  ]);
  const combatSelected = new Set([
    ...state.selectedObjects,
    ...state.blockAssignments.keys(),
    ...state.blockAssignments.values(),
    ...(state.focusedBlockerId === null ? [] : [state.focusedBlockerId])
  ]);
  const focused = state.focusedObjectId === null ? undefined : findCard(snapshot, state.focusedObjectId);

  state.root.innerHTML = `
    <div class="arena-shell ${state.pendingCmdId !== null ? "is-pending" : ""}">
      <header class="arena-header">
        <div class="wordmark"><span class="brand-mark">C</span><strong>COGATRICE</strong></div>
        <div class="turn-status">
          <span>TURN ${snapshot.turn} · ${escapeHtml(activeTurnLabel(snapshot, state.playerNames, bottom))}</span>
          <strong>${escapeHtml(phaseLabel(snapshot.phase))}</strong>
          <span>${escapeHtml(priorityText(snapshot, state.playerNames, bottom))}</span>
        </div>
        <div class="header-tools"><span>${escapeHtml(state.message)}</span><button data-log-toggle aria-label="Toggle game log">LOG</button></div>
      </header>

      <main class="arena-board">
        <section class="player-end opponent-end" aria-label="Opponent">
          ${playerBadge(snapshot, top, state.playerNames[top], state.clocks[top], false, targetPlayerIds.has(top))}
          ${hiddenHandHtml(snapshot.players[top].hand.length)}
          ${pileHtml("Library", snapshot.players[top].library_count, "library", top)}
          ${pileHtml("Graveyard", snapshot.players[top].graveyard.length, "graveyard", top, snapshot.players[top].graveyard.at(-1))}
          ${pileHtml("Exile", exileForSeat(snapshot, top).length, "exile", top, exileForSeat(snapshot, top).at(-1))}
        </section>

        ${battlefieldHtml(snapshot, top, "Opponent battlefield", combatSelected, interactiveCombatObjects, state)}

        <section class="table-center">
          ${stackHtml(snapshot, targetObjectIds, state.stackCollapsed)}
          ${phaseRail(snapshot, state)}
          <div class="priority-orb ${snapshot.priority_player === bottom ? "yours" : "theirs"}" title="Priority"></div>
        </section>

        ${battlefieldHtml(snapshot, bottom, "Your battlefield", combatSelected, interactiveCombatObjects, state)}

        <section class="player-end your-end" aria-label="You">
          ${playerBadge(snapshot, bottom, state.playerNames[bottom], state.clocks[bottom], state.mode === "player", targetPlayerIds.has(bottom))}
          ${pileHtml("Library", snapshot.players[bottom].library_count, "library", bottom)}
          ${pileHtml("Graveyard", snapshot.players[bottom].graveyard.length, "graveyard", bottom, snapshot.players[bottom].graveyard.at(-1))}
          ${pileHtml("Exile", exileForSeat(snapshot, bottom).length, "exile", bottom, exileForSeat(snapshot, bottom).at(-1))}
        </section>

        ${state.mode === "player" ? handHtml(snapshot, bottom, state, interactiveCombatObjects) : ""}
      </main>

      <svg class="combat-overlay" data-combat-overlay aria-hidden="true"></svg>
      <div class="damage-effects" data-damage-effects aria-live="polite"></div>
      ${combatSummaryHtml(snapshot, state)}

      ${state.mode === "player" ? (mulliganPending ? "" : actionDock(actions, snapshot, state)) : state.mode === "replay" ? replayControls(state) : spectatorBadge(state.mode)}
      ${focused ? focusPanel(focused, objectActions(snapshot, focused.object_id), snapshot, state.pendingCmdId !== null) : ""}
      <div class="card-preview" data-card-preview></div>
      ${mulliganOverlay(actions, snapshot, state.pendingCmdId !== null)}
      ${state.openZone ? zoneViewer(snapshot, state.openZone) : ""}
      ${state.logOpen ? eventDrawer(state.events) : ""}
    </div>`;

  bindInteractions(
    state,
    actions,
    attackable,
    blockerIds,
    blockTargetIds,
    targetObjectIds,
    targetPlayerIds,
    selectableCardIds
  );
  window.requestAnimationFrame(() => {
    drawCombatOverlay(state);
    drawDamageEffects(state);
  });
}

function bindInteractions(
  state: AppState,
  actions: GameAction[],
  attackable: Set<number>,
  blockerIds: Set<number>,
  blockTargetIds: Set<number>,
  targetObjectIds: Set<number>,
  targetPlayerIds: Set<SeatId>,
  selectableCardIds: Set<number>
): void {
  const snapshot = state.snapshot!;
  state.root.querySelectorAll<HTMLImageElement>(".game-card > img").forEach(image => {
    image.addEventListener("error", () => {
      image.style.display = "none";
      const fallback = image.parentElement?.querySelector<HTMLElement>(".fallback-face");
      if (fallback) fallback.style.display = "block";
    }, { once: true });
  });
  state.root.querySelectorAll<HTMLElement>("[data-object-id]").forEach(element => {
    const objectId = Number(element.dataset.objectId);
    element.addEventListener("click", event => {
      if ((event.target as HTMLElement).closest("button")) return;
      if (targetObjectIds.has(objectId)) {
        const targetAction = actions.find(action => targetObjectId(action) === objectId);
        if (targetAction) sendAction(state, targetAction);
        return;
      } else if (selectableCardIds.has(objectId)) {
        toggleSelected(state.selectedObjects, objectId);
      } else if (attackable.has(objectId)) {
        toggleSelected(state.selectedObjects, objectId);
      } else if (blockerIds.has(objectId)) {
        state.focusedBlockerId = state.focusedBlockerId === objectId ? null : objectId;
      } else if (blockTargetIds.has(objectId) && state.focusedBlockerId !== null) {
        state.blockAssignments.set(state.focusedBlockerId, objectId);
        state.focusedBlockerId = null;
      } else {
        const objectChoices = objectActions(snapshot, objectId);
        if (objectChoices.length === 1 && objectChoices[0]?.type === "TapLandForMana") {
          sendAction(state, objectChoices[0]);
          return;
        }
        state.focusedObjectId = state.focusedObjectId === objectId ? null : objectId;
        state.openZone = null;
      }
      render(state);
    });
    element.addEventListener("mouseenter", () => showPreview(
      state.root,
      findCard(snapshot, objectId) ?? snapshot.stack.find(entry => entry.id === objectId)?.source ?? undefined
    ));
    element.addEventListener("mouseleave", () => showPreview(state.root));
    element.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        element.click();
      }
    });
  });
  state.root.querySelectorAll<HTMLElement>("[data-player-id]").forEach(element => {
    const playerId = Number(element.dataset.playerId) as SeatId;
    if (!targetPlayerIds.has(playerId)) return;
    element.addEventListener("click", () => {
      const targetAction = actions.find(action => targetPlayerId(action) === playerId);
      if (targetAction) sendAction(state, targetAction);
    });
  });

  state.root.querySelectorAll<HTMLButtonElement>("[data-action-index]").forEach(button => {
    button.addEventListener("click", () => {
      const action = actions[Number(button.dataset.actionIndex)];
      if (action) sendAction(state, action);
    });
  });
  state.root.querySelector<HTMLButtonElement>("[data-confirm-attack]")?.addEventListener("click", () => {
    const matching = matchingAttackAction(actions, state.selectedObjects);
    if (matching) sendAction(state, matching);
  });
  state.root.querySelector<HTMLButtonElement>("[data-confirm-blocks]")?.addEventListener("click", () => {
    const matching = matchingBlockAction(actions, state.blockAssignments);
    if (matching) sendAction(state, matching);
  });
  state.root.querySelector<HTMLButtonElement>("[data-confirm-cards]")?.addEventListener("click", () => {
    const matching = matchingSelectCardsAction(actions, state.selectedObjects);
    if (matching) sendAction(state, matching);
  });
  state.root.querySelector<HTMLButtonElement>("[data-clear-selection]")?.addEventListener("click", () => {
    state.selectedObjects.clear();
    state.blockAssignments.clear();
    state.focusedBlockerId = null;
    render(state);
  });
  state.root.querySelector<HTMLButtonElement>("[data-close-focus]")?.addEventListener("click", () => {
    state.focusedObjectId = null;
    render(state);
  });
  state.root.querySelector<HTMLButtonElement>("[data-log-toggle]")?.addEventListener("click", () => {
    state.logOpen = !state.logOpen;
    render(state);
  });
  state.root.querySelector<HTMLButtonElement>("[data-log-close]")?.addEventListener("click", () => {
    state.logOpen = false;
    render(state);
  });
  state.root.querySelectorAll<HTMLButtonElement>("[data-zone-open]").forEach(button => {
    button.addEventListener("click", () => {
      const seat = Number(button.dataset.seat);
      const kind = button.dataset.zoneOpen;
      if ((seat === 0 || seat === 1) && (kind === "graveyard" || kind === "exile")) {
        state.openZone = { seat, kind };
        state.focusedObjectId = null;
        render(state);
        window.requestAnimationFrame(() => state.root.querySelector<HTMLButtonElement>(".zone-viewer [data-zone-close]")?.focus());
      }
    });
  });
  state.root.querySelectorAll<HTMLButtonElement>("[data-phase-stop]").forEach(button => {
    button.addEventListener("click", () => {
      const phase = button.dataset.phaseStop;
      const scope = button.dataset.stopScope as "OwnTurn" | "OpponentsTurns" | undefined;
      if (!phase || !scope) return;
      const stops = togglePhaseStop(snapshot.phase_stops, phase, scope);
      sendAction(state, { type: "SetPhaseStops", data: { stops } });
    });
  });
  state.root.querySelector<HTMLButtonElement>("[data-full-control]")?.addEventListener("click", () => {
    setFullControl(state, !state.holdFullControl, true);
  });
  state.root.querySelector<HTMLButtonElement>("[data-pass-turn]")?.addEventListener("click", () => {
    sendAction(state, {
      type: "SetAutoPass",
      data: { mode: { type: "UntilTurnBoundary", until: "EndOfCurrentTurn" } }
    });
  });
  state.root.querySelector<HTMLButtonElement>("[data-resolve-all]")?.addEventListener("click", () => {
    sendAction(state, { type: "SetAutoPass", data: { mode: { type: "UntilStackEmpty" } } });
  });
  state.root.querySelector<HTMLButtonElement>("[data-cancel-auto-pass]")?.addEventListener("click", () => {
    sendAction(state, { type: "CancelAutoPass" });
  });
  state.root.querySelector<HTMLButtonElement>("[data-stack-toggle]")?.addEventListener("click", () => {
    state.stackCollapsed = !state.stackCollapsed;
    render(state);
  });
  state.root.querySelectorAll<HTMLElement>("[data-zone-close]").forEach(element => {
    element.addEventListener("click", event => {
      if (event.target === element || element instanceof HTMLButtonElement) {
        state.openZone = null;
        render(state);
      }
    });
  });
  state.root.querySelector<HTMLButtonElement>("[data-concede]")?.addEventListener("click", () => {
    if (state.viewerSeat !== null && window.confirm("Concede this game?")) {
      sendAction(state, { type: "Concede", data: { player_id: state.viewerSeat } });
    }
  });
  state.root.querySelector<HTMLButtonElement>("[data-replay-toggle]")?.addEventListener("click", () => {
    state.replayPlaying = !state.replayPlaying;
    if (state.replayPlaying) startReplayTimer(state);
    else stopReplayTimer(state);
    render(state);
  });
  state.root.querySelector<HTMLButtonElement>("[data-replay-prev]")?.addEventListener("click", () => {
    state.replayPlaying = false;
    stopReplayTimer(state);
    showReplayStep(state, Math.max(0, state.replayIndex - 1));
    render(state);
  });
  state.root.querySelector<HTMLButtonElement>("[data-replay-next]")?.addEventListener("click", () => {
    state.replayPlaying = false;
    stopReplayTimer(state);
    showReplayStep(state, Math.min(state.replayFrames.length - 1, state.replayIndex + 1));
    render(state);
  });
  state.root.querySelector<HTMLInputElement>("[data-replay-range]")?.addEventListener("input", event => {
    state.replayPlaying = false;
    stopReplayTimer(state);
    showReplayStep(state, Number((event.currentTarget as HTMLInputElement).value));
    render(state);
  });
}

export function allActions(snapshot: ViewerSnapshot): GameAction[] {
  const seen = new Set<string>();
  const output: GameAction[] = [];
  for (const action of [...snapshot.legal_actions, ...Object.values(snapshot.legal_actions_by_object).flat()]) {
    const key = JSON.stringify(action);
    if (!seen.has(key)) {
      seen.add(key);
      output.push(action);
    }
  }
  return output;
}

function sendAction(state: AppState, action: GameAction): void {
  if (!state.socket || state.socket.readyState !== WebSocket.OPEN || state.pendingCmdId !== null) return;
  const cmdId = state.nextCmdId++;
  state.pendingCmdId = cmdId;
  state.focusedObjectId = null;
  state.focusedBlockerId = null;
  state.selectedObjects.clear();
  state.blockAssignments.clear();
  state.socket.send(JSON.stringify({ cmd_id: cmdId, action }));
  render(state);
}

function scheduleRecommendedPass(state: AppState): void {
  clearRecommendedPass(state);
  const snapshot = state.snapshot;
  if (
    state.mode !== "player"
    || !snapshot
    || state.viewerSeat === null
    || snapshot.priority_player !== state.viewerSeat
    || nestedType(snapshot.waiting_for) !== "Priority"
    || !snapshot.auto_pass_recommended
    || snapshot.auto_pass_mode !== null
    || phaseStopApplies(snapshot, state.viewerSeat)
    || state.fullControl
    || state.pendingCmdId !== null
  ) return;
  const pass = allActions(snapshot).find(action => action.type === "PassPriority");
  if (!pass) return;
  const decisionKey = state.decisionKey;
  state.autoPassTimer = window.setTimeout(() => {
    state.autoPassTimer = null;
    if (
      state.snapshot === snapshot
      && state.decisionKey === decisionKey
      && state.pendingCmdId === null
      && !state.fullControl
    ) sendAction(state, pass);
  }, 180);
}

function clearRecommendedPass(state: AppState): void {
  if (state.autoPassTimer !== null) window.clearTimeout(state.autoPassTimer);
  state.autoPassTimer = null;
}

export function togglePhaseStop(
  stops: ViewerSnapshot["phase_stops"],
  phase: string,
  scope: "OwnTurn" | "OpponentsTurns"
): ViewerSnapshot["phase_stops"] {
  const otherScope = scope === "OwnTurn" ? "OpponentsTurns" : "OwnTurn";
  const withoutPhase = stops.filter(stop => stop.phase !== phase);
  const hasAll = stops.some(stop => stop.phase === phase && stop.scope === "AllTurns");
  const hasScope = stops.some(stop => stop.phase === phase && stop.scope === scope);
  const hasOther = stops.some(stop => stop.phase === phase && stop.scope === otherScope);
  if (hasAll) return [...withoutPhase, { phase, scope: otherScope }];
  if (hasScope) return hasOther ? [...withoutPhase, { phase, scope: otherScope }] : withoutPhase;
  if (hasOther) return [...withoutPhase, { phase, scope: "AllTurns" }];
  return [...stops, { phase, scope }];
}

function hasPhaseStop(
  stops: ViewerSnapshot["phase_stops"],
  phase: string,
  scope: "OwnTurn" | "OpponentsTurns"
): boolean {
  return stops.some(stop => stop.phase === phase && (stop.scope === scope || stop.scope === "AllTurns"));
}

function phaseStopApplies(snapshot: ViewerSnapshot, viewer: SeatId): boolean {
  return snapshot.phase_stops.some(stop => stop.phase === snapshot.phase && (
    stop.scope === "AllTurns"
    || (stop.scope === "OwnTurn" && snapshot.active_player === viewer)
    || (stop.scope === "OpponentsTurns" && snapshot.active_player !== viewer)
  ));
}

function bindKeyboardControls(state: AppState): void {
  window.addEventListener("keydown", event => {
    if (event.repeat || isTypingTarget(event.target)) return;
    if (event.key === "Escape" && state.openZone) {
      event.preventDefault();
      state.openZone = null;
      render(state);
      return;
    }
    if (event.key === "Control") {
      event.preventDefault();
      if (event.shiftKey) setFullControl(state, !state.holdFullControl, true);
      else setFullControl(state, true, false);
      return;
    }
    if (event.code === "Space") {
      const pass = state.snapshot && allActions(state.snapshot).find(action => action.type === "PassPriority");
      if (pass) {
        event.preventDefault();
        sendAction(state, pass);
      }
      return;
    }
    if (
      event.key === "Enter"
      && !event.shiftKey
      && state.snapshot
      && state.viewerSeat !== null
      && state.snapshot.priority_player === state.viewerSeat
      && nestedType(state.snapshot.waiting_for) === "Priority"
    ) {
      event.preventDefault();
      sendAction(state, {
        type: "SetAutoPass",
        data: { mode: { type: "UntilTurnBoundary", until: "EndOfCurrentTurn" } }
      });
    }
  });
  window.addEventListener("keyup", event => {
    if (event.key === "Control" && !state.holdFullControl) setFullControl(state, false, false);
  });
  window.addEventListener("blur", () => {
    if (!state.holdFullControl) setFullControl(state, false, false);
  });
}

function setFullControl(state: AppState, enabled: boolean, held: boolean): void {
  state.holdFullControl = held ? enabled : state.holdFullControl;
  state.fullControl = enabled || state.holdFullControl;
  clearRecommendedPass(state);
  if (state.fullControl && state.snapshot?.auto_pass_mode) {
    sendAction(state, { type: "CancelAutoPass" });
    return;
  }
  render(state);
  scheduleRecommendedPass(state);
}

function isTypingTarget(target: EventTarget | null): boolean {
  return target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement;
}

function playerBadge(
  snapshot: ViewerSnapshot,
  seat: SeatId,
  name: string,
  clock: number | null,
  own: boolean,
  targetable: boolean
): string {
  const player = snapshot.players[seat];
  const mana = manaPoolHtml(player.mana_pool.mana ?? []);
  return `<div class="player-badge ${snapshot.active_player === seat ? "active" : ""} ${snapshot.priority_player === seat ? "priority" : ""} ${targetable ? "targetable" : ""}" data-player-id="${seat}">
    <div class="avatar">${escapeHtml(name.slice(0, 1).toUpperCase())}</div>
    <div class="identity"><strong>${escapeHtml(name)}</strong><span>${own ? "YOU" : `SEAT ${seat + 1}`}</span></div>
    ${mana}<div class="clock">${clock === null ? "" : clockText(clock)}</div>
    <div class="life"><span class="life-label">LIFE</span>${player.life}</div>
  </div>`;
}

function battlefieldHtml(
  snapshot: ViewerSnapshot,
  seat: SeatId,
  label: string,
  selected: Set<number>,
  attackable: Set<number>,
  state: AppState
): string {
  const permanents = snapshot.battlefield.filter(card => card.controller === seat);
  const lands = permanents.filter(isLand);
  const nonlands = permanents.filter(card => !isLand(card));
  return `<section class="battlefield ${seat === (state.viewerSeat ?? 0) ? "friendly" : "opposing"}" aria-label="${escapeHtml(label)}">
    <h2>${escapeHtml(label)}</h2>
    <div class="permanent-row creatures">${permanentCards(nonlands, snapshot, selected, attackable)}</div>
    <div class="permanent-row lands">${permanentCards(lands, snapshot, selected, attackable)}</div>
  </section>`;
}

function permanentCards(cards: CardView[], snapshot: ViewerSnapshot, selected: Set<number>, attackable: Set<number>): string {
  if (!cards.length) return `<span class="zone-empty"></span>`;
  return cards.map(card => cardHtml(card, snapshot, {
    selected: selected.has(card.object_id),
    actionable: objectActions(snapshot, card.object_id).length > 0 || attackable.has(card.object_id),
    compact: true
  })).join("");
}

function handHtml(snapshot: ViewerSnapshot, seat: SeatId, state: AppState, attackable: Set<number>): string {
  const hand = snapshot.players[seat].hand;
  return `<section class="hand-zone" aria-label="Your hand"><h2>Your hand <span>${hand.length}</span></h2><div class="hand-fan" style="--hand-size:${hand.length}">${hand.map((card, index) =>
    cardHtml(card, snapshot, {
      selected: state.focusedObjectId === card.object_id,
      actionable: objectActions(snapshot, card.object_id).length > 0 || attackable.has(card.object_id),
      handIndex: index
    })).join("")}</div></section>`;
}

interface CardOptions {
  selected?: boolean;
  actionable?: boolean;
  compact?: boolean;
  handIndex?: number;
}

function cardHtml(card: CardView, snapshot: ViewerSnapshot, options: CardOptions = {}): string {
  const effective = snapshot.spell_costs[String(card.object_id)] ?? card.mana_cost;
  const blocked = card.blocked;
  const classes = [
    "game-card",
    card.tapped ? "tapped" : "",
    card.attacking ? "attacking" : "",
    blocked ? "blocked" : "",
    card.blocking.length ? "blocking" : "",
    options.selected ? "selected" : "",
    options.actionable ? "actionable" : "",
    options.compact ? "compact" : "",
    card.face_down ? "face-down" : ""
  ].filter(Boolean).join(" ");
  const style = options.handIndex === undefined ? "" : `style="--hand-index:${options.handIndex}"`;
  const image = card.face_down || card.name === "Hidden Card"
    ? `<div class="card-back"><span>C</span></div>`
    : `<img loading="eager" src="${artUrl(card)}" alt="${escapeHtml(card.name)}" />`;
  const pt = card.power === null ? "" : `<b class="pt">${card.power}/${card.toughness ?? 0}</b>`;
  return `<article class="${classes}" data-object-id="${card.object_id}" ${style} tabindex="0" aria-label="${escapeHtml(card.name)}">
    ${image}<div class="fallback-face"><strong>${escapeHtml(card.face_down ? "Hidden card" : card.name)}</strong><span>${escapeHtml(manaCost(effective))}</span><small>${escapeHtml(card.type_line)}</small>${pt}</div>
    ${counterHtml(card.counters)}${card.tapped ? `<span class="status-chip">TAPPED</span>` : ""}${card.attacking ? `<span class="status-chip attack-chip">${blocked ? "BLOCKED" : "ATTACKING"}</span>` : ""}${card.blocking.length ? `<span class="status-chip block-chip">BLOCKING</span>` : ""}
  </article>`;
}

function focusPanel(card: CardView, actions: GameAction[], snapshot: ViewerSnapshot, disabled: boolean): string {
  return `<section class="focus-panel" aria-label="Card actions">
    <button class="close" data-close-focus aria-label="Close card actions">×</button>
    <div class="focus-card">${cardDetailHtml(card, snapshot)}</div>
    <div class="focus-actions"><span>AVAILABLE ACTIONS</span>${actions.length
      ? actions.map(action => `<button data-action-index="${allActions(snapshot).findIndex(candidate => sameAction(candidate, action))}" ${disabled ? "disabled" : ""}>${escapeHtml(actionLabel(action, snapshot))}</button>`).join("")
      : `<p>${escapeHtml(unavailableCardMessage(card, snapshot))}</p>`}</div>
  </section>`;
}

function cardDetailHtml(card: CardView, snapshot: ViewerSnapshot): string {
  const effective = snapshot.spell_costs[String(card.object_id)] ?? card.mana_cost;
  const pt = card.power === null ? "" : `<b>${card.power}/${card.toughness ?? 0}</b>`;
  return `<img src="${artUrl(card)}" alt="" /><div><strong>${escapeHtml(card.name)}</strong><span>${escapeHtml(manaCost(effective))}</span><small>${escapeHtml(card.type_line)}</small><p>${escapeHtml(card.oracle_text)}</p>${pt}</div>`;
}

function actionDock(actions: GameAction[], snapshot: ViewerSnapshot, state: AppState): string {
  const disabled = state.pendingCmdId !== null;
  const attackActions = actions.filter(action => action.type === "DeclareAttackers");
  const blockerActions = actions.filter(action => action.type === "DeclareBlockers");
  const targetActions = actions.filter(action => action.type === "ChooseTarget");
  const selectActions = actions.filter(action => action.type === "SelectCards");
  const matchingAttacks = matchingAttackActions(actions, state.selectedObjects);
  const matchingBlocks = matchingBlockAction(actions, state.blockAssignments);
  const matchingCards = matchingSelectCardsAction(actions, state.selectedObjects);
  const pass = actions.find(action => action.type === "PassPriority");
  const canSetAutoPass = state.viewerSeat !== null
    && snapshot.priority_player === state.viewerSeat
    && nestedType(snapshot.waiting_for) === "Priority"
    && !disabled;
  const globals = actions.filter(action => ![
    "PassPriority", "PlayLand", "CastSpell", "ActivateAbility", "MulliganDecision", "DeclareAttackers", "DeclareBlockers", "SelectCards",
    "TapLandForMana", "UntapLandForMana", "SpendPoolMana", "UnspendPoolMana"
  ].includes(action.type) && !(action.type === "ChooseTarget" && action.data?.target !== null));
  const prompt = decisionPrompt(
    snapshot,
    state.selectedObjects.size,
    attackActions.length > 0,
    blockerActions.length > 0,
    targetActions.some(action => action.data?.target !== null),
    selectActions.length > 0,
    state
  );
  return `<section class="action-dock" aria-label="Turn actions">
    <div class="priority-controls" aria-label="Priority controls">
      <button class="control-toggle ${state.fullControl ? "active" : ""}" data-full-control aria-pressed="${state.fullControl}" title="Full Control (Ctrl)">Full Control</button>
      ${snapshot.auto_pass_mode
        ? `<button class="control-toggle active" data-cancel-auto-pass title="Cancel automatic passing">Cancel Auto-Pass</button>`
        : canSetAutoPass ? `<button class="control-toggle" data-pass-turn title="Pass until Phase finds a response or stop (Enter)">Pass Until Response</button>` : ""}
      ${snapshot.stack.length && !snapshot.auto_pass_mode && canSetAutoPass ? `<button class="control-toggle" data-resolve-all title="Pass until this stack resolves">Resolve All</button>` : ""}
    </div>
    <div class="decision-copy"><span>${escapeHtml(prompt.eyebrow)}</span><strong>${escapeHtml(prompt.title)}</strong><small>${escapeHtml(prompt.detail)}</small></div>
    <div class="decision-actions">
      ${attackActions.length ? `<button class="secondary-action" data-clear-selection ${disabled ? "disabled" : ""}>Reset</button>${matchingAttacks.length > 1
        ? matchingAttacks.map(action => `<button class="primary-action combat-action" data-action-index="${actions.indexOf(action)}" ${disabled ? "disabled" : ""}>${escapeHtml(attackChoiceLabel(action, snapshot, state.playerNames))}</button>`).join("")
        : `<button class="primary-action combat-action" data-confirm-attack ${!matchingAttacks.length || disabled ? "disabled" : ""}>${state.selectedObjects.size ? `Attack (${state.selectedObjects.size})` : "No attacks"}</button>`}` : ""}
      ${blockerActions.length ? `<button class="secondary-action" data-clear-selection ${disabled ? "disabled" : ""}>Reset</button><button class="primary-action combat-action" data-confirm-blocks ${!matchingBlocks || disabled ? "disabled" : ""}>${state.blockAssignments.size ? `Block (${state.blockAssignments.size})` : "No blocks"}</button>` : ""}
      ${selectActions.length ? `<button class="secondary-action" data-clear-selection ${disabled ? "disabled" : ""}>Reset</button><button class="primary-action" data-confirm-cards ${!matchingCards || disabled ? "disabled" : ""}>Confirm (${state.selectedObjects.size})</button>` : ""}
      ${globals.map(action => `<button class="choice-action" data-action-index="${actions.indexOf(action)}" ${disabled ? "disabled" : ""}>${escapeHtml(actionLabel(action, snapshot))}</button>`).join("")}
      ${pass ? `<button class="primary-action" data-action-index="${actions.indexOf(pass)}" ${disabled ? "disabled" : ""}>${passLabel(snapshot.phase)}</button>` : ""}
    </div>
    <button class="menu-action" data-concede aria-label="Concede" title="Concede" ${disabled ? "disabled" : ""}>•••</button>
  </section>`;
}

function mulliganOverlay(actions: GameAction[], snapshot: ViewerSnapshot, disabled: boolean): string {
  const mulligans = actions.filter(action => action.type === "MulliganDecision");
  if (!mulligans.length) return "";
  return `<div class="decision-overlay"><section class="mulligan-dialog">
    <span>OPENING HAND</span><h2>Keep this hand?</h2><p>You may take a mulligan and draw a new hand. Phase will handle cards placed on the bottom.</p>
    <div>${mulligans.map(action => {
      const index = allActions(snapshot).findIndex(candidate => sameAction(candidate, action));
      const choice = nestedType(action.data?.choice) ?? "Decide";
      return `<button class="${choice === "Keep" ? "primary-action" : "secondary-action"}" data-action-index="${index}" ${disabled ? "disabled" : ""}>${choice}</button>`;
    }).join("")}</div>
  </section></div>`;
}

function stackHtml(snapshot: ViewerSnapshot, targetObjectIds: Set<number>, collapsed: boolean): string {
  if (!snapshot.stack.length) return "";
  const entries = snapshot.stack.slice().reverse();
  return `<section class="stack-zone ${collapsed ? "collapsed" : ""}" aria-label="Stack">
    <header><span>STACK · ${entries.length}</span><button data-stack-toggle aria-label="${collapsed ? "Expand" : "Collapse"} stack">${collapsed ? "+" : "−"}</button></header>
    <div class="stack-cards">${entries.map((entry, index) => {
      const targetable = targetObjectIds.has(entry.id);
      const name = entry.source?.name ?? `Ability ${entry.id}`;
      const art = entry.source && !entry.source.face_down ? `<img src="${artUrl(entry.source)}" alt="" />` : `<div class="card-back"><span>C</span></div>`;
      return `<article class="stack-card ${index === 0 ? "top" : ""} ${targetable ? "targetable" : ""}" data-object-id="${entry.id}" data-source-object-id="${entry.source_id}" tabindex="0" style="--stack-index:${index}" aria-label="${escapeHtml(name)} on the stack">
        ${art}<div class="stack-card-copy"><strong>${escapeHtml(name)}</strong><small>${escapeHtml(index === 0 ? "Next to resolve" : splitWords(nestedType(entry.kind) ?? "On the stack"))}</small></div>
      </article>`;
    }).join("")}</div>
  </section>`;
}

function phaseRail(snapshot: ViewerSnapshot, state: AppState): string {
  let matchedCurrent = false;
  const interactive = state.mode === "player";
  return `<nav class="phase-rail" aria-label="Turn phases">${PHASES.map(([phase, label]) => {
    const active = phase === snapshot.phase && (!matchedCurrent || phase !== "PostCombatMain");
    if (active) matchedCurrent = true;
    const own = hasPhaseStop(snapshot.phase_stops, phase, "OwnTurn");
    const opponent = hasPhaseStop(snapshot.phase_stops, phase, "OpponentsTurns");
    return `<div class="phase-step ${active ? "current" : ""}" title="${label}">
      <span>${label.slice(0, 1)}</span>
      ${interactive && phase !== "Untap" ? `<button class="stop own-stop ${own ? "set" : ""}" data-phase-stop="${phase}" data-stop-scope="OwnTurn" aria-pressed="${own}" aria-label="${own ? "Remove" : "Set"} ${label} stop on your turn"></button>
      <button class="stop opponent-stop ${opponent ? "set" : ""}" data-phase-stop="${phase}" data-stop-scope="OpponentsTurns" aria-pressed="${opponent}" aria-label="${opponent ? "Remove" : "Set"} ${label} stop on opponent turns"></button>` : ""}
    </div>`;
  }).join("")}</nav>`;
}

function pileHtml(label: string, count: number, kind: string, seat: SeatId, topCard?: CardView): string {
  const browseable = kind !== "library";
  const attributes = browseable
    ? `data-zone-open="${kind}" data-seat="${seat}" aria-label="View ${label}: ${count} cards"`
    : `disabled aria-label="${label}: ${count} cards"`;
  const face = kind === "library"
    ? `<div class="pile-card-back"><i>C</i></div>`
    : topCard && !topCard.face_down && topCard.name !== "Hidden Card"
      ? `<img src="${artUrl(topCard)}" alt="" />`
      : `<div class="pile-empty"></div>`;
  return `<button class="card-pile ${kind} ${browseable ? "browseable" : ""}" title="${label}: ${count}" ${attributes}>${face}<span class="pile-count">${count}</span><small>${label}</small></button>`;
}

function zoneViewer(snapshot: ViewerSnapshot, zone: { seat: SeatId; kind: "graveyard" | "exile" }): string {
  const cards = zone.kind === "graveyard" ? snapshot.players[zone.seat].graveyard : exileForSeat(snapshot, zone.seat);
  const label = zone.kind === "graveyard" ? "Graveyard" : "Exile";
  return `<div class="zone-overlay" data-zone-close><section class="zone-viewer" role="dialog" aria-modal="true" aria-label="${label}">
    <header><div><span>SEAT ${zone.seat + 1}</span><h2>${label}</h2><p>${cards.length} card${cards.length === 1 ? "" : "s"}</p></div><button data-zone-close aria-label="Close ${label}">×</button></header>
    <div class="zone-cards">${cards.length ? cards.map(card => cardHtml(card, snapshot, { actionable: objectActions(snapshot, card.object_id).length > 0 })).join("") : `<p class="empty-zone-copy">There are no cards here.</p>`}</div>
  </section></div>`;
}

function exileForSeat(snapshot: ViewerSnapshot, seat: SeatId): CardView[] {
  return snapshot.exile.filter(card => card.owner === seat);
}

function queueDamageCues(state: AppState, events: unknown[]): void {
  for (const event of events) {
    const value = event as { type?: string; data?: Record<string, unknown> };
    if (value.type !== "DamageDealt" || !value.data) continue;
    const sourceId = Number(value.data.source_id);
    const amount = Number(value.data.amount);
    const target = damageTarget(value.data.target);
    if (!Number.isFinite(sourceId) || !Number.isFinite(amount) || !target) continue;
    const cue: DamageCue = {
      id: state.nextDamageCueId++,
      sourceId,
      target,
      amount,
      isCombat: value.data.is_combat === true,
      sourcePoint: anchorPoint(state.root, "object", sourceId),
      targetPoint: anchorPoint(state.root, target.type.toLowerCase(), target.id)
    };
    state.damageCues.push(cue);
    window.setTimeout(() => {
      state.damageCues = state.damageCues.filter(candidate => candidate.id !== cue.id);
      drawDamageEffects(state);
    }, 900);
  }
}

function queueBlockPulse(state: AppState, events: unknown[]): void {
  if (!events.some(event => (event as { type?: string }).type === "BlockersDeclared")) return;
  state.blockPulseUntil = Date.now() + 700;
  window.setTimeout(() => drawCombatOverlay(state), 700);
}

function damageTarget(value: unknown): DamageCue["target"] | null {
  if (!value || typeof value !== "object") return null;
  const target = value as Record<string, unknown>;
  if (Number.isFinite(Number(target.Object))) return { type: "Object", id: Number(target.Object) };
  if (Number.isFinite(Number(target.Player))) return { type: "Player", id: Number(target.Player) };
  if (target.type === "Object" && Number.isFinite(Number(target.data))) return { type: "Object", id: Number(target.data) };
  if (target.type === "Player" && Number.isFinite(Number(target.data))) return { type: "Player", id: Number(target.data) };
  return null;
}

function anchorPoint(root: HTMLElement, kind: string, id: number): Point | undefined {
  const selector = kind === "player"
    ? `.player-badge[data-player-id="${id}"]`
    : `.battlefield [data-object-id="${id}"]`;
  const element = root.querySelector<HTMLElement>(selector)
    ?? (kind === "object"
      ? root.querySelector<HTMLElement>(`.stack-card[data-source-object-id="${id}"], .stack-card[data-object-id="${id}"]`)
      : null);
  if (!element) return undefined;
  const rootRect = root.getBoundingClientRect();
  const rect = element.getBoundingClientRect();
  return { x: rect.left - rootRect.left + rect.width / 2, y: rect.top - rootRect.top + rect.height / 2 };
}

function drawCombatOverlay(state: AppState): void {
  const overlay = state.root.querySelector<SVGSVGElement>("[data-combat-overlay]");
  const snapshot = state.snapshot;
  if (!overlay || !snapshot) return;
  overlay.setAttribute("viewBox", `0 0 ${state.root.clientWidth} ${state.root.clientHeight}`);
  const lines: string[] = [];
  for (const attacker of snapshot.combat?.attackers ?? []) {
    const source = anchorPoint(state.root, "object", attacker.object_id);
    const target = attacker.attack_target.type === "Player"
      ? anchorPoint(state.root, "player", attacker.attack_target.data)
      : anchorPoint(state.root, "object", attacker.attack_target.data);
    if (source && target) lines.push(combatLine(source, target, "attack-link"));
  }
  for (const blocker of snapshot.battlefield) {
    for (const attackerId of blocker.blocking) {
      const source = anchorPoint(state.root, "object", blocker.object_id);
      const target = anchorPoint(state.root, "object", attackerId);
      if (source && target) lines.push(combatLine(
        source,
        target,
        `block-link ${Date.now() < state.blockPulseUntil ? "declared" : ""}`
      ));
    }
  }
  for (const [blockerId, attackerId] of state.blockAssignments) {
    const source = anchorPoint(state.root, "object", blockerId);
    const target = anchorPoint(state.root, "object", attackerId);
    if (source && target) lines.push(combatLine(source, target, "block-link draft"));
  }
  overlay.innerHTML = `<defs>
    <marker id="attack-arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z"></path></marker>
    <marker id="block-arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z"></path></marker>
  </defs>${lines.join("")}`;
}

function combatLine(source: Point, target: Point, classes: string): string {
  return `<line class="${classes}" x1="${source.x}" y1="${source.y}" x2="${target.x}" y2="${target.y}"></line>`;
}

function drawDamageEffects(state: AppState): void {
  const container = state.root.querySelector<HTMLElement>("[data-damage-effects]");
  if (!container) return;
  container.innerHTML = state.damageCues.map(cue => {
    const source = anchorPoint(state.root, "object", cue.sourceId) ?? cue.sourcePoint;
    const target = anchorPoint(state.root, cue.target.type.toLowerCase(), cue.target.id) ?? cue.targetPoint;
    if (!source || !target) return "";
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const distance = Math.hypot(dx, dy);
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    return `<div class="damage-beam ${cue.isCombat ? "combat" : ""}" style="left:${source.x}px;top:${source.y}px;width:${distance}px;--angle:${angle}deg"></div>
      <div class="damage-burst ${cue.isCombat ? "combat" : ""}" style="left:${target.x}px;top:${target.y}px" role="status" aria-label="${cue.amount} damage">−${cue.amount}</div>`;
  }).join("");
}

function combatSummaryHtml(snapshot: ViewerSnapshot, state: AppState): string {
  const summaries: string[] = [];
  for (const blocker of snapshot.battlefield) {
    for (const attackerId of blocker.blocking) {
      const attacker = findCard(snapshot, attackerId);
      summaries.push(`${blocker.name} blocks ${attacker?.name ?? `attacker ${attackerId}`}`);
    }
  }
  for (const [blockerId, attackerId] of state.blockAssignments) {
    const blocker = findCard(snapshot, blockerId);
    const attacker = findCard(snapshot, attackerId);
    summaries.push(`${blocker?.name ?? `Creature ${blockerId}`} will block ${attacker?.name ?? `attacker ${attackerId}`}`);
  }
  return summaries.length
    ? `<div class="sr-only" aria-live="polite">${summaries.map(escapeHtml).join(". ")}</div>`
    : "";
}

function counterHtml(counters: unknown): string {
  if (!counters || typeof counters !== "object" || Array.isArray(counters)) return "";
  const entries = Object.entries(counters as Record<string, unknown>)
    .filter(([, count]) => Number(count) > 0)
    .slice(0, 3);
  if (!entries.length) return "";
  return `<div class="counter-rack">${entries.map(([name, count]) => `<span title="${escapeHtml(splitWords(name))}">${escapeHtml(counterLabel(name))} ${Number(count)}</span>`).join("")}</div>`;
}

function counterLabel(name: string): string {
  const normalized = name.toLowerCase();
  if (normalized.includes("plus") || normalized.includes("+1")) return "+1/+1";
  if (normalized.includes("minus") || normalized.includes("-1")) return "−1/−1";
  return splitWords(name).slice(0, 8);
}

function hiddenHandHtml(count: number): string {
  return `<div class="opponent-hand" aria-label="Opponent hand: ${count} cards">${Array.from({ length: Math.min(count, 9) }, (_, index) => `<i style="--card-index:${index}"></i>`).join("")}</div>`;
}

function manaPoolHtml(mana: Array<{ color: string }>): string {
  if (!mana.length) return `<div class="mana-pool"></div>`;
  return `<div class="mana-pool">${mana.map(unit => `<i class="mana ${unit.color.toLowerCase()}">${manaShard(unit.color)}</i>`).join("")}</div>`;
}

function eventDrawer(events: unknown[]): string {
  return `<aside class="event-drawer"><header><strong>GAME LOG</strong><button data-log-close>×</button></header><div>${events.slice(-100).reverse().map(eventHtml).join("")}</div></aside>`;
}

function eventHtml(event: unknown): string {
  const value = event as { type?: string; data?: unknown };
  return `<article><strong>${escapeHtml(splitWords(value.type ?? "Event"))}</strong><span>${escapeHtml(eventSummary(value.data))}</span></article>`;
}

function spectatorBadge(mode: AppState["mode"]): string {
  return `<div class="spectator-badge">${mode === "replay" ? "REPLAY" : "SPECTATING"}</div>`;
}

function replayControls(state: AppState): string {
  const received = state.replayFrames.length;
  const current = Math.max(0, state.replayIndex + 1);
  const total = Math.max(received, state.replayTotalSteps);
  return `<section class="replay-controls" aria-label="Replay controls">
    <button data-replay-prev aria-label="Previous replay step" ${state.replayIndex <= 0 ? "disabled" : ""}>‹</button>
    <button class="replay-toggle" data-replay-toggle>${state.replayPlaying ? "Pause" : "Play"}</button>
    <button data-replay-next aria-label="Next replay step" ${state.replayIndex >= received - 1 ? "disabled" : ""}>›</button>
    <input data-replay-range aria-label="Replay timeline" type="range" min="0" max="${Math.max(0, received - 1)}" value="${Math.max(0, state.replayIndex)}" ${received < 2 ? "disabled" : ""} />
    <strong>${current} / ${total || "…"}</strong>
  </section>`;
}

function showReplayStep(state: AppState, index: number): void {
  const bounded = Math.max(0, Math.min(index, state.replayFrames.length - 1));
  const frame = state.replayFrames[bounded];
  if (!frame?.step) return;
  queueDamageCues(state, frame.step.events);
  state.replayIndex = bounded;
  state.snapshot = frame.step.state;
  state.events = state.replayFrames.slice(0, bounded + 1).flatMap(candidate => {
    if (!candidate.step) return [];
    return candidate.step.action
      ? [...candidate.step.events, { type: "Action", data: candidate.step.action }]
      : candidate.step.events;
  });
  if (frame.clocks_ms) state.clocks = frame.clocks_ms;
  state.decisionKey = snapshotDecisionKey(frame.step.state);
}

function startReplayTimer(state: AppState): void {
  stopReplayTimer(state);
  state.replayTimer = window.setInterval(() => {
    if (!state.replayPlaying || state.replayIndex >= state.replayFrames.length - 1) return;
    showReplayStep(state, state.replayIndex + 1);
    render(state);
  }, 700);
}

function stopReplayTimer(state: AppState): void {
  if (state.replayTimer !== null) window.clearInterval(state.replayTimer);
  state.replayTimer = null;
}

function showPreview(root: HTMLElement, card?: CardView): void {
  const preview = root.querySelector<HTMLElement>("[data-card-preview]");
  if (!preview) return;
  if (!card || card.face_down || card.name === "Hidden Card") {
    preview.classList.remove("visible");
    preview.innerHTML = "";
    return;
  }
  preview.innerHTML = `<img src="${artUrl(card)}" alt="${escapeHtml(card.name)}" />`;
  preview.classList.add("visible");
}

function objectActions(snapshot: ViewerSnapshot, objectId: number): GameAction[] {
  return allActions(snapshot).filter(action => actionSourceId(action) === objectId);
}

function actionSourceId(action: GameAction): number {
  return Number(action.data?.object_id ?? action.data?.source_id ?? -1);
}

function attackObjectIds(action: GameAction): number[] {
  return attackEntries(action).map(([objectId]) => objectId);
}

function attackEntries(action: GameAction): Array<[number, unknown]> {
  const attacks = action.data?.attacks;
  if (!Array.isArray(attacks)) return [];
  return attacks.map(entry => {
    if (Array.isArray(entry)) return [Number(entry[0]), entry[1]] as [number, unknown];
    const value = entry as { object_id?: unknown; target?: unknown; attack_target?: unknown };
    return [Number(value.object_id), value.target ?? value.attack_target] as [number, unknown];
  }).filter(([objectId]) => Number.isFinite(objectId));
}

function blockAssignments(action: GameAction): Array<[number, number]> {
  const assignments = action.data?.assignments;
  if (!Array.isArray(assignments)) return [];
  return assignments.map(entry => {
    if (Array.isArray(entry)) return [Number(entry[0]), Number(entry[1])] as [number, number];
    const value = entry as { blocker_id?: unknown; attacker_id?: unknown };
    return [Number(value.blocker_id), Number(value.attacker_id)] as [number, number];
  }).filter(([blocker, attacker]) => Number.isFinite(blocker) && Number.isFinite(attacker));
}

function targetObjectId(action: GameAction): number | null {
  if (action.type !== "ChooseTarget" || !action.data?.target || typeof action.data.target !== "object") return null;
  const target = action.data.target as Record<string, unknown>;
  const value = target.Object ?? (target.type === "Object" ? target.data : undefined);
  const id = Number(value);
  return Number.isFinite(id) ? id : null;
}

function targetPlayerId(action: GameAction): SeatId | null {
  if (action.type !== "ChooseTarget" || !action.data?.target || typeof action.data.target !== "object") return null;
  const target = action.data.target as Record<string, unknown>;
  const value = target.Player ?? (target.type === "Player" ? target.data : undefined);
  const id = Number(value);
  return id === 0 || id === 1 ? id : null;
}

function selectCardIds(action: GameAction): number[] {
  if (action.type !== "SelectCards" || !Array.isArray(action.data?.cards)) return [];
  return action.data.cards.map(Number).filter(Number.isFinite);
}

export function matchingAttackAction(actions: GameAction[], selected: Set<number>): GameAction | undefined {
  return matchingAttackActions(actions, selected)[0];
}

export function matchingAttackActions(actions: GameAction[], selected: Set<number>): GameAction[] {
  const wanted = [...selected].sort((a, b) => a - b).join(",");
  return actions.filter(action => action.type === "DeclareAttackers" && attackObjectIds(action).sort((a, b) => a - b).join(",") === wanted);
}

function attackChoiceLabel(action: GameAction, snapshot: ViewerSnapshot, names: [string, string]): string {
  const entries = attackEntries(action);
  if (!entries.length) return "No attacks";
  const labels = [...new Set(entries.map(([, target]) => attackTargetLabel(target, snapshot, names)))];
  if (labels.length === 1) return `Attack ${labels[0]}`;
  return entries.map(([objectId, target]) => {
    const attacker = findCard(snapshot, objectId)?.name ?? `Creature ${objectId}`;
    return `${attacker} → ${attackTargetLabel(target, snapshot, names)}`;
  }).join("; ");
}

function attackTargetLabel(target: unknown, snapshot: ViewerSnapshot, names: [string, string]): string {
  if (!target || typeof target !== "object") return "opponent";
  const value = target as Record<string, unknown>;
  const type = String(value.type ?? Object.keys(value)[0] ?? "");
  const data = value.data ?? value[type];
  if (type === "Player") {
    const seat = Number(typeof data === "object" && data !== null && "0" in data ? (data as Record<string, unknown>)["0"] : data);
    return seat === 0 || seat === 1 ? names[seat] : "player";
  }
  if (type === "Planeswalker" || type === "Battle") {
    const objectId = Number(data);
    return findCard(snapshot, objectId)?.name ?? `${type.toLowerCase()} ${objectId}`;
  }
  return "opponent";
}

export function matchingBlockAction(actions: GameAction[], selected: Map<number, number>): GameAction | undefined {
  const wanted = [...selected.entries()].sort(comparePair).map(pair => pair.join(":")).join(",");
  return actions.find(action => action.type === "DeclareBlockers"
    && blockAssignments(action).sort(comparePair).map(pair => pair.join(":")).join(",") === wanted);
}

export function matchingSelectCardsAction(actions: GameAction[], selected: Set<number>): GameAction | undefined {
  const wanted = [...selected].sort((a, b) => a - b).join(",");
  return actions.find(action => action.type === "SelectCards"
    && selectCardIds(action).sort((a, b) => a - b).join(",") === wanted);
}

export function shouldBufferReplayFrame(received: number, authoritativeTotal: number): boolean {
  return authoritativeTotal <= 0 || received < authoritativeTotal;
}

function comparePair(left: [number, number], right: [number, number]): number {
  return left[0] - right[0] || left[1] - right[1];
}

function toggleSelected(selected: Set<number>, objectId: number): void {
  if (selected.has(objectId)) selected.delete(objectId);
  else selected.add(objectId);
}

export function actionLabel(action: GameAction, snapshot: ViewerSnapshot): string {
  const data = action.data ?? {};
  const source = findCard(snapshot, actionSourceId(action));
  switch (action.type) {
    case "PassPriority": return "Pass priority";
    case "PlayLand": return `Play ${source?.name ?? "land"}`;
    case "CastSpell": return `Cast ${source?.name ?? "spell"}`;
    case "ActivateAbility": return `Activate ${source?.name ?? "ability"}`;
    case "TapLandForMana": return `Tap ${source?.name ?? "land"} for mana`;
    case "UntapLandForMana": return `Undo mana from ${source?.name ?? "land"}`;
    case "SpendPoolMana": return "Use this mana";
    case "UnspendPoolMana": return "Use different mana";
    case "SetAutoPass": return "Pass automatically";
    case "CancelAutoPass": return "Cancel automatic passing";
    case "SetPhaseStops": return "Update phase stops";
    case "MulliganDecision": return `Mulligan: ${nestedType(data.choice) ?? "decide"}`;
    case "DeclareAttackers": return `Attack with ${attackObjectIds(action).length} creature(s)`;
    case "DeclareBlockers": return `Block with ${blockAssignments(action).length} creature(s)`;
    case "SelectCards": return `Select ${arrayLength(data.cards)} card(s)`;
    case "ChooseTarget": {
      const objectId = targetObjectId(action);
      const playerId = targetPlayerId(action);
      if (objectId !== null) return `Target ${findCard(snapshot, objectId)?.name ?? `card ${objectId}`}`;
      if (playerId !== null) return `Target player ${playerId + 1}`;
      return "Done choosing targets";
    }
    case "Concede": return "Concede";
    default: return `${splitWords(action.type)} ${shortJson(data)}`.trim();
  }
}

function decisionPrompt(
  snapshot: ViewerSnapshot,
  selectedCount: number,
  attacking: boolean,
  blocking: boolean,
  targeting: boolean,
  selectingCards: boolean,
  state: AppState
): { eyebrow: string; title: string; detail: string } {
  if (attacking) return { eyebrow: "COMBAT", title: "Choose attackers", detail: selectedCount ? `${selectedCount} selected` : "Select creatures on your battlefield" };
  if (blocking) {
    return state.focusedBlockerId === null
      ? { eyebrow: "COMBAT", title: "Choose blockers", detail: state.blockAssignments.size ? `${state.blockAssignments.size} assigned · select another blocker` : "Select one of your creatures" }
      : { eyebrow: "COMBAT", title: "Choose what it blocks", detail: "Select an attacking creature" };
  }
  if (targeting) return { eyebrow: "TARGET", title: "Choose a target", detail: "Select a highlighted card or player" };
  if (selectingCards) return { eyebrow: "CARDS", title: "Choose cards", detail: `${state.selectedObjects.size} selected · choose a highlighted card` };
  const waiting = nestedType(snapshot.waiting_for) ?? "Priority";
  if (waiting === "Priority") {
    if (state.viewerSeat !== null && snapshot.active_player !== state.viewerSeat) {
      const canRespond = allActions(snapshot).some(action => action.type !== "PassPriority");
      return {
        eyebrow: phaseLabel(snapshot.phase).toUpperCase(),
        title: `${state.playerNames[snapshot.active_player]}'s turn`,
        detail: canRespond ? "Respond or pass priority" : "No response is available · pass priority to continue"
      };
    }
    return { eyebrow: phaseLabel(snapshot.phase).toUpperCase(), title: "You have priority", detail: "Play a card or pass to continue" };
  }
  return { eyebrow: "DECISION", title: splitWords(waiting), detail: waitingDetail(snapshot.waiting_for.data) };
}

export function activeTurnLabel(snapshot: ViewerSnapshot, names: [string, string], viewer: SeatId): string {
  return snapshot.active_player === viewer ? "Your turn" : `${names[snapshot.active_player]}'s turn`;
}

export function unavailableCardMessage(card: CardView, snapshot: ViewerSnapshot): string {
  if (!isLand(card)) return "No action is available for this card right now.";
  if (snapshot.active_player !== card.controller) return "Lands can only be played during your turn.";
  if (snapshot.phase !== "PreCombatMain" && snapshot.phase !== "PostCombatMain") {
    return "Lands can only be played during your main phase.";
  }
  return "This land cannot be played right now.";
}

function priorityText(snapshot: ViewerSnapshot, names: [string, string], viewer: SeatId): string {
  return snapshot.priority_player === viewer ? "Your priority" : `${names[snapshot.priority_player]} has priority`;
}

function passLabel(phase: string): string {
  return phase === "End" ? "End Turn" : "Pass";
}

function snapshotDecisionKey(snapshot: ViewerSnapshot): string {
  return `${snapshot.turn}:${snapshot.phase}:${snapshot.priority_player}:${JSON.stringify(snapshot.waiting_for)}`;
}

function findCard(snapshot: ViewerSnapshot, id: number): CardView | undefined {
  return [...snapshot.battlefield, ...snapshot.exile, ...snapshot.stack.flatMap(entry => entry.source ? [entry.source] : []), ...snapshot.players.flatMap(player => [...player.hand, ...player.graveyard])]
    .find(card => card.object_id === id);
}

function isLand(card: CardView): boolean {
  return card.type_line.includes("Land");
}

function artUrl(card: CardView): string {
  return `https://api.scryfall.com/cards/named?format=image&version=normal&exact=${encodeURIComponent(card.name)}`;
}

function manaCost(cost: { type: string; shards?: string[]; generic?: number }): string {
  if (cost.type === "NoCost") return "";
  const generic = cost.generic ? `{${cost.generic}}` : "";
  return generic + (cost.shards ?? []).map(shard => `{${manaShard(shard)}}`).join("");
}

function manaShard(shard: string): string {
  return shard.replace("Phyrexian", "P/").replace("Two", "2/").replace("Colorless", "C/")
    .replace("White", "W").replace("Blue", "U").replace("Black", "B").replace("Red", "R").replace("Green", "G");
}

function nestedType(value: unknown): string | null {
  return typeof value === "object" && value !== null && "type" in value ? String((value as { type: unknown }).type) : null;
}

function arrayLength(value: unknown): number {
  return Array.isArray(value) ? value.length : 0;
}

function splitWords(text: string): string {
  return text.replace(/([a-z])([A-Z])/g, "$1 $2").replaceAll("_", " ");
}

function shortJson(value: unknown): string {
  if (value === undefined || value === null) return "";
  const text = typeof value === "string" ? value : JSON.stringify(value);
  return text.length > 90 ? `${text.slice(0, 87)}…` : text;
}

function eventSummary(value: unknown): string {
  if (!value || typeof value !== "object") return shortJson(value);
  const data = value as Record<string, unknown>;
  if (typeof data.phase === "string") return phaseLabel(data.phase);
  if (typeof data.object_id === "number" && typeof data.to === "string") return `Card ${data.object_id} → ${data.to}`;
  if (typeof data.player_id === "number") return `Player ${data.player_id + 1}`;
  return shortJson(value);
}

function waitingDetail(value: unknown): string {
  return shortJson(value).replace(/[{}"_]/g, " ").replace(/\s+/g, " ").trim();
}

function phaseLabel(phase: string): string {
  return splitWords(phase);
}

function clockText(ms: number): string {
  const seconds = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

function sameAction(left: GameAction, right: GameAction): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}

function playerUrl(): string {
  const params = new URLSearchParams(location.search);
  return wsUrl("/player", { slot: params.get("slot") ?? "0", token: params.get("token") ?? "" });
}

function wsUrl(path: string, params: Record<string, string> = {}): string {
  const url = new URL(path, location.href);
  url.protocol = location.protocol === "https:" ? "wss:" : "ws:";
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  return url.toString();
}

function escapeHtml(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}
