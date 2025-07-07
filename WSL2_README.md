# Gnosis Docker on Windows with WSL2

## Prerequisites

1. **Docker Desktop for Windows** installed with WSL2 backend
2. **WSL2** with a Linux distribution (Ubuntu recommended)
3. Docker Desktop configured with WSL2 integration

## Setup Instructions

### 1. Enable WSL2 Integration in Docker Desktop

1. Open Docker Desktop Settings
2. Go to **Resources** → **WSL Integration**
3. Enable integration with your WSL2 distro
4. Apply & Restart

### 2. Deploy from WSL2

The container needs to run from within WSL2 to access the Docker socket:

```bash
# Open WSL2 terminal (Ubuntu/Debian/etc)
wsl

# Navigate to the project directory
cd /mnt/c/Users/kord/Code/gnosis/gnosis-docker

# Make the deploy script executable
chmod +x deploy-wsl2.sh

# Run the deployment
./deploy-wsl2.sh
```

### 3. Alternative: Manual deployment

```bash
# From within WSL2
cd /mnt/c/Users/kord/Code/gnosis/gnosis-docker

# Build and run
docker-compose up --build -d

# Check logs
docker-compose logs -f gnosis-docker
```

## How it Works

- Docker Desktop runs the Docker Engine in a LinuxKit VM
- It exposes `/var/run/docker.sock` to your WSL2 distros
- Our container mounts this socket to control Docker
- The Flask API at `http://localhost:5680` is accessible from Windows

## Troubleshooting

### "Cannot connect to Docker daemon"
- Ensure Docker Desktop is running
- Check WSL2 integration is enabled in Docker Desktop settings
- Verify you're running commands from within WSL2, not PowerShell

### "Permission denied on /var/run/docker.sock"
- The container runs as root to access the Docker socket
- In production, use proper socket permissions instead

### Socket not found
- Run `ls -la /var/run/docker.sock` in WSL2
- Should show the socket file
- If missing, restart Docker Desktop

## Security Note

The Docker socket provides full control over Docker. In production:
- Use proper authentication
- Consider using Docker's TCP socket with TLS
- Implement RBAC for Docker operations

## Using the MCP Tool

Once deployed, you can install the MCP tool in Claude Desktop:

```powershell
# From PowerShell (not WSL2)
cd C:\Users\kord\Code\gnosis\gnosis-evolve
python evolve.py tool gnosis_docker
```

The tool will connect to the API at `http://localhost:5680`.
