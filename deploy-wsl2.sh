#!/bin/bash
# Deploy script for WSL2
# Run this from within your WSL2 distro

echo "🚀 Gnosis Docker - WSL2 Deployment Script"
echo "========================================="

# Check if we're in WSL2
if [[ ! -f /proc/sys/fs/binfmt_misc/WSLInterop ]] && [[ ! -f /run/WSL ]]; then
    echo "⚠️  Warning: This might not be WSL2"
    echo "   Checking /proc/version: $(cat /proc/version)"
    echo "   Continuing anyway..."
fi


# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker command not found!"
    echo "   Make sure Docker Desktop is running and WSL2 integration is enabled."
    exit 1
fi

# Test Docker connection
echo "🔍 Testing Docker connection..."
if docker version &> /dev/null; then
    echo "✅ Docker is accessible"
else
    echo "❌ Cannot connect to Docker!"
    echo "   Make sure Docker Desktop is running"
    exit 1
fi

# Test socket access
if [ -S /var/run/docker.sock ]; then
    echo "✅ Docker socket is available at /var/run/docker.sock"
else
    echo "❌ Docker socket not found!"
    echo "   Check Docker Desktop WSL2 integration settings"
    exit 1
fi

# Build and run
echo ""
echo "📦 Building Gnosis Docker..."
docker-compose build

echo ""
echo "🏃 Starting Gnosis Docker..."
docker-compose up -d

echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "✅ Deployment complete!"
echo "   Service available at: http://localhost:5680"
echo "   Logs: docker-compose logs -f gnosis-docker"
