#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PHASE_REVISION=${PHASE_REVISION:-$(sed -n 's/^pub const PHASE_REVISION: &str = "\([0-9a-f]*\)";.*/\1/p' "$ROOT/crates/phase-bridge/src/lib.rs")}
CHECKOUT="$ROOT/tmp/phase-client-$PHASE_REVISION"

if [[ ! -d "$CHECKOUT/.git" ]]; then
  mkdir -p "$CHECKOUT"
  git -C "$CHECKOUT" init
  git -C "$CHECKOUT" remote add origin https://github.com/nishu-builder/phase.git
fi

if [[ $(git -C "$CHECKOUT" rev-parse HEAD 2>/dev/null || true) != "$PHASE_REVISION" ]]; then
  git -C "$CHECKOUT" fetch --depth 1 origin "$PHASE_REVISION"
  git -C "$CHECKOUT" checkout --detach FETCH_HEAD
fi

test "$(git -C "$CHECKOUT" rev-parse HEAD)" = "$PHASE_REVISION"
if [[ -f "$ROOT/web/dist/replay.html" ]]; then
  cp "$ROOT/web/dist/replay.html" "$ROOT/web/dist/legacy-replay.html"
fi
rm -rf "$CHECKOUT/client/src/coworld"
mkdir -p "$CHECKOUT/client/src/coworld"
cp -R "$ROOT/phase-client/src/." "$CHECKOUT/client/src/coworld/"
cp "$ROOT/phase-client/player.html" "$CHECKOUT/client/player.html"
cp "$ROOT/phase-client/global.html" "$CHECKOUT/client/global.html"
cp "$ROOT/phase-client/replay.html" "$CHECKOUT/client/replay.html"
cp "$ROOT/phase-client/vite.config.ts" "$CHECKOUT/client/coworld.vite.config.ts"

PHASE_PATCH="$ROOT/phase-client/replay-player-names.patch"
if ! git -C "$CHECKOUT" apply --reverse --check "$PHASE_PATCH" >/dev/null 2>&1; then
  git -C "$CHECKOUT" apply --check "$PHASE_PATCH"
  git -C "$CHECKOUT" apply "$PHASE_PATCH"
fi

corepack pnpm@10.28.2 --dir "$CHECKOUT/client" install --frozen-lockfile
corepack pnpm@10.28.2 --dir "$CHECKOUT/client" exec vitest run \
  src/coworld/coworld-ws-adapter.test.ts \
  src/coworld/coworld-chrome.test.tsx
PHASE_REVISION="$PHASE_REVISION" corepack pnpm@10.28.2 --dir "$CHECKOUT/client" exec vite build --config coworld.vite.config.ts

mkdir -p "$ROOT/web/dist"
cp -R "$CHECKOUT/client/coworld-dist/." "$ROOT/web/dist/"
