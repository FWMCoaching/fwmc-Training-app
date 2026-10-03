import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Client feedback after the speed-cap question flagged in CLAUDE.md's Flash
# Speicher Test entry: "Darf ruhig noch höher und schneller gehen als Stufe
# 9" - FLASH_SPEED_STEPS raised from 8 to 20 and the per-step floors in
# flashEffectiveStimulusS()/flashEffectiveIntervalS() lowered from
# 0.25s/0.15s to 0.12s/0.08s, so "Konstant" mode keeps genuinely speeding up
# well past the old cap for every starting difficulty (at the OLD floors,
# "mittel"/"schwer" had already plateaued at/before step 8 - only "leicht"
# was still ramping - so raising the ceiling alone would've been cosmetic).
# Drives the real round engine (capture the flashed sequence, tap it back)
# rather than just re-deriving the formula, so it proves the actual on-screen
# behaviour - not just the constants - goes past Tempo-Stufe 9.

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
        await pg.evaluate("() => localStorage.removeItem('fwmc-flash-prefs-v1')")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenConstant"); await pg.wait_for_timeout(150)

        # Fastest allowed start (still well above the floor) and only 2
        # digits/round, so the test can climb many steps quickly.
        await pg.fill("#flashConstantSlider", "2"); await pg.dispatch_event("#flashConstantSlider", "input")
        await pg.click("#flashAdvanced summary"); await pg.wait_for_timeout(100)
        await pg.fill("#flashStimulusSlider", "0.3"); await pg.dispatch_event("#flashStimulusSlider", "input")
        await pg.fill("#flashIntervalSlider", "0.2"); await pg.dispatch_event("#flashIntervalSlider", "input")
        await pg.click("#flashReadyStartBtn")
        print("flashPlayer visible:", await pg.is_visible("#flashPlayer"))

        async def tap_answer(chars):
            for c in chars:
                await pg.click(f'#flashKeypad .flash-key:text-is("{c}")')
                await pg.wait_for_timeout(15)

        async def capture_sequence(max_polls=150, poll_ms=25):
            seq, last_txt, was_visible = [], None, False
            for _ in range(max_polls):
                await pg.wait_for_timeout(poll_ms)
                snap = await pg.evaluate("""() => {
                    const panel = document.getElementById('flashInputPanel');
                    const digit = document.getElementById('flashDigitEl');
                    return { inputVisible: !panel.hidden, digitVisible: !digit.hidden, text: digit.textContent };
                }""")
                if snap["inputVisible"]:
                    return seq
                if snap["digitVisible"]:
                    if not was_visible or snap["text"] != last_txt:
                        seq.append(snap["text"]); last_txt = snap["text"]
                    was_visible = True
                else:
                    was_visible = False
            return seq

        levels = []
        for round_i in range(16):
            seq = await capture_sequence()
            if len(seq) != 2:
                break
            await tap_answer(seq)
            await pg.wait_for_timeout(120)
            level_text = await pg.inner_text("#flashLevelEl")
            levels.append(level_text)

        print("Tempo-Stufe progression:", levels)
        max_step_seen = max(int(t.split("Tempo-Stufe ")[1]) for t in levels if "Tempo-Stufe" in t)
        print("max Tempo-Stufe reached:", max_step_seen)
        assert max_step_seen > 9, f"expected to climb past the old cap of Tempo-Stufe 9, only reached {max_step_seen}"
        assert max_step_seen <= 21, f"Tempo-Stufe {max_step_seen} exceeds the new ceiling of 21 (FLASH_SPEED_STEPS=20)"

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
