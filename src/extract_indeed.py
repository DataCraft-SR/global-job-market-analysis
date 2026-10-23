import requests
from pathlib import Path

# Countries to download (Indeed folder names use 2-letter codes)
COUNTRIES = ["DE", "US", "GB", "FR", "NL", "ES", "IT", "CA", "AU", "IN"]

API = "https://api.github.com/repos/hiring-lab/job_postings_tracker/contents"
OUT = Path("data/raw/indeed")
OUT.mkdir(parents=True, exist_ok=True)

# 1. List the folders in the repo
root = requests.get(API, timeout=30).json()
folders = {item["name"].upper(): item["name"]
           for item in root if item["type"] == "dir"}
print("Folders in repo:", sorted(folders))

# 2. Download every CSV inside each country folder
for code in COUNTRIES:
    if code not in folders:
        print(f"-- {code}: no folder found, skipping")
        continue
    files = requests.get(f"{API}/{folders[code]}", timeout=30).json()
    for f in files:
        if f["name"].endswith(".csv"):
            data = requests.get(f["download_url"], timeout=60).content
            (OUT / f"{code}_{f['name']}").write_bytes(data)
            print(f"Saved {code}_{f['name']}  ({len(data)//1024} KB)")

print("\nDone! Files are in data/raw/indeed/")