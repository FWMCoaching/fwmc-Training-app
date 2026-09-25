import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"
OUT = "screenshots/"

# Blitz-Raster: N grid cells light up simultaneously and briefly, then go
# dark; the client taps back exactly those cells, order doesn't matter -
# unlike Remember (ordered recall of a layout you have time to study).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="blitz"]'); await pg.wait_for_timeout(150)
        print("blitz panel visible:", await pg.is_visible("#natBlitzPanel"))
        await pg.click("#blitzOpenBtn"); await pg.wait_for_timeout(150)
        print("blitzReady visible:", await pg.is_visible("#blitzReady"))

        # --- grid size <-> Bereich visibility ---
        print("zone group visible at default 4x4:", await pg.is_visible("#blitzZoneGroup"))
        await pg.click('#blitzGridSizeRow [data-blitz-grid="3"]'); await pg.wait_for_timeout(80)
        print("zone group hidden at 3x3:", await pg.is_hidden("#blitzZoneGroup"))
        await pg.click('#blitzGridSizeRow [data-blitz-grid="5"]'); await pg.wait_for_timeout(80)
        print("zone group visible again at 5x5:", await pg.is_visible("#blitzZoneGroup"))

        # --- zone multi-select: min-one-zone rule + Start disabled at zero ---
        await pg.click("#blitzZoneAllBtn"); await pg.wait_for_timeout(80)
        print("start disabled at zero zones:", await pg.get_attribute("#blitzReadyStartBtn", "disabled") is not None)
        await pg.click('#blitzZoneGrid [data-zone="tl"]'); await pg.wait_for_timeout(80)
        print("start re-enabled with one zone:", await pg.get_attribute("#blitzReadyStartBtn", "disabled") is None)
        await pg.click("#blitzAdvanced summary"); await pg.wait_for_timeout(100)
        print("start-count max shrinks when restricted to one zone (< 16):", int(await pg.get_attribute("#blitzStartSlider", "max")) < 16)
        await pg.click("#blitzZoneAllBtn"); await pg.wait_for_timeout(80)  # back to all zones

        # --- background: swatches, cross-domain source list, transfer ---
        print("bg swatch count:", await pg.locator("#blitzBgColorPicker .color-swatch").count())
        print("bg source row lists VT and Remember (not itself):", await pg.locator("#blitzBgSourceRow button").all_inner_texts())

        # --- run a round: correct-tap success path ---
        await pg.fill("#blitzFlashSlider", "1.2"); await pg.dispatch_event("#blitzFlashSlider", "input")
        await pg.fill("#blitzStartSlider", "3"); await pg.dispatch_event("#blitzStartSlider", "input")
        await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(200)
        print("blitzPlayer visible:", await pg.is_visible("#blitzPlayer"))
        cell_count = await pg.locator("#blitzGrid .blitz-cell").count()
        print("cell count (5x5=25):", cell_count)
        lit_count = await pg.locator("#blitzGrid .blitz-cell.lit").count()
        print("lit cells during flash == startCount:", lit_count == 3)
        lit_indices = await pg.evaluate("() => Array.from(document.querySelectorAll('#blitzGrid .blitz-cell')).map((el,i)=>el.classList.contains('lit')?i:-1).filter(i=>i>=0)")
        await pg.screenshot(path=OUT + "blitz_flash.png")

        await pg.wait_for_timeout(1400)
        print("hint switches to input phase:", await pg.inner_text("#blitzHint"))
        await pg.screenshot(path=OUT + "blitz_input.png")
        cells = await pg.locator("#blitzGrid .blitz-cell").all()
        for i in lit_indices:
            await cells[i].click(); await pg.wait_for_timeout(80)
        print("hint after all correctly tapped:", await pg.inner_text("#blitzHint"))
        await pg.wait_for_timeout(1100)
        print("level advanced to 4 for next round:", await pg.inner_text("#blitzLevelEl"))

        # --- wrong-tap path: reveals the full lit set, applies error mode ---
        # "lit" only exists as a class during the flash phase (by design -
        # during input, tapped-but-unrevealed cells look identical whether
        # they were lit or not), so capture the next round's lit indices
        # while it's still flashing (we're already mid-flash at this point,
        # the level-4 round having started ~900ms after the last success).
        lit_indices2 = await pg.evaluate("() => Array.from(document.querySelectorAll('#blitzGrid .blitz-cell')).map((el,i)=>el.classList.contains('lit')?i:-1).filter(i=>i>=0)")
        await pg.wait_for_timeout(1300)  # past this round's flash -> input phase
        cells2 = await pg.locator("#blitzGrid .blitz-cell").all()
        wrong_index = next(i for i in range(25) if i not in lit_indices2)
        await cells2[wrong_index].click(); await pg.wait_for_timeout(150)
        print("hint after wrong tap (default reset2):", await pg.inner_text("#blitzHint"))
        print("full lit set revealed as correct:", await pg.locator("#blitzGrid .blitz-cell.correct").count() == len(lit_indices2))
        print("wrong-tapped cell marked:", await pg.locator("#blitzGrid .blitz-cell.wrong").count() == 1)

        # --- pause / live-adjust / resume ---
        await pg.wait_for_timeout(1800)
        await pg.click("#blitzPauseBtn"); await pg.wait_for_timeout(150)
        print("pause overlay visible:", await pg.is_visible("#blitzPauseOverlay"))
        print("pause button hidden while paused:", await pg.is_hidden("#blitzPauseBtn"))
        hint_before = await pg.inner_text("#blitzHint")
        await pg.wait_for_timeout(1400)
        print("frozen while paused:", hint_before == await pg.inner_text("#blitzHint"))
        await pg.click('#blitzPauseBgColorPicker .color-swatch[data-key="lila"]'); await pg.wait_for_timeout(80)
        bg = await pg.evaluate("() => document.getElementById('blitzStage').style.background")
        intensity_pct = await pg.inner_text("#blitzPauseBgValue")
        print("bg updated live while paused (0%->50% jump on colour pick):", bg not in ("", "rgb(255, 255, 255)"), intensity_pct)
        await pg.click("#blitzResumeBtn"); await pg.wait_for_timeout(150)
        print("pause overlay hidden after resume:", await pg.is_hidden("#blitzPauseOverlay"))
        print("pause button visible again:", await pg.is_visible("#blitzPauseBtn"))

        # --- Beenden while paused doesn't leave the overlay stuck ---
        await pg.click("#blitzPauseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#blitzBackBtn"); await pg.wait_for_timeout(150)
        print("done panel visible (progress was made):", await pg.is_visible("#blitzDonePanel"))
        print("done summary mentions a level:", "Stufe" in (await pg.inner_text("#blitzDoneSummary")))
        await pg.click("#blitzDoneBackBtn"); await pg.wait_for_timeout(150)
        print("back at natHome:", await pg.is_visible("#natHome"))

        # --- a fresh run has no stuck overlay / pause button hidden state ---
        await pg.click('#natHome .sub-tab[data-nat-sub="blitz"]'); await pg.wait_for_timeout(150)
        await pg.click("#blitzOpenBtn"); await pg.wait_for_timeout(150)
        await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(200)
        print("fresh run: pause overlay hidden:", await pg.is_hidden("#blitzPauseOverlay"))
        print("fresh run: pause button visible:", await pg.is_visible("#blitzPauseBtn"))
        # Beenden with zero cleared this run returns straight to natHome, no done panel
        await pg.click("#blitzBackBtn"); await pg.wait_for_timeout(150)
        print("Beenden with no progress skips done panel:", await pg.is_hidden("#blitzDonePanel"))

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
