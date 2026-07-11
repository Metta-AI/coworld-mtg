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
}

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
    message: "Connecting to Phase..."
  };
}

function connect(state: AppState, url: string): void {
  const socket = new WebSocket(url);
  state.socket = socket;
  socket.addEventListener("open", () => {
    state.message = "Connected";
    render(state);
  });
  socket.addEventListener("message", (message) => {
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
      const snapshot = frame.state ?? frame.step?.state;
      const events = frame.events ?? frame.step?.events ?? [];
      if (snapshot) state.snapshot = snapshot;
      // Live state is broadcast only after the server accepts and applies an
      // action. It intentionally arrives before the corresponding ack, so it
      // is sufficient proof that the pending command no longer needs to lock
      // the newly rendered legal actions.
      if (frame.state) state.pendingCmdId = null;
      state.events.push(...events);
      if (frame.step?.action) {
        state.events.push({ type: "Action", data: frame.step.action });
      }
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
        ? `Draw: ${frame.outcome.reason}`
        : `Slot ${frame.outcome.winner_slot + 1} wins: ${frame.outcome.reason}`;
      break;
    case "match_end":
      state.message = `Match ended ${frame.scores[0]}–${frame.scores[1]}`;
      break;
    case "replay_meta":
      state.playerNames = [frame.config.players[0]?.name ?? "Player 1", frame.config.players[1]?.name ?? "Player 2"];
      state.message = `Replay: ${frame.games.length} game(s)`;
      break;
  }
  render(state);
}

function render(state: AppState): void {
  const snapshot = state.snapshot;
  if (!snapshot) {
    state.root.innerHTML = `<main class="loading"><h1>Cogatrice</h1><p>${escapeHtml(state.message)}</p></main>`;
    return;
  }
  const bottom = state.viewerSeat ?? 0;
  const top = bottom === 0 ? 1 : 0;
  const actions = allActions(snapshot);
  state.root.innerHTML = `
    <div class="app-shell">
      <header>
        <div><h1>Cogatrice</h1><span>Phase rules engine</span></div>
        <strong>Turn ${snapshot.turn} · ${phaseLabel(snapshot.phase)} · ${escapeHtml(state.playerNames[snapshot.priority_player])} has priority</strong>
        <span>${escapeHtml(state.message)}</span>
      </header>
      <main class="game-table">
        ${playerHtml(snapshot, top, state.playerNames[top], state.clocks[top], false)}
        ${zoneHtml("Opponent battlefield", snapshot.battlefield.filter(card => card.controller === top), snapshot)}
        ${stackHtml(snapshot)}
        ${zoneHtml("Your battlefield", snapshot.battlefield.filter(card => card.controller === bottom), snapshot)}
        ${playerHtml(snapshot, bottom, state.playerNames[bottom], state.clocks[bottom], state.mode === "player")}
        ${state.mode === "player" ? zoneHtml("Your hand", snapshot.players[bottom].hand, snapshot) : ""}
      </main>
      <aside>
        <section class="prompt">
          <h2>Pending decision</h2>
          <p>${escapeHtml(promptLabel(snapshot.waiting_for))}</p>
        </section>
        ${state.mode === "player" ? actionPanel(actions, snapshot, state.pendingCmdId !== null) : ""}
        <section class="event-log"><h2>Phase events</h2>${state.events.slice(-80).reverse().map(eventHtml).join("")}</section>
      </aside>
    </div>`;
  state.root.querySelectorAll<HTMLButtonElement>("[data-action-index]").forEach(button => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.actionIndex);
      const action = actions[index];
      if (action) sendAction(state, action);
    });
  });
  state.root.querySelector<HTMLButtonElement>("[data-concede]")?.addEventListener("click", () => {
    if (state.viewerSeat !== null) {
      sendAction(state, { type: "Concede", data: { player_id: state.viewerSeat } });
    }
  });
}

export function allActions(snapshot: ViewerSnapshot): GameAction[] {
  const seen = new Set<string>();
  const output: GameAction[] = [];
  for (const action of [
    ...snapshot.legal_actions,
    ...Object.values(snapshot.legal_actions_by_object).flat()
  ]) {
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
  state.socket.send(JSON.stringify({ cmd_id: cmdId, action }));
  render(state);
}

function playerHtml(
  snapshot: ViewerSnapshot,
  seat: SeatId,
  name: string,
  clock: number | null,
  own: boolean
): string {
  const player = snapshot.players[seat];
  const mana = Array.isArray(player.mana_pool.mana)
    ? player.mana_pool.mana.map(unit => unit.color).join(" ")
    : "";
  return `<section class="player ${snapshot.active_player === seat ? "active" : ""}">
    <div><strong>${escapeHtml(own ? `${name} (you)` : name)}</strong><span>seat ${seat + 1}</span></div>
    <b>${player.life} life</b>
    <span>${player.poison} poison · ${player.energy} energy</span>
    <span>hand ${player.hand.length} · library ${player.library_count} · graveyard ${player.graveyard.length}</span>
    <span>mana ${escapeHtml(mana || "empty")}</span>
    <span>${clock === null ? "" : clockText(clock)}</span>
  </section>`;
}

function zoneHtml(label: string, cards: CardView[], snapshot: ViewerSnapshot): string {
  return `<section class="zone"><h2>${escapeHtml(label)}</h2><div class="cards">${
    cards.length ? cards.map(card => cardHtml(card, snapshot)).join("") : `<span class="empty">Empty</span>`
  }</div></section>`;
}

function cardHtml(card: CardView, snapshot: ViewerSnapshot): string {
  const effective = snapshot.spell_costs[String(card.object_id)] ?? card.mana_cost;
  const pt = card.power === null ? "" : `<b>${card.power}/${card.toughness ?? 0}</b>`;
  const image = card.face_down || card.name === "Hidden Card"
    ? ""
    : `<img loading="lazy" src="https://api.scryfall.com/cards/named?format=image&version=normal&exact=${encodeURIComponent(card.name)}" alt="" />`;
  return `<article class="card ${card.tapped ? "tapped" : ""} ${card.attacking ? "attacking" : ""}">
    ${image}<div class="card-copy"><strong>${escapeHtml(card.face_down ? "Hidden card" : card.name)}</strong>
    <span>${escapeHtml(card.type_line)}</span><span>${escapeHtml(manaCost(effective))}</span>
    <p>${escapeHtml(card.oracle_text)}</p>${pt}</div>
  </article>`;
}

function stackHtml(snapshot: ViewerSnapshot): string {
  return `<section class="stack"><h2>Stack</h2>${snapshot.stack.length
    ? snapshot.stack.slice().reverse().map(entry => `<div>${escapeHtml(entry.source?.name ?? `Ability ${entry.id}`)} · ${escapeHtml(JSON.stringify(entry.kind))}</div>`).join("")
    : `<span class="empty">Empty</span>`}</section>`;
}

function actionPanel(actions: GameAction[], snapshot: ViewerSnapshot, disabled: boolean): string {
  return `<section class="actions"><h2>Legal actions</h2><div>${actions.map((action, index) =>
    `<button data-action-index="${index}" ${disabled ? "disabled" : ""}>${escapeHtml(actionLabel(action, snapshot))}</button>`
  ).join("")}</div><button class="concede" data-concede ${disabled ? "disabled" : ""}>Concede</button></section>`;
}

export function actionLabel(action: GameAction, snapshot: ViewerSnapshot): string {
  const data = action.data ?? {};
  const sourceId = Number(data.object_id ?? data.source_id ?? -1);
  const source = findCard(snapshot, sourceId);
  switch (action.type) {
    case "PassPriority": return "Pass priority";
    case "PlayLand": return `Play ${source?.name ?? "land"}`;
    case "CastSpell": return `Cast ${source?.name ?? "spell"}`;
    case "ActivateAbility": return `Activate ${source?.name ?? "ability"}`;
    case "MulliganDecision": return `Mulligan: ${nestedType(data.choice) ?? "decide"}`;
    case "DeclareAttackers": return `Attack with ${arrayLength(data.attacks)} creature(s)`;
    case "DeclareBlockers": return `Block with ${arrayLength(data.assignments)} creature(s)`;
    case "SelectCards": return `Select ${arrayLength(data.cards)} card(s)`;
    case "ChooseTarget": return `Choose target ${shortJson(data.target)}`;
    case "Concede": return "Concede";
    default: return `${splitWords(action.type)} ${shortJson(data)}`.trim();
  }
}

function findCard(snapshot: ViewerSnapshot, id: number): CardView | undefined {
  return [...snapshot.battlefield, ...snapshot.exile, ...snapshot.players.flatMap(player => [...player.hand, ...player.graveyard])]
    .find(card => card.object_id === id);
}

function eventHtml(event: unknown): string {
  const value = event as { type?: string; data?: unknown };
  return `<div><b>${escapeHtml(splitWords(value.type ?? "Event"))}</b><span>${escapeHtml(shortJson(value.data))}</span></div>`;
}

function promptLabel(waiting: ViewerSnapshot["waiting_for"]): string {
  return `${splitWords(waiting.type ?? "Waiting")} ${shortJson(waiting.data)}`.trim();
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
  return text.replace(/([a-z])([A-Z])/g, "$1 $2");
}

function shortJson(value: unknown): string {
  if (value === undefined || value === null) return "";
  const text = typeof value === "string" ? value : JSON.stringify(value);
  return text.length > 140 ? `${text.slice(0, 137)}…` : text;
}

function phaseLabel(phase: string): string {
  return splitWords(phase);
}

function clockText(ms: number): string {
  const seconds = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
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
