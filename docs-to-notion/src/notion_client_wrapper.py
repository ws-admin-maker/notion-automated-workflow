import os
from notion_client import Client
from dotenv import load_dotenv
from typing import List

load_dotenv()
BATCH_SIZE = 100  # Notion APIの上限

class NotionPageCreator:
    def __init__(self):
        self.client = Client(auth=os.environ["NOTION_API_KEY"])
        self.parent_page_id = os.environ["NOTION_PARENT_PAGE_ID"]

    def create_page(self, title: str, blocks: List[dict], parent_id: str = None) -> str:
        """
        ページを作成し、ブロックを100件ずつのバッチで追加する。
        parent_id が指定されている場合はそちらを親にする。
        """
        pid = parent_id or self.parent_page_id
        
        # 最初の100件と残りを分割
        first_batch = blocks[:BATCH_SIZE]
        remaining = blocks[BATCH_SIZE:]

        print(f"  Creating page: '{title}' (blocks: {len(blocks)})")
        response = self.client.pages.create(
            parent={"page_id": pid},
            properties={"title": [{"text": {"content": title}}]},
            children=first_batch
        )
        page_id = response["id"]
        url = response["url"]

        # 残りのブロックを100件ずつ追加
        for i in range(0, len(remaining), BATCH_SIZE):
            batch = remaining[i:i + BATCH_SIZE]
            print(f"  Appending batch {i // BATCH_SIZE + 2} ({len(batch)} blocks)...")
            self.client.blocks.children.append(block_id=page_id, children=batch)

        return url

    def create_container_page(self, title: str, parent_id: str = None) -> str:
        """空のコンテナページを作成し、そのIDを返す"""
        pid = parent_id or self.parent_page_id
        response = self.client.pages.create(
            parent={"page_id": pid},
            properties={"title": [{"text": {"content": title}}]},
            children=[]
        )
        return response["id"]
