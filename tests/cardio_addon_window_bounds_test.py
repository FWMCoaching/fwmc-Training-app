import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Cardio "+ Zusatzaufgabe" Zeitfenster-Slider (ab/bis) durften bisher bis zu
# 60 Min. weit geschoben werden, unabhaengig davon, wie viel Zeit die vom
# Klienten tatsaechlich zusammengestellte Cardio-Einheit (Aktivitaeten +
# Pausen dazwischen) uebersteigt - z.B. bis "25 Min." trotz nur 10 Min.
# Joggen. syncCardioAddonWindowBounds() deckelt das max-Attribut beider
# Slider jetzt live auf cardioItemsSeconds(cardioPrefs.items) und klemmt
# einen jetzt zu grossen gespeicherten Wert zurueck; kommt danach mehr Zeit
# dazu, wächst die Reichweite wieder mit.

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click('.section-tab[data-section="cardio"]'); await pg.wait_for_timeout(200)
        await pg.click("#cardioStartCard"); await pg.wait_for_timeout(200)
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(100)

        await pg.click("#cardioAddonAdvanced summary"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonEnableToggle"); await pg.wait_for_timeout(150)
        await pg.check("#cardioAddonWindowToggle"); await pg.wait_for_timeout(150)

        # ---- one activity, 10 Min. (cardioPrefs.defaultDurationS), no pause
        # yet (only one item) - both sliders capped at 10 ----
        print("window-end slider max capped at the 10 Min. Joggen total:",
              await pg.get_attribute("#cardioAddonWindowEndSlider", "max") == "10")
        print("window-start slider max capped the same way:",
              await pg.get_attribute("#cardioAddonWindowStartSlider", "max") == "10")

        # ---- dragging past the plan's total is impossible: the browser's
        # own range-input clamping holds it at the max the moment it's set ----
        await pg.eval_on_selector("#cardioAddonWindowEndSlider",
            "el => { el.value = 25; el.dispatchEvent(new Event('input', {bubbles:true})); }")
        await pg.wait_for_timeout(100)
        print("dragging past the plan total clamps back to 10 Min. instead:",
              (await pg.inner_text("#cardioAddonWindowEndValue")) == "10 Min.")

        # ---- adding a second activity grows the total (10 + 10 + the
        # interleaved default pause) - the ceiling grows with it, so the
        # client "kann dann weiterziehen" as soon as there's more time ----
        await pg.click('#cardioAddGrid >> text="Rad fahren"'); await pg.wait_for_timeout(150)
        max_after_add = await pg.get_attribute("#cardioAddonWindowEndSlider", "max")
        print("adding a second activity raises the max above 10 Min.:", int(max_after_add) > 10)
        print("start slider's max grows identically:",
              await pg.get_attribute("#cardioAddonWindowStartSlider", "max") == max_after_add)

        await pg.eval_on_selector("#cardioAddonWindowEndSlider",
            f"el => {{ el.value = {max_after_add}; el.dispatchEvent(new Event('input', {{bubbles:true}})); }}")
        await pg.wait_for_timeout(100)
        print(f"can now actually drag out to the new max ({max_after_add} Min.):",
              (await pg.inner_text("#cardioAddonWindowEndValue")) == f"{max_after_add} Min.")

        # ---- removing the second activity again shrinks the total back down
        # - a stored value now above the shrunk plan must clamp down with it,
        # never left stranded pointing past the end of the actual session ----
        await pg.click('.combo-block-remove[data-i="1"]'); await pg.wait_for_timeout(150)
        print("removing it again shrinks the max back down to 10:",
              await pg.get_attribute("#cardioAddonWindowEndSlider", "max") == "10")
        print("the stored 'bis'-value clamps down with it instead of staying stranded:",
              (await pg.inner_text("#cardioAddonWindowEndValue")) == "10 Min.")

        await b.close()
    print("FINAL ERRORS:", errors)

asyncio.run(main())
