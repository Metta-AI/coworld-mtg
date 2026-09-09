import "./styles.css";
import "./fitting/styles.css";
import { caseRecord as fittingCase, fittingArtifactIds, fittingContext, fittingStatus, initialFittingSelection, isFittingRecord, selectedReport } from "./fitting/model";
import { renderFitting, renderFittingComparison } from "./fitting/view";
import { isScryfallRecord, renderGenericSourceRecord, renderRecordedResult } from "./record-view";
import {
  array, artifactReferences, candidateGateViolations, casesAt, decisionsForChange, emptyCaseState, evaluationReasons, eventTitle, label, object, parseReplay,
  portableBlockers, preferredRun, recordedRunContext,
  referenceIssues, short, string, updatedCursor, verifyArtifact, visibleEvents,
  type ArtifactState, type CaseView, type FactoryEvent, type Fields, type Replay, type RunSummary,
} from "./model";

const app = document.querySelector<HTMLDivElement>("#factory-app")!;
const state = {
  fitting: initialFittingSelection(), fittingStructureOpen: false,
  runs: [] as RunSummary[], replay: null as Replay | null, cursor: -1, selectedCase: "", requestedCase: "",
  tab: "evidence", filter: "", playing: false, following: false, loading: true,
  notice: "", error: "", sourceUrl: "", embedded: {} as Record<string, string>,
  artifacts: new Map<string, ArtifactState>(), inspecting: "", inspectingEvent: -1,
  issues: [] as string[], historyOpen: false, recoveryOpen: false, exportBlockers: [] as string[], timelineOpen: false, exporting: false, timelineFilter: "all", loadGeneration: 0,
};
const esc = (value: unknown) => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]!);
const pretty = (value: unknown) => JSON.stringify(value, null, 2);
const badge = (text: unknown, tone = "") => `<span class="badge ${esc(tone)}">${esc(label(text) || text)}</span>`;
const hashButton = (hash: unknown, title = "") => typeof hash === "string" && hash ? `<button class="artifact-link" data-artifact="${esc(hash)}" title="${esc(hash)}">${esc(title || short(hash))}<span aria-hidden="true"> ↗</span></button>` : "";
const empty = (title: string, detail: string) => `<div class="empty"><span class="empty-mark" aria-hidden="true">· · ·</span><h3>${esc(title)}</h3><p>${esc(detail)}</p></div>`;
const time = (ms: number | null) => ms === null ? "order only" : ms < 1000 ? ms + " ms" : ms < 60000 ? (ms / 1000).toFixed(1) + " s" : Math.floor(ms / 60000) + "m " + Math.floor(ms % 60000 / 1000) + "s";
const toneFor = (result: unknown) => ["accepted", "satisfied", "completed", "verified", "approve"].includes(string(result)) ? "positive" : ["rejected", "violated", "error", "failed", "mismatch"].includes(string(result)) ? "negative" : "muted";
const safeLink = (raw: unknown, title: string) => {
  try {
    const url = new URL(string(raw));
    if (["https:", "http:"].includes(url.protocol)) return `<a href="${esc(url.href)}" target="_blank" rel="noreferrer">${esc(title)} ↗</a>`;
  } catch { /* Invalid provenance URLs stay plain text. */ }
  return esc(title);
};
const currentEvents = () => state.replay ? visibleEvents(state.replay, state.cursor) : [];
const currentCases = () => casesAt(currentEvents());
const selectedCase = () => currentCases().find(item => item.id === state.selectedCase);
const valuesFor = (events: FactoryEvent[], kind: string) => events.filter(event => event.payload.kind === kind);
const artifactValue = (id: unknown): Fields => {
  const artifact = state.artifacts.get(string(id));
  return artifact?.status === "verified" || artifact?.status === "unverified" ? object(artifact.value) : {};
};

const currentFitting = () => fittingContext(currentEvents(), artifactValue);
const fittingHelpers = () => ({ read: artifactValue, artifact: hashButton, integrity: statusMarkup, caseTitle: (id: string) => currentCases().find(c => c.id === id)?.title || id });

function statusMarkup(id: string): string {
  const entry = state.artifacts.get(id);
  if (!state.replay?.artifacts[id]) return badge("not indexed", "negative");
  return badge(entry?.status ?? "not loaded", toneFor(entry?.status));
}
function render(): void {
  const active = document.activeElement as HTMLInputElement | null;
  const focusId = active?.id;
  const selection = active?.type === "search" ? active.selectionStart : null;
  const scrolls = new Map([...app.querySelectorAll<HTMLElement>("[data-scroll]")].map(el => [el.dataset.scroll, el.scrollTop]));
  const replay = state.replay, events = currentEvents(), cases = currentCases();
  if (cases.some(item => item.id === state.requestedCase)) state.selectedCase = state.requestedCase;
  if (cases.length && !cases.some(item => item.id === state.selectedCase)) state.selectedCase = cases[0].id;
  const selected = selectedCase();
  const feedback = valuesFor(events, "feedback_recorded");
  const decisions = valuesFor(events, "decision_recorded");
  const current = events.at(-1);
  const measured = valuesFor(events, "compute_recorded").filter(event => object(event.payload.usage).measurement === "measured");
  const wall = measured.reduce((total, event) => total + Number(object(event.payload.usage).wall_ms ?? 0), 0);
  const hasFitting = currentFitting().reports.length > 0;
  app.classList.toggle("fitting-run", hasFitting);
  app.classList.toggle("show-fit-structure", state.fittingStructureOpen);
  app.innerHTML = `
    <header class="topbar">
      <a class="brand" href="./factory.html" aria-label="Coworld factory home"><span class="brand-symbol" aria-hidden="true"><i></i><i></i><i></i></span><span>COWORLD <b>FACTORY</b></span></a>
      <span class="top-divider"></span><span class="top-context">Improvement run explorer</span>
      <div class="top-actions">
        <label class="sr-only" for="run-select">Select a recorded run</label>
        <select id="run-select" ${state.runs.length ? "" : "disabled"}><option value="">${state.runs.length ? "Select a run" : "No served runs"}</option>${state.runs.map(run => `<option value="${esc(run.run_id)}" ${run.run_id === replay?.run_id ? "selected" : ""}>${esc(label(run.status))} · ${esc(run.run_id)} · ${esc(run.title)}</option>`).join("")}</select>
        <button class="button" data-action="import">Open replay</button><input id="replay-file" type="file" accept=".json,application/json" hidden>
        <button class="button primary" data-action="export" ${!replay || state.exporting ? "disabled" : ""}>${state.exporting ? "Packaging…" : "Save portable"}</button>
      </div>
    </header>
    ${state.error ? `<div class="notice error" role="alert">${esc(state.error)}<button data-action="dismiss">Dismiss</button></div>` : ""}
    ${state.notice ? `<div class="notice" role="status">${esc(state.notice)}<button data-action="dismiss">Dismiss</button></div>` : ""}
    ${!replay ? `<main class="welcome"><p class="eyebrow">From evidence to improvement</p><h1>Follow the work.<br>Inspect the proof.</h1><p class="welcome-copy">Replay how source data became a case, how feedback motivated a change, and what the recorded evaluation actually established.</p><div class="welcome-actions"><button class="button primary" data-action="import">Open a replay file</button><button class="button" data-action="refresh">Refresh available runs</button></div><div class="welcome-path"><span>Source</span><span>Case</span><span>Feedback</span><span>Change</span><span>Decision</span></div><p class="subtle">${state.loading ? "Loading recorded runs…" : "Open a portable replay JSON, or serve a factory run to explore its artifacts."}</p></main>` : `
    <section class="run-heading">
      <div class="run-heading-main"><p class="eyebrow">${esc(replay.target.name)} <span>/</span> ${esc(replay.run_id)}</p><h1>${esc(replay.title)}</h1><div class="run-meta">${badge(replay.status, toneFor(replay.status))}${badge(replay.recording.kind === "imported" ? "Imported evidence" : "Recorded run")}<span>Baseline ${esc(short(replay.target.baseline_revision))}</span><button class="text-button" data-action="raw-export">Replay metadata ↗</button><button class="text-button" data-action="run-history">Run history ↗</button>${hasFitting ? `<button class="text-button" data-action="fitting-structure" aria-expanded="${state.fittingStructureOpen}">${state.fittingStructureOpen ? "Hide run structure" : "Show run structure"}</button>` : ""}</div></div>
      <div class="run-stats"><div><strong>${cases.length}</strong><span>cases visible</span></div><div><strong>${feedback.length}</strong><span>feedback records</span></div><div><strong>${decisions.length}</strong><span>recorded decisions</span></div><div><strong>${measured.length ? time(wall) : "—"}</strong><span>measured worker time</span></div></div>
    </section>
    ${replay.recording.kind === "imported" ? `<div class="recording-note">ARCHIVAL RECORD <span>${esc(replay.recording.description || "Imported evidence. Event order reflects recorded dependencies; timing is not reconstructed.")}</span></div>` : ""}
    ${state.issues.length ? `<details class="integrity-warning"><summary>${state.issues.length} reference issue${state.issues.length === 1 ? "" : "s"} in this recording</summary><ul>${state.issues.map(issue => `<li>${esc(issue)}</li>`).join("")}</ul></details>` : ""}
    ${renderRunContext()}
    <section class="pipeline-section" aria-label="Recorded pipeline"><div class="section-label"><span>PIPELINE</span><span>Defined by this replay · select a stage to seek</span></div><div class="pipeline" style="--stage-count:${replay.stages.length}">${replay.stages.map((stage, index) => {
      const recorded = events.filter(event => event.stage === stage.id);
      const hasAny = replay.events.some(event => event.stage === stage.id);
      return `<button class="stage ${current?.stage === stage.id ? "current" : recorded.length ? "visited" : ""}" data-stage="${esc(stage.id)}" ${hasAny ? "" : "disabled"} title="Next: ${esc(stage.next.map(id => replay.stages.find(s => s.id === id)?.title ?? id).join(", ") || "terminal stage")}"><span class="stage-top"><span class="stage-number">${String(index + 1).padStart(2, "0")}</span><span class="stage-dot" aria-hidden="true"></span></span><strong>${esc(stage.title)}</strong><span class="stage-count">${recorded.length ? recorded.length + " recorded event" + (recorded.length === 1 ? "" : "s") : "No events yet"}</span><span class="stage-next">${stage.next.length ? "→ " + esc(stage.next.map(id => replay.stages.find(s => s.id === id)?.title ?? id).join(" / ")) : "End of pipeline"}</span></button>`;
    }).join("")}</div></section>
    <main class="workspace ${state.timelineOpen ? "show-timeline" : ""}">
      <aside class="case-sidebar"><div class="panel-header"><h2>Case queue</h2><span class="count">${cases.length}</span></div><div class="search-wrap"><label class="sr-only" for="case-search">Search cases</label><input id="case-search" type="search" placeholder="Search cases or feedback" value="${esc(state.filter)}"></div><div class="case-list" data-scroll="cases">${renderCaseQueue(cases)}</div><div class="sidebar-footer">Cases appear at their registration event.<br>Every count follows the replay cursor.</div></aside>
      <section class="case-panel" aria-label="Selected case"><div class="case-heading"><p class="eyebrow">SELECTED CASE</p><h2>${esc(selected?.title || (replay.status === "running" ? "Waiting for a case" : "No case registered"))}</h2>${selected ? `<div class="case-meta">${badge(label(object(selected.event.payload.derivation).kind))}${hashButton(selected.id, "Case definition")}</div>` : ""}</div><div class="tabs" role="tablist" aria-label="Case inspection">${[["evidence", "Evidence"], ["lineage", "Source & lineage"], ["changes", "Changes & decision"], ["artifacts", "Artifacts"]].map(([id, title]) => `<button role="tab" id="tab-${id}" aria-controls="case-content" aria-selected="${state.tab === id}" data-tab="${id}" ${state.tab === id ? 'class="active"' : ""}>${title}</button>`).join("")}</div><div id="case-content" class="case-content" role="tabpanel" aria-labelledby="tab-${state.tab}" data-scroll="content">${selected ? renderCaseContent(selected) : empty(emptyCaseState(replay, state.cursor).title, emptyCaseState(replay, state.cursor).detail)}</div></section>
      <aside class="timeline-panel"><div class="panel-header"><h2>Event stream</h2><span class="count">${replay.events.length}</span></div><div class="timeline-filter"><button data-timeline="all" class="${state.timelineFilter === "all" ? "active" : ""}">Whole run</button><button data-timeline="case" class="${state.timelineFilter === "case" ? "active" : ""}">Selected case</button></div><ol class="event-list" data-scroll="timeline">${renderTimeline(selected)}</ol><div class="timeline-footer">${current ? `<span>At event ${current.sequence + 1}</span><button class="text-button" data-event-detail="${current.sequence}">Inspect event JSON ↗</button>` : "<span>Before the first event</span>"}</div></aside>
    </main>
    <footer class="transport"><div class="transport-buttons"><button data-action="start" title="Seek to beginning" aria-label="Seek to beginning">|‹</button><button data-action="back" title="Previous event (left arrow)" aria-label="Previous event">‹</button><button class="play-button" data-action="play" aria-label="${state.playing ? "Pause replay" : "Play replay"}">${state.playing ? "Pause" : "Play"}</button><button data-action="next" title="Next event (right arrow)" aria-label="Next event">›</button></div><div class="scrubber"><div class="scrubber-caption"><span>${state.following ? "FOLLOWING LATEST" : state.playing ? "PLAYING RECORDED EVENTS" : "REPLAY POSITION"}</span><span>${state.cursor + 1} / ${replay.events.length} events <b>·</b> ${current ? time(current.elapsed_ms) : "start"}</span></div><label class="sr-only" for="replay-position">Replay event position</label><input id="replay-position" type="range" min="-1" max="${Math.max(-1, replay.events.length - 1)}" value="${state.cursor}" ${replay.events.length ? "" : "disabled"}></div><button class="tablet-events" data-action="timeline" aria-expanded="${state.timelineOpen}">${state.timelineOpen ? "Close events" : "Events"}</button><button class="follow-button ${state.following ? "active" : ""}" data-action="follow" ${state.sourceUrl ? "" : "disabled"}><span class="live-dot"></span>${state.following ? "Following" : "Follow latest"}</button></footer>
    `}
    ${renderInspector()}
  `;
  for (const element of app.querySelectorAll<HTMLElement>("[data-scroll]")) element.scrollTop = scrolls.get(element.dataset.scroll) ?? 0;
  if (state.following) {
    const stream = app.querySelector<HTMLElement>(".event-list");
    if (stream) stream.scrollTop = stream.scrollHeight;
  }
  if (focusId) {
    const element = document.getElementById(focusId) as HTMLInputElement | null;
    element?.focus({ preventScroll: true });
    if (selection !== null && element?.type === "search") element.setSelectionRange(selection, selection);
  }
  const dialog = app.querySelector<HTMLDialogElement>("dialog");
  if (dialog) { dialog.showModal(); dialog.addEventListener("cancel", event => { event.preventDefault(); closeInspector(); }); }
  scheduleArtifacts();
}

function renderCaseQueue(cases: CaseView[]): string {
  const filter = state.filter.toLowerCase();
  const matches = cases.filter(item => (item.title + " " + item.id + " " + pretty(item.feedback.map(event => event.payload.feedback))).toLowerCase().includes(filter));
  return matches.length ? matches.map(item => {
    const latest = object(item.feedback.at(-1)?.payload.feedback);
    const report = selectedReport(currentFitting(), item.id, "");
    const fitStatus = report ? fittingStatus(fittingCase(report, item.id).status) : "";
    return `<button class="case-row ${state.selectedCase === item.id ? "selected" : ""}" data-case="${esc(item.id)}" aria-pressed="${state.selectedCase === item.id}"><span class="case-row-top"><span class="case-origin">${esc(label(object(item.event.payload.derivation).kind))}</span><span class="case-sequence">${String(item.event.sequence + 1).padStart(2, "0")}</span></span><strong>${esc(item.title)}</strong><span class="case-row-bottom">${badge(fitStatus || latest.result || "awaiting feedback", fitStatus ? "muted" : toneFor(latest.result))}<span>${item.feedback.length} feedback</span></span></button>`;
  }).join("") : empty(filter ? "No matching cases" : emptyCaseState(state.replay!, state.cursor).title, filter ? "Try a card name, case ID, or feedback result." : emptyCaseState(state.replay!, state.cursor).detail);
}

function renderCaseContent(selected: CaseView): string {
  if (state.tab === "lineage") return renderLineage(selected);
  if (state.tab === "changes") return renderFittingComparison(currentFitting(), selected.id, fittingHelpers()) + renderChanges(selected);
  if (state.tab === "artifacts") {
    const refs = artifactReferences(selected.events).filter(id => state.replay?.artifacts[id]);
    return `<div class="content-intro"><h3>Evidence inventory</h3><p>Artifacts referenced by the visible lineage of this case. Verification checks content against its recorded SHA-256.</p></div>${refs.length ? `<div class="artifact-list">${refs.map(id => `<button class="artifact-row" data-artifact="${esc(id)}"><span><strong>${esc(state.replay!.artifacts[id].path)}</strong><code>${esc(short(id))}</code></span>${statusMarkup(id)}</button>`).join("")}</div>` : empty("No indexed artifacts", "This recording contains no indexed artifacts for the selected case.")}`;
  }
  const fitting = renderFitting(currentFitting(), selected.id, state.fitting, fittingHelpers());
  if (fitting !== null) return fitting;
  const feedback = [...selected.feedback].reverse().map(event => object(event.payload.feedback));
  const caseRecord = artifactValue(selected.id);
  return `
    ${caseRecord.oracle_text ? `<div class="case-oracle"><span class="eyebrow">SOURCE ORACLE TEXT</span><p>${esc(caseRecord.oracle_text)}</p></div>` : ""}<div class="content-intro"><h3>What did the evidence establish?</h3><p>Results below are recorded evaluator claims. Their scope and strength travel with the evidence.</p></div>
    ${feedback.length ? feedback.map(f => `<article class="feedback-card ${esc(string(f.declared_strength))}"><div class="card-top"><span class="eyebrow">${esc(label(f.declared_strength))} FEEDBACK</span>${badge(f.result, toneFor(f.result))}</div><h4>${esc(f.summary)}</h4><p class="bounded-claim">${esc(f.bounded_claim)}</p>${renderEvaluationDetails(string(f.feedback_id))}<details><summary>Evaluation method & provenance</summary><dl class="detail-list"><dt>Adapter</dt><dd>${esc(label(f.adapter) || "Not declared")}</dd><dt>Evaluator</dt><dd>${esc(f.evaluator)} <code>${esc(f.evaluator_version)}</code></dd><dt>Method</dt><dd>${esc(f.method)}</dd><dt>Evidence</dt><dd>${array(f.execution_ids).map(id => `<code>${esc(id)}</code>`).join(" ")}</dd></dl>${hashButton(f.feedback_id, "Feedback record")}</details></article>`).join("") : empty("No feedback recorded", "Executions and evaluator feedback will appear here as the replay advances.")}
    <div class="subsection-heading"><h3>Baseline → candidate</h3><span>Recorded executions</span></div><div class="comparison-grid">${renderExecutions(selected, false)}${renderExecutions(selected, true)}</div>
    ${caseRecord.justification ? `<details class="document-details"><summary>Expectation & scope</summary><pre>${esc(pretty(caseRecord.justification))}</pre></details>` : ""}
    ${caseRecord.scenario ? `<details class="document-details"><summary>Case inputs & operations</summary><pre>${esc(pretty(caseRecord.scenario))}</pre></details>` : ""}
  `;
}
function renderExecutions(selected: CaseView, candidate: boolean): string {
  const executions = valuesFor(selected.events, "execution_started").filter(event => Boolean(event.payload.change_id) === candidate);
  return `<section class="execution-column"><div class="comparison-heading"><span class="comparison-dot ${candidate ? "candidate" : ""}"></span><h4>${candidate ? "Candidate" : "Baseline"}</h4><span>${executions.length} runs</span></div>${executions.length ? executions.map(event => {
    const p = event.payload;
    const finish = selected.events.find(other => other.payload.kind === "execution_finished" && other.payload.execution_id === p.execution_id)?.payload;
    const evidence = artifactValue(finish?.evidence_id);
    const outcome = object(evidence.outcome);
    const observation = evidence.observation ?? outcome.observation;
    const standaloneResult = observation ? null : renderRecordedResult(evidence);
    return `<article class="execution-card"><div class="card-top"><code>${esc(p.execution_id)}</code>${badge("execution " + (finish?.status || "running"), toneFor(finish?.status))}</div>${candidate ? renderExecutionDecision(string(p.change_id), selected.events) : ""}${finish?.evidence_id ? `<div class="evidence-integrity">${statusMarkup(string(finish.evidence_id))}<span>Evidence content</span></div>` : ""}<div class="execution-links">${hashButton(p.build_id, "Build")}${hashButton(p.request_id, "Input")}${hashButton(finish?.evidence_id, "Evidence")}${array(finish?.trace_ids).map((id, i) => hashButton(id, "Trace " + (i + 1))).join("")}</div>${finish?.detail ? `<p>${esc(finish.detail)}</p>` : ""}${observation ? renderObservation(object(observation)) : standaloneResult !== null ? standaloneResult : outcome.reason ? `<pre>${esc(pretty(outcome.reason))}</pre>` : `<p class="subtle">${finish?.evidence_id ? evidenceHint(string(finish.evidence_id)) : "No execution evidence recorded yet."}</p>`}</article>`;
  }).join("") : `<p class="column-empty">No ${candidate ? "candidate" : "baseline"} execution recorded at this point.</p>`}</section>`;
}
function renderExecutionDecision(changeId: string, events: FactoryEvent[]): string {
  const decisions = decisionsForChange(events, changeId);
  return `<div class="execution-decision"><div class="execution-links">${hashButton(changeId, "Candidate patch")}</div>${decisions.length ? decisions.map(event => {
    const decision = object(event.payload.decision);
    return `<div class="candidate-verdict ${esc(string(decision.kind))}"><strong>Recorded decision: ${esc(label(decision.kind))}</strong>${array(decision.reasons).length ? `<ul>${array(decision.reasons).map(reason => `<li>${esc(reason)}</li>`).join("")}</ul>` : ""}${renderGateViolations(event)}<p>Applies to the frozen plan bound by this decision.</p>${hashButton(event.payload.decision_id, "Decision record")}</div>`;
  }).join("") : '<p class="candidate-pending">No decision recorded for this change at this point.</p>'}</div>`;
}
function evidenceHint(id: string): string {
  const artifact = state.artifacts.get(id);
  if (artifact?.status === "mismatch") return "Artifact hash mismatch. Evidence is withheld; inspect the original artifact.";
  if (artifact?.status === "missing") return "Evidence unavailable. Open a portable replay containing its artifacts.";
  return artifact?.status === "loading" ? "Loading recorded evidence…" : "Open the evidence artifact to inspect its result.";
}
// Adapter views display recorded values. Evaluation and acceptance remain producer decisions.
function renderEvaluationDetails(id: string): string {
  const receipt = artifactValue(id);
  const recordedResult = renderRecordedResult(receipt);
  if (recordedResult !== null) return recordedResult;
  const evaluations = array(receipt.evaluations).map(object);
  const rows = evaluations.flatMap((evaluation, trial) => array(evaluation.abilities).map(object).map(ability => ({
    trial: trial + 1, paragraph: Number(ability.source_paragraph_index ?? 0) + 1,
    expected: ability.expected_is_mana_ability, observed: ability.observed_is_mana_ability,
    verdict: ability.verdict, alignment: ability.ast_alignment,
  })));
  const reasons = evaluationReasons(receipt);
  const explanation = reasons.length ? `<aside class="evaluation-reasons"><div class="card-top"><strong>Recorded evaluator explanation</strong>${statusMarkup(id)}</div><ul>${reasons.map(reason => `<li>${esc(reason)}</li>`).join("")}</ul></aside>` : "";
  if (!rows.length) return explanation;
  const booleanText = (value: unknown) => value === true ? "Yes" : value === false ? "No" : "Not recorded";
  return explanation + `<div class="recorded-measurements"><div class="measurement-heading"><span>RECORDED CLASSIFICATION CHECK</span>${statusMarkup(id)}</div><div class="table-scroll"><table><thead><tr><th>Trial / ability</th><th>Expected mana ability</th><th>Observed mana ability</th><th>Evaluator verdict</th></tr></thead><tbody>${rows.map(row => `<tr><td>${row.trial} / ${row.paragraph}</td><td>${booleanText(row.expected)}</td><td>${booleanText(row.observed)}</td><td>${badge(row.verdict, row.verdict === "pass" ? "positive" : row.verdict === "fail" ? "negative" : "muted")}</td></tr>`).join("")}</tbody></table></div><p>Exact values from the recorded evaluator receipt. ${receipt.repeatable === true ? "Producer recorded repeatable results." : "Repeatability is not established by this view."}</p></div>`;
}
function renderParsedAbilities(parsed: Fields): string {
  const abilities = array(parsed.abilities).map(object);
  if (!abilities.length) return "";
  return `<div class="parsed-abilities"><span class="eyebrow">PARSED ABILITIES</span>${abilities.map((ability, index) => `<div class="parsed-ability"><div><strong>Ability ${index + 1} · ${esc(ability.kind)}</strong>${typeof ability.is_mana_ability === "boolean" ? badge("mana ability: " + (ability.is_mana_ability ? "yes" : "no")) : ""}</div><p>${esc(ability.description || "No description recorded")}</p><span>Effect: ${esc(object(ability.effect).type || "not recorded")}${object(ability.sub_ability).effect ? " → " + esc(object(object(ability.sub_ability).effect).type) : ""}</span></div>`).join("")}</div>`;
}
function renderObservation(observation: Fields): string {
  const recordedResult = renderRecordedResult(observation);
  if (recordedResult !== null) return recordedResult;
  return `<div class="observation">${renderParsedAbilities(object(observation.parsed))}${Array.isArray(observation.life) ? `<div class="life-readings">${observation.life.map((life, index) => `<span>Player ${index + 1}<strong>${esc(life)} <small>life</small></strong></span>`).join("")}</div>` : ""}${Array.isArray(observation.objects) ? `<div class="observed-objects">${observation.objects.slice(0, 12).map(raw => { const card = object(raw); return `<div><strong>${esc(card.name || card.object_id)}</strong><span>${esc(label(card.zone))}${card.tapped === true ? " · tapped" : ""}${Number(card.plus_one_counters) > 0 ? " · " + esc(card.plus_one_counters) + " counters" : ""}</span></div>`; }).join("")}</div>` : ""}<details><summary>Raw observation</summary><pre>${esc(pretty(observation))}</pre></details></div>`;
}

function renderLineage(selected: CaseView): string {
  const derivation = object(selected.event.payload.derivation);
  const sources = valuesFor(selected.events, "source_imported");
  const parents = valuesFor(selected.events, "case_registered").filter(event => event.payload.case_id !== selected.id);
  return `<div class="content-intro"><h3>Where this case came from</h3><p>Source records, derivation recipes, and parent cases preserve the path from external data to an executable case.</p></div>
    <article class="lineage-card"><span class="eyebrow">DERIVATION · ${esc(label(derivation.kind))}</span><p>${esc(derivation.recipe || derivation.description || "Authored case")}</p>${derivation.author ? `<p class="subtle">Author: ${esc(derivation.author)}</p>` : ""}${derivation.seed !== undefined && derivation.seed !== null ? `<p class="subtle">Recorded seed: <code>${esc(derivation.seed)}</code></p>` : ""}${parents.map(event => `<div class="parent-case"><span>Parent case</span><button class="text-button" data-case="${esc(event.payload.case_id)}">${esc(event.payload.title)} ↗</button></div>`).join("")}${hashButton(derivation.reduction_receipt_id, "Reduction receipt")}</article>
    ${sources.map(event => {
      const source = object(event.payload.source), id = string(source.snapshot_id);
      const sourceData = artifactValue(id);
      const records = array(derivation.source_records).filter(ref => object(ref).source_id === id);
      return `<article class="source-card"><div class="card-top"><span class="eyebrow">${esc(source.provider)}</span>${statusMarkup(id)}</div><h4>${esc(source.description || "Source snapshot")}</h4><dl class="detail-list"><dt>Retrieved</dt><dd>${esc(source.retrieved_at || "Not recorded")}</dd><dt>Source</dt><dd>${safeLink(source.url, string(source.url))}</dd><dt>Snapshot</dt><dd>${hashButton(id)}</dd></dl>${records.map(ref => renderSourceRecord(sourceData, string(object(ref).record_id))).join("")}${isScryfallRecord(sourceData) ? renderCardRecord(sourceData) : ""}</article>`;
    }).join("") || empty("No external source linked", "This case's visible derivation does not reference an imported source snapshot.")}
  `;
}
function renderSourceRecord(source: Fields, recordId: string): string {
  const candidates = [...array(source.records), ...array(source.data), ...array(source.cards), source];
  const record = candidates.map(object).find(item => item.id === recordId || item.oracle_id === recordId || item.record_id === recordId);
  if (record) return renderSourceData(record);
  const matching = Object.entries(state.replay?.artifacts ?? {}).filter(([, artifact]) => artifact.path.includes(recordId));
  for (const [id] of matching) {
    const loaded = artifactValue(id);
    if (Object.keys(loaded).length) return renderSourceData(loaded);
  }
  // A snapshot descriptor can link a separate artifact containing the selected records.
  for (const id of artifactReferences(source)) {
    const linked = artifactValue(id);
    const found = [...array(linked.records), ...array(linked.data), linked].map(object).find(item => item.id === recordId || item.oracle_id === recordId || item.record_id === recordId);
    if (found) return renderSourceData(found);
  }
  return `<div class="source-record-missing"><span>Recorded source selector</span><code>${esc(recordId)}</code><p class="subtle">Inspect the linked source artifact for this selector. No matching structured record is embedded in the loaded snapshot.</p></div>`;
}
function renderSourceData(record: Fields): string {
  return isScryfallRecord(record) ? renderCardRecord(record) : renderGenericSourceRecord(record);
}
function renderCardRecord(card: Fields): string {
  const faces = array(card.card_faces).length ? array(card.card_faces).map(object) : [card];
  return `<div class="oracle-record">${faces.map(face => `<div class="oracle-face"><div><h4>${esc(face.name || card.name)}</h4><code>${esc(face.mana_cost)}</code></div><p class="card-type">${esc(face.type_line || card.type_line)}</p><p class="oracle-text">${esc(face.oracle_text || "No Oracle text recorded.")}</p>${face.power !== undefined ? `<p class="power-toughness">${esc(face.power)} / ${esc(face.toughness)}</p>` : ""}</div>`).join("")}<details><summary>Raw Scryfall record</summary><pre>${esc(pretty(card))}</pre></details></div>`;
}

function renderChanges(selected: CaseView): string {
  const changes = valuesFor(selected.events, "change_proposed"), plans = valuesFor(selected.events, "acceptance_plan_frozen");
  const reviews = valuesFor(selected.events, "review_recorded"), decisions = valuesFor(selected.events, "decision_recorded");
  const context = recordedRunContext(currentEvents());
  return `<div class="content-intro"><h3>From feedback to a recorded decision</h3><p>Changes cite their motivating feedback. Plans and reviews retain the scope under which a decision was recorded.</p></div>
    ${context ? `<aside class="change-context"><div class="card-top"><span class="eyebrow">LATEST RUN CONTEXT · ${esc(context.source.provider)}</span>${hashButton(context.source.snapshot_id, "Context record")}</div><p>${esc(context.source.description)}</p><p class="subtle">This is a run-level record. Patch proposals below carry their own case and feedback links.</p><button class="text-button" data-action="run-history">Inspect planning & run history ↗</button></aside>` : ""}
    ${changes.map(event => {
      const p = event.payload, patch = state.artifacts.get(string(p.change_id));
      return `<article class="change-card"><div class="card-top"><span class="eyebrow">PROPOSED CHANGE</span>${hashButton(p.change_id, "Patch artifact")}</div><h4>${esc(p.description)}</h4><p class="subtle">Base revision <code>${esc(p.base_revision)}</code></p><div class="motivations"><span>Motivated by</span>${array(p.motivating_feedback_ids).map(id => hashButton(id)).join("") || "<span>No feedback linked</span>"}</div>${patch?.status === "verified" && patch.text ? `<details class="patch-details"><summary>Inspect recorded diff</summary><pre class="diff">${patch.text.split("\n").slice(0, 1000).map(line => `<span class="${line.startsWith("+") ? "addition" : line.startsWith("-") ? "deletion" : line.startsWith("@@") ? "hunk" : ""}">${esc(line)}</span>`).join("\n")}</pre></details>` : ""}</article>`;
    }).join("") || empty("No patch proposed for this case", "Planning records can precede a patch. No candidate result or acceptance is implied by a plan.")}
    ${plans.map(event => {
      const plan = object(event.payload.plan);
      return `<article class="plan-card"><div class="card-top"><span class="eyebrow">FROZEN ACCEPTANCE PLAN</span>${hashButton(event.payload.plan_id, "Plan")}</div><div class="plan-counts"><span><strong>${array(plan.regression_case_ids).length}</strong> regression cases</span><span><strong>${array(plan.holdout_case_ids).length}</strong> held-out cases</span></div><details><summary>Inspect the frozen case set</summary><pre>${esc(pretty(plan))}</pre></details></article>`;
    }).join("")}
    ${reviews.map(event => { const review = object(event.payload.review); return `<article class="review-card"><div class="card-top"><span class="eyebrow">REVIEW ATTESTATION</span>${badge(review.decision, toneFor(review.decision))}</div><h4>${esc(review.reviewer)}</h4><p>${esc(review.rationale)}</p>${hashButton(event.payload.review_id, "Review record")}</article>`; }).join("")}
    ${decisions.map(event => { const decision = object(event.payload.decision), policy = object(event.payload.policy); return `<article class="decision-card ${esc(string(decision.kind))}"><div class="card-top"><span class="eyebrow">RECORDED DECISION</span>${badge(decision.kind, toneFor(decision.kind))}</div><h4>${decision.kind === "accepted" ? "Accepted for the recorded plan" : "The proposed change was rejected"}</h4>${array(decision.reasons).length ? `<ul>${array(decision.reasons).map(reason => `<li>${esc(reason)}</li>`).join("")}</ul>` : `<p>This decision is bounded to the cases and gates named by the frozen plan. It does not establish correctness outside that scope.</p>`}${renderGateViolations(event)}<dl class="detail-list"><dt>Policy</dt><dd>${esc(label(policy.kind) || "Not declared")}</dd>${policy.scope ? `<dt>Claim scope</dt><dd>${esc(policy.scope)}</dd>` : ""}${policy.attestation_id ? `<dt>Attestation</dt><dd>${hashButton(policy.attestation_id)}</dd>` : ""}</dl>${hashButton(event.payload.decision_id, "Decision record")}<details><summary>Decision bindings</summary><pre>${esc(pretty(decision))}</pre></details></article>`; }).join("") || `<div class="pending-decision"><span class="status-dot"></span><div><strong>No decision recorded at this point</strong><p>The viewer does not turn passing feedback into acceptance.</p></div></div>`}
  `;
}
function renderGateViolations(decision: FactoryEvent): string {
  const violations = candidateGateViolations(currentEvents(), decision);
  return violations.length ? `<section class="candidate-gate-violations"><strong>Recorded candidate gate violations</strong><ul>${violations.map(item => `<li><button class="text-button" data-case="${esc(item.caseId)}">${esc(item.title)}</button> ${item.feedbackIds.map(id => hashButton(id, "Feedback evidence")).join(" ")}</li>`).join("")}</ul></section>` : "";
}
function renderTimeline(selected: CaseView | undefined): string {
  const replay = state.replay!;
  const caseSequences = new Set(selected?.events.map(event => event.sequence));
  const events = replay.events.filter(event => state.timelineFilter !== "case" || caseSequences.has(event.sequence));
  return events.map(event => {
    const visible = event.sequence <= state.cursor;
    return `<li class="event ${visible ? "seen" : "future"} ${event.sequence === state.cursor ? "current" : ""}"><button data-seek="${event.sequence}" aria-current="${event.sequence === state.cursor ? "step" : "false"}"><span class="event-marker" aria-hidden="true"></span><span class="event-body"><span class="event-top"><code>${String(event.sequence + 1).padStart(3, "0")}</code><span>${esc(time(event.elapsed_ms))}</span></span><strong>${esc(eventTitle(event))}</strong><span class="event-stage">${esc(replay.stages.find(stage => stage.id === event.stage)?.title || event.stage)}</span></span></button></li>`;
  }).join("") || '<li class="timeline-empty">No events in this view.</li>';
}

function renderDiagnostic(record: Fields): string {
  const reasons = [record.error, record.reason].filter(value => typeof value === "string" && value);
  const successor = string(record.successor_run_id);
  return `${reasons.map(reason => `<p class="diagnostic-reason">${esc(reason)}</p>`).join("")}${successor ? `<div class="successor-run"><span>Recorded successor:</span> ${state.runs.some(run => run.run_id === successor) ? `<button class="text-button" data-run="${esc(successor)}">${esc(successor)} ↗</button>` : `<code>${esc(successor)}</code>`}</div>` : ""}`;
}
function renderRunContext(): string {
  const replay = state.replay;
  if (!replay || !["failed", "cancelled"].includes(replay.status)) return "";
  const context = recordedRunContext(currentEvents());
  return `<section class="run-status-context"><div><strong>${esc(label(replay.status))} run</strong>${context ? `<p>${esc(context.source.description)}</p>${renderDiagnostic(artifactValue(context.source.snapshot_id))}` : "<p>No diagnostic is visible at this replay position.</p>"}</div><button class="text-button" data-action="run-history">Inspect recorded history ↗</button></section>`;
}
function renderRecovery(): string {
  const path = "replays/" + (state.replay?.run_id ?? "example");
  const quoted = "'" + path.replaceAll("'", "'\\''") + "'";
  return `<section class="artifact-recovery"><h3>Restore missing source artifacts</h3><p>For a shared package with <code>external-artifacts.json</code>, run the following from the repository checkout. Replace the directory if your package is stored elsewhere.</p><pre>python3 scripts/share_factory_replay.py hydrate ${esc(quoted)} --runtime target/debug/factory-runtime
target/debug/factory-runtime export ${esc(quoted)} --output complete.replay.json</pre><p>Hydration verifies downloaded bytes before adding them. For other missing or mismatched evidence, obtain the original hash-matching artifact from the run producer. Then retry export from the served run, or open <code>complete.replay.json</code> for offline inspection.</p><p><a href="https://github.com/Metta-AI/coworld-mtg/blob/main/docs/software-factory.md#share-a-run" target="_blank" rel="noreferrer">Hydration and portable export instructions ↗</a></p></section>`;
}
function renderInspector(): string {
  if (state.historyOpen && state.replay) {
    const records = currentEvents().filter(event => event.payload.kind === "source_imported");
    return `<dialog class="artifact-dialog" aria-labelledby="inspector-title"><div class="inspector-header"><div><p class="eyebrow">RECORDED RUN CONTEXT</p><h2 id="inspector-title">Run history & source records</h2></div><button class="button" data-action="close-inspector">Close</button></div><div class="inspector-body"><p class="history-intro">These descriptions and diagnostics come from events visible at the current replay position.</p>${[...records].reverse().map(event => {
      const source = object(event.payload.source), record = artifactValue(source.snapshot_id);
      return `<article class="run-history-record"><div class="card-top"><span class="eyebrow">EVENT ${event.sequence + 1} · ${esc(source.provider)}</span>${hashButton(source.snapshot_id, "Record")}</div><p>${esc(source.description)}</p>${renderDiagnostic(record)}<div class="history-record-meta"><span>${esc(source.retrieved_at)}</span><button class="text-button" data-event-detail="${event.sequence}">Event JSON ↗</button></div></article>`;
    }).join("") || empty("No source or history records yet", "Advance the replay to inspect recorded context.")}</div></dialog>`;
  }
  if (state.recoveryOpen && state.replay) {
    return `<dialog class="artifact-dialog" aria-labelledby="inspector-title"><div class="inspector-header"><div><p class="eyebrow">EXPORT BLOCKED</p><h2 id="inspector-title">Complete the replay before exporting</h2></div><button class="button" data-action="close-inspector">Close</button></div><div class="inspector-body"><p class="history-intro">No portable bundle was downloaded. Every indexed artifact must be present, and a hash mismatch must be resolved before export.</p><ul class="export-blockers">${state.exportBlockers.map(id => `<li>${hashButton(id, state.replay!.artifacts[id].path)} ${statusMarkup(id)}</li>`).join("")}</ul>${renderRecovery()}<button class="button" data-action="retry-export">Retry portable export</button></div></dialog>`;
  }
  if (state.inspectingEvent >= 0 && state.replay) {
    const event = state.replay.events[state.inspectingEvent];
    return `<dialog class="artifact-dialog" aria-labelledby="inspector-title"><div class="inspector-header"><div><p class="eyebrow">EVENT ${event.sequence + 1}</p><h2 id="inspector-title">${esc(eventTitle(event))}</h2></div><button class="button" data-action="close-inspector">Close</button></div><div class="inspector-body"><pre>${esc(pretty(event))}</pre><h3>Artifact references</h3><div class="reference-chips">${artifactReferences(event).filter(id => state.replay?.artifacts[id]).map(id => hashButton(id, state.replay!.artifacts[id].path)).join("") || "<p>No indexed artifacts referenced.</p>"}</div></div></dialog>`;
  }
  if (!state.inspecting) return "";
  const id = state.inspecting, artifact = state.replay?.artifacts[id], loaded = state.artifacts.get(id);
  return `<dialog class="artifact-dialog" aria-labelledby="inspector-title"><div class="inspector-header"><div><p class="eyebrow">CONTENT-ADDRESSED ARTIFACT</p><h2 id="inspector-title">${esc(artifact?.path || "Missing artifact")}</h2></div><button class="button" data-action="close-inspector">Close</button></div><div class="inspector-body"><div class="integrity-card ${loaded?.status === "mismatch" ? "failed" : ""}"><div class="card-top">${statusMarkup(id)}<span>${esc(artifact?.hash_mode.replaceAll("_", " ") || "unknown format")}</span></div><code class="full-hash">${esc(id)}</code><p>${esc(loaded?.detail || (artifact ? "Loading artifact and checking its SHA-256…" : "This reference is absent from the replay artifact index."))}</p></div>${loaded?.status === "missing" || loaded?.status === "mismatch" ? renderRecovery() : ""}${loaded?.text !== undefined ? `<div class="artifact-toolbar"><span>${esc(artifact?.media_type)} · ${new TextEncoder().encode(loaded.text).length.toLocaleString()} bytes</span><button class="text-button" data-action="artifact-export">Download original ↗</button></div><pre class="artifact-pre">${esc(loaded.value === undefined ? loaded.text : pretty(loaded.value))}</pre>` : ""}</div></dialog>`;
}
function closeInspector(): void { state.inspecting = ""; state.inspectingEvent = -1; state.historyOpen = false; state.recoveryOpen = false; render(); }

let artifactQueue = false;
function scheduleArtifacts(): void {
  if (artifactQueue || !state.replay) return;
  artifactQueue = true;
  queueMicrotask(() => {
    artifactQueue = false;
    const selected = selectedCase(), ids = new Set<string>();
    for (const id of fittingArtifactIds(currentEvents(), currentFitting(), selected?.id || "")) ids.add(id);
    if (state.inspecting) ids.add(state.inspecting);
    if (state.historyOpen) for (const event of currentEvents()) if (event.payload.kind === "source_imported") ids.add(string(object(event.payload.source).snapshot_id));
    if (state.replay?.status !== "running") {
      const context = recordedRunContext(currentEvents());
      if (context) ids.add(string(context.source.snapshot_id));
    }
    if (selected) {
      ids.add(selected.id);
      for (const event of selected.events) {
        const p = event.payload;
        if (p.kind === "execution_finished" && p.evidence_id) ids.add(string(p.evidence_id));
        if (p.kind === "change_proposed") ids.add(string(p.change_id));
        if (p.kind === "feedback_recorded") ids.add(string(object(p.feedback).feedback_id));
        if (p.kind === "source_imported") ids.add(string(object(p.source).snapshot_id));
        if (p.kind === "case_registered") {
          for (const ref of array(object(p.derivation).source_records)) {
            const recordId = string(object(ref).record_id);
            Object.entries(state.replay!.artifacts).filter(([, artifact]) => recordId && artifact.path.includes(recordId)).forEach(([hash]) => ids.add(hash));
          }
        }
      }
      for (const id of [...ids]) if (!isFittingRecord(artifactValue(id))) for (const linked of artifactReferences(artifactValue(id))) if (state.replay!.artifacts[linked]) ids.add(linked);
    }
    for (const id of ids) if (!state.artifacts.has(id) && state.replay!.artifacts[id]) void loadArtifact(id);
  });
}
async function loadArtifact(id: string, retry = false): Promise<ArtifactState> {
  const cached = state.artifacts.get(id);
  if (cached && cached.status !== "loading" && !(retry && ["missing", "mismatch"].includes(cached.status))) return cached;
  const replay = state.replay, generation = state.loadGeneration;
  const artifact = replay?.artifacts[id];
  if (!artifact) return { status: "missing", detail: "Artifact is not indexed by this replay." };
  state.artifacts.set(id, { status: "loading" });
  let result: ArtifactState;
  try {
    let bytes: Uint8Array;
    if (state.embedded[id] !== undefined) bytes = new TextEncoder().encode(state.embedded[id]);
    else if (state.sourceUrl) {
      const response = await fetch("/factory-api/runs/" + encodeURIComponent(replay!.run_id) + "/artifacts/" + encodeURIComponent(id), { cache: "no-store" });
      if (!response.ok) throw new Error("Artifact request returned " + response.status + ".");
      bytes = new Uint8Array(await response.arrayBuffer());
    } else throw new Error("This replay file does not include the artifact. Open a portable replay to inspect it offline.");
    result = await verifyArtifact(id, artifact, bytes);
  } catch (error) { result = { status: "missing", detail: (error as Error).message }; }
  if (state.loadGeneration === generation) { state.artifacts.set(id, result); render(); }
  return result;
}

async function loadRuns(): Promise<void> {
  state.loading = true; render();
  try {
    const response = await fetch("/factory-api/runs", { cache: "no-store" });
    if (!response.ok) throw new Error("Run service returned " + response.status + ".");
    const data = await response.json();
    const runs: unknown = Array.isArray(data) ? data : data.runs;
    if (!Array.isArray(runs)) throw new Error("Run service returned an invalid index.");
    state.runs = runs.filter((run: RunSummary) => typeof run.run_id === "string" && typeof run.title === "string");
  } catch (error) { state.notice = "Run service unavailable. You can still open a replay file. " + (error as Error).message; }
  const params = new URLSearchParams(location.search), requested = params.get("run");
  const replayUrl = params.get("replay");
  if (replayUrl) {
    const url = new URL(replayUrl, location.href);
    if (url.origin !== location.origin) state.error = "Replay URLs must use the same origin as the viewer.";
    else await loadRun(url.href);
  } else if (requested || state.runs.length) await loadRun("/factory-api/runs/" + encodeURIComponent(requested || preferredRun(state.runs)!.run_id) + "/replay.json");
  state.loading = false; render();
}
async function loadRun(url: string, poll = false): Promise<void> {
  try {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) throw new Error("Replay request returned " + response.status + ".");
    const parsed = parseReplay(await response.json());
    if (poll && state.replay) {
      state.cursor = updatedCursor(state.replay, parsed.replay, state.cursor, state.following);
      state.replay = parsed.replay; state.embedded = { ...state.embedded, ...parsed.artifact_contents };
      state.issues = referenceIssues(parsed.replay);
    } else installReplay(parsed.replay, parsed.artifact_contents, url);
    state.error = ""; render();
  } catch (error) { state.error = (error as Error).message; if (poll) state.following = false; render(); }
}
function installReplay(replay: Replay, embedded: Record<string, string>, sourceUrl: string): void {
  state.loadGeneration++; state.replay = replay; state.embedded = embedded; state.sourceUrl = sourceUrl;
  state.cursor = replay.events.length - 1; state.playing = false; state.following = false;
  state.artifacts.clear(); state.fittingStructureOpen = false; state.fitting = initialFittingSelection(); state.selectedCase = ""; state.inspecting = ""; state.inspectingEvent = -1;
  const params = new URLSearchParams(location.search);
  state.requestedCase = sourceUrl ? params.get("case") || "" : "";
  state.fitting.reportId = sourceUrl ? params.get("report") || "" : "";
  state.issues = referenceIssues(replay); state.error = ""; state.notice = ""; state.historyOpen = false; state.recoveryOpen = false; state.exportBlockers = [];
}
function updateSelectionUrl(): void {
  if (!state.sourceUrl || !state.replay) return;
  const url = new URL(location.href);
  if (!url.searchParams.has("replay")) url.searchParams.set("run", state.replay.run_id);
  if (state.requestedCase) url.searchParams.set("case", state.requestedCase); else url.searchParams.delete("case");
  if (state.fitting.reportId) url.searchParams.set("report", state.fitting.reportId); else url.searchParams.delete("report");
  history.replaceState(null, "", url);
}
function seek(position: number): void {
  state.following = false;
  state.cursor = Math.max(-1, Math.min(state.replay!.events.length - 1, position));
  render();
}
function download(value: string, filename: string, media = "application/json"): void {
  const url = URL.createObjectURL(new Blob([value], { type: media }));
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function portableExport(): Promise<void> {
  const replay = state.replay, generation = state.loadGeneration;
  if (!replay || state.exporting) return;
  state.exporting = true; state.error = ""; state.recoveryOpen = false; render();
  const contents: Record<string, string> = {}, results = new Map<string, ArtifactState>();
  const ids = Object.keys(replay.artifacts);
  for (let index = 0; index < ids.length; index += 4) {
    if (state.loadGeneration !== generation) break;
    await Promise.all(ids.slice(index, index + 4).map(async id => {
      const result = await loadArtifact(id, true); results.set(id, result);
      if (result.text !== undefined) contents[id] = result.text;
    }));
  }
  if (state.loadGeneration === generation) {
    state.exportBlockers = portableBlockers(replay, results);
    if (state.exportBlockers.length) {
      state.recoveryOpen = true; state.historyOpen = false; state.inspecting = ""; state.inspectingEvent = -1;
      state.error = "Portable export blocked: " + state.exportBlockers.length + " artifacts are unavailable or do not match their hashes.";
    } else {
      download(pretty({ replay, artifact_contents: contents }), replay.run_id + ".portable.json");
      const unverified = [...results.values()].filter(result => result.status === "unverified").length;
      state.notice = "Saved complete portable replay with " + Object.keys(contents).length + " artifact contents." + (unverified ? " " + unverified + " artifacts need native hash verification; see the export instructions." : "");
    }
  }
  state.exporting = false; render();
}

app.addEventListener("click", event => {
  const element = (event.target as HTMLElement).closest<HTMLElement>("button, [data-seek]");
  if (!element) return;
  if (element.dataset.case) { state.selectedCase = element.dataset.case; state.requestedCase = element.dataset.case; state.fitting = initialFittingSelection(); updateSelectionUrl(); const content = app.querySelector("#case-content"); if (content) content.scrollTop = 0; render(); return; }
  if (element.dataset.fitStep !== undefined) { state.fitting.transition = Number(element.dataset.fitStep); render(); return; }
  if (element.dataset.fitFields) { state.fitting.allFields = element.dataset.fitFields === "all"; render(); return; }
  if (element.dataset.tab) { state.tab = element.dataset.tab; render(); return; }
  if (element.dataset.artifact) { state.historyOpen = false; state.recoveryOpen = false; state.inspecting = element.dataset.artifact; state.inspectingEvent = -1; render(); return; }
  if (element.dataset.eventDetail) { state.historyOpen = false; state.recoveryOpen = false; state.inspectingEvent = Number(element.dataset.eventDetail); state.inspecting = ""; render(); return; }
  if (element.dataset.run) {
    state.historyOpen = false; state.recoveryOpen = false;
    const url = new URL(location.href); url.search = ""; url.searchParams.set("run", element.dataset.run); history.replaceState(null, "", url);
    void loadRun("/factory-api/runs/" + encodeURIComponent(element.dataset.run) + "/replay.json"); return;
  }
  if (element.dataset.timeline) { state.timelineFilter = element.dataset.timeline; render(); return; }
  if (element.dataset.seek !== undefined) { state.playing = false; seek(Number(element.dataset.seek)); return; }
  if (element.dataset.stage) {
    const target = state.replay?.events.find(item => item.stage === element.dataset.stage);
    if (target) { state.playing = false; seek(target.sequence); }
    return;
  }
  switch (element.dataset.action) {
    case "timeline": state.timelineOpen = !state.timelineOpen; render(); break;
    case "import": document.getElementById("replay-file")!.click(); break;
    case "run-history": state.historyOpen = true; state.recoveryOpen = false; state.inspecting = ""; state.inspectingEvent = -1; render(); break;
    case "retry-export": void portableExport(); break;
    case "refresh": void loadRuns(); break;
    case "dismiss": state.error = ""; state.notice = ""; render(); break;
    case "export": void portableExport(); break;
    case "raw-export": download(pretty(state.replay), state.replay!.run_id + ".replay.json"); break;
    case "artifact-export": {
      const id = state.inspecting, loaded = state.artifacts.get(id), artifact = state.replay?.artifacts[id];
      if (loaded?.text !== undefined) download(loaded.text, artifact?.path.split("/").pop() || id, artifact?.media_type);
      break;
    }
    case "fitting-structure": state.fittingStructureOpen = !state.fittingStructureOpen; render(); break;
    case "close-inspector": closeInspector(); break;
    case "start": state.playing = false; seek(-1); break;
    case "back": state.playing = false; seek(state.cursor - 1); break;
    case "next": state.playing = false; seek(state.cursor + 1); break;
    case "play": state.following = false; state.playing = !state.playing; if (state.playing && state.cursor >= state.replay!.events.length - 1) state.cursor = -1; render(); break;
    case "follow": state.playing = false; state.following = !state.following; if (state.following) { state.cursor = state.replay!.events.length - 1; void loadRun(state.sourceUrl, true); } render(); break;
  }
});
app.addEventListener("input", event => {
  const target = event.target as HTMLInputElement;
  if (target.id === "case-search") { state.filter = target.value; render(); }
  if (target.id === "replay-position") { state.playing = false; seek(Number(target.value)); }
});
app.addEventListener("change", async event => {
  const target = event.target as HTMLInputElement;
  if (target.id === "fit-report-select") { state.fitting = { ...initialFittingSelection(), reportId: target.value }; updateSelectionUrl(); render(); return; }
  if (target.id === "fit-moment-select") { state.fitting.moment = Number(target.value); render(); return; }
  if (target.id === "fit-transition-select") { state.fitting.transition = Number(target.value); render(); return; }
  if (target.id === "run-select" && target.value) {
    const url = new URL(location.href); url.search = ""; url.searchParams.set("run", target.value); history.replaceState(null, "", url);
    await loadRun("/factory-api/runs/" + encodeURIComponent(target.value) + "/replay.json");
  }
  if (target.id === "replay-file" && target.files?.[0]) {
    try {
      const parsed = parseReplay(JSON.parse(await target.files[0].text()));
      installReplay(parsed.replay, parsed.artifact_contents, ""); render();
    } catch (error) { state.error = "Cannot open replay: " + (error as Error).message; render(); }
  }
});
document.addEventListener("keydown", event => {
  const target = event.target as HTMLElement;
  if (!state.replay || target.closest("input, select, textarea, dialog") || target.isContentEditable) return;
  if (event.key === "ArrowRight") { event.preventDefault(); state.playing = false; seek(state.cursor + 1); }
  if (event.key === "ArrowLeft") { event.preventDefault(); state.playing = false; seek(state.cursor - 1); }
  if (event.key === " " && !target.closest("button, a")) { event.preventDefault(); state.playing = !state.playing; state.following = false; render(); }
});
setInterval(() => {
  if (!state.playing || !state.replay) return;
  if (state.cursor < state.replay.events.length - 1) state.cursor++;
  else state.playing = false;
  render();
}, 900);
let polling = false;
setInterval(async () => {
  if (!state.following || !state.sourceUrl || polling || document.hidden) return;
  polling = true; await loadRun(state.sourceUrl, true); polling = false;
}, 3000);
void loadRuns();

