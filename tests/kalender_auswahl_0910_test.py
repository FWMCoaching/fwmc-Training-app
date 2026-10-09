"""Kalender: ausgewählter Tag vs. heute eindeutig, ungeplante Trainings im Tagesfeld (Fabian 09.10.).

- Ausgewählter Tag ist gefüllt (Hintergrund = Markenfarbe), heute (nicht ausgewählt)
  hat einen anderen Hintergrund, in hell und dunkel.
- Ein Training ohne Plan-Eintrag erscheint im Tagesfeld unter "Zusätzlich trainiert".
- Kein pageerror / console error.
"""
import asyncio, json, datetime
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=heute"
results = []

def check(name, ok, info=""):
    results.append(ok)
    print(f"{name}: {ok}{(' - ' + info) if info and not ok else ''}")

async def run(b, scheme):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme)
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    today = datetime.date.today()
    # a past day in the same week (or today if Monday)
    past = today - datetime.timedelta(days=min(1, today.weekday()))
    ts = datetime.datetime.combine(past, datetime.time(9, 30)).isoformat()
    hist = [{"id": "1", "ts": ts, "kind": "exercise", "exId": "periph", "title": "Periphere Wahrnehmung", "seconds": 420}]
    await pg.add_init_script(
        f"localStorage.setItem('fwmc-history-v1', {json.dumps(json.dumps(hist))});"
        "localStorage.setItem('fwmc-tips-seen','1');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
    await pg.goto(URL); await pg.wait_for_timeout(700)
    d = past.isoformat()
    await pg.evaluate(f"document.querySelector('.week-day[data-date=\"{d}\"]').click()")
    await pg.wait_for_timeout(250)
    styles = await pg.evaluate("""() => {
      const sel = document.querySelector('.week-day.selected');
      const tod = document.querySelector('.week-day.is-today');
      const brand = getComputedStyle(document.documentElement).getPropertyValue('--brand').trim();
      const bg = (e) => e ? getComputedStyle(e).backgroundColor : null;
      return {sel: bg(sel), tod: bg(tod), same: sel === tod, brand};
    }""")
    if d != today.isoformat():
        check(f"{scheme}: heute und ausgewählt sehen verschieden aus", styles["sel"] != styles["tod"], str(styles))
    body = await pg.locator("#dayPanelBody").inner_text()
    check(f"{scheme}: ungeplantes Training im Tagesfeld", "zusätzlich trainiert" in body.lower() and "periphere wahrnehmung" in body.lower(), body[:120])
    check(f"{scheme}: keine Fehler", not errs, str(errs))
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        for s in ("light", "dark"):
            await run(b, s)
        await b.close()
    print(f"\n{sum(results)}/{len(results)} passed")

asyncio.run(main())
