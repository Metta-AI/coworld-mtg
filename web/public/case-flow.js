/* A presentation of retained FactoryReplay evidence. This does not execute the engine. */
const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const display = (value) => value === null || value === undefined ? "Not recorded" : Array.isArray(value) ? value.join(", ") || "Empty" : typeof value === "object" ? JSON.stringify(value) : String(value);
const params = new URLSearchParams(location.search);
const run = params.get("run") || "17lands-trajectories-20260909-01";
const requestedCase = params.get("case") || "f12030d17b48417daf662d7754781c793580d37543a987ec50dcf813c44bfa6c";
const base = "/factory-api/runs/" + encodeURIComponent(run);
let steps = [], cursor = 0, timer = null, replay, caseId, checked = 0;
const cache = new Map();
const artifactUrl = (id) => base + "/artifacts/" + encodeURIComponent(id);
const link = (id, label) => '<a class="evidence-link" target="_blank" rel="noopener" href="' + artifactUrl(id) + '">' + esc(label) + ' <span aria-hidden="true">↗</span></a>';
const p = (text, cls = "") => '<p class="' + cls + '">' + esc(text) + "</p>";
const stats = (items) => '<div class="metric-grid">' + items.map(([label,value]) => '<div class="metric"><span class="value">' + esc(value) + '</span><span class="label">' + esc(label) + '</span></div>').join("") + "</div>";
const table = (headers, rows) => '<div class="table-scroll"><table class="field-table"><thead><tr>' + headers.map(h=>"<th>"+esc(h)+"</th>").join("") + "</tr></thead><tbody>" + rows.map(row=>"<tr>"+row.map(v=>"<td>"+esc(display(v))+"</td>").join("")+"</tr>").join("") + "</tbody></table></div>";
function requireValue(ok, message) { if (!ok) throw new Error(message); }
async function jsonUrl(url) {
  const response = await fetch(url, {cache:"no-store"});
  if (!response.ok) throw new Error("Evidence service returned " + response.status + ".");
  return response.json();
}
async function artifact(id) {
  requireValue(/^[a-f0-9]{64}$/.test(id || "") && replay.artifacts[id], "The replay does not contain the requested evidence.");
  if (!cache.has(id)) cache.set(id, (async () => {
    const response = await fetch(artifactUrl(id), {cache:"no-store"});
    if (!response.ok) throw new Error("An evidence artifact could not be loaded.");
    const bytes = await response.arrayBuffer();
    const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), b => b.toString(16).padStart(2,"0")).join("");
    // The recorder stores its canonical JSON in the exact bytes used for identity.
    requireValue(digest === id, "Artifact bytes do not match their recorded identity: " + id.slice(0,12));
    checked++;
    return JSON.parse(new TextDecoder().decode(bytes));
  })());
  return cache.get(id);
}
function sourceIds(provider) {
  return replay.events.filter(e => e.payload.kind === "source_imported" && e.payload.source.provider === provider).map(e => e.payload.source.snapshot_id);
}
function friendlyStatus(status) {
  return ({unsupported_boundary:"Unsupported turn boundary",matched_supported_projection:"Supported projections matched",input_issue:"Input needs attention",worker_execution:"Worker stopped"})[status] || String(status || "No native result").replaceAll("_"," ");
}
function simpleAction(transition) {
  const action=transition.action || {};
  if (action.type === "PlayLand") {
    const id=action.data?.object_id;
    const player=transition.before?.players?.find(p=>p.seat===transition.seat);
    return "Play " + (player?.hand?.find(c=>c.object_id===id)?.name || "land");
  }
  if (action.type === "MulliganDecision") return "Keep opening hand";
  if (action.type === "PassPriority") return "Pass priority";
  return action.type || "Recorded action";
}
function fieldLabel(field) {
  const column=field.source_field_id || field.column;
  const match=column.match(/^(user|oppo)_turn_(\d+)_(?:eot_)?(.*)$/);
  return match ? (match[1]==="user" ? "User" : "Opponent")+" turn "+match[2]+" · "+match[3].replaceAll("_"," ") : column;
}
function comparisonAtMoment(milestones) {
  return milestones.flatMap(m => m.fields.map(f=>({...f,key:m.key})));
}
async function load() {
  replay=await jsonUrl(base+"/replay.json");
  requireValue(replay.run_id === run && Array.isArray(replay.events) && replay.artifacts, "Unexpected replay format.");
  const comparisons=sourceIds("17Lands trajectory discovery comparison");
  requireValue(comparisons.length, "This walkthrough needs a recorded baseline/candidate comparison.");
  const comparisonId=comparisons.at(-1), comparison=await artifact(comparisonId);
  requireValue(comparison.schema === "coworld/17lands-discovery-comparison@1", "Unsupported comparison schema.");
  const [beforeReport,afterReport]=await Promise.all([artifact(comparison.baseline_report_id),artifact(comparison.candidate_report_id)]);
  const after=afterReport.cases.find(c=>c.case_id===requestedCase);
  requireValue(after, "This case is absent from the compared cohort.");
  caseId=after.case_id;
  const before=beforeReport.cases.find(c=>c.case_id===caseId);
  requireValue(before?.result_id && after.result_id, "This walkthrough requires retained native results for both attempts.");
  const [source,b,a,constraints]=await Promise.all([artifact(caseId),artifact(before.result_id),artifact(after.result_id),artifact(after.constraints_id)]);
  requireValue(a.trace?.schema === "coworld-17lands-fit-trace-v1", "The candidate has no supported explanatory trace.");
  const attributions=await Promise.all(sourceIds("17Lands trajectory repair attribution").map(artifact));
  const attribution=attributions.find(x=>x.change_id===comparison.change_id);
  requireValue(attribution?.origin_case_ids?.includes(caseId), "The proposed change is not attributed to this case.");
  const attributionId=sourceIds("17Lands trajectory repair attribution")[attributions.indexOf(attribution)];
  const row=comparison.rows.find(x=>x.case_id===caseId);
  requireValue(row, "The comparison does not contain this case.");
  const nativeIssue=beforeReport.issues.find(x=>x.kind==="unsupported_boundary" && x.origins.some(o=>o.case_id===caseId));
  const transitions=a.trace.transitions, failure=a.trace.failure, attempt=failure?.attempt;
  const matched=comparisonAtMoment(a.trace.milestones).filter(f=>f.comparison==="matched");
  const temporal=new Set(a.trace.milestones.filter(m=>m.fields.some(f=>f.comparison==="matched")).map(m=>JSON.stringify([m.key.turn_owner,m.key.turn_index,m.key.boundary]))).size;
  const seat=attempt?.seat;
  const bp=attempt?.before.players.find(p=>p.seat===seat), ap=attempt?.after.players.find(p=>p.seat===seat);
  const selected=attempt?.action.data?.cards || [];
  const cardNames=selected.map(id=>bp?.hand.find(c=>c.object_id===id)?.name || "object "+id);
  const events=attempt?.events || [];
  // Older traces use 'milestones' in failure context; locate the field-bearing list.
  const failedMilestones=Object.values(failure || {}).find(v=>Array.isArray(v) && v.some(x=>x && Array.isArray(x.fields))) || [];
  const expectedFields=comparisonAtMoment(failedMilestones).filter(f=>f.disposition==="enforced");
  const nextSource=constraints.fields.filter(f=>f.milestone?.turn_owner===1 && f.milestone.turn_index===1 && ["hand_count","lands","land_played"].includes(f.projection));
  const relevantSource=nextSource.filter(f=>f.column.includes("oppo_") && (f.column.endsWith("eot_oppo_cards_in_hand") || f.column.endsWith("eot_oppo_lands_in_play") || f.column.endsWith("lands_played")));
  const changed=(comparison.scope_changes || []).filter(x=>x.case_id===caseId);
  const reasonOnly=changed.length>0 && changed.every(x=>x.kind==="observation_changed" && JSON.stringify({...x.before,reason:null})===JSON.stringify({...x.after,reason:null}));
  const witnessSame=JSON.stringify(b.witness)===JSON.stringify(a.witness);
  const sourceRaw=source.selection.raw_metadata;
  const rowIndex=source.selection.source_row_index;
  const beforeLabel=friendlyStatus(before.status), afterLabel=friendlyStatus(after.status);
  const fullUrl="/client/factory.html?"+new URLSearchParams({run,case:caseId,report:comparison.candidate_report_id});
  $("full-replay").href=fullUrl;
  $("title").textContent="One game through the factory";
  $("subtitle").textContent="17Lands source row "+rowIndex+" · follow discovery, an attributed change, and the rerun.";
  const bounds=source.scope;
  const selectedAction=cardNames.length ? "Discard "+cardNames.join(", ") : "Inspect retained failure";
  const pathRows=transitions.map(t=>[t.index,simpleAction(t),t.seat===0?"User":"Opponent",t.after?.phase]);
  const eventsMarkup='<ol class="event-list">'+events.map(e=>"<li>"+esc(e.type)+(e.type==="ZoneChanged"?" · "+esc(e.data.record?.name || "")+" · "+esc(e.data.from)+" → "+esc(e.data.to):"")+"</li>").join("")+"</ol>";
  const mini=attempt?'<div class="mini-flow"><div class="mini-step"><span class="label">Before action '+esc(attempt.index)+'</span><strong>'+esc(attempt.before.phase)+'</strong><span>'+esc(bp?.hand.length)+' cards in hand</span></div><span aria-hidden="true">→</span><div class="mini-step"><span class="label">Engine action</span><strong>'+esc(selectedAction)+'</strong><span>'+esc(attempt.action.type)+'</span></div><span aria-hidden="true">→</span><div class="mini-step"><span class="label">After action</span><strong>'+esc(attempt.after.phase)+'</strong><span>'+esc(ap?.hand.length)+' cards in hand</span></div></div>':"";
  steps=[
    {id:"source",x:40,y:35,kicker:"SOURCE",title:"A real recorded game",metric:"17Lands · source row "+rowIndex,note:"Exact row and official card mapping",tone:"green",
     heading:"Begin with what the recording says",
     html:p("The game supplies the observations. We did not first invent a card-specific rule to test.")+
       stats([["recorded mulligans",sourceRaw.num_mulligans+" / "+sourceRaw.opp_num_mulligans],["plays first",sourceRaw.on_play==="True"?"User":"Opponent"]])+
       p("The original row, official Arena card mapping and sampling policy are retained. This previously inspected game is one of the first 20 rows, not an unseen holdout.","note")+
       link(source.source_id,"Original cohort CSV")+link(caseId,"Case definition")+link(source.mapping_id,"Official card mapping")},
    {id:"observations",x:415,y:35,kicker:"OBSERVATIONS + SETUP",title:"Make the recording executable",metric:a.milestones_total+" player-specific milestones",note:bounds.turn_pairs+" turns per player · partial coverage",tone:"green",
     heading:"Turn partial observations into checks",
     html:p("A milestone identifies whose turn ended and which player is observed. Card names, counts and life totals become requirements; missing fields remain unknown.")+
       stats([["enforced fields",after.coverage.enforced.length],["unsupported fields",after.coverage.unsupported.length]])+
       table(["Next recorded opponent turn","Source cell","Required value"],relevantSource.map(f=>[fieldLabel(f),f.raw,f.expected]))+
       p("Hidden cards and library order are reconstructed under explicit assumptions. The hypothetical opponent includes "+bounds.opponent_filler+" filler. This is one setup, not an exhaustive search over all hidden states.","warning")+
       link(after.constraints_id,"Extracted constraints and assumptions")},
    {id:"baseline",x:790,y:35,kicker:"BASELINE EXECUTION",title:"Search legal engine actions",metric:b.nodes.toLocaleString()+" nodes explored",note:b.milestones_fitted+" / "+b.milestones_total+" milestone keys matched",tone:"green",
     heading:"Ask whether an engine trajectory can fit",
     html:p("The fitter searches legal actions and can reconsider an earlier matching prefix when a later observation fails. The observation adapter decides which engine state corresponds to each recorded moment.")+
       stats([["nodes explored",b.nodes.toLocaleString()],["prefix backtracks",b.matched_prefix_backtracks],["matched keys",b.milestones_fitted+" / "+b.milestones_total],["fully covered milestones",b.fully_covered_milestones]])+
       p("Limits: "+bounds.nodes.toLocaleString()+" nodes, "+bounds.max_actions+" actions per path and "+bounds.deadline_seconds+" seconds. Recorded outcome: "+beforeLabel+".","note")+
       p("The original baseline receipt has no detailed trace. The two trace nodes below come from the instrumented rerun; they are labeled accordingly.","note")+
       link(before.result_id,"Original baseline result")},
    {id:"issue",x:790,y:255,kicker:"DISCOVERED OBSTACLE",title:"Preserve an issue candidate",metric:nativeIssue?"Unsupported turn boundary":beforeLabel,note:"Evidence to investigate · no rules verdict",tone:"amber",
     heading:"Discovery creates an investigation candidate",
     html:p(nativeIssue?"The observation mapper could not assign an end-of-turn state to a retained branch. The system records that obstacle and links it back to this game and the relevant source columns.":"The recorded outcome supplies an investigation candidate with its source links.")+
       stats([["case issue signatures",before.issue_ids.length],["engine bug established","No"]])+
       p("A diagnostic groups a symptom. It does not prove that this branch was the human's play or that no compatible trajectory exists. Other unchecked projections remain separate issues.","warning")+
       (nativeIssue?p("Boundary issue: "+nativeIssue.issue_id,"note"):"")+link(comparison.baseline_report_id,"Issue group and originating cases")},
    {id:"patch",x:790,y:475,kicker:"SEPARATE REPAIR PROCESS",title:"Propose an inspectability change",metric:"Retain actions, states and events",note:"Diagnosis supplied separately · origins linked",tone:"ink",
     heading:"Improve the evidence the machine keeps",
     html:p("The proposed change makes a failed fit inspectable: the candidate retains exact native transitions, field comparisons and a separate failure context. It also explains why certain fields remain unchecked.")+
       p(attribution.authority,"warning")+
       stats([["originating cases",attribution.origin_case_ids.length],["target component",attribution.component.replaceAll("_"," ")]])+
       p("The factory derives the case and feedback attribution from the baseline report. It did not autonomously establish the diagnosis or write this patch.")+
       link(attributionId,"Source-to-change attribution")+link(attribution.diagnosis_id,"Recorded diagnosis")+link(comparison.change_id,"Exact committed patch")},
    {id:"rerun",x:415,y:475,kicker:"CANDIDATE EXECUTION",title:"Rerun the same case",metric:a.nodes.toLocaleString()+" nodes · "+a.milestones_fitted+" / "+a.milestones_total+" keys",note:"Same cohort, runtime inputs and bounds",tone:"green",
     heading:"Measure the changed worker on the original game",
     html:p("The candidate uses the frozen source, runtime inputs, reconstruction policy and search limits. Its recorded outcome is "+afterLabel+".")+
       stats([["baseline search time",(b.elapsed_millis/1000).toFixed(3)+" s"],["candidate search time",(a.elapsed_millis/1000).toFixed(3)+" s"],["same witness actions",witnessSame?"Yes":"No"],["same node count",b.nodes===a.nodes?"Yes":"No"]])+
       p("The added trace contains two different views: the retained matched prefix and one separately identified unsuccessful branch. These are not the complete search tree.","note")+
       link(after.result_id,"Candidate result with native trace")},
    {id:"prefix",x:40,y:255,kicker:"EVIDENCE FROM THE RERUN",title:"Keep the successful prefix",metric:transitions.length+" actions · "+matched.length+" matched fields",note:temporal+" end-of-turn boundary · "+a.milestones_fitted+" player keys",tone:"green",
     heading:"A partial match has a concrete witness",
     html:p("The retained prefix includes "+transitions.map(simpleAction).filter(x=>x.startsWith("Play ")).join(", ")+". At its final sampled boundary, supported observations match.")+
       stats([["retained actions",transitions.length],["matching field comparisons",matched.length],["temporal boundaries",temporal],["fully covered milestones",a.fully_covered_milestones]])+
       table(["Recorded field","Expected","Engine projection"],matched.map(f=>[fieldLabel(f),f.expected,f.actual]))+
       '<details><summary>Inspect the '+transitions.length+' original actions</summary>'+table(["Index","Action","Player","After phase"],pathRows)+"</details>"+
       p("Two matched player-specific keys at one end-of-turn are not two completed turns. Unsupported observations prevent a complete-game compatibility claim.","note")+
       link(after.result_id,"Original actions, states and comparisons")},
    {id:"failure",x:415,y:255,kicker:"SEPARATE BRANCH FROM THE RERUN",title:"Inspect a branch that stops",metric:attempt?selectedAction:"No failure context retained",note:attempt?"Cleanup → discard → turn change":"No invented engine path",tone:"amber",
     heading:attempt?"Why this retained branch cannot be projected":"No retained failure branch",
     html:attempt?
       p("One explored branch reaches cleanup with "+bp.hand.length+" cards in the opponent's hand. The next legal action selects "+cardNames.join(", ")+" to discard. The engine advances to the following turn.")+
       mini+p("The boundary mapper requires a stable End snapshot and neutral events before TurnStarted. This action emits a discard first, so the mapper declines to assign actual end-of-turn field values.","warning")+
       p("This is not the recorded opponent's trajectory. The source instead records the following requirements:")+
       table(["Recorded opponent-turn requirement","Expected"],relevantSource.map(f=>[fieldLabel(f),f.expected]))+
       p("This explored branch has "+bp.battlefield.length+" opponent battlefield objects before the discard. Its failure is an investigation clue, not the established root cause of the game's failed fit.")+
       '<details open><summary>Original events from action '+esc(attempt.index)+"</summary>"+eventsMarkup+"</details>"+
       p("The failure branch retains "+failure.actions_before.length+" predecessor actions and this attempt's before/after states. Intermediate snapshots for the additional predecessor actions are absent; this view does not invent them.","note")+
       p("Recorded boundary actuals: "+(expectedFields.every(f=>f.actual===null)?"not assigned":"see original receipt")+".","note")+
       link(after.result_id,"Separate branch and original native events"):p("The native result has no separate failure context. No such path is reconstructed by this viewer.")},
    {id:"compare",x:40,y:475,kicker:"MEASURED COMPARISON",title:"What actually improved?",metric:before.status===after.status?"Same outcome · richer evidence":"Recorded outcome changed",note:"Comparison only · no accepted engine repair",tone:"ink",
     heading:"The improvement is inspectability",
     html:table(["Measurement","Baseline","Candidate"],[["Outcome",beforeLabel,afterLabel],["Nodes",b.nodes,a.nodes],["Matched milestone keys",b.milestones_fitted+"/"+b.milestones_total,a.milestones_fitted+"/"+a.milestones_total],["Fully covered milestones",b.fully_covered_milestones,a.fully_covered_milestones],["Retained typed trace",b.trace?"Present":"Absent",a.trace?"Present":"Absent"]])+
       stats([["remaining issue signatures",row.remaining_issue_ids.length],["signatures no longer reported",row.resolved_issue_ids.length],["new signatures",row.new_issue_ids.length]])+
       p(reasonOnly?changed.length+" constraint records changed only their reason annotations. Expected values, dispositions and projections are unchanged.":"Inspect the comparison's changed constraints before interpreting the result.","note")+
       p("The candidate lets us explain an existing obstacle. It does not improve observation coverage or establish a gameplay-correctness fix. The comparison records no acceptance decision.","warning")+
       link(comparisonId,"Full mechanical comparison")+link(comparison.candidate_report_id,"All 20 candidate cases")}
  ];
  $("status").textContent="Recorded run · "+checked+" artifacts checked";
  $("graph-caption").textContent="Arrows show evidence dependencies for this case. The trace nodes come from the rerun. Only retained paths are shown, not all "+a.nodes.toLocaleString()+" search nodes; playback is explanatory, not live computation.";
  $("progress").max=String(steps.length-1);
  renderGraph();
  ["play","previous","next","restart","progress"].forEach(id=>$(id).disabled=false);
  show(0);
  if(params.get("play")==="1" && !matchMedia("(prefers-reduced-motion: reduce)").matches) start();
}
const edges=[
  [0,1,"M330 100 H415"],[1,2,"M705 100 H790"],
  [2,3,"M935 165 V255"],[3,4,"M935 385 V475"],
  [4,5,"M790 540 H705"],
  [5,6,"M415 515 C350 515 365 350 330 320"],
  [5,7,"M560 475 V385"],
  [6,8,"M185 385 V475"],
  [7,8,"M415 350 C355 350 375 505 330 505"]
];
function renderGraph() {
  const svg=$("graph");
  svg.innerHTML='<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="context-stroke"/></marker></defs>'+
    '<text class="lane-label" x="40" y="675">DISCOVER → PROPOSE → RERUN → EXPLAIN → COMPARE</text>'+
    edges.map(([from,to,d],i)=>'<path class="edge" data-edge="'+i+'" data-from="'+from+'" data-to="'+to+'" d="'+d+'" marker-end="url(#arrow)"/>').join("")+
    steps.map((s,i)=>'<g class="node '+s.tone+'" data-step="'+i+'" transform="translate('+s.x+' '+s.y+')" tabindex="0" role="button" aria-label="Step '+(i+1)+': '+esc(s.title)+'. '+esc(s.metric)+'"><rect class="card" width="290" height="130" rx="14"/><text class="node-kicker" x="19" y="25">'+esc(s.kicker)+'</text><text class="node-title" x="19" y="52">'+esc(s.title)+'</text><text class="node-metric" x="19" y="80">'+esc(s.metric)+'</text><text class="node-note" x="19" y="103">'+esc(s.note)+'</text><circle class="node-number" cx="273" cy="9" r="14"/><text class="node-number-text" x="273" y="13" text-anchor="middle">'+(i+1)+'</text></g>').join("");
  svg.querySelectorAll(".node").forEach(node=>{
    const select=()=>{stop();show(Number(node.dataset.step));};
    node.addEventListener("click",select);
    node.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();select();}});
  });
  $("outline").innerHTML=steps.map((s,i)=>'<button type="button" data-step="'+i+'"><span>'+(i+1)+'</span>'+esc(s.title)+"</button>").join("");
  $("outline").querySelectorAll("button").forEach(b=>b.onclick=()=>{stop();show(Number(b.dataset.step));});
}
function show(index) {
  if (!steps.length) return;
  cursor=Math.max(0,Math.min(steps.length-1,index));
  const s=steps[cursor];
  $("graph").querySelectorAll(".node").forEach((n,i)=>{
    n.classList.toggle("active",i===cursor);n.classList.toggle("visited",i<cursor);
    n.setAttribute("aria-pressed",String(i===cursor));
  });
  $("graph").querySelectorAll(".edge").forEach(e=>{
    e.classList.toggle("active-edge",Number(e.dataset.to)===cursor);
    e.classList.toggle("visited",Number(e.dataset.from)<cursor && Number(e.dataset.to)<cursor);
  });
  $("outline").querySelectorAll("button").forEach((b,i)=>b.setAttribute("aria-current",String(i===cursor)));
  $("detail").innerHTML='<div class="eyebrow">STEP '+(cursor+1)+" / "+steps.length+" · "+esc(s.kicker)+"</div><h2>"+esc(s.heading)+"</h2>"+s.html;
  $("detail").scrollTop=0;
  $("progress").value=String(cursor);
  $("step-label").textContent=(cursor+1)+" / "+steps.length+" · "+s.title;
  $("previous").disabled=cursor===0;$("next").disabled=cursor===steps.length-1;
  if(cursor===steps.length-1)stop();
}
function stop(){if(timer)clearInterval(timer);timer=null;$("graph").classList.remove("playing");$("play").textContent="Play walkthrough";$("play").setAttribute("aria-pressed","false");}
function start(){if(!steps.length)return;$("graph").classList.add("playing");if(cursor===steps.length-1)show(0);$("play").textContent="Pause";$("play").setAttribute("aria-pressed","true");timer=setInterval(()=>show(cursor+1),5000);}
$("play").onclick=()=>timer?stop():start();
$("previous").onclick=()=>{stop();show(cursor-1);};
$("next").onclick=()=>{stop();show(cursor+1);};
$("restart").onclick=()=>{stop();show(0);};
$("progress").oninput=()=>{stop();show(Number($("progress").value));};
document.addEventListener("visibilitychange",()=>{if(document.hidden)stop();});
window.addEventListener("keydown",e=>{
  if(["INPUT","BUTTON","A","SUMMARY"].includes(document.activeElement?.tagName))return;
  if(e.key==="ArrowRight"){e.preventDefault();stop();show(cursor+1);}
  if(e.key==="ArrowLeft"){e.preventDefault();stop();show(cursor-1);}
});
["play","previous","next","restart","progress"].forEach(id=>$(id).disabled=true);
load().catch(error=>{
  stop();$("status").textContent="Evidence unavailable";
  $("error").hidden=false;$("error").textContent=error.message;
  ["play","previous","next","restart","progress"].forEach(id=>$(id).disabled=true);
});
