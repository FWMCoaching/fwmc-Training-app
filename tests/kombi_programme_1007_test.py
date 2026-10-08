"""Kombi-Programm: gespeicherte Programme bearbeiten / als neues speichern,
fertige Programme (App, Trainer, eigene) einfügen und als Kopie anpassen,
Liste nach zuletzt benutzt mit 5 + "Alle anzeigen" (Fabian 07.10.2026,
"Erst Vorschau"). Run from tests/ with a dev server on :8845."""
import asyncio, json
from playwright.async_api import async_playwright

URL = "http://localhost:8845/index.html?bereich=breath"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
INIT = ("localStorage.setItem('fwmc-tips-seen','true');"
        "localStorage.setItem('fwmc-master-v1', JSON.stringify({startCountdown:false}));")
SAVED = "fwmc-combo-saved-v1"

results = []
def check(name, ok, extra=""):
    results.append(bool(ok))
    print(f"{name}: {bool(ok)}" + (f"  ({extra})" if extra else ""))


async def saved(pg):
    return await pg.evaluate(f"() => JSON.parse(localStorage.getItem('{SAVED}') || '[]')")


async def open_combo(pg):
    await pg.goto(URL); await pg.wait_for_timeout(400)
    await pg.click('#breathHome .combo-entry-link'); await pg.wait_for_timeout(250)


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        await ctx.add_init_script(INIT)
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---- 1. Anpassen: built-in Feierabend-Reset as own copy ----
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.click('#breathFeaturedGrid .featured-card'); await pg.wait_for_timeout(300)
        link = '#breathProgramIntro .combo-adapt-link'
        check("intro shows 'Als Kombi-Programm anpassen'", await pg.is_visible(link))
        await pg.click(link); await pg.wait_for_timeout(300)
        check("opens the Kombi screen", await pg.is_visible("#comboScreen"))
        rows = await pg.locator("#comboBlockList .chapter-row").count()
        txt = await pg.inner_text("#comboBlockList")
        check("copy has both breath blocks", rows == 2 and "Box-Atmung" in txt, f"{rows} {txt[:60]!r}")
        check("note says it is a copy", "Kopie von" in await pg.inner_text("#comboEditNote"))
        await pg.click("#comboSaveBtn"); await pg.wait_for_timeout(100)
        check("name prefilled '(eigene)'", await pg.input_value("#comboNameInput") == "Feierabend-Reset (eigene)")
        check("no 'Als neues' for a fresh copy", not await pg.is_visible("#comboSaveAsNewBtn"))
        await pg.click("#comboSaveConfirmBtn"); await pg.wait_for_timeout(200)
        s = await saved(pg)
        check("saved as own programme", len(s) == 1 and s[0]["name"] == "Feierabend-Reset (eigene)" and len(s[0]["blocks"]) == 2)
        check("breath blocks converted to Kombi blocks", all(x.get("domain") == "breath" for x in s[0]["blocks"]))

        # ---- 2. Bearbeiten + Speichern ersetzt ----
        await pg.click("#comboSavedList .combo-saved-edit"); await pg.wait_for_timeout(200)
        check("edit loads the blocks", await pg.locator("#comboBlockList .chapter-row").count() == 2)
        check("note: Du bearbeitest", "Du bearbeitest" in await pg.inner_text("#comboEditNote"))
        check("save button reads 'Änderungen speichern'", (await pg.inner_text("#comboSaveBtn")).strip() == "Änderungen speichern")
        await pg.click("#comboBlockList .chapter-row .combo-block-remove >> nth=-1"); await pg.wait_for_timeout(100)
        await pg.click("#comboSaveBtn"); await pg.wait_for_timeout(100)
        check("name kept when editing", await pg.input_value("#comboNameInput") == "Feierabend-Reset (eigene)")
        check("'Als neues Programm speichern' offered", await pg.is_visible("#comboSaveAsNewBtn"))
        await pg.screenshot(path="screenshots/kombi_programme_edit_save.png")
        await pg.click("#comboSaveConfirmBtn"); await pg.wait_for_timeout(200)
        s = await saved(pg)
        check("Speichern replaced it (1 entry, 1 block)", len(s) == 1 and len(s[0]["blocks"]) == 1, json.dumps([len(x["blocks"]) for x in s]))
        check("edit mode ended", await pg.is_hidden("#comboEditNote"))

        # ---- 3. Als neues Programm speichern keeps the original ----
        await pg.click("#comboSavedList .combo-saved-edit"); await pg.wait_for_timeout(200)
        await pg.click("#comboInsertGroup summary"); await pg.wait_for_timeout(200)
        await pg.click('#comboInsertList .bundle-item >> text="Ganzkörper-Einstieg"'); await pg.wait_for_timeout(200)
        check("insert adds the 4 workout blocks", await pg.locator("#comboBlockList .chapter-row").count() == 5)
        check("inserted blocks show their origin", await pg.locator('#comboBlockList .combo-from >> text="aus Ganzkörper-Einstieg"').count() == 4)
        await pg.click("#comboSaveBtn"); await pg.wait_for_timeout(100)
        await pg.fill("#comboNameInput", "Abend lang")
        await pg.click("#comboSaveAsNewBtn"); await pg.wait_for_timeout(200)
        s = await saved(pg)
        names = {x["name"]: len(x["blocks"]) for x in s}
        check("new programme saved, original untouched", names == {"Feierabend-Reset (eigene)": 1, "Abend lang": 5}, json.dumps(names))
        check("newest saved first in the list", (await pg.inner_text("#comboSavedList .bundle-item >> nth=0")).startswith("Abend lang"))

        # ---- 4. Insert groups + VT programme conversion ----
        await pg.click("#comboInsertGroup summary"); await pg.wait_for_timeout(200)
        ins = await pg.inner_text("#comboInsertList")
        check("insert lists own + app programmes", "Deine Programme" in ins and "In der App" in ins and "Feierabend-Reset" in ins)
        check("no trainer group without trainer codes", "Von deinem Trainer" not in ins)
        await pg.click('#comboInsertList .bundle-item >> text="Einstieg · Tempo-Steigerung"'); await pg.wait_for_timeout(200)
        draft = await pg.evaluate("() => [...document.querySelectorAll('#comboBlockList .combo-pause-slider')].map(s => s.value)")
        check("VT programme pause carried as 'Pause danach' (15 s)", draft[:1] == ["15"], str(draft))
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(600)
        check("converted VT block plays in the VT player", await pg.is_visible("#player"))
        await pg.click("#backBtn") if await pg.locator("#backBtn").count() else None
        await pg.wait_for_timeout(300)

        # ---- 5. Trainer programmes (cached on this device) ----
        trainer = {"T1": {"at": "2026-10-07T10:00:00Z", "def": {"type": "breath-bundle", "name": "Von Anna", "programs": [{"label": "Atem morgens", "blocks": [{"pattern": "box", "durationMin": 2}]}]}}}
        await pg.evaluate("(t) => localStorage.setItem('fwmc-trainer-programs-v1', JSON.stringify(t))", trainer)
        await open_combo(pg)
        await pg.click("#comboInsertGroup summary"); await pg.wait_for_timeout(200)
        ins = await pg.inner_text("#comboInsertList")
        check("trainer group lists bundle programmes", "Von deinem Trainer" in ins and "Atem morgens" in ins)
        await pg.click('#comboInsertList .bundle-item >> text="Atem morgens"'); await pg.wait_for_timeout(200)
        check("trainer programme inserted as Baustein", "Box-Atmung" in await pg.inner_text("#comboBlockList"))
        await pg.click("#comboStartBtn"); await pg.wait_for_timeout(600)
        check("converted breath block plays", await pg.is_visible("#breathPlayer"))

        # ---- 6. Sort by last use, 5 shown + Alle anzeigen ----
        many = [{"id": str(i), "name": f"P{i}", "blocks": [{"domain": "breath", "pattern": "box", "durationMin": 1}],
                 "createdAt": f"2026-10-0{i}T08:00:00Z", "lastUsed": f"2026-10-0{i}T08:00:00Z"} for i in range(1, 8)]
        await pg.evaluate("(m) => localStorage.setItem('fwmc-combo-saved-v1', JSON.stringify(m))", many)
        await open_combo(pg)
        n = await pg.locator("#comboSavedList .bundle-item").count()
        first = (await pg.inner_text("#comboSavedList .bundle-item >> nth=0")).split("\n")[0]
        check("5 shown, newest use first", n == 5 and first == "P7", f"{n} {first}")
        check("'Alle anzeigen (7)'", (await pg.inner_text("#comboSavedMoreBtn")).strip() == "Alle anzeigen (7)")
        await pg.click("#comboSavedMoreBtn"); await pg.wait_for_timeout(100)
        check("all 7 after tap", await pg.locator("#comboSavedList .bundle-item").count() == 7)
        await pg.screenshot(path="screenshots/kombi_programme_list.png", full_page=True)

        # ✕ deletes at once (like every saved list; swiping asks first)
        await pg.click("#comboSavedList .bundle-item-wrap >> nth=0 >> .combo-block-remove"); await pg.wait_for_timeout(150)
        check("✕ deletes the programme", len(await saved(pg)) == 6)

        # tap targets
        small = await pg.evaluate("() => [...document.querySelectorAll('#comboSavedList button')].filter(b => b.offsetParent && (b.getBoundingClientRect().height < 44 || b.getBoundingClientRect().width < 44)).length")
        check("saved-list buttons ≥ 44 px", small == 0, str(small))

        await b.close()
    check("no pageerror/console error", not errors, "; ".join(errors[:3]))
    print("ALL PASS" if all(results) else "SOME FAILED")

asyncio.run(main())
