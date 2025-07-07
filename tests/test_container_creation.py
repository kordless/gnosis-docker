"""
Tests for container creation functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from core.docker_manager import DockerManager
from docker.errors import DockerException


class TestContainerCreation:
    """Test container creation and running"""
    
    @pytest.fixture
    def docker_manager(self):
        """Create a mock Docker manager"""
        with patch('core.docker_manager.docker') as mock_docker:
            # Mock successful Docker connection
            mock_client = Mock()
            mock_docker.from_env.return_value = mock_client
            mock_client.ping.return_value = True
            
            manager = DockerManager()
            return manager
    
    @pytest.mark.asyncio
    async def test_create_container_success(self, docker_manager):
        """Test successful container creation"""
        # Mock container object
        mock_container = Mock()
        mock_container.id = "container123"
        mock_container.name = "test-container"
        mock_container.status = "created"
        mock_container.attrs = {
            'Created': '2023-01-01T00:00:00Z',
            'NetworkSettings': {'Ports': {}},
            'Mounts': []
        }
        
        # Mock client.containers.create
        docker_manager.client.containers.create = Mock(return_value=mock_container)
        
        result = await docker_manager.create_container(
            image="nginx:latest",
            name="test-container",
            ports={"80": 8080}
        )
        
        assert result is not None
        assert result['id'] == "container123"
        assert result['name'] == "test-container"
        assert result['image'] == "nginx:latest"
        assert result['status'] == "created"
    
    @pytest.mark.asyncio
    async def test_create_container_validation_error(self, docker_manager):
        """Test container creation with validation error"""
        with pytest.raises(DockerException) as exc_info:
            await docker_manager.create_container(
                image="nginx; rm -rf /",  # Invalid image
                name="test-container"
            )
        
        assert "validation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_run_container_success(self, docker_manager):
        """Test successful container running"""
        # Mock container object
        mock_container = Mock()
        mock_container.id = "container456"
        mock_container.name = "running-container"
        mock_container.status = "running"
        mock_container.attrs = {
            'NetworkSettings': {'Ports': {'80/tcp': [{'HostPort': '8080'}]}},
            'Mounts': []
        }
        mock_container.logs.return_value = b"Container started successfully"
        mock_container.reload = Mock()
        
        # Mock client.containers.run
        docker_manager.client.containers.run = Mock(return_value=mock_container)
        
        result = await docker_manager.run_container(
            image="redis:latest",
            name="running-container",
            detach=False,
            ports={"6379": 6379}
        )
        
        assert result is not None
        assert result['id'] == "container456"
        assert result['name'] == "running-container"
        assert result['image'] == "redis:latest"
        assert result['detach'] is False
        assert 'logs' in result
    
    @pytest.mark.asyncio
    async def test_run_container_detached(self, docker_manager):
        """Test running detached container"""
        # Mock container object
        mock_container = Mock()
        mock_container.id = "container789"
        mock_container.name = "detached-container"
        mock_container.status = "running"
        mock_container.attrs = {
            'NetworkSettings': {'Ports': {}},
            'Mounts': []
        }
        mock_container.reload = Mock()
        
        # Mock client.containers.run
        docker_manager.client.containers.run = Mock(return_value=mock_container)
        
        result = await docker_manager.run_container(
            image="mysql:8.0",
            name="detached-container",
            detach=True,
            environment={"MYSQL_ROOT_PASSWORD": "secret"}
        )
        
        assert result is not None
        assert result['id'] == "container789"
        assert result['detach'] is True
        assert 'logs' not in result  # No logs for detached containers
    
    @pytest.mark.asyncio
    async def test_create_container_with_volumes(self, docker_manager):
        """Test container creation with volume mapping"""
        # Mock container object
        mock_container = Mock()
        mock_container.id = "container_vol"
        mock_container.name = "volume-container"
        mock_container.status = "created"
        mock_container.attrs = {
            'Created': '2023-01-01T00:00:00Z',
            'NetworkSettings': {'Ports': {}},
            'Mounts': [{'Source': '/tmp/data', 'Destination': '/app/data'}]
        }
        
        # Mock client.containers.create
        docker_manager.client.containers.create = Mock(return_value=mock_container)
        
        result = await docker_manager.create_container(
            image="ubuntu:20.04",
            name="volume-container",
            volumes={"/tmp/data": "/app/data"},
            command="sleep 3600"
        )
        
        assert result is not None
        assert len(result['mounts']) > 0
        
        # Verify the create call was made with correct parameters
        call_args = docker_manager.client.containers.create.call_args
        assert 'volumes' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_run_container_with_environment(self, docker_manager):
        """Test running container with environment variables"""
        # Mock container object
        mock_container = Mock()
        mock_container.id = "container_env"
        mock_container.name = "env-container"
        mock_container.status = "running"
        mock_container.attrs = {
            'NetworkSettings': {'Ports': {}},
            'Mounts': []
        }
        mock_container.reload = Mock()
        
        # Mock client.containers.run
        docker_manager.client.containers.run = Mock(return_value=mock_container)
        
        result = await docker_manager.run_container(
            image="node:16",
            name="env-container",
            environment={
                "NODE_ENV": "production",
                "PORT": "3000"
            },
            command="npm start"
        )
        
        assert result is not None
        
        # Verify the run call was made with environment
        call_args = docker_manager.client.containers.run.call_args
        assert 'environment' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_container_creation_docker_error(self, docker_manager):
        """Test handling of Docker API errors"""
        # Mock Docker API error
        docker_manager.client.containers.create = Mock(
            side_effect=Exception("Docker daemon not responding")
        )
        
        with pytest.raises(DockerException) as exc_info:
            await docker_manager.create_container(
                image="nginx:latest",
                name="error-container"
            )
        
        assert "Failed to create container" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_run_container_with_network(self, docker_manager):
        """Test running container with custom network"""
        # Mock container object
        mock_container = Mock()
        mock_container.id = "container_net"
        mock_container.name = "network-container"
        mock_container.status = "running"
        mock_container.attrs = {
            'NetworkSettings': {'Ports': {}},
            'Mounts': []
        }
        mock_container.reload = Mock()
        
        # Mock client.containers.run
        docker_manager.client.containers.run = Mock(return_value=mock_container)
        
        result = await docker_manager.run_container(
            image="postgres:13",
            name="network-container",
            network="custom-network",
            environment={"POSTGRES_PASSWORD": "secret"}
        )
        
        assert result is not None
        
        # Verify the run call was made with network
        call_args = docker_manager.client.containers.run.call_args
        assert 'network' in call_args[1]
        assert call_args[1]['network'] == "custom-network"