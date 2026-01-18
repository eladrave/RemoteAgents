# RemoteAgents

Agentic LangGraph app with a local CLI chat client and remote agents running in Docker.  
Remote agents: Orchestrator, Search, Code Interpreter, Document (PDF).

## Requirements
- Python 3.11+
- Docker + Docker Compose

## Project layout
- `cli/` local terminal chat client
- `agents/` remote LangGraph agent servers
- `registry/agents.yaml` registry used by the orchestrator
- `artifacts/` generated files (PDFs, code outputs)

## Environment variables
Each component has its own `.env`:
- `cli/.env`
- `agents/orchestrator/.env`
- `agents/search/.env`
- `agents/code_interpreter/.env`
- `agents/document/.env`
Fill in required API keys for OpenAI, Gemini, and Tavily where applicable.

Defaults:
- OpenAI model: `gpt-5.2`
- Gemini model: `gemini-3-pro-preview`

The orchestrator uses LiteLLM so you can switch providers by changing model names and keys.

## Run the remote agents (Docker)
Build fresh images and start the stack:
```
docker compose build --no-cache
docker compose up -d
```

Stop:
```
docker compose down
```

## Run the CLI (local)
```
python -m venv .venv
source .venv/bin/activate
pip install -r cli/requirements.txt
python cli/main.py
```

Type `exit` or `quit` to leave.

## Code interpreter providers
The code interpreter agent supports three backends:
1. OpenAI Code Interpreter (Responses API tool): set `CODE_EXECUTION_PROVIDER=openai`.
2. Gemini Code Execution: set `CODE_EXECUTION_PROVIDER=gemini`.
3. Local Python sandbox: set `CODE_EXECUTION_PROVIDER=local` and pass `code` in input.

References:
https://platform.openai.com/docs/guides/tools-code-interpreter  
https://ai.google.dev/gemini-api/docs/code-execution  
https://docs.litellm.ai/docs/guides/code_interpreter

## Registry
Edit `registry/agents.yaml` to add new agents. The orchestrator loads this file at startup.

## Testing
Run tests with timeouts to prevent hangs:
```
pip install -r requirements.txt
pip install -r requirements-dev.txt
timeout 120s python -m pytest -q
```

## Runbook
Detailed run instructions are in `RUNBOOK.md`.
