import asyncio, base64, os
from playwright.async_api import async_playwright
URL = "http://localhost:8845/index.html?bereich=visual"

# Cardio: background colour, per-activity motivation (quote/image/gallery),
# and the inline Zusatzreiz that flashes letters/digits only where nothing
# is drawn (never on a glyph of the quote, the image, timer, bars).

PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cardio_test_img.png")

async def new_page(b, errors, seed=""):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, service_workers="block")
    await ctx.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-workout-sound-v1', JSON.stringify({enabled:false}));" + seed)
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
    pg.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
    await pg.goto(URL); await pg.wait_for_timeout(300)
    return pg

async def open_cardio(pg):
    await pg.click('#home .section-tab[data-section="cardio"]'); await pg.wait_for_timeout(150)
    await pg.click("#cardioStartCard"); await pg.wait_for_timeout(150)

OVERLAP_JS = """() => {
  const ch = document.querySelector('#cardioFlashLayer .cardio-flash-char');
  if (!ch || ch.style.visibility === 'hidden') return null;
  const c = ch.getBoundingClientRect();
  const hit = (r) => c.left < r.right && c.right > r.left && c.top < r.bottom && c.bottom > r.top;
  const range = document.createRange();
  const p = document.getElementById('cardioMotivText');
  const node = p.firstChild;
  for (let i = 0; node && i < node.length; i++) {
    if (/\\s/.test(node.data[i])) continue;
    range.setStart(node, i); range.setEnd(node, i + 1);
    for (const r of range.getClientRects()) if (hit(r)) return 'glyph';
  }
  for (const id of ['cardioCountdown','cardioActivityTitle','cardioBlockProgress','cardioMotivImg']) {
    const el = document.getElementById(id);
    if (el && !el.hidden && hit(el.getBoundingClientRect())) return id;
  }
  for (const b of document.querySelectorAll('#cardioPlayerBar button, #cardioPlayer .chapter-nav'))
    if (hit(b.getBoundingClientRect())) return 'bar';
  return 'ok';
}"""

async def main():
    # small solid PNG for the image upload
    open(PNG, "wb").write(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAgAAAAICAIAAABLbSncAAAAEklEQVR4nGP4z8CAFWEXHbQSACj/P8Fu7N9hAAAAAElFTkSuQmCC"))
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome", args=["--no-sandbox"])

        pg = await new_page(b, errors)
        await open_cardio(pg)
        await pg.click("#cardioLookAdvanced summary"); await pg.wait_for_timeout(100)
        print("bg: swatches present:", await pg.locator("#cardioBgColorPicker .color-swatch").count() > 5)
        await pg.click('#cardioBgColorPicker .color-swatch[data-key="blau"]'); await pg.wait_for_timeout(100)
        print("bg: intensity jumps to 50%:", "50" in await pg.inner_text("#cardioBgIntensityValue"))

        # gallery: a quote and an image
        await pg.fill("#cardioGalleryTextInput", "Weiter so")
        await pg.click("#cardioGalleryAddTextBtn"); await pg.wait_for_timeout(80)
        await pg.set_input_files("#cardioGalleryImgInput", PNG); await pg.wait_for_timeout(500)
        print("gallery: 2 entries:", await pg.locator("#cardioGalleryList .cardio-gallery-item").count() == 2)
        print("gallery: image stored locally:", await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('fwmc-cardio-images-v1')||'{}')).length") == 1)

        # two activities: own quote, then gallery
        await pg.click('#cardioAddGrid >> text="Joggen"'); await pg.wait_for_timeout(60)
        await pg.click('#cardioAddGrid >> text="Walking"'); await pg.wait_for_timeout(60)
        sels = pg.locator("#cardioList .cardio-motiv-select")
        print("motiv: one selector per activity:", await sels.count() == 2)
        await sels.nth(0).select_option("spruch"); await pg.wait_for_timeout(80)
        quote = "Du bist stärker als du denkst und jeder Schritt zählt heute"
        await pg.fill("#cardioList .cardio-motiv-text", quote)
        await pg.dispatch_event("#cardioList .cardio-motiv-text", "change")
        await pg.locator("#cardioList .cardio-motiv-select").nth(1).select_option("galerie"); await pg.wait_for_timeout(80)
        await pg.reload(); await pg.wait_for_timeout(300)
        await open_cardio(pg)
        print("motiv: survives reload:", await pg.input_value("#cardioList .cardio-motiv-text") == quote)

        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(400)
        bg = await pg.evaluate("getComputedStyle(document.getElementById('cardioPlayer')).backgroundColor")
        print("bg: player tinted:", bg not in ("rgb(255, 255, 255)", "rgba(0, 0, 0, 0)"), bg)
        print("motiv: quote shown:", await pg.is_visible("#cardioMotivText") and quote in await pg.inner_text("#cardioMotivText"))

        # pause sheet carries the background controls
        await pg.click("#cardioPauseBtn"); await pg.wait_for_timeout(120)
        print("pause: bg group visible:", await pg.is_visible("#cardioPauseBgGroup"))
        await pg.click('#cardioPauseBgColorPicker .color-swatch[data-key="gelb"]'); await pg.wait_for_timeout(100)
        bg2 = await pg.evaluate("getComputedStyle(document.getElementById('cardioPlayer')).backgroundColor")
        print("pause: colour change applies live:", bg2 != bg, bg2)
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(150)

        # inline Zusatzreiz (addon-flash) while the quote is shown
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(150)
        det = "#cardioAddonPickerDetail"
        for f, v in (("duration", "60"), ("stimulusS", "0.3"), ("intervalMin", "0.5"), ("intervalMax", "0.5")):
            loc = pg.locator(f'{det} input[data-f="{f}"]').first
            await loc.fill(v); await loc.dispatch_event("input")
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(200)
        print("inline: Cardio stays on screen:", await pg.is_visible("#cardioPlayer") and await pg.is_hidden("#player"))
        print("inline: no takeover badge:", await pg.is_hidden("#cardioGuestBadge"))
        c0 = await pg.inner_text("#cardioCountdown")
        results = []
        for _ in range(60):
            r = await pg.evaluate(OVERLAP_JS)
            if r: results.append(r)
            await pg.wait_for_timeout(130)
        print("inline: characters appeared:", len(results) >= 8, len(results))
        print("inline: never on a glyph/timer/bar:", all(r == "ok" for r in results), [r for r in results if r != "ok"][:3])
        print("inline: Cardio kept counting:", c0 != await pg.inner_text("#cardioCountdown"))
        await pg.click("#cardioPauseBtn"); await pg.wait_for_timeout(100)
        n0 = await pg.evaluate("document.getElementById('cardioFlashLayer').innerHTML")
        await pg.wait_for_timeout(1200)
        print("inline: frozen while paused:", n0 == await pg.evaluate("document.getElementById('cardioFlashLayer').innerHTML"))
        await pg.click("#trainPauseResumeBtn"); await pg.wait_for_timeout(100)

        # other guests stay a full takeover
        await pg.click("#cardioAddonTriggerBtn"); await pg.wait_for_timeout(150)
        await pg.click('#cardioAddonPickerTypeRow .choice:has-text("VT")'); await pg.wait_for_timeout(100)
        await pg.click("#cardioAddonPickerStartBtn"); await pg.wait_for_timeout(300)
        print("other guest: full takeover:", await pg.is_visible("#player") and await pg.is_hidden("#cardioPlayer"))
        print("other guest: inline flash stopped:", await pg.evaluate("document.getElementById('cardioFlashLayer').childElementCount") == 0)
        await pg.click("#backBtn"); await pg.wait_for_timeout(300)

        # gallery activity
        await pg.click("#cardioSkipBtn"); await pg.wait_for_timeout(300)
        shown = await pg.evaluate("""() => ({img: !document.getElementById('cardioMotivImg').hidden,
            txt: document.getElementById('cardioMotivText').hidden ? '' : document.getElementById('cardioMotivText').textContent})""")
        print("gallery: an entry is shown on the gallery activity:", shown["img"] or shown["txt"] == "Weiter so", shown)
        await pg.click("#cardioBackBtn"); await pg.wait_for_timeout(200)
        await pg.context.close()

        # gallery change interval, in order (time warp)
        seed = """localStorage.setItem('fwmc-cardio-v1', JSON.stringify({items:[{activity:'joggen',durationS:600,label:'',interval:null,motiv:{mode:'galerie'}}],
          defaultDurationS:600,bgColorKey:'gruen',bgIntensity:0,gallery:[{id:'a',text:'Eins'},{id:'b',text:'Zwei'},{id:'c',text:'Drei'}],galleryChangeS:15,galleryOrder:'reihe'}));
          (function(){const real=performance.now.bind(performance);let off=0;window.__warp=(ms)=>{off+=ms};performance.now=()=>real()+off;
          const raf=window.requestAnimationFrame.bind(window);window.requestAnimationFrame=(cb)=>raf((t)=>cb(t+off));})();"""
        pg = await new_page(b, errors, seed)
        await open_cardio(pg)
        await pg.click("#cardioStartBtn"); await pg.wait_for_timeout(300)
        t1 = await pg.inner_text("#cardioMotivText")
        await pg.evaluate("window.__warp(16000)"); await pg.wait_for_timeout(200)
        t2 = await pg.inner_text("#cardioMotivText")
        await pg.evaluate("window.__warp(16000)"); await pg.wait_for_timeout(200)
        t3 = await pg.inner_text("#cardioMotivText")
        print("gallery: changes in order every interval:", [t1, t2, t3] == ["Eins", "Zwei", "Drei"], [t1, t2, t3])
        await pg.context.close()

        print("no page errors:", errors == [], errors[:3])
        await b.close()
    os.remove(PNG)

asyncio.run(main())
