"""
Application entry point.

Modes:
  - Dev:    python -m app.main
  - Frozen: bundled by PyInstaller (uses sys._MEIPASS)
"""
import sys
import webbrowser
from pathlib import Path
from threading import Timer

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)


def _resource_path(rel: str) -> Path:
    """Locate a bundled resource in both dev and frozen mode."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / rel
    return Path(__file__).resolve().parent.parent.parent / rel


FRONTEND_DIR = _resource_path("frontend")

app = FastAPI(title=f"{settings.APP_NAME} API", version="5.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


# Global exception handler — never return a bare 500 with no info
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal error: {type(exc).__name__}: {exc}"},
    )


# Frontend static files
if FRONTEND_DIR.exists():
    (FRONTEND_DIR / "css").exists() and app.mount(
        "/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css"
    )
    (FRONTEND_DIR / "js").exists() and app.mount(
        "/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js"
    )
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
else:
    log.warning("Frontend dir not found: %s", FRONTEND_DIR)

# Serve uploaded/generated files so frontend can display them
if settings.uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")


# PWA manifest & service worker at root paths
@app.get("/manifest.webmanifest")
def manifest():
    m = FRONTEND_DIR / "manifest.webmanifest"
    if m.exists():
        return FileResponse(m, media_type="application/manifest+json")
    return JSONResponse({"error": "no manifest"}, status_code=404)


@app.get("/sw.js")
def service_worker():
    sw = FRONTEND_DIR / "sw.js"
    if sw.exists():
        return FileResponse(sw, media_type="application/javascript",
                            headers={"Service-Worker-Allowed": "/"})
    return JSONResponse({"error": "no sw"}, status_code=404)


@app.get("/")
def index():
    idx = FRONTEND_DIR / "index.html"
    if idx.exists():
        return FileResponse(idx)
    return JSONResponse({"error": "Frontend not built. See README."}, status_code=500)


@app.get("/favicon.ico")
def favicon():
    fav = FRONTEND_DIR / "assets" / "favicon.ico"
    if fav.exists():
        return FileResponse(fav)
    return JSONResponse({"detail": "no favicon"}, status_code=204)


def _open_browser():
    url = f"http://{settings.API_HOST}:{settings.API_PORT}"
    log.info("👉 Opening browser: %s", url)
    try:
        webbrowser.open(url)
    except Exception as e:
        log.warning("Auto-open browser failed: %s", e)


def _banner():
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║              {settings.APP_NAME:^32s}         ║
    ║        AI Desktop Assistant v5.1 PRO                 ║
    ╠══════════════════════════════════════════════════════╣
    ║  → http://{settings.API_HOST}:{settings.API_PORT}{'':<28s}║
    ║  → Open in Chrome or Edge for best voice support     ║
    ║  → Press Ctrl+C to stop                              ║
    ╚══════════════════════════════════════════════════════╝
    """)


def main():
    _banner()
    log.info("Starting %s | model=%s | port=%d",
             settings.APP_NAME, settings.OLLAMA_MODEL, settings.API_PORT)

    if settings.AUTO_OPEN_BROWSER:
        Timer(1.5, _open_browser).start()

    try:
        uvicorn.run(
            app,
            host=settings.API_HOST,
            port=settings.API_PORT,
            log_level="warning",
            access_log=False,
        )
    except OSError as e:
        if "address already in use" in str(e).lower() or "10048" in str(e):
            log.error(
                "❌ Port %d is already in use. Change API_PORT in .env or "
                "close the other program using it.", settings.API_PORT
            )
        else:
            raise


if __name__ == "__main__":
    main()
