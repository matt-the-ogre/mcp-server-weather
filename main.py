#!/usr/bin/env python3
"""
Entry point for the MCP weather server.
Runs the server with streamable HTTP transport for web deployment.
"""
import sys
import os
import logging

# Add current directory to path to ensure server module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import mcp
import uvicorn
from datetime import datetime, timezone

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get the ASGI app for streamable HTTP transport and run with uvicorn
    app = mcp.streamable_http_app()

    # Add health check endpoint for monitoring (e.g., Uptime Kuma)
    @app.get("/health")
    async def health_check():
        """Simple health check endpoint that returns server status."""
        logger.info("Health check requested")
        return {
            "status": "healthy",
            "service": "mcp-server-weather",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mcp_endpoint": "/mcp"
        }

    @app.get("/")
    async def root():
        """Root endpoint with server information."""
        return {
            "service": "mcp-server-weather",
            "version": "1.0.0",
            "endpoints": {
                "mcp": "/mcp",
                "health": "/health"
            },
            "description": "MCP server providing weather data from Open-Meteo API"
        }

    logger.info("Starting MCP weather server on port 80")
    uvicorn.run(app, host="0.0.0.0", port=80)