#!/usr/bin/env python3
"""
Entry point for the MCP weather server.
Runs the server with streamable HTTP transport for web deployment.
"""
import sys
import os
import logging
import json

# Add current directory to path to ensure server module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import mcp
import uvicorn
from datetime import datetime, timezone
from starlette.routing import Route
from starlette.responses import JSONResponse
from starlette.applications import Starlette

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def health_check(request):
    """Simple health check endpoint that returns server status."""
    logger.info("Health check requested")
    return JSONResponse({
        "status": "healthy",
        "service": "mcp-server-weather",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mcp_endpoint": "/mcp"
    })

async def root(request):
    """Root endpoint with server information."""
    return JSONResponse({
        "service": "mcp-server-weather",
        "version": "1.0.0",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health"
        },
        "description": "MCP server providing weather data from Open-Meteo API"
    })

if __name__ == "__main__":
    # Get the base MCP app
    mcp_app = mcp.streamable_http_app()

    # Create a new Starlette app with custom routes and mount the MCP app
    routes = [
        Route("/health", health_check),
        Route("/", root),
    ]

    # Create new app with our routes plus the MCP app mounted
    from starlette.routing import Mount
    app = Starlette(routes=routes + [Mount("/mcp", app=mcp_app)])

    logger.info("Starting MCP weather server on port 80")
    uvicorn.run(app, host="0.0.0.0", port=80)