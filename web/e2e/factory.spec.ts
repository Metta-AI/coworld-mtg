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


test("run planning context is visible before a case has a patch", async ({ page }) => {
  const planning = { ...structuredClone(initial), events: [...initial.events, { sequence: 3, elapsed_ms: 300, stage: "sources", payload: { kind: "source_imported", source: { snapshot_id: sourceId, provider: "Synthetic planning record", description: "A partial candidate is planned; implementation has not started.", retrieved_at: "test fixture", url: "urn:test:plan" } } }] };
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs: [planning] } }));
  await page.route("**/replay.json", route => route.fulfill({ json: planning }));
  await page.route("**/artifacts/*", route => route.fulfill({ body: route.request().url().endsWith(sourceId) ? sourceText : caseText }));
  await page.goto(url);
  await page.getByRole("tab", { name: "Changes & decision" }).click();
  await expect(page.locator(".change-context")).toContainText("A partial candidate is planned; implementation has not started.");
  await expect(page.locator(".change-context")).toContainText("This is a run-level record.");
  await expect(page.getByRole("heading", { name: "No patch proposed for this case", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Inspect planning & run history" }).click();
  await expect(page.getByRole("dialog")).toContainText("A partial candidate is planned; implementation has not started.");
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("button", { name: "Previous event", exact: true }).click();
  await expect(page.locator(".change-context")).not.toContainText("A partial candidate is planned");
});

test("a satisfied candidate case retains its recorded rejection beside the before and after evidence", async ({ page }) => {
  // Exact reason retained by real Scryfall decision 11bd1d52f3d2dd823d3e72194beb7bf735fcc6d8c1cb455cec33c1ab9e6f00cb.
  // The surrounding replay stays an explicit UI fixture; this string reproduces its mobile overflow.
  const recordedReason = "Frozen acceptance requirements were not satisfied: frozen acceptance requirements failed: ['7d91f1fd538d1c634aef57b68fd7c32669b02af543380bb6b82da32417b6919e', '69007946c529eb39476a5dc5ed0944ad39af8ed5debcedc35ea95a4582ad28c8']";
  const patch = "Synthetic test patch only", patchId = digest(patch), decisionId = "d".repeat(64), planId = "e".repeat(64);
  const observation = (isMana: boolean) => JSON.stringify({ observation: { parsed: { abilities: [{ kind: "Activated", is_mana_ability: isMana, description: "Synthetic classification observation", effect: { type: "Synthetic" } }] } } });
  const before = observation(true), after = observation(false), beforeId = digest(before), afterId = digest(after);
  const texts: Record<string, string> = { [sourceId]: sourceText, [caseId]: caseText, [patchId]: patch, [beforeId]: before, [afterId]: after };
  const artifacts = Object.fromEntries(Object.entries(texts).map(([id]) => [id, { path: id + ".json", media_type: "application/json", hash_mode: "bytes" }]));
  const events: object[] = [...initial.events];
  const append = (payload: object) => events.push({ sequence: events.length, elapsed_ms: events.length * 100, stage: "feedback", payload });
  append({ kind: "acceptance_plan_frozen", plan_id: planId, plan: { case_id: caseId, regression_case_ids: [], holdout_case_ids: [] } });
  append({ kind: "change_proposed", change_id: patchId, description: "Synthetic partial change", base_revision: "synthetic-revision", motivating_feedback_ids: [feedbackId] });
  append({ kind: "execution_started", execution_id: "test-baseline", case_id: caseId, request_id: caseId, build_id: caseId, change_id: null });
  append({ kind: "execution_finished", execution_id: "test-baseline", status: "completed", evidence_id: beforeId, trace_ids: [], detail: null });
  append({ kind: "execution_started", execution_id: "test-candidate", case_id: caseId, request_id: caseId, build_id: caseId, change_id: patchId });
  append({ kind: "execution_finished", execution_id: "test-candidate", status: "completed", evidence_id: afterId, trace_ids: [], detail: null });
  append({ kind: "feedback_recorded", feedback: { feedback_id: "a".repeat(64), case_id: caseId, execution_ids: ["test-candidate"], evaluator: "test evaluator", evaluator_version: "test-only", adapter: "opaque", declared_strength: "strong", method: "Synthetic assertion", bounded_claim: "Only this synthetic check passed.", result: "satisfied", summary: "Synthetic candidate check is satisfied" } });
  append({ kind: "decision_recorded", change_id: patchId, plan_id: planId, decision_id: decisionId, policy: { kind: "external", scope: "Synthetic frozen checks" }, decision: { kind: "rejected", reasons: [recordedReason] } });
  const rejected = { ...structuredClone(initial), artifacts, events };
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs: [rejected] } }));
  await page.route("**/replay.json", route => route.fulfill({ json: rejected }));
  await page.route("**/artifacts/*", route => route.fulfill({ body: texts[route.request().url().split("/").pop()!] || "{}" }));
  await page.goto(url);
  await expect(page.getByText("Synthetic candidate check is satisfied", { exact: true })).toBeVisible();
  const comparison = page.locator(".comparison-grid");
  await expect(comparison.getByText("mana ability: yes", { exact: true })).toBeVisible();
  await expect(comparison.getByText("mana ability: no", { exact: true })).toBeVisible();
  await expect(comparison.getByText("Recorded decision: rejected", { exact: true })).toBeVisible();
  await expect(comparison).toContainText(recordedReason);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("tab", { name: "Changes & decision" }).click();
  await expect(page.locator(".decision-card")).toContainText(recordedReason);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("tab", { name: "Evidence", exact: true }).click();
  await expect(comparison).not.toContainText("accepted");
  await page.getByRole("button", { name: "Previous event", exact: true }).click();
  await expect(comparison).toContainText("No decision recorded for this change at this point.");
  await expect(comparison).not.toContainText("Recorded decision: rejected");
});

test("tagged source-ingestion results stay distinct from evaluator claims and Scryfall cards", async ({ page }) => {
  const csv = "game,casts\n1,111\n2,222\n", csvId = digest(csv);
  const output = JSON.stringify({ observation: { schema: "software-factory-result-v1", summary: "Synthetic miner output, not a full game replay.", data: { rows: 2, card_frequency: [] } } });
  const outputId = digest(output);
  const evaluation = JSON.stringify({ schema: "software-factory-result-v1", summary: "Synthetic extraction measurements", data: { expected_casts: 2, observed_casts: 0, evaluated_rows: [{ row: 1, column: "synthetic_turn_1_casts", observed_casts: 0 }, { row: 2, column: "synthetic_turn_2_casts", observed_casts: 0 }], unobserved_state: ["targets", "priority", "hidden cards"] } });
  const evaluationId = digest(evaluation);
  const replay = {
    ...structuredClone(initial),
    artifacts: {
      [csvId]: { path: "source.csv", media_type: "text/csv", hash_mode: "bytes" },
      [caseId]: initial.artifacts[caseId],
      [outputId]: { path: "output.json", media_type: "application/json", hash_mode: "bytes" },
      [evaluationId]: { path: "coverage.json", media_type: "application/json", hash_mode: "bytes" },
    },
    events: [
      { sequence: 0, elapsed_ms: 0, stage: "sources", payload: { kind: "source_imported", source: { snapshot_id: csvId, provider: "Synthetic partial source", url: "https://example.test/data.csv", retrieved_at: "test fixture", description: "Synthetic per-turn summary fixture; not a full ordered action replay." } } },
      { sequence: 1, elapsed_ms: 100, stage: "cases", payload: { kind: "case_registered", case_id: caseId, title: "Synthetic source ingestion case", derivation: { kind: "source_derived", source_ids: [csvId], source_records: [{ source_id: csvId, record_id: "data-rows:1-2" }], recipe: "Test-only source extraction", seed: null } } },
      { sequence: 2, elapsed_ms: 200, stage: "feedback", payload: { kind: "execution_started", execution_id: "test-miner", case_id: caseId, request_id: caseId, build_id: caseId, change_id: null } },
      { sequence: 3, elapsed_ms: 300, stage: "feedback", payload: { kind: "execution_finished", execution_id: "test-miner", status: "completed", evidence_id: outputId, trace_ids: [], detail: "Synthetic native measurement" } },
      { sequence: 4, elapsed_ms: 400, stage: "feedback", payload: { kind: "feedback_recorded", feedback: { feedback_id: evaluationId, case_id: caseId, execution_ids: ["test-miner"], evaluator: "synthetic extraction evaluator", evaluator_version: "test-only", adapter: "opaque", declared_strength: "strong", method: "Test fixture comparison", bounded_claim: "Extraction coverage only; no gameplay correctness claim.", result: "violated", summary: "Synthetic evaluator recorded missing casts" } } },
    ],
  };
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs: [] } }));
  await page.goto(url);
  await page.locator("#replay-file").setInputFiles({ name: "synthetic-ingestion.portable.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify({ replay, artifact_contents: { [csvId]: csv, [caseId]: caseText, [outputId]: output, [evaluationId]: evaluation } })) });
  await expect(page.getByRole("heading", { name: "Synthetic source ingestion case", exact: true })).toBeVisible();
  await expect(page.locator(".feedback-card")).toContainText("violated");
  await expect(page.locator(".feedback-card")).toContainText("observed casts");
  await expect(page.locator(".execution-column").first()).toContainText("0 recorded rows (empty array)");
  await expect(page.locator(".execution-column").first()).toContainText("not a full game replay");
  await expect(page.locator(".feedback-card")).toContainText("synthetic_turn_2_casts");
  await page.screenshot({ path: "test-results/factory-generic-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/factory-generic-mobile.png", fullPage: true });
  await page.getByRole("tab", { name: "Source & lineage" }).click();
  await expect(page.locator("#case-content")).toContainText("Recorded source selector");
  await expect(page.locator("#case-content")).toContainText("data-rows:1-2");
  await expect(page.locator("#case-content")).not.toContainText("Raw Scryfall record");
  await expect(page.locator("#case-content")).not.toContainText("No Oracle text");
  await page.getByRole("tab", { name: "Changes & decision" }).click();
  await expect(page.getByText("No decision recorded at this point", { exact: true })).toBeVisible();
});
