import pandas as pd
import os
import sys

def read_data(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    if filepath.endswith('.parquet'):
        df = pd.read_parquet(filepath)
    else:
        df = pd.read_csv(filepath)
    
    print(f"--- Data Preview: {os.path.basename(filepath)} ---")
    print(df.head())
    print(f"Total Rows: {len(df)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/read_data.py <path_to_file>")
    else:
        read_data(sys.argv[1])
