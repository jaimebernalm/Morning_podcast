# Fetches important news (non-personalized)
from google.genai import types

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search, AgentTool, ToolContext
from google.adk.code_executors import BuiltInCodeExecutor

# agents/base.py

import logging
from utils.memory import MemoryManager
from utils.session import SessionState

class BaseAgent:
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)

        # Shared infrastructure
        self.memory = MemoryManager()
        self.session = SessionState(agent_name=name)

    def run(self, *args, **kwargs):
        raise NotImplementedError("You must implement `run()` in your subclass.")
