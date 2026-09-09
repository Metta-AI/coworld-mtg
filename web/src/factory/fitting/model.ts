import { array, object, string, type FactoryEvent, type Fields } from "../model";

export const REPORT_SCHEMA = "coworld/17lands-discovery-report@1";
export const COMPARISON_SCHEMA = "coworld/17lands-discovery-comparison@1";
export const ATTRIBUTION_SCHEMA = "coworld/17lands-repair-attribution@1";
export const TRACE_SCHEMA = "coworld-17lands-fit-trace-v1";
export type ReadArtifact = (id: unknown) => Fields;
export interface LocatedRecord { id: string; sequence: number; value: Fields }
export interface FittingContext { reports: LocatedRecord[]; comparisons: LocatedRecord[]; attributions: LocatedRecord[] }
export interface FittingSelection { reportId: string; moment: number; transition: number; allFields: boolean }
export const initialFittingSelection = (): FittingSelection => ({ reportId: "", moment: -1, transition: -1, allFields: true });
export const records = (value: unknown): Fields[] => array(value).filter(v => v !== null && typeof v === "object" && !Array.isArray(v)).map(object);
export const count = (value: unknown): number | null => typeof value === "number" && Number.isSafeInteger(value) && value >= 0 ? value : null;
export const isFittingRecord = (value: Fields) => [REPORT_SCHEMA, COMPARISON_SCHEMA, ATTRIBUTION_SCHEMA].includes(string(value.schema));

// Only a visible source event introduces a report. Cached future artifacts cannot rewrite history.
export function fittingContext(events: FactoryEvent[], read: ReadArtifact): FittingContext {
  const introduced = events.filter(e => e.payload.kind === "source_imported").map(e => {
    const id = string(object(e.payload.source).snapshot_id);
    return { id, sequence: e.sequence, value: read(id) };
  });
  const reports = introduced.filter(r => r.value.schema === REPORT_SCHEMA && Array.isArray(r.value.cases) && Array.isArray(r.value.issues));
  const comparisons = introduced.filter(r => r.value.schema === COMPARISON_SCHEMA && Array.isArray(r.value.rows));
  const attributions = introduced.filter(r => r.value.schema === ATTRIBUTION_SCHEMA && Array.isArray(r.value.origin_case_ids));
  // A visible comparison can retain an earlier report from another run as an explicit input.
  for (const comparison of [...comparisons, ...attributions]) for (const key of ["baseline_report_id", "candidate_report_id"]) {
    const id = string(comparison.value[key]), value = read(id);
    if (id && !reports.some(r => r.id === id) && value.schema === REPORT_SCHEMA && Array.isArray(value.cases) && Array.isArray(value.issues)) reports.push({ id, sequence: comparison.sequence, value });
  }
  return { reports, comparisons, attributions };
}
export function reportCases(report: LocatedRecord): Fields[] { return records(report.value.cases); }
export function caseReports(context: FittingContext, caseId: string): LocatedRecord[] {
  return context.reports.filter(r => reportCases(r).some(c => c.case_id === caseId));
}
export function selectedReport(context: FittingContext, caseId: string, selectedId: string): LocatedRecord | undefined {
  const choices = caseReports(context, caseId);
  const explicit = choices.find(r => r.id === selectedId);
  if (explicit) return explicit;
  const comparison = context.comparisons.filter(c => records(c.value.rows).some(r => r.case_id === caseId)).at(-1);
  const compared = comparison && choices.find(r => r.id === comparison.value.candidate_report_id);
  return compared && comparison.sequence >= Math.max(...choices.map(r => r.sequence)) ? compared : choices.at(-1);
}
export function caseRecord(report: LocatedRecord, caseId: string): Fields { return reportCases(report).find(c => c.case_id === caseId) ?? {}; }
export function fittingStatus(status: unknown): string {
  const labels: Record<string, string> = {
    matched_supported_projection: "Supported projection matched", budget_exhausted: "Search budget exhausted",
    unsupported_boundary: "Turn boundary unsupported", no_witness_under_assumptions: "No witness under these assumptions",
    input_issue: "Input needs attention", timeout: "Worker timed out", timed_out: "Worker timed out",
    worker_execution: "Worker returned no fitting result", error: "Execution error", cancelled: "Execution cancelled", running: "Execution running",
  };
  return labels[string(status)] ?? (string(status).replaceAll("_", " ") || "Result not recorded");
}
export function momentKey(value: unknown): string {
  const k = object(value);
  if (!(k.turn_owner === 0 || k.turn_owner === 1) || !(k.observed_player === 0 || k.observed_player === 1) || !count(k.turn_index)) return "";
  return [k.turn_owner, k.turn_index, k.boundary, k.observed_player].join(":");
}
export function momentTitle(value: unknown): string {
  const k = object(value);
  if (!momentKey(k)) return "Unspecified observation moment";
  return `${k.turn_owner === 0 ? "User" : "Opponent"} turn ${k.turn_index} · ${k.boundary === "end_of_turn" ? "end of turn" : string(k.boundary).replaceAll("_", " ")} · observe ${k.observed_player === 0 ? "user" : "opponent"}`;
}
export function observationMoments(constraints: Fields): Fields[] {
  const found = new Map<string, Fields>();
  for (const field of records(constraints.fields)) if (momentKey(field.milestone)) found.set(momentKey(field.milestone), object(field.milestone));
  for (const key of records(constraints.milestones)) if (momentKey(key)) found.set(momentKey(key), key);
  const starter = constraints.on_play === false ? 1 : 0;
  return [...found.values()].sort((a, b) => (Number(a.turn_index) - Number(b.turn_index)) * 4 + (Number(a.turn_owner !== starter) - Number(b.turn_owner !== starter)) * 2 + Number(a.observed_player) - Number(b.observed_player));
}
export function supportedTrace(result: Fields): Fields | null { const trace = object(result.trace); return trace.schema === TRACE_SCHEMA ? trace : null; }
export interface ObservationRow { column: string; raw: string; disposition: string; projection: string; expected: unknown; actual: unknown; comparison: string; reason: string; diagnostic: Fields }
export function observationRows(constraints: Fields, result: Fields, key: unknown): ObservationRow[] {
  const wanted = momentKey(key);
  if (!wanted) return [];
  const trace = supportedTrace(result);
  const milestone = records(trace?.milestones).find(m => momentKey(m.key) === wanted);
  const measured = records(milestone?.fields);
  return records(constraints.fields).filter(f => momentKey(f.milestone) === wanted).map(field => {
    // Duplicate field IDs are ambiguous evidence, never a first-match measurement.
    const matches = measured.filter(m => m.source_field_id === field.column);
    const measurement = matches.length === 1 ? matches[0] : null;
    return {
      column: string(field.column), raw: string(field.raw), disposition: string(field.disposition), projection: string(field.projection),
      expected: field.expected, actual: measurement ? measurement.actual : undefined,
      comparison: matches.length > 1 ? "ambiguous_trace" : measurement ? string(measurement.comparison) || "not_recorded" : field.disposition === "unsupported" ? "unsupported" : field.disposition === "informational" ? (field.raw === "" || field.raw === null ? "unknown" : "informational") : "not_recorded",
      reason: string(field.reason), diagnostic: object(measurement?.diagnostic),
    };
  });
}
export function fittingArtifactIds(events: FactoryEvent[], context: FittingContext, caseId: string): string[] {
  const ids = new Set<string>();
  for (const event of events) if (event.payload.kind === "source_imported") {
    const source = object(event.payload.source);
    if (string(source.provider).startsWith("17Lands trajectory discovery") || string(source.provider) === "17Lands trajectory repair attribution") ids.add(string(source.snapshot_id));
  }
  for (const comparison of [...context.comparisons, ...context.attributions]) for (const key of ["baseline_report_id", "candidate_report_id"]) ids.add(string(comparison.value[key]));
  for (const report of caseReports(context, caseId)) {
    const item = caseRecord(report, caseId);
    for (const key of ["constraints_id", "result_id", "feedback_id"]) ids.add(string(item[key]));
  }
  return [...ids].filter(Boolean);
}
