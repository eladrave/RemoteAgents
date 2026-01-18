import types
import pytest

from agents.orchestrator.src import app as orchestrator


@pytest.mark.asyncio
async def test_plan_node_fallback(monkeypatch):
    def fake_load_registry():
        return {
            "agents": [
                {"id": "orchestrator", "url": "http://localhost:2024"},
                {"id": "search", "url": "http://localhost:2025"},
            ]
        }

    async def fake_llm_json(messages):
        return {}

    monkeypatch.setattr(orchestrator, "load_registry", fake_load_registry)
    monkeypatch.setattr(orchestrator, "llm_json", fake_llm_json)

    state = {"user_request": "Find info about X", "plan": None, "tasks": [], "results": {}, "final_response": ""}
    result = await orchestrator.plan_node(state)
    assert result["tasks"], "Fallback should create a search task"
    assert result["tasks"][0]["agent_id"] == "search"


@pytest.mark.asyncio
async def test_dispatch_node(monkeypatch):
    def fake_load_registry():
        return {
            "agents": [
                {"id": "search", "url": "http://localhost:2025"},
            ]
        }

    class FakeClient:
        async def threads(self):
            return None

        class _Threads:
            async def create(self):
                return {"thread_id": "t1"}

        class _Runs:
            async def wait(self, thread_id, assistant_id, input):
                return {"results": [{"title": "A"}]}

        @property
        def threads(self):
            return self._Threads()

        @property
        def runs(self):
            return self._Runs()

    def fake_get_client(url):
        return FakeClient()

    monkeypatch.setattr(orchestrator, "load_registry", fake_load_registry)
    monkeypatch.setattr(orchestrator, "get_client", fake_get_client)

    state = {
        "user_request": "Find info about X",
        "plan": None,
        "tasks": [{"agent_id": "search", "instruction": "Search", "input": {"query": "X", "max_results": 1}}],
        "results": {},
        "final_response": "",
    }
    result = await orchestrator.dispatch_node(state)
    assert "search" in result["results"]


@pytest.mark.asyncio
async def test_aggregate_node(monkeypatch):
    async def fake_llm_text(messages):
        return "Final response"

    monkeypatch.setattr(orchestrator, "llm_text", fake_llm_text)
    state = {
        "user_request": "Summarize",
        "plan": None,
        "tasks": [],
        "results": {"search": {"results": [{"title": "A"}]}},
        "final_response": "",
    }
    result = await orchestrator.aggregate_node(state)
    assert result["final_response"] == "Final response"
