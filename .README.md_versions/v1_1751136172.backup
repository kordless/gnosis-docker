# Gnosis Docker

A Flask async server that exposes Docker management endpoints for MCP (Model Context Protocol) integration with Claude Desktop and Claude Code.

## Features

- Full Docker container management (list, start, stop, restart, remove)
- Docker image management (list, pull, remove, build)
- Container logs streaming
- Container stats and inspection
- Docker build triggers for projects
- Async Flask server with proper error handling
- Security middleware for local-only access

## Directory Structure

```
gnosis-docker/
├── deploy.ps1          # Single deployment script for all environments
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Local development with Redis
├── .env.example       # Environment variable template
├── .gitignore        # Git ignore file
├── README.md         # This file
├── app.py            # Main Flask application
├── core/
│   ├── __init__.py
│   ├── docker_manager.py  # Docker operations handler
│   ├── auth.py           # Authentication middleware
│   ├── config.py         # Configuration management
│   └── utils.py          # Utility functions
└── tests/
    ├── __init__.py
    └── test_docker_api.py
```

## Quick Start

```powershell
# Deploy locally
.\deploy.ps1 -Target local

# Deploy to staging
.\deploy.ps1 -Target staging

# Deploy to production
.\deploy.ps1 -Target production

# Rebuild from scratch
.\deploy.ps1 -Target local -Rebuild

# Dry run (see what would happen)
.\deploy.ps1 -Target production -WhatIf
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/containers` - List all containers
- `GET /api/containers/<id>` - Get container details
- `POST /api/containers/<id>/start` - Start container
- `POST /api/containers/<id>/stop` - Stop container
- `POST /api/containers/<id>/restart` - Restart container
- `DELETE /api/containers/<id>` - Remove container
- `GET /api/containers/<id>/logs` - Get container logs
- `GET /api/containers/<id>/stats` - Get container stats
- `GET /api/images` - List all images
- `POST /api/images/pull` - Pull an image
- `DELETE /api/images/<id>` - Remove an image
- `POST /api/build` - Build a project
- `POST /api/projects/<name>/deploy` - Deploy a project

## MCP Integration

This server is designed to work with Claude Desktop and Claude Code through MCP tools.

## Security

- Local-only access by default
- API key authentication for production
- Request validation and sanitization
