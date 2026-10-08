"""QR-Übergabe (Idee 69, Fabian 2026-10-08, Variante A + Kunden-Training).

Trainer side: Fortschritt "An Kunden übergeben" -> range chips (seit <Zeit> /
30 / 60 / 90 Min) + checkboxes -> one QR code (or several for a big payload)
-> "Fertig" asks "Diese N Trainings auf deinem Gerät löschen?" (Löschen /
Behalten). Client side: the app opens with #import=…, asks once, imports with
the tag "bei deinem Trainer", dedupes, clears the fragment. iPhone Safari gets
"Code kopieren" + the paste field in the home-screen app. Kunden-Training:
runs go to their own store, never into the trainer's history/progress/bests,
"Beenden" goes straight to the QR code and the runs vanish after "Fertig".
Also: QR decodes (OpenCV if installed), 390/1024 light/dark without sideways
scroll, no page errors."""
import asyncio
import base64
import json
import os
import time
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
ROOT = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "qr_uebergabe")

try:
    import cv2  # noqa: F401
    import numpy as np  # noqa: F401
    HAVE_CV = True
except Exception:  # pragma: no cover - decoder optional
    HAVE_CV = False

results = []
errors = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}" + (f"  [{str(extra)[:160]}]" if not ok and extra != "" else ""))


def iso(ms):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ms / 1000)) + ".000Z"


def entry(i, minutes_ago, title=None, kind="exercise", sec=300):
    ms = int(time.time() * 1000) - minutes_ago * 60000
    return {"id": str(1759900000000 + i), "ts": iso(ms), "rating": None, "kind": kind,
            "title": title or f"Training {i}", "seconds": sec, "exId": "farbfelder" if kind == "exercise" else None}


async def new_page(b, scheme="light", width=390, height=844, seed=None, extra_init=""):
    ctx = await b.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, locale="de-DE",
                              service_workers="block", has_touch=True)
    init = "try{localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1','{\"startCountdown\":false}');"
    if seed is not None:
        init += "if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');"
        for k, v in seed.items():
            init += f"localStorage.setItem({json.dumps(k)}, {json.dumps(json.dumps(v))});"
        init += "}"
    init += extra_init + "}catch(e){}"
    await ctx.add_init_script(init)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    return ctx, pg


async def ls(pg, key, fallback=None):
    v = await pg.evaluate(f"localStorage.getItem({json.dumps(key)})")
    return json.loads(v) if v else fallback


async def no_sideways(pg):
    return await pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")


async def qr_url(pg):
    return await pg.get_attribute("#handoverQrCanvas", "data-url")


def cv_decode(img):
    """OpenCV's classic detector misses some large versions; try Aruco too."""
    import cv2
    txt, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    if not txt and hasattr(cv2, "QRCodeDetectorAruco"):
        txt = cv2.QRCodeDetectorAruco().detectAndDecode(img)[0]
    return txt


async def decode_canvas(pg):
    """Decodes the canvas pixels (full resolution) with OpenCV."""
    if not HAVE_CV:
        return None
    import cv2
    import numpy as np
    data = await pg.evaluate("document.getElementById('handoverQrCanvas').toDataURL('image/png')")
    raw = base64.b64decode(data.split(",", 1)[1])
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    return cv_decode(img)


async def decode_screenshot(pg):
    if not HAVE_CV:
        return None
    import cv2
    import numpy as np
    raw = await pg.locator(".handover-qr-card").screenshot()
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    return cv_decode(img)


async def open_progress(pg):
    await pg.goto(ROOT + "?bereich=fortschritt")
    await pg.wait_for_timeout(400)


async def main():
    os.makedirs(SHOTS, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ================= trainer: range chips + checkboxes =================
        hist = [entry(1, 10, "Positionen merken"), entry(2, 40, "Farbfelder · Antippen"),
                entry(3, 80, "Gleichgewicht · Wörter"), entry(4, 180, "Optodrum (dein Aufwärmen)", kind="optodrum")]
        ctx, pg = await new_page(b, seed={"fwmc-history-v1": hist})
        await open_progress(pg)
        check("Fortschritt shows the history section with the 4 entries",
              await pg.is_visible("#progressHistorySection") and await pg.locator("#progressHistoryList li").count() == 3)
        check("Fortschritt: 'An Kunden übergeben' (secondary) + one-line explanation",
              await pg.is_visible("#handoverOpenBtn") and "secondary" in (await pg.get_attribute("#handoverOpenBtn", "class"))
              and "QR-Code" in await pg.inner_text("#handoverGroup"))
        await pg.screenshot(path=os.path.join(SHOTS, "1_fortschritt_390_light.png"), full_page=True)
        prog_before = await ls(pg, "fwmc-progress-v1")
        await pg.click("#handoverOpenBtn"); await pg.wait_for_timeout(250)
        check("opens the screen 'An Kunden übergeben'", await pg.is_visible("#handoverScreen"))
        since = (await pg.inner_text("#handoverSinceLabel")).strip()
        import calendar
        exp = time.localtime(calendar.timegm(time.strptime(hist[2]["ts"][:19], "%Y-%m-%dT%H:%M:%S")))
        exp_txt = f"seit {exp.tm_hour:02d}:{(exp.tm_min // 5) * 5:02d}"
        check("default 'seit' = earliest entry of the last 2 h, rounded down to 5 min", since == exp_txt, (since, exp_txt))
        boxes = pg.locator("#handoverList input[type=checkbox]")
        check("3 entries in range, all checked", await boxes.count() == 3 and all([await boxes.nth(i).is_checked() for i in range(3)]))
        check("button '3 Trainings übergeben'", (await pg.inner_text("#handoverGoBtn")).strip() == "3 Trainings übergeben"
              and await pg.is_enabled("#handoverGoBtn"))
        await pg.screenshot(path=os.path.join(SHOTS, "2_zeitraum_390_light.png"), full_page=True)
        counts = {}
        for r in ("30", "60", "90"):
            await pg.click(f'#handoverRangeRow [data-ho-range="{r}"]'); await pg.wait_for_timeout(100)
            counts[r] = await boxes.count()
        check("30/60/90 Min chips filter (1/2/3)", counts == {"30": 1, "60": 2, "90": 3}, counts)
        check("time picker only with 'seit'", not await pg.is_visible("#handoverSinceRow"))
        await pg.click('#handoverRangeRow [data-ho-range="since"]'); await pg.wait_for_timeout(100)
        t = time.localtime(time.time() - 200 * 60)
        await pg.fill("#handoverSinceInput", f"{t.tm_hour:02d}:{t.tm_min:02d}")
        await pg.dispatch_event("#handoverSinceInput", "change"); await pg.wait_for_timeout(100)
        n_since = await boxes.count()
        check("an earlier 'seit' time brings in the older entry", n_since == 4 or t.tm_hour > time.localtime().tm_hour, n_since)
        for i in range(await boxes.count()):
            await boxes.nth(i).uncheck()
        check("0 selected: button disabled", not await pg.is_enabled("#handoverGoBtn")
              and (await pg.inner_text("#handoverGoBtn")).strip() == "0 Trainings übergeben")
        await pg.click('#handoverRangeRow [data-ho-range="90"]'); await pg.wait_for_timeout(100)
        await boxes.nth(1).uncheck(); await boxes.nth(1).check()
        check("range change resets to all checked", await pg.inner_text("#handoverGoBtn") == "3 Trainings übergeben")
        tap_small = await pg.evaluate("""[...document.querySelectorAll('#handoverScreen button, #handoverScreen label.handover-check')].filter(e => e.offsetParent)
              .map(e => e.getBoundingClientRect()).filter(r => r.height < 44 || r.width < 44).length""")
        check("tap targets >= 44 px on the range screen", tap_small == 0, tap_small)

        # ================= QR screen =================
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(700)
        check("QR screen: title, meta '3 Trainings · letzte 90 Min.', no part nav",
              await pg.is_visible("#handoverQrScreen") and "3 Trainings" in await pg.inner_text("#handoverQrMeta")
              and not await pg.is_visible("#handoverPartNav"))
        url = await qr_url(pg)
        check("URL = app URL + #import=1.1.<g>.<data>", url and url.startswith(ROOT + "#import=1.1."), url)
        check("payload never holds the name or settings", url and "fwmc" not in url.split("#", 1)[1], url)
        dec = await decode_canvas(pg)
        if HAVE_CV:
            check("QR decodes (OpenCV, canvas pixels) to exactly the URL", dec == url, dec)
            check("QR decodes from a 390 px screenshot too", await decode_screenshot(pg) == url)
        else:
            check("QR rendered (no decoder installed)", int(await pg.get_attribute("#handoverQrCanvas", "data-modules") or 0) >= 21)
        await pg.screenshot(path=os.path.join(SHOTS, "3_qr_390_light.png"), full_page=True)

        # ================= client: import =================
        cctx, cp = await new_page(b)
        await cp.goto(url); await cp.wait_for_timeout(700)
        check("client: sheet '3 Trainings von deinem Trainer übernehmen?'",
              await cp.is_visible("#handoverImportSheet") and (await cp.inner_text("#handoverImportTitle")) == "3 Trainings von deinem Trainer übernehmen?")
        check("client: list of 3, Übernehmen / Nicht jetzt, no iOS copy outside iPhone Safari",
              await cp.locator("#handoverImportList li").count() == 3 and await cp.inner_text("#handoverImportYesBtn") == "Übernehmen"
              and await cp.inner_text("#handoverImportNoBtn") == "Nicht jetzt" and not await cp.is_visible("#handoverImportCopyBtn"))
        check("fragment cleared from the address bar", "#" not in cp.url, cp.url)
        await cp.screenshot(path=os.path.join(SHOTS, "4_uebernehmen_390_light.png"))
        await cp.click("#handoverImportYesBtn"); await cp.wait_for_timeout(300)
        ch = await ls(cp, "fwmc-history-v1", [])
        check("client history has the 3 entries, tagged trainer", len(ch) == 3 and all(e.get("trainer") == 1 for e in ch)
              and sorted(e["title"] for e in ch) == sorted(["Positionen merken", "Farbfelder · Antippen", "Gleichgewicht · Wörter"]), ch)
        check("ts kept (to the second), kind/seconds/exId kept",
              {e["srcId"]: e["ts"][:19] for e in ch} == {e["id"]: e["ts"][:19] for e in hist[:3]}
              and all(e["seconds"] == 300 for e in ch) and any(e.get("exId") == "farbfelder" for e in ch))
        cprog = await ls(cp, "fwmc-progress-v1", {})
        check("they count for the client's progress (3 runs)", sum(d["n"] for d in cprog.get("days", {}).values()) == 3, cprog)
        await open_progress(cp)
        tags = await cp.locator("#progressHistoryList .h-tag").all_inner_texts()
        check("history list shows 'bei deinem Trainer'", tags.count("bei deinem Trainer") == 3, tags)
        await cp.screenshot(path=os.path.join(SHOTS, "4b_verlauf_kunde_390_light.png"), full_page=True)
        # dedupe
        await cp.goto(url); await cp.wait_for_timeout(600)
        await cp.click("#handoverImportYesBtn"); await cp.wait_for_timeout(300)
        ch2 = await ls(cp, "fwmc-history-v1", [])
        toast = await cp.evaluate("(document.querySelector('.app-toast')||{}).textContent || ''")
        check("second scan does not double the entries", len(ch2) == 3 and "schon" in toast, (len(ch2), toast))
        cprog2 = await ls(cp, "fwmc-progress-v1", {})
        check("... nor the progress", sum(d["n"] for d in cprog2.get("days", {}).values()) == 3)
        # Nicht jetzt writes nothing
        cctx2, cp2 = await new_page(b)
        await cp2.goto(url); await cp2.wait_for_timeout(600)
        await cp2.click("#handoverImportNoBtn"); await cp2.wait_for_timeout(200)
        check("'Nicht jetzt' writes nothing", (await ls(cp2, "fwmc-history-v1", [])) == [] and not await cp2.is_visible("#handoverImportSheet"))
        # invalid data
        await cp2.goto(ROOT + "#import=1.1.abcd.zQUJDREVGR0g"); await cp2.wait_for_timeout(600)
        check("invalid data: one friendly error, nothing written",
              await cp2.is_visible("#handoverImportSheet") and await cp2.inner_text("#handoverImportTitle") == "Das hat nicht geklappt"
              and not await cp2.is_visible("#handoverImportYesBtn") and (await ls(cp2, "fwmc-history-v1", [])) == [])
        await cp2.screenshot(path=os.path.join(SHOTS, "4c_fehler_390_light.png"))
        await cp2.click("#handoverImportNoBtn")
        await cp2.goto(ROOT + "#import=1.1.abcd.jW1tdXRpbGF0ZWRd"); await cp2.wait_for_timeout(500)
        check("valid base64 but wrong JSON shape: same error", await cp2.inner_text("#handoverImportTitle") == "Das hat nicht geklappt"
              and (await ls(cp2, "fwmc-history-v1", [])) == [])
        await cctx2.close()

        # ================= trainer: Fertig -> delete =================
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(300)
        check("Fertig asks 'Diese 3 Trainings auf deinem Gerät löschen?' (Löschen / Behalten)",
              await pg.is_visible("#confirmSheet") and await pg.inner_text("#confirmTitle") == "Diese 3 Trainings auf deinem Gerät löschen?"
              and await pg.inner_text("#confirmYesBtn") == "Löschen" and await pg.inner_text("#confirmNoBtn") == "Behalten")
        await pg.screenshot(path=os.path.join(SHOTS, "5_aufraeumen_390_light.png"))
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        th = await ls(pg, "fwmc-history-v1", [])
        check("Löschen removes exactly those 3 entries", [e["id"] for e in th] == [hist[3]["id"]], [e["id"] for e in th])
        tprog = await ls(pg, "fwmc-progress-v1", {})
        check("trainer progress drops them too", sum(d["n"] for d in tprog["days"].values()) == 1
              and sum(d["n"] for d in prog_before["days"].values()) == 4, tprog)
        await ctx.close()
        await cctx.close()

        # ================= multi-part =================
        big = [entry(100 + i, 1 + i % 50, f"Objektverfolgung (MOT) · Runde {i} mit langem Namen", sec=60 + i) for i in range(150)]
        for i, e in enumerate(big):
            e["note"] = f"Stufe {i % 9} · Treffer {i % 13}/12"
        ctx, pg = await new_page(b, seed={"fwmc-history-v1": big})
        await open_progress(pg)
        await pg.click("#handoverOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click('#handoverRangeRow [data-ho-range="90"]'); await pg.wait_for_timeout(200)
        check("150 entries selected", await pg.inner_text("#handoverGoBtn") == "150 Trainings übergeben")
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(800)
        label = await pg.inner_text("#handoverPartLabel")
        check("large payload is split: 'Code 1 von N' with ‹ ›", await pg.is_visible("#handoverPartNav") and label.startswith("Code 1 von "), label)
        nparts = int(label.split()[-1]) if label.startswith("Code 1 von ") else 1
        urls = []
        for i in range(nparts):
            urls.append(await qr_url(pg))
            if HAVE_CV:
                d = await decode_canvas(pg)
                check(f"part {i + 1} decodes", d == urls[i], (len(urls[i]), d))
            if i < nparts - 1:
                await pg.click("#handoverNextBtn"); await pg.wait_for_timeout(300)
        check("each code <= ~1200 characters", all(len(u) <= 1200 for u in urls), [len(u) for u in urls])
        check("› disabled on the last code, ‹ enabled", not await pg.is_enabled("#handoverNextBtn") and await pg.is_enabled("#handoverPrevBtn"))
        await pg.screenshot(path=os.path.join(SHOTS, "3b_qr_mehrteilig_390_light.png"), full_page=True)
        cctx, cp = await new_page(b)
        await cp.goto(urls[0]); await cp.wait_for_timeout(600)
        check("client: first part -> 'Code 1 von N gelesen', asks for the next",
              await cp.inner_text("#handoverImportTitle") == f"Code 1 von {nparts} gelesen" and "Code 2" in await cp.inner_text("#handoverImportText"))
        await cp.screenshot(path=os.path.join(SHOTS, "4d_teil1_390_light.png"))
        await cp.click("#handoverImportNoBtn")
        # the iPhone camera opens each scan in a new tab: use a second page of the same context
        cp_b = await cctx.new_page()
        for u in urls[1:]:
            await cp_b.goto(u); await cp_b.wait_for_timeout(600)
        check("client: after the last part the import sheet lists all 150",
              await cp_b.inner_text("#handoverImportTitle") == "150 Trainings von deinem Trainer übernehmen?")
        await cp_b.click("#handoverImportYesBtn"); await cp_b.wait_for_timeout(300)
        ch = await ls(cp_b, "fwmc-history-v1", [])
        check("all 150 imported with notes", len(ch) == 150 and all(e.get("trainer") == 1 and e.get("note") for e in ch))
        check("parts store cleaned up", await ls(cp_b, "fwmc-import-parts-v1") is None)
        await cctx.close()
        await ctx.close()

        # ================= iPhone Safari: copy + paste into the home-screen app =================
        hist2 = [entry(201, 5, "Flash-Speicher-Test"), entry(202, 15, "Blitz-Raster")]
        ctx, pg = await new_page(b, seed={"fwmc-history-v1": hist2})
        await open_progress(pg)
        await pg.click("#handoverOpenBtn"); await pg.wait_for_timeout(200)
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(600)
        url2 = await qr_url(pg)
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(200)
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(200)
        check("Behalten keeps the entries", len(await ls(pg, "fwmc-history-v1", [])) == 2)
        sctx, sp = await new_page(b, extra_init="localStorage.setItem('fwmc-test-ios-browser','true');")
        await sctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=f"http://localhost:{PORT}")
        await sp.goto(url2); await sp.wait_for_timeout(600)
        check("iPhone Safari: explanation + 'Code kopieren' + 'Hier in Safari übernehmen'",
              await sp.is_visible("#handoverImportIos") and await sp.is_visible("#handoverImportCopyBtn")
              and await sp.inner_text("#handoverImportYesBtn") == "Hier in Safari übernehmen")
        await sp.screenshot(path=os.path.join(SHOTS, "4e_safari_hinweis_390_light.png"))
        await sp.click("#handoverImportCopyBtn"); await sp.wait_for_timeout(300)
        copied = await sp.evaluate("navigator.clipboard.readText()")
        check("copied text is the code", copied.startswith("1.1.code.") and len(copied) > 20, copied[:40])
        check("copy button confirms", "Kopiert" in await sp.inner_text("#handoverImportCopyBtn"))
        await sctx.close()
        actx, ap = await new_page(b)
        await open_progress(ap)
        await ap.click("#handoverPasteOpenBtn"); await ap.wait_for_timeout(200)
        await ap.fill("#handoverPasteInput", "hallo welt")
        await ap.click("#handoverPasteGoBtn"); await ap.wait_for_timeout(150)
        check("paste: garbage -> inline error, sheet stays", await ap.is_visible("#handoverPasteError") and await ap.is_visible("#handoverPasteSheet"))
        await ap.fill("#handoverPasteInput", "  " + copied[:30] + "\n" + copied[30:] + "  ")
        await ap.screenshot(path=os.path.join(SHOTS, "6_einfuegen_390_light.png"))
        await ap.click("#handoverPasteGoBtn"); await ap.wait_for_timeout(500)
        check("paste: same import sheet (no Safari hint inside the app)",
              await ap.inner_text("#handoverImportTitle") == "2 Trainings von deinem Trainer übernehmen?" and not await ap.is_visible("#handoverImportIos"))
        await ap.click("#handoverImportYesBtn"); await ap.wait_for_timeout(300)
        ah = await ls(ap, "fwmc-history-v1", [])
        check("paste import writes the 2 entries", len(ah) == 2 and all(e.get("trainer") == 1 for e in ah))
        await actx.close()
        await ctx.close()

        # ================= Kunden-Training =================
        own = [entry(301, 300, "Eigenes Training morgens", kind="free")]
        seed = {"fwmc-history-v1": own, "fwmc-remember-best-v1": {"leicht": 4},
                "fwmc-free-blocks-v1": [{"id": "f1", "kind": "check", "title": "Eisbad", "note": "", "minutes": 5, "items": []}]}
        ctx, pg = await new_page(b, seed=seed)
        await open_progress(pg)
        prog0 = await ls(pg, "fwmc-progress-v1")
        await pg.click("#clientRunStartBtn"); await pg.wait_for_timeout(300)
        strip = await pg.inner_text("#clientRunStrip")
        check("strip 'Kunden-Training · seit HH:MM' + Beenden", await pg.is_visible("#clientRunStrip") and "Kunden-Training · seit " in strip
              and await pg.is_visible("#clientRunEndBtn"), strip)
        check("session stored in fwmc-client-session-v1", (await ls(pg, "fwmc-client-session-v1") or {}).get("start"))
        await pg.screenshot(path=os.path.join(SHOTS, "7_kunden_training_390_light.png"))
        await pg.goto(ROOT + "?bereich=free"); await pg.wait_for_timeout(400)
        check("strip stays on other pages", await pg.is_visible("#clientRunStrip"))
        await pg.click('#freeOwnGrid [data-free-id="f1"]'); await pg.wait_for_timeout(200)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(300)
        check("strip hidden inside the player", not await pg.is_visible("#clientRunStrip"))
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(300)
        await pg.evaluate("localStorage.setItem('fwmc-remember-best-v1', JSON.stringify({leicht: 9}))")  # a client's best
        await pg.click("#freeDoneBackBtn"); await pg.wait_for_timeout(200)
        th = await ls(pg, "fwmc-history-v1", [])
        runs = await ls(pg, "fwmc-client-runs-v1", [])
        check("client run NOT in the trainer's history", [e["id"] for e in th] == [own[0]["id"]], th)
        check("client run stored flagged in fwmc-client-runs-v1", len(runs) == 1 and runs[0]["title"] == "Eisbad" and runs[0].get("client"))
        check("trainer progress unchanged (stats, streak, Wochenabschluss read it)", await ls(pg, "fwmc-progress-v1") == prog0)
        check("strip counts '1 Training'", "1 Training" in await pg.inner_text("#clientRunStrip"))
        await pg.click("#clientRunEndBtn"); await pg.wait_for_timeout(700)
        check("Beenden goes straight to the QR code with that 1 run", await pg.is_visible("#handoverQrScreen")
              and "1 Training" in await pg.inner_text("#handoverQrMeta"))
        check("strip gone, session cleared", not await pg.is_visible("#clientRunStrip") and await ls(pg, "fwmc-client-session-v1") is None)
        check("own best restored after the session", await ls(pg, "fwmc-remember-best-v1") == {"leicht": 4})
        curl = await qr_url(pg)
        await pg.screenshot(path=os.path.join(SHOTS, "7b_kunden_qr_390_light.png"), full_page=True)
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(300)
        check("Fertig: no question, runs removed", not await pg.is_visible("#confirmSheet") and (await ls(pg, "fwmc-client-runs-v1", [])) == []
              and len(await ls(pg, "fwmc-history-v1", [])) == 1)
        cctx, cp = await new_page(b)
        await cp.goto(curl); await cp.wait_for_timeout(600)
        await cp.click("#handoverImportYesBtn"); await cp.wait_for_timeout(300)
        ch = await ls(cp, "fwmc-history-v1", [])
        check("client receives the Kunden-Training run", len(ch) == 1 and ch[0]["title"] == "Eisbad" and ch[0].get("trainer") == 1)
        await cctx.close()
        # leftover runs (left the QR screen via ‹): shown on Fortschritt
        await pg.click("#clientRunStartBtn"); await pg.wait_for_timeout(200)
        await pg.goto(ROOT + "?bereich=free"); await pg.wait_for_timeout(300)
        await pg.click('#freeOwnGrid [data-free-id="f1"]'); await pg.wait_for_timeout(150)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(250)
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(250)
        await pg.click("#freeDoneBackBtn"); await pg.wait_for_timeout(150)
        await pg.click("#clientRunEndBtn"); await pg.wait_for_timeout(600)
        await pg.click("#handoverQrBackBtn"); await pg.wait_for_timeout(300)
        check("leftover runs: Fortschritt says '1 Training … noch nicht übergeben'",
              await pg.is_visible("#clientRunPending") and "noch nicht übergeben" in await pg.inner_text("#clientRunPending"))
        await pg.click("#clientRunPendingBtn"); await pg.wait_for_timeout(600)
        check("'QR-Code zeigen' reopens the code", await pg.is_visible("#handoverQrScreen"))
        await pg.click("#handoverQrBackBtn"); await pg.wait_for_timeout(200)
        await pg.click("#clientRunDropBtn"); await pg.wait_for_timeout(200)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        check("'Löschen' drops the leftovers", (await ls(pg, "fwmc-client-runs-v1", [])) == [] and not await pg.is_visible("#clientRunPending"))
        await ctx.close()

        # ================= privacy sentence =================
        ctx, pg = await new_page(b)
        await pg.goto(ROOT + "?bereich=heute"); await pg.wait_for_timeout(300)
        txt = await pg.evaluate("document.getElementById('privacySheet').textContent")
        check("privacy sheet mentions the QR handover without a server",
              "Bei der Übergabe an einen Kunden wandern Trainings per QR-Code direkt von Gerät zu Gerät, ohne Server." in " ".join(txt.split()))
        await ctx.close()

        # ================= layout: 390/1024 light/dark =================
        lay_hist = [entry(401, 5, "Positionen merken"), entry(402, 25, "Farbfelder · Antippen"), entry(403, 45, "Gleichgewicht · Wörter")]
        for w, h in ((390, 844), (1024, 1366)):
            for scheme in ("light", "dark"):
                tag = f"{w}_{scheme}"
                ctx, pg = await new_page(b, scheme, w, h, seed={"fwmc-history-v1": lay_hist})
                await open_progress(pg)
                ok = [await no_sideways(pg)]
                await pg.screenshot(path=os.path.join(SHOTS, f"L1_fortschritt_{tag}.png"), full_page=True)
                await pg.click("#handoverOpenBtn"); await pg.wait_for_timeout(250)
                ok.append(await no_sideways(pg))
                await pg.screenshot(path=os.path.join(SHOTS, f"L2_zeitraum_{tag}.png"), full_page=True)
                wrap = await pg.evaluate("""[...document.querySelectorAll('#handoverRangeRow .choice, #handoverGoBtn')].filter(e => e.getClientRects().length)
                    .filter(e => e.getBoundingClientRect().height > 64).map(e => e.textContent)""")
                ok.append(not wrap)
                await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(600)
                ok.append(await no_sideways(pg))
                await pg.screenshot(path=os.path.join(SHOTS, f"L3_qr_{tag}.png"), full_page=True)
                await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(250)
                await pg.screenshot(path=os.path.join(SHOTS, f"L5_aufraeumen_{tag}.png"))
                await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(200)
                await pg.click("#clientRunStartBtn"); await pg.wait_for_timeout(250)
                ok.append(await no_sideways(pg))
                sh = await pg.evaluate("document.getElementById('clientRunStrip').getBoundingClientRect().height")
                ok.append(44 <= sh <= 60)
                await pg.screenshot(path=os.path.join(SHOTS, f"L7_streifen_{tag}.png"))
                await pg.click("#clientRunEndBtn"); await pg.wait_for_timeout(300)
                await pg.click("#handoverPasteOpenBtn"); await pg.wait_for_timeout(200)
                await pg.screenshot(path=os.path.join(SHOTS, f"L6_einfuegen_{tag}.png"))
                await pg.click("#handoverPasteCancelBtn")
                cctx, cp = await new_page(b, scheme, w, h, extra_init="localStorage.setItem('fwmc-test-ios-browser','true');")
                await pg.click("#handoverOpenBtn"); await pg.wait_for_timeout(200)
                await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(600)
                await cp.goto(await qr_url(pg)); await cp.wait_for_timeout(600)
                ok.append(await no_sideways(cp))
                await cp.screenshot(path=os.path.join(SHOTS, f"L4_uebernehmen_{tag}.png"))
                await cctx.close()
                check(f"layout {tag}: no sideways scroll, chips/button one line, strip 44-60 px", all(ok), ok)
                await ctx.close()
        await b.close()

    check("no pageerror / console error", not errors, errors[:5])
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    print("ERRORS:", errors)
    if failed:
        print("FAILED:", failed)


asyncio.run(main())
