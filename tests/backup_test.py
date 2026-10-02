import asyncio, json, os
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html"

# Datensicherung: export all fwmc- keys to a file, import writes only the
# keys in the file, skips junk, rejects a newer version, keeps other keys.

HERE = os.path.dirname(os.path.abspath(__file__))
F_MIXED = os.path.join(HERE, "_backup_mixed.json")
F_FUTURE = os.path.join(HERE, "_backup_future.json")

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block", accept_downloads=True)
        await ctx.add_init_script("""if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded','1');
          localStorage.setItem('fwmc-tips-seen','true');
          localStorage.setItem('fwmc-cardio-v1', JSON.stringify({items:[{activity:'joggen',durationS:600,label:'Warm-up',interval:null}],defaultDurationS:600}));
          localStorage.setItem('fwmc-keep-me-v1', JSON.stringify({x:1}));
          localStorage.setItem('other-app', 'x'); }""")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        await pg.goto(URL); await pg.wait_for_timeout(300)
        await pg.click("#home .master-settings-btn"); await pg.wait_for_timeout(150)
        print("ui: backup group visible:", await pg.is_visible("#masterBackupGroup"))

        async with pg.expect_download() as dl:
            await pg.click("#masterBackupExportBtn")
        d = await dl.value
        path = await d.path()
        data = json.load(open(path))
        print("export: filename:", d.suggested_filename.startswith("fwmc-sicherung-") and d.suggested_filename.endswith(".json"), d.suggested_filename)
        print("export: header:", data["app"] == "fwmc-training" and data["version"] == 1)
        print("export: contains cardio:", "Warm-up" in data["data"].get("fwmc-cardio-v1", ""))
        print("export: only fwmc keys:", all(k.startswith("fwmc-") for k in data["data"]) and "other-app" not in data["data"])

        # mixed file: old-ish cardio shape, unknown fwmc key, foreign key, invalid JSON
        json.dump({"app": "fwmc-training", "version": 1, "data": {
            "fwmc-cardio-v1": json.dumps({"items": [{"activity": "walking", "durationS": 900}]}),
            "fwmc-unknown-future-v9": json.dumps({"a": 1}),
            "other-app": "\"x2\"",
            "fwmc-broken-v1": "{nope",
        }}, open(F_MIXED, "w"))
        await pg.set_input_files("#masterBackupFile", F_MIXED); await pg.wait_for_timeout(200)
        print("import: asks first:", await pg.is_visible("#confirmSheet"))
        await pg.click("#confirmYesBtn"); await pg.wait_for_timeout(200)
        print("import: reports skipped:", "2 übersprungen" in await pg.inner_text("#masterBackupMsg"), await pg.inner_text("#masterBackupMsg"))
        await pg.wait_for_load_state("load"); await pg.wait_for_timeout(1200)
        st = await pg.evaluate("""() => ({cardio: localStorage.getItem('fwmc-cardio-v1'), keep: localStorage.getItem('fwmc-keep-me-v1'),
            other: localStorage.getItem('other-app'), broken: localStorage.getItem('fwmc-broken-v1')})""")
        print("import: value applied:", "walking" in (st["cardio"] or ""))
        print("import: missing keys untouched:", st["keep"] == json.dumps({"x": 1}, separators=(",", ":")), st["keep"])
        print("import: junk skipped:", st["other"] == "x" and st["broken"] is None)
        await pg.click('#home .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(150)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        print("import: app loads imported plan:", "Walking" in await pg.inner_text("#cardioList"))

        json.dump({"app": "fwmc-training", "version": 99, "data": {"fwmc-cardio-v1": "{}"}}, open(F_FUTURE, "w"))
        await pg.click("#cardioReady .master-settings-btn") if await pg.locator("#cardioReady .master-settings-btn").count() else await pg.evaluate("document.querySelector('.master-settings-btn').click()")
        await pg.wait_for_timeout(150)
        await pg.set_input_files("#masterBackupFile", F_FUTURE); await pg.wait_for_timeout(200)
        print("future: rejected without asking:", await pg.is_hidden("#confirmSheet") and "neueren" in await pg.inner_text("#masterBackupMsg"))
        print("future: nothing changed:", "walking" in (await pg.evaluate("localStorage.getItem('fwmc-cardio-v1')") or ""))

        print("no page errors:", errors == [], errors[:3])
        await b.close()
    for f in (F_MIXED, F_FUTURE):
        if os.path.exists(f): os.remove(f)

asyncio.run(main())
