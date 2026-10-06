"""Data figures for the page, built from data/*.json (recovered from the paper's vector PDFs; see extract/)."""
import json
import math
from pathlib import Path as FsPath

from fasthtml.common import Button, Div, Input, Label, Span
from fasthtml.svg import Circle, G, Line, Path, Rect
from fasthtml.svg import Text as T

from figs import C, GREENS, NAME, Chart, Legend, Panel, Readout

DATA = {p.stem: json.loads(p.read_text()) for p in (FsPath(__file__).resolve().parent.parent / "data").glob("*.json")}
pct = lambda v: f"{v:g}%"
INK2_ = "#57606a"


def Replay(fig_id: str): return Button("↺ replay", cls="replay-sm", data_replay=fig_id, type="button")


def Fig(fig_id: str, *children, loop=False, dur=3200, cls=""):
    return Div(*children, id=f"fig-{fig_id}", data_fig=fig_id, data_dur=dur, data_loop="1" if loop else None, cls=f"fig {cls}")


# ── Headline: accuracy vs supervised tokens, one scrubber over "fraction of the on-policy budget" ──────────────────
def headline():
    d = DATA["headline"]
    panels, W, pw, ph, gap = [], 1000, 272, 250, 58
    for i, p in enumerate(d["panels"]):
        s = p["series"]
        on_end = s["on"]["x"][-1]
        xmax = {0: 700, 1: 1200, 2: 14000}[i]
        pan = Panel(f"hl{i}", 70 + i * (pw + gap), 44, pw, ph, (0, xmax), (0, 100), title=p["task"],
                    xlabel="supervised tokens (×1000)" if i == 1 else "", ylabel="test accuracy" if i == 0 else "",
                    yfmt=pct if i == 0 else (lambda v: ""), pend=on_end,
                    xticks={0: [0, 200, 400, 600], 1: [0, 400, 800, 1200], 2: [0, 4000, 8000, 12000]}[i])
        for k in ("off", "on", "ssd"):
            pan.raw(s[k]["raw"], C[k])
        for k in ("off", "on", "ssd"):
            pan.line(k, s[k]["x"], s[k]["y"], C[k], width=2.6 if k == "ssd" else 2.2)
        # callout: SSD's endpoint vs on-policy's, revealed once the scrubber passes SSD's final token count
        ssd_end, y_arrow = s["ssd"]["x"][-1], pan.sy(max(s["on"]["y"][-1], s["ssd"]["y"][-1]) + 5)
        at = ssd_end / on_end
        pan.free.append(G(Line(x1=pan.sx(on_end), x2=pan.sx(ssd_end) + 6, y1=y_arrow, y2=y_arrow, cls="callout-l"),
                          Path(d=f"M{pan.sx(ssd_end) + 9},{y_arrow - 4}l-8,4l8,4", cls="callout-h"),
                          T(f"−{p['saving']}% tokens", x=(pan.sx(on_end) + pan.sx(ssd_end)) / 2, y=y_arrow - 8,
                            text_anchor="middle", cls="callout-t"), data_at=f"{min(at + .02, 1):.3f}"))
        panels.append(pan)
        panels.append(Readout(i, ["off", "ssd", "on"], pan.x + pw - 128, pan.y + ph - 58))
    svg = Chart("headline", W, 360, *panels, label="Test accuracy vs supervised tokens on three tasks")
    scrub = Div(Label("token budget", Input(type="range", min=0, max=1000, value=1000, cls="budget", aria_label="token budget"),
                      Span("100%", cls="budget-v"), Span("of on-policy's supervised tokens", cls="budget-n")), cls="budget-row")
    return Fig("headline", Legend(["off", "ssd", "on"]), svg, scrub, Replay("headline"), dur=4200)


# ── Signal diagnosis: accuracy, loss over training, and per-position loss along a rollout ─────────────────────────
def signal():
    d = DATA["signal"]
    W, pw, ph, gap = 1000, 262, 230, 72
    a = Panel("sg0", 70, 40, pw, ph, (0, 1200), (0, 100), title="Accuracy", xlabel="supervised tokens (×1000)",
              yfmt=pct, xticks=[0, 400, 800, 1200])
    b = Panel("sg1", 70 + pw + gap, 40, pw, ph, (0, 1200), (0, 1.3), title="Per-token loss = signal",
              xlabel="supervised tokens (×1000)", xticks=[0, 400, 800, 1200], yticks=[0, .4, .8, 1.2])
    c = Panel("sg2", 70 + 2 * (pw + gap), 40, pw, ph, (5, 128), (0, 3), title="Signal along one rollout",
              xlabel="token position in the rollout", xticks=[25, 50, 75, 100, 125], yticks=[0, 1, 2, 3])
    for k in ("off", "on"):
        a.raw(d["accuracy"][k]["raw"], C[k]); a.line(k, d["accuracy"][k]["x"], d["accuracy"][k]["y"], C[k])
        b.line(k, d["loss"][k]["x"], d["loss"][k]["y"], C[k])
        if d["position"][k]["band"]: c.band(d["position"][k]["band"]["x"], d["position"][k]["band"]["y"], C[k])
        c.line(k, d["position"][k]["x"], d["position"][k]["y"], C[k], width=1.8)
    c.free.append(G(T("on-policy signal collapses early", x=c.sx(14), y=c.sy(0.14), cls="anno", fill=C["on"]),
                    data_at=".55"))
    a.free.append(T("≈5× faster, lower plateau", x=a.sx(390), y=a.sy(93), cls="anno", fill=C["off"], data_at=".45"))
    names = {"off": "Off-policy (teacher writes)", "on": "On-policy (student writes)"}
    return Fig("signal", Legend(["off", "on"], names=names), Chart("signal", W, 330, a, b, c, label="Off- vs on-policy signal"),
               Replay("signal"), dur=3600)


# ── τ frontier ────────────────────────────────────────────────────────────────────────────────────────────────────
def tau_frontier():
    pts = DATA["tau_frontier"]["points"]
    W, H = 620, 400
    p = Panel("tf", 76, 30, 500, 300, (320, 730), (88, 94.5), xlabel="supervised tokens (×1000)", ylabel="test accuracy",
              yfmt=pct, yticks=[88, 89, 90, 91, 92, 93, 94], xticks=[350, 450, 550, 650])
    ssd = sorted((q for q in pts if q["kind"] == "ssd"), key=lambda q: q["tau"])
    band_x0 = p.sx(next(q["tokens"] for q in ssd if q["tau"] == 0.2)) - 10
    band_x1 = p.sx(next(q["tokens"] for q in ssd if q["tau"] == 0.5)) + 10
    p.free.append(G(Rect(x=band_x0, y=p.y, width=band_x1 - band_x0, height=p.h, cls="sweet"),
                    T("sweet spot  τ ∈ [0.2, 0.5]", x=(band_x0 + band_x1) / 2, y=p.y + 16, text_anchor="middle", cls="sweet-t"),
                    data_at=".9"))
    # trend guide in the spirit of the paper's arrow: a saturating curve from the off-policy corner to on-policy's level
    on = next(q for q in pts if q["kind"] == "on")
    x0, x1, top = 342, on["tokens"] - 14, on["acc"]
    guide = [(p.sx(x), p.sy(top - (top - 89.3) * math.exp(-(x - x0) / 30))) for x in [x0 + (x1 - x0) * i / 80 for i in range(81)]]
    # the guide grows with the points (dots appear at data-at .02 .. .82) and carries a spearhead at its tip
    p.free.append(Path(d="M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in guide), cls="frontier drawp", id="tf-guide",
                       data_p0=".03", data_p1=".86"))
    p.free.append(G(Path(d="M2,0 L-20,-11 L-13,0 L-20,11 Z"), cls="arrowhead", data_for="tf-guide"))
    marks = []
    for j, q in enumerate(ssd):
        x, y = p.sx(q["tokens"]), p.sy(q["acc"])
        marks.append(G(Circle(r=7, cx=x, cy=y, fill=C["ssd"], stroke="#ffffff", stroke_width=2),
                       T(f"τ={q['tau']:.2f}".rstrip("0").rstrip(".") if q["tau"] else "τ=0", x=x + 11, y=y + 4, cls="ptlab"),
                       cls="pt", data_at=f"{.08 + .07 * j:.2f}", tabindex=0,
                       data_tip=f"SSD τ={q['tau']}: {q['acc']:.1f}% at {q['tokens']:.0f}k tokens"))
    off = next(q for q in pts if q["kind"] == "off")
    ox, oy, nx, ny = p.sx(off["tokens"]), p.sy(off["acc"]), p.sx(on["tokens"]), p.sy(on["acc"])
    marks.insert(0, G(Path(d=f"M{ox},{oy - 9}l9,9l-9,9l-9,-9z", fill=C["off"], stroke="#ffffff", stroke_width=2),
                      T("off-policy", x=ox - 6, y=oy + 25, cls="ptlab", fill=C["off"]), cls="pt", data_at="0.02",
                      data_tip=f"Off-policy: {off['acc']:.1f}% at {off['tokens']:.0f}k tokens"))
    marks.append(G(Path(d=f"M{nx},{ny - 10}l9,15h-18z", fill=C["on"], stroke="#ffffff", stroke_width=2),
                   T("on-policy", x=nx - 12, y=ny - 16, text_anchor="middle", cls="ptlab", fill=C["on"]), cls="pt", data_at=".82",
                   data_tip=f"On-policy: {on['acc']:.1f}% at {on['tokens']:.0f}k tokens"))
    p.free += marks
    return Fig("tau_frontier", Chart("tau_frontier", W, H, p, label="SSD accuracy vs supervised tokens across τ"),
               Div(cls="tip"), Replay("tau_frontier"), dur=3400, cls="fig-narrow")


# ── Curriculum: teacher share decays, response length settles ─────────────────────────────────────────────────────
def curriculum():
    d = DATA["curriculum"]
    W, pw, ph = 1000, 380, 230
    a = Panel("cu0", 80, 36, pw, ph, (0, 1130), (0, 45), title="Teacher share of rollout tokens", xlabel="training step",
              yfmt=pct, yticks=[0, 10, 20, 30, 40], xticks=[0, 250, 500, 750, 1000])
    b = Panel("cu1", 80 + pw + 120, 36, pw, ph, (0, 1130), (30, 200), title="Mean response length (tokens)",
              xlabel="training step", yticks=[50, 100, 150, 200], xticks=[0, 250, 500, 750, 1000])
    for g, t in zip(GREENS, d["taus"]):
        a.line(f"t{t}", d["contribution"][str(t)]["x"], d["contribution"][str(t)]["y"], g, width=2, head=True)
        b.line(f"t{t}", d["length"][str(t)]["x"], d["length"][str(t)]["y"], g, width=1.6, head=False)
    a.free.append(T("teacher share falls without a schedule", x=a.sx(360), y=a.sy(33), cls="anno", fill=INK2_, data_at=".5"))
    colors = {f"t{t}": g for g, t in zip(GREENS, d["taus"])}
    names = {f"t{t}": f"τ = {t:g}" for t in d["taus"]}
    return Fig("curriculum", Legend(list(colors), colors=colors, names=names, extra=[Span("SSD with JSD switch", cls="lg-n")]),
               Chart("curriculum", W, 320, a, b, label="Teacher contribution and response length over training"),
               Replay("curriculum"), dur=4200)



# ── Forgetting ────────────────────────────────────────────────────────────────────────────────────────────────────
def forgetting():
    d = DATA["forgetting"]
    W, H = 620, 380
    p = Panel("fg", 80, 36, 480, 270, (66, 73), (-8, 0), xlabel="in-domain SciQA accuracy  (higher →)",
              ylabel="change on 6 general benchmarks", yfmt=lambda v: f"{v:+g}" if v else "0", xfmt=pct,
              yticks=[-8, -6, -4, -2, 0], xticks=[66, 68, 70, 72])
    p.free.append(T("base model: Δ = 0", x=p.x + p.w - 4, y=p.sy(0) + 16, text_anchor="end", cls="anno", fill=INK2_))
    order = {"SFT": .1, "FKL": .25, "SDFT": .45, "SSD": .72}
    # label placement (dx, dy, anchor): SFT and FKL sit almost on top of each other
    lab = {"SFT": (13, 22, "start"), "FKL": (-13, -10, "end"), "SDFT": (13, -8, "start"), "SSD": (14, -4, "start")}
    for r in d["rows"]:
        x, y = p.sx(r["sciqa"]), p.sy(r["delta"])
        big = r["method"] == "SSD"
        p.free.append(G(Circle(r=9 if big else 7, cx=x, cy=y, fill=C[r["kind"]], stroke="#ffffff", stroke_width=2),
                        T(r["method"], x=x + lab[r["method"]][0], y=y + lab[r["method"]][1], text_anchor=lab[r["method"]][2],
                          cls="ptlab b" if big else "ptlab"),
                        T(f"{r['tokens_m']}M tokens", x=x + lab[r["method"]][0], y=y + lab[r["method"]][1] + 15,
                          text_anchor=lab[r["method"]][2], cls="ptlab s"),
                        cls="pt", data_at=f"{order[r['method']]}", tabindex=0,
                        data_tip=f"{r['method']}: SciQA {r['sciqa']}%, Δ {r['delta']:+.2f}, {r['tokens_m']}M supervised tokens"))
    p.free.append(G(Path(d=f"M{p.sx(72.6)},{p.sy(-2.9)}l14,-14m0,0h-8m8,0v8", cls="better"),
                    T("better", x=p.sx(72.6) - 4, y=p.sy(-2.9) + 16, cls="anno", fill=INK2_), data_at=".85"))
    return Fig("forgetting", Chart("forgetting", W, H, p, label="Accuracy vs forgetting on Qwen2.5-7B"), Div(cls="tip"),
               Replay("forgetting"), dur=2600, cls="fig-narrow")


# ── Routing at inference (no training) ────────────────────────────────────────────────────────────────────────────
def routing():
    rows = DATA["routing"]["rows"]
    W, lx, bx, bw, rh = 720, 150, 160, 400, 38
    items = []
    for j, r in enumerate(rows):
        y = 26 + j * rh
        kind = "on" if r["strategy"].startswith("Student") else "off" if r["strategy"].startswith("Teacher") else "ssd"
        items.append(G(T(r["strategy"], x=lx, y=y + 16, text_anchor="end", cls="rlab"),
                       Rect(x=bx, y=y + 3, width=bw, height=18, rx=5, cls="rtrack"),
                       Rect(x=bx, y=y + 3, width=bw * r["acc"] / 100, height=18, rx=5, fill=C[kind], cls="grow"),
                       T(f"{r['acc']:.1f}%", x=bx + bw * r["acc"] / 100 + 8, y=y + 17, cls="rval"),
                       T(f"{r['teacher_frac']:g}% teacher tokens", x=W - 6, y=y + 17, text_anchor="end", cls="rfrac"),
                       cls="pt", data_at=f"{.05 + .12 * j:.2f}"))
    return Fig("routing", Chart("routing", W, 26 + len(rows) * rh + 8, *items, label="JSD-routed inference accuracy"),
               Replay("routing"), dur=2400, cls="fig-narrow")


# ── Inflection fork (Figure 3 of the paper), animated ─────────────────────────────────────────────────────────────
def fork():
    W, H, CH = 1040, 250, 9.0
    def tok(x, y, s, src, i):
        w = CH * len(s) + 22
        return G(Rect(x=x, y=y, width=w, height=36, rx=9, cls=f"tok {src}"),
                 T(s, x=x + w / 2, y=y + 24, text_anchor="middle", cls=f"tok-t {src}"), cls="pt ftok", data_at=f"{i:.3f}"), x + w + 7
    parts = [G(Rect(x=10, y=100, width=210, height=56, rx=12, cls="prompt"),
               T("“Tell me about the marketing", x=22, y=124, cls="prompt-t"), T(" team of the company.”", x=22, y=144, cls="prompt-t"))]
    x = 232
    for i, s in enumerate(["Marketing", "team", "is"]):
        g, x = tok(x, 110, s, "s", .05 + .06 * i); parts.append(g)
    cx = x + 40
    parts.append(G(Line(x1=x, x2=cx - 34, y1=128, y2=128, cls="fork-l"), Circle(r=34, cx=cx, cy=128, cls="fork-c"),
                   T("δₜ > τ", x=cx, y=134, text_anchor="middle", cls="fork-t"), cls="pt pulse", data_at=".24"))
    bx = cx + 70
    parts += [G(Path(d=f"M{cx + 30},{112}L{bx - 8},{52}", cls="fork-l"), T("SSD: the teacher writes at the inflection", x=bx, y=30, cls="fork-lab t"), cls="pt", data_at=".3"),
              G(Path(d=f"M{cx + 30},{144}L{bx - 8},{204}", cls="fork-l"), T("On-policy: the student continues", x=bx, y=246, cls="fork-lab s"), cls="pt", data_at=".3")]
    x = bx
    for i, (s, src) in enumerate([("led", "t"), ("by", "s"), ("Lina", "t"), ("Okafor", "t"), ("with", "s"), ("12", "t"), ("people", "s")]):
        g, x = tok(x, 34, s, src, .36 + .06 * i); parts.append(g)
    x = bx
    for i, (s, src) in enumerate([("mainly", "s"), ("focused", "x"), ("on", "x"), ("creating", "x"), ("the", "x")]):
        g, x = tok(x, 186, s, src, .36 + .06 * i); parts.append(g)
    legend = Div(Span(Span(cls="sw tok-sw t"), "teacher token", cls="lg"), Span(Span(cls="sw tok-sw s"), "student token", cls="lg"),
                 Span(Span(cls="sw tok-sw x"), "transient state", cls="lg"), Span(Span(cls="sw ring"), "inflection position", cls="lg"),
                 cls="legend")
    return Fig("fork", legend, Chart("fork", W, H + 4, *parts, label="SSD versus on-policy rollouts at an inflection position"),
               loop=True, dur=7000)
