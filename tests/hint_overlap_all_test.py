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
TEST=["ab","alarm","anti","antizip","bisect","corsi","dsst","eyecount","flanker","gng","hick","iconic","kippbild","merk","navon","posner","pvt","reakt","rotation","search","simon","stop","stroop","subitize","testNback","trail","ts","ufov","vorlauf","wcst","ton"]
NAT=[("remember","#rememberOpenFixed"),("blitz","#blitzOpenBtn"),("flash","#flashOpenConstant"),("mot","#motOpenSpeed"),("balance","#balanceOpenBtn")]
JS="""(p)=>{const pl=document.getElementById(p+'Player'); if(!pl||pl.hidden) return null;
const hint=document.getElementById(p+'Hint'); const bar=document.getElementById(p+'PlayerBar');
const R=e=>e.getBoundingClientRect(); const out=[];
const zones=[]; if(hint&&hint.textContent.trim()&&R(hint).height) zones.push(['hint',R(hint)]); if(bar&&R(bar).height){ for(const c of bar.children){const r=R(c); if(r.height) zones.push(['bar:'+(c.id||c.textContent.trim().slice(0,10)),r]);}}
for(const e of pl.querySelectorAll('*')){ if(['bisectArea','subitizeDots','trailLinesSvg','optoCanvas'].includes(e.id)||e.classList.contains('mbg-canvas')||e===hint||(hint&&hint.contains(e))||(bar&&bar.contains(e))) continue;
 if(e.closest('.pause-overlay,.done-panel,[id$=DonePanel],[id$=PauseOverlay]')) continue;
 const cs=getComputedStyle(e); if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity===0) continue;
 if([...e.children].some(c=>{const r=R(c);return r.width&&r.height;})) continue;
 const r=R(e); if(!r.width||!r.height) continue;
 for(const [n,z] of zones){ if(r.left<z.right-1&&r.right>z.left+1&&r.top<z.bottom-1&&r.bottom>z.top+1) out.push(n+' <> '+(e.id||e.className||e.tagName)); }}
return out;}"""
BAD=[]
async def run(b,vp,p,opener=None,worst=False,seed=None,tag=""):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    if seed: await pg.add_init_script(seed)
    await pg.add_init_script("localStorage.setItem('fwmc-test-unlocked','true');localStorage.setItem('fwmc-tips-seen','true')")
    # Farbbrille exercises start only once calibrated (eyecount, 2026-10-08)
    await pg.add_init_script("localStorage.setItem('fwmc-anaglyph-v1',JSON.stringify({left:'rot',red:'#ff0000',green:'#00ff00',calibrated:true,hintOff:true}))")
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
    print(vp['width'],p,tag or ("worst" if worst else ""),"OK" if not found else sorted(found)[:6])
    if found: BAD.append((vp['width'],p+tag))
    await ctx.close()
# Farbfelder (2026-10-07) draws its grid on the shared VT canvas, under the
# floating player bar: every mode must keep the grid below the bar and above
# its caption band (window.__ffLastGeom, CSS px).
async def run_ff(b,vp):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}))")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(250)
    # + the Reize (2026-10-07 night): Ansage, Farbwort, Fuß und Hand, Sehen und Hören
    for mode in ["leuchten","einblenden","regeln","leer","abfolge","ansage","farbwort","fusshand","sehenhoeren"]:
        await pg.click('.excard[data-exercise="farbfelder"]'); await pg.wait_for_timeout(150)
        await pg.evaluate("(m)=>{document.querySelector(`[data-ff-mode=${m}]`).click();document.querySelector('[data-ff-foot=wechsel]').click();document.querySelector('[data-ff-flip=\"2\"]').click()}",mode)
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
# Richtungskreuz (2026-10-08): cross overview and signs stay below the player
# bar (now with ⓘ) and above the caption band (shares ffGeometry).
async def run_rk(b,vp):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}))")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(250)
    for mode in ["zeigen","abfolge"]:
        await pg.click('.excard[data-exercise="richtungskreuz"]'); await pg.wait_for_timeout(150)
        await pg.evaluate("(m)=>{document.querySelector(`[data-rk-mode=${m}]`).click();document.querySelector('[data-rk-signs=beide]').click()}",mode)
        await pg.evaluate("()=>{window.__ffLastGeom=null;document.getElementById('startBtn').click()}")
        bad=set(); seen=0
        for i in range(25):
            await pg.wait_for_timeout(200)
            g=await pg.evaluate("()=>window.__ffLastGeom")
            if g:
                seen+=1
                if not (g['top']>=g['barBottom'] and g['bottom']<=g['capTop']+0.5): bad.add("cross/sign <> bar/caption")
        if not seen: bad.add("nothing drawn")
        if errs: bad.add("pageerror: "+errs[0][:80])
        print(vp['width'],"richtungskreuz",mode,"OK" if not bad else sorted(bad))
        if bad: BAD.append((vp['width'],"richtungskreuz "+mode))
        await pg.click("#backBtn"); await pg.wait_for_timeout(250)
        await pg.click("#backToHome"); await pg.wait_for_timeout(150)
    await ctx.close()
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
# Optodrum (Aktivierung, 2026-10-08): the pattern canvas fills the stage
# behind the floating bar on purpose (like the VT canvas, nothing to read
# there); the "Fertig" chip (Ohne Zeitlimit) and the fixation point must be
# clear of every bar item.
async def run_opto(b,vp):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}));localStorage.setItem('fwmc-optodrum-prefs-v1',JSON.stringify({noLimit:true,fix:true}))")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL.replace("bereich=visual","bereich=aktivierung")); await pg.wait_for_timeout(250)
    await pg.click("#optoOpenBtn"); await pg.click("#optoStartBtn"); await pg.wait_for_timeout(400)
    found=set(await pg.evaluate(JS,"opto") or [])
    fix=await pg.evaluate("()=>{const s=document.getElementById('optoStage').getBoundingClientRect();const cy=s.top+s.height/2;return [...document.getElementById('optoPlayerBar').children].every(c=>{const r=c.getBoundingClientRect();return !r.height||r.bottom<cy-12;});}")
    if not fix: found.add("fixation point <> bar")
    if errs: found.add("pageerror: "+errs[0][:80])
    print(vp['width'],"optodrum","OK" if not found else sorted(found))
    if found: BAD.append((vp['width'],"optodrum"))
    await ctx.close()
# Neuro-Aktivierung (2026-10-08): step text, side pill and countdown sit
# below the floating player bar (flow layout like Eigenes Training).
async def run_neuro(b,vp):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-test-neuro','true');localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}))")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    for ex in ["vibration","gelenke"]:
        await pg.goto(URL.replace("bereich=visual","bereich=neuro")); await pg.wait_for_timeout(250)
        await pg.click(f'[data-neuro-ex="{ex}"]'); await pg.click("#neuroStartBtn"); await pg.wait_for_timeout(300)
        bad=set(await pg.evaluate("()=>{const bar=[...document.getElementById('neuroPlayerBar').children].map(c=>c.getBoundingClientRect()).filter(r=>r.height);const bb=Math.max(...bar.map(r=>r.bottom));return ['neuroRunProgress','neuroRunTitle','neuroRunIcon','neuroRunItem','neuroRunSide','neuroRunCountdown'].filter(id=>{const e=document.getElementById(id);const r=e.getBoundingClientRect();return r.height&&r.top<bb-1;});}"))
        if errs: bad.add("pageerror: "+errs[0][:80])
        print(vp['width'],"neuro",ex,"OK" if not bad else sorted(bad))
        if bad: BAD.append((vp['width'],"neuro "+ex))
        await pg.click("#neuroBackBtn"); await pg.wait_for_timeout(200)
    await ctx.close()
# Hütchen · Laufweg (2026-10-08): caption, map and buttons sit below the
# floating player bar, in both variants (Karte / Weg merken).
async def run_lw(b,vp):
    ctx=await b.new_context(viewport=vp,service_workers="block"); pg=await ctx.new_page()
    await pg.add_init_script("localStorage.setItem('fwmc-tips-seen','true');localStorage.setItem('fwmc-master-v1',JSON.stringify({startCountdown:false}))")
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(URL); await pg.wait_for_timeout(250)
    for v in ["karte","merken"]:
        await pg.click('.excard[data-exercise="cone-path"]'); await pg.wait_for_timeout(150)
        await pg.evaluate("(v)=>{document.querySelector(`[data-lw-variant=${v}]`).click();document.getElementById('startBtn').click()}",v)
        await pg.wait_for_timeout(300)
        bad=await pg.evaluate("()=>{const bar=[...document.getElementById('playerBar').children].map(c=>c.getBoundingClientRect()).filter(r=>r.height);const bb=Math.max(...bar.map(r=>r.bottom));return ['lwCaption','lwMap','lwNextBtn'].filter(id=>{const e=document.getElementById(id);const r=e.getBoundingClientRect();return r.height&&r.top<bb-1;});}")
        bad=set(bad)
        if errs: bad.add("pageerror: "+errs[0][:80])
        print(vp['width'],"cone-path",v,"OK" if not bad else sorted(bad))
        if bad: BAD.append((vp['width'],"cone-path "+v))
        await pg.click("#backBtn"); await pg.wait_for_timeout(250)
        if await pg.is_visible("#doneBackBtn"): await pg.click("#doneBackBtn"); await pg.wait_for_timeout(150)
        if await pg.is_visible("#backToHome"): await pg.click("#backToHome"); await pg.wait_for_timeout(150)
    await ctx.close()
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox"])
        for vp in [{"width":390,"height":844},{"width":1000,"height":750}]:
            for p in TEST: await run(b,vp,p)
            for p,o in NAT: await run(b,vp,p,o)
            # Gleichgewicht · Wörter + Bewegter Hintergrund (2026-10-08): the word stays below the hint
            await run(b,vp,"balance","#balanceOpenBtn",seed="localStorage.setItem('fwmc-balance-prefs-v1',JSON.stringify({content:'woerter',wordList:'farben',size:2,bpm:200,mbg:{pattern:'punkte'}}))",tag=" woerter+mbg")
            await run(b,vp,"flash","#flashOpenConstant",seed="localStorage.setItem('fwmc-flash-prefs-v1',JSON.stringify({mbg:{pattern:'streifen'}}))",tag=" mbg")
            await run(b,vp,"mot","#motOpenSpeed",seed="localStorage.setItem('fwmc-mot-prefs-v1',JSON.stringify({mbg:{pattern:'streifen'}}))",tag=" mbg")
            await run(b,vp,"bisect",worst=True)
            await run_ff(b,vp)
            await run_cn(b,vp)
            await run_rk(b,vp)
            await run_opto(b,vp)
            await run_neuro(b,vp)
            await run_lw(b,vp)
        await b.close()
    print("all exercises clear of hint/bar:", not BAD)
asyncio.run(main())
