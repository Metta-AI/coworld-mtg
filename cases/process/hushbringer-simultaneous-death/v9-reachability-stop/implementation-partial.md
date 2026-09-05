# Hushbringer v9 implementation — partial stop and ownership handoff

Final partial handoff 2026-09-05T18:22:41.616327+00:00. Root requested stop-and-return because the reviewed battle-protector handoff runtime discriminator is not reachable through normal supported-format game-over flow. Fresh integrated planning/review is required. Active source remains frozen and ownership is released to root. Isolated experiments continue under root ownership; this is not an implementation-complete or accepted-repair claim.

## Result and source identity

The reviewed per-selection deferred sacrifice provenance is implemented. One Count(2) selection remains simultaneous; distinct Count(1) selections have distinct component boundaries even with identical filters and cost source. Canonical pending IDs survive clone, serde and normalization. Old nonempty or malformed provenance is preserved on load but refuses progression before new payment/discard/append mutations; CancelCast and natural reannouncement recover. Authorized Concede and existing independent preferences/debug permission gates remain available. The original event-time suppression repair, exact resolver wrapper discriminator and the four reviewed transient-layer/controller fixture corrections are retained.

- Base: 2dec6c88915db4697706234a7ba2fcedd97b1689; branch codex/hushbringer-simultaneous-death.
- Frozen2051-file manifest: [source.json](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/frozen-candidate-v9/source.json), SHA256 46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803.
- Complete candidate including untracked modules: [source.tar.gz](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/frozen-candidate-v9/source.tar.gz), SHA256 3f7768a91a7456a5b0b7e6a5d9cb6f769eb8fd2c6ec0cfeec9fac559cb8cb1a5.
- Tracked patch SHA256 bec636d52b8c7225c6646c7f92ce7e3d41bf37cbcf547c29aa6b78176c920383; the archive also contains both untracked modules.
- All commands, reads, edits, compiles and artifacts were remote through ssh nishadsingh-box-4. No commits, pushes, Coworld source edits, production pin changes or child agents were performed by this executor.
- Root owns independent implementation review, final commits and clean committed-worker acceptance.

## Verification currently complete

| Gate | Exact result and evidence |
|---|---|
| Active public suppression matrix |91 passed,0 failed,20 ignored; [active-10/1.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/active-10/1.log).|
| Full engine library |16,581 passed,0 failed,7 ignored; post-generator-restoration compile [active-10/4.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/active-10/4.log). Includes scope/private pipeline, event serde and four new component guard tests.|
| Full integration target |3,067 passed,0 failed,22 ignored; post-restoration compile [active-10/5.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/active-10/5.log).|
| Engine Clippy |cargo clippy -p engine --all-targets -- -D warnings exit0; [active-10/2.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/active-10/2.log).|
| Formatting |cargo fmt --all --check exit0 before compilation and after generator restoration; [active-10 receipt](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/active-10/receipt.json). No source changes during the certified run.|
| Card-data generation |exit0,2,870 token presets,35,802 schema-valid card entries; [generation.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/card-data-final/generation.log). Only known-tokens.toml/oracle-subtypes.json changed among2051 tracked/candidate source files; original bytes restored with fresh mtimes. Exact generated/before/restored files and hashes preserved in [receipt](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/card-data-final/receipt.json). Full card-data JSON SHA50335033e5bf8e0871ecb57bb9d9a710869aafb042c27c83c90b07fd468fb4bf unchanged. Post-restoration library/integration compilation associates the restored source.|
| Explicit desired diagnostics |Fixed candidate2 passed/18 failed; [active-10/7.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/active-10/7.log), exit101. Original isolated production0 passed/20 failed; [baseline-r3-8/6.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/baseline-r3-8/6.log). Each retained ignored case is diagnostic, never passing repaired coverage.|
| Original R3 fixtures/public companions |Corrected tests pass on original production in its own target: old LKI6,bounce2,Oversimplify1,public entry3,real control2; [baseline-r3-8 receipt](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/baseline-r3-8/receipt.json). Test-only overlay is separately preserved and audited; original production is unchanged.|
| Scute committed batching guards |5 passed, including real landfall-copy shape, refusal and divergent-prefix siblings; [receipt](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/scute-committed-batch-guards/receipt.json). This is deterministic behavior/batching evidence, not throughput.|
| Historical Scute throughput snapshot |Unavailable: both existing ignored benchmarks explicitly skipped because /tmp/gamestate.json is absent; [log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/scute-available-guards/command.log). Root also searched retained artifacts and found no original snapshot. No throughput number claimed.|
| Bin tests/rustdoc/workspace Clippy |Bin unit tests15 passed; rustdoc0 failed/7 existing ignored examples (none executed). Extra workspace Clippy exited101 after root SIGTERM to two active clippy-driver children for memory pressure, so this is resource-interrupted evidence, not an actual compiler-diagnostic result; [active-11 receipt](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/active-11/receipt.json). Prior workspace Clippy failure is the original manabrew-compat SetFullControl E0004, separately reproduced on isolated original production; fresh workspace rerun remains required when memory permits. Root interruption receipt: /home/ubuntu/coworld-migration-20260904/hushbringer-v9-workspace-clippy-resource-stop.json.|
| Root exploratory worker |Root reports all10 frozen cases satisfied and repeatability/receipt checks passed using original checker. Worker SHA2bc9d4c58c0c3ac54ceafdbe09c7208f5b1f7dca04cdb627ebba1e572b75e55b; [root campaign receipt](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-exploratory-campaign-receipt.json). Exploratory only, not acceptance.|

## Exact changed file list

All paths below are relative to /home/ubuntu/repos/phase-verifiable-loop. No Cargo dependency, parser, database, oracle semantics or enum variant changed.

| File | SHA256 |
|---|---|
|crates/engine/src/game/augment.rs|2043b2204e22607e7c1a087803e15a7c366eb6545b5da443bd15c2d44fe82460|
|crates/engine/src/game/casting_costs.rs|3aa382b537506f6b71e1bd3c4041ff8564878711c9a382a2a24bc0c67a19b162|
|crates/engine/src/game/derived_views.rs|1bd7797b61555a7396ea07dcd342d70323664a2b3246499cdaafa13b770d7775|
|crates/engine/src/game/effects/change_zone.rs|c5e12a1cad5cbc23a87e48c23e0ebd3f8f8878eb347c0172bd2bed718db6b56b|
|crates/engine/src/game/effects/choose_and_sacrifice_rest.rs|8b889373a9238b46a169044b3405a5efb7b7dfcf378209da2726f09dde5d1bcc|
|crates/engine/src/game/effects/destroy.rs|4e406bbd6cf734adf91b1f4b700ee9b19745b44b50dbbb44af46bc098b6b5006|
|crates/engine/src/game/effects/mod.rs|35b0d4f29051664c16f798f3f9b806f2aa5f34928ed893bdae150d803d2fbc26|
|crates/engine/src/game/effects/sacrifice.rs|81b55a267e6538f47c406bae9e6dceb0915c187e7d684dc80ffd30b238417d27|
|crates/engine/src/game/engine.rs|e58c0f6ff1d62bb6d0c78b2cbe45a880681766369a4c92cf60124ecfca8d1822|
|crates/engine/src/game/engine_resolution_choices.rs|88425c7787d1afcdacc5d8789bafa99d712f7b837ed8455ca0b7b64b5e2bfa77|
|crates/engine/src/game/filter.rs|8be0212e2d35255eb269b4d1b3a8c494c54c233eca4c11d9cc58c2f28a750f66|
|crates/engine/src/game/game_object.rs|a5737473ca1011bacdeefdde53866c67ed3079ab212101c11e5fe31f1f456abc|
|crates/engine/src/game/haunt.rs|2a4226407c86adca02220dab2bd95ec9b4f4817c125f7861005980a6fa7a1e3a|
|crates/engine/src/game/mod.rs|4d5c083a86163f7706dbc10466d4ad8804ad9cfe74bebfc48ea8896a9a3e32c1|
|crates/engine/src/game/sba.rs|1099bf23c185e6982d64276882ba036c66591bffd5d1bdf7c23b82f9670106c0|
|crates/engine/src/game/stack.rs|228b8f8082d1775f75e336f25f304648a5f3c0704d5b8339c9087a8ff9777cb9|
|crates/engine/src/game/trigger_matchers.rs|1eef66a5b3f50dceb8643ede0ea6deac723336640a3bd006dfa96406eb7002d7|
|crates/engine/src/game/trigger_suppression.rs|f37e54b657772b0551e46d3d612e4d44682ebfd6cffca8b1936b80d266d929cc|
|crates/engine/src/game/triggers.rs|05cc6b381dc6637312e4f7559f764355c3485b25185136fdde6107d5881c4903|
|crates/engine/src/game/zone_pipeline.rs|ecc6dbd6f0385c72ab2238dc700692c60255f041628985e4ac6cf5db301a8e72|
|crates/engine/src/game/zones.rs|740e37afea6f50ad08af2a27b9603ed06c576341370d6664ceb4a1080f35b6f3|
|crates/engine/src/types/events.rs|ebfd1027f45468d12a9f97bc2f057b9c457166e09ba824a61b028343beaa20c9|
|crates/engine/src/types/game_state.rs|065812c4cf63c11a1bb724f7997b07346c76a2480eceebfa0bb30ec7a02c3828|
|crates/engine/tests/integration/issue_3277_captain_nghathrod_eliminated_opponent.rs|e9c899abb333a2ee836dde07e3770963eaa9829f5a47143100aefcd9125a3172|
|crates/engine/tests/integration/issue_5332_gandalf_trigger_doubling.rs|3e165ca76c8fec0c94eea3894df7b2020d1ca8bf5dee14e060f01ba63196c5ae|
|crates/engine/tests/integration/loop_shortcut.rs|f1b7a337c26554bc0c7b82b39c524f5cd1ebbac80195b751984b920f31b5b134|
|crates/engine/tests/integration/madame_null_integration.rs|07e4406f5333bfc1ee4bd91e0a95819920ad0300776178bd18c720653f416c69|
|crates/engine/tests/integration/main.rs|3c9de72738baaf5c2f4009a282f309776661182bc806b2be3483b212a3208438|
|crates/engine/tests/integration/oversimplify_per_player_fractal.rs|c0f3c1512a23df4005facfb0b605558022fa605766e30a827a11f03f0e2a6b51|
|crates/engine/tests/integration/trigger_suppression_event_timing.rs|85f67b07f89f44b7bd7a5d6b3399bfbbfa62c2501ffc8a33b3c5739a3dd6ca11|

## Path, authority and mutation maps

The [maintenance matrix](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/maintenance-matrix-draft.md) maps producer authority, storage, lifetime, consumers, invalidation and concrete positive/hostile fixtures. It is being completed with actual isolated results. The [public mutation map](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/public-mutation-map-progress.json) preserves exact transformations, actual failing test/assertion excerpts, all passing sibling test names, source archives/manifests, command/exit/log hashes and fresh compiled integration executable identity for every mutant and restored candidate. Each public command runs the entire91-active matrix; ignored diagnostics are excluded from mutation success.

Root now owns the deterministic41-row public supervisor in phase-hushbringer-mutations. At handoff8 rows have exact runtime failures and restored91-test matrix passes;0 survived and0 compile-invalid attempts. The other33 rows are in-flight/unstarted, not complete. Root explicitly assigned the independent resolver/four old LKI-controller seams to phase-hushbringer-mutations-r2-r3, and19 non-public seams to phase-hushbringer-mutations-library. All targets are separate. Canonical restores use fresh byte writes; no cross-checkout target reuse. Incomplete, survived or compile-invalid attempts remain evidence, not kills.

The three native EffectZoneChoice library-position member wrappers have no reachable owned Battlefield-departure behavior under existing constructors/zone validation: [source reachability](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/library-choice-reachability.json) and [root disposition](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/library-choice-disposition.json) apply the existing full-plan line132. No killed wrapper mutation or repaired behavior is claimed for those three arms. Real Battlefield library-leaf/after-world mutations remain required. Fresh implementation review must audit the classification and placement.

## Provenance, CR and parser audit

Exhaustive constructor and pending consumer evidence is in [source-constructor-parser-audit.json](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/source-constructor-parser-audit.json). Only handle_sacrifice_for_cost creates nonempty production DeferredSacrificeSelection entries. Pending storage preserves IDs; validation never guesses identity by filter/source equality. Other consumers keep their existing object/filter/controller/mana/reservation authority. Synthetic/legacy ZoneChangeRecord constructors remain None; authoritative empty snapshots remain Some(empty). Lexical owner state is serde-skipped and reset at completed boundaries, while persistent pending component IDs survive normalization.

The [novel CR audit](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/novel-cr-source-audit.json) compares58 new/nonidentical annotations against41 exact rule paragraphs in active docs/MagicCompRules.txt SHA4381ad1b39ab2c05f7d03633a20f711ed37277074d3266dcba5f38cbb527423f. The wider raw diff audit includes moved comments and86 IDs. Timing603.10/603.6c, grouping608.2f/704.3, control/PT layers613.1b/613.4c, LKI608.2h, concession104.3a and existing cause/lifetime rules were checked semantically. Old skill tables were not treated as rule authority.

No parser support was promoted. Full Oracle strings and typed fixture guards retain their original labels. The complementary-OneOf test certifies only the existing parser shape, including its lost positive-versus-excluded origin provenance. Typed replacement, delayed and suppression fixtures are not named-card parser claims.

## Preserved failures, corrected fixture expectations and limits

The earlier empty-choice drafted expectation20 failed with actual23 in [extended-6/1.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/extended-6/1.log). Original production independently reproduces23 at [baseline-r3-8/0.log](/home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/baseline-r3-8/0.log). Full-plan preserve-publication instruction therefore retains empty prior tracked-set compatibility23, with nonempty selection replacing the prior set and giving22. The test name explicitly states this compatibility;23 is not a new rules-conformance claim.

Separate exclusions remain aggregate grouping, inherited-target grouping, full cross-pause grouping, ambiguous origins, direct delayed suppression, intrinsic merge/nested layer worlds, source availability, aggregate paid continuation, cast-created regeneration persistence, and the specific resumed duplicate dispatch. Seeded regeneration certifies the first Destroy replacement application only. The aggregate predecessor fixture certifies payment and skip-loss, not a following paid continuation. Resumed exactly-two Spirits is one narrow baseline compatibility; its desired-one diagnostic remains unchanged.

Failed compile/fixture attempts and immutable receipts remain under /home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution. Earlier fmt-after-archive attempts extended4/5/6 have exact postformat supplemental source archives, matched to their recorded compile-source manifests; original receipts were not relabeled. Later certified attempts formatted first and ran fmt --check only.

## Stop proof, remaining obligations and ownership release

The precise stop is documented in /home/ubuntu/coworld-migration-20260904/hushbringer-implementation-stop-v9-battle-protector.md (SHA256456da9e54e8b4306f859c76ecf63125211734f81c29fc365676e120af10e10da). Source/topology proof: /home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/battle-protector-stop-proof.json SHA256f54d36ec126c27681f7a42714977cc16d5b704ab1fd52395d2e1b2108a5f6238. Independent library executor proof: /home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/battle-protector-reachability.md SHA256626dcd161fe097cd12d40585f6db2845bee1256728eb4393e624bf60b0174034; receipt SHA256f8944129109ab70ad8df9568b38d95ad9c0ae0e5627f6d8077a1720f1dcb731a. Full v9 has no disposition analogous to its explicit native-library-choice restriction. An inconsistent eliminated_players versus player.is_eliminated fixture, bypassing terminal handling, or a custom-format terminal mismatch cannot substitute for the required legitimate runtime proof.

Eight other SBA public fixture proposals are staged, not adopted or certified here: /home/ubuntu/coworld-migration-20260904/hushbringer-v9-library-mutations/proposals/sba-public-observer-fixtures.rs. The library executor is independently testing under root authorization. Fresh v10 planning/review must integrate the exact stop, those fixture obligations and all inherited v9 gates without retiring coverage.

The frozen proof at handoff is /home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/public-mutation-map-at-handoff.json. Completed public rows are Augment, targeted Destroy, mass Destroy, keep/sacrifice sweep, targeted ChangeZone, mass ChangeZone, shared batch delivery and resumed ChangeZone. Every row has exact source/patch/command/log/exit plus an actually fresh integration test executable and restored positive. The live progress map can grow after this handoff; the handoff copy is immutable.

Remaining:33 primary public rows; completion/merge of the independent five R2/R3 and19 library rows; evidence-backed disposition of any survived/invalid/unreachable seams; any reviewed fixture adoption followed by appropriate fresh source freezes and checks; rerun the resource-interrupted workspace Clippy gate; final complete maintainer/physical-seam map; independent implementation review; root final commits and clean committed-worker acceptance. The missing historical throughput snapshot remains explicitly unavailable, not a passing benchmark.

Performance scope: normal captured departures, including Some(empty), avoid per-matcher fallback rescans, and ordinary ETB uses its cached static list. Legacy/unavailable None records in trigger_suppression.rs160–174 recompute active statics inside the death helper. Universal no-suppressor throughput for that fallback is not established; fresh planning/review should assess this source fact against the hot-path requirement. No measured throughput regression is claimed.

I release active source ownership, primary isolated mutation checkout/supervisor ownership and this agent slot to root. Supervisor PID3257715 remains remote under nohup, with own target and jobs2. Full fixed-source/restore guarantees, script hashes, exact row status, independent owners, safe11-row suffix, graceful quiescence and forced-stop recovery protocols are in /home/ubuntu/coworld-migration-20260904/hushbringer-v9-execution/public-supervisor-handoff-v9.json SHA25695461ce788a8bc52c4cdd7f78e20280df27ecfd27a66ee4c881f4ef910ec18e8. Root can reserve only unstarted rows using reserve-public-mutations.py; explicit marker directories make the driver skip those obligations before source mutation. Markers are never completed proofs. No suffix has yet been reserved or reassigned. Active source remains unchanged from the2051-file freeze.
