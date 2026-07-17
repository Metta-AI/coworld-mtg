#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TOOLCHAIN=$(sed -n 's/^channel = "\([^"]*\)"/\1/p' "$ROOT/rust-toolchain.toml")
RUSTUP_BIN=${RUSTUP_BIN:-$(command -v rustup || true)}

if [[ -z "$TOOLCHAIN" || -z "$RUSTUP_BIN" ]]; then
  echo "rustup and the pinned rust-toolchain.toml channel are required" >&2
  exit 1
fi

RUSTUP_DIR=$(dirname "$RUSTUP_BIN")
export PATH="$RUSTUP_DIR:$PATH"
export RUSTC="$RUSTUP_DIR/rustc"
export RUSTDOC="$RUSTUP_DIR/rustdoc"
exec "$RUSTUP_DIR/cargo" "+$TOOLCHAIN" "$@"
