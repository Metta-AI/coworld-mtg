# Hushbringer suppresses a death trigger even while dying

Generated from [attribution.json](attribution.json). Edit the source case or review in a new experiment; this note is generated.

Accepted repair for case `01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa`.

Origin: an authored scenario.

Cards: Hushbringer, Doomed Traveler, Wrath of God. The setup contains 3 cards and 1 operations.

## Observed result

Each worker ran twice. Reachability guards passed before judging these assertions.

| Assertion | Expected | Baseline | Candidate |
| --- | --- | --- | --- |
| simultaneous-death-suppressed | 0 | 1 | 0 |

## Basis for the expectation

- Ruling 2019-10-04; CR 603.10 — A creature dying simultaneously with Hushbringer does not cause death abilities to trigger, including when Hushbringer also dies.. Source: <https://scryfall.com/card/eld/18/hushbringer>

## Repair and review

Repository: <https://github.com/nishu-builder/phase.git>. Commit `fa0ebfe88db224ebd32624bb96ef033d338c2d8c` from base `2dec6c88915db4697706234a7ba2fcedd97b1689`. [Recorded patch](repair.patch), SHA-256 `f35967418e623234a47a9dd4499a5516e05cd4fc16d898953e60465d1a87fc60`.

Reviewer: /root/hushbringer_full_review_final. I independently reviewed the full 30-path engine patch and all affected source/tests against the approved 868-line plan, actual repository CR, constructor/consumer inventories and mutation/native-path evidence. Maintainer-Simulation and CR gates pass with no outstanding findings; full implementation report SHA256 be29698badceaa2add9f90213642feb4e91d6682535b79a97f61f712d5d6a7a2. The repair captures event-time functioning trigger-suppression authority and source last-known information through scoped immediate, deferred-cost and native choice/SBA paths; it is not a card-name condition. I then verified the newly compiled clean Phase commit fa0ebfe88db224ebd32624bb96ef033d338c2d8c against all2051 reviewed live source hashes (manifest ee906941362b78f3ad170fc733a4ca34ee28fcd571f7fafe14f3c900e7204847); all2050 files captured by the unchanged builder match. Candidate worker SHA256 f5b0de9436da31a00aaf7a1d28b92bd4288bd47077412970e0c3585f0cce1784 uses the same39 harness sources, compiler, builder and relevant build settings as original e4 baseline. All206 compiler artifacts were newly built; the resolved lock differs only in the expected engine source. Build detail audit SHA256 7f407c9660e797a0572453f2cd7a9c6b19ebe0f0a0bfe8ed5839be7c04e52f05. Using the unchanged f9 checker I independently verified all20 retained bundles, their exact case/corpus/worker/checker/evidence bindings and all40 repeated executions, and separately recalculated every reachability guard and observed assertion. Baseline creates1 Spirit while both Hushbringer and Doomed Traveler die; candidate creates0. All7 frozen regression and2 separately selected holdout cases satisfy with the same candidate worker/corpus/checker. Verification detail SHA256 c74ede9415f699952e814132cc4798e9cb2f98b58b0252bb79753a6585ec905a. Six additional fresh final-worker executions confirm both object orders produce0 and the no-Hush control produces1, with exact repeat equality and graveyard guards. This approval is limited to this exact plan and these bound receipt/build/evidence identities. Prior full-engine test evidence retains the implementation review's exact comment-only predecessor lineage; this worker build is fresh but is not a rerun of those full suites. The20 ignored desired diagnostics and all10 approved engine limitations remain excluded, as do parser/data coverage promotion, throughput and universal rules correctness. No acceptance command has been executed by this reviewer.

## Accumulated regression evidence

| Role | Case | Result |
| --- | --- | --- |
| Regression | Lightning Helix gains life when its target remains legal (`29de70628e65267abb50880e52218b236f0cd01bf16c8c09cf1618adff544967`) | Satisfied |
| Regression | Lightning Helix loses its target and its life gain (`3cb0040d03c76a86eb4bb6f4b957ff2c7c10b6639d6e108347889cad87d040f9`) | Satisfied |
| Regression | Swords to Plowshares remembers counters after exile (`4c10da113ad94461054f7c391fad097ca7f6c0a21b603b7cc93d03ec5199da9d`) | Satisfied |
| Regression | Young Pyromancer keeps the token from a countered spell (`b01d18fdb026136222e89758643dd5a9ddb513ce09192cba26394a064e44a366`) | Satisfied |
| Regression | Doomed Traveler creates a Spirit without Hushbringer (`7f9527c7d6ff1ac3b478c581100180cc844973ed9f61bdd3a305daf8d7244c8b`) | Satisfied |
| Regression | Rancor cannot return from a battlefield it never reached (`816630598b10a1f0acb9bdaf710f4ec37d1668d72796156972db9c78173f10bc`) | Satisfied |
| Regression | Rancor returns after its enchanted creature dies (`19e61869d1fd6ee075becbfff8ab5233132c3a6fe33134d0aa27437c9d86616a`) | Satisfied |
| Held-out case | Removing Hushbringer before the deaths restores the trigger (`7e24ad79064c7144e7d947cdc71e59085be84f468efdbee8172e526e02f2b6db`) | Satisfied |
| Held-out case | Hushbringer leaves Stonecoil Serpent entry counters intact (`454d3e00b1bf825aa1f19f6501c9d096de30dff426bdcbe2b95978518e9f3512`) | Satisfied |

## Stable attribution

- Case: `01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa`
- Acceptance: `66ef2e974d5dfb7f59f93f98405dcd6d9dd7b17fb9fab9df0fc3491dfdf6aba4`
- Attribution: `79e6ca745b4b25a2e154691f316210542c927cbbbb14328e37f406c99236bf28`
- Baseline worker: `e4e8cb9d6024592745a0da533bcd86001c8115184a1ddcf0163c1f3f04494d98`
- Candidate worker: `f5b0de9436da31a00aaf7a1d28b92bd4288bd47077412970e0c3585f0cce1784`
- Checker: `f9faf4b72b5f3df0342290a0ee30ac3207c799c6032ec2679090fc37bc656dd1`
- Corpus: `8b7151e61d99082ba22c39ee5dc56e798e339e44387af5834f6b3c1982dfbb3c`

This records evidence for the stated scenarios. It does not establish correctness outside them.
