# Hushbringer plan v5 — fresh full review

Result: one blocking implementation gap. The v5 owner/member design resolves the executor's v4 stop in principle; the correction below is a bounded wiring completion.

Reviewed the full /home/ubuntu/coworld-migration-20260904/hushbringer-plan-v5.md against clean baseline 2dec6c88915db4697706234a7ba2fcedd97b1689 in /home/ubuntu/repos/phase-verifiable-loop, the original Hushbringer/Traveler/Wrath task, and the implementation stop report. All commands, source inspection, current Oracle/ruling requests, and this report write ran through ssh nishadsingh-box-4. No source edits, builds, tests, commits, or subagents.

## Blocking gap

### [P2] Thread the SBA owner through the existing standalone Augment departure helper

Plan evidence:
- Lines 173, 181 and 191 require same-action SBA sub-checks to receive the iteration's borrowed owner token and explicitly bind each member; they prohibit inferring ownership merely from global scope state.
- Lines 182–195 make explicit claimed occurrences the exclusive source of parent snapshots and co_departed stamping. An unowned leaf under a capturing ancestor retains None and cannot join the parent.
- Line 216 claims one owner for the complete existing SBA iteration.
- Lines 110–119 give a strict edit manifest that does not include game/augment.rs; only newly discovered constructor obligations can extend it without review.

Source evidence:
- crates/engine/src/game/sba.rs:247–255 calls game::augment::check_standalone_augment_permanents(state, events, any_performed, battlefield_snapshot) within that iteration.
- crates/engine/src/game/augment.rs:168–205 computes its existing standalone set, then loops through it and calls sba::move_to_graveyard_via_pipeline for each actual departure.
- crates/engine/src/game/sba.rs:675–691 exposes that helper with only state/id/events, so this caller cannot pass the new owner token as presently specified.
- At baseline, sba.rs:299–300 stamps the whole iteration's emitted battlefield departures, including this external sub-check. triggers.rs:2119 onward uses that stamp to discover co-departed observers.

Consequences: changing the shared SBA helper to require a token creates an unlisted caller/edit obligation. Leaving this external path unchanged makes its leaf unowned beneath the new capturing iteration frame. It then loses the iteration's snapshot and its contribution to the exact claimed co_departure set. This can lose an already-working no-Hush observer payoff when an observer dies in an earlier SBA category and the standalone Augment creature dies in the same iteration. This is an introduced ownership/stamping risk, not an existing nested-layer or cross-pause limitation. No failing execution is claimed; the gap is demonstrated by the call graph and the proposed ownership contract.

Smallest required revision:
1. Add crates/engine/src/game/augment.rs to the narrow edit manifest for token plumbing only.
2. Specify passing the same iteration token from check_state_based_actions through check_standalone_augment_permanents, and placing with_departure_member around each existing move_to_graveyard_via_pipeline call (or forwarding to a token-taking private SBA delivery worker). Preserve its existing candidate computation, live guard, replacement authority, pause result, and any_performed updates.
3. Retain its current public helper behavior for any standalone callers if needed; do not open a second owner or infer an ancestor token.
4. Add one production apply/cast test reaching this existing sub-check in the same SBA iteration as an ordinary death. A labeled typed fixture can make an otherwise legal creature gain Augment during a resolving chain while the chain makes an observer lethally damaged, so both are applicable when the normal SBA pass begins. Prove both departures, a shared claimed group and authoritative snapshots, and the exact no-Hush observer payoff. Pair it with the reached Hush suppression case. The no-Hush co-departed payoff must fail if this token threading is omitted. Keep this a test of existing SBA wiring, with no new Augment or merge semantics.

## Remaining review disposition

No other blocking gap was found in the full reviewed plan within its explicitly bounded scope.

- The primitive covers the existing SuppressTriggers family rather than using card names. Current Scryfall Oracle strings and Hushbringer's Wizards-sourced simultaneous-death/from-anywhere rulings were independently fetched through the remote host and agree with the premise.
- The cited timing/rules sections were checked in the current local docs/MagicCompRules.txt. Before/after timing, written-instruction boundaries, SBA iterations, and the self-from-anywhere exception have an appropriate rules basis. The misleading existing 603.2g interpretation is explicitly removed.
- The transient owner/member stack, closure epilogue, incarnation binding, actual event keys, resolver reentry barrier, zero/single/error/pause closure and reset behavior supply a concrete producer-to-leaf authority. They do not require a new layer transaction.
- Existing replacement execution calls use resolve_ability_chain, so the specified reentry barrier covers the inspected independent replacement chains. The inspected deferred-cost simulation/commit occurs before its proposed sacrifice owner.
- The clause-local ordinary adapter and canonical registered wrappers preserve the explicit ordinary-live versus delayed-ungated compatibility contract for ambiguous origins. Dedicated Haunt and Unattach routes, registered delayed lifetime/alternative consumers, and ordinary/batched/index paths have concrete dispositions.
- Event constructors, serde None versus Some(empty), deferred-event carry-through, scope exclusion from serialization/equality, normalization, settled clone/checkpoint handling, and the non-authoritative history ledger have specified treatment.
- The verification matrix includes production entry points, positive reach guards, negative/sibling cases and revert discrimination for the required changed seams. The additional SBA row above is needed to complete its new ownership claim.
- The original frozen worker/corpus/checker and repeated rebuilt-worker evidence remain mandatory implementation acceptance work. This review does not substitute for them.

Applicable instructions read: repository AGENTS.md/CLAUDE.md; review-engine-plan; add-trigger; add-static-ability; card-test; project-reference; and the relevant existing interactive-handler lifecycle checklist. There are no parser or new enum changes, and no frontend/protocol decision changes requiring corresponding implementation work.

All existing exclusions remain unchanged: aggregate unless-payment and inherited-target completed sacrifice loops; full cross-pause grouping; direct delayed bypasses; ambiguous OneOf/NotEquals timing; and existing intrinsic merge/reentrant-child layer-world limitations. The finding above must not expand any of those categories or become a layer/engine rewrite.

Final repository verification was read-only. Runtime behavior and compilation remain untested by this review.
