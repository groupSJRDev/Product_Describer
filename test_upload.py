#!/usr/bin/env python3
"""Quick script to test image upload via API."""
import sys
import requests
import json
from pathlib import Path

print("Starting upload test...", flush=True)

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2OTU0ODUzMH0.kWXjQ6OEHsIFFfvLnMFxk-rtMIB1o6zASkXCIUOWLpg"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Upload reference images
project_root = Path(__file__).parent
image_files = [
    project_root / "data/stasher_half_gallon/Screenshot 2026-01-23 at 11.02.34 AM.png",
    project_root / "data/stasher_half_gallon/Screenshot 2026-01-23 at 11.03.14 AM.png",
    project_root / "data/stasher_half_gallon/Screenshot 2026-01-23 at 11.03.24 AM.png",
]

files = []
for img_path in image_files:
    p = Path(img_path)
    print(f"Checking {img_path}: exists={p.exists()}")
    if p.exists():
        files.append(("images", (p.name, open(p, "rb"), "image/png")))
        
print(f"Found {len(files)} files to upload")

data = {"primary_image_index": 0}

print("Uploading reference images...")
response = requests.post(
    f"{BASE_URL}/api/products/1/upload-references",
    headers=headers,
    files=files,
    data=data
)

print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

# Close file handles
for _, (_, fh, _) in files:
    fh.close()
