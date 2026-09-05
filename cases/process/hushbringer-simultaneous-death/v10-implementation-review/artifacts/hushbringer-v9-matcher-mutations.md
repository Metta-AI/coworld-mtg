# Frozen v9 supplemental matcher mutation evidence

Completed nine assigned rows at 2026-09-05T20:28:15.900422+00:00. The two batched rows remain unexecuted under root's explicit hold for fully reviewed fixture changes. This is bounded verification evidence, not repair approval.

All work ran on EC2 in `/home/ubuntu/repos/phase-hushbringer-mutations-r2-r3` with its own `target`, nightly-2026-04-19 and CARGO_BUILD_JOBS=2. No Mac build/edit, child executor, commit, push, active Phase write or Coworld repository write. The original five-seam report and artifacts remain separate and unchanged.

The exact supplemental release SHA is `dee6a9f52c59bf2dd621861ec8e6f7afbedf1465b1eb687776b1683210f52ec4`. Independent ownership verification confirms the original driver skips each reserved marker-only job directory. The complete frozen v9 source manifest is `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803` (2051 files), including cfg(test), new untracked modules and .cargo/config.toml. Full source archives, runtime fixture/card-data/rules manifest/archive, build context, exact mutation patches and commands are retained.

## Execution method

Root explicitly authorized preserving a freshly compiled canonical integration executable for candidate-before/restored checks. The canonical full matrix passed 91 tests with 20 existing ignored diagnostics. Every mutant was freshly compiled in the same dedicated target, with Cargo fresh=false engine/integration artifacts and output mtimes after command start; each ran the entire unchanged 91-test matrix and exact named filters. Each mutant executable is also preserved by byte copy and hash.

After each mutation, the original file bytes were written with fresh mtimes and all 2051 source plus runtime-input hashes were verified. The same full matrix and exact filters then ran directly on the preserved canonical executable. Those restoration checks deliberately reuse the canonical binary; they do not claim a restoration compilation. Candidate-before checks use the same explicit method. Actual Cargo child cwd, allowlisted runtime/config variables including package metadata and LD_LIBRARY_PATH, executable hash and dynamic-library hashes were captured in runtime-context.json; direct commands use that same package cwd/environment and verify library hashes. Source checks bracket every recorded phase command. A supplemental, explicitly later audit of the still-running supervisor records absence of replacement-index/set-gating and library-preload/audit variables; it does not rewrite the earlier Cargo-child capture. Mutations were formatted before snapshots; phase commands use cargo fmt --all --check. No test expectations, public setup or guard ordering were changed.

Canonical executable SHA `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`; canonical full-source archive SHA `e1d6aa4ccc573d98c55ae509077faa96041182e4880a96cb183fabce9f78b8ad`. Complete Cargo/binary associations are in `runtime-probe/binary.json` and `audited-results.json`; confirmed direct baseline results are in `canonical-runtime-confirmed`.

Build-inputs-verification.json records a read-only post-build audit of the frozen Cargo.lock, toolchain/config/build-script/TOML source hashes, actual compiler executable hashes, and generated Cargo build outputs. All generated-output mtimes precede the final canonical compilation; output bytes are archived, and final audit rechecks their hashes and unchanged mtimes. The canonical build and every mutant retain Cargo build-script records. This records post-build hashes, not an independent regeneration or a claim they were captured at compilation start.

## Outcomes

| Mutation | Mutant matrix pass/fail/ignored | Exact named exits | Restored full matrix |
|---|---|---|---|
| before-clause-gate | 42/49/20 | [101, 101] | 91 pass / 20 ignored |
| any-clause-after-to-before | 85/6/20 | [101, 101] | 91 pass / 20 ignored |
| ambiguous-origin-before-misclassification | 87/4/20 | [101, 101] | 91 pass / 20 ignored |
| ambiguous-origin-after-approximation | 87/4/20 | [101] | 91 pass / 20 ignored |
| delayed-ambiguous-live-gate | 88/3/20 | [101, 101] | 91 pass / 20 ignored |
| ordinary-adapter | 90/1/20 | [101] | 91 pass / 20 ignored |
| ordinary-global-death-gate | 89/2/20 | [101, 0] | 91 pass / 20 ignored |
| self-arrival-exception | 90/1/20 | [101] | 91 pass / 20 ignored |
| before-live-subject-authority | 89/2/20 | [101, 101] | 91 pass / 20 ignored |

### before-clause-gate

Production path `crates/engine/src/game/trigger_matchers.rs`, function(s) `zone_change_clause_matches`. Exact patch SHA `8c1deb96bc6f33325ec7aa3c736ecbcd15265cea2a2fca60738bc9a8c0aa320f`; mutant file SHA `2609440e68a32618f51fb51c43a221e41a16e1f2b6d9f731b2cdecddae665e30`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `2d6e957a9ce6aa2ea499443d8644ccc5baa734ff1b705072aab76253fc050e44`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `e2bb6d047afed43e9820aeeb03bec863196479986edd9cf7919f165bff3d34e3`.
- `trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `8be77a3f94bcac59f49212d58f42428598b81499dd166a200d6f68201441d4fd`.
- `trigger_suppression_event_timing::delayed_first_suppressed_occurrence_retains_one_shot_or_recurring_listener`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `2d43e1aa550fa690262c45c2dbc3da9187b6471fa26434dfe76743c3d013c557`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `42e13cae87ade91d6e6a14fd6b3998b8de04db3c9214a6b1d5d024afd3f69243`; archive `0aa25e68c11972cd6c7ae7ae069d8cd7d7a4c529d9fea048a769bff78ca50482`; executable `0c2a0cec220dc06d8209906535819eb2cf15e9b1773f3857074ea1d2e0d3dae0`.

- `full matrix`: exit 101; {'passed': 42, 'failed': 49, 'ignored': 20}; log SHA `2d12b585d8e2f13b0e90182aca769c0da4f8c44a178c3ee9f1ddc9547c57b13c`.
- `trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `b039cb1e07e6eb8cc86233600b1dcef4d91a1c8890ebf99ec80904a21d471307`.
- `trigger_suppression_event_timing::delayed_first_suppressed_occurrence_retains_one_shot_or_recurring_listener`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `192901fbf7836694bbede3d9455b5c5b8acc7d3f7e3644aa08c062f8a561ff0b`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `518cfea1d800fb3e7b6e293d057759f9a149b994e327aea375db0cf7b20f1b5f`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `1e7cf26d96fbd4cfaea0970bdb0bdc2fbe730218314333905aa5c49c9890b076`.
- `trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `8be77a3f94bcac59f49212d58f42428598b81499dd166a200d6f68201441d4fd`.
- `trigger_suppression_event_timing::delayed_first_suppressed_occurrence_retains_one_shot_or_recurring_listener`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `2d43e1aa550fa690262c45c2dbc3da9187b6471fa26434dfe76743c3d013c557`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::oracle_wrath_hush_first_suppresses_simultaneous_traveler_death' (3403225) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:135:5:
assertion `left == right` failed: simultaneous-death-suppressed; hush_first=true
  left: 1
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

```text
thread 'trigger_suppression_event_timing::delayed_first_suppressed_occurrence_retains_one_shot_or_recurring_listener' (3403402) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 0, got 3 (before 20, final 23)
  left: 3
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```


### any-clause-after-to-before

Production path `crates/engine/src/game/trigger_matchers.rs`, function(s) `zone_change_clause_matches`. Exact patch SHA `d96c5c8f585432fac59e853a7a738eda5df6cb2c697b57083430e59caa2d71f9`; mutant file SHA `9ffd210ffa241e1ffd47a7356fbec3abedb9980790a103df485b8fbe3b99bdbe`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `7587dceae368801a1894505a6d1c0ded8c7c57f08a0e2b49270c62178c8eba50`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `20fc1ada79160047525693aaa447f29ba1383d89530216b07a2b835f0b939fa4`.
- `trigger_suppression_event_timing::from_anywhere_and_dies_observers_choose_different_worlds`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `19db7ecb9d8e6ef638772a3c5af713b3ee58233ff32cacc09bc71397d79ecbca`.
- `trigger_suppression_event_timing::delayed_same_occurrence_tries_eligible_alternative_exactly_once`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `b8899f53e7cd6e9de5272d3b79376ac45effd637541812f2d284077b5ab0f6c5`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `20ecc9b5f117d7676af99fa7d2e4b6076f6e7bb83b542334f56a76779fdba067`; archive `56b4fd2fb3bd6ff0fd019c1cac817d18f7b5dcf1258b006e5dc1f6d5c44a133f`; executable `aa20461402cd358ea1f79561cec633c51b43f916b45b610dc0ccb833ca8f9729`.

- `full matrix`: exit 101; {'passed': 85, 'failed': 6, 'ignored': 20}; log SHA `f394d0eae0febc96357bb5ab507ba434100a2d4a41c03b6b4e48b82c63efcc27`.
- `trigger_suppression_event_timing::from_anywhere_and_dies_observers_choose_different_worlds`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `45eb0c6551702a1b07e1c90e6d3bc41b7767bf98a8fb3a636b59a97a6b6b42c5`.
- `trigger_suppression_event_timing::delayed_same_occurrence_tries_eligible_alternative_exactly_once`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `01d1c58e4cfbe3968a2b1dacdd8f714b82a0282cd55347a9d0bbc6ca433c0a9c`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `919225ced8c6d2a9ab9a9a05fb293a3b537c0f5eac5ed1bf0af2d6511e8e9406`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `268dfa047f7ba8d56bc2d35dad15002a7adccf43c33f2cba1b34d8a50c84358f`.
- `trigger_suppression_event_timing::from_anywhere_and_dies_observers_choose_different_worlds`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `e096cbc1d9aaa2d7e4046a617921884a95a57ea2f2e78d764fab310c7ab88d34`.
- `trigger_suppression_event_timing::delayed_same_occurrence_tries_eligible_alternative_exactly_once`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `5e6f42e777c79dac5b758562c71b5fdacfc4c1a57e083618cfb1b59b2201e43c`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::from_anywhere_and_dies_observers_choose_different_worlds' (3419190) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 1, got 0 (before 20, final 20)
  left: 0
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

```text
thread 'trigger_suppression_event_timing::delayed_same_occurrence_tries_eligible_alternative_exactly_once' (3419200) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 4, got 0 (before 20, final 20)
  left: 0
 right: 4
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```


### ambiguous-origin-before-misclassification

Production path `crates/engine/src/game/trigger_matchers.rs`, function(s) `zone_change_clause_matches`. Exact patch SHA `30a02841ef287ae0b7949ad5b5337421958af1fb8065aa898a34b4f9bbfd5ae5`; mutant file SHA `ca59e22f5434de1219ad09cbe4b10e743cffe77e6af7390e08e229d62fa2c168`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `ca524f28ce45690c797b30c40cf97691abd94d9886258d54bd654b3bb1f74a89`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `9fda21bdfd71755b224df355e74d8f317292b3124a943fba3f647c49af7ec186`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `598525f067e8874f80aa060d82d4847a7bcea0a1fd4978031ac3ed5bc202b2ff`.
- `trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `305a87b9513f2171e6e7ca26c62b5a2a4f187dddbd1d73cfaa108a348a9f0f19`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `26497796a212f7aa9720a8d3b11b5e937ec239b46d60ceffca94cda7843e0ecf`; archive `2bc8e2fb06d358d40168f6471a85dba5f0cc46b59a06bea38519d3e2f00b9984`; executable `c3ee6dc86c40eba7730a34a3f8e473093040adbcb131db853643c6515004e13d`.

- `full matrix`: exit 101; {'passed': 87, 'failed': 4, 'ignored': 20}; log SHA `1a0bb20bbb2a31f87ed987a060ce0996ac2f78bd2c816d04dac6a794b7b38959`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `b835dd52c30e1e02c52531576dab9fbce9cfec8bdb96ce1c6d66b80ab7000dd8`.
- `trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `876dc40d85afbcbf3253b2daac0a5696e00da40447606314defe207b2ee1bb7d`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `888b7edc222ab52976545c291c353b78cb553f1ad2a4ea7c53cdc0c530dbfc1b`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `18b9096ca2a758714bb1549e3b20e93a2acb26ce29e8ae264271f523615af549`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `e0209b48f2a56b420407c26b23b4a3fa6c005bf4b2c5c9ca132d3eae4a802b20`.
- `trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `5506b92bd1bcb51a6ad320ebf7c0a8b662e6119a9dc8923599c4fb6b49e3d045`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility' (3426254) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 1, got 0 (before 20, final 20)
  left: 0
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

```text
thread 'trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility' (3426256) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)
  left: 0
 right: 2
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```


### ambiguous-origin-after-approximation

Production path `crates/engine/src/game/trigger_matchers.rs`, function(s) `zone_change_clause_matches`. Exact patch SHA `0733e8c1d5c5819e3f3e78da6c9052f65670b9fd70741a2443fb5e9cceb5b4c0`; mutant file SHA `842942a8f5012240ec30ce4b323f4def363e05467227975a727c85383b5079a0`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `4c3512510995b23f2237701056f12d05b2aae1cae822585cd3c3eef17e14b181`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `fc0811985d1ddb329637423054842c8fb88f680e5d01d1904b7d64fb7c1fb96b`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `f3f5d5c69cc5d02cf033fe237adc3715e225737f2ee041a4a1c9fa86a6bae01a`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `81d940ed2d1e15ae312a17359c084234dbe128497413ab5a440917aedca91b54`; archive `480fc567444adb0a7ea242d7cc13027042ef771377ae39e4e636ce2250d6d65e`; executable `121b4eecdd50c84d39dd3c05a627359913e4b07f6d41ba6cf936da574aae856f`.

- `full matrix`: exit 101; {'passed': 87, 'failed': 4, 'ignored': 20}; log SHA `d2a2b10d672fce58f1c7306e5a4daf88d8dea6091706b052f6a0e0d0fb88334c`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `b8d11395997b1b56e6ff5a7d1a6d3754d9d4ed1bdfea3c53275d27723a642365`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `02b4370ad1ba024ae5c4f938b5befc0673fe13a27b45f1eb13e5d986171e2561`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `9dcadac95b41a78b5bf3387917f447fb107d2994dfc1082ad1250a3faab1d301`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `e0209b48f2a56b420407c26b23b4a3fa6c005bf4b2c5c9ca132d3eae4a802b20`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility' (3429845) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 1, got 0 (before 20, final 20)
  left: 0
 right: 1
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```


### delayed-ambiguous-live-gate

Production path `crates/engine/src/game/trigger_matchers.rs`, function(s) `match_changes_zone`. Exact patch SHA `361dd36c1354ee24f082fd09df428e5d243544514f8b4273eb6e10d38d89b342`; mutant file SHA `8e3319c7c94c39f06d335ba39fd27e0bffac3193617da0d95ca74956be6ba531`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `60e8d409935c94a12027747a6f78277979d2d98345a68a6f4709942d557c7aff`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `143221af2e7d426a113bb4b3ad62cf41ad395eeb39498b6f06b4acb97a040449`.
- `trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `f2c345a90de71831e3dc84b5ffa4254eaf4e4bdeb1cf8d41e251597d83bdf965`.
- `trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `534f8095433c99dc84cfd4362c1028b048e94399d410376e510fab0a1e0d08bb`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `5ab16fa8c0bbdfacb18d3b9f2792650eb0fb43e02f8d6f731c974a3403a4bdb4`; archive `1a24295acc02f8c7fd494826e3a5632c085f620d37da043e949db98867bc74e5`; executable `e983222769523b7b65c9b87a2e3e6b36d79f297fc66b1d5f3623f46868608d99`.

- `full matrix`: exit 101; {'passed': 88, 'failed': 3, 'ignored': 20}; log SHA `3dc6c0604bfdfe772c29584cff0369de55b45123d7ca9f04911b00071cd71a8f`.
- `trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `02d8afe3e60b79331e5b3a168eddfe964fa392166f333f3796c4712b0aea4ed4`.
- `trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `55f97cef4fedea5486a2b648caa0824fd33578884bb27a53bdf8637709815d8a`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `acc923bbbf5269e042df4280a41440ae754eded5c138a41d8522bb7c7f229ef2`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `aaa3e186de4c866cf01bdba34ed2353be12460839c37de46c04743d251ff54b9`.
- `trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `d3d9487d9fc5bd80c79311267d7d9ea80e8ec2deef4b14c0c03c0a72e5e98e60`.
- `trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `92be97c11f99c316f70b153412088b3c1c99f1ddd411341e3d6b16cb6be75d86`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::ambiguous_registered_delayed_matchers_preserve_ungated_compatibility' (3436690) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)
  left: 0
 right: 2
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

```text
thread 'trigger_suppression_event_timing::ambiguous_delayed_primary_alternative_co_death_and_identity_compatibility' (3436692) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)
  left: 0
 right: 2
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```


### ordinary-adapter

Production path `crates/engine/src/game/triggers.rs`, function(s) `collect_matching_triggers_inner`. Exact patch SHA `4e4a568be306c9e984c5f464e8146190381277bf8231b1d11eb633eed6ba9d63`; mutant file SHA `f6b210d8264d7ab1aa3cd1e4aedbd2648a127b892e29fa2f10d803fd2df1f5b3`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `8acb3ce959a917f33062aef1e3c7a374e7a1a7870f35b4dcd2117a9aca967252`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `bdfefe00ee1b265a51654c617bebf52192565a0c4050f8de457ac7880a1bc9d9`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `f3f5d5c69cc5d02cf033fe237adc3715e225737f2ee041a4a1c9fa86a6bae01a`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `9d11f9196844b02183e7548fb5ec785fd1c1edbc2b880033b79644d8c73beca2`; archive `10a398af6ef3eeec21acc0467590e323d9e668f26c3150f6f4023157fedda77c`; executable `8ac6b58a6bd9b340db07ebcac0b0d0af738e5ab4e62c66be5ddf33958032e5e6`.

- `full matrix`: exit 101; {'passed': 90, 'failed': 1, 'ignored': 20}; log SHA `ecd131d1a0e50819091bcc2e1263ce81ad51b9f3031df319b5d01b433d4edf64`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `16f4e9d45a2dfa2858753aee9719456fee95678b36108fa4977a7baa5415c4e8`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `101af301e4d8f1a20606180c32544ddc5a3c639129a42b81688cff6476ee2041`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `67dcbe06821a394dd55b222d37f89471df4f286820be877188a965f3a6b5253e`.
- `trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `e0209b48f2a56b420407c26b23b4a3fa6c005bf4b2c5c9ca132d3eae4a802b20`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::ordinary_ambiguous_origins_preserve_live_collection_compatibility' (3441317) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 0, got 1 (before 20, final 21)
  left: 1
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```


### ordinary-global-death-gate

Production path `crates/engine/src/game/triggers.rs`, function(s) `collect_pending_triggers`. Exact patch SHA `f223bb097842971952c017c67c96b32ed7716f367f017855df6c5bdaa2cfdb29`; mutant file SHA `eb3864bcfc711372f6234e135136c090ad6a29e31d2afcdca81a2f8a3b24e84b`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `4ee5b5d371a63a132a87cf1649e798d5d10263c1ddeac56c660f3b153df2ed38`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `3e5aceeb764298904b6b2d6ac9915131f1afae4511714314895419419e24f8ab`.
- `trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `e64f06f811082b9e7c3598d2316fad3d7e05c01d7d66356d92a813f9d9821296`.
- `trigger_suppression_event_timing::clause_local_disjunction_registers_once_for_eligible_sibling`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `31804ba34aa24988f83c08dbca2ac2fb6dc5b536d3ba910ae6d02ba82433aa97`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `9920cb53e2deb12818cfc778980642309e5292df944c609cc76608c75e54d919`; archive `907dd223cf126cf83c990744627de95b972905d58b5877e9d9c1fd6a4823dce7`; executable `4e82d5da84367eed234ae8c1465faf0076f99f8335d21fe9fa66d62e7b151a47`.

- `full matrix`: exit 101; {'passed': 89, 'failed': 2, 'ignored': 20}; log SHA `c6a0013cedbdcd67ea9bbd3ec105db256871b37dce6e759f62f6b5b3fa10c0c4`.
- `trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `84678b42dab0513af49828085a8a2e2926dada27734b67470ea1ef1ef75042e8`.
- `trigger_suppression_event_timing::clause_local_disjunction_registers_once_for_eligible_sibling`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `0fd16e3f1efa79c67c10271b060d64471181b548b50de9c7776056a21dff2253`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `d9506dfc0f435a22d29c55c02e15d6afcba8c6008fdcf40210009d7dbb6b07e0`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `f84c2f1f5fc3d4dc89980ddede4f24ca562fe44cbba553b26c692fa884b5bc37`.
- `trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `e64f06f811082b9e7c3598d2316fad3d7e05c01d7d66356d92a813f9d9821296`.
- `trigger_suppression_event_timing::clause_local_disjunction_registers_once_for_eligible_sibling`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `0fd16e3f1efa79c67c10271b060d64471181b548b50de9c7776056a21dff2253`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving' (3444780) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)
  left: 0
 right: 2
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```


### self-arrival-exception

Production path `crates/engine/src/game/trigger_matchers.rs`, function(s) `zone_change_clause_matches`. Exact patch SHA `762f559474b24043847def241cf6204efff2159698ee988136f0470f0a846995`; mutant file SHA `5274d23a341b736494e8ee1b1aecd9b69720bdae829d7fad68ea89734d1f2ffa`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `abac6318673e6b245c413b14340cbac167766fa69e74bd5bd23c6ecd6acfbae7`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `67dcbe06821a394dd55b222d37f89471df4f286820be877188a965f3a6b5253e`.
- `trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `e64f06f811082b9e7c3598d2316fad3d7e05c01d7d66356d92a813f9d9821296`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `e4977a830e25383223f1298cc9873ec0e24642e18bea3f8e111c414124130bbf`; archive `460f79491ec7c899bffab2761352cc94f8f83eff80fd2f184e691a6e0b58d27a`; executable `c0b8d657fe01f62dd087fd6d47a9fecab4a308a26bc851d76fb6919af377b41d`.

- `full matrix`: exit 101; {'passed': 90, 'failed': 1, 'ignored': 20}; log SHA `603a830177ce9da292b3d8c27c3ca3147b40e596110d749cd9a40130385bd442`.
- `trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `43f7d968d4f17733e6c464df4386e3305e0a747521bbd696eccd491284bafbb4`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `ef44a5dd55fed9a2a53d61e2c68095ad3ee0a1b2b1d5955353950a64c22603ba`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `a3472cd07d844b1c990568b28d0d8e279da37789662e3c982eb999e913e0d8f2`.
- `trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `e64f06f811082b9e7c3598d2316fad3d7e05c01d7d66356d92a813f9d9821296`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::self_from_anywhere_exception_functions_in_destination_with_hush_surviving' (3449202) panicked at crates/engine/src/game/scenario.rs:3353:9:
assertion `left == right` failed: P0 life delta: expected 2, got 0 (before 20, final 20)
  left: 0
 right: 2
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```


### before-live-subject-authority

Production path `crates/engine/src/game/trigger_suppression.rs`, function(s) `outcomes_for_live_subject`. Exact patch SHA `cf221857e3f4c8adbe157ac9a6f254e7cbd50f33b0d4b282642f3f3e241fe57a`; mutant file SHA `a30ba72ce0ad476c295abf17a0def5f6142771c740fb299dee99a65bff5d437a`.

Outcome: intended assertion failure.

before: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `b3ca8c5420ad3ea491618863a41db28fc24b7d6207b98a15a94ca41c0ca59ba2`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `cc213026f037169eac800cb46cd25e012d585dfed35a6607675b239aabf39af7`.
- `trigger_suppression_event_timing::attachment_relative_suppression_binds_live_relation_before_departure`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `f0503775e0846d4ddf9e017228752056923ebda96e433e16e0e39b735ed5b6db`.
- `trigger_suppression_event_timing::enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `8de2ffbf9751d25a8d1edd3293bd3330ddf12bde9bbc2b75e6b8e2217ec11898`.

mutant: fresh Cargo compile plus preserved-mutant executable; source manifest `fc1bd0e677dc7e5e58b5c08e17f7c94efb19fd9256d8f1c4545f6ecc86a32875`; archive `b972858adad7ea4fa340c4dc71fc3306773c7e5fa95fe9605a2ed0af5fafe726`; executable `62a1ab0de6a20fed2b379a26bbe10ea98afebf061416b454acf6e17c391a5714`.

- `full matrix`: exit 101; {'passed': 89, 'failed': 2, 'ignored': 20}; log SHA `be7784ae612e45d6c531e3b6a60e5b2b7d3276c31bf37fdee24e1a00b2e01bb2`.
- `trigger_suppression_event_timing::attachment_relative_suppression_binds_live_relation_before_departure`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `aa5cc7a2e9965c169b25ef872bff6d36cf1e4d3f6b7fa1f46aaaed0bcd6c487c`.
- `trigger_suppression_event_timing::enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat`: exit 101; {'passed': 0, 'failed': 1, 'ignored': 0}; log SHA `7d46d3b0cc6408223e440f2ef57958a9f3cc95e90976a6cc86d7ee42d381c788`.

restored: reused preserved canonical executable after full source/runtime verification; source manifest `46ac753dff4229b2b2841a86b5334f2595c4b76bef4be8a4941dd76756f5f803`; archive `955b50427be6e9c9bad8dbdb437e05b7a66cead6474f31b1914dca76916e314c`; executable `6f5af1ecec2b609c3ba717b2778528971dea3917035bc50a0a8aa5c0354ee13e`.

- `trigger_suppression_event_timing`: exit 0; {'passed': 91, 'failed': 0, 'ignored': 20}; log SHA `8afb6dfca8f76c16c5237ea0cd68e2ea44d48e0715287f3da480c60074b3f273`.
- `trigger_suppression_event_timing::attachment_relative_suppression_binds_live_relation_before_departure`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `fdf789102aa958695ec1045ba81cca836ecf50428cc1228a51ab8c77e5fdbe47`.
- `trigger_suppression_event_timing::enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat`: exit 0; {'passed': 1, 'failed': 0, 'ignored': 0}; log SHA `8de2ffbf9751d25a8d1edd3293bd3330ddf12bde9bbc2b75e6b8e2217ec11898`.

Reached assertion contexts from independently run exact named filters:

```text
thread 'trigger_suppression_event_timing::attachment_relative_suppression_binds_live_relation_before_departure' (3452341) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:3751:9:
assertion `left == right` failed
  left: 1
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

```text
thread 'trigger_suppression_event_timing::enters_or_attacks_attack_and_combat_dependent_suppression_use_real_combat' (3452346) panicked at crates/engine/tests/integration/trigger_suppression_event_timing.rs:3716:13:
assertion `left == right` failed
  left: 1
 right: 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
FAILED

failures:
```

## Interpretation and remaining work

One preliminary direct-execution setup aborted with stack overflow because the launcher omitted the frozen repository RUST_MIN_STACK=16777216 that Cargo supplies. No mutant had run. Original command/log/exit and successful canonical Cargo91/20 build remain retained; a preliminary stack-corrected full matrix and eleven filters passed, then root required an actual Cargo runtime-identity probe. The recorded package cwd and allowlisted environment/library paths were applied and the full matrix plus eleven exact filters rerun before mutations. The probe itself freshly compiled canonical source and passed91/20; its preserved executable is the final canonical binding. This is setup evidence, not discrimination.

The first mutant completed designated assertion failures, then the supervisor stopped on a timestamp-bookkeeping check after restoring exact bytes. All2051 hashes were independently verified. The failed supervisor/script are retained; restoration was repeated with an explicit current-time os.utime newer than the mutant, followed by the same full matrix and named filters. Later rows use that robust timestamp check.

Exact named failures and matrix counts above are observations. The source/control map and pre-execution expectations are in source-review-notes.md. A panic stops its test: later loop cases, peer/counter/snapshot assertions and downstream payoff are not claimed executed. Full-matrix collateral failures are reported separately from designated exact semantic assertions. The ordinary-global-death-gate mutant independently passed clause_local_disjunction_registers_once_for_eligible_sibling while its destination-self-arrival test failed; those are separate executions, not inferred later loop cases. Independently passing named tests and the passing portion of the unchanged full matrix retain controls; no zero-match, data skip, compile failure or ignored desired diagnostic counts as a mutation proof.

Root holds batched-adapter and batched-global-death-gate. Source review identified that the ordinary guard can mask the current batched-adapter fixture and that the current self-arrival fixture is not batched. The complete v10 plan and clean review have been read; its reviewed mixed creature/noncreature batch/count and batched self-arrival fixtures are being implemented by the separate active executor. Applying that consolidated source requires a new canonical build and separate evidence report. This report does not claim those two mutations ran or that their discrimination is resolved.

All own-checkout candidate source bytes are restored. Nine-row mutation ownership is released; the two held rows remain assigned but unstarted pending root direction. No repair approval, production pin change, checker change or supported-behavior promotion is made.
