"""Atempausen + Sehen und Reize (Fabian 07.10.2026, Nacht-Paket M + N).

M-A  Nichtraucher-Pause on Heute: card, 1/2/3 Min. (saved), info sheet,
     start -> calm breathing run (Ruhige Atmung) -> history kind "breath"
     titled "Nichtraucher-Pause", back to Heute; ?bereich=atempause.
M-B  Wim-Hof "Pause zwischen den Runden": slider 0-180 s, saved, carried by
     presets and Kombi blocks, "Normal atmen · 0:20" between the rounds.
M-C  Atempausen-Erinnerung: 1-3 times a day in #reminderGroup, POST body to
     the (routed) Worker holds {at,title,body} "Zeit für eine Atempause",
     works without the training reminders, DELETE when both are off.
N    Schriftgröße (multiplies --ts) and Sanfte Reize (note + link on the
     ready screens, per-exercise override in Feineinstellungen, live switch
     in the pause sheet, longer minimum times), light/dark, no page errors.
Run from tests/ with a dev server on :8845."""
import asyncio, json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
BERLIN = ZoneInfo("Europe/Berlin")
KEY = "BCVODgVri4ZeawfHr3aK0XBrzRKXW99TZWGDqPgydlQqIVam8-qlZ2UsrJVjQRArI2-ANSeVYTiURAqn9Msd9Nk"
SHOTS = "screenshots/nacht3_1007"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "if(!localStorage.getItem('fwmc-master-v1'))localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")

# Fake push stack (same as reminders_1005_test.py).
FAKE_PUSH = r"""
(() => {
  const ss = window.sessionStorage;
  const makeSub = () => ({
    endpoint: 'https://fcm.googleapis.com/fcm/send/test-device-1',
    toJSON() { return { endpoint: this.endpoint, expirationTime: null, keys: { p256dh: 'BPfake', auth: 'authfake' } }; },
    async unsubscribe() { ss.removeItem('fake-sub'); return true; },
  });
  const pm = {
    async getSubscription() { return ss.getItem('fake-sub') ? makeSub() : null; },
    async subscribe() { ss.setItem('fake-sub', '1'); return makeSub(); },
  };
  const reg = { pushManager: pm, scope: location.origin + '/' };
  Object.defineProperty(navigator, 'serviceWorker', { configurable: true, value: {
    ready: Promise.resolve(reg), register: async () => reg, addEventListener() {}, removeEventListener() {}, controller: null } });
  if (!('PushManager' in window)) window.PushManager = function () {};
  class FakeNotification {
    static get permission() { return ss.getItem('fake-perm') || 'default'; }
    static async requestPermission() { ss.setItem('fake-perm', 'granted'); return 'granted'; }
  }
  window.Notification = FakeNotification;
})();
"""

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


async def new_ctx(b, scheme="light", extra_init=None, push=False):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block",
                              color_scheme=scheme, timezone_id="Europe/Berlin")
    if push:
        await ctx.add_init_script(FAKE_PUSH)
        await ctx.add_init_script(f"localStorage.setItem('fwmc-test-reminder-key', JSON.stringify('{KEY}'));")
    await ctx.add_init_script(INIT)
    if extra_init:
        await ctx.add_init_script(extra_init)
    pg = await ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    return ctx, pg, errors


async def open_master(pg):
    await pg.locator(".master-settings-btn:visible").first.click()
    await pg.wait_for_timeout(250)


async def main():
    import os
    os.makedirs(SHOTS, exist_ok=True)
    all_errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ================= M-A: Nichtraucher-Pause on Heute =================
        ctx, pg, errors = await new_ctx(b)
        await pg.clock.install()
        await pg.goto(BASE + "?bereich=heute"); await pg.clock.run_for(600)
        check("A: card visible on Heute", await pg.is_visible("#todayBreak"))
        title = await pg.inner_text("#todayBreakTitle")
        sub = await pg.inner_text("#todayBreak .today-tile-sub")
        # Heute E (09.10.): half tile, title in quotes, minutes in the ⓘ sheet
        check("A: recognisable as a breathing pause", title == "„Nichtraucher-Pause“" and "durchatmen" in sub, f"{title} / {sub}")
        check("A: default 2 Min. active", await pg.locator('[data-break-min="2"].active').count() == 1 and (await pg.inner_text("#todayBreakStartBtn")).startswith("2 Min."))
        sizes = await pg.evaluate("() => [...document.querySelectorAll('#todayBreak button')].map(e => Math.min(e.getBoundingClientRect().width, e.getBoundingClientRect().height))")
        check("A: tap targets >= 44 px", min(sizes) >= 44, sizes)
        order = await pg.evaluate("() => { const ids = [...document.querySelectorAll('#todayHome > section, #todayPair > section')].map(s => s.id || s.className); return ids.indexOf('todayMain') < ids.indexOf('todayBreak'); }")
        check("A: below the main card", order)
        await pg.click("#todayBreakInfoBtn"); await pg.clock.run_for(200)
        await pg.click('#breakInfoSheet [data-break-min="1"]'); await pg.clock.run_for(100)
        await pg.click("#breakInfoCloseBtn"); await pg.clock.run_for(200)
        check("A: 1 Min. saved", json.loads(await pg.evaluate("() => localStorage.getItem('fwmc-atempause-v1')")).get("min") == 1)
        await pg.reload(); await pg.clock.run_for(600)
        check("A: persists across reload", await pg.locator('[data-break-min="1"].active').count() == 1 and (await pg.inner_text("#todayBreakMinText")) == "1 Min.")
        # info sheet
        await pg.click("#todayBreakInfoBtn"); await pg.clock.run_for(200)
        txt = await pg.inner_text("#breakInfoSheet")
        check("A: info sheet opens", await pg.is_visible("#breakInfoSheet"))
        check("A: warm text, no blunt wording", "Auszeit" in txt and "Gift" not in txt and "ohne Zigarette" in txt)
        await pg.screenshot(path=f"{SHOTS}/heute_info_light.png")
        await pg.click("#breakInfoCloseBtn"); await pg.clock.run_for(200)
        check("A: info sheet closes", not await pg.is_visible("#breakInfoSheet"))
        await pg.locator("#todayBreak").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/heute_card_light.png")
        # start the 1-minute pause
        await pg.click("#todayBreakStartBtn"); await pg.clock.run_for(500)
        check("A: breathing player runs", await pg.is_visible("#breathPlayer"))
        await pg.screenshot(path=f"{SHOTS}/atempause_player_light.png")
        for _ in range(8):
            await pg.clock.run_for(10000)
        check("A: ends after about a minute", await pg.is_visible("#breathDonePanel"), await pg.inner_text("#breathPhaseLabel"))
        summ = await pg.inner_text("#breathDoneSummary")
        check("A: done summary names the pause", summ.startswith("Nichtraucher-Pause"), summ)
        hist = json.loads(await pg.evaluate("() => localStorage.getItem('fwmc-history-v1') || '[]'"))
        last = hist[-1] if hist else {}
        check("A: history kind breath, title Nichtraucher-Pause", last.get("kind") == "breath" and last.get("title") == "Nichtraucher-Pause" and 50 <= last.get("seconds", 0) <= 70, last)
        check("A: no Weitermachen record", not await pg.evaluate("() => localStorage.getItem('fwmc-resume-single-v1')"))
        await pg.click("#breathDoneBackBtn"); await pg.clock.run_for(400)
        check("A: back to Heute", await pg.is_visible("#todayHome"))
        # Beenden mid-run also leads back to Heute
        await pg.click("#todayBreakStartBtn"); await pg.clock.run_for(2000)
        await pg.click("#breathBackBtn"); await pg.clock.run_for(400)
        check("A: Beenden -> Heute", await pg.is_visible("#todayHome") and not await pg.is_visible("#breathPlayer"))
        # deep link from the push
        await pg.goto(BASE + "?bereich=atempause"); await pg.clock.run_for(800)
        check("A: ?bereich=atempause opens Heute at the card", await pg.is_visible("#todayHome") and await pg.evaluate("() => document.getElementById('todayBreak').classList.contains('is-called')"))
        all_errors += errors
        await ctx.close()

        # ================= M-B: Wim-Hof Pause zwischen den Runden =================
        ctx, pg, errors = await new_ctx(b)
        await pg.clock.install()
        await pg.goto(BASE + "?bereich=breath"); await pg.clock.run_for(600)
        await pg.evaluate("() => [...document.querySelectorAll('#patternGrid > button')].pop().click()"); await pg.clock.run_for(300)
        check("B: Wim-Hof has 'Pause zwischen den Runden'", await pg.is_visible("#wimhofRoundRestSlider"))
        check("B: default Keine (0 = straight on)", (await pg.inner_text("#wimhofRoundRestValue")) == "Keine")
        rng = await pg.evaluate("() => { const s = document.getElementById('wimhofRoundRestSlider'); return [s.min, s.max, s.step]; }")
        check("B: slider 0-180 s in 5 s steps", rng == ["0", "180", "5"], rng)
        await pg.evaluate("() => { const s = document.getElementById('wimhofRoundRestSlider'); s.value = 20; s.dispatchEvent(new Event('input', {bubbles:true})); }")
        check("B: value shows 20 s", (await pg.inner_text("#wimhofRoundRestValue")) == "20 s")
        check("B: saved in fwmc-wimhof-v1", json.loads(await pg.evaluate("() => localStorage.getItem('fwmc-wimhof-v1')")).get("roundRestS") == 20)
        await pg.click('[data-wh-breaths="20"]'); await pg.click('[data-wh-rounds="2"]'); await pg.click('[data-wh-recovery="10"]')
        # preset
        await pg.click("#wimhofSaveBtn"); await pg.fill("#wimhofSaveNameInput", "Morgens"); await pg.click("#wimhofSaveConfirmBtn"); await pg.clock.run_for(100)
        meta = await pg.inner_text("#wimhofSavedList")
        check("B: preset carries the pause", "Morgens" in meta and "20 s Pause" in meta, meta)
        await pg.evaluate("() => { const s = document.getElementById('wimhofRoundRestSlider'); s.value = 0; s.dispatchEvent(new Event('input', {bubbles:true})); }")
        await pg.click("#wimhofSavedList .bundle-item"); await pg.clock.run_for(100)
        check("B: loading the preset restores 20 s", (await pg.inner_text("#wimhofRoundRestValue")) == "20 s")
        await pg.locator("#wimhofRoundRestGroup").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/wimhof_ready_light.png")
        # run: 20 breaths, hold, recovery 10 s, then the rest phase
        await pg.check("#wimhofAckCheck"); await pg.click("#wimhofStartBtn"); await pg.clock.run_for(500)
        await pg.clock.run_for(36000)
        await pg.click("#wimhofHoldDoneBtn"); await pg.clock.run_for(11000)
        lab, cnt = await pg.inner_text("#wimhofPhaseLabel"), await pg.inner_text("#wimhofPhaseCount")
        check("B: calm 'Normal atmen · 0:xx' between rounds", lab == "Normal atmen" and cnt.startswith("0:"), f"{lab} {cnt}")
        await pg.screenshot(path=f"{SHOTS}/wimhof_rest_light.png")
        await pg.clock.run_for(21000)
        check("B: round 2 starts after the pause", "Runde 2" in await pg.inner_text("#wimhofStatusEl") and await pg.inner_text("#wimhofPhaseLabel") != "Normal atmen")
        await pg.evaluate("() => document.getElementById('wimhofBackBtn').click()"); await pg.clock.run_for(300)
        if await pg.is_visible("#confirmSheet"):
            await pg.click("#confirmYesBtn"); await pg.clock.run_for(300)
        # Kombi block keeps it
        await pg.goto(BASE + "?bereich=breath"); await pg.clock.run_for(600)
        await pg.evaluate("() => document.querySelector('[data-open-combo]').click()"); await pg.clock.run_for(300)
        opened = await pg.evaluate("""() => { const b = [...document.querySelectorAll('#comboScreen button')].find(x => /Wim-Hof/.test(x.textContent)); if (b) { b.click(); return true; } return false; }""")
        await pg.clock.run_for(300)
        if opened and await pg.is_visible("#wimhofReady"):
            await pg.check("#wimhofAckCheck"); await pg.click("#wimhofStartBtn"); await pg.clock.run_for(300)
        meta = await pg.evaluate("() => document.getElementById('comboScreen').innerText")
        check("B: Kombi-Baustein shows the pause", opened and "20 s Pause" in meta, meta[-200:] if meta else "")
        all_errors += errors
        await ctx.close()

        # ================= M-C: Atempausen-Erinnerung =================
        posts = []
        ctx, pg, errors = await new_ctx(b, push=True)
        async def handle(route):
            req = route.request
            posts.append({"method": req.method, "body": json.loads(req.post_data or "null")})
            await route.fulfill(status=200, content_type="application/json", body='{"ok":true}', headers={"Access-Control-Allow-Origin": "*"})
        await pg.route("https://online-training.fwmc.workers.dev/**", handle)
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(500)
        await open_master(pg)
        # Prüfer 07.10. Nr. 6: every tick row of the Grundeinstellungen is a 44 px tap row
        small = await pg.evaluate("""() => [...document.querySelectorAll('#masterSettingsSheet label.checkbox-row')].filter(l => l.getClientRects().length && !l.closest('[hidden]'))
            .map(l => [l.textContent.trim().slice(0, 30), Math.round(l.getBoundingClientRect().height)]).filter(([t, h]) => h < 44)""")
        n_rows = await pg.evaluate("() => [...document.querySelectorAll('#masterSettingsSheet label.checkbox-row')].filter(l => l.getClientRects().length && !l.closest('[hidden]')).length")
        check("Prüfer 6: every Grundeinstellungen tick row >= 44 px high", n_rows >= 5 and not small, (n_rows, small))
        await pg.locator("#reminderBreakGroup").scroll_into_view_if_needed()
        check("C: Atempausen switch in Erinnerungen", await pg.is_visible("#reminderGroup #reminderBreakCheck"))
        check("C: times hidden while off", not await pg.is_visible("#reminderBreakBody"))
        await pg.check("#reminderBreakCheck"); await pg.wait_for_timeout(600)
        check("C: count + times shown when on", await pg.is_visible("#reminderBreakCountRow"))
        await pg.click('[data-break-count="3"]'); await pg.wait_for_timeout(100)
        await pg.fill('[data-break-time="0"]', "09:15"); await pg.dispatch_event('[data-break-time="0"]', "change")
        await pg.wait_for_timeout(2200)
        await pg.screenshot(path=f"{SHOTS}/master_reminder_light.png")
        post = [x for x in posts if x["method"] == "POST"]
        check("C: synced with the Worker", bool(post))
        body = post[-1]["body"] if post else {}
        rem = body.get("reminders", [])
        brk = [r for r in rem if r["title"] == "Zeit für eine Atempause"]
        check("C: training switch stays off", not await pg.is_checked("#reminderOnCheck"))
        check("C: only Atempausen sent (no training reminders)", rem and len(brk) == len(rem))
        check("C: payload limits (<= 60, title <= 80, body <= 160)", len(rem) <= 60 and all(len(r["title"]) <= 80 and len(r["body"]) <= 160 for r in rem), len(rem))
        check("C: body without names or free text", all(r["body"] == "2 Min. ruhig atmen: deine Nichtraucher-Pause" for r in brk), brk[:1])
        now = datetime.now(BERLIN)
        exp = []
        for i in range(14):
            d = (now + timedelta(days=i)).date()
            for t in ["09:15", "15:00", "18:30"]:
                dt = datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M").replace(tzinfo=BERLIN)
                if dt > now:
                    exp.append(dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"))
        got = sorted(r["at"] for r in brk)
        check("C: 3 a day at the chosen times for 14 days (UTC)", got == sorted(exp)[:60], f"{len(got)} vs {len(exp)}")
        prefs = json.loads(await pg.evaluate("() => localStorage.getItem('fwmc-reminders-v1')"))
        check("C: prefs saved", prefs.get("breaks", {}).get("on") is True and prefs["breaks"]["count"] == 3 and prefs["breaks"]["times"][0] == "09:15")
        # combined with training reminders: still capped at 60
        await pg.check("#reminderOnCheck"); await pg.wait_for_timeout(800)
        both = await pg.evaluate("() => window.__fwmcComputeReminders().length")
        check("C: combined list capped at 60", both <= 60, both)
        await pg.uncheck("#reminderOnCheck"); await pg.wait_for_timeout(800)
        check("C: unchecking trainings keeps the subscription", not any(x["method"] == "DELETE" for x in posts))
        await pg.uncheck("#reminderBreakCheck"); await pg.wait_for_timeout(800)
        check("C: both off -> DELETE", any(x["method"] == "DELETE" for x in posts))
        sw = open("../sw.js").read()
        check("C: sw.js opens ?bereich=atempause for this title", "Zeit für eine Atempause" in sw and "bereich=atempause" in sw)
        privacy = await pg.evaluate("() => document.getElementById('faqSheet') ? document.body.innerHTML.includes('Zeit für eine Atempause') : false")
        check("C: privacy/FAQ text mentions the Atempausen times", privacy)
        all_errors += errors
        await ctx.close()

        # ================= N: Schriftgröße + Sanfte Reize =================
        ctx, pg, errors = await new_ctx(b)
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(500)
        await open_master(pg)
        await pg.locator("#masterSeeGroup").scroll_into_view_if_needed()
        check("N: section 'Sehen und Reize'", (await pg.inner_text("#masterSeeGroup .group-label")).strip() == "Sehen und Reize")
        ts0 = float(await pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ts')"))
        await pg.click('[data-master-textsize="sehrgross"]'); await pg.wait_for_timeout(100)
        ts1 = float(await pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ts')"))
        check("N: Sehr groß multiplies --ts", abs(ts1 - min(1.3, ts0 * 1.25)) < 0.011, f"{ts0} -> {ts1}")
        tab_fs = await pg.evaluate("() => { const t = document.querySelector('.section-tab'); return t ? parseFloat(getComputedStyle(t).fontSize) : 0; }")
        await pg.check("#masterSoftCheck"); await pg.wait_for_timeout(100)
        await pg.locator("#masterSoftGroup").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/master_see_light.png")
        await pg.click("#masterSettingsCloseBtn")
        await pg.reload(); await pg.wait_for_timeout(500)
        ts2 = float(await pg.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--ts')"))
        m = json.loads(await pg.evaluate("() => localStorage.getItem('fwmc-master-v1')"))
        check("N: both persist across reload", abs(ts2 - ts1) < 0.011 and m.get("textSize") == "sehrgross" and m.get("softStimuli") is True)
        # back to normal text for the rest
        await open_master(pg); await pg.click('[data-master-textsize="normal"]'); await pg.click("#masterSettingsCloseBtn")
        # VT ready screen: note + link + override
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(400)
        note = pg.locator('#ready [data-soft-note]')
        check("N: VT ready shows 'Sanfte Reize sind an · Grundeinstellungen'", await note.is_visible() and "Sanfte Reize sind an" in await note.inner_text() and "Grundeinstellungen" in await note.inner_text())
        await pg.screenshot(path=f"{SHOTS}/vt_ready_note_light.png")
        await note.locator("button").click(); await pg.wait_for_timeout(400)
        in_view = await pg.evaluate("() => { const g = document.getElementById('masterSoftGroup').getBoundingClientRect(); return !document.getElementById('masterSettingsSheet').hidden && g.top >= 0 && g.top < innerHeight; }")
        check("N: link opens Grundeinstellungen at the section", in_view)
        await pg.click("#masterSettingsCloseBtn"); await pg.wait_for_timeout(200)
        # 08.10.: #ready now also holds Hütchen-Laufweg's own (hidden) #lwAdvanced
        # before the shared one, so open the shared Feineinstellungen by id.
        await pg.evaluate("() => { const d = document.querySelector('#ready #advanced'); if (d) d.open = true; }")
        check("N: Feineinstellungen have 'Sanfte Reize für diese Übung'", await pg.is_visible('#ready [data-soft-group]') and "Sanfte Reize für diese Übung" in await pg.inner_text('#ready [data-soft-group]'))
        check("N: soft min display time applies (0.8 s)", await pg.evaluate("() => { return window.__fwmcSoft.on('vt-color') && window.__fwmcSoft.show() >= 0.8; }"))
        await pg.click('#ready [data-soft-ex][data-soft-val="0"]'); await pg.wait_for_timeout(100)
        ov = json.loads(await pg.evaluate("() => localStorage.getItem('fwmc-soft-overrides-v1')"))
        check("N: override stored under fwmc-soft-overrides-v1", ov == {"vt-color": False}, ov)
        check("N: override off hides the note", not await note.is_visible())
        await pg.locator('#ready [data-soft-group]').scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/vt_ready_override_light.png")
        await pg.reload(); await pg.wait_for_timeout(500)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(400)
        check("N: override persists across reload", not await pg.evaluate("() => window.__fwmcSoft.on('vt-color')") and await pg.locator('#ready [data-soft-ex][data-soft-val="0"].active').count() == 1)
        await pg.evaluate("() => document.querySelector('#ready [data-soft-reset]').click()"); await pg.wait_for_timeout(100)
        check("N: 'Wieder den Grundeinstellungen folgen' resets", await pg.evaluate("() => window.__fwmcSoft.on('vt-color')") and await pg.evaluate("() => localStorage.getItem('fwmc-soft-overrides-v1')") == "{}")
        gap = await pg.evaluate("() => window.__fwmcSoft.gap(0.2, 0.5, 'vt-color')")
        check("N: soft minimum gap", gap[0] >= 1.2 and gap[1] >= gap[0], gap)
        # Hütchen sortieren is not affected
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="cone-tap"]'); await pg.wait_for_timeout(300)
        check("N: Hütchen sortieren not marked", not await note.is_visible())
        # live switch in the VT pause sheet
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="4-straight"]'); await pg.wait_for_timeout(300)
        await pg.click("#startBtn"); await pg.wait_for_timeout(800)
        await pg.click("#periphPauseBtn"); await pg.wait_for_timeout(200)
        live_off = '#periphPauseOverlay [data-soft-live][data-soft-val="0"]'
        check("N: pause sheet has Sanfte Reize", await pg.is_visible(live_off))
        check("N: pause shows current state (on)", await pg.locator('#periphPauseOverlay [data-soft-live][data-soft-val="1"].active').count() == 1)
        await pg.locator(live_off).scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/vt_pause_light.png")
        await pg.click(live_off); await pg.wait_for_timeout(100)
        check("N: live off for this run", not await pg.evaluate("() => window.__fwmcSoft.on('4-straight')"))
        check("N: live choice is not stored", await pg.evaluate("() => localStorage.getItem('fwmc-soft-overrides-v1')") in (None, "{}"))
        await pg.click("#periphResumeBtn"); await pg.wait_for_timeout(300)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        await pg.click("#startBtn"); await pg.wait_for_timeout(300)
        check("N: next run follows the settings again", await pg.evaluate("() => window.__fwmcSoft.on('4-straight')"))
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)
        # NAT: Blitz-Raster + Flash
        await pg.goto(BASE + "?bereich=nat"); await pg.wait_for_timeout(400)
        await pg.evaluate("() => { document.querySelector('#natHome .sub-tab[data-nat-sub=\"blitz\"]').click(); document.getElementById('blitzOpenBtn').click(); }")
        await pg.wait_for_timeout(300)
        check("N: Blitz-Raster ready marked", await pg.is_visible('#blitzReady [data-soft-note]'))
        check("N: Blitz soft class on", await pg.evaluate("() => document.body.classList.contains('soft-blitz')"))
        await pg.screenshot(path=f"{SHOTS}/blitz_ready_light.png")
        check("N: Flash screens marked", await pg.evaluate("() => ['flashReady','flashTrainingReady'].every(id => document.querySelector('#' + id + ' [data-soft-note]'))"))
        check("N: Flash/Blitz pause sheets have the switch", await pg.evaluate("() => ['blitzPauseOverlay','flashPauseOverlay'].every(id => document.querySelector('#' + id + ' [data-soft-live]'))"))
        all_errors += errors
        await ctx.close()

        # ================= Dark mode =================
        ctx, pg, errors = await new_ctx(b, scheme="dark", extra_init="localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false, softStimuli:true}));")
        await pg.goto(BASE + "?bereich=heute"); await pg.wait_for_timeout(500)
        await pg.locator("#todayBreak").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/heute_card_dark.png")
        bg = await pg.evaluate("() => getComputedStyle(document.getElementById('todayBreak')).backgroundColor")
        nums = [int(x) for x in bg[bg.index("(") + 1:bg.index(")")].split(",")[:3]]
        check("D: card is dark in dark mode", sum(nums) < 200, bg)
        await pg.click("#todayBreakInfoBtn"); await pg.wait_for_timeout(200)
        await pg.screenshot(path=f"{SHOTS}/heute_info_dark.png")
        await pg.click("#breakInfoCloseBtn")
        await open_master(pg)
        await pg.locator("#masterSoftGroup").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/master_see_dark.png")
        await pg.locator("#reminderGroup").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/master_reminder_dark.png")
        await pg.click("#masterSettingsCloseBtn")
        await pg.goto(BASE + "?bereich=visual"); await pg.wait_for_timeout(400)
        await pg.click('.excard[data-exercise="vt-color"]'); await pg.wait_for_timeout(400)
        await pg.screenshot(path=f"{SHOTS}/vt_ready_note_dark.png")
        nb = await pg.evaluate("() => getComputedStyle(document.querySelector('#ready [data-soft-note]')).backgroundColor")
        nn = [int(x) for x in nb[nb.index("(") + 1:nb.index(")")].split(",")[:3]]
        check("D: note is dark in dark mode", sum(nn) < 300, nb)
        await pg.goto(BASE + "?bereich=breath"); await pg.wait_for_timeout(400)
        await pg.evaluate("() => [...document.querySelectorAll('#patternGrid > button')].pop().click()"); await pg.wait_for_timeout(300)
        await pg.locator("#wimhofRoundRestGroup").scroll_into_view_if_needed()
        await pg.screenshot(path=f"{SHOTS}/wimhof_ready_dark.png")
        all_errors += errors
        await ctx.close()
        await b.close()

    check("no pageerror/console error", not all_errors, "; ".join(all_errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
