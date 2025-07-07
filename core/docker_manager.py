"""
Docker management operations
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

import docker
from docker.errors import DockerException, APIError, NotFound
from docker.models.containers import Container
from docker.models.images import Image
from .validation import ContainerValidator, ContainerValidationError

class DockerManager:
    """Handles all Docker operations"""
    
    def __init__(self):
        try:
            # Try default connection first (will use DOCKER_HOST if set)
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            # Don't print to stdout in MCP tools - use logging instead
            # print(f"Successfully connected to Docker daemon")

        except DockerException as e:
            # If that fails and socket exists, try explicit socket connection
            if os.path.exists('/var/run/docker.sock'):
                try:
                    self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')
                    self.client.ping()
                    # Don't print to stdout in MCP tools - use logging instead
                    # print(f"Connected to Docker via Unix socket")

                except Exception as socket_error:
                    raise RuntimeError(f"Failed to connect to Docker: {e} | Socket error: {socket_error}")
            else:
                raise RuntimeError(f"Failed to connect to Docker: {e}")


    
    async def list_containers(self, all: bool = False, filters: Dict = None) -> List[Container]:
        """List containers"""
        try:
            loop = asyncio.get_event_loop()
            containers = await loop.run_in_executor(
                None, 
                lambda: self.client.containers.list(all=all, filters=filters)
            )
            return containers
        except Exception as e:
            raise DockerException(f"Failed to list containers: {e}")
    
    async def get_container(self, container_id: str) -> Optional[Container]:
        """Get a specific container"""
        try:
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                self.client.containers.get,
                container_id
            )
            return container
        except NotFound:
            return None
        except Exception as e:
            raise DockerException(f"Failed to get container: {e}")
    
    async def start_container(self, container_id: str) -> bool:
        """Start a container"""
        try:
            container = await self.get_container(container_id)
            if not container:
                return False
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, container.start)
            return True
        except Exception as e:
            raise DockerException(f"Failed to start container: {e}")
    
    async def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """Stop a container"""
        try:
            container = await self.get_container(container_id)
            if not container:
                return False
            
            loop = asyncio.get_event_loop()
            # Use a lambda to properly pass timeout as keyword argument
            await loop.run_in_executor(None, lambda: container.stop(timeout=timeout))
            return True
        except Exception as e:
            raise DockerException(f"Failed to stop container: {e}")

    
    async def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """Restart a container"""
        try:
            container = await self.get_container(container_id)
            if not container:
                return False
            
            loop = asyncio.get_event_loop()
            # Use a lambda to properly pass timeout as keyword argument
            await loop.run_in_executor(None, lambda: container.restart(timeout=timeout))
            return True
        except Exception as e:
            raise DockerException(f"Failed to restart container: {e}")

    
    async def remove_container(self, container_id: str, force: bool = False, v: bool = False) -> bool:
        """Remove a container"""
        try:
            container = await self.get_container(container_id)
            if not container:
                return False
            
            loop = asyncio.get_event_loop()
            # Use a lambda to properly pass arguments as keyword arguments
            await loop.run_in_executor(None, lambda: container.remove(force=force, v=v))
            return True
        except Exception as e:
            raise DockerException(f"Failed to remove container: {e}")

    
    async def get_container_logs(
        self, 
        container_id: str, 
        tail: int = 100,
        since: str = None,
        until: str = None,
        timestamps: bool = False
    ) -> Optional[str]:
        """Get container logs"""
        try:
            container = await self.get_container(container_id)
            if not container:
                return None
            
            loop = asyncio.get_event_loop()
            logs = await loop.run_in_executor(
                None,
                lambda: container.logs(
                    tail=tail,
                    since=since,
                    until=until,
                    timestamps=timestamps
                ).decode('utf-8')
            )
            return logs
        except Exception as e:
            raise DockerException(f"Failed to get logs: {e}")
    
    async def get_container_stats(self, container_id: str) -> Optional[Dict]:
        """Get container stats"""
        try:
            container = await self.get_container(container_id)
            if not container:
                return None
            
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(
                None,
                lambda: container.stats(stream=False)
            )
            
            # Process stats
            if stats:
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0
                
                memory_usage = stats['memory_stats']['usage']
                memory_limit = stats['memory_stats']['limit']
                memory_percent = (memory_usage / memory_limit) * 100.0
                
                return {
                    'cpu_percent': round(cpu_percent, 2),
                    'memory_usage': memory_usage,
                    'memory_limit': memory_limit,
                    'memory_percent': round(memory_percent, 2),
                    'network': stats.get('networks', {}),
                    'block_io': stats.get('blkio_stats', {})
                }
            
            return None
        except Exception as e:
            raise DockerException(f"Failed to get stats: {e}")
    
    async def list_images(self) -> List[Image]:
        """List all images"""
        try:
            loop = asyncio.get_event_loop()
            images = await loop.run_in_executor(
                None,
                self.client.images.list
            )
            return images
        except Exception as e:
            raise DockerException(f"Failed to list images: {e}")
    
    async def pull_image(self, image_name: str, tag: str = 'latest') -> Dict:
        """Pull an image"""
        try:
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(
                None,
                self.client.images.pull,
                image_name,
                tag
            )
            
            return {
                'id': image.id,
                'tags': image.tags,
                'size': image.attrs.get('Size', 0)
            }
        except Exception as e:
            raise DockerException(f"Failed to pull image: {e}")
    
    async def remove_image(self, image_id: str, force: bool = False) -> bool:
        """Remove an image"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.client.images.remove,
                image_id,
                force
            )
            return True
        except Exception as e:
            raise DockerException(f"Failed to remove image: {e}")
    
    async def build_image(self, path: str, tag: str, dockerfile: str = 'Dockerfile') -> Dict:
        """Build an image from a Dockerfile"""
        try:
            # Validate path
            if not path or not isinstance(path, str):
                raise ValueError(f"Invalid path provided: {path}")
            
            # Log the build attempt
            print(f"Building image {tag} from path: {path}")
            
            loop = asyncio.get_event_loop()
            
            # Build the image - returns (image, build_logs_generator)
            result = await loop.run_in_executor(
                None,
                lambda: self.client.images.build(
                    path=path,
                    tag=tag,
                    dockerfile=dockerfile,
                    rm=True,
                    forcerm=True
                )
            )

            
            # Unpack the result
            image, logs_generator = result
            
            # Collect build logs
            build_logs = []
            for log_entry in logs_generator:
                if isinstance(log_entry, dict) and 'stream' in log_entry:
                    build_logs.append(log_entry['stream'].strip())
                elif isinstance(log_entry, str):
                    build_logs.append(log_entry.strip())
            
            return {
                'id': image.id,
                'tags': image.tags,
                'logs': build_logs,
                'tag': tag
            }
        except Exception as e:
            raise DockerException(f"Failed to build image: {e}")
    
    async def create_container(
        self, 
        image: str, 
        name: Optional[str] = None,
        command: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, int]] = None,
        volumes: Optional[Dict[str, str]] = None,
        network: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict]:
        """Create a new container"""
        try:
            # Validate all parameters for security
            ContainerValidator.validate_container_params(
                image=image,
                name=name,
                command=command,
                environment=environment,
                ports=ports,
                volumes=volumes,
                **kwargs
            )
            
            # Prepare container configuration
            container_config = {
                'image': image,
                'detach': True,
                **kwargs
            }
            
            # Add optional parameters
            if name:
                container_config['name'] = name
            if command:
                container_config['command'] = command
            if environment:
                container_config['environment'] = environment
            if network:
                container_config['network'] = network
            
            # Handle port mapping
            if ports:
                port_bindings = {}
                for container_port, host_port in ports.items():
                    container_port_str = f"{container_port}/tcp"
                    port_bindings[container_port_str] = host_port
                
                container_config['ports'] = port_bindings

            
            # Handle volume mapping
            if volumes:
                volume_bindings = {}
                for host_path, container_path in volumes.items():
                    volume_bindings[host_path] = {'bind': container_path, 'mode': 'rw'}
                container_config['volumes'] = volume_bindings
            
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.create(**container_config)
            )
            
            return {
                'id': container.id,
                'name': container.name,
                'image': image,
                'status': container.status,
                'created': container.attrs.get('Created', ''),
                'ports': container.attrs.get('NetworkSettings', {}).get('Ports', {}),
                'mounts': container.attrs.get('Mounts', [])
            }
            
        except ContainerValidationError as e:
            raise DockerException(f"Container validation failed: {e}")
        except Exception as e:
            raise DockerException(f"Failed to create container: {e}")
    
    async def run_container(
        self,
        image: str,
        name: Optional[str] = None,
        command: Optional[str] = None,
        detach: bool = True,
        remove: bool = False,
        environment: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, int]] = None,
        volumes: Optional[Dict[str, str]] = None,
        network: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """Create and start a new container"""
        try:
            # Validate all parameters for security
            ContainerValidator.validate_container_params(
                image=image,
                name=name,
                command=command,
                environment=environment,
                ports=ports,
                volumes=volumes,
                **kwargs
            )
            
            # Prepare container configuration
            container_config = {
                'image': image,
                'detach': detach,
                'remove': remove,
                **kwargs
            }
            
            # Add optional parameters
            if name:
                container_config['name'] = name
            if command:
                container_config['command'] = command
            if environment:
                container_config['environment'] = environment
            if network:
                container_config['network'] = network
            
            # Handle port mapping
            if ports:
                port_bindings = {}
                for container_port, host_port in ports.items():
                    container_port_str = f"{container_port}/tcp"
                    port_bindings[container_port_str] = host_port
                
                container_config['ports'] = port_bindings

            
            # Handle volume mapping
            if volumes:
                volume_bindings = {}
                for host_path, container_path in volumes.items():
                    volume_bindings[host_path] = {'bind': container_path, 'mode': 'rw'}
                container_config['volumes'] = volume_bindings
            
            loop = asyncio.get_event_loop()
            container = await loop.run_in_executor(
                None,
                lambda: self.client.containers.run(**container_config)
            )
            
            # Prepare response
            result = {
                'id': container.id,
                'name': container.name,
                'image': image,
                'status': container.status,
                'detach': detach,
                'remove': remove
            }
            
            # If not detached, get initial logs
            if not detach:
                try:
                    logs = await loop.run_in_executor(
                        None,
                        lambda: container.logs().decode('utf-8')
                    )
                    result['logs'] = logs
                except Exception:
                    result['logs'] = "Could not retrieve logs"
            
            # Get port mappings
            container.reload()
            result['ports'] = container.attrs.get('NetworkSettings', {}).get('Ports', {})
            result['mounts'] = container.attrs.get('Mounts', [])
            
            return result
            
        except ContainerValidationError as e:
            raise DockerException(f"Container validation failed: {e}")
        except Exception as e:
            raise DockerException(f"Failed to run container: {e}")

