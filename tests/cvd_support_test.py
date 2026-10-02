import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Farbschwäche-Unterstützung (2026-10-02): ticking any Farbsehen option in
# Master-Einstellungen turns on, for every exercise, (a) a tick/cross badge
# on right/wrong feedback (body.fbs-<ex>) and (b) colour-safe replacement
# colours where an exercise has a fixed colour pair/palette (body.cvdp-<ex>).
# Each exercise's own Feineinstellungen can switch either one on/off
# independently (stored as an override in fwmc-cvd-overrides-v1), with a
# link back to "follow Master" and a global reset in Master-Einstellungen.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked', 'true'); localStorage.setItem('fwmc-tips-seen', 'true')")
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def body_has(cls):
            return await pg.evaluate(f"() => document.body.classList.contains('{cls}')")

        async def open_test(prefix):
            await pg.goto(URL); await pg.wait_for_timeout(300)
            await pg.click('#home .section-tab[data-section="test"]'); await pg.wait_for_timeout(120)
            await pg.click(f"#{prefix}OpenBtn"); await pg.wait_for_timeout(150)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        print("controls injected into ready screens (26 exercises + 2 training screens):", await pg.locator(".cvd-group").count() == 28)
        print("off by default (no Master selection):", not await body_has("fbs-flanker") and not await body_has("cvdp-gng"))

        # --- Master switches everything on ---
        await pg.click("#home .master-settings-btn"); await pg.wait_for_timeout(150)
        await pg.click('[data-master-cvd="blaugelb"]'); await pg.wait_for_timeout(80)
        print("Master Blau-Gelb turns on feedback symbols + safe colours:", await body_has("fbs-flanker") and await body_has("fbs-remember") and await body_has("cvdp-gng") and await body_has("cvdp-stroop"))
        print("no reset button while no exercise has its own setting:", await pg.is_hidden("#masterCvdResetBtn"))

        # --- Per-exercise override in Flanker ---
        await open_test("flanker")
        await pg.click("#flankerAdvanced summary"); await pg.wait_for_timeout(80)
        grp = '#flankerReady .cvd-group'
        print("Flanker shows only the symbol switch (no fixed palette):", await pg.locator(f"{grp} [data-cvd-kind='fb']").count() == 2 and await pg.locator(f"{grp} [data-cvd-kind='pal']").count() == 0)
        print("'An' active, following Master:", "active" in (await pg.get_attribute(f"{grp} [data-cvd-val='1']", "class") or "") and "Grundeinstellungen" in await pg.inner_text(f"{grp} .cvd-status"))

        # Badge appears on real feedback
        await pg.click("#flankerReadyStartBtn"); await pg.wait_for_timeout(200)
        for _ in range(120):
            if await pg.locator(".flanker-arrow").count() == 5: break
            await pg.wait_for_timeout(25)
        await pg.click("#flankerLeftBtn"); await pg.wait_for_timeout(60)
        img = await pg.evaluate("() => { const b = document.querySelector('.flanker-response-btn.correct, .flanker-response-btn.wrong'); return b ? getComputedStyle(b).backgroundImage : ''; }")
        print("tapped button shows a tick/cross badge:", "svg" in img)
        await pg.click("#flankerBackBtn"); await pg.wait_for_timeout(200)

        await open_test("flanker")
        await pg.click("#flankerAdvanced summary"); await pg.wait_for_timeout(80)
        await pg.click(f"{grp} [data-cvd-val='0']"); await pg.wait_for_timeout(80)
        print("switching off in Flanker removes only Flanker's symbols:", not await body_has("fbs-flanker") and await body_has("fbs-simon"))
        print("status now offers 'follow Master' again:", await pg.locator(f"{grp} [data-cvd-reset]").count() == 1)
        stored = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cvd-overrides-v1'))")
        print("override persisted:", stored == {"flanker": {"fb": False}})
        await pg.reload(); await pg.wait_for_timeout(300)
        print("override survives reload:", not await body_has("fbs-flanker") and await body_has("fbs-hick"))

        # Opposite direction: an exercise can be ON while Master is off
        await open_test("gng")
        await pg.click("#gngAdvanced summary"); await pg.wait_for_timeout(80)
        await pg.click("#gngReady .cvd-group [data-cvd-kind='pal'][data-cvd-val='0']"); await pg.wait_for_timeout(60)
        print("GNG safe colours off, text back to grün:", not await body_has("cvdp-gng") and (await pg.inner_text('#gngReady .page-sub [data-sig="gng.go"]')) == "grün")
        await pg.click("#gngReady .cvd-group [data-cvd-kind='pal'][data-cvd-val='1']"); await pg.wait_for_timeout(60)
        print("GNG instruction text says blau when safe colours are on:", (await pg.inner_text('#gngReady .page-sub [data-sig="gng.go"]')) == "blau")
        await pg.click("#gngReadyStartBtn"); await pg.wait_for_timeout(150)
        colour = ""
        for _ in range(200):
            cls = await pg.get_attribute("#gngStimulus", "class") or ""
            if "go" in cls.split() or "nogo" in cls.split():
                await pg.wait_for_timeout(250)  # let the colour transition settle
                colour = await pg.eval_on_selector("#gngStimulus", "el => getComputedStyle(el).backgroundColor"); break
            await pg.wait_for_timeout(25)
        print("GNG stimulus uses dark blue / amber:", colour in ("rgb(11, 61, 145)", "rgb(245, 163, 0)"), colour)

        # Stroop: safe word set
        await open_test("stroop")
        await pg.click("#stroopReadyStartBtn"); await pg.wait_for_timeout(150)
        word = ""
        for _ in range(200):
            word = (await pg.inner_text("#stroopWord")).strip()
            if word: break
            await pg.wait_for_timeout(25)
        print("Stroop shows the safe colour words:", word in ("SCHWARZ", "BLAU", "ORANGE", "GELB"), word)
        print("Stroop buttons relabelled:", await pg.get_attribute('[data-stroop-color="gruen"]', "aria-label") == "Orange")

        # Suchtest cue
        await open_test("search")
        await pg.click("#searchReadyStartBtn"); await pg.wait_for_timeout(150)
        hint = ""
        for _ in range(200):
            hint = await pg.inner_text("#searchHint")
            if "Ziel" in hint: break
            await pg.wait_for_timeout(25)
        print("Suchtest cue names the blue target:", "Blau" in hint, hint)

        # Kartensortier-Test reference cards
        await open_test("wcst")
        c = await pg.eval_on_selector('.wcst-ref[data-ref-idx="0"] .wcst-shape', "el => getComputedStyle(el).color")
        print("WCST reference card 1 recoloured:", c == "rgb(22, 35, 42)", c)
        print("WCST got its own Feineinstellungen with the switches:", await pg.locator("#wcstReady details.advanced .cvd-group [data-cvd-kind='pal']").count() == 2)

        # Master reset clears every exercise's own setting
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click("#home .master-settings-btn"); await pg.wait_for_timeout(150)
        print("reset button shown once overrides exist:", await pg.is_visible("#masterCvdResetBtn"))
        pg.once("dialog", lambda d: asyncio.ensure_future(d.accept()))
        await pg.click("#masterCvdResetBtn"); await pg.wait_for_timeout(120)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(120)
        print("reset: Flanker follows Master again:", await body_has("fbs-flanker") and await pg.evaluate("() => localStorage.getItem('fwmc-cvd-overrides-v1')") == "{}")
        await pg.click('[data-master-cvd="blaugelb"]'); await pg.wait_for_timeout(80)
        print("Master off: everything off again:", not await body_has("fbs-flanker") and not await body_has("cvdp-gng"))

        print("no page/console errors:", not errors, errors[:3])
        await b.close()

asyncio.run(main())
