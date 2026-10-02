import asyncio, json, urllib.parse
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

# Audit decisions round 3 (Fabian, 2026-10-02):
# 16 no "Beta" tag in the footer; 17 Kombi-Bausteine can be moved up/down;
# 18 skipping past the end counts a programme as aborted, not completed;
# 19 Flash-Speicher-Test "Konstant" runs a fixed number of rounds with a tally.

FAKE_DEFS = {
    "skip-test": {"name": "Skip-Test", "blocks": [
        {"exercise": "vt-color", "duration": 30, "palette": "ORL"},
        {"exercise": "vt-color", "duration": 30, "palette": "ORL"},
    ]},
}


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def handle_route(route):
            code = urllib.parse.unquote(route.request.url.split("code=")[-1].split("&")[0])
            d = FAKE_DEFS.get(code)
            if d is None:
                await route.fulfill(status=404, body="not found")
            else:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(d))
        await pg.route("**/program?code=*", handle_route)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # ---- 16: no Beta tag ----
        footers = await pg.eval_on_selector_all(".site-footer", "els => els.map(e => e.textContent).join(' ')")
        print("no 'Beta' in any footer:", "Beta" not in footers)
        print("footer still shows Stand:", "Stand:" in footers)

        # ---- 17: Kombi reorder ----
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('#natHome .combo-entry-link'); await pg.wait_for_timeout(300)
        for label in ("Positionen merken · Feste Positionen", "Positionen merken · Bewegte Positionen"):
            await pg.click(f'#comboAddGrid >> text="{label}"'); await pg.wait_for_timeout(300)
            await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        rows = pg.locator("#comboBlockList .chapter-row")
        print("two blocks in the draft:", await rows.count() == 2)
        print("first block has only a down button:",
              await rows.nth(0).locator('[data-move="down"]').count() == 1 and await rows.nth(0).locator('[data-move="up"]').count() == 0)
        print("last block has only an up button:",
              await rows.nth(1).locator('[data-move="up"]').count() == 1 and await rows.nth(1).locator('[data-move="down"]').count() == 0)
        await rows.nth(0).locator('[data-move="down"]').click(); await pg.wait_for_timeout(150)
        first = await rows.nth(0).inner_text()
        second = await rows.nth(1).inner_text()
        print("down swaps the order:", "Bewegte" in first and "Feste" in second)
        await rows.nth(1).locator('[data-move="up"]').click(); await pg.wait_for_timeout(150)
        print("up swaps it back:", "Feste" in await rows.nth(0).inner_text())
        # buttons must not push the row wider than the screen
        overflow = await pg.evaluate("() => { const l = document.getElementById('comboBlockList'); return l.scrollWidth > l.clientWidth + 1; }")
        print("block row fits the phone width:", not overflow)
        await pg.click("#comboBackToHome"); await pg.wait_for_timeout(200)

        # ---- 18: skip to end = aborted ----
        await pg.click('#natHome .section-tab[data-section="visual"]'); await pg.wait_for_timeout(200)
        await pg.fill("#programCodeInput", "skip-test")
        await pg.click("#programGoBtn"); await pg.wait_for_timeout(500)
        await pg.click("#programStartBtn"); await pg.wait_for_timeout(500)
        await pg.click("#liveNextBtn"); await pg.wait_for_timeout(300)
        await pg.click("#liveNextBtn"); await pg.wait_for_timeout(400)
        print("done panel shown after skipping past the end:", await pg.is_visible("#programDonePanel"))
        print("heading says 'Programm beendet':", (await pg.inner_text("#programDonePanel h2")).strip() == "Programm beendet")
        print("summary says Abgebrochen:", "Abgebrochen" in await pg.inner_text("#programDoneSummary"))
        print("check mark hidden:", await pg.is_hidden("#programDonePanel .done-check"))
        hist = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')[0]")
        print("history entry marked aborted:", bool(hist) and hist.get("aborted") is True and hist.get("note") == "abgebrochen")

        # a natural finish (Übung beenden through the last exercise) still counts as completed
        await pg.click("#programAgainBtn"); await pg.wait_for_timeout(500)
        await pg.click("#liveEndBtn"); await pg.wait_for_timeout(400)
        print("Übung beenden leads to the pause screen:", await pg.is_visible("#pauseScreen"))
        await pg.click("#pauseSkipBtn"); await pg.wait_for_timeout(400)
        await pg.click("#liveEndBtn"); await pg.wait_for_timeout(400)
        print("natural end: heading 'Programm geschafft!':", (await pg.inner_text("#programDonePanel h2")).strip() == "Programm geschafft!")
        print("natural end: check mark visible again:", await pg.is_visible("#programDonePanel .done-check"))
        hist = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')[0]")
        print("natural end: history not aborted:", bool(hist) and not hist.get("aborted"))
        await pg.click("#programDoneBackBtn"); await pg.wait_for_timeout(300)

        # ---- 19: Flash Konstant with a fixed round count ----
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenConstant"); await pg.wait_for_timeout(200)
        print("rounds slider visible in Konstant:", await pg.is_visible("#flashRoundsSlider"))
        print("rounds default 20:", await pg.input_value("#flashRoundsSlider") == "20")
        await pg.fill("#flashRoundsSlider", "5"); await pg.dispatch_event("#flashRoundsSlider", "input")
        await pg.fill("#flashConstantSlider", "2"); await pg.dispatch_event("#flashConstantSlider", "input")
        await pg.wait_for_timeout(100)
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(200)
        print("level shows Runde 1/5:", "Runde 1/5" in await pg.inner_text("#flashLevelEl"))

        async def capture_sequence(max_polls=150, poll_ms=40):
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

        async def tap(chars):
            for c in chars:
                await pg.click(f'#flashKeypad .flash-key:text-is("{c}")')

        seq = await capture_sequence()
        await tap(seq if len(seq) == 2 else "99")
        hits = 1 if len(seq) == 2 else 0
        for r in range(2, 6):
            for _ in range(150):
                if await pg.is_visible("#flashInputPanel"):
                    break
                await pg.wait_for_timeout(60)
            if r < 5:
                pass
            await tap("99")
        await pg.wait_for_timeout(1500)
        print("run ends by itself after 5 rounds:", await pg.is_visible("#flashDonePanel"))
        summary = await pg.inner_text("#flashDoneSummary")
        print("summary shows the tally:", f"{hits} von 5 Runden richtig" in summary)
        print("summary does not say 'vorzeitig':", "vorzeitig" not in summary)
        await pg.click("#flashDoneBackBtn"); await pg.wait_for_timeout(200)

        # persistence
        await pg.reload(); await pg.wait_for_timeout(400)
        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(200)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenConstant"); await pg.wait_for_timeout(200)
        print("rounds setting survives reload:", await pg.input_value("#flashRoundsSlider") == "5")

        # Beenden mid-run shows the tally so far, marked as stopped early
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(200)
        for _ in range(150):
            if await pg.is_visible("#flashInputPanel"):
                break
            await pg.wait_for_timeout(60)
        await tap("99")
        await pg.wait_for_timeout(300)
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(300)
        summary = await pg.inner_text("#flashDoneSummary")
        print("early Beenden shows tally marked 'vorzeitig':", "von 1 Runden richtig" in summary and "vorzeitig" in summary)

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
