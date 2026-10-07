"""Hütchen · Farbe + Zahl (Fabian 07.10.2026, Idee H): 3-6 numbered fields,
a coloured cup on each; the screen shows a colour with a big number.
Ready screen (Anzahl Felder, colours capped at the field count, Hilfsmittel),
presets, Kombi capture/edit/playback, Cardio guest, Wochenplan option.
Run from tests/ with a dev server on :8845."""
import asyncio, json, os
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
SHOTS = "screenshots/nacht2_1007"
CARD = '.excard[data-exercise="cone-number"]'
COLOR_HEX = {"rot": "#d32f2f", "gelb": "#f2a900", "gruen": "#2e7d32", "blau": "#1565c0", "orange": "#ff9110", "lila": "#7e4fbe", "pink": "#e6399b"}

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


async def st(pg):
    return await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}')")


async def pick_colors(pg, keys):
    """Select exactly `keys` in the VT colour picker."""
    for _ in range(2):
        cur = (await st(pg)).get("colors", [])
        for k in keys:
            if k not in cur:
                await pg.click(f'#colorPicker .color-swatch[data-color="{k}"]'); await pg.wait_for_timeout(60)
        cur = (await st(pg)).get("colors", [])
        for k in cur:
            if k not in keys:
                await pg.click(f'#colorPicker .color-swatch[data-color="{k}"]'); await pg.wait_for_timeout(60)


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
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- card + ready screen ----
        check("card on the VT home next to the other Hütchen", await pg.is_visible(CARD) and await pg.evaluate(
            "() => { const c = [...document.querySelectorAll('#home .excard')].map(e => e.dataset.exercise); return c.indexOf('cone-number') === c.indexOf('cone-compass') + 1; }"))
        await pg.click(CARD); await pg.wait_for_timeout(250)
        check("ready screen opens", (await pg.inner_text("#readyTitle")).strip() == "Hütchen · Farbe + Zahl")
        check("Hilfsmittel note", await pg.is_visible("#hilfsmittelNote") and "nummerierte Felder" in await pg.inner_text("#hilfsmittelNote"))
        check("Anzahl Felder shown, default 4", await pg.is_visible("#cnFieldsGroup") and "active" in (await pg.get_attribute('[data-cn-fields="4"]', "class")))
        check("background picker offered (Feineinstellungen)", await pg.evaluate("() => !document.getElementById('bgGroup').hidden && !document.getElementById('advanced').hidden"))
        check("Zusatzaufgabe offered", await pg.is_visible("#addonGroup"))
        check("start button reads Training starten", (await pg.inner_text("#startBtn")).strip() == "Training starten")
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="cone-compass"]'); await pg.wait_for_timeout(200)
        check("sibling has no Felder row / note", not await pg.is_visible("#cnFieldsGroup") and not await pg.is_visible("#hilfsmittelNote"))
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)

        # ---- colours capped at the field count ----
        await pg.click(CARD); await pg.wait_for_timeout(200)
        await pg.click('[data-cn-fields="6"]'); await pg.wait_for_timeout(80)
        await pick_colors(pg, ["rot", "gelb", "gruen", "blau", "orange", "lila"])
        check("6 fields: 6 colours possible", len((await st(pg))["colors"]) == 6, (await st(pg))["colors"])
        await pg.click('#colorPicker .color-swatch[data-color="pink"]'); await pg.wait_for_timeout(80)
        check("7th colour blocked at 6 fields", len((await st(pg))["colors"]) == 6)
        await pg.click('[data-cn-fields="3"]'); await pg.wait_for_timeout(80)
        s = await st(pg)
        check("3 fields: colours trimmed to 3", s["cnFields"] == 3 and len(s["colors"]) == 3, s["colors"])
        await pg.click('#colorPicker .color-swatch[data-color="pink"]'); await pg.wait_for_timeout(80)
        check("4th colour blocked at 3 fields", len((await st(pg))["colors"]) == 3)
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); s.cnFields = 99; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click(CARD); await pg.wait_for_timeout(200)
        check("broken field count falls back to 4", "active" in (await pg.get_attribute('[data-cn-fields="4"]', "class")))
        await pg.click('[data-cn-fields="5"]'); await pg.wait_for_timeout(80)
        await pick_colors(pg, ["rot", "gelb", "blau"])
        # fast tempo for sampling the stimuli below
        await pg.evaluate("() => { const s = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); Object.assign(s, {stimulusS: 0.5, intervalMin: 0.5, intervalMax: 0.5}); localStorage.setItem('fwmc-webapp-v3', JSON.stringify(s)); }")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click(CARD); await pg.wait_for_timeout(200)
        check("Felder persist across reload", "active" in (await pg.get_attribute('[data-cn-fields="5"]', "class")))

        # ---- schedule: only chosen colours, numbers 1..N, no pair twice in a row ----
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        seen = []
        for i in range(30):
            await pg.wait_for_timeout(150)
            last = await pg.evaluate("() => window.__cnLast")
            g = await pg.evaluate("() => window.__cnLastGeom")
            if last and (not seen or seen[-1] != last): seen.append(last)
            if g and not (g["top"] >= g["barBottom"] and g["bottom"] <= g["stageBottom"] + 0.5): check("disc below the bar, inside the stage", False, g)
        allowed = {COLOR_HEX[k] for k in ["rot", "gelb", "blau"]}
        check("stimuli drawn", len(seen) >= 4, len(seen))
        for n in (3, 6):
            res = await pg.evaluate("""(n) => { const fr = window.__cn.build({cnFields: n, duration: 600, stimulusS: 0.5, intervalMin: 0.5, intervalMax: 0.5}, ['rot','gelb']).filter(f => f.kind === 'colornum');
                return { n: fr.length, nums: [...new Set(fr.map(f => f.payload.num))].sort(), norep: fr.every((f, i) => !i || f.payload.num !== fr[i-1].payload.num || f.payload.color !== fr[i-1].payload.color) }; }""", n)
            check(f"{n} fields: numbers exactly 1..{n}, no pair twice in a row", res["nums"] == list(range(1, n + 1)) and res["norep"] and res["n"] > 100, res["nums"])
        check("only chosen colours, numbers 1..5", all(x["color"] in allowed and 1 <= x["num"] <= 5 for x in seen), seen)
        await pg.screenshot(path=f"{SHOTS}/cn_player_light.png")
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)

        check("number ink is white or dark (fixed hex)", all(x["ink"] in ("#ffffff", "#16232a") for x in seen))

        # ---- preset carries Felder ----
        await pg.click("#vtSaveBtn"); await pg.fill("#vtSaveNameInput", "Fünf Felder"); await pg.click("#vtSaveConfirmBtn"); await pg.wait_for_timeout(150)
        vt = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-vt-saved-v1') || '[]')")
        check("preset stores Felder", vt and vt[-1].get("cn", {}).get("cnFields") == 5 and vt[-1]["exercise"] == "cone-number", vt[-1] if vt else None)
        check("preset meta names Felder", "5 Felder" in await pg.inner_text("#vtSavedList"))
        await pg.click('[data-cn-fields="3"]'); await pg.wait_for_timeout(80)
        await pg.click('#vtSavedList .bundle-item:has-text("Fünf Felder")'); await pg.wait_for_timeout(400)
        check("preset tap restores Felder + starts", (await st(pg))["cnFields"] == 5 and await pg.is_visible("#player"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)

        # ---- Kombi capture/edit/playback, standalone untouched ----
        before = (await st(pg))["cnFields"]
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(250)
        await pg.click('#comboAddGrid .combo-add-btn:has-text("Farbe + Zahl")'); await pg.wait_for_timeout(250)
        check("Kombi: capture opens the ready screen", "Baustein: Hütchen · Farbe + Zahl" in await pg.inner_text("#readyTitle") and (await pg.inner_text("#startBtn")).strip() == "Baustein übernehmen")
        await pg.click('[data-cn-fields="6"]'); await pg.wait_for_timeout(80)
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        check("Kombi: block added", await pg.is_visible("#comboScreen") and "Farbe + Zahl" in await pg.inner_text("#comboBlockList"))
        check("Kombi: standalone Felder unchanged", (await st(pg))["cnFields"] == before, ((await st(pg))["cnFields"], before))
        await pg.click("#comboBlockList .chapter-main"); await pg.wait_for_timeout(250)
        check("Kombi: block re-editable with its own Felder", "active" in (await pg.get_attribute('[data-cn-fields="6"]', "class")))
        await pg.click("#startBtn"); await pg.wait_for_timeout(250)
        await pg.evaluate("() => { window.__cnLast = null; }")
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(2500)
        last = await pg.evaluate("() => window.__cnLast")
        check("Kombi: block plays on the canvas", await pg.is_visible("#player") and last is not None, last)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        check("Kombi run leaves standalone Felder alone", (await st(pg))["cnFields"] == before)

        # ---- Wochenplan: offered as a plan target ----
        opts = await pg.evaluate("() => [...document.querySelectorAll('#home .excard[data-exercise]')].map(c => c.dataset.exercise)")
        check("Wochenplan source lists it", "cone-number" in opts)

        # ---- Cardio guest ----
        await pg.goto("http://localhost:8845/index.html?bereich=cardio"); await pg.wait_for_timeout(400)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        check("Cardio: in the Zusatzaufgaben pool", await pg.locator('#cardioAddonPoolGrid [data-pool="cone-number"]').count() == 1)
        await pg.check('#cardioAddonPoolGrid [data-pool="cone-number"]'); await pg.wait_for_timeout(150)
        check("Cardio: own Felder field", await pg.locator('#cardioAddonPerType input[data-type="cone-number"][data-f="fields"]').count() == 1)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(100)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddonPickerTypeRow .choice:has-text("Farbe + Zahl")'); await pg.wait_for_timeout(120)
        await pg.fill('#cardioAddonPickerDetail input[data-f="fields"]', "3")
        await pg.dispatch_event('#cardioAddonPickerDetail input[data-f="fields"]', "input")
        await pg.evaluate("() => { window.__cnLast = null; }")
        await pg.click("#cardioAddonPickerStartBtn")
        nums = set()
        for i in range(8):
            await pg.wait_for_timeout(400)
            l = await pg.evaluate("() => window.__cnLast")
            if l: nums.add(l["num"])
        check("Cardio: guest runs Farbe + Zahl with its own Felder", await pg.is_visible("#player") and nums and max(nums) <= 3, nums)
        own = await st(pg)
        check("Cardio guest leaves standalone Felder alone", own["cnFields"] == before, own["cnFields"])
        await pg.screenshot(path=f"{SHOTS}/cn_cardio_guest_light.png")

        # ---- screenshots light/dark: ready screen next to its sibling ----
        for scheme in ("light", "dark"):
            c2 = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", color_scheme=scheme)
            await c2.add_init_script(INIT)
            p2 = await c2.new_page()
            await p2.goto(URL); await p2.wait_for_timeout(400)
            await p2.evaluate("() => document.querySelector('.excard[data-exercise=\"cone-compass\"]').scrollIntoView({block:'center'})")
            await p2.screenshot(path=f"{SHOTS}/cn_home_{scheme}.png")
            await p2.click(CARD); await p2.wait_for_timeout(250)
            await p2.screenshot(path=f"{SHOTS}/cn_ready_{scheme}.png", full_page=True)
            await p2.click("#backToHome"); await p2.wait_for_timeout(150)
            await p2.click('.excard[data-exercise="cone-compass"]'); await p2.wait_for_timeout(250)
            await p2.screenshot(path=f"{SHOTS}/cn_sibling_compass_{scheme}.png", full_page=True)
            await p2.click("#backToHome"); await p2.wait_for_timeout(150)
            await p2.click(CARD); await p2.wait_for_timeout(250)
            await p2.click("#startBtn"); await p2.wait_for_timeout(1200)
            await p2.screenshot(path=f"{SHOTS}/cn_player_{scheme}.png")
            await c2.close()
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
