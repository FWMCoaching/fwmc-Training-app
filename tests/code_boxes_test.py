import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

# Fake remote defs, served in place of the real Cloudflare worker via
# page.route() - lets this test exercise the movement-plan/cardio-plan/
# NAT-via-default-type dispatch end-to-end without a live coach-authored
# code, and without touching the real CODE_API.
FAKE_DEFS = {
    "mv-solo-test": {
        "type": "movement-plan", "name": "Test Bewegungsplan",
        "movements": ["armL-heben", "armR-heben"], "bpm": 90, "durationMin": 1,
        "preview": 3, "mirror": True, "showLabel": True,
    },
    "mv-bundle-test": {
        "type": "movement-bundle", "name": "Test Bewegungsprogramme",
        "programs": [{"label": "Plan A", "movements": ["armL-heben", "armR-heben"], "bpm": 90, "durationMin": 1, "preview": 3, "mirror": True, "showLabel": True}],
    },
    "cd-solo-test": {
        "type": "cardio-plan", "name": "Test Cardio-Einheit",
        "items": [{"activity": "joggen", "durationS": 60, "label": "", "interval": None}],
    },
    "cd-bundle-test": {
        "type": "cardio-bundle", "name": "Test Cardio-Einheiten",
        "programs": [{"label": "Einheit A", "items": [{"activity": "joggen", "durationS": 60, "label": "", "interval": None}]}],
    },
    "nat-solo-test": {
        "name": "Test NAT-Programm",
        "blocks": [{"exercise": "periph-flash", "duration": 15}],
    },
}

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def handle_route(route):
            url = route.request.url
            code = url.split("code=")[-1] if "code=" in url else ""
            code = urllib.parse.unquote(code.split("&")[0])
            def_ = FAKE_DEFS.get(code)
            if def_ is None:
                await route.fulfill(status=404, body="not found")
            else:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(def_))

        await pg.route("**/program?code=*", handle_route)

        # Screens like movementProgramIntro/cardioReady/bundleOverview have
        # no nav bar of their own (same as workoutTabataReady) - always jump
        # sections from a screen that has one (scoped, since every home
        # screen repeats the whole nav bar verbatim - a bare selector matches
        # 7 elements and may resolve to a hidden copy).
        async def nav(current_home, sec):
            await pg.click(f'#{current_home} .section-tab[data-section="{sec}"]')
            await pg.wait_for_timeout(200)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- basic presence + bad-code path stays on own home screen ----
        await nav("home", "movement")
        for sec, home, input_id, go_id, err_id in [
            ("movement", "movementHome", "movementProgramCodeInput", "movementProgramGoBtn", "movementProgramError"),
            ("cardio", "cardioHome", "cardioProgramCodeInput", "cardioProgramGoBtn", "cardioProgramError"),
            ("nat", "natHome", "natProgramCodeInput", "natProgramGoBtn", "natProgramError"),
        ]:
            print(f"{sec}: code input visible:", await pg.is_visible(f"#{input_id}"))
            await pg.fill(f"#{input_id}", "definitely-not-a-real-code")
            await pg.click(f"#{go_id}"); await pg.wait_for_timeout(600)
            print(f"{sec}: error shown for bad code:", await pg.is_visible(f"#{err_id}"))
            print(f"{sec}: stayed on own home after bad code:", await pg.is_visible(f"#{home}"))
            if sec == "movement": await nav("movementHome", "cardio")
            elif sec == "cardio": await nav("cardioHome", "nat")
        # now on natHome

        await nav("natHome", "movement")
        # ==== Movement coach-plan: solo ====
        await pg.fill("#movementProgramCodeInput", "mv-solo-test")
        await pg.click("#movementProgramGoBtn"); await pg.wait_for_timeout(500)
        print("movement solo: intro screen shown:", await pg.is_visible("#movementProgramIntro"))
        print("movement solo: title shown:", "Test Bewegungsplan" in await pg.inner_text("#movementProgramTitle"))
        await pg.click("#movementProgramStartBtn"); await pg.wait_for_timeout(400)
        print("movement solo: player running:", await pg.is_visible("#movementPlayer"))
        # abort mid-run -> back to the SAME programme intro (not the generic builder)
        await pg.click("#movementBackBtn"); await pg.wait_for_timeout(300)
        print("movement solo: abort returns to its own intro:", await pg.is_visible("#movementProgramIntro"))
        await pg.click("#movementProgramBackToHome"); await pg.wait_for_timeout(200)
        print("movement solo: back-to-home lands on movementHome:", await pg.is_visible("#movementHome"))

        # ==== Movement coach-plan: bundle ====
        await pg.fill("#movementProgramCodeInput", "mv-bundle-test")
        await pg.click("#movementProgramGoBtn"); await pg.wait_for_timeout(500)
        print("movement bundle: bundle overview shown:", await pg.is_visible("#movementBundleOverview"))
        await pg.click("#movementBundleList .bundle-item"); await pg.wait_for_timeout(300)
        print("movement bundle: opens intro for the picked plan:", await pg.is_visible("#movementProgramIntro"))
        await pg.click("#movementProgramBackToHome"); await pg.wait_for_timeout(300)
        print("movement bundle: back from intro returns to bundle list:", await pg.is_visible("#movementBundleOverview"))
        await pg.click("#movementBundleBackToHome"); await pg.wait_for_timeout(200)
        print("movement bundle: back-to-home lands on movementHome:", await pg.is_visible("#movementHome"))

        await nav("movementHome", "cardio")
        # ==== Cardio coach-plan: solo, run to completion ====
        await pg.fill("#cardioProgramCodeInput", "cd-solo-test")
        await pg.click("#cardioProgramGoBtn"); await pg.wait_for_timeout(500)
        print("cardio solo: intro screen shown:", await pg.is_visible("#cardioProgramIntro"))
        print("cardio solo: chapter list shows activity:", "Joggen" in await pg.inner_text("#cardioProgramChapterList"))
        await pg.click("#cardioProgramStartBtn"); await pg.wait_for_timeout(400)
        print("cardio solo: player running:", await pg.is_visible("#cardioPlayer"))
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(300)
        print("cardio solo: abort returns to its own intro:", await pg.is_visible("#cardioProgramIntro"))
        await pg.click("#cardioProgramStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(600)  # only 1 block -> should finish
        print("cardio solo: done panel shown after finishing:", await pg.is_visible("#cardioDonePanel"))
        await pg.click("#cardioDoneBackBtn"); await pg.wait_for_timeout(300)
        print("cardio solo: done-back lands on cardioHome:", await pg.is_visible("#cardioHome"))

        # ==== Cardio coach-plan: bundle ====
        await pg.fill("#cardioProgramCodeInput", "cd-bundle-test")
        await pg.click("#cardioProgramGoBtn"); await pg.wait_for_timeout(500)
        print("cardio bundle: bundle overview shown:", await pg.is_visible("#cardioBundleOverview"))
        await pg.click("#cardioBundleList .bundle-item"); await pg.wait_for_timeout(300)
        print("cardio bundle: opens intro for the picked unit:", await pg.is_visible("#cardioProgramIntro"))
        await pg.click("#cardioProgramBackToHome"); await pg.wait_for_timeout(300)
        print("cardio bundle: back from intro returns to bundle list:", await pg.is_visible("#cardioBundleOverview"))
        await pg.click("#cardioBundleBackToHome"); await pg.wait_for_timeout(200)
        print("cardio bundle: back-to-home lands on cardioHome:", await pg.is_visible("#cardioHome"))

        await nav("cardioHome", "nat")
        # ==== NAT via the shared default/"bundle" pipeline: solo programme,
        # ctx-aware back-routing (must land on natHome, not Visual home) ====
        await pg.fill("#natProgramCodeInput", "nat-solo-test")
        await pg.click("#natProgramGoBtn"); await pg.wait_for_timeout(500)
        print("nat solo: programIntro shown (shared screen):", await pg.is_visible("#programIntro"))
        print("nat solo: title shown:", "Test NAT-Programm" in await pg.inner_text("#programTitle"))
        await pg.click("#programBackToHome"); await pg.wait_for_timeout(300)
        print("nat solo: back-from-intro lands on natHome (not Visual home):", await pg.is_visible("#natHome") and not await pg.is_visible("#home"))

        await pg.fill("#natProgramCodeInput", "nat-solo-test")
        await pg.click("#natProgramGoBtn"); await pg.wait_for_timeout(500)
        await pg.click("#programStartBtn"); await pg.wait_for_timeout(500)
        print("nat solo: exercise running:", await pg.is_visible("#player"))
        # abortTraining() for a running programme always returns to the
        # (already ctx-correct) programIntro screen, same as Visual/Breath -
        # not straight to natHome.
        await pg.click("#backBtn"); await pg.wait_for_timeout(400)
        print("nat solo: abort mid-exercise returns to programIntro:", await pg.is_visible("#programIntro"))
        await pg.click("#programBackToHome"); await pg.wait_for_timeout(300)
        print("nat solo: then back-to-home lands on natHome (not Visual home):", await pg.is_visible("#natHome") and not await pg.is_visible("#home"))

        # ---- Visual's own code box still lands on Visual home as before
        # (regression check: ctx-threading must not break the original path) ----
        await nav("natHome", "visual")
        await pg.fill("#programCodeInput", "definitely-not-a-real-code")
        await pg.click("#programGoBtn"); await pg.wait_for_timeout(600)
        print("visual: bad code still stays on Visual home:", await pg.is_visible("#home"))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
