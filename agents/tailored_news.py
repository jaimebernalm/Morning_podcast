from agents.base import BaseAgent
from agents.news_core import NewsAgent
import asyncio

class TailoredNewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TailoredNewsAgent")

    async def get_news_for_interests(self, interests: list[str]) -> dict:
        """
        Fetches news for a list of interests.
        Returns a dictionary where keys are interests and values are the list of validated news items.
        """
        results = {}
        
        # We can run these in parallel for better performance
        tasks = []
        for interest in interests:
            tasks.append(self._fetch_single_interest(interest))
        
        # Gather all results
        news_items_list = await asyncio.gather(*tasks)
        
        for interest, news_items in zip(interests, news_items_list):
            results[interest] = news_items
            
        return results

    async def _fetch_single_interest(self, interest: str):
        """
        Helper to run the NewsAgent for a single topic.
        """
        print(f"[{self.name}] Fetching news for interest: {interest}...")
        
        agent = NewsAgent()
        # Use the new validated fetch method
        # We ask specifically for news about the interest
        news_items = await agent.fetch_and_validate_news(f"Find the top 3 most important news stories specifically about: {interest}")
        
        return news_items
