#!/usr/bin/env python3
"""Acquire immutable Scryfall evidence and nominate weak discovery candidates.

CLI:
  python3 scripts/scryfall_source.py fetch --output-dir /path/snapshot --include-rules
  python3 scripts/scryfall_source.py scan --snapshot-dir /path/snapshot --output-dir /path/scan

No engine is invoked and no semantic failure is established by this module.
All output directories are independent of the repository and never overwritten.
"""
from __future__ import annotations

import argparse
from collections import Counter
import codecs
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = "CoworldMTGDiscovery/1.0 (+https://github.com/Metta-AI/coworld-mtg)"
DESCRIPTOR_URL = "https://api.scryfall.com/bulk-data/oracle_cards"
RULES_URL = "https://media.wizards.com/2026/downloads/MagicCompRules%2020260819.txt"
RULES_EXPECTED_SHA256 = "4381ad1b39ab2c05f7d03633a20f711ed37277074d3266dcba5f38cbb527423f"
BULLETIN_URL = "https://magic.wizards.com/en/news/announcements/the-hobbit-update-bulletin"
DOCS = {
    "bulk": "https://scryfall.com/docs/api/bulk-data",
    "cards": "https://scryfall.com/docs/api/cards",
    "rate_limits": "https://scryfall.com/docs/api/rate-limits",
    "usage": "https://scryfall.com/docs/api",
    "rules_landing": "https://magic.wizards.com/en/rules",
}
RECIPE = {
    "version": 1,
    "seed": "coworld-scryfall-discovery-20260907-v1",
    "cohort": {
        "object": "card", "oracle_id": "present", "printing_id": "present",
        "layout": "normal", "games_contains": "paper",
        "legalities.vintage": ["legal", "restricted"],
    },
    "signal": "activated paragraph with mana production and potential library movement in cost or effect",
    "signal_strength": "weak; text heuristics nominate candidates and do not establish semantic failure",
    "ranking": ["family eligible distinct oracle count descending", "family name",
                "oracle text length ascending", "sha256(seed NUL oracle_id)", "printing_id", "source_index"],
    "split": "int(sha256(seed NUL oracle_id)[:8], 16) % 100 < 20 => holdout; otherwise development",
    "scope": "All source rows audited; only the declared cohort is ranked. No card-name allowlist.",
    "limits": {"archive_bytes": 134217728, "uncompressed_bytes": 536870912, "record_bytes": 8388608},
}
LIBRARY = re.compile(r"\b(?:mill(?:s|ed|ing)?|draw(?:s|n|ing)?|librar(?:y|ies)|search(?:es|ing)?)\b", re.I)
ADD = re.compile(r"\badd\b", re.I)
MANA = re.compile(r"\{[WUBRGCSXYZ0-9/]+\}|\bmana\b", re.I)


class SourceError(ValueError):
    """Invalid or incomplete source evidence; never a gameplay failure."""


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n")


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_revision():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True)
    return {
        "git_revision": result.stdout.strip() if result.returncode == 0 else None,
        "git_dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
        "script_sha256": file_sha256(Path(__file__)),
        "recipe_sha256": sha256(canonical(RECIPE)),
    }


def descriptor_download(descriptor):
    if descriptor.get("type") != "oracle_cards":
        raise SourceError("descriptor is not oracle_cards")
    if descriptor.get("jsonl_download_uri"):
        url = descriptor["jsonl_download_uri"]
        expected = descriptor.get("compressed_size")
        if not isinstance(expected, int) or isinstance(expected, bool) or expected <= 0:
            raise SourceError("JSONL descriptor needs a positive compressed_size")
        kind, filename = "gzip_jsonl", "oracle-cards.jsonl.gz"
    elif descriptor.get("download_uri"):
        url, expected, kind, filename = descriptor["download_uri"], None, "legacy_json", "oracle-cards.json"
    else:
        raise SourceError("descriptor has neither jsonl_download_uri nor download_uri")
    host = urlparse(url).hostname or ""
    if urlparse(url).scheme != "https" or not host.endswith(".scryfall.io"):
        raise SourceError("bulk download URI must use an HTTPS Scryfall file origin")
    return {"url": url, "expected_bytes": expected, "format": kind, "filename": filename}


class Fetcher:
    """Small sequential client. A 429 stops immediately; transient retries are bounded."""
    def __init__(self, opener=urlopen, sleeper=time.sleep):
        self.opener, self.sleeper = opener, sleeper
        self.last_api_request = None

    def download(self, url, path, limit, expected_bytes=None):
        path = Path(path)
        if path.exists() or path.with_suffix(path.suffix + ".part").exists():
            raise SourceError(f"refusing to overwrite evidence: {path}")
        if urlparse(url).scheme != "https":
            raise SourceError("HTTPS required")
        attempts = []
        partial = path.with_suffix(path.suffix + ".part")
        metadata_path = path.with_suffix(path.suffix + ".http.json")
        for attempt_number in range(1, 4):
            api = urlparse(url).hostname == "api.scryfall.com"
            if api and self.last_api_request is not None:
                self.sleeper(max(0, 0.15 - (time.monotonic() - self.last_api_request)))
            if api:
                self.last_api_request = time.monotonic()
            attempt = {"attempt": attempt_number, "requested_at": now(), "request_url": url,
                       "request_headers": {"User-Agent": USER_AGENT, "Accept": "application/json;q=0.9,*/*;q=0.8"}}
            attempts.append(attempt)
            try:
                request = Request(url, headers=attempt["request_headers"])
                with self.opener(request, timeout=30) as response:
                    attempt.update(status=response.status, final_url=response.geturl(),
                                   response_headers=list(response.headers.items()))
                    if urlparse(response.geturl()).scheme != "https":
                        raise SourceError("refusing an insecure redirect")
                    if response.status != 200:
                        raise SourceError(f"unexpected HTTP status {response.status}")
                    size_header = response.headers.get("Content-Length")
                    if size_header and int(size_header) > limit:
                        raise SourceError("Content-Length exceeds download limit")
                    digest, size = hashlib.sha256(), 0
                    with partial.open("wb") as output:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            size += len(chunk)
                            if size > limit:
                                raise SourceError("download exceeds byte limit")
                            digest.update(chunk)
                            output.write(chunk)
                    if expected_bytes is not None and size != expected_bytes:
                        raise SourceError(f"descriptor size mismatch: expected {expected_bytes}, received {size}")
                    if size_header and size != int(size_header):
                        raise SourceError("HTTP Content-Length mismatch")
                    partial.rename(path)
                    attempt.update(completed_at=now(), bytes=size, sha256=digest.hexdigest())
                    meta = {"path": path.name, "bytes": size, "sha256": digest.hexdigest(),
                            "attempts": attempts}
                    write_json(metadata_path, meta)
                    return meta
            except HTTPError as exc:
                attempt.update(status=exc.code, response_headers=list(exc.headers.items()), error=str(exc))
                write_json(metadata_path, {"path": path.name, "status": "failed", "attempts": attempts})
                if exc.code == 429:
                    raise SourceError("HTTP 429: acquisition stopped; respect Retry-After and Scryfall's 30-second restriction before a new run") from exc
                if exc.code not in (500, 502, 503, 504) or attempt_number == 3:
                    raise SourceError(f"HTTP acquisition failed: {exc.code}") from exc
            except (URLError, TimeoutError, ConnectionError) as exc:
                attempt.update(error=str(exc))
                write_json(metadata_path, {"path": path.name, "status": "failed", "attempts": attempts})
                if attempt_number == 3:
                    raise SourceError("acquisition failed after three attempts") from exc
            except Exception as exc:
                attempt.update(error=str(exc))
                write_json(metadata_path, {"path": path.name, "status": "failed", "attempts": attempts})
                raise
            self.sleeper(attempt_number)
        raise AssertionError("unreachable")


def verify_snapshot(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "source-manifest.json").read_text())
    if manifest.get("status") != "complete":
        raise SourceError("snapshot is incomplete")
    for artifact in manifest["artifacts"].values():
        path = directory / artifact["path"]
        if path.parent.resolve() != directory.resolve():
            raise SourceError("artifact path escapes snapshot")
        if not path.is_file() or path.stat().st_size != artifact["bytes"] or file_sha256(path) != artifact["sha256"]:
            raise SourceError(f"snapshot artifact mismatch: {path.name}")
    return manifest


def fetch_snapshot(output_dir, include_rules=False, fetcher=None):
    output_dir = Path(output_dir)
    if output_dir.exists():
        manifest = verify_snapshot(output_dir)
        if include_rules and "rules" not in manifest["artifacts"]:
            raise SourceError("cached snapshot lacks rules; use a new output directory")
        return manifest
    output_dir.mkdir(parents=True)
    client = fetcher or Fetcher()
    manifest = {"schema_version": 1, "status": "acquiring", "started_at": now(),
                "source_kind": "scryfall_oracle_cards", "source_docs": DOCS,
                "recipe": RECIPE, "producer": source_revision(), "artifacts": {}}
    write_json(output_dir / "source-manifest.json", manifest)
    try:
        manifest["artifacts"]["descriptor"] = client.download(DESCRIPTOR_URL, output_dir / "descriptor.json", 1048576)
        descriptor = json.loads((output_dir / "descriptor.json").read_bytes())
        download = descriptor_download(descriptor)
        manifest["bulk_descriptor"] = descriptor
        manifest["archive_format"] = download["format"]
        manifest["artifacts"]["archive"] = client.download(
            download["url"], output_dir / download["filename"],
            RECIPE["limits"]["archive_bytes"], download["expected_bytes"])
        if include_rules:
            manifest["artifacts"]["rules"] = client.download(RULES_URL, output_dir / "rules.txt", 4194304)
            rules = (output_dir / "rules.txt").read_text(encoding="utf-8-sig")
            match = re.search(r"These rules are effective as of ([^.]+)\.", rules)
            manifest["rules_version"] = {
                "effective_date_text": match.group(1) if match else None,
                "filename_date": "2026-08-19", "url": RULES_URL,
                "research_expected_sha256": RULES_EXPECTED_SHA256,
                "matches_research_hash": manifest["artifacts"]["rules"]["sha256"] == RULES_EXPECTED_SHA256,
                "contract_rule": "605.1a",
            }
            manifest["artifacts"]["update_bulletin"] = client.download(
                BULLETIN_URL, output_dir / "update-bulletin.html", 4194304)
            manifest["update_bulletin"] = {"url": BULLETIN_URL, "published_date": "2026-08-10"}
        manifest.update(status="complete", completed_at=now())
    except Exception as exc:
        manifest.update(status="failed", failed_at=now(), error=str(exc))
        write_json(output_dir / "source-manifest.json", manifest)
        raise
    write_json(output_dir / "source-manifest.json", manifest)
    return manifest


@dataclass
class SourceRecord:
    index: int
    offset: int
    raw: bytes
    card: dict | None
    error: str | None
    source_format: str


def decode_record(index, offset, raw, source_format):
    try:
        card = json.loads(raw)
        if not isinstance(card, dict):
            raise SourceError("record is not a JSON object")
        return SourceRecord(index, offset, raw, card, None, source_format)
    except (ValueError, UnicodeDecodeError) as exc:
        return SourceRecord(index, offset, raw, None, str(exc), source_format)


def _array_records(stream, max_record_bytes, max_uncompressed_bytes):
    """Incremental legacy JSON-array reader retaining each exact object byte span."""
    decoder = json.JSONDecoder()
    text = codecs.getreader("utf-8")(stream)
    buffer, consumed_bytes, read_bytes, eof, index = "", 0, 0, False, 0

    def fill():
        nonlocal buffer, read_bytes, eof
        chunk = text.read(65536)
        read_bytes += len(chunk.encode("utf-8"))
        if read_bytes > max_uncompressed_bytes:
            raise SourceError("expanded input exceeds byte limit")
        buffer += chunk
        eof = not chunk

    def consume(count):
        nonlocal buffer, consumed_bytes
        consumed_bytes += len(buffer[:count].encode("utf-8"))
        buffer = buffer[count:]

    def whitespace():
        while True:
            consume(len(buffer) - len(buffer.lstrip()))
            if buffer or eof:
                return
            fill()

    fill()
    whitespace()
    if not buffer.startswith("["):
        raise SourceError("expected JSON array")
    consume(1)
    first = True
    while True:
        whitespace()
        if buffer.startswith("]"):
            consume(1)
            whitespace()
            if buffer or not eof:
                raise SourceError("trailing data after JSON array")
            return
        if not first:
            if not buffer.startswith(","):
                raise SourceError("expected array separator")
            consume(1)
            whitespace()
            if buffer.startswith("]"):
                raise SourceError("trailing comma in JSON array")
        if not buffer:
            raise SourceError("truncated JSON array")
        while True:
            try:
                _, end = decoder.raw_decode(buffer)
                break
            except json.JSONDecodeError as exc:
                if eof or len(buffer.encode("utf-8")) >= max_record_bytes:
                    raise SourceError(f"corrupt or oversized JSON array record {index + 1}") from exc
                fill()
        raw = buffer[:end].encode("utf-8")
        if len(raw) > max_record_bytes:
            raise SourceError("array record exceeds byte limit")
        index += 1
        yield decode_record(index, consumed_bytes, raw, "json_array")
        consume(end)
        first = False


def iter_records(path, max_record_bytes=None, max_uncompressed_bytes=None):
    """Yield source records; malformed JSONL rows remain visible as error envelopes.

    JSONL hashes cover the exact line including its terminator. Array hashes cover
    each exact JSON value, excluding the surrounding commas and array whitespace.
    Offsets are byte offsets in the uncompressed source.
    """
    max_record_bytes = max_record_bytes or RECIPE["limits"]["record_bytes"]
    max_uncompressed_bytes = max_uncompressed_bytes or RECIPE["limits"]["uncompressed_bytes"]
    with Path(path).open("rb") as raw:
        magic = raw.read(2)
        raw.seek(0)
        stream = io.BufferedReader(gzip.GzipFile(fileobj=raw)) if magic == b"\x1f\x8b" else raw
        try:
            if stream.peek(4096).lstrip().startswith(b"["):
                yield from _array_records(stream, max_record_bytes, max_uncompressed_bytes)
                return
            offset, index = 0, 0
            while True:
                line = stream.readline(max_record_bytes + 1)
                if not line:
                    return
                if len(line) > max_record_bytes:
                    raise SourceError("JSONL record exceeds byte limit")
                if offset + len(line) > max_uncompressed_bytes:
                    raise SourceError("expanded input exceeds byte limit")
                index += 1
                yield decode_record(index, offset, line, "jsonl")
                offset += len(line)
        except (OSError, EOFError, UnicodeError) as exc:
            raise SourceError(f"corrupt archive or text: {exc}") from exc
        finally:
            stream.close()


def split_identity(oracle_id, seed=None):
    if not isinstance(oracle_id, str) or not oracle_id:
        return None
    digest = sha256(((seed or RECIPE["seed"]) + "\0" + oracle_id).encode())
    return "holdout" if int(digest[:8], 16) % 100 < 20 else "development"


def paragraph_signals(text):
    """Heuristic nomination only: no full Oracle grammar or semantic inference."""
    found, position = [], 0
    for paragraph in text.splitlines(keepends=True):
        stripped = paragraph.rstrip("\r\n")
        if ":" in stripped:
            cost, effect = stripped.split(":", 1)
            if ADD.search(effect) and MANA.search(effect):
                cost_terms = [m.group() for m in LIBRARY.finditer(cost)]
                effect_terms = [m.group() for m in LIBRARY.finditer(effect)]
                if cost_terms or effect_terms:
                    location = "both" if cost_terms and effect_terms else "cost" if cost_terms else "effect"
                    ambiguity = ["text pattern does not prove library movement or ability ownership"]
                    if any(q in stripped for q in ('"', "\u201c", "\u201d")):
                        ambiguity.append("quoted or granted ability may not belong to this permanent")
                    if cost.count(":") or effect.count(":"):
                        ambiguity.append("multiple colons in paragraph")
                    found.append({
                        "kind": "mana_with_potential_library_movement",
                        "strength": "weak", "family": "mana_library_" + location,
                        "movement_location": location,
                        "cost_text": cost, "effect_text": effect,
                        "cost_terms": cost_terms, "effect_terms": effect_terms,
                        "paragraph": stripped, "character_span": [position, position + len(stripped)],
                        "mentions_target": bool(re.search(r"\btarget\b", stripped, re.I)),
                        "ambiguities": ambiguity,
                        "semantic_verdict": "not_evaluated",
                    })
        position += len(paragraph)
    return found


def classify_card(card, seed=None):
    exclusions = []
    if card.get("object") != "card":
        exclusions.append("object_not_card")
    for key in ("oracle_id", "id"):
        if not isinstance(card.get(key), str) or not card.get(key):
            exclusions.append("missing_" + key)
    if card.get("layout") != "normal":
        exclusions.append("layout_not_normal")
    games = card.get("games")
    if not isinstance(games, list) or "paper" not in games:
        exclusions.append("representative_printing_not_paper")
    legalities = card.get("legalities")
    vintage = legalities.get("vintage") if isinstance(legalities, dict) else None
    if vintage not in ("legal", "restricted"):
        exclusions.append("vintage_not_legal_or_restricted")
    text = card.get("oracle_text")
    if text is not None and not isinstance(text, str):
        exclusions.append("oracle_text_not_string")
    signals = paragraph_signals(text) if isinstance(text, str) else []
    faces = card.get("card_faces")
    face_ids = [f.get("oracle_id") for f in faces if isinstance(f, dict)] if isinstance(faces, list) else []
    return {
        "oracle_id": card.get("oracle_id"), "printing_id": card.get("id"),
        "face_oracle_ids": face_ids, "name": card.get("name"), "layout": card.get("layout"),
        "eligible": not exclusions, "exclusion_reasons": exclusions,
        "split": split_identity(card.get("oracle_id"), seed),
        "oracle_text_length": len(text) if isinstance(text, str) else 0,
        "scryfall_uri": card.get("scryfall_uri"),
        "signals": signals, "semantic_verdict": "not_evaluated",
        "import_audit": "source_record_decoded_only; Phase import and runtime not evaluated",
    }


def scan_snapshot(snapshot_dir, output_dir):
    snapshot_dir, output_dir = Path(snapshot_dir), Path(output_dir)
    manifest = verify_snapshot(snapshot_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    raw_dir = output_dir / "raw-candidates"
    raw_dir.mkdir()
    counts, exclusions, layouts, split_counts = Counter(), Counter(), Counter(), Counter()
    families, candidates, selected_cards, identities = {}, [], {}, set()
    report = {
        "schema_version": 1, "status": "running", "started_at": now(), "recipe": RECIPE,
        "producer": source_revision(), "source_manifest_sha256": file_sha256(snapshot_dir / "source-manifest.json"),
        "source_archive_sha256": manifest["artifacts"]["archive"]["sha256"],
        "interpretation": "Whole-snapshot source audit and weak nomination. No Phase import, gameplay failure, patch, or improvement is claimed.",
    }
    write_json(output_dir / "report.json", report)
    try:
        with (output_dir / "discovery.jsonl").open("wb") as audit:
            for record in iter_records(snapshot_dir / manifest["artifacts"]["archive"]["path"]):
                counts["source_rows"] += 1
                entry = {
                    "source_index": record.index, "uncompressed_byte_offset": record.offset,
                    "raw_record_sha256": sha256(record.raw), "raw_record_bytes": len(record.raw),
                    "source_format": record.source_format, "source_decode_error": record.error,
                }
                if record.card is None:
                    entry.update(oracle_id=None, printing_id=None, layout=None, eligible=False,
                                 exclusion_reasons=["source_decode_error"], split=None,
                                 signals=[], semantic_verdict="not_evaluated")
                    counts["source_decode_errors"] += 1
                else:
                    entry.update(classify_card(record.card))
                    counts["decoded_records"] += 1
                    if isinstance(entry["oracle_id"], str) and entry["oracle_id"]:
                        identities.add(entry["oracle_id"])
                layouts[str(entry["layout"])] += 1
                exclusions.update(entry["exclusion_reasons"])
                counts["eligible_records" if entry["eligible"] else "excluded_records"] += 1
                if entry.get("split"):
                    split_counts[entry["split"]] += 1
                if entry["signals"]:
                    counts["all_weak_signal_records"] += 1
                if entry["eligible"] and entry["signals"]:
                    counts["eligible_weak_candidate_records"] += 1
                    raw_path = raw_dir / f'{record.index:06d}.json'
                    raw_path.write_bytes(record.raw)
                    entry["raw_record_path"] = str(raw_path.relative_to(output_dir))
                    candidates.append(entry)
                    selected_cards[record.index] = record.card
                    for family in {s["family"] for s in entry["signals"]}:
                        families.setdefault(family, set()).add(entry["oracle_id"])
                audit.write(canonical(entry) + b"\n")
        family_order = sorted(families, key=lambda f: (-len(families[f]), f))
        family_rank = {name: rank for rank, name in enumerate(family_order, 1)}
        for entry in candidates:
            entry["primary_family"] = min({s["family"] for s in entry["signals"]}, key=family_rank.get)
            entry["family_rank"] = family_rank[entry["primary_family"]]
        candidates.sort(key=lambda e: (
            e["family_rank"], e["oracle_text_length"],
            sha256((RECIPE["seed"] + "\0" + e["oracle_id"]).encode()),
            e["printing_id"], e["source_index"]))
        with (output_dir / "candidates.jsonl").open("wb") as ranked, (output_dir / "selected-records.jsonl").open("wb") as selected:
            for rank, entry in enumerate(candidates, 1):
                entry["rank"] = rank
                ranked.write(canonical(entry) + b"\n")
                selected.write(canonical(selected_cards[entry["source_index"]]) + b"\n")
        counts["distinct_oracle_ids"] = len(identities)
        for key in ("source_decode_errors", "eligible_weak_candidate_records", "all_weak_signal_records"):
            counts.setdefault(key, 0)
        report.update(
            status="complete_with_input_errors" if counts["source_decode_errors"] else "complete",
            completed_at=now(), counts=dict(counts), exclusion_counts=dict(exclusions),
            layout_counts=dict(layouts), split_counts=dict(split_counts),
            families=[{"family": f, "rank": family_rank[f], "distinct_eligible_oracle_ids": len(families[f])} for f in family_order],
            candidate_split_counts=dict(Counter(e["split"] for e in candidates)),
            representative_ranks=[e["rank"] for e in candidates[:10]],
            selected_records_note="All ranked weak candidates, reserialized as JSONL for import. Exact source bytes are retained at each candidate's raw_record_path.",
            artifacts={name: {"sha256": file_sha256(output_dir / name), "bytes": (output_dir / name).stat().st_size}
                       for name in ("discovery.jsonl", "candidates.jsonl", "selected-records.jsonl")},
        )
    except Exception as exc:
        report.update(status="failed", failed_at=now(), error=str(exc), partial_counts=dict(counts))
        write_json(output_dir / "report.json", report)
        raise
    write_json(output_dir / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch")
    fetch.add_argument("--output-dir", type=Path, required=True)
    fetch.add_argument("--include-rules", action="store_true")
    scan = commands.add_parser("scan")
    scan.add_argument("--snapshot-dir", type=Path, required=True)
    scan.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "fetch":
        result = fetch_snapshot(args.output_dir, include_rules=args.include_rules)
    else:
        result = scan_snapshot(args.snapshot_dir, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
