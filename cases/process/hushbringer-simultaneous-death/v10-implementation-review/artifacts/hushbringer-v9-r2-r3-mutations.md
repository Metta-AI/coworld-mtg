# Frozen v9 R2/R3 mutation handoff

Completed at 2026-09-05T18:44:33.669953+00:00. All five specified isolated mutations reached the intended semantic assertion failures. All 15 clean-before and 15 restored exact-filter invocations passed; mutants produced 10 expected assertion failures and five retained-control passes. No compile/setup failure, data skip, ignored test or zero-match result counted as discrimination.

This is bounded execution evidence, not repair approval. It binds only the frozen v9 candidate. Original-production overlays, full repair acceptance, current planning revisions, other mutations and independent implementation review belong to root or their separate executors.

Checkout: `/home/ubuntu/repos/phase-hushbringer-mutations-r2-r3`; dedicated target: `/home/ubuntu/repos/phase-hushbringer-mutations-r2-r3/target`; base `2dec6c88915db4697706234a7ba2fcedd97b1689`. All work ran on EC2 through SSH with keepalives. No Mac edit/build, child agent, commit, push, Coworld write or active Phase write.

## Immutable provenance and execution

The full 752-line reviewed plan and full clean review were read. `immutable-input-bindings.json` verifies plan SHA `1e2c3adde42263f56fc9a25c7745854f4a5426ae4d2c25eda36f4f6fb0c3613f`, review SHA `b340c41d627e9068990ea4d37caba5111dd307cb7e43b42c6eb7116ffc84647a`, five-seam specification SHA `6194816481d7aeaef2a5bdbb009f96ae9cf999135837d371bcf3da57c4196ad9`, frozen receipt/archive/source hashes and active-10 reference receipt.

All 2051 complete frozen source files, including cfg(test), .cargo/config.toml and untracked modules, were extracted by byte writes with fresh mtimes. Every hash was verified. Frozen source manifest SHA is `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`. Runtime fixture/card-data/rules inputs have their own verified manifest and archive. Curated integration fixture and both mandatory Oversimplify executions prove data loading; no DB-unavailable early return was accepted.

Each before/mutant/restored directory retains its complete source manifest/archive, mtimes, exact commands/environment, exit files, logs and compiler-artifact/executable hashes. Mutations have exact unified patches and original/mutant file hashes. Every mutant and restoration has an engine Cargo artifact with fresh=false and an output mtime after its command started. Engine/integration targets were rebuilt against the changed file before results were used. Full-source checks before and after each command protect against unarchived edits.

Toolchain is nightly-2026-04-19; jobs2, own target, no RUSTFLAGS, test threads1, repository RUST_MIN_STACK=16777216, dev/test opt0 and line-table debug. Toolchain details and flags are in build-context.json/toolchain.txt. Exact commands use cargo test -p engine --message-format=json with --lib or --test integration, fully qualified filter, --exact --nocapture --test-threads=1. Mutations were formatted before snapshot; recorded phase checks use cargo fmt --all --check. Tilt was unavailable.

## Per-seam results and authority map

| Seam | Before | Mutant | Restored |
|---|---:|---:|---:|
| R2-resolver-barrier | 4 pass / 0 assertion fail | 2 pass / 2 assertion fail | 4 pass / 0 assertion fail |
| R3-original-entry-exit-lki | 3 pass / 0 assertion fail | 1 pass / 2 assertion fail | 3 pass / 0 assertion fail |
| R3-original-entry-incarnation | 3 pass / 0 assertion fail | 1 pass / 2 assertion fail | 3 pass / 0 assertion fail |
| R3-bounce-exit-controller | 3 pass / 0 assertion fail | 1 pass / 2 assertion fail | 3 pass / 0 assertion fail |
| R3-oversimplify-exit-controller | 2 pass / 0 assertion fail | 0 pass / 2 assertion fail | 2 pass / 0 assertion fail |

### R2-resolver-barrier

Changed production seam: `crates/engine/src/game/effects/mod.rs`. GameRunner cast two-target ChangeZone -> replacement no-op delivery tail -> resolve_ability_chain -> explicit SelfRef Sacrifice -> zone leaf -> outer owner close.

Same X ObjectId and initial incarnation bound before proposed move; wrapper None barrier keeps child unowned. Event snapshot lives on emitted ZoneChangeRecord; parent owns only Y. No-op preserves incarnation; actual child/parent departures increment each once. Scope closes before later independent Traveler death.

Both orders fail X trigger_suppression.is_none at integration:4356. Pre-assertion logs independently show X Some(empty), X peers[Y], Y peers[X], one replacement/one sacrifice, initial0/final1. No-replacement and redirect-only controls each execute both orders and retain intended membership/no-op behavior.

Exact test results:

- before: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `7cac469e570d664c8c165a6b7f9fdb48f0770ebda2950d759f235688238b6b4e`; phase receipt `1c8b12aa9e260ae8dcf15f5b4ab6e492a6ca7a167cb678d64b80e5d11e9f4178`.
  - `trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.14s; log SHA `e9f6a09284ba64fbbd6a85c54b5a13bd54eec3714d6e877ab56d0e5ee55294fe`.
  - `trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure_reversed`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.14s; log SHA `b5bbf011bcb88a1d6686379d64d2c87987695936e9563ce71c0231324136f84c`.
  - `trigger_suppression_event_timing::resolver_reentry_no_replacement_borrows_outer_owner`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.63s; log SHA `c3a93bcd714e069e4639ebf68a2b68d473ed45355c0bfe58b53905560f30715a`.
  - `trigger_suppression_event_timing::resolver_reentry_redirect_only_preserves_original_incarnation`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.16s; log SHA `c1c230551277a45087009d61006390f62e87a9b7ac6c1e53af6917c9c5b716b1`.
- mutant: source manifest `8c9bc1c9f65986f8fb98c73b6ce5a7038841e58982c2f41be1f6493aa6292ded`; archive `7255ebdb9422a897f142163ec9b2e364ebcb4b1a0048e9784e3f9918f745e942`; phase receipt `fac12ba402fcd03c9648e0fb0f7eb8cf68bbf4a099ed8e8f220deb7d4824c47a`.
  - `trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.14s; log SHA `110f3b87b4c6113b1fad01be0f06cd98bf5fe975c2e50708ae89de57c5dc8c78`.

```text

thread 'trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure' (3306014) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4356:9:
assertion failed: x_record.trigger_suppression.is_none()
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:

failures:
```

  - `trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure_reversed`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.14s; log SHA `0c78f0f4bb2a021cc16d51c0201f2beb704a217665003294a37578458816f994`.

```text

thread 'trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure_reversed' (3306042) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:4356:9:
assertion failed: x_record.trigger_suppression.is_none()
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:

failures:
```

  - `trigger_suppression_event_timing::resolver_reentry_no_replacement_borrows_outer_owner`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.16s; log SHA `e32716e3776e0351c020e429c1b846c9332afdb90ba30856aa680e8c02c66643`.
  - `trigger_suppression_event_timing::resolver_reentry_redirect_only_preserves_original_incarnation`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.17s; log SHA `fdb3f4bd6414a301aae1b82a5c97c55a892a5999a5a683bebf840b5725b0f23d`.
- restored: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `190d6d3ac205bcb51529f5b21a2819b19e7dd9ecfae8115fab7426ea635a2912`; phase receipt `ddfafb6e67abefeced42f43851ed2eccc02e4f9e9e587ab5ea84c8eff96d7362`.
  - `trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.15s; log SHA `bbb755055892821c081a39e7376b0ef2d70adc5f5d05757872c2349c52413ce6`.
  - `trigger_suppression_event_timing::resolver_reentry_same_incarnation_cannot_claim_outer_departure_reversed`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.26s; log SHA `6527979185b998541f2bd6f7ad314a27be6ad6ce12b2926b337415c236738270`.
  - `trigger_suppression_event_timing::resolver_reentry_no_replacement_borrows_outer_owner`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.16s; log SHA `16141f29937141e392432542bc0fee540c6c308f088cfda5cb03c1cc87eaba7a`.
  - `trigger_suppression_event_timing::resolver_reentry_redirect_only_preserves_original_incarnation`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.16s; log SHA `5afa1a828592ddc75534aebc125e7eee82cd4b43f8352bd8d3d746f15c0ece79`.

### R3-original-entry-exit-lki

Changed production seam: `crates/engine/src/game/filter.rs`. Old condition test: seeded +2/+2 UntilEndTurn TCE -> flush -> move_to_zone -> check_trigger_condition -> matches_zone_change_event_object_filter. Public companion: real entry -> unresolved trigger -> legal exit/removal responses -> original trigger resolution..

Observer base/live2; entrant base1/effective3. Actual exit prunes TCE and stores exit LKI3 while live returns1. Original event destination Battlefield plus off-battlefield entrant selects cached exit LKI. Mutation replaces only that read with live filtering.

Old positive fails triggers.rs:11864 after live1/LKI3 guards; public condition fails life20 versus21 at integration:5152. Independent unpumped public negative passes. Old weak unit sibling is after failing positive and is not reached in mutant.

Exact test results:

- before: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `324f3f95379aedd568f5be36cfe3e1d9d1afb869caa578820c5ced717ea83976`; phase receipt `322e641bed5155af0b77d98dba6829daf6dff8cf6b125f21d068c0ac3d020476`.
  - `game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `83e2c5baf6371354e56697c9f6cad23ef63cb0496202b0a1f9b9e0be163ff435`.
  - `trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.84s; log SHA `b46838e742efa66a1b82644547c89c1a341d500b04c346ccd105cf6352d2e699`.
  - `trigger_suppression_event_timing::original_entry_lki_public_unpumped_entry_does_not_trigger`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `b34085be2f8db59b2d55f1617254613bc0961a8687da0f782f60ea8cb2f0a18b`.
- mutant: source manifest `a1d5f3ece402cd09194847652265b6f50f5ad6829f2652a60d34208857999ff1`; archive `6ee855356e395ccd757065b4c7e986ec7756a3854e256e62d43ab213463ccfe2`; phase receipt `ed9595b8e4dfd1ad61449d91f86784d5999f62fd16d884643df9ad1e043726a1`.
  - `game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `266d2e8d71d6dd4e97c26c6ad52caa248c6a0c239fed387d67d513c8f8511caa`.

```text
test game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield ... 
thread 'game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield' (3313571) panicked at crates/engine/src/game/triggers.rs:11864:9:
exit LKI 3/3 > source 2/2 (CR 608.2h); pre-fix reads reverted 1/1 -> false
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:

failures:
```

  - `trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `e2b265eb09c8f37ef74379a601187a1a43c94df33e7a8c3cd29b1959731d3ca6`.

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

  - `trigger_suppression_event_timing::original_entry_lki_public_unpumped_entry_does_not_trigger`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `e0b7e334d737f5521002a81a07739200493ab7362813023c20ebf35fda44ff6d`.
- restored: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `fcf705aa64bbfd6ca566926db3614dc695539a73a7767a429e87d8bd9a3a9043`; phase receipt `f6c1cf70ae4bbe6ce24f6d0c5962cb11c289e9b01b9d00b109c69ec32c74edd4`.
  - `game::triggers::tests::zone_change_object_condition_entering_uses_exit_lki_after_leaving_battlefield`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `66a491158638a22ee35b6b8ad0c4db04f7f9635edb3b7b47fdc9d4d9ce8ef76a`.
  - `trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `ca0d93711fdb0f9a9ba76c07450e6dfcb8c9f6604a106256bb9cfec11a03dc4f`.
  - `trigger_suppression_event_timing::original_entry_lki_public_unpumped_entry_does_not_trigger`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `17ca99a313b88a612d3ed21f0964fd3a74336a5bcc05a457c7f70c3fbd004f8b`.

### R3-original-entry-incarnation

Changed production seam: `crates/engine/src/game/filter.rs`. Old real Hand->Battlefield entry -> seeded TCE -> actual exit -> same-ID reentry -> original condition recheck. Public companion uses legal response casts before original trigger resolves..

Original entry carries entered_incarnation; old exit caches3 and prunes object-specific TCE; reentry is a new incarnation live1. Zone-and-incarnation guard selects LKI for original trigger. Mutation removes only entered-incarnation comparison, preserving zone check and LKI branches.

Old positive fails its original-exit-LKI condition; public same-ID reentry fails life20 versus21. Non-reentry public response control stays passing.

Exact test results:

- before: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `4f0df367c88f5a9b4d97924fa685b13ffbcea56610dd5ca9cb3047ebf67eea4c`; phase receipt `d5d4e219df865bcbe6d859f25a972715907f2ac8c111a82e9193ac694c482aa1`.
  - `game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `7d6f19fdd0609acae9224f7a30c22c8bbc3a396708fffc2dbc6e1a3f31e0913c`.
  - `trigger_suppression_event_timing::original_entry_lki_public_same_id_reentry_preserves_original_condition`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `33dc81a4c622a896598fd2aca5d8aa9b2733873a1306ffb4974c33b7f4271a45`.
  - `trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `6de747df0420ea630ce1c71f9804c5061866a0f76ed441d5045b01261292c8fd`.
- mutant: source manifest `4b02c8b8fa14bdbb651bb6a5616e1dc79e69927a31ce257026feef893e9899e3`; archive `adad57870148a5920fe6903213e84ce0480c77174db07fc2f29fae4cdee8bd09`; phase receipt `8b43188e326079d6a71da3c775fd848f943f4e65e8d4fff20d668db09d727737`.
  - `game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.09s; log SHA `638ec9d5cd3dcc5097f0425cb8e5e580eef5b6876781f6d584023b0df89490d2`.

```text
test game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry ... 
thread 'game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry' (3327287) panicked at crates/engine/src/game/triggers.rs:12093:9:
original exit LKI 3/3 > source 2/2 (CR 608.2h); reverting the incarnation gate reads the re-entered base 1/1 -> false
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:

failures:
```

  - `trigger_suppression_event_timing::original_entry_lki_public_same_id_reentry_preserves_original_condition`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `3e0b334ebf8fcf0c148f56a581c1f42db38eb4a4ca21b73b80045bec63fd95db`.

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

  - `trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `2c947fe19c7d7a3d97becbb526f3aa7a414ed4ac31d970ca899dd6312cbf2f31`.
- restored: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `13f88114f811c5dcb1e109d1da6a6a8ef8b94699b460a6b0c1781dc469b5eb85`; phase receipt `e6851e0a1a098e47b1fa3854702c24e5f6a9144f887043327f59cd7efe424c8d`.
  - `game::triggers::tests::zone_change_object_condition_uses_original_exit_lki_after_leave_and_reentry`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `49fcedaf19fc4e149c150a260431036ef1b1597f7e169a05b0e93105be49338b`.
  - `trigger_suppression_event_timing::original_entry_lki_public_same_id_reentry_preserves_original_condition`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `e3cf10d086645e5436cd742a7f940bd67dbc7d4c69409e83952d8f7e748a37bc`.
  - `trigger_suppression_event_timing::original_entry_lki_public_responses_preserve_original_condition`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `ff6026015e28b9402e64f26b623739b08011950ec399a57b7f1b8a602636dcb0`.

### R3-bounce-exit-controller

Changed production seam: `crates/engine/src/game/effects/mod.rs`. Old seeded actual temporary control -> unchanged bounce/conditional Draw chain -> TargetMatchesFilter(use_lki). Public companion casts GainControl UntilEndTurn then real bounce/draw chain..

Target remains P1-owned. Temporary control binds P0 until exit, event/cache preserve P0, live resets P1. Only explicit use_lki event/cache controller is locally replaced with live controller; all other fields and general effective_controller remain unchanged.

Positive old draw-one becomes0; public theft branch also fails exact draw-one. Original P1/no-theft negative runs independently and passes. Old positive helper reaches owner/control/exit/LKI guards before draw assertion.

Exact test results:

- before: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `5a2738635b47c0be0f5437c76446886af1f79804a376f9c3c8f26b05c10e4599`; phase receipt `3e48c04ba9b347d7de3f5079dc3a9fd740d2771cabd11c7a9b6c8f5154527c17`.
  - `game::effects::tests::bounce_followup_draws_when_caster_controlled_parent_target`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `058a554f923fd94173e0deb90eb6d8ebe0726b234495b8886e7a999a571a56e8`.
  - `game::effects::tests::bounce_followup_skips_draw_when_opponent_controlled_parent_target`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `f6c26b18c7a408059cf1bea15ae80c7f98d6ce8ace5ded1a389518810cc3f9cd`.
  - `trigger_suppression_event_timing::real_control_spell_then_bounce_uses_exit_controller_for_draw`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `034f7956d69102b168d757d5507cb0b029a52238ee2f07e0ad64a4ebf48a128c`.
- mutant: source manifest `d667c425a996d5f6ee1be01b74fb05358bfd1fbc5d14ede631b2057d6095cd52`; archive `b1d835b7634bd9ef370276c357567e61827c6e7bf0fd851fb70db0e3b65e24ce`; phase receipt `e5412ab45f7ce30908d4b1d4627268f1666661a76d280e6441c80a76da7635d4`.
  - `game::effects::tests::bounce_followup_draws_when_caster_controlled_parent_target`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `eb37ca77bfbd892ee81eee3b713c9ff65e43aa60a0aa173ac6cbe9dce8643302`.

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

  - `game::effects::tests::bounce_followup_skips_draw_when_opponent_controlled_parent_target`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `9f17ff0d418a2805b2b7f70007e7820dbdba5d378d728a405a1f1e04155be973`.
  - `trigger_suppression_event_timing::real_control_spell_then_bounce_uses_exit_controller_for_draw`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `82a2be8baa6ffb84ed4116afc65e1d82c934ac4d7256e137e370282d3c465652`.

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

- restored: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `da53b3a0fe730c8afb762631f33061e49aba914de07281a66b025f7e21a2abb2`; phase receipt `5e0c551fb0fb21667840e8b5130fd2ec29cb2725b778c5ff6f7c14fe3a4937e3`.
  - `game::effects::tests::bounce_followup_draws_when_caster_controlled_parent_target`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `ab585b3cf7a6fc71a836cf8c49231667751bc29d29f3811b475cf8757729f167`.
  - `game::effects::tests::bounce_followup_skips_draw_when_opponent_controlled_parent_target`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 16587 filtered out; finished in 0.00s; log SHA `3a5abe3ec2043b2c149a21324dedf34191d7d912bf771f6bdd7e943185e54249`.
  - `trigger_suppression_event_timing::real_control_spell_then_bounce_uses_exit_controller_for_draw`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 0.01s; log SHA `78349924a1fd67bf373cd18f9012e16a162ec5bc6717b81139228d3fcc5038b6`.

### R3-oversimplify-exit-controller

Changed production seam: `crates/engine/src/game/filter.rs`. Old full loaded Oversimplify definition/parser assertions -> real exile/token chain. Public companion casts temporary theft at legal P1 priority then full Oracle Oversimplify with five mana..

P0-owned2/2 controlledP1 at exile; exits livecontrollerP0/cachecontrollerP1/power2. Off-Battlefield/Stack LiveOrLki chooses exit controller to partition exiled power. Mutation changes only this effective_controller return.

Both original/public theft tests fail P0 counters7 versus5 after exile/LKI guards. Public no-theft7/3 case executes first and passes. P1 counter assertion in failing theft branch is not reached; no runtime claim of its later value.

Exact test results:

- before: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `f64721fbce207987fcba8dbcc63321d06489d1a1ee962037dad62b77c820466e`; phase receipt `2d8a20e20ff4088bd1ba136ebb57788ab1bece03df8e071c5aac03ae8404c00a`.
  - `oversimplify_per_player_fractal::oversimplify_per_player_fractal_counters_match_exiled_power`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 1.21s; log SHA `83981e3f0343c4808088cb9b0fa7b646512fd4ab112a14dafbc83f5329bc65a1`.
  - `trigger_suppression_event_timing::real_control_spell_then_oracle_oversimplify_keeps_per_player_exit_power`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 1.19s; log SHA `340a15bb7ffeabf346ffa012c4fc2c4f1feac306ab7ab8bf756bb10393e27000`.
- mutant: source manifest `aa1deb3202b92ea785863768c6c02a073ae6b810f54f83a5d80cd911536758cf`; archive `6eb26a3488483286ab7fc91f9eed3a6833583f314ee7a85939350c11108927c2`; phase receipt `8fc0e86cf69606cacf3ddcd3b90319b3c2ca9d82d24730b46e803fc771754664`.
  - `oversimplify_per_player_fractal::oversimplify_per_player_fractal_counters_match_exiled_power`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 1.23s; log SHA `6caad7af37ef47fdb957b8ce7cd85a0fdc14b408bd3f17bd2c7f43c2bd17ceb2`.

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

  - `trigger_suppression_event_timing::real_control_spell_then_oracle_oversimplify_keeps_per_player_exit_power`: exit 101; FAILED. 0 passed; 1 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 1.20s; log SHA `e4838ed1e518588094a57a9717c12eb83e0fadd3414d8ce409a2560f03cc7241`.

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

- restored: source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `2369914da3be71aaca402fb65448cca2bfaebab0fd7e2b0e4f76b9827af8d8ea`; phase receipt `fca62700a7f99a6b75566827931b521360e2a6cfb256c26572b1d24767e563e6`.
  - `oversimplify_per_player_fractal::oversimplify_per_player_fractal_counters_match_exiled_power`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 1.37s; log SHA `b41ea1e20dfa68863f1e1899c2daef12161a17eb065f944a87c03039009fffa3`.
  - `trigger_suppression_event_timing::real_control_spell_then_oracle_oversimplify_keeps_per_player_exit_power`: exit 0; ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3088 filtered out; finished in 1.30s; log SHA `6716dd7464a68e9f1729332f51cea5cf120abf7f771a039a7160349c9295acdc`.

## Scope, limitations and ownership

Root explicitly corrected one metadata-only test name: specified bounce_followup_does_not_draw_when_caster_did_not_control_parent_target does not exist; the retained frozen negative is bounce_followup_skips_draw_when_opponent_controlled_parent_target. No test byte or expectation changed. This is recorded in spec-name-correction.json.

First-failure order is preserved. R2 logs both peer sets and X snapshot before its first assertion; later peer assertions are not claimed separately executed. The old exit-LKI weak unit negative lies after the failing positive, so only the independent public unpumped control is observed under that mutant. Oversimplify directly observes P0=7 versus5 in theft; its later P1 assertion is not reached. The preceding public no-theft7/3 control executes and passes.

One initial setup-only command failed with exit127 because non-login SSH PATH lacked rustc. No build had begun; PATH was corrected and the attempt retained in setup-attempt-1.json. No five-seam compile/test process was interrupted. Root separately stopped extra active-checkout Clippy under resource pressure; that external interruption is not this subtask's evidence.

Parser/CR annotation gates: no parser mutation or new annotation; frozen tests and annotation text were preserved. Final source is byte-for-byte candidate, so there is no production change to review from this executor. The snapshots add no serialized surface or runtime capability; they record counterfactual executions only.

All five seams are mapped to reached production/old-authority paths, exact assertions and named controls above; no specified mutation remains unresolved. Assertion-order limits remain explicitly available to the independent reviewer. Repair approval and broader acceptance remain unresolved outside this assignment.

Five-seam mutation ownership is released with all candidate bytes restored and no five-seam command running. Root has separately assigned eleven reserved matcher/filter mutations to this same executor/checkout after this report; those will have a separate supplemental handoff and cannot alter these immutable five-seam receipts. Active Phase remains read only.
