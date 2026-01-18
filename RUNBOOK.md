# RemoteAgents Runbook (Detailed)

## Overview
RemoteAgents consists of a **local CLI** and **remote LangGraph agent servers**.  
You must run all remote agents (Docker containers) before using the CLI.

Remote agents:
- Orchestrator (port 2024)
- Search (port 2025)
- Code Interpreter (port 2026)
- Document (port 2027)

The orchestrator loads agent endpoints from `registry/agents.yaml`.  
You **must** update this registry if the agent URLs change (for example, when deploying to remote hosts).

## 1) Configure environment files
Each component has its own `.env`:
- `cli/.env`
- `agents/orchestrator/.env`
- `agents/search/.env`
- `agents/code_interpreter/.env`
- `agents/document/.env`

Set API keys:
- `OPENAI_API_KEY` for OpenAI
- `GEMINI_API_KEY` for Gemini
- `TAVILY_API_KEY` for search

Defaults:
- OpenAI model: `gpt-5.2`
- Gemini model: `gemini-3-pro-preview`

## 2) Update the registry (required)
Open `registry/agents.yaml` and confirm the URLs.  
Example local values:
```
orchestrator: http://localhost:2024
search:       http://localhost:2025
code_interp:  http://localhost:2026
document:     http://localhost:2027
```

If you run agents on remote machines, update each URL to the correct host:
```
orchestrator: http://<orch-host>:2024
search:       http://<search-host>:2025
code_interp:  http://<code-host>:2026
document:     http://<doc-host>:2027
```

## 3) Start all agents (Docker)
Build and run all containers:
```
docker compose build --no-cache
docker compose up -d
```

Verify containers are running:
```
docker ps
```

## 4) Run the CLI (local machine)
```
python -m venv .venv
source .venv/bin/activate
pip install -r cli/requirements.txt
python cli/main.py
```

The CLI will connect to the orchestrator URL in `cli/.env`.

## 5) Run tests (local)
```
pip install -r requirements.txt
pip install -r requirements-dev.txt
timeout 120s python -m pytest -q
```

## 6) CI (regression)
GitHub Actions runs the test suite on every push and PR:
- Workflow: `.github/workflows/ci.yml`

## Notes
- The orchestrator **must** be running before the CLI can be used.
- If you change any agent ports or deploy to remote hosts, **update `registry/agents.yaml`**.
