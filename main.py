#!/usr/bin/env python3
"""
Entry point for the MCP weather server.
Runs the server with SSE transport for web deployment.
"""
import sys
import os

# Add current directory to path to ensure server module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import mcp

if __name__ == "__main__":
    # Run with SSE transport on port 80 for CapRover deployment
    mcp.run(transport="sse", host="0.0.0.0", port=80)