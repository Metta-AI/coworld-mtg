export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export type Fields = { [key: string]: Json };
export interface Artifact { path: string; media_type: string; hash_mode: "canonical_json" | "bytes" }
export interface Stage { id: string; title: string; next: string[] }
export interface FactoryEvent { sequence: number; elapsed_ms: number | null; stage: string; payload: Fields & { kind: string } }
export interface Replay {
  version: "software-factory-v1";
  run_id: string;
  title: string;
  target: { name: string; repository: string; baseline_revision: string };
  recording: { kind: "live" | "imported"; description?: string };
  status: "running" | "completed" | "failed" | "cancelled";
  stages: Stage[];
  artifacts: Record<string, Artifact>;
  events: FactoryEvent[];
}
export interface ReplayFile { replay: Replay; artifact_contents: Record<string, string> }
export interface CaseView { id: string; title: string; event: FactoryEvent; feedback: FactoryEvent[]; events: FactoryEvent[] }
export interface ArtifactState {
  status: "loading" | "verified" | "mismatch" | "missing" | "unverified";
  text?: string;
  value?: Json;
  detail?: string;
}

export const object = (value: unknown): Fields =>
  value !== null && typeof value === "object" && !Array.isArray(value) ? value as Fields : {};
export const string = (value: unknown): string => typeof value === "string" ? value : "";
export const array = (value: unknown): Json[] => Array.isArray(value) ? value as Json[] : [];
export const label = (value: unknown): string => string(value).replaceAll("_", " ");
export const short = (value: unknown): string => string(value).length > 18 ? string(value).slice(0, 10) + "…" : string(value);
export const isHash = (value: unknown): value is string => typeof value === "string" && /^[a-f0-9]{64}$/.test(value);
const kinds = new Set(["source_imported", "case_registered", "build_recorded", "execution_started", "execution_finished", "feedback_recorded", "change_proposed", "acceptance_plan_frozen", "review_recorded", "decision_recorded", "compute_recorded"]);

export function parseReplay(input: unknown): ReplayFile {
  const container = object(input);
  const value = object(container.replay ?? input);
  if (value.version !== "software-factory-v1") throw new Error("Unsupported replay version. Expected software-factory-v1.");
  if (!string(value.run_id) || !string(value.title)) throw new Error("Replay must identify its run and title.");
  if (!Array.isArray(value.events) || !Array.isArray(value.stages)) throw new Error("Replay events and stages must be arrays.");
  if (!["running", "completed", "failed", "cancelled"].includes(string(value.status))) throw new Error("Unknown run status.");
  if (!["live", "imported"].includes(string(object(value.recording).kind))) throw new Error("Replay must declare live or imported recording.");
  const stageIds = new Set<string>();
  for (const entry of value.stages) {
    const stage = object(entry);
    if (!string(stage.id) || !string(stage.title) || !Array.isArray(stage.next) || stage.next.some(id => typeof id !== "string")) throw new Error("A pipeline stage is malformed.");
    if (stageIds.has(string(stage.id))) throw new Error("Duplicate pipeline stage: " + stage.id);
    stageIds.add(string(stage.id));
  }
  for (const entry of value.stages) {
    for (const next of array(object(entry).next)) if (!stageIds.has(string(next))) throw new Error("Pipeline references an unknown stage: " + next);
  }
  value.events.forEach((entry, index) => {
    const event = object(entry), payload = object(event.payload);
    if (event.sequence !== index) throw new Error("Events must be contiguous and ordered from sequence zero.");
    if (!stageIds.has(string(event.stage))) throw new Error("Event " + index + " references an unknown stage.");
    if (!kinds.has(string(payload.kind))) throw new Error("Unknown event kind at sequence " + index + ".");
    if (event.elapsed_ms !== null && (!Number.isSafeInteger(event.elapsed_ms) || Number(event.elapsed_ms) < 0)) throw new Error("Invalid elapsed time at sequence " + index + ".");
    const required: Record<string, string[]> = {
      source_imported: ["source"], case_registered: ["case_id", "title", "derivation"],
      build_recorded: ["build_id", "build"], execution_started: ["execution_id", "case_id", "request_id", "build_id"],
      execution_finished: ["execution_id", "status"], feedback_recorded: ["feedback"],
      change_proposed: ["change_id", "description", "motivating_feedback_ids"],
      acceptance_plan_frozen: ["plan_id", "plan"], review_recorded: ["review_id", "review"],
      decision_recorded: ["decision_id", "change_id", "plan_id", "decision"], compute_recorded: ["usage"],
    };
    if (required[string(payload.kind)].some(key => payload[key] === undefined || payload[key] === null)) throw new Error("Event " + index + " is missing required fields.");
  });
  if (!value.artifacts || Array.isArray(value.artifacts) || typeof value.artifacts !== "object") throw new Error("Replay artifact index is missing.");
  for (const [hash, raw] of Object.entries(object(value.artifacts))) {
    const artifact = object(raw);
    if (!isHash(hash) || !string(artifact.path) || !string(artifact.media_type) || !["bytes", "canonical_json"].includes(string(artifact.hash_mode))) throw new Error("Malformed artifact index entry: " + hash);
  }
  const target = object(value.target);
  if (!string(target.name) || typeof target.repository !== "string" || typeof target.baseline_revision !== "string") throw new Error("Replay target metadata is incomplete.");
  const contents: Record<string, string> = {};
  for (const [hash, content] of Object.entries(object(container.artifact_contents))) {
    if (!isHash(hash) || typeof content !== "string") throw new Error("Portable artifact contents must map SHA-256 hashes to UTF-8 strings.");
    contents[hash] = content;
  }
  return { replay: value as unknown as Replay, artifact_contents: contents };
}

export function visibleEvents(replay: Replay, cursor: number): FactoryEvent[] {
  return replay.events.slice(0, Math.max(0, Math.min(replay.events.length, cursor + 1)));
}
export function updatedCursor(previous: Replay, next: Replay, cursor: number, following: boolean): number {
  if (previous.run_id !== next.run_id) return next.events.length - 1;
  if (next.events.length < previous.events.length || previous.events.some((event, index) => JSON.stringify(event) !== JSON.stringify(next.events[index]))) {
    throw new Error("The recorded event history changed. Reload the run to inspect the new recording.");
  }
  return following ? next.events.length - 1 : Math.min(cursor, next.events.length - 1);
}
export function artifactReferences(value: unknown): string[] {
  const found = new Set<string>();
  const visit = (entry: unknown) => {
    if (isHash(entry)) found.add(entry);
    else if (Array.isArray(entry)) entry.forEach(visit);
    else if (entry && typeof entry === "object") Object.values(entry).forEach(visit);
  };
  visit(value);
  return [...found];
}

export function caseEvents(events: FactoryEvent[], caseId: string): FactoryEvent[] {
  const executions = new Set<string>(), feedback = new Set<string>(), changes = new Set<string>(), plans = new Set<string>(), sources = new Set<string>();
  const lineage = new Set([caseId]);
  for (const event of [...events].reverse()) {
    const p = event.payload, derivation = object(p.derivation);
    if (p.kind === "case_registered" && lineage.has(string(p.case_id))) {
      if (derivation.parent_case_id) lineage.add(string(derivation.parent_case_id));
      array(derivation.source_ids).forEach(id => sources.add(string(id)));
      array(derivation.source_records).forEach(ref => sources.add(string(object(ref).source_id)));
    }
  }
  for (const event of events) {
    const p = event.payload;
    if (p.kind === "execution_started" && p.case_id === caseId) executions.add(string(p.execution_id));
    if (p.kind === "feedback_recorded" && object(p.feedback).case_id === caseId) feedback.add(string(object(p.feedback).feedback_id));
    if (p.kind === "change_proposed" && array(p.motivating_feedback_ids).some(id => feedback.has(string(id)))) changes.add(string(p.change_id));
    if (p.kind === "execution_started" && p.case_id === caseId && p.change_id) changes.add(string(p.change_id));
    if (p.kind === "acceptance_plan_frozen" && [object(p.plan).case_id, ...array(object(p.plan).regression_case_ids), ...array(object(p.plan).holdout_case_ids)].includes(caseId)) plans.add(string(p.plan_id));
  }
  return events.filter(event => {
    const p = event.payload;
    return p.case_id === caseId ||
      (p.kind === "case_registered" && lineage.has(string(p.case_id))) ||
      (p.kind === "source_imported" && sources.has(string(object(p.source).snapshot_id))) ||
      (p.execution_id !== undefined && executions.has(string(p.execution_id))) ||
      (p.kind === "feedback_recorded" && feedback.has(string(object(p.feedback).feedback_id))) ||
      (p.kind === "change_proposed" && changes.has(string(p.change_id))) ||
      (p.kind === "acceptance_plan_frozen" && plans.has(string(p.plan_id))) ||
      (p.kind === "review_recorded" && plans.has(string(object(p.review).plan_id))) ||
      (p.kind === "decision_recorded" && (changes.has(string(p.change_id)) || plans.has(string(p.plan_id)))) ||
      (p.kind === "compute_recorded" && executions.has(string(object(p.usage).execution_id)));
  });
}
export function casesAt(events: FactoryEvent[]): CaseView[] {
  return events.filter(event => event.payload.kind === "case_registered").map(event => {
    const id = string(event.payload.case_id), related = caseEvents(events, id);
    return { id, title: string(event.payload.title), event, events: related, feedback: related.filter(item => item.payload.kind === "feedback_recorded" && object(item.payload.feedback).case_id === id) };
  });
}
export function eventTitle(event: FactoryEvent): string {
  const p = event.payload;
  switch (p.kind) {
    case "source_imported": return string(object(p.source).provider) + " source imported";
    case "case_registered": return string(p.title);
    case "execution_started": return p.change_id ? "Candidate execution started" : "Baseline execution started";
    case "execution_finished": return "Execution " + label(p.status);
    case "feedback_recorded": return label(object(p.feedback).declared_strength) + " feedback · " + label(object(p.feedback).result);
    case "change_proposed": return string(p.description);
    case "decision_recorded": return "Recorded decision · " + label(object(p.decision).kind);
    case "review_recorded": return "Review · " + label(object(p.review).decision);
    case "acceptance_plan_frozen": return "Acceptance plan frozen";
    case "compute_recorded": return "Compute usage recorded";
    case "build_recorded": return "Build provenance recorded";
    default: return label(p.kind);
  }
}
export function referenceIssues(replay: Replay): string[] {
  const issues: string[] = [];
  const cases = new Set<string>(), executions = new Set<string>(), feedback = new Set<string>(), changes = new Set<string>(), plans = new Set<string>(), sources = new Set<string>(), finished = new Set<string>();
  const requireRef = (set: Set<string>, id: Json | undefined, name: string, seq: number) => {
    if (typeof id !== "string" || !set.has(id)) issues.push("Event " + seq + ": missing earlier " + name + " " + short(id) + ".");
  };
  for (const event of replay.events) {
    const p = event.payload, seq = event.sequence;
    if (p.kind === "source_imported") sources.add(string(object(p.source).snapshot_id));
    if (p.kind === "case_registered") {
      const d = object(p.derivation);
      if (d.kind === "reduced") requireRef(cases, d.parent_case_id, "parent case", seq);
      array(d.source_ids).forEach(id => requireRef(sources, id, "source", seq));
      cases.add(string(p.case_id));
    }
    if (p.kind === "execution_started") {
      requireRef(cases, p.case_id, "case", seq);
      if (executions.has(string(p.execution_id))) issues.push("Event " + seq + ": duplicate execution identifier.");
      if (p.change_id) requireRef(changes, p.change_id, "change", seq);
      executions.add(string(p.execution_id));
    }
    if (p.kind === "execution_finished") {
      requireRef(executions, p.execution_id, "execution", seq);
      if (finished.has(string(p.execution_id))) issues.push("Event " + seq + ": execution has multiple finishes.");
      finished.add(string(p.execution_id));
    }
    if (p.kind === "feedback_recorded") {
      const f = object(p.feedback);
      requireRef(cases, f.case_id, "case", seq);
      array(f.execution_ids).forEach(id => requireRef(executions, id, "execution", seq));
      feedback.add(string(f.feedback_id));
    }
    if (p.kind === "change_proposed") {
      array(p.motivating_feedback_ids).forEach(id => requireRef(feedback, id, "feedback", seq));
      changes.add(string(p.change_id));
    }
    if (p.kind === "acceptance_plan_frozen") plans.add(string(p.plan_id));
    if (p.kind === "review_recorded") requireRef(plans, object(p.review).plan_id, "plan", seq);
    if (p.kind === "decision_recorded") {
      requireRef(changes, p.change_id, "change", seq);
      requireRef(plans, p.plan_id, "plan", seq);
    }
  }
  return issues;
}

export function canonicalJson(value: Json): string {
  if (typeof value === "number" && !Number.isSafeInteger(value)) throw new Error("Canonical verification requires exactly representable integers.");
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return "[" + value.map(canonicalJson).join(",") + "]";
  return "{" + Object.keys(value).sort().map(key => JSON.stringify(key) + ":" + canonicalJson(value[key])).join(",") + "}";
}
export async function verifyArtifact(hash: string, artifact: Artifact, bytes: Uint8Array): Promise<ArtifactState> {
  let text: string;
  try { text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes); }
  catch { return { status: "unverified", detail: "Binary artifact. Download the original to inspect it." }; }
  let value: Json | undefined;
  try { value = JSON.parse(text.replace(/^\uFEFF/, "")) as Json; } catch { /* Text artifacts remain readable. */ }
  let digestBytes = bytes;
  if (artifact.hash_mode === "canonical_json") {
    if (value === undefined) return { status: "mismatch", text, detail: "Expected JSON, but the artifact cannot be parsed." };
    // JSON.parse loses lexical distinctions such as 1.0 or 1e3 that serde retains.
    const numericTokens = text.replace(/"(?:\\.|[^"\\])*"/g, '""').match(/-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/g) ?? [];
    if (numericTokens.some(token => /[.eE]/.test(token))) return { status: "unverified", text, value, detail: "Decimal or exponent numbers need verification by the native exporter." };
    try { digestBytes = new TextEncoder().encode(canonicalJson(value)); }
    catch (error) { return { status: "unverified", text, value, detail: (error as Error).message }; }
  }
  if (!globalThis.crypto?.subtle) return { status: "unverified", text, value, detail: "Hash verification requires a secure browser context (HTTPS or localhost)." };
  const buffer = new Uint8Array(digestBytes).buffer;
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  const actual = [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, "0")).join("");
  return { status: actual === hash ? "verified" : "mismatch", text, value, detail: actual === hash ? "SHA-256 matches the replay artifact index." : "SHA-256 does not match. This artifact is not trusted evidence." };
}

