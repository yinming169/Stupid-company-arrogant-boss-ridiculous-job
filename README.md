# 高低压柜报价 Skill

## 2026-11-08 更新：请先阅读

**铜排专题补充**：新增 `switchgear-quote/references/铜排计算规则_统一口径.md`（唯一裁决源）、`铜排制作与用量计算_综合学习资料.md`（约 70 条来源与 18 条冲突速查）、`铜排算量学习记录_2026-11-08.md`（方法沉淀与跨 AI 调用说明）。涉及铜排的选型、折弯、用量、重量、损耗与分摊时先读统一口径文件。原始标准/手册 PDF 与客户项目资料不随本仓库分发。

已更新铜排分段计算、材料单规格要求及六份资料的学习成果。请先阅读 [技能入口](switchgear-quote/SKILL.md)、[使用说明](switchgear-quote/README.md) 和 [学习成果与覆盖](switchgear-quote/knowledge/六份资料索引/00_学习成果与覆盖.md)。以下旧说明中“每柜单独工作表”、自动配齐及旧版本格式等内容如与技能入口冲突，均以技能入口为准。教材原始 PDF 和重建索引用旧文字库不包含在本次仓库更新中，需从本地备份获取；OCR 数值须对照原图。


> 最新用法：先读取 [技能入口](switchgear-quote/SKILL.md) 和 [统一入口](switchgear-quote/references/统一入口.md)。多个柜箱放在同一工作表；铜排采用人工确认的分段输入。图纸识别、配套件与铜排结果须人工复核，项目资料见 [金冠项目归档](switchgear-quote/assets/项目归档/金冠选铁磨浮车间)。下方历史描述如有冲突，以技能入口和统一入口为准。

从电气图纸（DWG / DXF / PDF）提取元器件，按标号规则生成单工作表、按柜箱分区的分项报价表。

## 仓库内容（完整）

```
├── switchgear-quote/              技能本体（24 文件）
│   ├── SKILL.md                   主入口
│   ├── scripts/                   12 个 Python 脚本
│   ├── references/                7 份规则文档
│   │   ├── 标号规则.md            ★ 型号写法标准（最高优先级）
│   │   ├── 元器件物料表规则.xlsx  原始规则表（40 条子类码）
│   │   ├── 开源项目参考.md        开源项目研判
│   │   ├── recognition-rules.md
│   │   ├── electrical-knowledge.md
│   │   ├── accessory_rules.json
│   │   └── markup_rates.json
│   └── assets/                    价格库模板 / 标准参考格式 / 标准样例
├── knowledge/                     知识库（完整）
│   ├── handbooks-and-ocr.zip      46 MB，958 文件（五本书全文 + OCR + 页面图）
│   └── README.md
├── samples/                       示例图纸（dwg + dxf，4 个文件 30 MB）
│   ├── jinguan.dwg / .dxf         低压配电工程图纸
│   ├── yalv.dwg / .dxf            压滤机房低压配电图纸
│   └── README.md
└── README.md
```

## 在其他电脑使用

### 1. 克隆

```bash
git clone https://github.com/yinming169/Stupid-company-arrogant-boss-ridiculous-job.git
cd Stupid-company-arrogant-boss-ridiculous-job
```

### 2. 安装 Python 依赖

```bash
pip install ezdxf pdfplumber pymupdf openpyxl pandas
# 扫描件 OCR（可选）
pip install paddlepaddle paddleocr
```

### 3. 安装 DWG 转换工具（仅 DWG 图纸需要）

本仓库**不包含** LibreDWG 二进制（第三方 GPL 工具 + 体积 93 MB），按需安装：

- 从 [LibreDWG releases](https://github.com/LibreDWG/libredwg/releases) 下载，把 `dwg2dxf` 所在目录加入 PATH
- 或先把 DWG 转成 DXF（AutoCAD / ODA File Converter / 在线转换），本工具直接读 DXF

### 4. 解压知识库（供 AI 检索，可选）

```bash
cd knowledge && unzip handbooks-and-ocr.zip
```

### 5. 跑起来

```bash
cd switchgear-quote
python scripts/pipeline.py --input <图纸或目录> --db <价格库.xlsx> --out 报价单.xlsx
```

- 默认：一个工作簿，**每柜一个 sheet**
- `--split-files`：每柜一个独立 xlsx
- `--format detail`：内部核价用 7 表
- `--cabinet-type`：强制柜体型号（XL-21 / JXF / GGD / MNS抽屉式 / MNS固定式）

## 关于「不包含的内容」

以下内容**有意不放入仓库**，不是私藏：

| 内容 | 原因 |
|---|---|
| LibreDWG 二进制（93 MB） | 第三方 GPL 工具，官方 releases 可下载 |
| Python wheels（253 MB） | PyPI 公开可下载，`pip install` 即可 |

示例图纸已放入 `samples/`（dwg + 已转换的 dxf），**DXF 可直接解析，无需安装 LibreDWG**。

## 让 AI 使用

支持 Agent Skills 的工具：把 `switchgear-quote` 安装到技能目录后启用。
其他能读文件的 AI：提供本仓库，要求先读 `switchgear-quote/SKILL.md`，按其中流程执行。

## 许可证

MIT，见 LICENSE。手册 OCR 的版权归各自权利人，本仓库仅供个人与朋友内部使用。
