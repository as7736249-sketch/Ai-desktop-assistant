"""
Internationalization (i18n) — English, Hindi, Punjabi.
"""

TRANSLATIONS = {
    "en": {
        "time_is": "The time is {value}",
        "today_is": "Today is {value}",
        "day_is": "Today is {value}",
        "opening": "Opening {value}",
        "playing_youtube": "Playing {value} on YouTube",
        "goodbye": "Goodbye! Have a great day.",
        "hello": "Hello! How can I help you today?",
        "no_notes": "You have no pending notes.",
        "note_added": "Added note: {value}",
        "notes_cleared": "All notes cleared.",
        "cannot_fetch": "Sorry, I couldn't fetch that right now.",
        "answer_is": "The answer is {value}",
        "llm_offline": "I'm having trouble reaching my brain. Please make sure Ollama is running.",
        "understand_error": "Sorry, I didn't understand that.",
        "no_input": "I didn't catch that. Please try again.",
    },
    "hi": {
        "time_is": "समय है {value}",
        "today_is": "आज है {value}",
        "day_is": "आज {value} है",
        "opening": "{value} खोल रहा हूँ",
        "playing_youtube": "YouTube पर {value} चला रहा हूँ",
        "goodbye": "अलविदा! आपका दिन शुभ हो।",
        "hello": "नमस्ते! मैं आपकी क्या मदद कर सकता हूँ?",
        "no_notes": "आपके पास कोई लंबित नोट नहीं है।",
        "note_added": "नोट जोड़ा गया: {value}",
        "notes_cleared": "सभी नोट्स हटा दिए गए।",
        "cannot_fetch": "क्षमा करें, मैं अभी वह जानकारी नहीं ला सका।",
        "answer_is": "उत्तर है {value}",
        "llm_offline": "मुझे अपने दिमाग तक पहुँचने में समस्या हो रही है। कृपया Ollama चालू करें।",
        "understand_error": "क्षमा करें, मैं समझ नहीं पाया।",
        "no_input": "मुझे सुनाई नहीं दिया। कृपया फिर कोशिश करें।",
    },
    "pa": {
        "time_is": "ਸਮਾਂ ਹੈ {value}",
        "today_is": "ਅੱਜ ਹੈ {value}",
        "day_is": "ਅੱਜ {value} ਹੈ",
        "opening": "{value} ਖੋਲ੍ਹ ਰਿਹਾ ਹਾਂ",
        "playing_youtube": "YouTube ਤੇ {value} ਚਲਾ ਰਿਹਾ ਹਾਂ",
        "goodbye": "ਅਲਵਿਦਾ! ਤੁਹਾਡਾ ਦਿਨ ਸ਼ੁਭ ਹੋਵੇ।",
        "hello": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ?",
        "no_notes": "ਤੁਹਾਡੇ ਕੋਲ ਕੋਈ ਬਾਕੀ ਨੋਟ ਨਹੀਂ ਹੈ।",
        "note_added": "ਨੋਟ ਜੋੜਿਆ ਗਿਆ: {value}",
        "notes_cleared": "ਸਾਰੇ ਨੋਟ ਹਟਾ ਦਿੱਤੇ ਗਏ।",
        "cannot_fetch": "ਮਾਫ਼ ਕਰਨਾ, ਮੈਂ ਹੁਣੇ ਉਹ ਜਾਣਕਾਰੀ ਨਹੀਂ ਲਿਆ ਸਕਿਆ।",
        "answer_is": "ਜਵਾਬ ਹੈ {value}",
        "llm_offline": "ਮੈਨੂੰ ਆਪਣੇ ਦਿਮਾਗ ਤੱਕ ਪਹੁੰਚਣ ਵਿੱਚ ਸਮੱਸਿਆ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ Ollama ਚਾਲੂ ਕਰੋ।",
        "understand_error": "ਮਾਫ਼ ਕਰਨਾ, ਮੈਂ ਸਮਝ ਨਹੀਂ ਸਕਿਆ।",
        "no_input": "ਮੈਨੂੰ ਸੁਣਾਈ ਨਹੀਂ ਦਿੱਤਾ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
    },
}

LANG_NAMES = {"en": "English", "hi": "हिंदी", "pa": "ਪੰਜਾਬੀ"}


class LanguageManager:
    def __init__(self):
        self.current: str = "en"

    def set(self, lang: str) -> bool:
        if lang in TRANSLATIONS:
            self.current = lang
            return True
        return False

    def t(self, key: str, value: str = "") -> str:
        d = TRANSLATIONS.get(self.current, TRANSLATIONS["en"])
        template = d.get(key) or TRANSLATIONS["en"].get(key, key)
        try:
            return template.format(value=value)
        except Exception:
            return template

    def instruction_for_llm(self) -> str:
        if self.current == "hi":
            return "IMPORTANT: Reply ONLY in Hindi (Devanagari script). Absolutely no English words."
        if self.current == "pa":
            return "IMPORTANT: Reply ONLY in Punjabi (Gurmukhi script). Absolutely no English words."
        return "Reply in English."

    @staticmethod
    def detect(text: str) -> str:
        """Auto-detect language from Unicode script."""
        for ch in text:
            code = ord(ch)
            # Devanagari (Hindi): U+0900–U+097F
            if 0x0900 <= code <= 0x097F:
                return "hi"
            # Gurmukhi (Punjabi): U+0A00–U+0A7F
            if 0x0A00 <= code <= 0x0A7F:
                return "pa"
        return "en"


lang_manager = LanguageManager()
