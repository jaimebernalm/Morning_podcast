# Fetches important news (non-personalized)
from google.genai import types
import json
import logging

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from google.adk.runners import InMemoryRunner

from utils.fetch_tools import retry_config
from agents.base import BaseAgent
from agents.memory_validator import MemoryValidator


class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="NewsAgent")

    def create_news_agent(self) -> LlmAgent:
        # We force the LLM to output a structured list for the Validator
        instructions = """
        You are a News Aggregator.
        1. Search for the top 5 most important news stories for the requested location/topic.
        2. You MUST output a Valid JSON list of objects.
        
        Format:
        [
          {
            "id": "short_unique_headline_slug",
            "headline": "The actual headline",
            "summary": "A dense paragraph with key facts, numbers, and quotes.",
            "source": "Source Name"
          }
        ]
        """

        return LlmAgent(
            name="NewsAgent",
            model=Gemini(model="gemini-2.5-flash-lite"),
            instruction=instructions,
            tools=[google_search],
        )

    async def fetch_and_validate_news(self, query: str) -> list:
        """
        Runs the news agent, parses the JSON output, and validates against memory.
        """
        blueprint = self.create_news_agent()
        runner = InMemoryRunner(agent=blueprint)
        
        print(f"[{self.name}] Fetching news for: {query}")
        
        try:
            # Run the agent
            events = await runner.run_debug(f"Find news about: {query}")
            
            # Extract text
            response_text = ""
            for event in events:
                if hasattr(event, 'content') and event.content:
                    parts = getattr(event.content, 'parts', [])
                    if parts:
                        for part in parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
            
            # Parse JSON
            # Clean up markdown code blocks if present
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            # Find the first [ and last ]
            start = clean_text.find("[")
            end = clean_text.rfind("]")
            if start != -1 and end != -1:
                clean_text = clean_text[start:end+1]
                news_items = json.loads(clean_text)
            else:
                self.logger.warning(f"Could not find JSON list in response: {response_text[:100]}...")
                return []

            # Validate
            validator = MemoryValidator()
            valid_news = validator.validate_and_log(news_items)
            
            print(f"[{self.name}] Found {len(news_items)} items, {len(valid_news)} valid after deduplication.")
            return valid_news

        except Exception as e:
            self.logger.error(f"Error fetching/validating news: {e}")
            return []