import { eventToLogLine, type LogNames } from "./log";
import {
  phases,
  phaseLabel,
  type CardModel,
  type PlayerModel,
  type TableModel
} from "./model";
import { type CardId, type LoggedEvent, type SeatId } from "./protocol";
import "./styles.css";

export interface UiState {
  popover: { kind: "hand" | "battlefield"; cardId: CardId } | null;
  pointFrom: CardId | null;
  mulliganBottom: CardId[];
  toast: string | null;
  replay?: ReplayUiState;
}

export interface ReplayUiState {
  playing: boolean;
  speed: 1 | 2 | 4;
  games: number[];
  currentGame: number | null;
}

export type UiCommand =
  | { type: "open_hand"; cardId: CardId }
  | { type: "open_battlefield"; cardId: CardId }
  | { type: "close_popover" }
  | { type: "hand_action"; cardId: CardId; action: "play" | "play_face_down" | "discard" | "reveal" | "library_top" | "library_bottom" }
  | { type: "battlefield_action"; cardId: CardId; action: BattlefieldAction }
  | { type: "counter"; cardId: CardId; delta: number; name: string }
  | { type: "annotation"; cardId: CardId; value: string }
  | { type: "life"; seat: SeatId; delta: number }
  | { type: "library"; action: "draw" | "mill" | "shuffle" }
  | { type: "action_bar"; action: "draw" | "untap_all" | "next_phase" | "next_turn" | "pass" | "concede" }
  | { type: "chat"; text: string }
  | { type: "mulligan_toggle"; cardId: CardId }
  | { type: "mulligan_keep" }
  | { type: "mulligan_again" }
  | { type: "replay"; action: "toggle" | "speed" | "seek"; speed?: 1 | 2 | 4; game?: number };

type HandAction = "play" | "play_face_down" | "discard" | "reveal" | "library_top" | "library_bottom";
type BattlefieldAction = "tap" | "attack" | "graveyard" | "exile" | "hand" | "point_start" | "point_clear" | "point_here";

export function renderTable(
  root: HTMLElement,
  model: TableModel,
  logs: LoggedEvent[],
  ui: UiState,
  onCommand: (command: UiCommand) => void
): void {
  root.innerHTML = [
    `<div class="app-shell mode-${model.mode}">`,
    tableHtml(model, ui),
    sidePaneHtml(model, logs, ui),
    "</div>",
    popoverHtml(model, ui),
    mulliganHtml(model, ui),
    ui.toast ? `<div class="toast" role="status">${escapeHtml(ui.toast)}</div>` : ""
  ].join("");
  bindCommands(root, onCommand);
  scrollLog(root);
}

function tableHtml(model: TableModel, ui: UiState): string {
  if (!model.snapshot || !model.top || !model.bottom) {
    return `
      <main class="table-surface empty">
        <div class="window-banner neutral" data-testid="window-banner">${escapeHtml(model.banner.text)}</div>
        <div class="empty-state">Waiting for table state...</div>
      </main>`;
  }
  const showPlayerControls = model.mode === "player";
  return `
    <main class="table-surface">
      <div class="window-banner ${model.banner.tone}" data-testid="window-banner">${escapeHtml(model.banner.text)}</div>
      ${playerStrip(model.top, model, "top")}
      ${battlefieldHtml(model.top, "top", ui)}
      ${phaseTrackHtml(model)}
      ${battlefieldHtml(model.bottom, "bottom", ui)}
      ${playerStrip(model.bottom, model, "bottom")}
      ${showPlayerControls ? handHtml(model) : ""}
      ${showPlayerControls ? actionBarHtml(model) : replayBarHtml(ui)}
    </main>`;
}

function sidePaneHtml(model: TableModel, logs: LoggedEvent[], ui: UiState): string {
  const names: LogNames = {
    players: model.players ? [model.players[0].name, model.players[1].name] : undefined,
    viewerSlot: model.viewerSlot
  };
  const lines = logs.slice(-220).map((event) => eventToLogLine(event, names));
  return `
    <aside class="log-pane">
      <div class="log-head">
        <div>
          <strong>Log</strong>
          <span>${model.turn === null ? "waiting" : `turn ${model.turn} - ${phaseLabel(model.phase)}`}</span>
        </div>
        ${model.awaitingAck ? `<span class="pill">pending</span>` : ""}
      </div>
      <div class="log-list" data-testid="log-list">
        ${
          lines.length === 0
            ? `<div class="empty-line">No table events yet.</div>`
            : lines.map((line) => `<div class="log-line ${line.kind}"><span>${line.seq}</span>${escapeHtml(line.text)}</div>`).join("")
        }
      </div>
      ${
        model.mode === "player"
          ? `<form class="chat-form" data-chat-form>
              <input name="chat" autocomplete="off" placeholder="Say..." ${model.canAct ? "" : "disabled"} />
              <button type="submit" ${model.canAct ? "" : "disabled"}>Send</button>
            </form>`
          : ui.replay
            ? `<div class="replay-readout">${ui.replay.playing ? "Playing" : "Paused"} ${ui.replay.speed}x</div>`
            : ""
      }
    </aside>`;
}

function playerStrip(player: PlayerModel, model: TableModel, position: "top" | "bottom"): string {
  const own = model.mode === "player" && model.viewerSlot === player.seat;
  const clock = model.clocks[player.seat]?.ms ?? null;
  const isActive = model.active === player.seat;
  return `
    <section class="player-strip ${position} ${isActive ? "active" : ""}">
      <div class="identity">
        <strong>${escapeHtml(own ? "you" : player.name)}</strong>
        <span class="seat">slot ${player.seat}</span>
      </div>
      <div class="life-block">
        ${own ? `<button class="step" data-command="life" data-seat="${player.seat}" data-delta="-1" aria-label="life minus">-</button>` : ""}
        <span class="life">life ${player.life}</span>
        ${own ? `<button class="step" data-command="life" data-seat="${player.seat}" data-delta="1" aria-label="life plus">+</button>` : ""}
      </div>
      <div class="zone-counts">
        <span>hand:${player.handCount}</span>
        <span>lib:${player.libraryCount}</span>
        <span>grave:${player.graveyardCount}</span>
        <span>exile:${player.exileCount}</span>
      </div>
      <div class="clock">clock ${clock === null ? "--:--" : clockText(clock)}</div>
      ${
        own
          ? `<div class="library-tools">
              <button data-command="library" data-action="draw" ${model.canAct ? "" : "disabled"}>Draw 1</button>
              <button data-command="library" data-action="mill" ${model.canAct ? "" : "disabled"}>Mill 1</button>
              <button data-command="library" data-action="shuffle" ${model.canAct ? "" : "disabled"}>Shuffle</button>
            </div>`
          : ""
      }
    </section>`;
}

function battlefieldHtml(player: PlayerModel, position: "top" | "bottom", ui: UiState): string {
  return `
    <section class="battlefield ${position}">
      ${cardRowHtml(player.battlefield.creatures, "creatures", ui)}
      ${cardRowHtml(player.battlefield.lands, "lands", ui)}
    </section>`;
}

function cardRowHtml(cards: CardModel[], label: string, ui: UiState): string {
  return `
    <div class="battle-row ${label}">
      <div class="row-label">${label}</div>
      <div class="row-cards">
        ${cards.length === 0 ? `<div class="empty-line">empty</div>` : cards.map((card) => tableCardHtml(card, "battlefield", ui)).join("")}
      </div>
    </div>`;
}

function phaseTrackHtml(model: TableModel): string {
  return `
    <section class="phase-track">
      <div class="turn-chip">Turn ${model.turn ?? "-"}</div>
      <div class="phase-steps">
        ${phases
          .map(
            (phase) => `
              <div class="phase-step ${model.phase === phase.phase ? "current" : ""}" data-testid="phase-${phase.phase}">
                <span>${phase.short}</span>
                <small>${phase.label}</small>
              </div>`
          )
          .join("")}
      </div>
      <div class="turn-chip">${model.active === null || !model.players ? "waiting" : `${model.players[model.active].name} active`}</div>
    </section>`;
}

function handHtml(model: TableModel): string {
  const cards = model.hand;
  return `
    <section class="hand-zone">
      <div class="hand-label">Hand</div>
      <div class="hand-cards">
        ${
          cards.length === 0
            ? `<div class="empty-line">No cards in hand.</div>`
            : cards.map((card, index) => tableCardHtml(card, "hand", null, index)).join("")
        }
      </div>
    </section>`;
}

function actionBarHtml(model: TableModel): string {
  const disabled = model.canAct ? "" : "disabled";
  return `
    <section class="action-bar">
      <button data-command="action_bar" data-action="draw" ${disabled}>Draw</button>
      <button data-command="action_bar" data-action="untap_all" ${disabled}>Untap all</button>
      <button data-command="action_bar" data-action="next_phase" data-testid="next-phase" ${disabled}>Next phase</button>
      <button data-command="action_bar" data-action="next_turn" ${disabled}>Next turn</button>
      <button data-command="action_bar" data-action="pass" ${disabled}>Pass</button>
      <button class="danger" data-command="action_bar" data-action="concede" ${disabled}>Concede</button>
    </section>`;
}

function replayBarHtml(ui: UiState): string {
  if (!ui.replay) {
    return "";
  }
  return `
    <section class="replay-bar">
      <button data-command="replay" data-action="toggle">${ui.replay.playing ? "Pause" : "Play"}</button>
      <select data-command="replay" data-action="speed" aria-label="speed">
        ${([1, 2, 4] as const).map((speed) => `<option value="${speed}" ${ui.replay?.speed === speed ? "selected" : ""}>${speed}x</option>`).join("")}
      </select>
      <select data-command="replay" data-action="seek" aria-label="game">
        ${ui.replay.games.map((game) => `<option value="${game}" ${ui.replay?.currentGame === game ? "selected" : ""}>Game ${game}</option>`).join("")}
      </select>
    </section>`;
}

function tableCardHtml(card: CardModel, zone: "hand" | "battlefield", ui: UiState | null, index = 0): string {
  const command = zone === "hand" ? "open_hand" : "open_battlefield";
  const selected = ui?.popover?.cardId === card.id ? "selected" : "";
  return `
    <button
      class="text-card ${card.tapped ? "tapped" : ""} ${card.attacking ? "attacking" : ""} ${card.faceDown ? "face-down" : ""} ${selected}"
      style="--fan-index:${index}"
      data-command="${command}"
      data-card-id="${card.id}"
      data-card-kind="${card.kind}"
      data-testid="${zone === "hand" ? "hand-card" : "battlefield-card"}">
      ${cardFrameContentsHtml(card)}
    </button>`;
}

function cardFrameContentsHtml(card: CardModel): string {
  return `
      <div class="card-title">
        <strong>${escapeHtml(card.name)}</strong>
        <span>${manaHtml(card.manaCost)}</span>
      </div>
      <div class="type-line">${escapeHtml(card.typeLine)}</div>
      <div class="oracle">${escapeHtml(card.oracleText)}</div>
      <div class="card-foot">
        <span>${escapeHtml(counterText(card.counters))}</span>
        <span>${escapeHtml(card.powerToughness ?? "")}</span>
      </div>
      ${card.annotation ? `<div class="annotation">${escapeHtml(card.annotation)}</div>` : ""}`;
}

function popoverHtml(model: TableModel, ui: UiState): string {
  if (!ui.popover || !model.snapshot) {
    return "";
  }
  const card = findCard(model, ui.popover.cardId);
  if (!card) {
    return "";
  }
  const canAct = model.canAct;
  if (ui.popover.kind === "hand") {
    return `
      <div class="popover" role="dialog">
        <div class="popover-title">${escapeHtml(card.name)}</div>
        <button data-command="hand_action" data-action="play" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Play to battlefield</button>
        <button data-command="hand_action" data-action="play_face_down" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Play face down</button>
        <button data-command="hand_action" data-action="discard" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Discard</button>
        <button data-command="hand_action" data-action="reveal" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Reveal</button>
        <button data-command="hand_action" data-action="library_top" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>To library top</button>
        <button data-command="hand_action" data-action="library_bottom" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>To library bottom</button>
        <button class="ghost" data-command="close_popover">Close</button>
      </div>`;
  }
  const own = model.viewerSlot !== null && card.view?.controller === model.viewerSlot;
  const attackingPhase = model.phase === "declare_attackers";
  return `
    <div class="popover" role="dialog">
      <div class="popover-title">${escapeHtml(card.name)}</div>
      ${
        own
          ? `
            <button data-command="battlefield_action" data-action="tap" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>${card.tapped ? "Untap" : "Tap"}</button>
            <button data-command="battlefield_action" data-action="attack" data-card-id="${card.id}" ${canAct && attackingPhase ? "" : "disabled"}>${card.attacking ? "Attack off" : "Attack on"}</button>
            <div class="counter-tools">
              <input data-counter-name value="+1/+1" aria-label="counter name" />
              <button data-command="counter" data-delta="1" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Add</button>
              <button data-command="counter" data-delta="-1" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Remove</button>
            </div>
            <button data-command="battlefield_action" data-action="graveyard" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>To graveyard</button>
            <button data-command="battlefield_action" data-action="exile" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>To exile</button>
            <button data-command="battlefield_action" data-action="hand" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>To hand</button>
            <button data-command="battlefield_action" data-action="point_start" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Point at...</button>
            <button data-command="battlefield_action" data-action="point_clear" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Clear pointer</button>
            <div class="annotation-tools">
              <input data-annotation value="${escapeAttr(card.annotation ?? "")}" aria-label="annotation" />
              <button data-command="annotation" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Save</button>
            </div>`
          : `<button data-command="battlefield_action" data-action="point_start" data-card-id="${card.id}" disabled>Point at...</button>`
      }
      ${
        ui.pointFrom !== null && ui.pointFrom !== card.id
          ? `<button data-command="battlefield_action" data-action="point_here" data-card-id="${card.id}" ${canAct ? "" : "disabled"}>Point here</button>`
          : ""
      }
      <button class="ghost" data-command="close_popover">Close</button>
    </div>`;
}

function mulliganHtml(model: TableModel, ui: UiState): string {
  const expectation = model.expectation;
  if (model.mode !== "player" || !model.snapshot || expectation?.type !== "mulligan" || model.viewerSlot !== expectation.seat) {
    return "";
  }
  const selected = new Set(ui.mulliganBottom);
  const required = expectation.must_bottom;
  const keepDisabled = model.canAct && selected.size === required ? "" : "disabled";
  return `
    <div class="modal-backdrop" data-testid="mulligan-modal">
      <div class="mulligan-modal" role="dialog" aria-modal="true">
        <div class="modal-head">
          <strong>Mulligan</strong>
          <span>Keep ${expectation.keeping_hand_of}${required > 0 ? ` - bottom ${required}` : ""}</span>
        </div>
        <div class="mulligan-hand">
          ${model.hand
            .map(
              (card) => `
              <button
                class="text-card mulligan-card ${selected.has(card.id) ? "chosen" : ""}"
                data-command="mulligan_toggle"
                data-card-id="${card.id}"
                data-card-kind="${card.kind}"
                data-testid="mulligan-card">
                ${cardFrameContentsHtml(card)}
                ${selected.has(card.id) ? `<em class="mulligan-order">${ui.mulliganBottom.indexOf(card.id) + 1}</em>` : ""}
              </button>`
            )
            .join("")}
        </div>
        <div class="modal-actions">
          <button data-command="mulligan_again" ${model.canAct ? "" : "disabled"}>Mulligan</button>
          <button data-command="mulligan_keep" data-testid="keep-button" ${keepDisabled}>Keep</button>
        </div>
      </div>
    </div>`;
}

function bindCommands(root: HTMLElement, onCommand: (command: UiCommand) => void): void {
  root.querySelectorAll<HTMLElement>("[data-command]").forEach((element) => {
    const command = element.dataset.command;
    if (element instanceof HTMLSelectElement) {
      element.addEventListener("change", () => {
        if (command === "replay" && element.dataset.action === "speed") {
          onCommand({ type: "replay", action: "speed", speed: Number(element.value) as 1 | 2 | 4 });
        } else if (command === "replay" && element.dataset.action === "seek") {
          onCommand({ type: "replay", action: "seek", game: Number(element.value) });
        }
      });
      return;
    }
    element.addEventListener("click", () => {
      const cardId = Number(element.dataset.cardId);
      const action = element.dataset.action ?? "";
      switch (command) {
        case "open_hand":
          onCommand({ type: "open_hand", cardId });
          break;
        case "open_battlefield":
          onCommand({ type: "open_battlefield", cardId });
          break;
        case "close_popover":
          onCommand({ type: "close_popover" });
          break;
        case "hand_action":
          onCommand({ type: "hand_action", cardId, action: action as HandAction });
          break;
        case "battlefield_action":
          onCommand({ type: "battlefield_action", cardId, action: action as BattlefieldAction });
          break;
        case "counter": {
          const input = root.querySelector<HTMLInputElement>("[data-counter-name]");
          onCommand({ type: "counter", cardId, delta: Number(element.dataset.delta), name: input?.value.trim() || "+1/+1" });
          break;
        }
        case "annotation": {
          const input = root.querySelector<HTMLInputElement>("[data-annotation]");
          onCommand({ type: "annotation", cardId, value: input?.value ?? "" });
          break;
        }
        case "life":
          onCommand({ type: "life", seat: Number(element.dataset.seat) as SeatId, delta: Number(element.dataset.delta) });
          break;
        case "library":
          onCommand({ type: "library", action: action as "draw" | "mill" | "shuffle" });
          break;
        case "action_bar":
          onCommand({ type: "action_bar", action: action as "draw" | "untap_all" | "next_phase" | "next_turn" | "pass" | "concede" });
          break;
        case "mulligan_toggle":
          onCommand({ type: "mulligan_toggle", cardId });
          break;
        case "mulligan_keep":
          onCommand({ type: "mulligan_keep" });
          break;
        case "mulligan_again":
          onCommand({ type: "mulligan_again" });
          break;
        case "replay":
          onCommand({ type: "replay", action: "toggle" });
          break;
      }
    });
  });
  root.querySelector<HTMLFormElement>("[data-chat-form]")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = new FormData(event.currentTarget).get("chat");
    const text = typeof input === "string" ? input.trim() : "";
    if (text) {
      onCommand({ type: "chat", text });
    }
  });
}

function findCard(model: TableModel, id: CardId): CardModel | null {
  const zones = [model.hand];
  if (model.players) {
    for (const player of model.players) {
      zones.push(player.battlefield.lands, player.battlefield.creatures);
    }
  }
  return zones.flat().find((card) => card.id === id) ?? null;
}

function scrollLog(root: HTMLElement): void {
  const list = root.querySelector<HTMLElement>(".log-list");
  if (list) {
    list.scrollTop = list.scrollHeight;
  }
}

function manaHtml(cost: string | null): string {
  if (!cost) {
    return "";
  }
  const symbols = [...cost.matchAll(/\{([^}]+)\}/g)].map((match) => match[1]);
  return symbols.map((symbol) => `<span class="mana">${escapeHtml(symbol)}</span>`).join("");
}

function counterText(counters: Record<string, number>): string {
  return Object.entries(counters)
    .filter(([, value]) => value !== 0)
    .map(([name, value]) => `${name} ${value > 0 ? "+" : ""}${value}`)
    .join(" ");
}

function clockText(ms: number): string {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function escapeAttr(value: string): string {
  return escapeHtml(value).replaceAll("'", "&#39;");
}
