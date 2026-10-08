"""Reaktionstraining neu (Fabian 07.10.): Anzeige Wandernde Zeilen / Ganzes
Feld / Band, Felder pro Zeile 3-5, Symbole Vier Felder / Vier Punkte / Nur
Pfeil / Figur / Kreise, carried by presets and Kombi; plus the yellow
Test look on the Reaktion pages (area stays open, no code)."""
import asyncio, json
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)} {extra}")

INIT = ("localStorage.setItem('fwmc-tips-seen','1');localStorage.setItem('fwmc-test-bottomnav','true');"
        "localStorage.setItem('fwmc-test-codequiet','true');"
        "if(!localStorage.getItem('fwmc-master-v1'))localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}));")

ROWS_INFO = """() => {
  const v = document.querySelector('#movementLane .mv-rows-view');
  if (!v) return null;
  const st = document.querySelector('.movement-stage').getBoundingClientRect();
  const r = v.getBoundingClientRect(), bar = document.getElementById('movementPlayerBar').getBoundingClientRect();
  const rows = [...v.querySelectorAll('.mv-row')].map(e => ({ k: Math.floor(+e.firstElementChild.dataset.idx / e.children.length), y: e.getBoundingClientRect().top, op: +getComputedStyle(e).opacity, n: e.children.length }));
  const cell = v.querySelector('.mv-cell').getBoundingClientRect();
  return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, stageBottom: st.bottom, barBottom: bar.bottom,
           active: v.querySelectorAll('.mv-cell.active').length, activeIdx: +(v.querySelector('.mv-cell.active') || {dataset:{idx:-1}}).dataset.idx,
           rows, cellW: cell.width, sw: document.documentElement.scrollWidth, vw: innerWidth };
}"""

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        errs = []
        async def page(w=390, h=844, scheme="light", init=""):
            ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
            await ctx.add_init_script(INIT + init)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            return ctx, pg

        # ---- 1. Test look on the Reaktion pages ----
        for w, scheme in [(390, "light"), (390, "dark"), (1024, "light")]:
            ctx, pg = await page(w, 844, scheme)
            await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(500)
            info = await pg.evaluate("""() => {
              const h = document.getElementById('movementHome'), k = h.querySelector('.hero-kicker');
              const acc = getComputedStyle(document.documentElement).getPropertyValue('--test-accent').trim();
              const card = document.getElementById('movementStartCard');
              const note = h.querySelector('.test-note');
              return { badge: (k.querySelector('.test-unlock-badge') || {}).textContent, noCodeText: !h.textContent.includes('Mit Code freigeschaltet'),
                       kicker: getComputedStyle(k).color, bar: getComputedStyle(card).borderLeftColor, accRgb: (() => { const d = document.createElement('i'); d.style.color = acc; document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; })(),
                       note: note && note.getBoundingClientRect().height > 0 ? note.textContent : null, sw: document.documentElement.scrollWidth, vw: innerWidth };
            }""")
            tag = f"{w} {scheme}"
            check(f"[{tag}] Reaktion home: kicker with 'Test' pill, no 'Mit Code freigeschaltet'", info["badge"] == "Test" and info["noCodeText"], info["badge"])
            check(f"[{tag}] kicker and exercise bar in the Test yellow", info["kicker"] == info["accRgb"] and info["bar"] == info["accRgb"], (info["kicker"], info["bar"], info["accRgb"]))
            check(f"[{tag}] 'Noch im Test' note visible", info["note"] and info["note"].startswith("Noch im Test"), info["note"])
            check(f"[{tag}] no sideways scroll on Reaktion home", info["sw"] <= info["vw"])
            await pg.click("#movementStartCard"); await pg.wait_for_timeout(300)
            check(f"[{tag}] ready screen shows the Test note too", await pg.evaluate("(() => { const n = document.querySelector('#movementReady .test-note'); return !!n && n.getBoundingClientRect().height > 0; })()"))
            await ctx.close()
        ctx, pg = await page()
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        check("other areas have no Test look", await pg.evaluate("document.querySelectorAll('.screen.test-look:not([id^=movement])').length === 0 && !document.querySelector('#home .test-note')"))
        await ctx.close()

        # ---- 2. defaults + migration ----
        ctx, pg = await page(init="if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');localStorage.setItem('fwmc-movement-v1',JSON.stringify({bpm:60,preview:2,figureStyle:'figur',direction:'links'}));}")
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(300)
        st = await pg.evaluate("""() => ({ layout: [...document.querySelectorAll('[data-mv-layout].active')].map(e => e.dataset.mvLayout),
            rowlen: [...document.querySelectorAll('[data-mv-rowlen].active')].map(e => e.dataset.mvRowlen),
            fig: [...document.querySelectorAll('[data-mv-figure].active')].map(e => e.dataset.mvFigure),
            prevHidden: document.getElementById('movementPreviewGroup').hidden, dirHidden: document.getElementById('movementDirectionGroup').hidden,
            rowHidden: document.getElementById('movementRowLenGroup').hidden, help: document.getElementById('movementLayoutHelp').textContent })""")
        check("old saved settings move once to Wandernde Zeilen, 4 Felder, Vier Felder", st["layout"] == ["zeilen"] and st["rowlen"] == ["4"] and st["fig"] == ["felder"], st)
        check("Vorschau + Laufrichtung only for Band, Felder pro Zeile shown", st["prevHidden"] and st["dirHidden"] and not st["rowHidden"] and len(st["help"]) > 20)
        await pg.click("[data-mv-layout=band]")
        st2 = await pg.evaluate("({ p: document.getElementById('movementPreviewGroup').hidden, r: document.getElementById('movementRowLenGroup').hidden })")
        check("Band shows Vorschau again, hides Felder pro Zeile", not st2["p"] and st2["r"])
        await pg.click("[data-mv-layout=feld]"); await pg.click("[data-mv-rowlen='3']"); await pg.click("[data-mv-figure=pfeil]")
        await pg.reload(); await pg.wait_for_timeout(400)
        saved = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-movement-v1'))")
        check("choice persists across reload (no second migration)", saved["layout"] == "feld" and saved["rowLen"] == 3 and saved["figureStyle"] == "pfeil", saved)
        await ctx.close()

        # ---- 3. symbols: each style draws one highlighted limb ----
        ctx, pg = await page()
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(300)
        for sym in ["felder", "punkte", "pfeil", "figur"]:
            await pg.click(f"[data-mv-figure={sym}]")
            n = await pg.evaluate("""() => [...document.querySelectorAll('#movementPicker .movement-chip')].map(c => c.querySelector('svg').innerHTML.toLowerCase().split('#ff9110').length - 1)""")
            check(f"symbol '{sym}': every picker chip shows exactly one highlighted part", len(n) == 8 and all(x >= 1 for x in n), n)
        check("four symbol choices visible (Kreise only kept for old settings)", await pg.evaluate("[...document.querySelectorAll('[data-mv-figure]')].filter(e => e.offsetParent).length === 4"))
        await ctx.close()

        # ---- 4. players: Zeilen wander, Feld stands still, both stay clear of the bar ----
        for w, h in [(390, 844), (360, 640), (1024, 768), (430, 932)]:
            for lay, rl in [("zeilen", 4), ("feld", 5), ("zeilen", 3)]:
                ctx, pg = await page(w, h, init="window.__fastBpm=1;")
                await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
                await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
                await pg.click(f"[data-mv-layout={lay}]"); await pg.click(f"[data-mv-rowlen='{rl}']"); await pg.click("[data-mv-figure=felder]")
                await pg.evaluate("document.getElementById('movementBpmSlider').value=160;document.getElementById('movementBpmSlider').dispatchEvent(new Event('input'))")
                await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
                a = await pg.evaluate(ROWS_INFO)
                await pg.wait_for_timeout(int(60 / 160 * 1000 * (rl + 1.5)))
                b2 = await pg.evaluate(ROWS_INFO)
                tag = f"{w}x{h} {lay} {rl}"
                check(f"[{tag}] rows view below the player bar and on the stage", a and a["top"] >= a["barBottom"] and a["bottom"] <= a["stageBottom"] + 1, a and (a["top"], a["barBottom"], a["bottom"], a["stageBottom"]))
                check(f"[{tag}] exactly one active field, cells >= 44 px, no sideways scroll", a["active"] == 1 and b2["active"] == 1 and a["cellW"] >= 44 and a["sw"] <= a["vw"], (a["active"], a["cellW"]))
                check(f"[{tag}] {rl} fields per row", all(r["n"] == rl for r in a["rows"]), [r["n"] for r in a["rows"]])
                check(f"[{tag}] active field moves on", b2["activeIdx"] > a["activeIdx"], (a["activeIdx"], b2["activeIdx"]))
                if lay == "zeilen":
                    # after row 1 (2nd row) started, the rows glide up continuously
                    await pg.wait_for_timeout(120)
                    c = await pg.evaluate(ROWS_INFO)
                    # follow one row (by its first cell index) between two frames
                    def row_y(info, k): return next((r["y"] for r in info["rows"] if r.get("k") == k), None)
                    k = (c["activeIdx"]) // rl
                    y1 = row_y(b2, k); y2 = row_y(c, k)
                    check(f"[{tag}] rows glide up while you work (no jump)", y1 is not None and y2 is not None and 0 < y1 - y2 < 60, (k, y1, y2))
                    check(f"[{tag}] next row visible (2+ rows shown, faded ahead)", sum(1 for r in c["rows"] if r["op"] > 0.3) >= 2)
                else:
                    check(f"[{tag}] field stands still ({rl} rows)", sorted(round(r["y"]) for r in a["rows"]) == sorted(round(r["y"]) for r in b2["rows"]) and len(a["rows"]) == rl)
                # pause: Vorschau not offered for rows, resume keeps rows
                await pg.click("#movementPauseBtn"); await pg.wait_for_timeout(200)
                check(f"[{tag}] pause sheet hides Vorschau", await pg.evaluate("document.getElementById('movementPausePreviewRow').closest('.group').hidden"))
                await pg.click("#movementResumeBtn"); await pg.wait_for_timeout(300)
                d = await pg.evaluate(ROWS_INFO)
                check(f"[{tag}] after Weiter still rows with one active field", d and d["active"] == 1)
                await ctx.close()

        # ---- 5. Band still works and resets the rows padding ----
        ctx, pg = await page()
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.click("[data-mv-layout=zeilen]"); await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(300)
        if await pg.locator("#movementReady").is_hidden():
            await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        await pg.click("[data-mv-layout=band]"); await pg.click("[data-mv-preview='3']"); await pg.click("#movementStartBtn"); await pg.wait_for_timeout(300)
        bi = await pg.evaluate("({ cls: document.getElementById('movementLane').className, pad: document.getElementById('movementLane').style.paddingTop, act: document.querySelectorAll('#movementLane .movement-tile.active').length, next: document.querySelectorAll('#movementLane .movement-tile.next').length })")
        check("Band: strip with active + 2 next, no leftover padding", "dir-" in bi["cls"] and bi["act"] == 1 and bi["next"] == 2 and bi["pad"] in ("", "0px"), bi)
        await ctx.close()

        # ---- 6. presets + Kombi carry layout/rowLen/symbol; old blocks keep the strip ----
        ctx, pg = await page()
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.click("[data-mv-layout=feld]"); await pg.click("[data-mv-rowlen='5']"); await pg.click("[data-mv-figure=punkte]")
        await pg.click("#movementSaveBtn"); await pg.fill("#movementSaveNameInput", "Feld 5"); await pg.click("#movementSaveConfirmBtn")
        pre = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-movement-saved-v1')).slice(-1)[0]")
        check("preset stores layout, rowLen, symbol", pre.get("layout") == "feld" and pre.get("rowLen") == 5 and pre.get("figureStyle") == "punkte", pre)
        await pg.click("[data-mv-layout=zeilen]"); await pg.click("[data-mv-rowlen='3']")
        await pg.locator("#movementSavedList button", has_text="Feld 5").first.click(); await pg.wait_for_timeout(400)
        pi = await pg.evaluate(ROWS_INFO)
        check("loading the preset plays Feld with 5 per row", pi and all(r["n"] == 5 for r in pi["rows"]) and len(pi["rows"]) == 5, pi and [r["n"] for r in pi["rows"]])
        await ctx.close()
        # an old preset (made before 07.10., no layout) keeps the strip it was built with
        ctx, pg = await page(init="localStorage.setItem('fwmc-movement-saved-v1',JSON.stringify([{id:'1',name:'Alt',movements:['armL-heben','armR-heben','legL-heben'],preview:2,bpm:60,durationMin:1,mirror:true,showLabel:true,direction:'rechts',figureStyle:'figur'}]));")
        await pg.goto(BASE + "?bereich=movement"); await pg.wait_for_timeout(400)
        await pg.click("#movementStartCard"); await pg.wait_for_timeout(200)
        await pg.locator("#movementSavedList button", has_text="Alt").first.click(); await pg.wait_for_timeout(400)
        old = await pg.evaluate("({ cls: document.getElementById('movementLane').className, rows: !!document.querySelector('.mv-rows-view') })")
        check("old preset without layout plays the strip (Band)", "dir-" in old["cls"] and not old["rows"], old)
        await ctx.close()

        # ---- 7. Tipps-Karte auf Heute (Fabian 07.10.) ----
        for w, scheme in [(390, "light"), (390, "dark"), (1024, "light")]:
            # 08.10.: since 07.10. (7e15737, "Heute für Neue") an empty history shows
            # the newcomer layout (Wochenplan below the code card, progress card
            # hidden), so "between week and progress" only exists for a regular
            # client - seed three finished runs (starterStage() -> null).
            regular = "[" + ",".join('{"id":"r%d","ts":"2026-10-01T10:00:00.000Z","kind":"exercise","exId":"vt-color","title":"X","seconds":300}' % i for i in range(3)) + "]"
            ctx, pg = await page(w, 844, scheme, init="localStorage.setItem('fwmc-test-tipshint','true');"
                                 f"if(!localStorage.getItem('fwmc-history-v1'))localStorage.setItem('fwmc-history-v1','{regular}');")
            await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(500)
            info = await pg.evaluate("""() => { const c = document.getElementById('todayTipsCard').getBoundingClientRect();
              const wk = document.querySelector('.today-week').getBoundingClientRect(), pr = document.querySelector('.today-progress').getBoundingClientRect();
              return { vis: c.height > 0, between: c.top >= wk.bottom && c.bottom <= pr.top,
                       taps: [...document.querySelectorAll('#todayTipsCard button')].every(x => x.getBoundingClientRect().height >= 44) }; }""")
            tag = f"{w} {scheme}"
            check(f"[{tag}] Tipps card on Heute between week and progress, buttons >= 44 px", info["vis"] and info["between"] and info["taps"], info)
            await pg.click("#todayTipsOpenBtn"); await pg.wait_for_timeout(200)
            check(f"[{tag}] 'Tipps ansehen' opens the tips sheet", await pg.is_visible("#tipsSheet"))
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(200)
            check(f"[{tag}] card stays after just reading the tips", await pg.is_visible("#todayTipsCard"))
            await pg.click("#todayTipsHideBtn"); await pg.wait_for_timeout(300)
            toast = await pg.evaluate("(document.querySelector('.where-toast') || {}).textContent || ''")
            check(f"[{tag}] Ausblenden hides it and says it stays under Mehr", await pg.is_hidden("#todayTipsCard") and "Mehr" in toast, toast)
            await pg.reload(); await pg.wait_for_timeout(400)
            check(f"[{tag}] stays hidden after reload, Mehr still has the tips", await pg.is_hidden("#todayTipsCard") and await pg.evaluate("!!document.getElementById('moreTipsBtn')"))
            await ctx.close()

        check("no page errors", not errs, errs[:3])
        await b.close()
    print(f"\n{sum(results)}/{len(results)} checks passed")

asyncio.run(main())
