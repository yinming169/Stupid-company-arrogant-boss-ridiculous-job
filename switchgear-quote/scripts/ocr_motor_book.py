"""Local page OCR for scanned book; resumable; OCR is unverified, preserve original PDF."""
import argparse, os, pathlib, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'knowledge'/'六份资料索引'/'ocr_runtime'))
os.environ.setdefault('OMP_NUM_THREADS','1')

def main():
    import pypdfium2
    from rapidocr_onnxruntime import RapidOCR
    from PIL import Image
    import numpy as np
    p=argparse.ArgumentParser(); p.add_argument('--start',type=int,default=31); p.add_argument('--end',type=int,default=246); a=p.parse_args()
    source=ROOT.parent/'source_books'/'电机与拖动基础.pdf'; out=ROOT/'knowledge'/'六份资料索引'/'ocr'/'资料5_电机与拖动基础'; out.mkdir(parents=True,exist_ok=True)
    pdf=pypdfium2.PdfDocument(str(source)); ocr=RapidOCR(intra_op_num_threads=1, inter_op_num_threads=1); started=time.time()
    for page in range(a.start,min(a.end,len(pdf))+1):
        f=out/f'p{page:04}.txt'
        if f.exists() and f.stat().st_size>50: continue
        try:
            bitmap=pdf[page-1].render(scale=1.5).to_pil().convert('RGB')
            rows,_=ocr(np.asarray(bitmap))
            if not rows: raise ValueError('未识别文字，需人工检查')
            f.write_text('\n'.join(row[1] for row in rows)+'\n',encoding='utf8')
            print(f'PDF第{page}页：{len(rows)}行，用时{time.time()-started:.0f}秒',flush=True)
        except Exception as e:
            print(f'PDF第{page}页失败：{e}',flush=True)
    print('完成；必须核对原图与缺失页。',flush=True)
if __name__=='__main__': main()

