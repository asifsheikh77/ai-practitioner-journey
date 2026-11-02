import unittest
from run_day36 import build_context, neighbors_for, metrics

class TestDay36(unittest.TestCase):
    def setUp(self):
        self.records = [
            {'chunk_id':'a','page_number':1,'kind':'narrative','text':'alpha beta'},
            {'chunk_id':'b','page_number':1,'kind':'narrative','text':'gamma delta'},
            {'chunk_id':'c','page_number':2,'kind':'narrative','text':'epsilon zeta'},
        ]
    def test_parent_stays_on_page(self):
        adj = neighbors_for(self.records)
        ids, used = build_context([{'chunk_id':'a'}],self.records,adj,4,True)
        self.assertEqual(ids,['a','b'])
        self.assertEqual(used,4)
        self.assertNotIn(2, adj.get(1,[]))
    def test_budget_excludes_overflow(self):
        ids, used = build_context([{'chunk_id':'a'},{'chunk_id':'b'}],self.records,{},3,False)
        self.assertEqual(ids,['a'])
        self.assertEqual(used,2)
    def test_facet_metrics(self):
        rubric=[{'id':'Q1','facets':[{'facet_id':'Q1.F1','v2_evidence_ids':['b']}]}]
        rankings={'Q1':[{'chunk_id':'a'}]}
        self.assertEqual(metrics(rubric,rankings,self.records,budgets=(4,),expand=True)['4']['facet_hit_rate'],1.0)
        self.assertEqual(metrics(rubric,rankings,self.records,budgets=(4,),expand=False)['4']['facet_hit_rate'],0.0)
if __name__ == '__main__': unittest.main()
