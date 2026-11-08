"""核查索引页码和扫描书识别覆盖；不代表识别正确或内容已审校。"""
from pathlib import Path
import sqlite3
ROOT=Path(__file__).resolve().parents[1]/'knowledge'/'六份资料索引'
folder=ROOT/'ocr'/'资料5_电机与拖动基础'
files={int(p.stem[1:]):p for p in folder.glob('p*.txt') if p.stem[1:].isdigit()}
missing=sorted(set(range(31,247))-set(files)); short=[i for i,p in files.items() if len(p.read_text(encoding='utf8').strip())<80]
db=sqlite3.connect(ROOT/'pages.sqlite3'); count=db.execute("SELECT COUNT(DISTINCT page) FROM pages WHERE book=?",('资料5',)).fetchone()[0]
invalid=list(db.execute('SELECT p.book,p.page FROM pages p JOIN books b ON p.book=b.book WHERE p.page<1 OR p.page>b.page_count'))
extra=[]
for book,first,last in [('资料1',206,374),('资料4',171,214)]:
    pages={int(p.stem[1:]) for p in (ROOT/'ocr'/book).glob('p*.txt') if p.stem[1:].isdigit() and p.stat().st_size>50}
    missing_extra=sorted(set(range(first,last+1))-pages)
    indexed=db.execute('SELECT COUNT(DISTINCT page) FROM pages WHERE book=? AND source=?',(book,'本次OCR/'+book)).fetchone()[0]
    print(f'{book}: 本次OCR {len(pages)}页，索引{indexed}页，缺页{missing_extra}')
    if missing_extra or indexed!=last-first+1: extra.append(book)
print('资料5本次OCR文件数:',len(files),'缺页:',missing,'短页:',short)
print('资料5索引覆盖页:',count,'索引越界页:',invalid)
if missing or short or count!=246 or invalid or extra: raise SystemExit('覆盖或页码异常，请复核')
print('覆盖检查通过；不表示识别内容、公式、数字和图表已校验。')

