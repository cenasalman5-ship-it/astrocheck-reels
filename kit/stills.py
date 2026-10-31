"""Carousel slides + Instagram story from a reel (no extra voice).
  python3 kit/stills.py <reel_dir> carousel slides.json   -> <reel_dir>/stills/slide1.jpg ... (1080x1350)
     slides.json = {"theme":{"bg":"#..","ink":"#..","accent":"#.."}, "bg_time":3.2, "series":"108 KA KHAZANA · PART 3",
                    "slides":[{"big":"7th ghar ka Mangal = shaadi kharab?","small":"Swipe karo →"}, ..., {"big":"Aapka Mangal kis ghar me?","small":"Comment karo · astrocheck.app"}]}
  python3 kit/stills.py <reel_dir> story <t> "Nayi reel aa gayi" "Apni rashi reply karo"  -> stills/story.jpg (1080x1920)"""
import sys, os, json, asyncio, html
from playwright.async_api import async_playwright
D = os.path.abspath(sys.argv[1]); MODE = sys.argv[2]; K = os.path.dirname(os.path.abspath(__file__)); os.makedirs(D + '/stills', exist_ok=True)
async def frame_png(t):
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--allow-file-access-from-files']); pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.goto('file://' + D + '/reel.html'); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(600)
        await pg.evaluate("document.querySelectorAll('#mk-cap,#mk-url,#mk-end,#mk-badge').forEach(e=>e.remove())")
        await pg.evaluate(f'REEL.render({t})'); path = f'{D}/stills/_bg.png'; await pg.screenshot(path=path); await b.close(); return path
CSS = """@font-face{font-family:IB;src:url(file://%(K)s/fonts/InterDisplay-Black.otf)}@font-face{font-family:IBo;src:url(file://%(K)s/fonts/InterDisplay-Bold.otf)}
*{margin:0;box-sizing:border-box}body{width:%(w)dpx;height:%(h)dpx;overflow:hidden;position:relative;background:%(bg)s;color:%(ink)s;font-family:IBo}
.bg{position:absolute;inset:-30px;background:url(file://%(bgimg)s) center/cover;filter:blur(14px) brightness(.45)}
.c{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:0 80px;gap:40px}
.big{font:%(big)dpx/1.05 IB;text-wrap:balance}.small{font:50px/1.2 IBo;color:%(accent)s}
.top{position:absolute;top:60px;left:60px;font:38px IBo;letter-spacing:.06em;padding:12px 26px;border-radius:40px;background:rgba(0,0,0,.4)}
.n{position:absolute;bottom:60px;right:70px;font:40px IBo;opacity:.7}.arrow{width:120px;height:120px}"""
async def shoot(pages, w, h, prefix):
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--allow-file-access-from-files']); pg = await b.new_page(viewport={'width': w, 'height': h})
        for i, body in enumerate(pages, 1):
            await pg.set_content(body); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(200)
            await pg.screenshot(path=f'{D}/stills/{prefix}{i if len(pages) > 1 else ""}.jpg', type='jpeg', quality=90)
        await b.close()
if MODE == 'carousel':
    C = json.load(open(os.path.join(D, sys.argv[3]), encoding='utf-8')); th = C['theme']; bg = asyncio.run(frame_png(C.get('bg_time', 2)))
    pages = []
    for i, s in enumerate(C['slides'], 1):
        css = CSS % dict(K=K, w=1080, h=1350, bg=th['bg'], ink=th['ink'], accent=th['accent'], bgimg=bg, big=118 if i == 1 else 96)
        pages.append(f"<style>{css}</style><div class=bg></div><div class=top>{html.escape(C.get('series', 'AstroCheck'))}</div><div class=c><div class=big>{html.escape(s['big'])}</div><div class=small>{html.escape(s.get('small', ''))}</div></div><div class=n>{i}/{len(C['slides'])}</div>")
    asyncio.run(shoot(pages, 1080, 1350, 'slide'))
elif MODE == 'story':
    t = float(sys.argv[3]); big, small = sys.argv[4], sys.argv[5]; bg = asyncio.run(frame_png(t))
    css = CSS % dict(K=K, w=1080, h=1920, bg='#000', ink='#fff', accent='#f2c14e', bgimg=bg, big=120)
    arrow = '<svg class=arrow viewBox="0 0 24 24"><path d="M12 3v15m0 0l-6-6m6 6l6-6" stroke="#f2c14e" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    page = f"<style>{css}.bg{{filter:brightness(.6)}}</style><div class=bg></div><div class=c><div class=big>{html.escape(big)}</div>{arrow}<div class=small>{html.escape(small)}</div></div>"
    asyncio.run(shoot([page], 1080, 1920, 'story'))
print(sorted(os.listdir(D + '/stills')))
