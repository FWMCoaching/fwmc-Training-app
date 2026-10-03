"""Start page "Heute": greeting, Weitermachen card, week strip, calendar
(month / next month / quarter / year), day view (list + hour grid, no
overlaps), plan editor with phases, extra entries, done/skip, persistence,
?bereich= start parameter, area tiles, code line staying on Heute."""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8845/index.html"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
results = []


def check(name, ok):
    results.append((name, bool(ok)))
    print(f"{name}: {bool(ok)}")


async def visible(pg, sel):
    return await pg.locator(sel).first.is_visible()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844})
        pg = await ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "404" not in m.text else None)
        await pg.route("**/online-training.fwmc.workers.dev/**", lambda r: r.fulfill(status=404, body="{}"))
        await pg.add_init_script("try{localStorage.setItem('fwmc-tips-seen','true')}catch(e){}")
        await pg.goto(BASE)
        await pg.wait_for_timeout(500)

        # --- opens on Heute ---
        check("opens on todayHome", await visible(pg, "#todayHome"))
        check("visual home hidden", not await visible(pg, "#home"))
        active = await pg.locator("#todayHome .section-tab.active").inner_text()
        check("Heute tab active", "Heute" in active)
        first_tab = await pg.locator("#todayHome .section-tab").first.inner_text()
        check("Heute is first tab", "Heute" in first_tab)
        g = await pg.locator("#todayGreeting").inner_text()
        check("greeting by time of day", any(w in g for w in ["Guten Morgen", "Guten Tag", "Guten Abend", "Gute Nacht", "Hallo"]))
        check("date shown", len((await pg.locator("#todayDate").inner_text()).strip()) > 5)
        main_txt = await pg.locator("#todayMain").inner_text()
        check("Weitermachen card with hint", "Trainer" in main_txt)
        check("6 area tiles", await pg.locator("#todayAreaGrid .area-tile").count() == 6)
        check("7 days in strip", await pg.locator("#todayWeekStrip .week-day").count() == 7)
        check("no plan yet: empty day text", "Noch kein Plan" in await pg.locator("#dayPanelBody").inner_text())

        # --- area tile navigates ---
        await pg.locator('#todayAreaGrid .area-tile[data-area="breath"]').click()
        await pg.wait_for_timeout(200)
        check("breath tile opens breathHome", await visible(pg, "#breathHome"))
        await pg.locator('#breathHome .section-tab[data-section="today"]').click()
        await pg.wait_for_timeout(200)
        check("Heute tab back to todayHome", await visible(pg, "#todayHome"))

        # --- code line: wrong code stays on Heute ---
        await pg.fill("#todayCodeInput", "gibtsnicht-xyz")
        await pg.click("#todayCodeGoBtn")
        await pg.wait_for_timeout(800)
        check("wrong code error on Heute", await visible(pg, "#todayCodeError") and await visible(pg, "#todayHome"))

        # --- plan editor: add today's weekday entry with time ---
        await pg.click("#todayPlanBtn")
        await pg.wait_for_timeout(200)
        check("plan screen opens", await visible(pg, "#planScreen"))
        check("one phase created", await pg.locator(".plan-phase").count() == 1)
        wd = await pg.evaluate("(new Date().getDay()+6)%7")
        await pg.locator(f'[data-add="0:{wd}"]').click()
        await pg.wait_for_timeout(150)
        check("entry sheet opens", await visible(pg, "#planEntrySheet"))
        await pg.select_option("#planEntryArea", "breath")
        await pg.fill("#planEntryTime", "07:30")
        await pg.select_option("#planEntryMinutes", "10")
        await pg.click("#planEntrySaveBtn")
        await pg.wait_for_timeout(150)
        check("entry listed in plan", await pg.locator(".plan-item").count() == 1)
        # second entry same day, overlapping time
        await pg.locator(f'[data-add="0:{wd}"]').click()
        await pg.select_option("#planEntryArea", "movement")
        await pg.fill("#planEntryTime", "07:35")
        await pg.select_option("#planEntryMinutes", "10")
        await pg.click("#planEntrySaveBtn")
        await pg.wait_for_timeout(150)
        # a third entry later
        await pg.locator(f'[data-add="0:{wd}"]').click()
        await pg.select_option("#planEntryArea", "workout")
        await pg.fill("#planEntryTime", "12:00")
        await pg.select_option("#planEntryMinutes", "30")
        await pg.click("#planEntrySaveBtn")
        await pg.wait_for_timeout(150)
        check("3 entries", await pg.locator(".plan-item").count() == 3)
        # add a second phase, check weeks select present
        await pg.click("#planAddPhaseBtn")
        await pg.wait_for_timeout(150)
        check("second phase added", await pg.locator(".plan-phase").count() == 2)
        # page must not scroll horizontally
        sw = await pg.evaluate("document.documentElement.scrollWidth")
        check("plan screen no horizontal scroll", sw <= 390)
        await pg.click("#planBackBtn")
        await pg.wait_for_timeout(200)

        # --- Heute with plan ---
        check("back on Heute", await visible(pg, "#todayHome"))
        prog = await pg.locator("#todayProgress").inner_text()
        check("progress line", "geplant" in prog)
        check("main card shows today's training", "heutiges training" in (await pg.locator("#todayMain").inner_text()).lower())
        check("day list shows 3 items", await pg.locator("#dayPanelBody .day-item").count() == 3)
        check("gap placeholder between items", await pg.locator("#dayPanelBody .day-gap").count() >= 1)

        # hours view: overlapping entries must not overlap visually
        await pg.click('.day-view-btn[data-day-view="hours"]')
        await pg.wait_for_timeout(150)
        boxes = await pg.evaluate("""[...document.querySelectorAll('#dayPanelBody .day-item')].map(e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom]})""")
        def ov(a, c):
            return a[0] < c[2] - 1 and c[0] < a[2] - 1 and a[1] < c[3] - 1 and c[1] < a[3] - 1
        overl = any(ov(boxes[i], boxes[j]) for i in range(len(boxes)) for j in range(i + 1, len(boxes)))
        check("hour grid: 3 blocks", len(boxes) == 3)
        check("hour grid: no overlapping blocks", not overl)
        clipped = await pg.evaluate("""[...document.querySelectorAll('#dayPanelBody .day-item')].some(it=>{const r=it.getBoundingClientRect();return [...it.querySelectorAll('button')].some(b=>{const q=b.getBoundingClientRect();return q.right>r.right+1||q.bottom>r.bottom+1})})""")
        check("hour grid: buttons inside blocks", not clipped)
        await pg.click('.day-view-btn[data-day-view="list"]')
        await pg.wait_for_timeout(150)

        # done / skip
        first = pg.locator("#dayPanelBody .day-item").first
        await first.locator('[data-act="done"]').click()
        await pg.wait_for_timeout(150)
        check("abhaken marks done", await pg.locator("#dayPanelBody .day-item.done").count() >= 1)
        await pg.locator("#dayPanelBody .day-item").nth(2).locator('[data-act="skip"]').click()
        await pg.wait_for_timeout(150)
        check("auslassen removes item for today", await pg.locator("#dayPanelBody .day-item").count() == 2)

        # extra entry only for this day
        await pg.click("#dayAddBtn")
        await pg.select_option("#planEntryArea", "cardio")
        await pg.fill("#planEntryTime", "18:00")
        await pg.click("#planEntrySaveBtn")
        await pg.wait_for_timeout(150)
        check("extra entry added", await pg.locator("#dayPanelBody .day-item").count() == 3)

        # --- calendar toggles ---
        await pg.click("#calMonthBtn")
        await pg.wait_for_timeout(150)
        check("month opens", await pg.locator("#calExpand .cal-month").count() == 1)
        check("next-month toggle visible", await visible(pg, "#calNextMonthBtn"))
        await pg.click("#calNextMonthBtn")
        await pg.wait_for_timeout(150)
        check("next month added", await pg.locator("#calExpand .cal-month").count() == 2)
        await pg.click("#calQuarterBtn")
        await pg.wait_for_timeout(150)
        check("quarter: many months in scroller", await pg.locator("#calQuarterScroller .cal-month").count() >= 3)
        check("quarter hint", "iPad" in await pg.locator("#calExpand").inner_text())
        await pg.click("#calYearBtn")
        await pg.wait_for_timeout(150)
        check("year: 12 mini months", await pg.locator("#calExpand .cal-month.mini").count() == 12)
        sw = await pg.evaluate("document.documentElement.scrollWidth")
        check("year view no horizontal page scroll", sw <= 390)
        # tapping a day in the calendar selects it
        await pg.click("#calMonthBtn")
        await pg.wait_for_timeout(150)
        cells = pg.locator("#calExpand .cal-cell[data-date]")
        target = await cells.nth(0).get_attribute("data-date")
        await cells.nth(0).click()
        await pg.wait_for_timeout(150)
        check("calendar tap selects day", await pg.locator(f'#calExpand .cal-cell.selected[data-date="{target}"]').count() == 1)

        # week navigation
        before = await pg.locator("#todayWeekStrip .week-day").first.get_attribute("data-date")
        await pg.click("#todayWeekNext")
        await pg.wait_for_timeout(150)
        after = await pg.locator("#todayWeekStrip .week-day").first.get_attribute("data-date")
        check("week next moves strip", before != after)

        # --- persistence ---
        await pg.reload()
        await pg.wait_for_timeout(500)
        check("after reload on Heute", await visible(pg, "#todayHome"))
        check("plan persisted (3 items today)", await pg.locator("#dayPanelBody .day-item").count() == 3)
        check("done persisted", await pg.locator("#dayPanelBody .day-item.done").count() >= 1)

        # --- ?bereich parameter ---
        await pg.goto(BASE + "?bereich=nat")
        await pg.wait_for_timeout(400)
        check("?bereich=nat opens NAT", await visible(pg, "#natHome"))
        await pg.goto(BASE + "?bereich=test")
        await pg.wait_for_timeout(400)
        check("?bereich=test locked falls back to visual", await visible(pg, "#home"))
        await pg.goto(BASE + "?bereich=quatsch")
        await pg.wait_for_timeout(400)
        check("unknown bereich opens Heute", await visible(pg, "#todayHome"))

        # --- iPad width: nav fits ---
        await pg.set_viewport_size({"width": 820, "height": 1180})
        await pg.wait_for_timeout(200)
        sw = await pg.evaluate("document.documentElement.scrollWidth")
        check("iPad no horizontal scroll", sw <= 820)

        check("no page errors", not errors)
        if errors:
            print(errors[:5])
        await b.close()
    bad = [n for n, ok in results if not ok]
    print("FAILED:", bad if bad else "none")


asyncio.run(main())
