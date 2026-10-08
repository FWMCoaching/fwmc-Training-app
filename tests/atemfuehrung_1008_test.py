import asyncio, json, os
from playwright.async_api import async_playwright

# Pausen mit Atemführung (Idee 16, Fabian 08.10.): Grundeinstellungen switch
# "Pausen mit Atemführung" (masterPrefs.pauseBreath, default off). When on, the
# pauses of the Kombi-Programm (between Bausteine), Krafttraining (Tabata/Zirkel
# rest + Satzpause, Kraftplan rest between sets/exercises) and Ausdauertraining
# (pauses between activities) show the same breathing circle as the
# trainer-programme pause (.breath + .breath-circle + "Einatmen"/"Ausatmen").
# Pauses under 10 s, "Bereit machen", the cool-down and the switch off keep the
# plain countdown. Fabian 08.10.: the remaining pause time stays clearly
# visible and readable (full size, inside the circle, never hidden or tiny).
# Persistence across reload, dark mode colours, no page/console errors.
# Run from tests/ with a dev server (FWMC_PORT, default 8845).
# Screenshots: tests/screenshots/paket_h/.

PORT = os.environ.get("FWMC_PORT", "8845")
URL = f"http://localhost:{PORT}/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "paket_h")
os.makedirs(SHOTS, exist_ok=True)

QUIET = "localStorage.setItem('fwmc-workout-sound-v1', JSON.stringify({enabled:false}));"
def master(on, pause=20):
    return f"localStorage.setItem('fwmc-master-v1', JSON.stringify({{startCountdown:false, pauseBreath:{str(on).lower()}, defaultPauseS:{pause}}}));"

fails = []
def check(label, cond, info=""):
    print(f"{label}: {bool(cond)}" + (f"  [{info}]" if not cond and info != "" else ""))
    if not cond: fails.append(label)

# State of one guest host: guide on? label, countdown readable inside the circle.
STATE_JS = """([host, cd, label]) => {
  const h = document.getElementById(host), c = document.getElementById(cd), l = document.getElementById(label);
  const hr = h.getBoundingClientRect(), cr = c.getBoundingClientRect();
  const circle = h.querySelector('.breath-circle');
  const cs = getComputedStyle(c);
  return { on: h.classList.contains('breath') && h.classList.contains('run'),
    circleShown: getComputedStyle(circle).display !== 'none' && circle.getBoundingClientRect().width > 100,
    label: l.hidden ? null : l.textContent, labelVisible: !l.hidden && l.getBoundingClientRect().height > 0,
    cdText: c.textContent.trim(), cdFont: parseFloat(cs.fontSize), cdVisible: cr.width > 0 && cr.height > 0 && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.9,
    cdInside: cr.left >= hr.left - 1 && cr.right <= hr.right + 1 && cr.top >= hr.top - 1 && cr.bottom <= hr.bottom + 1,
    cdOnScreen: cr.top >= 0 && cr.bottom <= innerHeight && cr.left >= 0 && cr.right <= innerWidth,
    cdColor: cs.color, labelColor: getComputedStyle(l).color,
    scrollW: document.documentElement.scrollWidth, w: innerWidth };
}"""

async def state(pg, host, cd, label):
    return await pg.evaluate(STATE_JS, [host, cd, label])

def check_readable(name, s):
    # Fabian 08.10.: the remaining pause time stays clearly readable while the circle runs.
    check(f"{name}: countdown visible + readable (>= 40 px, on screen)", s["cdVisible"] and s["cdFont"] >= 40 and s["cdOnScreen"] and s["cdText"] != "", s)
    check(f"{name}: countdown sits inside the circle", s["cdInside"], s)

async def new_page(b, errors, seed, dark=False, w=390, h=844):
    ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block", color_scheme="dark" if dark else "light")
    await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true');" + seed)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    await pg.clock.install()
    await pg.goto(URL); await pg.wait_for_timeout(300)
    return pg

async def tick(pg, ms):
    await pg.clock.fast_forward(ms)
    await pg.clock.run_for(400)

CIRCUIT = lambda rest, setrest: ("localStorage.setItem('fwmc-workout-circuit-v1', JSON.stringify({items:[{exercise:'kniebeuge',workS:20},{exercise:'liegestuetz',workS:20}],"
                                 f"restS:{rest},sets:2,setRestS:{setrest},defaultWorkS:20,prepS:3,cooldownS:0}}));")
CARDIO = ("localStorage.setItem('fwmc-cardio-v1', JSON.stringify({items:[{activity:'joggen',durationS:60,pauseAfterS:20,label:''},"
          "{activity:'walking',durationS:60,pauseAfterS:5,label:''},{activity:'rad',durationS:60,label:''}]}));")

async def start_tabata(pg):
    await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
    await pg.click("#workoutTabataStartCard"); await pg.wait_for_timeout(150)
    await pg.click("#workoutTabataStartBtn"); await pg.wait_for_timeout(300)

async def start_cardio(pg):
    await pg.click('#home .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(150)
    await pg.click("#cardioStartCard"); await pg.wait_for_timeout(150)
    await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(300)

TAB = ("tabataBreath", "tabataCountdown", "tabataBreathLabel")
REST = ("workoutRestBreath", "workoutRestCountdown", "workoutRestBreathLabel")
CAR = ("cardioBreath", "cardioCountdown", "cardioBreathLabel")
KOM = ("comboTransitionBreath", "comboTransitionCountdown", "comboTransitionBreathLabel")

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---------- Grundeinstellungen: switch, default off, persists ----------
        pg = await new_page(b, errors, QUIET + "if(!localStorage.getItem('fwmc-master-v1'))localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
        await pg.click("#home .master-settings-btn"); await pg.wait_for_timeout(200)
        box = pg.locator("#masterPauseBreathCheck")
        check("switch: present in the Grundeinstellungen", await box.count() == 1)
        check("switch: default off", not await box.is_checked())
        lab = await pg.evaluate("document.getElementById('masterPauseBreathCheck').closest('.group').querySelector('.group-label').textContent")
        check("switch: sits in the pause group", "Pause" in lab, lab)
        row_h = await pg.evaluate("document.getElementById('masterPauseBreathCheck').closest('label').getBoundingClientRect().height")
        check("switch: row >= 44 px", row_h >= 44, row_h)
        await pg.locator("#masterPauseBreathCheck").scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "atem_switch_390_light.png"))
        await box.check(); await pg.wait_for_timeout(100)
        stored = json.loads(await pg.evaluate("localStorage.getItem('fwmc-master-v1')"))
        check("switch: stored as pauseBreath true", stored.get("pauseBreath") is True, stored)
        await pg.reload(); await pg.wait_for_timeout(300)
        await pg.click("#home .master-settings-btn"); await pg.wait_for_timeout(200)
        check("switch: still on after reload", await pg.locator("#masterPauseBreathCheck").is_checked())
        await pg.locator("#masterPauseBreathCheck").uncheck(); await pg.wait_for_timeout(100)
        stored = json.loads(await pg.evaluate("localStorage.getItem('fwmc-master-v1')"))
        check("switch: off again stored", stored.get("pauseBreath") is False, stored)
        await pg.context.close()

        # ---------- Tabata / Zirkel ----------
        pg = await new_page(b, errors, QUIET + master(True) + CIRCUIT(10, 30))
        await start_tabata(pg)
        s = await state(pg, *TAB)
        check("tabata: no circle in 'Bereit machen'", not s["on"] and not s["circleShown"] and s["label"] is None, s)
        await tick(pg, 3000 + 20000 + 500)
        phase = await pg.text_content("#tabataPhaseLabel")
        s = await state(pg, *TAB)
        check("tabata: rest (10 s) shows the breathing circle", phase == "Pause" and s["on"] and s["circleShown"] and s["label"] == "Einatmen", (phase, s))
        check_readable("tabata rest", s)
        await pg.screenshot(path=os.path.join(SHOTS, "atem_tabata_390_light.png"))
        await tick(pg, 4000)
        s = await state(pg, *TAB)
        check("tabata: label switches to Ausatmen after 4 s", s["label"] == "Ausatmen", s)
        await tick(pg, 6000 + 500)
        s = await state(pg, *TAB)
        check("tabata: work phase = circle gone again", await pg.text_content("#tabataPhaseLabel") == "Los!" and not s["on"] and s["label"] is None, s)
        await tick(pg, 20000)
        s = await state(pg, *TAB)
        check("tabata: Satzpause (30 s) shows the circle", await pg.text_content("#tabataPhaseLabel") == "Satzpause" and s["on"], s)
        check_readable("tabata Satzpause", s)
        await pg.click("#workoutBackBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmYesBtn"):
            await pg.click("#confirmYesBtn")
        await pg.wait_for_timeout(200)
        s = await state(pg, *TAB)
        check("tabata: Beenden stops the guide", not s["on"] and s["label"] is None, s)
        await pg.context.close()

        # Tabata rest under 10 s keeps the plain countdown
        pg = await new_page(b, errors, QUIET + master(True) + CIRCUIT(5, 30))
        await start_tabata(pg)
        await tick(pg, 3000 + 20000 + 500)
        s = await state(pg, *TAB)
        check("tabata: 5 s rest = plain countdown", await pg.text_content("#tabataPhaseLabel") == "Pause" and not s["on"] and not s["circleShown"], s)
        await pg.context.close()

        # Switch off: plain countdown even in a long rest
        pg = await new_page(b, errors, QUIET + master(False) + CIRCUIT(10, 30))
        await start_tabata(pg)
        await tick(pg, 3000 + 20000 + 500)
        s = await state(pg, *TAB)
        check("tabata: switch off = plain countdown", await pg.text_content("#tabataPhaseLabel") == "Pause" and not s["on"] and not s["circleShown"], s)
        await pg.context.close()

        # ---------- Kraftplan ----------
        for dark in (False, True):
            pg = await new_page(b, errors, QUIET + master(True), dark=dark)
            await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(100)
            await pg.click("#workoutRepsStartCard"); await pg.wait_for_timeout(150)
            await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Kniebeugen") .ca-plus-btn'); await pg.wait_for_timeout(60)
            await pg.click('#workoutRepsExerciseGrid .custom-exercise-add-row:has-text("Liegestütze") .ca-plus-btn'); await pg.wait_for_timeout(60)
            await pg.click("#workoutRepsStartBtn"); await pg.wait_for_timeout(300)
            s = await state(pg, *REST)
            if not dark:
                check("kraft: no circle in 'Bereit machen'", await pg.is_visible("#workoutRestBox") and not s["on"], s)
            await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
            await pg.click("#workoutSetDoneBtn"); await pg.wait_for_timeout(200)
            s = await state(pg, *REST)
            rest_s = int(s["cdText"]) if s["cdText"].isdigit() else -1
            check(f"kraft{' dark' if dark else ''}: rest between sets shows the circle", rest_s >= 10 and s["on"] and s["circleShown"] and s["label"] == "Einatmen", s)
            check_readable("kraft rest" + (" dark" if dark else ""), s)
            if dark:
                check("kraft dark: countdown light on dark", s["cdColor"] == "rgb(233, 240, 242)", s["cdColor"])
                check("kraft dark: label readable (#a9bbc0)", s["labelColor"] == "rgb(169, 187, 192)", s["labelColor"])
            await pg.screenshot(path=os.path.join(SHOTS, f"atem_kraft_390_{'dark' if dark else 'light'}.png"))
            await pg.click("#workoutRestSkipBtn"); await pg.wait_for_timeout(150)
            s = await state(pg, *REST)
            check(f"kraft{' dark' if dark else ''}: next set = circle gone", not s["on"] and s["label"] is None, s)
            await pg.context.close()

        # ---------- Ausdauertraining ----------
        for dark, w in ((False, 390), (True, 390), (False, 1024), (True, 1024)):
            pg = await new_page(b, errors, QUIET + master(True) + CARDIO, dark=dark, w=w, h=844 if w == 390 else 768)
            await start_cardio(pg)
            tag = f"cardio {w}{' dark' if dark else ''}"
            s = await state(pg, *CAR)
            if w == 390 and not dark:
                check("cardio: no circle during an activity", not s["on"] and s["label"] is None, s)
            await tick(pg, 60500)
            title = await pg.inner_text("#cardioActivityTitle")
            s = await state(pg, *CAR)
            check(f"{tag}: 20 s pause shows the circle", title == "Pause" and s["on"] and s["circleShown"] and s["label"] == "Einatmen", (title, s))
            check_readable(tag, s)
            check(f"{tag}: no sideways scroll", s["scrollW"] <= s["w"], s)
            await pg.screenshot(path=os.path.join(SHOTS, f"atem_cardio_{w}_{'dark' if dark else 'light'}.png"))
            if w == 390 and not dark:
                # Pausiert sheet: countdown freezes, circle keeps breathing, Weiter resumes.
                await pg.click("#cardioPauseBtn"); await pg.wait_for_timeout(150)
                c0 = await pg.inner_text("#cardioCountdown"); await tick(pg, 2000)
                check("cardio: countdown frozen while paused", c0 == await pg.inner_text("#cardioCountdown"))
                await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(150)
                await tick(pg, 20000)
                s = await state(pg, *CAR)
                check("cardio: next activity = circle gone", await pg.inner_text("#cardioActivityTitle") == "Walking" and not s["on"], s)
                await tick(pg, 60000)
                s = await state(pg, *CAR)
                check("cardio: 5 s pause = plain countdown", await pg.inner_text("#cardioActivityTitle") == "Pause" and not s["on"] and not s["circleShown"], s)
            await pg.context.close()

        # ---------- Kombi pause between Bausteine ----------
        for dark in (False, True):
            pg = await new_page(b, errors, QUIET + master(True, 20), dark=dark)
            await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
            for _ in range(2):
                await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
                await pg.fill("#rememberComboDurationSlider", "15")
                await pg.dispatch_event("#rememberComboDurationSlider", "input")
                await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
            await pg.click("#comboStartBtn"); await pg.wait_for_timeout(300)
            await tick(pg, 16500)
            vis = await pg.is_visible("#comboTransition")
            s = await state(pg, *KOM)
            tag = "kombi" + (" dark" if dark else "")
            check(f"{tag}: pause screen shows the circle", vis and s["on"] and s["circleShown"] and s["label"] == "Einatmen", (vis, s))
            check_readable(tag, s)
            if dark:
                check("kombi dark: countdown light on dark", s["cdColor"] == "rgb(233, 240, 242)", s["cdColor"])
                check("kombi dark: label readable", s["labelColor"] == "rgb(169, 187, 192)", s["labelColor"])
            await pg.screenshot(path=os.path.join(SHOTS, f"atem_kombi_390_{'dark' if dark else 'light'}.png"))
            await pg.click("#comboTransitionBtn"); await pg.wait_for_timeout(300)
            s = await state(pg, *KOM)
            check(f"{tag}: Überspringen stops the guide", not s["on"] and s["label"] is None, s)
            await pg.context.close()

        # Kombi pause under 10 s = plain countdown
        pg = await new_page(b, errors, QUIET + master(True, 5))
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(150)
        for _ in range(2):
            await pg.click('#comboAddGrid >> text="Positionen merken · Feste Positionen"'); await pg.wait_for_timeout(300)
            await pg.fill("#rememberComboDurationSlider", "15")
            await pg.dispatch_event("#rememberComboDurationSlider", "input")
            await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(300)
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(300)
        await tick(pg, 16500)
        s = await state(pg, *KOM)
        check("kombi: 5 s pause = plain countdown", await pg.is_visible("#comboTransition") and not s["on"] and not s["circleShown"], s)
        check_readable_plain = s["cdVisible"] and s["cdFont"] >= 40
        check("kombi: plain countdown still big", check_readable_plain, s)
        await pg.context.close()

        check("no page/console errors", errors == [], errors[:5])
        await b.close()
    print("FAILS:", fails)
    print("ERRORS:", errors)

asyncio.run(main())
