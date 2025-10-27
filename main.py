#!/usr/bin/env python3
"""
Entry point for the MCP weather server.
Runs the server with streamable HTTP transport for web deployment.

This file provides a production entry point that runs the MCP server
using the streamable-http transport for CapRover deployment.

Port and host are configured via environment variables:
- PORT: Server port (default: 80 for production)
- HOST: Server host (default: 0.0.0.0 for production to accept external connections)
"""
import sys
import os

# Set default port to 80 for production if not already set
if 'PORT' not in os.environ:
    os.environ['PORT'] = '80'

# Set default host to 0.0.0.0 for production if not already set
# This allows the server to accept external connections
if 'HOST' not in os.environ:
    os.environ['HOST'] = '0.0.0.0'

# Add current directory to path to ensure server module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import mcp

if __name__ == "__main__":
    # Run the MCP server with streamable-http transport
    # This will expose the MCP protocol at /mcp endpoint
    # Port and host are configured via environment variables in server.py
    mcp.run(transport='streamable-http')