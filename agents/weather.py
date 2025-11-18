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
        unit = unit.lower()

        # Fetch daily forecast
        daily_url = (
            f"https://weather.googleapis.com/v1/weather:dailyForecast"
            f"?location.latitude={latitude}&location.longitude={longitude}"
            f"&dailyForecastDays=1&units={unit.upper()}&key={api_key}"
        )

        # Fetch hourly forecast
        hourly_url = (
            f"https://weather.googleapis.com/v1/weather:hourlyForecast"
            f"?location.latitude={latitude}&location.longitude={longitude}"
            f"&hourlyForecastHours=24&units={unit.upper()}&key={api_key}"
        )

        daily_response = requests.get(daily_url)
        hourly_response = requests.get(hourly_url)

        daily_data = daily_response.json()
        hourly_data = hourly_response.json()

        result = {
            "max_uv_time": None,
            "max_uv_value": None,
            "max_temp_time": None,
            "max_temp_value": None,
            "rain_window": {"start": None, "end": None, "peak_chance": 0},
            "daily_summary": {}
        }

        # Daily summary
        today = daily_data.get("dailyForecasts", [{}])[0]
        segments = today.get("segments", {})
        result["daily_summary"] = {
            "day_condition": segments.get("day", {}).get("weatherCondition", {}).get("description", "Unknown"),
            "night_condition": segments.get("night", {}).get("weatherCondition", {}).get("description", "Unknown"),
            "temp_max": segments.get("day", {}).get("temperatureMax", {}).get("value", "N/A"),
            "temp_min": segments.get("night", {}).get("temperatureMin", {}).get("value", "N/A"),
            "uv_index": today.get("uvIndex", {}).get("value", "N/A")
        }

        # Track peak values
        peak_uv = 0
        peak_temp = float("-inf")
        rain_times = []
        rain_threshold = 0.3  # 30%+ is considered notable

        for hour in hourly_data.get("hourlyForecasts", []):
            time_str = hour.get("validTime")
            time_obj = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
            time_local = time_obj.strftime("%H:%M")

            uv = hour.get("uvIndex", {}).get("value", 0)
            temp = hour.get("temperature", {}).get("value", 0)
            rain_chance = hour.get("precipitationChance", 0.0)

            if uv > peak_uv:
                peak_uv = uv
                result["max_uv_time"] = time_local
                result["max_uv_value"] = uv

            if temp > peak_temp:
                peak_temp = temp
                result["max_temp_time"] = time_local
                result["max_temp_value"] = temp

            if rain_chance >= rain_threshold:
                rain_times.append((time_obj, rain_chance))

        # Determine rain window
        if rain_times:
            start_time = min(rain_times, key=lambda x: x[0])[0].strftime("%H:%M")
            end_time = max(rain_times, key=lambda x: x[0])[0].strftime("%H:%M")
            peak = max(rain_times, key=lambda x: x[1])[1]
            result["rain_window"] = {
                "start": start_time,
                "end": end_time,
                "peak_chance": round(peak, 2)
            }

        return result
    
    def create_weather_agent(self) -> LlmAgent:
        instructions = (
            """
            You are a helpful weather assistant.
            Provide a concise today's weather forecast for the requested location.
            Use the google_search tool to gather raw weather data before summarizing.
            Keep the tone friendly and informative.
            """
        )

        weather_agent = LlmAgent(
            name="WeatherAgent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction=instructions,
            tools=[google_search],
        )
        return weather_agent