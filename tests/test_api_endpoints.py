"""
Tests for new API endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock


class TestContainerAPIEndpoints:
    """Test container creation API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        with patch('core.docker_manager.docker') as mock_docker:
            # Mock successful Docker connection
            mock_client = Mock()
            mock_docker.from_env.return_value = mock_client
            mock_client.ping.return_value = True
            
            # Import app after mocking
            from app import app
            app.config['TESTING'] = True
            with app.test_client() as client:
                yield client
    
    @pytest.fixture
    def mock_docker_manager(self):
        """Mock the Docker manager"""
        with patch('app.docker_manager') as mock_manager:
            yield mock_manager
    
    def test_create_container_success(self, client, mock_docker_manager):
        """Test successful container creation via API"""
        # Mock successful creation
        mock_docker_manager.create_container = AsyncMock(return_value={
            'id': 'container123',
            'name': 'test-container',
            'image': 'nginx:latest',
            'status': 'created'
        })
        
        response = client.post('/api/containers/create', 
                             json={
                                 'image': 'nginx:latest',
                                 'name': 'test-container',
                                 'ports': {'80': 8080}
                             })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'container' in data
        assert data['container']['id'] == 'container123'
    
    def test_create_container_missing_image(self, client, mock_docker_manager):
        """Test container creation without image parameter"""
        response = client.post('/api/containers/create', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Image name required' in data['error']
    
    def test_create_container_validation_error(self, client, mock_docker_manager):
        """Test container creation with validation error"""
        from docker.errors import DockerException
        
        # Mock validation error
        mock_docker_manager.create_container = AsyncMock(
            side_effect=DockerException("Container validation failed: Invalid image")
        )
        
        response = client.post('/api/containers/create',
                             json={'image': 'invalid; rm -rf /'})
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'validation failed' in data['error']
    
    def test_run_container_success(self, client, mock_docker_manager):
        """Test successful container running via API"""
        # Mock successful run
        mock_docker_manager.run_container = AsyncMock(return_value={
            'id': 'container456',
            'name': 'running-container',
            'image': 'redis:latest',
            'status': 'running',
            'detach': True
        })
        
        response = client.post('/api/containers/run',
                             json={
                                 'image': 'redis:latest',
                                 'name': 'running-container',
                                 'detach': True,
                                 'ports': {'6379': 6379}
                             })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'container' in data
        assert data['container']['id'] == 'container456'
        assert 'started successfully' in data['message']
    
    def test_run_container_non_detached(self, client, mock_docker_manager):
        """Test running non-detached container"""
        # Mock successful run with logs
        mock_docker_manager.run_container = AsyncMock(return_value={
            'id': 'container789',
            'name': 'interactive-container',
            'image': 'ubuntu:20.04',
            'status': 'exited',
            'detach': False,
            'logs': 'Hello from container'
        })
        
        response = client.post('/api/containers/run',
                             json={
                                 'image': 'ubuntu:20.04',
                                 'name': 'interactive-container',
                                 'detach': False,
                                 'command': 'echo "Hello from container"'
                             })
        
        assert response.status_code == 200  # 200 for non-detached
        data = json.loads(response.data)
        assert 'executed successfully' in data['message']
    
    def test_run_container_with_environment(self, client, mock_docker_manager):
        """Test running container with environment variables"""
        mock_docker_manager.run_container = AsyncMock(return_value={
            'id': 'container_env',
            'name': 'env-container',
            'image': 'node:16',
            'status': 'running'
        })
        
        response = client.post('/api/containers/run',
                             json={
                                 'image': 'node:16',
                                 'name': 'env-container',
                                 'environment': {
                                     'NODE_ENV': 'production',
                                     'PORT': '3000'
                                 },
                                 'command': 'npm start'
                             })
        
        assert response.status_code == 201
        
        # Verify environment was passed to docker_manager
        call_args = mock_docker_manager.run_container.call_args
        assert call_args[1]['environment'] == {
            'NODE_ENV': 'production',
            'PORT': '3000'
        }
    
    def test_run_container_with_volumes(self, client, mock_docker_manager):
        """Test running container with volumes"""
        mock_docker_manager.run_container = AsyncMock(return_value={
            'id': 'container_vol',
            'name': 'volume-container',
            'image': 'mysql:8.0',
            'status': 'running'
        })
        
        response = client.post('/api/containers/run',
                             json={
                                 'image': 'mysql:8.0',
                                 'name': 'volume-container',
                                 'volumes': {
                                     '/tmp/mysql': '/var/lib/mysql'
                                 },
                                 'environment': {
                                     'MYSQL_ROOT_PASSWORD': 'secret'
                                 }
                             })
        
        assert response.status_code == 201
        
        # Verify volumes were passed
        call_args = mock_docker_manager.run_container.call_args
        assert '/tmp/mysql' in call_args[1]['volumes']
    
    def test_create_container_with_resource_limits(self, client, mock_docker_manager):
        """Test container creation with resource limits"""
        mock_docker_manager.create_container = AsyncMock(return_value={
            'id': 'container_limits',
            'name': 'limited-container',
            'image': 'nginx:latest',
            'status': 'created'
        })
        
        response = client.post('/api/containers/create',
                             json={
                                 'image': 'nginx:latest',
                                 'name': 'limited-container',
                                 'mem_limit': '512m',
                                 'cpu_count': 1.0
                             })
        
        assert response.status_code == 201
        
        # Verify resource limits were passed
        call_args = mock_docker_manager.create_container.call_args
        assert call_args[1]['mem_limit'] == '512m'
        assert call_args[1]['cpu_count'] == 1.0
    
    def test_run_container_docker_error(self, client, mock_docker_manager):
        """Test handling Docker errors in run endpoint"""
        from docker.errors import DockerException
        
        mock_docker_manager.run_container = AsyncMock(
            side_effect=DockerException("Docker daemon not responding")
        )
        
        response = client.post('/api/containers/run',
                             json={'image': 'nginx:latest'})
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Failed to run container' in data['error']
    
    def test_create_container_invalid_json(self, client, mock_docker_manager):
        """Test container creation with invalid JSON"""
        response = client.post('/api/containers/create',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_run_container_with_network(self, client, mock_docker_manager):
        """Test running container with custom network"""
        mock_docker_manager.run_container = AsyncMock(return_value={
            'id': 'container_net',
            'name': 'network-container',
            'image': 'postgres:13',
            'status': 'running'
        })
        
        response = client.post('/api/containers/run',
                             json={
                                 'image': 'postgres:13',
                                 'name': 'network-container',
                                 'network': 'custom-network',
                                 'environment': {
                                     'POSTGRES_PASSWORD': 'secret'
                                 }
                             })
        
        assert response.status_code == 201
        
        # Verify network was passed
        call_args = mock_docker_manager.run_container.call_args
        assert call_args[1]['network'] == 'custom-network'