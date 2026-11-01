/* AstroCheck Reel Kit — motion engine. Every reel: include kit.css + motionkit.js + timing.js + scenes.js.
   scenes.js calls MK.setup({...}) once and defines REEL.render(t) which ends with MK.render(t).
   Lint reads: window.MK_META, window.MK_EVENTS, window.SFX, data-role attributes. */
(function () {
  const cl = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const prog = (t, a, b) => (b === a ? (t >= b ? 1 : 0) : cl((t - a) / (b - a)));
  const lerp = (a, b, p) => a + (b - a) * p;
  const ease = {
    lin: p => p,
    io: p => (p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2),
    out: p => 1 - Math.pow(1 - p, 3),
    in: p => p * p * p,
    back: p => { const c = 1.4, c3 = c + 1; return 1 + c3 * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
  };
  const $ = s => document.querySelector(s);
  /* keyframes: keys = [[t, v] or [t, [v1,v2..]]], eased between neighbours */
  function kf(t, keys, e = ease.io) {
    if (t <= keys[0][0]) return keys[0][1];
    for (let i = 1; i < keys.length; i++) {
      const [ta, va] = keys[i - 1], [tb, vb] = keys[i];
      if (t <= tb) {
        const p = e(prog(t, ta, tb));
        return Array.isArray(va) ? va.map((x, j) => lerp(x, vb[j], p)) : lerp(va, vb, p);
      }
    }
    return keys[keys.length - 1][1];
  }
  /* set: {x,y,s,r,o,blur} */
  function set(el, o) {
    if (typeof el === 'string') el = $(el);
    if (!el) return;
    const x = o.x || 0, y = o.y || 0, s = o.s == null ? 1 : o.s, r = o.r || 0;
    el.style.transform = `translate(${x}px,${y}px) scale(${s}) rotate(${r}deg)`;
    if (o.o != null) el.style.opacity = o.o;
    if (o.blur != null) el.style.filter = o.blur > 0.05 ? `blur(${o.blur}px)` : '';
  }
  /* reveal: 0..1 progress with optional rise */
  function pop(el, t, at, d = .35, rise = 30) { const p = ease.back(prog(t, at, at + d)); set(el, { y: (1 - p) * rise, s: .86 + .14 * p, o: cl(prog(t, at, at + d * .5)) }); return p; }
  function fade(el, t, at, d = .3) { const p = ease.out(prog(t, at, at + d)); set(el, { o: p, y: (1 - p) * 24 }); return p; }
  /* camera: gentle push-in (<=1.06) with parallax layers [[el, depth]] */
  function camera(el, t, a, b, s0 = 1, s1 = 1.05, dx = 0, dy = 0) {
    const p = ease.io(prog(t, a, b)); const s = Math.min(1.06, lerp(s0, s1, p));
    set(el, { s, x: dx * p, y: dy * p, o: 1 });
    return p;
  }
  /* punch: eased punch-in <=1.08 over >=0.2 s (6 frames) */
  function punch(t, at, amt = 1.06, d = .5) { const p = prog(t, at, at + d); return 1 + (Math.min(amt, 1.08) - 1) * Math.sin(Math.PI * cl(p)); }
  /* transitions between scenes (no whip pans). Returns {outP,inP}. Types: fade, rise, iris, wipe, zoom */
  function tr(type, outEl, inEl, t, at, d = .45) {
    const p = ease.io(prog(t, at, at + d));
    if (typeof outEl === 'string') outEl = $(outEl);
    if (typeof inEl === 'string') inEl = $(inEl);
    if (t < at) { if (outEl) { outEl.style.opacity = 1; } if (inEl) inEl.style.opacity = 0; return; }
    if (t > at + d) { if (outEl) outEl.style.opacity = 0; if (inEl) { inEl.style.opacity = 1; inEl.style.clipPath = ''; } return; }
    if (inEl) { inEl.style.opacity = 1; inEl.style.clipPath = ''; }
    if (type === 'fade') { if (outEl) outEl.style.opacity = 1 - p; if (inEl) inEl.style.opacity = p; }
    else if (type === 'rise') { if (outEl) set(outEl, { y: -80 * p, o: 1 - p, blur: 8 * p }); if (inEl) set(inEl, { y: 120 * (1 - p), o: p, blur: 8 * (1 - p) }); }
    else if (type === 'iris') { if (outEl) outEl.style.opacity = 1; if (inEl) inEl.style.clipPath = `circle(${p * 125}% at 50% 46%)`; }
    else if (type === 'wipe') { if (outEl) outEl.style.opacity = 1; if (inEl) { const k = -40 + p * 180; inEl.style.clipPath = `polygon(0 0,${k}% 0,${k - 30}% 100%,0 100%)`; } }
    else if (type === 'zoom') { if (outEl) set(outEl, { s: 1 + .12 * p, o: 1 - p }); if (inEl) set(inEl, { s: .92 + .08 * p, o: p }); }
  }
  /* scenes: list [[id, startTime, transitionType, dur], ...] (first start 0). Shows exactly one scene except during a transition. */
  function scenes(t, list) {
    if (!META.scenes) META.scenes = list.map(s => +s[1].toFixed(3));
    let k = 0; list.forEach((s, i) => { if (t >= s[1]) k = i; });
    list.forEach((s, i) => { const e = $('#' + s[0]); if (!e) return; if (i !== k && i !== k - 1) { e.style.opacity = 0; e.style.visibility = 'hidden'; } });
    const cur = list[k], prev = list[k - 1], ce = $('#' + cur[0]); ce.style.visibility = 'visible';
    const d = cur[3] || .4;
    if (prev && t < cur[1] + d) { const pe = $('#' + prev[0]); pe.style.visibility = 'visible'; tr(cur[2] || 'fade', pe, ce, t, cur[1], d); }
    else { if (prev) { const pe = $('#' + prev[0]); pe.style.opacity = 0; pe.style.visibility = 'hidden'; } ce.style.opacity = 1; ce.style.transform = ''; ce.style.filter = ''; ce.style.clipPath = ''; }
    return k;
  }
  /* ---------------- meta, events, sfx cues ---------------- */
  const META = window.MK_META = { type: 'placement', mythbust: false, captionsFrom: 3, ctaAt: null, endAt: null, dur: 0, hold: null };
  const EVENTS = window.MK_EVENTS = [];
  const SFX = window.SFX = [];
  function event(t, label) { EVENTS.push([+t.toFixed(3), label || 'ev']); }
  function cue(t, name, gain = 1) { SFX.push([+t.toFixed(3), name, gain]); }
  /* ---------------- captions ---------------- */
  let CH = [];
  function buildChunks(words, from) {
    const out = []; let cur = [];
    const flush = () => { if (cur.length) { out.push({ a: cur[0].a, b: cur[cur.length - 1].b, w: cur }); cur = []; } };
    words.filter(w => w.a >= from - .01 && !/^[—–-]+$/.test(w.w)).forEach((w, i, arr) => {
      cur.push(w);
      const nx = arr[i + 1];
      const punct = /[,.?!…—]$/.test(w.w);
      if (cur.length >= 4 || (punct && cur.length >= 2) || (nx && nx.a - w.b > .25 && cur.length >= 2) || (cur.length >= 2 && w.w.length > 9) || (punct && /[.?!]$/.test(w.w))) flush();
    });
    flush();
    out.forEach((c, i) => { c.end = out[i + 1] ? out[i + 1].a : c.b + .4; });
    return out;
  }
  function renderCaptions(t) {
    const box = $('#mk-cap'); if (!box) return;
    const end = META.endAt == null ? 1e9 : META.endAt;
    const c = CH.find(c => t >= c.a - .04 && t < c.end);
    if (!c || t >= end) { box.innerHTML = ''; box.style.opacity = 0; return; }
    box.style.opacity = 1;
    if (box.dataset.k !== String(c.a)) {
      box.dataset.k = String(c.a);
      box.innerHTML = '<div class="line" data-role="caption">' + c.w.map((w, i) => `<span class="w${w.key ? ' k' : ''}" data-i="${i}">${w.w}</span>`).join(' ') + '</div>';
    }
    box.querySelectorAll('.w').forEach((el, i) => {
      const w = c.w[i]; const p = prog(t, w.a, w.a + .2);
      const s = w.key ? 1 + .08 * Math.sin(Math.PI * p) : 1;
      el.style.transform = `scale(${s})`;
      el.style.opacity = t >= w.a - .05 ? 1 : .55;
    });
  }
  /* ---------------- URL tag -> chip ---------------- */
  let URLCFG = null;
  function renderUrl(t) {
    const el = $('#mk-url'); if (!el || !URLCFG) return;
    const cta = META.ctaAt == null ? 1e9 : META.ctaAt, end = META.endAt == null ? 1e9 : META.endAt;
    const p = ease.io(prog(t, cta - .1, cta + .45));
    // tag geometry (badge row, right side) -> chip geometry (chip zone, centered in 60..960)
    const tag = { w: 400, h: 76, x: 960 - 400, y: 148, f: 46 }, chip = { w: 860, h: 160, x: 80, y: 1450, f: 56 };
    const w = lerp(tag.w, chip.w, p), h = lerp(tag.h, chip.h, p), x = lerp(tag.x, chip.x, p), y = lerp(tag.y, chip.y, p);
    Object.assign(el.style, { width: w + 'px', height: h + 'px', left: x + 'px', top: y + 'px', fontSize: lerp(tag.f, chip.f, p) + 'px' });
    el.querySelector('.free').style.display = p > .5 ? '' : 'none';
    el.querySelector('.dot').style.display = 'none';
    el.style.flexDirection = p > .5 ? 'column' : 'row'; el.style.lineHeight = p > .5 ? '1.08' : '1'; el.style.gap = p > .5 ? '0' : '14px';
    const sp = t > cta + .45 ? 1 + .03 * Math.sin((t - cta) * 5) : 1;
    el.style.transform = `scale(${sp})`;
    el.style.opacity = t >= end - .15 ? Math.max(0, 1 - (t - end + .15) / .15) : 1;
    el.style.visibility = el.style.opacity < .02 ? 'hidden' : 'visible';
  }
  /* ---------------- end card ---------------- */
  function renderEnd(t) {
    const el = $('#mk-end'); if (!el || META.endAt == null) return;
    const p = ease.back(prog(t, META.endAt, META.endAt + .35));
    el.style.opacity = cl(prog(t, META.endAt, META.endAt + .15));
    el.style.transform = `translateY(${(1 - p) * 60}px) scale(${.94 + .06 * p})`;
    el.style.visibility = t < META.endAt ? 'hidden' : 'visible';
  }
  const ICON = {
    ig: '<svg viewBox="0 0 24 24"><rect x="2.5" y="2.5" width="19" height="19" rx="5.5" fill="none" stroke="currentColor" stroke-width="2.2"/><circle cx="12" cy="12" r="4.3" fill="none" stroke="currentColor" stroke-width="2.2"/><circle cx="17.6" cy="6.4" r="1.4" fill="currentColor"/></svg>',
    yt: '<svg viewBox="0 0 24 24"><rect x="1.5" y="5" width="21" height="14" rx="4" fill="currentColor"/><path d="M10 9l5 3-5 3z" fill="var(--panel)"/></svg>',
    fb: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10.5" fill="currentColor"/><path d="M13.3 19v-6h2l.3-2.4h-2.3V9.2c0-.7.2-1.2 1.2-1.2h1.2V5.9a16 16 0 0 0-1.8-.1c-1.8 0-3 1.1-3 3.1v1.7H9v2.4h2v6z" fill="var(--panel)"/></svg>',
  };
  /* ---------------- setup ---------------- */
  function setup(o) {
    Object.assign(META, o.meta || {});
    META.dur = window.DUR || META.dur;
    if (o.skin) document.body.classList.add('skin' + o.skin);
    if (/guides=1/.test(location.search)) document.body.classList.add('guides');
    const st = $('#st');
    // badge
    if (o.badge) { const b = document.createElement('div'); b.id = 'mk-badge'; b.dataset.role = 'badge'; b.innerHTML = o.badge; st.appendChild(b); }
    // captions
    const cap = document.createElement('div'); cap.id = 'mk-cap'; st.appendChild(cap);
    CH = buildChunks(o.words || window.WORDS || [], META.captionsFrom);
    // url element
    if (o.url) {
      URLCFG = o.url; const u = document.createElement('div'); u.id = 'mk-url'; u.dataset.role = 'url';
      u.innerHTML = `<span class="free">FREE ${o.url.tool}</span><span class="dot">·</span><span>astrocheck.app</span>`; st.appendChild(u);
    }
    // end card
    if (o.end) {
      const e = document.createElement('div'); e.id = 'mk-end'; e.dataset.role = 'endcard';
      e.innerHTML = `<img src="kit/icon.png" alt=""><div class="tool">${o.end.tool || ''}</div><div class="url" data-role="url">astrocheck.app</div>
        <div class="hd" data-role="handles"><span>${ICON.ig}@astrocheckk</span><span>${ICON.yt}@AstrocheckApp</span><span>${ICON.fb}AstroCheck</span></div>
        ${o.end.next ? `<div class="next">${o.end.next}</div>` : ''}${o.end.disc ? `<div class="disc">${o.end.disc}</div>` : ''}`;
      st.appendChild(e);
    }
    const v = document.createElement('div'); v.id = 'mk-vig'; st.appendChild(v);
    const g = document.createElement('div'); g.id = 'mk-guides';
    g.innerHTML = [[120, '120 no key text'], [260, '260 title'], [620, '620 hero'], [1150, '1150 captions'], [1420, '1420'], [1440, '1440 chip'], [1632, '1632 nothing below']].map(([y, s]) => `<i style="top:${y}px">${s}</i>`).join('') + '<u></u>';
    st.appendChild(g);
  }
  function render(t) { renderCaptions(t); renderUrl(t); renderEnd(t); }
  window.MK = { scenes, cl, prog, lerp, ease, kf, set, pop, fade, camera, punch, tr, event, cue, setup, render, $ };
})();
