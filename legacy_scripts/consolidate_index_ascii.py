import os
import requests
import json
from dotenv import load_dotenv

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
    # Japanese text escaped: 📌 文書目録 (Knowledge Index)
    title_text = "\ud83d\udccc \u6587\u66f8\u76ee\u9332 (Knowledge Index)"
    
    # Categories: 委員会 (Committee), 事務 (Admin), マニュアル (Manual), その他 (Other)
    cat_committee = "\u59d4\u54e1\u4f1a"
    cat_admin = "\u4e8b\u52d9"
    cat_manual = "\u30de\u30cb\u30e5\u30a2\u30eb"
    cat_other = "\u305d\u306e\u4ed6"
    cat_label = "\u30ab\u30c6\u30b4\u30ea\u30fc"

    print(f"Updating Database {DB_ID}...")
    db_url = f"https://api.notion.com/v1/databases/{DB_ID}"
    db_payload = {
        "title": [{"text": {"content": title_text}}],
        "properties": {
            cat_label: {
                "select": {
                    "options": [
                        {"name": cat_committee, "color": "orange"},
                        {"name": cat_admin, "color": "blue"},
                        {"name": cat_manual, "color": "green"},
                        {"name": cat_other, "color": "gray"}
                    ]
                }
            }
        }
    }
    
    resp = requests.patch(db_url, headers=headers, json=db_payload)
    if resp.status_code == 200:
        print("Done: Database renamed and property added.")
    else:
        print(f"Error: Database update failed: {resp.status_code} {resp.text}")

    # 2. Delete the redundant manual Index page
    print(f"Archiving old Index page {OLD_INDEX_PAGE_ID}...")
    page_url = f"https://api.notion.com/v1/pages/{OLD_INDEX_PAGE_ID}"
    page_payload = {"archived": True}
    resp = requests.patch(page_url, headers=headers, json=page_payload)
    if resp.status_code == 200:
        print("Done: Old Index page archived.")
    else:
        print(f"Error: Old Index page archive failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    consolidate()
