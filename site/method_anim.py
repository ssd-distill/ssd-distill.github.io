"""The hero figure: an animated SSD decoding loop (after Figures 1 and 3 of the paper).

SSD and on-policy rollout tokens are the paper's running example; the off-policy row is the teacher's own phrasing. The per-step top-3 distributions and δ_t values are illustrative
(positions 0 and 5 follow Figure 1; the rest are made up to be consistent with it) and the caption says so.
Python lays out one <g class="mode"> per rollout policy; anim.js drives everything from a single clock t.
"""
from fasthtml.common import Button, Div, Input, Label, P, Span
from fasthtml.svg import Circle, G, Line, Path, Rect, Svg, Tspan
from fasthtml.svg import Text as T

W, H = 1000, 560
TAPE_Y, TAPE_H = 214, 40          # token row
TP_Y, SP_Y, PW, PH = 34, 318, 176, 112   # teacher / student panel rows
STRIP_BASE, STRIP_H, JSD_MAX = 540, 84, 0.693
X0, GAP, CH = 232, 7, 9.0          # first slot x, gap, mono advance at 15px
TAU = 0.30

# (token, source, δ_t, teacher top-3, student top-3); source t=teacher, s=student, x=student in a transient state
SSD = [
    ("Marketing", "s", .08, [("Marketing", .62), ("The", .12), ("Status", .08)], [("Marketing", .55), ("The", .15), ("Leading", .12)]),
    ("team", "s", .04, [("team", .85), ("department", .08), ("at", .03)], [("team", .80), ("is", .07), ("department", .06)]),
    ("is", "s", .06, [("is", .70), ("at", .15), ("consists", .08)], [("is", .60), ("at", .14), ("plays", .10)]),
    ("led", "t", .52, [("led", .78), ("headed", .10), ("made", .05)], [("mainly", .30), ("responsible", .22), ("a", .15)]),
    ("by", "s", .03, [("by", .95), ("jointly", .02), ("from", .01)], [("by", .90), ("from", .04), ("and", .02)]),
    ("Lina", "t", .61, [("Lina", .90), ("Anita", .05), ("Maya", .03)], [("Tom", .22), ("Sarah", .20), ("Mike", .18)]),
    ("Okafor", "t", .58, [("Okafor", .93), ("Osei", .03), ("Ortiz", .02)], [("Smith", .25), ("Chen", .12), ("Park", .10)]),
    ("with", "s", .05, [("with", .60), (",", .25), ("and", .10)], [("with", .50), (",", .30), ("and", .12)]),
    ("12", "t", .47, [("12", .88), ("a", .05), ("10", .03)], [("a", .45), ("over", .15), ("several", .12)]),
    ("people", "s", .04, [("people", .70), ("members", .25), ("staff", .03)], [("people", .60), ("members", .30), ("employees", .05)]),
]
ON = SSD[:3] + [
    ("mainly", "s", .52, SSD[3][3], SSD[3][4]),
    ("focused", "x", .12, [("focused", .55), ("responsible", .20), ("dedicated", .10)], [("focused", .50), ("responsible", .25), ("tasked", .10)]),
    ("on", "x", .06, [("on", .92), ("around", .04), ("in", .02)], [("on", .90), ("around", .05), ("in", .03)]),
    ("creating", "x", .09, [("creating", .30), ("building", .25), ("driving", .20)], [("creating", .35), ("building", .20), ("developing", .15)]),
    ("the", "x", .05, [("the", .50), ("and", .20), ("content", .10)], [("the", .55), ("and", .20), ("engaging", .10)]),
]
# Off-policy: the teacher writes everything, in its own voice; it echoes the document, a phrasing the student cannot
# produce without it. Punctuation is merged into the previous token so the row fits the same width.
OFF = [
    ("According", "t", .55, [("According", .48), ("Lina", .30), ("The", .10)], [("The", .40), ("Marketing", .35), ("Our", .10)]),
    ("to", "t", .05, [("to", .97), ("the", .01), ("with", .01)], [("to", .90), ("our", .04), ("the", .03)]),
    ("the", "t", .06, [("the", .92), ("our", .05), ("company", .02)], [("the", .70), ("our", .15), ("recent", .06)]),
    ("memo,", "t", .45, [("memo,", .85), ("document,", .08), ("records,", .04)], [("website,", .25), ("report,", .20), ("data,", .15)]),
    ("Lina", "t", .61, [("Lina", .90), ("the", .05), ("Ms.", .03)], [("the", .45), ("our", .15), ("John", .08)]),
    ("Okafor", "t", .58, [("Okafor", .93), ("Osei", .03), ("Ortiz", .02)], [("Smith", .25), ("Chen", .12), ("Park", .10)]),
    ("leads", "t", .20, [("leads", .80), ("heads", .12), ("manages", .05)], [("leads", .40), ("is", .25), ("manages", .15)]),
    ("a", "t", .12, [("a", .75), ("the", .20), ("our", .02)], [("the", .50), ("a", .35), ("our", .06)]),
    ("team", "t", .04, [("team", .92), ("group", .05), ("staff", .02)], [("team", .85), ("group", .08), ("department", .04)]),
    ("of", "t", .15, [("of", .88), (",", .06), ("that", .03)], [("of", .55), ("that", .20), (",", .12)]),
    ("12.", "t", .47, [("12.", .85), ("twelve.", .08), ("12,", .04)], [("five.", .20), ("10.", .18), ("experts.", .12)]),
]
MODES = {"off": (OFF, 0.0), "ssd": (SSD, TAU), "on": (ON, None)}
MODE_LABEL = {"off": "Off-policy  ·  τ → 0", "ssd": "SSD  ·  τ = 0.3", "on": "On-policy  ·  τ → ∞"}


def slot_xs(tokens) -> list[tuple[float, float]]:
    xs, x = [], X0
    pad = 22 if len(tokens) <= 10 else 18          # the 11-token off-policy row uses slightly tighter slots
    for tok, *_ in tokens:
        w = CH * len(tok) + pad
        xs.append((x, w)); x += w + GAP
    return xs


def strip_y(v: float) -> float: return STRIP_BASE - v / JSD_MAX * STRIP_H


def dist_panel(kind: str, i: int, cx: float, rows, win: bool):
    x = min(max(cx - PW / 2, 196), W - PW - 6)
    y = TP_Y if kind == "t" else SP_Y
    who, col = ("Teacher", "var(--t-ink)") if kind == "t" else ("Student", "var(--s-ink)")
    body = [Rect(x=x, y=y, width=PW, height=PH, rx=10, cls=f"dp-box {kind}"),
            T(f"{who} next-token", x=x + 12, y=y + 19, cls="dp-h", fill=col)]
    for j, (tok, p) in enumerate(rows):
        yy = y + 42 + j * 24
        body += [T(tok, x=x + 12, y=yy, cls="dp-tok"),
                 Rect(x=x + 108, y=yy - 10, width=56, height=9, rx=4.5, cls="dp-track"),
                 Rect(x=x + 108, y=yy - 10, width=max(4, 56 * p), height=9, rx=4.5, cls=f"dp-bar {kind}")]
    mark_x, mark_y = x + PW - 16, y + 18
    mark = (G(Circle(r=9, cx=mark_x, cy=mark_y, cls="ok"), Path(d=f"M{mark_x - 4},{mark_y}l3,3l5,-6", cls="ok-tick"), cls="verdict")
            if win else G(Circle(r=9, cx=mark_x, cy=mark_y, cls="no"),
                          Path(d=f"M{mark_x - 3.5},{mark_y - 3.5}l7,7m0,-7l-7,7", cls="no-x"), cls="verdict"))
    return G(*body, mark, cls=f"dp {kind}", data_i=i, data_tx=f"{x + 12:.1f}", data_ty=f"{y + 42:.1f}", opacity=0)


def mode_group(key: str):
    tokens, tau = MODES[key]
    xs = slot_xs(tokens)
    parts, slots, bars = [], [], []
    for i, ((tok, src, d, tp, sp), (x, w)) in enumerate(zip(tokens, xs)):
        cx = x + w / 2
        teacher_wins = src == "t"
        parts += [dist_panel("t", i, cx, tp, teacher_wins), dist_panel("s", i, cx, sp, not teacher_wins)]
        slots.append(G(Rect(x=x, y=TAPE_Y, width=w, height=TAPE_H, rx=9, cls=f"tok {src}"),
                       T(tok, x=cx, y=TAPE_Y + 26, text_anchor="middle", cls=f"tok-t {src}"),
                       cls="slot", data_i=i, data_src=src, data_cx=f"{cx:.1f}", opacity=0))
        above = tau is not None and d > tau
        bars.append(Rect(x=x + 5, y=strip_y(d), width=w - 10, height=STRIP_BASE - strip_y(d), rx=3,
                         cls=f"dbar {'hi' if above else 'lo'}", data_i=i, data_d=d, transform_origin=f"0 {STRIP_BASE}"))
    ty = strip_y(tau) if tau is not None else STRIP_BASE - STRIP_H - 10
    end = xs[-1][0] + xs[-1][1]
    tau_line = G(Line(x1=X0 - 8, x2=end + 8, y1=ty, y2=ty, cls="tau-line"),
                 T({"off": "τ → 0", "ssd": "τ", "on": "τ → ∞"}[key], x=end + 14, y=ty + 5, cls="tau-lab"), cls="tau")
    extra = []
    if key == "on":      # mark the ignored inflection and the transient tail
        x3, w3 = xs[3]
        extra += [Rect(x=x3 - 4, y=TAPE_Y - 4, width=w3 + 8, height=TAPE_H + 8, rx=12, cls="infl", data_at_i=3),
                  G(Path(d=f"M{xs[4][0]},{TAPE_Y + TAPE_H + 10}h{end - xs[4][0]}", cls="brace"),
                    T("transient states: after the update the student stops reaching them", x=(xs[4][0] + end) / 2, y=TAPE_Y + TAPE_H + 28,
                      text_anchor="middle", cls="note"), cls="late", data_at_i=len(tokens))]
    n_t = sum(1 for t in tokens if t[1] == "t")
    summary = {"off": f"All {len(tokens)} tokens from the teacher: strong signal, but on text the student would not generate.",
               "ssd": f"{n_t} of {len(tokens)} tokens from the teacher, at the positions where the context changes the answer.",
               "on": "After “mainly”, the rollout never reaches the team lead, and the teacher has little left to correct."}[key]
    return G(*bars, tau_line, *slots, *extra, *parts,
             T(summary, x=X0 - 8, y=TAPE_Y - 16, cls="summary late", data_at_i=len(tokens)),
             cls=f"mode m-{key}", data_mode=key, data_n=len(tokens), data_nt=n_t, data_tau=tau if tau is not None else "inf")


def pi(sub: str, args: str, **kw):
    """π with a real subscript, e.g. π_T( · | x, C)."""
    return T("π", Tspan(sub, dy=4, font_size=11), Tspan(args, dy=-4), **kw)


def cards():
    doc = G(Rect(x=36, y=58, width=26, height=32, rx=3, cls="doc"), Rect(x=31, y=53, width=26, height=32, rx=3, cls="doc"),
            *[Line(x1=36, x2=52, y1=62 + 5 * k, y2=62 + 5 * k, cls="doc-l") for k in range(4)], T("C", x=44, y=108, cls="doc-c"))
    teacher = G(Rect(x=20, y=34, width=192, height=112, rx=14, cls="card t"), doc,
                T("Teacher", x=74, y=66, cls="card-h t"), pi("T", "( · | x, C)", x=74, y=89, cls="card-s"),
                T("reads the document", x=74, y=110, cls="card-n"), cls="intro")
    student = G(Rect(x=20, y=318, width=192, height=112, rx=14, cls="card s"),
                T("Student", x=36, y=352, cls="card-h s"), pi("θ", "( · | x)", x=36, y=375, cls="card-s"),
                T("same model, closed-book", x=36, y=396, cls="card-n"), cls="intro")
    prompt = G(Rect(x=20, y=TAPE_Y - 8, width=198, height=TAPE_H + 16, rx=12, cls="prompt"),
               T("“Tell me about the marketing", x=31, y=TAPE_Y + 15, cls="prompt-t"),
               T(" team of the company.”", x=31, y=TAPE_Y + 34, cls="prompt-t"), cls="intro")
    arrows = G(Path(d=f"M110,{TAPE_Y - 10}V150", cls="flow", pathLength=1), Path(d=f"M110,{TAPE_Y + TAPE_H + 10}V314", cls="flow", pathLength=1),
               T("x", x=118, y=TAPE_Y - 26, cls="flow-l"), T("x", x=118, y=TAPE_Y + TAPE_H + 38, cls="flow-l"), cls="arrows")
    strip = G(T("divergence per position", x=20, y=STRIP_BASE - 70, cls="strip-n"),
              Line(x1=X0 - 8, x2=920, y1=STRIP_BASE, y2=STRIP_BASE, cls="strip-base"), cls="intro")
    hud = G(T("δₜ", x=20, y=STRIP_BASE - 34, cls="hud-d"),
            T("", x=20, y=STRIP_BASE - 10, cls="hud-v"),
            T("", x=W - 12, y=22, text_anchor="end", cls="hud-c"), cls="hud")
    return teacher, student, prompt, arrows, strip, hud


def MethodFigure():
    svg = Svg(*cards(), *[mode_group(k) for k in MODES], viewBox=f"0 0 {W} {H}", width="100%", cls="method-svg",
              role="img", aria_label="Animated SSD decoding loop: the student writes by default, the teacher takes over at inflection tokens")
    tabs = Div(*[Button(MODE_LABEL[k], cls="tab" + (" on" if k == "ssd" else ""), data_mode=k, type="button") for k in MODES],
               cls="tabs", role="tablist")
    ctrl = Div(Button("❚❚", cls="play", aria_label="play/pause", type="button"),
               Input(type="range", min=0, max=1000, value=0, cls="scrub", aria_label="timeline"),
               Button("↺", cls="replay", aria_label="replay", type="button"), cls="ctrl")
    return Div(tabs, Div(svg, cls="scroll-x"), ctrl, id="fig-method", data_fig="method", data_loop="1", cls="fig fig-method")
