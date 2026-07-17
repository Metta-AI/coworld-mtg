export interface CoworldReplayLogEntry {
  id: string;
  eventIndex: number;
  gameNumber: number;
  turnNumber: number;
  actorName: string | null;
  actionLabel: string;
  life: [number, number];
}

export interface CoworldReplayOutcome {
  gameNumber: number;
  winnerSlot: number | null;
  winnerName: string | null;
  loserSlot: number | null;
  loserName: string | null;
  reason: string;
  headline: string;
  detail: string;
}

export interface CoworldReplayTurnMarker {
  eventIndex: number;
  timelinePosition: number;
  gameNumber: number;
  turnNumber: number;
  activePlayerSlot: number;
  activePlayerName: string;
  life: [number, number];
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
  playerNames: [string, string];
  selectedPlayerSlot: number;
  seatPlayerSlots: [number, number];
  showPriorityPasses: boolean;
  logEntries: CoworldReplayLogEntry[];
  turnMarkers: CoworldReplayTurnMarker[];
  outcome: CoworldReplayOutcome | null;
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
  setPerspective: (playerSlot: number) => void;
  setShowPriorityPasses: (show: boolean) => void;
}
