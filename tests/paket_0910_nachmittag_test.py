"""Paket 09.10. nachmittags (Fabian's answers on the decision page).

- QR handover carries freeId/neuroEx (sub field); a plan entry naming one
  Eigenes Training is ticked only by exactly that training.
- Verschickt: sent runs stay 21 days in fwmc-trainer-sent-v1, tagged
  "verschickt" in Gespeicherte Trainings, filter chip "Verschickt".
- Ausgeblendete zeigen: hidden own runs come back in the overview on tap.
- Kürzel pro Kunden-Training (sheet, only on this device, not in the QR).
- "Und wie geht es dir jetzt?" after a finished training when today's
  Tagesform is set; Fortschritt shows "Vorher und nachher".
- Körperregel je Farbe per exercise (Feineinstellungen, ready note, preset
  snapshot, "Von anderer Übung übernehmen").
- First tap on a greyed equipment exercise asks "Hast du …?".
- Cardio guest Fixpunkt text up to 12 characters.
No page errors."""
import asyncio
import json
import os
import time
from datetime import datetime, timezone
from playwright.async_api import async_playwright

PORT = os.environ.get("FWMC_PORT", "8845")
ROOT = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results, errors = [], []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}" + (f"  [{str(extra)[:240]}]" if not ok and extra != "" else ""))


FREE = [{"id": "f1", "kind": "check", "title": "Dehnen eigen", "note": "", "minutes": 5, "items": []},
        {"id": "f2", "kind": "check", "title": "Eisbad", "note": "", "minutes": 5, "items": []}]


def now_iso(offset_s=0):
    return datetime.fromtimestamp(time.time() - offset_s, timezone.utc).isoformat().replace("+00:00", "Z")


async def new_page(b, extra="", w=390, h=844):
    ctx = await b.new_context(viewport={"width": w, "height": h}, locale="de-DE", service_workers="block", has_touch=True)
    init = ("try{if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');"
            "localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1','{\"startCountdown\":false}');"
            f"localStorage.setItem('fwmc-free-blocks-v1', {json.dumps(json.dumps(FREE))});"
            "localStorage.setItem('fwmc-test-trainer-tools','true');" + extra + "}}catch(e){}")
    await ctx.add_init_script(init)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    return ctx, pg


async def ls(pg, key, fallback=None):
    v = await pg.evaluate(f"localStorage.getItem({json.dumps(key)})")
    return json.loads(v) if v else fallback


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---- 1. QR sub field + plan tick ----
        ctx, pg = await new_page(b)
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(400)
        e = {"id": "123", "ts": now_iso(), "kind": "free", "title": "Dehnen eigen", "seconds": 60, "freeId": "f1"}
        packed = await pg.evaluate("(e) => window.__ho0910.pack(e)", e)
        un = await pg.evaluate("(a) => window.__ho0910.unpack(a)", packed)
        check("QR packs the freeId and reads it back", len(packed) == 11 and un and un["sub"] == "f1", packed)
        bad = await pg.evaluate("(a) => window.__ho0910.unpack(a)", packed[:10] + ["<x>"])
        check("QR rejects a strange sub field", bad is None)
        today = await pg.evaluate("(() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); })()")
        ex = [{"id": "x1", "area": "free", "what": "free:f1"}]
        other = await pg.evaluate("([d, ex, h]) => window.__ho0910.planTry(d, ex, h)", [today, ex, [{"kind": "free", "freeId": "f2", "ts": now_iso()}]])
        same = await pg.evaluate("([d, ex, h]) => window.__ho0910.planTry(d, ex, h)", [today, ex, [{"kind": "free", "freeId": "f1", "ts": now_iso(), "trainer": 1}]])
        gen = await pg.evaluate("([d, ex, h]) => window.__ho0910.planTry(d, ex, h)", [today, [{"id": "x2", "area": "free", "what": ""}], [{"kind": "free", "freeId": "f2", "ts": now_iso()}]])
        both = await pg.evaluate("([d, ex, h]) => window.__ho0910.planTry(d, ex, h)", [today, [{"id": "x2", "area": "free", "what": ""}, {"id": "x1", "area": "free", "what": "free:f1"}], [{"kind": "free", "freeId": "f1", "ts": now_iso()}]])
        check("plan 'Dehnen' stays open after a different Eigenes Training", other and not other[0]["done"], other)
        check("plan 'Dehnen' is ticked by Dehnen from the trainer's QR", same and same[0]["done"], same)
        check("a general Eigenes-Training entry is ticked by any of them", gen and gen[0]["done"], gen)
        check("the specific entry gets the matching run first", both and [o["done"] for o in both if o["what"] == "free:f1"] == [True], both)
        await ctx.close()

        # ---- 2. Verschickt + Ausgeblendete zeigen ----
        hist = [{"id": "own1", "ts": now_iso(600), "kind": "free", "title": "Eisbad", "seconds": 120, "freeId": "f2"},
                {"id": "own2", "ts": now_iso(1200), "kind": "free", "title": "Dehnen eigen", "seconds": 90, "freeId": "f1"}]
        seed = (f"localStorage.setItem('fwmc-history-v1', {json.dumps(json.dumps(hist))});"
                "localStorage.setItem('fwmc-trainer-hidden-v1', '[\"own2\"]');")
        ctx, pg = await new_page(b, extra=seed)
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(400)
        await pg.locator(".trainer-mode-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.click("#tmStoreBtn"); await pg.wait_for_timeout(350)
        titles = await pg.locator("#handoverList .h-title").all_inner_texts()
        check("overview hides the hidden own run at first", len(titles) == 1 and "Eisbad" in titles[0], titles)
        hb = pg.locator("#handoverHiddenBtn")
        check("'Ausgeblendete zeigen (1)' offered", await hb.is_visible() and "(1)" in await hb.inner_text(), await hb.inner_text())
        await hb.click(); await pg.wait_for_timeout(200)
        titles = await pg.locator("#handoverList .h-title").all_inner_texts()
        check("hidden own run is back, tagged 'ausgeblendet'", any("Dehnen" in t and "Ausgeblendet" in t for t in titles), titles)
        check("button now reads 'wieder verbergen'", "verbergen" in await hb.inner_text())
        # send Eisbad
        await pg.locator("#handoverList li", has_text="Eisbad").locator("input").check(); await pg.wait_for_timeout(100)
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(700)
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(400)
        sent = await ls(pg, "fwmc-trainer-sent-v1", [])
        h_now = await ls(pg, "fwmc-history-v1", [])
        check("sent run kept in fwmc-trainer-sent-v1 with a time stamp", len(sent) == 1 and sent[0]["id"] == "own1" and isinstance(sent[0].get("sent"), (int, float)), sent)
        check("sent own run left the history (as before)", not any(x["id"] == "own1" for x in h_now))
        await pg.locator(".trainer-mode-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.click("#tmStoreBtn"); await pg.wait_for_timeout(350)
        rows = await pg.locator("#handoverList li").all_inner_texts()
        check("overview lists it as 'verschickt'", any("Eisbad" in r and "Verschickt" in r for r in rows), rows)
        await pg.click('#handoverKindRow [data-ho-kind="sent"]'); await pg.wait_for_timeout(200)
        rows = await pg.locator("#handoverList li").all_inner_texts()
        check("filter 'Verschickt' shows only sent runs", len(rows) == 1 and "Verschickt" in rows[0], rows)
        await pg.locator("#handoverList li input").first.check(); await pg.wait_for_timeout(100)
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(700)
        check("a sent run can be shown again as QR", await pg.is_visible("#handoverQrScreen"))
        await pg.click("#handoverDoneBtn"); await pg.wait_for_timeout(300)
        check("sending it again keeps one copy", len(await ls(pg, "fwmc-trainer-sent-v1", [])) == 1)
        # old sent runs are cleaned up after 21 days
        await pg.evaluate("(() => { const l = JSON.parse(localStorage.getItem('fwmc-trainer-sent-v1')); l[0].sent = Date.now() - 22 * 86400e3; localStorage.setItem('fwmc-trainer-sent-v1', JSON.stringify(l)); })()")
        await pg.locator(".trainer-mode-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.click("#tmStoreBtn"); await pg.wait_for_timeout(350)
        check("after 21 days the sent copy is gone", len(await ls(pg, "fwmc-trainer-sent-v1", [])) == 0)
        await ctx.close()

        # ---- 3. Kürzel pro Kunden-Training ----
        ctx, pg = await new_page(b, extra="localStorage.setItem('fwmc-test-clienttag','true');")
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(400)
        await pg.locator(".trainer-mode-btn:visible").first.click(); await pg.wait_for_timeout(150)
        await pg.click('#tmModes [data-tm="client"]'); await pg.wait_for_timeout(400)
        check("Kürzel sheet opens when 'Mit Kunde' starts", await pg.is_visible("#clientTagSheet"))
        await pg.fill("#clientTagInput", "MK Max"); await pg.click("#clientTagOkBtn"); await pg.wait_for_timeout(200)
        sess = await ls(pg, "fwmc-client-session-v1", {})
        check("Kürzel stored, max 4 characters, no spaces", sess.get("tag") == "MKM", sess.get("tag"))
        await pg.goto(ROOT + "?bereich=free"); await pg.wait_for_timeout(350)
        await pg.click('#freeOwnGrid [data-free-id="f2"]'); await pg.wait_for_timeout(150)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(250)
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(250)
        runs = await ls(pg, "fwmc-client-runs-v1", [])
        check("client run carries the Kürzel", runs and runs[0].get("tag") == "MKM", runs)
        packed = await pg.evaluate("(e) => window.__ho0910.pack(e)", runs[0])
        check("Kürzel never travels in the QR", "MKM" not in json.dumps(packed), packed)
        await ctx.close()

        # ---- 4. Vorher und nachher ----
        today_key = datetime.now().strftime("%Y-%m-%d")
        mood = {today_key: {"v": 1, "at": int(time.time() * 1000)}}
        ctx, pg = await new_page(b, extra=f"localStorage.setItem('fwmc-mood-v1', {json.dumps(json.dumps(mood))});")
        await pg.goto(ROOT + "?bereich=free"); await pg.wait_for_timeout(350)
        await pg.click('#freeOwnGrid [data-free-id="f2"]'); await pg.wait_for_timeout(150)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(250)
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(400)
        q = pg.locator("#freeDonePanel .mood-after")
        check("done panel asks 'Und wie geht es dir jetzt?'", await q.is_visible() and "jetzt" in await q.inner_text())
        await q.locator('[data-mood-after="3"]').click(); await pg.wait_for_timeout(150)
        h0 = (await ls(pg, "fwmc-history-v1", []))[0]
        check("answer stored on the run (vorher müde, jetzt fit)", h0.get("moodBefore") == 1 and h0.get("moodAfter") == 3, h0)
        check("thank-you line names before and after", "Vorher müde, jetzt fit" in await q.inner_text())
        check("one question per panel: the 1-5 rating steps aside", await pg.locator("#freeDonePanel .rating:not(.mood-after):visible").count() == 0)
        # three answers -> Fortschritt summary
        await pg.evaluate("(() => { const l = JSON.parse(localStorage.getItem('fwmc-history-v1')); const b = l[0]; for (let i = 1; i < 3; i++) l.push({...b, id: 'm' + i, moodAfter: i === 1 ? 1 : 2}); localStorage.setItem('fwmc-history-v1', JSON.stringify(l)); })()")
        await pg.goto(ROOT + "?bereich=fortschritt"); await pg.wait_for_timeout(500)
        txt = await pg.inner_text("#progressMoodGroup")
        check("Fortschritt shows 'Vorher und nachher' per area", "Vorher und nachher" in txt and "Eigenes Training" in txt and "2 von 3 Mal danach besser" in txt, txt[-300:])
        await ctx.close()
        ctx, pg = await new_page(b)
        await pg.goto(ROOT + "?bereich=free"); await pg.wait_for_timeout(350)
        await pg.click('#freeOwnGrid [data-free-id="f2"]'); await pg.wait_for_timeout(150)
        await pg.click("#freeStartBtn"); await pg.wait_for_timeout(250)
        await pg.click("#freeTickBtn"); await pg.wait_for_timeout(400)
        check("no question without today's Tagesform", await pg.locator("#freeDonePanel .mood-after").count() == 0)
        await ctx.close()

        # ---- 5. Körperregel je Farbe ----
        ctx, pg = await new_page(b)
        await pg.goto(ROOT + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(250)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(150)
        check("Körperregel box in the Feineinstellungen", await pg.is_visible("#bodyRuleBox"))
        await pg.check("#bodyRuleOn"); await pg.wait_for_timeout(150)
        first = pg.locator("#bodyRuleRows [data-body-col]").first
        col = await first.get_attribute("data-body-col")
        await pg.click(f'#bodyRuleRows [data-body-col="{col}"][data-val="haende"]'); await pg.wait_for_timeout(150)
        note = await pg.inner_text("#zusNote")
        check("ready note names the Körperregel", "körperregel" in note.lower() and "beide Hände hoch" in note, note)
        prefs = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}')")
        zo = (prefs.get("zusOben") or {}).get("vt-color", {})
        check("rule stored for this exercise only", zo.get("body", {}).get("rules", {}).get(col) == "haende" and not (prefs.get("zusOben") or {}).get("farbfelder", {}).get("body"), zo)
        await pg.goto(ROOT + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(250)
        await pg.click("#advanced summary"); await pg.wait_for_timeout(150)
        await pg.click("#bodyRuleXfer .xfer-btn"); await pg.wait_for_timeout(150)
        items = await pg.locator("#xferList .xfer-item").all_inner_texts()
        check("'Von anderer Übung übernehmen' offers the rule from Farbe", any("Wie bei" in i and "Hände" in i for i in items), items)
        await pg.locator("#xferList .xfer-item").first.click(); await pg.wait_for_timeout(200)
        prefs = await pg.evaluate("JSON.parse(localStorage.getItem('fwmc-webapp-v3') || '{}')")
        check("rule copied to Farbfelder", ((prefs.get("zusOben") or {}).get("farbfelder", {}).get("body") or {}).get("rules", {}).get(col) == "haende")
        await ctx.close()

        # ---- 6. First grey equipment exercise ----
        ctx, pg = await new_page(b, extra="localStorage.setItem('fwmc-test-gear','1');localStorage.setItem('fwmc-test-gearfirst','true');")
        await pg.goto(ROOT + "?bereich=visual"); await pg.wait_for_timeout(400)
        grey = pg.locator(".excard.gear-missing").first
        check("a greyed equipment exercise exists", await grey.count() == 1)
        await grey.click(); await pg.wait_for_timeout(600)
        check("first tap asks 'Hast du …?'", await pg.is_visible("#gearFirstSheet") and (await pg.inner_text("#gearFirstTitle")).startswith("Hast du"))
        n_more = await pg.locator("#gearFirstMore input[data-gear-have]").count()
        check("sheet offers the other Hilfsmittel to tick", n_more >= 2, n_more)
        await pg.click("#gearFirstYesBtn"); await pg.wait_for_timeout(150)
        await pg.locator("#gearFirstMore input[data-gear-have]").first.check(); await pg.wait_for_timeout(150)
        owned = await ls(pg, "fwmc-gear-v1", {})
        check("'Ja, hab ich' + one more tick land in Meine Hilfsmittel", len([k for k, v in owned.items() if v]) >= 2, owned)
        await pg.click("#gearFirstDoneBtn"); await pg.wait_for_timeout(150)
        await pg.goto(ROOT + "?bereich=visual"); await pg.wait_for_timeout(400)
        g2 = pg.locator(".excard.gear-missing").first
        if await g2.count():
            await g2.click(); await pg.wait_for_timeout(600)
        check("asks only once", not await pg.is_visible("#gearFirstSheet"))
        await ctx.close()

        # ---- 7. Cardio guest Fixpunkt text 12 characters ----
        ctx, pg = await new_page(b)
        await pg.goto(ROOT + "?bereich=cardio"); await pg.wait_for_timeout(400)
        ml = await pg.evaluate("[...document.querySelectorAll('input[data-fixchar]')].map(i => i.maxLength)")
        check("Cardio guest Fixpunkt fields allow 12 characters", all(m == 12 for m in ml), ml)
        await ctx.close()

        await b.close()
    check("no page errors", not errors, errors[:3])
    ok = sum(1 for _, v in results if v)
    print(f"{ok}/{len(results)} passed")
    if ok != len(results):
        print("SOME FAILED")


asyncio.run(main())
