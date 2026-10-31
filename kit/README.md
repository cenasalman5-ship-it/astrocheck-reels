# AstroCheck Reel Kit

Engine for the daily AstroCheck reels (the look changes every day; this kit only removes repeat work and catches mistakes).

## Daily flow for one reel
```bash
python3 kit/new_reel.py <dir>                 # reel.html (zones + theme tokens), scenes.js stub, kit symlink
# write <dir>/script.json  {"type":"placement|rashi|app","mythbust":true,"voice":"देवनागरी … [M7-A5]","cap_roman":"…","screen_text":"…"}
python3 kit/lint.py --script <dir>             # word count, banned/filler words, Bunty misreads, fact-card IDs + hedges
# generate ONE voice take (ElevenLabs), transcribe it (scribe), curl the mp3 to <dir>/aud/raw.mp3
# write <dir>/segs.json (segments in raw time + Roman caption text, *key* words, drop list, scribe_words)
python3 kit/vo.py <dir> segs.json              # tight voice (gaps 0.15 s, tempo) + timing.js (W, WORDS, DUR)
# build scenes in reel.html / scenes.js with MK.setup + MK.scenes + data-role marks (hook, hero, verdict, climax, cta, grah, dive-grah)
GUIDES=1 python3 kit/render.py <dir> preview 0,0.6,1.2,…   # zone guide lines on
python3 kit/render.py <dir> frames 30 3        # frames + meta.json (events, SFX cues)
python3 kit/mix.py <dir> <music> 16            # voice + music 16 dB under + SFX under music, −16 LUFS, TP ≤ −1.5
python3 kit/lint.py <dir>                      # must PASS before QA (write transcript.txt from scribe for the voice check)
python3 kit/contact_sheet.py <dir>             # qa/sheet_0-2s.jpg (6 fps) + qa/sheet_full.jpg (2 fps) for the QA agents
python3 kit/render.py <dir> encode <out.mp4>
python3 kit/stills.py <dir> carousel slides.json · python3 kit/stills.py <dir> story <t> "<big>" "<small>"
```

## Files
- `kit.css`, `template.html`, `motionkit.js` — zones, captions (3 skins), URL tag→chip, series badge, end card, camera/punch/transitions, scene manager
- `render.py`, `mix.py`, `vo.py`, `contact_sheet.py`, `stills.py`, `new_reel.py`
- `lint.py` + `words/` — the code gate (thresholds = SKILL.md section 8)
- `sfx/` (from `sfx_gen.py`), `fonts/`, `icon.png`
- `astro_tables.py/.json` — exact drishti + lagna dignity tables; `khazana-cards.json` — verified facts for the 108 series (`khazana-audit.md` = jyotishi audit log)

Acceptance test (1 Nov 2026): the old Mangal 7th reel FAILS lint (41 fails); the same voice rebuilt on the kit PASSES (0 fail, 0 warn).
