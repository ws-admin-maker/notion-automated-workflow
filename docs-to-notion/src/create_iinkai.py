"""
チームスペース直下に「委員会組成」ページを作成し、
その中にExcelデータをインポートするスクリプト。
"""
import os, sys, glob
from notion_client import Client
from dotenv import load_dotenv
from rich.console import Console

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from excel_reader import read_excel
from markdown_converter import convert_to_markdown
from block_builder import markdown_to_notion_blocks

load_dotenv()
console = Console()
BATCH_SIZE = 100

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_PARENT_PAGE_ID = os.environ["NOTION_PARENT_PAGE_ID"]  # Accessible parent

client = Client(auth=NOTION_API_KEY)

def create_container_page(parent_id: str, title: str) -> str:
    """新しいコンテナページを作成してそのIDを返す"""
    console.print(f"[bold green]📁 コンテナページ作成中: '{title}'[/bold green]")
    response = client.pages.create(
        parent={"page_id": parent_id},
        properties={"title": [{"text": {"content": title}}]},
        children=[]
    )
    page_id = response["id"]
    url = response["url"]
    console.print(f"  ✅ コンテナページ作成: {url}")
    return page_id

def create_page_with_content(parent_id: str, title: str, blocks: list) -> str:
    """コンテンツ付きのページを作成してそのURLを返す"""
    first_batch = blocks[:BATCH_SIZE]
    remaining = blocks[BATCH_SIZE:]

    response = client.pages.create(
        parent={"page_id": parent_id},
        properties={"title": [{"text": {"content": title}}]},
        children=first_batch
    )
    page_id = response["id"]
    url = response["url"]

    for i in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[i:i + BATCH_SIZE]
        client.blocks.children.append(block_id=page_id, children=batch)

    return url

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Step 1: 「委員会組成」コンテナページを作成
    container_page_id = create_container_page(NOTION_PARENT_PAGE_ID, "委員会組成")

    # Step 2: inputフォルダのExcelを処理
    input_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "input")
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(".xlsx")]

    if not files:
        console.print("[red]❌ input/ にExcelファイルが見つかりません[/red]")
        return

    console.print(f"[bold]📊 {len(files)}ファイルを処理します[/bold]")
    for file_path in files:
        name = os.path.basename(file_path)
        console.print(f"\n[bold blue]📄 {name}[/bold blue]")
        try:
            sheets = read_excel(file_path)
            console.print(f"  ✅ {len(sheets)}シート検出")
            for sheet in sheets:
                md = convert_to_markdown(sheet, source_type="excel")
                blocks = markdown_to_notion_blocks(md)
                title = f"{os.path.splitext(name)[0]} - {sheet.name}"
                url = create_page_with_content(container_page_id, title, blocks)
                console.print(f"  ✅ ページ作成: {url}")
        except Exception as e:
            console.print(f"  [red]❌ エラー: {e}[/red]")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
