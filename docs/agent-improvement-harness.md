# MTG fidelity agent-improvement harness

## Implementation

The reusable local/offline foundation described here is implemented in
`crates/cogatrice-harness`. It provides content-addressed corpus
materialization, Scryfall identity/text/face/layout/legality validation,
17Lands soft-signal mining, exact-legal-action seed shards, authoritative event
traces, stable state hashes that include the RNG stream, serialized
checkpoints, checkpoint-suffix replay, hidden-information and zone invariants,
resume, bounded trace artifacts, normalized findings, prefix minimization, and
scoreboard aggregation. `scripts/run-harness-worker.sh` is the non-interactive
worker entry point.

Exact commands and artifact schemas are in
[the operations guide](agent-improvement-harness-operations.md). A production
campaign still requires immutable full Phase, MTGJSON, Scryfall, and 17Lands
snapshots supplied by the operator; the repository does not silently select or
download mutable “latest” data.

The current SOS production-fidelity campaign status and its prioritized engine
follow-ups are recorded in
[the campaign next-steps plan](mtg-fidelity-campaign-next-steps.md).

## Decision

Build a reproducible improvement harness around Phase rather than adding Magic
rules to Cogatrice. Phase remains the only executable rules authority. The
harness supplies it with a production-sized card corpus, exercises it with
deterministic and realistic workloads, minimizes failures, and gives coding
agents enough evidence to make narrowly scoped fixes with permanent regression
tests.

The four inputs have deliberately different roles:

- **Phase and MTGJSON** provide executable card definitions and the state
  transition system.
- **Scryfall bulk data** provides canonical Oracle identity, Oracle-text
  cross-checks, printings, and presentation metadata. It is not an executable
  rules engine.
- **Comprehensive Rules scenarios** and engine invariants provide hard
  correctness assertions.
- **17Lands public replay data** supplies realistic decks, card combinations,
  turn patterns, and anomaly signals. It is observational evidence, not a
  deterministic rules oracle.

This preserves the boundary in [the Phase port contract](phase-rules-port.md):
Cogatrice hosts games and exposes exact legal actions, while rules changes are
made and tested in Phase.

## Why 17Lands is a workload, not an oracle

The public 17Lands replay export contains useful per-turn observations such as
cards drawn and cast, attackers, blockers, damage, mana spent, and end-of-turn
summaries. It does not preserve all action ordering, targets, priority passes,
trigger ordering, modal choices, hidden state, or Arena's complete internal
state.

Consequently, the harness must not fail a Phase build merely because it cannot
literally reproduce a 17Lands row. It should use those rows to:

1. rank frequently exercised cards and mechanics;
2. construct realistic deck and matchup workloads;
3. identify implausible aggregate behavior;
4. generate candidates for a minimized, rules-backed regression scenario.

Only the minimized scenario, supported by a rules citation and discriminating
runtime assertions, becomes a hard conformance test.

## Architecture

```text
Phase + MTGJSON ----> executable card corpus --+
Scryfall bulk ------> identity/text validation +--> deterministic runner
CR scenarios -------> hard conformance tests ---+            |
17Lands ------------> realistic scenario mining +            v
                                                    failure minimizer
                                                            |
                                                            v
                                                  Sol patch + review
                                                            |
                                                            v
                                                 permanent regression
```

### Corpus builder

The corpus builder should:

- generate the full Phase card export instead of using the compact bundled
  fixture;
- resolve cards by Oracle ID while retaining printing and Arena IDs as aliases;
- ingest Scryfall through bulk snapshots, never one request per card;
- cross-check name, Oracle ID, Oracle text, faces, layout, and legalities without
  creating a second parsed-rules representation;
- fail deck import explicitly for missing or unsupported Phase faces;
- publish a content-addressed manifest containing the Phase commit, generator
  schema, MTGJSON version/hash, Scryfall snapshot/hash, 17Lands dataset/hash,
  and output hashes.

Every run must be reproducible from this manifest even after upstream data has
changed.

### Deterministic runner

The high-volume runner should call Phase directly through `phase-bridge` rather
than paying WebSocket and browser overhead. A smaller set of end-to-end tests
will continue to validate the server and wire protocol.

For each game, record:

- corpus manifest ID;
- seed and format configuration;
- ordered deck lists;
- every submitted exact `GameAction`;
- authoritative event stream;
- stable state hash after each transition;
- optional serialized checkpoints;
- terminal outcome or failure classification.

The same manifest, seed, decks, and action trace must produce the same state
hashes and outcome. Checkpointing and restoring in the middle of a trace must
also produce an identical suffix.

### Workload generators

The harness should support several complementary generators:

1. **Golden scenarios:** small, hand-authored setups proving specific rules and
   card interactions.
2. **Legal-action fuzzing:** policies choose only from Phase's exact legal
   actions and explore many seeds, cards, targets, and action sequences.
3. **Coverage-directed games:** deck and policy selection favors mechanics,
   parser branches, and cards that have received little runtime exercise.
4. **17Lands-derived games:** reconstruct available decks and matchup features,
   then simulate plausible games rather than pretending to reproduce Arena's
   missing decisions.
5. **Metamorphic cases:** replay after serialization, repeat from the same
   seed, exchange seats where symmetry applies, and compare equivalent action
   paths where the rules require equivalent results.

### Hard gates and soft signals

| Class | Examples | Result |
| --- | --- | --- |
| Hard conformance | Golden rules scenarios, exact legal-action enforcement, deterministic replay, serialization round-trip, hidden-information checks, object/zone invariants, no panic or deadlock | Pass or fail the run |
| Coverage | Card import support, parser gaps, mechanics reached, action variants reached | Rank work and enforce explicitly chosen thresholds |
| Soft evidence | 17Lands game length, cast/attack/damage patterns, card interaction frequency, simulated-versus-observed distributions | Create ranked investigations; never fail correctness alone |

Parser coverage is not equivalent to semantic correctness. Cards reported as
supported must still receive runtime scenarios that would fail if targets,
conditions, quantities, durations, triggers, or replacements were interpreted
incorrectly.

## Agent improvement loop

Each improvement attempt follows the same closed loop:

1. Select a failure or high-value coverage gap.
2. Minimize it to the smallest corpus, decks, seed, state, and action trace that
   still demonstrates the problem.
3. Classify it as a Cogatrice integration defect, a Phase defect, a data defect,
   or an inconclusive observational anomaly.
4. For a Phase defect, locate the relevant Comprehensive Rules sections and at
   least two analogous Phase implementations.
5. Add a discriminating runtime regression test that fails before the fix.
6. Implement the smallest reusable fix at the owning Phase seam.
7. Run focused tests, Phase's coverage and semantic audits, the accumulated
   regression suite, and a randomized shard.
8. Have an independent reviewer examine the diff and test discrimination.
9. Accept the change only if all hard gates pass and no unrelated coverage or
   behavior regresses.

Agents must not implement card rules in `phase-bridge`, the server, policies, or
the browser. Integration defects can be fixed in Coworld; rules and parser
defects should be prepared as Phase commits or upstream-ready pull requests.

## Sol-in-the-cloud execution model

The harness must be designed for ephemeral, non-interactive cloud workers from
the beginning.

### Worker contract

Each worker receives only:

- a repository commit;
- a content-addressed corpus manifest;
- a shard specification;
- a time or action budget;
- an output URI and run ID.

Each worker produces bounded artifacts:

- `result.json` with counts, timings, and terminal status;
- compressed JSONL findings;
- minimized traces for novel hard failures;
- structured logs with secrets removed;
- an optional patch bundle for an improvement attempt.

Workers must not depend on another worker's filesystem, local Cargo cache, or
mutable branch. Communication happens through manifests and uploaded artifacts.

### Cloud requirements

- Setup is a single non-interactive command and is safe to retry.
- All external inputs are downloaded from immutable or hash-verified locations.
- Large Scryfall, MTGJSON, Phase export, and 17Lands artifacts are cached by
  content hash in shared object storage.
- Fuzzing is split into deterministic seed ranges so shards can run in parallel,
  retry independently, and avoid duplicate work.
- Every shard checkpoints progress and can resume after eviction or timeout.
- A coordinator deduplicates findings by normalized failure signature before
  spending agent compute on minimization or patches.
- CPU, memory, disk, wall-clock, action-count, log-size, and artifact-size
  limits are explicit.
- Network access is required only during corpus materialization and artifact
  upload. Test execution itself can run offline.
- Credentials are injected at runtime, never written to traces, patches, or
  replay artifacts.
- A worker that cannot prove its input hashes or complete required verification
  reports `inconclusive`; it does not publish a successful fix.

Rust compilation is likely to dominate cold-start cost. Cloud images should pin
the Rust toolchain and prebuild unchanged dependencies, while correctness must
not depend on the cache being present. Generated card data should be a separate
immutable artifact so ordinary runner shards do not regenerate it.

### Suggested roles

Independent Sol workers can specialize without sharing conversational state:

- **corpus worker:** materializes and validates an immutable card/data snapshot;
- **runner workers:** execute deterministic seed shards and emit findings;
- **scenario miner:** turns 17Lands observations into ranked workloads;
- **minimizer:** reduces one hard failure to a portable test case;
- **implementer:** makes one narrowly scoped Phase or integration change;
- **reviewer:** receives the diff, regression, and relevant contracts in a fresh
  context and checks correctness and test discrimination;
- **coordinator:** deduplicates results, applies hard gates, and publishes the
  scoreboard.

No worker should both invent a semantic expectation and be the only reviewer of
the patch that satisfies it.

## First one-day campaign

Use one recent Limited set with strong Phase coverage and available 17Lands
data, rather than attempting all of Magic. At the time this plan was written,
SOS was a useful candidate: the published Phase coverage report listed 300 of
307 cards as supported, and 17Lands published current Limited replay datasets.
The campaign configuration should select the set dynamically so this historical
choice does not become a permanent default.

### Hours 0-4: baseline and corpus

- Trial the newest compatible Phase release against `phase-bridge`.
- Generate, validate, and publish the full content-addressed card export.
- Materialize Scryfall and 17Lands snapshots with hashes.
- Record baseline import, coverage, determinism, and existing-test results.

### Hours 4-8: runner and reporting

- Implement the direct deterministic runner and action-trace format.
- Add checkpoint/restore and state-hash verification.
- Add shardable seed ranges, failure signatures, and resumable output.
- Establish the hard-gate and soft-signal report schemas.

### Hours 8-20: parallel improvement loops

- Exercise unsupported cards and high-impact parser gaps.
- Audit frequently played supported cards for silent semantic errors.
- Run randomized legal-action games and minimize novel failures.
- Produce small Phase fixes with discriminating regressions and independent
  review.

### Hours 20-24: freeze and evaluate

- Rerun all accumulated regressions from a clean environment.
- Run a larger held-out seed shard that implementers did not see.
- Regenerate the coverage and semantic-audit reports.
- Publish the corpus manifest, scoreboard, unresolved findings, accepted
  patches, and exact reproduction commands.

## Proposed interface

The exact binary and flags can evolve, but the workflow should converge on a
single resumable command such as:

```sh
cargo run -p cogatrice-harness -- improve \
  --set SOS \
  --phase-rev <commit> \
  --manifest-uri <immutable-manifest-uri> \
  --seed-start 0 \
  --seed-count 100000 \
  --checkpoint-uri <run-output-uri>
```

Separate commands should materialize a corpus, run a shard, minimize a finding,
replay a trace, and aggregate a scoreboard. Every command must accept local
paths as well as object-storage URIs so the same workflow runs on a laptop and
in the cloud.

## Day-one success criteria

The first campaign is successful when it leaves behind a reusable system, not
merely a collection of patches:

- one immutable, reproducible Limited-set corpus;
- complete import results with explicit unsupported-card errors;
- deterministic replay and checkpoint round-trip gates;
- shardable cloud execution with retry and resume behavior;
- tens of thousands of completed randomized games without an unclassified
  panic, invalid action, or deadlock;
- minimized regression fixtures for every accepted hard failure;
- ranked 17Lands-derived investigations clearly labeled as soft evidence;
- before-and-after coverage and conformance metrics;
- a small number of independently reviewed, high-confidence fixes.

A reasonable first-day expectation is the durable harness plus several
minimized defects and approximately three to ten safe fixes. “All Magic cards
work” is not a credible one-day target.

## Risks and controls

- **Treating observations as rules:** keep 17Lands comparisons soft until a
  rules-backed minimal test exists.
- **Silent parser errors:** require runtime discrimination for cards already
  marked supported; do not rely only on parser coverage.
- **Data drift:** pin every input by hash and record it in every trace.
- **Upstream churn:** test a Phase upgrade independently and retain the prior
  pin until compatibility and replay migrations pass.
- **Agent overfitting:** reserve held-out seeds and scenarios for the final
  gate.
- **Duplicate cloud work:** normalize and deduplicate failure signatures before
  invoking minimizers or implementers.
- **Runaway cost:** enforce per-role budgets and stop exploring a signature once
  it has a stable minimal reproducer.
- **Rules leakage into Coworld:** reject changes that reproduce Phase legality
  or card semantics outside Phase.

## External data guidance

- [Scryfall API guidance](https://scryfall.com/docs/faqs/i-m-having-trouble-accessing-the-scryfall-api-or-i-m-blocked-17)
  recommends bulk downloads for large-scale data use.
- [17Lands public datasets](https://www.17lands.com/public_datasets) documents
  the available game and replay observations and their licensing.
- [Phase](https://github.com/phase-rs/phase) supplies the engine, card-data
  generation, coverage reporting, semantic audits, and upstream contribution
  workflow that this harness should reuse rather than duplicate.
