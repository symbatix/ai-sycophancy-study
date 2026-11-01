#!/usr/bin/env python3
"""Build the article's inline SVG charts from results/summary.csv.

  python3 charts.py      # writes results/charts/*.html (SVG snippets styled by the site's .chart classes)
"""
import csv, html, os

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "results", "charts")
rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "summary.csv"))))
LABS = ["OpenAI", "Anthropic", "Google", "DeepSeek", "xAI"]
SHORT = {"GPT-3.5 Turbo (0613)": "3.5", "GPT-4": "4", "GPT-4o (2024-05-13)": "4o May", "GPT-4o (2024-11-20)": "4o Nov",
         "GPT-4.1": "4.1", "GPT-5": "5", "GPT-5.2": "5.2", "GPT-5.5": "5.5", "GPT-6.1 Sol": "6.1 Sol",
         "Claude Opus 4.1": "Opus 4.1", "Claude Sonnet 4.5": "Son. 4.5", "Claude Sonnet 4.6": "Son. 4.6",
         "Claude Sonnet 5": "Son. 5", "Claude Sonnet 5.5": "Son. 5.5", "Claude Opus 5.5": "Opus 5.5",
         "Gemini 2.5 Flash": "2.5 Flash", "Gemini 3 Flash (preview)": "3 Flash", "Gemini 3.5 Flash": "3.5 Flash",
         "Gemini 4 Argon": "4 Argon", "DeepSeek V3": "V3", "DeepSeek R1 (0528)": "R1", "DeepSeek V3.2": "V3.2",
         "DeepSeek V4.1 Flash": "V4.1", "Grok 4.20": "4.20", "Grok 4.7": "4.7"}
FAMILY = {"OpenAI": "GPT", "Anthropic": "Claude", "Google": "Gemini", "DeepSeek": "DeepSeek", "xAI": "Grok"}
esc = html.escape


def by_lab(lab):
    return sorted([r for r in rows if r["family"] == lab], key=lambda r: (r["released"], r["model"] != "GPT-3.5 Turbo (0613)"))


def dumbbell():
    """Oldest vs newest model per lab: average score on the same flawed work (neutral framing)."""
    data = []
    for lab in LABS:
        rs = by_lab(lab)
        old, new = rs[0], rs[-1]
        data.append((lab, old["model"], float(old["mean_score_neutral"]), new["model"], float(new["mean_score_neutral"])))
    data.sort(key=lambda d: d[2] - d[4], reverse=True)
    W, left, right, top, rowh = 640, 250, 600, 8, 58
    x = lambda v: left + (v - 4) / 4 * (right - left)
    H = top + rowh * len(data) + 26
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-labelledby="f1t">',
           '<title id="f1t">Average score on the same flawed work, oldest vs newest model tested per lab</title>']
    for t in range(4, 9):
        out.append(f'<line class="grid" x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{top}" y2="{H - 22}"/>'
                   f'<text class="tick" x="{x(t):.1f}" y="{H - 6}" text-anchor="middle">{t}</text>')
    for i, (lab, om, ov, nm, nv) in enumerate(data):
        cy = top + rowh * i + rowh / 2
        out.append(f'<text class="row-label" x="0" y="{cy - 3:.1f}">{lab}</text>'
                   f'<text class="row-sub" x="0" y="{cy + 13:.1f}">{esc(om)} → {esc(nm)}</text>'.replace("Turbo (0613)", "Turbo"))
        out.append(f'<line class="link" x1="{x(nv):.1f}" x2="{x(ov):.1f}" y1="{cy:.1f}" y2="{cy:.1f}"/>')
        out.append(f'<g class="pt" tabindex="0"><title>{esc(om)}: {ov:.1f} / 10</title>'
                   f'<circle class="dot-old" cx="{x(ov):.1f}" cy="{cy:.1f}" r="5.5"/></g>'
                   f'<text class="val-muted" x="{x(ov) + 11:.1f}" y="{cy + 4:.1f}">{ov:.1f}</text>')
        out.append(f'<g class="pt" tabindex="0"><title>{esc(nm)}: {nv:.1f} / 10</title>'
                   f'<circle class="dot-new" cx="{x(nv):.1f}" cy="{cy:.1f}" r="5.5"/></g>'
                   f'<text class="val" x="{x(nv) - 11:.1f}" y="{cy + 4:.1f}" text-anchor="end">{nv:.1f}</text>')
    out.append("</svg>")
    return "\n".join(out), data


def multiple(lab, W):
    """Authorship bonus per model version, oldest to newest, with 95% intervals."""
    rs = by_lab(lab)
    H, left, right, top, bottom = 172, 34, W - 14, 12, 132
    lo_v, hi_v = -0.3, 0.75
    y = lambda v: bottom - (v - lo_v) / (hi_v - lo_v) * (bottom - top)
    n = len(rs)
    step = (right - left) / n
    x = lambda i: left + step * (i + 0.5)
    out = [f'<svg class="chart" viewBox="0 0 {W} {H}" role="img" aria-label="{FAMILY[lab]} authorship bonus by version">']
    for t in (0.0, 0.25, 0.5):
        cls = "zero" if t == 0 else "grid"
        lab_t = "0" if t == 0 else f"+{t:g}"
        out.append(f'<line class="{cls}" x1="{left}" x2="{right}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>'
                   f'<text class="tick" x="{left - 6}" y="{y(t) + 4:.1f}" text-anchor="end">{lab_t}</text>')
    pts = []
    for i, r in enumerate(rs):
        v, lo, hi = float(r["self_minus_coworker"]), float(r["ci_low"]), float(r["ci_high"])
        out.append(f'<line class="ci" x1="{x(i):.1f}" x2="{x(i):.1f}" y1="{y(min(hi, hi_v)):.1f}" y2="{y(max(lo, lo_v)):.1f}"/>')
        pts.append((x(i), y(v), v, r))
        out.append(f'<text class="tick" x="{x(i):.1f}" y="{H - 22}" text-anchor="middle">{esc(SHORT[r["model"]])}</text>')
    out.append('<polyline class="series" points="' + " ".join(f"{px:.1f},{py:.1f}" for px, py, _, _ in pts) + '"/>')
    for k, (px, py, v, r) in enumerate(pts):
        tip = f'{r["model"]}: {v:+.2f} points (95% CI {float(r["ci_low"]):+.2f} to {float(r["ci_high"]):+.2f})'
        out.append(f'<g class="pt" tabindex="0"><title>{esc(tip)}</title><circle class="hit" cx="{px:.1f}" cy="{py:.1f}" r="12"/>'
                   f'<circle class="dot-new" cx="{px:.1f}" cy="{py:.1f}" r="4.5"/></g>')
        if k in (0, len(pts) - 1) or v == max(p[2] for p in pts):
            out.append(f'<text class="val" x="{px:.1f}" y="{py - 10:.1f}" text-anchor="middle">{v:+.2f}</text>')
    out.append(f'<text class="row-sub" x="{left}" y="{H - 4}">oldest → newest tested</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    svg, data = dumbbell()
    open(os.path.join(OUT, "fig1-scores.html"), "w").write(svg)
    for lab, om, ov, nm, nv in data:
        print(f"{lab:10} {om} {ov:.2f} -> {nm} {nv:.2f}  drop {ov - nv:.2f}")
    parts = ['<div class="multiples">']
    for lab in LABS:
        wide = lab in ("OpenAI", "Anthropic")
        parts.append(f'<div class="{"wide" if wide else ""}"><div class="multiple-title">{FAMILY[lab]}</div>{multiple(lab, 640 if wide else 310)}</div>')
    parts.append("</div>")
    open(os.path.join(OUT, "fig2-bonus.html"), "w").write("\n".join(parts))
    print("wrote", OUT)
