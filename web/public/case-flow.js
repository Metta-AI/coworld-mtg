import {observedMoment, matchedSnapshot, groupCards, discardedCards, onlyReasonChanges} from "./case-flow-model.js?v=20260919";
const $ = id => document.getElementById(id);
const esc = value => String(value ?? "").replace(/[&<>"']/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const params = new URLSearchParams(location.search);
const run = params.get("run") || "17lands-trajectories-20260909-01";
const caseId = params.get("case") || "f12030d17b48417daf662d7754781c793580d37543a987ec50dcf813c44bfa6c";
const base = "/factory-api/runs/"+encodeURIComponent(run);
let replay, model, cursor=0, timer=null, turn=1, failureSide="before", checked=0, visuals={};
const cache=new Map();
const chapters=[
  ["Read the game","What the recording actually tells us"],
  ["Match the first turn","A small part the engine can explain"],
  ["Inspect a search branch","Where one attempted path leads"],
  ["Locate the obstacle","Why the comparison stops here"],
  ["Change the recorder","Keep enough evidence to investigate"],
  ["Check the rerun","What improved, and what remains"]
];
const paragraphs=text=>"<p>"+esc(text)+"</p>";
function assert(ok,message){if(!ok)throw new Error(message);}
const artifactUrl=id=>base+"/artifacts/"+encodeURIComponent(id);
const evidenceLink=(id,title)=>'<a class="evidence-link" target="_blank" rel="noopener" href="'+artifactUrl(id)+'">'+esc(title)+" ↗</a>";
function evidence(summary,body,links=""){
  return '<details class="evidence-details"><summary>'+esc(summary)+'</summary><div class="evidence-body">'+body+links+"</div></details>";
}
function facts(rows,headers=["Observation","Recorded value"]){
  const format=v=>Array.isArray(v)?v.join(", "):v==null?"Unknown":String(v);
  return '<div class="table-scroll"><table class="fact-table"><thead><tr>'+headers.map(h=>"<th>"+esc(h)+"</th>").join("")+"</tr></thead><tbody>"+rows.map(row=>"<tr>"+row.map(v=>"<td>"+esc(format(v))+"</td>").join("")+"</tr>").join("")+"</tbody></table></div>";
}
const metric=(label,value)=>'<div class="metric"><span class="value">'+esc(value)+'</span><span class="label">'+esc(label)+"</span></div>";
const banner=(title,text,good=false)=>'<div class="result-banner '+(good?"good":"caution")+'"><strong>'+esc(title)+"</strong><p>"+esc(text)+"</p></div>";
function allowedUrl(value,host){
  try { const url=new URL(value);return url.protocol==="https:" && url.hostname===host ? url.href : null; }catch{return null;}
}
function card(name,count=1,kind="",badge=""){
  const record=visuals[name],src=allowedUrl(record?.image_uri,"cards.scryfall.io");
  return '<button type="button" class="card-visual '+kind+'" data-card="'+esc(name)+'" aria-label="Inspect '+esc(name)+(count>1?", "+count+" copies":"")+'"><span class="card-image">'+
    (src?'<img src="'+esc(src)+'" alt="'+esc(name)+' card" loading="lazy" decoding="async" referrerpolicy="no-referrer">':"")+
    '<span class="card-fallback"'+(src?' hidden':"")+'>'+esc(name)+"</span>"+
    (count>1?'<span class="card-quantity">×'+count+"</span>":"")+
    (badge?'<span class="card-state-label">'+esc(badge)+"</span>":"")+
    '</span><span class="card-name">'+esc(name)+"</span></button>";
}
function cards(list,{kind="",highlight=null}={}){
  return '<div class="card-row">'+groupCards(list).map(c=>card(c.name,c.count,kind+(c.name===highlight?" highlight":""),c.name===highlight?"Selected":"")).join("")+"</div>";
}
function unknownHand(count){
  return '<div class="unknown-hand" aria-label="'+(count==null?"Unknown hand":count+" cards; identities not recorded")+'"><div class="card-backs" aria-hidden="true">'+
    Array.from({length:count==null?3:Math.min(count,7)},()=>'<span class="card-back"></span>').join("")+'</div><div><strong>'+(count==null?"Unknown":count+" cards")+'</strong><span>Card identities not recorded</span></div></div>';
}
const missing=text=>'<div class="missing">'+esc(text)+"</div>";
const zone=(name,body)=>'<section class="zone"><h4 class="zone-label">'+esc(name)+"</h4>"+body+"</section>";
const life=value=>'<span class="life-badge">'+(value==null?"Life unknown":esc(value)+" life")+"</span>";
const playerName=seat=>seat===0?"Player A":"Player B";
function sourceBoard(moment,focus,{label="17Lands recording",showPlayed=true}={}){
  const player=moment.players[focus],other=moment.players[1-focus];
  return '<section class="game-board recorded" data-board="recorded"><div class="board-topline"><span class="board-badge">OBSERVED</span><span>'+esc(playerName(moment.turnOwner)+" · end of turn "+moment.turnIndex)+'</span></div><h3 class="board-title">'+esc(label)+'</h3><div class="player-strip"><strong>'+playerName(focus)+"</strong>"+life(player.life)+"</div>"+
    (showPlayed && player.played ? zone("Land played this turn",cards(player.played,{kind:"compact"})):"")+
    zone("Lands observed at end of turn",player.lands===null?missing("Not recorded · no empty-board claim"):cards(player.lands))+
    zone("Hand · "+(player.handCount==null?"count unknown":player.handCount+" cards"),player.hand===null?unknownHand(player.handCount):cards(player.hand,{kind:"compact"}))+
    '<div class="other-player"><strong>'+playerName(other.seat)+'</strong> · '+esc(other.life??"?")+" life · "+esc(other.handCount??"?")+" cards in hand"+(other.lands?" · "+esc(other.lands.join(", ")):"")+"</div>"+
    '<p class="board-note">Selected recorded fields. Other permanents and missing substeps are not reconstructed here.</p></section>';
}
function engineBoard(state,focus,{label="Engine snapshot",subtitle="",highlight=null,graveyard=null}={}){
  const player=state.players.find(p=>p.seat===focus),other=state.players.find(p=>p.seat!==focus);
  assert(player,"Engine snapshot is missing its player.");
  return '<section class="game-board engine" data-board="engine"><div class="board-topline"><span class="board-badge">ENGINE HYPOTHESIS</span><span>'+esc(state.phase)+'</span></div><h3 class="board-title">'+esc(label)+'</h3>'+
    (subtitle?'<p class="board-subtitle">'+esc(subtitle)+"</p>":"")+
    '<div class="player-strip"><strong>'+playerName(focus)+"</strong>"+life(player.life)+"</div>"+
    zone("Battlefield",player.battlefield.length?cards(player.battlefield):missing("No cards in play"))+
    zone("Hand · "+player.hand.length+" cards",cards(player.hand,{kind:"compact",highlight}))+
    (graveyard!==null?zone("Graveyard · "+player.graveyard_count+" card"+(player.graveyard_count===1?"":"s"),graveyard.length?cards(graveyard,{kind:"compact highlight"}):missing("Empty")):"")+
    '<div class="other-player"><strong>'+playerName(other.seat)+"</strong> · "+other.life+" life · "+other.hand.length+" cards in hand"+(other.battlefield.length?" · "+esc(other.battlefield.map(c=>c.name).join(", ")):"")+"</div>"+
    '<p class="board-note">Exact retained state from one reconstructed setup. Player B’s card identities are hypothetical. Tap states are not retained.</p></section>';
}
function stage(index,heading,deck,body){
  return '<div class="chapter-tag">STEP '+(index+1)+" OF "+chapters.length+'</div><h2 class="stage-heading">'+esc(heading)+'</h2><p class="stage-deck">'+esc(deck)+"</p>"+body;
}
const pair=(left,right)=>'<div class="board-pair">'+left+right+"</div>";
const actionButton=(action,label,active=false)=>'<button type="button" data-action="'+action+'" class="'+(active?"active":"")+'" aria-pressed="'+active+'">'+label+"</button>";
function renderStage(){
  const m=model,{source,b,a,constraints,matched,failure,attempt,comparison,row,attribution}=m;
  const obsA=observedMoment(constraints,0),obsB=observedMoment(constraints,1);
  const selected=discardedCards(attempt),forest=selected[0]?.name || "the selected card";
  let content="";
  if(cursor===0){
    content=stage(0,"What happened in the recorded game?","Start with two snapshots from a real game. The recording gives us some cards and counts, but leaves out many intervening actions.",
      '<div class="state-tabs" aria-label="Recorded turn">'+actionButton("turn-a","Player A’s first turn",turn===0)+actionButton("turn-b","Player B’s first turn",turn===1)+"</div>"+
      '<div class="scene-grid">'+sourceBoard(turn===0?obsA:obsB,turn,{showPlayed:false})+
      '<section class="explanation"><span class="chapter-tag">THE QUESTION</span><h3>Can the engine reach these observations?</h3>'+
      paragraphs(turn===1?"The recording says Player B played Terramorphic Expanse, then ended the turn with Island in play and seven cards in hand.":"The recording says Player A played Sundown Pass, then ended the turn with six cards in hand. Both players have 20 life.")+
      (turn===1?'<div class="observed-land-story"><div>'+card("Terramorphic Expanse",1,"compact")+'<span>Recorded as played</span></div><div class="missing-substeps">Substeps<br>not shown</div><div>'+card("Island",1,"compact")+'<span>Observed at turn end</span></div></div>':"")+
      '<p class="scope-note">These are separate recorded facts. This view does not infer a particular activation or sacrifice sequence between them.</p>'+
      '<h3>Give the engine room to fill the gaps</h3>'+paragraphs("The fitter tries legal actions between recorded moments. Missing opponent cards require a guessed starting setup; those guesses must remain separate from observations.")+
      '<p class="scope-note">Player A is the player whose game was logged; Player B is their opponent. This case covers the first two turns per player, not the full game.</p></section></div>'+
      evidence("See the original fields and setup",facts((turn===0?obsA:obsB).fields.filter(f=>f.disposition==="enforced").map(f=>[f.column,f.expected]))+
      paragraphs("Both recorded mulligan counts are zero. Previously inspected source row "+source.selection.source_row_index+" was kept in the cohort without filtering on the fit result."),
      evidenceLink(caseId,"Case and sampling record")+evidenceLink(source.source_id,"Original CSV")+evidenceLink(m.after.constraints_id,"Constraints and assumptions")));
  }else if(cursor===1){
    content=stage(1,"The engine explains Player A’s first turn","Playing Sundown Pass leaves six cards in Player A’s hand. At this moment, all six enforced comparisons agree.",
      banner("A real partial match","Both players are checked at this one turn boundary. That is what the older “2 / 8 milestone keys” count means.",true)+
      pair(sourceBoard(obsA,0,{showPlayed:false}),engineBoard(matched.state,0,{label:"Matched end of Player A’s turn",subtitle:"The retained state before the engine starts Player B’s turn."}))+
      evidence("Inspect the matching fields and legal actions",facts(matched.matched.map(f=>[f.source_field_id,Array.isArray(f.expected)?f.expected.join(", "):f.expected,Array.isArray(f.actual)?f.actual.join(", "):f.actual]),["Field","Recording","Engine"])+
      paragraphs("The comparison uses action "+matched.index+"'s "+matched.side+" state. The later state has already advanced to the opponent’s upkeep.")+
      facts(a.trace.transitions.map(t=>[t.index,playerName(t.seat),t.action.type,t.after.phase]),["Action","Player","Submitted action","After phase"]),
      evidenceLink(m.after.result_id,"Native trace"))+
      '<p class="scope-note">Only the supported observations match. Mana, combat and other unsupported fields still prevent a fully checked turn. This detailed trace comes from the later rerun.</p>');
  }else if(cursor===2){
    const after=failureSide==="after",state=after?attempt.after:attempt.before;
    content=stage(2,"One explored branch takes a different path","The source expects Island in play. This retained branch passes without playing a land, reaches eight cards, and must discard.",
      '<div class="transition-controls"><div><span class="label">Inspect the retained engine action</span><strong>'+esc("Discard "+forest)+'</strong></div><div class="state-tabs">'+actionButton("before-discard","Before discard",!after)+actionButton("after-discard","After discard",after)+'</div><button type="button" class="primary action-forward" data-action="'+(after?"before-discard":"after-discard")+'">'+(after?"Reset action":"Step through discard →")+"</button></div>"+
      pair(sourceBoard(obsB,1,{label:"What the recording requires",showPlayed:false}),
      engineBoard(state,1,{label:after?"The branch after discarding":"The branch before discarding",subtitle:after?"Now Player A’s upkeep. The next draw has not happened.":"Cleanup at the end of Player B’s turn.",highlight:after?null:forest,graveyard:after?selected:[]}))+
      '<div class="event-strip" aria-label="Events recorded in this one action"><span class="event-step '+(after?"done":"")+'">Forest: hand → graveyard</span><span class="event-step '+(after?"done":"")+'">Next turn starts</span><span class="event-step '+(after?"done":"")+'">Player A’s upkeep</span></div>'+
      banner("This is one engine branch, not the recorded play","The named opponent hand belongs to the reconstructed setup. Seeing this branch fail does not prove that the game is impossible or that the engine broke a Magic rule.")+
      evidence("Inspect the original action and its scope",facts([["Submitted action",attempt.action.type],["Action index",attempt.index],["Predecessor actions retained",failure.actions_before.length],["Before phase",attempt.before.phase],["After phase",attempt.after.phase],["Unassigned boundary comparisons",failure.milestones.flatMap(x=>x.fields).filter(f=>f.disposition==="enforced"&&f.actual===null).length]])+
      facts(attempt.events.map(e=>[e.type,e.type==="ZoneChanged"?(e.data.record?.name+": "+e.data.from+" → "+e.data.to):""]),["Native event","Detail"])+
      paragraphs("This step switches between the exact before and after snapshots of action "+attempt.index+". It does not invent intermediate board states. The extra predecessor actions do not have retained intermediate snapshots."),
      evidenceLink(m.after.result_id,"Failed branch, states and events")));
  }else if(cursor===3){
    content=stage(3,"The comparison cannot find a safe turn-end snapshot","A single engine action both discards the card and advances the turn. Our observation mapper cannot reliably choose the end-of-turn state from this transition.",
      '<div class="mechanism"><div class="mechanism-step"><span class="label">Snapshot before action</span><h3>Cleanup · 8 cards</h3>'+card(forest,1,"compact highlight")+paragraphs("The discard still has to happen.")+'</div><div class="mechanism-step mechanism-events"><span class="label">Inside one engine action</span><h3>Discard, then change turn</h3>'+paragraphs("Forest leaves the hand. The next turn starts. The retained events describe both changes.")+'</div><div class="mechanism-step"><span class="label">Snapshot after action</span><h3>Upkeep · 7 cards</h3>'+paragraphs("The engine is already in Player A’s next turn.")+"</div></div>"+
      banner("The result is “unsupported turn boundary”","The mapper expects a stable End-phase snapshot with only neutral events before the turn changes. Cleanup plus a discard does not meet that assumption, so it leaves the required values unassigned.")+
      '<div class="explanation-grid"><section class="explanation"><h3>What was discovered?</h3>'+paragraphs("A concrete limit in how our software interprets the engine’s states. The source game raised the question; the search exposed a transition the mapper does not handle.")+'</section><section class="explanation"><h3>What remains open?</h3>'+paragraphs("The retained branch also has no Island in play. Fixing this boundary limitation alone would not establish a full fit. Other branches, hidden setups and unsupported abilities still need investigation.")+"</section></div>"+
      evidence("See the precise diagnostic and source-linked issue",paragraphs(failure.detail)+
      paragraphs("Ability ID 88024 in the recorded opponent turn is also unsupported. Card identity resolution is not proof that every card effect is implemented."),
      evidenceLink(m.comparison.baseline_report_id,"Baseline issue origins")+evidenceLink(m.after.result_id,"Native failure context")));
  }else if(cursor===4){
    content=stage(4,"The change makes failed fits explainable","The first run reported the obstacle. A separate diagnosis led to a recorder change: keep the actions, states and events needed to inspect it.",
      '<div class="change-pair"><section class="explanation old-recorder"><span class="board-badge">BEFORE</span><h3>A result without the scene</h3><div class="old-result">unsupported_boundary</div>'+paragraphs("A status and a partial witness tell us where to investigate, but do not show the board around the failed comparison.")+'</section><section class="explanation new-recorder"><span class="board-badge">AFTER</span><h3>The attempted action and both states</h3><div class="change-visual">'+card(forest,1,"compact")+'<div><strong>8 cards → 7 cards</strong><p>Cleanup → discard → upkeep</p><span class="count-pill">States + native events</span></div></div>'+paragraphs("The rerun supplies the concrete branch we just inspected, with unknown values and unchecked fields still labeled.")+"</section></div>"+
      banner("This patch improves the explanation","It does not make the missing Island appear, add new card support, or repair the turn-boundary mapper.",true)+
      '<div class="explanation"><h3>Keep discovery and fixing separate</h3>'+paragraphs("The factory links the proposed patch back to "+attribution.origin_case_ids.length+" originating cases and their feedback. The diagnosis and code change were supplied separately; discovery did not automatically prove or fix the cause.")+"</div>"+
      evidence("Inspect the change and its attribution",paragraphs(attribution.authority),
      evidenceLink(m.attributionId,"Origin cases and feedback")+evidenceLink(attribution.diagnosis_id,"Diagnosis")+evidenceLink(comparison.change_id,"Exact patch")));
  }else{
    content=stage(5,"The rerun is easier to understand, but still blocked","The same game, runtime inputs and search limits produce the same outcome. What changed is the evidence available to explain it.",
      '<div class="metric-grid">'+metric("Search states, before and after",a.nodes.toLocaleString())+metric("Matched turn boundaries","1 of 4")+metric("Fully checked turns","0")+metric("Issue signatures remaining",row.remaining_issue_ids.length)+"</div>"+
      facts([["Outcome","Unsupported turn boundary","Unsupported turn boundary"],["Search states",b.nodes,a.nodes],["Supported first-turn checks","6 matched","6 matched"],["Witness actions","Same","Same"],["States and events around failure",b.trace?"Retained":"Not retained","Retained"],["Observation coverage","Partial","Unchanged"]],["This case","Before","After"])+
      banner("Useful progress, with a specific next problem","We can now inspect the failed comparison. Reconstructing more hidden states, handling turn boundaries and checking more observations remain separate work.")+
      '<div class="explanation"><h3>What the full 20-game run found</h3>'+paragraphs("Both workers produced eight partial matches, nine unsupported mulligan inputs, one unsupported boundary, and two timeouts. No cases were dropped, and this run established no engine rules defect.")+"</div>"+
      evidence("Inspect the measured comparison",paragraphs(onlyReasonChanges(m.changed)?m.changed.length+" constraint records changed only their explanatory reason. Expected values, dispositions and projections are unchanged.":"Inspect changed constraints before interpreting the comparison.")+
      paragraphs("All 20 games were previously inspected, not an unseen holdout. Search time can vary; the case used "+a.nodes+" nodes in both runs."),
      evidenceLink(m.comparisonId,"Before/after comparison")+evidenceLink(comparison.candidate_report_id,"All candidate cases")));
  }
  $("detail").innerHTML=content;
  $("detail").querySelectorAll("[data-action]").forEach(button=>button.onclick=()=>{
    stop();const action=button.dataset.action;
    if(action==="turn-a")turn=0;
    if(action==="turn-b")turn=1;
    if(action==="before-discard")failureSide="before";
    if(action==="after-discard")failureSide="after";
    renderStage();
  });
  bindCards($("detail"));
}
function bindCards(root){
  root.querySelectorAll("[data-card]").forEach(button=>button.onclick=()=>openCard(button.dataset.card));
  root.querySelectorAll(".card-image img").forEach(img=>{
    const failed=()=>{img.hidden=true;img.parentElement.querySelector(".card-fallback").hidden=false;};
    img.addEventListener("error",failed,{once:true});if(img.complete && !img.naturalWidth)failed();
  });
}
function openCard(name){
  stop();const meta=visuals[name],url=allowedUrl(meta?.scryfall_uri,"scryfall.com"),src=allowedUrl(meta?.image_uri,"cards.scryfall.io");
  $("card-dialog-content").innerHTML='<div class="card-dialog-layout">'+(src?'<img class="dialog-card-image" src="'+esc(src)+'" alt="'+esc(name)+' card" referrerpolicy="no-referrer">':'<div class="missing">'+esc(name)+"</div>")+
    '<div class="card-dialog-copy"><span class="chapter-tag">CARD REFERENCE</span><h2 id="dialog-card-name">'+esc(name)+"</h2>"+
    (meta?.type_line?paragraphs(meta.type_line):"")+paragraphs("Representative card art matched by name. This is not proof of the exact printing or artwork used in the recorded game.")+
    '<p class="card-attribution">Card images via Scryfall. Magic: The Gathering card art and text © Wizards of the Coast.'+(meta?.artist?" Illustration: "+esc(meta.artist)+".":"")+"</p>"+
    (url?'<a class="evidence-link" target="_blank" rel="noopener" href="'+esc(url)+'">View card on Scryfall ↗</a>':"")+"</div></div>";
  const img=$("card-dialog-content").querySelector("img");
  if(img)img.onerror=()=>{img.hidden=true;img.insertAdjacentHTML("afterend",missing("Image unavailable · "+name));};
  $("card-dialog").setAttribute("aria-labelledby","dialog-card-name");$("card-dialog").showModal();
}
function renderNavigation(){
  $("outline").innerHTML=chapters.map(([title,subtitle],i)=>'<button type="button" data-step="'+i+'" aria-current="'+(i===cursor?"step":"false")+'"><span class="step-number">'+(i+1)+'</span><span><strong>'+esc(title)+'</strong><small>'+esc(subtitle)+"</small></span></button>").join("");
  $("outline").querySelectorAll("button").forEach(button=>button.onclick=()=>{stop();show(Number(button.dataset.step));});
  $("graph").innerHTML='<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#799482"/></marker></defs>'+
    chapters.map(([title],i)=>'<g class="node '+(i===cursor?"active":"")+'" transform="translate(12 '+(20+i*88)+')" role="button" tabindex="0" data-step="'+i+'" aria-label="'+esc(title)+'"><rect class="card" width="236" height="58" rx="9"/><text x="13" y="23">'+(i+1)+". "+esc(title)+'</text><text class="map-note" x="13" y="42">'+(i===1||i===2?"Shown using the later trace":"Case evidence")+"</text></g>"+(i<5?'<path class="edge" d="M130 '+(78+i*88)+' V'+(108+i*88)+'" marker-end="url(#arrow)"/>':"")).join("");
  $("graph").querySelectorAll(".node").forEach(node=>{
    const select=()=>{stop();show(Number(node.dataset.step));};
    node.onclick=select;node.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();select();}};
  });
}
function show(index){
  if(!model)return;
  cursor=Math.max(0,Math.min(chapters.length-1,index));
  renderNavigation();renderStage();
  $("progress").value=cursor;$("step-label").textContent=(cursor+1)+" / "+chapters.length+" · "+chapters[cursor][0];
  $("previous").disabled=cursor===0;$("next").disabled=cursor===chapters.length-1;
  if(cursor===chapters.length-1)stop();
}
function stop(){if(timer)clearInterval(timer);timer=null;$("play").textContent="Play walkthrough";$("play").setAttribute("aria-pressed","false");}
function start(){if(!model)return;if(cursor===chapters.length-1)show(0);$("play").textContent="Pause";$("play").setAttribute("aria-pressed","true");timer=setInterval(()=>show(cursor+1),9000);}
async function getJSON(url){const r=await fetch(url,{cache:"no-store"});assert(r.ok,"Evidence service returned "+r.status+".");return r.json();}
async function artifact(id){
  assert(/^[a-f0-9]{64}$/.test(id||"")&&replay.artifacts[id],"The replay does not contain the required evidence.");
  if(!cache.has(id))cache.set(id,(async()=>{
    const r=await fetch(artifactUrl(id),{cache:"no-store"});assert(r.ok,"Evidence artifact could not be loaded.");
    const bytes=await r.arrayBuffer();
    const digest=[...new Uint8Array(await crypto.subtle.digest("SHA-256",bytes))].map(b=>b.toString(16).padStart(2,"0")).join("");
    assert(digest===id,"Artifact bytes do not match their recorded identity.");
    checked++;return JSON.parse(new TextDecoder().decode(bytes));
  })());return cache.get(id);
}
function sourceIds(provider){return replay.events.filter(e=>e.payload.kind==="source_imported"&&e.payload.source.provider===provider).map(e=>e.payload.source.snapshot_id);}
async function load(){
  const artRequest=getJSON(new URL("./case-flow-cards.json?v=20260919",import.meta.url)).then(v=>visuals=v.cards||{}).catch(()=>{visuals={};});
  replay=await getJSON(base+"/replay.json");
  assert(replay.run_id===run&&Array.isArray(replay.events)&&replay.artifacts,"Unexpected replay format.");
  assert(caseId==="f12030d17b48417daf662d7754781c793580d37543a987ec50dcf813c44bfa6c","This guided story currently covers source row 8. Use the full replay for other cases.");
  const comparisonId=sourceIds("17Lands trajectory discovery comparison").at(-1),comparison=await artifact(comparisonId);
  assert(comparison.schema==="coworld/17lands-discovery-comparison@1","Unsupported comparison schema.");
  const [beforeReport,afterReport]=await Promise.all([artifact(comparison.baseline_report_id),artifact(comparison.candidate_report_id)]);
  const before=beforeReport.cases.find(c=>c.case_id===caseId),after=afterReport.cases.find(c=>c.case_id===caseId);
  assert(before?.result_id&&after?.result_id,"This case requires both native results.");
  const [source,b,a,constraints]=await Promise.all([artifact(caseId),artifact(before.result_id),artifact(after.result_id),artifact(after.constraints_id)]);
  assert(a.trace?.schema==="coworld-17lands-fit-trace-v1","This case needs a supported native trace.");
  const ids=sourceIds("17Lands trajectory repair attribution"),records=await Promise.all(ids.map(artifact));
  const attribution=records.find(r=>r.change_id===comparison.change_id);
  assert(attribution?.origin_case_ids.includes(caseId),"This change is not attributed to the case.");
  const row=comparison.rows.find(r=>r.case_id===caseId),matched=matchedSnapshot(a.trace,0),failure=a.trace.failure,attempt=failure?.attempt;
  assert(row&&matched&&failure?.path_kind==="separate_search_branch"&&attempt,"The expected retained states are absent.");
  assert(attempt.action.type==="SelectCards"&&discardedCards(attempt).some(c=>c.name==="Forest"),"This story requires the retained Forest discard branch.");
  model={source,b,a,constraints,matched,failure,attempt,comparison,row,attribution,before,after,comparisonId,attributionId:ids[records.indexOf(attribution)],changed:(comparison.scope_changes||[]).filter(c=>c.case_id===caseId)};
  await artRequest;
  $("full-replay").href="/client/factory.html?"+new URLSearchParams({run,case:caseId,report:comparison.candidate_report_id});
  $("title").textContent="Why this game stopped matching";
  $("subtitle").textContent="See what 17Lands recorded, what the engine tried, and what changed afterward.";
  $("status").textContent="Real game · source row 8";
  $("graph-caption").textContent="A guided reading of this case’s evidence. Detailed states come from the instrumented rerun; this is not the full search tree.";
  $("progress").max=chapters.length-1;
  ["play","previous","next","restart","progress"].forEach(id=>$(id).disabled=false);
  const requested=Number(params.get("step"));show(Number.isInteger(requested)&&requested>=1&&requested<=6?requested-1:0);
  if(params.get("play")==="1"&&!matchMedia("(prefers-reduced-motion: reduce)").matches)start();
}
$("play").onclick=()=>timer?stop():start();
$("previous").onclick=()=>{stop();show(cursor-1);};$("next").onclick=()=>{stop();show(cursor+1);};
$("restart").onclick=()=>{stop();turn=1;failureSide="before";show(0);};
$("progress").oninput=()=>{stop();show(Number($("progress").value));};
$("card-dialog-close").onclick=()=>$("card-dialog").close();
$("card-dialog").addEventListener("click",e=>{if(e.target===$("card-dialog"))$("card-dialog").close();});
document.addEventListener("visibilitychange",()=>{if(document.hidden)stop();});
document.addEventListener("keydown",e=>{
  if($("card-dialog").open||["INPUT","BUTTON","A","SUMMARY"].includes(document.activeElement?.tagName))return;
  if(e.key==="ArrowRight"){e.preventDefault();stop();show(cursor+1);}
  if(e.key==="ArrowLeft"){e.preventDefault();stop();show(cursor-1);}
});
["play","previous","next","restart","progress"].forEach(id=>$(id).disabled=true);
load().catch(error=>{
  stop();model=null;$("status").textContent="Evidence unavailable";$("error").hidden=false;$("error").textContent=error.message;
  ["play","previous","next","restart","progress"].forEach(id=>$(id).disabled=true);
});
