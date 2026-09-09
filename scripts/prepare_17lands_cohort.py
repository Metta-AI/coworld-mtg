#!/usr/bin/env python3
"""Freeze exact public 17Lands CSV rows for bounded fitting; never run an engine.

Paths inside cohort.json are relative to that manifest. CSV bytes are preserved,
including quoting and line endings. No rows are filtered by mapping, mulligans,
or observed outcomes. Existing output directories are never modified.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile

SCHEMA = "coworld/17lands-cohort@1"
METADATA = ("on_play", "num_mulligans", "opp_num_mulligans", "opening_hand")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path, max_bytes: int) -> str:
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise ValueError(f"Input missing or exceeds {max_bytes} bytes: {path}")
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("Input grew beyond its byte limit")
            h.update(chunk)
    return h.hexdigest()


class RawLines:
    """Supply CSV text lines while retaining exact bytes consumed per record."""

    def __init__(self, source, max_bytes: int):
        self.source = source
        self.max_bytes = max_bytes
        self.offset = 0
        self.record = bytearray()

    def __iter__(self):
        return self

    def __next__(self):
        remaining = self.max_bytes - self.offset
        data = self.source.readline(max(1, remaining + 1))
        if not data:
            raise StopIteration
        if len(data) > remaining:
            raise ValueError("Selected CSV prefix exceeds its decompressed byte limit")
        self.offset += len(data)
        self.record.extend(data)
        return data.decode("utf-8")

    def take(self, reader):
        start = self.offset
        self.record.clear()
        fields = next(reader)
        return start, bytes(self.record), fields


def extract_records(archive: Path, start_row: int, count: int, max_csv_bytes: int):
    if start_row < 0 or count < 1:
        raise ValueError("start_row must be nonnegative and count must be positive")
    with gzip.open(archive, "rb") as source:
        lines = RawLines(source, max_csv_bytes)
        reader = csv.reader(lines, strict=True)
        try:
            _, header_raw, header = lines.take(reader)
        except StopIteration as exc:
            raise ValueError("CSV has no header") from exc
        if not header or len(set(header)) != len(header):
            raise ValueError("CSV header must contain unique columns")
        selected = []
        for index in range(start_row + count):
            try:
                offset, raw, fields = lines.take(reader)
            except StopIteration as exc:
                raise ValueError(f"CSV ended before requested source row {index}") from exc
            if len(fields) != len(header):
                raise ValueError(f"CSV source row {index} has the wrong field count")
            if index >= start_row:
                selected.append((index, offset, raw, dict(zip(header, fields))))
    return header_raw, header, selected


def prepare_cohort(
    *,
    archive: Path,
    archive_sha256: str,
    source_url: str,
    cards_csv: Path,
    cards_sha256: str,
    output_dir: Path,
    start_row: int = 0,
    count: int = 20,
    development_rows: tuple[int, ...] = (),
    previously_inspected_prefix: int = 0,
    turn_pairs: int = 2,
    nodes: int = 10000,
    max_actions: int = 128,
    opponent_filler: str = "Plains",
    max_archive_bytes: int = 1024**3,
    max_csv_bytes: int = 16 * 1024**2,
    max_mapping_bytes: int = 8 * 1024**2,
) -> dict:
    """Write a standalone cohort atomically; return its deterministic manifest."""
    if output_dir.exists():
        raise ValueError("Output directory already exists; earlier evidence is immutable")
    if not source_url.startswith("https://"):
        raise ValueError("Source URL must identify an HTTPS source")
    if count < 1 or count > 1000 or start_row < 0:
        raise ValueError("Select 1..1000 rows at a nonnegative start")
    if min(turn_pairs, nodes, max_actions) < 1 or previously_inspected_prefix < 0:
        raise ValueError("Fit limits must be positive and inspected prefix nonnegative")
    if len(set(development_rows)) != len(development_rows):
        raise ValueError("Duplicate development source row")
    if not set(development_rows) <= set(range(start_row, start_row + count)):
        raise ValueError("Every declared development row must belong to this cohort")
    if file_sha256(archive, max_archive_bytes) != archive_sha256:
        raise ValueError("Archive SHA256 mismatch")
    if file_sha256(cards_csv, max_mapping_bytes) != cards_sha256:
        raise ValueError("Official mapping SHA256 mismatch")
    mapping = cards_csv.read_bytes()
    if sha256(mapping) != cards_sha256:
        raise ValueError("Mapping changed while being snapshotted")
    mapping_reader = csv.DictReader(io.StringIO(mapping.decode("utf-8"), newline=""))
    if not {"id", "name"} <= set(mapping_reader.fieldnames or []):
        raise ValueError("Official mapping must expose id and name columns")
    header_raw, header, selected = extract_records(archive, start_row, count, max_csv_bytes)
    if file_sha256(archive, max_archive_bytes) != archive_sha256:
        raise ValueError("Archive changed while extracting the selected prefix")
    csv_snapshot = header_raw + b"".join(raw for _, _, raw, _ in selected)
    cases = []
    for game_index, (source_index, offset, raw, row) in enumerate(selected):
        cases.append({
            "case_id": f"sos-source-row-{source_index:06d}",
            "game_index": game_index,
            "source_row_index": source_index,
            "role": "development" if source_index in development_rows else "evaluation",
            "previously_inspected": source_index < previously_inspected_prefix,
            "unseen_holdout": False,
            "source_row_sha256": sha256(raw),
            "source_row_bytes": len(raw),
            "decompressed_byte_offset": offset,
            "raw_metadata": {key: row.get(key) for key in METADATA},
            "metadata_presence": {
                key: "missing_column" if key not in row else "blank" if row[key] == "" else "present"
                for key in METADATA
            },
        })
    manifest = {
        "schema": SCHEMA,
        "source": {
            "url": source_url,
            "archive_sha256": archive_sha256,
            "bytes": archive.stat().st_size,
            "retrieved_at": None,
            "acquisition_binding": "Retained local archive rehashed before and after selection. "
            "Historical source URL association is caller-attested; original HTTP receipt and "
            "retrieval time are unavailable. This command does not download data.",
            "attribution": {
                "provider": "17Lands",
                "documentation_url": "https://www.17lands.com/public_datasets",
                "license": "CC BY 4.0",
                "license_url": "https://creativecommons.org/licenses/by/4.0/",
                "credit": "Source data: 17Lands public datasets. Cohort selection and provenance "
                "by Coworld MTG. 17Lands does not endorse this work.",
                "modifications": "Exact complete CSV rows selected with their original header, "
                "quoting and line endings; no field values changed. Manifest and case labels derived.",
            },
        },
        "replay": {"path": "games.csv", "sha256": sha256(csv_snapshot),
                   "bytes": len(csv_snapshot), "rows": count, "columns": len(header)},
        "mapping": {"path": "cards.csv", "sha256": cards_sha256, "bytes": len(mapping),
                    "url": "https://17lands-public.s3.amazonaws.com/analysis_data/cards/cards.csv",
                    "binding": "Exact supplied official mapping bytes; URL association is caller-attested."},
        "selection": {
            "start_row": start_row, "count": count, "no_filters": True,
            "algorithm": "Contiguous source rows in original CSV order; no outcome, identity, "
            "mulligan or support filters.",
            "previously_inspected_prefix": previously_inspected_prefix,
            "development_source_rows": list(development_rows),
            "unseen_holdout": False,
            "history_boundary": "Inspection history is caller-declared. Evaluation is a role, "
            "not a claim that source rows were unseen.",
        },
        "fit": {"turn_pairs": turn_pairs, "nodes": nodes, "max_actions": max_actions,
                "opponent_filler": opponent_filler},
        "preparer_sha256": sha256(Path(__file__).read_bytes()),
        "cases": cases,
        "scope": "Frozen source workload only. No engine execution, compatibility result, "
        "rules correctness verdict or acceptance decision is encoded.",
    }
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        (staged / "games.csv").write_bytes(csv_snapshot)
        (staged / "cards.csv").write_bytes(mapping)
        (staged / "cohort.json").write_text(
            json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if output_dir.exists():
            raise ValueError("Output appeared during preparation; refusing to replace it")
        os.rename(staged, output_dir)
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--cards-csv", required=True, type=Path)
    parser.add_argument("--cards-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--start-row", type=int, default=0)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--development-row", action="append", type=int, default=[])
    parser.add_argument("--previously-inspected-prefix", type=int, default=0)
    parser.add_argument("--turn-pairs", type=int, default=2)
    parser.add_argument("--nodes", type=int, default=10000)
    parser.add_argument("--max-actions", type=int, default=128)
    parser.add_argument("--opponent-filler", default="Plains")
    args = vars(parser.parse_args())
    args["development_rows"] = tuple(args.pop("development_row"))
    manifest = prepare_cohort(**args)
    print(json.dumps({"schema": manifest["schema"], "rows": len(manifest["cases"]),
                      "replay_sha256": manifest["replay"]["sha256"],
                      "mapping_sha256": manifest["mapping"]["sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()

