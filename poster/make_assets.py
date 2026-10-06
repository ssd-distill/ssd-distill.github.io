"""Poster assets that the paper doesn't already provide: forgetting plot, vector logo PDFs, QR codes.

usage (from repo root): uv run python poster/make_assets.py
"""
import json
import re
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import segno
from playwright.sync_api import sync_playwright

matplotlib.use("Agg")
ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "poster/figures"
C = {"off": "#ff751f", "ssd": "#3ccb81", "on": "#0cc0df"}    # the paper's plot colors
CARDINAL = "#8c1515"
LINKS = {"paper": "https://openreview.net/forum?id=6DlaA6eBt7", "blog": "https://ssd-distill.github.io/"}


def forgetting():
    """SciQA vs mean change on 6 general benchmarks (Table 1), styled like the paper's matplotlib figures."""
    rows = json.loads((ROOT / "data/forgetting.json").read_text())["rows"]
    plt.rcParams.update({"font.size": 15, "axes.labelweight": "bold", "axes.labelsize": 18})
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    place = {"SFT": (8, -24, "left"), "FKL": (-12, 10, "right"), "SDFT": (12, 0, "left"), "SSD": (-14, -6, "right")}
    for r in rows:
        ax.plot(r["sciqa"], r["delta"], "o", ms=12 if r["method"] == "SSD" else 10, color=C[r["kind"]], mec="white", mew=1.5, zorder=3)
        dx, dy, ha = place[r["method"]]
        ax.annotate(f"{r['method']}", (r["sciqa"], r["delta"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    fontsize=15, fontweight="bold")
    ax.axhline(0, color="#999", lw=1, ls="--")
    ax.text(72.9, -0.35, "base model", ha="right", va="top", color="#777", fontsize=13)
    ax.annotate("", xy=(72.3, -2.4), xytext=(71.6, -3.3), arrowprops=dict(arrowstyle="->", color="#555", lw=1.6))
    ax.text(72.2, -3.45, "better", ha="center", va="top", color="#555", fontsize=13)
    ax.set_xlim(66, 73); ax.set_ylim(-8, 0.5)
    ax.set_xlabel("In-domain SciQA (%)"); ax.set_ylabel("Δ general benchmarks")
    ax.grid(alpha=.3); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(FIG / "forgetting.pdf", transparent=True); plt.close(fig)


def logos(pw):
    """SVG wordmarks -> vector PDFs sized to the artwork (XeLaTeX can't include SVG directly)."""
    b = pw.chromium.launch()
    for name, white in [("stanford", False), ("eth", False), ("stanford", True), ("eth", True)]:
        svg = (ROOT / f"site/static/logos/{name}.svg").read_text()
        svg = svg[svg.index("<svg"):]
        if "viewBox" not in svg:   # ETH ships width/height only; give it a viewBox so it scales
            w = re.search(r'width="([\d.]+)"', svg).group(1); h = re.search(r'height="([\d.]+)"', svg).group(1)
            svg = svg.replace("<svg ", f'<svg viewBox="0 0 {w} {h}" ', 1)
        svg = re.sub(r'\s(width|height)="[^"]*"', "", svg[:svg.index(">")], count=2) + svg[svg.index(">"):]
        pg = b.new_page()
        pg.set_content(f"<html><body style='margin:0'><div id=l style='display:inline-block;height:200px'>{svg}</div></body></html>")
        pg.add_style_tag(content="#l svg{height:200px;width:auto;display:block}" + ("#l svg *{fill:#fff !important}" if white else ""))
        box = pg.locator("#l svg").bounding_box()
        pg.pdf(path=str(FIG / f"logo_{name}{'_white' if white else ''}.pdf"), width=f"{box['width']:.0f}px", height=f"{box['height']:.0f}px",
               print_background=False, page_ranges="1")
    b.close()


def qr():
    """QR codes as plain vector paths (segno's own PDF output trips up xdvipdfmx), on a white tile with a quiet zone."""
    from matplotlib.patches import Rectangle
    for name, url in LINKS.items():
        m = [list(r) for r in segno.make(url, error="m").matrix]
        n, q = len(m), 2     # q = quiet-zone modules
        fig = plt.figure(figsize=(4, 4), facecolor="white"); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
        ax.set_xlim(-q, n + q); ax.set_ylim(n + q, -q)
        for y, row in enumerate(m):
            for x, v in enumerate(row):
                if v: ax.add_patch(Rectangle((x, y), 1.02, 1.02, color=CARDINAL, lw=0))
        fig.savefig(FIG / f"qr_{name}.pdf"); plt.close(fig)


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    forgetting(); qr()
    with sync_playwright() as pw: logos(pw)
    print(sorted(p.name for p in FIG.iterdir()))
