import os
from notion_client import Client
from dotenv import load_dotenv
from typing import List
from datetime import datetime

load_dotenv()
BATCH_SIZE = 100  # Notion APIの上限

class NotionPageCreator:
    def __init__(self):
        self.client = Client(auth=os.environ["NOTION_API_KEY"])
        # チームスペースのメインページ（親ページ）
        self.teamspace_id = "30c03344-ad0f-808c-8470-c4534446ad65" 
        self.database_id = os.environ.get("NOTION_DATABASE_ID", "db4b008caf5a4240b942d0e44d09c1ac")

    def ensure_category_folder(self, category_name: str) -> str:
        """
        指定したカテゴリーのフォルダ（ページ）が存在するか確認し、なければ作成する。
        フォルダ内にはデータベースのリンクビューを設置する。
        """
        folder_title = f"📁 {category_name}"
        
        # 1. 既存のフォルダ（ページ）を検索
        search_results = self.client.search(
            query=folder_title,
            filter={"property": "object", "value": "page"}
        ).get("results", [])
        
        for res in search_results:
            title_list = res.get("properties", {}).get("title", {}).get("title", [])
            if title_list and title_list[0].get("plain_text") == folder_title:
                return res["id"]

        # 2. 存在しない場合は新規作成
        print(f"  Creating category folder: {folder_title}")
        
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": f"{category_name} の文書一覧"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [
                    {"type": "text", "text": {"content": "※以下のデータベースビューでサイドピークをご利用いただけます。"}},
                    {"type": "text", "text": {"content": "\n（フィルター設定：カテゴリー が "}},
                    {"type": "text", "annotations": {"italic": True}, "text": {"content": category_name}},
                    {"type": "text", "text": {"content": " に一致するもの）"}}
                ]}
            },
            {
                "object": "block",
                "type": "link_to_page",
                "link_to_page": {
                    "type": "database_id",
                    "database_id": self.database_id
                }
            }
        ]
        
        response = self.client.pages.create(
            parent={"page_id": self.teamspace_id},
            properties={"title": [{"text": {"content": folder_title}}]},
            children=children
        )
        return response["id"]

    def create_page(self, title: str, blocks: List[dict], parent_id: str = None, 
                    ftype: str = "Other", source: str = "", cat: str = "その他") -> str:
        """
        ページを作成し、ブロックを100件ずつのバッチで追加する。
        """
        # 親IDが指定されていない場合はデータベースへ
        pid = parent_id or self.database_id
        
        # 最初の100件と残りを分割
        first_batch = blocks[:BATCH_SIZE]
        remaining = blocks[BATCH_SIZE:]

        print(f"  Creating database item: '{title}' (category: {cat})")
        
        parent_obj = {"database_id": pid}
        properties = {
            "Name": {"title": [{"text": {"content": title}}]},
            "種別": {"select": {"name": ftype}},
            "カテゴリー": {"select": {"name": cat}},
            "元ファイル": {"rich_text": [{"text": {"content": source}}]},
            "インポート日時": {"date": {"start": datetime.now().isoformat()}}
        }

        response = self.client.pages.create(
            parent=parent_obj,
            properties=properties,
            children=first_batch
        )
        page_id = response["id"]
        url = response["url"]

        for i in range(0, len(remaining), BATCH_SIZE):
            batch = remaining[i:i + BATCH_SIZE]
            self.client.blocks.children.append(block_id=page_id, children=batch)

        return url

    def create_container_page(self, title: str, parent_id: str = None) -> str:
        """空のコンテナページを作成し、そのIDを返す"""
        pid = parent_id or self.teamspace_id
        response = self.client.pages.create(
            parent={"page_id": pid},
            properties={"title": [{"text": {"content": title}}]},
            children=[]
        )
        return response["id"]
