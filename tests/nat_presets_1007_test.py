"""NAT: "Aktuelle Einstellung speichern" (Idee 54, Fabian 07.10.2026) on all
NAT ready screens - same list + name form as VT/Atem/Reaktion, tap = apply
and start, ✕ asks via confirmDialog, Kombi capture only fills the draft and
never leaks into the client's own prefs. Periphere Wahrnehmung (VT ready
screen) now carries its own settings in the VT preset.
Run from tests/ with a dev server on :8845."""
import asyncio, json
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=nat"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-test-natmodes','1');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


async def js_click(pg, sel):
    await pg.evaluate("(s) => document.querySelector(s).click()", sel)
    await pg.wait_for_timeout(200)


async def save(pg, sid, name):
    await pg.click(f"#{sid}SaveBtn"); await pg.wait_for_timeout(100)
    await pg.fill(f"#{sid}SaveNameInput", name)
    await pg.click(f"#{sid}SaveConfirmBtn"); await pg.wait_for_timeout(150)


async def store(pg):
    return await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-nat-saved-v1') || '[]')")


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)

        # ---- every NAT ready screen has the save link, list hidden while empty ----
        for card, sid in [("#rememberOpenFixed", "rememberReady"), ("#rememberOpenTraining", "rememberTrainingReady"),
                          ("#blitzOpenBtn", "blitzReady"), ("#flashOpenConstant", "flashReady"), ("#flashOpenTraining", "flashTrainingReady"),
                          ("#motOpenSpeed", "motReady"), ("#motOpenTraining", "motTrainingReady"), ("#balanceOpenBtn", "balanceReady")]:
            await js_click(pg, card)
            ok = await pg.is_visible(f"#{sid}") and await pg.is_visible(f"#{sid}SaveBtn") and not await pg.is_visible(f"#{sid}SavedGroup")
            check(f"{sid}: save link, no list yet", ok, await pg.inner_text(f"#{sid}SaveBtn") if await pg.is_visible(f"#{sid}SaveBtn") else "")

        # ---- Positionen merken: save Schwer, change to Leicht, reload, apply ----
        await js_click(pg, "#rememberOpenFixed")
        await js_click(pg, '#rememberReady [data-remember-diff="schwer"]')
        await save(pg, "rememberReady", "Schwer fest")
        st = await store(pg)
        check("saved entry has ex/mode/prefs", len(st) == 1 and st[0]["ex"] == "remember" and st[0]["mode"] == "fixed" and abs(st[0]["prefs"]["revealBaseS"] - 0.7) < 1e-6, json.dumps(st)[:200])
        meta = await pg.inner_text("#rememberReadySavedList")
        check("list shows name + mode + difficulty", "Schwer fest" in meta and "Feste Positionen" in meta and "Schwer" in meta, meta)
        await js_click(pg, '#rememberReady [data-remember-diff="leicht"]')
        await js_click(pg, "#rememberOpenShuffle")
        await save(pg, "rememberReady", "")  # empty name = default name
        st = await store(pg)
        check("empty name gets default name", len(st) == 2 and st[1]["name"].startswith("Eigene Einstellung") and st[1]["mode"] == "shuffle")
        await pg.screenshot(path="screenshots/nacht2_1007/nat_presets_remember_light.png", full_page=True)

        await pg.goto(URL); await pg.wait_for_timeout(400)
        await js_click(pg, "#rememberOpenFixed")
        n = await pg.locator("#rememberReadySavedList .bundle-item").count()
        check("persists across reload, both modes listed", n == 2, str(n))
        await js_click(pg, "#blitzOpenBtn")
        check("Blitz-Raster list stays empty", not await pg.is_visible("#blitzReadySavedGroup"))

        await js_click(pg, "#rememberOpenFixed")
        await pg.click('#rememberReadySavedList .bundle-item:has-text("Schwer fest")'); await pg.wait_for_timeout(400)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1'))")
        check("tap applies + starts", await pg.is_visible("#rememberPlayer") and abs(prefs["revealBaseS"] - 0.7) < 1e-6, str(prefs.get("revealBaseS")))
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(300)

        # mode switches along: the shuffle preset tapped on the fixed screen
        await js_click(pg, "#rememberOpenFixed")
        await pg.click('#rememberReadySavedList .bundle-item:has-text("Eigene Einstellung")'); await pg.wait_for_timeout(400)
        mode = await pg.evaluate("() => (JSON.parse(localStorage.getItem('fwmc-nat-mode-v1') || '{}')).remember")
        check("preset of another mode starts in that mode", await pg.is_visible("#rememberPlayer") and mode == "shuffle", str(mode))
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(300)

        # ---- delete asks first ----
        await js_click(pg, "#rememberOpenFixed")
        await pg.click("#rememberReadySavedList .bundle-item-wrap >> nth=0 >> .combo-block-remove"); await pg.wait_for_timeout(150)
        check("✕ opens confirm sheet", await pg.is_visible("#confirmSheet") and "löschen" in (await pg.inner_text("#confirmText")))
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(150)
        check("Abbrechen keeps it", await pg.locator("#rememberReadySavedList .bundle-item").count() == 2)
        await pg.click("#rememberReadySavedList .bundle-item-wrap >> nth=0 >> .combo-block-remove"); await pg.wait_for_timeout(150)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(150)
        check("Löschen removes it", await pg.locator("#rememberReadySavedList .bundle-item").count() == 1 and len(await store(pg)) == 1)

        # ---- the other NAT exercises: save + tap starts their player ----
        for card, sid, player, back in [("#blitzOpenBtn", "blitzReady", "#blitzPlayer", "#blitzBackBtn"),
                                        ("#flashOpenTraining", "flashTrainingReady", "#flashPlayer", "#flashBackBtn"),
                                        ("#motOpenSpeed", "motReady", "#motPlayer", "#motBackBtn"),
                                        ("#balanceOpenBtn", "balanceReady", "#balancePlayer", "#balanceBackBtn")]:
            await js_click(pg, card)
            await save(pg, sid, f"Mein {sid}")
            item = f'#{sid}SavedList .bundle-item:has-text("Mein {sid}")'
            check(f"{sid}: listed", await pg.locator(item).count() == 1, await pg.inner_text(f"#{sid}SavedList"))
            await pg.click(item); await pg.wait_for_timeout(500)
            check(f"{sid}: tap starts the exercise", await pg.is_visible(player))
            if await pg.is_visible(back):
                await pg.click(back); await pg.wait_for_timeout(300)
            if await pg.is_visible("#confirmSheet"):
                await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
            await pg.evaluate("() => document.querySelectorAll('.player').forEach((p) => { p.hidden = true; }); document.querySelectorAll('.done-panel').forEach((d) => { d.hidden = true; })")
        st = await store(pg)
        check("training mode saved as 'training'", any(e["ex"] == "flash" and e["mode"] == "training" for e in st))
        check("balance preset keeps its prefs", any(e["ex"] == "balance" and "bpm" in e["prefs"] for e in st))

        # ---- Kombi capture: only the captured mode's presets, fills the draft only ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await js_click(pg, '[data-remember-diff="leicht"]')
        before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1')).revealBaseS")
        await js_click(pg, "#rememberOpenFixed")
        await save(pg, "rememberReady", "Kombi schwer")  # leicht now
        await pg.evaluate("""() => { const st = JSON.parse(localStorage.getItem('fwmc-nat-saved-v1')); st[st.length-1].prefs.revealBaseS = 0.7; st[st.length-1].prefs.revealStepS = 0.15; localStorage.setItem('fwmc-nat-saved-v1', JSON.stringify(st)); }""")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await js_click(pg, "#natHome .combo-entry-link")
        await pg.click('#comboAddGrid >> text="Positionen merken · Bewegte Positionen"'); await pg.wait_for_timeout(300)
        txt = await pg.inner_text("#rememberReadySavedList") if await pg.is_visible("#rememberReadySavedList") else ""
        check("capture (shuffle): fixed presets hidden", "Kombi schwer" not in txt, txt)
        await pg.click("#rememberReadyBackToHome"); await pg.wait_for_timeout(300)
        await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
        await pg.click('#rememberReadySavedList .bundle-item:has-text("Kombi schwer")'); await pg.wait_for_timeout(300)
        check("capture: tap fills draft, stays on screen", await pg.is_visible("#rememberReady") and not await pg.is_visible("#rememberPlayer"))
        check("capture: title + button kept", "Baustein" in await pg.inner_text("#rememberReadyTitle") and "Baustein übernehmen" in await pg.inner_text("#rememberReadyStartBtn"))
        await pg.screenshot(path="screenshots/nacht2_1007/nat_presets_capture_light.png", full_page=True)
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        rows = await pg.locator("#comboBlockList .chapter-row").count()
        check("capture: block committed", await pg.is_visible("#comboScreen") and rows == 1)
        after = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-remember-prefs-v1')).revealBaseS")
        check("Kombi preset never leaks into own prefs", abs(after - before) < 1e-6, f"{before} -> {after}")

        # ---- Periphere Wahrnehmung: VT preset carries periph settings ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await js_click(pg, "#periphOpenBtn")
        await js_click(pg, '[data-periph-kind="buchstaben"]')
        await save(pg, "vt", "Peripher Buchstaben")
        vt = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-vt-saved-v1') || '[]')")
        check("periph preset has periph block", vt and vt[-1].get("periph", {}).get("periphKind") == "buchstaben", json.dumps(vt[-1] if vt else {})[:200])
        await js_click(pg, '[data-periph-kind="zahlen"]')
        await pg.click('#vtSavedList .bundle-item:has-text("Peripher Buchstaben")'); await pg.wait_for_timeout(400)
        kind = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-webapp-v3')).periphKind")
        check("periph preset restores Zeichen", kind == "buchstaben", kind)

        # ---- screenshots light/dark ----
        for scheme in ("light", "dark"):
            c2 = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", color_scheme=scheme)
            await c2.add_init_script(INIT)
            p2 = await c2.new_page()
            await p2.goto(URL); await p2.wait_for_timeout(300)
            await p2.evaluate("(s) => localStorage.setItem('fwmc-nat-saved-v1', s)", json.dumps(await store(pg)))
            await p2.goto(URL); await p2.wait_for_timeout(400)
            for card, sid in [("#motOpenSpeed", "motReady"), ("#balanceOpenBtn", "balanceReady")]:
                await js_click(p2, card)
                await p2.evaluate("(s) => document.getElementById(s + 'SaveBtn').scrollIntoView({block:'center'})", sid)
                await p2.wait_for_timeout(150)
                await p2.screenshot(path=f"screenshots/nacht2_1007/nat_presets_{sid}_{scheme}.png")
            await c2.close()
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")


if __name__ == "__main__":
    import os
    os.makedirs("screenshots/nacht2_1007", exist_ok=True)
    asyncio.run(main())
