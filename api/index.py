"""
Vercel / serverless entrypoint for the Jarvis FastAPI (ASGI) app.

Vercel invokes `handler`. We adapt the ASGI app with Mangum and normalize the
incoming event so it works whether Vercel sends an API-Gateway **v1** event
(`httpMethod` + `path`), a **v2** event (`version: 2.0` + `rawPath`), or a
generic HTTP event. Nothing here affects the normal local run
(`python -m app.main` / START.bat).
"""
import os
import sys

# Make the backend package importable (repo_root/backend)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND = os.path.join(_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from app.main import app as fastapi_app  # noqa: E402

try:
    from mangum import Mangum
    _mangum = Mangum(fastapi_app, lifespan="off")
except Exception:  # pragma: no cover - mangum is in requirements.txt
    _mangum = None


def _normalize_event(event):
    """Return a complete API-Gateway v2-shaped event Mangum can always parse,
    regardless of whether Vercel sent a v1, v2 or generic HTTP event."""
    if not isinstance(event, dict):
        return event

    rc = event.get("requestContext") or {}
    http = (rc.get("http") or {}) if isinstance(rc, dict) else {}

    method = (event.get("httpMethod") or http.get("method")
              or event.get("method") or "GET")
    path = event.get("rawPath") or event.get("path") or http.get("path") or "/"

    # Split an inline query string off the path, if present
    raw_qs = event.get("rawQueryString") or ""
    if "?" in path:
        path, _, inline = path.partition("?")
        raw_qs = raw_qs or inline

    source_ip = (http.get("sourceIp")
                 or (rc.get("identity", {}) or {}).get("sourceIp")
                 or "0.0.0.0")

    # Flatten headers into a str->str map
    headers = event.get("headers") or {}
    flat_headers = {}
    if isinstance(headers, dict):
        for k, v in headers.items():
            flat_headers[str(k)] = v if isinstance(v, str) else str(v)

    qs = event.get("queryStringParameters")
    if not isinstance(qs, dict):
        qs = None

    return {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": raw_qs,
        "headers": flat_headers,
        "queryStringParameters": qs,
        "cookies": event.get("cookies") or [],
        "requestContext": {
            "http": {"method": method.upper(), "path": path,
                     "protocol": "HTTP/1.1", "sourceIp": source_ip},
            "stage": "$default",
        },
        "body": event.get("body"),
        "isBase64Encoded": bool(event.get("isBase64Encoded", False)),
    }


def handler(event, context=None):
    if _mangum is None:  # fallback safety
        return {"statusCode": 500,
                "body": "Serverless adapter (mangum) not installed."}
    return _mangum(_normalize_event(event), context)
