"""Code-synth SFX library -> kit/sfx/*.wav (48 kHz mono). Short, sharp transients with 2–5 kHz presence."""
import numpy as np, os
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
SR = 48000; R = os.path.dirname(os.path.abspath(__file__)); rng = np.random.default_rng(11)
tt = lambda d: np.arange(int(SR * d)) / SR
f = lambda x, k, c, o=2: sosfilt(butter(o, c, k, fs=SR, output='sos'), x)
def norm(x, pk=.9): return x / (np.max(np.abs(x)) or 1) * pk
def thud():
    t = tt(.45); body = np.sin(2*np.pi*np.cumsum(60+110*np.exp(-t*35))/SR)*np.exp(-t*10)
    click = f(rng.standard_normal(len(t)), 'band', [2000, 5000]) * np.exp(-t*90) * .5; return body + click
def pop():
    t = tt(.16); return np.sin(2*np.pi*np.cumsum(900+1400*np.exp(-t*60))/SR)*np.exp(-t*30) + f(rng.standard_normal(len(t)),'band',[2500,5000])*np.exp(-t*120)*.3
def tick():
    t = tt(.08); return f(rng.standard_normal(len(t)), 'band', [3000, 5500]) * np.exp(-t * 140) + np.sin(2*np.pi*3200*t)*np.exp(-t*90)*.4
def paper():
    t = tt(.32); n = f(rng.standard_normal(len(t)), 'band', [1800, 6500]); return n * np.exp(-t * 14) * (.55 + .45 * np.abs(np.sin(2*np.pi*35*t)))
def stamp():
    t = tt(.45); return thud() * .9 + f(rng.standard_normal(len(t)), 'band', [2000, 4500]) * np.exp(-t * 60) * .6
def whoosh():
    t = tt(.5); n = rng.standard_normal(len(t)); env = np.sin(np.pi * t / .5) ** 2
    lo = f(n, 'band', [500, 2500]) * env * (1 - t / .5); hi = f(n, 'band', [2500, 6000]) * env * (t / .5); return lo + hi
def riser():
    t = tt(1.2); n = f(rng.standard_normal(len(t)), 'band', [1500, 6000]) * (t / 1.2) ** 2
    tone = np.sin(2*np.pi*np.cumsum(300 + 900 * t / 1.2)/SR) * (t / 1.2) ** 2 * .3; return n * .6 + tone
def sparkle():
    t = tt(.9); x = np.zeros(len(t))
    for i, fr in enumerate([1568, 2093, 2637, 3136]):
        a = int(i * .07 * SR); tt2 = t[:len(t) - a]; x[a:] += np.sin(2*np.pi*fr*tt2) * np.exp(-tt2 * 7) * .5
    return x
def chime():
    t = tt(1.0); return (np.sin(2*np.pi*784*t) + .5*np.sin(2*np.pi*1568*t) + .25*np.sin(2*np.pi*2352*t)) * np.exp(-t * 4) * np.minimum(1, t / .003)
os.makedirs(R + '/sfx', exist_ok=True)
for name, fn in [('thud', thud), ('pop', pop), ('tick', tick), ('paper', paper), ('stamp', stamp), ('whoosh', whoosh), ('riser', riser), ('sparkle', sparkle), ('chime', chime)]:
    wavfile.write(f'{R}/sfx/{name}.wav', SR, norm(fn()).astype(np.float32))
print(sorted(os.listdir(R + '/sfx')))
