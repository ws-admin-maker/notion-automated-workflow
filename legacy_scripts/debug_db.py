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

COMMITTEE_PAGE_ID = "30c03344-ad0f-80b0-b7c4-d13c0b379ed0"

def debug_create():
    url = "https://api.notion.com/v1/databases"
    payload = {
        "parent": {"type": "page_id", "page_id": COMMITTEE_PAGE_ID},
        "title": [{"text": {"content": "Test Database"}}],
        "properties": {
            "Name": {"title": {}}
        }
    }
    resp = requests.post(url, headers=headers, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")

if __name__ == "__main__":
    debug_create()
