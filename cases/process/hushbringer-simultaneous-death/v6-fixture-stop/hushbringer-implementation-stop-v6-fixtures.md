# V6 executor stop: three fixture/claim contradictions proven on original source

This is a new stop artifact, not an overwrite of the prior v4 stop. Per root instruction, dependent assertion changes and proposed dispositions are on hold pending revised plan and fresh full review. No production edits were made by this test executor.

## Evidence lineage

All inspection, file writes and commands ran through `ssh nishadsingh-box-4`. Baseline `/home/ubuntu/repos/phase-hushbringer-baseline-tests` remains at `2dec6c88915db4697706234a7ba2fcedd97b1689`, with an empty production-source diff. The original three-test Oracle reproduction and initial hashes remain immutable in `hushbringer-baseline-v6.log`, `hushbringer-baseline-v6-receipt.json`, `hushbringer-baseline-v6-source-manifest.txt`, and `hushbringer-baseline-v6-initial-test-module.rs`.

The expanded baseline overlay copies the active semantic fixtures. Its only baseline compatibility transformation replaces `assert_snapshot` with a documented no-op and replaces new-field-presence guards with `true`, because original source has no event snapshot field. No payoff, life, zone, target, ordering, listener, count, or equality assertion was changed. This overlay is not claimed to test new snapshot data. Exact original overlay/active hashes and transformation are in `hushbringer-baseline-v6-expanded-fixture-receipt.json`; final expanded overlay/source/log hashes and clean production diff are in `hushbringer-implementation-stop-v6-fixtures-proof.json`.

Active command: `cd /home/ubuntu/repos/phase-verifiable-loop && export PATH=/home/ubuntu/.cargo/bin:$PATH CARGO_BUILD_JOBS=4 && cargo test -p engine --test integration trigger_suppression_event_timing -- --nocapture`.

Active semantic receipt: `hushbringer-active-tests-v6-attempt-4.log`: 41 passed, 3 failed, 4 ignored. Original primary both orders, no-Hush twin, Augment, Haunt, Unattach, member-layer/type preservation, ordinary/Any/ambiguous timing, delayed lifetimes/alternatives/controllers, primary producers, cost commit, Devour and identity tests pass.

Expanded baseline command: `cd /home/ubuntu/repos/phase-hushbringer-baseline-tests && export PATH=/home/ubuntu/.cargo/bin:$PATH CARGO_BUILD_JOBS=4 CARGO_TARGET_DIR=/home/ubuntu/repos/phase-verifiable-loop/target && cargo test -p engine --test integration trigger_suppression_event_timing -- --include-ignored --nocapture`.

Expanded baseline receipt: `hushbringer-baseline-expanded-v6-attempt-1.log`: 15 passed, 33 failed, 0 ignored. Expected original-bug failures are not a build failure. The three residual active failures have identical baseline outputs, detailed below. The known direct-delayed, inherited-target and full cross-pause desired assertions also fail on original source; the aggregate desired suppression assertion is currently masked by the independently failing continuation guard and must not be described as reached evidence.

## 1. Aggregate unless-payment continuation

Test: `aggregate_payment_no_hush_and_surviving_hush_single_payment_controls` and the same helper used by `known_gap_aggregate_payment_should_group_completed_selection`.

Natural route: typed spell -> UnlessPayment -> PayUnlessCost(true) -> WardSacrificeChoice(min_total_power=Some(2)) -> SelectCards -> actual Hush/Traveler or vanilla/Traveler sacrifices -> settled priority. The typed gain-1 continuation is marked `SequentialSibling` on the child (initial parent-marker fixture attempt was corrected before this evidence). Both baseline and active produce P0 life20 versus required21 at the continuation guard. Intended victims reached expected zones first. Therefore the expected zero-Spirit assertion in the ignored desired aggregate case has not yet been reached; the continuation bug is not evidence of suppression discrimination.

Source evidence: `engine_payment_choices.rs::handle_ward_sacrifice_choice` loops selected sacrifices, emits EffectResolved, sets priority, and calls `resume_pending_continuation_if_priority`; this route and continuation logic are unchanged by v6 production diff. The fixture demonstrates a pre-existing omission, not a repaired continuation contract.

Proposed bounded disposition (not implemented): move an observable gain instruction before the unless-payment instruction and use paid/declined life totals + actual sacrifice + settled priority as the reaching success guard; explicitly record that this fixture does not certify post-payment continuation. Preserve separate diagnostic evidence of the post-payment continuation limitation. No parser or payment/continuation engine fix.

## 2. Cast-created regeneration shield

Test: `destroy_guard_regeneration_and_indestructible_preserve_actual_departures_only`.

Natural route: cast typed Regenerate on Traveler -> confirm nonempty replacement definitions -> cast two-target Destroy(cant_regenerate=false), targeting Hush first and Traveler second. For protect_hush=false, regenerate=true, Traveler reaches Graveyard rather than required Battlefield on both baseline and active. The installed-shield reach guard passes on both. The preceding indestructible fixture passes. No new capture-regression claim is warranted from this fixture.

Source evidence: `effects/regenerate.rs` creates the ordinary Destroy replacement with `valid_card=SelfRef` and regeneration shield kind; existing Destroy tests seed the same replacement definition directly. The creator appends only effective replacement definitions. This executor does not repair that unrelated lifetime problem.

Proposed bounded disposition (not implemented): seed the existing typed regeneration replacement fixture before the cast, using the established builder so the actual Destroy replacement authority is reached; retain cast-created-shield failure as separately named baseline diagnostic evidence and do not claim regeneration-creation/lifetime repaired.

## 3. Resumed ChangeZone duplicate payoff

Test: `resumed_change_zone_segment_captures_hush_and_traveler_after_natural_pause`.

Natural route: three announced ChangeZone targets in explicit order first/Hush/Traveler; first has two applicable Graveyard->Exile redirects causing real ReplacementChoice; serialize/deserialize paused state; choose replacement and resume remaining Hush/Traveler tail. No-Hush twin replaces Hush with vanilla. Both baseline and active move first to Exile and remaining two to Graveyard, but create2 Spirits versus required1. This is a reached ordinary-payoff discrepancy, not a scope setup failure.

Source evidence: unchanged `effects/mod.rs::drain_pending_change_zone_iteration` collects/dequeues resumed tail triggers; replacement completion continues through `engine_replacement.rs` into the unchanged post-action scan in `engine.rs`, which can see those same events again. Production peer independently traced these unchanged paths. New capture does not implement replay deduplication.

Proposed bounded disposition (not implemented): preserve an explicit active compatibility assertion for the existing no-Hush two-payoff result, keep a desired-one-payoff characterization separate, and require the Hush suppression branch's zero payoff plus authoritative resumed records. This would validate suppression and baseline preservation, not certify resumed replay correctness. The planner/reviewer must decide whether this is acceptable or require a different reaching fixture; it must not silently upgrade the original v6 exact-one claim.

## Independent remaining work

Two already-authored independent tests (chosen spell/activation cost invalid-selection retry and library-position choice/leaf behavior) await compilation/execution. Immediate/deferred cost and library-position scope branches have explicit public apply entry points. Production peer owns Cargo for lifecycle/serde and clippy; this executor is not building concurrently.

Per-seam rollback discrimination, final coverage/maintainer matrices, remaining explicit controls and complete acceptance are not yet finished. No runtime/card/parser support expansion or full completion claim is made.
