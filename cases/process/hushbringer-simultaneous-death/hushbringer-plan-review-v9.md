# Fresh full review: Hushbringer plan v9

## Verdict

**CLEAN: zero blocking or material plan gaps.** This is a fresh review of the entire frozen 752-line v9 plan, its full proposed repair and retained validation obligations. It is not a delta review of R1–R3 and is not acceptance of the current partial implementation.

The three v8 findings are resolved at the plan level. The selected deferred-component authority addresses the proven sequential-cost regression. The event-local suppression architecture, exact producer ownership, consumers, migration policy, adversarial fixtures, exclusions and completion gates are sufficiently concrete to implement and independently verify. No new design decision is required before that implementation.

Current active failures and unexecuted tests/mutations remain open acceptance obligations. In particular, this verdict does not turn the active 67-pass matrix, reversed-order diagnostic passes, or four original-production baseline passes into evidence that the proposed v9 repairs have run.

## Review scope and frozen authority

- All repository inspection, source comparison, rules verification and review-artifact work ran through `ssh nishadsingh-box-4`.
- Reviewed plan: `/home/ubuntu/coworld-migration-20260904/hushbringer-plan-v9.md`, SHA256 `1e2c3adde42263f56fc9a25c7745854f4a5426ae4d2c25eda36f4f6fb0c3613f`.
- Plan freeze receipt: `hushbringer-plan-v9-freeze-receipt.json`, SHA256 `36aa05a0c5fb7961aef0eec3126994a97b6015218e2923efd07bc53f0c2de518`.
- Active source: `/home/ubuntu/repos/phase-verifiable-loop`; comparison base `2dec6c88915db4697706234a7ba2fcedd97b1689`.
- Complete joint archive SHA256 `e252079cbab8be1d0f1ffdf0c06856e59c4bef1afbf613ce1d7de84128dc1622`.
- Source manifest SHA256 `0301cf3cce5276bedb0ef6c68451c6ec81adf3cf3877cc1bad099a4c5aba9263`: independently checked all 2,051 files; none changed or missing.
- Current tracked binary diff against the comparison base SHA256 `d9eb4769cb42734b98e4a9ff02e5d8708eccb3564ba1537193c23b5f5bded472`.
- All hashes bound by the plan freeze receipt were independently checked and matched.
- All 125 v8 table rows remain in v9's 151 table rows. Preservation was checked mechanically and their surrounding contracts were read.
- Original-production baseline `/home/ubuntu/repos/phase-hushbringer-baseline-tests` has no production source diff. Baseline, candidate and mutations retain separate targets.
- No engine, test, plan, rule, skill or card-data source was edited. No build, test, Cargo process, commit, push or child agent was started. Only this report and its review evidence/receipt were written.

Read `CLAUDE.md`, applicable `AGENTS.md`, and the complete `.claude/skills/review-engine-plan/SKILL.md`. Inspected the complete active changed-file inventory and production diff against the base as review context, the new suppression implementation, relevant producer/consumer/cost/authorization/layer/replacement source paths and old regression fixtures. Read both final implementation handoffs, the final-partial receipts, v8 review as findings context, root broad-suite receipts and original-production confirmation receipts. This is a plan review; it does not claim a fresh runtime run or a line-by-line implementation acceptance review of the entire new integration test module.

## Mandatory full architectural assessment

| Review requirement | Assessment and evidence |
|---|---|
| Class of mechanic, not card patch | PASS. Generic event-time trigger suppression is repaired at typed event producers and trigger consumers. Hushbringer is the motivating real case. Torpor/dies restrictions, ordinary/delayed clauses, simultaneous/sequential actions, controller/condition changes and replacement siblings are explicitly covered. No runtime card-name branch is proposed. |
| Building blocks and helper justification | PASS. Reuses existing layer/functioning-ability evaluation, zone records, trigger matchers, replacement dispatch, delayed listener lifecycle, transient continuous effects and payment validation. The new snapshot and lexical ownership carrier solve distinct missing authorities. Typed deferred component IDs represent selected cost boundaries that cannot be recovered from existing flat entries. |
| Analogous full trace | PASS. Plan traces announcement/payment, effect resolution, replacement diversion, synchronous owner/member capture, event dispatch, ordinary/delayed eligibility and stack payoff. The deferred path covers both finalizers and interruptions before commit. The R2 replacement trace was checked against actual production source. |
| Logic placement and boundaries | PASS. Event timing lives in the runtime, typed persisted outcomes on the emitted event, and ephemeral scope in GameState. Card grammar, card database, UI, AI, decisions and mtgish do not compute the rule. Pending-cost compatibility is handled at authorized action ingress and finalizers. |
| Rust representation and discoverability | PASS. Optional serde-default event data distinguishes unavailable from authoritative empty; scope is owned, defaultable, skipped by serde and excluded from settled-state equality. Component identity is a transparent typed integer, carried per selection. Constructor/consumer/field-audit inventories are explicit. No new enum variant is planned; any discovered variant or parser work returns to the applicable workflow. |
| Parser/nom honesty | PASS. No parser expansion. Existing real-card ASTs and complementary-OneOf shape guards remain required. OriginConstraint's inability to retain positive-origin versus negated-exclusion provenance is explicitly acknowledged and not inferred from set membership. |
| Comprehensive Rules verification | PASS. Relevant rules were verified in the remote MagicCompRules.txt, including timing, lookback, delayed lifetime, cost payment, replacement, layers, incarnation, sacrifice and rollback. Details below. |
| Applicable skill checklists | PASS. Engine-planner, casting-stack-conditions, add-trigger, add-static-ability, card-test, project-reference, relevant existing-handler interactive phases and replacement fixture lifecycle are disposed explicitly. Stale skill references are reported rather than used as law. |
| Concrete end-to-end proof and mutations | PASS. Matrices name production entry, exact boundary, reaching action/event guard, expected payoff/provenance, negative siblings and isolated mutation. Helper-only assertions are supplemental. Unrun fixtures and mutations remain gates; unavailable data, fixture failure and semantic failure cannot be conflated. |
| Identity, binding, invalidation and competing authority | PASS. Event occurrence, object incarnation, owner/member tokens, selected cost components, source/controller and Haunt links are separately bound. Same-filter and same-ID hostile cases distinguish those authorities. Cleanup, serialization, retry, cancellation, rollback and delayed consumption are explicit. |
| Complete scope and sibling coverage | PASS. Producer, consumer and maintainer inventories include normal/library, destruction, SBA/Augment, keep/sacrifice, choices, resumed segments, ordinary/batched and registered delayed paths. Known aggregate, cross-pause, ambiguous-origin and bypass limitations remain separately labeled. No unrelated scope expansion is required. |

## Core architecture and ownership review

The original Hushbringer plus Doomed Traveler simultaneous Wrath case remains fixed evidence: original produces one Spirit and desired produces zero in both target orders. No-Hush and Hush-removed-before controls must each produce one; Stonecoil's replacement-based three counters remain unaffected. Those outcomes follow from event-time suppression, not current graveyard state.

A saved event outcome contains the evaluated suppression result for its before/after boundary. It does not serialize a GameState, live filter, closure or functioning-source cache. `Some(empty)` is authoritative and may not fall back to current state; `None` is old/unavailable authority. The turn history ledger intentionally stays `None`, because it is not the replay/dispatch authority. Event clones and parked event vectors carry the snapshot through collection and serialization.

The synchronous frame/token/member design binds a producer's actual logical action and each member's ObjectId/incarnation. It bounds claims by event offsets and turn-zone-change identity. A borrowed leaf does not flush or finish its ancestor. Independent resolver entry masks member authority, noncapturing nested work cannot claim ancestor events, and only the lexical owner finishes exactly once on normal/error/pause return. The default/serde/clone/equality/normalization/checkpoint contracts are explicit and do not introduce cross-pause ownership.

The normal leaf and library variant, destroy and destroy-all, common keep helper and all its routes, each SBA iteration including the standalone Augment handoff, batch/resume segments, ChangeZone branches, sacrifice variants and EffectZoneChoice routes are named. A remaining legacy stamping helper is not a substitute for the new producer boundary. Specific isolated owner/member, wrapper and intermediate-flush mutations remain mandatory.

Ordinary and batched collection choose before or after from the matching unambiguous clause. From-anywhere/self-destination exceptions, Haunt's established exile link and Unattach's death-capable adapter are separately accounted for. A suppressed clause cannot reject an eligible alternative in the same definition. Controller/condition/functioning-ability evaluation is frozen at the selected boundary.

Registered delayed triggers use the occurrence's snapshot, not creation-time suppression or one broad reject at listener level. Suppressed non-reflexive occurrences do not consume a one-shot; eligible ones do. Recurring retention, cleanup, reflexive disposal, same-occurrence alternatives and controller/source creation binding retain separate fixtures. Direct delayed bypass routes stay exclusions.

For ambiguous OneOf/NotEquals origins, ordinary collection retains its live-static compatibility context and registered delayed matching retains its existing ungated behavior. This is not promoted as a rules-correct new timing mechanism. Complementary-OneOf parser shape, subject-first/later-Hush departure, ordinary/delayed surviving-Hush siblings and mixed repaired/excluded clauses make the boundary concrete.

## Deferred component repair

The current partial implementation flattens separate deferred Composite sacrifice components into one owner. The original-production Hush-first sequential case produces one Spirit; current active produces zero; desired remains one. A reversed-order diagnostic pass is sequential compatibility and does not prove this repair.

The plan selects one successful, nonempty cost-selection append as the component authority. `DeferredSacrificeComponentId` is carried on every selected entry. Count(2) yields IDs [0,0]; a subsequent single selection yields [0,0,2]; two independent single selections yield [0,1]. Equal filters, source, controller and cost syntax are never used to infer identity.

The pure validator accepts contiguous all-Some runs whose ID equals their starting position, and rejects missing/mixed IDs, recurring/noncontiguous components and wrong positions. Validation occurs before mutation at append and before the specified early finalizer operations. The final commit opens and closes a separate owner for each component while preserving existing flat reservations, eligibility and payment order.

Both finalizers, Count(2) versus two identical Count(1) components, mixed cardinalities, component-local target orders, selection retry, invalid membership, insufficient resources, mana tap/sacrifice interactions, save/load, clone and cancellation are required. Event parking order is distinct from physical commit timing. There is no new general scheduler or generalized transaction system.

Old nonempty pending selections deserialize and reserialize honestly with unavailable provenance; they are not silently regrouped or assigned guessed IDs. They must refuse further payment-affecting advancement, while retaining existing reservations and providing lawful cancellation/reannouncement. Empty/absent legacy lists and valid new payloads retain their normal behavior. This design is complete at the plan level and still requires its specified execution/mutation evidence.

## V8 R1 closure: legacy recovery and lawful actions

**Resolved in v9 sections R1, component matrices and completion gates.**

The new guard is placed after existing actor authorization and delegates to the same pure component validator. It may refuse a payment/resume action with invalid component layout, but cannot become an unconditional pre-dispatch denial.

The bypass set is explicitly CancelCast, OutOfBandPreference, Concede, Debug, GrantDebugPermission and RevokeDebugPermission. These bypass only the new component-layout check. Their existing actor, payload, feature, permission and sandbox-host restrictions remain operative. SetAutoPass is not mislabeled as an independent preference; it retains its priority-automation behavior.

The plan includes lawful prompt-owner and other-player concession, requires the conceding player to match the actor, and retains spoofed-concession WrongPlayer behavior. It includes permission-enabled/disabled debug controls, host/nonhost permission changes, preference validation, cancel/reannounce and valid/legacy comparison cases. Invalid component metadata is introduced only after a natural pending checkpoint is reached.

These obligations agree with the inspected action authorization and dispatch order and CR 104.3a. The preflight-only mutation must fail the lawful-action recovery assertion while leaving the existing authorization negatives intact. This closes the previous universal-guard gap without weakening action security or cost refusal.

## V8 R2 closure: exact resolver-wrapper-only discriminator

**Resolved in v9 R2 with a production-reaching concrete trace and isolated mutation.**

The source-supported fixture starts with healthy, ordinary P0 permanents X and Y, with no merge, counter, attachment or unrelated trigger path. X has a one-use mandatory Moved SelfRef-to-Graveyard replacement, seeded coherently in base/live ability authority. Its existing Execute payload redirects the attempted move to Battlefield and leaves a terminal SelfRef Sacrifice(1) component. There is no added nested component between the wrapper and sacrifice.

Normal cast/target/priority actions resolve a typed two-target ChangeZone-to-Graveyard effect in both target orders. The outer member binding names X's exact current incarnation before replacement. Replacement evaluation consumes the one-use rule and queues the terminal non-modifier component.

The redirected Battlefield-to-Battlefield no-op emits no X departure and does not change X's incarnation. Its temporary nondeparture mask unwinds, restoring that exact outer member binding. The zone-pipeline delivery tail reaches the real replacement-component resolver. Inspection found no mandatory layer flush between that no-op and the terminal component in this constrained path; marking layers dirty does not itself flush them.

The real resolver wrapper masks member authority. Explicit-object Sacrifice has no intervening producer scope; the consumed replacement is skipped. X's resulting independent departure is therefore unclaimed by the capturing ancestor and intentionally has snapshot None in this bounded layer-world characterization. Y is the parent-owned singleton, with an authoritative empty snapshot and empty co-departed peers.

Removing only the production wrapper's `without_departure_member` call restores X's still-valid parent binding. X then claims the parent group with Y. The required X-None and Y-empty-peer assertions discriminate this mutation. No helper replacement, changed branch, removed leaf barrier, explicit layer flush or synthetic event can stand in for this test.

The no-replacement sibling requires both actual parent departures and mutual peers; redirect-only requires X to remain on Battlefield at the same incarnation and Y to remain a singleton. A later public Traveler death with exact one Spirit proves cleanup. Both target orders and reaching guards prevent vacuous success.

This is sufficient to close the prior missing discriminator. The actual fixture and mutation remain unexecuted. If the specified runtime trace differs, implementation must stop and return the concrete blocker; the plan does not authorize relaxing the assertion or claiming general nested layer-world correctness.

## V8 R3 closure: four old LKI/controller regressions

**Resolved as an explicit, bounded test-fixture disposition with mandatory independent proofs.**

The four failures are retained as introduced active regressions. The original tests pass on original production; v9 does not label them unrelated or waive their assertions. The proposed correction replaces unsupported derived-field writes with existing transient effect authority that survives the new legitimate pre-event layer flush.

| Original regression | Preserved semantics and exact discrimination |
|---|---|
| Exited entrant's original ETB condition | Coherent observer 2/2, entrant printed/base 1/1 plus registered SpecificObject +2/+2 UntilEndTurn effect. Flush produces 3/3. Exit leaves live 1 but LKI 3; comparison to source 2 remains true, weak unpumped 1 remains false. A live-characteristic fallback mutation makes only the positive condition fail. |
| Leave and same-ID reentry | Retains the real initial entry event and its incarnation, LKI 3 on exit, effect pruning and later live 1 in a distinct incarnation. The original event remains true. Removing only the entered-incarnation comparison reads the wrong live object and fails that unchanged condition. |
| Bounce then conditional draw | P1 ownership with actual transient P0 control, owner-based base authority unchanged. After bounce live controller resets to P1 but event/LKI stays P0; P0 draws exactly one, no-theft sibling zero. The explicit use_lki-controller bypass must read actual live controller and fail draw-one. |
| Oversimplify per-player Fractals | Full existing real card and parser checks remain. P0's 2/2 is transiently controlled by P1. All four creatures actually exile; live controller resets to owner P0 while exit LKI stays P1/power 2. Exact existing 5/5 counters remain. Off-zone effective-controller fallback mutation produces 7/3 and fails. |

The Oversimplify test file is explicitly added to v9's bounded scope only for runtime fixture setup/helpers/imports/guards. No production filter, controller, layer or quantity semantics are changed by this disposition. DB-unavailable early return does not count as execution evidence. The Oversimplify fixture discriminates controller fallback, not independent aggregate-power fallback; the latter's existing coverage remains required.

The new public companions use ordinary scenario/runner casts, choices and priority: a real static +2/+2 grant at ETB followed by legal removal/reentry responses and exact one-life payoff; an actual GainControl spell followed by bounce/draw; and actual theft followed by full real {3}{G}{U} Oversimplify with exact 5/5 versus no-theft 7/3. No synthetic event, injected continuation or direct stack manipulation substitutes for those paths.

The identical bounded fixture overlay must pass on original production in its isolated target and on candidate, including existing matching LKI siblings and the new public companions. Only snapshot fields absent on original may be omitted; payoff/control/LKI/incarnation assertions may not change. The four old-seam mutations run separately after unmutated passes. If lawful layer/control authority cannot preserve the behavior, the result is an unresolved engine regression requiring renewed review.

## Rules and Oracle verification

Read the remote rule text for CR 101.4; 104.3a; 113.6 and 113.6k; 118.3, 118.3a, 118.10 and 118.12a; 400.7; 601.2f–h; 603.2, 603.2c and 603.2g; 603.4; 603.6a–d; 603.7a–b and 603.7d–e; 603.10 and 603.10a/c; 603.12; 605.4a; 608.2b/c/f/h; 611.2a/c and 611.3a/b; 613.1b, 613.4c and 613.11; 614.1a, 614.5–6 and 614.8; 616.1; 700.4; 701.8a–c, 701.19a/c and 701.21a; 702.12b and 702.55a–c; 704.3; and 733.1.

The selected rules support simultaneous true action boundaries, sequential selected costs, before-event lookback for death/LTB clauses, after-event general matching with enumerated exceptions, no event from a replaced-away occurrence, delayed lifetime separation, layer-based characteristic/control authority and new incarnations. Concession remains lawful at any time subject to correct player identity. Rule 603.12 keeps reflexive creation-batch behavior distinct from recurring delayed listeners.

Independently fetched current Scryfall Oracle records for Hushbringer, Doomed Traveler, Wrath of God, Curtains' Call, Stonecoil Serpent, Oversimplify and Hulkling, Burgeoning Bruiser, plus Hushbringer's official-source rulings through the Scryfall rulings API. All seven Oracle-response hashes match the plan evidence. The rulings corroborate simultaneous co-death suppression, unaffected replacement/counter effects, sacrifice-versus-death trigger distinctions, last-effective creature characteristics and the from-anywhere exception.

Review evidence: `hushbringer-plan-review-v9-oracle-evidence.json`, SHA256 `d68e767c1463155e5b70b173afb54880acc6c90cf939db54d6021227ed481141`. Fetched remotely at 2026-09-05T17:04:14.503723+00:00. Oracle/API responses are supporting evidence, not instructions or parser support claims.

## Retained verification and exclusion audit

The full production-path, maintainer, runtime and isolated-revert matrices remain binding. In particular, none of these obligations was lost while fixing R1–R3:

- Standalone Augment owner/member handoff with co-departed no-Hush observer, exact +1 payoff and shared authoritative records; isolated handoff-only mutation.
- An added intermediate leaf-layer flush mutation, with a reaching adversarial static/layer fixture.
- An earlier tracked-set producer followed by EffectZoneChoice, its empty-choice sibling and preserved tracking/publication/continuation behavior.
- Complementary-OneOf parser-shape proof, ordinary live-versus-saved-after compatibility and separate delayed bypass characterization.
- Normal and library before/after timing, authoritative empty versus old missing snapshot, serde carry-through, settled clone/equality/normalization and post-resume fresh ownership.
- Every deferred component constructor, both finalizers, legacy refusal/recovery, unchanged independent actions, payment-order/reservation controls, atomic invalid input, rollback and retry.
- Dedicated keep, destroy, replacement-wrapper, clause timing, Haunt and delayed matching/lifetime/alternative mutations.
- The four old LKI/control seam mutations, original-production corrected overlays and public companions.
- Full appropriate Phase formatting, check/library/integration and required project suites, independent implementation review, followed by root-owned frozen worker/checker acceptance twice.

Existing receipts remain accurately partial: active new matrix 67 pass / 4 cost failures / 20 ignored; explicit desired diagnostics 2 pass / 18 fail; all exact seam mutations zero executed. Root broad library is 16,574 pass / 3 fail / 7 ignored; integration is 3,042 pass / 5 fail / 22 ignored. The four additional old regressions pass original production, and the fresh original cost confirmation is 1 pass / 4 fail, including original Hush-first sequential payoff one.

These results establish what is currently broken and which cases reach their paths. They do not complete the new plan's execution gates. Full suites must be rerun on the final source; neither compilation-only checks nor stale green results from another checkout suffice.

Separately retained exclusions are: completed aggregate/inherited sacrifice grouping; full cross-pause simultaneity; legacy direct delayed bypasses; ambiguous/restricted-origin timing; intrinsic merge and independent nested layer worlds; co-dying off-zone Any source availability; aggregate post-payment continuation; cast-created regeneration persistence; and the precise resumed duplicate-dispatch compatibility count. Segment snapshots, seeded replacement fixtures, reversed-order passes and successful parsing do not repair or promote these categories.

The root's original case, corpus, checker and production baseline pin remain fixed. A rebuilt candidate must provide the required same semantic evidence twice, preserve the no-Hush/removed-before and Stonecoil controls, cover the full ten-case worker corpus, and bind source/worker hashes and maintainer attribution. The reviewer did not alter or execute any of these acceptance inputs.

## Residual execution uncertainty

No unresolved plan-level question remains. The R2 exact runtime trace, R3 corrected original/candidate overlays and public companions, selected-component implementation, every retained reaching fixture and every isolated mutation still require execution. They are concrete falsifiable gates, not assumptions being accepted as true.

Implementation acceptance must stop if a gate exposes a different production path, missing source authority, unsupported fixture, changed original expectation or broader regression. Record that evidence and obtain a new full plan review if the design changes. This clean report authorizes progress through the existing plan; it does not waive any gate or exclusion.
