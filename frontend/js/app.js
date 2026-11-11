/* ═══════════════════════════════════════════════════════════════
   JARVIS FRONTEND v5.1 PRO — Production build
   ═══════════════════════════════════════════════════════════════ */
'use strict';

const $ = (id) => document.getElementById(id);
const chat        = $("chat");
const input       = $("text-input");
const sendBtn     = $("send-btn");
const micBtn      = $("mic-btn");
const statusText  = $("status-text");
const canvas      = $("visualizer");
const ctx         = canvas.getContext("2d");
const API_BASE    = "/api";

const LANG_MAP = { en: "en-IN", hi: "hi-IN", pa: "pa-IN" };
let currentLang    = "en";
let autoDetectLang = true;
let streamingOn    = true;

const WAKE_WORDS = [
  "hey jarvis", "hi jarvis", "ok jarvis", "jarvis",
  "हे जार्विस", "जार्विस",
  "ਹੇ ਜਾਰਵਿਸ", "ਜਾਰਵਿਸ",
];

/* ═══════════════════════════════════════════════════════════════
   0. TOASTS (professional notifications)
   ═══════════════════════════════════════════════════════════════ */
function toast(message, type = "info", duration = 3500) {
  const wrap = $("toasts");
  if (!wrap) return;
  const icons = { success: "✅", error: "❌", warn: "⚠️", info: "ℹ️" };
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `
    <span class="toast-icon">${icons[type] || "ℹ️"}</span>
    <span class="toast-msg">${escapeHtml(message)}</span>
    <button class="toast-close" aria-label="Close">✖</button>
  `;
  wrap.appendChild(el);
  const remove = () => {
    el.classList.add("leaving");
    setTimeout(() => el.remove(), 300);
  };
  el.querySelector(".toast-close").addEventListener("click", remove);
  setTimeout(remove, duration);
}

/* ═══════════════════════════════════════════════════════════════
   1. SPLASH SCREEN
   ═══════════════════════════════════════════════════════════════ */
const SPLASH_STEPS = [
  { pct: 15, msg: "Loading configuration..." },
  { pct: 35, msg: "Connecting to AI brain..." },
  { pct: 55, msg: "Initializing voice engine..." },
  { pct: 75, msg: "Preparing themes..." },
  { pct: 95, msg: "Almost ready..." },
  { pct: 100, msg: "Welcome, Boss!" },
];

async function playSplash() {
  const bar = document.querySelector(".splash-bar-fill");
  const status = $("splash-status");
  for (const step of SPLASH_STEPS) {
    bar.style.width = step.pct + "%";
    status.textContent = step.msg;
    await new Promise(r => setTimeout(r, 300));
  }
  await new Promise(r => setTimeout(r, 200));
  $("splash").classList.add("hide");
}

/* ═══════════════════════════════════════════════════════════════
   2. CHAT HELPERS
   ═══════════════════════════════════════════════════════════════ */
function addMessage(text, who = "assistant") {
  const wrap = document.createElement("div");
  wrap.className = `message ${who}`;
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  wrap.innerHTML = `
    <div class="avatar">${who === "user" ? "🙂" : "🤖"}</div>
    <div class="bubble">
      <span class="bubble-text">${escapeHtml(text)}</span>
      <div class="timestamp">${time}</div>
    </div>`;
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  saveHistory();
  return wrap;
}

function addStreamingMessage() {
  const wrap = document.createElement("div");
  wrap.className = "message assistant";
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  wrap.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="bubble">
      <span class="bubble-text"></span><span class="streaming-cursor"></span>
      <div class="timestamp">${time}</div>
    </div>`;
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

function addTyping() {
  const wrap = document.createElement("div");
  wrap.className = "message assistant typing-msg";
  wrap.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="bubble">
      <div class="typing"><span></span><span></span><span></span></div>
    </div>`;
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function setStatus(msg, color) {
  statusText.textContent = msg;
  const dot = document.querySelector(".status-dot");
  if (dot && color) dot.style.background = color;
}

/* ─── Backend connection watchdog (auto-detect + auto-reconnect) ─── */
let _backendDown = false;
let _reconnectTimer = null;

function setBackendBanner(show, text) {
  const b = $("backend-banner");
  if (!b) return;
  if (show) {
    if (text && $("backend-banner-text")) $("backend-banner-text").textContent = text;
    b.classList.remove("hidden");
  } else {
    b.classList.add("hidden");
  }
}

async function pingBackend() {
  try {
    const r = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    return r.ok;
  } catch {
    return false;
  }
}

function backendWentOffline() {
  setBackendBanner(true, "⚠️ Backend is offline. Keep the black START.bat window OPEN. Reconnecting…");
  setStatus("Offline", "#ff5370");
  if (!_backendDown) _backendDown = true;
  if (!_reconnectTimer) {
    _reconnectTimer = setInterval(async () => {
      if (await pingBackend()) backendReconnected();
    }, 3000);
  }
}

function backendReconnected() {
  if (_reconnectTimer) { clearInterval(_reconnectTimer); _reconnectTimer = null; }
  setBackendBanner(false);
  setStatus("Ready", "#4caf50");
  if (_backendDown) {
    _backendDown = false;
    toast("Backend reconnected ✅", "success", 3000);
  }
}

/* ═══════════════════════════════════════════════════════════════
   3. HISTORY
   ═══════════════════════════════════════════════════════════════ */
function saveHistory() {
  try {
    const msgs = Array.from(chat.querySelectorAll(".message:not(.typing-msg)"))
      .map(m => ({
        who: m.classList.contains("user") ? "user" : "assistant",
        text: (m.querySelector(".bubble-text")?.textContent ||
               m.querySelector(".bubble")?.childNodes[0]?.textContent || "").trim(),
      }))
      .filter(m => m.text);
    localStorage.setItem("jarvis_chat", JSON.stringify(msgs.slice(-50)));
  } catch {}
}
function loadHistory() {
  try {
    const raw = localStorage.getItem("jarvis_chat");
    if (!raw) return;
    const msgs = JSON.parse(raw);
    if (Array.isArray(msgs) && msgs.length) {
      chat.innerHTML = "";
      msgs.forEach(m => addMessage(m.text, m.who));
    }
  } catch {}
}
function clearHistory() {
  localStorage.removeItem("jarvis_chat");
  chat.innerHTML = `
    <div class="message assistant">
      <div class="avatar">🤖</div>
      <div class="bubble"><span class="bubble-text">Chat cleared! How can I help?</span></div>
    </div>`;
  toast("Chat cleared", "success", 2000);
}
function getMessages() {
  return Array.from(chat.querySelectorAll(".message:not(.typing-msg)"))
    .map(m => ({
      who: m.classList.contains("user") ? "user" : "assistant",
      text: (m.querySelector(".bubble-text")?.textContent || "").trim(),
    }))
    .filter(m => m.text);
}

/* ═══════════════════════════════════════════════════════════════
   4. SEND TEXT (with optional streaming)
   ═══════════════════════════════════════════════════════════════ */
async function sendText(text) {
  text = (text || "").trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";
  setStatus("Thinking...", "#ffb300");

  if (streamingOn && "EventSource" in window) {
    await sendTextStream(text);
  } else {
    await sendTextClassic(text);
  }
}

async function sendTextClassic(text) {
  const typing = addTyping();
  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, auto_detect_lang: autoDetectLang }),
    });
    const data = await res.json().catch(() => ({}));
    typing.remove();
    if (!res.ok) {
      const msg = data.detail || "Server error";
      addMessage(`⚠️ ${msg}`, "assistant");
      toast(msg, "error");
      setStatus("Error", "#ff5370");
      return;
    }
    if (data.detected_lang && data.detected_lang !== currentLang) {
      syncLanguageUI(data.detected_lang);
    }
    const reply = data.reply || "(no reply)";
    // Special marker for image results
    if (reply.startsWith("__IMAGE__:")) {
      const parts = reply.substring(10).split(":");
      const url = parts[0];
      const prompt = parts.slice(1).join(":");
      addImageMessage(url, prompt);
      toast("Image ready!", "success");
    } else {
      addMessage(reply, "assistant");
      speakInBrowser(reply);
    }
    setStatus("Ready", "#4caf50");
  } catch (err) {
    typing.remove();
    addMessage("⚠️ Cannot reach the server. Make sure the black START.bat window is still open, then I'll reconnect automatically.", "assistant");
    toast("Backend unreachable — reconnect banner shown", "error");
    backendWentOffline();
    console.error(err);
  }
}

function addImageMessage(url, prompt) {
  const wrap = document.createElement("div");
  wrap.className = "message assistant";
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  wrap.innerHTML = `
    <div class="avatar">🎨</div>
    <div class="bubble">
      <span class="bubble-text">Here's your image of: <em>${escapeHtml(prompt)}</em></span>
      <img class="gen-image" src="${url}" alt="${escapeHtml(prompt)}" loading="lazy" />
      <div class="timestamp">${time}</div>
    </div>`;
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  saveHistory();
}

async function sendTextStream(text) {
  const bubble = addStreamingMessage();
  const textEl = bubble.querySelector(".bubble-text");
  const cursor = bubble.querySelector(".streaming-cursor");
  let full = "";

  try {
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, auto_detect_lang: autoDetectLang }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() || "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6);
        if (payload === "[DONE]") continue;
        const chunk = payload.replace(/\\n/g, "\n");
        full += chunk;
        textEl.textContent = full;
        chat.scrollTop = chat.scrollHeight;
      }
    }

    cursor.remove();
    // Handle image marker in streaming too
    if (full.startsWith("__IMAGE__:")) {
      bubble.remove();
      const parts = full.substring(10).split(":");
      addImageMessage(parts[0], parts.slice(1).join(":"));
      toast("Image ready!", "success");
    } else {
      saveHistory();
      speakInBrowser(full);
    }
    setStatus("Ready", "#4caf50");
  } catch (err) {
    cursor.remove();
    textEl.textContent = "⚠️ Streaming failed. Falling back...";
    console.warn(err);
    bubble.remove();
    await sendTextClassic(text);
  }
}

/* ═══════════════════════════════════════════════════════════════
   5. SPEECH RECOGNITION
   ═══════════════════════════════════════════════════════════════ */
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition, isListening = false, wakeWordActive = false;
let wakeRecognition, wakeRestartTimer;

function createRecognizer() {
  if (!SpeechRecognition) return null;
  const rec = new SpeechRecognition();
  rec.lang = LANG_MAP[currentLang] || "en-IN";
  rec.interimResults = true;
  rec.maxAlternatives = 1;
  return rec;
}

function startListening() {
  if (wakeWordActive) {
    stopWakeWord(true);
    openListenWindow(() => {
      $("wake-toggle").checked = true;
      startWakeWord();
    });
    return;
  }
  if (isListening) { recognition?.stop(); return; }
  if (!SpeechRecognition) {
    toast("Voice not supported. Please use Chrome or Edge.", "warn");
    return;
  }
  recognition = createRecognizer();
  recognition.continuous = false;

  recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add("listening");
    setStatus("Listening...", "#00e5ff");
    startRealVisualizer();
  };
  recognition.onresult = (e) => {
    let interim = "", final = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) final += t; else interim += t;
    }
    input.value = final || interim;
    if (final) { stopListeningUI(); sendText(final.trim()); }
  };
  recognition.onerror = handleRecError;
  recognition.onend = stopListeningUI;

  try { recognition.start(); } catch (e) { console.warn(e); stopListeningUI(); }
}

function stopListeningUI() {
  isListening = false;
  micBtn.classList.remove("listening");
  stopVisualizer();
  if (!wakeWordActive) setStatus("Ready", "#4caf50");
}

function startWakeWord() {
  if (!SpeechRecognition) {
    toast("Voice not supported. Use Chrome/Edge.", "warn");
    $("wake-toggle").checked = false;
    return;
  }
  wakeWordActive = true;
  micBtn.classList.add("wake-mode");
  document.querySelector(".wake-section")?.classList.add("active");
  setStatus("Say 'Hey Jarvis'...", "#00e5ff");
  toast("Wake word active — say 'Hey Jarvis'", "info", 2500);

  wakeRecognition = createRecognizer();
  wakeRecognition.continuous = true;

  wakeRecognition.onresult = (e) => {
    let heard = "";
    for (let i = e.resultIndex; i < e.results.length; i++)
      heard += e.results[i][0].transcript;
    heard = heard.toLowerCase().trim();

    const matched = WAKE_WORDS.find(w => heard.includes(w.toLowerCase()));
    if (!matched) return;

    playChime();
    setStatus("Yes, boss! 👂", "#ff9800");
    const startIdx = heard.toLowerCase().indexOf(matched.toLowerCase()) + matched.length;
    const cmd = heard.substring(startIdx).trim().replace(/^[,.\s]+/, "");

    if (cmd && cmd.length > 2) {
      try { wakeRecognition.stop(); } catch {}
      sendText(cmd);
    } else {
      try { wakeRecognition.stop(); } catch {}
      setTimeout(() => openListenWindow(() => {
        if (wakeWordActive) restartWakeListener();
      }), 300);
    }
  };
  wakeRecognition.onerror = (e) => {
    if (wakeWordActive && e.error !== "aborted") restartWakeListener();
  };
  wakeRecognition.onend = () => { if (wakeWordActive) restartWakeListener(); };
  try { wakeRecognition.start(); } catch (e) { restartWakeListener(); }
}

function restartWakeListener() {
  clearTimeout(wakeRestartTimer);
  wakeRestartTimer = setTimeout(() => {
    if (wakeWordActive && wakeRecognition) {
      try { wakeRecognition.start(); } catch {}
    }
  }, 400);
}

function stopWakeWord(silent = false) {
  wakeWordActive = false;
  micBtn.classList.remove("wake-mode");
  document.querySelector(".wake-section")?.classList.remove("active");
  clearTimeout(wakeRestartTimer);
  if (wakeRecognition) { try { wakeRecognition.stop(); } catch {} ; wakeRecognition = null; }
  if (!silent) { setStatus("Ready", "#4caf50"); toast("Wake word disabled", "info", 2000); }
}

function openListenWindow(onFinish) {
  const listener = createRecognizer();
  if (!listener) { onFinish && onFinish(); return; }
  listener.continuous = false;
  micBtn.classList.add("listening");
  startRealVisualizer();
  setStatus("Listening...", "#00e5ff");

  let done = false;
  const finish = () => {
    if (done) return;
    done = true;
    micBtn.classList.remove("listening");
    stopVisualizer();
    onFinish && onFinish();
  };
  listener.onresult = (e) => {
    let final = "";
    for (let i = e.resultIndex; i < e.results.length; i++)
      if (e.results[i].isFinal) final += e.results[i][0].transcript;
    if (final) sendText(final.trim());
  };
  listener.onend = finish;
  listener.onerror = finish;
  try { listener.start(); } catch { finish(); }
}

function handleRecError(e) {
  const messages = {
    "not-allowed": "Please allow microphone access.",
    "no-speech":   "I didn't hear anything. Try again.",
    "network":     "Network error. Check internet.",
    "aborted":     "Cancelled.",
    "audio-capture": "No microphone detected.",
  };
  const msg = messages[e.error] || ("Mic error: " + e.error);
  setStatus(msg, "#ff5370");
  if (e.error !== "aborted" && e.error !== "no-speech") toast(msg, "error");
  stopListeningUI();
}

function playChime() {
  try {
    const ac = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ac.createOscillator();
    const gain = ac.createGain();
    osc.connect(gain); gain.connect(ac.destination);
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.15, ac.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + 0.3);
    osc.start(); osc.stop(ac.currentTime + 0.3);
  } catch {}
}

/* ═══════════════════════════════════════════════════════════════
   6. TTS
   ═══════════════════════════════════════════════════════════════ */
function speakInBrowser(text) {
  if (!text || !window.speechSynthesis) return;
  try {
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    const targetLang = LANG_MAP[currentLang] || "en-IN";
    utter.lang = targetLang;
    const voices = window.speechSynthesis.getVoices();
    const preferred =
      voices.find(v => v.lang === targetLang) ||
      voices.find(v => v.lang.startsWith(currentLang)) ||
      voices.find(v => v.lang.startsWith("en"));
    if (preferred) utter.voice = preferred;

    // 3D avatar talking animation
    const av = document.getElementById("avatar-3d");
    utter.onstart = () => av?.classList.add("talking");
    utter.onend   = () => av?.classList.remove("talking");
    utter.onerror = () => av?.classList.remove("talking");

    window.speechSynthesis.speak(utter);
  } catch (e) { console.warn(e); }
}

/* ═══════════════════════════════════════════════════════════════
   7. VISUALIZER
   ═══════════════════════════════════════════════════════════════ */
let audioCtx, analyser, micStream, vizRAF;

async function startRealVisualizer() {
  try {
    if (!micStream) {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const source = audioCtx.createMediaStreamSource(micStream);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
    }
    drawRealVisualizer();
  } catch { fakeVisualizer(); }
}
function themeColors() {
  const s = getComputedStyle(document.documentElement);
  return {
    c1: s.getPropertyValue("--primary").trim() || "#00e5ff",
    c2: s.getPropertyValue("--primary-2").trim() || "#7c4dff",
  };
}
function drawRealVisualizer() {
  const buffer = new Uint8Array(analyser.frequencyBinCount);
  const bars = buffer.length;
  const w = canvas.width / bars;
  function loop() {
    analyser.getByteFrequencyData(buffer);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const { c1, c2 } = themeColors();
    for (let i = 0; i < bars; i++) {
      const h = (buffer[i] / 255) * canvas.height * 0.9 + 2;
      const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
      g.addColorStop(0, c1); g.addColorStop(1, c2);
      ctx.fillStyle = g;
      ctx.fillRect(i * w + 1, (canvas.height - h) / 2, w - 2, h);
    }
    vizRAF = requestAnimationFrame(loop);
  }
  loop();
}
function fakeVisualizer() {
  const bars = 60, w = canvas.width / bars;
  function loop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const { c1, c2 } = themeColors();
    for (let i = 0; i < bars; i++) {
      const t = Date.now() / 300 + i * 0.3;
      const h = (Math.sin(t) * 0.5 + 0.5) * canvas.height * 0.8 + 4;
      const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
      g.addColorStop(0, c1); g.addColorStop(1, c2);
      ctx.fillStyle = g;
      ctx.fillRect(i * w + 2, (canvas.height - h) / 2, w - 4, h);
    }
    vizRAF = requestAnimationFrame(loop);
  }
  loop();
}
function stopVisualizer() { if (vizRAF) cancelAnimationFrame(vizRAF); drawIdle(); }
function drawIdle() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const cy = canvas.height / 2;
  const { c1 } = themeColors();
  ctx.strokeStyle = c1 + "40";
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(canvas.width, cy); ctx.stroke();
}
function fitCanvas() {
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * (window.devicePixelRatio || 1);
  canvas.height = rect.height * (window.devicePixelRatio || 1);
}

/* ═══════════════════════════════════════════════════════════════
   8. THEME + LANGUAGE
   ═══════════════════════════════════════════════════════════════ */
function setTheme(name) {
  document.documentElement.setAttribute("data-theme", name);
  localStorage.setItem("jarvis_theme", name);
  document.querySelectorAll(".theme-btn").forEach(b =>
    b.classList.toggle("active", b.dataset.theme === name)
  );
  drawIdle();
}
function loadTheme() { setTheme(localStorage.getItem("jarvis_theme") || "dark"); }

const GREETINGS = {
  en: `Hello, <span class="user-name">Boss</span> 👋`,
  hi: `नमस्ते, <span class="user-name">बॉस</span> 👋`,
  pa: `ਸਤ ਸ੍ਰੀ ਅਕਾਲ, <span class="user-name">ਬੌਸ</span> 👋`,
};
const HINTS = {
  en: 'Click the mic 🎤 or say "Hey Jarvis"',
  hi: 'माइक 🎤 दबाएँ या "Hey Jarvis" कहें',
  pa: 'ਮਾਈਕ 🎤 ਦਬਾਓ ਜਾਂ "Hey Jarvis" ਕਹੋ',
};

function syncLanguageUI(lang) {
  currentLang = lang;
  document.querySelectorAll(".lang-btn").forEach(b =>
    b.classList.toggle("active", b.dataset.lang === lang)
  );
  const g = $("greeting"), h = $("header-hint");
  if (g) g.innerHTML = GREETINGS[lang] || GREETINGS.en;
  if (h) h.textContent = HINTS[lang] || HINTS.en;
  if (recognition) recognition.lang = LANG_MAP[lang];
  if (wakeWordActive) {
    stopWakeWord(true);
    setTimeout(startWakeWord, 200);
  }
}

async function setLanguage(lang) {
  syncLanguageUI(lang);
  localStorage.setItem("jarvis_lang", lang);
  try {
    await fetch(`${API_BASE}/language`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lang }),
    });
  } catch {}
}
function loadLanguage() { setLanguage(localStorage.getItem("jarvis_lang") || "en"); }

/* ═══════════════════════════════════════════════════════════════
   9. PERSONALITY
   ═══════════════════════════════════════════════════════════════ */
async function loadPersonality() {
  try {
    const r = await fetch(`${API_BASE}/personalities`);
    const d = await r.json();
    const sel = $("personality-select");
    if (sel) sel.value = d.current;
  } catch {}
}
async function setPersonality(name) {
  try {
    await fetch(`${API_BASE}/personality`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    addMessage(`✨ Personality changed to ${name}. Chat memory reset.`, "assistant");
    toast(`Personality: ${name}`, "success");
  } catch (e) { console.error(e); }
}

/* ═══════════════════════════════════════════════════════════════
   10. NOTES / PDF / IMAGE modals (unified factory)
   ═══════════════════════════════════════════════════════════════ */
function openModal(id)  { $(id)?.classList.remove("hidden"); }
function closeModal(id) { $(id)?.classList.add("hidden"); }

// ── Notes ──
async function renderNotes() {
  const list = $("notes-list");
  list.innerHTML = "<li class='empty-notes'>Loading...</li>";
  try {
    const r = await fetch(`${API_BASE}/notes`);
    const notes = await r.json();
    if (!Array.isArray(notes) || !notes.length) {
      list.innerHTML = "<li class='empty-notes'>No notes yet. Add one above! 📝</li>";
      return;
    }
    list.innerHTML = "";
    notes.forEach(n => {
      const li = document.createElement("li");
      if (n.done) li.classList.add("done");
      li.innerHTML = `
        <input type="checkbox" class="note-check" ${n.done ? "checked" : ""} data-id="${n.id}"/>
        <span class="note-text">${escapeHtml(n.text)}</span>
        <button class="note-del" data-id="${n.id}" title="Delete" aria-label="Delete">🗑️</button>`;
      list.appendChild(li);
    });
    list.querySelectorAll(".note-check").forEach(c =>
      c.addEventListener("change", () => toggleNote(c.dataset.id))
    );
    list.querySelectorAll(".note-del").forEach(b =>
      b.addEventListener("click", () => deleteNote(b.dataset.id))
    );
  } catch { list.innerHTML = "<li class='empty-notes'>Error loading notes.</li>"; }
}
async function addNote() {
  const inp = $("new-note-input"); const text = inp.value.trim();
  if (!text) return;
  await fetch(`${API_BASE}/notes`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  inp.value = ""; renderNotes(); toast("Note added", "success", 1500);
}
async function toggleNote(id) { await fetch(`${API_BASE}/notes/${id}/toggle`, { method: "POST" }); renderNotes(); }
async function deleteNote(id) { await fetch(`${API_BASE}/notes/${id}`, { method: "DELETE" }); renderNotes(); }

// ── PDF ──
async function renderPDFList() {
  const list = $("pdf-list");
  list.innerHTML = "<li class='empty-notes'>Loading...</li>";
  try {
    const r = await fetch(`${API_BASE}/pdf`);
    const data = await r.json();
    const docs = data.documents || [];
    updatePDFBanner(data.active);
    if (!docs.length) {
      list.innerHTML = "<li class='empty-notes'>No PDFs uploaded yet.</li>";
      return;
    }
    list.innerHTML = "";
    docs.forEach(d => {
      const li = document.createElement("li");
      li.className = "pdf-item" + (d.active ? " active" : "");
      li.innerHTML = `
        <span>📄</span>
        <span class="pdf-item-name" title="${escapeHtml(d.filename)}">${escapeHtml(d.filename)}</span>
        ${d.active ? '<span class="pdf-item-badge">ACTIVE</span>' : ''}
        <button class="note-del" data-file="${escapeHtml(d.filename)}" title="Delete" aria-label="Delete">🗑️</button>`;
      li.addEventListener("click", (e) => {
        if (e.target.closest(".note-del")) return;
        selectPDF(d.filename);
      });
      list.appendChild(li);
    });
    list.querySelectorAll(".note-del").forEach(b =>
      b.addEventListener("click", (e) => { e.stopPropagation(); deletePDF(b.dataset.file); })
    );
  } catch { list.innerHTML = "<li class='empty-notes'>Error loading PDFs.</li>"; }
}
async function selectPDF(filename) {
  await fetch(`${API_BASE}/pdf/select`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });
  updatePDFBanner(filename); renderPDFList();
  addMessage(`📄 Now chatting with: ${filename}. Try "summarize the pdf".`, "assistant");
  closeModal("pdf-modal");
}
async function deletePDF(f) { await fetch(`${API_BASE}/pdf/${encodeURIComponent(f)}`, { method: "DELETE" }); renderPDFList(); }
function updatePDFBanner(active) {
  const b = $("pdf-banner");
  if (active) { b.classList.remove("hidden"); $("pdf-banner-name").textContent = active; }
  else b.classList.add("hidden");
}
async function uploadPDF(file) { await uploadFile(file, "pdf", ".pdf"); }

// ── Image ──
async function renderImageList() {
  const list = $("image-list");
  list.innerHTML = "<li class='empty-notes'>Loading...</li>";
  try {
    const r = await fetch(`${API_BASE}/image`);
    const data = await r.json();
    const imgs = data.images || [];
    updateImageBanner(data.active);
    if (!imgs.length) {
      list.innerHTML = "<li class='empty-notes'>No images uploaded yet.</li>";
      return;
    }
    list.innerHTML = "";
    imgs.forEach(d => {
      const li = document.createElement("li");
      li.className = "pdf-item" + (d.active ? " active" : "");
      li.innerHTML = `
        <span>🖼️</span>
        <span class="pdf-item-name" title="${escapeHtml(d.filename)}">${escapeHtml(d.filename)}</span>
        ${d.active ? '<span class="pdf-item-badge">ACTIVE</span>' : ''}
        <button class="note-del" data-file="${escapeHtml(d.filename)}" title="Delete" aria-label="Delete">🗑️</button>`;
      li.addEventListener("click", (e) => {
        if (e.target.closest(".note-del")) return;
        selectImage(d.filename);
      });
      list.appendChild(li);
    });
    list.querySelectorAll(".note-del").forEach(b =>
      b.addEventListener("click", (e) => { e.stopPropagation(); deleteImage(b.dataset.file); })
    );
  } catch { list.innerHTML = "<li class='empty-notes'>Error loading images.</li>"; }
}
async function selectImage(filename) {
  await fetch(`${API_BASE}/image/select`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename }),
  });
  updateImageBanner(filename); renderImageList();
  addMessage(`🖼️ Now chatting with image: ${filename}. Try "describe the image".`, "assistant");
  closeModal("image-modal");
}
async function deleteImage(f) { await fetch(`${API_BASE}/image/${encodeURIComponent(f)}`, { method: "DELETE" }); renderImageList(); }
function updateImageBanner(active) {
  const b = $("image-banner");
  if (active) { b.classList.remove("hidden"); $("image-banner-name").textContent = active; }
  else b.classList.add("hidden");
}
async function uploadImage(file) { await uploadFile(file, "image", null); }

// Shared uploader
async function uploadFile(file, endpoint, ext) {
  if (!file) return;
  if (ext && !file.name.toLowerCase().endsWith(ext)) {
    toast(`Please select a ${ext} file`, "warn"); return;
  }
  if (file.size > 25 * 1024 * 1024) { toast("File too large (max 25 MB)", "warn"); return; }
  const progressEl = $(`${endpoint}-upload-progress`);
  const fill = progressEl.querySelector(".progress-fill");
  const txt  = progressEl.querySelector(".progress-text");
  progressEl.classList.remove("hidden");
  fill.style.width = "40%";
  txt.textContent = "Uploading...";
  try {
    const form = new FormData(); form.append("file", file);
    const r = await fetch(`${API_BASE}/${endpoint}/upload`, { method: "POST", body: form });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Upload failed");
    fill.style.width = "100%";
    txt.textContent = "✅ Uploaded!";
    toast("Upload complete", "success");
    setTimeout(() => { progressEl.classList.add("hidden"); fill.style.width = "0%"; }, 1500);
    endpoint === "pdf" ? renderPDFList() : renderImageList();
    addMessage(`${endpoint === "pdf" ? "📄" : "🖼️"} "${data.filename}" ready!`, "assistant");
  } catch (e) {
    txt.textContent = "❌ " + e.message;
    toast(e.message, "error");
    setTimeout(() => progressEl.classList.add("hidden"), 3000);
  }
}

/* ═══════════════════════════════════════════════════════════════
   11. STATS
   ═══════════════════════════════════════════════════════════════ */
async function openStats() {
  openModal("stats-modal");
  try {
    const d = await (await fetch(`${API_BASE}/stats`)).json();
    $("stat-total").textContent = d.total_commands ?? 0;
    $("stat-llm").textContent   = d.total_llm_calls ?? 0;
    $("stat-types").textContent = d.unique_command_types ?? 0;

    const topEl = $("stat-top");
    const top = d.top_commands || [];
    if (!top.length) {
      topEl.innerHTML = "<li class='empty-notes'>No data yet.</li>";
    } else {
      const max = Math.max(...top.map(x => x.count));
      topEl.innerHTML = top.map(x => `
        <li>
          <span style="width:80px;font-weight:500;">${escapeHtml(x.name)}</span>
          <div class="bar"><div class="bar-fill" style="width:${(x.count / max * 100).toFixed(0)}%"></div></div>
          <span class="count">${x.count}</span>
        </li>`).join("");
    }

    const chartEl = $("stat-chart");
    const daily = d.daily_activity || [];
    if (!daily.length) {
      chartEl.innerHTML = "<p style='color:var(--text-dim);font-size:12px;padding:10px;'>No activity yet.</p>";
    } else {
      const max = Math.max(...daily.map(x => x.count), 1);
      chartEl.innerHTML = daily.map(x => `
        <div class="day" style="height:${(x.count / max * 100).toFixed(0)}%" data-tooltip="${x.date}: ${x.count}"></div>
      `).join("");
    }
  } catch (e) { toast("Failed to load stats", "error"); }
}
async function resetStats() {
  if (!confirm("Reset all usage statistics?")) return;
  await fetch(`${API_BASE}/stats`, { method: "DELETE" });
  toast("Stats reset", "success");
  openStats();
}

/* ═══════════════════════════════════════════════════════════════
   12. EXPORT CHAT
   ═══════════════════════════════════════════════════════════════ */
async function exportChat() {
  const messages = getMessages();
  if (!messages.length) { toast("Nothing to export", "warn"); return; }
  try {
    const r = await fetch(`${API_BASE}/export/markdown`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `jarvis_chat_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast(`Exported ${messages.length} messages`, "success");
  } catch (e) { toast("Export failed", "error"); }
}

/* ═══════════════════════════════════════════════════════════════
   13. COMMAND PALETTE (Ctrl+K)
   ═══════════════════════════════════════════════════════════════ */
const PALETTE_ITEMS = [
  { icon: "🕐", title: "What time is it",              cmd: "what time is it" },
  { icon: "📅", title: "What's today's date",           cmd: "what is today's date" },
  { icon: "🌤️", title: "Weather in my city",           cmd: "what's the weather in Ludhiana" },
  { icon: "📰", title: "Latest news",                   cmd: "latest news" },
  { icon: "😂", title: "Tell me a joke",                cmd: "tell me a joke" },
  { icon: "💪", title: "Motivate me",                   cmd: "motivate me" },
  { icon: "🔋", title: "Battery status",                cmd: "battery status" },
  { icon: "💻", title: "CPU usage",                     cmd: "cpu usage" },
  { icon: "🧠", title: "Memory usage",                  cmd: "memory usage" },
  { icon: "💾", title: "Disk space",                    cmd: "disk space" },
  { icon: "📸", title: "Take screenshot",               cmd: "take a screenshot" },
  { icon: "▶️", title: "Open YouTube",                  cmd: "open youtube" },
  { icon: "🔍", title: "Open Google",                   cmd: "open google" },
  { icon: "📧", title: "Open Gmail",                    cmd: "open gmail" },
  { icon: "🐙", title: "Open GitHub",                   cmd: "open github" },
  { icon: "📝", title: "Open Notepad",                  cmd: "open notepad" },
  { icon: "🧮", title: "Open Calculator",               cmd: "open calculator" },
  { icon: "📅", title: "My calendar",                   cmd: "my calendar" },
  { icon: "📋", title: "Show my notes",                 cmd: "show my notes",           action: () => openModal("notes-modal") },
  { icon: "📄", title: "Chat with PDF",                 action: () => { openModal("pdf-modal"); renderPDFList(); } },
  { icon: "🖼️", title: "Chat with Image",              action: () => { openModal("image-modal"); renderImageList(); } },
  { icon: "🎨", title: "Generate Image (AI)",           action: openImageGen },
  { icon: "📧", title: "Send Email",                    action: () => { openModal("email-modal"); switchTab("email-tab"); } },
  { icon: "💬", title: "Send WhatsApp",                 action: () => { openModal("email-modal"); switchTab("wa-tab"); } },
  { icon: "🔍", title: "Search the web",                cmd: "search for latest AI news" },
  { icon: "📊", title: "Open Stats",                    action: openStats },
  { icon: "📤", title: "Export Chat",                   action: exportChat },
  { icon: "🗑️", title: "Clear Chat",                   action: clearHistory },
  { icon: "🎭", title: "Personality: Jarvis",           action: () => { $("personality-select").value = "jarvis"; setPersonality("jarvis"); } },
  { icon: "😏", title: "Personality: Sassy",            action: () => { $("personality-select").value = "sassy"; setPersonality("sassy"); } },
  { icon: "👨‍🏫", title: "Personality: Teacher",         action: () => { $("personality-select").value = "teacher"; setPersonality("teacher"); } },
  { icon: "🌙", title: "Theme: Dark",                   action: () => setTheme("dark") },
  { icon: "☀️", title: "Theme: Light",                  action: () => setTheme("light") },
  { icon: "🎮", title: "Theme: Cyberpunk",              action: () => setTheme("cyberpunk") },
  { icon: "🌊", title: "Theme: Ocean",                  action: () => setTheme("ocean") },
  { icon: "🌅", title: "Theme: Sunset",                 action: () => setTheme("sunset") },
  { icon: "🌲", title: "Theme: Forest",                 action: () => setTheme("forest") },
  { icon: "🇬🇧", title: "Language: English",            action: () => setLanguage("en") },
  { icon: "🇮🇳", title: "Language: Hindi",              action: () => setLanguage("hi") },
  { icon: "🇮🇳", title: "Language: Punjabi",            action: () => setLanguage("pa") },
];

let paletteFiltered = PALETTE_ITEMS.slice();
let paletteIndex = 0;

function openPalette() {
  $("palette").classList.remove("hidden");
  const inp = $("palette-input");
  inp.value = "";
  paletteFiltered = PALETTE_ITEMS.slice();
  paletteIndex = 0;
  renderPalette();
  setTimeout(() => inp.focus(), 50);
}
function closePalette() { $("palette").classList.add("hidden"); }

function renderPalette() {
  const list = $("palette-list");
  list.innerHTML = paletteFiltered.slice(0, 20).map((it, i) => `
    <li class="${i === paletteIndex ? 'selected' : ''}" data-idx="${i}">
      <span class="pal-icon">${it.icon}</span>
      <span class="pal-title">${escapeHtml(it.title)}</span>
      <span class="pal-hint">${it.cmd ? "⏎ send" : "⏎ open"}</span>
    </li>`).join("");
  list.querySelectorAll("li").forEach(li =>
    li.addEventListener("click", () => runPaletteItem(+li.dataset.idx))
  );
}

function filterPalette(query) {
  const q = query.toLowerCase().trim();
  paletteFiltered = !q ? PALETTE_ITEMS.slice()
    : PALETTE_ITEMS.filter(it => it.title.toLowerCase().includes(q));
  paletteIndex = 0;
  renderPalette();
}

function runPaletteItem(idx) {
  const item = paletteFiltered[idx];
  if (!item) return;
  closePalette();
  if (item.action) item.action();
  else if (item.cmd) sendText(item.cmd);
}

/* ═══════════════════════════════════════════════════════════════
   13b. IMAGE GENERATION MODAL
   ═══════════════════════════════════════════════════════════════ */
async function openImageGen() {
  openModal("imagegen-modal");
  await loadRecentImages();
}
async function loadRecentImages() {
  try {
    const r = await fetch(`${API_BASE}/imagegen/recent`);
    const recent = await r.json();
    const grid = $("imagegen-recent");
    if (!recent.length) {
      grid.innerHTML = "<p style='color:var(--text-dim);font-size:12px;grid-column:1/-1;'>No images yet.</p>";
      return;
    }
    grid.innerHTML = recent.map(r => `
      <img src="${r.url}" alt="${escapeHtml(r.prompt)}" title="${escapeHtml(r.prompt)}" loading="lazy" data-prompt="${escapeHtml(r.prompt)}" />
    `).join("");
    grid.querySelectorAll("img").forEach(img => {
      img.addEventListener("click", () => {
        $("imagegen-preview").innerHTML = `<img src="${img.src}" />`;
      });
    });
  } catch (e) { console.warn(e); }
}

async function generateImage() {
  const prompt = $("imagegen-prompt").value.trim();
  if (!prompt) { toast("Enter a prompt first", "warn"); return; }
  const btn = $("imagegen-go");
  const progress = $("imagegen-progress");
  const preview = $("imagegen-preview");
  btn.disabled = true;
  progress.classList.remove("hidden");
  preview.innerHTML = "";
  try {
    const r = await fetch(`${API_BASE}/imagegen`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Failed");
    preview.innerHTML = `<img src="${data.url}" alt="${escapeHtml(prompt)}" />`;
    toast("Image generated!", "success");
    loadRecentImages();
    // Also add to chat
    addMessage(`🎨 Generated: ${prompt}`, "user");
    addImageMessage(data.url, prompt);
  } catch (e) {
    toast(e.message, "error");
    preview.innerHTML = `<p style="color:var(--danger);padding:20px;">❌ ${escapeHtml(e.message)}</p>`;
  } finally {
    btn.disabled = false;
    progress.classList.add("hidden");
  }
}

/* ═══════════════════════════════════════════════════════════════
   13c. EMAIL / WHATSAPP MODAL
   ═══════════════════════════════════════════════════════════════ */
function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(b =>
    b.classList.toggle("active", b.dataset.tab === tabId)
  );
  document.querySelectorAll(".tab-content").forEach(c =>
    c.classList.toggle("hidden", c.id !== tabId)
  );
}

function sendEmailFromModal() {
  const to = $("em-to").value.trim();
  const subject = $("em-subject").value.trim();
  const body = $("em-body").value.trim();
  if (!to) { toast("Enter recipient email", "warn"); return; }
  const params = new URLSearchParams();
  if (to) params.set("to", to);
  if (subject) params.set("su", subject);
  if (body) params.set("body", body);
  window.open(`https://mail.google.com/mail/?view=cm&fs=1&${params}`, "_blank");
  toast("Opening Gmail...", "info");
  closeModal("email-modal");
}

function sendWhatsAppFromModal() {
  const phone = $("wa-phone").value.replace(/\D/g, "");
  const message = $("wa-message").value.trim();
  if (!message) { toast("Enter a message", "warn"); return; }
  const url = phone
    ? `https://web.whatsapp.com/send?phone=${phone}&text=${encodeURIComponent(message)}`
    : `https://web.whatsapp.com/send?text=${encodeURIComponent(message)}`;
  window.open(url, "_blank");
  toast("Opening WhatsApp...", "info");
  closeModal("email-modal");
}

/* ═══════════════════════════════════════════════════════════════
   13b. AI SETTINGS (provider + API key)
   ═══════════════════════════════════════════════════════════════ */
async function openSettings() {
  openModal("settings-modal");
  const dot = document.querySelector("#settings-status .status-dot");
  const txt = $("settings-status-text");
  if (txt) txt.textContent = "Checking AI brain…";
  try {
    const s = await (await fetch(`${API_BASE}/llm/status`)).json();
    if ($("settings-provider")) $("settings-provider").value = s.provider || "auto";
    if ($("settings-model")) $("settings-model").value = s.model || "";
    if ($("settings-key")) $("settings-key").value = "";
    const ok = s.ok;
    if (dot) dot.style.background = ok ? "#4caf50" : "#ffb300";
    if (txt) {
      txt.textContent = ok
        ? `Connected · ${s.label || s.provider} · model: ${s.model}${s.key_set ? " · key set" : " · no key (free)"}`
        : (s.last_error || "Not connected");
    }
  } catch {
    if (txt) txt.textContent = "Backend unreachable";
  }
}

async function saveSettings() {
  const provider = $("settings-provider")?.value || "auto";
  const api_key  = $("settings-key")?.value.trim() || "";
  const model    = $("settings-model")?.value.trim() || "";
  const btn = $("settings-save");
  if (btn) { btn.disabled = true; btn.textContent = "Saving…"; }
  try {
    const r = await fetch(`${API_BASE}/llm/config`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider, api_key, model }),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.detail || "Save failed");
    toast(`AI connected via ${d.label || d.provider}`, "success", 4000);
    if ($("settings-status-text"))
      $("settings-status-text").textContent =
        `Connected · ${d.label || d.provider} · model: ${d.model}`;
    const dot = document.querySelector("#settings-status .status-dot");
    if (dot) dot.style.background = "#4caf50";
    if ($("settings-key")) $("settings-key").value = "";
  } catch (e) {
    toast(e.message || "Could not save settings", "error");
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "💾 Save & Connect"; }
  }
}

async function testLLM() {
  const txt = $("settings-status-text");
  const dot = document.querySelector("#settings-status .status-dot");
  if (txt) txt.textContent = "Testing…";
  if (dot) dot.style.background = "#ffb300";
  try {
    const d = await (await fetch(`${API_BASE}/llm/test`, { method: "POST" })).json();
    if (d.ok) {
      if (txt) txt.textContent = `✅ Working! (${d.provider}) · reply: ${d.reply}`;
      if (dot) dot.style.background = "#4caf50";
      toast("AI is working!", "success");
    } else {
      if (txt) txt.textContent = `❌ ${d.error || "Test failed"}`;
      if (dot) dot.style.background = "#ff5370";
      toast("AI test failed — check key/provider", "error");
    }
  } catch {
    if (txt) txt.textContent = "❌ Backend unreachable";
    toast("Cannot reach backend", "error");
  }
}

/* ═══════════════════════════════════════════════════════════════
   14. EVENT BINDINGS
   ═══════════════════════════════════════════════════════════════ */
sendBtn.addEventListener("click", () => sendText(input.value));
input.addEventListener("keydown", (e) => { if (e.key === "Enter") sendText(input.value); });
micBtn.addEventListener("click", startListening);

document.querySelectorAll(".quick-btn").forEach(b => b.addEventListener("click", () => sendText(b.dataset.cmd)));
document.querySelectorAll(".theme-btn").forEach(b => b.addEventListener("click", () => setTheme(b.dataset.theme)));
document.querySelectorAll(".lang-btn").forEach(b => b.addEventListener("click", () => setLanguage(b.dataset.lang)));

$("personality-select")?.addEventListener("change", e => setPersonality(e.target.value));
$("wake-toggle")?.addEventListener("change", e => e.target.checked ? startWakeWord() : stopWakeWord());
$("autodetect-toggle")?.addEventListener("change", e => {
  autoDetectLang = e.target.checked;
  toast(autoDetectLang ? "Auto-detect ON" : "Auto-detect OFF", "info", 1500);
});
$("stream-toggle")?.addEventListener("change", e => {
  streamingOn = e.target.checked;
  toast(streamingOn ? "Streaming ON" : "Streaming OFF", "info", 1500);
});

// Sidebar buttons
$("notes-btn")?.addEventListener("click", () => { openModal("notes-modal"); renderNotes(); });
$("pdf-btn")?.addEventListener("click",   () => { openModal("pdf-modal"); renderPDFList(); });
$("image-btn")?.addEventListener("click", () => { openModal("image-modal"); renderImageList(); });
$("imagegen-btn")?.addEventListener("click", openImageGen);
$("email-btn")?.addEventListener("click", () => openModal("email-modal"));
$("backend-retry")?.addEventListener("click", async () => {
  setBackendBanner(true, "Checking backend…");
  if (await pingBackend()) backendReconnected();
  else toast("Still offline — make sure the START.bat window is open", "error");
});
$("settings-btn")?.addEventListener("click", openSettings);
$("settings-save")?.addEventListener("click", saveSettings);
$("settings-test")?.addEventListener("click", testLLM);
$("stats-btn")?.addEventListener("click", openStats);
$("export-btn")?.addEventListener("click", exportChat);
$("clear-btn")?.addEventListener("click", clearHistory);
$("stats-reset")?.addEventListener("click", resetStats);

// Image generation
$("imagegen-go")?.addEventListener("click", generateImage);
$("imagegen-prompt")?.addEventListener("keydown", e => { if (e.key === "Enter") generateImage(); });

// Email / WhatsApp
document.querySelectorAll(".tab-btn").forEach(b =>
  b.addEventListener("click", () => switchTab(b.dataset.tab))
);
$("em-send")?.addEventListener("click", sendEmailFromModal);
$("wa-send")?.addEventListener("click", sendWhatsAppFromModal);

// Avatar click reaction
$("avatar-3d")?.addEventListener("click", () => {
  const av = $("avatar-3d");
  av.classList.add("talking");
  setTimeout(() => av.classList.remove("talking"), 800);
  toast("Hello, boss! 👋", "info", 1500);
});

// Note input
$("add-note-btn")?.addEventListener("click", addNote);
$("new-note-input")?.addEventListener("keydown", e => { if (e.key === "Enter") addNote(); });

// PDF / Image uploads
$("pdf-upload")?.addEventListener("change", e => { if (e.target.files[0]) uploadPDF(e.target.files[0]); e.target.value = ""; });
$("image-upload")?.addEventListener("change", e => { if (e.target.files[0]) uploadImage(e.target.files[0]); e.target.value = ""; });
$("pdf-banner-close")?.addEventListener("click", async () => {
  await fetch(`${API_BASE}/pdf/select`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filename: "___none___" }) }).catch(()=>{});
  updatePDFBanner(null);
});
$("image-banner-close")?.addEventListener("click", async () => {
  await fetch(`${API_BASE}/image/select`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filename: "___none___" }) }).catch(()=>{});
  updateImageBanner(null);
});

// Drag & drop
document.querySelectorAll(".upload-box").forEach(box => {
  ["dragover", "dragenter"].forEach(ev => box.addEventListener(ev, e => { e.preventDefault(); box.classList.add("drag"); }));
  ["dragleave", "drop"].forEach(ev => box.addEventListener(ev, e => { e.preventDefault(); box.classList.remove("drag"); }));
  box.addEventListener("drop", e => {
    const f = e.dataTransfer.files[0];
    if (!f) return;
    const modalId = box.closest(".modal")?.id;
    if (modalId === "pdf-modal") uploadPDF(f);
    else if (modalId === "image-modal") uploadImage(f);
  });
});

// Modal close (unified)
document.querySelectorAll("[data-close]").forEach(btn => btn.addEventListener("click", () => closeModal(btn.dataset.close)));
document.querySelectorAll(".modal").forEach(m => m.addEventListener("click", e => { if (e.target === m) m.classList.add("hidden"); }));

// Command palette
$("palette-btn")?.addEventListener("click", openPalette);
$("palette")?.addEventListener("click", e => { if (e.target.id === "palette") closePalette(); });
$("palette-input")?.addEventListener("input", e => filterPalette(e.target.value));
$("palette-input")?.addEventListener("keydown", e => {
  if (e.key === "ArrowDown") { e.preventDefault(); paletteIndex = Math.min(paletteIndex + 1, Math.min(paletteFiltered.length, 20) - 1); renderPalette(); }
  else if (e.key === "ArrowUp") { e.preventDefault(); paletteIndex = Math.max(paletteIndex - 1, 0); renderPalette(); }
  else if (e.key === "Enter") { e.preventDefault(); runPaletteItem(paletteIndex); }
  else if (e.key === "Escape") { closePalette(); }
});

// Global keyboard shortcuts
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "/") { e.preventDefault(); startListening(); }
  if (e.ctrlKey && e.key.toLowerCase() === "l") { e.preventDefault(); clearHistory(); }
  if (e.ctrlKey && e.key.toLowerCase() === "k") { e.preventDefault(); openPalette(); }
  if (e.key === "Escape") {
    document.querySelectorAll(".modal:not(.hidden), .palette:not(.hidden)").forEach(m => m.classList.add("hidden"));
  }
});

/* ═══════════════════════════════════════════════════════════════
   15. INIT
   ═══════════════════════════════════════════════════════════════ */
window.addEventListener("load", async () => {
  playSplash(); // start splash animation immediately

  loadTheme();
  loadLanguage();
  loadHistory();
  loadPersonality();
  fitCanvas();
  drawIdle();

  fetch(`${API_BASE}/pdf`).then(r => r.json()).then(d => updatePDFBanner(d.active)).catch(()=>{});
  fetch(`${API_BASE}/image`).then(r => r.json()).then(d => updateImageBanner(d.active)).catch(()=>{});

  if (window.speechSynthesis) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
  }

  try {
    const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
    if (!res.ok) throw new Error("health " + res.status);
    const h = await res.json();
    backendReconnected(); // clears any offline banner, marks Ready
    if (!h.llm_ok) {
      setTimeout(() => toast("AI brain not connected — open ⚙️ AI Settings to pick a free provider.", "warn", 7000), 2500);
    } else if (h.llm_provider === "pollinations") {
      setTimeout(() => toast("AI ready (free tier). For unlimited speed, add a free Groq key in ⚙️ AI Settings.", "info", 6500), 2500);
    } else {
      setTimeout(() => toast(`AI ready · ${h.llm_provider}`, "success", 3000), 2500);
    }
  } catch {
    // Backend not up yet / not reachable — show banner and keep retrying
    setTimeout(() => { backendWentOffline(); toast("Backend unreachable — is START.bat running?", "error", 6000); }, 1200);
  }

  // Register service worker for PWA / offline support
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js")
      .then(() => console.log("SW registered"))
      .catch(err => console.warn("SW failed:", err));
  }
});
window.addEventListener("resize", () => { fitCanvas(); drawIdle(); });
