"""
Test script to verify Gnosis Docker API
"""

import requests
import json
import time

BASE_URL = "http://localhost:5680"

def test_health():
    """Test health endpoint"""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_list_containers():
    """Test listing containers"""
    print("\nTesting list containers...")
    response = requests.get(f"{BASE_URL}/api/containers?all=true")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['total']} containers:")
        for container in data['containers'][:3]:  # Show first 3
            print(f"  - {container['name']} ({container['image']}) - {container['status']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return response.status_code == 200

def test_list_images():
    """Test listing images"""
    print("\nTesting list images...")
    response = requests.get(f"{BASE_URL}/api/images")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['total']} images:")
        for image in data['images'][:3]:  # Show first 3
            tags = image['tags'] if image['tags'] else ['<none>']
            print(f"  - {tags[0]} ({image['id']})")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    return response.status_code == 200

def test_build_project():
    """Test building a project"""
    print("\nTesting project build...")
    
    # Try to build gnosis-docker itself
    payload = {
        "project": "gnosis-docker",
        "tag": "gnosis-docker:test"
    }
    
    print(f"Building project: {payload['project']}")
    response = requests.post(f"{BASE_URL}/api/build", json=payload)
    
    if response.status_code == 202:  # 202 Accepted for async build
        data = response.json()
        print(f"Build started: {data['message']}")
        print(f"Build ID: {data['build_id']}")
        print(f"Status endpoint: {data.get('status_endpoint', 'N/A')}")
        
        # Poll for build completion (optional)
        if 'build_id' in data:
            print("\nChecking build status...")
            for i in range(5):  # Check 5 times
                time.sleep(2)  # Wait 2 seconds between checks
                status_response = requests.get(f"{BASE_URL}/api/build/{data['build_id']}/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"  Status: {status_data.get('status', 'unknown')}")
                    if status_data.get('status') == 'completed':
                        print(f"  Build completed successfully!")
                        break
                    elif status_data.get('status') == 'failed':
                        print(f"  Build failed: {status_data.get('error', 'Unknown error')}")
                        break
    elif response.status_code == 200:  # Legacy synchronous response
        data = response.json()
        print(f"Build successful: {data['message']}")
        print(f"Image: {data.get('image', 'N/A')}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    return response.status_code in [200, 202]


def test_container_logs():
    """Test getting container logs"""
    print("\nTesting container logs...")
    
    # First, get the gnosis-docker container ID
    response = requests.get(f"{BASE_URL}/api/containers")
    if response.status_code == 200:
        containers = response.json()['containers']
        gnosis_container = next((c for c in containers if 'gnosis-docker' in c['name']), None)
        
        if gnosis_container:
            container_id = gnosis_container['id']
            print(f"Getting logs for container: {gnosis_container['name']}")
            
            # Get logs
            response = requests.get(f"{BASE_URL}/api/containers/{container_id}/logs?tail=10")
            if response.status_code == 200:
                logs = response.json()['logs']
                print("Last 10 log lines:")
                print(logs)
            else:
                print(f"Error getting logs: {response.status_code}")
        else:
            print("Gnosis Docker container not found")
    
    return True

def main():
    """Run all tests"""
    print("=== Gnosis Docker API Test Suite ===\n")
    
    # Wait a moment for service to be ready
    time.sleep(2)
    
    tests = [
        test_health,
        test_list_containers,
        test_list_images,
        test_build_project,
        test_container_logs
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✓ {test.__name__} passed")
            else:
                print(f"✗ {test.__name__} failed")
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
    
    print(f"\n=== Test Results: {passed}/{len(tests)} passed ===")

if __name__ == "__main__":
    main()
