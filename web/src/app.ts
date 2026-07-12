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
}

type StateFrame = Extract<ServerFrame, { type: "state" }>;

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
    replayTimer: null
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
      if (frame.state) state.pendingCmdId = null;
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
}

function render(state: AppState): void {
  const snapshot = state.snapshot;
  if (!snapshot) {
    state.root.innerHTML = `<main class="loading"><div class="brand-mark">C</div><h1>Cogatrice</h1><p>${escapeHtml(state.message)}</p></main>`;
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
          <span>TURN ${snapshot.turn}</span>
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
          ${pileHtml("Graveyard", snapshot.players[top].graveyard.length, "graveyard", top, true)}
          ${pileHtml("Exile", exileForSeat(snapshot, top).length, "exile", top, true)}
        </section>

        ${battlefieldHtml(snapshot, top, "Opponent battlefield", combatSelected, interactiveCombatObjects, state)}

        <section class="table-center">
          ${stackHtml(snapshot, targetObjectIds)}
          ${phaseRail(snapshot.phase)}
          <div class="priority-orb ${snapshot.priority_player === bottom ? "yours" : "theirs"}" title="Priority"></div>
        </section>

        ${battlefieldHtml(snapshot, bottom, "Your battlefield", combatSelected, interactiveCombatObjects, state)}

        <section class="player-end your-end" aria-label="You">
          ${playerBadge(snapshot, bottom, state.playerNames[bottom], state.clocks[bottom], state.mode === "player", targetPlayerIds.has(bottom))}
          ${pileHtml("Library", snapshot.players[bottom].library_count, "library", bottom)}
          ${pileHtml("Graveyard", snapshot.players[bottom].graveyard.length, "graveyard", bottom, true)}
          ${pileHtml("Exile", exileForSeat(snapshot, bottom).length, "exile", bottom, true)}
        </section>

        ${state.mode === "player" ? handHtml(snapshot, bottom, state, interactiveCombatObjects) : ""}
      </main>

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
        state.focusedObjectId = state.focusedObjectId === objectId ? null : objectId;
        state.openZone = null;
      }
      render(state);
    });
    element.addEventListener("mouseenter", () => showPreview(state.root, findCard(snapshot, objectId)));
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
      }
    });
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
  const classes = [
    "game-card",
    card.tapped ? "tapped" : "",
    card.attacking ? "attacking" : "",
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
    ${counterHtml(card.counters)}${card.tapped ? `<span class="status-chip">TAPPED</span>` : ""}${card.attacking ? `<span class="status-chip attack-chip">ATTACKING</span>` : ""}
  </article>`;
}

function focusPanel(card: CardView, actions: GameAction[], snapshot: ViewerSnapshot, disabled: boolean): string {
  return `<section class="focus-panel" aria-label="Card actions">
    <button class="close" data-close-focus aria-label="Close card actions">×</button>
    <div class="focus-card">${cardDetailHtml(card, snapshot)}</div>
    <div class="focus-actions"><span>AVAILABLE ACTIONS</span>${actions.length
      ? actions.map(action => `<button data-action-index="${allActions(snapshot).findIndex(candidate => sameAction(candidate, action))}" ${disabled ? "disabled" : ""}>${escapeHtml(actionLabel(action, snapshot))}</button>`).join("")
      : `<p>No action is available for this card right now.</p>`}</div>
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
  const matchingAttack = matchingAttackAction(actions, state.selectedObjects);
  const matchingBlocks = matchingBlockAction(actions, state.blockAssignments);
  const matchingCards = matchingSelectCardsAction(actions, state.selectedObjects);
  const pass = actions.find(action => action.type === "PassPriority");
  const globals = actions.filter(action => ![
    "PassPriority", "PlayLand", "CastSpell", "ActivateAbility", "MulliganDecision", "DeclareAttackers", "DeclareBlockers", "SelectCards"
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
    <div class="decision-copy"><span>${escapeHtml(prompt.eyebrow)}</span><strong>${escapeHtml(prompt.title)}</strong><small>${escapeHtml(prompt.detail)}</small></div>
    <div class="decision-actions">
      ${attackActions.length ? `<button class="secondary-action" data-clear-selection ${disabled ? "disabled" : ""}>Reset</button><button class="primary-action combat-action" data-confirm-attack ${!matchingAttack || disabled ? "disabled" : ""}>${state.selectedObjects.size ? `Attack (${state.selectedObjects.size})` : "No attacks"}</button>` : ""}
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

function stackHtml(snapshot: ViewerSnapshot, targetObjectIds: Set<number>): string {
  if (!snapshot.stack.length) return `<div class="stack-zone empty-stack"><span>STACK</span></div>`;
  return `<section class="stack-zone"><span>STACK</span><div>${snapshot.stack.slice().reverse().map(entry => {
    const objectId = entry.source?.object_id ?? entry.source_id;
    const targetable = targetObjectIds.has(objectId);
    return `<article class="${targetable ? "targetable" : ""}" data-object-id="${objectId}" tabindex="0"><strong>${escapeHtml(entry.source?.name ?? `Ability ${entry.id}`)}</strong><small>${escapeHtml(splitWords(nestedType(entry.kind) ?? "On the stack"))}</small></article>`;
  }).join("")}</div></section>`;
}

function phaseRail(current: string): string {
  let matchedCurrent = false;
  return `<nav class="phase-rail" aria-label="Turn phases">${PHASES.map(([phase, label]) => {
    const active = phase === current && (!matchedCurrent || phase !== "PostCombatMain");
    if (active) matchedCurrent = true;
    return `<span class="${active ? "current" : ""}" title="${label}">${label.slice(0, 1)}</span>`;
  }).join("")}</nav>`;
}

function pileHtml(label: string, count: number, kind: string, seat: SeatId, browseable = false): string {
  const attributes = browseable
    ? `data-zone-open="${kind}" data-seat="${seat}" aria-label="View ${label}: ${count} cards"`
    : `disabled aria-label="${label}: ${count} cards"`;
  return `<button class="card-pile ${kind} ${browseable ? "browseable" : ""}" title="${label}: ${count}" ${attributes}><span>${count}</span><small>${label}</small></button>`;
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
  const attacks = action.data?.attacks;
  if (!Array.isArray(attacks)) return [];
  return attacks.map(entry => Array.isArray(entry) ? Number(entry[0]) : Number((entry as { object_id?: unknown }).object_id)).filter(Number.isFinite);
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
  const wanted = [...selected].sort((a, b) => a - b).join(",");
  return actions.find(action => action.type === "DeclareAttackers" && attackObjectIds(action).sort((a, b) => a - b).join(",") === wanted);
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
  if (waiting === "Priority") return { eyebrow: phaseLabel(snapshot.phase).toUpperCase(), title: "You have priority", detail: "Play a card or pass to continue" };
  return { eyebrow: "DECISION", title: splitWords(waiting), detail: waitingDetail(snapshot.waiting_for.data) };
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
