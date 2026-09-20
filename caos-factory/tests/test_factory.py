import copy, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"lib"))
from contracts import Bounds, Plan, Review
from evaluate import apply_edits, compare_pair

class TrustBoundaries(unittest.TestCase):
    def test_edits_cannot_escape_or_guess_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"target.rs").write_text("one\none\n")
            for edit in (
                {"path":"../target.rs","old":"one","new":"two"},
                {"path":"policy.json","old":"one","new":"two"},
                {"path":"target.rs","old":"one","new":"two"},
                {"path":"target.rs","old":"missing","new":"two"},
            ):
                with self.subTest(edit=edit),self.assertRaises(ValueError):
                    apply_edits(root,[edit],["target.rs"])
            self.assertEqual((root/"target.rs").read_text(),"one\none\n")
            (root/"target.rs").chmod(0o444)
            apply_edits(root,[{"path":"target.rs","old":"one\none\n","new":"two\n"}],["target.rs"])
            self.assertEqual((root/"target.rs").read_text(),"two\n")

    def pair(self):
        value={"case_id":"real-row-8","status":"matched_supported_projection","nodes":100,
            "milestones_fitted":2,"milestones_total":4,"fully_covered_milestones":0,
            "enforced_fields":["life"],"field_contracts":{"life":{"raw":"17","disposition":"enforced","projection":"life","expected":17}},
            "assumptions":["fixed library"],"execution":"completed"}
        return value,copy.deepcopy(value)

    def test_faster_compatible_search_counts_but_noise_does_not(self):
        a,b=self.pair();self.assertFalse(compare_pair(a,b)["improved"])
        b["nodes"]=50;self.assertTrue(compare_pair(a,b)["improved"])
        b["status"]="external_deadline";b["execution"]="external_deadline"
        self.assertFalse(compare_pair(a,b)["improved"])

    def test_lost_checks_and_forged_observations_cannot_improve(self):
        for mutation in ("drop","raw","expected","projection","weaken"):
            a,b=self.pair();b["nodes"]=50
            if mutation=="drop":b["field_contracts"].clear()
            elif mutation=="weaken":b["field_contracts"]["life"]["disposition"]="unsupported"
            else:b["field_contracts"]["life"][mutation]="changed"
            with self.subTest(mutation=mutation):
                self.assertFalse(compare_pair(a,b)["improved"])
                self.assertTrue(compare_pair(a,b)["reasons"])

    def test_unreported_deadline_progress_is_not_zero(self):
        a,b=self.pair()
        a.update(status="external_deadline",execution="external_deadline",nodes=None,milestones_fitted=None,fully_covered_milestones=None)
        b.update(status="budget_exhausted",milestones_fitted=1)
        self.assertFalse(compare_pair(a,b)["improved"])
        b["status"]="matched_supported_projection"
        self.assertTrue(compare_pair(a,b)["improved"])

    def test_model_types_fail_closed(self):
        for approve in ("true",1,None):
            with self.assertRaises(ValueError):Review.parse({"approve":approve,"findings":[],"rationale":"x"})
        with self.assertRaises(ValueError):Review.parse({"approve":True,"findings":[],"rationale":"x","override_policy":True})
        with self.assertRaises(ValueError):Plan.parse({"status":"propose"})

    def test_bounds_do_not_accept_booleans_or_unbounded_fanout(self):
        value=dict(nodes=10,max_actions=128,turn_pairs=2,deadline_seconds=60,memory_bytes=4096,
            concurrency=2,max_model_calls=4,max_candidate_attempts=1)
        Bounds.parse(value)
        for key,bad in (("concurrency",True),("concurrency",20),("max_actions",513),("nodes",0)):
            with self.subTest(key=key),self.assertRaises(ValueError):Bounds.parse({**value,key:bad})

if __name__=="__main__":unittest.main()
