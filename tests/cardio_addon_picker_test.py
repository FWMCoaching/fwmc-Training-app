import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Cardio "+ Zusatzaufgabe" live picker (Tier 2) - supersedes the first
# manual-trigger version (cardio_addon_manual_test.py, now removed), which
# fired a random pick from the pre-configured Feineinstellungen pool at its
# pre-configured duration. Client's clarified ask: actively CHOOSE which
# guest exercise, right now, mid-Cardio-activity ("ich mache jetzt zwei
# Minuten Blitzreiz-Reaktionstraining"), with the option to bail out, all
# while still seeing Cardio's own status ticking behind the picker
# (cardioTick keeps running - the picker never cancels cardioRaf), and a
# small floating badge during the guest exercise itself reading the still-
# running Cardio block's remaining time, warning once it's about to change.
# cardio_test.py already covers the AUTOMATIC randomized-interval trigger,
# unaffected by any of this.
#
# Follow-up client ask (2026-09-30, Periphere Wahrnehmung/Blitz-Raster as
# the example): picking exercise+duration live used to be the whole picker -
# every other "Unterpunkt" (colours, difficulty, background, ...) was only
# reachable in the pre-start Feineinstellungen panel. #cardioAddonPickerDetail
# now renders the exact same buildCardioGuestFieldsHtml() markup the
# pre-start panel uses (see cardio_addon_picker_full_settings_test.py for
# the dedicated parity/isolation coverage) - the old dedicated duration-
# stepper markup is gone, replaced by that panel's own Dauer field
# (data-f="duration", 5-120s, same range the pre-start panel already used).

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        async def wait_for_visible(sel, max_ms=30000, poll_ms=100):
            waited = 0
            while waited < max_ms:
                if await pg.is_visible(sel):
                    return True
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return False

        async def wait_for_countdown_at_most(max_remaining, max_ms=90000, poll_ms=200):
            waited = 0
            while waited < max_ms:
                txt = await pg.inner_text("#cardioCountdown")
                try:
                    m, s = txt.split(":")
                    remaining = int(m) * 60 + int(s)
                except ValueError:
                    remaining = None
                if remaining is not None and remaining <= max_remaining:
                    return remaining
                await pg.wait_for_timeout(poll_ms)
                waited += poll_ms
            return None

        async def set_duration(seconds):
            field = pg.locator('#cardioAddonPickerDetail input[data-f="duration"]')
            await field.fill(str(seconds))
            await field.dispatch_event("input")
            await pg.wait_for_timeout(80)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)

        # ---- shorten Joggen to the UI floor (60s) so the whole test
        # finishes in reasonable real time ----
        row = pg.locator("#cardioList .circuit-item-row").first
        for _ in range(9):
            await row.locator('.circuit-step[data-dir="-1"]').first.click(); await pg.wait_for_timeout(30)
        print("activity duration at floor (1 Min.):", "1 Min." in await row.inner_text())

        # ---- touch the advanced panel once just to force cardioAddonPrefs'
        # in-memory defaults (already fully populated per-type at load time)
        # to actually persist to localStorage - otherwise the "never
        # persisted" isolation check further down has nothing to read yet.
        # Toggled back off immediately after: the manual picker itself needs
        # no advance configuration, still true below. ----
        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.uncheck("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)

        # ---- a second activity so Joggen finishing mid-test lands on the
        # interleaved pause (still #cardioPlayer), not finishCardio() ----
        await pg.click('#cardioAddGrid >> text="Rad fahren"'); await pg.wait_for_timeout(100)

        # ---- deliberately NOT touching cardioAddonEnableToggle/pool at
        # all: the manual live picker needs no advance configuration, only
        # the automatic randomized-interval system (unchanged, still
        # opt-in) does ----
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        print("cardioPlayer visible:", await pg.is_visible("#cardioPlayer"))
        print("trigger button visible with no addon config at all:", await pg.is_visible("#cardioAddonTriggerBtn"))

        # ---- open the picker: Cardio's own status keeps visibly running
        # behind it (semi-transparent overlay, cardioRaf untouched) ----
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        print("picker sheet visible:", await pg.is_visible("#cardioAddonPicker"))
        print("cardioPlayer (with its countdown) still there underneath:", await pg.is_visible("#cardioPlayer"))
        countdown_a = await pg.inner_text("#cardioCountdown")
        await pg.wait_for_timeout(1300)
        countdown_b = await pg.inner_text("#cardioCountdown")
        print("Cardio countdown keeps ticking while the picker is open:", countdown_a != countdown_b)

        # ---- default selection + duration ----
        choices = pg.locator("#cardioAddonPickerTypeRow .choice")
        print("all 17 exercise choices offered (not just the addon pool):", await choices.count() == 17)
        print("first type pre-selected by default:", "active" in (await choices.nth(0).get_attribute("class")))
        print("default duration shown as 20 (matches the saved default):",
              (await pg.locator('#cardioAddonPickerDetail input[data-f="duration"]').input_value()) == "20")

        # ---- switch the exercise choice - detail panel rebuilds for the
        # newly-selected type, fresh from its own saved settings ----
        await choices.nth(1).click(); await pg.wait_for_timeout(100)
        print("second type now selected instead:", "active" in (await choices.nth(1).get_attribute("class")))
        print("first type no longer selected:", "active" not in (await choices.nth(0).get_attribute("class")))

        # ---- live duration edit, ephemeral: never written back to the
        # saved per-type default ----
        saved_before = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['vt-color'].duration")
        await set_duration(15)
        print("duration field reflects the live edit:", (await pg.locator('#cardioAddonPickerDetail input[data-f="duration"]').input_value()) == "15")

        # ---- Abbrechen big enough to comfortably tap, but still visibly
        # smaller than "Jetzt starten" (client-reported: was default-tiny) ----
        cancel_h = await pg.eval_on_selector("#cardioAddonPickerCancelBtn", "el => el.getBoundingClientRect().height")
        start_h = await pg.eval_on_selector("#cardioAddonPickerStartBtn", "el => el.getBoundingClientRect().height")
        print("Abbrechen bigger than the old browser-default size but smaller than Jetzt starten:", 35 < cancel_h < start_h)

        # ---- cancel: bails out cleanly, nothing started, and the live edit
        # never touched the saved default either ----
        await pg.click("#cardioAddonPickerCancelBtn"); await pg.wait_for_timeout(200)
        print("cancel closes the picker without starting anything:",
              await pg.is_hidden("#cardioAddonPicker") and await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#player"))
        saved_after_cancel = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['vt-color'].duration")
        print("saved default duration untouched by the cancelled live edit:", saved_after_cancel == saved_before)

        # ---- for real this time: pick, live-set a fast duration, start,
        # full takeover ----
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await pg.locator("#cardioAddonPickerTypeRow .choice").nth(1).click(); await pg.wait_for_timeout(80)
        await set_duration(15)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(300)
        print("chosen guest exercise takes over full-screen:",
              await pg.is_visible("#player") and not await pg.is_visible("#cardioPlayer") and not await pg.is_visible("#cardioAddonPicker"))
        saved_after_start = await pg.evaluate("() => JSON.parse(localStorage.getItem('fwmc-cardio-addon-v1')).perType['vt-color'].duration")
        print("saved default duration still untouched after actually starting the live-edited burst:", saved_after_start == saved_before)

        # ---- floating Cardio-status badge, not yet in warn range ----
        print("badge visible during the guest exercise:", await pg.is_visible("#cardioGuestBadge"))
        badge_a = await pg.inner_text("#cardioGuestBadge")
        print("badge reads remaining Cardio time:", badge_a.startswith("Cardio: noch"))
        print("not warning yet (block just started, ~1 Min. left):", "warn" not in (await pg.get_attribute("#cardioGuestBadge", "class")))
        await pg.wait_for_timeout(1300)
        badge_b = await pg.inner_text("#cardioGuestBadge")
        print("badge counts down live:", badge_a != badge_b)

        # ---- let the live-edited 15s guest window finish on its own ->
        # back to cardio, badge gone, trigger available again, same activity
        # (not restarted). Polls rather than a fixed wait: under heavy
        # parallel test load the guest exercise's own internal timer can
        # legitimately take longer wall-clock time to reach its 15s than an
        # unloaded run (see the subitize_test.py flake fixed earlier for the
        # same class of issue) - a fixed wait here raced that and flaked in
        # the full suite even though it always passed standalone. ----
        print("returned to cardioPlayer after guest window finished:", await wait_for_visible("#cardioPlayer"))
        print("badge hidden again after returning:", await pg.is_hidden("#cardioGuestBadge"))
        print("trigger button visible again:", await pg.is_visible("#cardioAddonTriggerBtn"))
        print("still on the same activity (Joggen), not restarted:", "Joggen" in await pg.inner_text("#cardioActivityTitle"))

        # ---- wait until the Cardio block is close to changing (polling
        # the real countdown instead of guessing a fixed delay, for the
        # same reason as above), then trigger again: the badge should come
        # up already warning ----
        remaining = await wait_for_countdown_at_most(15)
        print("Cardio block down to 15s or less remaining:", remaining is not None)
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(200)
        await set_duration(15)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(300)
        badge_class = await pg.get_attribute("#cardioGuestBadge", "class")
        badge_text = await pg.inner_text("#cardioGuestBadge")
        print("badge already warns once the Cardio block is close to ending:", "warn" in badge_class)
        print(f"(for reference, badge read: {badge_text!r})")

        # ---- let it finish, then end the session cleanly ----
        print("back at cardioPlayer once more:", await wait_for_visible("#cardioPlayer"))
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        print("abort back at cardioReady:", await pg.is_visible("#cardioReady"))
        print("badge stays hidden after aborting:", await pg.is_hidden("#cardioGuestBadge"))

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
