# V10 exact batched mutation evidence

Both remaining assigned batched seams discriminated in both independently run orders. Every named control passed. All source bytes are restored to the exact released v10 candidate. This report is bounded verification evidence, not repair approval.

All edits, builds and tests ran on EC2 in `/home/ubuntu/repos/phase-hushbringer-mutations-r2-r3` with its own target, nightly-2026-04-19 and CARGO_BUILD_JOBS=2. No active Phase or Coworld source write, child executor, commit or push was performed. Prior five-seam and nine-row reports/artifacts remain separate.

Released complete2051-source manifest `3016d5db7d54e3be126e7e83b74e4080d11b52a8bb3ba2bc0da09ef601e1d0f2`, archive `3bc0679cc156ef7a1ee3d8d57c9f341521681595632f32a3337c0846b27e7bc1`, receipt `a0afbd5663fc4548e040830f6e93442499497d987fc76dd10221857e4dfa6fd1`. Exact20-name batch map `b042be1ab1c39292a518657175ca70cb15eeafd0c4fb6d23d0c0bc9ca136529c`. All archive member hashes were verified before fresh-mtime adoption; adoption.json records complete post-write verification. The full v10 plan and clean review were read; source-review-notes.md records exact fixture/guard/storage inspection.

## Compilation and runtime identity

A new canonical Cargo compilation rebuilt the engine and integration artifacts from the full v10 source, with fresh=false and output mtimes after command start. It passed184 tests with20 existing ignored diagnostics. The actual Cargo integration child supplied package cwd, allowlisted runtime/config/package environment including RUST_MIN_STACK and LD_LIBRARY_PATH, plus executable identity. Its preserved executable then directly passed the same184/20 matrix and23 exact filters before mutations.

Canonical executable SHA `a78be2c21c349e0d7873375e696d66b382d82cd16d8770276acea316e3b1c2e2`. Runtime context SHA `ea8972d1adbd5f6d401ac8a3663ba618e6c84093f7c1824cb45c1c10717bacce`; runtime input manifest SHA `b4231b215f1507070cb401e3fdc51f62b04a0f318362dacb5915f422e62259b3`. Compiler tool hashes/versions were recorded before canonical compilation and checked afterward. Generated build-script outputs were archived and hashed immediately after canonical compilation before mutations. Every mutation phase verifies these source/build/runtime inputs; the final audit verifies those outputs, tools and dynamic libraries again. Main-executor card-data generation receipts are retained in the frozen handoff; this executor does not claim an independent generation run.

Each mutant separately recompiles and runs the entire unchanged184-test matrix, preserves the actual compiled executable, then runs every assigned exact order/control filter on that preserved mutant binary. Before/restored checks directly reuse the applicable canonical binary after full2051 source/runtime verification; no restoration compilation is claimed. Exact candidate bytes are written with explicit fresh os.utime before restoration checks. Each recorded phase command has cwd/target/flags, source checks, log/exit and executable hash records. Mutations are formatted before snapshots and recorded phase commands run fmt --all --check. No tests, expectations, setup or guard order were altered.

## Results

| Exact seam | Mutant full matrix pass/fail/ignored | Designated exact failures | Named exact controls passed | Before/restored matrix |
|---|---|---|---|---|
| batched-adapter | 182/2/20 | 2 | 11 |184 pass /20 ignored|
| batched-global-death-gate | 182/2/20 | 2 | 8 |184 pass /20 ignored|

### batched-adapter

Production `crates/engine/src/game/triggers.rs` in `matching_batched_trigger_events`. Exact patch SHA `fb3a03d6cb804423aa9838fec3c6c1f3d8f76a1b2e1c648bfa18f1ea1f5f8dce`; mutant file SHA `61a7b5bf384846acb8cec3c28dbf6b086e8ee822d02b784902dd7242992cba39`. The ordinary precondition and the other batched seam remain unchanged.

before: reused preserved canonical executable after full source/runtime verification; source manifest `3016d5db7d54e3be126e7e83b74e4080d11b52a8bb3ba2bc0da09ef601e1d0f2`; source archive `73f15546658d14231019e7b5dfbead5d7832cfe002b6bd7bc5d6056e06211b63`; executable `a78be2c21c349e0d7873375e696d66b382d82cd16d8770276acea316e3b1c2e2`; phase receipt `ea40395db89ccf0b6715e8ae2bec06d63a25e2921ad9ec2eb3793625feb6b119`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `ab6b475f5eefc1f33870b285d643c86065ab4fae7700e6150733df8a6024ef69`; source archive `5c135bcc7027e4cc5709c7ba22a1c649ee07fab735e3535b2e61f1a385f2e07a`; executable `791ebdfb3d2311a38a0e2118cd89e0a247a61cc1ab5d5adfc75269d2adc8abf1`; phase receipt `28c2027e4e1c1ca823d600270a398b1837a7f344483721a7c2271bfe81119b26`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `3016d5db7d54e3be126e7e83b74e4080d11b52a8bb3ba2bc0da09ef601e1d0f2`; source archive `aed0609cc87f9304dbb72e5efe234407186c6b0fd68609e188c6f9f7c1074a0b`; executable `a78be2c21c349e0d7873375e696d66b382d82cd16d8770276acea316e3b1c2e2`; phase receipt `9c9fbd8925e7f11fd1ff48a1b60ced659b82c38c84565b5c4dd9dd3b614ed619`.

Independently run `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch`; log SHA `6ceaa9a2c73b0dc337b394be68eb61ba23302611661109257526bd83e79e0af5`.
```text
thread 'trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch' (3505793) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6701:9:
assertion `left == right` failed: batched eligible subject count
  left: Some(2)
 right: Some(1)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

Independently run `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_mixed_hush_reverse`; log SHA `f2ffd786610f525e470801c271c5c49b768187d9cece1a0d29595b13e6a538b5`.
```text
thread 'trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_mixed_hush_reverse' (3505859) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6701:9:
assertion `left == right` failed: batched eligible subject count
  left: Some(2)
 right: Some(1)
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

Independently passing mutant controls:

- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_noncreature_only_hush_forward`: exit0; log SHA `caaa2012c77e95fdac17c87f72ea434188ad792760b452512c684d8f25105191`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_creature_only_hush_forward`: exit0; log SHA `cfd5e5bc23b2791255ef1c4b553da7a4fca8371bf55d5704c7e3215005557c99`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_noncreature_only_hush_reverse`: exit0; log SHA `1f4b98453d11027d710a94b784274a06e32de9e1de2f416b89733d0c03220b56`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_creature_only_hush_reverse`: exit0; log SHA `f7cb288a69eca0ec952d146471fbe7fcabadb44092f977bcd336a59a826c7c61`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_mixed_no_hush_forward`: exit0; log SHA `915a913f0f971f63b4370c2db707b2b8dfdf0f9d3cf6a6425ee81a97fbfbaefe`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_noncreature_only_no_hush_forward`: exit0; log SHA `1824ef1fed9e5ff21bd77a10e1ab1641a0eff1665eeee284a1e1b67797b5a702`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_creature_only_no_hush_forward`: exit0; log SHA `60cdf3da923286b9b7d39d623a6c8b07eefad174e5e5e4ae289823610efa6972`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_mixed_no_hush_reverse`: exit0; log SHA `30b8806845fc1216b9ea7d5d5e79218456279cc6304aa8475df3a6765dc5ff72`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_noncreature_only_no_hush_reverse`: exit0; log SHA `9e1df2e319601f7894b0d8a32c93528adea9dd287cc0dbdecc2fb76a5104f53e`.
- `trigger_suppression_event_timing::batched_ambiguous_adapter_filters_mixed_eligible_batch_creature_only_no_hush_reverse`: exit0; log SHA `cbeac5d94c88494fdf2505e173900c6507321c8179747c4dbf5913b6f21dd985`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit0; log SHA `bf7a4b5eb2e78f91984c9b0811d83f6db646c59377f165c48b664d368e1c7c92`.

### batched-global-death-gate

Production `crates/engine/src/game/triggers.rs` in `matching_batched_trigger_events`. Exact patch SHA `6821845b214bedf41ba2f9e7f6b6981a6b2893398b7fc86d94acce0a3e516a9f`; mutant file SHA `cb9566aee38438c40fd69a8971bd44b6579489471c1b8b31fac562675bbdd5be`. The ordinary precondition and the other batched seam remain unchanged.

before: reused preserved canonical executable after full source/runtime verification; source manifest `3016d5db7d54e3be126e7e83b74e4080d11b52a8bb3ba2bc0da09ef601e1d0f2`; source archive `68aee5d2e922cc5ea3ad8c812c60fa8fe96cb6f11503654a2704c0ed44ff5f45`; executable `a78be2c21c349e0d7873375e696d66b382d82cd16d8770276acea316e3b1c2e2`; phase receipt `5f5e8d3327dbf6a82e778c1fce1dce1cbb7d76b559030b184e1497cce114c2ba`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `f8a95ba4a44e8f1e637fb76c546f9a8ff8486648ab94ba922f70dc4cc7e60bf6`; source archive `56bdac8bd9318d0e5e655742a8b1ccf2d4591f0fd2e03bad7b2801fad17e6dc1`; executable `682dc5c7c2a804ce6ace3ea427629ab7afae8dc2ef36daa72eda971ffc9bdc68`; phase receipt `c1b983f2c28af00e259dfeb91780aa0c48baefd8b4fcb6d5f1f53195028ff154`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `3016d5db7d54e3be126e7e83b74e4080d11b52a8bb3ba2bc0da09ef601e1d0f2`; source archive `cfca05f9a0303eb19f3e87b2de034ea7b124960857b99fb605835050ed0ee7fa`; executable `a78be2c21c349e0d7873375e696d66b382d82cd16d8770276acea316e3b1c2e2`; phase receipt `78bd369d58a7d70958f38733aa7de9b0dc27540ad22f6e247fb34c0d3c499f7d`.

Independently run `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter`; log SHA `0066482748ddfa10339b36d5be07f8f65da2d4559af7b0ce236c1a677c7ba9aa`.
```text
thread 'trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter' (3515337) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6685:5:
assertion `left == right` failed: one natural observer registration for the eligible batch
  left: 0
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

Independently run `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_any_hush_reverse`; log SHA `0c57e65513e3b7fb20c435760dd8f143db23fec31bce66bfac36da960a4e91b0`.
```text
thread 'trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_any_hush_reverse' (3515363) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:6685:5:
assertion `left == right` failed: one natural observer registration for the eligible batch
  left: 0
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

Independently passing mutant controls:

- `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_battlefield_hush_forward`: exit0; log SHA `0b3fd31c50098064d4b293b599c795314a9e776e6ccb0b6c05186cda64aa73b8`.
- `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_battlefield_hush_reverse`: exit0; log SHA `bbdf4205942b38a5c975f727aa507d1fac1117f2e7ccd2e62c821dfb084c7999`.
- `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_any_no_hush_forward`: exit0; log SHA `02edc8b5ac1f9dbd6cf60e4695f2725a1cf738364e24e83a0d6729981f876d10`.
- `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_battlefield_no_hush_forward`: exit0; log SHA `07ab1a5d57ae6bb9b6fa60cdf353940a8596ee51c7b41d9a07f2c82f7befd2ec`.
- `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_any_no_hush_reverse`: exit0; log SHA `c0324ab6807ac9c44f6c97b6697b60cd792e9d2458033edddeda89241eed4142`.
- `trigger_suppression_event_timing::batched_self_arrival_bypasses_broad_death_prefilter_battlefield_no_hush_reverse`: exit0; log SHA `0160c99bc840bcd9cb6db9513825587525d15b1df226349bd642dc01733397e7`.
- `trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving`: exit0; log SHA `fddcdfe170fd29e2e9e72ba35555eb88fde7c50591fe9c6a4a08a266afc96f68`.
- `trigger_suppression_event_timing::clause_local_disjunction_registers_once_for_eligible_sibling`: exit0; log SHA `6ba2572fb41c8d355d0a18edfd9cc7266122aa6dc6604c84d9d3434cb3af2cf6`.

## Interpretation and handoff

For the adapter seam, the mixed creature/noncreature fixture reaches the inner batch helper through the eligible noncreature seed. Its native departure/snapshot/peer/incarnation guards run first. Both designated orders print the actual natural trigger/batch context before failing the eligible subject count assertion. The unchanged exact subject-list and settled +11 payoff assertions after that count failure are not claimed reached. No-Hush and single-subject controls execute independently.

For the broad batched death gate, the destination-functioning Any/SelfRef seed reaches the inner helper with Hush surviving. Both designated orders print the actual natural context before failing the registration-count assertion. Subsequent subject and settled-payoff values are not claimed observed. Explicit-Battlefield and no-Hush controls, plus original nonbatched compatibility tests, execute independently. The source helper correctly expects None subject_match_count for this self trigger.

Complete printed native departure/context payloads, first failures, all before/mutant/restored command results and binary/source associations are in audited-results.json and the retained logs. Full-matrix failures are reported separately from the designated semantic failures; no zero-match, setup/compile error, ignored diagnostic or unexecuted later assertion counts as discrimination.

Both exact held mutations are completed and ownership is released. No unresolved item remains in this bounded two-seam assignment. The isolated checkout contains the exact v10 candidate bytes. Overall implementation approval, final validation, commit/push and Coworld attribution remain with root and its independent reviewers.
