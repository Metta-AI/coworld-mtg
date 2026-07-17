import { expect, test } from "@playwright/test";
import { spawn, execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import net from "node:net";

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const binSuffix = process.platform === "win32" ? ".exe" : "";
const shots = process.env.SHOT_DIR ?? mkdtempSync(join(tmpdir(), "coworld-mtg-shots-"));

test.beforeAll(() => {
  mkdirSync(shots, { recursive: true });
  execFileSync(join(repoRoot, "scripts", "cargo.sh"), ["build", "--quiet", "-p", "coworld-mtg-server", "-p", "goldfish"], {
    cwd: repoRoot,
    stdio: "inherit",
    env: {
      ...process.env,
      CARGO_INCREMENTAL: "0",
      CARGO_PROFILE_DEV_DEBUG: "0"
    }
  });
});

test("capture player and global views", async ({ page, context }) => {
  test.setTimeout(120_000);
  const harness = await startHarness();
  try {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(`http://127.0.0.1:${harness.port}/client/player?slot=0&token=tokA`);
    const continueButton = page.getByRole("button", { name: "Tap to continue", exact: true });
    await expect(continueButton).toBeVisible({ timeout: 20_000 });
    await continueButton.click();
    await expect(page.getByRole("button", { name: "Keep Hand", exact: true })).toBeVisible({ timeout: 20_000 });
    await page.screenshot({ path: join(shots, "1-mulligan.png") });

    await page.getByRole("button", { name: "Keep Hand", exact: true }).click();
    await expect(page.getByRole("button", { name: "Game menu" })).toBeVisible({ timeout: 20_000 });
    await page.screenshot({ path: join(shots, "2-table-main1.png") });

    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.getByRole("button", { name: /View full hand/ })).toBeVisible();
    await page.screenshot({ path: join(shots, "3-table-mobile.png") });

    const globalPage = await context.newPage();
    await globalPage.setViewportSize({ width: 1440, height: 900 });
    await globalPage.goto(`http://127.0.0.1:${harness.port}/client/global`);
    await globalPage.waitForTimeout(2000);
    await globalPage.screenshot({ path: join(shots, "4-global.png") });

    console.log("SHOT_DIR=" + shots);
  } finally {
    await harness.stop();
  }
});

async function startHarness(): Promise<{ port: number; stop: () => Promise<void> }> {
  const port = await freePort();
  const root = mkdtempSync(join(tmpdir(), "coworld-mtg-shot-harness-"));
  const config = join(root, "config.json");
  writeFileSync(
    config,
    JSON.stringify({
      tokens: ["tokA", "tokB"],
      players: [{ name: "nishad" }, { name: "goldfish" }],
      seed: 977,
      decks: ["lorehold_excavation", "fractal_convergence"],
      games_to_win: 1,
      clock_s: 3600,
      decision_cap_s: 600,
      player_connect_timeout_s: 30
    })
  );
  const env: NodeJS.ProcessEnv = {
    ...process.env,
    COGAME_HOST: "127.0.0.1",
    COGAME_PORT: String(port),
    COGAME_CORPUS_DIR: join(repoRoot, ".private", "corpus"),
    COGAME_CONFIG_URI: config,
    COGAME_RESULTS_URI: join(root, "results.json"),
    COGAME_SAVE_REPLAY_URI: join(root, "replay.json"),
    COGAME_WEB_DIST: join(repoRoot, "web", "dist")
  };
  delete env.COGAME_LOAD_REPLAY_URI;
  const server = spawn(join(repoRoot, "target", "debug", `coworld-mtg-server${binSuffix}`), {
    cwd: repoRoot,
    env,
    stdio: ["ignore", "ignore", "ignore"]
  });
  await waitHealthz(port);
  const goldfish = spawn(
    join(repoRoot, "target", "debug", `goldfish${binSuffix}`),
    ["--url", `ws://127.0.0.1:${port}/player?slot=1&token=tokB`],
    { cwd: repoRoot, env: process.env, stdio: ["ignore", "ignore", "ignore"] }
  );
  return {
    port,
    stop: async () => {
      for (const child of [goldfish, server]) {
        if (child.exitCode === null && child.signalCode === null) {
          child.kill("SIGKILL");
        }
      }
    }
  };
}

async function waitHealthz(port: number): Promise<void> {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/healthz`);
      if (response.ok) return;
    } catch {
      await new Promise((r) => setTimeout(r, 50));
    }
  }
  throw new Error("server did not become healthy");
}

async function freePort(): Promise<number> {
  const server = net.createServer();
  await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("no port");
  const port = address.port;
  await new Promise<void>((r) => server.close(() => r()));
  return port;
}
