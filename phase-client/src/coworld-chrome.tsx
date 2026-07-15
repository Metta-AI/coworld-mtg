import { useEffect, useState } from "react";

interface CoworldStatus {
  connection?: string;
  gameNumber?: number;
  gamesToWin?: number;
  wins?: [number, number];
  scores?: [number, number];
  matchComplete?: boolean;
}

interface ReplayState {
  index: number;
  count: number;
  playing: boolean;
  complete: boolean;
}

type CoworldWindow = Window & {
  __coworldStatus?: CoworldStatus;
  __coworldReplayState?: ReplayState;
  __coworldReplay?: { play: () => void; pause: () => void; seek: (index: number) => void };
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
  const replay = useWindowState<ReplayState | null>(
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
          className="fixed left-1/2 top-2 z-[120] flex -translate-x-1/2 items-center gap-2 rounded-md bg-black/80 px-3 py-1 text-xs text-white shadow-lg backdrop-blur"
        >
          <button
            type="button"
            className="rounded bg-white/15 px-2 py-1"
            onClick={() => (replay.playing ? host.__coworldReplay?.pause() : host.__coworldReplay?.play())}
          >
            {replay.playing ? "Pause" : "Play"}
          </button>
          <input
            aria-label="Replay position"
            type="range"
            min={0}
            max={Math.max(0, replay.count - 1)}
            value={Math.min(replay.index, Math.max(0, replay.count - 1))}
            onChange={(event) => host.__coworldReplay?.seek(Number(event.currentTarget.value))}
          />
          <span>{replay.count === 0 ? "Loading" : `${replay.index + 1}/${replay.count}`}</span>
        </aside>
      )}
    </>
  );
}
