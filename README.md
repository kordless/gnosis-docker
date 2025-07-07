# Gnosis Docker

A Flask async server that exposes Docker management endpoints for MCP (Model Context Protocol) integration with Claude Desktop and Claude Code.

## Features

- Full Docker container management (list, start, stop, restart, remove)
- Docker image management (list, pull, remove, build)
- Container logs streaming and stats monitoring
- Container inspection and health checks
- Docker build triggers for Gnosis projects
- Async Flask server with proper error handling
- Security middleware for local-only access
- **MCP tools for AI assistant integration**

## Directory Structure

```
gnosis-docker/
├── deploy.ps1              # Single deployment script for all environments
├── deploy-wsl2.sh          # WSL2 deployment script
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Local development with Redis
├── .env.example           # Environment variable template
├── .gitignore            # Git ignore file
├── README.md             # This file
├── app.py                # Main Flask application
├── core/                 # Core application modules
│   ├── __init__.py
│   ├── docker_manager.py  # Docker operations handler
│   ├── auth.py           # Authentication middleware
│   ├── config.py         # Configuration management
│   └── utils.py          # Utility functions
├── tests/                # Test suite
│   ├── __init__.py
│   └── test_docker_api.py
├── mcp/                  # MCP Tools Directory
│   ├── README.md         # MCP tools documentation
│   ├── requirements.txt  # MCP-specific dependencies
│   ├── setup.py          # MCP tools setup script
│   ├── gnosis_docker_mcp.py    # Docker management MCP tool
│   ├── file_manager_mcp.py     # File operations MCP tool
│   └── example_utilities_mcp.py # Example MCP tool
└── cleanup_*.py|ps1|sh   # Repository cleanup scripts
```

## Quick Start

### Deploy the Docker API Server

```powershell
# Windows - Deploy locally
.\\deploy.ps1 -Target local

# Windows - Deploy to staging
.\\deploy.ps1 -Target staging

# Windows - Deploy to production
.\\deploy.ps1 -Target production

# Windows - Rebuild from scratch
.\\deploy.ps1 -Target local -Rebuild

# Windows - Dry run (see what would happen)
.\\deploy.ps1 -Target production -WhatIf
```

```bash
# WSL2 - Deploy locally
./deploy-wsl2.sh local

# WSL2 - Deploy to staging
./deploy-wsl2.sh staging
```

### Use MCP Tools with AI Assistants

The `/mcp` directory contains ready-to-use MCP tools that integrate with Claude Code and Claude Desktop:

```bash
# Navigate to MCP tools
cd mcp

# Install dependencies
pip install -r requirements.txt

# Run setup and validation
python setup.py

# Configure with Claude Code
claude mcp add gnosis-docker python3 gnosis_docker_mcp.py

# Test the integration
claude
# Then try: "list docker containers", "check docker health"
```

See [`mcp/README.md`](mcp/README.md) for complete MCP setup instructions.

## API Endpoints

### Container Management
- `GET /health` - Health check
- `GET /api/containers` - List all containers
- `GET /api/containers/<id>` - Get container details
- `POST /api/containers/<id>/start` - Start container
- `POST /api/containers/<id>/stop` - Stop container
- `POST /api/containers/<id>/restart` - Restart container
- `DELETE /api/containers/<id>` - Remove container
- `GET /api/containers/<id>/logs` - Get container logs
- `GET /api/containers/<id>/stats` - Get container stats

### Image Management
- `GET /api/images` - List all images
- `POST /api/images/pull` - Pull an image
- `DELETE /api/images/<id>` - Remove an image

### Project Operations
- `POST /api/build` - Build a Gnosis project
- `POST /api/projects/<name>/deploy` - Deploy a project

## MCP Integration

This server provides Docker management capabilities to AI assistants through MCP tools:

### Available MCP Tools

1. **Gnosis Docker MCP** (`mcp/gnosis_docker_mcp.py`)
   - Complete Docker management through Claude Code/Desktop
   - List, start, stop, restart containers
   - Get container logs and statistics
   - Manage Docker images
   - Build and deploy Gnosis projects

2. **File Manager MCP** (`mcp/file_manager_mcp.py`)
   - Cross-platform file operations
   - Create, copy, move, delete files and directories
   - Backup support for safe operations

3. **Example Utilities MCP** (`mcp/example_utilities_mcp.py`)
   - Demonstrates MCP development patterns
   - Basic utilities (echo, timestamps, calculations)
   - Text analysis and system information

### Configuration Methods

**Claude Code (Recommended):**
```bash
claude mcp add gnosis-docker python3 /path/to/gnosis-docker/mcp/gnosis_docker_mcp.py
```

**Claude Desktop:**
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "gnosis-docker-mcp": {
      "command": "python",
      "args": ["C:\\\\path\\\\to\\\\gnosis-docker\\\\mcp\\\\gnosis_docker_mcp.py"]
    }
  }
}
```

## Repository Maintenance

### Clean Up Versioning Directories

This repository includes cleanup scripts to remove unwanted versioning directories and Python cache files:

```bash
# Python script (cross-platform)
python cleanup_comprehensive.py

# PowerShell script (Windows)
.\\cleanup_comprehensive.ps1

# Bash script (Linux/WSL2)
./cleanup_quick.sh
```

These scripts will remove:
- `*_versions/` directories
- `__pycache__/` directories
- `*.pyc` files
- Update `.gitignore` with proper patterns

## Environment Variables

- `FLASK_ENV` - Environment (development/staging/production)
- `DOCKER_HOST` - Docker daemon URL (default: unix:///var/run/docker.sock)
- `API_KEY` - Authentication key for production
- `REDIS_URL` - Redis URL for caching (optional)
- `GNOSIS_DOCKER_URL` - API endpoint URL (default: http://localhost:5680)

## Security

- **Local-only access** by default (binds to 127.0.0.1)
- **API key authentication** for production deployments
- **Request validation** and sanitization
- **Docker socket security** with proper permissions
- **CORS protection** for web interfaces

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
python app.py

# Run tests
python -m pytest tests/

# Test API endpoints
python test_api.py
```

### Docker Development

```bash
# Build container
docker build -t gnosis-docker .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f gnosis-docker
```

## Integration with Gnosis Ecosystem

This Docker controller is designed to work with other Gnosis components:

- **Gnosis Wraith** - Web crawling and data extraction
- **Gnosis Mystic** - Function interception and analysis
- **Gnosis Stream** - Data processing and streaming
- **Gnosis Evolve** - Development tools and utilities

The MCP tools provide a unified interface for AI assistants to manage the entire Gnosis ecosystem through Docker containers.

## API Usage Examples

### List Running Containers
```bash
curl http://localhost:5680/api/containers
```

### Start a Container
```bash
curl -X POST http://localhost:5680/api/containers/mycontainer/start
```

### Get Container Logs
```bash
curl http://localhost:5680/api/containers/mycontainer/logs?tail=100
```

### Build a Gnosis Project
```bash
curl -X POST http://localhost:5680/api/build \
  -H "Content-Type: application/json" \
  -d '{"project": "gnosis-wraith", "tag": "latest"}'
```

## Troubleshooting

### Common Issues

1. **Docker daemon not accessible**
   - Check Docker Desktop is running
   - Verify Docker socket permissions
   - Check `DOCKER_HOST` environment variable

2. **Port 5680 already in use**
   - Stop existing instances
   - Change port in deployment scripts
   - Check for conflicting services

3. **MCP tools not connecting**
   - Verify API server is running on localhost:5680
   - Check firewall settings
   - Ensure MCP dependencies are installed

### Logs and Debugging

```bash
# Check API server logs
docker-compose logs gnosis-docker

# Enable debug logging
export FLASK_ENV=development
python app.py

# Test API health
curl http://localhost:5680/health
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## License

This project is part of the Gnosis ecosystem and follows the same licensing terms.
