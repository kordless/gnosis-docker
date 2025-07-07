"""
Docker Compose management operations
"""

import asyncio
import os
import yaml
import tempfile
from typing import Dict, List, Optional, Any
from pathlib import Path

import docker
from docker.errors import DockerException, APIError, NotFound


class ComposeManager:
    """Handles Docker Compose operations"""
    
    def __init__(self, docker_client):
        self.client = docker_client
        self.compose_projects = {}  # Track active projects
    
    async def parse_compose_file(self, compose_content: str) -> Dict:
        """Parse and validate compose file content"""
        try:
            compose_dict = yaml.safe_load(compose_content)
            
            # Basic validation
            if 'services' not in compose_dict:
                raise ValueError("No services defined in compose file")
            
            return compose_dict
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in compose file: {e}")
    
    async def compose_up(
        self, 
        compose_content: str,
        project_name: str,
        services: Optional[List[str]] = None,
        detach: bool = True,
        build: bool = False
    ) -> Dict:
        """Deploy services from compose file content"""
        try:
            # Parse compose file
            compose_dict = await self.parse_compose_file(compose_content)
            
            deployed_containers = []
            errors = []
            
            # Get services to deploy
            service_names = services or list(compose_dict['services'].keys())
            
            # Create project network if specified
            networks = compose_dict.get('networks', {})
            created_networks = []
            for network_name, network_config in networks.items():
                try:
                    full_network_name = f"{project_name}_{network_name}"
                    self.client.networks.create(
                        name=full_network_name,
                        driver=network_config.get('driver', 'bridge')
                    )
                    created_networks.append(full_network_name)
                except Exception as e:
                    if "already exists" not in str(e):
                        errors.append(f"Failed to create network {network_name}: {e}")
            
            # Deploy each service
            for service_name in service_names:
                if service_name not in compose_dict['services']:
                    errors.append(f"Service {service_name} not found in compose file")
                    continue
                
                service_config = compose_dict['services'][service_name]
                
                try:
                    # Prepare container configuration
                    container_name = f"{project_name}-{service_name}"
                    
                    # Convert compose config to docker run params
                    container_config = {
                        'image': service_config.get('image'),
                        'name': container_name,
                        'detach': detach,
                        'labels': {
                            'com.docker.compose.project': project_name,
                            'com.docker.compose.service': service_name,
                        }
                    }
                    
                    # Add environment variables
                    if 'environment' in service_config:
                        env_dict = {}
                        if isinstance(service_config['environment'], list):
                            for env in service_config['environment']:
                                if '=' in env:
                                    key, value = env.split('=', 1)
                                    env_dict[key] = value
                        else:
                            env_dict = service_config['environment']
                        container_config['environment'] = env_dict
                    
                    # Add ports
                    if 'ports' in service_config:
                        ports = {}
                        for port_mapping in service_config['ports']:
                            if ':' in str(port_mapping):
                                host_port, container_port = str(port_mapping).split(':')
                                ports[container_port] = int(host_port)
                            else:
                                ports[str(port_mapping)] = int(port_mapping)
                        container_config['ports'] = ports
                    
                    # Add volumes (with security checks)
                    if 'volumes' in service_config:
                        volumes = {}
                        for volume in service_config['volumes']:
                            if ':' in volume:
                                host_path, container_path = volume.split(':', 1)
                                # Security: Only allow specific paths
                                if any(host_path.startswith(allowed) for allowed in ['/tmp', '/data', '/app']):
                                    volumes[host_path] = container_path
                                else:
                                    errors.append(f"Volume path not allowed for {service_name}: {host_path}")
                        if volumes:
                            container_config['volumes'] = volumes
                    
                    # Add network
                    if networks:
                        container_config['network'] = created_networks[0] if created_networks else None
                    
                    # Add command
                    if 'command' in service_config:
                        container_config['command'] = service_config['command']
                    
                    # Create and start container
                    container = self.client.containers.run(**container_config)
                    
                    deployed_containers.append({
                        'service': service_name,
                        'container_id': container.id,
                        'container_name': container_name,
                        'status': 'running' if detach else 'exited'
                    })
                    
                except Exception as e:
                    errors.append(f"Failed to deploy {service_name}: {str(e)}")
            
            # Store project info
            self.compose_projects[project_name] = {
                'services': deployed_containers,
                'networks': created_networks,
                'compose': compose_dict
            }
            
            return {
                'project_name': project_name,
                'deployed_services': deployed_containers,
                'networks': created_networks,
                'errors': errors,
                'success': len(errors) == 0
            }
            
        except Exception as e:
            raise DockerException(f"Failed to deploy compose project: {e}")
    
    async def compose_down(
        self,
        project_name: str,
        remove_volumes: bool = False,
        remove_images: bool = False
    ) -> Dict:
        """Stop and remove containers for a compose project"""
        try:
            removed_containers = []
            removed_networks = []
            errors = []
            
            # Find all containers for this project
            containers = self.client.containers.list(
                all=True,
                filters={'label': f'com.docker.compose.project={project_name}'}
            )
            
            # Stop and remove containers
            for container in containers:
                try:
                    if container.status == 'running':
                        container.stop()
                    container.remove(v=remove_volumes)
                    removed_containers.append(container.name)
                except Exception as e:
                    errors.append(f"Failed to remove container {container.name}: {e}")
            
            # Remove networks
            networks = self.client.networks.list(
                filters={'label': f'com.docker.compose.project={project_name}'}
            )
            
            for network in networks:
                try:
                    network.remove()
                    removed_networks.append(network.name)
                except Exception as e:
                    errors.append(f"Failed to remove network {network.name}: {e}")
            
            # Remove from tracking
            if project_name in self.compose_projects:
                del self.compose_projects[project_name]
            
            return {
                'project_name': project_name,
                'removed_containers': removed_containers,
                'removed_networks': removed_networks,
                'errors': errors,
                'success': len(errors) == 0
            }
            
        except Exception as e:
            raise DockerException(f"Failed to remove compose project: {e}")
    
    async def compose_ps(self, project_name: str) -> List[Dict]:
        """List containers for a compose project"""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={'label': f'com.docker.compose.project={project_name}'}
            )
            
            container_info = []
            for container in containers:
                container_info.append({
                    'id': container.id,
                    'name': container.name,
                    'service': container.labels.get('com.docker.compose.service', 'unknown'),
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown'
                })
            
            return container_info
            
        except Exception as e:
            raise DockerException(f"Failed to list compose containers: {e}")
    
    async def compose_logs(
        self,
        project_name: str,
        services: Optional[List[str]] = None,
        tail: int = 100
    ) -> Dict[str, str]:
        """Get logs for compose services"""
        try:
            logs = {}
            
            # Get containers
            containers = self.client.containers.list(
                all=True,
                filters={'label': f'com.docker.compose.project={project_name}'}
            )
            
            for container in containers:
                service_name = container.labels.get('com.docker.compose.service', 'unknown')
                
                # Filter by requested services
                if services and service_name not in services:
                    continue
                
                try:
                    container_logs = container.logs(tail=tail).decode('utf-8')
                    logs[service_name] = container_logs
                except Exception as e:
                    logs[service_name] = f"Error getting logs: {e}"
            
            return logs
            
        except Exception as e:
            raise DockerException(f"Failed to get compose logs: {e}")