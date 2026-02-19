# -*- coding: utf-8 -*-
import os
import requests
import json
from dotenv import load_dotenv

# Use explicit encoding for load_dotenv is not supported, but we can ensure environment is clean
load_dotenv(dotenv_path="docs-to-notion/.env")
token = os.getenv("NOTION_API_KEY")
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

DB_ID = "db4b008caf5a4240b942d0e44d09c1ac"
OLD_INDEX_PAGE_ID = "30c03344-ad0f-8113-8be5-e15b6fbcd2bd"

def consolidate():
    # 1. Rename Database and Add Categorization
    print(f"Updating Database {DB_ID}...")
    db_url = f"https://api.notion.com/v1/databases/{DB_ID}"
    db_payload = {
        "title": [{"text": {"content": "📌 文書目録 (Knowledge Index)"}}],
        "properties": {
            "カテゴリー": {
                "select": {
                    "options": [
                        {"name": "委員会", "color": "orange"},
                        {"name": "事務", "color": "blue"},
                        {"name": "マニュアル", "color": "green"},
                        {"name": "その他", "color": "gray"}
                    ]
                }
            }
        }
    }
    # Ensure payload is sent as UTF-8
    resp = requests.patch(db_url, headers=headers, data=json.dumps(db_payload, ensure_ascii=False).encode('utf-8'))
    if resp.status_code == 200:
        print("✅ Database renamed and property added.")
    else:
        print(f"❌ Database update failed: {resp.status_code} {resp.text}")

    # 2. Delete the redundant manual Index page
    print(f"Archiving old Index page {OLD_INDEX_PAGE_ID}...")
    page_url = f"https://api.notion.com/v1/pages/{OLD_INDEX_PAGE_ID}"
    page_payload = {"archived": True}
    resp = requests.patch(page_url, headers=headers, json=page_payload)
    if resp.status_code == 200:
        print("✅ Old Index page archived.")
    else:
        print(f"❌ Old Index page archive failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    consolidate()
