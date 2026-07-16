#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCK="$ROOT/corpus.lock.json"
DESTINATION="${COWORLD_MTG_CORPUS_DIR:-$ROOT/.private/corpus}"
URI="${COWORLD_MTG_CORPUS_URI:-$(jq -r .archive_uri "$LOCK")}"
EXPECTED_SHA256="$(jq -r .sha256 "$LOCK")"
ARCHIVE="$(mktemp)"
EXTRACTED="$(mktemp -d)"
trap 'rm -f "$ARCHIVE"; rm -rf "$EXTRACTED"' EXIT

case "$URI" in
  s3://*) aws s3 cp "$URI" "$ARCHIVE" --profile "${AWS_PROFILE:-softmax}" --only-show-errors ;;
  file://*) cp "${URI#file://}" "$ARCHIVE" ;;
  https://*|http://*) curl --fail --location --silent --show-error "$URI" --output "$ARCHIVE" ;;
  *) cp "$URI" "$ARCHIVE" ;;
esac

ACTUAL_SHA256="$(shasum -a 256 "$ARCHIVE" | awk '{print $1}')"
test "$ACTUAL_SHA256" = "$EXPECTED_SHA256" || {
  echo "corpus archive SHA-256 mismatch: expected $EXPECTED_SHA256, got $ACTUAL_SHA256" >&2
  exit 1
}

zstd -q -d -c "$ARCHIVE" | tar -xf - -C "$EXTRACTED"
python3 - "$EXTRACTED" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
assert manifest["schema"] == "coworld-mtg-corpus-v1"
for name, expected in manifest["files"].items():
    data = (root / name).read_bytes()
    assert len(data) == expected["bytes"], name
    assert hashlib.sha256(data).hexdigest() == expected["sha256"], name
PY

rm -rf "$DESTINATION"
mkdir -p "$(dirname "$DESTINATION")"
mv "$EXTRACTED" "$DESTINATION"
echo "materialized $DESTINATION ($EXPECTED_SHA256)"
