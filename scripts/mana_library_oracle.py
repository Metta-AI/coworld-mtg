#!/usr/bin/env python3
"""Conservative source-derived oracle for CR 605.1a mana-ability classification.

This is a bounded grammar, not a Magic interpreter. Source qualification is
frozen before inspecting classifier outcomes; an AST mismatch blocks a qualified
gate rather than silently removing the case. It does not certify runtime play.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess

from scryfall_source import (
    RECIPE as DISCOVERY_RECIPE, RULES_EXPECTED_SHA256, RULES_URL, SourceError,
    canonical, classify_card, file_sha256, iter_records, now, sha256, split_identity,
    verify_snapshot, write_json,
)

ORACLE_RECIPE = {
    "version": 1,
    "scope": "Activated ability classification under current CR605.1a; no runtime semantics certified.",
    "source_grammar": {
        "costs": ["fixed mana symbols", "{T}", "Mill a fixed positive number of cards",
                  "Sacrifice this artifact/creature/permanent"],
        "effects": ["Add a fixed sequence of WUBRGC mana symbols",
                    "Add one mana of any color", "Draw a fixed positive number of cards",
                    "Mill a fixed positive number of cards"],
        "structure": "Whole unquoted paragraph; mana is the first effect; all source syntax accounted for.",
        "reminder": "Remove balanced parentheses, retaining the original paragraph as evidence.",
        "unsupported": "Unknown syntax, conditional/delayed/granted/targeted/loyalty abilities remain inconclusive.",
    },
    "controls": {
        "population": "Full eligible source corpus excluding all discovered Oracle IDs",
        "source_predicate": "Artifact or land; one complete paragraph exactly {T}: Add one WUBRGC mana symbol.",
        "strata": "Each mana symbol separately in development and holdout",
        "selection": "Lowest sha256(discovery seed NUL oracle_id) in each nonempty stratum; at most 12",
    },
    "gate": {
        "eligibility": "Source grammar only; frozen before classifier/AST observations.",
        "primary": "First ranked source-qualified development discovery candidate",
        "regression": "Other source-qualified development discovery candidates and development controls",
        "holdout": "Source-qualified holdout discovery candidates and holdout controls",
        "inconclusive": "A prequalified gate with missing or unaligned AST blocks acceptance; never drop it.",
        "required_nonempty": ["primary", "regression", "holdout"],
    },
    "rules": {
        "url": RULES_URL, "sha256": RULES_EXPECTED_SHA256, "effective_date": "2026-08-07",
        "filename_date": "2026-08-19",
        "references": ["605.1a", "602.1", "207.2a", "121.1", "701.17a"],
    },
}
NUMBERS = {"a": 1, "one": 1, "two": 2, "three": 3, "four": 4,
           "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
COUNT = r"(a|one|two|three|four|five|six|seven|eight|nine|ten|[1-9][0-9]?)"


def strip_reminder(text):
    result, depth = [], 0
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                raise SourceError("unmatched closing parenthesis")
            depth -= 1
        elif depth == 0:
            result.append(char)
    if depth:
        raise SourceError("unmatched opening parenthesis")
    return "".join(result).strip()


def number(value):
    return NUMBERS[value] if value in NUMBERS else int(value)


def parse_cost(text):
    result = {"mana_symbols": [], "tap": False, "mill_cards": 0, "sacrifice_self": False}
    for component in text.split(","):
        component = component.strip()
        if component == "{T}" and not result["tap"]:
            result["tap"] = True
        elif re.fullmatch(r"(?:\{(?:[0-9]+|[WUBRGC])\})+", component):
            result["mana_symbols"].extend(re.findall(r"\{([^}]+)\}", component))
        elif match := re.fullmatch(r"Mill " + COUNT + r" cards?", component):
            if result["mill_cards"]:
                raise SourceError("multiple milling cost components")
            result["mill_cards"] = number(match.group(1))
        elif re.fullmatch(r"Sacrifice this (?:artifact|creature|permanent)", component) and not result["sacrifice_self"]:
            result["sacrifice_self"] = True
        else:
            raise SourceError("unsupported or ambiguous cost component: " + component)
    if not result["tap"]:
        raise SourceError("bounded grammar requires an explicit tap cost")
    return result


def parse_effects(text):
    timing = "Activate only as an instant."
    if text.endswith(timing):
        text = text[:-len(timing)].strip()
    effects = []
    while text:
        if match := re.match(r"Add ((?:\{[WUBRGC]\})+)\.(?:\s+|$)", text):
            effects.append({"kind": "mana", "symbols": re.findall(r"\{([WUBRGC])\}", match.group(1))})
        elif match := re.match(r"Add one mana of any color\.(?:\s+|$)", text):
            effects.append({"kind": "mana", "any_color": True, "amount": 1})
        elif match := re.match(r"Draw " + COUNT + r" cards?\.(?:\s+|$)", text):
            effects.append({"kind": "draw", "amount": number(match.group(1))})
        elif match := re.match(r"Mill " + COUNT + r" cards?\.(?:\s+|$)", text):
            effects.append({"kind": "mill", "amount": number(match.group(1))})
        else:
            raise SourceError("unsupported or ambiguous effect/timing text: " + text)
        text = text[match.end():]
    if not effects or effects[0]["kind"] != "mana":
        raise SourceError("bounded grammar requires mana production as the first effect")
    return effects


def source_contracts(card):
    result = {"oracle_id": card.get("oracle_id"), "printing_id": card.get("id"),
              "source_card_sha256": sha256(canonical(card)), "rules": ORACLE_RECIPE["rules"],
              "abilities": [], "strong_gate": False, "reasons": []}
    if not classify_card(card)["eligible"]:
        result["reasons"].append("source card is outside the frozen eligible cohort")
        return result
    text = card.get("oracle_text")
    if not isinstance(text, str):
        result["reasons"].append("missing source Oracle text")
        return result
    result["oracle_text_sha256"] = sha256(text.encode())
    paragraph_count = 0
    for paragraph_index, original in enumerate(text.splitlines()):
        try:
            paragraph = strip_reminder(original)
        except SourceError as exc:
            result["reasons"].append(str(exc))
            return result
        if not paragraph:
            continue
        paragraph_count += 1
        if ":" not in paragraph:
            result["reasons"].append("additional unaccounted source paragraph")
            continue
        entry = {"paragraph_index": paragraph_index, "source_paragraph": original,
                 "normalized_paragraph": paragraph, "status": "inconclusive", "reasons": []}
        result["abilities"].append(entry)
        try:
            if any(quote in paragraph for quote in ('"', "\u201c", "\u201d")):
                raise SourceError("quoted or granted text does not establish an own activated ability")
            if paragraph.count(":") != 1:
                raise SourceError("multiple colons prevent unambiguous ability matching")
            cost_text, effect_text = paragraph.split(":", 1)
            cost, effects = parse_cost(cost_text.strip()), parse_effects(effect_text.strip())
            library = cost["mill_cards"] > 0 or any(e["kind"] in ("draw", "mill") for e in effects)
            entry.update(status="supported", cost=cost, effects=effects,
                         expected_is_mana_ability=not library,
                         library_movement={"cost": cost["mill_cards"] > 0,
                                           "effect": any(e["kind"] in ("draw", "mill") for e in effects)})
        except SourceError as exc:
            entry["reasons"].append(str(exc))
    # Complete source coverage makes activation-order matching conservative.
    result["strong_gate"] = bool(result["abilities"]) and not result["reasons"] and all(
        a["status"] == "supported" for a in result["abilities"])
    result["source_paragraph_count"] = paragraph_count
    if not result["abilities"]:
        result["reasons"].append("no supported own activated paragraph")
    return result


def control_symbol(card):
    if not classify_card(card)["eligible"]:
        return None
    if not re.search(r"\b(?:Artifact|Land)\b", card.get("type_line") or ""):
        return None
    text = card.get("oracle_text")
    if not isinstance(text, str) or len(text.splitlines()) != 1:
        return None
    try:
        clean = strip_reminder(text)
    except SourceError:
        return None
    match = re.fullmatch(r"\{T\}: Add \{([WUBRGC])\}\.", clean)
    return match.group(1) if match else None


def oracle_revision():
    root = Path(__file__).resolve().parents[1]
    revision = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True)
    return {"git_revision": revision.stdout.strip() if revision.returncode == 0 else None,
            "git_dirty": bool(dirty.stdout.strip()),
            "evaluator_sha256": file_sha256(Path(__file__)),
            "recipe_sha256": sha256(canonical(ORACLE_RECIPE))}


def freeze_plan(snapshot_dir, discovery_dir, output_dir):
    snapshot_dir, discovery_dir, output_dir = map(Path, (snapshot_dir, discovery_dir, output_dir))
    manifest = verify_snapshot(snapshot_dir)
    if manifest["artifacts"].get("rules", {}).get("sha256") != RULES_EXPECTED_SHA256:
        raise SourceError("plan requires the exact independently pinned rules source")
    discovery = json.loads((discovery_dir / "report.json").read_text())
    if discovery["source_archive_sha256"] != manifest["artifacts"]["archive"]["sha256"]:
        raise SourceError("discovery and source archive differ")
    candidates_path = discovery_dir / "candidates.jsonl"
    if file_sha256(candidates_path) != discovery["artifacts"]["candidates.jsonl"]["sha256"]:
        raise SourceError("candidate evidence hash mismatch")
    candidates = [json.loads(line) for line in candidates_path.read_text().splitlines()]
    candidate_ids = {candidate["oracle_id"] for candidate in candidates}
    controls = {}
    for record in iter_records(snapshot_dir / manifest["artifacts"]["archive"]["path"]):
        if record.card is None:
            raise SourceError("control selection cannot proceed through corrupted source rows")
        card = record.card
        if card.get("oracle_id") in candidate_ids:
            continue
        symbol = control_symbol(card)
        if symbol is None:
            continue
        split = split_identity(card["oracle_id"])
        key = (symbol, split)
        rank = sha256((DISCOVERY_RECIPE["seed"] + "\0" + card["oracle_id"]).encode())
        if key not in controls or rank < controls[key][0]:
            controls[key] = (rank, record)
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "raw-cards").mkdir()
    entries = []
    primary_chosen = False
    for candidate in candidates:
        raw = (discovery_dir / candidate["raw_record_path"]).read_bytes()
        if sha256(raw) != candidate["raw_record_sha256"]:
            raise SourceError("candidate raw source hash mismatch")
        card = json.loads(raw)
        if card.get("oracle_id") != candidate["oracle_id"] or card.get("id") != candidate["printing_id"]:
            raise SourceError("candidate source identity mismatch")
        contract = source_contracts(card)
        eligible = contract["strong_gate"]
        role = "queue_only"
        if eligible:
            if candidate["split"] == "holdout":
                role = "holdout"
            elif not primary_chosen:
                role, primary_chosen = "primary", True
            else:
                role = "regression"
        path = f'raw-cards/{candidate["source_index"]:06d}.json'
        (output_dir / path).write_bytes(raw)
        entries.append({
            "case_id": "mana-classification-" + card["oracle_id"],
            "oracle_id": card["oracle_id"], "printing_id": card["id"],
            "origin": "discovery", "discovery_rank": candidate["rank"], "split": candidate["split"],
            "role": role, "strong_gate": eligible, "raw_record_path": path,
            "raw_record_sha256": sha256(raw), "source_contract": contract,
        })
    for (symbol, split), (_, record) in sorted(controls.items()):
        card = record.card
        path = f'raw-cards/control-{record.index:06d}.json'
        (output_dir / path).write_bytes(record.raw)
        contract = source_contracts(card)
        if not contract["strong_gate"] or not all(a["expected_is_mana_ability"] for a in contract["abilities"]):
            raise SourceError("selected control violates source-only control contract")
        entries.append({
            "case_id": "mana-classification-" + card["oracle_id"],
            "oracle_id": card["oracle_id"], "printing_id": card["id"], "origin": "control",
            "control_symbol": symbol, "split": split, "role": "holdout" if split == "holdout" else "regression",
            "strong_gate": True, "raw_record_path": path, "raw_record_sha256": sha256(record.raw),
            "source_contract": contract,
        })
    counts = dict(Counter(entry["role"] for entry in entries))
    missing = [role for role in ("primary", "regression", "holdout") if not counts.get(role)]
    with (output_dir / "cases.jsonl").open("wb") as output:
        for entry in entries:
            output.write(canonical(entry) + b"\n")
    plan = {"schema_version": 1, "frozen_at": now(), "status": "ready" if not missing else "blocked",
            "blocking_reasons": ["empty required gate: " + role for role in missing],
            "recipe": ORACLE_RECIPE, "producer": oracle_revision(),
            "source_archive_sha256": manifest["artifacts"]["archive"]["sha256"],
            "discovery_report_sha256": file_sha256(discovery_dir / "report.json"),
            "counts": counts, "discovery_cases": len(candidates), "control_cases": len(controls),
            "cases_sha256": file_sha256(output_dir / "cases.jsonl"),
            "scope": "Only classification; source-qualified alignment failures block acceptance."}
    write_json(output_dir / "plan.json", plan)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("freeze-plan")
    plan.add_argument("--snapshot-dir", type=Path, required=True)
    plan.add_argument("--discovery-dir", type=Path, required=True)
    plan.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze_plan(args.snapshot_dir, args.discovery_dir, args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
