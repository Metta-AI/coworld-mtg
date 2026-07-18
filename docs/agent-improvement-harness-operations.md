# Agent-improvement harness operations

The harness calls Phase directly through `phase-bridge`. It does not contain
card rules, infer legal actions, or treat 17Lands observations as conformance
expectations.

## Build

The repository's `rust-toolchain.toml` pins the Phase-compatible toolchain. On
a machine with rustup, setup and compilation are non-interactive:

```sh
rustup show
scripts/cargo.sh build --locked -p coworld-mtg-harness
```

The production card export and deck lists are private artifacts. Authorized local runs first materialize the pinned
compact runtime corpus:

```sh
scripts/fetch-corpus.sh
```

Cloud images should run that build while constructing the image. Runner
workers can then set `CARGO_NET_OFFLINE=true`; corpus inputs are the only
runtime downloads.

## Materialize a corpus

Inputs can be local paths, `file://` URIs, or immutable HTTP(S) URLs. Remote
inputs require an expected SHA-256 value. The Phase input is the full generated
card export, not Coworld MTG's compact test fixture.

```sh
scripts/cargo.sh run --locked -p coworld-mtg-harness -- materialize \
  --set <set-code> \
  --phase-card-data <phase-card-export> \
  --phase-card-data-sha256 <sha256> \
  --mtgjson <mtgjson-snapshot> \
  --mtgjson-sha256 <sha256> \
  --mtgjson-version <version> \
  --scryfall <scryfall-bulk-snapshot> \
  --scryfall-sha256 <sha256> \
  --scryfall-snapshot <snapshot-date> \
  --17lands <17lands-replay-snapshot> \
  --17lands-sha256 <sha256> \
  --17lands-dataset <dataset-name> \
  --output-dir artifacts/corpus
```

The output contains copied content-addressed artifacts, `validation.json`,
`manifest.json`, and `<manifest-id>.manifest.json`. The manifest ID covers the
Phase revision, set, generator schema, source URIs, all input hashes, output
hashes, and cross-check results. Re-running from identical inputs produces the
same ID.

## Mine observational workloads

This command ranks card and event frequency and summarizes turn, damage, mana,
and game-length columns from a 17Lands CSV or CSV gzip snapshot:

```sh
scripts/cargo.sh run --locked -p coworld-mtg-harness -- mine17lands \
  --manifest-uri artifacts/corpus/manifest.json \
  --output artifacts/soft-signals.json
```

The report labels itself observational. It cannot fail a hard gate. Its card
ranking is input for deck/scenario selection and investigation only.

## Run or resume a shard

```sh
scripts/cargo.sh run --locked -p coworld-mtg-harness -- run \
  --manifest-uri artifacts/corpus/manifest.json \
  --deck-a .private/corpus/decks/a.json \
  --deck-b .private/corpus/decks/b.json \
  --run-id campaign-shard-000 \
  --seed-start 0 \
  --seed-count 10000 \
  --action-budget 2000 \
  --checkpoint-every 100 \
  --max-trace-bytes 1073741824 \
  --output-dir artifacts/runs/shard-000
```

Add `--resume` with identical parameters after eviction. `result.json` records
the next seed after every completed game. A resumed gzip is a valid
multi-member gzip, so no existing trace or finding is rewritten.

Every non-concession action comes verbatim from the current viewer's Phase
legal-action set. Each game is replayed from its manifest, decks, seed, and
trace. The hard gate verifies the canonical authoritative state including the
live RNG stream, the event stream, hidden-information projections, zone
references, serialized checkpoint state, and the suffix after restoration.

The equivalent cloud-worker entry point is:

```sh
HARNESS_SET=<set-code> \
HARNESS_PHASE_REV=<phase-commit> \
HARNESS_MANIFEST_URI=<manifest-uri> \
HARNESS_SEED_START=0 \
HARNESS_SEED_COUNT=10000 \
HARNESS_ACTION_BUDGET=2000 \
HARNESS_OUTPUT_DIR=artifacts/runs/shard-000 \
HARNESS_RUN_ID=campaign-shard-000 \
scripts/run-harness-worker.sh
```

Workers stage output locally. A cloud coordinator is responsible for uploading
the bounded directory to its authorized object-storage URI and for marking a
worker `inconclusive` when setup, hash verification, or upload fails.

## Replay, minimize, and aggregate

`traces.jsonl.gz` contains one complete trace per line. Extract a novel trace
before replay or minimization:

```sh
gzip -dc artifacts/runs/shard-000/traces.jsonl.gz | sed -n '1p' > trace.json

scripts/cargo.sh run --locked -p coworld-mtg-harness -- replay \
  --manifest-uri artifacts/corpus/manifest.json \
  --trace trace.json

scripts/cargo.sh run --locked -p coworld-mtg-harness -- minimize \
  --manifest-uri artifacts/corpus/manifest.json \
  --trace trace.json \
  --output minimized.json

scripts/cargo.sh run --locked -p coworld-mtg-harness -- aggregate \
  --run-dir artifacts/runs/shard-000 \
  --run-dir artifacts/runs/shard-001 \
  --output artifacts/scoreboard.json
```

Minimization keeps the smallest action prefix reaching the first reproducible
hash/action failure. A semantic Phase fix still requires a rules-backed,
discriminating Phase regression test as specified by the improvement loop.

## Artifact contract

- `result.json`: schema/version, run and manifest IDs, seed range, next seed,
  limits, counts, elapsed time, and terminal status.
- `traces.jsonl.gz`: ordered decks, seed, initial events/hash, every exact
  action, authoritative events/hash after every transition, optional complete
  checkpoints, and terminal outcome/classification.
- `findings.jsonl.gz`: normalized signature, provisional ownership
  classification, seed, detail, and source trace line.
- `minimized/*.json`: portable traces for hard failures.
- `scoreboard.json`: aggregate counts and findings deduplicated by normalized
  signature. Its `soft_signals` object is explicitly non-conformance evidence.

Credentials are not accepted as CLI arguments and are never written into these
artifacts. Use workload identity or coordinator-provided transport credentials
only for the external download/upload layer.
