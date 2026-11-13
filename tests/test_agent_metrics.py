import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'starter'))
from agent_metrics import aggregate

class AgentMetricTests(unittest.TestCase):
    def test_counts_and_errors_are_separate(self):
        cases = [{'id':'a','answerable':True}, {'id':'b','answerable':False}, {'id':'c','answerable':True}]
        traces = [{'query_id':'a','status':'answered','events':[{'event':'search'}],'citations':['c1','c2']},
                  {'query_id':'b','status':'abstain','events':[{'event':'search'}],'citations':[]},
                  {'query_id':'c','status':'error','events':[],'citations':[]}]
        reviews = [{'query_id':'a','answer_grade':1,'citation_support':[True,False]},
                   {'query_id':'b','citation_support':[]}]
        result = aggregate(cases, traces, reviews)
        self.assertEqual(result['provider_errors'], 1)
        self.assertEqual(result['tool_use'], {'n':2,'N':2})
        self.assertEqual(result['citation_validity'], {'n':1,'N':2})
        self.assertEqual(result['abstention'], {'n':1,'N':1})
        self.assertEqual(result['grounded_answer']['mean'], 1)

    def test_rejects_missing_review_and_false_abstention_grade(self):
        cases = [{'id':'a','answerable':True}]
        traces = [{'query_id':'a','status':'abstain','events':[],'citations':[]}]
        with self.assertRaises(ValueError): aggregate(cases,traces,[])
        with self.assertRaises(ValueError): aggregate(cases,traces,[{'query_id':'a','answer_grade':2,'citation_support':[]}])

if __name__ == '__main__': unittest.main()
