"""Einheitliche Steuerleiste « ↻ » (Fabian, 2026-10-04): one bar at the
bottom of every running exercise and every pause between Bausteine, same
place and look everywhere, nothing on a stage under it."""
import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
fails = []
def check(name, ok):
    print(f"{name}: {ok}")
    if not ok: fails.append(name)

NAV = "#stepNav"
NAV_RECT = "() => { const r = document.getElementById('stepNav').getBoundingClientRect(); return [r.top, r.bottom, r.height]; }"
# Every visible element of the player (except the bar itself) ends above the bar.
UNDER_JS = """(pid) => {
  const nav = document.getElementById('stepNav').getBoundingClientRect();
  const bad = [];
  document.querySelectorAll('#' + pid + ' button, #' + pid + ' .player-status, #' + pid + ' canvas').forEach(el => {
    if (el.closest('#stepNav')) return;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    if (r.bottom > nav.top + 0.5) bad.push(el.id || el.className || el.tagName);
  });
  return bad;
}"""
HIST = "() => (JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')).length"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-unlocked','true')")
        await pg.goto(URL); await pg.wait_for_timeout(400)
        check("bar hidden on normal screens", await pg.is_hidden(NAV))

        # ---- single Visual-Training exercise: ↻ only, « » shown disabled ----
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(1500)
        check("bar visible in a running exercise", await pg.is_visible(NAV))
        top, bottom, h = await pg.evaluate(NAV_RECT)
        check("bar sits at the bottom", abs(bottom - 844) < 1 and h >= 60)
        check("« and » disabled for a single exercise", await pg.is_disabled("#stepPrevBtn") and await pg.is_disabled("#stepNextBtn"))
        check("↻ enabled", await pg.is_enabled("#stepRestartBtn"))
        bad = await pg.evaluate(UNDER_JS, "player")
        check(f"nothing under the bar (VT) {bad}", bad == [])
        await pg.wait_for_timeout(2500)
        t1 = await pg.inner_text("#timeEl")
        hist0 = await pg.evaluate(HIST)
        await pg.click("#stepRestartBtn"); await pg.wait_for_timeout(600)
        t2 = await pg.inner_text("#timeEl")
        check(f"↻ starts the exercise again ({t1} -> {t2})", await pg.is_visible("#player") and t2 > t1)
        check("restart leaves no history entry", await pg.evaluate(HIST) == hist0)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)

        # ---- Test-Bereich exercise: same bar, ↻ restarts ----
        await pg.goto(URL.replace("visual", "test")); await pg.wait_for_timeout(400)
        await pg.click("#flankerOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click("#flankerReadyStartBtn"); await pg.wait_for_timeout(1200)
        check("bar visible in a Test exercise", await pg.is_visible(NAV))
        bad = await pg.evaluate(UNDER_JS, "flankerPlayer")
        check(f"nothing under the bar (Flanker) {bad}", bad == [])
        await pg.click("#stepRestartBtn"); await pg.wait_for_timeout(500)
        check("Flanker still running after ↻", await pg.is_visible("#flankerPlayer"))
        await pg.click("#flankerPauseBtn"); await pg.wait_for_timeout(200)
        check("bar hidden while paused", await pg.is_hidden(NAV))
        await pg.click("#flankerBackBtn"); await pg.wait_for_timeout(300)

        # ---- Tabata lends its own buttons to the bar ----
        await pg.goto(URL.replace("visual", "workout")); await pg.wait_for_timeout(400)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(200)
        await pg.click("#workoutCircuitAddGrid .ca-plus-btn >> nth=0"); await pg.wait_for_timeout(100)
        await pg.click("#workoutCircuitAddGrid .ca-plus-btn >> nth=1"); await pg.wait_for_timeout(100)
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(600)
        check("Tabata skip button lives in the bar", await pg.evaluate("!!document.querySelector('#stepNav #tabataSkipBtn')"))
        check("Tabata skip button clickable", await pg.is_visible("#tabataSkipBtn"))
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(300)
        check("bar gone after leaving", await pg.is_hidden(NAV))

        # ---- Kraftplan: « ↻ » step by step ----
        await pg.goto(URL.replace("visual", "workout")); await pg.wait_for_timeout(400)
        await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Kniebeugen") .ca-plus-btn'); await pg.wait_for_timeout(80)
        await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Liegestütze") .ca-plus-btn'); await pg.wait_for_timeout(80)
        await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(400)
        # start countdown: » starts right away
        await pg.click("#stepNextBtn"); await pg.wait_for_timeout(300)
        info1 = await pg.text_content("#workoutSetInfo")
        check(f"Kraftplan at set 1 ({info1})", "Übung 1" in info1 and "Satz 1" in info1)
        check("« disabled on the first set", await pg.is_disabled("#stepPrevBtn"))
        await pg.click("#stepNextBtn"); await pg.wait_for_timeout(200)
        info2 = await pg.text_content("#workoutSetInfo")
        check(f"» goes to set 2 ({info2})", "Satz 2" in info2)
        await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(200)
        check("rest shown after a set", await pg.is_visible("#workoutRestBox"))
        await pg.click("#stepRestartBtn"); await pg.wait_for_timeout(200)
        check("↻ in the rest repeats that set", "Satz 2" in await pg.text_content("#workoutSetInfo") and await pg.is_hidden("#workoutRestBox"))
        await pg.click("#stepPrevBtn"); await pg.wait_for_timeout(200)
        check("« goes back to set 1", "Satz 1" in await pg.text_content("#workoutSetInfo"))
        bad = await pg.evaluate(UNDER_JS, "workoutPlayer")
        check(f"nothing under the bar (Kraftplan) {bad}", bad == [])
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(300)

        # ---- Kombi: « » jump between Bausteine, also in the pause ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
        await pg.fill("#rememberComboDurationSlider", "15"); await pg.dispatch_event("#rememberComboDurationSlider", "input")
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click('#comboAddGrid >> text="Blitz-Raster"'); await pg.wait_for_timeout(300)
        await pg.click("#blitzReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(500)
        check("Kombi block 1 (Positionen merken) runs", await pg.is_visible("#rememberPlayer"))
        check("« disabled in the first Baustein", await pg.is_disabled("#stepPrevBtn"))
        hist0 = await pg.evaluate(HIST)
        await pg.click("#stepNextBtn"); await pg.wait_for_timeout(500)
        check("» jumps to Baustein 2 (Blitz-Raster)", await pg.is_visible("#blitzPlayer") and await pg.is_hidden("#rememberPlayer"))
        check("» disabled in the last Baustein", await pg.is_disabled("#stepNextBtn"))
        await pg.click("#stepPrevBtn"); await pg.wait_for_timeout(500)
        check("« jumps back to Baustein 1", await pg.is_visible("#rememberPlayer"))
        await pg.click("#stepRestartBtn"); await pg.wait_for_timeout(500)
        check("↻ starts Baustein 1 again", await pg.is_visible("#rememberPlayer"))
        check("jumps leave no history entry", await pg.evaluate(HIST) == hist0)
        bad = await pg.evaluate(UNDER_JS, "rememberPlayer")
        check(f"nothing under the bar (Remember) {bad}", bad == [])
        await pg.wait_for_timeout(16000)
        check("Kombi pause shown after block 1", await pg.is_visible("#comboTransition"))
        check("bar visible in the Kombi pause", await pg.is_visible(NAV))
        await pg.click("#stepRestartBtn"); await pg.wait_for_timeout(500)
        check("↻ in the pause repeats the Baustein just done", await pg.is_visible("#rememberPlayer") and await pg.is_hidden("#comboTransition"))
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(300)

        check(f"no page errors {errs}", errs == [])
        await b.close()
    print("ALL OK" if not fails else f"FAILED: {fails}")

asyncio.run(main())
