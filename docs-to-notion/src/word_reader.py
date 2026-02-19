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
    level: int = 0
    style: str = ""
    children: List = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

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
    """文書bodyの直下のブロック要素を出現順に取得"""
    body = doc.element.body
    for child in body.iterchildren():
        yield child

def _parse_paragraph(element, doc) -> Optional[DocElement]:
    """XML段落要素をDocElementに変換する"""
    from docx.text.paragraph import Paragraph
    para = Paragraph(element, doc)

    text = para.text.strip()
    if not text:
        return None

    style_name = para.style.name if para.style else ""

    # 見出し判定
    if style_name.startswith("Heading") or style_name.startswith("見出し"):
        level = _extract_heading_level(style_name)
        return DocElement(type="heading", content=text, level=level)

    # Title / Subtitle スタイル
    if style_name in ("Title", "タイトル"):
        return DocElement(type="heading", content=text, level=1)
    if style_name in ("Subtitle", "サブタイトル"):
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
    """XMLテーブル要素をDocElementに変換する"""
    from docx.table import Table
    table = Table(element, doc)

    rows_data = []
    for row in table.rows:
        row_cells = [cell.text.strip() for cell in row.cells]
        # 結合セルの重複を除去
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

def _deduplicate_cells(cell_texts: List[str], row) -> List[str]:
    """
    python-docxの結合セルによる重複を除去する。
    同じ _tc オブジェクトを複数回持つセルをスキップする。
    """
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
    return min(int(match.group()) if match else 1, 3)

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
        capture_output=True, text=True, timeout=120
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
            print(f"  ⚠️ mammoth warning: {msg}")
    return result.value
