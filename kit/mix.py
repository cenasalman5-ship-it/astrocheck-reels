"""Mix voice + music + SFX for a kit reel (run AFTER render.py frames, which writes meta.json with the SFX cues).
  python3 kit/mix.py <reel_dir> <music.wav|mp3> [under_db=16]
Owner rules: music soft (14–20 dB under the voice, ducked while speaking), SFX always quieter than the music
(limited ~12 dB under the music envelope), true peak <= -1 dBTP, integrated ~ -16 LUFS.
Writes aud/stem_vo.wav, stem_music.wav, stem_sfx.wav, mix.wav."""
import sys, os, json, subprocess, re, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, resample_poly
SR = 48000; K = os.path.dirname(os.path.abspath(__file__))
D = os.path.abspath(sys.argv[1]); MUS = sys.argv[2]; UNDER = float(sys.argv[3]) if len(sys.argv) > 3 else 16
meta = json.load(open(D + '/meta.json')); DUR = float(meta['dur']); N = int(SR * DUR)
TJ = open(D + '/timing.js').read(); OFF = float(re.search(r'window\.OFF=([\d.]+)', TJ).group(1))
def load(p): return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',p,'-f','f32le','-ac','1','-ar',str(SR),'-'],capture_output=True).stdout,np.float32).astype(np.float64)
def flt(x, k, c, o=2): return sosfilt(butter(o, c, k, fs=SR, output='sos'), x)
def put(buf, x, t, g=1.0):
    i = int(round(t * SR)); 
    if i < 0: x = x[-i:]; i = 0
    if i >= len(buf): return
    n = min(len(x), len(buf) - i); buf[i:i + n] += x[:n] * g
rms = lambda x: np.sqrt(np.mean(x ** 2)) + 1e-12; db = lambda x: 20 * np.log10(rms(x))
# voice
vo = np.zeros(N); put(vo, load(D + '/aud/vo.wav'), OFF); vo = flt(vo, 'high', 85); vo = vo + flt(vo, 'band', [2500, 5200]) * .18
a = int(SR * .04); e = np.convolve(np.abs(vo), np.ones(a) / a, 'same'); ref = np.percentile(e[e > 1e-4], 40); on = np.clip(e / ref, 0, 1); sp = on > .5
duck = 1 - .45 * on; k1 = int(SR * .2); duck = np.convolve(duck, np.ones(k1) / k1, 'same')
vo = vo / np.max(np.abs(vo)) * .9
# music (looped with crossfade, fade in/out)
m = load(MUS); music = np.zeros(N); L = len(m); X = int(SR * 2.0); pos = 0
while pos < N:
    seg = m.copy()
    if pos > 0: seg[:X] *= np.linspace(0, 1, X)
    if pos + L < N: seg[-X:] *= np.linspace(1, 0, X)
    put(music, seg, pos / SR); pos += max(L - X, SR)
fi = int(SR * .3); music[:fi] *= np.linspace(0, 1, fi); fo = int(SR * 1.0); music[-fo:] *= np.linspace(1, 0, fo)
music *= duck; music *= 10 ** ((db(vo[sp]) - UNDER - db(music[sp])) / 20)
# sfx cues
sfx = np.zeros(N); lib = {}
for t, name, g in meta.get('sfx') or []:
    if name not in lib: lib[name] = load(f'{K}/sfx/{name}.wav')
    put(sfx, lib[name], t, g)
if np.max(np.abs(sfx)) > 0:
    def env(x, w): k = int(SR * w); return np.sqrt(np.convolve(x ** 2, np.ones(k) / k, 'same')) + 1e-6
    me = env(music / np.maximum(duck, 1e-3), .4); sfx = sfx / np.max(np.abs(sfx)) * np.max(np.abs(music)) * .7
    se = env(sfx, .05); g = np.minimum(1, 10 ** (-12 / 20) * me / se); kk = int(SR * .03); sfx *= np.convolve(g, np.ones(kk) / kk, 'same')
    if np.max(np.abs(sfx)) >= .9 * np.max(np.abs(music)): sfx *= .9 * np.max(np.abs(music)) / np.max(np.abs(sfx))
sfx[-fo:] *= np.linspace(1, 0, fo)
mix = vo + music + sfx
# loudness to ~-16 LUFS, then true-peak safety (-1.5 dBTP)
def lufs(x):
    p = D + '/aud/_tmp.wav'; wavfile.write(p, SR, np.stack([x, x], 1).astype(np.float32))
    r = subprocess.run(['ffmpeg','-hide_banner','-i',p,'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
    os.remove(p); return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1])
gain = 10 ** ((-16 - lufs(mix)) / 20); vo, music, sfx = vo * gain, music * gain, sfx * gain; mix = vo + music + sfx
tp = np.max(np.abs(resample_poly(mix, 4, 1))); lim = 10 ** (-1.5 / 20)
if tp > lim: s = lim / tp; vo, music, sfx, mix = vo * s, music * s, sfx * s, mix * s
for name, x in (('stem_vo', vo), ('stem_music', music), ('stem_sfx', sfx), ('mix', mix)):
    wavfile.write(f'{D}/aud/{name}.wav', SR, np.stack([x, x], 1).astype(np.float32))
print('voice', round(db(vo[sp]), 1), 'music under voice', round(db(vo[sp]) - db(music[sp]), 1), 'dB · sfx cues', len(meta.get('sfx') or []), '· LUFS', round(lufs(mix), 1))
