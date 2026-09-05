#!/usr/bin/env python3
"""Extract a small, identity-checked regression corpus from two pinned snapshots.

This does not parse card rules: the Phase export remains executable input.
The independent Scryfall snapshot checks identity and printed Oracle text.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def records(raw):
    if raw.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    if raw.lstrip().startswith(b"["):
        return json.loads(raw)
    return (json.loads(line) for line in raw.splitlines() if line.strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase-export", type=Path, required=True)
    parser.add_argument("--scryfall", type=Path, required=True)
    parser.add_argument("--cases", type=Path, default=Path("cases/cards"))
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    export_raw = args.phase_export.read_bytes()
    scryfall_raw = args.scryfall.read_bytes()
    export = json.loads(export_raw)
    names = {
        card["name"]
        for path in sorted(args.cases.glob("*.json"))
        for card in json.loads(path.read_text())["scenario"]["cards"]
    }
    if not names:
        raise ValueError("no case cards found")
    canonical = {card["name"]: card for card in records(scryfall_raw) if card.get("name") in names}
    subset, sources = {}, []
    for name in sorted(names):
        face = export.get(name.lower())
        if face is None or face["name"] != name:
            raise ValueError(f"no unambiguous primary Phase face for {name}")
        oracle = canonical.get(name)
        if oracle is None:
            raise ValueError(f"Scryfall identity unresolved for {name}")
        if face.get("scryfall_oracle_id") != oracle["oracle_id"]:
            raise ValueError(f"Oracle identity mismatch for {name}")
        if (face.get("oracle_text") or "").split() != (oracle.get("oracle_text") or "").split():
            raise ValueError(f"Oracle text mismatch for {name}")
        subset[name.lower()] = face
        sources.append({"name": name, "oracle_id": oracle["oracle_id"],
                        "source": oracle["scryfall_uri"].split("?")[0]})
    raw = (json.dumps(subset, sort_keys=True, indent=2) + "\n").encode()
    provenance = {"phase_export_sha256": sha(export_raw), "scryfall_sha256": sha(scryfall_raw),
                  "corpus_sha256": sha(raw), "cards": sources,
                  "interpretation": "Identity and Oracle text checked; semantic correctness is evaluated by cases."}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "corpus.json").write_bytes(raw)
    (args.output_dir / "sources.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Prepared {len(subset)} cards; corpus SHA-256 {sha(raw)}")


if __name__ == "__main__":
    main()
