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

# チームスペースのルート
TEAMSPACE_ROOT_ID = "30c03344-ad0f-808c-8470-c4534446ad65"

# インデックスの内容
INDEX_CONTENT = [
    {
        "object": "block",
        "type": "heading_1",
        "heading_1": {"rich_text": [{"type": "text", "text": {"content": "Knowledge Index (目録)"}}]}
    },
    {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": "Antigravity Agentによって管理されているドキュメントの索引です。"}}]}
    },
    {
        "object": "block",
        "type": "divider",
        "divider": {}
    },
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "📁 委員会プロジェクト"}}]}
    },
    {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [
                {"type": "mention", "mention": {"type": "page", "page": {"id": "30c03344-ad0f-80b0-b7c4-d13c0b379ed0"}}}
            ]
        }
    }
]

def create_index_page():
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": {"page_id": TEAMSPACE_ROOT_ID},
        "properties": {
            "title": [{"text": {"content": "📌 目録 (Knowledge Index)"}}]
        },
        "children": INDEX_CONTENT
    }
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        page = resp.json()
        print(f"Index created: {page['url']}")
        return page['id']
    else:
        print(f"Failed: {resp.status_code} {resp.text}")
        return None

if __name__ == "__main__":
    create_index_page()
