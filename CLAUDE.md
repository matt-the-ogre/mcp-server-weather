# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server that provides comprehensive weather data functionality. It's built using the FastMCP framework and integrates with both the Open-Meteo API for current/forecast data and the Open-Meteo Archive API for historical weather data.

## Key Architecture

- **server.py**: Main MCP server implementation using FastMCP framework
  - Defines three weather tools accessible via MCP protocol
  - Uses Open-Meteo APIs for weather data (no API key required)
  - Includes robust error handling and input validation
  - Supports both stdio (local) and HTTP (remote) transports
  - Configurable via environment variables: PORT (default: 8000), HOST (default: 0.0.0.0)
- **main.py**: Production entry point for HTTP deployment
  - Runs the MCP server with streamable HTTP transport
  - Uses FastMCP's built-in HTTP server (uvicorn)
  - Exposes MCP protocol at `/mcp` endpoint (FastMCP default)
  - Defaults to port 80 for CapRover deployment (configurable via PORT env var)

## Development Commands

Since this uses `uv` for dependency management:

```bash
# Install dependencies
uv sync

# Run the MCP server locally for development/testing (stdio transport)
mcp dev server.py

# Or run directly with Python (stdio transport)
python server.py

# Run the HTTP server locally for testing remote connections
PORT=8000 python main.py
# Server will be available at http://localhost:8000/mcp

# Or on port 80 (requires sudo on Linux, default for main.py)
python main.py
# Server will be available at http://localhost:80/mcp
```

## Deployment

Deployed to CapRover at https://mcp-weather.mattmanuel.ca/mcp

```bash
# Deploy using the provided script (sources .env for credentials)
./deploy.sh

# Or manually with environment variables
source .env && caprover deploy
```

The deployment uses:
- **Dockerfile**: Python 3.13 + uv for dependencies
- **captain-definition**: CapRover deployment config
- **.env**: CapRover credentials (not committed to git)

## MCP Tools Available

The server exposes three weather tools through the MCP protocol:

1. **`get_current_weather(latitude=49.0, longitude=-122.05)`**
   - Gets current weather conditions for a location
   - Returns comprehensive current weather data as JSON
   - Defaults to Vancouver, BC coordinates

2. **`get_forecast(latitude=49.0, longitude=-122.05)`**
   - Gets weather forecast for a location
   - Returns formatted daily forecast with max/min temps, precipitation, weather codes
   - Defaults to Vancouver, BC coordinates

3. **`get_historical_weather(latitude=49.0, longitude=-122.05, start_date, end_date)`**
   - Gets historical weather data from Open-Meteo Archive API
   - Requires start_date and end_date in YYYY-MM-DD format
   - Returns both daily and hourly historical data
   - Includes sample data points plus full JSON response
   - Defaults to Vancouver, BC coordinates

## Input Validation

All tools include comprehensive validation:
- Latitude: Must be between -90 and 90 degrees
- Longitude: Must be between -180 and 180 degrees
- Dates: Must be in YYYY-MM-DD format (for historical data)
- Proper error messages for invalid inputs

## Error Handling

- Network errors are caught and logged with specific error types
- HTTP status errors are handled separately
- API request failures return helpful error messages
- 30-second timeout on all API requests

## Dependencies

- `httpx`: For async HTTP requests to weather APIs
- `mcp[cli]`: Official MCP Python SDK with FastMCP framework
- `uvicorn`: ASGI server for HTTP transport
- `fastapi`: Required by mcp[cli] for HTTP transport
- `re`: For date format validation
- Python 3.13+ required

## API Integration

- **Current/Forecast**: Open-Meteo API (https://api.open-meteo.com/v1)
- **Historical**: Open-Meteo Archive API (https://archive-api.open-meteo.com/v1)
- Both APIs require no authentication and provide free weather data