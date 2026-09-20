import sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"lib"))
import factory

class PlanningBudget(unittest.TestCase):
    def exercise(self, values, result, budget=6):
        def next_result(state, name):
            state[name]={"result":result}
            return True
        with patch.object(factory,"state",return_value=values), \
             patch.object(factory,"next_result",side_effect=next_result), \
             patch.object(factory.cas,"read_receipt",side_effect=lambda value:value), \
             patch.object(factory.cas,"load",return_value={"bounds":{"max_model_calls":budget}}), \
             patch.object(factory,"launch_role") as launch, \
             patch.object(factory,"finish") as finish:
            factory.planned()
            return launch.call_args,finish.call_args

    def test_invalid_schema_gets_feedback_once_then_stops(self):
        bad={"valid":False,"failure_kind":"invalid_response","error":"unknown component"}
        state={"policy":"frozen"}
        launched,finished=self.exercise(state,bad)
        self.assertIsNone(finished)
        self.assertEqual(launched.args[1:],("plan","planned"))
        self.assertEqual(state["prior-plan"]["result"],bad)
        launched,finished=self.exercise(state,bad)
        self.assertIsNone(launched)
        self.assertEqual(finished.args[1],"inconclusive")

    def test_provider_failure_is_not_a_schema_retry(self):
        launched,finished=self.exercise({"policy":"frozen"},
            {"valid":False,"failure_kind":"provider_error","error":"outage"})
        self.assertIsNone(launched)
        self.assertEqual(finished.args[1],"inconclusive")

    def test_smaller_budget_does_not_start_a_revision(self):
        launched,finished=self.exercise({"policy":"frozen"},
            {"valid":False,"failure_kind":"invalid_response","error":"bad JSON"},budget=4)
        self.assertIsNone(launched)
        self.assertEqual(finished.args[1],"inconclusive")

    def test_no_safe_change_does_not_start_a_review_or_candidate(self):
        launched,finished=self.exercise({"policy":"frozen"},
            {"valid":True,"value":{"status":"no_safe_change"}})
        self.assertIsNone(launched)
        self.assertEqual(finished.args[1],"no_change")

    def test_model_approval_cannot_override_failed_comparison(self):
        values={"comparison":{"result":{"passed":False}}}
        with patch.object(factory,"state",return_value=values), \
             patch.object(factory,"valid_role",return_value={"approve":True}), \
             patch.object(factory.cas,"read_receipt",side_effect=lambda value:value), \
             patch.object(factory,"finish") as finish:
            factory.reviewed()
        self.assertEqual(finish.call_args.args[1],"rejected")
        self.assertIn("frozen comparison",finish.call_args.args[2])

if __name__=="__main__":unittest.main()
