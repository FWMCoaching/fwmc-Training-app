import asyncio
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

SPEEDUP = """
  const orig = window.setTimeout;
  window.setTimeout = (fn, delay, ...args) => orig(fn, Math.min(delay, 250), ...args);
"""

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
        pg = await ctx.new_page()
        await ctx.add_init_script(SPEEDUP)
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        await pg.goto(URL); await pg.wait_for_timeout(300)
        if await pg.is_visible("#tipsCloseBtn"):
            await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)

        await pg.click('[data-open-combo="1"]'); await pg.wait_for_timeout(200)
        print("combo screen visible:", await pg.is_visible("#comboScreen"))

        nat_group_title = await pg.inner_text(".combo-domain-group:has-text('NAT') .combo-domain-title")
        print("NAT domain group title:", nat_group_title)
        nat_btns = pg.locator(".combo-domain-group:has(.combo-domain-title:text-is('NAT')) .combo-add-btn")
        print("NAT preset count:", await nat_btns.count())
        print("NAT preset 1 label:", await nat_btns.nth(0).inner_text())
        print("NAT preset 2 label:", await nat_btns.nth(1).inner_text())

        # Remember is now capture-mode (see the Kombi-Baukasten rebuild note
        # in CLAUDE.md) - the add-grid button reopens Remember's own ready
        # screen instead of adding a block instantly; commit via its own
        # start button, now repurposed to "Baustein übernehmen".
        await nat_btns.nth(0).click(); await pg.wait_for_timeout(200)
        print("capture opens rememberReady:", await pg.is_visible("#rememberReady"))
        await pg.click("#rememberReadyStartBtn"); await pg.wait_for_timeout(150)
        print("block count text:", await pg.inner_text("#comboBlockCount"))
        block_row_text = await pg.inner_text("#comboBlockList")
        print("block list mentions Remember:", "Positionen merken" in block_row_text)

        # SPEEDUP caps the block's 60 s timer at 250 ms, so a fixed 300 ms
        # sleep raced the block's end - wait for the player instead.
        await pg.click("#comboStartBtn")
        try:
            await pg.wait_for_selector("#rememberPlayer", state="visible", timeout=1500); rp_vis = True
        except Exception:
            rp_vis = False
        print("remember player visible:", rp_vis)
        print("remember nav hidden (fixed mode, not training):", await pg.is_hidden("#rememberNav"))

        # sped-up combo-duration timer should fire soon and, since this is the
        # only block, finish the whole combo automatically
        await pg.wait_for_timeout(2500)
        print("combo done panel visible:", await pg.is_visible("#comboDonePanel"))
        print("combo done summary:", await pg.inner_text("#comboDoneSummary") if await pg.locator("#comboDonePanel").count() else "(n/a)")

        await b.close()
    print("ERRORS:", errors)

asyncio.run(main())
