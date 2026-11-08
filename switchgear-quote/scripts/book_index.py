"""Build/search a page-labelled local research index; OCR and text are clues, not verified facts."""
import argparse, hashlib, json, pathlib, re, sqlite3

SKILL = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_BACKUP = SKILL.parent
INDEX = SKILL / 'knowledge' / '六份资料索引' / 'pages.sqlite3'
MAP = {'资料1':'常用低压供配电设备选型与安装技术手册(1).pdf','资料2':'电气控制工程师手册(向晓汉).pdf','资料3':'低压成套开关设备的原理及其控制技术.pdf','资料4':'工业与民用配电设计手册第三版高清晰版.pdf','资料5':'电机与拖动基础.pdf','资料6':'GBT+24275-2019.pdf'}

def build(base):
    import pypdfium2
    INDEX.parent.mkdir(parents=True,exist_ok=True)
    temp=INDEX.with_suffix('.tmp'); temp.unlink(missing_ok=True)
    db=sqlite3.connect(temp)
    db.executescript('CREATE TABLE books(book TEXT PRIMARY KEY, filename TEXT, sha256 TEXT, page_count INTEGER); CREATE TABLE pages(book TEXT, page INTEGER, source TEXT, text TEXT, UNIQUE(book,page,source)); CREATE INDEX page_ref ON pages(book,page);')
    for book,name in MAP.items():
        path=base/'source_books'/name
        if not path.is_file(): raise FileNotFoundError(path)
        h=hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
        pdf=pypdfium2.PdfDocument(str(path)); db.execute('INSERT INTO books VALUES(?,?,?,?)',(book,name,h.hexdigest(),len(pdf)))
        print(f'{book}: {len(pdf)}页',flush=True)
    root=base/'knowledge'; counts={}
    for file in sorted((root/'txt').glob('*.md')):
        name=file.name; book=name.split('_')[0]
        if book not in MAP: continue
        raw=file.read_text(encoding='utf8',errors='replace'); chunks=re.split(r'<!--\s*p(\d+)\s*-->',raw)
        for i in range(1,len(chunks)-1,2):
            page=int(chunks[i]); txt=chunks[i+1].strip()
            if txt: db.execute('INSERT OR REPLACE INTO pages VALUES(?,?,?,?)',(book,page,'文字库/'+name,txt)); counts[book]=counts.get(book,0)+1
    for folder in sorted((root/'ocr').iterdir()):
        if not folder.is_dir(): continue
        n=folder.name; book=n.split('_')[0]
        if n.startswith('复核_资料4'): book='资料4'
        if book not in MAP: continue
        for f in folder.glob('p*.txt'):
            m=re.fullmatch(r'p(\d+)\.txt',f.name)
            if not m: continue
            txt=f.read_text(encoding='utf8',errors='replace').strip()
            if txt: db.execute('INSERT OR REPLACE INTO pages VALUES(?,?,?,?)',(book,int(m.group(1)),'OCR/'+n,txt)); counts[book]=counts.get(book,0)+1
    added=SKILL/'knowledge'/'六份资料索引'/'ocr'/'资料5_电机与拖动基础'
    if added.is_dir():
        for file in sorted(added.glob('p*.txt')):
            m=re.fullmatch(r'p(\d+)\.txt',file.name)
            if not m: continue
            text=file.read_text(encoding='utf8',errors='replace').strip()
            if len(text)>30:
                db.execute('INSERT OR REPLACE INTO pages VALUES(?,?,?,?)',('资料5',int(m.group(1)),'本次OCR/资料5',text)); counts['资料5']=counts.get('资料5',0)+1
    for book in ('资料1','资料4'):
        extra=SKILL/'knowledge'/'六份资料索引'/'ocr'/book
        if extra.is_dir():
            for file in sorted(extra.glob('p*.txt')):
                m=re.fullmatch(r'p(\d+)\.txt',file.name)
                if not m: continue
                text=file.read_text(encoding='utf8',errors='replace').strip()
                if len(text)>30:
                    db.execute('INSERT OR REPLACE INTO pages VALUES(?,?,?,?)',(book,int(m.group(1)),'本次OCR/'+book,text)); counts[book]=counts.get(book,0)+1
    db.commit(); db.close(); temp.replace(INDEX)
    print('索引记录（含不同来源重复页）：',json.dumps(counts,ensure_ascii=False),flush=True)

def query(words,book,limit):
    if not INDEX.is_file(): raise SystemExit('索引不存在，先执行 build。')
    db=sqlite3.connect(INDEX); sql='SELECT book,page,source,text FROM pages WHERE '+' AND '.join(['text LIKE ?']*len(words)); args=['%'+x+'%' for x in words]
    if book: sql+=' AND book=?'; args.append(book)
    sql+=' ORDER BY book,page,source LIMIT ?'; args.append(limit)
    for b,p,src,t in db.execute(sql,args):
        print(f'[{b} PDF第{p}页 | {src}]')
        pos=min((t.find(x) for x in words if x in t),default=0); print(re.sub(r'\s+',' ',t[max(0,pos-90):pos+240]))
    print('注意：命中仅是线索；数字、表格、公式和页号须核对原PDF，版本状态另核。')

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('build'); b.add_argument('--backup',default=str(DEFAULT_BACKUP))
    s=sub.add_parser('search'); s.add_argument('words',nargs='+'); s.add_argument('--book',choices=list(MAP)); s.add_argument('--limit',type=int,default=20)
    sub.add_parser('status')
    v=sub.add_parser('page'); v.add_argument('--book',required=True,choices=list(MAP)); v.add_argument('--page',type=int,required=True)
    a=p.parse_args()
    if a.cmd=='build': build(pathlib.Path(a.backup))
    elif a.cmd=='search': query(a.words,a.book,a.limit)
    else:
        if not INDEX.is_file(): raise SystemExit('索引不存在，先执行 build。')
        db=sqlite3.connect(INDEX)
        if a.cmd=='status':
            for b,name,n in db.execute('select book,filename,page_count from books order by book'):
                count=db.execute('select count(distinct page) from pages where book=?',(b,)).fetchone()[0]
                print(f'{b}: {name} PDF共{n}页，现有文字/OCR覆盖{count}页（不代表内容已审核）')
        else:
            rows=db.execute('select source,text from pages where book=? and page=? order by source',(a.book,a.page)).fetchall()
            if not rows: raise SystemExit('该页无可检索文字；直接查看原PDF。')
            for source,text in rows: print(f'\n[{a.book} PDF第{a.page}页 | {source}]\n{text}')
            print('文字仅作检索线索；数字、表格、公式及页码须核原PDF。')
if __name__=='__main__': main()



