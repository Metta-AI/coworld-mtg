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

## A regression required a stronger cost boundary

The [v7 component stop](v7-component-stop/README.md) preserves an introduced
regression found by the expanded tests. Deferred payment merged separate
sacrifice costs, which gave the second cost an earlier event snapshot. The
repair was sent back through planning and review. This was not treated as an
existing-engine compatibility exception or as acceptance of the candidate.

The [frozen v8 plan](hushbringer-plan-v8.md) adds explicit cost-component
provenance while retaining the earlier obligations. The
[partial implementation handoff](v7-partial/README.md) records the exact source,
passing checks, unresolved failures and remaining gates before that revision.
The plan is pending independent review at this checkpoint.

The [full v8 review](hushbringer-plan-review-v8.md) returned three blocking
findings: preserve concession during legacy recovery, establish exact
production discrimination for the resolver wrapper, and resolve the
[four additional LKI/controller failures](v7-broad-suite/README.md) while
preserving their assertions. The [v8 manifest](v8-plan-manifest.json) binds
the eighth full review and the supporting evidence. A fresh v9 planner was
dispatched; implementation remains unaccepted.

An [isolated original-engine cost run](v7-component-isolated-runtime/README.md)
confirmed the earlier deferred-cost observations using a fresh baseline
compilation and the exact retained test overlay. This supplements the
historical shared-target evidence without relabeling it.

The [frozen v9 plan](hushbringer-plan-v9.md) addresses those findings with
explicit global-action exemptions, a concrete same-object replacement and
sacrifice path for the resolver boundary, and bounded LKI/controller fixture
changes that preserve the original assertions. Its
[freeze receipt](hushbringer-plan-v9-freeze-receipt.json) records source
preservation. A fresh full v9 review is pending at this checkpoint.

The [fresh full v9 review](hushbringer-plan-review-v9.md) was clean, the
ninth completed full plan-review round. The
[v9 manifest](v9-plan-manifest.json) binds the plan, review and supporting
evidence. A fresh executor was dispatched with exclusive source ownership
and a separate mutation checkout. Runtime proof and independent implementation
review remain required before acceptance.
