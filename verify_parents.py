import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path="docs-to-notion/.env")
token = os.getenv("NOTION_API_KEY")
headers = {
    "Authorization": f"Bearer {token}",
    "Notion-Version": "2022-06-28"
}

pages = {
    "委員会": "30c03344-ad0f-80b0-b7c4-d13c0b379ed0",
    "委員会組成": "30c03344-ad0f-8133-8a2e-ed28c9261bed",
    "年間スケジュール": "30c03344-ad0f-81db-b1c5-f7f5b0e5521a",
}

def check_parent(name, page_id):
    resp = requests.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers)
    if resp.status_code == 200:
        parent = resp.json().get("parent")
        print(f"{name} ({page_id}) -> Parent: {parent}")
    else:
        print(f"FAILED to check {name}: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    for name, pid in pages.items():
        check_parent(name, pid)
