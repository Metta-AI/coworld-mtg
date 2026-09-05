# Full review of Hushbringer plan v8

Verdict: REVISE — three blocking gaps. This is a fresh review of the entire 634-line plan, not a review of only the v8 addition. The partial implementation is not accepted. No engine/test source was edited and no build, Cargo command, test, commit, or child agent was invoked by this reviewer.

## Blocking findings and required revisions

### R1 — Preserve concession and audit the global-action boundary before applying legacy-cast preflight

Priority: P1. Dimensions: runtime rules, action scope, recovery contract, verification matrix.

Evidence:
- Plan /home/ubuntu/coworld-migration-20260904/hushbringer-plan-v8.md:170 places the provenance preflight after actor authorization but before action dispatch, exempting only CancelCast and OutOfBandPreference.
- /home/ubuntu/repos/phase-verifiable-loop/crates/engine/src/types/actions.rs:1463 enumerates OutOfBandPreference. Concede is instead in the RulesDecision group at :1545.
- /home/ubuntu/repos/phase-verifiable-loop/crates/engine/src/game/engine.rs:243 authorizes the actor before the action is dispatched at :263. Its check_actor_authorization at :2122 explicitly permits a player's own concession regardless of whose prompt is pending, while rejecting a player_id different from the actor.
- The existing apply_action concession branch at engine.rs:3108 bypasses WaitingFor and eliminates the player at :3114.
- /home/ubuntu/repos/phase-verifiable-loop/docs/MagicCompRules.txt:340, CR 104.3a, permits concession at any time.

Under the specified preflight, a nonempty legacy/malformed deferred queue in P0's pending cast rejects both P0's lawful concession and P1's lawful concession before the existing concession branch. This is a concrete new rules regression; Concede is neither CancelCast nor an OutOfBandPreference. Valid component queues do not reveal it.

Required revision:
1. Explicitly exempt Concede from this cast-provenance preflight, preserving the existing actor authorization first. Keep recovery validation for actual cast/payment progression.
2. Audit the other pre-WaitingFor global branches, especially Debug, GrantDebugPermission, and RevokeDebugPermission (actions.rs:1546 and engine.rs:2137/:3122), and specify their disposition. Preserve their existing independent authority/permission gates; do not accidentally make cast provenance their new authorization policy. No broad action-class redesign is needed.
3. Add natural pending-cast checkpoint tests with only the serialized component metadata removed or malformed. Prove the caster and the other player can each concede on their own behalf; spoofed player_id still returns WrongPlayer. Retain valid-queue controls, rejection of ordinary payment progression before mutation, CancelCast/reannouncement, and preference controls. Use the public action boundary and assert actual elimination/terminal or surviving-player state as appropriate.
4. Include this case in the action-scope and preflight mutation rows. A mutation restoring the overly broad preflight must fail the concession assertion, while removing provenance validation must still fail the existing unchanged-hand/payment guards.

### R2 — Resolve the missing production discriminator for the resolver wrapper before calling the full plan executable

Priority: P2, blocking architectural review. Dimensions: concrete claim-to-test mapping, production reach, identity provenance.

Evidence:
- Plan :498 supplies same-iteration SBA, public Devour/co-entry, and a helper-only overlapping-candidate test.
- Plan :563 explicitly says the real production resolver-wrapper-only discriminator is still missing, correctly notes that another parent candidate is insufficient, and says private barrier tests/public Devour do not satisfy it.
- The changed production seam is /home/ubuntu/repos/phase-verifiable-loop/crates/engine/src/game/effects/mod.rs:5995, wrapping resolve_ability_chain with without_departure_member at :6001.
- /home/ubuntu/repos/phase-verifiable-loop/crates/engine/src/game/zones.rs:736 binds a specific current ObjectId and incarnation. The binding is limited to the selected candidate at :744; a child moving a different candidate does not demonstrate accidental borrowing of that binding.
- The public Devour fixture in /home/ubuntu/repos/phase-verifiable-loop/crates/engine/tests/integration/trigger_suppression_event_timing.rs:2600 exercises an entering parent and a completed child choice. Its parent does not provide the same active battlefield member binding required to distinguish this wrapper.
- The mandatory review skill requires a production entry point, runtime test, exact revert-failing assertion, and positive/sibling guards for every changed behavioral seam. A statement that a fixture must later be found is not that map.

Required revision:
1. Before the next full review, trace and specify a real public cast/apply/replacement execution that reaches resolve_ability_chain while the relevant exact parent member ObjectId/incarnation binding remains active, then reaches an independent cause involving that same binding. Name the actual existing effect/replacement constructor and execution path, natural setup, event timing, and precise observable assertion. Do not invent a reachable flow or manually install execution scope/WaitingFor.
2. Show why reverting only this resolver wrapper, leaving the exact member identity checks and all other barriers intact, makes that assertion fail. Preserve positive reach, actual occurrence counts/keys, parent/child membership, and following-action closure guards.
3. If the wrapper's distinguishing situation is unreachable in current production, provide the complete source reachability proof and a reviewed disposition of the wrapper/claim and test obligation. Do not silently count a helper test as production coverage or merely delete the gate.
4. Keep the private transparent-member/None-barrier tests and public Devour/SBA tests as their own useful obligations. This finding does not invalidate those tests; they do not prove this specific changed seam.

This is different from an already concrete test whose execution is pending. Ordinary listed mutations may properly remain execution gates after clean plan review. Here the production fixture itself is unspecified.

### R3 — Add an explicit bounded disposition for four newly proved LKI/controller regressions

Priority: P1 for acceptance; blocking plan revision. Dimensions: layer authority, regression scope, unchanged sibling guarantees, verification.

The root's frozen-source broad runs found four additional failures beyond the known component failures:
- game::effects::tests::bounce_followup_draws_when_caster_controlled_parent_target
- game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield
- game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry
- oversimplify_per_player_fractal::oversimplify_per_player_fractal_counters_match_exiled_power

The active library result is 16,574 passed / 3 failed / 7 ignored. The separate integration result is 3,042 passed / 5 failed / 22 ignored: four known deferred-component failures and Oversimplify. On the original baseline with an isolated target, all six zone_change_object_condition_ library tests passed, the exact bounce test passed, and the exact Oversimplify integration test passed. Therefore these are introduced test regressions, not pre-existing failures that can be waived by proximity to an exclusion.

Source evidence and the unresolved mechanism:
- triggers.rs:11802 sets printed base power/toughness to 1 but only derived live values to 3, then invokes the production departure at :11821. The assertions deliberately require live power 1 versus exit LKI power 3 at :11825/:11830.
- triggers.rs:11999 writes live 3/3 before leaving at :12006. Reentry at :12016 must be a later incarnation with live power 1 at :12023, while the original event's condition still reads the old 3-power LKI; the explicit incarnation-gate discriminator is documented at :12035.
- effects/mod.rs:13033 creates a P1-owned permanent, then :13041 sets only its derived controller to the fixture parameter. The positive bounce-followup test at :13076 requires the caster's draw and return to the owner's hand.
- /home/ubuntu/repos/phase-verifiable-loop/crates/engine/tests/integration/oversimplify_per_player_fractal.rs:170 creates a P0-owned creature, then :171 writes only controller P1. The exact final counter assertions at :217/:223 are 5 for each player, distinguishing the correct LKI controller from the reset owner; the active failure reports P0 7.
- layers.rs:1624 reseeds live power/toughness from base, and :1723 resets controller from base_controller/owner before reapplying layer effects. The newly introduced before-event flush can therefore erase these direct derived-field writes. This is a source-supported hypothesis, not proof that all four failures are fixture-only or that an alternative setup will preserve the intended regression discrimination.

The full plan correctly requires no-regression evidence and stopping on new conflicts (:565, :626, :634), but it has no disposition for these newly discovered failures. Oversimplify is outside its exact edit manifest (:243–256); the constructor-only exception cannot authorize this behavioral test change.

Required revision:
1. Add these four named regressions and their baseline/active evidence to the full plan. Trace the new capture/flush interaction and choose a bounded, authority-correct resolution before implementation resumes.
2. If fixture repair is justified, explicitly authorize the exact tests/helper regions, including oversimplify_per_player_fractal.rs. Use existing real P/T and control effect authority with appropriate object/incarnation lifetime, rather than direct derived writes that the new flush discards. Any earlier fixture setup of base characteristics must remain consistent with the test's intended source threshold.
3. Preserve the substance of the old assertions: original entrant base/live-after-exit power 1, exit LKI power 3, source comparison threshold 2, later incarnation live power 1, original-event LKI match, and the weak/negative twin; bounce owner different from controlled-at-departure player plus correct draw/hand ownership; Oversimplify exact 5/5 counters with the stolen object's owner still distinct from its at-exile controller. Changing the entrant's base to 3, aligning stolen owner/controller, weakening expected values, deleting the original condition, or ignoring the tests is not an acceptable repair.
4. Prove the corrected fixtures pass both original and changed production through appropriately isolated targets, then retain and execute their original LKI/incarnation/controller seam discriminators. Add a public cast/apply companion where needed to show the authority is reachable in normal play rather than only a synthetic helper state.
5. If authority-correct reaching fixtures still fail, treat that as an engine defect and return an explicit broader correction for review. Do not remove the required capture flush or alter layer/LKI behavior merely to accommodate invalid fixture writes.
6. Rerun the relevant existing suites and full library/integration gate after correction. These four cases must not be added to the list of accepted baseline exclusions.

## Full architectural review

The following dispositions cover the full plan, including inherited v7 obligations. PASS means the design is adequately specified, not that the unexecuted implementation or tests are accepted.

| Mandatory review dimension | Disposition and evidence |
|---|---|
| Class vs card | PASS. Hushbringer validates generic functioning StaticMode::SuppressTriggers against event-time subject facts. The plan covers ordinary, Haunt, Unattach, registered delayed, sequential, grouped, and chosen-cost paths; it has no card-name switch. Doomed Traveler, Wrath, Curtains' Call, and Stonecoil supply concrete controls. |
| Building-block reuse and helper justification | PASS. Existing active-static iteration, live and ZoneChangeRecord filter matching, trigger clause matching, quantity/cost selection, sacrifice execution, and GameScenario/GameRunner remain authorities. The evaluator removes duplication; the owner/member helpers provide exact synchronous provenance; the new pure component validator addresses information the flat queue did not contain. No replacement cost parser, generic mechanic, or parallel cost tree is introduced. |
| Analogous-feature trace | PASS with R2 unresolved. The plan traces existing live ETB suppression, co_departed production/stamping, zone-delivery/resume, ordinary registry/batch matching, delayed creation/dispatch, and chosen/deferred payment. Source inspection corroborates the producer and consumer seams. The wrapper's exact production reach is the missing trace described in R2. |
| Abstraction and i18n | PASS except R1's dispatch policy. Record/pending types remain in types; evaluator/ownership/payment validation remain in game; engine.rs delegates validation. No frontend/WASM decision logic, card-data AST, or frontend chrome is added. An existing engine error can carry the legacy-save recovery explanation without a new UI schema. |
| Idiomatic Rust | PASS. Optional typed snapshots distinguish unavailable from authoritative empty; a transparent DeferredSacrificeComponentId is separate from ObjectId and lexical scope identity; ownership uses an opaque non-Clone/non-Copy token; no parser-string inference, global latch, parallel grouping vector, or exhaustive-enum wildcard shortcut is proposed. |
| Parser/nom honesty | PASS. No parser edits or new accepted Oracle strings. Named cards use verbatim current Oracle with keyword helpers and zero-Unimplemented/functioning-static reach guards. Typed stress fixtures are labeled as engine fixtures. Complementary OneOf SHAPE remains a required guard, with ambiguous timing and direct delayed bypass support unchanged. Any discovered parser work returns for a new plan. |
| CR verification | PASS except R1. Referenced numbers and expanded ranges were checked in docs/MagicCompRules.txt, including 603.10/603.10a, 603.6c/d, 608.2c/f, 704.3, 601.2f/g/h, 118.3/10, 614.6/8, 701.19/21, 603.7 and 603.12. Cost components are distinct selected payments; 601.2h permits the applicable payment ordering, not an invented rule requiring printed order. Added comments must cite verified local text. Concession needs the newly identified 104.3a guard. |
| Applicable skill phases | PASS in specification, subject to R1–R3. Read engine-planner, card-test, casting-stack-conditions, add-trigger, add-static-ability, add-interactive-effect, and project-reference in addition to review-engine-plan. Type/event/consumer, delayed lifetime, cost, natural-choice/continuation, constructor/serde, parser reach, and verification phases are addressed. No new effect/keyword/replacement/enum variant warrants a new variant workflow. Stale skill paths/rule descriptions are correctly reported rather than treated as authority. |
| Claim-to-test and maintainer matrix | BLOCKED by R2 and the R1/R3 additions. The remaining extensive rows contain changed seam, public path, concrete payoff/provenance assertion, negative/positive siblings, and honest repaired/compatibility/ignored status. The explicitly outstanding tracked-set/empty-choice and parser SHAPE tests, plus all execution/mutation gates, remain required. |
| Identity/provenance | PASS in the proposed contracts, subject to R2 production proof. The full component contract and three separate event/lexical/pending lifetimes are explicit, including binding time, authority, transport, consumption, invalidation, hostile peers, and legacy handling. No consumption-time filter/source rescan substitutes for cost identity. |
| Scope and sibling matrix | BLOCKED only where identified in R1/R3. Otherwise target/self/multi/choice, players, controllers/owners, origin variants, duration/lifetime, empty/prevented/error/pause, serialization, merge, direct delayed, and other known exclusions are enumerated. No parser/mtgish/support expansion is authorized. |

## Detailed contract checks

### Deferred component authority, ordering, and validation

The selected contract at plan :138–180 and :549–559 is coherent. A component ID is its checked u64 append-start offset within one PendingCast. Count(2) yields [0,0]; a following Count(1) yields [2]; two separate Count(1) choices yield [0,1]. Empty selections append nothing. Component binding occurs once after existing selection validation and successful deferral, before any eventual sacrifice. Same filter/source/cost does not imply one component.

The pure validator accepts empty and well-formed all-Some contiguous runs with ID equal to run start; it rejects missing/mixed provenance, wrong starts, recurrence, and noncontiguous reuse without repairing the payload. The preserved append-only queue makes this canonical. Stored component order is payment order; chosen order remains within each component. The shared commit helper opens and closes one owner per component, with no capturing outer queue owner. The overall cost-event range is transport for trigger parking, not a simultaneity claim.

Both finalizers and the append path must check provenance before their identified side effects. The existing selected-object/controller/filter/prohibition validator remains separate. Reservation remains flat and includes old entries; mana simulation/state-event replacement occurs before owners open. Immediate selected costs keep their existing one-component owner. This does not promise a general cost payability or rollback redesign.

Constructor/consumer audit checked:
- Current sole production DeferredSacrificeSelection literal: casting_costs.rs:2005.
- Existing selection type and pending Vec: types/game_state.rs:2301/:2418; PendingCast construction retains the empty Vec.
- Selection/deferral handler, replacement-choice simulation, mana simulation, flat commit validator, commit helper, and both finalizers in casting_costs.rs.
- Existing CostResume::SpellCost producer and its component dispatch; inline WaitingFor pending-cast access and ManaPayment/PhyrexianPayment handoff.
- mana_abilities::deferred_spell_sacrifice_reserved remains an all-selection object reservation; no component interpretation there.
- Clone/move/serde, full PendingCast literals, equality, and loop normalization must retain component metadata. It does not reach stack/card export data.

No additional production grouping authority is required by the source read. The incomplete active implementation still uses one owner for the entire deferred queue, which is the known stopped defect, not the plan's chosen behavior.

### Recovery and serialization

Three distinct authorities must remain distinct:
1. ZoneChangeRecord.trigger_suppression is serialized event context. Some(empty) is authoritative and cannot use live fallback on repaired paths; None is unavailable legacy/synthetic context.
2. Lexical departure scope is serde-skipped, defaulted on deserialization, excluded from completed-boundary equality, cleared by normalize_for_loop, and empty at external completion/pause/error boundaries.
3. DeferredSacrificeSelection.component is serialized pending provenance. It survives normal clone/serde/equality/normalization and expires with the pending cast.

Old absent/empty queues resume. Old nonempty queues cannot reveal whether their equal-filter entries came from Count(2) or separate Count(1) choices. Loading/reserializing None honestly and requiring cancellation/reannouncement is an explicit, narrow compatibility limit, not an invented grouping guess. Newly produced valid queues must always resume; losing a field cannot be excused as legacy input. Existing CancelCast owns cancellation; already-paid unrelated costs are not given a new rollback guarantee. R1 is needed so this recovery policy does not restrict unrelated global actions.

The snapshot constructor inventory, event serde round-trip/default tests, GameState exhaustive field audit/new/equality/normalization, and non-replay history ledger distinction are adequate. The two added None fields are the only bytes changed in the historical loop_shortcut golden, verified by exact text subtraction against baseline.

### Synchronous ownership and producer coverage

Reviewed owner semantics: candidate identity includes current ObjectId/incarnation; binding is explicit and top-only; None is a barrier; emitted occurrences are claimed at emission with event offset and turn-zone-change index; finalization validates those exact keys. It does not discover membership by scanning all intervening events. Only actual departures get snapshots/peers. Before and after outcomes are evaluated at the owner's boundaries; borrowed member leaves introduce no provisional snapshot or new flush. Normal return, error return, empty result, and real pause use one lexical epilogue. No owner is serialized across a pause.

Producer inventory is complete for the stated bounded scope:
- normal and library-position standalone zone leaves;
- DestroyAll and multi-target/self Destroy;
- private choose-and-sacrifice-rest completion, both category/total-power callers;
- each SBA fixpoint iteration, including the separately called standalone-Augment check;
- completed batch delivery and each nonpaused/resumed ChangeZone segment;
- selected/fast sacrifice groups;
- each affected EffectZoneChoice movement/payment loop, finalized before continuation;
- immediate selected costs and the newly distinct deferred components.

The snapshot freezes suppression outcomes rather than retaining a whole GameState. Existing intrinsic merge flushes and independent nested child layer-world limitations remain explicit exclusions. A noncapturing independent child cannot manufacture a new layer world or claim an ancestor's occurrence. Structural clone has no shared mutable aliases; supported state/event swaps and external rollback checkpoints occur outside owner closures. Discovery of another mid-scope replacement is a stop condition. R2 must complete the specific public resolver-reentry proof.

### Matcher, delayed, and source availability coverage

Before-event death/LTB, normal Any-origin after-event, destination-self availability, matching-clause locality, per-event dedup, Haunt's selected linked subject, and Unattach death fallback versus native cause are specified separately. Existing ETB/ward behavior is preserved.

Ordinary and batched collection, cached/direct registry dispatch, registered WheneverEvent, one-shot primary/alternative matching, and Reflexive creation-batch checking are accounted for. Creation source/controller and cleanup/lifetime remain existing authority. Suppressed in-scope occurrences retain non-reflexive listeners; eligible one-shot consumes; recurring persists to its existing cleanup; unmatched Reflexive is discarded. Distinct controllers/sources, eligible alternatives on the same occurrence, later permitted events, and ThisTurn/Persistent/Reflexive fixtures prevent broad rejection or lifetime drift.

Ambiguous OneOf/NotEquals matches deliberately retain separate ordinary live-cache and registered-delayed ungated compatibility, never claiming recovered Oracle provenance or using the event snapshot as false certification. Direct legacy delayed conditions remain explicitly unrepaired, with individual desired diagnostics and positive/lifetime siblings.

## Verification, exclusions, and evidence integrity

The plan preserves the original hostile fixture requirements:
- A: real reached aggregate unless-payment with predecessor gain, exact life 21 at prompt, paid 21 / declined 16. The following-instruction desired 21 diagnostic remains separate; aggregate desired simultaneous suppression remains excluded rather than silently fixed.
- B: seeded base/live Regenerate shield proves first-destruction replacement using Regenerated, tapped/survival, and no false departure; cant-regenerate twin and subject/order/no-Hush variants remain. Cast-created shield persistence is a separate desired diagnostic.
- C: real three-target ChangeZone replacement pause and serialized resume, tail authoritative snapshots and exact occurrence/peer counts, both orders, Hush payoff 0. Resumed no-Hush 2 remains narrowly labeled compatibility, desired 1 remains separately ignored, and ordinary unpaused/following independent deaths remain exact 1.

Keep all separately named exclusions: aggregate/inherited-target completed grouping; full cross-pause grouping; direct delayed suppression; ambiguous origins; intrinsic merge/independent nested layer-world limits; co-dying off-zone Any source availability; aggregate paid continuation; cast-created regeneration persistence; resumed duplicate dispatch. Component flattening and the four new regressions are not exclusions.

Uncompleted mandatory gates are not waived:
- all inherited producer/consumer/runtime rows plus all component and R1/R3 rows;
- the R2 concrete production proof, earlier tracked-set/empty-choice continuation sibling, and complementary-OneOf SHAPE guard;
- every exact isolated source-associated mutation, currently zero executed, including Augment-only handoff, added member flush, wrapper-only barrier, standalone normal/library boundary, matcher/Haunt/Unattach, ordinary/batched/delayed compatibility and lifetime alternatives, whole-queue/singleton/filter-grouping/component-serde/preflight;
- explicit independent desired-diagnostic execution with first reached assertion and baseline/changed evidence, not one aggregate failure hiding the others;
- fresh formatting, full library and integration evidence, scoped and required broader checks with existing failures correctly separated, constructor/serde/source audit, and independent implementation review;
- original frozen case/corpus/checker and original failing worker preserved, freshly rebuilt changed worker run twice with identical semantic evidence and both worker hashes. Unit/integration tests do not replace this maintainer simulation or the blog's attribution/evidence chain.

No assertion, corpus, checker, Oracle text, or support label may be changed to manufacture a pass.

## Review inputs and reproducibility

All inspection and artifact creation ran through ssh nishadsingh-box-4. The reviewed checkout is /home/ubuntu/repos/phase-verifiable-loop. Its HEAD is the original baseline 2dec6c88915db4697706234a7ba2fcedd97b1689 plus the frozen partial working diff.

Reviewed in full:
- /home/ubuntu/coworld-migration-20260904/hushbringer-plan-v8.md and adjacent freeze receipt.
- Root CLAUDE.md and applicable AGENTS.md; review-engine-plan and the applicable skills named above. Ancestor/subdirectory instruction search found no additional applicable engine instruction file.
- Current functional tracked diff against baseline, new trigger_suppression.rs, all 4,231 lines of trigger_suppression_event_timing.rs, and exact mechanical golden/constructor changes; referenced production paths and applicable local CR text.
- hushbringer-implementation-stop-v7-components.md and -proof.json.
- hushbringer-implementation-tests-v7.md and hushbringer-implementation-production-v6.md, including final-partial receipts.
- Root broad-suite and original-baseline receipts and reported test outcomes for the four new failures.
- Current Scryfall Oracle/rulings for Hushbringer, Doomed Traveler, Wrath of God, Curtains' Call, and Stonecoil Serpent, obtained read-only on the remote host. The local CR file remains the rule-number authority.

Integrity values:
- Full v8 plan SHA256: a9a0b06254700faab85996d1ddfbbbbceabc2a57a35034f89a0531f7ffe179be; unchanged at report preparation.
- Tracked binary diff against baseline SHA256: d9eb4769cb42734b98e4a9ff02e5d8708eccb3564ba1537193c23b5f5bded472.
- New trigger_suppression.rs SHA256: f37e54b657772b0551e46d3d612e4d44682ebfd6cffca8b1936b80d266d929cc.
- New integration module SHA256: 9c910733be643af92021c946351b70d9e4dd6c8d8df1f92016f3980ebbaf4486.
- Final joint source archive (2,051 files) /home/ubuntu/coworld-migration-20260904/hushbringer-v7-final-joint-source.tar.gz SHA256: e252079cbab8be1d0f1ffdf0c06856e59c4bef1afbf613ce1d7de84128dc1622.
- Root broad-run source manifest SHA256: 0301cf3cce5276bedb0ef6c68451c6ec81adf3cf3877cc1bad099a4c5aba9263. Both broad receipts report no changed source files during their runs.
- hushbringer-root-full-engine-v7-receipt.json SHA256: 66cf3b1921cdc5392caec88c05c48aefad632f250b920a05ce8c20b059d9b1c0.
- hushbringer-root-integration-v7-receipt.json SHA256: cc558a89f34735d327e548e92d4d8ad15a2c1ad89d864089e13ce8d93690aed6.
- hushbringer-root-baseline-library-v7-receipt.json SHA256: 7c4fbd545b6ec439a3046a4e5e8f40ee2a2234374270eff6681d4554292e6ec0.
- hushbringer-root-baseline-oversimplify-v7-receipt.json SHA256: 3bc057fc3cbbcc5f33ef3da7f614a0afba1bf3d16dabf90ff48bfabeaed12fd4.

Baseline receipts attest HEAD 2dec6c88915db4697706234a7ba2fcedd97b1689 and empty production diff, with their own /home/ubuntu/repos/phase-hushbringer-baseline-tests/target. Broad active runs used the separate active target. Historical shared-target evidence is not promoted to current source-version proof. The earlier 67-pass/4-fail/20-ignored matrix and 2-pass/18-fail desired diagnostics remain partial evidence, not an accepted repair.

The next step is a revised full plan resolving R1–R3, then another fresh full review. No dependent implementation or fixture change is authorized by a CLEAN result from this report, because this report is not CLEAN.
