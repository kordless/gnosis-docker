# Gnosis Docker MCP Tools

This directory contains Model Context Protocol (MCP) tools that integrate with the Gnosis Docker controller. These tools demonstrate how to build MCP servers that can be used with both Claude Code and Claude Desktop.

## Overview

The MCP tools in this directory are designed to work WITH the Gnosis Docker API (running on `localhost:5680`), not to configure the Gnosis Docker system itself for MCP. They provide external interfaces to interact with Docker containers through Claude AI assistants.

## Tools Included

### 1. `gnosis_docker_mcp.py`
Complete Docker management through the Gnosis Docker API:
- List, start, stop, restart containers
- Get container logs and statistics
- Manage Docker images
- Build and deploy Gnosis projects
- Health monitoring

### 2. `file_manager_mcp.py`
File system management utilities:
- Create, copy, move, delete files and directories
- File operations with backup support
- Cross-platform compatibility

### 3. `example_utilities_mcp.py`
Simple example demonstrating MCP patterns:
- Echo messages
- Timestamp utilities
- Basic calculations
- Text analysis
- System information

## Prerequisites

### Windows Requirements
- **Python 3.8+** installed and in PATH
- **Claude Code** v1.0.24+ or **Claude Desktop** v1.0+
- **Docker Desktop** with WSL2 backend (recommended)
- **Gnosis Docker** running on `localhost:5680`

### WSL2 Requirements (Recommended)
- **WSL2** with Ubuntu/Debian distribution
- **Python 3.8+** (`sudo apt install python3 python3-pip`)
- **Claude Code** v1.0.24+
- **Docker Desktop** with WSL2 integration enabled
- **Gnosis Docker** accessible from WSL via Docker socket

### Docker Setup Requirements
Before using these MCP tools, ensure Gnosis Docker is properly configured:

#### WSL2 Setup (Recommended)
1. Install WSL2: `wsl --install` (as Administrator)
2. Install Docker Desktop with WSL2 backend
3. Enable WSL2 integration in Docker Desktop settings
4. Verify Docker socket access in WSL2:
   ```bash
   ls -la /var/run/docker.sock
   docker version
   ```

#### Windows Setup (Alternative)
1. Enable Docker Desktop TCP endpoint (Settings → General → "Expose daemon")
2. Set environment variable: `$env:DOCKER_HOST = "tcp://localhost:2375"`
3. Run setup script: `.\setup-docker-desktop.ps1`

The Docker socket communication is essential for Gnosis Docker to manage containers and for these MCP tools to function properly.


## Installation

### 1. Install Dependencies

**Windows PowerShell:**
```powershell
cd C:\Users\kord\Code\gnosis\gnosis-docker\mcp
pip install -r requirements.txt
```

**WSL2:**
```bash
cd /mnt/c/Users/kord/Code/gnosis/gnosis-docker/mcp
pip3 install -r requirements.txt
```

### 2. Test MCP Server

Test that the MCP server can start:

**Windows:**
```powershell
python gnosis_docker_mcp.py
```

**WSL2:**
```bash
python3 gnosis_docker_mcp.py
```

You should see: "Starting Gnosis Docker MCP server v2.1.0"

Press `Ctrl+C` to stop the test.

## Configuration Methods

You can configure these MCP tools using either Claude Code or Claude Desktop:

### Method 1: Claude Code Configuration (Recommended)

Claude Code provides a built-in MCP management system:

#### Global Configuration (Available everywhere)
```bash
# Add tools globally
claude mcp add --global gnosis-docker python3 /full/path/to/gnosis-docker/mcp/gnosis_docker_mcp.py
claude mcp add --global file-manager python3 /full/path/to/gnosis-docker/mcp/file_manager_mcp.py
claude mcp add --global example-utils python3 /full/path/to/gnosis-docker/mcp/example_utilities_mcp.py

# List configured tools
claude mcp list

# Remove a tool
claude mcp remove gnosis-docker
```

#### Project-Specific Configuration
```bash
# From the project directory where you want the tools available
cd /path/to/your/project
claude mcp add gnosis-docker python3 /full/path/to/gnosis-docker/mcp/gnosis_docker_mcp.py
```

#### Team Configuration (Shared in Repository)
Create `.mcp.json` in your project root:
```json
{
  "mcpServers": {
    "gnosis-docker": {
      "command": "python3",
      "args": ["/full/path/to/gnosis-docker/mcp/gnosis_docker_mcp.py"]
    }
  }
}
```

### Method 2: Claude Desktop Configuration

Edit your Claude Desktop configuration file:

**Windows:** `C:\Users\kord\AppData\Roaming\Claude\claude_desktop_config.json`


**WSL2:** Access the Windows config file from WSL:
```bash
nano /mnt/c/Users/kord/AppData/Roaming/Claude/claude_desktop_config.json
```

Add to the `mcpServers` section:

```json
{
  "mcpServers": {
    "gnosis-docker-mcp": {
      "command": "python",
      "args": [
        "C:\\Users\\kord\\Code\\gnosis\\gnosis-docker\\mcp\\gnosis_docker_mcp.py"
      ]
    },
    "file-manager-mcp": {
      "command": "python",
      "args": [
        "C:\\Users\\kord\\Code\\gnosis\\gnosis-docker\\mcp\\file_manager_mcp.py"
      ]
    },
    "example-utilities-mcp": {
      "command": "python",
      "args": [
        "C:\\Users\\kord\\Code\\gnosis\\gnosis-docker\\mcp\\example_utilities_mcp.py"
      ]
    }

  }
}
```

**Important:** 
- Use Windows paths even from WSL2
- Restart Claude Desktop after editing the config
- Use `python` (not `python3`) for Windows paths

## Usage Examples

### With Claude Code

After configuring the tools, you can use them directly in Claude Code:

```
# Docker management
list docker containers
start container myapp
get logs for container myapp
check docker health

# File operations
create directory /tmp/test
copy file README.md to /tmp/test/
list files in current directory

# Utilities
echo hello world 3 times
get current timestamp in human format
calculate 15 multiply 23
analyze this text: "The quick brown fox jumps over the lazy dog"
```

### With Claude Desktop

The tools will be available in your Claude Desktop conversations:

```
Can you list all running Docker containers?
What's the current system information?
Calculate 142 divided by 7 and show me the details
```

## Path Configuration

### Windows Users
Use full Windows paths:
```json
"C:\\Users\\kord\\Code\\gnosis\\gnosis-docker\\mcp\\gnosis_docker_mcp.py"
```

### WSL2 Users
For Claude Code running in WSL2, use WSL paths:
```bash
claude mcp add gnosis-docker python3 /mnt/c/Users/kord/Code/gnosis/gnosis-docker/mcp/gnosis_docker_mcp.py
```

For Claude Desktop (always runs on Windows), use Windows paths even from WSL2.

## Environment Variables

### Gnosis Docker API Configuration
Set the API endpoint if it's not on the default port:

**Windows:**
```powershell
$env:GNOSIS_DOCKER_URL = "http://localhost:5680"
```

**WSL2:**
```bash
export GNOSIS_DOCKER_URL="http://localhost:5680"
```

## Troubleshooting

### Common Issues

#### "MCP library not installed"
```bash
pip install mcp
# or
pip3 install mcp
```

#### "No module named 'requests'"
```bash
pip install requests
# or
pip3 install requests
```

#### "Connection refused to localhost:5680"
- Ensure Gnosis Docker is running
- Check the API endpoint: `curl http://localhost:5680/health`
- Verify firewall settings

#### "Python not found"
- Ensure Python is installed and in PATH
- On Windows: Use `python`
- On WSL2: Use `python3`

#### Claude Code can't find MCP server
```bash
# Check if registered
claude mcp list

# Test server manually
python3 gnosis_docker_mcp.py

# Check Claude Code version
claude --version  # Need 1.0.24+
```

#### Claude Desktop doesn't see MCP tools
- Restart Claude Desktop after config changes
- Check config file syntax with JSON validator
- Verify paths are correct Windows paths
- Check Claude Desktop logs for errors

### Debug Mode

Enable debug logging:

**Windows:**
```powershell
$env:MCP_DEBUG = "1"
claude --mcp-debug
```

**WSL2:**
```bash
export MCP_DEBUG=1
claude --mcp-debug
```

## Development

### Creating Custom MCP Tools

Use `example_utilities_mcp.py` as a template:

```python
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My Custom Server")

@mcp.tool()
async def my_custom_tool(param: str) -> str:
    \"\"\"Description of what this tool does\"\"\"
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run()
```

### Best Practices

1. **Error Handling**: Always handle exceptions gracefully
2. **Documentation**: Use clear docstrings for all tools
3. **Input Validation**: Validate all parameters
4. **Logging**: Use `file=sys.stderr` for debug output
5. **Testing**: Test tools manually before deployment

## Integration with Gnosis Ecosystem

These MCP tools are designed to work with:
- **Gnosis Docker API** (localhost:5680)
- **Gnosis Wraith** (web crawling)
- **Gnosis Mystic** (function interception)
- **Gnosis Stream** (data processing)

They provide a consistent interface for AI assistants to interact with the entire Gnosis ecosystem.

## Security Considerations

- MCP tools run with your user permissions
- Validate all inputs from AI assistants
- Use environment variables for sensitive configuration
- Consider containerizing MCP tools for additional isolation
- Regularly update dependencies

## Support

For issues with:
- **MCP Protocol**: Check [Model Context Protocol Documentation](https://modelcontextprotocol.io)
- **Claude Code**: Check [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- **Gnosis Docker**: Check the main Gnosis Docker README
- **This Setup**: Create an issue in the Gnosis Docker repository

## License

These MCP tools are part of the Gnosis ecosystem and follow the same licensing as the parent project.
