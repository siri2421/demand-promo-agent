# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import logging
import os
import requests

from datetime import datetime
from collections import defaultdict

from fastmcp import FastMCP 

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP(name="WeatherServer")

@mcp.tool
def get_weather(latitude: float, longitude: float) -> str:
    """
    Gets the daily weather forecast for a given latitude and longitude from the NWS API.

    Args:
        latitude: The latitude of the location.
        longitude: The longitude of the location.

    Returns:
        A string containing the weather details for multiple days, or an error message.
    """
    # NWS API requires a User-Agent header.
    # See: https://www.weather.gov/documentation/services-web-api
    headers = {"User-Agent": "MyWeatherMCP/1.0 (dbeanish@google.com)"}

    # 1. Get the API endpoints for the grid area for the given coordinates.
    points_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    try:
        points_response = requests.get(points_url, headers=headers)
        points_response.raise_for_status()
        points_data = points_response.json().get("properties", {})
        forecast_url = points_data.get("forecast")
        hourly_forecast_url = points_data.get("forecastHourly")
        if not forecast_url or not hourly_forecast_url:
            return "Could not retrieve forecast URLs from NWS API."
    except requests.exceptions.RequestException as e:
        return f"Error contacting NWS API for points: {e}"
    except (ValueError, KeyError):
        return "Error parsing NWS points response. Are the coordinates valid?"

    # 2. Get hourly forecast data for High/Low temperatures.
    try:
        hourly_response = requests.get(hourly_forecast_url, headers=headers)
        hourly_response.raise_for_status()
        hourly_periods = hourly_response.json().get("properties", {}).get("periods", [])
        if not hourly_periods:
            return "No hourly forecast periods found in NWS response."
    except requests.exceptions.RequestException as e:
        return f"Error fetching hourly forecast: {e}"
    except (ValueError, KeyError):
        return "Error parsing NWS hourly forecast response."

    # 3. Process hourly data to get daily High/Low temperatures.
    daily_temps = defaultdict(lambda: {'high': -999, 'low': 999, 'unit': ''})
    for period in hourly_periods:
        p_date = datetime.fromisoformat(period['startTime']).date()
        temp = period['temperature']
        daily_temps[p_date]['high'] = max(daily_temps[p_date]['high'], temp)
        daily_temps[p_date]['low'] = min(daily_temps[p_date]['low'], temp)
        if not daily_temps[p_date]['unit']:
            daily_temps[p_date]['unit'] = period['temperatureUnit']

    # 4. Get daily forecast data for detailed descriptions and wind.
    try:
        forecast_response = requests.get(forecast_url, headers=headers)
        forecast_response.raise_for_status()
        daily_periods = forecast_response.json().get("properties", {}).get("periods", [])
        if not daily_periods:
            return "No daily forecast periods found in NWS response."
    except requests.exceptions.RequestException as e:
        return f"Error fetching daily forecast: {e}"
    except (ValueError, KeyError):
        return "Error parsing NWS daily forecast response."

    # 5. Process daily periods to get detailed forecast and wind.
    daily_details = {}
    for period in daily_periods:
        p_date = datetime.fromisoformat(period['startTime']).date()
        if p_date not in daily_details:
            daily_details[p_date] = {
                'name': p_date.strftime('%A, %B %d'),
                'detailedForecast': '',
                'windSpeed': ''
            }
        
        # Prioritize daytime forecast details
        if period['isDaytime']:
            daily_details[p_date]['detailedForecast'] = period.get('detailedForecast', '')
            daily_details[p_date]['windSpeed'] = f"{period.get('windSpeed', '')} {period.get('windDirection', '')}".strip()
        else:
            # Use nighttime details only if daytime details are missing
            if not daily_details[p_date]['detailedForecast']:
                daily_details[p_date]['detailedForecast'] = period.get('detailedForecast', '')
            if not daily_details[p_date]['windSpeed']:
                daily_details[p_date]['windSpeed'] = f"{period.get('windSpeed', '')} {period.get('windDirection', '')}".strip()

    # 6. Format and return the weather details for all days.
    output_details = []
    # Use dates from daily_temps as the source of truth for which days we have full data
    for d in sorted(daily_temps.keys()):
        if d in daily_details:
            temps = daily_temps[d]
            details = daily_details[d]
            
            high_temp = f"{temps['high']}°{temps['unit']}"
            low_temp = f"{temps['low']}°{temps['unit']}"
            
            output_details.append(
                f"{details['name']}: High: {high_temp}, Low: {low_temp}, "
                f"Wind: {details['windSpeed']}, Forecast: {details['detailedForecast']}"
            )

    if not output_details:
        return "Could not find any forecast for the specified location."
        
    return "\n".join(output_details)

if __name__ == "__main__":
    # 1. Explicitly cast PORT to an integer
    port = int(os.getenv("PORT", 8080))
    
    logger.info(f"🚀 MCP server started on port {port}")
    
    # Could also use 'sse' transport, host="0.0.0.0" required for Cloud Run.
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            # 2. Pass the integer variable here
            port=port,
        )
    )