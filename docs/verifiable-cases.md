# Verifiable improvement cases

A case connects a rule claim to an executable scenario. The coordinator freezes
that claim, runs a worker twice, and judges observations without sending the
expected answer to the worker. A repair earns an acceptance receipt only after
it fixes the same case with the same corpus and checker, passes the selected
regressions and held-out cases, and receives independent review.

This is an executable repair protocol. An agent or operator still proposes the
case, interprets its sources, implements a patch, and supplies the review. The
legacy `improve` command still runs a seeded shard; it is not an autonomous
repair agent. Recorded play remains a source of hypotheses and workloads.

## Boundaries

`crates/loop-contract` owns the Rust types, validation, checker and acceptance
rules. It depends on no engine, agent, filesystem or network. Serde and Schemars
produce strict JSON Schemas from those types. The same boundary registry
produces [the architecture diagram](contracts/architecture.mmd) and
[the message diagram](contracts/message-flow.mmd). These describe logical roles;
only the worker is required to be a separate process.

| Artifact | Producer → consumer | Meaning |
| --- | --- | --- |
| `CaseSpec` | Author → coordinator | Setup, operations, reachability guards, expected observations and their justification |
| `ExecutionRequest` | Coordinator → worker | Scenario and exact corpus identity; no assertions |
| `ExecutionEvidence` | Worker → coordinator | Observations, operation checkpoints and executable fingerprint |
| `EvaluationReceipt` | Coordinator → evidence store | Input/evidence hashes, repeatability and a typed verdict |
| `ReductionReceipt` | Reducer → evidence store | Preserved predicate, original/reduced identities and search bounds |
| `AcceptancePlan` | Operator → coordinator | Fixed target, regression cases and separately selected held-out cases |
| `ReviewRecord` | Reviewer → coordinator | Approval/rejection bound to the plan and before/after receipts |
| `AcceptanceDecision` | Coordinator → evidence store | Accepted experiment or explicit rejection reasons |

JSON fits these inspectable, local process boundaries. Protobuf would add a
second schema language and compiler without a current RPC consumer. The wire
format is versioned and can acquire a different transport later. Generate or
check the schemas and diagrams with:

```sh
scripts/cargo.sh run --locked -p coworld-mtg-harness -- case contracts --output-dir docs/contracts
scripts/cargo.sh run --locked -p coworld-mtg-harness -- case contracts --output-dir docs/contracts --check
```

The second command is part of `scripts/check.sh`. Unknown JSON fields and enum
variants fail decoding; semantic validation also checks labels, references,
nonempty expectations and reachability guards.

## Run a case or campaign

The focused [card corpus](../cases/corpus/corpus.json) is extracted from a Phase
export. [Its source record](../cases/corpus/sources.json) pins the full export
and Scryfall snapshots, checks Oracle IDs and text, and links each card. This
checks the input's identity; it does not certify the rules engine's behavior.
The full private runtime corpus is separate.

```sh
scripts/cargo.sh build --locked -p coworld-mtg-harness
target/debug/coworld-mtg-harness case evaluate \
  --case cases/cards/helix-resolves.json --corpus cases/corpus/corpus.json \
  --output-dir tmp/cases/helix-001
target/debug/coworld-mtg-harness case campaign \
  --case-dir cases/cards --corpus cases/corpus/corpus.json \
  --output-dir tmp/cases/campaign-001
```

Every output directory must be new. A failed or inconclusive campaign exits
nonzero and retains its results. Each bundle includes the normalized case,
request, exact corpus bytes, both execution results, worker logs and receipt.
A scenario checkpoint hashes Phase state, including the RNG, after each
scenario operation. It is not a complete trace of the driver's individual
priority and choice actions. The older shard runner retains individual actions.

| Verdict | Interpretation |
| --- | --- |
| `satisfied` | All guards and predicates passed on repeatable execution |
| `violated` | Guards passed and the named expected predicates failed reproducibly |
| `inconclusive` | The experiment cannot judge the rule claim |

Inconclusive reasons distinguish missing card identity, invalid setup, driver
failure, worker timeout/failure, malformed evidence, diverging repeats,
unreached guards and missing observations. A `--timeout-seconds` budget applies
to each worker process. It is a wall-clock limit, not an OS memory or disk quota.

The adapter builds a small initial position and uses Phase's scenario driver
for casts, priority and resolution. It observes zones, life, counters, prepared
state, ordinary `CastSpell` offers, and counts of named objects. `owner` means
owner, including on the battlefield; it is not a controller assertion. This
DSL deliberately has no arbitrary executable predicates or card-specific repair
logic. It is not yet a general importer for recorded games or every game action.

## Reduce an established failure

```sh
target/debug/coworld-mtg-harness case reduce \
  --case cases/cards/hushbringer-simultaneous-death.json \
  --corpus cases/corpus/corpus.json \
  --predicate simultaneous-death-suppressed --budget 32 \
  --output-dir tmp/cases/hush-reduced-001
```

The reducer attempts individual card and operation deletions. It keeps only
valid candidates that reproduce the same violated assertion set twice and
still satisfy every guard. Removing the cast or the creature whose death is
being tested cannot silently become a smaller reproducer. It reports a fixed
point under those deletions or an exhausted budget; neither means globally
minimal. Original and attempted bundles remain available.

Legacy `minimize` is a separate bounded prefix reducer. It distinguishes
reproducing a recorded hard failure from a clean replay, preserves the same
replay assessment, and adjusts action-budget terminals when truncating. Full
shard failure traces now live in `failures/`, not a directory claiming they
have already been minimized.

## Freeze, compare and accept a repair

Preserve a coordinator before building candidates. The checker fingerprint is
the complete coordinator executable, including its compiled dependencies. Use
that same executable to judge both workers and verify or accept the results.
Rebuilding a coordinator is a new checker identity, even if its source looks
unchanged.

```sh
python3 scripts/build-case-worker.py --output-dir tmp/cases/baseline-build
# Capture an experimental checkout without changing the production pin:
python3 scripts/build-case-worker.py --phase-checkout /path/to/phase-checkout \
  --output-dir tmp/cases/candidate-build
```

The builder copies the harness workspace, records source file hashes, the
resolved lockfile and the executable digest, and records an optional Phase
checkout's commit, patch from the baseline, dirty diff and source files. The builder checks its record against the Rust `BuildRecord` contract before reporting success. A local override changes only the copied
workspace. The worker's `declared_phase_revision` is the workspace declaration;
the executable fingerprint and build record identify an override's actual
source. Source changes during a build prevent it from being certified.

Before repair, run `case plan --case TARGET --regression CASE --holdout CASE
--output PLAN`. Both gate options may repeat. Keep that plan fixed. It requires
disjoint target, regression and held-out identities. Held-out means separately
selected for evaluation here; it is not a claim of secret data or statistical
independence.

Evaluate with `BASELINE_COORDINATOR case evaluate --worker WORKER ...` or
`case campaign --worker WORKER ...`. Then use that coordinator's `case verify
--receipt BUNDLE/receipt.json` to recompute a completed receipt from its bundle.
Verification may succeed on an accurately recorded violation. That establishes
the evidence, not that the engine passed the case.

A fresh reviewer checks the expectation, patch and discriminating tests, then
writes a `ReviewRecord` using the generated schema. Its IDs are SHA-256 hashes
of compact, sorted-key JSON after typed normalization; array order is retained.
The final command is:

```sh
BASELINE_COORDINATOR case accept --case TARGET --plan PLAN \
  --baseline BASELINE_BUNDLE/receipt.json --candidate CANDIDATE_BUNDLE/receipt.json \
  --gate REGRESSION_BUNDLE/receipt.json --gate HOLDOUT_BUNDLE/receipt.json \
  --review REVIEW --baseline-build BASELINE_BUILD --candidate-build CANDIDATE_BUILD \
  --output-dir ACCEPTED_BUNDLE
```

Acceptance rereads and rechecks the bundles instead of trusting verdict flags.
It requires a reproducible baseline violation, a passing candidate, unchanged
case/corpus/checker, a different worker, every planned candidate gate, and an
approval bound to this plan and these receipts. Observation-only justifications
cannot become conformance obligations through this gate. A checker or data
repair needs a separate experiment, not altered scoring within an engine repair.

Hashes detect substitution relative to recorded identities. They are not
signatures or a sandbox. Reviewer names are operator-managed attestations, not
an authenticated identity service, and the operator must preserve a plan before
repair rather than rewrite every artifact afterward. The reviewer must audit
the worker/adapter and scope of the patch; repeatable observations alone can
come from a consistently wrong implementation. An accepted receipt does not
publish code, update a production dependency, or prove behavior outside its
stated cases.


## Automatic attribution

Acceptance now emits `attribution.json` and `case-note.md`, along with the
review, plan, build records, source patch and before/after/gate bundles. The
completion marker `acceptance.json` is written last. A repair must be committed
and clean, based on the baseline pin; both builds must use identical harness
source files, compiler, relevant flags and builder. Build hashes identify the
executables actually evaluated, including an experimental source override.

The note's result table uses the same typed measurement function as the checker.
It includes the case's origin, rules citations, controls, source commit and
stable case/acceptance IDs. Reviewer rationale is labeled as review; the
renderer does not invent a discovery story or root cause. Authored cases are
explicitly labeled. Imported evidence can record source artifact hashes;
successful reduction records its parent case and transformation.

`scripts/compare-case-workers.py` runs both campaigns with one coordinator and
writes a bound review template and the exact acceptance command. Approval still
requires a fresh review. When it succeeds, copy the accepted directory into
`cases/evidence/CASE-SLUG` and regenerate the index:

```sh
BASELINE_COORDINATOR case catalog --evidence-dir cases/evidence \
  --output cases/evidence/README.md
BASELINE_COORDINATOR case note --attribution ACCEPTED_BUNDLE/attribution.json \
  --output ACCEPTED_BUNDLE/case-note.md --check
```

CI checks the generated notes, patch and build-record bindings, and index for
drift. Archived notes carry a portable record of evidence; reproducing the
experiments also requires the preserved coordinator and workers or rebuilding
new artifacts with new identities. Build records and review identities are
operator attestations, not cryptographic proof of a trustworthy compiler.
Use the generated case note as the factual reference when writing the blog.

The production Phase dependency stays pinned until a reviewed repair is
published and the pin is deliberately updated. An accepted bundle retains
`repair.patch` so the experiment does not depend on publishing the repair
branch. To reconstruct the engine source, create a fresh checkout at the
bundle's `repair.base_revision`, apply that patch with `git apply --check`
followed by `git apply`, and commit it with a `Case-Id: CASE_ID` trailer.
Use that checkout with `build-case-worker.py --phase-checkout ...`.
A reconstructed commit and rebuilt executable have new identities: run a new
comparison and review rather than copying an old approval onto new receipts.
