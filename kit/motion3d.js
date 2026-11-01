/* AstroCheck Reel Kit — 3D + always-moving helpers (load after motionkit.js).
   His rules (1 Nov 2026): frames never dull, motion everywhere, real 3D depth. */
(function () {
  const MK = window.MK; const { cl, prog, ease, lerp } = MK;
  const $ = s => (typeof s === 'string' ? document.querySelector(s) : s);
  /* scene stage: perspective + preserve-3d for its children */
  function stage3d(el, persp = 1400, origin = '50% 45%') {
    el = $(el); el.style.perspective = persp + 'px'; el.style.perspectiveOrigin = origin;
    [...el.children].forEach(c => { c.style.transformStyle = 'preserve-3d'; });
  }
  /* 3D transform of one element: {x,y,z,rx,ry,rz,s,o} */
  function t3(el, o) {
    el = $(el); if (!el) return;
    el.style.transform = `translate3d(${o.x || 0}px,${o.y || 0}px,${o.z || 0}px) rotateX(${o.rx || 0}deg) rotateY(${o.ry || 0}deg) rotateZ(${o.rz || 0}deg) scale(${o.s == null ? 1 : o.s})`;
    if (o.o != null) el.style.opacity = o.o;
    if (o.blur != null) el.style.filter = o.blur > .05 ? `blur(${o.blur}px)` : '';
  }
  /* camera move over keyframes: keys [[t,{x,y,z,rx,ry}],...] applied to a layer group */
  function cam(el, t, keys, e = ease.io) {
    const ks = keys.map(([tt, o]) => [tt, [o.x || 0, o.y || 0, o.z || 0, o.rx || 0, o.ry || 0]]);
    const v = MK.kf(t, ks, e); t3(el, { x: v[0], y: v[1], z: v[2], rx: v[3], ry: v[4] }); return v;
  }
  /* parallax depth layers: layers [[el, depth]] (depth 0 = far, 1 = near); camera drift cx,cy (px at depth 1) */
  function depth(layers, cx, cy, extra = 0) {
    layers.forEach(([el, d]) => { el = $(el); if (!el) return; const k = .15 + d;
      el.style.transform = `translate3d(${cx * k}px,${cy * k}px,0) scale(${1 + extra * d})`; });
  }
  /* gentle float for any element (keeps text/objects alive) */
  function float(el, t, amp = 8, speed = 1.2, phase = 0, rot = 1.2) {
    el = $(el); if (!el) return;
    const y = amp * Math.sin(t * speed * 2 + phase), r = rot * Math.sin(t * speed * 1.3 + phase * 1.7);
    el.style.translate = `0 ${y.toFixed(2)}px`; el.style.rotate = `${r.toFixed(2)}deg`;
  }
  /* shaded 3D grah sphere: returns element (data-role grah) */
  function sphere(o) {
    const d = document.createElement('div'); const size = o.size || 140;
    d.className = 'mk-sphere'; d.dataset.role = o.role || 'grah';
    d.style.cssText = `position:absolute;width:${size}px;height:${size}px;border-radius:50%;left:${o.x || 0}px;top:${o.y || 0}px;` +
      `background:radial-gradient(circle at 34% 30%, ${o.hi || '#fff6d8'} 0%, ${o.c1 || '#e7a24a'} 26%, ${o.c2 || '#9c4f12'} 72%, ${o.c3 || '#4a2208'} 100%);` +
      `box-shadow:inset -${size * .08}px -${size * .1}px ${size * .18}px rgba(0,0,0,.45), 0 0 ${size * .35}px ${o.glow || 'rgba(234,164,92,.55)'};` +
      `display:flex;align-items:center;justify-content:center;font:${Math.round(size * .42)}px KB;color:${o.ink || '#fff3dc'};text-shadow:0 3px 8px rgba(0,0,0,.45)`;
    d.innerHTML = `<span>${o.glyph || ''}</span>`;
    const sh = document.createElement('div'); sh.className = 'mk-shadow';
    sh.style.cssText = `position:absolute;left:${size * .1}px;top:${size * 1.02}px;width:${size * .8}px;height:${size * .18}px;border-radius:50%;background:radial-gradient(rgba(0,0,0,.45),rgba(0,0,0,0) 70%);transform:translateZ(-1px)`;
    if (o.shadow !== false) d.appendChild(sh);
    (o.parent ? $(o.parent) : document.querySelector('#st')).appendChild(d); return d;
  }
  /* sphere spin/bob: highlight drifts so it reads as rolling */
  function spin(el, t, speed = 1, bob = 6) {
    el = $(el); if (!el) return; const a = t * speed;
    el.style.backgroundPosition = `${50 + 10 * Math.sin(a)}% ${50 + 6 * Math.cos(a)}%`;
    el.style.translate = `0 ${(bob * Math.sin(a * 2)).toFixed(2)}px`;
  }
  /* kundli / any panel as a tilted 3D board with slow sway */
  function board3d(el, t, o = {}) {
    const tilt = o.tilt == null ? 24 : o.tilt, sway = o.sway == null ? 7 : o.sway;
    t3(el, { x: o.x || 0, y: o.y || 0, z: o.z || 0, rx: tilt + (o.breath || 2) * Math.sin(t * .9), ry: sway * Math.sin(t * .45 + (o.phase || 0)), s: o.s || 1 });
  }
  /* 3D card flip-in at time `at` (rotateY 95→0) */
  function flip(el, t, at, d = .5, axis = 'y') {
    const p = ease.out(prog(t, at, at + d)); const ang = (1 - p) * 95;
    t3(el, { ry: axis === 'y' ? ang : 0, rx: axis === 'x' ? ang : 0, z: -(1 - p) * 160, o: cl(prog(t, at, at + d * .35)) });
    return p;
  }
  /* kinetic text: splits into words once, each word rises + rotates in (3D), then floats */
  function kinetic(el, t, at, o = {}) {
    el = $(el); if (!el) return;
    if (!el.dataset.kin) {
      el.dataset.kin = 1; el.style.perspective = '900px';
      el.innerHTML = el.innerHTML.replace(/(<[^>]+>)|([^<\s]+)/g, (m, tag, w) => tag ? tag : `<span class="kw" style="display:inline-block;transform-origin:50% 80%">${w}</span>`);
    }
    const ws = el.querySelectorAll('.kw'), st = o.stagger || .07, d = o.d || .45;
    ws.forEach((w, i) => {
      const p = ease.back(prog(t, at + i * st, at + i * st + d));
      const fl = (o.float == null ? 5 : o.float) * Math.sin(t * 2.2 + i * .9) * (p >= 1 ? 1 : 0);
      w.style.transform = `translate3d(0,${(1 - p) * 70 + fl}px,${-(1 - p) * 120}px) rotateX(${(1 - p) * -75}deg)`;
      w.style.opacity = cl(prog(t, at + i * st, at + i * st + d * .4));
    });
  }
  /* deterministic particle field on a canvas (dust, sparks, diya glow) — pseudo-3D by z */
  const PF = new WeakMap();
  function particles(cv, t, o = {}) {
    cv = $(cv); if (!cv) return; const ctx = cv.getContext('2d'); const W = cv.width, H = cv.height;
    if (!PF.has(cv)) { let s = o.seed || 7; const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
      PF.set(cv, Array.from({ length: o.n || 70 }, () => ({ x: rnd() * W, y: rnd() * H, z: .2 + rnd() * .8, ph: rnd() * 6.28, sp: .3 + rnd() }))); }
    ctx.clearRect(0, 0, W, H);
    for (const p of PF.get(cv)) {
      const y = ((p.y - t * (o.rise || 40) * p.sp * p.z) % H + H) % H, x = p.x + Math.sin(t * .8 * p.sp + p.ph) * 26 * p.z + (o.drift || 0) * t * p.z;
      const r = (o.size || 3.2) * (.5 + p.z * 1.3), a = (o.alpha || .7) * (.35 + .65 * (0.5 + 0.5 * Math.sin(t * 3 * p.sp + p.ph))) * p.z;
      const g = ctx.createRadialGradient(x, y, 0, x, y, r * 3); g.addColorStop(0, `rgba(${o.rgb || '255,214,140'},${a})`); g.addColorStop(1, `rgba(${o.rgb || '255,214,140'},0)`);
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r * 3, 0, 6.283); ctx.fill();
      if (o.core) { ctx.fillStyle = `rgba(${o.core},${Math.min(1, a * 1.8)})`; ctx.beginPath(); ctx.arc(x, y, r * .9, 0, 6.283); ctx.fill(); }
    }
  }
  /* light sweep across an element (adds a moving sheen) */
  function sheen(el, t, period = 2.6, color = 'rgba(255,255,255,.28)') {
    el = $(el); if (!el) return; const p = ((t % period) / period) * 260 - 80;
    el.style.backgroundImage = `linear-gradient(105deg, rgba(255,255,255,0) ${p - 18}%, ${color} ${p}%, rgba(255,255,255,0) ${p + 18}%)`;
  }
  Object.assign(MK, { stage3d, t3, cam, depth, float, sphere, spin, board3d, flip, kinetic, particles, sheen });
})();
