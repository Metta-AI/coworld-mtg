import type { BracketDeckRequest, BracketEstimate } from "../types/bracketEstimate";
import type {
  EngineAdapter,
  EngineSnapshot,
  GameAction,
  GameEvent,
  GameLogEntry,
  GameState,
  LegalActionsResult,
  ManaCost,
  PlayerId,
  SubmitResult,
} from "../adapter/types";
import { AdapterError, nextSnapshotSeq } from "../adapter/types";

export const PROTOCOL_VERSION = 1;
export const MIN_SUPPORTED_SERVER_PROTOCOL = 1;
export const LOBBY_MIN_SUPPORTED_SERVER_PROTOCOL = 1;

export interface DeckData {
  main_deck: string[];
  sideboard: string[];
}

export interface ServerInfo {
  version: string;
  buildCommit: string;
  protocolVersion: number;
  mode: "Full" | "LobbyOnly";
  publicUrl?: string;
}

export type WsAdapterEvent =
  | { type: "serverHello"; info: ServerInfo; compatible: boolean }
  | {
      type: "playerIdentity";
      playerId: PlayerId;
      opponentName: string | null;
      playerNames?: Record<number, string>;
    }
  | { type: "actionPendingChanged"; pending: boolean }
  | { type: "latencyChanged"; latencyMs: number | null }
  | { type: "sessionChanged"; session: null }
  | { type: "gameCreated"; gameCode: string }
  | { type: "passwordRequired"; gameCode: string }
  | { type: "waitingForOpponent" }
  | { type: "opponentJoined"; opponentName?: string }
  | { type: "opponentDisconnected"; graceSeconds: number }
  | { type: "opponentReconnected" }
  | { type: "playerDisconnected"; playerId: PlayerId; graceSeconds: number }
  | { type: "playerReconnected"; playerId: PlayerId }
  | { type: "gamePaused"; disconnectedPlayer: PlayerId; timeoutSeconds: number }
  | { type: "gameResumed" }
  | { type: "playerEliminated"; playerId: PlayerId; becameSpectator: boolean }
  | { type: "spectatorJoined"; name: string }
  | { type: "gameOver"; winner: PlayerId | null; reason: string }
  | { type: "error"; message: string }
  | { type: "deckRejected"; reason: string }
  | { type: "reconnecting"; attempt: number; maxAttempts: number }
  | { type: "reconnected" }
  | { type: "reconnectFailed" }
  | {
      type: "stateChanged";
      snapshot: EngineSnapshot;
      events: GameEvent[];
      logEntries?: GameLogEntry[];
    }
  | { type: "emoteReceived"; fromPlayer: PlayerId; emote: string }
  | { type: "conceded"; player: PlayerId }
  | { type: "timerUpdate"; player: PlayerId; remainingSeconds: number }
  | { type: "takebackRequested"; requester: PlayerId; requesterName: string }
  | { type: "takebackResolved"; approved: boolean; resolvedBy: PlayerId | null };

type Listener = (event: WsAdapterEvent) => void;

interface PhaseClientPayload {
  state: GameState;
  derived?: GameState["derived"];
  legal_actions: GameAction[];
  auto_pass_recommended: boolean;
  spell_costs: Record<string, ManaCost>;
  legal_actions_by_object: Record<string, GameAction[]>;
}

interface StateFrame {
  type: "state";
  game_number?: number;
  state?: {
    phase_client?: PhaseClientPayload;
  };
  events?: GameEvent[];
  clocks_ms?: [number, number];
  step?: {
    state?: { phase_client?: PhaseClientPayload };
    events?: GameEvent[];
    wall_ms?: number;
    actor_slot?: number | null;
    action?: GameAction | null;
  };
}

interface ReplayMetaFrame {
  type: "replay_meta";
  games?: Array<{ game_number: number; steps: number }>;
}

interface ReplayFrameData {
  snapshot: EngineSnapshot;
  events: GameEvent[];
  gameNumber: number;
  wallMs: number | null;
  actorSlot: number | null;
  action: GameAction | null;
}

interface ReplayGameSegment {
  gameNumber: number;
  startIndex: number;
  stepCount: number;
}

export interface CoworldReplayState {
  index: number;
  count: number;
  playing: boolean;
  complete: boolean;
  rate: number;
  gameIndex: number;
  gameCount: number;
  gameNumber: number;
  gameStepIndex: number;
  gameStepCount: number;
  turnIndex: number;
  turnCount: number;
  turnNumber: number;
  actionLabel: string;
}

export interface CoworldReplayController {
  play: () => void;
  pause: () => void;
  seek: (index: number) => void;
  step: (offset: number) => void;
  seekTurn: (index: number) => void;
  stepTurn: (offset: number) => void;
  seekGame: (index: number) => void;
  stepGame: (offset: number) => void;
  setRate: (rate: number) => void;
}

interface HelloFrame {
  type: "hello";
  slot?: number;
  seat?: PlayerId;
  player_names: [string, string];
  match?: {
    games_to_win: number;
    game_number: number;
    wins: [number, number];
  };
}

interface PendingCommand {
  id: number;
  events: GameEvent[];
  resolve: (result: SubmitResult) => void;
  reject: (error: Error) => void;
}

/**
 * Phase `EngineAdapter` backed by Coworld MTG's assigned socket.
 *
 * This class deliberately knows nothing about deck registration, lobbies,
 * matchmaking, or rules. It maps one atomic, already-filtered Coworld payload
 * into Phase's store shape and sends exact Phase actions back in `cmd_id`
 * envelopes.
 */
export class WebSocketAdapter implements EngineAdapter {
  private socket: WebSocket | null = null;
  private snapshot: EngineSnapshot | null = null;
  private listeners: Listener[] = [];
  private initResolve: (() => void) | null = null;
  private initReject: ((error: Error) => void) | null = null;
  private initialEvents: GameEvent[] = [];
  private pending: PendingCommand | null = null;
  private nextCommandId = 1;
  private disposed = false;
  private _playerId: PlayerId | null = null;
  private playerSlot: number | null = null;
  private replayFrames: ReplayFrameData[] = [];
  private replayGames: ReplayGameSegment[] = [];
  private replayIndex = 0;
  private replayComplete = false;
  private replayPlaying = false;
  private replayRate = 1;
  private replayTimer: number | null = null;
  private replayKeyHandler: ((event: KeyboardEvent) => void) | null = null;

  constructor(
    _serverUrl: string,
    private readonly mode: "host" | "join" | "spectate",
    _deckData: DeckData,
    _joinGameCode?: string,
    _joinPassword?: string,
    _reservationToken?: string,
    _displayName = "Player",
  ) {
    this.publishStatus({ connection: "connecting" });
    if (this.isReplay()) this.installReplayController();
  }

  get gameCode(): string | null {
    return "coworld";
  }

  get playerId(): PlayerId | null {
    return this._playerId;
  }

  getServerInfo(): ServerInfo {
    return {
      version: __APP_VERSION__,
      buildCommit: __BUILD_HASH__,
      protocolVersion: PROTOCOL_VERSION,
      mode: "Full",
    };
  }

  onEvent(listener: Listener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((candidate) => candidate !== listener);
    };
  }

  async initialize(): Promise<void> {
    if (this.disposed) {
      throw new AdapterError("WS_CLOSED", "Coworld adapter is disposed", false);
    }
    if (this.socket) return;

    return new Promise<void>((resolve, reject) => {
      this.initResolve = resolve;
      this.initReject = reject;
      const socket = new WebSocket(this.coworldSocketUrl());
      this.socket = socket;
      socket.onopen = () => {
        this.publishStatus({ connection: "connected" });
        this.emit({
          type: "serverHello",
          info: this.getServerInfo(),
          compatible: true,
        });
      };
      socket.onmessage = (event) => this.handleFrame(JSON.parse(String(event.data)) as unknown);
      socket.onerror = () => this.failInitialization("Coworld WebSocket connection failed");
      socket.onclose = () => {
        this.publishStatus({ connection: "disconnected" });
        this.socket = null;
        if (!this.disposed) {
          this.failInitialization("Coworld WebSocket closed before game start");
          this.emit({ type: "error", message: "Coworld connection closed" });
        }
        if (this.pending) {
          this.pending.reject(new AdapterError("WS_CLOSED", "Connection closed during action", true));
          this.pending = null;
          this.emit({ type: "actionPendingChanged", pending: false });
        }
      };
    });
  }

  async initializeGame(): Promise<SubmitResult> {
    const events = this.initialEvents;
    this.initialEvents = [];
    return { events };
  }

  submitAction(action: GameAction, actor: PlayerId): Promise<SubmitResult> {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(new AdapterError("WS_CLOSED", "Coworld connection is not open", true));
    }
    if (this.mode === "spectate") {
      return Promise.reject(new AdapterError("READ_ONLY", "Spectators cannot submit actions", false));
    }
    if (this._playerId === null || actor !== this._playerId) {
      return Promise.reject(new AdapterError("STALE_ACTION", "Action actor is not this Coworld seat", false));
    }
    if (this.pending) {
      return Promise.reject(new AdapterError("ACTION_PENDING", "Another action is awaiting acknowledgement", true));
    }

    const id = this.nextCommandId++;
    this.emit({ type: "actionPendingChanged", pending: true });
    return new Promise<SubmitResult>((resolve, reject) => {
      this.pending = { id, events: [], resolve, reject };
      this.socket?.send(JSON.stringify({ cmd_id: id, action }));
    });
  }

  async getState(): Promise<GameState> {
    return this.requireSnapshot().state;
  }

  async getLegalActions(): Promise<LegalActionsResult> {
    return this.requireSnapshot().legalResult;
  }

  async getSnapshot(): Promise<EngineSnapshot> {
    return this.requireSnapshot();
  }

  getAiAction(): Promise<GameAction | null> {
    return Promise.resolve(null);
  }

  restoreState(): never {
    throw new AdapterError("READ_ONLY", "Coworld owns authoritative restore", false);
  }

  dispose(): void {
    this.disposed = true;
    this.socket?.close();
    this.socket = null;
    this.listeners = [];
    this.snapshot = null;
    if (this.replayTimer !== null) window.clearTimeout(this.replayTimer);
    if (this.replayKeyHandler) window.removeEventListener("keydown", this.replayKeyHandler, true);
  }

  estimateBracket(_deck: BracketDeckRequest): Promise<BracketEstimate | null> {
    return Promise.resolve(null);
  }

  tryReconnect(): void {
    this.emit({ type: "reconnectFailed" });
  }

  sendConcede(): void {
    if (this._playerId === null || !this.snapshot) return;
    const action = this.snapshot.legalResult.actions.find(
      (candidate) =>
        candidate.type === "Concede" && candidate.data.player_id === this._playerId,
    );
    if (!action) {
      this.emit({ type: "error", message: "Coworld server omitted the legal concession action" });
      return;
    }
    void this.submitAction(action, this._playerId).catch(() => {});
  }

  sendEmote(_emote: string): void {}
  sendRequestTakeback(): void {}
  sendRespondTakeback(_approve: boolean): void {}
  sendCancelTakeback(): void {}

  private coworldSocketUrl(): string {
    const scheme = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = new URL(`${scheme}//${window.location.host}`);
    const page = new URL(window.location.href);
    const clientPathIndex = page.pathname.lastIndexOf("/client/");
    const proxyPrefix = clientPathIndex < 0 ? "" : page.pathname.slice(0, clientPathIndex);
    if (document.body.dataset.coworldRole === "replay") {
      url.pathname = `${proxyPrefix}/replay`;
    } else if (this.mode === "spectate") {
      url.pathname = `${proxyPrefix}/global`;
    } else {
      url.pathname = `${proxyPrefix}/player`;
      for (const key of ["slot", "token"]) {
        const value = page.searchParams.get(key);
        if (value !== null) url.searchParams.set(key, value);
      }
    }
    url.searchParams.set("client", "phase");
    return url.toString();
  }

  private handleFrame(raw: unknown): void {
    if (raw === null || typeof raw !== "object" || !("type" in raw)) return;
    const frame = raw as { type: string; [key: string]: unknown };
    switch (frame.type) {
      case "replay_meta":
        this.handleReplayMeta(frame as unknown as ReplayMetaFrame);
        break;
      case "hello":
        this.handleHello(frame as unknown as HelloFrame);
        break;
      case "state":
        this.handleState(frame as unknown as StateFrame);
        break;
      case "ack":
        this.handleAck(frame);
        break;
      case "reject":
        this.handleReject(frame);
        break;
      case "game_end": {
        const outcome = frame.outcome as { winner_slot?: number | null; reason?: string } | undefined;
        if (!this.isReplay()) {
          this.emit({
            type: "gameOver",
            winner: this.winnerSeat(outcome?.winner_slot),
            reason: outcome?.reason ?? "game_end",
          });
        }
        if (Array.isArray(frame.wins)) this.publishStatus({ wins: frame.wins as [number, number] });
        break;
      }
      case "match_end":
        if (this.isReplay() && !this.replayComplete) {
          this.replayComplete = true;
          this.replayPlaying = false;
          this.publishReplay();
        }
        if (Array.isArray(frame.scores)) {
          this.publishStatus({ scores: frame.scores as [number, number], matchComplete: true });
        }
        break;
    }
  }

  private handleHello(frame: HelloFrame): void {
    if (frame.match) {
      this.publishStatus({
        gameNumber: frame.match.game_number,
        gamesToWin: frame.match.games_to_win,
        wins: frame.match.wins,
      });
    }
    if (this.mode === "spectate") {
      this._playerId = 255;
      this.emit({
        type: "playerIdentity",
        playerId: 255,
        opponentName: null,
        playerNames: this.playerNames(frame.player_names),
      });
      return;
    }
    if (frame.seat === undefined) return;
    this._playerId = frame.seat;
    this.playerSlot = frame.slot ?? null;
    this.emit({
      type: "playerIdentity",
      playerId: frame.seat,
      opponentName: frame.player_names[1 - frame.seat] ?? null,
      playerNames: this.playerNames(frame.player_names),
    });
  }

  private handleReplayMeta(frame: ReplayMetaFrame): void {
    let startIndex = 0;
    this.replayGames = (frame.games ?? []).map((game) => {
      const segment = {
        gameNumber: game.game_number,
        startIndex,
        stepCount: game.steps,
      };
      startIndex += game.steps;
      return segment;
    });
    this.publishReplay();
  }

  private handleState(frame: StateFrame): void {
    if (this.isReplay() && this.replayComplete) return;
    const phase = frame.state?.phase_client ?? frame.step?.state?.phase_client;
    if (!phase) {
      this.failInitialization("Coworld server omitted the negotiated Phase client snapshot");
      return;
    }
    const state: GameState = { ...phase.state, derived: phase.derived ?? phase.state.derived };
    const snapshot: EngineSnapshot = {
      state,
      legalResult: {
        actions: phase.legal_actions,
        autoPassRecommended: phase.auto_pass_recommended,
        spellCosts: phase.spell_costs,
        legalActionsByObject: phase.legal_actions_by_object,
      },
      seq: nextSnapshotSeq(),
    };
    const events = frame.events ?? frame.step?.events ?? [];
    if (this.isReplay() && !this.replayComplete) {
      const firstFrame = this.replayFrames.length === 0;
      this.replayFrames.push({
        snapshot,
        events,
        gameNumber: frame.game_number ?? this.gameNumberForIndex(this.replayFrames.length),
        wallMs: frame.step?.wall_ms ?? null,
        actorSlot: frame.step?.actor_slot ?? null,
        action: frame.step?.action ?? null,
      });
      if (firstFrame) {
        this.snapshot = snapshot;
        this.replayIndex = 0;
      }
      this.publishReplay();
    } else {
      this.snapshot = snapshot;
    }

    if (frame.clocks_ms && this._playerId !== null && this.mode !== "spectate") {
      const ownSlot = this.playerSlot ?? 0;
      this.emit({
        type: "timerUpdate",
        player: this._playerId,
        remainingSeconds: Math.ceil(frame.clocks_ms[ownSlot] / 1000),
      });
      this.emit({
        type: "timerUpdate",
        player: 1 - this._playerId,
        remainingSeconds: Math.ceil(frame.clocks_ms[1 - ownSlot] / 1000),
      });
    }

    if (this.initResolve) {
      // Replay frames should be inert until the transport advances them. In
      // particular, presenting the first frame's StartingPlayerContest during
      // initialization leaves Phase's tap-to-continue overlay covering the
      // whole replay before playback has even begun.
      this.initialEvents = this.isReplay() ? [] : events;
      this.initResolve();
      this.initResolve = null;
      this.initReject = null;
    } else if (this.pending) {
      this.pending.events = events;
    } else if (!this.isReplay()) {
      this.emit({ type: "stateChanged", snapshot, events });
    }
  }

  private handleAck(frame: { [key: string]: unknown }): void {
    const id = typeof frame.cmd_id === "number" ? frame.cmd_id : -1;
    if (!this.pending || this.pending.id !== id) return;
    const pending = this.pending;
    this.pending = null;
    this.emit({ type: "actionPendingChanged", pending: false });
    pending.resolve({ events: pending.events });
  }

  private handleReject(frame: { [key: string]: unknown }): void {
    const id = typeof frame.cmd_id === "number" ? frame.cmd_id : -1;
    if (!this.pending || this.pending.id !== id) return;
    const error = frame.error as { detail?: string; kind?: string } | undefined;
    const pending = this.pending;
    this.pending = null;
    this.emit({ type: "actionPendingChanged", pending: false });
    pending.reject(
      new AdapterError(
        error?.kind === "illegal_action" ? "STALE_ACTION" : "ACTION_REJECTED",
        error?.detail ?? "Coworld rejected the action",
        true,
      ),
    );
  }

  private requireSnapshot(): EngineSnapshot {
    if (!this.snapshot) {
      throw new AdapterError("NOT_INITIALIZED", "Coworld has not sent game state", true);
    }
    return this.snapshot;
  }

  private failInitialization(message: string): void {
    if (!this.initReject) return;
    this.initReject(new AdapterError("WS_ERROR", message, true));
    this.initResolve = null;
    this.initReject = null;
  }

  private emit(event: WsAdapterEvent): void {
    for (const listener of this.listeners) listener(event);
  }

  private playerNames(names: [string, string]): Record<number, string> {
    return { 0: names[0], 1: names[1] };
  }

  private winnerSeat(winnerSlot: number | null | undefined): PlayerId | null {
    if (winnerSlot === null || winnerSlot === undefined) return null;
    if (this.playerSlot === null || this._playerId === null || this._playerId === 255) {
      return winnerSlot;
    }
    return winnerSlot === this.playerSlot ? this._playerId : 1 - this._playerId;
  }

  private isReplay(): boolean {
    return document.body.dataset.coworldRole === "replay";
  }

  private installReplayController(): void {
    const host = window as unknown as {
      __coworldReplay?: CoworldReplayController;
    };
    host.__coworldReplay = {
      play: () => this.playReplay(),
      pause: () => this.pauseReplay(),
      seek: (index) => this.seekReplay(index),
      step: (offset) => this.seekReplay(this.replayIndex + offset),
      seekTurn: (index) => this.seekReplayTurn(index),
      stepTurn: (offset) => this.seekReplayTurn(this.replayPosition().turnIndex + offset),
      seekGame: (index) => this.seekReplayGame(index),
      stepGame: (offset) => this.seekReplayGame(this.replayPosition().gameIndex + offset),
      setRate: (rate) => this.setReplayRate(rate),
    };
    this.replayKeyHandler = (event) => this.handleReplayKey(event);
    window.addEventListener("keydown", this.replayKeyHandler, true);
    this.publishReplay();
  }

  private playReplay(): void {
    if (!this.replayComplete || this.replayFrames.length === 0) return;
    if (this.replayTimer !== null) return;
    if (this.replayIndex >= this.replayFrames.length - 1) this.showReplayFrame(0, false);
    this.replayPlaying = true;
    this.publishReplay();
    this.scheduleReplayAdvance();
  }

  private pauseReplay(): void {
    this.replayPlaying = false;
    if (this.replayTimer !== null) window.clearTimeout(this.replayTimer);
    this.replayTimer = null;
    this.publishReplay();
  }

  private seekReplay(index: number): void {
    if (this.replayFrames.length === 0) return;
    this.pauseReplay();
    this.showReplayFrame(index, false);
  }

  private showReplayFrame(index: number, includeEvents: boolean): void {
    this.replayIndex = Math.max(0, Math.min(Math.round(index), this.replayFrames.length - 1));
    const frame = this.replayFrames[this.replayIndex];
    this.snapshot = frame.snapshot;
    this.emit({ type: "stateChanged", snapshot: frame.snapshot, events: includeEvents ? frame.events : [] });
    this.publishReplay();
  }

  private scheduleReplayAdvance(): void {
    if (!this.replayPlaying || this.replayIndex >= this.replayFrames.length - 1) {
      this.pauseReplay();
      return;
    }
    this.replayTimer = window.setTimeout(() => {
      this.replayTimer = null;
      this.showReplayFrame(this.replayIndex + 1, true);
      this.scheduleReplayAdvance();
    }, this.replayDelay());
  }

  private replayDelay(): number {
    const current = this.replayFrames[this.replayIndex];
    const next = this.replayFrames[this.replayIndex + 1];
    if (!current || !next) return 650 / this.replayRate;
    if (current.gameNumber !== next.gameNumber) return 1200 / this.replayRate;
    const elapsed =
      current.wallMs === null || next.wallMs === null ? 650 : next.wallMs - current.wallMs;
    return Math.max(400, Math.min(elapsed, 1400)) / this.replayRate;
  }

  private setReplayRate(rate: number): void {
    if (![0.5, 1, 2, 4].includes(rate)) return;
    this.replayRate = rate;
    if (this.replayPlaying) {
      if (this.replayTimer !== null) window.clearTimeout(this.replayTimer);
      this.replayTimer = null;
      this.scheduleReplayAdvance();
    }
    this.publishReplay();
  }

  private seekReplayGame(gameIndex: number): void {
    const games = this.availableReplayGames();
    if (games.length === 0) return;
    const target = games[Math.max(0, Math.min(Math.round(gameIndex), games.length - 1))];
    this.seekReplay(target.startIndex);
  }

  private seekReplayTurn(turnIndex: number): void {
    const position = this.replayPosition();
    const turns = this.turnStarts(position.gameNumber);
    if (turns.length === 0) return;
    const target = turns[Math.max(0, Math.min(Math.round(turnIndex), turns.length - 1))];
    this.seekReplay(target.index);
  }

  private handleReplayKey(event: KeyboardEvent): void {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    const target = event.target as HTMLElement | null;
    if (
      target &&
      (target.isContentEditable || ["INPUT", "SELECT", "TEXTAREA", "BUTTON"].includes(target.tagName))
    ) {
      return;
    }
    if (event.code === "Space") {
      event.preventDefault();
      event.stopPropagation();
      this.replayPlaying ? this.pauseReplay() : this.playReplay();
    } else if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      event.stopPropagation();
      const offset = event.key === "ArrowLeft" ? -1 : 1;
      if (event.shiftKey) this.seekReplayTurn(this.replayPosition().turnIndex + offset);
      else this.seekReplay(this.replayIndex + offset);
    } else if (event.key === "PageUp" || event.key === "PageDown") {
      event.preventDefault();
      event.stopPropagation();
      this.seekReplayGame(this.replayPosition().gameIndex + (event.key === "PageUp" ? -1 : 1));
    }
  }

  private availableReplayGames(): ReplayGameSegment[] {
    if (this.replayGames.length > 0) return this.replayGames;
    const games: ReplayGameSegment[] = [];
    for (const [index, frame] of this.replayFrames.entries()) {
      const current = games[games.length - 1];
      if (!current || current.gameNumber !== frame.gameNumber) {
        games.push({ gameNumber: frame.gameNumber, startIndex: index, stepCount: 1 });
      } else {
        current.stepCount += 1;
      }
    }
    return games;
  }

  private gameNumberForIndex(index: number): number {
    const game = this.replayGames.find(
      (candidate) => index >= candidate.startIndex && index < candidate.startIndex + candidate.stepCount,
    );
    return game?.gameNumber ?? this.replayFrames[this.replayFrames.length - 1]?.gameNumber ?? 1;
  }

  private turnStarts(gameNumber: number): Array<{ index: number; number: number }> {
    const turns: Array<{ index: number; number: number }> = [];
    for (const [index, frame] of this.replayFrames.entries()) {
      if (frame.gameNumber !== gameNumber) continue;
      const number = frame.snapshot.state.turn_number;
      if (turns[turns.length - 1]?.number !== number) turns.push({ index, number });
    }
    return turns;
  }

  private replayPosition(): Omit<CoworldReplayState, "playing" | "complete" | "rate" | "actionLabel"> {
    const games = this.availableReplayGames();
    const frame = this.replayFrames[this.replayIndex];
    const gameIndex = Math.max(
      0,
      games.findIndex(
        (game) =>
          this.replayIndex >= game.startIndex && this.replayIndex < game.startIndex + game.stepCount,
      ),
    );
    const game = games[gameIndex] ?? { gameNumber: 1, startIndex: 0, stepCount: 0 };
    const turns = this.turnStarts(game.gameNumber);
    const turnNumber = frame?.snapshot.state.turn_number ?? turns[0]?.number ?? 0;
    const turnIndex = Math.max(0, turns.findIndex((turn) => turn.number === turnNumber));
    return {
      index: this.replayIndex,
      count: this.replayFrames.length,
      gameIndex,
      gameCount: games.length,
      gameNumber: game.gameNumber,
      gameStepIndex: Math.max(0, this.replayIndex - game.startIndex),
      gameStepCount: game.stepCount,
      turnIndex,
      turnCount: turns.length,
      turnNumber,
    };
  }

  private replayActionLabel(): string {
    const frame = this.replayFrames[this.replayIndex];
    if (!frame?.action) {
      return this.replayPosition().gameStepIndex === 0 ? "Game start" : "State update";
    }
    const action = frame.action.type.replace(/([a-z0-9])([A-Z])/g, "$1 $2");
    return frame.actorSlot === null ? action : `Player ${frame.actorSlot + 1} · ${action}`;
  }

  private publishReplay(): void {
    const host = window as unknown as {
      __coworldReplayState?: CoworldReplayState;
    };
    host.__coworldReplayState = {
      ...this.replayPosition(),
      playing: this.replayPlaying,
      complete: this.replayComplete,
      rate: this.replayRate,
      actionLabel: this.replayActionLabel(),
    };
    window.dispatchEvent(new Event("coworld-replay-status"));
  }

  private publishStatus(update: Record<string, unknown>): void {
    const host = window as unknown as { __coworldStatus?: Record<string, unknown> };
    host.__coworldStatus = { ...host.__coworldStatus, ...update };
    window.dispatchEvent(new Event("coworld-status"));
  }
}
