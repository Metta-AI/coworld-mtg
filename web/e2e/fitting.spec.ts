import { test, expect, type Page } from "@playwright/test";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";

test.use({ launchOptions: { args: ["--js-flags=--max-old-space-size=2048"] } });

// This wrapper is UI test data around retained real receipts, never an actual factory run.
const url = process.env.FACTORY_VIEWER_URL || "http://127.0.0.1:4199/client/factory.html";
const receipt = (file: string) => JSON.parse(readFileSync(new URL(`../../docs/artifacts/17lands-guided-fit-20260908/real-probes-01/game-11/${file}`, import.meta.url), "utf8"));
const digest = (text: string) => createHash("sha256").update(text).digest("hex");
function fixture(withTrace = false) {
  const contents: Record<string, string> = {}, artifacts: Record<string, object> = {};
  const put = (value: unknown) => { const text = JSON.stringify(value), id = digest(text); contents[id] = text; artifacts[id] = { path: id + ".json", media_type: "application/json", hash_mode: "bytes" }; return id; };
  const constraints = receipt("constraints.json"), result = receipt("result.json");
  const caseId = put({ title: "UI wrapper · retained SOS game 11" });
  const field = constraints.fields.find((f: any) => f.projection === "hand_count" && f.milestone?.turn_owner === 0);
  if (withTrace) {
    const state = { turn_owner: 0, turn_number: 1, phase: "Main", stack_count: 0, players: [{ seat: 0, life: 20, hand: [{ object_id: 1, name: "Fixture Plains" }], battlefield: [], library_count: 40, graveyard_count: 0 }, { seat: 1, life: 20, hand: [], battlefield: [], library_count: 40, graveyard_count: 0 }] };
    result.trace = { schema: "coworld-17lands-fit-trace-v1", path_kind: "complete_witness", initial_state: state,
      transitions: [{ index: 0, seat: 0, action: { type: "PlayLand", data: { object_id: 1 } }, before: state, after: { ...state, players: [{ ...state.players[0], hand: [], battlefield: [{ object_id: 1, name: "Fixture Plains" }] }, state.players[1]] }, events: [] }],
      milestones: [{ key: field.milestone, transition_index: 0, state_position: "before_transition", fields: [{ source_field_id: field.column, raw: field.raw, disposition: field.disposition, projection: field.projection, expected: field.expected, actual: field.expected, comparison: "mismatched" }] }],
      failure: { path_kind: "separate_search_branch", kind: "offered_action_failure", detail: "UI fixture only: an offered action was rejected.", actions_before: [], attempted_action: { seat: 0, action: { type: "PassPriority" } }, attempt: null, state, milestones: [] } };
    const diagnosticField = constraints.fields.find((f: any) => f.milestone?.turn_owner === 0 && f.milestone?.observed_player === 1 && f.disposition === "unsupported");
    result.trace.milestones[0].fields.push({ source_field_id: diagnosticField.column, actual: null, comparison: "unsupported", diagnostic: { metric: "native_combat_damage_received", value: 0, limitation: "UI diagnostic fixture. Source semantics are unchecked." } });
  }
  const constraintsId = put(constraints), resultId = put(result);
  const issue = { issue_id: "ui-issue", kind: "unsupported_projection", component: "observation_adapter", title: "UI issue wrapper: ability observation remains unsupported", origins: [{ case_id: caseId, source_row_index: 11, execution_id: "ui-execution", result_id: resultId, source_columns: ["oppo_turn_1_user_abilities"], detail: "The real retained result does not check ability ID 88024.", evidence: null }] };
  const reportId = put({ schema: "coworld/17lands-discovery-report@1", cohort_id: "ui-cohort", label: "baseline", build_id: "ui-build", complete: true, scope: { turn_pairs: 1, nodes: 10000, max_actions: 128, deadline_seconds: 30, memory_bytes: 1073741824 }, cases: [{ case_id: caseId, title: "UI wrapper · retained SOS game 11", source_row_index: 11, execution_id: "ui-execution", constraints_id: constraintsId, result_id: resultId, status: result.status, issue_ids: [issue.issue_id] }], issues: [issue], summary: { cases: 1, planned_cases: 1 } });
  const replay = { version: "software-factory-v1", run_id: "fitting-ui-fixture", title: withTrace ? "Explicit UI trace fixture" : "UI wrapper around retained old receipt", target: { name: "Fitting UI test", baseline_revision: "fixture", repository: "https://example.test" }, recording: { kind: "imported", description: "UI fixture wrapper" }, status: "completed", artifacts, stages: [{ id: "cases", title: "Cases", next: ["sources"] }, { id: "sources", title: "Reports", next: [] }], events: [
    { sequence: 0, elapsed_ms: null, stage: "cases", payload: { kind: "case_registered", case_id: caseId, title: "UI wrapper · retained SOS game 11", derivation: { kind: "authored", author: "UI test", description: "Testing wrapper only" } } },
    { sequence: 1, elapsed_ms: null, stage: "sources", payload: { kind: "source_imported", source: { snapshot_id: reportId, provider: "17Lands trajectory discovery report", url: "urn:ui-fixture", description: "UI wrapper, not an actual run", retrieved_at: "fixture" } } },
  ] };
  return { replay, contents, reportId, resultId, field, put, caseId };
}
async function mount(page: Page, data: ReturnType<typeof fixture>, corrupt = "") {
  await page.route("**/factory-api/runs", route => route.fulfill({ json: { runs: [data.replay] } }));
  await page.route("**/replay.json", route => route.fulfill({ json: data.replay }));
  await page.route("**/artifacts/*", route => { const id = route.request().url().split("/").pop()!; return route.fulfill({ contentType: "application/json", body: id === corrupt ? "{}" : data.contents[id] || "{}" }); });
  await page.goto(url);
}
test("older real receipts show source chronology without invented engine measurements", async ({ page }) => {
  const data = fixture(); await mount(page, data);
  await expect(page.locator(".fit-head h3")).toHaveText("Supported projection matched");
  await expect(page.locator(".pipeline-section")).toBeHidden();
  await expect(page.locator(".timeline-panel")).toBeHidden();
  await page.getByRole("button", { name: "Show run structure", exact: true }).click();
  await expect(page.locator(".pipeline-section")).toBeVisible();
  await page.getByRole("button", { name: "Hide run structure", exact: true }).click();
  await expect(page.locator(".pipeline-section")).toBeHidden();
  await expect(page.locator(".fit-stats")).toContainText("0fully covered milestones");
  await expect(page.locator(".fit-trace-note").first()).toContainText("older receipt");
  await page.locator("#fit-moment-select").selectOption("1");
  await expect(page.locator(".fit-observation-table tbody tr").filter({ hasText: "Cards in hand (count)" })).toContainText("7Not recordednot recorded");
  await page.locator("#fit-moment-select").selectOption("3");
  await expect(page.locator(".fit-observation-table tbody tr").filter({ hasText: "Cards in hand (count)" })).toContainText("6Not recordednot recorded");
  await page.getByRole("button", { name: "Previous event", exact: true }).click();
  await expect(page.locator(".fitting-view")).toHaveCount(0);
  await page.getByRole("button", { name: "Next event", exact: true }).click();
  await expect(page.locator(".fitting-view")).toBeVisible();
});
test("typed trace separates comparisons, unchecked diagnostics, and failed branch actions", async ({ page }) => {
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  await mount(page, fixture(true));
  await expect(page.locator(".fit-head h3")).toHaveText("Supported projection matched");
  await page.locator("#fit-moment-select").selectOption("1");
  await expect(page.locator(".fit-pill.mismatched")).toHaveText("mismatched");
  await expect(page.locator(".fit-diagnostic")).toContainText("Unchecked native diagnostic");
  await expect(page.locator(".fit-diagnostic").locator("..")).toContainText("Not recorded");
  await expect(page.locator(".fit-diagnostic").locator("../..")).toContainText("unsupported");
  await expect(page.locator("#fit-transition-select")).toContainText("Play Land · Fixture Plains");
  await expect(page.locator(".fit-state-grid")).toContainText("Before action");
  await expect(page.locator(".fit-failure")).toContainText("Attempt: Pass Priority");
  await expect(page.locator(".fit-failure")).toContainText("separate search branch");
  await page.locator(".fit-issue > summary").click();
  await expect(page.locator(".fit-issue")).toContainText("88024");
  expect(errors).toEqual([]);
  await page.screenshot({ path: "test-results/fitting-trace-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/fitting-trace-mobile.png", fullPage: true });
});
test("corrupt report bytes never introduce a discovery view", async ({ page }) => {
  const data = fixture(); await mount(page, data, data.reportId);
  await expect(page.getByRole("heading", { name: data.replay.title, exact: true })).toBeVisible();
  await expect(page.locator(".fitting-view")).toHaveCount(0);
  await page.getByRole("button", { name: "Run history", exact: false }).click();
  await page.locator("dialog [data-artifact]").click();
  await expect(page.locator("dialog")).toContainText("SHA-256 does not match");
});
test("actual live discovery reports and old receipts render without claim inflation", async ({ page, request }, testInfo) => {
  const run = process.env.FITTING_LIVE_RUN;
  test.skip(!run, "Explicit real live run required; this is not a synthetic replay assertion.");
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  let replayBytes = Buffer.from(""), artifactReads = new Set<string>();
  await page.route("**/factory-api/**", async route => {
    const u = new URL(route.request().url()), response = await request.get("http://127.0.0.1:8030" + u.pathname);
    const body = await response.body();
    if (u.pathname.endsWith("/replay.json")) replayBytes = Buffer.from(body);
    if (u.pathname.includes("/artifacts/")) artifactReads.add(u.pathname.split("/").pop()!);
    await route.fulfill({ status: response.status(), contentType: response.headers()["content-type"], body });
  });
  await page.goto(url + "?run=" + encodeURIComponent(run!));
  await expect(page.locator(".fitting-view")).toBeVisible();
  await expect(page.locator(".fit-head h3")).toHaveText("Input needs attention");
  await expect(page.locator(".fit-stop")).toBeVisible();
  await expect(page.locator(".fit-scope")).toContainText("not a complete game reconstruction");
  await expect(page.locator(".fit-provenance")).toContainText("verified");
  await expect(page.locator(".fit-issues")).toContainText("observation adapter");
  const matched = page.locator(".case-row").filter({ hasText: "Supported projection matched" }).first();
  await matched.click();
  await expect(page.locator(".fit-head h3")).toHaveText("Supported projection matched");
  await expect(page.locator(".fit-stats")).toContainText("0fully covered milestones");
  await expect(page.locator(".fit-trace-note").first()).toContainText("older receipt");
  await page.screenshot({ path: "test-results/fitting-real-baseline-desktop.png", fullPage: true });
  await page.locator(".fit-observations").evaluate(element => element.scrollIntoView({ block: "start" }));
  await page.screenshot({ path: "test-results/fitting-real-observations-desktop.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/fitting-real-baseline-mobile.png", fullPage: true });
  expect(errors).toEqual([]);
  const replay = JSON.parse(replayBytes.toString());
  const row8 = replay.events.find((e: any) => e.payload.kind === "case_registered" && e.payload.title === "17Lands source row 8")?.payload.case_id;
  expect(row8).toBeTruthy();
  const reportId = replay.events.filter((e: any) => e.payload.kind === "source_imported" && e.payload.source.provider === "17Lands trajectory discovery report").at(-1).payload.source.snapshot_id;
  await page.goto(url + "?run=" + encodeURIComponent(run!) + "&case=" + row8 + "&report=" + reportId);
  await expect(page.locator(".case-heading h2")).toHaveText("17Lands source row 8");
  await expect(page.locator(".fit-head h3")).toHaveText("Turn boundary unsupported");
  await expect(page.locator("#fit-report-select")).toHaveValue(reportId);
  await page.getByRole("button", { name: "Follow latest", exact: false }).click();
  await expect(page.locator(".case-heading h2")).toHaveText("17Lands source row 8");
  await page.getByRole("button", { name: "Previous event", exact: true }).click();
  await page.getByRole("button", { name: "Next event", exact: true }).click();
  await expect(page.locator(".case-heading h2")).toHaveText("17Lands source row 8");
  await page.setViewportSize({ width: 1280, height: 720 });
  expect((await page.locator("#case-content").boundingBox())!.height).toBeGreaterThan(330);
  await page.screenshot({ path: "test-results/fitting-real-row8-desktop.png", fullPage: true });
  writeFileSync(testInfo.outputPath("actual-live-browser-evidence.json"), JSON.stringify({ run_id: run, replay_sha256: digest(replayBytes.toString()), events: replay.events.length, artifacts: Object.keys(replay.artifacts).length, report_ids: replay.events.filter((e: any) => e.payload.kind === "source_imported" && e.payload.source.provider === "17Lands trajectory discovery report").map((e: any) => e.payload.source.snapshot_id), selected_case: await page.locator(".case-heading h2").innerText(), checked: ["actual input issue and recorded stop reason", "actual supported match with zero fully covered milestones", "old receipt engine values not reconstructed", "desktop and mobile render", "no mobile page overflow", "no JavaScript errors", "real row 8 unsupported boundary deep link", "case and report selection retained through live fetch and scrub"], artifact_reads: [...artifactReads], js_errors: errors }, null, 2));
});


test("actual comparison field shape wraps on mobile without claiming changed scope or a repair", async ({ page }) => {
  const data = fixture();
  // Exact source-field shape from comparison 188bb412b86a7d6a0900ecb044c1c43575ec6beb533ead14dbdcb4930ed072ee.
  // The wrapper remains UI fixture data, not an additional factory measurement.
  const before = { column: "oppo_turn_1_oppo_combat_damage_taken", disposition: "unsupported", expected: null, milestone: { boundary: "end_of_turn", observed_player: 1, turn_index: 1, turn_owner: 1 }, projection: null, raw: "0", reason: "no implemented projection for this recorded field; ability IDs are not card IDs" };
  const after = { ...before, reason: "source aggregation is unverified: retained combat_damage_taken values can be negative, so a raw native combat-damage event total is not an established equivalent" };
  const id = data.put({ schema: "coworld/17lands-discovery-comparison@1", baseline_report_id: data.reportId, candidate_report_id: data.reportId, assessment: "comparison_only", origin_issue_ids: [], rows: [{ case_id: data.caseId, before_status: "matched_supported_projection", after_status: "matched_supported_projection", resolved_issue_ids: [], remaining_issue_ids: ["ui-issue"], new_issue_ids: [] }], scope_changes: [{ case_id: data.caseId, kind: "observation_changed", column: before.column, before, after }], limitations: [] });
  data.replay.events.push({ sequence: 2, elapsed_ms: null, stage: "sources", payload: { kind: "source_imported", source: { snapshot_id: id, provider: "17Lands trajectory discovery comparison", url: "urn:ui-fixture", description: "UI comparison fixture", retrieved_at: "fixture" } } });
  await page.setViewportSize({ width: 390, height: 844 });
  await mount(page, data);
  await expect(page.getByRole("heading", { name: "Recorded before / after comparison" })).toBeVisible();
  await expect(page.locator(".fit-repair")).toContainText("Changed constraint records");
  await expect(page.locator(".fit-repair")).toContainText("Diagnostic signatures no longer reported");
  await expect(page.locator(".fit-repair .fit-scope p").first()).toHaveText("Before: " + JSON.stringify(before));
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("tab", { name: "Changes & decision" }).click();
  await expect(page.locator(".fit-repair")).toContainText(after.reason);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
