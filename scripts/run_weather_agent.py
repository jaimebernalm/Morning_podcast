"""CLI helper to run the WeatherAgent and print its output."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Iterable

# Add repository root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

from agents.weather import WeatherAgent
from google.adk.runners import InMemoryRunner

def _ensure_api_key() -> None:
    if load_dotenv is not None:
        load_dotenv()
    
    # We check for GOOGLE_API_KEY for the LLM
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Warning: GOOGLE_API_KEY not found. The LLM might fail.")

def _extract_text(parts: Iterable) -> str:
    lines: list[str] = []
    for part in parts:
        text = getattr(part, "text", None)
        if text:
            lines.append(text)
    return "\n".join(lines)

async def _run(lat: float, lon: float) -> None:
    _ensure_api_key()

    print(f"Initializing WeatherAgent for coordinates: {lat}, {lon}...")
    weather_agent = WeatherAgent()
    llm_agent = weather_agent.create_weather_agent()
    runner = InMemoryRunner(agent=llm_agent)

    # We explicitly ask the model to use the tool with the provided coordinates
    prompt = f"Call the get_weather_insights tool for latitude={lat} and longitude={lon}."
    
    print("Running agent...")
    # Using quiet=False to see the runner's internal steps (tool calls, etc.)
    events = await runner.run_debug(
        prompt,
        quiet=False, 
    )

    print("\n=== Weather Agent Output ===\n")
    
    # Extract and print the response
    found_content = False
    for i, event in enumerate(events):
        print(f"Event {i}: {type(event)}")
        if hasattr(event, 'content') and event.content:
            parts = getattr(event.content, 'parts', [])
            if parts:
                print(f"  Parts: {[type(p) for p in parts]}")
                for part in parts:
                    # Check for text
                    if hasattr(part, 'text') and part.text:
                        print(f"  Text: {part.text}")
                        found_content = True
                    
                    # Check for function call
                    if hasattr(part, 'function_call') and part.function_call:
                        print(f"  Function Call: {part.function_call.name} args={part.function_call.args}")
                    
                    # Check for function response
                    if hasattr(part, 'function_response') and part.function_response:
                        print(f"  Function Response: {part.function_response.name} response={part.function_response.response}")
                        
        else:
             print("  (No content in this event)")
    
    if not found_content:
        print("No text output received from the agent.")

def main():
    parser = argparse.ArgumentParser(
        description="Run the WeatherAgent."
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=37.7749,
        help="Latitude (default: San Francisco)",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=-122.4194,
        help="Longitude (default: San Francisco)",
    )

    args = parser.parse_args()
    
    try:
        asyncio.run(_run(args.lat, args.lon))
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()
