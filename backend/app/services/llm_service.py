"""
LLM Service — multi-provider AI brain for Jarvis.

Works TWO ways:
  1. FREE, out of the box, NO API key, NO local install
        -> uses Pollinations.ai (free OpenAI-compatible text API)
  2. Bring-your-own API key (better quality / speed)
        -> Groq, Google Gemini, OpenAI, OpenRouter
  3. 100% offline
        -> local Ollama (no key)

Provider is chosen in .env (or the in-app Settings box):
    LLM_PROVIDER = auto | pollinations | groq | gemini | openai | openrouter | ollama
    LLM_API_KEY  = <your key, optional>
    LLM_MODEL    = <optional model override>

With LLM_PROVIDER=auto (the default):
    - if LLM_API_KEY is set  -> provider is auto-detected from the key,
    - if no key              -> free Pollinations (always works).
Any provider failure automatically falls back to free Pollinations so the
assistant keeps replying instead of going silent.
"""
import json
import time
from typing import Dict, Iterator, List, Optional

import requests

from app.core.config import settings
from app.core.logger import get_logger
from app.core.i18n import lang_manager

log = get_logger(__name__)

# ──────────────────────────── Personalities ────────────────────────────
PERSONALITIES = {
    "jarvis": "You are Jarvis, a witty, sophisticated AI assistant. Address the user as 'sir' or 'boss'. Be clever and slightly sarcastic.",
    "friendly": "You are a warm, friendly desktop assistant. Be encouraging and casual — like a supportive friend.",
    "professional": "You are a professional executive assistant. Be crisp, formal, and precise. No emojis, no jokes.",
    "sassy": "You are a sassy, sarcastic AI with attitude. Roast the user lovingly but still answer their questions.",
    "teacher": "You are a patient, encouraging teacher. Explain concepts simply, use analogies.",
    "gen_z": "You are a Gen Z AI. Use slang like 'bro', 'no cap', 'lowkey', 'fr'. Be chill but helpful.",
}

# ──────────────────────────── Provider registry ────────────────────────────
# Every provider below speaks the OpenAI "/chat/completions" protocol, so one
# code path handles all of them — we only switch base URL + key + model.
PROVIDERS: Dict[str, dict] = {
    "pollinations": {
        "base": "https://text.pollinations.ai/openai",
        "model": "openai",
        "needs_key": False,
        "label": "Pollinations — free, no key needed",
    },
    "groq": {
        "base": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "needs_key": True,
        "label": "Groq — free API key from console.groq.com",
    },
    "gemini": {
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-2.0-flash",
        "needs_key": True,
        "label": "Google Gemini — free API key from aistudio.google.com",
    },
    "openai": {
        "base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "needs_key": True,
        "label": "OpenAI — paid key from platform.openai.com",
    },
    "openrouter": {
        "base": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "needs_key": True,
        "label": "OpenRouter — free key from openrouter.ai",
    },
    "ollama": {
        "base": "",  # filled from OLLAMA_BASE_URL at runtime
        "model": "",  # filled from OLLAMA_MODEL at runtime
        "needs_key": False,
        "label": "Ollama — local, offline, no key",
    },
}


def _detect_provider_from_key(key: str) -> Optional[str]:
    """Guess the provider from the API key prefix (used in 'auto' mode)."""
    k = (key or "").strip()
    if k.startswith("gsk_"):
        return "groq"
    if k.startswith("sk-or-"):
        return "openrouter"
    if k.startswith("sk-"):
        return "openai"
    if k.startswith("AIza"):
        return "gemini"
    return None


class LLMService:
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.personality: str = "jarvis"
        # provider runtime state (filled by _resolve_provider)
        self.provider: str = "pollinations"
        self.base_url: str = ""
        self.model: str = ""
        self.api_key: str = ""
        self._last_error: str = ""
        self._ok: bool = True  # optimistic until a call proves otherwise
        self._resolve_provider()
        log.info("LLM ready — provider=%s | model=%s | key=%s",
                 self.provider, self.model, "yes" if self.api_key else "no")

    # ── provider resolution ────────────────────────────────────────────
    def _resolve_provider(self) -> None:
        """Pick the provider from settings (auto-detects the key in 'auto' mode)."""
        provider = (settings.LLM_PROVIDER or "auto").lower().strip()
        key = (settings.LLM_API_KEY or "").strip()
        model = (settings.LLM_MODEL or "").strip()

        if provider == "auto":
            if key:
                provider = _detect_provider_from_key(key) or "groq"
            else:
                provider = "pollinations"

        if provider not in PROVIDERS:
            log.warning("Unknown LLM_PROVIDER '%s' — using free pollinations", provider)
            provider = "pollinations"

        self._use_provider(provider, key, model)

    def _use_provider(self, provider: str, key: str, model: str) -> None:
        """Apply a provider + key + model to the live client."""
        if provider not in PROVIDERS:
            provider = "pollinations"
        spec = PROVIDERS[provider]

        if provider == "ollama":
            base = settings.OLLAMA_BASE_URL.rstrip("/") + "/v1"
            default_model = settings.OLLAMA_MODEL
        else:
            base = spec["base"]
            default_model = spec["model"]

        self.provider = provider
        self.base_url = base
        self.model = (model or "").strip() or default_model
        # Only keep the key for providers that need one (avoid leaking it to the
        # free endpoint, though it is harmless there).
        self.api_key = key if spec["needs_key"] else ""

        if spec["needs_key"] and not self.api_key:
            self._last_error = (
                f"{provider} needs an API key. Add one in Settings, "
                f"or switch provider to 'pollinations' (free)."
            )
            self._ok = False
        else:
            self._last_error = ""
            self._ok = True

    def configure(self, provider: str, api_key: str = "", model: str = "") -> None:
        """Reconfigure at runtime (called by the Settings panel)."""
        self._use_provider((provider or "auto").lower().strip(),
                           (api_key or "").strip(), (model or "").strip())
        self.history.clear()
        log.info("LLM reconfigured — provider=%s | model=%s | key=%s",
                 self.provider, self.model, "yes" if self.api_key else "no")

    # ── personalities ──────────────────────────────────────────────────
    def set_personality(self, name: str) -> bool:
        name = (name or "").lower().strip()
        if name in PERSONALITIES:
            self.personality = name
            self.history.clear()
            return True
        return False

    def get_available_personalities(self) -> List[str]:
        return list(PERSONALITIES.keys())

    def _system_prompt(self) -> str:
        return (
            f"{PERSONALITIES[self.personality]} "
            "Reply in ONE or TWO short sentences. "
            "Plain text only — no markdown, no bullets, no code fences, no emojis. "
            f"{lang_manager.instruction_for_llm()}"
        )

    # ── low-level HTTP (OpenAI-compatible) ─────────────────────────────
    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        # OpenRouter likes an identifying referer; harmless for others.
        if self.provider == "openrouter":
            h["HTTP-Referer"] = "http://localhost"
            h["X-Title"] = "Jarvis"
        return h

    def _chat_url(self) -> str:
        return self.base_url.rstrip("/") + "/chat/completions"

    @staticmethod
    def _extract_error(r: "requests.Response") -> str:
        try:
            j = r.json()
            if isinstance(j, dict):
                err = j.get("error")
                if isinstance(err, dict):
                    return str(err.get("message") or err.get("code") or j)
                return str(err or j.get("message") or "")
        except Exception:
            pass
        return (r.text or "")[:200]

    def _complete(self, messages: List[Dict[str, str]]) -> str:
        """Blocking completion with light retry on transient rate-limits."""
        payload = {"model": self.model, "messages": messages, "temperature": 0.7}
        last_exc: Optional[Exception] = None
        for attempt in range(2):  # one retry on transient busy/5xx responses
            try:
                r = requests.post(self._chat_url(), headers=self._headers(),
                                  json=payload, timeout=settings.LLM_TIMEOUT_SEC)
                if r.status_code in (401, 403):
                    raise RuntimeError("API key rejected (401/403). Check the key in Settings.")
                if r.status_code == 402:
                    # Free-tier quota (e.g. Pollinations: 1 reply / 45s) — retry won't help now
                    raise RuntimeError("FREE_LIMIT: " + self._extract_error(r))
                if r.status_code in (429, 500, 502, 503, 504) and attempt == 0:
                    last_exc = RuntimeError(f"HTTP {r.status_code} (busy)")
                    time.sleep(1.5)
                    continue
                r.raise_for_status()
                data = r.json()
                return (data["choices"][0]["message"]["content"] or "").strip()
            except requests.exceptions.Timeout as e:
                last_exc = e
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                raise
        raise last_exc or RuntimeError("LLM request failed")

    def _friendly_error(self) -> str:
        """Turn the last error into a helpful, non-technical message."""
        e = (self._last_error or "").lower()
        if "key rejected" in e or "401" in e or "403" in e:
            return ("My AI key was rejected. Open ⚙️ AI Settings and paste a valid "
                    "key, or switch the provider to the free option.")
        if "free_limit" in e or "402" in e or "429" in e or "rate" in e or "busy" in e:
            return ("The free AI allows only ~1 reply every 45 seconds, so I'm briefly "
                    "rate-limited. Please wait a few seconds and try again — or add a "
                    "FREE Groq key in ⚙️ AI Settings (console.groq.com, ~2 min) for "
                    "fast, unlimited replies.")
        if "timeout" in e or "timed out" in e:
            return "The AI took too long to answer. Please try again."
        return ("I can't reach the AI right now. Check your internet connection, or "
                "open ⚙️ AI Settings to choose a provider.")

    def _complete_with_fallback(self, messages: List[Dict[str, str]]) -> str:
        """Try the active provider; on failure fall back to free Pollinations."""
        try:
            out = self._complete(messages)
            self._ok = True
            self._last_error = ""
            return out
        except Exception as e:
            self._last_error = str(e)
            self._ok = False
            log.warning("Provider '%s' failed: %s", self.provider, e)
            if self.provider == "pollinations":
                raise
            # one-shot fallback to the always-free endpoint
            prev = (self.provider, self.base_url, self.model, self.api_key)
            try:
                self._use_provider("pollinations", "", "")
                out = self._complete(messages)
                self._last_error = ""
                return out
            finally:
                # restore the user's chosen provider for the next attempt
                self.provider, self.base_url, self.model, self.api_key = prev

    # ── public chat API ────────────────────────────────────────────────
    def chat(self, user_message: str) -> str:
        if not user_message:
            return lang_manager.t("no_input")

        self.history.append({"role": "user", "content": user_message})
        self.history = self.history[-20:]
        messages = [{"role": "system", "content": self._system_prompt()}] + self.history

        try:
            reply = self._complete_with_fallback(messages)
        except Exception as e:
            log.error("LLM chat failed: %s", e)
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
            return self._friendly_error()

        if reply:
            self.history.append({"role": "assistant", "content": reply})
            log.info("🤖 [%s/%s] %s", self.personality, self.provider, reply[:80])
        return reply or self._friendly_error()

    def chat_with_context(self, user_message: str, context: str) -> str:
        """Answer using extra document/context info (RAG-lite)."""
        system = (
            f"{PERSONALITIES[self.personality]} "
            "Answer based ONLY on the CONTEXT below. If the answer isn't in the "
            "context, say so plainly. Reply in 1-3 sentences, plain text only. "
            f"{lang_manager.instruction_for_llm()}\n\nCONTEXT:\n{context[:6000]}"
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]
        try:
            return self._complete_with_fallback(messages) or self._friendly_error()
        except Exception as e:
            log.error("LLM context chat failed: %s", e)
            return self._friendly_error()

    def chat_stream(self, user_message: str) -> Iterator[str]:
        """Yield reply chunks for streaming to the frontend (SSE)."""
        if not user_message:
            yield lang_manager.t("no_input")
            return

        self.history.append({"role": "user", "content": user_message})
        self.history = self.history[-20:]
        messages = [{"role": "system", "content": self._system_prompt()}] + self.history

        collected: List[str] = []
        try:
            payload = {"model": self.model, "messages": messages,
                       "temperature": 0.7, "stream": True}
            r = requests.post(self._chat_url(), headers=self._headers(),
                             json=payload, timeout=settings.LLM_TIMEOUT_SEC, stream=True)
            if r.status_code in (401, 403):
                raise RuntimeError("API key rejected")
            r.raise_for_status()

            for line in r.iter_lines(decode_unicode=True):
                if not line:
                    continue
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    piece = delta.get("content") or ""
                except Exception:
                    piece = ""
                if piece:
                    collected.append(piece)
                    yield piece

            self._ok = True
            self._last_error = ""
        except Exception as e:
            log.warning("Stream failed on '%s' (%s) — falling back to full reply",
                        self.provider, e)
            try:
                full = self._complete_with_fallback(messages)
                if full:
                    collected = [full]
                    yield full
            except Exception as e2:
                self._last_error = str(e2)
                self._ok = False
                if self.history and self.history[-1]["role"] == "user":
                    self.history.pop()
                yield self._friendly_error()
                return

        # If the provider streamed nothing, try one blocking call
        if not collected:
            try:
                full = self._complete_with_fallback(messages)
                if full:
                    collected = [full]
                    yield full
            except Exception:
                pass

        full = "".join(collected).strip()
        if full:
            self.history.append({"role": "assistant", "content": full})
            log.info("🤖 [stream/%s/%s] %s", self.personality, self.provider, full[:80])

    # ── status / diagnostics ───────────────────────────────────────────
    def status(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "key_set": bool(self.api_key),
            "ok": self._ok,
            "last_error": self._last_error,
            "label": PROVIDERS[self.provider]["label"],
            "available": list(PROVIDERS.keys()),
        }

    def test(self) -> dict:
        """Send a tiny prompt to the *configured* provider (no silent fallback),
        so the user gets truthful feedback about whether their key works."""
        msgs = [{"role": "user", "content": "Reply with the single word: OK"}]
        try:
            out = self._complete(msgs)
            self._ok = True
            self._last_error = ""
            return {"ok": True, "provider": self.provider,
                    "model": self.model, "reply": out[:120]}
        except Exception as e:
            self._ok = False
            self._last_error = str(e)
            return {"ok": False, "provider": self.provider,
                    "model": self.model, "error": str(e)}

    def clear_history(self) -> None:
        self.history.clear()


llm_service = LLMService()
