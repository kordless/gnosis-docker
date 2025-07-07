# Docker-in-Docker Architecture

## How Gnosis Docker Controls Docker from Inside a Container

### The Socket Mount Approach

Gnosis Docker uses the **Docker socket mount** approach, which is the most common and efficient way to control Docker from within a container.

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

### How It Works

1. **Docker Daemon**: The Docker daemon (dockerd) runs on the host machine and listens on a Unix socket at `/var/run/docker.sock`

2. **Socket Mount**: We mount this socket file into the container as a volume

3. **Docker Client**: Inside the container, the Docker Python SDK (or Docker CLI) connects to this socket

4. **Communication**: When the app makes Docker API calls, they go through the socket to the host's Docker daemon

### Visual Flow

```
Host Machine
├── Docker Daemon (dockerd)
├── /var/run/docker.sock (Unix Socket)
│
Container: gnosis-docker
├── Flask App (app.py)
├── Docker Python SDK
└── /var/run/docker.sock (mounted from host)
    │
    └──> Communicates with host Docker daemon
```

### Important Considerations

1. **Security**: The container has full access to the Docker daemon, which means it can:
   - Start/stop ANY container on the host
   - Build images
   - Access volumes
   - Even start containers that mount the host filesystem

2. **Permissions**: The user inside the container needs to be in the `docker` group or the socket needs appropriate permissions

3. **Read-Only Mount**: We use `:ro` (read-only) but this only prevents writing to the socket file itself, not the Docker operations

### Alternative Approaches (Not Used)

1. **Docker-in-Docker (DinD)**: Running a full Docker daemon inside the container
   - More isolated but more complex
   - Requires privileged mode
   - Can cause storage driver issues

2. **TCP Socket**: Exposing Docker daemon on TCP port
   - Less secure (requires TLS)
   - More complex configuration

3. **SSH**: Connecting to host via SSH to run Docker commands
   - Requires SSH keys
   - More overhead

### Why Socket Mount?

- **Simple**: Just one volume mount
- **Efficient**: Direct communication with host daemon
- **Standard**: Most common approach for CI/CD and management tools
- **No Overhead**: No extra daemon or network layer

### Security Best Practices

1. **Local Only**: The API is restricted to localhost access
2. **No Internet Exposure**: Should never be exposed to the internet
3. **Audit Logs**: All operations should be logged
4. **Limited Scope**: Only necessary Docker operations exposed
5. **Authentication**: Can add API key authentication for additional security

### Example API Call Flow

1. Claude Desktop calls: `POST http://localhost:5680/api/containers/abc123/restart`
2. Flask app receives request
3. Docker Python SDK calls: `container.restart()`
4. This goes through `/var/run/docker.sock` to host Docker daemon
5. Host Docker daemon restarts the container
6. Response flows back through the socket to the app
7. App returns JSON response to Claude

This architecture allows Gnosis Docker to manage all Docker containers on the host system, including other Gnosis projects like gnosis-wraith, while running inside its own container.
