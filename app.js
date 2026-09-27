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
  // The three pure-arrow exercises (4 gerade, 4 diagonal, 8 Pfeile) pick
  // their arrow colour from a separately stored selection, with a much
  // looser range than VT/VRW's 2-4 (down to a single colour, up to all of
  // COLOR_LIB) plus an "alle Farben" shortcut - see the colour-picker code
  // below.
  const ARROW_MIN_COLORS = 1;
  const ARROW_MAX_COLORS = COLOR_LIB.length;

  // Stroop uses the same colour picker again, but with Schwarz/Weiß added on
  // top of COLOR_LIB - "the colour word isn't the ink colour" reads better
  // with black/white in the mix, and unlike VT/arrows there's no physical
  // hütchen to match, so any colour is fair game. Needs at least two colours
  // to have a word/ink mismatch at all.
  const STROOP_EXTRA_COLORS = [
    { key: "schwarz", name: "Schwarz", hex: "#000000" },
    { key: "weiss", name: "Weiß", hex: "#ffffff" },
  ];
  const STROOP_COLOR_LIB = [...COLOR_LIB, ...STROOP_EXTRA_COLORS];
  const STROOP_COLOR_BY_KEY = Object.fromEntries(STROOP_COLOR_LIB.map((c) => [c.key, c]));
  const STROOP_MIN_COLORS = 2;
  const STROOP_MAX_COLORS = STROOP_COLOR_LIB.length;

  // Single-select colour for the centre fixation point (Periphere
  // Wahrnehmung's own Feineinstellung) - "Grau" is the plain default dot
  // every other exercise still uses, plus every Stroop colour on top.
  const FIX_COLOR_LIB = [{ key: "grau", name: "Grau", hex: DOT }, ...STROOP_COLOR_LIB];
  const FIX_COLOR_BY_KEY = Object.fromEntries(FIX_COLOR_LIB.map((c) => [c.key, c]));

  // 3x3 field split for Periphere Wahrnehmung's "Eigene Auswahl" mode - the
  // centre cell is where the fixation point already sits, so it's not a
  // selectable zone.
  const PERIPH_ZONES = {
    tl: { row: 0, col: 0 }, tm: { row: 0, col: 1 }, tr: { row: 0, col: 2 },
    ml: { row: 1, col: 0 },                          mr: { row: 1, col: 2 },
    bl: { row: 2, col: 0 }, bm: { row: 2, col: 1 }, br: { row: 2, col: 2 },
  };
  const PERIPH_ZONE_KEYS = Object.keys(PERIPH_ZONES);
  const PERIPH_AXIS_KEYS = ["horizontal", "vertikal", "diagonal"];

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
  function keysToColors(keys, lib = COLOR_LIB) {
    return lib.filter((c) => keys.includes(c.key));
  }

  // ---- Small helpers ----
  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
  }
  // Perceived brightness (0 = black, 1 = white) of a "#rrggbb" hex colour -
  // used to pick a legible checkmark/outline colour against an arbitrary
  // swatch, now that Schwarz/Weiß are selectable Stroop colours too.
  function relLuma(hex) {
    const h = hex.replace("#", "");
    const r = parseInt(h.substr(0, 2), 16), g = parseInt(h.substr(2, 2), 16), b = parseInt(h.substr(4, 2), 16);
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  }
  // Blends two "#rrggbb" colours - used for the background "Intensität"
  // slider (white at 0 .. the full chosen colour at 1).
  function mixHex(hexA, hexB, t) {
    const pa = hexA.replace("#", ""), pb = hexB.replace("#", "");
    const ar = parseInt(pa.substr(0, 2), 16), ag = parseInt(pa.substr(2, 2), 16), ab = parseInt(pa.substr(4, 2), 16);
    const br = parseInt(pb.substr(0, 2), 16), bg = parseInt(pb.substr(2, 2), 16), bb = parseInt(pb.substr(4, 2), 16);
    const r = Math.round(ar + (br - ar) * t), g = Math.round(ag + (bg - ag) * t), b = Math.round(ab + (bb - ab) * t);
    const hex = (n) => n.toString(16).padStart(2, "0");
    return `#${hex(r)}${hex(g)}${hex(b)}`;
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

  // The small centre dot every VT-style exercise shows between stimuli, so
  // the eyes have somewhere fixed to rest on. Periphere Wahrnehmung is the
  // first exercise that lets the client swap it for their own character and
  // change its size/colour - every other exercise keeps the plain default
  // dot untouched.
  function drawFixationPoint(cx, cy, unit) {
    if (!state.periphFixEnabled) return;
    const ex = EXERCISES[state.exercise];
    // Every exercise with this dot can customise it now, except "Hütchen
    // sortieren" which never shows it at all (own colour-tap mechanic).
    const custom = ex && ex.type !== "color-tap";
    const color = custom ? (FIX_COLOR_BY_KEY[state.periphFixColor] || FIX_COLOR_BY_KEY.grau).hex : DOT;
    const scale = custom ? state.periphFixSize : 1;
    const char = custom ? state.periphFixChar.trim() : "";
    if (char) {
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.font = `700 ${Math.round(unit * 0.09 * scale)}px Magra, sans-serif`;
      ctx.fillStyle = color;
      ctx.fillText(char.slice(0, 3), cx, cy);
    } else {
      ctx.beginPath();
      ctx.fillStyle = color;
      ctx.arc(cx, cy, unit * 0.03 * scale, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // Draws one peripheral character (used both by Periphere Wahrnehmung's own
  // "periph" frames and by the Zusatzaufgabe overlay other exercises can
  // show on top of their own schedule) at a {fx,fy} canvas fraction, sized
  // per the given "gleich"/"wachsend" mode - pulled out so both call sites
  // stay pixel-identical instead of drifting apart.
  function drawPeriphChar(cw, ch, unit, fx, fy, char, sizeMode, color) {
    const x = fx * cw, y = fy * ch;
    // Distance from the fixation point, 0 in the centre to ~1 at the
    // screen edge - used for the "nach außen größer" size mode.
    const dist = Math.min(1, Math.hypot((fx - 0.5) * 2, (fy - 0.5) * 2));
    const sizeMul = sizeMode === "wachsend" ? 0.65 + dist * 0.9 : 1;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = `700 ${Math.round(unit * 0.16 * sizeMul)}px Magra, sans-serif`;
    ctx.fillStyle = color || INK;
    ctx.fillText(char, x, y);
  }

  // The client's chosen background tint, or `fallback` for an exercise
  // whose background already carries the trained signal itself (VT's
  // colour, VRW, Kompass-Aufbau, Stroop mit Hintergrund) or when the
  // intensity slider is still at 0 (nothing to blend).
  function currentBgFill(fallback) {
    const ex = EXERCISES[state.exercise];
    if (!ex || ex.type === "color-tap" || ex.bgIsStimulus || state.bgIntensity <= 0) return fallback;
    return mixHex("#ffffff", (STROOP_COLOR_BY_KEY[state.bgColorKey] || STROOP_COLOR_BY_KEY.gruen).hex, state.bgIntensity);
  }

  function drawScene(kind, payload) {
    const cw = canvas.width, ch = canvas.height;
    const cx = cw / 2, cy = ch / 2;
    const unit = Math.min(cw, ch) / 2;
    ctx.fillStyle = currentBgFill("#ffffff");
    ctx.fillRect(0, 0, cw, ch);

    if (kind === "blank") {
      ctx.fillStyle = currentBgFill(NEUTRAL);
      ctx.fillRect(0, 0, cw, ch);
      drawFixationPoint(cx, cy, unit);
    } else if (kind === "periph") {
      ctx.fillStyle = currentBgFill(NEUTRAL);
      ctx.fillRect(0, 0, cw, ch);
      drawFixationPoint(cx, cy, unit);
      drawPeriphChar(cw, ch, unit, payload.fx, payload.fy, payload.char, state.periphSizeMode, payload.color);
      barCaption(cw, ch, "Blick auf die Mitte richten", false);
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
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const size = fitText(ctx, payload.word, cw * 0.82, Math.round(unit * 0.62), "Magra, sans-serif", 700);
      ctx.font = `700 ${size}px Magra, sans-serif`;
      // Ink and background can now both be black or white (Stroop's colour
      // picker includes Schwarz/Weiß) - a thin outline of the opposite
      // brightness keeps the word legible whenever the two nearly match.
      if (Math.abs(relLuma(payload.ink) - relLuma(payload.bg)) < 0.15) {
        ctx.lineWidth = Math.max(2, size * 0.05);
        ctx.strokeStyle = relLuma(payload.ink) > 0.5 ? "#000000" : "#ffffff";
        ctx.strokeText(payload.word, cx, cy);
      }
      ctx.fillStyle = payload.ink;
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
      usesColors: true, bgIsStimulus: true,
      task: "Erkenne Farbe und Pfeilrichtung und reagiere mit der passenden Seite.",
      trains: "Farbwahrnehmung und schnelle Seitenentscheidung",
      rules: "Du siehst eine Farbfläche mit weißem Pfeil. Die Farbe sagt dir, was du tust – der Pfeil zeigt die Seite (links oder rechts). Welche Farbe wofür steht, legst du mit deinem Coach fest.",
    },
    "vrw-original": {
      title: "VRW · Direkt & Umgekehrt",
      type: "vrw-real",
      usesColors: true, bgIsStimulus: true,
      task: "Weißer Pfeil auf Farbe: gezeigte Seite. Farbiger Pfeil auf Weiß: Gegenseite.",
      trains: "Regelwechsel und Impulskontrolle",
      rules: "Weißer Pfeil auf farbiger Fläche: Die gezeigte Seite zählt (direkt). Farbiger Pfeil auf weißer Fläche: Die Gegenseite zählt (umgekehrt).",
      explainerVideo: "explainer-vrw-placeholder.mp4",
    },
    "4-straight": {
      title: "4 Pfeile · gerade", type: "arrows", dirset: 4, dual: false, usesArrowColors: true,
      task: "Reagiere so schnell wie möglich in die gezeigte Richtung.",
      trains: "Reaktionsgeschwindigkeit und Richtungserkennung",
      rules: "Ein Pfeil zeigt nach vorne, rechts, hinten oder links. Reagiere so schnell wie möglich in diese Richtung.",
    },
    "4-diag": {
      title: "4 Pfeile · diagonal", type: "arrows", dirset: "diag", dual: false, usesArrowColors: true,
      task: "Reagiere so schnell wie möglich in die gezeigte Schrägrichtung.",
      trains: "Reaktionsgeschwindigkeit und Orientierung",
      rules: "Ein Pfeil zeigt in eine der vier Schrägrichtungen. Reagiere so schnell wie möglich in diese Richtung.",
    },
    "8-solo": {
      title: "8 Pfeile", type: "arrows", dirset: 8, dual: false, usesArrowColors: true,
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
      title: "Stroop · klassisch", type: "stroop", bg: false, usesStroopColors: true,
      task: "Sag laut die Schriftfarbe – nicht das Wort.",
      trains: "Konzentration und Ausblenden von Störreizen",
      rules: "Du siehst ein Farbwort in einer anderen Schriftfarbe. Sag laut die Schriftfarbe – nicht das, was da steht.",
    },
    "stroop-bg": {
      title: "Stroop · mit Hintergrund", type: "stroop", bg: true, usesStroopColors: true, bgIsStimulus: true,
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
      title: "Hütchen · Kompass-Aufbau", type: "color", usesColors: true, setupDiagram: true, bgIsStimulus: true,
      task: "Reagiere auf die Farbe – passend zu deinem eigenen Richtungs-Aufbau am Boden.",
      trains: "Reaktionsschnelligkeit gezielt in frei gewählte Richtungen",
      rules: "Klebe ein Kreuz oder einen Stern mit vier oder acht Richtungen auf den Boden und stelle deine Farbhütchen in die Richtungen, die du trainieren willst. Mehrere Farben auf derselben Richtung lassen diese Richtung häufiger drankommen. Welche Farbe wohin gehört, legst du komplett selbst fest – die App zeigt immer nur die Farbe.",
    },
    "periph-flash": {
      title: "Periphere Wahrnehmung", type: "periph",
      task: "Fixiere den Punkt in der Mitte. Nimm wahr, was am Rand erscheint, ohne die Augen zu bewegen.",
      trains: "Peripheres Sehen bei stabiler Fixierung",
      rules: "Visuelles Training ist anstrengend – vor allem für Augen und Nervensystem. Achte auf ausreichend Pausen. Merkst du, dass dein System stark gefordert ist oder droht zu überlasten, reduziere Tempo/Dauer oder sprich im Zweifel mit deinem Trainer.",
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

  // Two pictogram styles, picked per client via movementPrefs.figureStyle
  // (Feineinstellungen → "Darstellung"). The original single design (four
  // spokes off a plain hub, no head/body outline - deliberately not a
  // little figure, since the closest known reference, Life Kinetik's
  // "Bocobrain" sheets, already owns that visual territory) turned out to
  // read as neither a clear figure nor a clean abstract symbol once Fabian
  // saw it in real use ("weit genug weg vom Original... aber nichts halbes
  // und nichts ganzes") - replaced 2026-09-27 with two new, more
  // committed alternatives instead of one compromise:
  // - "figur": an actual stick figure (head/torso/four limbs) - the
  //   "richtige Darstellung" option.
  // - "abstrakt": a 2x2 grid of independent symbol tiles (one per limb,
  //   arm row above leg row), each just an up-arrow ("heben") or an
  //   outward arrow ("strecken") on a neutral dot otherwise - not a body
  //   silhouette at all, so it can't land in that same awkward middle
  //   ground the old spokes did.
  // `baseColor` lets either renderer sit on a themed background (settings
  // screen, follows dark mode) or the always-light player stage (fixed
  // dark ink, matching the visual-training canvas).
  const FIG_HIGHLIGHT = "#ff9110";
  // slots: { armLeft, armRight, legLeft, legRight } - each holds a pose
  // name ("heben"/"strecken") when that screen-side limb is the active one.
  const FIGURE_LIMB = {
    armLeft: { x0: 41, y0: 30, neutral: [31, 50], heben: [21, 15], strecken: [6, 27] },
    armRight: { x0: 59, y0: 30, neutral: [69, 50], heben: [79, 15], strecken: [94, 27] },
    legLeft: { x0: 45, y0: 60, neutral: [35, 93], heben: [26, 63], strecken: [10, 85] },
    legRight: { x0: 55, y0: 60, neutral: [65, 93], heben: [74, 63], strecken: [90, 85] },
  };
  function figureSVGFigur(slots, baseColor) {
    baseColor = baseColor || "#16232a";
    const limbs = ["armLeft", "armRight", "legLeft", "legRight"].map((key) => {
      const type = slots[key];
      const def = FIGURE_LIMB[key];
      const [x2, y2] = def[type || "neutral"];
      const color = type ? FIG_HIGHLIGHT : baseColor;
      const width = type ? 10 : 8;
      return `<line x1="${def.x0}" y1="${def.y0}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}" stroke-linecap="round"/>`;
    }).join("");
    return `<svg viewBox="0 0 100 100" class="figure-svg" aria-hidden="true">` +
      `<line x1="50" y1="30" x2="50" y2="60" stroke="${baseColor}" stroke-width="9" stroke-linecap="round"/>` +
      limbs +
      `<circle cx="50" cy="16" r="10" fill="${baseColor}"/></svg>`;
  }
  const ABSTRACT_CELL = {
    armLeft: { cx: 25, cy: 25, out: 180 }, armRight: { cx: 75, cy: 25, out: 0 },
    legLeft: { cx: 25, cy: 75, out: 180 }, legRight: { cx: 75, cy: 75, out: 0 },
  };
  function arrowPolygon(cx, cy, angleDeg, size) {
    const rad = (angleDeg * Math.PI) / 180;
    const tip = [cx + Math.cos(rad) * size, cy + Math.sin(rad) * size];
    const b1 = [cx + Math.cos(rad + 2.4) * size * 0.55, cy + Math.sin(rad + 2.4) * size * 0.55];
    const b2 = [cx + Math.cos(rad - 2.4) * size * 0.55, cy + Math.sin(rad - 2.4) * size * 0.55];
    return [tip, b1, b2].map((p) => p.map((n) => n.toFixed(1)).join(",")).join(" ");
  }
  function figureSVGAbstrakt(slots, baseColor) {
    baseColor = baseColor || "#16232a";
    const cells = ["armLeft", "armRight", "legLeft", "legRight"].map((key) => {
      const type = slots[key];
      const def = ABSTRACT_CELL[key];
      const active = !!type;
      const ring = active ? FIG_HIGHLIGHT : baseColor;
      const fill = active ? FIG_HIGHLIGHT : "none";
      let mark;
      if (type === "heben") mark = `<polygon points="${arrowPolygon(def.cx, def.cy, -90, 13)}" fill="#fff"/>`;
      else if (type === "strecken") mark = `<polygon points="${arrowPolygon(def.cx, def.cy, def.out, 13)}" fill="#fff"/>`;
      else mark = `<circle cx="${def.cx}" cy="${def.cy}" r="3" fill="${baseColor}"/>`;
      return `<circle cx="${def.cx}" cy="${def.cy}" r="19" fill="${fill}" stroke="${ring}" stroke-width="3"/>${mark}`;
    }).join("");
    return `<svg viewBox="0 0 100 100" class="figure-svg" aria-hidden="true">${cells}</svg>`;
  }
  function figureSVG(slots, baseColor) {
    return movementPrefs.figureStyle === "abstrakt" ? figureSVGAbstrakt(slots, baseColor) : figureSVGFigur(slots, baseColor);
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
    burpee: {
      name: "Burpees", icon: "burpee",
      note: "In die Hocke, Hände auf den Boden, Beine nach hinten in den Stütz, zurück in die Hocke, hochspringen.",
    },
    situp: {
      name: "Sit-ups", icon: "situp",
      note: "Füße aufgestellt, Hände locker an den Schläfen. Aus dem Bauch aufrollen, nicht am Nacken ziehen.",
    },
    superman: {
      name: "Superman", icon: "superman",
      note: "Bauchlage, Arme und Beine gleichzeitig anheben, kurz halten, kontrolliert absenken.",
    },
    huefthebe: {
      name: "Hüftheben (Brücke)", icon: "gluebridge",
      note: "Rückenlage, Füße hüftbreit aufgestellt. Gesäß anspannen und die Hüfte gerade nach oben schieben.",
    },
    kniehebelauf: {
      name: "Kniehebelauf", icon: "highknees",
      note: "Auf der Stelle laufen, Knie abwechselnd zügig bis auf Hüfthöhe anheben, Arme mitschwingen.",
    },
    wandsitz: {
      name: "Wandsitz", icon: "wallsit",
      note: "Rücken flach an der Wand, Knie im rechten Winkel wie auf einem unsichtbaren Stuhl. Ruhig durchatmen.",
    },
    trizepsdip: {
      name: "Trizeps-Dips", icon: "dip",
      note: "Hände am Stuhl-/Bankrand, Beine gestreckt nach vorne. Ellbogen zeigen nach hinten, Gesäß dicht an der Kante absenken.",
    },
    sprungkniebeuge: {
      name: "Sprungkniebeugen", icon: "squatjump",
      note: "Wie eine normale Kniebeuge, aus der unteren Position aber explosiv nach oben abspringen, weich landen.",
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
    burpee: `<circle cx="5" cy="15" r="2" fill="#fff"/><path d="M7 15 L12 9 L19 11" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 9 L15 16 L19 19" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
    situp: `<circle cx="4" cy="16" r="2" fill="#fff"/><path d="M6 16 Q11 9 14 13" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M14 13 L13 18 L18 18" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M13 18 L17 14" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    superman: `<circle cx="19" cy="7" r="2" fill="#fff"/><path d="M17 8 Q11 12 6 8" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    gluebridge: `<circle cx="19" cy="14" r="2" fill="#fff"/><path d="M17 14 L10 14" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M10 14 L13 9 L16 14" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
    highknees: `<circle cx="12" cy="4" r="2" fill="#fff"/><path d="M12 6 L11 13" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M12 8 L8 6 M12 8 L17 10" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M11 13 L7 11 L7 17" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M11 13 L15 17 L15 20" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
    wallsit: `<circle cx="15" cy="4" r="2" fill="#fff"/><path d="M15 6 L15 11" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M15 7 L11 9" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M15 11 L9 11 L9 18" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M17 2 L17 20" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    dip: `<circle cx="17" cy="8" r="2" fill="#fff"/><path d="M17 10 L14 14" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M17 11 L20 13" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M14 14 L6 14" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M20 13 L20 18" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
    squatjump: `<circle cx="12" cy="4" r="2" fill="#fff"/><path d="M12 6 L12 11" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M12 7 L8 3 M12 7 L16 3" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/><path d="M12 11 L9 15 L9 19 M12 11 L15 15 L15 19" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 20 L8 20 M16 20 L19 20" stroke="#fff" stroke-width="1.8" fill="none" stroke-linecap="round"/>`,
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
    if (block.domain === "nat") return `Remember · ${REMEMBER_MODES[block.mode] ? REMEMBER_MODES[block.mode].title : block.mode}`;
    return block.domain;
  }
  function comboBlockMeta(block) {
    if (block.domain === "wimhof") return `${block.rounds ?? WIMHOF_DEFAULTS.rounds} Runden`;
    if (block.domain === "breath") return fmtMinutes((block.durationMin ?? 5) * 60);
    if (block.domain === "movement") return fmtMinutes((block.durationMin ?? 2) * 60);
    if (block.domain === "workout") return workoutBlockMeta(block);
    if (block.domain === "visual") return fmtMinutes((block.duration ?? 60));
    if (block.domain === "nat") return fmtMinutes((block.duration ?? 60));
    return "";
  }
  function comboBlockSeconds(block) {
    if (block.domain === "wimhof") { const r = block.rounds ?? WIMHOF_DEFAULTS.rounds, n = block.breaths ?? WIMHOF_DEFAULTS.breaths; return r * (n * (block.breathPaceS ?? WIMHOF_DEFAULTS.breathPaceS) + 30 + (block.recoveryHoldS ?? WIMHOF_DEFAULTS.recoveryHoldS)); }
    if (block.domain === "breath") return (block.durationMin ?? 5) * 60;
    if (block.domain === "movement") return (block.durationMin ?? 2) * 60;
    if (block.domain === "workout") return workoutBlockSeconds(block);
    if (block.domain === "visual") return block.duration ?? 60;
    if (block.domain === "nat") return block.duration ?? 60;
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
    nat: [
      { domain: "nat", mode: "fixed", duration: 60 },
      { domain: "nat", mode: "shuffle", duration: 60 },
    ],
  };
  const COMBO_DOMAIN_TITLE = { breath: "Atemtraining", movement: "Movement", visual: "Visual Training", workout: "Workout", nat: "NAT" };

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
    periphKindGroup: $("periphKindGroup"), periphFixGroup: $("periphFixGroup"),
    periphFixToggleRow: $("periphFixToggleRow"), periphFixOptions: $("periphFixOptions"),
    periphFixCharInput: $("periphFixCharInput"), periphFixColorPicker: $("periphFixColorPicker"),
    periphFixSizeSlider: $("periphFixSizeSlider"), periphFixSizeValue: $("periphFixSizeValue"),
    periphColorGroup: $("periphColorGroup"), periphColorPicker: $("periphColorPicker"), periphColorHint: $("periphColorHint"),
    periphOpenBtn: $("periphOpenBtn"),
    periphFieldGroup: $("periphFieldGroup"), periphFieldRow: $("periphFieldRow"), periphZoneGrid: $("periphZoneGrid"), periphSizeGroup: $("periphSizeGroup"),
    periphZoneWeights: $("periphZoneWeights"),
    periphAllBtn: $("periphAllBtn"), periphZonesBtn: $("periphZonesBtn"), periphFieldHint: $("periphFieldHint"),
    addonGroup: $("addonGroup"), addonPhaseRow: $("addonPhaseRow"), addonPhaseAllBtn: $("addonPhaseAllBtn"), addonPhaseHint: $("addonPhaseHint"),
    addonConfigBody: $("addonConfigBody"), addonModeRow: $("addonModeRow"), addonOwnBody: $("addonOwnBody"),
    addonKindRow: $("addonKindRow"), addonFieldRow: $("addonFieldRow"), addonAllBtn: $("addonAllBtn"),
    addonFieldHint: $("addonFieldHint"), addonZonesBtn: $("addonZonesBtn"), addonZoneGrid: $("addonZoneGrid"),
    addonColorPicker: $("addonColorPicker"), addonColorHint: $("addonColorHint"),
    addonStimulusSlider: $("addonStimulusSlider"), addonStimulusValue: $("addonStimulusValue"),
    addonIntervalMinSlider: $("addonIntervalMinSlider"), addonIntervalMaxSlider: $("addonIntervalMaxSlider"), addonIntervalValue: $("addonIntervalValue"),
    addonPresetGroup: $("addonPresetGroup"), addonPresetList: $("addonPresetList"),
    addonSaveBtn: $("addonSaveBtn"), addonSaveForm: $("addonSaveForm"), addonSaveNameInput: $("addonSaveNameInput"),
    addonSaveCancelBtn: $("addonSaveCancelBtn"), addonSaveConfirmBtn: $("addonSaveConfirmBtn"),
    bgGroup: $("bgGroup"), bgColorPicker: $("bgColorPicker"), bgIntensitySlider: $("bgIntensitySlider"),
    bgIntensityValue: $("bgIntensityValue"), bgContrastHint: $("bgContrastHint"),
    bgSourceRow: $("bgSourceRow"), bgPresetGroup: $("bgPresetGroup"), bgPresetList: $("bgPresetList"),
    bgSaveBtn: $("bgSaveBtn"), bgSaveForm: $("bgSaveForm"), bgSaveNameInput: $("bgSaveNameInput"),
    bgSaveCancelBtn: $("bgSaveCancelBtn"), bgSaveConfirmBtn: $("bgSaveConfirmBtn"),
    periphPauseBtn: $("periphPauseBtn"), periphPauseOverlay: $("periphPauseOverlay"),
    periphPauseBgSlider: $("periphPauseBgSlider"), periphPauseBgValue: $("periphPauseBgValue"),
    periphPauseBgColorPicker: $("periphPauseBgColorPicker"), periphPauseFixColorPicker: $("periphPauseFixColorPicker"),
    periphPauseFixSizeSlider: $("periphPauseFixSizeSlider"), periphPauseFixSizeValue: $("periphPauseFixSizeValue"),
    periphResumeBtn: $("periphResumeBtn"),
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
    setupBtn: $("setupBtn"), setupThumb: $("setupThumb"),
    setupModal: $("setupModal"), setupModalClose: $("setupModalClose"),
    setupSlideArt: $("setupSlideArt"), setupSlideTitle: $("setupSlideTitle"), setupSlideCaption: $("setupSlideCaption"),
    setupCounter: $("setupCounter"), setupPrevBtn: $("setupPrevBtn"), setupNextBtn: $("setupNextBtn"),
    historySection: $("historySection"), historyStats: $("historyStats"), historyList: $("historyList"), historyClearBtn: $("historyClearBtn"),
    historyMoreBtn: $("historyMoreBtn"),
    tipsSheet: $("tipsSheet"), tipsBtn: $("tipsBtn"), tipsCloseBtn: $("tipsCloseBtn"),
    tipInstall: $("tipInstall"), tipInstallText: $("tipInstallText"),
    faqSheet: $("faqSheet"), faqCloseBtn: $("faqCloseBtn"),
    masterSettingsSheet: $("masterSettingsSheet"), masterSettingsCloseBtn: $("masterSettingsCloseBtn"),
    masterCodeHistoryGroup: $("masterCodeHistoryGroup"), masterCodeHistoryList: $("masterCodeHistoryList"),
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
    natHome: $("natHome"), natPeripherPanel: $("natPeripherPanel"), natRememberPanel: $("natRememberPanel"), natBlitzPanel: $("natBlitzPanel"), natFlashPanel: $("natFlashPanel"), natMotPanel: $("natMotPanel"),
    testHome: $("testHome"), testPanel: $("testPanel"), testEmptyHint: $("testEmptyHint"),
    gngOpenBtn: $("gngOpenBtn"), gngBestHint: $("gngBestHint"), gngReady: $("gngReady"),
    gngReadyBackToHome: $("gngReadyBackToHome"), gngDifficultyRow: $("gngDifficultyRow"),
    gngAdvanced: $("gngAdvanced"), gngBgColorPicker: $("gngBgColorPicker"), gngBgIntensitySlider: $("gngBgIntensitySlider"),
    gngBgIntensityValue: $("gngBgIntensityValue"), gngBgContrastHint: $("gngBgContrastHint"),
    gngReadyBestHint: $("gngReadyBestHint"), gngReadyStartBtn: $("gngReadyStartBtn"),
    gngPlayer: $("gngPlayer"), gngStage: $("gngStage"), gngHint: $("gngHint"), gngStimulus: $("gngStimulus"),
    gngPauseOverlay: $("gngPauseOverlay"), gngResumeBtn: $("gngResumeBtn"),
    gngPauseBgColorPicker: $("gngPauseBgColorPicker"), gngPauseBgSlider: $("gngPauseBgSlider"), gngPauseBgValue: $("gngPauseBgValue"),
    gngPlayerBar: $("gngPlayerBar"), gngBackBtn: $("gngBackBtn"), gngPauseBtn: $("gngPauseBtn"), gngProgressEl: $("gngProgressEl"),
    gngFsBtn: $("gngFsBtn"), gngFsHint: $("gngFsHint"), gngFsHintOpenBtn: $("gngFsHintOpenBtn"), gngFsHintClose: $("gngFsHintClose"),
    gngDonePanel: $("gngDonePanel"), gngDoneSummary: $("gngDoneSummary"), gngRating: $("gngRating"),
    gngAgainBtn: $("gngAgainBtn"), gngDoneBackBtn: $("gngDoneBackBtn"),
    testNbackOpenBtn: $("testNbackOpenBtn"), testNbackBestHint: $("testNbackBestHint"),
    testNbackReady: $("testNbackReady"), testNbackReadyBackToHome: $("testNbackReadyBackToHome"),
    testNbackStartRow: $("testNbackStartRow"),
    testNbackAdvanced: $("testNbackAdvanced"), testNbackBgColorPicker: $("testNbackBgColorPicker"),
    testNbackBgIntensitySlider: $("testNbackBgIntensitySlider"), testNbackBgIntensityValue: $("testNbackBgIntensityValue"),
    testNbackBgContrastHint: $("testNbackBgContrastHint"),
    testNbackReadyBestHint: $("testNbackReadyBestHint"),
    testNbackReadyStartBtn: $("testNbackReadyStartBtn"),
    testNbackPlayer: $("testNbackPlayer"), testNbackStage: $("testNbackStage"), testNbackHint: $("testNbackHint"),
    testNbackGrid: $("testNbackGrid"), testNbackMatchBtn: $("testNbackMatchBtn"),
    testNbackPauseOverlay: $("testNbackPauseOverlay"), testNbackResumeBtn: $("testNbackResumeBtn"),
    testNbackPauseBgColorPicker: $("testNbackPauseBgColorPicker"), testNbackPauseBgSlider: $("testNbackPauseBgSlider"),
    testNbackPauseBgValue: $("testNbackPauseBgValue"),
    testNbackPlayerBar: $("testNbackPlayerBar"), testNbackBackBtn: $("testNbackBackBtn"), testNbackPauseBtn: $("testNbackPauseBtn"),
    testNbackLevelEl: $("testNbackLevelEl"), testNbackFsBtn: $("testNbackFsBtn"), testNbackFsHint: $("testNbackFsHint"),
    testNbackFsHintOpenBtn: $("testNbackFsHintOpenBtn"), testNbackFsHintClose: $("testNbackFsHintClose"),
    testNbackDonePanel: $("testNbackDonePanel"), testNbackDoneSummary: $("testNbackDoneSummary"), testNbackRating: $("testNbackRating"),
    testNbackAgainBtn: $("testNbackAgainBtn"), testNbackDoneBackBtn: $("testNbackDoneBackBtn"),
    trailOpenBtn: $("trailOpenBtn"), trailBestHint: $("trailBestHint"), trailReady: $("trailReady"),
    trailReadyBackToHome: $("trailReadyBackToHome"), trailTeilRow: $("trailTeilRow"), trailDifficultyRow: $("trailDifficultyRow"),
    trailAdvanced: $("trailAdvanced"), trailBgColorPicker: $("trailBgColorPicker"), trailBgIntensitySlider: $("trailBgIntensitySlider"),
    trailBgIntensityValue: $("trailBgIntensityValue"), trailBgContrastHint: $("trailBgContrastHint"),
    trailReadyBestHint: $("trailReadyBestHint"), trailReadyStartBtn: $("trailReadyStartBtn"),
    trailPlayer: $("trailPlayer"), trailStage: $("trailStage"), trailHint: $("trailHint"),
    trailLinesSvg: $("trailLinesSvg"), trailMarkersLayer: $("trailMarkersLayer"),
    trailPauseOverlay: $("trailPauseOverlay"), trailResumeBtn: $("trailResumeBtn"),
    trailPauseBgColorPicker: $("trailPauseBgColorPicker"), trailPauseBgSlider: $("trailPauseBgSlider"), trailPauseBgValue: $("trailPauseBgValue"),
    trailPlayerBar: $("trailPlayerBar"), trailBackBtn: $("trailBackBtn"), trailPauseBtn: $("trailPauseBtn"), trailProgressEl: $("trailProgressEl"),
    trailFsBtn: $("trailFsBtn"), trailFsHint: $("trailFsHint"), trailFsHintOpenBtn: $("trailFsHintOpenBtn"), trailFsHintClose: $("trailFsHintClose"),
    trailDonePanel: $("trailDonePanel"), trailDoneSummary: $("trailDoneSummary"), trailRating: $("trailRating"),
    trailAgainBtn: $("trailAgainBtn"), trailDoneBackBtn: $("trailDoneBackBtn"),
    flankerOpenBtn: $("flankerOpenBtn"), flankerBestHint: $("flankerBestHint"), flankerReady: $("flankerReady"),
    flankerReadyBackToHome: $("flankerReadyBackToHome"), flankerDifficultyRow: $("flankerDifficultyRow"),
    flankerAdvanced: $("flankerAdvanced"), flankerBgColorPicker: $("flankerBgColorPicker"), flankerBgIntensitySlider: $("flankerBgIntensitySlider"),
    flankerBgIntensityValue: $("flankerBgIntensityValue"), flankerBgContrastHint: $("flankerBgContrastHint"),
    flankerReadyBestHint: $("flankerReadyBestHint"), flankerReadyStartBtn: $("flankerReadyStartBtn"),
    flankerPlayer: $("flankerPlayer"), flankerStage: $("flankerStage"), flankerHint: $("flankerHint"), flankerRow: $("flankerRow"),
    flankerLeftBtn: $("flankerLeftBtn"), flankerRightBtn: $("flankerRightBtn"),
    flankerPauseOverlay: $("flankerPauseOverlay"), flankerResumeBtn: $("flankerResumeBtn"),
    flankerPauseBgColorPicker: $("flankerPauseBgColorPicker"), flankerPauseBgSlider: $("flankerPauseBgSlider"), flankerPauseBgValue: $("flankerPauseBgValue"),
    flankerPlayerBar: $("flankerPlayerBar"), flankerBackBtn: $("flankerBackBtn"), flankerPauseBtn: $("flankerPauseBtn"), flankerProgressEl: $("flankerProgressEl"),
    flankerFsBtn: $("flankerFsBtn"), flankerFsHint: $("flankerFsHint"), flankerFsHintOpenBtn: $("flankerFsHintOpenBtn"), flankerFsHintClose: $("flankerFsHintClose"),
    flankerDonePanel: $("flankerDonePanel"), flankerDoneSummary: $("flankerDoneSummary"), flankerRating: $("flankerRating"),
    flankerAgainBtn: $("flankerAgainBtn"), flankerDoneBackBtn: $("flankerDoneBackBtn"),

    ufovOpenBtn: $("ufovOpenBtn"), ufovBestHint: $("ufovBestHint"), ufovReady: $("ufovReady"),
    ufovReadyBackToHome: $("ufovReadyBackToHome"), ufovLengthRow: $("ufovLengthRow"),
    ufovAdvanced: $("ufovAdvanced"), ufovBgColorPicker: $("ufovBgColorPicker"), ufovBgIntensitySlider: $("ufovBgIntensitySlider"),
    ufovBgIntensityValue: $("ufovBgIntensityValue"), ufovBgContrastHint: $("ufovBgContrastHint"),
    ufovReadyBestHint: $("ufovReadyBestHint"), ufovReadyStartBtn: $("ufovReadyStartBtn"),
    ufovPlayer: $("ufovPlayer"), ufovStage: $("ufovStage"), ufovHint: $("ufovHint"), ufovField: $("ufovField"),
    ufovCenterEl: $("ufovCenterEl"),
    ufovRing0: $("ufovRing0"), ufovRing1: $("ufovRing1"), ufovRing2: $("ufovRing2"), ufovRing3: $("ufovRing3"),
    ufovRing4: $("ufovRing4"), ufovRing5: $("ufovRing5"), ufovRing6: $("ufovRing6"), ufovRing7: $("ufovRing7"),
    ufovShapeBtns: $("ufovShapeBtns"), ufovShapeCircleBtn: $("ufovShapeCircleBtn"), ufovShapeSquareBtn: $("ufovShapeSquareBtn"),
    ufovRingBtns: $("ufovRingBtns"), ufovRingBtnField: $("ufovRingBtnField"),
    ufovPauseOverlay: $("ufovPauseOverlay"), ufovResumeBtn: $("ufovResumeBtn"),
    ufovPauseBgColorPicker: $("ufovPauseBgColorPicker"), ufovPauseBgSlider: $("ufovPauseBgSlider"), ufovPauseBgValue: $("ufovPauseBgValue"),
    ufovPlayerBar: $("ufovPlayerBar"), ufovBackBtn: $("ufovBackBtn"), ufovPauseBtn: $("ufovPauseBtn"), ufovProgressEl: $("ufovProgressEl"),
    ufovFsBtn: $("ufovFsBtn"), ufovFsHint: $("ufovFsHint"), ufovFsHintOpenBtn: $("ufovFsHintOpenBtn"), ufovFsHintClose: $("ufovFsHintClose"),
    ufovDonePanel: $("ufovDonePanel"), ufovDoneSummary: $("ufovDoneSummary"), ufovRating: $("ufovRating"),
    ufovAgainBtn: $("ufovAgainBtn"), ufovDoneBackBtn: $("ufovDoneBackBtn"),

    posnerOpenBtn: $("posnerOpenBtn"), posnerBestHint: $("posnerBestHint"), posnerReady: $("posnerReady"),
    posnerReadyBackToHome: $("posnerReadyBackToHome"), posnerDifficultyRow: $("posnerDifficultyRow"),
    posnerAdvanced: $("posnerAdvanced"), posnerBgColorPicker: $("posnerBgColorPicker"), posnerBgIntensitySlider: $("posnerBgIntensitySlider"),
    posnerBgIntensityValue: $("posnerBgIntensityValue"), posnerBgContrastHint: $("posnerBgContrastHint"),
    posnerReadyBestHint: $("posnerReadyBestHint"), posnerReadyStartBtn: $("posnerReadyStartBtn"),
    posnerPlayer: $("posnerPlayer"), posnerStage: $("posnerStage"), posnerHint: $("posnerHint"),
    posnerLeftBtn: $("posnerLeftBtn"), posnerRightBtn: $("posnerRightBtn"),
    posnerLeftDot: $("posnerLeftDot"), posnerRightDot: $("posnerRightDot"),
    posnerPauseOverlay: $("posnerPauseOverlay"), posnerResumeBtn: $("posnerResumeBtn"),
    posnerPauseBgColorPicker: $("posnerPauseBgColorPicker"), posnerPauseBgSlider: $("posnerPauseBgSlider"), posnerPauseBgValue: $("posnerPauseBgValue"),
    posnerPlayerBar: $("posnerPlayerBar"), posnerBackBtn: $("posnerBackBtn"), posnerPauseBtn: $("posnerPauseBtn"), posnerProgressEl: $("posnerProgressEl"),
    posnerFsBtn: $("posnerFsBtn"), posnerFsHint: $("posnerFsHint"), posnerFsHintOpenBtn: $("posnerFsHintOpenBtn"), posnerFsHintClose: $("posnerFsHintClose"),
    posnerDonePanel: $("posnerDonePanel"), posnerDoneSummary: $("posnerDoneSummary"), posnerRating: $("posnerRating"),
    posnerAgainBtn: $("posnerAgainBtn"), posnerDoneBackBtn: $("posnerDoneBackBtn"),
    simonOpenBtn: $("simonOpenBtn"), simonBestHint: $("simonBestHint"), simonReady: $("simonReady"),
    simonReadyBackToHome: $("simonReadyBackToHome"), simonDifficultyRow: $("simonDifficultyRow"),
    simonAdvanced: $("simonAdvanced"), simonBgColorPicker: $("simonBgColorPicker"), simonBgIntensitySlider: $("simonBgIntensitySlider"),
    simonBgIntensityValue: $("simonBgIntensityValue"), simonBgContrastHint: $("simonBgContrastHint"),
    simonReadyBestHint: $("simonReadyBestHint"), simonReadyStartBtn: $("simonReadyStartBtn"),
    simonPlayer: $("simonPlayer"), simonStage: $("simonStage"), simonHint: $("simonHint"),
    simonSlotLeft: $("simonSlotLeft"), simonSlotRight: $("simonSlotRight"), simonDotLeft: $("simonDotLeft"), simonDotRight: $("simonDotRight"),
    simonLeftBtn: $("simonLeftBtn"), simonRightBtn: $("simonRightBtn"),
    simonPauseOverlay: $("simonPauseOverlay"), simonPauseBgSlider: $("simonPauseBgSlider"), simonPauseBgValue: $("simonPauseBgValue"),
    simonPauseBgColorPicker: $("simonPauseBgColorPicker"), simonResumeBtn: $("simonResumeBtn"),
    simonPlayerBar: $("simonPlayerBar"), simonBackBtn: $("simonBackBtn"), simonPauseBtn: $("simonPauseBtn"), simonProgressEl: $("simonProgressEl"),
    simonFsBtn: $("simonFsBtn"), simonFsHint: $("simonFsHint"), simonFsHintOpenBtn: $("simonFsHintOpenBtn"), simonFsHintClose: $("simonFsHintClose"),
    simonDonePanel: $("simonDonePanel"), simonDoneSummary: $("simonDoneSummary"), simonRating: $("simonRating"),
    simonAgainBtn: $("simonAgainBtn"), simonDoneBackBtn: $("simonDoneBackBtn"),
    searchOpenBtn: $("searchOpenBtn"), searchBestHint: $("searchBestHint"), searchReady: $("searchReady"),
    searchReadyBackToHome: $("searchReadyBackToHome"), searchLengthRow: $("searchLengthRow"),
    searchAdvanced: $("searchAdvanced"), searchBgColorPicker: $("searchBgColorPicker"), searchBgIntensitySlider: $("searchBgIntensitySlider"),
    searchBgIntensityValue: $("searchBgIntensityValue"), searchBgContrastHint: $("searchBgContrastHint"),
    searchReadyBestHint: $("searchReadyBestHint"), searchReadyStartBtn: $("searchReadyStartBtn"),
    searchPlayer: $("searchPlayer"), searchStage: $("searchStage"), searchHint: $("searchHint"), searchItemsLayer: $("searchItemsLayer"),
    searchPauseOverlay: $("searchPauseOverlay"), searchPauseBgSlider: $("searchPauseBgSlider"), searchPauseBgValue: $("searchPauseBgValue"),
    searchPauseBgColorPicker: $("searchPauseBgColorPicker"), searchResumeBtn: $("searchResumeBtn"),
    searchPlayerBar: $("searchPlayerBar"), searchBackBtn: $("searchBackBtn"), searchPauseBtn: $("searchPauseBtn"), searchProgressEl: $("searchProgressEl"),
    searchFsBtn: $("searchFsBtn"), searchFsHint: $("searchFsHint"), searchFsHintOpenBtn: $("searchFsHintOpenBtn"), searchFsHintClose: $("searchFsHintClose"),
    searchDonePanel: $("searchDonePanel"), searchDoneSummary: $("searchDoneSummary"), searchRating: $("searchRating"),
    searchAgainBtn: $("searchAgainBtn"), searchDoneBackBtn: $("searchDoneBackBtn"),
    abOpenBtn: $("abOpenBtn"), abBestHint: $("abBestHint"), abReady: $("abReady"),
    abReadyBackToHome: $("abReadyBackToHome"), abDifficultyRow: $("abDifficultyRow"),
    abAdvanced: $("abAdvanced"), abBgColorPicker: $("abBgColorPicker"), abBgIntensitySlider: $("abBgIntensitySlider"),
    abBgIntensityValue: $("abBgIntensityValue"), abBgContrastHint: $("abBgContrastHint"),
    abReadyBestHint: $("abReadyBestHint"), abReadyStartBtn: $("abReadyStartBtn"),
    abPlayer: $("abPlayer"), abStage: $("abStage"), abHint: $("abHint"), abStreamChar: $("abStreamChar"),
    abT1Panel: $("abT1Panel"), abT1Btn0: $("abT1Btn0"), abT1Btn1: $("abT1Btn1"), abT1Btn2: $("abT1Btn2"), abT1Btn3: $("abT1Btn3"),
    abT2Panel: $("abT2Panel"), abT2JaBtn: $("abT2JaBtn"), abT2NeinBtn: $("abT2NeinBtn"), abRevealHint: $("abRevealHint"),
    abPauseOverlay: $("abPauseOverlay"), abPauseBgSlider: $("abPauseBgSlider"), abPauseBgValue: $("abPauseBgValue"),
    abPauseBgColorPicker: $("abPauseBgColorPicker"), abResumeBtn: $("abResumeBtn"),
    abPlayerBar: $("abPlayerBar"), abBackBtn: $("abBackBtn"), abPauseBtn: $("abPauseBtn"), abProgressEl: $("abProgressEl"),
    abFsBtn: $("abFsBtn"), abFsHint: $("abFsHint"), abFsHintOpenBtn: $("abFsHintOpenBtn"), abFsHintClose: $("abFsHintClose"),
    abDonePanel: $("abDonePanel"), abDoneSummary: $("abDoneSummary"), abRating: $("abRating"),
    abAgainBtn: $("abAgainBtn"), abDoneBackBtn: $("abDoneBackBtn"),
    antizipOpenBtn: $("antizipOpenBtn"), antizipBestHint: $("antizipBestHint"), antizipReady: $("antizipReady"),
    antizipReadyBackToHome: $("antizipReadyBackToHome"), antizipDifficultyRow: $("antizipDifficultyRow"),
    antizipAdvanced: $("antizipAdvanced"), antizipBgColorPicker: $("antizipBgColorPicker"), antizipBgIntensitySlider: $("antizipBgIntensitySlider"),
    antizipBgIntensityValue: $("antizipBgIntensityValue"), antizipBgContrastHint: $("antizipBgContrastHint"),
    antizipReadyBestHint: $("antizipReadyBestHint"), antizipReadyStartBtn: $("antizipReadyStartBtn"),
    antizipPlayer: $("antizipPlayer"), antizipStage: $("antizipStage"), antizipHint: $("antizipHint"),
    antizipTrack: $("antizipTrack"), antizipTargetZone: $("antizipTargetZone"), antizipBall: $("antizipBall"),
    antizipFeedback: $("antizipFeedback"), antizipTapBtn: $("antizipTapBtn"),
    antizipPauseOverlay: $("antizipPauseOverlay"), antizipPauseBgSlider: $("antizipPauseBgSlider"), antizipPauseBgValue: $("antizipPauseBgValue"),
    antizipPauseBgColorPicker: $("antizipPauseBgColorPicker"), antizipResumeBtn: $("antizipResumeBtn"),
    antizipPlayerBar: $("antizipPlayerBar"), antizipBackBtn: $("antizipBackBtn"), antizipPauseBtn: $("antizipPauseBtn"), antizipProgressEl: $("antizipProgressEl"),
    antizipFsBtn: $("antizipFsBtn"), antizipFsHint: $("antizipFsHint"), antizipFsHintOpenBtn: $("antizipFsHintOpenBtn"), antizipFsHintClose: $("antizipFsHintClose"),
    antizipDonePanel: $("antizipDonePanel"), antizipDoneSummary: $("antizipDoneSummary"), antizipRating: $("antizipRating"),
    antizipAgainBtn: $("antizipAgainBtn"), antizipDoneBackBtn: $("antizipDoneBackBtn"),
    hickOpenBtn: $("hickOpenBtn"), hickBestHint: $("hickBestHint"), hickReady: $("hickReady"),
    hickReadyBackToHome: $("hickReadyBackToHome"), hickLengthRow: $("hickLengthRow"),
    hickAdvanced: $("hickAdvanced"), hickBgColorPicker: $("hickBgColorPicker"), hickBgIntensitySlider: $("hickBgIntensitySlider"),
    hickBgIntensityValue: $("hickBgIntensityValue"), hickBgContrastHint: $("hickBgContrastHint"),
    hickReadyBestHint: $("hickReadyBestHint"), hickReadyStartBtn: $("hickReadyStartBtn"),
    hickPlayer: $("hickPlayer"), hickStage: $("hickStage"), hickHint: $("hickHint"), hickBoxesGrid: $("hickBoxesGrid"),
    hickPauseOverlay: $("hickPauseOverlay"), hickResumeBtn: $("hickResumeBtn"),
    hickPauseBgColorPicker: $("hickPauseBgColorPicker"), hickPauseBgSlider: $("hickPauseBgSlider"), hickPauseBgValue: $("hickPauseBgValue"),
    hickPlayerBar: $("hickPlayerBar"), hickBackBtn: $("hickBackBtn"), hickPauseBtn: $("hickPauseBtn"), hickProgressEl: $("hickProgressEl"),
    hickFsBtn: $("hickFsBtn"), hickFsHint: $("hickFsHint"), hickFsHintOpenBtn: $("hickFsHintOpenBtn"), hickFsHintClose: $("hickFsHintClose"),
    hickDonePanel: $("hickDonePanel"), hickDoneSummary: $("hickDoneSummary"), hickRating: $("hickRating"),
    hickAgainBtn: $("hickAgainBtn"), hickDoneBackBtn: $("hickDoneBackBtn"),

    corsiOpenBtn: $("corsiOpenBtn"), corsiBestHint: $("corsiBestHint"), corsiReady: $("corsiReady"),
    corsiReadyBackToHome: $("corsiReadyBackToHome"), corsiDifficultyRow: $("corsiDifficultyRow"),
    corsiAdvanced: $("corsiAdvanced"), corsiBgColorPicker: $("corsiBgColorPicker"), corsiBgIntensitySlider: $("corsiBgIntensitySlider"),
    corsiBgIntensityValue: $("corsiBgIntensityValue"), corsiBgContrastHint: $("corsiBgContrastHint"),
    corsiReadyBestHint: $("corsiReadyBestHint"), corsiReadyStartBtn: $("corsiReadyStartBtn"),
    corsiPlayer: $("corsiPlayer"), corsiStage: $("corsiStage"), corsiHint: $("corsiHint"), corsiBoard: $("corsiBoard"),
    corsiPauseOverlay: $("corsiPauseOverlay"), corsiResumeBtn: $("corsiResumeBtn"),
    corsiPauseBgColorPicker: $("corsiPauseBgColorPicker"), corsiPauseBgSlider: $("corsiPauseBgSlider"), corsiPauseBgValue: $("corsiPauseBgValue"),
    corsiPlayerBar: $("corsiPlayerBar"), corsiBackBtn: $("corsiBackBtn"), corsiPauseBtn: $("corsiPauseBtn"), corsiProgressEl: $("corsiProgressEl"),
    corsiFsBtn: $("corsiFsBtn"), corsiFsHint: $("corsiFsHint"), corsiFsHintOpenBtn: $("corsiFsHintOpenBtn"), corsiFsHintClose: $("corsiFsHintClose"),
    corsiDonePanel: $("corsiDonePanel"), corsiDoneSummary: $("corsiDoneSummary"), corsiRating: $("corsiRating"),
    corsiAgainBtn: $("corsiAgainBtn"), corsiDoneBackBtn: $("corsiDoneBackBtn"),
    reaktOpenBtn: $("reaktOpenBtn"), reaktBestHint: $("reaktBestHint"), reaktReady: $("reaktReady"),
    reaktReadyBackToHome: $("reaktReadyBackToHome"), reaktModeRow: $("reaktModeRow"), reaktDifficultyRow: $("reaktDifficultyRow"),
    reaktLengthRow: $("reaktLengthRow"), reaktReadyBestHint: $("reaktReadyBestHint"), reaktReadyStartBtn: $("reaktReadyStartBtn"),
    reaktAdvanced: $("reaktAdvanced"), reaktBgColorPicker: $("reaktBgColorPicker"), reaktBgIntensitySlider: $("reaktBgIntensitySlider"),
    reaktBgIntensityValue: $("reaktBgIntensityValue"), reaktBgContrastHint: $("reaktBgContrastHint"),
    reaktPlayer: $("reaktPlayer"), reaktStage: $("reaktStage"), reaktHint: $("reaktHint"), reaktField: $("reaktField"),
    reaktPauseOverlay: $("reaktPauseOverlay"), reaktResumeBtn: $("reaktResumeBtn"),
    reaktPauseBgColorPicker: $("reaktPauseBgColorPicker"), reaktPauseBgSlider: $("reaktPauseBgSlider"), reaktPauseBgValue: $("reaktPauseBgValue"),
    reaktPlayerBar: $("reaktPlayerBar"), reaktBackBtn: $("reaktBackBtn"), reaktPauseBtn: $("reaktPauseBtn"), reaktProgressEl: $("reaktProgressEl"),
    reaktFsBtn: $("reaktFsBtn"), reaktFsHint: $("reaktFsHint"), reaktFsHintOpenBtn: $("reaktFsHintOpenBtn"), reaktFsHintClose: $("reaktFsHintClose"),
    reaktDonePanel: $("reaktDonePanel"), reaktDoneSummary: $("reaktDoneSummary"), reaktRating: $("reaktRating"),
    reaktAgainBtn: $("reaktAgainBtn"), reaktDoneBackBtn: $("reaktDoneBackBtn"),
    tsOpenBtn: $("tsOpenBtn"), tsBestHint: $("tsBestHint"), tsReady: $("tsReady"),
    tsReadyBackToHome: $("tsReadyBackToHome"), tsDifficultyRow: $("tsDifficultyRow"),
    tsAdvanced: $("tsAdvanced"), tsBgColorPicker: $("tsBgColorPicker"), tsBgIntensitySlider: $("tsBgIntensitySlider"),
    tsBgIntensityValue: $("tsBgIntensityValue"), tsBgContrastHint: $("tsBgContrastHint"),
    tsReadyBestHint: $("tsReadyBestHint"), tsReadyStartBtn: $("tsReadyStartBtn"),
    tsPlayer: $("tsPlayer"), tsStage: $("tsStage"), tsCue: $("tsCue"), tsStimulus: $("tsStimulus"), tsHint: $("tsHint"),
    tsLeftBtn: $("tsLeftBtn"), tsRightBtn: $("tsRightBtn"),
    tsPauseOverlay: $("tsPauseOverlay"), tsResumeBtn: $("tsResumeBtn"),
    tsPauseBgColorPicker: $("tsPauseBgColorPicker"), tsPauseBgSlider: $("tsPauseBgSlider"), tsPauseBgValue: $("tsPauseBgValue"),
    tsPlayerBar: $("tsPlayerBar"), tsBackBtn: $("tsBackBtn"), tsPauseBtn: $("tsPauseBtn"), tsProgressEl: $("tsProgressEl"),
    tsFsBtn: $("tsFsBtn"), tsFsHint: $("tsFsHint"), tsFsHintOpenBtn: $("tsFsHintOpenBtn"), tsFsHintClose: $("tsFsHintClose"),
    tsDonePanel: $("tsDonePanel"), tsDoneSummary: $("tsDoneSummary"), tsRating: $("tsRating"),
    tsAgainBtn: $("tsAgainBtn"), tsDoneBackBtn: $("tsDoneBackBtn"),
    antiOpenBtn: $("antiOpenBtn"), antiBestHint: $("antiBestHint"), antiReady: $("antiReady"),
    antiReadyBackToHome: $("antiReadyBackToHome"), antiDifficultyRow: $("antiDifficultyRow"),
    antiAdvanced: $("antiAdvanced"), antiBgColorPicker: $("antiBgColorPicker"), antiBgIntensitySlider: $("antiBgIntensitySlider"),
    antiBgIntensityValue: $("antiBgIntensityValue"), antiBgContrastHint: $("antiBgContrastHint"),
    antiReadyBestHint: $("antiReadyBestHint"), antiReadyStartBtn: $("antiReadyStartBtn"),
    antiPlayer: $("antiPlayer"), antiStage: $("antiStage"), antiRule: $("antiRule"), antiHint: $("antiHint"),
    antiSlotLeft: $("antiSlotLeft"), antiDotLeft: $("antiDotLeft"), antiSlotRight: $("antiSlotRight"), antiDotRight: $("antiDotRight"),
    antiLeftBtn: $("antiLeftBtn"), antiRightBtn: $("antiRightBtn"),
    antiPauseOverlay: $("antiPauseOverlay"), antiResumeBtn: $("antiResumeBtn"),
    antiPauseBgColorPicker: $("antiPauseBgColorPicker"), antiPauseBgSlider: $("antiPauseBgSlider"), antiPauseBgValue: $("antiPauseBgValue"),
    antiPlayerBar: $("antiPlayerBar"), antiBackBtn: $("antiBackBtn"), antiPauseBtn: $("antiPauseBtn"), antiProgressEl: $("antiProgressEl"),
    antiFsBtn: $("antiFsBtn"), antiFsHint: $("antiFsHint"), antiFsHintOpenBtn: $("antiFsHintOpenBtn"), antiFsHintClose: $("antiFsHintClose"),
    antiDonePanel: $("antiDonePanel"), antiDoneSummary: $("antiDoneSummary"), antiRating: $("antiRating"),
    antiAgainBtn: $("antiAgainBtn"), antiDoneBackBtn: $("antiDoneBackBtn"),
    stroopOpenBtn: $("stroopOpenBtn"), stroopBestHint: $("stroopBestHint"), stroopReady: $("stroopReady"),
    stroopReadyBackToHome: $("stroopReadyBackToHome"), stroopDifficultyRow: $("stroopDifficultyRow"),
    stroopReadyBestHint: $("stroopReadyBestHint"), stroopReadyStartBtn: $("stroopReadyStartBtn"),
    stroopPlayer: $("stroopPlayer"), stroopStage: $("stroopStage"), stroopHint: $("stroopHint"), stroopWord: $("stroopWord"),
    stroopResponseRow: $("stroopResponseRow"),
    stroopPauseOverlay: $("stroopPauseOverlay"), stroopResumeBtn: $("stroopResumeBtn"),
    stroopPlayerBar: $("stroopPlayerBar"), stroopBackBtn: $("stroopBackBtn"), stroopPauseBtn: $("stroopPauseBtn"), stroopProgressEl: $("stroopProgressEl"),
    stroopFsBtn: $("stroopFsBtn"), stroopFsHint: $("stroopFsHint"), stroopFsHintOpenBtn: $("stroopFsHintOpenBtn"), stroopFsHintClose: $("stroopFsHintClose"),
    stroopDonePanel: $("stroopDonePanel"), stroopDoneSummary: $("stroopDoneSummary"), stroopRating: $("stroopRating"),
    stroopAgainBtn: $("stroopAgainBtn"), stroopDoneBackBtn: $("stroopDoneBackBtn"),
    rotationOpenBtn: $("rotationOpenBtn"), rotationBestHint: $("rotationBestHint"), rotationReady: $("rotationReady"),
    rotationReadyBackToHome: $("rotationReadyBackToHome"), rotationDifficultyRow: $("rotationDifficultyRow"),
    rotationAdvanced: $("rotationAdvanced"), rotationBgColorPicker: $("rotationBgColorPicker"), rotationBgIntensitySlider: $("rotationBgIntensitySlider"),
    rotationBgIntensityValue: $("rotationBgIntensityValue"), rotationBgContrastHint: $("rotationBgContrastHint"),
    rotationReadyBestHint: $("rotationReadyBestHint"), rotationReadyStartBtn: $("rotationReadyStartBtn"),
    rotationPlayer: $("rotationPlayer"), rotationStage: $("rotationStage"), rotationHint: $("rotationHint"),
    rotationCharEl: $("rotationCharEl"), rotationNormalBtn: $("rotationNormalBtn"), rotationMirroredBtn: $("rotationMirroredBtn"),
    rotationPauseOverlay: $("rotationPauseOverlay"), rotationPauseBgSlider: $("rotationPauseBgSlider"), rotationPauseBgValue: $("rotationPauseBgValue"),
    rotationPauseBgColorPicker: $("rotationPauseBgColorPicker"), rotationResumeBtn: $("rotationResumeBtn"),
    rotationPlayerBar: $("rotationPlayerBar"), rotationBackBtn: $("rotationBackBtn"), rotationPauseBtn: $("rotationPauseBtn"), rotationProgressEl: $("rotationProgressEl"),
    rotationFsBtn: $("rotationFsBtn"), rotationFsHint: $("rotationFsHint"), rotationFsHintOpenBtn: $("rotationFsHintOpenBtn"), rotationFsHintClose: $("rotationFsHintClose"),
    rotationDonePanel: $("rotationDonePanel"), rotationDoneSummary: $("rotationDoneSummary"), rotationRating: $("rotationRating"),
    rotationAgainBtn: $("rotationAgainBtn"), rotationDoneBackBtn: $("rotationDoneBackBtn"),
    merkOpenBtn: $("merkOpenBtn"), merkBestHint: $("merkBestHint"), merkReady: $("merkReady"),
    merkReadyBackToHome: $("merkReadyBackToHome"), merkDifficultyRow: $("merkDifficultyRow"),
    merkAdvanced: $("merkAdvanced"), merkBgColorPicker: $("merkBgColorPicker"), merkBgIntensitySlider: $("merkBgIntensitySlider"),
    merkBgIntensityValue: $("merkBgIntensityValue"), merkBgContrastHint: $("merkBgContrastHint"),
    merkReadyBestHint: $("merkReadyBestHint"), merkReadyStartBtn: $("merkReadyStartBtn"),
    merkPlayer: $("merkPlayer"), merkStage: $("merkStage"), merkHint: $("merkHint"), merkField: $("merkField"),
    merkSameBtn: $("merkSameBtn"), merkChangedBtn: $("merkChangedBtn"),
    merkPauseOverlay: $("merkPauseOverlay"), merkPauseBgSlider: $("merkPauseBgSlider"), merkPauseBgValue: $("merkPauseBgValue"),
    merkPauseBgColorPicker: $("merkPauseBgColorPicker"), merkResumeBtn: $("merkResumeBtn"),
    merkPlayerBar: $("merkPlayerBar"), merkBackBtn: $("merkBackBtn"), merkPauseBtn: $("merkPauseBtn"), merkProgressEl: $("merkProgressEl"),
    merkFsBtn: $("merkFsBtn"), merkFsHint: $("merkFsHint"), merkFsHintOpenBtn: $("merkFsHintOpenBtn"), merkFsHintClose: $("merkFsHintClose"),
    merkDonePanel: $("merkDonePanel"), merkDoneSummary: $("merkDoneSummary"), merkRating: $("merkRating"),
    merkAgainBtn: $("merkAgainBtn"), merkDoneBackBtn: $("merkDoneBackBtn"),
    blitzOpenBtn: $("blitzOpenBtn"), blitzBestHint: $("blitzBestHint"), blitzReady: $("blitzReady"),
    blitzReadyBackToHome: $("blitzReadyBackToHome"), blitzGridSizeRow: $("blitzGridSizeRow"),
    blitzZoneGroup: $("blitzZoneGroup"), blitzZoneAllBtn: $("blitzZoneAllBtn"), blitzZoneGrid: $("blitzZoneGrid"), blitzZoneHint: $("blitzZoneHint"),
    blitzDifficultyRow: $("blitzDifficultyRow"), blitzDiffCustom: $("blitzDiffCustom"), blitzErrorRow: $("blitzErrorRow"),
    blitzAdvanced: $("blitzAdvanced"), blitzFlashSlider: $("blitzFlashSlider"), blitzFlashValue: $("blitzFlashValue"),
    blitzStartSlider: $("blitzStartSlider"), blitzStartValue: $("blitzStartValue"),
    blitzBgColorPicker: $("blitzBgColorPicker"), blitzBgIntensitySlider: $("blitzBgIntensitySlider"),
    blitzBgIntensityValue: $("blitzBgIntensityValue"), blitzBgContrastHint: $("blitzBgContrastHint"),
    blitzBgSourceRow: $("blitzBgSourceRow"), blitzBgPresetGroup: $("blitzBgPresetGroup"), blitzBgPresetList: $("blitzBgPresetList"),
    blitzBgSaveBtn: $("blitzBgSaveBtn"), blitzBgSaveForm: $("blitzBgSaveForm"), blitzBgSaveNameInput: $("blitzBgSaveNameInput"),
    blitzBgSaveCancelBtn: $("blitzBgSaveCancelBtn"), blitzBgSaveConfirmBtn: $("blitzBgSaveConfirmBtn"),
    blitzReadyBestHint: $("blitzReadyBestHint"), blitzReadyStartBtn: $("blitzReadyStartBtn"),
    blitzPlayer: $("blitzPlayer"), blitzStage: $("blitzStage"), blitzHint: $("blitzHint"), blitzGrid: $("blitzGrid"),
    blitzPauseOverlay: $("blitzPauseOverlay"), blitzPauseBgSlider: $("blitzPauseBgSlider"), blitzPauseBgValue: $("blitzPauseBgValue"),
    blitzPauseBgColorPicker: $("blitzPauseBgColorPicker"), blitzResumeBtn: $("blitzResumeBtn"),
    blitzPlayerBar: $("blitzPlayerBar"), blitzBackBtn: $("blitzBackBtn"), blitzPauseBtn: $("blitzPauseBtn"), blitzLevelEl: $("blitzLevelEl"),
    blitzFsBtn: $("blitzFsBtn"), blitzFsHint: $("blitzFsHint"), blitzFsHintOpenBtn: $("blitzFsHintOpenBtn"), blitzFsHintClose: $("blitzFsHintClose"),
    blitzDonePanel: $("blitzDonePanel"), blitzDoneSummary: $("blitzDoneSummary"), blitzRating: $("blitzRating"),
    blitzAgainBtn: $("blitzAgainBtn"), blitzDoneBackBtn: $("blitzDoneBackBtn"),
    flashOpenConstant: $("flashOpenConstant"), flashOpenClimb: $("flashOpenClimb"), flashOpenClimbRepeat: $("flashOpenClimbRepeat"), flashOpenTraining: $("flashOpenTraining"),
    flashBestConstant: $("flashBestConstant"), flashBestClimb: $("flashBestClimb"), flashBestClimbRepeat: $("flashBestClimbRepeat"), flashBestTraining: $("flashBestTraining"),
    flashReady: $("flashReady"), flashReadyBackToHome: $("flashReadyBackToHome"), flashReadyTitle: $("flashReadyTitle"), flashReadyDesc: $("flashReadyDesc"),
    flashFieldRow: $("flashFieldRow"), flashAllBtn: $("flashAllBtn"), flashFieldHint: $("flashFieldHint"), flashZonesBtn: $("flashZonesBtn"), flashZoneGrid: $("flashZoneGrid"),
    flashDifficultyRow: $("flashDifficultyRow"), flashDiffCustom: $("flashDiffCustom"), flashErrorRow: $("flashErrorRow"),
    flashConstantGroup: $("flashConstantGroup"), flashConstantSlider: $("flashConstantSlider"), flashConstantValue: $("flashConstantValue"),
    flashStartGroup: $("flashStartGroup"), flashStartSlider: $("flashStartSlider"), flashStartValue: $("flashStartValue"),
    flashRepsGroup: $("flashRepsGroup"), flashRepsSlider: $("flashRepsSlider"), flashRepsValue: $("flashRepsValue"),
    flashAdvanced: $("flashAdvanced"), flashStimulusSlider: $("flashStimulusSlider"), flashStimulusValue: $("flashStimulusValue"),
    flashIntervalSlider: $("flashIntervalSlider"), flashIntervalValue: $("flashIntervalValue"),
    flashBgColorPicker: $("flashBgColorPicker"), flashBgIntensitySlider: $("flashBgIntensitySlider"),
    flashBgIntensityValue: $("flashBgIntensityValue"), flashBgContrastHint: $("flashBgContrastHint"),
    flashBgSourceRow: $("flashBgSourceRow"), flashBgPresetGroup: $("flashBgPresetGroup"), flashBgPresetList: $("flashBgPresetList"),
    flashBgSaveBtn: $("flashBgSaveBtn"), flashBgSaveForm: $("flashBgSaveForm"), flashBgSaveNameInput: $("flashBgSaveNameInput"),
    flashBgSaveCancelBtn: $("flashBgSaveCancelBtn"), flashBgSaveConfirmBtn: $("flashBgSaveConfirmBtn"),
    flashReadyBestHint: $("flashReadyBestHint"), flashReadyStartBtn: $("flashReadyStartBtn"),
    flashTrainingReady: $("flashTrainingReady"), flashTrainingBackToHome: $("flashTrainingBackToHome"),
    flashTrainingStartSlider: $("flashTrainingStartSlider"), flashTrainingStartValue: $("flashTrainingStartValue"),
    flashTrainingProgressRow: $("flashTrainingProgressRow"),
    flashTrainingFieldRow: $("flashTrainingFieldRow"), flashTrainingAllBtn: $("flashTrainingAllBtn"), flashTrainingFieldHint: $("flashTrainingFieldHint"),
    flashTrainingZonesBtn: $("flashTrainingZonesBtn"), flashTrainingZoneGrid: $("flashTrainingZoneGrid"),
    flashTrainingAdvanced: $("flashTrainingAdvanced"), flashTrainingStimulusSlider: $("flashTrainingStimulusSlider"), flashTrainingStimulusValue: $("flashTrainingStimulusValue"),
    flashTrainingIntervalSlider: $("flashTrainingIntervalSlider"), flashTrainingIntervalValue: $("flashTrainingIntervalValue"),
    flashTrainingBgColorPicker: $("flashTrainingBgColorPicker"), flashTrainingBgIntensitySlider: $("flashTrainingBgIntensitySlider"),
    flashTrainingBgIntensityValue: $("flashTrainingBgIntensityValue"), flashTrainingBgContrastHint: $("flashTrainingBgContrastHint"),
    flashTrainingBgSourceRow: $("flashTrainingBgSourceRow"), flashTrainingBgPresetGroup: $("flashTrainingBgPresetGroup"), flashTrainingBgPresetList: $("flashTrainingBgPresetList"),
    flashTrainingBgSaveBtn: $("flashTrainingBgSaveBtn"), flashTrainingBgSaveForm: $("flashTrainingBgSaveForm"), flashTrainingBgSaveNameInput: $("flashTrainingBgSaveNameInput"),
    flashTrainingBgSaveCancelBtn: $("flashTrainingBgSaveCancelBtn"), flashTrainingBgSaveConfirmBtn: $("flashTrainingBgSaveConfirmBtn"),
    flashTrainingBestHint: $("flashTrainingBestHint"), flashTrainingStartBtn: $("flashTrainingStartBtn"),
    flashPlayer: $("flashPlayer"), flashStage: $("flashStage"), flashHint: $("flashHint"), flashDigitEl: $("flashDigitEl"),
    flashInputPanel: $("flashInputPanel"), flashInputLabel: $("flashInputLabel"),
    flashAnswerBoxes: $("flashAnswerBoxes"), flashKeypad: $("flashKeypad"), flashBackspaceBtn: $("flashBackspaceBtn"),
    flashKindRow: $("flashKindRow"), flashTrainingKindRow: $("flashTrainingKindRow"),
    flashPauseOverlay: $("flashPauseOverlay"), flashPauseBgSlider: $("flashPauseBgSlider"), flashPauseBgValue: $("flashPauseBgValue"),
    flashPauseBgColorPicker: $("flashPauseBgColorPicker"), flashResumeBtn: $("flashResumeBtn"),
    flashPlayerBar: $("flashPlayerBar"), flashBackBtn: $("flashBackBtn"), flashPauseBtn: $("flashPauseBtn"), flashLevelEl: $("flashLevelEl"),
    flashFsBtn: $("flashFsBtn"), flashFsHint: $("flashFsHint"), flashFsHintOpenBtn: $("flashFsHintOpenBtn"), flashFsHintClose: $("flashFsHintClose"),
    flashDonePanel: $("flashDonePanel"), flashDoneSummary: $("flashDoneSummary"), flashRating: $("flashRating"),
    flashAgainBtn: $("flashAgainBtn"), flashDoneBackBtn: $("flashDoneBackBtn"),
    flashFixGroup: $("flashFixGroup"), flashFixToggleRow: $("flashFixToggleRow"), flashFixOptions: $("flashFixOptions"),
    flashFixCharInput: $("flashFixCharInput"), flashFixColorPicker: $("flashFixColorPicker"),
    flashFixSizeSlider: $("flashFixSizeSlider"), flashFixSizeValue: $("flashFixSizeValue"),
    flashTrainingFixGroup: $("flashTrainingFixGroup"), flashTrainingFixToggleRow: $("flashTrainingFixToggleRow"), flashTrainingFixOptions: $("flashTrainingFixOptions"),
    flashTrainingFixCharInput: $("flashTrainingFixCharInput"), flashTrainingFixColorPicker: $("flashTrainingFixColorPicker"),
    flashTrainingFixSizeSlider: $("flashTrainingFixSizeSlider"), flashTrainingFixSizeValue: $("flashTrainingFixSizeValue"),
    flashFixpointEl: $("flashFixpointEl"),

    motOpenSpeed: $("motOpenSpeed"), motBestSpeed: $("motBestSpeed"),
    motOpenCount: $("motOpenCount"), motBestCount: $("motBestCount"),
    motOpenBoth: $("motOpenBoth"), motBestBoth: $("motBestBoth"),
    motOpenTraining: $("motOpenTraining"), motBestTraining: $("motBestTraining"),
    motReady: $("motReady"), motReadyBackToHome: $("motReadyBackToHome"),
    motReadyTitle: $("motReadyTitle"), motReadyDesc: $("motReadyDesc"),
    motStyleRow: $("motStyleRow"), motColorPicker: $("motColorPicker"), motColorHint: $("motColorHint"),
    motTargetColorPicker: $("motTargetColorPicker"), motTargetColorHint: $("motTargetColorHint"),
    motDifficultyRow: $("motDifficultyRow"), motDiffCustom: $("motDiffCustom"),
    motErrorRow: $("motErrorRow"),
    motFixedCountGroup: $("motFixedCountGroup"),
    motObjectsSlider: $("motObjectsSlider"), motObjectsValue: $("motObjectsValue"),
    motTargetsSlider: $("motTargetsSlider"), motTargetsValue: $("motTargetsValue"),
    motGrowStartGroup: $("motGrowStartGroup"),
    motGrowObjectsSlider: $("motGrowObjectsSlider"), motGrowObjectsValue: $("motGrowObjectsValue"),
    motGrowTargetsSlider: $("motGrowTargetsSlider"), motGrowTargetsValue: $("motGrowTargetsValue"),
    motAdvanced: $("motAdvanced"),
    motSpeedSlider: $("motSpeedSlider"), motSpeedValue: $("motSpeedValue"),
    motTrackSlider: $("motTrackSlider"), motTrackValue: $("motTrackValue"),
    motHighlightSlider: $("motHighlightSlider"), motHighlightValue: $("motHighlightValue"),
    motBgColorPicker: $("motBgColorPicker"), motBgIntensitySlider: $("motBgIntensitySlider"),
    motBgIntensityValue: $("motBgIntensityValue"), motBgContrastHint: $("motBgContrastHint"),
    motBgSourceRow: $("motBgSourceRow"), motBgPresetGroup: $("motBgPresetGroup"), motBgPresetList: $("motBgPresetList"),
    motBgSaveBtn: $("motBgSaveBtn"), motBgSaveForm: $("motBgSaveForm"), motBgSaveNameInput: $("motBgSaveNameInput"),
    motBgSaveCancelBtn: $("motBgSaveCancelBtn"), motBgSaveConfirmBtn: $("motBgSaveConfirmBtn"),
    motReadyBestHint: $("motReadyBestHint"), motReadyStartBtn: $("motReadyStartBtn"),
    motTrainingReady: $("motTrainingReady"), motTrainingBackToHome: $("motTrainingBackToHome"),
    motTrainingObjectsSlider: $("motTrainingObjectsSlider"), motTrainingObjectsValue: $("motTrainingObjectsValue"),
    motTrainingTargetsSlider: $("motTrainingTargetsSlider"), motTrainingTargetsValue: $("motTrainingTargetsValue"),
    motTrainingSpeedStepSlider: $("motTrainingSpeedStepSlider"), motTrainingSpeedStepValue: $("motTrainingSpeedStepValue"),
    motTrainingProgressRow: $("motTrainingProgressRow"),
    motTrainingStyleRow: $("motTrainingStyleRow"),
    motTrainingColorPicker: $("motTrainingColorPicker"), motTrainingColorHint: $("motTrainingColorHint"),
    motTrainingTargetColorPicker: $("motTrainingTargetColorPicker"), motTrainingTargetColorHint: $("motTrainingTargetColorHint"),
    motTrainingAdvanced: $("motTrainingAdvanced"),
    motTrainingSpeedSlider: $("motTrainingSpeedSlider"), motTrainingSpeedValue: $("motTrainingSpeedValue"),
    motTrainingTrackSlider: $("motTrainingTrackSlider"), motTrainingTrackValue: $("motTrainingTrackValue"),
    motTrainingHighlightSlider: $("motTrainingHighlightSlider"), motTrainingHighlightValue: $("motTrainingHighlightValue"),
    motTrainingBgColorPicker: $("motTrainingBgColorPicker"), motTrainingBgIntensitySlider: $("motTrainingBgIntensitySlider"),
    motTrainingBgIntensityValue: $("motTrainingBgIntensityValue"), motTrainingBgContrastHint: $("motTrainingBgContrastHint"),
    motTrainingBgSourceRow: $("motTrainingBgSourceRow"), motTrainingBgPresetGroup: $("motTrainingBgPresetGroup"), motTrainingBgPresetList: $("motTrainingBgPresetList"),
    motTrainingBgSaveBtn: $("motTrainingBgSaveBtn"), motTrainingBgSaveForm: $("motTrainingBgSaveForm"), motTrainingBgSaveNameInput: $("motTrainingBgSaveNameInput"),
    motTrainingBgSaveCancelBtn: $("motTrainingBgSaveCancelBtn"), motTrainingBgSaveConfirmBtn: $("motTrainingBgSaveConfirmBtn"),
    motTrainingBestHint: $("motTrainingBestHint"), motTrainingStartBtn: $("motTrainingStartBtn"),
    motPlayer: $("motPlayer"), motStage: $("motStage"), motHint: $("motHint"), motObjectsLayer: $("motObjectsLayer"),
    motPauseOverlay: $("motPauseOverlay"), motPauseBgSlider: $("motPauseBgSlider"), motPauseBgValue: $("motPauseBgValue"),
    motPauseBgColorPicker: $("motPauseBgColorPicker"), motResumeBtn: $("motResumeBtn"),
    motPlayerBar: $("motPlayerBar"), motBackBtn: $("motBackBtn"), motPauseBtn: $("motPauseBtn"), motLevelEl: $("motLevelEl"),
    motFsBtn: $("motFsBtn"), motFsHint: $("motFsHint"), motFsHintOpenBtn: $("motFsHintOpenBtn"), motFsHintClose: $("motFsHintClose"),
    motDonePanel: $("motDonePanel"), motDoneSummary: $("motDoneSummary"), motRating: $("motRating"),
    motAgainBtn: $("motAgainBtn"), motDoneBackBtn: $("motDoneBackBtn"),
    rememberOpenFixed: $("rememberOpenFixed"), rememberOpenShuffle: $("rememberOpenShuffle"), rememberOpenTraining: $("rememberOpenTraining"),
    rememberBestFixed: $("rememberBestFixed"), rememberBestShuffle: $("rememberBestShuffle"), rememberBestTraining: $("rememberBestTraining"),
    rememberReady: $("rememberReady"), rememberReadyBackToHome: $("rememberReadyBackToHome"),
    rememberReadyTitle: $("rememberReadyTitle"), rememberReadyDesc: $("rememberReadyDesc"),
    rememberDiffCustom: $("rememberDiffCustom"), rememberRevealSlider: $("rememberRevealSlider"), rememberRevealValue: $("rememberRevealValue"),
    rememberStepSlider: $("rememberStepSlider"), rememberStepValue: $("rememberStepValue"),
    rememberReadyBestHint: $("rememberReadyBestHint"), rememberReadyStartBtn: $("rememberReadyStartBtn"),
    rememberTrainingReady: $("rememberTrainingReady"), rememberTrainingBackToHome: $("rememberTrainingBackToHome"),
    rememberStartSlider: $("rememberStartSlider"), rememberStartValue: $("rememberStartValue"),
    rememberTrainingDiffCustom: $("rememberTrainingDiffCustom"),
    rememberTrainingRevealSlider: $("rememberTrainingRevealSlider"), rememberTrainingRevealValue: $("rememberTrainingRevealValue"),
    rememberTrainingStepSlider: $("rememberTrainingStepSlider"), rememberTrainingStepValue: $("rememberTrainingStepValue"),
    rememberTrainingBestHint: $("rememberTrainingBestHint"), rememberTrainingStartBtn: $("rememberTrainingStartBtn"),
    rememberBgColorPicker: $("rememberBgColorPicker"), rememberBgIntensitySlider: $("rememberBgIntensitySlider"),
    rememberBgIntensityValue: $("rememberBgIntensityValue"), rememberBgContrastHint: $("rememberBgContrastHint"),
    rememberBgSourceRow: $("rememberBgSourceRow"), rememberBgPresetGroup: $("rememberBgPresetGroup"), rememberBgPresetList: $("rememberBgPresetList"),
    rememberBgSaveBtn: $("rememberBgSaveBtn"), rememberBgSaveForm: $("rememberBgSaveForm"), rememberBgSaveNameInput: $("rememberBgSaveNameInput"),
    rememberBgSaveCancelBtn: $("rememberBgSaveCancelBtn"), rememberBgSaveConfirmBtn: $("rememberBgSaveConfirmBtn"),
    rememberTrainingBgColorPicker: $("rememberTrainingBgColorPicker"), rememberTrainingBgIntensitySlider: $("rememberTrainingBgIntensitySlider"),
    rememberTrainingBgIntensityValue: $("rememberTrainingBgIntensityValue"), rememberTrainingBgContrastHint: $("rememberTrainingBgContrastHint"),
    rememberTrainingBgSourceRow: $("rememberTrainingBgSourceRow"), rememberTrainingBgPresetGroup: $("rememberTrainingBgPresetGroup"), rememberTrainingBgPresetList: $("rememberTrainingBgPresetList"),
    rememberTrainingBgSaveBtn: $("rememberTrainingBgSaveBtn"), rememberTrainingBgSaveForm: $("rememberTrainingBgSaveForm"), rememberTrainingBgSaveNameInput: $("rememberTrainingBgSaveNameInput"),
    rememberTrainingBgSaveCancelBtn: $("rememberTrainingBgSaveCancelBtn"), rememberTrainingBgSaveConfirmBtn: $("rememberTrainingBgSaveConfirmBtn"),
    rememberPlayer: $("rememberPlayer"), rememberStage: $("rememberStage"), rememberHint: $("rememberHint"),
    rememberNav: $("rememberNav"), rememberNavPrevBtn: $("rememberNavPrevBtn"), rememberNavRestartBtn: $("rememberNavRestartBtn"), rememberNavNextBtn: $("rememberNavNextBtn"),
    rememberPlayerBar: $("rememberPlayerBar"), rememberBackBtn: $("rememberBackBtn"), rememberLevelEl: $("rememberLevelEl"),
    rememberPauseBtn: $("rememberPauseBtn"), rememberPauseOverlay: $("rememberPauseOverlay"),
    rememberPauseBgSlider: $("rememberPauseBgSlider"), rememberPauseBgValue: $("rememberPauseBgValue"),
    rememberPauseBgColorPicker: $("rememberPauseBgColorPicker"), rememberResumeBtn: $("rememberResumeBtn"),
    rememberFsBtn: $("rememberFsBtn"), rememberFsHint: $("rememberFsHint"),
    rememberFsHintOpenBtn: $("rememberFsHintOpenBtn"), rememberFsHintClose: $("rememberFsHintClose"),
    rememberDonePanel: $("rememberDonePanel"), rememberDoneSummary: $("rememberDoneSummary"), rememberRating: $("rememberRating"),
    rememberAgainBtn: $("rememberAgainBtn"), rememberDoneBackBtn: $("rememberDoneBackBtn"),
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
    tabataExerciseCustomNote: $("tabataExerciseCustomNote"),
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
    comboSaveForm: $("comboSaveForm"), comboSaveCancelBtn: $("comboSaveCancelBtn"), comboSaveConfirmBtn: $("comboSaveConfirmBtn"),
    comboTransition: $("comboTransition"), comboTransitionTitle: $("comboTransitionTitle"), comboTransitionMeta: $("comboTransitionMeta"), comboTransitionBtn: $("comboTransitionBtn"),
    comboDonePanel: $("comboDonePanel"), comboDoneSummary: $("comboDoneSummary"), comboRating: $("comboRating"),
    comboAgainBtn: $("comboAgainBtn"), comboDoneBackBtn: $("comboDoneBackBtn"),
  };

  const SCREENS = ["home", "breathHome", "movementHome", "workoutHome", "natHome", "testHome", "bundleOverview", "programIntro", "ready", "breathReady", "breathBundleOverview", "breathProgramIntro", "wimhofReady", "movementReady", "workoutBundleOverview", "workoutProgramIntro", "workoutTabataReady", "comboScreen", "comboBundleOverview", "rememberReady", "rememberTrainingReady", "blitzReady", "flashReady", "flashTrainingReady", "motReady", "motTrainingReady", "gngReady", "testNbackReady", "trailReady", "flankerReady", "ufovReady", "posnerReady", "rotationReady", "merkReady", "simonReady", "searchReady", "abReady", "antizipReady", "hickReady", "corsiReady", "reaktReady", "tsReady", "antiReady", "stroopReady"];
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
      showScreen(sec === "breath" ? "breathHome" : sec === "movement" ? "movementHome" : sec === "workout" ? "workoutHome" : sec === "nat" ? "natHome" : sec === "test" ? "testHome" : "home");
    });
  });

  // ---- NAT sub-navigation (second-level tabs within the NAT section) ----
  document.querySelectorAll(".sub-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      const sub = btn.dataset.natSub;
      document.querySelectorAll(".sub-tab").forEach((b) => {
        const on = b.dataset.natSub === sub;
        setActive(b, on);
        b.setAttribute("aria-selected", on ? "true" : "false");
      });
      els.natPeripherPanel.hidden = sub !== "peripher";
      els.natRememberPanel.hidden = sub !== "remember";
      els.natBlitzPanel.hidden = sub !== "blitz";
      els.natFlashPanel.hidden = sub !== "flash";
      els.natMotPanel.hidden = sub !== "mot";
      if (sub === "remember") renderRememberBests();
      if (sub === "blitz") renderBlitzBest();
      if (sub === "flash") renderFlashBests();
      if (sub === "mot") renderMotBests();
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
  const HISTORY_VISIBLE_SHORT = 3;
  const HISTORY_VISIBLE_EXPANDED = 200; // effectively "all" - addHistory() itself caps storage at 200
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

  // ---- Shared top-clearance measurement for every full-stage exercise
  // (Remember/Blitz-Raster/Flash/Trail/Search/Corsi/Reaktionsfeld etc.) -
  // their stage fills the whole player from y=0, with the instruction hint
  // (".remember-hint", short status blips OR - since Trail Making Test's
  // real bug report - a much longer, wrapping instruction sentence) and the
  // player-bar floating on top via z-index. A hardcoded pixel minY can't
  // account for wrapped-hint height (varies with instruction length) or
  // safe-area notch size (varies per device), so every exercise that
  // scatters markers/targets across its whole stage should measure the
  // hint's and bar's real rendered bottom edge instead. Falls back to
  // fallbackMinY only while the stage isn't actually laid out yet
  // (rect.height === 0, e.g. read before the player is unhidden).
  // IMPORTANT: the returned value is meant to be used as a constraint on a
  // marker's CENTRE y - every caller positions markers via translate(-50%,
  // -50%), so the marker's own rendered TOP edge sits `halfSizePx` above its
  // centre. Without adding halfSizePx here, a centre placed exactly at the
  // hint's measured bottom edge would still visually overlap it by
  // (halfSizePx - marginPx); this bit past every caller the first time
  // (caught via a repeated Playwright run, not a single deterministic one -
  // the overlap only happens for markers whose random draw lands near this
  // boundary, so a single-shot test can easily miss it).
  function stageTopClearanceY(stageRect, hintEl, barEl, fallbackMinY, halfSizePx = 0, marginPx = 16) {
    if (!stageRect.height) return fallbackMinY;
    const hintRect = hintEl.getBoundingClientRect();
    const barRect = barEl.getBoundingClientRect();
    return Math.max(fallbackMinY, Math.max(hintRect.bottom, barRect.bottom) - stageRect.top + halfSizePx + marginPx);
  }

  // ---- Swipe navigation: lets a left/right swipe trigger the same action as
  // an existing prev/next button, wherever paging through a fixed sequence
  // (slides, chapters) makes sense. Reuses the button's own .click() so
  // disabled state (start/end of the sequence) is respected for free.
  function wireSwipeNav(el, { onLeft, onRight, thresholdPx = 40 } = {}) {
    let startX = 0, startY = 0, tracking = false;
    el.addEventListener("touchstart", (e) => {
      if (e.touches.length !== 1) return;
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      tracking = true;
    }, { passive: true });
    el.addEventListener("touchend", (e) => {
      if (!tracking) return;
      tracking = false;
      const dx = e.changedTouches[0].clientX - startX;
      const dy = e.changedTouches[0].clientY - startY;
      if (Math.abs(dx) < thresholdPx || Math.abs(dx) < Math.abs(dy) * 1.5) return;
      if (dx < 0) onLeft && onLeft();
      else onRight && onRight();
    }, { passive: true });
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

  // ---- Setup diagrams (e.g. Hütchen-Kompass-Aufbau): small SVG sketches ----
  // showing how the physical cone layout on the ground can look, since this
  // exercise has no fixed setup - the player builds it themselves.
  function coneSetupSVG(points) {
    const size = 220, cx = size / 2, cy = size / 2, r = 78;
    let lines = "", cones = "";
    points.forEach((p) => {
      const rad = ((p.angle - 90) * Math.PI) / 180;
      const ex = cx + r * Math.cos(rad), ey = cy + r * Math.sin(rad);
      lines += `<line x1="${cx}" y1="${cy}" x2="${ex.toFixed(1)}" y2="${ey.toFixed(1)}" stroke="var(--line)" stroke-width="2" stroke-dasharray="4 4"/>`;
      const perpX = -Math.sin(rad), perpY = Math.cos(rad);
      const n = p.colors.length;
      p.colors.forEach((color, i) => {
        const spread = (i - (n - 1) / 2) * 20;
        const x = (ex + perpX * spread).toFixed(1), y = (ey + perpY * spread).toFixed(1);
        cones += `<g transform="translate(${x},${y})"><circle r="13" fill="${color}" stroke="rgba(0,0,0,.15)" stroke-width="1.5"/><polygon points="0,-6 5,6 -5,6" fill="#fff" opacity=".9"/></g>`;
      });
    });
    return `<svg viewBox="0 0 ${size} ${size}" class="setup-svg" role="img" aria-hidden="true">
      <circle cx="${cx}" cy="${cy}" r="${r + 24}" fill="var(--surface-2)"/>
      ${lines}
      <circle cx="${cx}" cy="${cy}" r="15" fill="var(--brand)"/>
      <text x="${cx}" y="${cy + 4.5}" text-anchor="middle" font-size="11" font-weight="700" fill="#fff">DU</text>
      ${cones}
    </svg>`;
  }
  const SETUP_SLIDES = [
    {
      title: "Kreuz · 4 Richtungen",
      caption: "Klebe ein einfaches Kreuz auf den Boden – vorne, rechts, hinten, links – und stelle in jede Richtung ein Hütchen in einer eigenen Farbe.",
      points: [
        { angle: 0, colors: [COLOR_BY_KEY.rot.hex] },
        { angle: 90, colors: [COLOR_BY_KEY.gruen.hex] },
        { angle: 180, colors: [COLOR_BY_KEY.blau.hex] },
        { angle: 270, colors: [COLOR_BY_KEY.gelb.hex] },
      ],
    },
    {
      title: "Kompass · 8 Richtungen (Kreuz + Diagonale)",
      caption: "Ergänze die vier Schrägen, um alle acht Richtungen zu trainieren – ein Hütchen pro Richtung.",
      points: [
        { angle: 0, colors: [COLOR_BY_KEY.rot.hex] },
        { angle: 45, colors: [COLOR_BY_KEY.orange.hex] },
        { angle: 90, colors: [COLOR_BY_KEY.gruen.hex] },
        { angle: 135, colors: [COLOR_BY_KEY.lila.hex] },
        { angle: 180, colors: [COLOR_BY_KEY.blau.hex] },
        { angle: 225, colors: [COLOR_BY_KEY.pink.hex] },
        { angle: 270, colors: [COLOR_BY_KEY.gelb.hex] },
        { angle: 315, colors: [COLOR_BY_KEY.rot.hex] },
      ],
    },
    {
      title: "Eigene Auswahl – nur die Richtungen, die du üben willst",
      caption: "Du musst nicht alle Punkte besetzen. Stellst du mehrere Farben auf dieselbe Richtung (hier Rot und Grün beide nach vorne), kommt genau diese Richtung häufiger dran, weil mehrere Farben zu ihr führen.",
      points: [
        { angle: 0, colors: [COLOR_BY_KEY.rot.hex, COLOR_BY_KEY.gruen.hex] },
        { angle: 90, colors: [COLOR_BY_KEY.blau.hex] },
        { angle: 315, colors: [COLOR_BY_KEY.gelb.hex] },
      ],
    },
  ];
  els.setupThumb.innerHTML = coneSetupSVG(SETUP_SLIDES[0].points);

  let setupSlideIdx = 0;
  function renderSetupSlide() {
    const s = SETUP_SLIDES[setupSlideIdx];
    els.setupSlideTitle.textContent = s.title;
    els.setupSlideArt.innerHTML = coneSetupSVG(s.points);
    els.setupSlideCaption.textContent = s.caption;
    els.setupCounter.textContent = `${setupSlideIdx + 1} / ${SETUP_SLIDES.length}`;
    els.setupPrevBtn.disabled = setupSlideIdx === 0;
    els.setupNextBtn.disabled = setupSlideIdx === SETUP_SLIDES.length - 1;
  }
  let setupModalReturnFocus = null;
  function openSetupModal() {
    setupSlideIdx = 0;
    renderSetupSlide();
    setupModalReturnFocus = document.activeElement;
    els.setupModal.hidden = false;
    focusFirstIn(els.setupModal);
  }
  function closeSetupModal() {
    els.setupModal.hidden = true;
    if (setupModalReturnFocus) setupModalReturnFocus.focus();
  }
  els.setupModalClose.addEventListener("click", closeSetupModal);
  els.setupModal.addEventListener("click", (e) => { if (e.target === els.setupModal) closeSetupModal(); });
  els.setupModal.addEventListener("keydown", (e) => trapTabKey(els.setupModal, e));
  els.setupPrevBtn.addEventListener("click", () => { if (setupSlideIdx > 0) { setupSlideIdx--; renderSetupSlide(); } });
  els.setupNextBtn.addEventListener("click", () => { if (setupSlideIdx < SETUP_SLIDES.length - 1) { setupSlideIdx++; renderSetupSlide(); } });
  wireSwipeNav(els.setupModal, {
    onLeft: () => els.setupNextBtn.click(),
    onRight: () => els.setupPrevBtn.click(),
  });

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
    arrowColors: ["blau"],
    stroopColors: ["rot", "gruen", "blau", "gelb", "lila"],
    periphKind: "gemischt",
    periphFixEnabled: true,
    periphFixChar: "",
    periphFixColor: "grau",
    periphFixSize: 1,
    periphAxes: ["horizontal", "vertikal", "diagonal"],
    periphUseZones: false,
    periphZones: ["tl", "tm", "tr", "ml", "mr", "bl", "bm", "br"],
    // "Dominanz": relative pick-weight per zone (1-3x) when useZones is on -
    // 1 everywhere means the previous flat-equal-split behaviour.
    periphZoneWeights: { tl: 1, tm: 1, tr: 1, ml: 1, mr: 1, bl: 1, bm: 1, br: 1 },
    periphSizeMode: "gleich",
    // Which colour(s) the flashed characters themselves use - separate from
    // the background tint. More than one selected is "gemischt": each flash
    // rolls its own colour independently (see pickPeriphColor()).
    periphColors: ["schwarz"],
    bgColorKey: "gruen",
    bgIntensity: 0,
  };
  const state = { ...DEFAULTS };
  function loadPrefs() {
    const saved = readJSON(PREFS_KEY, null);
    Object.assign(state, DEFAULTS, saved && typeof saved === "object" ? saved : {});
    if (!Array.isArray(state.colors) || keysToColors(state.colors).length < MIN_COLORS) state.colors = ["orange", "rot", "lila"];
    if (!Array.isArray(state.arrowColors) || keysToColors(state.arrowColors).length < ARROW_MIN_COLORS) state.arrowColors = ["blau"];
    if (!Array.isArray(state.stroopColors) || keysToColors(state.stroopColors, STROOP_COLOR_LIB).length < STROOP_MIN_COLORS) state.stroopColors = DEFAULTS.stroopColors.slice();
    if (!["buchstaben", "zahlen", "gemischt"].includes(state.periphKind)) state.periphKind = "gemischt";
    if (typeof state.periphFixEnabled !== "boolean") state.periphFixEnabled = true;
    if (typeof state.periphFixChar !== "string") state.periphFixChar = "";
    if (!FIX_COLOR_BY_KEY[state.periphFixColor]) state.periphFixColor = "grau";
    if (typeof state.periphFixSize !== "number" || state.periphFixSize < 0.6 || state.periphFixSize > 2) state.periphFixSize = 1;
    if (!Array.isArray(state.periphAxes) || !state.periphAxes.every((a) => ["horizontal", "vertikal", "diagonal"].includes(a))) state.periphAxes = DEFAULTS.periphAxes.slice();
    if (typeof state.periphUseZones !== "boolean") state.periphUseZones = false;
    if (!Array.isArray(state.periphZones) || !state.periphZones.length || !state.periphZones.every((z) => PERIPH_ZONE_KEYS.includes(z))) state.periphZones = DEFAULTS.periphZones.slice();
    if (!state.periphZoneWeights || typeof state.periphZoneWeights !== "object") state.periphZoneWeights = { ...DEFAULTS.periphZoneWeights };
    else PERIPH_ZONE_KEYS.forEach((z) => {
      const w = state.periphZoneWeights[z];
      state.periphZoneWeights[z] = typeof w === "number" && w >= 1 && w <= 3 ? w : 1;
    });
    if (!["gleich", "wachsend"].includes(state.periphSizeMode)) state.periphSizeMode = "gleich";
    if (!Array.isArray(state.periphColors) || !state.periphColors.length || !state.periphColors.every((k) => STROOP_COLOR_BY_KEY[k])) state.periphColors = DEFAULTS.periphColors.slice();
    if (!STROOP_COLOR_BY_KEY[state.bgColorKey]) state.bgColorKey = "gruen";
    if (typeof state.bgIntensity !== "number" || state.bgIntensity < 0 || state.bgIntensity > 1) state.bgIntensity = 0;
  }
  function savePrefs() { writeJSON(PREFS_KEY, state); }
  loadPrefs();

  // ---- Zusatzaufgabe: peripheral flashes as an optional add-on other
  // exercises can run during their own "Reiz"/"Pause" phases. Unlike every
  // other per-domain setting so far (background colour, Bereich, ...), this
  // one is genuinely per-EXERCISE - "4 Pfeile" and "8 Pfeile" can each carry
  // their own on/off + config - so it can't live in the flat `state` blob
  // the way everything else does. It gets its own small store keyed by
  // exercise id instead: { [exerciseId]: { phases, mode, own } }.
  //   phases: subset of "reiz"/"pause" - which of the host exercise's own
  //     schedule kinds ("blank" = pause, anything else = reiz) the add-on
  //     is allowed to fire during. Empty = the add-on is off for this
  //     exercise - a *valid* rest state here, unlike every other multi-select
  //     in the app where zero-selected is an error.
  //   mode: "uebernehmen" (default - mirrors Periphere Wahrnehmung's own
  //     live Bereich/Zeichentyp/Tempo settings, always in sync) or "eigen"
  //     (a per-exercise override bundle, `own`, edited independently).
  const ADDON_KEY = "fwmc-addon-v1";
  const ADDON_PHASE_KEYS = ["reiz", "pause"];
  const ADDON_PRESETS_KEY = "fwmc-addon-presets-v1"; // [{ id, name, own }] - not exercise-scoped, any saved bundle applies anywhere
  const addonPresetStore = makePresetStore(ADDON_PRESETS_KEY);
  function addonDefaultOwn() {
    return {
      kind: "gemischt", axes: PERIPH_AXIS_KEYS.slice(), useZones: false, zones: PERIPH_ZONE_KEYS.slice(),
      sizeMode: "gleich", stimulusS: 1, intervalMin: 2, intervalMax: 4, colors: ["schwarz"],
    };
  }
  function normalizeAddonEntry(e) {
    if (!e || typeof e !== "object") e = {};
    if (!Array.isArray(e.phases) || !e.phases.every((p) => ADDON_PHASE_KEYS.includes(p))) e.phases = [];
    e.phases = [...new Set(e.phases)];
    if (!["uebernehmen", "eigen"].includes(e.mode)) e.mode = "uebernehmen";
    const d = addonDefaultOwn();
    if (!e.own || typeof e.own !== "object") e.own = d;
    else {
      if (!["buchstaben", "zahlen", "gemischt"].includes(e.own.kind)) e.own.kind = d.kind;
      if (!Array.isArray(e.own.axes) || !e.own.axes.every((a) => PERIPH_AXIS_KEYS.includes(a))) e.own.axes = d.axes.slice();
      if (typeof e.own.useZones !== "boolean") e.own.useZones = d.useZones;
      if (!Array.isArray(e.own.zones) || !e.own.zones.length || !e.own.zones.every((z) => PERIPH_ZONE_KEYS.includes(z))) e.own.zones = d.zones.slice();
      if (!["gleich", "wachsend"].includes(e.own.sizeMode)) e.own.sizeMode = d.sizeMode;
      if (typeof e.own.stimulusS !== "number" || e.own.stimulusS < 0.3 || e.own.stimulusS > 2) e.own.stimulusS = d.stimulusS;
      if (typeof e.own.intervalMin !== "number" || e.own.intervalMin < 0.5 || e.own.intervalMin > 15) e.own.intervalMin = d.intervalMin;
      if (typeof e.own.intervalMax !== "number" || e.own.intervalMax < 0.5 || e.own.intervalMax > 15) e.own.intervalMax = d.intervalMax;
      if (!Array.isArray(e.own.colors) || !e.own.colors.length || !e.own.colors.every((k) => STROOP_COLOR_BY_KEY[k])) e.own.colors = d.colors.slice();
    }
    return e;
  }
  function loadAddonStore() {
    const s = readJSON(ADDON_KEY, {});
    return s && typeof s === "object" && !Array.isArray(s) ? s : {};
  }
  let addonStore = loadAddonStore();
  function saveAddonStore() { writeJSON(ADDON_KEY, addonStore); }
  // Always returns a normalized entry for this exercise id, creating one
  // (add-on off, defaults otherwise) the first time it's asked for.
  function getAddonEntry(exId) {
    addonStore[exId] = normalizeAddonEntry(addonStore[exId]);
    return addonStore[exId];
  }
  // The "übernehmen" config: reads Periphere Wahrnehmung's own live settings
  // (no Dominanz here - that stays opt-in-tested on Periph itself only).
  function addonConfigFromState() {
    return {
      kind: state.periphKind, useZones: state.periphUseZones, axes: state.periphAxes, zones: state.periphZones,
      sizeMode: state.periphSizeMode, stimulusS: state.stimulusS, intervalMin: state.intervalMin, intervalMax: state.intervalMax,
      colors: state.periphColors,
    };
  }

  // Colours + seed used by the running exercise (set per start).
  let active = {
    colors: keysToColors(state.colors),
    arrowColors: keysToColors(state.arrowColors),
    stroopColors: keysToColors(state.stroopColors, STROOP_COLOR_LIB),
  };

  function randInterval(rng) {
    const lo = Math.min(state.intervalMin, state.intervalMax);
    const hi = Math.max(state.intervalMin, state.intervalMax);
    return lo + rng() * (hi - lo);
  }
  // ---- Colour picker. Shared by three independent selections: the
  // "standard" 2-4 colour VT/VRW/Kompass palette (state.colors), the looser
  // 1-7 colour palette for the three pure-arrow exercises (state.arrowColors),
  // and Stroop's own 2-9 colour palette (state.stroopColors, COLOR_LIB plus
  // Schwarz/Weiß). Which one is active is decided per exercise in
  // openReady() below, which also rebuilds the swatches for that palette's
  // colour list via renderColorSwatches() - the three lists differ in size,
  // so the DOM can't just stay built from a single fixed COLOR_LIB forever.
  let colorMode = "standard";
  function colorModePalette() { return colorMode === "stroop" ? STROOP_COLOR_LIB : COLOR_LIB; }
  function colorModeArray() {
    if (colorMode === "arrows") return state.arrowColors;
    if (colorMode === "stroop") return state.stroopColors;
    return state.colors;
  }
  function setColorModeArray(keys) {
    if (colorMode === "arrows") state.arrowColors = keys;
    else if (colorMode === "stroop") state.stroopColors = keys;
    else state.colors = keys;
  }
  function colorModeLimits() {
    if (colorMode === "arrows") return { min: ARROW_MIN_COLORS, max: ARROW_MAX_COLORS };
    if (colorMode === "stroop") return { min: STROOP_MIN_COLORS, max: STROOP_MAX_COLORS };
    return { min: MIN_COLORS, max: MAX_COLORS };
  }
  let hintTimer = null;
  function colorHint(text, warn) {
    els.colorHint.textContent = text;
    els.colorHint.classList.toggle("warn", !!warn);
    if (hintTimer) clearTimeout(hintTimer);
    if (warn) hintTimer = setTimeout(() => colorHint(defaultColorHint()), 2200);
  }
  function defaultColorHint() {
    const { min, max } = colorModeLimits();
    return `Wähle ${min} bis ${max} Farben – sie werden zufällig gemischt.`;
  }
  function buildColorSwatch(c) {
    const btn = document.createElement("button");
    btn.className = "color-swatch";
    btn.dataset.color = c.key;
    btn.setAttribute("aria-pressed", "false");
    // A checkmark drawn in white would vanish on a white (Weiß) swatch, so
    // pick a stroke colour that stays visible against this specific swatch.
    const stroke = relLuma(c.hex) > 0.75 ? "#16232a" : "#fff";
    btn.innerHTML = `<span class="swatch" style="background:${c.hex}"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="${stroke}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="swatch-name">${c.name}</span>`;
    btn.addEventListener("click", () => {
      const keys = colorModeArray();
      const { min, max } = colorModeLimits();
      const lib = colorModePalette();
      const selected = keys.includes(c.key);
      if (selected) {
        // Arrow/Stroop mode allow going all the way down to zero -
        // syncColorUI() shows a "pick at least N" hint and disables the
        // start button for that, rather than blocking the click outright
        // like the standard 2-4 palette below does.
        if (colorMode === "standard" && keys.length <= min) { colorHint(`Mindestens ${min} Farben.`, true); return; }
        setColorModeArray(keys.filter((k) => k !== c.key));
      } else {
        if (keys.length >= max) { colorHint(`Höchstens ${max} Farben – wähle zuerst eine ab.`, true); return; }
        setColorModeArray(lib.map((x) => x.key).filter((k) => k === c.key || keys.includes(k)));
      }
      savePrefs();
      syncColorUI();
    });
    return btn;
  }
  // "Alle Farben" shortcut - hidden in standard mode (its 2-4 cap makes "all
  // colours" impossible there anyway). Its active state is never stored on
  // its own - it's simply true whenever every colour of the current
  // palette happens to be selected, whether that came from this button or
  // from picking every swatch by hand.
  let colorAllBtn = null;
  function buildColorAllBtn(lib) {
    const btn = document.createElement("button");
    btn.className = "color-swatch";
    btn.setAttribute("aria-pressed", "false");
    const wedges = lib.map((c, i) => `${c.hex} ${(i / lib.length * 100).toFixed(2)}% ${((i + 1) / lib.length * 100).toFixed(2)}%`).join(",");
    btn.innerHTML = `<span class="swatch" style="background:conic-gradient(${wedges})"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="swatch-name">Alle Farben</span>`;
    btn.addEventListener("click", () => {
      const allSelected = colorModeArray().length === lib.length;
      // Toggle: every colour <-> none at all, rather than picking an
      // arbitrary colour to leave behind. syncColorUI() shows a "pick at
      // least N" hint and disables the start button while too few (or none)
      // are selected.
      setColorModeArray(allSelected ? [] : lib.map((c) => c.key));
      savePrefs();
      syncColorUI();
    });
    return btn;
  }
  function renderColorSwatches() {
    const lib = colorModePalette();
    els.colorPicker.innerHTML = "";
    lib.forEach((c) => els.colorPicker.appendChild(buildColorSwatch(c)));
    colorAllBtn = buildColorAllBtn(lib);
    els.colorPicker.appendChild(colorAllBtn);
  }
  function syncColorUI() {
    const keys = colorModeArray();
    const { min, max } = colorModeLimits();
    const lib = colorModePalette();
    els.colorPicker.querySelectorAll(".color-swatch[data-color]").forEach((el) => {
      const on = keys.includes(el.dataset.color);
      el.classList.toggle("active", on);
      el.setAttribute("aria-pressed", on ? "true" : "false");
    });
    colorAllBtn.hidden = colorMode === "standard";
    const allOn = keys.length === lib.length;
    colorAllBtn.classList.toggle("active", allOn);
    colorAllBtn.setAttribute("aria-pressed", allOn ? "true" : "false");
    els.colorCount.textContent = `${keys.length} gewählt`;
    const belowMin = colorMode !== "standard" && keys.length < min;
    if (hintTimer) { clearTimeout(hintTimer); hintTimer = null; }
    els.colorHint.textContent = belowMin
      ? (min === 1 ? "Wähle mindestens eine Farbe." : `Wähle mindestens ${min} Farben.`)
      : defaultColorHint();
    els.colorHint.classList.toggle("warn", belowMin);
    els.startBtn.disabled = belowMin;
    els.vtSaveBtn.disabled = belowMin;
  }

  // ---- "Farbe der Reize": a second, independent multi-select swatch picker
  // for the peripheral characters themselves (Periphere Wahrnehmung's own,
  // and the Zusatzaufgabe's "eigene Feineinstellung" bundle) - deliberately
  // NOT the colorMode/colorModeArray() system above, since both of these can
  // be open on screen at the same time as an exercise's own arrow/Stroop
  // colour picker (they colour a different thing), not instead of it.
  // Selecting more than one colour is what "gemischt" means here - each
  // flash rolls its own colour independently, see pickPeriphColor().
  function buildStimColorSwatch(c, getKeys, setKeys, onChange) {
    const btn = document.createElement("button");
    btn.className = "color-swatch";
    btn.dataset.color = c.key;
    btn.setAttribute("aria-pressed", "false");
    const stroke = relLuma(c.hex) > 0.75 ? "#16232a" : "#fff";
    btn.innerHTML = `<span class="swatch" style="background:${c.hex}"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="${stroke}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="swatch-name">${c.name}</span>`;
    btn.addEventListener("click", () => {
      const keys = getKeys();
      const selected = keys.includes(c.key);
      if (selected && keys.length <= 1) return; // keep at least one, same rule as every other colour picker
      setKeys(selected ? keys.filter((k) => k !== c.key) : [...keys, c.key]);
      onChange();
    });
    return btn;
  }
  function buildStimColorPicker(container, getKeys, setKeys, onChange) {
    container.innerHTML = "";
    STROOP_COLOR_LIB.forEach((c) => container.appendChild(buildStimColorSwatch(c, getKeys, setKeys, onChange)));
  }
  function syncStimColorUI(container, getKeys, hintEl) {
    const keys = getKeys();
    container.querySelectorAll(".color-swatch[data-color]").forEach((el) => {
      const on = keys.includes(el.dataset.color);
      el.classList.toggle("active", on);
      el.setAttribute("aria-pressed", on ? "true" : "false");
    });
    if (!hintEl) return;
    hintEl.textContent = keys.length > 1
      ? "Gemischt – bei jedem Reiz wird automatisch eine Farbe aus deiner Auswahl gewählt, die sich vom Hintergrund abhebt."
      : "Nur eine Farbe gewählt – wähle mehr als eine, damit automatisch ausgewichen werden kann, falls sie einmal zum Hintergrund passt.";
  }
  buildStimColorPicker(els.periphColorPicker, () => state.periphColors, (keys) => { state.periphColors = keys; }, () => { savePrefs(); syncPeriphColorUI(); });
  function syncPeriphColorUI() { syncStimColorUI(els.periphColorPicker, () => state.periphColors, els.periphColorHint); }

  // ---- Periphere Wahrnehmung: Zeichentyp + Fixpunkt Feineinstellungen ----
  document.querySelectorAll("#periphKindRow [data-periph-kind]").forEach((el) => {
    el.addEventListener("click", () => {
      state.periphKind = el.dataset.periphKind;
      savePrefs();
      syncPeriphKindUI();
    });
  });
  function syncPeriphKindUI() {
    document.querySelectorAll("#periphKindRow [data-periph-kind]").forEach((el) => {
      setActive(el, el.dataset.periphKind === state.periphKind);
    });
  }
  // Single-select swatch picker, shared by every "pick one colour" UI
  // (fixation-point colour, background colour, and their pause-overlay
  // twins) - avoids a near-identical copy of this DOM-building code per screen.
  function buildSingleSelectPicker(container, lib, onPick) {
    lib.forEach((c) => {
      const btn = document.createElement("button");
      btn.className = "color-swatch";
      btn.dataset.key = c.key;
      btn.setAttribute("aria-pressed", "false");
      const stroke = relLuma(c.hex) > 0.75 ? "#16232a" : "#fff";
      btn.innerHTML = `<span class="swatch" style="background:${c.hex}"><svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="${stroke}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="swatch-name">${c.name}</span>`;
      btn.addEventListener("click", () => onPick(c.key));
      container.appendChild(btn);
    });
  }
  function syncSingleSelectPicker(container, currentKey) {
    container.querySelectorAll(".color-swatch").forEach((el) => {
      const on = el.dataset.key === currentKey;
      el.classList.toggle("active", on);
      el.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }
  // Generic "background colour + intensity" control for exercises outside
  // the shared VT/Periph canvas pipeline (Remember; Flash Speicher Test
  // will reuse it once it exists) that still want the same customisable
  // tint. Wires as many synced picker/slider instances as given against a
  // single prefs object (e.g. one per ready screen plus one in a pause
  // overlay) and calls `onChange` after every edit so the caller can
  // re-apply the tint to whatever it's drawn on and persist the prefs.
  // (Periph/VT's own bg picker predates this and isn't migrated to it, to
  // avoid touching that already-tested code for no functional gain.)
  // Every place with a background colour/intensity control can copy
  // another domain's CURRENT live setting, or a name the client saved
  // themselves - "Bestehende Farbgestaltung übernehmen". Only two domains
  // have one today: the whole VT/NAT canvas pipeline shares one setting
  // (every non-"bgIsStimulus" VT/Periph exercise reads state.bgColorKey/
  // bgIntensity - it isn't exclusive to Periph, that's just where the
  // control first got built) and Remember has its own
  // (rememberPrefs.bgColorKey/bgIntensity). Flash Speicher Test will be a
  // third once it exists and gets its own background setting.
  const BG_SOURCES = [
    { id: "vt", label: "Visual Training / NAT", get: () => ({ colorKey: state.bgColorKey, intensity: state.bgIntensity }) },
    { id: "remember", label: "Remember", get: () => ({ colorKey: rememberPrefs.bgColorKey, intensity: rememberPrefs.bgIntensity }) },
    { id: "blitz", label: "Blitz-Raster", get: () => ({ colorKey: blitzPrefs.bgColorKey, intensity: blitzPrefs.bgIntensity }) },
    { id: "flash", label: "Flash Speicher Test", get: () => ({ colorKey: flashPrefs.bgColorKey, intensity: flashPrefs.bgIntensity }) },
    { id: "mot", label: "MOT-Fähigkeit", get: () => ({ colorKey: motPrefs.bgColorKey, intensity: motPrefs.bgIntensity }) },
  ];
  const BG_PRESETS_KEY = "fwmc-bg-presets-v1"; // [{ id, name, colorKey, intensity }] - not scoped to a domain, any saved combo applies anywhere
  const bgPresetStore = makePresetStore(BG_PRESETS_KEY);
  function wireBgIntensityControl(store, refs, onChange, transferSelfId) {
    function apply(colorKey, intensity) {
      if (colorKey != null) store.bgColorKey = colorKey;
      if (intensity != null) store.bgIntensity = intensity;
      onChange();
      sync();
    }
    function renderTransfer() {
      (refs.transfer || []).forEach((t) => {
        t.sourceRow.innerHTML = "";
        BG_SOURCES.filter((s) => s.id !== transferSelfId).forEach((s) => {
          // A source whose own prefs object is declared later in the file
          // (rememberPrefs isn't initialised yet when this first runs for
          // the VT/Periph instance, at page-load time) throws a TDZ error -
          // skip it for now, it'll render fine once actually opened, after
          // every top-level const has run.
          let v;
          try { v = s.get(); } catch (e) { return; }
          const hex = STROOP_COLOR_BY_KEY[v.colorKey].hex;
          const btn = document.createElement("button");
          btn.className = "choice";
          btn.innerHTML = `<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:${hex};margin-right:6px;vertical-align:-1px"></span>Wie bei ${s.label}`;
          btn.addEventListener("click", () => apply(v.colorKey, v.intensity));
          t.sourceRow.appendChild(btn);
        });
        renderPresetList(bgPresetStore, t.presetList, t.presetGroup, null,
          (p) => `${STROOP_COLOR_BY_KEY[p.colorKey].name} · ${Math.round(p.intensity * 100)}%`,
          (p) => apply(p.colorKey, p.intensity));
      });
    }
    function sync() {
      refs.pickers.forEach((el) => syncSingleSelectPicker(el, store.bgColorKey));
      refs.sliders.forEach((el) => { el.value = store.bgIntensity; });
      const pct = Math.round(store.bgIntensity * 100) + "%";
      refs.valueEls.forEach((el) => { el.textContent = pct; });
      const mixed = mixHex("#ffffff", STROOP_COLOR_BY_KEY[store.bgColorKey].hex, store.bgIntensity);
      const showTip = store.bgIntensity > 0 && relLuma(mixed) < 0.45;
      (refs.hintEls || []).forEach((el) => {
        el.hidden = !showTip;
        el.textContent = showTip ? "Tipp: Bei dieser Hintergrundfarbe ist weißer Text/eine weiße Form oft besser lesbar als Schwarz." : "";
      });
      renderTransfer();
    }
    // Picking a colour while intensity is at 0% would otherwise have no
    // visible effect at all (0% always renders plain white regardless of
    // colour) - looks broken, not "off". Jump to 50% in that case only, so
    // the pick is immediately visible; once intensity is already > 0 (the
    // client cared enough to set it), further colour picks leave it alone.
    refs.pickers.forEach((el) => buildSingleSelectPicker(el, STROOP_COLOR_LIB, (key) => {
      apply(key, store.bgIntensity > 0 ? null : 0.5);
    }));
    refs.sliders.forEach((el) => el.addEventListener("input", () => apply(null, Number(el.value))));
    (refs.transfer || []).forEach((t) => {
      wirePresetSaveForm({
        saveBtn: t.saveBtn, form: t.form, nameInput: t.nameInput,
        cancelBtn: t.cancelBtn, confirmBtn: t.confirmBtn,
        defaultName: () => `${STROOP_COLOR_BY_KEY[store.bgColorKey].name} ${Math.round(store.bgIntensity * 100)}%`,
        onSave: (name) => {
          const list = bgPresetStore.load();
          list.push({ id: String(Date.now()), name, colorKey: store.bgColorKey, intensity: store.bgIntensity });
          bgPresetStore.save(list);
          renderTransfer();
        },
      });
    });
    sync();
    return sync;
  }
  // On/off toggle for the fixation point itself - same "Anzeigen"/
  // "Ausblenden" pattern as Flash Speicher Test's, added so it can be fully
  // removed (not just recoloured/resized) for every exercise that shows it
  // (Periphere Wahrnehmung and, since drawFixationPoint() is shared, every
  // other VT-canvas exercise too - one shared state.periphFixEnabled, no
  // per-exercise duplication needed).
  document.querySelectorAll("#periphFixToggleRow [data-periph-fix]").forEach((el) => {
    el.addEventListener("click", () => {
      state.periphFixEnabled = el.dataset.periphFix === "1";
      savePrefs();
      syncPeriphFixUI();
    });
  });
  buildSingleSelectPicker(els.periphFixColorPicker, FIX_COLOR_LIB, (key) => {
    state.periphFixColor = key;
    savePrefs();
    syncPeriphFixUI();
  });
  buildSingleSelectPicker(els.periphPauseFixColorPicker, FIX_COLOR_LIB, (key) => {
    state.periphFixColor = key;
    savePrefs();
    syncPeriphFixUI();
    redrawFrozenFrame();
  });
  els.periphFixCharInput.addEventListener("input", () => {
    state.periphFixChar = els.periphFixCharInput.value.slice(0, 3);
    savePrefs();
  });
  els.periphFixSizeSlider.addEventListener("input", () => {
    state.periphFixSize = Number(els.periphFixSizeSlider.value);
    savePrefs();
    syncPeriphFixUI();
  });
  els.periphPauseFixSizeSlider.addEventListener("input", () => {
    state.periphFixSize = Number(els.periphPauseFixSizeSlider.value);
    savePrefs();
    syncPeriphFixUI();
    redrawFrozenFrame();
  });
  function syncPeriphFixUI() {
    document.querySelectorAll("#periphFixToggleRow [data-periph-fix]").forEach((el) => setActive(el, (el.dataset.periphFix === "1") === state.periphFixEnabled));
    els.periphFixOptions.hidden = !state.periphFixEnabled;
    syncSingleSelectPicker(els.periphFixColorPicker, state.periphFixColor);
    syncSingleSelectPicker(els.periphPauseFixColorPicker, state.periphFixColor);
    els.periphFixCharInput.value = state.periphFixChar;
    els.periphFixSizeSlider.value = state.periphFixSize;
    els.periphFixSizeValue.textContent = state.periphFixSize.toFixed(1) + "×";
    els.periphPauseFixSizeSlider.value = state.periphFixSize;
    els.periphPauseFixSizeValue.textContent = state.periphFixSize.toFixed(1) + "×";
  }
  // Horizontal/Vertikal/Diagonal are a multi-select set, same pattern as
  // the arrow-colour picker: "Überall" is the "alle Farben" shortcut for
  // "all three at once", auto-activates once all three end up selected by
  // hand, and toggling it off drops to zero (with a "pick at least one"
  // warning) rather than falling back to some arbitrary one.
  document.querySelectorAll("#periphFieldRow [data-periph-axis]").forEach((el) => {
    el.addEventListener("click", () => {
      const axis = el.dataset.periphAxis;
      const on = state.periphAxes.includes(axis);
      state.periphAxes = on ? state.periphAxes.filter((a) => a !== axis) : [...state.periphAxes, axis];
      savePrefs();
      syncPeriphFieldUI();
    });
  });
  els.periphAllBtn.addEventListener("click", () => {
    const allOn = state.periphAxes.length === PERIPH_AXIS_KEYS.length;
    state.periphAxes = allOn ? [] : PERIPH_AXIS_KEYS.slice();
    savePrefs();
    syncPeriphFieldUI();
  });
  els.periphZonesBtn.addEventListener("click", () => {
    state.periphUseZones = !state.periphUseZones;
    savePrefs();
    syncPeriphFieldUI();
  });
  document.querySelectorAll("#periphZoneGrid [data-zone]").forEach((el) => {
    el.addEventListener("click", () => {
      const z = el.dataset.zone;
      const on = state.periphZones.includes(z);
      // Keep at least one zone selected - same "don't let the last one go"
      // rule as the standard VT colour picker.
      if (on && state.periphZones.length <= 1) return;
      state.periphZones = on ? state.periphZones.filter((k) => k !== z) : [...state.periphZones, z];
      savePrefs();
      syncPeriphFieldUI();
    });
  });
  // "Dominanz": one 1x-3x weight slider per currently *selected* zone,
  // shown only in zone mode with more than one zone picked (weighting a
  // single zone against nothing else is meaningless). Rebuilt on every
  // zone (de)selection so it always matches exactly what's on offer.
  function renderPeriphZoneWeights() {
    const show = state.periphUseZones && state.periphZones.length > 1;
    els.periphZoneWeights.hidden = !show;
    if (!show) return;
    els.periphZoneWeights.querySelectorAll(".slider-row").forEach((el) => el.remove());
    state.periphZones.forEach((z) => {
      const label = els.periphZoneGrid.querySelector(`[data-zone="${z}"]`).getAttribute("aria-label");
      const row = document.createElement("div");
      row.className = "slider-row";
      row.innerHTML = `<span class="slider-label">${label}</span><input type="range" data-zone-weight="${z}" min="1" max="3" step="1" aria-label="Dominanz ${label}"><span class="slider-value">${state.periphZoneWeights[z]}×</span>`;
      const input = row.querySelector("input");
      input.value = state.periphZoneWeights[z];
      input.addEventListener("input", () => {
        state.periphZoneWeights[z] = Number(input.value);
        savePrefs();
        row.querySelector(".slider-value").textContent = state.periphZoneWeights[z] + "×";
      });
      els.periphZoneWeights.appendChild(row);
    });
  }
  function syncPeriphFieldUI() {
    document.querySelectorAll("#periphFieldRow [data-periph-axis]").forEach((el) => setActive(el, state.periphAxes.includes(el.dataset.periphAxis)));
    setActive(els.periphAllBtn, state.periphAxes.length === PERIPH_AXIS_KEYS.length);
    setActive(els.periphZonesBtn, state.periphUseZones);
    els.periphFieldRow.hidden = state.periphUseZones;
    els.periphZoneGrid.hidden = !state.periphUseZones;
    document.querySelectorAll("#periphZoneGrid [data-zone]").forEach((el) => el.classList.toggle("active", state.periphZones.includes(el.dataset.zone)));
    renderPeriphZoneWeights();
    const belowMin = !state.periphUseZones && state.periphAxes.length === 0;
    els.periphFieldHint.textContent = belowMin ? "Wähle mindestens einen Bereich." : "";
    els.periphFieldHint.classList.toggle("warn", belowMin);
    // Safe to assign outright (not OR-in): Periphere Wahrnehmung never uses
    // the colour picker, so syncColorUI()'s own belowMin for this exercise
    // is always false and there's nothing of its to preserve here.
    els.startBtn.disabled = belowMin;
    els.vtSaveBtn.disabled = belowMin;
  }
  document.querySelectorAll("#periphSizeGroup [data-periph-size]").forEach((el) => {
    el.addEventListener("click", () => {
      state.periphSizeMode = el.dataset.periphSize;
      savePrefs();
      syncPeriphSizeUI();
    });
  });
  function syncPeriphSizeUI() {
    document.querySelectorAll("#periphSizeGroup [data-periph-size]").forEach((el) => setActive(el, el.dataset.periphSize === state.periphSizeMode));
  }

  // ---- Zusatzaufgabe: Phase 1/Phase 2/Beide is the same multi-select +
  // "select all" shortcut pattern as everywhere else (colours, Periph's own
  // Bereich, ...), except zero-selected is this control's valid "off" state
  // rather than an error - so no warning hint and no start-button disabling
  // for it. Everything below reads/writes getAddonEntry(state.exercise), not
  // `state` itself, since this is the app's first genuinely per-exercise
  // setting (see the comment by ADDON_KEY above).
  document.querySelectorAll("#addonPhaseRow [data-addon-phase]").forEach((el) => {
    el.addEventListener("click", () => {
      const entry = getAddonEntry(state.exercise);
      const p = el.dataset.addonPhase;
      const on = entry.phases.includes(p);
      entry.phases = on ? entry.phases.filter((x) => x !== p) : [...entry.phases, p];
      saveAddonStore();
      syncAddonUI();
    });
  });
  els.addonPhaseAllBtn.addEventListener("click", () => {
    const entry = getAddonEntry(state.exercise);
    const allOn = entry.phases.length === ADDON_PHASE_KEYS.length;
    entry.phases = allOn ? [] : ADDON_PHASE_KEYS.slice();
    saveAddonStore();
    syncAddonUI();
  });
  document.querySelectorAll("#addonModeRow [data-addon-mode]").forEach((el) => {
    el.addEventListener("click", () => {
      const entry = getAddonEntry(state.exercise);
      entry.mode = el.dataset.addonMode;
      saveAddonStore();
      syncAddonUI();
    });
  });
  document.querySelectorAll("#addonKindRow [data-addon-kind]").forEach((el) => {
    el.addEventListener("click", () => {
      const entry = getAddonEntry(state.exercise);
      entry.own.kind = el.dataset.addonKind;
      saveAddonStore();
      syncAddonUI();
    });
  });
  document.querySelectorAll("#addonFieldRow [data-addon-axis]").forEach((el) => {
    el.addEventListener("click", () => {
      const entry = getAddonEntry(state.exercise);
      const axis = el.dataset.addonAxis;
      const on = entry.own.axes.includes(axis);
      entry.own.axes = on ? entry.own.axes.filter((a) => a !== axis) : [...entry.own.axes, axis];
      saveAddonStore();
      syncAddonUI();
    });
  });
  els.addonAllBtn.addEventListener("click", () => {
    const entry = getAddonEntry(state.exercise);
    const allOn = entry.own.axes.length === PERIPH_AXIS_KEYS.length;
    entry.own.axes = allOn ? [] : PERIPH_AXIS_KEYS.slice();
    saveAddonStore();
    syncAddonUI();
  });
  els.addonZonesBtn.addEventListener("click", () => {
    const entry = getAddonEntry(state.exercise);
    entry.own.useZones = !entry.own.useZones;
    saveAddonStore();
    syncAddonUI();
  });
  document.querySelectorAll("#addonZoneGrid [data-zone]").forEach((el) => {
    el.addEventListener("click", () => {
      const entry = getAddonEntry(state.exercise);
      const z = el.dataset.zone;
      const on = entry.own.zones.includes(z);
      if (on && entry.own.zones.length <= 1) return;
      entry.own.zones = on ? entry.own.zones.filter((k) => k !== z) : [...entry.own.zones, z];
      saveAddonStore();
      syncAddonUI();
    });
  });
  document.querySelectorAll("#addonOwnBody [data-addon-size]").forEach((el) => {
    el.addEventListener("click", () => {
      const entry = getAddonEntry(state.exercise);
      entry.own.sizeMode = el.dataset.addonSize;
      saveAddonStore();
      syncAddonUI();
    });
  });
  buildStimColorPicker(els.addonColorPicker,
    () => getAddonEntry(state.exercise).own.colors,
    (keys) => { getAddonEntry(state.exercise).own.colors = keys; },
    () => { saveAddonStore(); syncStimColorUI(els.addonColorPicker, () => getAddonEntry(state.exercise).own.colors, els.addonColorHint); });
  els.addonStimulusSlider.addEventListener("input", () => {
    const entry = getAddonEntry(state.exercise);
    entry.own.stimulusS = Number(els.addonStimulusSlider.value);
    saveAddonStore();
    els.addonStimulusValue.textContent = fmtSeconds(entry.own.stimulusS);
  });
  els.addonIntervalMinSlider.addEventListener("input", () => {
    const entry = getAddonEntry(state.exercise);
    entry.own.intervalMin = Number(els.addonIntervalMinSlider.value);
    saveAddonStore();
    syncAddonIntervalLabel(entry);
  });
  els.addonIntervalMaxSlider.addEventListener("input", () => {
    const entry = getAddonEntry(state.exercise);
    entry.own.intervalMax = Number(els.addonIntervalMaxSlider.value);
    saveAddonStore();
    syncAddonIntervalLabel(entry);
  });
  function syncAddonIntervalLabel(entry) {
    const lo = Math.min(entry.own.intervalMin, entry.own.intervalMax), hi = Math.max(entry.own.intervalMin, entry.own.intervalMax);
    els.addonIntervalValue.textContent = `${fmtSeconds(lo)}–${fmtSeconds(hi)}`;
  }
  function addonPresetMeta(own) {
    const kindLabel = own.kind === "buchstaben" ? "Buchstaben" : own.kind === "zahlen" ? "Zahlen" : "Gemischt";
    return `${kindLabel} · ${fmtSeconds(own.stimulusS)}`;
  }
  function renderAddonPresets() {
    renderPresetList(addonPresetStore, els.addonPresetList, els.addonPresetGroup, null, (e) => addonPresetMeta(e.own), (e) => {
      const entry = getAddonEntry(state.exercise);
      entry.own = { ...addonDefaultOwn(), ...e.own };
      saveAddonStore();
      syncAddonUI();
    });
  }
  wirePresetSaveForm({
    saveBtn: els.addonSaveBtn, form: els.addonSaveForm, nameInput: els.addonSaveNameInput,
    cancelBtn: els.addonSaveCancelBtn, confirmBtn: els.addonSaveConfirmBtn,
    defaultName: () => "Zusatzaufgabe " + new Date().toLocaleDateString("de-DE"),
    onSave: (name) => {
      const entry = getAddonEntry(state.exercise);
      const list = addonPresetStore.load();
      list.push({ id: String(Date.now()), name, own: { ...entry.own } });
      addonPresetStore.save(list);
      renderAddonPresets();
    },
  });
  function syncAddonUI() {
    const entry = getAddonEntry(state.exercise);
    document.querySelectorAll("#addonPhaseRow [data-addon-phase]").forEach((el) => setActive(el, entry.phases.includes(el.dataset.addonPhase)));
    setActive(els.addonPhaseAllBtn, entry.phases.length === ADDON_PHASE_KEYS.length);
    const enabled = entry.phases.length > 0;
    els.addonPhaseHint.textContent = enabled ? "" : "Aus – wähle „Beim Reiz“, „In der Pause“ oder beides, um die Zusatzaufgabe zu aktivieren.";
    els.addonConfigBody.hidden = !enabled;
    if (!enabled) return;
    document.querySelectorAll("#addonModeRow [data-addon-mode]").forEach((el) => setActive(el, el.dataset.addonMode === entry.mode));
    els.addonOwnBody.hidden = entry.mode !== "eigen";
    if (entry.mode !== "eigen") return;
    document.querySelectorAll("#addonKindRow [data-addon-kind]").forEach((el) => setActive(el, el.dataset.addonKind === entry.own.kind));
    document.querySelectorAll("#addonFieldRow [data-addon-axis]").forEach((el) => setActive(el, entry.own.axes.includes(el.dataset.addonAxis)));
    setActive(els.addonAllBtn, entry.own.axes.length === PERIPH_AXIS_KEYS.length);
    setActive(els.addonZonesBtn, entry.own.useZones);
    els.addonFieldRow.hidden = entry.own.useZones;
    els.addonZoneGrid.hidden = !entry.own.useZones;
    document.querySelectorAll("#addonZoneGrid [data-zone]").forEach((el) => el.classList.toggle("active", entry.own.zones.includes(el.dataset.zone)));
    const belowMin = !entry.own.useZones && entry.own.axes.length === 0;
    els.addonFieldHint.textContent = belowMin ? "Wähle mindestens einen Bereich." : "";
    els.addonFieldHint.classList.toggle("warn", belowMin);
    // OR'd in (not assigned outright) - the host exercise's own colour
    // picker may already have disabled these for an unrelated reason.
    els.startBtn.disabled = els.startBtn.disabled || belowMin;
    els.vtSaveBtn.disabled = els.vtSaveBtn.disabled || belowMin;
    document.querySelectorAll("#addonOwnBody [data-addon-size]").forEach((el) => setActive(el, el.dataset.addonSize === entry.own.sizeMode));
    syncStimColorUI(els.addonColorPicker, () => entry.own.colors, els.addonColorHint);
    els.addonStimulusSlider.value = entry.own.stimulusS;
    els.addonStimulusValue.textContent = fmtSeconds(entry.own.stimulusS);
    els.addonIntervalMinSlider.value = entry.own.intervalMin;
    els.addonIntervalMaxSlider.value = entry.own.intervalMax;
    syncAddonIntervalLabel(entry);
    renderAddonPresets();
  }

  // ---- Background colour + intensity ("Champions League" mode) - the
  // page stays plain white at intensity 0 and gets tinted from there, for
  // every exercise whose background isn't already the trained signal
  // itself (see bgIsStimulus on VT/VRW/Kompass-Aufbau/Stroop mit Hintergrund).
  // redrawFrozenFrame() is a safe no-op with no active/paused session (i.e.
  // every edit made on the ready screen, before a session exists), and
  // repaints the frozen frame immediately when edited from the pause
  // overlay mid-session. ----
  const syncBgUI = wireBgIntensityControl(state, {
    pickers: [els.bgColorPicker, els.periphPauseBgColorPicker],
    sliders: [els.bgIntensitySlider, els.periphPauseBgSlider],
    valueEls: [els.bgIntensityValue, els.periphPauseBgValue],
    hintEls: [els.bgContrastHint],
    transfer: [{
      sourceRow: els.bgSourceRow, presetGroup: els.bgPresetGroup, presetList: els.bgPresetList,
      saveBtn: els.bgSaveBtn, form: els.bgSaveForm, nameInput: els.bgSaveNameInput,
      cancelBtn: els.bgSaveCancelBtn, confirmBtn: els.bgSaveConfirmBtn,
    }],
  }, () => { savePrefs(); redrawFrozenFrame(); }, "vt");

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
  // Almost every exercise opens from the VT home grid, so "Zurück" on the
  // ready/done screens defaults to "home" - but Periphere Wahrnehmung opens
  // from the NAT home instead and needs to return there.
  let readyReturnScreen = "home";
  document.querySelectorAll(".excard").forEach((card) => {
    card.addEventListener("click", () => {
      // Greyed-out/incompatible (see Master-Einstellungen further below) -
      // tapping it opens Settings instead of the exercise, since the card
      // itself IS the "Verweis auf die Master-Einstellungen".
      if (card.classList.contains("incompatible")) { openMasterSettings(); return; }
      readyReturnScreen = "home";
      openReady(card.dataset.exercise, card.querySelector(".icon-badge,.icon-tile").outerHTML);
    });
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
    els.setupBtn.hidden = !ex.setupDiagram;
    els.setupBtn.onclick = ex.setupDiagram ? openSetupModal : null;
    colorMode = ex.usesArrowColors ? "arrows" : ex.usesStroopColors ? "stroop" : "standard";
    els.colorGroup.hidden = !ex.usesColors && !ex.usesArrowColors && !ex.usesStroopColors;
    const isConeTap = ex.type === "color-tap";
    const isPeriph = ex.type === "periph";
    const bgAllowed = !isConeTap && !ex.bgIsStimulus;
    els.tempoGroup.hidden = isConeTap;
    els.advanced.hidden = isConeTap;
    els.periphKindGroup.hidden = !isPeriph;
    // The fixation-point Feineinstellung applies to every exercise with
    // this dot (i.e. everything except Hütchen sortieren), not just
    // Periphere Wahrnehmung - it was just built there first.
    els.periphFixGroup.hidden = isConeTap;
    els.periphFieldGroup.hidden = !isPeriph;
    els.periphSizeGroup.hidden = !isPeriph;
    els.periphColorGroup.hidden = !isPeriph;
    els.bgGroup.hidden = !bgAllowed;
    // The add-on can't sensibly run on itself, and Hütchen sortieren has no
    // schedule of "Reiz"/"Pause" frames for it to hook into at all.
    els.addonGroup.hidden = isConeTap || isPeriph;
    renderColorSwatches();
    syncColorUI();
    // Runs after syncColorUI() so its own start/save-button disabling (the
    // "pick at least one Bereich" rule) isn't clobbered by colour's - the
    // two checks are independent and both need to hold.
    if (!isConeTap) syncPeriphFixUI();
    if (isPeriph) { syncPeriphKindUI(); syncPeriphFieldUI(); syncPeriphSizeUI(); syncPeriphColorUI(); }
    if (bgAllowed) syncBgUI();
    if (!isConeTap && !isPeriph) syncAddonUI();
    syncDurationUI();
    syncTempoUI();
    els.vtSaveForm.hidden = true;
    els.vtSaveBtn.hidden = false;
    renderVTSaved();
    showScreen("ready");
  }
  els.backToHome.addEventListener("click", () => showScreen(readyReturnScreen));

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
    recordCodeUsage(code);
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
  let periphPausedAt = null; // performance.now() timestamp while the Periph pause overlay is open, else null

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
      const color = cfg.dual ? (rng() < 0.5 ? GREEN : RED) : active.arrowColors[Math.floor(rng() * active.arrowColors.length)].hex;
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
    const colors = active.stroopColors;
    while (t < state.duration) {
      const wIdx = Math.floor(rng() * colors.length);
      const inkIdx = pick(colors, [wIdx], rng);
      let bg = currentBgFill("#ffffff");
      // With only 2 colours picked there's no third one left for the
      // background to stay distinct from both word and ink - fall back to
      // just excluding the word colour then (bg may equal ink; the render
      // code's outline keeps the word legible even so).
      if (cfg.bg) bg = colors[pick(colors, colors.length > 2 ? [wIdx, inkIdx] : [wIdx], rng)].hex;
      const word = colors[wIdx].name.toUpperCase();
      const ink = colors[inkIdx].hex;
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
      cfg.type === "periph" ? buildPeriphSchedule(cfg, rng) :
      buildArrowSchedule(cfg, rng);
  }
  const PERIPH_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ"; // I/O left out - too easily confused with 1/0
  const PERIPH_DIGITS = "0123456789";
  function randPeriphChar(kind, rng) {
    const pool = kind === "buchstaben" ? PERIPH_LETTERS
      : kind === "zahlen" ? PERIPH_DIGITS
      : (rng() < 0.5 ? PERIPH_LETTERS : PERIPH_DIGITS);
    return pool[Math.floor(rng() * pool.length)];
  }
  // Base angles (radians) each "Bereich" mode samples its stimuli around -
  // "Überall" ignores this and picks any angle at all.
  const PERIPH_FIELD_ANGLES = {
    horizontal: [0, Math.PI],
    vertikal: [Math.PI / 2, Math.PI * 1.5],
    diagonal: [Math.PI / 4, Math.PI * 0.75, Math.PI * 1.25, Math.PI * 1.75],
  };
  // Weighted random pick - "Dominanz": each item's own weight makes it
  // proportionally more likely, instead of every item having an equal
  // 1/n chance. A flat weight of 1 everywhere reduces to a plain equal pick.
  function weightedPick(items, weightFn, rng) {
    const weights = items.map(weightFn);
    const total = weights.reduce((a, b) => a + b, 0);
    let r = rng() * total;
    for (let i = 0; i < items.length; i++) {
      r -= weights[i];
      if (r <= 0) return items[i];
    }
    return items[items.length - 1];
  }
  // Every "Bereich" mode ends up as a simple {fx, fy} fraction of the canvas
  // (0..1), resolved to real pixels at render time - so a stimulus already
  // mid-flight still lands correctly if the device is rotated. Pulled out of
  // randPeriphPos() so the Zusatzaufgabe add-on (which has its own Bereich
  // config, either "übernehmen" from state or its own per-exercise "eigen"
  // bundle) can reuse the exact same positioning math instead of duplicating
  // it - cfg just needs {useZones, zones, axes, zoneWeights?}.
  function randPosFromCfg(cfg, rng) {
    if (cfg.useZones) {
      const zones = cfg.zones && cfg.zones.length ? cfg.zones : PERIPH_ZONE_KEYS;
      const zone = cfg.zoneWeights ? weightedPick(zones, (z) => cfg.zoneWeights[z] || 1, rng) : zones[Math.floor(rng() * zones.length)];
      const { row, col } = PERIPH_ZONES[zone];
      const pad = 0.14, cell = 1 / 3;
      return {
        fx: col * cell + pad * cell + rng() * cell * (1 - 2 * pad),
        fy: row * cell + pad * cell + rng() * cell * (1 - 2 * pad),
      };
    }
    // "Überall" isn't its own mode any more - selecting all three axes
    // (via the individual buttons or the "Überall" shortcut) covers it,
    // same as picking every colour does for the arrow exercises.
    const axes = cfg.axes && cfg.axes.length ? cfg.axes : PERIPH_AXIS_KEYS;
    const radiusFrac = 0.45 + rng() * 0.5;
    const axis = axes[Math.floor(rng() * axes.length)];
    const bases = PERIPH_FIELD_ANGLES[axis];
    const base = bases[Math.floor(rng() * bases.length)];
    const angle = base + (rng() - 0.5) * (Math.PI / 6); // ±15° jitter around the axis
    return { fx: 0.5 + 0.42 * radiusFrac * Math.cos(angle), fy: 0.5 + 0.42 * radiusFrac * Math.sin(angle) };
  }
  function randPeriphPos(rng) {
    return randPosFromCfg({ useZones: state.periphUseZones, zones: state.periphZones, axes: state.periphAxes, zoneWeights: state.periphZoneWeights }, rng);
  }
  // Two colours "clash" - one drawn on the other would be hard or impossible
  // to make out - if they're the same named colour, or close enough in
  // brightness that they'd blend (the same luma-distance check already used
  // for Stroop's word/background outline fix, just reused here).
  function colorsClash(hexA, hexB) {
    if (hexA.toLowerCase() === hexB.toLowerCase()) return true;
    return Math.abs(relLuma(hexA) - relLuma(hexB)) < 0.12;
  }
  // Picks a stimulus colour from the client's selection, situationally
  // avoiding whichever colour the background happens to be right now (a
  // fixed tint for most exercises, but a new colour every single frame for
  // VT/VRW/Kompass-Aufbau/Stroop mit Hintergrund, where the background IS
  // the trained stimulus) - so the client can never end up with, say, a red
  // character flashed on a red background. If every selected colour clashes
  // (most likely: only one colour is selected at all, so there's nothing
  // else to fall back to), keeps the full selection rather than picking
  // nothing - a rare near-invisible flash beats a crash.
  function pickPeriphColor(colorKeys, avoidHex, rng) {
    const all = keysToColors(colorKeys && colorKeys.length ? colorKeys : ["schwarz"], STROOP_COLOR_LIB);
    const safe = avoidHex ? all.filter((c) => !colorsClash(c.hex, avoidHex)) : all;
    const pool = safe.length ? safe : all;
    return pool[Math.floor(rng() * pool.length)].hex;
  }
  function buildPeriphSchedule(cfg, rng) {
    const schedule = [];
    let t = pushCountdown(schedule, cfg);
    const show = state.stimulusS;
    // Periph's own background is a flat tint, constant for the whole run
    // (it's never bgIsStimulus), so this only needs computing once.
    const bgHex = currentBgFill(NEUTRAL);
    while (t < state.duration) {
      const char = randPeriphChar(state.periphKind, rng);
      const pos = randPeriphPos(rng);
      const color = pickPeriphColor(state.periphColors, bgHex, rng);
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "periph", payload: { char, fx: pos.fx, fy: pos.fy, color } });
      schedule.push({ t0: t + show, t1: t + show + pause, kind: "blank", payload: {} });
      t += show + pause;
    }
    return { schedule, total: t };
  }

  // The background hex actually painted for one host schedule frame - most
  // kinds paint a flat, run-constant tint (see currentBgFill()), but VT/VRW/
  // Kompass-Aufbau/Stroop mit Hintergrund carry a fresh background colour in
  // their own payload every single frame (that colour IS the trained
  // stimulus there) - mirrors drawScene()'s own fill logic exactly, so a
  // Zusatzaufgabe flash always knows what it would actually be drawn on top
  // of, without having to render a frame to find out.
  function frameBgHex(frame) {
    if (frame.kind === "stroop" || frame.kind === "vt") return frame.payload.bg;
    if (frame.kind === "color") return frame.payload.color;
    if (frame.kind === "vrw") return frame.payload.direct ? frame.payload.color : "#ffffff";
    if (frame.kind === "cross" && frame.payload.mode === "audio") return "#e5f1f4";
    if (frame.kind === "blank" || frame.kind === "periph") return currentBgFill(NEUTRAL);
    return currentBgFill("#ffffff"); // "cue" (arrows) and cross's visual/conflict/invert branch: the flat top-level fill
  }
  // Standard ray-casting point-in-polygon test, used to keep a Zusatzaufgabe
  // flash off of a drawn arrow (see frameArrowPolygon()) rather than landing
  // right on top of it, where it'd be unreadable either way.
  function pointInPolygon(px, py, pts) {
    let inside = false;
    for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
      const [xi, yi] = pts[i], [xj, yj] = pts[j];
      const crosses = yi > py !== yj > py && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi;
      if (crosses) inside = !inside;
    }
    return inside;
  }
  // The arrow polygon a frame draws, in pixel space, or null for a frame
  // with no arrow to avoid (e.g. Kompass-Aufbau's flat colour, or Sehen &
  // Hören's audio-only frames, which show a speaker icon instead).
  function frameArrowPolygon(cw, ch, frame) {
    const drawsArrow = frame.kind === "cue" || frame.kind === "vt" || frame.kind === "vrw" ||
      (frame.kind === "cross" && frame.payload.mode !== "audio");
    if (!drawsArrow) return null;
    return arrowPoints(frame.payload.angle, cw / 2, ch / 2, Math.min(cw, ch) / 2);
  }

  // Zusatzaufgabe overlay schedule: subdivides the host exercise's own
  // schedule frames into the add-on's own show/gap timing, but only inside
  // the frame kinds the client enabled it for ("blank" = Pause, anything
  // else = Reiz) - so an add-on flash can never land outside its chosen
  // phase, whatever the host exercise's own timing looks like. Returns []
  // (i.e. nothing drawn) when the add-on is off for this exercise, or for
  // Periphere Wahrnehmung/Hütchen sortieren themselves. The 3-2-1 countdown
  // ("count" frames, always first) is neither Reiz nor Pause and is always
  // skipped, so the add-on never starts before the exercise itself does.
  // Each flash also situationally avoids the background colour in effect
  // during ITS OWN host frame (frameBgHex()) and, for a frame that draws an
  // arrow, re-rolls its position (a handful of tries) rather than landing
  // on top of it.
  function buildAddonSchedule(ex, exId, hostSchedule, rng) {
    if (!ex || ex.type === "color-tap" || ex.type === "periph") return { schedule: [], sizeMode: "gleich" };
    const entry = getAddonEntry(exId);
    if (!entry.phases.length) return { schedule: [], sizeMode: "gleich" };
    const cfg = entry.mode === "eigen" ? entry.own : addonConfigFromState();
    const phaseSet = new Set(entry.phases);
    const cw = canvas.width, ch = canvas.height;
    const schedule = [];
    hostSchedule.forEach((frame) => {
      if (frame.kind === "count") return;
      const phase = frame.kind === "blank" ? "pause" : "reiz";
      if (!phaseSet.has(phase)) return;
      const avoidHex = frameBgHex(frame);
      const polygon = frameArrowPolygon(cw, ch, frame);
      let t = frame.t0;
      const show = cfg.stimulusS;
      const gapMin = Math.min(cfg.intervalMin, cfg.intervalMax), gapMax = Math.max(cfg.intervalMin, cfg.intervalMax);
      while (t + show <= frame.t1) {
        const char = randPeriphChar(cfg.kind, rng);
        let pos = randPosFromCfg(cfg, rng);
        for (let tries = 0; polygon && tries < 12 && pointInPolygon(pos.fx * cw, pos.fy * ch, polygon); tries++) pos = randPosFromCfg(cfg, rng);
        const color = pickPeriphColor(cfg.colors, avoidHex, rng);
        schedule.push({ t0: t, t1: t + show, char, fx: pos.fx, fy: pos.fy, color });
        t += show + (gapMin + rng() * (gapMax - gapMin));
      }
    });
    return { schedule, sizeMode: cfg.sizeMode };
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
      drawAddonOverlay(elapsed);
    } else if (elapsed >= session.total) {
      finishSession();
      return;
    }
    const remaining = fmtClock(session.total - elapsed);
    els.timeEl.textContent = program ? `Übung ${program.chapterIndex + 1}/${program.def.blocks.length} · ${remaining}` : remaining;
    setProgress(program ? program.chapterIndex : 0, elapsed / session.total);
    raf = requestAnimationFrame(tick);
  }

  // Draws the Zusatzaufgabe's own peripheral flash (if this exercise has one
  // active right now) on top of whatever the host exercise's own frame just
  // drew - an independent overlay schedule, gated to the phases the client
  // enabled it for, see buildAddonSchedule().
  function drawAddonOverlay(elapsed) {
    if (!session.addonSchedule || !session.addonSchedule.length) return;
    const idx = session.addonSchedule.findIndex((f) => elapsed >= f.t0 && elapsed < f.t1);
    if (idx === -1) return;
    const f = session.addonSchedule[idx];
    const cw = canvas.width, ch = canvas.height, unit = Math.min(cw, ch) / 2;
    drawPeriphChar(cw, ch, unit, f.fx, f.fy, f.char, session.addonSizeMode, f.color);
  }

  // Redraws whatever frame is currently frozen on screen (used while the
  // Periph pause overlay is open) without touching the schedule/elapsed
  // time, so a live background/fixation-point tweak shows immediately.
  function redrawFrozenFrame() {
    if (!session || session.lastIndex < 0) return;
    const frame = session.schedule[session.lastIndex];
    if (frame) drawScene(frame.kind, frame.payload);
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
    els.periphPauseOverlay.hidden = true;
    periphPausedAt = null;
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
    els.rememberPlayer.hidden = true;
    els.blitzPlayer.hidden = true;
    els.flashPlayer.hidden = true;
    els.motPlayer.hidden = true;
    els.gngPlayer.hidden = true;
    els.testNbackPlayer.hidden = true;
    els.trailPlayer.hidden = true;
    els.flankerPlayer.hidden = true;
    els.ufovPlayer.hidden = true;
    els.posnerPlayer.hidden = true;
    els.rotationPlayer.hidden = true;
    els.merkPlayer.hidden = true;
    els.simonPlayer.hidden = true;
    els.searchPlayer.hidden = true;
    els.abPlayer.hidden = true;
    els.hickPlayer.hidden = true;
    els.corsiPlayer.hidden = true;
    els.reaktPlayer.hidden = true;
    els.tsPlayer.hidden = true;
    els.antiPlayer.hidden = true;
    els.stroopPlayer.hidden = true;
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
    els.periphPauseBtn.hidden = EXERCISES[state.exercise].type !== "periph";
    fitCanvas();
    ensureAudioCtx();
    const built = buildScheduleFor(EXERCISES[state.exercise], Math.random);
    const addon = buildAddonSchedule(EXERCISES[state.exercise], state.exercise, built.schedule, Math.random);
    session = { ...built, startTime: performance.now(), lastIndex: -1, addonSchedule: addon.schedule, addonSizeMode: addon.sizeMode };
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
    els.periphPauseBtn.hidden = true;
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
  wireSwipeNav(els.pauseScreen, {
    onLeft: () => els.nextChapterBtn.click(),
    onRight: () => els.prevChapterBtn.click(),
  });

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
    const startEx = EXERCISES[state.exercise];
    if (startEx.usesArrowColors && state.arrowColors.length < ARROW_MIN_COLORS) return;
    if (startEx.usesStroopColors && state.stroopColors.length < STROOP_MIN_COLORS) return;
    if (startEx.type === "periph" && !state.periphUseZones && state.periphAxes.length === 0) return;
    program = null;
    hideOverlays();
    active = { colors: keysToColors(state.colors), arrowColors: keysToColors(state.arrowColors), stroopColors: keysToColors(state.stroopColors, STROOP_COLOR_LIB) };
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
    showScreen(readyReturnScreen);
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

  // ---- Periph: pause mid-training to adjust background/fixation point ----
  // Reuses the same startTime-shift trick as the visibilitychange handler
  // below (backgrounding compensation), so the schedule never notices the
  // gap: elapsed time is always (now - session.startTime), so shifting
  // startTime forward by exactly the paused duration on resume makes the
  // pause invisible to the stimulus timing.
  els.periphPauseBtn.addEventListener("click", () => {
    if (!session || periphPausedAt) return;
    if (raf) cancelAnimationFrame(raf);
    raf = null;
    periphPausedAt = performance.now();
    syncBgUI();
    syncPeriphFixUI();
    els.periphPauseBtn.hidden = true;
    els.periphPauseOverlay.hidden = false;
  });
  els.periphResumeBtn.addEventListener("click", () => {
    if (!session || !periphPausedAt) return;
    session.startTime += performance.now() - periphPausedAt;
    periphPausedAt = null;
    els.periphPauseOverlay.hidden = true;
    els.periphPauseBtn.hidden = false;
    raf = requestAnimationFrame(tick);
  });

  // ---- VT: save the current settings under a name, reuse from the list ----
  const VT_SAVED_KEY = "fwmc-vt-saved-v1";
  const vtSavedStore = makePresetStore(VT_SAVED_KEY);
  function renderVTSaved() {
    renderPresetList(vtSavedStore, els.vtSavedList, els.vtSavedGroup, (e) => e.exercise === state.exercise,
      (e) => {
        const ex = EXERCISES[e.exercise];
        const usedColors = ex && ex.usesArrowColors ? e.arrowColors : ex && ex.usesStroopColors ? e.stroopColors : e.colors;
        return `${fmtMinutes(e.duration)}${usedColors && usedColors.length ? ` · ${usedColors.length} Farben` : ""}`;
      },
      (entry) => {
        state.colors = entry.colors.slice();
        if (entry.arrowColors) state.arrowColors = entry.arrowColors.slice();
        if (entry.stroopColors) state.stroopColors = entry.stroopColors.slice();
        state.duration = entry.duration;
        state.stimulusS = entry.stimulusS;
        state.intervalMin = entry.intervalMin;
        state.intervalMax = entry.intervalMax;
        savePrefs();
        active = { colors: keysToColors(state.colors), arrowColors: keysToColors(state.arrowColors), stroopColors: keysToColors(state.stroopColors, STROOP_COLOR_LIB) };
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
        colors: state.colors.slice(), arrowColors: state.arrowColors.slice(), stroopColors: state.stroopColors.slice(), duration: state.duration,
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
  wireFullscreen({ player: els.rememberPlayer, btn: els.rememberFsBtn, hint: els.rememberFsHint, hintOpen: els.rememberFsHintOpenBtn, hintClose: els.rememberFsHintClose });
  wireFullscreen({ player: els.blitzPlayer, btn: els.blitzFsBtn, hint: els.blitzFsHint, hintOpen: els.blitzFsHintOpenBtn, hintClose: els.blitzFsHintClose });
  wireFullscreen({ player: els.flashPlayer, btn: els.flashFsBtn, hint: els.flashFsHint, hintOpen: els.flashFsHintOpenBtn, hintClose: els.flashFsHintClose });
  wireFullscreen({ player: els.motPlayer, btn: els.motFsBtn, hint: els.motFsHint, hintOpen: els.motFsHintOpenBtn, hintClose: els.motFsHintClose });
  wireFullscreen({ player: els.gngPlayer, btn: els.gngFsBtn, hint: els.gngFsHint, hintOpen: els.gngFsHintOpenBtn, hintClose: els.gngFsHintClose });
  wireFullscreen({ player: els.testNbackPlayer, btn: els.testNbackFsBtn, hint: els.testNbackFsHint, hintOpen: els.testNbackFsHintOpenBtn, hintClose: els.testNbackFsHintClose });
  wireFullscreen({ player: els.trailPlayer, btn: els.trailFsBtn, hint: els.trailFsHint, hintOpen: els.trailFsHintOpenBtn, hintClose: els.trailFsHintClose });
  wireFullscreen({ player: els.flankerPlayer, btn: els.flankerFsBtn, hint: els.flankerFsHint, hintOpen: els.flankerFsHintOpenBtn, hintClose: els.flankerFsHintClose });
  wireFullscreen({ player: els.ufovPlayer, btn: els.ufovFsBtn, hint: els.ufovFsHint, hintOpen: els.ufovFsHintOpenBtn, hintClose: els.ufovFsHintClose });
  wireFullscreen({ player: els.posnerPlayer, btn: els.posnerFsBtn, hint: els.posnerFsHint, hintOpen: els.posnerFsHintOpenBtn, hintClose: els.posnerFsHintClose });
  wireFullscreen({ player: els.rotationPlayer, btn: els.rotationFsBtn, hint: els.rotationFsHint, hintOpen: els.rotationFsHintOpenBtn, hintClose: els.rotationFsHintClose });
  wireFullscreen({ player: els.merkPlayer, btn: els.merkFsBtn, hint: els.merkFsHint, hintOpen: els.merkFsHintOpenBtn, hintClose: els.merkFsHintClose });
  wireFullscreen({ player: els.simonPlayer, btn: els.simonFsBtn, hint: els.simonFsHint, hintOpen: els.simonFsHintOpenBtn, hintClose: els.simonFsHintClose });
  wireFullscreen({ player: els.searchPlayer, btn: els.searchFsBtn, hint: els.searchFsHint, hintOpen: els.searchFsHintOpenBtn, hintClose: els.searchFsHintClose });
  wireFullscreen({ player: els.abPlayer, btn: els.abFsBtn, hint: els.abFsHint, hintOpen: els.abFsHintOpenBtn, hintClose: els.abFsHintClose });
  wireFullscreen({ player: els.antizipPlayer, btn: els.antizipFsBtn, hint: els.antizipFsHint, hintOpen: els.antizipFsHintOpenBtn, hintClose: els.antizipFsHintClose });
  wireFullscreen({ player: els.hickPlayer, btn: els.hickFsBtn, hint: els.hickFsHint, hintOpen: els.hickFsHintOpenBtn, hintClose: els.hickFsHintClose });
  wireFullscreen({ player: els.corsiPlayer, btn: els.corsiFsBtn, hint: els.corsiFsHint, hintOpen: els.corsiFsHintOpenBtn, hintClose: els.corsiFsHintClose });
  wireFullscreen({ player: els.reaktPlayer, btn: els.reaktFsBtn, hint: els.reaktFsHint, hintOpen: els.reaktFsHintOpenBtn, hintClose: els.reaktFsHintClose });
  wireFullscreen({ player: els.tsPlayer, btn: els.tsFsBtn, hint: els.tsFsHint, hintOpen: els.tsFsHintOpenBtn, hintClose: els.tsFsHintClose });
  wireFullscreen({ player: els.antiPlayer, btn: els.antiFsBtn, hint: els.antiFsHint, hintOpen: els.antiFsHintOpenBtn, hintClose: els.antiFsHintClose });
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
  // FAQ sheet: one shared overlay, reachable from every section's footer
  // (".faq-open-btn" appears once per site-footer, six in total) - unlike
  // the Tips sheets above this is a repeatedly-reopenable reference, not a
  // one-time onboarding hint, so closing it never writes a "seen" flag.
  let faqReturnFocus = null;
  function openFaq() { faqReturnFocus = document.activeElement; els.faqSheet.hidden = false; focusFirstIn(els.faqSheet); }
  function closeFaq() { els.faqSheet.hidden = true; if (faqReturnFocus) faqReturnFocus.focus(); }
  document.querySelectorAll(".faq-open-btn").forEach((btn) => btn.addEventListener("click", openFaq));
  els.faqCloseBtn.addEventListener("click", closeFaq);
  els.faqSheet.addEventListener("click", (e) => { if (e.target === els.faqSheet) closeFaq(); });
  els.faqSheet.addEventListener("keydown", (e) => trapTabKey(els.faqSheet, e));
  // ==== Master-Einstellungen: a no-login "profile" (added 2026-09-27,
  // client's own framing) ====
  // Everything here lives in ONE localStorage key, same convention as every
  // other *Prefs object in this file - just cross-cutting instead of
  // per-exercise. Two concerns share the sheet: (1) accessibility/physical
  // presets that would otherwise need re-setting in every exercise's own
  // Feineinstellungen every time, and (2) a locally-remembered list of
  // Trainings-Codes the client has typed in, so they don't have to keep
  // retyping/re-finding one from the coach. Both are explicitly LOCAL-ONLY -
  // the sheet's own first line says so, matching the FAQ's existing "wo
  // werden meine Trainingsdaten gespeichert" answer.
  const MASTER_PREFS_KEY = "fwmc-master-v1";
  const masterPrefs = { colorVision: "normal", limb: "none", hearing: "normal" };
  function loadMasterPrefs() {
    const saved = readJSON(MASTER_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(masterPrefs, saved);
    if (masterPrefs.colorVision !== "normal" && masterPrefs.colorVision !== "rotgruen") masterPrefs.colorVision = "normal";
    if (!["none", "armL", "armR"].includes(masterPrefs.limb)) masterPrefs.limb = "none";
    if (masterPrefs.hearing !== "normal" && masterPrefs.hearing !== "gehoerlos") masterPrefs.hearing = "normal";
  }
  function saveMasterPrefs() { writeJSON(MASTER_PREFS_KEY, masterPrefs); }
  loadMasterPrefs();

  // Colour-vision preset: today only Go/No-Go has a genuine red/green
  // discrimination signal (every other exercise's colour is either neutral
  // or already colour-blind-safe, e.g. Simon's blue/orange - see CLAUDE.md's
  // colour-clash audit) - applied as a body class so styles.css can override
  // just `.gng-stimulus.go/.nogo` without touching GNG's own code. Reusing
  // Simon's own blue/orange pair keeps the app's "safe pair" consistent
  // rather than inventing a second one.
  function applyColorVisionMode() {
    document.body.classList.toggle("cvd-rotgruen", masterPrefs.colorVision === "rotgruen");
  }
  document.querySelectorAll("[data-master-cvd]").forEach((el) => el.addEventListener("click", () => {
    masterPrefs.colorVision = el.dataset.masterCvd; saveMasterPrefs(); applyColorVisionMode(); syncMasterCvdUI();
  }));
  function syncMasterCvdUI() { document.querySelectorAll("[data-master-cvd]").forEach((el) => setActive(el, el.dataset.masterCvd === masterPrefs.colorVision)); }
  applyColorVisionMode();

  document.querySelectorAll("[data-master-limb]").forEach((el) => el.addEventListener("click", () => {
    masterPrefs.limb = el.dataset.masterLimb; saveMasterPrefs(); syncMasterLimbUI(); applyMovementLimbFilter();
  }));
  function syncMasterLimbUI() { document.querySelectorAll("[data-master-limb]").forEach((el) => setActive(el, el.dataset.masterLimb === masterPrefs.limb)); }

  document.querySelectorAll("[data-master-hearing]").forEach((el) => el.addEventListener("click", () => {
    masterPrefs.hearing = el.dataset.masterHearing; saveMasterPrefs(); syncMasterHearingUI(); applyExerciseCompatibility();
  }));
  function syncMasterHearingUI() { document.querySelectorAll("[data-master-hearing]").forEach((el) => setActive(el, el.dataset.masterHearing === masterPrefs.hearing)); }

  // ---- Exercise compatibility: greyed out + marked, not hidden ----
  // Unlike Farbsehen (which ADAPTS an exercise, e.g. Go/No-Go's colour swap)
  // some master restrictions make an exercise genuinely unusable - today
  // just "Gehörlos" vs any exercise tagged "ton" (VT's own existing
  // ton/ohne-ton filter tag, reused here rather than a second parallel
  // list - "Sehen & Hören" is the only one right now). Reusable for future
  // exercises/restrictions: add a tag, extend the `blocked` check below.
  function exerciseBlockedReason(card) {
    const tags = (card.dataset.tags || "").split(/\s+/);
    if (masterPrefs.hearing === "gehoerlos" && tags.includes("ton")) return "Benötigt Ton – in Einstellungen anpassbar";
    return null;
  }
  function applyExerciseCompatibility() {
    document.querySelectorAll(".excard").forEach((card) => {
      const reason = exerciseBlockedReason(card);
      card.classList.toggle("incompatible", !!reason);
      let note = card.querySelector(".excard-blocked-note");
      if (reason) {
        if (!note) {
          note = document.createElement("span");
          note.className = "excard-blocked-note";
          card.appendChild(note);
        }
        note.textContent = reason;
      } else if (note) {
        note.remove();
      }
    });
  }
  applyExerciseCompatibility();

  const CODE_HISTORY_KEY = "fwmc-code-history-v1";
  const CODE_HISTORY_MAX = 20;
  function loadCodeHistory() {
    const list = readJSON(CODE_HISTORY_KEY, []);
    return Array.isArray(list) ? list : [];
  }
  function recordCodeUsage(code) {
    const list = loadCodeHistory();
    const today = new Date().toISOString().slice(0, 10);
    const existing = list.find((h) => h.code === code);
    if (existing) existing.lastUsed = today;
    else list.push({ code, firstUsed: today, lastUsed: today });
    list.sort((a, b) => b.lastUsed.localeCompare(a.lastUsed));
    writeJSON(CODE_HISTORY_KEY, list.slice(0, CODE_HISTORY_MAX));
  }
  function renderMasterCodeHistory() {
    const history = loadCodeHistory();
    els.masterCodeHistoryGroup.hidden = history.length === 0;
    els.masterCodeHistoryList.innerHTML = "";
    history.forEach((h) => {
      const wrap = document.createElement("div");
      wrap.className = "bundle-item-wrap";
      const item = document.createElement("button");
      item.className = "bundle-item";
      item.innerHTML = `<div class="bundle-item-head"><strong>${esc(h.code)}</strong></div>` +
        `<span class="bundle-meta">zuerst ${formatDateDE(h.firstUsed)} &middot; zuletzt ${formatDateDE(h.lastUsed)}</span>`;
      item.addEventListener("click", () => { closeMasterSettings(); openProgramIntro(h.code); });
      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "combo-block-remove";
      copyBtn.setAttribute("aria-label", "Code kopieren");
      copyBtn.textContent = "⧉";
      copyBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        try {
          await navigator.clipboard.writeText(h.code);
          copyBtn.textContent = "✓";
          setTimeout(() => { copyBtn.textContent = "⧉"; }, 1200);
        } catch (err) { /* clipboard API unavailable/denied - silently no-op, copy just doesn't happen */ }
      });
      wrap.appendChild(item);
      wrap.appendChild(copyBtn);
      els.masterCodeHistoryList.appendChild(wrap);
    });
  }

  let masterSettingsReturnFocus = null;
  function openMasterSettings() {
    masterSettingsReturnFocus = document.activeElement;
    syncMasterCvdUI(); syncMasterLimbUI(); syncMasterHearingUI(); renderMasterCodeHistory();
    els.masterSettingsSheet.hidden = false;
    focusFirstIn(els.masterSettingsSheet);
  }
  function closeMasterSettings() {
    els.masterSettingsSheet.hidden = true;
    if (masterSettingsReturnFocus) masterSettingsReturnFocus.focus();
  }
  document.querySelectorAll(".master-settings-btn").forEach((btn) => btn.addEventListener("click", openMasterSettings));
  els.masterSettingsCloseBtn.addEventListener("click", closeMasterSettings);
  els.masterSettingsSheet.addEventListener("click", (e) => { if (e.target === els.masterSettingsSheet) closeMasterSettings(); });
  els.masterSettingsSheet.addEventListener("keydown", (e) => trapTabKey(els.masterSettingsSheet, e));

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!els.tipsSheet.hidden) closeTips();
    if (!els.breathTipsSheet.hidden) closeBreathTips();
    if (!els.faqSheet.hidden) closeFaq();
    if (!els.masterSettingsSheet.hidden) closeMasterSettings();
    if (!els.videoModal.hidden) closeVideoModal();
    if (!els.setupModal.hidden) closeSetupModal();
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
  const MOVEMENT_DIRECTIONS = ["rechts", "links", "oben", "unten"];
  const movementPrefs = {
    movements: MOVEMENTS.map((m) => m.id),
    preview: 3, bpm: 60, durationMin: 1, mirror: true, showLabel: true, figureStyle: "figur", direction: "rechts",
  };
  function loadMovementPrefs() {
    const saved = readJSON(MOVEMENT_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(movementPrefs, saved);
    if (!Array.isArray(movementPrefs.movements) || movementPrefs.movements.length < MIN_MOVEMENTS) {
      movementPrefs.movements = MOVEMENTS.map((m) => m.id);
    }
    if (movementPrefs.figureStyle !== "figur" && movementPrefs.figureStyle !== "abstrakt") movementPrefs.figureStyle = "figur";
    if (!MOVEMENT_DIRECTIONS.includes(movementPrefs.direction)) movementPrefs.direction = "rechts";
  }
  function saveMovementPrefs() { writeJSON(MOVEMENT_PREFS_KEY, movementPrefs); }
  loadMovementPrefs();

  // Master-Einstellungen's "Bewegungseinschränkung" (nur linker/rechter Arm)
  // excludes the OTHER arm's movements everywhere Movement builds its pool
  // from - both the picker (so a client with one usable arm never even sees
  // a chip for the other) and the actual play pool, so it's a genuine
  // cross-cutting default rather than something re-picked per session.
  function movementAllowedByLimb(m) {
    if (masterPrefs.limb === "armL" && m.limb === "armR") return false;
    if (masterPrefs.limb === "armR" && m.limb === "armL") return false;
    return true;
  }
  function renderMovementPickerChips() {
    els.movementPicker.innerHTML = "";
    MOVEMENTS.filter(movementAllowedByLimb).forEach((m) => {
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
  }
  // Called at load and whenever the master limb setting changes - drops any
  // now-disallowed movement from the saved selection (falling back to
  // "everything still allowed" if that would leave too few) and rebuilds
  // the picker so it never offers a chip that can't actually be played.
  function applyMovementLimbFilter() {
    const allowedIds = MOVEMENTS.filter(movementAllowedByLimb).map((m) => m.id);
    movementPrefs.movements = movementPrefs.movements.filter((id) => allowedIds.includes(id));
    if (movementPrefs.movements.length < MIN_MOVEMENTS) movementPrefs.movements = allowedIds.slice();
    saveMovementPrefs();
    renderMovementPickerChips();
    syncMvPickerUI();
  }
  applyMovementLimbFilter();
  function syncMvPickerUI() {
    els.movementPicker.querySelectorAll(".movement-chip").forEach((el) => {
      setActive(el, movementPrefs.movements.includes(el.dataset.moveId));
      const m = MOVEMENT_BY_ID[el.dataset.moveId];
      const svg = el.querySelector(".figure-svg");
      if (svg) svg.outerHTML = figureSVG(resolveSlots([m], true), "var(--ink)");
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

  document.querySelectorAll("[data-mv-figure]").forEach((el) => el.addEventListener("click", () => { movementPrefs.figureStyle = el.dataset.mvFigure; saveMovementPrefs(); syncMvFigureUI(); syncMvPickerUI(); }));
  function syncMvFigureUI() { document.querySelectorAll("[data-mv-figure]").forEach((el) => setActive(el, el.dataset.mvFigure === movementPrefs.figureStyle)); }

  document.querySelectorAll("[data-mv-direction]").forEach((el) => el.addEventListener("click", () => { movementPrefs.direction = el.dataset.mvDirection; saveMovementPrefs(); syncMvDirectionUI(); }));
  function syncMvDirectionUI() { document.querySelectorAll("[data-mv-direction]").forEach((el) => setActive(el, el.dataset.mvDirection === movementPrefs.direction)); }

  function openMovementReady() {
    syncMvPickerUI(); syncMvPreviewUI(); syncMvTempoUI(); syncMvDurationUI(); syncMvMirrorUI(); syncMvLabelUI(); syncMvFigureUI(); syncMvDirectionUI();
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
  // Fixed at 2 (not another Feineinstellung to expose): enough "done" tiles
  // behind the active one that it reads as a continuous strip flowing past
  // a fixed centre - see CLAUDE.md's Movement section for why this exists
  // (was active-tile-first with nothing behind it, which didn't match the
  // "runs in from one edge, whatever's centred on the beat counts" feel the
  // client described).
  const MOVEMENT_PAST_COUNT = 2;
  function renderMovementLaneWindow(seq, beatIdx, preview, mirrored, showLabel) {
    els.movementLane.className = "movement-lane dir-" + movementPrefs.direction;
    els.movementLane.innerHTML = "";
    const pastStart = Math.max(0, beatIdx - MOVEMENT_PAST_COUNT);
    for (let i = pastStart; i < beatIdx; i++) {
      const m = seq[i];
      if (!m) continue;
      const tile = document.createElement("div");
      tile.className = "movement-tile done";
      tile.innerHTML = movementTileHTML(m, mirrored, showLabel);
      els.movementLane.appendChild(tile);
    }
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

  // ==== NAT · Remember: spatial sequence memory game ====
  // A number appears somewhere on screen and stays there; more numbers get
  // added one at a time, then all get covered and must be tapped back in
  // order (1, 2, 3, ...). Three variants, sharing one engine:
  // - "fixed": already-placed numbers keep last round's spot, only the new
  //   one gets a fresh position.
  // - "shuffle": every number - old and new - gets reshuffled together.
  // - "training": you pick your own starting count (instead of always 2)
  //   and can skip freely up/down with the on-screen nav during play;
  //   because that manual skipping breaks the "kept last round's spot"
  //   assumption, positions always reshuffle fresh here, same as "shuffle".
  // Endless/progressive - there's no fixed end, so the only way to finish
  // is "Beenden", which doubles as the finish action (shows a summary)
  // once at least the first round has been cleared.
  const REMEMBER_MODES = {
    fixed: { id: "fixed", title: "Feste Positionen", keepPositions: true },
    shuffle: { id: "shuffle", title: "Bewegte Positionen", keepPositions: false },
    training: { id: "training", title: "Trainingsmodus", keepPositions: false },
  };
  // Schwierigkeit sets how long a round is shown: a base time for the
  // first (2-number) round, plus extra time for every number beyond that.
  // Higher values on both = more generous = easier.
  const REMEMBER_DIFFICULTIES = {
    leicht: { title: "Leicht", revealBaseS: 1.8, revealStepS: 0.5 },
    mittel: { title: "Mittel", revealBaseS: 1.1, revealStepS: 0.3 },
    schwer: { title: "Schwer", revealBaseS: 0.7, revealStepS: 0.15 },
  };
  // Bei Fehler (Feste/Bewegte Positionen only - Trainingsmodus always
  // resets to its own configured start number, see rememberClick below):
  // "reset2" restarts from 2 like before, "backOne" drops one level, "stay"
  // repeats the same level until it's cleared.
  const REMEMBER_PREFS_KEY = "fwmc-remember-prefs-v1";
  const rememberPrefs = {
    revealBaseS: REMEMBER_DIFFICULTIES.mittel.revealBaseS,
    revealStepS: REMEMBER_DIFFICULTIES.mittel.revealStepS,
    errorMode: "reset2",
    trainingStart: 8,
    trainingProgress: true,
    trainingPositionMode: "shuffle",
    bgColorKey: "gruen",
    bgIntensity: 0,
  };
  function loadRememberPrefs() {
    const saved = readJSON(REMEMBER_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(rememberPrefs, saved);
    if (!STROOP_COLOR_BY_KEY[rememberPrefs.bgColorKey]) rememberPrefs.bgColorKey = "gruen";
    if (typeof rememberPrefs.bgIntensity !== "number" || rememberPrefs.bgIntensity < 0 || rememberPrefs.bgIntensity > 1) rememberPrefs.bgIntensity = 0;
  }
  function saveRememberPrefsToStorage() { writeJSON(REMEMBER_PREFS_KEY, rememberPrefs); }
  loadRememberPrefs();

  // Remember has no canvas - the tint goes straight on the DOM stage that
  // holds the number markers, applied fresh whenever a game starts (in
  // case the prefs changed since the stage was last shown) and again on
  // every live edit (ready screen or the mid-game pause overlay).
  function applyRememberBg() {
    els.rememberStage.style.background = rememberPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[rememberPrefs.bgColorKey].hex, rememberPrefs.bgIntensity)
      : "";
  }
  const syncRememberBgUI = wireBgIntensityControl(rememberPrefs, {
    pickers: [els.rememberBgColorPicker, els.rememberTrainingBgColorPicker, els.rememberPauseBgColorPicker],
    sliders: [els.rememberBgIntensitySlider, els.rememberTrainingBgIntensitySlider, els.rememberPauseBgSlider],
    valueEls: [els.rememberBgIntensityValue, els.rememberTrainingBgIntensityValue, els.rememberPauseBgValue],
    hintEls: [els.rememberBgContrastHint, els.rememberTrainingBgContrastHint],
    transfer: [
      {
        sourceRow: els.rememberBgSourceRow, presetGroup: els.rememberBgPresetGroup, presetList: els.rememberBgPresetList,
        saveBtn: els.rememberBgSaveBtn, form: els.rememberBgSaveForm, nameInput: els.rememberBgSaveNameInput,
        cancelBtn: els.rememberBgSaveCancelBtn, confirmBtn: els.rememberBgSaveConfirmBtn,
      },
      {
        sourceRow: els.rememberTrainingBgSourceRow, presetGroup: els.rememberTrainingBgPresetGroup, presetList: els.rememberTrainingBgPresetList,
        saveBtn: els.rememberTrainingBgSaveBtn, form: els.rememberTrainingBgSaveForm, nameInput: els.rememberTrainingBgSaveNameInput,
        cancelBtn: els.rememberTrainingBgSaveCancelBtn, confirmBtn: els.rememberTrainingBgSaveConfirmBtn,
      },
    ],
  }, () => { saveRememberPrefsToStorage(); applyRememberBg(); }, "remember");

  function rememberDifficultyBucket() {
    for (const key of Object.keys(REMEMBER_DIFFICULTIES)) {
      const p = REMEMBER_DIFFICULTIES[key];
      if (Math.abs(p.revealBaseS - rememberPrefs.revealBaseS) < 0.001 && Math.abs(p.revealStepS - rememberPrefs.revealStepS) < 0.001) return key;
    }
    return "custom";
  }
  // { fixed: {leicht:N, mittel:N, schwer:N, custom:N}, shuffle: {...}, training: N }
  const REMEMBER_BEST_KEY = "fwmc-remember-best-v1";
  function rememberBestFor(mode) {
    const all = readJSON(REMEMBER_BEST_KEY, {});
    if (mode === "training") return all.training || 0;
    return (all[mode] && all[mode][rememberDifficultyBucket()]) || 0;
  }
  function rememberOverallBestFor(mode) {
    const all = readJSON(REMEMBER_BEST_KEY, {});
    if (mode === "training") return all.training || 0;
    const byDifficulty = all[mode] || {};
    return Math.max(0, ...Object.values(byDifficulty));
  }
  function saveRememberBest(mode, level) {
    const all = readJSON(REMEMBER_BEST_KEY, {});
    if (mode === "training") {
      if (level > (all.training || 0)) { all.training = level; writeJSON(REMEMBER_BEST_KEY, all); return true; }
      return false;
    }
    if (!all[mode]) all[mode] = {};
    const bucket = rememberDifficultyBucket();
    if (level > (all[mode][bucket] || 0)) { all[mode][bucket] = level; writeJSON(REMEMBER_BEST_KEY, all); return true; }
    return false;
  }
  function renderRememberBests() {
    const f = rememberOverallBestFor("fixed");
    const s = rememberOverallBestFor("shuffle");
    const t = rememberOverallBestFor("training");
    els.rememberBestFixed.textContent = f ? `Bestleistung: ${f}` : "";
    els.rememberBestShuffle.textContent = s ? `Bestleistung: ${s}` : "";
    els.rememberBestTraining.textContent = t ? `Bestleistung: ${t}` : "";
  }
  renderRememberBests();

  // ---- Difficulty picker, shared by the fixed/shuffle Ready screen and
  // the Trainingsmodus Ready screen (each has its own set of DOM elements
  // but the same underlying rememberPrefs and sync logic). ----
  function wireRememberDifficultyUI(cfg) {
    document.querySelectorAll(cfg.rowSelector + " [data-remember-diff]").forEach((el) => {
      el.addEventListener("click", () => {
        Object.assign(rememberPrefs, REMEMBER_DIFFICULTIES[el.dataset.rememberDiff]);
        saveRememberPrefsToStorage();
        cfg.sync();
      });
    });
    cfg.revealSlider.addEventListener("input", () => {
      rememberPrefs.revealBaseS = Number(cfg.revealSlider.value);
      saveRememberPrefsToStorage();
      cfg.sync();
    });
    cfg.stepSlider.addEventListener("input", () => {
      rememberPrefs.revealStepS = Number(cfg.stepSlider.value);
      saveRememberPrefsToStorage();
      cfg.sync();
    });
  }
  function syncRememberDifficultyUI(cfg) {
    let any = false;
    document.querySelectorAll(cfg.rowSelector + " [data-remember-diff]").forEach((el) => {
      const p = REMEMBER_DIFFICULTIES[el.dataset.rememberDiff];
      const on = Math.abs(p.revealBaseS - rememberPrefs.revealBaseS) < 0.001 && Math.abs(p.revealStepS - rememberPrefs.revealStepS) < 0.001;
      if (on) any = true;
      setActive(el, on);
    });
    cfg.custom.hidden = any;
    cfg.revealSlider.value = rememberPrefs.revealBaseS;
    cfg.revealValue.textContent = fmtSeconds(rememberPrefs.revealBaseS);
    cfg.stepSlider.value = rememberPrefs.revealStepS;
    cfg.stepValue.textContent = fmtSeconds(rememberPrefs.revealStepS);
  }

  let rememberState = null; // { mode, level, cleared, positions, phase, nextExpected, startTime, timer, revealBaseS, revealStepS, trainingStart, trainingProgress }
  let rememberReturnScreen = "natHome";

  // Placement works in real pixels (not raw percent) so the no-overlap
  // guarantee is exact regardless of the stage's aspect ratio - a phone
  // screen is much taller than wide, so equal percent distances on the x
  // and y axes are very different absolute distances. MIN_CENTER_PX is
  // the marker's own diameter plus a visible gap, i.e. the true minimum
  // centre-to-centre distance for two markers to never touch.
  const REMEMBER_MARKER_PX = 72;
  const REMEMBER_MIN_CENTER_PX = REMEMBER_MARKER_PX + 10;
  function rememberStageBounds() {
    const rect = els.rememberStage.getBoundingClientRect();
    const w = rect.width || 390;
    const h = rect.height || 600;
    const half = REMEMBER_MARKER_PX / 2;
    const minY = stageTopClearanceY(rect, els.rememberHint, els.rememberPlayerBar, 112, half);
    return { w, h, minX: half + 8, maxX: Math.max(half + 8, w - half - 8), minY, maxY: Math.max(minY, h - 16) };
  }
  function randomRememberPixelPosition(existingPx, bounds) {
    for (let attempt = 0; attempt < 300; attempt++) {
      const x = bounds.minX + Math.random() * (bounds.maxX - bounds.minX);
      const y = bounds.minY + Math.random() * (bounds.maxY - bounds.minY);
      if (!existingPx.some((p) => Math.hypot(p.x - x, p.y - y) < REMEMBER_MIN_CENTER_PX)) return { x, y };
    }
    // Crowded fallback (many markers in a small area): scan a fine grid of
    // candidates and take whichever is farthest from every existing marker,
    // so it's always the best available spot rather than a blind overlap.
    let best = null, bestDist = -1;
    const STEPS = 24;
    for (let gx = 0; gx <= STEPS; gx++) {
      for (let gy = 0; gy <= STEPS; gy++) {
        const x = bounds.minX + (gx / STEPS) * (bounds.maxX - bounds.minX);
        const y = bounds.minY + (gy / STEPS) * (bounds.maxY - bounds.minY);
        const dist = existingPx.length ? Math.min(...existingPx.map((p) => Math.hypot(p.x - x, p.y - y))) : Infinity;
        if (dist > bestDist) { bestDist = dist; best = { x, y }; }
      }
    }
    return best;
  }
  // "keep" (fixed positions): every number's spot is looked up in
  // rememberState.positionCache, keyed by its own number, and only
  // generated once, the first time that number is ever shown - so jumping
  // back down (Trainingsmodus nav) and back up again always finds the same
  // numbers exactly where they were, not just "whatever last round had".
  // Without "keep" (shuffle), the cache is ignored and every number gets a
  // fresh spot on every call.
  function buildRememberPositions(count, keep) {
    const bounds = rememberStageBounds();
    const cache = keep && rememberState ? rememberState.positionCache : null;
    const positions = [];
    const existingPx = [];
    for (let num = 1; num <= count; num++) {
      const cached = cache && cache[num];
      if (cached) {
        positions.push({ num, x: cached.x, y: cached.y });
        existingPx.push({ x: (cached.x / 100) * bounds.w, y: (cached.y / 100) * bounds.h });
      } else {
        const px = randomRememberPixelPosition(existingPx, bounds);
        existingPx.push(px);
        const pos = { num, x: (px.x / bounds.w) * 100, y: (px.y / bounds.h) * 100 };
        if (cache) cache[num] = { x: pos.x, y: pos.y };
        positions.push(pos);
      }
    }
    return positions;
  }
  function renderRememberMarkers() {
    els.rememberStage.querySelectorAll(".remember-marker").forEach((el) => el.remove());
    rememberState.positions.forEach((p) => {
      const el = document.createElement("button");
      const covered = rememberState.phase === "covered";
      el.className = "remember-marker" + (covered ? " covered" : "");
      el.style.left = p.x + "%";
      el.style.top = p.y + "%";
      el.textContent = covered ? "" : String(p.num);
      // A covered marker must not have its number in the accessible name -
      // that would hand a screen reader user the answer - so it gets a
      // plain, identical-for-all label instead of being left unlabelled.
      if (covered) el.setAttribute("aria-label", "Verdecktes Zahlenfeld");
      else el.removeAttribute("aria-label");
      el.dataset.num = p.num;
      if (covered) el.addEventListener("click", () => rememberClick(p.num, el));
      els.rememberStage.appendChild(el);
    });
  }
  // Wraps every rememberState.timer scheduling so Pause can later work out
  // "how much longer was this waiting" and reschedule the exact same
  // callback with the remaining time on Resume, instead of restarting the
  // whole reveal/cover cycle from scratch.
  function scheduleRememberTimer(fn, delayMs) {
    rememberState.timerFn = fn;
    rememberState.timerFiresAt = performance.now() + delayMs;
    rememberState.timer = setTimeout(fn, delayMs);
  }
  function startRememberLevel() {
    // Hint/level text set BEFORE buildRememberPositions() - rememberStageBounds()
    // measures #rememberHint's live rendered height (see stageTopClearanceY),
    // which only reflects whatever text is in the DOM at that moment; reading
    // it before updating the text would still see the PREVIOUS round's
    // (possibly shorter, e.g. empty on the very first round) hint.
    els.rememberHint.textContent = "Merken …";
    els.rememberLevelEl.textContent = `${rememberState.level} Zahlen`;
    rememberState.positions = buildRememberPositions(rememberState.level, rememberState.keepPositions);
    rememberState.phase = "reveal";
    rememberState.nextExpected = 1;
    renderRememberMarkers();
    const extra = Math.max(0, rememberState.level - 2) * rememberState.revealStepS;
    const revealMs = Math.min(6000, Math.max(300, (rememberState.revealBaseS + extra) * 1000));
    scheduleRememberTimer(coverRememberLevel, revealMs);
  }
  function coverRememberLevel() {
    if (!rememberState) return;
    rememberState.phase = "covered";
    els.rememberHint.textContent = "Jetzt in der richtigen Reihenfolge antippen";
    renderRememberMarkers();
  }
  // Manual skip nav (Trainingsmodus only): jump straight to a given level,
  // clamped between the chosen starting number and a practical ceiling -
  // past that many markers, a phone screen can no longer fit them all with
  // a guaranteed non-overlapping gap.
  const REMEMBER_MAX_LEVEL = 24;
  function rememberGoToLevel(newLevel) {
    if (!rememberState || rememberState.mode !== "training" || rememberState.paused) return;
    if (rememberState.timer) clearTimeout(rememberState.timer);
    rememberState.level = Math.min(REMEMBER_MAX_LEVEL, Math.max(rememberState.trainingStart, newLevel));
    startRememberLevel();
  }
  function rememberClick(num, el) {
    if (!rememberState || rememberState.phase !== "covered" || rememberState.paused) return;
    if (num === rememberState.nextExpected) {
      el.classList.add("correct");
      el.textContent = String(num);
      el.style.pointerEvents = "none";
      rememberState.nextExpected += 1;
      if (rememberState.nextExpected > rememberState.level) {
        if (rememberState.level > rememberState.cleared) rememberState.cleared = rememberState.level;
        rememberState.phase = "success";
        els.rememberHint.textContent = "Richtig! Weiter geht's …";
        els.rememberStage.querySelectorAll(".remember-marker").forEach((m) => { m.textContent = m.dataset.num; m.style.pointerEvents = "none"; m.classList.remove("covered"); });
        const stayPut = rememberState.mode === "training" && !rememberState.trainingProgress;
        if (!stayPut) rememberState.level = Math.min(REMEMBER_MAX_LEVEL, rememberState.level + 1);
        scheduleRememberTimer(startRememberLevel, 900);
      }
    } else {
      rememberState.phase = "checking";
      el.classList.add("wrong");
      el.textContent = String(num);
      els.rememberStage.querySelectorAll(".remember-marker").forEach((m) => { m.textContent = m.dataset.num; m.style.pointerEvents = "none"; m.classList.remove("covered"); });
      let resetLevel, hint;
      if (rememberState.mode === "training") {
        resetLevel = rememberState.trainingStart;
        rememberState.positionCache = {};
        hint = "Leider falsch – nochmal von vorne";
      } else if (rememberState.errorMode === "stay") {
        resetLevel = rememberState.level;
        hint = "Leider falsch – nochmal versuchen";
      } else if (rememberState.errorMode === "backOne") {
        resetLevel = Math.max(2, rememberState.level - 1);
        hint = "Leider falsch – eine Zahl zurück";
      } else {
        resetLevel = 2;
        rememberState.positionCache = {};
        hint = "Leider falsch – nochmal von vorne";
      }
      els.rememberHint.textContent = hint;
      scheduleRememberTimer(() => { rememberState.level = resetLevel; startRememberLevel(); }, 1400);
    }
  }
  let lastRememberMode = null;
  function startRememberGame(mode, opts) {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.rememberPlayer.hidden = false;
    els.rememberPlayerBar.hidden = false;
    els.rememberDonePanel.hidden = true;
    els.rememberNav.hidden = mode !== "training";
    els.rememberPauseOverlay.hidden = true;
    els.rememberPauseBtn.hidden = false;
    lastRememberMode = mode;
    rememberReturnScreen = mode === "training" ? "rememberTrainingReady" : "rememberReady";
    const startLevel = mode === "training" ? rememberPrefs.trainingStart : 2;
    const keepPositions = mode === "training" ? rememberPrefs.trainingPositionMode === "fixed" : REMEMBER_MODES[mode].keepPositions;
    rememberState = {
      mode, level: startLevel, cleared: 0, positions: [], phase: "reveal", nextExpected: 1,
      startTime: performance.now(), timer: null, comboDurationTimer: null, positionCache: {}, keepPositions,
      revealBaseS: rememberPrefs.revealBaseS, revealStepS: rememberPrefs.revealStepS,
      errorMode: rememberPrefs.errorMode,
      trainingStart: rememberPrefs.trainingStart, trainingProgress: rememberPrefs.trainingProgress,
      paused: false,
    };
    applyRememberBg();
    requestWakeLock();
    startRememberLevel();
    // Kombi block: Remember has no natural end of its own (unlike VT's
    // fixed-length schedule), so a Kombi block gives it a duration and just
    // cuts over to the next block when time is up, same as every other
    // domain's Kombi blocks.
    if (opts && opts.comboDurationS) {
      rememberState.comboDurationFiresAt = performance.now() + opts.comboDurationS * 1000;
      rememberState.comboDurationTimer = setTimeout(finishRememberCombo, opts.comboDurationS * 1000);
    }
  }
  function finishRememberCombo() {
    if (!rememberState) return;
    if (rememberState.timer) clearTimeout(rememberState.timer);
    const playedS = (performance.now() - rememberState.startTime) / 1000;
    rememberState = null;
    els.rememberPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.rememberPlayer) document.exitFullscreen().catch(() => {});
    els.rememberFsHint.hidden = true;
    if (comboProgram) advanceComboProgram(playedS);
  }

  // ---- Remember: pause mid-game to adjust the background, same
  // mechanism as Periph's pause (freeze, let the overlay's controls edit
  // state directly, shift timestamps forward by the paused duration on
  // resume) but adapted for Remember's setTimeout-driven reveal/cover
  // cycle instead of a rAF schedule - the pending timer is cancelled and
  // its remaining delay is replayed via scheduleRememberTimer() on resume,
  // rather than shifting a startTime that a schedule is re-read against. ----
  function pauseRemember() {
    if (!rememberState || rememberState.paused) return;
    rememberState.paused = true;
    rememberState.pausedAt = performance.now();
    if (rememberState.timer) {
      clearTimeout(rememberState.timer);
      rememberState.timer = null;
      rememberState.timerRemainingMs = Math.max(0, rememberState.timerFiresAt - rememberState.pausedAt);
    }
    if (rememberState.comboDurationTimer) {
      clearTimeout(rememberState.comboDurationTimer);
      rememberState.comboDurationTimer = null;
      rememberState.comboRemainingMs = Math.max(0, rememberState.comboDurationFiresAt - rememberState.pausedAt);
    }
    syncRememberBgUI();
    els.rememberPauseBtn.hidden = true;
    els.rememberPauseOverlay.hidden = false;
  }
  function resumeRemember() {
    if (!rememberState || !rememberState.paused) return;
    rememberState.startTime += performance.now() - rememberState.pausedAt;
    rememberState.paused = false;
    if (rememberState.timerFn && rememberState.timerRemainingMs != null) {
      scheduleRememberTimer(rememberState.timerFn, rememberState.timerRemainingMs);
      rememberState.timerRemainingMs = null;
    }
    if (rememberState.comboRemainingMs != null) {
      rememberState.comboDurationFiresAt = performance.now() + rememberState.comboRemainingMs;
      rememberState.comboDurationTimer = setTimeout(finishRememberCombo, rememberState.comboRemainingMs);
      rememberState.comboRemainingMs = null;
    }
    els.rememberPauseOverlay.hidden = true;
    els.rememberPauseBtn.hidden = false;
  }
  els.rememberPauseBtn.addEventListener("click", pauseRemember);
  els.rememberResumeBtn.addEventListener("click", resumeRemember);
  els.rememberNavPrevBtn.addEventListener("click", () => rememberState && rememberGoToLevel(rememberState.level - 1));
  els.rememberNavRestartBtn.addEventListener("click", () => rememberState && rememberGoToLevel(rememberState.level));
  els.rememberNavNextBtn.addEventListener("click", () => rememberState && rememberGoToLevel(rememberState.level + 1));

  // ---- Ready screens: Feste/Bewegte Positionen share one, Trainingsmodus
  // has its own (extra Startzahl + Steigern controls). ----
  let rememberReadyMode = "fixed";
  function updateRememberReadyBestHint() {
    const best = rememberBestFor(rememberReadyMode);
    els.rememberReadyBestHint.textContent = best
      ? `Deine Bestleistung bei dieser Schwierigkeit: ${best}.`
      : "Noch keine Bestleistung bei dieser Schwierigkeit – leg los!";
  }
  function syncRememberErrorUI() {
    document.querySelectorAll("#rememberErrorRow [data-remember-error]").forEach((el) => {
      setActive(el, el.dataset.rememberError === rememberPrefs.errorMode);
    });
  }
  function openRememberReady(mode) {
    rememberReadyMode = mode;
    const m = REMEMBER_MODES[mode];
    els.rememberReadyTitle.textContent = m.title;
    els.rememberReadyDesc.textContent = mode === "fixed"
      ? "Jede neue Zahl kommt an einen neuen Platz dazu – die bisherigen bleiben, wo sie waren."
      : "Bei jeder neuen Zahl werden alle Positionen neu gemischt – schwerer zu merken.";
    syncRememberDifficultyUI(rememberReadyCfg);
    syncRememberErrorUI();
    syncRememberBgUI();
    updateRememberReadyBestHint();
    showScreen("rememberReady");
  }
  document.querySelectorAll("#rememberErrorRow [data-remember-error]").forEach((el) => {
    el.addEventListener("click", () => {
      rememberPrefs.errorMode = el.dataset.rememberError;
      saveRememberPrefsToStorage();
      syncRememberErrorUI();
    });
  });
  const rememberReadyCfg = {
    rowSelector: "#rememberDifficultyRow",
    custom: els.rememberDiffCustom,
    revealSlider: els.rememberRevealSlider, revealValue: els.rememberRevealValue,
    stepSlider: els.rememberStepSlider, stepValue: els.rememberStepValue,
    // Just re-sync the values in place - no showScreen() here, or every
    // slider drag on the already-open Feineinstellungen would jump the
    // page back to the top.
    sync: () => { syncRememberDifficultyUI(rememberReadyCfg); updateRememberReadyBestHint(); },
  };
  wireRememberDifficultyUI(rememberReadyCfg);
  els.rememberOpenFixed.addEventListener("click", () => openRememberReady("fixed"));
  els.rememberOpenShuffle.addEventListener("click", () => openRememberReady("shuffle"));
  els.rememberReadyBackToHome.addEventListener("click", () => showScreen("natHome"));

  // ---- Periphere Wahrnehmung: reuses the shared VT ready/player screens
  // (same flashing-stimulus mechanic, just centred on a fixation point)
  // instead of a separate mini-screen set like Remember has. ----
  els.periphOpenBtn.addEventListener("click", () => {
    readyReturnScreen = "natHome";
    openReady("periph-flash", '<div class="icon-badge"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" fill="none" stroke="#fff" stroke-width="1.5" stroke-dasharray="2 3"/><circle cx="12" cy="12" r="2.2" fill="#fff"/></svg></div>');
  });
  els.rememberReadyStartBtn.addEventListener("click", () => startRememberGame(rememberReadyMode));

  function syncRememberTrainingUI() {
    els.rememberStartSlider.value = rememberPrefs.trainingStart;
    els.rememberStartValue.textContent = String(rememberPrefs.trainingStart);
    document.querySelectorAll("[data-remember-position]").forEach((el) => {
      setActive(el, el.dataset.rememberPosition === rememberPrefs.trainingPositionMode);
    });
    document.querySelectorAll("[data-remember-progress]").forEach((el) => {
      setActive(el, (el.dataset.rememberProgress === "1") === rememberPrefs.trainingProgress);
    });
    syncRememberDifficultyUI(rememberTrainingCfg);
    syncRememberBgUI();
    const best = rememberBestFor("training");
    els.rememberTrainingBestHint.textContent = best
      ? `Deine bisher höchste geschaffte Zahlenfolge im Trainingsmodus: ${best}.`
      : "Noch keine Bestleistung im Trainingsmodus – leg los!";
  }
  const rememberTrainingCfg = {
    rowSelector: "#rememberTrainingDifficultyRow",
    custom: els.rememberTrainingDiffCustom,
    revealSlider: els.rememberTrainingRevealSlider, revealValue: els.rememberTrainingRevealValue,
    stepSlider: els.rememberTrainingStepSlider, stepValue: els.rememberTrainingStepValue,
    sync: syncRememberTrainingUI,
  };
  wireRememberDifficultyUI(rememberTrainingCfg);
  els.rememberStartSlider.addEventListener("input", () => {
    rememberPrefs.trainingStart = Number(els.rememberStartSlider.value);
    saveRememberPrefsToStorage();
    syncRememberTrainingUI();
  });
  document.querySelectorAll("[data-remember-progress]").forEach((el) => {
    el.addEventListener("click", () => {
      rememberPrefs.trainingProgress = el.dataset.rememberProgress === "1";
      saveRememberPrefsToStorage();
      syncRememberTrainingUI();
    });
  });
  document.querySelectorAll("[data-remember-position]").forEach((el) => {
    el.addEventListener("click", () => {
      rememberPrefs.trainingPositionMode = el.dataset.rememberPosition;
      saveRememberPrefsToStorage();
      syncRememberTrainingUI();
    });
  });
  els.rememberOpenTraining.addEventListener("click", () => { syncRememberTrainingUI(); showScreen("rememberTrainingReady"); });
  els.rememberTrainingBackToHome.addEventListener("click", () => showScreen("natHome"));
  els.rememberTrainingStartBtn.addEventListener("click", () => startRememberGame("training"));

  // "Beenden" doubles as the finish action here (see comment above) - only
  // shows a summary once at least one round has actually been cleared;
  // quitting with no progress at all just returns to the settings screen
  // it was started from, like "Beenden" elsewhere in the app.
  function rememberStop() {
    if (!rememberState) return;
    if (rememberState.timer) clearTimeout(rememberState.timer);
    if (rememberState.comboDurationTimer) clearTimeout(rememberState.comboDurationTimer);
    const state = rememberState;
    rememberState = null;
    els.rememberPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.rememberPlayer) document.exitFullscreen().catch(() => {});
    els.rememberFsHint.hidden = true;
    // "Beenden" mid-Kombi quits the whole Kombi programme, not just this
    // block - matches every other domain's "Beenden" behaviour.
    if (comboProgram) { abortComboProgram(); return; }
    if (state.cleared > 0) {
      const isRecord = saveRememberBest(state.mode, state.cleared);
      renderRememberBests();
      const played = (performance.now() - state.startTime) / 1000;
      const modeTitle = REMEMBER_MODES[state.mode].title;
      els.rememberPlayerBar.hidden = true;
      els.rememberDoneSummary.textContent = `${modeTitle} · Zahl ${state.cleared} erreicht` + (isRecord ? " · Neue Bestleistung!" : "");
      const id = addHistory({ kind: "remember", title: `Remember · ${modeTitle}`, seconds: Math.round(played), note: `Zahl ${state.cleared} erreicht` });
      renderRating(els.rememberRating, id, "Wie war deine Konzentration?");
      els.rememberDonePanel.hidden = false;
    } else {
      els.rememberPlayer.hidden = true;
      showScreen(rememberReturnScreen);
    }
  }
  els.rememberBackBtn.addEventListener("click", rememberStop);
  els.rememberAgainBtn.addEventListener("click", () => { els.rememberDonePanel.hidden = true; startRememberGame(lastRememberMode); });
  els.rememberDoneBackBtn.addEventListener("click", () => { els.rememberPlayer.hidden = true; els.rememberDonePanel.hidden = true; showScreen("natHome"); });

  // ==== Blitz-Raster engine ====
  // A grid of cells lights up SIMULTANEOUSLY for a brief moment, then goes
  // dark; the client taps back exactly the cells that lit up - order
  // doesn't matter. That's the key difference from Remember (a sequential,
  // ordered recall of a layout you have time to study): this is a single
  // brief snapshot and an unordered "which ones" recall. Endless/
  // progressive like Remember - "Beenden" doubles as the finish action.
  const BLITZ_PREFS_KEY = "fwmc-blitz-prefs-v1";
  const BLITZ_DIFFICULTIES = {
    leicht: { title: "Leicht", flashS: 1.2 },
    mittel: { title: "Mittel", flashS: 0.8 },
    schwer: { title: "Schwer", flashS: 0.5 },
  };
  const BLITZ_MAX_LEVEL_CAP = 16; // absolute ceiling, regardless of how many cells a grid/Bereich combo could fit
  const blitzPrefs = {
    flashS: BLITZ_DIFFICULTIES.mittel.flashS,
    errorMode: "reset2",
    gridSize: 4,
    zones: PERIPH_ZONE_KEYS.slice(),
    startCount: 3,
    bgColorKey: "gruen",
    bgIntensity: 0,
  };
  function loadBlitzPrefs() {
    const saved = readJSON(BLITZ_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(blitzPrefs, saved);
    if (![3, 4, 5, 6, 7, 8].includes(blitzPrefs.gridSize)) blitzPrefs.gridSize = 4;
    if (!Array.isArray(blitzPrefs.zones) || blitzPrefs.zones.length === 0 || !blitzPrefs.zones.every((z) => PERIPH_ZONE_KEYS.includes(z))) blitzPrefs.zones = PERIPH_ZONE_KEYS.slice();
    if (!["reset2", "backOne", "stay"].includes(blitzPrefs.errorMode)) blitzPrefs.errorMode = "reset2";
    if (typeof blitzPrefs.flashS !== "number" || blitzPrefs.flashS < 0.3 || blitzPrefs.flashS > 2) blitzPrefs.flashS = BLITZ_DIFFICULTIES.mittel.flashS;
    if (typeof blitzPrefs.startCount !== "number" || blitzPrefs.startCount < 2) blitzPrefs.startCount = 3;
    if (!STROOP_COLOR_BY_KEY[blitzPrefs.bgColorKey]) blitzPrefs.bgColorKey = "gruen";
    if (typeof blitzPrefs.bgIntensity !== "number" || blitzPrefs.bgIntensity < 0 || blitzPrefs.bgIntensity > 1) blitzPrefs.bgIntensity = 0;
  }
  function saveBlitzPrefsToStorage() { writeJSON(BLITZ_PREFS_KEY, blitzPrefs); }
  loadBlitzPrefs();

  function blitzDifficultyBucket() {
    for (const key of Object.keys(BLITZ_DIFFICULTIES)) {
      if (Math.abs(BLITZ_DIFFICULTIES[key].flashS - blitzPrefs.flashS) < 0.001) return key;
    }
    return "custom";
  }
  const BLITZ_BEST_KEY = "fwmc-blitz-best-v1"; // { [difficultyBucket]: bestLevel }
  function blitzBestFor() { return readJSON(BLITZ_BEST_KEY, {})[blitzDifficultyBucket()] || 0; }
  function blitzOverallBest() { return Math.max(0, ...Object.values(readJSON(BLITZ_BEST_KEY, {})), 0); }
  function saveBlitzBest(level) {
    const all = readJSON(BLITZ_BEST_KEY, {});
    const bucket = blitzDifficultyBucket();
    if (level > (all[bucket] || 0)) { all[bucket] = level; writeJSON(BLITZ_BEST_KEY, all); return true; }
    return false;
  }
  function renderBlitzBest() {
    const b = blitzOverallBest();
    els.blitzBestHint.textContent = b ? `Bestleistung: ${b}` : "";
  }
  renderBlitzBest();

  // Maps the 3x3 "Bereich" band system Periphere Wahrnehmung already uses
  // (PERIPH_ZONES) onto an NxN grid, splitting rows/cols into three bands.
  // The centre band is always eligible, same convention as Periph (there
  // it's reserved for the fixation point; here there's no such reason, but
  // keeping it "always on" avoids a confusing extra toggle for one band).
  function blitzEligibleCells(gridSize, zones) {
    const cells = [];
    for (let r = 0; r < gridSize; r++) {
      for (let c = 0; c < gridSize; c++) {
        const br = Math.floor((r * 3) / gridSize), bc = Math.floor((c * 3) / gridSize);
        const isCenter = br === 1 && bc === 1;
        const inZone = isCenter || zones.some((z) => PERIPH_ZONES[z].row === br && PERIPH_ZONES[z].col === bc);
        if (inZone) cells.push(r + "," + c);
      }
    }
    return cells;
  }
  function blitzMaxLevelForCurrentSettings() {
    const eligible = blitzEligibleCells(blitzPrefs.gridSize, blitzPrefs.zones);
    return Math.max(2, Math.min(BLITZ_MAX_LEVEL_CAP, eligible.length - 1));
  }

  function applyBlitzBg() {
    els.blitzStage.style.background = blitzPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[blitzPrefs.bgColorKey].hex, blitzPrefs.bgIntensity)
      : "";
  }
  const syncBlitzBgUI = wireBgIntensityControl(blitzPrefs, {
    pickers: [els.blitzBgColorPicker, els.blitzPauseBgColorPicker],
    sliders: [els.blitzBgIntensitySlider, els.blitzPauseBgSlider],
    valueEls: [els.blitzBgIntensityValue, els.blitzPauseBgValue],
    hintEls: [els.blitzBgContrastHint],
    transfer: [{
      sourceRow: els.blitzBgSourceRow, presetGroup: els.blitzBgPresetGroup, presetList: els.blitzBgPresetList,
      saveBtn: els.blitzBgSaveBtn, form: els.blitzBgSaveForm, nameInput: els.blitzBgSaveNameInput,
      cancelBtn: els.blitzBgSaveCancelBtn, confirmBtn: els.blitzBgSaveConfirmBtn,
    }],
  }, () => { saveBlitzPrefsToStorage(); applyBlitzBg(); }, "blitz");

  // ---- Ready screen ----
  function syncBlitzGridSizeUI() {
    document.querySelectorAll("#blitzGridSizeRow [data-blitz-grid]").forEach((el) => setActive(el, Number(el.dataset.blitzGrid) === blitzPrefs.gridSize));
    els.blitzZoneGroup.hidden = blitzPrefs.gridSize === 3;
  }
  document.querySelectorAll("#blitzGridSizeRow [data-blitz-grid]").forEach((el) => {
    el.addEventListener("click", () => {
      blitzPrefs.gridSize = Number(el.dataset.blitzGrid);
      saveBlitzPrefsToStorage();
      syncBlitzGridSizeUI();
      syncBlitzStartUI();
    });
  });
  document.querySelectorAll("#blitzZoneGrid [data-zone]").forEach((el) => {
    el.addEventListener("click", () => {
      const z = el.dataset.zone;
      const on = blitzPrefs.zones.includes(z);
      // Keep at least one zone selected, same rule as Periph's own zone grid.
      if (on && blitzPrefs.zones.length <= 1) return;
      blitzPrefs.zones = on ? blitzPrefs.zones.filter((k) => k !== z) : [...blitzPrefs.zones, z];
      saveBlitzPrefsToStorage();
      syncBlitzZoneUI();
      syncBlitzStartUI();
    });
  });
  els.blitzZoneAllBtn.addEventListener("click", () => {
    const allOn = blitzPrefs.zones.length === PERIPH_ZONE_KEYS.length;
    blitzPrefs.zones = allOn ? [] : PERIPH_ZONE_KEYS.slice();
    saveBlitzPrefsToStorage();
    syncBlitzZoneUI();
    syncBlitzStartUI();
  });
  function syncBlitzZoneUI() {
    document.querySelectorAll("#blitzZoneGrid [data-zone]").forEach((el) => el.classList.toggle("active", blitzPrefs.zones.includes(el.dataset.zone)));
    setActive(els.blitzZoneAllBtn, blitzPrefs.zones.length === PERIPH_ZONE_KEYS.length);
    const belowMin = blitzPrefs.zones.length === 0;
    els.blitzZoneHint.textContent = belowMin ? "Wähle mindestens einen Bereich." : "";
    els.blitzZoneHint.classList.toggle("warn", belowMin);
    els.blitzReadyStartBtn.disabled = belowMin;
  }
  document.querySelectorAll("#blitzDifficultyRow [data-blitz-diff]").forEach((el) => {
    el.addEventListener("click", () => {
      blitzPrefs.flashS = BLITZ_DIFFICULTIES[el.dataset.blitzDiff].flashS;
      saveBlitzPrefsToStorage();
      syncBlitzDifficultyUI();
    });
  });
  els.blitzFlashSlider.addEventListener("input", () => {
    blitzPrefs.flashS = Number(els.blitzFlashSlider.value);
    saveBlitzPrefsToStorage();
    syncBlitzDifficultyUI();
  });
  function syncBlitzDifficultyUI() {
    const bucket = blitzDifficultyBucket();
    document.querySelectorAll("#blitzDifficultyRow [data-blitz-diff]").forEach((el) => setActive(el, el.dataset.blitzDiff === bucket));
    els.blitzDiffCustom.hidden = bucket !== "custom";
    els.blitzFlashSlider.value = blitzPrefs.flashS;
    els.blitzFlashValue.textContent = fmtSeconds(blitzPrefs.flashS);
    updateBlitzReadyBestHint();
  }
  document.querySelectorAll("#blitzErrorRow [data-blitz-error]").forEach((el) => {
    el.addEventListener("click", () => {
      blitzPrefs.errorMode = el.dataset.blitzError;
      saveBlitzPrefsToStorage();
      syncBlitzErrorUI();
    });
  });
  function syncBlitzErrorUI() {
    document.querySelectorAll("#blitzErrorRow [data-blitz-error]").forEach((el) => setActive(el, el.dataset.blitzError === blitzPrefs.errorMode));
  }
  function syncBlitzStartUI() {
    const max = blitzMaxLevelForCurrentSettings();
    blitzPrefs.startCount = Math.min(blitzPrefs.startCount, max);
    els.blitzStartSlider.max = String(max);
    els.blitzStartSlider.value = blitzPrefs.startCount;
    els.blitzStartValue.textContent = String(blitzPrefs.startCount);
  }
  els.blitzStartSlider.addEventListener("input", () => {
    blitzPrefs.startCount = Number(els.blitzStartSlider.value);
    saveBlitzPrefsToStorage();
    syncBlitzStartUI();
  });
  function updateBlitzReadyBestHint() {
    const best = blitzBestFor();
    els.blitzReadyBestHint.textContent = best
      ? `Deine Bestleistung bei dieser Schwierigkeit: ${best}.`
      : "Noch keine Bestleistung bei dieser Schwierigkeit – leg los!";
  }
  els.blitzOpenBtn.addEventListener("click", () => {
    syncBlitzGridSizeUI();
    syncBlitzZoneUI();
    syncBlitzDifficultyUI();
    syncBlitzErrorUI();
    syncBlitzStartUI();
    syncBlitzBgUI();
    showScreen("blitzReady");
  });
  els.blitzReadyBackToHome.addEventListener("click", () => showScreen("natHome"));

  // ---- Grid rendering + gameplay ----
  function pickRandomSubset(pool, count) {
    const copy = pool.slice();
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return new Set(copy.slice(0, count));
  }
  // Same timer-wrapping trick as Remember's scheduleRememberTimer: records
  // what's pending and when it fires, so Pause can cancel it and Resume can
  // replay it with its exact remaining delay.
  function scheduleBlitzTimer(fn, delayMs) {
    blitzState.timerFn = fn;
    blitzState.timerFiresAt = performance.now() + delayMs;
    blitzState.timer = setTimeout(fn, delayMs);
  }
  function renderBlitzGrid() {
    els.blitzGrid.style.gridTemplateColumns = `repeat(${blitzState.gridSize}, 1fr)`;
    els.blitzGrid.style.gridTemplateRows = `repeat(${blitzState.gridSize}, 1fr)`;
    // A fixed 10px gap (the CSS default) eats too much of each cell once
    // there are 6+ of them per row on a phone-width screen - narrow it down
    // for the larger grids so cells stay a reasonable tap target. Still
    // roomy on a bigger screen (iPad), which is the main use case for 6-8.
    els.blitzGrid.style.gap = blitzState.gridSize <= 5 ? "10px" : blitzState.gridSize === 6 ? "8px" : blitzState.gridSize === 7 ? "6px" : "5px";
    els.blitzGrid.innerHTML = "";
    for (let r = 0; r < blitzState.gridSize; r++) {
      for (let c = 0; c < blitzState.gridSize; c++) {
        const key = r + "," + c;
        const eligible = blitzState.eligible.has(key);
        const el = document.createElement("button");
        el.className = "blitz-cell";
        el.setAttribute("aria-label", `Feld Zeile ${r + 1}, Spalte ${c + 1}`);
        if (blitzState.phase === "flash" && blitzState.lit.has(key)) el.classList.add("lit");
        if (blitzState.tapped.has(key) && blitzState.lit.has(key)) el.classList.add("correct");
        if (key === blitzState.wrongKey) el.classList.add("wrong");
        const tappable = eligible && blitzState.phase === "input" && !blitzState.tapped.has(key);
        if (tappable) {
          el.classList.add("tappable");
          el.addEventListener("click", () => blitzTapCell(key, el));
        }
        els.blitzGrid.appendChild(el);
      }
    }
  }
  function blitzStartRound() {
    const eligibleArr = blitzEligibleCells(blitzState.gridSize, blitzState.zones);
    blitzState.eligible = new Set(eligibleArr);
    const maxLevel = Math.max(2, eligibleArr.length - 1);
    blitzState.level = Math.min(blitzState.level, maxLevel);
    blitzState.lit = pickRandomSubset(eligibleArr, blitzState.level);
    blitzState.tapped = new Set();
    blitzState.wrongKey = null;
    blitzState.phase = "flash";
    els.blitzHint.textContent = "Merken …";
    els.blitzLevelEl.textContent = `${blitzState.level} Felder`;
    renderBlitzGrid();
    scheduleBlitzTimer(blitzCoverRound, blitzState.flashS * 1000);
  }
  function blitzCoverRound() {
    if (!blitzState) return;
    blitzState.phase = "input";
    els.blitzHint.textContent = "Jetzt genau diese Felder antippen";
    renderBlitzGrid();
  }
  function blitzTapCell(key, el) {
    if (!blitzState || blitzState.phase !== "input" || blitzState.paused || blitzState.tapped.has(key)) return;
    if (blitzState.lit.has(key)) {
      blitzState.tapped.add(key);
      el.classList.remove("tappable");
      el.classList.add("correct");
      if ([...blitzState.lit].every((k) => blitzState.tapped.has(k))) {
        if (blitzState.level > blitzState.cleared) blitzState.cleared = blitzState.level;
        blitzState.phase = "success";
        els.blitzHint.textContent = "Richtig! Weiter geht's …";
        blitzState.level = Math.min(blitzMaxLevelForCurrentSettings(), blitzState.level + 1);
        scheduleBlitzTimer(blitzStartRound, 900);
      }
    } else {
      blitzState.phase = "checking";
      blitzState.wrongKey = key;
      blitzState.tapped = new Set(blitzState.lit); // reveal every cell that was actually lit
      renderBlitzGrid();
      let resetLevel, hint;
      if (blitzState.errorMode === "stay") { resetLevel = blitzState.level; hint = "Leider falsch – nochmal versuchen"; }
      else if (blitzState.errorMode === "backOne") { resetLevel = Math.max(2, blitzState.level - 1); hint = "Leider falsch – ein Feld weniger"; }
      else { resetLevel = 2; hint = "Leider falsch – nochmal von vorne"; }
      els.blitzHint.textContent = hint;
      scheduleBlitzTimer(() => { blitzState.level = resetLevel; blitzStartRound(); }, 1400);
    }
  }
  let blitzState = null;
  function startBlitzGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.blitzPlayer.hidden = false;
    els.blitzPlayerBar.hidden = false;
    els.blitzDonePanel.hidden = true;
    els.blitzPauseOverlay.hidden = true;
    els.blitzPauseBtn.hidden = false;
    blitzState = {
      level: blitzPrefs.startCount, cleared: 0, phase: "reveal", lit: new Set(), tapped: new Set(), eligible: new Set(),
      startTime: performance.now(), timer: null, gridSize: blitzPrefs.gridSize, zones: blitzPrefs.zones.slice(),
      flashS: blitzPrefs.flashS, errorMode: blitzPrefs.errorMode, paused: false,
    };
    applyBlitzBg();
    requestWakeLock();
    blitzStartRound();
  }
  els.blitzReadyStartBtn.addEventListener("click", startBlitzGame);

  // ---- Pause mid-game, live-adjust the background - same trick as
  // Remember's pause (cancel the pending timer, replay it with its exact
  // remaining delay on resume) since Blitz-Raster is also setTimeout-driven. ----
  function pauseBlitz() {
    if (!blitzState || blitzState.paused) return;
    blitzState.paused = true;
    blitzState.pausedAt = performance.now();
    if (blitzState.timer) {
      clearTimeout(blitzState.timer);
      blitzState.timer = null;
      blitzState.timerRemainingMs = Math.max(0, blitzState.timerFiresAt - blitzState.pausedAt);
    }
    syncBlitzBgUI();
    els.blitzPauseBtn.hidden = true;
    els.blitzPauseOverlay.hidden = false;
  }
  function resumeBlitz() {
    if (!blitzState || !blitzState.paused) return;
    blitzState.startTime += performance.now() - blitzState.pausedAt;
    blitzState.paused = false;
    if (blitzState.timerFn && blitzState.timerRemainingMs != null) {
      scheduleBlitzTimer(blitzState.timerFn, blitzState.timerRemainingMs);
      blitzState.timerRemainingMs = null;
    }
    els.blitzPauseOverlay.hidden = true;
    els.blitzPauseBtn.hidden = false;
  }
  els.blitzPauseBtn.addEventListener("click", pauseBlitz);
  els.blitzResumeBtn.addEventListener("click", resumeBlitz);

  // "Beenden" doubles as the finish action, same convention as Remember -
  // Blitz-Raster is endless/progressive with no fixed end of its own.
  function blitzStop() {
    if (!blitzState) return;
    if (blitzState.timer) clearTimeout(blitzState.timer);
    const state = blitzState;
    blitzState = null;
    els.blitzPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.blitzPlayer) document.exitFullscreen().catch(() => {});
    els.blitzFsHint.hidden = true;
    if (state.cleared > 0) {
      const isRecord = saveBlitzBest(state.cleared);
      renderBlitzBest();
      const played = (performance.now() - state.startTime) / 1000;
      els.blitzPlayerBar.hidden = true;
      els.blitzDoneSummary.textContent = `Blitz-Raster · Stufe ${state.cleared} erreicht` + (isRecord ? " · Neue Bestleistung!" : "");
      const id = addHistory({ kind: "blitz", title: "Blitz-Raster", seconds: Math.round(played), note: `Stufe ${state.cleared} erreicht` });
      renderRating(els.blitzRating, id, "Wie war deine Konzentration?");
      els.blitzDonePanel.hidden = false;
    } else {
      els.blitzPlayer.hidden = true;
      showScreen("natHome");
    }
  }
  els.blitzBackBtn.addEventListener("click", blitzStop);
  els.blitzAgainBtn.addEventListener("click", () => { els.blitzDonePanel.hidden = true; startBlitzGame(); });
  els.blitzDoneBackBtn.addEventListener("click", () => { els.blitzPlayer.hidden = true; els.blitzDonePanel.hidden = true; showScreen("natHome"); });

  // ==== Flash Speicher Test engine ====
  // A THIRD distinct NAT memory mechanic (the user was explicit this isn't
  // "Remember but faster" nor "Blitz-Raster"): numbers appear ONE AT A TIME
  // at scattered positions - reusing Periph's own axis/zone "Bereich" maths
  // directly (randFlashPos() mirrors randPeriphPos()) rather than a new
  // positioning system - each briefly, then an input box opens to type the
  // whole sequence back IN ORDER (unlike Blitz-Raster, where order doesn't
  // matter). Four modes share one `flashPrefs` object (mirroring how
  // Remember's fixed/shuffle/training share `rememberPrefs`):
  // - "constant": count never changes, only gets faster on success.
  // - "climb": count grows by one every successful round.
  // - "climbRepeat": like climb, but repeats each count `repsPerLevel`
  //   times before advancing.
  // - "training": Remember-style direct start at a chosen count/speed.
  const FLASH_PREFS_KEY = "fwmc-flash-prefs-v1";
  const FLASH_DIFFICULTIES = {
    leicht: { title: "Leicht", stimulusS: 1.2, intervalS: 0.6 },
    mittel: { title: "Mittel", stimulusS: 0.8, intervalS: 0.4 },
    schwer: { title: "Schwer", stimulusS: 0.5, intervalS: 0.25 },
  };
  const FLASH_SPEED_STEPS = 20; // ceiling for "constant" mode's speed-up steps
  const flashPrefs = {
    kind: "zahlen",
    stimulusS: FLASH_DIFFICULTIES.mittel.stimulusS,
    intervalS: FLASH_DIFFICULTIES.mittel.intervalS,
    errorMode: "reset2",
    axes: PERIPH_AXIS_KEYS.slice(),
    useZones: false,
    zones: PERIPH_ZONE_KEYS.slice(),
    constantCount: 3,
    startCount: 3,
    repsPerLevel: 2,
    trainingStart: 5,
    trainingProgress: true,
    bgColorKey: "gruen",
    bgIntensity: 0,
    fixEnabled: true,
    fixChar: "",
    fixColor: "grau",
    fixSize: 1,
  };
  function loadFlashPrefs() {
    const saved = readJSON(FLASH_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(flashPrefs, saved);
    if (!["buchstaben", "zahlen", "gemischt"].includes(flashPrefs.kind)) flashPrefs.kind = "zahlen";
    if (!Array.isArray(flashPrefs.axes) || flashPrefs.axes.length === 0 || !flashPrefs.axes.every((a) => PERIPH_AXIS_KEYS.includes(a))) flashPrefs.axes = PERIPH_AXIS_KEYS.slice();
    if (!Array.isArray(flashPrefs.zones) || flashPrefs.zones.length === 0 || !flashPrefs.zones.every((z) => PERIPH_ZONE_KEYS.includes(z))) flashPrefs.zones = PERIPH_ZONE_KEYS.slice();
    if (!["reset2", "backOne", "stay"].includes(flashPrefs.errorMode)) flashPrefs.errorMode = "reset2";
    if (typeof flashPrefs.stimulusS !== "number" || flashPrefs.stimulusS < 0.3 || flashPrefs.stimulusS > 2) flashPrefs.stimulusS = FLASH_DIFFICULTIES.mittel.stimulusS;
    if (typeof flashPrefs.intervalS !== "number" || flashPrefs.intervalS < 0.2 || flashPrefs.intervalS > 2) flashPrefs.intervalS = FLASH_DIFFICULTIES.mittel.intervalS;
    if (typeof flashPrefs.constantCount !== "number" || flashPrefs.constantCount < 2) flashPrefs.constantCount = 3;
    if (typeof flashPrefs.startCount !== "number" || flashPrefs.startCount < 2) flashPrefs.startCount = 3;
    if (![2, 3].includes(flashPrefs.repsPerLevel)) flashPrefs.repsPerLevel = 2;
    if (typeof flashPrefs.trainingStart !== "number" || flashPrefs.trainingStart < 2) flashPrefs.trainingStart = 5;
    if (typeof flashPrefs.trainingProgress !== "boolean") flashPrefs.trainingProgress = true;
    if (!STROOP_COLOR_BY_KEY[flashPrefs.bgColorKey]) flashPrefs.bgColorKey = "gruen";
    if (typeof flashPrefs.bgIntensity !== "number" || flashPrefs.bgIntensity < 0 || flashPrefs.bgIntensity > 1) flashPrefs.bgIntensity = 0;
    if (typeof flashPrefs.fixEnabled !== "boolean") flashPrefs.fixEnabled = true;
    if (typeof flashPrefs.fixChar !== "string") flashPrefs.fixChar = "";
    if (!FIX_COLOR_BY_KEY[flashPrefs.fixColor]) flashPrefs.fixColor = "grau";
    if (typeof flashPrefs.fixSize !== "number" || flashPrefs.fixSize < 0.6 || flashPrefs.fixSize > 2) flashPrefs.fixSize = 1;
  }
  function saveFlashPrefsToStorage() { writeJSON(FLASH_PREFS_KEY, flashPrefs); }
  loadFlashPrefs();
  // "Zahlen"/"Buchstaben"/"Zeichen" (gemischt, since a shown sequence can
  // contain both) - used everywhere a count needs a unit word.
  function flashUnitLabel(kind) {
    return kind === "buchstaben" ? "Buchstaben" : kind === "gemischt" ? "Zeichen" : "Zahlen";
  }

  const FLASH_BEST_KEY = "fwmc-flash-best-v1"; // { constant: bestSpeedStep, climb: N, climbRepeat: N, training: N }
  function flashBestFor(mode) { return readJSON(FLASH_BEST_KEY, {})[mode] || 0; }
  function saveFlashBest(mode, value) {
    const all = readJSON(FLASH_BEST_KEY, {});
    if (value > (all[mode] || 0)) { all[mode] = value; writeJSON(FLASH_BEST_KEY, all); return true; }
    return false;
  }
  function renderFlashBests() {
    const c = flashBestFor("constant"), cl = flashBestFor("climb"), cr = flashBestFor("climbRepeat"), t = flashBestFor("training");
    const unit = flashUnitLabel(flashPrefs.kind);
    els.flashBestConstant.textContent = c ? `Bestleistung: Tempo-Stufe ${c + 1}` : "";
    els.flashBestClimb.textContent = cl ? `Bestleistung: ${cl} ${unit}` : "";
    els.flashBestClimbRepeat.textContent = cr ? `Bestleistung: ${cr} ${unit}` : "";
    els.flashBestTraining.textContent = t ? `Bestleistung: ${t} ${unit}` : "";
  }
  renderFlashBests();

  function applyFlashBg() {
    els.flashStage.style.background = flashPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[flashPrefs.bgColorKey].hex, flashPrefs.bgIntensity)
      : "";
  }
  const syncFlashBgUI = wireBgIntensityControl(flashPrefs, {
    pickers: [els.flashBgColorPicker, els.flashTrainingBgColorPicker, els.flashPauseBgColorPicker],
    sliders: [els.flashBgIntensitySlider, els.flashTrainingBgIntensitySlider, els.flashPauseBgSlider],
    valueEls: [els.flashBgIntensityValue, els.flashTrainingBgIntensityValue, els.flashPauseBgValue],
    hintEls: [els.flashBgContrastHint, els.flashTrainingBgContrastHint],
    transfer: [
      {
        sourceRow: els.flashBgSourceRow, presetGroup: els.flashBgPresetGroup, presetList: els.flashBgPresetList,
        saveBtn: els.flashBgSaveBtn, form: els.flashBgSaveForm, nameInput: els.flashBgSaveNameInput,
        cancelBtn: els.flashBgSaveCancelBtn, confirmBtn: els.flashBgSaveConfirmBtn,
      },
      {
        sourceRow: els.flashTrainingBgSourceRow, presetGroup: els.flashTrainingBgPresetGroup, presetList: els.flashTrainingBgPresetList,
        saveBtn: els.flashTrainingBgSaveBtn, form: els.flashTrainingBgSaveForm, nameInput: els.flashTrainingBgSaveNameInput,
        cancelBtn: els.flashTrainingBgSaveCancelBtn, confirmBtn: els.flashTrainingBgSaveConfirmBtn,
      },
    ],
  }, () => { saveFlashPrefsToStorage(); applyFlashBg(); }, "flash");

  // ---- Fixpunkt in der Mitte - same customisation (Zeichen/Farbe/Größe)
  // as Periphere Wahrnehmung's, reusing FIX_COLOR_LIB, but with its own
  // on/off toggle: unlike Periph's canvas dot (always drawn), Flash
  // Speicher Test's is a DOM element the client can switch off entirely,
  // and it stays visible for the whole run (not tied to flash/gap/input
  // phase) as a constant reference point. Shared flashPrefs.fix* fields,
  // both ready screens carry a synced instance (same pattern as Bereich/
  // Hintergrund above).
  document.querySelectorAll("#flashFixToggleRow [data-flash-fix], #flashTrainingFixToggleRow [data-flash-fix]").forEach((el) => {
    el.addEventListener("click", () => {
      flashPrefs.fixEnabled = el.dataset.flashFix === "1";
      saveFlashPrefsToStorage();
      syncFlashFixUI();
    });
  });
  buildSingleSelectPicker(els.flashFixColorPicker, FIX_COLOR_LIB, (key) => {
    flashPrefs.fixColor = key;
    saveFlashPrefsToStorage();
    syncFlashFixUI();
  });
  buildSingleSelectPicker(els.flashTrainingFixColorPicker, FIX_COLOR_LIB, (key) => {
    flashPrefs.fixColor = key;
    saveFlashPrefsToStorage();
    syncFlashFixUI();
  });
  function flashFixCharInputHandler(input) {
    flashPrefs.fixChar = input.value.slice(0, 3);
    saveFlashPrefsToStorage();
    if (flashState) renderFlashFixpoint();
  }
  els.flashFixCharInput.addEventListener("input", () => flashFixCharInputHandler(els.flashFixCharInput));
  els.flashTrainingFixCharInput.addEventListener("input", () => flashFixCharInputHandler(els.flashTrainingFixCharInput));
  function flashFixSizeSliderInput(slider) {
    flashPrefs.fixSize = Number(slider.value);
    saveFlashPrefsToStorage();
    syncFlashFixUI();
  }
  els.flashFixSizeSlider.addEventListener("input", () => flashFixSizeSliderInput(els.flashFixSizeSlider));
  els.flashTrainingFixSizeSlider.addEventListener("input", () => flashFixSizeSliderInput(els.flashTrainingFixSizeSlider));
  function syncFlashFixUI() {
    [
      [els.flashFixToggleRow, els.flashFixOptions, els.flashFixColorPicker, els.flashFixCharInput, els.flashFixSizeSlider, els.flashFixSizeValue],
      [els.flashTrainingFixToggleRow, els.flashTrainingFixOptions, els.flashTrainingFixColorPicker, els.flashTrainingFixCharInput, els.flashTrainingFixSizeSlider, els.flashTrainingFixSizeValue],
    ].forEach(([toggleRow, options, picker, charInput, sizeSlider, sizeValue]) => {
      toggleRow.querySelectorAll("[data-flash-fix]").forEach((el) => setActive(el, (el.dataset.flashFix === "1") === flashPrefs.fixEnabled));
      options.hidden = !flashPrefs.fixEnabled;
      syncSingleSelectPicker(picker, flashPrefs.fixColor);
      charInput.value = flashPrefs.fixChar;
      sizeSlider.value = flashPrefs.fixSize;
      sizeValue.textContent = flashPrefs.fixSize.toFixed(1) + "×";
    });
    if (flashState) renderFlashFixpoint();
  }
  // Mirrors Periph's drawFixationPoint(): a custom character (sized text,
  // no background) if one is set, otherwise a plain coloured dot.
  function renderFlashFixpoint() {
    const el = els.flashFixpointEl;
    if (!flashPrefs.fixEnabled) { el.hidden = true; return; }
    el.hidden = false;
    const color = (FIX_COLOR_BY_KEY[flashPrefs.fixColor] || FIX_COLOR_BY_KEY.grau).hex;
    const char = flashPrefs.fixChar.trim();
    if (char) {
      el.textContent = char;
      el.style.fontSize = Math.round(28 * flashPrefs.fixSize) + "px";
      el.style.color = color;
      el.style.background = "transparent";
      el.style.width = "auto";
      el.style.height = "auto";
      el.style.borderRadius = "0";
    } else {
      el.textContent = "";
      const size = Math.round(12 * flashPrefs.fixSize);
      el.style.width = size + "px";
      el.style.height = size + "px";
      el.style.background = color;
      el.style.borderRadius = "50%";
    }
  }

  // ---- Zeichentyp - same three-way choice as Periphere Wahrnehmung's own
  // Zeichentyp, shared by both ready screens. "Gemischt" is per-character,
  // not per-run: randPeriphChar() itself rolls digit-or-letter independently
  // for each position, exactly like Periph.
  document.querySelectorAll("#flashKindRow [data-flash-kind], #flashTrainingKindRow [data-flash-kind]").forEach((el) => {
    el.addEventListener("click", () => {
      flashPrefs.kind = el.dataset.flashKind;
      saveFlashPrefsToStorage();
      syncFlashKindUI();
    });
  });
  function syncFlashKindUI() {
    document.querySelectorAll("#flashKindRow [data-flash-kind], #flashTrainingKindRow [data-flash-kind]").forEach((el) => setActive(el, el.dataset.flashKind === flashPrefs.kind));
    renderFlashBests();
  }

  // ---- Bereich (axes/zones) - same picker pattern as Periph's, mirrored
  // onto flashPrefs.axes/useZones/zones, shared by both ready screens. ----
  document.querySelectorAll("#flashFieldRow [data-flash-axis], #flashTrainingFieldRow [data-flash-axis]").forEach((el) => {
    el.addEventListener("click", () => {
      const axis = el.dataset.flashAxis;
      const on = flashPrefs.axes.includes(axis);
      flashPrefs.axes = on ? flashPrefs.axes.filter((a) => a !== axis) : [...flashPrefs.axes, axis];
      saveFlashPrefsToStorage();
      syncFlashFieldUI();
    });
  });
  function flashToggleAllAxes() {
    const allOn = flashPrefs.axes.length === PERIPH_AXIS_KEYS.length;
    flashPrefs.axes = allOn ? [] : PERIPH_AXIS_KEYS.slice();
    saveFlashPrefsToStorage();
    syncFlashFieldUI();
  }
  els.flashAllBtn.addEventListener("click", flashToggleAllAxes);
  els.flashTrainingAllBtn.addEventListener("click", flashToggleAllAxes);
  function flashToggleZonesMode() {
    flashPrefs.useZones = !flashPrefs.useZones;
    saveFlashPrefsToStorage();
    syncFlashFieldUI();
  }
  els.flashZonesBtn.addEventListener("click", flashToggleZonesMode);
  els.flashTrainingZonesBtn.addEventListener("click", flashToggleZonesMode);
  document.querySelectorAll("#flashZoneGrid [data-zone], #flashTrainingZoneGrid [data-zone]").forEach((el) => {
    el.addEventListener("click", () => {
      const z = el.dataset.zone;
      const on = flashPrefs.zones.includes(z);
      if (on && flashPrefs.zones.length <= 1) return;
      flashPrefs.zones = on ? flashPrefs.zones.filter((k) => k !== z) : [...flashPrefs.zones, z];
      saveFlashPrefsToStorage();
      syncFlashFieldUI();
    });
  });
  function syncFlashFieldUI() {
    document.querySelectorAll("#flashFieldRow [data-flash-axis], #flashTrainingFieldRow [data-flash-axis]").forEach((el) => setActive(el, flashPrefs.axes.includes(el.dataset.flashAxis)));
    setActive(els.flashAllBtn, flashPrefs.axes.length === PERIPH_AXIS_KEYS.length);
    setActive(els.flashTrainingAllBtn, flashPrefs.axes.length === PERIPH_AXIS_KEYS.length);
    setActive(els.flashZonesBtn, flashPrefs.useZones);
    setActive(els.flashTrainingZonesBtn, flashPrefs.useZones);
    els.flashFieldRow.hidden = flashPrefs.useZones;
    els.flashTrainingFieldRow.hidden = flashPrefs.useZones;
    els.flashZoneGrid.hidden = !flashPrefs.useZones;
    els.flashTrainingZoneGrid.hidden = !flashPrefs.useZones;
    document.querySelectorAll("#flashZoneGrid [data-zone], #flashTrainingZoneGrid [data-zone]").forEach((el) => el.classList.toggle("active", flashPrefs.zones.includes(el.dataset.zone)));
    const belowMin = !flashPrefs.useZones && flashPrefs.axes.length === 0;
    els.flashFieldHint.textContent = belowMin ? "Wähle mindestens einen Bereich." : "";
    els.flashFieldHint.classList.toggle("warn", belowMin);
    els.flashTrainingFieldHint.textContent = belowMin ? "Wähle mindestens einen Bereich." : "";
    els.flashTrainingFieldHint.classList.toggle("warn", belowMin);
    els.flashReadyStartBtn.disabled = belowMin;
    els.flashTrainingStartBtn.disabled = belowMin;
  }

  // ---- Schwierigkeit / Bei Fehler / mode-specific sliders ----
  function flashDifficultyBucket() {
    for (const key of Object.keys(FLASH_DIFFICULTIES)) {
      const p = FLASH_DIFFICULTIES[key];
      if (Math.abs(p.stimulusS - flashPrefs.stimulusS) < 0.001 && Math.abs(p.intervalS - flashPrefs.intervalS) < 0.001) return key;
    }
    return "custom";
  }
  function syncFlashSpeedUI() {
    els.flashStimulusSlider.value = flashPrefs.stimulusS;
    els.flashStimulusValue.textContent = fmtSeconds(flashPrefs.stimulusS);
    els.flashIntervalSlider.value = flashPrefs.intervalS;
    els.flashIntervalValue.textContent = fmtSeconds(flashPrefs.intervalS);
    els.flashTrainingStimulusSlider.value = flashPrefs.stimulusS;
    els.flashTrainingStimulusValue.textContent = fmtSeconds(flashPrefs.stimulusS);
    els.flashTrainingIntervalSlider.value = flashPrefs.intervalS;
    els.flashTrainingIntervalValue.textContent = fmtSeconds(flashPrefs.intervalS);
  }
  function syncFlashDifficultyUI() {
    const bucket = flashDifficultyBucket();
    document.querySelectorAll("#flashDifficultyRow [data-flash-diff]").forEach((el) => setActive(el, el.dataset.flashDiff === bucket));
    els.flashDiffCustom.hidden = bucket !== "custom";
    syncFlashSpeedUI();
    updateFlashReadyBestHint();
  }
  document.querySelectorAll("#flashDifficultyRow [data-flash-diff]").forEach((el) => {
    el.addEventListener("click", () => {
      Object.assign(flashPrefs, FLASH_DIFFICULTIES[el.dataset.flashDiff]);
      saveFlashPrefsToStorage();
      syncFlashDifficultyUI();
    });
  });
  function flashSpeedSliderInput() {
    flashPrefs.stimulusS = Number(els.flashStimulusSlider.value);
    flashPrefs.intervalS = Number(els.flashIntervalSlider.value);
    saveFlashPrefsToStorage();
    syncFlashDifficultyUI();
  }
  els.flashStimulusSlider.addEventListener("input", flashSpeedSliderInput);
  els.flashIntervalSlider.addEventListener("input", flashSpeedSliderInput);
  function flashTrainingSpeedSliderInput() {
    flashPrefs.stimulusS = Number(els.flashTrainingStimulusSlider.value);
    flashPrefs.intervalS = Number(els.flashTrainingIntervalSlider.value);
    saveFlashPrefsToStorage();
    syncFlashDifficultyUI();
  }
  els.flashTrainingStimulusSlider.addEventListener("input", flashTrainingSpeedSliderInput);
  els.flashTrainingIntervalSlider.addEventListener("input", flashTrainingSpeedSliderInput);

  document.querySelectorAll("#flashErrorRow [data-flash-error]").forEach((el) => {
    el.addEventListener("click", () => {
      flashPrefs.errorMode = el.dataset.flashError;
      saveFlashPrefsToStorage();
      syncFlashErrorUI();
    });
  });
  function syncFlashErrorUI() {
    document.querySelectorAll("#flashErrorRow [data-flash-error]").forEach((el) => setActive(el, el.dataset.flashError === flashPrefs.errorMode));
  }
  els.flashConstantSlider.addEventListener("input", () => {
    flashPrefs.constantCount = Number(els.flashConstantSlider.value);
    saveFlashPrefsToStorage();
    syncFlashConstantUI();
  });
  function syncFlashConstantUI() {
    els.flashConstantSlider.value = flashPrefs.constantCount;
    els.flashConstantValue.textContent = String(flashPrefs.constantCount);
  }
  els.flashStartSlider.addEventListener("input", () => {
    flashPrefs.startCount = Number(els.flashStartSlider.value);
    saveFlashPrefsToStorage();
    syncFlashStartUI();
  });
  function syncFlashStartUI() {
    els.flashStartSlider.value = flashPrefs.startCount;
    els.flashStartValue.textContent = String(flashPrefs.startCount);
  }
  els.flashRepsSlider.addEventListener("input", () => {
    flashPrefs.repsPerLevel = Number(els.flashRepsSlider.value);
    saveFlashPrefsToStorage();
    syncFlashRepsUI();
  });
  function syncFlashRepsUI() {
    els.flashRepsSlider.value = flashPrefs.repsPerLevel;
    els.flashRepsValue.textContent = String(flashPrefs.repsPerLevel);
  }
  els.flashTrainingStartSlider.addEventListener("input", () => {
    flashPrefs.trainingStart = Number(els.flashTrainingStartSlider.value);
    saveFlashPrefsToStorage();
    syncFlashTrainingUI();
  });
  document.querySelectorAll("#flashTrainingProgressRow [data-flash-progress]").forEach((el) => {
    el.addEventListener("click", () => {
      flashPrefs.trainingProgress = el.dataset.flashProgress === "1";
      saveFlashPrefsToStorage();
      syncFlashTrainingUI();
    });
  });
  function syncFlashTrainingUI() {
    els.flashTrainingStartSlider.value = flashPrefs.trainingStart;
    els.flashTrainingStartValue.textContent = String(flashPrefs.trainingStart);
    document.querySelectorAll("#flashTrainingProgressRow [data-flash-progress]").forEach((el) => setActive(el, (el.dataset.flashProgress === "1") === flashPrefs.trainingProgress));
    syncFlashSpeedUI();
    const best = flashBestFor("training");
    els.flashTrainingBestHint.textContent = best
      ? `Deine bisher höchste geschaffte Zeichenfolge im Trainingsmodus: ${best}.`
      : "Noch keine Bestleistung im Trainingsmodus – leg los!";
  }

  // ---- Ready screens ----
  let flashReadyMode = "constant";
  function updateFlashReadyBestHint() {
    const best = flashBestFor(flashReadyMode);
    els.flashReadyBestHint.textContent = best
      ? (flashReadyMode === "constant" ? `Deine Bestleistung: Tempo-Stufe ${best + 1}.` : `Deine bisher höchste geschaffte Zeichenfolge: ${best}.`)
      : "Noch keine Bestleistung bei diesem Modus – leg los!";
  }
  function openFlashReady(mode) {
    flashReadyMode = mode;
    els.flashReadyTitle.textContent = mode === "constant" ? "Konstant" : mode === "climb" ? "Steigend, direkt" : "Steigend, mit Wiederholung";
    els.flashReadyDesc.textContent = mode === "constant"
      ? "Immer gleich viele Zahlen – wird dafür immer schneller eingeblendet."
      : mode === "climb"
      ? "Nach jeder richtigen Runde kommt eine Zahl mehr dazu."
      : "Jede Stufe wird erst mehrmals wiederholt, bevor eine Zahl dazukommt.";
    els.flashConstantGroup.hidden = mode !== "constant";
    els.flashStartGroup.hidden = mode === "constant";
    els.flashRepsGroup.hidden = mode !== "climbRepeat";
    syncFlashKindUI();
    syncFlashFieldUI();
    syncFlashDifficultyUI();
    syncFlashErrorUI();
    syncFlashConstantUI();
    syncFlashStartUI();
    syncFlashRepsUI();
    syncFlashBgUI();
    syncFlashFixUI();
    updateFlashReadyBestHint();
    showScreen("flashReady");
  }
  els.flashOpenConstant.addEventListener("click", () => openFlashReady("constant"));
  els.flashOpenClimb.addEventListener("click", () => openFlashReady("climb"));
  els.flashOpenClimbRepeat.addEventListener("click", () => openFlashReady("climbRepeat"));
  els.flashReadyBackToHome.addEventListener("click", () => showScreen("natHome"));
  els.flashOpenTraining.addEventListener("click", () => {
    syncFlashKindUI();
    syncFlashFieldUI();
    syncFlashTrainingUI();
    syncFlashBgUI();
    syncFlashFixUI();
    showScreen("flashTrainingReady");
  });
  els.flashTrainingBackToHome.addEventListener("click", () => showScreen("natHome"));

  // ---- Round engine ----
  // Same {fx,fy} fractional positioning as Periph, so a number already
  // mid-flash still lands correctly if the device is rotated.
  function randFlashPos() {
    if (flashState.useZones) {
      const zones = flashState.zones.length ? flashState.zones : PERIPH_ZONE_KEYS;
      const { row, col } = PERIPH_ZONES[zones[Math.floor(Math.random() * zones.length)]];
      const pad = 0.14, cell = 1 / 3;
      return {
        fx: col * cell + pad * cell + Math.random() * cell * (1 - 2 * pad),
        fy: row * cell + pad * cell + Math.random() * cell * (1 - 2 * pad),
      };
    }
    const axes = flashState.axes.length ? flashState.axes : PERIPH_AXIS_KEYS;
    const radiusFrac = 0.45 + Math.random() * 0.5;
    const axis = axes[Math.floor(Math.random() * axes.length)];
    const bases = PERIPH_FIELD_ANGLES[axis];
    const base = bases[Math.floor(Math.random() * bases.length)];
    const angle = base + (Math.random() - 0.5) * (Math.PI / 6);
    return { fx: 0.5 + 0.42 * radiusFrac * Math.cos(angle), fy: 0.5 + 0.42 * radiusFrac * Math.sin(angle) };
  }
  // Same timer-wrapping trick as Remember/Blitz-Raster: records what's
  // pending and when it fires, so Pause can cancel it and Resume can
  // replay it with its exact remaining delay.
  function scheduleFlashTimer(fn, delayMs) {
    flashState.timerFn = fn;
    flashState.timerFiresAt = performance.now() + delayMs;
    flashState.timer = setTimeout(fn, delayMs);
  }
  function flashEffectiveStimulusS() {
    if (flashState.mode !== "constant") return flashState.stimulusS;
    return Math.max(0.12, flashState.stimulusS * Math.pow(0.85, flashState.speedStep));
  }
  function flashEffectiveIntervalS() {
    if (flashState.mode !== "constant") return flashState.intervalS;
    return Math.max(0.08, flashState.intervalS * Math.pow(0.85, flashState.speedStep));
  }
  function flashStartRound() {
    const count = flashState.mode === "constant" ? flashState.constantCount : flashState.count;
    flashState.sequence = Array.from({ length: count }, () => randPeriphChar(flashState.kind, Math.random));
    flashState.shownIndex = 0;
    els.flashInputPanel.hidden = true;
    els.flashHint.textContent = "Merken …";
    els.flashLevelEl.textContent = flashState.mode === "constant" ? `Tempo-Stufe ${flashState.speedStep + 1}` : `${flashState.count} ${flashUnitLabel(flashState.kind)}`;
    flashShowDigit();
  }
  function flashShowDigit() {
    const digit = flashState.sequence[flashState.shownIndex];
    const pos = randFlashPos();
    flashState.phase = "flash";
    renderFlashFixpoint(); // restores it (if enabled) after flashOpenInput() forced it off
    els.flashDigitEl.textContent = digit;
    els.flashDigitEl.style.left = pos.fx * 100 + "%";
    els.flashDigitEl.style.top = flashSafeFy(pos.fy) * 100 + "%";
    els.flashDigitEl.hidden = false;
    scheduleFlashTimer(flashAfterDigit, flashEffectiveStimulusS() * 1000);
  }
  // randFlashPos() is shared with Periph, which has no fixed on-screen text -
  // Flash Speicher Test always shows the "Merken …"/"Richtig!"/error hint
  // pill near the top of the stage, so a digit placed near-vertical at a
  // large radius can land underneath/inside it. Measure the hint's actual
  // rendered bottom edge (adapts to safe-area insets and device size) and
  // push the digit down below it instead of hardcoding a percentage.
  function flashSafeFy(fy) {
    const stageRect = els.flashStage.getBoundingClientRect();
    if (!stageRect.height) return fy;
    const hintRect = els.flashHint.getBoundingClientRect();
    const minFy = (hintRect.bottom - stageRect.top + 20) / stageRect.height;
    return Math.min(0.94, Math.max(fy, minFy));
  }
  function flashAfterDigit() {
    if (!flashState) return;
    els.flashDigitEl.hidden = true;
    flashState.shownIndex += 1;
    if (flashState.shownIndex >= flashState.sequence.length) {
      flashOpenInput();
    } else {
      flashState.phase = "gap";
      scheduleFlashTimer(flashShowDigit, flashEffectiveIntervalS() * 1000);
    }
  }
  // On-screen keypad (Zahlen 0-9, Buchstaben A-Z minus I/O, or both for
  // Gemischt) instead of the system keyboard - built once per game (the
  // Zeichentyp doesn't change mid-run), tapping a key fills the next empty
  // answer box, same "auto-check once full" behaviour the old text input had.
  function renderFlashKeypad() {
    const keys = flashState.kind === "buchstaben" ? PERIPH_LETTERS.split("")
      : flashState.kind === "gemischt" ? [...PERIPH_DIGITS.split(""), ...PERIPH_LETTERS.split("")]
      : PERIPH_DIGITS.split("");
    els.flashKeypad.style.setProperty("--flash-keypad-cols", flashState.kind === "zahlen" ? "5" : "6");
    els.flashKeypad.innerHTML = "";
    keys.forEach((k) => {
      const btn = document.createElement("button");
      btn.className = "flash-key";
      btn.type = "button";
      btn.textContent = k;
      btn.addEventListener("click", () => flashTypeChar(k));
      els.flashKeypad.appendChild(btn);
    });
  }
  function renderFlashAnswerBoxes() {
    els.flashAnswerBoxes.innerHTML = "";
    for (let i = 0; i < flashState.sequence.length; i++) {
      const box = document.createElement("div");
      box.className = "flash-answer-box";
      els.flashAnswerBoxes.appendChild(box);
    }
    syncFlashAnswerBoxes();
  }
  function syncFlashAnswerBoxes() {
    const boxes = els.flashAnswerBoxes.children;
    for (let i = 0; i < boxes.length; i++) {
      const ch = flashState.typed[i] || "";
      boxes[i].textContent = ch;
      boxes[i].classList.toggle("filled", !!ch);
    }
  }
  function flashTypeChar(ch) {
    if (!flashState || flashState.phase !== "input" || flashState.paused) return;
    if (flashState.typed.length >= flashState.sequence.length) return;
    flashState.typed += ch;
    syncFlashAnswerBoxes();
    if (flashState.typed.length >= flashState.sequence.length) flashCheckAnswer(flashState.typed);
  }
  function flashBackspace() {
    if (!flashState || flashState.phase !== "input" || flashState.paused) return;
    flashState.typed = flashState.typed.slice(0, -1);
    syncFlashAnswerBoxes();
  }
  els.flashBackspaceBtn.addEventListener("click", flashBackspace);
  function flashOpenInput() {
    flashState.phase = "input";
    flashState.typed = "";
    els.flashHint.textContent = "Jetzt in der richtigen Reihenfolge eintippen";
    renderFlashAnswerBoxes();
    els.flashInputPanel.hidden = false;
    // The fixpoint is absolutely centred on the whole stage, which - once
    // the answer panel (boxes + keypad) fills that space - lands it right
    // on top of the keypad and covers a key. Always hide it here regardless
    // of flashPrefs.fixEnabled; flashShowDigit() restores it for the next
    // flash/gap phase.
    els.flashFixpointEl.hidden = true;
  }
  function flashCheckAnswer(typed) {
    flashState.phase = "checking";
    if (typed === flashState.sequence.join("")) flashSuccessTransition();
    else flashWrongTransition();
  }
  function flashSuccessTransition() {
    els.flashHint.textContent = "Richtig! Weiter geht's …";
    els.flashInputPanel.hidden = true;
    if (flashState.mode === "constant") {
      if (flashState.speedStep > flashState.cleared) flashState.cleared = flashState.speedStep;
      flashState.speedStep = Math.min(FLASH_SPEED_STEPS, flashState.speedStep + 1);
    } else if (flashState.mode === "climb") {
      if (flashState.count > flashState.cleared) flashState.cleared = flashState.count;
      flashState.count += 1;
    } else if (flashState.mode === "climbRepeat") {
      flashState.repsDone += 1;
      if (flashState.repsDone >= flashState.repsPerLevel) {
        if (flashState.count > flashState.cleared) flashState.cleared = flashState.count;
        flashState.count += 1;
        flashState.repsDone = 0;
      }
    } else if (flashState.mode === "training") {
      if (flashState.count > flashState.cleared) flashState.cleared = flashState.count;
      if (flashState.trainingProgress) flashState.count += 1;
    }
    scheduleFlashTimer(flashStartRound, 900);
  }
  function flashWrongTransition() {
    let hint;
    els.flashInputPanel.hidden = true;
    if (flashState.mode === "training") {
      flashState.count = flashState.trainingStartLevel;
      hint = "Leider falsch – nochmal von vorne";
    } else if (flashState.mode === "constant") {
      if (flashState.errorMode === "stay") hint = "Leider falsch – nochmal versuchen";
      else if (flashState.errorMode === "backOne") { flashState.speedStep = Math.max(0, flashState.speedStep - 1); hint = "Leider falsch – einen Schritt langsamer"; }
      else { flashState.speedStep = 0; hint = "Leider falsch – wieder von vorne"; }
    } else {
      flashState.repsDone = 0;
      if (flashState.errorMode === "stay") hint = "Leider falsch – nochmal versuchen";
      else if (flashState.errorMode === "backOne") { flashState.count = Math.max(2, flashState.count - 1); hint = "Leider falsch – eine Zahl weniger"; }
      else { flashState.count = flashState.startLevel; hint = "Leider falsch – nochmal von vorne"; }
    }
    els.flashHint.textContent = hint;
    scheduleFlashTimer(flashStartRound, 1400);
  }

  let flashState = null;
  let lastFlashMode = null;
  let flashReturnScreen = "natHome";
  function startFlashGame(mode) {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.flashPlayer.hidden = false;
    els.flashPlayerBar.hidden = false;
    els.flashDonePanel.hidden = true;
    els.flashPauseOverlay.hidden = true;
    els.flashPauseBtn.hidden = false;
    els.flashInputPanel.hidden = true;
    els.flashDigitEl.hidden = true;
    lastFlashMode = mode;
    flashReturnScreen = mode === "training" ? "flashTrainingReady" : "flashReady";
    const startCount = mode === "training" ? flashPrefs.trainingStart : flashPrefs.startCount;
    flashState = {
      mode, kind: flashPrefs.kind, count: startCount, constantCount: flashPrefs.constantCount, speedStep: 0, repsDone: 0, cleared: 0,
      sequence: [], shownIndex: 0, typed: "", phase: "flash", timer: null,
      stimulusS: flashPrefs.stimulusS, intervalS: flashPrefs.intervalS, errorMode: flashPrefs.errorMode,
      axes: flashPrefs.axes.slice(), zones: flashPrefs.zones.slice(), useZones: flashPrefs.useZones,
      trainingProgress: flashPrefs.trainingProgress, startLevel: flashPrefs.startCount, trainingStartLevel: flashPrefs.trainingStart,
      startTime: performance.now(), paused: false,
    };
    renderFlashKeypad();
    applyFlashBg();
    renderFlashFixpoint();
    requestWakeLock();
    flashStartRound();
  }
  els.flashReadyStartBtn.addEventListener("click", () => startFlashGame(flashReadyMode));
  els.flashTrainingStartBtn.addEventListener("click", () => startFlashGame("training"));

  // ---- Pause mid-game, live-adjust the background - same trick as
  // Remember/Blitz-Raster's pause (cancel the pending timer, replay it
  // with its exact remaining delay on resume). ----
  function pauseFlash() {
    if (!flashState || flashState.paused) return;
    flashState.paused = true;
    flashState.pausedAt = performance.now();
    if (flashState.timer) {
      clearTimeout(flashState.timer);
      flashState.timer = null;
      flashState.timerRemainingMs = Math.max(0, flashState.timerFiresAt - flashState.pausedAt);
    }
    syncFlashBgUI();
    els.flashPauseBtn.hidden = true;
    els.flashPauseOverlay.hidden = false;
  }
  function resumeFlash() {
    if (!flashState || !flashState.paused) return;
    flashState.startTime += performance.now() - flashState.pausedAt;
    flashState.paused = false;
    if (flashState.timerFn && flashState.timerRemainingMs != null) {
      scheduleFlashTimer(flashState.timerFn, flashState.timerRemainingMs);
      flashState.timerRemainingMs = null;
    }
    els.flashPauseOverlay.hidden = true;
    els.flashPauseBtn.hidden = false;
  }
  els.flashPauseBtn.addEventListener("click", pauseFlash);
  els.flashResumeBtn.addEventListener("click", resumeFlash);

  // "Beenden" doubles as the finish action, same convention as Remember/
  // Blitz-Raster - Flash Speicher Test is endless/progressive with no
  // fixed end of its own.
  function flashStop() {
    if (!flashState) return;
    if (flashState.timer) clearTimeout(flashState.timer);
    const state = flashState;
    flashState = null;
    els.flashPauseOverlay.hidden = true;
    els.flashDigitEl.hidden = true;
    els.flashInputPanel.hidden = true;
    els.flashFixpointEl.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.flashPlayer) document.exitFullscreen().catch(() => {});
    els.flashFsHint.hidden = true;
    if (state.cleared > 0) {
      const isRecord = saveFlashBest(state.mode, state.cleared);
      renderFlashBests();
      const played = (performance.now() - state.startTime) / 1000;
      const modeTitle = state.mode === "constant" ? "Konstant" : state.mode === "climb" ? "Steigend, direkt" : state.mode === "climbRepeat" ? "Steigend, mit Wiederholung" : "Trainingsmodus";
      const note = state.mode === "constant" ? `Tempo-Stufe ${state.cleared + 1} erreicht` : `${state.cleared} ${flashUnitLabel(state.kind)} erreicht`;
      els.flashPlayerBar.hidden = true;
      els.flashDoneSummary.textContent = `${modeTitle} · ${note}` + (isRecord ? " · Neue Bestleistung!" : "");
      const id = addHistory({ kind: "flash", title: `Flash Speicher Test · ${modeTitle}`, seconds: Math.round(played), note });
      renderRating(els.flashRating, id, "Wie war deine Konzentration?");
      els.flashDonePanel.hidden = false;
    } else {
      els.flashPlayer.hidden = true;
      showScreen(flashReturnScreen);
    }
  }
  els.flashBackBtn.addEventListener("click", flashStop);
  els.flashAgainBtn.addEventListener("click", () => { els.flashDonePanel.hidden = true; startFlashGame(lastFlashMode); });
  els.flashDoneBackBtn.addEventListener("click", () => { els.flashPlayer.hidden = true; els.flashDonePanel.hidden = true; showScreen("natHome"); });

  // ==== MOT-Fähigkeit engine ====
  // Multiple Object Tracking: N identical-looking objects drift around the
  // stage; K of them are briefly highlighted as "targets", then everything
  // looks the same again and keeps moving for a while - the client has to
  // track the target(s) with their eyes the whole time - and finally
  // everything stops and the client taps back exactly the target(s), same
  // unordered tap-set mechanic as Blitz-Raster's (blitzTapCell). A genuinely
  // new shape for this app: every other exercise is either a precomputed
  // schedule (VT/Periph, tick()-driven) or discrete flash/gap/input phases
  // (Remember/Blitz/Flash, setTimeout-driven) - MOT additionally needs a
  // continuous physics simulation (bouncing off the stage edges) during its
  // "tracking" phase, so it's the first requestAnimationFrame-driven engine
  // outside the VT canvas.
  //
  // Difficulty progression is modelled on the established MOT literature
  // (researched before building this, not guessed): the classic paradigm
  // and commercial tools (e.g. NeuroTracker's 3D-MOT) fix object/target
  // count per session (NeuroTracker: 8 objects, 4 targets) and instead adapt
  // SPEED via a staircase - correct round: speed up by a fixed ratio; wrong:
  // slow down by the same ratio. An initial draft only offered that one
  // "Tempo steigt" shape; the client then asked for the other two obvious
  // axes too - "Anzahl steigt" (count grows, speed fixed) and "Beides
  // steigt" - plus a Trainingsmodus, mirroring how Flash Speicher Test
  // itself grew from one mode to four. So there are now FOUR modes sharing
  // one `motPrefs` object (mirroring `flashPrefs`): "speed" (fixed count,
  // Tempo-Stufe rises), "count" (fixed speed, count rises), "both" (both
  // rise together), "training" (direct start at a chosen object/target/
  // speed combination, with the same "weiter steigern"/"bei dieser
  // Einstellung bleiben" choice as Flash's Trainingsmodus - progressing
  // there follows the same rule as "both"). A single `motState.level`
  // counter drives whichever of these an active mode says should grow;
  // Bei-Fehler always resets/steps that one counter, so the three error
  // options behave identically regardless of what they end up changing.
  //
  // Plus a "Darstellung" and "Farbe der Objekte" setting the client asked
  // for up front - "Flach" (plain circles) or "3D-Optik" (a radial-gradient
  // glossy-sphere look, generated from whichever colour(s) are chosen -
  // see motGradientCss()) - movement stays a flat 2D plane either way;
  // genuine 3D movement is explicitly "Zukunftsmusik" per the client, not
  // attempted here. Objects don't bounce off each other (only off the stage
  // edges) - a full elastic collision isn't needed here - but a lightweight
  // positional separation pass (motSeparateObjects()) keeps them from fully
  // overlapping, which would otherwise hide one object behind another and
  // make it untappable once movement stops (a real usability bug, not just
  // a visual nitpick).
  const MOT_PREFS_KEY = "fwmc-mot-prefs-v1";
  const MOT_DIFFICULTIES = {
    leicht: { title: "Leicht", speed: 0.10, trackS: 5, highlightS: 2.5 },
    mittel: { title: "Mittel", speed: 0.16, trackS: 7, highlightS: 2 },
    schwer: { title: "Schwer", speed: 0.24, trackS: 9, highlightS: 1.5 },
  };
  // Per-round speed multiplier for a correct/wrong round: 10^0.05 ≈ 1.12,
  // matching NeuroTracker's published "±0.05 log" staircase step exactly.
  const MOT_SPEED_STEP_FACTOR = 1.12;
  const MOT_OBJ_MIN = 3, MOT_OBJ_MAX = 12;
  const MOT_TARGET_MAX = 4;
  const MOT_RADIUS = 22; // px - constant regardless of object count, like real MOT tasks
  // Each object's actual clickable hit-area is a square (2×radius a side),
  // not the circle it looks like. Two circles merely touching (centres
  // 2×radius apart) can still have OVERLAPPING square hit-areas depending
  // on the angle between them (worst case: exactly diagonal, needing up to
  // 2×radius×√2 ≈ 2.83×radius of separation to guarantee no overlap at any
  // angle) - hence 2.9, not the more obvious-looking 2. Below this, a tap
  // meant for one object could register on its (invisibly) overlapping
  // neighbour instead - confusing for a real finger, and exactly what broke
  // Playwright's own click targeting during testing.
  const MOT_MIN_DIST_FACTOR = 2.9;
  const motPrefs = {
    speed: MOT_DIFFICULTIES.mittel.speed,
    trackS: MOT_DIFFICULTIES.mittel.trackS,
    highlightS: MOT_DIFFICULTIES.mittel.highlightS,
    errorMode: "reset2",
    style: "flach",
    colors: ["schwarz"],
    targetColors: ["gelb"], // "gelb" = #f2a900, the exact colour .mot-object.target used before this was configurable
    bgColorKey: "gruen",
    bgIntensity: 0,
    objectCount: 8, targetCount: 4,           // "speed" mode's fixed counts (matches NeuroTracker's own 8/4)
    growStartObjects: 4, growStartTargets: 1, // "count"/"both" modes' starting counts
    trainingObjects: 6, trainingTargets: 2, trainingSpeedStep: 0, trainingProgress: true,
  };
  function loadMotPrefs() {
    const saved = readJSON(MOT_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(motPrefs, saved);
    if (typeof motPrefs.speed !== "number" || motPrefs.speed < 0.05 || motPrefs.speed > 0.4) motPrefs.speed = MOT_DIFFICULTIES.mittel.speed;
    if (typeof motPrefs.trackS !== "number" || motPrefs.trackS < 3 || motPrefs.trackS > 15) motPrefs.trackS = MOT_DIFFICULTIES.mittel.trackS;
    if (typeof motPrefs.highlightS !== "number" || motPrefs.highlightS < 1 || motPrefs.highlightS > 4) motPrefs.highlightS = MOT_DIFFICULTIES.mittel.highlightS;
    if (!["reset2", "backOne", "stay"].includes(motPrefs.errorMode)) motPrefs.errorMode = "reset2";
    if (!["flach", "3d"].includes(motPrefs.style)) motPrefs.style = "flach";
    if (!Array.isArray(motPrefs.colors) || !motPrefs.colors.length || !motPrefs.colors.every((k) => STROOP_COLOR_BY_KEY[k])) motPrefs.colors = ["schwarz"];
    if (!Array.isArray(motPrefs.targetColors) || !motPrefs.targetColors.length || !motPrefs.targetColors.every((k) => STROOP_COLOR_BY_KEY[k])) motPrefs.targetColors = ["gelb"];
    if (!STROOP_COLOR_BY_KEY[motPrefs.bgColorKey]) motPrefs.bgColorKey = "gruen";
    if (typeof motPrefs.bgIntensity !== "number" || motPrefs.bgIntensity < 0 || motPrefs.bgIntensity > 1) motPrefs.bgIntensity = 0;
    if (typeof motPrefs.objectCount !== "number" || motPrefs.objectCount < MOT_OBJ_MIN || motPrefs.objectCount > MOT_OBJ_MAX) motPrefs.objectCount = 8;
    if (typeof motPrefs.targetCount !== "number" || motPrefs.targetCount < 1) motPrefs.targetCount = 4;
    motPrefs.targetCount = Math.min(motPrefs.targetCount, Math.max(1, motPrefs.objectCount - 2), MOT_TARGET_MAX);
    if (typeof motPrefs.growStartObjects !== "number" || motPrefs.growStartObjects < MOT_OBJ_MIN || motPrefs.growStartObjects > 8) motPrefs.growStartObjects = 4;
    if (typeof motPrefs.growStartTargets !== "number" || motPrefs.growStartTargets < 1) motPrefs.growStartTargets = 1;
    motPrefs.growStartTargets = Math.min(motPrefs.growStartTargets, Math.max(1, motPrefs.growStartObjects - 2), 3);
    if (typeof motPrefs.trainingObjects !== "number" || motPrefs.trainingObjects < MOT_OBJ_MIN || motPrefs.trainingObjects > MOT_OBJ_MAX) motPrefs.trainingObjects = 6;
    if (typeof motPrefs.trainingTargets !== "number" || motPrefs.trainingTargets < 1) motPrefs.trainingTargets = 2;
    motPrefs.trainingTargets = Math.min(motPrefs.trainingTargets, Math.max(1, motPrefs.trainingObjects - 2), MOT_TARGET_MAX);
    if (typeof motPrefs.trainingSpeedStep !== "number" || motPrefs.trainingSpeedStep < 0) motPrefs.trainingSpeedStep = 0;
    if (typeof motPrefs.trainingProgress !== "boolean") motPrefs.trainingProgress = true;
  }
  function saveMotPrefsToStorage() { writeJSON(MOT_PREFS_KEY, motPrefs); }
  loadMotPrefs();

  const MOT_BEST_KEY = "fwmc-mot-best-v1"; // { speed: bestLevel, count: N, both: N, training: N }
  function motDifficultyBucket() {
    for (const key of Object.keys(MOT_DIFFICULTIES)) {
      const p = MOT_DIFFICULTIES[key];
      if (Math.abs(p.speed - motPrefs.speed) < 0.001 && Math.abs(p.trackS - motPrefs.trackS) < 0.001 && Math.abs(p.highlightS - motPrefs.highlightS) < 0.001) return key;
    }
    return "custom";
  }
  function motBestFor(mode) { return readJSON(MOT_BEST_KEY, {})[mode] || 0; }
  function saveMotBest(mode, level) {
    const all = readJSON(MOT_BEST_KEY, {});
    if (level > (all[mode] || 0)) { all[mode] = level; writeJSON(MOT_BEST_KEY, all); return true; }
    return false;
  }
  function renderMotBests() {
    const s = motBestFor("speed"), c = motBestFor("count"), b = motBestFor("both"), t = motBestFor("training");
    els.motBestSpeed.textContent = s ? `Bestleistung: Tempo-Stufe ${s + 1}` : "";
    els.motBestCount.textContent = c ? `Bestleistung: Stufe ${c}` : "";
    els.motBestBoth.textContent = b ? `Bestleistung: Stufe ${b}` : "";
    els.motBestTraining.textContent = t ? `Bestleistung: Stufe ${t}` : "";
  }
  renderMotBests();

  function applyMotBg() {
    els.motStage.style.background = motPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[motPrefs.bgColorKey].hex, motPrefs.bgIntensity)
      : "";
  }
  const syncMotBgUI = wireBgIntensityControl(motPrefs, {
    pickers: [els.motBgColorPicker, els.motTrainingBgColorPicker, els.motPauseBgColorPicker],
    sliders: [els.motBgIntensitySlider, els.motTrainingBgIntensitySlider, els.motPauseBgSlider],
    valueEls: [els.motBgIntensityValue, els.motTrainingBgIntensityValue, els.motPauseBgValue],
    hintEls: [els.motBgContrastHint, els.motTrainingBgContrastHint],
    transfer: [
      {
        sourceRow: els.motBgSourceRow, presetGroup: els.motBgPresetGroup, presetList: els.motBgPresetList,
        saveBtn: els.motBgSaveBtn, form: els.motBgSaveForm, nameInput: els.motBgSaveNameInput,
        cancelBtn: els.motBgSaveCancelBtn, confirmBtn: els.motBgSaveConfirmBtn,
      },
      {
        sourceRow: els.motTrainingBgSourceRow, presetGroup: els.motTrainingBgPresetGroup, presetList: els.motTrainingBgPresetList,
        saveBtn: els.motTrainingBgSaveBtn, form: els.motTrainingBgSaveForm, nameInput: els.motTrainingBgSaveNameInput,
        cancelBtn: els.motTrainingBgSaveCancelBtn, confirmBtn: els.motTrainingBgSaveConfirmBtn,
      },
    ],
  }, () => { saveMotPrefsToStorage(); applyMotBg(); }, "mot");

  // ---- Darstellung: Flach vs. 3D-Optik (still 2D movement either way) -
  // shared by both ready screens, same "two synced DOM instances" pattern
  // as Flash's Bereich/Fixpunkt controls. ----
  document.querySelectorAll("#motStyleRow [data-mot-style], #motTrainingStyleRow [data-mot-style]").forEach((el) => {
    el.addEventListener("click", () => {
      motPrefs.style = el.dataset.motStyle;
      saveMotPrefsToStorage();
      syncMotStyleUI();
    });
  });
  function syncMotStyleUI() {
    document.querySelectorAll("#motStyleRow [data-mot-style], #motTrainingStyleRow [data-mot-style]").forEach((el) => setActive(el, el.dataset.motStyle === motPrefs.style));
  }

  // ---- Farbe der Objekte - the same generic multi-select swatch picker
  // built for the Zusatzaufgabe/Periph "Farbe der Reize" controls
  // (buildStimColorPicker/syncStimColorUI), reused as-is. "Gemischt" (2+
  // colours) rolls one colour per ROUND, not per object - every object in
  // a single round still looks identical to every other, which is the
  // whole point of the exercise; only the round-to-round palette varies. ----
  buildStimColorPicker(els.motColorPicker, () => motPrefs.colors, (keys) => { motPrefs.colors = keys; }, () => { saveMotPrefsToStorage(); syncMotColorUI(); });
  buildStimColorPicker(els.motTrainingColorPicker, () => motPrefs.colors, (keys) => { motPrefs.colors = keys; }, () => { saveMotPrefsToStorage(); syncMotColorUI(); });
  buildStimColorPicker(els.motTargetColorPicker, () => motPrefs.targetColors, (keys) => { motPrefs.targetColors = keys; }, () => { saveMotPrefsToStorage(); syncMotColorUI(); });
  buildStimColorPicker(els.motTrainingTargetColorPicker, () => motPrefs.targetColors, (keys) => { motPrefs.targetColors = keys; }, () => { saveMotPrefsToStorage(); syncMotColorUI(); });
  function syncMotColorUI() {
    syncStimColorUI(els.motColorPicker, () => motPrefs.colors, els.motColorHint);
    syncStimColorUI(els.motTrainingColorPicker, () => motPrefs.colors, els.motTrainingColorHint);
    syncStimColorUI(els.motTargetColorPicker, () => motPrefs.targetColors, els.motTargetColorHint);
    syncStimColorUI(els.motTrainingTargetColorPicker, () => motPrefs.targetColors, els.motTrainingTargetColorHint);
  }

  // ---- Bei Fehler - shared setting, no separate Trainingsmodus picker
  // (same precedent as Flash's Trainingsmodus, which also reuses whatever
  // Bei-Fehler was last set on its other screens rather than showing its
  // own). ----
  document.querySelectorAll("#motErrorRow [data-mot-error]").forEach((el) => {
    el.addEventListener("click", () => {
      motPrefs.errorMode = el.dataset.motError;
      saveMotPrefsToStorage();
      syncMotErrorUI();
    });
  });
  function syncMotErrorUI() {
    document.querySelectorAll("#motErrorRow [data-mot-error]").forEach((el) => setActive(el, el.dataset.motError === motPrefs.errorMode));
  }

  // ---- Schwierigkeit (Geschwindigkeit/Verfolgungsdauer/Markierdauer) -
  // shared base pace, two synced slider instances (main + Trainingsmodus),
  // same pattern as Flash's syncFlashSpeedUI(). ----
  function syncMotSpeedUI() {
    [[els.motSpeedSlider, els.motSpeedValue], [els.motTrainingSpeedSlider, els.motTrainingSpeedValue]].forEach(([slider, value]) => {
      slider.value = motPrefs.speed;
      value.textContent = Math.round(motPrefs.speed * 100) + "%";
    });
    [[els.motTrackSlider, els.motTrackValue], [els.motTrainingTrackSlider, els.motTrainingTrackValue]].forEach(([slider, value]) => {
      slider.value = motPrefs.trackS;
      value.textContent = fmtSeconds(motPrefs.trackS);
    });
    [[els.motHighlightSlider, els.motHighlightValue], [els.motTrainingHighlightSlider, els.motTrainingHighlightValue]].forEach(([slider, value]) => {
      slider.value = motPrefs.highlightS;
      value.textContent = fmtSeconds(motPrefs.highlightS);
    });
  }
  function syncMotDifficultyUI() {
    const bucket = motDifficultyBucket();
    document.querySelectorAll("#motDifficultyRow [data-mot-diff]").forEach((el) => setActive(el, el.dataset.motDiff === bucket));
    els.motDiffCustom.hidden = bucket !== "custom";
    syncMotSpeedUI();
    updateMotReadyBestHint();
  }
  document.querySelectorAll("#motDifficultyRow [data-mot-diff]").forEach((el) => {
    el.addEventListener("click", () => {
      Object.assign(motPrefs, MOT_DIFFICULTIES[el.dataset.motDiff]);
      saveMotPrefsToStorage();
      syncMotDifficultyUI();
    });
  });
  function motSliderInput(speedEl, trackEl, highlightEl) {
    motPrefs.speed = Number(speedEl.value);
    motPrefs.trackS = Number(trackEl.value);
    motPrefs.highlightS = Number(highlightEl.value);
    saveMotPrefsToStorage();
    syncMotDifficultyUI();
  }
  els.motSpeedSlider.addEventListener("input", () => motSliderInput(els.motSpeedSlider, els.motTrackSlider, els.motHighlightSlider));
  els.motTrackSlider.addEventListener("input", () => motSliderInput(els.motSpeedSlider, els.motTrackSlider, els.motHighlightSlider));
  els.motHighlightSlider.addEventListener("input", () => motSliderInput(els.motSpeedSlider, els.motTrackSlider, els.motHighlightSlider));
  els.motTrainingSpeedSlider.addEventListener("input", () => motSliderInput(els.motTrainingSpeedSlider, els.motTrainingTrackSlider, els.motTrainingHighlightSlider));
  els.motTrainingTrackSlider.addEventListener("input", () => motSliderInput(els.motTrainingSpeedSlider, els.motTrainingTrackSlider, els.motTrainingHighlightSlider));
  els.motTrainingHighlightSlider.addEventListener("input", () => motSliderInput(els.motTrainingSpeedSlider, els.motTrainingTrackSlider, els.motTrainingHighlightSlider));

  // ---- "speed" mode's fixed Anzahl Objekte/Ziele - the target slider's
  // max is clamped to leave ≥2 distractors and never exceed MOT_TARGET_MAX,
  // same "recompute the other slider's bounds when this one changes"
  // pattern as Blitz-Raster's syncBlitzStartUI(). ----
  els.motObjectsSlider.addEventListener("input", () => {
    motPrefs.objectCount = Number(els.motObjectsSlider.value);
    motPrefs.targetCount = Math.min(motPrefs.targetCount, Math.max(1, motPrefs.objectCount - 2), MOT_TARGET_MAX);
    saveMotPrefsToStorage();
    syncMotCountsUI();
  });
  els.motTargetsSlider.addEventListener("input", () => {
    motPrefs.targetCount = Number(els.motTargetsSlider.value);
    saveMotPrefsToStorage();
    syncMotCountsUI();
  });
  function syncMotCountsUI() {
    els.motObjectsSlider.value = motPrefs.objectCount;
    els.motObjectsValue.textContent = String(motPrefs.objectCount);
    els.motTargetsSlider.max = String(Math.min(MOT_TARGET_MAX, Math.max(1, motPrefs.objectCount - 2)));
    els.motTargetsSlider.value = motPrefs.targetCount;
    els.motTargetsValue.textContent = String(motPrefs.targetCount);
  }

  // ---- "count"/"both" modes' starting Anzahl Objekte/Ziele (the point
  // they then grow from) - a separate pair of fields from the "speed"
  // mode's fixed counts above, same "each mode keeps its own starting
  // point" precedent as Flash's constantCount vs. startCount vs.
  // trainingStart. ----
  els.motGrowObjectsSlider.addEventListener("input", () => {
    motPrefs.growStartObjects = Number(els.motGrowObjectsSlider.value);
    motPrefs.growStartTargets = Math.min(motPrefs.growStartTargets, Math.max(1, motPrefs.growStartObjects - 2), 3);
    saveMotPrefsToStorage();
    syncMotGrowStartUI();
  });
  els.motGrowTargetsSlider.addEventListener("input", () => {
    motPrefs.growStartTargets = Number(els.motGrowTargetsSlider.value);
    saveMotPrefsToStorage();
    syncMotGrowStartUI();
  });
  function syncMotGrowStartUI() {
    els.motGrowObjectsSlider.value = motPrefs.growStartObjects;
    els.motGrowObjectsValue.textContent = String(motPrefs.growStartObjects);
    els.motGrowTargetsSlider.max = String(Math.min(3, Math.max(1, motPrefs.growStartObjects - 2)));
    els.motGrowTargetsSlider.value = motPrefs.growStartTargets;
    els.motGrowTargetsValue.textContent = String(motPrefs.growStartTargets);
  }

  // ---- Trainingsmodus: direct start point for every axis + progress choice ----
  els.motTrainingObjectsSlider.addEventListener("input", () => {
    motPrefs.trainingObjects = Number(els.motTrainingObjectsSlider.value);
    motPrefs.trainingTargets = Math.min(motPrefs.trainingTargets, Math.max(1, motPrefs.trainingObjects - 2), MOT_TARGET_MAX);
    saveMotPrefsToStorage();
    syncMotTrainingUI();
  });
  els.motTrainingTargetsSlider.addEventListener("input", () => {
    motPrefs.trainingTargets = Number(els.motTrainingTargetsSlider.value);
    saveMotPrefsToStorage();
    syncMotTrainingUI();
  });
  els.motTrainingSpeedStepSlider.addEventListener("input", () => {
    motPrefs.trainingSpeedStep = Number(els.motTrainingSpeedStepSlider.value);
    saveMotPrefsToStorage();
    syncMotTrainingUI();
  });
  document.querySelectorAll("#motTrainingProgressRow [data-mot-progress]").forEach((el) => {
    el.addEventListener("click", () => {
      motPrefs.trainingProgress = el.dataset.motProgress === "1";
      saveMotPrefsToStorage();
      syncMotTrainingUI();
    });
  });
  function syncMotTrainingUI() {
    els.motTrainingObjectsSlider.value = motPrefs.trainingObjects;
    els.motTrainingObjectsValue.textContent = String(motPrefs.trainingObjects);
    els.motTrainingTargetsSlider.max = String(Math.min(MOT_TARGET_MAX, Math.max(1, motPrefs.trainingObjects - 2)));
    els.motTrainingTargetsSlider.value = motPrefs.trainingTargets;
    els.motTrainingTargetsValue.textContent = String(motPrefs.trainingTargets);
    els.motTrainingSpeedStepSlider.value = motPrefs.trainingSpeedStep;
    els.motTrainingSpeedStepValue.textContent = String(motPrefs.trainingSpeedStep + 1);
    document.querySelectorAll("#motTrainingProgressRow [data-mot-progress]").forEach((el) => setActive(el, (el.dataset.motProgress === "1") === motPrefs.trainingProgress));
    syncMotSpeedUI();
    const best = motBestFor("training");
    els.motTrainingBestHint.textContent = best ? `Deine bisher höchste geschaffte Stufe im Trainingsmodus: ${best}.` : "Noch keine Bestleistung im Trainingsmodus – leg los!";
  }

  // ---- Ready screens ----
  let motReadyMode = "speed";
  function updateMotReadyBestHint() {
    const best = motBestFor(motReadyMode);
    els.motReadyBestHint.textContent = best
      ? (motReadyMode === "speed" ? `Deine Bestleistung: Tempo-Stufe ${best + 1}.` : `Deine bisher höchste geschaffte Stufe: ${best}.`)
      : "Noch keine Bestleistung bei diesem Modus – leg los!";
  }
  function openMotReady(mode) {
    motReadyMode = mode;
    els.motReadyTitle.textContent = mode === "speed" ? "Tempo steigt" : mode === "count" ? "Anzahl steigt" : "Beides steigt";
    els.motReadyDesc.textContent = mode === "speed"
      ? "Anzahl der Objekte und Ziele bleibt gleich – sie bewegen sich dafür immer schneller."
      : mode === "count"
      ? "Tempo bleibt gleich – es kommen dafür immer mehr Objekte und irgendwann auch mehr Ziele dazu."
      : "Tempo und Anzahl steigern sich gemeinsam.";
    els.motFixedCountGroup.hidden = mode !== "speed";
    els.motGrowStartGroup.hidden = mode === "speed";
    syncMotStyleUI();
    syncMotColorUI();
    syncMotErrorUI();
    syncMotDifficultyUI();
    syncMotCountsUI();
    syncMotGrowStartUI();
    syncMotBgUI();
    updateMotReadyBestHint();
    showScreen("motReady");
  }
  els.motOpenSpeed.addEventListener("click", () => openMotReady("speed"));
  els.motOpenCount.addEventListener("click", () => openMotReady("count"));
  els.motOpenBoth.addEventListener("click", () => openMotReady("both"));
  els.motReadyBackToHome.addEventListener("click", () => showScreen("natHome"));
  els.motOpenTraining.addEventListener("click", () => {
    syncMotStyleUI();
    syncMotColorUI();
    syncMotTrainingUI();
    syncMotBgUI();
    showScreen("motTrainingReady");
  });
  els.motTrainingBackToHome.addEventListener("click", () => showScreen("natHome"));

  // ---- Round engine ----
  function motEffectiveSpeed() { return motState.speed * Math.pow(MOT_SPEED_STEP_FACTOR, motState.speedStep); }
  // Same timer-wrapping trick as Remember/Blitz/Flash's: records what's
  // pending and when it fires, so Pause can cancel it and Resume can replay
  // it with its exact remaining delay. Only used for the highlight/checking
  // phases' delays - the tracking phase's own continuous animation is paused
  // separately (cancelling/restarting its requestAnimationFrame loop).
  function scheduleMotTimer(fn, delayMs) {
    motState.timerFn = fn;
    motState.timerFiresAt = performance.now() + delayMs;
    motState.timer = setTimeout(fn, delayMs);
  }
  // Rejection-sampling placement (same idea as Remember's overlap avoidance):
  // retry a candidate spot a handful of times if it lands too close to an
  // already-placed object, else just accept it - a rare, brief overlap at
  // high object counts is a much smaller problem than an infinite loop.
  function motPlaceObjects(n, stageW, stageH, radius, topMinY) {
    const objs = [];
    const minDist = radius * MOT_MIN_DIST_FACTOR;
    for (let i = 0; i < n; i++) {
      let x, y, tries = 0;
      do {
        x = radius + Math.random() * Math.max(1, stageW - 2 * radius);
        y = topMinY + Math.random() * Math.max(1, stageH - radius - topMinY);
        tries++;
      } while (tries < 30 && objs.some((o) => Math.hypot(o.x - x, o.y - y) < minDist));
      const angle = Math.random() * Math.PI * 2;
      objs.push({ id: i, x, y, vx: Math.cos(angle), vy: Math.sin(angle) });
    }
    return objs;
  }
  function motMoveObjects(dt) {
    const speedPx = motEffectiveSpeed() * Math.min(motState.stageW, motState.stageH);
    motState.objects.forEach((o) => {
      o.x += o.vx * speedPx * dt;
      o.y += o.vy * speedPx * dt;
      if (o.x < motState.radius) { o.x = motState.radius; o.vx = Math.abs(o.vx); }
      if (o.x > motState.stageW - motState.radius) { o.x = motState.stageW - motState.radius; o.vx = -Math.abs(o.vx); }
      // The whole stage's y=0 sits under the instruction hint/player-bar
      // (see stageTopClearanceY) - objects bounce continuously throughout
      // the tracking phase, not just at initial placement, so the top
      // boundary itself needs to stay below that fixed UI, not just y=0.
      if (o.y < motState.topMinY) { o.y = motState.topMinY; o.vy = Math.abs(o.vy); }
      if (o.y > motState.stageH - motState.radius) { o.y = motState.stageH - motState.radius; o.vy = -Math.abs(o.vy); }
    });
    motSeparateObjects();
  }
  // Positional-only separation (no velocity/bounce change) for any pair of
  // objects that have drifted closer than 2×radius - just enough to stop
  // one from fully hiding behind another. O(n²) but object count tops out
  // at MOT_OBJ_MAX, so this is trivially cheap once per frame.
  function motSeparateObjects() {
    const objs = motState.objects, minDist = motState.radius * MOT_MIN_DIST_FACTOR;
    for (let i = 0; i < objs.length; i++) {
      for (let j = i + 1; j < objs.length; j++) {
        const a = objs[i], b = objs[j];
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.hypot(dx, dy);
        if (dist >= minDist) continue;
        // Coincident centres (vanishingly rare) - nudge apart along a fixed
        // axis rather than dividing by a zero distance.
        const nx = dist > 0.0001 ? dx / dist : 1, ny = dist > 0.0001 ? dy / dist : 0;
        const push = (minDist - dist) / 2;
        a.x -= nx * push; a.y -= ny * push;
        b.x += nx * push; b.y += ny * push;
      }
    }
    objs.forEach((o) => {
      o.x = Math.min(motState.stageW - motState.radius, Math.max(motState.radius, o.x));
      // Must match motMoveObjects()'s own top boundary (topMinY, not just
      // radius) - this second clamp exists only to undo overlap from the
      // pairwise push-apart above, but re-clamping against the plain radius
      // here would silently push an object back past the hint/player-bar
      // clearance whenever separation happens to shove it upward.
      o.y = Math.min(motState.stageH - motState.radius, Math.max(motState.topMinY, o.y));
    });
  }
  // Generalises the fixed-gray "3D-Optik" gradient to whichever colour was
  // rolled for this round - mixHex() (already used for the background
  // Intensität slider) gives a lighter "highlight" spot and a darker
  // "shadow" edge from the same base hex, same glossy-sphere illusion as
  // before but now colour-agnostic.
  function motGradientCss(hex) {
    const light = mixHex(hex, "#ffffff", 0.55), dark = mixHex(hex, "#000000", 0.35);
    return `radial-gradient(circle at 34% 28%, ${light} 0%, ${hex} 55%, ${dark} 100%)`;
  }
  // Same idea as pickPeriphColor(), but the target highlight needs to avoid
  // TWO colours at once - the background AND this round's own object colour
  // (during the highlight phase both are on screen together and must read
  // as clearly different at a glance) - pickPeriphColor() itself only ever
  // avoids one, so this is a small MOT-local variant rather than a change
  // to that shared helper.
  function pickMotColor(colorKeys, avoidHexes, rng) {
    const all = keysToColors(colorKeys && colorKeys.length ? colorKeys : ["gelb"], STROOP_COLOR_LIB);
    const safe = all.filter((c) => !avoidHexes.some((h) => h && colorsClash(c.hex, h)));
    const pool = safe.length ? safe : all;
    return pool[Math.floor(rng() * pool.length)].hex;
  }
  // Full rebuild (creates/removes DOM nodes and sets classes) - called on
  // every phase change. renderMotPositions() below is the cheap per-frame
  // counterpart used during the tracking animation itself.
  function renderMotObjects() {
    els.motObjectsLayer.innerHTML = "";
    motState.objects.forEach((o) => {
      const el = document.createElement("button");
      el.type = "button";
      el.className = "mot-object" + (motState.style === "3d" ? " style-3d" : "");
      el.style.width = el.style.height = motState.radius * 2 + "px";
      el.style.left = o.x - motState.radius + "px";
      el.style.top = o.y - motState.radius + "px";
      const isTarget = motState.phase === "highlight" && motState.targetIds.has(o.id);
      const isCorrect = motState.tapped.has(o.id) && motState.targetIds.has(o.id);
      const isWrong = o.id === motState.wrongId;
      if (isTarget) el.classList.add("target");
      if (isCorrect) el.classList.add("correct");
      if (isWrong) el.classList.add("wrong");
      // Normal objects use the round's chosen object colour, the
      // highlighted target(s) the round's chosen target colour - both
      // configurable and rolled once per round (see the engine header
      // comment). correct/wrong stay fixed semantic colours (CSS classes
      // above): those are pass/fail feedback, not a look the client picks.
      if (isTarget) {
        el.style.background = motState.style === "3d" ? motGradientCss(motState.targetColorHex) : motState.targetColorHex;
      } else if (!isCorrect && !isWrong) {
        el.style.background = motState.style === "3d" ? motGradientCss(motState.baseColorHex) : motState.baseColorHex;
      }
      const tappable = motState.phase === "identify" && !motState.tapped.has(o.id);
      if (tappable) {
        el.classList.add("tappable");
        el.addEventListener("click", () => motTapObject(o.id));
      }
      el.setAttribute("aria-label", `Objekt ${o.id + 1}`);
      o.el = el;
      els.motObjectsLayer.appendChild(el);
    });
  }
  function renderMotPositions() {
    motState.objects.forEach((o) => {
      if (!o.el) return;
      o.el.style.left = o.x - motState.radius + "px";
      o.el.style.top = o.y - motState.radius + "px";
    });
  }
  // Derives this round's object/target count and speed-step from
  // `motState.level` and the active mode - the one place all four modes'
  // progression rules are decided. "count" mode never advances speed;
  // "speed" mode never advances count; "both" advances both from the same
  // level; "training" either stays exactly at its chosen start (progress
  // off) or advances both, same as "both" (progress on).
  function motCountsForRound() {
    if (motState.mode === "speed") return { n: motState.objectCount, k: motState.targetCount, speedStep: motState.level - 1 };
    if (motState.mode === "training" && !motState.trainingProgress) return { n: motState.startObjects, k: motState.startTargets, speedStep: motState.startSpeedStep };
    const n = Math.min(MOT_OBJ_MAX, motState.startObjects + Math.floor((motState.level - 1) / 2));
    const k = Math.min(MOT_TARGET_MAX, n - 2, motState.startTargets + Math.floor((motState.level - 1) / 4));
    const speedStep = motState.mode === "count" ? 0 : (motState.mode === "training" ? motState.startSpeedStep : 0) + motState.level - 1;
    return { n, k, speedStep };
  }
  function motLevelLabel() {
    const { n, k } = motCountsForRound();
    const base = `${n} Objekte · ${k} Ziel${k > 1 ? "e" : ""}`;
    return motState.mode === "count" ? base : `${base} · Tempo-Stufe ${motState.speedStep + 1}`;
  }
  function motStartRound() {
    const { n, k, speedStep } = motCountsForRound();
    motState.speedStep = speedStep;
    // Hint/level text must be set BEFORE measuring stageTopClearanceY() below -
    // motLevelLabel() can be long enough to wrap the player-bar onto two
    // lines (see .player-bar flex-wrap fix), and getBoundingClientRect()
    // only reflects whatever text is in the DOM at the moment it's called.
    // Measuring first (old order) captured the previous round's/short
    // leftover text and produced a topMinY too small for THIS round's
    // actual (possibly wrapped) bar height.
    els.motHint.textContent = k > 1 ? "Merke dir die markierten Objekte" : "Merke dir das markierte Objekt";
    els.motLevelEl.textContent = motLevelLabel();
    const rect = els.motObjectsLayer.getBoundingClientRect();
    motState.stageW = rect.width;
    motState.stageH = rect.height;
    motState.radius = MOT_RADIUS;
    motState.topMinY = Math.max(motState.radius, stageTopClearanceY(rect, els.motHint, els.motPlayerBar, motState.radius, motState.radius));
    motState.objects = motPlaceObjects(n, motState.stageW, motState.stageH, motState.radius, motState.topMinY);
    motState.targetIds = pickRandomSubset(motState.objects.map((o) => o.id), k);
    motState.tapped = new Set();
    motState.wrongId = null;
    motState.phase = "highlight";
    // One colour per ROUND (not per object - see the engine header comment),
    // situationally avoiding the current background colour so the objects
    // never blend into it - same pickPeriphColor()/colorsClash() logic the
    // Zusatzaufgabe add-on and Periph's own stimulus colour already use.
    const bgHex = motPrefs.bgIntensity > 0 ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[motPrefs.bgColorKey].hex, motPrefs.bgIntensity) : "#ffffff";
    motState.baseColorHex = pickPeriphColor(motState.colors, bgHex, Math.random);
    motState.targetColorHex = pickMotColor(motState.targetColors, [bgHex, motState.baseColorHex], Math.random);
    renderMotObjects();
    scheduleMotTimer(motBeginTracking, motState.highlightS * 1000);
  }
  function motBeginTracking() {
    if (!motState) return;
    motState.phase = "tracking";
    els.motHint.textContent = "Mit den Augen verfolgen …";
    motState.trackTotalMs = motState.trackS * 1000;
    motState.trackElapsedMs = 0;
    motState.trackLastTs = null;
    renderMotObjects(); // rebuilds without the "target" highlight class
    motState.raf = requestAnimationFrame(motPhysicsTick);
  }
  function motPhysicsTick(ts) {
    if (!motState || motState.phase !== "tracking") return;
    if (motState.trackLastTs == null) motState.trackLastTs = ts;
    // Clamped so a dropped/backgrounded frame can't fling objects across
    // the stage in one jump once the tab regains focus.
    const dt = Math.min(0.05, (ts - motState.trackLastTs) / 1000);
    motState.trackLastTs = ts;
    motState.trackElapsedMs += dt * 1000;
    motMoveObjects(dt);
    renderMotPositions();
    if (motState.trackElapsedMs >= motState.trackTotalMs) { motOpenIdentify(); return; }
    motState.raf = requestAnimationFrame(motPhysicsTick);
  }
  function motOpenIdentify() {
    if (!motState) return;
    motState.raf = null;
    motState.phase = "identify";
    els.motHint.textContent = motState.targetIds.size > 1 ? "Welche waren es? Tippen." : "Welches war es? Tippen.";
    renderMotObjects();
  }
  function motTapObject(id) {
    if (!motState || motState.phase !== "identify" || motState.paused || motState.tapped.has(id)) return;
    if (motState.targetIds.has(id)) {
      motState.tapped.add(id);
      renderMotObjects();
      if (motState.tapped.size >= motState.targetIds.size) {
        if (motState.level > motState.cleared) motState.cleared = motState.level;
        motState.phase = "success";
        els.motHint.textContent = "Richtig! Weiter geht's …";
        motState.level += 1;
        scheduleMotTimer(motStartRound, 900);
      }
    } else {
      motState.phase = "checking";
      motState.wrongId = id;
      motState.tapped = new Set(motState.targetIds); // reveal every actual target
      renderMotObjects();
      let resetLevel, hint;
      if (motState.errorMode === "stay") { resetLevel = motState.level; hint = "Leider falsch – nochmal versuchen"; }
      else if (motState.errorMode === "backOne") { resetLevel = Math.max(1, motState.level - 1); hint = "Leider falsch – eine Stufe runter"; }
      else { resetLevel = 1; hint = "Leider falsch – nochmal von vorne"; }
      els.motHint.textContent = hint;
      scheduleMotTimer(() => { motState.level = resetLevel; motStartRound(); }, 1400);
    }
  }

  let motState = null;
  let lastMotMode = null;
  let motReturnScreen = "natHome";
  function startMotGame(mode) {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.motPlayer.hidden = false;
    els.motPlayerBar.hidden = false;
    els.motDonePanel.hidden = true;
    els.motPauseOverlay.hidden = true;
    els.motPauseBtn.hidden = false;
    lastMotMode = mode;
    motReturnScreen = mode === "training" ? "motTrainingReady" : "motReady";
    const startObjects = mode === "training" ? motPrefs.trainingObjects : motPrefs.growStartObjects;
    const startTargets = mode === "training" ? motPrefs.trainingTargets : motPrefs.growStartTargets;
    const startSpeedStep = mode === "training" ? motPrefs.trainingSpeedStep : 0;
    motState = {
      mode, level: 1, cleared: 0, phase: "highlight",
      objects: [], targetIds: new Set(), tapped: new Set(), wrongId: null,
      objectCount: motPrefs.objectCount, targetCount: motPrefs.targetCount,
      startObjects, startTargets, startSpeedStep,
      trainingProgress: motPrefs.trainingProgress,
      speed: motPrefs.speed, trackS: motPrefs.trackS, highlightS: motPrefs.highlightS,
      errorMode: motPrefs.errorMode, style: motPrefs.style, colors: motPrefs.colors.slice(), targetColors: motPrefs.targetColors.slice(),
      startTime: performance.now(), timer: null, raf: null, paused: false,
    };
    applyMotBg();
    requestWakeLock();
    motStartRound();
  }
  els.motReadyStartBtn.addEventListener("click", () => startMotGame(motReadyMode));
  els.motTrainingStartBtn.addEventListener("click", () => startMotGame("training"));

  // ---- Pause mid-game, live-adjust the background - same trick as
  // Remember/Blitz/Flash's for the highlight/checking delays; the tracking
  // phase's requestAnimationFrame loop is cancelled outright and restarted
  // fresh on resume (trackElapsedMs already reflects exactly how much
  // tracking time had elapsed, so nothing is lost or double-counted). ----
  function pauseMot() {
    if (!motState || motState.paused) return;
    motState.paused = true;
    motState.pausedAt = performance.now();
    if (motState.raf) { cancelAnimationFrame(motState.raf); motState.raf = null; motState.trackLastTs = null; }
    if (motState.timer) {
      clearTimeout(motState.timer);
      motState.timer = null;
      motState.timerRemainingMs = Math.max(0, motState.timerFiresAt - motState.pausedAt);
    }
    syncMotBgUI();
    els.motPauseBtn.hidden = true;
    els.motPauseOverlay.hidden = false;
  }
  function resumeMot() {
    if (!motState || !motState.paused) return;
    motState.startTime += performance.now() - motState.pausedAt;
    motState.paused = false;
    if (motState.phase === "tracking") motState.raf = requestAnimationFrame(motPhysicsTick);
    if (motState.timerFn && motState.timerRemainingMs != null) {
      scheduleMotTimer(motState.timerFn, motState.timerRemainingMs);
      motState.timerRemainingMs = null;
    }
    els.motPauseOverlay.hidden = true;
    els.motPauseBtn.hidden = false;
  }
  els.motPauseBtn.addEventListener("click", pauseMot);
  els.motResumeBtn.addEventListener("click", resumeMot);

  // "Beenden" doubles as the finish action, same convention as Remember/
  // Blitz/Flash - MOT-Fähigkeit is endless/progressive with no fixed end.
  function motStop() {
    if (!motState) return;
    if (motState.timer) clearTimeout(motState.timer);
    if (motState.raf) cancelAnimationFrame(motState.raf);
    const state = motState;
    motState = null;
    els.motPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.motPlayer) document.exitFullscreen().catch(() => {});
    els.motFsHint.hidden = true;
    if (state.cleared > 0) {
      const isRecord = saveMotBest(state.mode, state.cleared);
      renderMotBests();
      const played = (performance.now() - state.startTime) / 1000;
      const modeTitle = state.mode === "speed" ? "Tempo steigt" : state.mode === "count" ? "Anzahl steigt" : state.mode === "both" ? "Beides steigt" : "Trainingsmodus";
      const note = state.mode === "speed" ? `Tempo-Stufe ${state.cleared + 1} erreicht` : `Stufe ${state.cleared} erreicht`;
      els.motPlayerBar.hidden = true;
      els.motDoneSummary.textContent = `MOT-Fähigkeit · ${modeTitle} · ${note}` + (isRecord ? " · Neue Bestleistung!" : "");
      const id = addHistory({ kind: "mot", title: `MOT-Fähigkeit · ${modeTitle}`, seconds: Math.round(played), note });
      renderRating(els.motRating, id, "Wie war deine Konzentration?");
      els.motDonePanel.hidden = false;
    } else {
      els.motPlayer.hidden = true;
      showScreen(motReturnScreen);
    }
  }
  els.motBackBtn.addEventListener("click", motStop);
  els.motAgainBtn.addEventListener("click", () => { els.motDonePanel.hidden = true; startMotGame(lastMotMode); });
  els.motDoneBackBtn.addEventListener("click", () => { els.motPlayer.hidden = true; els.motDonePanel.hidden = true; showScreen(motReturnScreen); });

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
        els.tabataExerciseNote.textContent = ex.note || "";
        els.tabataExerciseNote.hidden = !ex.note;
        els.tabataExerciseCustomNote.hidden = !note;
        if (note) els.tabataExerciseCustomNote.innerHTML = `<strong>Deine Notiz:</strong> ${esc(note)}`;
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
  wireSwipeNav(els.workoutTabataView, {
    onLeft: () => els.tabataSkipBtn.click(),
    onRight: () => els.tabataPrevBtn.click(),
  });

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
    return sec === "breath" ? "breathHome" : sec === "movement" ? "movementHome" : sec === "workout" ? "workoutHome" : sec === "nat" ? "natHome" : sec === "test" ? "testHome" : "home";
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
        active = { colors: keysToColors(state.colors), arrowColors: keysToColors(state.arrowColors), stroopColors: keysToColors(state.stroopColors, STROOP_COLOR_LIB) };
      startSession();
    } else if (block.domain === "workout") {
      workoutPlan = null;
      runWorkoutBlock(block);
    } else if (block.domain === "nat") {
      startRememberGame(block.mode || "fixed", { comboDurationS: block.duration ?? 60 });
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
  const comboSavedStore = makePresetStore(COMBO_SAVED_KEY);

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
    renderPresetList(comboSavedStore, els.comboSavedList, els.comboSavedGroup, null,
      (e) => `${exerciseCountLabel(e.blocks.length)} · ca. ${fmtMinutes(e.blocks.reduce((s, b) => s + comboBlockSeconds(b), 0))}`,
      (entry) => {
        comboOriginBundle = null;
        startComboProgram({ name: entry.name, blocks: entry.blocks }, "local", "local:" + entry.id, currentHomeScreen());
      });
  }
  function openComboScreen() {
    comboDraftBlocks = [];
    els.comboSaveForm.hidden = true;
    els.comboSaveBtn.hidden = false;
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
  wirePresetSaveForm({
    saveBtn: els.comboSaveBtn, form: els.comboSaveForm, nameInput: els.comboNameInput,
    cancelBtn: els.comboSaveCancelBtn, confirmBtn: els.comboSaveConfirmBtn,
    defaultName: () => `Programm ${new Date().toLocaleDateString("de-DE")}`,
    onSave: (name) => {
      const list = comboSavedStore.load();
      list.push({ id: String(Date.now()), name, blocks: comboDraftBlocks.slice(), createdAt: new Date().toISOString() });
      comboSavedStore.save(list);
      renderComboSaved();
      comboDraftBlocks = [];
      renderComboBlockList();
    },
  });

  // ==== Go/No-Go Reaktionstest (Test-Bereich, first autonomous entry) ====
  // Classic Go/No-Go inhibitory-control paradigm: a series of single
  // stimuli, most demanding a fast "Go" response, a minority demanding the
  // response be WITHHELD ("No-Go"). Research on this task in sport/exercise
  // contexts measures reaction time to Go stimuli plus the false-alarm
  // (commission-error) rate on No-Go trials as the key outcome (see e.g. the
  // 2023 ScienceDirect meta-analysis on inhibitory control in sport
  // performance, and PMC8048576 on go/no-go ISI design) - both are reported
  // here. The classic design keeps the No-Go rate a MINORITY (commonly ~20%,
  // per PMC12650625/PMC8048576-style designs) rather than 50/50, precisely
  // so a prepotent "respond" tendency actually builds up and there is
  // something real to inhibit - a 50/50 split would just be simple choice
  // reaction time, not response inhibition. Distinct from every other Test/
  // NAT exercise: no spatial recall (Remember/Blitz), no sequence memory
  // (Flash), no sustained tracking (MOT) - this is pure speeded go/no-go
  // decision + inhibition, closest to what real game situations demand
  // (react to the real cue, don't react to the decoy).
  const GNG_PREFS_KEY = "fwmc-gng-prefs-v1";
  const GNG_DIFFICULTIES = {
    leicht: { title: "Leicht", stimMs: 600, isiMin: 1000, isiMax: 1600 },
    mittel: { title: "Mittel", stimMs: 450, isiMin: 800, isiMax: 1300 },
    schwer: { title: "Schwer", stimMs: 300, isiMin: 600, isiMax: 1000 },
  };
  const GNG_TRIAL_COUNT = 24;
  const GNG_NOGO_RATIO = 0.2;
  const gngPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadGngPrefs() {
    const saved = readJSON(GNG_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(gngPrefs, saved);
    if (!GNG_DIFFICULTIES[gngPrefs.difficulty]) gngPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[gngPrefs.bgColorKey]) gngPrefs.bgColorKey = "gruen";
    if (typeof gngPrefs.bgIntensity !== "number" || gngPrefs.bgIntensity < 0 || gngPrefs.bgIntensity > 1) gngPrefs.bgIntensity = 0;
  }
  loadGngPrefs();
  function saveGngPrefsToStorage() { writeJSON(GNG_PREFS_KEY, gngPrefs); }

  // Background colour/intensity, added later (client asked every Test-Bereich
  // exercise get the same background customisation NAT's Remember/Blitz/
  // Flash/MOT already have) - see CLAUDE.md Established patterns for the
  // scope decision (no transfer/preset-save here, unlike those four). The
  // tint goes straight on the DOM stage that holds the go/no-go circle, same
  // "no canvas" approach as Remember's own applyRememberBg().
  function applyGngBg() {
    els.gngStage.style.background = gngPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[gngPrefs.bgColorKey].hex, gngPrefs.bgIntensity)
      : "";
  }
  const syncGngBgUI = wireBgIntensityControl(gngPrefs, {
    pickers: [els.gngBgColorPicker, els.gngPauseBgColorPicker],
    sliders: [els.gngBgIntensitySlider, els.gngPauseBgSlider],
    valueEls: [els.gngBgIntensityValue, els.gngPauseBgValue],
    hintEls: [els.gngBgContrastHint],
  }, () => { saveGngPrefsToStorage(); applyGngBg(); });

  const GNG_BEST_KEY = "fwmc-gng-best-v1"; // { [difficulty]: bestAccuracyPct }
  function gngBestFor() { return readJSON(GNG_BEST_KEY, {})[gngPrefs.difficulty] || 0; }
  function saveGngBest(accuracyPct) {
    const all = readJSON(GNG_BEST_KEY, {});
    if (accuracyPct > (all[gngPrefs.difficulty] || 0)) { all[gngPrefs.difficulty] = accuracyPct; writeJSON(GNG_BEST_KEY, all); return true; }
    return false;
  }
  function renderGngBest() {
    const best = gngBestFor();
    const text = best ? `Beste Genauigkeit (${GNG_DIFFICULTIES[gngPrefs.difficulty].title}): ${best}%` : "";
    els.gngBestHint.textContent = text;
    els.gngReadyBestHint.textContent = text;
  }
  function syncGngDifficultyUI() {
    els.gngDifficultyRow.querySelectorAll("[data-gng-diff]").forEach((btn) => setActive(btn, btn.dataset.gngDiff === gngPrefs.difficulty));
  }
  els.gngDifficultyRow.querySelectorAll("[data-gng-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      gngPrefs.difficulty = btn.dataset.gngDiff;
      saveGngPrefsToStorage();
      syncGngDifficultyUI();
      renderGngBest();
    });
  });

  els.gngOpenBtn.addEventListener("click", () => {
    syncGngDifficultyUI();
    syncGngBgUI();
    renderGngBest();
    showScreen("gngReady");
  });
  els.gngReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleBlitzTimer/scheduleRememberTimer:
  // records what's pending and when it fires, so Pause can cancel it and
  // Resume can replay it with its exact remaining delay.
  function scheduleGngTimer(fn, delayMs) {
    gngState.timerFn = fn;
    gngState.timerFiresAt = performance.now() + delayMs;
    gngState.timer = setTimeout(() => { gngState.timer = null; fn(); }, delayMs);
  }

  function buildGngTrials() {
    const n = GNG_TRIAL_COUNT;
    const nogoCount = Math.round(n * GNG_NOGO_RATIO);
    const trials = [];
    for (let i = 0; i < n; i++) trials.push(i < nogoCount ? "nogo" : "go");
    // Shuffle, then avoid two No-Go trials back to back - a run of
    // consecutive No-Go trials would let the client just switch the
    // "respond" impulse off instead of actually having to inhibit it.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true;
      for (let i = 1; i < trials.length; i++) if (trials[i] === "nogo" && trials[i - 1] === "nogo") { ok = false; break; }
      if (ok) break;
    }
    return trials;
  }

  let gngState = null;
  function startGngGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.gngPlayer.hidden = false;
    els.gngPlayerBar.hidden = false;
    els.gngDonePanel.hidden = true;
    els.gngPauseOverlay.hidden = true;
    els.gngPauseBtn.hidden = false;
    gngState = {
      diff: GNG_DIFFICULTIES[gngPrefs.difficulty], trials: buildGngTrials(), index: -1, phase: "gap", responded: false,
      hits: 0, misses: 0, falseAlarms: 0, correctInhibitions: 0, rts: [],
      stimAt: 0, paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    applyGngBg();
    els.gngStimulus.className = "gng-stimulus";
    els.gngHint.textContent = "Bereit? Gleich geht's los …";
    els.gngProgressEl.textContent = `0/${gngState.trials.length}`;
    requestWakeLock();
    scheduleGngTimer(gngNextTrial, 1200);
  }
  els.gngReadyStartBtn.addEventListener("click", startGngGame);

  function gngNextTrial() {
    if (!gngState) return;
    gngState.index++;
    if (gngState.index >= gngState.trials.length) { gngFinish(); return; }
    els.gngProgressEl.textContent = `${gngState.index + 1}/${gngState.trials.length}`;
    gngState.phase = "gap";
    gngState.responded = false;
    els.gngStimulus.className = "gng-stimulus";
    const isi = gngState.diff.isiMin + Math.random() * (gngState.diff.isiMax - gngState.diff.isiMin);
    scheduleGngTimer(gngShowStimulus, isi);
  }
  function gngShowStimulus() {
    if (!gngState) return;
    const kind = gngState.trials[gngState.index];
    gngState.phase = kind; // "go" or "nogo"
    gngState.stimAt = performance.now();
    gngState.responded = false;
    els.gngHint.textContent = "";
    els.gngStimulus.className = "gng-stimulus " + kind;
    scheduleGngTimer(gngEndStimulus, gngState.diff.stimMs);
  }
  function gngEndStimulus() {
    if (!gngState) return;
    if (gngState.phase === "go" && !gngState.responded) { gngState.misses++; els.gngHint.textContent = "Verpasst!"; }
    else if (gngState.phase === "nogo" && !gngState.responded) gngState.correctInhibitions++;
    gngState.phase = "gap";
    els.gngStimulus.className = "gng-stimulus";
    gngNextTrial();
  }
  function gngTap() {
    if (!gngState || gngState.paused || gngState.responded) return;
    if (gngState.phase === "go") {
      gngState.responded = true;
      gngState.hits++;
      gngState.rts.push(performance.now() - gngState.stimAt);
      els.gngStimulus.classList.add("hit");
    } else if (gngState.phase === "nogo") {
      gngState.responded = true;
      gngState.falseAlarms++;
      els.gngStimulus.classList.add("wrong");
      els.gngHint.textContent = "Fehlalarm – das war Rot!";
    }
    // Taps during the "gap" phase (no stimulus shown yet) are ignored -
    // reaction time is measured stimulus-locked, same as the paradigm this
    // is grounded in.
  }
  els.gngStage.addEventListener("click", gngTap);

  // Pause stops/replays the pending timer, same setTimeout trick as
  // Remember/Blitz/Flash/MOT, plus a live background-adjust overlay (added
  // later, see CLAUDE.md - every Test-Bereich exercise now gets the same
  // background colour/intensity control NAT's own exercises have).
  function pauseGng() {
    if (!gngState || gngState.paused) return;
    gngState.paused = true;
    gngState.pausedAt = performance.now();
    if (gngState.timer) {
      clearTimeout(gngState.timer);
      gngState.timer = null;
      gngState.timerRemainingMs = Math.max(0, gngState.timerFiresAt - gngState.pausedAt);
    }
    syncGngBgUI();
    els.gngPauseBtn.hidden = true;
    els.gngPauseOverlay.hidden = false;
  }
  function resumeGng() {
    if (!gngState || !gngState.paused) return;
    const pausedMs = performance.now() - gngState.pausedAt;
    gngState.startTime += pausedMs;
    gngState.stimAt += pausedMs;
    gngState.paused = false;
    if (gngState.timerFn && gngState.timerRemainingMs != null) {
      scheduleGngTimer(gngState.timerFn, gngState.timerRemainingMs);
      gngState.timerRemainingMs = null;
    }
    els.gngPauseOverlay.hidden = true;
    els.gngPauseBtn.hidden = false;
  }
  els.gngPauseBtn.addEventListener("click", pauseGng);
  els.gngResumeBtn.addEventListener("click", resumeGng);

  function finalizeGngRun(state, totalTrials) {
    els.gngPauseOverlay.hidden = true;
    els.gngPlayerBar.hidden = true;
    const correct = state.hits + state.correctInhibitions;
    const accuracyPct = Math.round(100 * correct / totalTrials);
    const avgRt = state.rts.length ? Math.round(state.rts.reduce((a, b) => a + b, 0) / state.rts.length) : null;
    const isRecord = saveGngBest(accuracyPct);
    renderGngBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.gngDoneSummary.textContent =
      `Go/No-Go (${state.diff.title}) · ${accuracyPct}% richtig` +
      (avgRt != null ? ` · Ø Reaktionszeit ${avgRt} ms` : "") +
      ` · ${state.falseAlarms} Fehlalarm${state.falseAlarms === 1 ? "" : "e"}` +
      (isRecord ? " · Neue Bestleistung!" : "");
    const id = addHistory({ kind: "gng", title: "Go/No-Go Reaktionstest", seconds: Math.round(played), note: `${accuracyPct}% richtig${avgRt != null ? `, Ø ${avgRt} ms` : ""}` });
    renderRating(els.gngRating, id, "Wie fokussiert warst du?");
    els.gngDonePanel.hidden = false;
  }
  function gngFinish() {
    if (!gngState) return;
    const state = gngState;
    gngState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.gngPlayer) document.exitFullscreen().catch(() => {});
    els.gngFsHint.hidden = true;
    finalizeGngRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as Remember/
  // Blitz/Flash/MOT - quitting early still shows a summary as long as at
  // least a few trials were actually resolved, otherwise it's not worth a
  // done-panel and just exits like Blitz-Raster does at level 0.
  function gngStop() {
    if (!gngState) return;
    if (gngState.timer) clearTimeout(gngState.timer);
    const state = gngState;
    gngState = null;
    els.gngPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.gngPlayer) document.exitFullscreen().catch(() => {});
    els.gngFsHint.hidden = true;
    const resolved = state.hits + state.misses + state.falseAlarms + state.correctInhibitions;
    if (resolved >= 4) {
      finalizeGngRun(state, resolved);
    } else {
      els.gngPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.gngBackBtn.addEventListener("click", gngStop);
  els.gngAgainBtn.addEventListener("click", () => { els.gngDonePanel.hidden = true; startGngGame(); });
  els.gngDoneBackBtn.addEventListener("click", () => { els.gngPlayer.hidden = true; els.gngDonePanel.hidden = true; showScreen("testHome"); });

  // ==== Test-Bereich: Positions-Gedächtnis (N-Back) ====
  // First exercise added under the autonomous "Test" section (see CLAUDE.md's
  // "Test-Bereich (autonomous, ongoing)"). Grounded in the classic n-back
  // working-memory paradigm (Kirchner 1958) and its adaptive form used for
  // training studies (Jaeggi et al. 2008, PNAS "Improving fluid intelligence
  // with training on working memory"): a single stimulus position appears at
  // a time in a 3×3 grid; the client reports whether the CURRENT position
  // matches the one exactly N steps back. This is a genuinely distinct
  // mechanic from every existing NAT memory exercise - Remember/Blitz-Raster/
  // Flash Speicher Test all show a set/sequence ONCE and then ask for pure
  // recall afterwards, whereas n-back is continuous *updating*: every single
  // trial is simultaneously a probe on the last one and new material to hold
  // for the next. Only the visuospatial half of Jaeggi's DUAL n-back was
  // built (no simultaneous audio letter stream) - a deliberate v1 scope cut,
  // see the roster entry in CLAUDE.md for why.
  // Timing/adaptive parameters taken directly from Jaeggi et al. 2008's own
  // single-modality stream, not guessed: 500ms stimulus, 2500ms ISI (3000ms/
  // trial), a block of 20+N trials, and the exact published adaptive rule -
  // ≤2 errors in a block → N+1, >5 errors → N-1 (floor 1), otherwise N stays.
  // "Bei-Fehler reset2/backOne/stay" does NOT apply here on purpose: that
  // convention is about ONE wrong tap ending a round outright (Remember/
  // Blitz/Flash/MOT), but n-back's own paradigm is judged over a whole block
  // of many trials, not a single mistake - inventing a per-tap fail mode
  // would misrepresent the paradigm being trained. Likewise no background
  // colour/intensity or Zusatzaufgabe (all explicitly optional for a first
  // Test pass, and there is no obvious per-domain colour choice here - the
  // grid itself, not a tinted backdrop, is the whole stimulus).
  const NBACK_STIMULUS_MS = 500;
  const NBACK_ISI_MS = 2500;
  const NBACK_MATCH_PROB = 0.3; // standard target-trial rate in n-back implementations (~20-35%)
  const NBACK_BLOCK_BASE_TRIALS = 20; // block length = 20 + N, per Jaeggi et al. 2008

  const TEST_NBACK_PREFS_KEY = "fwmc-test-nback-prefs-v1";
  const testNbackPrefs = { startLevel: 2, bgColorKey: "gruen", bgIntensity: 0 }; // Jaeggi's own studies start every participant at 2-back
  (function loadTestNbackPrefs() {
    const saved = readJSON(TEST_NBACK_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(testNbackPrefs, saved);
    if (![1, 2, 3].includes(testNbackPrefs.startLevel)) testNbackPrefs.startLevel = 2;
    if (!STROOP_COLOR_BY_KEY[testNbackPrefs.bgColorKey]) testNbackPrefs.bgColorKey = "gruen";
    if (typeof testNbackPrefs.bgIntensity !== "number" || testNbackPrefs.bgIntensity < 0 || testNbackPrefs.bgIntensity > 1) testNbackPrefs.bgIntensity = 0;
  })();
  function saveTestNbackPrefsToStorage() { writeJSON(TEST_NBACK_PREFS_KEY, testNbackPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyTestNbackBg() {
    els.testNbackStage.style.background = testNbackPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[testNbackPrefs.bgColorKey].hex, testNbackPrefs.bgIntensity)
      : "";
  }
  const syncTestNbackBgUI = wireBgIntensityControl(testNbackPrefs, {
    pickers: [els.testNbackBgColorPicker, els.testNbackPauseBgColorPicker],
    sliders: [els.testNbackBgIntensitySlider, els.testNbackPauseBgSlider],
    valueEls: [els.testNbackBgIntensityValue, els.testNbackPauseBgValue],
    hintEls: [els.testNbackBgContrastHint],
  }, () => { saveTestNbackPrefsToStorage(); applyTestNbackBg(); });

  const TEST_NBACK_BEST_KEY = "fwmc-test-nback-best-v1"; // plain number: highest N level ever played to the end of a block
  function testNbackBest() { return readJSON(TEST_NBACK_BEST_KEY, 0); }
  function saveTestNbackBest(level) {
    const cur = testNbackBest();
    if (level > cur) { writeJSON(TEST_NBACK_BEST_KEY, level); return true; }
    return false;
  }
  function renderTestNbackBest() {
    const b = testNbackBest();
    els.testNbackBestHint.textContent = b ? `Bestleistung: Stufe ${b}` : "";
    els.testNbackReadyBestHint.textContent = b
      ? `Deine bisherige Bestleistung: Stufe ${b}.`
      : "Noch keine Bestleistung – leg los!";
  }
  renderTestNbackBest();

  function syncTestNbackStartUI() {
    document.querySelectorAll("#testNbackStartRow [data-nback-start]").forEach((el) => setActive(el, Number(el.dataset.nbackStart) === testNbackPrefs.startLevel));
  }
  document.querySelectorAll("#testNbackStartRow [data-nback-start]").forEach((el) => {
    el.addEventListener("click", () => {
      testNbackPrefs.startLevel = Number(el.dataset.nbackStart);
      saveTestNbackPrefsToStorage();
      syncTestNbackStartUI();
    });
  });
  els.testNbackOpenBtn.addEventListener("click", () => {
    syncTestNbackStartUI();
    syncTestNbackBgUI();
    renderTestNbackBest();
    showScreen("testNbackReady");
  });
  els.testNbackReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // ---- Sequence generation: a match trial reuses the position from exactly
  // N steps back; a non-match trial re-rolls until it genuinely differs from
  // that same target position, so "isMatch" is never accidentally wrong. ----
  function nbackGenerateBlock(n, trialCount) {
    const seq = [];
    for (let i = 0; i < trialCount; i++) {
      const isMatch = i >= n && Math.random() < NBACK_MATCH_PROB;
      let pos;
      if (isMatch) {
        pos = seq[i - n].pos;
      } else {
        do { pos = Math.floor(Math.random() * 9); } while (i >= n && pos === seq[i - n].pos);
      }
      seq.push({ pos, isMatch });
    }
    return seq;
  }

  function renderTestNbackGrid() {
    const state = testNbackState;
    els.testNbackGrid.innerHTML = "";
    const litPos = state && state.phase === "show" && state.trialIndex >= 0 ? state.seq[state.trialIndex].pos : -1;
    for (let i = 0; i < 9; i++) {
      const el = document.createElement("div");
      el.className = "nback-cell" + (i === litPos ? " lit" : "");
      els.testNbackGrid.appendChild(el);
    }
  }

  function scheduleNbackTimer(fn, delayMs) {
    testNbackState.timerFn = fn;
    testNbackState.timerFiresAt = performance.now() + delayMs;
    testNbackState.timer = setTimeout(fn, delayMs);
  }

  function flashNbackMatchBtn(cls) {
    els.testNbackMatchBtn.classList.remove("correct", "wrong");
    void els.testNbackMatchBtn.offsetWidth; // restart the transition if the same class was just applied
    els.testNbackMatchBtn.classList.add(cls);
    setTimeout(() => { if (els.testNbackMatchBtn) els.testNbackMatchBtn.classList.remove(cls); }, 350);
  }

  function testNbackUpdateStatus() {
    const state = testNbackState;
    els.testNbackLevelEl.textContent = `Stufe ${state.level} · ${state.trialIndex + 1}/${state.seq.length}`;
  }

  function testNbackNextTrial() {
    const state = testNbackState;
    state.trialIndex++;
    if (state.trialIndex >= state.seq.length) { testNbackFinishBlock(); return; }
    state.responded = false;
    state.phase = "show";
    renderTestNbackGrid();
    testNbackUpdateStatus();
    els.testNbackHint.textContent = state.trialIndex < state.level ? "Merken …" : "Übereinstimmung mit vorhin?";
    scheduleNbackTimer(testNbackHideStimulus, NBACK_STIMULUS_MS);
  }
  function testNbackHideStimulus() {
    testNbackState.phase = "gap";
    renderTestNbackGrid();
    scheduleNbackTimer(testNbackEndTrial, NBACK_ISI_MS);
  }
  function testNbackEndTrial() {
    const state = testNbackState;
    const trial = state.seq[state.trialIndex];
    const correct = trial.isMatch === state.responded;
    if (!correct) state.errors++;
    flashNbackMatchBtn(correct ? "correct" : "wrong");
    testNbackNextTrial();
  }
  function testNbackTapMatch() {
    const state = testNbackState;
    if (!state || state.paused || state.responded) return;
    if (state.phase !== "show" && state.phase !== "gap") return;
    state.responded = true;
  }
  els.testNbackMatchBtn.addEventListener("click", testNbackTapMatch);

  function testNbackStartBlock() {
    const state = testNbackState;
    state.seq = nbackGenerateBlock(state.level, NBACK_BLOCK_BASE_TRIALS + state.level);
    state.trialIndex = -1;
    state.errors = 0;
    testNbackNextTrial();
  }
  // Adaptive rule per Jaeggi et al. 2008: ≤2 errors in the block → harder;
  // >5 errors → easier; otherwise the level carries over unchanged.
  function testNbackFinishBlock() {
    const state = testNbackState;
    state.cleared = Math.max(state.cleared, state.level);
    const delta = state.errors <= 2 ? 1 : state.errors > 5 ? -1 : 0;
    const newLevel = Math.max(1, state.level + delta);
    const changeLabel = delta > 0 ? "Stufe steigt" : delta < 0 ? "Stufe sinkt" : "Stufe bleibt gleich";
    els.testNbackHint.textContent = `Block beendet · ${state.errors} Fehler · ${changeLabel} auf ${newLevel}`;
    state.phase = "betweenBlocks";
    renderTestNbackGrid();
    state.level = newLevel;
    state.blockIndex++;
    scheduleNbackTimer(testNbackStartBlock, 1800);
  }

  let testNbackState = null;
  function startTestNbackGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.testNbackPlayer.hidden = false;
    els.testNbackPlayerBar.hidden = false;
    els.testNbackDonePanel.hidden = true;
    els.testNbackPauseOverlay.hidden = true;
    els.testNbackPauseBtn.hidden = false;
    testNbackState = {
      level: testNbackPrefs.startLevel, cleared: 0, blockIndex: 0, seq: [], trialIndex: -1,
      phase: "idle", responded: false, errors: 0, timer: null, timerFn: null, timerFiresAt: null,
      timerRemainingMs: null, paused: false, startTime: performance.now(),
    };
    applyTestNbackBg();
    requestWakeLock();
    testNbackStartBlock();
  }
  els.testNbackReadyStartBtn.addEventListener("click", startTestNbackGame);

  // ---- Pause: cancel/replay the pending timer, same setTimeout trick as
  // Remember/Blitz/Flash/MOT, plus a live background-adjust overlay (added
  // later, see CLAUDE.md Established patterns). ----
  function pauseTestNback() {
    if (!testNbackState || testNbackState.paused) return;
    testNbackState.paused = true;
    testNbackState.pausedAt = performance.now();
    if (testNbackState.timer) {
      clearTimeout(testNbackState.timer);
      testNbackState.timer = null;
      testNbackState.timerRemainingMs = Math.max(0, testNbackState.timerFiresAt - testNbackState.pausedAt);
    }
    syncTestNbackBgUI();
    els.testNbackPauseBtn.hidden = true;
    els.testNbackPauseOverlay.hidden = false;
  }
  function resumeTestNback() {
    if (!testNbackState || !testNbackState.paused) return;
    testNbackState.startTime += performance.now() - testNbackState.pausedAt;
    testNbackState.paused = false;
    if (testNbackState.timerFn && testNbackState.timerRemainingMs != null) {
      scheduleNbackTimer(testNbackState.timerFn, testNbackState.timerRemainingMs);
      testNbackState.timerRemainingMs = null;
    }
    els.testNbackPauseOverlay.hidden = true;
    els.testNbackPauseBtn.hidden = false;
  }
  els.testNbackPauseBtn.addEventListener("click", pauseTestNback);
  els.testNbackResumeBtn.addEventListener("click", resumeTestNback);

  // "Beenden" doubles as the finish action, same convention as every other
  // NAT/Test memory exercise - n-back is endless/progressive with no fixed end.
  function testNbackStop() {
    if (!testNbackState) return;
    if (testNbackState.timer) clearTimeout(testNbackState.timer);
    const state = testNbackState;
    testNbackState = null;
    els.testNbackPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.testNbackPlayer) document.exitFullscreen().catch(() => {});
    els.testNbackFsHint.hidden = true;
    if (state.cleared > 0) {
      const isRecord = saveTestNbackBest(state.cleared);
      renderTestNbackBest();
      const played = (performance.now() - state.startTime) / 1000;
      els.testNbackPlayerBar.hidden = true;
      els.testNbackDoneSummary.textContent = `Positions-Gedächtnis (N-Back) · Stufe ${state.cleared} erreicht` + (isRecord ? " · Neue Bestleistung!" : "");
      const id = addHistory({ kind: "test-nback", title: "Positions-Gedächtnis (N-Back)", seconds: Math.round(played), note: `Stufe ${state.cleared} erreicht` });
      renderRating(els.testNbackRating, id, "Wie war deine Konzentration?");
      els.testNbackDonePanel.hidden = false;
    } else {
      els.testNbackPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.testNbackBackBtn.addEventListener("click", testNbackStop);
  els.testNbackAgainBtn.addEventListener("click", () => { els.testNbackDonePanel.hidden = true; startTestNbackGame(); });
  els.testNbackDoneBackBtn.addEventListener("click", () => { els.testNbackPlayer.hidden = true; els.testNbackDonePanel.hidden = true; showScreen("testHome"); });

  // ==== Test-Bereich: Verbindungstest (Trail Making) ====
  // Third exercise added under the autonomous "Test" section. Grounded in the
  // Trail Making Test (Reitan 1958; part of the Halstead-Reitan
  // Neuropsychological Battery) - one of the most widely used measures of
  // visual scanning, sustained attention and processing speed, with Part B
  // adding a cognitive-flexibility/set-shifting demand via alternating
  // number/letter sequencing. The standard paper test uses 25 circles per
  // part (Part A: 1-25; Part B: numbers 1-13 + letters A-L, alternating),
  // scored primarily by completion time in seconds; it is also a standard
  // component of sports concussion baseline/return-to-play batteries
  // (tracking processing-speed recovery over time) - a direct fit for this
  // app's sport-mental-coaching context. This version keeps the real scoring
  // (time + error count, no artificial "level") and the real error handling
  // (a wrong tap doesn't advance or reset anything - exactly like an
  // examiner redirecting a participant back to the last correct circle
  // without stopping the clock), but randomises the circle layout fresh
  // every run (the paper test uses one fixed printed sheet per part) so
  // repeat play trains genuine visual search rather than layout
  // memorisation. "Bei-Fehler reset2/backOne/stay" does not apply - same
  // reasoning as Go/No-Go: there is no "level" to reset, a mistake here is
  // simply counted while the client keeps aiming for the same next target.
  // No background colour/Zusatzaufgabe/Trainingsmodus - all explicitly
  // optional, and none add anything to a task whose stimulus IS the
  // scattered layout itself.
  const TRAIL_TEILE = {
    a: { title: "Teil A", instruction: "Tippe die Zahlen in aufsteigender Reihenfolge an: 1, 2, 3 …" },
    b: { title: "Teil B", instruction: "Tippe abwechselnd Zahl und Buchstabe in aufsteigender Reihenfolge an: 1, A, 2, B …" },
  };
  const TRAIL_DIFFICULTIES = {
    leicht: { title: "Leicht", count: 15 },
    mittel: { title: "Mittel", count: 20 },
    schwer: { title: "Schwer", count: 25 }, // matches the original TMT's own 25-item sheet
  };
  const TRAIL_LETTERS = "ABCDEFGHIJKLM";
  const TRAIL_PREFS_KEY = "fwmc-trail-prefs-v1";
  const trailPrefs = { teil: "a", difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  (function loadTrailPrefs() {
    const saved = readJSON(TRAIL_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(trailPrefs, saved);
    if (!TRAIL_TEILE[trailPrefs.teil]) trailPrefs.teil = "a";
    if (!TRAIL_DIFFICULTIES[trailPrefs.difficulty]) trailPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[trailPrefs.bgColorKey]) trailPrefs.bgColorKey = "gruen";
    if (typeof trailPrefs.bgIntensity !== "number" || trailPrefs.bgIntensity < 0 || trailPrefs.bgIntensity > 1) trailPrefs.bgIntensity = 0;
  })();
  function saveTrailPrefsToStorage() { writeJSON(TRAIL_PREFS_KEY, trailPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  // The tint goes on the same #trailStage the scattered markers/SVG lines
  // sit on top of.
  function applyTrailBg() {
    els.trailStage.style.background = trailPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[trailPrefs.bgColorKey].hex, trailPrefs.bgIntensity)
      : "";
  }
  const syncTrailBgUI = wireBgIntensityControl(trailPrefs, {
    pickers: [els.trailBgColorPicker, els.trailPauseBgColorPicker],
    sliders: [els.trailBgIntensitySlider, els.trailPauseBgSlider],
    valueEls: [els.trailBgIntensityValue, els.trailPauseBgValue],
    hintEls: [els.trailBgContrastHint],
  }, () => { saveTrailPrefsToStorage(); applyTrailBg(); });

  // Best time is kept per Teil+Schwierigkeit combo (lower = better), and only
  // ever recorded for a FULLY completed run - a partial run has no
  // comparable "time", same reasoning as Blitz-Raster only ever counting a
  // reached level.
  const TRAIL_BEST_KEY = "fwmc-trail-best-v1"; // { "a-leicht": seconds, "b-schwer": seconds, ... }
  function trailBestFor() { return readJSON(TRAIL_BEST_KEY, {})[`${trailPrefs.teil}-${trailPrefs.difficulty}`]; }
  function saveTrailBest(seconds) {
    const key = `${trailPrefs.teil}-${trailPrefs.difficulty}`;
    const all = readJSON(TRAIL_BEST_KEY, {});
    if (all[key] == null || seconds < all[key]) { all[key] = seconds; writeJSON(TRAIL_BEST_KEY, all); return true; }
    return false;
  }
  function fmtTrailSeconds(s) { return s.toFixed(1).replace(".", ",") + "s"; }
  function renderTrailBest() {
    const best = trailBestFor();
    const text = best != null ? `Bestzeit (${TRAIL_TEILE[trailPrefs.teil].title}, ${TRAIL_DIFFICULTIES[trailPrefs.difficulty].title}): ${fmtTrailSeconds(best)}` : "";
    els.trailBestHint.textContent = text;
    els.trailReadyBestHint.textContent = text;
  }
  function syncTrailReadyUI() {
    els.trailTeilRow.querySelectorAll("[data-trail-teil]").forEach((btn) => setActive(btn, btn.dataset.trailTeil === trailPrefs.teil));
    els.trailDifficultyRow.querySelectorAll("[data-trail-diff]").forEach((btn) => setActive(btn, btn.dataset.trailDiff === trailPrefs.difficulty));
  }
  els.trailTeilRow.querySelectorAll("[data-trail-teil]").forEach((btn) => {
    btn.addEventListener("click", () => {
      trailPrefs.teil = btn.dataset.trailTeil;
      saveTrailPrefsToStorage();
      syncTrailReadyUI();
      renderTrailBest();
    });
  });
  els.trailDifficultyRow.querySelectorAll("[data-trail-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      trailPrefs.difficulty = btn.dataset.trailDiff;
      saveTrailPrefsToStorage();
      syncTrailReadyUI();
      renderTrailBest();
    });
  });
  els.trailOpenBtn.addEventListener("click", () => {
    syncTrailReadyUI();
    syncTrailBgUI();
    renderTrailBest();
    showScreen("trailReady");
  });
  els.trailReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // ---- Sequence + scatter layout ----
  function buildTrailSequence(teil, n) {
    const seq = [];
    if (teil === "a") {
      for (let i = 1; i <= n; i++) seq.push(String(i));
    } else {
      let num = 1, letIdx = 0;
      for (let i = 0; i < n; i++) {
        if (i % 2 === 0) { seq.push(String(num)); num++; }
        else { seq.push(TRAIL_LETTERS[letIdx % TRAIL_LETTERS.length]); letIdx++; }
      }
    }
    return seq;
  }
  // Anti-overlap scatter placement: the same rejection-sampling-then-grid-
  // fallback approach as Remember's own buildRememberPositions/
  // randomRememberPixelPosition, copy-adapted with Trail Making's own marker
  // size rather than shared - per this app's established "copy-adapt when
  // the engine differs" convention (see Blitz-Raster/Flash Speicher Test in
  // CLAUDE.md). Trail also has no fixed/shuffle "keep" concept to share
  // either way - every run is a fresh random layout by design (see note
  // above on why, unlike the paper test's one fixed printed sheet).
  const TRAIL_MARKER_PX = 54;
  const TRAIL_MIN_CENTER_PX = TRAIL_MARKER_PX + 12;
  function trailStageBounds() {
    const rect = els.trailStage.getBoundingClientRect();
    const w = rect.width || 390, h = rect.height || 600;
    const half = TRAIL_MARKER_PX / 2;
    const minY = stageTopClearanceY(rect, els.trailHint, els.trailPlayerBar, 92, half);
    return { w, h, minX: half + 8, maxX: Math.max(half + 8, w - half - 8), minY, maxY: Math.max(minY, h - 16) };
  }
  function trailRandomPixelPosition(existingPx, bounds) {
    for (let attempt = 0; attempt < 300; attempt++) {
      const x = bounds.minX + Math.random() * (bounds.maxX - bounds.minX);
      const y = bounds.minY + Math.random() * (bounds.maxY - bounds.minY);
      if (!existingPx.some((p) => Math.hypot(p.x - x, p.y - y) < TRAIL_MIN_CENTER_PX)) return { x, y };
    }
    let best = null, bestDist = -1;
    const STEPS = 24;
    for (let gx = 0; gx <= STEPS; gx++) {
      for (let gy = 0; gy <= STEPS; gy++) {
        const x = bounds.minX + (gx / STEPS) * (bounds.maxX - bounds.minX);
        const y = bounds.minY + (gy / STEPS) * (bounds.maxY - bounds.minY);
        const dist = existingPx.length ? Math.min(...existingPx.map((p) => Math.hypot(p.x - x, p.y - y))) : Infinity;
        if (dist > bestDist) { bestDist = dist; best = { x, y }; }
      }
    }
    return best;
  }
  function buildTrailLayout(labels) {
    const bounds = trailStageBounds();
    const existingPx = [];
    return labels.map((label, i) => {
      const px = trailRandomPixelPosition(existingPx, bounds);
      existingPx.push(px);
      return { label, seqIndex: i, x: (px.x / bounds.w) * 100, y: (px.y / bounds.h) * 100 };
    });
  }

  function renderTrailMarkers() {
    els.trailMarkersLayer.innerHTML = "";
    trailState.layout.forEach((m) => {
      const el = document.createElement("button");
      el.className = "trail-marker";
      el.style.left = m.x + "%";
      el.style.top = m.y + "%";
      el.textContent = m.label;
      el.dataset.seqIndex = m.seqIndex;
      el.addEventListener("click", () => trailTapMarker(m.seqIndex, el));
      els.trailMarkersLayer.appendChild(el);
    });
  }

  function trailMarkerCenterPx(el) {
    const mRect = el.getBoundingClientRect();
    const sRect = els.trailStage.getBoundingClientRect();
    return { x: mRect.left + mRect.width / 2 - sRect.left, y: mRect.top + mRect.height / 2 - sRect.top };
  }

  function trailTapMarker(seqIndex, el) {
    if (!trailState || trailState.paused || trailState.finished || el.classList.contains("done")) return;
    if (seqIndex === trailState.currentIndex) {
      el.classList.add("done");
      const px = trailMarkerCenterPx(el);
      if (trailState.tappedPx.length) {
        const prev = trailState.tappedPx[trailState.tappedPx.length - 1];
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", prev.x); line.setAttribute("y1", prev.y);
        line.setAttribute("x2", px.x); line.setAttribute("y2", px.y);
        line.setAttribute("class", "trail-line");
        els.trailLinesSvg.appendChild(line);
      }
      trailState.tappedPx.push(px);
      trailState.currentIndex++;
      updateTrailProgress();
      if (trailState.currentIndex >= trailState.layout.length) trailFinish();
    } else {
      trailState.errors++;
      el.classList.add("wrong");
      setTimeout(() => el.classList.remove("wrong"), 220);
    }
  }

  function updateTrailProgress() {
    if (!trailState) return;
    const elapsed = (performance.now() - trailState.startTime) / 1000;
    els.trailProgressEl.textContent = `${trailState.currentIndex}/${trailState.layout.length} · ${fmtTrailSeconds(elapsed)}`;
  }

  let trailState = null;
  let trailTickInterval = null;
  function startTrailGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.trailPlayer.hidden = false;
    els.trailPlayerBar.hidden = false;
    els.trailDonePanel.hidden = true;
    els.trailPauseOverlay.hidden = true;
    els.trailPauseBtn.hidden = false;
    els.trailLinesSvg.innerHTML = "";
    const diff = TRAIL_DIFFICULTIES[trailPrefs.difficulty];
    const labels = buildTrailSequence(trailPrefs.teil, diff.count);
    trailState = {
      teil: trailPrefs.teil, diff, layout: [], currentIndex: 0, errors: 0, tappedPx: [],
      paused: false, finished: false, startTime: performance.now(),
    };
    applyTrailBg();
    els.trailHint.textContent = TRAIL_TEILE[trailPrefs.teil].instruction;
    requestAnimationFrame(() => {
      // Read the stage's real rect only once it's actually visible (same
      // "no rAF wait needed once unhidden" trick fitCanvas()/MOT's own
      // placement rely on) so the SVG viewBox and scattered layout match the
      // real on-screen stage size, not a stale/zero one from while hidden.
      if (!trailState) return;
      const bounds = trailStageBounds();
      els.trailLinesSvg.setAttribute("viewBox", `0 0 ${bounds.w} ${bounds.h}`);
      trailState.layout = buildTrailLayout(labels);
      renderTrailMarkers();
      updateTrailProgress();
    });
    requestWakeLock();
    if (trailTickInterval) clearInterval(trailTickInterval);
    trailTickInterval = setInterval(() => { if (trailState && !trailState.paused && !trailState.finished) updateTrailProgress(); }, 150);
  }
  els.trailReadyStartBtn.addEventListener("click", startTrailGame);

  // Pause just freezes the elapsed-time display - unlike Remember/Blitz/
  // Flash/N-Back/MOT there is no discrete scheduled setTimeout transition to
  // cancel/replay here (the only "clock" is the continuous progress readout),
  // so shifting startTime forward by the paused duration on resume is enough
  // to make the stage genuinely freeze without anything left to reschedule.
  function pauseTrail() {
    if (!trailState || trailState.paused) return;
    trailState.paused = true;
    trailState.pausedAt = performance.now();
    syncTrailBgUI();
    els.trailPauseBtn.hidden = true;
    els.trailPauseOverlay.hidden = false;
  }
  function resumeTrail() {
    if (!trailState || !trailState.paused) return;
    trailState.startTime += performance.now() - trailState.pausedAt;
    trailState.paused = false;
    els.trailPauseOverlay.hidden = true;
    els.trailPauseBtn.hidden = false;
  }
  els.trailPauseBtn.addEventListener("click", pauseTrail);
  els.trailResumeBtn.addEventListener("click", resumeTrail);

  function finalizeTrailRun(state, completed) {
    if (trailTickInterval) { clearInterval(trailTickInterval); trailTickInterval = null; }
    els.trailPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.trailPlayer) document.exitFullscreen().catch(() => {});
    els.trailFsHint.hidden = true;
    if (!completed) { els.trailPlayer.hidden = true; showScreen("testHome"); return; }
    els.trailPlayerBar.hidden = true;
    const seconds = (performance.now() - state.startTime) / 1000;
    const isRecord = saveTrailBest(seconds);
    renderTrailBest();
    els.trailDoneSummary.textContent =
      `Verbindungstest (${TRAIL_TEILE[state.teil].title}, ${state.diff.title}) · ${fmtTrailSeconds(seconds)}` +
      ` · ${state.errors} Fehler` +
      (isRecord ? " · Neue Bestzeit!" : "");
    const id = addHistory({ kind: "trail", title: "Verbindungstest (Trail Making)", seconds: Math.round(seconds), note: `${TRAIL_TEILE[state.teil].title}, ${state.diff.title} · ${state.errors} Fehler` });
    renderRating(els.trailRating, id, "Wie hat sich das visuelle Absuchen angefühlt?");
    els.trailDonePanel.hidden = false;
  }
  function trailFinish() {
    if (!trailState) return;
    trailState.finished = true;
    const state = trailState;
    trailState = null;
    finalizeTrailRun(state, true);
  }
  // "Beenden" mid-run has no meaningful partial "time" to report (unlike
  // Go/No-Go's accuracy%, which stays valid over any number of resolved
  // trials) - a Trail run is only a valid measurement once the whole
  // sequence is complete, so quitting early just exits, same as Blitz-Raster
  // exiting without a done-panel at level 0.
  function trailStop() {
    if (!trailState) return;
    const state = trailState;
    trailState = null;
    finalizeTrailRun(state, false);
  }
  els.trailBackBtn.addEventListener("click", trailStop);
  els.trailAgainBtn.addEventListener("click", () => { els.trailDonePanel.hidden = true; startTrailGame(); });
  els.trailDoneBackBtn.addEventListener("click", () => { els.trailPlayer.hidden = true; els.trailDonePanel.hidden = true; showScreen("testHome"); });

  // ==== Test-Bereich: Ablenkungstest (Flanker) ====
  // Fourth autonomous entry (see CLAUDE.md's "Test-Bereich (autonomous,
  // ongoing)"). Grounded in the Eriksen flanker task (Eriksen & Eriksen,
  // 1974): a central target arrow is flanked by four distractor arrows that
  // either point the same way ("congruent") or the opposite way
  // ("incongruent"). The client must respond to the CENTRE arrow only and
  // ignore the flankers. Incongruent flankers reliably slow reaction time
  // and raise error rate versus congruent ones - the "flanker effect" /
  // interference cost - a well-replicated measure of selective attention
  // and interference control, including in sport-specific research (e.g.
  // collegiate football players showing smaller interference costs than
  // controls in a flanker variant, PMC5811505). This is a genuinely
  // distinct mechanic from every existing Test/NAT exercise: Go/No-Go tests
  // withholding a response to a single stimulus (response inhibition),
  // while Flanker always demands the SAME central response every trial and
  // instead tests filtering out simultaneous conflicting visual
  // information (selective attention / interference control) - a
  // complementary, not overlapping, executive-function facet. The existing
  // VT "4/8 Pfeile" exercises are direction-cue reaction tasks with a
  // single unambiguous arrow, not an interference paradigm, so there is no
  // overlap there either.
  const FLANKER_PREFS_KEY = "fwmc-flanker-prefs-v1";
  // Difficulty controls the response window (arrows stay up until tapped or
  // this elapses - both the "how long you have" AND, mirroring Go/No-Go's
  // stimMs, how long any tap/timeout feedback colour stays visible before
  // the next trial) and the gap between trials, same shape as GNG_DIFFICULTIES.
  const FLANKER_DIFFICULTIES = {
    leicht: { title: "Leicht", responseMs: 2200, isiMin: 900, isiMax: 1400 },
    mittel: { title: "Mittel", responseMs: 1600, isiMin: 700, isiMax: 1100 },
    schwer: { title: "Schwer", responseMs: 1100, isiMin: 500, isiMax: 900 },
  };
  // 32 trials, balanced 16 congruent / 16 incongruent and 16 left / 16
  // right within each - enough per condition for a meaningful congruent-vs-
  // incongruent average RT comparison without turning this into a long test.
  const FLANKER_TRIAL_COUNT = 32;
  const flankerPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadFlankerPrefs() {
    const saved = readJSON(FLANKER_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(flankerPrefs, saved);
    if (!FLANKER_DIFFICULTIES[flankerPrefs.difficulty]) flankerPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[flankerPrefs.bgColorKey]) flankerPrefs.bgColorKey = "gruen";
    if (typeof flankerPrefs.bgIntensity !== "number" || flankerPrefs.bgIntensity < 0 || flankerPrefs.bgIntensity > 1) flankerPrefs.bgIntensity = 0;
  }
  loadFlankerPrefs();
  function saveFlankerPrefsToStorage() { writeJSON(FLANKER_PREFS_KEY, flankerPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyFlankerBg() {
    els.flankerStage.style.background = flankerPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[flankerPrefs.bgColorKey].hex, flankerPrefs.bgIntensity)
      : "";
  }
  const syncFlankerBgUI = wireBgIntensityControl(flankerPrefs, {
    pickers: [els.flankerBgColorPicker, els.flankerPauseBgColorPicker],
    sliders: [els.flankerBgIntensitySlider, els.flankerPauseBgSlider],
    valueEls: [els.flankerBgIntensityValue, els.flankerPauseBgValue],
    hintEls: [els.flankerBgContrastHint],
  }, () => { saveFlankerPrefsToStorage(); applyFlankerBg(); });

  const FLANKER_BEST_KEY = "fwmc-flanker-best-v1"; // { [difficulty]: bestAccuracyPct }
  function flankerBestFor() { return readJSON(FLANKER_BEST_KEY, {})[flankerPrefs.difficulty] || 0; }
  function saveFlankerBest(accuracyPct) {
    const all = readJSON(FLANKER_BEST_KEY, {});
    if (accuracyPct > (all[flankerPrefs.difficulty] || 0)) { all[flankerPrefs.difficulty] = accuracyPct; writeJSON(FLANKER_BEST_KEY, all); return true; }
    return false;
  }
  function renderFlankerBest() {
    const best = flankerBestFor();
    const text = best ? `Beste Genauigkeit (${FLANKER_DIFFICULTIES[flankerPrefs.difficulty].title}): ${best}%` : "";
    els.flankerBestHint.textContent = text;
    els.flankerReadyBestHint.textContent = text;
  }
  function syncFlankerDifficultyUI() {
    els.flankerDifficultyRow.querySelectorAll("[data-flanker-diff]").forEach((btn) => setActive(btn, btn.dataset.flankerDiff === flankerPrefs.difficulty));
  }
  els.flankerDifficultyRow.querySelectorAll("[data-flanker-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      flankerPrefs.difficulty = btn.dataset.flankerDiff;
      saveFlankerPrefsToStorage();
      syncFlankerDifficultyUI();
      renderFlankerBest();
    });
  });

  els.flankerOpenBtn.addEventListener("click", () => {
    syncFlankerDifficultyUI();
    syncFlankerBgUI();
    renderFlankerBest();
    showScreen("flankerReady");
  });
  els.flankerReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleGngTimer/scheduleBlitzTimer: records
  // what's pending and when it fires, so Pause can cancel it and Resume can
  // replay it with its exact remaining delay.
  function scheduleFlankerTimer(fn, delayMs) {
    flankerState.timerFn = fn;
    flankerState.timerFiresAt = performance.now() + delayMs;
    flankerState.timer = setTimeout(() => { flankerState.timer = null; fn(); }, delayMs);
  }

  function buildFlankerTrials() {
    const perGroup = FLANKER_TRIAL_COUNT / 2; // 16 congruent, 16 incongruent
    const trials = [];
    [true, false].forEach((congruent) => {
      for (let i = 0; i < perGroup; i++) trials.push({ congruent, dir: i < perGroup / 2 ? "left" : "right" });
    });
    // Shuffle, then avoid more than 3 identical CORRECT directions back to
    // back - a long run of "the answer is always left" would let a simple
    // "just keep pressing the same button" motor strategy pass undetected,
    // masking the very interference effect this test exists to measure.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < trials.length; i++) {
        if (trials[i].dir === trials[i - 1].dir) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return trials;
  }

  function flankerArrowChar(dir) { return dir === "left" ? "←" : "→"; }
  function flankerClearRow() { els.flankerRow.innerHTML = ""; }
  function flankerRenderTrial(trial) {
    const flankDir = trial.congruent ? trial.dir : (trial.dir === "left" ? "right" : "left");
    const dirs = [flankDir, flankDir, trial.dir, flankDir, flankDir];
    els.flankerRow.innerHTML = dirs.map((d, i) =>
      `<span class="flanker-arrow${i === 2 ? " flanker-target" : ""}">${flankerArrowChar(d)}</span>`
    ).join("");
  }

  let flankerState = null;
  function startFlankerGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.flankerPlayer.hidden = false;
    els.flankerPlayerBar.hidden = false;
    els.flankerDonePanel.hidden = true;
    els.flankerPauseOverlay.hidden = true;
    els.flankerPauseBtn.hidden = false;
    flankerState = {
      diff: FLANKER_DIFFICULTIES[flankerPrefs.difficulty], trials: buildFlankerTrials(), index: -1, phase: "gap", responded: false,
      correct: 0, incorrect: 0, timeouts: 0, rtsCongruent: [], rtsIncongruent: [],
      stimAt: 0, paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    applyFlankerBg();
    flankerClearRow();
    els.flankerLeftBtn.classList.remove("correct", "wrong");
    els.flankerRightBtn.classList.remove("correct", "wrong");
    els.flankerHint.textContent = "Bereit? Gleich geht's los …";
    els.flankerProgressEl.textContent = `0/${flankerState.trials.length}`;
    requestWakeLock();
    scheduleFlankerTimer(flankerNextTrial, 1200);
  }
  els.flankerReadyStartBtn.addEventListener("click", startFlankerGame);

  function flankerNextTrial() {
    if (!flankerState) return;
    flankerState.index++;
    if (flankerState.index >= flankerState.trials.length) { flankerFinish(); return; }
    els.flankerProgressEl.textContent = `${flankerState.index + 1}/${flankerState.trials.length}`;
    flankerState.phase = "gap";
    flankerState.responded = false;
    flankerClearRow();
    const isi = flankerState.diff.isiMin + Math.random() * (flankerState.diff.isiMax - flankerState.diff.isiMin);
    scheduleFlankerTimer(flankerShowStimulus, isi);
  }
  function flankerShowStimulus() {
    if (!flankerState) return;
    const trial = flankerState.trials[flankerState.index];
    flankerState.phase = "responding";
    flankerState.responded = false;
    flankerState.stimAt = performance.now();
    els.flankerHint.textContent = "";
    els.flankerLeftBtn.classList.remove("correct", "wrong");
    els.flankerRightBtn.classList.remove("correct", "wrong");
    flankerRenderTrial(trial);
    scheduleFlankerTimer(flankerEndTrial, flankerState.diff.responseMs);
  }
  function flankerEndTrial() {
    if (!flankerState) return;
    if (flankerState.phase === "responding" && !flankerState.responded) {
      flankerState.incorrect++;
      flankerState.timeouts++;
      els.flankerHint.textContent = "Verpasst!";
    }
    flankerState.phase = "gap";
    flankerClearRow();
    flankerNextTrial();
  }
  function flankerTap(dir) {
    if (!flankerState || flankerState.paused || flankerState.responded) return;
    // Taps before the arrows actually appear are ignored - reaction time is
    // measured stimulus-locked, same convention as Go/No-Go's gngTap.
    if (flankerState.phase !== "responding") return;
    flankerState.responded = true;
    const trial = flankerState.trials[flankerState.index];
    const rt = performance.now() - flankerState.stimAt;
    const correct = dir === trial.dir;
    const btn = dir === "left" ? els.flankerLeftBtn : els.flankerRightBtn;
    btn.classList.add(correct ? "correct" : "wrong");
    if (correct) {
      flankerState.correct++;
      (trial.congruent ? flankerState.rtsCongruent : flankerState.rtsIncongruent).push(rt);
    } else {
      flankerState.incorrect++;
      els.flankerHint.textContent = "Falsche Richtung!";
    }
    // The feedback colour on the tapped button stays up for whatever's left
    // of diff.responseMs (the already-scheduled flankerEndTrial fires the
    // actual transition) - same rhythm as GNG leaving its stimulus's
    // hit/wrong colour up for the rest of stimMs, no separate timer needed.
  }
  els.flankerLeftBtn.addEventListener("click", () => flankerTap("left"));
  els.flankerRightBtn.addEventListener("click", () => flankerTap("right"));

  // Pause stops/replays the pending timer, same setTimeout trick as
  // Remember/Blitz/Flash/MOT, plus a live background-adjust overlay (added
  // later, see CLAUDE.md - every Test-Bereich exercise now gets the same
  // background colour/intensity control NAT's own exercises have).
  function pauseFlanker() {
    if (!flankerState || flankerState.paused) return;
    flankerState.paused = true;
    flankerState.pausedAt = performance.now();
    if (flankerState.timer) {
      clearTimeout(flankerState.timer);
      flankerState.timer = null;
      flankerState.timerRemainingMs = Math.max(0, flankerState.timerFiresAt - flankerState.pausedAt);
    }
    syncFlankerBgUI();
    els.flankerPauseBtn.hidden = true;
    els.flankerPauseOverlay.hidden = false;
  }
  function resumeFlanker() {
    if (!flankerState || !flankerState.paused) return;
    const pausedMs = performance.now() - flankerState.pausedAt;
    flankerState.startTime += pausedMs;
    flankerState.stimAt += pausedMs;
    flankerState.paused = false;
    if (flankerState.timerFn && flankerState.timerRemainingMs != null) {
      scheduleFlankerTimer(flankerState.timerFn, flankerState.timerRemainingMs);
      flankerState.timerRemainingMs = null;
    }
    els.flankerPauseOverlay.hidden = true;
    els.flankerPauseBtn.hidden = false;
  }
  els.flankerPauseBtn.addEventListener("click", pauseFlanker);
  els.flankerResumeBtn.addEventListener("click", resumeFlanker);

  function avgOf(arr) { return arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length) : null; }
  function finalizeFlankerRun(state, totalTrials) {
    els.flankerPauseOverlay.hidden = true;
    els.flankerPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const avgCong = avgOf(state.rtsCongruent);
    const avgIncong = avgOf(state.rtsIncongruent);
    // The "flanker effect" itself: how much slower correct incongruent
    // responses were versus correct congruent ones - the classic
    // interference-cost measure this whole task is built to surface.
    const interference = (avgCong != null && avgIncong != null) ? (avgIncong - avgCong) : null;
    const isRecord = saveFlankerBest(accuracyPct);
    renderFlankerBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.flankerDoneSummary.textContent =
      `Ablenkungstest (${state.diff.title}) · ${accuracyPct}% richtig` +
      (avgCong != null ? ` · Ø kongruent ${avgCong} ms` : "") +
      (avgIncong != null ? ` · Ø inkongruent ${avgIncong} ms` : "") +
      (interference != null ? ` · Interferenz-Kosten ${interference} ms` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` + (interference != null ? `, Interferenz ${interference} ms` : "");
    const id = addHistory({ kind: "flanker", title: "Ablenkungstest (Flanker)", seconds: Math.round(played), note });
    renderRating(els.flankerRating, id, "Wie fokussiert warst du?");
    els.flankerDonePanel.hidden = false;
  }
  function flankerFinish() {
    if (!flankerState) return;
    const state = flankerState;
    flankerState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.flankerPlayer) document.exitFullscreen().catch(() => {});
    els.flankerFsHint.hidden = true;
    finalizeFlankerRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as Go/No-Go/
  // Remember/Blitz/Flash/MOT - quitting early still shows a summary as long
  // as at least a few trials were actually resolved.
  function flankerStop() {
    if (!flankerState) return;
    if (flankerState.timer) clearTimeout(flankerState.timer);
    const state = flankerState;
    flankerState = null;
    els.flankerPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.flankerPlayer) document.exitFullscreen().catch(() => {});
    els.flankerFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= 4) {
      finalizeFlankerRun(state, resolved);
    } else {
      els.flankerPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.flankerBackBtn.addEventListener("click", flankerStop);
  els.flankerAgainBtn.addEventListener("click", () => { els.flankerDonePanel.hidden = true; startFlankerGame(); });
  els.flankerDoneBackBtn.addEventListener("click", () => { els.flankerPlayer.hidden = true; els.flankerDonePanel.hidden = true; showScreen("testHome"); });

  // ==== Test-Bereich: Blickfeld-Test (UFOV) ====
  // Fifth autonomous entry (see CLAUDE.md's "Test-Bereich (autonomous,
  // ongoing)"). Grounded in the Useful Field of View test (Ball & Owsley,
  // 1987/1993): a measure of visual processing speed AND divided attention
  // - how much information can be taken in from a cluttered display in one
  // brief glance, without moving the eyes. The real protocol runs three
  // subtests of rising demand (central discrimination only; central +
  // peripheral localization; the same plus distractors); this is a single,
  // simplified subtest combining the divided-attention and
  // selective-attention ideas (a central shape AND a peripheral target
  // among distractors, every trial), not a clinical replica - framed
  // "UFOV-inspired" in the client-facing copy for that reason. Central
  // task: identify which of two shapes flashed at fixation (circle/
  // square, standing in for the original car/truck discrimination).
  // Peripheral task, simultaneously: locate which of 8 positions around a
  // ring held a diamond target among plain dot distractors. Both are
  // followed by a pattern mask (standard in the real protocol, to wipe out
  // any lingering afterimage/iconic memory so the score reflects genuine
  // processing speed, not a longer look than the nominal exposure gave).
  // The exposure duration is the dependent variable, adapted trial-by-trial
  // via a 3-down/1-up staircase (three consecutive fully-correct trials
  // shorten it, any error lengthens it) - the same staircase shape the real
  // UFOV protocol itself uses to estimate a threshold. Real UFOV steps in
  // single 60Hz frames (16.67ms, 16.67-500ms range); this uses 33ms
  // (2-frame) steps and an equal floor instead, since setTimeout-driven
  // browser timing can't reliably resolve single-frame differences the way
  // calibrated lab hardware can - see the Offene Fragen note on this.
  // Genuinely distinct from every existing Test/NAT mechanic: Periphere
  // Wahrnehmung trains detecting/naming a single peripheral flash with no
  // central task, no masking and no adaptive threshold; this is a DIVIDED-
  // attention dual task (a central AND a peripheral judgement on every
  // trial) that reports a processing-speed threshold in ms, closer in
  // spirit to N-Back's "adaptive test with no client-set level" shape than
  // to Periph's client-configurable one. Sport-vision relevance: UFOV
  // performance has been linked to driving safety and, in several more
  // recent studies, to athletic expertise (e.g. table-tennis players and
  // action-video-game players showing UFOV advantages over untrained
  // controls) - a good fit for FWMC's peripheral-vision/visual-processing-
  // speed focus.
  const UFOV_PREFS_KEY = "fwmc-ufov-prefs-v1";
  const UFOV_LENGTHS = {
    kurz: { title: "Kurz", trials: 20 },
    mittel: { title: "Mittel", trials: 30 },
    lang: { title: "Lang", trials: 40 },
  };
  const ufovPrefs = { length: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadUfovPrefs() {
    const saved = readJSON(UFOV_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(ufovPrefs, saved);
    if (!UFOV_LENGTHS[ufovPrefs.length]) ufovPrefs.length = "mittel";
    if (!STROOP_COLOR_BY_KEY[ufovPrefs.bgColorKey]) ufovPrefs.bgColorKey = "gruen";
    if (typeof ufovPrefs.bgIntensity !== "number" || ufovPrefs.bgIntensity < 0 || ufovPrefs.bgIntensity > 1) ufovPrefs.bgIntensity = 0;
  }
  loadUfovPrefs();
  function saveUfovPrefsToStorage() { writeJSON(UFOV_PREFS_KEY, ufovPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyUfovBg() {
    els.ufovStage.style.background = ufovPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[ufovPrefs.bgColorKey].hex, ufovPrefs.bgIntensity)
      : "";
  }
  const syncUfovBgUI = wireBgIntensityControl(ufovPrefs, {
    pickers: [els.ufovBgColorPicker, els.ufovPauseBgColorPicker],
    sliders: [els.ufovBgIntensitySlider, els.ufovPauseBgSlider],
    valueEls: [els.ufovBgIntensityValue, els.ufovPauseBgValue],
    hintEls: [els.ufovBgContrastHint],
  }, () => { saveUfovPrefsToStorage(); applyUfovBg(); });

  // Best is keyed by length, LOWER is better here (a shorter exposure the
  // client could still solve) - the opposite direction from Go/No-Go's or
  // Flanker's best-accuracy%, so it gets its own comparison, not a copy of
  // saveFlankerBest/saveGngBest's ">" check.
  const UFOV_BEST_KEY = "fwmc-ufov-best-v1"; // { [length]: bestThresholdMs }
  function ufovBestFor() {
    const v = readJSON(UFOV_BEST_KEY, {})[ufovPrefs.length];
    return typeof v === "number" ? v : null;
  }
  function saveUfovBest(thresholdMs) {
    const all = readJSON(UFOV_BEST_KEY, {});
    const cur = all[ufovPrefs.length];
    if (cur == null || thresholdMs < cur) { all[ufovPrefs.length] = thresholdMs; writeJSON(UFOV_BEST_KEY, all); return true; }
    return false;
  }
  function renderUfovBest() {
    const best = ufovBestFor();
    const text = best != null ? `Beste Schwelle (${UFOV_LENGTHS[ufovPrefs.length].title}): ${Math.round(best)} ms` : "";
    els.ufovBestHint.textContent = text;
    els.ufovReadyBestHint.textContent = text;
  }
  renderUfovBest();
  function syncUfovLengthUI() {
    els.ufovLengthRow.querySelectorAll("[data-ufov-length]").forEach((btn) => setActive(btn, btn.dataset.ufovLength === ufovPrefs.length));
  }
  els.ufovLengthRow.querySelectorAll("[data-ufov-length]").forEach((btn) => {
    btn.addEventListener("click", () => {
      ufovPrefs.length = btn.dataset.ufovLength;
      saveUfovPrefsToStorage();
      syncUfovLengthUI();
      renderUfovBest();
    });
  });

  els.ufovOpenBtn.addEventListener("click", () => {
    syncUfovLengthUI();
    syncUfovBgUI();
    renderUfovBest();
    showScreen("ufovReady");
  });
  els.ufovReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleFlankerTimer/scheduleGngTimer:
  // records what's pending and when it fires, so Pause can cancel it and
  // Resume can replay it with its exact remaining delay. Only the
  // fixation/stim/mask/feedback phases use this - the two response phases
  // wait on a tap instead, with nothing to cancel/replay.
  function scheduleUfovTimer(fn, delayMs) {
    ufovState.timerFn = fn;
    ufovState.timerFiresAt = performance.now() + delayMs;
    ufovState.timer = setTimeout(() => { ufovState.timer = null; fn(); }, delayMs);
  }

  const UFOV_POS_COUNT = 8;
  const UFOV_FIXATION_MS = 500;
  const UFOV_MASK_MS = 400;
  const UFOV_FEEDBACK_MS = 550;
  const UFOV_START_MS = 500; // easiest first, same "start easy" spirit as Blitz/Flash/MOT's progression modes
  const UFOV_MIN_MS = 33;
  const UFOV_MAX_MS = 500;
  const UFOV_STEP_MS = 33;
  const UFOV_STAIRCASE_HITS_NEEDED = 3; // 3-down/1-up, matching Ball & Owsley's own UFOV staircase
  const UFOV_SCORE_TRIALS = 10; // reported threshold = average duration of the last N trials, once the staircase has had time to settle

  function ufovRingEl(i) { return els["ufovRing" + i]; }
  function ufovSetCenter(stateClass) {
    els.ufovCenterEl.className = "ufov-center" + (stateClass ? " " + stateClass : "");
  }
  const UFOV_POS_CLASSES = ["ufov-p-n", "ufov-p-ne", "ufov-p-e", "ufov-p-se", "ufov-p-s", "ufov-p-sw", "ufov-p-w", "ufov-p-nw"];
  function ufovSetRing(i, stateClass) {
    ufovRingEl(i).className = "ufov-ring-pos " + UFOV_POS_CLASSES[i] + (stateClass ? " " + stateClass : "");
  }
  function ufovClearField() {
    ufovSetCenter(null);
    for (let i = 0; i < UFOV_POS_COUNT; i++) ufovSetRing(i, null);
  }

  let ufovState = null;
  function startUfovGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.ufovPlayer.hidden = false;
    els.ufovPlayerBar.hidden = false;
    els.ufovDonePanel.hidden = true;
    els.ufovPauseOverlay.hidden = true;
    els.ufovPauseBtn.hidden = false;
    els.ufovShapeBtns.hidden = true;
    els.ufovRingBtns.hidden = true;
    ufovClearField();
    const len = UFOV_LENGTHS[ufovPrefs.length];
    ufovState = {
      len, total: len.trials, index: -1,
      durationMs: UFOV_START_MS, streak: 0,
      durations: [], // one entry per COMPLETED trial, in order
      correctTrials: 0,
      phase: "idle", trial: null, shapeCorrect: false,
      paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    applyUfovBg();
    els.ufovHint.textContent = "Bereit? Gleich geht's los …";
    els.ufovProgressEl.textContent = `0/${ufovState.total}`;
    requestWakeLock();
    scheduleUfovTimer(ufovNextTrial, 1200);
  }
  els.ufovReadyStartBtn.addEventListener("click", startUfovGame);

  function ufovNextTrial() {
    if (!ufovState) return;
    ufovState.index++;
    if (ufovState.index >= ufovState.total) { ufovFinish(); return; }
    els.ufovProgressEl.textContent = `${ufovState.index + 1}/${ufovState.total}`;
    ufovState.phase = "fixation";
    els.ufovShapeBtns.hidden = true;
    els.ufovRingBtns.hidden = true;
    ufovClearField();
    els.ufovHint.textContent = "+";
    scheduleUfovTimer(ufovShowStimulus, UFOV_FIXATION_MS);
  }
  function ufovShowStimulus() {
    if (!ufovState) return;
    const shape = Math.random() < 0.5 ? "circle" : "square";
    const pos = Math.floor(Math.random() * UFOV_POS_COUNT);
    ufovState.trial = { shape, pos };
    ufovState.phase = "stim";
    els.ufovHint.textContent = "";
    ufovSetCenter("shape-" + shape);
    for (let i = 0; i < UFOV_POS_COUNT; i++) ufovSetRing(i, i === pos ? "target" : "dot");
    scheduleUfovTimer(ufovShowMask, ufovState.durationMs);
  }
  function ufovShowMask() {
    if (!ufovState) return;
    ufovState.phase = "mask";
    ufovSetCenter("masked");
    for (let i = 0; i < UFOV_POS_COUNT; i++) ufovSetRing(i, "masked");
    scheduleUfovTimer(ufovAskShape, UFOV_MASK_MS);
  }
  function ufovAskShape() {
    if (!ufovState) return;
    ufovState.phase = "respond-shape";
    ufovClearField();
    els.ufovShapeCircleBtn.classList.remove("correct", "wrong");
    els.ufovShapeSquareBtn.classList.remove("correct", "wrong");
    els.ufovShapeBtns.hidden = false;
  }
  function ufovPickShape(shape) {
    if (!ufovState || ufovState.paused || ufovState.phase !== "respond-shape") return;
    const correct = shape === ufovState.trial.shape;
    const btn = shape === "circle" ? els.ufovShapeCircleBtn : els.ufovShapeSquareBtn;
    btn.classList.add(correct ? "correct" : "wrong");
    if (!correct) {
      const rightBtn = ufovState.trial.shape === "circle" ? els.ufovShapeCircleBtn : els.ufovShapeSquareBtn;
      rightBtn.classList.add("correct");
    }
    ufovState.shapeCorrect = correct;
    ufovState.phase = "shape-feedback";
    scheduleUfovTimer(ufovAskPosition, UFOV_FEEDBACK_MS);
  }
  els.ufovShapeCircleBtn.addEventListener("click", () => ufovPickShape("circle"));
  els.ufovShapeSquareBtn.addEventListener("click", () => ufovPickShape("square"));

  function ufovAskPosition() {
    if (!ufovState) return;
    els.ufovShapeBtns.hidden = true;
    els.ufovRingBtns.querySelectorAll("[data-ufov-pos]").forEach((b) => b.classList.remove("correct", "wrong"));
    ufovState.phase = "respond-position";
    els.ufovRingBtns.hidden = false;
  }
  function ufovResolveTrial(bothCorrect) {
    ufovState.durations.push(ufovState.durationMs);
    if (bothCorrect) {
      ufovState.correctTrials++;
      ufovState.streak++;
      if (ufovState.streak >= UFOV_STAIRCASE_HITS_NEEDED) {
        ufovState.durationMs = Math.max(UFOV_MIN_MS, ufovState.durationMs - UFOV_STEP_MS);
        ufovState.streak = 0;
      }
    } else {
      ufovState.streak = 0;
      ufovState.durationMs = Math.min(UFOV_MAX_MS, ufovState.durationMs + UFOV_STEP_MS);
    }
  }
  function ufovPickPosition(pos) {
    if (!ufovState || ufovState.paused || ufovState.phase !== "respond-position") return;
    const correct = pos === ufovState.trial.pos;
    const btns = Array.from(els.ufovRingBtns.querySelectorAll("[data-ufov-pos]"));
    btns[pos].classList.add(correct ? "correct" : "wrong");
    // Reveal the true target position too when wrong - same "show what it
    // actually was" convention as MOT's wrong-tap reveal.
    if (!correct) btns[ufovState.trial.pos].classList.add("correct");
    ufovState.phase = "position-feedback";
    ufovResolveTrial(ufovState.shapeCorrect && correct);
    scheduleUfovTimer(ufovNextTrial, UFOV_FEEDBACK_MS);
  }
  els.ufovRingBtns.querySelectorAll("[data-ufov-pos]").forEach((btn) => {
    btn.addEventListener("click", () => ufovPickPosition(Number(btn.dataset.ufovPos)));
  });

  // During the two untimed response phases there is no pending timer to
  // cancel; pause still blocks taps via the `paused` check and the overlay
  // covers the buttons, resume just hides the overlay again. Also carries a
  // live background-adjust overlay (added later, see CLAUDE.md - every
  // Test-Bereich exercise now gets the same background colour/intensity
  // control NAT's own exercises have).
  function pauseUfov() {
    if (!ufovState || ufovState.paused) return;
    ufovState.paused = true;
    ufovState.pausedAt = performance.now();
    if (ufovState.timer) {
      clearTimeout(ufovState.timer);
      ufovState.timer = null;
      ufovState.timerRemainingMs = Math.max(0, ufovState.timerFiresAt - ufovState.pausedAt);
    }
    syncUfovBgUI();
    els.ufovPauseBtn.hidden = true;
    els.ufovPauseOverlay.hidden = false;
  }
  function resumeUfov() {
    if (!ufovState || !ufovState.paused) return;
    const pausedMs = performance.now() - ufovState.pausedAt;
    ufovState.startTime += pausedMs;
    ufovState.paused = false;
    if (ufovState.timerFn && ufovState.timerRemainingMs != null) {
      scheduleUfovTimer(ufovState.timerFn, ufovState.timerRemainingMs);
      ufovState.timerRemainingMs = null;
    }
    els.ufovPauseOverlay.hidden = true;
    els.ufovPauseBtn.hidden = false;
  }
  els.ufovPauseBtn.addEventListener("click", pauseUfov);
  els.ufovResumeBtn.addEventListener("click", resumeUfov);

  function ufovThresholdMs(state) {
    const n = Math.min(UFOV_SCORE_TRIALS, state.durations.length);
    if (!n) return state.durationMs;
    const slice = state.durations.slice(-n);
    return slice.reduce((a, b) => a + b, 0) / n;
  }
  function finalizeUfovRun(state, totalTrials) {
    els.ufovPauseOverlay.hidden = true;
    els.ufovPlayerBar.hidden = true;
    els.ufovShapeBtns.hidden = true;
    els.ufovRingBtns.hidden = true;
    const accuracyPct = totalTrials ? Math.round(100 * state.correctTrials / totalTrials) : 0;
    const threshold = ufovThresholdMs(state);
    // Needs a handful of trials before the rolling average - and a best-
    // score comparison against it - actually means anything.
    const isRecord = state.durations.length >= 5 ? saveUfovBest(threshold) : false;
    renderUfovBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.ufovDoneSummary.textContent =
      `Blickfeld-Test (${state.len.title}) · Schwelle ${Math.round(threshold)} ms · ${accuracyPct}% richtig` +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `Schwelle ${Math.round(threshold)} ms, ${accuracyPct}% richtig`;
    const id = addHistory({ kind: "ufov", title: "Blickfeld-Test (UFOV)", seconds: Math.round(played), note });
    renderRating(els.ufovRating, id, "Wie fokussiert warst du?");
    els.ufovDonePanel.hidden = false;
  }
  function ufovFinish() {
    if (!ufovState) return;
    const state = ufovState;
    ufovState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.ufovPlayer) document.exitFullscreen().catch(() => {});
    els.ufovFsHint.hidden = true;
    finalizeUfovRun(state, state.total);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as a
  // few trials were actually resolved.
  function ufovStop() {
    if (!ufovState) return;
    if (ufovState.timer) clearTimeout(ufovState.timer);
    const state = ufovState;
    ufovState = null;
    els.ufovPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.ufovPlayer) document.exitFullscreen().catch(() => {});
    els.ufovFsHint.hidden = true;
    if (state.durations.length >= 4) {
      finalizeUfovRun(state, state.durations.length);
    } else {
      els.ufovPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.ufovBackBtn.addEventListener("click", ufovStop);
  els.ufovAgainBtn.addEventListener("click", () => { els.ufovDonePanel.hidden = true; startUfovGame(); });
  els.ufovDoneBackBtn.addEventListener("click", () => { els.ufovPlayer.hidden = true; els.ufovDonePanel.hidden = true; showScreen("testHome"); });

  // ==== Test-Bereich: Hinweisreiz-Test (Posner-Cueing) ====
  // Sixth autonomous entry (see CLAUDE.md's "Test-Bereich (autonomous,
  // ongoing)"). Grounded in the Posner cueing task (Posner, 1980): a
  // symbolic/spatial cue briefly highlights one of two locations, a target
  // then appears at the cued location on most trials ("valid") but at the
  // other location on a minority ("invalid") - the RT cost of an invalid
  // cue versus a valid one (the "validity effect"/"cueing effect") is the
  // classic index of how efficiently attention gets voluntarily oriented
  // and, when needed, disengaged and re-oriented. Also researched as sport-
  // relevant: a 2025 multilevel Bayesian meta-analysis across 72 studies/885
  // athletes found cueing/benefit effects scale with cue validity, and
  // athletes in several sports (boxers, volleyball players, ...) show more
  // efficient attentional orienting (smaller valid/invalid RT gaps) than
  // non-athletes - a direct fit for FWMC's "visuelle
  // Entscheidungsgeschwindigkeit"/Aufmerksamkeit focus. Genuinely distinct
  // from every existing Test/NAT mechanic: Go/No-Go tests withholding a
  // response (inhibition), Flanker tests filtering out simultaneous
  // conflicting information (interference control), UFOV tests a divided-
  // attention glance under a time pressure that adapts automatically - this
  // is the only one that isolates the cost of VOLUNTARILY SHIFTING spatial
  // attention from one location to another, using a fixed, clearly-signalled
  // two-location layout rather than a whole-field glance or a central/
  // flanking conflict.
  const POSNER_PREFS_KEY = "fwmc-posner-prefs-v1";
  // Difficulty controls the cue-to-target gap (SOA) - shorter SOA leaves
  // less time to actually use the cue to shift attention before the target
  // appears, same "less time = harder" shape as every other difficulty
  // ladder in this app (GNG_DIFFICULTIES/FLANKER_DIFFICULTIES) - plus the
  // response window and inter-trial gap, same idea as those too.
  const POSNER_DIFFICULTIES = {
    leicht: { title: "Leicht", cueMs: 200, soaMin: 450, soaMax: 650, responseMs: 2200, isiMin: 900, isiMax: 1300 },
    mittel: { title: "Mittel", cueMs: 150, soaMin: 250, soaMax: 400, responseMs: 1600, isiMin: 700, isiMax: 1100 },
    schwer: { title: "Schwer", cueMs: 100, soaMin: 100, soaMax: 200, responseMs: 1100, isiMin: 500, isiMax: 900 },
  };
  // 40 trials at the classic 80% cue validity Posner (1980) himself used -
  // 32 valid (16 left/16 right) + 8 invalid (4 left-cued-right-target/4
  // right-cued-left-target). Enough invalid trials for a meaningful average
  // without making the cue so unreliable it stops being worth attending to.
  const POSNER_TRIAL_COUNT = 40;
  const posnerPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadPosnerPrefs() {
    const saved = readJSON(POSNER_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(posnerPrefs, saved);
    if (!POSNER_DIFFICULTIES[posnerPrefs.difficulty]) posnerPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[posnerPrefs.bgColorKey]) posnerPrefs.bgColorKey = "gruen";
    if (typeof posnerPrefs.bgIntensity !== "number" || posnerPrefs.bgIntensity < 0 || posnerPrefs.bgIntensity > 1) posnerPrefs.bgIntensity = 0;
  }
  loadPosnerPrefs();
  function savePosnerPrefsToStorage() { writeJSON(POSNER_PREFS_KEY, posnerPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyPosnerBg() {
    els.posnerStage.style.background = posnerPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[posnerPrefs.bgColorKey].hex, posnerPrefs.bgIntensity)
      : "";
  }
  const syncPosnerBgUI = wireBgIntensityControl(posnerPrefs, {
    pickers: [els.posnerBgColorPicker, els.posnerPauseBgColorPicker],
    sliders: [els.posnerBgIntensitySlider, els.posnerPauseBgSlider],
    valueEls: [els.posnerBgIntensityValue, els.posnerPauseBgValue],
    hintEls: [els.posnerBgContrastHint],
  }, () => { savePosnerPrefsToStorage(); applyPosnerBg(); });

  const POSNER_BEST_KEY = "fwmc-posner-best-v1"; // { [difficulty]: bestAccuracyPct }
  function posnerBestFor() { return readJSON(POSNER_BEST_KEY, {})[posnerPrefs.difficulty] || 0; }
  function savePosnerBest(accuracyPct) {
    const all = readJSON(POSNER_BEST_KEY, {});
    if (accuracyPct > (all[posnerPrefs.difficulty] || 0)) { all[posnerPrefs.difficulty] = accuracyPct; writeJSON(POSNER_BEST_KEY, all); return true; }
    return false;
  }
  function renderPosnerBest() {
    const best = posnerBestFor();
    const text = best ? `Beste Genauigkeit (${POSNER_DIFFICULTIES[posnerPrefs.difficulty].title}): ${best}%` : "";
    els.posnerBestHint.textContent = text;
    els.posnerReadyBestHint.textContent = text;
  }
  function syncPosnerDifficultyUI() {
    els.posnerDifficultyRow.querySelectorAll("[data-posner-diff]").forEach((btn) => setActive(btn, btn.dataset.posnerDiff === posnerPrefs.difficulty));
  }
  els.posnerDifficultyRow.querySelectorAll("[data-posner-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      posnerPrefs.difficulty = btn.dataset.posnerDiff;
      savePosnerPrefsToStorage();
      syncPosnerDifficultyUI();
      renderPosnerBest();
    });
  });

  els.posnerOpenBtn.addEventListener("click", () => {
    syncPosnerDifficultyUI();
    syncPosnerBgUI();
    renderPosnerBest();
    showScreen("posnerReady");
  });
  els.posnerReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleFlankerTimer/scheduleGngTimer:
  // records what's pending and when it fires, so Pause can cancel it and
  // Resume can replay it with its exact remaining delay.
  function schedulePosnerTimer(fn, delayMs) {
    posnerState.timerFn = fn;
    posnerState.timerFiresAt = performance.now() + delayMs;
    posnerState.timer = setTimeout(() => { posnerState.timer = null; fn(); }, delayMs);
  }

  function buildPosnerTrials() {
    const trials = [];
    ["left", "right"].forEach((side) => {
      for (let i = 0; i < 16; i++) trials.push({ cueSide: side, targetSide: side, valid: true });
    });
    ["left", "right"].forEach((side) => {
      const other = side === "left" ? "right" : "left";
      for (let i = 0; i < 4; i++) trials.push({ cueSide: side, targetSide: other, valid: false });
    });
    // Shuffle, then avoid more than 3 identical TARGET sides back to back -
    // same guard as buildFlankerTrials, so a "just keep tapping the same
    // side" motor strategy can't pass undetected.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < trials.length; i++) {
        if (trials[i].targetSide === trials[i - 1].targetSide) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return trials;
  }

  function posnerClearBoxes() {
    els.posnerLeftBtn.classList.remove("cued", "correct", "wrong");
    els.posnerRightBtn.classList.remove("cued", "correct", "wrong");
    els.posnerLeftDot.classList.remove("show");
    els.posnerRightDot.classList.remove("show");
  }
  function posnerBoxFor(side) { return side === "left" ? els.posnerLeftBtn : els.posnerRightBtn; }
  function posnerDotFor(side) { return side === "left" ? els.posnerLeftDot : els.posnerRightDot; }

  let posnerState = null;
  function startPosnerGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.posnerPlayer.hidden = false;
    els.posnerPlayerBar.hidden = false;
    els.posnerDonePanel.hidden = true;
    els.posnerPauseOverlay.hidden = true;
    els.posnerPauseBtn.hidden = false;
    posnerState = {
      diff: POSNER_DIFFICULTIES[posnerPrefs.difficulty], trials: buildPosnerTrials(), index: -1, phase: "gap", responded: false,
      correct: 0, incorrect: 0, timeouts: 0, rtsValid: [], rtsInvalid: [],
      stimAt: 0, paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    applyPosnerBg();
    posnerClearBoxes();
    els.posnerHint.textContent = "Bereit? Gleich geht's los …";
    els.posnerProgressEl.textContent = `0/${posnerState.trials.length}`;
    requestWakeLock();
    schedulePosnerTimer(posnerNextTrial, 1200);
  }
  els.posnerReadyStartBtn.addEventListener("click", startPosnerGame);

  function posnerNextTrial() {
    if (!posnerState) return;
    posnerState.index++;
    if (posnerState.index >= posnerState.trials.length) { posnerFinish(); return; }
    els.posnerProgressEl.textContent = `${posnerState.index + 1}/${posnerState.trials.length}`;
    posnerState.phase = "gap";
    posnerState.responded = false;
    posnerClearBoxes();
    const isi = posnerState.diff.isiMin + Math.random() * (posnerState.diff.isiMax - posnerState.diff.isiMin);
    schedulePosnerTimer(posnerShowCue, isi);
  }
  function posnerShowCue() {
    if (!posnerState) return;
    const trial = posnerState.trials[posnerState.index];
    posnerState.phase = "cue";
    // The previous trial's feedback hint ("Verpasst!"/"Falsche Seite!")
    // deliberately stays up through the whole ISI gap and is only cleared
    // once the NEXT trial's own visible event (the cue) actually appears -
    // same rhythm as flankerShowStimulus clearing flankerHint only once the
    // next arrow row appears, not immediately when the trial index advances.
    els.posnerHint.textContent = "";
    posnerBoxFor(trial.cueSide).classList.add("cued");
    schedulePosnerTimer(posnerHideCue, posnerState.diff.cueMs);
  }
  function posnerHideCue() {
    if (!posnerState) return;
    els.posnerLeftBtn.classList.remove("cued");
    els.posnerRightBtn.classList.remove("cued");
    posnerState.phase = "soa";
    const soa = posnerState.diff.soaMin + Math.random() * (posnerState.diff.soaMax - posnerState.diff.soaMin);
    schedulePosnerTimer(posnerShowTarget, soa);
  }
  function posnerShowTarget() {
    if (!posnerState) return;
    const trial = posnerState.trials[posnerState.index];
    posnerState.phase = "responding";
    posnerState.responded = false;
    posnerState.stimAt = performance.now();
    posnerDotFor(trial.targetSide).classList.add("show");
    schedulePosnerTimer(posnerEndTrial, posnerState.diff.responseMs);
  }
  function posnerEndTrial() {
    if (!posnerState) return;
    if (posnerState.phase === "responding" && !posnerState.responded) {
      posnerState.incorrect++;
      posnerState.timeouts++;
      els.posnerHint.textContent = "Verpasst!";
    }
    posnerState.phase = "gap";
    posnerNextTrial();
  }
  function posnerTap(side) {
    if (!posnerState || posnerState.paused || posnerState.responded) return;
    // Taps before the target actually appears (during the cue or the SOA
    // gap) are ignored - reaction time is measured target-locked, same
    // convention as Flanker's/Go-No-Go's own tap handlers. This also means
    // tapping the cued box the instant it lights up scores nothing either
    // way - only a tap once the real target is on screen counts.
    if (posnerState.phase !== "responding") return;
    posnerState.responded = true;
    const trial = posnerState.trials[posnerState.index];
    const rt = performance.now() - posnerState.stimAt;
    const correct = side === trial.targetSide;
    posnerBoxFor(side).classList.add(correct ? "correct" : "wrong");
    if (correct) {
      posnerState.correct++;
      (trial.valid ? posnerState.rtsValid : posnerState.rtsInvalid).push(rt);
    } else {
      posnerState.incorrect++;
      els.posnerHint.textContent = "Falsche Seite!";
    }
    // The feedback colour stays up for whatever's left of diff.responseMs
    // (the already-scheduled posnerEndTrial fires the actual transition) -
    // same rhythm as Flanker/Go-No-Go leaving their own tap feedback up for
    // the rest of the response window, no separate timer needed.
  }
  els.posnerLeftBtn.addEventListener("click", () => posnerTap("left"));
  els.posnerRightBtn.addEventListener("click", () => posnerTap("right"));

  // Pause stops/replays the pending timer, same setTimeout trick as
  // Remember/Blitz/Flash/MOT, plus a live background-adjust overlay (added
  // later, see CLAUDE.md - every Test-Bereich exercise now gets the same
  // background colour/intensity control NAT's own exercises have).
  function pausePosner() {
    if (!posnerState || posnerState.paused) return;
    posnerState.paused = true;
    posnerState.pausedAt = performance.now();
    if (posnerState.timer) {
      clearTimeout(posnerState.timer);
      posnerState.timer = null;
      posnerState.timerRemainingMs = Math.max(0, posnerState.timerFiresAt - posnerState.pausedAt);
    }
    syncPosnerBgUI();
    els.posnerPauseBtn.hidden = true;
    els.posnerPauseOverlay.hidden = false;
  }
  function resumePosner() {
    if (!posnerState || !posnerState.paused) return;
    const pausedMs = performance.now() - posnerState.pausedAt;
    posnerState.startTime += pausedMs;
    posnerState.stimAt += pausedMs;
    posnerState.paused = false;
    if (posnerState.timerFn && posnerState.timerRemainingMs != null) {
      schedulePosnerTimer(posnerState.timerFn, posnerState.timerRemainingMs);
      posnerState.timerRemainingMs = null;
    }
    els.posnerPauseOverlay.hidden = true;
    els.posnerPauseBtn.hidden = false;
  }
  els.posnerPauseBtn.addEventListener("click", pausePosner);
  els.posnerResumeBtn.addEventListener("click", resumePosner);

  function finalizePosnerRun(state, totalTrials) {
    els.posnerPauseOverlay.hidden = true;
    els.posnerPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const avgValid = avgOf(state.rtsValid);
    const avgInvalid = avgOf(state.rtsInvalid);
    // The "cueing effect"/"validity effect" itself: how much slower correct
    // invalid-cue responses were versus correct valid-cue ones - the classic
    // attentional-orienting-cost measure this whole task exists to surface.
    const cueingEffect = (avgValid != null && avgInvalid != null) ? (avgInvalid - avgValid) : null;
    const isRecord = savePosnerBest(accuracyPct);
    renderPosnerBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.posnerDoneSummary.textContent =
      `Hinweisreiz-Test (${state.diff.title}) · ${accuracyPct}% richtig` +
      (avgValid != null ? ` · Ø gültiger Hinweis ${avgValid} ms` : "") +
      (avgInvalid != null ? ` · Ø ungültiger Hinweis ${avgInvalid} ms` : "") +
      (cueingEffect != null ? ` · Umlenkungs-Kosten ${cueingEffect} ms` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` + (cueingEffect != null ? `, Umlenkung ${cueingEffect} ms` : "");
    const id = addHistory({ kind: "posner", title: "Hinweisreiz-Test (Posner-Cueing)", seconds: Math.round(played), note });
    renderRating(els.posnerRating, id, "Wie fokussiert warst du?");
    els.posnerDonePanel.hidden = false;
  }
  function posnerFinish() {
    if (!posnerState) return;
    const state = posnerState;
    posnerState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.posnerPlayer) document.exitFullscreen().catch(() => {});
    els.posnerFsHint.hidden = true;
    finalizePosnerRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function posnerStop() {
    if (!posnerState) return;
    if (posnerState.timer) clearTimeout(posnerState.timer);
    const state = posnerState;
    posnerState = null;
    els.posnerPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.posnerPlayer) document.exitFullscreen().catch(() => {});
    els.posnerFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= 4) {
      finalizePosnerRun(state, resolved);
    } else {
      els.posnerPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.posnerBackBtn.addEventListener("click", posnerStop);
  els.posnerAgainBtn.addEventListener("click", () => { els.posnerDonePanel.hidden = true; startPosnerGame(); });
  els.posnerDoneBackBtn.addEventListener("click", () => { els.posnerPlayer.hidden = true; els.posnerDonePanel.hidden = true; showScreen("testHome"); });

  // Rotationstest (Mentale Rotation) - grounded in the classic mental-
  // rotation/character-rotation chronometric paradigm (Cooper & Shepard,
  // 1973): a letter or digit is shown rotated out of its upright
  // orientation, either in its normal form or mirror-reversed, and the
  // participant judges "normal" or "mirrored" as fast as possible. The
  // hallmark, endlessly-replicated finding is that reaction time rises
  // roughly with how far the character is rotated from upright - the mind
  // is understood to mentally "rotate the image back" toward upright
  // before it can judge it. Genuinely distinct from every existing
  // Test/NAT mechanic: Go/No-Go tests withholding a response, Flanker
  // tests filtering simultaneous conflicting stimuli, Posner-Cueing tests
  // voluntarily shifting spatial attention, UFOV tests a divided-attention
  // glance under adaptive time pressure - none of them ask the participant
  // to judge a SPATIAL TRANSFORMATION of a single stimulus, which is what
  // this one adds. Also researched as sport-relevant before building:
  // athletes in high-spatial-demand sports (e.g. rotation/aerial sports)
  // show better mental-rotation performance than non-athletes, an
  // "embodied cognition" effect attributed to years of training rather
  // than innate ability - see the 2023 Exp Brain Res VR study on embodied
  // mental rotation comparing open- vs closed-skill-sport athletes, and a
  // 2024/2025 behavioural+fNIRS study directly linking sport training in
  // AXIAL ROTATION to improved spatial/mental-rotation ability. A good fit
  // for FWMC's "bewegungsnahes mentales Training" angle, not just a pure
  // desk-cognition task.
  const ROTATION_PREFS_KEY = "fwmc-rotation-prefs-v1";
  // Difficulty controls the response window (the character stays up until
  // tapped or this elapses) and the inter-trial gap - same shape as
  // FLANKER_DIFFICULTIES/POSNER_DIFFICULTIES. Windows run longer than
  // Flanker's own since judging a rotated/mirrored character is a genuinely
  // slower decision than reading a simple arrow direction.
  const ROTATION_DIFFICULTIES = {
    leicht: { title: "Leicht", responseMs: 4000, isiMin: 900, isiMax: 1400 },
    mittel: { title: "Mittel", responseMs: 3000, isiMin: 700, isiMax: 1100 },
    schwer: { title: "Schwer", responseMs: 2000, isiMin: 500, isiMax: 900 },
  };
  // Asymmetric letters/digits only - each must look genuinely different
  // mirrored versus normal (unlike e.g. "O"/"H"/"A"/"0"/"1"/"8", which look
  // identical either way), the same requirement Cooper & Shepard's own
  // letter stimuli met.
  const ROTATION_CHARS = ["F", "G", "J", "L", "P", "R", "2", "4", "5", "7"];
  // 8 orientations around the full circle (0-315 in 45-degree steps) x
  // normal/mirrored x 2 repeats = 32 trials - every orientation sampled
  // equally often in both forms, rather than forcing an artificial 50/50
  // near/far-rotation split (the angular-disparity effect this task
  // measures is a continuous one, not a binary category).
  const ROTATION_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315];
  const ROTATION_TRIAL_COUNT = ROTATION_ANGLES.length * 2 * 2;
  // Angular disparity from upright, 0-180 - a 200 degree rotation is just as
  // far from upright as a 160 degree one (the mind can rotate either way).
  function rotationDisparity(angle) { return Math.min(angle, 360 - angle); }
  const rotationPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadRotationPrefs() {
    const saved = readJSON(ROTATION_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(rotationPrefs, saved);
    if (!ROTATION_DIFFICULTIES[rotationPrefs.difficulty]) rotationPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[rotationPrefs.bgColorKey]) rotationPrefs.bgColorKey = "gruen";
    if (typeof rotationPrefs.bgIntensity !== "number" || rotationPrefs.bgIntensity < 0 || rotationPrefs.bgIntensity > 1) rotationPrefs.bgIntensity = 0;
  }
  loadRotationPrefs();
  function saveRotationPrefsToStorage() { writeJSON(ROTATION_PREFS_KEY, rotationPrefs); }

  // Background colour/intensity, added later (client asked every Test-Bereich
  // exercise get the same background customisation NAT's Remember/Blitz/
  // Flash/MOT already have) - see CLAUDE.md Established patterns for the
  // scope decision (no transfer/preset-save here, unlike those four). The
  // tint goes straight on the DOM stage that holds the rotated character,
  // same "no canvas" approach as Remember's own applyRememberBg().
  function applyRotationBg() {
    els.rotationStage.style.background = rotationPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[rotationPrefs.bgColorKey].hex, rotationPrefs.bgIntensity)
      : "";
  }
  const syncRotationBgUI = wireBgIntensityControl(rotationPrefs, {
    pickers: [els.rotationBgColorPicker, els.rotationPauseBgColorPicker],
    sliders: [els.rotationBgIntensitySlider, els.rotationPauseBgSlider],
    valueEls: [els.rotationBgIntensityValue, els.rotationPauseBgValue],
    hintEls: [els.rotationBgContrastHint],
  }, () => { saveRotationPrefsToStorage(); applyRotationBg(); });

  const ROTATION_BEST_KEY = "fwmc-rotation-best-v1"; // { [difficulty]: bestAccuracyPct }
  function rotationBestFor() { return readJSON(ROTATION_BEST_KEY, {})[rotationPrefs.difficulty] || 0; }
  function saveRotationBest(accuracyPct) {
    const all = readJSON(ROTATION_BEST_KEY, {});
    if (accuracyPct > (all[rotationPrefs.difficulty] || 0)) { all[rotationPrefs.difficulty] = accuracyPct; writeJSON(ROTATION_BEST_KEY, all); return true; }
    return false;
  }
  function renderRotationBest() {
    const best = rotationBestFor();
    const text = best ? `Beste Genauigkeit (${ROTATION_DIFFICULTIES[rotationPrefs.difficulty].title}): ${best}%` : "";
    els.rotationBestHint.textContent = text;
    els.rotationReadyBestHint.textContent = text;
  }
  function syncRotationDifficultyUI() {
    els.rotationDifficultyRow.querySelectorAll("[data-rotation-diff]").forEach((btn) => setActive(btn, btn.dataset.rotationDiff === rotationPrefs.difficulty));
  }
  els.rotationDifficultyRow.querySelectorAll("[data-rotation-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      rotationPrefs.difficulty = btn.dataset.rotationDiff;
      saveRotationPrefsToStorage();
      syncRotationDifficultyUI();
      renderRotationBest();
    });
  });

  els.rotationOpenBtn.addEventListener("click", () => {
    syncRotationDifficultyUI();
    syncRotationBgUI();
    renderRotationBest();
    showScreen("rotationReady");
  });
  els.rotationReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleFlankerTimer/schedulePosnerTimer:
  // records what's pending and when it fires, so Pause can cancel it and
  // Resume can replay it with its exact remaining delay.
  function scheduleRotationTimer(fn, delayMs) {
    rotationState.timerFn = fn;
    rotationState.timerFiresAt = performance.now() + delayMs;
    rotationState.timer = setTimeout(() => { rotationState.timer = null; fn(); }, delayMs);
  }

  function buildRotationTrials() {
    const trials = [];
    ROTATION_ANGLES.forEach((angle) => {
      [false, true].forEach((mirrored) => {
        for (let i = 0; i < 2; i++) {
          const char = ROTATION_CHARS[Math.floor(Math.random() * ROTATION_CHARS.length)];
          trials.push({ angle, mirrored, char, disparity: rotationDisparity(angle) });
        }
      });
    });
    // Shuffle, then avoid more than 3 identical CORRECT answers (normal vs
    // mirrored) back to back - same "just keep tapping the same button"
    // motor-strategy guard as buildFlankerTrials/buildPosnerTrials.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < trials.length; i++) {
        if (trials[i].mirrored === trials[i - 1].mirrored) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return trials;
  }

  function rotationClearChar() {
    els.rotationCharEl.textContent = "";
    els.rotationCharEl.style.transform = "";
  }
  function rotationRenderTrial(trial) {
    els.rotationCharEl.textContent = trial.char;
    // Mirror FIRST, then rotate - matches the real paradigm (a letter is
    // either printed normally or mirror-reversed, and that physical form is
    // THEN rotated in the picture plane) rather than rotating first and
    // mirroring the already-rotated result, which is a different transform
    // (rotation and horizontal mirroring don't commute except at 0/180
    // degrees) - CSS applies the rightmost function first, so scaleX runs
    // before rotate here.
    els.rotationCharEl.style.transform = `rotate(${trial.angle}deg) scaleX(${trial.mirrored ? -1 : 1})`;
  }

  let rotationState = null;
  function startRotationGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.rotationPlayer.hidden = false;
    els.rotationPlayerBar.hidden = false;
    els.rotationDonePanel.hidden = true;
    els.rotationPauseOverlay.hidden = true;
    els.rotationPauseBtn.hidden = false;
    rotationState = {
      diff: ROTATION_DIFFICULTIES[rotationPrefs.difficulty], trials: buildRotationTrials(), index: -1, phase: "gap", responded: false,
      correct: 0, incorrect: 0, timeouts: 0, rtsNear: [], rtsFar: [],
      stimAt: 0, paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    applyRotationBg();
    rotationClearChar();
    els.rotationNormalBtn.classList.remove("correct", "wrong");
    els.rotationMirroredBtn.classList.remove("correct", "wrong");
    els.rotationHint.textContent = "Bereit? Gleich geht's los …";
    els.rotationProgressEl.textContent = `0/${rotationState.trials.length}`;
    requestWakeLock();
    scheduleRotationTimer(rotationNextTrial, 1200);
  }
  els.rotationReadyStartBtn.addEventListener("click", startRotationGame);

  function rotationNextTrial() {
    if (!rotationState) return;
    rotationState.index++;
    if (rotationState.index >= rotationState.trials.length) { rotationFinish(); return; }
    els.rotationProgressEl.textContent = `${rotationState.index + 1}/${rotationState.trials.length}`;
    rotationState.phase = "gap";
    rotationState.responded = false;
    rotationClearChar();
    const isi = rotationState.diff.isiMin + Math.random() * (rotationState.diff.isiMax - rotationState.diff.isiMin);
    scheduleRotationTimer(rotationShowStimulus, isi);
  }
  function rotationShowStimulus() {
    if (!rotationState) return;
    const trial = rotationState.trials[rotationState.index];
    rotationState.phase = "responding";
    rotationState.responded = false;
    rotationState.stimAt = performance.now();
    els.rotationHint.textContent = "";
    els.rotationNormalBtn.classList.remove("correct", "wrong");
    els.rotationMirroredBtn.classList.remove("correct", "wrong");
    rotationRenderTrial(trial);
    scheduleRotationTimer(rotationEndTrial, rotationState.diff.responseMs);
  }
  function rotationEndTrial() {
    if (!rotationState) return;
    if (rotationState.phase === "responding" && !rotationState.responded) {
      rotationState.incorrect++;
      rotationState.timeouts++;
      els.rotationHint.textContent = "Verpasst!";
    }
    rotationState.phase = "gap";
    rotationClearChar();
    rotationNextTrial();
  }
  function rotationTap(mirroredGuess) {
    if (!rotationState || rotationState.paused || rotationState.responded) return;
    // Taps before the character actually appears are ignored - reaction
    // time is measured stimulus-locked, same convention as Flanker's/
    // Posner's own tap handlers.
    if (rotationState.phase !== "responding") return;
    rotationState.responded = true;
    const trial = rotationState.trials[rotationState.index];
    const rt = performance.now() - rotationState.stimAt;
    const correct = mirroredGuess === trial.mirrored;
    const btn = mirroredGuess ? els.rotationMirroredBtn : els.rotationNormalBtn;
    btn.classList.add(correct ? "correct" : "wrong");
    if (correct) {
      rotationState.correct++;
      (trial.disparity <= 90 ? rotationState.rtsNear : rotationState.rtsFar).push(rt);
    } else {
      rotationState.incorrect++;
      els.rotationHint.textContent = "Leider falsch!";
    }
    // The feedback colour on the tapped button stays up for whatever's left
    // of diff.responseMs (the already-scheduled rotationEndTrial fires the
    // actual transition) - same rhythm as Flanker/Posner leaving their own
    // tap feedback up for the rest of the response window, no separate
    // timer needed.
  }
  els.rotationNormalBtn.addEventListener("click", () => rotationTap(false));
  els.rotationMirroredBtn.addEventListener("click", () => rotationTap(true));

  // Pause just stops/replays the pending timer, no live background-adjust
  // overlay - background colour customisation was skipped for this exercise
  // (explicitly optional per the Test-Bereich guidance) so there is nothing
  // to adjust while paused.
  function pauseRotation() {
    if (!rotationState || rotationState.paused) return;
    rotationState.paused = true;
    rotationState.pausedAt = performance.now();
    if (rotationState.timer) {
      clearTimeout(rotationState.timer);
      rotationState.timer = null;
      rotationState.timerRemainingMs = Math.max(0, rotationState.timerFiresAt - rotationState.pausedAt);
    }
    els.rotationPauseBtn.hidden = true;
    els.rotationPauseOverlay.hidden = false;
  }
  function resumeRotation() {
    if (!rotationState || !rotationState.paused) return;
    const pausedMs = performance.now() - rotationState.pausedAt;
    rotationState.startTime += pausedMs;
    rotationState.stimAt += pausedMs;
    rotationState.paused = false;
    if (rotationState.timerFn && rotationState.timerRemainingMs != null) {
      scheduleRotationTimer(rotationState.timerFn, rotationState.timerRemainingMs);
      rotationState.timerRemainingMs = null;
    }
    els.rotationPauseOverlay.hidden = true;
    els.rotationPauseBtn.hidden = false;
  }
  els.rotationPauseBtn.addEventListener("click", pauseRotation);
  els.rotationResumeBtn.addEventListener("click", resumeRotation);

  function finalizeRotationRun(state, totalTrials) {
    els.rotationPauseOverlay.hidden = true;
    els.rotationPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const avgNear = avgOf(state.rtsNear);
    const avgFar = avgOf(state.rtsFar);
    // The classic mental-rotation effect itself: how much slower correct
    // responses were for characters rotated FAR from upright (>90 degrees
    // of angular disparity) versus NEAR upright (<=90 degrees) - the
    // signature "RT rises with rotation angle" finding this paradigm exists
    // to surface.
    const rotationCost = (avgNear != null && avgFar != null) ? (avgFar - avgNear) : null;
    const isRecord = saveRotationBest(accuracyPct);
    renderRotationBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.rotationDoneSummary.textContent =
      `Rotationstest (${state.diff.title}) · ${accuracyPct}% richtig` +
      (avgNear != null ? ` · Ø nah an aufrecht ${avgNear} ms` : "") +
      (avgFar != null ? ` · Ø stark gedreht ${avgFar} ms` : "") +
      (rotationCost != null ? ` · Rotations-Kosten ${rotationCost} ms` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` + (rotationCost != null ? `, Rotation ${rotationCost} ms` : "");
    const id = addHistory({ kind: "rotation", title: "Rotationstest (Mentale Rotation)", seconds: Math.round(played), note });
    renderRating(els.rotationRating, id, "Wie sicher hast du dich gefühlt?");
    els.rotationDonePanel.hidden = false;
  }
  function rotationFinish() {
    if (!rotationState) return;
    const state = rotationState;
    rotationState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.rotationPlayer) document.exitFullscreen().catch(() => {});
    els.rotationFsHint.hidden = true;
    finalizeRotationRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function rotationStop() {
    if (!rotationState) return;
    if (rotationState.timer) clearTimeout(rotationState.timer);
    const state = rotationState;
    rotationState = null;
    els.rotationPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.rotationPlayer) document.exitFullscreen().catch(() => {});
    els.rotationFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= 4) {
      finalizeRotationRun(state, resolved);
    } else {
      els.rotationPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.rotationBackBtn.addEventListener("click", rotationStop);
  els.rotationAgainBtn.addEventListener("click", () => { els.rotationDonePanel.hidden = true; startRotationGame(); });
  els.rotationDoneBackBtn.addEventListener("click", () => { els.rotationPlayer.hidden = true; els.rotationDonePanel.hidden = true; showScreen("testHome"); });

  // Merkspanne-Test (Change Detection) - grounded in the classic visual
  // working-memory change-detection paradigm (Phillips, 1974; popularised by
  // Luck & Vogel, 1997, Nature 390:279-281): a brief sample array of coloured
  // squares is shown, followed by a blank retention interval, then a test
  // array at the SAME positions that is either identical or has exactly one
  // square's colour changed - the participant reports whether anything
  // changed anywhere in the whole display. This whole-display "has anything
  // changed" judgment (as opposed to a single cued/probed item) is scored
  // with Pashler's K = N x (hitRate - falseAlarmRate) / (1 - falseAlarmRate)
  // - the capacity-correction formula for exactly this whole-display method
  // (Pashler, 1988; Cowan's simpler K = N x (hitRate - falseAlarmRate) is the
  // right formula for a single-item-probe variant instead, which this isn't -
  // see Rouder et al. 2011/Cowan 2001 on the distinction). Typical human
  // capacity for simple single-feature (colour) arrays is roughly 3-4 items
  // (Luck & Vogel's own headline finding), which is why "Schwer" (8 items) is
  // deliberately set well above that ceiling - there's supposed to be a real
  // capacity limit to bump into, not just a task everyone maxes out. Also
  // researched as sport-relevant before building: a 2026 Frontiers study
  // found visuospatial working-memory capacity predicts faster, more
  // efficient tactical decision-making in soccer players' 3v2 offensive
  // scenarios - a good fit for FWMC's "Gedächtnis" focus - though flagging
  // honestly that evidence specifically for THIS RT-free change-detection
  // paradigm distinguishing athletes from non-athletes is mixed (e.g. one
  // PLOS ONE study found volleyball players showed advantages on iconic
  // memory/attentional alerting but not on change-detection RT itself); the
  // paradigm is included for its capacity-measurement value regardless.
  // Genuinely distinct from every existing Test/NAT memory mechanic:
  // Positions-Gedächtnis (N-Back) is a SEQUENTIAL trial-by-trial match-back
  // task with no set "array" held at once; Remember and Blitz-Raster both
  // test recalling WHICH positions were shown (spatial location memory,
  // reproduced by tapping); Flash Speicher Test is a digit SEQUENCE recall
  // task. This is the only one that holds a whole array in memory
  // simultaneously and probes a single FEATURE (colour) of it via a global
  // same/different judgment - the classic visual-working-memory-STORAGE
  // paradigm, a different construct from all of the above.
  const MERK_PREFS_KEY = "fwmc-merk-prefs-v1";
  // Difficulty is array size (N) - the actual experimental manipulation in
  // the real paradigm (Luck & Vogel varied set size, not exposure timing).
  // Exposure/retention timing stays fixed across difficulties, same idea as
  // UFOV's own "the built-in task IS the difficulty axis" shape, just here
  // it's client-picked rather than adaptive.
  const MERK_DIFFICULTIES = {
    leicht: { title: "Leicht", n: 4 },
    mittel: { title: "Mittel", n: 6 },
    schwer: { title: "Schwer", n: 8 },
  };
  // Fixed, dark-mode-safe hex colours - never var(--...), per the
  // Test-Bereich convention. 9 entries so even "Schwer" (8 shown at once)
  // always leaves at least one unused colour available to swap in as an
  // unambiguous "changed" colour.
  const MERK_PALETTE = ["#e53935", "#1e88e5", "#43a047", "#fdd835", "#8e24aa", "#fb8c00", "#00acc1", "#d81b60", "#6d4c41"];
  const MERK_TRIAL_COUNT = 20; // balanced 10 changed / 10 unchanged, see buildMerkTrials
  const MERK_STUDY_MS = 500; // sample-array exposure
  const MERK_RETENTION_MS = 900; // blank retention interval - same order of magnitude as Luck & Vogel's own design
  const MERK_ISI_MIN = 700, MERK_ISI_MAX = 1000; // gap before the next trial's sample array
  const MERK_FEEDBACK_MS = 800; // how long the tapped button's correct/wrong colour stays up before the next trial
  const MERK_ITEM_PX = 40;
  const MERK_MIN_CENTER_PX = MERK_ITEM_PX + 14;
  const merkPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadMerkPrefs() {
    const saved = readJSON(MERK_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(merkPrefs, saved);
    if (!MERK_DIFFICULTIES[merkPrefs.difficulty]) merkPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[merkPrefs.bgColorKey]) merkPrefs.bgColorKey = "gruen";
    if (typeof merkPrefs.bgIntensity !== "number" || merkPrefs.bgIntensity < 0 || merkPrefs.bgIntensity > 1) merkPrefs.bgIntensity = 0;
  }
  loadMerkPrefs();
  function saveMerkPrefsToStorage() { writeJSON(MERK_PREFS_KEY, merkPrefs); }

  // Background colour/intensity, added later (client asked every Test-Bereich
  // exercise get the same background customisation NAT's Remember/Blitz/
  // Flash/MOT already have) - see CLAUDE.md Established patterns for the
  // scope decision (no transfer/preset-save here, unlike those four). The
  // tint goes on the outer #merkStage (which also holds the hint and the
  // response row), NOT #merkField - the smaller sub-box where the coloured
  // memoranda themselves render - so the background never competes with the
  // colour-change signal being tested.
  function applyMerkBg() {
    els.merkStage.style.background = merkPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[merkPrefs.bgColorKey].hex, merkPrefs.bgIntensity)
      : "";
  }
  const syncMerkBgUI = wireBgIntensityControl(merkPrefs, {
    pickers: [els.merkBgColorPicker, els.merkPauseBgColorPicker],
    sliders: [els.merkBgIntensitySlider, els.merkPauseBgSlider],
    valueEls: [els.merkBgIntensityValue, els.merkPauseBgValue],
    hintEls: [els.merkBgContrastHint],
  }, () => { saveMerkPrefsToStorage(); applyMerkBg(); });

  const MERK_BEST_KEY = "fwmc-merk-best-v1"; // { [difficulty]: bestK (Pashler's K, one decimal) }
  function merkBestFor() { return readJSON(MERK_BEST_KEY, {})[merkPrefs.difficulty] || 0; }
  function saveMerkBest(k) {
    const all = readJSON(MERK_BEST_KEY, {});
    if (k > (all[merkPrefs.difficulty] || 0)) { all[merkPrefs.difficulty] = k; writeJSON(MERK_BEST_KEY, all); return true; }
    return false;
  }
  function renderMerkBest() {
    const best = merkBestFor();
    const text = best ? `Beste Kapazität (${MERK_DIFFICULTIES[merkPrefs.difficulty].title}): K ${best}` : "";
    els.merkBestHint.textContent = text;
    els.merkReadyBestHint.textContent = text;
  }
  function syncMerkDifficultyUI() {
    els.merkDifficultyRow.querySelectorAll("[data-merk-diff]").forEach((btn) => setActive(btn, btn.dataset.merkDiff === merkPrefs.difficulty));
  }
  els.merkDifficultyRow.querySelectorAll("[data-merk-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      merkPrefs.difficulty = btn.dataset.merkDiff;
      saveMerkPrefsToStorage();
      syncMerkDifficultyUI();
      renderMerkBest();
    });
  });

  els.merkOpenBtn.addEventListener("click", () => {
    syncMerkDifficultyUI();
    syncMerkBgUI();
    renderMerkBest();
    showScreen("merkReady");
  });
  els.merkReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleRotationTimer/scheduleFlankerTimer:
  // records what's pending and when it fires, so Pause can cancel it and
  // Resume can replay it with its exact remaining delay. During the
  // untimed "responding" phase (waiting on a tap) no timer is pending at
  // all, which pause/resume below handle the same way UFOV's own untimed
  // response phases do - there's simply nothing to cancel/replay then.
  function scheduleMerkTimer(fn, delayMs) {
    merkState.timerFn = fn;
    merkState.timerFiresAt = performance.now() + delayMs;
    merkState.timer = setTimeout(() => { merkState.timer = null; fn(); }, delayMs);
  }

  function buildMerkTrials() {
    const trials = [];
    for (let i = 0; i < MERK_TRIAL_COUNT / 2; i++) { trials.push({ changed: true }); trials.push({ changed: false }); }
    // Shuffle, then avoid more than 3 identical answers back to back - same
    // "just keep tapping the same button" motor-strategy guard as
    // buildFlankerTrials/buildPosnerTrials/buildRotationTrials.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < trials.length; i++) {
        if (trials[i].changed === trials[i - 1].changed) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return trials;
  }

  // Anti-overlap scatter placement inside the fixed merk-field box -
  // copy-adapted from Trail Making's own trailRandomPixelPosition (rejection
  // sampling with a grid-search fallback), per this app's established
  // "copy-adapt when the engine differs" convention, since here the box is
  // a small fixed rectangle rather than the whole stage.
  function merkFieldBounds() {
    const rect = els.merkField.getBoundingClientRect();
    const w = rect.width || 320, h = rect.height || 260;
    const half = MERK_ITEM_PX / 2;
    return { w, h, minX: half + 4, maxX: Math.max(half + 4, w - half - 4), minY: half + 4, maxY: Math.max(half + 4, h - half - 4) };
  }
  function merkRandomPixelPosition(existingPx, bounds) {
    for (let attempt = 0; attempt < 300; attempt++) {
      const x = bounds.minX + Math.random() * (bounds.maxX - bounds.minX);
      const y = bounds.minY + Math.random() * (bounds.maxY - bounds.minY);
      if (!existingPx.some((p) => Math.hypot(p.x - x, p.y - y) < MERK_MIN_CENTER_PX)) return { x, y };
    }
    let best = null, bestDist = -1;
    const STEPS = 20;
    for (let gx = 0; gx <= STEPS; gx++) {
      for (let gy = 0; gy <= STEPS; gy++) {
        const x = bounds.minX + (gx / STEPS) * (bounds.maxX - bounds.minX);
        const y = bounds.minY + (gy / STEPS) * (bounds.maxY - bounds.minY);
        const dist = existingPx.length ? Math.min(...existingPx.map((p) => Math.hypot(p.x - x, p.y - y))) : Infinity;
        if (dist > bestDist) { bestDist = dist; best = { x, y }; }
      }
    }
    return best;
  }
  function buildMerkLayout(n, bounds) {
    const existingPx = [];
    const positions = [];
    for (let i = 0; i < n; i++) {
      const px = merkRandomPixelPosition(existingPx, bounds);
      existingPx.push(px);
      positions.push({ x: (px.x / bounds.w) * 100, y: (px.y / bounds.h) * 100 });
    }
    return positions;
  }
  function shuffledPalette() {
    const arr = MERK_PALETTE.slice();
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }
  function merkRenderItems(items) {
    els.merkField.innerHTML = "";
    items.forEach((it) => {
      const el = document.createElement("div");
      el.className = "merk-item";
      el.style.left = it.x + "%";
      el.style.top = it.y + "%";
      el.style.background = it.color;
      els.merkField.appendChild(el);
    });
  }
  function merkClearField() { els.merkField.innerHTML = ""; }

  let merkState = null;
  function startMerkGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.merkPlayer.hidden = false;
    els.merkPlayerBar.hidden = false;
    els.merkDonePanel.hidden = true;
    els.merkPauseOverlay.hidden = true;
    els.merkPauseBtn.hidden = false;
    applyMerkBg();
    merkClearField();
    els.merkSameBtn.classList.remove("correct", "wrong");
    els.merkChangedBtn.classList.remove("correct", "wrong");
    merkState = {
      diff: MERK_DIFFICULTIES[merkPrefs.difficulty], trials: buildMerkTrials(), index: -1, phase: "gap", responded: false,
      hits: 0, misses: 0, falseAlarms: 0, correctRejections: 0,
      items: null, paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    els.merkHint.textContent = "Bereit? Gleich geht's los …";
    els.merkProgressEl.textContent = `0/${merkState.trials.length}`;
    requestWakeLock();
    // Measure the field's real box only once it's actually visible (same
    // "no rAF wait needed once unhidden" trick Trail/MOT rely on), then keep
    // reusing those bounds for every trial's fresh layout - the box itself
    // never resizes mid-run.
    requestAnimationFrame(() => {
      if (!merkState) return;
      merkState.bounds = merkFieldBounds();
      scheduleMerkTimer(merkNextTrial, 1200);
    });
  }
  els.merkReadyStartBtn.addEventListener("click", startMerkGame);

  function merkNextTrial() {
    if (!merkState) return;
    merkState.index++;
    if (merkState.index >= merkState.trials.length) { merkFinish(); return; }
    els.merkProgressEl.textContent = `${merkState.index + 1}/${merkState.trials.length}`;
    merkState.phase = "gap";
    merkState.responded = false;
    merkClearField();
    els.merkHint.textContent = "";
    els.merkSameBtn.classList.remove("correct", "wrong");
    els.merkChangedBtn.classList.remove("correct", "wrong");
    const isi = MERK_ISI_MIN + Math.random() * (MERK_ISI_MAX - MERK_ISI_MIN);
    scheduleMerkTimer(merkShowStudy, isi);
  }
  function merkShowStudy() {
    if (!merkState) return;
    const n = merkState.diff.n;
    const positions = buildMerkLayout(n, merkState.bounds);
    const colors = shuffledPalette().slice(0, n);
    merkState.items = positions.map((p, i) => ({ x: p.x, y: p.y, color: colors[i] }));
    merkState.phase = "study";
    merkRenderItems(merkState.items);
    scheduleMerkTimer(merkShowRetention, MERK_STUDY_MS);
  }
  function merkShowRetention() {
    if (!merkState) return;
    merkState.phase = "retention";
    merkClearField();
    scheduleMerkTimer(merkShowTest, MERK_RETENTION_MS);
  }
  function merkShowTest() {
    if (!merkState) return;
    const trial = merkState.trials[merkState.index];
    let testItems = merkState.items.map((it) => ({ x: it.x, y: it.y, color: it.color }));
    if (trial.changed) {
      const idx = Math.floor(Math.random() * testItems.length);
      const usedColors = merkState.items.map((it) => it.color);
      const spare = MERK_PALETTE.filter((c) => !usedColors.includes(c));
      testItems[idx].color = spare[Math.floor(Math.random() * spare.length)];
    }
    merkState.phase = "responding";
    merkState.responded = false;
    merkState.stimAt = performance.now();
    merkRenderItems(testItems);
  }
  function merkTap(saidChanged) {
    if (!merkState || merkState.paused || merkState.responded) return;
    if (merkState.phase !== "responding") return;
    merkState.responded = true;
    const trial = merkState.trials[merkState.index];
    const correct = saidChanged === trial.changed;
    if (trial.changed) { if (correct) merkState.hits++; else merkState.misses++; }
    else { if (correct) merkState.correctRejections++; else merkState.falseAlarms++; }
    const btn = saidChanged ? els.merkChangedBtn : els.merkSameBtn;
    btn.classList.add(correct ? "correct" : "wrong");
    if (!correct) els.merkHint.textContent = "Leider falsch!";
    scheduleMerkTimer(merkNextTrial, MERK_FEEDBACK_MS);
  }
  els.merkSameBtn.addEventListener("click", () => merkTap(false));
  els.merkChangedBtn.addEventListener("click", () => merkTap(true));

  // Pause just stops/replays the pending timer, no live background-adjust
  // overlay - background colour customisation was skipped for this exercise
  // (explicitly optional per the Test-Bereich guidance) so there is nothing
  // to adjust while paused. Pausing during the untimed "responding" phase
  // works too - merkState.timer is simply null then (nothing pending), same
  // as UFOV's own untimed response-phase pause.
  function pauseMerk() {
    if (!merkState || merkState.paused) return;
    merkState.paused = true;
    merkState.pausedAt = performance.now();
    if (merkState.timer) {
      clearTimeout(merkState.timer);
      merkState.timer = null;
      merkState.timerRemainingMs = Math.max(0, merkState.timerFiresAt - merkState.pausedAt);
    }
    els.merkPauseBtn.hidden = true;
    els.merkPauseOverlay.hidden = false;
  }
  function resumeMerk() {
    if (!merkState || !merkState.paused) return;
    const pausedMs = performance.now() - merkState.pausedAt;
    merkState.startTime += pausedMs;
    if (merkState.stimAt) merkState.stimAt += pausedMs;
    merkState.paused = false;
    if (merkState.timerFn && merkState.timerRemainingMs != null) {
      scheduleMerkTimer(merkState.timerFn, merkState.timerRemainingMs);
      merkState.timerRemainingMs = null;
    }
    els.merkPauseOverlay.hidden = true;
    els.merkPauseBtn.hidden = false;
  }
  els.merkPauseBtn.addEventListener("click", pauseMerk);
  els.merkResumeBtn.addEventListener("click", resumeMerk);

  function finalizeMerkRun(state, totalTrials) {
    els.merkPauseOverlay.hidden = true;
    els.merkPlayerBar.hidden = true;
    const changeTrials = state.hits + state.misses;
    const noChangeTrials = state.falseAlarms + state.correctRejections;
    const hitRate = changeTrials ? state.hits / changeTrials : 0;
    const faRate = noChangeTrials ? state.falseAlarms / noChangeTrials : 0;
    const n = state.diff.n;
    // Pashler's K - the capacity estimate for a whole-display "did anything
    // change" judgment (Pashler, 1988), clamped to [0, n] since a poor-enough
    // false-alarm rate can otherwise push the raw formula negative or above
    // the array size at these small trial counts.
    const rawK = faRate >= 1 ? 0 : n * (hitRate - faRate) / (1 - faRate);
    const k = Math.max(0, Math.min(n, Math.round(rawK * 10) / 10));
    const accuracyPct = Math.round(100 * (state.hits + state.correctRejections) / totalTrials);
    const isRecord = saveMerkBest(k);
    renderMerkBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.merkDoneSummary.textContent =
      `Merkspanne-Test (${state.diff.title}) · ${accuracyPct}% richtig · Kapazität (K) ${k} von ${n} Objekten` +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig, K ${k}/${n}`;
    const id = addHistory({ kind: "merk", title: "Merkspanne-Test (Change Detection)", seconds: Math.round(played), note });
    renderRating(els.merkRating, id, "Wie sicher hast du dich gefühlt?");
    els.merkDonePanel.hidden = false;
  }
  function merkFinish() {
    if (!merkState) return;
    const state = merkState;
    merkState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.merkPlayer) document.exitFullscreen().catch(() => {});
    els.merkFsHint.hidden = true;
    finalizeMerkRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function merkStop() {
    if (!merkState) return;
    if (merkState.timer) clearTimeout(merkState.timer);
    const state = merkState;
    merkState = null;
    els.merkPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.merkPlayer) document.exitFullscreen().catch(() => {});
    els.merkFsHint.hidden = true;
    const resolved = state.hits + state.misses + state.falseAlarms + state.correctRejections;
    if (resolved >= 4) {
      finalizeMerkRun(state, resolved);
    } else {
      els.merkPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.merkBackBtn.addEventListener("click", merkStop);
  els.merkAgainBtn.addEventListener("click", () => { els.merkDonePanel.hidden = true; startMerkGame(); });
  els.merkDoneBackBtn.addEventListener("click", () => { els.merkPlayer.hidden = true; els.merkDonePanel.hidden = true; showScreen("testHome"); });

  // ==== Test-Bereich: Farbkonflikt-Test (Simon-Aufgabe) ====
  // Ninth autonomous entry (see CLAUDE.md's "Test-Bereich (autonomous,
  // ongoing)"). Grounded in the Simon task (Simon & Rudell, 1967; Simon,
  // 1969): a stimulus's IRRELEVANT spatial position (here: which of two
  // slots a coloured dot appears in) automatically activates a response
  // tendency toward that same side, even though the actual instructed
  // response is determined by something else entirely (here: the dot's
  // colour, mapped to a fixed left/right button that never moves during a
  // run). When the automatically-activated side and the instructed side
  // agree ("congruent") responses are fast; when they conflict
  // ("incongruent") responses are slower and more error-prone - the classic
  // "Simon effect", a pure measure of resolving an automatic spatial S-R
  // (stimulus-response) conflict. Also researched as sport-relevant before
  // building: open-skill-sport athletes (e.g. futsal players) show reduced
  // Simon-effect interference versus non-athletes, and action-video-game
  // training has been shown to shrink the Simon effect too - both point to
  // this specific kind of interference control being trainable, a good fit
  // for FWMC's "visuelle Entscheidungsgeschwindigkeit" focus. Genuinely
  // distinct from every existing Test/NAT mechanic: Flanker's conflict comes
  // from simultaneous DISTRACTOR STIMULI around a central target (the
  // target's identity itself is never in question, only what surrounds it);
  // Posner-Cueing tests voluntarily/endogenously shifting attention between
  // two known locations after an explicit cue; Simon's conflict instead
  // comes from the single target STIMULUS's own task-irrelevant location
  // automatically priming a response side, entirely without any cue,
  // distractor, or shift instruction - a third, complementary facet of
  // interference control alongside those two.
  const SIMON_PREFS_KEY = "fwmc-simon-prefs-v1";
  // Difficulty controls the response window and inter-trial gap - same
  // shape and the same numbers as FLANKER_DIFFICULTIES (a single-stimulus,
  // immediate-response task of comparable cognitive load).
  const SIMON_DIFFICULTIES = {
    leicht: { title: "Leicht", responseMs: 2200, isiMin: 900, isiMax: 1400 },
    mittel: { title: "Mittel", responseMs: 1600, isiMin: 700, isiMax: 1100 },
    schwer: { title: "Schwer", responseMs: 1100, isiMin: 500, isiMax: 900 },
  };
  // 40 trials, a full 2x2 design (colour x side) balanced 10 each way - 20
  // congruent / 20 incongruent, 20 blue / 20 orange, 20 left / 20 right -
  // enough per condition for a meaningful congruent-vs-incongruent RT
  // comparison, matching Posner-Cueing's own trial count.
  const SIMON_TRIAL_COUNT = 40;
  const simonPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadSimonPrefs() {
    const saved = readJSON(SIMON_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(simonPrefs, saved);
    if (!SIMON_DIFFICULTIES[simonPrefs.difficulty]) simonPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[simonPrefs.bgColorKey]) simonPrefs.bgColorKey = "gruen";
    if (typeof simonPrefs.bgIntensity !== "number" || simonPrefs.bgIntensity < 0 || simonPrefs.bgIntensity > 1) simonPrefs.bgIntensity = 0;
  }
  loadSimonPrefs();
  function saveSimonPrefsToStorage() { writeJSON(SIMON_PREFS_KEY, simonPrefs); }

  // Background colour/intensity, added later (client asked every Test-Bereich
  // exercise get the same background customisation NAT's Remember/Blitz/
  // Flash/MOT already have) - see CLAUDE.md Established patterns for the
  // scope decision (no transfer/preset-save here, unlike those four). The
  // tint goes on the outer #simonStage - the blue/orange stimulus dot lives
  // inside its own neutral, fixed-background `.simon-slot` box (already
  // audited as safe: the background sits behind that box, never on the dot
  // itself), so this never touches the response-mapped colour signal.
  function applySimonBg() {
    els.simonStage.style.background = simonPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[simonPrefs.bgColorKey].hex, simonPrefs.bgIntensity)
      : "";
  }
  const syncSimonBgUI = wireBgIntensityControl(simonPrefs, {
    pickers: [els.simonBgColorPicker, els.simonPauseBgColorPicker],
    sliders: [els.simonBgIntensitySlider, els.simonPauseBgSlider],
    valueEls: [els.simonBgIntensityValue, els.simonPauseBgValue],
    hintEls: [els.simonBgContrastHint],
  }, () => { saveSimonPrefsToStorage(); applySimonBg(); });

  const SIMON_BEST_KEY = "fwmc-simon-best-v1"; // { [difficulty]: bestAccuracyPct }
  function simonBestFor() { return readJSON(SIMON_BEST_KEY, {})[simonPrefs.difficulty] || 0; }
  function saveSimonBest(accuracyPct) {
    const all = readJSON(SIMON_BEST_KEY, {});
    if (accuracyPct > (all[simonPrefs.difficulty] || 0)) { all[simonPrefs.difficulty] = accuracyPct; writeJSON(SIMON_BEST_KEY, all); return true; }
    return false;
  }
  function renderSimonBest() {
    const best = simonBestFor();
    const text = best ? `Beste Genauigkeit (${SIMON_DIFFICULTIES[simonPrefs.difficulty].title}): ${best}%` : "";
    els.simonBestHint.textContent = text;
    els.simonReadyBestHint.textContent = text;
  }
  function syncSimonDifficultyUI() {
    els.simonDifficultyRow.querySelectorAll("[data-simon-diff]").forEach((btn) => setActive(btn, btn.dataset.simonDiff === simonPrefs.difficulty));
  }
  els.simonDifficultyRow.querySelectorAll("[data-simon-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      simonPrefs.difficulty = btn.dataset.simonDiff;
      saveSimonPrefsToStorage();
      syncSimonDifficultyUI();
      renderSimonBest();
    });
  });

  els.simonOpenBtn.addEventListener("click", () => {
    syncSimonDifficultyUI();
    syncSimonBgUI();
    renderSimonBest();
    showScreen("simonReady");
  });
  els.simonReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleFlankerTimer/schedulePosnerTimer:
  // records what's pending and when it fires, so Pause can cancel it and
  // Resume can replay it with its exact remaining delay.
  function scheduleSimonTimer(fn, delayMs) {
    simonState.timerFn = fn;
    simonState.timerFiresAt = performance.now() + delayMs;
    simonState.timer = setTimeout(() => { simonState.timer = null; fn(); }, delayMs);
  }

  // The fixed colour->response-side mapping for the whole run: Blau is
  // always the LEFT button, Orange always the RIGHT button (matches
  // simonLeftBtn/simonRightBtn's fixed on-screen position). "congruent"
  // means the dot's on-screen SIDE happens to match that colour's button
  // side too - the one thing this task actually varies independently of the
  // instructed (colour) response.
  function simonCorrectSide(color) { return color === "blue" ? "left" : "right"; }
  function buildSimonTrials() {
    const trials = [];
    ["blue", "orange"].forEach((color) => {
      ["left", "right"].forEach((side) => {
        for (let i = 0; i < SIMON_TRIAL_COUNT / 4; i++) trials.push({ color, side });
      });
    });
    // Shuffle, then avoid more than 3 identical CORRECT (colour-determined)
    // responses back to back - same guard as buildFlankerTrials/
    // buildPosnerTrials, so a "just keep pressing the same button" motor
    // strategy can't pass undetected.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < trials.length; i++) {
        if (simonCorrectSide(trials[i].color) === simonCorrectSide(trials[i - 1].color)) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return trials;
  }

  function simonClearStage() {
    els.simonDotLeft.classList.remove("show", "simon-dot-blue", "simon-dot-orange");
    els.simonDotRight.classList.remove("show", "simon-dot-blue", "simon-dot-orange");
    els.simonLeftBtn.classList.remove("correct", "wrong");
    els.simonRightBtn.classList.remove("correct", "wrong");
  }
  function simonDotFor(side) { return side === "left" ? els.simonDotLeft : els.simonDotRight; }
  function simonBtnFor(side) { return side === "left" ? els.simonLeftBtn : els.simonRightBtn; }

  let simonState = null;
  function startSimonGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.simonPlayer.hidden = false;
    els.simonPlayerBar.hidden = false;
    els.simonDonePanel.hidden = true;
    els.simonPauseOverlay.hidden = true;
    els.simonPauseBtn.hidden = false;
    simonState = {
      diff: SIMON_DIFFICULTIES[simonPrefs.difficulty], trials: buildSimonTrials(), index: -1, phase: "gap", responded: false,
      correct: 0, incorrect: 0, timeouts: 0, rtsCongruent: [], rtsIncongruent: [],
      stimAt: 0, paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    applySimonBg();
    simonClearStage();
    els.simonHint.textContent = "Bereit? Gleich geht's los …";
    els.simonProgressEl.textContent = `0/${simonState.trials.length}`;
    requestWakeLock();
    scheduleSimonTimer(simonNextTrial, 1200);
  }
  els.simonReadyStartBtn.addEventListener("click", startSimonGame);

  function simonNextTrial() {
    if (!simonState) return;
    simonState.index++;
    if (simonState.index >= simonState.trials.length) { simonFinish(); return; }
    els.simonProgressEl.textContent = `${simonState.index + 1}/${simonState.trials.length}`;
    simonState.phase = "gap";
    simonState.responded = false;
    simonClearStage();
    const isi = simonState.diff.isiMin + Math.random() * (simonState.diff.isiMax - simonState.diff.isiMin);
    scheduleSimonTimer(simonShowStimulus, isi);
  }
  function simonShowStimulus() {
    if (!simonState) return;
    const trial = simonState.trials[simonState.index];
    simonState.phase = "responding";
    simonState.responded = false;
    simonState.stimAt = performance.now();
    els.simonHint.textContent = "";
    simonClearStage();
    simonDotFor(trial.side).classList.add("show", `simon-dot-${trial.color}`);
    scheduleSimonTimer(simonEndTrial, simonState.diff.responseMs);
  }
  function simonEndTrial() {
    if (!simonState) return;
    if (simonState.phase === "responding" && !simonState.responded) {
      simonState.incorrect++;
      simonState.timeouts++;
      els.simonHint.textContent = "Verpasst!";
    }
    simonState.phase = "gap";
    simonNextTrial();
  }
  function simonTap(side) {
    if (!simonState || simonState.paused || simonState.responded) return;
    // Taps before the dot actually appears are ignored - reaction time is
    // measured stimulus-locked, same convention as Flanker's/Posner's own
    // tap handlers.
    if (simonState.phase !== "responding") return;
    simonState.responded = true;
    const trial = simonState.trials[simonState.index];
    const rt = performance.now() - simonState.stimAt;
    const correctSide = simonCorrectSide(trial.color);
    const correct = side === correctSide;
    const congruent = trial.side === correctSide;
    simonBtnFor(side).classList.add(correct ? "correct" : "wrong");
    if (correct) {
      simonState.correct++;
      (congruent ? simonState.rtsCongruent : simonState.rtsIncongruent).push(rt);
    } else {
      simonState.incorrect++;
      els.simonHint.textContent = "Falsche Farbe!";
    }
    // The feedback ring stays up for whatever's left of diff.responseMs (the
    // already-scheduled simonEndTrial fires the actual transition) - same
    // rhythm as Flanker/Posner leaving their own tap feedback up for the
    // rest of the response window, no separate timer needed.
  }
  els.simonLeftBtn.addEventListener("click", () => simonTap("left"));
  els.simonRightBtn.addEventListener("click", () => simonTap("right"));

  // Pause just stops/replays the pending timer, no live background-adjust
  // overlay - background colour customisation was skipped for this exercise
  // (explicitly optional per the Test-Bereich guidance) so there is nothing
  // to adjust while paused.
  function pauseSimon() {
    if (!simonState || simonState.paused) return;
    simonState.paused = true;
    simonState.pausedAt = performance.now();
    if (simonState.timer) {
      clearTimeout(simonState.timer);
      simonState.timer = null;
      simonState.timerRemainingMs = Math.max(0, simonState.timerFiresAt - simonState.pausedAt);
    }
    els.simonPauseBtn.hidden = true;
    els.simonPauseOverlay.hidden = false;
  }
  function resumeSimon() {
    if (!simonState || !simonState.paused) return;
    const pausedMs = performance.now() - simonState.pausedAt;
    simonState.startTime += pausedMs;
    simonState.stimAt += pausedMs;
    simonState.paused = false;
    if (simonState.timerFn && simonState.timerRemainingMs != null) {
      scheduleSimonTimer(simonState.timerFn, simonState.timerRemainingMs);
      simonState.timerRemainingMs = null;
    }
    els.simonPauseOverlay.hidden = true;
    els.simonPauseBtn.hidden = false;
  }
  els.simonPauseBtn.addEventListener("click", pauseSimon);
  els.simonResumeBtn.addEventListener("click", resumeSimon);

  function finalizeSimonRun(state, totalTrials) {
    els.simonPauseOverlay.hidden = true;
    els.simonPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const avgCong = avgOf(state.rtsCongruent);
    const avgIncong = avgOf(state.rtsIncongruent);
    // The "Simon effect" itself: how much slower correct incongruent
    // responses were versus correct congruent ones - the classic spatial
    // S-R-conflict cost this paradigm exists to surface.
    const simonEffect = (avgCong != null && avgIncong != null) ? (avgIncong - avgCong) : null;
    const isRecord = saveSimonBest(accuracyPct);
    renderSimonBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.simonDoneSummary.textContent =
      `Farbkonflikt-Test (${state.diff.title}) · ${accuracyPct}% richtig` +
      (avgCong != null ? ` · Ø kongruent ${avgCong} ms` : "") +
      (avgIncong != null ? ` · Ø inkongruent ${avgIncong} ms` : "") +
      (simonEffect != null ? ` · Simon-Effekt ${simonEffect} ms` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` + (simonEffect != null ? `, Simon-Effekt ${simonEffect} ms` : "");
    const id = addHistory({ kind: "simon", title: "Farbkonflikt-Test (Simon-Aufgabe)", seconds: Math.round(played), note });
    renderRating(els.simonRating, id, "Wie fokussiert warst du?");
    els.simonDonePanel.hidden = false;
  }
  function simonFinish() {
    if (!simonState) return;
    const state = simonState;
    simonState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.simonPlayer) document.exitFullscreen().catch(() => {});
    els.simonFsHint.hidden = true;
    finalizeSimonRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function simonStop() {
    if (!simonState) return;
    if (simonState.timer) clearTimeout(simonState.timer);
    const state = simonState;
    simonState = null;
    els.simonPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.simonPlayer) document.exitFullscreen().catch(() => {});
    els.simonFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= 4) {
      finalizeSimonRun(state, resolved);
    } else {
      els.simonPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.simonBackBtn.addEventListener("click", simonStop);
  els.simonAgainBtn.addEventListener("click", () => { els.simonDonePanel.hidden = true; startSimonGame(); });
  els.simonDoneBackBtn.addEventListener("click", () => { els.simonPlayer.hidden = true; els.simonDonePanel.hidden = true; showScreen("testHome"); });

  // ==== Test-Bereich: Suchtest (Visuelle Suche) ====
  // Tenth autonomous entry (see CLAUDE.md "Test-Bereich (autonomous,
  // ongoing)"). Grounded in the classic visual-search paradigm and
  // Treisman & Gelade's Feature Integration Theory (1980): a single target
  // hides among several distractors; in "Merkmalssuche" (feature search)
  // the target differs from every distractor by ONE salient feature
  // (colour) and "pops out" instantly regardless of how many distractors
  // are on screen (parallel processing, ~flat RT-by-set-size slope); in
  // "Verbindungssuche" (conjunction search) the target is defined by a
  // COMBINATION of two features (colour AND shape) that individually also
  // appear on distractors, forcing a slower, roughly serial item-by-item
  // scan whose reaction time rises with the number of items on screen
  // (Treisman & Gelade's own colour-conjunction data implies a slope on the
  // order of ~25-30ms per added item - cited as "28.7 ms" in later
  // reanalyses). This exercise runs both conditions across three set sizes
  // in one balanced run and reports the actual set-size SLOPE per
  // condition (ms per added object), not just accuracy/RT - the real
  // outcome measure this paradigm exists to surface, and a genuinely new
  // kind of result on this Test tab (every other exercise reports a flat
  // average or a single interference cost, not a slope). Also researched
  // as sport-relevant: a 2026 Frontiers systematic review/meta-analysis
  // found expert athletes show more EFFICIENT visual search than novices -
  // fewer but more informative fixations and better foveal/peripheral
  // coordination - a direct fit for FWMC's "visuelle
  // Entscheidungsgeschwindigkeit" and peripheral-vision focus specifically.
  // Genuinely distinct from every existing Test/NAT mechanic: MOT tracks
  // moving objects that stay identical the whole time; Trail Making scans
  // a scattered layout in a KNOWN ascending order; UFOV is a brief-glance
  // divided-attention judgement with no active scanning at all (everything
  // is masked before the eyes could move) - this is the only exercise
  // whose stimulus display stays up and static while the client actively
  // searches it, the textbook visual-search setup.
  const SEARCH_PREFS_KEY = "fwmc-search-prefs-v1";
  const SEARCH_LENGTHS = {
    kurz: { title: "Kurz", reps: 2 },
    mittel: { title: "Mittel", reps: 4 },
    lang: { title: "Lang", reps: 6 },
  };
  const SEARCH_SET_SIZES = { klein: 6, mittel: 12, gross: 18 }; // total items on stage, target included
  const SEARCH_MODES = ["feature", "conjunction"];
  const SEARCH_CUE_MS = 700; // target-definition text shown before the array appears, so RT is measured from array onset, not from reading the cue
  const SEARCH_ISI_MIN = 300, SEARCH_ISI_MAX = 500; // brief blank gap before the next cue
  const SEARCH_FEEDBACK_MS = 550;
  const SEARCH_TIMEOUT_MS = 8000; // generous safety net, not the driver of pacing - this is a self-paced "search until found" task, unlike the fixed-response-window exercises elsewhere on this tab
  const SEARCH_MIN_RESOLVED = 4;
  const SEARCH_ITEM_PX = 34;
  const SEARCH_MIN_CENTER_PX = SEARCH_ITEM_PX + 12;
  const SEARCH_COLOR_TARGET = "#d64545";
  const SEARCH_COLOR_DISTRACTOR = "#8a97a3";
  const searchPrefs = { length: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadSearchPrefs() {
    const saved = readJSON(SEARCH_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(searchPrefs, saved);
    if (!SEARCH_LENGTHS[searchPrefs.length]) searchPrefs.length = "mittel";
    if (!STROOP_COLOR_BY_KEY[searchPrefs.bgColorKey]) searchPrefs.bgColorKey = "gruen";
    if (typeof searchPrefs.bgIntensity !== "number" || searchPrefs.bgIntensity < 0 || searchPrefs.bgIntensity > 1) searchPrefs.bgIntensity = 0;
  }
  loadSearchPrefs();
  function saveSearchPrefsToStorage() { writeJSON(SEARCH_PREFS_KEY, searchPrefs); }

  // Background colour/intensity, added later (client asked every Test-Bereich
  // exercise get the same background customisation NAT's Remember/Blitz/
  // Flash/MOT already have) - see CLAUDE.md Established patterns for the
  // scope decision (no transfer/preset-save here, unlike those four). The
  // target/distractor items sit directly on #searchStage with no neutral box
  // around them (audited and approved - the tint is always mixed toward
  // white, per mixHex, never full saturation, keeping contrast usable).
  function applySearchBg() {
    els.searchStage.style.background = searchPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[searchPrefs.bgColorKey].hex, searchPrefs.bgIntensity)
      : "";
  }
  const syncSearchBgUI = wireBgIntensityControl(searchPrefs, {
    pickers: [els.searchBgColorPicker, els.searchPauseBgColorPicker],
    sliders: [els.searchBgIntensitySlider, els.searchPauseBgSlider],
    valueEls: [els.searchBgIntensityValue, els.searchPauseBgValue],
    hintEls: [els.searchBgContrastHint],
  }, () => { saveSearchPrefsToStorage(); applySearchBg(); });

  const SEARCH_BEST_KEY = "fwmc-search-best-v1"; // { [length]: bestAccuracyPct }
  function searchBestFor() { return readJSON(SEARCH_BEST_KEY, {})[searchPrefs.length] || 0; }
  function saveSearchBest(accuracyPct) {
    const all = readJSON(SEARCH_BEST_KEY, {});
    if (accuracyPct > (all[searchPrefs.length] || 0)) { all[searchPrefs.length] = accuracyPct; writeJSON(SEARCH_BEST_KEY, all); return true; }
    return false;
  }
  function renderSearchBest() {
    const best = searchBestFor();
    const text = best ? `Beste Genauigkeit (${SEARCH_LENGTHS[searchPrefs.length].title}): ${best}%` : "";
    els.searchBestHint.textContent = text;
    els.searchReadyBestHint.textContent = text;
  }
  function syncSearchLengthUI() {
    els.searchLengthRow.querySelectorAll("[data-search-length]").forEach((btn) => setActive(btn, btn.dataset.searchLength === searchPrefs.length));
  }
  els.searchLengthRow.querySelectorAll("[data-search-length]").forEach((btn) => {
    btn.addEventListener("click", () => {
      searchPrefs.length = btn.dataset.searchLength;
      saveSearchPrefsToStorage();
      syncSearchLengthUI();
      renderSearchBest();
    });
  });
  els.searchOpenBtn.addEventListener("click", () => {
    syncSearchLengthUI();
    syncSearchBgUI();
    renderSearchBest();
    showScreen("searchReady");
  });
  els.searchReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Single active timer, remaining-delay pause/resume - same shape as every
  // other setTimeout-driven Test exercise. Unlike Simon/Flanker (a fixed
  // response window that always runs its full length before advancing),
  // this task can transition to the NEXT phase early (as soon as the
  // client taps something), so - unlike scheduleSimonTimer - this always
  // clears any still-pending timer first, or an old, no-longer-relevant
  // timeout could fire later on top of an already-advanced trial.
  function scheduleSearchTimer(fn, delayMs) {
    if (searchState.timer) clearTimeout(searchState.timer);
    searchState.timerFn = fn;
    searchState.timerFiresAt = performance.now() + delayMs;
    searchState.timer = setTimeout(() => { searchState.timer = null; fn(); }, delayMs);
  }

  function buildSearchTrials() {
    const reps = SEARCH_LENGTHS[searchPrefs.length].reps;
    const sizeKeys = Object.keys(SEARCH_SET_SIZES);
    const trials = [];
    SEARCH_MODES.forEach((mode) => {
      sizeKeys.forEach((sizeKey) => {
        for (let i = 0; i < reps; i++) trials.push({ mode, sizeKey, setSize: SEARCH_SET_SIZES[sizeKey] });
      });
    });
    // Shuffle, then avoid more than 3 identical MODES back to back - same
    // guard as buildSimonTrials/buildFlankerTrials/buildPosnerTrials, so a
    // long run of "same kind of search" can't cluster by chance.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < trials.length; i++) {
        if (trials[i].mode === trials[i - 1].mode) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return trials;
  }

  // Feature search: every distractor is a plain grey circle, the target is
  // the only RED circle - a single feature (colour) makes it pop out.
  // Conjunction search: the target is a red SQUARE; distractors are split
  // between red circles (share colour with the target) and grey squares
  // (share shape with the target) - the classic Treisman construction
  // where no single feature is unique, forcing an item-by-item scan.
  function buildSearchItems(mode, setSize, rng) {
    const items = [];
    if (mode === "feature") {
      for (let i = 0; i < setSize - 1; i++) items.push({ shape: "circle", color: SEARCH_COLOR_DISTRACTOR, isTarget: false });
      items.push({ shape: "circle", color: SEARCH_COLOR_TARGET, isTarget: true });
    } else {
      const distractorCount = setSize - 1;
      const groupA = Math.ceil(distractorCount / 2); // red circles
      const groupB = distractorCount - groupA; // grey squares
      for (let i = 0; i < groupA; i++) items.push({ shape: "circle", color: SEARCH_COLOR_TARGET, isTarget: false });
      for (let i = 0; i < groupB; i++) items.push({ shape: "square", color: SEARCH_COLOR_DISTRACTOR, isTarget: false });
      items.push({ shape: "square", color: SEARCH_COLOR_TARGET, isTarget: true });
    }
    for (let i = items.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [items[i], items[j]] = [items[j], items[i]];
    }
    return items;
  }
  function searchTargetLabel(mode) { return mode === "feature" ? "Roter Kreis" : "Rotes Quadrat"; }

  // Anti-overlap scatter placement across the whole stage - copy-adapted
  // from Trail Making's own trailRandomPixelPosition/trailStageBounds
  // (rejection sampling with a grid-search fallback), per this app's
  // established "copy-adapt when the engine differs" convention, since
  // this stage needs its own item size/margins for up to 18 items at once.
  function searchStageBounds() {
    const rect = els.searchStage.getBoundingClientRect();
    const w = rect.width || 390, h = rect.height || 600;
    const half = SEARCH_ITEM_PX / 2;
    const minY = stageTopClearanceY(rect, els.searchHint, els.searchPlayerBar, 84, half);
    return { w, h, minX: half + 8, maxX: Math.max(half + 8, w - half - 8), minY, maxY: Math.max(minY, h - 16) };
  }
  function searchRandomPixelPosition(existingPx, bounds) {
    for (let attempt = 0; attempt < 300; attempt++) {
      const x = bounds.minX + Math.random() * (bounds.maxX - bounds.minX);
      const y = bounds.minY + Math.random() * (bounds.maxY - bounds.minY);
      if (!existingPx.some((p) => Math.hypot(p.x - x, p.y - y) < SEARCH_MIN_CENTER_PX)) return { x, y };
    }
    let best = null, bestDist = -1;
    const STEPS = 24;
    for (let gx = 0; gx <= STEPS; gx++) {
      for (let gy = 0; gy <= STEPS; gy++) {
        const x = bounds.minX + (gx / STEPS) * (bounds.maxX - bounds.minX);
        const y = bounds.minY + (gy / STEPS) * (bounds.maxY - bounds.minY);
        const dist = existingPx.length ? Math.min(...existingPx.map((p) => Math.hypot(p.x - x, p.y - y))) : Infinity;
        if (dist > bestDist) { bestDist = dist; best = { x, y }; }
      }
    }
    return best;
  }
  function buildSearchLayout(n) {
    const bounds = searchStageBounds();
    const existingPx = [];
    const positions = [];
    for (let i = 0; i < n; i++) {
      const px = searchRandomPixelPosition(existingPx, bounds);
      existingPx.push(px);
      positions.push({ x: (px.x / bounds.w) * 100, y: (px.y / bounds.h) * 100 });
    }
    return positions;
  }
  function renderSearchItems(itemDefs, positions) {
    els.searchItemsLayer.innerHTML = "";
    itemDefs.forEach((it, i) => {
      const el = document.createElement("button");
      el.className = `search-item shape-${it.shape}`;
      el.style.left = positions[i].x + "%";
      el.style.top = positions[i].y + "%";
      el.style.background = it.color;
      el.dataset.target = it.isTarget ? "1" : "0";
      el.addEventListener("click", () => searchTapItem(it, el));
      els.searchItemsLayer.appendChild(el);
    });
  }
  function searchRevealTarget() {
    const el = Array.from(els.searchItemsLayer.children).find((c) => c.dataset.target === "1" && !c.classList.contains("correct"));
    if (el) el.classList.add("reveal");
  }

  function searchSlope(rtBySize) {
    const a = avgOf(rtBySize.klein), b = avgOf(rtBySize.gross);
    if (a == null || b == null) return null;
    return Math.round(((b - a) / (SEARCH_SET_SIZES.gross - SEARCH_SET_SIZES.klein)) * 10) / 10;
  }

  let searchState = null;
  function startSearchGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.searchPlayer.hidden = false;
    els.searchPlayerBar.hidden = false;
    els.searchDonePanel.hidden = true;
    els.searchPauseOverlay.hidden = true;
    els.searchPauseBtn.hidden = false;
    els.searchItemsLayer.innerHTML = "";
    searchState = {
      trials: buildSearchTrials(), index: -1, phase: "gap",
      correct: 0, incorrect: 0, timeouts: 0,
      rtByMode: { feature: [], conjunction: [] },
      rtByModeSize: { feature: { klein: [], mittel: [], gross: [] }, conjunction: { klein: [], mittel: [], gross: [] } },
      paused: false, startTime: performance.now(), stimAt: null,
      timer: null, timerFn: null, timerFiresAt: null,
    };
    applySearchBg();
    els.searchHint.textContent = "Bereit? Gleich geht's los …";
    els.searchProgressEl.textContent = `0/${searchState.trials.length}`;
    requestWakeLock();
    scheduleSearchTimer(searchNextTrial, 1000);
  }
  els.searchReadyStartBtn.addEventListener("click", startSearchGame);

  function searchNextTrial() {
    if (!searchState) return;
    searchState.index++;
    if (searchState.index >= searchState.trials.length) { searchFinish(); return; }
    els.searchItemsLayer.innerHTML = "";
    searchState.phase = "cue";
    const trial = searchState.trials[searchState.index];
    els.searchProgressEl.textContent = `${searchState.index + 1}/${searchState.trials.length}`;
    els.searchHint.textContent = `Ziel: ${searchTargetLabel(trial.mode)}`;
    const isi = SEARCH_ISI_MIN + Math.random() * (SEARCH_ISI_MAX - SEARCH_ISI_MIN);
    scheduleSearchTimer(searchShowArray, SEARCH_CUE_MS + isi);
  }
  function searchShowArray() {
    if (!searchState) return;
    const trial = searchState.trials[searchState.index];
    const itemDefs = buildSearchItems(trial.mode, trial.setSize, Math.random);
    const positions = buildSearchLayout(itemDefs.length);
    renderSearchItems(itemDefs, positions);
    searchState.phase = "responding";
    searchState.stimAt = performance.now();
    scheduleSearchTimer(searchTimeoutTrial, SEARCH_TIMEOUT_MS);
  }
  function searchTimeoutTrial() {
    if (!searchState || searchState.phase !== "responding") return;
    searchState.incorrect++;
    searchState.timeouts++;
    searchState.phase = "feedback";
    searchRevealTarget();
    els.searchHint.textContent = "Zeit abgelaufen!";
    scheduleSearchTimer(searchNextTrial, SEARCH_FEEDBACK_MS);
  }
  function searchTapItem(itemDef, el) {
    if (!searchState || searchState.paused || searchState.phase !== "responding") return;
    const trial = searchState.trials[searchState.index];
    const rt = performance.now() - searchState.stimAt;
    searchState.phase = "feedback";
    if (itemDef.isTarget) {
      el.classList.add("correct");
      searchState.correct++;
      searchState.rtByMode[trial.mode].push(rt);
      searchState.rtByModeSize[trial.mode][trial.sizeKey].push(rt);
    } else {
      el.classList.add("wrong");
      searchState.incorrect++;
      searchRevealTarget();
      els.searchHint.textContent = "Daneben!";
    }
    scheduleSearchTimer(searchNextTrial, SEARCH_FEEDBACK_MS);
  }

  function pauseSearch() {
    if (!searchState || searchState.paused) return;
    searchState.paused = true;
    searchState.pausedAt = performance.now();
    if (searchState.timer) {
      clearTimeout(searchState.timer);
      searchState.timer = null;
      searchState.timerRemainingMs = Math.max(0, searchState.timerFiresAt - searchState.pausedAt);
    }
    els.searchPauseBtn.hidden = true;
    els.searchPauseOverlay.hidden = false;
  }
  function resumeSearch() {
    if (!searchState || !searchState.paused) return;
    const pausedMs = performance.now() - searchState.pausedAt;
    searchState.startTime += pausedMs;
    if (searchState.stimAt != null) searchState.stimAt += pausedMs;
    searchState.paused = false;
    if (searchState.timerFn && searchState.timerRemainingMs != null) {
      scheduleSearchTimer(searchState.timerFn, searchState.timerRemainingMs);
      searchState.timerRemainingMs = null;
    }
    els.searchPauseOverlay.hidden = true;
    els.searchPauseBtn.hidden = false;
  }
  els.searchPauseBtn.addEventListener("click", pauseSearch);
  els.searchResumeBtn.addEventListener("click", resumeSearch);

  function finalizeSearchRun(state, totalTrials) {
    els.searchPauseOverlay.hidden = true;
    els.searchPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const featAvg = avgOf(state.rtByMode.feature);
    const conjAvg = avgOf(state.rtByMode.conjunction);
    const featSlope = searchSlope(state.rtByModeSize.feature);
    const conjSlope = searchSlope(state.rtByModeSize.conjunction);
    const isRecord = saveSearchBest(accuracyPct);
    renderSearchBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.searchDoneSummary.textContent =
      `Suchtest (${SEARCH_LENGTHS[searchPrefs.length].title}) · ${accuracyPct}% richtig` +
      (featAvg != null ? ` · Merkmalssuche Ø ${featAvg} ms` : "") +
      (featSlope != null ? ` (${featSlope} ms/Objekt)` : "") +
      (conjAvg != null ? ` · Verbindungssuche Ø ${conjAvg} ms` : "") +
      (conjSlope != null ? ` (${conjSlope} ms/Objekt)` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` +
      (featSlope != null ? `, Merkmalssuche ${featSlope} ms/Objekt` : "") +
      (conjSlope != null ? `, Verbindungssuche ${conjSlope} ms/Objekt` : "");
    const id = addHistory({ kind: "search", title: "Suchtest (Visuelle Suche)", seconds: Math.round(played), note });
    renderRating(els.searchRating, id, "Wie hat sich das Suchen angefühlt?");
    els.searchDonePanel.hidden = false;
  }
  function searchFinish() {
    if (!searchState) return;
    const state = searchState;
    searchState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.searchPlayer) document.exitFullscreen().catch(() => {});
    els.searchFsHint.hidden = true;
    finalizeSearchRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function searchStop() {
    if (!searchState) return;
    if (searchState.timer) clearTimeout(searchState.timer);
    const state = searchState;
    searchState = null;
    els.searchPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.searchPlayer) document.exitFullscreen().catch(() => {});
    els.searchFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= SEARCH_MIN_RESOLVED) {
      finalizeSearchRun(state, resolved);
    } else {
      els.searchPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.searchBackBtn.addEventListener("click", searchStop);
  els.searchAgainBtn.addEventListener("click", () => { els.searchDonePanel.hidden = true; startSearchGame(); });
  els.searchDoneBackBtn.addEventListener("click", () => { els.searchPlayer.hidden = true; els.searchDonePanel.hidden = true; showScreen("testHome"); });

  // Doppelziel-Test (Attentional Blink) - grounded in the classic RSVP
  // (rapid serial visual presentation) attentional-blink paradigm (Raymond,
  // Shapiro & Arnell, 1992): a stream of single letters flashes one at a
  // time at fixation; one letter is coloured (T1, the first target, its
  // colour the only thing that marks it - identity must still be read and
  // remembered) and, at a variable "lag" (number of items) afterwards, the
  // letter X may or may not appear (T2, a fixed, uncoloured target). The
  // hallmark finding: correctly reporting T1 measurably impairs detecting
  // T2 for a brief window afterwards (roughly lag 2-3, ~200-300ms into the
  // stream) even though the eyes see it just fine - attention needs a
  // moment to "recover" and re-engage. Performance is spared at lag 1 (the
  // very next item) and recovers again by lag ~8, so this exercise samples
  // exactly those three points (1/3/8) to make the dip visible rather than
  // sampling every lag in between. Sport-relevant: Enhanced Temporal but
  // Not Attentional Processing in Expert Tennis Players (Overney, Blanke &
  // Herzog, 2008, PLOS ONE) used this exact white-letter-T1/X-as-T2 RSVP
  // design and found expert tennis players process the temporal stream
  // itself faster than novices (though, honestly, not a smaller blink
  // magnitude specifically) - flagged both ways rather than only the
  // flattering half, same spirit as Merkspanne-Test's mixed-evidence note.
  // Separately, a 2012 PNAS study (Choi, Lisberger et al.) found the blink
  // itself can shrink substantially and durably with repeated RSVP
  // practice - the actual rationale for treating this as a trainable
  // exercise rather than a fixed trait. Genuinely distinct from every
  // existing Test/NAT mechanic: every other exercise here presents its
  // stimuli either continuously visible (Merkspanne/Suchtest), one at a
  // time with a real gap between items (Go/No-Go, Flanker, Posner, Simon,
  // Rotationstest), or as a spatial layout (Trail Making, N-Back, Remember,
  // Blitz-Raster) - none of them is a fast, gapless TEMPORAL stream where
  // the very act of recognising one target costs attention needed for the
  // next. Both response questions are asked untimed, after the stream ends
  // (same "wait for a tap, no countdown" convention as UFOV's two
  // post-glance questions) - the whole point is measuring what got through
  // DURING the rapid stream, not adding a second speed pressure on top of
  // it. No Bei-Fehler/background colour/Zusatzaufgabe/Trainingsmodus - all
  // correctly skipped per the "optional, skip what doesn't fit in an hour"
  // guidance (a fixed-trial accuracy test, nothing to configure beyond
  // stream speed).
  const AB_PREFS_KEY = "fwmc-ab-prefs-v1";
  // Difficulty controls the RSVP rate (ms per letter) and the inter-trial
  // gap - same "less time = harder" shape as every other difficulty ladder
  // in this app. 100ms/item (mittel) matches the classic ~10 items/sec RSVP
  // rate used in the original paradigm.
  const AB_DIFFICULTIES = {
    leicht: { title: "Leicht", itemMs: 140, isiMin: 900, isiMax: 1300 },
    mittel: { title: "Mittel", itemMs: 100, isiMin: 700, isiMax: 1100 },
    schwer: { title: "Schwer", itemMs: 70, isiMin: 500, isiMax: 900 },
  };
  // Consonants only (no vowels, no X - X is reserved as the fixed T2
  // identity, never used as a distractor or as T1, so its appearance is
  // always meaningful).
  const AB_LETTERS = ["B", "C", "D", "F", "G", "H", "J", "K", "L", "M", "N", "P", "R", "S", "T", "V", "W", "Z"];
  // The three lags this exercise samples - lag 1 (sparing: the very next
  // item, usually still detected fine), lag 3 (deep in the blink window,
  // the hardest), lag 8 (fully recovered) - rather than the full lag 1-8
  // range real AB studies use, to keep the trial count practical while
  // still making the dip-and-recovery shape visible in the result.
  const AB_LAGS = [1, 3, 8];
  const AB_LEAD_IN = 4; // distractors before T1, so the stream is under way before the coloured target appears
  const AB_TAIL = 3; // distractors after the T2 slot, backward-masking it the same way the real paradigm does
  // 3 lags x (6 T2-present + 2 T2-absent) = 24 trials. The ~25% T2-absent
  // trials are a signal-detection control (without them, always answering
  // "Ja" would score 100% on the T2 question) - same false-alarm-guard
  // logic as every accuracy-scored yes/no judgement in this app.
  const AB_TRIAL_COUNT = AB_LAGS.length * 8;
  const abPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadAbPrefs() {
    const saved = readJSON(AB_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(abPrefs, saved);
    if (!AB_DIFFICULTIES[abPrefs.difficulty]) abPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[abPrefs.bgColorKey]) abPrefs.bgColorKey = "gruen";
    if (typeof abPrefs.bgIntensity !== "number" || abPrefs.bgIntensity < 0 || abPrefs.bgIntensity > 1) abPrefs.bgIntensity = 0;
  }
  loadAbPrefs();
  function saveAbPrefsToStorage() { writeJSON(AB_PREFS_KEY, abPrefs); }

  // Background colour/intensity, added later (client asked every Test-Bereich
  // exercise get the same background customisation NAT's Remember/Blitz/
  // Flash/MOT already have) - see CLAUDE.md Established patterns for the
  // scope decision (no transfer/preset-save here, unlike those four). The
  // T1 accent colour (#007094 teal, see .ab-stream-char.is-t1) sits directly
  // on #abStage with no neutral box around it (audited and approved - the
  // tint is always mixed toward white, per mixHex, never full saturation,
  // keeping contrast usable).
  function applyAbBg() {
    els.abStage.style.background = abPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[abPrefs.bgColorKey].hex, abPrefs.bgIntensity)
      : "";
  }
  const syncAbBgUI = wireBgIntensityControl(abPrefs, {
    pickers: [els.abBgColorPicker, els.abPauseBgColorPicker],
    sliders: [els.abBgIntensitySlider, els.abPauseBgSlider],
    valueEls: [els.abBgIntensityValue, els.abPauseBgValue],
    hintEls: [els.abBgContrastHint],
  }, () => { saveAbPrefsToStorage(); applyAbBg(); });

  const AB_BEST_KEY = "fwmc-ab-best-v1"; // { [difficulty]: bestOverallAccuracyPct }
  function abBestFor() { return readJSON(AB_BEST_KEY, {})[abPrefs.difficulty] || 0; }
  function saveAbBest(accuracyPct) {
    const all = readJSON(AB_BEST_KEY, {});
    if (accuracyPct > (all[abPrefs.difficulty] || 0)) { all[abPrefs.difficulty] = accuracyPct; writeJSON(AB_BEST_KEY, all); return true; }
    return false;
  }
  function renderAbBest() {
    const best = abBestFor();
    const text = best ? `Beste Gesamtgenauigkeit (${AB_DIFFICULTIES[abPrefs.difficulty].title}): ${best}%` : "";
    els.abBestHint.textContent = text;
    els.abReadyBestHint.textContent = text;
  }
  function syncAbDifficultyUI() {
    els.abDifficultyRow.querySelectorAll("[data-ab-diff]").forEach((btn) => setActive(btn, btn.dataset.abDiff === abPrefs.difficulty));
  }
  els.abDifficultyRow.querySelectorAll("[data-ab-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      abPrefs.difficulty = btn.dataset.abDiff;
      saveAbPrefsToStorage();
      syncAbDifficultyUI();
      renderAbBest();
    });
  });

  els.abOpenBtn.addEventListener("click", () => {
    syncAbDifficultyUI();
    syncAbBgUI();
    renderAbBest();
    showScreen("abReady");
  });
  els.abReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  function abShuffled(arr) {
    const copy = arr.slice();
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  // Same timer-wrapping trick as scheduleRotationTimer/scheduleUfovTimer:
  // records what's pending and when it fires, so Pause can cancel it and
  // Resume can replay it with its exact remaining delay.
  function scheduleAbTimer(fn, delayMs) {
    abState.timerFn = fn;
    abState.timerFiresAt = performance.now() + delayMs;
    abState.timer = setTimeout(() => { abState.timer = null; fn(); }, delayMs);
  }

  // Builds the actual RSVP letter sequence for one trial: AB_LEAD_IN
  // distractors, then T1 (coloured), then (lag-1) filler distractors, then
  // the T2 slot (the letter X if this trial is T2-present, one more plain
  // distractor otherwise), then AB_TAIL trailing distractors. Every letter
  // in the sequence is distinct (sampled without replacement from
  // AB_LETTERS, 18 letters - comfortably enough for the longest possible
  // sequence, lag 8's 16 items) so a repeated letter never gets mistaken
  // for T1 or for X.
  function buildAbSequence(trial) {
    const len = AB_LEAD_IN + 1 + (trial.lag - 1) + 1 + AB_TAIL;
    const t1Index = AB_LEAD_IN;
    const t2Index = t1Index + trial.lag;
    const pool = abShuffled(AB_LETTERS);
    let pi = 0;
    const frames = [];
    for (let i = 0; i < len; i++) {
      if (i === t1Index) {
        const ch = pool[pi++];
        frames.push({ char: ch, role: "t1" });
        trial.t1Char = ch;
      } else if (i === t2Index) {
        frames.push(trial.t2Present ? { char: "X", role: "t2" } : { char: pool[pi++], role: "distractor" });
      } else {
        frames.push({ char: pool[pi++], role: "distractor" });
      }
    }
    trial.frames = frames;
  }

  function buildAbTrials() {
    const trials = [];
    AB_LAGS.forEach((lag) => {
      for (let i = 0; i < 6; i++) trials.push({ lag, t2Present: true });
      for (let i = 0; i < 2; i++) trials.push({ lag, t2Present: false });
    });
    // Shuffle, then avoid more than 3 identical lags back to back - same
    // guard as buildFlankerTrials/buildPosnerTrials, so the lag pattern
    // itself can't become predictable enough to game.
    for (let tries = 0; tries < 200; tries++) {
      const shuffled = abShuffled(trials);
      let ok = true, run = 1;
      for (let i = 1; i < shuffled.length; i++) {
        if (shuffled[i].lag === shuffled[i - 1].lag) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) { trials.length = 0; trials.push(...shuffled); break; }
    }
    trials.forEach(buildAbSequence);
    return trials;
  }

  // Picks the 4 multiple-choice options for "which letter was blue": the
  // real T1 letter plus 3 distinct foils, shuffled into a random order (so
  // the correct answer's position isn't learnable across trials).
  function abT1Options(trial) {
    const foils = abShuffled(AB_LETTERS.filter((l) => l !== trial.t1Char)).slice(0, 3);
    return abShuffled([trial.t1Char, ...foils]);
  }

  const AB_T1_BTNS = [];
  let abState = null;
  function startAbGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.abPlayer.hidden = false;
    els.abPlayerBar.hidden = false;
    els.abDonePanel.hidden = true;
    els.abPauseOverlay.hidden = true;
    els.abPauseBtn.hidden = false;
    if (!AB_T1_BTNS.length) AB_T1_BTNS.push(els.abT1Btn0, els.abT1Btn1, els.abT1Btn2, els.abT1Btn3);
    abState = {
      diff: AB_DIFFICULTIES[abPrefs.difficulty], trials: buildAbTrials(), index: -1, phase: "gap",
      frameIdx: 0, t1Options: [], pendingT1Correct: false,
      records: [], // { lag, t2Present, t1Correct, t2Correct }
      paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    els.abT1Panel.hidden = true;
    els.abT2Panel.hidden = true;
    els.abRevealHint.textContent = "";
    els.abStreamChar.textContent = "";
    els.abStreamChar.classList.remove("is-t1");
    applyAbBg();
    els.abHint.textContent = "Bereit? Gleich geht's los …";
    els.abProgressEl.textContent = `0/${abState.trials.length}`;
    requestWakeLock();
    scheduleAbTimer(abNextTrial, 1200);
  }
  els.abReadyStartBtn.addEventListener("click", startAbGame);

  function abNextTrial() {
    if (!abState) return;
    abState.index++;
    if (abState.index >= abState.trials.length) { abFinish(); return; }
    els.abProgressEl.textContent = `${abState.index + 1}/${abState.trials.length}`;
    abState.phase = "gap";
    els.abHint.textContent = "";
    els.abT1Panel.hidden = true;
    els.abT2Panel.hidden = true;
    els.abRevealHint.textContent = "";
    els.abStreamChar.textContent = "";
    els.abStreamChar.classList.remove("is-t1");
    const isi = abState.diff.isiMin + Math.random() * (abState.diff.isiMax - abState.diff.isiMin);
    scheduleAbTimer(abStartStream, isi);
  }
  function abStartStream() {
    if (!abState) return;
    abState.phase = "stream";
    abState.frameIdx = 0;
    abShowFrame();
  }
  function abShowFrame() {
    if (!abState) return;
    const trial = abState.trials[abState.index];
    if (abState.frameIdx >= trial.frames.length) {
      els.abStreamChar.textContent = "";
      els.abStreamChar.classList.remove("is-t1");
      abAskT1();
      return;
    }
    const frame = trial.frames[abState.frameIdx];
    els.abStreamChar.textContent = frame.char;
    els.abStreamChar.classList.toggle("is-t1", frame.role === "t1");
    scheduleAbTimer(() => { abState.frameIdx++; abShowFrame(); }, abState.diff.itemMs);
  }
  function abAskT1() {
    if (!abState) return;
    abState.phase = "askT1";
    const trial = abState.trials[abState.index];
    abState.t1Options = abT1Options(trial);
    AB_T1_BTNS.forEach((btn, i) => {
      btn.textContent = abState.t1Options[i];
      btn.classList.remove("correct", "wrong");
    });
    els.abT1Panel.hidden = false;
  }
  function abT1Tap(i) {
    if (!abState || abState.paused || abState.phase !== "askT1") return;
    abState.phase = "t1-feedback";
    const trial = abState.trials[abState.index];
    const guess = abState.t1Options[i];
    const correct = guess === trial.t1Char;
    abState.pendingT1Correct = correct;
    AB_T1_BTNS[i].classList.add(correct ? "correct" : "wrong");
    if (!correct) {
      const rightIdx = abState.t1Options.indexOf(trial.t1Char);
      if (rightIdx >= 0) AB_T1_BTNS[rightIdx].classList.add("correct");
    }
    scheduleAbTimer(abAskT2, 900);
  }
  els.abT1Btn0.addEventListener("click", () => abT1Tap(0));
  els.abT1Btn1.addEventListener("click", () => abT1Tap(1));
  els.abT1Btn2.addEventListener("click", () => abT1Tap(2));
  els.abT1Btn3.addEventListener("click", () => abT1Tap(3));

  function abAskT2() {
    if (!abState) return;
    els.abT1Panel.hidden = true;
    abState.phase = "askT2";
    els.abT2JaBtn.classList.remove("correct", "wrong");
    els.abT2NeinBtn.classList.remove("correct", "wrong");
    els.abRevealHint.textContent = "";
    els.abT2Panel.hidden = false;
  }
  function abT2Tap(guessPresent) {
    if (!abState || abState.paused || abState.phase !== "askT2") return;
    abState.phase = "t2-feedback";
    const trial = abState.trials[abState.index];
    const correct = guessPresent === trial.t2Present;
    const btn = guessPresent ? els.abT2JaBtn : els.abT2NeinBtn;
    btn.classList.add(correct ? "correct" : "wrong");
    if (!correct) {
      els.abRevealHint.textContent = trial.t2Present ? "Es war doch ein X dabei." : "Es war kein X dabei.";
    }
    abState.records.push({ lag: trial.lag, t2Present: trial.t2Present, t1Correct: abState.pendingT1Correct, t2Correct: correct });
    scheduleAbTimer(abNextTrial, correct ? 700 : 1300);
  }
  els.abT2JaBtn.addEventListener("click", () => abT2Tap(true));
  els.abT2NeinBtn.addEventListener("click", () => abT2Tap(false));

  // Pause just stops/replays the pending timer (a no-op during the two
  // untimed response phases, which just wait on a tap - pause still blocks
  // input via the phase check in abT1Tap/abT2Tap plus the overlay), same
  // convention as pauseUfov/pausePosner.
  function pauseAb() {
    if (!abState || abState.paused) return;
    abState.paused = true;
    abState.pausedAt = performance.now();
    if (abState.timer) {
      clearTimeout(abState.timer);
      abState.timer = null;
      abState.timerRemainingMs = Math.max(0, abState.timerFiresAt - abState.pausedAt);
    }
    els.abPauseBtn.hidden = true;
    els.abPauseOverlay.hidden = false;
  }
  function resumeAb() {
    if (!abState || !abState.paused) return;
    const pausedMs = performance.now() - abState.pausedAt;
    abState.startTime += pausedMs;
    abState.paused = false;
    if (abState.timerFn && abState.timerRemainingMs != null) {
      scheduleAbTimer(abState.timerFn, abState.timerRemainingMs);
      abState.timerRemainingMs = null;
    }
    els.abPauseOverlay.hidden = true;
    els.abPauseBtn.hidden = false;
  }
  els.abPauseBtn.addEventListener("click", pauseAb);
  els.abResumeBtn.addEventListener("click", resumeAb);

  // Accuracy of the T2 ("was X there?") judgement, counted only among
  // trials where T1 was ALSO correctly identified - the standard AB scoring
  // convention (Raymond, Shapiro & Arnell themselves score it this way):
  // the blink is specifically about what happens to T2 when attention was
  // actually engaged by T1, not about trials where T1 was missed entirely.
  function abT2AccuracyForLag(records, lag) {
    const relevant = records.filter((r) => r.lag === lag && r.t1Correct);
    if (!relevant.length) return null;
    const hits = relevant.filter((r) => r.t2Correct).length;
    return Math.round((100 * hits) / relevant.length);
  }

  function finalizeAbRun(state, totalTrials) {
    els.abPauseOverlay.hidden = true;
    els.abPlayerBar.hidden = true;
    const t1Hits = state.records.filter((r) => r.t1Correct).length;
    const t2Hits = state.records.filter((r) => r.t2Correct).length;
    const accuracyPct = Math.round((100 * (t1Hits + t2Hits)) / (2 * totalTrials));
    const accLag1 = abT2AccuracyForLag(state.records, 1);
    const accLag3 = abT2AccuracyForLag(state.records, 3);
    const accLag8 = abT2AccuracyForLag(state.records, 8);
    // The attentional-blink effect itself: how much worse T2 detection is
    // deep in the blink window (lag 3) than once it's fully recovered
    // (lag 8) - the actual signature dip-and-recovery shape this paradigm
    // exists to surface. Only meaningful once both sides have data.
    const blinkEffect = (accLag3 != null && accLag8 != null) ? (accLag8 - accLag3) : null;
    const isRecord = saveAbBest(accuracyPct);
    renderAbBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.abDoneSummary.textContent =
      `Doppelziel-Test (${state.diff.title}) · ${accuracyPct}% Gesamtgenauigkeit` +
      (accLag1 != null ? ` · T2 bei Lag 1: ${accLag1}%` : "") +
      (accLag3 != null ? ` · Lag 3: ${accLag3}%` : "") +
      (accLag8 != null ? ` · Lag 8: ${accLag8}%` : "") +
      (blinkEffect != null ? ` · Aufmerksamkeitslücke: ${blinkEffect} Punkte` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% gesamt` + (blinkEffect != null ? `, Lücke ${blinkEffect} Punkte` : "");
    const id = addHistory({ kind: "ab", title: "Doppelziel-Test (Attentional Blink)", seconds: Math.round(played), note });
    renderRating(els.abRating, id, "Wie konzentriert warst du?");
    els.abDonePanel.hidden = false;
  }
  function abFinish() {
    if (!abState) return;
    const state = abState;
    abState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.abPlayer) document.exitFullscreen().catch(() => {});
    els.abFsHint.hidden = true;
    finalizeAbRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved (both T1 and T2 answered).
  function abStop() {
    if (!abState) return;
    if (abState.timer) clearTimeout(abState.timer);
    const state = abState;
    abState = null;
    els.abPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.abPlayer) document.exitFullscreen().catch(() => {});
    els.abFsHint.hidden = true;
    if (state.records.length >= 4) {
      finalizeAbRun(state, state.records.length);
    } else {
      els.abPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.abBackBtn.addEventListener("click", abStop);
  els.abAgainBtn.addEventListener("click", () => { els.abDonePanel.hidden = true; startAbGame(); });
  els.abDoneBackBtn.addEventListener("click", () => { els.abPlayer.hidden = true; els.abDonePanel.hidden = true; showScreen("testHome"); });

  // ==== Test-Bereich: Antizipationstest (Coincidence-Anticipation Timing) ====
  // Twelfth autonomous entry (see CLAUDE.md "Test-Bereich (autonomous,
  // ongoing)"). Grounded in the classic Coincidence-Anticipation Timing (CAT)
  // paradigm from sport science - the ability to precisely predict WHEN a
  // moving object will arrive at a target location and time a response to
  // coincide with that exact moment, rather than simply reacting to it after
  // the fact. Historically measured with the "Bassin Anticipation Timer"
  // (Bassin, Cal Poly Pomona): a linear runway of sequentially-illuminated
  // LEDs simulating an approaching object, widely used across sport-science
  // research (soccer, tennis, volleyball, baseball/softball, racket sports).
  // Performance is scored via Absolute Error (AE, overall timing accuracy),
  // Constant Error (CE, the signed early/late bias) and Variable Error (VE,
  // response consistency) - the standard three-way error decomposition for
  // this paradigm (Schutz & Roy, 1973/1977). This exercise reimplements the
  // same idea on a phone screen: a ball moves at constant speed across a
  // horizontal track toward a marked target zone; the client taps a single
  // button at the moment they believe the ball arrives. Genuinely distinct
  // from every existing Test/NAT mechanic: MOT tracks objects that move
  // continuously but never need a precisely-TIMED response (only an eventual
  // identification tap after motion has already stopped); every RT-based
  // exercise here (Go/No-Go, Flanker, Posner, Simon, Rotationstest) measures
  // how FAST a client responds to an already-present or just-appeared
  // stimulus - this is the only one where the stimulus is continuously
  // visible and moving, and being precisely ACCURATE in timing (neither too
  // early nor too late) is the entire point, not speed. A direct fit for
  // FWMC's "bewegungsnahes mentales Training" angle - the same skill needed
  // to time a strike, catch, or interception of a moving ball or opponent.
  const ANTIZIP_PREFS_KEY = "fwmc-antizip-prefs-v1";
  // Difficulty sets how long the ball takes to reach the target zone
  // (jittered per trial within this range so a client can't just count
  // seconds instead of actually watching the ball - the real risk with a
  // screen-based, rhythmic-motion task like this one) and how tight the
  // "Treffer" tolerance window is - matching the real CAT literature's use
  // of different simulated stimulus speeds (slow/moderate/fast) as the main
  // difficulty manipulation. tailMs is how much further the ball keeps
  // moving past the target zone before an unanswered trial times out - a
  // generous window so a late-but-real tap still gets scored precisely
  // rather than being cut off.
  const ANTIZIP_DIFFICULTIES = {
    leicht: { title: "Leicht", preMsMin: 2200, preMsMax: 2600, tailMs: 1300, toleranceMs: 150 },
    mittel: { title: "Mittel", preMsMin: 1500, preMsMax: 1900, tailMs: 950, toleranceMs: 110 },
    schwer: { title: "Schwer", preMsMin: 950, preMsMax: 1250, tailMs: 700, toleranceMs: 80 },
  };
  // 20 trials - shorter than the fixed-response-window exercises (Flanker's
  // 32, Simon's 40) since each trial here already takes several real seconds
  // (the ball's full travel plus a short gap), not a sub-second flash.
  const ANTIZIP_TRIAL_COUNT = 20;
  const antizipPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadAntizipPrefs() {
    const saved = readJSON(ANTIZIP_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(antizipPrefs, saved);
    if (!ANTIZIP_DIFFICULTIES[antizipPrefs.difficulty]) antizipPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[antizipPrefs.bgColorKey]) antizipPrefs.bgColorKey = "gruen";
    if (typeof antizipPrefs.bgIntensity !== "number" || antizipPrefs.bgIntensity < 0 || antizipPrefs.bgIntensity > 1) antizipPrefs.bgIntensity = 0;
  }
  loadAntizipPrefs();
  function saveAntizipPrefsToStorage() { writeJSON(ANTIZIP_PREFS_KEY, antizipPrefs); }

  // Background colour/intensity, added later (client asked every Test-Bereich
  // exercise get the same background customisation NAT's Remember/Blitz/
  // Flash/MOT already have) - see CLAUDE.md Established patterns for the
  // scope decision (no transfer/preset-save here, unlike those four). The
  // target zone (#ffe0b2/#e65100 dashed border) lives in its own fixed-colour
  // .antizip-track sub-element, not directly on the raw stage - lower-risk
  // by construction, same reasoning as Merkspanne's .merk-field.
  function applyAntizipBg() {
    els.antizipStage.style.background = antizipPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[antizipPrefs.bgColorKey].hex, antizipPrefs.bgIntensity)
      : "";
  }
  const syncAntizipBgUI = wireBgIntensityControl(antizipPrefs, {
    pickers: [els.antizipBgColorPicker, els.antizipPauseBgColorPicker],
    sliders: [els.antizipBgIntensitySlider, els.antizipPauseBgSlider],
    valueEls: [els.antizipBgIntensityValue, els.antizipPauseBgValue],
    hintEls: [els.antizipBgContrastHint],
  }, () => { saveAntizipPrefsToStorage(); applyAntizipBg(); });

  // "Lower is better" (a timing-error score, same shape as UFOV's exposure-
  // duration threshold) - tracks the lowest average Absolute Error (AE, ms)
  // achieved per difficulty.
  const ANTIZIP_BEST_KEY = "fwmc-antizip-best-v1"; // { [difficulty]: bestAeMs }
  function antizipBestFor() {
    const v = readJSON(ANTIZIP_BEST_KEY, {})[antizipPrefs.difficulty];
    return (typeof v === "number") ? v : null;
  }
  function saveAntizipBest(aeMs) {
    const all = readJSON(ANTIZIP_BEST_KEY, {});
    const cur = all[antizipPrefs.difficulty];
    if (cur == null || aeMs < cur) { all[antizipPrefs.difficulty] = aeMs; writeJSON(ANTIZIP_BEST_KEY, all); return true; }
    return false;
  }
  function renderAntizipBest() {
    const best = antizipBestFor();
    const text = (best != null) ? `Bester mittlerer Fehler (${ANTIZIP_DIFFICULTIES[antizipPrefs.difficulty].title}): ${best} ms` : "";
    els.antizipBestHint.textContent = text;
    els.antizipReadyBestHint.textContent = text;
  }
  function syncAntizipDifficultyUI() {
    els.antizipDifficultyRow.querySelectorAll("[data-antizip-diff]").forEach((btn) => setActive(btn, btn.dataset.antizipDiff === antizipPrefs.difficulty));
  }
  els.antizipDifficultyRow.querySelectorAll("[data-antizip-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      antizipPrefs.difficulty = btn.dataset.antizipDiff;
      saveAntizipPrefsToStorage();
      syncAntizipDifficultyUI();
      renderAntizipBest();
    });
  });

  els.antizipOpenBtn.addEventListener("click", () => {
    syncAntizipDifficultyUI();
    syncAntizipBgUI();
    renderAntizipBest();
    showScreen("antizipReady");
  });
  els.antizipReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleSimonTimer/scheduleSearchTimer for
  // the (setTimeout-driven) inter-trial gap; the ball's own motion phase is
  // driven by requestAnimationFrame instead (see antizipTick below) since it
  // needs a continuously-updating position, not a single delayed callback -
  // its pause/resume instead shifts the trial's own start timestamp forward
  // by the paused duration, the same trick VT/Periphere Wahrnehmung use for
  // their own rAF schedules (simpler than MOT's "cancel outright" approach
  // since a single elapsed-time-since-start calculation, unlike MOT's
  // per-frame position accumulator, tolerates a shifted origin with no extra
  // bookkeeping).
  function scheduleAntizipTimer(fn, delayMs) {
    antizipState.timerFn = fn;
    antizipState.timerFiresAt = performance.now() + delayMs;
    antizipState.timer = setTimeout(() => { antizipState.timer = null; fn(); }, delayMs);
  }

  function buildAntizipTrials(diff) {
    const trials = [];
    for (let i = 0; i < ANTIZIP_TRIAL_COUNT; i++) {
      const preMs = diff.preMsMin + Math.random() * (diff.preMsMax - diff.preMsMin);
      trials.push({ preMs, tailMs: diff.tailMs });
    }
    return trials;
  }

  let antizipState = null;
  function startAntizipGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.antizipPlayer.hidden = false;
    els.antizipPlayerBar.hidden = false;
    els.antizipDonePanel.hidden = true;
    els.antizipPauseOverlay.hidden = true;
    els.antizipPauseBtn.hidden = false;
    els.antizipBall.hidden = true;
    els.antizipFeedback.textContent = "";
    els.antizipFeedback.className = "antizip-feedback";
    const diff = ANTIZIP_DIFFICULTIES[antizipPrefs.difficulty];
    antizipState = {
      diff, trials: buildAntizipTrials(diff),
      index: -1, phase: "gap", tapped: false, raf: null,
      errors: [], hits: 0, timeouts: 0,
      trialStartAt: 0, preMs: 0, total: 0,
      paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    applyAntizipBg();
    els.antizipHint.textContent = "Bereit? Gleich geht's los …";
    els.antizipProgressEl.textContent = `0/${antizipState.trials.length}`;
    requestWakeLock();
    scheduleAntizipTimer(antizipNextTrial, 1200);
  }
  els.antizipReadyStartBtn.addEventListener("click", startAntizipGame);

  function antizipNextTrial() {
    if (!antizipState) return;
    antizipState.index++;
    if (antizipState.index >= antizipState.trials.length) { antizipFinish(); return; }
    els.antizipProgressEl.textContent = `${antizipState.index + 1}/${antizipState.trials.length}`;
    antizipState.phase = "gap";
    antizipState.tapped = false;
    els.antizipBall.hidden = true;
    els.antizipFeedback.textContent = "";
    els.antizipFeedback.className = "antizip-feedback";
    els.antizipHint.textContent = "Bereit …";
    const isi = 700 + Math.random() * 500;
    scheduleAntizipTimer(antizipStartMove, isi);
  }
  function antizipStartMove() {
    if (!antizipState) return;
    const trial = antizipState.trials[antizipState.index];
    antizipState.phase = "moving";
    antizipState.tapped = false;
    antizipState.trialStartAt = performance.now();
    antizipState.total = trial.preMs + trial.tailMs;
    antizipState.preMs = trial.preMs;
    els.antizipHint.textContent = "";
    els.antizipBall.hidden = false;
    els.antizipBall.style.left = "0%";
    const targetFraction = trial.preMs / antizipState.total;
    els.antizipTargetZone.style.left = `${Math.min(86, Math.max(0, targetFraction * 100 - 7))}%`;
    antizipState.raf = requestAnimationFrame(antizipTick);
  }
  function antizipTick() {
    if (!antizipState || antizipState.phase !== "moving") return;
    const elapsed = performance.now() - antizipState.trialStartAt;
    if (elapsed >= antizipState.total) {
      // Never tapped at all within the ball's full travel - a genuine miss,
      // not scored into the timing-error stats (there's no meaningful
      // "how early/late" for a response that never happened), same
      // convention as Simon/Flanker's own timeout handling.
      antizipState.timeouts++;
      antizipState.phase = "gap";
      els.antizipBall.hidden = true;
      els.antizipFeedback.textContent = "Verpasst!";
      els.antizipFeedback.className = "antizip-feedback late";
      scheduleAntizipTimer(antizipNextTrial, 900);
      return;
    }
    els.antizipBall.style.left = `${(elapsed / antizipState.total) * 100}%`;
    antizipState.raf = requestAnimationFrame(antizipTick);
  }
  function antizipTap() {
    if (!antizipState || antizipState.paused || antizipState.tapped) return;
    if (antizipState.phase !== "moving") return;
    antizipState.tapped = true;
    antizipState.phase = "gap";
    if (antizipState.raf) { cancelAnimationFrame(antizipState.raf); antizipState.raf = null; }
    const elapsed = performance.now() - antizipState.trialStartAt;
    const error = Math.round(elapsed - antizipState.preMs); // + = zu spät, - = zu früh
    antizipState.errors.push(error);
    const isHit = Math.abs(error) <= antizipState.diff.toleranceMs;
    if (isHit) {
      antizipState.hits++;
      els.antizipFeedback.textContent = `Super! (${error >= 0 ? "+" : ""}${error} ms)`;
      els.antizipFeedback.className = "antizip-feedback good";
    } else if (error < 0) {
      els.antizipFeedback.textContent = `Zu früh (${error} ms)`;
      els.antizipFeedback.className = "antizip-feedback early";
    } else {
      els.antizipFeedback.textContent = `Zu spät (+${error} ms)`;
      els.antizipFeedback.className = "antizip-feedback late";
    }
    els.antizipBall.hidden = true;
    scheduleAntizipTimer(antizipNextTrial, 900);
  }
  els.antizipTapBtn.addEventListener("click", antizipTap);

  // Pause: the moving phase (rAF-driven) cancels the frame loop outright and,
  // on resume, shifts trialStartAt forward by exactly the paused duration -
  // the ball reappears at precisely the position/timing it would have
  // reached had the pause never happened. The gap phase (setTimeout-driven)
  // uses the standard remaining-delay replay trick instead, same as every
  // other Test exercise.
  function pauseAntizip() {
    if (!antizipState || antizipState.paused) return;
    antizipState.paused = true;
    antizipState.pausedAt = performance.now();
    if (antizipState.raf) { cancelAnimationFrame(antizipState.raf); antizipState.raf = null; }
    if (antizipState.timer) {
      clearTimeout(antizipState.timer);
      antizipState.timer = null;
      antizipState.timerRemainingMs = Math.max(0, antizipState.timerFiresAt - antizipState.pausedAt);
    }
    els.antizipPauseBtn.hidden = true;
    els.antizipPauseOverlay.hidden = false;
  }
  function resumeAntizip() {
    if (!antizipState || !antizipState.paused) return;
    const pausedMs = performance.now() - antizipState.pausedAt;
    antizipState.startTime += pausedMs;
    antizipState.paused = false;
    if (antizipState.phase === "moving") {
      antizipState.trialStartAt += pausedMs;
      antizipState.raf = requestAnimationFrame(antizipTick);
    }
    if (antizipState.timerFn && antizipState.timerRemainingMs != null) {
      scheduleAntizipTimer(antizipState.timerFn, antizipState.timerRemainingMs);
      antizipState.timerRemainingMs = null;
    }
    els.antizipPauseOverlay.hidden = true;
    els.antizipPauseBtn.hidden = false;
  }
  els.antizipPauseBtn.addEventListener("click", pauseAntizip);
  els.antizipResumeBtn.addEventListener("click", resumeAntizip);

  // Population-free sample standard deviation of the signed timing errors -
  // the "Variable Error" (VE) leg of the classic AE/CE/VE decomposition
  // (Schutz & Roy, 1973/1977) this paradigm is scored with; no shared helper
  // for this exists elsewhere in the app yet (nothing else here reports a
  // spread, only averages/slopes), so it's local to this exercise.
  function antizipStdDev(arr) {
    if (arr.length < 2) return null;
    const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
    const variance = arr.reduce((a, b) => a + (b - mean) * (b - mean), 0) / (arr.length - 1);
    return Math.round(Math.sqrt(variance));
  }
  function finalizeAntizipRun(state, totalTrials) {
    els.antizipPauseOverlay.hidden = true;
    els.antizipPlayerBar.hidden = true;
    const trefferPct = Math.round(100 * state.hits / totalTrials);
    const ae = state.errors.length ? Math.round(state.errors.reduce((a, b) => a + Math.abs(b), 0) / state.errors.length) : null;
    const ce = state.errors.length ? avgOf(state.errors) : null;
    const ve = antizipStdDev(state.errors);
    const isRecord = (ae != null) ? saveAntizipBest(ae) : false;
    renderAntizipBest();
    const played = (performance.now() - state.startTime) / 1000;
    const ceText = (ce == null) ? "" : (ce === 0 ? "genau im Schnitt getroffen" : (ce > 0 ? `im Schnitt ${ce} ms zu spät` : `im Schnitt ${Math.abs(ce)} ms zu früh`));
    els.antizipDoneSummary.textContent =
      `Antizipationstest (${state.diff.title}) · Trefferquote ${trefferPct}%` +
      (ae != null ? ` · mittlerer Fehler (AE) ${ae} ms` : "") +
      (ceText ? ` · ${ceText} (CE)` : "") +
      (ve != null ? ` · Streuung (VE) ${ve} ms` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${trefferPct}% Treffer` + (ae != null ? `, AE ${ae} ms` : "");
    const id = addHistory({ kind: "antizip", title: "Antizipationstest (Coincidence-Anticipation Timing)", seconds: Math.round(played), note });
    renderRating(els.antizipRating, id, "Wie gut hast du den Ball getroffen?");
    els.antizipDonePanel.hidden = false;
  }
  function antizipFinish() {
    if (!antizipState) return;
    const state = antizipState;
    antizipState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.antizipPlayer) document.exitFullscreen().catch(() => {});
    els.antizipFsHint.hidden = true;
    finalizeAntizipRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function antizipStop() {
    if (!antizipState) return;
    if (antizipState.timer) clearTimeout(antizipState.timer);
    if (antizipState.raf) cancelAnimationFrame(antizipState.raf);
    const state = antizipState;
    antizipState = null;
    els.antizipPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.antizipPlayer) document.exitFullscreen().catch(() => {});
    els.antizipFsHint.hidden = true;
    const resolved = state.errors.length + state.timeouts;
    if (resolved >= 4) {
      finalizeAntizipRun(state, resolved);
    } else {
      els.antizipPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.antizipBackBtn.addEventListener("click", antizipStop);
  els.antizipAgainBtn.addEventListener("click", () => { els.antizipDonePanel.hidden = true; startAntizipGame(); });
  els.antizipDoneBackBtn.addEventListener("click", () => { els.antizipPlayer.hidden = true; els.antizipDonePanel.hidden = true; showScreen("testHome"); });

  // Wahlreaktionstest (Hick's Law) - grounded in Hick's Law (Hick, 1952,
  // "On the rate of gain of information", Quarterly Journal of Experimental
  // Psychology; reviewed in Proctor & Schneider, 2018, QJEP): choice
  // reaction time rises LINEARLY with log2(N), the number of possible
  // stimulus-response alternatives (RT = a + b·log2(N)) - one of the few
  // widely-replicated quantitative laws in experimental psychology. A block
  // of N boxes is shown (N=2, then 4, then 8, always ascending - a fixed
  // block design, matching how Hick studies are actually run: the client
  // has to learn the current layout/mapping before a block of trials makes
  // sense, so set size can't be randomised trial-to-trial the way Suchtest
  // randomises its DISPLAY set size); each trial one box lights up and the
  // client taps that SAME box as fast as possible - a spatially-compatible
  // stimulus=response-target mapping (the lit box IS the tap target),
  // deliberately the same convention as Posner-Cueing's boxes, so the
  // measured RT reflects choice complexity alone, not an added
  // S-R-compatibility cost from a separate mapping. Reports average RT per
  // block size plus the actual outcome measure this paradigm exists to
  // surface: the Hick-Steigung (slope) in ms/Bit = (RT@8 - RT@2) /
  // (log2(8) - log2(2)) - tracking the LOWEST slope per length as the best
  // score (lower slope = more efficient information processing under
  // rising choice complexity, the theoretically "better" direction here,
  // same lower-is-better shape as UFOV's threshold/Antizip's AE). Also
  // researched as sport-relevant: sports-science explanations of elite
  // athletes' fast in-game decisions invoke Hick's own formula directly -
  // deliberate practice ingrains a "most likely" response, collapsing
  // effective choice complexity and lowering the informational load - and
  // studies comparing athletes/non-athletes on simple vs. choice RT
  // consistently find athletes pull further ahead as the number of
  // alternatives rises. Genuinely distinct from every existing Test/NAT
  // mechanic: none of the twelve exercises above this one systematically
  // varies the NUMBER OF RESPONSE ALTERNATIVES as the independent variable
  // (Go/No-Go is 1-vs-withhold; Flanker/Simon/Posner are always exactly 2
  // responses with a conflict/cue layered on top; Suchtest varies DISPLAY
  // set size, not response count) - this is the only exercise whose entire
  // point is the RT-vs-choice-count relationship itself. No Bei-Fehler/
  // background colour/Zusatzaufgabe/Trainingsmodus - correctly skipped,
  // same reasoning as every other fixed-trial RT exercise on this tab
  // (nothing to configure beyond length, since the difficulty ladder IS
  // the fixed 2->4->8 block structure, not something client-configurable).
  const HICK_PREFS_KEY = "fwmc-hick-prefs-v1";
  // "Length" = repeats per box position per block (no natural difficulty
  // dial otherwise, same "length setting" shape as Suchtest/UFOV) - total
  // trials = reps * (2+4+8) = reps*14.
  const HICK_LENGTHS = {
    kurz: { title: "Kurz", reps: 3 },
    mittel: { title: "Mittel", reps: 5 },
    lang: { title: "Lang", reps: 7 },
  };
  const HICK_SET_SIZES = [2, 4, 8]; // always ascending - see comment above
  const HICK_ISI_MIN = 500, HICK_ISI_MAX = 800;
  const HICK_BLOCK_INTRO_MS = 1400; // brief "Block x: N Möglichkeiten" pause before a block's first trial
  const HICK_FEEDBACK_MS = 400;
  const HICK_TIMEOUT_MS = 5000; // safety net only, self-paced task like Suchtest - a trial ends the instant something is tapped
  const HICK_MIN_RESOLVED = 6;
  const hickPrefs = { length: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadHickPrefs() {
    const saved = readJSON(HICK_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(hickPrefs, saved);
    if (!HICK_LENGTHS[hickPrefs.length]) hickPrefs.length = "mittel";
    if (!STROOP_COLOR_BY_KEY[hickPrefs.bgColorKey]) hickPrefs.bgColorKey = "gruen";
    if (typeof hickPrefs.bgIntensity !== "number" || hickPrefs.bgIntensity < 0 || hickPrefs.bgIntensity > 1) hickPrefs.bgIntensity = 0;
  }
  loadHickPrefs();
  function saveHickPrefsToStorage() { writeJSON(HICK_PREFS_KEY, hickPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyHickBg() {
    els.hickStage.style.background = hickPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[hickPrefs.bgColorKey].hex, hickPrefs.bgIntensity)
      : "";
  }
  const syncHickBgUI = wireBgIntensityControl(hickPrefs, {
    pickers: [els.hickBgColorPicker, els.hickPauseBgColorPicker],
    sliders: [els.hickBgIntensitySlider, els.hickPauseBgSlider],
    valueEls: [els.hickBgIntensityValue, els.hickPauseBgValue],
    hintEls: [els.hickBgContrastHint],
  }, () => { saveHickPrefsToStorage(); applyHickBg(); });

  const HICK_BEST_KEY = "fwmc-hick-best-v1"; // { [length]: bestSlopeMsPerBit } - lower is better
  function hickBestFor() {
    const v = readJSON(HICK_BEST_KEY, {})[hickPrefs.length];
    return typeof v === "number" ? v : null;
  }
  function saveHickBest(slope) {
    const all = readJSON(HICK_BEST_KEY, {});
    const cur = all[hickPrefs.length];
    if (cur == null || slope < cur) { all[hickPrefs.length] = slope; writeJSON(HICK_BEST_KEY, all); return true; }
    return false;
  }
  function renderHickBest() {
    const best = hickBestFor();
    const text = best != null ? `Beste Hick-Steigung (${HICK_LENGTHS[hickPrefs.length].title}): ${best} ms/Bit` : "";
    els.hickBestHint.textContent = text;
    els.hickReadyBestHint.textContent = text;
  }
  renderHickBest();
  function syncHickLengthUI() {
    els.hickLengthRow.querySelectorAll("[data-hick-length]").forEach((btn) => setActive(btn, btn.dataset.hickLength === hickPrefs.length));
  }
  els.hickLengthRow.querySelectorAll("[data-hick-length]").forEach((btn) => {
    btn.addEventListener("click", () => {
      hickPrefs.length = btn.dataset.hickLength;
      saveHickPrefsToStorage();
      syncHickLengthUI();
      renderHickBest();
    });
  });
  els.hickOpenBtn.addEventListener("click", () => {
    syncHickLengthUI();
    syncHickBgUI();
    renderHickBest();
    showScreen("hickReady");
  });
  els.hickReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Single active timer, remaining-delay pause/resume - same shape as every
  // other setTimeout-driven Test exercise. Like scheduleSearchTimer (and
  // unlike scheduleSimonTimer's fixed full-duration window), this always
  // clears any still-pending timer first, since a trial here can transition
  // early the instant a box is tapped.
  function scheduleHickTimer(fn, delayMs) {
    if (hickState.timer) clearTimeout(hickState.timer);
    hickState.timerFn = fn;
    hickState.timerFiresAt = performance.now() + delayMs;
    hickState.timer = setTimeout(() => { hickState.timer = null; fn(); }, delayMs);
  }

  function buildHickBlockTrials(n, reps) {
    const trials = [];
    for (let p = 0; p < n; p++) for (let i = 0; i < reps; i++) trials.push(p);
    // Shuffle, then avoid more than 3 identical POSITIONS back to back -
    // same guard as buildSearchTrials/buildPosnerTrials/buildSimonTrials, so
    // a long run of "it's always the same box" can't cluster by chance.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < trials.length; i++) {
        if (trials[i] === trials[i - 1]) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return trials;
  }
  function buildHickBlocks(reps) {
    return HICK_SET_SIZES.map((n) => ({ n, trials: buildHickBlockTrials(n, reps) }));
  }

  function hickSlope(avg2, avg8) {
    if (avg2 == null || avg8 == null) return null;
    return Math.round(((avg8 - avg2) / (Math.log2(8) - Math.log2(2))) * 10) / 10;
  }

  // Boxes are generated dynamically per block (unlike Posner's two fixed
  // HTML boxes) since N varies across the run - a plain CSS grid, 2/4
  // columns for N=2/4, 4 columns (2 rows) for N=8.
  function renderHickGrid(n) {
    els.hickBoxesGrid.innerHTML = "";
    els.hickBoxesGrid.dataset.n = String(n);
    els.hickBoxesGrid.style.gridTemplateColumns = `repeat(${Math.min(n, 4)}, 1fr)`;
    hickState.boxEls = [];
    for (let i = 0; i < n; i++) {
      const btn = document.createElement("button");
      btn.className = "hick-box";
      btn.setAttribute("aria-label", `Feld ${i + 1}`);
      btn.addEventListener("click", () => hickTap(i));
      els.hickBoxesGrid.appendChild(btn);
      hickState.boxEls.push(btn);
    }
  }
  function hickClearBoxes() {
    hickState.boxEls.forEach((el) => el.classList.remove("lit", "correct", "wrong"));
  }

  let hickState = null;
  function startHickGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.hickPlayer.hidden = false;
    els.hickPlayerBar.hidden = false;
    els.hickDonePanel.hidden = true;
    els.hickPauseOverlay.hidden = true;
    els.hickPauseBtn.hidden = false;
    const reps = HICK_LENGTHS[hickPrefs.length].reps;
    const blocks = buildHickBlocks(reps);
    hickState = {
      length: HICK_LENGTHS[hickPrefs.length], blocks, blockIndex: -1, trialIndexInBlock: -1, overallIndex: -1,
      totalTrials: blocks.reduce((s, b) => s + b.trials.length, 0),
      phase: "gap", boxEls: [], targetPos: null,
      correct: 0, incorrect: 0, timeouts: 0,
      rtByN: { 2: [], 4: [], 8: [] },
      paused: false, startTime: performance.now(), stimAt: null,
      timer: null, timerFn: null, timerFiresAt: null,
    };
    applyHickBg();
    els.hickHint.textContent = "Bereit? Gleich geht's los …";
    els.hickProgressEl.textContent = `0/${hickState.totalTrials}`;
    requestWakeLock();
    scheduleHickTimer(hickStartBlock, 1000);
  }
  els.hickReadyStartBtn.addEventListener("click", startHickGame);

  function hickStartBlock() {
    if (!hickState) return;
    hickState.blockIndex++;
    if (hickState.blockIndex >= hickState.blocks.length) { hickFinish(); return; }
    hickState.trialIndexInBlock = -1;
    hickState.phase = "blockintro";
    const block = hickState.blocks[hickState.blockIndex];
    renderHickGrid(block.n);
    els.hickHint.textContent = `Block ${hickState.blockIndex + 1} von ${hickState.blocks.length}: ${block.n} Möglichkeiten`;
    scheduleHickTimer(hickNextTrial, HICK_BLOCK_INTRO_MS);
  }
  function hickNextTrial() {
    if (!hickState) return;
    hickState.trialIndexInBlock++;
    const block = hickState.blocks[hickState.blockIndex];
    if (hickState.trialIndexInBlock >= block.trials.length) { hickStartBlock(); return; }
    hickState.overallIndex++;
    els.hickProgressEl.textContent = `${hickState.overallIndex + 1}/${hickState.totalTrials}`;
    hickState.phase = "gap";
    hickClearBoxes();
    els.hickHint.textContent = "";
    const isi = HICK_ISI_MIN + Math.random() * (HICK_ISI_MAX - HICK_ISI_MIN);
    scheduleHickTimer(hickShowTarget, isi);
  }
  function hickShowTarget() {
    if (!hickState) return;
    const block = hickState.blocks[hickState.blockIndex];
    const pos = block.trials[hickState.trialIndexInBlock];
    hickState.targetPos = pos;
    hickState.phase = "responding";
    hickState.stimAt = performance.now();
    hickState.boxEls[pos].classList.add("lit");
    scheduleHickTimer(hickTimeoutTrial, HICK_TIMEOUT_MS);
  }
  function hickTimeoutTrial() {
    if (!hickState || hickState.phase !== "responding") return;
    hickState.incorrect++;
    hickState.timeouts++;
    hickState.phase = "feedback";
    els.hickHint.textContent = "Verpasst!";
    scheduleHickTimer(hickNextTrial, HICK_FEEDBACK_MS);
  }
  function hickTap(pos) {
    if (!hickState || hickState.paused || hickState.phase !== "responding") return;
    const block = hickState.blocks[hickState.blockIndex];
    const rt = performance.now() - hickState.stimAt;
    hickState.phase = "feedback";
    if (pos === hickState.targetPos) {
      hickState.boxEls[pos].classList.add("correct");
      hickState.correct++;
      hickState.rtByN[block.n].push(rt);
    } else {
      hickState.boxEls[pos].classList.add("wrong");
      hickState.boxEls[hickState.targetPos].classList.add("correct");
      hickState.incorrect++;
      els.hickHint.textContent = "Daneben!";
    }
    scheduleHickTimer(hickNextTrial, HICK_FEEDBACK_MS);
  }

  function pauseHick() {
    if (!hickState || hickState.paused) return;
    hickState.paused = true;
    hickState.pausedAt = performance.now();
    if (hickState.timer) {
      clearTimeout(hickState.timer);
      hickState.timer = null;
      hickState.timerRemainingMs = Math.max(0, hickState.timerFiresAt - hickState.pausedAt);
    }
    els.hickPauseBtn.hidden = true;
    els.hickPauseOverlay.hidden = false;
  }
  function resumeHick() {
    if (!hickState || !hickState.paused) return;
    const pausedMs = performance.now() - hickState.pausedAt;
    hickState.startTime += pausedMs;
    if (hickState.stimAt != null) hickState.stimAt += pausedMs;
    hickState.paused = false;
    if (hickState.timerFn && hickState.timerRemainingMs != null) {
      scheduleHickTimer(hickState.timerFn, hickState.timerRemainingMs);
      hickState.timerRemainingMs = null;
    }
    els.hickPauseOverlay.hidden = true;
    els.hickPauseBtn.hidden = false;
  }
  els.hickPauseBtn.addEventListener("click", pauseHick);
  els.hickResumeBtn.addEventListener("click", resumeHick);

  function finalizeHickRun(state, totalTrials) {
    els.hickPauseOverlay.hidden = true;
    els.hickPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const avg2 = avgOf(state.rtByN[2]);
    const avg4 = avgOf(state.rtByN[4]);
    const avg8 = avgOf(state.rtByN[8]);
    const slope = hickSlope(avg2, avg8);
    const isRecord = slope != null ? saveHickBest(slope) : false;
    renderHickBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.hickDoneSummary.textContent =
      `Wahlreaktionstest (${state.length.title}) · ${accuracyPct}% richtig` +
      (avg2 != null ? ` · Ø 2 Möglichkeiten ${avg2} ms` : "") +
      (avg4 != null ? ` · Ø 4 Möglichkeiten ${avg4} ms` : "") +
      (avg8 != null ? ` · Ø 8 Möglichkeiten ${avg8} ms` : "") +
      (slope != null ? ` · Hick-Steigung ${slope} ms/Bit` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` + (slope != null ? `, Hick-Steigung ${slope} ms/Bit` : "");
    const id = addHistory({ kind: "hick", title: "Wahlreaktionstest (Hick's Law)", seconds: Math.round(played), note });
    renderRating(els.hickRating, id, "Wie klar fielen dir die Entscheidungen?");
    els.hickDonePanel.hidden = false;
  }
  function hickFinish() {
    if (!hickState) return;
    const state = hickState;
    hickState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.hickPlayer) document.exitFullscreen().catch(() => {});
    els.hickFsHint.hidden = true;
    finalizeHickRun(state, state.totalTrials);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function hickStop() {
    if (!hickState) return;
    if (hickState.timer) clearTimeout(hickState.timer);
    const state = hickState;
    hickState = null;
    els.hickPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.hickPlayer) document.exitFullscreen().catch(() => {});
    els.hickFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= HICK_MIN_RESOLVED) {
      finalizeHickRun(state, resolved);
    } else {
      els.hickPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.hickBackBtn.addEventListener("click", hickStop);
  els.hickAgainBtn.addEventListener("click", () => { els.hickDonePanel.hidden = true; startHickGame(); });
  els.hickDoneBackBtn.addEventListener("click", () => { els.hickPlayer.hidden = true; els.hickDonePanel.hidden = true; showScreen("testHome"); });

  // ---- Blockspanne-Test (Corsi Block-Tapping Task) ----
  // Grounded in the Corsi block-tapping task (Corsi, 1972; standardised
  // administration/scoring in Kessels et al., 2000, "The Corsi Block-Tapping
  // Task: standardization and normative data") - nine identical blocks are
  // scattered on a board; a subset lights up ONE AT A TIME in a specific
  // order, then the client reproduces that exact order by tapping the same
  // blocks. Forward version only (no backward recall) - a deliberate first-
  // version scope, same "don't build everything at once" spirit as every
  // other Test exercise. Simplified to a single-trial-per-length adaptive
  // climb (sequence length +1 after every correct recall, ends on the first
  // wrong tap) rather than Kessels' own 2-trials-per-length protocol - the
  // same simplification several digital adaptations use (e.g. PsyToolkit's
  // own Corsi implementation climbs the same way) - so "Blockspanne erreicht"
  // here means "the longest sequence recalled" (a client-facing analogue of
  // the standard Corsi span score), not a lab-grade psychometric span; see
  // Offene Fragen for this scope note. Genuinely distinct from every existing
  // Test/NAT memory mechanic: N-Back is a continuous match-N-back-trials-ago
  // stream; Remember/Blitz-Raster show several positions SIMULTANEOUSLY and
  // probe recall of WHICH ones (unordered for Blitz, positions only for
  // Remember); Flash Speicher Test recalls a sequence of CHARACTER IDENTITIES
  // in order, at scattered but visually irrelevant positions; Merkspanne-Test
  // is a single global same/different feature judgment over a whole array -
  // this is the only exercise where the client must reproduce an ORDERED
  // SEQUENCE OF SPATIAL LOCATIONS, the defining feature of the Corsi task and
  // a genuinely different visuospatial-working-memory demand (holding both
  // "where" and "in what order" at once) from all of the above.
  const CORSI_BLOCK_COUNT = 9; // the classic Corsi board's block count
  const CORSI_START_SPAN = 2; // classic starting sequence length
  const CORSI_ITEM_PX = 56;
  const CORSI_MIN_CENTER_PX = CORSI_ITEM_PX + 20;
  // "Tempo" is the one client-facing setting - how fast the to-be-remembered
  // sequence flashes, not a level the client climbs themselves (the climb
  // itself is the adaptive difficulty, same shape as N-Back/Hick's own
  // "no client-set level" exercises).
  const CORSI_DIFFICULTIES = {
    leicht: { title: "Leicht", litMs: 900, gapMs: 450 },
    mittel: { title: "Mittel", litMs: 700, gapMs: 350 },
    schwer: { title: "Schwer", litMs: 500, gapMs: 250 },
  };
  const CORSI_PRE_SEQUENCE_MS = 900; // brief "Merken ..." lead-in before each sequence's first flash
  const CORSI_FEEDBACK_MS = 550;
  const CORSI_FAIL_PAUSE_MS = 1300; // longer than the correct-feedback pause, so the reveal (wrong tap red / real next block green) is actually readable before the run ends

  const CORSI_PREFS_KEY = "fwmc-corsi-prefs-v1";
  const corsiPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadCorsiPrefs() {
    const saved = readJSON(CORSI_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(corsiPrefs, saved);
    if (!CORSI_DIFFICULTIES[corsiPrefs.difficulty]) corsiPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[corsiPrefs.bgColorKey]) corsiPrefs.bgColorKey = "gruen";
    if (typeof corsiPrefs.bgIntensity !== "number" || corsiPrefs.bgIntensity < 0 || corsiPrefs.bgIntensity > 1) corsiPrefs.bgIntensity = 0;
  }
  loadCorsiPrefs();
  function saveCorsiPrefsToStorage() { writeJSON(CORSI_PREFS_KEY, corsiPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyCorsiBg() {
    els.corsiStage.style.background = corsiPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[corsiPrefs.bgColorKey].hex, corsiPrefs.bgIntensity)
      : "";
  }
  const syncCorsiBgUI = wireBgIntensityControl(corsiPrefs, {
    pickers: [els.corsiBgColorPicker, els.corsiPauseBgColorPicker],
    sliders: [els.corsiBgIntensitySlider, els.corsiPauseBgSlider],
    valueEls: [els.corsiBgIntensityValue, els.corsiPauseBgValue],
    hintEls: [els.corsiBgContrastHint],
  }, () => { saveCorsiPrefsToStorage(); applyCorsiBg(); });

  const CORSI_BEST_KEY = "fwmc-corsi-best-v1"; // { [difficulty]: bestSpan } - higher is better
  function corsiBestFor() {
    const v = readJSON(CORSI_BEST_KEY, {})[corsiPrefs.difficulty];
    return typeof v === "number" ? v : 0;
  }
  function saveCorsiBest(span) {
    const all = readJSON(CORSI_BEST_KEY, {});
    const cur = all[corsiPrefs.difficulty] || 0;
    if (span > cur) { all[corsiPrefs.difficulty] = span; writeJSON(CORSI_BEST_KEY, all); return true; }
    return false;
  }
  function renderCorsiBest() {
    const best = corsiBestFor();
    const text = best ? `Beste Blockspanne (${CORSI_DIFFICULTIES[corsiPrefs.difficulty].title}): ${best}` : "";
    els.corsiBestHint.textContent = text;
    els.corsiReadyBestHint.textContent = text;
  }
  renderCorsiBest();
  function syncCorsiDifficultyUI() {
    els.corsiDifficultyRow.querySelectorAll("[data-corsi-difficulty]").forEach((btn) => setActive(btn, btn.dataset.corsiDifficulty === corsiPrefs.difficulty));
  }
  els.corsiDifficultyRow.querySelectorAll("[data-corsi-difficulty]").forEach((btn) => {
    btn.addEventListener("click", () => {
      corsiPrefs.difficulty = btn.dataset.corsiDifficulty;
      saveCorsiPrefsToStorage();
      syncCorsiDifficultyUI();
      renderCorsiBest();
    });
  });
  els.corsiOpenBtn.addEventListener("click", () => {
    syncCorsiDifficultyUI();
    syncCorsiBgUI();
    renderCorsiBest();
    showScreen("corsiReady");
  });
  els.corsiReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Single active timer, remaining-delay pause/resume - same shape as every
  // other setTimeout-driven Test exercise.
  function scheduleCorsiTimer(fn, delayMs) {
    if (corsiState.timer) clearTimeout(corsiState.timer);
    corsiState.timerFn = fn;
    corsiState.timerFiresAt = performance.now() + delayMs;
    corsiState.timer = setTimeout(() => { corsiState.timer = null; fn(); }, delayMs);
  }

  // Anti-overlap scatter placement, copy-adapted from Trail Making/Suchtest's
  // own (rejection sampling with a grid-search fallback), per this app's
  // established "copy-adapt when the engine differs" convention - this
  // board needs its own item size/margins for exactly 9 fixed blocks.
  function corsiStageBounds() {
    const rect = els.corsiStage.getBoundingClientRect();
    const w = rect.width || 390, h = rect.height || 600;
    const half = CORSI_ITEM_PX / 2;
    const minY = stageTopClearanceY(rect, els.corsiHint, els.corsiPlayerBar, 84, half);
    return { w, h, minX: half + 8, maxX: Math.max(half + 8, w - half - 8), minY, maxY: Math.max(minY, h - 16) };
  }
  function corsiRandomPixelPosition(existingPx, bounds) {
    for (let attempt = 0; attempt < 300; attempt++) {
      const x = bounds.minX + Math.random() * (bounds.maxX - bounds.minX);
      const y = bounds.minY + Math.random() * (bounds.maxY - bounds.minY);
      if (!existingPx.some((p) => Math.hypot(p.x - x, p.y - y) < CORSI_MIN_CENTER_PX)) return { x, y };
    }
    let best = null, bestDist = -1;
    const STEPS = 24;
    for (let gx = 0; gx <= STEPS; gx++) {
      for (let gy = 0; gy <= STEPS; gy++) {
        const x = bounds.minX + (gx / STEPS) * (bounds.maxX - bounds.minX);
        const y = bounds.minY + (gy / STEPS) * (bounds.maxY - bounds.minY);
        const dist = existingPx.length ? Math.min(...existingPx.map((p) => Math.hypot(p.x - x, p.y - y))) : Infinity;
        if (dist > bestDist) { bestDist = dist; best = { x, y }; }
      }
    }
    return best;
  }
  // The board's 9 positions are fixed for the whole game (one scattered
  // layout per run, regenerated on "Nochmal") - unlike a fresh scatter every
  // trial, this task needs one stable board the client can actually build a
  // spatial memory of across the whole climb.
  function buildCorsiBoard() {
    const bounds = corsiStageBounds();
    const existingPx = [];
    const positions = [];
    for (let i = 0; i < CORSI_BLOCK_COUNT; i++) {
      const px = corsiRandomPixelPosition(existingPx, bounds);
      existingPx.push(px);
      positions.push({ x: (px.x / bounds.w) * 100, y: (px.y / bounds.h) * 100 });
    }
    return positions;
  }
  function renderCorsiBoard(positions) {
    els.corsiBoard.innerHTML = "";
    corsiState.blockEls = positions.map((pos, i) => {
      const el = document.createElement("button");
      el.className = "corsi-block";
      el.style.left = pos.x + "%";
      el.style.top = pos.y + "%";
      el.setAttribute("aria-label", `Block ${i + 1}`);
      el.addEventListener("click", () => corsiTap(i));
      els.corsiBoard.appendChild(el);
      return el;
    });
  }
  function corsiClearBlocks() {
    corsiState.blockEls.forEach((el) => el.classList.remove("lit", "correct", "wrong"));
  }
  function corsiRandomSequence(len) {
    const idx = Array.from({ length: CORSI_BLOCK_COUNT }, (_, i) => i);
    for (let i = idx.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [idx[i], idx[j]] = [idx[j], idx[i]];
    }
    return idx.slice(0, len);
  }

  let corsiState = null;
  function startCorsiGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.corsiPlayer.hidden = false;
    els.corsiPlayerBar.hidden = false;
    els.corsiDonePanel.hidden = true;
    els.corsiPauseOverlay.hidden = true;
    els.corsiPauseBtn.hidden = false;
    corsiState = {
      diff: CORSI_DIFFICULTIES[corsiPrefs.difficulty],
      span: CORSI_START_SPAN, reachedSpan: 0,
      sequence: [], sequenceIndexShown: -1, tapIndex: 0,
      blockEls: [], phase: "intro", paused: false, startTime: performance.now(),
      timer: null, timerFn: null, timerFiresAt: null,
    };
    applyCorsiBg();
    renderCorsiBoard(buildCorsiBoard());
    els.corsiHint.textContent = "Gleich geht's los …";
    els.corsiProgressEl.textContent = `Länge ${corsiState.span}`;
    requestWakeLock();
    scheduleCorsiTimer(corsiStartLevel, 1000);
  }
  els.corsiReadyStartBtn.addEventListener("click", startCorsiGame);

  function corsiStartLevel() {
    if (!corsiState) return;
    corsiState.sequence = corsiRandomSequence(corsiState.span);
    corsiState.sequenceIndexShown = -1;
    corsiState.tapIndex = 0;
    corsiState.phase = "showing";
    corsiClearBlocks();
    els.corsiProgressEl.textContent = `Länge ${corsiState.span}`;
    els.corsiHint.textContent = "Merken …";
    scheduleCorsiTimer(corsiShowNext, CORSI_PRE_SEQUENCE_MS);
  }
  function corsiShowNext() {
    if (!corsiState) return;
    corsiClearBlocks();
    corsiState.sequenceIndexShown++;
    if (corsiState.sequenceIndexShown >= corsiState.sequence.length) {
      corsiState.phase = "responding";
      els.corsiHint.textContent = "Jetzt in der gleichen Reihenfolge antippen!";
      return;
    }
    const pos = corsiState.sequence[corsiState.sequenceIndexShown];
    corsiState.blockEls[pos].classList.add("lit");
    scheduleCorsiTimer(corsiHideCurrent, corsiState.diff.litMs);
  }
  function corsiHideCurrent() {
    if (!corsiState) return;
    corsiClearBlocks();
    scheduleCorsiTimer(corsiShowNext, corsiState.diff.gapMs);
  }
  function corsiTap(pos) {
    if (!corsiState || corsiState.paused || corsiState.phase !== "responding") return;
    const expected = corsiState.sequence[corsiState.tapIndex];
    if (pos === expected) {
      corsiState.blockEls[pos].classList.add("correct");
      corsiState.tapIndex++;
      if (corsiState.tapIndex >= corsiState.sequence.length) {
        corsiState.reachedSpan = corsiState.span;
        corsiState.phase = "feedback";
        els.corsiHint.textContent = "Richtig! Eine Länge weiter …";
        corsiState.span++;
        scheduleCorsiTimer(corsiStartLevel, CORSI_FEEDBACK_MS);
      }
    } else {
      // Same "show what it actually was" reveal convention as Hick/MOT/UFOV:
      // the wrongly-tapped block turns red, the block that was actually next
      // in the sequence turns green.
      corsiState.blockEls[pos].classList.add("wrong");
      corsiState.blockEls[expected].classList.add("correct");
      corsiState.phase = "feedback";
      els.corsiHint.textContent = "Leider daneben.";
      scheduleCorsiTimer(corsiFinish, CORSI_FAIL_PAUSE_MS);
    }
  }

  function pauseCorsi() {
    if (!corsiState || corsiState.paused) return;
    corsiState.paused = true;
    corsiState.pausedAt = performance.now();
    if (corsiState.timer) {
      clearTimeout(corsiState.timer);
      corsiState.timer = null;
      corsiState.timerRemainingMs = Math.max(0, corsiState.timerFiresAt - corsiState.pausedAt);
    }
    els.corsiPauseBtn.hidden = true;
    els.corsiPauseOverlay.hidden = false;
  }
  function resumeCorsi() {
    if (!corsiState || !corsiState.paused) return;
    const pausedMs = performance.now() - corsiState.pausedAt;
    corsiState.startTime += pausedMs;
    corsiState.paused = false;
    if (corsiState.timerFn && corsiState.timerRemainingMs != null) {
      scheduleCorsiTimer(corsiState.timerFn, corsiState.timerRemainingMs);
      corsiState.timerRemainingMs = null;
    }
    els.corsiPauseOverlay.hidden = true;
    els.corsiPauseBtn.hidden = false;
  }
  els.corsiPauseBtn.addEventListener("click", pauseCorsi);
  els.corsiResumeBtn.addEventListener("click", resumeCorsi);

  function finalizeCorsiRun(state) {
    els.corsiPauseOverlay.hidden = true;
    els.corsiPlayerBar.hidden = true;
    const span = state.reachedSpan;
    const isRecord = span > 0 ? saveCorsiBest(span) : false;
    renderCorsiBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.corsiDoneSummary.textContent =
      `Blockspanne-Test (${state.diff.title}) · Blockspanne erreicht: ${span}` +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `Blockspanne ${span}`;
    const id = addHistory({ kind: "corsi", title: "Blockspanne-Test (Corsi)", seconds: Math.round(played), note });
    renderRating(els.corsiRating, id, "Wie klar konntest du dir die Reihenfolge merken?");
    els.corsiDonePanel.hidden = false;
  }
  function corsiFinish() {
    if (!corsiState) return;
    const state = corsiState;
    corsiState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.corsiPlayer) document.exitFullscreen().catch(() => {});
    els.corsiFsHint.hidden = true;
    finalizeCorsiRun(state);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - but unlike a fixed-trial exercise, quitting before
  // even one sequence was correctly recalled (reachedSpan still 0) has
  // nothing meaningful to report, so that case just returns home quietly,
  // same threshold spirit as Trail Making's own "only a completed run
  // records" guard.
  function corsiStop() {
    if (!corsiState) return;
    if (corsiState.timer) clearTimeout(corsiState.timer);
    const state = corsiState;
    corsiState = null;
    els.corsiPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.corsiPlayer) document.exitFullscreen().catch(() => {});
    els.corsiFsHint.hidden = true;
    if (state.reachedSpan > 0) {
      finalizeCorsiRun(state);
    } else {
      els.corsiPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.corsiBackBtn.addEventListener("click", corsiStop);
  els.corsiAgainBtn.addEventListener("click", () => { els.corsiDonePanel.hidden = true; startCorsiGame(); });
  els.corsiDoneBackBtn.addEventListener("click", () => { els.corsiPlayer.hidden = true; els.corsiDonePanel.hidden = true; showScreen("testHome"); });

  // Reaktionsfeld-Test (fifteenth autonomous Test entry): grounded in
  // reaction-light-board training devices such as the Dynavision D2 (a
  // 64-light board across five concentric rings from centre to periphery,
  // used in sport-vision training, concussion/return-to-play protocols and
  // OT rehab research) - a single light appears somewhere across the whole
  // field, the client taps it as fast as possible, and the next light
  // appears elsewhere immediately. The real device runs two distinct modes:
  // "Mode A" (proactive) leaves a light on until it's hit, "Mode B"
  // (reactive) times each light out after a preset duration and moves on
  // regardless - both are offered here (`reaktPrefs.mode`) rather than
  // picking just one, same "don't force a single mode when the source
  // paradigm itself defines several" spirit as MOT's speed/count/both.
  // Genuinely distinct from every existing Test/NAT mechanic: this is the
  // only exercise whose stimulus can land ANYWHERE across a continuous
  // field (not fixed grid cells like Blitz-Raster/N-Back/Corsi, not framed
  // compass positions like UFOV/Posner) and whose whole point is raw
  // speeded motor reaction to wherever it appears next, one at a time, for
  // a sustained stretch of time rather than a fixed trial count - UFOV
  // measures a masked GLANCE under adaptive exposure with no motor race,
  // Blitz-Raster shows several cells AT ONCE then asks for delayed recall,
  // MOT tracks objects that stay put in identity but move continuously.
  const REAKT_MODES = {
    proaktiv: { title: "Proaktiv" },
    reaktiv: { title: "Reaktiv" },
  };
  const REAKT_DIFFICULTIES = {
    // exposureMs only matters in "reaktiv" mode (how long an unhit light
    // stays on before it moves anyway); minJumpFrac (as a fraction of the
    // stage's own half-diagonal) sets how far the NEXT light must appear
    // from the current one in BOTH modes, so higher difficulty always means
    // more ground to cover with eyes/hand across the whole field, matching
    // the real device's emphasis on scanning the full board, not just
    // reacting fast in one spot.
    leicht: { title: "Leicht", exposureMs: 1500, minJumpFrac: 0.15 },
    mittel: { title: "Mittel", exposureMs: 1000, minJumpFrac: 0.22 },
    schwer: { title: "Schwer", exposureMs: 650, minJumpFrac: 0.30 },
  };
  const REAKT_LENGTHS = {
    kurz: { title: "Kurz (30 Sek.)", durationS: 30 },
    mittel: { title: "Mittel (60 Sek.)", durationS: 60 },
    lang: { title: "Lang (90 Sek.)", durationS: 90 },
  };
  const REAKT_ITEM_PX = 66;
  const REAKT_LEAD_IN_MS = 900;
  // A light landing within this fraction of the stage's half-diagonal from
  // its centre counts as "zentral", further out as "peripher" - a pure
  // reporting/analysis split (nothing is drawn to mark the boundary, same as
  // UFOV's own invisible centre/peripheral split), mirroring the Dynavision
  // literature's own central-vs-peripheral-ring breakdown of hit data.
  const REAKT_CENTRAL_RADIUS_FRAC = 0.4;

  const REAKT_PREFS_KEY = "fwmc-reakt-prefs-v1";
  const reaktPrefs = { mode: "reaktiv", difficulty: "mittel", length: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadReaktPrefs() {
    const saved = readJSON(REAKT_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(reaktPrefs, saved);
    if (!REAKT_MODES[reaktPrefs.mode]) reaktPrefs.mode = "reaktiv";
    if (!REAKT_DIFFICULTIES[reaktPrefs.difficulty]) reaktPrefs.difficulty = "mittel";
    if (!REAKT_LENGTHS[reaktPrefs.length]) reaktPrefs.length = "mittel";
    if (!STROOP_COLOR_BY_KEY[reaktPrefs.bgColorKey]) reaktPrefs.bgColorKey = "gruen";
    if (typeof reaktPrefs.bgIntensity !== "number" || reaktPrefs.bgIntensity < 0 || reaktPrefs.bgIntensity > 1) reaktPrefs.bgIntensity = 0;
  }
  loadReaktPrefs();
  function saveReaktPrefsToStorage() { writeJSON(REAKT_PREFS_KEY, reaktPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyReaktBg() {
    els.reaktStage.style.background = reaktPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[reaktPrefs.bgColorKey].hex, reaktPrefs.bgIntensity)
      : "";
  }
  const syncReaktBgUI = wireBgIntensityControl(reaktPrefs, {
    pickers: [els.reaktBgColorPicker, els.reaktPauseBgColorPicker],
    sliders: [els.reaktBgIntensitySlider, els.reaktPauseBgSlider],
    valueEls: [els.reaktBgIntensityValue, els.reaktPauseBgValue],
    hintEls: [els.reaktBgContrastHint],
  }, () => { saveReaktPrefsToStorage(); applyReaktBg(); });

  // Best score is Treffer PRO MINUTE (hits/min) - deliberately length-
  // independent (a 30s and a 90s run are directly comparable), keyed by
  // mode+difficulty (a "Lang" run isn't a harder difficulty, just more of
  // the same rate) - higher is better, mirroring the real device's own
  // "number of hits" / hits-per-minute outcome measure.
  const REAKT_BEST_KEY = "fwmc-reakt-best-v1";
  function reaktBestKeyFor() { return `${reaktPrefs.mode}_${reaktPrefs.difficulty}`; }
  function reaktBestFor() {
    const v = readJSON(REAKT_BEST_KEY, {})[reaktBestKeyFor()];
    return typeof v === "number" ? v : 0;
  }
  function saveReaktBest(hitsPerMin) {
    const all = readJSON(REAKT_BEST_KEY, {});
    const key = reaktBestKeyFor();
    const cur = all[key] || 0;
    if (hitsPerMin > cur) { all[key] = hitsPerMin; writeJSON(REAKT_BEST_KEY, all); return true; }
    return false;
  }
  function renderReaktBest() {
    const best = reaktBestFor();
    const text = best ? `Beste Trefferquote (${REAKT_MODES[reaktPrefs.mode].title}, ${REAKT_DIFFICULTIES[reaktPrefs.difficulty].title}): ${best.toFixed(0)} Treffer/Min` : "";
    els.reaktBestHint.textContent = text;
    els.reaktReadyBestHint.textContent = text;
  }
  renderReaktBest();
  function syncReaktUI() {
    els.reaktModeRow.querySelectorAll("[data-reakt-mode]").forEach((btn) => setActive(btn, btn.dataset.reaktMode === reaktPrefs.mode));
    els.reaktDifficultyRow.querySelectorAll("[data-reakt-difficulty]").forEach((btn) => setActive(btn, btn.dataset.reaktDifficulty === reaktPrefs.difficulty));
    els.reaktLengthRow.querySelectorAll("[data-reakt-length]").forEach((btn) => setActive(btn, btn.dataset.reaktLength === reaktPrefs.length));
  }
  els.reaktModeRow.querySelectorAll("[data-reakt-mode]").forEach((btn) => {
    btn.addEventListener("click", () => { reaktPrefs.mode = btn.dataset.reaktMode; saveReaktPrefsToStorage(); syncReaktUI(); renderReaktBest(); });
  });
  els.reaktDifficultyRow.querySelectorAll("[data-reakt-difficulty]").forEach((btn) => {
    btn.addEventListener("click", () => { reaktPrefs.difficulty = btn.dataset.reaktDifficulty; saveReaktPrefsToStorage(); syncReaktUI(); renderReaktBest(); });
  });
  els.reaktLengthRow.querySelectorAll("[data-reakt-length]").forEach((btn) => {
    btn.addEventListener("click", () => { reaktPrefs.length = btn.dataset.reaktLength; saveReaktPrefsToStorage(); syncReaktUI(); });
  });
  els.reaktOpenBtn.addEventListener("click", () => {
    syncReaktUI();
    syncReaktBgUI();
    renderReaktBest();
    showScreen("reaktReady");
  });
  els.reaktReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Single active timer, remaining-delay pause/resume - same shape as every
  // other setTimeout-driven Test exercise. Only ever actually armed in
  // "reaktiv" mode (the exposure timeout) or during the lead-in; "proaktiv"
  // mode's lights have no timer of their own (they wait indefinitely for a
  // tap), same "pause is a no-op beyond blocking input" shape UFOV's own
  // untimed response phases already use.
  function scheduleReaktTimer(fn, delayMs) {
    if (reaktState.timer) clearTimeout(reaktState.timer);
    reaktState.timerFn = fn;
    reaktState.timerFiresAt = performance.now() + delayMs;
    reaktState.timer = setTimeout(() => { reaktState.timer = null; fn(); }, delayMs);
  }

  function reaktStageBounds() {
    const rect = els.reaktStage.getBoundingClientRect();
    const w = rect.width || 390, h = rect.height || 600;
    const half = REAKT_ITEM_PX / 2;
    const minY = stageTopClearanceY(rect, els.reaktHint, els.reaktPlayerBar, 70, half);
    return { w, h, minX: half + 8, maxX: Math.max(half + 8, w - half - 8), minY, maxY: Math.max(minY, h - 16) };
  }
  // Picks a random point at least `minJumpPx` away from the previous light's
  // position (null previous = anywhere) - forces genuine eye/hand travel
  // across the whole field every step rather than letting two consecutive
  // lights land right next to each other. Falls back to the single farthest
  // point from the previous one if 200 random tries can't satisfy the
  // minimum (can happen on a very small/narrow viewport at "schwer").
  function reaktRandomPosition(prevPx, bounds, minJumpPx) {
    for (let attempt = 0; attempt < 200; attempt++) {
      const x = bounds.minX + Math.random() * (bounds.maxX - bounds.minX);
      const y = bounds.minY + Math.random() * (bounds.maxY - bounds.minY);
      if (!prevPx || Math.hypot(prevPx.x - x, prevPx.y - y) >= minJumpPx) return { x, y };
    }
    if (!prevPx) return { x: (bounds.minX + bounds.maxX) / 2, y: (bounds.minY + bounds.maxY) / 2 };
    let best = null, bestDist = -1;
    const STEPS = 20;
    for (let gx = 0; gx <= STEPS; gx++) {
      for (let gy = 0; gy <= STEPS; gy++) {
        const x = bounds.minX + (gx / STEPS) * (bounds.maxX - bounds.minX);
        const y = bounds.minY + (gy / STEPS) * (bounds.maxY - bounds.minY);
        const dist = Math.hypot(prevPx.x - x, prevPx.y - y);
        if (dist > bestDist) { bestDist = dist; best = { x, y }; }
      }
    }
    return best;
  }
  function reaktZoneFor(px, bounds) {
    const cx = (bounds.minX + bounds.maxX) / 2, cy = (bounds.minY + bounds.maxY) / 2;
    const halfDiag = Math.hypot(bounds.maxX - cx, bounds.maxY - cy) || 1;
    const dist = Math.hypot(px.x - cx, px.y - cy);
    return (dist / halfDiag) <= REAKT_CENTRAL_RADIUS_FRAC ? "zentral" : "peripher";
  }
  function reaktNewZoneStat() { return { hits: 0, misses: 0, rtSum: 0, rtCount: 0 }; }

  let reaktState = null;
  function startReaktGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.reaktPlayer.hidden = false;
    els.reaktPlayerBar.hidden = false;
    els.reaktDonePanel.hidden = true;
    els.reaktPauseOverlay.hidden = true;
    els.reaktPauseBtn.hidden = false;
    reaktState = {
      mode: reaktPrefs.mode, diff: REAKT_DIFFICULTIES[reaktPrefs.difficulty], length: REAKT_LENGTHS[reaktPrefs.length],
      durationMs: REAKT_LENGTHS[reaktPrefs.length].durationS * 1000,
      hits: 0, misses: 0, rtSum: 0, rtCount: 0,
      zoneStats: { zentral: reaktNewZoneStat(), peripher: reaktNewZoneStat() },
      prevPx: null, lightEl: null, onsetAt: 0, curZone: null,
      paused: false, startTime: performance.now(),
      timer: null, timerFn: null, timerFiresAt: null,
    };
    applyReaktBg();
    els.reaktField.innerHTML = "";
    els.reaktHint.textContent = "Gleich geht's los …";
    els.reaktProgressEl.textContent = `Treffer: 0 · ${reaktState.length.title}`;
    requestWakeLock();
    scheduleReaktTimer(reaktSpawnLight, REAKT_LEAD_IN_MS);
  }
  els.reaktReadyStartBtn.addEventListener("click", startReaktGame);

  function reaktSpawnLight() {
    if (!reaktState) return;
    const elapsedMs = performance.now() - reaktState.startTime - REAKT_LEAD_IN_MS;
    if (elapsedMs >= reaktState.durationMs) { reaktFinish(); return; }
    els.reaktHint.textContent = "";
    const bounds = reaktStageBounds();
    const minJumpPx = reaktState.diff.minJumpFrac * Math.hypot(bounds.maxX - bounds.minX, bounds.maxY - bounds.minY);
    const px = reaktRandomPosition(reaktState.prevPx, bounds, minJumpPx);
    reaktState.prevPx = px;
    reaktState.curZone = reaktZoneFor(px, bounds);
    const el = document.createElement("button");
    el.className = "reakt-light";
    el.style.left = ((px.x / bounds.w) * 100) + "%";
    el.style.top = ((px.y / bounds.h) * 100) + "%";
    el.setAttribute("aria-label", "Reaktionsfeld-Licht");
    el.addEventListener("click", reaktTap);
    els.reaktField.innerHTML = "";
    els.reaktField.appendChild(el);
    reaktState.lightEl = el;
    reaktState.onsetAt = performance.now();
    if (reaktState.mode === "reaktiv") {
      scheduleReaktTimer(reaktMiss, reaktState.diff.exposureMs);
    }
  }
  function reaktAdvance() {
    if (!reaktState) return;
    els.reaktProgressEl.textContent = `Treffer: ${reaktState.hits}` + (reaktState.misses ? ` · Verpasst: ${reaktState.misses}` : "") + ` · ${reaktState.length.title}`;
    reaktSpawnLight();
  }
  function reaktTap() {
    if (!reaktState || reaktState.paused || !reaktState.lightEl) return;
    const rt = performance.now() - reaktState.onsetAt;
    reaktState.lightEl = null;
    reaktState.hits++;
    reaktState.rtSum += rt; reaktState.rtCount++;
    const zs = reaktState.zoneStats[reaktState.curZone];
    zs.hits++; zs.rtSum += rt; zs.rtCount++;
    reaktAdvance();
  }
  // Reaktiv-mode-only: the light wasn't tapped within its exposure window,
  // so it moves on regardless - same "Mode B" behaviour the real Dynavision
  // device uses (illuminate for a preset time, then automatically jump to a
  // new location whether hit or not).
  function reaktMiss() {
    if (!reaktState) return;
    reaktState.lightEl = null;
    reaktState.misses++;
    reaktState.zoneStats[reaktState.curZone].misses++;
    reaktAdvance();
  }

  function pauseReakt() {
    if (!reaktState || reaktState.paused) return;
    reaktState.paused = true;
    reaktState.pausedAt = performance.now();
    if (reaktState.timer) {
      clearTimeout(reaktState.timer);
      reaktState.timer = null;
      reaktState.timerRemainingMs = Math.max(0, reaktState.timerFiresAt - reaktState.pausedAt);
    }
    els.reaktPauseBtn.hidden = true;
    els.reaktPauseOverlay.hidden = false;
  }
  function resumeReakt() {
    if (!reaktState || !reaktState.paused) return;
    const pausedMs = performance.now() - reaktState.pausedAt;
    reaktState.startTime += pausedMs;
    reaktState.onsetAt += pausedMs;
    reaktState.paused = false;
    if (reaktState.timerFn && reaktState.timerRemainingMs != null) {
      scheduleReaktTimer(reaktState.timerFn, reaktState.timerRemainingMs);
      reaktState.timerRemainingMs = null;
    }
    els.reaktPauseOverlay.hidden = true;
    els.reaktPauseBtn.hidden = false;
  }
  els.reaktPauseBtn.addEventListener("click", pauseReakt);
  els.reaktResumeBtn.addEventListener("click", resumeReakt);

  function reaktZoneSummary(state, zone, label) {
    const zs = state.zoneStats[zone];
    const avgRt = zs.rtCount ? Math.round(zs.rtSum / zs.rtCount) : null;
    const total = zs.hits + zs.misses;
    if (!total) return `${label}: keine Reize`;
    const parts = [`${label}: ${zs.hits}/${total} getroffen`];
    if (avgRt != null) parts.push(`Ø ${avgRt} ms`);
    return parts.join(", ");
  }
  function finalizeReaktRun(state) {
    els.reaktPauseOverlay.hidden = true;
    els.reaktPlayerBar.hidden = true;
    const playedMs = Math.max(1000, Math.min(state.durationMs, performance.now() - state.startTime - REAKT_LEAD_IN_MS));
    const playedS = playedMs / 1000;
    const hitsPerMin = state.hits / (playedS / 60);
    const isRecord = state.hits > 0 ? saveReaktBest(hitsPerMin) : false;
    renderReaktBest();
    const avgRt = state.rtCount ? Math.round(state.rtSum / state.rtCount) : null;
    els.reaktDoneSummary.textContent =
      `Reaktionsfeld-Test (${REAKT_MODES[state.mode].title}, ${state.diff.title}) · ${state.hits} Treffer` +
      (state.misses ? ` · ${state.misses} verpasst` : "") +
      (avgRt != null ? ` · Ø Reaktionszeit ${avgRt} ms` : "") +
      ` · ${hitsPerMin.toFixed(0)} Treffer/Min` +
      (isRecord ? " · Neue Bestleistung!" : "") +
      ` · ${reaktZoneSummary(state, "zentral", "Zentral")} · ${reaktZoneSummary(state, "peripher", "Peripher")}`;
    const note = `${state.hits} Treffer, ${hitsPerMin.toFixed(0)}/Min`;
    const id = addHistory({ kind: "reakt", title: "Reaktionsfeld-Test", seconds: Math.round(playedS), note });
    renderRating(els.reaktRating, id, "Wie gut konntest du dich auch auf den Rand deines Blickfelds konzentrieren?");
    els.reaktDonePanel.hidden = false;
  }
  function reaktFinish() {
    if (!reaktState) return;
    const state = reaktState;
    reaktState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.reaktPlayer) document.exitFullscreen().catch(() => {});
    els.reaktFsHint.hidden = true;
    els.reaktField.innerHTML = "";
    finalizeReaktRun(state);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - but with nothing hit yet (state.hits === 0) there's
  // nothing meaningful to report, so that case just returns home quietly,
  // same threshold spirit as Corsi/Trail Making's own "only real progress
  // records" guard.
  function reaktStop() {
    if (!reaktState) return;
    if (reaktState.timer) clearTimeout(reaktState.timer);
    const state = reaktState;
    reaktState = null;
    els.reaktPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.reaktPlayer) document.exitFullscreen().catch(() => {});
    els.reaktFsHint.hidden = true;
    els.reaktField.innerHTML = "";
    if (state.hits > 0 || state.misses > 0) {
      finalizeReaktRun(state);
    } else {
      els.reaktPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.reaktBackBtn.addEventListener("click", reaktStop);
  els.reaktAgainBtn.addEventListener("click", () => { els.reaktDonePanel.hidden = true; startReaktGame(); });
  els.reaktDoneBackBtn.addEventListener("click", () => { els.reaktPlayer.hidden = true; els.reaktDonePanel.hidden = true; showScreen("testHome"); });

  // ---- Regelwechsel-Test (Task-Switching) ----
  // Grounded in the task-switching paradigm (Jersild, 1927; popularised by
  // Rogers & Monsell, 1995's "alternating runs" design, and Meiran, 1996's
  // CUED task-switching variant, the shape used here) - the very same
  // simple, ambiguous stimulus (a digit) can be classified by one of two
  // rules ("Zahl": gerade/ungerade, or "Größe": kleiner/größer als 5), and
  // a cue names which rule applies THIS trial; the rule sometimes stays
  // the same as the previous trial ("repeat") and sometimes changes
  // ("switch"). The classic, endlessly replicated finding this paradigm
  // exists to surface: even though the DECISION itself is equally simple
  // either way, a SWITCH trial is reliably slower (and often less
  // accurate) than a REPEAT trial - the "switch cost", the actual cost of
  // reconfiguring which rule is currently active, not of any single
  // decision being harder. Meiran (1996) showed this switch cost shrinks
  // the longer the cue is shown before the stimulus (the cue-stimulus
  // interval, CSI - more time to prepare the new rule) but never fully
  // disappears even with a long CSI (a "residual" switch cost) - reflected
  // here by `csiMs` varying with difficulty (generous prep time on Leicht,
  // almost none on Schwer) as the one thing difficulty actually changes,
  // rather than trial count or response window alone. Also researched as
  // sport-relevant: skilled/expert athletes show more flexible allocation
  // of attentional resources and better task-switching accuracy than
  // non-athletes under dual-task load (e.g. a 2024 postural-control/
  // cognitive-flexibility study), while task-switching accuracy specifically
  // drops under mental fatigue in athletes (a 2026 soccer-player ERP
  // study) - a fit for FWMC's "visuelle Entscheidungsgeschwindigkeit"
  // focus, this time the specific facet of adapting the decision RULE
  // itself rather than filtering/inhibiting/timing an already-fixed one.
  // Genuinely distinct from every existing Test/NAT mechanic: none of the
  // fifteen exercises already on this tab ever changes WHICH RULE governs
  // the same response mid-run - Simon/Flanker/Posner/Rotationstest all
  // apply one constant rule to a changing stimulus, Hick varies the NUMBER
  // of alternatives but never their meaning, Suchtest varies the target
  // definition only across whole BLOCKS (feature vs. conjunction), never
  // trial-by-trial with a real switch-vs-repeat contrast within one run.
  // Bivalent bare-digit stimuli (every digit from 1-4/6-9, excluding the
  // neutral 5, is a valid input to BOTH rules) copy the classic Rogers &
  // Monsell/Meiran stimulus design directly, rather than inventing an
  // artificial two-task pair from scratch. No Bei-Fehler/Zusatzaufgabe/
  // Trainingsmodus/length setting - correctly skipped per the "optional,
  // skip what doesn't fit in an hour" guidance, same reasoning as every
  // other fixed-trial RT exercise here (a fixed-count switch-cost measure,
  // nothing to configure beyond difficulty, plus the background-colour
  // Feineinstellungen every Test-Bereich exercise gets, see CLAUDE.md).
  // Pause/
  // resume and the self-paced tap-ends-trial-immediately/safety-net-timeout
  // shape both reuse the same scheduleXTimer-remaining-delay pattern as
  // Hick/Suchtest. New CSS is `.ts-*` (fixed hex colours throughout, no
  // `var(--...)`); correct/wrong is a plain solid background swap on the
  // tapped response button (Flanker/Posner/Hick's convention), not Simon's
  // colour-neutral ring, since these buttons' LABELS themselves change
  // every trial with the active rule - there's no fixed button colour
  // meaning here that a solid swap could confuse.
  const TS_DIFFICULTIES = {
    // csiMs = cue-stimulus interval (task preparation time) - the one
    // variable Meiran (1996) showed actually shrinks the switch cost, so
    // it's what "difficulty" means here rather than a shorter response
    // window on its own. isiMs = gap between one trial's feedback and the
    // next cue (keeps overall pace brisk at higher difficulty too).
    leicht: { title: "Leicht", csiMs: 800, isiMs: 500, timeoutMs: 3000 },
    mittel: { title: "Mittel", csiMs: 400, isiMs: 400, timeoutMs: 2200 },
    schwer: { title: "Schwer", csiMs: 150, isiMs: 350, timeoutMs: 1600 },
  };
  const TS_TASKS = [
    { key: "zahl", cueLabel: "Aufgabe: ZAHL", leftLabel: "Gerade", rightLabel: "Ungerade", answerSide: (d) => (d % 2 === 0 ? "left" : "right") },
    { key: "groesse", cueLabel: "Aufgabe: GRÖSSE", leftLabel: "Klein (<5)", rightLabel: "Groß (>5)", answerSide: (d) => (d < 5 ? "left" : "right") },
  ];
  // Excludes 5 (neutral for the "Größe" rule) - every remaining digit is a
  // valid, unambiguous input to BOTH rules at once (classic bivalent
  // stimulus design), so the cue alone determines which answer is correct.
  const TS_DIGITS = [1, 2, 3, 4, 6, 7, 8, 9];
  // Trial 0 is an unclassified "warm-up" - there's no previous task yet to
  // compare it against, so it can't be a switch or a repeat trial; the
  // other 43 trials split roughly evenly between the two by chance (with
  // the same max-3-in-a-row guard used elsewhere), giving a workable
  // per-type sample comparable to Flanker's own 16-per-condition split.
  const TS_TRIAL_COUNT = 44;
  const TS_FEEDBACK_MS = 400;
  const TS_MIN_RESOLVED = 8;
  const TS_PREFS_KEY = "fwmc-ts-prefs-v1";
  const tsPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadTsPrefs() {
    const saved = readJSON(TS_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(tsPrefs, saved);
    if (!TS_DIFFICULTIES[tsPrefs.difficulty]) tsPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[tsPrefs.bgColorKey]) tsPrefs.bgColorKey = "gruen";
    if (typeof tsPrefs.bgIntensity !== "number" || tsPrefs.bgIntensity < 0 || tsPrefs.bgIntensity > 1) tsPrefs.bgIntensity = 0;
  }
  loadTsPrefs();
  function saveTsPrefsToStorage() { writeJSON(TS_PREFS_KEY, tsPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyTsBg() {
    els.tsStage.style.background = tsPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[tsPrefs.bgColorKey].hex, tsPrefs.bgIntensity)
      : "";
  }
  const syncTsBgUI = wireBgIntensityControl(tsPrefs, {
    pickers: [els.tsBgColorPicker, els.tsPauseBgColorPicker],
    sliders: [els.tsBgIntensitySlider, els.tsPauseBgSlider],
    valueEls: [els.tsBgIntensityValue, els.tsPauseBgValue],
    hintEls: [els.tsBgContrastHint],
  }, () => { saveTsPrefsToStorage(); applyTsBg(); });

  const TS_BEST_KEY = "fwmc-ts-best-v1"; // { [difficulty]: bestSwitchCostMs } - lower is better
  function tsBestFor() {
    const v = readJSON(TS_BEST_KEY, {})[tsPrefs.difficulty];
    return typeof v === "number" ? v : null;
  }
  function saveTsBest(cost) {
    const all = readJSON(TS_BEST_KEY, {});
    const cur = all[tsPrefs.difficulty];
    if (cur == null || cost < cur) { all[tsPrefs.difficulty] = cost; writeJSON(TS_BEST_KEY, all); return true; }
    return false;
  }
  function renderTsBest() {
    const best = tsBestFor();
    const text = best != null ? `Niedrigste Wechselkosten (${TS_DIFFICULTIES[tsPrefs.difficulty].title}): ${Math.round(best)} ms` : "";
    els.tsBestHint.textContent = text;
    els.tsReadyBestHint.textContent = text;
  }
  renderTsBest();
  function syncTsDifficultyUI() {
    els.tsDifficultyRow.querySelectorAll("[data-ts-diff]").forEach((btn) => setActive(btn, btn.dataset.tsDiff === tsPrefs.difficulty));
  }
  els.tsDifficultyRow.querySelectorAll("[data-ts-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      tsPrefs.difficulty = btn.dataset.tsDiff;
      saveTsPrefsToStorage();
      syncTsDifficultyUI();
      renderTsBest();
    });
  });
  els.tsOpenBtn.addEventListener("click", () => {
    syncTsDifficultyUI();
    syncTsBgUI();
    renderTsBest();
    showScreen("tsReady");
  });
  els.tsReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Single active timer, remaining-delay pause/resume - same shape as every
  // other setTimeout-driven Test exercise. Self-paced like Hick/Suchtest
  // (a trial's response phase can end early the instant a button is
  // tapped), so this always clears any still-pending timer first.
  function scheduleTsTimer(fn, delayMs) {
    if (tsState.timer) clearTimeout(tsState.timer);
    tsState.timerFn = fn;
    tsState.timerFiresAt = performance.now() + delayMs;
    tsState.timer = setTimeout(() => { tsState.timer = null; fn(); }, delayMs);
  }

  // Random binary task sequence, regenerated whole until no run of more
  // than 3 identical trial TYPES (switch/repeat) in a row - same guard
  // convention as buildHickBlockTrials/buildFlankerTrials, so a client
  // can't settle into "just keep expecting the same thing" for a stretch.
  function buildTsTaskSeq(count) {
    let tasks, types;
    for (let tries = 0; tries < 300; tries++) {
      tasks = [];
      for (let i = 0; i < count; i++) tasks.push(Math.random() < 0.5 ? 0 : 1);
      types = [];
      for (let i = 1; i < tasks.length; i++) types.push(tasks[i] === tasks[i - 1] ? "repeat" : "switch");
      let ok = true, run = 1;
      for (let i = 1; i < types.length; i++) {
        if (types[i] === types[i - 1]) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return tasks;
  }
  function tsRandomDigit() { return TS_DIGITS[Math.floor(Math.random() * TS_DIGITS.length)]; }

  let tsState = null;
  function startTsGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.tsPlayer.hidden = false;
    els.tsPlayerBar.hidden = false;
    els.tsDonePanel.hidden = true;
    els.tsPauseOverlay.hidden = true;
    els.tsPauseBtn.hidden = false;
    const diff = TS_DIFFICULTIES[tsPrefs.difficulty];
    const taskSeq = buildTsTaskSeq(TS_TRIAL_COUNT);
    tsState = {
      diff, taskSeq, index: -1,
      phase: "gap", digit: null, task: null, type: null,
      correct: 0, incorrect: 0,
      rtByType: { repeat: [], switch: [] },
      paused: false, startTime: performance.now(), stimAt: null,
      timer: null, timerFn: null, timerFiresAt: null,
    };
    applyTsBg();
    els.tsCue.textContent = "";
    els.tsStimulus.textContent = "";
    els.tsHint.textContent = "Bereit? Gleich geht's los …";
    els.tsLeftBtn.textContent = "";
    els.tsRightBtn.textContent = "";
    els.tsLeftBtn.classList.remove("correct", "wrong");
    els.tsRightBtn.classList.remove("correct", "wrong");
    els.tsProgressEl.textContent = `0/${taskSeq.length}`;
    requestWakeLock();
    scheduleTsTimer(tsNextTrial, 1000);
  }
  els.tsReadyStartBtn.addEventListener("click", startTsGame);

  function tsNextTrial() {
    if (!tsState) return;
    tsState.index++;
    if (tsState.index >= tsState.taskSeq.length) { tsFinish(); return; }
    els.tsProgressEl.textContent = `${tsState.index + 1}/${tsState.taskSeq.length}`;
    tsState.phase = "cue";
    tsState.digit = tsRandomDigit();
    const task = TS_TASKS[tsState.taskSeq[tsState.index]];
    tsState.task = task;
    tsState.type = tsState.index === 0 ? null : (tsState.taskSeq[tsState.index] === tsState.taskSeq[tsState.index - 1] ? "repeat" : "switch");
    els.tsStimulus.textContent = "";
    els.tsHint.textContent = "";
    els.tsLeftBtn.textContent = task.leftLabel;
    els.tsRightBtn.textContent = task.rightLabel;
    els.tsLeftBtn.classList.remove("correct", "wrong");
    els.tsRightBtn.classList.remove("correct", "wrong");
    els.tsCue.textContent = task.cueLabel;
    scheduleTsTimer(tsShowStimulus, tsState.diff.csiMs);
  }
  function tsShowStimulus() {
    if (!tsState) return;
    tsState.phase = "responding";
    tsState.stimAt = performance.now();
    els.tsStimulus.textContent = String(tsState.digit);
    scheduleTsTimer(tsTimeoutTrial, tsState.diff.timeoutMs);
  }
  function tsTimeoutTrial() {
    if (!tsState || tsState.phase !== "responding") return;
    tsState.incorrect++;
    tsState.phase = "feedback";
    els.tsHint.textContent = "Verpasst!";
    scheduleTsTimer(tsAfterFeedback, TS_FEEDBACK_MS);
  }
  function tsAnswer(side) {
    if (!tsState || tsState.paused || tsState.phase !== "responding") return;
    const rt = performance.now() - tsState.stimAt;
    tsState.phase = "feedback";
    const correctSide = tsState.task.answerSide(tsState.digit);
    const tappedBtn = side === "left" ? els.tsLeftBtn : els.tsRightBtn;
    const otherBtn = side === "left" ? els.tsRightBtn : els.tsLeftBtn;
    if (side === correctSide) {
      tappedBtn.classList.add("correct");
      tsState.correct++;
      if (tsState.type) tsState.rtByType[tsState.type].push(rt);
    } else {
      tappedBtn.classList.add("wrong");
      otherBtn.classList.add("correct");
      tsState.incorrect++;
      els.tsHint.textContent = "Daneben!";
    }
    scheduleTsTimer(tsAfterFeedback, TS_FEEDBACK_MS);
  }
  function tsAfterFeedback() {
    if (!tsState) return;
    tsState.phase = "gap";
    els.tsCue.textContent = "";
    els.tsStimulus.textContent = "";
    els.tsHint.textContent = "";
    els.tsLeftBtn.textContent = "";
    els.tsRightBtn.textContent = "";
    els.tsLeftBtn.classList.remove("correct", "wrong");
    els.tsRightBtn.classList.remove("correct", "wrong");
    scheduleTsTimer(tsNextTrial, tsState.diff.isiMs);
  }
  els.tsLeftBtn.addEventListener("click", () => tsAnswer("left"));
  els.tsRightBtn.addEventListener("click", () => tsAnswer("right"));

  function pauseTs() {
    if (!tsState || tsState.paused) return;
    tsState.paused = true;
    tsState.pausedAt = performance.now();
    if (tsState.timer) {
      clearTimeout(tsState.timer);
      tsState.timer = null;
      tsState.timerRemainingMs = Math.max(0, tsState.timerFiresAt - tsState.pausedAt);
    }
    syncTsBgUI();
    els.tsPauseBtn.hidden = true;
    els.tsPauseOverlay.hidden = false;
  }
  function resumeTs() {
    if (!tsState || !tsState.paused) return;
    const pausedMs = performance.now() - tsState.pausedAt;
    tsState.startTime += pausedMs;
    if (tsState.stimAt != null) tsState.stimAt += pausedMs;
    tsState.paused = false;
    if (tsState.timerFn && tsState.timerRemainingMs != null) {
      scheduleTsTimer(tsState.timerFn, tsState.timerRemainingMs);
      tsState.timerRemainingMs = null;
    }
    els.tsPauseOverlay.hidden = true;
    els.tsPauseBtn.hidden = false;
  }
  els.tsPauseBtn.addEventListener("click", pauseTs);
  els.tsResumeBtn.addEventListener("click", resumeTs);

  function finalizeTsRun(state, totalTrials) {
    els.tsPauseOverlay.hidden = true;
    els.tsPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const avgRepeat = avgOf(state.rtByType.repeat);
    const avgSwitch = avgOf(state.rtByType.switch);
    const cost = (avgRepeat != null && avgSwitch != null) ? Math.round(avgSwitch - avgRepeat) : null;
    const isRecord = cost != null ? saveTsBest(cost) : false;
    renderTsBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.tsDoneSummary.textContent =
      `Regelwechsel-Test (${state.diff.title}) · ${accuracyPct}% richtig` +
      (avgRepeat != null ? ` · Ø gleiche Regel ${Math.round(avgRepeat)} ms` : "") +
      (avgSwitch != null ? ` · Ø nach Wechsel ${Math.round(avgSwitch)} ms` : "") +
      (cost != null ? ` · Wechselkosten ${cost} ms` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` + (cost != null ? `, Wechselkosten ${cost} ms` : "");
    const id = addHistory({ kind: "ts", title: "Regelwechsel-Test (Task-Switching)", seconds: Math.round(played), note });
    renderRating(els.tsRating, id, "Wie klar war dir jeweils, welche Regel gerade gilt?");
    els.tsDonePanel.hidden = false;
  }
  function tsFinish() {
    if (!tsState) return;
    const state = tsState;
    tsState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.tsPlayer) document.exitFullscreen().catch(() => {});
    els.tsFsHint.hidden = true;
    finalizeTsRun(state, state.taskSeq.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function tsStop() {
    if (!tsState) return;
    if (tsState.timer) clearTimeout(tsState.timer);
    const state = tsState;
    tsState = null;
    els.tsPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.tsPlayer) document.exitFullscreen().catch(() => {});
    els.tsFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= TS_MIN_RESOLVED) {
      finalizeTsRun(state, resolved);
    } else {
      els.tsPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.tsBackBtn.addEventListener("click", tsStop);
  els.tsAgainBtn.addEventListener("click", () => { els.tsDonePanel.hidden = true; startTsGame(); });
  els.tsDoneBackBtn.addEventListener("click", () => { els.tsPlayer.hidden = true; els.tsDonePanel.hidden = true; showScreen("testHome"); });

  // ---- Gegenrichtungs-Test (Antisakkaden-Prinzip) ----
  // Grounded in the antisaccade task (Hallett, 1978): a peripheral stimulus
  // automatically pulls attention/gaze toward it (the "prosaccade" response)
  // - the antisaccade variant instead instructs looking (or, here,
  // responding) AWAY from it, which requires actively inhibiting that
  // automatic pull rather than just reacting fast. Real eye movements can't
  // be measured on a phone screen, so this is built as the well-established
  // MANUAL adaptation used throughout individual-differences and applied
  // research whenever eye-tracking hardware isn't available - a fixed-
  // position dot appears left or right, and the client taps a button either
  // on the SAME side ("Pro" block - the automatic/compatible response, a
  // baseline) or the OPPOSITE side ("Anti" block - requires inhibiting that
  // same pull), same core logic as Kane, Bleckley, Conway & Engle (2001)'s
  // manual antisaccade task for measuring individual differences in
  // cognitive inhibition. Deliberately BLOCKED, not mixed trial-by-trial,
  // matching how the real paradigm (and its manual adaptations) is actually
  // administered - genuinely distinct from Regelwechsel-Test, which mixes
  // two classification RULES trial-by-trial on an ambiguous stimulus; here
  // one single, unambiguous location judgment is made throughout, and only
  // the RESPONSE MAPPING (same-side vs. opposite-side) changes, once, at
  // the block boundary. Also distinct from Simon (an automatic, uninstructed
  // location-vs-colour conflict baked into every trial) and Posner-Cueing
  // (a cue that may or may not predict the real target's location) - this
  // is the only exercise whose entire point is an EXPLICITLY INSTRUCTED
  // override of an automatic orienting response. Also researched as sport-
  // relevant: volleyball players showed a different interference pattern
  // between saccadic and key-press reaction times than non-athletes on this
  // exact manual/oculomotor contrast (Kokubu, Ando, Kida & Oda, 2006); more
  // recent work links athletes' antisaccade performance to distinct
  // microsaccade-preparation behaviour and shows prior high cognitive
  // demand measurably lowers subsequent manual-antisaccade performance
  // (2026 studies) - a fit for FWMC's inhibitory-control/visuelle-
  // Entscheidungsgeschwindigkeit focus specifically.
  const ANTI_DIFFICULTIES = {
    // Self-paced (a tap ends a trial immediately) with only a generous
    // safety-net timeout, same shape as Regelwechsel-Test/Suchtest/Hick -
    // there's no "fixed full-duration response window" here (unlike Simon/
    // Flanker/Posner) since direction ERRORS, not raw speed, are the classic
    // antisaccade outcome, and truncating slower (especially Anti-block) RTs
    // with a tight fixed window would bias the very cost this exercise
    // measures. isiMs is the fixation-only foreperiod before each dot
    // appears; only that foreperiod and the timeout shrink with difficulty.
    leicht: { title: "Leicht", isiMs: 900, timeoutMs: 3000 },
    mittel: { title: "Mittel", isiMs: 600, timeoutMs: 2200 },
    schwer: { title: "Schwer", isiMs: 400, timeoutMs: 1600 },
  };
  const ANTI_TRIALS_PER_BLOCK = 16; // 16 Pro + 16 Anti = 32 total, comparable scale to Flanker/Rotationstest
  const ANTI_FEEDBACK_MS = 400;
  const ANTI_BLOCK_INTRO_MS = 3200; // long enough to actually read the new block's rule before the first dot
  const ANTI_MIN_RESOLVED = 8;
  const ANTI_PREFS_KEY = "fwmc-anti-prefs-v1";
  const antiPrefs = { difficulty: "mittel", bgColorKey: "gruen", bgIntensity: 0 };
  function loadAntiPrefs() {
    const saved = readJSON(ANTI_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(antiPrefs, saved);
    if (!ANTI_DIFFICULTIES[antiPrefs.difficulty]) antiPrefs.difficulty = "mittel";
    if (!STROOP_COLOR_BY_KEY[antiPrefs.bgColorKey]) antiPrefs.bgColorKey = "gruen";
    if (typeof antiPrefs.bgIntensity !== "number" || antiPrefs.bgIntensity < 0 || antiPrefs.bgIntensity > 1) antiPrefs.bgIntensity = 0;
  }
  loadAntiPrefs();
  function saveAntiPrefsToStorage() { writeJSON(ANTI_PREFS_KEY, antiPrefs); }

  // Background colour/intensity, added later - see CLAUDE.md Established
  // patterns (every Test-Bereich exercise now gets the same background
  // control NAT's Remember/Blitz/Flash/MOT already have, minus their
  // transfer/preset-save machinery - a deliberate scope decision, see there).
  function applyAntiBg() {
    els.antiStage.style.background = antiPrefs.bgIntensity > 0
      ? mixHex("#ffffff", STROOP_COLOR_BY_KEY[antiPrefs.bgColorKey].hex, antiPrefs.bgIntensity)
      : "";
  }
  const syncAntiBgUI = wireBgIntensityControl(antiPrefs, {
    pickers: [els.antiBgColorPicker, els.antiPauseBgColorPicker],
    sliders: [els.antiBgIntensitySlider, els.antiPauseBgSlider],
    valueEls: [els.antiBgIntensityValue, els.antiPauseBgValue],
    hintEls: [els.antiBgContrastHint],
  }, () => { saveAntiPrefsToStorage(); applyAntiBg(); });

  const ANTI_BEST_KEY = "fwmc-anti-best-v1"; // { [difficulty]: bestHemmKostenMs } - lower is better, same shape as TS_BEST_KEY
  function antiBestFor() {
    const v = readJSON(ANTI_BEST_KEY, {})[antiPrefs.difficulty];
    return typeof v === "number" ? v : null;
  }
  function saveAntiBest(cost) {
    const all = readJSON(ANTI_BEST_KEY, {});
    const cur = all[antiPrefs.difficulty];
    if (cur == null || cost < cur) { all[antiPrefs.difficulty] = cost; writeJSON(ANTI_BEST_KEY, all); return true; }
    return false;
  }
  function renderAntiBest() {
    const best = antiBestFor();
    const text = best != null ? `Niedrigste Hemm-Kosten (${ANTI_DIFFICULTIES[antiPrefs.difficulty].title}): ${Math.round(best)} ms` : "";
    els.antiBestHint.textContent = text;
    els.antiReadyBestHint.textContent = text;
  }
  renderAntiBest();
  function syncAntiDifficultyUI() {
    els.antiDifficultyRow.querySelectorAll("[data-anti-diff]").forEach((btn) => setActive(btn, btn.dataset.antiDiff === antiPrefs.difficulty));
  }
  els.antiDifficultyRow.querySelectorAll("[data-anti-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      antiPrefs.difficulty = btn.dataset.antiDiff;
      saveAntiPrefsToStorage();
      syncAntiDifficultyUI();
      renderAntiBest();
    });
  });
  els.antiOpenBtn.addEventListener("click", () => {
    syncAntiDifficultyUI();
    syncAntiBgUI();
    renderAntiBest();
    showScreen("antiReady");
  });
  els.antiReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Single active timer, remaining-delay pause/resume - same shape as every
  // other setTimeout-driven Test exercise.
  function scheduleAntiTimer(fn, delayMs) {
    if (antiState.timer) clearTimeout(antiState.timer);
    antiState.timerFn = fn;
    antiState.timerFiresAt = performance.now() + delayMs;
    antiState.timer = setTimeout(() => { antiState.timer = null; fn(); }, delayMs);
  }

  // Balanced left/right side sequence with the same "no more than 3 in a
  // row identical" guard used throughout this Test tab, so a client can't
  // settle into "just keep tapping the same button" for a stretch.
  function buildAntiSideSeq(n) {
    let sides;
    for (let tries = 0; tries < 300; tries++) {
      sides = [];
      for (let i = 0; i < n / 2; i++) sides.push("left", "right");
      for (let i = sides.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [sides[i], sides[j]] = [sides[j], sides[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < sides.length; i++) {
        if (sides[i] === sides[i - 1]) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return sides;
  }
  // Pro block always first (the automatic/compatible mapping, doubling as a
  // baseline/practice block) then Anti - matches how the real paradigm is
  // conventionally administered. A fixed order, not counterbalanced (see
  // Offene Fragen), same limitation already flagged for Wahlreaktionstest's
  // own fixed 2->4->8 block order.
  function buildAntiTrials() {
    const pro = buildAntiSideSeq(ANTI_TRIALS_PER_BLOCK).map((side) => ({ block: "pro", side }));
    const anti = buildAntiSideSeq(ANTI_TRIALS_PER_BLOCK).map((side) => ({ block: "anti", side }));
    return pro.concat(anti);
  }
  function antiClearDots() {
    els.antiDotLeft.classList.remove("show");
    els.antiDotRight.classList.remove("show");
  }

  let antiState = null;
  function startAntiGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.antiPlayer.hidden = false;
    els.antiPlayerBar.hidden = false;
    els.antiDonePanel.hidden = true;
    els.antiPauseOverlay.hidden = true;
    els.antiPauseBtn.hidden = false;
    const diff = ANTI_DIFFICULTIES[antiPrefs.difficulty];
    const trials = buildAntiTrials();
    antiState = {
      diff, trials, index: -1,
      phase: "isi", side: null, block: null,
      correct: 0, incorrect: 0,
      rtByBlock: { pro: [], anti: [] },
      paused: false, startTime: performance.now(), stimAt: null,
      timer: null, timerFn: null, timerFiresAt: null,
    };
    applyAntiBg();
    els.antiRule.textContent = "";
    antiClearDots();
    els.antiHint.textContent = "Bereit? Gleich geht's los …";
    els.antiLeftBtn.classList.remove("correct", "wrong");
    els.antiRightBtn.classList.remove("correct", "wrong");
    els.antiProgressEl.textContent = `0/${trials.length}`;
    requestWakeLock();
    scheduleAntiTimer(antiNextTrial, 1000);
  }
  els.antiReadyStartBtn.addEventListener("click", startAntiGame);

  function antiNextTrial() {
    if (!antiState) return;
    antiState.index++;
    if (antiState.index >= antiState.trials.length) { antiFinish(); return; }
    const trial = antiState.trials[antiState.index];
    const blockChanged = antiState.block !== trial.block;
    antiState.block = trial.block;
    antiState.side = trial.side;
    antiState.phase = "isi";
    els.antiProgressEl.textContent = `${antiState.index + 1}/${antiState.trials.length}`;
    antiClearDots();
    els.antiLeftBtn.classList.remove("correct", "wrong");
    els.antiRightBtn.classList.remove("correct", "wrong");
    els.antiRule.textContent = trial.block === "pro" ? "Regel: GLEICHE SEITE" : "Regel: GEGENTEIL";
    if (blockChanged) {
      els.antiHint.textContent = trial.block === "pro"
        ? "Block 1 von 2 — tippe auf die Seite, auf der der Punkt erscheint."
        : "Block 2 von 2 — jetzt bewusst auf die ANDERE Seite tippen!";
      scheduleAntiTimer(antiShowStimulus, ANTI_BLOCK_INTRO_MS);
    } else {
      els.antiHint.textContent = "";
      scheduleAntiTimer(antiShowStimulus, antiState.diff.isiMs);
    }
  }
  function antiShowStimulus() {
    if (!antiState) return;
    antiState.phase = "responding";
    antiState.stimAt = performance.now();
    const dot = antiState.side === "left" ? els.antiDotLeft : els.antiDotRight;
    dot.classList.add("show");
    scheduleAntiTimer(antiTimeoutTrial, antiState.diff.timeoutMs);
  }
  function antiTimeoutTrial() {
    if (!antiState || antiState.phase !== "responding") return;
    antiState.incorrect++;
    antiState.phase = "feedback";
    els.antiHint.textContent = "Verpasst!";
    scheduleAntiTimer(antiAfterFeedback, ANTI_FEEDBACK_MS);
  }
  function antiAnswer(side) {
    if (!antiState || antiState.paused || antiState.phase !== "responding") return;
    const rt = performance.now() - antiState.stimAt;
    antiState.phase = "feedback";
    const correctSide = antiState.block === "pro" ? antiState.side : (antiState.side === "left" ? "right" : "left");
    const tappedBtn = side === "left" ? els.antiLeftBtn : els.antiRightBtn;
    const otherBtn = side === "left" ? els.antiRightBtn : els.antiLeftBtn;
    if (side === correctSide) {
      tappedBtn.classList.add("correct");
      antiState.correct++;
      antiState.rtByBlock[antiState.block].push(rt);
    } else {
      tappedBtn.classList.add("wrong");
      otherBtn.classList.add("correct");
      antiState.incorrect++;
      els.antiHint.textContent = "Daneben!";
    }
    scheduleAntiTimer(antiAfterFeedback, ANTI_FEEDBACK_MS);
  }
  function antiAfterFeedback() {
    if (!antiState) return;
    antiState.phase = "isi";
    antiClearDots();
    els.antiHint.textContent = "";
    els.antiLeftBtn.classList.remove("correct", "wrong");
    els.antiRightBtn.classList.remove("correct", "wrong");
    antiNextTrial();
  }
  els.antiLeftBtn.addEventListener("click", () => antiAnswer("left"));
  els.antiRightBtn.addEventListener("click", () => antiAnswer("right"));

  function pauseAnti() {
    if (!antiState || antiState.paused) return;
    antiState.paused = true;
    antiState.pausedAt = performance.now();
    if (antiState.timer) {
      clearTimeout(antiState.timer);
      antiState.timer = null;
      antiState.timerRemainingMs = Math.max(0, antiState.timerFiresAt - antiState.pausedAt);
    }
    syncAntiBgUI();
    els.antiPauseBtn.hidden = true;
    els.antiPauseOverlay.hidden = false;
  }
  function resumeAnti() {
    if (!antiState || !antiState.paused) return;
    const pausedMs = performance.now() - antiState.pausedAt;
    antiState.startTime += pausedMs;
    if (antiState.stimAt != null) antiState.stimAt += pausedMs;
    antiState.paused = false;
    if (antiState.timerFn && antiState.timerRemainingMs != null) {
      scheduleAntiTimer(antiState.timerFn, antiState.timerRemainingMs);
      antiState.timerRemainingMs = null;
    }
    els.antiPauseOverlay.hidden = true;
    els.antiPauseBtn.hidden = false;
  }
  els.antiPauseBtn.addEventListener("click", pauseAnti);
  els.antiResumeBtn.addEventListener("click", resumeAnti);

  function finalizeAntiRun(state, totalTrials) {
    els.antiPauseOverlay.hidden = true;
    els.antiPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const avgPro = avgOf(state.rtByBlock.pro);
    const avgAnti = avgOf(state.rtByBlock.anti);
    const cost = (avgPro != null && avgAnti != null) ? Math.round(avgAnti - avgPro) : null;
    const isRecord = cost != null ? saveAntiBest(cost) : false;
    renderAntiBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.antiDoneSummary.textContent =
      `Gegenrichtungs-Test (${state.diff.title}) · ${accuracyPct}% richtig` +
      (avgPro != null ? ` · Ø gleiche Seite ${Math.round(avgPro)} ms` : "") +
      (avgAnti != null ? ` · Ø Gegenteil ${Math.round(avgAnti)} ms` : "") +
      (cost != null ? ` · Hemm-Kosten ${cost} ms` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` + (cost != null ? `, Hemm-Kosten ${cost} ms` : "");
    const id = addHistory({ kind: "anti", title: "Gegenrichtungs-Test (Antisakkaden-Prinzip)", seconds: Math.round(played), note });
    renderRating(els.antiRating, id, "Wie leicht fiel es dir, im zweiten Block bewusst gegenzusteuern?");
    els.antiDonePanel.hidden = false;
  }
  function antiFinish() {
    if (!antiState) return;
    const state = antiState;
    antiState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.antiPlayer) document.exitFullscreen().catch(() => {});
    els.antiFsHint.hidden = true;
    finalizeAntiRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function antiStop() {
    if (!antiState) return;
    if (antiState.timer) clearTimeout(antiState.timer);
    const state = antiState;
    antiState = null;
    els.antiPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.antiPlayer) document.exitFullscreen().catch(() => {});
    els.antiFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= ANTI_MIN_RESOLVED) {
      finalizeAntiRun(state, resolved);
    } else {
      els.antiPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.antiBackBtn.addEventListener("click", antiStop);
  els.antiAgainBtn.addEventListener("click", () => { els.antiDonePanel.hidden = true; startAntiGame(); });
  els.antiDoneBackBtn.addEventListener("click", () => { els.antiPlayer.hidden = true; els.antiDonePanel.hidden = true; showScreen("testHome"); });

  // ---- Wortfarben-Test (Stroop-Aufgabe) ----
  // Eighteenth autonomous entry (see CLAUDE.md's "Test-Bereich (autonomous,
  // ongoing)"). Grounded in the classic Stroop colour-word task (Stroop,
  // 1935, "Studies of interference in serial verbal reactions", Journal of
  // Experimental Psychology 18(6), 643-662): a colour NAME ("ROT"/"BLAU"/
  // "GRÜN"/"GELB") is printed in one of four ink colours, and the client
  // must name the INK colour, ignoring the word's meaning. Reading a
  // familiar word is a fast, automatic process that keeps happening
  // whether or not it's wanted, so when the word's meaning conflicts with
  // its own ink colour ("incongruent" - e.g. "ROT" printed in blue) that
  // automatic reading response competes with the instructed colour-naming
  // response, and correct answers come slower and less accurately than
  // when word and ink agree ("congruent") - the classic Stroop effect, one
  // of the most replicated findings in cognitive psychology. Also
  // researched as sport-relevant before building: "Enhanced Cognitive
  // Inhibition in Table Tennis Athletes: Insights from Color-Word and
  // Spatial Stroop Tasks" (2024, PMC11117886) found table-tennis athletes
  // showed a SMALLER Stroop effect (faster, more stable colour-naming
  // despite the word conflict) than non-athletes on both the classic
  // colour-word Stroop task and a spatial Stroop variant - a fit for
  // FWMC's "visuelle Entscheidungsgeschwindigkeit" focus. Genuinely
  // distinct from every existing Test/NAT mechanic: Simon's conflict comes
  // from a stimulus's task-IRRELEVANT spatial location automatically
  // priming a response side, with no verbal/reading component at all;
  // Flanker's conflict comes from simultaneous DISTRACTOR stimuli
  // surrounding an unambiguous central target; Regelwechsel-Test mixes two
  // classification RULES on one ambiguous stimulus, but the stimulus
  // itself (a bare digit) has no automatic reading response competing with
  // anything - this is the only exercise whose interference comes from
  // WITHIN a single stimulus, between its automatically-read verbal
  // identity and the separate perceptual dimension (colour) actually being
  // judged.
  const STROOP_PREFS_KEY = "fwmc-stroop-prefs-v1";
  // Difficulty controls the response window and inter-trial gap - same
  // shape and the same numbers as SIMON_DIFFICULTIES/FLANKER_DIFFICULTIES
  // (a single-stimulus, immediate-response task of comparable load).
  const STROOP_DIFFICULTIES = {
    leicht: { title: "Leicht", responseMs: 2200, isiMin: 900, isiMax: 1400 },
    mittel: { title: "Mittel", responseMs: 1600, isiMin: 700, isiMax: 1100 },
    schwer: { title: "Schwer", responseMs: 1100, isiMin: 500, isiMax: 900 },
  };
  // Four colours, fixed hex throughout (never var(--...)). "gruen"/"gelb"
  // are plain ASCII keys internally; the displayed word/button text uses
  // the proper German spelling.
  const STROOP_COLORS = {
    rot: { title: "Rot", word: "ROT", hex: "#d6373c" },
    blau: { title: "Blau", word: "BLAU", hex: "#2f6fed" },
    gruen: { title: "Grün", word: "GRÜN", hex: "#1f9d55" },
    gelb: { title: "Gelb", word: "GELB", hex: "#e0a300" },
  };
  const STROOP_COLOR_KEYS = Object.keys(STROOP_COLORS);
  // 48 trials: 24 congruent (6 per colour, word == ink) + 24 incongruent
  // (2 reps of each of the 12 word≠ink combinations) - a balanced 50/50
  // congruent/incongruent split, same "enough per condition for a
  // meaningful RT comparison" reasoning as Simon's own 20/20 split, with
  // every colour appearing equally often as the correct (ink) answer.
  const STROOP_MIN_RESOLVED = 4;
  const stroopPrefs = { difficulty: "mittel" };
  function loadStroopPrefs() {
    const saved = readJSON(STROOP_PREFS_KEY, null);
    if (saved && typeof saved === "object") Object.assign(stroopPrefs, saved);
    if (!STROOP_DIFFICULTIES[stroopPrefs.difficulty]) stroopPrefs.difficulty = "mittel";
  }
  loadStroopPrefs();
  function saveStroopPrefsToStorage() { writeJSON(STROOP_PREFS_KEY, stroopPrefs); }

  const STROOP_BEST_KEY = "fwmc-stroop-best-v1"; // { [difficulty]: bestAccuracyPct }
  function stroopBestFor() { return readJSON(STROOP_BEST_KEY, {})[stroopPrefs.difficulty] || 0; }
  function saveStroopBest(accuracyPct) {
    const all = readJSON(STROOP_BEST_KEY, {});
    if (accuracyPct > (all[stroopPrefs.difficulty] || 0)) { all[stroopPrefs.difficulty] = accuracyPct; writeJSON(STROOP_BEST_KEY, all); return true; }
    return false;
  }
  function renderStroopBest() {
    const best = stroopBestFor();
    const text = best ? `Beste Genauigkeit (${STROOP_DIFFICULTIES[stroopPrefs.difficulty].title}): ${best}%` : "";
    els.stroopBestHint.textContent = text;
    els.stroopReadyBestHint.textContent = text;
  }
  function syncStroopDifficultyUI() {
    els.stroopDifficultyRow.querySelectorAll("[data-stroop-diff]").forEach((btn) => setActive(btn, btn.dataset.stroopDiff === stroopPrefs.difficulty));
  }
  els.stroopDifficultyRow.querySelectorAll("[data-stroop-diff]").forEach((btn) => {
    btn.addEventListener("click", () => {
      stroopPrefs.difficulty = btn.dataset.stroopDiff;
      saveStroopPrefsToStorage();
      syncStroopDifficultyUI();
      renderStroopBest();
    });
  });

  els.stroopOpenBtn.addEventListener("click", () => {
    syncStroopDifficultyUI();
    renderStroopBest();
    showScreen("stroopReady");
  });
  els.stroopReadyBackToHome.addEventListener("click", () => showScreen("testHome"));

  // Same timer-wrapping trick as scheduleSimonTimer/scheduleFlankerTimer:
  // records what's pending and when it fires, so Pause can cancel it and
  // Resume can replay it with its exact remaining delay.
  function scheduleStroopTimer(fn, delayMs) {
    stroopState.timerFn = fn;
    stroopState.timerFiresAt = performance.now() + delayMs;
    stroopState.timer = setTimeout(() => { stroopState.timer = null; fn(); }, delayMs);
  }

  function buildStroopTrials() {
    const trials = [];
    STROOP_COLOR_KEYS.forEach((color) => {
      for (let i = 0; i < 6; i++) trials.push({ ink: color, word: color });
    });
    STROOP_COLOR_KEYS.forEach((ink) => {
      STROOP_COLOR_KEYS.forEach((word) => {
        if (word === ink) return;
        for (let i = 0; i < 2; i++) trials.push({ ink, word });
      });
    });
    // Shuffle, then avoid more than 3 identical correct (ink-determined)
    // responses back to back - same guard as buildSimonTrials/
    // buildFlankerTrials, so a "just keep tapping the same button" motor
    // strategy can't pass undetected.
    for (let tries = 0; tries < 200; tries++) {
      for (let i = trials.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [trials[i], trials[j]] = [trials[j], trials[i]];
      }
      let ok = true, run = 1;
      for (let i = 1; i < trials.length; i++) {
        if (trials[i].ink === trials[i - 1].ink) { run++; if (run > 3) { ok = false; break; } }
        else run = 1;
      }
      if (ok) break;
    }
    return trials;
  }

  function stroopBtnFor(color) { return els.stroopResponseRow.querySelector(`[data-stroop-color="${color}"]`); }
  function stroopClearStage() {
    els.stroopWord.textContent = "";
    els.stroopWord.style.color = "";
    els.stroopResponseRow.querySelectorAll("[data-stroop-color]").forEach((btn) => btn.classList.remove("correct", "wrong"));
  }

  let stroopState = null;
  function startStroopGame() {
    hideAllPlayers();
    SCREENS.forEach((s) => { els[s].hidden = true; });
    els.stroopPlayer.hidden = false;
    els.stroopPlayerBar.hidden = false;
    els.stroopDonePanel.hidden = true;
    els.stroopPauseOverlay.hidden = true;
    els.stroopPauseBtn.hidden = false;
    stroopState = {
      diff: STROOP_DIFFICULTIES[stroopPrefs.difficulty], trials: buildStroopTrials(), index: -1, phase: "gap", responded: false,
      correct: 0, incorrect: 0, timeouts: 0, rtsCongruent: [], rtsIncongruent: [],
      stimAt: 0, paused: false, timer: null, timerFn: null, timerFiresAt: 0, timerRemainingMs: null,
      startTime: performance.now(),
    };
    stroopClearStage();
    els.stroopHint.textContent = "Bereit? Gleich geht's los …";
    els.stroopProgressEl.textContent = `0/${stroopState.trials.length}`;
    requestWakeLock();
    scheduleStroopTimer(stroopNextTrial, 1200);
  }
  els.stroopReadyStartBtn.addEventListener("click", startStroopGame);

  function stroopNextTrial() {
    if (!stroopState) return;
    stroopState.index++;
    if (stroopState.index >= stroopState.trials.length) { stroopFinish(); return; }
    els.stroopProgressEl.textContent = `${stroopState.index + 1}/${stroopState.trials.length}`;
    stroopState.phase = "gap";
    stroopState.responded = false;
    stroopClearStage();
    const isi = stroopState.diff.isiMin + Math.random() * (stroopState.diff.isiMax - stroopState.diff.isiMin);
    scheduleStroopTimer(stroopShowStimulus, isi);
  }
  function stroopShowStimulus() {
    if (!stroopState) return;
    const trial = stroopState.trials[stroopState.index];
    stroopState.phase = "responding";
    stroopState.responded = false;
    stroopState.stimAt = performance.now();
    els.stroopHint.textContent = "";
    stroopClearStage();
    els.stroopWord.textContent = STROOP_COLORS[trial.word].word;
    els.stroopWord.style.color = STROOP_COLORS[trial.ink].hex;
    scheduleStroopTimer(stroopEndTrial, stroopState.diff.responseMs);
  }
  function stroopEndTrial() {
    if (!stroopState) return;
    if (stroopState.phase === "responding" && !stroopState.responded) {
      stroopState.incorrect++;
      stroopState.timeouts++;
      els.stroopHint.textContent = "Verpasst!";
    }
    stroopState.phase = "gap";
    stroopNextTrial();
  }
  function stroopTap(color) {
    if (!stroopState || stroopState.paused || stroopState.responded) return;
    // Taps before the word actually appears are ignored - reaction time is
    // measured stimulus-locked, same convention as Simon's/Flanker's own
    // tap handlers.
    if (stroopState.phase !== "responding") return;
    stroopState.responded = true;
    const trial = stroopState.trials[stroopState.index];
    const rt = performance.now() - stroopState.stimAt;
    const isCorrect = color === trial.ink;
    const congruent = trial.word === trial.ink;
    stroopBtnFor(color).classList.add(isCorrect ? "correct" : "wrong");
    if (isCorrect) {
      stroopState.correct++;
      (congruent ? stroopState.rtsCongruent : stroopState.rtsIncongruent).push(rt);
    } else {
      stroopState.incorrect++;
      els.stroopHint.textContent = "Falsche Farbe!";
    }
    // The feedback ring stays up for whatever's left of diff.responseMs
    // (the already-scheduled stroopEndTrial fires the actual transition) -
    // same rhythm as Simon/Flanker leaving their own tap feedback up for
    // the rest of the response window, no separate timer needed.
  }
  els.stroopResponseRow.querySelectorAll("[data-stroop-color]").forEach((btn) => {
    btn.addEventListener("click", () => stroopTap(btn.dataset.stroopColor));
  });

  // Pause just stops/replays the pending timer, no live background-adjust
  // overlay - background colour customisation was skipped for this
  // exercise (explicitly optional per the Test-Bereich guidance) so there
  // is nothing to adjust while paused.
  function pauseStroop() {
    if (!stroopState || stroopState.paused) return;
    stroopState.paused = true;
    stroopState.pausedAt = performance.now();
    if (stroopState.timer) {
      clearTimeout(stroopState.timer);
      stroopState.timer = null;
      stroopState.timerRemainingMs = Math.max(0, stroopState.timerFiresAt - stroopState.pausedAt);
    }
    els.stroopPauseBtn.hidden = true;
    els.stroopPauseOverlay.hidden = false;
  }
  function resumeStroop() {
    if (!stroopState || !stroopState.paused) return;
    const pausedMs = performance.now() - stroopState.pausedAt;
    stroopState.startTime += pausedMs;
    stroopState.stimAt += pausedMs;
    stroopState.paused = false;
    if (stroopState.timerFn && stroopState.timerRemainingMs != null) {
      scheduleStroopTimer(stroopState.timerFn, stroopState.timerRemainingMs);
      stroopState.timerRemainingMs = null;
    }
    els.stroopPauseOverlay.hidden = true;
    els.stroopPauseBtn.hidden = false;
  }
  els.stroopPauseBtn.addEventListener("click", pauseStroop);
  els.stroopResumeBtn.addEventListener("click", resumeStroop);

  function finalizeStroopRun(state, totalTrials) {
    els.stroopPauseOverlay.hidden = true;
    els.stroopPlayerBar.hidden = true;
    const accuracyPct = Math.round(100 * state.correct / totalTrials);
    const avgCong = avgOf(state.rtsCongruent);
    const avgIncong = avgOf(state.rtsIncongruent);
    // The Stroop effect itself: how much slower correct incongruent
    // responses were versus correct congruent ones - the classic
    // word-colour interference cost this paradigm exists to surface.
    const stroopEffect = (avgCong != null && avgIncong != null) ? (avgIncong - avgCong) : null;
    const isRecord = saveStroopBest(accuracyPct);
    renderStroopBest();
    const played = (performance.now() - state.startTime) / 1000;
    els.stroopDoneSummary.textContent =
      `Wortfarben-Test (${state.diff.title}) · ${accuracyPct}% richtig` +
      (avgCong != null ? ` · Ø kongruent ${avgCong} ms` : "") +
      (avgIncong != null ? ` · Ø inkongruent ${avgIncong} ms` : "") +
      (stroopEffect != null ? ` · Stroop-Effekt ${stroopEffect} ms` : "") +
      (isRecord ? " · Neue Bestleistung!" : "");
    const note = `${accuracyPct}% richtig` + (stroopEffect != null ? `, Stroop-Effekt ${stroopEffect} ms` : "");
    const id = addHistory({ kind: "stroop", title: "Wortfarben-Test (Stroop-Aufgabe)", seconds: Math.round(played), note });
    renderRating(els.stroopRating, id, "Wie fokussiert warst du?");
    els.stroopDonePanel.hidden = false;
  }
  function stroopFinish() {
    if (!stroopState) return;
    const state = stroopState;
    stroopState = null;
    releaseWakeLock();
    if (document.fullscreenElement === els.stroopPlayer) document.exitFullscreen().catch(() => {});
    els.stroopFsHint.hidden = true;
    finalizeStroopRun(state, state.trials.length);
  }
  // "Beenden" doubles as the finish action, same convention as every other
  // Test/NAT exercise - quitting early still shows a summary as long as at
  // least a few trials were actually resolved.
  function stroopStop() {
    if (!stroopState) return;
    if (stroopState.timer) clearTimeout(stroopState.timer);
    const state = stroopState;
    stroopState = null;
    els.stroopPauseOverlay.hidden = true;
    releaseWakeLock();
    if (document.fullscreenElement === els.stroopPlayer) document.exitFullscreen().catch(() => {});
    els.stroopFsHint.hidden = true;
    const resolved = state.correct + state.incorrect;
    if (resolved >= STROOP_MIN_RESOLVED) {
      finalizeStroopRun(state, resolved);
    } else {
      els.stroopPlayer.hidden = true;
      showScreen("testHome");
    }
  }
  els.stroopBackBtn.addEventListener("click", stroopStop);
  els.stroopAgainBtn.addEventListener("click", () => { els.stroopDonePanel.hidden = true; startStroopGame(); });
  els.stroopDoneBackBtn.addEventListener("click", () => { els.stroopPlayer.hidden = true; els.stroopDonePanel.hidden = true; showScreen("testHome"); });
  wireFullscreen({ player: els.stroopPlayer, btn: els.stroopFsBtn, hint: els.stroopFsHint, hintOpen: els.stroopFsHintOpenBtn, hintClose: els.stroopFsHintClose });

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
