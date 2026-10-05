// Fabian-Blick audit of the current top layer (see fabian_blick_test.py).
// Returns {findings: [{cat, msg, el}], info: {styles: [[kind, signature]]}}.
(opts) => {
  const findings = [];
  const add = (cat, msg, el) => findings.push({cat, msg, el: el ? desc(el) : ''});
  const cs = el => getComputedStyle(el);
  const vis = el => {
    if (!el || el.closest('[hidden]')) return false;
    const r = el.getBoundingClientRect(), s = cs(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05;
  };
  function desc(el) {
    const id = el.id ? '#' + el.id : '';
    const cls = (typeof el.className === 'string' && el.className.trim()) ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
    const t = (el.textContent || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 28);
    return el.tagName.toLowerCase() + id + cls + (t ? ' "' + t + '"' : '');
  }
  const inFixed = el => { for (let e = el; e && e !== document.body; e = e.parentElement) { const p = cs(e).position; if (p === 'fixed' || p === 'sticky') return true; } return false; };

  const sheets = [...document.querySelectorAll('.sheet')].filter(vis);
  const players = [...document.querySelectorAll('.player')].filter(vis);
  const screen = [...document.querySelectorAll('.screen')].find(vis);
  const root = sheets[sheets.length - 1] || players[0] || screen || document.body;
  const isPlayer = !sheets.length && !!players.length;
  const isSheet = !!sheets.length;

  // ---------- umbruch: split words, text out of its box, sideways scroll ----------
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let n;
  const textEls = new Set();
  while ((n = walker.nextNode())) {
    const el = n.parentElement;
    if (!el || !n.textContent.trim() || !vis(el)) continue;
    if (el.closest('details:not([open]) > :not(summary), input, textarea, select, svg, canvas, script, style')) continue;
    textEls.add(el);
    const re = /[^\s\-–­/]+[\-–­/]?/g;
    let m;
    while ((m = re.exec(n.textContent))) {
      const tok = m[0].replace(/[\-–­/]$/, '');
      if (tok.length < 2) continue;
      const lineOf = i => { const rg = document.createRange(); rg.setStart(n, i); rg.setEnd(n, i + 1);
        const rs = [...rg.getClientRects()]; return rs.length ? Math.round(rs[rs.length - 1].top) : null; };
      const a = lineOf(m.index), z = lineOf(m.index + tok.length - 1);
      if (a !== null && z !== null && Math.abs(z - a) > 4) add('umbruch', 'Wort mitten getrennt: "' + tok + '"', el);
    }
  }
  textEls.forEach(el => {
    const s = cs(el);
    if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0 && (s.overflowX === 'hidden' || s.textOverflow === 'ellipsis'))
      add('umbruch', 'Text abgeschnitten', el);
  });
  root.querySelectorAll('button, .section-tab, .sub-tab, .choice, .chip').forEach(b => {
    if (vis(b) && b.scrollWidth > b.clientWidth + 2) add('umbruch', 'Text ragt aus Knopf', b);
  });
  if (document.documentElement.scrollWidth > window.innerWidth + 1)
    add('umbruch', 'Seite scrollt seitlich (' + document.documentElement.scrollWidth + ' > ' + window.innerWidth + ' px)');
  // Text wider than its card/group (visually sticks out, even without scroll).
  textEls.forEach(el => {
    const box = el.closest('.card, .group, .code-card, .tile, .sheet-inner, .hero, section');
    if (!box || box === el) return;
    const r = el.getBoundingClientRect(), b = box.getBoundingClientRect();
    if (r.right > b.right + 2 || r.left < b.left - 2) add('umbruch', 'Text ragt aus seinem Kasten', el);
  });

  // ---------- ueberlappt: atoms on top of each other ----------
  const isInteractive = el => el.matches('button, a[href], select, input:not([type=hidden]), textarea, [role=button], summary, label.choice');
  const atoms = [];
  const seen = new Set();
  const consider = el => {
    if (!vis(el)) return;
    const owner = el.closest('button, a[href], [role=button], label, summary') || el;
    if (seen.has(owner) || !root.contains(owner)) return;
    seen.add(owner); atoms.push(owner);
  };
  textEls.forEach(consider);
  root.querySelectorAll('button, a[href], select, input:not([type=hidden]), textarea, canvas, img').forEach(consider);
  const fixedAtoms = atoms.filter(inFixed), flowAtoms = atoms.filter(a => !inFixed(a));
  const check = (list, fixedMode) => {
    for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
      const a = list[i], b = list[j];
      if (a.contains(b) || b.contains(a)) continue;
      // canvas/img under its own overlay label is the design (stage text) unless one is a control
      if ((a.tagName === 'CANVAS' || b.tagName === 'CANVAS') && !(isInteractive(a) || isInteractive(b) || /hint/.test(a.className + b.className))) continue;
      if (a.tagName === 'IMG' && b.tagName === 'IMG') continue;
      if (inFixed(a) !== inFixed(b) && !fixedMode) continue;
      const r = a.getBoundingClientRect(), q = b.getBoundingClientRect();
      const w = Math.min(r.right, q.right) - Math.max(r.left, q.left), h = Math.min(r.bottom, q.bottom) - Math.max(r.top, q.top);
      if (w <= 3 || h <= 3) continue;
      const small = Math.min(r.width * r.height, q.width * q.height);
      if (w * h < 0.12 * small) continue;
      add('ueberlappt', 'liegt über ' + desc(b), a);
    }
  };
  check(flowAtoms.slice(0, 400), false);
  check(fixedAtoms.slice(0, 120), true);
  // Player: the stage hint and stage content must stay clear of the player bar.
  if (isPlayer) {
    const bar = root.querySelector('.player-bar');
    if (bar && vis(bar)) {
      const br = bar.getBoundingClientRect();
      root.querySelectorAll('[class*=hint], canvas, [class*=answer], [class*=response], [class*=keypad]').forEach(el => {
        if (!vis(el) || bar.contains(el) || el.contains(bar)) return;
        const r = el.getBoundingClientRect();
        if (el.tagName === 'CANVAS') return; // canvas may span the stage; engines keep content below the bar
        if (r.top < br.bottom - 2 && r.bottom > br.top + 2 && r.left < br.right && r.right > br.left)
          add('player', 'liegt unter der Spielerleiste', el);
      });
    }
  }
  // Content must be able to scroll out from under the bottom bar.
  const nav = document.getElementById('bottomNav');
  if (!isPlayer && !isSheet && nav && vis(nav)) {
    const navTop = nav.getBoundingClientRect().top;
    const maxBottom = Math.max(0, ...flowAtoms.filter(a => !nav.contains(a)).map(a => a.getBoundingClientRect().bottom + window.scrollY));
    const reach = document.documentElement.scrollHeight - (window.innerHeight - navTop);
    if (maxBottom > reach + 2) add('ueberlappt', 'Unterster Inhalt bleibt unter der unteren Leiste (' + Math.round(maxBottom - reach) + ' px)');
  }

  // ---------- taste: tap targets >= 44 px ----------
  root.querySelectorAll('button, a[href], select, [role=button], summary, input[type=checkbox], input[type=radio], input[type=text], input[type=number], input[type=date], input[type=time], input:not([type])').forEach(el => {
    if (!vis(el)) return;
    let t = el;
    if (el.matches('input[type=checkbox], input[type=radio]')) t = el.closest('label') || el;
    const r = t.getBoundingClientRect();
    // Links inside running text are measured by line height; skip them.
    if (t.tagName === 'A' && t.closest('p, li') && cs(t).display === 'inline') return;
    const min = Math.min(r.width, r.height);
    if (min < 43.5) add('taste', 'Tipp-Fläche nur ' + Math.round(r.width) + '×' + Math.round(r.height) + ' px', t);
  });

  // ---------- kopf: one common top bar, bottom bar on screens ----------
  const styles = [];
  const sig = (el, props) => { const s = cs(el); return props.map(p => s.getPropertyValue(p).replace(/\s+/g, ' ')).join(' | '); };
  if (!isPlayer && !isSheet && screen) {
    const bar = screen.querySelector(':scope > .brandbar, :scope .app-bar-inner');
    if (!bar || !vis(bar)) add('kopf', 'Keine obere Leiste');
    else {
      const r = bar.getBoundingClientRect();
      const logo = bar.querySelector('img');
      const title = (bar.textContent || '').replace(/\s+/g, ' ');
      const gear = bar.querySelector('.master-settings-btn');
      if (Math.abs(r.top) > 1) add('kopf', 'Obere Leiste nicht ganz oben (top ' + Math.round(r.top) + ')');
      if (!logo || !vis(logo)) add('kopf', 'Logo fehlt in der oberen Leiste');
      if (!/FWMC/.test(title) || !/Online-Training/.test(title)) add('kopf', 'Titel "FWMC / Online-Training" fehlt');
      if (!gear || !vis(gear)) add('kopf', 'Zahnrad fehlt in der oberen Leiste');
      const back = bar.querySelector('.bar-back-btn');
      const top = ['todayHome', 'trainingHub', 'moreScreen', 'progressScreen'].includes(screen.id);
      if (!top && !(back && vis(back))) add('kopf', 'Unterseite ohne Zurück-Knopf ‹');
      styles.push(['obere Leiste', Math.round(r.height) + 'px | ' + sig(bar, ['background-color', 'border-bottom-color', 'border-bottom-width'])]);
      if (logo && vis(logo)) styles.push(['Logo oben', Math.round(logo.getBoundingClientRect().height) + 'px']);
      const t = bar.querySelector('.brand-sub');
      if (t && vis(t)) styles.push(['Titel oben', sig(t, ['font-family', 'font-size', 'font-weight', 'color'])]);
    }
    if (nav && !vis(nav)) add('kopf', 'Untere Leiste fehlt');
  }

  // ---------- farbe + kontrast ----------
  const parse = c => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
    return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
  const rootStyle = cs(document.documentElement);
  const tokenNames = [];
  for (const sh of document.styleSheets) { try { for (const rule of sh.cssRules) { if (rule.selectorText === ':root' || (rule.cssRules && true)) {
    const txt = rule.cssText; (txt.match(/--[a-z0-9-]+(?=\s*:)/g) || []).forEach(x => tokenNames.push(x)); } } } catch (e) {} }
  const probe = document.createElement('i'); document.body.appendChild(probe);
  const palette = new Set(['#ffffff', '#000000']);
  [...new Set(tokenNames)].forEach(t => { const v = rootStyle.getPropertyValue(t).trim(); if (!v || /px|var\(|,.*,.*,.*,/.test(v) && !/^rgba?\(/.test(v)) return;
    probe.style.color = ''; probe.style.color = v; if (!probe.style.color) return; const c = parse(cs(probe).color); if (c) palette.add(hex(c)); });
  probe.remove();
  const near = h => { const c = parse('rgb(' + parseInt(h.slice(1, 3), 16) + ',' + parseInt(h.slice(3, 5), 16) + ',' + parseInt(h.slice(5, 7), 16) + ')');
    for (const p of palette) { const q = {r: parseInt(p.slice(1, 3), 16), g: parseInt(p.slice(3, 5), 16), b: parseInt(p.slice(5, 7), 16)};
      if (Math.abs(q.r - c.r) + Math.abs(q.g - c.g) + Math.abs(q.b - c.b) <= 6) return true; } return false; };
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const blend = (top, bot) => ({r: top.r * top.a + bot.r * (1 - top.a), g: top.g * top.a + bot.g * (1 - top.a), b: top.b * top.a + bot.b * (1 - top.a), a: 1});
  const bgOf = el => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const s = cs(e);
      if (s.backgroundImage && s.backgroundImage !== 'none') return null; // gradient/image: cannot judge
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a >= 0.99) break; }
    }
    let base = {r: 255, g: 255, b: 255, a: 1};
    for (let i = layers.length - 1; i >= 0; i--) base = blend(layers[i], base);
    return base;
  };
  const skipColour = el => el.closest('canvas, svg, [data-sig], .look-host, [class*=swatch], [class*=color-pick], [class*=colour], [class*=signal], [style*="background"], .player .stage, .sig, [class*=stroop]');
  const offPalette = {};
  if (!isPlayer) {
    root.querySelectorAll('*').forEach(el => {
      if (!vis(el) || skipColour(el)) return;
      const s = cs(el);
      const check = (prop, val) => { const c = parse(val); if (!c || c.a < 0.05) return; const h = hex(c); if (!near(h)) (offPalette[h + ' (' + prop + ')'] = offPalette[h + ' (' + prop + ')'] || el); };
      check('Hintergrund', s.backgroundColor);
      if (textEls.has(el)) check('Schrift', s.color);
      if (parseFloat(s.borderTopWidth) > 0) check('Rahmen', s.borderTopColor);
    });
  }
  Object.entries(offPalette).forEach(([k, el]) => add('farbe', 'Farbe außerhalb des Designs ' + k, el));
  textEls.forEach(el => {
    if (skipColour(el) || el.closest('[disabled], .is-disabled') || el.matches(':disabled')) return;
    const s = cs(el), fg = parse(s.color), bg = bgOf(el);
    if (!fg || !bg) return;
    const f = blend(fg, bg);
    const L1 = lum(f), L2 = lum(bg), ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const size = parseFloat(s.fontSize), bold = +s.fontWeight >= 600;
    const need = (size >= 24 || (bold && size >= 18.6)) ? 3 : 4.5;
    if (ratio < need) add('kontrast', 'Kontrast ' + ratio.toFixed(1) + ':1 (nötig ' + need + ')', el);
  });

  // ---------- name: old / forbidden names ----------
  const text = (root.innerText || '');
  const bad = [[/\bRemember\b/, 'Remember (heißt Positionen merken)'], [/\bCoach(es)?\b/, 'Coach (heißt dein Trainer)'],
    [/Komplett-Programm|Kombi-Baukasten/, 'alter Kombi-Name'], [/Zusatzimpuls|Zusatzübung/, 'Zusatzimpuls/Zusatzübung (heißt Zusatzaufgabe)'],
    [/Master-?Einstellungen/, 'Master-Einstellungen (heißt Grundeinstellungen)'], [/\bBeta\b/, 'Beta-Hinweis'],
    [/undefined|NaN|\[object Object\]/, 'Programmier-Rest (undefined/NaN)']];
  bad.forEach(([re, label]) => { const m = text.match(re); if (m) add('name', 'Alter/falscher Begriff: ' + label + ' ("' + m[0] + '")'); });
  root.querySelectorAll('button').forEach(b => {
    if (!vis(b)) return; const t = b.textContent.trim();
    if (/^(Start|Starten|Los|Los geht's|Übung starten|Jetzt starten)$/i.test(t)) add('name', 'Start-Knopf heißt nicht "Training starten"', b);
  });

  // ---------- player conventions ----------
  if (isPlayer && opts.isStart) {
    const p = players[0];
    const back = [...p.querySelectorAll('button[id$="BackBtn"]')].find(vis);
    const pause = [...p.querySelectorAll('button[id$="PauseBtn"]')].find(vis);
    if (!back) add('player', 'Kein sichtbarer Beenden-Knopf (…BackBtn)');
    else if (!/Beenden/.test(back.textContent)) add('player', 'Beenden-Knopf heißt "' + back.textContent.trim() + '"', back);
    if (pause && !/Pause|Weiter/.test(pause.textContent)) add('player', 'Pause-Knopf heißt "' + pause.textContent.trim() + '"', pause);
  }

  // ---------- stil: signatures of shared kinds (compared across screens in Python) ----------
  const kinds = [['Seitentitel', 'h1.page-title'], ['Unterzeile', '.page-sub'], ['Gruppen-Überschrift', '.group-label'],
    ['Abschnitt-Überschrift', '.section-head h2'], ['Code-Karte', '.code-card'], ['Kombi-Eintrag', '.combo-entry-link'],
    ['Zurück-Knopf', '.bar-back-btn'], ['Zahnrad', '.master-settings-btn'], ['Bereichs-Kachel', '.nat-tile, .tile']];
  kinds.forEach(([k, sel]) => { const el = [...root.querySelectorAll(sel)].find(vis); if (el) styles.push([k, sig(el, ['font-family', 'font-size', 'font-weight', 'color', 'background-color', 'border-radius'])]); });
  const startBtn = [...root.querySelectorAll('button')].find(b => vis(b) && b.textContent.trim() === 'Training starten');
  if (startBtn) styles.push(['Knopf "Training starten"', Math.round(startBtn.getBoundingClientRect().height) + 'px | ' + sig(startBtn, ['font-family', 'font-size', 'font-weight', 'color', 'background-color', 'border-radius'])]);

  // dedupe
  const uniq = {}; findings.forEach(f => { uniq[f.cat + f.msg + f.el] = f; });
  return {findings: Object.values(uniq), info: {styles, layer: isPlayer ? 'player' : isSheet ? 'sheet' : 'screen'}};
}
