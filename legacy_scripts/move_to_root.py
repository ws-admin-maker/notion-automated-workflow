import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="docs-to-notion/.env")
NOTION_TOKEN = os.getenv("NOTION_API_KEY")

PAGE_ID_TO_MOVE = "30c03344-ad0f-80b0-b7c4-d13c0b379ed0"  # 「委員会」ページ

def move_to_workspace_root(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = {
        "parent": {"workspace": True}
    }
    resp = requests.patch(url, headers=headers, json=data)
    if resp.status_code == 200:
        print(f"Successfully moved {page_id} to workspace root.")
    else:
        print(f"Failed to move {page_id}: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    move_to_workspace_root(PAGE_ID_TO_MOVE)
