# Physical production paths and maintainer simulation

Final source885baf9780651ece1b38291acbcfa2ab2cb766defd3fe49671ace1ca40a73d0b. This is an executor handoff with unresolved moved/adjacent CR and native-library runtime obligations. See unresolved-review-items.json and the implementation report;67 measured mutations do not establish implementation completion.

This map retains each comparison’s actual source and compilation method. It does not turn private contracts into public producer proofs. The linked JSON carries exact transformations, runtime counts, assertion excerpts, complete source/archive identities and restored commands for every row.

Distinct seams: 67; classifications: {'public': 56, 'private': 10, 'defensive': 1}.

## augment-handoff

public runtime mutation.

Physical source: `crates/engine/src/game/augment.rs`. Entry: crates/engine/src/game/augment.rs::check_standalone_augment_permanents

First branch: Public typed Animate grants only Augment to a healthy nonmerged subject; observer gets lethal damage, ordinary lethal category removes observer before standalone Augment removes subject in same SBA iteration.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Keyword absent and surviving observer; functioning surviving Hush changes +1 to0.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff`

```text
thread 'trigger_suppression_event_timing::augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff' (3264936) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 1, got 0 (before 20, final 20)
  left: 0
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff ... FAILED
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## destroy-resolve

public runtime mutation.

Physical source: `crates/engine/src/game/effects/destroy.rs`. Entry: crates/engine/src/game/effects/destroy.rs::resolve

First branch: Public single Effect::Destroy with SelfRef or already-valid target set; separate physical targets belong to one completed instruction.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Both target intent orders; no Hush; partially illegal, indestructible, prohibited/regenerated victims keep native exclusion.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `two_target_destroy_owns_one_event_in_both_target_orders`

```text
thread 'trigger_suppression_event_timing::two_target_destroy_owns_one_event_in_both_target_orders' (3270119) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:339:13:
assertion `left == right` failed
  left: 1
 right: 0
test trigger_suppression_event_timing::two_target_destroy_owns_one_event_in_both_target_orders ... FAILED
COST_COMPONENT_PROOF deferred=false with_hush=true traveler_first=true spirits=0 expected=0 h_peers=[] t_peers=[] t_snapshot={"after":["EntersBattlefield","Dies"],"before":["EntersBattlefield","Dies"]} life=22 zones=[Graveyard, Graveyard, Graveyard]
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## destroy-resolve_all

public runtime mutation.

Physical source: `crates/engine/src/game/effects/destroy.rs`. Entry: crates/engine/src/game/effects/destroy.rs::resolve_all

First branch: Public real Oracle Wrath; effective mass target filter selects simultaneous live creature victims.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Oracle Wrath reverse insertion and no-Hush exact1 Spirit; source-strip/phasing/controller and replacement controls.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `oracle_wrath_hush_first_suppresses_simultaneous_traveler_death`

```text
thread 'trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death' (3279430) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:135:5:
assertion `left == right` failed: simultaneous-death-suppressed; hush_first=true
  left: 1
 right: 0
test trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death ... FAILED
test trigger_suppression_event_timing::natural_effect_zone_choice_finalizes_before_chained_hush_departure ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## keep-sweep

public runtime mutation.

Physical source: `crates/engine/src/game/effects/choose_and_sacrifice_rest.rs`. Entry: crates/engine/src/game/effects/choose_and_sacrifice_rest.rs::sacrifice_unchosen

First branch: All final keep choices complete; shared sacrifice_unchosen recomputes scoped, matching, not-kept victims. Five entry routes all reach this one helper.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Category empty/automatic/manual, APNAP/total-power terminal routes; opponent scope/current controller; empty sweep.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `completed_keep_sacrifice_sweeps_share_one_boundary_across_choice_routes`

```text
thread 'trigger_suppression_event_timing::completed_keep_sacrifice_sweeps_share_one_boundary_across_choice_routes' (3285142) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:819:17:
assertion `left == right` failed: route=0, hush_first=false
  left: 1
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::completed_keep_sacrifice_sweeps_share_one_boundary_across_choice_routes ... FAILED
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## change-zone-resolve

public runtime mutation.

Physical source: `crates/engine/src/game/effects/change_zone.rs`. Entry: crates/engine/src/game/effects/change_zone.rs::resolve

First branch: Public targeted ChangeZone; target validation and actual current source zone precede process_one_zone_move.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Targeted Graveyard/exile/bounce/native selected group, replacement skip/pause; ordinary no-Hush1.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `remaining_complete_producers_capture_each_actual_group`

```text
thread 'trigger_suppression_event_timing::remaining_complete_producers_capture_each_actual_group' (3292507) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
test trigger_suppression_event_timing::remaining_complete_producers_capture_each_actual_group ... FAILED
test trigger_suppression_event_timing::opponent_scoped_keep_sweep_preserves_owner_and_out_of_scope_board ... ok
test trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility ... ok
test trigger_suppression_event_timing::repeated_object_id_retains_distinct_incarnation_and_event_suppression ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## change-zone-resolve_all

public runtime mutation.

Physical source: `crates/engine/src/game/effects/change_zone.rs`. Entry: crates/engine/src/game/effects/change_zone.rs::resolve_all

First branch: Public mass ChangeZone; effective matching set and existing library shuffle/order rules select the action.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Native completed mass group and actual exclusions; later independent written instruction gets a new owner.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `remaining_complete_producers_capture_each_actual_group`

```text
thread 'trigger_suppression_event_timing::remaining_complete_producers_capture_each_actual_group' (3296245) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::remaining_complete_producers_capture_each_actual_group ... FAILED
COST_COMPONENT_PROOF deferred=true with_hush=false traveler_first=false spirits=1 expected=1 h_peers=[] t_peers=[] t_snapshot={"after":[],"before":[]} life=22 zones=[Graveyard, Graveyard, Graveyard]
COST_COMPONENT_PROOF deferred=true with_hush=false traveler_first=true spirits=1 expected=1 h_peers=[] t_peers=[] t_snapshot={"after":[],"before":[]} life=22 zones=[Graveyard, Graveyard, Graveyard]
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## shared-batch-delivery

public runtime mutation.

Physical source: `crates/engine/src/game/zone_pipeline.rs`. Entry: crates/engine/src/game/zone_pipeline.rs::deliver_batch

First branch: Existing deliver_batch consumes a real Vec<ZoneMoveRequest> and attempted set; each request retains its own actual destination/guards.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Unpaused batch and selected-bounce exact group; native no-move/non-Battlefield/choice siblings.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `unpaused_bounce_batch_and_selected_bounce_share_actual_departure_group`

```text
thread 'trigger_suppression_event_timing::unpaused_bounce_batch_and_selected_bounce_share_actual_departure_group' (3301130) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::unpaused_bounce_batch_and_selected_bounce_share_actual_departure_group ... FAILED
test trigger_suppression_event_timing::two_suppression_controllers_and_between_event_control_rebind_are_distinct ... ok
test trigger_suppression_event_timing::two_target_destroy_owns_one_event_in_both_target_orders ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## resumed-change-zone

public runtime mutation.

Physical source: `crates/engine/src/game/effects/mod.rs`. Entry: crates/engine/src/game/effects/mod.rs::drain_pending_change_zone_iteration

First branch: Natural parked ChangeZone resumes existing remaining list; only completed current segment is owned.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Both tail orders; authoritative snapshot suppression; narrowly retained no-Hush2 compatibility and ignored desired1.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `resumed_change_zone_tail_suppression_uses_authoritative_records`

```text
thread 'trigger_suppression_event_timing::resumed_change_zone_tail_suppression_uses_authoritative_records' (3304923) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::resumed_change_zone_tail_suppression_uses_authoritative_records ... FAILED

thread 'trigger_suppression_event_timing::resumed_change_zone_no_hush_duplicate_payoff_compatibility' (3304922) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## all-eligible-sacrifice

public runtime mutation.

Physical source: `crates/engine/src/game/effects/sacrifice.rs`. Entry: crates/engine/src/game/effects/sacrifice.rs::resolve

First branch: Mandatory non-up-to sacrifice with eligible.len() <= requested count selects the whole eligible pool before native sacrifice.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: No-Hush/surviving-Hush positives; inherited-target and aggregate loops remain separately excluded.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `remaining_complete_producers_capture_each_actual_group`

```text
thread 'trigger_suppression_event_timing::remaining_complete_producers_capture_each_actual_group' (3310208) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::remaining_complete_producers_capture_each_actual_group ... FAILED
COST_COMPONENT_PROOF deferred=true with_hush=true traveler_first=false spirits=1 expected=1 h_peers=[] t_peers=[] t_snapshot={"after":[],"before":[]} life=22 zones=[Graveyard, Graveyard, Graveyard]
test trigger_suppression_event_timing::separate_deferred_spell_sacrifice_cost_components_hush_first ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## player-scope-sacrifice

public runtime mutation.

Physical source: `crates/engine/src/game/effects/mod.rs`. Entry: crates/engine/src/game/effects/mod.rs::perform_player_scope_sacrifices

First branch: Existing final player/card selections form candidates; current selection player remains sacrifice authority.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Current-controller and chooser scope, native sacrifice cause, earlier/later instruction boundaries.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `remaining_complete_producers_capture_each_actual_group`

```text
thread 'trigger_suppression_event_timing::remaining_complete_producers_capture_each_actual_group' (3313653) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::remaining_complete_producers_capture_each_actual_group ... FAILED
COST_COMPONENT_PROOF deferred=false with_hush=false traveler_first=false spirits=1 expected=1 h_peers=[] t_peers=[] t_snapshot={"after":[],"before":[]} life=22 zones=[Graveyard, Graveyard, Graveyard]
test trigger_suppression_event_timing::legacy_direct_delayed_identity_and_nondeath_siblings_preserve_lifetime ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## choice-sacrifice

public runtime mutation.

Physical source: `crates/engine/src/game/engine_resolution_choices.rs`. Entry: crates/engine/src/game/engine_resolution_choices.rs::handle_resolution_choice

First branch: Natural EffectZoneChoice Sacrifice after count/ID/current-zone validation; complete chosen slice owns completed segment.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Earlier tracked producer plus empty choice keeps23; nonempty selected set22; invalid/retry and later Hush departure.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `natural_effect_zone_choice_finalizes_before_chained_hush_departure`

```text
thread 'trigger_suppression_event_timing::natural_effect_zone_choice_finalizes_before_chained_hush_departure' (3319207) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:932:13:
assertion `left == right` failed
  left: 1
 right: 0
test trigger_suppression_event_timing::natural_effect_zone_choice_finalizes_before_chained_hush_departure ... FAILED
test trigger_suppression_event_timing::not_equals_battlefield_rejects_death_but_allows_real_library_graveyard_move ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## choice-change-bounce

public runtime mutation.

Physical source: `crates/engine/src/game/engine_resolution_choices.rs`. Entry: crates/engine/src/game/engine_resolution_choices.rs::handle_resolution_choice

First branch: Natural EffectZoneChoice ChangeZone/Bounce shared arm validates chosen IDs and actual zone before delivery.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Selected group, proper destination, chain continuation and tracked-set publication; earlier empty-choice compatibility.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `change_zone_choice_uses_selected_objects_and_finalizes_before_continuation`

```text
thread 'trigger_suppression_event_timing::change_zone_choice_uses_selected_objects_and_finalizes_before_continuation' (3324217) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:2409:13:
assertion failed: moved.events.iter().any(|e|
        matches!(e,GameEvent::ZoneChanged{object_id,record,..} if
            *object_id==t&&record.trigger_suppression.is_some()))
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::change_zone_choice_uses_selected_objects_and_finalizes_before_continuation ... FAILED
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## choice-pay-cost

public runtime mutation.

Physical source: `crates/engine/src/game/engine_resolution_choices.rs`. Entry: crates/engine/src/game/engine_resolution_choices.rs::handle_resolution_choice

First branch: Natural EffectZoneChoice PayCost validates chosen set; cost-payment zone delivery precedes continuation/exile-link indexing.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Selected group peers/history; legal cost/continuation and rejected selection preserve prior authority.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `effect_zone_choice_pay_cost_uses_selected_group_before_continuation`

```text
thread 'trigger_suppression_event_timing::effect_zone_choice_pay_cost_uses_selected_group_before_continuation' (3329839) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::effect_zone_choice_pay_cost_uses_selected_group_before_continuation ... FAILED
test trigger_suppression_event_timing::granted_suppression_and_granted_death_trigger_use_effective_abilities ... ok
test trigger_suppression_event_timing::hand_library_choice_preserves_selected_cards_and_nondeath_payoff ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## cost-member-handle_sacrifice_for_cost

public runtime mutation.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: crates/engine/src/game/casting_costs.rs::handle_sacrifice_for_cost

First branch: Immediate successful chosen sacrifice component; existing legal selection/controller/payment checks still own eligibility.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: One component Count2, both orders and no-Hush; prohibited/invalid/insufficient-mana controls.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `multi_object_spell_sacrifice_cost_preserves_commit_and_suppression`

```text
thread 'trigger_suppression_event_timing::multi_object_spell_sacrifice_cost_preserves_commit_and_suppression' (3335765) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
test trigger_suppression_event_timing::multi_object_spell_sacrifice_cost_preserves_commit_and_suppression ... FAILED
test trigger_suppression_event_timing::legacy_direct_delayed_surviving_hush_bypass_compatibility ... ok
test trigger_suppression_event_timing::not_equals_battlefield_rejects_death_but_allows_real_library_graveyard_move ... ok
test trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## cost-member-pay_deferred_spell_sacrifices_at_commit

public runtime mutation.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: crates/engine/src/game/casting_costs.rs::pay_deferred_spell_sacrifices_at_commit

First branch: Deferred selected queue has validated canonical component runs; each contiguous original run opens its own action owner.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Identical-filter Count1+1, Count2+1 and Count1+2, generic/Phyrexian completion, both victim orders.

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_mixed_cardinalities_keep_exact_peers`

```text
thread 'trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers' (3341593) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4638:29:
assertion `left == right` failed
  left: []
 right: [ObjectId(3)]
test trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers ... FAILED

```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## sba-check_zero_toughness

public runtime mutation.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_zero_toughness

First branch: Creature and effective toughness <= 0

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: healthy positive-toughness subject; surviving observer; both insertion orders

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Added public first co-dying forward tuple reaches actual departures and fails observer payoff20 versus21; old119 library filter survives.

Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/sba-check_zero_toughness/outcome.json` SHA `db7cc88654d6dc0553d489de819aa6f2a55b3161064ee6df3c715f4d081417c4`.

## sba-check_lethal_damage

public runtime mutation.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_lethal_damage

First branch: Creature and effective toughness > 0 and lethal marked damage, no Indestructible

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: undamaged subject; surviving observer; both insertion orders

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Added public first co-dying forward tuple reaches actual departures and fails observer payoff20 versus21; old119 library filter survives.

Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/sba-check_lethal_damage/outcome.json` SHA `0cc229e547c3f3d871d93a1590e1da6d711677c45aa61079bcfa9a3b4e8b5d8c`.

## sba-check_unattached_auras

public runtime mutation.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_unattached_auras

First branch: Enchantment plus Aura subtype, no legal attachment, not BestowRevert

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: legally attached Aura; host survives; surviving observer; both insertion orders

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Added public first co-dying forward tuple reaches actual departures and fails observer payoff20 versus21; old119 library filter survives.

Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/sba-check_unattached_auras/outcome.json` SHA `236d5c22bb8ba78b644758fd15f2d86828d8a94738c3b3e7d558eb32457c03ff`.

## sba-check_role_uniqueness

public runtime mutation.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_role_uniqueness

First branch: live attached Role, same host/controller group >= 2, older timestamp

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: single Role; newer Role and host survive; surviving observer; both insertion orders

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Added public first co-dying forward tuple reaches actual departures and fails observer payoff20 versus21; old119 library filter survives.

Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/sba-check_role_uniqueness/outcome.json` SHA `3fd832d4ede93e94fd96fac854253ebe7b8948dfa040c75f2c12f36a2b40bee1`.

## sba-check_world_rule

public runtime mutation.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_world_rule

First branch: at least two live World permanents; older acquisition timestamp

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: single World; newer World survives; surviving observer; both insertion orders

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Added public first co-dying forward tuple reaches actual departures and fails observer payoff20 versus21; old119 library filter survives.

Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/sba-check_world_rule/outcome.json` SHA `601da9adeccf484c2ced2a50e6812b980abbe98172e0e6a03434c37420777f3a`.

## sba-check_zero_loyalty

public runtime mutation.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_zero_loyalty

First branch: Planeswalker and loyalty == 0

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: three-loyalty subject; surviving observer; both insertion orders

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Added public first co-dying forward tuple reaches actual departures and fails observer payoff20 versus21; old119 library filter survives.

Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/sba-check_zero_loyalty/outcome.json` SHA `5ef14df242af25ccf3b689ccbbbb96affcdf63007136244984041dd06eb0e4ab`.

## sba-check_zero_defense

public runtime mutation.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_zero_defense

First branch: Battle and defense == 0, no source trigger on stack

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: three-defense subject; surviving observer; both insertion orders

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Added public first co-dying forward tuple reaches actual departures and fails observer payoff20 versus21; old119 library filter survives.

Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/sba-check_zero_defense/outcome.json` SHA `0b12a58aa98ef6aeb0300f57f5b3a419e650cdfae4a6eebc878fe8f80d2d33a8`.

## sba-check_battle_protector

lower-level defensive contract; no public runtime kill.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_battle_protector

First branch: Siege, absent/illegal protector, not attacked, zero legal living opponents

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: bounded source proof in battle-protector-reachability.md; ordinary protector/choice tests are siblings, not evidence for this empty-choice arm

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: thread 'game::sba::tests::battle_protector_defensive_handoff_after_terminal_setup' (3475867) panicked at crates/engine/src/game/sba.rs:2198:14:
defensive member owns an authoritative singleton snapshot
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED


Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- v10 private lexical or defensive battle exact runtime discriminator: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/lexical-battle-v10-attempt-1/results.json` SHA `73fd0fd034cfe09fe84e1939bbdfdcb0387df5fa6c359bfd9a7a93d2c6007d5d`.

## sba-check_saga_sacrifice

public runtime mutation.

Physical source: `crates/engine/src/game/sba.rs`. Entry: GameRunner.act(PassPriority) -> public engine action boundary -> priority/SBA iteration -> check_saga_sacrifice

First branch: final chapter exists, lore >= final chapter, no chapter on stack or pending Lore event

Authority: one SBA-iteration DepartureScopeToken; member ObjectId plus current incarnation Binding: owner captures before first iteration mutation; sub-check binds immediately before existing movement/replacement call

Storage: GameState.departure_suppression_scope frames/member_bindings and claimed event keys; final GameEvent::ZoneChanged.record Consumer: with_departure_leaf -> claim_departure_event -> finish_departure_suppression; trigger collection reads co_departed/snapshot and resolves GainLife

Invalidation: live-zone/phasing and current incarnation checks reject stale candidates; actual prevented/no-op moves emit no claim; owner closes before next SBA iteration/pause Serialization: no source shape change; emitted snapshot persists, lexical owner remains serde-skipped; prototype tests only

Hostile/sibling controls: below-final Lore count; surviving observer; both insertion orders

Exact mutation: Remove only this newly added member-handoff wrapper. Existing movement expression, owner scope, candidate/guard/filter and returned outcome remain.

Actual assertion: Added public first co-dying forward tuple reaches actual departures and fails observer payoff20 versus21; old119 library filter survives.

Tests: `game::sba::tests`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/sba-check_saga_sacrifice/outcome.json` SHA `ed8f71645b0a1be1b85a7127daef275cbb87fd2450a3c6f625c418567bb6f37d`.

## components-whole-queue

public runtime mutation.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: crates/engine/src/game/casting_costs.rs::pay_deferred_spell_sacrifices_at_commit

First branch: Natural selected sacrifice/mana/Phyrexian or inline PayCost checkpoint; malformed fixtures alter only serialized provenance. See exact operation and designated semantic test for this physical guard.

Authority: One successful selected cost-component invocation; checked append-start offset is its opaque DeferredSacrificeComponentId. Actor authorization remains prior authority. Binding: Selection binds one ID to every selected object. Pure run-layout validation occurs before append, prompt/payment finalizers, or in-band action progression.

Storage: DeferredSacrificeSelection { object_id, filter, component } within the existing PendingCast, preserved through choices and mana checkpoints. Consumer: validate_deferred_sacrifice_components; pending carrier preflight; both mana finalizers; pay_deferred_spell_sacrifices_at_commit consumes canonical contiguous component slices.

Invalidation: Component provenance expires with PendingCast completion/cancel. Per-component lexical owners close before the next cost. Missing legacy nonempty metadata refuses progression without guessing. Serialization: Optional serde-default component ID is real pending provenance; Clone/equality/serde/normalization preserve it. No component ID is exported to cards, permanents or stack paid metadata.

Hostile/sibling controls: Valid empty/singleton/contiguous repeated-ID runs; Count1+1 versus Count2 same filters; malformed recurrence/missing/mixed IDs; cancel/reannounce, insufficient payment/retry, lawful concession/preferences and spoof/debug authorization.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_identical_filters_serde_and_both_finalizers`, `deferred_components_mixed_cardinalities_keep_exact_peers`

```text
thread 'trigger_suppression_event_timing::deferred_components_identical_filters_serde_and_both_finalizers' (3346495) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4574:21:
assertion failed: event_departure(&events, id).co_departed.is_empty()
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::deferred_components_identical_filters_serde_and_both_finalizers ... FAILED
test trigger_suppression_event_timing::deferred_components_inline_legacy_rejects_before_discard ... ok
test trigger_suppression_event_timing::deferred_components_invalid_checkpoints_preserve_independent_preferences_and_debug_gates ... ok
```

```text
thread 'trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers' (3346500) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4638:29:
assertion `left == right` failed
  left: [ObjectId(1), ObjectId(3)]
 right: []
test trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers ... FAILED

```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## components-singleton

public runtime mutation.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: crates/engine/src/game/casting_costs.rs::pay_deferred_spell_sacrifices_at_commit

First branch: Natural selected sacrifice/mana/Phyrexian or inline PayCost checkpoint; malformed fixtures alter only serialized provenance. See exact operation and designated semantic test for this physical guard.

Authority: One successful selected cost-component invocation; checked append-start offset is its opaque DeferredSacrificeComponentId. Actor authorization remains prior authority. Binding: Selection binds one ID to every selected object. Pure run-layout validation occurs before append, prompt/payment finalizers, or in-band action progression.

Storage: DeferredSacrificeSelection { object_id, filter, component } within the existing PendingCast, preserved through choices and mana checkpoints. Consumer: validate_deferred_sacrifice_components; pending carrier preflight; both mana finalizers; pay_deferred_spell_sacrifices_at_commit consumes canonical contiguous component slices.

Invalidation: Component provenance expires with PendingCast completion/cancel. Per-component lexical owners close before the next cost. Missing legacy nonempty metadata refuses progression without guessing. Serialization: Optional serde-default component ID is real pending provenance; Clone/equality/serde/normalization preserve it. No component ID is exported to cards, permanents or stack paid metadata.

Hostile/sibling controls: Valid empty/singleton/contiguous repeated-ID runs; Count1+1 versus Count2 same filters; malformed recurrence/missing/mixed IDs; cancel/reannounce, insufficient payment/retry, lawful concession/preferences and spoof/debug authorization.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_identical_filters_serde_and_both_finalizers`, `deferred_components_mixed_cardinalities_keep_exact_peers`

```text
thread 'trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers' (3352754) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4638:29:
assertion `left == right` failed
  left: []
 right: [ObjectId(3)]
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers ... FAILED
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## components-filter-grouping

public runtime mutation.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: crates/engine/src/game/casting_costs.rs::pay_deferred_spell_sacrifices_at_commit

First branch: Natural selected sacrifice/mana/Phyrexian or inline PayCost checkpoint; malformed fixtures alter only serialized provenance. See exact operation and designated semantic test for this physical guard.

Authority: One successful selected cost-component invocation; checked append-start offset is its opaque DeferredSacrificeComponentId. Actor authorization remains prior authority. Binding: Selection binds one ID to every selected object. Pure run-layout validation occurs before append, prompt/payment finalizers, or in-band action progression.

Storage: DeferredSacrificeSelection { object_id, filter, component } within the existing PendingCast, preserved through choices and mana checkpoints. Consumer: validate_deferred_sacrifice_components; pending carrier preflight; both mana finalizers; pay_deferred_spell_sacrifices_at_commit consumes canonical contiguous component slices.

Invalidation: Component provenance expires with PendingCast completion/cancel. Per-component lexical owners close before the next cost. Missing legacy nonempty metadata refuses progression without guessing. Serialization: Optional serde-default component ID is real pending provenance; Clone/equality/serde/normalization preserve it. No component ID is exported to cards, permanents or stack paid metadata.

Hostile/sibling controls: Valid empty/singleton/contiguous repeated-ID runs; Count1+1 versus Count2 same filters; malformed recurrence/missing/mixed IDs; cancel/reannounce, insufficient payment/retry, lawful concession/preferences and spoof/debug authorization.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_identical_filters_serde_and_both_finalizers`, `deferred_components_mixed_cardinalities_keep_exact_peers`

```text
thread 'trigger_suppression_event_timing::deferred_components_identical_filters_serde_and_both_finalizers' (3359754) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4574:21:
assertion failed: event_departure(&events, id).co_departed.is_empty()
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::deferred_components_identical_filters_serde_and_both_finalizers ... FAILED
test trigger_suppression_event_timing::deferred_components_inline_legacy_rejects_before_discard ... ok
test trigger_suppression_event_timing::deferred_components_invalid_checkpoints_preserve_independent_preferences_and_debug_gates ... ok
```

```text
thread 'trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers' (3359759) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4638:29:
assertion `left == right` failed
  left: [ObjectId(1), ObjectId(3)]
 right: []
test trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers ... FAILED

```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## component-guard-normal-finalizer

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: Natural manual CastSpell + SelectCards through GameRunner reaches pending checkpoint; targeted internal finalizer/append entry then exercised with missing component metadata

First branch: nonempty deferred queue whose first selection component is None

Authority: selected DeferredSacrificeComponentId provenance on existing pending entries Binding: earlier natural successful nonempty selection append; validation before finalizer/append mutation

Storage: PendingCast.deferred_sacrificed_permanents[*].component Consumer: validate_deferred_sacrifice_components; normal/Phyrexian finalizers; handle_sacrifice_for_cost

Invalidation: missing/malformed saved layout refuses payment, normal CancelCast/reannouncement remains root/public suite authority Serialization: optional persisted component provenance; no test-only fake pending state; private exact guard tests supplement public ingress tests

Hostile/sibling controls: natural two-stage costs; real ManaPayment and PhyrexianPayment; unknown queue first entry; main public migration/valid-new controls remain distinct

Exact mutation: None

Actual assertion: Missing component provenance unexpectedly returns PhyrexianPayment instead of refusing before changing state.

Tests: `deferred_component_normal_finalizer_guard_precedes_phyrexian_prompt`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.

## component-guard-phyrexian-finalizer

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: Natural manual CastSpell + SelectCards through GameRunner reaches pending checkpoint; targeted internal finalizer/append entry then exercised with missing component metadata

First branch: nonempty deferred queue whose first selection component is None

Authority: selected DeferredSacrificeComponentId provenance on existing pending entries Binding: earlier natural successful nonempty selection append; validation before finalizer/append mutation

Storage: PendingCast.deferred_sacrificed_permanents[*].component Consumer: validate_deferred_sacrifice_components; normal/Phyrexian finalizers; handle_sacrifice_for_cost

Invalidation: missing/malformed saved layout refuses payment, normal CancelCast/reannouncement remains root/public suite authority Serialization: optional persisted component provenance; no test-only fake pending state; private exact guard tests supplement public ingress tests

Hostile/sibling controls: natural two-stage costs; real ManaPayment and PhyrexianPayment; unknown queue first entry; main public migration/valid-new controls remain distinct

Exact mutation: None

Actual assertion: Guard removal changes full serialized state before the eventual refusal: P0 life20 to18, life_lost_this_turn0 to2 and a Colorless mana pip spent.

Tests: `deferred_component_phyrexian_finalizer_guard_precedes_payment`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.

## component-guard-append

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: Natural manual CastSpell + SelectCards through GameRunner reaches pending checkpoint; targeted internal finalizer/append entry then exercised with missing component metadata

First branch: nonempty deferred queue whose first selection component is None

Authority: selected DeferredSacrificeComponentId provenance on existing pending entries Binding: earlier natural successful nonempty selection append; validation before finalizer/append mutation

Storage: PendingCast.deferred_sacrificed_permanents[*].component Consumer: validate_deferred_sacrifice_components; normal/Phyrexian finalizers; handle_sacrifice_for_cost

Invalidation: missing/malformed saved layout refuses payment, normal CancelCast/reannouncement remains root/public suite authority Serialization: optional persisted component provenance; no test-only fake pending state; private exact guard tests supplement public ingress tests

Hostile/sibling controls: natural two-stage costs; real ManaPayment and PhyrexianPayment; unknown queue first entry; main public migration/valid-new controls remain distinct

Exact mutation: None

Actual assertion: Missing provenance unexpectedly returns ManaPayment and allows a new selection instead of refusing.

Tests: `deferred_component_append_guard_precedes_cost_snapshot_and_new_selection`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.

## owner-finalization

public runtime mutation.

Physical source: `crates/engine/src/game/zones.rs`. Entry: crates/engine/src/game/zones.rs::with_departure_suppression

First branch: Owner completes with actual claimed native Battlefield departure keys; no emitted keys is an immediate no-op.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Oracle Wrath, repeated ObjectId/incarnations, paused return, zero-move and exact peer controls.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `oracle_wrath_hush_first_suppresses_simultaneous_traveler_death`, `repeated_object_id_retains_distinct_incarnation_and_event_suppression`

```text
thread 'trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death' (3367369) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:135:5:
assertion `left == right` failed: simultaneous-death-suppressed; hush_first=true
  left: 1
 right: 0
test trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death ... FAILED
test trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition ... ok
```

```text
thread 'trigger_suppression_event_timing::repeated_object_id_retains_distinct_incarnation_and_event_suppression' (3367381) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
test trigger_suppression_event_timing::repeated_object_id_retains_distinct_incarnation_and_event_suppression ... FAILED

thread 'trigger_suppression_event_timing::paused_choice_state_roundtrip_and_following_action_have_no_stale_scope' (3367376) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:1926:5:
assertion `left == right` failed
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## after-world-flush

public runtime mutation.

Physical source: `crates/engine/src/game/zones.rs`. Entry: crates/engine/src/game/zones.rs::finish_departure_suppression

First branch: Finalizer has capture and actual events; functioning post-event authority is evaluated after the owner body and before next instruction.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Normal/library inverse source grant/removal and surviving-source controls; immediate-return snapshots.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins`, `standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice`

```text
thread 'trigger_suppression_event_timing::dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins' (3372229) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:276:5:
assertion `left == right` failed
  left: false
 right: true
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins ... FAILED
```

```text
thread 'trigger_suppression_event_timing::standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice' (3372280) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:276:5:
assertion `left == right` failed
  left: false
 right: true
test trigger_suppression_event_timing::standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice ... FAILED
COST_COMPONENT_PROOF deferred=false with_hush=true traveler_first=false spirits=1 expected=1 h_peers=[] t_peers=[] t_snapshot={"after":[],"before":[]} life=22 zones=[Graveyard, Graveyard, Graveyard]
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## haunt-adapter

public runtime mutation.

Physical source: `crates/engine/src/game/haunt.rs`. Entry: crates/engine/src/game/haunt.rs::match_haunted_creature_dies

First branch: Real Haunt link with source in Exile and haunted creature actually departing; surviving Hush directly discriminates adapter.

Authority: Established exiled Haunt source -> haunted ObjectId link, actual creature death and event before suppression. Binding: Source/link setup precedes death; suppression chosen from completed departure before history at matching.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: Dedicated match_haunt matcher -> ordinary trigger registration and exact exiled-source payoff.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush exact payoff; missing/other link; sequential both orders; simultaneous Wrath both insertion orders.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `haunt_payoff_uses_the_linked_subject_death_before_world`

```text
thread 'trigger_suppression_event_timing::haunt_payoff_uses_the_linked_subject_death_before_world' (3379304) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 0, got 3 (before 20, final 23)
  left: 3
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::haunt_payoff_uses_the_linked_subject_death_before_world ... FAILED
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## unattach-adapter

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_matchers.rs`. Entry: crates/engine/src/game/trigger_matchers.rs::match_unattach

First branch: Exact matching actual event reaches the named physical predicate/adapter; designated public fixture exports meaningful event identity and payoff before comparison.

Authority: Actual previously attached source/subject relation and death-caused Unattach event with departure before history. Binding: Relation and suppression before death; matching follows native detach emission.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: Dedicated death-caused Unattach branch -> exact triggered payoff.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: Native detach for nondeath remains unchanged; no-Hush and surviving/co-dying Hush cases prove matching.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `unattach_fallback_and_native_cause_remain_distinct`

```text
thread 'trigger_suppression_event_timing::unattach_fallback_and_native_cause_remain_distinct' (3384200) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 0, got 2 (before 20, final 22)
  left: 2
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::unattach_fallback_and_native_cause_remain_distinct ... FAILED
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## component-binding-distinct-invocation

public runtime mutation.

Physical source: `crates/engine/src/game/casting_costs.rs`. Entry: crates/engine/src/game/casting_costs.rs::handle_sacrifice_for_cost

First branch: Natural WaitingFor::SacrificeForCost -> handle_sacrifice_for_cost selected valid sacrifice cost; a separate invocation begins after prior queue items and assigns component=u64(queue.len()) before appending. Same-valued cost/filter cannot merge invocations.

Authority: One successful selected cost-component invocation; checked append-start offset is its opaque DeferredSacrificeComponentId. Actor authorization remains prior authority. Binding: Selection binds one ID to every selected object. Pure run-layout validation occurs before append, prompt/payment finalizers, or in-band action progression.

Storage: DeferredSacrificeSelection { object_id, filter, component } within the existing PendingCast, preserved through choices and mana checkpoints. Consumer: validate_deferred_sacrifice_components; pending carrier preflight; both mana finalizers; pay_deferred_spell_sacrifices_at_commit consumes canonical contiguous component slices.

Invalidation: Component provenance expires with PendingCast completion/cancel. Per-component lexical owners close before the next cost. Missing legacy nonempty metadata refuses progression without guessing. Serialization: Optional serde-default component ID is real pending provenance; Clone/equality/serde/normalization preserve it. No component ID is exported to cards, permanents or stack paid metadata.

Hostile/sibling controls: Valid empty/singleton/contiguous repeated-ID runs; Count1+1 versus Count2 same filters; malformed recurrence/missing/mixed IDs; cancel/reannounce, insufficient payment/retry, lawful concession/preferences and spoof/debug authorization.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_identical_filters_serde_and_both_finalizers`

```text
thread 'trigger_suppression_event_timing::deferred_components_identical_filters_serde_and_both_finalizers' (3388737) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4552:17:
assertion `left == right` failed
  left: [Number(0), Number(0)]
 right: [Number(0), Number(1)]
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::deferred_components_identical_filters_serde_and_both_finalizers ... FAILED
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## component-serde-drop

public runtime mutation.

Physical source: `crates/engine/src/types/game_state.rs`. Entry: crates/engine/src/types/game_state.rs::

First branch: Naturally paused pending_cast with nonempty deferred_sacrificed_permanents serializes each DeferredSacrificedPermanent.component; replay must preserve Some(component) rather than recreate missing None provenance.

Authority: One successful selected cost-component invocation; checked append-start offset is its opaque DeferredSacrificeComponentId. Actor authorization remains prior authority. Binding: Selection binds one ID to every selected object. Pure run-layout validation occurs before append, prompt/payment finalizers, or in-band action progression.

Storage: DeferredSacrificeSelection { object_id, filter, component } within the existing PendingCast, preserved through choices and mana checkpoints. Consumer: validate_deferred_sacrifice_components; pending carrier preflight; both mana finalizers; pay_deferred_spell_sacrifices_at_commit consumes canonical contiguous component slices.

Invalidation: Component provenance expires with PendingCast completion/cancel. Per-component lexical owners close before the next cost. Missing legacy nonempty metadata refuses progression without guessing. Serialization: Optional serde-default component ID is real pending provenance; Clone/equality/serde/normalization preserve it. No component ID is exported to cards, permanents or stack paid metadata.

Hostile/sibling controls: Valid empty/singleton/contiguous repeated-ID runs; Count1+1 versus Count2 same filters; malformed recurrence/missing/mixed IDs; cancel/reannounce, insufficient payment/retry, lawful concession/preferences and spoof/debug authorization.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_identical_filters_serde_and_both_finalizers`, `deferred_components_mixed_cardinalities_keep_exact_peers`

```text
thread 'trigger_suppression_event_timing::deferred_components_identical_filters_serde_and_both_finalizers' (3394046) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4549:17:
assertion `left == right` failed
  left: [Null]
 right: [Number(0)]
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::deferred_components_identical_filters_serde_and_both_finalizers ... FAILED
```

```text
thread 'trigger_suppression_event_timing::deferred_components_mixed_cardinalities_keep_exact_peers' (3394052) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4617:21:
assertion `left == right` failed
  left: [Null, Null, Null]
 right: [Number(0), Number(1), Number(1)]

thread 'trigger_suppression_event_timing::deferred_components_legacy_and_malformed_refuse_then_cancel_reannounce' (3394051) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4733:9:
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## inline-migration-preflight

public runtime mutation.

Physical source: `crates/engine/src/game/engine.rs`. Entry: crates/engine/src/game/engine.rs::apply_action_boundary_with_stack_limit

First branch: Public action boundary first authenticates actor, classifies action, then non-OutOfBandPreference and non-exempt inline PayCost/continuation action must validate pending components before dispatch. Only serialized provenance is removed in the hostile fixture.

Authority: One successful selected cost-component invocation; checked append-start offset is its opaque DeferredSacrificeComponentId. Actor authorization remains prior authority. Binding: Selection binds one ID to every selected object. Pure run-layout validation occurs before append, prompt/payment finalizers, or in-band action progression.

Storage: DeferredSacrificeSelection { object_id, filter, component } within the existing PendingCast, preserved through choices and mana checkpoints. Consumer: validate_deferred_sacrifice_components; pending carrier preflight; both mana finalizers; pay_deferred_spell_sacrifices_at_commit consumes canonical contiguous component slices.

Invalidation: Component provenance expires with PendingCast completion/cancel. Per-component lexical owners close before the next cost. Missing legacy nonempty metadata refuses progression without guessing. Serialization: Optional serde-default component ID is real pending provenance; Clone/equality/serde/normalization preserve it. No component ID is exported to cards, permanents or stack paid metadata.

Hostile/sibling controls: Valid empty/singleton/contiguous repeated-ID runs; Count1+1 versus Count2 same filters; malformed recurrence/missing/mixed IDs; cancel/reannounce, insufficient payment/retry, lawful concession/preferences and spoof/debug authorization.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_inline_legacy_rejects_before_discard`

```text
thread 'trigger_suppression_event_timing::deferred_components_inline_legacy_rejects_before_discard' (3398305) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4697:10:
invalid provenance must refuse progression: ActionResult { events: [ZoneChanged { object_id: ObjectId(5), from: Some(Hand), to: Graveyard, record: ZoneChangeRecord { trigger_suppression: None, object_id: ObjectId(5), name: "Test later discard", core_types: [], subtypes: [], supertypes: [], keywords: [], trigger_definitions: [], power: None, toughness: None, base_power: None, base_toughness: None, colors: [], mana_value: 0, controller: PlayerId(0), owner: PlayerId(0), from_zone: Some(Hand), cast_from_zone: None, played_from_zone: None, to_zone: Graveyard, attachments: [], linked_exile_snapshot: [], is_token: false, combat_status: ZoneChangeCombatStatus { attacking: false, blocking: false, blocked: false, attacking_alone: false, blocking_alone
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## concession-preflight-exception

public runtime mutation.

Physical source: `crates/engine/src/game/engine.rs`. Entry: crates/engine/src/game/engine.rs::apply_action_boundary_with_stack_limit

First branch: After public actor authorization, matches!(action, Concede{..}) bypasses only pending-component metadata validation. Actual concession remains subject to normal actor/seat gates and reaches elimination despite malformed saved payment provenance.

Authority: One successful selected cost-component invocation; checked append-start offset is its opaque DeferredSacrificeComponentId. Actor authorization remains prior authority. Binding: Selection binds one ID to every selected object. Pure run-layout validation occurs before append, prompt/payment finalizers, or in-band action progression.

Storage: DeferredSacrificeSelection { object_id, filter, component } within the existing PendingCast, preserved through choices and mana checkpoints. Consumer: validate_deferred_sacrifice_components; pending carrier preflight; both mana finalizers; pay_deferred_spell_sacrifices_at_commit consumes canonical contiguous component slices.

Invalidation: Component provenance expires with PendingCast completion/cancel. Per-component lexical owners close before the next cost. Missing legacy nonempty metadata refuses progression without guessing. Serialization: Optional serde-default component ID is real pending provenance; Clone/equality/serde/normalization preserve it. No component ID is exported to cards, permanents or stack paid metadata.

Hostile/sibling controls: Valid empty/singleton/contiguous repeated-ID runs; Count1+1 versus Count2 same filters; malformed recurrence/missing/mixed IDs; cancel/reannounce, insufficient payment/retry, lawful concession/preferences and spoof/debug authorization.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_invalid_checkpoints_preserve_concession_and_actor_authority`

```text
thread 'trigger_suppression_event_timing::deferred_components_invalid_checkpoints_preserve_concession_and_actor_authority' (3403910) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4817:14:
lawful concession at pending cast: ActionNotAllowed("Deferred sacrifice component provenance is unavailable or invalid; cancel this saved cast and announce it again")
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::deferred_components_invalid_checkpoints_preserve_concession_and_actor_authority ... FAILED
test trigger_suppression_event_timing::dedicated_mill_exile_and_torpor_only_etb_controls_remain_positive ... ok
test trigger_suppression_event_timing::deferred_components_invalid_checkpoints_preserve_independent_preferences_and_debug_gates ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## independent-debug-preflight-exceptions

public runtime mutation.

Physical source: `crates/engine/src/game/engine.rs`. Entry: crates/engine/src/game/engine.rs::apply_action_boundary_with_stack_limit

First branch: After actor authorization, Debug/GrantDebugPermission/RevokeDebugPermission match explicit metadata-preflight exclusions. Downstream debug permission and host authorization remain authoritative; permitted actions proceed, unauthorized twins remain rejected.

Authority: One successful selected cost-component invocation; checked append-start offset is its opaque DeferredSacrificeComponentId. Actor authorization remains prior authority. Binding: Selection binds one ID to every selected object. Pure run-layout validation occurs before append, prompt/payment finalizers, or in-band action progression.

Storage: DeferredSacrificeSelection { object_id, filter, component } within the existing PendingCast, preserved through choices and mana checkpoints. Consumer: validate_deferred_sacrifice_components; pending carrier preflight; both mana finalizers; pay_deferred_spell_sacrifices_at_commit consumes canonical contiguous component slices.

Invalidation: Component provenance expires with PendingCast completion/cancel. Per-component lexical owners close before the next cost. Missing legacy nonempty metadata refuses progression without guessing. Serialization: Optional serde-default component ID is real pending provenance; Clone/equality/serde/normalization preserve it. No component ID is exported to cards, permanents or stack paid metadata.

Hostile/sibling controls: Valid empty/singleton/contiguous repeated-ID runs; Count1+1 versus Count2 same filters; malformed recurrence/missing/mixed IDs; cancel/reannounce, insufficient payment/retry, lawful concession/preferences and spoof/debug authorization.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `deferred_components_invalid_checkpoints_preserve_independent_preferences_and_debug_gates`

```text
thread 'trigger_suppression_event_timing::deferred_components_invalid_checkpoints_preserve_independent_preferences_and_debug_gates' (3409168) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4924:9:
assertion failed: matches!(error,engine::game::engine::EngineError::InvalidAction(ref text) if
    text.contains("debug_mode"))
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::deferred_components_invalid_checkpoints_preserve_independent_preferences_and_debug_gates ... FAILED
test trigger_suppression_event_timing::deferred_components_legacy_and_malformed_refuse_then_cancel_reannounce ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## normal-leaf-authority

public runtime mutation.

Physical source: `crates/engine/src/game/zones.rs`. Entry: crates/engine/src/game/zones.rs::move_to_zone

First branch: Actual normal leaf receives a live Battlefield subject and non-Battlefield destination; absent usable explicit binding and absent capturing ancestor creates singleton owner.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Standalone sacrifice inverse; no-op/non-Battlefield, nested child and normal explicit-member siblings.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice`

```text
thread 'trigger_suppression_event_timing::standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice' (3413484) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
test trigger_suppression_event_timing::standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice ... FAILED
COST_COMPONENT_PROOF deferred=false with_hush=false traveler_first=false spirits=1 expected=1 h_peers=[] t_peers=[] t_snapshot=null life=22 zones=[Graveyard, Graveyard, Graveyard]

thread 'trigger_suppression_event_timing::separate_spell_sacrifice_cost_components_bind_separate_worlds' (3413481) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## library-leaf-authority

public runtime mutation.

Physical source: `crates/engine/src/game/zones.rs`. Entry: crates/engine/src/game/zones.rs::move_to_library_at_index

First branch: Actual move_to_library_at_index has the same standalone/member authority as normal leaf before native library placement.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: Targeted Battlefield-to-library event/payoff and after-world inverse; native Hand/Library ordering choice siblings.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins`, `library_position_choice_and_targeted_leaf_preserve_non_death_events`

```text
thread 'trigger_suppression_event_timing::dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins' (3419132) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins ... FAILED
test trigger_suppression_event_timing::empty_sweep_and_zero_choice_do_not_leak_into_later_death ... ok
test trigger_suppression_event_timing::effect_zone_choice_pay_cost_uses_selected_group_before_continuation ... ok
```

```text
thread 'trigger_suppression_event_timing::library_position_choice_and_targeted_leaf_preserve_non_death_events' (3419147) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:271:10:
completed departure is authoritative
test trigger_suppression_event_timing::merged_intrinsic_flush_limit_has_a_subject_first_positive_twin ... ok
test trigger_suppression_event_timing::library_position_choice_and_targeted_leaf_preserve_non_death_events ... FAILED
test trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility ... ok
test trigger_suppression_event_timing::not_equals_battlefield_rejects_death_but_allows_real_library_graveyard_move ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## added-mid-leaf-flush

public runtime mutation.

Physical source: `crates/engine/src/game/zones.rs`. Entry: crates/engine/src/game/zones.rs::move_to_zone_inner

First branch: A bound later member must retain the selected group layer world until owner epilogue; no new layer flush inside move_to_zone_inner.

Authority: One synchronous action candidate set, each live Battlefield ObjectId and incarnation, with evaluated functioning suppression sources. Binding: Before its first physical member move; selected source/controller/condition/effective ability and live subject relations are evaluated at owner entry.

Storage: Borrowed DepartureScopeToken; serde-skipped frame, explicit member binding and exact emitted event offset/ObjectId/turn_zone_change_index keys; finalized ZoneChangeRecord payload. Consumer: with_departure_member -> existing replacement-aware delivery -> normal/library leaf -> claim_departure_event -> finish_departure_suppression; matching consumers select the captured clause side.

Invalidation: Member/leaf masks pop on synchronous closure return; owner closes before continuation, pause return or Err propagation; allocator resets when stacks are empty. No token crosses a saved continuation. Serialization: Only new event-local optional TriggerSuppressionSnapshot is serialized; existing exact co_departed peers remain. No scope/member/token is serialized.

Hostile/sibling controls: First departing granter leaves later member Creature/trigger authority intact; exact target, two-target Destroy and three Oracle Wrath controls.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `first_departing_granter_preserves_later_member_types_and_trigger`

```text
thread 'trigger_suppression_event_timing::first_departing_granter_preserves_later_member_types_and_trigger' (3422637) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:2257:13:
assertion failed: record.core_types.contains(&CoreType::Creature)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
test trigger_suppression_event_timing::first_departing_granter_preserves_later_member_types_and_trigger ... FAILED
test trigger_suppression_event_timing::effect_zone_choice_pay_cost_uses_selected_group_before_continuation ... ok
test trigger_suppression_event_timing::effect_zone_choice_replaces_nonempty_tracked_set_and_preserves_empty_compatibility ... ok
```

- original public runtime; fresh mutant/restored compilations: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-public-root-audit-final.json` SHA `519e2e272528546ec20a037f4581f0296c41e1a1b05572d45dfefd84e78a9d18`.

## before-clause-gate

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_matchers.rs`. Entry: crates/engine/src/game/trigger_matchers.rs::zone_change_clause_matches

First branch: TriggerMode ChangesZone/ChangesZoneAll or LeavesBattlefield selects zone matching; actual ZoneChanged; nonempty clauses take precedence over scalar origin_zones/origin. Matching origin/destination/valid_card plus actual Battlefield->Graveyard reaches OriginConstraint::Equals(Battlefield) and the before predicate.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `oracle_wrath_hush_first_suppresses_simultaneous_traveler_death`, `delayed_first_suppressed_occurrence_retains_one_shot_or_recurring_listener`

```text
[
  "thread 'trigger_suppression_event_timing::aggregate_payment_no_hush_and_surviving_hush_single_payment_controls' (3402516) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:1519:5:\nassertion `left == right` failed: aggregate grouping; reverse=false\n  left: 1\n right: 0\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility ... ok\ntest trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal ... ok",
  "thread 'trigger_suppression_event_timing::attachment_relative_suppression_binds_live_relation_before_departure' (3402520) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:3751:9:\nassertion `left == right` failed\n  left: 1\n right: 0\nFAILED\ntest trigger_suppression_event_timing::augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff ... \nthread 'trigger_suppression_event_timing::augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff' (3402521) panicked at crates/engine/src/game/scenario.rs:3353:9:\
```

```text
[
  "thread 'trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death' (3403225) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:135:5:\nassertion `left == right` failed: simultaneous-death-suppressed; hush_first=true\n  left: 1\n right: 0\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::delayed_first_suppressed_occurrence_retains_one_shot_or_recurring_listener' (3403402) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 0, got 3 (before 20, final 23)\n  left: 3\n right: 0\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## any-clause-after-to-before

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_matchers.rs`. Entry: crates/engine/src/game/trigger_matchers.rs::zone_change_clause_matches

First branch: Actual ZoneChanged and matching ChangesZone clause reaches Battlefield->Graveyard with OriginConstraint::Any; surviving observer is not SelfRef destination-functioning source, so !self_arrival selects after.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `from_anywhere_and_dies_observers_choose_different_worlds`, `delayed_same_occurrence_tries_eligible_alternative_exactly_once`

```text
[
  "thread 'trigger_suppression_event_timing::clause_local_disjunction_registers_once_for_eligible_sibling' (3418142) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 1, got 0 (before 20, final 20)\n  left: 0\n right: 1\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::co_departed_observer_and_self_trigger_both_use_before_suppression ... ok\ntest trigger_suppression_event_timing::complementary_one_of_parser_shape_remains_honest ... ok",
  "thread 'trigger_suppression_event_timing::delayed_same_occurrence_tries_eligible_alternative_exactly_once' (3418539) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 4, got 0 (before 20, final 20)\n  left: 0\n right: 4\nFAILED\ntest trigger_suppression_event_timing::destroy_guard_regeneration_and_indestructible_preserve_actual_departures_only ... ok\ntest trigger_suppression_event_timing::destroy_self_reference_and_partial_illegality_preserve_existing_guards ... ok\ntest trigger_suppression_event_timing::devour_child_sacrifice_is_independent_
```

```text
[
  "thread 'trigger_suppression_event_timing::from_anywhere_and_dies_observers_choose_different_worlds' (3419190) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 1, got 0 (before 20, final 20)\n  left: 0\n right: 1\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::delayed_same_occurrence_tries_eligible_alternative_exactly_once' (3419200) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 4, got 0 (before 20, final 20)\n  left: 0\n right: 4\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## ambiguous-origin-before-misclassification

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_matchers.rs`. Entry: crates/engine/src/game/trigger_matchers.rs::zone_change_clause_matches

First branch: ChangesZone ordinary adapter supplies Some(live active slice); nonempty complementary OneOf clause or scalar origin_zones passes matches_from and reaches OneOf/NotEquals arm after actual Battlefield->Graveyard. Co-dying Hush absent at collection permits exact payoff.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `ordinary_ambiguous_origins_preserve_live_collection_compatibility`, `ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility`

```text
[
  "thread 'trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility' (3425959) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal ... \nthread 'trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal' (3425960) panicked at crates/engine/src/game/scenario.rs:3353:9:",
  "thread 'trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal' (3425960) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nFAILED\ntest trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility ... \nthread 'trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility' (3425961) pani
```

```text
[
  "thread 'trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility' (3426254) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 1, got 0 (before 20, final 20)\n  left: 0\n right: 1\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility' (3426256) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## ambiguous-origin-after-approximation

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_matchers.rs`. Entry: crates/engine/src/game/trigger_matchers.rs::zone_change_clause_matches

First branch: Same OneOf/NotEquals dispatch, but real subject-first death retains Dies after history while later Hush departure makes ordinary live slice empty before collection; this specifically distinguishes current live from captured after.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `ordinary_ambiguous_origins_preserve_live_collection_compatibility`

```text
[
  "thread 'trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility' (3429569) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal ... \nthread 'trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal' (3429570) panicked at crates/engine/src/game/scenario.rs:3353:9:",
  "thread 'trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal' (3429570) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nFAILED\ntest trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility ... \nthread 'trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility' (3429571) pani
```

```text
[
  "thread 'trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility' (3429845) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 1, got 0 (before 20, final 20)\n  left: 0\n right: 1\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## delayed-ambiguous-live-gate

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_matchers.rs`. Entry: crates/engine/src/game/trigger_matchers.rs::match_changes_zone

First branch: Registered WhenNextEvent/WheneverEvent registry invokes match_changes_zone with None compatibility context; actual ZoneChanged then OneOf/NotEquals arm sees None and preserves ungated delayed matching. Surviving Hush is the discriminator.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: None

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `ambiguous_registered_delayed_matchers_preserve_ungated_compatibility`, `ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility`

```text
[
  "thread 'trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility' (3435613) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal ... \nthread 'trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal' (3435614) panicked at crates/engine/src/game/scenario.rs:3353:9:",
  "thread 'trigger_suppression_event_timing::ambiguous_reflexive_compatibility_and_empty_creation_disposal' (3435614) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nFAILED\ntest trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility ... \nthread 'trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility' (3435615) pani
```

```text
[
  "thread 'trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility' (3436690) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility' (3436692) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## record-snapshot-serde-drop

private helper/serialization/guard contract.

Physical source: `crates/engine/src/types/game_state.rs`. Entry: GameEvent::ZoneChanged serde serialization/deserialization boundary (schema-only test)

First branch: snapshot None versus Some(empty) versus Some(before Dies)

Authority: completed event suppression history Binding: event owner finish before serialization

Storage: ZoneChangeRecord.trigger_suppression Consumer: serde GameEvent roundtrip; public parked-event matching covered separately by main executor

Invalidation: None is missing history, Some(empty) is authoritative; neither normalized away Serialization: directly tests additive optional field; explicitly schema-only, no standalone runtime card claim

Hostile/sibling controls: old missing, authoritative empty and populated snapshot

Exact mutation: None

Actual assertion: First authoritative Some(empty) serialization loses trigger_suppression: key-presence false versus true.

Tests: `zone_change_suppression_preserves_missing_empty_and_captured_history`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.

## owner-allocator-reset

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/zones.rs`. Entry: producer/standalone zone boundary -> lexical helper; released tests invoke real zone moves and one natural public replacement pause

First branch: outermost owner epilogue after both stacks empty

Authority: DepartureScopeId plus explicit top DepartureMemberBinding(ObjectId, incarnation), bounded emitted occurrence keys Binding: owner/member call entry; actual event emission binds occurrence index

Storage: serde-skipped GameState.departure_suppression_scope; finalized emitted ZoneChanged records only Consumer: with_departure_suppression, with_departure_binding, with_departure_leaf, claim_departure_event, finish_departure_suppression

Invalidation: allocator reused only after both frame and member stacks empty Serialization: helper state is transient; public serde pause test checks fresh empty scope and retained event history; helper-only proofs are not substituted for mapped public producer claims

Hostile/sibling controls: allocator reused only after both frame and member stacks empty

Exact mutation: None

Actual assertion: Completed owner leaves allocator next_id2 rather than0; all6 scope tests fail.

Tests: `departure_scope_`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.

## ordinary-adapter

public runtime mutation.

Physical source: `crates/engine/src/game/triggers.rs`. Entry: crates/engine/src/game/triggers.rs::collect_matching_triggers_inner

First branch: collect_matching_triggers_inner passes source/functioning/zone checks, then calls ordinary adapter; TriggerMode::ChangesZone routes to contextual matcher with Some(active). Actual matching ambiguous creature death beside surviving Hush is filtered before registration.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `ordinary_ambiguous_origins_preserve_live_collection_compatibility`

```text
[
  "thread 'trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility' (3441277) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 0, got 1 (before 20, final 21)\n  left: 1\n right: 0\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition ... ok\ntest trigger_suppression_event_timing::original_entry_lki_public_same_id_reentry_preserves_original_condition ... ok"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility' (3441317) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 0, got 1 (before 20, final 21)\n  left: 1\n right: 0\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## batched-adapter

public runtime mutation.

Physical source: `crates/engine/src/game/triggers.rs`. Entry: crates/engine/src/game/triggers.rs::matching_batched_trigger_events

First branch: A matching noncreature N event passes the outer ordinary gate and trig_def.batched=true enters matching_batched_trigger_events. Each candidate passes the ETB-only filter, then ChangesZone adapter supplies Some(active) to OneOf(Battlefield); surviving Hush excludes creature C. Exact native singleton N/countSome(1) becomes C+N/countSome(2) under only inner-adapter removal.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch`, `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_mixed_hush_reverse`

```text
[
  "thread 'trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch' (3505020) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6701:9:\nassertion `left == right` failed: batched eligible subject count\n  left: Some(2)\n right: Some(1)\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_creature_only_hush_forward ... BATCH_AMBIGUOUS_DEPARTURES {\"events\":[{\"data\":{\"player_id\":1},\"type\":\"PriorityPassed\"},{\"data\":{\"from\":\"Battlefield\",\"object_id\":2,\"record\":{\"attached_to\":null,\"attachments\":[],\"base_power\":2,\"base_toughness\":2,\"cast_from_zone\":null,\"co_departed\":[],\"colors\":[],\"combat_status\":{\"attacking\":false,\"attacking_alone\":false,\"blocked\":false,\"blocking\":false,\"blocking_alone\":false,\"defending_player\":null},\"controller\":0,\"core_types\":[\"Creature\"],\"entered_incarnation\":null,\"from_zone\":\"Battlefield\",\"is_suspected\":false,\"is_token\":false,\"keywords\":[],\"linked_exile_snapshot\":[],\"mana_value\":0,\"name\":\"2/2 Vanilla\",\
```

```text
[
  "thread 'trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch' (3505793) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6701:9:\nassertion `left == right` failed: batched eligible subject count\n  left: Some(2)\n right: Some(1)\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_mixed_hush_reverse' (3505859) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6701:9:\nassertion `left == right` failed: batched eligible subject count\n  left: Some(2)\n right: Some(1)\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v10-batched-mutations/audited-results.json` SHA `e266178778d3d94b3200d846c9aa881e9efe8e6da331ed291a4999363037d596`.

## ordinary-global-death-gate

public runtime mutation.

Physical source: `crates/engine/src/game/triggers.rs`. Entry: crates/engine/src/game/triggers.rs::collect_pending_triggers

First branch: collect_pending_triggers outer event prefilter is ETB-only. Actual Battlefield->Graveyard must reach destination-functioning self ChangesZone Any clause rather than be globally discarded; source_id==record.object_id, SelfRef, and trigger_zones contains Graveyard.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `self_from_anywhere_exception_functions_in_destination_with_hush_surviving`, `clause_local_disjunction_registers_once_for_eligible_sibling`

```text
[
  "thread 'trigger_suppression_event_timing::repeated_object_id_retains_distinct_incarnation_and_event_suppression' (3444629) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:2050:9:\nassertion `left == right` failed\n  left: 0\n right: 1\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::resolver_reentry_no_replacement_borrows_outer_owner ... RESOLVER_REENTRY reverse=false replacement=false terminal=false replacements=0 x_sacrifices=0 x_departures=[(Graveyard, ZoneChangeRecord { trigger_suppression: Some(TriggerSuppressionSnapshot { before: [], after: [] }), object_id: ObjectId(1), name: \"Test replacement subject X\", core_types: [Creature], subtypes: [], supertypes: [], keywords: [], trigger_definitions: [], power: Some(2), toughness: Some(2), base_power: Some(2), base_toughness: Some(2), colors: [], mana_value: 0, controller: PlayerId(0), owner: PlayerId(0), from_zone: Some(Battlefield), cast_from_zone: None, played_from_zone: None, to_zone: Graveyard, attachments: [], linked_exile_snapshot: [], is_token: false, combat_status: ZoneChangeCombatStatus { attacking: false, b
```

```text
[
  "thread 'trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving' (3444780) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## batched-global-death-gate

public runtime mutation.

Physical source: `crates/engine/src/game/triggers.rs`. Entry: crates/engine/src/game/triggers.rs::matching_batched_trigger_events

First branch: Source is dying card functioning in Graveyard with batched=true, Any origin, SelfRef, exact event/source identity. Outer ordinary Any self-arrival gate passes; matching_batched_trigger_events inner ETB-only filter must retain the death event. Broad inner death gate removes it and yields zero versus one registration.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter`, `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_any_hush_reverse`

```text
[
  "thread 'trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter' (3514399) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6685:5:\nassertion `left == right` failed: one natural observer registration for the eligible batch\n  left: 0\n right: 1\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_any_hush_reverse ... BATCH_SELF_ARRIVAL_DEPARTURES {\"any\":true,\"events\":[{\"data\":{\"player_id\":1},\"type\":\"PriorityPassed\"},{\"data\":{\"from\":\"Battlefield\",\"object_id\":1,\"record\":{\"attached_to\":null,\"attachments\":[],\"base_power\":2,\"base_toughness\":2,\"cast_from_zone\":null,\"co_departed\":[],\"colors\":[],\"combat_status\":{\"attacking\":false,\"attacking_alone\":false,\"blocked\":false,\"blocking\":false,\"blocking_alone\":false,\"defending_player\":null},\"controller\":0,\"core_types\":[\"Creature\"],\"entered_incarnation\":null,\"from_zone\":\"Battlefield\",\"is_suspected\":false,\"is_token\":false,\"keywords\":[],\"linked_exile_snapshot\":[],\"mana_value\":0,\"name\":\"T
```

```text
[
  "thread 'trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter' (3515337) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6685:5:\nassertion `left == right` failed: one natural observer registration for the eligible batch\n  left: 0\n right: 1\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_any_hush_reverse' (3515363) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6685:5:\nassertion `left == right` failed: one natural observer registration for the eligible batch\n  left: 0\n right: 1\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v10-batched-mutations/audited-results.json` SHA `e266178778d3d94b3200d846c9aa881e9efe8e6da331ed291a4999363037d596`.

## self-arrival-exception

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_matchers.rs`. Entry: crates/engine/src/game/trigger_matchers.rs::zone_change_clause_matches

First branch: Actual ChangesZone Battlefield->Graveyard with Any origin passes shape/destination/filter checks; all three self-arrival predicates are true (same source ObjectId, SelfRef filter, trigger functions in destination). Any exempts this occurrence; Equals(Battlefield) sibling still uses before.

Authority: Actual event subject and matching typed trigger clause, or the existing dedicated Haunt/Unattach authority; ordinary legacy ambiguity additionally borrows its collection-local live static list. Binding: After origin/destination/subject predicates match. Explicit Battlefield origin selects before; Any selects after except destination-functioning SelfRef; ambiguous ordinary clauses use live context and registered delayed clauses preserve ungated context.

Storage: Serialized ZoneChangeRecord Some(snapshot) or explicitly legacy/unavailable None; borrowed live static vector for ordinary ETB/ambiguous gates. No consumer cache persists. Consumer: zone_change_clause_matches / ordinary match_for_ordinary_collection; dedicated Haunt or Unattach adapter as named in this row; natural trigger stack and existing delayed lifetime/alternative machinery.

Invalidation: Borrowed ordinary cache ends with collection; snapshot follows its event; listener consumption/lifetime remains existing eligible-match policy. Serialization: Some(empty) is authoritative and stays Some; None remains None and invokes bounded live fallback. No parser metadata, listener suppression latch or new AST variant.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `self_from_anywhere_exception_functions_in_destination_with_hush_surviving`

```text
[
  "thread 'trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving' (3449116) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::separate_deferred_spell_sacrifice_cost_components_bind_separate_worlds ... COST_COMPONENT_PROOF deferred=true with_hush=false traveler_first=false spirits=1 expected=1 h_peers=[] t_peers=[] t_snapshot={\"after\":[],\"before\":[]} life=22 zones=[Graveyard, Graveyard, Graveyard]\nCOST_COMPONENT_PROOF deferred=true with_hush=false traveler_first=true spirits=1 expected=1 h_peers=[] t_peers=[] t_snapshot={\"after\":[],\"before\":[]} life=22 zones=[Graveyard, Graveyard, Graveyard]"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving' (3449202) panicked at crates/engine/src/game/scenario.rs:3353:9:\nassertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)\n  left: 0\n right: 2\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## before-live-subject-authority

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_suppression.rs`. Entry: crates/engine/src/game/trigger_suppression.rs::outcomes_for_live_subject

First branch: Public attachment-relative suppression and actual combat-dependent suppression positively match only the live pre-departure relation.

Authority: Effective functioning static source/controller/condition/ability plus live pre-departure subject attachment and combat relations. Binding: Owner entry, after one before-world layer evaluation and before any member leaves.

Storage: Per-candidate typed before outcomes captured in owner frame; eventual event snapshot.before. Consumer: outcomes_for_live_subject -> finish_departure_suppression -> before-selected trigger clauses.

Invalidation: Subject relation is bound before departure; later detach/combat cleanup cannot replace it. Serialization: Captured enum outcomes only; no live relation graph copied.

Hostile/sibling controls: No-Hush and surviving/co-dying/later-departed Hush; mismatching origins/subjects; ordinary versus registered-delayed ambiguity; eligible alternatives once, native nondeath events, listener later occurrence/cleanup, one versus multi-event batching.

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `attachment_relative_suppression_binds_live_relation_before_departure`, `enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat`

```text
[
  "thread 'trigger_suppression_event_timing::attachment_relative_suppression_binds_live_relation_before_departure' (3452031) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:3751:9:\nassertion `left == right` failed\n  left: 1\n right: 0\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\ntest trigger_suppression_event_timing::augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff ... ok\ntest trigger_suppression_event_timing::change_zone_choice_uses_selected_objects_and_finalizes_before_continuation ... ok",
  "thread 'trigger_suppression_event_timing::enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat' (3452179) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:3716:13:\nassertion `left == right` failed\n  left: 1\n right: 0\nFAILED\ntest trigger_suppression_event_timing::first_departing_granter_preserves_later_member_types_and_trigger ... ok\ntest trigger_suppression_event_timing::from_anywhere_and_dies_observers_choose_different_worlds ... ok\ntest trigger_suppression_event_timing::granted_suppression_and_granted_death_trigger_use_effective_
```

```text
[
  "thread 'trigger_suppression_event_timing::attachment_relative_suppression_binds_live_relation_before_departure' (3452341) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:3751:9:\nassertion `left == right` failed\n  left: 1\n right: 0\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

```text
[
  "thread 'trigger_suppression_event_timing::enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat' (3452346) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:3716:13:\nassertion `left == right` failed\n  left: 1\n right: 0\nnote: run with `RUST_BACKTRACE=1` environment variable to display a backtrace\nFAILED\n\nfailures:"
]
```

- public runtime; exact source-bound canonical reuse explicitly labeled per phase: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-matcher-mutations/audited-results.json` SHA `3a99952a542bdaf98922e9b1e5c092c0ad2561e18b99ae163197ab392f1bfe58`.

## scope-before-flush

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/zones.rs`. Entry: producer/standalone zone boundary -> lexical helper; released tests invoke real zone moves and one natural public replacement pause

First branch: nonempty candidates and no capturing ancestor

Authority: DepartureScopeId plus explicit top DepartureMemberBinding(ObjectId, incarnation), bounded emitted occurrence keys Binding: owner/member call entry; actual event emission binds occurrence index

Storage: serde-skipped GameState.departure_suppression_scope; finalized emitted ZoneChanged records only Consumer: with_departure_suppression, with_departure_binding, with_departure_leaf, claim_departure_event, finish_departure_suppression

Invalidation: live/empty parent; dynamic grant/removal cases; normal/library leaves Serialization: helper state is transient; public serde pause test checks fresh empty scope and retained event history; helper-only proofs are not substituted for mapped public producer claims

Hostile/sibling controls: live/empty parent; dynamic grant/removal cases; normal/library leaves

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: thread 'game::zones::tests::departure_scope_before_world_flushes_dirty_ability_authority' (3471359) panicked at crates/engine/src/game/zones.rs:4003:17:
assertion `left == right` failed: owner before-world must evaluate dirty continuous-effect authority
  left: Some(TriggerSuppressionSnapshot { before: [Dies], after: [Dies] })
 right: Some(TriggerSuppressionSnapshot { before: [], after: [Dies] })
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

Tests: `departure_scope_`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- v10 private lexical or defensive battle exact runtime discriminator: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/lexical-battle-v10-attempt-1/results.json` SHA `73fd0fd034cfe09fe84e1939bbdfdcb0387df5fa6c359bfd9a7a93d2c6007d5d`.

## scope-capturing-ancestor-policy

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/zones.rs`. Entry: producer/standalone zone boundary -> lexical helper; released tests invoke real zone moves and one natural public replacement pause

First branch: nonempty candidates inside already capturing owner

Authority: DepartureScopeId plus explicit top DepartureMemberBinding(ObjectId, incarnation), bounded emitted occurrence keys Binding: owner/member call entry; actual event emission binds occurrence index

Storage: serde-skipped GameState.departure_suppression_scope; finalized emitted ZoneChanged records only Consumer: with_departure_suppression, with_departure_binding, with_departure_leaf, claim_departure_event, finish_departure_suppression

Invalidation: empty parent permits independent Some; capturing parent forbids fabricated child world Serialization: helper state is transient; public serde pause test checks fresh empty scope and retained event history; helper-only proofs are not substituted for mapped public producer claims

Hostile/sibling controls: empty parent permits independent Some; capturing parent forbids fabricated child world

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Nested owner wrongly gains a snapshot: records[1].trigger_suppression.is_none() fails.

Tests: `departure_scope_`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.

## leaf-top-barrier

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/zones.rs`. Entry: producer/standalone zone boundary -> lexical helper; released tests invoke real zone moves and one natural public replacement pause

First branch: top member binding is None above matching ancestor binding

Authority: DepartureScopeId plus explicit top DepartureMemberBinding(ObjectId, incarnation), bounded emitted occurrence keys Binding: owner/member call entry; actual event emission binds occurrence index

Storage: serde-skipped GameState.departure_suppression_scope; finalized emitted ZoneChanged records only Consumer: with_departure_suppression, with_departure_binding, with_departure_leaf, claim_departure_event, finish_departure_suppression

Invalidation: explicit transparent member positive; nested independent child and reused ObjectId/incarnation Serialization: helper state is transient; public serde pause test checks fresh empty scope and retained event history; helper-only proofs are not substituted for mapped public producer claims

Hostile/sibling controls: explicit transparent member positive; nested independent child and reused ObjectId/incarnation

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Ancestor binding crosses an intervening None mask: peer list contains ObjectId3 and2 rather than only2.

Tests: `departure_scope_`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.

## leaf-consumes-member

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/zones.rs`. Entry: producer/standalone zone boundary -> lexical helper; released tests invoke real zone moves and one natural public replacement pause

First branch: valid top binding when entering owned departure leaf

Authority: DepartureScopeId plus explicit top DepartureMemberBinding(ObjectId, incarnation), bounded emitted occurrence keys Binding: owner/member call entry; actual event emission binds occurrence index

Storage: serde-skipped GameState.departure_suppression_scope; finalized emitted ZoneChanged records only Consumer: with_departure_suppression, with_departure_binding, with_departure_leaf, claim_departure_event, finish_departure_suppression

Invalidation: same-id recursion requires targeted supplemental helper proof; no inferred public recursion reach Serialization: helper state is transient; public serde pause test checks fresh empty scope and retained event history; helper-only proofs are not substituted for mapped public producer claims

Hostile/sibling controls: same-id recursion requires targeted supplemental helper proof; no inferred public recursion reach

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: thread 'game::zones::tests::departure_scope_recursive_member_leaf_does_not_claim_ancestor' (3473546) panicked at crates/engine/src/game/zones.rs:4084:9:
recursive child cannot claim the ancestor member's snapshot
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED


Tests: `departure_scope_`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.
- v10 private lexical or defensive battle exact runtime discriminator: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/lexical-battle-v10-attempt-1/results.json` SHA `73fd0fd034cfe09fe84e1939bbdfdcb0387df5fa6c359bfd9a7a93d2c6007d5d`.

## member-error-closure-pop

private helper/serialization/guard contract.

Physical source: `crates/engine/src/game/zones.rs`. Entry: producer/standalone zone boundary -> lexical helper; released tests invoke real zone moves and one natural public replacement pause

First branch: member closure returns while its owner remains live

Authority: DepartureScopeId plus explicit top DepartureMemberBinding(ObjectId, incarnation), bounded emitted occurrence keys Binding: owner/member call entry; actual event emission binds occurrence index

Storage: serde-skipped GameState.departure_suppression_scope; finalized emitted ZoneChanged records only Consumer: with_departure_suppression, with_departure_binding, with_departure_leaf, claim_departure_event, finish_departure_suppression

Invalidation: error after actual member move; nested barriers; normal and natural pause/resume Serialization: helper state is transient; public serde pause test checks fresh empty scope and retained event history; helper-only proofs are not substituted for mapped public producer claims

Hostile/sibling controls: error after actual member move; nested barriers; normal and natural pause/resume

Exact mutation: Isolated physical seam mutation; record runtime failure and restored positive, never compile-error kill.

Actual assertion: Actual with_departure_binding LIFO assertion fails at closure return (for example depth4 versus3); all6 tests fail before later cleanup assertions.

Tests: `departure_scope_`

- original library/SBA comparison, including three historical survivors: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/original-nineteen-proof-index.json` SHA `eba94ec9c4255a431f42fe771fbe2b8823cef25650de991ff4a7e22297cfc526`.

## before-snapshot-some-to-live-fallback

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_suppression.rs`. Entry: crates/engine/src/game/trigger_suppression.rs::death_suppressed_before

First branch: Actual before-timed clause on a real creature departure, followed by later source arrival/departure so live authority disagrees with captured history.

Authority: Authoritative Some(snapshot) selected before vector; live functioning suppression only when the optional history is absent. Binding: Snapshot captured at the actual completed departure; clause classification selects the side at matching. None alone consults present functioning statics.

Storage: ZoneChangeRecord.trigger_suppression: Option<TriggerSuppressionSnapshot>; canonical enum vectors. Consumer: death_suppressed_before -> zone_change_clause_matches -> ordinary/delayed collection and exact public payoff.

Invalidation: Serialized event authority is immutable; later actions and another incarnation cannot replace it. No ongoing cache is introduced. Serialization: Some(empty), Some(Dies), asymmetric sides and None remain distinct through serde; helper does not rewrite the record.

Hostile/sibling controls: Independent unchanged-world no-Hush Oracle Wrath plus both contradictory historical/live worlds.

Exact mutation: see exact operation in JSON

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `trigger_suppression_event_timing::repeated_object_id_retains_distinct_incarnation_and_event_suppression`, `trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death`, `trigger_suppression_event_timing::oracle_wrath_without_hush_creates_exactly_one_spirit`

- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/before-snapshot-some-to-live-fallback/outcome.json` SHA `5ea5daff7f527d95036af307894f9697ad4b7af79bc81a811090cc96c91bdfed`.

## after-snapshot-some-to-live-fallback

public runtime mutation.

Physical source: `crates/engine/src/game/trigger_suppression.rs`. Entry: crates/engine/src/game/trigger_suppression.rs::death_suppressed_after

First branch: Actual after-timed clause on a real creature departure, followed by later source arrival/departure so live authority disagrees with captured history.

Authority: Authoritative Some(snapshot) selected after vector; live functioning suppression only when the optional history is absent. Binding: Snapshot captured at the actual completed departure; clause classification selects the side at matching. None alone consults present functioning statics.

Storage: ZoneChangeRecord.trigger_suppression: Option<TriggerSuppressionSnapshot>; canonical enum vectors. Consumer: death_suppressed_after -> zone_change_clause_matches -> ordinary/delayed collection and exact public payoff.

Invalidation: Serialized event authority is immutable; later actions and another incarnation cannot replace it. No ongoing cache is introduced. Serialization: Some(empty), Some(Dies), asymmetric sides and None remain distinct through serde; helper does not rewrite the record.

Hostile/sibling controls: Independent unchanged-world no-Hush Oracle Wrath plus both contradictory historical/live worlds.

Exact mutation: see exact operation in JSON

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `trigger_suppression_event_timing::after_history_authoritative_empty_allows_observer_despite_later_hush_arrival`, `trigger_suppression_event_timing::after_history_captured_dies_blocks_observer_after_later_hush_departure`, `trigger_suppression_event_timing::oracle_wrath_without_hush_creates_exactly_one_spirit`

- expanded v10 public per-order/per-control comparison: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/expanded-v10-root-attempt-1/after-snapshot-some-to-live-fallback/outcome.json` SHA `8106a65a88ee1d03a48c03de80a463bfe40b25a48b5e47a5352627a821e90c48`.

## R2-resolver-barrier

public runtime mutation with retained original lower-level test siblings.

Physical source: `crates/engine/src/game/effects/mod.rs`. Entry: Public two-target ChangeZone replacement tail -> child explicit SelfRef Sacrifice of the same live incarnation; parent owns Y only.

First branch: Public two-target ChangeZone replacement tail -> child explicit SelfRef Sacrifice of the same live incarnation; parent owns Y only.

Authority: Top explicit None member barrier, selected parent candidates and actual child/parent event keys. Binding: At independent resolver-chain entry before any callback can consume a member binding.

Storage: Serde-skipped lexical binding stack plus final event-local snapshot/peers. Consumer: with_departure_leaf and claim_departure_event; public X-None/Y-singleton assertions.

Invalidation: Barrier pops at synchronous return; no ancestor lookup through None. Serialization: Only actually owned event history persists; no lexical token serialized.

Hostile/sibling controls: Redirect-only no-departure and existing nested independent-cause control; both exact same-incarnation orders.

Exact mutation: Remove only resolver entry wrapper, keeping resolver body and owner/member implementation.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure`, `trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure_reversed`, `trigger_suppression_event_timing::resolver_reentry_no_replacement_borrows_outer_owner`, `trigger_suppression_event_timing::resolver_reentry_redirect_only_preserves_original_incarnation`

```text

thread 'trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure' (3306014) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4356:9:
assertion failed: x_record.trigger_suppression.is_none()
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:

failures:
```

```text

thread 'trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure_reversed' (3306042) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4356:9:
assertion failed: x_record.trigger_suppression.is_none()
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:

failures:
```

- five-seam original public/lower-level baseline/mutant/restored fresh compile comparisons: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-r2-r3-mutations/audited-results.json` SHA `6123afad5b7244548d50f37012ef5179ea492aad43b58c35c35ad4e5a624e522`.

## R3-original-entry-exit-lki

public runtime mutation with retained original lower-level test siblings.

Physical source: `crates/engine/src/game/filter.rs`. Entry: Public entry trigger responds with typed temporary +2/+2 then bounce; original entered incarnation no longer on Battlefield.

First branch: Public entry trigger responds with typed temporary +2/+2 then bounce; original entered incarnation no longer on Battlefield.

Authority: Original entry event and matching exit LKI, including effective3/3, against live2/2 source. Binding: Entry records incarnation; exit records its actual evaluated characteristics before cleanup.

Storage: Existing event snapshot/exit LKI and original-incarnation association. Consumer: object-condition power comparison at trigger resolution.

Invalidation: After departure do not read reset live1/1; unrelated incarnation cannot replace original exit history. Serialization: Existing event/LKI serialization unchanged.

Hostile/sibling controls: Existing departed/bounced/reentered conditions and public baseline+1 control.

Exact mutation: Revert only original-entry exit-LKI fallback; unchanged test source.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield`, `trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition`, `trigger_suppression_event_timing::original_entry_lki_public_unpumped_entry_does_not_trigger`

```text
test game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield ... 
thread 'game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield' (3313571) panicked at crates/engine/src/game/triggers.rs:11864:9:
exit LKI 3/3 > source 2/2 (CR 608.2h); pre-fix reads reverted 1/1 -> false
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:

failures:
```

```text
test trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition ... 
thread 'trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition' (3316930) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:5152:5:
assertion `left == right` failed
  left: 20
 right: 21
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

- five-seam original public/lower-level baseline/mutant/restored fresh compile comparisons: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-r2-r3-mutations/audited-results.json` SHA `6123afad5b7244548d50f37012ef5179ea492aad43b58c35c35ad4e5a624e522`.

## R3-original-entry-incarnation

public runtime mutation with retained original lower-level test siblings.

Physical source: `crates/engine/src/game/filter.rs`. Entry: Same public entry-trigger response followed by actual leave and same-ID reentry with a new incarnation.

First branch: Same public entry-trigger response followed by actual leave and same-ID reentry with a new incarnation.

Authority: Original entered incarnation exit3/3, not new live1/1 sharing ObjectId. Binding: Bind entry incarnation at trigger creation and resolve against its own later exit.

Storage: Existing entry/exit LKI and ObjectId plus incarnation. Consumer: object-condition power comparison.

Invalidation: New incarnation is not evidence for the original entry. Serialization: No new schema in this seam.

Hostile/sibling controls: Original-entry departed/bounced siblings and exact public reentry+1.

Exact mutation: Revert only original-incarnation guard; unchanged test source.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry`, `trigger_suppression_event_timing::original_entry_lki_public_same_id_reentry_preserves_original_condition`, `trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition`

```text
test game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry ... 
thread 'game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry' (3327287) panicked at crates/engine/src/game/triggers.rs:12093:9:
original exit LKI 3/3 > source 2/2 (CR 608.2h); reverting the incarnation gate reads the re-entered base 1/1 -> false
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:

failures:
```

```text
test trigger_suppression_event_timing::original_entry_lki_public_same_id_reentry_preserves_original_condition ... 
thread 'trigger_suppression_event_timing::original_entry_lki_public_same_id_reentry_preserves_original_condition' (3330863) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:5152:5:
assertion `left == right` failed
  left: 20
 right: 21
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

- five-seam original public/lower-level baseline/mutant/restored fresh compile comparisons: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-r2-r3-mutations/audited-results.json` SHA `6123afad5b7244548d50f37012ef5179ea492aad43b58c35c35ad4e5a624e522`.

## R3-bounce-exit-controller

public runtime mutation with retained original lower-level test siblings.

Physical source: `crates/engine/src/game/effects/mod.rs`. Entry: Real control spell makes P0 controller of P1-owned creature, then public bounce followed by conditional draw.

First branch: Real control spell makes P0 controller of P1-owned creature, then public bounce followed by conditional draw.

Authority: Effective controller at exit P0, not reset owner P1 after bounce. Binding: Capture evaluated controller before battlefield departure.

Storage: Existing exit LKI in parent-target context. Consumer: Conditional bounce follow-up Draw.

Invalidation: Zone reset cannot alter historical controller. Serialization: Existing LKI surface unchanged.

Hostile/sibling controls: No-theft and existing bounce target-controller tests.

Exact mutation: Revert only use of exit controller for parent-target condition.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `game::effects::tests::bounce_followup_draws_when_caster_controlled_parent_target`, `game::effects::tests::bounce_followup_skips_draw_when_opponent_controlled_parent_target`, `trigger_suppression_event_timing::real_control_spell_then_bounce_uses_exit_controller_for_draw`

```text
test game::effects::tests::bounce_followup_draws_when_caster_controlled_parent_target ... 
thread 'game::effects::tests::bounce_followup_draws_when_caster_controlled_parent_target' (3344773) panicked at crates/engine/src/game/effects/mod.rs:13109:9:
assertion `left == right` failed
  left: 0
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

```text
test trigger_suppression_event_timing::real_control_spell_then_bounce_uses_exit_controller_for_draw ... 
thread 'trigger_suppression_event_timing::real_control_spell_then_bounce_uses_exit_controller_for_draw' (3348595) panicked at crates/engine/src/game/scenario.rs:3327:9:
assertion `left == right` failed: P0 hand delta since stack commit: expected 1, got 0 (baseline 0, final 0)
  left: 0
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

- five-seam original public/lower-level baseline/mutant/restored fresh compile comparisons: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-r2-r3-mutations/audited-results.json` SHA `6123afad5b7244548d50f37012ef5179ea492aad43b58c35c35ad4e5a624e522`.

## R3-oversimplify-exit-controller

public runtime mutation with retained original lower-level test siblings.

Physical source: `crates/engine/src/game/filter.rs`. Entry: Real theft spell followed by real Oracle Oversimplify; actual exile and per-player Fractal creation.

First branch: Real theft spell followed by real Oracle Oversimplify; actual exile and per-player Fractal creation.

Authority: Each departed creature effective controller and power at exit. Binding: Evaluate typed control effect before exile; retain exit history after owner reset.

Storage: Existing event/LKI and per-player iteration context. Consumer: Oversimplify EventContext power sum and Fractal counters.

Invalidation: Later live owner/controller reset cannot rebucket departed power. Serialization: No new schema in this seam.

Hostile/sibling controls: No-theft7/3 executes first; theft expects5/5, mutant first P0 is7 versus5; later P1 assertion unexecuted.

Exact mutation: Revert only per-controller exit-LKI authority for power summation.

Actual assertion: Actual designated failure excerpts below; a panic does not certify later assertions or loop iterations.

Tests: `oversimplify_per_player_fractal::oversimplify_per_player_fractal_counters_match_exiled_power`, `trigger_suppression_event_timing::real_control_spell_then_oracle_oversimplify_keeps_per_player_exit_power`

```text
test oversimplify_per_player_fractal::oversimplify_per_player_fractal_counters_match_exiled_power ... 
thread 'oversimplify_per_player_fractal::oversimplify_per_player_fractal_counters_match_exiled_power' (3361350) panicked at crates/engine/tests/integration/oversimplify_per_player_fractal.rs:236:5:
assertion `left == right` failed: P0's Fractal must enter with 5 +1/+1 counters (4+1 power exiled — the stolen 2/2 must NOT count for P0 since P1 controlled it at exile), got 7
  left: 7
 right: 5
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

```text
test trigger_suppression_event_timing::real_control_spell_then_oracle_oversimplify_keeps_per_player_exit_power ... 
thread 'trigger_suppression_event_timing::real_control_spell_then_oracle_oversimplify_keeps_per_player_exit_power' (3361673) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:5312:13:
assertion `left == right` failed
  left: Some(7)
 right: Some(5)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

- five-seam original public/lower-level baseline/mutant/restored fresh compile comparisons: `/home/ubuntu/coworld-migration-20260904/hushbringer-v9-r2-r3-mutations/audited-results.json` SHA `6123afad5b7244548d50f37012ef5179ea492aad43b58c35c35ad4e5a624e522`.

