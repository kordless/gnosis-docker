"""
Real integration tests against the actual Gnosis Docker service
These tests create and manage real Docker containers
"""

import pytest
import requests
import time
import json
import uuid
from typing import List, Dict


class TestGnosisDockerIntegration:
    """Integration tests for Gnosis Docker service"""
    
    BASE_URL = "http://localhost:5680"
    created_containers: List[str] = []
    
    @classmethod
    def setup_class(cls):
        """Check if service is available"""
        try:
            response = requests.get(f"{cls.BASE_URL}/health")
            assert response.status_code == 200
            health = response.json()
            assert health["status"] == "healthy"
            assert health["checks"]["docker"] == "healthy"
            print("✅ Gnosis Docker service is healthy")
        except Exception as e:
            pytest.skip(f"Gnosis Docker service not available: {e}")
    
    @classmethod 
    def teardown_class(cls):
        """Clean up any containers created during tests"""
        for container_id in cls.created_containers:
            try:
                response = requests.delete(
                    f"{cls.BASE_URL}/api/containers/{container_id}",
                    params={"force": "true"}
                )
                if response.status_code == 200:
                    print(f"✅ Cleaned up container {container_id}")
                else:
                    print(f"⚠️ Failed to clean up {container_id}: {response.text}")
            except Exception as e:
                print(f"⚠️ Error cleaning up {container_id}: {e}")
    
    def track_container(self, container_id: str):
        """Track container for cleanup"""
        self.created_containers.append(container_id)
    
    def test_service_health(self):
        """Test service health endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")
        assert response.status_code == 200
        
        health = response.json()
        assert health["service"] == "gnosis-docker"
        assert health["status"] == "healthy"
        assert "docker" in health["checks"]
    
    def test_list_containers(self):
        """Test listing containers"""
        response = requests.get(f"{self.BASE_URL}/api/containers")
        assert response.status_code == 200
        
        data = response.json()
        assert "containers" in data
        assert "total" in data
        assert isinstance(data["containers"], list)
        assert data["total"] >= 0
    
    def test_create_container_basic(self):
        """Test creating a basic container"""
        payload = {
            "image": "redis:7-alpine",
            "name": "integration-test-create"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/containers/create",
            json=payload
        )
        assert response.status_code == 201
        
        data = response.json()
        assert "container" in data
        assert "message" in data
        assert "created successfully" in data["message"]
        
        container = data["container"]
        assert container["name"] == "integration-test-create"
        assert container["image"] == "redis:7-alpine"
        assert container["status"] == "created"
        assert "id" in container
        
        # Verify container exists before tracking for cleanup
        list_response = requests.get(f"{self.BASE_URL}/api/containers?all=true")
        containers = list_response.json()["containers"]
        container_names = [c["name"] for c in containers]
        assert "integration-test-create" in container_names
        
        # Track for cleanup
        self.track_container(container["id"])
    
    def test_create_container_with_ports(self):
        """Test creating container with port mapping"""
        payload = {
            "image": "redis:7-alpine",
            "name": "integration-test-ports",
            "ports": {"6379": 6382}
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/containers/create",
            json=payload
        )
        assert response.status_code == 201
        
        container = response.json()["container"]
        self.track_container(container["id"])
        
        # Port mapping is configured during creation but shows in network settings
        assert container["name"] == "integration-test-ports"
    
    def test_run_container_detached(self):
        """Test running a container in detached mode"""
        payload = {
            "image": "redis:7-alpine",
            "name": "integration-test-run",
            "detach": True,
            "ports": {"6379": 6383}
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/containers/run",
            json=payload
        )
        assert response.status_code == 201
        
        data = response.json()
        assert "container" in data
        assert "started successfully" in data["message"]
        
        container = data["container"]
        assert container["name"] == "integration-test-run"
        assert container["detach"] is True
        assert "ports" in container
        
        self.track_container(container["id"])
        
        # Wait a moment for container to start
        time.sleep(2)
        
        # Verify container is running
        detail_response = requests.get(
            f"{self.BASE_URL}/api/containers/{container['id']}"
        )
        assert detail_response.status_code == 200
        container_detail = detail_response.json()
        assert container_detail["state"]["Running"] is True
    
    def test_run_container_with_environment(self):
        """Test running container with environment variables"""
        payload = {
            "image": "redis:7-alpine",
            "name": "integration-test-env",
            "detach": True,
            "environment": {
                "REDIS_PASSWORD": "test123",
                "DEBUG": "true"
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/containers/run",
            json=payload
        )
        assert response.status_code == 201
        
        container = response.json()["container"]
        self.track_container(container["id"])
        
        # Verify container was created
        assert container["name"] == "integration-test-env"
    
    def test_run_container_with_auto_remove(self):
        """Test running container with auto-remove"""
        payload = {
            "image": "redis:7-alpine",
            "name": "integration-test-remove",
            "detach": True,
            "remove": True
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/containers/run",
            json=payload
        )
        assert response.status_code == 201
        
        container = response.json()["container"]
        assert container["remove"] is True
        
        # Don't track for cleanup since it auto-removes
        # Note: Container will remove itself when stopped
    
    def test_container_lifecycle(self):
        """Test complete container lifecycle: create -> start -> stop -> remove"""
        # 1. Create container with unique name
        unique_name = f"integration-test-lifecycle-{uuid.uuid4().hex[:8]}"
        create_payload = {
            "image": "redis:7-alpine",
            "name": unique_name
        }
        
        create_response = requests.post(
            f"{self.BASE_URL}/api/containers/create",
            json=create_payload
        )
        assert create_response.status_code == 201
        
        container_id = create_response.json()["container"]["id"]
        
        # 2. Start container
        start_response = requests.post(
            f"{self.BASE_URL}/api/containers/{container_id}/start"
        )
        assert start_response.status_code == 200
        
        # Wait for container to start
        time.sleep(1)
        
        # 3. Verify running
        detail_response = requests.get(
            f"{self.BASE_URL}/api/containers/{container_id}"
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["state"]["Running"] is True
        
        # 4. Stop container
        stop_response = requests.post(
            f"{self.BASE_URL}/api/containers/{container_id}/stop",
            json={}
        )
        assert stop_response.status_code == 200
        
        # 5. Remove container
        remove_response = requests.delete(
            f"{self.BASE_URL}/api/containers/{container_id}"
        )
        assert remove_response.status_code == 200
        
        # 6. Verify removed
        final_detail = requests.get(
            f"{self.BASE_URL}/api/containers/{container_id}"
        )
        assert final_detail.status_code == 404
    
    def test_create_container_validation_error(self):
        """Test container creation with invalid parameters"""
        # Missing image
        response = requests.post(
            f"{self.BASE_URL}/api/containers/create",
            json={}
        )
        assert response.status_code == 400
        assert "Image name required" in response.json()["error"]
        
        # Invalid image name (security test)
        payload = {
            "image": "nginx; rm -rf /",
            "name": "bad-container"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/containers/create",
            json=payload
        )
        assert response.status_code == 500
        assert "validation failed" in response.json()["error"]
    
    def test_run_container_validation_error(self):
        """Test run container with invalid parameters"""
        # Invalid port mapping (privileged port)
        payload = {
            "image": "redis:7-alpine",
            "name": "bad-ports",
            "ports": {"6379": 80}  # Port 80 should be blocked
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/containers/run",
            json=payload
        )
        assert response.status_code == 500
        assert "validation failed" in response.json()["error"]
    
    def test_container_with_nonexistent_image(self):
        """Test creating container with non-existent image"""
        payload = {
            "image": "nonexistent:invalid",
            "name": "test-bad-image"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/containers/create",
            json=payload
        )
        assert response.status_code == 500
        assert "No such image" in response.json()["error"]
    
    def test_get_container_logs(self):
        """Test getting logs from a container"""
        # Create and start a container
        payload = {
            "image": "redis:7-alpine",
            "name": "integration-test-logs",
            "detach": True
        }
        
        run_response = requests.post(
            f"{self.BASE_URL}/api/containers/run",
            json=payload
        )
        assert run_response.status_code == 201
        
        container_id = run_response.json()["container"]["id"]
        self.track_container(container_id)
        
        # Wait for container to generate some logs
        time.sleep(3)
        
        # Get logs
        logs_response = requests.get(
            f"{self.BASE_URL}/api/containers/{container_id}/logs",
            params={"tail": 10}
        )
        assert logs_response.status_code == 200
        
        logs_data = logs_response.json()
        assert "logs" in logs_data
        assert "container_id" in logs_data
        assert logs_data["container_id"] == container_id
    
    def test_get_container_stats(self):
        """Test getting stats from a running container"""
        # Create and start a container
        payload = {
            "image": "redis:7-alpine", 
            "name": "integration-test-stats",
            "detach": True
        }
        
        run_response = requests.post(
            f"{self.BASE_URL}/api/containers/run",
            json=payload
        )
        assert run_response.status_code == 201
        
        container_id = run_response.json()["container"]["id"]
        self.track_container(container_id)
        
        # Wait for container to be fully running
        time.sleep(3)
        
        # Get stats
        stats_response = requests.get(
            f"{self.BASE_URL}/api/containers/{container_id}/stats"
        )
        assert stats_response.status_code == 200
        
        stats_data = stats_response.json()
        assert "stats" in stats_data
        assert "container_id" in stats_data
        
        stats = stats_data["stats"]
        assert "cpu_percent" in stats
        assert "memory_usage" in stats
        assert "memory_percent" in stats


if __name__ == "__main__":
    # Can run individual tests
    import sys
    if len(sys.argv) > 1:
        pytest.main([__file__ + "::" + sys.argv[1], "-v", "-s"])
    else:
        pytest.main([__file__, "-v", "-s"])