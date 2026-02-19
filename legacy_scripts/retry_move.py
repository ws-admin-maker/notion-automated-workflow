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

target = "30c03344-ad0f-80b0-b7c4-d13c0b379ed0"
pages = ["30c03344-ad0f-81db-b1c5-f7f5b0e5521a", "30c03344-ad0f-8140-9411-c2e102e921cf"]

for p in pages:
    resp = requests.patch(f"https://api.notion.com/v1/pages/{p}", headers=headers, json={"parent": {"page_id": target}})
    print(f"{p}: {resp.status_code}")
    if resp.status_code != 200:
        print(resp.text)
