import asyncio
import json
import os
from typing import Any, Dict, List, Optional, TypedDict

import yaml
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph_sdk import get_client
import litellm


load_dotenv()


class Task(TypedDict):
    agent_id: str
    instruction: str
    input: Dict[str, Any]


class State(TypedDict):
    user_request: str
    plan: Optional[Dict[str, Any]]
    tasks: List[Task]
    results: Dict[str, Any]
    final_response: str


def load_registry() -> Dict[str, Any]:
    path = os.getenv("AGENT_REGISTRY_PATH", "/app/registry/agents.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


async def llm_json(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    model = os.getenv("LLM_MODEL", "gpt-5.2")
    try:
        response = await litellm.acompletion(model=model, messages=messages)
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception:
        return {}


async def llm_text(messages: List[Dict[str, str]]) -> str:
    model = os.getenv("LLM_MODEL", "gpt-5.2")
    try:
        response = await litellm.acompletion(model=model, messages=messages)
        return response.choices[0].message.content or ""
    except Exception:
        return "LLM unavailable. Returning aggregated results without synthesis."


async def plan_node(state: State) -> Dict[str, Any]:
    registry = load_registry()
    agents = [a for a in registry.get("agents", []) if a.get("id") != "orchestrator"]
    system = (
        "You are an orchestrator. Create a short plan and a list of tasks for agents. "
        "Return JSON with keys: plan (string) and tasks (array). Each task: "
        "{agent_id, instruction, input}. Use only available agent ids."
    )
    user = {
        "role": "user",
        "content": f"User request: {state['user_request']}\nAvailable agents: {agents}",
    }
    plan_json = await llm_json([{"role": "system", "content": system}, user])

    raw_tasks = plan_json.get("tasks", [])
    tasks: List[Task] = []
    if isinstance(raw_tasks, list):
        for t in raw_tasks:
            if isinstance(t, dict) and "agent_id" in t:
                tasks.append(
                    {
                        "agent_id": t.get("agent_id"),
                        "instruction": t.get("instruction", ""),
                        "input": t.get("input", {}),
                    }
                )
    if not tasks:
        for agent in agents:
            if agent.get("id") == "search":
                tasks.append(
                    {
                        "agent_id": "search",
                        "instruction": "Search the web for relevant info.",
                        "input": {"query": state["user_request"], "max_results": 5},
                    }
                )
    return {"plan": {"plan": plan_json.get("plan", "")}, "tasks": tasks, "results": {}}


async def dispatch_node(state: State) -> Dict[str, Any]:
    registry = load_registry()
    agent_map = {a["id"]: a for a in registry.get("agents", [])}

    async def run_task(task: Task) -> Dict[str, Any]:
        try:
            agent_id = task["agent_id"]
            agent = agent_map.get(agent_id)
            if not agent:
                return {agent_id: {"error": "Unknown agent"}}
            url = agent["url"]
            client = get_client(url=url)
            thread = await client.threads.create()
            result = await client.runs.wait(
                thread["thread_id"],
                agent_id,
                input=task.get("input", {}),
            )
            return {agent_id: result}
        except Exception as e:
            return {task.get("agent_id", "unknown"): {"error": str(e)}}

    results: Dict[str, Any] = {}
    responses = await asyncio.gather(*(run_task(t) for t in state["tasks"]))
    for r in responses:
        results.update(r)
    return {"results": results}


async def aggregate_node(state: State) -> Dict[str, Any]:
    system = (
        "Combine agent results into a final response. Be concise and actionable."
    )
    user = {
        "role": "user",
        "content": json.dumps(
            {"request": state["user_request"], "results": state["results"]},
            indent=2,
        ),
    }
    final_response = await llm_text([{"role": "system", "content": system}, user])
    return {"final_response": final_response}


builder = StateGraph(State)
builder.add_node("plan", plan_node)
builder.add_node("dispatch", dispatch_node)
builder.add_node("aggregate", aggregate_node)
builder.add_edge(START, "plan")
builder.add_edge("plan", "dispatch")
builder.add_edge("dispatch", "aggregate")
builder.add_edge("aggregate", END)

graph = builder.compile()
