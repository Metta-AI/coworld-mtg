#!/bin/sh
set -eu

: "${HARNESS_SET:?HARNESS_SET is required}"
: "${HARNESS_PHASE_REV:?HARNESS_PHASE_REV is required}"
: "${HARNESS_MANIFEST_URI:?HARNESS_MANIFEST_URI is required}"
: "${HARNESS_SEED_START:?HARNESS_SEED_START is required}"
: "${HARNESS_SEED_COUNT:?HARNESS_SEED_COUNT is required}"
: "${HARNESS_OUTPUT_DIR:?HARNESS_OUTPUT_DIR is required}"
: "${HARNESS_RUN_ID:?HARNESS_RUN_ID is required}"

HARNESS_ACTION_BUDGET="${HARNESS_ACTION_BUDGET:-2000}"
HARNESS_CHECKPOINT_EVERY="${HARNESS_CHECKPOINT_EVERY:-100}"
HARNESS_MAX_TRACE_BYTES="${HARNESS_MAX_TRACE_BYTES:-1073741824}"
HARNESS_CORPUS_DIR="${HARNESS_CORPUS_DIR:-.private/corpus}"
HARNESS_DECK_A="${HARNESS_DECK_A:-$HARNESS_CORPUS_DIR/decks/lorehold_excavation.json}"
HARNESS_DECK_B="${HARNESS_DECK_B:-$HARNESS_CORPUS_DIR/decks/fractal_convergence.json}"
CARGO_NET_OFFLINE="${CARGO_NET_OFFLINE:-true}"
export CARGO_NET_OFFLINE

set -- improve \
  --set "$HARNESS_SET" \
  --phase-rev "$HARNESS_PHASE_REV" \
  --manifest-uri "$HARNESS_MANIFEST_URI" \
  --seed-start "$HARNESS_SEED_START" \
  --seed-count "$HARNESS_SEED_COUNT" \
  --checkpoint-uri "$HARNESS_OUTPUT_DIR" \
  --run-id "$HARNESS_RUN_ID" \
  --deck-a "$HARNESS_DECK_A" \
  --deck-b "$HARNESS_DECK_B" \
  --action-budget "$HARNESS_ACTION_BUDGET" \
  --checkpoint-every "$HARNESS_CHECKPOINT_EVERY" \
  --max-trace-bytes "$HARNESS_MAX_TRACE_BYTES"

if [ "${HARNESS_RESUME:-false}" = "true" ]; then
  set -- "$@" --resume
fi

exec cargo run --locked -p coworld-mtg-harness -- "$@"
