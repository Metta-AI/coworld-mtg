import { test, expect } from "@playwright/test";
import { createHash } from "node:crypto";

const url = process.env.FACTORY_VIEWER_URL || "http://127.0.0.1:4196/client/factory.html";
const digest = (text: string) => createHash("sha256").update(text).digest("hex");
const sourceText = JSON.stringify({ records: [{ id: "test-printing", oracle_id: "test-oracle", name: "Synthetic Browser Card", type_line: "Creature", oracle_text: "Synthetic test Oracle text.", mana_cost: "{1}{G}" }] });
const sourceId = digest(sourceText);
const caseText = JSON.stringify({ title: "Synthetic case", scenario: { cards: [] } });
const caseId = digest(caseText);
const feedbackId = "f".repeat(64);
const initial = {
  version: "software-factory-v1",
  run_id: "synthetic-browser-test", title: "Synthetic browser fixture",
  target: { name: "Test target", repository: "https://example.test/repository", baseline_revision: "synthetic-revision" },
  recording: { kind: "live" }, status: "running",
  stages: [
    { id: "sources", title: "Source data", next: ["cases"] },
    { id: "cases", title: "Case discovery", next: ["feedback"] },
    { id: "feedback", title: "Evaluation", next: ["decisions"] },
    { id: "decisions", title: "Decisions", next: [] },
  ],
  artifacts: {
    [sourceId]: { path: "records.json", media_type: "application/json", hash_mode: "bytes" },
    [caseId]: { path: "case.json", media_type: "application/json", hash_mode: "bytes" },
  },
  events: [
    { sequence: 0, elapsed_ms: 0, stage: "sources", payload: { kind: "source_imported", source: { snapshot_id: sourceId, provider: "Synthetic Scryfall fixture", url: "https://example.test/source", retrieved_at: "test fixture", description: "Synthetic browser testing data" } } },
    { sequence: 1, elapsed_ms: 100, stage: "cases", payload: { kind: "case_registered", case_id: caseId, title: "Synthetic browser case", derivation: { kind: "source_derived", source_ids: [sourceId], source_records: [{ source_id: sourceId, record_id: "test-oracle" }], recipe: "Synthetic derivation for UI assertions.", seed: null } } },
    { sequence: 2, elapsed_ms: 200, stage: "feedback", payload: { kind: "feedback_recorded", feedback: { feedback_id: feedbackId, case_id: caseId, execution_ids: [], evaluator: "test evaluator", evaluator_version: "test-only", adapter: "opaque", declared_strength: "weak", method: "Synthetic claim", bounded_claim: "This is a test-only bounded claim.", result: "satisfied", summary: "Synthetic weak feedback is satisfied" } } },
  ],
};
test("source provenance, scrubbing, and acceptance remain grounded in visible events", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs: [{ run_id: initial.run_id, title: initial.title, status: initial.status }] } }));
  await page.route("**/replay.json", route => route.fulfill({ json: initial }));
  await page.route("**/artifacts/*", route => {
    const id = route.request().url().split("/").pop();
    return route.fulfill({ contentType: "application/json", body: id === sourceId ? sourceText : caseText });
  });
  await page.goto(url);
  await expect(page.getByRole("heading", { name: "Synthetic browser fixture", exact: true })).toBeVisible();
  await expect(page.getByText("Synthetic weak feedback is satisfied", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Changes & decision" }).click();
  await expect(page.getByText("No decision recorded at this point", { exact: true })).toBeVisible();
  await page.getByRole("tab", { name: "Source & lineage" }).click();
  await expect(page.getByText("Synthetic test Oracle text.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Seek to beginning", exact: true }).click();
  await expect(page.locator(".case-panel").getByRole("heading", { name: "No case recorded at this point" })).toBeVisible();
  await page.getByRole("button", { name: "Next event", exact: true }).click();
  await expect(page.locator(".case-row")).toHaveCount(0);
  await page.getByRole("button", { name: "Next event", exact: true }).click();
  await expect(page.locator(".case-row")).toHaveCount(1);
  await page.getByRole("tab", { name: "Evidence", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No feedback recorded", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Next event", exact: true }).click();
  await expect(page.getByText("Synthetic weak feedback is satisfied", { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
  const workspace = await page.locator(".workspace").boundingBox();
  const transport = await page.locator(".transport").boundingBox();
  expect(workspace!.y + workspace!.height).toBeLessThanOrEqual(transport!.y + 1);
  await page.screenshot({ path: "test-results/factory-desktop.png", fullPage: true });
});
test("portable local replay works offline and exposes hash mismatches", async ({ page }) => {
  await page.route("**/factory-api/**", route => route.fulfill({ status: 503, body: "offline" }));
  await page.goto(url);
  await page.locator("#replay-file").setInputFiles({ name: "synthetic.portable.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify({ replay: initial, artifact_contents: { [sourceId]: sourceText, [caseId]: "corrupt" } })) });
  await expect(page.getByRole("heading", { name: "Synthetic browser fixture", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Case definition" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByText("SHA-256 does not match. This artifact is not trusted evidence.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  const downloads: string[] = [];
  page.on("download", item => downloads.push(item.suggestedFilename()));
  await page.getByRole("button", { name: "Save portable", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Complete the replay before exporting", exact: true })).toBeVisible();
  expect(downloads).toEqual([]);
  await expect(page.getByRole("link", { name: "Hydration and portable export instructions" })).toBeVisible();
});
test("mobile layout exposes the case and timeline without horizontal page overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs: [] } }));
  await page.goto(url);
  await page.locator("#replay-file").setInputFiles({ name: "synthetic.portable.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify({ replay: initial, artifact_contents: { [sourceId]: sourceText, [caseId]: caseText } })) });
  await expect(page.getByRole("heading", { name: "Synthetic browser case", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Event stream", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/factory-mobile.png", fullPage: true });
});


test("run selection distinguishes attempts and presents failed and superseded history", async ({ page }) => {
  const active = { ...structuredClone(initial), run_id: "current-attempt", title: "Repeated run title" };
  const diagnostic = JSON.stringify({ error: "Recorded input decoding failure." }), diagnosticId = digest(diagnostic);
  const revision = JSON.stringify({ reason: "Recorded measurement boundary changed; no candidate ran.", successor_run_id: active.run_id }), revisionId = digest(revision);
  const failed = { ...structuredClone(initial), run_id: "failed-attempt", title: active.title, status: "failed", artifacts: { [diagnosticId]: { path: "diagnostic.json", media_type: "application/json", hash_mode: "bytes" } }, events: [{ sequence: 0, elapsed_ms: 10, stage: "sources", payload: { kind: "source_imported", source: { snapshot_id: diagnosticId, provider: "Preparation diagnostic", description: "The initial preparation failed.", retrieved_at: "fixture", url: "urn:test:diagnostic" } } }] };
  const cancelled = { ...structuredClone(initial), run_id: "superseded-attempt", title: active.title, status: "cancelled", artifacts: { ...initial.artifacts, [revisionId]: { path: "revision.json", media_type: "application/json", hash_mode: "bytes" } }, events: [...initial.events, { sequence: 3, elapsed_ms: 300, stage: "sources", payload: { kind: "source_imported", source: { snapshot_id: revisionId, provider: "Measurement revision", description: "This attempt was superseded.", retrieved_at: "fixture", url: "urn:test:revision" } } }] };
  const runs = [ { ...initial, run_id: "authored-history", recording: { kind: "imported" }, status: "completed" }, failed, cancelled, active ];
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs } }));
  await page.route("**/replay.json", route => route.fulfill({ json: runs.find(run => route.request().url().includes("/" + run.run_id + "/")) }));
  const texts: Record<string, string> = { [sourceId]: sourceText, [caseId]: caseText, [diagnosticId]: diagnostic, [revisionId]: revision };
  await page.route("**/artifacts/*", route => route.fulfill({ contentType: "application/json", body: texts[route.request().url().split("/").pop()!] || "{}" }));
  await page.goto(url);
  await expect(page.locator("#run-select")).toHaveValue(active.run_id);
  await expect(page.locator("#run-select option[value=failed-attempt]")).toHaveText("failed · failed-attempt · Repeated run title");
  await page.locator("#run-select").selectOption(failed.run_id);
  await expect(page.getByText("Recorded input decoding failure.", { exact: true })).toBeVisible();
  await expect(page.locator(".case-panel")).toContainText("This recording ended without registering a case.");
  await expect(page.locator(".case-panel")).not.toContainText("Step forward");
  await page.locator("#run-select").selectOption(cancelled.run_id);
  await expect(page.getByText("Recorded measurement boundary changed; no candidate ran.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "current-attempt", exact: false }).click();
  await expect(page.locator("#run-select")).toHaveValue(active.run_id);
  await expect(page).toHaveURL(/run=current-attempt/);
});

test("inconclusive receipts expose their recorded reason without ability rows", async ({ page }) => {
  const receiptText = JSON.stringify({ result: "inconclusive", evaluations: [{ abilities: [], reasons: ["Source grammar did not qualify this card."], source_contract: { reasons: ["Additional unaccounted source paragraph."] } }] });
  const receiptId = digest(receiptText), replay = structuredClone(initial);
  replay.artifacts[receiptId] = { path: "inconclusive.json", media_type: "application/json", hash_mode: "bytes" };
  const payload = replay.events[2].payload as unknown as { feedback: { feedback_id: string; declared_strength: string; result: string } };
  payload.feedback.feedback_id = receiptId; payload.feedback.declared_strength = "strong"; payload.feedback.result = "inconclusive";
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs: [replay] } }));
  await page.route("**/replay.json", route => route.fulfill({ json: replay }));
  await page.route("**/artifacts/*", route => route.fulfill({ contentType: "application/json", body: route.request().url().endsWith(receiptId) ? receiptText : route.request().url().endsWith(sourceId) ? sourceText : caseText }));
  await page.goto(url);
  await expect(page.getByText("Source grammar did not qualify this card.", { exact: true })).toBeVisible();
  await expect(page.getByText("Additional unaccounted source paragraph.", { exact: true })).toBeVisible();
});

test("missing artifacts block portable export and can be retried after hydration", async ({ page }) => {
  const missingText = "Restored publisher source bytes.", missingId = digest(missingText);
  const replay = structuredClone(initial);
  replay.artifacts[missingId] = { path: "rules.txt", media_type: "text/plain", hash_mode: "bytes" };
  let hydrated = false;
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs: [replay] } }));
  await page.route("**/replay.json", route => route.fulfill({ json: replay }));
  await page.route("**/artifacts/*", route => {
    const id = route.request().url().split("/").pop();
    if (id === missingId) return route.fulfill({ status: hydrated ? 200 : 404, body: hydrated ? missingText : "Missing" });
    return route.fulfill({ body: id === sourceId ? sourceText : caseText });
  });
  const downloads: string[] = [];
  page.on("download", item => downloads.push(item.suggestedFilename()));
  await page.goto(url);
  await page.getByRole("heading", { name: initial.title, exact: true }).waitFor();
  await page.getByRole("button", { name: "Save portable", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Complete the replay before exporting", exact: true })).toBeVisible();
  expect(downloads).toEqual([]);
  await expect(page.locator(".artifact-recovery pre")).toContainText("scripts/share_factory_replay.py hydrate");
  await expect(page.getByRole("link", { name: "Hydration and portable export instructions" })).toHaveAttribute("href", /docs\/software-factory.md#share-a-run$/);
  hydrated = true;
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Retry portable export", exact: true }).click();
  expect((await download).suggestedFilename()).toBe(initial.run_id + ".portable.json");
  await expect(page.getByRole("status")).toContainText("Saved complete portable replay with 3 artifact contents.");
});

