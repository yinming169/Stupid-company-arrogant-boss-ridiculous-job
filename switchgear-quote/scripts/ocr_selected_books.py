"""选定参考书PDF按页OCR；结果仅作检索线索，支持断点续跑。"""
import argparse, os, pathlib, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'knowledge'/'六份资料索引'/'ocr_runtime'))
os.environ.setdefault('OMP_NUM_THREADS','1')
BOOKS={'资料1':'常用低压供配电设备选型与安装技术手册(1).pdf','资料4':'工业与民用配电设计手册第三版高清晰版.pdf'}
def main():
    import pypdfium2, numpy as np
    from rapidocr_onnxruntime import RapidOCR
    p=argparse.ArgumentParser(); p.add_argument('--book',choices=BOOKS,required=True); p.add_argument('--start',type=int,required=True); p.add_argument('--end',type=int,required=True); a=p.parse_args()
    pdf=pypdfium2.PdfDocument(str(ROOT.parent/'source_books'/BOOKS[a.book])); out=ROOT/'knowledge'/'六份资料索引'/'ocr'/a.book;out.mkdir(parents=True,exist_ok=True); model=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1); start=time.time()
    for n in range(a.start,min(a.end,len(pdf))+1):
        path=out/f'p{n:04}.txt'
        if path.exists() and path.stat().st_size>50:continue
        try:
            im=pdf[n-1].render(scale=1.5).to_pil().convert('RGB'); rows,_=model(np.asarray(im))
            if not rows:raise ValueError('未识别文字；可能为空白页，须人工确认')
            path.write_text('\n'.join(x[1] for x in rows)+'\n',encoding='utf8'); print(f'{a.book} PDF第{n}页 {len(rows)}行 用时{time.time()-start:.0f}秒',flush=True)
        except Exception as e:print(f'{a.book} PDF第{n}页未完成：{e}',flush=True)
    print('范围处理结束，须检查缺页与原图。',flush=True)
if __name__=='__main__':main()
