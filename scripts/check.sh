#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

python3 scripts/check-phase-pin.py
scripts/cargo.sh fmt --all -- --check
scripts/cargo.sh clippy --workspace --all-targets -- -D warnings
scripts/cargo.sh test --workspace --locked
scripts/cargo.sh run --locked -q -p coworld-mtg-harness -- case contracts --output-dir docs/contracts --check
if [[ -f .private/corpus/phase-card-data.json ]]; then
  scripts/cargo.sh test --workspace --locked --features private-corpus-tests
fi
scripts/cargo.sh run --locked -q -p coworld-mtg-harness -- case catalog --evidence-dir cases/evidence --output cases/evidence/README.md --check
python3 -m py_compile scripts/build-corpus-artifact.py scripts/check-phase-pin.py scripts/prepare-case-corpus.py scripts/build-case-worker.py scripts/compare-case-workers.py
python3 -m unittest discover -s scripts/tests
bash -n scripts/*.sh
scripts/clean-generated.sh --tests
npm run typecheck
npm test
npm run build
if [[ -f .private/corpus/phase-card-data.json ]]; then
  npm run test:e2e
fi
