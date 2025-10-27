from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import json
import re
from datetime import datetime, timezone
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastMCP server with configuration
# Use environment variable for port, default to 8000
import os
PORT = int(os.getenv('PORT', '8000'))
HOST = os.getenv('HOST', '0.0.0.0')

mcp = FastMCP("weather", host=HOST, port=PORT)

# Constants
OPENMETEO_API_BASE = "https://api.open-meteo.com/v1"
OPENMETEO_ARCHIVE_API_BASE = "https://archive-api.open-meteo.com/v1"
USER_AGENT = "weather-app/1.0"

def get_weather_description(code: int) -> str:
    """Map WMO weather code to human-readable description."""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Drizzle: Light intensity",
        53: "Drizzle: Moderate intensity",
        55: "Drizzle: Dense intensity",
        56: "Freezing drizzle: Light intensity",
        57: "Freezing drizzle: Dense intensity",
        61: "Rain: Slight intensity",
        63: "Rain: Moderate intensity",
        65: "Rain: Heavy intensity",
        66: "Freezing rain: Light intensity",
        67: "Freezing rain: Heavy intensity",
        71: "Snow fall: Slight intensity",
        73: "Snow fall: Moderate intensity",
        75: "Snow fall: Heavy intensity",
        77: "Snow grains",
        80: "Rain showers: Slight intensity",
        81: "Rain showers: Moderate intensity",
        82: "Rain showers: Violent intensity",
        85: "Snow showers: Slight intensity",
        86: "Snow showers: Heavy intensity",
        95: "Thunderstorm: Slight or moderate",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(code, f"Unknown weather code: {code}")

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
            logger.error(f"Network error occurred: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            return None

@mcp.tool()
async def get_forecast(latitude: float = 49.0, longitude: float = -122.05) -> dict[str, Any]:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return {
            "error": {
                "type": "ValidationError",
                "message": "Invalid latitude. Must be between -90 and 90 degrees.",
                "details": {
                    "parameter": "latitude",
                    "provided_value": latitude,
                    "valid_range": [-90, 90]
                }
            }
        }
    if not (-180 <= longitude <= 180):
        return {
            "error": {
                "type": "ValidationError",
                "message": "Invalid longitude. Must be between -180 and 180 degrees.",
                "details": {
                    "parameter": "longitude",
                    "provided_value": longitude,
                    "valid_range": [-180, 180]
                }
            }
        }

    # Request comprehensive forecast data including additional fields
    daily_params = "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weathercode,wind_speed_10m_max,wind_direction_10m_dominant,uv_index_max,sunrise,sunset"
    hourly_params = "temperature_2m,precipitation,precipitation_probability,weathercode,wind_speed_10m,uv_index"
    url = f"{OPENMETEO_API_BASE}/forecast?latitude={latitude}&longitude={longitude}&hourly={hourly_params}&daily={daily_params}&timezone=auto"
    data = await make_openmeteo_request(url)

    if not data:
        return {
            "error": {
                "type": "APIError",
                "message": "Unable to fetch forecast data for this location.",
                "details": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
        }

    # Add weather descriptions to daily forecast
    if "daily" in data and "weathercode" in data["daily"]:
        weather_descriptions = [get_weather_description(code) for code in data["daily"]["weathercode"]]
        data["daily"]["weather_description"] = weather_descriptions

    # Add weather descriptions to hourly forecast
    if "hourly" in data and "weathercode" in data["hourly"]:
        weather_descriptions = [get_weather_description(code) for code in data["hourly"]["weathercode"]]
        data["hourly"]["weather_description"] = weather_descriptions

    # Add timestamp for when the response was generated
    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    return data

@mcp.tool()
async def get_current_weather(latitude: float = 49.0, longitude: float = -122.05) -> dict[str, Any]:
    """Get current weather for a location.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return {
            "error": {
                "type": "ValidationError",
                "message": "Invalid latitude. Must be between -90 and 90 degrees.",
                "details": {
                    "parameter": "latitude",
                    "provided_value": latitude,
                    "valid_range": [-90, 90]
                }
            }
        }
    if not (-180 <= longitude <= 180):
        return {
            "error": {
                "type": "ValidationError",
                "message": "Invalid longitude. Must be between -180 and 180 degrees.",
                "details": {
                    "parameter": "longitude",
                    "provided_value": longitude,
                    "valid_range": [-180, 180]
                }
            }
        }

    # Build URL with comprehensive current weather parameters
    current_params = "temperature_2m,is_day,showers,cloud_cover,wind_speed_10m,wind_direction_10m,pressure_msl,snowfall,precipitation,relative_humidity_2m,apparent_temperature,rain,weather_code,surface_pressure,wind_gusts_10m"
    url = f"{OPENMETEO_API_BASE}/forecast?latitude={latitude}&longitude={longitude}&current={current_params}&timezone=auto"
    data = await make_openmeteo_request(url)

    if not data:
        return {
            "error": {
                "type": "APIError",
                "message": "Unable to fetch current weather data for this location.",
                "details": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            }
        }

    # Enhance response structure with organized data and weather description
    if "current" in data and "weather_code" in data["current"]:
        weather_code = data["current"]["weather_code"]
        data["current"]["weather_description"] = get_weather_description(weather_code)

    # Add timestamp for when the response was generated
    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    return data

@mcp.tool()
async def get_historical_weather(latitude: float = 49.0, longitude: float = -122.05, start_date: str = "", end_date: str = "") -> dict[str, Any]:
    """Get historical weather data for a location and date range.

    Args:
        latitude: Latitude of the location (-90 to 90)
        longitude: Longitude of the location (-180 to 180)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    # Validate coordinates
    if not (-90 <= latitude <= 90):
        return {
            "error": {
                "type": "ValidationError",
                "message": "Invalid latitude. Must be between -90 and 90 degrees.",
                "details": {
                    "parameter": "latitude",
                    "provided_value": latitude,
                    "valid_range": [-90, 90]
                }
            }
        }
    if not (-180 <= longitude <= 180):
        return {
            "error": {
                "type": "ValidationError",
                "message": "Invalid longitude. Must be between -180 and 180 degrees.",
                "details": {
                    "parameter": "longitude",
                    "provided_value": longitude,
                    "valid_range": [-180, 180]
                }
            }
        }

    # Check if dates are provided
    if not start_date or not end_date:
        return {
            "error": {
                "type": "ValidationError",
                "message": "Please provide both start_date and end_date in YYYY-MM-DD format.",
                "details": {
                    "parameter": "start_date and end_date",
                    "provided_values": {
                        "start_date": start_date,
                        "end_date": end_date
                    }
                }
            }
        }

    # Validate date format (basic check)
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(date_pattern, start_date) or not re.match(date_pattern, end_date):
        return {
            "error": {
                "type": "ValidationError",
                "message": "Invalid date format. Use YYYY-MM-DD format.",
                "details": {
                    "parameter": "date format",
                    "provided_values": {
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "expected_format": "YYYY-MM-DD"
                }
            }
        }

    # Parse and validate date logic
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        today = datetime.now(timezone.utc).date()

        # Check if start_date is after end_date
        if start > end:
            return {
                "error": {
                    "type": "ValidationError",
                    "message": "start_date must be before or equal to end_date.",
                    "details": {
                        "start_date": start_date,
                        "end_date": end_date
                    }
                }
            }

        # Check if dates are in the future
        if start > today or end > today:
            return {
                "error": {
                    "type": "ValidationError",
                    "message": "Historical weather dates cannot be in the future.",
                    "details": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "today": today.isoformat()
                    }
                }
            }

        # Check if date range is reasonable (max 2 years)
        date_diff = (end - start).days
        if date_diff > 730:  # 2 years
            return {
                "error": {
                    "type": "ValidationError",
                    "message": "Date range exceeds maximum allowed period of 2 years (730 days).",
                    "details": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "requested_days": date_diff,
                        "max_days": 730
                    }
                }
            }

    except ValueError as e:
        return {
            "error": {
                "type": "ValidationError",
                "message": f"Invalid date values: {str(e)}",
                "details": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }

    # Build URL for ERA5 historical data with comprehensive weather parameters
    daily_params = "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,rain_sum,snowfall_sum,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,weather_code"
    hourly_params = "temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl"
    parameters = f"daily={daily_params}&hourly={hourly_params}&timezone=auto"
    url = f"{OPENMETEO_ARCHIVE_API_BASE}/era5?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&{parameters}"

    data = await make_openmeteo_request(url)

    if not data:
        return {
            "error": {
                "type": "APIError",
                "message": "Unable to fetch historical weather data for this location and date range.",
                "details": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }

    # Add weather descriptions to daily historical data
    if "daily" in data and "weather_code" in data["daily"]:
        weather_descriptions = [get_weather_description(code) for code in data["daily"]["weather_code"]]
        data["daily"]["weather_description"] = weather_descriptions

    # Add weather descriptions to hourly historical data
    if "hourly" in data and "weather_code" in data["hourly"]:
        weather_descriptions = [get_weather_description(code) for code in data["hourly"]["weather_code"]]
        data["hourly"]["weather_description"] = weather_descriptions

    # Add timestamp for when the response was generated
    data["generated_at"] = datetime.now(timezone.utc).isoformat()

    return data

if __name__ == "__main__":
    # Initialize and run the server
    import sys
    # Check if running with HTTP transport (for web deployment)
    if len(sys.argv) > 1 and sys.argv[1] == '--http':
        mcp.run(transport='streamable-http')
    else:
        # Default to stdio for local MCP usage
        mcp.run(transport='stdio')