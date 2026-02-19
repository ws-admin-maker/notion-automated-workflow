import requests
import json

NOTION_TOKEN = "ntn_Lr8601387675RHm46nctBabcqoVzBNzsUNZyI443J0S3S7"

def list_accessible_pages():
    url = "https://api.notion.com/v1/search"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # Empty query searches for everything
    payload = {
        "query": "",
        "page_size": 100
    }
    response = requests.post(url, headers=headers, json=payload)
    with open("accessible_pages.txt", "w", encoding="utf-8") as f:
        if response.status_code == 200:
            results = response.json().get("results", [])
            f.write(f"Found {len(results)} accessible objects.\n")
            print(f"Found {len(results)} accessible objects.")
            for item in results:
                obj_type = item.get("object")
                if obj_type == "page":
                    title_prop = item.get("properties", {}).get("title", {}).get("title", [])
                    title = title_prop[0].get("plain_text") if title_prop else "No Title"
                    f.write(f"[PAGE] {title} (ID: {item['id']})\n")
                    parent = item.get("parent", {})
                    f.write(f"       Parent: {parent.get('type')} - {parent.get(parent.get('type', ''), 'Unknown')}\n")
                    
                elif obj_type == "database":
                    title_prop = item.get("title", [])
                    title = title_prop[0].get("plain_text") if title_prop else "No Title"
                    f.write(f"[DATABASE] {title} (ID: {item['id']})\n")
        else:
            f.write(f"Error searching: {response.status_code}\n{response.text}\n")
            print(f"Error searching: {response.status_code}")

if __name__ == "__main__":
    list_accessible_pages()
