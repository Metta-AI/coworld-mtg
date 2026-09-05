# Hushbringer plan v6 — fresh full review

Result: no blocking gaps found within the explicitly bounded scope. V6 resolves the v5 standalone-Augment ownership finding.

Reviewed the entire /home/ubuntu/coworld-migration-20260904/hushbringer-plan-v6.md against clean baseline 2dec6c88915db4697706234a7ba2fcedd97b1689 in /home/ubuntu/repos/phase-verifiable-loop and the original simultaneous Hushbringer / Doomed Traveler / Wrath failure. Source inspection and current Oracle/ruling requests ran through ssh nishadsingh-box-4. No engine edits, builds, tests, commits, or subagents were used. An initial report-write command failed from shell quoting before writing the report; the corrected command writes only this remote artifact.

## V6 correction

The narrow augment.rs manifest entry and borrowed iteration-token parameter close the concrete v5 call-graph gap:

- sba.rs:252 calls check_standalone_augment_permanents inside the same iteration as ordinary zero-toughness/lethal and other departure checks.
- augment.rs:168–205 has one production caller, retains the existing battlefield/phase/Augment/unmerged selection and live guard, and delivers each selected object through sba.rs:676 move_to_graveyard_via_pipeline.
- The proposed with_departure_member wrapper passes the iteration's authority transparently through that unchanged replacement-aware delivery. It closes before the existing pause return and preserves any_performed behavior.
- Exact claimed-event stamping therefore keeps the Augment departure in the same group as the earlier ordinary SBA death. It does not open an independent nested scope or require ownership inference from global state.

The production discriminator is implementable with existing facilities. effects/animate.rs supports a keyword-only Animate with unchanged P/T and types. The normal cast chain can grant Augment to a healthy unmerged creature and mark a separate observer lethally damaged before the ordinary SBA pass. The earlier lethal check removes the observer; the later Augment check removes its specific observed subject. triggers.rs:2119 onward requires the subject's co_departed set to discover that off-battlefield observer. Thus the exact no-Hush +1 life payoff, paired with authoritative snapshots and exact peer sets, fails when only the Augment ownership handoff is omitted. The surviving-Hush zero-payoff twin, order reversal, no-grant and live-observer controls make this a reaching runtime test.

## Full architectural gate

1. **Class rather than card:** event-local evaluated outcomes extend the existing SuppressTriggers family. Hushbringer is a validating consumer; no card-name branch or new card encoding is proposed.
2. **Building-block reuse:** functioning_abilities::battlefield_active_statics, existing live/record filters, ZoneChangeRecord, SuppressedTriggerEvent, incarnation/index identities, canonical matchers and producer boundaries provide the required primitives. The new module and transient scope carry information that cannot be recovered after departure; they do not duplicate sacrifice, replacement, layer or delayed-lifetime logic.
3. **Trace verification:** the plan supplies end-to-end suppression, ordinary death, co-departed observer, Haunt, choices/continuations, destruction, delayed-listener, origin-normalization and owner/leaf traces. Inspected source agrees with the relevant dispatch and consumption seams.
4. **Abstraction placement:** rules and capture remain in game modules; event/state structures remain in types. No frontend decision, adapter logic, grammar or translated UI text is introduced.
5. **Rust/API:** owned scope data, opaque borrowed tokens, explicit member/barrier bindings, closure epilogues and existing result types give a concrete synchronous ownership contract. Empty/single/error/pause completion, incarnation reuse, exact emitted keys and independent reentry are specified without unsafe/global state or an implicit layer lock.
6. **Nom/variants:** no parser edit or enum variant is proposed. Existing OriginConstraint normalization is preserved; parse_origin_constraint_tail confirms its OneOf complement ambiguity. Unexpected grammar/variant work returns to the corresponding gate.
7. **Rules and premise:** current Scryfall Oracle responses for Hushbringer, Doomed Traveler, Wrath of God and Curtains' Call agree with the plan. Current Wizards-sourced Hushbringer rulings confirm simultaneous suppression and the self/from-anywhere distinction. The cited timing, static-function, zone, destruction/sacrifice, replacement, SBA and delayed/reflexive rules were checked in docs/MagicCompRules.txt. The plan correctly rejects the existing misuse of 603.2g and 704.7.
8. **Skill checklists:** review-engine-plan, add-trigger, add-static-ability, card-test, the existing interactive-handler lifecycle and project-reference verification requirements have concrete dispositions. No missing parser, UI, AI or new-mechanic registration is required. Stale skill reference tables are not used as rules evidence.
9. **Verification matrix:** production cast/apply entry points, positive reach guards, payoff/zone/lifetime assertions, siblings and revert discriminators cover the changed seams. The Augment row supplies the formerly missing production preservation test. Frozen case/corpus/checker, original failing worker and twice-repeated rebuilt-worker evidence remain required.
10. **Identity/provenance:** outcomes bind at the producer boundary; owner/member state is transient, and completed events alone carry serialized authority. Before/after, Some(empty)/None, consumer-local ambiguous-origin compatibility, Haunt subject links and delayed creation-bound source/controller/lifetime remain distinct.
11. **Scope/construction/serialization:** the existing stamp inventory, ZoneChangeRecord constructor obligations, GameState initialization/audit/normalization/equality and pending-event carry-through are addressed. Completion precedes continuation/deferred collection at touched choice, batch, drain and cost boundaries. The non-dispatched history ledger is explicitly non-authoritative.

The collector currently has the reported whole-event death gate. Replacing it requires the planned ordinary/batched adapters, dedicated Haunt and Unattach fallback checks, and registered delayed-consumer tests; v6 retains all of them. WheneverEvent/WhenNextEvent dispatch uses canonical matchers while preserving its occurrence/lifetime policies. Direct delayed routes demonstrably bypass those matchers and remain separately characterized.

## Residual assumptions and acceptance

This approves the implementation plan; it is not evidence of a working implementation. Exact lexical closure, event-vector ownership, settled checkpoint behavior, no additional mid-group layer flushes and all active matrix assertions still require implementation verification. A discovered mid-scope state replacement/event-vector swap remains a reportable implementation conflict, not permission to ignore missing ownership.

Accepted exclusions are unchanged: aggregate unless-payment and inherited-target completed sacrifice loops; full cross-pause grouping; direct delayed bypasses; ambiguous OneOf/NotEquals timing; and existing intrinsic merge/reentrant-child layer-world limitations. Active compatibility and working-sibling controls distinguish ignored desired behavior from repaired coverage. These existing limits do not justify an unrelated redesign.

Proceed with v6's bounded implementation and full acceptance gates. No revision is required by this review.

