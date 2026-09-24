(() => {
  "use strict";

  // ---- Shared colours ----
  const BLUE = "#1565c0";
  const GREEN = "#2e7d32";
  const RED = "#d32f2f";
  const INK = "#16232a";
  const INK_SOFT = "#4f6168";
  const BRAND = "#007094";
  const NEUTRAL = "#eef3f4";
  const DOT = "#8fa2a8";

  const STROOP_COLORS = [
    { name: "ROT", hex: RED },
    { name: "GRÜN", hex: GREEN },
    { name: "BLAU", hex: BLUE },
    { name: "GELB", hex: "#f2a900" },
    { name: "LILA", hex: "#7e4fbe" },
  ];

  const DIR4 = [["Vorne", 0], ["Rechts", 90], ["Hinten", 180], ["Links", 270]];
  const DIR_DIAG = [["Vorne-Rechts", 45], ["Hinten-Rechts", 135], ["Hinten-Links", 225], ["Vorne-Links", 315]];
  const DIR8 = [...DIR4, ...DIR_DIAG].sort((a, b) => a[1] - b[1]);

  // ---- Colour library for VT/VRW. The client picks MIN_COLORS..MAX_COLORS
  // of these and they are mixed at random. Raise MAX_COLORS (and add colours
  // here) if an exercise ever needs more than four.
  const COLOR_LIB = [
    { key: "rot", name: "Rot", hex: "#d32f2f" },
    { key: "gelb", name: "Gelb", hex: "#f2a900" },
    { key: "gruen", name: "Grün", hex: "#2e7d32" },
    { key: "blau", name: "Blau", hex: "#1565c0" },
    { key: "orange", name: "Orange", hex: "#ff9110" },
    { key: "lila", name: "Lila", hex: "#7e4fbe" },
    { key: "pink", name: "Pink", hex: "#e6399b" },
  ];
  const COLOR_BY_KEY = Object.fromEntries(COLOR_LIB.map((c) => [c.key, c]));
  const MIN_COLORS = 2;
  const MAX_COLORS = 4;

  // Legacy three-colour palettes from the production ARCHITECTURE/PALETTES
  // files. Programmes stored before the free colour picker existed reference
  // these by code ("palette": "ORL"), so they stay resolvable with their
  // exact original shades.
  const C = { orange: "#ff9110", rot: "#d32f2f", lila: "#7e4fbe", blau: "#1565c0", gruen: "#2e7d32", gelb: "#f2a900" };
  const N = { orange: "Orange", rot: "Rot", lila: "Lila", blau: "Blau", gruen: "Grün", gelb: "Gelb" };
  const col = (k) => ({ name: N[k], hex: C[k] });
  const PALETTES = {
    ORL: [{ name: "Orange", hex: "#ff911f" }, { name: "Rot", hex: "#e84835" }, col("lila")],
    RGB: [col("rot"), col("blau"), col("gruen")],
    RGY: [col("rot"), col("gruen"), col("gelb")],
    RYB: [col("rot"), col("gelb"), col("blau")],
    YGB: [col("gelb"), col("gruen"), col("blau")],
    ORB: [col("orange"), col("rot"), col("blau")],
    ORG: [col("orange"), col("rot"), col("gruen")],
    ORY: [col("orange"), col("rot"), col("gelb")],
    OLB: [col("orange"), col("lila"), col("blau")],
    OLG: [col("orange"), col("lila"), col("gruen")],
    OLY: [col("orange"), col("lila"), col("gelb")],
    OBG: [col("orange"), col("blau"), col("gruen")],
    OBY: [col("orange"), col("blau"), col("gelb")],
    OGY: [col("orange"), col("gruen"), col("gelb")],
    RLB: [col("rot"), col("lila"), col("blau")],
    RLG: [col("rot"), col("lila"), col("gruen")],
    RLY: [col("rot"), col("lila"), col("gelb")],
    LBG: [col("lila"), col("blau"), col("gruen")],
    LBY: [col("lila"), col("blau"), col("gelb")],
    LGY: [col("lila"), col("gruen"), col("gelb")],
  };

  // Colours of a programme block: free selection ("colors": ["rot","blau"]),
  // a legacy palette code, or the ORL default.
  function blockColors(block) {
    if (Array.isArray(block.colors)) {
      const list = block.colors.map((k) => COLOR_BY_KEY[k]).filter(Boolean);
      if (list.length >= MIN_COLORS) return { colors: list, seedKey: block.colors.join("-") };
    }
    const id = PALETTES[block.palette] ? block.palette : "ORL";
    return { colors: PALETTES[id], seedKey: id };
  }
  function keysToColors(keys) {
    return COLOR_LIB.filter((c) => keys.includes(c.key));
  }

  // ---- Seeded RNG (mulberry32) so a fixed "Reihenfolge" always
  // reproduces the exact same stimulus order for the same settings.
  // "Zufällig" keeps using Math.random for a fresh draw each run.
  function mulberry32(seed) {
    return function () {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function hashSeed(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
    return h;
  }

  // ---- Small helpers ----
  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  }
  function fmtClock(sec) {
    const s = Math.max(0, Math.ceil(sec));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  }
  function fmtMinutes(sec) {
    if (sec < 60) return `${Math.max(1, Math.round(sec))} Sek`;
    const m = Math.round(sec / 30) / 2;
    return `${String(m).replace(".", ",")} Min`;
  }
  function fmtSeconds(sec) {
    return `${String(Math.round(sec * 10) / 10).replace(".", ",")} s`;
  }
  function programSeconds(def) {
    const pause = def.pauseS ?? 15;
    return def.blocks.reduce((sum, b, i) => sum + b.duration + (i > 0 ? (b.pauseS ?? pause) : 0), 0);
  }
  function exerciseCountLabel(n) {
    return n === 1 ? "1 Übung" : `${n} Übungen`;
  }
  function colorDots(colors) {
    return `<span class="dots">${colors.map((c) => `<span class="dot" style="background:${c.hex}"></span>`).join("")}</span>`;
  }

  // ---- Audio: spoken direction words (Web Speech API) + a plain beep ----
  let audioCtx = null;
  function ensureAudioCtx() {
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    if (!audioCtx) audioCtx = new AC();
    if (audioCtx.state === "suspended") audioCtx.resume().catch(() => {});
    return audioCtx;
  }
  function playBeep() {
    const ac = ensureAudioCtx();
    if (!ac) return;
    const osc = ac.createOscillator();
    const gain = ac.createGain();
    osc.type = "sine";
    osc.frequency.value = 880;
    gain.gain.setValueAtTime(0.0001, ac.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.35, ac.currentTime + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + 0.2);
    osc.connect(gain).connect(ac.destination);
    osc.start();
    osc.stop(ac.currentTime + 0.22);
  }
  let deVoice = null;
  function pickVoice() {
    if (!window.speechSynthesis) return;
    const voices = speechSynthesis.getVoices();
    deVoice = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("de")) || voices[0] || null;
  }
  if (window.speechSynthesis) {
    pickVoice();
    speechSynthesis.onvoiceschanged = pickVoice;
  }
  function speakWord(word) {
    if (!window.speechSynthesis) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(word);
    u.lang = "de-DE";
    if (deVoice) u.voice = deVoice;
    u.rate = 1.0;
    speechSynthesis.speak(u);
  }

  // Arrow geometry as fractions of `unit` (half the smaller canvas
  // dimension) so it fills any aspect ratio edge-to-edge without clipping.
  const F_TIP = 0.704, F_HEADBASE = 0.426, F_TAIL = 0.685, F_SHAFT = 0.157, F_HEAD = 0.315;

  function rotate(f, l, theta, cx, cy) {
    const dx = f * Math.sin(theta) + l * Math.cos(theta);
    const dy = -f * Math.cos(theta) + l * Math.sin(theta);
    return [cx + dx, cy + dy];
  }

  function arrowPoints(angleDeg, cx, cy, unit) {
    const theta = (angleDeg * Math.PI) / 180;
    const Ltip = F_TIP * unit, Lhead = F_HEADBASE * unit, Ltail = F_TAIL * unit;
    const Ws = F_SHAFT * unit, Wh = F_HEAD * unit;
    const local = [
      [Ltip, 0], [Lhead, Wh], [Lhead, Ws],
      [-Ltail, Ws], [-Ltail, -Ws], [Lhead, -Ws], [Lhead, -Wh],
    ];
    return local.map(([f, l]) => rotate(f, l, theta, cx, cy));
  }

  function fitText(ctx, text, maxW, startSize, family, weight = 800) {
    let size = startSize;
    while (size > 10) {
      ctx.font = `${weight} ${size}px ${family}`;
      if (ctx.measureText(text).width <= maxW) break;
      size -= 2;
    }
    return size;
  }

  function wrapLines(ctx, text, maxW) {
    const words = text.split(/\s+/);
    const lines = [];
    let line = "";
    words.forEach((w) => {
      const test = line ? line + " " + w : w;
      if (ctx.measureText(test).width > maxW && line) { lines.push(line); line = w; } else { line = test; }
    });
    if (line) lines.push(line);
    return lines;
  }

  // ---- Canvas rendering ----
  const canvas = document.getElementById("stage");
  const ctx = canvas.getContext("2d");

  function fitCanvas() {
    const rect = canvas.parentElement.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
  }

  function barCaption(cw, ch, text, atTop) {
    const barH = Math.max(46, ch * 0.065);
    const y0 = atTop ? 0 : ch - barH;
    ctx.fillStyle = "#f5f5f5";
    ctx.fillRect(0, y0, cw, barH);
    ctx.fillStyle = INK;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const size = fitText(ctx, text, cw * 0.94, Math.round(barH * 0.38), "'Public Sans', sans-serif", 700);
    ctx.font = `700 ${size}px 'Public Sans', sans-serif`;
    ctx.fillText(text, cw / 2, y0 + barH / 2);
    return barH;
  }

  function drawSpeakerIcon(x, y, r, muted) {
    ctx.save();
    ctx.fillStyle = muted ? "#5c6e75" : "#16232a";
    ctx.strokeStyle = ctx.fillStyle;
    ctx.lineWidth = Math.max(2, r * 0.12);
    const w = r * 0.5;
    ctx.beginPath();
    ctx.moveTo(x - r, y - w * 0.5);
    ctx.lineTo(x - r * 0.4, y - w * 0.5);
    ctx.lineTo(x - r * 0.05, y - r * 0.9);
    ctx.lineTo(x - r * 0.05, y + r * 0.9);
    ctx.lineTo(x - r * 0.4, y + w * 0.5);
    ctx.lineTo(x - r, y + w * 0.5);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath(); ctx.arc(x - r * 0.05, y, r * 0.55, -0.6, 0.6); ctx.stroke();
    ctx.beginPath(); ctx.arc(x - r * 0.05, y, r * 0.95, -0.5, 0.5); ctx.stroke();
    ctx.restore();
  }

  function drawBellIcon(x, y, r) {
    ctx.save();
    ctx.fillStyle = "#5c6e75";
    ctx.beginPath();
    ctx.arc(x, y - r * 0.1, r * 0.8, Math.PI, 0);
    ctx.lineTo(x + r * 0.9, y + r * 0.6);
    ctx.lineTo(x - r * 0.9, y + r * 0.6);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.arc(x, y + r * 0.85, r * 0.18, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function drawCountdown(cw, ch, payload) {
    const cx = cw / 2, cy = ch / 2;
    const unit = Math.min(cw, ch) / 2;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = BRAND;
    ctx.font = `700 ${Math.round(unit * 0.07)}px 'Public Sans', sans-serif`;
    ctx.fillText("GLEICH GEHT’S LOS", cx, cy - unit * 0.62);
    ctx.fillStyle = INK;
    ctx.font = `700 ${Math.round(unit * 0.55)}px Magra, sans-serif`;
    ctx.fillText(String(payload.n), cx, cy - unit * 0.06);
    if (payload.task) {
      const size = Math.round(unit * 0.075);
      ctx.font = `600 ${size}px 'Public Sans', sans-serif`;
      ctx.fillStyle = INK_SOFT;
      const lines = wrapLines(ctx, payload.task, Math.min(cw * 0.84, unit * 2.2));
      lines.forEach((line, i) => ctx.fillText(line, cx, cy + unit * 0.48 + i * size * 1.35));
    }
  }

  function drawScene(kind, payload) {
    const cw = canvas.width, ch = canvas.height;
    const cx = cw / 2, cy = ch / 2;
    const unit = Math.min(cw, ch) / 2;
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, cw, ch);

    if (kind === "blank") {
      ctx.fillStyle = NEUTRAL;
      ctx.fillRect(0, 0, cw, ch);
      ctx.beginPath();
      ctx.fillStyle = DOT;
      ctx.arc(cx, cy, unit * 0.03, 0, Math.PI * 2);
      ctx.fill();
    } else if (kind === "count") {
      drawCountdown(cw, ch, payload);
    } else if (kind === "cue") {
      const pts = arrowPoints(payload.angle, cx, cy, unit);
      ctx.beginPath();
      pts.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
      ctx.closePath();
      ctx.fillStyle = payload.color;
      ctx.fill();
      if (payload.caption) barCaption(cw, ch, payload.caption, false);
    } else if (kind === "stroop") {
      ctx.fillStyle = payload.bg;
      ctx.fillRect(0, 0, cw, ch);
      if (payload.instruction) barCaption(cw, ch, payload.instruction, false);
      ctx.fillStyle = payload.ink;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const size = fitText(ctx, payload.word, cw * 0.82, Math.round(unit * 0.62), "Magra, sans-serif", 700);
      ctx.font = `700 ${size}px Magra, sans-serif`;
      ctx.fillText(payload.word, cx, cy);
    } else if (kind === "cross") {
      const p = payload;
      if (p.mode === "audio") {
        ctx.fillStyle = "#e5f1f4";
        ctx.fillRect(0, 0, cw, ch);
        drawSpeakerIcon(cx, cy, unit * 0.32);
      } else {
        const pts = arrowPoints(p.angle, cx, cy, unit);
        ctx.beginPath();
        pts.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
        ctx.closePath();
        ctx.fillStyle = BLUE;
        ctx.fill();
        const iconR = unit * 0.1, iconX = unit * 0.32, iconY = unit * 0.32;
        if (p.sound === "speech") drawSpeakerIcon(iconX, iconY, iconR, true);
        if (p.sound === "beep") drawBellIcon(iconX, iconY, iconR);
      }
    } else if (kind === "vt") {
      ctx.fillStyle = payload.bg;
      ctx.fillRect(0, 0, cw, ch);
      const pts = arrowPoints(payload.angle, cx, cy, unit);
      ctx.beginPath();
      pts.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
      ctx.closePath();
      ctx.fillStyle = "#ffffff";
      ctx.fill();
    } else if (kind === "vrw") {
      const bg = payload.direct ? payload.color : "#ffffff";
      const arrowFill = payload.direct ? "#ffffff" : payload.color;
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, cw, ch);
      const pts = arrowPoints(payload.angle, cx, cy, unit);
      ctx.beginPath();
      pts.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
      ctx.closePath();
      ctx.fillStyle = arrowFill;
      ctx.fill();
    }
  }

  // ---- Exercise catalogue ----
  // title: full name · task: one sentence shown in the countdown and pause
  // preview · trains: what the exercise is good for · rules: explanation on
  // the settings screen.
  const EXERCISES = {
    "vt-color": {
      title: "VT · Farbe & Seite",
      type: "vt",
      usesColors: true,
      task: "Erkenne Farbe und Pfeilrichtung und reagiere mit der passenden Seite.",
      trains: "Farbwahrnehmung und schnelle Seitenentscheidung",
      rules: "Du siehst eine Farbfläche mit weißem Pfeil. Die Farbe sagt dir, was du tust – der Pfeil zeigt die Seite (links oder rechts). Welche Farbe wofür steht, legst du mit deinem Coach fest.",
    },
    "vrw-original": {
      title: "VRW · Direkt & Umgekehrt",
      type: "vrw-real",
      usesColors: true,
      task: "Weißer Pfeil auf Farbe: gezeigte Seite. Farbiger Pfeil auf Weiß: Gegenseite.",
      trains: "Regelwechsel und Impulskontrolle",
      rules: "Weißer Pfeil auf farbiger Fläche: Die gezeigte Seite zählt (direkt). Farbiger Pfeil auf weißer Fläche: Die Gegenseite zählt (umgekehrt).",
      explainerVideo: "explainer-vrw-placeholder.mp4",
    },
    "4-straight": {
      title: "4 Pfeile · gerade", type: "arrows", dirset: 4, dual: false,
      task: "Reagiere so schnell wie möglich in die gezeigte Richtung.",
      trains: "Reaktionsgeschwindigkeit und Richtungserkennung",
      rules: "Ein Pfeil zeigt nach vorne, rechts, hinten oder links. Reagiere so schnell wie möglich in diese Richtung.",
    },
    "4-diag": {
      title: "4 Pfeile · diagonal", type: "arrows", dirset: "diag", dual: false,
      task: "Reagiere so schnell wie möglich in die gezeigte Schrägrichtung.",
      trains: "Reaktionsgeschwindigkeit und Orientierung",
      rules: "Ein Pfeil zeigt in eine der vier Schrägrichtungen. Reagiere so schnell wie möglich in diese Richtung.",
    },
    "8-solo": {
      title: "8 Pfeile", type: "arrows", dirset: 8, dual: false,
      task: "Reagiere so schnell wie möglich in die gezeigte Richtung.",
      trains: "Reaktion in alle Richtungen",
      rules: "Ein Pfeil zeigt in eine von acht Richtungen – gerade oder schräg. Reagiere so schnell wie möglich in diese Richtung.",
    },
    "8-vrw": {
      title: "8 Pfeile · Rot/Grün", type: "arrows", dirset: 8, dual: true,
      task: "Grüner Pfeil: gezeigte Richtung. Roter Pfeil: Gegenrichtung.",
      trains: "Umschalten unter Zeitdruck und Impulskontrolle",
      rules: "Grüner Pfeil: Reagiere in die gezeigte Richtung. Roter Pfeil: Reagiere in die Gegenrichtung.",
    },
    "stroop-classic": {
      title: "Stroop · klassisch", type: "stroop", bg: false,
      task: "Sag laut die Schriftfarbe – nicht das Wort.",
      trains: "Konzentration und Ausblenden von Störreizen",
      rules: "Du siehst ein Farbwort in einer anderen Schriftfarbe. Sag laut die Schriftfarbe – nicht das, was da steht.",
    },
    "stroop-bg": {
      title: "Stroop · mit Hintergrund", type: "stroop", bg: true,
      task: "Sag laut die Schriftfarbe – nicht das Wort, nicht den Hintergrund.",
      trains: "Konzentration bei starker Ablenkung",
      rules: "Wort, Schriftfarbe und Hintergrund sind alle unterschiedlich. Sag laut die Schriftfarbe. Diese Variante ist eine Weiterentwicklung von Fabian Westermann Mentalcoaching.",
    },
    "cross-modal": {
      title: "Sehen & Hören", type: "cross",
      task: "Reagiere auf Bild oder Ton – bei Konflikt gilt die Sonderregel.",
      trains: "Verarbeitung von Sehen und Hören, Regelwechsel",
      rules: "Nur Bild oder nur Ton: Reagiere wie gezeigt oder gesagt. Bild und Ton gleichzeitig mit unterschiedlicher Richtung: Zeigt der Pfeil nach VORNE oder RECHTS, gilt der TON; zeigt er nach HINTEN oder LINKS, gilt das BILD. Bild mit Piepton: Reagiere in die Gegenrichtung des Pfeils. Die Sprachausgabe nutzt die Stimme deines Geräts. Diese Übung ist eine Weiterentwicklung von Fabian Westermann Mentalcoaching.",
    },
  };

  // ---- Programmes: coach-authored multi-block sessions. Real client
  // programmes live in the Cloudflare database (see lookupProgram below),
  // never here - this table only holds anonymous, public example programmes.
  const PROGRAMS = {
    // "featured: true" programmes are shown publicly on the home screen.
    "dig01": {
      name: "Einstieg · Tempo-Steigerung",
      featured: true,
      description: "Zweimal VT: erst ruhig mit viel Zeit, dann doppelt so schnell.",
      pauseS: 15,
      blocks: [
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 2.5, intervalMin: 15, intervalMax: 25, sequence: "S01" },
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 1.25, intervalMin: 7.5, intervalMax: 12.5, sequence: "S01" },
      ],
    },
    "dig02": {
      name: "Fortgeschritten · Gemischtes Training",
      featured: true,
      description: "VT, VRW, Stroop und nochmal VRW – durchgehend zügiges Tempo.",
      pauseS: 15,
      blocks: [
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5, sequence: "S01" },
        { exercise: "vrw-original", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5, sequence: "S01" },
        { exercise: "stroop-classic", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5, sequence: "S01" },
        { exercise: "vrw-original", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5, sequence: "S01" },
      ],
    },
  };

  // ---- Breathing patterns (Atemtraining) ----
  // Every pattern uses the same four-phase model (in / hold / out / hold);
  // a phase set to 0 seconds is skipped. "custom" starts from the client's
  // saved values (see breathPrefs below) so it works as a persistent
  // "rebuild my metronome tempo" slot, while the named presets always reset
  // to their textbook timing when reopened (on-screen tweaks to them are
  // for that session only).
  const BREATH_PATTERNS = {
    coherent: {
      name: "Ruhige Atmung (Kohärenz)",
      short: "Gleichmäßig ein und aus, kein Halten.",
      goal: "Bei diesem Tempo (ca. 5,5 Atemzüge pro Minute) ist die Herzratenvariabilität bei den meisten Menschen am höchsten – gut für Ruhe und Fokus.",
      phases: { in: 5.5, hold1: 0, out: 5.5, hold2: 0 },
    },
    box: {
      name: "Box-Atmung",
      short: "4-4-4-4 – ein- und ausatmen, mit Halten dazwischen.",
      goal: "Bekannt aus dem Einsatztraining (u.a. Navy SEALs) – hilft, unter Druck ruhig und klar zu bleiben.",
      phases: { in: 4, hold1: 4, out: 4, hold2: 4 },
    },
    relax478: {
      name: "4-7-8",
      short: "Kurz einatmen, lange halten, lang ausatmen.",
      goal: "Wirkt stark beruhigend – beliebt zum Runterkommen und vor dem Einschlafen.",
      phases: { in: 4, hold1: 7, out: 8, hold2: 0 },
    },
    custom: {
      name: "Eigenes Muster",
      short: "Stelle jede Phase frei ein.",
      goal: "Baue dir dein bisheriges Metronom-Tempo nach oder finde ein neues Muster für deine Klienten.",
      phases: null,
    },
  };
  const PHASE_LABELS = { in: "Einatmen", hold1: "Halten", out: "Ausatmen", hold2: "Halten" };
  const PHASE_ORDER = ["in", "hold1", "out", "hold2"];

  // ---- Elements ----
  const $ = (id) => document.getElementById(id);
  const els = {
    home: $("home"), ready: $("ready"), player: $("player"), playerBar: $("playerBar"),
    donePanel: $("donePanel"), doneSummary: $("doneSummary"), doneRating: $("doneRating"),
    readyTitle: $("readyTitle"), readyIcon: $("readyIcon"), readyTrains: $("readyTrains"), rulesBox: $("rulesBox"),
    filterMoreBtn: $("filterMoreBtn"), filterExtra: $("filterExtra"),
    startBtn: $("startBtn"), backToHome: $("backToHome"), backBtn: $("backBtn"),
    fsBtn: $("fsBtn"), fsHint: $("fsHint"), fsHintOpenBtn: $("fsHintOpenBtn"), fsHintClose: $("fsHintClose"),
    featuredPrograms: $("featuredPrograms"), featuredGrid: $("featuredGrid"), featuredMoreBtn: $("featuredMoreBtn"),
    liveNav: $("liveNav"), livePrevBtn: $("livePrevBtn"), liveRestartBtn: $("liveRestartBtn"),
    liveEndBtn: $("liveEndBtn"), liveNextBtn: $("liveNextBtn"),
    timeEl: $("timeEl"), progressTrack: $("progressTrack"),
    again: $("againBtn"), doneBack: $("doneBackBtn"),
    durationSlider: $("durationSlider"), durationValue: $("durationValue"),
    stimulusSlider: $("stimulusSlider"), stimulusValue: $("stimulusValue"),
    intervalMinSlider: $("intervalMinSlider"), intervalMaxSlider: $("intervalMaxSlider"), intervalValue: $("intervalValue"),
    tempoCustom: $("tempoCustom"),
    colorGroup: $("colorGroup"), colorPicker: $("colorPicker"), colorCount: $("colorCount"), colorHint: $("colorHint"),
    programCodeInput: $("programCodeInput"), programGoBtn: $("programGoBtn"), programError: $("programError"),
    programIntro: $("programIntro"), programBackToHome: $("programBackToHome"), programTitle: $("programTitle"),
    programMeta: $("programMeta"), programDesc: $("programDesc"), chapterList: $("chapterList"),
    programStartBtn: $("programStartBtn"),
    bundleOverview: $("bundleOverview"), bundleBackToHome: $("bundleBackToHome"), bundleTitle: $("bundleTitle"), bundleList: $("bundleList"),
    pauseScreen: $("pauseScreen"), pauseCountdown: $("pauseCountdown"), pauseToggleBtn: $("pauseToggleBtn"),
    pauseSkipBtn: $("pauseSkipBtn"), pauseAbortBtn: $("pauseAbortBtn"), pauseProgress: $("pauseProgress"),
    breath: $("breath"), breathLabel: $("breathLabel"), nextTitle: $("nextTitle"), nextTask: $("nextTask"), nextCard: $("nextCard"),
    prevChapterBtn: $("prevChapterBtn"), restartChapterBtn: $("restartChapterBtn"), nextChapterBtn: $("nextChapterBtn"),
    programDonePanel: $("programDonePanel"), programDoneSummary: $("programDoneSummary"), programRating: $("programRating"),
    programAgainBtn: $("programAgainBtn"), programDoneBackBtn: $("programDoneBackBtn"),
    introVideo: $("introVideo"), explainerBtn: $("explainerBtn"),
    videoModal: $("videoModal"), videoModalPlayer: $("videoModalPlayer"), videoModalClose: $("videoModalClose"),
    historySection: $("historySection"), historyStats: $("historyStats"), historyList: $("historyList"), historyClearBtn: $("historyClearBtn"),
    tipsSheet: $("tipsSheet"), tipsBtn: $("tipsBtn"), tipsCloseBtn: $("tipsCloseBtn"),
    tipInstall: $("tipInstall"), tipInstallText: $("tipInstallText"),
    breathHome: $("breathHome"), breathReady: $("breathReady"), breathBackToHome: $("breathBackToHome"),
    breathReadyTitle: $("breathReadyTitle"), breathReadyGoal: $("breathReadyGoal"), patternGrid: $("patternGrid"),
    patternBreakdown: $("patternBreakdown"), phaseHelp: $("phaseHelp"),
    phaseInSlider: $("phaseInSlider"), phaseInValue: $("phaseInValue"),
    phaseHold1Slider: $("phaseHold1Slider"), phaseHold1Value: $("phaseHold1Value"),
    phaseOutSlider: $("phaseOutSlider"), phaseOutValue: $("phaseOutValue"),
    phaseHold2Slider: $("phaseHold2Slider"), phaseHold2Value: $("phaseHold2Value"),
    breathDurationSlider: $("breathDurationSlider"), breathDurationValue: $("breathDurationValue"),
    breathStartBtn: $("breathStartBtn"),
    breathPlayer: $("breathPlayer"), breathPlayerBar: $("breathPlayerBar"), breathBig: $("breathBig"),
    breathPhaseCount: $("breathPhaseCount"), breathPhaseLabel: $("breathPhaseLabel"), breathTimeEl: $("breathTimeEl"),
    breathBackBtn: $("breathBackBtn"), breathFsBtn: $("breathFsBtn"), breathFsHint: $("breathFsHint"),
    breathFsHintOpenBtn: $("breathFsHintOpenBtn"), breathFsHintClose: $("breathFsHintClose"),
    breathDonePanel: $("breathDonePanel"), breathDoneSummary: $("breathDoneSummary"), breathRating: $("breathRating"),
    breathAgainBtn: $("breathAgainBtn"), breathDoneBackBtn: $("breathDoneBackBtn"),
    breathHistorySection: $("breathHistorySection"), breathHistoryStats: $("breathHistoryStats"),
    breathHistoryList: $("breathHistoryList"), breathHistoryClearBtn: $("breathHistoryClearBtn"),
    breathTipsSheet: $("breathTipsSheet"), breathTipsBtn: $("breathTipsBtn"), breathTipsCloseBtn: $("breathTipsCloseBtn"),
  };

  const SCREENS = ["home", "breathHome", "bundleOverview", "programIntro", "ready", "breathReady"];
  function showScreen(name) {
    SCREENS.forEach((s) => { els[s].hidden = s !== name; });
    if (name === "home" || name === "breathHome") renderHistory();
    if (name !== "home") els.programError.hidden = true;
    window.scrollTo(0, 0);
  }

  // ---- Section switcher (Visual Training / Atemtraining) ----
  document.querySelectorAll(".section-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sec = btn.dataset.section;
      document.querySelectorAll(".section-tab").forEach((b) => {
        const on = b.dataset.section === sec;
        b.classList.toggle("active", on);
        b.setAttribute("aria-selected", on ? "true" : "false");
      });
      showScreen(sec === "breath" ? "breathHome" : "home");
    });
  });

  // ---- Storage (all local to this device, wrapped for private mode) ----
  function readJSON(key, fallback) {
    try { const raw = localStorage.getItem(key); return raw ? JSON.parse(raw) : fallback; } catch (e) { return fallback; }
  }
  function writeJSON(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
  }

  // ---- Training history ----
  const HISTORY_KEY = "fwmc-history-v1";
  function loadHistory() {
    const h = readJSON(HISTORY_KEY, []);
    return Array.isArray(h) ? h : [];
  }
  function addHistory(entry) {
    const list = loadHistory();
    const item = { id: String(Date.now()), ts: new Date().toISOString(), rating: null, ...entry };
    list.unshift(item);
    writeJSON(HISTORY_KEY, list.slice(0, 200));
    return item.id;
  }
  function rateHistory(id, rating) {
    const list = loadHistory();
    const item = list.find((e) => e.id === id);
    if (item) { item.rating = rating; writeJSON(HISTORY_KEY, list); }
  }
  function isCompleted(progKey) {
    return loadHistory().some((e) => e.kind === "program" && e.progKey === progKey);
  }
  function startOfWeek() {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    return d;
  }
  const WEEKDAYS = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
  function ratingLabel(kind) { return kind === "breath" ? "Ruhe" : "Fokus"; }
  function renderHistoryInto(sectionEl, statsEl, listEl, list) {
    sectionEl.hidden = list.length === 0;
    if (!list.length) return;
    const weekStart = startOfWeek();
    const week = list.filter((e) => new Date(e.ts) >= weekStart);
    const weekSec = week.reduce((s, e) => s + (e.seconds || 0), 0);
    statsEl.innerHTML =
      `<div class="stat"><strong>${week.length}</strong><span>Trainings diese Woche</span></div>` +
      `<div class="stat"><strong>${week.length ? fmtMinutes(weekSec) : "–"}</strong><span>Trainingszeit diese Woche</span></div>` +
      `<div class="stat"><strong>${list.length}</strong><span>Trainings gesamt</span></div>`;
    listEl.innerHTML = list.slice(0, 5).map((e) => {
      const d = new Date(e.ts);
      const date = `${WEEKDAYS[d.getDay()]}, ${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.`;
      const rating = e.rating ? ` · ${ratingLabel(e.kind)} ${e.rating}/5` : "";
      return `<li><span class="h-date">${date}</span><span class="h-title">${esc(e.title)}</span><span class="h-meta">${fmtMinutes(e.seconds || 0)}${rating}</span></li>`;
    }).join("");
  }
  function renderHistory() {
    const list = loadHistory();
    renderHistoryInto(els.historySection, els.historyStats, els.historyList, list);
    renderHistoryInto(els.breathHistorySection, els.breathHistoryStats, els.breathHistoryList, list);
  }
  function clearHistory() {
    if (!confirm("Deinen Trainingsverlauf auf diesem Gerät löschen?")) return;
    writeJSON(HISTORY_KEY, []);
    renderHistory();
  }
  els.historyClearBtn.addEventListener("click", clearHistory);
  els.breathHistoryClearBtn.addEventListener("click", clearHistory);

  // Rating widget shown on the finish screens.
  function renderRating(container, entryId, question) {
    container.innerHTML =
      `<div class="rating-q">${esc(question || "Wie fokussiert warst du?")}</div>` +
      `<div class="rating-row">${[1, 2, 3, 4, 5].map((n) => `<button data-rate="${n}" aria-label="${n} von 5">${n}</button>`).join("")}</div>` +
      `<div class="rating-scale"><span>kaum</span><span>voll da</span></div>` +
      `<div class="rating-thanks" hidden>Danke – gespeichert.</div>`;
    container.querySelectorAll("[data-rate]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const n = Number(btn.dataset.rate);
        rateHistory(entryId, n);
        container.querySelectorAll("[data-rate]").forEach((b) => b.classList.toggle("active", Number(b.dataset.rate) === n));
        container.querySelector(".rating-thanks").hidden = false;
      });
    });
  }

  // ---- Video modal (explainer clips) ----
  function openVideoModal(src) {
    els.videoModalPlayer.src = src;
    els.videoModal.hidden = false;
    els.videoModalPlayer.play().catch(() => {});
  }
  function closeVideoModal() {
    els.videoModalPlayer.pause();
    els.videoModalPlayer.removeAttribute("src");
    els.videoModalPlayer.load();
    els.videoModal.hidden = true;
  }
  els.videoModalClose.addEventListener("click", closeVideoModal);
  els.videoModal.addEventListener("click", (e) => { if (e.target === els.videoModal) closeVideoModal(); });

  // ---- Settings state ----
  const TEMPO_PRESETS = {
    leicht: { stimulusS: 2.5, intervalMin: 6, intervalMax: 10 },
    mittel: { stimulusS: 1.5, intervalMin: 3, intervalMax: 6 },
    schwer: { stimulusS: 0.8, intervalMin: 2, intervalMax: 4 },
  };
  const PREFS_KEY = "fwmc-webapp-v3";
  const DEFAULTS = {
    exercise: null,
    duration: 60,
    stimulusS: 1.5,
    intervalMin: 3,
    intervalMax: 6,
    colors: ["orange", "rot", "lila"],
    sequence: "frei",
  };
  const state = { ...DEFAULTS };
  function loadPrefs() {
    const saved = readJSON(PREFS_KEY, null);
    Object.assign(state, DEFAULTS, saved && typeof saved === "object" ? saved : {});
    if (!Array.isArray(state.colors) || keysToColors(state.colors).length < MIN_COLORS) state.colors = ["orange", "rot", "lila"];
  }
  function savePrefs() { writeJSON(PREFS_KEY, state); }
  loadPrefs();

  // Colours + seed used by the running exercise (set per start).
  let active = { colors: keysToColors(state.colors), seedKey: state.colors.join("-") };

  function randInterval(rng) {
    const lo = Math.min(state.intervalMin, state.intervalMax);
    const hi = Math.max(state.intervalMin, state.intervalMax);
    return lo + rng() * (hi - lo);
  }
  function makeRng() {
    if (state.sequence === "frei") return Math.random;
    const key = [state.exercise, active.seedKey, state.sequence, state.duration, state.stimulusS, state.intervalMin, state.intervalMax].join("|");
    return mulberry32(hashSeed(key));
  }

  // ---- Colour picker ----
  let hintTimer = null;
  function colorHint(text, warn) {
    els.colorHint.textContent = text;
    els.colorHint.classList.toggle("warn", !!warn);
    if (hintTimer) clearTimeout(hintTimer);
    if (warn) hintTimer = setTimeout(() => colorHint(defaultColorHint()), 2200);
  }
  function defaultColorHint() {
    return `Wähle ${MIN_COLORS} bis ${MAX_COLORS} Farben – sie werden zufällig gemischt.`;
  }
  COLOR_LIB.forEach((c) => {
    const btn = document.createElement("button");
    btn.className = "color-swatch";
    btn.dataset.color = c.key;
    btn.setAttribute("aria-pressed", "false");
    btn.innerHTML = `<span class="swatch" style="background:${c.hex}"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="swatch-name">${c.name}</span>`;
    btn.addEventListener("click", () => {
      const selected = state.colors.includes(c.key);
      if (selected) {
        if (state.colors.length <= MIN_COLORS) { colorHint(`Mindestens ${MIN_COLORS} Farben.`, true); return; }
        state.colors = state.colors.filter((k) => k !== c.key);
      } else {
        if (state.colors.length >= MAX_COLORS) { colorHint(`Höchstens ${MAX_COLORS} Farben – wähle zuerst eine ab.`, true); return; }
        state.colors = COLOR_LIB.map((x) => x.key).filter((k) => k === c.key || state.colors.includes(k));
      }
      savePrefs();
      syncColorUI();
    });
    els.colorPicker.appendChild(btn);
  });
  function syncColorUI() {
    els.colorPicker.querySelectorAll(".color-swatch").forEach((el) => {
      const on = state.colors.includes(el.dataset.color);
      el.classList.toggle("active", on);
      el.setAttribute("aria-pressed", on ? "true" : "false");
    });
    els.colorCount.textContent = `${state.colors.length} gewählt`;
    colorHint(defaultColorHint());
  }

  // ---- Sequence / duration / tempo / sliders ----
  document.querySelectorAll("[data-seq]").forEach((el) => {
    el.addEventListener("click", () => { state.sequence = el.dataset.seq; savePrefs(); syncSequenceUI(); });
  });
  function syncSequenceUI() {
    document.querySelectorAll("[data-seq]").forEach((el) => el.classList.toggle("active", el.dataset.seq === state.sequence));
  }

  document.querySelectorAll("[data-dur]").forEach((el) => {
    el.addEventListener("click", () => { state.duration = Number(el.dataset.dur); savePrefs(); syncDurationUI(); });
  });
  function syncDurationUI() {
    document.querySelectorAll("[data-dur]").forEach((el) => el.classList.toggle("active", el.dataset.dur === String(state.duration)));
    els.durationSlider.value = state.duration;
    els.durationValue.textContent = state.duration >= 60 ? fmtMinutes(state.duration) : state.duration + " s";
  }
  els.durationSlider.addEventListener("input", () => { state.duration = Number(els.durationSlider.value); savePrefs(); syncDurationUI(); });

  document.querySelectorAll("[data-tempo]").forEach((el) => {
    el.addEventListener("click", () => { Object.assign(state, TEMPO_PRESETS[el.dataset.tempo]); savePrefs(); syncTempoUI(); });
  });
  function syncTempoUI() {
    let any = false;
    document.querySelectorAll("[data-tempo]").forEach((el) => {
      const p = TEMPO_PRESETS[el.dataset.tempo];
      const on = p.stimulusS === state.stimulusS && p.intervalMin === state.intervalMin && p.intervalMax === state.intervalMax;
      if (on) any = true;
      el.classList.toggle("active", on);
    });
    els.tempoCustom.hidden = any;
    els.stimulusSlider.value = state.stimulusS;
    els.stimulusValue.textContent = fmtSeconds(state.stimulusS);
    els.intervalMinSlider.value = state.intervalMin;
    els.intervalMaxSlider.value = state.intervalMax;
    els.intervalValue.textContent = `${Math.round(state.intervalMin)}–${Math.round(state.intervalMax)} s`;
  }
  els.stimulusSlider.addEventListener("input", () => { state.stimulusS = Number(els.stimulusSlider.value); savePrefs(); syncTempoUI(); });
  els.intervalMinSlider.addEventListener("input", () => {
    state.intervalMin = Math.min(Number(els.intervalMinSlider.value), state.intervalMax); savePrefs(); syncTempoUI();
  });
  els.intervalMaxSlider.addEventListener("input", () => {
    state.intervalMax = Math.max(Number(els.intervalMaxSlider.value), state.intervalMin); savePrefs(); syncTempoUI();
  });

  // ---- Exercise settings screen ----
  document.querySelectorAll(".excard").forEach((card) => {
    card.addEventListener("click", () => openReady(card.dataset.exercise, card.querySelector(".icon-badge,.icon-tile").outerHTML));
  });

  function openReady(id, iconHtml) {
    const ex = EXERCISES[id];
    loadPrefs(); // drop any values a programme run left in `state`
    state.exercise = id;
    savePrefs();
    els.readyTitle.textContent = ex.title;
    els.readyIcon.innerHTML = iconHtml;
    els.readyTrains.textContent = ex.trains ? "Trainiert: " + ex.trains : "";
    els.rulesBox.textContent = ex.rules || "";
    els.rulesBox.hidden = !ex.rules;
    els.explainerBtn.hidden = !ex.explainerVideo;
    els.explainerBtn.onclick = ex.explainerVideo ? () => openVideoModal(ex.explainerVideo) : null;
    els.colorGroup.hidden = !ex.usesColors;
    syncColorUI();
    syncSequenceUI();
    syncDurationUI();
    syncTempoUI();
    showScreen("ready");
  }
  els.backToHome.addEventListener("click", () => showScreen("home"));

  // ---- Exercise filter chips (multi-select "typ", exclusive "ton") ----
  const activeFilters = { ton: null, typ: new Set() };
  function applyFilters() {
    document.querySelectorAll(".excard").forEach((card) => {
      const tags = (card.dataset.tags || "").split(/\s+/).filter(Boolean);
      let visible = true;
      if (activeFilters.ton === "ton" && !tags.includes("ton")) visible = false;
      if (activeFilters.ton === "ohne-ton" && tags.includes("ton")) visible = false;
      if (activeFilters.typ.size > 0 && !tags.some((t) => activeFilters.typ.has(t))) visible = false;
      card.hidden = !visible;
    });
  }
  document.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const group = chip.dataset.filterGroup;
      const value = chip.dataset.filterValue;
      if (group === "ton") {
        const turningOn = activeFilters.ton !== value;
        document.querySelectorAll('.filter-chip[data-filter-group="ton"]').forEach((c) => c.classList.remove("active"));
        activeFilters.ton = turningOn ? value : null;
        if (turningOn) chip.classList.add("active");
      } else if (activeFilters.typ.has(value)) {
        activeFilters.typ.delete(value);
        chip.classList.remove("active");
      } else {
        activeFilters.typ.add(value);
        chip.classList.add("active");
      }
      applyFilters();
    });
  });
  els.filterMoreBtn.addEventListener("click", () => {
    const willShow = els.filterExtra.hidden;
    els.filterExtra.hidden = !willShow;
    els.filterMoreBtn.textContent = willShow ? "Weniger Filter" : "Mehr Filter";
  });

  // ---- Programme lookup + overview screens ----
  let program = null; // { def, chapterIndex, code, key, title, playedS }

  function normCode(s) { return s.trim().toLowerCase().replace(/\s+/g, "-"); }

  const CODE_API = "https://online-training.fwmc.workers.dev/program";

  async function lookupProgram(code) {
    if (PROGRAMS[code]) return PROGRAMS[code];
    try {
      const res = await fetch(`${CODE_API}?code=${encodeURIComponent(code)}`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return null;
  }

  let originBundle = null; // { def, code } - set when a programme was opened from a bundle overview

  async function openProgramIntro(code) {
    els.programGoBtn.disabled = true;
    els.programGoBtn.textContent = "Lädt …";
    const def = await lookupProgram(code);
    els.programGoBtn.disabled = false;
    els.programGoBtn.textContent = "Öffnen";
    if (!def) {
      els.programError.hidden = false;
      showScreen("home");
      return;
    }
    els.programError.hidden = true;
    if (def.type === "bundle") {
      openBundleOverview(def, code);
      return;
    }
    originBundle = null;
    renderProgramIntro(def, code, code);
  }

  function formatDateDE(iso) {
    const parts = (iso || "").split("-");
    if (parts.length !== 3) return "";
    const [y, m, d] = parts;
    return `${d}.${m}.${y}`;
  }

  function openBundleOverview(bundleDef, code) {
    els.bundleTitle.textContent = bundleDef.name || "Deine Programme";
    els.bundleList.innerHTML = "";
    const sorted = bundleDef.programs
      .map((p, i) => ({ p, i }))
      .sort((a, b) => (b.p.createdAt || "").localeCompare(a.p.createdAt || "") || (a.i - b.i));
    sorted.forEach(({ p, i }, pos) => {
      const key = `${code}#${i}`;
      const done = isCompleted(key);
      const isNew = pos === 0 && sorted.length > 1 && p.createdAt;
      const item = document.createElement("button");
      item.className = "bundle-item";
      const dateLabel = formatDateDE(p.createdAt);
      const badges = (isNew ? `<span class="badge badge-new">Neu</span>` : "") + (done ? `<span class="badge badge-done">&#10003; Erledigt</span>` : "");
      item.innerHTML =
        `<div class="bundle-item-head"><strong>${esc(p.label || ("Programm " + (i + 1)))}</strong>${dateLabel ? `<span class="bundle-date">${dateLabel}</span>` : ""}</div>` +
        (badges ? `<div class="badges">${badges}</div>` : "") +
        `<span class="bundle-meta">${exerciseCountLabel(p.blocks.length)} · ca. ${fmtMinutes(programSeconds({ pauseS: bundleDef.pauseS, ...p }))}</span>` +
        (p.description ? `<span class="bundle-desc">${esc(p.description)}</span>` : "");
      item.addEventListener("click", () => {
        originBundle = { def: bundleDef, code };
        renderProgramIntro({ pauseS: bundleDef.pauseS, ...p }, code, key);
      });
      els.bundleList.appendChild(item);
    });
    showScreen("bundleOverview");
  }

  function renderProgramIntro(def, code, key) {
    const title = def.name || def.label || "Dein Programm";
    els.programTitle.textContent = title;
    els.programMeta.textContent = `${exerciseCountLabel(def.blocks.length)} · ca. ${fmtMinutes(programSeconds(def))}`;
    els.programDesc.textContent = def.description || "";
    els.programDesc.hidden = !def.description;
    if (def.introVideo) {
      els.introVideo.src = def.introVideo;
      els.introVideo.hidden = false;
    } else {
      els.introVideo.hidden = true;
      els.introVideo.removeAttribute("src");
    }
    const start = (i) => {
      program = { def, chapterIndex: i, code, key, title, playedS: 0 };
      playChapter(i);
    };
    els.chapterList.innerHTML = "";
    def.blocks.forEach((block, i) => {
      const ex = EXERCISES[block.exercise];
      if (!ex) return;
      const row = document.createElement("div");
      row.className = "chapter-row";
      const main = document.createElement("button");
      main.className = "chapter-main";
      let detail = fmtMinutes(block.duration);
      if (ex.usesColors) {
        const cols = blockColors(block).colors;
        detail += ` · ${colorDots(cols)} ${cols.map((c) => c.name).join(", ")}`;
      }
      main.innerHTML = `<span class="num">${i + 1}</span><span class="info"><strong>${esc(ex.title)}</strong><span>${detail}</span></span>`;
      main.addEventListener("click", () => start(i));
      row.appendChild(main);
      const video = block.video || ex.explainerVideo;
      if (video) {
        const playBtn = document.createElement("button");
        playBtn.className = "play-explainer";
        playBtn.innerHTML = "&#9654; Video";
        playBtn.title = "Erklärvideo ansehen";
        playBtn.addEventListener("click", (e) => { e.stopPropagation(); openVideoModal(video); });
        row.appendChild(playBtn);
      }
      els.chapterList.appendChild(row);
    });
    els.programStartBtn.onclick = () => start(0);
    showScreen("programIntro");
  }

  els.programGoBtn.addEventListener("click", () => {
    const code = normCode(els.programCodeInput.value || "");
    if (code) openProgramIntro(code);
  });
  els.programCodeInput.addEventListener("keydown", (e) => { if (e.key === "Enter") els.programGoBtn.click(); });
  els.programCodeInput.addEventListener("input", () => { els.programError.hidden = true; });
  els.programBackToHome.addEventListener("click", () => {
    if (originBundle) openBundleOverview(originBundle.def, originBundle.code);
    else showScreen("home");
  });
  els.bundleBackToHome.addEventListener("click", () => { originBundle = null; showScreen("home"); });

  // A #code in the link (…/fwmc-Training-app/#abc123) opens that programme
  // directly - no typing needed. Also reacts when only the hash changes.
  function openFromHash() {
    if (!location.hash || location.hash.length < 2) return;
    const tokenCode = normCode(decodeURIComponent(location.hash.slice(1)));
    if (!tokenCode) return;
    els.programCodeInput.value = tokenCode;
    openProgramIntro(tokenCode);
  }
  window.addEventListener("hashchange", openFromHash);

  // ---- Featured programmes: public examples, no code needed ----
  const FEATURED_VISIBLE = 3;
  function renderFeaturedPrograms() {
    const entries = Object.entries(PROGRAMS).filter(([, def]) => def.featured);
    if (entries.length === 0) { els.featuredPrograms.hidden = true; return; }
    els.featuredPrograms.hidden = false;
    els.featuredGrid.innerHTML = "";
    entries.forEach(([code, def], i) => {
      const card = document.createElement("button");
      card.className = "featured-card";
      if (i >= FEATURED_VISIBLE) card.classList.add("hidden-extra");
      card.innerHTML =
        `<span class="fc-title">${esc(def.name)}</span>` +
        `<span class="fc-desc">${esc(def.description || "")}</span>` +
        `<span class="fc-meta">${exerciseCountLabel(def.blocks.length)} · ca. ${fmtMinutes(programSeconds(def))}</span>`;
      card.addEventListener("click", () => openProgramIntro(code));
      els.featuredGrid.appendChild(card);
    });
    els.featuredMoreBtn.hidden = entries.length <= FEATURED_VISIBLE;
    els.featuredMoreBtn.dataset.expanded = "0";
    els.featuredMoreBtn.onclick = () => {
      const expanded = els.featuredMoreBtn.dataset.expanded === "1";
      els.featuredGrid.querySelectorAll(".featured-card").forEach((c, idx) => {
        if (idx >= FEATURED_VISIBLE) c.classList.toggle("hidden-extra", expanded);
      });
      els.featuredMoreBtn.dataset.expanded = expanded ? "0" : "1";
      els.featuredMoreBtn.textContent = expanded ? "Weitere anzeigen" : "Weniger anzeigen";
    };
  }
  renderFeaturedPrograms();

  // ---- Session engine ----
  let raf = null;
  let wakeLock = null;
  let session = null;

  // 3-2-1 lead-in with the exercise's one-line task; returns its length.
  function pushCountdown(schedule, cfg) {
    for (let n = 3; n >= 1; n--) schedule.push({ t0: 3 - n, t1: 4 - n, kind: "count", payload: { n, task: cfg.task } });
    return 3;
  }

  function buildArrowSchedule(cfg, rng) {
    const directions = cfg.dirset === "diag" ? DIR_DIAG : cfg.dirset === 8 ? DIR8 : DIR4;
    const schedule = [];
    let t = pushCountdown(schedule, cfg);
    let last = null;
    const show = state.stimulusS;
    while (t < state.duration) {
      const choices = directions.filter((d) => d[0] !== last);
      const [name, angle] = choices[Math.floor(rng() * choices.length)];
      last = name;
      const color = cfg.dual ? (rng() < 0.5 ? GREEN : RED) : BLUE;
      const caption = cfg.dual ? "GRÜN = gezeigte Richtung · ROT = Gegenrichtung" : null;
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "cue", payload: { angle, color, caption } });
      schedule.push({ t0: t + show, t1: t + show + pause, kind: "blank", payload: {} });
      t += show + pause;
    }
    return { schedule, total: t };
  }

  function pick(arr, excludeIdx, rng) {
    let idx;
    do { idx = Math.floor(rng() * arr.length); } while (excludeIdx.includes(idx));
    return idx;
  }

  function buildStroopSchedule(cfg, rng) {
    const schedule = [];
    let t = pushCountdown(schedule, cfg);
    const instruction = "Sag laut die SCHRIFTFARBE (nicht das Wort)";
    const show = state.stimulusS;
    while (t < state.duration) {
      const wIdx = Math.floor(rng() * STROOP_COLORS.length);
      const inkIdx = pick(STROOP_COLORS, [wIdx], rng);
      let bg = "#ffffff";
      if (cfg.bg) bg = STROOP_COLORS[pick(STROOP_COLORS, [wIdx, inkIdx], rng)].hex;
      const word = STROOP_COLORS[wIdx].name;
      const ink = STROOP_COLORS[inkIdx].hex;
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "stroop", payload: { word, ink, bg, instruction } });
      schedule.push({ t0: t + show, t1: t + show + pause, kind: "blank", payload: {} });
      t += show + pause;
    }
    return { schedule, total: t };
  }

  function buildCrossModalSchedule(cfg, rng) {
    const schedule = [];
    let t = pushCountdown(schedule, cfg);
    const show = state.stimulusS;
    let last = null;
    while (t < state.duration) {
      const roll = rng();
      const choices = DIR4.filter((d) => d[0] !== last);
      let payload;
      if (roll < 0.3) {
        const [name, angle] = choices[Math.floor(rng() * choices.length)];
        last = name;
        payload = { mode: "visual", angle };
      } else if (roll < 0.5) {
        const [name] = choices[Math.floor(rng() * choices.length)];
        last = name;
        payload = { mode: "audio", word: name, sound: "speech" };
      } else if (roll < 0.8) {
        const [vName, vAngle] = choices[Math.floor(rng() * choices.length)];
        last = vName;
        const otherWords = DIR4.filter((d) => d[0] !== vName);
        const [aName] = otherWords[Math.floor(rng() * otherWords.length)];
        payload = { mode: "conflict", angle: vAngle, word: aName, sound: "speech" };
      } else {
        const [vName, vAngle] = choices[Math.floor(rng() * choices.length)];
        last = vName;
        payload = { mode: "invert", angle: vAngle, sound: "beep" };
      }
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "cross", payload });
      schedule.push({ t0: t + show, t1: t + show + pause, kind: "blank", payload: {} });
      t += show + pause;
    }
    return { schedule, total: t };
  }

  function buildVTSchedule(cfg, rng) {
    const colors = active.colors;
    const schedule = [];
    let t = pushCountdown(schedule, cfg);
    const show = state.stimulusS;
    while (t < state.duration) {
      const color = colors[Math.floor(rng() * colors.length)];
      const angle = rng() < 0.5 ? 90 : 270;
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "vt", payload: { angle, bg: color.hex } });
      schedule.push({ t0: t + show, t1: t + show + pause, kind: "blank", payload: {} });
      t += show + pause;
    }
    return { schedule, total: t };
  }

  function buildVRWRealSchedule(cfg, rng) {
    const colors = active.colors;
    const schedule = [];
    let t = pushCountdown(schedule, cfg);
    const show = state.stimulusS;
    while (t < state.duration) {
      const color = colors[Math.floor(rng() * colors.length)];
      const angle = rng() < 0.5 ? 90 : 270;
      const direct = rng() < 0.5;
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "vrw", payload: { angle, color: color.hex, direct } });
      schedule.push({ t0: t + show, t1: t + show + pause, kind: "blank", payload: {} });
      t += show + pause;
    }
    return { schedule, total: t };
  }

  function buildScheduleFor(cfg, rng) {
    return cfg.type === "stroop" ? buildStroopSchedule(cfg, rng) :
      cfg.type === "cross" ? buildCrossModalSchedule(cfg, rng) :
      cfg.type === "vt" ? buildVTSchedule(cfg, rng) :
      cfg.type === "vrw-real" ? buildVRWRealSchedule(cfg, rng) :
      buildArrowSchedule(cfg, rng);
  }

  function onEnterFrame(frame) {
    if (frame.kind !== "cross") return;
    const p = frame.payload;
    if (p.mode === "audio" || p.mode === "conflict") speakWord(p.word);
    else if (p.mode === "invert") playBeep();
  }

  // Segmented progress bar: one segment per exercise of the programme.
  function buildProgressTrack(count) {
    els.progressTrack.innerHTML = Array.from({ length: count }, () => `<span class="seg"><span class="fill"></span></span>`).join("");
  }
  function setProgress(index, fraction) {
    els.progressTrack.querySelectorAll(".seg .fill").forEach((f, i) => {
      f.style.width = (i < index ? 100 : i === index ? Math.min(100, fraction * 100) : 0) + "%";
    });
  }

  function tick(now) {
    if (!session) return;
    const elapsed = (now - session.startTime) / 1000;
    const idx = session.schedule.findIndex((f) => elapsed >= f.t0 && elapsed < f.t1);
    if (idx !== -1) {
      const frame = session.schedule[idx];
      if (idx !== session.lastIndex) {
        session.lastIndex = idx;
        onEnterFrame(frame);
      }
      drawScene(frame.kind, frame.payload);
    } else if (elapsed >= session.total) {
      finishSession();
      return;
    }
    const remaining = fmtClock(session.total - elapsed);
    els.timeEl.textContent = program ? `Übung ${program.chapterIndex + 1}/${program.def.blocks.length} · ${remaining}` : remaining;
    setProgress(program ? program.chapterIndex : 0, elapsed / session.total);
    raf = requestAnimationFrame(tick);
  }

  // Adds the time spent in the current exercise to the programme total.
  function accountSession() {
    if (!session) return 0;
    const spent = Math.min((performance.now() - session.startTime) / 1000, session.total);
    if (program) program.playedS += spent;
    session = null;
    return spent;
  }

  function applyBlockToState(block) {
    state.exercise = block.exercise;
    state.sequence = block.sequence || "frei";
    state.duration = block.duration;
    state.stimulusS = block.stimulusS ?? 1.5;
    state.intervalMin = block.intervalMin ?? 2;
    state.intervalMax = block.intervalMax ?? 4;
    active = blockColors(block);
  }

  async function requestWakeLock() {
    try { if ("wakeLock" in navigator) wakeLock = await navigator.wakeLock.request("screen"); } catch (e) {}
  }

  function hideOverlays() {
    els.donePanel.hidden = true;
    els.programDonePanel.hidden = true;
    els.pauseScreen.hidden = true;
    stopPauseTimers();
  }

  function runSession() {
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.player.hidden = false;
    els.playerBar.hidden = false;
    els.progressTrack.hidden = false;
    fitCanvas();
    ensureAudioCtx();
    const built = buildScheduleFor(EXERCISES[state.exercise], makeRng());
    session = { ...built, startTime: performance.now(), lastIndex: -1 };
    requestWakeLock();
    raf = requestAnimationFrame(tick);
  }

  function playChapter(idx) {
    if (!program) return;
    if (idx < 0) idx = 0;
    if (raf) cancelAnimationFrame(raf);
    accountSession();
    if (window.speechSynthesis) speechSynthesis.cancel();
    hideOverlays();
    if (idx >= program.def.blocks.length) { finishProgram(); return; }
    program.chapterIndex = idx;
    applyBlockToState(program.def.blocks[idx]);
    buildProgressTrack(program.def.blocks.length);
    els.liveNav.hidden = false;
    runSession();
  }

  els.liveRestartBtn.addEventListener("click", () => { if (program) playChapter(program.chapterIndex); });
  els.liveEndBtn.addEventListener("click", () => finishSession());
  els.livePrevBtn.addEventListener("click", () => { if (program) playChapter(program.chapterIndex - 1); });
  els.liveNextBtn.addEventListener("click", () => { if (program) playChapter(program.chapterIndex + 1); });

  // ---- Pause between programme exercises ----
  let pauseTimer = null;
  let breathTimer = null;
  let pauseRemaining = 0;
  let pausePaused = false;

  function stopPauseTimers() {
    if (pauseTimer) clearTimeout(pauseTimer);
    if (breathTimer) clearInterval(breathTimer);
    pauseTimer = breathTimer = null;
    els.breath.classList.remove("run");
  }

  function startPause() {
    const def = program.def;
    const nextBlock = def.blocks[program.chapterIndex + 1];
    if (!nextBlock) { finishProgram(); return; }
    pauseRemaining = nextBlock.pauseS ?? def.pauseS ?? 15;
    pausePaused = false;
    els.pauseToggleBtn.textContent = "Pause verlängern";
    els.pauseProgress.textContent = `Übung ${program.chapterIndex + 1} von ${def.blocks.length} geschafft`;
    const ex = EXERCISES[nextBlock.exercise];
    els.nextTitle.textContent = ex.title;
    els.nextTask.textContent = ex.task || "";
    els.pauseScreen.hidden = false;
    els.playerBar.hidden = true;
    els.liveNav.hidden = true;
    setProgress(program.chapterIndex + 1, 0);
    // Breathing guide: 4 s in, 4 s out, synced with the CSS animation.
    let inhale = true;
    els.breathLabel.textContent = "Einatmen";
    els.breath.classList.remove("run");
    void els.breath.offsetWidth;
    els.breath.classList.add("run");
    breathTimer = setInterval(() => {
      inhale = !inhale;
      els.breathLabel.textContent = inhale ? "Einatmen" : "Ausatmen";
    }, 4000);
    tickPause();
  }
  function tickPause() {
    if (pauseTimer) clearTimeout(pauseTimer);
    els.pauseCountdown.textContent = Math.max(0, Math.ceil(pauseRemaining));
    if (pausePaused) return;
    if (pauseRemaining <= 0) {
      playChapter(program.chapterIndex + 1);
      return;
    }
    pauseTimer = setTimeout(() => { pauseRemaining -= 1; tickPause(); }, 1000);
  }
  els.pauseToggleBtn.addEventListener("click", () => {
    pausePaused = !pausePaused;
    els.pauseToggleBtn.textContent = pausePaused ? "Countdown fortsetzen" : "Pause verlängern";
    if (!pausePaused) tickPause();
  });
  els.pauseSkipBtn.addEventListener("click", () => playChapter(program.chapterIndex + 1));
  els.prevChapterBtn.addEventListener("click", () => playChapter(program.chapterIndex - 1));
  els.restartChapterBtn.addEventListener("click", () => playChapter(program.chapterIndex));
  els.nextChapterBtn.addEventListener("click", () => playChapter(program.chapterIndex + 1));
  els.pauseAbortBtn.addEventListener("click", () => abortTraining());

  function releaseWakeLock() {
    if (wakeLock) { wakeLock.release().catch(() => {}); wakeLock = null; }
  }

  function finishProgram() {
    if (raf) cancelAnimationFrame(raf);
    accountSession();
    releaseWakeLock();
    stopPauseTimers();
    els.pauseScreen.hidden = true;
    els.liveNav.hidden = true;
    els.playerBar.hidden = true;
    setProgress(program.def.blocks.length, 0);
    const played = program.playedS;
    els.programDoneSummary.textContent = `${exerciseCountLabel(program.def.blocks.length)} · ${fmtMinutes(played)} Training`;
    const id = addHistory({ kind: "program", title: program.title, progKey: program.key, seconds: Math.round(played) });
    renderRating(els.programRating, id);
    els.programDoneBackBtn.textContent = originBundle ? "Zurück zu meinen Programmen" : "Zur Startseite";
    els.programDonePanel.hidden = false;
  }
  els.programAgainBtn.addEventListener("click", () => {
    if (!program) return;
    program.playedS = 0;
    playChapter(0);
  });
  els.programDoneBackBtn.addEventListener("click", () => {
    leavePlayer();
    if (originBundle) openBundleOverview(originBundle.def, originBundle.code);
    else showScreen("home");
  });

  // ---- Single exercise ----
  function startSession() {
    program = null;
    hideOverlays();
    active = { colors: keysToColors(state.colors), seedKey: state.colors.join("-") };
    buildProgressTrack(1);
    els.liveNav.hidden = true;
    runSession();
  }

  function finishSession() {
    if (raf) cancelAnimationFrame(raf);
    const spent = accountSession();
    if (window.speechSynthesis) speechSynthesis.cancel();
    els.liveNav.hidden = true;
    if (program) { startPause(); return; }
    releaseWakeLock();
    setProgress(1, 0);
    const ex = EXERCISES[state.exercise];
    els.doneSummary.textContent = `${ex.title} · ${fmtMinutes(spent)}`;
    const id = addHistory({ kind: "exercise", title: ex.title, seconds: Math.round(spent) });
    renderRating(els.doneRating, id);
    els.donePanel.hidden = false;
    els.playerBar.hidden = true;
  }

  function leavePlayer() {
    if (raf) cancelAnimationFrame(raf);
    session = null;
    program = null;
    stopPauseTimers();
    releaseWakeLock();
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    els.fsHint.hidden = true;
    els.liveNav.hidden = true;
    if (window.speechSynthesis) speechSynthesis.cancel();
    els.player.hidden = true;
    hideOverlays();
  }
  function stopToHome() {
    leavePlayer();
    originBundle = null;
    showScreen("home");
  }
  // "Beenden" mid-training: back to where the training was started from.
  function abortTraining() {
    const wasProgram = !!program;
    leavePlayer();
    if (wasProgram) showScreen("programIntro");
    else openReady(state.exercise, els.readyIcon.innerHTML);
  }

  els.startBtn.addEventListener("click", startSession);
  els.backBtn.addEventListener("click", abortTraining);
  els.doneBack.addEventListener("click", stopToHome);
  els.again.addEventListener("click", startSession);

  // ---- Fullscreen (shared by the visual player and the breath player) ----
  function wireFullscreen(cfg) {
    function updateLabel() {
      cfg.btn.textContent = document.fullscreenElement === cfg.player ? "Vollbild aus" : "Vollbild";
    }
    document.addEventListener("fullscreenchange", updateLabel);
    cfg.btn.addEventListener("click", () => {
      if (document.fullscreenElement === cfg.player) { document.exitFullscreen().catch(() => {}); return; }
      if (document.fullscreenEnabled && cfg.player.requestFullscreen) {
        cfg.player.requestFullscreen().catch(() => { cfg.hint.hidden = false; });
      } else {
        cfg.hint.hidden = false;
      }
    });
    cfg.hintOpen.addEventListener("click", () => window.open(location.href, "_blank"));
    cfg.hintClose.addEventListener("click", () => { cfg.hint.hidden = true; });
  }
  wireFullscreen({ player: els.player, btn: els.fsBtn, hint: els.fsHint, hintOpen: els.fsHintOpenBtn, hintClose: els.fsHintClose });
  wireFullscreen({ player: els.breathPlayer, btn: els.breathFsBtn, hint: els.breathFsHint, hintOpen: els.breathFsHintOpenBtn, hintClose: els.breathFsHintClose });
  window.addEventListener("resize", () => { if (!els.player.hidden) fitCanvas(); });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && (session || breathSession) && wakeLock === null) requestWakeLock();
  });

  // ---- Tips sheet (shown once on first visit, reopenable) ----
  const TIPS_KEY = "fwmc-tips-seen";
  const standalone = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  if (standalone) els.tipInstall.hidden = true;
  else if (isIOS) els.tipInstallText.textContent = "Tippe in Safari auf „Teilen“ und dann auf „Zum Home-Bildschirm“ – dann startest du dein Training mit einem Tipp.";
  function openTips() { els.tipsSheet.hidden = false; }
  function closeTips() { els.tipsSheet.hidden = true; writeJSON(TIPS_KEY, true); }
  els.tipsBtn.addEventListener("click", openTips);
  els.tipsCloseBtn.addEventListener("click", closeTips);
  els.tipsSheet.addEventListener("click", (e) => { if (e.target === els.tipsSheet) closeTips(); });
  function openBreathTips() { els.breathTipsSheet.hidden = false; }
  function closeBreathTips() { els.breathTipsSheet.hidden = true; }
  els.breathTipsBtn.addEventListener("click", openBreathTips);
  els.breathTipsCloseBtn.addEventListener("click", closeBreathTips);
  els.breathTipsSheet.addEventListener("click", (e) => { if (e.target === els.breathTipsSheet) closeBreathTips(); });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!els.tipsSheet.hidden) closeTips();
    if (!els.breathTipsSheet.hidden) closeBreathTips();
    if (!els.videoModal.hidden) closeVideoModal();
  });

  // ==== Atemtraining (breathing) ====
  // Client-adjustable phase pacer, built to replace a hand-set metronome:
  // every pattern is the same four-phase model (in/hold/out/hold, seconds),
  // rendered as a circle that grows on the in-breath and shrinks on the
  // out-breath, with an optional spoken phase cue.
  const BREATH_PREFS_KEY = "fwmc-breath-v1";
  const breathPrefs = { durationMin: 5, sound: true, custom: { in: 4, hold1: 0, out: 6, hold2: 0 } };
  function loadBreathPrefs() {
    const saved = readJSON(BREATH_PREFS_KEY, null);
    if (saved && typeof saved === "object") {
      Object.assign(breathPrefs, saved);
      breathPrefs.custom = Object.assign({ in: 4, hold1: 0, out: 6, hold2: 0 }, saved.custom || {});
    }
  }
  function saveBreathPrefs() { writeJSON(BREATH_PREFS_KEY, breathPrefs); }
  loadBreathPrefs();

  function renderPatternGrid() {
    els.patternGrid.innerHTML = "";
    Object.entries(BREATH_PATTERNS).forEach(([key, p]) => {
      const card = document.createElement("button");
      card.className = "featured-card";
      card.innerHTML = `<span class="fc-title">${esc(p.name)}</span><span class="fc-desc">${esc(p.short)}</span>`;
      card.addEventListener("click", () => openBreathReady(key));
      els.patternGrid.appendChild(card);
    });
  }
  renderPatternGrid();

  let breathPatternKey = null;
  let breathWorking = null; // { in, hold1, out, hold2 } - the phase seconds used for the next start

  function phaseChipsHtml(phases) {
    return PHASE_ORDER.filter((k) => phases[k] > 0)
      .map((k) => `<span class="phase-chip">${fmtSeconds(phases[k]).replace(" ", "")} ${PHASE_LABELS[k]}</span>`)
      .join("");
  }
  function syncPhaseUI() {
    const total = PHASE_ORDER.reduce((s, k) => s + breathWorking[k], 0);
    els.phaseInSlider.value = breathWorking.in; els.phaseInValue.textContent = fmtSeconds(breathWorking.in);
    els.phaseHold1Slider.value = breathWorking.hold1; els.phaseHold1Value.textContent = fmtSeconds(breathWorking.hold1);
    els.phaseOutSlider.value = breathWorking.out; els.phaseOutValue.textContent = fmtSeconds(breathWorking.out);
    els.phaseHold2Slider.value = breathWorking.hold2; els.phaseHold2Value.textContent = fmtSeconds(breathWorking.hold2);
    els.patternBreakdown.innerHTML = phaseChipsHtml(breathWorking);
    els.phaseHelp.hidden = total > 0;
    els.breathStartBtn.disabled = total <= 0;
  }
  function onPhaseSliderInput(key, slider) {
    breathWorking[key] = Number(slider.value);
    if (breathPatternKey === "custom") { breathPrefs.custom[key] = breathWorking[key]; saveBreathPrefs(); }
    syncPhaseUI();
  }
  els.phaseInSlider.addEventListener("input", () => onPhaseSliderInput("in", els.phaseInSlider));
  els.phaseHold1Slider.addEventListener("input", () => onPhaseSliderInput("hold1", els.phaseHold1Slider));
  els.phaseOutSlider.addEventListener("input", () => onPhaseSliderInput("out", els.phaseOutSlider));
  els.phaseHold2Slider.addEventListener("input", () => onPhaseSliderInput("hold2", els.phaseHold2Slider));

  document.querySelectorAll("[data-breath-dur]").forEach((el) => {
    el.addEventListener("click", () => { breathPrefs.durationMin = Number(el.dataset.breathDur); saveBreathPrefs(); syncBreathDurationUI(); });
  });
  function syncBreathDurationUI() {
    document.querySelectorAll("[data-breath-dur]").forEach((el) => el.classList.toggle("active", Number(el.dataset.breathDur) === breathPrefs.durationMin));
    els.breathDurationSlider.value = breathPrefs.durationMin;
    els.breathDurationValue.textContent = `${breathPrefs.durationMin} Min`;
  }
  els.breathDurationSlider.addEventListener("input", () => {
    breathPrefs.durationMin = Number(els.breathDurationSlider.value); saveBreathPrefs(); syncBreathDurationUI();
  });

  document.querySelectorAll("[data-breath-sound]").forEach((el) => {
    el.addEventListener("click", () => { breathPrefs.sound = el.dataset.breathSound === "on"; saveBreathPrefs(); syncBreathSoundUI(); });
  });
  function syncBreathSoundUI() {
    document.querySelectorAll("[data-breath-sound]").forEach((el) => {
      el.classList.toggle("active", (el.dataset.breathSound === "on") === breathPrefs.sound);
    });
  }

  function openBreathReady(key) {
    breathPatternKey = key;
    const pattern = BREATH_PATTERNS[key];
    breathWorking = key === "custom" ? { ...breathPrefs.custom } : { ...pattern.phases };
    els.breathReadyTitle.textContent = pattern.name;
    els.breathReadyGoal.textContent = pattern.goal;
    syncPhaseUI();
    syncBreathDurationUI();
    syncBreathSoundUI();
    showScreen("breathReady");
  }
  els.breathBackToHome.addEventListener("click", () => showScreen("breathHome"));

  // ---- Breathing session engine ----
  let breathRaf = null;
  let breathSession = null; // { schedule, cycleLen, plannedTotal, startTime, lastKey, sound }
  let breathPatternName = "";
  const breathCircle = els.breathBig.querySelector(".breath-circle");

  function buildBreathCycle(phases) {
    const schedule = [];
    let t = 0;
    PHASE_ORDER.forEach((k) => {
      if (phases[k] > 0) { schedule.push({ key: k, label: PHASE_LABELS[k], t0: t, t1: t + phases[k] }); t += phases[k]; }
    });
    return { schedule, cycleLen: t };
  }
  function easeInOut(x) { return x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2; }

  function breathTick(now) {
    if (!breathSession) return;
    const elapsed = Math.min((now - breathSession.startTime) / 1000, breathSession.plannedTotal);
    const inCycle = elapsed % breathSession.cycleLen;
    const cycleNum = Math.floor(elapsed / breathSession.cycleLen);
    const frame = breathSession.schedule.find((f) => inCycle >= f.t0 && inCycle < f.t1) || breathSession.schedule[breathSession.schedule.length - 1];
    const frameKey = cycleNum + ":" + frame.key;
    if (frameKey !== breathSession.lastKey) {
      breathSession.lastKey = frameKey;
      if (breathSession.sound) speakWord(frame.label);
    }
    const progress = easeInOut((inCycle - frame.t0) / (frame.t1 - frame.t0 || 1));
    let scale;
    if (frame.key === "in") scale = 0.55 + 0.45 * progress;
    else if (frame.key === "out") scale = 1 - 0.45 * progress;
    else if (frame.key === "hold1") scale = 1;
    else scale = 0.55;
    breathCircle.style.transform = `scale(${scale.toFixed(3)})`;
    els.breathPhaseLabel.textContent = frame.label;
    els.breathPhaseCount.textContent = Math.max(1, Math.ceil(frame.t1 - inCycle));
    els.breathTimeEl.textContent = fmtClock(breathSession.plannedTotal - elapsed);
    if (elapsed >= breathSession.plannedTotal) { breathFinishSession(); return; }
    breathRaf = requestAnimationFrame(breathTick);
  }

  function startBreathSession() {
    const built = buildBreathCycle(breathWorking);
    if (built.cycleLen <= 0) return;
    breathPatternName = BREATH_PATTERNS[breathPatternKey].name;
    const cycles = Math.max(1, Math.round((breathPrefs.durationMin * 60) / built.cycleLen));
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.breathPlayer.hidden = false;
    els.breathPlayerBar.hidden = false;
    els.breathDonePanel.hidden = true;
    breathSession = { schedule: built.schedule, cycleLen: built.cycleLen, plannedTotal: cycles * built.cycleLen, startTime: performance.now(), lastKey: null, sound: breathPrefs.sound };
    requestWakeLock();
    breathRaf = requestAnimationFrame(breathTick);
  }
  els.breathStartBtn.addEventListener("click", startBreathSession);

  function breathLeavePlayer() {
    if (breathRaf) cancelAnimationFrame(breathRaf);
    breathRaf = null;
    breathSession = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.breathPlayer) document.exitFullscreen().catch(() => {});
    els.breathFsHint.hidden = true;
    if (window.speechSynthesis) speechSynthesis.cancel();
    els.breathPlayer.hidden = true;
    els.breathDonePanel.hidden = true;
  }
  function breathFinishSession() {
    if (breathRaf) cancelAnimationFrame(breathRaf);
    breathRaf = null;
    const played = breathSession ? breathSession.plannedTotal : 0;
    breathSession = null;
    releaseWakeLock();
    if (window.speechSynthesis) speechSynthesis.cancel();
    els.breathPlayerBar.hidden = true;
    els.breathDoneSummary.textContent = `${breathPatternName} · ${fmtMinutes(played)}`;
    const id = addHistory({ kind: "breath", title: breathPatternName, seconds: Math.round(played) });
    renderRating(els.breathRating, id, "Wie ruhig fühlst du dich gerade?");
    els.breathDonePanel.hidden = false;
  }
  els.breathBackBtn.addEventListener("click", () => { breathLeavePlayer(); showScreen("breathReady"); });
  els.breathAgainBtn.addEventListener("click", () => { breathLeavePlayer(); startBreathSession(); });
  els.breathDoneBackBtn.addEventListener("click", () => { breathLeavePlayer(); showScreen("breathHome"); });

  // ---- Start-up ----
  renderHistory();
  openFromHash();
  if (!readJSON(TIPS_KEY, false)) openTips();

  // PWA: only meaningful on real hosting - service workers do not run
  // inside the Artifacts preview sandbox, so registration there is a
  // silent, expected no-op.
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  }
})();
