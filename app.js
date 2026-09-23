(() => {
  "use strict";

  // ---- Shared palette (matches FWMC's existing training colour library) ----
  const BLUE = "#1565c0";
  const GREEN = "#2e7d32";
  const RED = "#d32f2f";
  const INK = "#16232a";
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
  const INVERT_OF = { Vorne: "Hinten", Hinten: "Vorne", Rechts: "Links", Links: "Rechts" };

  // ---- Palette library: the same 20 three-colour combinations from the
  // production ARCHITECTURE/PALETTES/*.json files, ported as data so
  // VT/VRW can use the exact same colour meanings as the real videos.
  const C = {
    orange: "#ff9110", rot: "#d32f2f", lila: "#7e4fbe",
    blau: "#1565c0", gruen: "#2e7d32", gelb: "#f2a900",
    orl_orange: "#ff911f", orl_rot: "#e84835",
  };
  function pal(id, name, colors) { return { id, name, colors }; }
  const PALETTES = {
    ORL: pal("ORL", "Orange Rot Lila", [{ name: "Orange", hex: "#ff911f" }, { name: "Rot", hex: "#e84835" }, { name: "Lila", hex: C.lila }]),
    RGB: pal("RGB", "Rot Grün Blau", [{ name: "Rot", hex: C.rot }, { name: "Blau", hex: C.blau }, { name: "Grün", hex: C.gruen }]),
    RGY: pal("RGY", "Rot Grün Gelb", [{ name: "Rot", hex: C.rot }, { name: "Grün", hex: C.gruen }, { name: "Gelb", hex: C.gelb }]),
    RYB: pal("RYB", "Rot Gelb Blau", [{ name: "Rot", hex: C.rot }, { name: "Gelb", hex: C.gelb }, { name: "Blau", hex: C.blau }]),
    YGB: pal("YGB", "Gelb Grün Blau", [{ name: "Gelb", hex: C.gelb }, { name: "Grün", hex: C.gruen }, { name: "Blau", hex: C.blau }]),
    ORB: pal("ORB", "Orange Rot Blau", [{ name: "Orange", hex: C.orange }, { name: "Rot", hex: C.rot }, { name: "Blau", hex: C.blau }]),
    ORG: pal("ORG", "Orange Rot Grün", [{ name: "Orange", hex: C.orange }, { name: "Rot", hex: C.rot }, { name: "Grün", hex: C.gruen }]),
    ORY: pal("ORY", "Orange Rot Gelb", [{ name: "Orange", hex: C.orange }, { name: "Rot", hex: C.rot }, { name: "Gelb", hex: C.gelb }]),
    OLB: pal("OLB", "Orange Lila Blau", [{ name: "Orange", hex: C.orange }, { name: "Lila", hex: C.lila }, { name: "Blau", hex: C.blau }]),
    OLG: pal("OLG", "Orange Lila Grün", [{ name: "Orange", hex: C.orange }, { name: "Lila", hex: C.lila }, { name: "Grün", hex: C.gruen }]),
    OLY: pal("OLY", "Orange Lila Gelb", [{ name: "Orange", hex: C.orange }, { name: "Lila", hex: C.lila }, { name: "Gelb", hex: C.gelb }]),
    OBG: pal("OBG", "Orange Blau Grün", [{ name: "Orange", hex: C.orange }, { name: "Blau", hex: C.blau }, { name: "Grün", hex: C.gruen }]),
    OBY: pal("OBY", "Orange Blau Gelb", [{ name: "Orange", hex: C.orange }, { name: "Blau", hex: C.blau }, { name: "Gelb", hex: C.gelb }]),
    OGY: pal("OGY", "Orange Grün Gelb", [{ name: "Orange", hex: C.orange }, { name: "Grün", hex: C.gruen }, { name: "Gelb", hex: C.gelb }]),
    RLB: pal("RLB", "Rot Lila Blau", [{ name: "Rot", hex: C.rot }, { name: "Lila", hex: C.lila }, { name: "Blau", hex: C.blau }]),
    RLG: pal("RLG", "Rot Lila Grün", [{ name: "Rot", hex: C.rot }, { name: "Lila", hex: C.lila }, { name: "Grün", hex: C.gruen }]),
    RLY: pal("RLY", "Rot Lila Gelb", [{ name: "Rot", hex: C.rot }, { name: "Lila", hex: C.lila }, { name: "Gelb", hex: C.gelb }]),
    LBG: pal("LBG", "Lila Blau Grün", [{ name: "Lila", hex: C.lila }, { name: "Blau", hex: C.blau }, { name: "Grün", hex: C.gruen }]),
    LBY: pal("LBY", "Lila Blau Gelb", [{ name: "Lila", hex: C.lila }, { name: "Blau", hex: C.blau }, { name: "Gelb", hex: C.gelb }]),
    LGY: pal("LGY", "Lila Grün Gelb", [{ name: "Lila", hex: C.lila }, { name: "Grün", hex: C.gruen }, { name: "Gelb", hex: C.gelb }]),
  };
  const PALETTE_ORDER = ["ORL", "RGB", "RGY", "RYB", "YGB", "ORB", "ORG", "ORY", "OLB", "OLG", "OLY", "OBG", "OBY", "OGY", "RLB", "RLG", "RLY", "LBG", "LBY", "LGY"];

  // ---- Seeded RNG (mulberry32) so a chosen "Sequenz" (S01-S05) always
  // reproduces the exact same stimulus order for the same settings -
  // matching the deterministic seed_pair() behaviour of the real render
  // pipeline. "Zufällig" keeps using Math.random for a fresh draw each run.
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

  // ---- Audio: spoken direction words (Web Speech API) + a plain beep
  // (Web Audio API). No audio files needed, works fully offline once the
  // page/voices are loaded once.
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
      ctx.arc(cx, cy, unit * 0.026, 0, Math.PI * 2);
      ctx.fill();
    } else if (kind === "count") {
      ctx.fillStyle = INK;
      ctx.font = `800 ${Math.round(unit * 0.5)}px Magra, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(payload.n), cx, cy);
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
      const size = fitText(ctx, payload.word, cw * 0.82, Math.round(unit * 0.62), "Magra, sans-serif", 800);
      ctx.font = `800 ${size}px Magra, sans-serif`;
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

  // ---- Exercise catalogue (drives the "ready" sub-screen) ----
  const EXERCISES = {
    "vt-color": {
      title: "VT · Farbe + Handseite",
      type: "vt",
      usesPalette: true,
      rules:
        "Original-System: Hintergrundfarbe aus der gewählten Palette + weißer Pfeil = Handseite (links/rechts). Portierung des echten VT-Prinzips – die genaue Sequenz-Balancierung des Original-Algorithmus ist hier vereinfacht (gleichverteilt statt kontrolliert-zufällig).",
    },
    "vrw-original": {
      title: "VRW · Original (Direkt/Umgekehrt)",
      type: "vrw-real",
      usesPalette: true,
      rules:
        "Original-System: Weißer Pfeil auf Farbe = gezeigte Seite zählt (direkt). Farbiger Pfeil auf Weiß = Gegenseite zählt (umgekehrt). Portierung des echten VRW-Prinzips, vereinfachte Sequenzverteilung.",
      explainerVideo: "explainer-vrw-placeholder.mp4",
    },
    "4-straight": { title: "4 Pfeile · gerade", type: "arrows", dirset: 4, dual: false },
    "4-diag": { title: "4 Pfeile · diagonal", type: "arrows", dirset: "diag", dual: false },
    "8-solo": { title: "8 Pfeile · einfarbig", type: "arrows", dirset: 8, dual: false },
    "8-vrw": { title: "8 Pfeile · Rot/Grün (VRW)", type: "arrows", dirset: 8, dual: true },
    "stroop-classic": { title: "Stroop · klassisch", type: "stroop", bg: false },
    "stroop-bg": { title: "Stroop · mit Hintergrundfarbe", type: "stroop", bg: true },
    "cross-modal": {
      title: "Kreuzmodal · Sehen & Hören",
      type: "cross",
      rules:
        "Nur Bild oder nur Ton: reagiere wie gezeigt/gesagt. Bild + Ton gleichzeitig (unterschiedliche Richtung): zeigt der Pfeil VORNE oder RECHTS → der TON gilt; zeigt er HINTEN oder LINKS → das BILD gilt. Bild + Piepton: reagiere auf die Gegenrichtung des gezeigten Pfeils.",
    },
  };

  // ---- Programme: coach-authored multi-block sessions, looked up by a
  // short code (baked into this table - no account/login needed, works
  // for any client with the link). Real client programmes live in the
  // Cloudflare database (see lookupProgram below), never here - this table
  // only holds anonymous, public example programmes.
  const PROGRAMS = {
    // "featured: true" programmes are shown publicly on the home screen
    // (no code needed) as examples of what a coach-built programme looks like.
    "dig01": {
      name: "Dig01 · VT Tempo-Steigerung",
      featured: true,
      description: "2 Durchgänge VT: erst langsam mit langen Pausen, dann doppelt so schnell mit halber Einblendzeit.",
      pauseS: 15,
      blocks: [
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 2.5, intervalMin: 15, intervalMax: 25, sequence: "S01" },
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 1.25, intervalMin: 7.5, intervalMax: 12.5, sequence: "S01" },
      ],
    },
    "dig02": {
      name: "Dig02 · Gemischt (Fortgeschritten)",
      featured: true,
      description: "VT → VRW → Stroop → VRW, durchgehend kurze Einblendzeit und kurze Pausen für ein zügiges Tempo.",
      pauseS: 15,
      blocks: [
        { exercise: "vt-color", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5, sequence: "S01" },
        { exercise: "vrw-original", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5, sequence: "S01" },
        { exercise: "stroop-classic", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5, sequence: "S01" },
        { exercise: "vrw-original", palette: "ORL", duration: 60, stimulusS: 0.8, intervalMin: 3, intervalMax: 5, sequence: "S01" },
      ],
    },
  };

  // ---- Navigation ----
  const els = {
    home: document.getElementById("home"),
    ready: document.getElementById("ready"),
    player: document.getElementById("player"),
    playerBar: document.getElementById("playerBar"),
    donePanel: document.getElementById("donePanel"),
    readyTitle: document.getElementById("readyTitle"),
    readyIcon: document.getElementById("readyIcon"),
    rulesBox: document.getElementById("rulesBox"),
    filterMoreBtn: document.getElementById("filterMoreBtn"),
    filterExtra: document.getElementById("filterExtra"),
    startBtn: document.getElementById("startBtn"),
    backToHome: document.getElementById("backToHome"),
    backBtn: document.getElementById("backBtn"),
    fsBtn: document.getElementById("fsBtn"),
    fsHint: document.getElementById("fsHint"),
    fsHintOpenBtn: document.getElementById("fsHintOpenBtn"),
    fsHintClose: document.getElementById("fsHintClose"),
    featuredPrograms: document.getElementById("featuredPrograms"),
    featuredGrid: document.getElementById("featuredGrid"),
    featuredMoreBtn: document.getElementById("featuredMoreBtn"),
    liveNav: document.getElementById("liveNav"),
    livePrevBtn: document.getElementById("livePrevBtn"),
    liveRestartBtn: document.getElementById("liveRestartBtn"),
    liveEndBtn: document.getElementById("liveEndBtn"),
    liveNextBtn: document.getElementById("liveNextBtn"),
    liveChapterLabel: document.getElementById("liveChapterLabel"),
    timeEl: document.getElementById("timeEl"),
    again: document.getElementById("againBtn"),
    doneBack: document.getElementById("doneBackBtn"),
    durationSlider: document.getElementById("durationSlider"),
    durationValue: document.getElementById("durationValue"),
    stimulusSlider: document.getElementById("stimulusSlider"),
    stimulusValue: document.getElementById("stimulusValue"),
    intervalMinSlider: document.getElementById("intervalMinSlider"),
    intervalMaxSlider: document.getElementById("intervalMaxSlider"),
    intervalValue: document.getElementById("intervalValue"),
    paletteGroup: document.getElementById("paletteGroup"),
    paletteGrid: document.getElementById("paletteGrid"),
    sequenceGroup: document.getElementById("sequenceGroup"),
    programCodeInput: document.getElementById("programCodeInput"),
    programGoBtn: document.getElementById("programGoBtn"),
    programError: document.getElementById("programError"),
    programIntro: document.getElementById("programIntro"),
    programBackToHome: document.getElementById("programBackToHome"),
    programTitle: document.getElementById("programTitle"),
    chapterList: document.getElementById("chapterList"),
    programStartBtn: document.getElementById("programStartBtn"),
    pauseScreen: document.getElementById("pauseScreen"),
    pauseCountdown: document.getElementById("pauseCountdown"),
    pauseToggleBtn: document.getElementById("pauseToggleBtn"),
    pauseAbortBtn: document.getElementById("pauseAbortBtn"),
    prevChapterBtn: document.getElementById("prevChapterBtn"),
    restartChapterBtn: document.getElementById("restartChapterBtn"),
    nextChapterBtn: document.getElementById("nextChapterBtn"),
    chapterLabel: document.getElementById("chapterLabel"),
    nextPreview: document.getElementById("nextPreview"),
    programDonePanel: document.getElementById("programDonePanel"),
    programAgainBtn: document.getElementById("programAgainBtn"),
    programDoneBackBtn: document.getElementById("programDoneBackBtn"),
    introVideo: document.getElementById("introVideo"),
    explainerBtn: document.getElementById("explainerBtn"),
    videoModal: document.getElementById("videoModal"),
    videoModalPlayer: document.getElementById("videoModalPlayer"),
    videoModalClose: document.getElementById("videoModalClose"),
  };

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
  if (els.videoModalClose) els.videoModalClose.addEventListener("click", closeVideoModal);
  if (els.videoModal) {
    els.videoModal.addEventListener("click", (e) => { if (e.target === els.videoModal) closeVideoModal(); });
  }

  // Build the palette swatch grid once (20 buttons, three colour dots + code).
  if (els.paletteGrid) {
    PALETTE_ORDER.forEach((id) => {
      const p = PALETTES[id];
      const btn = document.createElement("button");
      btn.className = "palette-chip";
      btn.dataset.palette = id;
      btn.innerHTML =
        p.colors.map((c) => `<span class="dot" style="background:${c.hex}"></span>`).join("") +
        `<span class="code">${id}</span>`;
      btn.addEventListener("click", () => {
        state.palette = id;
        savePrefs();
        syncPaletteUI();
      });
      els.paletteGrid.appendChild(btn);
    });
  }
  function syncPaletteUI() {
    if (!els.paletteGrid) return;
    els.paletteGrid.querySelectorAll(".palette-chip").forEach((el) => {
      el.classList.toggle("active", el.dataset.palette === state.palette);
    });
  }

  document.querySelectorAll("[data-seq]").forEach((el) => {
    el.addEventListener("click", () => {
      state.sequence = el.dataset.seq;
      savePrefs();
      syncSequenceUI();
    });
  });
  function syncSequenceUI() {
    document.querySelectorAll("[data-seq]").forEach((el) => {
      el.classList.toggle("active", el.dataset.seq === state.sequence);
    });
  }

  const state = {
    exercise: null,
    duration: 30,
    stimulusS: 1.5,
    intervalMin: 2,
    intervalMax: 4,
    palette: "ORL",
    sequence: "frei",
  };

  function randInterval(rng) {
    const lo = Math.min(state.intervalMin, state.intervalMax);
    const hi = Math.max(state.intervalMin, state.intervalMax);
    return lo + rng() * (hi - lo);
  }

  function makeRng() {
    if (state.sequence === "frei") return Math.random;
    const key = [state.exercise, state.palette, state.sequence, state.duration, state.stimulusS, state.intervalMin, state.intervalMax].join("|");
    return mulberry32(hashSeed(key));
  }

  function loadPrefs() {
    try {
      const raw = localStorage.getItem("fwmc-webapp-v2");
      if (raw) Object.assign(state, JSON.parse(raw));
    } catch (e) {}
  }
  function savePrefs() {
    try { localStorage.setItem("fwmc-webapp-v2", JSON.stringify(state)); } catch (e) {}
  }

  document.querySelectorAll(".excard").forEach((card) => {
    card.addEventListener("click", () => openReady(card.dataset.exercise, card.querySelector(".icon-badge,.icon-tile").outerHTML));
  });

  function openReady(id, iconHtml) {
    state.exercise = id;
    savePrefs();
    els.readyTitle.textContent = EXERCISES[id].title;
    els.readyIcon.innerHTML = iconHtml;
    if (EXERCISES[id].rules) {
      els.rulesBox.textContent = EXERCISES[id].rules;
      els.rulesBox.hidden = false;
    } else {
      els.rulesBox.hidden = true;
    }
    if (EXERCISES[id].explainerVideo) {
      els.explainerBtn.hidden = false;
      els.explainerBtn.onclick = () => openVideoModal(EXERCISES[id].explainerVideo);
    } else {
      els.explainerBtn.hidden = true;
    }
    if (els.paletteGroup) els.paletteGroup.hidden = !EXERCISES[id].usesPalette;
    syncPaletteUI();
    syncSequenceUI();
    syncDurationUI();
    syncStimulusUI();
    syncIntervalUI();
    els.home.hidden = true;
    els.ready.hidden = false;
  }

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
      } else {
        if (activeFilters.typ.has(value)) {
          activeFilters.typ.delete(value);
          chip.classList.remove("active");
        } else {
          activeFilters.typ.add(value);
          chip.classList.add("active");
        }
      }
      applyFilters();
    });
  });
  if (els.filterMoreBtn) {
    els.filterMoreBtn.addEventListener("click", () => {
      const willShow = els.filterExtra.hidden;
      els.filterExtra.hidden = !willShow;
      els.filterMoreBtn.textContent = willShow ? "Weniger Filter" : "Mehr Filter";
    });
  }

  document.querySelectorAll("[data-dur]").forEach((el) => {
    el.addEventListener("click", () => {
      state.duration = Number(el.dataset.dur);
      savePrefs();
      syncDurationUI();
    });
  });
  function syncDurationUI() {
    document.querySelectorAll("[data-dur]").forEach((el) => {
      el.classList.toggle("active", el.dataset.dur === String(state.duration));
    });
    if (els.durationSlider) els.durationSlider.value = state.duration;
    if (els.durationValue) els.durationValue.textContent = state.duration + " s";
  }

  const INTERVAL_PRESETS = { kurz: [3, 5], mittel: [8, 12], lang: [15, 25] };
  document.querySelectorAll("[data-interval-preset]").forEach((el) => {
    el.addEventListener("click", () => {
      const [lo, hi] = INTERVAL_PRESETS[el.dataset.intervalPreset];
      state.intervalMin = lo;
      state.intervalMax = hi;
      savePrefs();
      syncIntervalUI();
    });
  });
  function syncIntervalUI() {
    document.querySelectorAll("[data-interval-preset]").forEach((el) => {
      const [lo, hi] = INTERVAL_PRESETS[el.dataset.intervalPreset];
      el.classList.toggle("active", lo === state.intervalMin && hi === state.intervalMax);
    });
    if (els.intervalMinSlider) els.intervalMinSlider.value = state.intervalMin;
    if (els.intervalMaxSlider) els.intervalMaxSlider.value = state.intervalMax;
    if (els.intervalValue) {
      els.intervalValue.textContent = `${state.intervalMin.toFixed(0)}–${state.intervalMax.toFixed(0)} s`;
    }
  }
  if (els.intervalMinSlider) {
    els.intervalMinSlider.addEventListener("input", () => {
      state.intervalMin = Math.min(Number(els.intervalMinSlider.value), state.intervalMax);
      savePrefs();
      syncIntervalUI();
    });
  }
  if (els.intervalMaxSlider) {
    els.intervalMaxSlider.addEventListener("input", () => {
      state.intervalMax = Math.max(Number(els.intervalMaxSlider.value), state.intervalMin);
      savePrefs();
      syncIntervalUI();
    });
  }

  const STIMULUS_PRESETS = { kurz: 0.8, mittel: 1.5, lang: 2.5 };
  document.querySelectorAll("[data-stimulus-preset]").forEach((el) => {
    el.addEventListener("click", () => {
      state.stimulusS = STIMULUS_PRESETS[el.dataset.stimulusPreset];
      savePrefs();
      syncStimulusUI();
    });
  });
  function syncStimulusUI() {
    document.querySelectorAll("[data-stimulus-preset]").forEach((el) => {
      el.classList.toggle("active", STIMULUS_PRESETS[el.dataset.stimulusPreset] === state.stimulusS);
    });
    if (els.stimulusSlider) els.stimulusSlider.value = state.stimulusS;
    if (els.stimulusValue) els.stimulusValue.textContent = state.stimulusS.toFixed(1) + " s";
  }
  if (els.stimulusSlider) {
    els.stimulusSlider.addEventListener("input", () => {
      state.stimulusS = Number(els.stimulusSlider.value);
      savePrefs();
      syncStimulusUI();
    });
  }
  if (els.durationSlider) {
    els.durationSlider.addEventListener("input", () => {
      state.duration = Number(els.durationSlider.value);
      savePrefs();
      syncDurationUI();
    });
  }

  els.backToHome.addEventListener("click", () => { els.ready.hidden = true; els.home.hidden = false; });

  // ---- Programme lookup + overview screen ----
  let program = null; // { def, chapterIndex, code }

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

  async function openProgramIntro(code) {
    if (els.programGoBtn) els.programGoBtn.disabled = true;
    const def = await lookupProgram(code);
    if (els.programGoBtn) els.programGoBtn.disabled = false;
    if (!def) {
      els.programError.hidden = false;
      return;
    }
    els.programError.hidden = true;
    els.programTitle.textContent = def.name;
    if (def.introVideo) {
      els.introVideo.src = def.introVideo;
      els.introVideo.hidden = false;
    } else {
      els.introVideo.hidden = true;
      els.introVideo.removeAttribute("src");
    }
    els.chapterList.innerHTML = "";
    def.blocks.forEach((block, i) => {
      const row = document.createElement("div");
      row.className = "chapter-row";
      const main = document.createElement("button");
      main.className = "chapter-main";
      main.innerHTML =
        `<span class="num">${i + 1}</span><span class="info"><strong>${EXERCISES[block.exercise].title}</strong><span>${block.duration}s${block.palette ? " · " + block.palette : ""}</span></span>`;
      main.addEventListener("click", () => {
        program = { def, chapterIndex: i, code };
        playChapter(i);
      });
      row.appendChild(main);
      const video = block.video || EXERCISES[block.exercise].explainerVideo;
      if (video) {
        const playBtn = document.createElement("button");
        playBtn.className = "play-explainer";
        playBtn.title = "Erklärvideo ansehen";
        playBtn.textContent = "▶";
        playBtn.addEventListener("click", (e) => { e.stopPropagation(); openVideoModal(video); });
        row.appendChild(playBtn);
      }
      els.chapterList.appendChild(row);
    });
    els.programStartBtn.onclick = () => {
      program = { def, chapterIndex: 0, code };
      playChapter(0);
    };
    els.home.hidden = true;
    els.programIntro.hidden = false;
  }

  if (els.programGoBtn) {
    els.programGoBtn.addEventListener("click", () => {
      const code = normCode(els.programCodeInput.value || "");
      if (code) openProgramIntro(code);
    });
  }
  if (els.programCodeInput) {
    els.programCodeInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") els.programGoBtn.click();
    });
  }
  if (els.programBackToHome) {
    els.programBackToHome.addEventListener("click", () => {
      els.programIntro.hidden = true;
      els.home.hidden = false;
    });
  }

  // A bare #token in the artifact's link (e.g. .../artifact/xyz#julia-1)
  // auto-opens that client's programme - no code typing needed.
  if (location.hash && location.hash.length > 1) {
    const tokenCode = normCode(decodeURIComponent(location.hash.slice(1)));
    if (tokenCode) {
      if (els.programCodeInput) els.programCodeInput.value = tokenCode;
      openProgramIntro(tokenCode);
    }
  }

  // ---- Featured programmes: public showcase examples, no code needed ----
  const FEATURED_VISIBLE = 3;
  function renderFeaturedPrograms() {
    if (!els.featuredGrid) return;
    const entries = Object.entries(PROGRAMS).filter(([, def]) => def.featured);
    if (entries.length === 0) { els.featuredPrograms.hidden = true; return; }
    els.featuredPrograms.hidden = false;
    els.featuredGrid.innerHTML = "";
    entries.forEach(([code, def], i) => {
      const card = document.createElement("button");
      card.className = "featured-card";
      if (i >= FEATURED_VISIBLE) card.classList.add("hidden-extra");
      card.innerHTML = `<span class="fc-title">${def.name}</span><span class="fc-desc">${def.description || ""}</span>`;
      card.addEventListener("click", () => openProgramIntro(code));
      els.featuredGrid.appendChild(card);
    });
    if (entries.length > FEATURED_VISIBLE) {
      els.featuredMoreBtn.hidden = false;
      els.featuredMoreBtn.dataset.expanded = "0";
      els.featuredMoreBtn.textContent = "Weitere anzeigen";
      els.featuredMoreBtn.onclick = () => {
        const expanded = els.featuredMoreBtn.dataset.expanded === "1";
        els.featuredGrid.querySelectorAll(".featured-card").forEach((c, idx) => {
          if (idx >= FEATURED_VISIBLE) c.classList.toggle("hidden-extra", expanded);
        });
        els.featuredMoreBtn.dataset.expanded = expanded ? "0" : "1";
        els.featuredMoreBtn.textContent = expanded ? "Weitere anzeigen" : "Weniger anzeigen";
      };
    } else {
      els.featuredMoreBtn.hidden = true;
    }
  }
  renderFeaturedPrograms();

  // ---- Session engine ----
  let raf = null;
  let wakeLock = null;
  let session = null;

  function buildArrowSchedule(cfg, rng) {
    const directions = cfg.dirset === "diag" ? DIR_DIAG : cfg.dirset === 8 ? DIR8 : DIR4;
    const schedule = [];
    let t = 0;
    for (let n = 3; n >= 1; n--) { schedule.push({ t0: t, t1: t + 1, kind: "count", payload: { n } }); t += 1; }
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
    let t = 0;
    for (let n = 3; n >= 1; n--) { schedule.push({ t0: t, t1: t + 1, kind: "count", payload: { n } }); t += 1; }
    const instruction = "Sag laut die SCHRIFTFARBE (nicht das Wort)";
    const show = state.stimulusS;
    while (t < state.duration) {
      const wIdx = Math.floor(rng() * STROOP_COLORS.length);
      const inkIdx = pick(STROOP_COLORS, [wIdx], rng);
      let bg = "#ffffff";
      if (cfg.bg) {
        const bgIdx = pick(STROOP_COLORS, [wIdx, inkIdx], rng);
        bg = STROOP_COLORS[bgIdx].hex;
      }
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
    let t = 0;
    for (let n = 3; n >= 1; n--) { schedule.push({ t0: t, t1: t + 1, kind: "count", payload: {} }); t += 1; }
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
    const palette = PALETTES[state.palette];
    const schedule = [];
    let t = 0;
    for (let n = 3; n >= 1; n--) { schedule.push({ t0: t, t1: t + 1, kind: "count", payload: { n } }); t += 1; }
    const show = state.stimulusS;
    while (t < state.duration) {
      const color = palette.colors[Math.floor(rng() * palette.colors.length)];
      const angle = rng() < 0.5 ? 90 : 270;
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "vt", payload: { angle, bg: color.hex } });
      schedule.push({ t0: t + show, t1: t + show + pause, kind: "blank", payload: {} });
      t += show + pause;
    }
    return { schedule, total: t };
  }

  function buildVRWRealSchedule(cfg, rng) {
    const palette = PALETTES[state.palette];
    const schedule = [];
    let t = 0;
    for (let n = 3; n >= 1; n--) { schedule.push({ t0: t, t1: t + 1, kind: "count", payload: { n } }); t += 1; }
    const show = state.stimulusS;
    while (t < state.duration) {
      const color = palette.colors[Math.floor(rng() * palette.colors.length)];
      const angle = rng() < 0.5 ? 90 : 270;
      const direct = rng() < 0.5;
      const pause = randInterval(rng);
      schedule.push({ t0: t, t1: t + show, kind: "vrw", payload: { angle, color: color.hex, direct } });
      schedule.push({ t0: t + show, t1: t + show + pause, kind: "blank", payload: {} });
      t += show + pause;
    }
    return { schedule, total: t };
  }

  function onEnterFrame(frame) {
    if (frame.kind !== "cross") return;
    const p = frame.payload;
    if (p.mode === "audio" || p.mode === "conflict") speakWord(p.word);
    else if (p.mode === "invert") playBeep();
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
    els.timeEl.textContent = Math.max(0, Math.ceil(session.total - elapsed)) + "s";
    raf = requestAnimationFrame(tick);
  }

  function applyBlockToState(block) {
    state.exercise = block.exercise;
    if (block.palette) state.palette = block.palette;
    state.sequence = block.sequence || "frei";
    state.duration = block.duration;
    state.stimulusS = block.stimulusS ?? 1.5;
    state.intervalMin = block.intervalMin ?? 2;
    state.intervalMax = block.intervalMax ?? 4;
  }

  function buildScheduleFor(cfg, rng) {
    return cfg.type === "stroop" ? buildStroopSchedule(cfg, rng) :
      cfg.type === "cross" ? buildCrossModalSchedule(cfg, rng) :
      cfg.type === "vt" ? buildVTSchedule(cfg, rng) :
      cfg.type === "vrw-real" ? buildVRWRealSchedule(cfg, rng) :
      buildArrowSchedule(cfg, rng);
  }

  async function playChapter(idx) {
    if (!program) return;
    if (idx < 0) idx = 0;
    if (idx >= program.def.blocks.length) { finishProgram(); return; }
    if (raf) cancelAnimationFrame(raf);
    if (window.speechSynthesis) speechSynthesis.cancel();
    program.chapterIndex = idx;
    const block = program.def.blocks[idx];
    applyBlockToState(block);
    els.home.hidden = true;
    els.programIntro.hidden = true;
    els.ready.hidden = true;
    els.player.hidden = false;
    els.donePanel.hidden = true;
    els.programDonePanel.hidden = true;
    els.pauseScreen.hidden = true;
    els.playerBar.hidden = false;
    els.liveNav.hidden = false;
    fitCanvas();
    ensureAudioCtx();
    const cfg = EXERCISES[state.exercise];
    const rng = makeRng();
    const built = buildScheduleFor(cfg, rng);
    session = { ...built, startTime: performance.now(), lastIndex: -1 };
    const label = `Kapitel ${idx + 1}/${program.def.blocks.length}`;
    els.chapterLabel.textContent = label;
    els.liveChapterLabel.textContent = label;
    try { if ("wakeLock" in navigator) wakeLock = await navigator.wakeLock.request("screen"); } catch (e) {}
    raf = requestAnimationFrame(tick);
  }

  if (els.liveRestartBtn) els.liveRestartBtn.addEventListener("click", () => { if (program) playChapter(program.chapterIndex); });
  if (els.liveEndBtn) els.liveEndBtn.addEventListener("click", () => finishSession());
  if (els.livePrevBtn) els.livePrevBtn.addEventListener("click", () => { if (program) playChapter(program.chapterIndex - 1); });
  if (els.liveNextBtn) els.liveNextBtn.addEventListener("click", () => { if (program) playChapter(program.chapterIndex + 1); });

  let pauseTimer = null;
  let pauseRemaining = 0;
  let pausePaused = false;

  function startPause() {
    const def = program.def;
    const block = def.blocks[program.chapterIndex];
    pauseRemaining = block.pauseS ?? def.pauseS ?? 15;
    pausePaused = false;
    els.pauseToggleBtn.textContent = "Pause verlängern";
    els.pauseScreen.hidden = false;
    els.playerBar.hidden = true;
    els.liveNav.hidden = true;
    const nextBlock = def.blocks[program.chapterIndex + 1];
    els.nextPreview.textContent = nextBlock ? "Nächstes: " + EXERCISES[nextBlock.exercise].title : "Letztes Kapitel";
    els.chapterLabel.textContent = `Kapitel ${program.chapterIndex + 1}/${def.blocks.length}`;
    tickPause();
  }
  function tickPause() {
    if (pauseTimer) clearTimeout(pauseTimer);
    els.pauseCountdown.textContent = Math.max(0, Math.ceil(pauseRemaining)) + "s";
    if (pausePaused) return;
    if (pauseRemaining <= 0) {
      els.pauseScreen.hidden = true;
      playChapter(program.chapterIndex + 1);
      return;
    }
    pauseTimer = setTimeout(() => { pauseRemaining -= 1; tickPause(); }, 1000);
  }
  if (els.pauseToggleBtn) {
    els.pauseToggleBtn.addEventListener("click", () => {
      pausePaused = !pausePaused;
      els.pauseToggleBtn.textContent = pausePaused ? "Fortsetzen" : "Pause verlängern";
      if (!pausePaused) tickPause();
    });
  }
  if (els.prevChapterBtn) els.prevChapterBtn.addEventListener("click", () => { if (pauseTimer) clearTimeout(pauseTimer); playChapter(program.chapterIndex - 1); });
  if (els.restartChapterBtn) els.restartChapterBtn.addEventListener("click", () => { if (pauseTimer) clearTimeout(pauseTimer); playChapter(program.chapterIndex); });
  if (els.nextChapterBtn) els.nextChapterBtn.addEventListener("click", () => { if (pauseTimer) clearTimeout(pauseTimer); playChapter(program.chapterIndex + 1); });
  if (els.pauseAbortBtn) els.pauseAbortBtn.addEventListener("click", () => stopToHome());

  function finishProgram() {
    els.pauseScreen.hidden = true;
    els.programDonePanel.hidden = false;
    els.playerBar.hidden = true;
  }
  if (els.programAgainBtn) {
    els.programAgainBtn.addEventListener("click", () => { if (program) playChapter(0); });
  }
  if (els.programDoneBackBtn) {
    els.programDoneBackBtn.addEventListener("click", () => stopToHome());
  }

  async function startSession() {
    const cfg = EXERCISES[state.exercise];
    els.ready.hidden = true;
    els.player.hidden = false;
    els.donePanel.hidden = true;
    els.playerBar.hidden = false;
    els.liveNav.hidden = true;
    fitCanvas();
    ensureAudioCtx();
    const rng = makeRng();
    const built = buildScheduleFor(cfg, rng);
    session = { ...built, startTime: performance.now(), lastIndex: -1 };
    try { if ("wakeLock" in navigator) wakeLock = await navigator.wakeLock.request("screen"); } catch (e) {}
    raf = requestAnimationFrame(tick);
  }

  function finishSession() {
    if (raf) cancelAnimationFrame(raf);
    session = null;
    if (wakeLock) { wakeLock.release().catch(() => {}); wakeLock = null; }
    els.liveNav.hidden = true;
    if (program) { startPause(); return; }
    els.donePanel.hidden = false;
    els.playerBar.hidden = true;
  }

  function stopToHome() {
    if (raf) cancelAnimationFrame(raf);
    session = null;
    if (pauseTimer) clearTimeout(pauseTimer);
    program = null;
    if (wakeLock) { wakeLock.release().catch(() => {}); wakeLock = null; }
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
    els.fsHint.hidden = true;
    els.liveNav.hidden = true;
    if (window.speechSynthesis) speechSynthesis.cancel();
    els.player.hidden = true;
    els.pauseScreen.hidden = true;
    els.programDonePanel.hidden = true;
    els.programIntro.hidden = true;
    els.home.hidden = false;
    els.ready.hidden = true;
  }

  els.startBtn.addEventListener("click", startSession);
  els.backBtn.addEventListener("click", stopToHome);
  els.doneBack.addEventListener("click", stopToHome);
  els.again.addEventListener("click", startSession);
  function updateFsBtnLabel() {
    els.fsBtn.textContent = document.fullscreenElement ? "Vollbild verlassen" : "Vollbild";
  }
  document.addEventListener("fullscreenchange", updateFsBtnLabel);
  els.fsBtn.addEventListener("click", () => {
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
      return;
    }
    if (document.fullscreenEnabled && els.player.requestFullscreen) {
      els.player.requestFullscreen().catch(() => { els.fsHint.hidden = false; });
    } else {
      els.fsHint.hidden = false;
    }
  });
  if (els.fsHintOpenBtn) {
    els.fsHintOpenBtn.addEventListener("click", () => {
      window.open(location.href, "_blank");
    });
  }
  if (els.fsHintClose) {
    els.fsHintClose.addEventListener("click", () => { els.fsHint.hidden = true; });
  }
  window.addEventListener("resize", () => { if (!els.player.hidden) fitCanvas(); });
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && session && wakeLock === null && "wakeLock" in navigator) {
      navigator.wakeLock.request("screen").then((w) => (wakeLock = w)).catch(() => {});
    }
  });

  loadPrefs();

  // PWA: only meaningful on real hosting - service workers do not run
  // inside the Artifacts preview sandbox, so registration there is a
  // silent, expected no-op.
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  }
})();
