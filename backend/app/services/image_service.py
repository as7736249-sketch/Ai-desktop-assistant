"""
Image Chat — upload an image and ask AI about it.

Uses Ollama with a vision model (llava, moondream, or bakllava).
Falls back gracefully if no vision model is installed.
"""
import base64
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)


class ImageService:
    """Stores uploaded images and chats about them via vision LLM."""

    # Preferred vision model, in order
    VISION_MODELS = ["llava:latest", "llava", "moondream", "bakllava"]

    def __init__(self):
        self.images: dict[str, bytes] = {}   # filename → bytes
        self.active: Optional[str] = None
        self._store = settings.uploads_dir
        self._vision_model: Optional[str] = None
        self._client = None  # created lazily so a missing 'ollama' pkg can't crash startup
        self._reload_existing()

    def _get_client(self):
        """Lazily create the Ollama client (vision chat is optional)."""
        if self._client is None:
            import ollama
            self._client = ollama.Client(host=settings.OLLAMA_BASE_URL,
                                         timeout=settings.LLM_TIMEOUT_SEC)
        return self._client

    def _reload_existing(self):
        for img in self._store.glob("*"):
            if img.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                try:
                    self.images[img.name] = img.read_bytes()
                except Exception as e:
                    log.warning("Could not load image %s: %s", img.name, e)

    def _detect_vision_model(self) -> Optional[str]:
        """Find first available vision-capable model."""
        if self._vision_model:
            return self._vision_model
        try:
            import requests
            r = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3)
            available = {m["name"] for m in r.json().get("models", [])}
            for candidate in self.VISION_MODELS:
                if candidate in available:
                    self._vision_model = candidate
                    log.info("Vision model detected: %s", candidate)
                    return candidate
                # Match by prefix (e.g., "llava" matches "llava:7b")
                for name in available:
                    if name.startswith(candidate.split(":")[0]):
                        self._vision_model = name
                        log.info("Vision model detected: %s", name)
                        return name
        except Exception as e:
            log.warning("Could not detect vision model: %s", e)
        return None

    def upload(self, filename: str, content: bytes) -> dict:
        ext = Path(filename).suffix.lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise ValueError("Only PNG, JPG, JPEG, WEBP images are allowed")
        safe = Path(filename).name
        path = self._store / safe
        path.write_bytes(content)
        self.images[safe] = content
        self.active = safe
        log.info("Image uploaded: %s (%d bytes)", safe, len(content))
        return {
            "filename": safe,
            "size": len(content),
            "b64_preview": "data:image/{};base64,{}".format(
                ext.strip(".") if ext != ".jpg" else "jpeg",
                base64.b64encode(content).decode("ascii")
            )[:80] + "...",
        }

    def list_all(self):
        return [
            {"filename": name, "size": len(data),
             "active": name == self.active}
            for name, data in self.images.items()
        ]

    def set_active(self, filename: str) -> bool:
        if filename == "___none___":
            self.active = None
            return True
        if filename in self.images:
            self.active = filename
            return True
        return False

    def delete(self, filename: str) -> bool:
        if filename not in self.images:
            return False
        del self.images[filename]
        (self._store / filename).unlink(missing_ok=True)
        if self.active == filename:
            self.active = None
        return True

    def ask(self, question: str) -> str:
        if not self.active:
            return "No image is active. Upload one first."
        model = self._detect_vision_model()
        if not model:
            return (
                "No vision model installed. Run: ollama pull llava "
                "(≈4 GB download, one-time)."
            )
        img_bytes = self.images.get(self.active)
        if not img_bytes:
            return "Image data missing."
        try:
            client = self._get_client()
            response = client.chat(
                model=model,
                messages=[{
                    "role": "user",
                    "content": question or "Describe this image in detail.",
                    "images": [base64.b64encode(img_bytes).decode("ascii")],
                }],
            )
            return response["message"]["content"].strip()
        except Exception as e:
            log.error("Image chat failed: %s", e)
            return f"Sorry, image chat failed: {e}"


image_service = ImageService()
