# Gnosis Docker

A Flask async server that exposes Docker management endpoints for MCP (Model Context Protocol) integration with Claude Desktop and Claude Code. This server communicates with the Docker daemon via Docker socket mounting, enabling comprehensive container management through AI assistants.

## Features

- Full Docker container management (list, start, stop, restart, remove)
- Docker image management (list, pull, remove, build)
- Container logs streaming and stats monitoring
- Container inspection and health checks
- Docker build triggers for Gnosis projects
- Async Flask server with proper error handling
- Security middleware for local-only access
- **MCP tools for AI assistant integration**

## Prerequisites and Setup

### Windows with WSL2 (Recommended)

Gnosis Docker works best on Windows using WSL2 with Docker Desktop, as it provides native Docker socket access:

#### 1. Install WSL2
```powershell
# Run as Administrator in PowerShell
wsl --install
# Restart your computer
```

#### 2. Install Docker Desktop
- Download Docker Desktop from https://www.docker.com/products/docker-desktop/
- During installation, ensure "Use WSL 2 based engine" is selected
- Start Docker Desktop

#### 3. Configure Docker Desktop for WSL2
```powershell
# Run the setup helper script
.\setup-docker-desktop.ps1
```

Or manually configure:
1. Open Docker Desktop Settings
2. Go to **General** tab → Enable "Use WSL 2 based engine"
3. Go to **Resources** → **WSL Integration** → Enable integration with your WSL2 distro
4. **Optional for development**: In **General** tab → Enable "Expose daemon on tcp://localhost:2375 without TLS"
5. Click **Apply & Restart**

#### 4. Verify Docker Socket Access
In WSL2:
```bash
# Check if Docker socket is accessible
ls -la /var/run/docker.sock
# Should show: srw-rw---- 1 root docker 0 [date] /var/run/docker.sock

# Test Docker connection
docker version
```

### Windows without WSL2 (Limited)

For development without WSL2, you can use Docker Desktop's TCP endpoint:

1. Enable TCP endpoint in Docker Desktop (Settings → General → "Expose daemon on tcp://localhost:2375")
2. Set environment variable: `$env:DOCKER_HOST = "tcp://localhost:2375"`
3. Run: `.\setup-docker-desktop.ps1` to verify setup

**Note**: This method has limitations and security considerations. WSL2 is strongly recommended.

### Docker Socket Communication

Gnosis Docker uses Docker socket mounting to communicate with the Docker daemon:
- **WSL2**: Uses Unix socket `/var/run/docker.sock` (mounted into containers)
- **TCP**: Uses `tcp://localhost:2375` (for development only)
- **Security**: The server validates all container operations and mounts


## Directory Structure

```
gnosis-docker/
├── deploy.ps1              # Single deployment script for all environments
├── deploy-wsl2.sh          # WSL2 deployment script
├── requirements.txt        # Python dependencies
├── setup.ps1               # Initial setup script
├── setup-docker-desktop.ps1 # Docker Desktop configuration helper
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Local development with Redis
├── .env.example           # Environment variable template
├── .gitignore            # Git ignore file
├── README.md             # This file
├── WSL2_README.md        # WSL2-specific documentation
├── app.py                # Main Flask application
├── core/                 # Core application modules
│   ├── __init__.py
│   ├── docker_manager.py  # Docker operations handler
│   ├── auth.py           # Authentication middleware
│   ├── config.py         # Configuration management
│   ├── validation.py     # Container security validation
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

#### Windows WSL2 (Recommended)
```bash
# From WSL2 terminal
cd /mnt/c/Users/kord/Code/gnosis/gnosis-docker

# Make scripts executable
chmod +x deploy-wsl2.sh

# Deploy locally
./deploy-wsl2.sh
```

#### Windows PowerShell
```powershell
# Initial setup (run once)
.\setup.ps1

# Windows - Deploy locally
.\deploy.ps1 -Target local

# Windows - Deploy to staging
.\deploy.ps1 -Target staging

# Windows - Deploy to production
.\deploy.ps1 -Target production

# Windows - Rebuild from scratch
.\deploy.ps1 -Target local -Rebuild

# Windows - Dry run (see what would happen)
.\deploy.ps1 -Target production -WhatIf
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
      "args": ["C:\\path\\to\\gnosis-docker\\mcp\\gnosis_docker_mcp.py"]
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
.\cleanup_comprehensive.ps1


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
- `DOCKER_HOST` - Docker daemon URL (default: unix:///var/run/docker.sock, or tcp://localhost:2375 for Windows)

- `API_KEY` - Authentication key for production
- `REDIS_URL` - Redis URL for caching (optional)
- `GNOSIS_DOCKER_URL` - API endpoint URL (default: http://localhost:5680)

## Security

- **Local-only access** by default (binds to 127.0.0.1)
- **API key authentication** for production deployments
- **Request validation** and sanitization
- **Docker socket security** with proper permissions and validation
- **CORS protection** for web interfaces
- **Container parameter validation** prevents dangerous operations
- **Volume mount restrictions** limit filesystem access


## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Or use setup script
.\setup.ps1

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

# Or use deployment script
.\deploy.ps1 -Target local

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

1. **Docker daemon not accessible in WSL2**
   - Check Docker Desktop is running
   - Verify WSL2 integration is enabled in Docker Desktop
   - Check Docker socket exists: `ls -la /var/run/docker.sock`
   - Restart Docker Desktop and try again

2. **Docker daemon not accessible on Windows**
   - Ensure Docker Desktop is running
   - Check if TCP endpoint is enabled (Settings → General)
   - Verify `DOCKER_HOST` environment variable
   - Try running: `.\setup-docker-desktop.ps1`

3. **"Cannot connect to Docker daemon" errors**
   - WSL2: Check that Docker socket is mounted: `docker version`
   - Windows: Verify TCP endpoint: `curl http://localhost:2375/version`
   - Check firewall settings
   - Ensure Docker Desktop has started completely

4. **Container fails to start**
   - Check Docker logs: `docker-compose logs gnosis-docker`
   - Verify port 5680 is not in use: `netstat -an | findstr 5680`
   - Check volume mounts in docker-compose.yml

5. **Port 5680 already in use**
   - Stop existing instances
   - Change port in deployment scripts
   - Check for conflicting services

6. **MCP tools not connecting**
   - Verify API server is running on localhost:5680
   - Check firewall settings
   - Ensure MCP dependencies are installed

7. **Path issues with double slashes**
   - Use single backslashes in Windows paths
   - WSL2 paths should use `/mnt/c/` prefix
   - Docker-compose uses Linux-style paths inside containers
   - Check docker-compose.yml volume mappings


### Logs and Debugging

```bash
# Check API server logs
docker-compose logs gnosis-docker

# Enable debug logging
export FLASK_ENV=development  # WSL2
$env:FLASK_ENV = "development"  # PowerShell
python app.py

# Test API health
curl http://localhost:5680/health

# Test Docker socket access (WSL2)
docker version
ls -la /var/run/docker.sock

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
