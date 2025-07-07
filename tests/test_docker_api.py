"""
Test Docker API endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_docker():
    """Mock Docker client"""
    with patch('docker.from_env') as mock:
        docker_client = Mock()
        docker_client.ping.return_value = True
        mock.return_value = docker_client
        yield docker_client

def test_health_check(client, mock_docker):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] in ['healthy', 'degraded']
    assert 'timestamp' in data
    assert data['service'] == 'gnosis-docker'

def test_list_containers(client, mock_docker):
    """Test list containers endpoint"""
    # Mock container data
    mock_container = Mock()
    mock_container.short_id = 'abc123'
    mock_container.name = 'test-container'
    mock_container.status = 'running'
    mock_container.image.tags = ['test:latest']
    mock_container.attrs = {
        'State': {'Running': True},
        'Created': '2024-01-01T00:00:00Z'
    }
    mock_container.labels = {}
    
    mock_docker.containers.list.return_value = [mock_container]
    
    response = client.get('/api/containers')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'containers' in data
    assert len(data['containers']) == 1
    assert data['containers'][0]['name'] == 'test-container'

def test_start_container(client, mock_docker):
    """Test start container endpoint"""
    mock_container = Mock()
    mock_docker.containers.get.return_value = mock_container
    
    response = client.post('/api/containers/abc123/start')
    assert response.status_code == 200
    mock_container.start.assert_called_once()

def test_stop_container(client, mock_docker):
    """Test stop container endpoint"""
    mock_container = Mock()
    mock_docker.containers.get.return_value = mock_container
    
    response = client.post('/api/containers/abc123/stop', 
                          json={'timeout': 10})
    assert response.status_code == 200
    mock_container.stop.assert_called_once_with(10)

def test_container_not_found(client, mock_docker):
    """Test container not found"""
    mock_docker.containers.get.side_effect = docker.errors.NotFound("Not found")
    
    response = client.get('/api/containers/notfound')
    assert response.status_code == 404

def test_list_images(client, mock_docker):
    """Test list images endpoint"""
    mock_image = Mock()
    mock_image.short_id = 'sha256:abc123'
    mock_image.tags = ['test:latest']
    mock_image.attrs = {
        'Created': '2024-01-01T00:00:00Z',
        'Size': 1000000,
        'Architecture': 'amd64',
        'Os': 'linux'
    }
    mock_image.labels = {}
    
    mock_docker.images.list.return_value = [mock_image]
    
    response = client.get('/api/images')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'images' in data
    assert len(data['images']) == 1

def test_pull_image(client, mock_docker):
    """Test pull image endpoint"""
    mock_image = Mock()
    mock_image.id = 'sha256:abc123'
    mock_image.tags = ['test:latest']
    mock_image.attrs = {'Size': 1000000}
    
    mock_docker.images.pull.return_value = mock_image
    
    response = client.post('/api/images/pull', 
                          json={'image': 'test', 'tag': 'latest'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'image' in data

def test_build_project(client, mock_docker):
    """Test build project endpoint"""
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        
        mock_image = Mock()
        mock_image.id = 'sha256:newimage'
        mock_image.tags = ['myproject:latest']
        
        mock_docker.images.build.return_value = (mock_image, [{'stream': 'Building...'}])
        
        response = client.post('/api/build',
                              json={'path': '/test/path', 'tag': 'myproject:latest'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Build completed successfully'

def test_local_only_restriction(client):
    """Test local-only access restriction"""
    # Simulate non-local request
    with app.test_client() as client:
        response = client.get('/api/containers', 
                             environ_base={'REMOTE_ADDR': '192.168.1.100'})
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'Local access only' in data['error']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
