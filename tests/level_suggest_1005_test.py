import asyncio, json
from playwright.async_api import async_playwright

# Stufen-Vorschlag (Fabian, 2026-10-05, Favorit): nach 3 sehr guten Runden
# auf Leicht/Mittel schlägt das Ergebnis die nächste Stufe vor; pro Übung
# wegklickbar, Link in die Grundeinstellungen, dort ein Schalter für alle.
BASE = "http://localhost:8845/index.html?bereich=nat"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = "localStorage.setItem('fwmc-tips-seen','true');if(!localStorage.getItem('fwmc-master-v1'))localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

async def play_blitz_round_and_stop(pg, start=6):
    await pg.click('#natHome .sub-tab[data-nat-sub="blitz"]'); await pg.wait_for_timeout(120)
    await pg.click("#blitzOpenBtn"); await pg.wait_for_timeout(150)
    await pg.click("#blitzAdvanced summary"); await pg.wait_for_timeout(100)
    await pg.fill("#blitzStartSlider", str(start)); await pg.dispatch_event("#blitzStartSlider", "input")
    await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(200)
    lit = await pg.evaluate("() => Array.from(document.querySelectorAll('#blitzGrid .blitz-cell')).map((el,i)=>el.classList.contains('lit')?i:-1).filter(i=>i>=0)")
    await pg.wait_for_timeout(1100)
    cells = await pg.locator("#blitzGrid .blitz-cell").all()
    for i in lit:
        await cells[i].click(); await pg.wait_for_timeout(60)
    await pg.wait_for_timeout(300)
    await pg.click("#blitzBackBtn"); await pg.wait_for_timeout(300)
    return len(lit)

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        seed = json.dumps({"streaks": {"blitz:standard:mittel": 2}, "muted": {}})
        await ctx.add_init_script(INIT + f"if(!sessionStorage.getItem('seeded')){{localStorage.setItem('fwmc-level-suggest-v1', {json.dumps(seed)});sessionStorage.setItem('seeded','1')}}")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        n = await play_blitz_round_and_stop(pg)
        check("round played with 6 cells", n == 6, n)
        check("done panel visible", await pg.is_visible("#blitzDonePanel"))
        check("3rd very good run: suggestion shows", await pg.is_visible("#blitzDonePanel .level-suggest"))
        txt = await pg.inner_text("#blitzDonePanel .level-suggest")
        check("names Mittel -> Schwer", "Mittel" in txt and "Schwer" in txt, txt)
        small = await pg.evaluate("() => [...document.querySelectorAll('#blitzDonePanel .level-suggest button')].map(e => Math.round(e.getBoundingClientRect().height)).filter(h => h < 44)")
        check("buttons >= 44 px", not small, small)
        await pg.screenshot(path="level_suggest_blitz.png")
        await pg.click("#blitzDonePanel .level-suggest-yes"); await pg.wait_for_timeout(150)
        prefs = json.loads(await pg.evaluate("localStorage.getItem('fwmc-blitz-prefs-v1') || '{}'"))
        check("Ja sets Schwer", abs(prefs.get("flashS", 0) - 0.5) < 0.001, prefs)
        check("confirmation text", "Eingestellt: Schwer" in await pg.inner_text("#blitzDonePanel .level-suggest"))
        st = json.loads(await pg.evaluate("localStorage.getItem('fwmc-level-suggest-v1')"))
        check("streak reset after showing", st["streaks"].get("blitz:standard:mittel") == 0, st)
        # schwer: never suggests further
        await pg.click("#blitzDoneBackBtn") if await pg.locator("#blitzDoneBackBtn").count() else None
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        await pg.evaluate("localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks:{'blitz:standard:schwer':5},muted:{}}))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await play_blitz_round_and_stop(pg, start=3)
        check("weak run / Schwer: no suggestion", not await pg.is_visible("#blitzDonePanel .level-suggest"))
        st = json.loads(await pg.evaluate("localStorage.getItem('fwmc-level-suggest-v1')"))
        check("weak run resets the streak", st["streaks"].get("blitz:standard:schwer") == 0, st)
        # mute for this exercise
        await pg.evaluate("localStorage.setItem('fwmc-blitz-prefs-v1', JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('fwmc-blitz-prefs-v1')), {flashS:0.8})))")
        await pg.evaluate("localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks:{'blitz:standard:mittel':2},muted:{}}))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await play_blitz_round_and_stop(pg)
        check("suggestion again", await pg.is_visible("#blitzDonePanel .level-suggest"))
        await pg.click("#blitzDonePanel .level-suggest-mute"); await pg.wait_for_timeout(100)
        check("mute removes the box", not await pg.is_visible("#blitzDonePanel .level-suggest"))
        st = json.loads(await pg.evaluate("localStorage.getItem('fwmc-level-suggest-v1')"))
        check("blitz muted", st["muted"].get("blitz") is True, st)
        await pg.evaluate("localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks:{'blitz:standard:mittel':2},muted:{blitz:true}}))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await play_blitz_round_and_stop(pg)
        check("muted: no suggestion", not await pg.is_visible("#blitzDonePanel .level-suggest"))
        # master switch: link opens Grundeinstellungen; turning it on clears mutes
        await pg.evaluate("localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks:{'blitz:standard:mittel':2},muted:{}}))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await play_blitz_round_and_stop(pg)
        await pg.click("#blitzDonePanel .level-suggest-off"); await pg.wait_for_timeout(200)
        check("link opens Grundeinstellungen", await pg.is_visible("#masterSettingsSheet"))
        check("switch is on", await pg.is_checked("#masterLevelSuggestCheck"))
        await pg.uncheck("#masterLevelSuggestCheck"); await pg.wait_for_timeout(100)
        m = json.loads(await pg.evaluate("localStorage.getItem('fwmc-master-v1')"))
        check("switch off saved", m.get("levelSuggest") is False, m)
        await pg.evaluate("localStorage.setItem('fwmc-level-suggest-v1', JSON.stringify({streaks:{'blitz:standard:mittel':2},muted:{blitz:true}}))")
        await pg.reload(); await pg.wait_for_timeout(300)
        await play_blitz_round_and_stop(pg)
        check("switched off: no suggestion", not await pg.is_visible("#blitzDonePanel .level-suggest"))
        await pg.click("#blitzDoneBackBtn") if await pg.locator("#blitzDoneBackBtn").count() else None
        await pg.evaluate("document.querySelector('#natHome .master-settings-btn').click()"); await pg.wait_for_timeout(200)
        await pg.check("#masterLevelSuggestCheck"); await pg.wait_for_timeout(100)
        st = json.loads(await pg.evaluate("localStorage.getItem('fwmc-level-suggest-v1')"))
        check("switching on clears mutes", st.get("muted") == {}, st)
        await ctx.close()
        await b.close()
    check("no page errors", not errors, errors)
    print("ALL OK" if ok_all else "SOME FAILED")

asyncio.run(main())
