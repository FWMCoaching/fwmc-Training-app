"""Speicher-Register + Modus-Isolation (Fabian 2026-10-09: "solche
Fehlerquellen ohne Zufallsbefund finden").

1. Static: every fwmc- key literal in app.js is listed in
   speicher_register.json; "restore" keys match HO_SNAP_RE, all others don't;
   backup:false keys are exactly BACKUP_EXCLUDE.
2. Live: after walking every area home and the Grundeinstellungen, every key
   in localStorage is listed.
3. Durchspiel Mit Kunde / Ausprobieren: own state seeded, mode started, trainer
   codes of several kinds entered (CODE_API routed), a training finished,
   settings changed, mode ended -> storage equals the start state except the
   mode's own bookkeeping keys."""
import asyncio
import json
import os
import re
import urllib.parse
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = os.environ.get("FWMC_PORT", "8845")
ROOT = f"http://localhost:{PORT}/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results, errors = [], []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}" + (f"  [{str(extra)[:400]}]" if not ok and extra != "" else ""))


REG = json.load(open(os.path.join(HERE, "speicher_register.json")))
ENTRIES = [(re.compile(e["re"]), e) for e in REG["entries"]]
SRC = open(os.path.join(HERE, "..", "app.js"), encoding="utf-8").read()


def entry_of(k):
    for rx, e in ENTRIES:
        if rx.search(k):
            return e
    return None


def static_checks():
    keys = sorted(set(re.findall(r"[\"'`](fwmc-[A-Za-z0-9_-]*)", SRC)) - set(REG["not_keys"]))
    missing = [k for k in keys if not entry_of(k)]
    check(f"every key in app.js is in the register ({len(keys)} keys)", not missing, missing)
    snap = re.compile(re.search(r"var HO_SNAP_RE = /(.+?)/;", SRC).group(1))
    excl = set(json.loads(re.search(r"const BACKUP_EXCLUDE = (\[[^\]]*\])", SRC).group(1)))
    wrong_cat = [k for k in keys if entry_of(k) and entry_of(k)["cat"] != "test"
                 and (entry_of(k)["cat"] == "restore") != bool(snap.search(k))]
    check("restore keys = HO_SNAP_RE (Kunden-/Test-Modus puts them back)", not wrong_cat, wrong_cat)
    wrong_bk = [k for k in keys if entry_of(k) and entry_of(k)["cat"] != "test"
                and (entry_of(k).get("backup", True) is False) != (k in excl)]
    check("backup:false keys = BACKUP_EXCLUDE", not wrong_bk, wrong_bk)


FREE = [{"id": "f1", "kind": "check", "title": "Eisbad", "note": "", "minutes": 5, "items": []}]
CODES = {
    "reg-vorlage": {"type": "free-template", "name": "Vorlagen", "trainings": [{"kind": "check", "title": "Journal"}]},
    "reg-neuro": {"type": "neuro-unlock", "name": "Neuro"},
    "reg-mv": {"type": "movement-plan", "name": "Plan", "movements": ["armL-heben", "armR-heben"], "bpm": 90,
               "durationMin": 1, "preview": 3, "mirror": True, "showLabel": True},
}
OWN = {
    "fwmc-tips-seen": "true",
    "fwmc-master-v1": json.dumps({"startCountdown": False, "volume": 0.7}),
    "fwmc-free-blocks-v1": json.dumps(FREE),
    "fwmc-name-v1": "Fabian",
    "fwmc-start-v1": json.dumps({"who": "allein", "goal": "fokus"}),
    "fwmc-plan-v1": json.dumps({"mine": 1}),
    "fwmc-history-v1": json.dumps([{"id": "h1", "ts": "2026-10-01T10:00:00.000Z", "kind": "free", "title": "Eisbad", "seconds": 60}]),
    "fwmc-remember-best-v1": json.dumps({"leicht": 4}),
    "fwmc-test-trainer-tools": "true",
    "fwmc-test-bottomnav": "true",
}
MODE_KEYS = re.compile(r"^fwmc-(client-session-v1|client-runs-v1|try-runs-v1|trainer-mode-v1|trainer-hidden-v1|trainer-seen-v1|trainer-asked-v1|import-parts-v1)$")


async def new_page(b):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, locale="de-DE", service_workers="block", has_touch=True)
    seed = "".join(f"localStorage.setItem({json.dumps(k)}, {json.dumps(v)});" for k, v in OWN.items())
    await ctx.add_init_script("try{if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');" + seed + "}}catch(e){}")

    async def api(route):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(route.request.url).query)
        code = (q.get("code") or [""])[0].lower()
        if code in CODES:
            await route.fulfill(status=200, content_type="application/json", body=json.dumps(CODES[code]))
        else:
            await route.fulfill(status=404, content_type="application/json", body='{"error":"not_found"}')
    await ctx.route("https://online-training.fwmc.workers.dev/**", api)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
    return ctx, pg


async def storage(pg):
    return await pg.evaluate("Object.fromEntries(Object.keys(localStorage).filter(k => k.startsWith('fwmc-')).map(k => [k, localStorage.getItem(k)]))")


async def set_mode(pg, m):
    if not await pg.is_visible("#trainerMenuSheet"):
        await pg.locator(".trainer-mode-btn:visible").first.click(); await pg.wait_for_timeout(150)
    await pg.click(f'#tmModes [data-tm="{m}"]'); await pg.wait_for_timeout(300)


async def enter_code(pg, code):
    await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(350)
    await pg.evaluate("(() => { const t = document.querySelector('#trainingHub .code-toggle'); if (t && t.getAttribute('aria-expanded') !== 'true') t.click(); })()")
    await pg.fill("#moreCodeInput", code); await pg.evaluate("document.getElementById('moreCodeGoBtn').click()")
    await pg.wait_for_timeout(600)


async def do_free(pg):
    await pg.goto(ROOT + "?bereich=free"); await pg.wait_for_timeout(350)
    await pg.click('#freeOwnGrid [data-free-id="f1"]'); await pg.wait_for_timeout(150)
    await pg.click("#freeStartBtn"); await pg.wait_for_timeout(250)
    await pg.click("#freeTickBtn"); await pg.wait_for_timeout(250)
    await pg.click("#freeDoneBackBtn"); await pg.wait_for_timeout(200)


def diff(a, b):
    out = []
    for k in sorted(set(a) | set(b)):
        if MODE_KEYS.match(k) or k.startswith("fwmc-test-") or k == "fwmc-device-id":
            continue
        if a.get(k) != b.get(k):
            out.append(f"{k}: {str(a.get(k))[:60]} -> {str(b.get(k))[:60]}")
    return out


async def durchspiel(b, mode):
    ctx, pg = await new_page(b)
    await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(500)
    before = await storage(pg)
    await set_mode(pg, mode)
    for c in CODES:
        await enter_code(pg, c)
    mid = await storage(pg)
    check(f"Durchspiel {mode}: the codes really took effect inside the mode",
          mid.get("fwmc-neuro-unlocked-v1") == "true" and "reg-vorlage" in (mid.get("fwmc-free-trainer-v1") or "")
          and "reg-mv" in (mid.get("fwmc-code-history-v1") or "").lower(), {k: mid.get(k) for k in ["fwmc-neuro-unlocked-v1", "fwmc-code-history-v1"]})
    await do_free(pg)
    await pg.evaluate("""localStorage.setItem('fwmc-mot-prefs-v1', JSON.stringify({speed: 9}));
      localStorage.setItem('fwmc-remember-best-v1', JSON.stringify({leicht: 9}));
      localStorage.setItem('fwmc-name-v1', 'Kunde Anna');
      localStorage.setItem('fwmc-start-v1', JSON.stringify({who: 'trainer', goal: 'ruhe'}));""")
    await pg.goto(ROOT + "?bereich=training"); await pg.wait_for_timeout(400)
    if mode == "client":
        await set_mode(pg, "own")
    else:
        await pg.click("#clientRunEndBtn")
    await pg.wait_for_timeout(1500)
    after = await storage(pg)
    d = diff(before, after)
    check(f"Durchspiel {mode}: storage after the mode equals the start state", not d, d)
    runs_key = "fwmc-client-runs-v1" if mode == "client" else "fwmc-try-runs-v1"
    check(f"Durchspiel {mode}: the run sits in its own store", len(json.loads(after.get(runs_key) or "[]")) >= 1, after.get(runs_key))
    await ctx.close()


async def main():
    static_checks()
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx, pg = await new_page(b)
        for area in ["heute", "training", "visual", "breath", "nat", "movement", "workout", "cardio", "free", "aktivierung", "fortschritt"]:
            await pg.goto(ROOT + "?bereich=" + area); await pg.wait_for_timeout(300)
        await pg.evaluate("(() => { const g = document.querySelector('.gear-btn:not([hidden]), #masterGearBtn'); if (g) g.click(); })()")
        await pg.wait_for_timeout(300)
        live = [k for k in (await storage(pg)) if not entry_of(k)]
        check("every key in live localStorage is in the register", not live, live)
        await ctx.close()
        await durchspiel(b, "client")
        await durchspiel(b, "try")
        await b.close()
    check("no page errors", not errors, errors[:5])
    print(f"\n{sum(1 for _, ok in results if ok)}/{len(results)} passed")


asyncio.run(main())
