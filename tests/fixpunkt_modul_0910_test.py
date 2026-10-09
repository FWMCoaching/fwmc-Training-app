"""Fixpunkt-Modul (Fabian 2026-10-09): Grundeinstellungen = Standard
(Punkt/Kreuz/Text bis 12 Zeichen, Farbe, Größe), each exercise and each NAT
mode keeps its own change (fwmc-fix-v1), "Auf Grundeinstellung zurück",
"Von anderer Übung übernehmen", "Für alle übernehmen, auch geänderte" with
confirmDialog, MOT gets a fixation point, Flash per mode, VT pause sheet has
the full group, old settings migrate, screenshots, no page errors."""
import asyncio
import json
import os
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
ROOT = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "fixpunkt_modul")
results, errors = [], []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}" + (f"  [{str(extra)[:300]}]" if not ok and extra != "" else ""))


async def new_page(b, extra="", scheme="light"):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, locale="de-DE", service_workers="block", color_scheme=scheme)
    await ctx.add_init_script("try{if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');"
                              "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1','{\"startCountdown\":false}');" + extra + "}}catch(e){}")
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
    return ctx, pg


async def own(pg):
    v = await pg.evaluate("localStorage.getItem('fwmc-fix-v1')")
    return json.loads(v) if v else None


async def open_vt(pg, ex):
    await pg.goto(ROOT + "?bereich=visual"); await pg.wait_for_timeout(350)
    await pg.evaluate(f"document.querySelector('#home .excard[data-exercise=\"{ex}\"]').click()"); await pg.wait_for_timeout(250)
    await pg.evaluate("document.querySelectorAll('#ready details').forEach(d => d.open = true)")


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx, pg = await new_page(b)
        await open_vt(pg, "vt-color")
        check("migration: empty own store, standard written", await own(pg) == {} and (json.loads(await pg.evaluate("localStorage.getItem('fwmc-master-v1')")).get("fix") or {}).get("kind") == "punkt")
        check("VT group: kind row Punkt/Kreuz/Text, text field hidden for Punkt",
              await pg.locator("#periphFixKindRow button").all_inner_texts() == ["Punkt", "Kreuz", "Text"] and not await pg.is_visible("#periphFixCharInput"))
        check("follows the Grundeinstellungen", "Wie in den Grundeinstellungen" in await pg.inner_text("#periphFixStatus"))
        await pg.click('#periphFixKindRow [data-fix-kind="text"]'); await pg.wait_for_timeout(100)
        check("Text shows the field", await pg.is_visible("#periphFixCharInput"))
        await pg.fill("#periphFixCharInput", "Anna 🙂 sehr lang"); await pg.wait_for_timeout(100)
        o = await own(pg)
        check("text stored for this exercise only, max 12 characters", list(o) == ["vt:vt-color"] and o["vt:vt-color"]["kind"] == "text" and len(o["vt:vt-color"]["text"]) <= 12, o)
        await pg.locator("#periphFixGroup").scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "vt-eigene-390-light.png"))
        await open_vt(pg, "4-straight")
        check("another VT exercise still shows the standard", await pg.evaluate("document.querySelector('#periphFixKindRow .choice.active').dataset.fixKind") == "punkt"
              and "Wie in den Grundeinstellungen" in await pg.inner_text("#periphFixStatus"))
        await pg.click("#periphFixStatus .xfer-btn"); await pg.wait_for_timeout(150)
        items = await pg.locator("#xferList .xfer-item").all_inner_texts()
        check("Übernehmen lists Grundeinstellungen + the changed exercise", len(items) == 2 and "Grundeinstellungen" in items[0] and "Wie bei" in items[1], items)
        await pg.screenshot(path=os.path.join(SHOTS, "uebernehmen-390-light.png"))
        await pg.locator("#xferList .xfer-item").nth(1).click(); await pg.wait_for_timeout(150)
        o = await own(pg)
        check("'Wie bei' copies the value into this exercise", o.get("vt:4-straight", {}).get("text") == o["vt:vt-color"]["text"], o)
        await pg.click("#periphFixStatus .text-link:not(.xfer-btn)"); await pg.wait_for_timeout(150)
        check("'Auf Grundeinstellung zurück' drops only this exercise", "vt:4-straight" not in await own(pg) and "vt:vt-color" in await own(pg))
        # Grundeinstellungen: change the standard -> untouched exercises follow
        await pg.evaluate("[...document.querySelectorAll('.master-settings-btn')].find((b) => b.offsetParent).click()"); await pg.wait_for_timeout(300)
        check("Grundeinstellungen: Standard-Fixpunkt with info and overwrite button", await pg.is_visible("#masterFixGroup")
              and "1 Übung" in await pg.inner_text("#masterFixOwnInfo") and await pg.is_visible("#masterFixAllBtn")
              and "Überschreibt alle deine Änderungen" in await pg.inner_text("#masterFixGroup"))
        await pg.click('#masterFixKindRow [data-fix-kind="kreuz"]'); await pg.wait_for_timeout(100)
        await pg.locator("#masterFixGroup").scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "grundeinstellungen-390-light.png"))
        await pg.click("#masterFixAllBtn"); await pg.wait_for_timeout(150)
        check("overwrite asks first", await pg.is_visible("#confirmYesBtn") and "überschreibt" in (await pg.inner_text("#confirmText")).lower())
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(150)
        check("after overwrite: no own settings left", await own(pg) == {})
        await open_vt(pg, "vt-color")
        check("untouched exercise now shows the new standard (Kreuz)", await pg.evaluate("document.querySelector('#periphFixKindRow .choice.active').dataset.fixKind") == "kreuz")
        # MOT: standard on, per mode
        await pg.goto(ROOT + "?bereich=nat"); await pg.wait_for_timeout(350)
        await pg.evaluate("document.getElementById('motOpenSpeed').click()"); await pg.wait_for_timeout(250)
        await pg.evaluate("document.querySelectorAll('#motReady details').forEach(d => d.open = true)")
        check("MOT ready screen has the group, on by default", await pg.locator("#motFixGroup").count() == 1
              and await pg.evaluate("document.querySelector('#motFixToggleRow .choice.active').dataset.fixOn") == "1")
        await pg.click('#motFixToggleRow [data-fix-on="0"]'); await pg.wait_for_timeout(100)
        check("MOT off stored for 'Tempo steigt' only", (await own(pg)).get("mot:speed", {}).get("on") is False and "mot:count" not in await own(pg))
        await pg.click('#motFixToggleRow [data-fix-on="1"]'); await pg.wait_for_timeout(100)
        await pg.click("#motReadyStartBtn"); await pg.wait_for_timeout(700)
        check("MOT run shows the fixation point", await pg.is_visible("#motFixpointEl"))
        await pg.click("#motPauseBtn"); await pg.wait_for_timeout(200)
        check("MOT pause sheet has the full group", await pg.is_visible("#motPauseFixToggleRow") and await pg.is_visible("#motPauseFixKindRow"))
        await pg.click('#motPauseFixToggleRow [data-fix-on="0"]'); await pg.wait_for_timeout(100)
        check("switching off in the pause hides it at once", not await pg.is_visible("#motFixpointEl") or await pg.evaluate("document.getElementById('motFixpointEl').hidden"))
        await pg.screenshot(path=os.path.join(SHOTS, "mot-pause-390-light.png"))
        await ctx.close()

        # migration from the old shared VT + Flash values
        ctx, pg = await new_page(b, "localStorage.setItem('fwmc-webapp-v3', JSON.stringify({periphFixEnabled:true, periphFixChar:'X', periphFixColor:'rot', periphFixSize:1.4}));"
                                    "localStorage.setItem('fwmc-flash-prefs-v1', JSON.stringify({fixEnabled:true, fixChar:'', fixColor:'blau', fixSize:1}));")
        await pg.goto(ROOT + "?bereich=visual"); await pg.wait_for_timeout(500)
        m = json.loads(await pg.evaluate("localStorage.getItem('fwmc-master-v1')")).get("fix")
        o = await own(pg)
        check("migration: old VT value becomes the standard", m == {"kind": "text", "text": "X", "color": "rot", "size": 1.4}, m)
        check("migration: a different Flash value stays Flash's own in every mode", sorted(o) == ["flash:climb", "flash:climbRepeat", "flash:constant", "flash:training"] and o["flash:constant"]["color"] == "blau", o)
        await ctx.close()

        # dark screenshot of the VT group
        ctx, pg = await new_page(b, scheme="dark")
        await open_vt(pg, "vt-color")
        await pg.locator("#periphFixGroup").scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "vt-390-dark.png"))
        await ctx.close()
        await b.close()
    check("no page errors", not errors, errors[:5])
    print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} passed")


asyncio.run(main())
