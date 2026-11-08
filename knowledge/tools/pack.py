"""打包：把 skill + 知识库备份到 D 盘，并生成可上传 GitHub 的仓库结构。

用法:
    python tools/pack.py              # 打包（含全文库，本地备份）
    python tools/pack.py --no-fulltext # 不打包全文库（体积小，适合上传）
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # knowledge/
PROJECT = os.path.dirname(BASE)                                             # 工作区
SKILL_SRC = os.path.join(os.path.expanduser("~"), ".workbuddy-ai", "skills", "switchgear-quote")
DEST = r"D:/高低压柜报价-skill"


IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.png", "*.err")


def merge_ocr():
    """把 OCR 单页合并成整本 md。"""
    sys.path.insert(0, os.path.join(BASE, "tools"))
    import merge_ocr as m
    for d in glob.glob(os.path.join(BASE, "ocr", "*")):
        if os.path.isdir(d):
            n, size = m.merge(d)
            print(f"  合并 {os.path.basename(d)}: {n} 页 -> {size//1024} KB")


def copy_skill():
    dst = os.path.join(DEST, "switchgear-quote")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(SKILL_SRC, dst, ignore=IGNORE)
    print(f"  skill -> {dst}")
    return dst


def copy_knowledge(fulltext=True):
    dst = os.path.join(DEST, "knowledge")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst, exist_ok=True)
    # 必带：提炼文档 + 工具
    for f in ["配电柜知识库.md", "00_知识边界与覆盖度.md", "README.md"]:
        src = os.path.join(BASE, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, f))
    for sub in ["tools", "txt"]:
        src = os.path.join(BASE, sub)
        if os.path.exists(src):
            shutil.copytree(src, os.path.join(dst, sub), ignore=IGNORE)
    if fulltext:
        for sub in ["ocr"]:
            src = os.path.join(BASE, sub)
            if os.path.exists(src):
                shutil.copytree(src, os.path.join(dst, sub), ignore=IGNORE)
    print(f"  knowledge -> {dst}（全文库{'含' if fulltext else '不含'}）")
    return dst


README = """# 高低压柜报价 Skill

把电气图纸变成可报价的 Excel 材料清单，并自动配齐配套件。

## 能力

- **图纸解析**：DWG（经 LibreDWG 转 DXF）/ DXF / 矢量 PDF / 扫描件 OCR
- **元器件识别**：型号、数量、柜型、柜体尺寸、铜排规格
- **配套件自动配齐**：马达保护器、接触器、变频器、软启动器等按规则配附件
- **报价单生成**：按用户既有「分项报价表」格式输出，含分项、单价、加价率、利润
- **知识检索**：五本配电资料全文检索，查选型依据

## 目录

```
switchgear-quote/          skill 本体
├── SKILL.md               技能说明与工作流
├── scripts/               可执行脚本
│   ├── pipeline.py        一键：图纸 → 报价单
│   ├── dispatch.py        图纸分流
│   ├── extract_dxf.py     DXF 提取
│   ├── extract_pdf.py     PDF 提取
│   ├── classify.py        型号/柜型/尺寸识别
│   ├── price_match.py     价格库匹配 + 加价
│   ├── build_quote.py     生成报价 Excel
│   └── template_quote.py  按用户模板出表 + 配齐配套件
├── references/            规则与知识
│   ├── recognition-rules.md     型号识别规则库
│   ├── electrical-knowledge.md  选型知识库
│   ├── accessory_rules.json     配套件规则
│   └── markup_rates.json        加价率
└── assets/
    └── price_db_template.xlsx   价格库模板
```

## 快速开始

```bash
# 一键生成报价单
python scripts/pipeline.py --input <图纸或目录> --db <价格库.xlsx> --out 报价单.xlsx

# 按用户模板出配齐版
python scripts/template_quote.py <源清单.xlsx> --out <配齐版.xlsx>
```

## 依赖

```bash
python -c "import ezdxf, pdfplumber, fitz, openpyxl, pandas"
```

DWG 需先用 LibreDWG 转 DXF：

```bash
dwg2dxf.exe -o out.dxf in.dwg
```

## 免责与边界

- 本 skill 是**选型逻辑与流程工具**，不是参数手册。最终参数以厂家样本为准。
- 铜排用量、柜体部件数量为**推算值**，报价前必须人工复核。
- 价格只能来自用户自有价格库，不联网抓价、不猜价。
"""


def write_readme():
    p = os.path.join(DEST, "README.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(README)
    # skill 目录内也放一份
    shutil.copy2(p, os.path.join(DEST, "switchgear-quote", "README.md"))
    print(f"  README -> {p}")


def git_init():
    repo = os.path.join(DEST, "switchgear-quote")
    if not os.path.isdir(os.path.join(repo, ".git")):
        subprocess.run(["git", "init", "-q"], cwd=repo)
        subprocess.run(["git", "checkout", "-q", "-b", "main"], cwd=repo)
    # 仓库级身份（不改全局配置）
    subprocess.run(["git", "config", "user.name", "switchgear-quote"], cwd=repo)
    subprocess.run(["git", "config", "user.email", "local@localhost"], cwd=repo)
    with open(os.path.join(repo, ".gitignore"), "w", encoding="utf-8") as f:
        f.write("__pycache__/\n*.pyc\n*.xlsx\n!assets/*.xlsx\nwork/\n")
    subprocess.run(["git", "add", "-A"], cwd=repo)
    r = subprocess.run(["git", "commit", "-q", "-m", "更新：识别优先级与通用代号"],
                       cwd=repo)
    print(f"  git 仓库 -> {repo}（{'已提交' if r.returncode == 0 else '无变更'}）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fulltext", action="store_true", help="不打包 OCR 全文库")
    a = ap.parse_args()

    print("1) 合并 OCR 结果")
    merge_ocr()
    print("2) 复制 skill")
    copy_skill()
    print("3) 复制知识库")
    copy_knowledge(fulltext=not a.no_fulltext)
    print("4) 生成 README")
    write_readme()
    print("5) 初始化 git 仓库")
    git_init()

    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(DEST) for f in fs)
    print(f"\n完成：{DEST}　总计 {total/1048576:.1f} MB")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
