# Hushbringer v6 production implementation

Status: FINAL STRUCTURED PARTIAL HANDOFF — production ownership RELEASED for the fresh v8 executor. The introduced deferred Composite regression is NOT ACCEPTED; this is not an implementation-complete or commit-ready receipt. Independent assigned gates are closed below. Root owns fresh v8 planning/review, remaining acceptance gates, worker comparison, independent implementation review and commit.

Remote checkout: /home/ubuntu/repos/phase-verifiable-loop
Branch: codex/hushbringer-simultaneous-death
Base: 2dec6c88915db4697706234a7ba2fcedd97b1689
Case: 01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa
All operations performed through ssh nishadsingh-box-4. No commits, pushes, local checkout edits, Coworld changes, or child agents.

## Implemented authority

The event carries Option<TriggerSuppressionSnapshot>, with canonical before/after SuppressedTriggerEvent vectors. Some(empty) is authoritative; None alone selects unavailable-history live fallback for repaired timing. The ordinary ambiguous-origin compatibility branch deliberately ignores both sides and borrows its collector's live cache; registered delayed wrappers pass no legacy gate.

The transient GameState departure_suppression_scope owns incarnation-bound candidates and exact emitted event keys (vector offset, object id, turn index). Only an explicit borrowed DepartureScopeToken can bind a producer member. Top member bindings and None barriers prevent incidental object-ID overlap from borrowing a parent's authority. The general ability-chain resolver introduces an independent-cause barrier. Member leaves mask their binding during recursive mutation and claim only their own emitted occurrence. Owners finalize once on normal, pause, and Result error returns, before handing control to continuations or event consumers. Allocator history is cleared at the outermost completed boundary.

Before capture uses live target-filter authority after a genuine boundary flush; after capture uses the existing zone-change-record filter authority after the completed action's flush. This preserves full live attachment/combat/controller-relative predicates before departure and pre-death characteristics afterward. No member leaf introduces a flush. Independent nested owners under a capturing ancestor keep None, preserving the bounded layer-world limitation. Empty/non-departure parents do not suppress an independent child's capture.

Historical zone_changes_this_turn copies remain None. Emitted and parked GameEvents retain the completed snapshot through ordinary clone/serde. The synchronous scope is serde-skipped/defaulted, structurally cloned, omitted from equality, normalized to empty for loop comparison, and named in the exhaustive GameState field audit.

## Production-path coverage map

The test names below refer to crates/engine/tests/integration/trigger_suppression_event_timing.rs unless qualified. Runtime results are pending the tests executor's receipt; these names describe intended reaching fixtures, not a current passing claim.

| Claim / changed seam | Production entry and first relevant branch | Runtime fixture / exact discriminator |
|---|---|---|
| Wrath simultaneous self death | cast Wrath -> DestroyAll -> resolve_all matching vector -> shared owner | oracle_wrath_hush_first_suppresses_simultaneous_traveler_death and reversed order: Hush, Traveler, spell graveyard; Spirit 0 vs baseline 1. No-Hush twin exactly 1. |
| Multi-target Destroy | cast typed Destroy -> resolve -> nonempty object targets -> each guarded destroy_single_object member | two_target_destroy_owns_one_event_in_both_target_orders: exact deaths, Spirit 0; no-Hush 1. |
| Destroy guards and self-reference | existing destruction guard/replacement authority inside member | destroy_guard_regeneration_and_indestructible_preserve_actual_departures_only; further self-reference/illegal-target rows to be supplied in peer receipt. |
| Separate written instructions | cast chained Destroy instructions -> separate resolve owner closures | sequential_destroy_instructions_bind_separate_before_worlds: Hush-first 1 Spirit, Traveler-first 0; distinct indices/groups. |
| Typed target and mass ChangeZone | cast -> target loop / resolve_all matching -> member delivery | remaining_complete_producers_capture_each_actual_group routes 0/1: both orders, zero with Hush / one without, authoritative record. |
| Complete all-eligible Sacrifice | cast -> empty explicit targets -> eligible.len <= count fast path | remaining_complete_producers_capture_each_actual_group route 2, same exact payoff and snapshot discriminator. |
| Player-scope simultaneous sacrifices | cast -> collect choices -> perform_player_scope_sacrifices flattened selected IDs | remaining_complete_producers_capture_each_actual_group route 3; controller/choice variants in peer receipt. |
| Complete keep/sacrifice sweep | cast -> CategoryChoice/ChooseKeptCreatures or auto/empty category -> private sacrifice_unchosen | completed_keep_sacrifice_sweeps_share_one_boundary_across_choice_routes: keeps expected third card, reached victim deaths, Spirit 0/1 twins, actual choice actions. |
| EffectZoneChoice movement | apply SelectCards -> validated chosen -> scoped loop, then continuation | natural_effect_zone_choice_finalizes_before_chained_hush_departure and paused_choice_state_roundtrip_and_following_action_have_no_stale_scope: exact victim zones, completed continuation payoff, later fresh death 1. Other movement-arm rows pending peer receipt. |
| Spell cost component | cast pipeline -> deferred sacrifice commit / chosen cost handler | multi_object_spell_sacrifice_cost_preserves_commit_and_suppression: paid spell resolves, exact life delta, victim deaths and zero/one Spirit. Immediate/failed-retry variants pending peer receipt. |
| SBA iteration | post-action priority -> one iteration owner -> borrowed zero/lethal/aura/role/world/loyalty/defense/protector/saga checks | remaining_complete_producers_capture_each_actual_group lethal route and successive_sba_iterations_bind_new_world_after_suppressor_dies: first vs next iteration timing and exact event group. |
| Standalone Augment retains SBA group | post-action SBA -> check_standalone_augment_permanents -> same iteration token -> replacement-aware graveyard delivery | augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff: no-Hush exact +1 co-departed observer payoff, Hush twin zero, exact peer set/snapshot; omitted Augment handoff loses +1. |
| Batch delivery / resumed tails | move_objects_simultaneously_then -> deliver_batch; drain_pending_change_zone_iteration -> remaining loop | Additional production row requested from peer; closure ends before BatchCompletion/deferred trigger collection. |
| Ordinary self, observer, co-departed, off-zone and shadow scans | collect_matching_triggers_inner -> match_for_ordinary_collection | co_departed_observer_and_self_trigger_both_use_before_suppression; ordinary_ambiguous_origins_preserve_live_collection_compatibility; index audit selected by scenario. |
| Clause-local before vs after | typed matching origin/destination/filter -> Equals(Battlefield) before; Any after | from_anywhere_and_dies_observers_choose_different_worlds and clause_local_disjunction_registers_once_for_eligible_sibling: matching eligible sibling pays once while dies sibling is suppressed; no-Hush independent positives. |
| Self from-anywhere exception | source == subject, typed SelfRef, Any, destination-functioning trigger | self_from_anywhere_exception_functions_in_destination_with_hush_surviving: self arrival pays despite Hush, ordinary dies does not. |
| Ambiguous origin compatibility | matching OneOf / NotEquals(other) -> ordinary Some(cache) or registered None | ordinary_ambiguous_origins_preserve_live_collection_compatibility and ambiguous_registered_delayed_matchers_preserve_ungated_compatibility: ordinary surviving-Hush zero, delayed surviving-Hush baseline payoff, sequential subject-before-Hush positive despite saved suppression. |
| Nonmatching origin remains rejected | OriginConstraint::matches_from before suppression | not_equals_battlefield_rejects_death_but_allows_real_library_graveyard_move: real death negative plus real mill positive. |
| Haunt linked subject | registered HauntedCreatureDies -> real battlefield/graveyard Creature guard -> existing Haunt link -> before predicate | haunt_payoff_uses_the_linked_subject_death_before_world: link-bound correct subject only, Hush zero, no-Hush positive. |
| Unattach fallback only | registered Unattach -> Battlefield-origin ZoneChanged fallback -> attachment match -> death before predicate | unattach_fallback_and_native_cause_remain_distinct: actual fallback suppressed; native Unattached remains causal. |
| Delayed matching/lifetime | cast-created WheneverEvent / WhenNextEvent -> registered wrappers -> per-occurrence snapshot | delayed_first_suppressed_occurrence_retains_one_shot_or_recurring_listener: first death 0 and retained listener; later payoff and correct consumption/retention. |
| Delayed alternative match | WhenNextEvent primary then alternative on same event | delayed_same_occurrence_tries_eligible_alternative_exactly_once: suppressed primary cannot veto eligible Any; exact single payoff/removal. |
| Native cause/exile not dies | registered Sacrificed or matching Exile alternative | delayed_native_sacrifice_and_exile_alternatives_remain_eligible: reached cause/exile pays and consumes while death-only retains. |
| Reflexive disposal | creation-batch registered match -> existing unmatched-reflexive disposal | delayed_reflexive_suppression_discards_unmatched_listener: reached suppressed death no payoff, no surviving listener/later payoff; native sacrifice positive. |
| Creation-bound source/controller/duration | delayed creation unchanged; matching event cloned into existing context | distinct_controller_delayed_listeners_keep_creation_source_and_controller; delayed_cleanup_retains_persistent_and_expires_this_turn_listeners. Exact P0/P1 payoffs and listener identities. |
| Effective suppression/trigger characteristics | functioning statics + layers at real boundary | stripped_or_phased_suppressor_allows_the_same_reached_death; granted_suppression_and_granted_death_trigger_use_effective_abilities; first_departing_granter_preserves_later_member_types_and_trigger; controller_relative_and_conditional_suppression_bind_before_departure. |
| Immediate after world and no stale lifetime | standalone leaf -> complete owner -> after flush | single_departure_after_world_observes_ability_removal_source_leaving; repeated_object_id_retains_distinct_incarnation_and_event_suppression. |
| Serialization/default / private lifecycle | completed GameEvent serde; synchronous helpers, no public action replacement | types::events::zone_change_suppression_preserves_missing_empty_and_captured_history; zones::departure_scope_* supplemental tests inspect errors, barriers, nested ownership, repeated incarnation, empty parent/library leaf, clone/equality/normalization/serde. |

## Maintainer simulation matrix

All binding values below are concrete values or IDs, never card names. Hostile fixture names are in the coverage table; peer runtime result columns remain pending.

| Seam | Selected authority and bound value / time | Mode, storage, consumer | Invalidation and protocol effect |
|---|---|---|---|
| Ordinary grouped/standalone departure | producer-selected ObjectId + pre-move incarnation; owner minted at movement boundary | Evaluated before vector in DepartureSuppressionCapture; claimed vector offset/id/turn index in owner frame; finish writes record before/after | Exact incarnation mismatch denies stale membership; zero/prevented/no-op emits nothing; redirected actual BF departure records correct destination. Lexical owner/member stacks disappear before pause/error return. |
| Owner/member nested delivery | borrowed DepartureScopeToken and top Option<DepartureMemberBinding>; chosen before invoking existing guard/replacement/pipeline | Latch exact member through transparent delivery; leaf consumes binding during recursion; claim_departure_event records exact emission | Resolver reentry inserts None barrier. Capturing ancestor prevents invented child world; child/parent cannot rewrite each other's snapshots or group. No serialized token/pending field. |
| Sequential / repeated ObjectId | each written instruction opens fresh owner; object incarnation rechecked at member invocation | Event-local Some vectors; matcher reads that occurrence's record | Later departure cannot extend earlier suppression or reuse old incarnation's authority. Index identifies repeated ID occurrences. |
| Ordinary zone clauses | typed matching OriginConstraint plus destination/filter; selected at occurrence matching | Equals(Battlefield) reads before; Any reads after; self-arrival uses source/subject SelfRef and trigger_zones; per-clause any deduplicates registration | Subject/destination/origin mismatch rejects before suppression; bounce/exile/native cause unaffected. Additive optional record JSON, no trigger AST changes. |
| Ambiguous origins | actual consumer selects Some(live active-static cache) vs None; bound for one matcher call only | Ordinary live compatibility, registered delayed bypass; no snapshot-side selection and no stored metadata | Cache lifetime ends with collector call. Mixed definitions evaluate each clause independently. No new parsing/provenance claim. |
| Haunt | existing ExileLink selects haunted subject; event record binds that subject's before vector | match_haunted_creature_dies after existing type/zone/link guard | Source leaving exile invalidates link at existing authority; no source-equals-subject assumption, no self-any exception. No link schema changes. |
| Unattach | current attachment/subject relation selects existing ZoneChanged fallback | Only actual death fallback reads before; native Unattached unchanged | Existing attachment cleanup/lifetime preserved. No new causal record or event shape. |
| Delayed listener | existing source_id/controller/condition/ability/one_shot bound during creation; later event outcome bound at emission | Shared registered clause matcher sees record; existing delayed context clones matched GameEvent into pending/stack | Suppressed ordinary next-event does not consume; eligible match consumes one-shot; recurring retained to cleanup; unmatched reflexive discarded immediately. No creation/cleanup/target authority changes. |
| Cost/choice/resume | validated chosen IDs and existing payer/controller or remaining pending IDs | Transient owner within payment/movement; finalize before finish_pending_cost_or_cast, resume_with_error_propagation, deferred collection or BatchCompletion | Failed payment uses existing rollback/event vector; ActionResult mem::take occurs after finalization. Separate immediate components pass the current matrix, but flat deferred Composite selections share a group and fail their per-component assertion; baseline classification is pending. No final per-component acceptance claim. |
| GameState carrier | synchronous local scope state, never a rules checkpoint | serde(skip, default), ordinary owned Clone; manual PartialEq excludes; normalize_for_loop clears; exhaustive audit names field | Valid settled/paused checkpoints always empty. Deserialization cannot resume lexical frames. Saved completed events retain snapshots; history ledger deliberately does not. |

## Field and producer inventories

Detailed line inventories are saved in hushbringer-scope-threading-v6.txt, hushbringer-field-threading-v6.txt, and hushbringer-record-constructor-sweep-v6.txt.

Every production old mark_simultaneous_departures / stamp_simultaneous_from_slice call was replaced by scoped exact-key finalization. Public legacy helpers remain for existing direct tests/compatibility. Producer inventory: Destroy resolve/all; ChangeZone target/all; keep/sacrifice shared helper; all-eligible Sacrifice; player-scope sacrifice; pending ChangeZone drain; zone_pipeline deliver_batch; EffectZoneChoice Sacrifice/ChangeZone/BounceAll/PayCost/library-position loops; deferred spell and immediate chosen sacrifice cost; one SBA iteration and all its departure subchecks including Augment; standalone zone/library leaves.

Exhaustive constructor additions outside the manifest are mechanical None defaults only: game/derived_views.rs and integration fixtures issue_3277_captain_nghathrod_eliminated_opponent.rs, issue_5332_gandalf_trigger_doubling.rs, madame_null_integration.rs. The plan explicitly permits newly discovered constructor obligations. Remaining struct-update constructors inherit test_minimal or existing record values; constructor compile audit pending final full checks.

## Verification

- Baseline: peer confirmed both primary orders fail semantically with one Spirit vs zero; no-Hush positive passes. See hushbringer-baseline-v6.log and receipt/source manifest.
- Tilt probe: exit 127, unavailable. Direct Cargo fallback authorized by project-reference.
- First check: routine production wiring errors, resolved.
- Second check: production library compiled; old exhaustive test constructors and one test import plus peer fixture type errors found and corrected.
- Formatter: owned files formatted with rustfmt while peer writes disjoint module; final cargo fmt --all pending both writers.
- git diff --check: pass at audit time.
- Parser diff: empty; no grammar/AST/card-data support promotion, no card-name branches. Parser-only audit commands are not applicable.
- CR added-line audit: zero nonexistent references; exact text saved in hushbringer-cr-diff-v6.txt. Final refresh pending final diff.
- Targeted/new matrix, all-target clippy, full engine tests, card-data generation: pending.
- Frozen Coworld rebuilt-worker comparisons: root-owned, pending; original case/corpus/checker and failing worker unchanged.

## Judgement calls and known limits

1. Before predicates use live filter matching. A bare GameObject snapshot does not populate combat/attachment context, so it is insufficient as an intermediate before-world subject. After predicates intentionally use the existing pre-death zone record filter authority.
2. Existing EffectZoneChoice ActionResult helper consumes its events vector. Movement closures return only pause state or error; the helper is invoked after finalization, preventing stale offsets.
3. Mechanical exhaustive record fixtures were added under the plan's constructor exception, with no gameplay changes.
4. Moved SBA comments were checked against current CR: Role uniqueness 704.5z, battle attachment 310.10, protector 704.5x/y + 310.9, speed 702.179a. Underlying mechanics unchanged.
5. No panic recovery introduced: an abandoned panicking operation retains the existing unusable-state contract.

Separate retained limits: complete aggregate unless-payment sacrifice loops; complete inherited-target sacrifice loops; cross-pause full simultaneity; direct delayed bypasses; ambiguous OneOf/NotEquals event-time timing; independent nested layer worlds under capturing ancestors; existing intrinsic merge mid-leaf flush/characteristic behavior. None is represented as repaired merely because an event has Some(snapshot). In-scope acceptance and explicit compatibility/ignored characterization results will be recorded separately in final receipt.

## Preserved source-availability distinction

game/triggers.rs::source_was_not_co_departed_into_zone remains unchanged. It rejects an off-zone source appearing in another subject's co_departed list before the off-zone collection call. Required Any-origin observer fixtures use a surviving enchantment, and the separate destination-functioning self-arrival fixture uses source == subject, which never appears in its own co_departed list. No generalized co-dying destination-functioning Any-observer availability is claimed. The reviewer must assess this retained baseline distinction against the full v6 scope; the root explicitly requested preserving and reporting it rather than inferring approval for broader work.

## Remaining gate

This in-progress report must be updated with exact final test names/results, missing seam dispositions, full verification logs, and the root's frozen-worker evidence before completion. No commit or push has occurred.

## September 4 runtime checkpoint, before bounded plan correction

Active matrix attempts3/4:41 passed,3 failed,4 ignored. Original-base expanded run (including ignored):15 passed,33 failed. All three remaining active failures reproduced at original base without snapshot assertions: aggregate paid continuation life20 versus21; typed cast-created regeneration left the protected Traveler in Graveyard instead of Battlefield; naturally resumed targeted ChangeZone no-Hush control produced2 Spirits versus1. Logs are preserved as hushbringer-active-tests-v6-attempt-3.log and hushbringer-active-tests-v6-attempt-4.log, and hushbringer-baseline-expanded-v6-attempt-1.log (authoritative exact filename). The baseline primary continues to fail1 versus0; no-Hush primary passes.

These three are not fixed by the suppression work and are not silently promoted to supported behavior. Root has routed a bounded v7 plan correction and fresh review for the required-positive-control conflict. Dependent fixture/semantic edits are paused; independent lifecycle/clippy/card-data gates continue. Existing resumed scalar replay path: effects/mod.rs drain_pending_change_zone_iteration collects and drains its emitted tail; engine_replacement.rs calls drain_pending_continuation; engine.rs then runs the unchanged post-action scan. No engine_priority/engine_replacement dispatch changes are authorized or present.

Source preparation is complete. All production/owned test files formatted; exact constructor status inventory adds hushbringer-record-constructor-status-v6.txt with85 status-tagged occurrences (excluding declaration/signature and Debug strings). Added/moved CR references:65 verified present, including the new untracked module. Public token data:334 downloads,0failed; deck archive installed in ignored cache. Pre-generation known-token bytes are saved in hushbringer-known-tokens-before-v6.toml, and any generator delta will be reported separately.

## Independent lifecycle result

`cargo test -p engine --lib departure_scope_ -- --nocapture` passed3/3 with0ignored (hushbringer-production-private-v6.log). Exact tests: game::zones::tests::departure_scope_closes_on_error_and_only_claims_explicit_members; game::zones::tests::departure_scope_nested_owners_and_reused_ids_do_not_steal_occurrences; game::zones::tests::departure_scope_empty_parent_allows_independent_capture_and_settled_roundtrip. These are supplemental internals, not replacements for public production-path tests. The error fixture performs real zone moves before returning Err, checks no intermediate leaf flush/provisional snapshot, barrier isolation, exact co-departed peers, ledger None, and final empty stacks/reset allocator. Nested fixture checks new incarnation cannot borrow stale ownership and child records are not overwritten. Empty-parent/library fixture checks authoritative empty snapshot, actual library move, settled clone equality, normalization, absent serialized scope, and restored default carrier.

An additional explicit shared-helper obligation is implemented as game::zone_pipeline::departure_scope_tests::synchronous_batch_finalizes_exact_departures_before_return. It drives two real ZoneMoveRequests through move_objects_simultaneously and asserts both actual departures, first-member suppression retained in both before snapshots, empty after snapshots, exact peers, and both stacks/allocator reset before return. Runtime result pending next library run; this supplements the required public batch caller matrix.

## Build prerequisite receipt

Initial cargo clippy --all-targets -- -D warnings reached an environmental openssl-sys failure: no pkg-config or libssl-dev. The engine analysis job was allowed to finish; no source failure is inferred from this prerequisite error. Installed the two standard Ubuntu development packages with sudo, using a task-local apt source list pointing at the signed official HTTPS archive/security mirrors after the configured EC2 HTTP mirror stalled. System apt source-list configuration and Cargo dependencies were not edited. Exact logs: hushbringer-build-prerequisites-v6.log (first update, intentionally terminated), hushbringer-build-prerequisites-v6-https.log (successful install). Package command exited0. The same all-target clippy command will be rerun after the two independent fixture filters.

Combined tracked+untracked CR-diff audit now covers73 unique references, zero missing, saved in hushbringer-cr-diff-v6.txt; includes the formatted new integration module. Rule meaning was compared to each comment, including typed fixture comments. No new parser production code or support claim.

## Event serialization result

types::events::tests::zone_change_suppression_preserves_missing_empty_and_captured_history passed1/1,0ignored. Exact output: hushbringer-production-serde-v6.log. Ran the unit binary compiled by the successful private Cargo run (target/debug/deps/engine-444923dba8f143d6); this serialization source was unchanged afterward. Assertions distinguish omitted/None, Some(empty), and nonempty before/after captured GameEvent records through JSON round trips. The sole later source edit before Clippy was the supplementary shared-pipeline helper test, so no serialization production delta was uncompiled.

## Two independent production-route checks after the stop

The two newly added fixtures are compiled and passed independently without modifying the three stopped assertions:
- chosen_spell_and_activation_cost_rejection_preserves_state_for_valid_retry:1passed,0failed,0ignored. hushbringer-independent-cost-v6-attempt-2.log. The initial hushbringer-independent-cost-v6.log is compile-only (private import path corrected by test owner).
- library_position_choice_and_targeted_leaf_preserve_non_death_events:1passed,0failed,0ignored. hushbringer-independent-library-v6.log.

The first reaches both deferred spell sacrifice and immediate activated-ability sacrifice choices, rejects invalid selection while preserving state and real prompt, then accepts a valid retry and settles the cast/activation. The second reaches the real library-position choice and targeted leaf with actual non-death events. These are independent of the paused v7 fixture-plan correction. Their precise parameter/authority matrix is supplied by the test executor report.

cargo fmt --all -- --check:passed (hushbringer-format-v6.log), after both writers formatted their own files. git diff --check:passed. Mechanical Debug audit:exactly two inserted trigger_suppression: None fields, all other loop_shortcut.rs bytes equal originalbase (hushbringer-loop-golden-v6.txt).

## Workspace Clippy retry

hushbringer-production-clippy-v6-attempt-2.log reached an existing exhaustive-match error in crates/manabrew-compat/src/lib.rs:1601: GameAction::SetFullControl is not covered. Both that module and types/actions.rs are outside the diff. No compatibility-crate/action edit is authorized or present. Root requested an originalbase package reproduction and a separate engine all-target Clippy run; both remain pending until in-flight jobs close. This is not a passing workspace Clippy claim.

The supplemental synchronous batch test now includes a typed generic suppression static on the first departing member: both records must retain Dies in before, with empty after, which makes the helper test distinguish a real group from individual leaf captures. This test-only refinement does not change production behavior. Runtime remains pending.

## V7 continuation and private gate completion

Root supplied the CLEAN full v7 plan review and assigned fresh test executor hushbringer_impl_tests_v7. V7 changes only three fixture/claim dispositions; no additional production semantics are authorized or implemented. Reviewed the v6-to-v7 changes and clean full review. Earlier three desired assertions remain unresolved, separately named diagnostics; the aggregate predecessor does not claim following-instruction continuation, the seeded shield proves first Destroy application only, and the exact resumed two-payoff control is narrowly baseline compatibility. Their detailed v7 test names/results belong to the fresh peer receipt.

The private run hushbringer-production-private-v7.log passed5/5: the original3, game::zone_pipeline::departure_scope_tests::synchronous_batch_finalizes_exact_departures_before_return, and game::zones::tests::departure_scope_natural_replacement_pause_and_resume_restore_empty_stacks. The batch helper has a first-departing typed generic suppressor: both before vectors contain Dies, both after vectors are empty, actual victims/peer groups and final carrier state are checked. The natural-pause test casts a typed three-target ChangeZone with two real replacement options on the second target: first departure completes, remaining members stay on the battlefield, a natural ReplacementChoice is reached, the original in-memory frame/member stacks and allocator are empty before JSON, the restored default carrier is empty, and public actions complete the remaining moves with empty carrier at every returned action and normal settled priority.

The additional literal flush measurement uses cfg(test)-only boundary_flushes counters in DepartureSuppressionScopeState, incremented only at the two new capture-boundary flush sites. The Err/member helper requires (1,0) after members and barrier child, then (1,1) after error finalization, alongside dirty intermediate layers/no provisional snapshot checks. No production-build field, global/thread-local store, RefCell or serialized metric was added. Because this last test-only instrumentation was finalized during the preceding compile, a distinct stable-source rerun is in progress: hushbringer-production-private-v7-attempt-2.log, source manifest hushbringer-private-final-source-v7.sha256. Do not attach that new instrumentation claim to the earlier5/5 run.

## Stable private gate and production freeze

hushbringer-production-private-v7-attempt-2.log:5passed,0failed,0ignored. This run includes the final cfg(test) literal boundary-count assertions and both new helper tests. Verified all493 source hashes from hushbringer-private-final-source-v7.sha256 unchanged after the run. Production/private source frozen at this checkpoint; Cargo handed directly to the fresh v7 tests executor for its complete matrix and exact combined-source archive. No further production edits planned unless real diagnostics require them.

## V7 production-route map supplement (submitted fixtures; runtime pending peer)

The following closes names/branches that were pending in the earlier map. These are source-inspected fixture mappings, not a claim that the current v7 matrix has passed.

| Changed seam | First public branch and selected authority | Fixture and exact guard/discriminator |
|---|---|---|
| zone_pipeline::deliver_batch | BounceAll count=None gathers live creature IDs and calls move_objects_simultaneously_then; each request lends its selected ID to the same owner | unpaused_bounce_batch_and_selected_bounce_share_actual_departure_group, choice=false: both actual deaths, exact peer list and Some(before/after),0Spirit with Hush /1without, both orders, life22 continuation, pending batch empty. Companion private synchronous_batch_finalizes_exact_departures_before_return passes and directly distinguishes first-member static before/after outcomes. |
| EffectZoneChoice BounceAll | count=Some(2) with third eligible creature creates actual EffectZoneChoice; SelectCards validation owns chosen IDs | Same fixture choice=true: unchosen third remains, exact chosen peer group,0/1Spirit, life22, spell graveyard. No scope spans the prompt. |
| EffectZoneChoice PayCost | resolution PayCost Exile(count2,Battlefield) enters is_cost_payment=true prompt; one existing redirect makes both actual destinations Graveyard | effect_zone_choice_pay_cost_uses_selected_group_before_continuation: exact count/player prompt, chosen deaths/group/snapshots, spare remains, life22 continuation,0/1Spirit both orders. Suppression derives from delivered death, not proposed exile. |
| EffectZoneChoice Sacrifice epilogue | SelectCards chooses Traveler+other while Hush remains; continuation separately destroys Hush | chosen_sacrifice_closes_before_later_hush_departure_instruction: first record before/after both suppress, exactly selected peer; later Hush record alone and distinct turn index, final life22 and0/1Spirit. |
| Separate sacrifice cost components — NOT YET VERIFIED | Composite residuals split through continue_after_declared_mana_split; zero-mana immediate and mana-deferred paths require separate evidence | separate_spell_sacrifice_cost_components_bind_separate_worlds was corrected by the v7 owner from repeated builder setters (which overwrite) to one Composite. Runtime still pending. Read-only audit found the mana-deferred carrier flattens selections across components; a deferred Composite twin is required before certifying this row. |
| Chosen immediate/deferred sacrifice and retry | explicit casting or activation enters existing selected-cost prompt; invalid action precedes valid submission | chosen_spell_and_activation_cost_rejection_preserves_state_for_valid_retry PASSED in independent run: invalid selection preserves objects/prompt, valid retry settles correct cast/activation and suppression. |
| Library-position EffectZoneChoice and raw leaf | real selected movement plus targeted PutAtLibraryPosition -> existing library primitive wrapper | library_position_choice_and_targeted_leaf_preserve_non_death_events PASSED independently; dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins further requires grant/remove sources, exact after-world functioning status, actual top placement and retained LTB payoff. |
| Resumed ChangeZone remaining loop | real first-member replacement-order pause -> JSON restoration -> ChooseReplacement -> pending remaining tail | resumed_change_zone_tail_suppression_uses_authoritative_records: both orders, exact tail group excluding first member, both authoritative snapshots, one actual occurrence per identity/index and0Spirit. Separate explicit no-Hush replay compatibility and desired-one diagnostics retain v7 boundary; unpaused exact-one and later independent+1 remain required. |
| Live before filter/context | source FilterContext evaluated before movement using actual attached/combat/controller relations | attachment_relative_suppression_binds_live_relation_before_departure; enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat; two_suppression_controllers_and_between_event_control_rebind_are_distinct: positive relation/control guards and exact separate payoffs. |
| Immediate after filter/context | completed standalone zone/library departure flush removes or restores a grant/removal source before outcomes_for_record | dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins: source reaches destination, remaining suppressor authority flips, exact before/after vectors and1/0Any payoff, library nondeath retains1. |
| Ordinary unaffected cause/alias routes | registered ETB/attack, library-origin mill, exile; broad ETB gate unchanged | dedicated_mill_exile_and_torpor_only_etb_controls_remain_positive and enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat: actual distinct native trigger causes retain observable payoff. |
| Existing merge intrinsic layer behavior | public Mutate cast merges first, later departure routes existing components through intrinsic split; no merge/layer file edit | real_mutate_cast_departure_preserves_component_routing_and_normal_group_controls; merged_intrinsic_flush_limit_has_a_subject_first_positive_twin; separate ignored known_gap_merged_intrinsic_flush_should_preserve_later_member_world. Receipt must separate baseline limitation from repaired nonmerged groups. |

## Maintainer matrix supplement for pending v7 rows

| Seam / first dispatch | Selected authority, binding time and mode | Concrete storage/readers | Invalidation / hostile fixture / protocol |
|---|---|---|---|
| Unpaused batch or chosen BounceAll | gathered or validated ObjectId set; live incarnation at group start, explicit member at each delivery | DepartureScopeFrame.candidates/capture/emitted -> finish_departure_suppression -> record snapshot; existing BatchCompletion only after finish | Redirect/prevention supplies actual event key; unchosen spare stays; empty request no record; no pending-token field. Public batch/choice twins plus private helper above. |
| Choice PayCost redirected exile | selected payer and cards remain existing validator authority; delivered from/to decides whether death is matched | Existing WaitingFor::EffectZoneChoice carries choices before scope; scope lends ID through move_object, finishes before continuation and ActionResult event extraction | Proposed exile redirected to Graveyard is a reached death; continuation+spare guards; no choice/protocol enum changes. |
| Sacrifice component and continuation | existing component-specific selected IDs/controller; snapshot boundary closes before next component/instruction | casting_costs deferred/immediate owner, effect choice owner; persisted GameEvent carries outcomes into later scan | Distinct component and later Hush departure cannot rewrite earlier outcome; invalid input never opens group, valid retry works; existing rollback/event-vector authority retained. |
| Resumed tail | existing PendingChangeZoneIteration.remaining and current live incarnations bind at resume; no old owner survives prompt | new lexical owner only; existing pending payload unchanged; deferred collector runs after finish | Prior paused member excluded; actual occurrence key preserves identity; exact branch replay duplication explicitly retained, not generalized to unpaused routes. |
| Controller/combat/attachment filter | each suppression source controller and current condition/context live at before capture; outcomes latched for that occurrence | active_suppress_trigger_statics + matches_target_filter; after uses existing record filter authority | New controller between events affects next record only; attachment/combat reach guards distinguish live subject from incomplete synthetic snapshot. No listener/source authority rewrite. |
| Grant/removal inversion | functioning effective statics on either side of completed action; source departure changes layers | before outcomes_for_live_subject and after outcomes_for_record on same emitted record | Member capture never flushes intermediate group; standalone/library endpoint gets after flush; no rule/card schema addition. |
| Merge/independent child | original merge component authority remains; explicit None barrier isolates independent cause | original merge state/records untouched; only claimed main leaf event can be finalized by owner; noncapturing nested frame retains None | Existing intrinsic flush cannot certify general simultaneous layer worlds. Real Mutate guard and ignored desired diagnostic plus nonmerged positive; no merge parser/AST/transport promotion. |

Source-availability exact current reference: game/triggers.rs:1074 source_was_not_co_departed_into_zone and off-zone call at:2142. Both are unchanged. Co-dying other off-zone Any sources are rejected before the shared matcher; required surviving-observer and self-arrival cases do not claim that broader availability.


## Current verification epoch: sixth private test and cost provenance audit

Added game::zones::tests::departure_scope_standalone_after_world_is_final_at_each_leaf_return, pending compilation/run. Four tuples cover normal/library movement and departing grant/removal source. Each calls the real primitive and immediately checks inverse before/after suppression, the surviving source's functioning static, actual destination (and library front), literal boundary counts (1,1), and empty owner/member carrier. No trigger collector or post-return flush precedes those assertions. The previous private5 source manifest predates this test; do not present it as the final shared-source manifest.

No final source-freeze signal has been given to the worker builder. Production writes are idle for the peer's current compile epoch; integration work and final gates remain outstanding.

Read-only potential contradiction, not yet classified: plan v7 line286 requires deferred and chosen cost loops to capture one cost component and never join separate components. casting_costs.rs:264 splits Composite residuals into first current cost and remaining additional_cost_flow. handle_sacrifice_for_cost appends chosen deferred objects to a flat DeferredSacrificeSelection list (object_id/filter only), and pay_deferred_spell_sacrifices_at_commit currently wraps that entire list in one owner. can_defer_spell_sacrifice_until_mana_payment does not exclude a second component. The preexisting flattened carrier and new capture semantics must be distinguished using an actual mana-deferred Composite fixture and originalbase evidence before any disposition. No production change or new exception is authorized by this audit.


The v7 active attempt3 matrix reached 66 passing, 2 failing, 20 ignored. One failure is a test-only library-choice target declaration, being corrected by its owner. The other is a reached deferred Composite: both payments complete, but the first no-Hush tuple has nonempty co_departed peers and fails the required separate-component assertion. The immediate Composite twin passes. This is not relabeled as a supported grouping or a waived test. Exact active/baseline tuple receipts remain pending the test executor.


## Private six completion and cost stop

hushbringer-production-private-v7-attempt-3.log: cargo test -p engine --lib departure_scope -- --nocapture PASSED 6/6, 0 ignored. This is the first run that includes departure_scope_standalone_after_world_is_final_at_each_leaf_return. It passes all four normal/library × grant/removal immediate-return tuples, with correct final functioning static authority and literal boundary counts (1,1). The five prior helper/lifecycle tests also pass. Current production source hash manifest: hushbringer-private-six-source-v7.sha256. This is a check receipt, not a final worker source freeze.

Root confirmed the deferred Composite baseline comparison: Hush-first changes from baseline 1 Spirit to active 0 (new regression); Traveler-first changes from baseline 1 to active 0 (suppression repaired but still merged component peers); both no-Hush variants keep 1 but incorrectly share peers in both builds. Immediate Composite twin passes. Full active/baseline tuple receipts are supplied by hushbringer_impl_tests_v7. V7 line286 explicitly forbids joining separate cost components. No compatibility waiver is inferred. Root is routing fresh v8 planning/review for missing component authority; existing production semantics are paused, with no local patch improvised.

Root requests a structured PARTIAL handoff after independent scoped engine Clippy, originalbase compatibility isolation, and card-data generation/restoration. Full engine testing, per-seam mutation completion, full runtime acceptance, worker simulation and final review/commit remain for v8; they cannot be certified by this partial report.


## Exact stop artifact and build provenance correction

The authoritative stop and bound proof are hushbringer-implementation-stop-v7-components.md and hushbringer-implementation-stop-v7-components-proof.json. Active attempt4 is 66 passed/5 failed/20 ignored; the cost tuples are independently named, so an early no-Hush group assertion cannot hide the new Hush-first 0-versus-1 regression. Baseline full-include-ignored is 28 passed/63 failed/0 ignored. See the peer's final partial receipt for the final corrected exploratory library fixture and exact log hashes.

The attempted extra Battlefield-library-choice fixture did not reach a private-zone choice: its BF filter announced a target, while the empty-target private-zone scan is limited to Hand/Library. Its corrected fixture uses an actual two-of-three Hand-to-Library choice. This proves the existing nondeath selection route only; it does not claim a public BF library-choice departure group. Targeted BF library movement and the private direct leaf inverse remain covered separately. Both exploratory failures are preserved.

A final active compile after the originalbase shared-target run reused an external engine library without trigger_suppression despite the active source declaring it. This is a build-provenance failure, not grounds to remove required fields or assertions. Failed active attempt5 is compile-only. The peer is forcing a fresh active library build with only a source-file mtime refresh, preserving source bytes. Root now requires permanently distinct target directories: active checks use /home/ubuntu/repos/phase-verifiable-loop/target; originalbase checks use /home/ubuntu/repos/phase-hushbringer-baseline-tests/target; future mutation checks must use separate directories too. The upcoming originalbase manabrew reproduction will explicitly use its own target.


## Authoritative final v7 public runtime receipt

Final active source and forced active-library rebuild are bound in hushbringer-v7-active-attempt-6/manifest.json, cargo.log, final-confirmation.log and final-confirmation.exit. The confirmed runtime result is 67 passed, 4 failed, 20 ignored. The 4 failures are the unchanged deferred Composite requirements below. Full fixture/tuple, baseline, ignored-diagnostic and pending-seam details are in hushbringer-implementation-tests-v7.md and hushbringer-tests-v7-final-partial-receipt.json. No isolated per-seam rollback/mutation has run: zero completed, all remain pending v8. The exact general resolver-reentry rollback is not yet production-reachability-proven.

This table supersedes provisional test status text in earlier chronological sections. A passed test is evidence only for its reached tuples; it does not waive the failed cost-component contract or certify the remaining mutation/worker/full-engine gates.

| Integration test | Final active result |
|---|---|
| aggregate_payment_no_hush_and_surviving_hush_single_payment_controls | passed |
| ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility | passed |
| ambiguous_reflexive_compatibility_and_empty_creation_disposal | passed |
| ambiguous_registered_delayed_matchers_preserve_ungated_compatibility | passed |
| attachment_relative_suppression_binds_live_relation_before_departure | passed |
| augment_subject_preserves_the_sba_owner_and_co_departed_observer_payoff | passed |
| change_zone_choice_uses_selected_objects_and_finalizes_before_continuation | passed |
| chosen_sacrifice_closes_before_later_hush_departure_instruction | passed |
| chosen_spell_and_activation_cost_rejection_preserves_state_for_valid_retry | passed |
| clause_local_disjunction_registers_once_for_eligible_sibling | passed |
| co_departed_observer_and_self_trigger_both_use_before_suppression | passed |
| completed_keep_sacrifice_sweeps_share_one_boundary_across_choice_routes | passed |
| controller_relative_and_conditional_suppression_bind_before_departure | passed |
| cross_pause_batch_preserves_completed_segment_compatibility_and_no_hush_twin | passed |
| dedicated_mill_exile_and_torpor_only_etb_controls_remain_positive | passed |
| delayed_cleanup_retains_persistent_and_expires_this_turn_listeners | passed |
| delayed_first_suppressed_occurrence_retains_one_shot_or_recurring_listener | passed |
| delayed_native_sacrifice_and_exile_alternatives_remain_eligible | passed |
| delayed_reflexive_suppression_discards_unmatched_listener | passed |
| delayed_same_occurrence_tries_eligible_alternative_exactly_once | passed |
| destroy_guard_regeneration_and_indestructible_preserve_actual_departures_only | passed |
| destroy_self_reference_and_partial_illegality_preserve_existing_guards | passed |
| devour_child_sacrifice_is_independent_of_parent_co_entry | passed |
| distinct_controller_delayed_listeners_keep_creation_source_and_controller | passed |
| dynamic_after_world_inverse_and_library_leaf_keep_runtime_positive_twins | passed |
| effect_zone_choice_pay_cost_uses_selected_group_before_continuation | passed |
| empty_sweep_and_zero_choice_do_not_leak_into_later_death | passed |
| enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat | passed |
| first_departing_granter_preserves_later_member_types_and_trigger | passed |
| from_anywhere_and_dies_observers_choose_different_worlds | passed |
| granted_suppression_and_granted_death_trigger_use_effective_abilities | passed |
| hand_library_choice_preserves_selected_cards_and_nondeath_payoff | passed |
| haunt_payoff_uses_the_linked_subject_death_before_world | passed |
| inherited_sacrifice_current_controller_and_unauthorized_nonanaphoric_siblings | passed |
| inherited_sacrifice_no_hush_and_single_slot_controls | passed |
| known_gap_aggregate_paid_continuation_should_resume_sequential_sibling | ignored |
| known_gap_aggregate_payment_should_group_completed_selection | ignored |
| known_gap_aggregate_payment_should_group_completed_selection_reversed | ignored |
| known_gap_ambiguous_registered_delayed_should_be_suppressed | ignored |
| known_gap_cast_created_regeneration_shield_should_survive_to_destroy | ignored |
| known_gap_cast_created_regeneration_shield_should_survive_to_destroy_hush | ignored |
| known_gap_cast_created_regeneration_shield_should_survive_to_destroy_hush_reversed | ignored |
| known_gap_cast_created_regeneration_shield_should_survive_to_destroy_traveler_reversed | ignored |
| known_gap_cross_pause_batch_should_share_full_group_suppression | ignored |
| known_gap_inherited_target_sacrifice_should_group_both_departures | ignored |
| known_gap_inherited_target_sacrifice_should_group_both_departures_reversed | ignored |
| known_gap_legacy_direct_delayed_should_be_suppressed | ignored |
| known_gap_legacy_when_dies_or_exiled_should_be_suppressed | ignored |
| known_gap_legacy_when_dies_should_be_suppressed | ignored |
| known_gap_legacy_when_enters_should_be_suppressed | ignored |
| known_gap_legacy_when_leaves_filtered_should_be_suppressed | ignored |
| known_gap_merged_intrinsic_flush_should_preserve_later_member_world | ignored |
| known_gap_restricted_registered_delayed_should_be_suppressed | ignored |
| known_gap_resumed_change_zone_no_hush_should_pay_once | ignored |
| known_gap_resumed_change_zone_no_hush_should_pay_once_reversed | ignored |
| legacy_direct_delayed_identity_and_nondeath_siblings_preserve_lifetime | passed |
| legacy_direct_delayed_no_hush_positive_controls | passed |
| legacy_direct_delayed_surviving_hush_bypass_compatibility | passed |
| library_position_choice_and_targeted_leaf_preserve_non_death_events | passed |
| merged_intrinsic_flush_limit_has_a_subject_first_positive_twin | passed |
| multi_object_spell_sacrifice_cost_preserves_commit_and_suppression | passed |
| natural_effect_zone_choice_finalizes_before_chained_hush_departure | passed |
| not_equals_battlefield_rejects_death_but_allows_real_library_graveyard_move | passed |
| opponent_scoped_keep_sweep_preserves_owner_and_out_of_scope_board | passed |
| oracle_wrath_hush_first_suppresses_simultaneous_traveler_death | passed |
| oracle_wrath_traveler_first_suppresses_simultaneous_traveler_death | passed |
| oracle_wrath_without_hush_creates_exactly_one_spirit | passed |
| ordinary_ambiguous_origins_preserve_live_collection_compatibility | passed |
| paused_choice_state_roundtrip_and_following_action_have_no_stale_scope | passed |
| real_mutate_cast_departure_preserves_component_routing_and_normal_group_controls | passed |
| remaining_complete_producers_capture_each_actual_group | passed |
| repeated_object_id_retains_distinct_incarnation_and_event_suppression | passed |
| resumed_change_zone_no_hush_duplicate_payoff_compatibility | passed |
| resumed_change_zone_tail_suppression_uses_authoritative_records | passed |
| seeded_regeneration_guard_preserves_actual_departures_only | passed |
| self_from_anywhere_exception_functions_in_destination_with_hush_surviving | passed |
| separate_deferred_spell_sacrifice_cost_components_bind_separate_worlds | failed |
| separate_deferred_spell_sacrifice_cost_components_hush_first | failed |
| separate_deferred_spell_sacrifice_cost_components_no_hush_reversed | failed |
| separate_deferred_spell_sacrifice_cost_components_traveler_first | failed |
| separate_spell_sacrifice_cost_components_bind_separate_worlds | passed |
| sequential_destroy_instructions_bind_separate_before_worlds | passed |
| single_departure_after_world_observes_ability_removal_source_leaving | passed |
| standalone_zone_leaf_after_world_inverse_reaches_unowned_sacrifice | passed |
| stripped_or_phased_suppressor_allows_the_same_reached_death | passed |
| successive_sba_iterations_bind_new_world_after_suppressor_dies | passed |
| two_suppression_controllers_and_between_event_control_rebind_are_distinct | passed |
| two_target_destroy_owns_one_event_in_both_target_orders | passed |
| unattach_fallback_and_native_cause_remain_distinct | passed |
| unpaused_bounce_batch_and_selected_bounce_share_actual_departure_group | passed |
| unpaused_change_zone_no_hush_payoff_remains_exactly_one | passed |


## Scoped engine Clippy result

cargo clippy -p engine --all-targets -- -D warnings PASSED with saved remote exit0. Log hushbringer-production-engine-clippy-v7.log; exit receipt hushbringer-production-engine-clippy-v7.exit. Runtime6m35s; no warnings or source changes. SSH transport later returned255/Broken pipe, but the remote command completed and wrote its explicit successful exit before disconnect. The completed log/receipt and absence of remaining Cargo processes establish the actual result. Do not replace the command result with the transport code.

Originalbase package reproduction is now running with CARGO_TARGET_DIR=/home/ubuntu/repos/phase-hushbringer-baseline-tests/target. Preflight confirms no production/Cargo manifest diff in that checkout and target is not a symlink to the active cache. Card-data and final partial source-hash/status checks remain.


## Final independent gates and released source

Production ownership and Cargo are released. No production semantics were changed after the cost stop. There are no remaining source writes or Cargo processes owned by this executor. Root may assign the fresh v8 executor to the active checkout. This release is a stopped implementation handoff, not a worker acceptance freeze.

| Command / check | Actual result | Evidence |
|---|---|---|
| cargo test -p engine --lib departure_scope -- --nocapture | PASS6/6,0ignored | hushbringer-production-private-v7-attempt-3.log |
| Event missing/empty/captured history serde test | PASS1/1,0ignored; source unchanged since run | hushbringer-production-serde-v6.log |
| cargo clippy -p engine --all-targets -- -D warnings | PASS, command exit0 | hushbringer-production-engine-clippy-v7.log and .exit |
| cargo clippy --all-targets -- -D warnings | FAIL at unrelated manabrew missing SetFullControl match arm | hushbringer-production-clippy-v6-attempt-2.log |
| Originalbase cargo clippy -p manabrew-compat --all-targets -- -D warnings, baseline-owned target | Reproduced SAME E0004 at manabrew-compat/src/lib.rs:1601, command exit101 | hushbringer-baseline-manabrew-clippy-v7.log and .exit; unchanged-source proof hushbringer-manabrew-source-baseline-v6.txt |
| ./scripts/gen-card-data.sh | PASS, command exit0; schema validated35802cards | hushbringer-card-data-v7.log and .exit |
| cargo fmt --all -- --check | PASS, exit0 | hushbringer-format-final-partial-v7.log and .exit |
| git diff --check | PASS after generator restoration | final command output; final tracked patch |
| Final source comparison | All493 private-tested production Rust source hashes unchanged | hushbringer-private-six-source-v7.sha256 |
| Final shared-source manifest |2051 tracked/untracked nonignored files under crates plus root Cargo/config/toolchain files | hushbringer-production-final-partial-source-v7.json and .sha256 |
| Public v7 final module |67pass/4costfail/20ignored, command101 | hushbringer-v7-active-attempt-6/final-confirmation.log and .exit |
| Full cargo test -p engine | NOT RUN to acceptance; explicitly deferred until cost fix | root v8 handoff instruction |
| Per-seam rollback/mutation, final frozen worker and independent review | PENDING, zero per-seam mutations complete | v7 tests partial and root-owned later gates |

Originalbase compatibility source preflight checked an empty production/Cargo diff, and its target directory is independent of the active cache. It reproduced the exact same GameAction::SetFullControl missing exhaustive arm in both lib and lib-test, so no out-of-scope compatibility fix was made. Baseline and card-data SSH transports later returned255/reset or timeout, but each completed remote command wrote its explicit .exit receipt:101 and0 respectively. Treat the saved command result separately from transport status.

Card-data generation produced2870 token presets and rebuilt the generators to embed the new catalog. It validated35802 exported cards, reported31668 supported (88.5%), and emitted1102 parser warnings (4 ignored-remainder,1043 swallowed-clause,55 target-fallback). These are observed generator diagnostics, not newly claimed parser support. No parser production file is changed. It generated the ignored card/coverage/deck outputs and exactly two tracked source deltas: known-tokens.toml and oracle-subtypes.json. Both generated files and their exact diff were archived in hushbringer-known-tokens-generated-v7.toml, hushbringer-oracle-subtypes-generated-v7.json and hushbringer-generator-source-delta-v7.patch. Both sources were restored BYTE FOR BYTE to saved pre-generation bytes, with hashes in hushbringer-generator-restoration-v7.json. Final git status exactly equals hushbringer-pre-carddata-status-v7.txt. The generated output reflects the regenerated catalog; restored source remains in the authorized diff. No generated catalog/subtype change is proposed for commit.

Final source manifest JSON SHA256:0301cf3cce5276bedb0ef6c68451c6ec81adf3cf3877cc1bad099a4c5aba9263. Tracked patch: hushbringer-production-final-partial-tracked-v7.patch; stat: hushbringer-production-final-partial-stat-v7.txt. The tracked patch necessarily omits new untracked modules; both are included in the source manifest and peer source.tar.gz. Exact28-file change list follows. The additional discovered constructor files carry only mechanical None defaults, as allowed by the plan; loop_shortcut is exactly two Debug field-string insertions and no other changed bytes. The cfg(test) flush counters and six private tests are verification-only; no production counter is serialized or present in non-test builds.

- crates/engine/src/game/augment.rs
- crates/engine/src/game/casting_costs.rs
- crates/engine/src/game/derived_views.rs
- crates/engine/src/game/effects/change_zone.rs
- crates/engine/src/game/effects/choose_and_sacrifice_rest.rs
- crates/engine/src/game/effects/destroy.rs
- crates/engine/src/game/effects/mod.rs
- crates/engine/src/game/effects/sacrifice.rs
- crates/engine/src/game/engine_resolution_choices.rs
- crates/engine/src/game/filter.rs
- crates/engine/src/game/game_object.rs
- crates/engine/src/game/haunt.rs
- crates/engine/src/game/mod.rs
- crates/engine/src/game/sba.rs
- crates/engine/src/game/stack.rs
- crates/engine/src/game/trigger_matchers.rs
- crates/engine/src/game/trigger_suppression.rs
- crates/engine/src/game/triggers.rs
- crates/engine/src/game/zone_pipeline.rs
- crates/engine/src/game/zones.rs
- crates/engine/src/types/events.rs
- crates/engine/src/types/game_state.rs
- crates/engine/tests/integration/issue_3277_captain_nghathrod_eliminated_opponent.rs
- crates/engine/tests/integration/issue_5332_gandalf_trigger_doubling.rs
- crates/engine/tests/integration/loop_shortcut.rs
- crates/engine/tests/integration/madame_null_integration.rs
- crates/engine/tests/integration/main.rs
- crates/engine/tests/integration/trigger_suppression_event_timing.rs


## Remaining obligations for v8

1. Implement only the newly reviewed component-authority design after its full plan review. Fix the new deferred Hush-first regression and all four active deferred-component failures without changing the required payoff/group assertions. Preserve immediate Composite and one-component multi-object controls, payment/rollback authority and serialization compatibility.
2. Rerun the complete public matrix, primary originalbase/fixed comparison and six private lifecycle helpers against the final v8 source. Include the exact source/target provenance; never reuse active/target for baseline or mutation trees.
3. Complete one reaching isolated rollback per claimed producer/consumer seam, including Augment member handoff, after-boundary flush omission and new-mid-leaf-flush checks. Zero such mutations were completed here. Establish an actual production-reaching general resolver barrier discriminator or carry the concrete unproven reachability finding to review; moving another parent candidate alone does not discriminate because member binding also checks current object/incarnation.
4. Complete full cargo test -p engine, repeat scoped Clippy/format/card-data if final source changes require it, and retain the independently proven unrelated workspace manabrew failure. Do not call the full workspace Clippy gate green.
5. Preserve the existing bounded limits and v7 A/B/C dispositions described above: ambiguous-origin consumer compatibility; other co-departed off-zone Any source availability; direct delayed bypasses; aggregate/inherited ungrouped sacrifice; full cross-pause grouping; exact resumed duplicate dispatch; cast-created regeneration persistence; aggregate following continuation; intrinsic merge/nested layer-world limits. None waive the newly failed deferred component contract.
6. Root owns rebuilding both frozen workers with its revised isolated-target builder, running the preserved acceptance checker, independent combined-diff review, scoped commit and final certifiable build. No worker acceptance, commit or push is claimed by this executor.

Final CR evidence:65 unique production added/moved references in hushbringer-production-cr-diff-v7.txt and79 combined references in hushbringer-combined-cr-diff-v7.txt; all exist in docs/MagicCompRules.txt, with exact comment/rule excerpts preserved. Written-rule meaning was checked by the responsible implementation/test writer. Previously corrected moved annotations include Roles704.5z, battle attachment310.10, protector704.5x/y and310.9, and speed702.179a; incorrect blanket603.2g/704.7 suppression/simultaneity comments were not propagated. Fresh review should assess the code and these exact annotations, not infer parser/provenance support from typed fixtures.

No commits, pushes, Coworld changes, local source edits, or child agents were made by this executor. This executor's only shared checkout mutations after the implementation stop were generator-owned data output followed by exact restoration; existing production code remains available for the fresh bounded executor.

Peer final handoff is now written: hushbringer-implementation-tests-v7.md SHA25652456b23142de241fdb299e43d691f3dcb63127a43a51a2f09d5929ed309d71a; hushbringer-tests-v7-final-partial-receipt.json SHA2560e0b00af0cb605871bbed6d864d000135c6b6aaaeebb70e545058bd3b330ce0e. It binds64 proof artifacts and records the same source ownership release.
