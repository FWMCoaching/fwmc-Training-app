import asyncio, json, os
from playwright.async_api import async_playwright

# Aktivierung (8th area) + Optodrum (Fabian 2026-10-08: "Ja so").
# Area: Training hub tile ("Dazu" group), ?bereich=aktivierung, same frame as
# the siblings (code card, tiles, Kombi link, Gesamter Trainingsverlauf).
# Optodrum: settings persist, the canvas really moves (pixels sampled over
# time, direction respected for links/rechts/hoch), live tempo/direction in
# the pause sheet, "Wechsel" flips, presets, Kombi capture/edit/playback
# without touching the client's own settings, plan entry + history,
# Sanfte Reize caps the tempo, no page/console errors. Screenshots in
# tests/screenshots/aktivierung/.

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "aktivierung")
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "if(!localStorage.getItem('fwmc-master-v1'))localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}));")

fails = []
def check(label, cond, info=""):
    print(f"{label}: {bool(cond)}" + (f"  [{info}]" if not cond and info != "" else ""))
    if not cond: fails.append(label)

async def visible_screen(pg):
    return await pg.evaluate("() => { const s = [...document.querySelectorAll('.screen')].find(e => !e.hidden); return s ? s.id : null; }")

async def prefs(pg):
    return await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-optodrum-prefs-v1') || '{}')")

async def set_prefs(pg, p):
    await pg.evaluate("(p) => localStorage.setItem('fwmc-optodrum-prefs-v1', JSON.stringify(p))", p)

# Shift of the pattern along one line of the canvas between two samples
# (best match within half a period); positive = towards right/bottom.
SHIFT_JS = """async ([axis, waitMs]) => {
  const c = document.getElementById('optoCanvas'), ctx = c.getContext('2d');
  const line = () => { const d = axis === 'x' ? ctx.getImageData(0, Math.floor(c.height * 0.6), c.width, 1).data
                                               : ctx.getImageData(Math.floor(c.width / 2), 0, 1, c.height).data;
    const out = []; for (let i = 0; i < d.length; i += 4) out.push((d[i] + d[i + 1] + d[i + 2]) / 3); return out; };
  const a = line(), t0 = window.__opto().t;
  await new Promise((r) => setTimeout(r, waitMs));
  const b = line(), t1 = window.__opto().t;
  let best = 0, bestErr = Infinity;
  for (let k = -39; k <= 39; k++) { let err = 0, n = 0;
    for (let i = 60; i < a.length - 60; i++) { err += Math.abs(a[i] - b[i + k]); n++; }
    err /= n; if (err < bestErr) { bestErr = err; best = k; } }
  return { shift: best, err: bestErr, dt: t1 - t0, pxs: window.__opto().pxs, dpr: window.devicePixelRatio };
}"""

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- area: hub tile + ?bereich= + frame ----
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(200)
        await pg.evaluate("() => localStorage.setItem('fwmc-test-bottomnav', 'true')")
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(400)
        tile = pg.locator('#hubAreaGrid .hub-extra .area-tile[data-area="activation"]')
        check("Training hub: Aktivierung tile in the 'Dazu' group", await tile.count() == 1 and "Aktivierung" in await tile.inner_text())
        await tile.click(); await pg.wait_for_timeout(300)
        check("tile opens #activationHome", await visible_screen(pg) == "activationHome")
        frame = await pg.evaluate("""() => { const h = document.getElementById('activationHome');
          return { code: !!h.querySelector('.code-card'), combo: !!h.querySelector('[data-open-combo]'), hist: !h.querySelector('#activationHistorySection').hidden,
                   tiles: h.querySelectorAll('#activationGrid [data-act-ex]').length, kicker: h.querySelector('.hero-kicker').textContent.trim(),
                   intro: h.querySelector('.hero-text').textContent.trim(), back: !!h.querySelector('.bar-back-btn') }; }""")
        check("area frame: code card, Kombi link, history, one exercise tile, ‹ back", frame["code"] and frame["combo"] and frame["hist"] and frame["tiles"] == 1 and frame["back"], frame)
        check("hero: 'Aktivierung' + one intro sentence", frame["kicker"] == "Aktivierung" and frame["intro"].startswith("Kurze Aktivierungen für zwischendurch"), frame)
        await pg.evaluate("() => localStorage.removeItem('fwmc-test-bottomnav')")
        for q in ("aktivierung", "activation"):
            await pg.goto(BASE + "?bereich=" + q); await pg.wait_for_timeout(250)
            check(f"?bereich={q} opens the area", await visible_screen(pg) == "activationHome")
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(300)
        check("Heute area tiles list Aktivierung too", await pg.evaluate("() => !!document.querySelector('#todayAreaGrid .area-tile[data-area=\"activation\"]')"))
        await pg.goto(BASE + "?bereich=aktivierung"); await pg.wait_for_timeout(250)

        # ---- ready screen: defaults, persistence ----
        await pg.click("#optoOpenBtn"); await pg.wait_for_timeout(200)
        check("ready screen opens with 'Training starten'", await visible_screen(pg) == "optoReady" and (await pg.inner_text("#optoStartBtn")).strip() == "Training starten")
        act = await pg.evaluate("() => [...document.querySelectorAll('#optoReadyControls .choice.active')].map(b => b.dataset.optoF + '=' + b.dataset.optoV)")
        check("defaults: Streifen, links, Mittel, 1 Min, Fixierpunkt aus", set(act) >= {"pattern=streifen", "dir=links", "speed=5", "durationS=60", "fix=0"}, act)
        R = "#optoReadyControls "
        for sel in ['[data-opto-f=pattern][data-opto-v=punkte]', '[data-opto-f=dir][data-opto-v=schraeg]', '[data-opto-f=diag][data-opto-v=lu]',
                    '[data-opto-f=speed][data-opto-v="8"]', '[data-opto-f=durationS][data-opto-v="120"]']:
            await pg.click(R + sel)
        await pg.click("#optoAdvanced summary")
        await pg.click(R + '[data-opto-f=fix][data-opto-v="1"]')
        await pg.evaluate("""() => { const set = (f, v) => { const i = document.querySelector(`#optoReadyControls [data-opto-r=${f}]`); i.value = v; i.dispatchEvent(new Event('input')); };
          set('size', 60); set('gap', 20); }""")
        await pg.click(R + '[data-opto-c=fg] [data-key=blau]'); await pg.click(R + '[data-opto-c=bg] [data-key=gelb]')
        lbl = await pg.inner_text(R + '[data-opto-lbl=size]')
        check("labels follow the pattern (Punktgröße)", lbl == "Punktgröße", lbl)
        await pg.reload(); await pg.wait_for_timeout(300)
        pr = await prefs(pg)
        check("settings persist across reload", pr.get("pattern") == "punkte" and pr.get("dir") == "schraeg" and pr.get("diag") == "lu" and pr.get("speed") == 8
              and pr.get("durationS") == 120 and pr.get("fix") is True and pr.get("size") == 60 and pr.get("gap") == 20 and pr.get("fg") == "blau" and pr.get("bg") == "gelb", pr)
        # boundary clamping of stored values
        await set_prefs(pg, {"pattern": "x", "speed": 99, "size": 1, "gap": 999, "swapS": 2, "durationS": 7, "fg": "pink"})
        await pg.goto(BASE + "?bereich=aktivierung"); await pg.wait_for_timeout(250)
        await pg.click("#optoOpenBtn"); await pg.wait_for_timeout(150)
        clamped = await pg.evaluate("() => [...document.querySelectorAll('#optoReadyControls input[type=range]')].map(i => i.dataset.optoR + '=' + i.value)")
        check("broken stored values are clamped (Stufe 10, 10 px, 200 px, 5 s, 10 s)", {"speed=10", "size=10", "gap=200", "swapS=5", "durationS=10"} <= set(clamped), clamped)

        # ---- run: the pattern moves, in the chosen direction ----
        async def start_with(pp):
            await set_prefs(pg, {**{"pattern": "streifen", "dir": "links", "speed": 2, "size": 40, "gap": 40, "fg": "schwarz", "bg": "weiss", "durationS": 60}, **pp})
            await pg.goto(BASE + "?bereich=aktivierung"); await pg.wait_for_timeout(250)
            await pg.click("#optoOpenBtn"); await pg.wait_for_timeout(120)
            await pg.click("#optoStartBtn"); await pg.wait_for_timeout(400)
        await start_with({})
        conv = await pg.evaluate("""() => ({ player: document.getElementById('optoPlayer').classList.contains('player'), back: document.getElementById('optoBackBtn').textContent,
          pause: document.getElementById('optoPauseBtn').textContent, status: document.getElementById('optoStatusEl').textContent })""")
        check("player conventions: .player, '✕ Beenden', 'Pause', status with arrow + time", conv["player"] and "Beenden" in conv["back"] and conv["pause"] == "Pause" and conv["status"].startswith("←"), conv)
        r = await pg.evaluate(SHIFT_JS, ["x", 250])
        exp = r["pxs"] * r["dt"]
        check("links: stripes move left at the chosen speed", r["shift"] < 0 and abs(-r["shift"] - exp) <= 4 and r["err"] < 20, r)
        await pg.screenshot(path=os.path.join(SHOTS, "390_light_run_streifen.png"))
        await start_with({"dir": "rechts"})
        r = await pg.evaluate(SHIFT_JS, ["x", 250])
        check("rechts: stripes move right", r["shift"] > 0 and abs(r["shift"] - r["pxs"] * r["dt"]) <= 4, r)
        await start_with({"dir": "hoch"})
        r = await pg.evaluate(SHIFT_JS, ["y", 250])
        check("hoch: stripes lie across and move up", r["shift"] < 0 and abs(-r["shift"] - r["pxs"] * r["dt"]) <= 4, r)
        await start_with({"pattern": "punkte", "dir": "schraeg", "diag": "ru", "size": 24, "gap": 30, "speed": 5})
        moved = await pg.evaluate("""async () => { const c = document.getElementById('optoCanvas'), ctx = c.getContext('2d');
          const snap = () => Array.from(ctx.getImageData(0, 0, c.width, c.height).data.filter((_, i) => i % 4 === 0 && (i / 4) % 7 === 0));
          const a = snap(), o0 = window.__opto(); await new Promise(r => setTimeout(r, 200)); const b = snap(), o1 = window.__opto();
          let diff = 0; for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) diff++;
          return { diff, dx: o1.dx - o0.dx, dy: o1.dy - o0.dy }; }""")
        check("Punkte schräg rechts unten: raster drifts right and down", moved["diff"] > 100 and moved["dx"] > 0 and moved["dy"] > 0, moved)
        await pg.screenshot(path=os.path.join(SHOTS, "390_light_run_punkte.png"))

        # ---- pause sheet: live tempo + direction, saved for a standalone run ----
        await start_with({})
        await pg.click("#optoPauseBtn"); await pg.wait_for_timeout(200)
        t0 = (await pg.evaluate("window.__opto()"))["t"]
        await pg.wait_for_timeout(300)
        t1 = (await pg.evaluate("window.__opto()"))["t"]
        check("pause freezes the run", await pg.is_visible("#optoPauseOverlay") and abs(t1 - t0) < 0.01)
        P = "#optoPauseControls "
        await pg.click(P + '[data-opto-f=dir][data-opto-v=rechts]')
        await pg.click(P + '[data-opto-f=speed][data-opto-v="3"]')
        await pg.click(P + '[data-opto-f=pattern][data-opto-v=schach]')
        await pg.click(P + '[data-opto-c=fg] [data-key=rot]')
        o = await pg.evaluate("window.__opto()")
        pr = await prefs(pg)
        check("pause sheet: direction/tempo/pattern change live", o["dir"] == "rechts" and o["speed"] == 3 and o["pattern"] == "schach", o)
        check("standalone: live changes are saved", pr.get("dir") == "rechts" and pr.get("speed") == 3 and pr.get("pattern") == "schach" and pr.get("fg") == "rot", pr)
        await pg.screenshot(path=os.path.join(SHOTS, "390_light_pause.png"))
        await pg.click(P + '[data-opto-f=pattern][data-opto-v=streifen]')
        await pg.click("#optoResumeBtn"); await pg.wait_for_timeout(150)
        r = await pg.evaluate(SHIFT_JS, ["x", 200])
        check("after Weiter: moves right at Stufe 3", r["shift"] > 0 and r["pxs"] == 65, r)

        # ---- Wechsel flips every N s ----
        await start_with({"dir": "wechsel", "axis": "h", "swapS": 5, "speed": 2})
        r1 = await pg.evaluate(SHIFT_JS, ["x", 200])
        await pg.wait_for_timeout(5200)
        o = await pg.evaluate("window.__opto()")
        r2 = await pg.evaluate(SHIFT_JS, ["x", 200])
        st = await pg.inner_text("#optoStatusEl")
        check("Wechsel: starts to the left, flips after 5 s and runs right", r1["shift"] < 0 and o["flips"] >= 1 and r2["shift"] > 0 and st.startswith("→"), (r1, o, r2, st))

        # ---- natural end: done panel + history ----
        await start_with({"durationS": 10})
        await pg.wait_for_timeout(10600)
        h = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')[0] || null")
        check("10 s run ends by itself: done panel + history kind optodrum", await pg.is_visible("#optoDonePanel") and h and h["kind"] == "optodrum" and not h.get("aborted") and h["title"] == "Optodrum · Streifen", h)
        await pg.click("#optoDoneBackBtn"); await pg.wait_for_timeout(200)
        check("'Zur Übersicht' returns to the area", await visible_screen(pg) == "activationHome")
        hist = await pg.inner_text("#activationHistoryList")
        check("area history lists the run", "Optodrum" in hist, hist[:80])
        # Beenden before the end = aborted; Ohne Zeitlimit: Fertig = done
        await start_with({})
        await pg.wait_for_timeout(5300)
        await pg.click("#optoBackBtn"); await pg.wait_for_timeout(200)
        h = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')[0]")
        check("Beenden after 5 s = aborted (history + 'Optodrum beendet')", h.get("aborted") and (await pg.inner_text("#optoDonePanel h2")) == "Optodrum beendet", h)
        await start_with({"noLimit": True})
        check("Ohne Zeitlimit: 'Fertig' shown, clock counts up", await pg.is_visible("#optoFinishBtn") and (await pg.inner_text("#optoStatusEl"))[-4:] in ("0:00", "0:01"))
        await pg.wait_for_timeout(1200)
        await pg.click("#optoFinishBtn"); await pg.wait_for_timeout(200)
        h = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')[0]")
        check("Fertig = completed", not h.get("aborted") and await pg.is_visible("#optoDonePanel .done-check"), h)

        # ---- presets ----
        await set_prefs(pg, {"pattern": "punkte", "dir": "rechts", "speed": 7, "durationS": 30})
        await pg.goto(BASE + "?bereich=aktivierung"); await pg.wait_for_timeout(250)
        await pg.click("#optoOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#optoSaveBtn"); await pg.fill("#optoSaveNameInput", "Punkte rechts"); await pg.click("#optoSaveConfirmBtn"); await pg.wait_for_timeout(100)
        check("preset saved and listed", await pg.locator("#optoSavedList .bundle-item").count() == 1 and "Punkte rechts" in await pg.inner_text("#optoSavedList"))
        await pg.click(R + '[data-opto-f=pattern][data-opto-v=streifen]'); await pg.click(R + '[data-opto-f=dir][data-opto-v=hoch]')
        await pg.click("#optoSavedList .bundle-item"); await pg.wait_for_timeout(300)
        o = await pg.evaluate("window.__opto()")
        check("tapping the preset starts it with its values", o and o["pattern"] == "punkte" and o["dir"] == "rechts" and o["speed"] == 7, o)
        await pg.click("#optoBackBtn"); await pg.wait_for_timeout(150)

        # ---- Kombi: capture, edit, playback, isolation ----
        await set_prefs(pg, {"pattern": "streifen", "dir": "links", "speed": 5, "durationS": 60})
        def own_ok(pr): return pr.get("pattern") == "streifen" and pr.get("dir") == "links" and pr.get("speed") == 5 and pr.get("durationS") == 60
        await pg.goto(BASE + "?bereich=aktivierung"); await pg.wait_for_timeout(250)
        await pg.evaluate("() => document.querySelector('#activationHome [data-open-combo]').click()"); await pg.wait_for_timeout(200)
        grp = pg.locator('#comboAddGrid .combo-domain-group[data-domain="activation"]')
        check("Kombi: own group 'Aktivierung' with Optodrum", await grp.count() == 1 and "aktivierung" in (await grp.inner_text()).lower() and "Optodrum" in await grp.inner_text())
        await grp.locator(".combo-add-btn").first.click(); await pg.wait_for_timeout(200)
        check("capture opens the ready screen as 'Baustein: Optodrum'", await visible_screen(pg) == "optoReady" and await pg.inner_text("#optoReadyTitle") == "Baustein: Optodrum"
              and (await pg.inner_text("#optoStartBtn")).strip() == "Baustein übernehmen")
        await pg.click(R + '[data-opto-f=pattern][data-opto-v=schach]'); await pg.click(R + '[data-opto-f=dir][data-opto-v=rechts]')
        await pg.evaluate("() => { const i = document.querySelector('#optoReadyControls [data-opto-r=durationS]'); i.value = 10; i.dispatchEvent(new Event('input')); }")
        await pg.click("#optoStartBtn"); await pg.wait_for_timeout(200)
        rows = await pg.locator("#comboBlockList .chapter-row").all_inner_texts()
        check("commit adds 'Optodrum · Schachbrett' to the Kombi", await visible_screen(pg) == "comboScreen" and len(rows) == 1 and "Optodrum · Schachbrett" in rows[0] and "10 Sek" in rows[0], rows)
        check("capture left the own settings untouched", own_ok(await prefs(pg)), await prefs(pg))
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(200)
        a2 = await pg.evaluate("() => [...document.querySelectorAll('#optoReadyControls .choice.active')].map(b => b.dataset.optoF + '=' + b.dataset.optoV)")
        check("edit reopens the block's own values", await visible_screen(pg) == "optoReady" and "pattern=schach" in a2 and "dir=rechts" in a2, a2)
        await pg.click(R + '[data-opto-f=speed][data-opto-v="3"]')
        await pg.click("#optoStartBtn"); await pg.wait_for_timeout(200)
        rows = await pg.locator("#comboBlockList .chapter-row").all_inner_texts()
        check("edit replaces the block (Stufe 3), own settings still untouched", len(rows) == 1 and "Stufe 3" in rows[0] and own_ok(await prefs(pg)), rows)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(400)
        o = await pg.evaluate("window.__opto()")
        check("playback runs the block's settings (not the own ones)", o and o["pattern"] == "schach" and o["dir"] == "rechts" and o["speed"] == 3 and o["own"] is False, o)
        await pg.click("#optoPauseBtn"); await pg.wait_for_timeout(150)
        help_txt = await pg.inner_text("#optoPauseHelp")
        await pg.click(P + '[data-opto-f=dir][data-opto-v=hoch]')
        check("Kombi pause sheet changes only this run", (await pg.evaluate("window.__opto()"))["dir"] == "hoch" and own_ok(await prefs(pg)) and "nur für diesen Durchgang" in help_txt, help_txt)
        await pg.click("#optoResumeBtn")
        await pg.wait_for_timeout(10500)
        check("block ends after its 10 s and the Kombi finishes", await pg.is_visible("#comboDonePanel"))
        check("Kombi run never changed the own settings", own_ok(await prefs(pg)), await prefs(pg))

        # ---- Wochenplan: area + exercise entry, auto-tick ----
        opts = await pg.evaluate("""() => { const a = document.getElementById('planEntryArea'); a.value = 'activation';
          a.dispatchEvent(new Event('change')); return [...document.getElementById('planEntryWhat').options].map(o => o.textContent); }""")
        check("Wochenplan: area 'Aktivierung' offers Optodrum", "Optodrum" in opts, opts)
        await pg.evaluate("""() => { const d = new Date(); const ds = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
          localStorage.setItem('fwmc-history-v1', '[]');
          localStorage.setItem('fwmc-plan-v1', JSON.stringify({startDate: ds, phases: [], extras: {[ds]: [{id: 'pa1', area: 'activation', what: 'act:optodrum', code: '', time: '', minutes: 5}]}, skips: {}, done: {}})); }""")
        await set_prefs(pg, {"durationS": 10, "speed": 2})
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(400)
        main_txt = await pg.inner_text("#todayMain")
        check("Heute shows the planned Optodrum", "Optodrum" in main_txt, main_txt[:100])
        await pg.click("#todayMain [data-today-start]"); await pg.wait_for_timeout(200)
        check("starting it opens the Optodrum ready screen", await visible_screen(pg) == "optoReady")
        await pg.click("#optoStartBtn"); await pg.wait_for_timeout(10600)
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(400)
        done = await pg.evaluate("() => { const el = [...document.querySelectorAll('[data-occ=\"pa1\"]')].find(e => e.offsetParent); return el ? el.className : ''; }")
        check("planned entry auto-ticked (historyAreaOf -> activation)", "done" in done, done)

        # ---- Sanfte Reize: tempo capped, note + live switch ----
        await pg.evaluate("() => { const m = JSON.parse(localStorage.getItem('fwmc-master-v1') || '{}'); m.softStimuli = true; localStorage.setItem('fwmc-master-v1', JSON.stringify(m)); }")
        await set_prefs(pg, {"speed": 8, "durationS": 60})
        await pg.goto(BASE + "?bereich=aktivierung"); await pg.wait_for_timeout(250)
        await pg.click("#optoOpenBtn"); await pg.wait_for_timeout(150)
        note = await pg.is_visible('#optoReady [data-soft-note="optodrum"]')
        sh = await pg.inner_text('#optoReadyControls [data-opto-out=speedHelp]')
        check("Sanfte Reize: note on the ready screen + 'höchstens Stufe 4'", note and "höchstens Stufe 4" in sh, sh)
        await pg.click("#optoStartBtn"); await pg.wait_for_timeout(300)
        o = await pg.evaluate("window.__opto()")
        check("Sanfte Reize: Stufe 8 runs as Stufe 4", o["speed"] == 8 and o["eff"] == 4 and o["pxs"] == 90, o)
        await pg.click("#optoPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click('#optoPauseOverlay [data-soft-live="optodrum"][data-soft-val="0"]'); await pg.wait_for_timeout(100)
        o = await pg.evaluate("window.__opto()")
        check("pause sheet: Sanfte Reize off for this run = full tempo", o["eff"] == 8, o)
        await pg.click("#optoResumeBtn"); await pg.click("#optoBackBtn"); await pg.wait_for_timeout(150)
        await ctx.close()

        # ---- screenshots: 390 light/dark, 1024 running ----
        for scheme in ("light", "dark"):
            c2 = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", color_scheme=scheme)
            await c2.add_init_script(INIT + "localStorage.setItem('fwmc-test-bottomnav','true');")
            q = await c2.new_page()
            q.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            await q.goto(BASE + "?bereich=training"); await q.wait_for_timeout(400)
            await q.screenshot(path=os.path.join(SHOTS, f"390_{scheme}_hub.png"), full_page=True)
            await q.click('#hubAreaGrid .area-tile[data-area="activation"]'); await q.wait_for_timeout(300)
            await q.screenshot(path=os.path.join(SHOTS, f"390_{scheme}_home.png"), full_page=True)
            await q.click("#optoOpenBtn"); await q.wait_for_timeout(200)
            await q.click("#optoAdvanced summary"); await q.wait_for_timeout(100)
            await q.screenshot(path=os.path.join(SHOTS, f"390_{scheme}_ready.png"), full_page=True)
            await q.click("#optoStartBtn"); await q.wait_for_timeout(500)
            await q.screenshot(path=os.path.join(SHOTS, f"390_{scheme}_run.png"))
            await q.click("#optoPauseBtn"); await q.wait_for_timeout(200)
            await q.screenshot(path=os.path.join(SHOTS, f"390_{scheme}_pause.png"))
            await c2.close()
        c3 = await b.new_context(viewport={"width": 1024, "height": 768}, service_workers="block")
        await c3.add_init_script(INIT + "localStorage.setItem('fwmc-optodrum-prefs-v1', JSON.stringify({pattern:'punkte',dir:'schraeg',diag:'ro',fix:true}));")
        q = await c3.new_page()
        await q.goto(BASE + "?bereich=aktivierung"); await q.wait_for_timeout(300)
        await q.click("#optoOpenBtn"); await q.click("#optoStartBtn"); await q.wait_for_timeout(500)
        await q.screenshot(path=os.path.join(SHOTS, "1024_light_run_punkte_fix.png"))
        geo = await q.evaluate("() => { const c = document.getElementById('optoCanvas').getBoundingClientRect(), s = document.getElementById('optoStage').getBoundingClientRect(); return [c.width, c.height, s.width, s.height]; }")
        check("1024: canvas fills the stage", geo[0] == geo[2] and geo[1] == geo[3], geo)
        await q.set_viewport_size({"width": 800, "height": 600}); await q.wait_for_timeout(300)
        geo = await q.evaluate("() => { const c = document.getElementById('optoCanvas'), s = document.getElementById('optoStage').getBoundingClientRect(); return [c.width, c.height, Math.round(s.width), Math.round(s.height)]; }")
        check("resize: canvas follows the stage", geo[0] == geo[2] and geo[1] == geo[3], geo)
        await c3.close()
        await b.close()
    print("FAILED:", fails or "none")
    print("FINAL ERRORS:", errors)

asyncio.run(main())
