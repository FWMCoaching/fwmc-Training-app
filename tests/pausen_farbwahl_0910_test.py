"""Pausen-Farbwähler (Fabian 09.10.: Hintergrund sprang in der Pause auf
50 %): real taps on every NAT pause colour picker - a new colour and the
active one again - alone and inside a Kombi. The intensity must stay where
the run is; only a pick at 0 % jumps to 50 % (by design, so it is visible).
A Kombi never changes the exercise's own settings. Run from tests/."""
import asyncio, json
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results, errors = [], []
def check(name, ok, extra=""):
    results.append(bool(ok)); print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))

# exercise -> (sub tab, opener, prefs key, kombi block)
EX = {
    "remember": ("remember", "#rememberOpenFixed", "fwmc-remember-prefs-v1", {"domain": "nat", "mode": "fixed", "duration": 60}),
    "blitz": ("blitz", "#blitzOpenBtn", "fwmc-blitz-prefs-v1", {"domain": "blitz", "duration": 60}),
    "flash": ("flash", "#flashOpenClimb", "fwmc-flash-prefs-v1", {"domain": "flash", "mode": "climb", "duration": 60}),
    "mot": ("mot", "#motOpenSpeed", "fwmc-mot-prefs-v1", {"domain": "mot", "mode": "speed", "duration": 60}),
    "balance": ("balance", "#balanceOpenBtn", "fwmc-balance-prefs-v1", {"domain": "balance", "duration": 60}),
    "schulte": ("schulte", "#schulteOpenFest", "fwmc-schulte-prefs-v1", {"domain": "schulte", "mode": "fest", "duration": 120}),
}

async def ctx_page(b, store):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    base = {"fwmc-tips-seen": True, "fwmc-master-v1": {"startCountdown": False}}
    base.update(store)
    js = "".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(json.dumps(v))});" for k, v in base.items())
    await ctx.add_init_script(f"if (!sessionStorage.getItem('seeded')) {{ {js} sessionStorage.setItem('seeded','1'); }}")
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    await pg.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
    return ctx, pg

async def pause_and_tap(pg, ex, label):
    await pg.click(f"#{ex}PauseBtn"); await pg.wait_for_timeout(250)
    val = lambda: pg.inner_text(f"#{ex}PauseBgValue")
    before = await val()
    sw = pg.locator(f"#{ex}PauseBgColorPicker .color-swatch")
    active = pg.locator(f"#{ex}PauseBgColorPicker .color-swatch.active")
    await active.first.scroll_into_view_if_needed()
    await active.first.tap() if False else await active.first.click(); await pg.wait_for_timeout(120)
    after_same = await val()
    other = pg.locator(f"#{ex}PauseBgColorPicker .color-swatch:not(.active)").first
    await other.click(); await pg.wait_for_timeout(120)
    after_other = await val()
    check(f"{label}: pause shows the run's 30 %", before == "30 %", before)
    check(f"{label}: tapping the active colour keeps 30 %", after_same == "30 %", after_same)
    check(f"{label}: tapping another colour keeps 30 %", after_other == "30 %", after_other)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        for ex, (sub, opener, key, block) in EX.items():
            # 1. alone, own background 30 %
            ctx, pg = await ctx_page(b, {key: {"bgColorKey": "blau", "bgIntensity": 0.3, "bgCustom": True}})
            await pg.goto(URL + "?bereich=nat"); await pg.wait_for_timeout(500)
            await pg.click(f'#natHome .sub-tab[data-nat-sub="{sub}"]'); await pg.wait_for_timeout(150)
            await pg.click(opener); await pg.wait_for_timeout(200)
            await pg.click(f"#{ex}ReadyStartBtn"); await pg.wait_for_timeout(600)
            await pause_and_tap(pg, ex, f"{ex} alone")
            await ctx.close()
            # 2. alone, 0 % -> a colour pick jumps to 50 % (by design)
            ctx, pg = await ctx_page(b, {key: {"bgColorKey": "blau", "bgIntensity": 0, "bgCustom": True}})
            await pg.goto(URL + "?bereich=nat"); await pg.wait_for_timeout(500)
            await pg.click(f'#natHome .sub-tab[data-nat-sub="{sub}"]'); await pg.wait_for_timeout(150)
            await pg.click(opener); await pg.wait_for_timeout(200)
            await pg.click(f"#{ex}ReadyStartBtn"); await pg.wait_for_timeout(600)
            await pg.click(f"#{ex}PauseBtn"); await pg.wait_for_timeout(250)
            await pg.locator(f"#{ex}PauseBgColorPicker .color-swatch:not(.active)").first.click(); await pg.wait_for_timeout(120)
            check(f"{ex} alone at 0 %: a pick shows 50 %", await pg.inner_text(f"#{ex}PauseBgValue") == "50 %")
            await ctx.close()
            # 3. Kombi block with its own 30 %, the client's own setting 0 %
            blk = dict(block, prefs={"bgColorKey": "gelb", "bgIntensity": 0.3, "bgCustom": True})
            combo = [{"id": "k1", "name": "Farbtest", "blocks": [blk], "createdAt": "2026-10-09T08:00:00Z", "lastUsed": "2026-10-09T08:00:00Z"}]
            ctx, pg = await ctx_page(b, {key: {"bgColorKey": "blau", "bgIntensity": 0, "bgCustom": True}, "fwmc-combo-saved-v1": combo})
            await pg.goto(URL + "?bereich=breath"); await pg.wait_for_timeout(500)
            await pg.click("#breathHome .combo-entry-link"); await pg.wait_for_timeout(250)
            await pg.click("#comboSavedList .bundle-item >> nth=0"); await pg.wait_for_timeout(300)
            if await pg.is_visible("#comboStartBtn"):
                await pg.click("#comboStartBtn")
            await pg.wait_for_timeout(800)
            await pause_and_tap(pg, ex, f"{ex} in Kombi")
            await pg.click(f"#{ex}BackBtn"); await pg.wait_for_timeout(300)
            if await pg.is_visible("#confirmSheet"):
                yes = pg.locator("#confirmSheet button.start-btn").first
                await yes.click(); await pg.wait_for_timeout(300)
            own = json.loads(await pg.evaluate(f"localStorage.getItem('{key}')"))
            check(f"{ex} in Kombi: own setting untouched (0 %, blau)", own.get("bgIntensity") == 0 and own.get("bgColorKey") == "blau", f"{own.get('bgColorKey')} {own.get('bgIntensity')}")
            await ctx.close()
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
