"""Gleichgewicht + VORtrain (Fabian 09.10. 👍): Modus "Wanderndes Ziel"
(Ziel gleitet im Takt hin und her, Kopf gegenläufig), Wortliste
"Richtungen" mit "Lies: das Gegenteil", Stand "Gehen"; Kombi/Vorlagen
tragen es über die Einstellungen. Run from tests/."""
import asyncio, json
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
OUT = "screenshots/"
results, errors = [], []
def check(name, ok, extra=""):
    results.append(bool(ok)); print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra != "" else ""))

async def ctx_page(b, store=None, scheme="light", w=390):
    ctx = await b.new_context(viewport={"width": w, "height": 844}, color_scheme=scheme, service_workers="block")
    base = {"fwmc-tips-seen": True, "fwmc-master-v1": {"startCountdown": False}, "fwmc-silent-hint-v1": True}
    base.update(store or {})
    js = "".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(json.dumps(v))});" for k, v in base.items())
    await ctx.add_init_script(f"if (!sessionStorage.getItem('seeded')) {{ {js} sessionStorage.setItem('seeded','1'); }}")
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    return ctx, pg

async def open_balance(pg):
    await pg.goto(URL + "?bereich=nat"); await pg.wait_for_timeout(500)
    await pg.click('#natHome .sub-tab[data-nat-sub="balance"]'); await pg.wait_for_timeout(150)
    await pg.click("#balanceOpenBtn"); await pg.wait_for_timeout(250)

async def translates(pg, sel, n=8, gap=110):
    out = []
    for _ in range(n):
        out.append(await pg.evaluate(f"(() => {{ const t = getComputedStyle(document.querySelector('{sel}')).translate; return t === 'none' ? 0 : parseFloat(t); }})()"))
        await pg.wait_for_timeout(gap)
    return out

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx, pg = await ctx_page(b)
        await open_balance(pg)
        check("mode row has Wanderndes Ziel", await pg.is_visible('#balanceModeRow [data-bal-mode="wander"]'))
        await pg.click('#balanceModeRow [data-bal-mode="wander"]'); await pg.wait_for_timeout(100)
        check("help explains the opposite head turn", "Gegenrichtung" in await pg.inner_text("#balanceModeHelp"))
        await pg.click('#balanceStanceRow [data-bal-stance="gehen"]'); await pg.wait_for_timeout(100)
        check("stance Gehen saved", json.loads(await pg.evaluate("localStorage.getItem('fwmc-balance-prefs-v1')")).get("stance") == "gehen")
        await pg.screenshot(path=OUT + "gleichgewicht_vor_ready.png", full_page=True)
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(600)
        xs = await translates(pg, "#balanceStick0", 12, 120)
        check("the stick glides from side to side", max(xs) > 20 and min(xs) < -20, xs)
        check("hint names Gehen", "Gehen" in await pg.inner_text("#balanceHint"))
        cue = await pg.inner_text("#balanceCue")
        check("cue says where the head goes", "Kopf" in cue, cue)
        box = await pg.evaluate("(() => { const r = document.getElementById('balanceStick0').getBoundingClientRect(); const s = document.getElementById('balanceStage').getBoundingClientRect(); return [r.left - s.left, s.right - r.right]; })()")
        check("stick stays on the stage", box[0] >= 0 and box[1] >= 0, box)
        await pg.screenshot(path=OUT + "gleichgewicht_vor_wander.png")
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(200)
        a = await translates(pg, "#balanceStick0", 3, 200)
        check("paused: no movement", len(set(a)) == 1, a)
        await pg.click("#balanceResumeBtn"); await pg.wait_for_timeout(200)
        await pg.click("#balanceBackBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmYesBtn"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        await ctx.close()

        # words: Richtungen + Gegenteil, wander without Takt still moves
        ctx, pg = await ctx_page(b, {"fwmc-balance-prefs-v1": {"mode": "wander", "content": "woerter", "metro": False}})
        await open_balance(pg)
        check("Richtungen in the word list", await pg.is_visible('#balanceWordListRow [data-bal-wordlist="richtungen"]'))
        await pg.click('#balanceWordListRow [data-bal-wordlist="richtungen"]'); await pg.wait_for_timeout(100)
        vis = await pg.evaluate("[...document.querySelectorAll('#balanceWordReadRow [data-bal-wordread]')].filter(b => !b.hidden).map(b => b.dataset.balWordread)")
        check("Lies: das Wort / das Gegenteil (no Farbe)", vis == ["wort", "gegenteil"], vis)
        await pg.click('#balanceWordReadRow [data-bal-wordread="gegenteil"]'); await pg.wait_for_timeout(100)
        check("help explains the opposite", "Gegenteil" in await pg.inner_text("#balanceWordHelp"))
        await pg.click('#balanceWordListRow [data-bal-wordlist="farben"]'); await pg.wait_for_timeout(100)
        vis2 = await pg.evaluate("[...document.querySelectorAll('#balanceWordReadRow [data-bal-wordread]')].filter(b => !b.hidden).map(b => b.dataset.balWordread)")
        check("Farbwörter: das Wort / die Farbe", vis2 == ["wort", "farbe"], vis2)
        await pg.click('#balanceWordListRow [data-bal-wordlist="richtungen"]'); await pg.wait_for_timeout(100)
        await pg.screenshot(path=OUT + "gleichgewicht_vor_words_ready.png", full_page=True)
        await pg.click("#balanceReadyStartBtn"); await pg.wait_for_timeout(600)
        word = await pg.inner_text("#balanceWord")
        check("a direction word is shown", word in ("LINKS", "RECHTS", "OBEN", "UNTEN"), word)
        check("caption 'Sag das Gegenteil'", await pg.get_attribute("#balanceWord", "data-cap") == "Sag das Gegenteil")
        xs = await translates(pg, "#balanceWord", 14, 110)
        check("word wanders even without Takt", max(xs) > 15 and min(xs) < -15, xs)
        await pg.screenshot(path=OUT + "gleichgewicht_vor_words.png")
        await pg.click("#balancePauseBtn"); await pg.wait_for_timeout(250)
        pv = await pg.evaluate("[...document.querySelectorAll('#balancePauseOverlay [data-pause-choice=\"bal-wordread\"] [data-pause-val]')].filter(b => !b.hidden).map(b => b.dataset.pauseVal)")
        check("pause sheet: Lies row with Wort/Gegenteil", pv == ["wort", "gegenteil"], pv)
        await pg.screenshot(path=OUT + "gleichgewicht_vor_pause.png", full_page=True)
        await ctx.close()

        # Kombi block carries the mode
        combo = [{"id": "k1", "name": "VOR", "blocks": [{"domain": "balance", "duration": 60, "prefs": {"mode": "wander", "metro": True, "bpm": 60}}],
                  "createdAt": "2026-10-09T08:00:00Z", "lastUsed": "2026-10-09T08:00:00Z"}]
        ctx, pg = await ctx_page(b, {"fwmc-combo-saved-v1": combo})
        await pg.goto(URL + "?bereich=breath"); await pg.wait_for_timeout(500)
        await pg.click("#breathHome .combo-entry-link"); await pg.wait_for_timeout(250)
        await pg.click("#comboSavedList .bundle-item >> nth=0"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#comboStartBtn"): await pg.click("#comboStartBtn")
        await pg.wait_for_timeout(900)
        xs = await translates(pg, "#balanceStick0", 12, 120)
        check("Kombi block plays Wanderndes Ziel", max(xs) > 20 and min(xs) < -20, xs)
        check("Kombi did not change own settings", await pg.evaluate("localStorage.getItem('fwmc-balance-prefs-v1')") is None)
        await ctx.close()
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
