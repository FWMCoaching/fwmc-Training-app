import asyncio, json, math
from playwright.async_api import async_playwright

# Paket 2026-10-05 (Fabian: "1. 2. 4."): Startbild mit Logo, App-Symbol +
# einmaliger Hinweis "Zum Startbildschirm hinzufügen" auf Heute, und Größe
# + Farbe der Zahlen/Zeichen in Positionen merken, Flash-Speicher-Test, MOT
# (ready screens, persisted, played, Cardio guest panel).
BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

async def new_page(b, init, errors, vw=390, vh=844):
    ctx = await b.new_context(viewport={"width": vw, "height": vh}, service_workers="block")
    await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));" + init)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    return ctx, pg

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---- 1. Startbild ----
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-test-splash','true')", errors)
        await pg.goto(BASE)
        check("splash visible right after opening", await pg.is_visible("#appSplash"))
        bg = await pg.evaluate("getComputedStyle(document.getElementById('appSplash')).backgroundColor")
        check("splash is brand teal", bg == "rgb(0, 112, 148)", bg)
        check("splash logo loaded", await pg.evaluate("(() => { const i = document.querySelector('#appSplash img'); return i.complete && i.naturalWidth > 0; })()"))
        await pg.wait_for_timeout(1500)
        check("splash gone after start", await pg.locator("#appSplash").count() == 0)
        await ctx.close()
        ctx, pg = await new_page(b, "", errors)
        await pg.goto(BASE); await pg.wait_for_timeout(200)
        check("no splash in automated runs without opt-in", await pg.locator("#appSplash").count() == 0)
        man = await pg.evaluate("fetch('manifest.json').then(r => r.json())")
        check("manifest background is brand teal", man["background_color"] == "#007094")
        links = await pg.evaluate("[...document.querySelectorAll('link[rel=apple-touch-startup-image]')].map(l => l.href)")
        check("iOS startup images linked", len(links) >= 15, len(links))
        codes = await pg.evaluate("Promise.all([...document.querySelectorAll('link[rel=apple-touch-startup-image]')].map(l => fetch(l.href).then(r => r.status)))")
        check("every startup image exists", all(c == 200 for c in codes), codes)
        check("app icon linked", await pg.evaluate("!!document.querySelector('link[rel=apple-touch-icon]')"))
        check("install hint hidden on desktop/automation", not await pg.is_visible("#installHint"))
        await ctx.close()

        # ---- 2. Hinweis Startbildschirm ----
        ctx, pg = await new_page(b, "if (!localStorage.getItem('fwmc-install-hint-dismissed')) localStorage.setItem('fwmc-test-install', JSON.stringify('ios'))", errors)
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        check("install hint visible on Heute (iOS)", await pg.is_visible("#todayHome #installHint"))
        txt = await pg.inner_text("#installHintText")
        check("iOS text names Teilen and Home-Bildschirm", "Teilen" in txt and "Home-Bildschirm" in txt, txt)
        check("no install button on iOS", not await pg.is_visible("#installHintAddBtn"))
        box = await pg.locator("#installHintCloseBtn").bounding_box()
        check("close link is a 44 px tap target", box and box["height"] >= 44, box)
        await pg.click("#installHintCloseBtn"); await pg.wait_for_timeout(100)
        check("install hint gone after 'Nicht mehr anzeigen'", not await pg.is_visible("#installHint"))
        await pg.evaluate("localStorage.setItem('fwmc-test-install', JSON.stringify('ios'))")
        await pg.reload(); await pg.wait_for_timeout(300)
        check("install hint stays gone after reload", not await pg.is_visible("#installHint"))
        await ctx.close()
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-test-install', JSON.stringify('android'))", errors)
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        txt = await pg.inner_text("#installHintText")
        check("Android text names the browser menu", "Browser-Menü" in txt, txt)
        await ctx.close()

        # ---- 3. Positionen merken ----
        ctx, pg = await new_page(b, "", errors)
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        await pg.click('[data-nat-sub="remember"]'); await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(200)
        await pg.click("#rememberAdvanced summary")
        size = pg.locator('#rememberReady [data-look-size="remember"] input[type=range]')
        check("Remember: size slider in Feineinstellungen", await size.is_visible())
        check("Remember: size label", "Größe der Kreise" in await pg.inner_text('#rememberReady [data-look-size="remember"]'))
        check("Remember: colour picker", await pg.locator('#rememberReady [data-look-color="remember"] .color-swatch').count() >= 8)
        await size.evaluate("(e) => { e.value = '1.5'; e.dispatchEvent(new Event('input', {bubbles:true})); }")
        await pg.click('#rememberReady [data-look-color="remember"] .color-swatch[data-key="schwarz"]')
        hint_hidden_black = await pg.is_hidden('#rememberReady [data-look-color="remember"] .look-contrast-hint')
        await pg.click('#rememberReady [data-look-color="remember"] .color-swatch[data-key="weiss"]')
        check("Remember: no contrast hint for white", await pg.is_hidden('#rememberReady [data-look-color="remember"] .look-contrast-hint'))
        low = None
        for key in await pg.eval_on_selector_all('#rememberReady [data-look-color="remember"] .color-swatch', "els => els.map(e => e.dataset.key)"):
            await pg.click(f'#rememberReady [data-look-color="remember"] .color-swatch[data-key="{key}"]')
            if await pg.is_visible('#rememberReady [data-look-color="remember"] .look-contrast-hint'):
                low = key; break
        check("Remember: contrast hint for a colour close to the circle", low is not None, low)
        await pg.click('#rememberReady [data-look-color="remember"] .color-swatch[data-key="schwarz"]')
        saved = json.loads(await pg.evaluate("localStorage.getItem('fwmc-remember-prefs-v1')"))
        check("Remember: saved", saved.get("markerScale") == 1.5 and saved.get("numColor") == "schwarz", saved)
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('[data-nat-sub="remember"]'); await pg.click("#rememberOpenTraining"); await pg.wait_for_timeout(200)
        await pg.click("#rememberTrainingAdvanced summary")
        v = await pg.locator('#rememberTrainingReady [data-look-size="remember"] input').input_value()
        check("Remember: training screen shows the saved size", v == "1.5", v)
        await pg.click('[data-nat-sub="remember"]') if await pg.is_visible('[data-nat-sub="remember"]') else None
        await pg.click("#rememberTrainingStartBtn"); await pg.wait_for_timeout(400)
        px = await pg.evaluate("parseFloat(getComputedStyle(document.getElementById('rememberStage')).getPropertyValue('--remember-marker-px'))")
        check("Remember: circles bigger than before (72 px), capped to fit", 72 < px <= 108, px)
        col = await pg.evaluate("getComputedStyle(document.querySelector('.remember-marker')).color")
        check("Remember: number colour applied", col == "rgb(0, 0, 0)", col)
        await ctx.close()

        # ---- 4. Flash ----
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-flash-prefs-v1', JSON.stringify({charScale:2, charColor:'rot', fixEnabled:false, stimulusS:2}))", errors)
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        await pg.click('[data-nat-sub="flash"]'); await pg.click("#flashOpenConstant"); await pg.wait_for_timeout(200)
        await pg.click("#flashAdvanced summary")
        check("Flash: size slider shows saved 2.0", await pg.locator('#flashReady [data-look-size="flash"] input').input_value() == "2")
        check("Flash: colour label", "Farbe der Zeichen" in await pg.inner_text('#flashReady [data-look-color="flash"]'))
        await pg.click("#flashReadyStartBtn")
        await pg.wait_for_selector("#flashDigit:not([hidden])", timeout=5000) if await pg.locator("#flashDigit").count() else None
        info = await pg.evaluate("""(() => { const d = document.querySelector('.flash-digit:not([hidden])'); const s = document.getElementById('flashStage').getBoundingClientRect();
            if (!d) return null; const r = d.getBoundingClientRect(); const cs = getComputedStyle(d);
            return {fs: parseFloat(cs.fontSize), color: cs.color, inside: r.left >= s.left - 1 && r.right <= s.right + 1, cap: Math.min(s.width, s.height) * 0.3}; })()""")
        check("Flash: character bigger than 64 px but capped", info and 64 < info["fs"] <= info["cap"] + 1, info)
        check("Flash: character colour applied", info and info["color"] != "rgb(22, 35, 42)", info)
        check("Flash: character fully inside the stage", info and info["inside"], info)
        await ctx.close()

        # ---- 5. MOT ----
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-mot-prefs-v1', JSON.stringify({objScale:1.5, objectCount:12, targetCount:4}))", errors, 375, 667)
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        await pg.click('[data-nat-sub="mot"]'); await pg.click("#motOpenSpeed"); await pg.wait_for_timeout(200)
        await pg.click("#motAdvanced summary")
        check("MOT: size slider, no colour picker", await pg.locator('#motReady [data-look-size="mot"] input').is_visible() and await pg.locator('#motReady [data-look-color]').count() == 0)
        check("MOT: slider never below 1.0 (tap size)", await pg.locator('#motReady [data-look-size="mot"] input').get_attribute("min") == "1")
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(500)
        objs = await pg.evaluate("[...document.querySelectorAll('.mot-object')].map(e => { const r = e.getBoundingClientRect(); return [r.left + r.width/2, r.top + r.height/2, r.width]; })")
        w = objs[0][2] if objs else 0
        check("MOT: 12 objects bigger than 44 px", len(objs) == 12 and 44 < w <= 66, (len(objs), w))
        mind = min(math.hypot(a[0]-c[0], a[1]-c[1]) for i, a in enumerate(objs) for c in objs[i+1:]) if len(objs) > 1 else 0
        check("MOT: objects do not overlap", mind >= w, round(mind, 1))
        await ctx.close()

        # ---- 6. Cardio guest parity ----
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-cardio-addon-v1', JSON.stringify({enabled:true, pool:['remember','flash','mot']}))", errors)
        await pg.goto(BASE + "?bereich=cardio"); await pg.wait_for_timeout(300)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        html = await pg.evaluate("document.getElementById('cardioAddonPerType').innerHTML")
        check("Cardio guest: Remember size + colour", 'data-f="markerScale"' in html and 'data-lookfield="numColor"' in html)
        check("Cardio guest: Flash size + colour", 'data-f="charScale"' in html and 'data-lookfield="charColor"' in html)
        check("Cardio guest: MOT size", 'data-f="objScale"' in html)
        await ctx.close()
        await b.close()
    check("no page errors", not errors, errors[:3])
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
