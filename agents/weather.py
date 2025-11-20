# Fetches daily weather for user location
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from utils.fetch_tools import retry_config
import requests
import os
from datetime import datetime, timedelta
from agents.base import BaseAgent

class WeatherAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="WeatherAgent")
        self.api_key = os.getenv("WEATHER_API_KEY")

    def get_weather_insights(self, latitude: float, longitude: float, unit: str = "metric"):
        api_key = os.getenv("WEATHER_API_KEY")
        
        units_param = "METRIC" if unit.lower() == "metric" else "IMPERIAL"

        daily_url = (
            f"https://weather.googleapis.com/v1/forecast/days:lookup"
            f"?key={api_key}&location.latitude={latitude}&location.longitude={longitude}"
            f"&days=1&unitsSystem={units_param}"
        )

        hourly_url = (
            f"https://weather.googleapis.com/v1/forecast/hours:lookup"
            f"?key={api_key}&location.latitude={latitude}&location.longitude={longitude}"
            f"&hours=24&unitsSystem={units_param}"
        )

        daily_response = requests.get(daily_url)
        hourly_response = requests.get(hourly_url)

        daily_response.raise_for_status()
        daily_data = daily_response.json()
        
        hourly_response.raise_for_status()
        hourly_data = hourly_response.json()

        result = {
            "max_uv_time": None,
            "max_uv_value": 0, 
            "max_temp_time": None,
            "max_temp_value": float("-inf"),
            # Added "peak_time" to the structure
            "rain_window": {"start": None, "end": None, "peak_chance": 0, "peak_time": None},
            "daily_summary": {}
        }

        today = daily_data.get("forecastDays", [{}])[0]
        day_forecast = today.get("daytimeForecast", {})
        night_forecast = today.get("nighttimeForecast", {})
        
        result["daily_summary"] = {
            "day_condition": day_forecast.get("weatherCondition", {}).get("description", {}).get("text", "Unknown"),
            "night_condition": night_forecast.get("weatherCondition", {}).get("description", {}).get("text", "Unknown"),
            "temp_max": today.get("maxTemperature", {}).get("degrees", "N/A"),
            "temp_min": today.get("minTemperature", {}).get("degrees", "N/A"),
            "uv_index": day_forecast.get("uvIndex", 0)
        }

        peak_uv = -1
        peak_temp = float("-inf")
        rain_times = []
        rain_threshold = 30 

        # NEW: Track absolute peak regardless of threshold
        absolute_peak_rain = 0
        absolute_peak_rain_time = None

        for hour in hourly_data.get("forecastHours", []):
            time_str = hour.get("interval", {}).get("startTime")
            if not time_str:
                continue
            
            try:
                time_obj = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
                time_local = time_obj.strftime("%H:%M")
            except ValueError:
                continue

            uv = hour.get("uvIndex", 0)
            temp = hour.get("temperature", {}).get("degrees", 0)
            rain_chance = hour.get("precipitation", {}).get("probability", {}).get("percent", 0)

            # 1. Update Absolute Peak Rain (Global Tracker)
            if rain_chance > absolute_peak_rain:
                absolute_peak_rain = rain_chance
                absolute_peak_rain_time = time_local

            # 2. Update Max UV
            if uv > peak_uv:
                peak_uv = uv
                result["max_uv_time"] = time_local
                result["max_uv_value"] = uv

            # 3. Update Max Temp
            if temp > peak_temp:
                peak_temp = temp
                result["max_temp_time"] = time_local
                result["max_temp_value"] = temp

            # 4. Collect Rain Window Candidates
            if rain_chance >= rain_threshold:
                rain_times.append((time_obj, rain_chance))

        # Determine rain window
        if rain_times:
            rain_times.sort(key=lambda x: x[0])
            
            start_time = rain_times[0][0].strftime("%H:%M")
            end_time = rain_times[-1][0].strftime("%H:%M")
            
            # Find the max tuple inside the window to get the specific time
            peak_tuple = max(rain_times, key=lambda x: x[1])
            peak_val = peak_tuple[1]
            peak_time_str = peak_tuple[0].strftime("%H:%M")
            
            result["rain_window"] = {
                "start": start_time,
                "end": end_time,
                "peak_chance": round(peak_val, 2),
                "peak_time": peak_time_str # Added
            }
        else:
            # Even if threshold wasn't met, show the highest chance found
            result["rain_window"] = {
                "start": None,
                "end": None,
                "peak_chance": absolute_peak_rain,
                "peak_time": absolute_peak_rain_time # Added
            }

        return result

       
    
    def create_weather_agent(self) -> LlmAgent:
            # Changed instructions to force Tool usage over Google Search
            instructions = """
            You are a Data Fetcher.
            1. Run the `get_weather_insights` tool to get the weather data.
            2. Once you have the data, you MUST output the raw JSON string as your final answer.
            3. Do not add any markdown formatting or conversational text. Just the JSON.
            """
            
            return LlmAgent(
                name="WeatherAgent",
                model=Gemini(model="gemini-2.5-flash-lite"),
                instruction=instructions,
                tools=[self.get_weather_insights], # Explicitly use your custom tool
            )