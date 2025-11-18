#  Daily Personalized Podcast Generator (Multi-Agent System)

This project is a backend prototype of a **daily, personalized podcast generator**. It uses a modular **multi-agent architecture** to gather and synthesize content (news, weather, traffic, niche interests) into a daily audio or text briefing, tailored to each user's preferences.

---

##  Project Structure

```
daily_podcast_agent/

 main.py                          # Entry point: manager agent triggers pipeline

 agents/
    manager.py                   # Controls overall flow
    profile_fetcher.py           # Fetches user preferences from the DB
    news_core.py                 # Fetches important news (non-personalized)
    weather.py                   # Fetches daily weather for user location
    traffic.py                   # (Optional) Traffic report based on location
    tailored_news/
       coordinator.py           # Loops through user interests
       topic_agent.py           # Fetches/summarizes one topic
    memory_validator.py          # Checks yesterday's content to avoid repetition
    summarizer.py                # Merges all inputs into a coherent podcast script

 db/
    preferences.json             # User preferences (topics, tone, etc.)
    memory_log.json              # Stores recent podcast topics
    user_log.json                # Tracks if user listened to past podcasts
    db_utils.py                  # Helper functions to load/save JSONs

 utils/
    fetch_tools.py               # Web scraping / API fetching tools
    tts.py                       # (Optional) Text-to-speech engine
    logger.py                    # Logger for agent activity

 tests/
    test_tailored_news.py
    test_memory_validator.py
    ...

 README.md
 requirements.txt
```

---

##  Agents Overview

| Agent | Role |
|-------|------|
| **Manager** | Orchestrates the entire pipeline. |
| **Profile Fetcher** | Loads user interests, tone, location, time limits. |
| **Tailored News Coordinator** | Reads preferences and calls subagents. |
| **Topic Agent(s)** | Fetch and summarize topic-specific news. |
| **Memory Validator** | Filters out repeated stories from previous day. |
| **Summarizer** | Combines all content into one engaging script. |
| **TTS (Optional)** | Converts final text into audio output. |

---

##  How to Run

1. Create or modify `db/preferences.json` with a sample user profile.
2. Run `main.py` to generate the podcast script.
3. (Optional) Use `utils/tts.py` to generate audio from the script.

---

##  Tech Stack

- Python 3.10+
- OpenAI or other summarization APIs (optional)
- News/weather/traffic APIs (e.g., NewsAPI, OpenWeatherMap, Google Maps)
- ElevenLabs or Google TTS (optional)

---

##  Testing

Unit tests for each agent live in the `tests/` folder. Run:

```bash
pytest tests/
```
