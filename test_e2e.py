#!/usr/bin/env python3
"""Complete end-to-end test of backend API."""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def login():
    """Login and get token."""
    print("1. Logging in...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    token = response.json()["access_token"]
    print(f"✅ Got token: {token[:50]}...")
    return token

def upload_images(token, product_id, image_paths):
    """Upload reference images."""
    print(f"\n2. Uploading {len(image_paths)} reference images...")
    headers = {"Authorization": f"Bearer {token}"}
    
    files = []
    for img_path in image_paths:
        p = Path(img_path)
        print(f"   Checking: {p}")
        print(f"   Exists: {p.exists()}")
        print(f"   Is file: {p.is_file() if p.exists() else False}")
        if p.exists():
            files.append(("files", (p.name, open(p, "rb"), "image/png")))
    
    print(f"   Found {len(files)} files to upload")
    
    if not files:
        print("❌ No files found to upload!")
        return []
    
    response = requests.post(
        f"{BASE_URL}/api/products/{product_id}/upload-references",
        headers=headers,
        files=files
    )
    
    # Close file handles
    for _, (_, fh, _) in files:
        fh.close()
    
    if response.status_code == 200:
        images = response.json()
        print(f"✅ Uploaded {len(images)} images")
        for img in images:
            print(f"   - {img['filename']} ({img['width']}x{img['height']})")
        return images
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return []

def analyze_product(token, product_id):
    """Trigger GPT analysis."""
    print(f"\n3. Analyzing product {product_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/api/products/{product_id}/analyze",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Analysis complete")
        print(f"   - Specification ID: {result['specification_id']}")
        print(f"   - Version: {result['version']}")
        print(f"   - Dimensions: {result['dimensions']}")
        print(f"   - Colors: {result['colors']}")
        return result
    else:
        print(f"❌ Analysis failed: {response.status_code}")
        print(response.text)
        return None

def generate_images(token, product_id):
    """Create generation request."""
    print(f"\n4. Creating generation request...")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "custom_prompt": "professional product photography, clean background, studio lighting",
        "count": 2,
        "aspect_ratio": "1:1",
        "resolution": "1024x1024"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/products/{product_id}/generate",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Generation request created")
        print(f"   - Request ID: {result['id']}")
        print(f"   - Status: {result['status']}")
        return result
    else:
        print(f"❌ Generation failed: {response.status_code}")
        print(response.text)
        return None

def check_generation_status(token, request_id, max_wait=60):
    """Poll generation status."""
    print(f"\n5. Waiting for generation to complete...")
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        response = requests.get(
            f"{BASE_URL}/api/generation-requests/{request_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result['status']
            print(f"   Status: {status}")
            
            if status == 'completed':
                print(f"✅ Generation completed!")
                print(f"   - Generated {result['images_generated']} images")
                return result
            elif status == 'failed':
                print(f"❌ Generation failed: {result.get('error_message')}")
                return result
            
        time.sleep(2)
    
    print(f"⏱️ Timeout waiting for generation")
    return None

def main():
    """Run complete end-to-end test."""
    print("=" * 60)
    print("Backend API End-to-End Test")
    print("=" * 60)
    
    # Step 1: Login
    token = login()
    
    # Step 2: Upload reference images
    project_root = Path(__file__).parent
    image_paths = [
        project_root / "data/stasher_half_gallon/Screenshot 2026-01-23 at 11.02.34 AM.png",
        project_root / "data/stasher_half_gallon/Screenshot 2026-01-23 at 11.03.14 AM.png",
        project_root / "data/stasher_half_gallon/Screenshot 2026-01-23 at 11.03.24 AM.png",
    ]
    
    uploaded_images = upload_images(token, 1, image_paths)
    if not uploaded_images:
        return
    
    # Step 3: Analyze product
    analysis = analyze_product(token, 1)
    if not analysis:
        return
    
    # Step 4: Generate images
    generation = generate_images(token, 1)
    if not generation:
        return
    
    # Step 5: Check status
    final_result = check_generation_status(token, generation['id'])
    
    print("\n" + "=" * 60)
    if final_result and final_result['status'] == 'completed':
        print("✅ END-TO-END TEST PASSED")
    else:
        print("❌ END-TO-END TEST FAILED")
    print("=" * 60)

if __name__ == "__main__":
    main()
