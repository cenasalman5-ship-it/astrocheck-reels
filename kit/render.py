"""Render a kit reel. Run from anywhere:
  python3 kit/render.py <reel_dir> preview 0,0.6,1.2,...      -> <reel_dir>/prev/pXX.XX.jpg
  python3 kit/render.py <reel_dir> frames [fps=30] [jobs=3]   -> <reel_dir>/frames/f00000.jpg ... + meta.json (MK_META, MK_EVENTS, SFX)
  python3 kit/render.py <reel_dir> encode [out.mp4]           -> frames + aud/mix.wav -> mp4 (crf 20, faststart)
  add ?guides=1 by setting GUIDES=1 for zone guide lines in previews."""
import asyncio, sys, os, json, subprocess
from playwright.async_api import async_playwright
D = os.path.abspath(sys.argv[1]); MODE = sys.argv[2]
URL = 'file://' + D + '/reel.html' + ('?guides=1' if os.environ.get('GUIDES') else '')
async def page(b):
    pg = await b.new_page(viewport={'width': 1080, 'height': 1920}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200])); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text[:200]))
    await pg.goto(URL); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(800); return pg, errs
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--allow-file-access-from-files'])
        pg, errs = await page(b); dur = await pg.evaluate('window.DUR')
        if MODE == 'preview':
            os.makedirs(D + '/prev', exist_ok=True)
            for ts in sys.argv[3].split(','):
                t = float(ts); await pg.evaluate(f'REEL.render({t})'); await pg.wait_for_timeout(40)
                await pg.screenshot(path=f'{D}/prev/p{t:05.2f}.jpg', type='jpeg', quality=72)
        elif MODE == 'frames':
            fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30; jobs = int(sys.argv[4]) if len(sys.argv) > 4 else 3
            n = int(round(dur * fps)); os.makedirs(D + '/frames', exist_ok=True)
            for f in os.listdir(D + '/frames'): os.remove(D + '/frames/' + f)
            meta = await pg.evaluate('({meta:window.MK_META,events:window.MK_EVENTS,sfx:window.SFX,dur:window.DUR})')
            json.dump(meta, open(D + '/meta.json', 'w'), indent=1)
            pages = [pg] + [(await page(b))[0] for _ in range(jobs - 1)]
            async def run(k, q):
                for i in range(k, n, jobs):
                    await q.evaluate(f'REEL.render({i / fps})'); await q.screenshot(path=f'{D}/frames/f{i:05d}.jpg', type='jpeg', quality=90)
            await asyncio.gather(*[run(k, q) for k, q in enumerate(pages)])
            print('frames', n)
        print('dur', dur, 'errors', errs[:5]); await b.close()
if MODE == 'encode':
    out = sys.argv[3] if len(sys.argv) > 3 else D + '/out.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-i', D + '/frames/f%05d.jpg', '-i', D + '/aud/mix.wav',
                    '-c:v', 'libx264', '-crf', '20', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', '-shortest', out], check=True)
    print('encoded', out, round(os.path.getsize(out) / 1e6, 1), 'MB')
else:
    asyncio.run(main())
