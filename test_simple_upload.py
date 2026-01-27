#!/usr/bin/env python3
import requests
import os

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc2OTU0ODUzMH0.kWXjQ6OEHsIFFfvLnMFxk-rtMIB1o6zASkXCIUOWLpg"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Use os.listdir to find files
data_dir = "/Users/Brian.Douglas/GXM_DEV/2026-01-23_product_describer/data/stasher_half_gallon"
filenames = [f for f in os.listdir(data_dir) if f.endswith('.png')][:3]

print(f"Found {len(filenames)} files to upload:")
for fname in filenames:
    print(f"  - {fname}")

files = []
for fname in filenames:
    full_path = os.path.join(data_dir, fname)
    files.append(("files", (fname, open(full_path, "rb"), "image/png")))

print("\nUploading...")
response = requests.post(
    f"{BASE_URL}/api/products/1/upload-references",
    headers=headers,
    files=files
)

print(f"\nStatus: {response.status_code}")
if response.status_code == 200:
    print("✅ Upload successful!")
    for img in response.json():
        print(f"   - {img['filename']} ({img['width']}x{img['height']})")
else:
    print(f"❌ Upload failed:")
    print(response.text)

# Close file handles
for _, (_, fh, _) in files:
    fh.close()
