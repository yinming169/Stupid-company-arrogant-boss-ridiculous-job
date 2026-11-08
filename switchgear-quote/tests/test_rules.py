import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from copper_segments import calculate
from build_quote import build_standard
from classify import derive_copper, _power_prefix
from openpyxl import load_workbook

class RulesTest(unittest.TestCase):
    def segment(self, **kw):
        return dict({'id':'a','material':'铜','category':'主排','cabinet':'公共','phase':'ABC','width_mm':80,'thickness_mm':10,'length_m':4,'pieces':3,'parallel':1,'status':'估算','basis':'条件假设'}, **kw)
    def test_segment_math_and_no_double_pe(self):
        d=calculate({'voltage_class':'低压','segments':[self.segment(), self.segment(id='pe',category='PE',phase='PE',width_mm=30,thickness_mm=4,pieces=1)]})
        self.assertAlmostEqual(d['segments'][0]['weight_kg'],86.016)
        self.assertAlmostEqual(d['total_weight_kg'],90.3168)
        self.assertFalse(d['complete'])
    def test_incomplete_and_duplicate_rejected(self):
        for segments in ([],[self.segment(),self.segment()], [self.segment(length_m=0)]):
            with self.assertRaises(ValueError): calculate({'voltage_class':'低压','segments':segments})
        self.assertEqual(derive_copper([],None,2,[])[0],[])
    def test_power_not_confused(self):
        self.assertEqual(_power_prefix('软启动器90kW'),'')
        self.assertIn('75',_power_prefix('电机功率75kW'))
    def test_one_sheet_unknown_price(self):
        data={'cabinets':[{'id':'RQ1','count':1},{'id':'RQ2','count':1}], 'items':[{'cabinet':'RQ1','name':'软启','model':'规格','qty':2,'unit':'台','amount':None,'cost_amount':None},{'cabinet':'RQ2','name':'断路器','model':'规格','qty':1,'unit':'台','amount':None,'cost_amount':None}]}
        with tempfile.TemporaryDirectory() as d:
            f=os.path.join(d,'quote.xlsx'); build_standard(data,f); w=load_workbook(f); self.assertEqual(w.sheetnames,['分项报价表']); s=w.active
            self.assertEqual(s['A1'].value,'RQ1'); self.assertEqual(s['E1'].value,1); self.assertEqual(s['A9'].value,'RQ2'); self.assertIsNone(s['F3'].value)
            self.assertEqual(s['B3'].value,'材料小计'); self.assertIsNone(s['F3'].value)
if __name__=='__main__': unittest.main()
