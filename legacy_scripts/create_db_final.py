from notion_client import Client, APIResponseError
import os
import json
from dotenv import load_dotenv

load_dotenv("docs-to-notion/.env")
client = Client(auth=os.environ["NOTION_API_KEY"])
parent_id = "30c03344-ad0f-80b0-b7c4-d13c0b379ed0" # 委員会

def create():
    try:
        db = client.databases.create(
            parent={"type": "page_id", "page_id": parent_id},
            title=[{"type": "text", "text": {"content": "文書管理データベース"}}],
            properties={"Name": {"title": {}}}
        )
        print(f"SUCCESS: {db['id']}")
    except APIResponseError as e:
        print(f"FAILED: {e.status}")
        print(json.dumps(e.body, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    create()
