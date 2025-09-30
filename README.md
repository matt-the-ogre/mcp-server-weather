# mcp-server-weather

A comprehensive MCP (Model Context Protocol) server that provides weather data functionality through three powerful tools. Built with FastMCP and integrating with Open-Meteo APIs for current, forecast, and historical weather data.

## Features

- **Current Weather**: Get real-time weather conditions for any location
- **Weather Forecast**: Retrieve daily weather forecasts with temperature and precipitation data
- **Historical Weather**: Access historical weather data from the Open-Meteo Archive
- **Default Location**: All tools default to Vancouver, BC (49.0, -122.05) if no coordinates provided
- **Input Validation**: Comprehensive validation for coordinates and date formats
- **Error Handling**: Robust error handling with specific error messages

## Installation

This project uses `uv` for dependency management:

```bash
# install uv
brew install uv
```

```bash
# Install dependencies
uv sync
```

## Usage

### Running the MCP Server

**Local Development (stdio transport):**
```bash
# With MCP Inspector
mcp dev server.py

# Or directly
python server.py
```

**Remote/Production (HTTP transport):**
```bash
# Run HTTP server locally for testing
python main.py
# Server available at http://localhost:80/mcp

# Deploy to CapRover
./deploy.sh
```

### Deployed Server

The server is deployed at: **https://mcp-weather.mattmanuel.ca/mcp**

Connect via Claude Desktop by adding to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "weather": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp-weather.mattmanuel.ca/mcp"]
    }
  }
}
```

### Available Tools

#### 1. get_current_weather(latitude, longitude)
Get current weather conditions for a location.

**Parameters:**
- `latitude` (float, optional): Latitude (-90 to 90). Default: 49.0 (Vancouver, BC)
- `longitude` (float, optional): Longitude (-180 to 180). Default: -122.05 (Vancouver, BC)

**Returns:** JSON with comprehensive current weather data including temperature, humidity, wind, precipitation, etc.

#### 2. get_forecast(latitude, longitude)
Get weather forecast for a location.

**Parameters:**
- `latitude` (float, optional): Latitude (-90 to 90). Default: 49.0 (Vancouver, BC)
- `longitude` (float, optional): Longitude (-180 to 180). Default: -122.05 (Vancouver, BC)

**Returns:** Formatted daily forecast with max/min temperatures, precipitation, and weather codes.

#### 3. get_historical_weather(latitude, longitude, start_date, end_date)
Get historical weather data for a location and date range.

**Parameters:**
- `latitude` (float, optional): Latitude (-90 to 90). Default: 49.0 (Vancouver, BC)
- `longitude` (float, optional): Longitude (-180 to 180). Default: -122.05 (Vancouver, BC)
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format

**Returns:** Historical weather data with both daily and hourly information, including sample data points and full JSON response.

## Example Usage

Using the MCP Inspector, you can test the tools with:

```javascript
// Current weather for Vancouver (default)
get_current_weather()

// Current weather for New York City
get_current_weather(40.7128, -74.0060)

// Forecast for London
get_forecast(51.5074, -0.1278)

// Historical weather for Paris in January 2023
get_historical_weather(48.8566, 2.3522, "2023-01-01", "2023-01-31")
```

## API Integration

This server integrates with two Open-Meteo APIs:

- **Open-Meteo API** (https://api.open-meteo.com/v1): Current weather and forecasts
- **Open-Meteo Archive API** (https://archive-api.open-meteo.com/v1): Historical weather data

Both APIs are free and require no authentication.

## Dependencies

- Python 3.13+
- `httpx`: Async HTTP client for API requests
- `mcp[cli]`: Official MCP Python SDK with FastMCP framework
- `uvicorn`: ASGI server for HTTP transport
- `fastapi`: Required by mcp[cli] for HTTP transport
- `re`: Regular expressions for date validation

## Error Handling

The server includes comprehensive error handling:

- **Input Validation**: Validates coordinate ranges and date formats
- **Network Errors**: Handles connection issues with descriptive messages
- **HTTP Errors**: Catches and reports API response errors
- **Timeout Protection**: 30-second timeout on all API requests

## Architecture

- **server.py**: Core MCP server with tool definitions
- **main.py**: Production entry point using streamable HTTP transport
- **Dockerfile**: Container configuration for CapRover deployment
- **captain-definition**: CapRover deployment settings
- **deploy.sh**: Deployment script with environment variable loading

## Deployment

Deployed to CapRover using Docker containers. The deployment process:

1. Sources environment variables from `.env` (CapRover credentials)
2. Builds Docker image with Python 3.13 and uv
3. Deploys to CapRover instance
4. Exposes MCP protocol via streamable HTTP at `/mcp` endpoint

## Development

This project was developed as part of a LinkedIn Learning course on MCP Servers and demonstrates best practices for building robust MCP tools with proper error handling, user-friendly interfaces, and production deployment via HTTP transport.
