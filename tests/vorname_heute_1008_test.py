"""Vorname in der Begrüßung (Fabian, 2026-10-08).

Heute's hello card: without a name "+ Wie heißt du?" opens an
inline form (Speichern / Enter / Abbrechen); with a name the greeting reads
"Guten …, <Name>". Stored only on the device (fwmc-name-v1, trimmed, max 30),
editable/clearable in Grundeinstellungen "Dein Name", shown as text (no HTML),
never in a reminder payload or any Worker request. Layout at 390/1024 light
and dark without sideways scroll, no page errors."""
import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html?bereich=heute"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "vorname")

results = []


def check(name, ok):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}")


PLAN_JS = """(() => {
  const days = [[{id:'a',area:'cardio',what:'',code:'',time:'18:00',minutes:20}],[], [{id:'b',area:'visual',what:'',code:'',time:'',minutes:15}],[],[],[],[]];
  return {startDate:'2026-09-28', phases:[{id:'p',name:'P',weeks:0,days}], extras:{}, skips:{}, done:{}};
})()"""


async def greeting(pg):
    return (await pg.locator("#todayGreeting").inner_text()).strip()


async def vis(pg, sel):
    return await pg.locator(sel).is_visible()


async def open_master(pg):
    await pg.locator(".master-settings-btn:visible").first.click()
    await pg.wait_for_timeout(250)


async def close_master(pg):
    await pg.click("#masterSettingsCloseBtn")
    await pg.wait_for_timeout(200)


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors, worker_bodies = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", has_touch=True)
        await ctx.add_init_script("try{localStorage.setItem('fwmc-tips-seen','true')}catch(e){}")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def worker(route):
            worker_bodies.append((route.request.url, route.request.post_data or ""))
            await route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
        await pg.route("**/*.workers.dev/**", worker)

        await pg.goto(BASE)
        await pg.wait_for_timeout(500)

        # --- without a name ---
        check("no name stored", await pg.evaluate("localStorage.getItem('fwmc-name-v1')") is None)
        check("button shown without name", await vis(pg, "#helloNameBtn"))
        check("button text", "Wie heißt du?" in await pg.inner_text("#helloNameBtn"))
        bh = await pg.evaluate("document.getElementById('helloNameBtn').getBoundingClientRect().height")
        check(f"button >= 44 px ({bh})", bh >= 44)
        check("button inside the hello card", await pg.evaluate("!!document.querySelector('.today-hello #helloNameBtn')"))
        g0 = await greeting(pg)
        check(f"greeting without comma ({g0})", "," not in g0 and g0.startswith("Gute"))
        await pg.screenshot(path=os.path.join(SHOTS, "heute_ohne_name_390_light.png"))

        # --- inline form, cancel ---
        await pg.click("#helloNameBtn")
        await pg.wait_for_timeout(100)
        check("form opens", await vis(pg, "#helloNameForm") and await vis(pg, "#helloNameInput"))
        check("button hidden while form open", not await vis(pg, "#helloNameBtn"))
        check("input focused", await pg.evaluate("document.activeElement && document.activeElement.id") == "helloNameInput")
        attrs = await pg.evaluate("(() => { const i = document.getElementById('helloNameInput'); return [i.autocomplete, i.placeholder, i.maxLength, parseFloat(getComputedStyle(i).fontSize), i.getBoundingClientRect().height]; })()")
        check(f"input attrs ({attrs})", attrs[0] == "given-name" and attrs[1] == "Dein Vorname" and attrs[2] == 30)
        check("input >= 16 px font, >= 44 px tall", attrs[3] >= 16 and attrs[4] >= 44)
        sh = await pg.evaluate("[document.getElementById('helloNameSaveBtn').getBoundingClientRect().height, document.getElementById('helloNameCancelBtn').getBoundingClientRect().height]")
        check(f"Speichern/Abbrechen >= 44 px ({sh})", min(sh) >= 44)
        await pg.screenshot(path=os.path.join(SHOTS, "heute_formular_390_light.png"))
        await pg.click("#helloNameCancelBtn")
        await pg.wait_for_timeout(100)
        check("cancel closes form", not await vis(pg, "#helloNameForm") and await vis(pg, "#helloNameBtn"))
        check("cancel saves nothing", await pg.evaluate("localStorage.getItem('fwmc-name-v1')") is None)

        # --- whitespace only is not saved ---
        await pg.click("#helloNameBtn")
        await pg.fill("#helloNameInput", "    ")
        await pg.press("#helloNameInput", "Enter")
        await pg.wait_for_timeout(100)
        check("whitespace not saved", await pg.evaluate("localStorage.getItem('fwmc-name-v1')") is None)
        check("form stays open on empty save", await vis(pg, "#helloNameForm"))
        await pg.click("#helloNameSaveBtn")
        await pg.wait_for_timeout(100)
        check("empty Speichern saves nothing", await pg.evaluate("localStorage.getItem('fwmc-name-v1')") is None)

        # --- save with Enter ---
        await pg.fill("#helloNameInput", "  Anna  ")
        await pg.press("#helloNameInput", "Enter")
        await pg.wait_for_timeout(150)
        check("stored trimmed", await pg.evaluate("localStorage.getItem('fwmc-name-v1')") == "Anna")
        g1 = await greeting(pg)
        check(f"greeting ends ', Anna' ({g1})", g1.endswith(", Anna") and g1.split(",")[0] in ("Guten Morgen", "Guten Tag", "Guten Abend"))
        check("button gone after save", not await vis(pg, "#helloNameBtn") and not await vis(pg, "#helloNameForm"))
        await pg.screenshot(path=os.path.join(SHOTS, "heute_mit_name_390_light.png"))

        # --- persists after reload ---
        await pg.reload()
        await pg.wait_for_timeout(500)
        check("name after reload", (await greeting(pg)).endswith(", Anna"))
        check("button still gone after reload", not await vis(pg, "#helloNameBtn"))

        # --- in backups ---
        exclude = await pg.evaluate("fetch('app.js').then(r => r.text()).then(t => (t.match(/BACKUP_EXCLUDE = \\[[^\\]]*\\]/) || [''])[0])")
        check(f"backup does not exclude the name ({exclude})", "BACKUP_EXCLUDE" in exclude and "fwmc-name" not in exclude)

        # --- Grundeinstellungen: change ---
        await open_master(pg)
        check("Dein Name group visible", await vis(pg, "#masterNameGroup"))
        check("group help text", "Nur für die Begrüßung. Bleibt auf diesem Gerät." in await pg.inner_text("#masterNameGroup"))
        check("field shows current name", await pg.input_value("#masterNameInput") == "Anna")
        check("sheet does not start in the name field (no keyboard)", await pg.evaluate("document.activeElement && document.activeElement.id") != "masterNameInput")
        await pg.screenshot(path=os.path.join(SHOTS, "grundeinstellungen_name_390_light.png"))
        await pg.fill("#masterNameInput", "Ben")
        await pg.press("#masterNameInput", "Tab")
        await pg.wait_for_timeout(100)
        check("changed in storage", await pg.evaluate("localStorage.getItem('fwmc-name-v1')") == "Ben")
        await close_master(pg)
        check("greeting updated to Ben", (await greeting(pg)).endswith(", Ben"))

        # --- Grundeinstellungen: clear brings the button back ---
        await open_master(pg)
        await pg.fill("#masterNameInput", "")
        await pg.press("#masterNameInput", "Enter")
        await pg.wait_for_timeout(100)
        check("cleared in storage", await pg.evaluate("localStorage.getItem('fwmc-name-v1')") is None)
        await close_master(pg)
        check("button back after clearing", await vis(pg, "#helloNameBtn"))
        check("greeting without name again", "," not in await greeting(pg))

        # --- HTML is shown as text ---
        await pg.click("#helloNameBtn")
        await pg.fill("#helloNameInput", "<b>X</b><img src=x>")
        await pg.click("#helloNameSaveBtn")
        await pg.wait_for_timeout(150)
        g2 = await greeting(pg)
        check(f"HTML shown literally ({g2})", "<b>X</b>" in g2)
        check("no element injected", await pg.evaluate("document.querySelectorAll('#todayGreeting b, #todayGreeting img').length") == 0)

        # --- 30-character cap ---
        long40 = "A" * 40
        await pg.evaluate(f"localStorage.setItem('fwmc-name-v1', {json.dumps(long40)})")
        await pg.reload()
        await pg.wait_for_timeout(400)
        nm = await pg.evaluate("document.querySelector('#todayGreeting .today-greeting-name').textContent")
        check(f"greeting name capped at 30 ({len(nm)})", len(nm) == 30)
        await open_master(pg)
        await pg.evaluate(f"(() => {{ const i = document.getElementById('masterNameInput'); i.value = {json.dumps('B' * 45)}; i.dispatchEvent(new Event('change')); }})()")
        await pg.wait_for_timeout(100)
        stored = await pg.evaluate("localStorage.getItem('fwmc-name-v1')")
        check(f"stored capped at 30 ({len(stored or '')})", stored == "B" * 30)
        await close_master(pg)
        await pg.evaluate("localStorage.removeItem('fwmc-name-v1')")
        await pg.reload()
        await pg.wait_for_timeout(400)
        await pg.click("#helloNameBtn")
        await pg.type("#helloNameInput", "C" * 35)
        await pg.press("#helloNameInput", "Enter")
        await pg.wait_for_timeout(100)
        check("typed name capped at 30", await pg.evaluate("localStorage.getItem('fwmc-name-v1')") == "C" * 30)

        # --- reminder payload never contains the name ---
        await pg.evaluate("localStorage.setItem('fwmc-name-v1', 'Zebulonia')")
        await pg.evaluate(f"localStorage.setItem('fwmc-plan-v1', JSON.stringify({PLAN_JS}))")
        await pg.evaluate("""localStorage.setItem('fwmc-reminders-v1', JSON.stringify({on: true, lead: 10, morning: '08:00'}))""")
        await pg.reload()
        await pg.wait_for_timeout(500)
        rem = await pg.evaluate("JSON.stringify(window.__fwmcComputeReminders(new Date('2026-10-23T10:00:00Z')))")
        check("reminders computed", len(json.loads(rem)) > 0)
        check("reminder payload has no name", "Zebulonia" not in rem)
        # a code lookup goes to the Worker too: the name is in no request
        await pg.evaluate("(() => { const i = document.getElementById('moreCodeInput') || document.getElementById('todayCodeInput'); if (i) { i.value = 'abc123'; } const g = document.getElementById('moreCodeGoBtn') || document.getElementById('todayCodeGoBtn'); if (g) g.click(); })()")
        await pg.wait_for_timeout(600)
        check(f"no Worker request carries the name ({len(worker_bodies)} requests)", all("Zebulonia" not in u and "Zebulonia" not in d for u, d in worker_bodies))
        src = await pg.evaluate("fetch('app.js').then(r => r.text())")
        name_uses = [l.strip() for l in src.splitlines() if "fwmc-name-v1" in l or "getUserName(" in l]
        check(f"name read only by greeting/settings ({len(name_uses)} lines)", all(("NAME_KEY" in l or "getUserName" in l or "fwmc-name-v1" in l) and "fetch" not in l and "REMINDER" not in l for l in name_uses))
        await ctx.close()

        # --- 390 + 1024, light + dark, with and without name ---
        for scheme in ("light", "dark"):
            for w in (390, 1024):
                c = await b.new_context(viewport={"width": w, "height": 844}, service_workers="block", color_scheme=scheme)
                await c.add_init_script("try{localStorage.setItem('fwmc-tips-seen','true')}catch(e){}")
                q = await c.new_page()
                q.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
                q.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
                await q.route("**/*.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
                await q.goto(BASE)
                await q.wait_for_timeout(500)
                sw = await q.evaluate("document.documentElement.scrollWidth")
                check(f"{w} {scheme} no name: no sideways scroll ({sw})", sw <= w)
                if w == 390:
                    await q.screenshot(path=os.path.join(SHOTS, f"heute_ohne_name_390_{scheme}.png"))
                await q.click("#helloNameBtn")
                await q.wait_for_timeout(100)
                sw = await q.evaluate("document.documentElement.scrollWidth")
                check(f"{w} {scheme} form: no sideways scroll ({sw})", sw <= w)
                if w == 390:
                    await q.screenshot(path=os.path.join(SHOTS, f"heute_formular_390_{scheme}.png"))
                await q.fill("#helloNameInput", "Maximiliane-Charlotte")
                await q.press("#helloNameInput", "Enter")
                await q.wait_for_timeout(150)
                sw = await q.evaluate("document.documentElement.scrollWidth")
                check(f"{w} {scheme} long name: no sideways scroll ({sw})", sw <= w)
                over = await q.evaluate("(() => { const g = document.getElementById('todayGreeting'); return g.scrollWidth > g.clientWidth + 1; })()")
                check(f"{w} {scheme} long name fits the card", not over)
                await q.screenshot(path=os.path.join(SHOTS, f"heute_langer_name_{w}_{scheme}.png"))
                await q.evaluate("localStorage.setItem('fwmc-name-v1', 'Anna')")
                await q.reload()
                await q.wait_for_timeout(400)
                if w == 390:
                    await q.screenshot(path=os.path.join(SHOTS, f"heute_mit_name_390_{scheme}.png"))
                    await open_master(q)
                    await q.locator("#masterNameGroup").scroll_into_view_if_needed()
                    await q.screenshot(path=os.path.join(SHOTS, f"grundeinstellungen_name_390_{scheme}.png"))
                    sw = await q.evaluate("document.documentElement.scrollWidth")
                    check(f"{w} {scheme} Grundeinstellungen: no sideways scroll ({sw})", sw <= w)
                await c.close()
        await b.close()

    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("FAILED:", failed)
    print("ERRORS:", errors)


asyncio.run(main())
