# Start-Knöpfe einheitlich (Fabian, 2026-10-02): jeder Knopf, der ein
# Training/Programm/einen Plan startet, heißt "Training starten". Im
# Kombi-Bau-Modus heißt er "Baustein übernehmen". Die Cardio-Zusatzaufgabe
# heißt überall "Zusatzaufgabe".
import sys
from playwright.sync_api import sync_playwright

URL = "http://localhost:8845/index.html?bereich=visual"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(label, ok):
    results.append(ok)
    print(f"{label}: {ok}")


IDS = ["startBtn", "programStartBtn", "movementProgramStartBtn", "cardioProgramStartBtn",
       "breathProgramStartBtn", "workoutProgramStartBtn", "comboStartBtn",
       "cardioAddonPickerStartBtn", "breathStartBtn"]

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 390, "height": 844})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');")
    pg.goto(URL)
    pg.wait_for_timeout(300)
    for i in IDS:
        txt = pg.evaluate(f"(document.getElementById('{i}')||{{}}).textContent")
        check(f"#{i} says Training starten", (txt or "").strip() == "Training starten")
    old = pg.evaluate("""[...document.querySelectorAll('button')].map(b=>b.textContent.trim())
      .filter(t=>/^(Programm|Plan|Cardio|Atemtraining|Jetzt|Kraftvolle Atmung) starten$/.test(t))""")
    check("no old start labels left", old == [])
    # Wim Hof (Kraftvolle Atmung) after acknowledging the safety note.
    pg.evaluate("document.getElementById('wimhofSafetyAck') && (document.getElementById('wimhofSafetyAck').checked=true, document.getElementById('wimhofSafetyAck').dispatchEvent(new Event('change',{bubbles:true})))")
    wim = pg.evaluate("document.getElementById('wimhofStartBtn').textContent.trim()")
    check("Wim Hof label is Training starten or still waiting for ack", wim in ("Training starten", "Bitte oben bestätigen"))
    # Cardio extra task has one name everywhere (Fabian, 2026-10-02).
    trig = pg.evaluate("document.getElementById('cardioAddonTriggerBtn').textContent.trim()")
    check("Cardio trigger says + Zusatzaufgabe", trig == "+ Zusatzaufgabe")
    names = pg.evaluate("document.body.innerHTML.match(/Zusatzimpuls|Zusatzübung/g)")
    check("no Zusatzimpuls/Zusatzübung in the page", not names)
    check("no page errors", not errors)
    b.close()

print("ALL OK" if all(results) else "SOME FAILED")
sys.exit(0 if all(results) else 1)
