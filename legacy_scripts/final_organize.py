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

COMMITTEE_DIR_ID = "30c03344-ad0f-80b0-b7c4-d13c0b379ed0" # 「委員会」
ROOT_PAGE_ID = "30c03344-ad0f-808c-8470-c4534446ad65" # 「あおい調剤情報共有」

PAGES_TO_MOVE_TO_COMMITTEE = [
    "30c03344-ad0f-8133-8a2e-ed28c9261bed", # 委員会組成
    "30c03344-ad0f-81db-b1c5-f7f5b0e5521a", # 年間スケジュール
    "30c03344-ad0f-8140-9411-c2e102e921cf", # 運営委員会まとめ
]

def update_parent(page_id, parent_id, is_workspace=False):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    if is_workspace:
        parent = {"type": "workspace", "workspace": True}
    else:
        parent = {"type": "page_id", "page_id": parent_id}
    
    data = {"parent": parent}
    resp = requests.patch(url, headers=headers, json=data)
    if resp.status_code == 200:
        print(f"SUCCESS: {page_id} -> {parent}")
    else:
        print(f"ERROR: {page_id} -> {parent}: {resp.status_code} {resp.text}")

def main():
    # 1. Move contents into Committee dir
    for pid in PAGES_TO_MOVE_TO_COMMITTEE:
        update_parent(pid, COMMITTEE_DIR_ID)
    
    # 2. Move Committee dir to workspace root
    update_parent(COMMITTEE_DIR_ID, None, is_workspace=True)

if __name__ == "__main__":
    main()
