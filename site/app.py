"""Speculative Self-Distillation: the blog. `python site/app.py` serves on :5001; export/build_static.py freezes it.

Layout follows the Distill-to-Detect project page: sticky site header, centered post heading, cover image,
then [sticky TOC | 660px article | sidenote rail]. Citations and asides are numbered sidenotes.
"""
from itertools import count
from pathlib import Path

from fasthtml.common import *

import figures as F
from method_anim import MethodFigure

HERE = Path(__file__).resolve().parent
PAPER = "https://openreview.net/pdf?id=6DlaA6eBt7"
CODE = "https://anonymous.4open.science/r/Speculative-Self-Distillation/"
POSTER = "static/media/ssd_poster.pdf"   # copy of poster/poster.pdf
TITLE = "Speculative Self-Distillation"
SUBTITLE = "Efficient knowledge internalization with per-token mixed-policy distillation"
TLDR = ("SSD lets the student write its own training rollouts and lets the teacher take over only at tokens where the "
        "document changes the prediction. It matches on-policy self-distillation with 45% fewer supervised tokens on average "
        "and forgets less of the model's general ability.")
DESC = ("SSD lets the student write its own training rollouts and lets the teacher take over only at tokens where the "
        "document changes the prediction, matching on-policy self-distillation with 45% fewer supervised tokens.")
# (name, homepage or None, affiliation marks)
AUTHORS = [("Shayan Talaei", "https://shayantalaei.com/", "*1"), ("Agam Bhatia", "https://agammsbhatia.com/", "*1"),
           ("Arshia Soltani Moakhar", None, "1"), ("Jonas Hübotter", "https://jonhue.github.io/", "2"),
           ("Amin Saberi", "https://stanford.edu/~saberi/", "1"), ("Azalia Mirhoseini", "https://www.azaliamirhoseini.com/", "1")]
MEDIA = [("method loop", "method_ssd"), ("on-policy loop", "method_onpolicy"), ("inflection fork", "fork"), ("signal", "signal"),
         ("headline", "headline"), ("τ frontier", "tau_frontier"), ("curriculum", "curriculum")]
BIBTEX = r"""@misc{talaei2026ssd,
  title  = {Speculative Self-Distillation enables Efficient Knowledge Internalization},
  author = {Talaei, Shayan and Bhatia, Agam and Soltani Moakhar, Arshia and
            H{\"u}botter, Jonas and Saberi, Amin and Mirhoseini, Azalia},
  year   = {2026}
}"""

# key -> (title, short author list, year, url or None); taken from the paper's references.bib
REFS = {
    "liu2024lost": ("Lost in the Middle: How Language Models Use Long Contexts", "Liu et al.", 2024, "https://arxiv.org/abs/2307.03172"),
    "snell2023": ("Learning by Distilling Context", "Snell, Klein and Zhong", 2023, "https://arxiv.org/abs/2209.15189"),
    "kujanpaa": ("Efficient Knowledge Injection in LLMs via Self-Distillation", "Kujanpää, Marttinen, Valpola and Ilin", 2025,
                 "https://arxiv.org/abs/2412.14964"),
    "entigraph": ("Synthetic Continued Pretraining", "Yang et al.", 2025, "https://arxiv.org/abs/2409.07431"),
    "sdft": ("Self-Distillation Enables Continual Learning", "Shenfeld, Damani, Hübotter and Agrawal", 2026, "https://arxiv.org/abs/2601.19897"),
    "skd": ("Speculative Knowledge Distillation: Bridging the Teacher-Student Gap Through Interleaved Sampling", "Xu et al.", 2025,
            "https://arxiv.org/abs/2410.11325"),
    "adaswitch": ("AdaSwitch: Balancing Exploration and Guidance in Knowledge Distillation via Adaptive Switching", "Peng et al.", 2025,
                  "https://arxiv.org/abs/2510.07842"),
    "switch": ("SWITCH: Studying with Teacher for Knowledge Distillation of Large Language Models", "Koo et al.", 2025, None),
    "gkd": ("On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes", "Agarwal et al.", 2024,
            "https://arxiv.org/abs/2306.13649"),
    "dagger": ("A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning", "Ross, Gordon and Bagnell", 2011,
               "https://arxiv.org/abs/1011.0686"),
    "tm_opd": ("On-Policy Distillation", "Lu and Thinking Machines Lab", 2025, "https://thinkingmachines.ai/blog/on-policy-distillation/"),
    "lin1991": ("Divergence Measures Based on the Shannon Entropy", "Lin", 1991, None),
    "leviathan": ("Fast Inference from Transformers via Speculative Decoding", "Leviathan, Kalman and Matias", 2023,
                  "https://arxiv.org/abs/2211.17192"),
    "sciknoweval": ("SciKnowEval: Evaluating Multi-level Scientific Knowledge of Large Language Models", "Feng et al.", 2024,
                    "https://arxiv.org/abs/2406.09098"),
}

hdrs = (
    Meta(name="viewport", content="width=device-width, initial-scale=1"),
    Link(rel="preconnect", href="https://fonts.googleapis.com"),
    Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,600;1,7..72,400"
         "&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"),
    Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css"),
    Script(src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js", defer=True),
    Script(src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js", defer=True),
    Link(rel="icon", type="image/png", href="static/favicon.png"),
    Link(rel="stylesheet", href="static/site.css"),
    Script(src="static/anim.js", defer=True),
    Socials(title=TITLE, site_name=TITLE, description=DESC, image="static/media/cover.png", url=""),
)
app, rt = fast_app(pico=False, hdrs=hdrs, static_path=str(HERE), live=False, default_hdrs=False)

ICON_PAPER = ('<svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
              '<polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>')
ICON_CODE = ('<svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
             'stroke-linejoin="round" aria-hidden="true"><path d="M8 7l-5 5 5 5M16 7l5 5-5 5"/></svg>')


class Notes:
    """Numbered sidenotes (D2D markup: label + hidden checkbox + floated span). One instance per page render."""
    def __init__(self): self.n = count(1)

    def note(self, *c):
        i = next(self.n)
        return (Label(fr=f"sn-{i}", cls="margin-toggle sidenote-number"), Input(type="checkbox", id=f"sn-{i}", cls="margin-toggle"),
                Span(*c, cls="sidenote"))

    def cite(self, *keys):
        parts = []
        for j, k in enumerate(keys):
            title, who, year, url = REFS[k]
            parts += [Br() if j else "", A(title, href=url, target="_blank", rel="noopener") if url else Em(title), f" ({who}, {year})"]
        return self.note(*parts)


def M(tex: str): return Div(f"$${tex}$$", cls="math-display")
def Fig(fig, *caption, wide=True): return Figure(fig, Figcaption(*caption), cls="wide" if wide else "")
def Off(): return Span("off-policy", cls="k-off")
def On(): return Span("on-policy", cls="k-on")


def header():
    return Header(A(Img(src="static/logos/ssd_logo.png", alt="", cls="mark"), TITLE, href="#top", cls="wordmark"),
                  Nav(A("Paper", href=PAPER, target="_blank", rel="noopener"), A("Code", href=CODE, target="_blank", rel="noopener"),
                      A("Poster", href=POSTER, target="_blank", rel="noopener"), A("Cite", href="#citation")), cls="site-header")


def heading():
    authors = []
    for i, (name, url, sup) in enumerate(AUTHORS):
        authors += [", " if i else "", A(name, href=url, target="_blank", rel="noopener") if url else name, Sup(sup)]
    return Div(
        H1(TITLE, cls="post-title"), P(SUBTITLE, cls="post-subtitle"),
        Div(P(*authors, cls="authors"),
            P(NotStr("<sup>*</sup>Equal contribution &nbsp;·&nbsp; <sup>1</sup>Stanford University &nbsp;·&nbsp; <sup>2</sup>ETH Zürich"),
              cls="affiliations"), cls="publish-metadata"),
        Div(A(NotStr(ICON_PAPER), "Paper", href=PAPER, target="_blank", rel="noopener"), Span("·", cls="sep"),
            A(NotStr(ICON_CODE), "Code", href=CODE, target="_blank", rel="noopener"), Span("·", cls="sep"),
            A("Poster", href=POSTER, target="_blank", rel="noopener"), Span("·", cls="sep"),
            A("Cite", href="#citation"), cls="resource-links"),
        Div(Img(src="static/logos/stanford_color.png", alt="Stanford University"), Img(src="static/logos/eth.svg", alt="ETH Zürich", cls="eth"),
            cls="logo-row"),
        P(B("TL;DR "), TLDR, cls="tldr"),
        cls="post-heading", id="top")


TOC = [("setup", "Self-distillation and who writes the rollout"), ("why", "On-policy signal fades after ~15 tokens"),
       ("inflection", "Inflection tokens"), ("method", "Speculative Self-Distillation"), ("results", "On-policy accuracy, 34–57% fewer tokens"),
       ("knob", "One knob from off- to on-policy"), ("curriculum", "The teacher steps back on its own"), ("forgetting", "It also forgets less"),
       ("citation", "Citation")]


def article(n: Notes):
    return Article(
        P("Language models are routinely asked about things they never saw during pretraining: the internal documents of a "
          "company, events that happened after the training cutoff, or the vocabulary of a specialized field. The standard "
          "answer is to put the relevant text in the prompt. This works, but the document has to be processed again on every "
          "query, it competes for limited context, and models do not always make good use of evidence that is in their "
          "context.", *n.cite("liu2024lost"), " When the same knowledge is needed repeatedly, it is more economical to train it "
          "into the weights once."),
        P("Self-distillation does this without labels or a larger model. The model is given the document and acts as a teacher; the same model "
          "without the document is the student, and it is trained to reproduce the teacher's next-token distributions.",
          *n.cite("snell2023"), " Existing methods differ mainly in who generates the text the student is trained on. Off-policy "
          "methods train on text written by the teacher,", *n.cite("kujanpaa"), " while on-policy methods such as "
          "SDFT let the student write and use the teacher only to score each token.", *n.cite("sdft"), " In standard "
          "teacher–student distillation, Speculative Knowledge Distillation (SKD) mixes the two inside a single sequence, letting "
          "the teacher replace student tokens that it considers unlikely.", *n.cite("skd"), " We bring this per-token view to "
          "self-distillation. In ", Strong("Speculative Self-Distillation (SSD)"), " the student writes by default and the "
          "teacher takes over only at tokens where the document changes the prediction. On three knowledge-acquisition tasks, "
          "SSD reaches the accuracy of on-policy self-distillation with 45% fewer supervised tokens on average, and it forgets "
          "less of the model's general ability."),
        Fig(MethodFigure(),
            B("The SSD decoding loop. "), "The student and the teacher are the same model, and only the teacher sees the document ",
            I("C"), ". At each position both produce a next-token distribution (panels above and below the token being decided). "
            "The bars at the bottom show their divergence δ", Sub("t"), "; when it exceeds the threshold τ (dashed line), the teacher "
            "writes the token (orange), otherwise the student does (blue). The tabs replay the same prompt under off-policy (τ → 0), "
            "SSD and on-policy (τ → ∞) generation. Tokens follow the paper's running example; the distributions and δ values are "
            "illustrative."),

        H2("Self-distillation and who writes the rollout", id="setup"),
        P("Let $x$ be a prompt and $C$ the privileged context, for example a document. The teacher $\\pi_T(\\cdot\\mid x, C)$ is the "
          "base model with $C$ in its context, and the student $\\pi_\\theta(\\cdot\\mid x)$ is the same model without it. The goal "
          "is to update $\\theta$ so that the student behaves like the teacher on new prompts, without being given $C$. All the "
          "methods we compare minimize the same token-level objective:",
          *n.note("Throughout, the teacher is kept frozen at the initial weights, so every method is trained toward the same target.")),
        M("\\mathcal{L}(\\theta)=\\mathbb{E}_{y\\sim\\pi_{\\text{gen}}}\\Big[\\tfrac{1}{|y|}\\sum_t D\\big(\\pi_T(\\cdot\\mid x,C,y_{<t})"
          "\\,\\|\\,\\pi_\\theta(\\cdot\\mid x,y_{<t})\\big)\\Big]"),
        P("where $D$ is a divergence between the two next-token distributions, such as forward KL, reverse KL or the Jensen–Shannon "
          "divergence (JSD).", *n.cite("lin1991"), " What distinguishes the methods is the rollout policy $\\pi_{\\text{gen}}$: the "
          "model that writes the sequence $y$ on which the loss is computed."),
        P("Setting $\\pi_{\\text{gen}} = \\pi_T$ gives ", Off(), " self-distillation: the teacher writes the response and the student "
          "imitates it. Every position lies on a well-informed trajectory, but at test time the student has to continue from its "
          "own prefixes, which it never practiced on, a form of exposure bias familiar from imitation learning.", *n.cite("dagger"),
          " Setting $\\pi_{\\text{gen}} = \\pi_\\theta$ gives ", On(), " self-distillation: the student writes the response and the "
          "teacher scores every token of it.", *n.cite("gkd", "sdft"), " Training and test-time behavior then match, and on-policy "
          "training reaches higher accuracy, but it is considerably slower.", *n.cite("tm_opd")),

        H2("On-policy signal fades after ~15 tokens", id="why"),
        P("In our experiments on-policy training was several times slower than off-policy, so we looked at where its supervision "
          "goes. The per-token loss measures how much the teacher and the student disagree at a position, and therefore how large "
          "an update that token produces; we call it the ", Strong("signal"), ". On the Wikipedia task (Figure 2), the on-policy signal "
          "is high for the first ~15 tokens of each rollout and then drops to a low level for the rest of it."),
        Fig(F.signal(), B("On-policy rollouts lose their training signal after a few tokens. "), "Off- and on-policy self-distillation "
            "on the Wikipedia task. Left: test accuracy against supervised tokens; off-policy converges about five times faster but "
            "plateaus lower. Middle: average per-token loss during training; off-policy rollouts start with more than twice the "
            "signal and use it up quickly. Right: per-token loss by position within a rollout; along on-policy rollouts it drops "
            "from around 2 to below 1 within the first 15 tokens, while off-policy rollouts stay high."),
        P("Off-policy training converges about five times faster, consistent with prior work, but "
          "on-policy training reaches a higher final accuracy. Off-policy rollouts start with more than twice the per-token signal "
          "and reduce it quickly. And along on-policy rollouts, the signal is concentrated in the first few tokens. The student "
          "writes without the document, so it soon reaches states that have little to do with it; conditioned on such a prefix, "
          "the teacher's distribution falls back to one close to the student's, and there is little left to correct."),
        P("Most of the supervised tokens in on-policy training are therefore spent on positions where the teacher adds little "
          "information."),

        H2("Inflection tokens", id="inflection"),
        P("In the example of Figure 3, asked about the marketing team of the company described in the memo, the student and the "
          "teacher agree on the opening words “Marketing team is”. At the fourth token they diverge: the teacher, which has read "
          "the memo, continues with “led by Lina Okafor”, while the student writes the generic “mainly focused on creating the …”. "
          "We call such a position an ", Strong("inflection position"), ". Given a rollout and a threshold τ, position $t$ is a "
          "τ-inflection position if"),
        M("\\delta_t = D_{\\text{switch}}\\big(\\pi_\\theta(\\cdot\\mid x,y_{<t}) \\,\\|\\, \\pi_T(\\cdot\\mid x,C,y_{<t})\\big) > \\tau,"),
        P("where $D_{\\text{switch}}$ is any divergence between the two next-token distributions."),
        Fig(F.fork(), B("Two continuations of the same prefix. "), "Student and teacher agree up to “Marketing team is”, and the next "
            "token is an inflection position (δ", Sub("t"), " > τ). SSD lets the teacher write it, and the rollout goes on to name the "
            "team lead and the team size. On-policy keeps the student's “mainly”; the grey tokens after it are transient states, "
            "which the student will rarely visit once the update has corrected the inflection."),
        P("At an inflection position the loss pushes the student strongly away from its original prediction, so after the update "
          "it is unlikely to write “mainly” in this context again. The states that follow in the on-policy rollout were generated by "
          "a policy that the update is changing, and the student will rarely visit them again. We call them ",
          Strong("transient states"), ", and supervision on them is of limited use. On-policy training learns about each inflection "
          "position separately, over many updates, whereas an off-policy rollout contains the team lead, the team size and the "
          "remaining details in a single pass, but on text the student would not have written."),

        H2("Speculative Self-Distillation", id="method"),
        P("SSD keeps the rollout on the student wherever the student already agrees with the teacher, and switches to the teacher "
          "where it does not. The student generates by default. At every position both models produce their next-token "
          "distributions; if their divergence exceeds τ, the position is an inflection position and the teacher samples the token. "
          "Otherwise the student does. Every position is trained with the same loss as before, so the only change is in how the "
          "rollout is generated."),
        Pre(Code(Span("for", cls="kw"), " t = 1, 2, … until EOS:\n"
                 "    p_S, p_T = student(x, y<t), teacher(x, C, y<t)\n",
                 Span("    if D_switch(p_S ‖ p_T) > τ:", cls="hl"), "   ", Span("# inflection position", cls="cm"), "\n"
                 "        y_t ~ p_T                  ", Span("# teacher writes", cls="cm t"), "\n"
                 "    else:\n"
                 "        y_t ~ p_S                  ", Span("# student writes", cls="cm s"), "\n"
                 "    loss += D_loss(p_T ‖ p_S)      ", Span("# every position is supervised", cls="cm"), "\n"), cls="algo"),
        P("The name comes from speculative decoding, in which a small draft model proposes tokens and a larger model verifies "
          "them.", *n.cite("leviathan"), " Several distillation methods already switch between student and teacher inside a "
          "sequence: SKD resamples low-confidence student tokens from the teacher's top-K distribution,", *n.cite("skd"),
          " AdaSwitch hands over to the teacher once a sliding-window KL divergence exceeds a threshold,", *n.cite("adaswitch"),
          " and SWITCH uses a per-position divergence criterion.", *n.cite("switch"), " These methods distill a separate teacher "
          "into a student. In self-distillation the two models share their weights and differ only in the privileged context, so "
          "the divergence between them indicates directly where the context changes the prediction."),
        P("The threshold τ is the only new hyperparameter. Setting τ → 0 lets the teacher write every token and recovers off-policy "
          "distillation; τ → ∞ never hands over and recovers on-policy distillation.",
          *n.note("With JSD as $D_{\\text{switch}}$ the divergence is bounded by $\\ln 2 \\approx 0.69$, so any larger τ is exactly "
                  "on-policy."),
          " The divergence used for routing need not be the one used for training: $D_{\\text{switch}}$ decides who writes a token, "
          "and $D_{\\text{loss}}$ trains the student."),

        H2("On-policy accuracy with 34–57% fewer tokens", id="results"),
        P("We follow the evaluation protocol of SDFT", *n.cite("sdft"), " and use Qwen3-4B-Instruct as both student and teacher. The "
          "three tasks cover different reasons to internalize knowledge. ", Strong("Company Memo"), " is a synthetic internal "
          "document about a fictional cooperative, standing in for private organizational knowledge. ", Strong("Wikipedia"),
          " uses an article on Cyclone Ditwah, which postdates the model's training data and on which the base model scores below "
          "20%. ", Strong("Science Q&A"), " is the Chemistry L-3 subset of SciKnowEval,", *n.cite("sciknoweval"), " which requires "
          "reasoning with domain knowledge rather than recalling a fact. We compare against the off-policy baselines SFT and FKL "
          "and the on-policy baseline SDFT."),
        P("We measure cost in ", Em("supervised tokens"), ", the number of response positions on which the loss is computed. This is "
          "roughly proportional to compute, and it is a fairer comparison than optimizer steps: on-policy rollouts are longer than "
          "off-policy ones, so each on-policy step costs more."),
        P("Supervised tokens do not capture everything. SSD needs the teacher's next-token distribution at every decoding step, "
          "whereas on-policy training can score a finished rollout with a single parallel teacher pass. Because teacher and "
          "student share weights, both forward passes can run in the same batch at each step, but the teacher pass still happens "
          "during generation."),
        Fig(F.headline(), B("SSD reaches on-policy accuracy with 34–57% fewer supervised tokens. "), "Test accuracy against cumulative "
            "supervised tokens on Company Memo, Wikipedia and Science Q&A for the best off-policy baseline (SFT or FKL), on-policy "
            "SDFT and SSD. Arrows mark the savings at the on-policy plateau. The slider compares the methods at the same budget, as a "
            "fraction of the on-policy run; dots are individual evaluations and lines are smoothed."),
        P("On all three tasks the baselines show the same trade-off. Off-policy training improves quickly but levels off below the "
          "best accuracy; on-policy training reaches a higher plateau only after much more supervision. SSD follows the steep early "
          "part of the off-policy curve and then keeps improving to the on-policy plateau, which it reaches with 44%, 34% and 57% "
          "fewer supervised tokens. On Science Q&A it finishes about 3 points above on-policy and 15 points above off-policy."),

        H2("One knob from off- to on-policy", id="knob"),
        P("Figure 5 sweeps the threshold on Company Memo. At small τ the teacher intervenes often: few tokens are supervised and "
          "final accuracy is close to off-policy. As τ grows, more of each rollout is written by the student, and accuracy rises "
          "toward the on-policy level along with the cost. Intermediate thresholds reach higher accuracy than off-policy while "
          "converging faster than on-policy, so SSD traces a Pareto frontier between the two. With JSD as the switching divergence, "
          "τ between 0.2 and 0.5 is a good default."),
        Fig(F.tau_frontier(), B("The threshold τ traces a Pareto frontier. "), "Final test accuracy against supervised tokens for SSD "
            "with JSD thresholds from 0 to 0.75, with the off- and on-policy baselines (Company Memo, Qwen3-4B-Instruct). Small τ "
            "sits next to off-policy and large τ next to on-policy; τ between 0.2 and 0.5 (shaded) reaches most of the on-policy "
            "accuracy at close to off-policy cost. The y-axis spans 88–94%, so nearby thresholds differ by only a point or two. The "
            "curve is a guide to the eye; hover over a point for its values.", wide=False),

        H2("The teacher steps back on its own", id="curriculum"),
        P("SSD has no schedule for how much the teacher participates, and Figure 6 shows that none is needed. Early in training the student and the teacher disagree at many positions, and the teacher "
          "writes a large share of each rollout, up to 40% of tokens at the lowest threshold. As the student learns the document, "
          "the switch fires less often and teacher involvement decays for every threshold."),
        Fig(F.curriculum(), B("Teacher involvement decays without a schedule. "), "SSD on Company Memo with four JSD thresholds. Left: "
            "fraction of rollout tokens written by the teacher at each training step. Right: mean response length. Lower thresholds "
            "use the teacher more at the start, and all runs move toward student-written rollouts and similar response lengths."),
        P("Response lengths follow the same pattern. With a high threshold the student keeps control for longer before enough "
          "divergence builds up to trigger the teacher, so early rollouts are long and variable. As training proceeds, lengths "
          "settle and converge across thresholds. The teacher is used heavily while the student lacks the knowledge, and its share "
          "falls as the student learns, until training is close to on-policy."),

        H2("It also forgets less", id="forgetting"),
        P("We also measure how much each method degrades the model's general capabilities. SDFT showed that on-policy self-distillation forgets less than "
          "supervised fine-tuning,", *n.cite("sdft"), " and because SSD keeps rollouts close to the student's distribution we "
          "expected it to share this property. With Qwen3-4B we saw little forgetting under any method, likely because the model "
          "was already post-trained on data resembling the evaluation suite. We therefore follow the SDFT protocol and fine-tune "
          "Qwen2.5-7B on SciKnowEval chemistry, measuring in-domain accuracy against the average change on six general benchmarks."),
        Fig(F.forgetting(), B("SSD learns the new domain with the least forgetting. "), "In-domain accuracy on SciKnowEval chemistry "
            "against the average change on six general benchmarks (HellaSwag, HumanEval, IFEval, MMLU, TruthfulQA, Winogrande) after "
            "fine-tuning Qwen2.5-7B. Labels give supervised tokens. Up and to the right is "
            "better.", wide=False),
        P("The off-policy methods SFT and FKL learn the new skill but lose about 6.6 points on the general benchmarks. On-policy "
          "SDFT loses 4.5 at comparable in-domain accuracy. SSD has both the highest in-domain accuracy (71.6, against 68.4 for "
          "SDFT) and the smallest loss (−1.4), while using 22% fewer supervised tokens than SDFT."),

        H2("Citation", id="citation"),
        Div(Button("copy", cls="copy", type="button"), Pre(BIBTEX, cls="citation-block bib"), cls="bibwrap"),
        cls="content")


CAPTURE = {"method": MethodFigure, "fork": F.fork, "signal": F.signal, "headline": F.headline,
           "tau_frontier": F.tau_frontier, "curriculum": F.curriculum, "forgetting": F.forgetting}


@rt
def index(capture: str = ""):
    if capture in CAPTURE:
        return Title(f"SSD · {capture}"), Main(CAPTURE[capture](), cls=f"capture-main cap-{capture}", data_capture=capture)
    return (Title(TITLE), Meta(name="description", content=DESC),
            header(), heading(),
            Div(Img(src="static/media/cover.png", alt="A student robot writes a path of blue tokens while a teacher robot in a "
                    "graduation cap, reading a book, places orange tokens at the forks; the abandoned branch fades out"), cls="post-cover"),
            Div(Nav(Ul(*[Li(A(t, href=f"#{i}", data_sec=i)) for i, t in TOC]), cls="left-toc", aria_label="Table of contents"),
                article(Notes()), cls="post-shell"),
            Footer(P("Speculative Self-Distillation · Stanford University and ETH Zürich · 2026"), cls="site-footer"))


serve(port=5001, reload=False)
