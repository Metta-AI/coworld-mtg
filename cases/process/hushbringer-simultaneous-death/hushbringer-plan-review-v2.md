# Full review of hushbringer-plan-v2.md

**Not clean: two bounded plan gaps remain.** The revised primary design is sound for the explicitly enumerated ordinary-trigger paths and producer boundaries. The remaining issues concern undisclosed producer bounds and a production consumer changed indirectly by the shared matcher. They do not justify a general batching or delayed-trigger rewrite.

Review target: `/home/ubuntu/coworld-migration-20260904/hushbringer-plan-v2.md`, all 272 lines, against `/home/ubuntu/repos/phase-verifiable-loop` at `2dec6c88915db4697706234a7ba2fcedd97b1689`. HEAD matched and the checkout was clean when inspected. Every command, source read, current-source request, and this artifact write ran through `ssh nishadsingh-box-4`. No implementation, build, test execution, commit, local checkout operation, or subagent was performed.

The review followed `.claude/skills/review-engine-plan/SKILL.md`, remote AGENTS.md/CLAUDE.md, and the applicable add-trigger, add-static-ability, card-test, and existing-handler portions of add-interactive-effect checklists. This is a fresh full review, not only a recheck of the preceding review's three findings.

## 1. State or implement the bounds for additional complete sacrifice actions

**Classification: pre-existing unmodeled simultaneous batches; incomplete scope/coverage claim in this plan. Not an established regression introduced by the proposed change.**

The plan makes complete, unpaused producer groups part of acceptance (lines 119–124, 154, 242), and treats the two-target Destroy route as required even though it has no existing stamp. Its producer table does not account for two analogous complete sacrifice routes:

- `crates/engine/src/game/engine_payment_choices.rs::handle_ward_sacrifice_choice`, lines 1574–1598, handles `min_total_power = Some(...)`. It validates the entire unique selection and its aggregate power **before** a single loop sacrifices every chosen permanent. This is a complete one-action selection, with no pre-move capture or group stamp. It is separate from the explicitly documented sequential, one-per-round-trip Ward branch at lines 1606–1628.
- This is a real production path: `engine_payment_choices.rs:726–762` creates the aggregate `WardSacrificeChoice` from an `AbilityCost::Sacrifice(SacrificeRequirement::Aggregate)`; `engine.rs:4634` dispatches the response; `tests/integration/issue_864_phyrexian_dreadnought.rs:136–174` reaches the prompt through casting, pays it, selects two creatures, and verifies both leave.
- `crates/engine/src/game/effects/sacrifice.rs::resolve`, lines 344–402, has a separate loop over already bound `targeted_objects`. The plan covers only its all-eligible branch at lines 277–299. `effects/mod.rs::effect_object_targets`, lines 223–252, explicitly preserves all inherited object targets for `ParentTarget`; the sacrifice loop explicitly supports `ParentTarget` and `ParentTargetSlot` at lines 365–375. It does not necessarily reduce to one object. This path also bypasses the all-eligible branch, player-scope sweep, and EffectZoneChoice handler.

With Hushbringer processed before Traveler in either complete loop, proposed leaf defaults capture Traveler after Hushbringer is gone unless the outer loop supplies an authoritative before snapshot. Reversing the order gives a different snapshot. This is the same uncovered grouping issue as the newly added two-target Destroy seam. The old broad live gate already fails when Hushbringer has departed; these findings must not be reported as new regressions merely because the new leaf defaults make the two orders distinguishable.

**Required revision:** choose and document one of these bounded dispositions for each route:

1. Include the completed loop, using the same capture/finalize helpers around the already validated selected set, before continuation/collection, with the existing sacrifice primitive and payment validation unchanged; or
2. Explicitly exclude its pre-existing unmodeled batch, narrow the all-complete-groups/coverage wording accordingly, and retain a characterization/no-regression test. Do not describe the aggregate branch as the existing cross-pause limitation: its selected set is known before any move.

If included, add a production-path test with Hushbringer and Traveler in both selection orders, actual departure/cost-success assertions, zero Spirit, and a no-Hush positive twin producing one Spirit. For the aggregate route, use a labeled typed unless-payment fixture or establish the named-card trigger before introducing Hushbringer; simply casting Phyrexian Dreadnought beside an already functioning Hushbringer never reaches the payment prompt because its ETB trigger is suppressed. The targeted/anaphoric route can be exercised by a typed cast chain whose preceding effect binds two legal object targets and whose single ParentTarget sacrifice instruction consumes them; do not invoke the raw effect resolver. Preserve current-controller sacrifice authority and test the single-object sibling.

No cross-pause carrier, cost resolver duplication, or generic scheduler is required to repair either complete loop.

## 2. Add delayed-trigger consumers to the change map and runtime validation

**Classification: indirectly changed production consumers omitted from the verification map; existing bypass gaps must be identified separately. No current-source evidence proves that the intended shared predicate itself introduces a wrong runtime result.**

The plan's route inventory stops at registered TriggerMode matchers and ordinary collection. The proposed change to `zone_change_clause_matches` also changes two delayed-trigger production paths:

- `crates/engine/src/game/triggers.rs::delayed_trigger_event_with_index`, lines 6321–6327: `DelayedTriggerCondition::WheneverEvent` calls the same registered matcher directly.
- Lines 6336–6348: `WhenNextEvent` calls that matcher for its primary and optional alternative trigger.
- `check_delayed_triggers`, lines 5755–5832, uses that result to fire and remove a one-shot trigger, retain a persistent trigger, or discard an unmatched reflexive trigger. These consumers do not pass through the old whole-event continue in `collect_pending_triggers`.

Consequently, moving suppression into the ordinary matcher changes matching, trigger lifetime, and alternative selection for these paths even if no delayed-trigger code is edited. The plan has no delayed-trigger runtime row or explicit disposition for them. Ordinary observer and batched tests do not exercise the one-shot removal/persistence branch.

Adjacent legacy delayed variants follow separate routes: `WhenLeavesPlay` at 6252–6261; `WhenDies` and `WhenLeavesPlayFiltered` at 6263–6282; `WhenDiesOrExiled` at 6297–6319; and `delayed_zone_change_event_with_index` at 6354–6384. These currently bypass both the broad ordinary gate and the shared clause matcher. Their missing Hushbringer suppression is pre-existing. `WhenEntersBattlefield` is another legacy direct route at 6285–6294. Do not silently claim that adding the event field repairs these variants.

**Required revision:** enumerate this delayed-consumer split and add production tests for the paths that will change through the shared matcher. At minimum:

- Create a typed `WhenNextEvent` death listener through its normal effect/cast path. Cause a reached death with Hushbringer surviving or co-dying; assert no payoff and that an ordinary non-reflexive one-shot remains available. After Hushbringer is gone, cause another matching death and assert exactly one payoff and consumption. Include the no-suppression positive control.
- Exercise a `WheneverEvent` death listener through normal creation and apply/stack flow, proving a suppressed occurrence does not fire and a later unsuppressed occurrence does fire without removing the persistent listener.
- Cover an alternative non-death event/clause where the death match is suppressed, so a broad event rejection cannot discard a legitimately matching alternative. Keep native sacrifice-cause/exile behavior positive and preserve reflexive lifetime handling.
- State whether the legacy direct delayed variants remain characterized pre-existing exclusions or receive a small shared-predicate adapter. A general delayed-trigger identity/dispatch rewrite is not required by this review.

This is required by review-engine-plan's claim-to-production-test requirement and the requested protection of adjacent trigger consumers. The minimum revision is an honest scope map plus discriminating tests for the already touched shared matcher consumers, not automatic expansion into all existing delayed mechanics.

## Checks that passed

The previous three findings are addressed concretely:

- **Haunt:** both registry entry points route to `haunt.rs::match_haunted_creature_dies` (125–149); the planned adapter retains the Haunt-link subject, recorded Creature guard, and before-event timing. Surviving-Hush and co-death tests distinguish adapter failure from capture failure.
- **Choose-and-sacrifice-rest:** all five completed entry/bypass paths converge on `sacrifice_unchosen` (517–580). Moving sole sweep finalization into that helper avoids duplicated authority and covers choices made before the first sacrifice. The plan's empty/auto/APNAP/total-power tests have positive reach guards.
- **Multi-target Destroy:** `destroy::resolve` (181–236) is correctly distinguished from `resolve_all`. The plan preserves `destroy_single_object` as the guard/replacement authority and requires cast tests in both target orders, partial legality, SelfRef, regeneration, and prevention siblings.

The broader architectural review found:

| Required dimension | Assessment |
|---|---|
| Class versus card | Pass. Existing SuppressTriggers/typed zone-trigger behavior is the abstraction; no card-name special case or new mechanic. |
| Building-block reuse | Pass. Functioning-static iterator, existing filters, ZoneChangeRecord, producer stamps, ordinary clause matcher, Haunt link, and standard stack path are reused. New event-outcome storage is justified because source/controller/filter applicability cannot be recovered from a later world. |
| Analogous trace | Pass. Suppression, co-departed observer, ChangesZone, Changeling/layers, Haunt, interactive selection, and Destroy traces name the relevant existing files and boundaries. |
| Layer placement | Pass. Types and runtime work stay in engine; no transport/frontend game logic. No new UI text or i18n work. |
| Rust/data model | Pass in principle. Typed before/after outcomes and Option distinguish authoritative empty from absent historical context. No borrowed state or whole-GameState clone is proposed. |
| Nom/parser | Not applicable. No parser edits or accepted-but-unimplemented grammar is proposed. Runtime fixture parsing remains a reach guard. |
| CR and card premise | Pass. Relevant numbers were checked against remote docs/MagicCompRules.txt. Current Scryfall Hushbringer Oracle and Wizards-sourced rulings were independently fetched remotely; they support simultaneous suppression, artifact-creature/LTB causality, replacement/cause-event distinctions, and the self/from-anywhere exception. The plan correctly rejects the old 603.2g suppression explanation and 704.7 simultaneity claim. |
| Skill adherence | Pass except the missing consumer/scope test map above. Existing choice types, handlers, legal actions, and transport interfaces stay intact; tests use normal cast/apply paths and real prompts. |
| Verification matrix | Strong for its enumerated seams. Both directions, no-Hush reach controls, event provenance, authoritative empty serde, replacements/no-ops, and rollback discrimination are specified. Gap 2 identifies indirectly changed paths omitted from it. |
| Identity/provenance | Pass in principle. Binding is at the logical producer event, outcomes live on emitted/parked records, bounded event slices plus turn_zone_change_index prevent later ObjectId incarnations from being rewritten, and no lingering global suppression set is proposed. |
| Scope matrix | Needs gap 1's explicit dispositions and gap 2's delayed route split. No general repair of pre-existing cross-pause batching is required. |

Constructor review agrees with the plan's production constructor choices: `game_object::snapshot_for_zone_change`, the synthetic filter/stack constructors, and `test_minimal`; other construction sites use these or test struct updates. The ledger clone at `zones.rs:918` precedes emitted-record finalization, so leaving non-dispatched history copies None is a coherent documented contract. Existing emitted/parked GameEvent serialization must carry the new field verbatim.

The registered death-capable routes ChangesZone/ChangesZoneAll/LeavesBattlefield, Haunt, and Unattach are covered. Dedicated mill/exile/EntersOrAttacks guards support their stated exclusions. Immediate/Always matches any event (`trigger_matchers.rs:3064–3071`), but the source inventory shows only registry/type/index/test uses and no production parser/synthesis definition; this is not raised as a blocker to the bounded supported suppression fix.

## Implementation constraints and residual assumptions

- The plan already forbids per-member layer flushes that reinterpret an intermediate board as a complete simultaneous event. This prohibition must be enforced in the helper design: overwriting provisional snapshot fields after a group does not undo gameplay mutations caused by an intermediate flush. For example, `destroy_single_object` reads live effective indestructibility at `destroy.rs:156–159`. A typed two-target case with the first target granting the second indestructible is a useful focused guard if the implementation adds any leaf-level flushing. This is an implementation-review watch item, not a new plan blocker because the prohibition is explicit.
- The planned self-from-anywhere test must actually reach the destination-functioning trigger path. The co-departed availability guard and LKI partition must not turn the negative sibling into an unreachable test. The plan explicitly calls this out and gives it a separate positive test.
- Cross-pause simultaneity remains excluded as instructed. The existing ignored characterization must remain visible. Completed-segment serialization evidence cannot be described as full unpaused-equivalent simultaneity.
- These are plan findings, not test results. The frozen harness evidence cited by the plan was not independently rerun in this review. Fresh changed-checkout build/test and worker evidence remain implementation acceptance requirements.

After the two bounded revisions, request another fresh full review. No additional confirmed blocking gap was found in the rest of the artifact.

