"""FastAPI routes for Jarvis."""
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.logger import get_logger
from app.core.i18n import lang_manager, LANG_NAMES, LanguageManager
from app.services.command_service import command_service
from app.services.llm_service import llm_service
from app.services.notes_service import notes_service
from app.services.pdf_service import pdf_service
from app.services.image_service import image_service
from app.services.calendar_service import calendar_service
from app.services.stats_service import stats_service
from app.services.export_service import export_service
from app.services.image_gen_service import image_gen_service
from app.services.websearch_service import websearch_service

log = get_logger(__name__)
router = APIRouter()


# ═══════════════════ CHAT ═══════════════════
class ChatIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    auto_detect_lang: bool = True


class ChatOut(BaseModel):
    user: str
    reply: str
    source: str
    detected_lang: str


@router.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn):
    user_text = payload.text.strip()

    # Auto-detect language from script
    detected = LanguageManager.detect(user_text)
    if payload.auto_detect_lang and detected != lang_manager.current:
        lang_manager.set(detected)
        log.info("🌐 Auto-switched language to '%s'", detected)

    log.info("💬 [%s] %s", lang_manager.current, user_text[:100])

    reply = command_service.handle(user_text)
    source = "command"

    if not reply:
        reply = llm_service.chat(user_text)
        source = "llm"
        stats_service.track("llm", is_llm=True)

    return ChatOut(
        user=user_text,
        reply=reply or "…",
        source=source,
        detected_lang=lang_manager.current,
    )


@router.post("/chat/stream")
def chat_stream(payload: ChatIn):
    """Server-Sent Events for typing effect."""
    user_text = payload.text.strip()
    detected = LanguageManager.detect(user_text)
    if payload.auto_detect_lang and detected != lang_manager.current:
        lang_manager.set(detected)

    # First check command router (returns full text, no streaming needed)
    cmd_reply = command_service.handle(user_text)
    if cmd_reply:
        def command_gen():
            # Split into chunks for a "typing" feel
            words = cmd_reply.split(" ")
            for i, w in enumerate(words):
                chunk = w + (" " if i < len(words) - 1 else "")
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(command_gen(), media_type="text/event-stream")

    stats_service.track("llm", is_llm=True)

    def llm_gen():
        for chunk in llm_service.chat_stream(user_text):
            # Escape newlines for SSE
            safe = chunk.replace("\n", "\\n")
            yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(llm_gen(), media_type="text/event-stream")


# ═══════════════════ PERSONALITY ═══════════════════
class PersonalityIn(BaseModel):
    name: str


@router.get("/personalities")
def get_personalities():
    return {
        "current": llm_service.personality,
        "available": llm_service.get_available_personalities(),
    }


@router.post("/personality")
def set_personality(payload: PersonalityIn):
    if not llm_service.set_personality(payload.name):
        raise HTTPException(status_code=400, detail=f"Unknown personality: {payload.name}")
    return {"ok": True, "current": llm_service.personality}


# ═══════════════════ LANGUAGE ═══════════════════
class LanguageIn(BaseModel):
    lang: str


@router.get("/language")
def get_language():
    return {"current": lang_manager.current, "available": LANG_NAMES}


@router.post("/language")
def set_language(payload: LanguageIn):
    if not lang_manager.set(payload.lang):
        raise HTTPException(status_code=400, detail=f"Unsupported language: {payload.lang}")
    llm_service.clear_history()
    return {"ok": True, "current": lang_manager.current}


# ═══════════════════ NOTES ═══════════════════
class NoteIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


@router.get("/notes")
def list_notes():
    return notes_service.list_all()


@router.post("/notes")
def add_note(payload: NoteIn):
    return {"ok": True, "message": notes_service.add(payload.text)}


@router.post("/notes/{note_id}/toggle")
def toggle_note(note_id: int):
    if not notes_service.toggle(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    return {"ok": True}


@router.delete("/notes/{note_id}")
def delete_note(note_id: int):
    if not notes_service.delete(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    return {"ok": True}


@router.delete("/notes")
def clear_notes():
    notes_service.clear()
    return {"ok": True}


# ═══════════════════ PDF ═══════════════════
MAX_UPLOAD = 25 * 1024 * 1024


@router.post("/pdf/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files allowed")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > MAX_UPLOAD:
        raise HTTPException(status_code=400, detail="PDF too large (max 25 MB)")
    try:
        return {"ok": True, **pdf_service.upload(file.filename, content)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.exception("PDF upload failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf")
def list_pdfs():
    return {"active": pdf_service.active, "documents": pdf_service.list_docs()}


class SelectIn(BaseModel):
    filename: str


@router.post("/pdf/select")
def select_pdf(payload: SelectIn):
    if not pdf_service.set_active(payload.filename):
        raise HTTPException(status_code=404, detail="PDF not found")
    return {"ok": True, "active": pdf_service.active}


@router.delete("/pdf/{filename}")
def delete_pdf(filename: str):
    if not pdf_service.delete(filename):
        raise HTTPException(status_code=404, detail="PDF not found")
    return {"ok": True}


# ═══════════════════ IMAGE CHAT ═══════════════════
@router.post("/image/upload")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > MAX_UPLOAD:
        raise HTTPException(status_code=400, detail="Image too large (max 25 MB)")
    try:
        return {"ok": True, **image_service.upload(file.filename, content)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/image")
def list_images():
    return {"active": image_service.active, "images": image_service.list_all()}


@router.post("/image/select")
def select_image(payload: SelectIn):
    if not image_service.set_active(payload.filename):
        raise HTTPException(status_code=404, detail="Image not found")
    return {"ok": True, "active": image_service.active}


@router.delete("/image/{filename}")
def delete_image(filename: str):
    if not image_service.delete(filename):
        raise HTTPException(status_code=404, detail="Image not found")
    return {"ok": True}


# ═══════════════════ CALENDAR ═══════════════════
@router.get("/calendar/status")
def calendar_status():
    return {"enabled": calendar_service.enabled, "message": calendar_service.setup_message}


# ═══════════════════ STATS ═══════════════════
@router.get("/stats")
def get_stats():
    return stats_service.get()


@router.delete("/stats")
def reset_stats():
    stats_service.reset()
    return {"ok": True}


# ═══════════════════ EXPORT ═══════════════════
class ExportIn(BaseModel):
    messages: List[dict]


@router.post("/export/markdown")
def export_markdown(payload: ExportIn):
    md = export_service.to_markdown(payload.messages)
    from datetime import datetime
    filename = f"jarvis_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    from fastapi.responses import Response
    return Response(
        content=md,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ═══════════════════ IMAGE GENERATION ═══════════════════
class ImgGenIn(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    width: int = 1024
    height: int = 1024


@router.post("/imagegen")
def generate_image(payload: ImgGenIn):
    try:
        return {"ok": True, **image_gen_service.generate(
            payload.prompt, payload.width, payload.height
        )}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/imagegen/recent")
def recent_generations():
    return image_gen_service.list_recent()


# ═══════════════════ WEB SEARCH ═══════════════════
class SearchIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=300)


@router.post("/search")
def web_search(payload: SearchIn):
    return {"result": websearch_service.search(payload.query)}


# ═══════════════════ LLM SETTINGS ═══════════════════
class LLMConfigIn(BaseModel):
    provider: str = "auto"
    api_key: str = ""
    model: str = ""


@router.get("/llm/status")
def llm_status():
    return llm_service.status()


@router.post("/llm/config")
def llm_config(payload: LLMConfigIn):
    """Save provider + key + model at runtime and persist to backend/.env."""
    llm_service.configure(payload.provider, payload.api_key, payload.model)
    _persist_env({
        "LLM_PROVIDER": payload.provider,
        "LLM_API_KEY": payload.api_key,
        "LLM_MODEL": payload.model,
    })
    return {"ok": True, **llm_service.status()}


@router.post("/llm/test")
def llm_test():
    return llm_service.test()


def _persist_env(values: dict) -> None:
    """Write/refresh keys in backend/.env without disturbing other lines."""
    from app.core.config import ENV_FILE
    try:
        lines = []
        if ENV_FILE.exists():
            lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        seen = set()
        out = []
        for line in lines:
            key = line.split("=", 1)[0].strip()
            if key in values and "=" in line and not line.strip().startswith("#"):
                out.append(f"{key}={values[key]}")
                seen.add(key)
            else:
                out.append(line)
        for k, v in values.items():
            if k not in seen:
                out.append(f"{k}={v}")
        ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    except Exception as e:
        log.warning("Could not persist .env: %s", e)


# ═══════════════════ HEALTH ═══════════════════
@router.get("/health")
def health():
    st = llm_service.status()
    return {
        "status": "ok",
        "version": "5.1.0",
        "lang": lang_manager.current,
        "personality": llm_service.personality,
        "llm_ok": st["ok"],
        "llm_provider": st["provider"],
        "llm_model": st["model"],
        "llm_key_set": st["key_set"],
        "calendar_ok": calendar_service.enabled,
        "active_pdf": pdf_service.active,
        "active_image": image_service.active,
        "pdf_count": len(pdf_service.documents),
        "image_count": len(image_service.images),
    }
