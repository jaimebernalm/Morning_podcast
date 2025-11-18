import sys
import types
from types import SimpleNamespace


# Provide lightweight stand-ins for google.* modules so imports succeed during tests.
def _stub_module(path: str):
    if path in sys.modules:
        return sys.modules[path]

    module = types.ModuleType(path)
    sys.modules[path] = module

    parent_name, _, child_name = path.rpartition(".")
    if parent_name:
        parent = _stub_module(parent_name)
        setattr(parent, child_name, module)

    return module


_stub_module("google")
genai_types = _stub_module("google.genai.types")


def _http_retry_options(**kwargs):
    return SimpleNamespace(**kwargs)


genai_types.HttpRetryOptions = _http_retry_options

_stub_module("google.adk")
_stub_module("google.adk.models")
_stub_module("google.adk.runners")
_stub_module("google.adk.sessions")
_stub_module("google.adk.code_executors")

adk_agents = _stub_module("google.adk.agents")
adk_agents.LlmAgent = SimpleNamespace

adk_models = _stub_module("google.adk.models.google_llm")
adk_models.Gemini = SimpleNamespace

adk_tools = _stub_module("google.adk.tools")
setattr(adk_tools, "google_search", SimpleNamespace(name="google_search_tool"))
setattr(adk_tools, "AgentTool", SimpleNamespace)
setattr(adk_tools, "ToolContext", SimpleNamespace)

adk_code = _stub_module("google.adk.code_executors")
setattr(adk_code, "BuiltInCodeExecutor", SimpleNamespace)

adk_runners = sys.modules["google.adk.runners"]
setattr(adk_runners, "InMemoryRunner", SimpleNamespace)

adk_sessions = sys.modules["google.adk.sessions"]
setattr(adk_sessions, "InMemorySessionService", SimpleNamespace)


import agents.news_core as news_core  # noqa: E402
from agents.news_core import NewsAgent  # noqa: E402  pylint: disable=wrong-import-position


def test_create_news_agent_wires_llm_agent(monkeypatch):
    agent = NewsAgent()
    created_models = []

    def fake_gemini(*, model, retry_options):
        payload = SimpleNamespace(model=model, retry_options=retry_options)
        created_models.append(payload)
        return payload

    monkeypatch.setattr(news_core, "Gemini", fake_gemini)

    created_agents = []

    def fake_llm_agent(**kwargs):
        created_agents.append(kwargs)
        return SimpleNamespace(**kwargs)

    monkeypatch.setattr(news_core, "LlmAgent", fake_llm_agent)

    llm_agent = agent.create_news_agent()

    assert created_models, "Gemini should be instantiated"
    assert created_models[0].model == "gemini-2.5-flash-lite"
    assert created_models[0].retry_options is news_core.retry_config

    assert created_agents, "LlmAgent should be instantiated"
    call_kwargs = created_agents[0]
    assert call_kwargs["name"] == "NewsAgent"
    assert call_kwargs["model"] is created_models[0]
    assert "helpful news assistant" in call_kwargs["instruction"]
    assert call_kwargs["tools"] == [news_core.google_search]
    assert llm_agent.name == "NewsAgent"
