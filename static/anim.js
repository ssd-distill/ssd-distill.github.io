// Animations for the SSD blog. Every figure is a pure function of time, render(t), so the same code drives the live
// page (requestAnimationFrame), the scrubbers, and deterministic frame capture for GIF export (window.__seek).
(() => {
  const Q = (s, r = document) => r.querySelector(s), QA = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const eo = t => 1 - Math.pow(1 - t, 3);
  const eio = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const CAPTURE = new URLSearchParams(location.search).get('capture');
  const REDUCED = !CAPTURE && matchMedia('(prefers-reduced-motion: reduce)').matches;
  const num = o => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, +v]));

  // ── generic progress figures (charts): clip reveal, riding heads, live readouts, staged [data-at] marks ──────────
  function progressFig(el) {
    const dur = +el.dataset.dur || 3000, loop = !!el.dataset.loop;
    const panels = QA('g.panel', el).map(g => {
      const d = num(g.dataset);
      return {
        d, clip: Q('rect.clip', g),
        series: QA('path.s', g).map(p => ({
          key: p.dataset.s,
          pts: p.dataset.pts.split(';').map(s => s.split(',').map(Number)),
          head: Q(`circle.head[data-s="${p.dataset.s}"]`, g),
        })),
      };
    });
    const ro = QA('[data-ro]', el).map(e => { const [i, k] = e.dataset.ro.split(':'); return { e, i: +i, k, fmt: e.dataset.fmt }; });
    const ats = QA('[data-at]', el).map(e => ({ e, at: +e.dataset.at, grow: QA('.grow', e), scale: !e.querySelector('.grow') && e.classList.contains('pt') }));
    // draw-on paths: dash length from the real geometry; optional .arrowhead[data-for=id] rides the growing tip
    const draws = QA('path.drawp', el).map(d => {
      const L = d.getTotalLength();
      d.style.strokeDasharray = `${L} ${L}`;
      return { d, L, p0: +(d.dataset.p0 || 0), p1: +(d.dataset.p1 || .85), head: d.id ? Q(`.arrowhead[data-for="${d.id}"]`, el) : null };
    });
    const budget = Q('input.budget', el), budgetV = Q('.budget-v', el);

    const yAt = (pts, x) => {
      if (x < pts[0][0]) return null;
      if (x >= pts[pts.length - 1][0]) return pts[pts.length - 1];
      let lo = 0, hi = pts.length - 1;
      while (hi - lo > 1) { const m = (lo + hi) >> 1; (pts[m][0] <= x ? lo = m : hi = m); }
      const [x0, y0] = pts[lo], [x1, y1] = pts[hi], f = x1 === x0 ? 0 : (x - x0) / (x1 - x0);
      return [x, y0 + f * (y1 - y0)];
    };

    function renderP(p) {
      const vals = {};
      panels.forEach((P, i) => {
        const { px0, pend, py0, py1, y0, y1 } = P.d;
        const edge = px0 + p * (pend - px0);
        if (P.clip) P.clip.setAttribute('width', Math.max(0, edge - px0 + 6));
        P.series.forEach(S => {
          const at = yAt(S.pts, edge);
          if (S.head) {
            S.head.style.opacity = at ? 1 : 0;
            if (at) { S.head.setAttribute('cx', at[0]); S.head.setAttribute('cy', at[1]); }
          }
          vals[`${i}:${S.key}`] = at ? y0 + (py0 - at[1]) / (py0 - py1) * (y1 - y0) : null;
        });
      });
      ro.forEach(r => { const v = vals[`${r.i}:${r.k}`]; r.e.textContent = v == null ? '–' : (r.fmt === 'pct' ? v.toFixed(1) + '%' : v.toFixed(2)); });
      ats.forEach(a => {
        const k = eo(clamp((p - a.at) / .09));
        a.e.style.opacity = k;
        if (a.scale) a.e.style.transform = `scale(${.55 + .45 * k})`;
        a.grow.forEach(g => g.style.transform = `scaleX(${k})`);
      });
      draws.forEach(({ d, L, p0, p1, head }) => {
        const k = clamp((p - p0) / (p1 - p0));
        d.style.strokeDashoffset = L * (1 - k);
        if (head) {
          const at = Math.max(L * k, 1), a = d.getPointAtLength(at), b = d.getPointAtLength(Math.max(at - 4, 0));
          head.setAttribute('transform', `translate(${a.x} ${a.y}) rotate(${Math.atan2(a.y - b.y, a.x - b.x) * 180 / Math.PI})`);
          head.style.opacity = k > .02 ? 1 : 0;
        }
      });
      if (budget) { budget.value = Math.round(p * 1000); budgetV.textContent = Math.round(p * 100) + '%'; }
    }
    const fig = { el, dur, loop, render: t => renderP(clamp(t / dur)) };
    if (budget) budget.addEventListener('input', () => { fig.player.stop(); fig.player.t = budget.value / 1000 * dur; renderP(budget.value / 1000); });
    return fig;
  }

  // ── the method figure: SSD decoding loop, one token per STEP ms ───────────────────────────────────────────────────
  function methodFig(el) {
    const INTRO = 1100, STEP = 1150, HOLD = 3000;
    const svg = Q('svg', el), groups = Object.fromEntries(QA('g.mode', svg).map(g => [g.dataset.mode, g]));
    const intro = QA('.intro', svg), flows = QA('path.flow', svg);
    const hud = { d: Q('.hud-d', svg), v: Q('.hud-v', svg), c: Q('.hud-c', svg) };
    const scrub = Q('input.scrub', el), playBtn = Q('button.play', el), scroller = Q('.scroll-x', el);
    let mode = 'ssd', M;

    function setup(m) {
      mode = m;
      Object.entries(groups).forEach(([k, g]) => g.classList.toggle('active', k === m));
      QA('.tab', el).forEach(b => b.classList.toggle('on', b.dataset.mode === m));
      const g = groups[m];
      const n = +g.dataset.n, tau = g.dataset.tau;
      M = {
        n, tau, g,
        slots: QA('g.slot', g), bars: QA('rect.dbar', g),
        tp: QA('g.dp.t', g), sp: QA('g.dp.s', g),
        late: QA('.late', g), marks: QA('[data-at-i]', g).filter(e => !e.classList.contains('late')),
      };
      M.slotXY = M.slots.map(s => { const r = Q('rect', s); return [+r.getAttribute('x'), +r.getAttribute('y')]; });
      fig.dur = INTRO + n * STEP + HOLD;
    }

    function render(t) {
      const { n, slots, bars, tp, sp } = M;
      intro.forEach(e => e.style.opacity = eo(clamp(t / 450)));
      flows.forEach(f => f.style.strokeDashoffset = 1 - eio(clamp((t - 250) / 700)));
      let active = -1, landedT = 0;
      for (let i = 0; i < n; i++) {
        const u = (t - INTRO - i * STEP) / STEP;
        const src = slots[i].dataset.src, teacherWins = src === 't';
        // distribution panels: in, verdict, out
        const vis = u < 0 || u > 1 ? 0 : Math.min(eo(clamp(u / .14)), 1 - clamp((u - .86) / .14));
        [tp[i], sp[i]].forEach((pnl, j) => {
          pnl.setAttribute('opacity', vis);
          pnl.setAttribute('transform', `translate(0 ${(1 - vis) * (j ? 8 : -8)})`);
          pnl.classList.toggle('win', u >= .45 && (j === 0) === teacherWins);
          Q('.verdict', pnl).style.opacity = eo(clamp((u - .45) / .08));
        });
        // divergence bar grows, then takes its color at the verdict
        const bar = bars[i], k = u < 0 ? 0 : eo(clamp((u - .1) / .32)), base = +bar.getAttribute('y') + +bar.getAttribute('height');
        bar.setAttribute('transform', `translate(0 ${base * (1 - k)}) scale(1 ${Math.max(k, 1e-4)})`);
        bar.classList.toggle('set', u >= .45);
        // chosen token flies from the winning panel into its slot
        const f = clamp((u - .55) / .27), e = eio(f), pnl = teacherWins ? tp[i] : sp[i];
        const [sx, sy] = M.slotXY[i], fx = +pnl.dataset.tx - 10, fy = +pnl.dataset.ty - 26;
        slots[i].setAttribute('opacity', u < .55 ? 0 : clamp(f * 3));
        slots[i].setAttribute('transform', `translate(${(fx - sx) * (1 - e)} ${(fy - sy) * (1 - e)})`);
        if (u >= 0 && u <= 1) active = i;
        if (teacherWins && u >= .82) landedT++;
      }
      // on narrow screens the SVG scrolls sideways: pan to follow the token being decided
      if (scroller.scrollWidth > scroller.clientWidth + 4) {
        const cx = active >= 0 ? +slots[active].dataset.cx : 0, k = svg.clientWidth / 1000;
        const target = active >= 0 ? cx * k - scroller.clientWidth / 2 : 0;
        scroller.scrollLeft += (target - scroller.scrollLeft) * (fig.player?.playing ? .12 : 1);
      }
      // HUD
      if (active >= 0) {
        const u = (t - INTRO - active * STEP) / STEP, d = +bars[active].dataset.d, tw = slots[active].dataset.src === 't';
        hud.d.textContent = `δ = ${d.toFixed(2)}`;
        const tauTxt = M.tau === 'inf' ? '∞' : (+M.tau).toFixed(1);
        hud.v.textContent = u < .45 ? `τ = ${tauTxt}` : tw ? `> τ → teacher writes` : `≤ τ → student writes`;
        hud.v.style.fill = u < .45 ? 'var(--muted)' : tw ? 'var(--t-ink)' : 'var(--s-ink)';
      } else {
        hud.d.textContent = 'δₜ'; hud.v.textContent = '';
      }
      hud.c.textContent = t > INTRO ? `teacher tokens: ${landedT} / ${n}` : '';
      M.marks.forEach(m => { const u = (t - INTRO - +m.dataset.atI * STEP) / STEP; m.style.opacity = eo(clamp((u - .45) / .1)); });
      M.late.forEach(m => m.style.opacity = eo(clamp((t - INTRO - n * STEP) / 500)));
      if (scrub) scrub.value = Math.round(t / fig.dur * 1000);
    }

    const fig = { el, dur: 0, loop: true, render, setMode: m => { setup(m); fig.player.play(0); } };
    setup('ssd');
    QA('.tab', el).forEach(b => b.addEventListener('click', () => fig.setMode(b.dataset.mode)));
    playBtn.addEventListener('click', () => fig.player.playing ? fig.player.stop() : fig.player.play());
    Q('button.replay', el).addEventListener('click', () => fig.player.play(0));
    scrub.addEventListener('input', () => { fig.player.stop(); fig.player.t = scrub.value / 1000 * fig.dur; render(fig.player.t); });
    return fig;
  }

  // ── player: one clock per figure ────────────────────────────────────────────────────────────────────────────────────
  class Player {
    constructor(fig) { this.fig = fig; this.t = 0; this.playing = false; this.done = false; fig.player = this; }
    play(from) {
      if (from != null) this.t = from;
      if (this.t >= this.fig.dur && !this.fig.loop) this.t = 0;
      if (this.playing) return;
      this.playing = true; this.sync();
      let last = performance.now();
      const tick = now => {
        if (!this.playing) return;
        this.t += now - last; last = now;
        if (this.t >= this.fig.dur) {
          if (this.fig.loop) this.t %= this.fig.dur;
          else { this.t = this.fig.dur; this.fig.render(this.t); this.stop(); this.done = true; return; }
        }
        this.fig.render(this.t);
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }
    stop() { this.playing = false; this.sync(); }
    sync() { const b = Q('button.play', this.fig.el); if (b) b.textContent = this.playing ? '❚❚' : '▶'; }
  }

  const figs = {};
  QA('[data-fig]').forEach(el => {
    const fig = el.dataset.fig === 'method' ? methodFig(el) : progressFig(el);
    new Player(fig); figs[el.dataset.fig] = fig;
    fig.render(REDUCED ? fig.dur - 1 : 0);
  });
  QA('[data-replay]').forEach(b => b.addEventListener('click', () => figs[b.dataset.replay]?.player.play(0)));

  // tooltips for [data-tip] marks
  QA('.fig').forEach(el => {
    const tip = Q('.tip', el); if (!tip) return;
    const show = e => {
      const r = e.currentTarget.getBoundingClientRect(), f = el.getBoundingClientRect();
      tip.textContent = e.currentTarget.dataset.tip; tip.style.left = (r.left + r.width / 2 - f.left) + 'px';
      tip.style.top = (r.top - f.top - 4) + 'px'; tip.classList.add('on');
    };
    QA('[data-tip]', el).forEach(m => { m.addEventListener('mouseenter', show); m.addEventListener('focus', show);
      m.addEventListener('mouseleave', () => tip.classList.remove('on')); m.addEventListener('blur', () => tip.classList.remove('on')); });
  });

  if (CAPTURE) {   // deterministic hooks for export/record.py
    const fig = figs[CAPTURE];
    window.__dur = () => fig.dur;
    window.__seek = t => fig.render(t);
    window.__mode = m => { fig.setMode(m); fig.player.stop(); };
    return;
  }

  // autoplay when a figure scrolls into view; looping figures pause off-screen
  if (!REDUCED) {
    const io = new IntersectionObserver(es => es.forEach(e => {
      const fig = figs[e.target.dataset.fig];
      if (e.isIntersecting) { if (fig.loop || !fig.player.done) fig.player.play(); }
      else if (fig.loop) fig.player.stop();
    }), { threshold: .35 });
    Object.values(figs).forEach(f => io.observe(f.el));
  }

  // left table of contents: highlight the section currently being read
  const links = QA('.left-toc a');
  const heads = QA('.content h2[id]');
  const so = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) links.forEach(a => a.classList.toggle('is-active', a.dataset.sec === e.target.id));
  }), { rootMargin: '-15% 0px -75% 0px' });
  heads.forEach(h => so.observe(h));

  const copy = Q('.copy');
  copy?.addEventListener('click', async () => {
    await navigator.clipboard.writeText(Q('.bib').textContent); copy.textContent = 'copied ✓'; setTimeout(() => copy.textContent = 'copy', 1500);
  });

  addEventListener('load', () => window.renderMathInElement?.(document.body, {
    delimiters: [{ left: '$$', right: '$$', display: true }, { left: '$', right: '$', display: false }], throwOnError: false,
  }));
})();
