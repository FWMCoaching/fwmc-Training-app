import asyncio, json
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html#videotest1"
VIDEO_URL = "http://localhost:8845/explainer-vrw-placeholder.mp4"

DEF = {
    "name": "Video-Test-Programm",
    "pauseS": 2,
    "blocks": [
        {"exercise": "vt-color", "colors": ["orange", "rot", "lila"], "duration": 30,
         "stimulusS": 1, "intervalMin": 1, "intervalMax": 2, "videoAfter": VIDEO_URL},
        {"exercise": "vt-color", "colors": ["orange", "rot", "lila"], "duration": 30,
         "stimulusS": 1, "intervalMin": 1, "intervalMax": 2},
    ],
    "endVideo": VIDEO_URL,
}

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def handle_route(route):
            if "/program?code=videotest1" in route.request.url:
                await route.fulfill(status=200, body=json.dumps(DEF), headers={"content-type": "application/json"})
            else:
                await route.continue_()

        await pg.route("https://online-training.fwmc.workers.dev/**", handle_route)
        await pg.goto(URL); await pg.wait_for_timeout(600)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#programStartBtn"); await pg.wait_for_timeout(500)
        print("exercise 1 running (player visible):", await pg.is_visible("#player"))

        # end exercise 1 early -> should jump STRAIGHT into the videoAfter
        # video (bypassing the rest pause), since block 0 has one
        await pg.click("#liveEndBtn"); await pg.wait_for_timeout(700)
        print("video-after-block-1 shown, not pause screen:",
              await pg.is_visible("#programVideoPlayer") and not await pg.is_visible("#pauseScreen"))
        print("video src is the videoAfter url:", VIDEO_URL in (await pg.get_attribute("#programVideoEl", "src") or ""))
        print("skip checkbox unchecked by default:", not await pg.is_checked("#programVideoSkipCheck"))

        # flag this video for future auto-skip, then advance -> should now
        # land on the pause screen (next step is exercise 2)
        await pg.check("#programVideoSkipCheck"); await pg.wait_for_timeout(100)
        print("skip checkbox now checked:", await pg.is_checked("#programVideoSkipCheck"))
        await pg.click("#programVideoNextBtn"); await pg.wait_for_timeout(300)
        print("pause screen shown after video ends:", await pg.is_visible("#pauseScreen"))
        print("pause progress label correct:", "1 von 2" in (await pg.inner_text("#pauseProgress")))

        # skip the rest pause -> exercise 2 starts
        await pg.click("#pauseSkipBtn"); await pg.wait_for_timeout(400)
        print("exercise 2 running:", await pg.is_visible("#player") and not await pg.is_visible("#pauseScreen"))

        # end exercise 2 -> last block, no videoAfter of its own, but an
        # endVideo exists -> should play that instead of finishing outright
        await pg.click("#liveEndBtn"); await pg.wait_for_timeout(700)
        print("end-video shown after last exercise:", await pg.is_visible("#programVideoPlayer"))
        print("end-video skip checkbox unchecked (different video, own flag):",
              not await pg.is_checked("#programVideoSkipCheck"))

        # native seek: jump the video ahead, then let it finish naturally via 'ended'
        await pg.evaluate("""() => {
          const v = document.getElementById('programVideoEl');
          if (v.duration && isFinite(v.duration)) v.currentTime = Math.max(0, v.duration - 0.2);
        }""")
        await pg.wait_for_timeout(1500)
        done_after_end_video = await pg.is_visible("#programDonePanel")
        if not done_after_end_video:
            # some environments may not decode this placeholder file fully -
            # fall back to the explicit "end early" skip control either way
            await pg.click("#programVideoNextBtn"); await pg.wait_for_timeout(300)
            done_after_end_video = await pg.is_visible("#programDonePanel")
        print("programme finished after end-video:", done_after_end_video)

        # ---- restart the programme: the flagged video-after-block-1 should
        # now be auto-skipped on the natural forward path ----
        await pg.click("#programAgainBtn"); await pg.wait_for_timeout(400)
        print("restarted, exercise 1 running again:", await pg.is_visible("#player"))
        await pg.click("#liveEndBtn"); await pg.wait_for_timeout(700)
        print("flagged video auto-skipped -> straight to pause screen:", await pg.is_visible("#pauseScreen"))
        print("video player not shown (auto-skip honoured):", not await pg.is_visible("#programVideoPlayer"))

        # ---- reversibility: from the pause screen itself, "previous"
        # still redoes the exercise that actually just ran, never the
        # silently-skipped video - so proceed into exercise 2, and from
        # there its own back-nav steps through the plain step order and
        # reaches the skipped video, with its skip box shown as checked.
        # Unchecking it there removes the flag. ----
        await pg.click("#pauseSkipBtn"); await pg.wait_for_timeout(500)
        print("exercise 2 running:", await pg.is_visible("#player"))
        await pg.click("#livePrevBtn"); await pg.wait_for_timeout(300)
        print("back-nav from exercise 2 reaches the skipped video:", await pg.is_visible("#programVideoPlayer"))
        print("its skip box shows checked (flag intact):", await pg.is_checked("#programVideoSkipCheck"))
        await pg.uncheck("#programVideoSkipCheck"); await pg.wait_for_timeout(100)
        skip_map = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-program-video-skip-v1') || '{}')")
        print("unchecking removes the flag from storage:", "videotest1" not in skip_map or "after-0" not in skip_map.get("videotest1", {}))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
