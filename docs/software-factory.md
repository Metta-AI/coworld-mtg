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
measured wall time become artifacts/events. The checker receives observations
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

## Adapting another factory

Keep the replay, artifact store, viewer and process recorder. Replace the source
adapter, worker invocation, evaluator and acceptance policy. A compiler repair
factory could register an existing source file, use compiler warnings as weak
feedback, and use independently frozen differential tests as strong feedback.
A data-conversion factory could use production records, parse errors, round-trip
contracts and held-out formats.

Feedback strength names the authority of a bounded claim. Several weak checks
cannot overrule a failed strong gate. A discrete change points to motivating
feedback; feedback points to executions and cases; case derivation points to
source records. That chain supplies attribution for a later blog post.

The common layer does not select edits, interpret Magic, or certify arbitrary
external policies. Planning and repair remain agent-orchestrated. Domain adapters
define correctness; the common layer makes execution and decisions inspectable.
A non-MTG parser fixture exercises this separation in contract and recorder tests.
