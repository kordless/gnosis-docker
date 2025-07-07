
import sys
import os
import shutil
import logging
import time
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

__version__ = "0.2.0"
__updated__ = "2025-06-27"


# Define log path in the logs directory parallel to tools
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
logs_dir = os.path.join(parent_dir, "logs")

# Configure logging to file in the logs directory
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, "file_manager.log"))
    ]
)
logger = logging.getLogger("file_manager")

# imports mcp-server
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("file-manager-server")

def ensure_version_dir(file_path: str) -> str:
    """
    Ensures that a versions directory exists for the given file.
    The versions directory is stored alongside the file with the name 
    '.{filename}_versions'.
    
    Args:
        file_path: Path to the file for which to create a versions directory
    
    Returns:
        Path to the versions directory
    """
    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    versions_dir = os.path.join(directory, f".{filename}_versions")
    os.makedirs(versions_dir, exist_ok=True)
    return versions_dir

def get_file_versions(file_path: str) -> List[Dict[str, Any]]:
    """
    Gets information about all versions of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        List of dictionaries with version information
    """
    versions = []
    
    if not os.path.exists(file_path):
        return versions
    
    versions_dir = ensure_version_dir(file_path)
    
    if not os.path.exists(versions_dir):
        return versions
    
    try:
        version_files = [f for f in os.listdir(versions_dir) if os.path.isfile(os.path.join(versions_dir, f))]
        
        for version_file in version_files:
            match = re.match(r"v(\d+)_(\d+)\.backup", version_file)
            if match:
                version_number = int(match.group(1))
                timestamp = int(match.group(2))
                
                version_path = os.path.join(versions_dir, version_file)
                stats = os.stat(version_path)
                
                versions.append({
                    "version": version_number,
                    "timestamp": timestamp,
                    "date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                    "size": stats.st_size,
                    "size_human": f"{stats.st_size/1024:.1f}KB" if stats.st_size < 1048576 else f"{stats.st_size/1048576:.1f}MB",
                    "path": version_path
                })
    except Exception as e:
        logger.error(f"Error getting versions for {file_path}: {str(e)}")
    
    versions.sort(key=lambda x: x["version"], reverse=True)
    
    if os.path.exists(file_path):
        stats = os.stat(file_path)
        versions.insert(0, {
            "version": "current",
            "timestamp": int(stats.st_mtime),
            "date": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "size": stats.st_size,
            "size_human": f"{stats.st_size/1024:.1f}KB" if stats.st_size < 1048576 else f"{stats.st_size/1048576:.1f}MB",
            "path": file_path
        })
    
    return versions

def get_next_version_number(file_path: str) -> int:
    """Gets the next version number for a file."""
    versions = get_file_versions(file_path)
    past_versions = [v for v in versions if v["version"] != "current"]
    
    if not past_versions:
        return 1
    
    highest_version = max(v["version"] for v in past_versions)
    return highest_version + 1

def create_file_backup(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Creates a backup of the file if it exists.
    
    Args:
        file_path: Path to the file to back up
    
    Returns:
        Dictionary with backup information or None if no backup was created
    """
    if not os.path.exists(file_path):
        return None
    
    versions_dir = ensure_version_dir(file_path)
    version_number = get_next_version_number(file_path)
    timestamp = int(time.time())
    
    backup_filename = f"v{version_number}_{timestamp}.backup"
    backup_path = os.path.join(versions_dir, backup_filename)
    
    try:
        shutil.copy2(file_path, backup_path)
        
        stats = os.stat(backup_path)
        
        return {
            "version": version_number,
            "timestamp": timestamp,
            "date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "size": stats.st_size,
            "size_human": f"{stats.st_size/1024:.1f}KB" if stats.st_size < 1048576 else f"{stats.st_size/1048576:.1f}MB",
            "path": backup_path
        }
    except Exception as e:
        logger.error(f"Error creating backup for {file_path}: {str(e)}")
        return None


@mcp.tool()
async def create_directory(path: str, parents: bool = True, exist_ok: bool = True) -> Dict[str, Any]:
    '''
    Creates a new directory at the specified path.
    
    Args:
        path: Path where the directory should be created
        parents: If True, create parent directories as needed (default: True)
        exist_ok: If True, don't raise error if directory already exists (default: True)
    
    Returns:
        Dictionary with operation result
    '''
    logger.info(f"Creating directory: {path}")
    
    try:
        Path(path).mkdir(parents=parents, exist_ok=exist_ok)
        logger.info(f"Successfully created directory: {path}")
        return {
            "success": True,
            "message": f"Directory created: {path}",
            "path": str(Path(path).absolute())
        }
    except Exception as e:
        logger.error(f"Failed to create directory: {str(e)}")
        return {
            "success": False,
            "error": "Failed to create directory",
            "reason": str(e)
        }

@mcp.tool()
async def move_file(source: str, destination: str, overwrite: bool = False, create_backup: bool = True) -> Dict[str, Any]:
    '''
    Moves a file or directory from source to destination.
    
    Args:
        source: Path to the file or directory to move
        destination: Destination path (can be a directory or new filename)
        overwrite: If True, overwrite destination if it exists (default: False)
        create_backup: If True, create backup of destination if overwriting (default: True)
    
    Returns:
        Dictionary with operation result
    '''
    logger.info(f"Moving from {source} to {destination}")
    
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            return {
                "success": False,
                "error": "Source does not exist",
                "source": str(source_path)
            }
        
        # If destination is a directory and exists, construct full path
        if dest_path.is_dir():
            dest_path = dest_path / source_path.name
        
        # Check if destination already exists
        if dest_path.exists():
            if not overwrite:
                return {
                    "success": False,
                    "error": "Destination already exists",
                    "destination": str(dest_path),
                    "hint": "Set overwrite=True to replace existing file"
                }
            
            # Create backup if requested and destination is a file
            if create_backup and dest_path.is_file():
                backup_info = create_file_backup(str(dest_path))
                if not backup_info:
                    logger.warning("Failed to create backup, but continuing with move")

        
        result = {
            "success": True,
            "message": f"Moved successfully",
            "source": str(source_path),
            "destination": str(dest_path.absolute())
        }
        
        # Add backup info if created
        if dest_path.exists() and create_backup and dest_path.is_file():
            if 'backup_info' in locals() and backup_info:
                result["backup_created"] = True
                result["backup_info"] = backup_info
        
        shutil.move(str(source_path), str(dest_path))
        logger.info(f"Successfully moved {source} to {dest_path}")
        
        return result
    except Exception as e:
        logger.error(f"Failed to move file: {str(e)}")
        return {
            "success": False,
            "error": "Failed to move file",
            "reason": str(e)
        }

@mcp.tool()
async def copy_file(source: str, destination: str, overwrite: bool = False) -> Dict[str, Any]:
    '''
    Copies a file or directory from source to destination.
    
    Args:
        source: Path to the file or directory to copy
        destination: Destination path (can be a directory or new filename)
        overwrite: If True, overwrite destination if it exists (default: False)
    
    Returns:
        Dictionary with operation result
    '''
    logger.info(f"Copying from {source} to {destination}")
    
    try:
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            return {
                "success": False,
                "error": "Source does not exist",
                "source": str(source_path)
            }
        
        # If destination is a directory and exists, construct full path
        if dest_path.is_dir():
            dest_path = dest_path / source_path.name
        
        # Check if destination already exists
        if dest_path.exists() and not overwrite:
            return {
                "success": False,
                "error": "Destination already exists",
                "destination": str(dest_path),
                "hint": "Set overwrite=True to replace existing file"
            }
        
        if source_path.is_file():
            shutil.copy2(str(source_path), str(dest_path))
        else:
            shutil.copytree(str(source_path), str(dest_path), dirs_exist_ok=overwrite)
        
        logger.info(f"Successfully copied {source} to {dest_path}")
        
        return {
            "success": True,
            "message": f"Copied successfully",
            "source": str(source_path),
            "destination": str(dest_path.absolute())
        }
    except Exception as e:
        logger.error(f"Failed to copy: {str(e)}")
        return {
            "success": False,
            "error": "Failed to copy",
            "reason": str(e)
        }

@mcp.tool()
async def delete_file(path: str, confirm: bool = False, create_backup: bool = True) -> Dict[str, Any]:
    '''
    Deletes a file or directory.
    
    Args:
        path: Path to the file or directory to delete
        confirm: Must be True to confirm deletion (safety check)
        create_backup: If True, create backup before deleting files (default: True)
    
    Returns:
        Dictionary with operation result
    '''
    logger.info(f"Delete request for: {path}")
    
    if not confirm:
        return {
            "success": False,
            "error": "Deletion not confirmed",
            "hint": "Set confirm=True to delete the file/directory"
        }
    
    try:
        target_path = Path(path)
        
        if not target_path.exists():
            return {
                "success": False,
                "error": "Path does not exist",
                "path": str(target_path)
            }
        
        # Store type before deletion
        is_file = target_path.is_file()
        
        # Create backup if it's a file and backup is requested
        backup_info = None
        if is_file and create_backup:
            backup_info = create_file_backup(str(target_path))
            if not backup_info:
                logger.warning("Failed to create backup, but continuing with deletion")

        
        # Delete the file or directory
        if is_file:
            target_path.unlink()
            logger.info(f"Successfully deleted file: {path}")
        else:
            shutil.rmtree(str(target_path))
            logger.info(f"Successfully deleted directory: {path}")
        
        result = {
            "success": True,
            "message": f"Deleted successfully",
            "path": str(target_path),
            "type": "file" if is_file else "directory"
        }
        
        # Add backup info if created
        if backup_info:
            result["backup_created"] = True
            result["backup_info"] = backup_info
            result["recovery_hint"] = f"File backed up to: {backup_info['path']}"
        
        return result
    except Exception as e:
        logger.error(f"Failed to delete: {str(e)}")
        return {
            "success": False,
            "error": "Failed to delete",
            "reason": str(e)
        }

@mcp.tool()
async def rename_file(old_path: str, new_name: str, create_backup: bool = True) -> Dict[str, Any]:
    '''
    Renames a file or directory.
    
    Args:
        old_path: Current path of the file or directory
        new_name: New name (not full path, just the name)
        create_backup: If True, create backup before renaming files (default: True)
    
    Returns:
        Dictionary with operation result
    '''
    logger.info(f"Renaming {old_path} to {new_name}")
    
    try:
        old_path_obj = Path(old_path)
        
        if not old_path_obj.exists():
            return {
                "success": False,
                "error": "Path does not exist",
                "path": str(old_path_obj)
            }
        
        # Construct new path in same directory
        new_path = old_path_obj.parent / new_name
        
        if new_path.exists():
            return {
                "success": False,
                "error": "A file or directory with the new name already exists",
                "new_path": str(new_path)
            }
        
        # Create backup if it's a file and backup is requested
        backup_info = None
        if old_path_obj.is_file() and create_backup:
            backup_info = create_file_backup(str(old_path_obj))
            if not backup_info:
                logger.warning("Failed to create backup, but continuing with rename")

        
        old_path_obj.rename(new_path)
        logger.info(f"Successfully renamed to: {new_path}")
        
        result = {
            "success": True,
            "message": "Renamed successfully",
            "old_path": str(old_path_obj),
            "new_path": str(new_path.absolute())
        }
        
        # Add backup info if created
        if backup_info:
            result["backup_created"] = True
            result["backup_info"] = backup_info
        
        return result
    except Exception as e:
        logger.error(f"Failed to rename: {str(e)}")
        return {
            "success": False,
            "error": "Failed to rename",
            "reason": str(e)
        }

if __name__ == "__main__":
    logger.info("Starting File Manager MCP server")
    mcp.run(transport='stdio')
