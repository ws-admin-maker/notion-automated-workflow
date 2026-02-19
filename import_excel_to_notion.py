import pandas as pd
import requests
import json
import os
import sys

# Constants
NOTION_TOKEN = "ntn_Lr8601387675RHm46nctBabcqoVzBNzsUNZyI443J0S3S7"
PAGE_ID = "180a308cd37244a98086b739510811f8"
FILES_TO_PROCESS = ['R8委員会編成.xlsx', '運営委員会　R8活動予定.xlsx']

def read_excel_to_markdown(file_path):
    """
    Reads an Excel file and converts each sheet into a Markdown table string.
    Returns a dictionary of {sheet_name: markdown_string}.
    """
    try:
        xls = pd.ExcelFile(file_path)
        sheet_data = {}
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            
            # fillna to avoid "nan" in markdown
            df = df.fillna("")
            
            # Convert to markdown
            md_table = df.to_markdown(index=False)
            sheet_data[sheet_name] = md_table
        return sheet_data
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def append_children_to_block(block_id, children):
    """
    Appends blocks to a Notion page/block.
    """
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Notion API has a limit of 100 children per request
    # We will send them in chunks if necessary, but here we process file by file
    
    data = {
        "children": children
    }
    
    response = requests.patch(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Successfully appended blocks.")
        return response.json()
    else:
        error_msg = f"Error appending blocks: {response.status_code}\n{response.text}"
        print(error_msg)
        with open("error.log", "w", encoding="utf-8") as f:
            f.write(error_msg)
        return None

def main():
    if not os.path.exists("venv"): 
         # Assuming user has packages installed globally or we are in an env where we can just run.
         # 'tabulate' is needed for to_markdown
         pass

    blocks_to_add = []

    for file_name in FILES_TO_PROCESS:
        if not os.path.exists(file_name):
            print(f"File not found: {file_name}")
            continue
            
        print(f"Processing {file_name}...")
        
        # Add Heading 2 for File Name
        blocks_to_add.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": f"File: {file_name}"}}]
            }
        })
        
        sheet_data = read_excel_to_markdown(file_name)
        if sheet_data:
            for sheet_name, md_content in sheet_data.items():
                # Add Heading 3 for Sheet Name
                blocks_to_add.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": f"Sheet: {sheet_name}"}}]
                    }
                })
                
                # Truncate content if too long (Notion block limit is 2000 chars strictly speaking, 
                # but code blocks can hold more usually. Safest is to split if huge, but let's try simple first)
                # Actually, rich_text text content max is 2000. Code block text is also rich_text.
                # If table is huge, this might fail. We'll handle basic cases.
                
                if len(md_content) > 2000:
                    md_content = md_content[:1900] + "\n...(truncated)"
                
                # Add Code Block with Markdown
                blocks_to_add.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "caption": [],
                        "rich_text": [{"type": "text", "text": {"content": md_content}}],
                        "language": "markdown"
                    }
                })

    if blocks_to_add:
        print(f"Sending {len(blocks_to_add)} blocks to Notion...")
        # Send in chunks of 100 just in case
        chunk_size = 100
        for i in range(0, len(blocks_to_add), chunk_size):
            chunk = blocks_to_add[i:i + chunk_size]
            append_children_to_block(PAGE_ID, chunk)
    else:
        print("No content to add.")

if __name__ == "__main__":
    main()
