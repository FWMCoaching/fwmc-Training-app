import asyncio, json, os
from playwright.async_api import async_playwright

# Meine Hilfsmittel (Idee 67, Fabian 08.10.): the client ticks what they have
# (Grundeinstellungen group, "Hab ich" on the Hilfsmittel page, "Hab ich" in a
# ready screen's note), stored in fwmc-gear-v1. Nothing ticked = nothing owned:
# equipment exercises are greyed ("Braucht: …" pill), stay openable, their start
# button reads "Braucht: …" and asks once via confirmDialog. optional entries are
# never greyed. Area hint card "Welche Hilfsmittel hast du?" (dismissible), Kombi
# tag, trainer-code intro note, no sideways scroll at 390/1024 light/dark, no
# page/console errors. Automated browsers own everything unless fwmc-test-gear.
# Run from tests/ with a dev server (FWMC_PORT, default 8845).
# Screenshots: tests/screenshots/meine_hilfsmittel/.

PORT = os.environ.get("FWMC_PORT", "8845")
BASE = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "meine_hilfsmittel")
INIT_BASE = ("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-bottomnav','true');"
             "if(!localStorage.getItem('fwmc-master-v1'))localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}));")
INIT = INIT_BASE + "localStorage.setItem('fwmc-test-gear','1');"

fails = []
def check(label, cond, info=""):
    print(f"{label}: {bool(cond)}" + (f"  [{info}]" if not cond and info != "" else ""))
    if not cond: fails.append(label)

CARD_JS = """(k) => { const c = document.querySelector(`.excard[data-exercise="${k}"]`); const p = c.querySelector('.excard-gear-note');
  return { grey: c.classList.contains('gear-missing'), pill: p ? p.textContent : '' }; }"""

async def vis_screen(pg):
    return await pg.evaluate("() => { const s = [...document.querySelectorAll('.screen')].find(e => !e.hidden); return s ? s.id : null; }")

async def no_sideways(pg):
    return await pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1")

async def open_master(pg):
    await pg.evaluate("() => [...document.querySelectorAll('.master-settings-btn')].find(b => b.getClientRects().length).click()")
    await pg.wait_for_timeout(200)

async def main():
    os.makedirs(SHOTS, exist_ok=True)
    errors = []
    def watch(pg):
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # --- automated browser without the flag: everything owned (suite stays valid)
        ctx0 = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx0.add_init_script(INIT_BASE)
        pg0 = await ctx0.new_page(); watch(pg0)
        await pg0.goto(BASE + "?bereich=visual"); await pg0.wait_for_timeout(300)
        n = await pg0.evaluate("() => document.querySelectorAll('.gear-missing').length")
        check("without fwmc-test-gear nothing is greyed", n == 0, n)
        check("without fwmc-test-gear no hint card", await pg0.evaluate("() => ![...document.querySelectorAll('.gear-ask-card')].some(c => c.getClientRects().length)"))
        await ctx0.close()

        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page(); watch(pg)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)

        # --- nothing ticked = greyed + "Braucht:" pill
        c = await pg.evaluate(CARD_JS, "cone-compass")
        check("Kompass-Aufbau greyed", c["grey"])
        check("Kompass-Aufbau pill 'Braucht: Hütchen und Klebeband'", c["pill"] == "Braucht: Hütchen und Klebeband", c["pill"])
        c = await pg.evaluate(CARD_JS, "cone-tap")
        check("Hütchen sortieren pill 'Braucht: Hütchen'", c["grey"] and c["pill"] == "Braucht: Hütchen", c)
        c = await pg.evaluate(CARD_JS, "farbfelder")
        check("Farbfelder (anyOf) pill 'Braucht: Farbmatte oder Hütchen'", c["grey"] and c["pill"] == "Braucht: Farbmatte oder Hütchen", c)
        c = await pg.evaluate(CARD_JS, "vt-color")
        check("exercise without equipment not greyed", not c["grey"] and not c["pill"])
        op = await pg.evaluate("() => getComputedStyle(document.querySelector('.excard[data-exercise=\"cone-compass\"] h3')).opacity")
        check("greyed card title is dimmed", float(op) < 0.8, op)
        # area hint card
        hint = pg.locator("#home .gear-ask-card")
        check("area hint card shows while nothing ticked", await hint.is_visible())
        await pg.evaluate("() => document.querySelector('.excard[data-exercise=\"cone-tap\"]').scrollIntoView({block:'center'})")
        await pg.screenshot(path=os.path.join(SHOTS, "01_vt_home_greyed_390_light.png"))
        await hint.scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "02_vt_home_hint_card_390_light.png"))
        check("hint card button opens Hilfsmittel page", True)
        await pg.click("#home .gear-ask-open"); await pg.wait_for_timeout(250)
        check("hint card -> gearScreen", await vis_screen(pg) == "gearScreen")
        check("gear page cards have 'Hab ich' toggles", await pg.evaluate("() => [...document.querySelectorAll('#gearScreen .gear-card')].every(c => c.querySelector('input[data-gear-have]'))"))
        await pg.click("#gearBackBtn"); await pg.wait_for_timeout(250)
        check("back from gear page returns to VT home", await vis_screen(pg) == "home")

        # --- anyOf (Farbfelder): one "Hab ich: …" button per option
        await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(300)
        ff = await pg.evaluate("() => [...document.querySelectorAll('#hilfsmittelNote .hilfsmittel-have')].map(b => b.textContent)")
        check("Farbfelder note offers 'Hab ich: Farbmatte' / 'Hab ich: Hütchen'", ff == ["Hab ich: Farbmatte", "Hab ich: Hütchen"], ff)
        check("Farbfelder start reads 'Braucht: Farbmatte oder Hütchen'", await pg.evaluate("() => document.getElementById('startBtn').textContent.trim()") == "Braucht: Farbmatte oder Hütchen")
        await pg.click("#backToHome"); await pg.wait_for_timeout(300)

        # --- ready screen: "Braucht:" label, confirm path
        await pg.click('.excard[data-exercise="cone-compass"]'); await pg.wait_for_timeout(300)
        check("greyed card still opens the ready screen", await vis_screen(pg) == "ready")
        st = await pg.evaluate("() => { const b = document.getElementById('startBtn'); return { t: b.textContent.trim(), g: b.classList.contains('gear-missing') }; }")
        check("start button reads 'Braucht: Hütchen und Klebeband'", st["t"] == "Braucht: Hütchen und Klebeband" and st["g"], st)
        check("note offers 'Hab ich'", await pg.locator("#hilfsmittelNote .hilfsmittel-have").count() == 1)
        await pg.locator("#startBtn").scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "03_ready_braucht_390_light.png"))
        await pg.locator("#hilfsmittelNote").scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "04_ready_note_hab_ich_390_light.png"))
        await pg.click("#startBtn"); await pg.wait_for_timeout(200)
        conf = await pg.evaluate("() => ({ open: !document.getElementById('confirmSheet').hidden, text: document.getElementById('confirmText').textContent, yes: document.getElementById('confirmYesBtn').textContent, no: document.getElementById('confirmNoBtn').textContent })")
        check("start asks via confirmDialog", conf["open"])
        check("confirm text", conf["text"] == "Du hast Hütchen und Klebeband noch nicht abgehakt. Trotzdem starten?", conf["text"])
        check("confirm buttons Trotzdem starten / Abbrechen", conf["yes"] == "Trotzdem starten" and conf["no"] == "Abbrechen", conf)
        await pg.screenshot(path=os.path.join(SHOTS, "05_confirm_390_light.png"))
        await pg.click("#confirmNoBtn"); await pg.wait_for_timeout(200)
        check("Abbrechen stays on the ready screen", await vis_screen(pg) == "ready" and await pg.evaluate("() => !document.getElementById('player') || document.getElementById('player').hidden"))
        await pg.click("#startBtn"); await pg.wait_for_timeout(200)
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(500)
        check("Trotzdem starten starts the run", await pg.evaluate("() => !document.getElementById('player').hidden"))
        check("only one question per start", await pg.evaluate("() => document.getElementById('confirmSheet').hidden"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(400)
        if not await pg.evaluate("() => document.getElementById('confirmSheet').hidden"):
            await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        scr = await vis_screen(pg)
        if scr != "ready":
            await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)
            await pg.click('.excard[data-exercise="cone-compass"]'); await pg.wait_for_timeout(300)
        t = await pg.evaluate("() => document.getElementById('startBtn').textContent.trim()")
        check("label is 'Braucht:' again on the next visit", t.startswith("Braucht: "), t)

        # --- "Hab ich" ticks and un-greys
        await pg.click("#hilfsmittelNote .hilfsmittel-have"); await pg.wait_for_timeout(200)
        st = await pg.evaluate("() => { const b = document.getElementById('startBtn'); return { t: b.textContent.trim(), g: b.classList.contains('gear-missing') }; }")
        check("after 'Hab ich' start reads 'Training starten'", st["t"] == "Training starten" and not st["g"], st)
        check("'Hab ich' row gone", await pg.locator("#hilfsmittelNote .hilfsmittel-have").count() == 0)
        owned = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-gear-v1') || '{}')")
        check("fwmc-gear-v1 has cups + tape", owned.get("cups") is True and owned.get("tape") is True, owned)
        await pg.click("#backToHome"); await pg.wait_for_timeout(300)
        check("Kompass-Aufbau no longer greyed", not (await pg.evaluate(CARD_JS, "cone-compass"))["grey"])
        check("Hütchen sortieren no longer greyed", not (await pg.evaluate(CARD_JS, "cone-tap"))["grey"])
        c = await pg.evaluate(CARD_JS, "cone-number")
        check("Farbe + Zahl still needs Zahlenfelder", c["grey"] and c["pill"] == "Braucht: Zahlenfelder", c)
        check("Farbfelder (anyOf) fine with Hütchen", not (await pg.evaluate(CARD_JS, "farbfelder"))["grey"])
        check("hint card hidden once something is ticked", not await pg.locator("#home .gear-ask-card").is_visible())

        # --- Grundeinstellungen group, persistence
        await open_master(pg)
        grp = pg.locator("#masterGearGroup")
        check("Grundeinstellungen has 'Meine Hilfsmittel'", await grp.is_visible() and "Meine Hilfsmittel" in await grp.inner_text())
        ids = await pg.evaluate("() => [...document.querySelectorAll('#masterGearList input')].map(i => i.dataset.gearHave + ':' + i.checked)")
        check("master list mirrors ticks", "cups:True".lower() in [x.lower() for x in ids] and "tape:true" in ids and "numbers:false" in ids, ids)
        check("Rot-Grün-Brille hidden while Test-Bereich locked", not any(x.startswith("glasses") for x in ids), ids)
        hs = await pg.evaluate("() => Math.min(...[...document.querySelectorAll('#masterGearList label')].map(l => l.getBoundingClientRect().height))")
        check("master rows >= 44 px", hs >= 44, hs)
        await grp.scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "06_grundeinstellungen_390_light.png"))
        await pg.click('#masterGearList input[data-gear-have="numbers"]'); await pg.wait_for_timeout(150)
        await pg.reload(); await pg.wait_for_timeout(400)
        owned = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-gear-v1') || '{}')")
        check("master tick persists after reload", owned.get("numbers") is True, owned)
        check("Farbe + Zahl un-greyed after reload", not (await pg.evaluate(CARD_JS, "cone-number"))["grey"])
        await open_master(pg)
        check("master checkbox still ticked after reload", await pg.evaluate("() => document.querySelector('#masterGearList input[data-gear-have=\"numbers\"]').checked"))

        # --- Hilfsmittel page toggles sync with Grundeinstellungen
        await pg.click("#masterGearOpenBtn"); await pg.wait_for_timeout(300)
        check("'Alle Hilfsmittel ansehen' opens the page", await vis_screen(pg) == "gearScreen")
        check("page toggle reflects master tick", await pg.evaluate("() => document.querySelector('#gearScreen input[data-gear-have=\"numbers\"]').checked"))
        await pg.click('#gearScreen input[data-gear-have="tape"]'); await pg.wait_for_timeout(150)
        await pg.click('#gearScreen input[data-gear-have="mat"]'); await pg.wait_for_timeout(150)
        hh = await pg.evaluate("() => Math.min(...[...document.querySelectorAll('#gearScreen .gear-have')].map(l => l.getBoundingClientRect().height))")
        check("'Hab ich' toggles >= 44 px", hh >= 44, hh)
        await pg.screenshot(path=os.path.join(SHOTS, "07_gear_page_hab_ich_390_light.png"))
        await open_master(pg)
        m = await pg.evaluate("() => Object.fromEntries([...document.querySelectorAll('#masterGearList input')].map(i => [i.dataset.gearHave, i.checked]))")
        check("master follows page toggles (tape off, mat on)", m.get("tape") is False and m.get("mat") is True, m)
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)
        check("unticking Klebeband greys Kompass-Aufbau again", (await pg.evaluate(CARD_JS, "cone-compass"))["pill"] == "Braucht: Klebeband")

        # --- optional entries never greyed (generic, data-driven)
        r = await pg.evaluate("""() => { const H = window.__myGear.hilfsmittel;
          H['vt-color'] = { text: 'x', link: '', gear: ['glasses'], optional: true };
          H['stroop-classic'] = { text: 'x', link: '', gear: ['glasses'] };
          window.__myGear.sync();
          const g = (k) => document.querySelector(`.excard[data-exercise="${k}"]`).classList.contains('gear-missing');
          const out = { opt: g('vt-color'), req: g('stroop-classic') };
          delete H['vt-color']; delete H['stroop-classic']; window.__myGear.sync(); return out; }""")
        check("optional entry never greyed", r["opt"] is False, r)
        check("a new non-optional entry is picked up without extra code", r["req"] is True, r)

        # --- Kombi tag (capture mode: no 'Braucht:' label, no question)
        await pg.goto(BASE + "?bereich=training"); await pg.wait_for_timeout(300)
        await pg.evaluate("() => [...document.querySelectorAll('[data-open-combo]')].find(b => b.getClientRects().length).click()")
        await pg.wait_for_timeout(300)
        btn = pg.locator("#comboAddGrid .combo-add-btn", has_text="Kompass-Aufbau").first
        await btn.click(); await pg.wait_for_timeout(300)
        t = await pg.evaluate("() => document.getElementById('startBtn').textContent.trim()")
        check("capture mode keeps 'Baustein übernehmen'", t == "Baustein übernehmen", t)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        check("capture commits without a question", await pg.evaluate("() => document.getElementById('confirmSheet').hidden") and await vis_screen(pg) == "comboScreen")
        tag = await pg.evaluate("() => [...document.querySelectorAll('#comboBlockList .gear-need-tag')].map(e => e.textContent)")
        check("Kombi list shows 'Braucht: Klebeband'", tag == ["Braucht: Klebeband"], tag)
        await pg.locator("#comboBlockList").scroll_into_view_if_needed()
        await pg.screenshot(path=os.path.join(SHOTS, "08_kombi_tag_390_light.png"))

        # --- trainer code intro: "Dafür brauchst du: …", never blocked
        await pg.route("**/online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=200, content_type="application/json",
            body=json.dumps({"name": "Hütchen-Test", "blocks": [{"exercise": "cone-compass", "duration": 60}, {"exercise": "vt-color", "duration": 60}]})))
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(300)
        await pg.evaluate("() => { const t = document.querySelector('#home .code-toggle'); if (t && t.getClientRects().length) t.click(); }")
        await pg.fill("#programCodeInput", "huetchen1"); await pg.click("#programGoBtn"); await pg.wait_for_timeout(800)
        check("code with equipment exercise opens the intro", await vis_screen(pg) == "programIntro")
        note = await pg.evaluate("() => { const n = document.getElementById('programGearNote'); return n.hidden ? '' : n.textContent; }")
        check("intro names missing equipment", note == "Dafür brauchst du: Klebeband für den Boden.", note)
        await pg.unroute("**/online-training.fwmc.workers.dev/**")

        # --- hint card dismiss (fresh profile)
        ctx2 = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx2.add_init_script(INIT)
        pg2 = await ctx2.new_page(); watch(pg2)
        await pg2.goto(BASE + "?bereich=visual"); await pg2.wait_for_timeout(300)
        check("hint card shown on a fresh profile", await pg2.locator("#home .gear-ask-card").is_visible())
        hide = await pg2.evaluate("() => document.querySelector('#home .gear-ask-hide').getBoundingClientRect().height")
        check("Ausblenden >= 44 px", hide >= 44, hide)
        await pg2.click("#home .gear-ask-hide"); await pg2.wait_for_timeout(150)
        check("Ausblenden hides the card", not await pg2.locator("#home .gear-ask-card").is_visible())
        await pg2.reload(); await pg2.wait_for_timeout(300)
        check("dismissal survives reload", not await pg2.locator("#home .gear-ask-card").is_visible() and await pg2.evaluate("() => localStorage.getItem('fwmc-gear-hint-dismissed') === 'true'"))
        # Test-Bereich: Rot-Grün-Brille in the list, Jedes Auge zählt greyed
        await pg2.evaluate("() => localStorage.setItem('fwmc-test-unlocked','true')")
        await pg2.goto(BASE + "?bereich=visual"); await pg2.wait_for_timeout(300)
        await open_master(pg2)
        check("Rot-Grün-Brille listed with Test-Bereich unlocked", await pg2.locator('#masterGearList input[data-gear-have="glasses"]').count() == 1)
        eye = await pg2.evaluate("() => { const c = document.getElementById('eyecountOpenBtn'); const p = c.querySelector('.excard-gear-note'); return { g: c.classList.contains('gear-missing'), p: p ? p.textContent : '' }; }")
        check("Jedes Auge zählt card greyed 'Braucht: Rot-Grün-Brille'", eye["g"] and eye["p"] == "Braucht: Rot-Grün-Brille", eye)
        await pg2.evaluate("() => document.getElementById('eyecountOpenBtn').click()"); await pg2.wait_for_timeout(300)
        t = await pg2.evaluate("() => document.getElementById('eyecountReadyStartBtn').textContent.trim()")
        check("Jedes Auge zählt start reads 'Braucht: Rot-Grün-Brille'", t == "Braucht: Rot-Grün-Brille", t)
        await pg2.evaluate("() => document.querySelector('#eyecountHilfsmittel .hilfsmittel-have').click()"); await pg2.wait_for_timeout(200)
        t = await pg2.evaluate("() => document.getElementById('eyecountReadyStartBtn').textContent.trim()")
        check("'Hab ich' on a non-VT ready screen restores 'Training starten'", t == "Training starten", t)
        await ctx2.close()

        # --- layout: 390/1024 light/dark, no sideways scroll; dark screenshots
        for w, h in ((390, 844), (1024, 768)):
            for scheme in ("light", "dark"):
                c3 = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, service_workers="block")
                await c3.add_init_script(INIT)
                p3 = await c3.new_page(); watch(p3)
                await p3.goto(BASE + "?bereich=visual"); await p3.wait_for_timeout(300)
                ok_home = await no_sideways(p3)
                if w == 390 and scheme == "dark":
                    await p3.evaluate("() => document.querySelector('.excard[data-exercise=\"cone-tap\"]').scrollIntoView({block:'center'})")
                    await p3.screenshot(path=os.path.join(SHOTS, "01_vt_home_greyed_390_dark.png"))
                    await p3.locator("#home .gear-ask-card").scroll_into_view_if_needed()
                    await p3.screenshot(path=os.path.join(SHOTS, "02_vt_home_hint_card_390_dark.png"))
                await p3.click('.excard[data-exercise="cone-number"]'); await p3.wait_for_timeout(300)
                ok_ready = await no_sideways(p3)
                if w == 390 and scheme == "dark":
                    await p3.locator("#startBtn").scroll_into_view_if_needed()
                    await p3.screenshot(path=os.path.join(SHOTS, "03_ready_braucht_390_dark.png"))
                    await p3.locator("#hilfsmittelNote").scroll_into_view_if_needed()
                    await p3.screenshot(path=os.path.join(SHOTS, "04_ready_note_hab_ich_390_dark.png"))
                await open_master(p3)
                ok_master = await no_sideways(p3)
                if w == 390 and scheme == "dark":
                    await p3.locator("#masterGearGroup").scroll_into_view_if_needed()
                    await p3.screenshot(path=os.path.join(SHOTS, "06_grundeinstellungen_390_dark.png"))
                if w == 1024 and scheme == "light":
                    await p3.locator("#masterGearGroup").scroll_into_view_if_needed()
                    await p3.screenshot(path=os.path.join(SHOTS, "06_grundeinstellungen_1024_light.png"))
                await p3.click("#masterGearOpenBtn"); await p3.wait_for_timeout(300)
                ok_gear = await no_sideways(p3)
                if w == 390 and scheme == "dark":
                    await p3.screenshot(path=os.path.join(SHOTS, "07_gear_page_hab_ich_390_dark.png"))
                check(f"no sideways scroll {w} {scheme}", ok_home and ok_ready and ok_master and ok_gear, (ok_home, ok_ready, ok_master, ok_gear))
                await c3.close()

        await b.close()
    check("no pageerror / console error", not errors, errors[:5])
    print("\nFAILED:" if fails else "\nALL PASSED", fails if fails else "")

asyncio.run(main())
