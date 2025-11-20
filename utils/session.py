class SessionState:
    def __init__(self, agent_name="Global"):
        self.agent_name = agent_name
        self.state = {}

    def get(self, key, default=None):
        return self.state.get(key, default)

    def __setitem__(self, key, value):
        self.state[key] = value

    def __getitem__(self, key):
        return self.state[key]

# Keys for session state
KEY_USER_NAME = "user_name"
KEY_LOCATION = "location"
KEY_INTERESTS = "interests"
KEY_NEWS_DATA = "news_data"
KEY_WEATHER_DATA = "weather_data"
KEY_TRAFFIC_DATA = "traffic_data"
KEY_ORIGIN = "origin"
KEY_DESTINATION = "destination"

class InMemorySessionService:
    def __init__(self):
        self.state = {}

    def initialize_user_context(self, profile_data):
        self.state[KEY_USER_NAME] = profile_data.get("name")
        self.state[KEY_LOCATION] = profile_data.get("location")
        self.state[KEY_INTERESTS] = profile_data.get("interests")
        
        commute = profile_data.get("commute", {})
        self.state[KEY_ORIGIN] = commute.get("origin")
        self.state[KEY_DESTINATION] = commute.get("destination")
