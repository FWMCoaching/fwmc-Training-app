// Fabian-Blick audit of the current top layer (see fabian_blick_test.py).
// Returns {findings: [{cat, msg, el}], info: {styles: [[kind, signature]]}}.
(opts) => {
  const findings = [];
  const add = (cat, msg, el) => findings.push({cat, msg, el: el ? desc(el) : ''});
  const cs = el => getComputedStyle(el);
  const vis = el => {
    if (!el || el.closest('[hidden]')) return false;
    const det = el.closest('details:not([open])');
    if (det && !el.closest('summary')) return false;
    if (el.checkVisibility && !el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true})) return false;
    const r = el.getBoundingClientRect(), s = cs(el);
    if (!(r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05)) return false;
    // Clipped away by a collapsed ancestor (e.g. closed "Feineinstellungen" with max-height 0)?
    for (let e = el.parentElement; e && e !== document.body; e = e.parentElement) {
      const es = cs(e);
      if (+es.opacity <= 0.05) return false;
      if (es.overflowX !== 'visible' || es.overflowY !== 'visible') {
        const q = e.getBoundingClientRect();
        if (q.height < 1 || q.width < 1) return false;
        if (es.overflowY !== 'visible' && es.overflowY !== 'auto' && es.overflowY !== 'scroll' && (r.top >= q.bottom - 1 || r.bottom <= q.top + 1)) return false;
        if (es.overflowX === 'hidden' || es.overflowX === 'clip') { if (r.left >= q.right - 1 || r.right <= q.left + 1) return false; }
      }
    }
    return true;
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
  // Nested scroll boxes inside the layer (e.g. "Mein Plan" week list with
  // max-height + overflow-y:auto, the Heute "Zum Ausprobieren" row with
  // overflow-x:auto): what is scrolled out of such a box is not on screen.
  // The layer itself and .sheet-inner are not counted - the walk audits their
  // whole content on purpose.
  const nestedScrollers = el => {
    const out = [];
    for (let e = el.parentElement; e && e !== root && root.contains(e); e = e.parentElement) {
      if (e.matches('.sheet-inner, .screen')) continue;
      const es = cs(e);
      const sx = /auto|scroll/.test(es.overflowX) && e.scrollWidth > e.clientWidth + 1;
      const sy = /auto|scroll/.test(es.overflowY) && e.scrollHeight > e.clientHeight + 1;
      if (sx || sy) out.push(e);
    }
    return out;
  };
  // The on-screen part of el: its rect cut to every nested scroll box.
  const clipRect = el => {
    const r = el.getBoundingClientRect(); let L = r.left, T = r.top, R = r.right, B = r.bottom;
    nestedScrollers(el).forEach(e => { const q = e.getBoundingClientRect();
      L = Math.max(L, q.left); T = Math.max(T, q.top); R = Math.min(R, q.right); B = Math.min(B, q.bottom); });
    return {left: L, top: T, right: R, bottom: B, width: Math.max(0, R - L), height: Math.max(0, B - T)};
  };
  const inScrollView = el => {
    const r = el.getBoundingClientRect();
    return nestedScrollers(el).every(e => { const q = e.getBoundingClientRect();
      return r.right > q.left + 1 && r.left < q.right - 1 && r.bottom > q.top + 1 && r.top < q.bottom - 1; });
  };

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
  // Tabs never wrap (CLAUDE.md 2026-10-05; Prüfer 07.10. Nr. 3: "Woche / A"
  // in the plan's week tabs): any tab-like button whose label runs onto a
  // second line, in every tab row the app has or gets.
  root.querySelectorAll('[role=tab], button[class*="tab"]').forEach(b => {
    if (!vis(b) || b.closest('#bottomNav')) return;
    const tops = new Set();
    const walker = document.createTreeWalker(b, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!n.textContent.trim() || !vis(n.parentElement)) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      [...rg.getClientRects()].forEach(r => { if (r.width > 1) tops.add(Math.round(r.top / 4)); });
    }
    if (tops.size > 1) add('umbruch', 'Reiter bricht in zwei Zeilen um', b);
  });
  if (document.documentElement.scrollWidth > window.innerWidth + 1)
    add('umbruch', 'Seite scrollt seitlich (' + document.documentElement.scrollWidth + ' > ' + window.innerWidth + ' px)');
  // Text wider than its card/group (visually sticks out, even without scroll).
  textEls.forEach(el => {
    const box = el.closest('.card, .group, .code-card, .tile, .sheet-inner, .hero, section');
    if (!box || box === el) return;
    // clipped by a horizontal scroll box inside the card: does not stick out
    if (nestedScrollers(el).some(e => box.contains(e) && /auto|scroll/.test(cs(e).overflowX))) return;
    const r = el.getBoundingClientRect(), b = box.getBoundingClientRect();
    if (r.right > b.right + 2 || r.left < b.left - 2) add('umbruch', 'Text ragt aus seinem Kasten', el);
  });

  // ---------- ueberlappt: atoms on top of each other ----------
  const isInteractive = el => el.matches('button, a[href], select, input:not([type=hidden]), textarea, [role=button], summary, label.choice');
  const atoms = [];
  const seen = new Set();
  const consider = el => {
    if (!vis(el) || !inScrollView(el)) return;
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
      // the player bar floats over the stage canvas by design (engines draw below it)
      if ((a.tagName === 'CANVAS' && b.closest('.player-bar')) || (b.tagName === 'CANVAS' && a.closest('.player-bar'))) continue;
      if (a.tagName === 'IMG' && b.tagName === 'IMG') continue;
      if (inFixed(a) !== inFixed(b) && !fixedMode) continue;
      // inline pieces of one wrapped paragraph share line boxes: not an overlap
      const inl = e => cs(e).display.startsWith('inline') && !isInteractive(e);
      if (inl(a) && inl(b) && a.closest('p, li, div, label') === b.closest('p, li, div, label')) continue;
      const r = clipRect(a), q = clipRect(b);
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
    let low = null, maxBottom = 0;
    flowAtoms.filter(a => !nav.contains(a)).forEach(a => { const b = a.getBoundingClientRect().bottom + window.scrollY; if (b > maxBottom) { maxBottom = b; low = a; } });
    const reach = document.documentElement.scrollHeight - (window.innerHeight - navTop);
    if (maxBottom > reach + 2) add('ueberlappt', 'Unterster Inhalt bleibt unter der unteren Leiste (' + Math.round(maxBottom - reach) + ' px)', low);
  }

  // ---------- taste: tap targets >= 44 px ----------
  root.querySelectorAll('button, a[href], select, [role=button], summary, input[type=checkbox], input[type=radio], input[type=text], input[type=number], input[type=date], input[type=time], input:not([type])').forEach(el => {
    if (!vis(el)) return;
    let t = el;
    if (el.matches('input[type=checkbox], input[type=radio]')) t = el.closest('label') || el;
    let r = t.getBoundingClientRect();
    // mid pop-in animation (scale .5 -> 1, e.g. Reaktionsfeld-Licht): measure the real size
    if (t.getAnimations && t.getAnimations().some(a => a.playState === 'running') && t.offsetHeight)
      r = {width: t.offsetWidth, height: t.offsetHeight};
    // Links inside running text are measured by line height; skip them.
    if (t.tagName === 'A' && t.closest('p, li') && cs(t).display === 'inline') return;
    if (r.height < 43.5) add('taste', 'nur ' + Math.round(r.height) + ' px hoch (mind. 44)', t);
    else if (r.width < 43.5) add('taste', 'nur ' + Math.round(r.width) + ' px breit (mind. 44)', t);
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
      if (!vis(el) || skipColour(el) || el.matches('input[type=range]')) return;
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
    const back = [...p.querySelectorAll('button[id$="BackBtn"], button#backBtn')].find(vis);
    const pause = [...p.querySelectorAll('button[id$="PauseBtn"]')].find(vis);
    if (!back) add('player', 'Kein sichtbarer Beenden-Knopf (…BackBtn)');
    else if (!/Beenden/.test(back.textContent)) add('player', 'Beenden-Knopf heißt "' + back.textContent.trim() + '"', back);
    if (pause && !/Pause|Weiter/.test(pause.textContent)) add('player', 'Pause-Knopf heißt "' + pause.textContent.trim() + '"', pause);
  }

  // ---------- Benchmark (app/benchmark-gute-app.md) ----------
  // 11 druck: every control shows a pressed state on touch (a CSS :active rule matches it)
  if (!window.__fbActiveSel) {
    const sels = [];
    for (const sh of document.styleSheets) { try { const walk = rules => { for (const r of rules) {
      if (r.selectorText && r.selectorText.includes(':active')) r.selectorText.split(',').forEach(x => { if (x.includes(':active')) sels.push(x.replace(/:active/g, '').trim() || '*'); });
      if (r.cssRules) walk(r.cssRules); } }; walk(sh.cssRules); } catch (e) {} }
    window.__fbActiveSel = sels;
  }
  const pressed = el => window.__fbActiveSel.some(x => { try { return el.matches(x) || !!el.closest(x); } catch (e) { return false; } });
  root.querySelectorAll('button, a[href], [role=button], summary').forEach(el => {
    if (!vis(el) || el.disabled) return;
    if (!pressed(el)) add('druck', 'Kein Druckzustand beim Antippen (keine :active-Regel)', el);
  });
  // 24 dunkel: no light patches in dark mode (also fixed bars outside the layer)
  if (matchMedia('(prefers-color-scheme: dark)').matches) {
    const pool = new Set([...root.querySelectorAll('*'), ...[...document.body.querySelectorAll('*')].filter(e => cs(e).position === 'fixed' && !e.closest('.sheet, .screen[hidden], .player[hidden]'))]);
    pool.forEach(el => {
      if (!vis(el) || el.matches('img, canvas, svg, input[type=range]') || el.closest('canvas, svg, [data-sig], .look-host, [class*=swatch], .app-splash') || el.getAttribute('style')?.includes('background')) return;
      const c = parse(cs(el).backgroundColor); if (!c || c.a < 0.9) return;
      const r = el.getBoundingClientRect(); if (r.width * r.height < 2500) return;
      if (lum(c) > 0.6) add('dunkel', 'Heller Fleck im Dunkelmodus (' + hex(c) + ', ' + Math.round(r.width) + '×' + Math.round(r.height) + ' px)', el);
    });
  }
  // 17 hauptaktion: at most one primary button per screen
  if (!isPlayer && !isSheet) {
    const prim = [...root.querySelectorAll('.start-btn')].filter(vis);
    if (prim.length > 1) add('hauptaktion', prim.length + ' Hauptknöpfe gleichzeitig sichtbar: ' + prim.map(b => b.textContent.trim().slice(0, 20)).join(' / '));
  }
  // 23 ziffern: running times keep their width (tabular digits)
  if (isPlayer) textEls.forEach(el => {
    if (/^\s*\d{1,2}:\d{2}\s*$/.test(el.textContent) && !/tabular-nums/.test(cs(el).fontVariantNumeric)) add('ziffern', 'Zeit springt in der Breite (keine gleich breiten Ziffern)', el);
  });

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
