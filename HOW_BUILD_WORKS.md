# How Gnosis Docker Builds Projects

## Two Approaches for Building Projects from Inside a Container

### Approach 1: Docker API Build (Recommended)
When using the Docker API, the **host Docker daemon** does the building, not the container.

```python
# Inside the container, we call:
client.images.build(path="/Users/kord/Code/gnosis/gnosis-wraith", tag="gnosis-wraith:latest")

# This tells the HOST Docker daemon to:
# 1. Go to that path ON THE HOST filesystem
# 2. Read the Dockerfile ON THE HOST
# 3. Build the image using HOST resources
# 4. The container never needs access to the files
```

**How it works:**
1. Container sends build command through Docker socket
2. Host Docker daemon receives the command
3. Host daemon accesses the project files directly from host filesystem
4. Host daemon runs the build
5. Built image is available to both host and container

**Pros:**
- No need to mount project directories
- Container stays lightweight
- Security: Container can't modify project files
- Works with any project location on host

**Cons:**
- Paths must be absolute host paths
- Container needs to know where projects are located

### Approach 2: Mount Projects Directory (Alternative)
Mount the entire gnosis directory into the container:

```yaml
volumes:
  - C:/Users/kord/Code/gnosis:/gnosis:ro
```

Then the container can access files directly, but still uses Docker API to build.

### Updated Build Function

Here's how the build function should work using Approach 1:

```python
async def build_project(self, project_name: str, tag: str = None) -> Dict:
    """Build a project using host paths"""
    
    # Define host paths for known projects
    host_projects = {
        'gnosis-wraith': 'C:/Users/kord/Code/gnosis/gnosis-wraith',
        'gnosis-ocr': 'C:/Users/kord/Code/gnosis/gnosis-ocr',
        'gnosis-mystic': 'C:/Users/kord/Code/gnosis/gnosis-mystic',
        'gnosis-docker': 'C:/Users/kord/Code/gnosis/gnosis-docker',
    }
    
    if project_name not in host_projects:
        raise ValueError(f"Unknown project: {project_name}")
    
    host_path = host_projects[project_name]
    tag = tag or f"{project_name}:latest"
    
    # Tell the HOST Docker daemon to build from HOST path
    image, logs = await self.client.images.build(
        path=host_path,  # This is a HOST filesystem path
        tag=tag,
        rm=True
    )
    
    return {
        'project': project_name,
        'image': image.tags[0],
        'built_from': host_path
    }
```

### The Key Insight

The container is just a **messenger** - it tells the host Docker daemon what to do, but the host daemon does all the actual work using host resources and host filesystem.

### Real-World Example

When you run:
```bash
POST /api/projects/gnosis-wraith/build
```

1. Gnosis Docker container receives the request
2. Container sends build command through Docker socket
3. Host Docker daemon goes to `C:/Users/kord/Code/gnosis/gnosis-wraith`
4. Host daemon reads the Dockerfile and builds the image
5. The built image `gnosis-wraith:latest` is now available
6. Container returns success response

### For Deployment Scripts

Similarly, when running deployment scripts:

```python
# This runs ON THE HOST through Docker
proc = await asyncio.create_subprocess_exec(
    'docker', 'exec', 'gnosis-docker',
    'powershell.exe', '-File', '/gnosis/gnosis-wraith/deploy.ps1'
)
```

Or we can trigger the script to run directly on the host if we have the right setup.

### Best Practice

Use **Approach 1** (Docker API with host paths) because:
- More secure (container can't modify source code)
- Simpler (no complex volume mounts)
- More flexible (can build any project anywhere on host)
- Standard Docker build behavior
