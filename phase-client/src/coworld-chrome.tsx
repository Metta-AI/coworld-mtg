import { useEffect, useState } from "react";

import type { CoworldReplayController, CoworldReplayState } from "./coworld-ws-adapter";

interface CoworldStatus {
  connection?: string;
  gameNumber?: number;
  gamesToWin?: number;
  wins?: [number, number];
  scores?: [number, number];
  matchComplete?: boolean;
}

type CoworldWindow = Window & {
  __coworldStatus?: CoworldStatus;
  __coworldReplayState?: CoworldReplayState;
  __coworldReplay?: CoworldReplayController;
};

function useWindowState<T>(event: string, read: () => T): T {
  const [value, setValue] = useState(read);
  useEffect(() => {
    const update = () => setValue(read());
    window.addEventListener(event, update);
    update();
    return () => window.removeEventListener(event, update);
  }, [event]);
  return value;
}

export function CoworldChrome() {
  const host = window as CoworldWindow;
  const status = useWindowState("coworld-status", () => host.__coworldStatus ?? {});
  const replay = useWindowState<CoworldReplayState | null>(
    "coworld-replay-status",
    () => host.__coworldReplayState ?? null,
  );

  return (
    <>
      {(status.gameNumber || status.matchComplete || status.connection === "disconnected") && (
        <aside className="fixed left-2 top-2 z-[120] rounded-md bg-black/75 px-3 py-1 text-xs text-white shadow-lg backdrop-blur">
          {status.matchComplete ? "Match complete" : `Game ${status.gameNumber ?? 1}`}
          {status.wins && ` · ${status.wins[0]}–${status.wins[1]}`}
          {status.connection === "disconnected" && " · disconnected"}
        </aside>
      )}
      {replay && (
        <aside
          aria-label="Replay controls"
          className="fixed bottom-3 left-1/2 z-[120] w-[min(46rem,calc(100vw-1rem))] -translate-x-1/2 rounded-xl border border-white/15 bg-zinc-950/90 px-4 py-3 text-xs text-white shadow-2xl backdrop-blur-md"
        >
          <div className="mb-2 flex min-w-0 items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="truncate font-semibold">
                {replay.count === 0
                  ? "Loading replay"
                  : `Game ${replay.gameIndex + 1}/${Math.max(1, replay.gameCount)} · Turn ${replay.turnNumber} · ${replay.actionLabel}`}
              </div>
              <div className="mt-0.5 hidden text-[10px] text-white/55 sm:block">
                Space: play/pause · ←/→: event · Shift+←/→: turn · Page Up/Down: game
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-1">
              <button
                type="button"
                aria-label="Previous event"
                title="Previous event (Left arrow)"
                className="rounded-md bg-white/10 px-2.5 py-1.5 hover:bg-white/20 disabled:opacity-35"
                disabled={replay.index <= 0}
                onClick={() => host.__coworldReplay?.step(-1)}
              >
                Back
              </button>
              <button
                type="button"
                className="min-w-16 rounded-md bg-white px-3 py-1.5 font-semibold text-black hover:bg-white/85 disabled:opacity-40"
                disabled={!replay.complete || replay.count === 0}
                onClick={() =>
                  replay.playing ? host.__coworldReplay?.pause() : host.__coworldReplay?.play()
                }
              >
                {!replay.complete
                  ? "Loading…"
                  : replay.playing
                    ? "Pause"
                    : replay.index >= replay.count - 1
                      ? "Replay"
                      : "Play"}
              </button>
              <button
                type="button"
                aria-label="Next event"
                title="Next event (Right arrow)"
                className="rounded-md bg-white/10 px-2.5 py-1.5 hover:bg-white/20 disabled:opacity-35"
                disabled={replay.index >= replay.count - 1}
                onClick={() => host.__coworldReplay?.step(1)}
              >
                Next
              </button>
              <label className="ml-1 flex items-center gap-1 text-white/65">
                <span className="sr-only">Playback speed</span>
                <select
                  aria-label="Playback speed"
                  className="rounded-md border border-white/10 bg-white/10 px-1.5 py-1.5 text-white"
                  value={replay.rate}
                  onChange={(event) => host.__coworldReplay?.setRate(Number(event.currentTarget.value))}
                >
                  {[0.5, 1, 2, 4].map((rate) => (
                    <option key={rate} value={rate} className="bg-zinc-900">
                      {rate}×
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <ReplaySlider
            label="Event"
            value={replay.index}
            count={replay.count}
            display={`${Math.min(replay.index + 1, replay.count)}/${replay.count}`}
            onChange={(value) => host.__coworldReplay?.seek(value)}
          />
          <ReplaySlider
            label="Turn"
            value={replay.turnIndex}
            count={replay.turnCount}
            display={`${replay.turnIndex + 1}/${Math.max(1, replay.turnCount)}`}
            onChange={(value) => host.__coworldReplay?.seekTurn(value)}
          />
          <ReplaySlider
            label="Game"
            value={replay.gameIndex}
            count={replay.gameCount}
            display={`${replay.gameIndex + 1}/${Math.max(1, replay.gameCount)}`}
            onChange={(value) => host.__coworldReplay?.seekGame(value)}
          />
        </aside>
      )}
    </>
  );
}

function ReplaySlider({
  label,
  value,
  count,
  display,
  onChange,
}: {
  label: string;
  value: number;
  count: number;
  display: string;
  onChange: (value: number) => void;
}) {
  const max = Math.max(0, count - 1);
  return (
    <label className="grid grid-cols-[3.25rem_1fr_3rem] items-center gap-2 py-0.5 text-white/65">
      <span>{label}</span>
      <input
        aria-label={`${label} position`}
        type="range"
        min={0}
        max={max}
        disabled={count <= 1}
        value={Math.min(value, max)}
        onChange={(event) => onChange(Number(event.currentTarget.value))}
        className="h-1.5 w-full cursor-pointer accent-white disabled:cursor-default disabled:opacity-40"
      />
      <output className="text-right tabular-nums text-white/80">{count === 0 ? "–" : display}</output>
    </label>
  );
}
