import asyncio
from playwright.async_api import async_playwright

# Tipp-Tasten (Fabian, 2026-10-05): answer keys grow with the screen and are
# never under 44 px. Checks the Flash keypad (largest key set, "gemischt")
# on a phone and an iPad, and the Stroop answer buttons, plus the second-
# package details: the step-bar sound button is a single-colour icon.
URL = "http://localhost:8845/index.html?bereich=nat"
ok_all = True
def check(label, ok, info=""):
    global ok_all
    ok_all = ok_all and bool(ok)
    print(label + ":", bool(ok), info)

async def flash_keys(b, w, h):
    ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block")
    await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true')")
    pg = await ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(300)
    await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
    await pg.click("#flashOpenClimb"); await pg.wait_for_timeout(150)
    await pg.click('#flashKindRow [data-flash-kind="gemischt"]'); await pg.wait_for_timeout(80)
    await pg.click("#flashReadyStartBtn")
    await pg.wait_for_selector("#flashKeypad .flash-key", state="visible", timeout=20000); await pg.wait_for_timeout(200)
    sizes = await pg.eval_on_selector_all("#flashKeypad .flash-key", "els => els.map(e => e.getBoundingClientRect().width)")
    bottom = await pg.evaluate("Math.max(...[...document.querySelectorAll('#flashKeypad .flash-key')].map(e => e.getBoundingClientRect().bottom))")
    clear = await pg.evaluate("""() => { const bar = document.getElementById('flashPlayerBar').getBoundingClientRect();
      const box = document.querySelector('#flashPlayer .flash-answer-box'); return box ? box.getBoundingClientRect().top >= bar.bottom : true; }""")
    sound = await pg.evaluate("(() => { const b = document.getElementById('stepSoundBtn'); return b ? !!b.querySelector('svg') && !/\\u{1F50A}|\\u{1F507}/u.test(b.textContent) : null; })()")
    await ctx.close()
    return min(sizes) if sizes else 0, bottom, sound, errs, clear

async def stroop_size(b, w, h):
    ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block")
    pg = await ctx.new_page()
    await pg.goto("http://localhost:8845/index.html?bereich=visual"); await pg.wait_for_timeout(200)
    size = await pg.evaluate("""() => { const b = document.createElement('button'); b.className = 'stroop-response-btn'; document.body.appendChild(b);
      const r = b.getBoundingClientRect(); b.remove(); return r.width; }""")
    await ctx.close()
    return size

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        k_phone, bot_phone, snd, e1, c1 = await flash_keys(b, 375, 667)
        k_pad, bot_pad, _, e2, c2 = await flash_keys(b, 820, 1180)
        k_land, bot_land, _, e3, c3 = await flash_keys(b, 1024, 768)
        e2 = e2 + e3
        check("answer boxes below the player bar (phone, iPad, iPad landscape)", c1 and c2 and c3, (c1, c2, c3))
        check("all keys visible on the iPad in landscape", bot_land <= 768 - 56, round(bot_land))
        check("all keys visible on a small phone (above the step bar)", bot_phone <= 667 - 56, round(bot_phone))
        check("Flash keys at least 44 px on a small phone", k_phone >= 44, round(k_phone))
        check("Flash keys clearly bigger on the iPad (portrait)", k_pad >= k_phone * 1.3, (round(k_phone), round(k_pad)))
        check("step-bar sound button is a single-colour icon", snd is True, snd)
        s_phone, s_pad = await stroop_size(b, 390, 844), await stroop_size(b, 1024, 1366)
        check("answer buttons grow on the iPad", s_pad > s_phone * 1.3, (round(s_phone), round(s_pad)))
        check("No page errors", not (e1 + e2), (e1 + e2)[:2])
        await b.close()
    print("ALL OK:", ok_all)

asyncio.run(main())
