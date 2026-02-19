import sys, os
from rich.console import Console

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

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
    raise ValueError(f"未対応形式: {ext}")

def process_file(path: str, creator: NotionPageCreator, parent_id: str = None):
    name = os.path.basename(path)
    try:
        ftype = detect_type(path)
        console.print(f"\n[bold blue]📄 処理中: {name} ({ftype})[/bold blue]")

        if ftype == "word_legacy":
            console.print("  🔄 .doc → .docx に変換中...")
            path = convert_doc_to_docx(path)
            ftype = "word"
            console.print("  ✅ 変換完了")

        if ftype == "excel":
            sheets = read_excel(path)
            console.print(f"  ✅ {len(sheets)}シート検出")
            for sheet in sheets:
                md = convert_to_markdown(sheet, source_type="excel")
                blocks = markdown_to_notion_blocks(md)
                title = f"{os.path.splitext(name)[0]} - {sheet.name}"
                url = creator.create_page(title=title, blocks=blocks, parent_id=parent_id)
                console.print(f"  ✅ ページ作成: {url}")

        elif ftype == "word":
            elements = read_word(path)
            console.print(f"  ✅ {len(elements)}要素検出")
            md = convert_to_markdown(elements, source_type="word")
            blocks = markdown_to_notion_blocks(md)
            title = os.path.splitext(name)[0]
            url = creator.create_page(title=title, blocks=blocks, parent_id=parent_id)
            console.print(f"  ✅ ページ作成: {url}")

    except Exception as e:
        console.print(f"  [red]❌ エラー: {e}[/red]")
        import traceback
        traceback.print_exc()

def main():
    try:
        creator = NotionPageCreator()
    except Exception as e:
        console.print(f"[red]❌ 初期化エラー: {e}[/red]")
        return

    # inputフォルダのファイルを検出
    input_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input")
    files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if os.path.splitext(f)[1].lower() in SUPPORTED
    ]

    if not files:
        console.print("[red]❌ input/ にファイルが見つかりません (.xlsx/.docx/.doc)[/red]")
        return

    console.print(f"[bold green]🚀 {len(files)}ファイルを処理[/bold green]")
    for f in files:
        process_file(f, creator)

if __name__ == "__main__":
    main()
