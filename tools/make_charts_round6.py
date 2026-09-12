# -*- coding: utf-8 -*-
"""Round-6 charts: full context curve + final config evolution."""
import os, html

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(OUT, exist_ok=True)

FONT = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
GOLD = "#d97706"
BLUE = "#2563eb"
GRAY = "#94a3b8"
DARK = "#0f172a"
MUTED = "#64748b"
GREEN = "#059669"
RED = "#dc2626"


def head(w, h, title, subtitle=""):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">']
    s.append(f'<rect width="{w}" height="{h}" rx="12" fill="#ffffff"/>')
    s.append(f'<text x="24" y="34" font-family="{FONT}" font-size="19" font-weight="700" fill="{DARK}">{html.escape(title)}</text>')
    if subtitle:
        s.append(f'<text x="24" y="56" font-family="{FONT}" font-size="12.5" fill="{MUTED}">{html.escape(subtitle)}</text>')
    return s


def save(name, s):
    s.append('</svg>')
    p = os.path.join(OUT, name)
    open(p, "w", encoding="utf-8").write("\n".join(s))
    print("wrote", p)


# ---- Chart 9: full context curve (150-192K) ----
def chart_context_full():
    W, H = 960, 470
    s = head(W, H, "Full Context Sweep — Vision Mode Safe up to 180K, Text up to 190K",
             "Qwen3.8-27B NVFP4-LOW · self-built CUDA 13.3 · -np 1 · 512-token runs · the curve is NON-MONOTONIC (allocation alignment effects)")
    x0, y0, w, h = 70, 105, 850, 260
    labels = ["150K", "152K", "155K", "158K", "160K", "170K", "180K", "182K", "184K", "186K", "188K", "190K", "192K"]
    values = [81.4, 82.0, 86.8, 86.5, 82.7, 85.7, 83.9, 59.2, 61.0, 62.2, 81.2, 86.7, 63.1]
    base = y0 + h
    mv = 100.0
    for i in range(5):
        gy = base - h * i / 4
        s.append(f'<line x1="{x0}" y1="{gy:.1f}" x2="{x0 + w}" y2="{gy:.1f}" stroke="#e2e8f0" stroke-width="1"/>')
        s.append(f'<text x="{x0 - 8}" y="{gy + 4:.1f}" font-family="{FONT}" font-size="11" fill="{MUTED}" text-anchor="end">{int(mv * i / 4)}</text>')
    # bars
    slot = w / len(values)
    bw = slot * 0.62
    for i, (lab, v) in enumerate(zip(labels, values)):
        cx = x0 + slot * (i + 0.5)
        bh = h * v / mv
        by = base - bh
        c = GREEN if v >= 75 else RED
        s.append(f'<rect x="{cx - bw/2:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{c}"/>')
        s.append(f'<text x="{cx:.1f}" y="{by - 6:.1f}" font-family="{FONT}" font-size="11.5" font-weight="700" fill="{DARK}" text-anchor="middle">{v:.0f}</text>')
        s.append(f'<text x="{cx:.1f}" y="{base + 16:.1f}" font-family="{FONT}" font-size="10.5" fill="{MUTED}" text-anchor="middle">{lab}</text>')
    # markers
    # vision safe line at 180K (index 6)
    cx180 = x0 + slot * 6.5
    s.append(f'<line x1="{cx180:.1f}" y1="{y0 - 5}" x2="{cx180:.1f}" y2="{base + 22}" stroke="{BLUE}" stroke-width="2" stroke-dasharray="5,3"/>')
    s.append(f'<text x="{cx180:.1f}" y="{y0 - 12}" font-family="{FONT}" font-size="12" font-weight="700" fill="{BLUE}" text-anchor="middle">vision safe ceiling</text>')
    # text best at 190K (index 11)
    cx190 = x0 + slot * 11.5
    s.append(f'<text x="{cx190:.1f}" y="{y0 - 12}" font-family="{FONT}" font-size="12" font-weight="700" fill="{GOLD}" text-anchor="middle">text optimum</text>')
    # oscillation zone
    s.append(f'<rect x="{x0 + slot*7:.1f}" y="{y0 - 3}" width="{slot*3:.1f}" height="{h + 6}" fill="{RED}" opacity="0.06"/>')
    s.append(f'<text x="{x0 + slot*8.5:.1f}" y="{base - 12}" font-family="{FONT}" font-size="10.5" fill="{RED}" text-anchor="middle">oscillation valley (avoid)</text>')
    s.append(f'<text x="24" y="{H - 22}" font-family="{FONT}" font-size="11.5" fill="{MUTED}">Green = usable (≥75 tok/s), red = valley. Correction: the earlier "152K collapse" was an artifact of the default -np 4 config.</text>')
    save("chart9-context-full-curve.svg", s)


# ---- Chart 10: evolution of the final config ----
def chart_evolution():
    W, H = 960, 420
    s = head(W, H, "Final Config Evolution — Where the Gains Came From",
             "RTX 5090 Laptop 24GB · Qwen3.8-27B NVFP4 · start of tuning → today")
    # rows: metric, before, after, before_label, after_label
    rows = [
        ("Context (vision mode)", 150, 180, "150K", "180K"),
        ("Decode (tok/s, mid-range)", 79.6, 83.9, "79.6", "83.9"),
        ("Prefill 4K (tok/s)", 1482, 1692, "1482", "1692"),
        ("Vision latency (s)", 6.1, 4.2, "6.1s", "4.2s"),
        ("Thinking control", 0, 100, "no", "budget+template"),
        ("Engine", 0, 100, "official", "self-built 13.3"),
    ]
    y = 100
    rh = 46
    x0 = 300
    scale_w = 380
    for i, (label, before, after, bl, al) in enumerate(rows):
        yy = y + i * rh
        s.append(f'<text x="{x0 - 14}" y="{yy + 22}" font-family="{FONT}" font-size="12.5" fill="{DARK}" text-anchor="end">{html.escape(label)}</text>')
        # before value (gray, fixed width marker)
        s.append(f'<rect x="{x0}" y="{yy + 8}" width="46" height="20" rx="4" fill="{GRAY}"/>')
        s.append(f'<text x="{x0 + 23}" y="{yy + 22}" font-family="{FONT}" font-size="10.5" fill="#ffffff" text-anchor="middle">{html.escape(bl)}</text>')
        # arrow
        s.append(f'<path d="M {x0 + 54} {yy + 18} l 14 0 m -5 -5 l 5 5 l -5 5" stroke="{MUTED}" stroke-width="1.6" fill="none"/>')
        # after value (green)
        wdt = 100
        s.append(f'<rect x="{x0 + 78}" y="{yy + 8}" width="{wdt}" height="20" rx="4" fill="{GREEN}"/>')
        s.append(f'<text x="{x0 + 78 + wdt/2}" y="{yy + 22}" font-family="{FONT}" font-size="10.5" fill="#ffffff" text-anchor="middle">{html.escape(al)}</text>')
    s.append(f'<text x="24" y="{H - 22}" font-family="{FONT}" font-size="11.5" fill="{MUTED}">Gray = starting point, green = today. The biggest single win: removing the default -np 4 (freed 1.15GB VRAM → +30K context).</text>')
    save("chart10-config-evolution.svg", s)


chart_context_full()
chart_evolution()
print("done")
