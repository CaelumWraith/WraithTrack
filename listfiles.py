# List all files in data directory that start with the current date
import glob
from pathlib import Path

data_dir = Path('data')
current_date = "2025-02-07"

print("Available track files:")
for file in data_dir.glob(f"{current_date}__track__*"):
    print(f"  {file.name}")