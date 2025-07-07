"""
Container creation validation and security checks
"""

import re
import os
from typing import Dict, List, Optional, Any
from .config import Config


class ContainerValidationError(Exception):
    """Raised when container parameters fail validation"""
    pass


class ContainerValidator:
    """Validates container creation parameters for security"""
    
    @staticmethod
    def validate_image_name(image: str) -> None:
        """Validate image name for security"""
        if not image or not isinstance(image, str):
            raise ContainerValidationError("Image name must be a non-empty string")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'[;&|`$]',  # Shell injection characters
            r'\.\.',     # Path traversal
            r'^https?://',  # URL schemes (should use registry format)
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, image):
                raise ContainerValidationError(f"Image name contains dangerous pattern: {pattern}")
        
        # Check against allowlist/blocklist
        if Config.ALLOWED_IMAGES:
            if not any(allowed in image for allowed in Config.ALLOWED_IMAGES):
                raise ContainerValidationError(f"Image not in allowed list: {image}")
        
        if Config.BLOCKED_IMAGES:
            if any(blocked in image for blocked in Config.BLOCKED_IMAGES):
                raise ContainerValidationError(f"Image is blocked: {image}")
    
    @staticmethod
    def validate_container_name(name: Optional[str]) -> None:
        """Validate container name"""
        if name is None:
            return
        
        if not isinstance(name, str):
            raise ContainerValidationError("Container name must be a string")
        
        # Docker container name validation
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', name):
            raise ContainerValidationError(
                "Container name must start with alphanumeric and contain only letters, digits, underscore, period, or dash"
            )
        
        if len(name) > 253:
            raise ContainerValidationError("Container name must be 253 characters or less")
    
    @staticmethod
    def validate_command(command: Optional[str]) -> None:
        """Validate command for dangerous patterns"""
        if command is None:
            return
        
        if not isinstance(command, str):
            raise ContainerValidationError("Command must be a string")
        
        # Check for dangerous command patterns
        dangerous_patterns = [
            r'rm\s+-rf\s*/',  # Dangerous rm commands
            r'dd\s+if=',      # Disk dumping
            r'curl.*\|\s*(sh|bash)', # Download and execute
            r'wget.*\|\s*(sh|bash)', # Download and execute
            r'nc\s+-l',       # Netcat listener
            r'python.*-c.*exec', # Python exec
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                raise ContainerValidationError(f"Command contains dangerous pattern: {pattern}")
    
    @staticmethod
    def validate_environment(environment: Optional[Dict[str, str]]) -> None:
        """Validate environment variables"""
        if environment is None:
            return
        
        if not isinstance(environment, dict):
            raise ContainerValidationError("Environment must be a dictionary")
        
        # Check for dangerous environment variables
        dangerous_vars = ['LD_PRELOAD', 'PATH', 'PYTHONPATH', 'DYLD_LIBRARY_PATH']
        
        for key, value in environment.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ContainerValidationError("Environment keys and values must be strings")
            
            if key in dangerous_vars:
                raise ContainerValidationError(f"Environment variable not allowed: {key}")
            
            # Check for injection patterns in values
            if re.search(r'[;&|`$()]', value):
                raise ContainerValidationError(f"Environment value contains dangerous characters: {key}")
    
    @staticmethod
    def validate_ports(ports: Optional[Dict[str, int]]) -> None:
        """Validate port mappings"""
        if ports is None:
            return
        
        if not isinstance(ports, dict):
            raise ContainerValidationError("Ports must be a dictionary")
        
        for container_port, host_port in ports.items():
            # Validate container port
            try:
                c_port = int(container_port)
                if not (1 <= c_port <= 65535):
                    raise ContainerValidationError(f"Invalid container port: {container_port}")
            except ValueError:
                raise ContainerValidationError(f"Container port must be numeric: {container_port}")
            
            # Validate host port
            if not isinstance(host_port, int) or not (1 <= host_port <= 65535):
                raise ContainerValidationError(f"Invalid host port: {host_port}")
            
            # Block privileged ports on host
            if host_port < 1024:
                raise ContainerValidationError(f"Cannot bind to privileged port: {host_port}")
    
    @staticmethod
    def validate_volumes(volumes: Optional[Dict[str, str]]) -> None:
        """Validate volume mappings"""
        if volumes is None:
            return
        
        if not isinstance(volumes, dict):
            raise ContainerValidationError("Volumes must be a dictionary")
        
        for host_path, container_path in volumes.items():
            if not isinstance(host_path, str) or not isinstance(container_path, str):
                raise ContainerValidationError("Volume paths must be strings")
            
            # Check for path traversal
            if '..' in host_path or '..' in container_path:
                raise ContainerValidationError("Volume paths cannot contain path traversal")
            
            # Validate host path against allowlist
            if Config.ALLOWED_VOLUME_PATHS:
                allowed = any(host_path.startswith(allowed_path) 
                            for allowed_path in Config.ALLOWED_VOLUME_PATHS)
                if not allowed:
                    raise ContainerValidationError(f"Host path not allowed: {host_path}")
            
            # Block dangerous container paths
            dangerous_paths = ['/etc', '/var/run/docker.sock', '/proc', '/sys']
            if any(container_path.startswith(dangerous) for dangerous in dangerous_paths):
                raise ContainerValidationError(f"Dangerous container path: {container_path}")
    
    @staticmethod
    def validate_resource_limits(**kwargs) -> None:
        """Validate resource limits"""
        # Memory limit
        if 'mem_limit' in kwargs:
            mem_limit = kwargs['mem_limit']
            if mem_limit and not isinstance(mem_limit, (str, int)):
                raise ContainerValidationError("Memory limit must be string or integer")
        
        # CPU limit
        if 'cpu_count' in kwargs:
            cpu_count = kwargs['cpu_count']
            if cpu_count is not None:
                try:
                    cpu_val = float(cpu_count)
                    if cpu_val > Config.MAX_CPUS:
                        raise ContainerValidationError(f"CPU count exceeds limit: {cpu_val} > {Config.MAX_CPUS}")
                except (ValueError, TypeError):
                    raise ContainerValidationError("CPU count must be numeric")
        
        # Block privileged containers
        if Config.BLOCK_PRIVILEGED and kwargs.get('privileged'):
            raise ContainerValidationError("Privileged containers are not allowed")
    
    @classmethod
    def validate_container_params(
        cls,
        image: str,
        name: Optional[str] = None,
        command: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, int]] = None,
        volumes: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> None:
        """Validate all container creation parameters"""
        cls.validate_image_name(image)
        cls.validate_container_name(name)
        cls.validate_command(command)
        cls.validate_environment(environment)
        cls.validate_ports(ports)
        cls.validate_volumes(volumes)
        cls.validate_resource_limits(**kwargs)