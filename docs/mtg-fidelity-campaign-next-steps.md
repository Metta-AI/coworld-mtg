# MTG production-fidelity campaign next steps

## Current validated state

The immutable SOS campaign remains anchored to manifest
`026d9f9648f61cca935f62e2a181bfd01e5ad94a407a4e9a8ee79e00a78f40c9`.
Do not rewrite its corpus, decks, prior shards, hashes, or rules boundary.

The local Phase improvement chain validated by the campaign is:

1. `fe60029b2` — flashback nonmana cost payability;
2. `aacc45329` — checkpoint replay and mana-payment stabilization;
3. `c3f288ebd` — restriction-, pin-, and demand-consistent hybrid payment with
   transactional mana-pool failure handling;
4. `a0f0e759a` — deterministic blocker prompt ordering across all producers.

The chain is published on `nishu-builder/phase`. Follow-up owner fixes for
viewer-scoped simultaneous decisions, deterministic batched-trigger
serialization, mandatory additional-cost castability, and Arena priority
controls are merged into that fork's `main` at
`2dec6c88915db4697706234a7ba2fcedd97b1689`. Coworld pins that exact revision;
upstream synchronization must preserve a content-addressed revision rather
than following a mutable branch.

The post-review production shard `shard-008-reviewed-phase-payment-fixes`
completed four seeds to the 500-action budget: four attempted, four
action-budget exhausted, zero hard failures, and 2,000 actions. Trace replay,
checkpoint suffix restoration, hidden-information checks, zone invariants, and
finding aggregation were clean. That historical shard used the reviewed local
Phase patch overlay while retaining the sealed corpus rules boundary at
`f6fd1fca5c581bcd127d5b18742623e1298ae3c7`.

The production dependency now moves the rules boundary to `2dec6c889`. The
existing harness correctly rejects the old manifest against that binary. Do
not relabel or edit the old corpus to bypass the guard. Before claiming a
production shard for the fork-main pin, record a new immutable corpus and
manifest under a new campaign identity, then run a newly named shard and
scoreboard against that exact manifest.

## Priority 1: transactional generic tap costs

The next Phase change should make generic `AbilityCost::TapCreatures` use one
eligibility and transaction authority across spell costs, ordinary activated
abilities, and mana abilities.

Required properties:

- exclude objects rejected by `restrictions::object_cant_tap` from payability
  and prompt candidates;
- retain the exact cost/filter provenance through `WaitingFor::PayCost` and
  revalidate it when the selection is submitted;
- reject duplicate, removed, tapped, controller-changed, filter-changed, or
  newly prohibited selections before committing real state;
- execute helper taps and any source `{T}` continuation on a scratch
  `GameState` and temporary event buffer, committing only if the entire
  sequential payment succeeds;
- fail multiple simultaneously payable `TapCreatures` legs before mutation
  until a complete allocation authority exists;
- leave Crew, Saddle, and Station with their mechanic-specific authorities.

The discriminating regressions should include exact Group Project flashback, a
nonmana Lathril-shaped `{T}` plus TapCreatures activation, and a selected-choice
mana ability. Hostile cases must prove state and event atomicity when tapping an
earlier object activates a conditional prohibition on a later object.

## Priority 2: whole composite-cost affordability

`AbilityCost::Composite` currently checks components independently against an
unchanged state. That can double-count life or the same object and can expose a
cost that fails after a prior component has already mutated state.

The owning fix needs an existence search, not greedy reservation. CR 601.2h
allows cost components to be paid in any order, so overlapping filters must be
evaluated across alternative allocations. For example, “sacrifice a creature,
sacrifice an Elf” is payable with an Elf and a Bear only when the broad leg uses
the Bear.

The design should:

- bind the complete selected cost, targets, X value, modes, and elected optional
  costs at the casting or activation payment boundary;
- explore `Composite` allocations and `OneOf` alternatives on independent
  scratch states;
- consume scalar resources and interactive object resources in the probe;
- exclude already-paid continuation components and unelected optional costs;
- use the same leaf authorities as live payment;
- commit no state or events until the selected payment path succeeds.

Minimum regressions are two `PayLife(3)` legs at four and six life, overlapping
sacrifice/filter allocations in both component orders, duplicate-object reuse,
and equivalent discard, exile, and tap resource cases.

## Campaign continuation

First establish a new immutable corpus whose manifest records Phase
`2dec6c88915db4697706234a7ba2fcedd97b1689`; preserve the existing SOS corpus as
historical evidence. Record the new manifest ID and all input hashes before
running any shard.

After each owning Phase fix:

1. run formatting, authority checks, focused regressions, workspace clippy, and
   the full proptest-enabled engine suite through `cargo nextest`;
2. run Coworld `cogatrice-harness` tests against its pinned Phase fork
   revision;
3. rebuild the release harness against the candidate Phase checkout;
4. write a uniquely named shard and scoreboard without overwriting prior
   evidence;
5. obtain an independent correctness and test-discrimination review;
6. run held-out seed ranges only after the focused production shard remains
   replay- and checkpoint-clean.

Do not globally sort serialized JSON arrays. When a new nondeterministic set is
observed, add deterministic serde at its owning Phase field or type boundary and
cover checkpoint round-trip behavior. Create a new immutable manifest only when
the Phase export or another corpus input changes; never edit the existing
manifest in place.
