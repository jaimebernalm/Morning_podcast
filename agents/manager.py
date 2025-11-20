# Controls overall flow
# Fetches important news (non-personalized)
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool

from agents.base import BaseAgent
from utils.session import (
    KEY_USER_NAME, KEY_LOCATION, KEY_INTERESTS, 
    KEY_NEWS_DATA, KEY_WEATHER_DATA, KEY_TRAFFIC_DATA,
    KEY_ORIGIN, KEY_DESTINATION
)

class ManagerAgent(BaseAgent):
    def __init__(self, session):
        """
        We inject the session here so the Manager can read user prefs
        and write the results.
        """
        super().__init__(name="ManagerAgent")
        self.session = session

    def _build_system_instruction(self) -> str:
        """
        Dynamically creates the prompt based on the User's specific session data.
        """
        # 1. Read Context from Session (Safe access with .get)
        user_name = self.session.state.get(KEY_USER_NAME, "User")
        # Handle location if it's a dict (from preferences) or string
        location_data = self.session.state.get(KEY_LOCATION, "Unknown Location")
        if isinstance(location_data, dict):
            location_str = f"{location_data.get('city', 'Unknown City')}, {location_data.get('country', '')}"
        else:
            location_str = str(location_data)

        # 2. Inject into Prompt
        return f"""
        You are the **Executive Producer** of a morning podcast for {user_name}.
        
        **YOUR CONTEXT:**
        - User Location: {location_str}
        
        **YOUR GOAL:**
        Coordinate the collection of data to build a briefing.
        
        **YOUR TOOLS:**
        1. `get_weather`: Get weather for the user's location.
        2. `get_traffic`: Get traffic for the user's commute.
        3. `get_news`: Get the top trending news headlines globally and for the user's location.
        4. `get_tailored_news`: Get news specific to the user's interests.
        
        **CRITICAL INSTRUCTION:**
        Do not summarize the data yourself yet. Just execute the tools to gather the raw information.
        """

    def create_orchestrator(self) -> LlmAgent:
        instructions = self._build_system_instruction()
        
        # We wrap the tools so the Manager can call them.
        tools = [
            self._wrap_traffic_tool,
            self._wrap_weather_tool,
            self._wrap_news_tool,
            self._wrap_tailored_news_tool
        ]

        return LlmAgent(
            name="ManagerOrchestrator",
            model=Gemini(model="gemini-2.0-flash-exp"), 
            instruction=instructions,
            tools=tools,
        )

    # --- Tool Wrappers ---

    async def _wrap_news_tool(self, query: str):
        """Tool exposed to the LLM to fetch news."""
        from agents.news_core import NewsAgent 
        
        print(f"Manager: Fetching news for {query}...")
        
        agent = NewsAgent()
        # Use the validated fetch
        news_items = await agent.fetch_and_validate_news(query)
        
        # Append to existing news data
        current_news = self.session.state.get(KEY_NEWS_DATA, [])
        if not isinstance(current_news, list):
            current_news = []
            
        current_news.append({
            "query": query,
            "result": news_items # Now storing structured list
        })

        self.session.state[KEY_NEWS_DATA] = current_news
        return f"Found {len(news_items)} new valid news stories. Saved to session."

    async def _wrap_tailored_news_tool(self):
        """Tool exposed to the LLM to fetch tailored news based on user interests."""
        from agents.tailored_news import TailoredNewsAgent
        
        # Get interests from session
        interests = self.session.state.get(KEY_INTERESTS, [])
        if not interests:
            return "No user interests found in session."
            
        print(f"Manager: Fetching tailored news for interests: {interests}...")
        
        agent = TailoredNewsAgent()
        results = await agent.get_news_for_interests(interests)
        
        # Append to existing news data
        current_news = self.session.state.get(KEY_NEWS_DATA, [])
        if not isinstance(current_news, list):
            current_news = []
            
        count = 0
        for interest, items in results.items():
            if items:
                current_news.append({
                    "query": f"Interest: {interest}",
                    "result": items
                })
                count += len(items)

        self.session.state[KEY_NEWS_DATA] = current_news
        return f"Found {count} tailored news stories across {len(results)} interests. Saved to session."

    def _wrap_weather_tool(self):
        """Fetches weather for the user's stored location."""
        from agents.weather import WeatherAgent
        
        print(f"Manager: Fetching weather...")
        weather_agent = WeatherAgent()
        
        # Get location from session (expecting dict with coordinates)
        location_data = self.session.state.get(KEY_LOCATION)
        
        if not location_data or not isinstance(location_data, dict):
            return "Error: No valid location data found in session."
            
        coords = location_data.get("coordinates", {})
        lat = coords.get("lat")
        lon = coords.get("lon")
        
        if lat is None or lon is None:
             return "Error: Latitude or Longitude missing in location data."
        
        try:
            results = weather_agent.get_weather_insights(lat, lon)
        except Exception as e:
            results = f"Error fetching weather: {e}"
            
        self.session.state[KEY_WEATHER_DATA] = results
        return "Weather data saved."

    def _wrap_traffic_tool(self):
        """Fetches traffic for the user's stored commute."""
        from agents.traffic import TrafficAgent
        
        print(f"Manager: Fetching traffic...")
        traffic_agent = TrafficAgent()
        
        origin = self.session.state.get(KEY_ORIGIN)
        destination = self.session.state.get(KEY_DESTINATION)
        
        if not origin or not destination:
            return "Error: Origin or Destination missing in session."
        
        try:
            results = traffic_agent.get_traffic_data(origin, destination)
        except Exception as e:
            results = f"Error fetching traffic: {e}"

        self.session.state[KEY_TRAFFIC_DATA] = results
        return "Traffic data saved."

    def execute_gathering(self):
        """
        Orchestrates the data gathering process by running the Manager Agent.
        """
        from google.adk.runners import InMemoryRunner
        import asyncio
        
        print("Manager: Starting data gathering...")
        orchestrator = self.create_orchestrator()
        runner = InMemoryRunner(agent=orchestrator)
        
        async def _run():
            # Trigger the agent to use its tools
            await runner.run_debug("Please gather all necessary information for the morning briefing.")
            
        try:
            asyncio.run(_run())
        except RuntimeError:
            # If we are already in a loop (e.g. notebook), we await if possible or fail
            # For a script like main.py, asyncio.run is correct.
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_run())
            else:
                raise
