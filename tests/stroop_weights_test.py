import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Stroop "Häufigkeit der Farben" (Fabian, 2026-10-02 "B. Ja"): per-colour
# 1x-3x weight for the ink colour in VT Stroop klassisch / mit Hintergrund.


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(200)
        print("no weights on an arrow exercise:", await pg.is_hidden("#stroopWeights"))
        await pg.click("#backToHome"); await pg.wait_for_timeout(200)

        await pg.click('.excard[data-exercise="stroop-classic"]'); await pg.wait_for_timeout(200)
        print("weights box shown for Stroop:", await pg.is_visible("#stroopWeights"))
        n_sel = len(await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}').stroopColors || ['rot','gruen','blau','gelb','lila']"))
        await pg.click("#stroopWeights summary"); await pg.wait_for_timeout(100)
        rows = await pg.locator("#stroopWeightRows .slider-row").count()
        print("one slider per selected colour:", rows == n_sel, rows, n_sel)
        await pg.fill('[data-stroop-weight="rot"]', "3"); await pg.dispatch_event('[data-stroop-weight="rot"]', "input")
        print("value label 3x:", "3×" in await pg.inner_text('#stroopWeightRows .slider-row:has([data-stroop-weight="rot"])'))
        saved = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-webapp-v3')).stroopWeights")
        print("saved:", saved == {"rot": 3}, saved)
        # deselecting a colour drops its row
        await pg.click('#colorPicker .color-swatch[data-color="lila"]'); await pg.wait_for_timeout(100)
        print("row count follows the selection:", await pg.locator("#stroopWeightRows .slider-row").count() == n_sel - 1)

        # statistics on the real schedule: red as ink ~3x as often
        stats = await pg.evaluate("""() => {
            const keys = ['rot','gruen','blau','gelb'];
            const raw = JSON.parse(localStorage.getItem('fwmc-webapp-v3'));
            return raw.stroopColors;
        }""")
        print("selection now:", stats)
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="stroop-classic"]'); await pg.wait_for_timeout(200)
        await pg.click("#stroopWeights summary"); await pg.wait_for_timeout(100)
        print("weight survives reload:", await pg.input_value('[data-stroop-weight="rot"]') == "3")
        # sample the drawn ink colour across a fast run
        await pg.evaluate("""() => { const raw = JSON.parse(localStorage.getItem('fwmc-webapp-v3')); raw.stimulusS = 0.5; raw.intervalMin = 0.5; raw.intervalMax = 0.5; raw.duration = 300; localStorage.setItem('fwmc-webapp-v3', JSON.stringify(raw)); }""")
        await pg.reload(); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.excard[data-exercise="stroop-classic"]'); await pg.wait_for_timeout(200)
        await pg.click("#startBtn"); await pg.wait_for_timeout(3300)
        counts = {}
        last = None
        for _ in range(300):
            c = await pg.evaluate("""() => {
                const lib = {'211,47,47':'rot','46,125,50':'gruen','21,101,192':'blau','242,169,0':'gelb'};
                const c = document.getElementById('stage'), x = c.getContext('2d');
                const d = x.getImageData(0, 0, c.width, c.height).data;
                const tally = {};
                for (let i = 0; i < d.length; i += 4 * 3) {
                    const k = lib[d[i] + ',' + d[i+1] + ',' + d[i+2]];
                    if (k) tally[k] = (tally[k] || 0) + 1;
                }
                let best = null, n = 0; for (const k in tally) if (tally[k] > n) { n = tally[k]; best = k; }
                return n > 50 ? best : null;
            }""")
            if c and c != last:
                counts[c] = counts.get(c, 0) + 1
            last = c
            await pg.wait_for_timeout(55)
        red = counts.get("rot", 0)
        total = sum(counts.values())
        others = [v for k, v in counts.items() if k != "rot"]
        print("ink sampled:", counts)
        print("red appears clearly more often than any other colour:", total > 20 and others and red > max(others))
        await pg.click("#backBtn"); await pg.wait_for_timeout(200)
        if await pg.is_visible("#confirmSheet"):
            await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
