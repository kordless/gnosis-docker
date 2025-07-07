#!/usr/bin/env python3
"""
Example MCP Tool - Simple utility functions for demonstration
This shows basic MCP server patterns and can be used as a template.
"""

import sys
import os
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

__version__ = "1.0.0"

# Import MCP server library
try:
    from mcp.server.fastmcp import FastMCP
    # Initialize the MCP server
    mcp = FastMCP("Example Utilities")
except ImportError:
    print("Error: MCP library not installed. Please run: pip install mcp", file=sys.stderr)
    sys.exit(1)

@mcp.tool()
async def echo_message(message: str, repeat: int = 1) -> str:
    """
    Echo a message back, optionally repeating it multiple times.
    
    Args:
        message: The message to echo
        repeat: Number of times to repeat the message (default: 1)
    
    Returns:
        The echoed message(s)
    """
    if repeat <= 0:
        return "Error: repeat count must be positive"
    
    if repeat == 1:
        return f"Echo: {message}"
    else:
        return f"Echo ({repeat}x): " + " | ".join([message] * repeat)

@mcp.tool()
async def get_timestamp(format_type: str = "iso") -> str:
    """
    Get current timestamp in various formats.
    
    Args:
        format_type: Format type - "iso", "unix", "human", "utc"
    
    Returns:
        Formatted timestamp string
    """
    now = datetime.now()
    
    if format_type == "iso":
        return now.isoformat()
    elif format_type == "unix":
        return str(int(now.timestamp()))
    elif format_type == "human":
        return now.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "utc":
        return datetime.utcnow().isoformat() + "Z"
    else:
        return f"Error: Unknown format type '{format_type}'. Use: iso, unix, human, utc"

@mcp.tool()
async def calculate_basic(operation: str, a: float, b: float) -> Dict[str, Any]:
    """
    Perform basic mathematical operations.
    
    Args:
        operation: Operation type - "add", "subtract", "multiply", "divide", "power"
        a: First number
        b: Second number
    
    Returns:
        Dictionary with calculation result and metadata
    """
    try:
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return {"error": "Division by zero", "operation": operation, "operands": [a, b]}
            result = a / b
        elif operation == "power":
            result = a ** b
        else:
            return {"error": f"Unknown operation '{operation}'", "valid_operations": ["add", "subtract", "multiply", "divide", "power"]}
        
        return {
            "result": result,
            "operation": operation,
            "operands": [a, b],
            "expression": f"{a} {operation} {b} = {result}",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e), "operation": operation, "operands": [a, b]}

@mcp.tool()
async def system_info() -> Dict[str, Any]:
    """
    Get basic system information.
    
    Returns:
        Dictionary with system information
    """
    import platform
    
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "current_directory": os.getcwd(),
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def text_analysis(text: str) -> Dict[str, Any]:
    """
    Analyze text and return basic statistics.
    
    Args:
        text: Text to analyze
    
    Returns:
        Dictionary with text analysis results
    """
    if not text:
        return {"error": "No text provided"}
    
    words = text.split()
    sentences = text.split('.')
    paragraphs = text.split('\n\n')
    
    # Character frequency
    char_freq = {}
    for char in text.lower():
        if char.isalpha():
            char_freq[char] = char_freq.get(char, 0) + 1
    
    # Most common words (simple approach)
    word_freq = {}
    for word in words:
        clean_word = word.lower().strip('.,!?;:"()[]{}')
        if clean_word:
            word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
    
    # Sort by frequency
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "paragraph_count": len([p for p in paragraphs if p.strip()]),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "most_common_words": top_words,
        "character_frequency": dict(sorted(char_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
        "analysis_timestamp": datetime.now().isoformat()
    }

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """
    Perform a health check of the MCP server.
    
    Returns:
        Dictionary with health status
    """
    return {
        "status": "healthy",
        "server_name": "Example Utilities MCP Server",
        "version": __version__,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time(),
        "available_tools": [
            "echo_message",
            "get_timestamp", 
            "calculate_basic",
            "system_info",
            "text_analysis",
            "health_check"
        ]
    }

if __name__ == "__main__":
    try:
        print(f"Starting Example Utilities MCP server v{__version__}", file=sys.stderr)
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down Example Utilities MCP server...", file=sys.stderr)
    except Exception as e:
        print(f"Error running MCP server: {e}", file=sys.stderr)
        sys.exit(1)
