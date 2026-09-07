import gzip
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import mana_library_oracle as oracle
import scryfall_source as source


def card(identity="example", text="{T}, Mill a card: Add {C}."):
    return {"object": "card", "oracle_id": identity, "id": "printing-" + identity,
            "name": "Unit-test source", "layout": "normal", "games": ["paper"],
            "legalities": {"vintage": "legal"}, "type_line": "Artifact",
            "oracle_text": text}


class SourceGrammarTests(unittest.TestCase):
    def test_cost_mill_reminder_is_not_effect_mill(self):
        result = oracle.source_contracts(card(text="{T}, Mill a card: Add {C}. (Activate only as an instant. To mill a card, put the top card of your library into your graveyard.)"))
        self.assertTrue(result["strong_gate"])
        ability = result["abilities"][0]
        self.assertEqual(ability["library_movement"], {"cost": True, "effect": False})
        self.assertEqual(ability["cost"]["mill_cards"], 1)
        self.assertFalse(ability["expected_is_mana_ability"])

    def test_direct_draw_and_mill_effects_are_distinct_from_costs(self):
        result = oracle.source_contracts(card(text="{2}, {T}, Sacrifice this artifact: Add {U}{B}. Draw a card. Mill two cards."))
        ability = result["abilities"][0]
        self.assertTrue(result["strong_gate"])
        self.assertEqual(ability["cost"]["mana_symbols"], ["2"])
        self.assertTrue(ability["cost"]["sacrifice_self"])
        self.assertEqual(ability["effects"], [
            {"kind": "mana", "symbols": ["U", "B"]}, {"kind": "draw", "amount": 1},
            {"kind": "mill", "amount": 2}])
        self.assertEqual(ability["library_movement"], {"cost": False, "effect": True})
        self.assertFalse(ability["expected_is_mana_ability"])

    def test_any_color_and_simple_control_expectations(self):
        result = oracle.source_contracts(card(text="{1}, {T}, Sacrifice this artifact: Add one mana of any color. Draw a card."))
        self.assertTrue(result["strong_gate"])
        self.assertEqual(result["abilities"][0]["effects"][0], {"kind": "mana", "any_color": True, "amount": 1})
        control = card(text="{T}: Add {G}.")
        self.assertTrue(oracle.source_contracts(control)["abilities"][0]["expected_is_mana_ability"])
        self.assertEqual(oracle.control_symbol(control), "G")
        self.assertIsNone(oracle.control_symbol(card(text="{T}: Add {G}{G}.")))

    def test_unknown_conditional_delayed_targeted_and_granted_forms_abstain(self):
        texts = [
            "{T}: Add {C} for each card you've drawn this turn.",
            "{T}: Add {G}. When you spend this mana, draw a card.",
            "{T}: Add {G}. Target player draws a card.",
            '{2}, {T}: Draw a card. Create a Treasure token. (It has "{T}: Add {G}.")',
            'Draw a card and create a token with "{T}: Add {C}."',
            "{T}, Mill a card: For each colored symbol in that card, add one mana of that color.",
            "+1: Add {R}. Draw a card.",
            "{T}: Add {C}. This mana can only pay for artifacts.",
            "{T}: Add {C}. (unclosed",
            "Other creatures have vigilance.\n{T}: Add {G}.",
        ]
        for text in texts:
            with self.subTest(text=text):
                result = oracle.source_contracts(card(text=text))
                self.assertFalse(result["strong_gate"])

    def test_multiple_own_abilities_keep_separate_expectations(self):
        result = oracle.source_contracts(card(text="{T}: Add {G}.\n{1}, {T}: Add {C}. Draw a card."))
        self.assertTrue(result["strong_gate"])
        self.assertEqual([a["expected_is_mana_ability"] for a in result["abilities"]], [True, False])
        self.assertEqual([a["paragraph_index"] for a in result["abilities"]], [0, 1])


class FrozenPlanTests(unittest.TestCase):
    def test_source_only_gate_and_stratified_controls_are_frozen(self):
        identities = {}
        for index in range(100):
            identity = "fixture-" + str(index)
            identities.setdefault(source.split_identity(identity), []).append(identity)
        dev, holdout = identities["development"], identities["holdout"]
        cards = [
            card(dev[0]),
            card(dev[1], "{T}: Add {C}. Draw a card."),
            card(holdout[0], "{T}: Add {C}. Draw a card."),
            card(dev[2], '{T}: Add {C} for each card you have drawn this turn.'),
        ]
        for index, identity in enumerate(dev[3:8] + holdout[1:6]):
            cards.append(card(identity, "{T}: Add {G}."))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = root / "snapshot"
            snapshot.mkdir()
            archive = snapshot / "cards.jsonl.gz"
            archive.write_bytes(gzip.compress(b"".join(source.canonical(c) + b"\n" for c in cards)))
            rules = snapshot / "rules.txt"
            rules.write_text("offline rules fixture")
            rules_hash = source.file_sha256(rules)
            manifest = {"status": "complete", "artifacts": {
                "archive": {"path": archive.name, "bytes": archive.stat().st_size, "sha256": source.file_sha256(archive)},
                "rules": {"path": rules.name, "bytes": rules.stat().st_size, "sha256": rules_hash}}}
            source.write_json(snapshot / "source-manifest.json", manifest)
            source.scan_snapshot(snapshot, root / "discovery")
            with patch.object(oracle, "RULES_EXPECTED_SHA256", rules_hash):
                result = oracle.freeze_plan(snapshot, root / "discovery", root / "plan")
            entries = [json.loads(line) for line in (root / "plan/cases.jsonl").read_text().splitlines()]
            self.assertEqual(result["status"], "ready")
            self.assertEqual(result["discovery_cases"], 4)
            self.assertEqual(result["control_cases"], 2)
            self.assertEqual(result["counts"], {"primary": 1, "regression": 2, "holdout": 2, "queue_only": 1})
            for entry in entries:
                self.assertEqual(entry["split"], source.split_identity(entry["oracle_id"]))
                self.assertEqual(entry["strong_gate"], entry["role"] != "queue_only")
                raw = (root / "plan" / entry["raw_record_path"]).read_bytes()
                self.assertEqual(source.sha256(raw), entry["raw_record_sha256"])
            controls = [entry for entry in entries if entry["origin"] == "control"]
            self.assertEqual({entry["split"] for entry in controls}, {"development", "holdout"})
            self.assertEqual(result["cases_sha256"], source.file_sha256(root / "plan/cases.jsonl"))
            with patch.object(oracle, "RULES_EXPECTED_SHA256", rules_hash):
                with self.assertRaises(FileExistsError):
                    oracle.freeze_plan(snapshot, root / "discovery", root / "plan")


def ast_ability(cost, produced, following=None, classified=True):
    return {
        "kind": "Activated", "cost": cost, "effect": {"type": "Mana", "produced": produced},
        "condition": None, "duration": None, "description": None, "forward_result": False,
        "optional": False, "optional_targeting": False, "target_prompt": None,
        "sub_ability": following, "is_mana_ability": classified,
    }


def draw_node():
    return {
        "kind": "Spell", "cost": None,
        "effect": {"type": "Draw", "count": {"type": "Fixed", "value": 1}, "target": {"type": "Controller"}},
        "condition": None, "duration": None, "description": None, "forward_result": False,
        "optional": False, "optional_targeting": False, "target_prompt": None,
        "sub_ability": None, "sub_link": "SequentialSibling",
    }


def inspection(raw, abilities):
    return {"status": "parsed", "card_id": raw["id"], "oracle_id": raw["oracle_id"],
            "phase_revision": "offline-test-revision",
            "parsed": {"abilities": abilities, "extractedKeywords": [], "replacements": [],
                       "statics": [], "triggers": []}}


class ASTAlignmentTests(unittest.TestCase):
    def egg(self):
        raw = card(text="{2}, {T}, Sacrifice this artifact: Add {U}{B}. Draw a card. (Activate only as an instant.)")
        cost = {"type": "Composite", "costs": [
            {"type": "Mana", "cost": {"type": "Cost", "generic": 2, "shards": []}},
            {"type": "Tap"}, {"type": "Sacrifice", "count": 1, "target": {"type": "SelfRef"}}]}
        node = ast_ability(cost, {"type": "Fixed", "colors": ["Blue", "Black"]}, draw_node())
        node["activation_restrictions"] = [{"type": "AsInstant"}]
        return raw, inspection(raw, [node])

    def test_mana_then_draw_aligns_before_classification_is_compared(self):
        raw, observed = self.egg()
        result = oracle.evaluate_card(raw, observed)
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["abilities"][0]["ast_alignment"], "aligned")
        self.assertFalse(result["abilities"][0]["expected_is_mana_ability"])
        self.assertTrue(result["abilities"][0]["observed_is_mana_ability"])
        observed["parsed"]["abilities"][0]["is_mana_ability"] = False
        result = oracle.evaluate_card(raw, observed)
        self.assertEqual(result["verdict"], "pass")
        self.assertFalse(result["gate_blocked"])

    def test_mill_cost_with_no_draw_subeffect_is_not_mistaken_for_mana_only(self):
        raw = card()
        node = ast_ability({"type": "Composite", "costs": [{"type": "Tap"}, {"type": "Mill", "count": 1}]},
                           {"type": "Colorless", "count": {"type": "Fixed", "value": 1}})
        result = oracle.evaluate_card(raw, inspection(raw, [node]))
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["abilities"][0]["ast_alignment"], "aligned")
        node["cost"]["costs"][1]["count"] = 2
        result = oracle.evaluate_card(raw, inspection(raw, [node]))
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertTrue(result["strong_gate"])
        self.assertTrue(result["gate_blocked"])

    def test_any_color_requires_all_five_options_and_exact_count(self):
        raw, observed = self.egg()
        raw["oracle_text"] = "{2}, {T}, Sacrifice this artifact: Add one mana of any color. Draw a card."
        produced = {"type": "AnyOneColor", "count": {"type": "Fixed", "value": 1},
                    "color_options": ["White", "Blue", "Black", "Red", "Green"]}
        observed["parsed"]["abilities"][0]["effect"]["produced"] = produced
        self.assertEqual(oracle.evaluate_card(raw, observed)["verdict"], "fail")
        produced["color_options"].remove("Red")
        self.assertEqual(oracle.evaluate_card(raw, observed)["verdict"], "inconclusive")

    def test_source_qualified_gates_are_not_dropped_when_alignment_fails(self):
        import copy
        raw, observed = self.egg()
        mutations = [
            lambda a: a.update(sub_ability=None),
            lambda a: a.update(optional=True),
            lambda a: a.update(condition={"type": "SomeCondition"}),
            lambda a: a["sub_ability"].update(sub_link="IfPaid"),
            lambda a: a["sub_ability"]["effect"].update(target={"type": "Opponent"}),
            lambda a: a.update(is_mana_ability=None),
            lambda a: a.update(unrecognized_effect_semantics=True),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = copy.deepcopy(observed)
                mutate(changed["parsed"]["abilities"][0])
                result = oracle.evaluate_card(raw, changed)
                self.assertEqual(result["verdict"], "inconclusive")
                self.assertTrue(result["strong_gate"])
                self.assertTrue(result["gate_blocked"])

    def test_identity_parse_and_ability_count_failures_block(self):
        import copy
        raw, observed = self.egg()
        for change in [{"status": "failed"}, {"oracle_id": "wrong"}, {"card_id": "wrong"}]:
            changed = dict(observed, **change)
            result = oracle.evaluate_card(raw, changed)
            self.assertEqual(result["verdict"], "inconclusive")
            self.assertTrue(result["gate_blocked"])
        changed = copy.deepcopy(observed)
        changed["parsed"]["abilities"] = []
        self.assertEqual(oracle.evaluate_card(raw, changed)["verdict"], "inconclusive")

    def test_simple_control_requires_correct_cost_and_mana_color(self):
        raw = card(text="{T}: Add {G}.")
        node = ast_ability({"type": "Tap"}, {"type": "Fixed", "colors": ["Green"]})
        result = oracle.evaluate_card(raw, inspection(raw, [node]))
        self.assertEqual(result["verdict"], "pass")
        self.assertTrue(result["abilities"][0]["expected_is_mana_ability"])
        node["effect"]["produced"]["colors"] = ["Red"]
        self.assertEqual(oracle.evaluate_card(raw, inspection(raw, [node]))["verdict"], "inconclusive")

    def test_multiple_abilities_align_individually_in_source_order(self):
        raw = card(text="{T}: Add {G}.\n{1}, {T}: Add {C}. Draw a card.")
        first = ast_ability({"type": "Tap"}, {"type": "Fixed", "colors": ["Green"]})
        second = ast_ability(
            {"type": "Composite", "costs": [
                {"type": "Mana", "cost": {"type": "Cost", "generic": 1, "shards": []}}, {"type": "Tap"}]},
            {"type": "Colorless", "count": {"type": "Fixed", "value": 1}}, draw_node(), classified=False)
        self.assertEqual(oracle.evaluate_card(raw, inspection(raw, [first, second]))["verdict"], "pass")
        swapped = oracle.evaluate_card(raw, inspection(raw, [second, first]))
        self.assertEqual(swapped["verdict"], "inconclusive")
        self.assertTrue(swapped["gate_blocked"])

    def test_unsupported_source_cannot_be_promoted_by_convincing_ast(self):
        raw, observed = self.egg()
        raw["oracle_text"] = "{T}: Add {G}. When you spend this mana, draw a card."
        result = oracle.evaluate_card(raw, observed)
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertFalse(result["strong_gate"])
        self.assertEqual(result["abilities"], [])


if __name__ == "__main__":
    unittest.main()
