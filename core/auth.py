"""
Authentication and security middleware
"""

from functools import wraps
from flask import request, jsonify, current_app
from core.config import Config

def require_auth(f):
    """Require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.REQUIRE_AUTH:
            return f(*args, **kwargs)
        
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            # Check in query params as fallback
            api_key = request.args.get('api_key')
        
        if not api_key or api_key != Config.API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def local_only(f):
    """Restrict access to local requests only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not Config.LOCAL_ONLY:
            return f(*args, **kwargs)
        
        # Check if request is from localhost
        remote_addr = request.remote_addr
        if remote_addr not in ['127.0.0.1', 'localhost', '::1']:
            # Also check X-Forwarded-For header
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                # Get the first IP in the chain
                remote_addr = forwarded_for.split(',')[0].strip()
            
            if remote_addr not in ['127.0.0.1', 'localhost', '::1']:
                return jsonify({"error": "Access denied: Local access only"}), 403
        
        return f(*args, **kwargs)
    return decorated_function
