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

# 「委員会」ページのID
COMMITTEE_PAGE_ID = "30c03344-ad0f-80b0-b7c4-d13c0b379ed0"

def create_document_database():
    url = "https://api.notion.com/v1/databases"
    payload = {
        "parent": {"type": "page_id", "page_id": COMMITTEE_PAGE_ID},
        "title": [
            {
                "type": "text",
                "text": {"content": "文書管理データベース (Document Repository)"}
            }
        ],
        "properties": {
            "Name": {"title": {}},
            "種別": {
                "select": {
                    "options": [
                        {"name": "Excel", "color": "green"},
                        {"name": "Word", "color": "blue"}
                    ]
                }
            },
            "元ファイル": {"rich_text": {}},
            "インポート日時": {"date": {}}
        }
    }
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        db = resp.json()
        print(f"Database created: {db['url']}")
        print(f"Database ID: {db['id']}")
        return db['id']
    else:
        print(f"Failed: {resp.status_code} {resp.text}")
        return None

if __name__ == "__main__":
    create_document_database()
