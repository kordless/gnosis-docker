"""
Gnosis Docker - Main Flask Application
Async Flask server for Docker management via MCP
"""

import os
import asyncio
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import docker
from docker.errors import DockerException, APIError, NotFound

from core.config import Config
from core.auth import require_auth, local_only
from core.docker_manager import DockerManager
# from core.compose_manager import ComposeManager  # TODO: Add pyyaml to Docker image
from core.utils import async_route, format_container_info, format_image_info

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, origins=Config.ALLOWED_ORIGINS)

# Initialize Docker manager
docker_manager = DockerManager()
# compose_manager = ComposeManager(docker_manager.client)  # TODO: Add pyyaml to Docker image

# Build status tracking (in production, use Redis or database)
build_status = {}

# Error handlers
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return jsonify({
        "error": e.name,
        "message": e.description,
        "status": e.code
    }), e.code

@app.errorhandler(DockerException)
def handle_docker_exception(e):
    return jsonify({
        "error": "Docker Error",
        "message": str(e),
        "status": 500
    }), 500

@app.errorhandler(Exception)
def handle_generic_exception(e):
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "status": 500
    }), 500

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}), 200


# API Help
@app.route('/api/help', methods=['GET'])
def api_help():
    """API documentation for Claude Code"""
    return jsonify({
        "service": "Gnosis Docker API",
        "endpoints": {
            "GET /api/containers": "List containers (params: all=true)",
            "POST /api/containers/<id>/start": "Start container",
            "POST /api/containers/<id>/stop": "Stop container",
            "GET /api/containers/<id>/logs": "Get logs (params: tail=100)",
            "GET /api/images": "List images",
            "POST /api/images/pull": "Pull image {image:name, tag:latest}",
            "POST /api/build": "Build project {project:name}"
        }
    }), 200


# Container endpoints
@app.route('/api/containers', methods=['GET'])

@local_only
@async_route
async def list_containers():
    """List all containers"""
    all_containers = request.args.get('all', 'false').lower() == 'true'
    filters = {}
    
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    
    containers = await docker_manager.list_containers(all=all_containers, filters=filters)
    return jsonify({
        "containers": [format_container_info(c) for c in containers],
        "total": len(containers)
    })

@app.route('/api/containers/<container_id>', methods=['GET'])
@local_only
@async_route
async def get_container(container_id):
    """Get container details"""
    container = await docker_manager.get_container(container_id)
    if not container:
        return jsonify({"error": "Container not found"}), 404
    
    return jsonify(format_container_info(container, detailed=True))

@app.route('/api/containers/<container_id>/start', methods=['POST'])
@local_only
@async_route
async def start_container(container_id):
    """Start a container"""
    success = await docker_manager.start_container(container_id)
    if success:
        return jsonify({"message": f"Container {container_id} started successfully"})
    return jsonify({"error": "Failed to start container"}), 400

@app.route('/api/containers/<container_id>/stop', methods=['POST'])
@local_only
@async_route
async def stop_container(container_id):
    """Stop a container"""
    try:
        timeout = request.json.get('timeout', 10) if request.json else 10
        success = await docker_manager.stop_container(container_id, timeout=timeout)
        if success:
            return jsonify({"message": f"Container {container_id} stopped successfully"})
        return jsonify({"error": "Failed to stop container"}), 400
    except Exception as e:
        app.logger.error(f"Error stopping container {container_id}: {e}", exc_info=True)
        return jsonify({"error": f"Failed to stop container: {str(e)}"}), 500


@app.route('/api/containers/<container_id>/restart', methods=['POST'])
@local_only
@async_route
async def restart_container(container_id):
    """Restart a container"""
    timeout = request.json.get('timeout', 10) if request.json else 10
    success = await docker_manager.restart_container(container_id, timeout=timeout)
    if success:
        return jsonify({"message": f"Container {container_id} restarted successfully"})
    return jsonify({"error": "Failed to restart container"}), 400

@app.route('/api/containers/<container_id>', methods=['DELETE'])
@local_only
@async_route
async def remove_container(container_id):
    """Remove a container"""
    force = request.args.get('force', 'false').lower() == 'true'
    volumes = request.args.get('volumes', 'false').lower() == 'true'
    
    success = await docker_manager.remove_container(container_id, force=force, v=volumes)
    if success:
        return jsonify({"message": f"Container {container_id} removed successfully"})
    return jsonify({"error": "Failed to remove container"}), 400

@app.route('/api/containers/<container_id>/logs', methods=['GET'])
@local_only
@async_route
async def get_container_logs(container_id):
    """Get container logs"""
    tail = request.args.get('tail', 100)
    since = request.args.get('since')
    until = request.args.get('until')
    timestamps = request.args.get('timestamps', 'false').lower() == 'true'
    
    logs = await docker_manager.get_container_logs(
        container_id, 
        tail=tail,
        since=since,
        until=until,
        timestamps=timestamps
    )
    
    if logs is None:
        return jsonify({"error": "Failed to get logs"}), 400
    
    return jsonify({
        "container_id": container_id,
        "logs": logs
    })

@app.route('/api/containers/<container_id>/stats', methods=['GET'])
@local_only
@async_route
async def get_container_stats(container_id):
    """Get container stats"""
    stats = await docker_manager.get_container_stats(container_id)
    if stats is None:
        return jsonify({"error": "Failed to get stats"}), 400
    
    return jsonify({
        "container_id": container_id,
        "stats": stats
    })

@app.route('/api/containers/create', methods=['POST'])
@local_only
@async_route
async def create_container():
    """Create a new container"""
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"error": "Image name required"}), 400
    
    try:
        # Extract parameters from request
        image = data['image']
        name = data.get('name')
        command = data.get('command')
        environment = data.get('environment')
        ports = data.get('ports')
        volumes = data.get('volumes')
        network = data.get('network')
        
        # Additional docker options
        kwargs = {}
        for key in ['restart_policy', 'mem_limit', 'cpu_count', 'working_dir', 'user']:
            if key in data:
                kwargs[key] = data[key]
        
        result = await docker_manager.create_container(
            image=image,
            name=name,
            command=command,
            environment=environment,
            ports=ports,
            volumes=volumes,
            network=network,
            **kwargs
        )
        
        if result:
            return jsonify({
                "message": f"Container created successfully",
                "container": result
            }), 201
        else:
            return jsonify({"error": "Failed to create container"}), 400
            
    except Exception as e:
        app.logger.error(f"Error creating container: {e}", exc_info=True)
        return jsonify({"error": f"Failed to create container: {str(e)}"}), 500

@app.route('/api/containers/run', methods=['POST'])
@local_only
@async_route
async def run_container():
    """Create and start a new container"""
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"error": "Image name required"}), 400
    
    try:
        # Extract parameters from request
        image = data['image']
        name = data.get('name')
        command = data.get('command')
        detach = data.get('detach', True)
        remove = data.get('remove', False)
        environment = data.get('environment')
        ports = data.get('ports')
        volumes = data.get('volumes')
        network = data.get('network')
        
        # Additional docker options
        kwargs = {}
        for key in ['restart_policy', 'mem_limit', 'cpu_count', 'working_dir', 'user']:
            if key in data:
                kwargs[key] = data[key]
        
        result = await docker_manager.run_container(
            image=image,
            name=name,
            command=command,
            detach=detach,
            remove=remove,
            environment=environment,
            ports=ports,
            volumes=volumes,
            network=network,
            **kwargs
        )
        
        if result:
            status_code = 201 if detach else 200
            return jsonify({
                "message": f"Container {'started' if detach else 'executed'} successfully",
                "container": result
            }), status_code
        else:
            return jsonify({"error": "Failed to run container"}), 400
            
    except Exception as e:
        app.logger.error(f"Error running container: {e}", exc_info=True)
        return jsonify({"error": f"Failed to run container: {str(e)}"}), 500

# Image endpoints
@app.route('/api/images', methods=['GET'])
@local_only
@async_route
async def list_images():
    """List all images"""
    images = await docker_manager.list_images()
    return jsonify({
        "images": [format_image_info(img) for img in images],
        "total": len(images)
    })

@app.route('/api/images/pull', methods=['POST'])
@local_only
@async_route
async def pull_image():
    """Pull an image"""
    data = request.json
    if not data or 'image' not in data:
        return jsonify({"error": "Image name required"}), 400
    
    image_name = data['image']
    tag = data.get('tag', 'latest')
    
    result = await docker_manager.pull_image(image_name, tag)
    if result:
        return jsonify({
            "message": f"Image {image_name}:{tag} pulled successfully",
            "image": result
        })
    return jsonify({"error": "Failed to pull image"}), 400

@app.route('/api/images/<path:image_id>', methods=['DELETE'])
@local_only
@async_route
async def remove_image(image_id):
    """Remove an image"""
    force = request.args.get('force', 'false').lower() == 'true'
    
    success = await docker_manager.remove_image(image_id, force=force)
    if success:
        return jsonify({"message": f"Image {image_id} removed successfully"})
    return jsonify({"error": "Failed to remove image"}), 400

# Build endpoints
@app.route('/api/build', methods=['POST'])
@local_only
def build_project():
    """Build a Docker image from a project"""
    
    def run_build_async(project_name, project_path, tag, dockerfile, build_id):
        """Run the build in a background thread"""
        try:
            build_status[build_id] = {
                "status": "building",
                "started": datetime.utcnow().isoformat(),
                "project": project_name,
                "tag": tag
            }
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async build
            result = loop.run_until_complete(
                docker_manager.build_image(project_path, tag, dockerfile)
            )
            
            build_status[build_id] = {
                "status": "completed",
                "started": build_status[build_id]["started"],
                "completed": datetime.utcnow().isoformat(),
                "project": project_name,
                "tag": tag,
                "result": result
            }
            app.logger.info(f"Build completed for {project_name}: {result}")
        except Exception as e:
            app.logger.error(f"Build failed for {project_name}: {e}")
            build_status[build_id] = {
                "status": "failed",
                "error": str(e),
                "project": project_name,
                "tag": tag
            }
        finally:
            loop.close()
    
    try:

        data = request.json
        if not data or 'project' not in data:
            return jsonify({"error": "Project name required"}), 400
        
        project_name = data['project']
        tag = data.get('tag')
        dockerfile = data.get('dockerfile', 'Dockerfile')
        custom_path = data.get('path')  # Get custom path if provided
        
        # Generate a build ID
        build_id = f"{project_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        
        # Define host paths for known projects
        # When running from WSL2, Docker Desktop can access Windows paths via /mnt/c
        # Check if we're running in a container
        is_container = os.path.exists('/.dockerenv')
        
        # Define host paths for known projects
        if is_container:
            # When running in container, projects are mounted at /projects
            host_projects = {
                'gnosis-wraith': '/projects/gnosis-wraith',
                'gnosis-ocr': '/projects/gnosis-ocr',
                'gnosis-mystic': '/projects/gnosis-mystic',
                'gnosis-docker': '/projects/gnosis-docker',
                'gnosis-evolve': '/projects/gnosis-evolve',
                'gnosis-forge': '/projects/gnosis-forge',
            }
        else:
            # When running on host, use Windows paths
            host_projects = {
                'gnosis-wraith': 'C:\\Users\\kord\\code\\gnosis\\gnosis-wraith',
                'gnosis-ocr': 'C:\\Users\\kord\\code\\gnosis\\gnosis-ocr',
                'gnosis-mystic': 'C:\\Users\\kord\\code\\gnosis\\gnosis-mystic',
                'gnosis-docker': 'C:\\Users\\kord\\code\\gnosis\\gnosis-docker',
                'gnosis-evolve': 'C:\\Users\\kord\\code\\gnosis\\gnosis-evolve',
                'gnosis-forge': 'C:\\Users\\kord\\code\\gnosis\\gnosis-forge',
            }




        
        if custom_path:
            # Use the custom path provided
            project_path = custom_path
            app.logger.info(f"Using custom path for {project_name}: {project_path}")
        elif project_name not in host_projects:
            return jsonify({
                "error": f"Unknown project: {project_name}",
                "known_projects": list(host_projects.keys()),
                "suggestion": "Provide a custom path parameter for unknown projects"
            }), 400
        else:
            # Get the host path from predefined projects
            project_path = host_projects[project_name]
        tag = tag or f"{project_name}:latest"
        
        # Log the path for debugging
        app.logger.info(f"Building {project_name} from path: {project_path}")
        
        # Start the build in a background thread
        build_thread = threading.Thread(
            target=run_build_async,
            args=(project_name, project_path, tag, dockerfile, build_id)
        )
        build_thread.daemon = True
        build_thread.start()
        
        # Return immediately with build ID
        return jsonify({
            "message": "Build started",
            "build_id": build_id,
            "project": project_name,
            "tag": tag,
            "host_path": project_path,
            "status_endpoint": f"/api/build/{build_id}/status"
        }), 202  # 202 Accepted

    except Exception as e:
        app.logger.error(f"Build error for project {project_name}: {e}", exc_info=True)
        return jsonify({"error": f"Build failed: {str(e)}"}), 500



# Build status endpoint
@app.route('/api/build/<build_id>/status', methods=['GET'])
@local_only
def get_build_status(build_id):
    """Get the status of a build"""
    if build_id not in build_status:
        return jsonify({"error": "Build ID not found"}), 404
    
    return jsonify(build_status[build_id])

# Docker Compose endpoints (TODO: Add pyyaml to Docker image)
'''
@app.route('/api/compose/up', methods=['POST'])
@local_only
@async_route
async def compose_up():
    """Deploy services using docker-compose"""
    data = request.json
    if not data:
        return jsonify({"error": "Request body required"}), 400
    
    # Check for compose file content or path
    if 'compose_file' not in data and 'compose_content' not in data:
        return jsonify({"error": "Either compose_file path or compose_content required"}), 400
    
    try:
        # Get compose content
        if 'compose_content' in data:
            compose_content = data['compose_content']
        else:
            # Read from file path
            compose_file = data['compose_file']
            if not os.path.exists(compose_file):
                return jsonify({"error": f"Compose file not found: {compose_file}"}), 404
            
            with open(compose_file, 'r') as f:
                compose_content = f.read()
        
        # Deploy
        project_name = data.get('project_name', 'gnosis-project')
        services = data.get('services')  # Optional: specific services
        detach = data.get('detach', True)
        build = data.get('build', False)
        
        result = await compose_manager.compose_up(
            compose_content=compose_content,
            project_name=project_name,
            services=services,
            detach=detach,
            build=build
        )
        
        if result['success']:
            return jsonify({
                "message": "Compose project deployed successfully",
                "result": result
            }), 201
        else:
            return jsonify({
                "message": "Compose project deployed with errors",
                "result": result
            }), 207  # Multi-status
            
    except Exception as e:
        app.logger.error(f"Error deploying compose project: {e}", exc_info=True)
        return jsonify({"error": f"Failed to deploy compose project: {str(e)}"}), 500

@app.route('/api/compose/down', methods=['POST'])
@local_only
@async_route
async def compose_down():
    """Stop and remove compose project"""
    data = request.json
    if not data or 'project_name' not in data:
        return jsonify({"error": "project_name required"}), 400
    
    try:
        project_name = data['project_name']
        remove_volumes = data.get('remove_volumes', False)
        remove_images = data.get('remove_images', False)
        
        result = await compose_manager.compose_down(
            project_name=project_name,
            remove_volumes=remove_volumes,
            remove_images=remove_images
        )
        
        if result['success']:
            return jsonify({
                "message": "Compose project removed successfully",
                "result": result
            })
        else:
            return jsonify({
                "message": "Compose project removed with errors",
                "result": result
            }), 207
            
    except Exception as e:
        app.logger.error(f"Error removing compose project: {e}", exc_info=True)
        return jsonify({"error": f"Failed to remove compose project: {str(e)}"}), 500

@app.route('/api/compose/ps', methods=['GET'])
@local_only
@async_route
async def compose_ps():
    """List containers for compose project"""
    project_name = request.args.get('project_name')
    if not project_name:
        return jsonify({"error": "project_name required"}), 400
    
    try:
        containers = await compose_manager.compose_ps(project_name)
        return jsonify({
            "project_name": project_name,
            "containers": containers,
            "total": len(containers)
        })
    except Exception as e:
        app.logger.error(f"Error listing compose containers: {e}", exc_info=True)
        return jsonify({"error": f"Failed to list compose containers: {str(e)}"}), 500

@app.route('/api/compose/logs', methods=['GET'])
@local_only
@async_route
async def compose_logs():
    """Get logs for compose services"""
    project_name = request.args.get('project_name')
    if not project_name:
        return jsonify({"error": "project_name required"}), 400
    
    try:
        services = request.args.getlist('services')
        tail = int(request.args.get('tail', 100))
        
        logs = await compose_manager.compose_logs(
            project_name=project_name,
            services=services if services else None,
            tail=tail
        )
        
        return jsonify({
            "project_name": project_name,
            "logs": logs
        })
    except Exception as e:
        app.logger.error(f"Error getting compose logs: {e}", exc_info=True)
        return jsonify({"error": f"Failed to get compose logs: {str(e)}"}), 500
'''

# Project deployment endpoint

@app.route('/api/projects/<project_name>/deploy', methods=['POST'])
@local_only
@async_route
async def deploy_project(project_name):
    """Deploy a specific project (e.g., gnosis-wraith)"""
    data = request.json or {}
    target = data.get('target', 'local')
    
    # Map project names to paths
    project_paths = {
        'gnosis-wraith': os.path.join(os.path.dirname(app.root_path), 'gnosis-wraith'),
        'gnosis-ocr': os.path.join(os.path.dirname(app.root_path), 'gnosis-ocr'),
        'gnosis-mystic': os.path.join(os.path.dirname(app.root_path), 'gnosis-mystic'),
    }
    
    if project_name not in project_paths:
        return jsonify({"error": f"Unknown project: {project_name}"}), 400
    
    project_path = project_paths[project_name]
    if not os.path.exists(project_path):
        return jsonify({"error": f"Project not found: {project_path}"}), 404
    
    # Check for deployment script
    deploy_script = os.path.join(project_path, 'deploy.ps1')
    if not os.path.exists(deploy_script):
        deploy_script = os.path.join(project_path, 'scripts', 'deploy_v2.ps1')
    
    if not os.path.exists(deploy_script):
        return jsonify({"error": "No deployment script found"}), 400
    
    # Execute deployment
    try:
        proc = await asyncio.create_subprocess_exec(
            'powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', deploy_script,
            '-Target', target,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=project_path
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            return jsonify({
                "message": f"Project {project_name} deployed successfully",
                "target": target,
                "output": stdout.decode('utf-8')
            })
        else:
            return jsonify({
                "error": "Deployment failed",
                "stderr": stderr.decode('utf-8')
            }), 400
            
    except Exception as e:
        return jsonify({"error": f"Deployment error: {str(e)}"}), 500

# Main entry point
if __name__ == '__main__':
    # Run the app
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
