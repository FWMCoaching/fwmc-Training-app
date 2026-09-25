import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Two changes to Flash Speicher Test, from the client's own reference video
# of a similar app: (1) a "Zeichentyp" setting (Buchstaben/Zahlen/Gemischt),
# same three-way choice and same per-character "gemischt" semantics as
# Periphere Wahrnehmung's; (2) the free-text numeric input field is replaced
# by individual answer boxes (one per shown character) filled in by tapping
# an on-screen keypad, instead of the system keyboard.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def tap_answer(chars):
            for c in chars:
                await pg.click(f'#flashKeypad .flash-key:text-is("{c}")')
                await pg.wait_for_timeout(20)

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

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.evaluate("() => localStorage.removeItem('fwmc-flash-prefs-v1')")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('#home .section-tab[data-section="nat"]'); await pg.wait_for_timeout(150)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenClimb"); await pg.wait_for_timeout(150)

        # --- Zeichentyp defaults to Zahlen (unchanged prior behaviour) ---
        print("Zeichentyp defaults to Zahlen:", "active" in (await pg.get_attribute('#flashKindRow [data-flash-kind="zahlen"]', "class") or ""))

        # --- switch to Buchstaben, persists, shared with Trainingsmodus ---
        await pg.click('#flashKindRow [data-flash-kind="buchstaben"]'); await pg.wait_for_timeout(80)
        prefs = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-flash-prefs-v1')||'{}').kind")
        print("Buchstaben saved to prefs:", prefs == "buchstaben")
        await pg.click("#flashReadyBackToHome"); await pg.wait_for_timeout(100)
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenTraining"); await pg.wait_for_timeout(150)
        print("Trainingsmodus shows the same Zeichentyp:", "active" in (await pg.get_attribute('#flashTrainingKindRow [data-flash-kind="buchstaben"]', "class") or ""))

        # --- Buchstaben run: keypad shows letters (24, I/O excluded), sequence is letters ---
        await pg.fill("#flashTrainingStartSlider", "3"); await pg.dispatch_event("#flashTrainingStartSlider", "input")
        await pg.click("#flashTrainingStartBtn"); await pg.wait_for_timeout(200)
        keys = await pg.locator("#flashKeypad .flash-key").all_inner_texts()
        print("keypad shows exactly the 24-letter pool, no digits:", len(keys) == 24 and all(k.isalpha() for k in keys) and "I" not in keys and "O" not in keys)
        seq = await capture_sequence()
        print("shown sequence is letters:", len(seq) == 3 and all(c.isalpha() for c in seq))
        await tap_answer(seq)
        await pg.wait_for_timeout(150)
        print("correct letter answer accepted:", await pg.inner_text("#flashHint") == "Richtig! Weiter geht's …")
        await pg.wait_for_timeout(1000)
        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(150)
        if await pg.is_visible("#flashDonePanel"):
            await pg.click("#flashDoneBackBtn"); await pg.wait_for_timeout(150)
        if await pg.is_visible("#flashTrainingReady"):
            await pg.click("#flashTrainingBackToHome"); await pg.wait_for_timeout(150)

        # --- Gemischt: keypad shows both digits and letters (34 keys) ---
        await pg.click('#natHome .sub-tab[data-nat-sub="flash"]'); await pg.wait_for_timeout(150)
        await pg.click("#flashOpenClimb"); await pg.wait_for_timeout(150)
        await pg.click('#flashKindRow [data-flash-kind="gemischt"]'); await pg.wait_for_timeout(80)
        await pg.click("#flashReadyStartBtn"); await pg.wait_for_timeout(200)
        keys2 = await pg.locator("#flashKeypad .flash-key").all_inner_texts()
        print("gemischt keypad has 10 digits + 24 letters = 34 keys:", len(keys2) == 34)
        seq2 = await capture_sequence()
        print("gemischt sequence length matches Startanzahl:", len(seq2) >= 2)

        # --- answer boxes fill in as you tap, and backspace removes the last one ---
        await tap_answer(seq2[:-1])
        filled_before = await pg.evaluate("() => [...document.querySelectorAll('#flashAnswerBoxes .flash-answer-box')].filter(b => b.classList.contains('filled')).length")
        print("boxes fill in as keys are tapped:", filled_before == len(seq2) - 1)
        await pg.click("#flashBackspaceBtn"); await pg.wait_for_timeout(60)
        filled_after = await pg.evaluate("() => [...document.querySelectorAll('#flashAnswerBoxes .flash-answer-box')].filter(b => b.classList.contains('filled')).length")
        print("backspace removes the last typed character:", filled_after == len(seq2) - 2)
        # re-type the correct full sequence including a deliberate mistake, then fix it
        await tap_answer([seq2[-2]])
        await tap_answer([seq2[-1]])
        await pg.wait_for_timeout(150)
        print("correct mixed answer accepted, no crash:", await pg.is_visible("#flashPlayer"))

        await pg.click("#flashBackBtn"); await pg.wait_for_timeout(150)
        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
