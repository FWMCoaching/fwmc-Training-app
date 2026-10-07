# Client report 2026-10-01 (iPad screenshot): Linienhalbierungs-Test drew its
# line right next to the "Tippe auf die Mitte der Linie" hint. Rule from the
# client: nothing in any exercise may ever sit behind/under a button, the
# top hint, or anything else floating on the stage. This audit starts every
# Test-Bereich and NAT exercise at phone (390px) and iPad (1000px) width,
# samples the stage repeatedly, and fails if any visible leaf element
# overlaps the hint or a player-bar item. Plus a worst-case run of
# Linienhalbierung with Math.random forced to 0 (line at the very top).
import asyncio, sys
from playwright.async_api import async_playwright
URL="http://localhost:8845/index.html?bereich=visual"
TEST=["ab","alarm","anti","antizip","bisect","corsi","dsst","flanker","gng","hick","iconic","kippbild","merk","navon","posner","pvt","reakt","rotation","search","simon","stop","stroop","subitize","testNback","trail","ts","ufov","vorlauf","wcst"]
NAT=[("remember","#rememberOpenFixed"),("blitz","#blitzOpenBtn"),("flash","#flashOpenConstant"),("mot","#motOpenSpeed"),("balance","#balanceOpenBtn")]
JS="""(p)=>{const pl=document.getElementById(p+'Player'); if(!pl||pl.hidden) return null;
const hint=document.getElementById(p+'Hint'); const bar=document.getElementById(p+'PlayerBar');
const R=e=>e.getBoundingClientRect(); const out=[];
const zones=[]; if(hint&&hint.textContent.trim()&&R(hint).height) zones.push(['hint',R(hint)]); if(bar&&R(bar).height){ for(const c of bar.children){const r=R(c); if(r.height) zones.push(['bar:'+(c.id||c.textContent.trim().slice(0,10)),r]);}}
for(const e of pl.querySelectorAll('*')){ if(['bisectArea','subitizeDots','trailLinesSvg'].includes(e.id)||e===hint||(hint&&hint.contains(e))||(bar&&bar.contains(e))) continue;
 if(e.closest('.pause-overlay,.done-panel,[id$=DonePanel],[id$=PauseOverlay]')) continue;
 const cs=getComputedStyle(e); if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity===0) continue;
 if([...e.children].some(c=>{const r=R(c);return r.width&&r.height;})) continue;
 const r=R(e); if(!r.width||!r.height) continue;
 for(const [n,z] of zones){ if(r.left<z.right-1&&r.right>z.left+1&&r.top<z.bottom-1&&r.bottom>z.top+1) out.push(n+' <> '+(e.id||e.className||e.tagName)); }}
return out;}"""
BAD=[]
async def run(b,vp,p,opener=None,worst=False):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked','true');localStorage.setItem('fwmc-tips-seen','true')")
    if worst: await pg.add_init_script("Math.random=()=>0")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(250)
    try:
        if opener:
            await pg.click('[data-section="nat"]'); await pg.click(f'.sub-tab[data-nat-sub="{p}"]'); await pg.click(opener)
        else:
            await pg.click('[data-section="test"]'); await pg.click(f'#{p}OpenBtn')
        await pg.wait_for_timeout(150); await pg.click(f'#{p}ReadyStartBtn')
    except Exception as e:
        print(vp['width'],p,"NAV FAIL",str(e)[:80]); BAD.append((vp['width'],p)); await ctx.close(); return
    found=set()
    for i in range(24):
        await pg.wait_for_timeout(150)
        r=await pg.evaluate(JS,p)
        if r: found.update(r)
        if p=="bisect" and i%2==1:
            try: await pg.click("#bisectArea", position={"x":20,"y":300}, timeout=500)
            except Exception: pass
    if errs: found.add("pageerror: "+errs[0][:80])
    print(vp['width'],p,"worst" if worst else "","OK" if not found else sorted(found)[:6])
    if found: BAD.append((vp['width'],p))
    await ctx.close()
# Farbfelder (2026-10-07) draws its grid on the shared VT canvas, under the
# floating player bar: every mode must keep the grid below the bar and above
# its caption band (window.__ffLastGeom, CSS px).
async def run_ff(b,vp):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}))")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(250)
    for mode in ["leuchten","regeln","leer","abfolge"]:
        await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(150)
        await pg.evaluate("(m)=>{document.querySelector(`[data-ff-mode=${m}]`).click();document.querySelector('[data-ff-foot=wechsel]').click()}",mode)
        await pg.evaluate("()=>document.getElementById('startBtn').click()")
        bad=set()
        for i in range(10):
            await pg.wait_for_timeout(200)
            g=await pg.evaluate("()=>window.__ffLastGeom")
            if g and not (g['top']>=g['barBottom'] and g['bottom']<=g['capTop']+0.5): bad.add("grid <> bar/caption")
        if errs: bad.add("pageerror: "+errs[0][:80])
        print(vp['width'],"farbfelder",mode,"OK" if not bad else sorted(bad))
        if bad: BAD.append((vp['width'],"farbfelder "+mode))
        await pg.click("#backBtn"); await pg.wait_for_timeout(250)
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
    await ctx.close()
# Hütchen · Farbe + Zahl (2026-10-07): the colour disc on the shared VT
# canvas stays below the floating player bar and inside the stage, at every
# field count (window.__cnLastGeom, CSS px).
async def run_cn(b,vp):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}))")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(250)
    for n in ["3","6"]:
        await pg.click('.excard[data-exercise="cone-number"]'); await pg.wait_for_timeout(150)
        await pg.evaluate("(n)=>document.querySelector(`[data-cn-fields=\"${n}\"]`).click()",n)
        await pg.evaluate("()=>{window.__cnLastGeom=null;document.getElementById('startBtn').click()}")
        bad=set(); seen=0
        for i in range(30):
            await pg.wait_for_timeout(200)
            g=await pg.evaluate("()=>window.__cnLastGeom")
            if g:
                seen+=1
                if not (g['top']>=g['barBottom'] and g['bottom']<=g['stageBottom']+0.5): bad.add("disc <> bar/stage")
        if not seen: bad.add("no stimulus drawn")
        if errs: bad.add("pageerror: "+errs[0][:80])
        print(vp['width'],"cone-number",n,"OK" if not bad else sorted(bad))
        if bad: BAD.append((vp['width'],"cone-number "+n))
        await pg.click("#backBtn"); await pg.wait_for_timeout(250)
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
    await ctx.close()
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox"])
        for vp in [{"width":390,"height":844},{"width":1000,"height":750}]:
            for p in TEST: await run(b,vp,p)
            for p,o in NAT: await run(b,vp,p,o)
            await run(b,vp,"bisect",worst=True)
            await run_ff(b,vp)
            await run_cn(b,vp)
        await b.close()
    print("all exercises clear of hint/bar:", not BAD)
asyncio.run(main())
