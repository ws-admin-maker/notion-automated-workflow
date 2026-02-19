from typing import List
import re

def convert_to_markdown(source, source_type: str = "auto") -> str:
    """Excel SheetDataまたはWord DocElementリストをMarkdownに変換する"""
    if source_type == "auto":
        if hasattr(source, "name"):  # SheetData
            source_type = "excel"
        else:
            source_type = "word"

    if source_type == "word":
        return _convert_word_elements(source)
    else:
        return _convert_excel_sheet(source)

def _convert_word_elements(elements: List) -> str:
    """DocElementリストをMarkdownに変換する"""
    md_parts = []

    for el in elements:
        if el.type == "heading":
            level = min(el.level, 3)
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
    parts = []
    for rt in rich_text:
        text = rt.get("text", rt.get("content", ""))
        if isinstance(text, dict):
            text = text.get("content", "")
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
    text = re.sub(r"^[・●○■□◆※→]\s*", "", text)
    text = re.sub(r"^\d+[.）)]\s*", "", text)
    text = re.sub(r"^[（(]\d+[）)]\s*", "", text)
    text = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", text)
    return text.strip()

def _convert_excel_sheet(sheet) -> str:
    """Excel SheetDataをMarkdownに変換する"""
    md_parts = []
    md_parts.append(f"# {sheet.name}")
    md_parts.append("")

    from excel_reader import _iterate_elements
    elements = _iterate_elements(sheet)

    for element in elements:
        if element["type"] == "heading":
            level = element.get("level", 2)
            md_parts.append(f"{'#' * level} {element['text']}")
            md_parts.append("")
        elif element["type"] == "table":
            md_parts.append(_format_table(element["headers"], element["rows"]))
            md_parts.append("")
        elif element["type"] == "paragraph":
            md_parts.append(element["text"])
            md_parts.append("")
        elif element["type"] == "list":
            for item in element.get("items", []):
                prefix = "-" if element.get("style") == "bullet" else f"{item.get('index', 1)}."
                md_parts.append(f"{prefix} {item['text']}")
            md_parts.append("")
        elif element["type"] == "divider":
            md_parts.append("---")
            md_parts.append("")

    return "\n".join(md_parts)

def _format_table(headers: List, rows: List) -> str:
    """Markdownテーブルを生成する"""
    def escape(s):
        return str(s).replace("|", "\\|").replace("\n", " ").replace("\r", "")

    if not headers:
        return ""
    
    header_line = "| " + " | ".join(escape(h) for h in headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    data_lines = [
        "| " + " | ".join(
            escape(c) for c in (row + [""] * (len(headers) - len(row)))[:len(headers)]
        ) + " |"
        for row in rows
    ]
    return "\n".join([header_line, separator] + data_lines)
