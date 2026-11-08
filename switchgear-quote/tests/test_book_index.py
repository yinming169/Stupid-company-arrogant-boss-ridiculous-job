import math, pathlib, sqlite3, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
DB=ROOT/'knowledge'/'六份资料索引'/'pages.sqlite3'
class BookIndexTest(unittest.TestCase):
    def setUp(self): self.db=sqlite3.connect(DB)
    def tearDown(self): self.db.close()
    def test_expected_six_books(self):
        self.assertEqual(dict(self.db.execute('select book,page_count from books')),{'资料1':1684,'资料2':571,'资料3':445,'资料4':1039,'资料5':246,'资料6':38})
    def test_pages_in_range_and_motor_scanned_coverage(self):
        self.assertEqual(self.db.execute('select count(*) from pages p join books b on p.book=b.book where p.page<1 or p.page>b.page_count').fetchone()[0],0)
        self.assertEqual(self.db.execute("select count(distinct page) from pages where book='资料5'").fetchone()[0],246)
    def test_original_source_retrievable(self):
        text=self.db.execute('select text from pages where book=? and page=? and source=?',('资料5',195,'本次OCR/资料5')).fetchone()
        self.assertIsNotNone(text); self.assertIn('起动转矩',text[0])
    def test_compensation_example_sign(self):
        pre=math.tan(math.acos(.7)); post=math.tan(math.acos(.9)); self.assertGreater(100*(pre-post),0); self.assertAlmostEqual(100*(pre-post),53.59,delta=.1)
    def test_local_cards_and_origin(self):
        p=ROOT/'knowledge'/'cards'/'card-09-原图复核_压降与补偿.md'; t=p.read_text(encoding='utf8'); self.assertIn('原书符号与例题追查',t); self.assertIn('tanφ2−tanφ1',t)
if __name__=='__main__':unittest.main()
