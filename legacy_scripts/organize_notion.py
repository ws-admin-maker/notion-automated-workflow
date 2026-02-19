import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="docs-to-notion/.env")
NOTION_TOKEN = os.getenv("NOTION_API_KEY")

TARGET_PARENT_ID = "30c03344-ad0f-80b0-b7c4-d13c0b379ed0"  # 「委員会」ページ

PAGES_TO_MOVE = [
    "30c03344-ad0f-8133-8a2e-ed28c9261bed",  # 委員会組成
    "30c03344-ad0f-81db-b1c5-f7f5b0e5521a",  # 運営委員会　R8活動予定 - 年間スケジュール
    "30c03344-ad0f-8140-9411-c2e102e921cf",  # 運営委員会　R8活動予定 - 運営委員会まとめ
]

def move_page(page_id, parent_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    data = {
        "parent": {"page_id": parent_id}
    }
    resp = requests.patch(url, headers=headers, json=data)
    if resp.status_code == 200:
        print(f"Successfully moved {page_id} to {parent_id}")
    else:
        print(f"Failed to move {page_id}: {resp.status_code} {resp.text}")

def main():
    for pid in PAGES_TO_MOVE:
        move_page(pid, TARGET_PARENT_ID)

if __name__ == "__main__":
    main()
