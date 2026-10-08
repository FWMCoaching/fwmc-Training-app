import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Standing coverage guard (client rule, 2026-10-02, after Kraftübungen
# could not be stacked): every exercise/exercise type outside the
# Test-Bereich must work everywhere - single, as a Kombi-Baustein (added
# AND editable afterwards), and, for Workout exercises, stackable in both
# plan builders (Zirkel and Kraftplan); the pause between exercises/
# Bausteine must be a 0-180 s slider everywhere (Zirkel, Kraftplan, Kombi,
# Cardio). This test walks EVERY entry in
# the Kombi add grid generically, so a new entry that can't be committed
# fails here without anyone writing a new test - and it checks that the
# number of Visual Training / NAT / Atemtraining exercises on their home
# screens matches what the Kombi offers, so a new exercise that was
# forgotten in the Kombi fails here too.

async def visible_screen(pg):
    return await pg.evaluate("""() => {
        const s = [...document.querySelectorAll('.screen')].find((el) => !el.hidden && el.offsetParent !== null);
        return s ? s.id : null;
    }""")

async def make_committable(pg, sid):
    # Minimal setup a capture screen needs before its start button enables.
    scr = pg.locator(f"#{sid}")
    for cb in await scr.locator(".warn-box input[type=checkbox]").all():
        if not await cb.is_checked(): await cb.check()
    if await scr.locator(".ca-plus-btn").count():
        await scr.locator(".ca-plus-btn").first.click()
    if sid == "cardioReady":
        await scr.locator("#cardioAddGrid .combo-add-btn").first.click()
    await pg.wait_for_timeout(80)

async def main():
    errors = []
    fails = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true')")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(300)

        # ---- 1. Inventory vs Kombi offer ----
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(200)
        groups = await pg.evaluate("""() => [...document.querySelectorAll('#comboAddGrid > *')].map((g) => ({
            label: (g.querySelector('.group-label, .combo-add-group-label, h3, .combo-domain-title') || {}).textContent || '',
            n: g.querySelectorAll('.combo-add-btn').length }))""")
        print("Kombi add grid groups:", groups)
        total_entries = await pg.locator("#comboAddGrid .combo-add-btn").count()
        kombi_labels = [t.split("\n")[0].strip() for t in await pg.locator("#comboAddGrid .combo-add-btn").all_inner_texts()]
        # Visual Training: every home-grid card by its exercise title.
        visual_titles = await pg.evaluate("() => [...document.querySelectorAll('#home .excard')].map((c) => c.dataset.exercise)")
        missing = []
        for ex_id in visual_titles:
            title = await pg.evaluate("(id) => document.querySelector(`.excard[data-exercise='${id}']`).querySelector('h3, .ex-title, strong, .title')?.textContent.trim() || id", ex_id)
            if not any(l.startswith(title[:12]) for l in kombi_labels): missing.append(title)
        # NAT: every sub-tab by the first word of its name.
        nat_tabs = await pg.evaluate("() => [...new Set([...document.querySelectorAll('#natHome [data-nat-sub]')].map((e) => e.textContent.replace(/\u00ad/g, '').trim()))]")
        for t in nat_tabs:
            word = t.split(" ")[0].split("-")[0]
            if not any(l.startswith(word) for l in kombi_labels): missing.append(t)
        print("every Visual Training and NAT exercise is offered in the Kombi:", not missing)
        if missing: fails.append("missing in Kombi: " + ", ".join(missing))

        # ---- 1b. Every area and every exercise of every area (Fabian 07.10.:
        # "haben wir dafür einen Automatismus?"). Generic, so a new area or a
        # new exercise anywhere fails here until it is in the Kombi:
        # - every Training-hub area (except Test) has its own Kombi group;
        # - Atemtraining: every pattern card (incl. Wim-Hof) is offered;
        # - Krafttraining: every exercise type card (Intervall/Zirkel, Kraft) has an entry;
        # - Reaktion/Ausdauer: every start card has an entry.
        # Ready-made programmes (featured grids, trainer codes) are whole runs
        # of several steps, not single Bausteine - listed, not required.
        domains = await pg.evaluate("() => [...document.querySelectorAll('#comboAddGrid .combo-domain-group')].map((g) => g.dataset.domain)")
        # the area list comes from the Training hub itself (built from PLAN_AREAS),
        # so a new area shows up here without touching this test
        await pg.evaluate("() => localStorage.setItem('fwmc-test-bottomnav', 'true')")
        await pg.goto(URL.replace("bereich=visual", "bereich=training")); await pg.wait_for_timeout(400)
        hub_areas = await pg.evaluate("() => [...document.querySelectorAll('#hubAreaGrid .area-tile')].map((t) => t.dataset.area)")
        await pg.evaluate("() => localStorage.removeItem('fwmc-test-bottomnav')")
        print("areas on the Training page:", hub_areas)
        if len(hub_areas) < 7: fails.append(f"Training hub lists only {hub_areas}")
        no_group = [a for a in hub_areas if a != "test" and a not in domains]
        print("every area has its own group in the Kombi:", not no_group, domains)
        if no_group: fails.append("area without Kombi group: " + ", ".join(no_group))
        def group_labels(dom):
            return pg.evaluate("(d) => [...document.querySelectorAll(`#comboAddGrid .combo-domain-group[data-domain='${d}'] .ca-title`)].map((e) => e.textContent.trim())", dom)
        await pg.goto(URL.replace("bereich=visual", "bereich=breath")); await pg.wait_for_timeout(400)
        breath_cards = await pg.evaluate("() => [...document.querySelectorAll('#patternGrid > button')].map((b) => (b.querySelector('.fc-title, h3, strong') || b).textContent.trim())")
        await pg.click('#breathHome [data-open-combo="1"]') if await pg.locator('#breathHome [data-open-combo="1"]').count() else await pg.evaluate("() => document.querySelector('[data-open-combo]').click()")
        await pg.wait_for_timeout(200)
        bl = await group_labels("breath")
        miss_b = [c for c in breath_cards if not any(l.startswith(c[:14]) for l in bl)]
        print(f"every Atemtraining exercise ({len(breath_cards)}) is offered in the Kombi:", bool(breath_cards) and not miss_b, miss_b)
        if not breath_cards or miss_b: fails.append("Atem missing in Kombi: " + ", ".join(miss_b or ["no cards found"]))
        for dom, sel in [("workout", "#workoutHome > section:not(.featured-programs) .featured-card[id$='StartCard']"),
                         ("movement", "#movementHome .featured-card[id$='StartCard']"),
                         ("cardio", "#cardioHome .featured-card[id$='StartCard']"),
                         # Aktivierung (2026-10-08): every own exercise tile
                         ("activation", "#activationHome [data-act-ex]")]:
            n_cards = await pg.evaluate("(s) => document.querySelectorAll(s).length", sel)
            n_kombi = len(await group_labels(dom))
            print(f"{dom}: every exercise type ({n_cards}) has a Kombi entry ({n_kombi}):", n_cards > 0 and n_kombi >= n_cards)
            if not (n_cards > 0 and n_kombi >= n_cards): fails.append(f"{dom}: {n_cards} exercise types, {n_kombi} Kombi entries")
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click('#home [data-open-combo="1"]'); await pg.wait_for_timeout(200)

        # ---- 2. Every Kombi entry: open, commit, editable ----
        idx = 0
        committed = 0
        fails_before = len(fails)
        while idx < total_entries:
            btn = pg.locator("#comboAddGrid .combo-add-btn").nth(idx)
            label = (await btn.inner_text()).split("\n")[0].strip()
            before = await pg.locator("#comboBlockList .chapter-row").count()
            await btn.click(); await pg.wait_for_timeout(200)
            sid = await visible_screen(pg)
            if sid == "comboScreen":
                after = await pg.locator("#comboBlockList .chapter-row").count()
                if after != before + 1: fails.append(f"{label}: one-click entry added nothing")
                else: committed += 1
                idx += 1; continue
            await make_committable(pg, sid)
            start = pg.locator(f"#{sid} .start-btn:visible").last
            if await start.is_disabled():
                fails.append(f"{label}: start button on {sid} stays disabled"); 
                await pg.locator(f"#{sid} .back-link:visible").first.click(); await pg.wait_for_timeout(150)
                idx += 1; continue
            await start.click(); await pg.wait_for_timeout(250)
            sid2 = await visible_screen(pg)
            after = await pg.locator("#comboBlockList .chapter-row").count()
            if sid2 != "comboScreen" or after != before + 1:
                fails.append(f"{label}: commit from {sid} did not add a Baustein (now on {sid2})")
                if sid2 != "comboScreen":
                    await pg.click('#home [data-open-combo="1"]') if await pg.is_visible('#home') else None
            else:
                committed += 1
            idx += 1
        print(f"every Kombi entry ({total_entries}) can be added as a Baustein:", committed == total_entries and len(fails) == fails_before)

        # Kombi pause between Bausteine: a 0-180 s slider between every two blocks.
        bad = await pg.evaluate("() => [...document.querySelectorAll('#comboBlockList .combo-pause-slider')].filter((r) => !(r.min === '0' && r.max === '180' && r.step === '5')).length")
        n_pause = await pg.locator("#comboBlockList .combo-pause-slider").count()
        print("Kombi: pause slider (0–180 s) between every two Bausteine:", bad == 0 and n_pause == total_entries - 1)
        if bad or n_pause != total_entries - 1: fails.append(f"Kombi pause sliders: {n_pause}, wrong range: {bad}")

        not_editable = await pg.evaluate("() => [...document.querySelectorAll('#comboBlockList .chapter-row')].filter((r) => r.querySelector('.chapter-main').tagName !== 'BUTTON').map((r) => r.textContent.trim())")
        print("every added Baustein is editable afterwards:", len(not_editable) == 0)
        if not_editable: fails.append("not editable: " + "; ".join(not_editable))

        # ---- 3. Workout: every exercise stackable in Zirkel AND Kraftplan ----
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="workout"]'); await pg.wait_for_timeout(150)
        for card, grid, lst in [("#workoutTabataStartCard, [data-open-tabata], #workoutCircuitStartCard", "#workoutCircuitAddGrid", "#workoutCircuitList .circuit-item-row"),
                                ("#workoutRepsStartCard", "#workoutRepsExerciseGrid", "#workoutRepsList .strength-item-row")]:
            await pg.click('#home .section-tab[data-section="workout"]') if await pg.is_visible('#home') else None
            await pg.evaluate("(sel) => { const el = document.querySelector(sel); el && el.click(); }", card)
            await pg.wait_for_timeout(200)
            n_ex = await pg.locator(f"{grid} .custom-exercise-add-row").count()
            n_plus = await pg.locator(f"{grid} .ca-plus-btn").count()
            for i in range(n_plus):
                await pg.locator(f"{grid} .ca-plus-btn").nth(i).click(); await pg.wait_for_timeout(30)
            n_items = await pg.locator(lst).count()
            rest_sel = "#workoutCircuitRestSlider" if "Circuit" in grid else "#workoutRepsExerciseRestSlider"
            rng = await pg.evaluate("(sel) => { const r = document.querySelector(sel); return r ? [r.min, r.max, r.step] : null; }", rest_sel)
            print(f"{grid}: 'Pause zwischen Übungen' is a 0–180 s slider:", rng == ["0", "180", "5"])
            if rng != ["0", "180", "5"]: fails.append(f"{rest_sel}: {rng}")
            print(f"{grid}: all {n_ex} exercises stackable into one plan:", n_ex > 0 and n_plus == n_ex and n_items == n_ex)
            if not (n_ex > 0 and n_plus == n_ex and n_items == n_ex): fails.append(f"{grid}: {n_plus}/{n_ex} addable, {n_items} in plan")
            await pg.locator(".screen:not([hidden]) .back-link").first.click(); await pg.wait_for_timeout(150)

        # Cardio: pause slider between activities, 0-180 s.
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click('#home .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(150)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(150)
        await pg.locator("#cardioAddGrid .combo-add-btn").nth(0).click(); await pg.wait_for_timeout(60)
        await pg.locator("#cardioAddGrid .combo-add-btn").nth(1).click(); await pg.wait_for_timeout(60)
        rng = await pg.evaluate("() => { const r = document.querySelector('#cardioList .combo-pause-slider'); return r ? [r.min, r.max, r.step] : null; }")
        print("Cardio: pause between activities is a 0–180 s slider:", rng == ["0", "180", "5"])
        if rng != ["0", "180", "5"]: fails.append(f"cardio pause: {rng}")

        print("coverage failures:", fails)
        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
