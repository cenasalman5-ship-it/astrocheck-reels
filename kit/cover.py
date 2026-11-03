"""Reel cover (1080x1920) in the house style used since 2 Nov 2026: blurred reel frame behind, AstroCheck pill on top,
small kicker line, BIG title, coloured band, one handwritten line, astrocheck.app at the bottom. Key text stays in the centre (grid crop).
  python3 kit/cover.py <reel_dir> <frame_t> "<kicker>" "<TITLE (use | for line break)>" "<band>" "<band_bg>" "<band_ink>" "<hand line>" <out.jpg>"""
import sys, os, asyncio, html
from playwright.async_api import async_playwright
K = os.path.dirname(os.path.abspath(__file__))
D, T, kicker, title, band, bbg, bink, hand, out = os.path.abspath(sys.argv[1]), float(sys.argv[2]), *sys.argv[3:10]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--allow-file-access-from-files']); pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.goto('file://' + D + '/reel.html'); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(600)
        await pg.evaluate("document.querySelectorAll('#mk-cap,#mk-url,#mk-end,#mk-endbg,#mk-badge').forEach(e=>e.remove())")
        await pg.evaluate(f'REEL.render({T})'); bg = D + '/_cover_bg.png'; await pg.screenshot(path=bg)
        t = '<br>'.join(html.escape(x) for x in title.split('|'))
        page = f"""<style>@font-face{{font-family:IB;src:url(file://{K}/fonts/InterDisplay-Black.otf)}}@font-face{{font-family:IBo;src:url(file://{K}/fonts/InterDisplay-Bold.otf)}}@font-face{{font-family:KB;src:url(file://{K}/fonts/Kalam-700.woff2)}}
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1920px;overflow:hidden;position:relative;background:#000;color:#fff}}
.bg{{position:absolute;inset:-40px;background:url(file://{bg}) center/cover;filter:blur(18px) brightness(.62) saturate(1.15)}}
.pill{{position:absolute;top:140px;left:0;right:0;margin:auto;width:max-content;display:flex;gap:16px;align-items:center;padding:12px 30px 12px 14px;border-radius:50px;background:rgba(0,0,0,.55);font:44px IBo}}
.pill img{{width:58px;height:58px;border-radius:14px}}
.c{{position:absolute;left:60px;right:60px;top:560px;text-align:center}}
.k{{font:52px IBo;letter-spacing:.03em}}.t{{margin-top:18px;font:200px/0.95 IB;letter-spacing:-.02em;text-shadow:0 18px 50px rgba(0,0,0,.45)}}
.b{{display:inline-block;margin-top:46px;padding:12px 34px 18px;border-radius:22px;font:82px IB;background:{bbg};color:{bink};transform:rotate(-2deg)}}
.h{{margin-top:36px;font:70px KB}}.u{{position:absolute;bottom:330px;left:0;right:0;text-align:center;font:54px IBo}}</style>
<div class=bg></div><div class=pill><img src="file://{K}/icon.png">AstroCheck</div>
<div class=c><div class=k>{html.escape(kicker)}</div><div class=t>{t}</div><div class=b>{html.escape(band)}</div><div class=h>{html.escape(hand)}</div></div><div class=u>astrocheck.app</div>"""
        await pg.set_content(page); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=out, type='jpeg', quality=90); await b.close(); os.remove(bg)
asyncio.run(main()); print('cover', out)
