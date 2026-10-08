import asyncio, json, os, time, urllib.parse
from playwright.async_api import async_playwright

# Trainer-Dashboard auf dem Server (kp20, 2026-10-08): with an admin token the
# planning data (Bausätze, plans, Stände, selected client) loads from the
# Worker's /admin/items on open (newer updated_at wins), every local save goes
# up (debounced), offline keeps everything local with a status line, and the
# first run with an empty server asks "Deine Dashboard-Daten auf den Server
# übernehmen?" (Ja/Später). A second device (fresh context) gets the same
# data; a delete on one device removes it on the other. The live Worker is
# never used: page.route stands in for it.
PORT = os.environ.get("FWMC_PORT", "8845")
DASH = f"http://localhost:{PORT}/dashboard.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots", "dashboard_server")
OFFLINE_TEXT = "Nur auf diesem Gerät gespeichert – wird übertragen, sobald der Server erreichbar ist"
results = []


def check(name, ok, extra=""):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}", extra if not ok else "")


async def ls(pg, key, default=None):
    v = await pg.evaluate("(k) => JSON.parse(localStorage.getItem(k) || 'null')", key)
    return default if v is None else v


async def wait_for(fn, timeout=4.0):
    end = time.time() + timeout
    while time.time() < end:
        if await fn():
            return True
        await asyncio.sleep(0.1)
    return False


async def main():
    errors = []
    os.makedirs(SHOTS, exist_ok=True)
    store = {}          # (kind, id) -> {"data":..., "updatedAt": ms}
    log = []            # (method, kind, id)
    state = {"offline": False}
    KINDS = ["bausaetze", "plans", "plan-versions", "current"]

    async def api(route):
        req = route.request; u = urllib.parse.urlparse(req.url)
        if req.headers.get("authorization") != "Bearer test":
            await route.fulfill(status=401, content_type="application/json", body='{"error":"unauthorized"}'); return
        if u.path.startswith("/admin/items"):
            if state["offline"]:
                await route.abort("internetdisconnected"); return
            parts = [urllib.parse.unquote(x) for x in u.path.split("/")[3:] if x]
            if not parts and req.method == "GET":
                kind = (urllib.parse.parse_qs(u.query).get("kind") or [""])[0]
                if kind and kind not in KINDS:
                    await route.fulfill(status=400, content_type="application/json", body='{"error":"bad_kind"}'); return
                items = [{"kind": k, "id": i, "data": v["data"], "updatedAt": v["updatedAt"]} for (k, i), v in store.items() if not kind or k == kind]
                log.append(("GET", kind, ""))
                await route.fulfill(status=200, content_type="application/json", body=json.dumps({"items": items})); return
            if len(parts) == 2 and parts[0] in KINDS:
                kind, iid = parts
                if req.method == "PUT":
                    body = json.loads(req.post_data)
                    ts = body.get("updatedAt") or int(time.time() * 1000)
                    store[(kind, iid)] = {"data": body["data"], "updatedAt": ts}
                    log.append(("PUT", kind, iid))
                    await route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "kind": kind, "id": iid, "updatedAt": ts})); return
                if req.method == "DELETE":
                    had = store.pop((kind, iid), None) is not None
                    log.append(("DELETE", kind, iid))
                    await route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "deleted": had})); return
            await route.fulfill(status=400, content_type="application/json", body='{"error":"bad_kind"}'); return
        if "/admin/programs" in u.path:
            await route.fulfill(status=200, content_type="application/json", body='{"programs":[]}'); return
        if "/admin/client-history" in u.path:
            await route.fulfill(status=200, content_type="application/json", body='{"entries":[]}'); return
        await route.fulfill(status=404, content_type="application/json", body="{}")

    def puts(kind, iid=None):
        return [x for x in log if x[0] == "PUT" and x[1] == kind and (iid is None or x[2] == iid)]

    def watch(pg, label):
        pg.on("pageerror", lambda e: errors.append(f"{label} pageerror: {e}"))
        pg.on("console", lambda m: errors.append(f"{label} console: {m.text}") if m.type == "error" and "Failed to load resource" not in m.text else None)

    now_iso = "2026-10-01T09:00:00.000Z"
    local_plan = {"kuerzel": "TS-07", "group": False, "name": "Grundlage", "code": "", "startDate": "2026-10-05",
                  "phases": [{"id": "ph1", "name": "Aufbau", "weeks": 4, "days": [[{"id": "e1", "area": "breath", "what": "", "code": "", "time": "", "minutes": 10}], [], [], [], [], [], []]}],
                  "comps": [], "issued": [], "updatedAt": now_iso}
    local_bs = {"id": "bs1", "kind": "kombi", "name": "Kopf wach", "note": "", "tags": ["Sportler"], "version": 1, "used": 0,
                "createdAt": now_iso, "updatedAt": now_iso, "data": {"items": [{"area": "nat", "what": "nat:remember", "minutes": 10}], "asOne": True, "code": ""}}
    seed_a = f"""if (!sessionStorage.getItem('seeded')) {{ sessionStorage.setItem('seeded','1');
      localStorage.setItem('fwmc-admin-token','test');
      localStorage.setItem('fwmc-dash-plans-v1', JSON.stringify({json.dumps({"TS-07": local_plan})}));
      localStorage.setItem('fwmc-dash-bausaetze-v1', JSON.stringify({json.dumps([local_bs])}));
      localStorage.setItem('fwmc-dash-current-v1', JSON.stringify('TS-07')); }}"""

    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])

        # ---- device A: local data from before, empty server -> first-run question ----
        ctxA = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctxA.route("https://online-training.fwmc.workers.dev/**", api)
        await ctxA.add_init_script(seed_a)
        pa = await ctxA.new_page(); watch(pa, "A")
        await pa.goto(DASH)
        asked = await wait_for(lambda: pa.is_visible("#plConfirmSheet"))
        check("first run with empty server asks to upload", asked and await pa.inner_text("#plConfirmTitle") == "Deine Dashboard-Daten auf den Server übernehmen?")
        check("question offers Ja / Später", (await pa.inner_text("#plConfirmYes")).strip() == "Ja" and (await pa.inner_text("#plConfirmNo")).strip() == "Später")
        check("Ja is not a red (danger) button here", "danger" not in (await pa.get_attribute("#plConfirmYes", "class") or ""))
        await pa.screenshot(path=os.path.join(SHOTS, "frage_390.png"))
        await pa.click("#plConfirmNo"); await pa.wait_for_timeout(1200)
        check("Später: nothing uploaded", not [x for x in log if x[0] == "PUT"], log)
        check("Später: status line says only on this device", "Nur auf diesem Gerät gespeichert" in await pa.inner_text("#plSyncLine") and await pa.is_visible("#plSyncNowBtn"))
        await pa.fill("#plNewKuerzel", "zz-1"); await pa.click("#plNewClientBtn"); await pa.wait_for_timeout(1300)
        check("Später: a local save is not pushed either", not [x for x in log if x[0] == "PUT"])
        await pa.click('#plClientSelect'); await pa.select_option("#plClientSelect", "ZZ-1")
        await pa.click("#plDeleteClientBtn"); await pa.click("#plConfirmYes"); await pa.wait_for_timeout(200)

        await pa.reload(); asked = await wait_for(lambda: pa.is_visible("#plConfirmSheet"))
        check("next open asks again", asked)
        await pa.click("#plConfirmYes")
        ok = await wait_for(lambda: pa.evaluate("document.querySelector('#plSyncLine').dataset.state === 'ok'"))
        check("Ja: plan, Bausatz and selection uploaded", ok and puts("plans", "TS-07") and puts("bausaetze", "bs1") and puts("current", "current"), log)
        check("uploaded plan is the local one (Kürzel only)", store[("plans", "TS-07")]["data"]["name"] == "Grundlage" and store[("plans", "TS-07")]["data"]["kuerzel"] == "TS-07")
        check("uploaded with the local time, not now", store[("plans", "TS-07")]["updatedAt"] == 1790845200000, store[("plans", "TS-07")]["updatedAt"])
        check("status line: saved on the server", "Auf dem Server gespeichert" in await pa.inner_text("#plSyncLine"))

        # ---- write-through ----
        n0 = len(log)
        await pa.fill("#plNewKuerzel", "ab-12"); await pa.click("#plNewClientBtn")
        ok = await wait_for(lambda: asyncio.sleep(0, bool(puts("plans", "AB-12"))))
        check("new client goes up by itself (write-through)", ok and store.get(("plans", "AB-12")), log[n0:])
        check("selected client goes up too", store[("current", "current")]["data"]["kuerzel"] == "AB-12")
        await pa.click("#plSaveVersionBtn")
        ok = await wait_for(lambda: asyncio.sleep(0, bool(puts("plan-versions", "AB-12"))))
        check("Stand speichern goes up as plan-versions", ok and len(store[("plan-versions", "AB-12")]["data"]) == 1)
        n1 = len(puts("plans", "AB-12"))
        await pa.fill("#plName", "Herbst"); await pa.press("#plName", "Tab")
        for _ in range(3):
            await pa.click("#plAddPhaseBtn"); await pa.wait_for_timeout(60)
        await pa.wait_for_timeout(1500)
        check("several quick edits = few uploads (debounced)", 1 <= len(puts("plans", "AB-12")) - n1 <= 2, len(puts("plans", "AB-12")) - n1)
        check("server has the latest edit", len(store[("plans", "AB-12")]["data"]["phases"]) == 3)

        # ---- device B: fresh browser, same token -> same data ----
        ctxB = await b.new_context(viewport={"width": 1440, "height": 1000}, service_workers="block")
        await ctxB.route("https://online-training.fwmc.workers.dev/**", api)
        await ctxB.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
        nB = len(log)
        pb = await ctxB.new_page(); watch(pb, "B")
        await pb.goto(DASH)
        ok = await wait_for(lambda: pb.evaluate("[...document.querySelectorAll('#plClientSelect option')].map(o => o.value).join(',') === 'AB-12,TS-07'"))
        check("second device loads the clients from the server", ok, await pb.evaluate("[...document.querySelectorAll('#plClientSelect option')].map(o => o.value)"))
        check("second device: no upload question", not await pb.is_visible("#plConfirmSheet"))
        check("second device: Bausatz is there", await pb.locator(".bs-card").count() == 1 and "Kopf wach" in await pb.inner_text("#bsList"))
        check("second device: selected client follows", await pb.input_value("#plClientSelect") == "AB-12")
        check("second device: plan details are the same", len((await ls(pb, "fwmc-dash-plans-v1", {}))["AB-12"]["phases"]) == 3)
        check("second device: Stände are there", len((await ls(pb, "fwmc-dash-plan-versions-v1", {})).get("AB-12", [])) == 1)
        await pb.wait_for_timeout(1000)
        check("second device: nothing pushed back that did not change", not [x for x in log[nB:] if x[0] == "PUT"], log[nB:])

        # edit on B, A sees it after reopening (B newer wins)
        await pb.select_option("#plClientSelect", "TS-07"); await pb.wait_for_timeout(100)
        await pb.fill("#plName", "Von Gerät B"); await pb.press("#plName", "Tab")
        ok = await wait_for(lambda: asyncio.sleep(0, store[("plans", "TS-07")]["data"].get("name") == "Von Gerät B"))
        check("edit on device B reaches the server", ok, store[("plans", "TS-07")]["data"].get("name"))
        await pa.reload(); await pa.wait_for_timeout(1500)
        check("device A takes the newer server version on open", (await ls(pa, "fwmc-dash-plans-v1", {}))["TS-07"]["name"] == "Von Gerät B")
        check("device A: no question once data is on the server", not await pa.is_visible("#plConfirmSheet"))

        # delete on A -> gone on B after reopening
        await pa.select_option("#plClientSelect", "AB-12"); await pa.wait_for_timeout(100)
        await pa.click("#plDeleteClientBtn")
        check("delete text mentions the server", "auch auf dem Server" in await pa.inner_text("#plConfirmText"))
        await pa.click("#plConfirmYes")
        ok = await wait_for(lambda: asyncio.sleep(0, ("plans", "AB-12") not in store and ("plan-versions", "AB-12") not in store))
        check("delete goes up (plan and its Stände)", ok, [x for x in log if x[0] == "DELETE"])
        await pb.reload(); await pb.wait_for_timeout(1500)
        check("deleted on A = gone on B", "AB-12" not in (await ls(pb, "fwmc-dash-plans-v1", {})))

        # ---- offline: stays local, status line, goes up when back ----
        state["offline"] = True
        await pb.fill("#plNewKuerzel", "of-1"); await pb.click("#plNewClientBtn")
        ok = await wait_for(lambda: pb.evaluate(f"document.querySelector('#plSyncText').textContent === {json.dumps(OFFLINE_TEXT)}"))
        check("offline: status line says it stays on this device", ok, await pb.inner_text("#plSyncLine"))
        check("offline: data is kept locally", "OF-1" in (await ls(pb, "fwmc-dash-plans-v1", {})))
        await pb.screenshot(path=os.path.join(SHOTS, "offline_1440.png"))
        await pb.reload(); await pb.wait_for_timeout(1200)
        check("offline open: local data shown, status line offline", "OF-1" in await pb.evaluate("[...document.querySelectorAll('#plClientSelect option')].map(o => o.value).join(',')")
              and OFFLINE_TEXT in await pb.inner_text("#plSyncLine"))
        state["offline"] = False
        await pb.evaluate("window.dispatchEvent(new Event('online'))")
        ok = await wait_for(lambda: asyncio.sleep(0, ("plans", "OF-1") in store), 5)
        check("back online: the offline change goes up", ok)
        ok = await wait_for(lambda: pb.evaluate("document.querySelector('#plSyncLine').dataset.state === 'ok'"))
        check("back online: status line ok again", ok)

        # ---- 390 px light and dark with the status line ----
        for scheme in ("light", "dark"):
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, color_scheme=scheme, service_workers="block")
            await ctx.route("https://online-training.fwmc.workers.dev/**", api)
            await ctx.add_init_script("localStorage.setItem('fwmc-admin-token','test')")
            pg = await ctx.new_page(); watch(pg, scheme)
            await pg.goto(DASH); await pg.wait_for_timeout(1200)
            check(f"{scheme}: status line visible", await pg.is_visible("#plSyncLine"))
            sw = await pg.evaluate("document.documentElement.scrollWidth")
            check(f"{scheme}: no sideways scroll at 390 px", sw <= 390, sw)
            await pg.locator("#plSyncLine").scroll_into_view_if_needed()
            await pg.screenshot(path=os.path.join(SHOTS, f"status_{scheme}_390.png"))
            # the "Später" state with its button
            await pg.evaluate("document.querySelector('#plSyncNowBtn').hidden = false")
            h = await pg.evaluate("document.querySelector('#plSyncNowBtn').getBoundingClientRect().height")
            check(f"{scheme}: 'Jetzt übernehmen' button >= 44 px", h >= 44, h)
            sw = await pg.evaluate("document.documentElement.scrollWidth")
            check(f"{scheme}: no sideways scroll with the button", sw <= 390, sw)
            await ctx.close()

        # ---- without token: no server calls, no status line ----
        n = len(log)
        ctxL = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctxL.route("https://online-training.fwmc.workers.dev/**", api)
        pl = await ctxL.new_page(); watch(pl, "local")
        await pl.goto(DASH); await pl.click("#gateLocalBtn"); await pl.wait_for_timeout(200)
        await pl.fill("#plNewKuerzel", "lo-1"); await pl.click("#plNewClientBtn"); await pl.wait_for_timeout(1300)
        check("local-only: nothing sent to the server", len(log) == n, log[n:])
        check("local-only: no status line", not await pl.is_visible("#plSyncLine"))

        # ---- token rejected while syncing -> back to the gate ----
        ctxX = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctxX.route("https://online-training.fwmc.workers.dev/**", api)
        await ctxX.add_init_script("if (!sessionStorage.getItem('s')) { sessionStorage.setItem('s','1'); localStorage.setItem('fwmc-admin-token','wrong'); }")
        px = await ctxX.new_page(); watch(px, "wrong")
        await px.goto(DASH); await px.wait_for_timeout(1000)
        check("wrong token: gate shown again", await px.is_visible("#gate"))

        await b.close()

    check("no page errors", not errors, errors[:5])
    failed = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("FAILED:", failed)


asyncio.run(main())
