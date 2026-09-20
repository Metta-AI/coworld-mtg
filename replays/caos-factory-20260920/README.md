# A complete improvement epoch executed by CAOS

This is a real 17Lands discovery run with a real model contributor, followed by a
separate, explicitly synthetic integration test of the candidate path.

The real contributor retained **no change**. Its final proposal says the available
evidence does not justify an edit. That is an abstention by this contributor,
not a finding that the program cannot be improved.

| Native outcome | Games |
| --- | ---: |
| Matched the supported projection | 8 |
| Unsupported mulligan reconstruction | 9 |
| External deadline; progress unreported | 3 |

All eight matches have zero fully covered milestones. The workload is the retained
first 20 SOS games, previously inspected, with a two-turn horizon per player.
The original row index remains the native seed. These are not unseen holdouts.

## Inspect the execution

Serve this directory and open [index.html](index.html). The viewer starts at game
18, which has a retained 53-action path and eight partial milestone matches.
Choose a checkpoint to compare source fields with their engine projections.
The state slider and optional Scryfall card art show the reconstructed board.
Hidden opponent cards and library order include explicit assumptions.

The DAG is derived from the linked receipt objects in [replay.json](replay.json).
Only executed stages appear. The final real run stopped before implementation;
it did not compile or evaluate a model-proposed repair.

- [run.json](run.json) identifies the input revision, runtime, worker image,
  original request, terminal commit, build and native requests.
- [status.json](status.json) retains CAOS's execution-tree view.
- [migration-attempts.json](migration-attempts.json) preserves earlier decisions,
  model responses and their identities, with separately labeled operator notes.
- [integration-test.json](integration-test.json) records the complete candidate
  branch test, including its comparison and both reviews.

The immutable terminal commit is
`71af54aec8d387524dad2884cf055e5a9a53cc7c`;
the original root request is
`58410bd942e3b7d298a15f6c5938e74b2a711716`.
The complete private object closure is retained on the EC2 runtime. This public
export omits the corpus, binaries, source snapshots, prompts and credentials.

## What the candidate-path test establishes

The deterministic contributor in
[noop_contributor.py](../../caos-factory/tests/noop_contributor.py) proposes a
comment-only source edit and returns synthetic approvals. It is not a model
repair, and its proposal is not an interesting discovered Magic case.

CAOS applied that edit, compiled the candidate, passed the 11 native fitting
tests, fit all 20 original games, compared them, ran the final review and
returned a rejection. There were zero improved cases. All completed cases had
the same outcomes and node counts; the same three deadlines remained unresolved.

This verifies that the complete execution path runs and that contributor
approval cannot override a failed comparison. Boundary tests separately reject
no improvement even when there are no unresolved executions.

Two integration failures found along the way also have retained origins:
read-only copied source blobs prevented edits, and an unmaterialized nested
source object prevented candidate fitting. The migration notes identify the
failed requests and resulting factory changes.

## Limits relevant to interpreting this run

The acceptance policy is deliberately strict: an unresolved candidate execution
blocks promotion even when the corresponding baseline also timed out. Consequently,
a repair elsewhere in this cohort cannot pass until those unresolved executions
are addressed. We did not relax that policy to manufacture an accepted result.

The contributor receives bounded examples and source files; it cannot run its
own additional diagnosis experiments during planning in this first integration.
Its raw reasoning is fallible. For example, reconstructing mulligans is allowed
within the edit scope if justified; the final model's assertion that any such
expansion would violate policy is not itself a policy rule.

An independently frozen native witness verifier is not implemented. Candidate
reports, regression checks and model reviews do not amount to a proof of Magic
rules correctness. Cached observations reused across migration attempts are not
new independent trials.

Source data: [17Lands public datasets](https://www.17lands.com/public_datasets),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Exact complete CSV rows were retained; manifests, case labels and execution
artifacts were derived. 17Lands does not endorse this work. Card art is loaded
optionally from Scryfall; Magic card artwork belongs to its respective owners.
