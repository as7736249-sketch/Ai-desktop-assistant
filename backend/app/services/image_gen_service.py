"""
Image Generation Service — uses Pollinations.ai (FREE, no API key needed!).
Docs: https://pollinations.ai/
"""
import hashlib
from pathlib import Path
from urllib.parse import quote

import requests

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)


class ImageGenService:
    """Text-to-image generation using free Pollinations.ai API."""

    BASE = "https://image.pollinations.ai/prompt"

    def __init__(self):
        self._store = settings.uploads_dir / "generated"
        self._store.mkdir(parents=True, exist_ok=True)
        self.recent: list = []  # last 20 generations

    def generate(self, prompt: str, width: int = 1024, height: int = 1024,
                 model: str = "flux") -> dict:
        """
        Generate an image from a text prompt.
        Returns: {url, prompt, filename, local_path}
        """
        prompt = (prompt or "").strip()
        if not prompt:
            raise ValueError("Prompt is empty")

        # Deterministic filename from prompt hash
        digest = hashlib.md5(prompt.encode()).hexdigest()[:12]
        filename = f"gen_{digest}.jpg"
        local_path = self._store / filename

        url = (
            f"{self.BASE}/{quote(prompt)}"
            f"?width={width}&height={height}&model={model}&nologo=true"
        )

        try:
            log.info("🎨 Generating image: %s", prompt[:80])
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            local_path.write_bytes(r.content)

            entry = {
                "prompt": prompt,
                "filename": filename,
                "url": f"/uploads/generated/{filename}",  # served by main.py
                "size": len(r.content),
            }
            self.recent.insert(0, entry)
            self.recent = self.recent[:20]
            log.info("✅ Image generated: %s (%d KB)", filename, len(r.content) // 1024)
            return entry
        except requests.Timeout:
            raise RuntimeError("Image generation timed out (try shorter prompt)")
        except Exception as e:
            log.error("Image generation failed: %s", e)
            raise RuntimeError(f"Image generation failed: {e}")

    def list_recent(self):
        return self.recent

    def clear(self):
        for f in self._store.glob("*.jpg"):
            try: f.unlink()
            except: pass
        self.recent.clear()


image_gen_service = ImageGenService()
