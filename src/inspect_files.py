import pandas as pd
from pathlib import Path

folder = Path("data/raw/indeed")

for file in sorted(folder.glob("DE_*.csv")) + sorted(folder.glob("US_*.csv"))[:2]:
    df = pd.read_csv(file)
    print("=" * 70)
    print(file.name, "->", df.shape[0], "rows")
    print("Columns:", df.columns.tolist())
    print(df.head(3).to_string())