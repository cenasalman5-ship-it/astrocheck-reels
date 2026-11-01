"""AstroCheck reel lint — the code gate in front of the 9/10 QA bar (thresholds = SKILL.md section 8 table).
  python3 kit/lint.py --script <reel_dir>      pre-voice: checks <reel_dir>/script.json
  python3 kit/lint.py <reel_dir> [--type placement|rashi|app]   post-render: needs reel.html, frames/, aud/ stems
Exit 1 if any FAIL. Writes <reel_dir>/lint-report.txt."""
import sys, os, re, json, glob, subprocess, difflib, asyncio
import numpy as np
K = os.path.dirname(os.path.abspath(__file__)); RES = []
def rep(level, check, msg): RES.append((level, check, msg))
def words(name): return [l.strip() for l in open(f'{K}/words/{name}.txt', encoding='utf-8') if l.strip() and not l.startswith('#')]
def finish(D):
    order = {'FAIL': 0, 'WARN': 1, 'PASS': 2}; RES.sort(key=lambda r: order[r[0]])
    txt = '\n'.join(f'{l:4} | {c:18} | {m}' for l, c, m in RES); nf = sum(r[0] == 'FAIL' for r in RES); nw = sum(r[0] == 'WARN' for r in RES)
    txt += f'\n\nRESULT: {"FAIL" if nf else "PASS"} — {nf} fail, {nw} warn'; open(D + '/lint-report.txt', 'w').write(txt); print(txt); sys.exit(1 if nf else 0)
def banned_hits(text):
    t = text.lower(); al = [a.lower() for a in words('allow')]
    for a in al: t = t.replace(a, ' ')
    return [b for b in words('banned') if b.lower() in t]
# ------------------------------------------------------------------ script lint
def lint_script(D):
    S = json.load(open(D + '/script.json', encoding='utf-8')); typ = S.get('type', 'placement'); v = S['voice']
    plain = re.sub(r'\[[A-Z0-9]+-[AB]\d+\]', ' ', v); n = len(re.findall(r'[\u0900-\u097F]+|[A-Za-z0-9%]+', plain))
    lo, hi, wlo, whi = (45, 65, 45, 60) if typ == 'app' else (50, 70, 55, 65)
    if n < lo or n > hi: rep('FAIL', 'spoken words', f'{n} words (allowed {lo}–{hi})')
    elif n < wlo or n > whi: rep('WARN', 'spoken words', f'{n} words (target {wlo}–{whi})')
    else: rep('PASS', 'spoken words', f'{n}')
    if typ in ('rashi', 'placement'):
        np_ = len(S.get('points') or []); rep('FAIL' if np_ < 3 else 'PASS', 'info points', f'{np_} points (need 3–4)')
    allt = ' '.join([v, S.get('cap_roman', ''), S.get('screen_text', ''), S.get('captions', '')])
    b = banned_hits(allt); rep('FAIL' if b else 'PASS', 'banned words', ', '.join(b) or 'none')
    head = ' '.join(re.findall(r'\S+', plain)[:16]).lower() + ' ' + ' '.join(S.get('cap_roman', '').split()[:16]).lower()
    fl = [f for f in words('filler') if f.lower() in head]; rep('FAIL' if fl else 'PASS', 'filler (first 6 s)', ', '.join(fl) or 'none')
    bad = re.findall(r'[0-9]+|[A-Za-z]+', plain) + [m for m in words('misreads') if m in plain]
    rep('FAIL' if bad else 'PASS', 'pronunciation', ('digits/Roman in voice: ' + ', '.join(sorted(set(bad)))) if bad else 'clean Devanagari')
    tags = re.findall(r'\[([A-Z0-9]+-[AB]\d+)\]', v)
    if typ == 'placement':
        cards = json.load(open(K + '/khazana-cards.json', encoding='utf-8'))['cards'] if os.path.exists(K + '/khazana-cards.json') else {}
        ids = {i['id']: (k, 'A') for k, c in cards.items() for i in c.get('A', [])} | {i['id']: (k, 'B') for k, c in cards.items() for i in c.get('B', [])}
        if not tags: rep('WARN', 'fact-card IDs', 'no claim tags in the voice script')
        for line in re.split(r'[।?\n]', re.sub(r'([।?])\s*((?:\[[A-Z0-9]+-[AB]\d+\]\s*)+)', r' \2\1', v)):
            for tg in re.findall(r'\[([A-Z0-9]+-[AB]\d+)\]', line):
                if tg not in ids: rep('FAIL', 'fact-card IDs', f'{tg} not in khazana-cards.json')
                elif ids[tg][1] == 'B' and not any(h in line.lower() for h in words('hedges')): rep('FAIL', 'fact-card IDs', f'{tg} is a B item without a hedge')
        if tags and not any(r[1] == 'fact-card IDs' and r[0] == 'FAIL' for r in RES): rep('PASS', 'fact-card IDs', ', '.join(tags))
    finish(D)
# ------------------------------------------------------------------ post-render lint
JS = r"""(t)=>{REEL.render(t);
 const eff=el=>{let o=1,e=el;while(e&&e.nodeType===1){const cs=getComputedStyle(e);if(cs.display==='none'||cs.visibility==='hidden')return 0;o*=parseFloat(cs.opacity);e=e.parentElement}return o};
 const out=[];const seen=new Set();
 const all=document.querySelectorAll('#st *');
 for(const el of all){ if(el.closest('#mk-guides'))continue;
   const own=[...el.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).map(n=>n.textContent.trim()).join(' ');
   if(!own)continue; const o=eff(el); if(o<0.3)continue; const r=el.getBoundingClientRect(); if(r.width<2||r.height<2)continue;
   if(r.right<0||r.left>1080||r.bottom<0||r.top>1920)continue;
   let fs;const isSvg=el instanceof SVGElement;
   if(isSvg){fs=r.height/1.15}else{const cs=getComputedStyle(el);const lh=el.offsetHeight||r.height;fs=parseFloat(cs.fontSize)*(lh?r.height/lh:1)}
   const roleEl=el.closest('[data-role]');const deco=!!el.closest('[data-lint=deco]');
   out.push({tx:own.slice(0,40),x:r.left,y:r.top,r:r.right,b:r.bottom,fs:Math.round(fs),o:+o.toFixed(2),role:roleEl?roleEl.dataset.role:'',deco});}
 const roles={};for(const el of document.querySelectorAll('[data-role]')){const r=el.getBoundingClientRect();const o=eff(el);const k=el.dataset.role;
   (roles[k]=roles[k]||[]).push({o:+o.toFixed(2),w:r.width,h:r.height,x:r.left,y:r.top,b:r.bottom})}
 return {txt:out,roles};}"""
async def sample_dom(D, times):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--allow-file-access-from-files']); pg = await b.new_page(viewport={'width': 1080, 'height': 1920})
        await pg.goto('file://' + D + '/reel.html'); await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(800)
        res = [(t, await pg.evaluate(JS, t)) for t in times]
        meta = await pg.evaluate('({meta:window.MK_META||null,events:window.MK_EVENTS||[],sfx:window.SFX||[],dur:window.DUR})'); await b.close(); return meta, res
def gray_small(p):
    from PIL import Image
    return np.asarray(Image.open(p).convert('L').resize((108, 192)), dtype=np.float32)
def lint_reel(D, typ_arg=None):
    meta0 = json.load(open(D + '/meta.json')) if os.path.exists(D + '/meta.json') else {}
    frames = sorted(glob.glob(D + '/frames/f*.jpg')); fps = 30
    dur = len(frames) / fps if frames else float(meta0.get('dur') or 0)
    times = [round(x, 2) for x in np.arange(0, dur, .25)] + [round(dur - .05, 2)]
    meta, S = asyncio.run(sample_dom(D, times)); M = meta.get('meta') or {}
    typ = typ_arg or M.get('type') or 'placement'; dur = float(meta.get('dur') or dur)
    # duration
    if dur < 15 or dur > 26: rep('FAIL', 'duration', f'{dur:.1f} s (allowed 15–26)')
    elif typ != 'app' and not 20 <= dur <= 24: rep('WARN', 'duration', f'{dur:.1f} s (target 20–24)')
    else: rep('PASS', 'duration', f'{dur:.1f} s')
    # frame 0
    r0 = S[0][1]['roles']
    for role in ('hook', 'hero'):
        els = r0.get(role)
        if not els: rep('FAIL', 'frame 0', f'no data-role="{role}" element')
        elif max(e['o'] for e in els) < .9: rep('FAIL', 'frame 0', f'{role} not visible at t=0 (opacity {max(e["o"] for e in els)})')
        else: rep('PASS', 'frame 0', f'{role} visible')
    # verdict
    if M.get('mythbust'):
        ok = any(max([e['o'] for e in res['roles'].get('verdict', [])] or [0]) >= .9 for t, res in S if t <= 2.5)
        rep('PASS' if ok else 'FAIL', 'verdict direction', 'visible by 2.5 s' if ok else 'data-role=verdict not visible by 2.5 s')
    # text size + safe zones
    size_f, zone_f = {}, {}
    for t, res in S:
        for e in res['txt']:
            if e['deco']: continue
            role, fs = e['role'], e['fs']; key = e['tx']
            lim = {'hook': (100, 999), 'caption': (84, 104), 'verdict': (80, 999), 'climax': (80, 999), 'cta': (80, 999)}.get(role, (44, 999))
            cur = size_f.get(key)
            if cur is None or fs > cur[2]: size_f[key] = (t, role or 'text', fs, lim)
            if e['b'] > 1632 or e['r'] > 961 or (e['y'] < 120 and e['b'] > 0):
                zone_f.setdefault(key, (t, round(e['y']), round(e['b']), round(e['r'])))
    # judge each text by its largest settled size (entrances/flips shrink it for a moment)
    size_f = {k: v for k, v in size_f.items() if not v[3][0] <= v[2] <= v[3][1]}
    for k, (t, role, fs, lim) in list(size_f.items())[:8]: rep('FAIL', 'text size', f'"{k}" {role} {fs}px at {t}s (need {lim[0]}{"–"+str(lim[1]) if lim[1] < 999 else "+"})')
    if len(size_f) > 8: rep('FAIL', 'text size', f'…and {len(size_f) - 8} more')
    if not size_f: rep('PASS', 'text size', 'all text big enough')
    for k, (t, y, b, r) in list(zone_f.items())[:8]: rep('FAIL', 'safe zones', f'"{k}" at {t}s box y{y}–{b}, right {r}')
    if len(zone_f) > 8: rep('FAIL', 'safe zones', f'…and {len(zone_f) - 8} more')
    if not zone_f: rep('PASS', 'safe zones', 'nothing below 1632, right of 960 or above 120')
    # url element
    two = [t for t, res in S if t > .5 and sum(e['o'] > .3 for e in res['roles'].get('url', [])) > 1]
    rep('FAIL' if two else 'PASS', 'URL element', f'two URLs visible at {two[:3]}' if two else 'one at a time')
    # end card
    vis = [t for t, res in S if max([e['o'] for e in res['roles'].get('endcard', [])] or [0]) > .5]
    if not vis: rep('FAIL', 'end card', 'no data-role="endcard" visible')
    else:
        ed = dur - vis[0]
        rep('PASS' if 2.0 <= ed <= 2.6 else 'FAIL', 'end card', f'{ed:.1f} s (need 2.0–2.5)')
        last = S[-1][1]['txt']; urls = [e for e in last if 'astrocheck.app' in e['tx'] and e['role'] == 'url']
        hd = [e for e in last if e['role'] == 'handles']
        if not urls or max(e['fs'] for e in urls) < 100: rep('FAIL', 'end card', f'URL size {max([e["fs"] for e in urls] or [0])}px (need ≥100)')
        if not hd: rep('FAIL', 'end card', 'handles missing (data-role="handles")')
        elif min(e['fs'] for e in hd) < 44: rep('FAIL', 'end card', f'handles {min(e["fs"] for e in hd)}px (need ≥44)')
    # grah size
    if typ == 'placement':
        g = [e for t, res in S for e in res['roles'].get('grah', []) if e['o'] > .5]
        small = [e for e in g if min(e['w'], e['h']) < 80]
        if small: rep('FAIL', 'grah size', f'grah token {round(min(min(e["w"], e["h"]) for e in small))}px (need ≥80)')
        dive = [e for t, res in S for e in res['roles'].get('dive-grah', []) if e['o'] > .5]
        if not dive or max(min(e['w'], e['h']) for e in dive) < 220: rep('FAIL', 'grah size', 'no kundli dive with grah glyph ≥220px (data-role="dive-grah")')
        if g and not small and dive: rep('PASS', 'grah size', 'ok')
    # ---- pixel checks
    if frames:
        idx = list(range(0, len(frames), 3)); G = [gray_small(frames[i]) for i in idx]; tt = [i / fps for i in idx]
        mask = np.ones((192, 108), bool); mask[int(1150 / 10):int(1625 / 10), :] = False  # captions + chip zone excluded
        ch = [float(((np.abs(G[i] - G[i - 1]) > 20) & mask).mean()) for i in range(1, len(G))]
        ev = sorted(set([round(tt[i + 1], 2) for i, c in enumerate(ch) if c > .025] + [e[0] for e in meta.get('events', [])]))
        hold = M.get('hold'); inhold = lambda a, b: hold and a >= hold[0] - .05 and b <= hold[1] + .05 and hold[1] - hold[0] <= 2.5
        first = [e for e in ev if e <= .6]; second = [e for e in ev if .6 < e <= 1.2]
        moving0 = any(c > .005 for c in ch[:3])
        if not moving0: rep('FAIL', 'visual events', 'nothing moves in the first 0.3 s')
        if not first or not second: rep('FAIL', 'visual events', f'need events by 0.6 s and by 1.2 s (got {ev[:4]})')
        gapmax = 1.5 if typ == 'app' else 2.0; endt = (vis[0] if vis else dur)
        pts = [0] + [e for e in ev if e < endt] + [endt]; gaps = [(a, b) for a, b in zip(pts, pts[1:]) if b - a > gapmax and not inhold(a, b)]
        for a, b in gaps[:6]: rep('FAIL', 'visual events', f'no visual event {a:.1f}–{b:.1f} s ({b - a:.1f} s > {gapmax})')
        if moving0 and first and second and not gaps: rep('PASS', 'visual events', f'{len(ev)} events, max gap ≤{gapmax} s')
        # layout held >3.5 s: big change (>15%) vs 0.5 s earlier
        big = sorted([tt[i] for i in range(5, len(G)) if float(((np.abs(G[i] - G[i - 5]) > 20) & mask).mean()) > .15] + [x for x in (M.get('scenes') or []) if x > 0])
        pts2 = [0] + big + [endt]; lh = [(a, b) for a, b in zip(pts2, pts2[1:]) if b - a > 3.5 and not inhold(a, b)]
        for a, b in lh[:4]: rep('FAIL', 'visual events', f'same layout held {a:.1f}–{b:.1f} s (>3.5 s)')
        # shot rate (his rule 3, 1 Nov 2026): a new shot every 0.7–1.0 s
        sc = sorted(set([tt[i] for i in range(3, len(G)) if float(((np.abs(G[i] - G[i - 3]) > 20) & mask).mean()) > .12] + [x for x in (M.get('scenes') or []) if x > 0]))
        cuts = [0.0]
        for x in sc:
            if x - cuts[-1] >= .35: cuts.append(x)
        pts3 = cuts + [endt]; sg = [(a, b) for a, b in zip(pts3, pts3[1:]) if b - a > 1.0 and not inhold(a, b)]
        avg = endt / max(1, len(cuts))
        bad = [(a, b) for a, b in sg if b - a > 1.2]
        for a, b in bad[:6]: rep('FAIL', 'shot rate', f'same shot {a:.1f}–{b:.1f} s ({b - a:.1f} s > 1.2) — need a new shot every 0.7–1 s')
        if not bad: rep('WARN' if (sg or avg > .9) else 'PASS', 'shot rate', f'{len(cuts)} shots, avg {avg:.2f} s' + (f', {len(sg)} shots >1.0 s' if sg else ''))
        # motion coverage (his rule: always moving) — share of 0.1 s steps with visible change, before the end card
        steps = [c for i, c in enumerate(ch) if tt[i + 1] < endt]
        cov = sum(c > .003 for c in steps) / max(1, len(steps))
        rep('FAIL' if cov < .90 else 'WARN' if cov < .95 else 'PASS', 'motion coverage', f'{cov * 100:.0f}% of 0.1 s steps move (need ≥90%, target ≥95%)')
        # frozen
        run = 0; frz = []
        for i, c in enumerate(ch):
            run = run + .1 if c < .01 else 0
            if run >= 1.5 and not inhold(tt[i + 1] - run, tt[i + 1]) and tt[i + 1] < endt: frz.append(round(tt[i + 1], 1)); run = 0
        rep('FAIL' if frz else 'PASS', 'frozen render', f'≥1.5 s with almost no change ending at {frz[:4]}' if frz else 'no frozen stretch')
        # fill at 2 fps
        thin = []
        for i in range(0, len(frames), 15):
            g = gray_small(frames[i])[12:163, :96]; bg = np.median(g)
            blk = g[:150].reshape(30, 5, 32, 3).transpose(0, 2, 1, 3).reshape(30, 32, 15)
            cont = (blk.std(-1) > 6) | (np.abs(blk.mean(-1) - bg) > 22); tot = cont.mean(); top = cont[:15].mean(); bot = cont[15:].mean()
            if (tot < .45 or top < .15 or bot < .15) and i / fps < endt: thin.append((round(i / fps, 1), round(tot * 100), round(top * 100), round(bot * 100)))
        for t, a, tp, bt in thin[:6]: rep('FAIL', 'fill', f'{t}s content {a}% (top {tp}%, bottom {bt}%) — need ≥45%, each half ≥15%')
        if not thin: rep('PASS', 'fill', 'frames well filled')
    else: rep('FAIL', 'frames', 'no frames/ — run render.py frames first')
    # ---- audio
    A = D + '/aud'
    if all(os.path.exists(f'{A}/{s}.wav') for s in ('mix', 'stem_vo', 'stem_music', 'stem_sfx')):
        r = subprocess.run(['ffmpeg', '-hide_banner', '-i', f'{A}/mix.wav', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
        I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); tp = float(re.findall(r'Peak:\s+(-?[\d.]+|-inf) dBFS', r)[-1])
        def ld(p):
            from scipy.io import wavfile
            sr, x = wavfile.read(p); x = x.astype(np.float64); return sr, (x[:, 0] if x.ndim > 1 else x)
        sr, vo = ld(f'{A}/stem_vo.wav'); _, mu = ld(f'{A}/stem_music.wav'); _, sx = ld(f'{A}/stem_sfx.wav')
        k = int(sr * .04); e = np.convolve(np.abs(vo), np.ones(k) / k, 'same'); sp = e > np.percentile(e[e > 1e-4], 40) * .5
        rms = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-12; under = 20 * np.log10(rms(vo[sp]) / rms(mu[sp]))
        start = np.argmax(np.abs(vo) > .02) / sr
        if tp > -1.0: rep('FAIL', 'audio', f'true peak {tp} dBTP (> −1.0)')
        if not 14 <= under <= 20: rep('FAIL', 'audio', f'music {under:.1f} dB under voice (need 14–20)')
        if np.max(np.abs(sx)) >= np.max(np.abs(mu)) and np.max(np.abs(sx)) > 0: rep('FAIL', 'audio', 'SFX peak ≥ music peak')
        if start > .2: rep('FAIL', 'audio', f'voice starts at {start:.2f} s (need ≤0.2)')
        if not -17.5 <= I <= -14.5: rep('WARN', 'audio', f'integrated {I} LUFS (target −16 ± 1.5)')
        if tp <= -1.0 and 14 <= under <= 20 and start <= .2: rep('PASS', 'audio', f'{I} LUFS, TP {tp}, music {under:.1f} dB under, voice at {start:.2f}s')
        cues = sorted(c[0] for c in meta.get('sfx', []))
        if not cues and np.max(np.abs(sx)) > 0:
            k2 = int(sr * .02); env = np.convolve(np.abs(sx), np.ones(k2) / k2, 'same'); thr = env.max() * .25; cues = []
            for i in np.where((env[1:] > thr) & (env[:-1] <= thr))[0]:
                if not cues or i / sr - cues[-1] > .12: cues.append(i / sr)
        dense = [c for c in cues if sum(c <= x < c + 3 for x in cues) > 3]
        if len(cues) > dur / 1.5 + 1 or dense: rep('FAIL', 'SFX density', f'{len(cues)} cues in {dur:.0f} s' + (f', crowded near {dense[0]:.1f}s' if dense else ''))
        else: rep('PASS', 'SFX density', f'{len(cues)} cues')
    else: rep('FAIL', 'audio', 'stems missing — run mix.py')
    # voice vs script
    if os.path.exists(D + '/transcript.txt') and os.path.exists(D + '/script.json'):
        a = re.findall(r'[\u0900-\u097F]+', re.sub(r'\[[^\]]+\]', ' ', json.load(open(D + '/script.json', encoding='utf-8'))['voice']))
        b = re.findall(r'[\u0900-\u097F]+', open(D + '/transcript.txt', encoding='utf-8').read())
        diff = 1 - difflib.SequenceMatcher(None, a, b).ratio()
        rep('FAIL' if diff > .10 else 'WARN' if diff > .05 else 'PASS', 'voice↔script', f'{diff * 100:.0f}% different')
    else: rep('WARN', 'voice↔script', 'skipped (needs transcript.txt + script.json)')
    finish(D)
if __name__ == '__main__':
    if sys.argv[1] == '--script': lint_script(os.path.abspath(sys.argv[2]))
    else:
        typ = sys.argv[sys.argv.index('--type') + 1] if '--type' in sys.argv else None
        lint_reel(os.path.abspath(sys.argv[1]), typ)
