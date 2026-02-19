# -*- coding: utf-8 -*-
import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path="docs-to-notion/.env")
token = os.getenv("NOTION_API_KEY")
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

DB_ID = "db4b008caf5a4240b942d0e44d09c1ac"
# Standalone pages to move into DB
PAGES_TO_MOVE = {
    "30c03344-ad0f-8133-8a2e-ed28c9261bed": {"title": "委員会組成", "cat": "委員会", "source": "R8委員会編成.xlsx"},
    "30c03344-ad0f-81db-b1c5-f7f5b0e5521a": {"title": "運営委員会　R8活動予定 - 年間スケジュール", "cat": "委員会", "source": "運営委員会　R8活動予定.xlsx"},
    "30c03344-ad0f-8140-9411-c2e102e921cf": {"title": "運営委員会　R8活動予定 - 運営委員会まとめ", "cat": "委員会", "source": "運営委員会　R8活動予定.xlsx"},
}

# Redundant items to archive (ID: 委員会 folder)
ITEMS_TO_ARCHIVE = [
    "30c03344-ad0f-80b0-b7c4-d13c0b379ed0", # 「委員会」フォルダ
]

def cleanup_notion():
    print("Moving standalone pages into Database...")
    for pid, info in PAGES_TO_MOVE.items():
        url = f"https://api.notion.com/v1/pages/{pid}"
        payload = {
            "parent": {"type": "database_id", "database_id": DB_ID},
            "properties": {
                "Name": {"title": [{"text": {"content": info["title"]}}]},
                "種別": {"select": {"name": "Excel"}},
                "カテゴリー": {"select": {"name": info["cat"]}},
                "元ファイル": {"rich_text": [{"text": {"content": info["source"]}}]},
                "インポート日時": {"date": {"start": datetime.now().isoformat()}}
            }
        }
        resp = requests.patch(url, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        if resp.status_code == 200:
            print(f"  ✅ Moved and updated properties: {info['title']}")
        else:
            print(f"  ❌ Failed to move {info['title']}: {resp.status_code} {resp.text}")

    print("\nArchiving redundant folders...")
    for rid in ITEMS_TO_ARCHIVE:
        url = f"https://api.notion.com/v1/pages/{rid}"
        resp = requests.patch(url, headers=headers, json={"archived": True})
        if resp.status_code == 200:
            print(f"  ✅ Archived: {rid}")
        else:
            print(f"  ❌ Failed to archive {rid}: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    cleanup_notion()
