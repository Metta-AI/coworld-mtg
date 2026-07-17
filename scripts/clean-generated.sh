#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
EXECUTE=0
declare -a TARGETS=()

add_target() {
  TARGETS+=("$1")
}

while (($#)); do
  case "$1" in
    --execute) EXECUTE=1 ;;
    --rust) add_target "$ROOT/target" ;;
    --web) add_target "$ROOT/web/dist" ;;
    --tests)
      add_target "$ROOT/test-results"
      add_target "$ROOT/playwright-report"
      ;;
    --phase)
      while IFS= read -r path; do add_target "$path"; done < <(
        find "$ROOT/tmp" -maxdepth 1 -type d -name 'phase-client-*' -print 2>/dev/null
      )
      ;;
    --all)
      add_target "$ROOT/target"
      add_target "$ROOT/web/dist"
      add_target "$ROOT/test-results"
      add_target "$ROOT/playwright-report"
      while IFS= read -r path; do add_target "$path"; done < <(
        find "$ROOT/tmp" -maxdepth 1 -type d -name 'phase-client-*' -print 2>/dev/null
      )
      ;;
    *)
      echo "usage: $0 [--rust] [--web] [--phase] [--tests] [--all] [--execute]" >&2
      exit 2
      ;;
  esac
  shift
done

if ((${#TARGETS[@]} == 0)); then
  echo "no cleanup category selected" >&2
  exit 2
fi

for target in "${TARGETS[@]}"; do
  resolved=$(python3 - "$ROOT" "$target" <<'PY'
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
target = Path(sys.argv[2]).resolve(strict=False)
allowed = {
    root / "target",
    root / "web/dist",
    root / "test-results",
    root / "playwright-report",
}
if target not in allowed and not (
    target.parent == root / "tmp" and target.name.startswith("phase-client-")
):
    raise SystemExit(f"refusing unexpected cleanup target: {target}")
print(target)
PY
  )
  [[ -e "$resolved" ]] || continue
  size=$(du -sh "$resolved" | awk '{print $1}')
  if ((EXECUTE)); then
    echo "removing $resolved ($size)"
    rm -rf -- "$resolved"
  else
    echo "would remove $resolved ($size)"
  fi
done

if ((!EXECUTE)); then
  echo "dry run only; pass --execute to remove the listed generated paths"
fi
