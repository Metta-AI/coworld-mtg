# Hushbringer full engine-plan review v4

Verdict: **Clean — no blocking gaps found.**

Reviewed the complete `/home/ubuntu/coworld-migration-20260904/hushbringer-plan-v4.md` against checkout `/home/ubuntu/repos/phase-verifiable-loop` at `2dec6c88915db4697706234a7ba2fcedd97b1689`. All inspection, current Oracle/rulings requests, and this report write ran through `ssh nishadsingh-box-4`. No implementation, builds, tests, commits, or subagents were performed.

## Findings

No required plan revision. The v3 origin-provenance finding is corrected without adding an AST/parser feature or changing the expressly excluded consumers' behavior:

- `OriginConstraint::matches_from` (`types/ability.rs:17954`) remains the predicate authority. `OneOf` represents both positive sets and complements; `parse_origin_constraint_tail` (`parser/oracle_trigger.rs:14802`) builds a complementary `OneOf` for multiple exclusions and `NotEquals` for one exclusion. The plan does not infer before-event timing from membership of Battlefield, including singleton sets and scalar `origin_zones`.
- The ordinary collector currently gathers a live suppression cache and gates the event (`triggers.rs:1480–1501`); its batched path independently applies that gate (`triggers.rs:280–298`). Registered delayed matching calls canonical matchers directly (`triggers.rs:6321–6348`) and has no equivalent gate. The call-local `Option<&[ActiveSuppressTriggerStatic]>` distinguishes these existing consumers without changing the matcher function-pointer ABI or persisting compatibility policy.
- The proposed compatibility decision is per matching excluded clause. It cannot veto an eligible repaired sibling, replace the authoritative empty-snapshot contract, or leak the ordinary gate into registered delayed matching.
- The planned subject-first/later-Hush-departure ordinary test distinguishes the actual baseline live scan from both stored before and stored immediately-after outcomes. Surviving-Hush ordinary/delayed counterparts distinguish the consumer contexts. Both `OneOf` and `NotEquals` have positive reach guards, sibling predicates, scalar/disjunctive coverage, and explicit non-promotion of the known timing gap.

## Independent full-plan checks

The plan satisfies the review-engine-plan gate for this bounded repair:

1. **Premise and rules.** Independently fetched current Scryfall Oracle text for Hushbringer, Doomed Traveler, Wrath of God, and Curtains' Call and Hushbringer's Wizards-sourced rulings. They confirm simultaneous-death suppression, causal sacrifice independence, pre-death creature characteristics, and the separate graveyard-from-anywhere/self-arrival cases. Verified the cited CR provisions directly in remote `docs/MagicCompRules.txt`, including 603.6c, 603.10/603.10a/c, 603.7, 603.12, 608.2c/f, 611.3a/b, 613.11, 700.4, and 704.3. The plan correctly rejects the existing misuse of 603.2g as a suppression rule.
2. **Reusable architecture.** Event-local evaluated outcomes repair the existing `SuppressTriggers` family rather than special-casing Hushbringer. Functioning-ability, layer, and filter authorities are reused. Before/after outcome storage has a concrete need: saving filters or looking up departed sources later cannot recover event-time controllers, conditions, or effective abilities.
3. **Producer authority and lifetime.** The producer inventory covers the existing `mark_simultaneous_departures` and `stamp_simultaneous_from_slice` production callers, plus the required unstamped multi-target `destroy::resolve` route. It puts keep/sacrifice finalization in the shared sweep helper, moves EffectZoneChoice finalization ahead of continuation, separates SBA iterations and written instructions, and bounds finalization by actual departures and event identity. Zero/single groups, prevented moves, repeated storage IDs, nested causes, and pause segments are explicitly addressed.
4. **Consumer completeness.** Ordinary scalar/disjunctive zone matchers, LeavesBattlefield normalization, batched matching, self/LKI/co-departed/off-zone collection, and the trigger-index shadow path are covered. The dedicated Haunt matcher (`haunt.rs:125`) and death-caused Unattach fallback (`trigger_matchers.rs:2800`) have explicit before-event adapters. Other enumerated registered routes cannot match a death or preserve their distinct cause events. The broad death gate is not reintroduced elsewhere.
5. **Delayed behavior.** Changed registered delayed consumers have production tests for suppression, one-shot retention and consumption, recurring retention/cleanup, same-occurrence alternatives, reflexive disposal, and source/controller bindings. The current creation, matching order, lifetime, and pending/stack authorities remain intact. Direct delayed variants are honestly characterized as exclusions.
6. **Data and boundaries.** The optional ZoneChangeRecord field distinguishes missing history from authoritative emptiness, covers constructors and serialization tests, preserves emitted/parked events, and deliberately leaves nondispatched history copies unset. Runtime rules stay in the engine; no parser grammar, card-data AST, frontend, AI, or protocol decision logic is introduced.
7. **Verification.** The matrix uses the real cast/apply pipeline and natural choice prompts, with exact Oracle or explicitly labeled typed building-block fixtures. It supplies observable effects, reach guards, revert-failing assertions, negative/sibling cases, and unchanged coverage status. The frozen case/corpus/checker and baseline-worker preservation, fresh changed worker, repeated semantic evidence, and actual changed-checkout validation remain mandatory.

Read the applicable repository AGENTS.md/CLAUDE.md and review-engine-plan skill, and checked the applicable add-trigger, add-static-ability, card-test, and existing interactive-handler checklist requirements against the plan. No parser or new-variant checklist is newly triggered.

## Residual assumptions and handoff

This is approval of the plan, not a claim that implementation or runtime validation has passed. The implementation must honor the specified event boundaries, including avoiding intermediate layer flushes that change a simultaneous group's rules world, finalizing completed segments before any collection/continuation, and never falling back from Some(empty) on a repaired clause. The named runtime matrix and fresh frozen-worker evidence are the acceptance gate.

The caller's exclusions remain unchanged and separate: unmodeled aggregate/inherited-target sacrifice batches; replacement-continuation cross-pause grouping; legacy direct delayed bypasses; and ambiguous/restricted death-capable OneOf/NotEquals timing. Their characterization and active no-regression controls are required. No exclusion is promoted to supported by this clean review.

Ready for executor handoff.
