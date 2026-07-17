use anyhow::{bail, Result};
use phase_bridge::{PhaseGame, StackEntryKind, Zone, SPECTATOR_ID};
use std::collections::BTreeMap;

pub(crate) fn validate_invariants(game: &PhaseGame) -> Result<()> {
    for seat in [0, 1] {
        let state = game.viewer_state(seat);
        let opponent = 1 - seat as usize;
        if state.players[opponent].hand.iter().any(|id| {
            state
                .objects
                .get(id)
                .is_none_or(|card| card.name != "Hidden Card" || !card.face_down)
        }) {
            bail!("hidden_information_leak: seat {seat} can inspect opponent hand");
        }
    }
    let spectator = game.viewer_state(SPECTATOR_ID);
    if spectator
        .players
        .iter()
        .flat_map(|player| player.hand.iter())
        .any(|id| {
            spectator
                .objects
                .get(id)
                .is_none_or(|card| card.name != "Hidden Card" || !card.face_down)
        })
    {
        bail!("hidden_information_leak: spectator can inspect a player hand");
    }

    let state = game.state();
    let mut zone_ids = BTreeMap::new();
    let mut check = |id: u64, zone: &'static str| -> Result<()> {
        if let Some(first_zone) = zone_ids.insert(id, zone) {
            bail!("zone_invariant: object {id} appears in both {first_zone} and {zone}");
        }
        if !state.objects.keys().any(|object_id| object_id.0 == id) {
            bail!("zone_invariant: zone {zone} references absent object {id}");
        }
        Ok(())
    };
    for player in &state.players {
        for id in &player.library {
            check(id.0, "library")?;
        }
        for id in &player.hand {
            check(id.0, "hand")?;
        }
        for id in &player.graveyard {
            check(id.0, "graveyard")?;
        }
        for id in &player.attraction_deck {
            check(id.0, "attraction_deck")?;
        }
        for id in &player.contraption_deck {
            check(id.0, "contraption_deck")?;
        }
    }
    for id in &state.battlefield {
        check(id.0, "battlefield")?;
    }
    for entry in &state.stack {
        // During CR 601.2 announcement, a pending spell remains in its origin
        // zone so cancellation can rewind it. Ability entry IDs are not zone
        // objects and may numerically collide with cards.
        let object_on_stack = state
            .objects
            .get(&entry.id)
            .is_some_and(|object| object.zone == Zone::Stack);
        let pending_cast_object = state
            .waiting_for
            .pending_cast_ref()
            .or(state.pending_cast.as_deref())
            .map(|pending| pending.object_id.0);
        if stack_entry_requires_unique_zone(
            entry.id.0,
            &entry.kind,
            pending_cast_object,
            object_on_stack,
        ) {
            check(entry.id.0, "stack")?;
        }
    }
    for id in &state.exile {
        check(id.0, "exile")?;
    }
    for id in &state.command_zone {
        check(id.0, "command_zone")?;
    }
    Ok(())
}

fn stack_entry_requires_unique_zone(
    entry_id: u64,
    kind: &StackEntryKind,
    pending_cast_object: Option<u64>,
    object_on_stack: bool,
) -> bool {
    matches!(kind, StackEntryKind::Spell { .. })
        && (pending_cast_object != Some(entry_id) || object_on_stack)
}

pub(crate) fn invariant_failure_signature(detail: &str) -> &str {
    if detail.starts_with("zone_invariant:") {
        "zone_invariant"
    } else if detail.starts_with("hidden_information_leak:") {
        "hidden_information_leak"
    } else {
        "invariant_failure"
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn only_committed_spell_stack_entries_require_a_unique_zone() {
        let spell: StackEntryKind = serde_json::from_value(json!({
            "type": "Spell",
            "data": { "card_id": 7 }
        }))
        .expect("spell stack entry should deserialize");
        let keyword_ability: StackEntryKind = serde_json::from_value(json!({
            "type": "KeywordAction",
            "data": {
                "action": {
                    "type": "Equip",
                    "data": { "equipment_id": 7, "target_creature_id": 8 }
                }
            }
        }))
        .expect("keyword ability stack entry should deserialize");

        assert!(stack_entry_requires_unique_zone(7, &spell, None, true));
        assert!(stack_entry_requires_unique_zone(7, &spell, Some(7), true));
        assert!(!stack_entry_requires_unique_zone(7, &spell, Some(7), false));
        assert!(stack_entry_requires_unique_zone(7, &spell, Some(8), false));
        assert!(!stack_entry_requires_unique_zone(
            7,
            &keyword_ability,
            None,
            false
        ));
    }
}
