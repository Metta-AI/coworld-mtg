# Original public-path mutation checks

Thirty isolated mutations each reached a designated failing runtime assertion.
All thirty freshly compiled restored runs completed the full focused matrix:
91 passed and 20 ignored. The [root audit](hushbringer-v9-public-root-audit-final.json)
checks exact transformed source, unchanged test bytes, full source archives,
compiler artifacts, log hashes and designated failing test names. It is a
mechanical evidence audit, not independent implementation approval.

Twenty-nine mutant matrices completed. In the last, added-mid-leaf-flush,
the intended Creature-record assertion failed before another resolver test
overflowed its stack and aborted the process. That full mutant matrix has no
completion summary. The [focused follow-up](focused-leaf/receipt.json) ran the target and
four controls independently. Only the target failed on the mutant, at the
intended Creature-record assertion; all four controls passed. All five
baseline and freshly compiled restored tests passed. This completes the
bounded target/control evidence without relabeling the aborted full run.

The source is the frozen v9 candidate, not a claim that later added v10
fixtures were present. Eleven other public rows were explicitly released
to another proof owner and are not counted among these thirty. Marker
directories are not passing tests.

Each row retains its exact mutation, definition, result, compiler receipt
and complete compressed runtime log. Large source archives remain at the
EC2 paths bound by the receipts. The full frozen source manifest is archived
in [v9-frozen-gates](../v9-frozen-gates/README.md). The original audit fully
checked 27 rows; the final audit reused their unchanged archive-content
checks after rehashing the archives, then checked the three new rows.

| Mutation | Designated failing test(s) | Mutant matrix |
| --- | --- | --- |
| augment-handoff | augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff | Completed with failure |
| destroy-resolve | two_target_destroy_owns_one_event_in_both_target_orders | Completed with failure |
| destroy-resolve_all | oracle_wrath_hush_first_suppresses_simultaneous_traveler_death | Completed with failure |
| keep-sweep | completed_keep_sacrifice_sweeps_share_one_boundary_across_choice_routes | Completed with failure |
| change-zone-resolve | remaining_complete_producers_capture_each_actual_group | Completed with failure |
| change-zone-resolve_all | remaining_complete_producers_capture_each_actual_group | Completed with failure |
| shared-batch-delivery | unpaused_bounce_batch_and_selected_bounce_share_actual_departure_group | Completed with failure |
| resumed-change-zone | resumed_change_zone_tail_suppression_uses_authoritative_records | Completed with failure |
| all-eligible-sacrifice | remaining_complete_producers_capture_each_actual_group | Completed with failure |
| player-scope-sacrifice | remaining_complete_producers_capture_each_actual_group | Completed with failure |
| choice-sacrifice | natural_effect_zone_choice_finalizes_before_chained_hush_departure | Completed with failure |
| choice-change-bounce | change_zone_choice_uses_selected_objects_and_finalizes_before_continuation | Completed with failure |
| choice-pay-cost | effect_zone_choice_pay_cost_uses_selected_group_before_continuation | Completed with failure |
| cost-member-handle_sacrifice_for_cost | multi_object_spell_sacrifice_cost_preserves_commit_and_suppression | Completed with failure |
| cost-member-pay_deferred_spell_sacrifices_at_commit | deferred_components_mixed_cardinalities_keep_exact_peers | Completed with failure |
| components-whole-queue | deferred_components_identical_filters_serde_and_both_finalizers, deferred_components_mixed_cardinalities_keep_exact_peers | Completed with failure |
| components-singleton | deferred_components_mixed_cardinalities_keep_exact_peers | Completed with failure |
| components-filter-grouping | deferred_components_identical_filters_serde_and_both_finalizers, deferred_components_mixed_cardinalities_keep_exact_peers | Completed with failure |
| owner-finalization | oracle_wrath_hush_first_suppresses_simultaneous_traveler_death, repeated_object_id_retains_distinct_incarnation_and_event_suppression | Completed with failure |
| after-world-flush | dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins, standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice | Completed with failure |
| haunt-adapter | haunt_payoff_uses_the_linked_subject_death_before_world | Completed with failure |
| unattach-adapter | unattach_fallback_and_native_cause_remain_distinct | Completed with failure |
| component-binding-distinct-invocation | deferred_components_identical_filters_serde_and_both_finalizers | Completed with failure |
| component-serde-drop | deferred_components_identical_filters_serde_and_both_finalizers, deferred_components_mixed_cardinalities_keep_exact_peers | Completed with failure |
| inline-migration-preflight | deferred_components_inline_legacy_rejects_before_discard | Completed with failure |
| concession-preflight-exception | deferred_components_invalid_checkpoints_preserve_concession_and_actor_authority | Completed with failure |
| independent-debug-preflight-exceptions | deferred_components_invalid_checkpoints_preserve_independent_preferences_and_debug_gates | Completed with failure |
| normal-leaf-authority | standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice | Completed with failure |
| library-leaf-authority | dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins, library_position_choice_and_targeted_leaf_preserve_non_death_events | Completed with failure |
| added-mid-leaf-flush | first_departing_granter_preserves_later_member_types_and_trigger | Semantic assertion, then collateral abort |
