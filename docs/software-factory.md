# Software factory replays

A factory run records where a case came from, which program ran it, what each
evaluator established, what changed, and why a decision followed. The viewer
reads those records directly. A prose case study is an interpretation of a
replay, rather than the evidence format.

| Boundary | Responsibility |
| --- | --- |
| `loop-contract::FactoryReplay` | Versioned stages, ordered events, content identities, source lineage, builds, feedback, frozen gates, reviews and decisions. |
| `factory-runtime` | Target-independent validation, read-only HTTP serving and portable UTF-8 bundles. |
| `scripts/factory_replay.py` | Single-writer recording, immutable artifacts, atomic snapshots, bounded subprocess execution and measured compute. |
| Domain adapter | Case derivation, worker protocol, weak signals, strong evaluator and bounded acceptance policy. |
| `web/src/factory/` | Display recorded state, inspect provenance and hashes, replay events and follow live work. |

Rust types generate the JSON Schemas and architecture diagram in
[`docs/contracts`](contracts). Stage topology comes from `factory_stages()`;
the viewer does not carry a separate lifecycle. JSON fits the existing artifact,
browser and command-line boundaries without adding a second representation.

## The Scryfall adapter

The adapter saves one Oracle Cards bulk snapshot, then audits every row.
Acquisition records the descriptor, archive hash, retrieval headers, dates,
attempts and pinned rules version. The scanner handles compressed JSONL and
retains decoding and exclusion outcomes.

The frozen recipe selects normal-layout, paper-printing representatives legal or
restricted in Vintage. A broad text heuristic nominates activated mana-producing
paragraphs that may involve library movement. Quoted token abilities, delayed
effects and references to cards drawn can match without establishing a defect.

A separate source grammar freezes the stronger cohort before candidate results.
It interprets a small set of complete cost/effect sentences, aligns them with
the actual Phase AST, then compares Phase's native classification with CR605.1a.
Missing, unsupported or misaligned observations are inconclusive. A failed
frozen gate cannot be dropped to obtain acceptance.

Each measurement runs the expectation-free Phase worker twice in separate
processes. Exact inputs, outputs, exit results, binary/build identities and
measured wall time become artifacts/events. Verification binds each parsed
observation back to its retained JSONL bytes; new receipts name that output
artifact explicitly. The checker receives observations
after execution; the worker does not receive expected classifications.

For the September 7, 2026 snapshot:

- 38,633 rows were audited; 29,530 qualified for the declared source population.
- 47 cards matched the broad discovery heuristic.
- The frozen gate contains eight discovered development cards and ten
  mechanically selected simple-mana controls.
- Four gates are holdout controls. No source-qualified library-moving card fell
  in holdout, so this experiment cannot claim held-out repair performance for
  that family.
- The repeated development baseline found eight violations, six passing controls
  and 27 inconclusive candidates.

These are authentic card definitions, not human gameplay transcripts.
Acceptance covers classification within the frozen grammar; runtime gameplay
needs its own production-path evidence.

## Run and inspect

Use a reserved EC2 workspace with an isolated build target and bounded worker
count. No private MTGJSON runtime corpus is needed for this adapter.

```sh
export CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0
scripts/cargo.sh build -p factory-runtime -p coworld-mtg-harness
npm ci
npm run build:legacy

python3 scripts/scryfall_source.py fetch --output-dir tmp/source --include-rules
python3 scripts/scryfall_source.py scan --snapshot-dir tmp/source --output-dir tmp/discovery
python3 scripts/mana_library_oracle.py freeze-plan \
  --snapshot-dir tmp/source --discovery-dir tmp/discovery --output-dir tmp/plan

python3 scripts/scryfall_factory.py prepare \
  --snapshot-dir tmp/source --discovery-dir tmp/discovery --plan-dir tmp/plan \
  --output-dir tmp/runs/example --run-id example \
  --runtime target/debug/factory-runtime \
  --baseline-revision <actual-phase-baseline-revision>

target/debug/factory-runtime serve \
  --root tmp/runs --web-dist web/dist --bind 127.0.0.1:8030
```

Open `/client/factory.html`. Select a run with `?run=example`.
The three HTTP reads are run listings, a run's `replay.json`, and its artifacts
addressed by hash. The server validates paths and hashes and rejects symlinks.

The existing isolated builder preserves source snapshots and checks its own build receipt:

```sh
python3 scripts/build-case-worker.py --phase-checkout /absolute/phase-checkout --output-dir tmp/candidate-build
python3 scripts/scryfall_factory.py attest-build --build-dir tmp/candidate-build --output tmp/candidate-attestation.json
```

`execute` takes a worker binary and build attestation. Baseline runs use
development cases; candidate runs include every queued case and all holdouts.
Candidate attestations bind the actual source revision, original baseline,
exact patch hash and binary hash. A worker's declared Phase pin is separate from
the attested source revision when a checkout override is used.

After a patch exists, `propose` attaches it to measured failures. `review`
records the independent review and exact before/after receipts. `decide`
recomputes the frozen requirements and validates a decision before publication.
Each command's `--help` lists its arguments.

By default, `decide` closes the run after either outcome. Use
`decide --continue-on-rejection` to retain an immutable rejected decision while
leaving that replay running for a distinct next patch against the same baseline.
The source identities, evaluator and frozen target/regression/holdout plan stay
unchanged; the next patch receives its own executions, feedback and decision.
The same exact change cannot be decided again. Accepted decisions always close
the run, including with this flag, and terminal runs cannot be reopened.

```sh
python3 scripts/scryfall_factory.py verify \
  --run-dir tmp/runs/example --runtime target/debug/factory-runtime
target/debug/factory-runtime export tmp/runs/example --output tmp/example.replay.json
target/debug/factory-runtime verify tmp/example.replay.json
```

The first check reruns the installed, hash-matched domain evaluator. The native
check validates artifact identities and declared provenance; it does not imply
that an external policy's semantics are correct. Importing a bundle never
executes embedded evaluator source.

A portable bundle contains `{replay, artifact_contents}`. Artifact contents are
exact UTF-8 strings, preserving whitespace and byte-order marks. Executables and
the full bulk archive remain separate retained inputs with recorded identities.
Interrupted, superseded and rejected work stays separate from successful runs.

## Share a run

A shareable directory preserves the exact replay and artifact identities. Large
publisher-owned source documents can stay at the recorded source URL:

```sh
python3 scripts/share_factory_replay.py package tmp/runs/example \
  --output tmp/shared/example --runtime target/debug/factory-runtime \
  --external '<recorded-source-sha256>=<recorded-https-url>'
python3 scripts/share_factory_replay.py hydrate tmp/shared/example \
  --runtime target/debug/factory-runtime
```

The package includes `external-artifacts.json` for explicitly designated source
artifacts. Hydration downloads missing bytes into a staging directory, verifies
the complete run, and atomically adds the verified artifacts. Existing files
remain immutable. After hydration the ordinary viewer, domain verification and
portable export commands work unchanged. Portable export is the fully contained
format for local offline viewing.

## Record finished agent work

Record a completed Codex CLI JSONL session without copying its private inputs
into the replay:

```sh
python3 scripts/record_agent_work.py \
  --run-dir tmp/runs/example --runtime target/debug/factory-runtime \
  --session private/session.jsonl --prompt private/prompt.txt --report private/report.md \
  --model gpt-6-astra --role repair_plan --reasoning-effort ultra \
  --summary "Reviewed the implementation plan against the recorded failures."
```

Only content hashes and caller-selected public metadata are retained. Prompt,
report and session contents and local paths stay private. The model and role are
caller declarations. `--feedback-id SHA` may be repeated; links default to
cross-references. `--feedback-supplied-at-start` explicitly records the caller's
assertion that those exact receipts were supplied initially, without claiming
independent proof of prompt contents. `--stage review` assigns review compute to
that stage; planning defaults to `changes`.

The recorder accepts one completed CLI thread, including startup items and
multiple completed turns, and sums measured `turn.completed` usage once. Input
and output totals feed the compute event; cached input and reasoning output are
reported separately as subsets. Billing, wall time and absent usage stay unknown.
If any turn lacks a count, that whole-session count remains null. No empty
compute event is emitted when neither input nor output totals are known.

The summary and compute events pass native verification before one atomic
publication. Each work unit must use one ephemeral CLI thread, recorded once as a
complete thread snapshot. A domain-separated hash identifies that thread without
publishing its raw ID. Repeating identical metadata is idempotent; any different
record for the same thread is rejected, including an appended turn with a new
report and session-file hash. Turn deltas are not inferred. Reusing a report or
session file with conflicting attribution is also rejected.

Older CLI records without the thread hash and ad hoc summaries cannot detect
thread overlap. Do not re-import or continue those already-counted threads; use
new ephemeral threads for new work. Existing records remain immutable.
Malformed, failed, incomplete or concatenated sessions, unknown feedback links
and terminal runs are rejected. Publication time is not the agent's work duration.

The caller also associates the supplied prompt and report with the session.
Their hashes preserve those supplied files; they do not independently prove
that the session consumed the prompt or authored the report.

## Adapting another factory

The reusable boundary is the replay, artifact store, viewer and recording kernel.
`FactoryBuild` has no Phase fields; cases can be arbitrary retained inputs;
`FeedbackAdapter::Opaque` and `DecisionPolicy::External` carry another evaluator's
records. The standalone runtime does not depend on the Phase bridge. Domain
adapters still supply acquisition, worker invocation, evaluation and acceptance
logic; the common layer does not choose edits or schedule an autonomous search.

The following CSV-to-JSON repair factory is a **hypothetical adapter mapping**,
not another measured run. It needs no new common schema:

| Factory concept | What this adapter would record |
| --- | --- |
| Target and build | Converter repository and baseline revision in `ProgramTarget`; candidate source, executable hash, build command/environment and optional source attestation in `FactoryBuild`. |
| Source and cases | Retained source files and acquisition metadata; one input file or selected record per case. `SourceDerived` identifies source hashes, record selectors and the selection recipe. Hand-authored tests remain `Authored`. |
| Weak feedback | A type-inference warning or unusual output shape, linked to the input and execution. It nominates an investigation; it does not establish a conversion defect. |
| Strong feedback | An installed checker compares the exact output with a frozen schema rule, such as preserving a column declared to contain string identifiers. The receipt states that bounded claim and checker version. |
| Discrete change | A patch hash and the feedback that motivated it. Candidate executions reference that change and its build. |
| Frozen gates | A target case plus separately selected regression and holdout cases, frozen before candidate execution. Unsupported or missing observations remain inconclusive. |
| Review and decision | Review bound to the exact plan and before/after receipts; an external policy artifact and attestation bound to the recorded decision, scope, plan and change. |
| Compute and explanation | Measured execution costs and agent-work records. The viewer follows decision → feedback → execution/build → case → source, with change motivation as an explicit link. |

A compiler adapter could instead retain source programs and compiler builds.
Differential output is a strong check only within a frozen language subset with
a pinned reference and relevant preconditions established, such as excluding undefined behavior;
otherwise disagreement is a useful weak signal or an inconclusive result.
Several weak signals do not satisfy a missing strong acceptance gate.

Start the adapter with `Replay.create`, retain inputs through `artifact`, register
cases through `event`, then use `build`, `run_jsonl` and `feedback`. Keep expected
results in the evaluator, outside the worker request. The Python runner currently
uses Unix process limits and defaults to one finite JSONL observation of at most
16 MiB. An adapter can supply `decode_output` and `output_media_type` for another
native format; raw output remains a separate byte artifact. Decoder exceptions
produce error evidence with no partial observation. Requests retain the actual
command vector as well as input and executable hashes. A domain verifier must
check those arguments and recompute the decoded observation with its frozen
decoder; imported replay code is never executed. For interpreted programs, the interpreter's binary hash alone
does not identify the target: retain the program's source and invocation in the
build attestation and verify that binding. Original domain data, including
floating-point values, can remain byte artifacts instead of canonical contracts.

### What verification establishes

Native verification checks the envelope, artifact hashes, references, ordering
and structural acceptance requirements. For opaque feedback it does not recompute
the evaluator or establish that a nested observation matches the retained worker
output. A new adapter needs an installed domain verifier that checks those bytes,
request/build identities, evaluator dependencies and frozen expectations before
recomputing feedback and policy decisions. The Scryfall adapter supplies that
extra audit for its own protocol; importing a replay never executes supplied code.

Hashes bind content, not source authenticity, reviewer independence or execution
truth. Those claims also require the operator's collection and review procedures.
A `strong` label is a declared level of support for a stated claim, not proof by
itself. The viewer displays recorded decisions; successful native verification
alone does not authorize a change or certify an external policy.

The current accepted-decision contract describes a repaired violation: a violated
baseline target, a satisfied candidate, all disjoint regression and holdout gates,
and a matching approving review. A performance adapter can use a genuine frozen
budget as its target requirement. Pure utility ranking without such a requirement
is outside this acceptance shape; do not invent a baseline violation to fit it.
The non-MTG parser fixtures establish that the envelope can represent another
domain. They do not establish a second production improvement result.


### Real 17Lands importer coverage adapter

`scripts/seventeenlands_factory.py` applies the same runtime to Coworld's native
`mine17lands` importer. The target is the Coworld harness repository and commit;
the Phase revision in its minimal manifest is a loader compatibility pin. It is
not the source revision being repaired. The observed discovery failure read 92
real public game rows but produced an empty card-frequency list. Independent
source parsing found 1,426 listed cast occurrences, 230 Arena IDs and 229 official
names (two IDs map to Lightning Strike). These counts concern source ingestion.
They do not establish a successful repair or gameplay correctness.

The frozen experiment uses exact public CSV bytes and the official `cards.csv`
mapping. Primary rows 1–46 and regression rows 47–92 are disjoint. The holdout is
the first 16 newly completed rows after those 92, selected from a longer prefix
of the same archive before candidate results and withheld from the miner
implementation agent. Acquisition checks the new prefix's first 65,536 bytes
against the retained prefix, and records ETag, Last-Modified, byte ranges and
hashes. The whole-92 case is an additional reproduction measurement that overlaps
the two known partitions; its counts must not be added to theirs. Holdout success
would cover unseen rows of this archive, not unseen formats or rules semantics.

`seventeenlands_coverage.py` independently enumerates exact per-turn cast columns,
pipe positions, Arena IDs and official names. It excludes totals, zone snapshots
and ability lists. Repeated casts retain separate entries; name frequencies may
combine different Arena IDs. Unknown schemas, missing input rows, invalid tokens,
unmapped IDs, failed workers and nonrepeatable output remain inconclusive. A provided
unknown or malformed normalization schema is inconclusive even when its frequency
list differs; the known baseline can still prove frequency loss without a
normalization field. Repeatability compares the coverage projection after omitting
the invocation-local mapping path. It does not require equality of unrelated weak
numeric summaries or entire raw output files; both raw files remain retained. Strong
feedback checks this source-coverage claim; the fact that the workload came from
human games is separately recorded as weak feedback. Both the native observation
and coverage receipt use the tagged `software-factory-result-v1` display envelope,
with the recorded feedback result separate from measured data.

The baseline uses its supported legacy flags. The candidate additionally receives
`--input-schema public-replay-wide-v1`, the official mapping path and its hash.
Both consume the same frozen public source identities through a minimal public-only
manifest; its zero corpus-validation fields make no assertion about a Phase
corpus. Historical discovery output that used private bootstrap material must be
described separately and must not be relabeled as public-input-only execution.

A build receipt has schema `17lands-miner-build-v1`: exact Coworld source/base
commits, patch and executable hashes, Cargo lock hash, source-file hashes before
and after compilation, compiler identity, command and environment. The before and
after maps must equal the retained source map; a baseline has the empty patch
hash, and a candidate binds its distinct clean commit to the proposed patch.
Retain the source archive and actual builder logs separately. These are explicit
caller attestations, not independent proof of reproducible compilation.

```sh
python3 scripts/seventeenlands_factory.py prepare --source-dir SOURCE_FREEZE_DIR \
  --output-dir RUN_DIR --runtime FACTORY_RUNTIME --run-id RUN_ID \
  --baseline-revision FULL_COWORLD_BASELINE_COMMIT
python3 scripts/seventeenlands_factory.py execute --run-dir RUN_DIR \
  --runtime FACTORY_RUNTIME --phase baseline --worker BASELINE_WORKER \
  --build-attestation BASELINE_BUILD_JSON
python3 scripts/seventeenlands_factory.py propose --run-dir RUN_DIR \
  --runtime FACTORY_RUNTIME --patch EXACT_TARGET_PATCH --description DESCRIPTION
python3 scripts/seventeenlands_factory.py execute --run-dir RUN_DIR \
  --runtime FACTORY_RUNTIME --phase candidate --worker CANDIDATE_WORKER \
  --build-attestation CANDIDATE_BUILD_JSON --change-id PATCH_SHA256
```

Then use `review`, `decide` and `verify` with the same run/runtime. A passing result
still needs a retained independent review bound to the exact plan and before/after
feedback. `verify` checks retained output bytes, source slices, mapping, invocation,
build binding, exact installed evaluator and adapter hashes, and recomputed
acceptance inputs. Only `decide`
records acceptance; default terminal-run immutability applies.

Public packaging is an explicit allowlist: derived source CSV partitions, official
mapping, sanitized acquisition/slicing receipt, frozen evaluator and expectations,
raw native outputs, bounded execution/feedback, patch/build/review/decision records.
Compressed prefix bytes remain in the source-freeze directory outside the UTF-8
portable bundle, with their hashes and derivation in the public receipt. A prefix
hash is never a full archive hash. Do not copy the audit directory wholesale or
publish its original completion/importer receipts, private bootstrap manifest or
materialized corpus. Attribute [17Lands public datasets](https://www.17lands.com/public_datasets)
under CC BY 4.0, record slicing as a modification, and retain the non-endorsement
notice. Wide game rows omit global action order, targets, priority and hidden state.
