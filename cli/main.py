import asyncio
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from langgraph_sdk import get_client


async def main() -> None:
    load_dotenv()
    console = Console()

    orchestrator_url = os.getenv("LANGGRAPH_ORCHESTRATOR_URL", "http://localhost:2024")
    api_key = os.getenv("LANGGRAPH_API_KEY") or None
    auth_scheme = os.getenv("LANGGRAPH_AUTH_SCHEME") or None

    headers = {}
    if auth_scheme:
        headers["X-Auth-Scheme"] = auth_scheme

    client = get_client(url=orchestrator_url, api_key=api_key, headers=headers)

    console.print(Panel(f"Connected to orchestrator at {orchestrator_url}", title="RemoteAgents CLI"))
    thread = await client.threads.create()
    thread_id = thread["thread_id"]
    assistant_id = "orchestrator"

    while True:
        user_input = Prompt.ask("\n[bold]You[/bold]")
        if user_input.strip().lower() in {"exit", "quit"}:
            console.print("Goodbye!")
            break

        result = await client.runs.wait(
            thread_id,
            assistant_id,
            input={"user_request": user_input},
        )
        console.print(Panel(result.get("final_response", "(no response)"), title="Orchestrator"))


if __name__ == "__main__":
    asyncio.run(main())
