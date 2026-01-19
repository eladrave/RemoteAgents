# Monkey‑patching LangGraph HTTP (Client & Server)

## Summary (what to patch)
**Client side (LangGraph SDK):** Patch `httpx.Client.request` and `httpx.AsyncClient.request` to intercept every outgoing request made by the SDK.  
**Server side (langgraph-api dev server):** Patch the ASGI app with middleware to intercept inbound requests and responses.

Use these to store request/response payloads in your DB. For simplicity, the examples below append JSON lines to a log file.

---

## Client‑side monkey patch (sync + async)
This captures all HTTPX requests (including those made by LangGraph SDK clients) and logs request/response data.

Save as `tools/httpx_patch.py` (or embed directly in your app before you create the SDK client).

```python
# path=null start=null
import json
import time
import httpx

LOG_PATH = "httpx_client_log.jsonl"


def _write_log(entry: dict) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


_orig_request = httpx.Client.request


def _patched_request(self, method, url, *args, **kwargs):
    start = time.time()
    req_body = None
    if "json" in kwargs:
        req_body = kwargs.get("json")
    elif "content" in kwargs:
        req_body = kwargs.get("content")
    elif "data" in kwargs:
        req_body = kwargs.get("data")

    try:
        resp = _orig_request(self, method, url, *args, **kwargs)
        elapsed_ms = int((time.time() - start) * 1000)
        entry = {
            "ts": time.time(),
            "method": method,
            "url": str(url),
            "request_body": req_body,
            "status_code": resp.status_code,
            "response_text": resp.text,
            "elapsed_ms": elapsed_ms,
        }
        _write_log(entry)
        return resp
    except Exception as e:
        _write_log(
            {
                "ts": time.time(),
                "method": method,
                "url": str(url),
                "request_body": req_body,
                "error": str(e),
            }
        )
        raise


httpx.Client.request = _patched_request


_orig_async_request = httpx.AsyncClient.request


async def _patched_async_request(self, method, url, *args, **kwargs):
    start = time.time()
    req_body = None
    if "json" in kwargs:
        req_body = kwargs.get("json")
    elif "content" in kwargs:
        req_body = kwargs.get("content")
    elif "data" in kwargs:
        req_body = kwargs.get("data")

    try:
        resp = await _orig_async_request(self, method, url, *args, **kwargs)
        elapsed_ms = int((time.time() - start) * 1000)
        entry = {
            "ts": time.time(),
            "method": method,
            "url": str(url),
            "request_body": req_body,
            "status_code": resp.status_code,
            "response_text": resp.text,
            "elapsed_ms": elapsed_ms,
        }
        _write_log(entry)
        return resp
    except Exception as e:
        _write_log(
            {
                "ts": time.time(),
                "method": method,
                "url": str(url),
                "request_body": req_body,
                "error": str(e),
            }
        )
        raise


httpx.AsyncClient.request = _patched_async_request
```

**Usage:**
```python
# path=null start=null
from tools.httpx_patch import *  # monkey-patches HTTPX
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")
# Run your normal SDK calls; requests will be logged to httpx_client_log.jsonl
```

---

## Client‑side targeted patch (optional)
If you want to patch only the SDK’s internal client (not global HTTPX), inspect the client to find the internal HTTPX object and patch that instance’s `.request()`.

```python
# path=null start=null
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")

# Inspect internal attributes to locate the httpx client
print([name for name in dir(client) if "client" in name.lower()])
```

Once you identify it (e.g., `_client`), patch `client._client.request` instead of global HTTPX.

---

## Server‑side monkey patch (ASGI middleware)
This wraps the server app and logs inbound request + outbound response.  
It works for FastAPI/Starlette ASGI apps.

Create a wrapper app (example, standalone ASGI):

```python
# path=null start=null
import json
import time
from typing import Callable

LOG_PATH = "asgi_server_log.jsonl"


def _write_log(entry: dict) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class LogMiddleware:
    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        body_parts = []

        async def _receive():
            message = await receive()
            if message.get("type") == "http.request":
                body_parts.append(message.get("body", b""))
            return message

        async def _send(message):
            if message.get("type") == "http.response.start":
                scope["_status"] = message.get("status")
            if message.get("type") == "http.response.body":
                if message.get("body"):
                    scope.setdefault("_resp_body", b"")
                    scope["_resp_body"] += message.get("body", b"")
            await send(message)

        start = time.time()
        await self.app(scope, _receive, _send)
        elapsed_ms = int((time.time() - start) * 1000)

        entry = {
            "ts": time.time(),
            "path": scope.get("path"),
            "method": scope.get("method"),
            "status": scope.get("_status"),
            "request_body": b"".join(body_parts).decode("utf-8", errors="ignore"),
            "response_body": (scope.get("_resp_body") or b"").decode("utf-8", errors="ignore"),
            "elapsed_ms": elapsed_ms,
        }
        _write_log(entry)


# Example: wrap a FastAPI app called `app`
# app = LogMiddleware(app)
```

**Where to insert:**
- If you control the server entrypoint, wrap the ASGI app right before it’s served.
- If you’re using `langgraph dev`, you can wrap its app by creating a custom ASGI entrypoint and running it with `uvicorn`, or by inserting middleware if you extend the server.

---

## Notes
- Logging full payloads can include sensitive data. Consider redaction.
- For large payloads, you may want to truncate before writing.
