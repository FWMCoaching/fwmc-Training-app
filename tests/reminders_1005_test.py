"""Erinnerungen (2026-10-05): push reminders before planned trainings.

Grundeinstellungen section (switch, lead time row, morning time, status
line), the computed payload (UTC times for Europe/Berlin local times, lead
time, morning time for untimed entries, DST), sync to the Worker on enable
and on plan change, DELETE + unsubscribe on switch-off, graceful states
(not set up yet, iPhone in the browser, permission denied), privacy text,
no page errors. Notification/PushManager/serviceWorker are faked with an
init script; the Worker is routed with page.route."""
import asyncio
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html?bereich=heute"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
BERLIN = ZoneInfo("Europe/Berlin")
KEY = "BCVODgVri4ZeawfHr3aK0XBrzRKXW99TZWGDqPgydlQqIVam8-qlZ2UsrJVjQRArI2-ANSeVYTiURAqn9Msd9Nk"

results = []


def check(name, ok):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}")


# Fake push stack. Subscription and permission survive a reload through
# sessionStorage, like the real browser state would.
FAKE_PUSH = r"""
(() => {
  const ss = window.sessionStorage;
  window.__pushLog = JSON.parse(ss.getItem('fake-push-log') || '[]');
  const log = (x) => { window.__pushLog.push(x); ss.setItem('fake-push-log', JSON.stringify(window.__pushLog)); };
  const makeSub = () => ({
    endpoint: 'https://fcm.googleapis.com/fcm/send/test-device-1',
    toJSON() { return { endpoint: this.endpoint, expirationTime: null, keys: { p256dh: 'BPfake', auth: 'authfake' } }; },
    async unsubscribe() { log('unsubscribe'); ss.removeItem('fake-sub'); return true; },
  });
  const pm = {
    async getSubscription() { return ss.getItem('fake-sub') ? makeSub() : null; },
    async subscribe(opts) {
      log('subscribe:' + (opts && opts.applicationServerKey ? opts.applicationServerKey.length : 0) + ':' + !!(opts && opts.userVisibleOnly));
      ss.setItem('fake-sub', '1'); return makeSub();
    },
  };
  const reg = { pushManager: pm, scope: location.origin + '/' };
  Object.defineProperty(navigator, 'serviceWorker', { configurable: true, value: {
    ready: Promise.resolve(reg), register: async () => reg, addEventListener() {}, removeEventListener() {}, controller: null } });
  if (!('PushManager' in window)) window.PushManager = function () {};
  class FakeNotification {
    static get permission() { return ss.getItem('fake-perm') || 'default'; }
    static async requestPermission() {
      const a = ss.getItem('fake-perm-answer') || 'granted';
      log('ask:' + a); ss.setItem('fake-perm', a); return a;
    }
  }
  window.Notification = FakeNotification;
})();
"""


def utc_iso(local_str):
    d = datetime.strptime(local_str, "%Y-%m-%d %H:%M").replace(tzinfo=BERLIN)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


async def open_master(pg):
    await pg.locator(".master-settings-btn:visible").first.click()
    await pg.wait_for_timeout(250)
    await pg.locator("#reminderGroup").scroll_into_view_if_needed()


async def new_page(b, init_storage, posts, extra_init=None, user_agent=None):
    kw = dict(viewport={"width": 390, "height": 844}, service_workers="block", timezone_id="Europe/Berlin")
    if user_agent:
        kw["user_agent"] = user_agent
    ctx = await b.new_context(**kw)
    errors = []
    await ctx.add_init_script(FAKE_PUSH)
    if extra_init:
        await ctx.add_init_script(extra_init)
    seed = "".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(v)});" for k, v in init_storage.items())
    await ctx.add_init_script("try{if(!sessionStorage.getItem('seeded')){" + seed + "sessionStorage.setItem('seeded','1')}}catch(e){}")
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

    async def handle(route):
        req = route.request
        posts.append({"method": req.method, "body": json.loads(req.post_data or "null")})
        await route.fulfill(status=200, content_type="application/json", body='{"ok":true}',
                            headers={"Access-Control-Allow-Origin": "*"})
    await pg.route("**/online-training.fwmc.workers.dev/reminders", handle)
    return ctx, pg, errors


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        today = datetime.now(BERLIN).date()
        monday = today - timedelta(days=today.weekday())
        tomorrow = (today + timedelta(days=1)).isoformat()
        wd = today.weekday()
        days = [[] for _ in range(7)]
        days[wd] = [{"id": "t1", "area": "cardio", "what": "", "code": "", "time": "23:59", "minutes": 20}]
        plan = {"startDate": monday.isoformat(), "phases": [{"id": "p1", "name": "Phase 1", "weeks": 0, "days": days}],
                "extras": {tomorrow: [{"id": "x1", "area": "breath", "what": "", "code": "", "time": "10:00", "minutes": 10}]},
                "skips": {}, "done": {}}
        base_storage = {"fwmc-tips-seen": "true", "fwmc-plan-v1": json.dumps(plan), "fwmc-test-reminder-key": json.dumps(KEY)}

        # ---- 1. Not set up yet (no VAPID key): switch disabled, clear text ----
        posts = []
        st = dict(base_storage); del st["fwmc-test-reminder-key"]
        ctx, pg, errors = await new_page(b, st, posts)
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        await open_master(pg)
        check("section in Grundeinstellungen", await pg.locator("#masterSettingsSheet #reminderGroup").is_visible())
        check("label 'Erinnerungen'", (await pg.locator("#reminderGroup .group-label").first.inner_text()).strip() == "Erinnerungen")
        check("not set up: switch disabled", await pg.locator("#reminderOnCheck").is_disabled())
        check("not set up: 'werden gerade eingerichtet'", "werden gerade eingerichtet" in await pg.inner_text("#reminderStatus"))
        labels = [t.strip() for t in await pg.locator("[data-reminder-lead]").all_inner_texts()]
        check("lead row: Zur Zeit, 5, 10, 15, 30", labels == ["Zur Zeit", "5 Min. vorher", "10 Min. vorher", "15 Min. vorher", "30 Min. vorher"])
        check("default lead 10 active", await pg.locator('[data-reminder-lead="10"].active').count() == 1)
        check("default morning 08:00", await pg.input_value("#reminderMorningInput") == "08:00")
        sizes = await pg.evaluate("""() => [...document.querySelectorAll('[data-reminder-lead], #reminderMorningInput')].map(e => e.getBoundingClientRect().height)""")
        check("tap targets >= 44 px", min(sizes) >= 44)
        check("no request without key", not posts)
        await pg.screenshot(path="reminders_setup.png")
        check("no page errors (setup)", not errors)
        if errors: print(errors)
        await ctx.close()

        # ---- 2. iPhone in Safari (not installed): explain home screen ----
        posts = []
        ios_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
        ctx, pg, errors = await new_page(b, base_storage, posts, user_agent=ios_ua)
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        await open_master(pg)
        txt = await pg.inner_text("#reminderStatus")
        check("iPhone: home screen hint", "Startbildschirm" in txt and "Zum Home-Bildschirm" in txt and "16.4" in txt)
        check("iPhone: switch disabled", await pg.locator("#reminderOnCheck").is_disabled())
        await pg.screenshot(path="reminders_ios.png")
        check("no page errors (iOS)", not errors)
        await ctx.close()

        # ---- 3. Permission denied by the user ----
        posts = []
        ctx, pg, errors = await new_page(b, base_storage, posts, extra_init="sessionStorage.setItem('fake-perm-answer','denied')")
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        await open_master(pg)
        check("supported: switch enabled", await pg.locator("#reminderOnCheck").is_enabled())
        check("off status mentions asking", "Aus" in await pg.inner_text("#reminderStatus"))
        await pg.locator("#reminderOnCheck").click(); await pg.wait_for_timeout(400)
        check("denied: switch back off", not await pg.locator("#reminderOnCheck").is_checked())
        check("denied: explains Einstellungen", "Einstellungen" in await pg.inner_text("#reminderStatus"))
        check("denied: nothing sent", not posts)
        check("denied: no subscription", not any(x.startswith("subscribe") for x in await pg.evaluate("window.__pushLog")))
        check("no page errors (denied)", not errors)
        await ctx.close()

        # ---- 4. Happy path: enable, payload, persistence, plan change, off ----
        posts = []
        ctx, pg, errors = await new_page(b, base_storage, posts)
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        await open_master(pg)
        await pg.locator("#reminderOnCheck").click(); await pg.wait_for_timeout(600)
        log = await pg.evaluate("window.__pushLog")
        check("asks permission on enable", "ask:granted" in log)
        check("subscribes with the 65-byte VAPID key, userVisibleOnly", "subscribe:65:true" in log)
        check("switch stays on", await pg.locator("#reminderOnCheck").is_checked())
        check("one POST after enabling", len([x for x in posts if x["method"] == "POST"]) == 1)
        body = posts[0]["body"] if posts else {}
        check("POST carries the subscription", body.get("subscription", {}).get("endpoint", "").endswith("test-device-1") and "keys" in body.get("subscription", {}))
        check("POST has only subscription + reminders", set(body.keys()) == {"subscription", "reminders"})
        rems = body.get("reminders", [])
        check("every reminder only at/title/body", all(set(r.keys()) == {"at", "title", "body"} for r in rems))
        exp_tomorrow = {"at": utc_iso(f"{tomorrow} 09:50"), "title": "Training um 10:00 Uhr", "body": "In 10 Minuten: Atemtraining · 10 Min."}
        check("tomorrow 10:00 entry -> 09:50 Berlin in UTC", exp_tomorrow in rems)
        status = await pg.inner_text("#reminderStatus")
        check("status 'Aktiv – n Erinnerungen'", status.startswith("Aktiv") and "Erinnerung" in status)
        await pg.screenshot(path="reminders_on.png")

        # Computed payload, fixed clock: Fri 2026-10-23 12:00 CEST, DST ends Sun 25.10.
        fixed_plan_js = """(() => {
          const days = [[{id:'a',area:'cardio',what:'',code:'',time:'18:00',minutes:20}],[], [{id:'b',area:'visual',what:'',code:'',time:'',minutes:15}],[],[],[],[]];
          return {startDate:'2026-09-28', phases:[{id:'p',name:'P',weeks:0,days}], extras:{'2026-10-24':[{id:'c',area:'breath',what:'',code:'',time:'09:30',minutes:10}],
            '2026-10-23':[{id:'d',area:'nat',what:'',code:'',time:'11:00',minutes:10}]}, skips:{}, done:{}};
        })()"""
        # Load the fixed plan into the page (reload reads fwmc-plan-v1).
        await pg.evaluate(f"localStorage.setItem('fwmc-plan-v1', JSON.stringify({fixed_plan_js}))")
        await pg.click('[data-reminder-lead="10"]')
        await pg.reload(); await pg.wait_for_timeout(600)
        got = await pg.evaluate("window.__fwmcComputeReminders(new Date('2026-10-23T10:00:00Z'))")
        exp = [
            {"at": utc_iso("2026-10-24 09:20"), "title": "Training um 09:30 Uhr", "body": "In 10 Minuten: Atemtraining · 10 Min."},
            {"at": utc_iso("2026-10-26 17:50"), "title": "Training um 18:00 Uhr", "body": "In 10 Minuten: Cardio · 20 Min."},
            {"at": utc_iso("2026-10-28 08:00"), "title": "Heute steht Training an", "body": "Heute geplant: Visual Training · 15 Min."},
            {"at": utc_iso("2026-11-02 17:50"), "title": "Training um 18:00 Uhr", "body": "In 10 Minuten: Cardio · 20 Min."},
            {"at": utc_iso("2026-11-04 08:00"), "title": "Heute steht Training an", "body": "Heute geplant: Visual Training · 15 Min."},
        ]
        check("payload: 14 days, past entry of today skipped, sorted", got == exp)
        if got != exp: print(json.dumps(got, indent=1, ensure_ascii=False))
        check("CEST before / CET after the DST switch", got and got[0]["at"] == "2026-10-24T07:20:00.000Z" and got[1]["at"] == "2026-10-26T16:50:00.000Z")
        check("morning time for untimed entry in UTC", got and got[2]["at"] == "2026-10-28T07:00:00.000Z")

        # Lead time "Zur Zeit" and 30, morning 06:45 - and persistence across reload.
        await open_master(pg)
        check("still on after reload", await pg.locator("#reminderOnCheck").is_checked())
        await pg.click('[data-reminder-lead="30"]')
        await pg.fill("#reminderMorningInput", "06:45")
        await pg.dispatch_event("#reminderMorningInput", "change")
        await pg.wait_for_timeout(200)
        await pg.reload(); await pg.wait_for_timeout(600)
        await open_master(pg)
        check("lead 30 persists across reload", await pg.locator('[data-reminder-lead="30"].active').count() == 1)
        check("morning 06:45 persists across reload", await pg.input_value("#reminderMorningInput") == "06:45")
        got = await pg.evaluate("window.__fwmcComputeReminders(new Date('2026-10-23T10:00:00Z'))")
        check("lead 30 applied", got[0]["at"] == "2026-10-24T07:00:00.000Z" and got[0]["body"].startswith("In 30 Minuten:"))
        check("morning 06:45 applied", any(r["at"] == "2026-10-28T05:45:00.000Z" for r in got))
        await pg.click('[data-reminder-lead="0"]'); await pg.wait_for_timeout(100)
        got = await pg.evaluate("window.__fwmcComputeReminders(new Date('2026-10-23T10:00:00Z'))")
        check("'Zur Zeit' = at the training time, 'Jetzt:'", got[0]["at"] == "2026-10-24T07:30:00.000Z" and got[0]["body"] == "Jetzt: Atemtraining · 10 Min.")
        # Cap at 60.
        await pg.evaluate("""(() => {
          const p = JSON.parse(localStorage.getItem('fwmc-plan-v1'));
          p.phases[0].days = [0,1,2,3,4,5,6].map(i => [0,1,2,3,4,5].map(k => ({id:'m'+i+k, area:'cardio', what:'', code:'', time: String(8+k*2).padStart(2,'0')+':00', minutes:10})));
          localStorage.setItem('fwmc-plan-v1', JSON.stringify(p)); return true; })()""")
        await pg.reload(); await pg.wait_for_timeout(600)
        got = await pg.evaluate("window.__fwmcComputeReminders(new Date('2026-10-23T10:00:00Z'))")
        check("capped at 60 reminders", len(got) == 60)
        await ctx.close()

        # ---- 5. Sync on plan change, then switch off -> DELETE + unsubscribe ----
        posts = []
        st = dict(base_storage)
        st["fwmc-reminders-v1"] = json.dumps({"on": True, "lead": 10, "morning": "08:00"})
        ctx, pg, errors = await new_page(b, st, posts, extra_init="sessionStorage.setItem('fake-perm','granted');sessionStorage.setItem('fake-sub','1')")
        await pg.goto(BASE); await pg.wait_for_timeout(2800)
        check("syncs on app start when on", len(posts) == 1 and posts[0]["method"] == "POST")
        before = posts[-1]["body"]["reminders"] if posts else []
        late = datetime.now(BERLIN).strftime("%H:%M") >= "23:45"
        # Tick today's planned 23:59 entry -> savePlan -> new sync without it.
        await pg.locator("#dayPanelBody .day-act[data-act='done']").first.click()
        await pg.wait_for_timeout(2200)
        check("plan change triggers a new sync", len(posts) == 2)
        after = posts[-1]["body"]["reminders"] if len(posts) == 2 else []
        today_at = utc_iso(f"{today.isoformat()} 23:49")
        if not late:
            check("ticked entry's reminder was in the first sync", any(r["at"] == today_at for r in before))
        check("ticked entry's reminder is gone", not any(r["at"] == today_at for r in after))
        await open_master(pg)
        await pg.locator("#reminderOnCheck").click(); await pg.wait_for_timeout(500)
        dels = [x for x in posts if x["method"] == "DELETE"]
        check("switch-off sends DELETE with the endpoint", len(dels) == 1 and dels[0]["body"].get("endpoint", "").endswith("test-device-1"))
        check("switch-off unsubscribes", "unsubscribe" in await pg.evaluate("window.__pushLog"))
        check("stored off", json.loads(await pg.evaluate("localStorage.getItem('fwmc-reminders-v1')"))["on"] is False)
        n = len(posts)
        await pg.click('[data-reminder-lead="15"]'); await pg.wait_for_timeout(1800)
        check("no sync while off", len(posts) == n)

        # Privacy sheet: explains the reminder storage, reachable from the section.
        await pg.locator("#reminderGroup .privacy-open-btn").click(); await pg.wait_for_timeout(250)
        check("privacy sheet opens above Grundeinstellungen", await pg.evaluate("""() => { const r = document.querySelector('#privacySheet .sheet-inner').getBoundingClientRect();
            const el = document.elementFromPoint(r.left + r.width/2, r.top + 30); return !!(el && el.closest('#privacySheet')); }"""))
        ptxt = await pg.evaluate("document.getElementById('privacyReminders').textContent")
        check("privacy: push address + times stored at Cloudflare", "Push-Adresse" in ptxt and "Cloudflare" in ptxt and "Zeiten" in ptxt)
        check("privacy: deleted after sending / when off", "nach dem Versenden gel" in ptxt and "schaltest du die Erinnerungen aus" in ptxt)
        check("privacy: never names Fabian", "Fabian" not in ptxt)
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(150)
        check("no page errors (sync/off)", not errors)
        if errors: print(errors)
        await ctx.close()

        # ---- 6. Dark mode screenshot of the section ----
        posts = []
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark", service_workers="block", timezone_id="Europe/Berlin")
        await ctx.add_init_script(FAKE_PUSH)
        await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-reminder-key', JSON.stringify('" + KEY + "'))")
        pg = await ctx.new_page()
        await pg.goto(BASE); await pg.wait_for_timeout(500)
        await open_master(pg)
        await pg.screenshot(path="reminders_dark.png")
        await ctx.close()
        await b.close()

    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("FAILED:", failed)


asyncio.run(main())
