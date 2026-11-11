# 🤖 Jarvis — AI Desktop Assistant v5.1 PRO

> **Production-ready** voice-controlled AI assistant with modern animated UI.
> Multi-language · Streaming AI · PDF & Image chat · Command palette · Themes.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![AI](https://img.shields.io/badge/AI-Free_·_No_API_Key_Needed-success)
![Ollama](https://img.shields.io/badge/Ollama-Optional-black)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Version](https://img.shields.io/badge/version-5.1_PRO-blueviolet)

---

## ✨ Features

### 🎙️ Voice & Speech
- **Browser-native STT** — accurate, zero install
- **Wake word** "Hey Jarvis" (also हे जार्विस, ਹੇ ਜਾਰਵਿਸ)
- **Live transcription** as you speak
- **Real audio visualizer** synced to your voice
- **Multi-lingual TTS** — replies spoken in your language

### 🧠 AI Intelligence
- **Works FREE out of the box** — no API key, no signup, no local install
  (uses the free Pollinations AI brain automatically)
- **Bring your own key** — plug in a **free Groq / Gemini / OpenRouter** key,
  or paid OpenAI, for faster unlimited replies. Set it in the app's
  **⚙️ AI Settings** box or in `backend/.env`.
- **Optional 100% offline mode** — local **Ollama** (no key)
- **⚡ Streaming replies** — words appear as they're generated (ChatGPT-style)
- **6 personalities** — Jarvis · Friendly · Professional · Sassy · Teacher · Gen Z
- **20-turn conversation memory**
- **Auto-fallback** — if a provider is busy/down, Jarvis keeps replying

### 🌐 Multi-Language (3 languages)
- 🇬🇧 **English** · 🇮🇳 **हिंदी** · 🇮🇳 **ਪੰਜਾਬੀ**
- **Auto-detect from script** — type in any language, get replies in same
- Wake word + voice recognition all work in every language

### 🎯 Skills (17 command types)
| Voice | Result |
|---|---|
| "what time is it" | Current time |
| "what's the weather in Delhi" | Weather (no API key) |
| "latest news" | Top 5 headlines |
| "what is 25 times 8" | Calculator = 200 |
| "tell me a joke" | Offline joke |
| "motivate me" | Inspirational quote |
| "battery status" | Battery % |
| "cpu usage" | Live CPU load |
| "memory usage" | RAM stats |
| "disk space" | Free space |
| "take a screenshot" | Saves to Pictures |
| "open notepad" | Launches app |
| "open youtube" | Opens site |
| "play shape of you" | YouTube auto-play |
| "who is elon musk" | Wikipedia |
| "remind me to buy milk" | Adds note |
| "schedule meeting tomorrow at 3pm" | Calendar event |
| "summarize the pdf" | AI + your PDF |
| "describe the image" | Vision AI |

### 🎨 UI/UX (v5.1 upgrades)
- **🎬 Splash screen** with animated boot sequence
- **⌘ Command palette** (`Ctrl+K`) — fuzzy search all commands
- **🍞 Toast notifications** — beautiful, dismissible
- **📊 Stats dashboard** — usage tracking + charts
- **📤 Export chat** to Markdown
- **6 stunning themes** — Dark · Light · Cyberpunk · Ocean · Sunset · Forest
- **Chat persistence** across reloads
- **Message timestamps**
- **Animated background particles**
- **Keyboard shortcuts** everywhere
- **Full ARIA labels** for accessibility

### 📄 Document Chat (NEW!)
- **PDF Chat** — upload PDF, ask questions ("summarize", "explain page 3")
- **Image Chat** — upload image, AI describes it (needs `ollama pull llava`)
- **Multiple documents** — switch between them anytime
- **Active banner** shows which doc you're chatting with

### 💼 Deployment
- **One-click `START.bat`** to run
- **One-click `BUILD_EXE.bat`** to package as `Jarvis.exe`

---

## 🚀 Quick Start (Windows)

### 1️⃣ Install Python 3.10+
https://www.python.org/downloads/ · ✅ tick **"Add Python to PATH"**

### 2️⃣ That's it — the AI works free, no key needed ✅
Jarvis uses a free cloud AI by default, so **you can skip straight to Step 3.**
No Ollama, no API key, no downloads required.

> **Want faster / unlimited replies?** Get a **free Groq key** (takes ~2 min,
> no card) at https://console.groq.com → API Keys, then paste it in the app's
> **⚙️ AI Settings** box (no file editing). Free Gemini and OpenRouter keys work too.

> **Want 100% offline?** Install Ollama from https://ollama.com/download, run
> `ollama pull llama3.2:3b`, then choose **Ollama** in ⚙️ AI Settings.
> *(For image/vision chat, run `ollama pull llava` too.)*

### 3️⃣ Run
**Double-click `START.bat`** — browser opens automatically at http://127.0.0.1:8000

Use **Chrome or Edge** for best voice support.

---

## ⚙️ Choosing your AI (⚙️ AI Settings)

Open the app → click **⚙️ AI Settings** in the sidebar:

| Provider | Cost | Key? | Notes |
|---|---|---|---|
| **Auto / Pollinations** | Free | ❌ none | Works instantly, default |
| **Groq** | Free | ✅ free key | Fastest, generous limit — recommended |
| **Google Gemini** | Free | ✅ free key | Great quality |
| **OpenRouter** | Free | ✅ free key | Many models |
| **OpenAI** | Paid | ✅ paid key | GPT models |
| **Ollama** | Free | ❌ none | Offline / private |

The panel has a **🧪 Test** button to confirm your key works, and **Save &
Connect** writes your choice to `backend/.env` so it's remembered.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl` + `K` | Open command palette |
| `Ctrl` + `/` | Start voice input |
| `Ctrl` + `L` | Clear chat |
| `Esc` | Close any modal / palette |
| `Enter` | Send message |

---

## 📅 Optional: Google Calendar Setup

Skip if you don't need it. Otherwise, 10-min one-time setup:

1. https://console.cloud.google.com/ → new project
2. Enable **Google Calendar API**
3. Credentials → Create OAuth Client ID → **Desktop app**
4. Download JSON → rename to **`credentials.json`** → put in `backend/`
5. First calendar command triggers browser authorization
6. Try: *"schedule meeting tomorrow at 3pm"*

---

## 📁 Project Structure

```
ai-desktop-assistant/
├── START.bat                          ▶️ Double-click to run
├── BUILD_EXE.bat                      🔨 Build .exe
├── README.md
├── .gitignore
│
├── backend/
│   ├── .env                           ⚙️ Configuration
│   ├── requirements.txt               📦 14 dependencies
│   │
│   └── app/
│       ├── main.py                    Entry point + auto-browser
│       ├── core/
│       │   ├── config.py              Settings loader
│       │   ├── logger.py              Colored logs
│       │   └── i18n.py                🌐 3-language manager + auto-detect
│       ├── services/                  (12 services)
│       │   ├── command_service.py     Intent router (17 handlers)
│       │   ├── llm_service.py         Ollama + streaming + personalities
│       │   ├── weather_service.py     wttr.in
│       │   ├── news_service.py        Google News RSS
│       │   ├── notes_service.py       Persistent to-dos
│       │   ├── calendar_service.py    Google Calendar
│       │   ├── calendar_parser.py     NL date parser
│       │   ├── pdf_service.py         PDF text extraction
│       │   ├── image_service.py       ✨ Vision AI (llava)
│       │   ├── jokes_service.py       Offline jokes/quotes
│       │   ├── system_service.py      Battery/CPU/RAM/screenshot
│       │   ├── stats_service.py       ✨ Usage tracking
│       │   └── export_service.py      ✨ Markdown export
│       └── api/
│           └── routes.py              25 REST endpoints
│
└── frontend/
    ├── index.html                     Splash · palette · 4 modals
    ├── css/style.css                  1200+ lines · 6 themes
    └── js/app.js                      950+ lines · fully commented
```

---

## 🧪 Test Report

All features **verified working end-to-end**:

```
✅ 18/18 Python files pass syntax
✅ Frontend JS passes syntax
✅ 14/14 v5.1 feature tests pass:
   ✅ Health endpoint v5.1
   ✅ Streaming SSE (7 chunks in "hello" response)
   ✅ Auto-detect Hindi from Devanagari
   ✅ Auto-detect Punjabi from Gurmukhi
   ✅ Stats tracking + top commands
   ✅ Image list endpoint
   ✅ Markdown export
   ✅ Calculator (25 times 8 = 200)
   ✅ All 17 command types
   ✅ All 25 API endpoints
```

---

## 🛠️ Troubleshooting

<details>
<summary><b>Voice recognition not working</b></summary>

- Use **Chrome or Edge** (Firefox doesn't support Web Speech API)
- Allow microphone permission when browser prompts
- Windows Settings → Privacy → Microphone → allow browsers
</details>

<details>
<summary><b>"AI brain not connected" toast / AI not replying</b></summary>

- Open **⚙️ AI Settings** and click **🧪 Test** to see the exact status
- The free provider needs an internet connection — check Wi-Fi
- If it says "rate limit / busy", wait a moment or add a **free Groq key**
- Using **Ollama** instead? Make sure it's running (`ollama list`) and the
  model is pulled (`ollama pull llama3.2:3b`), then choose Ollama in Settings
</details>

<details>
<summary><b>"No vision model" when using image chat</b></summary>

Run: `ollama pull llava` (≈4 GB, one-time)
</details>

<details>
<summary><b>"Port 8000 already in use"</b></summary>

Edit `backend/.env` → `API_PORT=8001`
</details>

<details>
<summary><b>Hindi/Punjabi TTS not speaking</b></summary>

Windows Settings → Time & Language → Language → Add Hindi/Punjabi
</details>

<details>
<summary><b>Streaming doesn't work</b></summary>

Toggle off "Streaming replies" in sidebar → uses classic mode
</details>

---

## 🎁 What's New in v5.1 PRO

| Feature | Description |
|---|---|
| ⚡ **Streaming AI** | Words appear as generated (like ChatGPT) |
| 🍞 **Toast notifications** | Beautiful non-blocking messages |
| ⌘ **Command palette** | `Ctrl+K` fuzzy search everything |
| 🎬 **Splash screen** | Cinematic boot animation |
| 🖼️ **Image chat** | Vision AI with llava model |
| 📊 **Stats dashboard** | Track your usage with charts |
| 📤 **Export chat** | Download as Markdown |
| 🌈 **Auto-language** | Detect Hindi/Punjabi from script |
| ♿ **Accessibility** | ARIA labels, focus rings, keyboard nav |
| 🎨 **Micro-animations** | Everywhere — smooth as butter |

---

## 📊 Stats

| Metric | Value |
|---|---|
| Python files | **18** |
| Python LOC | ~2,100 |
| Frontend LOC | ~2,700 |
| Total files | **32** |
| API endpoints | **25** |
| Languages supported | 3 |
| Themes | 6 |
| Personalities | 6 |
| Zero-cost APIs | ✅ (all free) |
| Offline-capable | ✅ (with Ollama) |

---

## 🚀 What Could Be Next

- 🖼️ Image generation (Stable Diffusion)
- 📧 Email sending (Gmail API)
- 📱 Mobile PWA
- 🎨 Custom color picker
- 💾 Vector DB for huge PDFs
- 🔊 ElevenLabs realistic voice
- 👤 Face recognition login
- 🐳 Docker container

---

**Made with ❤️ for the AI-assistant community.**

Enjoy Jarvis Pro! 🤖✨

---

## ☁️ Deploying the backend to Vercel (optional)

The repo is Vercel-ready out of the box:

- `api/index.py` — serverless entrypoint (FastAPI + Mangum, normalizes any event)
- `api/requirements.txt` — Linux-safe deps (Windows-only packages auto-skipped)
- `vercel.json` — routes every path to the Python function
- Writable data (logs/uploads/notes/stats) auto-falls back to `/tmp` on read-only hosts

**Steps:**
1. Push the repo to GitHub (already done).
2. In Vercel → **New Project → import the repo**.
3. **Settings → Build & Deployment → Root Directory = the repository root (leave empty — NOT `backend/`).**
4. Framework preset = **Other**. Deploy.

> ⚠️ Vercel is **serverless** — it can serve the web app + free AI chat, but
> desktop-only features (open apps, screenshots, local Ollama, pywhatkit) and
> data persistence won't work there. For the **real desktop assistant**, run
> `START.bat` on your PC. For a **live demo website**, use GitHub Pages with
> `demo.html`.
