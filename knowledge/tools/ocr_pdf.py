"""PDF 批量 OCR → 结构化文本（按坐标重排成行，保留表格）。

用法:
    python ocr_pdf.py <pdf> <out_dir> [--dpi 150] [--workers 4] [--start 1] [--end N]

特性:
    - 多进程并行
    - 断点续传（已存在的页跳过）
    - 按检测框坐标重排：同一 y 归为一行，行内按 x 排序，用制表符分隔 → 保留表格列
"""
import argparse
import os
import re
import sys
import glob
from multiprocessing import Pool

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("ORT_NUM_THREADS", "1")

_OCR = None


def _init():
    global _OCR
    from rapidocr import RapidOCR
    _OCR = RapidOCR()


def _rows_from_result(res):
    """把 OCR 结果按坐标重排成行。"""
    if res is None:
        return []
    boxes = getattr(res, "boxes", None)
    txts = getattr(res, "txts", None)
    scores = getattr(res, "scores", None)
    if boxes is None or txts is None or len(boxes) == 0:
        return []
    if scores is None:
        scores = [1.0] * len(txts)
    items = []
    for box, txt, score in zip(boxes, txts, scores):
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append({
            "x": min(xs), "y": min(ys), "x2": max(xs), "y2": max(ys),
            "t": str(txt).strip(), "s": float(score),
        })
    items = [i for i in items if i["t"]]
    if not items:
        return []
    items.sort(key=lambda i: (i["y"], i["x"]))
    rows, cur, cur_y = [], [], None
    for it in items:
        h = max(1.0, it["y2"] - it["y"])
        if cur_y is None or abs(it["y"] - cur_y) <= h * 0.6:
            cur.append(it)
            cur_y = it["y"] if cur_y is None else cur_y
        else:
            rows.append(cur)
            cur = [it]
            cur_y = it["y"]
    if cur:
        rows.append(cur)
    out = []
    for r in rows:
        r.sort(key=lambda i: i["x"])
        out.append("\t".join(i["t"] for i in r))
    return out


def _work(job):
    pdf, page_no, out_path, dpi = job
    if os.path.exists(out_path):
        return (page_no, "skip", 0)
    import fitz
    doc = fitz.open(pdf)
    try:
        page = doc[page_no - 1]
        pix = page.get_pixmap(dpi=dpi)
        img_path = out_path + ".png"
        pix.save(img_path)
    finally:
        doc.close()
    try:
        res = _OCR(img_path)
        rows = _rows_from_result(res)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"<!-- page {page_no} -->\n")
            f.write("\n".join(rows))
        return (page_no, "ok", len(rows))
    except Exception as e:
        with open(out_path + ".err", "w", encoding="utf-8") as f:
            f.write(str(e))
        return (page_no, "err", 0)
    # 不删除中间 png：删除次数累计会触发文件批量删除保护，导致任务被拦。
    # 残留 png 同名会被下次覆盖，不影响正确性。


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def run_batch(pdf, pages, out_dir, dpi, workers, per_page_timeout=25):
    """跑一批，带超时；超时则终止整批，返回未完成的页。"""
    jobs = [(pdf, p, os.path.join(out_dir, f"p{p:04d}.txt"), dpi) for p in pages]
    ok, err = 0, 0
    pool = Pool(workers, initializer=_init)
    try:
        ar = pool.map_async(_work, jobs)
        results = ar.get(timeout=max(90, len(jobs) * per_page_timeout))
        for pg, st, n in results:
            if st == "ok":
                ok += 1
            elif st == "err":
                err += 1
        pool.close()
        pool.join()
        return ok, err, []
    except Exception as e:
        pool.terminate()
        pool.join()
        done = {int(m.group(1)) for f in glob.glob(os.path.join(out_dir, "p*.txt"))
                for m in [re.search(r"p(\d+)\.txt$", f)] if m}
        failed = [p for p in pages if p not in done]
        print(f"  [!] 批次超时/异常（{type(e).__name__}），{len(failed)} 页待重试", flush=True)
        return ok, err, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out_dir")
    ap.add_argument("--dpi", type=int, default=140)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=0)
    ap.add_argument("--batch", type=int, default=20, help="每批页数")
    a = ap.parse_args()

    import fitz
    doc = fitz.open(a.pdf)
    total = doc.page_count
    doc.close()
    end = a.end or total
    os.makedirs(a.out_dir, exist_ok=True)

    # 注意：不在此处批量清理残留 png（会触发文件批量删除保护）。
    # _work 的 finally 会删除自己产生的 png；残留的同名 png 会被下次覆盖。

    want = list(range(a.start, end + 1))
    done = {int(m.group(1)) for f in glob.glob(os.path.join(a.out_dir, "p*.txt"))
            for m in [re.search(r"p(\d+)\.txt$", f)] if m}
    pending = [p for p in want if p not in done]
    print(f"总页 {total}，范围 {a.start}-{end}，已完成 {len(want)-len(pending)}，"
          f"待处理 {len(pending)}", flush=True)

    total_ok = total_err = 0
    for round_no in range(1, 4):
        if not pending:
            break
        print(f"\n--- 第 {round_no} 轮，{len(pending)} 页 ---", flush=True)
        retry = []
        for bi, batch in enumerate(_chunks(pending, a.batch), 1):
            ok, err, failed = run_batch(a.pdf, batch, a.out_dir, a.dpi, a.workers)
            total_ok += ok
            total_err += err
            retry.extend(failed)
            print(f"  批 {bi}: 成功 {ok}，失败 {err}，待重试 {len(failed)}", flush=True)
        pending = retry
        if pending:
            print(f"  本轮剩余 {len(pending)} 页，降配重试", flush=True)
            a.workers = 1

    print(f"\n完成：成功 {total_ok}，失败 {total_err}，仍缺 {len(pending)}", flush=True)
    if pending:
        print(f"缺失页: {pending[:40]}", flush=True)


if __name__ == "__main__":
    main()
