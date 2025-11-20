# Fetches daily weather for user location
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from utils.fetch_tools import retry_config
import requests
import os
from datetime import datetime
from typing import Dict, Any

from pathlib import Path
from agents.base import BaseAgent# (Optional) Traffic report based on location

class TrafficAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TrafficAgent")
        self.api_key = os.getenv("DIRECTIONS_API_KEY")

    def get_traffic_data(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Fetches raw traffic statistics. Does NOT write a summary.
        """
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

            # We return a dictionary of FACTS
            return {
                "type": "traffic",
                "route_summary": route.get("summary", "main route"),
                "duration_in_traffic_text": leg["duration_in_traffic"]["text"],
                "duration_in_traffic_value": leg["duration_in_traffic"]["value"], # Seconds
                "normal_duration_text": leg["duration"]["text"],
                "normal_duration_value": leg["duration"]["value"], # Seconds
                "start_address": leg["start_address"],
                "end_address": leg["end_address"],
                "has_delay": leg["duration_in_traffic"]["value"] > leg["duration"]["value"]
            }

        except Exception as e:
            return {"error": str(e)}

    def create_traffic_agent(self) -> LlmAgent:
        # Instruction: STRICTLY return the JSON from the tool. Do not chat.
        instructions = """
        You are a Data Fetcher. 
        Your ONLY job is to run the `get_traffic_data` tool and return its output exactly as JSON.
        Do not add any conversational text.
        """
        
        return LlmAgent(
            name="TrafficAgent",
            model=Gemini(model="gemini-2.5-flash-lite"),
            instruction=instructions,
            tools=[self.get_traffic_data], 
        )