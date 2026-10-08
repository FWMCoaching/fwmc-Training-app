"""Prüfer-Funde 08.10. abends (reviewer list, fixed the same evening).

Each block keeps one fix fixed:
 1-3  Gleichgewicht · Wörter: pause sheet shows word rows + "Größe der
      Wörter" (no stick rows), one size control on the ready screen, word
      groups spaced like every other group.
 4    Kombi pause countdown readable in dark mode (any .pause-countdown on a
      dark done panel).
 5-6  Neuro pause: one help sentence, nothing covered by the sticky "Weiter";
      « ↻ » in the stage (pause open) are 46 px like the step bar.
 7    Trainer-Werkzeuge only after a "feature-unlock" code (lock hides them,
      a running Kunden-Training stays endable); "Trainer-QR-Code scannen" for
      everyone: jsQR path with a fake camera, BarcodeDetector stub, camera
      denied -> calm message + "Code von Hand einfügen"; trainer pre-check.
 8    Hütchen · Laufweg: calm paths on a phone, no stacked direction marks.
 9    Zusatzaufgabe: "Art der Zusatzaufgabe" label, no empty hint line.
 10   Neuro hub tile without the amber "Mit Code freigeschaltet" pill.
 11   "Spezialübung von deinem Trainer": one teal style; the Kombi pause
      result line without the tag.
 12   "Übungen" heading, Z‑Vibe with a non-breaking hyphen.
 13   Farbfelder description: at most three sentences.
 14   One checkbox style (22 px, brand accent).
 15   Richtungskreuz Farbregel as chips, Farbfelder hands as chips.
 16   Regeln sheet: only deviating colours, "Regeln und Notiz" everywhere,
      colour placeholder only where colours mean something.
 17   Player bars with ⓘ stay one row at 360/375/390 px.
 18   Dashboard "Spezialübung · Kombi" one line at 390; Freischaltung builder.
 NICE "Zusatz für oben" without colon, "80 %" spacing, Cardio guest values
      with comma, "+ Wie heißt du?", gear intro, Neuro 1×/2×/3× and one
      duration slider.
Run from tests/ with a dev server (FWMC_PORT, default 8845).
Screenshots: tests/screenshots/pruefer_fix/."""
import asyncio, json, os, re, urllib.parse
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
DASH = f"http://localhost:{PORT}/dashboard.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "pruefer_fix")
os.makedirs(SHOTS, exist_ok=True)
results, errors = [], []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra if not ok else "")


INIT = """try{localStorage.setItem('fwmc-tips-seen','true');
localStorage.setItem('fwmc-test-bottomnav','true');
localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));}catch(e){}"""

SERVED = {
    "tools-an": {"type": "feature-unlock", "name": "Trainer-Werkzeuge", "features": ["trainer-tools"]},
    "tools-aus": {"type": "feature-unlock", "name": "aus", "features": ["trainer-tools"], "lock": True},
    "kaputt": {"type": "feature-unlock", "name": "x", "features": ["gibt-es-nicht"]},
    "spezial": {"type": "combo-program", "name": "Spezial", "blocks": [
        {"domain": "neuro", "ex": "vibration", "prefs": {"stepS": 10, "reps": 1}, "pauseAfterS": 30},
        {"domain": "neuro", "ex": "gelenke", "prefs": {"stepS": 10}},
    ]},
}

# Fake rear camera: a canvas stream showing a QR code (qrcode.js) for
# window.__fakeQr; window.__camDeny = permission denied.
FAKE_CAM = """(() => {
  window.__fakeQr = null; window.__camDeny = false; window.__camAsked = null;
  const md = { getUserMedia: async (c) => {
    window.__camAsked = c;
    if (window.__camDeny) { const e = new Error('denied'); e.name = 'NotAllowedError'; throw e; }
    if (!window.qrcode) await new Promise((r) => { const s = document.createElement('script'); s.src = 'qrcode.js'; s.onload = r; document.head.appendChild(s); });
    const cv = document.createElement('canvas'); cv.width = 480; cv.height = 640;
    const g = cv.getContext('2d');
    let last = '', q = null;
    const draw = () => {
      g.fillStyle = '#ffffff'; g.fillRect(0, 0, 480, 640);
      const t = window.__fakeQr;
      if (!t) return;
      if (t !== last) { q = qrcode(0, 'M'); q.addData(t); q.make(); last = t; }
      const n = q.getModuleCount(), m = Math.floor(440 / (n + 8)), off = Math.round((480 - m * n) / 2);
      g.fillStyle = '#000000';
      for (let r = 0; r < n; r++) for (let c2 = 0; c2 < n; c2++) if (q.isDark(r, c2)) g.fillRect(off + c2 * m, 100 + r * m, m, m);
    };
    draw(); setInterval(draw, 100);
    return cv.captureStream(10);
  } };
  Object.defineProperty(navigator, 'mediaDevices', { value: md, configurable: true });
})();"""
NO_DETECTOR = "try { delete window.BarcodeDetector; } catch (e) {} window.BarcodeDetector = undefined;"
STUB_DETECTOR = """window.__detectCalls = 0;
window.BarcodeDetector = class { static async getSupportedFormats() { return ['qr_code']; }
  async detect() { window.__detectCalls++; return window.__fakeQr ? [{ rawValue: window.__fakeQr }] : []; } };"""


def entry(i, minutes_ago, title):
    import time
    ms = int(time.time() * 1000) - minutes_ago * 60000
    ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms / 1000)) + ".000Z"
    return {"id": str(1759900000000 + i), "ts": ts, "rating": None, "kind": "exercise", "title": title, "seconds": 300, "exId": "farbfelder"}


async def tm_menu(pg):
    """Trainer-Menü oben links (08.10. abends): trainer buttons live there."""
    if not await pg.is_visible("#trainerMenuSheet"):
        await pg.locator(".trainer-mode-btn:visible").first.click()
        await pg.wait_for_timeout(150)


async def tm_click(pg, sel):
    await tm_menu(pg)
    await pg.click(sel)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        async def api(route):
            url = route.request.url
            q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            code = (q.get("code") or [""])[0].lower()
            if "/program" in url and code in SERVED:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps(SERVED[code]))
            else:
                await route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')

        async def new_ctx(w=390, h=844, scheme="light", extra=""):
            ctx = await b.new_context(viewport={"width": w, "height": h}, service_workers="block", color_scheme=scheme)
            await ctx.add_init_script(INIT + extra)
            await ctx.route("https://online-training.fwmc.workers.dev/**", api)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
            pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
            return ctx, pg

        async def shot(pg, name, full=False):
            await pg.screenshot(path=os.path.join(SHOTS, name), full_page=full)

        # ================= 1-3 Gleichgewicht · Wörter =================
        for scheme in ["light", "dark"]:
            ctx, pg = await new_ctx(scheme=scheme, extra="localStorage.setItem('fwmc-balance-prefs-v1', JSON.stringify({content:'woerter', wordList:'tiere'}));")
            await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
            await pg.evaluate("document.getElementById('balanceOpenBtn').click()"); await pg.wait_for_timeout(200)
            await pg.evaluate("document.getElementById('balanceAdvanced').open = true")
            if scheme == "light":
                check("1/2 ready: words -> stick Schriftgröße hidden, one size control", not await pg.is_visible("#balanceFontSlider")
                      and await pg.locator('#balanceReady [data-look-size="balance"]:visible').count() == 1)
                gap = await pg.evaluate("""(() => { const row = document.getElementById('balanceContentRow').getBoundingClientRect();
                    const lab = document.querySelector('#balanceWordBox .group-label').getBoundingClientRect();
                    const every = document.getElementById('balanceWordEveryRow').previousElementSibling.getBoundingClientRect();
                    const list = document.getElementById('balanceWordListRow').getBoundingClientRect();
                    return { first: lab.top - row.bottom, second: every.top - list.bottom }; })()""")
                check("3 ready: word labels spaced like groups (>= 16 px)", gap["first"] >= 16 and gap["second"] >= 16, gap)
            await shot(pg, f"gleichgewicht_ready_390_{scheme}.png", True)
            await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(500)
            await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(250)
            if scheme == "light":
                vis = await pg.evaluate("""(() => { const v = (id) => { const e = document.getElementById(id); return !!e && e.offsetParent !== null; };
                    const ov = document.getElementById('balancePauseOverlay');
                    const labels = [...ov.querySelectorAll('.group:not([hidden]) > .group-label')].filter((l) => l.offsetParent).map((l) => l.textContent.trim());
                    return { stick: v('balancePauseColor1Picker'), length: v('balancePauseLengthSlider'), reset: v('balancePauseResetPosBtn'), labels }; })()""")
                check("1 pause: no stick rows in words mode", not vis["stick"] and not vis["length"] and not vis["reset"], vis)
                check("1 pause: 'Größe der Wörter', 'Wörter', 'Wort wechselt' shown",
                      any(l.startswith("Größe der Wörter") for l in vis["labels"]) and "Wörter" in vis["labels"] and "Wort wechselt" in vis["labels"], vis["labels"])
                await pg.locator('#balancePauseOverlay [data-pause-val="alltag"]').click(); await pg.wait_for_timeout(100)
                await pg.locator('#balancePauseOverlay [data-pause-val="4"]').click(); await pg.wait_for_timeout(100)
                saved = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-balance-prefs-v1'))")
                check("1 pause: word list + change live, saved for the own run", saved.get("wordList") == "alltag" and saved.get("wordEvery") == 4, saved)
                lies = await pg.locator('#balancePauseOverlay [data-pause-choice="bal-wordread"]').is_visible()
                await pg.locator('#balancePauseOverlay [data-pause-val="farben"]').click(); await pg.wait_for_timeout(100)
                check("1 pause: 'Lies' row only for Farbwörter", not lies and await pg.locator('#balancePauseOverlay [data-pause-choice="bal-wordread"]').is_visible())
            await shot(pg, f"gleichgewicht_pause_390_{scheme}.png")
            await ctx.close()
        # sticks mode keeps the stick rows
        ctx, pg = await new_ctx(extra="localStorage.setItem('fwmc-balance-prefs-v1', JSON.stringify({content:'stifte'}));")
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('balanceOpenBtn').click()"); await pg.wait_for_timeout(200)
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(400)
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(200)
        lab = await pg.inner_text('#balancePauseOverlay [data-live-look="balance"] .group-label')
        check("1 pause (sticks): stick rows + 'Größe der Stifte', no word rows",
              await pg.is_visible("#balancePauseColor1Picker") and lab.startswith("Größe der Stifte") and not await pg.locator('#balancePauseOverlay [data-pause-choice="bal-wordlist"]').is_visible())
        await ctx.close()

        # ================= 4 Kombi pause countdown in dark mode + 11 result line =================
        ctx, pg = await new_ctx(scheme="dark")
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelector('#trainingHub .code-toggle') && document.querySelector('#trainingHub .code-toggle').click()")
        await pg.fill("#moreCodeInput", "spezial"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(900)
        tag_player = await pg.evaluate("(() => { const t = document.getElementById('neuroRunSpecial'); const cs = getComputedStyle(t); return { vis: t.offsetParent !== null, border: cs.borderTopColor }; })()")
        await shot(pg, "spezial_player_390_dark.png")
        for _ in range(60):
            if await pg.is_visible("#comboTransition"): break
            await pg.evaluate("window.__neuroSkipTime && window.__neuroSkipTime(999)"); await pg.wait_for_timeout(160)
        cd = await pg.evaluate("""(() => { const lum = (c) => { const m = c.match(/\\d+(\\.\\d+)?/g).map(Number).slice(0, 3).map((v) => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * m[0] + .7152 * m[1] + .0722 * m[2]; };
            const el = document.getElementById('comboTransitionCountdown'); const fg = getComputedStyle(el).color; const bg = getComputedStyle(document.getElementById('comboTransition')).backgroundColor;
            const a = lum(fg), b2 = lum(bg); return { fg, bg, ratio: (Math.max(a, b2) + .05) / (Math.min(a, b2) + .05), text: el.textContent }; })()""")
        check("4 Kombi pause reached", await pg.is_visible("#comboTransition"))
        check("4 Kombi pause countdown readable in dark mode (contrast >= 4.5)", cd["ratio"] >= 4.5, cd)
        res = await pg.inner_text("#comboTransitionResult")
        check("11 Kombi pause result line without the Spezialübung tag", "erledigt" in res and "Spezialübung" not in res, res)
        tag_pause = await pg.evaluate("getComputedStyle(document.getElementById('comboTransitionSpecial')).borderTopColor")
        check("11 one tag style (teal outline in player and pause)", tag_player["vis"] and "57, 167, 204" in tag_player["border"] and "57, 167, 204" in tag_pause, (tag_player, tag_pause))
        await shot(pg, "kombi_pause_390_dark.png")
        await ctx.close()

        # ================= 5-6 Neuro pause sheet + chapter buttons =================
        for scheme in ["light", "dark"]:
            ctx, pg = await new_ctx(scheme=scheme, extra="localStorage.setItem('fwmc-test-neuro','true');")
            await pg.goto(BASE + "?bereich=neuro"); await pg.wait_for_timeout(300)
            if scheme == "light":
                check("12 neuro home heading 'Übungen'", "Übungen" in await pg.inner_text("#neuroHome .patterns .section-head h2"))
                hero = await pg.inner_text("#neuroHome .hero-text")
                check("10 neuro home says 'freigeschaltet' at most in the one-time notice", "freigeschaltet" not in hero, hero)
            await pg.click('[data-neuro-ex="vibration"]'); await pg.wait_for_timeout(200)
            if scheme == "light":
                check("NICE neuro: Durchgänge read 1×/2×/3×", [t.strip() for t in await pg.locator('#neuroReadyControls [data-nr-f="reps"]').all_inner_texts()] == ["1×", "2×", "3×"])
                check("NICE neuro: Dauer pro Schritt is one slider (no chips)", await pg.locator('#neuroReadyControls [data-nr-f="stepS"]').count() == 0
                      and await pg.locator('#neuroReadyControls input[data-nr-r="stepS"]').count() == 1)
                hm = await pg.inner_text("#neuroHilfsmittel")
                check("12 Z‑Vibe with a non-breaking hyphen", "Z‑Vibe" in hm and "Z-Vibe" not in hm, hm)
            await pg.click("#neuroStartBtn"); await pg.wait_for_timeout(300)
            await pg.click("#neuroPauseBtn"); await pg.wait_for_timeout(250)
            info = await pg.evaluate("""(() => { const ov = document.getElementById('neuroPauseOverlay');
                const helps = [...ov.querySelectorAll('.group-help')].filter((h) => h.offsetParent && h.textContent.trim()).map((h) => h.textContent.trim());
                const help = document.getElementById('neuroPauseHelp').getBoundingClientRect(); const btn = document.getElementById('neuroResumeBtn').getBoundingClientRect();
                const nav = [...document.querySelectorAll('#neuroPrevBtn,#neuroRestartBtn,#neuroSkipBtn')].map((x) => [Math.round(x.getBoundingClientRect().width), Math.round(x.getBoundingClientRect().height)]);
                return { helps, gap: btn.top - help.bottom, nav }; })()""")
            if scheme == "light":
                check("5 neuro pause: one help sentence, no contradiction", len(info["helps"]) == 1 and "Takt gilt sofort" in info["helps"][0] and "ab dem nächsten Schritt" in info["helps"][0], info["helps"])
                check("5 neuro pause: help not under the 'Weiter' fade (>= 14 px)", info["gap"] >= 14, info["gap"])
                check("6 « ↻ » in the stage are 46 px (step bar size)", all(w >= 44 and h >= 44 for w, h in info["nav"]), info["nav"])
            await shot(pg, f"neuro_pause_390_{scheme}.png")
            await ctx.close()
        # 5 sibling: every pause sheet keeps loose last items clear of the fade
        ctx, pg = await new_ctx()
        await pg.goto(BASE); await pg.wait_for_timeout(300)
        mb = await pg.evaluate("""(() => [...document.querySelectorAll('.pause-panel > :nth-last-child(2):not(.group)')].map((e) => parseFloat(getComputedStyle(e).marginBottom)))()""")
        check("5 all pause sheets: loose item before 'Weiter' keeps 14 px", mb and min(mb) >= 14, mb)
        await ctx.close()

        # ================= 7 QR-Übergabe: unlock + scanner =================
        seed = "localStorage.setItem('fwmc-history-v1', JSON.stringify(%s));" % json.dumps([entry(1, 10, "Farbfelder · Antippen"), entry(2, 30, "Gleichgewicht · Wörter")]).replace("'", "\\'")
        ctx, pg = await new_ctx(extra=seed)
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(350)
        check("7 default: trainer menu button hidden", not (await pg.locator(".trainer-mode-btn:visible").count() > 0))
        scan_btn = await pg.evaluate("(() => { const b = document.getElementById('handoverScanOpenBtn'); const r = b.getBoundingClientRect(); return { vis: b.offsetParent !== null, cls: b.className, h: r.height, text: b.textContent.trim() }; })()")
        check("7 'Trainer-QR-Code scannen' always visible, quiet, >= 44 px", scan_btn["vis"] and "text-link" in scan_btn["cls"] and scan_btn["h"] >= 44 and scan_btn["text"] == "Trainer-QR-Code scannen", scan_btn)
        check("7 no top-level paste button any more", await pg.locator("#handoverPasteOpenBtn").count() == 0)
        await shot(pg, "fortschritt_kunde_390_light.png", True)
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelector('#trainingHub .code-toggle') && document.querySelector('#trainingHub .code-toggle').click()")
        await pg.fill("#moreCodeInput", "kaputt"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(700)
        check("7 broken feature-unlock code -> code error, nothing stored", await pg.evaluate("localStorage.getItem('fwmc-features-v1')") is None)
        await pg.fill("#moreCodeInput", "tools-an"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(700)
        toast = await pg.evaluate("(document.querySelector('.app-toast') || {}).textContent || ''")
        vis_screen = await pg.evaluate("[...document.querySelectorAll('.screen')].find((s) => !s.hidden).id")
        check("7 unlock code: toast in Du-form, Training shown, tools visible", "Trainer-Werkzeuge sind jetzt freigeschaltet" in toast and vis_screen == "trainingHub"
              and (await pg.locator(".trainer-mode-btn:visible").count() > 0), (toast, vis_screen))
        check("7 unlock stored in fwmc-features-v1", (await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-features-v1'))")).get("trainer-tools") is True)
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(350)
        check("7 unlock persists across reload", (await pg.locator(".trainer-mode-btn:visible").count() > 0))
        await tm_click(pg, "#handoverOpenBtn"); await pg.wait_for_timeout(250)
        pre = await pg.evaluate("document.getElementById('handoverPrecheck').textContent")
        check("7 trainer pre-check card above the button", "Bevor dein Kunde scannt" in pre and "Startbildschirm" in pre and "„Trainer-QR-Code scannen“" in pre, pre)
        await shot(pg, "uebergabe_zeitraum_390_light.png", True)
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(700)
        sub = await pg.inner_text("#handoverQrScreen .page-sub")
        check("7 line under the QR code names the in-app scanner", "„Trainer-QR-Code scannen“" in sub and "Kamera" not in sub, sub)
        qurl = await pg.get_attribute("#handoverQrCanvas", "data-url")
        await shot(pg, "uebergabe_qr_390_light.png", True)
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(300)
        await tm_click(pg, '#tmModes [data-tm="client"]'); await pg.wait_for_timeout(250)
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelector('#trainingHub .code-toggle') && document.querySelector('#trainingHub .code-toggle').click()")
        await pg.fill("#moreCodeInput", "tools-aus"); await pg.click("#moreCodeGoBtn"); await pg.wait_for_timeout(700)
        await tm_menu(pg)
        check("7 lock code hides the tools, a running Kunden-Training stays endable (menu button shows 'Kunde')", not await pg.is_visible("#handoverOpenBtn")
              and await pg.is_visible("#clientRunActiveNote") and await pg.is_visible("#clientRunEndBtn")
              and "Kunde" in await pg.locator(".trainer-mode-btn:visible").first.inner_text())
        await ctx.close()
        token = qurl.split("#import=")[1] if qurl and "#import=" in qurl else ""
        check("7 trainer produced a token", bool(token), qurl)

        # client, jsQR path
        for scheme in ["light", "dark"]:
            ctx, pg = await new_ctx(scheme=scheme, extra=FAKE_CAM + NO_DETECTOR)
            await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(350)
            await pg.click("#handoverScanOpenBtn"); await pg.wait_for_timeout(900)
            st = await pg.evaluate("window.__hoScan()")
            asked = await pg.evaluate("window.__camAsked")
            if scheme == "light":
                check("7 scanner: rear camera asked, camera running, jsQR (no BarcodeDetector)", st["running"] and not st["detector"] and asked and asked["video"]["facingMode"]["ideal"] == "environment", (st, asked))
                check("7 scanner: jsqr.js loaded lazily (not in index.html)", await pg.evaluate("!!window.jsQR") and "src=\"jsqr.js\"" not in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "index.html"), encoding="utf-8").read())
                check("7 scanner: help text", "Halte die Kamera auf den QR-Code deines Trainers." in await pg.inner_text("#handoverScanSheet"))
            await shot(pg, f"scanner_390_{scheme}.png")
            await pg.evaluate("(t) => { window.__fakeQr = 'https://example.org/irgendwas'; }", token); await pg.wait_for_timeout(1500)
            if scheme == "light":
                check("7 scanner: foreign QR -> calm status, keeps scanning", "kein Code deines Trainers" in await pg.inner_text("#handoverScanStatus") and (await pg.evaluate("window.__hoScan()"))["running"])
            await pg.evaluate("(t) => { window.__fakeQr = location.origin + location.pathname + '#import=' + t; }", token)
            for _ in range(30):
                if await pg.is_visible("#handoverImportSheet"): break
                await pg.wait_for_timeout(200)
            st = await pg.evaluate("window.__hoScan()")
            if scheme == "light":
                check("7 scanner (jsQR): code read -> 'übernehmen?' sheet, camera off", await pg.is_visible("#handoverImportSheet") and "übernehmen?" in await pg.inner_text("#handoverImportTitle")
                      and not st["running"] and not st["open"], st)
                check("7 scanner: no Safari copy hint inside the app", not await pg.is_visible("#handoverImportCopyBtn"))
                await pg.click("#handoverImportYesBtn"); await pg.wait_for_timeout(250)
                hist = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-history-v1') || '[]')")
                check("7 scanner: entries imported", len(hist) == 2 and all(e.get("trainer") for e in hist), len(hist))
            await ctx.close()

        # client, BarcodeDetector stub
        ctx, pg = await new_ctx(extra=FAKE_CAM + STUB_DETECTOR)
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(350)
        await pg.evaluate("(t) => { window.__fakeQr = 'x#import=' + t; }", token)
        await pg.click("#handoverScanOpenBtn")
        for _ in range(30):
            if await pg.is_visible("#handoverImportSheet"): break
            await pg.wait_for_timeout(200)
        check("7 scanner (BarcodeDetector): detector used, import sheet, jsqr.js not loaded",
              await pg.evaluate("window.__detectCalls") > 0 and await pg.is_visible("#handoverImportSheet") and not await pg.evaluate("!!window.jsQR"))
        await ctx.close()

        # client, permission denied
        for scheme in ["light", "dark"]:
            ctx, pg = await new_ctx(scheme=scheme, extra=FAKE_CAM + "window.__camDeny = true;")
            await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(350)
            await pg.click("#handoverScanOpenBtn"); await pg.wait_for_timeout(500)
            err = await pg.inner_text("#handoverScanError") if await pg.is_visible("#handoverScanError") else ""
            if scheme == "light":
                check("7 scanner denied: calm message + 'Code von Hand einfügen'", "Kamera nicht nutzen" in err and await pg.is_visible("#handoverScanPasteBtn") and not await pg.is_visible("#handoverScanView"), err)
            await shot(pg, f"scanner_verweigert_390_{scheme}.png")
            if scheme == "light":
                await pg.click("#handoverScanPasteBtn"); await pg.wait_for_timeout(200)
                check("7 fallback opens the paste field", await pg.is_visible("#handoverPasteSheet") and not await pg.is_visible("#handoverScanSheet"))
            await ctx.close()
        # trainer code as QR (Fabian 08.10.): scan "<app>#code=…" / bare code
        ctx, pg = await new_ctx(extra=FAKE_CAM + NO_DETECTOR + "localStorage.setItem('fwmc-test-codequiet','true');")
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(350)
        await pg.evaluate("window.__fakeQr = location.origin + location.pathname + '#code=tools-an'")
        await pg.click("#handoverScanOpenBtn")
        for _ in range(30):
            if await pg.evaluate("!!localStorage.getItem('fwmc-features-v1')"): break
            await pg.wait_for_timeout(200)
        await pg.wait_for_timeout(500)
        st = await pg.evaluate("window.__hoScan()")
        toast = await pg.evaluate("(document.querySelector('.app-toast') || {}).textContent || ''")
        check("7 code QR scan (#code=) runs the code card path: unlocked, toast, camera off",
              (await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-features-v1') || '{}')")).get("trainer-tools") is True
              and "freigeschaltet" in toast and not st["running"] and not st["open"] and (await pg.locator(".trainer-mode-btn:visible").count() > 0), (toast, st))
        await pg.evaluate("window.__fakeQr = 'unbekannt-77'")
        await pg.click("#handoverScanOpenBtn")
        for _ in range(30):
            if await pg.is_visible("#moreCodeError"): break
            await pg.wait_for_timeout(200)
        vis_screen = await pg.evaluate("[...document.querySelectorAll('.screen')].find((s) => !s.hidden).id")
        check("7 bare unknown code scanned -> code card error on Training, card opened", await pg.is_visible("#moreCodeError") and vis_screen == "trainingHub"
              and await pg.input_value("#moreCodeInput") == "unbekannt-77", vis_screen)
        await shot(pg, "code_qr_unbekannt_390_light.png")
        await ctx.close()
        ctx, pg = await new_ctx()
        await pg.goto(BASE + "#code=spezial"); await pg.wait_for_timeout(1200)
        check("7 #code= link from the phone camera opens the code (Kombi player runs), hash cleared",
              await pg.evaluate("[...document.querySelectorAll('.player')].some((p) => !p.hidden)") and "code=" not in await pg.evaluate("location.hash"))
        await ctx.close()
        ctx, pg = await new_ctx()
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.evaluate("history.replaceState(null, '', location.pathname + '?bereich=training'); location.hash = 'code=tools-an'"); await pg.wait_for_timeout(900)
        check("7 #code= as hashchange (app already open) unlocks too", (await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-features-v1') || '{}')")).get("trainer-tools") is True)
        await ctx.close()

        # #import= link still works without any unlock
        ctx, pg = await new_ctx()
        await pg.goto(BASE + "#import=" + token); await pg.wait_for_timeout(800)
        check("7 camera-app link (#import=) works without unlock", await pg.is_visible("#handoverImportSheet"))
        check("7 privacy sheet names the camera", "Kamera nur, um den Code auf deinem Gerät zu lesen" in await pg.evaluate("document.body.textContent"))
        await ctx.close()

        # ================= 8 Laufweg =================
        ctx, pg = await new_ctx()
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)
        picks = await pg.evaluate("(() => { const out = []; for (let i = 0; i < 25; i++) out.push(window.__lw.pick(3, 3, 'mittel', true).score); return out; })()")
        check("8 phone: Mittel 3×3 paths have at most 2 extra crossings", max(x["tangle"] for x in picks) <= 2 and sum(1 for x in picks if x["tangle"] == 0) >= 15, [x["tangle"] for x in picks])
        raw = await pg.evaluate("(() => { let t = 0; for (let i = 1; i <= 25; i++) t += window.__lw.score(window.__lw.make(3, 3, 'mittel', i)).tangle; return t / 25; })()")
        check("8 the pick is calmer than a raw path", raw > 2, raw)
        await pg.click('.excard[data-exercise="cone-path"]'); await pg.wait_for_timeout(200)
        await pg.evaluate("document.querySelector('[data-lw-length=mittel]').click()")
        await pg.click("#startBtn"); await pg.wait_for_timeout(900)
        marks = await pg.evaluate("""(() => [...document.querySelectorAll('#lwMap .lw-chevron')].map((c) => { const r = c.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }))()""")
        close = [(a, b2) for i, a in enumerate(marks) for b2 in marks[i + 1:] if abs(a[0] - b2[0]) < 12 and abs(a[1] - b2[1]) < 12]
        sw = await pg.evaluate("document.querySelector('#lwMap [data-lw-path]').getAttribute('stroke-width')")
        check("8 run: no stacked direction marks, thin line on a phone", not close and sw == "0.05", (len(marks), close[:2], sw))
        await shot(pg, "laufweg_run_390_light.png")
        await ctx.close()

        # ================= 9, 13, 15, 16, NICE on the VT ready screens =================
        for scheme in ["light", "dark"]:
            ctx, pg = await new_ctx(scheme=scheme)
            await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)
            await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(200)
            await pg.evaluate("document.querySelector('#addonPhaseRow [data-addon-phase=pause]').click()"); await pg.wait_for_timeout(100)
            await pg.evaluate("document.getElementById('advanced') && (document.getElementById('advanced').open = true)")
            if scheme == "light":
                lab = await pg.evaluate("(() => { const r = document.getElementById('addonTaskRow'); const l = r.previousElementSibling; const hint = document.getElementById('addonPhaseHint'); return { label: l && l.textContent.trim(), hint: getComputedStyle(hint).display, gap: r.getBoundingClientRect().top - document.getElementById('addonPhaseRow').getBoundingClientRect().bottom }; })()")
                check("9 'Art der Zusatzaufgabe' label, no empty hint, no big gap", lab["label"] == "Art der Zusatzaufgabe" and lab["hint"] == "none" and lab["gap"] < 60, lab)
                zl = await pg.inner_text("#zusGroup .zus-row-label")
                check("NICE 'Zusatz für oben' without colon", zl.strip() == "Zusatz für oben", zl)
                pill = await pg.inner_text("#home, #readyScreen, .screen:not([hidden]) .regeln-btn") if False else await pg.evaluate("(() => { const b = [...document.querySelectorAll('.regeln-btn')].find((x) => x.offsetParent); return b ? b.textContent.trim() : ''; })()")
                check("16 ready pill reads 'Regeln und Notiz'", pill == "Regeln und Notiz", pill)
                await pg.evaluate("[...document.querySelectorAll('.regeln-btn')].find((x) => x.offsetParent).click()"); await pg.wait_for_timeout(250)
                ph = await pg.get_attribute("#regelnNoteInput", "placeholder")
                check("16 arrows: general placeholder, sheet title 'Regeln und Notiz'", "Blau" not in ph and (await pg.inner_text("#regelnTitle")) == "Regeln und Notiz", ph)
                lines = await pg.inner_text("#regelnList")
                check("16 4 Pfeile: second sentence names the direction", "in die Richtung, in die er zeigt" in lines and "in diese Richtung" not in lines, lines)
                focus_ring = await pg.evaluate("(() => { const a = document.activeElement; return a ? getComputedStyle(a).outlineStyle + ':' + a.className : ''; })()")
                check("NICE sheet opens without a focus ring on a button", focus_ring.startswith("none"), focus_ring)
                await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(150)
            await shot(pg, f"vt_zusatzaufgabe_390_{scheme}.png", True)
            # Richtungskreuz
            await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)
            await pg.click('.excard[data-exercise="richtungskreuz"]'); await pg.wait_for_timeout(200)
            await pg.evaluate("document.querySelector('[data-rk-rule=\"1\"]').click()"); await pg.wait_for_timeout(100)
            if scheme == "light":
                check("15 Farbregel: chip rows, no native select", await pg.locator("#rkRuleRows select").count() == 0 and await pg.locator("#rkRuleRows .color-choice-line").count() == 4
                      and await pg.locator("#rkRuleRows .color-choice-line").first.locator(".choice").count() == 4)
                small = await pg.evaluate("Math.min(...[...document.querySelectorAll('#rkRuleRows .choice')].map((c) => c.getBoundingClientRect().height))")
                check("15 chips >= 44 px", small >= 44, small)
                await pg.click('#rkRuleRows [data-rk-rulecol="gelb"][data-val="stehen"]'); await pg.wait_for_timeout(100)
                hm = await pg.inner_text('.hilfsmittel-note:visible')
                check("NICE Richtungskreuz Hilfsmittel text without 'Optional:'", "Optional:" not in hm, hm)
                await pg.evaluate("[...document.querySelectorAll('.regeln-btn')].find((x) => x.offsetParent).click()"); await pg.wait_for_timeout(250)
                lines = [l.strip() for l in (await pg.inner_text("#regelnList")).split("\n") if l.strip()]
                meaning = [l for l in lines if re.match(r"^(Rot|Gelb|Blau|Grün): (Schritt in die Gegenrichtung|stehen bleiben|kein Schritt|Schritt in die gezeigte)", l)]
                check("16 Regeln: only deviating colours + one 'Alle anderen' line", sorted(meaning) == ["Blau: Schritt in die Gegenrichtung.", "Gelb: stehen bleiben, kein Schritt."]
                      and "Alle anderen Farben: Schritt in die gezeigte Richtung." in lines, lines)
                ph = await pg.get_attribute("#regelnNoteInput", "placeholder")
                check("16 colour exercise keeps the colour placeholder", "Blau" in ph, ph)
                await pg.click("#regelnDoneBtn"); await pg.wait_for_timeout(150)
            await shot(pg, f"richtungskreuz_ready_390_{scheme}.png", True)
            # Farbfelder
            await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)
            await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(200)
            if scheme == "light":
                desc = await pg.evaluate("(() => { const e = [...document.querySelectorAll('.screen:not([hidden]) .ex-rules, .screen:not([hidden]) .rules-box, .screen:not([hidden]) [id$=Rules]')].find((x) => x.offsetParent && /Farbfelder/.test(x.textContent)); return e ? e.textContent.trim() : ''; })()")
                if not desc:
                    desc = await pg.evaluate("window.__regeln.vtLines('farbfelder').join(' ')")
                rules = await pg.evaluate("(() => { const t = document.body.innerText; const m = t.match(/Leg deine vier Farbfelder[^\\n]*/); return m ? m[0] : ''; })()")
                n_sent = len([x for x in re.split(r"(?<=[.!?])\s+", rules) if x.strip()])
                check("13 Farbfelder description: 2-3 short sentences", rules and n_sent <= 3, (n_sent, rules[:200]))
                await pg.evaluate("document.querySelector('[data-ff-hands=\"1\"]').click()"); await pg.wait_for_timeout(100)
                check("15 sibling: Farbfelder hands as chips", await pg.locator("#ffHandRows select").count() == 0 and await pg.locator("#ffHandRows .color-choice-line").count() == 4)
                await pg.click('#ffHandRows [data-val="klatschen"] >> nth=0'); await pg.wait_for_timeout(100)
                st = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}').ffHandRules || {}")
                check("15 hand chip saves", "klatschen" in st.values(), st)
            await shot(pg, f"farbfelder_ready_390_{scheme}.png", True)
            await ctx.close()

        # ================= 14 one checkbox style =================
        ctx, pg = await new_ctx(extra="localStorage.setItem('fwmc-test-gear','true');")
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.click('#bottomNav [data-nav="more"]'); await pg.wait_for_timeout(150)
        await pg.click("#moreGearBtn"); await pg.wait_for_timeout(250)
        intro = await pg.inner_text("#gearScreen .page-sub")
        check("NICE gear intro: 'Hak ab, was du hast.'", "Hak ab, was du hast. Dann siehst du bei jeder Übung, was dir noch fehlt." in intro)
        boxes = await pg.evaluate("""(() => [...document.querySelectorAll('input[type=checkbox]')].filter((i) => i.offsetParent).map((i) => { const r = i.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), getComputedStyle(i).accentColor]; }))()""")
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(300)
        await pg.evaluate("document.getElementById('balanceOpenBtn').click()"); await pg.wait_for_timeout(200)
        boxes += await pg.evaluate("""(() => [...document.querySelectorAll('input[type=checkbox]')].filter((i) => i.offsetParent).map((i) => { const r = i.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), getComputedStyle(i).accentColor]; }))()""")
        check("14 every visible checkbox 22 px with the brand accent", boxes and all(w == 22 and h == 22 and a == boxes[0][2] and a != "auto" for w, h, a in boxes), boxes)
        await ctx.close()

        # ================= 17 one-row player bars =================
        rows_bad = []
        for w in [360, 375, 390]:
            ctx, pg = await new_ctx(w=w)
            for nat, opener in [("remember", "#rememberOpenFixed"), ("flash", "#flashOpenConstant"), ("mot", "#motOpenSpeed"), ("blitz", "#blitzOpenBtn")]:
                await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(250)
                await pg.evaluate(f"document.querySelector('{opener}').click()"); await pg.wait_for_timeout(150)
                await pg.click(f"#{nat}ReadyStartBtn"); await pg.wait_for_timeout(900)
                n = await pg.evaluate(f"(() => {{ const t = new Set(); for (const c of document.getElementById('{nat}PlayerBar').children) {{ const r = c.getBoundingClientRect(); if (r.width && r.height) t.add(Math.round(r.top / 8)); }} return t.size; }})()")
                if n != 1: rows_bad.append((w, nat, n))
                if w == 360 and nat in ("mot", "flash"): await pg.screenshot(path=os.path.join(SHOTS, f"leiste_{nat}_360_light.png"), clip={"x": 0, "y": 0, "width": w, "height": 140})
                tb = await pg.evaluate(f"(() => {{ const b = document.getElementById('{nat}PauseBtn'); return [b.textContent.trim(), b.getBoundingClientRect().width]; }})()")
                if not (tb[0].startswith("Pause") and tb[1] >= 44): rows_bad.append((w, nat, "pause", tb))
            await ctx.close()
        check("17 NAT bars with ⓘ one row at 360/375/390 (Pause/Vollbild as 44 px symbols, text kept)", not rows_bad, rows_bad)

        # ================= NICE: Heute name button, Cardio guest value labels =================
        ctx, pg = await new_ctx()
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(300)
        check("NICE '+ Wie heißt du?'", "Wie heißt du?" in await pg.evaluate("document.getElementById('helloNameBtn').textContent"))
        dec = await pg.evaluate("""(() => { const t = document.body.textContent; return (t.match(/\\b\\d+\\.\\d+ ?(s|%|×)(?![a-zäöü])/g) || []).slice(0, 5); })()""")
        check("NICE no dot decimals in value labels (DOM text)", not dec, dec)
        await ctx.close()

        # ================= 18 dashboard =================
        ctx, _ = await new_ctx(390, 844)
        dash = await ctx.new_page()
        dash.on("pageerror", lambda e: errors.append("dash pageerror: " + str(e)))
        saved = []

        async def dash_api(route):
            req = route.request
            if "/admin/programs" in req.url:
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"programs": [
                    {"code": "tools-an", "name": "Trainer-Werkzeuge", "active": True, "updatedAt": "2026-10-08T10:00:00Z", "config": SERVED["tools-an"]}]}))
            elif "/admin/program" in req.url and req.method == "POST":
                saved.append(json.loads(req.post_data))
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"created": True}))
            else:
                await route.fulfill(status=200, content_type="application/json", body="{}")
        await dash.route("https://online-training.fwmc.workers.dev/**", dash_api)
        await dash.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
        await dash.goto(DASH); await dash.wait_for_timeout(600)
        await dash.click('#kindRow [data-kind="neuro"]'); await dash.wait_for_timeout(100)
        lines = await dash.evaluate("(() => { const b = document.querySelector('[data-neuro-mode=kombi]'); const lh = parseFloat(getComputedStyle(b).lineHeight) || 20; return { text: b.textContent.trim(), lines: Math.round((b.scrollHeight - parseFloat(getComputedStyle(b).paddingTop) - parseFloat(getComputedStyle(b).paddingBottom)) / lh) }; })()")
        check("18 dashboard: 'Spezialübung · Kombi' in one line at 390", lines["text"] == "Spezialübung · Kombi" and lines["lines"] <= 1, lines)
        await dash.screenshot(path=os.path.join(SHOTS, "dashboard_neuro_390_light.png"), full_page=True)
        check("7 dashboard marks the unlock code", "Freischaltung" in await dash.inner_text("#progTable"))
        await dash.fill("#pCode", "tools-neu"); await dash.fill("#pName", "Werkzeuge Fabian")
        await dash.click('#kindRow [data-kind="unlock"]')
        check("7 dashboard: Freischaltung builder with only Trainer-Werkzeuge", await dash.is_visible("#unlockBuilder") and await dash.locator("#unlockBuilder input[type=checkbox]").count() == 2)
        await dash.click("#pSaveBtn"); await dash.wait_for_timeout(150)
        check("7 dashboard: needs a choice", "Mindestens eine Freischaltung" in await dash.inner_text("#pMsg"))
        await dash.check('#unlockBuilder input[data-feature="trainer-tools"]'); await dash.click("#pSaveBtn"); await dash.wait_for_timeout(250)
        cfg = saved[-1]["config"] if saved else {}
        check("7 dashboard: saves feature-unlock trainer-tools", cfg.get("type") == "feature-unlock" and cfg.get("features") == ["trainer-tools"] and not cfg.get("lock"), cfg)
        await dash.screenshot(path=os.path.join(SHOTS, "dashboard_freischaltung_390_light.png"), full_page=True)
        await dash.click("text=Trainer-Werkzeuge >> nth=0"); await dash.wait_for_timeout(250)
        check("7 dashboard: an unlock code opens in its builder again", await dash.is_visible("#unlockBuilder") and await dash.is_checked('#unlockBuilder input[data-feature="trainer-tools"]'))
        check("7 dashboard: 'QR-Code zeigen' after saving", await dash.is_visible("#pQrBtn"))
        await dash.click("#pQrBtn"); await dash.wait_for_timeout(250)
        await dash.add_script_tag(url=DASH.rsplit("/", 1)[0] + "/jsqr.js")
        qr = await dash.evaluate("""(() => { const cv = document.getElementById('codeQrCanvas'); const g = cv.getContext('2d'); const d = g.getImageData(0, 0, cv.width, cv.height);
            const r = jsQR(d.data, cv.width, cv.height); return { text: r && r.data, url: cv.dataset.url, code: document.getElementById('codeQrText').textContent, hint: document.getElementById('codeQrHint').textContent, w: cv.getBoundingClientRect().width }; })()""")
        check("7 dashboard QR: decodes to <app>#code=<CODE>, code as text, hint", qr["text"] == qr["url"] and qr["url"].endswith("#code=tools-neu") and qr["code"] == "tools-neu"
              and "Trainer-QR-Code scannen" in qr["hint"] and qr["w"] >= 280, qr)
        await dash.screenshot(path=os.path.join(SHOTS, "dashboard_code_qr_390_light.png"))
        await dash.click('#codeQrSheet [data-close]'); await dash.wait_for_timeout(150)
        await dash.locator('#progTable [data-qr]').first.click(); await dash.wait_for_timeout(250)
        check("7 dashboard: 'QR-Code zeigen' in the codes table opens the QR (not the editor)", await dash.is_visible("#codeQrSheet") and (await dash.get_attribute("#codeQrCanvas", "data-url")).endswith("#code=" + await dash.inner_text("#codeQrText")))
        await dash.click('#codeQrSheet [data-close]'); await dash.wait_for_timeout(150)
        check("dashboard: no sideways scroll at 390", await dash.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"))
        await ctx.close()
        await b.close()

    passed = sum(1 for _, ok in results if ok)
    print(f"{passed}/{len(results)} checks passed")
    print("ERRORS:", errors)
    if passed != len(results) or errors:
        raise SystemExit(1)


asyncio.run(main())
