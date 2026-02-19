import pandas as pd
import os

files = ['R8委員会編成.xlsx', '運営委員会　R8活動予定.xlsx']
print("Starting Excel Inspection...")
for f in files:
    if os.path.exists(f):
        print(f"--- {f} ---")
        try:
            df = pd.read_excel(f)
            # Print columns and first few rows
            print(f"Columns: {list(df.columns)}")
            print(df.head().to_string())
            print("\n")
        except Exception as e:
            print(f"Error reading {f}: {e}")
    else:
        print(f"File not found: {f}")
