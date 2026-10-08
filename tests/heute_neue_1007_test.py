"""Heute für Neue (Fabian 06./07.10.2026): "Mit Trainer oder allein?",
"Wofür trainierst du?", the swipe row "Zum Ausprobieren", Fortschritt only
after the first training, week below the code card while new; plus the new
code card texts and the "Noch keinen Trainer?" link.
Run from tests/ with a dev server on :8845."""
import asyncio, json
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=heute"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-test-bottomnav','1');"
        "localStorage.setItem('fwmc-test-codequiet','1');"
        "localStorage.setItem('fwmc-test-natmodes','1');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


def hist(n):
    return [{"id": str(i), "ts": f"2026-10-0{i+1}T08:00:00Z", "kind": "breath", "title": "Box-Atmung", "rating": None} for i in range(n)]


async def fresh(pg, store=None):
    await pg.goto(URL); await pg.wait_for_timeout(200)
    await pg.evaluate("(s) => { const keep = ['fwmc-tips-seen','fwmc-test-bottomnav','fwmc-test-codequiet','fwmc-test-natmodes','fwmc-master-v1'];"
                      " Object.keys(localStorage).filter(k => !keep.includes(k)).forEach(k => localStorage.removeItem(k));"
                      " Object.entries(s || {}).forEach(([k, v]) => localStorage.setItem(k, JSON.stringify(v))); }", store or {})
    await pg.goto(URL); await pg.wait_for_timeout(400)


async def row_order(pg):
    return await pg.evaluate("() => [...document.querySelectorAll('#todayMain .starter-card')].map(c => c.dataset.starter)")


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- brand new ----
        await fresh(pg)
        check("ask 'Mit Trainer / Allein' shown", await pg.locator("#todayMain [data-starter-who]").count() == 2)
        check("row 'Zum Ausprobieren' shown", await pg.is_visible("#todayMain .starter-head"))
        check("default order", (await row_order(pg))[:3] == ["box", "vt", "remember"], str(await row_order(pg)))
        check("Fortschritt hidden at 0 trainings", await pg.is_hidden("#todayHome .today-progress"))
        below = await pg.evaluate("() => { const c = document.querySelector('#todayHome .today-code'); let n = c && c.nextElementSibling; if (n && n.classList.contains('handover-group')) n = n.nextElementSibling; return n === document.querySelector('#todayHome .today-week'); }")
        check("week sits below the code card (scan link group in between)", below)
        check("todayHome.newcomer", await pg.evaluate("() => document.getElementById('todayHome').classList.contains('newcomer')"))
        await pg.screenshot(path="screenshots/heute_neue_start.png")

        # code card texts
        tog = await pg.inner_text("#todayHome .today-code .code-toggle")
        check("collapsed title", "Dein persönlicher Trainingsplan" in tog, tog)
        check("collapsed sub", "Code eingeben oder individuell angepassten Plan anfragen" in tog)
        links = await pg.evaluate("() => [...document.querySelectorAll('.code-card .code-ask-link')].map(a => a.href)")
        cards = await pg.locator(".code-card").count()
        check("every code card has the 'Noch keinen Trainer?' link", len(links) == cards and all(h == "https://www.fabian-westermann.de/#Kontakt" for h in links), f"{len(links)}/{cards}")

        # Mit Trainer -> opens the code card
        await pg.click('#todayMain [data-starter-who="trainer"]'); await pg.wait_for_timeout(500)
        check("trainer: code card expanded", not await pg.evaluate("() => document.querySelector('#todayHome .today-code').classList.contains('is-collapsed')"))
        check("trainer: hint about the code", "Trainings-Code" in await pg.inner_text("#todayMain"))
        body = await pg.inner_text("#todayHome .today-code")
        check("expanded text", "Dein Trainer stellt dir einen Plan zusammen" in body and "Noch keinen Trainer?" in body, body[:120])
        check("prefs saved", (await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-start-v1'))")).get("who") == "trainer")
        await pg.click("#todayMain [data-starter-reset]"); await pg.wait_for_timeout(200)

        # Allein -> goals
        check("goal chips after 'Doch allein'", await pg.locator("#todayMain [data-starter-goal]").count() == 4)
        await pg.click('#todayMain [data-starter-goal="fokus"]'); await pg.wait_for_timeout(200)
        check("fokus order", (await row_order(pg))[:2] == ["remember", "vt"], str(await row_order(pg)))
        check("goal sentence", "Übungen für Fokus" in await pg.inner_text("#todayMain"))
        await pg.reload(); await pg.wait_for_timeout(400)
        check("goal persists over reload", (await row_order(pg))[0] == "remember")
        await pg.click("#todayMain [data-starter-reset]"); await pg.wait_for_timeout(200)
        await pg.click('#todayMain [data-starter-goal="ruhe"]'); await pg.wait_for_timeout(200)
        check("ruhe order", (await row_order(pg))[:2] == ["box", "coherent"])
        small = await pg.evaluate("() => [...document.querySelectorAll('#todayMain button')].filter(b => b.offsetParent && b.getBoundingClientRect().height < 44).map(b => b.textContent.trim())")
        check("buttons ≥ 44 px", not small, str(small))
        over = await pg.evaluate("() => document.documentElement.scrollWidth > innerWidth")
        check("no sideways page scroll", not over)

        # cards open the right screens
        for key, sel in [("box", "#breathReady"), ("reset", "#breathProgramIntro"), ("remember", "#rememberReady"), ("balance", None), ("vt", None), ("kraft", None)]:
            await fresh(pg, {"fwmc-start-v1": {"who": "allein"}})
            await pg.evaluate("(k) => { const c = document.querySelector(`#todayMain .starter-card[data-starter='${k}']`); c.scrollIntoView(); c.click(); }", key)
            await pg.wait_for_timeout(400)
            vis = await pg.evaluate("() => [...document.querySelectorAll('.screen')].filter(s => !s.hidden && s.offsetParent !== null).map(s => s.id)")
            ok = (sel.lstrip("#") in vis) if sel else (vis and "todayHome" not in vis)
            check(f"card {key} opens a screen", ok, str(vis))

        # soft stage: 1 training
        await fresh(pg, {"fwmc-history-v1": hist(1), "fwmc-start-v1": {"who": "allein", "goal": "ruhe"}})
        check("soft: no ask", await pg.locator("#todayMain [data-starter-who], #todayMain [data-starter-goal]").count() == 0)
        check("soft: row stays", await pg.is_visible("#todayMain .starter-row"))
        check("soft: Fortschritt shown", await pg.is_visible("#todayHome .today-progress"))
        back = await pg.evaluate("() => { const c = document.querySelector('#todayHome .today-code'); return c.nextElementSibling !== document.querySelector('#todayHome .today-week'); }")
        check("soft: week back in its place", back)

        # regular after 3 trainings, or with a code
        await fresh(pg, {"fwmc-history-v1": hist(3)})
        check("3 trainings: row gone", await pg.locator("#todayMain .starter-row").count() == 0)
        await fresh(pg, {"fwmc-code-history-v1": [{"code": "abc", "at": "2026-10-06T08:00:00Z"}]})
        check("code used: no starter", await pg.locator("#todayMain .starter-row, #todayMain [data-starter-who]").count() == 0)

        # dark mode look
        await fresh(pg)
        await pg.emulate_media(color_scheme="dark"); await pg.wait_for_timeout(200)
        await pg.screenshot(path="screenshots/heute_neue_dark.png")
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
