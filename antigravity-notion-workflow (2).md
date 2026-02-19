# Antigravity Agent Workflow: Excel / Word → Notion ページ自動作成

## Antigravity 動的追加ルール（優先）
- **MCP優先**: 全自動化のためにMCPツールを優先的に使用し、簡潔に完結させる。
- **ディレクトリ自動生成**: 関連するディレクトリ（親ページ）が存在しない場合、チームスペース直下に新規作成する。
- **判断と質問**: 内容から判断が難しい、または不確実な場合は、独断せずユーザに質問する。
- **インデックス（目録）管理**: AIが構造を常に把握できるよう、Notion内に「目録（Index）」を作成・更新し続ける。

## 概要

Excel（.xlsx）およびWord（.docx）ファイルを読み込み、適切なMarkdownに変換し、Notion APIを使ってページを作成するPythonプロジェクトを構築する。

**対応フォーマット**:
- Excel (.xlsx) → シートごとにNotionページ作成
- Word (.docx) → 文書構造を保持してNotionページ作成
- Word (.doc) → .docxに変換後に処理（LibreOffice使用）

---

## Phase 1: プロジェクトセットアップ

### 1.1 ディレクトリ構成

```
docs-to-notion/
├── src/
│   ├── __init__.py
│   ├── main.py               # エントリーポイント（ファイル種別を自動判定）
│   ├── excel_reader.py       # Excel読み込み・解析
│   ├── word_reader.py        # Word読み込み・解析
│   ├── markdown_converter.py # Markdown変換ロジック（共通）
│   ├── notion_client_wrapper.py  # Notion API操作
│   └── block_builder.py      # Notionブロック構築
├── templates/
│   └── mapping_rules.yaml    # 変換ルール設定
├── input/                    # 変換対象ファイル置き場（.xlsx, .docx, .doc）
├── .env                      # 環境変数
├── requirements.txt
└── README.md
```

### 1.2 依存パッケージ（requirements.txt）

```txt
notion-client>=2.2.0
openpyxl>=3.1.0
pandas>=2.0.0
python-docx>=1.1.0
mammoth>=1.8.0
python-dotenv>=1.0.0
pyyaml>=6.0
rich>=13.0.0
```

**パッケージの役割**:
| パッケージ | 用途 |
|---|---|
| `python-docx` | Word文書の構造解析（段落、表、スタイル情報） |
| `mammoth` | Word→Markdown変換（python-docxで取れない情報の補完） |
| `openpyxl` | Excel読み込み |
| `notion-client` | Notion API公式SDK |

### 1.3 環境変数（.env）

```env
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_PARENT_PAGE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 1.4 システム依存（.doc対応時のみ）

```bash
# .doc → .docx 変換にLibreOfficeが必要（.docxのみなら不要）
# Ubuntu/Debian
sudo apt install libreoffice-writer

# macOS
brew install --cask libreoffice
```

---

## Phase 2: Notion API セットアップ（事前準備）

以下はユーザーが手動で行う設定。エージェントはREADMEにこの手順を記載すること。

### 2.1 Notion Internal Integration 作成手順

1. https://developers.notion.com/ にアクセス
2. 「New integration」をクリック
3. 名前: `Docs to Notion Importer`
4. Capabilities:
   - Read content: ✅
   - Update content: ✅
   - Insert content: ✅
5. 「Submit」→ 表示されるシークレットキーを `.env` に設定

### 2.2 ページへのアクセス許可

1. Notionで対象の親ページを開く
2. 右上「…」→「コネクトの追加」→ 作成したインテグレーションを選択
3. アクセスを許可（子ページにも自動で継承される）

---

## Phase 3: Excel読み込みモジュール（excel_reader.py）

### 要件

- openpyxlでExcelファイルを読み込む
- 各シートを独立して処理する
- セルの内容だけでなく、以下の情報も抽出する:
  - **結合セル**: 結合範囲を検出し、見出しとして扱う
  - **書式情報**: 太字→見出し候補、背景色付き→セクション区切り
  - **空行**: セクション区切りとして認識
  - **数式**: 計算結果の値を取得（数式自体は無視）

### 実装ガイド

```python
import openpyxl
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CellData:
    value: str
    row: int
    col: int
    is_bold: bool = False
    is_merged: bool = False
    bg_color: Optional[str] = None
    font_size: Optional[float] = None

@dataclass
class SheetData:
    name: str
    cells: List[List[CellData]] = field(default_factory=list)
    tables: List[dict] = field(default_factory=list)
    headings: List[dict] = field(default_factory=list)
    paragraphs: List[dict] = field(default_factory=list)

def read_excel(file_path: str) -> List[SheetData]:
    """Excelファイルを読み込み、構造化データとして返す"""
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheets = []

    for ws in wb.worksheets:
        sheet = SheetData(name=ws.title)
        merged_ranges = list(ws.merged_cells.ranges)

        for row in ws.iter_rows(min_row=1, max_row=ws.max_row,
                                max_col=ws.max_column):
            row_data = []
            for cell in row:
                is_merged = any(cell.coordinate in mr for mr in merged_ranges)
                cell_data = CellData(
                    value=str(cell.value) if cell.value is not None else "",
                    row=cell.row,
                    col=cell.column,
                    is_bold=cell.font.bold if cell.font else False,
                    is_merged=is_merged,
                    bg_color=cell.fill.start_color.rgb if cell.fill and cell.fill.start_color else None,
                    font_size=cell.font.size if cell.font else None,
                )
                row_data.append(cell_data)
            sheet.cells.append(row_data)

        _analyze_structure(sheet)
        sheets.append(sheet)

    return sheets

def _analyze_structure(sheet: SheetData):
    """シートの構造を解析し、見出し・表・本文に分類する"""
    # 実装のポイント:
    # 1. 結合セル + 太字 + 大きいフォント → 見出し (heading)
    # 2. 連続する同一列数の行 → テーブル (table)
    # 3. 単一セルに長いテキスト → 本文 (paragraph)
    # 4. 空行 → セクション区切り
    pass  # エージェントが完全に実装すること
```

---

## Phase 4: Word読み込みモジュール（word_reader.py）

### 要件

- python-docxでWord文書の構造を解析する
- mammothでリッチな変換が必要な場合の補完を行う
- 以下の要素を正確に抽出する:
  - **見出し（Heading 1〜6）**: Wordスタイルから見出しレベルを取得
  - **段落**: 通常テキスト、太字・斜体・下線の書式を保持
  - **表（Table）**: ヘッダー行 + データ行として構造化
  - **箇条書き / 番号リスト**: リストスタイルを検出
  - **画像**: プレースホルダとして記録（Notionには外部URLが必要なため）
  - **ハイパーリンク**: リンクテキストとURLを保持
  - **ヘッダー / フッター**: オプションで先頭/末尾に追加

### 実装ガイド

```python
from docx import Document
from docx.oxml.ns import qn
from dataclasses import dataclass, field
from typing import List, Optional
import re

@dataclass
class DocElement:
    """Word文書の1要素を表す共通データ構造"""
    type: str  # "heading", "paragraph", "table", "list", "image", "divider"
    content: str = ""
    level: int = 0           # heading: 1-6, list: ネストレベル
    style: str = ""          # "bullet", "numbered", "bold", "italic"
    children: List = field(default_factory=list)  # テーブルの行データ等
    metadata: dict = field(default_factory=dict)  # リンクURL等の追加情報

def read_word(file_path: str) -> List[DocElement]:
    """Wordファイルを読み込み、DocElementのリストとして返す"""
    doc = Document(file_path)
    elements = []

    for block in _iter_block_items(doc):
        tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag
        if tag == "tbl":
            table = _parse_table(block, doc)
            if table:
                elements.append(table)
        elif tag == "p":
            para = _parse_paragraph(block, doc)
            if para:
                elements.append(para)

    return elements

def _iter_block_items(doc):
    """文書のbody直下のブロック要素を出現順に取得する。
    python-docxのdoc.paragraphsとdoc.tablesは別リストで順序が失われるため、
    XMLから直接イテレートする。"""
    body = doc.element.body
    for child in body.iterchildren():
        yield child

def _parse_paragraph(element, doc) -> Optional[DocElement]:
    """XML段落要素を解析してDocElementに変換する"""
    from docx.text.paragraph import Paragraph
    para = Paragraph(element, doc)

    text = para.text.strip()
    if not text:
        return None

    style_name = para.style.name if para.style else ""

    # 見出し判定
    if style_name.startswith("Heading"):
        level = _extract_heading_level(style_name)
        return DocElement(type="heading", content=text, level=level)

    # Title / Subtitle スタイル
    if style_name == "Title":
        return DocElement(type="heading", content=text, level=1)
    if style_name == "Subtitle":
        return DocElement(type="heading", content=text, level=2)

    # リスト判定
    if _is_list_item(para):
        list_style = _get_list_style(para)
        indent_level = _get_indent_level(para)
        return DocElement(type="list", content=text,
                          level=indent_level, style=list_style)

    # 通常段落（インライン書式情報を保持）
    rich_text = _extract_rich_text(para)
    return DocElement(type="paragraph", content=text,
                      metadata={"rich_text": rich_text})

def _parse_table(element, doc) -> Optional[DocElement]:
    """XMLテーブル要素を解析してDocElementに変換する"""
    from docx.table import Table
    table = Table(element, doc)

    rows_data = []
    for row in table.rows:
        row_cells = []
        for cell in row.cells:
            row_cells.append(cell.text.strip())
        # 結合セルによる重複を除去
        row_cells = _deduplicate_cells(row_cells, row)
        rows_data.append(row_cells)

    if not rows_data:
        return None

    return DocElement(
        type="table",
        children=rows_data,
        metadata={
            "headers": rows_data[0] if rows_data else [],
            "data_rows": rows_data[1:] if len(rows_data) > 1 else []
        }
    )

def _deduplicate_cells(cell_texts, row):
    """結合セルによるpython-docxの重複セルを除去する"""
    seen = set()
    unique = []
    for i, cell in enumerate(row.cells):
        cell_id = id(cell._tc)
        if cell_id not in seen:
            seen.add(cell_id)
            unique.append(cell_texts[i] if i < len(cell_texts) else "")
    return unique

def _extract_heading_level(style_name: str) -> int:
    match = re.search(r"\d+", style_name)
    return int(match.group()) if match else 1

def _is_list_item(para) -> bool:
    numPr = para._element.find(qn("w:pPr/w:numPr"))
    if numPr is not None:
        return True
    text = para.text.strip()
    jp_bullets = ("・", "●", "○", "■", "□", "◆", "※", "→")
    return text.startswith(jp_bullets)

def _get_list_style(para) -> str:
    style_name = para.style.name if para.style else ""
    if "Number" in style_name or "番号" in style_name:
        return "numbered"
    text = para.text.strip()
    if re.match(r"^\d+[.）)]\s", text):
        return "numbered"
    return "bullet"

def _get_indent_level(para) -> int:
    numPr = para._element.find(qn("w:pPr/w:numPr"))
    if numPr is not None:
        ilvl = numPr.find(qn("w:ilvl"))
        if ilvl is not None:
            return int(ilvl.get(qn("w:val"), 0))
    return 0

def _extract_rich_text(para) -> List[dict]:
    """段落内のランごとの書式情報を抽出する"""
    rich_text = []
    for run in para.runs:
        text = run.text
        if not text:
            continue
        entry = {"text": text}
        if run.bold:
            entry["bold"] = True
        if run.italic:
            entry["italic"] = True
        if run.underline:
            entry["underline"] = True
        if run.font.strike:
            entry["strikethrough"] = True

        hyperlink = _get_hyperlink(run)
        if hyperlink:
            entry["link"] = hyperlink

        rich_text.append(entry)
    return rich_text

def _get_hyperlink(run) -> Optional[str]:
    parent = run._element.getparent()
    if parent.tag.endswith("hyperlink"):
        r_id = parent.get(qn("r:id"))
        if r_id:
            try:
                rel = run.part.rels[r_id]
                return rel.target_ref
            except (KeyError, AttributeError):
                pass
    return None

# --- .doc → .docx 変換 ---

def convert_doc_to_docx(doc_path: str) -> str:
    """LibreOfficeを使って.docを.docxに変換する"""
    import subprocess, os
    output_dir = os.path.dirname(doc_path)
    result = subprocess.run(
        ["libreoffice", "--headless", "--convert-to", "docx",
         doc_path, "--outdir", output_dir],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice変換エラー: {result.stderr}")
    docx_path = os.path.splitext(doc_path)[0] + ".docx"
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"変換後ファイルが見つかりません: {docx_path}")
    return docx_path

# --- mammothフォールバック ---

def read_word_with_mammoth(file_path: str) -> str:
    """mammothで直接Markdown変換する（フォールバック用）"""
    import mammoth
    with open(file_path, "rb") as f:
        result = mammoth.convert_to_markdown(f)
    if result.messages:
        for msg in result.messages:
            print(f"  ⚠️ mammoth警告: {msg}")
    return result.value
```

---

## Phase 5: Markdown変換モジュール（markdown_converter.py）

### 変換ルール（Excel・Word共通出力）

| 入力の特徴 | Notion Markdown |
|---|---|
| 見出しレベル1 | `# 見出し1`（H1） |
| 見出しレベル2 | `## 見出し2`（H2） |
| 見出しレベル3 | `### 見出し3`（H3） |
| テーブル（ヘッダー + データ） | Markdownテーブル |
| 通常段落 | そのままテキスト |
| 太字テキスト | `**太字**` |
| 斜体テキスト | `*斜体*` |
| リンク | `[テキスト](URL)` |
| 箇条書き | `- リスト項目` |
| 番号リスト | `1. 番号リスト` |
| セクション区切り | `---`（divider） |
| 画像 | `[画像: ファイル名]`（プレースホルダ） |

### 実装ガイド

```python
from typing import List
import re

def convert_to_markdown(source, source_type: str = "auto") -> str:
    """Excel SheetDataまたはWord DocElementリストをMarkdownに変換する"""
    if source_type == "auto":
        if isinstance(source, list) and len(source) > 0 and hasattr(source[0], "type"):
            source_type = "word"
        else:
            source_type = "excel"

    if source_type == "word":
        return _convert_word_elements(source)
    else:
        return _convert_excel_sheet(source)

def _convert_word_elements(elements: List) -> str:
    """DocElementリストをMarkdownに変換する"""
    md_parts = []

    for el in elements:
        if el.type == "heading":
            level = min(el.level, 3)  # Notionは H1-H3 のみ
            md_parts.append(f"{'#' * level} {el.content}")
            md_parts.append("")

        elif el.type == "paragraph":
            rich_text = el.metadata.get("rich_text", [])
            if rich_text:
                md_parts.append(_rich_text_to_markdown(rich_text))
            else:
                md_parts.append(el.content)
            md_parts.append("")

        elif el.type == "table":
            headers = el.metadata.get("headers", [])
            data_rows = el.metadata.get("data_rows", [])
            if headers:
                md_parts.append(_format_table(headers, data_rows))
                md_parts.append("")

        elif el.type == "list":
            text = _clean_list_text(el.content)
            indent = "  " * el.level
            if el.style == "numbered":
                md_parts.append(f"{indent}1. {text}")
            else:
                md_parts.append(f"{indent}- {text}")

        elif el.type == "image":
            md_parts.append(f"[画像: {el.content}]")
            md_parts.append("")

        elif el.type == "divider":
            md_parts.append("---")
            md_parts.append("")

    return "\n".join(md_parts)

def _rich_text_to_markdown(rich_text: list) -> str:
    """リッチテキスト情報をMarkdownインライン書式に変換する"""
    parts = []
    for rt in rich_text:
        text = rt["text"]
        if rt.get("bold"):
            text = f"**{text}**"
        if rt.get("italic"):
            text = f"*{text}*"
        if rt.get("strikethrough"):
            text = f"~~{text}~~"
        if rt.get("link"):
            text = f"[{text}]({rt['link']})"
        parts.append(text)
    return "".join(parts)

def _clean_list_text(text: str) -> str:
    """日本語の箇条書き記号や番号プレフィックスを除去する"""
    text = re.sub(r"^[・●○■□◆※→]\s*", "", text)
    text = re.sub(r"^\d+[.）)]\s*", "", text)
    text = re.sub(r"^[（(]\d+[）)]\s*", "", text)
    text = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", text)
    return text.strip()

def _convert_excel_sheet(sheet) -> str:
    """Excel SheetDataをMarkdownに変換する"""
    md_parts = []
    for element in _iterate_elements(sheet):
        if element["type"] == "heading":
            level = element["level"]
            md_parts.append(f"{'#' * level} {element['text']}")
            md_parts.append("")
        elif element["type"] == "table":
            md_parts.append(_format_table(element["headers"], element["rows"]))
            md_parts.append("")
        elif element["type"] == "paragraph":
            md_parts.append(element["text"])
            md_parts.append("")
        elif element["type"] == "list":
            for item in element["items"]:
                prefix = "-" if element["style"] == "bullet" else f"{item['index']}."
                md_parts.append(f"{prefix} {item['text']}")
            md_parts.append("")
        elif element["type"] == "divider":
            md_parts.append("---")
            md_parts.append("")
    return "\n".join(md_parts)

def _format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Markdownテーブルを生成する"""
    def escape(s):
        return s.replace("|", "\\|")
    header_line = "| " + " | ".join(escape(h) for h in headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    data_lines = ["| " + " | ".join(escape(c) for c in row) + " |" for row in rows]
    return "\n".join([header_line, separator] + data_lines)
```

---

## Phase 6: Notionブロック構築（block_builder.py）

### 重要: Notion APIの制限

- **1回のAPIリクエストで追加できるブロックは最大100個**
- **rich_textは1ブロックあたり2000文字制限**
- テーブルは `table` ブロック + `table_row` 子ブロックで構成
- ネストは最大2レベルまで
- **Notionは H1〜H3 のみ対応**（H4以降はH3にフォールバック）

### 実装ガイド

```python
from typing import List
import re

def markdown_to_notion_blocks(markdown: str) -> list:
    """MarkdownをNotionブロックのリストに変換する"""
    blocks = []
    lines = markdown.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("### "):
            blocks.append(_heading_block(3, line[4:]))
        elif line.startswith("## "):
            blocks.append(_heading_block(2, line[3:]))
        elif line.startswith("# "):
            blocks.append(_heading_block(1, line[2:]))
        elif line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            i -= 1
            table_block = _build_table_block(table_lines)
            if table_block:
                blocks.append(table_block)
        elif line.startswith("- "):
            blocks.append(_list_block("bulleted", line[2:]))
        elif re.match(r"^\d+\.\s", line):
            text = re.sub(r"^\d+\.\s", "", line)
            blocks.append(_list_block("numbered", text))
        elif line == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif line:
            rich_text = _parse_inline_markdown(line)
            chunks = _split_rich_text(rich_text, 2000)
            for chunk in chunks:
                blocks.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": chunk}
                })
        i += 1

    return blocks

def _heading_block(level: int, text: str) -> dict:
    htype = f"heading_{level}"
    return {
        "object": "block", "type": htype,
        htype: {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }

def _list_block(style: str, text: str) -> dict:
    btype = f"{style}_list_item"
    rich_text = _parse_inline_markdown(text)
    return {"object": "block", "type": btype, btype: {"rich_text": rich_text}}

def _parse_inline_markdown(text: str) -> list:
    """Markdownインライン書式をNotion rich_textに変換する"""
    rich_text = []
    pattern = r"(\*\*(.+?)\*\*|\*(.+?)\*|~~(.+?)~~|\[(.+?)\]\((.+?)\)|([^*~\[]+))"

    for match in re.finditer(pattern, text):
        if match.group(2):
            rich_text.append({
                "type": "text", "text": {"content": match.group(2)},
                "annotations": {"bold": True}
            })
        elif match.group(3):
            rich_text.append({
                "type": "text", "text": {"content": match.group(3)},
                "annotations": {"italic": True}
            })
        elif match.group(4):
            rich_text.append({
                "type": "text", "text": {"content": match.group(4)},
                "annotations": {"strikethrough": True}
            })
        elif match.group(5) and match.group(6):
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(5), "link": {"url": match.group(6)}}
            })
        elif match.group(7):
            rich_text.append({"type": "text", "text": {"content": match.group(7)}})

    if not rich_text:
        rich_text.append({"type": "text", "text": {"content": text}})
    return rich_text

def _build_table_block(table_lines: list) -> dict:
    data_lines = [l for l in table_lines if not all(c in "|-: " for c in l)]
    if not data_lines:
        return None
    rows = []
    for line in data_lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return None
    col_count = len(rows[0])
    table_rows = []
    for row in rows:
        padded = row + [""] * (col_count - len(row)) if len(row) < col_count else row[:col_count]
        table_rows.append({
            "type": "table_row",
            "table_row": {
                "cells": [[{"type": "text", "text": {"content": cell}}] for cell in padded]
            }
        })
    return {
        "object": "block", "type": "table",
        "table": {
            "table_width": col_count,
            "has_column_header": True, "has_row_header": False,
            "children": table_rows
        }
    }

def _split_rich_text(rich_text: list, max_len: int) -> list:
    total = sum(len(rt.get("text", {}).get("content", "")) for rt in rich_text)
    if total <= max_len:
        return [rich_text]
    chunks, current, current_len = [], [], 0
    for rt in rich_text:
        content = rt.get("text", {}).get("content", "")
        if current_len + len(content) > max_len and current:
            chunks.append(current)
            current, current_len = [], 0
        current.append(rt)
        current_len += len(content)
    if current:
        chunks.append(current)
    return chunks
```

---

## Phase 7: Notion APIクライアント（notion_client_wrapper.py）

```python
import os
from notion_client import Client
from dotenv import load_dotenv
from typing import List

load_dotenv()
BATCH_SIZE = 100

class NotionPageCreator:
    def __init__(self):
        self.client = Client(auth=os.environ["NOTION_API_KEY"])
        self.parent_page_id = os.environ["NOTION_PARENT_PAGE_ID"]

    def create_page(self, title: str, blocks: List[dict]) -> str:
        first_batch = blocks[:BATCH_SIZE]
        remaining = blocks[BATCH_SIZE:]

        response = self.client.pages.create(
            parent={"page_id": self.parent_page_id},
            properties={"title": [{"text": {"content": title}}]},
            children=first_batch
        )
        page_id = response["id"]

        for i in range(0, len(remaining), BATCH_SIZE):
            batch = remaining[i:i + BATCH_SIZE]
            self.client.blocks.children.append(
                block_id=page_id, children=batch
            )
        return response["url"]
```

---

## Phase 8: メインスクリプト（main.py）

```python
import sys, os, glob
from rich.console import Console

from excel_reader import read_excel
from word_reader import read_word, convert_doc_to_docx
from markdown_converter import convert_to_markdown
from block_builder import markdown_to_notion_blocks
from notion_client_wrapper import NotionPageCreator

console = Console()
SUPPORTED = {".xlsx", ".docx", ".doc"}

def detect_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".xlsx": return "excel"
    if ext == ".docx": return "word"
    if ext == ".doc": return "word_legacy"
    raise ValueError(f"未対応: {ext}")

def process_file(path: str, creator: NotionPageCreator):
    name = os.path.basename(path)
    ftype = detect_type(path)
    console.print(f"\n[bold blue]📄 処理中: {name} ({ftype})[/bold blue]")

    if ftype == "word_legacy":
        console.print("  🔄 .doc → .docx に変換中...")
        path = convert_doc_to_docx(path)
        ftype = "word"

    if ftype == "excel":
        sheets = read_excel(path)
        console.print(f"  ✅ {len(sheets)}シート検出")
        for sheet in sheets:
            md = convert_to_markdown(sheet, source_type="excel")
            blocks = markdown_to_notion_blocks(md)
            title = f"{os.path.splitext(name)[0]} - {sheet.name}"
            url = creator.create_page(title=title, blocks=blocks)
            console.print(f"  ✅ ページ作成: {url}")

    elif ftype == "word":
        elements = read_word(path)
        console.print(f"  ✅ {len(elements)}要素検出")
        md = convert_to_markdown(elements, source_type="word")
        blocks = markdown_to_notion_blocks(md)
        title = os.path.splitext(name)[0]
        url = creator.create_page(title=title, blocks=blocks)
        console.print(f"  ✅ ページ作成: {url}")

def main():
    creator = NotionPageCreator()
    files = sys.argv[1:] if len(sys.argv) > 1 else \
            [f for ext in SUPPORTED for f in glob.glob(f"input/*{ext}")]

    if not files:
        console.print("[red]❌ ファイルが見つかりません[/red]")
        console.print("  対応: .xlsx, .docx, .doc")
        sys.exit(1)

    console.print(f"[bold green]🚀 {len(files)}ファイルを処理[/bold green]")
    for f in files:
        try:
            process_file(f, creator)
        except Exception as e:
            console.print(f"[red]❌ エラー ({os.path.basename(f)}): {e}[/red]")

    console.print("\n[bold green]✨ 完了[/bold green]")

if __name__ == "__main__":
    main()
```

---

## Phase 9: 変換ルール設定（templates/mapping_rules.yaml）

```yaml
# --- Excel用 ---
excel:
  heading_detection:
    h1:
      conditions: [merged_cells: true, bold: true, font_size_min: 14]
    h2:
      conditions: [bold: true, font_size_min: 11]
    h3:
      conditions: [bold: true]
  table_detection:
    min_rows: 2
    min_cols: 2
    header_row: first

# --- Word用 ---
word:
  heading_mapping:
    "Heading 1": 1
    "Heading 2": 2
    "Heading 3": 3
    "Heading 4": 3
    "Heading 5": 3
    "Heading 6": 3
    "Title": 1
    "Subtitle": 2
  preserve_formatting:
    bold: true
    italic: true
    underline: false      # Notionは下線未対応
    strikethrough: true
    hyperlinks: true
  image_handling: "placeholder"
  fallback_to_mammoth: false

# --- 共通 ---
common:
  list_detection:
    bullet_prefixes: ["・", "●", "○", "■", "□", "◆", "※"]
    numbered_prefixes:
      - regex: "^\\d+[.）)]\\s"
      - regex: "^[①②③④⑤⑥⑦⑧⑨⑩]"
  text_cleanup:
    replace_newlines: true
    trim_whitespace: true
    remove_empty_rows: true
```

---

## Phase 10: テストとデバッグ

```bash
cd docs-to-notion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# テスト実行
python src/main.py input/report.xlsx
python src/main.py input/document.docx
python src/main.py input/old_file.doc
python src/main.py input/*          # 一括処理
python src/main.py                  # input/自動検出
```

| エラー | 原因 | 対処 |
|---|---|---|
| `PackageNotFoundError` | Wordファイル破損 | Wordで開き直して保存 |
| `KeyError: 'w:numPr'` | リストスタイル検出失敗 | mammothフォールバック有効化 |
| `APIResponseError: body failed validation` | ブロック構造不正 | JSONログ出力して確認 |
| `APIResponseError: ... not shared` | インテグレーション未接続 | Notionで「コネクトの追加」 |
| `FileNotFoundError: libreoffice` | LibreOffice未インストール | .doc対応時のみ必要 |
| テーブルのセル重複 | python-docxの結合セル仕様 | _deduplicate_cells処理を確認 |

---

## Antigravityエージェントへの指示テンプレート

以下をAntigravityのエージェントに貼り付けて実行する：

```
このプロジェクトのワークフロードキュメント（antigravity-notion-workflow.md）に従って、
Excel・Word → Notion変換ツールを構築してください。

手順:
1. Phase 1のディレクトリ構成を作成
2. requirements.txtを作成しパッケージをインストール
3. Phase 3: excel_reader.py を実装（_analyze_structureを完全実装）
4. Phase 4: word_reader.py を実装（Word構造解析）
5. Phase 5: markdown_converter.py を実装（Excel・Word両対応）
6. Phase 6: block_builder.py を実装（インライン書式対応）
7. Phase 7: notion_client_wrapper.py を実装
8. Phase 8: main.py を実装（ファイル種別自動判定）
9. Phase 9: mapping_rules.yaml を配置
10. input/フォルダにサンプルファイルを配置してテスト

重要:
- _analyze_structure（Excel）と_iter_block_items（Word）は必ず完全に実装すること
- Word文書の見出しスタイル（Heading 1〜6）を正しく検出すること
- 太字・斜体・リンクのインライン書式をNotionのrich_textに反映すること
- 日本語の箇条書き記号（・●○■）に対応すること
- Notion APIの100ブロック制限と2000文字制限に対応すること
- .docファイルはLibreOfficeで.docxに変換してから処理すること
- python-docxの結合セル重複問題に対応すること（_deduplicate_cells）
```
