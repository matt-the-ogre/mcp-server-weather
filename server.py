from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import json
import re

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
OPENMETEO_API_BASE = "https://api.open-meteo.com/v1"
OPENMETEO_ARCHIVE_API_BASE = "https://archive-api.open-meteo.com/v1"
USER_AGENT = "weather-app/1.0"

async def make_openmeteo_request(url: str) -> dict[str, Any] | None:
    """Make a request to the Open-Meteo API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Network error occurred: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Unexpected error occurred: {e}")
            return None

@mcp.tool()
async def get_forecast(latitude: float = 49.0, longitude: float = -122.05) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return "Invalid latitude. Must be between -90 and 90 degrees."
    if not (-180 <= longitude <= 180):
        return "Invalid longitude. Must be between -180 and 180 degrees."
    
    url = f"{OPENMETEO_API_BASE}/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,precipitation,weathercode&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto"
    data = await make_openmeteo_request(url)

    if not data:
        return "Unable to fetch forecast data for this location."

    # Format the daily forecast into a readable format
    daily = data["daily"]
    forecasts = []
    for i in range(len(daily["time"])):
        forecast = f"""
Date: {daily['time'][i]}
Max Temperature: {daily['temperature_2m_max'][i]}°C
Min Temperature: {daily['temperature_2m_min'][i]}°C
Precipitation: {daily['precipitation_sum'][i]} mm
Weather Code: {daily['weathercode'][i]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def get_current_weather(latitude: float = 49.0, longitude: float = -122.05) -> str:
    """Get current weather for a location.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return "Invalid latitude. Must be between -90 and 90 degrees."
    if not (-180 <= longitude <= 180):
        return "Invalid longitude. Must be between -180 and 180 degrees."
    
    # Build URL with comprehensive current weather parameters
    current_params = "temperature_2m,is_day,showers,cloud_cover,wind_speed_10m,wind_direction_10m,pressure_msl,snowfall,precipitation,relative_humidity_2m,apparent_temperature,rain,weather_code,surface_pressure,wind_gusts_10m"
    url = f"{OPENMETEO_API_BASE}/forecast?latitude={latitude}&longitude={longitude}&current={current_params}"
    data = await make_openmeteo_request(url)

    if not data:
        return "Unable to fetch current weather data for this location."

    return json.dumps(data)

@mcp.tool()
async def get_historical_weather(latitude: float = 49.0, longitude: float = -122.05, start_date: str = "", end_date: str = "") -> str:
    """Get historical weather data for a location and date range.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        parameters: Comma-separated list of weather parameters (default: temperature_2m)
                   Available: temperature_2m, relative_humidity_2m, precipitation, weather_code, pressure_msl, etc.
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return "Invalid latitude. Must be between -90 and 90 degrees."
    if not (-180 <= longitude <= 180):
        return "Invalid longitude. Must be between -180 and 180 degrees."
    
    # Check if dates are provided
    if not start_date or not end_date:
        return "Please provide both start_date and end_date in YYYY-MM-DD format."
    
    # Validate date format (basic check)
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(date_pattern, start_date) or not re.match(date_pattern, end_date):
        return "Invalid date format. Use YYYY-MM-DD format."
    
    # Build URL for ERA5 historical data with comprehensive weather parameters
    parameters = "daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,rain_sum,snowfall_sum,wind_speed_10m_max,wind_gusts_10m_max&hourly=temperature_2m,relative_humidity_2m,precipitation,rain,snowfall&timezone=auto"
    url = f"{OPENMETEO_ARCHIVE_API_BASE}/era5?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&{parameters}"
    
    data = await make_openmeteo_request(url)

    if not data:
        return "Unable to fetch historical weather data for this location and date range."

    # Format response for better readability
    if "hourly" in data and "time" in data["hourly"]:
        hourly_data = data["hourly"]
        total_hours = len(hourly_data["time"])
        # Extract parameter names for display
        available_params = ["temperature_2m", "relative_humidity_2m", "precipitation", "rain", "snowfall"]
        
        summary = f"Historical weather data from {start_date} to {end_date}\n"
        summary += f"Location: {latitude}, {longitude}\n"
        summary += f"Total data points: {total_hours} hours\n\n"
        
        # Show first few data points as example
        summary += "Sample data (first 5 hours):\n"
        for i in range(min(5, total_hours)):
            summary += f"Time: {hourly_data['time'][i]}\n"
            for param in available_params:
                if param in hourly_data:
                    summary += f"  {param}: {hourly_data[param][i]}\n"
            summary += "\n"
        
        if total_hours > 5:
            summary += f"... and {total_hours - 5} more data points\n\n"
        
        summary += "Full data in JSON format:\n"
        summary += json.dumps(data, indent=2)
        
        return summary
    
    return json.dumps(data, indent=2)

if __name__ == "__main__":
    # Initialize and run the server
    import sys
    # Check if running with SSE transport (for web deployment)
    if len(sys.argv) > 1 and sys.argv[1] == '--sse':
        mcp.run(transport='sse', host='0.0.0.0', port=80)
    else:
        # Default to stdio for local MCP usage
        mcp.run(transport='stdio')