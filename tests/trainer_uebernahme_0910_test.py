"""Bestwerte + Einstellungen vom Trainer (Fabian 09.10.): a Kunden-Training
starts with empty best stores, each client run carries the client's bests
and settings, the QR payload brings them along; on the client's phone the
bests merge upwards and each exercise asks "Mit den Einstellungen deines
Trainers weitertrainieren?". Size only between the same device kind,
volume never. Run from tests/ with a dev server on :8845."""
import asyncio, json, base64, zlib, time
from playwright.async_api import async_playwright

ROOT = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results, errors = [], []
def check(name, ok, extra=""):
    results.append(bool(ok)); print(f"{name}: {bool(ok)}" + (f"  [{str(extra)[:200]}]" if not ok and extra != "" else ""))

async def new_page(b, seed=None, width=390, height=844, tablet=False):
    ctx = await b.new_context(viewport={"width": width, "height": height}, screen={"width": 820 if tablet else 390, "height": 1180 if tablet else 844},
                              service_workers="block", has_touch=True)
    init = "try{localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1','{\"startCountdown\":false}');localStorage.setItem('fwmc-test-trainer-tools','true');"
    if seed:
        init += "if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');"
        for k, v in seed.items():
            init += f"localStorage.setItem({json.dumps(k)}, {json.dumps(json.dumps(v))});"
        init += "}"
    init += "}catch(e){}"
    await ctx.add_init_script(init)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    await pg.route("https://online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
    return ctx, pg

async def ls(pg, key, fallback=None):
    v = await pg.evaluate(f"localStorage.getItem({json.dumps(key)})")
    return json.loads(v) if v else fallback

async def tm_click(pg, sel):
    if not await pg.is_visible("#trainerMenuSheet"):
        await pg.locator(".trainer-mode-btn:visible").first.click(); await pg.wait_for_timeout(150)
    await pg.click(sel)

def payload(url):
    data = url.split("#import=")[1].split(".", 3)[3]
    raw = base64.urlsafe_b64decode(data[1:] + "=" * (-len(data[1:]) % 4))
    return json.loads(zlib.decompress(raw, -15) if data[0] == "z" else raw)

def make_url(obj):
    raw = zlib.compressobj(9, zlib.DEFLATED, -15)
    z = raw.compress(json.dumps(obj).encode()) + raw.flush()
    return ROOT + "#import=1.1.abcd.z" + base64.urlsafe_b64encode(z).decode().rstrip("=")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        # ===== trainer device (tablet) =====
        ctx, pg = await new_page(b, seed={"fwmc-remember-best-v1": {"fixed": {"leicht": 9}}}, tablet=True)
        await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(500)
        await tm_click(pg, '#tmModes [data-tm="client"]'); await pg.wait_for_timeout(300)
        check("client session starts with empty bests (trainer's 9 is not the client's)", await ls(pg, "fwmc-remember-best-v1") is None)
        await pg.goto(ROOT + "?bereich=nat"); await pg.wait_for_timeout(500)
        await pg.click('#natHome .sub-tab[data-nat-sub="remember"]'); await pg.wait_for_timeout(150)
        await pg.click("#rememberOpenFixed"); await pg.wait_for_timeout(200)
        await pg.click("#rememberAdvanced summary") if await pg.is_visible("#rememberAdvanced summary") else None
        await pg.locator('[data-remember-diff="schwer"]').first.click(); await pg.wait_for_timeout(100)
        await pg.click("#rememberReadyStartBtn")
        for _ in range(120):  # wait until the numbers are covered, then tap them in order (level 1 cleared)
            if await pg.locator("#rememberStage .remember-marker.covered").count() >= 2: break
            await pg.wait_for_timeout(100)
        nums = await pg.evaluate("[...document.querySelectorAll('#rememberStage .remember-marker.covered')].map(m => Number(m.dataset.num)).sort((a,b)=>a-b)")
        for n in nums:
            await pg.locator(f'#rememberStage .remember-marker.covered[data-num="{n}"]').click(); await pg.wait_for_timeout(120)
        await pg.wait_for_timeout(600)
        await pg.evaluate("localStorage.setItem('fwmc-remember-best-v1', JSON.stringify({fixed: {schwer: 6}}))")  # the client's session best
        await pg.click("#rememberBackBtn"); await pg.wait_for_timeout(300)
        if await pg.is_visible("#confirmSheet"): await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(300)
        runs = await ls(pg, "fwmc-client-runs-v1", [])
        r = runs[0] if runs else {}
        check("client run carries bests, settings and device kind", r.get("kind") == "remember" and r.get("bs") == {"fixed": {"schwer": 6}}
              and "revealBaseS" in (r.get("ps") or {}) and r.get("dk") == "tablet", r)
        if await pg.is_visible("#rememberDoneBackBtn"): await pg.click("#rememberDoneBackBtn"); await pg.wait_for_timeout(300)
        await pg.click("#clientRunEndBtn"); await pg.wait_for_timeout(500)
        await pg.click("#handoverGoBtn"); await pg.wait_for_timeout(800)
        url = await pg.get_attribute("#handoverQrCanvas", "data-url")
        pl = payload(url)
        check("QR payload has b/s/d", pl.get("b") == {"remember": {"fixed": {"schwer": 6}}} and "remember" in pl.get("s", {}) and pl.get("d") == "tablet", pl)
        check("no volume in the settings", all("volume" not in v for v in pl.get("s", {}).values()))
        check("trainer's own best back after the session", await ls(pg, "fwmc-remember-best-v1") == {"fixed": {"leicht": 9}})
        sent_reveal = pl["s"]["remember"]["revealBaseS"]
        await ctx.close()

        # ===== client phone: best merge + settings question =====
        cctx, cp = await new_page(b, seed={"fwmc-remember-best-v1": {"fixed": {"schwer": 4, "leicht": 8}},
                                         "fwmc-remember-prefs-v1": {"revealBaseS": 9.9, "markerScale": 1.4}})
        await cp.goto(url); await cp.wait_for_timeout(700)
        check("import sheet mentions bests and the settings question",
              "Bestleistungen" in await cp.inner_text("#handoverImportText") and "Einstellungen deines Trainers" in await cp.inner_text("#handoverImportText"))
        await cp.click("#handoverImportYesBtn"); await cp.wait_for_timeout(900)
        check("bests merged upwards, own other values kept", await ls(cp, "fwmc-remember-best-v1") == {"fixed": {"schwer": 6, "leicht": 8}})
        txt = await cp.inner_text("#confirmSheet") if await cp.is_visible("#confirmSheet") else ""
        check("asks per exercise", "Positionen merken" in txt and "Einstellungen deines Trainers" in txt, txt)
        check("tablet -> phone: size note", "Größe bleibt deshalb bei dir" in txt, txt)
        await cp.click("#confirmYesBtn"); await cp.wait_for_timeout(500)
        pr = await ls(cp, "fwmc-remember-prefs-v1", {})
        check("settings applied", abs(pr.get("revealBaseS", 0) - sent_reveal) < 1e-9, pr)
        check("size stays the client's (other device kind)", pr.get("markerScale") == 1.4, pr)
        check("note 'von deinem Trainer übernommen' stored", "remember" in (await ls(cp, "fwmc-trainer-settings-v1", {})))
        await cp.goto(ROOT + "?bereich=nat"); await cp.wait_for_timeout(500)
        await cp.click('#natHome .sub-tab[data-nat-sub="remember"]'); await cp.wait_for_timeout(150)
        await cp.click("#rememberOpenFixed"); await cp.wait_for_timeout(250)
        check("ready screen shows the note", await cp.is_visible('#rememberReady .trainer-set-note'))
        await cp.screenshot(path="screenshots/trainer_uebernahme_note.png")
        await cctx.close()

        # ===== hostile / odd payloads: runs still come, odd extras dropped =====
        now = int(time.time()) - 60
        bad = {"v": 1, "e": [["x1", now, "remember", "Positionen merken · Feste Positionen", 60]],
               "b": {"remember": {"fixed": {"schwer": "<b>"}}, "evil": {"a": 1}}, "s": {"remember": {"revealBaseS": "x", "volume": 1, "__proto__": {}}, "evil": {}}, "d": "tablet"}
        cctx, cp = await new_page(b)
        await cp.goto(make_url(bad)); await cp.wait_for_timeout(700)
        await cp.click("#handoverImportYesBtn"); await cp.wait_for_timeout(700)
        check("odd extras dropped, run imported, no question", len(await ls(cp, "fwmc-history-v1", [])) == 1 and await ls(cp, "fwmc-remember-best-v1") is None
              and not await cp.is_visible("#confirmSheet"))
        await cctx.close()
        # same device kind: size travels, "Meine behalten" keeps everything
        good = {"v": 1, "e": [["x2", now, "mot", "Objektverfolgung (MOT) · Tempo", 60]], "s": {"mot": {"speed": 0.2, "objScale": 1.3}}, "d": "phone"}
        cctx, cp = await new_page(b)
        await cp.goto(make_url(good)); await cp.wait_for_timeout(700)
        await cp.click("#handoverImportYesBtn"); await cp.wait_for_timeout(900)
        txt = await cp.inner_text("#confirmSheet")
        check("phone -> phone: no size note", "Größe" not in txt, txt)
        await cp.click("#confirmYesBtn"); await cp.wait_for_timeout(400)
        mp = await ls(cp, "fwmc-mot-prefs-v1", {})
        check("same kind: size taken over too", mp.get("objScale") == 1.3 and abs(mp.get("speed") - 0.2) < 1e-9, mp)
        await cctx.close()
        good["e"][0][0] = "x3"
        cctx, cp = await new_page(b)
        await cp.goto(make_url(good)); await cp.wait_for_timeout(700)
        await cp.click("#handoverImportYesBtn"); await cp.wait_for_timeout(900)
        await cp.click("#confirmNoBtn"); await cp.wait_for_timeout(300)
        check("'Meine behalten' changes nothing", (await ls(cp, "fwmc-mot-prefs-v1")) is None and await ls(cp, "fwmc-trainer-settings-v1") is None)
        await cctx.close()
        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
