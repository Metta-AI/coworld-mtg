# Hushbringer process history

Case ID: `01edd604679d89888ad9bb3bd13ca1c531fbbdd1c65f98341e7ce2a5a57d09aa`.

This directory retains the plans, rejected proposals, reviews and baseline
runtime proof behind the case. [The manifest](planning-manifest.json) records
the hashes of the completed planning-stage artifacts. These records explain
how the repair obligation evolved; they do not establish acceptance.

There were six full plan reviews. Reviews of v4 and v6 were clean. The first
executor stopped before editing v4 because the proposed grouping did not yet
specify how a leaf zone move could know whether it belonged to a simultaneous
event. That stop led to another plan and review cycle. The
[retained stop report](hushbringer-implementation-stop-v4.md) records the
reason rather than replacing it with the eventual successful path.

The [baseline proof](baseline-proof/proof.json) records a test-only overlay on
the original engine revision. The no-Hushbringer control passed; both
battlefield insertion orders failed the reached zero-Spirit assertion with
one Spirit. The production source was unchanged in that experiment.

The authored case, frozen expectation, campaign receipts, source builds,
independent approval and generated note belong to the acceptance protocol
described in [verifiable cases](../../../docs/verifiable-cases.md).
Implementation and acceptance were still pending when this planning snapshot
was written.

## Implementation exposed three baseline test assumptions

The [v6 fixture stop](v6-fixture-stop/hushbringer-implementation-stop-v6-fixtures.md)
records three failures that also occurred on the original engine: a dropped
post-payment continuation, a cast-created regeneration shield that did not
preserve the expected creature, and duplicate token creation after a paused
zone change resumed. The Hushbringer primary tests had passed on the repair.

These are separate behavior claims. The [v7 plan](hushbringer-plan-v7.md)
proposes preserving the desired behavior for those old defects as explicit
diagnostics, while using reaching fixtures and narrowly labeled compatibility
checks to test this repair. The executable acceptance case and its zero-Spirit
expectation remain unchanged.

The [stop manifest](v6-fixture-stop/manifest.json) retains the exact baseline
overlay and runtime logs. It also discloses a retention gap: the earlier active
test-source hashes were recorded, but immutable copies of those exact active
files were not saved. Later snapshots must not be presented as those files.

The [full v7 review](hushbringer-plan-review-v7.md) was clean. This was the
seventh plan-review round. It preserves all pending runtime, isolated-revert
and frozen-worker gates. The [partial test handoff](v6-tests-partial/hushbringer-implementation-tests-v6.md)
and [immutable receipt](v6-tests-partial/hushbringer-tests-v6-final-partial-receipt.json)
record what had and had not run before the fresh v7 executor took over.
The [v7 checkpoint manifest](v7-plan-manifest.json) binds these artifacts.

## The build workflow also changed

The [build-isolation record](build-isolation/README.md) attributes a worker
builder correction to this investigation. Cross-checkout Cargo artifact reuse
caused an active Phase test compile to see an older engine type. Builds now
use separate output directories. Both comparison workers must be rebuilt
with the same corrected builder while the checker and case remain fixed.
