import { describe, expect, it } from "vitest";
import { artifactReferences, canonicalJson, caseEvents, casesAt, parseReplay, referenceIssues, updatedCursor, verifyArtifact, visibleEvents, type FactoryEvent, type Replay } from "./model";

const hash = (char: string) => char.repeat(64);
const event = (sequence: number, payload: FactoryEvent["payload"], stage = "cases"): FactoryEvent => ({ sequence, elapsed_ms: sequence * 100, stage, payload });
function fixture(events: FactoryEvent[] = []): Replay {
  return {
    version: "software-factory-v1", run_id: "synthetic-test-only", title: "Synthetic model test fixture",
    target: { name: "test", repository: "https://example.test/repo", baseline_revision: "abc" },
    recording: { kind: "live" }, status: "running",
    stages: [{ id: "sources", title: "Sources", next: ["cases"] }, { id: "cases", title: "Cases", next: [] }],
    artifacts: { [hash("a")]: { path: "case.json", media_type: "application/json", hash_mode: "canonical_json" } },
    events,
  };
}
const register = (sequence = 0) => event(sequence, { kind: "case_registered", case_id: hash("a"), title: "Test case", derivation: { kind: "authored", author: "test", description: "Synthetic test" } });

describe("factory replay parsing and bounded history", () => {
  it("accepts raw replays and portable UTF-8 artifact bundles", () => {
    const replay = fixture([register()]);
    expect(parseReplay(replay)).toEqual({ replay, artifact_contents: {} });
    expect(parseReplay({ replay, artifact_contents: { [hash("a")]: "{}" } }).artifact_contents[hash("a")]).toBe("{}");
  });
  it("rejects corrupt sequence ordering instead of silently sorting away provenance", () => {
    expect(() => parseReplay(fixture([register(1)]))).toThrow("contiguous");
    expect(() => parseReplay(fixture([register(), register()]))).toThrow("contiguous");
  });
  it("rejects unknown event kinds, stage references, and malformed artifact indexes", () => {
    expect(() => parseReplay(fixture([event(0, { kind: "guess_accepted" })]))).toThrow("Unknown event");
    expect(() => parseReplay(fixture([event(0, { ...register().payload }, "invented")]))).toThrow("unknown stage");
    const replay = fixture();
    replay.stages[0].next = ["missing"];
    expect(() => parseReplay(replay)).toThrow("unknown stage");
    replay.stages[0].next = [];
    replay.artifacts = { invalid: replay.artifacts[hash("a")] };
    expect(() => parseReplay(replay)).toThrow("Malformed artifact");
  });
  it("keeps future cases and feedback outside the scrubbed state", () => {
    const replay = fixture([
      register(),
      event(1, { kind: "feedback_recorded", feedback: { case_id: hash("a"), feedback_id: hash("b"), result: "satisfied" } }),
    ]);
    expect(visibleEvents(replay, -1)).toEqual([]);
    expect(casesAt(visibleEvents(replay, -1))).toEqual([]);
    expect(casesAt(visibleEvents(replay, 0))[0].feedback).toHaveLength(0);
    expect(casesAt(visibleEvents(replay, 1))[0].feedback).toHaveLength(1);
    expect(visibleEvents(replay, 100)).toHaveLength(2);
  });
  it("follows appended events only in follow mode and rejects rewritten live history", () => {
    const before = fixture([register()]);
    const after = fixture([...before.events, event(1, { kind: "compute_recorded", usage: {} })]);
    expect(updatedCursor(before, after, 0, true)).toBe(1);
    expect(updatedCursor(before, after, 0, false)).toBe(0);
    expect(updatedCursor(before, after, -1, false)).toBe(-1);
    expect(() => updatedCursor(after, before, 1, true)).toThrow("history changed");
    const rewritten = fixture([event(0, { ...register().payload, title: "Changed history" })]);
    expect(() => updatedCursor(before, rewritten, 0, true)).toThrow("history changed");
  });
});

describe("case provenance and missing references", () => {
  it("traces reduced cases to their original source and only links motivated changes", () => {
    const events = [
      event(0, { kind: "source_imported", source: { snapshot_id: hash("c"), provider: "test" } }, "sources"),
      event(1, { kind: "case_registered", case_id: hash("a"), title: "parent", derivation: { kind: "source_derived", source_ids: [hash("c")] } }),
      event(2, { kind: "case_registered", case_id: hash("b"), title: "reduced", derivation: { kind: "reduced", parent_case_id: hash("a") } }),
      event(3, { kind: "execution_started", execution_id: "run-1", case_id: hash("b"), change_id: null }),
      event(4, { kind: "execution_finished", execution_id: "run-1", status: "completed" }),
      event(5, { kind: "feedback_recorded", feedback: { case_id: hash("b"), feedback_id: hash("d"), execution_ids: ["run-1"] } }),
      event(6, { kind: "change_proposed", change_id: hash("e"), motivating_feedback_ids: [hash("d")] }),
      event(7, { kind: "change_proposed", change_id: hash("f"), motivating_feedback_ids: [] }),
    ];
    expect(caseEvents(events, hash("b")).map(item => item.sequence)).toEqual([0, 1, 2, 3, 4, 5, 6]);
  });
  it("surfaces dangling and duplicate execution references without inventing evidence", () => {
    const replay = fixture([
      register(),
      event(1, { kind: "execution_finished", execution_id: "missing", status: "completed" }),
      event(2, { kind: "execution_finished", execution_id: "missing", status: "completed" }),
      event(3, { kind: "decision_recorded", change_id: hash("e"), plan_id: hash("f"), decision: { kind: "accepted" } }),
    ]);
    const issues = referenceIssues(replay).join("\n");
    expect(issues).toContain("missing earlier execution");
    expect(issues).toContain("multiple finishes");
    expect(issues).toContain("missing earlier change");
    expect(issues).toContain("missing earlier plan");
    expect(casesAt(replay.events)[0].feedback).toHaveLength(0);
  });
  it("deduplicates nested artifact references without treating arbitrary labels as hashes", () => {
    expect(artifactReferences({ a: hash("a"), b: [hash("a"), { c: hash("b") }], text: "not-an-artifact" })).toEqual([hash("a"), hash("b")]);
  });
});

describe("artifact integrity", () => {
  const artifact = { path: "fixture.json", media_type: "application/json", hash_mode: "canonical_json" as const };
  const expected = "53779873b478d720f102da39cc4ecd6d1a6ab7ac94a900ecfe44558db075290d";
  it("matches the Rust canonical-json golden digest with Unicode and nested keys", async () => {
    const text = '{ "z": [3, 1], "a": { "text": "café", "flag": true } }';
    expect(canonicalJson(JSON.parse(text))).toBe('{"a":{"flag":true,"text":"café"},"z":[3,1]}');
    const result = await verifyArtifact(expected, artifact, new TextEncoder().encode(text));
    expect(result.status).toBe("verified");
  });
  it("marks corrupted content and malformed canonical JSON as a mismatch", async () => {
    expect((await verifyArtifact(expected, artifact, new TextEncoder().encode('{"wrong":true}'))).status).toBe("mismatch");
    expect((await verifyArtifact(expected, artifact, new TextEncoder().encode("broken"))).status).toBe("mismatch");
  });
  it("avoids false integrity claims when JavaScript cannot preserve native number representations", async () => {
    for (const text of ['{"number":9007199254740993}', '{"number":1.0}', '{"number":1e3}']) {
      expect((await verifyArtifact(expected, artifact, new TextEncoder().encode(text))).status).toBe("unverified");
    }
  });
  it("hashes byte artifacts without canonicalizing JSON", async () => {
    const text = "hello";
    const result = await verifyArtifact("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824", { ...artifact, hash_mode: "bytes" }, new TextEncoder().encode(text));
    expect(result.status).toBe("verified");
    expect(result.text).toBe(text);
  });
});

