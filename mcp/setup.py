#!/usr/bin/env python3
"""
Setup script for Gnosis Docker MCP Tools
Handles installation and configuration on Windows and WSL2
"""

import sys
import os
import subprocess
import json
import platform
from pathlib import Path

def run_command(cmd, shell=False):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_python():
    """Check if Python is properly installed"""
    print("Checking Python installation...")
    
    # Check Python version
    version_info = sys.version_info
    if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
        print(f"❌ Python 3.8+ required, found {version_info.major}.{version_info.minor}")
        return False
    
    print(f"✅ Python {version_info.major}.{version_info.minor}.{version_info.micro}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("Installing Python dependencies...")
    
    pip_cmd = "pip3" if platform.system() != "Windows" else "pip"
    success, stdout, stderr = run_command([pip_cmd, "install", "-r", "requirements.txt"])
    
    if success:
        print("✅ Dependencies installed successfully")
        return True
    else:
        print(f"❌ Failed to install dependencies: {stderr}")
        return False

def test_mcp_servers():
    """Test that MCP servers can start"""
    print("Testing MCP servers...")
    
    servers = [
        ("gnosis_docker_mcp.py", "Gnosis Docker MCP"),
        ("file_manager_mcp.py", "File Manager MCP"),
        ("example_utilities_mcp.py", "Example Utilities MCP")
    ]
    
    python_cmd = "python3" if platform.system() != "Windows" else "python"
    
    for server_file, server_name in servers:
        if not os.path.exists(server_file):
            print(f"❌ {server_name}: File not found ({server_file})")
            continue
        
        # Try to import the server (basic syntax check)
        try:
            result = subprocess.run([python_cmd, "-c", f"import {server_file[:-3]}"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ {server_name}: OK")
            else:
                print(f"❌ {server_name}: Import failed")
                print(f"   Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"✅ {server_name}: OK (timeout expected)")
        except Exception as e:
            print(f"❌ {server_name}: Error - {e}")

def check_claude_code():
    """Check if Claude Code is installed"""
    print("Checking Claude Code installation...")
    
    success, stdout, stderr = run_command(["claude", "--version"])
    if success:
        print(f"✅ Claude Code: {stdout.strip()}")
        
        # Check if version is 1.0.24+
        try:
            version_line = stdout.strip()
            if "1.0." in version_line:
                version_parts = version_line.split("1.0.")[1].split()[0]
                version_num = int(version_parts)
                if version_num >= 24:
                    print("✅ Claude Code version supports MCP")
                else:
                    print("⚠️  Claude Code version may not support MCP (need 1.0.24+)")
        except:
            print("⚠️  Could not parse Claude Code version")
        
        return True
    else:
        print("❌ Claude Code not found")
        print("   Install from: https://docs.anthropic.com/claude-code")
        return False

def check_gnosis_docker():
    """Check if Gnosis Docker API is accessible"""
    print("Checking Gnosis Docker API...")
    
    try:
        import requests
        response = requests.get("http://localhost:5680/health", timeout=5)
        if response.status_code == 200:
            print("✅ Gnosis Docker API is accessible")
            return True
        else:
            print(f"❌ Gnosis Docker API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Gnosis Docker API not accessible (connection refused)")
        print("   Make sure Gnosis Docker is running on localhost:5680")
        return False
    except ImportError:
        print("⚠️  Cannot check Gnosis Docker API (requests not installed)")
        return False
    except Exception as e:
        print(f"❌ Error checking Gnosis Docker API: {e}")
        return False

def show_configuration_help():
    """Show configuration instructions"""
    print("\\n" + "="*50)
    print("CONFIGURATION INSTRUCTIONS")
    print("="*50)
    
    current_dir = os.getcwd()
    
    print("\\n1. CLAUDE CODE CONFIGURATION (Recommended)")
    print("-" * 40)
    print("Add MCP tools to Claude Code:")
    print(f"claude mcp add gnosis-docker python3 {current_dir}/gnosis_docker_mcp.py")
    print(f"claude mcp add file-manager python3 {current_dir}/file_manager_mcp.py")
    print(f"claude mcp add example-utils python3 {current_dir}/example_utilities_mcp.py")
    print("\\nThen start Claude Code and test with:")
    print("• list docker containers")
    print("• get current timestamp")
    print("• create directory /tmp/test")
    
    print("\\n2. CLAUDE DESKTOP CONFIGURATION")
    print("-" * 40)
    
    if platform.system() == "Windows":
        config_path = f"C:\\\\Users\\\\{os.getenv('USERNAME', 'USER')}\\\\AppData\\\\Roaming\\\\Claude\\\\claude_desktop_config.json"
    else:
        config_path = f"/mnt/c/Users/{os.getenv('USER', 'USER')}/AppData/Roaming/Claude/claude_desktop_config.json"
    
    print(f"Edit: {config_path}")
    print("\\nAdd to mcpServers section:")
    
    # Convert to Windows path format for the JSON
    windows_path = current_dir.replace("/mnt/c/", "C:\\\\").replace("/", "\\\\")
    
    config_example = {
        "gnosis-docker-mcp": {
            "command": "python",
            "args": [f"{windows_path}\\\\gnosis_docker_mcp.py"]
        },
        "file-manager-mcp": {
            "command": "python", 
            "args": [f"{windows_path}\\\\file_manager_mcp.py"]
        },
        "example-utilities-mcp": {
            "command": "python",
            "args": [f"{windows_path}\\\\example_utilities_mcp.py"]
        }
    }
    
    print(json.dumps(config_example, indent=2))

def main():
    """Main setup function"""
    print("="*50)
    print("GNOSIS DOCKER MCP TOOLS SETUP")
    print("="*50)
    
    print(f"Platform: {platform.system()}")
    print(f"Current directory: {os.getcwd()}")
    
    # Check all prerequisites
    checks = [
        ("Python 3.8+", check_python()),
        ("Dependencies", install_dependencies()),
        ("MCP Servers", test_mcp_servers()),
        ("Claude Code", check_claude_code()),
        ("Gnosis Docker", check_gnosis_docker())
    ]
    
    print("\\n" + "="*50)
    print("SETUP SUMMARY")
    print("="*50)
    
    passed = 0
    for check_name, result in checks:
        if result:
            print(f"✅ {check_name}")
            passed += 1
        else:
            print(f"❌ {check_name}")
    
    print(f"\\nPassed: {passed}/{len(checks)} checks")
    
    if passed == len(checks):
        print("\\n🎉 All checks passed! MCP tools are ready to use.")
    else:
        print("\\n⚠️  Some checks failed. Please fix the issues above.")
    
    # Always show configuration help
    show_configuration_help()
    
    print("\\n" + "="*50)
    print("For more information, see README.md")
    print("="*50)

if __name__ == "__main__":
    main()
