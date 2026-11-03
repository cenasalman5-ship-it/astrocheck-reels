/* AstroCheck Reel Kit — SHOT ENGINE (the style he approved on 2 Nov 2026: "haaan sahi hai").
   Every key word = a NEW full-screen shot with its own background world, moving pattern and camera move.
   Load after motionkit.js + motion3d.js. Needs <div id="shots"></div><div id="flash"></div><canvas id="near"> in #st.

   Use:
     const WT = i => WORDS[i].a;                     // word onset (s) from timing.js
     SK.def('s1', {bg:['#3a1c71','#1a0b3a'], pats:['rays','stars'], cam:'push',
                   html:`<div class="big" style="top:300px" data-in="pop" data-role="hook">…</div>
                         <div class="hero" style="top:640px;width:560px" data-in="zoom" data-float="10">${SK.planet('गु',…)}</div>`,
                   anim:(lt, el, t, d) => {...}});
     SK.cut([[0,'s1'], [WT(4)-.02,'s2',{tr:'flash'}], …]);   // after all defs (cut times = word onset − 0.02 s)
     window.REEL = {render(t){ SK.render(t); MK.render(t); }};
   data-in: pop | zoom | rise | drop | slideL | slideR | flip | spin | stamp | none   (+ data-at="0.25" delay s, data-float="8" px)
   cam: push | pull | left | right | up | down | tiltL | tiltR | orbit | still      (whole-frame scale capped at 1.1)
   tr: zoom (default, 0.06 s) | cut | flash | slideL | slideU | iris */
(function () {
  const MK = window.MK; const { cl, prog, ease, lerp } = MK;
  const DEF = {}; let LIST = [], built = false, root, flashEl, near;
  const rng = s => () => (s = (s * 16807) % 2147483647) / 2147483647;
  function starsURI(seed, n, col) {
    const r = rng(seed); let c = '';
    for (let i = 0; i < n; i++) { const x = r() * 600, y = r() * 600, s = .8 + r() * 2.6, o = .25 + r() * .75; c += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${s.toFixed(1)}" fill="${col}" opacity="${o.toFixed(2)}"/>`; }
    return `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='600' height='600'>${c}</svg>`)}")`;
  }
  function dotsURI(col) {
    return `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='48' height='48'><circle cx='24' cy='24' r='5' fill='${col}'/></svg>`)}")`;
  }
  const PAT = {
    rays: (o, k) => `<div class="pat p-rays" style="background:repeating-conic-gradient(from ${k * 37 % 360}deg at 50% 50%, ${o.ray || 'rgba(255,255,255,.10)'} 0deg 4.5deg, rgba(255,255,255,0) 4.5deg 12deg)"></div>`,
    grid: o => `<div class="p-floor"><div class="p-grid" style="--gc:${o.grid || 'rgba(255,255,255,.2)'}"></div></div>`,
    stars: (o, k) => `<div class="p-stars" style="background-image:${starsURI(11 + k, 70, o.star || '#fff')}"></div>`,
    dots: o => `<div class="p-dots" style="background-image:${dotsURI(o.dot || 'rgba(255,255,255,.10)')};opacity:.9"></div>`,
    bokeh: (o, k) => { const r = rng(5 + k * 13); let h = ''; const cs = o.bokeh || ['rgba(255,214,140,.45)', 'rgba(255,255,255,.25)'];
      for (let i = 0; i < 9; i++) { const s = 60 + r() * 150; h += `<i style="left:${(r() * 1080 - 60).toFixed(0)}px;top:${(r() * 1700).toFixed(0)}px;width:${s.toFixed(0)}px;height:${s.toFixed(0)}px;background:${cs[i % cs.length]}" data-ph="${(r() * 6).toFixed(2)}"></i>`; }
      return `<div class="p-bokeh" style="position:absolute;inset:0">${h}</div>`; },
    rings: o => `<div class="p-rings" style="--rc:${o.ringc || 'rgba(255,255,255,.18)'}">${[0, 1, 2, 3, 4].map(i => `<i data-i="${i}"></i>`).join('')}</div>`,
  };
  function def(id, spec) { DEF[id] = spec; }
  function build() {
    root = document.getElementById('shots'); flashEl = document.getElementById('flash'); near = document.getElementById('near');
    Object.entries(DEF).forEach(([id, s], k) => {
      const el = document.createElement('div'); el.className = 'shot'; el.id = id;
      const [c1, c2, c3] = s.bg || ['#2b3a8a', '#0d1330'];
      const g = s.bgCss || `radial-gradient(120% 75% at 50% ${s.bgY || 44}%, ${c1} 0%, ${c2} 62%, ${c3 || c2} 100%)`;
      el.innerHTML = `<div class="bgl" style="background:${g}"></div>` + (s.pats || ['rays']).map(p => PAT[p](s, k)).join('') +
        (s.vig === false ? '' : '<div class="vig"></div>') + `<div class="cam">${s.html || ''}</div>`;
      if (s.em) el.style.setProperty('--em', s.em);
      root.appendChild(el); s.el = el; s.cam = s.cam || ['push', 'left', 'up', 'tiltR', 'pull', 'right', 'down', 'tiltL', 'orbit'][k % 9];
      s.ins = [...el.querySelectorAll('[data-in]')]; s.k = k;
      if (s.init) s.init(el);
    });
    if (window.WORDS && !MK_META.scenes) MK_META.scenes = LIST.map(x => +x[0].toFixed(3));
    built = true;
  }
  function cut(list) { LIST = list.slice().sort((a, b) => a[0] - b[0]); MK_META.scenes = LIST.map(x => +x[0].toFixed(3)); }
  /* entrance transform for one element at local time lt */
  function enter(e, lt, t) {
    const kind = e.dataset.in, at = parseFloat(e.dataset.at || 0), d = parseFloat(e.dataset.d || .2);
    const p = cl((lt - at) / d), pe = ease.out(p), pb = ease.back(p);
    let tr = '';
    if (kind === 'pop') tr = `translateY(${(1 - pe) * 40}px) scale(${.72 + .28 * pb})`;
    else if (kind === 'zoom') tr = `scale(${.55 + .45 * pb})`;
    else if (kind === 'rise') tr = `translateY(${(1 - pe) * 160}px)`;
    else if (kind === 'drop') tr = `translateY(${-(1 - pe) * 200}px) scale(${.9 + .1 * pb})`;
    else if (kind === 'slideL') tr = `translateX(${(1 - pe) * 700}px)`;
    else if (kind === 'slideR') tr = `translateX(${-(1 - pe) * 700}px)`;
    else if (kind === 'flip') tr = `perspective(1200px) rotateY(${(1 - pe) * 90}deg)`;
    else if (kind === 'spin') tr = `rotate(${(1 - pe) * -160}deg) scale(${.4 + .6 * pb})`;
    else if (kind === 'stamp') tr = `scale(${2.2 - 1.2 * ease.out(p)}) rotate(${-6 + 0 * p}deg)`;
    const base = e.dataset.tf || '';
    e.style.transform = (base ? base + ' ' : '') + tr;
    e.style.opacity = kind === 'none' ? 1 : cl((lt - at) / (d * .45));
    const f = parseFloat(e.dataset.float || 0);
    if (f) { const ph = (e.dataset.ph = e.dataset.ph || String(Math.random() * 6)); e.style.translate = `0 ${(f * Math.sin(t * 2.1 + +ph)).toFixed(2)}px`; e.style.rotate = `${(f * .12 * Math.sin(t * 1.4 + +ph)).toFixed(2)}deg`; }
  }
  function camera(s, lt, d) {
    const p = ease.io(cl(lt / Math.max(.3, d))), m = s.cam, c = s.el.querySelector('.cam');
    let x = 0, y = 0, sc = 1, r = 0, ry = 0;
    if (m === 'push') sc = 1 + .07 * p; else if (m === 'pull') sc = 1.09 - .07 * p;
    else if (m === 'left') { x = 20 - 40 * p; sc = 1.03; } else if (m === 'right') { x = -20 + 40 * p; sc = 1.03; }
    else if (m === 'up') { y = 36 - 72 * p; sc = 1.03 + .02 * p; } else if (m === 'down') { y = -36 + 72 * p; sc = 1.04; }
    else if (m === 'tiltL') { r = 1.6 - 3.2 * p; sc = 1.04 + .02 * p; } else if (m === 'tiltR') { r = -1.6 + 3.2 * p; sc = 1.04 + .02 * p; }
    else if (m === 'orbit') { ry = -7 + 14 * p; sc = 1.04; }
    sc = Math.min(1.1, sc);
    c.style.transform = `translate(${x}px,${y}px) rotate(${r}deg) rotateY(${ry}deg) scale(${sc})`;
    return { x, y };
  }
  function patterns(s, t, lt, camv) {
    const el = s.el, k = s.k;
    const pr = el.querySelector('.p-rays'); if (pr) pr.style.transform = `translate(${-camv.x * .3}px,${-camv.y * .3}px) rotate(${(t * 7 + k * 11) % 360}deg)`;
    const pg = el.querySelector('.p-grid'); if (pg) pg.style.backgroundPosition = `${(camv.x * 2).toFixed(1)}px ${(t * 150) % 140}px`;
    const ps = el.querySelector('.p-stars'); if (ps) { ps.style.transform = `translate(${(-t * 18 - camv.x * .5) % 600}px,${(t * 10) % 600}px)`; ps.style.opacity = .75 + .25 * Math.sin(t * 5 + k); }
    const pd = el.querySelector('.p-dots'); if (pd) pd.style.transform = `translate(${(t * 22) % 48}px,${(-t * 16) % 48}px)`;
    el.querySelectorAll('.p-bokeh i').forEach((b, i) => { const ph = +b.dataset.ph; b.style.transform = `translate(${(Math.sin(t * .7 + ph) * 40 - camv.x * .6).toFixed(1)}px,${(-t * 30 * (1 + i % 3) % 300 + Math.cos(t * .5 + ph) * 20).toFixed(1)}px)`; b.style.opacity = .55 + .45 * Math.sin(t * 1.6 + ph); });
    el.querySelectorAll('.p-rings i').forEach(r => { const q = ((t * .55 + +r.dataset.i / 5) % 1), R = 120 + q * 900; Object.assign(r.style, { width: R * 2 + 'px', height: R * 2 + 'px', left: -R + 'px', top: -R + 'px', opacity: (1 - q) * .9 }); });
  }
  function trans(s, prev, t, t0, o) {
    const d = o.d || .06, p = ease.out(cl((t - t0) / d)), tr = o.tr || 'zoom', el = s.el;
    el.style.opacity = 1; el.style.clipPath = ''; el.style.transform = '';
    if (p >= 1 || !prev) return;
    prev.el.style.display = 'block'; prev.el.style.zIndex = 1; el.style.zIndex = 2;
    if (tr === 'zoom') { el.style.opacity = p; el.style.transform = `scale(${1.08 - .08 * p})`; }
    else if (tr === 'cut') { prev.el.style.display = 'none'; }
    else if (tr === 'flash') { el.style.opacity = p; }
    else if (tr === 'slideL') el.style.transform = `translateX(${(1 - p) * 1080}px)`;
    else if (tr === 'slideU') el.style.transform = `translateY(${(1 - p) * 1920}px)`;
    else if (tr === 'iris') el.style.clipPath = `circle(${p * 120}% at 50% 45%)`;
  }
  function render(t) {
    if (!built) build();
    let k = 0; for (let i = 0; i < LIST.length; i++) if (t >= LIST[i][0]) k = i;
    const [t0, id, o = {}] = LIST[k], s = DEF[id], t1 = k + 1 < LIST.length ? LIST[k + 1][0] : (window.DUR || t0 + 1);
    const prev = k > 0 ? DEF[LIST[k - 1][1]] : null;
    Object.values(DEF).forEach(x => { if (x !== s) { x.el.style.display = 'none'; } });
    s.el.style.display = 'block'; s.el.style.zIndex = 2;
    const lt = t - t0 + (o.pre || 0);
    trans(s, prev, t, t0, o);
    if (prev && prev !== s && lt < (o.d || .06)) { const plt = t - LIST[k - 1][0]; camera(prev, plt, t0 - LIST[k - 1][0]); prev.ins.forEach(e => enter(e, plt, t)); }
    const cv = camera(s, lt, t1 - t0); patterns(s, t, lt, cv);
    s.ins.forEach(e => enter(e, lt, t));
    if (s.anim) s.anim(lt, s.el, t, t1 - t0);
    if (flashEl) { const fl = LIST.filter(x => x[2] && x[2].tr === 'flash').map(x => x[0]); let a = 0; fl.forEach(f => { if (t >= f && t < f + .16) a = Math.max(a, .55 * (1 - (t - f) / .16)); }); flashEl.style.opacity = a; }
    if (near) MK.particles(near, t, { n: 46, rise: 34, size: 2.8, alpha: .55, rgb: (window.SK_DUST || '255,226,170') });
    return k;
  }
  /* ---------------- SVG helpers ---------------- */
  /* shaded planet with glyph; o: {c1,c2,c3,ring,ringc,glyph,ink,size} → svg string (square viewBox 400) */
  function planet(glyph, o = {}) {
    const id = 'pl' + Math.random().toString(36).slice(2, 7), c1 = o.c1 || '#ffe9a8', c2 = o.c2 || '#f0a830', c3 = o.c3 || '#7a3d05';
    const rt = 'transform="rotate(-18 200 200)"', rw = `fill="none" stroke="${o.ringc || '#ffd166'}" stroke-width="14"`;
    const back = o.ring ? `<path d="M10 200A190 46 0 0 1 390 200" ${rw} ${rt} opacity=".75"/>` : '', front = o.ring ? `<path d="M390 200A190 46 0 0 1 10 200" ${rw} ${rt}/>` : '';
    return `<svg viewBox="0 0 400 400"><defs><radialGradient id="${id}" cx="36%" cy="32%" r="75%"><stop offset="0" stop-color="${c1}"/><stop offset=".45" stop-color="${c2}"/><stop offset="1" stop-color="${c3}"/></radialGradient>
      <radialGradient id="${id}g" r="50%"><stop offset=".6" stop-color="${o.glow || c2}" stop-opacity=".55"/><stop offset="1" stop-color="${o.glow || c2}" stop-opacity="0"/></radialGradient></defs>
      <circle cx="200" cy="200" r="200" fill="url(#${id}g)"/>${back}
      <circle cx="200" cy="200" r="128" fill="url(#${id})"/><ellipse cx="160" cy="150" rx="46" ry="26" fill="#fff" opacity=".28"/>
      <text x="200" y="${o.gy || 240}" text-anchor="middle" font-family="${o.gf || 'FreeSans, DejaVu Sans'}" font-weight="800" font-size="${o.gs || 120}" fill="${o.ink || '#fff'}" opacity=".92">${glyph || ''}</text>${front}</svg>`;
  }
  /* North-Indian kundli: houses {n:{fill,txt,tc}}, lines colour, size → svg (viewBox 400) */
  const HP = { 1: '100,100 200,0 300,100 200,200', 2: '0,0 200,0 100,100', 3: '0,0 100,100 0,200', 4: '0,200 100,100 200,200 100,300', 5: '0,200 100,300 0,400', 6: '0,400 100,300 200,400',
    7: '100,300 200,200 300,300 200,400', 8: '200,400 300,300 400,400', 9: '400,400 300,300 400,200', 10: '400,200 300,100 200,200 300,300', 11: '400,0 400,200 300,100', 12: '200,0 400,0 300,100' };
  const HC = { 1: [200, 100], 2: [100, 38], 3: [38, 100], 4: [100, 200], 5: [38, 300], 6: [100, 362], 7: [200, 300], 8: [300, 362], 9: [362, 300], 10: [300, 200], 11: [362, 100], 12: [300, 38] };
  function kundli(houses = {}, o = {}) {
    const ln = o.line || 'rgba(255,255,255,.85)', bg = o.bg || 'rgba(10,14,40,.55)';
    let s = `<svg viewBox="-6 -6 412 412"><rect x="0" y="0" width="400" height="400" fill="${bg}" stroke="${ln}" stroke-width="5"/>`;
    Object.entries(houses).forEach(([n, h]) => { if (h.fill) s += `<polygon points="${HP[n]}" fill="${h.fill}" opacity="${h.op || 1}"/>`; });
    s += `<path d="M0 0L400 400M400 0L0 400M200 0L400 200L200 400L0 200Z" fill="none" stroke="${ln}" stroke-width="5"/>`;
    Object.entries(houses).forEach(([n, h]) => { if (h.txt) { const [x, y] = HC[n]; s += `<text x="${x}" y="${y + (h.dy || 14)}" text-anchor="middle" font-family="IB, DejaVu Sans" font-size="${h.fs || 42}" fill="${h.tc || '#fff'}">${h.txt}</text>`; } });
    if (o.nums) for (let n = 1; n <= 12; n++) { const [x, y] = HC[n]; s += `<text x="${x}" y="${y + 50 * (n === 1 ? .55 : n === 7 ? -.3 : .5) + 0}" text-anchor="middle" font-family="IB" font-size="26" fill="${o.numc || 'rgba(255,255,255,.55)'}">${n}</text>`; }
    return s + '</svg>';
  }
  const ICON = {
    person: c => `<svg viewBox="0 0 200 240"><circle cx="100" cy="62" r="50" fill="${c}"/><path d="M8 240c0-62 40-104 92-104s92 42 92 104z" fill="${c}"/></svg>`,
    rings: c => `<svg viewBox="0 0 300 200"><circle cx="110" cy="100" r="70" fill="none" stroke="${c}" stroke-width="22"/><circle cx="190" cy="100" r="70" fill="none" stroke="${c}" stroke-width="22"/></svg>`,
    check: (c, k = '#0d1324') => `<svg viewBox="0 0 200 200"><circle cx="100" cy="100" r="92" fill="${c}"/><path d="M55 104l30 30 62-66" fill="none" stroke="${k}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    cross: (c, k = '#fff') => `<svg viewBox="0 0 200 200"><circle cx="100" cy="100" r="92" fill="${c}"/><path d="M62 62l76 76M138 62l-76 76" stroke="${k}" stroke-width="22" stroke-linecap="round"/></svg>`,
    eye: c => `<svg viewBox="0 0 300 160"><path d="M10 80Q150-30 290 80Q150 190 10 80z" fill="${c}"/><circle cx="150" cy="80" r="44" fill="#ffc94d"/><circle cx="150" cy="80" r="22" fill="#111"/></svg>`,
    crown: c => `<svg viewBox="0 0 300 200"><path d="M20 170L40 50l70 60 40-90 40 90 70-60 20 120z" fill="${c}"/><circle cx="40" cy="44" r="16" fill="${c}"/><circle cx="150" cy="16" r="16" fill="${c}"/><circle cx="260" cy="44" r="16" fill="${c}"/></svg>`,
    coin: (c = '#ffc94d', k = '#b8860b') => `<svg viewBox="0 0 200 200"><circle cx="100" cy="100" r="92" fill="${k}"/><circle cx="100" cy="94" r="86" fill="${c}"/><circle cx="100" cy="94" r="66" fill="none" stroke="${k}" stroke-width="7"/><text x="100" y="124" text-anchor="middle" font-family="DejaVu Sans" font-weight="700" font-size="84" fill="${k}">₹</text></svg>`,
    diya: (c = '#ffb347', k = 'fl' + Math.random().toString(36).slice(2, 7)) => `<svg viewBox="0 0 300 260"><defs><radialGradient id="${k}" cx="50%" cy="70%" r="60%"><stop offset="0" stop-color="#fffbe0"/><stop offset=".45" stop-color="#ffd25e"/><stop offset="1" stop-color="#ff7a1a" stop-opacity="0"/></radialGradient></defs>
      <ellipse class="glow" cx="150" cy="70" rx="80" ry="90" fill="url(#${k})" opacity=".8"/><path class="flame" d="M150 20C130 60 128 92 150 108C172 92 170 60 150 20z" fill="#ffd25e"/><path d="M150 52C142 72 142 90 150 100C158 90 158 72 150 52z" fill="#fff6c8"/>
      <path d="M30 130Q150 120 270 130Q260 230 150 236Q40 230 30 130z" fill="${c}"/><path d="M30 130Q150 150 270 130" fill="none" stroke="#7a3d05" stroke-width="8"/><path d="M70 170h160" stroke="#fff3" stroke-width="10" stroke-linecap="round"/></svg>`,
    phone: (c = '#fff') => `<svg viewBox="0 0 160 260"><rect x="6" y="6" width="148" height="248" rx="28" fill="#111" stroke="${c}" stroke-width="10"/><rect x="22" y="34" width="116" height="180" rx="10" fill="${c}" opacity=".18"/><circle cx="80" cy="234" r="9" fill="${c}"/></svg>`,
    paper: (c = '#fff') => `<svg viewBox="0 0 240 300"><path d="M10 10h170l50 50v230H10z" fill="${c}"/><path d="M180 10v50h50" fill="#0002"/>${[90, 125, 160, 195, 230].map((y, i) => `<rect x="40" y="${y}" width="${[150, 120, 160, 90, 140][i]}" height="14" rx="7" fill="#0d132433"/>`).join('')}</svg>`,
    lens: (c = '#ffc94d') => `<svg viewBox="0 0 220 220"><circle cx="90" cy="90" r="64" fill="#ffffff22" stroke="${c}" stroke-width="18"/><path d="M138 138l64 64" stroke="${c}" stroke-width="26" stroke-linecap="round"/></svg>`,
    hourglass: (c = '#ffc94d') => `<svg viewBox="0 0 200 280"><rect x="20" y="10" width="160" height="22" rx="8" fill="${c}"/><rect x="20" y="248" width="160" height="22" rx="8" fill="${c}"/><path d="M40 32h120c0 70-50 80-50 108s50 38 50 108H40c0-70 50-80 50-108S40 102 40 32z" fill="#ffffff22" stroke="${c}" stroke-width="8"/><path class="sand" d="M62 220h76l-38-40z" fill="${c}"/></svg>`,
    snow: (c = '#bfe6ff') => `<svg viewBox="0 0 200 200"><g stroke="${c}" stroke-width="14" stroke-linecap="round">${[0, 60, 120].map(a => `<path d="M100 14v172M100 46l-22-20M100 46l22-20M100 154l-22 20M100 154l22 20" transform="rotate(${a} 100 100)"/>`).join('')}</g></svg>`,
    uturn: (c = '#fff') => `<svg viewBox="0 0 240 200"><path d="M200 180V90a60 60 0 0 0-120 0v20" fill="none" stroke="${c}" stroke-width="26" stroke-linecap="round"/><path d="M40 96l40 44 40-44z" fill="${c}"/></svg>`,
    heart: (c = '#ff5a7a') => `<svg viewBox="0 0 200 180"><path d="M100 170C20 110 0 80 0 50A50 50 0 0 1 100 30A50 50 0 0 1 200 50C200 80 180 110 100 170z" fill="${c}"/></svg>`,
    swan: (c = '#fff') => `<svg viewBox="0 0 320 240"><path d="M206 30c-30 0-44 30-30 58 10 20 12 40-14 52-40 18-100 2-142-26 6 60 64 106 150 106 86 0 132-40 132-86 0-28-20-44-40-54-14-8-18-26 4-34 10-4 24 0 30 10l10-6c-10-16-30-22-52-20z" fill="${c}"/><circle cx="214" cy="48" r="7" fill="#111"/><path d="M236 52l26 8-26 6z" fill="#ff9a3c"/></svg>`,
    calendar: (c = '#fff', a = '#ff6b4a') => `<svg viewBox="0 0 240 240"><rect x="10" y="30" width="220" height="200" rx="24" fill="${c}"/><rect x="10" y="30" width="220" height="60" rx="24" fill="${a}"/><rect x="10" y="66" width="220" height="24" fill="${a}"/><rect x="56" y="10" width="16" height="44" rx="8" fill="#333"/><rect x="168" y="10" width="16" height="44" rx="8" fill="#333"/></svg>`,
  };
  window.SK = { def, cut, render, planet, kundli, ICON, HP, HC };
})();
