import { expect, test } from "@playwright/test";
import { spawn, execFileSync, type ChildProcess } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import net from "node:net";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const binSuffix = process.platform === "win32" ? ".exe" : "";

test.beforeAll(() => {
  execFileSync("cargo", ["build", "--quiet", "-p", "coworld-mtg-server"], {
    cwd: repoRoot,
    stdio: "inherit",
    env: rustEnv()
  });
});

test("two browser seats render Phase and submit a Phase preference action", async ({ page, context }) => {
  test.setTimeout(120_000);
  const harness = await startHarness();
  const opponent = await context.newPage();
  try {
    await page.goto(`http://127.0.0.1:${harness.port}/client/player?slot=0&token=tokA`);
    await opponent.goto(`http://127.0.0.1:${harness.port}/client/player?slot=1&token=tokB`);

    await dismissOpeningRoll(page);
    await dismissOpeningRoll(opponent);

    await expect(page.getByRole("heading", { name: "Review your opening hand" })).toBeVisible();
    await expect(opponent.getByRole("heading", { name: "Review your opening hand" })).toBeVisible();
    await expect(page.locator('img[src^="https://cards.scryfall.io"]').first()).toBeVisible({
      timeout: 20_000
    });
    await page.getByRole("button", { name: "Keep Hand", exact: true }).click();
    await opponent.getByRole("button", { name: "Keep Hand", exact: true }).click();

    await expect(page.getByRole("button", { name: "Game menu" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Full Control Off" })).toBeVisible();
    await expect(page.getByRole("button", { name: "View full hand (7 cards)" })).toBeVisible();
    await expect(page.getByAltText("Card back")).toHaveCount(7);

    const upkeepStop = page.getByRole("button", { name: /Phase stop: Upkeep step.*No stop set/ });
    await upkeepStop.click();
    await expect(page.getByRole("button", { name: /Phase stop: Upkeep step/ })).toHaveAttribute(
      "aria-pressed",
      "true"
    );
  } finally {
    await harness.stop();
  }
});

type Page = import("@playwright/test").Page;

async function dismissOpeningRoll(page: Page): Promise<void> {
  const continueButton = page.getByRole("button", { name: "Tap to continue", exact: true });
  await expect(continueButton).toBeVisible({ timeout: 20_000 });
  await continueButton.click();
}

async function startHarness(): Promise<{ port: number; stop: () => Promise<void> }> {
  const port = await freePort();
  const root = mkdtempSync(join(tmpdir(), "coworld-mtg-browser-"));
  const config = join(root, "config.json");
  writeFileSync(
    config,
    JSON.stringify(
      {
        tokens: ["tokA", "tokB"],
        players: [{ name: "browser-0" }, { name: "browser-1" }],
        seed: 5151,
        decks: ["lorehold_excavation", "fractal_convergence"],
        games_to_win: 1,
        clock_s: 300,
        decision_cap_s: 60,
        player_connect_timeout_s: 10
      },
      null,
      2
    )
  );
  const env: NodeJS.ProcessEnv = {
    ...process.env,
    COGAME_HOST: "127.0.0.1",
    COGAME_PORT: String(port),
    COGAME_CORPUS_DIR: join(repoRoot, ".private", "corpus"),
    COGAME_CONFIG_URI: config,
    COGAME_RESULTS_URI: join(root, "results.json"),
    COGAME_SAVE_REPLAY_URI: join(root, "replay.json"),
    COGAME_LOG_URI: join(root, "log.txt"),
    COGAME_WEB_DIST: join(repoRoot, "web", "dist")
  };
  delete env.COGAME_LOAD_REPLAY_URI;

  const server = spawn(join(repoRoot, "target", "debug", `coworld-mtg-server${binSuffix}`), {
    cwd: repoRoot,
    env,
    stdio: ["ignore", "pipe", "pipe"]
  });
  collectOutput("server", server);
  await waitHealthz(port);

  return {
    port,
    stop: async () => {
      await stopProcess(server);
    }
  };
}

function rustEnv(): NodeJS.ProcessEnv {
  return {
    ...process.env,
    PATH: `/tmp/coworld-rustup-cargo/bin:${process.env.PATH ?? ""}`,
    CARGO_HOME: `${process.env.HOME}/.cargo`,
    RUSTUP_HOME: "/tmp/coworld-rustup",
    RUSTUP_TOOLCHAIN: "nightly-2026-04-19",
    RUSTC_BOOTSTRAP: "1",
    RUSTFLAGS: "-Zcrate-attr=feature(if_let_guard)",
    CARGO_INCREMENTAL: "0",
    CARGO_PROFILE_DEV_DEBUG: "0"
  };
}

function collectOutput(name: string, child: ChildProcess): void {
  child.stdout?.on("data", (chunk) => process.stdout.write(`[${name}] ${chunk}`));
  child.stderr?.on("data", (chunk) => process.stderr.write(`[${name}] ${chunk}`));
}

async function waitHealthz(port: number): Promise<void> {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/healthz`);
      if (response.ok) {
        return;
      }
    } catch {
      await delay(50);
    }
  }
  throw new Error("server did not become healthy");
}

async function stopProcess(child: ChildProcess): Promise<void> {
  if (child.exitCode !== null || child.signalCode !== null) {
    return;
  }
  child.kill("SIGTERM");
  await Promise.race([
    new Promise<void>((resolveDone) => child.once("exit", () => resolveDone())),
    delay(2000).then(() => {
      if (child.exitCode === null && child.signalCode === null) {
        child.kill("SIGKILL");
      }
    })
  ]);
}

async function freePort(): Promise<number> {
  const server = net.createServer();
  await new Promise<void>((resolveListen) => server.listen(0, "127.0.0.1", resolveListen));
  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("failed to allocate port");
  }
  const port = address.port;
  await new Promise<void>((resolveClose) => server.close(() => resolveClose()));
  return port;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolveDelay) => setTimeout(resolveDelay, ms));
}
