# Fetches daily weather for user location
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from utils.fetch_tools import retry_config
import requests
import os
from datetime import datetime

from pathlib import Path
from agents.base import BaseAgent# (Optional) Traffic report based on location

class TrafficAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TrafficAgent")
        self.api_key = os.getenv("DIRECTIONS_API_KEY")

    def get_traffic_time(self, origin: str, destination: str) -> str:
        url = (
            "https://maps.googleapis.com/maps/api/directions/json"
            f"?origin={origin}&destination={destination}&departure_time=now&key={self.api_key}"
        )

        try:
            res = requests.get(url)
            res.raise_for_status()
            data = res.json()

            route = data["routes"][0]
            leg = route["legs"][0]

            duration_in_traffic = leg["duration_in_traffic"]["text"]
            normal_duration = leg["duration"]["text"]
            summary = route.get("summary", "your usual route")

            traffic_msg = (
                f"Traffic is smooth this morning. "
                f"Your commute from {origin} to {destination} via {summary} will take about {duration_in_traffic}."
                if duration_in_traffic == normal_duration
                else f"Expect some delays on your way from {origin} to {destination} via {summary}. "
                     f"With current traffic, it will take approximately {duration_in_traffic} instead of the usual {normal_duration}."
            )

            return traffic_msg

        except (requests.RequestException, KeyError, IndexError) as e:
            self.logger.error(f"TrafficAgent failed: {e}")
            return "I'm sorry, I couldn't fetch traffic information at the moment."

    def create_traffic_agent(self) -> LlmAgent:
        instructions = (
            """
            You are a helpful traffic assistant.
            Provide a concise traffic report for the requested location.
            Use the get_traffic_time tool to gather raw traffic data before summarizing.
            Only if it can't fetch the data, use the google_search tool.
            Keep the tone friendly and informative.
            """
        )

        traffic_agent = LlmAgent(
            name="TrafficAgent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction=instructions,
            tools=[self.get_traffic_time, google_search],
        )
        return traffic_agent