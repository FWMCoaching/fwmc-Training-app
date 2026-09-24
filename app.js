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

  // Fixed four-colour set for "Hütchen antippen" (cone order sorting) -
  // this exercise is always about four cones, so it skips the free colour
  // picker and always uses this base set, only their on-screen order changes.
  const CONE_TAP_COLORS = ["rot", "gelb", "gruen", "blau"].map((k) => COLOR_BY_KEY[k]);

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
      if (list.length >= MIN_COLORS) return { colors: list };
    }
    const id = PALETTES[block.palette] ? block.palette : "ORL";
    return { colors: PALETTES[id] };
  }
  function keysToColors(keys) {
    return COLOR_LIB.filter((c) => keys.includes(c.key));
  }

  // ---- Small helpers ----
  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  }
  // Pairs the visual ".active" state every choice/toggle button uses with
  // aria-pressed, so a screen reader can tell which option is selected.
  function setActive(el, on) {
    el.classList.toggle("active", on);
    el.setAttribute("aria-pressed", on ? "true" : "false");
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

  // ---- Named local presets: "save the current settings under a name, see
  // them in a list, tap to reuse" - the same idea as the combo builder's
  // saved list, reused for a single domain's own settings (Visual Training,
  // Atemtraining, Movement). A "store" just wraps one localStorage array;
  // renderPresetList renders it as a tappable list with a delete button per
  // entry; wirePresetSaveForm wires the "Speichern" link + its inline name
  // form shared by all three domains' ready screens.
  function makePresetStore(key) {
    function load() { const l = readJSON(key, []); return Array.isArray(l) ? l : []; }
    function save(list) { writeJSON(key, list); }
    return { load, save };
  }
  function renderPresetList(store, listEl, groupEl, filterFn, metaFn, onStart) {
    const all = store.load();
    const entries = filterFn ? all.filter(filterFn) : all;
    groupEl.hidden = entries.length === 0;
    listEl.innerHTML = "";
    entries.slice().reverse().forEach((entry) => {
      const wrap = document.createElement("div");
      wrap.className = "bundle-item-wrap";
      const btn = document.createElement("button");
      btn.className = "bundle-item";
      btn.innerHTML = `<div class="bundle-item-head"><strong>${esc(entry.name)}</strong></div><span class="bundle-meta">${esc(metaFn(entry))}</span>`;
      btn.addEventListener("click", () => onStart(entry));
      const rm = document.createElement("button");
      rm.className = "combo-block-remove";
      rm.title = "Löschen";
      rm.textContent = "✕";
      rm.addEventListener("click", () => {
        store.save(store.load().filter((e) => e.id !== entry.id));
        renderPresetList(store, listEl, groupEl, filterFn, metaFn, onStart);
      });
      wrap.appendChild(btn);
      wrap.appendChild(rm);
      listEl.appendChild(wrap);
    });
  }
  function wirePresetSaveForm(cfg) {
    // cfg: { saveBtn, form, nameInput, cancelBtn, confirmBtn, defaultName, onSave }
    function open() { cfg.form.hidden = false; cfg.saveBtn.hidden = true; cfg.nameInput.value = ""; cfg.nameInput.focus(); }
    function close() { cfg.form.hidden = true; cfg.saveBtn.hidden = false; }
    cfg.saveBtn.addEventListener("click", open);
    cfg.cancelBtn.addEventListener("click", close);
    cfg.confirmBtn.addEventListener("click", () => {
      const name = (cfg.nameInput.value || "").trim() || cfg.defaultName();
      cfg.onSave(name);
      close();
    });
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
    } else if (kind === "color") {
      ctx.fillStyle = payload.color;
      ctx.fillRect(0, 0, cw, ch);
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
    "cone-tap": {
      title: "Hütchen sortieren", type: "color-tap",
      task: "Sortiere deine vier Farbhütchen in dieser Reihenfolge, dann tippe für die nächste Reihenfolge. Wie oft schaffst du das in der eingestellten Zeit?",
      trains: "Schnelligkeit beim Umsortieren unter Zeitdruck",
      rules: "Du siehst vier große Farbpunkte – sie zeigen die Reihenfolge, in der deine vier Farbhütchen von links nach rechts stehen sollen. Sortiere deine Hütchen so schnell wie möglich um und tippe danach irgendwo auf den Bildschirm für die nächste Reihenfolge. Gezählt wird, wie viele Durchgänge du innerhalb der eingestellten Zeit schaffst – nicht, ob du eine bestimmte Anzahl erreichst.",
    },
    "cone-compass": {
      title: "Hütchen · Kompass-Aufbau", type: "color", usesColors: true,
      task: "Reagiere auf die Farbe – passend zu deinem eigenen Richtungs-Aufbau am Boden.",
      trains: "Reaktionsschnelligkeit gezielt in frei gewählte Richtungen",
      rules: "Klebe ein Kreuz oder einen Stern mit vier oder acht Richtungen auf den Boden und stelle deine Farbhütchen in die Richtungen, die du trainieren willst. Mehrere Farben auf derselben Richtung lassen diese Richtung häufiger drankommen. Welche Farbe wohin gehört, legst du komplett selbst fest – die App zeigt immer nur die Farbe.",
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
      description: "Zweimal VT: erst ruhig mit viel Zeit, dann doppelt so schnell. Beispiel-Zuordnung für dieses Demo: Orange = mit der Hand antippen · Rot = mit dem Fuß antippen · Lila = kurz stehen bleiben. Bei deinem Coach kann das anders aussehen.",
      pauseS: 15,
      blocks: [
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 2.5, intervalMin: 15, intervalMax: 25 },
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 1.25, intervalMin: 7.5, intervalMax: 12.5 },
      ],
    },
    "dig02": {
      name: "Fortgeschritten · Gemischtes Training",
      featured: true,
      description: "VT, VRW, Stroop und nochmal VRW – durchgehend zügiges Tempo. Beispiel-Zuordnung für dieses Demo: Orange = mit der Hand antippen · Rot = mit dem Fuß antippen · Lila = kurz stehen bleiben. Bei deinem Coach kann das anders aussehen.",
      pauseS: 15,
      blocks: [
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5 },
        { exercise: "vrw-original", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5 },
        { exercise: "stroop-classic", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5 },
        { exercise: "vrw-original", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5 },
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
      goal: "Dieses Tempo liegt im typischen Bereich der individuellen Resonanzatmung (ca. 4,5–6,5 Atemzüge pro Minute) und kann die Herzratenvariabilität unterstützen. Das optimale Tempo ist individuell – bei Bedarf in den Feineinstellungen anpassen.",
      phases: { in: 5.5, hold1: 0, out: 5.5, hold2: 0 },
    },
    box: {
      name: "Box-Atmung",
      short: "4-4-4-4 – ein- und ausatmen, mit Halten dazwischen.",
      goal: "Bekannt aus dem Einsatztraining (u.a. Navy SEALs) – hilft, unter Druck ruhig und klar zu bleiben.",
      phases: { in: 4, hold1: 4, out: 4, hold2: 4 },
    },
    relax478: {
      // Angelehnter Takt, kein 1:1-Original: das Original arbeitet mit
      // wenigen Runden (anfangs 4, später bis 8) statt einer Gesamtdauer in
      // Minuten, und atmet hörbar durch den Mund aus statt durch die Nase.
      name: "4-7-8 (angelehnter Takt)",
      short: "Kurz einatmen, lange halten, lang ausatmen – ausatmen hier bewusst durch den Mund.",
      goal: "Wird häufig zur Beruhigung und zum Einschlafen eingesetzt; die Wirkung ist individuell. Im Original übt man wenige Runden (4–8) statt einer festen Dauer – hier läuft das Muster wie die anderen über eine frei wählbare Gesamtdauer.",
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

  // Wim-Hof-style power breathing is a different mechanic (fast breathing,
  // then a self-timed breath hold, then a timed recovery hold) and doesn't
  // fit the steady four-phase cycle above, so it gets its own engine and
  // its own settings/info object instead of a BREATH_PATTERNS entry.
  const WIMHOF_INFO = {
    // The asterisk + footnote (see wimhofReady in _body.html and the
    // .footnote-mini styling) flags that "Wim-Hof-Stil" is a placeholder
    // name Fabian still needs to clear legally (trademark/name rights)
    // before this ships to real clients under that label.
    name: "Kraftvolle Atmung (Wim-Hof-Stil)*",
    short: "Schnelle Atemzüge, dann die Luft anhalten.",
  };
  const WIMHOF_DEFAULTS = { breaths: 30, rounds: 3, breathPaceS: 1.7, recoveryHoldS: 15 };

  // ---- Coach-authored breathing programmes (mirrors PROGRAMS below): a
  // sequence of breathing blocks delivered by code, or shown here for free
  // as a public example. Real client breath-programmes live in the same
  // Cloudflare database as the visual ones (see lookupProgram), returned
  // with type "breath-program" (single) or "breath-bundle" (several per
  // code, newest first) instead of the visual "bundle"/plain shape.
  //   Cycle block:  { pattern: "coherent"|"box"|"relax478"|"custom",
  //                   durationMin, phases?: {in,hold1,out,hold2}, sound? }
  //   Wim-Hof block: { pattern: "wimhof", breaths, rounds, breathPaceS,
  //                    recoveryHoldS, sound? }
  const BREATH_PROGRAMS = {
    "atem-reset": {
      type: "breath-program",
      name: "Feierabend-Reset",
      featured: true,
      description: "Erst Box-Atmung zum Ankommen, dann lange ruhige Atmung zum Runterkommen.",
      blocks: [
        { pattern: "box", durationMin: 3 },
        { pattern: "coherent", durationMin: 5 },
      ],
    },
  };
  function blockPatternName(block) {
    return block.pattern === "wimhof" ? WIMHOF_INFO.name : BREATH_PATTERNS[block.pattern].name;
  }
  function blockMetaText(block) {
    if (block.pattern === "wimhof") {
      const r = block.rounds ?? WIMHOF_DEFAULTS.rounds, n = block.breaths ?? WIMHOF_DEFAULTS.breaths;
      return `${r} ${r === 1 ? "Runde" : "Runden"} à ${n} Atemzüge`;
    }
    return fmtMinutes((block.durationMin ?? 5) * 60);
  }
  function breathProgramSeconds(def) {
    return def.blocks.reduce((sum, b) => {
      if (b.pattern === "wimhof") {
        const r = b.rounds ?? WIMHOF_DEFAULTS.rounds, n = b.breaths ?? WIMHOF_DEFAULTS.breaths;
        const pace = b.breathPaceS ?? WIMHOF_DEFAULTS.breathPaceS, rec = b.recoveryHoldS ?? WIMHOF_DEFAULTS.recoveryHoldS;
        return sum + r * (n * pace + 30 + rec); // 30s = rough average retention, for the "ca." estimate only
      }
      return sum + (b.durationMin ?? 5) * 60;
    }, 0);
  }

  // ==== Movement (placeholder name) ====
  // Deliberately designed from scratch, from Fabian's own description only
  // (no reference product was looked at), so the pictogram style, movement
  // set and interaction (a look-ahead "lane" of upcoming moves) are our own.
  // Parked for a later iteration, per Fabian: head-tilt + colour-inversion
  // rule (mirrors the VRW "green=shown/red=opposite" idea onto the body),
  // two-limb combo tiles, and coach-authored programmes/codes like the
  // other two sections already have.
  const MOVEMENTS = [
    { id: "armL-heben", limb: "armL", type: "heben", label: "Linker Arm heben" },
    { id: "armL-strecken", limb: "armL", type: "strecken", label: "Linker Arm strecken" },
    { id: "armR-heben", limb: "armR", type: "heben", label: "Rechter Arm heben" },
    { id: "armR-strecken", limb: "armR", type: "strecken", label: "Rechter Arm strecken" },
    { id: "legL-heben", limb: "legL", type: "heben", label: "Linkes Bein heben" },
    { id: "legL-strecken", limb: "legL", type: "strecken", label: "Linkes Bein strecken" },
    { id: "legR-heben", limb: "legR", type: "heben", label: "Rechtes Bein heben" },
    { id: "legR-strecken", limb: "legR", type: "strecken", label: "Rechtes Bein strecken" },
  ];
  const MOVEMENT_BY_ID = Object.fromEntries(MOVEMENTS.map((m) => [m.id, m]));
  const MIN_MOVEMENTS = 2;

  // An abstract four-spoke pictogram - deliberately NOT a little figure with
  // a head, since the closest known reference (Life Kinetik's "Bocobrain"
  // sheets, seen after this was first designed) already owns that visual
  // territory: a stick body topped with a smiley head, with triangles and
  // squares placed beside it to mark arms/legs. This version has no body
  // outline and no face at all - four short bars radiate from a plain hub,
  // one per limb; the active one turns the highlight colour and swings
  // toward vertical and short ("heben") or toward horizontal and long
  // ("strecken"). `baseColor` lets the same renderer sit on a themed
  // background (settings screen, follows dark mode) or the always-light
  // player stage (fixed dark ink, matching the visual-training canvas).
  const FIG_HIGHLIGHT = "#ff9110";
  const SPOKE_NEUTRAL_DIR = {
    armLeft: [-0.7071, -0.7071], armRight: [0.7071, -0.7071],
    legLeft: [-0.7071, 0.7071], legRight: [0.7071, 0.7071],
  };
  const SPOKE_ACTIVE_DIR = {
    heben: { armLeft: [-0.5, -0.87], armRight: [0.5, -0.87], legLeft: [-0.5, 0.87], legRight: [0.5, 0.87] },
    strecken: { armLeft: [-0.97, -0.26], armRight: [0.97, -0.26], legLeft: [-0.97, 0.26], legRight: [0.97, 0.26] },
  };
  const SPOKE_LEN = { neutral: 15, heben: 30, strecken: 43 };
  const SPOKE_START_R = 8;
  // slots: { armLeft, armRight, legLeft, legRight } - each holds a pose
  // name ("heben"/"strecken") when that screen-side limb is the active one.
  function figureSVG(slots, baseColor) {
    baseColor = baseColor || "#16232a";
    const parts = ["armLeft", "armRight", "legLeft", "legRight"].map((key) => {
      const type = slots[key];
      const dir = type ? SPOKE_ACTIVE_DIR[type][key] : SPOKE_NEUTRAL_DIR[key];
      const len = SPOKE_LEN[type || "neutral"];
      const color = type ? FIG_HIGHLIGHT : baseColor;
      const x1 = (50 + dir[0] * SPOKE_START_R).toFixed(1), y1 = (50 + dir[1] * SPOKE_START_R).toFixed(1);
      const x2 = (50 + dir[0] * len).toFixed(1), y2 = (50 + dir[1] * len).toFixed(1);
      return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="11" stroke-linecap="round"/>`;
    }).join("");
    return `<svg viewBox="0 0 100 100" class="figure-svg" aria-hidden="true">${parts}<circle cx="50" cy="50" r="7" fill="${baseColor}"/></svg>`;
  }
  // Resolves which SCREEN side each anatomical limb is drawn on. Mirrored
  // (default): the client's left appears on-screen left, like copying a
  // reflection. Non-mirrored: the figure faces the client, so its left is
  // on their right - anatomically correct but less intuitive to copy.
  function resolveSlots(moves, mirrored) {
    const slots = {};
    moves.forEach((m) => {
      const side = m.limb.endsWith("L") ? "left" : "right";
      const flip = !mirrored;
      const screenSide = flip ? (side === "left" ? "right" : "left") : side;
      const group = m.limb.startsWith("arm") ? "arm" : "leg";
      slots[group + (screenSide === "left" ? "Left" : "Right")] = m.type;
    });
    return slots;
  }

  // ==== Workout (placeholder name) ====
  // A small demo exercise library - real content (photos, precise coaching
  // notes) is for Fabian to fill in later; the schema carries an optional
  // `image` per exercise for that. Until then, `icon` points at a small
  // abstract pictogram (see WORKOUT_ICONS) as at-least-a-picture stand-in.
  const WORKOUT_EXERCISES = {
    kniebeuge: {
      name: "Kniebeugen", icon: "squat",
      note: "Rücken gerade, Blick nach vorne. Knie zeigen in Richtung der Zehen, Gewicht bleibt auf den Fersen.",
    },
    liegestuetz: {
      name: "Liegestütze", icon: "pushup",
      note: "Körper bildet eine gerade Linie von Kopf bis Ferse. Ellbogen nah am Körper, Arme nicht ganz durchdrücken.",
    },
    ausfallschritt: {
      name: "Ausfallschritte", icon: "lunge",
      note: "Oberkörper aufrecht, großer Schritt nach vorne. Das vordere Knie bleibt hinter der Zehenspitze.",
    },
    plank: {
      name: "Unterarmstütz (Plank)", icon: "plank",
      note: "Bauch und Gesäß anspannen. Hüfte weder durchhängen lassen noch hochziehen, Ellbogen unter den Schultern.",
    },
    hampelmann: {
      name: "Hampelmann", icon: "jumpingjack",
      note: "Locker und im eigenen Tempo, weiche Knie beim Landen.",
    },
    bergsteiger: {
      name: "Bergsteiger", icon: "mountainclimber",
      note: "Rücken flach wie im Unterarmstütz, Knie zügig und kontrolliert zur Brust ziehen.",
    },
  };
  // Small abstract stick-figure pictograms - generic exercise iconography
  // (the same kind of simple figure used everywhere from safety signage to
  // fitness apps), not tied to any specific reference system.
  const WORKOUT_ICONS = {
    squat: `<circle cx="12" cy="4" r="2" fill="#fff"/><path d="M12 6 L12 11" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M12 7 L6 7 M12 7 L18 7" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M12 11 L8 15 L8 19 M12 11 L16 15 L16 19" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
    pushup: `<circle cx="4" cy="10" r="2" fill="#fff"/><path d="M6 11 L18 11 L21 13" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M9 11 L9 17 M15 11 L15 17" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    lunge: `<circle cx="12" cy="4" r="2" fill="#fff"/><path d="M12 6 L12 12" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M12 12 L9 15 L9 19" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 12 L17 15 L20 19" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 8 L8 10 M12 8 L16 6" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    plank: `<circle cx="4" cy="9" r="2" fill="#fff"/><path d="M6 10 L20 14" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M9 10.7 L9 16" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M20 14 L17 18" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    jumpingjack: `<circle cx="12" cy="4" r="2" fill="#fff"/><path d="M12 6 L12 13" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M12 7 L5 2 M12 7 L19 2" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M12 13 L6 20 M12 13 L18 20" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    mountainclimber: `<circle cx="4" cy="9" r="2" fill="#fff"/><path d="M6 10 L18 15 L21 19" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M11 12 L8 13 L6 16" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M9 10.6 L9 16" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    custom: `<circle cx="7" cy="12" r="2.4" fill="none" stroke="#fff" stroke-width="1.8"/><circle cx="17" cy="12" r="2.4" fill="none" stroke="#fff" stroke-width="1.8"/><path d="M9.4 12 L14.6 12" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>`,
  };
  function workoutIconSVG(key) {
    return `<svg viewBox="0 0 24 24">${WORKOUT_ICONS[key] || WORKOUT_ICONS.custom}</svg>`;
  }
  // ---- Custom exercises: the client's own additions, alongside the built-in
  // library above. Stored locally, selectable and reusable just like a
  // built-in exercise (they just get the generic "custom" icon).
  const CUSTOM_WORKOUT_KEY = "fwmc-workout-custom-v1";
  function loadCustomWorkoutExercises() {
    const list = readJSON(CUSTOM_WORKOUT_KEY, []);
    return Array.isArray(list) ? list : [];
  }
  function saveCustomWorkoutExercises(list) { writeJSON(CUSTOM_WORKOUT_KEY, list); }
  let customWorkoutExercises = loadCustomWorkoutExercises();
  function findWorkoutExercise(id) {
    if (WORKOUT_EXERCISES[id]) return WORKOUT_EXERCISES[id];
    const custom = customWorkoutExercises.find((c) => c.id === id);
    return custom || { name: id, note: "", icon: "custom" };
  }
  function allWorkoutExerciseEntries() {
    return [...Object.entries(WORKOUT_EXERCISES), ...customWorkoutExercises.map((c) => [c.id, c])];
  }
  function circuitSummaryLabel(block) {
    return `Zirkel · ${block.items.length} Übung${block.items.length === 1 ? "" : "en"}` + (block.sets > 1 ? ` × ${block.sets} Sätze` : "");
  }
  function workoutBlockLabel(block) {
    if (block.kind === "circuit") return circuitSummaryLabel(block);
    return findWorkoutExercise(block.exercise).name;
  }
  function workoutBlockMeta(block) {
    if (block.kind === "tabata") return `${block.rounds} Runden à ${block.workS}s/${block.restS}s`;
    if (block.kind === "circuit") return `${block.items.length} Übungen × ${block.sets} Sätze`;
    return `${block.sets}×${block.reps}`;
  }
  function workoutBlockSeconds(block) {
    if (block.kind === "tabata") return block.rounds * (block.workS + block.restS);
    if (block.kind === "circuit") return buildCircuitSchedule(block).total;
    return block.sets * 30 + (block.sets - 1) * (block.restS ?? 30); // 30s/set is a rough estimate for the "ca." total
  }
  // ---- Coach-authored / self-built workout plans (mirrors the breath and
  // combo programme tables): a sequence of "reps" or "tabata" blocks,
  // delivered by code or built locally. Real client plans live in the same
  // Cloudflare database, returned as type "workout-plan" (single) or
  // "workout-bundle" (several per code).
  const WORKOUT_PLANS = {
    "workout-start": {
      type: "workout-plan",
      name: "Ganzkörper-Einstieg",
      featured: true,
      description: "Drei Kraftübungen mit festen Wiederholungen, zum Abschluss ein kurzes Intervall.",
      blocks: [
        { kind: "reps", exercise: "kniebeuge", sets: 3, reps: 12, restS: 30 },
        { kind: "reps", exercise: "liegestuetz", sets: 3, reps: 10, restS: 30 },
        { kind: "reps", exercise: "ausfallschritt", sets: 3, reps: 10, restS: 30 },
        { kind: "tabata", exercise: "hampelmann", workS: 20, restS: 10, rounds: 8 },
      ],
    },
  };

  // ==== Cross-section combo programmes ====
  // A combo programme chains blocks from any of the four sections behind
  // one code or one locally-saved plan - each block just says which
  // section's engine should run it (`domain`) plus that engine's own
  // settings. The dispatcher below reuses every section's existing start/
  // finish functions rather than a parallel implementation.
  function comboBlockLabel(block) {
    if (block.domain === "wimhof") return WIMHOF_INFO.name;
    if (block.domain === "breath") return BREATH_PATTERNS[block.pattern].name;
    if (block.domain === "movement") return "Movement · Ganzkörper-Reaktion";
    if (block.domain === "workout") return workoutBlockLabel(block);
    if (block.domain === "visual") return EXERCISES[block.exercise] ? EXERCISES[block.exercise].title : block.exercise;
    return block.domain;
  }
  function comboBlockMeta(block) {
    if (block.domain === "wimhof") return `${block.rounds ?? WIMHOF_DEFAULTS.rounds} Runden`;
    if (block.domain === "breath") return fmtMinutes((block.durationMin ?? 5) * 60);
    if (block.domain === "movement") return fmtMinutes((block.durationMin ?? 2) * 60);
    if (block.domain === "workout") return workoutBlockMeta(block);
    if (block.domain === "visual") return fmtMinutes((block.duration ?? 60));
    return "";
  }
  function comboBlockSeconds(block) {
    if (block.domain === "wimhof") { const r = block.rounds ?? WIMHOF_DEFAULTS.rounds, n = block.breaths ?? WIMHOF_DEFAULTS.breaths; return r * (n * (block.breathPaceS ?? WIMHOF_DEFAULTS.breathPaceS) + 30 + (block.recoveryHoldS ?? WIMHOF_DEFAULTS.recoveryHoldS)); }
    if (block.domain === "breath") return (block.durationMin ?? 5) * 60;
    if (block.domain === "movement") return (block.durationMin ?? 2) * 60;
    if (block.domain === "workout") return workoutBlockSeconds(block);
    if (block.domain === "visual") return block.duration ?? 60;
    return 0;
  }
  // Curated quick-add presets the combo builder offers per section - not the
  // full settings depth of each section's own screen, but enough to build a
  // useful cross-section session without reimplementing every settings UI.
  const COMBO_PRESETS = {
    breath: [
      { domain: "breath", pattern: "box", durationMin: 3 },
      { domain: "breath", pattern: "coherent", durationMin: 5 },
      { domain: "breath", pattern: "relax478", durationMin: 3 },
      { domain: "wimhof", breaths: 30, rounds: 3, breathPaceS: 1.7, recoveryHoldS: 15 },
    ],
    movement: [
      { domain: "movement", durationMin: 2, bpm: 60, preview: 3, mirror: true, showLabel: true },
      { domain: "movement", durationMin: 3, bpm: 80, preview: "all", mirror: true, showLabel: true },
    ],
    visual: [
      { domain: "visual", exercise: "vt-color", duration: 60, colors: ["orange", "rot", "lila"] },
      { domain: "visual", exercise: "vrw-original", duration: 60, colors: ["orange", "rot", "lila"] },
      { domain: "visual", exercise: "stroop-classic", duration: 60 },
    ],
    workout: [
      { domain: "workout", kind: "reps", exercise: "kniebeuge", sets: 3, reps: 12, restS: 30 },
      { domain: "workout", kind: "tabata", exercise: "hampelmann", workS: 20, restS: 10, rounds: 8 },
    ],
  };
  const COMBO_DOMAIN_TITLE = { breath: "Atemtraining", movement: "Movement", visual: "Visual Training", workout: "Workout" };

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
    durationGroup: $("durationGroup"), tempoGroup: $("tempoGroup"), advanced: $("advanced"),
    vtSavedGroup: $("vtSavedGroup"), vtSavedList: $("vtSavedList"), vtSaveBtn: $("vtSaveBtn"),
    vtSaveForm: $("vtSaveForm"), vtSaveNameInput: $("vtSaveNameInput"),
    vtSaveCancelBtn: $("vtSaveCancelBtn"), vtSaveConfirmBtn: $("vtSaveConfirmBtn"),
    stageWrap: $("stageWrap"), coneOrderStage: $("coneOrderStage"), coneOrderRow: $("coneOrderRow"),
    coneOrderCount: $("coneOrderCount"), coneBestHint: $("coneBestHint"),
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
    historyMoreBtn: $("historyMoreBtn"),
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
    breathSavedGroup: $("breathSavedGroup"), breathSavedList: $("breathSavedList"), breathSaveBtn: $("breathSaveBtn"),
    breathSaveForm: $("breathSaveForm"), breathSaveNameInput: $("breathSaveNameInput"),
    breathSaveCancelBtn: $("breathSaveCancelBtn"), breathSaveConfirmBtn: $("breathSaveConfirmBtn"),
    breathPlayer: $("breathPlayer"), breathPlayerBar: $("breathPlayerBar"), breathBig: $("breathBig"),
    breathPhaseCount: $("breathPhaseCount"), breathPhaseLabel: $("breathPhaseLabel"), breathTimeEl: $("breathTimeEl"),
    breathBackBtn: $("breathBackBtn"), breathFsBtn: $("breathFsBtn"), breathFsHint: $("breathFsHint"),
    breathPauseBtn: $("breathPauseBtn"),
    breathFsHintOpenBtn: $("breathFsHintOpenBtn"), breathFsHintClose: $("breathFsHintClose"),
    breathDonePanel: $("breathDonePanel"), breathDoneSummary: $("breathDoneSummary"), breathRating: $("breathRating"),
    breathAgainBtn: $("breathAgainBtn"), breathDoneBackBtn: $("breathDoneBackBtn"),
    breathHistorySection: $("breathHistorySection"), breathHistoryStats: $("breathHistoryStats"),
    breathHistoryList: $("breathHistoryList"), breathHistoryClearBtn: $("breathHistoryClearBtn"), breathHistoryMoreBtn: $("breathHistoryMoreBtn"),
    breathTipsSheet: $("breathTipsSheet"), breathTipsBtn: $("breathTipsBtn"), breathTipsCloseBtn: $("breathTipsCloseBtn"),
    breathFeaturedPrograms: $("breathFeaturedPrograms"), breathFeaturedGrid: $("breathFeaturedGrid"),
    breathProgramCodeInput: $("breathProgramCodeInput"), breathProgramGoBtn: $("breathProgramGoBtn"), breathProgramError: $("breathProgramError"),
    breathBundleOverview: $("breathBundleOverview"), breathBundleBackToHome: $("breathBundleBackToHome"),
    breathBundleTitle: $("breathBundleTitle"), breathBundleList: $("breathBundleList"),
    breathProgramIntro: $("breathProgramIntro"), breathProgramBackToHome: $("breathProgramBackToHome"),
    breathProgramTitle: $("breathProgramTitle"), breathProgramMeta: $("breathProgramMeta"), breathProgramDesc: $("breathProgramDesc"),
    breathChapterList: $("breathChapterList"), breathProgramStartBtn: $("breathProgramStartBtn"),
    breathTransition: $("breathTransition"), breathTransitionTitle: $("breathTransitionTitle"),
    breathTransitionMeta: $("breathTransitionMeta"), breathTransitionBtn: $("breathTransitionBtn"),
    breathProgramDonePanel: $("breathProgramDonePanel"), breathProgramDoneSummary: $("breathProgramDoneSummary"),
    breathProgramRating: $("breathProgramRating"), breathProgramAgainBtn: $("breathProgramAgainBtn"), breathProgramDoneBackBtn: $("breathProgramDoneBackBtn"),
    wimhofReady: $("wimhofReady"), wimhofBackToHome: $("wimhofBackToHome"), wimhofAckCheck: $("wimhofAckCheck"), wimhofStartBtn: $("wimhofStartBtn"),
    wimhofPlayer: $("wimhofPlayer"), wimhofPlayerBar: $("wimhofPlayerBar"), wimhofBig: $("wimhofBig"),
    wimhofPhaseCount: $("wimhofPhaseCount"), wimhofPhaseLabel: $("wimhofPhaseLabel"), wimhofSub: $("wimhofSub"),
    wimhofHoldDoneBtn: $("wimhofHoldDoneBtn"), wimhofStatusEl: $("wimhofStatusEl"),
    wimhofBackBtn: $("wimhofBackBtn"), wimhofFsBtn: $("wimhofFsBtn"), wimhofFsHint: $("wimhofFsHint"),
    wimhofFsHintOpenBtn: $("wimhofFsHintOpenBtn"), wimhofFsHintClose: $("wimhofFsHintClose"),
    wimhofDonePanel: $("wimhofDonePanel"), wimhofDoneSummary: $("wimhofDoneSummary"), wimhofRating: $("wimhofRating"),
    wimhofAgainBtn: $("wimhofAgainBtn"), wimhofDoneBackBtn: $("wimhofDoneBackBtn"),
    movementHome: $("movementHome"), movementHistorySection: $("movementHistorySection"),
    movementHistoryStats: $("movementHistoryStats"), movementHistoryList: $("movementHistoryList"),
    movementHistoryClearBtn: $("movementHistoryClearBtn"), movementHistoryMoreBtn: $("movementHistoryMoreBtn"), movementStartCard: $("movementStartCard"),
    movementTipsBtn: $("movementTipsBtn"), movementTipsSheet: $("movementTipsSheet"), movementTipsCloseBtn: $("movementTipsCloseBtn"),
    movementReady: $("movementReady"), movementBackToHome: $("movementBackToHome"),
    movementPicker: $("movementPicker"), movementCount: $("movementCount"),
    movementStartBtn: $("movementStartBtn"),
    movementSavedGroup: $("movementSavedGroup"), movementSavedList: $("movementSavedList"), movementSaveBtn: $("movementSaveBtn"),
    movementSaveForm: $("movementSaveForm"), movementSaveNameInput: $("movementSaveNameInput"),
    movementSaveCancelBtn: $("movementSaveCancelBtn"), movementSaveConfirmBtn: $("movementSaveConfirmBtn"),
    movementPlayer: $("movementPlayer"), movementLane: $("movementLane"), movementProgressTrack: $("movementProgressTrack"),
    movementFinishBadge: $("movementFinishBadge"), movementBpmSlider: $("movementBpmSlider"), movementBpmValue: $("movementBpmValue"),
    movementPlayerBar: $("movementPlayerBar"), movementBackBtn: $("movementBackBtn"), movementTimeEl: $("movementTimeEl"),
    movementFsBtn: $("movementFsBtn"), movementFsHint: $("movementFsHint"),
    movementFsHintOpenBtn: $("movementFsHintOpenBtn"), movementFsHintClose: $("movementFsHintClose"),
    movementDonePanel: $("movementDonePanel"), movementDoneSummary: $("movementDoneSummary"), movementRating: $("movementRating"),
    movementAgainBtn: $("movementAgainBtn"), movementDoneBackBtn: $("movementDoneBackBtn"),

    workoutHome: $("workoutHome"), workoutProgramCodeInput: $("workoutProgramCodeInput"), workoutProgramGoBtn: $("workoutProgramGoBtn"),
    workoutProgramError: $("workoutProgramError"), workoutHistorySection: $("workoutHistorySection"),
    workoutHistoryStats: $("workoutHistoryStats"), workoutHistoryList: $("workoutHistoryList"), workoutHistoryClearBtn: $("workoutHistoryClearBtn"), workoutHistoryMoreBtn: $("workoutHistoryMoreBtn"),
    workoutFeaturedPrograms: $("workoutFeaturedPrograms"), workoutFeaturedGrid: $("workoutFeaturedGrid"),
    workoutTabataStartCard: $("workoutTabataStartCard"),
    workoutBundleOverview: $("workoutBundleOverview"), workoutBundleBackToHome: $("workoutBundleBackToHome"),
    workoutBundleTitle: $("workoutBundleTitle"), workoutBundleList: $("workoutBundleList"),
    workoutProgramIntro: $("workoutProgramIntro"), workoutProgramBackToHome: $("workoutProgramBackToHome"),
    workoutProgramTitle: $("workoutProgramTitle"), workoutProgramMeta: $("workoutProgramMeta"), workoutProgramDesc: $("workoutProgramDesc"),
    workoutChapterList: $("workoutChapterList"), workoutProgramStartBtn: $("workoutProgramStartBtn"),
    workoutTabataReady: $("workoutTabataReady"), workoutTabataBackToHome: $("workoutTabataBackToHome"),
    workoutTabataStartBtn: $("workoutTabataStartBtn"),
    workoutCircuitSavedGroup: $("workoutCircuitSavedGroup"), workoutCircuitSavedList: $("workoutCircuitSavedList"),
    workoutCircuitSaveBtn: $("workoutCircuitSaveBtn"), workoutCircuitSaveForm: $("workoutCircuitSaveForm"),
    workoutCircuitSaveNameInput: $("workoutCircuitSaveNameInput"),
    workoutCircuitSaveCancelBtn: $("workoutCircuitSaveCancelBtn"), workoutCircuitSaveConfirmBtn: $("workoutCircuitSaveConfirmBtn"),
    workoutCircuitAddGrid: $("workoutCircuitAddGrid"), workoutCircuitCount: $("workoutCircuitCount"),
    workoutCircuitEmptyHint: $("workoutCircuitEmptyHint"), workoutCircuitList: $("workoutCircuitList"),
    workoutCircuitSetRestGroup: $("workoutCircuitSetRestGroup"),
    workoutCircuitDefaultWorkSlider: $("workoutCircuitDefaultWorkSlider"), workoutCircuitDefaultWorkValue: $("workoutCircuitDefaultWorkValue"),
    workoutCircuitAddCustomBtn: $("workoutCircuitAddCustomBtn"), workoutCircuitCustomForm: $("workoutCircuitCustomForm"),
    workoutCircuitCustomName: $("workoutCircuitCustomName"), workoutCircuitCustomNote: $("workoutCircuitCustomNote"),
    workoutCircuitCustomCancelBtn: $("workoutCircuitCustomCancelBtn"), workoutCircuitCustomSaveBtn: $("workoutCircuitCustomSaveBtn"),
    workoutPlayer: $("workoutPlayer"), workoutRepsView: $("workoutRepsView"), workoutExerciseName: $("workoutExerciseName"),
    workoutSetInfo: $("workoutSetInfo"), workoutRepsBig: $("workoutRepsBig"), workoutNote: $("workoutNote"),
    workoutSetDoneBtn: $("workoutSetDoneBtn"), workoutRestBox: $("workoutRestBox"), workoutRestCountdown: $("workoutRestCountdown"),
    workoutRestSkipBtn: $("workoutRestSkipBtn"), workoutTabataView: $("workoutTabataView"), tabataPhaseLabel: $("tabataPhaseLabel"),
    tabataCountdown: $("tabataCountdown"), tabataExerciseName: $("tabataExerciseName"), tabataRoundLabel: $("tabataRoundLabel"),
    tabataExerciseIcon: $("tabataExerciseIcon"), tabataExerciseNote: $("tabataExerciseNote"),
    tabataPrevBtn: $("tabataPrevBtn"), tabataRestartBtn: $("tabataRestartBtn"), tabataSkipBtn: $("tabataSkipBtn"),
    workoutOverview: $("workoutOverview"), workoutProgressTrack: $("workoutProgressTrack"), workoutPlayerBar: $("workoutPlayerBar"),
    workoutBackBtn: $("workoutBackBtn"), workoutTimeEl: $("workoutTimeEl"), workoutFsBtn: $("workoutFsBtn"), workoutFsHint: $("workoutFsHint"),
    workoutFsHintOpenBtn: $("workoutFsHintOpenBtn"), workoutFsHintClose: $("workoutFsHintClose"),
    workoutDonePanel: $("workoutDonePanel"), workoutDoneSummary: $("workoutDoneSummary"), workoutRating: $("workoutRating"),
    workoutAgainBtn: $("workoutAgainBtn"), workoutDoneBackBtn: $("workoutDoneBackBtn"),
    workoutTransition: $("workoutTransition"), workoutTransitionTitle: $("workoutTransitionTitle"),
    workoutTransitionMeta: $("workoutTransitionMeta"), workoutTransitionBtn: $("workoutTransitionBtn"),
    workoutProgramDonePanel: $("workoutProgramDonePanel"), workoutProgramDoneSummary: $("workoutProgramDoneSummary"),
    workoutProgramRating: $("workoutProgramRating"), workoutProgramAgainBtn: $("workoutProgramAgainBtn"), workoutProgramDoneBackBtn: $("workoutProgramDoneBackBtn"),

    comboBundleOverview: $("comboBundleOverview"), comboBundleBackToHome: $("comboBundleBackToHome"), comboBundleTitle: $("comboBundleTitle"), comboBundleList: $("comboBundleList"),
    comboScreen: $("comboScreen"), comboBackToHome: $("comboBackToHome"), comboSavedGroup: $("comboSavedGroup"), comboSavedList: $("comboSavedList"),
    comboNameInput: $("comboNameInput"), comboAddGrid: $("comboAddGrid"), comboBlockCount: $("comboBlockCount"),
    comboBlockList: $("comboBlockList"), comboEmptyHint: $("comboEmptyHint"), comboStartBtn: $("comboStartBtn"), comboSaveBtn: $("comboSaveBtn"),
    comboTransition: $("comboTransition"), comboTransitionTitle: $("comboTransitionTitle"), comboTransitionMeta: $("comboTransitionMeta"), comboTransitionBtn: $("comboTransitionBtn"),
    comboDonePanel: $("comboDonePanel"), comboDoneSummary: $("comboDoneSummary"), comboRating: $("comboRating"),
    comboAgainBtn: $("comboAgainBtn"), comboDoneBackBtn: $("comboDoneBackBtn"),
  };

  const SCREENS = ["home", "breathHome", "movementHome", "workoutHome", "bundleOverview", "programIntro", "ready", "breathReady", "breathBundleOverview", "breathProgramIntro", "wimhofReady", "movementReady", "workoutBundleOverview", "workoutProgramIntro", "workoutTabataReady", "comboScreen", "comboBundleOverview"];
  function showScreen(name) {
    SCREENS.forEach((s) => { els[s].hidden = s !== name; });
    if (name === "home" || name === "breathHome" || name === "movementHome" || name === "workoutHome") renderHistory();
    if (name !== "home") els.programError.hidden = true;
    if (name !== "breathHome") els.breathProgramError.hidden = true;
    if (name !== "workoutHome") els.workoutProgramError.hidden = true;
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
      showScreen(sec === "breath" ? "breathHome" : sec === "movement" ? "movementHome" : sec === "workout" ? "workoutHome" : "home");
    });
  });
  document.querySelectorAll("[data-open-combo]").forEach((btn) => btn.addEventListener("click", () => openComboScreen()));

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
  const PROGRAM_HISTORY_KINDS = ["program", "breath-program", "workout-plan", "combo"];
  function isCompleted(progKey) {
    return loadHistory().some((e) => PROGRAM_HISTORY_KINDS.includes(e.kind) && e.progKey === progKey);
  }
  function startOfWeek() {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    return d;
  }
  const WEEKDAYS = ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"];
  function ratingLabel(kind) { return kind === "breath" || kind === "breath-program" ? "Ruhe" : "Fokus"; }
  const HISTORY_VISIBLE_SHORT = 5;
  const HISTORY_VISIBLE_EXPANDED = 20;
  function renderHistoryInto(sectionEl, statsEl, listEl, moreBtn, list) {
    sectionEl.hidden = list.length === 0;
    if (!list.length) return;
    const weekStart = startOfWeek();
    const week = list.filter((e) => new Date(e.ts) >= weekStart);
    const weekSec = week.reduce((s, e) => s + (e.seconds || 0), 0);
    statsEl.innerHTML =
      `<div class="stat"><strong>${week.length}</strong><span>Trainings diese Woche</span></div>` +
      `<div class="stat"><strong>${week.length ? fmtMinutes(weekSec) : "–"}</strong><span>Trainingszeit diese Woche</span></div>` +
      `<div class="stat"><strong>${list.length}</strong><span>Trainings gesamt</span></div>`;
    const expanded = listEl.dataset.expanded === "1";
    const visibleCount = expanded ? HISTORY_VISIBLE_EXPANDED : HISTORY_VISIBLE_SHORT;
    listEl.innerHTML = list.slice(0, visibleCount).map((e) => {
      const d = new Date(e.ts);
      const date = `${WEEKDAYS[d.getDay()]}, ${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}.`;
      const rating = e.rating ? ` · ${ratingLabel(e.kind)} ${e.rating}/5` : "";
      const note = e.note ? ` · ${esc(e.note)}` : "";
      return `<li><span class="h-date">${date}</span><span class="h-title">${esc(e.title)}</span><span class="h-meta">${fmtMinutes(e.seconds || 0)}${note}${rating}</span></li>`;
    }).join("");
    moreBtn.hidden = list.length <= HISTORY_VISIBLE_SHORT;
    moreBtn.textContent = expanded ? "Weniger anzeigen" : "Alle anzeigen";
  }
  function renderHistory() {
    const list = loadHistory();
    renderHistoryInto(els.historySection, els.historyStats, els.historyList, els.historyMoreBtn, list);
    renderHistoryInto(els.breathHistorySection, els.breathHistoryStats, els.breathHistoryList, els.breathHistoryMoreBtn, list);
    renderHistoryInto(els.movementHistorySection, els.movementHistoryStats, els.movementHistoryList, els.movementHistoryMoreBtn, list);
    renderHistoryInto(els.workoutHistorySection, els.workoutHistoryStats, els.workoutHistoryList, els.workoutHistoryMoreBtn, list);
  }
  function clearHistory() {
    if (!confirm("Deinen Trainingsverlauf auf diesem Gerät löschen?")) return;
    writeJSON(HISTORY_KEY, []);
    renderHistory();
  }
  els.historyClearBtn.addEventListener("click", clearHistory);
  els.breathHistoryClearBtn.addEventListener("click", clearHistory);
  els.movementHistoryClearBtn.addEventListener("click", clearHistory);
  els.workoutHistoryClearBtn.addEventListener("click", clearHistory);
  [els.historyList, els.breathHistoryList, els.movementHistoryList, els.workoutHistoryList].forEach((listEl, i) => {
    const btn = [els.historyMoreBtn, els.breathHistoryMoreBtn, els.movementHistoryMoreBtn, els.workoutHistoryMoreBtn][i];
    btn.addEventListener("click", () => { listEl.dataset.expanded = listEl.dataset.expanded === "1" ? "0" : "1"; renderHistory(); });
  });

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
        container.querySelectorAll("[data-rate]").forEach((b) => setActive(b, Number(b.dataset.rate) === n));
        container.querySelector(".rating-thanks").hidden = false;
      });
    });
  }

  // ---- Focus trap for the sheets/modal (tips, video) ----
  // Keeps Tab from leaving the open dialog and returns focus to whatever
  // opened it on close, instead of letting it fall through to elements
  // underneath (e.g. Tab landing on "Verlauf löschen" behind the sheet).
  const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
  function focusFirstIn(sheetEl) {
    const f = sheetEl.querySelector(FOCUSABLE);
    if (f) f.focus();
  }
  function trapTabKey(sheetEl, e) {
    if (e.key !== "Tab" || sheetEl.hidden) return;
    const list = sheetEl.querySelectorAll(FOCUSABLE);
    if (!list.length) return;
    const first = list[0], last = list[list.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  }

  // ---- Video modal (explainer clips) ----
  let videoModalReturnFocus = null;
  function openVideoModal(src) {
    videoModalReturnFocus = document.activeElement;
    els.videoModalPlayer.src = src;
    els.videoModal.hidden = false;
    els.videoModalPlayer.play().catch(() => {});
    focusFirstIn(els.videoModal);
  }
  function closeVideoModal() {
    els.videoModalPlayer.pause();
    els.videoModalPlayer.removeAttribute("src");
    els.videoModalPlayer.load();
    els.videoModal.hidden = true;
    if (videoModalReturnFocus) videoModalReturnFocus.focus();
  }
  els.videoModalClose.addEventListener("click", closeVideoModal);
  els.videoModal.addEventListener("click", (e) => { if (e.target === els.videoModal) closeVideoModal(); });
  els.videoModal.addEventListener("keydown", (e) => trapTabKey(els.videoModal, e));

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
  let active = { colors: keysToColors(state.colors) };

  function randInterval(rng) {
    const lo = Math.min(state.intervalMin, state.intervalMax);
    const hi = Math.max(state.intervalMin, state.intervalMax);
    return lo + rng() * (hi - lo);
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

  // ---- Duration / tempo / sliders ----
  document.querySelectorAll("[data-dur]").forEach((el) => {
    el.addEventListener("click", () => { state.duration = Number(el.dataset.dur); savePrefs(); syncDurationUI(); });
  });
  function syncDurationUI() {
    document.querySelectorAll("[data-dur]").forEach((el) => setActive(el, el.dataset.dur === String(state.duration)));
    els.durationSlider.value = state.duration;
    els.durationValue.textContent = state.duration >= 60 ? fmtMinutes(state.duration) : state.duration + " s";
    const ex = EXERCISES[state.exercise];
    const isConeTap = ex && ex.type === "color-tap";
    els.coneBestHint.hidden = !isConeTap;
    if (isConeTap) {
      const best = coneBestFor(state.duration);
      els.coneBestHint.textContent = best
        ? `Deine Bestleistung bei dieser Dauer: ${best} Durchgänge.`
        : "Noch keine Bestleistung bei dieser Dauer – leg los!";
    }
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
      setActive(el, on);
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
    const isConeTap = ex.type === "color-tap";
    els.tempoGroup.hidden = isConeTap;
    els.advanced.hidden = isConeTap;
    syncColorUI();
    syncDurationUI();
    syncTempoUI();
    els.vtSaveForm.hidden = true;
    els.vtSaveBtn.hidden = false;
    renderVTSaved();
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
    if (BREATH_PROGRAMS[code]) return BREATH_PROGRAMS[code];
    if (WORKOUT_PLANS[code]) return WORKOUT_PLANS[code];
    try {
      const res = await fetch(`${CODE_API}?code=${encodeURIComponent(code)}`);
      if (res.ok) return await res.json();
    } catch (e) {}
    return null;
  }

  let originBundle = null; // { def, code } - set when a programme was opened from a bundle overview

  // A code can resolve to a visual programme/bundle or, with the newer
  // "breath-program"/"breath-bundle" types, a breathing one - handled from
  // either home's code box (and from a #code link) through this one lookup,
  // branching on the shape the API/local table returns.
  const VISUAL_CODE_CTX = { goBtn: els.programGoBtn, errorEl: els.programError, homeScreen: "home" };
  const BREATH_CODE_CTX = { goBtn: els.breathProgramGoBtn, errorEl: els.breathProgramError, homeScreen: "breathHome" };
  const WORKOUT_CODE_CTX = { goBtn: els.workoutProgramGoBtn, errorEl: els.workoutProgramError, homeScreen: "workoutHome" };

  async function openProgramIntro(code, ctx) {
    ctx = ctx || VISUAL_CODE_CTX;
    if (ctx.goBtn) { ctx.goBtn.disabled = true; ctx.goBtn.textContent = "Lädt …"; }
    const def = await lookupProgram(code);
    if (ctx.goBtn) { ctx.goBtn.disabled = false; ctx.goBtn.textContent = "Öffnen"; }
    if (!def) {
      if (ctx.errorEl) ctx.errorEl.hidden = false;
      showScreen(ctx.homeScreen);
      return;
    }
    if (ctx.errorEl) ctx.errorEl.hidden = true;
    if (def.type === "bundle") { openBundleOverview(def, code); return; }
    if (def.type === "breath-bundle") { openBreathBundleOverview(def, code); return; }
    if (def.type === "breath-program") { breathOriginBundle = null; renderBreathProgramIntro(def, code, code); return; }
    if (def.type === "workout-bundle") { openWorkoutBundleOverview(def, code); return; }
    if (def.type === "workout-plan") { workoutOriginBundle = null; renderWorkoutProgramIntro(def, code, code); return; }
    if (def.type === "combo-bundle") { openComboBundleOverview(def, code); return; }
    if (def.type === "combo-program") { comboOriginBundle = null; startComboProgram(def, code, code, ctx.homeScreen); return; }
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
    if (code) openProgramIntro(code, VISUAL_CODE_CTX);
  });
  els.programCodeInput.addEventListener("keydown", (e) => { if (e.key === "Enter") els.programGoBtn.click(); });
  els.programCodeInput.addEventListener("input", () => { els.programError.hidden = true; });
  els.programBackToHome.addEventListener("click", () => {
    if (originBundle) openBundleOverview(originBundle.def, originBundle.code);
    else showScreen("home");
  });
  els.bundleBackToHome.addEventListener("click", () => { originBundle = null; showScreen("home"); });

  els.breathProgramGoBtn.addEventListener("click", () => {
    const code = normCode(els.breathProgramCodeInput.value || "");
    if (code) openProgramIntro(code, BREATH_CODE_CTX);
  });
  els.breathProgramCodeInput.addEventListener("keydown", (e) => { if (e.key === "Enter") els.breathProgramGoBtn.click(); });
  els.breathProgramCodeInput.addEventListener("input", () => { els.breathProgramError.hidden = true; });

  // A #code in the link (…/fwmc-Training-app/#abc123) opens that programme
  // directly - no typing needed. Also reacts when only the hash changes.
  // Works for either a visual or a breathing code; only the fallback (error
  // box, home screen) if the code isn't found assumes Visual Training.
  function openFromHash() {
    if (!location.hash || location.hash.length < 2) return;
    const tokenCode = normCode(decodeURIComponent(location.hash.slice(1)));
    if (!tokenCode) return;
    els.programCodeInput.value = tokenCode;
    openProgramIntro(tokenCode, VISUAL_CODE_CTX);
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

  function renderBreathFeaturedPrograms() {
    const entries = Object.entries(BREATH_PROGRAMS).filter(([, def]) => def.featured);
    if (entries.length === 0) { els.breathFeaturedPrograms.hidden = true; return; }
    els.breathFeaturedPrograms.hidden = false;
    els.breathFeaturedGrid.innerHTML = "";
    entries.forEach(([code, def]) => {
      const card = document.createElement("button");
      card.className = "featured-card";
      card.innerHTML =
        `<span class="fc-title">${esc(def.name)}</span>` +
        `<span class="fc-desc">${esc(def.description || "")}</span>` +
        `<span class="fc-meta">${exerciseCountLabel(def.blocks.length)} · ca. ${fmtMinutes(breathProgramSeconds(def))}</span>`;
      card.addEventListener("click", () => openProgramIntro(code, BREATH_CODE_CTX));
      els.breathFeaturedGrid.appendChild(card);
    });
  }
  renderBreathFeaturedPrograms();

  // ---- Breathing programme overview + intro screens (mirrors the visual
  // bundle/programme screens above, one code namespace for both) ----
  let breathOriginBundle = null; // { def, code } - set when opened from a bundle overview

  function openBreathBundleOverview(bundleDef, code) {
    els.breathBundleTitle.textContent = bundleDef.name || "Deine Programme";
    els.breathBundleList.innerHTML = "";
    const sorted = bundleDef.programs
      .map((p, i) => ({ p, i }))
      .sort((a, b) => (b.p.createdAt || "").localeCompare(a.p.createdAt || "") || (a.i - b.i));
    sorted.forEach(({ p, i }, pos) => {
      const key = `breath:${code}#${i}`;
      const done = isCompleted(key);
      const isNew = pos === 0 && sorted.length > 1 && p.createdAt;
      const item = document.createElement("button");
      item.className = "bundle-item";
      const dateLabel = formatDateDE(p.createdAt);
      const badges = (isNew ? `<span class="badge badge-new">Neu</span>` : "") + (done ? `<span class="badge badge-done">&#10003; Erledigt</span>` : "");
      item.innerHTML =
        `<div class="bundle-item-head"><strong>${esc(p.label || ("Programm " + (i + 1)))}</strong>${dateLabel ? `<span class="bundle-date">${dateLabel}</span>` : ""}</div>` +
        (badges ? `<div class="badges">${badges}</div>` : "") +
        `<span class="bundle-meta">${exerciseCountLabel(p.blocks.length)} · ca. ${fmtMinutes(breathProgramSeconds(p))}</span>` +
        (p.description ? `<span class="bundle-desc">${esc(p.description)}</span>` : "");
      item.addEventListener("click", () => {
        breathOriginBundle = { def: bundleDef, code };
        renderBreathProgramIntro(p, code, key);
      });
      els.breathBundleList.appendChild(item);
    });
    showScreen("breathBundleOverview");
  }

  function renderBreathProgramIntro(def, code, key) {
    const title = def.name || def.label || "Dein Atemtraining";
    els.breathProgramTitle.textContent = title;
    els.breathProgramMeta.textContent = `${exerciseCountLabel(def.blocks.length)} · ca. ${fmtMinutes(breathProgramSeconds(def))}`;
    els.breathProgramDesc.textContent = def.description || "";
    els.breathProgramDesc.hidden = !def.description;
    const start = (i) => {
      breathProgram = { def, blockIndex: i, code, key, title, totalPlayedS: 0 };
      startBreathProgramBlock(i);
    };
    els.breathChapterList.innerHTML = "";
    def.blocks.forEach((block, i) => {
      const row = document.createElement("div");
      row.className = "chapter-row";
      const main = document.createElement("button");
      main.className = "chapter-main";
      main.innerHTML = `<span class="num">${i + 1}</span><span class="info"><strong>${esc(blockPatternName(block))}</strong><span>${esc(blockMetaText(block))}</span></span>`;
      main.addEventListener("click", () => start(i));
      row.appendChild(main);
      els.breathChapterList.appendChild(row);
    });
    els.breathProgramStartBtn.onclick = () => start(0);
    showScreen("breathProgramIntro");
  }

  els.breathProgramBackToHome.addEventListener("click", () => {
    if (breathOriginBundle) openBreathBundleOverview(breathOriginBundle.def, breathOriginBundle.code);
    else showScreen("breathHome");
  });
  els.breathBundleBackToHome.addEventListener("click", () => { breathOriginBundle = null; showScreen("breathHome"); });

  // ---- Workout programme overview + intro screens (same pattern as breath's) ----
  els.workoutProgramGoBtn.addEventListener("click", () => {
    const code = normCode(els.workoutProgramCodeInput.value || "");
    if (code) openProgramIntro(code, WORKOUT_CODE_CTX);
  });
  els.workoutProgramCodeInput.addEventListener("keydown", (e) => { if (e.key === "Enter") els.workoutProgramGoBtn.click(); });
  els.workoutProgramCodeInput.addEventListener("input", () => { els.workoutProgramError.hidden = true; });

  function renderWorkoutFeaturedPrograms() {
    const entries = Object.entries(WORKOUT_PLANS).filter(([, def]) => def.featured);
    if (entries.length === 0) { els.workoutFeaturedPrograms.hidden = true; return; }
    els.workoutFeaturedPrograms.hidden = false;
    els.workoutFeaturedGrid.innerHTML = "";
    entries.forEach(([code, def]) => {
      const card = document.createElement("button");
      card.className = "featured-card";
      card.innerHTML =
        `<span class="fc-title">${esc(def.name)}</span>` +
        `<span class="fc-desc">${esc(def.description || "")}</span>` +
        `<span class="fc-meta">${exerciseCountLabel(def.blocks.length)} · ca. ${fmtMinutes(def.blocks.reduce((s, b) => s + workoutBlockSeconds(b), 0))}</span>`;
      card.addEventListener("click", () => openProgramIntro(code, WORKOUT_CODE_CTX));
      els.workoutFeaturedGrid.appendChild(card);
    });
  }
  renderWorkoutFeaturedPrograms();

  let workoutOriginBundle = null; // { def, code } - set when opened from a bundle overview
  function workoutPlanSeconds(def) { return def.blocks.reduce((s, b) => s + workoutBlockSeconds(b), 0); }

  function openWorkoutBundleOverview(bundleDef, code) {
    els.workoutBundleTitle.textContent = bundleDef.name || "Deine Trainingspläne";
    els.workoutBundleList.innerHTML = "";
    const sorted = bundleDef.programs
      .map((p, i) => ({ p, i }))
      .sort((a, b) => (b.p.createdAt || "").localeCompare(a.p.createdAt || "") || (a.i - b.i));
    sorted.forEach(({ p, i }, pos) => {
      const key = `workout:${code}#${i}`;
      const done = isCompleted(key);
      const isNew = pos === 0 && sorted.length > 1 && p.createdAt;
      const item = document.createElement("button");
      item.className = "bundle-item";
      const dateLabel = formatDateDE(p.createdAt);
      const badges = (isNew ? `<span class="badge badge-new">Neu</span>` : "") + (done ? `<span class="badge badge-done">&#10003; Erledigt</span>` : "");
      item.innerHTML =
        `<div class="bundle-item-head"><strong>${esc(p.label || ("Plan " + (i + 1)))}</strong>${dateLabel ? `<span class="bundle-date">${dateLabel}</span>` : ""}</div>` +
        (badges ? `<div class="badges">${badges}</div>` : "") +
        `<span class="bundle-meta">${exerciseCountLabel(p.blocks.length)} · ca. ${fmtMinutes(workoutPlanSeconds(p))}</span>` +
        (p.description ? `<span class="bundle-desc">${esc(p.description)}</span>` : "");
      item.addEventListener("click", () => {
        workoutOriginBundle = { def: bundleDef, code };
        renderWorkoutProgramIntro(p, code, key);
      });
      els.workoutBundleList.appendChild(item);
    });
    showScreen("workoutBundleOverview");
  }

  function renderWorkoutProgramIntro(def, code, key) {
    const title = def.name || def.label || "Dein Trainingsplan";
    els.workoutProgramTitle.textContent = title;
    els.workoutProgramMeta.textContent = `${exerciseCountLabel(def.blocks.length)} · ca. ${fmtMinutes(workoutPlanSeconds(def))}`;
    els.workoutProgramDesc.textContent = def.description || "";
    els.workoutProgramDesc.hidden = !def.description;
    const start = (i) => {
      workoutPlan = { def, blockIndex: i, code, key, title, totalPlayedS: 0 };
      startWorkoutPlanBlock(i);
    };
    els.workoutChapterList.innerHTML = "";
    def.blocks.forEach((block, i) => {
      const row = document.createElement("div");
      row.className = "chapter-row";
      const main = document.createElement("button");
      main.className = "chapter-main";
      main.innerHTML = `<span class="num">${i + 1}</span><span class="info"><strong>${esc(workoutBlockLabel(block))}</strong><span>${esc(workoutBlockMeta(block))}</span></span>`;
      main.addEventListener("click", () => start(i));
      row.appendChild(main);
      els.workoutChapterList.appendChild(row);
    });
    els.workoutProgramStartBtn.onclick = () => start(0);
    showScreen("workoutProgramIntro");
  }

  els.workoutProgramBackToHome.addEventListener("click", () => {
    if (workoutOriginBundle) openWorkoutBundleOverview(workoutOriginBundle.def, workoutOriginBundle.code);
    else showScreen("workoutHome");
  });
  els.workoutBundleBackToHome.addEventListener("click", () => { workoutOriginBundle = null; showScreen("workoutHome"); });

  // ---- Session engine ----
  let raf = null;
  let wakeLock = null;
  let session = null;
  let coneTap = null; // { target, count } - set while the tap-paced cone-colour exercise runs

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

  function buildColorSchedule(cfg, rng) {
    const colors = active.colors;
    const schedule = [];
    let t = pushCountdown(schedule, cfg);
    const show = state.stimulusS;
    while (t < state.duration) {
      const color = colors[Math.floor(rng() * colors.length)];
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "color", payload: { color: color.hex } });
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
      cfg.type === "color" ? buildColorSchedule(cfg, rng) :
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

  // Hides every full-screen player overlay (visual, breath-cycle, Wim Hof)
  // plus the cross-engine transition/finish panels. Called at the start of
  // each engine's own start function so a leftover overlay from switching
  // mid-programme between a cycle block and a Wim-Hof block never shows.
  function hideAllPlayers() {
    els.player.hidden = true;
    els.breathPlayer.hidden = true;
    els.wimhofPlayer.hidden = true;
    els.movementPlayer.hidden = true;
    els.workoutPlayer.hidden = true;
    els.breathTransition.hidden = true;
    els.workoutTransition.hidden = true;
    els.workoutProgramDonePanel.hidden = true;
    els.comboTransition.hidden = true;
    els.comboDonePanel.hidden = true;
    els.breathProgramDonePanel.hidden = true;
  }

  function runSession() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.player.hidden = false;
    els.playerBar.hidden = false;
    els.progressTrack.hidden = false;
    els.coneOrderStage.hidden = true;
    els.stageWrap.hidden = false;
    fitCanvas();
    ensureAudioCtx();
    const built = buildScheduleFor(EXERCISES[state.exercise], Math.random);
    session = { ...built, startTime: performance.now(), lastIndex: -1 };
    requestWakeLock();
    raf = requestAnimationFrame(tick);
  }

  // Tap-paced cone-order exercise ("Hütchen sortieren"): four big colour
  // dots show the order the client's four cones should be sorted into. Runs
  // for a fixed duration (the shared "Dauer" setting) and counts how many
  // times the client manages to re-sort and confirm a new order before the
  // time is up - speed of repetition, not a target count, is the point. It
  // gets its own tiny tick loop (time-driven, not schedule-driven) and plain
  // DOM dots instead of the canvas, so the whole stage - including the gaps
  // between dots - is tappable, with no dead zone from canvas/CSS sizing
  // mismatches.
  const CONE_BEST_KEY = "fwmc-cone-best-v1"; // { [durationSeconds]: bestRoundCount }
  function coneBestFor(duration) { return readJSON(CONE_BEST_KEY, {})[duration] || 0; }
  function saveConeBest(duration, count) {
    const best = readJSON(CONE_BEST_KEY, {});
    if (count > (best[duration] || 0)) { best[duration] = count; writeJSON(CONE_BEST_KEY, best); return true; }
    return false;
  }

  function shuffledConeOrder(prevKey) {
    let order;
    do {
      order = [...CONE_TAP_COLORS];
      for (let i = order.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [order[i], order[j]] = [order[j], order[i]];
      }
    } while (prevKey && order.map((c) => c.key).join() === prevKey);
    return order;
  }

  function renderConeOrderRound() {
    const order = shuffledConeOrder(coneTap.lastOrder);
    coneTap.lastOrder = order.map((c) => c.key).join();
    els.coneOrderRow.innerHTML = order.map((c) =>
      `<span class="cone-order-dot" style="background:${c.hex}" aria-label="${c.name}"></span>`).join("");
    els.coneOrderCount.textContent = `${coneTap.count} geschafft`;
  }

  function coneTapTick(now) {
    if (!coneTap) return;
    const elapsed = (now - session.startTime) / 1000;
    if (elapsed >= session.total) { finishSession(); return; }
    els.timeEl.textContent = fmtClock(session.total - elapsed);
    raf = requestAnimationFrame(coneTapTick);
  }

  function startConeTap() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.player.hidden = false;
    els.playerBar.hidden = false;
    els.progressTrack.hidden = true;
    els.stageWrap.hidden = true;
    els.coneOrderStage.hidden = false;
    if (raf) cancelAnimationFrame(raf);
    session = { startTime: performance.now(), total: state.duration, schedule: [] };
    coneTap = { count: 0, lastOrder: null, duration: state.duration };
    requestWakeLock();
    renderConeOrderRound();
    raf = requestAnimationFrame(coneTapTick);
  }

  function coneTapAdvance() {
    if (!coneTap) return;
    coneTap.count++;
    renderConeOrderRound();
  }
  els.coneOrderStage.addEventListener("click", () => coneTapAdvance());

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
    active = { colors: keysToColors(state.colors) };
    buildProgressTrack(1);
    els.liveNav.hidden = true;
    if (EXERCISES[state.exercise].type === "color-tap") startConeTap();
    else runSession();
  }

  function finishSession() {
    if (raf) cancelAnimationFrame(raf);
    const spent = accountSession();
    if (window.speechSynthesis) speechSynthesis.cancel();
    els.liveNav.hidden = true;
    if (program) { startPause(); return; }
    if (comboProgram) { coneTap = null; advanceComboProgram(spent); return; }
    releaseWakeLock();
    setProgress(1, 0);
    const ex = EXERCISES[state.exercise];
    let summary, note;
    if (coneTap) {
      const isRecord = saveConeBest(coneTap.duration, coneTap.count);
      note = `${coneTap.count} Durchgänge`;
      summary = `${coneTap.count} Durchgänge · ${fmtMinutes(spent)}` + (isRecord && coneTap.count > 0 ? " · Neue Bestleistung!" : "");
    } else {
      summary = `${ex.title} · ${fmtMinutes(spent)}`;
    }
    els.doneSummary.textContent = summary;
    const id = addHistory({ kind: "exercise", title: ex.title, seconds: Math.round(spent), note });
    renderRating(els.doneRating, id);
    els.donePanel.hidden = false;
    els.playerBar.hidden = true;
    coneTap = null;
  }

  function leavePlayer() {
    if (raf) cancelAnimationFrame(raf);
    session = null;
    coneTap = null;
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
    if (comboProgram) { leavePlayer(); abortComboProgram(); return; }
    const wasProgram = !!program;
    leavePlayer();
    if (wasProgram) showScreen("programIntro");
    else openReady(state.exercise, els.readyIcon.innerHTML);
  }

  els.startBtn.addEventListener("click", startSession);
  els.backBtn.addEventListener("click", abortTraining);
  els.doneBack.addEventListener("click", stopToHome);

  // ---- VT: save the current settings under a name, reuse from the list ----
  const VT_SAVED_KEY = "fwmc-vt-saved-v1";
  const vtSavedStore = makePresetStore(VT_SAVED_KEY);
  function renderVTSaved() {
    renderPresetList(vtSavedStore, els.vtSavedList, els.vtSavedGroup, (e) => e.exercise === state.exercise,
      (e) => `${fmtMinutes(e.duration)}${e.colors && e.colors.length ? ` · ${e.colors.length} Farben` : ""}`,
      (entry) => {
        state.colors = entry.colors.slice();
        state.duration = entry.duration;
        state.stimulusS = entry.stimulusS;
        state.intervalMin = entry.intervalMin;
        state.intervalMax = entry.intervalMax;
        savePrefs();
        active = { colors: keysToColors(state.colors) };
        startSession();
      });
  }
  wirePresetSaveForm({
    saveBtn: els.vtSaveBtn, form: els.vtSaveForm, nameInput: els.vtSaveNameInput,
    cancelBtn: els.vtSaveCancelBtn, confirmBtn: els.vtSaveConfirmBtn,
    defaultName: () => `Eigene Einstellung ${new Date().toLocaleDateString("de-DE")}`,
    onSave: (name) => {
      const list = vtSavedStore.load();
      list.push({
        id: String(Date.now()), name, exercise: state.exercise,
        colors: state.colors.slice(), duration: state.duration,
        stimulusS: state.stimulusS, intervalMin: state.intervalMin, intervalMax: state.intervalMax,
      });
      vtSavedStore.save(list);
      renderVTSaved();
    },
  });
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
  wireFullscreen({ player: els.wimhofPlayer, btn: els.wimhofFsBtn, hint: els.wimhofFsHint, hintOpen: els.wimhofFsHintOpenBtn, hintClose: els.wimhofFsHintClose });
  wireFullscreen({ player: els.movementPlayer, btn: els.movementFsBtn, hint: els.movementFsHint, hintOpen: els.movementFsHintOpenBtn, hintClose: els.movementFsHintClose });
  wireFullscreen({ player: els.workoutPlayer, btn: els.workoutFsBtn, hint: els.workoutFsHint, hintOpen: els.workoutFsHintOpenBtn, hintClose: els.workoutFsHintClose });
  window.addEventListener("resize", () => { if (!els.player.hidden && !coneTap) fitCanvas(); });
  // All the exercise engines compute "elapsed" as performance.now() minus a
  // startTime captured when they began. Backgrounding the tab (switching
  // apps, locking the screen) doesn't pause that clock, so returning later
  // could skip stimuli or a whole breath phase. Shifting every active
  // engine's timestamps forward by exactly the hidden duration makes it as
  // if no time passed while away, instead of building a separate pause/
  // resume UI for each engine.
  let hiddenAt = null;
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      hiddenAt = performance.now();
      return;
    }
    if (document.visibilityState !== "visible") return;
    if (hiddenAt !== null) {
      const hiddenMs = performance.now() - hiddenAt;
      hiddenAt = null;
      if (hiddenMs > 500) {
        if (session) session.startTime += hiddenMs;
        if (breathSession && !breathPaused) breathSession.startTime += hiddenMs;
        if (wimhofState) { wimhofState.phaseStart += hiddenMs; wimhofState.sessionStart += hiddenMs; }
        if (movementSession) movementSession.startTime += hiddenMs;
        if (workoutState) {
          if (workoutState.startTime) workoutState.startTime += hiddenMs;
          if (workoutState.phaseStart) workoutState.phaseStart += hiddenMs;
          if (workoutState.sessionStart) workoutState.sessionStart += hiddenMs;
        }
      }
    }
    if ((session || breathSession || wimhofState || movementSession || workoutState) && wakeLock === null) requestWakeLock();
  });

  // ---- Tips sheet (shown once on first visit, reopenable) ----
  const TIPS_KEY = "fwmc-tips-seen";
  const standalone = window.matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  if (standalone) els.tipInstall.hidden = true;
  else if (isIOS) els.tipInstallText.textContent = "Tippe in Safari auf „Teilen“ und dann auf „Zum Home-Bildschirm“ – dann startest du dein Training mit einem Tipp.";
  let tipsReturnFocus = null;
  function openTips() { tipsReturnFocus = document.activeElement; els.tipsSheet.hidden = false; focusFirstIn(els.tipsSheet); }
  function closeTips() { els.tipsSheet.hidden = true; writeJSON(TIPS_KEY, true); if (tipsReturnFocus) tipsReturnFocus.focus(); }
  els.tipsBtn.addEventListener("click", openTips);
  els.tipsCloseBtn.addEventListener("click", closeTips);
  els.tipsSheet.addEventListener("click", (e) => { if (e.target === els.tipsSheet) closeTips(); });
  els.tipsSheet.addEventListener("keydown", (e) => trapTabKey(els.tipsSheet, e));
  let breathTipsReturnFocus = null;
  function openBreathTips() { breathTipsReturnFocus = document.activeElement; els.breathTipsSheet.hidden = false; focusFirstIn(els.breathTipsSheet); }
  function closeBreathTips() { els.breathTipsSheet.hidden = true; if (breathTipsReturnFocus) breathTipsReturnFocus.focus(); }
  els.breathTipsBtn.addEventListener("click", openBreathTips);
  els.breathTipsCloseBtn.addEventListener("click", closeBreathTips);
  els.breathTipsSheet.addEventListener("click", (e) => { if (e.target === els.breathTipsSheet) closeBreathTips(); });
  els.breathTipsSheet.addEventListener("keydown", (e) => trapTabKey(els.breathTipsSheet, e));
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
    // Wim Hof is a different mechanic (see below), so it's a separate card
    // with its own caution tag rather than one more BREATH_PATTERNS entry.
    const whCard = document.createElement("button");
    whCard.className = "featured-card";
    whCard.innerHTML =
      `<span class="fc-title">${esc(WIMHOF_INFO.name)}</span>` +
      `<span class="fc-desc">${esc(WIMHOF_INFO.short)}</span>` +
      `<span class="tag-caution">Aktivierend &middot; Sicherheitshinweise beachten</span>`;
    whCard.addEventListener("click", () => openWimhofReady());
    els.patternGrid.appendChild(whCard);
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
    document.querySelectorAll("[data-breath-dur]").forEach((el) => setActive(el, Number(el.dataset.breathDur) === breathPrefs.durationMin));
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
      setActive(el, (el.dataset.breathSound === "on") === breathPrefs.sound);
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
    els.breathSaveForm.hidden = true;
    els.breathSaveBtn.hidden = false;
    renderBreathSaved();
    showScreen("breathReady");
  }
  els.breathBackToHome.addEventListener("click", () => showScreen("breathHome"));

  // ---- Breathing session engine ----
  let breathRaf = null;
  let breathSession = null; // { schedule, cycleLen, plannedTotal, startTime, lastKey, sound }
  let breathPatternName = "";
  // Set while a coach-authored breathing programme is chaining blocks
  // through this engine and/or the Wim-Hof one below; null for a single
  // freely-chosen pattern. { def, blockIndex, code, key, title, totalPlayedS }
  let breathProgram = null;
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
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.breathPlayer.hidden = false;
    els.breathPlayerBar.hidden = false;
    els.breathDonePanel.hidden = true;
    breathSession = { schedule: built.schedule, cycleLen: built.cycleLen, plannedTotal: cycles * built.cycleLen, startTime: performance.now(), lastKey: null, sound: breathPrefs.sound };
    breathPaused = false;
    els.breathPauseBtn.textContent = "Pause";
    requestWakeLock();
    breathRaf = requestAnimationFrame(breathTick);
  }
  els.breathStartBtn.addEventListener("click", startBreathSession);

  // Pause/Fortsetzen: the tips sheet tells clients to pause if they feel
  // unwell, so the breath player needs an actual pause, not just "Beenden".
  let breathPaused = false;
  let breathPauseTime = 0;
  function toggleBreathPause() {
    if (!breathSession) return;
    if (breathPaused) {
      breathPaused = false;
      breathSession.startTime += performance.now() - breathPauseTime;
      els.breathPauseBtn.textContent = "Pause";
      breathRaf = requestAnimationFrame(breathTick);
    } else {
      breathPaused = true;
      breathPauseTime = performance.now();
      if (breathRaf) cancelAnimationFrame(breathRaf);
      breathRaf = null;
      els.breathPauseBtn.textContent = "Fortsetzen";
      els.breathPhaseLabel.textContent = "Pausiert";
    }
  }
  els.breathPauseBtn.addEventListener("click", toggleBreathPause);

  function breathLeavePlayer() {
    if (breathRaf) cancelAnimationFrame(breathRaf);
    breathRaf = null;
    breathSession = null;
    breathPaused = false;
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
    if (breathProgram) { advanceBreathProgram(played); return; }
    if (comboProgram) { advanceComboProgram(played); return; }
    els.breathPlayerBar.hidden = true;
    els.breathDoneSummary.textContent = `${breathPatternName} · ${fmtMinutes(played)}`;
    const id = addHistory({ kind: "breath", title: breathPatternName, seconds: Math.round(played) });
    renderRating(els.breathRating, id, "Wie ruhig fühlst du dich gerade?");
    els.breathDonePanel.hidden = false;
  }
  // "Beenden" mid-training: back to the pattern's settings, or to the
  // programme intro if a coach-authored programme was chaining blocks.
  function breathAbort() {
    if (comboProgram) { breathLeavePlayer(); abortComboProgram(); return; }
    const wasProgram = !!breathProgram;
    breathProgram = null;
    breathLeavePlayer();
    showScreen(wasProgram ? "breathProgramIntro" : "breathReady");
  }
  els.breathBackBtn.addEventListener("click", breathAbort);
  els.breathAgainBtn.addEventListener("click", () => { breathLeavePlayer(); startBreathSession(); });
  els.breathDoneBackBtn.addEventListener("click", () => { breathLeavePlayer(); showScreen("breathHome"); });

  // ---- Saved breathing settings: same "save under a name, tap to reuse"
  // pattern as Kombi/Visual Training, scoped per pattern (a saved 4-7-8
  // setting only shows up again under 4-7-8, etc.). ----
  const BREATH_SAVED_KEY = "fwmc-breath-saved-v1";
  const breathSavedStore = makePresetStore(BREATH_SAVED_KEY);
  function renderBreathSaved() {
    renderPresetList(breathSavedStore, els.breathSavedList, els.breathSavedGroup, (e) => e.patternKey === breathPatternKey,
      (e) => `${fmtMinutes(e.durationMin * 60)} · ${e.phases.in}-${e.phases.hold1}-${e.phases.out}-${e.phases.hold2}s`,
      (entry) => {
        breathPatternKey = entry.patternKey;
        breathWorking = { ...entry.phases };
        breathPrefs.durationMin = entry.durationMin;
        breathPrefs.sound = entry.sound;
        saveBreathPrefs();
        startBreathSession();
      });
  }
  wirePresetSaveForm({
    saveBtn: els.breathSaveBtn, form: els.breathSaveForm, nameInput: els.breathSaveNameInput,
    cancelBtn: els.breathSaveCancelBtn, confirmBtn: els.breathSaveConfirmBtn,
    defaultName: () => `Eigene Einstellung ${new Date().toLocaleDateString("de-DE")}`,
    onSave: (name) => {
      const list = breathSavedStore.load();
      list.push({
        id: String(Date.now()), name, patternKey: breathPatternKey,
        phases: { ...breathWorking }, durationMin: breathPrefs.durationMin, sound: breathPrefs.sound,
      });
      breathSavedStore.save(list);
      renderBreathSaved();
    },
  });

  // ---- Breathing programmes: chain cycle-engine and/or Wim-Hof blocks ----
  function startBreathProgramBlock(idx) {
    if (!breathProgram) return;
    if (idx >= breathProgram.def.blocks.length) { finishBreathProgram(); return; }
    breathProgram.blockIndex = idx;
    const block = breathProgram.def.blocks[idx];
    if (block.pattern === "wimhof") {
      wimhofSettings.breaths = block.breaths ?? WIMHOF_DEFAULTS.breaths;
      wimhofSettings.rounds = block.rounds ?? WIMHOF_DEFAULTS.rounds;
      wimhofSettings.breathPaceS = block.breathPaceS ?? WIMHOF_DEFAULTS.breathPaceS;
      wimhofSettings.recoveryHoldS = block.recoveryHoldS ?? WIMHOF_DEFAULTS.recoveryHoldS;
      startWimhofSession();
    } else {
      breathPatternKey = block.pattern;
      breathWorking = block.phases ? { ...block.phases } : { ...(BREATH_PATTERNS[block.pattern].phases || breathPrefs.custom) };
      breathPrefs.durationMin = block.durationMin ?? 5;
      breathPrefs.sound = block.sound !== false;
      startBreathSession();
    }
  }
  let breathTransitionTimer = null;
  function showBreathTransition(nextBlock, onContinue) {
    hideAllPlayers();
    els.breathTransitionTitle.textContent = blockPatternName(nextBlock);
    els.breathTransitionMeta.textContent = blockMetaText(nextBlock);
    els.breathTransition.hidden = false;
    if (breathTransitionTimer) clearTimeout(breathTransitionTimer);
    const go = () => {
      if (breathTransitionTimer) clearTimeout(breathTransitionTimer);
      els.breathTransition.hidden = true;
      onContinue();
    };
    els.breathTransitionBtn.onclick = go;
    breathTransitionTimer = setTimeout(go, 4000);
  }
  function advanceBreathProgram(playedS) {
    if (!breathProgram) return;
    breathProgram.totalPlayedS += playedS;
    const nextIdx = breathProgram.blockIndex + 1;
    if (nextIdx >= breathProgram.def.blocks.length) { finishBreathProgram(); return; }
    showBreathTransition(breathProgram.def.blocks[nextIdx], () => startBreathProgramBlock(nextIdx));
  }
  let lastBreathProgram = null; // kept after finishBreathProgram so "Nochmal von vorne" can restart it
  function finishBreathProgram() {
    hideAllPlayers();
    const played = breathProgram.totalPlayedS;
    const title = breathProgram.title;
    els.breathProgramDoneSummary.textContent = `${exerciseCountLabel(breathProgram.def.blocks.length)} · ${fmtMinutes(played)} Training`;
    const id = addHistory({ kind: "breath-program", title, progKey: breathProgram.key, seconds: Math.round(played) });
    renderRating(els.breathProgramRating, id, "Wie fühlst du dich nach dem Programm?");
    els.breathProgramDoneBackBtn.textContent = breathOriginBundle ? "Zurück zu meinen Programmen" : "Zur Startseite";
    els.breathProgramDonePanel.hidden = false;
    lastBreathProgram = breathProgram;
    breathProgram = null;
  }
  els.breathProgramAgainBtn.addEventListener("click", () => {
    if (!lastBreathProgram) return;
    els.breathProgramDonePanel.hidden = true;
    breathProgram = { ...lastBreathProgram, blockIndex: 0, totalPlayedS: 0 };
    startBreathProgramBlock(0);
  });
  els.breathProgramDoneBackBtn.addEventListener("click", () => {
    els.breathProgramDonePanel.hidden = true;
    if (breathOriginBundle) openBreathBundleOverview(breathOriginBundle.def, breathOriginBundle.code);
    else showScreen("breathHome");
  });

  // ==== Wim-Hof-style power breathing ====
  // A different mechanic from the steady cycle engine above: a round of
  // fast, full breaths, then a breath hold timed by the client themselves
  // (they end it whenever they feel the urge to breathe - never a forced
  // countdown), then a timed recovery hold on a full inhale, repeated for
  // the chosen number of rounds. Gated behind the safety notes checkbox.
  const WIMHOF_PREFS_KEY = "fwmc-wimhof-v1";
  const wimhofSettings = { ...WIMHOF_DEFAULTS };
  function loadWimhofSettings() {
    const saved = readJSON(WIMHOF_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(wimhofSettings, saved);
  }
  function saveWimhofSettings() { writeJSON(WIMHOF_PREFS_KEY, wimhofSettings); }
  loadWimhofSettings();

  function syncWimhofUI() {
    document.querySelectorAll("[data-wh-breaths]").forEach((el) => setActive(el, Number(el.dataset.whBreaths) === wimhofSettings.breaths));
    document.querySelectorAll("[data-wh-rounds]").forEach((el) => setActive(el, Number(el.dataset.whRounds) === wimhofSettings.rounds));
    document.querySelectorAll("[data-wh-pace]").forEach((el) => setActive(el, Number(el.dataset.whPace) === wimhofSettings.breathPaceS));
    document.querySelectorAll("[data-wh-recovery]").forEach((el) => setActive(el, Number(el.dataset.whRecovery) === wimhofSettings.recoveryHoldS));
  }
  document.querySelectorAll("[data-wh-breaths]").forEach((el) => el.addEventListener("click", () => { wimhofSettings.breaths = Number(el.dataset.whBreaths); saveWimhofSettings(); syncWimhofUI(); }));
  document.querySelectorAll("[data-wh-rounds]").forEach((el) => el.addEventListener("click", () => { wimhofSettings.rounds = Number(el.dataset.whRounds); saveWimhofSettings(); syncWimhofUI(); }));
  document.querySelectorAll("[data-wh-pace]").forEach((el) => el.addEventListener("click", () => { wimhofSettings.breathPaceS = Number(el.dataset.whPace); saveWimhofSettings(); syncWimhofUI(); }));
  document.querySelectorAll("[data-wh-recovery]").forEach((el) => el.addEventListener("click", () => { wimhofSettings.recoveryHoldS = Number(el.dataset.whRecovery); saveWimhofSettings(); syncWimhofUI(); }));

  function syncWimhofStartBtn() {
    const ok = els.wimhofAckCheck.checked;
    els.wimhofStartBtn.disabled = !ok;
    els.wimhofStartBtn.textContent = ok ? "Kraftvolle Atmung starten" : "Bitte oben bestätigen";
  }
  els.wimhofAckCheck.addEventListener("change", syncWimhofStartBtn);

  function openWimhofReady() {
    els.wimhofAckCheck.checked = false; // the safety notes are re-confirmed every visit, not just once
    syncWimhofStartBtn();
    syncWimhofUI();
    showScreen("wimhofReady");
  }
  els.wimhofBackToHome.addEventListener("click", () => showScreen("breathHome"));

  let wimhofRaf = null;
  let wimhofState = null; // { round, phase: "power"|"retention"|"recovery", phaseStart, sessionStart, retentions }
  const wimhofCircle = els.wimhofBig.querySelector(".breath-circle");

  function startWimhofSession() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.wimhofPlayer.hidden = false;
    els.wimhofPlayerBar.hidden = false;
    els.wimhofDonePanel.hidden = true;
    els.wimhofHoldDoneBtn.hidden = true;
    wimhofState = { round: 1, phase: "power", phaseStart: performance.now(), sessionStart: performance.now(), retentions: [] };
    requestWakeLock();
    wimhofRaf = requestAnimationFrame(wimhofTick);
  }
  els.wimhofStartBtn.addEventListener("click", startWimhofSession);

  function wimhofTick(now) {
    if (!wimhofState) return;
    const s = wimhofSettings;
    if (wimhofState.phase === "power") {
      const elapsedInPhase = (now - wimhofState.phaseStart) / 1000;
      const idx = Math.floor(elapsedInPhase / s.breathPaceS);
      if (idx >= s.breaths) {
        wimhofState.phase = "retention";
        wimhofState.phaseStart = now;
        wimhofCircle.style.transform = "scale(0.55)";
        els.wimhofHoldDoneBtn.hidden = false;
      } else {
        const within = (elapsedInPhase % s.breathPaceS) / s.breathPaceS;
        const half = within < 0.5;
        const p = half ? within * 2 : (within - 0.5) * 2;
        const eased = easeInOut(p);
        const scale = half ? 0.55 + 0.45 * eased : 1 - 0.45 * eased;
        wimhofCircle.style.transform = `scale(${scale.toFixed(3)})`;
        els.wimhofPhaseLabel.textContent = half ? "Kräftig einatmen" : "Locker loslassen";
        els.wimhofPhaseCount.textContent = idx + 1;
        els.wimhofSub.textContent = `Atemzug ${idx + 1} von ${s.breaths}`;
      }
    } else if (wimhofState.phase === "retention") {
      const held = (now - wimhofState.phaseStart) / 1000;
      els.wimhofPhaseLabel.textContent = "Anhalten – ausgeatmet";
      els.wimhofPhaseCount.textContent = fmtClock(held);
      els.wimhofSub.textContent = "Drücke unten, sobald du wieder einatmen musst.";
    } else {
      const elapsed = (now - wimhofState.phaseStart) / 1000;
      const remain = Math.max(0, s.recoveryHoldS - elapsed);
      wimhofCircle.style.transform = "scale(1)";
      els.wimhofPhaseLabel.textContent = "Halten – voll eingeatmet";
      els.wimhofPhaseCount.textContent = Math.ceil(remain);
      els.wimhofSub.textContent = `Runde ${wimhofState.round} von ${s.rounds}`;
      if (elapsed >= s.recoveryHoldS) {
        if (wimhofState.round >= s.rounds) { wimhofFinish(); return; }
        wimhofState.round += 1;
        wimhofState.phase = "power";
        wimhofState.phaseStart = now;
      }
    }
    els.wimhofStatusEl.textContent = `Runde ${wimhofState.round}/${s.rounds}`;
    wimhofRaf = requestAnimationFrame(wimhofTick);
  }
  els.wimhofHoldDoneBtn.addEventListener("click", () => {
    if (!wimhofState || wimhofState.phase !== "retention") return;
    const held = (performance.now() - wimhofState.phaseStart) / 1000;
    wimhofState.retentions.push(held);
    wimhofState.phase = "recovery";
    wimhofState.phaseStart = performance.now();
    els.wimhofHoldDoneBtn.hidden = true;
  });

  function wimhofFinish() {
    if (wimhofRaf) cancelAnimationFrame(wimhofRaf);
    wimhofRaf = null;
    const s = wimhofState;
    const played = s ? (performance.now() - s.sessionStart) / 1000 : 0;
    const retentions = s ? s.retentions : [];
    wimhofState = null;
    releaseWakeLock();
    if (breathProgram) { advanceBreathProgram(played); return; }
    if (comboProgram) { advanceComboProgram(played); return; }
    els.wimhofPlayerBar.hidden = true;
    const avgHold = retentions.length ? retentions.reduce((a, b) => a + b, 0) / retentions.length : 0;
    els.wimhofDoneSummary.textContent = `${wimhofSettings.rounds} Runden${avgHold ? " · komfortable Anhaltezeit " + fmtClock(avgHold) : ""}`;
    const id = addHistory({ kind: "breath", title: WIMHOF_INFO.name, seconds: Math.round(played) });
    renderRating(els.wimhofRating, id, "Wie wach und energiegeladen fühlst du dich?");
    els.wimhofDonePanel.hidden = false;
  }
  function wimhofLeave() {
    if (wimhofRaf) cancelAnimationFrame(wimhofRaf);
    wimhofRaf = null;
    wimhofState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.wimhofPlayer) document.exitFullscreen().catch(() => {});
    els.wimhofFsHint.hidden = true;
    els.wimhofHoldDoneBtn.hidden = true;
    els.wimhofPlayer.hidden = true;
    els.wimhofDonePanel.hidden = true;
  }
  function wimhofAbort() {
    if (comboProgram) { wimhofLeave(); abortComboProgram(); return; }
    const wasProgram = !!breathProgram;
    breathProgram = null;
    wimhofLeave();
    showScreen(wasProgram ? "breathProgramIntro" : "wimhofReady");
  }
  els.wimhofBackBtn.addEventListener("click", wimhofAbort);
  els.wimhofAgainBtn.addEventListener("click", () => { wimhofLeave(); startWimhofSession(); });
  els.wimhofDoneBackBtn.addEventListener("click", () => { wimhofLeave(); showScreen("breathHome"); });

  // ==== Movement settings + engine ====
  const MOVEMENT_PREFS_KEY = "fwmc-movement-v1";
  const movementPrefs = {
    movements: MOVEMENTS.map((m) => m.id),
    preview: 3, bpm: 60, durationMin: 1, mirror: true, showLabel: true,
  };
  function loadMovementPrefs() {
    const saved = readJSON(MOVEMENT_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(movementPrefs, saved);
    if (!Array.isArray(movementPrefs.movements) || movementPrefs.movements.length < MIN_MOVEMENTS) {
      movementPrefs.movements = MOVEMENTS.map((m) => m.id);
    }
  }
  function saveMovementPrefs() { writeJSON(MOVEMENT_PREFS_KEY, movementPrefs); }
  loadMovementPrefs();

  MOVEMENTS.forEach((m) => {
    const chip = document.createElement("button");
    chip.className = "movement-chip";
    chip.dataset.moveId = m.id;
    chip.innerHTML = figureSVG(resolveSlots([m], true), "var(--ink)") + `<span>${esc(m.label)}</span>`;
    chip.addEventListener("click", () => {
      const on = movementPrefs.movements.includes(m.id);
      if (on) {
        if (movementPrefs.movements.length <= MIN_MOVEMENTS) return;
        movementPrefs.movements = movementPrefs.movements.filter((id) => id !== m.id);
      } else {
        movementPrefs.movements = MOVEMENTS.map((x) => x.id).filter((id) => id === m.id || movementPrefs.movements.includes(id));
      }
      saveMovementPrefs();
      syncMvPickerUI();
    });
    els.movementPicker.appendChild(chip);
  });
  function syncMvPickerUI() {
    els.movementPicker.querySelectorAll(".movement-chip").forEach((el) => {
      setActive(el, movementPrefs.movements.includes(el.dataset.moveId));
    });
    els.movementCount.textContent = `${movementPrefs.movements.length} gewählt`;
  }

  function parsePreview(v) { return v === "all" ? "all" : Number(v); }
  document.querySelectorAll("[data-mv-preview]").forEach((el) => el.addEventListener("click", () => { movementPrefs.preview = parsePreview(el.dataset.mvPreview); saveMovementPrefs(); syncMvPreviewUI(); }));
  function syncMvPreviewUI() { document.querySelectorAll("[data-mv-preview]").forEach((el) => setActive(el, parsePreview(el.dataset.mvPreview) === movementPrefs.preview)); }

  document.querySelectorAll("[data-mv-bpm]").forEach((el) => el.addEventListener("click", () => { movementPrefs.bpm = Number(el.dataset.mvBpm); saveMovementPrefs(); syncMvTempoUI(); }));
  function syncMvTempoUI() {
    document.querySelectorAll("[data-mv-bpm]").forEach((el) => setActive(el, Number(el.dataset.mvBpm) === movementPrefs.bpm));
    els.movementBpmSlider.value = movementPrefs.bpm;
    els.movementBpmValue.textContent = `${movementPrefs.bpm} BPM`;
  }
  els.movementBpmSlider.addEventListener("input", () => {
    movementPrefs.bpm = Number(els.movementBpmSlider.value);
    saveMovementPrefs();
    syncMvTempoUI();
  });

  document.querySelectorAll("[data-mv-dur]").forEach((el) => el.addEventListener("click", () => { movementPrefs.durationMin = Number(el.dataset.mvDur); saveMovementPrefs(); syncMvDurationUI(); }));
  function syncMvDurationUI() { document.querySelectorAll("[data-mv-dur]").forEach((el) => setActive(el, Number(el.dataset.mvDur) === movementPrefs.durationMin)); }

  document.querySelectorAll("[data-mv-mirror]").forEach((el) => el.addEventListener("click", () => { movementPrefs.mirror = el.dataset.mvMirror === "1"; saveMovementPrefs(); syncMvMirrorUI(); }));
  function syncMvMirrorUI() { document.querySelectorAll("[data-mv-mirror]").forEach((el) => setActive(el, (el.dataset.mvMirror === "1") === movementPrefs.mirror)); }

  document.querySelectorAll("[data-mv-label]").forEach((el) => el.addEventListener("click", () => { movementPrefs.showLabel = el.dataset.mvLabel === "1"; saveMovementPrefs(); syncMvLabelUI(); }));
  function syncMvLabelUI() { document.querySelectorAll("[data-mv-label]").forEach((el) => setActive(el, (el.dataset.mvLabel === "1") === movementPrefs.showLabel)); }

  function openMovementReady() {
    syncMvPickerUI(); syncMvPreviewUI(); syncMvTempoUI(); syncMvDurationUI(); syncMvMirrorUI(); syncMvLabelUI();
    els.movementSaveForm.hidden = true;
    els.movementSaveBtn.hidden = false;
    renderMovementSaved();
    showScreen("movementReady");
  }
  els.movementStartCard.addEventListener("click", openMovementReady);
  els.movementBackToHome.addEventListener("click", () => showScreen("movementHome"));

  let movementTipsReturnFocus = null;
  function openMovementTips() { movementTipsReturnFocus = document.activeElement; els.movementTipsSheet.hidden = false; focusFirstIn(els.movementTipsSheet); }
  function closeMovementTips() { els.movementTipsSheet.hidden = true; if (movementTipsReturnFocus) movementTipsReturnFocus.focus(); }
  els.movementTipsBtn.addEventListener("click", openMovementTips);
  els.movementTipsCloseBtn.addEventListener("click", closeMovementTips);
  els.movementTipsSheet.addEventListener("click", (e) => { if (e.target === els.movementTipsSheet) closeMovementTips(); });
  els.movementTipsSheet.addEventListener("keydown", (e) => trapTabKey(els.movementTipsSheet, e));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !els.movementTipsSheet.hidden) closeMovementTips();
  });

  // ---- Movement session engine: a queue of upcoming movements, one made
  // active per beat. Two display modes: a sliding "lane" of `preview`
  // tiles (rebuilt each beat), or - when preview is "all" - the complete
  // sequence laid out once as a wrapping grid, where a beat just moves
  // which tile carries the "active" class. No audio: this runs purely on
  // the beat, per Fabian (a metronome, not an announcer). ----
  let movementRaf = null;
  let movementSession = null; // { sequence, beatLenS, totalBeats, startTime, lastBeatIdx, finishTimer }

  function pickRandomMovement(pool, avoidId) {
    let choice;
    do { choice = pool[Math.floor(Math.random() * pool.length)]; } while (pool.length > 1 && choice.id === avoidId);
    return choice;
  }
  function buildMovementSequence(pool, count) {
    const seq = [];
    let last = null;
    for (let i = 0; i < count; i++) {
      const m = pickRandomMovement(pool, last ? last.id : null);
      seq.push(m);
      last = m;
    }
    return seq;
  }
  function movementTileHTML(m, mirrored, showLabel) {
    const slots = resolveSlots([m], mirrored);
    return figureSVG(slots, "#16232a") + (showLabel ? `<span class="mv-label">${esc(m.label)}</span>` : "");
  }
  function renderMovementLaneWindow(seq, beatIdx, preview, mirrored, showLabel) {
    els.movementLane.className = "movement-lane";
    els.movementLane.innerHTML = "";
    for (let j = 0; j < preview; j++) {
      const m = seq[beatIdx + j];
      if (!m) continue;
      const tile = document.createElement("div");
      tile.className = "movement-tile" + (j === 0 ? " active" : " next");
      tile.innerHTML = movementTileHTML(m, mirrored, showLabel);
      els.movementLane.appendChild(tile);
    }
  }
  function buildMovementLaneGrid(seq, mirrored, showLabel) {
    els.movementLane.className = "movement-lane grid";
    els.movementLane.innerHTML = "";
    seq.forEach((m) => {
      const tile = document.createElement("div");
      tile.className = "movement-tile";
      tile.innerHTML = movementTileHTML(m, mirrored, showLabel);
      els.movementLane.appendChild(tile);
    });
  }
  function updateMovementLaneGrid(beatIdx) {
    const tiles = els.movementLane.children;
    for (let i = 0; i < tiles.length; i++) {
      tiles[i].classList.toggle("active", i === beatIdx);
      tiles[i].classList.toggle("done", i < beatIdx);
    }
    // At faster tempos or longer durations there are far more tiles than fit
    // on screen at once - without this, "Ganz" mode is unusable in practice
    // because nothing keeps the current step in view while you're moving.
    if (tiles[beatIdx]) tiles[beatIdx].scrollIntoView({ block: "nearest", inline: "nearest", behavior: "auto" });
  }

  function startMovementSession() {
    const pool = MOVEMENTS.filter((m) => movementPrefs.movements.includes(m.id));
    if (pool.length < MIN_MOVEMENTS) return;
    const beatLenS = 60 / movementPrefs.bpm;
    const totalBeats = Math.max(4, Math.round((movementPrefs.durationMin * 60) / beatLenS));
    const gridMode = movementPrefs.preview === "all";
    const seqCount = gridMode ? totalBeats : totalBeats + movementPrefs.preview - 1;
    const sequence = buildMovementSequence(pool, seqCount);
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.movementPlayer.hidden = false;
    els.movementPlayerBar.hidden = false;
    els.movementDonePanel.hidden = true;
    els.movementFinishBadge.hidden = true;
    els.movementProgressTrack.innerHTML = `<span class="seg"><span class="fill"></span></span>`;
    movementSession = { sequence, beatLenS, totalBeats, gridMode, startTime: performance.now(), lastBeatIdx: 0, finishTimer: null };
    if (gridMode) {
      buildMovementLaneGrid(sequence, movementPrefs.mirror, movementPrefs.showLabel);
      updateMovementLaneGrid(0);
    } else {
      renderMovementLaneWindow(sequence, 0, movementPrefs.preview, movementPrefs.mirror, movementPrefs.showLabel);
    }
    requestWakeLock();
    movementRaf = requestAnimationFrame(movementTick);
  }
  els.movementStartBtn.addEventListener("click", startMovementSession);

  // ---- Saved movement settings: same "save under a name, tap to reuse"
  // pattern as Kombi/Visual Training/Atemtraining. One flat list - there's
  // only one Movement mode, so no scoping needed. ----
  const MOVEMENT_SAVED_KEY = "fwmc-movement-saved-v1";
  const movementSavedStore = makePresetStore(MOVEMENT_SAVED_KEY);
  function renderMovementSaved() {
    renderPresetList(movementSavedStore, els.movementSavedList, els.movementSavedGroup, null,
      (e) => `${e.durationMin} Min · ${e.movements.length} Bewegungen · ${e.bpm} BPM`,
      (entry) => {
        movementPrefs.movements = entry.movements.slice();
        movementPrefs.preview = entry.preview;
        movementPrefs.bpm = entry.bpm;
        movementPrefs.durationMin = entry.durationMin;
        movementPrefs.mirror = entry.mirror;
        movementPrefs.showLabel = entry.showLabel;
        saveMovementPrefs();
        startMovementSession();
      });
  }
  wirePresetSaveForm({
    saveBtn: els.movementSaveBtn, form: els.movementSaveForm, nameInput: els.movementSaveNameInput,
    cancelBtn: els.movementSaveCancelBtn, confirmBtn: els.movementSaveConfirmBtn,
    defaultName: () => `Eigene Einstellung ${new Date().toLocaleDateString("de-DE")}`,
    onSave: (name) => {
      const list = movementSavedStore.load();
      list.push({
        id: String(Date.now()), name,
        movements: movementPrefs.movements.slice(), preview: movementPrefs.preview, bpm: movementPrefs.bpm,
        durationMin: movementPrefs.durationMin, mirror: movementPrefs.mirror, showLabel: movementPrefs.showLabel,
      });
      movementSavedStore.save(list);
      renderMovementSaved();
    },
  });

  function movementTick(now) {
    if (!movementSession) return;
    const elapsed = (now - movementSession.startTime) / 1000;
    const totalS = movementSession.totalBeats * movementSession.beatLenS;
    if (elapsed >= totalS) {
      // Keep the chart on screen with a "Fertig!" banner for a moment so
      // anyone who drifted off-beat sees the finish line, not a hard cut.
      // `movementSession` stays set (just no more raf frames) until the
      // timer below calls movementFinishSession, which reads it and clears it.
      els.movementFinishBadge.hidden = false;
      els.movementTimeEl.textContent = "0:00";
      movementSession.finishTimer = setTimeout(movementFinishSession, 1400);
      return;
    }
    const beatIdx = Math.min(Math.floor(elapsed / movementSession.beatLenS), movementSession.totalBeats - 1);
    if (beatIdx !== movementSession.lastBeatIdx) {
      movementSession.lastBeatIdx = beatIdx;
      if (movementSession.gridMode) updateMovementLaneGrid(beatIdx);
      else renderMovementLaneWindow(movementSession.sequence, beatIdx, movementPrefs.preview, movementPrefs.mirror, movementPrefs.showLabel);
    }
    els.movementTimeEl.textContent = fmtClock(totalS - elapsed);
    const fill = els.movementProgressTrack.querySelector(".fill");
    if (fill) fill.style.width = Math.min(100, (elapsed / totalS) * 100) + "%";
    movementRaf = requestAnimationFrame(movementTick);
  }

  function movementFinishSession() {
    const played = movementSession ? movementSession.totalBeats * movementSession.beatLenS : 0;
    movementSession = null;
    releaseWakeLock();
    els.movementFinishBadge.hidden = true;
    if (comboProgram) { advanceComboProgram(played); return; }
    els.movementPlayerBar.hidden = true;
    els.movementDoneSummary.textContent = `Ganzkörper-Reaktion · ${fmtMinutes(played)}`;
    const id = addHistory({ kind: "movement", title: "Ganzkörper-Reaktion", seconds: Math.round(played) });
    renderRating(els.movementRating, id, "Wie gut hast du mitgehalten?");
    els.movementDonePanel.hidden = false;
  }
  function movementLeavePlayer() {
    if (movementRaf) cancelAnimationFrame(movementRaf);
    movementRaf = null;
    if (movementSession && movementSession.finishTimer) clearTimeout(movementSession.finishTimer);
    movementSession = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.movementPlayer) document.exitFullscreen().catch(() => {});
    els.movementFsHint.hidden = true;
    els.movementFinishBadge.hidden = true;
    els.movementPlayer.hidden = true;
    els.movementDonePanel.hidden = true;
  }
  function movementAbort() {
    if (comboProgram) { movementLeavePlayer(); abortComboProgram(); return; }
    movementLeavePlayer();
    showScreen("movementReady");
  }
  els.movementBackBtn.addEventListener("click", movementAbort);
  els.movementAgainBtn.addEventListener("click", () => { movementLeavePlayer(); startMovementSession(); });
  els.movementDoneBackBtn.addEventListener("click", () => { movementLeavePlayer(); showScreen("movementHome"); });

  // ==== Workout engine ====
  // One engine serves three situations: a block inside a coach-authored/
  // self-built plan (workoutPlan set), a single block inside a cross-section
  // combo (comboProgram set), or a standalone quick Tabata run (neither
  // set). `onWorkoutBlockDone` is the single place that decides which of
  // those applies, so "reps" and "tabata" only ever report "this block is
  // done" and never need to know their own context.
  let workoutPlan = null; // { def, blockIndex, code, key, title, totalPlayedS }
  let workoutState = null; // running block state; shape depends on .kind
  let workoutRaf = null;
  let workoutRestTimer = null;
  let workoutTransitionTimer = null;
  let lastWorkoutPlan = null;
  let lastStandaloneWorkoutBlock = null;

  function runWorkoutBlock(block) {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.workoutPlayer.hidden = false;
    els.workoutPlayerBar.hidden = false;
    els.workoutDonePanel.hidden = true;
    const isTimed = block.kind === "tabata" || block.kind === "circuit";
    els.workoutRepsView.hidden = isTimed;
    els.workoutTabataView.hidden = !isTimed;
    els.workoutTabataView.classList.remove("phase-work", "phase-rest");
    renderWorkoutOverview();
    if (block.kind === "tabata") startTabataBlock(block);
    else if (block.kind === "circuit") startCircuitBlock(block);
    else startRepsBlock(block);
  }
  function renderWorkoutOverview() {
    if (!workoutPlan) { els.workoutOverview.hidden = true; return; }
    els.workoutOverview.hidden = false;
    els.workoutOverview.innerHTML = workoutPlan.def.blocks.map((b, i) => {
      const cls = i === workoutPlan.blockIndex ? "current" : i < workoutPlan.blockIndex ? "done" : "";
      return `<div class="workout-overview-row ${cls}"><span class="wo-num">${i + 1}</span><span>${esc(workoutBlockLabel(b))} · ${esc(workoutBlockMeta(b))}</span></div>`;
    }).join("");
  }

  // ---- Reps mode: manual "Satz erledigt", optional rest countdown ----
  function startRepsBlock(block) {
    const ex = findWorkoutExercise(block.exercise);
    workoutState = { kind: "reps", block, ex, setIndex: 1, startTime: performance.now() };
    renderRepsView();
    requestWakeLock();
  }
  function renderRepsView() {
    const { block, ex, setIndex } = workoutState;
    els.workoutExerciseName.textContent = ex.name;
    els.workoutSetInfo.textContent = `Satz ${setIndex} von ${block.sets}`;
    els.workoutRepsBig.textContent = `${block.reps} Wiederholungen`;
    els.workoutNote.textContent = block.note || ex.note || "";
    els.workoutSetDoneBtn.hidden = false;
    els.workoutRestBox.hidden = true;
  }
  els.workoutSetDoneBtn.addEventListener("click", () => {
    if (!workoutState || workoutState.kind !== "reps") return;
    if (workoutState.setIndex >= workoutState.block.sets) { finishWorkoutBlock(); return; }
    startRepsRest(workoutState.block.restS ?? 30);
  });
  function startRepsRest(restS) {
    els.workoutSetDoneBtn.hidden = true;
    els.workoutRestBox.hidden = false;
    let remaining = restS;
    const tick = () => {
      els.workoutRestCountdown.textContent = Math.max(0, Math.ceil(remaining));
      if (remaining <= 0) { advanceRepsSet(); return; }
      workoutRestTimer = setTimeout(() => { remaining -= 1; tick(); }, 1000);
    };
    tick();
  }
  function advanceRepsSet() {
    if (workoutRestTimer) clearTimeout(workoutRestTimer);
    workoutRestTimer = null;
    workoutState.setIndex += 1;
    renderRepsView();
  }
  els.workoutRestSkipBtn.addEventListener("click", () => advanceRepsSet());

  // ---- Tabata / circuit mode: a self-built sequence of one or several
  // exercises, each with its own work time, separated by a rest, the whole
  // sequence repeatable for several sets with a longer rest between sets.
  // A plain single-exercise "tabata" block (kind: "tabata", from an older
  // coach plan or a combo preset) is just a circuit with one item repeated
  // as "sets" - it's translated into that shape here so both kinds share
  // one engine, including the prev/restart/skip nav.
  //
  // Built as one flat, timed schedule up front (like the visual/breath
  // engines) rather than a phase-by-phase state machine, so pausing/
  // backgrounding compensation (see the shared visibilitychange handler)
  // works for free via workoutState.startTime, and jumping to a given
  // point is just moving that one timestamp.
  const TABATA_PREP_S = 5;
  function buildCircuitSchedule(block) {
    const schedule = [];
    let t = 0;
    schedule.push({ t0: t, t1: t + TABATA_PREP_S, type: "prep" });
    t += TABATA_PREP_S;
    for (let set = 1; set <= block.sets; set++) {
      block.items.forEach((item, i) => {
        schedule.push({ t0: t, t1: t + item.workS, type: "work", set, itemIdx: i, exercise: item.exercise, note: item.note });
        t += item.workS;
        if (i < block.items.length - 1) {
          schedule.push({ t0: t, t1: t + block.restS, type: "rest", set, itemIdx: i });
          t += block.restS;
        }
      });
      if (set < block.sets) {
        schedule.push({ t0: t, t1: t + block.setRestS, type: "setrest", set });
        t += block.setRestS;
      }
    }
    return { schedule, total: t };
  }
  function startCircuitBlock(block) {
    const built = buildCircuitSchedule(block);
    workoutState = { kind: "circuit", block, ex: { name: circuitSummaryLabel(block) }, schedule: built.schedule, total: built.total, startTime: performance.now() };
    requestWakeLock();
    workoutRaf = requestAnimationFrame(circuitTick);
  }
  function startTabataBlock(block) {
    const circuitBlock = { items: [{ exercise: block.exercise, workS: block.workS }], restS: 0, sets: block.rounds, setRestS: block.restS };
    const built = buildCircuitSchedule(circuitBlock);
    workoutState = { kind: "circuit", block: circuitBlock, ex: findWorkoutExercise(block.exercise), schedule: built.schedule, total: built.total, startTime: performance.now() };
    requestWakeLock();
    workoutRaf = requestAnimationFrame(circuitTick);
  }
  function circuitTick(now) {
    if (!workoutState || workoutState.kind !== "circuit") return;
    const elapsed = (now - workoutState.startTime) / 1000;
    if (elapsed >= workoutState.total) { finishWorkoutBlock(); return; }
    els.workoutTimeEl.textContent = fmtClock(workoutState.total - elapsed);
    const frame = workoutState.schedule.find((f) => elapsed >= f.t0 && elapsed < f.t1);
    if (frame) {
      const remain = frame.t1 - elapsed;
      const totalSets = workoutState.block.sets;
      const items = workoutState.block.items;
      const itemCount = items.length;
      const single = itemCount === 1; // an old-style single-exercise tabata block, shown as "Runde" not "Satz/Übung"
      els.tabataCountdown.textContent = Math.max(0, Math.ceil(remain));
      els.workoutTabataView.classList.remove("phase-work", "phase-rest");
      const showExercise = (id, note) => {
        const ex = findWorkoutExercise(id);
        els.tabataExerciseName.textContent = ex.name;
        els.tabataExerciseIcon.innerHTML = workoutIconSVG(ex.icon);
        els.tabataExerciseNote.textContent = [ex.note, note].filter(Boolean).join(" · ");
      };
      if (frame.type === "prep") {
        showExercise(items[0].exercise, items[0].note);
        els.tabataPhaseLabel.textContent = "Bereit machen";
        els.tabataRoundLabel.textContent = single ? `Runde 1 von ${totalSets}` : `Satz 1 von ${totalSets} · Übung 1 von ${itemCount}`;
      } else if (frame.type === "work") {
        showExercise(frame.exercise, frame.note);
        els.tabataPhaseLabel.textContent = "Los!";
        els.tabataRoundLabel.textContent = single ? `Runde ${frame.set} von ${totalSets}` : `Satz ${frame.set} von ${totalSets} · Übung ${frame.itemIdx + 1} von ${itemCount}`;
        els.workoutTabataView.classList.add("phase-work");
      } else if (frame.type === "rest") {
        const nextItem = items[frame.itemIdx + 1];
        if (nextItem) showExercise(nextItem.exercise, nextItem.note);
        els.tabataPhaseLabel.textContent = "Pause";
        els.tabataRoundLabel.textContent = `Satz ${frame.set} von ${totalSets} · gleich: Übung ${frame.itemIdx + 2} von ${itemCount}`;
        els.workoutTabataView.classList.add("phase-rest");
      } else if (frame.type === "setrest") {
        showExercise(items[0].exercise, items[0].note);
        els.tabataPhaseLabel.textContent = "Satzpause";
        els.tabataRoundLabel.textContent = single ? `Runde ${frame.set + 1} von ${totalSets} beginnt gleich` : `Satz ${frame.set + 1} von ${totalSets} beginnt gleich`;
        els.workoutTabataView.classList.add("phase-rest");
      }
    }
    workoutRaf = requestAnimationFrame(circuitTick);
  }

  // ---- Skip back/restart/forward through the exercises, like the visual
  // player's live-nav. Jumping just moves workoutState.startTime so the
  // next tick's elapsed-time lookup lands on the target exercise's frame.
  function circuitWorkFrames() {
    return workoutState.schedule.filter((f) => f.type === "work");
  }
  function circuitCurrentWorkIndex() {
    const frames = circuitWorkFrames();
    const elapsed = (performance.now() - workoutState.startTime) / 1000;
    let idx = 0;
    for (let i = 0; i < frames.length; i++) if (frames[i].t0 <= elapsed) idx = i;
    return idx;
  }
  function circuitJumpToWorkIndex(idx) {
    if (!workoutState || workoutState.kind !== "circuit") return;
    const frames = circuitWorkFrames();
    if (idx >= frames.length) { finishWorkoutBlock(); return; }
    const targetT = frames[Math.max(0, idx)].t0;
    workoutState.startTime = performance.now() - targetT * 1000;
  }
  els.tabataPrevBtn.addEventListener("click", () => circuitJumpToWorkIndex(circuitCurrentWorkIndex() - 1));
  els.tabataRestartBtn.addEventListener("click", () => circuitJumpToWorkIndex(circuitCurrentWorkIndex()));
  els.tabataSkipBtn.addEventListener("click", () => circuitJumpToWorkIndex(circuitCurrentWorkIndex() + 1));

  // ---- Shared block completion ----
  function finishWorkoutBlock() {
    if (workoutRaf) cancelAnimationFrame(workoutRaf);
    workoutRaf = null;
    if (workoutRestTimer) clearTimeout(workoutRestTimer);
    workoutRestTimer = null;
    const st = workoutState;
    const played = st ? (performance.now() - (st.sessionStart || st.startTime)) / 1000 : 0;
    workoutState = null;
    onWorkoutBlockDone(played, st ? st.ex : null);
  }
  function onWorkoutBlockDone(playedS, ex) {
    releaseWakeLock();
    if (workoutPlan) {
      workoutPlan.totalPlayedS += playedS;
      const next = workoutPlan.blockIndex + 1;
      if (next >= workoutPlan.def.blocks.length) { finishWorkoutPlan(); return; }
      showWorkoutTransition(workoutPlan.def.blocks[next], () => startWorkoutPlanBlock(next));
      return;
    }
    if (comboProgram) { advanceComboProgram(playedS); return; }
    els.workoutPlayerBar.hidden = true;
    els.workoutDoneSummary.textContent = `${ex ? ex.name : "Training"} · ${fmtMinutes(playedS)}`;
    const id = addHistory({ kind: "workout", title: ex ? ex.name : "Workout", seconds: Math.round(playedS) });
    renderRating(els.workoutRating, id, "Wie gut hast du durchgehalten?");
    els.workoutDonePanel.hidden = false;
  }

  function startWorkoutPlanBlock(idx) {
    if (!workoutPlan) return;
    if (idx >= workoutPlan.def.blocks.length) { finishWorkoutPlan(); return; }
    workoutPlan.blockIndex = idx;
    runWorkoutBlock(workoutPlan.def.blocks[idx]);
  }
  function showWorkoutTransition(nextBlock, onContinue) {
    hideAllPlayers();
    els.workoutTransitionTitle.textContent = workoutBlockLabel(nextBlock);
    els.workoutTransitionMeta.textContent = workoutBlockMeta(nextBlock);
    els.workoutTransition.hidden = false;
    if (workoutTransitionTimer) clearTimeout(workoutTransitionTimer);
    const go = () => { if (workoutTransitionTimer) clearTimeout(workoutTransitionTimer); els.workoutTransition.hidden = true; onContinue(); };
    els.workoutTransitionBtn.onclick = go;
    workoutTransitionTimer = setTimeout(go, 4000);
  }
  function finishWorkoutPlan() {
    hideAllPlayers();
    const played = workoutPlan.totalPlayedS;
    const title = workoutPlan.title;
    els.workoutProgramDoneSummary.textContent = `${exerciseCountLabel(workoutPlan.def.blocks.length)} · ${fmtMinutes(played)} Training`;
    const id = addHistory({ kind: "workout-plan", title, progKey: workoutPlan.key, seconds: Math.round(played) });
    renderRating(els.workoutProgramRating, id, "Wie gut hast du durchgehalten?");
    els.workoutProgramDoneBackBtn.textContent = workoutOriginBundle ? "Zurück zu meinen Plänen" : "Zur Startseite";
    els.workoutProgramDonePanel.hidden = false;
    lastWorkoutPlan = workoutPlan;
    workoutPlan = null;
  }
  els.workoutProgramAgainBtn.addEventListener("click", () => {
    if (!lastWorkoutPlan) return;
    els.workoutProgramDonePanel.hidden = true;
    workoutPlan = { ...lastWorkoutPlan, blockIndex: 0, totalPlayedS: 0 };
    startWorkoutPlanBlock(0);
  });
  els.workoutProgramDoneBackBtn.addEventListener("click", () => {
    els.workoutProgramDonePanel.hidden = true;
    if (workoutOriginBundle) openWorkoutBundleOverview(workoutOriginBundle.def, workoutOriginBundle.code);
    else showScreen("workoutHome");
  });

  function workoutLeavePlayer() {
    if (workoutRaf) cancelAnimationFrame(workoutRaf);
    workoutRaf = null;
    if (workoutRestTimer) clearTimeout(workoutRestTimer);
    workoutRestTimer = null;
    if (workoutTransitionTimer) clearTimeout(workoutTransitionTimer);
    workoutTransitionTimer = null;
    workoutState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.workoutPlayer) document.exitFullscreen().catch(() => {});
    els.workoutFsHint.hidden = true;
    els.workoutPlayer.hidden = true;
    els.workoutDonePanel.hidden = true;
    els.workoutTransition.hidden = true;
  }
  function workoutAbort() {
    if (comboProgram) { workoutLeavePlayer(); abortComboProgram(); return; }
    const wasPlan = !!workoutPlan;
    workoutPlan = null;
    workoutLeavePlayer();
    showScreen(wasPlan ? "workoutProgramIntro" : "workoutTabataReady");
  }
  els.workoutBackBtn.addEventListener("click", workoutAbort);
  els.workoutAgainBtn.addEventListener("click", () => {
    if (!lastStandaloneWorkoutBlock) return;
    workoutLeavePlayer();
    startStandaloneWorkoutBlock(lastStandaloneWorkoutBlock);
  });
  els.workoutDoneBackBtn.addEventListener("click", () => { workoutLeavePlayer(); showScreen("workoutHome"); });

  function startStandaloneWorkoutBlock(block) {
    workoutPlan = null;
    lastStandaloneWorkoutBlock = block;
    runWorkoutBlock(block);
  }

  // ---- Standalone Tabata/circuit quick-start (no plan, no code): the
  // client builds their own sequence of exercises (tap to append, tap the
  // same one again for a duplicate later in the sequence), each with its
  // own work time, then sets how many sets to repeat and the rests. Mirrors
  // the combo builder's add-grid/draft-list pattern.
  const WORKOUT_CIRCUIT_KEY = "fwmc-workout-circuit-v1";
  const workoutCircuitPrefs = { items: [], restS: 10, sets: 1, setRestS: 30, defaultWorkS: 15 };
  function loadWorkoutCircuitPrefs() {
    const saved = readJSON(WORKOUT_CIRCUIT_KEY, null);
    if (saved && typeof saved === "object") Object.assign(workoutCircuitPrefs, saved);
    if (!Array.isArray(workoutCircuitPrefs.items)) workoutCircuitPrefs.items = [];
  }
  function saveWorkoutCircuitPrefs() { writeJSON(WORKOUT_CIRCUIT_KEY, workoutCircuitPrefs); }
  loadWorkoutCircuitPrefs();

  function renderWorkoutCircuitAddGrid() {
    els.workoutCircuitAddGrid.innerHTML = "";
    allWorkoutExerciseEntries().forEach(([id, ex]) => {
      const isCustom = !WORKOUT_EXERCISES[id];
      const count = workoutCircuitPrefs.items.filter((it) => it.exercise === id).length;
      const wrap = document.createElement("div");
      wrap.className = "custom-exercise-add-row";
      const btn = document.createElement("button");
      btn.className = "combo-add-btn";
      btn.innerHTML = `<span class="ca-icon">${workoutIconSVG(ex.icon)}</span>` +
        `<span class="ca-text"><span class="ca-title">${esc(ex.name)}</span>` +
        (count ? `<br><span class="ca-meta">${count}× im Zirkel</span>` : "") + `</span><span class="ca-plus">+</span>`;
      btn.addEventListener("click", () => {
        workoutCircuitPrefs.items.push({ exercise: id, workS: workoutCircuitPrefs.defaultWorkS, note: "" });
        saveWorkoutCircuitPrefs();
        renderWorkoutCircuitAddGrid();
        renderWorkoutCircuitList();
        syncWorkoutCircuitUI();
      });
      wrap.appendChild(btn);
      if (isCustom) {
        const rm = document.createElement("button");
        rm.className = "combo-block-remove";
        rm.title = "Eigene Übung löschen";
        rm.textContent = "✕";
        rm.addEventListener("click", () => {
          customWorkoutExercises = customWorkoutExercises.filter((c) => c.id !== id);
          saveCustomWorkoutExercises(customWorkoutExercises);
          renderWorkoutCircuitAddGrid();
        });
        wrap.appendChild(rm);
      }
      els.workoutCircuitAddGrid.appendChild(wrap);
    });
  }
  function renderWorkoutCircuitList() {
    const items = workoutCircuitPrefs.items;
    els.workoutCircuitCount.textContent = items.length ? `${items.length} Übung${items.length === 1 ? "" : "en"}` : "";
    els.workoutCircuitEmptyHint.hidden = items.length > 0;
    els.workoutCircuitList.innerHTML = "";
    items.forEach((item, i) => {
      const ex = findWorkoutExercise(item.exercise);
      const row = document.createElement("div");
      row.className = "circuit-item-row";
      row.innerHTML =
        `<div class="circuit-item-main">` +
        `<span class="chapter-main" style="cursor:default"><span class="num">${i + 1}</span><span class="ca-icon">${workoutIconSVG(ex.icon)}</span><span class="info"><strong>${esc(ex.name)}</strong></span></span>` +
        `<div class="circuit-duration">` +
        `<button class="circuit-step" data-i="${i}" data-dir="-1" aria-label="kürzer">&minus;</button>` +
        `<span class="circuit-duration-value">${item.workS}s</span>` +
        `<button class="circuit-step" data-i="${i}" data-dir="1" aria-label="länger">+</button>` +
        `</div>` +
        `<button class="combo-block-remove" data-i="${i}" title="Entfernen">&#10005;</button>` +
        `</div>` +
        `<input type="text" class="circuit-item-note" data-i="${i}" placeholder="Eigene Notiz für diese Übung (optional)" maxlength="80" value="${esc(item.note || "")}">`;
      els.workoutCircuitList.appendChild(row);
    });
    els.workoutCircuitList.querySelectorAll(".circuit-step").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = workoutCircuitPrefs.items[Number(btn.dataset.i)];
        item.workS = Math.max(5, Math.min(120, item.workS + Number(btn.dataset.dir) * 5));
        saveWorkoutCircuitPrefs();
        renderWorkoutCircuitList();
      });
    });
    els.workoutCircuitList.querySelectorAll(".combo-block-remove").forEach((btn) => {
      btn.addEventListener("click", () => {
        workoutCircuitPrefs.items.splice(Number(btn.dataset.i), 1);
        saveWorkoutCircuitPrefs();
        renderWorkoutCircuitAddGrid();
        renderWorkoutCircuitList();
        syncWorkoutCircuitUI();
      });
    });
    els.workoutCircuitList.querySelectorAll(".circuit-item-note").forEach((input) => {
      input.addEventListener("change", () => {
        workoutCircuitPrefs.items[Number(input.dataset.i)].note = input.value.trim();
        saveWorkoutCircuitPrefs();
      });
    });
  }
  // ---- Custom exercises: name + optional note, reusable like a built-in ----
  function openWorkoutCircuitCustomForm() {
    els.workoutCircuitCustomForm.hidden = false;
    els.workoutCircuitAddCustomBtn.hidden = true;
    els.workoutCircuitCustomName.value = "";
    els.workoutCircuitCustomNote.value = "";
    els.workoutCircuitCustomName.focus();
  }
  function closeWorkoutCircuitCustomForm() {
    els.workoutCircuitCustomForm.hidden = true;
    els.workoutCircuitAddCustomBtn.hidden = false;
  }
  els.workoutCircuitAddCustomBtn.addEventListener("click", openWorkoutCircuitCustomForm);
  els.workoutCircuitCustomCancelBtn.addEventListener("click", closeWorkoutCircuitCustomForm);
  els.workoutCircuitCustomSaveBtn.addEventListener("click", () => {
    const name = els.workoutCircuitCustomName.value.trim();
    if (!name) { els.workoutCircuitCustomName.focus(); return; }
    const note = els.workoutCircuitCustomNote.value.trim();
    customWorkoutExercises.push({ id: `custom-${Date.now()}`, name, note, icon: "custom" });
    saveCustomWorkoutExercises(customWorkoutExercises);
    closeWorkoutCircuitCustomForm();
    renderWorkoutCircuitAddGrid();
  });
  document.querySelectorAll("[data-wo-rest]").forEach((el) => el.addEventListener("click", () => {
    workoutCircuitPrefs.restS = Number(el.dataset.woRest); saveWorkoutCircuitPrefs(); syncWorkoutCircuitUI();
  }));
  document.querySelectorAll("[data-wo-sets]").forEach((el) => el.addEventListener("click", () => {
    workoutCircuitPrefs.sets = Number(el.dataset.woSets); saveWorkoutCircuitPrefs(); syncWorkoutCircuitUI();
  }));
  document.querySelectorAll("[data-wo-setrest]").forEach((el) => el.addEventListener("click", () => {
    workoutCircuitPrefs.setRestS = Number(el.dataset.woSetrest); saveWorkoutCircuitPrefs(); syncWorkoutCircuitUI();
  }));
  function syncWorkoutCircuitUI() {
    document.querySelectorAll("[data-wo-rest]").forEach((el) => setActive(el, Number(el.dataset.woRest) === workoutCircuitPrefs.restS));
    document.querySelectorAll("[data-wo-sets]").forEach((el) => setActive(el, Number(el.dataset.woSets) === workoutCircuitPrefs.sets));
    document.querySelectorAll("[data-wo-setrest]").forEach((el) => setActive(el, Number(el.dataset.woSetrest) === workoutCircuitPrefs.setRestS));
    els.workoutCircuitSetRestGroup.hidden = workoutCircuitPrefs.sets <= 1;
    els.workoutCircuitDefaultWorkSlider.value = workoutCircuitPrefs.defaultWorkS;
    els.workoutCircuitDefaultWorkValue.textContent = `${workoutCircuitPrefs.defaultWorkS} s`;
    els.workoutTabataStartBtn.disabled = workoutCircuitPrefs.items.length === 0;
    els.workoutTabataStartBtn.textContent = workoutCircuitPrefs.items.length ? "Zirkel starten" : "Mindestens eine Übung hinzufügen";
  }
  els.workoutCircuitDefaultWorkSlider.addEventListener("input", () => {
    workoutCircuitPrefs.defaultWorkS = Number(els.workoutCircuitDefaultWorkSlider.value);
    saveWorkoutCircuitPrefs();
    syncWorkoutCircuitUI();
  });
  function openWorkoutTabataReady() {
    closeWorkoutCircuitCustomForm();
    renderWorkoutCircuitAddGrid();
    renderWorkoutCircuitList();
    syncWorkoutCircuitUI();
    els.workoutCircuitSaveForm.hidden = true;
    els.workoutCircuitSaveBtn.hidden = false;
    renderWorkoutCircuitSaved();
    showScreen("workoutTabataReady");
  }
  els.workoutTabataStartCard.addEventListener("click", openWorkoutTabataReady);
  els.workoutTabataBackToHome.addEventListener("click", () => showScreen("workoutHome"));
  function startWorkoutCircuitNow() {
    if (!workoutCircuitPrefs.items.length) return;
    startStandaloneWorkoutBlock({
      kind: "circuit",
      items: workoutCircuitPrefs.items.map((it) => ({ ...it })),
      restS: workoutCircuitPrefs.restS,
      sets: workoutCircuitPrefs.sets,
      setRestS: workoutCircuitPrefs.setRestS,
    });
  }
  els.workoutTabataStartBtn.addEventListener("click", startWorkoutCircuitNow);

  // ---- Saved workout circuits: same "save under a name, tap to reuse"
  // pattern as Kombi/Visual Training/Atemtraining/Movement. One flat list -
  // there's only one circuit builder, so no scoping needed. ----
  const WORKOUT_CIRCUIT_SAVED_KEY = "fwmc-workout-circuit-saved-v1";
  const workoutCircuitSavedStore = makePresetStore(WORKOUT_CIRCUIT_SAVED_KEY);
  function renderWorkoutCircuitSaved() {
    renderPresetList(workoutCircuitSavedStore, els.workoutCircuitSavedList, els.workoutCircuitSavedGroup, null,
      (e) => `${e.items.length} Übung${e.items.length === 1 ? "" : "en"} · ${e.sets} Satz${e.sets === 1 ? "" : "e"}`,
      (entry) => {
        workoutCircuitPrefs.items = entry.items.map((it) => ({ ...it }));
        workoutCircuitPrefs.restS = entry.restS;
        workoutCircuitPrefs.sets = entry.sets;
        workoutCircuitPrefs.setRestS = entry.setRestS;
        saveWorkoutCircuitPrefs();
        startWorkoutCircuitNow();
      });
  }
  wirePresetSaveForm({
    saveBtn: els.workoutCircuitSaveBtn, form: els.workoutCircuitSaveForm, nameInput: els.workoutCircuitSaveNameInput,
    cancelBtn: els.workoutCircuitSaveCancelBtn, confirmBtn: els.workoutCircuitSaveConfirmBtn,
    defaultName: () => `Eigener Zirkel ${new Date().toLocaleDateString("de-DE")}`,
    onSave: (name) => {
      const list = workoutCircuitSavedStore.load();
      list.push({
        id: String(Date.now()), name,
        items: workoutCircuitPrefs.items.map((it) => ({ ...it })),
        restS: workoutCircuitPrefs.restS, sets: workoutCircuitPrefs.sets, setRestS: workoutCircuitPrefs.setRestS,
      });
      workoutCircuitSavedStore.save(list);
      renderWorkoutCircuitSaved();
    },
  });

  // ==== Cross-section combo programmes ====
  let comboProgram = null; // { def, blockIndex, code, key, title, totalPlayedS }
  let comboOriginBundle = null; // { def, code } - set when opened from a combo-bundle code
  let comboReturnScreen = "home";
  let comboTransitionTimer = null;
  let lastComboProgram = null;

  function currentHomeScreen() {
    const active = document.querySelector(".section-tab.active");
    const sec = active ? active.dataset.section : "visual";
    return sec === "breath" ? "breathHome" : sec === "movement" ? "movementHome" : sec === "workout" ? "workoutHome" : "home";
  }

  function startComboProgram(def, code, key, fallbackReturnScreen) {
    comboReturnScreen = fallbackReturnScreen || "home";
    comboProgram = { def, blockIndex: 0, code, key, title: def.name || "Dein Programm", totalPlayedS: 0 };
    startComboBlock(0);
  }
  function startComboBlock(idx) {
    if (!comboProgram) return;
    if (idx >= comboProgram.def.blocks.length) { finishComboProgram(); return; }
    comboProgram.blockIndex = idx;
    const block = comboProgram.def.blocks[idx];
    if (block.domain === "wimhof") {
      // Safety first, always: even inside a combo, Wim-Hof-style breathing
      // stops on its own settings screen so the safety checkbox is never
      // skipped. wimhofFinish already checks comboProgram to continue on.
      wimhofSettings.breaths = block.breaths ?? WIMHOF_DEFAULTS.breaths;
      wimhofSettings.rounds = block.rounds ?? WIMHOF_DEFAULTS.rounds;
      wimhofSettings.breathPaceS = block.breathPaceS ?? WIMHOF_DEFAULTS.breathPaceS;
      wimhofSettings.recoveryHoldS = block.recoveryHoldS ?? WIMHOF_DEFAULTS.recoveryHoldS;
      hideAllPlayers();
      openWimhofReady();
    } else if (block.domain === "breath") {
      breathPatternKey = block.pattern;
      breathWorking = block.phases ? { ...block.phases } : { ...(BREATH_PATTERNS[block.pattern].phases || breathPrefs.custom) };
      breathPrefs.durationMin = block.durationMin ?? 5;
      breathPrefs.sound = block.sound !== false;
      startBreathSession();
    } else if (block.domain === "movement") {
      if (block.movements) movementPrefs.movements = block.movements;
      movementPrefs.preview = block.preview ?? movementPrefs.preview;
      movementPrefs.bpm = block.bpm ?? movementPrefs.bpm;
      movementPrefs.durationMin = block.durationMin ?? 2;
      movementPrefs.mirror = block.mirror ?? movementPrefs.mirror;
      movementPrefs.showLabel = block.showLabel ?? movementPrefs.showLabel;
      startMovementSession();
    } else if (block.domain === "visual") {
      program = null;
      state.exercise = block.exercise;
      if (block.colors && EXERCISES[block.exercise].usesColors) state.colors = block.colors;
      state.duration = block.duration ?? 60;
      state.stimulusS = block.stimulusS ?? 1.5;
      state.intervalMin = block.intervalMin ?? 3;
      state.intervalMax = block.intervalMax ?? 6;
        active = { colors: keysToColors(state.colors) };
      startSession();
    } else if (block.domain === "workout") {
      workoutPlan = null;
      runWorkoutBlock(block);
    } else {
      startComboBlock(idx + 1); // unknown domain - skip rather than get stuck
    }
  }
  function showComboTransition(nextBlock, onContinue) {
    hideAllPlayers();
    els.comboTransitionTitle.textContent = comboBlockLabel(nextBlock);
    els.comboTransitionMeta.textContent = comboBlockMeta(nextBlock);
    els.comboTransition.hidden = false;
    if (comboTransitionTimer) clearTimeout(comboTransitionTimer);
    const go = () => { if (comboTransitionTimer) clearTimeout(comboTransitionTimer); els.comboTransition.hidden = true; onContinue(); };
    els.comboTransitionBtn.onclick = go;
    comboTransitionTimer = setTimeout(go, 4000);
  }
  function advanceComboProgram(playedS) {
    if (!comboProgram) return;
    comboProgram.totalPlayedS += playedS;
    const nextIdx = comboProgram.blockIndex + 1;
    if (nextIdx >= comboProgram.def.blocks.length) { finishComboProgram(); return; }
    showComboTransition(comboProgram.def.blocks[nextIdx], () => startComboBlock(nextIdx));
  }
  function finishComboProgram() {
    hideAllPlayers();
    const played = comboProgram.totalPlayedS;
    const title = comboProgram.title;
    const key = comboProgram.key;
    els.comboDoneSummary.textContent = `${exerciseCountLabel(comboProgram.def.blocks.length)} · ${fmtMinutes(played)} Training`;
    const id = addHistory({ kind: "combo", title, progKey: key, seconds: Math.round(played) });
    renderRating(els.comboRating, id, "Wie fühlst du dich nach dem Programm?");
    els.comboDoneBackBtn.textContent = comboOriginBundle ? "Zurück zu meinen Programmen" : "Zurück";
    els.comboDonePanel.hidden = false;
    lastComboProgram = comboProgram;
    comboProgram = null;
  }
  function abortComboProgram() {
    hideAllPlayers();
    comboProgram = null;
    showScreen(comboReturnScreen);
  }
  els.comboAgainBtn.addEventListener("click", () => {
    if (!lastComboProgram) return;
    els.comboDonePanel.hidden = true;
    comboProgram = { ...lastComboProgram, blockIndex: 0, totalPlayedS: 0 };
    startComboBlock(0);
  });
  els.comboDoneBackBtn.addEventListener("click", () => {
    els.comboDonePanel.hidden = true;
    if (comboOriginBundle) { openComboBundleOverview(comboOriginBundle.def, comboOriginBundle.code); comboOriginBundle = null; }
    else showScreen(comboReturnScreen);
  });

  function openComboBundleOverview(bundleDef, code) {
    els.comboBundleTitle.textContent = bundleDef.name || "Deine Programme";
    els.comboBundleList.innerHTML = "";
    const sorted = bundleDef.programs
      .map((p, i) => ({ p, i }))
      .sort((a, b) => (b.p.createdAt || "").localeCompare(a.p.createdAt || "") || (a.i - b.i));
    sorted.forEach(({ p, i }, pos) => {
      const key = `combo:${code}#${i}`;
      const done = isCompleted(key);
      const isNew = pos === 0 && sorted.length > 1 && p.createdAt;
      const item = document.createElement("button");
      item.className = "bundle-item";
      const dateLabel = formatDateDE(p.createdAt);
      const badges = (isNew ? `<span class="badge badge-new">Neu</span>` : "") + (done ? `<span class="badge badge-done">&#10003; Erledigt</span>` : "");
      item.innerHTML =
        `<div class="bundle-item-head"><strong>${esc(p.label || ("Programm " + (i + 1)))}</strong>${dateLabel ? `<span class="bundle-date">${dateLabel}</span>` : ""}</div>` +
        (badges ? `<div class="badges">${badges}</div>` : "") +
        `<span class="bundle-meta">${exerciseCountLabel(p.blocks.length)} · ca. ${fmtMinutes(p.blocks.reduce((s, b) => s + comboBlockSeconds(b), 0))}</span>` +
        (p.description ? `<span class="bundle-desc">${esc(p.description)}</span>` : "");
      item.addEventListener("click", () => {
        comboOriginBundle = { def: bundleDef, code };
        startComboProgram(p, code, key, currentHomeScreen());
      });
      els.comboBundleList.appendChild(item);
    });
    showScreen("comboBundleOverview");
  }
  els.comboBundleBackToHome.addEventListener("click", () => { comboOriginBundle = null; showScreen(currentHomeScreen()); });

  // ---- Self-service builder: pick preset blocks from any section, order
  // them, then start right away or save locally under a name for later. ----
  const COMBO_SAVED_KEY = "fwmc-combo-saved-v1";
  function loadSavedCombos() { const l = readJSON(COMBO_SAVED_KEY, []); return Array.isArray(l) ? l : []; }
  function saveSavedCombos(list) { writeJSON(COMBO_SAVED_KEY, list); }

  let comboDraftBlocks = [];
  function renderComboAddGrid() {
    els.comboAddGrid.innerHTML = "";
    Object.entries(COMBO_PRESETS).forEach(([domain, presets]) => {
      const group = document.createElement("div");
      group.className = "combo-domain-group";
      group.innerHTML = `<div class="combo-domain-title">${esc(COMBO_DOMAIN_TITLE[domain])}</div>`;
      const opts = document.createElement("div");
      opts.className = "combo-domain-options";
      presets.forEach((preset) => {
        const btn = document.createElement("button");
        btn.className = "combo-add-btn";
        btn.innerHTML = `<span><span class="ca-title">${esc(comboBlockLabel(preset))}</span><br><span class="ca-meta">${esc(comboBlockMeta(preset))}</span></span><span class="ca-plus">+</span>`;
        btn.addEventListener("click", () => { comboDraftBlocks.push({ ...preset }); renderComboBlockList(); });
        opts.appendChild(btn);
      });
      group.appendChild(opts);
      els.comboAddGrid.appendChild(group);
    });
  }
  function renderComboBlockList() {
    els.comboBlockCount.textContent = comboDraftBlocks.length ? `${comboDraftBlocks.length} Baustein${comboDraftBlocks.length === 1 ? "" : "e"}` : "";
    els.comboEmptyHint.hidden = comboDraftBlocks.length > 0;
    els.comboBlockList.innerHTML = "";
    comboDraftBlocks.forEach((block, i) => {
      const row = document.createElement("div");
      row.className = "chapter-row";
      const main = document.createElement("span");
      main.className = "chapter-main";
      main.style.cursor = "default";
      main.innerHTML = `<span class="num">${i + 1}</span><span class="info"><strong>${esc(comboBlockLabel(block))}</strong><span>${esc(comboBlockMeta(block))}</span></span>`;
      row.appendChild(main);
      const rm = document.createElement("button");
      rm.className = "combo-block-remove";
      rm.textContent = "✕";
      rm.title = "Entfernen";
      rm.addEventListener("click", () => { comboDraftBlocks.splice(i, 1); renderComboBlockList(); });
      row.appendChild(rm);
      els.comboBlockList.appendChild(row);
    });
  }
  function renderComboSaved() {
    const saved = loadSavedCombos();
    els.comboSavedGroup.hidden = saved.length === 0;
    els.comboSavedList.innerHTML = "";
    saved.slice().reverse().forEach((entry) => {
      const item = document.createElement("button");
      item.className = "bundle-item";
      item.innerHTML =
        `<div class="bundle-item-head"><strong>${esc(entry.name)}</strong></div>` +
        `<span class="bundle-meta">${exerciseCountLabel(entry.blocks.length)} · ca. ${fmtMinutes(entry.blocks.reduce((s, b) => s + comboBlockSeconds(b), 0))}</span>`;
      item.addEventListener("click", () => {
        comboOriginBundle = null;
        startComboProgram({ name: entry.name, blocks: entry.blocks }, "local", "local:" + entry.id, currentHomeScreen());
      });
      els.comboSavedList.appendChild(item);
    });
  }
  function openComboScreen() {
    comboDraftBlocks = [];
    els.comboNameInput.value = "";
    renderComboAddGrid();
    renderComboBlockList();
    renderComboSaved();
    showScreen("comboScreen");
  }
  els.comboBackToHome.addEventListener("click", () => showScreen(currentHomeScreen()));
  function comboDraftName() {
    return (els.comboNameInput.value || "").trim() || `Programm ${new Date().toLocaleDateString("de-DE")}`;
  }
  els.comboStartBtn.addEventListener("click", () => {
    if (comboDraftBlocks.length === 0) return;
    comboOriginBundle = null;
    startComboProgram({ name: comboDraftName(), blocks: comboDraftBlocks.slice() }, "local", "local:draft", currentHomeScreen());
  });
  els.comboSaveBtn.addEventListener("click", () => {
    if (comboDraftBlocks.length === 0) return;
    const saved = loadSavedCombos();
    saved.push({ id: String(Date.now()), name: comboDraftName(), blocks: comboDraftBlocks.slice(), createdAt: new Date().toISOString() });
    saveSavedCombos(saved);
    renderComboSaved();
    els.comboNameInput.value = "";
    comboDraftBlocks = [];
    renderComboBlockList();
  });

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
