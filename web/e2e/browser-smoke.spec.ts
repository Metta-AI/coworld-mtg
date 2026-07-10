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
  execFileSync("cargo", ["build", "--quiet", "-p", "cogatrice-server", "-p", "goldfish"], {
    cwd: repoRoot,
    stdio: "inherit"
  });
});

test("browser slot 0 can keep, play a land, and advance phase against goldfish", async ({ page }) => {
  const harness = await startHarness();
  try {
    await page.goto(`http://127.0.0.1:${harness.port}/client/player?slot=0&token=tokA`);
    await expect(page.getByTestId("mulligan-modal")).toBeVisible();
    await page.getByTestId("keep-button").click();

    await expect(page.getByTestId("window-banner")).toContainText(/Your window/i, { timeout: 20_000 });
    await advanceToMain1(page);

    const land = page.locator('[data-testid="hand-card"][data-card-kind="land"]').first();
    await expect(land).toBeVisible();
    const landName = (await land.locator(".card-title strong").innerText()).trim();
    await land.click();
    await page.getByRole("button", { name: "Play to battlefield" }).click();

    await expect(page.locator('[data-testid="battlefield-card"][data-card-kind="land"]').filter({ hasText: landName })).toBeVisible({
      timeout: 10_000
    });
    await expect(page.getByTestId("window-banner")).toContainText(/Your window/i, { timeout: 20_000 });

    await page.getByTestId("next-phase").click();
    await expect(page.getByTestId("phase-begin_combat")).toHaveClass(/current/, { timeout: 20_000 });
  } finally {
    await harness.stop();
  }
});

async function advanceToMain1(page: import("@playwright/test").Page): Promise<void> {
  for (let step = 0; step < 4; step += 1) {
    if (await page.getByTestId("phase-main1").evaluate((node) => node.classList.contains("current")).catch(() => false)) {
      return;
    }
    await page.getByTestId("next-phase").click();
    await expect(page.getByTestId("window-banner")).toContainText(/Your window/i, { timeout: 20_000 });
  }
  await expect(page.getByTestId("phase-main1")).toHaveClass(/current/);
}

async function startHarness(): Promise<{ port: number; stop: () => Promise<void> }> {
  const port = await freePort();
  const root = mkdtempSync(join(tmpdir(), "cogatrice-browser-"));
  const config = join(root, "config.json");
  writeFileSync(
    config,
    JSON.stringify(
      {
        tokens: ["tokA", "tokB"],
        players: [{ name: "browser-0" }, { name: "goldfish-1" }],
        seed: 5151,
        decks: ["red_rush", "green_stompy"],
        games_to_win: 1,
        starting_life: 20,
        turn_cap: 8,
        clock_s: 60,
        decision_cap_s: 5,
        player_connect_timeout_s: 10
      },
      null,
      2
    )
  );
  const env = {
    ...process.env,
    COGAME_HOST: "127.0.0.1",
    COGAME_PORT: String(port),
    COGAME_CONFIG_URI: config,
    COGAME_RESULTS_URI: join(root, "results.json"),
    COGAME_SAVE_REPLAY_URI: join(root, "replay.json"),
    COGAME_LOG_URI: join(root, "log.txt"),
    COGAME_WEB_DIST: join(repoRoot, "web", "dist")
  };
  delete env.COGAME_LOAD_REPLAY_URI;

  const server = spawn(join(repoRoot, "target", "debug", `cogatrice-server${binSuffix}`), {
    cwd: repoRoot,
    env,
    stdio: ["ignore", "pipe", "pipe"]
  });
  collectOutput("server", server);
  await waitHealthz(port);

  const goldfish = spawn(
    join(repoRoot, "target", "debug", `goldfish${binSuffix}`),
    ["--url", `ws://127.0.0.1:${port}/player?slot=1&token=tokB`],
    {
      cwd: repoRoot,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"]
    }
  );
  collectOutput("goldfish", goldfish);

  return {
    port,
    stop: async () => {
      await stopProcess(goldfish);
      await stopProcess(server);
    }
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
