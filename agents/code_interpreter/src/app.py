import os
import subprocess
import sys
from typing import Any, Dict, Optional, TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from openai import OpenAI
from google import genai
from google.genai import types


load_dotenv()


class State(TypedDict):
    task: str
    code: Optional[str]
    provider: Optional[str]
    output: Dict[str, Any]


def _openai_code_interpreter(task: str, model: str) -> Dict[str, Any]:
    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=task,
        tools=[{"type": "code_interpreter", "container": {"type": "auto"}}],
    )
    output_text = getattr(response, "output_text", None)
    if not output_text:
        output_text = ""
        for item in getattr(response, "output", []) or []:
            if item.get("type") == "output_text":
                output_text += item.get("text", "")
    return {"provider": "openai", "text": output_text, "raw": response.model_dump()}


def _gemini_code_execution(task: str, model: str) -> Dict[str, Any]:
    client = genai.Client()
    response = client.models.generate_content(
        model=model,
        contents=task,
        config=types.GenerateContentConfig(
            tools=[types.Tool(code_execution=types.ToolCodeExecution)]
        ),
    )
    return {"provider": "gemini", "text": response.text, "raw": response.model_dump()}


def _local_exec(code: str, timeout: int) -> Dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "provider": "local",
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "exit_code": proc.returncode,
    }


def code_node(state: State) -> Dict[str, Any]:
    provider = (state.get("provider") or os.getenv("CODE_EXECUTION_PROVIDER", "openai")).lower()
    timeout = int(os.getenv("EXEC_TIMEOUT", "30"))
    if provider == "openai":
        model = os.getenv("CODE_EXECUTION_MODEL", "gpt-5.2")
        return {"output": _openai_code_interpreter(state["task"], model)}
    if provider == "gemini":
        model = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")
        return {"output": _gemini_code_execution(state["task"], model)}
    if provider == "local":
        if not state.get("code"):
            return {"output": {"provider": "local", "error": "No code provided"}}
        return {"output": _local_exec(state["code"], timeout)}
    return {"output": {"error": f"Unknown provider: {provider}"}}


builder = StateGraph(State)
builder.add_node("code", code_node)
builder.add_edge(START, "code")
builder.add_edge("code", END)

graph = builder.compile()
