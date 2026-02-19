import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="docs-to-notion/.env")
token = os.getenv("NOTION_API_KEY")
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

INDEX_PAGE_ID = "30c03344-ad0f-8113-8be5-e15b6fbcd2bd"
DB_ID = "db4b008caf5a4240b942d0e44d09c1ac"

def update_index():
    url = f"https://api.notion.com/v1/blocks/{INDEX_PAGE_ID}/children"
    new_blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🏢 文書管理データベース (Repository)"}}]}
        },
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {"type": "mention", "mention": {"type": "database", "database": {"id": DB_ID}}}
                ]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": "※今後インポートされる文書はすべてここに格納され、「サイドピーク」がデフォルトになります。"}}]}
        }
    ]
    resp = requests.patch(url, headers=headers, json={"children": new_blocks})
    if resp.status_code == 200:
        print("Index updated successfully.")
    else:
        print(f"Failed: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    update_index()
