import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { object, type FactoryEvent, type Fields } from "../model";
import { COMPARISON_SCHEMA, REPORT_SCHEMA, TRACE_SCHEMA, caseRecord, fittingArtifactIds, fittingContext, initialFittingSelection, momentKey, observationMoments, observationRows, selectedReport } from "./model";
import { renderFitting, renderFittingComparison, type FittingHelpers } from "./view";

const actual = (file: string): Fields => JSON.parse(readFileSync(new URL(`../../../../docs/artifacts/17lands-guided-fit-20260908/real-probes-01/game-11/${file}`, import.meta.url), "utf8"));
const constraints = actual("constraints.json"), result = actual("result.json");
const source = (id: string, sequence = 0, provider = "17Lands trajectory discovery report"): FactoryEvent => ({ sequence, elapsed_ms: null, stage: "sources", payload: { kind: "source_imported", source: { snapshot_id: id, provider } } });
const fixture = () => {
  const report: Fields = { schema: REPORT_SCHEMA, label: "baseline", build_id: "build", scope: { turn_pairs: 1, nodes: 10000, max_actions: 128 }, cases: [{ case_id: "game-11", source_row_index: 11, execution_id: "recorded-execution", constraints_id: "constraints", result_id: "result", feedback_id: "feedback", status: result.status, issue_ids: ["ability"] }], issues: [{ issue_id: "ability", kind: "unsupported_projection", component: "adapter", title: "Ability observation is unsupported", origins: [{ case_id: "game-11", source_row_index: 11, result_id: "result", source_columns: ["oppo_turn_1_user_abilities"], detail: "Recorded ability ID 88024 remains unsupported.", evidence: null }] }], summary: { cases: 1 } };
  const values: Record<string, Fields> = { report, constraints, result };
  const read = (id: unknown) => values[String(id)] ?? {};
  const h: FittingHelpers = { read, artifact: (id, title) => id ? `<button>${title}</button>` : "", integrity: () => "verified", caseTitle: id => id === "game-11" ? "Observed SOS game 11" : id };
  return { values, read, h };
};
describe("fitting reports remain tied to recorded events", () => {
  it("never exposes a cached future report when scrubbing before its source event", () => {
    const f = fixture();
    expect(fittingContext([], f.read).reports).toEqual([]);
    const context = fittingContext([source("report", 5)], f.read);
    expect(selectedReport(context, "game-11", "")?.id).toBe("report");
    expect(caseRecord(context.reports[0], "other")).toEqual({});
  });
  it("loads selected case evidence without hydrating every case in a cohort", () => {
    const f = fixture();
    f.values.report.cases = [...f.values.report.cases as Fields[], { case_id: "other", constraints_id: "other-constraints", result_id: "other-result", feedback_id: "other-feedback" }];
    const events = [source("report")], ids = fittingArtifactIds(events, fittingContext(events, f.read), "game-11");
    expect(ids).toEqual(["report", "constraints", "result", "feedback"]);
  });
  it("defaults to the recorded candidate when a comparison imports its older baseline", () => {
    const f = fixture();
    f.values.candidate = { ...f.values.report, label: "candidate" };
    f.values.comparison = { schema: COMPARISON_SCHEMA, baseline_report_id: "report", candidate_report_id: "candidate", assessment: "comparison_only", rows: [{ case_id: "game-11", before_status: "budget_exhausted", after_status: "matched_supported_projection" }] };
    const context = fittingContext([source("candidate", 5), source("comparison", 6)], f.read);
    expect(selectedReport(context, "game-11", "")?.id).toBe("candidate");
    expect(selectedReport(context, "game-11", "report")?.id).toBe("report");
    const before = fittingContext([source("candidate", 5)], f.read);
    expect(renderFittingComparison(before, "game-11", f.h)).toBe("");
    expect(renderFittingComparison(context, "game-11", f.h)).toContain("Acceptance, if any, is a separate factory decision");
  });
});
describe("actual retained first-turn receipts", () => {
  it("keeps the seven-versus-six counts at distinct owner boundaries and does not invent old trace values", () => {
    const keys = observationMoments(constraints).filter(k => k.observed_player === 1);
    const before = observationRows(constraints, result, keys[0]).find(r => r.projection === "hand_count")!;
    const after = observationRows(constraints, result, keys[1]).find(r => r.projection === "hand_count")!;
    expect([before.expected, after.expected]).toEqual([7, 6]);
    expect(before.actual).toBeUndefined(); expect(after.actual).toBeUndefined();
    expect(before.comparison).toBe("not_recorded");
    expect(after.comparison).toBe("not_recorded");
    expect(observationRows(constraints, result, { turn_owner: 1, turn_index: 1, boundary: "end_of_turn", observed_player: 0 }).find(r => r.raw === "88024")?.comparison).toBe("unsupported");
  });
  it("renders the real bounded result without relabeling unsupported fields or milestones", () => {
    const f = fixture(), html = renderFitting(fittingContext([source("report")], f.read), "game-11", initialFittingSelection(), f.h)!;
    expect(html).toContain("Supported projection matched");
    expect(html).toContain("<strong>0</strong><span>fully covered milestones");
    expect(html).toContain("older receipt did not record expected/actual trace comparisons");
    expect(html).toContain("Recorded ability ID 88024 remains unsupported");
    expect(html).toContain("30 retained witness actions");
    expect(html).not.toContain("Accepted");
  });
});
describe("trace rendering uses explicit measurements", () => {
  it("displays recorded comparisons instead of deriving a verdict from numbers", () => {
    const key = { turn_owner: 0, turn_index: 1, boundary: "end_of_turn", observed_player: 1 };
    const input = { fields: [{ column: "fixture-hand", raw: "7", milestone: key, disposition: "enforced", projection: "hand_count", expected: 7 }], milestones: [key] };
    const traceResult = { trace: { schema: TRACE_SCHEMA, milestones: [{ key, fields: [{ source_field_id: "fixture-hand", expected: 7, actual: 7, comparison: "mismatched" }] }] } };
    expect(observationRows(input, traceResult, key)[0]).toMatchObject({ actual: 7, comparison: "mismatched" });
    const m = object((traceResult.trace.milestones[0])); m.fields = [...m.fields as Fields[], object((m.fields as Fields[])[0])];
    expect(observationRows(input, traceResult, key)[0]).toMatchObject({ actual: undefined, comparison: "ambiguous_trace" });
  });
  it("keeps unknown-only source moments inspectable without counting them as fitted", () => {
    const key = { turn_owner: 1, turn_index: 1, boundary: "end_of_turn", observed_player: 0 };
    expect(observationMoments({ fields: [{ milestone: key, raw: "", disposition: "informational" }], milestones: [] })).toEqual([key]);
    expect(momentKey({ ...key, turn_owner: null })).toBe("");
    expect(momentKey({ ...key, observed_player: "0" })).toBe("");
  });
  it("shows absent or corrupt referenced evidence without treating it as an observation", () => {
    const f = fixture(); delete f.values.result;
    const html = renderFitting(fittingContext([source("report")], f.read), "game-11", initialFittingSelection(), f.h)!;
    expect(html).toContain("Fitter result unavailable");
    expect(html).toContain("Missing or corrupt bytes are not a result");
  });
  it("escapes hostile text and bounds issues and source display", () => {
    const f = fixture();
    f.values.report.issues = Array.from({ length: 62 }, () => ({ issue_id: "fixture", title: '<img src=x onerror="alert(1)">', component: "<script>", origins: [{ case_id: "game-11", source_columns: ["<svg>"], detail: "Hostile fixture" }] }));
    const html = renderFitting(fittingContext([source("report")], f.read), "game-11", initialFittingSelection(), f.h)!;
    expect(html).not.toContain("<img"); expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;img"); expect(html).toContain("Showing 60 of 62 issue groups");
  });
});


it("keeps native diagnostics unchecked and missing trace fields unrecorded", () => {
  const key = { turn_owner: 0, turn_index: 1, boundary: "end_of_turn", observed_player: 0 };
  const input: Fields = { fields: [{ column: "combat", raw: "0", milestone: key, disposition: "unsupported" }, { column: "hand", raw: "7", milestone: key, disposition: "enforced", expected: 7 }] };
  const measured = { trace: { schema: TRACE_SCHEMA, milestones: [{ key, fields: [{ source_field_id: "combat", actual: null, comparison: "unsupported", diagnostic: { metric: "native_combat_damage_received", value: 0, limitation: "Unchecked semantics" } }] }] } };
  const rows = observationRows(input, measured, key);
  expect(rows[0]).toMatchObject({ actual: null, comparison: "unsupported", diagnostic: { value: 0 } });
  expect(rows[1]).toMatchObject({ actual: undefined, comparison: "not_recorded" });
});
it("only visible typed repair attribution links the originating case and diagnosis", () => {
  const f = fixture();
  f.values.proposal = { schema: "coworld/17lands-repair-attribution@1", origin_case_ids: ["game-11"], origin_issue_ids: ["ability"], baseline_report_id: "report", diagnosis_id: "diagnosis", change_id: "patch", authority: "Operator-supplied diagnosis" };
  const context = fittingContext([source("proposal", 8, "17Lands trajectory repair attribution")], f.read);
  expect(context.reports[0].id).toBe("report");
  expect(fittingArtifactIds([source("proposal", 8, "17Lands trajectory repair attribution")], context, "game-11")).toContain("proposal");
  expect(renderFittingComparison(context, "game-11", f.h)).toContain("Ability observation is unsupported");
  expect(renderFittingComparison(context, "other", f.h)).toBe("");
  expect(renderFittingComparison(fittingContext([], f.read), "game-11", f.h)).toBe("");
});

it("does not relabel a nonblank informational zero as an unknown observation", () => {
  const key = { turn_owner: 0, turn_index: 1, boundary: "end_of_turn", observed_player: 0 };
  const input = { fields: [{ column: "known", raw: "0", milestone: key, disposition: "informational" }, { column: "blank", raw: "", milestone: key, disposition: "informational" }] };
  expect(observationRows(input, {}, key).map(row => row.comparison)).toEqual(["informational", "unknown"]);
});
