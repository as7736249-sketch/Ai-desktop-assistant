"""
PDF Chat Service — upload a PDF, extract text, chat with it (RAG-lite).
"""
from pathlib import Path
from typing import Dict, Optional

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)


class PDFService:
    def __init__(self):
        self.documents: Dict[str, str] = {}
        self.active: Optional[str] = None
        self._store = settings.uploads_dir
        # Load any PDFs that were previously uploaded
        self._reload_existing()

    def _reload_existing(self):
        """Re-scan uploads folder on startup."""
        for pdf in self._store.glob("*.pdf"):
            try:
                self.documents[pdf.name] = self.extract_text(pdf)
                log.info("Loaded existing PDF: %s", pdf.name)
            except Exception as e:
                log.warning("Skipping bad PDF %s: %s", pdf.name, e)

    def extract_text(self, pdf_path: Path) -> str:
        """Extract all text from a PDF."""
        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError("pypdf not installed — run: pip install pypdf")

        try:
            reader = PdfReader(str(pdf_path))
        except Exception as e:
            raise RuntimeError(f"Could not open PDF: {e}")

        chunks = []
        for i, page in enumerate(reader.pages):
            try:
                txt = page.extract_text() or ""
                if txt.strip():
                    chunks.append(f"[Page {i+1}]\n{txt}")
            except Exception as e:
                log.warning("PDF page %d extract failed: %s", i + 1, e)
        return "\n\n".join(chunks)

    def upload(self, filename: str, content_bytes: bytes) -> dict:
        # Sanitize filename
        safe = Path(filename).name.replace("\\", "").replace("/", "")
        if not safe.lower().endswith(".pdf"):
            raise ValueError("Only .pdf files allowed")

        path = self._store / safe
        path.write_bytes(content_bytes)

        text = self.extract_text(path)
        if not text.strip():
            raise ValueError(
                "This PDF contains no extractable text. "
                "It may be a scanned image — try OCR software first."
            )

        self.documents[safe] = text
        self.active = safe

        log.info("PDF uploaded: %s (%d chars extracted)", safe, len(text))
        return {
            "filename": safe,
            "chars": len(text),
            "pages": text.count("[Page "),
            "preview": (text[:200].strip() + "...") if len(text) > 200 else text,
        }

    def list_docs(self):
        return [
            {
                "filename": name,
                "chars": len(txt),
                "active": name == self.active,
            }
            for name, txt in self.documents.items()
        ]

    def set_active(self, filename: str) -> bool:
        if filename in self.documents:
            self.active = filename
            return True
        if filename == "___none___":
            self.active = None
            return True
        return False

    def delete(self, filename: str) -> bool:
        if filename not in self.documents:
            return False
        del self.documents[filename]
        try:
            (self._store / filename).unlink(missing_ok=True)
        except Exception as e:
            log.warning("Could not delete %s: %s", filename, e)
        if self.active == filename:
            self.active = None
        return True

    def get_context(self, query: str = "") -> str:
        """Return active document text. Future: vector search on `query`."""
        if not self.active:
            return ""
        return self.documents.get(self.active, "")


pdf_service = PDFService()
