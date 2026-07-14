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
  execFileSync("cargo", ["build", "--quiet", "-p", "cogatrice-server"], {
    cwd: repoRoot,
    stdio: "inherit",
    env: rustEnv()
  });
});

test("two browser seats can play a land, auto-pay for a spell, and declare an attacker", async ({ page, context }) => {
  test.setTimeout(120_000);
  const harness = await startHarness();
  const opponent = await context.newPage();
  try {
    await page.goto(`http://127.0.0.1:${harness.port}/client/player?slot=0&token=tokA`);
    await opponent.goto(`http://127.0.0.1:${harness.port}/client/player?slot=1&token=tokB`);

    await expect(page.getByRole("button", { name: "Keep", exact: true })).toBeVisible({ timeout: 20_000 });
    await expect(opponent.getByRole("button", { name: "Keep", exact: true })).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole("heading", { name: "Your hand" })).toBeVisible();
    await expect(opponent.getByRole("heading", { name: "Your hand" })).toBeVisible();

    await page.getByRole("button", { name: "Keep", exact: true }).click();
    await opponent.getByRole("button", { name: "Keep", exact: true }).click();

    await expect(page.getByRole("button", { name: "Full Control", exact: true })).toBeVisible();
    const upkeepStop = page.getByRole("button", { name: "Set Upkeep stop on opponent turns" });
    await upkeepStop.click();
    await expect(page.getByRole("button", { name: "Remove Upkeep stop on opponent turns" })).toBeVisible();
    await page.getByRole("button", { name: "Remove Upkeep stop on opponent turns" }).click();
    await expect(page.getByRole("button", { name: "Set Upkeep stop on opponent turns" })).toBeVisible();
    await expect(page.getByRole("button", { name: /object_id|Tap Land For Mana/i })).toHaveCount(0);

    await page.getByRole("button", { name: "Full Control", exact: true }).click();
    await opponent.getByRole("button", { name: "Full Control", exact: true }).click();
    await expect(page.getByRole("button", { name: "Full Control", exact: true })).toHaveAttribute("aria-pressed", "true");

    const firstCard = page.getByRole("region", { name: "Your hand" }).locator("article.game-card").first();
    await firstCard.hover();
    await expect(page.locator(".card-preview.visible")).toBeVisible();

    await page.getByRole("region", { name: "You", exact: true }).getByRole("button", { name: /^View Graveyard:/ }).click();
    await expect(page.getByRole("dialog", { name: "Graveyard" })).toBeVisible();
    await expect(page.getByText("There are no cards here.")).toBeVisible();
    await page.getByRole("button", { name: "Close Graveyard" }).click();
    await expect(page.getByRole("dialog", { name: "Graveyard" })).toHaveCount(0);

    const pages = [page, opponent];
    let played: { page: Page; label: string } | null = null;
    for (let step = 0; step < 40 && !played; step += 1) {
      played = await tryPlayLand(pages);
      if (played) break;
      await clickOneOf(pages, [
        /^Pass$/,
        /^End Turn$/,
        /^No attacks$/,
        /^Block with 0 creature\(s\)$/,
        /^Select \d+ card\(s\)$/
      ]);
    }

    expect(played, "Phase should expose a land play in the active player's main phase").not.toBeNull();
    const battlefield = played!.page.getByRole("heading", { name: "Your battlefield" }).locator("..");
    const landName = played!.label.replace(/^Play /, "");
    if (landName === "land") {
      await expect(battlefield.getByText("Empty", { exact: true })).toHaveCount(0, { timeout: 20_000 });
    } else {
      await expect(battlefield.locator(`img[alt="${landName}"]`)).toBeVisible({ timeout: 20_000 });
    }

    const cast = await tryCastSpell(pages);
    expect(cast, "a one-mana creature should be castable after the legal land play").not.toBeNull();
    await expect(cast!.page.locator(".stack-zone").getByText(cast!.cardName, { exact: true })).toBeVisible({ timeout: 20_000 });
    await expect(cast!.page.locator(".stack-card.top")).toContainText("Next to resolve");

    await page.getByRole("button", { name: "Full Control", exact: true }).click();
    await opponent.getByRole("button", { name: "Full Control", exact: true }).click();

    const creature = cast!.page.getByRole("region", { name: "Your battlefield" }).locator(`article:has(img[alt="${cast!.cardName}"])`);
    for (let step = 0; step < 12 && !await creature.isVisible().catch(() => false); step += 1) {
      await clickOneOf(pages, [/^Pass$/, /^End Turn$/]);
    }
    await expect(creature).toBeVisible({ timeout: 20_000 });
    await expect(cast!.page.getByRole("region", { name: "Your battlefield" }).locator("article.tapped")).toBeVisible();

    let declaredAttack = false;
    for (let step = 0; step < 100 && !declaredAttack; step += 1) {
      const noAttacks = cast!.page.getByRole("button", { name: "No attacks", exact: true });
      if (await noAttacks.isVisible().catch(() => false)) {
        await creature.click({ force: true });
        const attack = cast!.page.getByRole("button", { name: "Attack (1)", exact: true });
        await expect(attack).toBeEnabled();
        await attack.click();
        declaredAttack = true;
        break;
      }
      if (await tryResolveCardSelection(pages)) continue;
      await clickOneOf(pages, [/^Pass$/, /^End Turn$/, /^No blocks$/]);
    }
    expect(declaredAttack, "the active creature should reach a selectable attacker decision").toBe(true);
    await expect(creature).toHaveClass(/attacking/, { timeout: 20_000 });
  } finally {
    await harness.stop();
  }
});

type Page = import("@playwright/test").Page;

async function clickOneOf(pages: Page[], names: RegExp[]): Promise<void> {
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    for (const name of names) {
      if (await tryClickAction(pages, name)) return;
    }
    await pages[0].waitForTimeout(50);
  }
  const diagnostics = await Promise.all(pages.map(async (candidate, index) => ({
    page: index,
    title: await candidate.locator("header strong").textContent().catch(() => null),
    buttons: await candidate.getByRole("button").allTextContents()
  })));
  throw new Error(`no enabled action matching ${names}: ${JSON.stringify(diagnostics)}`);
}

async function tryClickAction(pages: Page[], name: RegExp): Promise<{ page: Page; label: string } | null> {
  for (const candidate of pages) {
    const action = candidate.getByRole("button", { name }).first();
    if (!await action.isVisible().catch(() => false) || !await action.isEnabled().catch(() => false)) continue;
    const label = await action.innerText().catch(() => "");
    if (!label) continue;
    if (await action.click({ timeout: 1_000 }).then(() => true).catch(() => false)) {
      // The state fan-out reaches the two sockets independently. Let both
      // pages consume the authoritative update before choosing the next seat's
      // action, otherwise the driver can race a just-replaced button.
      await candidate.waitForTimeout(100);
      return { page: candidate, label };
    }
  }
  return null;
}

async function tryPlayLand(pages: Page[]): Promise<{ page: Page; label: string } | null> {
  for (const candidate of pages) {
    const hand = candidate.getByRole("region", { name: "Your hand" });
    const land = hand.locator("article.actionable").filter({ has: candidate.locator('img[alt="Mountain"], img[alt="Forest"]') }).first();
    if (!await land.isVisible().catch(() => false)) continue;
    await land.click({ force: true });
    const play = candidate.getByRole("region", { name: "Card actions" }).getByRole("button", { name: /^Play / }).first();
    if (!await play.isVisible().catch(() => false)) continue;
    const label = await play.innerText();
    await play.click();
    await candidate.waitForTimeout(100);
    return { page: candidate, label };
  }
  return null;
}

async function tryCastSpell(pages: Page[]): Promise<{ page: Page; cardName: string } | null> {
  for (const candidate of pages) {
    const cards = candidate.getByRole("region", { name: "Your hand" }).locator("article.actionable");
    for (let index = 0; index < await cards.count(); index += 1) {
      const card = cards.nth(index);
      const cardName = await card.getAttribute("aria-label");
      if (!cardName || cardName === "Mountain" || cardName === "Forest") continue;
      await card.click({ force: true });
      const cast = candidate.getByRole("region", { name: "Card actions" }).getByRole("button", { name: /^Cast / }).first();
      if (!await cast.isVisible().catch(() => false)) continue;
      await cast.click();
      await candidate.waitForTimeout(100);
      return { page: candidate, cardName };
    }
  }
  return null;
}

async function tryResolveCardSelection(pages: Page[]): Promise<boolean> {
  for (const candidate of pages) {
    const confirm = candidate.getByRole("button", { name: /^Confirm \(\d+\)$/ });
    if (!await confirm.isVisible().catch(() => false)) continue;
    for (let selected = 0; selected < 10; selected += 1) {
      if (await confirm.isEnabled().catch(() => false)) {
        await confirm.click();
        await candidate.waitForTimeout(100);
        return true;
      }
      const next = candidate.getByRole("region", { name: "Your hand" }).locator("article.actionable:not(.selected)").first();
      if (!await next.isVisible().catch(() => false)) break;
      await next.click({ force: true });
    }
  }
  return false;
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
        players: [{ name: "browser-0" }, { name: "browser-1" }],
        seed: 5151,
        decks: ["red_rush", "green_stompy"],
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
