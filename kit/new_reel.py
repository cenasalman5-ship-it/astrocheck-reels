"""Start a reel folder on the kit: python3 kit/new_reel.py <folder>
Creates <folder>/reel.html (from template), scenes.js stub, aud/, and a 'kit' symlink."""
import os, sys, shutil
K = os.path.dirname(os.path.abspath(__file__)); d = os.path.abspath(sys.argv[1]); os.makedirs(d + '/aud', exist_ok=True)
if not os.path.exists(d + '/kit'): os.symlink(K, d + '/kit')
if not os.path.exists(d + '/reel.html'): shutil.copy(K + '/template.html', d + '/reel.html')
if not os.path.exists(d + '/scenes.js'):
    open(d + '/scenes.js', 'w').write("""// MK.setup once, then REEL.render(t). Times come from timing.js (W = segment starts/ends, WORDS = word timings).
MK.setup({meta:{type:'placement', mythbust:true, captionsFrom:W.HOOK_END, ctaAt:W.CTA, endAt:W.END},
  badge:'108 KA KHAZANA · <b>PART N</b>', url:{tool:'Kundli'}, skin:1,
  end:{tool:'FREE Kundli · Manglik jaanch', next:'Part N+1 kal — follow karo', disc:'Sirf margdarshan, guarantee nahi'}});
window.REEL={render(t){ /* scenes here */ MK.render(t);}};
""")
print('ready:', d)
