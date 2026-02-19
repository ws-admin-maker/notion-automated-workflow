from typing import List
import re

def markdown_to_notion_blocks(markdown: str) -> list:
    """MarkdownをNotionブロックのリストに変換する"""
    blocks = []
    lines = markdown.split("\n")
    i = 0

    # 日本語箇条書き記号
    JP_BULLETS = ("・", "●", "○", "■", "□", "◆", "※", "→")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("### "):
            blocks.append(_heading_block(3, stripped[4:]))
        elif stripped.startswith("## "):
            blocks.append(_heading_block(2, stripped[3:]))
        elif stripped.startswith("# "):
            blocks.append(_heading_block(1, stripped[2:]))
        elif stripped.startswith("|"):
            # テーブルブロック: 連続する|行をまとめる
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            i -= 1
            table_block = _build_table_block(table_lines)
            if table_block:
                blocks.append(table_block)
        elif stripped.startswith("- "):
            text = _clean_jp_bullets(stripped[2:])
            blocks.append(_list_block("bulleted", text))
        elif re.match(r"^\d+\.\s", stripped):
            text = re.sub(r"^\d+\.\s", "", stripped)
            blocks.append(_list_block("numbered", text))
        elif stripped == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif stripped.startswith(JP_BULLETS):
            # 日本語箇条書き記号で始まる行をbulletedリストとして扱う
            text = _clean_jp_bullets(stripped)
            blocks.append(_list_block("bulleted", text))
        elif re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", stripped):
            text = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", stripped)
            blocks.append(_list_block("bulleted", text))
        elif stripped:
            # 通常段落 - 2000文字制限対応
            rich_text = _parse_inline_markdown(stripped)
            for chunk in _split_rich_text(rich_text, 2000):
                blocks.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": chunk}
                })
        i += 1

    return blocks

def _clean_jp_bullets(text: str) -> str:
    """日本語箇条書き記号やプレフィックスを除去する"""
    text = re.sub(r"^[・●○■□◆※→]\s*", "", text)
    text = re.sub(r"^\d+[.）)]\s*", "", text)
    text = re.sub(r"^[（(]\d+[）)]\s*", "", text)
    text = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", text)
    return text.strip()

def _heading_block(level: int, text: str) -> dict:
    level = min(level, 3)  # Notionは H1〜H3 のみ
    htype = f"heading_{level}"
    return {
        "object": "block", "type": htype,
        htype: {"rich_text": _parse_inline_markdown(text)}
    }

def _list_block(style: str, text: str) -> dict:
    btype = f"{style}_list_item"
    rich_text = _parse_inline_markdown(text)
    return {"object": "block", "type": btype, btype: {"rich_text": rich_text}}

def _parse_inline_markdown(text: str) -> list:
    """
    Markdownインライン書式をNotion rich_textに変換する。
    対応: **bold**, *italic*, ~~strikethrough~~, [text](url)
    """
    rich_text = []
    # パターン: bold > italic > strikethrough > link > plain text
    pattern = (
        r"(\*\*(.+?)\*\*)"       # group 1,2: bold
        r"|(\*(.+?)\*)"           # group 3,4: italic
        r"|(~~(.+?)~~)"           # group 5,6: strikethrough
        r"|(\[(.+?)\]\((.+?)\))" # group 7,8,9: link
        r"|([^*~\[]+)"            # group 10: plain text
    )

    for match in re.finditer(pattern, text, re.DOTALL):
        if match.group(2):  # bold
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(2)},
                "annotations": {"bold": True}
            })
        elif match.group(4):  # italic
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(4)},
                "annotations": {"italic": True}
            })
        elif match.group(6):  # strikethrough
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(6)},
                "annotations": {"strikethrough": True}
            })
        elif match.group(8) and match.group(9):  # link
            rich_text.append({
                "type": "text",
                "text": {"content": match.group(8), "link": {"url": match.group(9)}}
            })
        elif match.group(10):  # plain text
            content = match.group(10)
            if content:
                rich_text.append({"type": "text", "text": {"content": content}})

    if not rich_text:
        rich_text.append({"type": "text", "text": {"content": text}})
    return rich_text

def _build_table_block(table_lines: list) -> dict:
    """Markdownテーブルの行リストからNotionテーブルブロックを構築する"""
    # セパレータ行（|---|---| など）を除外
    data_lines = [l for l in table_lines if not re.match(r"^\|[\s|:\-]+\|$", l)]
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
        padded = (row + [""] * col_count)[:col_count]
        safe_cells = []
        for cell in padded:
            # 2000文字制限
            content = cell[:2000]
            safe_cells.append([{"type": "text", "text": {"content": content}}])
        table_rows.append({
            "type": "table_row",
            "table_row": {"cells": safe_cells}
        })

    return {
        "object": "block", "type": "table",
        "table": {
            "table_width": col_count,
            "has_column_header": True,
            "has_row_header": False,
            "children": table_rows
        }
    }

def _split_rich_text(rich_text: list, max_len: int) -> list:
    """
    rich_textリストの合計文字数が max_len を超える場合、
    複数のチャンクに分割する（1ブロック = 1チャンク）。
    """
    total = sum(len(rt.get("text", {}).get("content", "")) for rt in rich_text)
    if total <= max_len:
        return [rich_text]

    chunks, current, current_len = [], [], 0
    for rt in rich_text:
        content = rt.get("text", {}).get("content", "")
        while len(content) > 0:
            space = max_len - current_len
            if space <= 0:
                chunks.append(current)
                current, current_len = [], 0
                space = max_len
            piece = content[:space]
            new_rt = {**rt, "text": {**rt.get("text", {}), "content": piece}}
            current.append(new_rt)
            current_len += len(piece)
            content = content[space:]

    if current:
        chunks.append(current)
    return chunks
