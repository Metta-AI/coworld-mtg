import { describe, expect, it } from "vitest";
import { isScryfallRecord, renderGenericSourceRecord, renderRecordedResult } from "./record-view";

const result = (data: unknown, summary = "Recorded test measurements") => ({ schema: "software-factory-result-v1", summary, data });

describe("tagged generic recorded results", () => {
  it("does not guess a result contract from counter names or unknown schemas", () => {
    expect(renderRecordedResult({ rows: 92, card_frequency: [] })).toBeNull();
    expect(renderRecordedResult({ ...result({ rows: 92 }), schema: "unknown-v2" })).toBeNull();
  });
  it("reports malformed tagged records instead of inventing missing measurements", () => {
    for (const malformed of [result(null), result([]), result("invalid"), { ...result({}), summary: 92 }]) {
      expect(renderRecordedResult(malformed)).toContain("Malformed recorded result");
    }
  });
  it("shows recorded zero, false, null and empty arrays without inferring success", () => {
    const html = renderRecordedResult(result({ rows: 92, normalized_casts: 0, card_frequency: [], repeatable: false, error: null }))!;
    expect(html).toContain("92");
    expect(html).toContain("<dd>0</dd>");
    expect(html).toContain("<dd>false</dd>");
    expect(html).toContain("<dd>null</dd>");
    expect(html).toContain("0 recorded rows (empty array)");
    expect(html).not.toContain("positive");
    expect(html).not.toContain("accepted");
    expect(html).toContain("not an inferred verdict");
  });
  it("bounds rows, columns and cell text while identifying truncation", () => {
    const rows = Array.from({ length: 35 }, (_, row) => Object.fromEntries(Array.from({ length: 12 }, (_, col) => ["field_" + col, row === 34 ? "hidden final row" : `${row}:` + "a".repeat(400)])));
    const html = renderRecordedResult(result({ normalized_casts: rows }))!;
    expect(html.match(/<tbody><tr>|<\/tr><tr>/g)?.length).toBe(20);
    expect(html).toContain("Showing 20 of 35 recorded rows");
    expect(html).toContain("Showing 8 of 12 fields");
    expect(html).toContain("more characters]");
    expect(html).not.toContain("hidden final row");
    expect(html.length).toBeLessThan(50_000);
  });
  it("handles mixed and deeply nested values and caps the overall display", () => {
    const html = renderRecordedResult(result({ mixed: [null, 7, false, "text", { nested: [] }], deep: { a: { b: { secret: "too deep" } } }, large: Object.fromEntries(Array.from({ length: 1000 }, (_, index) => [String(index), "value"])) }))!;
    expect(html).toContain("Recorded value");
    expect(html).toContain("Showing 16 of 1000 recorded fields");
    expect(html).toContain("Nested data is retained");
    expect(html).not.toContain("too deep");
  });
  it("escapes untrusted summaries, field names and values", () => {
    const html = renderRecordedResult(result({ '<img src=x onerror=alert(1)>': [{ name: '<script>alert(1)</script>' }] }, '<iframe src="bad">'))!;
    expect(html).not.toContain("<script>");
    expect(html).not.toContain("<iframe");
    expect(html).not.toContain("<img");
    expect(html).toContain("&lt;script&gt;");
  });
});

describe("source record presentation", () => {
  it("preserves actual Scryfall records and avoids labeling generic records as cards", () => {
    expect(isScryfallRecord({ oracle_id: "real-id", oracle_text: "Recorded text" })).toBe(true);
    expect(isScryfallRecord({ object: "card", card_faces: [] })).toBe(true);
    const source = { record_id: "row:1", row: 1, column: "user_turn_2_creatures_cast", arena_id: "104926" };
    expect(isScryfallRecord(source)).toBe(false);
    const html = renderGenericSourceRecord(source);
    expect(html).toContain("104926");
    expect(html).not.toContain("Oracle");
    expect(html).not.toContain("Scryfall");
  });
});
