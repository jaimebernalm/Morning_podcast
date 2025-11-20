import pytest
import asyncio
from agents.tailored_news import TailoredNewsAgent

@pytest.mark.asyncio
async def test_tailored_news_instantiation():
    agent = TailoredNewsAgent()
    assert agent.name == "TailoredNewsAgent"

# Note: Integration tests would require mocking NewsAgent or having API keys.

