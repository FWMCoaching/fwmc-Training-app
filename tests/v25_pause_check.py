import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width":390,"height":844})
        errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("http://localhost:8845/index.html#dig01"); await pg.wait_for_timeout(600)
        await pg.click("#tipsCloseBtn"); await pg.wait_for_timeout(150)
        await pg.click("#programStartBtn"); await pg.wait_for_timeout(500)
        await pg.click("#liveEndBtn"); await pg.wait_for_timeout(400)
        print("pause visible:", await pg.is_visible("#pauseScreen"), "errors:", errs)
        await b.close()
asyncio.run(main())
