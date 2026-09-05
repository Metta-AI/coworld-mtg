//! Event-time trigger suppression through the public cast/apply pipeline.
//! Named cards use verified Oracle; other fixtures exercise typed building blocks.

use engine::game::functioning_abilities::{active_trigger_definitions, battlefield_active_statics};
use engine::game::scenario::{GameScenario, P0};
use engine::types::ability::{AbilityDefinition, Effect};
use engine::types::game_state::{GameState, WaitingFor};
use engine::types::identifiers::ObjectId;
use engine::types::mana::{ManaCost, ManaCostShard, ManaType, ManaUnit};
use engine::types::phase::Phase;
use engine::types::statics::{StaticMode, SuppressedTriggerEvent};
use engine::types::zones::Zone;

const HUSHBRINGER: &str = "Flying, lifelink\nCreatures entering or dying don't cause abilities to trigger.";
const TRAVELER: &str = "When this creature dies, create a 1/1 white Spirit creature token with flying.";
const WRATH: &str = "Destroy all creatures. They can't be regenerated.";

fn scenario() -> GameScenario {
    let mut s = GameScenario::new();
    s.at_phase(Phase::PreCombatMain);
    s
}

fn hush(s: &mut GameScenario) -> ObjectId {
    s.add_creature(P0, "Hushbringer", 1, 2)
        .from_oracle_text_with_keywords(&["Flying", "Lifelink"], HUSHBRINGER)
        .id()
}

fn traveler(s: &mut GameScenario) -> ObjectId {
    s.add_creature_from_oracle(P0, "Doomed Traveler", 1, 1, TRAVELER).id()
}

fn wrath(s: &mut GameScenario) -> ObjectId {
    s.with_mana_pool(P0, vec![ManaType::White, ManaType::White, ManaType::Colorless, ManaType::Colorless]
        .into_iter().map(|color| ManaUnit::new(color, ObjectId(0), false, vec![])).collect());
    s.add_spell_to_hand_from_oracle(P0, "Wrath of God", false, WRATH)
        .with_mana_cost(ManaCost::Cost { shards: vec![ManaCostShard::White, ManaCostShard::White], generic: 2 })
        .id()
}

fn spirits(state: &GameState) -> usize {
    state.battlefield.iter().filter(|id| {
        let obj = &state.objects[id];
        obj.name == "Spirit" && obj.is_token
    }).count()
}

fn assert_implemented(ability: &AbilityDefinition) {
    assert!(!matches!(*ability.effect, Effect::Unimplemented { .. }), "unimplemented fixture: {ability:?}");
    if let Some(next) = &ability.sub_ability { assert_implemented(next); }
}

fn assert_fixture(state: &GameState, ids: &[ObjectId], expected_hush: Option<ObjectId>) {
    for id in ids {
        let obj = &state.objects[id];
        for ability in obj.abilities.iter() { assert_implemented(ability); }
        for (_, trigger) in active_trigger_definitions(state, obj) {
            if let Some(ability) = &trigger.execute { assert_implemented(ability); }
        }
    }
    let suppressors: Vec<_> = battlefield_active_statics(state).filter(|(_, def)| {
        matches!(&def.mode, StaticMode::SuppressTriggers { events, .. } if events.contains(&SuppressedTriggerEvent::Dies))
    }).map(|(obj, _)| obj.id).collect();
    assert_eq!(suppressors, expected_hush.into_iter().collect::<Vec<_>>());
}

fn oracle_wrath(hush_first: bool, with_hush: bool) {
    let mut s = scenario();
    let h = (with_hush && hush_first).then(|| hush(&mut s));
    let t = traveler(&mut s);
    let h = h.or_else(|| with_hush.then(|| hush(&mut s)));
    let w = wrath(&mut s);
    let mut runner = s.build();
    assert_fixture(runner.state(), &[t, w], h);
    if let Some(h) = h { assert_fixture(runner.state(), &[h], Some(h)); }
    let result = runner.cast(w).resolve();
    result.assert_zone(&[t, w], Zone::Graveyard);
    if let Some(h) = h { result.assert_zone(&[h], Zone::Graveyard); }
    assert!(result.state().stack.is_empty());
    assert!(matches!(result.final_waiting_for(), WaitingFor::Priority { .. }));
    // CR 603.10a: the functioning pre-event suppressor applies to simultaneous deaths.
    assert_eq!(spirits(result.state()), usize::from(!with_hush), "simultaneous-death-suppressed; hush_first={hush_first}");
}

#[test]
fn oracle_wrath_hush_first_suppresses_simultaneous_traveler_death() { oracle_wrath(true, true); }
#[test]
fn oracle_wrath_traveler_first_suppresses_simultaneous_traveler_death() { oracle_wrath(false, true); }
#[test]
fn oracle_wrath_without_hush_creates_exactly_one_spirit() { oracle_wrath(true, false); }
