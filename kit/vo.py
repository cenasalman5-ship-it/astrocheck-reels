"""Tighten the one-take voice and write timing.js for a kit reel.
  python3 kit/vo.py <reel_dir> segs.json
segs.json = {"raw":"aud/raw.mp3", "tempo":1.08, "off":0.15, "tail":0.6, "pause_before":"climax",
  "segs":[{"name":"hook","a":0.02,"b":2.82,"cap":"Agar aapki *kundli* me *Mangal* saatve ghar me hai"}, ...],
  "drop":["ruko"], "scribe_words":[{"text":..,"start":..,"end":..}] (optional, raw time)}
- gaps between kept segments: >0.25 s -> 0.15 s (after tempo); one pause <=0.4 s before 'pause_before' segment
- caption words: Roman 'cap' text per segment, *word* = key word (accent colour). Timed from scribe words if the
  count matches inside the segment, else spread by letter count across the segment.
Writes aud/vo.wav, timing.js (W = {name, name_e} final times, WORDS, DUR, OFF)."""
import sys, os, json, subprocess, numpy as np
from scipy.io import wavfile
SR = 48000
D = os.path.abspath(sys.argv[1]); C = json.load(open(os.path.join(D, sys.argv[2])))
def load(p): return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True).stdout,np.float32).astype(np.float64)
x = load(os.path.join(D, C['raw'])); TEMPO = C.get('tempo', 1.08); OFF = C.get('off', .15); M = .04
segs = [s for s in C['segs'] if s['name'] not in C.get('drop', [])]
out = []; T = {}; pos = 0; spans = []
for i, s in enumerate(segs):
    a, b = s['a'], s['b']; seg = x[int(max(0, a - M) * SR):int((b + M) * SR)].copy(); n = int(SR * .012)
    seg[:n] *= np.linspace(0, 1, n); seg[-n:] *= np.linspace(1, 0, n)
    T[s['name']] = pos + M; spans.append((s, pos + M, a)); out.append(seg); pos += len(seg) / SR; T[s['name'] + '_e'] = pos - M
    if i + 1 < len(segs):
        nxt = segs[i + 1]; raw_gap = nxt['a'] - b
        g = min(raw_gap, .15 * TEMPO) if raw_gap > .25 * TEMPO else raw_gap
        if nxt['name'] == C.get('pause_before'): g = min(max(raw_gap, .25 * TEMPO), .4 * TEMPO)
        g = max(0, g - 2 * M); out.append(np.zeros(int(g * SR))); pos += g
os.makedirs(D + '/aud', exist_ok=True)
wavfile.write(D + '/aud/vo_tight.wav', SR, np.concatenate(out).astype(np.float32))
subprocess.run(['ffmpeg','-v','error','-y','-i',D+'/aud/vo_tight.wav','-filter:a',f'atempo={TEMPO}',D+'/aud/vo.wav'], check=True)
W = {k: round(v / TEMPO + OFF, 3) for k, v in T.items()}
SW = C.get('scribe_words') or []
WORDS = []
for s, start_tight, raw_a in spans:
    toks = s.get('cap', '').split()
    if not toks: continue
    a, b = W[s['name']], W[s['name'] + '_e']
    inside = [w for w in SW if s['a'] - .05 <= w['start'] < s['b']]
    if len(inside) == len(toks):
        tm = [((w['start'] - raw_a + start_tight) / TEMPO + OFF, (w['end'] - raw_a + start_tight) / TEMPO + OFF) for w in inside]
    else:
        L = [len(t.strip('*')) + 2 for t in toks]; tot = sum(L); acc = 0; tm = []
        for l in L: tm.append((a + (b - a) * acc / tot, a + (b - a) * (acc + l) / tot)); acc += l
    for tok, (ta, tb) in zip(toks, tm):
        WORDS.append({'w': tok.replace('*', ''), 'a': round(ta, 3), 'b': round(tb, 3), 'key': '*' in tok})
last = segs[-1]['name']; DUR = round(W[last + '_e'] + C.get('tail', .6), 2)
open(D + '/timing.js', 'w').write('window.W=' + json.dumps(W) + ';window.WORDS=' + json.dumps(WORDS, ensure_ascii=False) + f';window.DUR={DUR};window.OFF={OFF};')
print('DUR', DUR); print({k: v for k, v in W.items() if not k.endswith('_e')})
