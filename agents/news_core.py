# Fetches important news (non-personalized)
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search

from utils.fetch_tools import retry_config
from agents.base import BaseAgent


class NewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="NewsAgent")

    def create_news_agent(self) -> LlmAgent:
        instructions = (
            """
            You are a helpful news assistant.
            Provide 3-5 concise briefings for the requested location and timeframe.
            Use the google_search tool to gather raw headlines before summarizing.
            Balance international and local relevance whenever possible and keep the tone friendly and actionable.
            """
        )

        news_agent = LlmAgent(
            name="NewsAgent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction=instructions,
            tools=[google_search],
        )
        return news_agent