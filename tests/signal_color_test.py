import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Ziel-/Signalfarbe pro Übung (Fabian, 2026-10-02 "A. Ja"): every Test
# exercise with a fixed signal colour gets a picker in its Feineinstellungen;
# custom > colour-safe palette > default; texts naming the colour follow.


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked', 'true')")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        groups = await pg.eval_on_selector_all(".sig-group", "els => els.map(e => e.dataset.sigGroup)")
        print("signal groups for all 8 exercises:", sorted(groups) == sorted(["gng", "simon", "search", "ab", "stop", "reakt", "antizip", "corsi"]), groups)
        print("palette has no white:", await pg.locator('[data-sig-picker="gng.go"] .color-swatch[data-key="weiss"]').count() == 0)

        async def open_ready(name):
            await pg.click('.section-tab[data-section="test"]:visible >> nth=0'); await pg.wait_for_timeout(150)
            await pg.click(f"#{name}OpenBtn"); await pg.wait_for_timeout(200)
            await pg.click(f"#{name}Ready details.advanced summary"); await pg.wait_for_timeout(100)

        # ---- Go/No-Go: pick lila for "go" ----
        await open_ready("gng")
        print("GNG default status:", "Standard: Grün" in await pg.inner_text('#gngReady [data-sig-picker="gng.go"] + [data-sig-status]'))
        await pg.click('#gngReady [data-sig-picker="gng.go"] .color-swatch[data-key="lila"]'); await pg.wait_for_timeout(80)
        print("GNG instruction text follows:", await pg.inner_text('#gngReady .page-sub [data-sig="gng.go"]') == "lila")
        print("swatch active:", "active" in (await pg.get_attribute('#gngReady [data-sig-picker="gng.go"] .color-swatch[data-key="lila"]', "class")))
        bg = await pg.evaluate("""() => { const d = document.createElement('div'); d.className = 'gng-stimulus go'; document.body.appendChild(d);
            const c = getComputedStyle(d).backgroundColor; d.remove(); return c; }""")
        print("GNG go stimulus uses lila:", bg == "rgb(126, 79, 190)", bg)
        # clash warning: nogo very close to go
        await pg.click('#gngReady [data-sig-picker="gng.nogo"] .color-swatch[data-key="lila"]'); await pg.wait_for_timeout(80)
        print("clash warning shown for equal colours:", await pg.is_visible('#gngReady [data-sig-clash="gng"]'))
        print("start still allowed:", await pg.is_enabled("#gngReadyStartBtn"))
        await pg.click('#gngReady [data-sig-picker="gng.nogo"] + [data-sig-status] [data-sig-reset]'); await pg.wait_for_timeout(80)
        print("reset brings nogo back to Rot:", await pg.inner_text('#gngReady .page-sub [data-sig="gng.nogo"]') == "rot")
        print("clash warning gone:", await pg.is_hidden('#gngReady [data-sig-clash="gng"]'))

        # custom wins over the colour-safe palette
        await pg.click("#gngReady .cvd-group [data-cvd-kind='pal'][data-cvd-val='1']"); await pg.wait_for_timeout(60)
        print("custom go stays lila with safe palette on:", await pg.inner_text('#gngReady .page-sub [data-sig="gng.go"]') == "lila")
        print("nogo follows safe palette (orange):", await pg.inner_text('#gngReady .page-sub [data-sig="gng.nogo"]') == "orange")
        await pg.click("#gngReady .cvd-group [data-cvd-kind='pal'] ~ .cvd-status [data-cvd-reset], #gngReady [data-cvd-reset]") if await pg.locator("#gngReady [data-cvd-reset]").count() else None
        await pg.wait_for_timeout(60)

        # persistence
        await pg.reload(); await pg.wait_for_timeout(400)
        stored = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-signal-colors-v1'))")
        print("stored after reload:", stored == {"gng": {"go": "lila"}}, stored)
        await open_ready("gng")
        print("text after reload:", await pg.inner_text('#gngReady .page-sub [data-sig="gng.go"]') == "lila")
        await pg.click("#gngReadyStartBtn"); await pg.wait_for_timeout(200)
        seen = set()
        for _ in range(60):
            cls = await pg.get_attribute("#gngStimulus", "class") or ""
            if "go" in cls.split():
                await pg.wait_for_timeout(250)
                seen.add(await pg.evaluate("getComputedStyle(document.getElementById('gngStimulus')).backgroundColor"))
                if "rgb(126, 79, 190)" in seen: break
            await pg.wait_for_timeout(60)
        print("running GNG shows lila go stimulus:", "rgb(126, 79, 190)" in seen, seen)
        await pg.click("#gngBackBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"):
            await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)

        # ---- Simon: buttons relabel and recolour ----
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await open_ready("simon")
        await pg.click('#simonReady [data-sig-picker="simon.a"] .color-swatch[data-key="gruen"]'); await pg.wait_for_timeout(80)
        print("Simon left button label Grün:", (await pg.inner_text("#simonLeftBtn")).strip() == "Grün")
        print("Simon aria-label Grün:", await pg.get_attribute("#simonLeftBtn", "aria-label") == "Grün")
        btn_bg = await pg.evaluate("getComputedStyle(document.getElementById('simonLeftBtn')).backgroundColor")
        print("Simon left button green:", btn_bg == "rgb(46, 125, 50)", btn_bg)
        print("Simon ready text says Grün:", "Grün" in await pg.inner_text("#simonReady .page-sub"))

        # ---- Suchtest: cue and item colour ----
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await open_ready("search")
        await pg.click('#searchReady [data-sig-picker="search.target"] .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(80)
        print("Suchtest ready text 'Blauer Kreis':", "Blauer Kreis" in await pg.inner_text("#searchReady .page-sub"))
        await pg.click("#searchReadyStartBtn"); await pg.wait_for_timeout(300)
        hint = ""
        for _ in range(30):
            hint = await pg.inner_text("#searchHint")
            if "Ziel" in hint: break
            await pg.wait_for_timeout(60)
        print("Suchtest cue names the blue target:", "Blau" in hint, hint)
        target = None
        for _ in range(60):
            target = await pg.evaluate("""() => { const t = [...document.querySelectorAll('.search-item')];
                return t.length ? t.map(e => getComputedStyle(e).backgroundColor) : null; }""")
            if target: break
            await pg.wait_for_timeout(80)
        print("Suchtest items use the blue target colour:", bool(target) and "rgb(21, 101, 192)" in target)

        # ---- Corsi / Reaktionsfeld / Antizip / Stopp / AB rules ----
        await pg.evaluate("""() => localStorage.setItem('fwmc-signal-colors-v1', JSON.stringify({corsi:{lit:'rot'},reakt:{light:'blau'},antizip:{ball:'pink'},stop:{signal:'lila'},ab:{t1:'gelb'}}))""")
        await pg.reload(); await pg.wait_for_timeout(300)
        res = await pg.evaluate("""() => {
            const mk = (cls, tag) => { const d = document.createElement(tag || 'div'); d.className = cls; document.body.appendChild(d); const s = getComputedStyle(d); const o = {bg: s.backgroundColor, bgi: s.backgroundImage, border: s.borderTopColor, color: s.color}; d.remove(); return o; };
            return { corsi: mk('corsi-block lit'), reakt: mk('reakt-light', 'button'), ball: mk('antizip-ball'), stop: mk('stop-arrow stop-signal'), ab: mk('ab-stream-char is-t1') };
        }""")
        print("Corsi lit border red:", res["corsi"]["border"] == "rgb(211, 47, 47)", res["corsi"])
        print("Reakt light gradient blue:", "21, 101, 192" in res["reakt"]["bgi"])
        print("Antizip ball pink:", res["ball"]["bg"] == "rgb(230, 57, 155)")
        print("Stop signal lila:", res["stop"]["color"] == "rgb(126, 79, 190)")
        print("AB T1 yellow:", res["ab"]["color"] == "rgb(242, 169, 0)")
        print("Stop text says LILA:", await pg.inner_text('#stopReady [data-sig="stop.signal"]') == "LILA")
        print("AB question says GELB:", "GELB" in await pg.text_content("#abReady .page-sub"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
