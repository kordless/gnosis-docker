#!/usr/bin/env python3
"""Gnosis Docker MCP Tool - Complete Docker management through Claude Code"""

import sys
import os
import logging
import requests
import json
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

__version__ = "2.1.0"
__updated__ = "2025-07-07"

# Import MCP server library
try:
    from mcp.server.fastmcp import FastMCP
    # Initialize the MCP server
    mcp = FastMCP("Gnosis Docker Management")
except ImportError:
    print("Error: MCP library not installed. Please run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Configuration
DOCKER_API_URL = os.getenv("GNOSIS_DOCKER_URL", "http://localhost:5680")
DEFAULT_TIMEOUT = 30

class DockerAPIClient:
    """Client for Gnosis Docker API"""
    
    def __init__(self, base_url: str = DOCKER_API_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the API"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("POST", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        return self._request("DELETE", endpoint, **kwargs)

# Initialize API client
api_client = DockerAPIClient()

@mcp.tool()
async def docker_ps(
    all: bool = False,
    filter_status: Optional[str] = None,
    filter_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    List Docker containers.
    
    Args:
        all: Show all containers (default: False, show only running)
        filter_status: Filter by status (running, exited, paused, etc.)
        filter_name: Filter by container name pattern
        
    Returns:
        Dictionary with container list and metadata
    """
    params = {"all": str(all).lower()}
    if filter_status:
        params["status"] = filter_status
    
    result = api_client.get("/api/containers", params=params)
    
    if "error" in result:
        return result
    
    # Apply name filter if specified
    containers = result.get("containers", [])
    if filter_name:
        containers = [c for c in containers if filter_name.lower() in c["name"].lower()]
        result["containers"] = containers
        result["total"] = len(containers)
    
    # Add summary
    result["summary"] = {
        "total": len(containers),
        "running": len([c for c in containers if c["status"] == "running"]),
        "stopped": len([c for c in containers if c["status"] == "exited"]),
        "paused": len([c for c in containers if c["status"] == "paused"])
    }
    
    return result

@mcp.tool()
async def docker_start(container_id: str) -> Dict[str, Any]:
    """
    Start a Docker container.
    
    Args:
        container_id: Container ID or name
        
    Returns:
        Dictionary with operation result
    """
    return api_client.post(f"/api/containers/{container_id}/start")

@mcp.tool()
async def docker_stop(container_id: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Stop a Docker container.
    
    Args:
        container_id: Container ID or name
        timeout: Seconds to wait before killing the container (default: 10)
        
    Returns:
        Dictionary with operation result
    """
    return api_client.post(f"/api/containers/{container_id}/stop", json={"timeout": timeout})

@mcp.tool()
async def docker_restart(container_id: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Restart a Docker container.
    
    Args:
        container_id: Container ID or name
        timeout: Seconds to wait before killing the container (default: 10)
        
    Returns:
        Dictionary with operation result
    """
    return api_client.post(f"/api/containers/{container_id}/restart", json={"timeout": timeout})

@mcp.tool()
async def docker_remove(container_id: str, force: bool = False, remove_volumes: bool = False) -> Dict[str, Any]:
    """
    Remove a Docker container.
    
    Args:
        container_id: Container ID or name
        force: Force removal of running container (default: False)
        remove_volumes: Remove associated volumes (default: False)
        
    Returns:
        Dictionary with operation result
    """
    params = {
        "force": str(force).lower(),
        "volumes": str(remove_volumes).lower()
    }
    
    return api_client.delete(f"/api/containers/{container_id}", params=params)

@mcp.tool()
async def docker_logs(
    container_id: str,
    tail: Union[int, str] = 100,
    since: Optional[str] = None,
    until: Optional[str] = None,
    timestamps: bool = True
) -> Dict[str, Any]:
    """
    Get logs from a Docker container.
    
    Args:
        container_id: Container ID or name
        tail: Number of lines from the end (default: 100, use "all" for all logs)
        since: Show logs since timestamp (e.g., "2h" for 2 hours ago)
        until: Show logs until timestamp
        timestamps: Include timestamps in output (default: True)
        
    Returns:
        Dictionary with logs and metadata
    """
    params = {
        "tail": tail,
        "timestamps": str(timestamps).lower()
    }
    
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    
    result = api_client.get(f"/api/containers/{container_id}/logs", params=params)
    
    if "logs" in result and isinstance(result["logs"], str):
        # Process logs for better readability
        lines = result["logs"].strip().split('\n')
        result["line_count"] = len(lines)
        result["preview"] = {
            "first_5_lines": lines[:5] if len(lines) > 5 else lines,
            "last_5_lines": lines[-5:] if len(lines) > 5 else []
        }
    
    return result

@mcp.tool()
async def docker_stats(container_id: str) -> Dict[str, Any]:
    """
    Get real-time stats for a Docker container.
    
    Args:
        container_id: Container ID or name
        
    Returns:
        Dictionary with container statistics
    """
    result = api_client.get(f"/api/containers/{container_id}/stats")
    
    if "stats" in result:
        stats = result["stats"]
        # Add human-readable values
        if "memory_usage" in stats and "memory_limit" in stats:
            stats["memory_usage_mb"] = round(stats["memory_usage"] / (1024 * 1024), 2)
            stats["memory_limit_gb"] = round(stats["memory_limit"] / (1024 * 1024 * 1024), 2)
    
    return result

@mcp.tool()
async def docker_images() -> Dict[str, Any]:
    """
    List Docker images.
        
    Returns:
        Dictionary with image list and metadata
    """
    result = api_client.get("/api/images")
    
    if "images" in result:
        # Add summary
        images = result["images"]
        total_size = sum(img.get("size", 0) for img in images)
        
        result["summary"] = {
            "total_images": len(images),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
            "untagged": len([img for img in images if not img.get("tags")])
        }
    
    return result

@mcp.tool()
async def docker_pull(image: str, tag: str = "latest") -> Dict[str, Any]:
    """
    Pull a Docker image from a registry.
    
    Args:
        image: Image name (e.g., "nginx", "python")
        tag: Image tag (default: "latest")
        
    Returns:
        Dictionary with pull result
    """
    return api_client.post("/api/images/pull", json={
        "image": image,
        "tag": tag
    })

@mcp.tool()
async def docker_build(
    project: str,
    tag: Optional[str] = None,
    dockerfile: str = "Dockerfile",
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build a Docker image from a Gnosis project.
    
    Args:
        project: Project name (e.g., "gnosis-wraith", "gnosis-ocr")
        tag: Image tag (default: project:latest)
        dockerfile: Dockerfile name (default: "Dockerfile")
        path: Optional absolute path to the project directory
        
    Returns:
        Dictionary with build result
    """
    return api_client.post("/api/build", json={
        "project": project,
        "tag": tag,
        "dockerfile": dockerfile,
        "path": path
    })

@mcp.tool()
async def docker_run(
    image: str,
    name: Optional[str] = None,
    command: Optional[str] = None,
    detach: bool = True,
    ports: Optional[str] = None,
    volumes: Optional[str] = None,
    environment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run a new Docker container (create and start).
    
    Args:
        image: Docker image to use
        name: Container name (optional)
        command: Command to run in container (optional)
        detach: Run container in background (default: True)
        ports: Port mappings (e.g., "80:8080,443:8443")
        volumes: Volume mappings (e.g., "/host/path:/container/path")
        environment: Environment variables (e.g., "KEY1=value1,KEY2=value2")
        
    Returns:
        Dictionary with container information and status
    """
    payload = {
        "image": image,
        "detach": detach,
        "remove": False
    }
    
    if name:
        payload["name"] = name
    if command:
        payload["command"] = command
    
    # Parse ports string into dict
    if ports:
        port_dict = {}
        for mapping in ports.split(','):
            if ':' in mapping:
                host_port, container_port = mapping.strip().split(':')
                port_dict[container_port] = int(host_port)
        payload["ports"] = port_dict
    
    # Parse volumes string into dict
    if volumes:
        volume_dict = {}
        for mapping in volumes.split(','):
            if ':' in mapping:
                host_path, container_path = mapping.strip().split(':')
                volume_dict[host_path] = container_path
        payload["volumes"] = volume_dict
    
    # Parse environment string into dict
    if environment:
        env_dict = {}
        for env_var in environment.split(','):
            if '=' in env_var:
                key, value = env_var.strip().split('=', 1)
                env_dict[key] = value
        payload["environment"] = env_dict
    
    return api_client.post("/api/containers/run", json=payload)

@mcp.tool()
async def docker_health() -> Dict[str, Any]:
    """
    Check the health of the Docker API and Docker daemon.
        
    Returns:
        Dictionary with health status
    """
    result = api_client.get("/health")
    
    # Add connection test
    if result.get("status") == "healthy":
        # Try to list containers as additional check
        containers_result = api_client.get("/api/containers")
        if "error" not in containers_result:
            result["docker_operational"] = True
            result["container_count"] = containers_result.get("total", 0)
        else:
            result["docker_operational"] = False
            result["docker_error"] = containers_result.get("error")
    
    return result

@mcp.tool()
async def docker_inspect(container_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a Docker container.
    
    Args:
        container_id: Container ID or name
        
    Returns:
        Dictionary with detailed container information
    """
    return api_client.get(f"/api/containers/{container_id}")

@mcp.tool()
async def deploy_gnosis_project(project: str, target: str = "local") -> Dict[str, Any]:
    """
    Deploy a Gnosis project using its deployment script.
    
    Args:
        project: Project name (e.g., "gnosis-wraith", "gnosis-ocr")
        target: Deployment target (local, staging, production)
        
    Returns:
        Dictionary with deployment result
    """
    return api_client.post(f"/api/projects/{project}/deploy", json={
        "target": target
    })

if __name__ == "__main__":
    try:
        print(f"Starting Gnosis Docker MCP server v{__version__}", file=sys.stderr)
        print(f"Docker API URL: {DOCKER_API_URL}", file=sys.stderr)
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down Gnosis Docker MCP server...", file=sys.stderr)
    except Exception as e:
        print(f"Error running MCP server: {e}", file=sys.stderr)
        sys.exit(1)
