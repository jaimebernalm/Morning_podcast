"""CLI helper to run the NewsAgent and print its morning briefing."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover - dependency is optional
    load_dotenv = None

from agents.news_core import NewsAgent
from google.adk.runners import InMemoryRunner


def _ensure_api_key() -> None:
    if load_dotenv is not None:
        load_dotenv()

    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError(
            "Missing GOOGLE_API_KEY. Set it in your environment or .env file before running."
        )


def _extract_text(parts: Iterable) -> str:
    lines: list[str] = []
    for part in parts:
        text = getattr(part, "text", None)
        if text:
            lines.append(text)
    return "\n".join(lines)


def _summaries_from_events(events, agent_name: str) -> list[str]:
    summaries: list[str] = []
    for event in events:
        if getattr(event, "author", None) != agent_name:
            continue
        is_final = getattr(event, "is_final_response", None)
        if callable(is_final) and not event.is_final_response():
            continue
        if event.content and event.content.parts:
            summaries.append(_extract_text(event.content.parts))
    return summaries


async def _run(location: str, *, user_id: str, session_id: str) -> None:
    _ensure_api_key()

    news_agent = NewsAgent()
    llm_agent = news_agent.create_news_agent()
    runner = InMemoryRunner(agent=llm_agent)

    prompt = f"Create a concise morning news briefing for {location}."
    events = await runner.run_debug(
        prompt,
        user_id=user_id,
        session_id=session_id,
        quiet=True,
        verbose=False,
    )

    summaries = [s for s in _summaries_from_events(events, llm_agent.name) if s]
    if not summaries:
        print("No textual response returned by the agent.")
        return

    print("\n=== Morning Briefing ===\n")
    print("\n\n".join(summaries))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the NewsAgent and print its generated briefing."
    )
    parser.add_argument(
        "--location",
        default="Berlin",
        help="City or region to fetch news for (defaults to Berlin).",
    )
    parser.add_argument(
        "--user-id",
        default="demo_user",
        help="Optional user identifier to reuse sessions.",
    )
    parser.add_argument(
        "--session-id",
        default="demo_session",
        help="Optional session identifier for conversation continuity.",
    )

    args = parser.parse_args(argv)

    try:
        asyncio.run(
            _run(args.location, user_id=args.user_id, session_id=args.session_id)
        )
    except KeyboardInterrupt:  # pragma: no cover - interactive convenience
        return 130
    except Exception as exc:  # pragma: no cover - surfaces runtime failures
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



