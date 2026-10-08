import asyncio, json
from playwright.async_api import async_playwright

# Layout audit (Fabian, 2026-10-04: "Sowas muss geprüft werden und darf
# nicht vorkommen"): every area's home screen, plus each NAT sub-tab, at
# phone, tablet and laptop widths. Fails on
#  - a word broken in the middle across two lines (e.g. "Atemtrainin|g"),
#  - text sticking out of its own button/tab,
#  - the page scrolling sideways.
# A break right after a hyphen ("Flash-|Speicher") is allowed.
# New screens get covered by adding them to AREAS / the NAT loop.

BASE = "http://localhost:8845/index.html?bereich="
AREAS = ["heute", "visual", "breath", "movement", "workout", "cardio", "nat", "test", "free", "aktivierung", "hilfsmittel", "fortschritt"]
WIDTHS = [375, 390, 430, 600, 768, 820, 1024, 1180, 1366]
# iPhone text size (2026-10-06): the app follows the iOS setting up to 1.25x
# (--ts), so small phones are also checked with the biggest and smallest factor.
SCALED = [(375, 1.25), (390, 1.25), (430, 1.25), (390, 0.95)]

AUDIT_JS = r"""
() => {
  const scr = [...document.querySelectorAll('.screen')].find(s => !s.hidden && s.offsetParent !== null);
  const root = scr || document.body;
  const out = [];
  const visible = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const el = n.parentElement;
    if (!el || !n.textContent.trim() || !visible(el)) continue;
    if (el.closest('[hidden], details:not([open]) > :not(summary), input, textarea, select, svg')) continue;
    const re = /[^\s\-–­/]+[\-–­/]?/g;
    let m;
    while ((m = re.exec(n.textContent))) {
      const tok = m[0].replace(/[\-–­/]$/, '');
      if (tok.length < 2) continue;
      // Compare the line of the word's first and last letter (per-letter
      // ranges: a range spanning a soft hyphen also reports the hyphen glyph
      // on the previous line, which is a legal break, not a split word).
      const lineOf = i => {
        const rg = document.createRange();
        rg.setStart(n, i); rg.setEnd(n, i + 1);
        const rs = [...rg.getClientRects()];
        return rs.length ? Math.round(rs[rs.length - 1].top) : null;
      };
      const a = lineOf(m.index), z = lineOf(m.index + tok.length - 1);
      if (a !== null && z !== null && Math.abs(z - a) > 4)
        out.push('Wort getrennt: "' + tok + '" in <' + el.tagName.toLowerCase() + '.' + el.className + '>');
    }
  }
  root.querySelectorAll('button, .section-tab, .sub-tab, .choice').forEach(b => {
    if (!visible(b) || b.closest('[hidden]')) return;
    if (b.scrollWidth > b.clientWidth + 2) out.push('Text ragt aus Knopf: "' + b.textContent.trim().slice(0, 30) + '"');
  });
  // Tabs keep their label on one line (Fabian, 2026-10-05: "keine Umbrüche in den Reitern").
  root.querySelectorAll('.section-tab, .sub-tab').forEach(t => {
    if (!visible(t)) return;
    const rg = document.createRange(); rg.selectNodeContents(t);
    const lines = new Set([...rg.getClientRects()].filter(r => r.width > 1).map(r => Math.round(r.top))).size;
    if (lines > 1) out.push('Reiter zweizeilig: "' + t.textContent.trim().slice(0, 30) + '"');
  });
  if (document.documentElement.scrollWidth > window.innerWidth + 1)
    out.push('Seite scrollt seitlich (' + document.documentElement.scrollWidth + ' > ' + window.innerWidth + ')');
  return [...new Set(out)];
}
"""

def ts_tag(ts):
    return "" if ts == 1 else f" Schrift x{ts}"

async def audit(pg, label, problems):
    found = await pg.evaluate(AUDIT_JS)
    for f in found:
        problems.append(label + ": " + f)

async def main():
    problems, errors = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        for w, ts in [(w, 1) for w in WIDTHS] + SCALED:
            ctx = await b.new_context(viewport={"width": w, "height": 900}, service_workers="block")
            await ctx.add_init_script("localStorage.setItem('fwmc-test-unlocked','true');localStorage.setItem('fwmc-tips-seen','true')"
                                      + (f";localStorage.setItem('fwmc-test-textscale','{ts}');localStorage.setItem('fwmc-test-bottomnav','true')" if ts != 1 else ""))
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            for area in AREAS:
                await pg.goto(BASE + ("heute" if area == "hilfsmittel" else area)); await pg.wait_for_timeout(250)
                if area == "hilfsmittel":
                    # Hilfsmittel und Starterpaket (Mehr, 2026-10-08): no page parameter, opened like the Mehr row
                    await pg.evaluate("() => document.getElementById('moreGearBtn').click()"); await pg.wait_for_timeout(150)
                await audit(pg, f"{w}px{ts_tag(ts)} {area}", problems)
                if area == "heute":
                    # Vorname in der Begrüßung (2026-10-08): inline form open, then a long name
                    await pg.evaluate("() => { const b = document.getElementById('helloNameBtn'); if (b && !b.hidden) b.click(); }")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} heute/vorname-form", problems)
                    await pg.evaluate("() => localStorage.setItem('fwmc-name-v1', 'Maximiliane-Charlotte-Josefine')")
                    await pg.goto(BASE + "heute"); await pg.wait_for_timeout(250)
                    await audit(pg, f"{w}px{ts_tag(ts)} heute/vorname-lang", problems)
                    await pg.evaluate("() => localStorage.removeItem('fwmc-name-v1')")
                if area == "fortschritt":
                    # QR-Übergabe (2026-10-08): range screen, QR code, import sheet, paste sheet, Kunden-Training strip
                    await pg.evaluate("""() => { const t = Date.now(); localStorage.setItem('fwmc-history-v1', JSON.stringify([0, 1, 2].map(i => ({id: 'w' + i, ts: new Date(t - (5 + i * 20) * 60000).toISOString(), kind: 'exercise', title: ['Objektverfolgung (MOT) · Geschwindigkeit', 'Farbfelder · Antippen', 'Gleichgewicht · Wörter'][i], seconds: 300, rating: null})))); }""")
                    await pg.goto(BASE + "fortschritt"); await pg.wait_for_timeout(250)
                    await audit(pg, f"{w}px{ts_tag(ts)} fortschritt/verlauf", problems)
                    await pg.evaluate("() => document.getElementById('handoverOpenBtn').click()"); await pg.wait_for_timeout(150)
                    await audit(pg, f"{w}px{ts_tag(ts)} uebergabe/zeitraum", problems)
                    await pg.evaluate("() => document.getElementById('handoverGoBtn').click()"); await pg.wait_for_timeout(500)
                    await audit(pg, f"{w}px{ts_tag(ts)} uebergabe/qr", problems)
                    qurl = await pg.get_attribute("#handoverQrCanvas", "data-url")
                    await pg.evaluate("() => { localStorage.setItem('fwmc-test-ios-browser', 'true'); localStorage.removeItem('fwmc-history-v1'); }")
                    await pg.goto(qurl); await pg.wait_for_timeout(400)
                    await audit(pg, f"{w}px{ts_tag(ts)} uebergabe/import-sheet", problems)
                    await pg.evaluate("() => { localStorage.removeItem('fwmc-test-ios-browser'); document.getElementById('handoverImportNoBtn').click(); }")
                    await pg.goto(BASE + "fortschritt"); await pg.wait_for_timeout(250)
                    await pg.evaluate("() => document.getElementById('handoverPasteOpenBtn').click()"); await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} uebergabe/einfuegen", problems)
                    await pg.evaluate("() => { document.getElementById('handoverPasteCancelBtn').click(); document.getElementById('clientRunStartBtn').click(); }"); await pg.wait_for_timeout(150)
                    await audit(pg, f"{w}px{ts_tag(ts)} uebergabe/kunden-training", problems)
                    await pg.evaluate("() => localStorage.removeItem('fwmc-client-session-v1')")
                if area == "hilfsmittel":
                    # with a shop link: "Ansehen" + "Werbung · Partner-Link" + partner sentence
                    await pg.evaluate("() => { window.__gear.items.forEach(g => { g.link = 'https://example.com/' + g.id; }); window.__gear.render(); }")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} hilfsmittel-links", problems)
                if area == "nat":
                    subs = await pg.eval_on_selector_all("#natHome .sub-tab", "els => els.map(e => e.dataset.natSub)")
                    for s in subs[1:]:
                        await pg.click(f'#natHome .sub-tab[data-nat-sub="{s}"]'); await pg.wait_for_timeout(150)
                        await audit(pg, f"{w}px{ts_tag(ts)} nat/{s}", problems)
                    # Gleichgewicht · Wörter + Bewegter Hintergrund (2026-10-08): ready screen with every row open
                    await pg.evaluate("() => document.getElementById('balanceOpenBtn').click()"); await pg.wait_for_timeout(150)
                    await pg.evaluate("() => { ['[data-bal-content=woerter]','[data-bal-wordlist=farben]'].forEach(s => document.querySelector(s).click()); document.getElementById('balanceAdvanced').open = true; const g = document.querySelector('#balanceReady .mbg-group'); g.querySelector('[data-opto-v=punkte]').click(); g.querySelector('[data-opto-v=schraeg]').click(); }")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} nat/balance-woerter-mbg", problems)
                    await pg.evaluate("() => { document.querySelector('[data-bal-content=stifte]').click(); const g = document.querySelector('#balanceReady .mbg-group'); g.querySelector('[data-opto-v=links]').click(); g.querySelector('[data-opto-v=aus]').click(); }")
                    # Objektverfolgung (MOT) + Bewegter Hintergrund (2026-10-08)
                    await pg.evaluate("() => { document.getElementById('motOpenSpeed').click(); document.getElementById('motAdvanced').open = true; const g = document.querySelector('#motReady .mbg-group'); g.querySelector('[data-opto-v=streifen]').click(); g.querySelector('[data-opto-v=schraeg]').click(); }")
                    await pg.wait_for_timeout(150)
                    await audit(pg, f"{w}px{ts_tag(ts)} nat/mot-mbg", problems)
                    await pg.evaluate("() => { const g = document.querySelector('#motReady .mbg-group'); g.querySelector('[data-opto-v=links]').click(); g.querySelector('[data-opto-v=aus]').click(); }")
                if area == "visual":
                    # Farbfelder ready screen (2026-10-07): Modus, Stufe 1-4, hand rows
                    await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(150)
                    await pg.evaluate("() => ['[data-ff-mode=regeln]','[data-ff-level=\"4\"]','[data-ff-hands=\"1\"]'].forEach(s => document.querySelector(s).click())")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} visual/farbfelder", problems)
                    # Reize (2026-10-07 night): Sehen und Hören shows gilt, Mischung, Rhythmus-Umkehr
                    await pg.evaluate("() => ['[data-ff-mode=sehenhoeren]','[data-ff-flip=\"2\"]'].forEach(s => document.querySelector(s).click())")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} visual/farbfelder-sehenhoeren", problems)
                    # Einblenden (2026-10-08): "Wie viele Felder" row
                    await pg.evaluate("() => ['[data-ff-mode=einblenden]','[data-ff-count=phasen]'].forEach(s => document.querySelector(s).click())")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} visual/farbfelder-einblenden", problems)
                    await pg.evaluate("() => document.querySelector('[data-ff-count=wechsel]').click()")
                    await pg.evaluate("() => ['[data-ff-hands=\"0\"]','[data-ff-flip=\"0\"]','[data-ff-mode=leuchten]'].forEach(s => document.querySelector(s).click())")
                    # Hütchen · Farbe + Zahl ready screen (2026-10-07): Anzahl Felder, Hilfsmittel
                    await pg.click("#backToHome"); await pg.wait_for_timeout(150)
                    await pg.click('.excard[data-exercise="cone-number"]'); await pg.wait_for_timeout(150)
                    await audit(pg, f"{w}px{ts_tag(ts)} visual/cone-number", problems)
                    # Hütchen · Laufweg ready screen (2026-10-08): Weg merken, Nach Zeit, Reihenfarben open
                    await pg.click("#backToHome"); await pg.wait_for_timeout(150)
                    await pg.click('.excard[data-exercise="cone-path"]'); await pg.wait_for_timeout(150)
                    await pg.evaluate("() => { document.querySelector('[data-lw-variant=merken]').click(); document.querySelector('[data-lw-end=dauer]').click(); document.getElementById('lwAdvanced').open = true; }")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} visual/cone-path", problems)
                    await pg.evaluate("() => { document.querySelector('[data-lw-variant=karte]').click(); document.querySelector('[data-lw-end=runden]').click(); }")
                    # Zusatzaufgabe Rechnen (2026-10-08) on an arrow exercise
                    await pg.click("#backToHome"); await pg.wait_for_timeout(150)
                    await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(150)
                    await pg.evaluate("() => { const t = document.querySelector('[data-addon-task=rechnen]'); if (t) { const d = t.closest('details'); if (d) d.open = true; t.click(); } }")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} visual/addon-rechnen", problems)
                    await pg.evaluate("() => { const t = document.querySelector('[data-addon-task=periph]'); if (t) t.click(); }")
                if area == "test":
                    # Ton-Sequenz ready screen (2026-10-08): safety note open, Wechsel + Puls + Gleiten rows
                    await pg.click("#tonOpenBtn"); await pg.wait_for_timeout(150)
                    await pg.evaluate("() => { document.getElementById('tonSafety').open = true; document.querySelector('[data-ton-ear=alt]').click(); document.querySelector('[data-ton-pattern=pulse]').click(); }")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} test/ton-sequenz", problems)
                    await pg.evaluate("() => { document.querySelector('[data-ton-pattern=glide]').click(); }")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} test/ton-sequenz-gleiten", problems)
                    await pg.evaluate("() => { document.querySelector('[data-ton-pattern=steady]').click(); document.querySelector('[data-ton-ear=both]').click(); }")
                if area == "aktivierung":
                    # Optodrum ready screen (2026-10-08) with every sub row open, then the pause sheet
                    await pg.click("#optoOpenBtn"); await pg.wait_for_timeout(150)
                    await pg.evaluate("() => { document.getElementById('optoAdvanced').open = true; document.querySelector('#optoReadyControls [data-opto-f=dir][data-opto-v=schraeg]').click(); }")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} aktivierung/optodrum", problems)
                    await pg.evaluate("() => document.querySelector('#optoReadyControls [data-opto-f=dir][data-opto-v=wechsel]').click()")
                    await pg.wait_for_timeout(100)
                    await audit(pg, f"{w}px{ts_tag(ts)} aktivierung/optodrum-wechsel", problems)
                    await pg.evaluate("() => document.querySelector('#optoReadyControls [data-opto-f=dir][data-opto-v=links]').click()")
                if area == "free":
                    # Freie Bausteine: ready screen and editor (checklist) of the template
                    await pg.click('#freeTplGrid [data-free-id="tpl-dehnen"]'); await pg.wait_for_timeout(150)
                    await audit(pg, f"{w}px{ts_tag(ts)} free/ready", problems)
                    await pg.click("#freeCopyBtn"); await pg.wait_for_timeout(150)
                    await audit(pg, f"{w}px{ts_tag(ts)} free/edit", problems)
            await ctx.close()
        await b.close()
    for x in problems: print("  " + x)
    print("Layout-Audit ohne Befund:", not problems, f"({len(problems)} Befunde)")
    print("No page errors:", not errors, errors[:3])

asyncio.run(main())
