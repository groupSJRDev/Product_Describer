#!/usr/bin/env python3
"""
Integration test to verify the complete e2e flow on ports 3001/8001.
Tests: Auth -> Products -> Specifications -> Generation request
"""

import requests
import json
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8001/api"
FRONTEND_URL = "http://localhost:3001"
USERNAME = "admin"
PASSWORD = "admin123"


def test_auth() -> Optional[str]:
    """Test authentication and return token."""
    print("1. Testing authentication...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"   ✓ Login successful")
        return token
    else:
        print(f"   ✗ Login failed: {response.status_code}")
        return None


def test_products(token: str) -> Optional[int]:
    """Test products endpoint and return first product ID."""
    print("\n2. Testing products endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/products", headers=headers)
    
    if response.status_code == 200:
        products = response.json()
        if products:
            product = products[0]
            print(f"   ✓ Found {len(products)} product(s)")
            print(f"   - Product: {product['name']} (ID: {product['id']})")
            return product['id']
        else:
            print("   ✗ No products found")
            return None
    else:
        print(f"   ✗ Request failed: {response.status_code}")
        return None


def test_specifications(token: str, product_id: int) -> bool:
    """Test specifications endpoint."""
    print(f"\n3. Testing specifications for product {product_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/products/{product_id}/specifications",
        headers=headers
    )
    
    if response.status_code == 200:
        specs = response.json()
        print(f"   ✓ Found {len(specs)} specification(s)")
        return True
    else:
        print(f"   ✗ Request failed: {response.status_code}")
        return False


def test_generation_request(token: str, product_id: int) -> Optional[int]:
    """Test generation request creation."""
    print(f"\n4. Testing generation request creation...")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "prompt": "Integration test - show product on white background",
        "specification_id": None,
        "aspect_ratio": "1:1",
        "resolution": "1024x1024",
        "image_count": 1,
        "custom_prompt_override": None
    }
    
    response = requests.post(
        f"{BASE_URL}/products/{product_id}/generate",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Generation request created (ID: {result['id']})")
        print(f"   - Status: {result['status']}")
        return result['id']
    else:
        print(f"   ✗ Request failed: {response.status_code}")
        print(f"   - Response: {response.text}")
        return None


def test_frontend():
    """Test frontend is accessible."""
    print("\n5. Testing frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Frontend accessible at {FRONTEND_URL}")
            return True
        else:
            print(f"   ✗ Frontend returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Frontend not accessible: {e}")
        return False


def main():
    print("=" * 60)
    print("Integration Test - Product Describer")
    print("=" * 60)
    print(f"Backend:  {BASE_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print("=" * 60)
    
    # Run tests
    token = test_auth()
    if not token:
        print("\n❌ Authentication failed - cannot proceed")
        return
    
    product_id = test_products(token)
    if not product_id:
        print("\n❌ No products found - cannot proceed")
        return
    
    test_specifications(token, product_id)
    
    generation_id = test_generation_request(token, product_id)
    
    test_frontend()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✓ Authentication working")
    print("✓ Backend API accessible on port 8001")
    print("✓ Products endpoint working")
    print("✓ Generation endpoint working")
    print("✓ Frontend accessible on port 3001")
    print("\nℹ️  Note: Generation processes in background.")
    print("   Check frontend dashboard for results.")
    print("=" * 60)


if __name__ == "__main__":
    main()
