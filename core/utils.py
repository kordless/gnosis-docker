"""
Utility functions for Gnosis Docker
"""

import asyncio
from functools import wraps
from typing import Dict, Any
from datetime import datetime
from flask import jsonify

def async_route(f):
    """Decorator to handle async routes in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

def format_container_info(container: Any, detailed: bool = False) -> Dict:
    """Format container information for API response"""
    info = {
        'id': container.short_id,
        'name': container.name,
        'image': container.image.tags[0] if container.image.tags else container.image.short_id,
        'status': container.status,
        'state': container.attrs['State'],
        'created': container.attrs['Created'],
        'labels': container.labels,
    }
    
    if detailed:
        info.update({
            'full_id': container.id,
            'ports': container.attrs.get('NetworkSettings', {}).get('Ports', {}),
            'mounts': container.attrs.get('Mounts', []),
            'env': container.attrs.get('Config', {}).get('Env', []),
            'cmd': container.attrs.get('Config', {}).get('Cmd', []),
            'restart_policy': container.attrs.get('HostConfig', {}).get('RestartPolicy', {}),
            'resources': {
                'cpu_shares': container.attrs.get('HostConfig', {}).get('CpuShares'),
                'memory': container.attrs.get('HostConfig', {}).get('Memory'),
            }
        })
    
    return info

def format_image_info(image: Any) -> Dict:
    """Format image information for API response"""
    return {
        'id': image.short_id,
        'tags': image.tags,
        'created': image.attrs.get('Created'),
        'size': image.attrs.get('Size', 0),
        'architecture': image.attrs.get('Architecture'),
        'os': image.attrs.get('Os'),
        'labels': image.labels,
    }

def format_datetime(dt: str) -> str:
    """Format datetime string for consistency"""
    try:
        # Parse and reformat datetime
        dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        return dt_obj.isoformat()
    except:
        return dt

def humanize_size(size: int) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"
