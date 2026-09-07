#!/usr/bin/env python3
"""Frozen independent source-schema coverage evaluator; no gameplay oracle.

This module consumes source CSV and official mapping bytes. It never imports the
native miner or reads its patch. Unknown source schemas/IDs remain inconclusive.
"""
from __future__ import annotations
from collections import Counter
import csv
import hashlib
import io
import json
import re

SCHEMA = "17lands-public-replay-wide-v1"
NATIVE_SCHEMA = "coworld-mtg-17lands-soft-signals-v1"
ENVELOPE = "software-factory-result-v1"
CLAIM = "The native miner preserves every listed cast occurrence, Arena identity, mapped card name and input row in the frozen public wide CSV partitions. This does not establish gameplay order or rules correctness."
METHOD = "Independent exact CSV column/token census and official Arena mapping, compared with retained native output"
EVALUATOR = "Independent 17Lands source coverage"
CAST = re.compile(r"^(user|oppo)_turn_([1-9][0-9]*)_(creatures_cast|non_creatures_cast|(user|oppo)_instants_sorceries_cast)$")
ID = re.compile(r"^[1-9][0-9]*$")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON value: " + value)
    value = json.loads(data.decode("utf-8"), object_pairs_hook=unique, parse_constant=invalid)
    json.dumps(value, allow_nan=False)  # Also rejects exponent overflow.
    return value


def decode_native(data):
    report = strict_json(data)
    if not isinstance(report, dict) or report.get("schema") != NATIVE_SCHEMA:
        raise ValueError("unsupported native miner report schema")
    if type(report.get("rows")) is not int or report["rows"] < 0:
        raise ValueError("native report lacks a nonnegative integer row count")
    if not isinstance(report.get("card_frequency"), list):
        raise ValueError("native report lacks card_frequency")
    return {"schema": ENVELOPE, "summary": "Recorded native 17Lands importer output; counters are observations, not an acceptance decision.", "data": report}


def csv_records(data):
    text = data.decode("utf-8")
    physical = text.splitlines(keepends=True)
    reader = csv.reader(physical, strict=True)
    rows = []
    raw_rows = []
    previous = 0
    for row in reader:
        rows.append(row)
        raw_rows.append("".join(physical[previous:reader.line_num]).encode("utf-8"))
        previous = reader.line_num
    if not rows or len(set(rows[0])) != len(rows[0]):
        raise ValueError("missing or duplicate CSV header")
    if any(len(row) != len(rows[0]) for row in rows[1:]):
        raise ValueError("CSV row width differs from header")
    return rows[0], rows[1:], raw_rows


def slice_csv(data, first, last):
    _, rows, raw = csv_records(data)
    if not 1 <= first <= last <= len(rows):
        raise ValueError("CSV selection outside complete source rows")
    return raw[0] + b"".join(raw[first:last + 1])


def source_expectation(source, mapping):
    """Return counts plus every occurrence, or explicit unqualified reasons."""
    problems = []
    try:
        header, rows, _ = csv_records(source)
        map_header, map_rows, _ = csv_records(mapping)
    except (ValueError, UnicodeError, csv.Error) as error:
        return {"qualified": False, "problems": [str(error)], "source_sha256": digest(source), "mapping_sha256": digest(mapping)}
    columns = [(i, CAST.fullmatch(name)) for i, name in enumerate(header) if CAST.fullmatch(name)]
    if not rows or not columns or "draft_id" not in header or "game_number" not in header:
        problems.append("unknown wide source schema")
    if any(name.lower().endswith("_cast") and not CAST.fullmatch(name) and not re.fullmatch(r"(user|oppo)_total_(creatures_cast|non_creatures_cast|instants_sorceries_cast)", name) for name in header):
        problems.append("unrecognized cast-related column")
    if "id" not in map_header or "name" not in map_header:
        problems.append("unknown official mapping schema")
        cards = {}
    else:
        cards = {}
        for record in map_rows:
            identity, name = record[map_header.index("id")], record[map_header.index("name")]
            if not ID.fullmatch(identity) or not name.strip():
                problems.append("invalid official mapping row")
                continue
            identity = int(identity)
            if identity in cards and cards[identity] != name:
                problems.append("conflicting duplicate Arena mapping")
            cards[identity] = name
    casts = []
    frequencies = Counter()
    for row_number, row in enumerate(rows, 1):
        for index, match in columns:
            value = row[index]
            if not value:
                continue
            for value_index, raw_id in enumerate(value.split("|")):
                token = raw_id
                arena_id = int(token) if re.fullmatch(r"[0-9]+", token) and 0 < int(token) <= 2**32 - 1 else None
                if arena_id is None:
                    resolution = {"status": "invalid", "reason": "expected_positive_decimal_arena_id"}
                    problems.append("invalid cast Arena ID")
                elif arena_id not in cards:
                    resolution = {"status": "unmapped", "reason": "unknown_arena_id"}
                    problems.append("unmapped cast Arena ID")
                else:
                    resolution = {"status": "mapped", "name": cards[arena_id]}
                    frequencies[cards[arena_id]] += 1
                active, turn, family, casting = match.groups()
                casts.append({"row": row_number, "column": header[index], "value_index": value_index,
                              "raw_id": raw_id, "arena_id": arena_id, "turn_number": int(turn),
                              "active_player": active, "casting_player": casting or active,
                              "cast_kind": {"creatures_cast": "creature", "non_creatures_cast": "non_creature"}.get(family, "instant_sorcery"),
                              "resolution": resolution})
    counts = Counter(item["resolution"]["status"] for item in casts)
    valid_ids = {item["arena_id"] for item in casts if item["arena_id"] is not None}
    mapped_ids = {item["arena_id"] for item in casts if item["resolution"]["status"] == "mapped"}
    return {"qualified": not problems, "problems": sorted(set(problems)),
            "source_sha256": digest(source), "mapping_sha256": digest(mapping), "rows": len(rows),
            "normalization": {"schema": SCHEMA, "cast_occurrences": len(casts),
                "mapped_cast_occurrences": counts["mapped"], "unmapped_cast_occurrences": counts["unmapped"],
                "invalid_cast_occurrences": counts["invalid"], "distinct_cast_arena_ids": len(valid_ids),
                "distinct_mapped_cast_arena_ids": len(mapped_ids), "casts": casts},
            "card_frequency": [{"name": name, "count": count} for name, count in sorted(frequencies.items(), key=lambda pair: (-pair[1], pair[0]))]}


def evaluate(expected, observation, manifest_id):
    """Transport/schema uncertainty is inconclusive; measured mismatch violates."""
    def result(verdict, reason):
        return {"result": verdict, "reason": reason, "expected_rows": expected.get("rows"),
                "expected_cast_occurrences": expected.get("normalization", {}).get("cast_occurrences"),
                "expected_distinct_cast_arena_ids": expected.get("normalization", {}).get("distinct_cast_arena_ids")}
    if not expected["qualified"]:
        return result("inconclusive", "Source is outside the frozen schema/mapping contract: " + "; ".join(expected["problems"]))
    if not isinstance(observation, dict) or observation.get("schema") != ENVELOPE:
        return result("inconclusive", "No supported successful native observation")
    report = observation.get("data", {})
    if report.get("schema") != NATIVE_SCHEMA or report.get("dataset_sha256") != expected["source_sha256"] or report.get("manifest_id") != manifest_id:
        return result("inconclusive", "Native report source/manifest identity or schema differs")
    if type(report.get("rows")) is not int or report["rows"] != expected["rows"]:
        return result("inconclusive", "Native report does not cover every frozen input row")
    normalization = report.get("normalization")
    if "normalization" in report and (not isinstance(normalization, dict) or normalization.get("schema") != SCHEMA):
        return result("inconclusive", "Unknown or malformed native normalization schema")
    if json.dumps(report.get("card_frequency"), sort_keys=True) != json.dumps(expected["card_frequency"], sort_keys=True):
        return result("violated", "Native card frequency does not preserve independently mapped source cast occurrences")
    if not isinstance(normalization, dict):
        return result("inconclusive", "Native output lacks auditable cast identity normalization")
    mapping = normalization.get("cards_mapping", {})
    if not isinstance(mapping, dict) or mapping.get("sha256") != expected["mapping_sha256"]:
        return result("inconclusive", "Native official mapping identity differs")
    observed = {key: normalization.get(key) for key in expected["normalization"]}
    # Serialized JSON comparison distinguishes booleans from integer measurements.
    if json.dumps(observed, sort_keys=True) != json.dumps(expected["normalization"], sort_keys=True):
        return result("violated", "Native normalization changes a source cast occurrence, identity, role or count")
    return result("satisfied", "Every source cast occurrence, mapped identity, count and input row is preserved")
