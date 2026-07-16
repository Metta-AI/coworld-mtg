import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CoworldChrome } from "./coworld-chrome";
import type { CoworldReplayController, CoworldReplayState } from "./coworld-ws-adapter";

type ReplayWindow = Window & {
  __coworldReplay?: CoworldReplayController;
  __coworldReplayState?: CoworldReplayState;
};

describe("Coworld replay chrome", () => {
  afterEach(() => {
    cleanup();
    delete (window as ReplayWindow).__coworldReplay;
    delete (window as ReplayWindow).__coworldReplayState;
  });

  it("exposes event, turn, and game transport controls", () => {
    const controller: CoworldReplayController = {
      play: vi.fn(),
      pause: vi.fn(),
      seek: vi.fn(),
      step: vi.fn(),
      seekTurn: vi.fn(),
      stepTurn: vi.fn(),
      seekGame: vi.fn(),
      stepGame: vi.fn(),
      setRate: vi.fn(),
      setPerspective: vi.fn(),
      setShowPriorityPasses: vi.fn(),
    };
    const host = window as ReplayWindow;
    host.__coworldReplay = controller;
    host.__coworldReplayState = replayState();

    render(<CoworldChrome />);

    expect(screen.getByText("Game 1/2 · Turn 2 · Nissa · Cast Spell")).toBeVisible();
    expect(screen.getByLabelText("Event position")).toHaveAttribute("max", "4");
    expect(screen.getByLabelText("Turn position")).toHaveAttribute("max", "2");
    expect(screen.getByLabelText("Game position")).toHaveAttribute("max", "1");

    fireEvent.change(screen.getByLabelText("Event position"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Turn position"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Game position"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Playback speed"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Chandra" }));
    fireEvent.click(screen.getByRole("button", { name: "Show priority passes" }));
    fireEvent.click(screen.getByRole("button", { name: "Next event" }));
    fireEvent.click(screen.getByRole("button", { name: "Play" }));

    expect(controller.seek).toHaveBeenCalledWith(3);
    expect(controller.seekTurn).toHaveBeenCalledWith(2);
    expect(controller.seekGame).toHaveBeenCalledWith(1);
    expect(controller.setRate).toHaveBeenCalledWith(2);
    expect(controller.setPerspective).toHaveBeenCalledWith(1);
    expect(controller.setShowPriorityPasses).toHaveBeenCalledWith(true);
    expect(controller.step).toHaveBeenCalledWith(1);
    expect(controller.play).toHaveBeenCalledOnce();

    host.__coworldReplayState = { ...replayState(), playing: true };
    act(() => window.dispatchEvent(new Event("coworld-replay-status")));
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    expect(controller.pause).toHaveBeenCalledOnce();

    fireEvent.click(screen.getByRole("button", { name: "Moves" }));
    expect(screen.getByRole("complementary", { name: "Replay move log" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /Nissa · Cast Spell/ }));
    expect(controller.seek).toHaveBeenCalledWith(2);
  });

  it("hides the game control for a single-game replay", () => {
    const host = window as ReplayWindow;
    host.__coworldReplay = {
      play: vi.fn(), pause: vi.fn(), seek: vi.fn(), step: vi.fn(), seekTurn: vi.fn(),
      stepTurn: vi.fn(), seekGame: vi.fn(), stepGame: vi.fn(), setRate: vi.fn(),
      setPerspective: vi.fn(), setShowPriorityPasses: vi.fn(),
    };
    host.__coworldReplayState = { ...replayState(), gameCount: 1 };

    render(<CoworldChrome />);

    expect(screen.queryByLabelText("Game position")).not.toBeInTheDocument();
  });
});

function replayState(): CoworldReplayState {
  return {
    index: 2,
    count: 5,
    playing: false,
    complete: true,
    rate: 1,
    gameIndex: 0,
    gameCount: 2,
    gameNumber: 1,
    gameStepIndex: 2,
    gameStepCount: 3,
    turnIndex: 1,
    turnCount: 3,
    turnNumber: 2,
    actionLabel: "Nissa · Cast Spell",
    playerNames: ["Nissa", "Chandra"],
    selectedPlayerSlot: 0,
    seatPlayerSlots: [0, 1],
    showPriorityPasses: false,
    logEntries: [
      { eventIndex: 0, gameNumber: 1, turnNumber: 1, actorName: null, actionLabel: "Game start", life: [20, 20] },
      { eventIndex: 2, gameNumber: 1, turnNumber: 2, actorName: "Nissa", actionLabel: "Cast Spell", life: [18, 16] },
    ],
    turnMarkers: [
      { eventIndex: 0, timelinePosition: 0, gameNumber: 1, turnNumber: 1, activePlayerSlot: 0, activePlayerName: "Nissa", life: [20, 20] },
      { eventIndex: 2, timelinePosition: 0.5, gameNumber: 1, turnNumber: 2, activePlayerSlot: 1, activePlayerName: "Chandra", life: [18, 16] },
    ],
  };
}
