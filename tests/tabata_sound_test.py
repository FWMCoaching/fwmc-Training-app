import asyncio
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 900})
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.evaluate("() => { localStorage.removeItem('fwmc-workout-circuit-v1'); localStorage.removeItem('fwmc-workout-sound-v1'); }")
        await pg.reload(); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        # instrument playWorkoutBeep to log calls without needing real audio hardware
        await pg.evaluate("""() => {
            window.__beeps = [];
            const check = setInterval(() => {
                if (window.playWorkoutBeepHook) { clearInterval(check); return; }
            }, 50);
        }""")

        await pg.click('[data-section="workout"]'); await pg.wait_for_timeout(200)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(200)

        print("sound toggle visible on ready screen:", await pg.is_visible("#workoutTabataSoundToggleBtn"))
        print("default sound icon is speaker:", "\U0001F50A" in await pg.inner_text("#workoutTabataSoundToggleBtn"))
        await pg.click("#workoutTabataSoundToggleBtn"); await pg.wait_for_timeout(100)
        print("icon switches to muted after toggle:", "\U0001F507" in await pg.inner_text("#workoutTabataSoundToggleBtn"))
        print("button gets is-off class:", "is-off" in (await pg.get_attribute("#workoutTabataSoundToggleBtn", "class") or ""))
        await pg.click("#workoutTabataSoundToggleBtn"); await pg.wait_for_timeout(100)
        print("icon back to speaker after second toggle:", "\U0001F50A" in await pg.inner_text("#workoutTabataSoundToggleBtn"))

        # build a tiny 1-item circuit, shrink work time via localStorage, run it
        await pg.locator("#workoutCircuitAddGrid .ca-plus-btn").nth(0).click(); await pg.wait_for_timeout(80)
        await pg.evaluate("""() => {
            const raw = localStorage.getItem('fwmc-workout-circuit-v1');
            const prefs = JSON.parse(raw);
            prefs.items = prefs.items.map(it => ({...it, workS: 4}));
            localStorage.setItem('fwmc-workout-circuit-v1', JSON.stringify(prefs));
        }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click('[data-section="workout"]'); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        await pg.click("#workoutCircuitAdvanced summary"); await pg.wait_for_timeout(100)
        await pg.evaluate("() => { document.getElementById('workoutCircuitPrepSlider').value = 3; document.getElementById('workoutCircuitPrepSlider').dispatchEvent(new Event('input')); }")
        await pg.wait_for_timeout(100)

        # monkey-patch AudioContext BEFORE starting, to count beeps by duration
        await pg.evaluate("""() => {
            window.__beepLog = [];
            const OrigCtx = window.AudioContext || window.webkitAudioContext;
            class FakeGain { constructor(){ this.gain = { setValueAtTime(){}, exponentialRampToValueAtTime(){} }; } connect(){} }
            class FakeOsc {
                constructor(){ this.frequency = { value: 0 }; }
                connect(){}
                start(){}
                stop(t){ window.__beepLog.push({ freq: this.frequency.value }); }
            }
            class FakeCtx {
                constructor(){ this.state = 'running'; this.currentTime = 0; this.destination = {}; }
                createOscillator(){ return new FakeOsc(); }
                createGain(){ return new FakeGain(); }
                resume(){}
            }
            window.AudioContext = FakeCtx;
            window.webkitAudioContext = FakeCtx;
        }""")

        print("sound icon still speaker (enabled) before start:", "\U0001F50A" in await pg.inner_text("#workoutTabataSoundToggleBtn"))
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(200)
        print("tabata player visible:", await pg.is_visible("#workoutTabataView"))
        print("sound toggle visible during live play:", await pg.is_visible("#tabataSoundToggleBtn"))

        # wait through: prep(3s) -> long beep(work start) -> work(4s) with short beeps at 3,2,1 -> long beep(work end, no more items/sets/cooldown) -> done
        await pg.wait_for_function("() => !document.getElementById('workoutDonePanel').hidden", timeout=10000)
        beeps = await pg.evaluate("() => window.__beepLog")
        print("total beeps recorded:", len(beeps))
        long_beeps = [x for x in beeps if x["freq"] == 1180]
        short_beeps = [x for x in beeps if x["freq"] == 880]
        print("long beeps (work start + work end):", len(long_beeps))
        print("short beeps (3-2-1 countdown into work):", len(short_beeps))
        # expect: 3 short (prep->work countdown) + 1 long (work starts) + 1 long (work ends, session finishes) = 2 long, 3 short minimum
        print("got at least 1 long beep for work-start:", len(long_beeps) >= 1)
        print("got the final long beep for work-end:", len(long_beeps) >= 2)
        print("got short countdown beeps:", len(short_beeps) >= 1)

        await pg.click('#workoutRating [data-rate="4"]')
        await pg.click("#workoutDoneBackBtn"); await pg.wait_for_timeout(150)

        # muted run -> zero beeps (toggle from the ready screen this time)
        await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
        await pg.click("#workoutTabataSoundToggleBtn"); await pg.wait_for_timeout(50)
        print("sound now off on ready screen:", "\U0001F507" in await pg.inner_text("#workoutTabataSoundToggleBtn"))
        await pg.evaluate("() => { window.__beepLog = []; }")
        await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(200)
        await pg.wait_for_function("() => !document.getElementById('workoutDonePanel').hidden", timeout=10000)
        beeps_muted = await pg.evaluate("() => window.__beepLog")
        print("zero beeps when muted:", len(beeps_muted) == 0, len(beeps_muted))

        print("FINAL ERRORS:", errors)
        await b.close()

asyncio.run(main())
