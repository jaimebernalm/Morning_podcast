# Merges all inputs into a coherent podcast script
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from utils.fetch_tools import retry_config
import requests
import os
from datetime import datetime, timedelta
from agents.base import BaseAgent
from utils.session import (
    KEY_USER_NAME, KEY_LOCATION, KEY_INTERESTS, 
    KEY_NEWS_DATA, KEY_WEATHER_DATA, KEY_TRAFFIC_DATA
)
from google.adk.runners import InMemoryRunner
import json

class SuperWriterAgent(BaseAgent):
    def __init__(self, session):
        super().__init__(name="SuperWriter")
        self.session = session

    def generate_script(self):
        """
        Reads all data from the session and generates the final script.
        """
        # 1. Gather Data from Session
        user_name = self.session.state.get(KEY_USER_NAME, "User")
        location = self.session.state.get(KEY_LOCATION, "Unknown")
        interests = self.session.state.get(KEY_INTERESTS, [])
        
        news_data = self.session.state.get(KEY_NEWS_DATA, [])
        weather_data = self.session.state.get(KEY_WEATHER_DATA, {})
        traffic_data = self.session.state.get(KEY_TRAFFIC_DATA, {})
        
        # 2. Construct the Input Payload
        payload = {
            "user_name": user_name,
            "location": location,
            "interests": interests,
            "news": news_data,
            "weather": weather_data,
            "traffic": traffic_data
        }
        
        payload_str = json.dumps(payload, indent=2, default=str)
        
        # 3. Create the Agent
        writer = self.create_writer_agent()
        runner = InMemoryRunner(agent=writer)
        
        # 4. Run the Agent
        print("SuperWriter: Generating script...")
        
        import asyncio
        
        async def _run():
            events = await runner.run_debug(f"Here is the collected data. Generate the morning briefing script:\n\n{payload_str}")
            texts = []
            for event in events:
                if hasattr(event, 'content') and event.content:
                    parts = getattr(event.content, 'parts', [])
                    if parts:
                        for part in parts:
                            if hasattr(part, 'text'):
                                texts.append(part.text)
            return "\n".join(texts)
            
        try:
            return asyncio.run(_run())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_run())

    def create_writer_agent(self) -> LlmAgent:
        # This System Prompt acts as the "Planner" and "Writer" combined
        instructions = """
        You are the Host and Executive Producer of a Daily Morning Podcast.

        **YOUR INPUTS:**
        1. User Profile: Name, Location, Interests.
        2. Tone Preference: (e.g., "Energetic," "Sarcastic," "Professional").
        3. Time Limit: (e.g., "2 minutes").
        4. Raw Data Payload: A JSON containing News, Weather, and Traffic data.

        **YOUR PROCESS (Chain of Thought):**
        Do not start writing immediately. You must perform a "Mental Draft" first.
        
        1. **Analyze Data:** Look at the Weather and Traffic. Is it a good day or bad day? (e.g., Rain + Traffic = Bad Day).
        2. **Select Content:** Look at the News. Pick only the stories that fit the Time Limit. Discard the rest.
        3. **Time Budgeting:** - Intro: 5% of Time Limit
           - Weather Overview: 20% of Time Limit
           - Traffic Overview: 20% of Time Limit
           - News Summary: 55% of Time Limit
           ...ensure total <= Time Limit.
        4. **Write Script:** Write the final spoken script.

        **WRITING RULES:**
        - **Transitions:** Use smooth transitions. (e.g., "Speaking of messy situations, let's look at the traffic...")
        - **Personality:** If the tone is "Sarcastic," complain about the traffic data. If "Energetic," hype up the rain.
        - **No Formatting:** Do not use markdown like **Bold** or [Brackets]. Write raw text for Text-to-Speech.
        - **Context:** Refer to the user by name.

        **OUTPUT:**
        Return ONLY the final script.
        """

        return LlmAgent(
            name="SuperWriter",
            model=Gemini(model="gemini-2.5-flash-lite"), # Use a smarter model (Pro) for the writing
            instruction=instructions,
            # No tools needed - it just processes the text input it receives
        )
