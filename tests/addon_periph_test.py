import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# "Zusatzaufgabe": lets a VT-canvas exercise (e.g. "4 Pfeile gerade") run
# Periphere Wahrnehmung's own peripheral-flash mechanic as an add-on during
# its own "Reiz" (any non-blank frame) and/or "Pause" (blank frame) phases.
# Unlike every other per-domain setting so far, this one is genuinely
# per-exercise: "4-straight" and "4-diag" each carry their own on/off +
# config, stored in localStorage under fwmc-addon-v1 keyed by exercise id -
# not in the flat shared `state` prefs blob every other setting uses.
# Zero phases selected is this control's valid "off" state (unlike every
# other multi-select in the app, where zero-selected is an error).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def open_card(exercise_id):
            if await pg.is_visible("#backToHome"):
                await pg.click("#backToHome"); await pg.wait_for_timeout(100)
            await pg.click('#home .section-tab[data-section="visual"]'); await pg.wait_for_timeout(150)
            await pg.click(f'.excard[data-exercise="{exercise_id}"]'); await pg.wait_for_timeout(150)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # --- off by default, hidden config body, group visible for a normal VT exercise ---
        await open_card("4-straight")
        print("addon group visible for '4 Pfeile gerade':", await pg.is_visible("#addonGroup"))
        print("config body hidden while off (no phase selected):", await pg.is_hidden("#addonConfigBody"))
        print("off hint shown:", (await pg.inner_text("#addonPhaseHint")).startswith("Aus"))
        print("start button NOT disabled just because the add-on is off:", not await pg.is_disabled("#startBtn"))

        # --- addon group hidden entirely for Hütchen sortieren (no schedule to hook into) ---
        await open_card("cone-tap")
        print("addon group hidden for Hütchen sortieren:", await pg.is_hidden("#addonGroup"))
        await pg.click("#backToHome"); await pg.wait_for_timeout(100)

        # --- back to 4-straight: phase multiselect + "Beide" shortcut ---
        await open_card("4-straight")
        await pg.click('#addonPhaseRow [data-addon-phase="reiz"]'); await pg.wait_for_timeout(80)
        print("config body visible once a phase is picked:", await pg.is_visible("#addonConfigBody"))
        print("hint cleared once enabled:", (await pg.inner_text("#addonPhaseHint")) == "")
        print("mode defaults to übernehmen:", "active" in (await pg.get_attribute('[data-addon-mode="uebernehmen"]', "class") or ""))
        print("own body hidden by default:", await pg.is_hidden("#addonOwnBody"))

        await pg.click('#addonPhaseAllBtn'); await pg.wait_for_timeout(80)
        reiz_active = "active" in (await pg.get_attribute('[data-addon-phase="reiz"]', "class") or "")
        pause_active = "active" in (await pg.get_attribute('[data-addon-phase="pause"]', "class") or "")
        print("'Beide' turns both phases on:", reiz_active and pause_active)
        await pg.click('#addonPhaseAllBtn'); await pg.wait_for_timeout(80)
        print("clicking 'Beide' again turns everything off:", await pg.is_hidden("#addonConfigBody"))

        # --- eigen (own) Feineinstellung: kind/Bereich/Größe/timing ---
        await pg.click('#addonPhaseRow [data-addon-phase="pause"]'); await pg.wait_for_timeout(80)
        await pg.click('[data-addon-mode="eigen"]'); await pg.wait_for_timeout(80)
        print("own body visible in eigen mode:", await pg.is_visible("#addonOwnBody"))
        print("own defaults: gemischt / all axes / gleich:",
              "active" in (await pg.get_attribute('[data-addon-kind="gemischt"]', "class") or "") and
              "active" in (await pg.get_attribute('#addonAllBtn', "class") or "") and
              "active" in (await pg.get_attribute('[data-addon-size="gleich"]', "class") or ""))

        await pg.click('[data-addon-kind="zahlen"]'); await pg.wait_for_timeout(60)
        await pg.click('#addonZonesBtn'); await pg.wait_for_timeout(60)
        # All 8 zones start selected (same default as Periph's own Bereich) -
        # deselect everything except tl/br to narrow down to exactly those two.
        for z in ["tm", "tr", "ml", "mr", "bl", "bm"]:
            await pg.click(f'#addonZoneGrid [data-zone="{z}"]'); await pg.wait_for_timeout(30)
        await pg.click('[data-addon-size="wachsend"]'); await pg.wait_for_timeout(60)
        await pg.fill("#addonStimulusSlider", "0.6"); await pg.dispatch_event("#addonStimulusSlider", "input")
        await pg.fill("#addonIntervalMinSlider", "1.5"); await pg.dispatch_event("#addonIntervalMinSlider", "input")
        await pg.fill("#addonIntervalMaxSlider", "3.5"); await pg.dispatch_event("#addonIntervalMaxSlider", "input")
        await pg.wait_for_timeout(80)

        store = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-addon-v1')||'{}')")
        entry = store.get("4-straight", {})
        print("stored under the exercise's own id:", entry.get("phases") == ["pause"] and entry.get("mode") == "eigen")
        own = entry.get("own", {})
        print("own config persisted (kind/zones/size/timing):",
              own.get("kind") == "zahlen" and own.get("useZones") is True and
              set(own.get("zones", [])) == {"tl", "br"} and own.get("sizeMode") == "wachsend" and
              abs(own.get("stimulusS", 0) - 0.6) < 0.01 and
              abs(own.get("intervalMin", 0) - 1.5) < 0.01 and abs(own.get("intervalMax", 0) - 3.5) < 0.01)

        # --- save as a named, exercise-agnostic preset ---
        await pg.click("#addonSaveBtn"); await pg.wait_for_timeout(80)
        await pg.fill("#addonSaveNameInput", "Nur Ecken, Zahlen")
        await pg.click("#addonSaveConfirmBtn"); await pg.wait_for_timeout(80)
        print("preset saved and listed:", await pg.locator("#addonPresetList .bundle-item").count() == 1)

        # --- a different exercise starts with its own, independent (off) config ---
        await pg.click("#backToHome"); await pg.wait_for_timeout(100)
        await open_card("4-diag")
        print("a different exercise's add-on starts off:", await pg.is_hidden("#addonConfigBody"))

        # apply the preset saved from "4-straight" here, on "4-diag"
        await pg.click('#addonPhaseRow [data-addon-phase="reiz"]'); await pg.wait_for_timeout(60)
        await pg.click('[data-addon-mode="eigen"]'); await pg.wait_for_timeout(60)
        print("preset list also offered here (not exercise-scoped):", await pg.locator("#addonPresetList .bundle-item").count() == 1)
        await pg.click("#addonPresetList .bundle-item"); await pg.wait_for_timeout(80)
        print("applying the preset loads its kind (zahlen) here:", "active" in (await pg.get_attribute('[data-addon-kind="zahlen"]', "class") or ""))

        store2 = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-addon-v1')||'{}')")
        print("4-straight's own entry is untouched by 4-diag's changes:",
              store2.get("4-straight", {}).get("own", {}).get("kind") == "zahlen" and
              store2.get("4-diag", {}).get("phases") == ["reiz"])

        # --- going back to 4-straight still shows its own saved config ---
        await pg.click("#backToHome"); await pg.wait_for_timeout(100)
        await open_card("4-straight")
        print("4-straight's phase/mode/kind survived the round trip:",
              "active" in (await pg.get_attribute('[data-addon-phase="pause"]', "class") or "") and
              "active" in (await pg.get_attribute('[data-addon-mode="eigen"]', "class") or "") and
              "active" in (await pg.get_attribute('[data-addon-kind="zahlen"]', "class") or ""))

        # --- runtime: the add-on overlay runs alongside the host exercise without
        # crashing (no internal session/schedule hook exists to inspect from
        # outside, so this is a smoke check - the config-storage assertions
        # above already cover buildAddonSchedule()'s inputs end to end). ---
        await pg.click("#startBtn"); await pg.wait_for_timeout(2500)
        print("exercise runs with the add-on active, no crash:", await pg.is_visible("#player"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(150)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
