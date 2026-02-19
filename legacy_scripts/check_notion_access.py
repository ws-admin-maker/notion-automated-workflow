import requests

NOTION_TOKEN = "ntn_Lr8601387675RHm46nctBabcqoVzBNzsUNZyI443J0S3S7"
PAGE_ID = "180a308cd37244a98086b739510811f8"

def check_access():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    # Try retrieving as Page
    print(f"Checking Page {PAGE_ID}...")
    resp = requests.get(f"https://api.notion.com/v1/pages/{PAGE_ID}", headers=headers)
    if resp.status_code == 200:
        print("Success! It is a PAGE.")
        print(f"Title/Info: {resp.json().get('properties', {}).keys()}")
        return
    else:
        print(f"Not a Page or No Access: {resp.status_code} {resp.text}")

    # Try retrieving as Database
    print(f"Checking Database {PAGE_ID}...")
    resp = requests.get(f"https://api.notion.com/v1/databases/{PAGE_ID}", headers=headers)
    if resp.status_code == 200:
        print("Success! It is a DATABASE.")
        print(f"Title: {resp.json().get('title', [])}")
        return
    else:
        print(f"Not a Database or No Access: {resp.status_code} {resp.text}")

if __name__ == "__main__":
    check_access()
