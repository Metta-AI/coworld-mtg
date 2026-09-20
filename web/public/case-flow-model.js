/** Source observations and engine snapshots remain separate, including their unknowns. */
export function observedMoment(constraints, turnOwner, turnIndex = 1) {
  const fields = constraints.fields.filter(f => f.milestone?.turn_owner === turnOwner &&
    f.milestone.turn_index === turnIndex && f.milestone.boundary === "end_of_turn");
  const players = [0, 1].map(seat => {
    const forSeat = fields.filter(f => f.milestone.observed_player === seat && f.disposition === "enforced");
    const value = projection => forSeat.find(f => f.projection === projection)?.expected ?? null;
    const hand = value("hand");
    return { seat, life: value("life"), hand, handCount: hand?.length ?? value("hand_count"),
      lands: value("lands"), played: value("land_played"), fields: forSeat };
  });
  return {turnOwner, turnIndex, players, fields};
}
export function matchedSnapshot(trace, turnOwner, turnIndex = 1) {
  const milestones = trace.milestones.filter(m => m.key.turn_owner === turnOwner &&
    m.key.turn_index === turnIndex && m.fields.some(f => f.comparison === "matched"));
  if (!milestones.length) return null;
  const refs = new Set(milestones.map(m => JSON.stringify([m.transition_index, m.state_position])));
  if (refs.size !== 1) throw new Error("Matched observations refer to different engine moments.");
  const {transition_index:index, state_position:position} = milestones[0];
  const transition = trace.transitions.find(t => t.index === index);
  const side = position === "before_transition" ? "before" : position === "after_transition" ? "after" : null;
  if (!transition || !side) throw new Error("The matched engine snapshot is not retained.");
  return {state:transition[side], index, side, milestones,
    matched:milestones.flatMap(m => m.fields.filter(f => f.comparison === "matched"))};
}
export function groupCards(cards) {
  const groups = new Map();
  for (const card of cards || []) {
    const name = typeof card === "string" ? card : card.name;
    groups.set(name, (groups.get(name) || 0) + 1);
  }
  return [...groups].map(([name,count])=>({name,count}));
}
export function discardedCards(attempt) {
  return (attempt?.events || []).filter(e => e.type === "ZoneChanged" &&
    e.data.from === "Hand" && e.data.to === "Graveyard").map(e=>({
      object_id:e.data.object_id, name:e.data.record?.name || "Unknown card"
    }));
}
export function onlyReasonChanges(changes) {
  const stable = value => JSON.stringify(Object.entries(value || {}).filter(([k])=>k !== "reason").sort(([a],[b])=>a.localeCompare(b)));
  return changes.length > 0 && changes.every(c=>c.kind==="observation_changed" && stable(c.before)===stable(c.after));
}
