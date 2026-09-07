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
  await expect(page.getByRole("heading", { name: "No case recorded at this point" })).toBeVisible();
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
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Save portable", exact: true }).click();
  expect((await download).suggestedFilename()).toBe(initial.run_id + ".portable.json");
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

