import { label, object, string, type Fields, type Json } from "./model";

const esc = (value: unknown) => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]!);
const MAX_ROWS = 20, MAX_COLUMNS = 8, MAX_FIELDS = 16, MAX_CELLS = 320, MAX_CELL_CHARS = 240;
const isRecord = (value: unknown): value is Fields => value !== null && typeof value === "object" && !Array.isArray(value);
const nested = (value: unknown) => value !== null && typeof value === "object";
const shortened = (text: string, limit = MAX_CELL_CHARS) => text.length > limit ? text.slice(0, limit) + `… [${text.length - limit} more characters]` : text;
const cell = (value: unknown) => value === undefined ? "—" : typeof value === "string" ? shortened(value) : nested(value) ? Array.isArray(value) ? `[${value.length} recorded items]` : `{${Object.keys(object(value)).length} recorded fields}` : String(value);
const fieldName = (key: string) => esc(shortened(label(key)));

// This envelope displays producer-recorded values. Its data never determines feedback or acceptance.
export function renderRecordedResult(value: unknown): string | null {
  const envelope = object(value);
  if (envelope.schema !== "software-factory-result-v1") return null;
  if (typeof envelope.summary !== "string" || !isRecord(envelope.data)) {
    return '<div class="recorded-result malformed"><strong>Malformed recorded result</strong><p>This tagged result requires a text summary and a data object. Inspect the original artifact.</p></div>';
  }
  const budget = { cells: MAX_CELLS };
  return `<section class="recorded-result"><span class="eyebrow">RECORDED RESULT</span><p class="result-summary">${esc(shortened(envelope.summary, 1200))}</p>${renderData(envelope.data, 0, budget)}<p class="recorded-result-note">Values are recorded measurements, not an inferred verdict. Tables show at most ${MAX_ROWS} rows and ${MAX_COLUMNS} columns; long cells are shortened. Inspect the original artifact for all data.</p></section>`;
}

function renderData(value: Json, depth: number, budget: { cells: number }): string {
  if (budget.cells <= 0) return '<p class="record-truncation">Display limit reached; inspect the original artifact for remaining data.</p>';
  if (Array.isArray(value)) {
    if (!value.length) return '<p class="record-empty">0 recorded rows (empty array).</p>';
    const displayed = value.slice(0, MAX_ROWS);
    const records = displayed.every(isRecord);
    const allColumns = records ? [...new Set(displayed.flatMap(row => Object.keys(object(row))))] : [];
    const columns = allColumns.slice(0, MAX_COLUMNS);
    const width = Math.max(1, columns.length);
    const rows = displayed.slice(0, Math.floor(budget.cells / width));
    budget.cells -= rows.length * width;
    if (!rows.length) return '<p class="record-truncation">Display limit reached; inspect the original artifact for remaining rows.</p>';
    return `<div class="generic-table table-scroll"><table><thead><tr>${columns.length ? columns.map(key => `<th>${fieldName(key)}</th>`).join("") : "<th>Recorded value</th>"}</tr></thead><tbody>${rows.map(row => `<tr>${columns.length ? columns.map(key => `<td>${esc(cell(object(row)[key]))}</td>`).join("") : `<td>${esc(cell(row))}</td>`}</tr>`).join("")}</tbody></table></div><p class="record-truncation">Showing ${rows.length} of ${value.length} recorded rows.${allColumns.length > columns.length ? ` Showing ${columns.length} of ${allColumns.length} fields found in these rows.` : ""}</p>`;
  }
  if (isRecord(value)) {
    const entries = Object.entries(value), shown = entries.slice(0, Math.min(MAX_FIELDS, budget.cells));
    budget.cells -= shown.length;
    const scalars = shown.filter(([, entry]) => !nested(entry));
    const children = shown.filter(([, entry]) => nested(entry));
    return `${scalars.length ? `<dl class="recorded-fields">${scalars.map(([key, entry]) => `<dt>${fieldName(key)}</dt><dd>${esc(cell(entry))}</dd>`).join("")}</dl>` : ""}${children.map(([key, entry]) => `<details class="recorded-section" ${depth === 0 && Array.isArray(entry) ? "open" : ""}><summary>${fieldName(key)} <span>${Array.isArray(entry) ? entry.length + " recorded rows" : Object.keys(object(entry)).length + " recorded fields"}</span></summary>${depth < 2 ? renderData(entry, depth + 1, budget) : '<p class="record-truncation">Nested data is retained in the original artifact.</p>'}</details>`).join("")}${entries.length > shown.length ? `<p class="record-truncation">Showing ${shown.length} of ${entries.length} recorded fields.</p>` : !entries.length ? '<p class="record-empty">No recorded fields (empty object).</p>' : ""}`;
  }
  budget.cells--;
  return `<p>${esc(cell(value))}</p>`;
}

export function isScryfallRecord(value: unknown): boolean {
  const record = object(value);
  return record.object === "card" || Boolean(string(record.oracle_id) && (typeof record.oracle_text === "string" || Array.isArray(record.card_faces)));
}

export function renderGenericSourceRecord(record: Fields): string {
  return `<div class="generic-source-record"><span class="eyebrow">RECORDED SOURCE RECORD</span>${renderData(record, 0, { cells: MAX_CELLS })}<p class="recorded-result-note">This is structured source data. Inspect the source artifact for the complete original record.</p></div>`;
}
