#!/usr/bin/env python3
"""
Entry point for the MCP weather server.
Runs the server with HTTP transport for web deployment.
"""
import sys
import os

# Add current directory to path to ensure server module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import mcp

if __name__ == "__main__":
    # Run with HTTP transport on port 80 for CapRover deployment
    mcp.run(transport="http", port=80)