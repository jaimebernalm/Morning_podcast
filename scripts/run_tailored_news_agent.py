"""CLI helper to run the TailoredNewsAgent and print its results."""

from __future__ import annotations

import asyncio
import os
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from agents.tailored_news import TailoredNewsAgent


def _ensure_api_key() -> None:
    if load_dotenv is not None:
        load_dotenv()

    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Set it in your environment or .env file before running."
        )


async def main() -> None:
    _ensure_api_key()

    # Sample interests for testing
    interests = [
        "Artificial Intelligence Agents",
        "SpaceX Starship",
        "Atletico Madrid"
    ]

    print(f"--- Starting Tailored News Agent ---")
    print(f"Fetching news for interests: {interests}")
    
    agent = TailoredNewsAgent()
    
    try:
        # The agent returns a dict: {interest: [list of news items]}
        results = await agent.get_news_for_interests(interests)
        
        print("\n=== Tailored News Results ===\n")
        
        for interest, news_items in results.items():
            print(f"--- Interest: {interest} ---")
            if not news_items:
                print("  No news found or validation failed.")
                continue
                
            for i, item in enumerate(news_items, 1):
                headline = item.get('headline', 'No Headline')
                source = item.get('source', 'Unknown Source')
                summary = item.get('summary', 'No Summary')
                
                print(f"  {i}. {headline} ({source})")
                print(f"     {summary[:150]}...") # Truncate summary for display
                print()
                
    except Exception as e:
        print(f"Error running tailored news agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
