from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import httpx
from typing import Any
import json
import re
import uvicorn

app = FastAPI(title="Weather API", version="1.0.0")

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

class WeatherRequest(BaseModel):
    latitude: float = Field(default=49.0, ge=-90, le=90)
    longitude: float = Field(default=-122.05, ge=-180, le=180)

class HistoricalWeatherRequest(BaseModel):
    latitude: float = Field(default=49.0, ge=-90, le=90)
    longitude: float = Field(default=-122.05, ge=-180, le=180)
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$')

@app.get("/")
async def root():
    return {
        "message": "Weather API",
        "endpoints": {
            "/health": "Health check",
            "/current": "Get current weather (params: latitude, longitude)",
            "/forecast": "Get weather forecast (params: latitude, longitude)",
            "/historical": "Get historical weather (params: latitude, longitude, start_date, end_date)"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/current")
async def get_current_weather(latitude: float = 49.0, longitude: float = -122.05):
    """Get current weather for a location."""
    if not (-90 <= latitude <= 90):
        raise HTTPException(status_code=400, detail="Invalid latitude. Must be between -90 and 90 degrees.")
    if not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid longitude. Must be between -180 and 180 degrees.")

    current_params = "temperature_2m,is_day,showers,cloud_cover,wind_speed_10m,wind_direction_10m,pressure_msl,snowfall,precipitation,relative_humidity_2m,apparent_temperature,rain,weather_code,surface_pressure,wind_gusts_10m"
    url = f"{OPENMETEO_API_BASE}/forecast?latitude={latitude}&longitude={longitude}&current={current_params}"
    data = await make_openmeteo_request(url)

    if not data:
        raise HTTPException(status_code=503, detail="Unable to fetch current weather data for this location.")

    return data

@app.get("/forecast")
async def get_forecast(latitude: float = 49.0, longitude: float = -122.05):
    """Get weather forecast for a location."""
    if not (-90 <= latitude <= 90):
        raise HTTPException(status_code=400, detail="Invalid latitude. Must be between -90 and 90 degrees.")
    if not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid longitude. Must be between -180 and 180 degrees.")

    url = f"{OPENMETEO_API_BASE}/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,precipitation,weathercode&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto"
    data = await make_openmeteo_request(url)

    if not data:
        raise HTTPException(status_code=503, detail="Unable to fetch forecast data for this location.")

    return data

@app.get("/historical")
async def get_historical_weather(
    latitude: float = 49.0,
    longitude: float = -122.05,
    start_date: str = None,
    end_date: str = None
):
    """Get historical weather data for a location and date range."""
    if not (-90 <= latitude <= 90):
        raise HTTPException(status_code=400, detail="Invalid latitude. Must be between -90 and 90 degrees.")
    if not (-180 <= longitude <= 180):
        raise HTTPException(status_code=400, detail="Invalid longitude. Must be between -180 and 180 degrees.")

    if not start_date or not end_date:
        raise HTTPException(status_code=400, detail="Please provide both start_date and end_date in YYYY-MM-DD format.")

    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(date_pattern, start_date) or not re.match(date_pattern, end_date):
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format.")

    parameters = "daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum,rain_sum,snowfall_sum,wind_speed_10m_max,wind_gusts_10m_max&hourly=temperature_2m,relative_humidity_2m,precipitation,rain,snowfall&timezone=auto"
    url = f"{OPENMETEO_ARCHIVE_API_BASE}/era5?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&{parameters}"

    data = await make_openmeteo_request(url)

    if not data:
        raise HTTPException(status_code=503, detail="Unable to fetch historical weather data for this location and date range.")

    return data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)