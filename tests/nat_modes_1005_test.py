import asyncio, json
from playwright.async_api import async_playwright

# NAT wie Visual Training (Fabian, 2026-10-05): keine zweite Reiterleiste,
# die fünf Übungen als Kacheln, Varianten als "Modus" auf der Übungsseite.
BASE = "http://localhost:8845/index.html?bereich=nat"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

async def visible_title(pg):
    return await pg.evaluate("() => { const s = [...document.querySelectorAll('.screen')].find(x => !x.hidden); const h = s && s.querySelector(':scope > h1.page-title'); return [s && s.id, h && h.textContent.trim()]; }")

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for vw, vh, scheme in [(390, 844, "light"), (1024, 768, "dark")]:
            t = f"[{vw} {scheme}] "
            ctx = await b.new_context(viewport={"width": vw, "height": vh}, color_scheme=scheme, service_workers="block")
            await ctx.add_init_script(INIT + "localStorage.setItem('fwmc-test-natmodes','true')")
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            await pg.goto(BASE); await pg.wait_for_timeout(300)
            check(t + "no second tab row", not await pg.is_visible("#natHome .sub-switch"))
            check(t + "no old variant panels", await pg.locator("#natHome .nat-panel:visible").count() == 0)
            names = await pg.eval_on_selector_all("#natExercises [data-nat-ex] h3", "els => els.map(e => e.textContent)")
            check(t + "five exercise tiles", names == ["Periphere Wahrnehmung", "Positionen merken", "Blitz-Raster", "Flash-Speicher-Test", "Objektverfolgung (MOT)"], names)
            check(t + "heading like Visual Training", (await pg.inner_text("#natExercises h2")) == (await pg.inner_text("#home .exercises h2")))
            # Flash: default mode, switch modes, training screen, back
            await pg.click('[data-nat-ex="flash"]'); await pg.wait_for_timeout(200)
            sid, title = await visible_title(pg)
            check(t + "Flash opens its ready screen", sid == "flashReady" and title == "Flash-Speicher-Test", (sid, title))
            check(t + "Modus row visible", await pg.is_visible("#flashReady .nat-mode-group"))
            check(t + "Konstant active by default", await pg.get_attribute('#flashReady [data-nat-mode="constant"]', "aria-pressed") == "true")
            await pg.click('#flashReady [data-nat-mode="climb"]'); await pg.wait_for_timeout(150)
            check(t + "Steigend active", await pg.get_attribute('#flashReady [data-nat-mode="climb"]', "aria-pressed") == "true")
            check(t + "desc follows mode", "ein Zeichen mehr" in await pg.inner_text("#flashReadyDesc"))
            await pg.click('#flashReady [data-nat-mode="training"]'); await pg.wait_for_timeout(150)
            sid, title = await visible_title(pg)
            check(t + "Trainingsmodus = training screen with same row", sid == "flashTrainingReady" and title == "Flash-Speicher-Test" and await pg.is_visible("#flashTrainingReady .nat-mode-group"), (sid, title))
            await pg.click("#flashTrainingBackToHome"); await pg.wait_for_timeout(150)
            check(t + "back to NAT home", (await visible_title(pg))[0] == "natHome")
            await pg.click('[data-nat-ex="flash"]'); await pg.wait_for_timeout(150)
            check(t + "last mode remembered", (await visible_title(pg))[0] == "flashTrainingReady")
            await pg.click("#flashTrainingBackToHome"); await pg.wait_for_timeout(150)
            # Remember + MOT
            await pg.click('[data-nat-ex="remember"]'); await pg.wait_for_timeout(150)
            check(t + "Positionen merken: 3 modes", await pg.locator("#rememberReady .nat-mode-group [data-nat-mode]").count() == 3)
            await pg.click('#rememberReady [data-nat-mode="shuffle"]'); await pg.wait_for_timeout(150)
            check(t + "Bewegte Positionen desc", "neu gemischt" in await pg.inner_text("#rememberReadyDesc"))
            await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(150)
            await pg.click('[data-nat-ex="mot"]'); await pg.wait_for_timeout(150)
            check(t + "MOT: 4 modes", await pg.locator("#motReady .nat-mode-group [data-nat-mode]").count() == 4)
            small = await pg.evaluate("() => [...document.querySelectorAll('#motReady .nat-mode-group .choice')].map(e => Math.round(e.getBoundingClientRect().height)).filter(h => h < 44)")
            check(t + "mode buttons >= 44 px", not small, small)
            await pg.screenshot(path=f"nat_modes_mot_{vw}_{scheme}.png")
            await pg.click("#motReadyBackToHome"); await pg.wait_for_timeout(150)
            # Periph + Blitz have no modes
            await pg.click('[data-nat-ex="blitz"]'); await pg.wait_for_timeout(150)
            check(t + "Blitz opens directly", (await visible_title(pg))[0] == "blitzReady")
            await pg.click("#blitzReadyBackToHome"); await pg.wait_for_timeout(150)
            await pg.click('[data-nat-ex="peripher"]'); await pg.wait_for_timeout(150)
            sid, _ = await visible_title(pg)
            check(t + "Periphere Wahrnehmung opens", sid == "ready", sid)
            # Kombi capture shows no Modus row and keeps the variant title
            await pg.goto(BASE); await pg.wait_for_timeout(300)
            await pg.evaluate("document.querySelector('#natHome [data-open-combo]').click()"); await pg.wait_for_timeout(200)
            await pg.evaluate("document.getElementById('flashOpenClimb').click()"); await pg.wait_for_timeout(150)
            check(t + "other paths: no Modus row", not await pg.is_visible("#flashReady .nat-mode-group"))
            check(t + "other paths: variant title", (await pg.inner_text("#flashReadyTitle")) == "Steigend, direkt")
            await pg.screenshot(path=f"nat_modes_home_{vw}_{scheme}.png")
            await ctx.close()
        # without opt-in: old layout
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        check("without opt-in: old sub-tabs", await pg.is_visible("#natHome .sub-switch") and not await pg.is_visible("#natExercises"))
        await ctx.close()
        await b.close()
    check("no page errors", not errors, errors)
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
