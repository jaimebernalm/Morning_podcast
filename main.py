# Entry point: manager agent triggers pipeline
# main.py (The "System")

import time
import sys
import os
import logging
from dotenv import load_dotenv

# Load environment variables (API keys)
load_dotenv()

# Configure logging to see agent and validator output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Ensure we can import from the current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.manager import ManagerAgent
from agents.summarizer import SuperWriterAgent
from db.db_utils import get_user_profile
from utils.session import InMemorySessionService

def main():
    user_id = "user_123"

    # 1. INIT SESSION SERVICE
    session_service = InMemorySessionService()

    # 2. FETCH DB DATA
    print(f"Fetching profile for {user_id}...")
    user_profile_data = get_user_profile(user_id)
    
    if not user_profile_data:
        print(f"User {user_id} not found in preferences.json")
        return

    # 3. INJECT INTO SESSION
    session_service.initialize_user_context(user_profile_data)
    
    # 4. START MANAGER
    print("Initializing Manager Agent...")
    manager = ManagerAgent(session_service)
    manager.execute_gathering() 

    # 5. START SUMMARIZER
    print("Initializing Summarizer Agent...")
    summarizer = SuperWriterAgent(session_service)
    final_script = summarizer.generate_script()

    print("\n" + "="*30)
    print(" FINAL PODCAST SCRIPT ")
    print("="*30 + "\n")
    print(final_script)

if __name__ == "__main__":
    main()