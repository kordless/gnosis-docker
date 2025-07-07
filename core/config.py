"""
Configuration management for Gnosis Docker
"""

import os
from typing import List

class Config:
    """Application configuration"""
    
    # Flask settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', '5680'))
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Docker settings
    DOCKER_SOCKET = os.getenv('DOCKER_SOCKET', 'unix://var/run/docker.sock')
    DOCKER_TIMEOUT = int(os.getenv('DOCKER_TIMEOUT', '30'))
    
    # Security settings
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:*').split(',')
    API_KEY = os.getenv('API_KEY', None)
    REQUIRE_AUTH = os.getenv('REQUIRE_AUTH', 'False').lower() == 'true'
    LOCAL_ONLY = os.getenv('LOCAL_ONLY', 'True').lower() == 'true'
    
    # Project paths
    GNOSIS_ROOT = os.getenv('GNOSIS_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'gnosis-docker.log')
    
    # Container security settings
    ALLOWED_IMAGES = os.getenv('ALLOWED_IMAGES', '').split(',') if os.getenv('ALLOWED_IMAGES') else []
    BLOCKED_IMAGES = os.getenv('BLOCKED_IMAGES', '').split(',') if os.getenv('BLOCKED_IMAGES') else []
    MAX_MEMORY = os.getenv('MAX_MEMORY', '1g')
    MAX_CPUS = float(os.getenv('MAX_CPUS', '2.0'))
    ALLOWED_VOLUME_PATHS = os.getenv('ALLOWED_VOLUME_PATHS', '/tmp,/data,/app,/mnt/c/Users/kord/Code/gnosis,/projects,C:\\Users\\kord\\Code\\gnosis').split(',')

    BLOCK_PRIVILEGED = os.getenv('BLOCK_PRIVILEGED', 'True').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.REQUIRE_AUTH and not cls.API_KEY:
            raise ValueError("API_KEY must be set when REQUIRE_AUTH is True")
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            if not cls.DEBUG:
                raise ValueError("SECRET_KEY must be set in production")
    
    @classmethod
    def get_project_path(cls, project_name: str) -> str:
        """Get the full path to a project"""
        return os.path.join(os.path.dirname(cls.GNOSIS_ROOT), project_name)
