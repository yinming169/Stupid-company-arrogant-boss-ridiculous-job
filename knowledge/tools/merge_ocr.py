"""把 OCR 单页文件合并成整本 Markdown，便于检索和阅读。

用法: python tools/merge_ocr.py [ocr子目录名]
"""
import glob
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OCR_DIR = os.path.join(BASE, "ocr")
TXT_DIR = os.path.join(BASE, "txt")


def merge(book_dir):
    files = sorted(glob.glob(os.path.join(book_dir, "p*.txt")))
    if not files:
        return 0, 0
    parts = []
    for path in files:
        m = re.search(r"p(\d+)\.txt$", path)
        if not m:
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            body = f.read()
        body = re.sub(r"<!--\s*page\s*\d+\s*-->", "", body).strip()
        if not body:
            continue
        parts.append(f"\n\n<!-- p{int(m.group(1))} -->\n{body}")
    name = os.path.basename(book_dir)
    os.makedirs(TXT_DIR, exist_ok=True)
    out = os.path.join(TXT_DIR, f"{name}_OCR.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    return len(parts), os.path.getsize(out)


def main():
    targets = []
    if len(sys.argv) > 1:
        targets = [os.path.join(OCR_DIR, sys.argv[1])]
    else:
        targets = [d for d in glob.glob(os.path.join(OCR_DIR, "*")) if os.path.isdir(d)]
    for d in targets:
        n, size = merge(d)
        print(f"{os.path.basename(d)}: {n} 页 -> {size//1024} KB")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
