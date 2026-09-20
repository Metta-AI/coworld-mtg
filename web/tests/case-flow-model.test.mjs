import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {observedMoment,matchedSnapshot,groupCards,discardedCards,onlyReasonChanges} from "../public/case-flow-model.js";
const read=id=>JSON.parse(readFileSync(new URL("../../replays/17lands-trajectories-20260909-01/artifacts/"+id,import.meta.url),"utf8"));
const constraints=read("5d888c8aac7b719ad6ef73edbd9c8f423512170a92252ef6bcd0df08767760fe");
const result=read("a6f670f523a10b2e367e70da07e52cce41b30526483ef617c25922f7967afd56");
test("a counted source hand does not acquire the reconstructed engine identities",()=>{
  const b=observedMoment(constraints,1).players[1];
  assert.equal(b.handCount,7);
  assert.equal(b.hand,null);
  assert.deepEqual(b.lands,["Island"]);
  assert.deepEqual(b.played,["Terramorphic Expanse"]);
});
test("blank source land cells stay unknown rather than an empty battlefield",()=>{
  const first=observedMoment(constraints,0);
  assert.equal(first.players[1].lands,null);
  assert.deepEqual(first.players[0].lands,["Sundown Pass"]);
  assert.equal(first.players[0].handCount,6);
});
test("matched first-turn state is before transition10, never its already advanced endpoint",()=>{
  const match=matchedSnapshot(result.trace,0);
  assert.equal(match.index,10);assert.equal(match.side,"before");
  assert.equal(match.state.phase,"End");assert.equal(match.state.turn_owner,0);
  assert.equal(result.trace.transitions[10].after.phase,"Upkeep");
  assert.equal(match.matched.length,6);
  assert.equal(matchedSnapshot(result.trace,1),null);
});
test("missing retained snapshot cannot be reconstructed by the viewer",()=>{
  const trace=structuredClone(result.trace);
  trace.transitions=trace.transitions.filter(t=>t.index!==10);
  assert.throws(()=>matchedSnapshot(trace,0),/not retained/);
});
test("the discard demonstrates only its original snapshots and native zone change",()=>{
  const attempt=result.trace.failure.attempt;
  assert.equal(attempt.before.players[1].hand.length,8);
  assert.equal(attempt.after.players[1].hand.length,7);
  assert.deepEqual(discardedCards(attempt),[{object_id:42,name:"Forest"}]);
  assert.equal(attempt.after.players[1].graveyard_count,1);
  assert.equal(attempt.after.players[0].hand.length,6,"no next-turn draw is invented");
  assert.deepEqual(groupCards(attempt.before.players[1].hand),[
    {name:"Forest",count:1},{name:"Island",count:1},{name:"Terramorphic Expanse",count:1},{name:"Plains",count:5}
  ]);
});
test("a changed expected value must not be described as an annotation-only change",()=>{
  const c={kind:"observation_changed",before:{column:"life",expected:20,reason:"old"},after:{column:"life",expected:20,reason:"new"}};
  assert.equal(onlyReasonChanges([c]),true);
  c.after.expected=19;assert.equal(onlyReasonChanges([c]),false);
});
