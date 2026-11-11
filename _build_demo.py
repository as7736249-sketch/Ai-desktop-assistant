#!/usr/bin/env python3
"""Assemble a standalone demo.html (real UI + mocked backend, no server needed)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
css = (ROOT / "frontend/css/style.css").read_text(encoding="utf-8")
js = (ROOT / "frontend/js/app.js").read_text(encoding="utf-8")

# ── The mock backend shim (injected BEFORE app.js) ──────────────────────
SHIM = r"""
/* ═══════════════════════════════════════════════════════════════════
   DEMO SHIM — safe localStorage + mocked backend (/api/*) so the whole
   site runs in the browser with no Python server. Everything is fake.
   ═══════════════════════════════════════════════════════════════════ */
(function () {
  // 1) localStorage fallback (sandboxed iframes may block real storage)
  try { window.localStorage.getItem("__probe__"); }
  catch (e) {
    var mem = {};
    Object.defineProperty(window, "localStorage", { configurable: true, value: {
      getItem: function (k) { return (k in mem) ? mem[k] : null; },
      setItem: function (k, v) { mem[k] = String(v); },
      removeItem: function (k) { delete mem[k]; },
      clear: function () { mem = {}; },
      key: function (i) { return Object.keys(mem)[i] || null; },
      get length() { return Object.keys(mem).length; }
    }});
  }

  var state = { personality: "jarvis", lang: "en", notes: [],
    stats: {
      total_commands: 57, total_llm_calls: 23, unique_command_types: 8,
      top_commands: [
        { name: "time", count: 14 }, { name: "weather", count: 11 },
        { name: "joke", count: 9 }, { name: "hello", count: 8 },
        { name: "calc", count: 7 }, { name: "news", count: 5 }
      ],
      daily_activity: (function () {
        var a = [], n = [3,5,2,7,4,9,6,3,8,5,10,7,4,6];
        for (var i = 0; i < 14; i++) a.push({ date: "Day " + (i + 1), count: n[i] });
        return a;
      })()
    }
  };

  var PERSONA = {
    jarvis: "Obviously, sir. ",
    friendly: "Aww, great question! ",
    professional: "Understood. ",
    sassy: "Oh honey. ",
    teacher: "Great question — let's break it down. ",
    gen_z: "Ngl bro, "
  };
  var JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs. 😄",
    "I told my computer I needed a break… now it won't stop sending me KitKat ads.",
    "There are 10 types of people: those who understand binary and those who don't.",
    "Why did the developer go broke? Because he used up all his cache."
  ];
  var QUOTES = [
    "“The only way to do great work is to love what you do.” — Steve Jobs",
    "“Believe you can and you're halfway there.” — Theodore Roosevelt",
    "“It always seems impossible until it's done.” — Nelson Mandela"
  ];
  function pick(a) { return a[Math.floor(Math.random() * a.length)]; }

  function detectLang(t) {
    if (/[\u0900-\u097F]/.test(t)) return "hi";
    if (/[\u0A00-\u0A7F]/.test(t)) return "pa";
    return "en";
  }

  function tryCalc(t) {
    var e = t.replace(/what is|what's|calculate|compute|how much is/g, "")
             .replace(/plus/g, "+").replace(/minus/g, "-")
             .replace(/times/g, "*").replace(/multiplied by/g, "*")
             .replace(/divided by/g, "/").replace(/ x /g, "*")
             .replace(/\?/g, "");
    e = e.replace(/[^0-9+\-*/().\s]/g, "").trim();
    if (!/\d/.test(e) || !/[+\-*/]/.test(e)) return null;
    try { var r = Function('"use strict";return (' + e + ')')();
      if (typeof r === "number" && isFinite(r)) return String(+r.toFixed(4)); } catch (x) {}
    return null;
  }

  function aiReply(text) {
    var t = text.toLowerCase().trim();
    var now = new Date();
    if (/^(hi|hello|hey|hii+|namaste|yo)\b/.test(t))
      return "Hello, Boss! 👋 I'm running in DEMO mode — all replies are simulated right here in your browser, no server needed.";
    if (/\btime\b/.test(t))
      return "The time is " + now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + " (demo).";
    if (/\bdate\b/.test(t))
      return "Today is " + now.toLocaleDateString([], { weekday: "long", year: "numeric", month: "long", day: "numeric" }) + " (demo).";
    if (/what day|which day/.test(t))
      return "It's " + now.toLocaleDateString([], { weekday: "long" }) + " (demo).";
    var c = tryCalc(t);
    if (c !== null) return "The answer is " + c + " (demo).";
    if (/joke|laugh/.test(t)) return pick(JOKES);
    if (/weather|temperature/.test(t)) return "It's a pleasant 27°C in Ludhiana with clear skies 🌤️ (demo data).";
    if (/news|headline/.test(t)) return "Top stories right now: a major AI breakthrough, tech markets rally, and a thrilling cricket finish (demo headlines).";
    if (/quote|motivat|inspire/.test(t)) return pick(QUOTES);
    if (/who is|wikipedia|tell me about/.test(t)) return "This is a DEMO — in the real app I'd look that up on Wikipedia and answer you. Try asking about a person or place.";
    if (/draw|generate image|picture/.test(t)) return "🎨 In the full app I'd generate an actual image — open the '🎨 Generate Image' panel to see a sample!";
    var p = PERSONA[state.personality] || "";
    return p + 'Here is a simulated answer to "' + text.slice(0, 70) +
      '": this DEMO replies instantly in your browser. In the real Jarvis, a live AI model answers using your chosen personality. Try "what time is it", "tell me a joke", or "what is 12 times 8".';
  }

  function json(obj, status) {
    return new Response(JSON.stringify(obj), { status: status || 200,
      headers: { "Content-Type": "application/json" } });
  }
  function sseStream(full) {
    var words = full.split(" "), i = 0, enc = new TextEncoder();
    var stream = new ReadableStream({
      pull: function (c) {
        if (i >= words.length) { c.enqueue(enc.encode("data: [DONE]\n\n")); c.close(); return; }
        var w = words[i] + (i < words.length - 1 ? " " : "");
        c.enqueue(enc.encode("data: " + w + "\n\n")); i++;
      }
    });
    return new Response(stream, { status: 200, headers: { "Content-Type": "text/event-stream" } });
  }
  function svgImage(prompt) {
    var txt = (prompt || "AI image").slice(0, 40).replace(/[<>&]/g, "");
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512">'
      + '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
      + '<stop offset="0" stop-color="#00e5ff"/><stop offset="0.5" stop-color="#7c4dff"/>'
      + '<stop offset="1" stop-color="#ff4081"/></linearGradient></defs>'
      + '<rect width="512" height="512" fill="url(#g)"/>'
      + '<circle cx="256" cy="210" r="90" fill="rgba(255,255,255,0.25)"/>'
      + '<text x="256" y="430" font-family="sans-serif" font-size="26" fill="#fff" '
      + 'text-anchor="middle">🎨 ' + txt + '</text>'
      + '<text x="256" y="470" font-family="sans-serif" font-size="16" fill="rgba(255,255,255,0.8)" '
      + 'text-anchor="middle">DEMO image</text></svg>';
    return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  }

  var realFetch = window.fetch ? window.fetch.bind(window) : function () {
    return Promise.reject(new Error("no fetch")); };

  window.fetch = function (input, init) {
    var url = (typeof input === "string") ? input : (input && input.url) || "";
    var method = (init && init.method) || "GET";
    var bodyStr = init && typeof init.body === "string" ? init.body : "";
    var idx = url.indexOf("/api/");
    if (idx === -1) return realFetch(input, init);
    var path = url.slice(idx);               // e.g. "/api/chat"
    var q = path.indexOf("?"); if (q !== -1) path = path.slice(0, q);

    // chat (streaming)
    if (path === "/api/chat/stream") {
      var txt = "";
      try { txt = JSON.parse(bodyStr).text || ""; } catch (e) {}
      return Promise.resolve(sseStream(aiReply(txt)));
    }
    // chat (classic)
    if (path === "/api/chat") {
      var t2 = "";
      try { t2 = JSON.parse(bodyStr).text || ""; } catch (e) {}
      return Promise.resolve(json({ user: t2, reply: aiReply(t2),
        source: "llm", detected_lang: detectLang(t2) }));
    }
    if (path === "/api/health") {
      return Promise.resolve(json({ status: "ok", version: "5.1.0-demo", lang: state.lang,
        personality: state.personality, llm_ok: true, llm_provider: "demo",
        llm_model: "demo-model", llm_key_set: false, calendar_ok: false,
        active_pdf: null, active_image: null, pdf_count: 0, image_count: 0 }));
    }
    if (path === "/api/personalities") {
      return Promise.resolve(json({ current: state.personality,
        available: ["jarvis","friendly","professional","sassy","teacher","gen_z"] }));
    }
    if (path === "/api/personality") {
      try { state.personality = JSON.parse(bodyStr).name || "jarvis"; } catch (e) {}
      return Promise.resolve(json({ ok: true, current: state.personality }));
    }
    if (path === "/api/language") {
      if (method === "POST") { try { state.lang = JSON.parse(bodyStr).lang; } catch (e) {} }
      return Promise.resolve(json({ current: state.lang,
        available: { en: "English", hi: "हिंदी", pa: "ਪੰਜਾਬੀ" } }));
    }
    // notes
    if (path === "/api/notes") {
      if (method === "POST") {
        var nt = ""; try { nt = JSON.parse(bodyStr).text || ""; } catch (e) {}
        state.notes.push({ id: Date.now(), text: nt, done: false });
        return Promise.resolve(json({ ok: true, message: "Note added (demo)" }));
      }
      if (method === "DELETE") { state.notes = []; return Promise.resolve(json({ ok: true })); }
      return Promise.resolve(json(state.notes));
    }
    if (/^\/api\/notes\/\d+\/toggle$/.test(path)) {
      var id = parseInt(path.split("/")[3], 10);
      state.notes.forEach(function (n) { if (n.id === id) n.done = !n.done; });
      return Promise.resolve(json({ ok: true }));
    }
    if (/^\/api\/notes\/\d+$/.test(path)) {
      var did = parseInt(path.split("/")[3], 10);
      state.notes = state.notes.filter(function (n) { return n.id !== did; });
      return Promise.resolve(json({ ok: true }));
    }
    // pdf / image — empty (uploads simulated)
    if (path === "/api/pdf" || path === "/api/image")
      return Promise.resolve(json({ active: null, documents: [], images: [] }));
    if (path.indexOf("/api/pdf/") === 0 || path.indexOf("/api/image/") === 0)
      return Promise.resolve(json({ ok: true }));
    // stats
    if (path === "/api/stats") {
      if (method === "DELETE") return Promise.resolve(json({ ok: true }));
      return Promise.resolve(json(state.stats));
    }
    // export
    if (path === "/api/export/markdown") {
      var md = "# Jarvis Chat (DEMO export)\n\n";
      try { JSON.parse(bodyStr).messages.forEach(function (m) { md += "**" + m.who + ":** " + m.text + "\n\n"; }); } catch (e) {}
      return Promise.resolve(new Response(md, { status: 200, headers: { "Content-Type": "text/markdown" } }));
    }
    // image generation
    if (path === "/api/imagegen") {
      var pr = ""; try { pr = JSON.parse(bodyStr).prompt || ""; } catch (e) {}
      return Promise.resolve(json({ ok: true, url: svgImage(pr), prompt: pr }));
    }
    if (path === "/api/imagegen/recent") return Promise.resolve(json([]));
    // web search
    if (path === "/api/search") {
      var sq = ""; try { sq = JSON.parse(bodyStr).query || ""; } catch (e) {}
      return Promise.resolve(json({ result: "🔎 DEMO search result for \"" + sq + "\": in the real app this returns live web results from DuckDuckGo." }));
    }
    // llm settings
    if (path === "/api/llm/status")
      return Promise.resolve(json({ provider: "demo", model: "demo-model", key_set: false,
        ok: true, last_error: "", label: "Demo mode — simulated AI (no key needed)",
        available: ["demo"] }));
    if (path === "/api/llm/config")
      return Promise.resolve(json({ ok: true, provider: "demo", model: "demo-model",
        key_set: false, label: "Demo mode — simulated AI (no key needed)", available: ["demo"] }));
    if (path === "/api/llm/test")
      return Promise.resolve(json({ ok: true, provider: "demo", reply: "OK (demo)" }));

    return Promise.resolve(json({ ok: true }));
  };
})();
"""

# ── Transforms ──────────────────────────────────────────────────────────
# remove manifest link, inline CSS, inline shim + app.js
html = html.replace('<link rel="manifest" href="/manifest.webmanifest" />', "")
html = html.replace('<link rel="stylesheet" href="/css/style.css" />',
                    "<style>\n" + css + "\n</style>")
shim_safe = SHIM.replace("</script", "<\\/script")
js_safe = js.replace("</script", "<\\/script")
html = html.replace('<script src="/js/app.js"></script>',
                    "<script>\n" + shim_safe + "\n</script>\n<script>\n" + js_safe + "\n</script>")

# Add a visible DEMO badge
badge = """
<style>
#demo-badge{position:fixed;top:12px;right:14px;z-index:99999;display:flex;gap:8px;
  align-items:center;background:linear-gradient(90deg,#7c4dff,#00e5ff);color:#05131f;
  font:700 12px/1 system-ui,sans-serif;padding:8px 12px;border-radius:999px;
  box-shadow:0 4px 18px rgba(0,0,0,.35);letter-spacing:.04em}
#demo-badge span{font-weight:800}
</style>
<div id="demo-badge">● <span>DEMO</span> · simulated AI · no server</div>
"""
html = html.replace("</body>", badge + "\n</body>")

out = ROOT / "demo.html"
out.write_text(html, encoding="utf-8")
print("Wrote", out, "(", len(html), "bytes )")
