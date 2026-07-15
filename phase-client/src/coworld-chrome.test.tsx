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
    };
    const host = window as ReplayWindow;
    host.__coworldReplay = controller;
    host.__coworldReplayState = replayState();

    render(<CoworldChrome />);

    expect(screen.getByText("Game 1/2 · Turn 2 · Player 1 · Pass Priority")).toBeVisible();
    expect(screen.getByLabelText("Event position")).toHaveAttribute("max", "4");
    expect(screen.getByLabelText("Turn position")).toHaveAttribute("max", "2");
    expect(screen.getByLabelText("Game position")).toHaveAttribute("max", "1");

    fireEvent.change(screen.getByLabelText("Event position"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Turn position"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Game position"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Playback speed"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Next event" }));
    fireEvent.click(screen.getByRole("button", { name: "Play" }));

    expect(controller.seek).toHaveBeenCalledWith(3);
    expect(controller.seekTurn).toHaveBeenCalledWith(2);
    expect(controller.seekGame).toHaveBeenCalledWith(1);
    expect(controller.setRate).toHaveBeenCalledWith(2);
    expect(controller.step).toHaveBeenCalledWith(1);
    expect(controller.play).toHaveBeenCalledOnce();

    host.__coworldReplayState = { ...replayState(), playing: true };
    act(() => window.dispatchEvent(new Event("coworld-replay-status")));
    fireEvent.click(screen.getByRole("button", { name: "Pause" }));
    expect(controller.pause).toHaveBeenCalledOnce();
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
    actionLabel: "Player 1 · Pass Priority",
  };
}
