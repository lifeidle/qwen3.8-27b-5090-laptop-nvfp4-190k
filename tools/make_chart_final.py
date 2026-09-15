# -*- coding: utf-8 -*-
"""Final performance chart for the production config (after the q4_0 + 256K findings)."""
import os, html

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(OUT, exist_ok=True)

FONT = "-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
GREEN = "#059669"
BLUE = "#2563eb"
GOLD = "#d97706"
DARK = "#0f172a"
MUTED = "#64748b"
LIGHT = "#e2e8f0"


def head(w, h, title, subtitle=""):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">']
    s.append(f'<rect width="{w}" height="{h}" rx="12" fill="#ffffff"/>')
    s.append(f'<text x="26" y="36" font-family="{FONT}" font-size="20" font-weight="700" fill="{DARK}">{html.escape(title)}</text>')
    if subtitle:
        s.append(f'<text x="26" y="58" font-family="{FONT}" font-size="12.5" fill="{MUTED}">{html.escape(subtitle)}</text>')
    return s


def save(name, s):
    s.append('</svg>')
    p = os.path.join(OUT, name)
    open(p, "w", encoding="utf-8").write("\n".join(s))
    print("wrote", p)


# ============ Chart 11: FINAL PERFORMANCE ============
def chart_final():
    W, H = 1000, 560
    s = head(W, H, "Final Performance — Qwen3.8-27B on RTX 5090 Laptop 24GB",
             "Production config: NVFP4-MTP-LOW · self-built CUDA 13.3 · 256K context · q4_0 KV · MTP n-max 3 · vision ON · -np 1")

    # --- KPI cards (top) ---
    kpis = [
        ("81.8", "tok/s", "generation (median of 8)", GREEN),
        ("0.17", "s", "time to first token (short)", BLUE),
        ("2.9", "s", "per image (vision)", GOLD),
        ("256K", "ctx", "hard ceiling (model)", DARK),
    ]
    for i, (val, unit, label, color) in enumerate(kpis):
        x = 26 + i * 240
        s.append(f'<rect x="{x}" y="76" width="222" height="104" rx="10" fill="#f8fafc" stroke="{LIGHT}"/>')
        s.append(f'<text x="{x+16}" y="{126}" font-family="{FONT}" font-size="34" font-weight="700" fill="{color}">{val}</text>')
        s.append(f'<text x="{x+16+len(val)*21}" y="{126}" font-family="{FONT}" font-size="14" fill="{MUTED}">{unit}</text>')
        s.append(f'<text x="{x+16}" y="{152}" font-family="{FONT}" font-size="11.5" fill="{MUTED}">{html.escape(label)}</text>')

    # --- decode stability (left bottom) ---
    s.append(f'<text x="26" y="222" font-family="{FONT}" font-size="14" font-weight="700" fill="{DARK}">Generation stability — 8 consecutive 512-token runs</text>')
    runs = [79.0, 81.6, 84.6, 82.0, 90.1, 81.5, 83.7, 81.1]
    x0, y0, w, h = 60, 250, 380, 150
    base = y0 + h
    mx = 100
    for i in range(5):
        gy = base - h * i / 4
        s.append(f'<line x1="{x0}" y1="{gy:.0f}" x2="{x0+w}" y2="{gy:.0f}" stroke="{LIGHT}"/>')
        s.append(f'<text x="{x0-8}" y="{gy+4:.0f}" font-family="{FONT}" font-size="10" fill="{MUTED}" text-anchor="end">{int(mx*i/4)}</text>')
    bw = w / len(runs) * 0.55
    for i, v in enumerate(runs):
        cx = x0 + w / len(runs) * (i + 0.5)
        bh = h * v / mx
        s.append(f'<rect x="{cx-bw/2:.0f}" y="{base-bh:.0f}" width="{bw:.0f}" height="{bh:.0f}" rx="3" fill="{GREEN}"/>')
        s.append(f'<text x="{cx:.0f}" y="{base-bh-5:.0f}" font-family="{FONT}" font-size="9.5" fill="{DARK}" text-anchor="middle">{v:.0f}</text>')
    med_y = base - h * 81.8 / mx
    s.append(f'<line x1="{x0}" y1="{med_y:.0f}" x2="{x0+w}" y2="{med_y:.0f}" stroke="{BLUE}" stroke-width="2" stroke-dasharray="5,3"/>')
    s.append(f'<text x="{x0+w+6}" y="{med_y+4:.0f}" font-family="{FONT}" font-size="11" font-weight="700" fill="{BLUE}">med 81.8</text>')

    # --- TTFT curve (right bottom) ---
    s.append(f'<text x="530" y="222" font-family="{FONT}" font-size="14" font-weight="700" fill="{DARK}">Time to first token vs prompt size</text>')
    pts = [(89, 0.17), (5535, 2.8), (45143, 31.0)]
    tx0, ty0, tw, th = 580, 250, 380, 150
    tbase = ty0 + th
    # y axis: 0..35 s (linear), x axis: 0..50k tokens
    for i in range(5):
        gy = tbase - th * i / 4
        s.append(f'<line x1="{tx0}" y1="{gy:.0f}" x2="{tx0+tw}" y2="{gy:.0f}" stroke="{LIGHT}"/>')
        s.append(f'<text x="{tx0-8}" y="{gy+4:.0f}" font-family="{FONT}" font-size="10" fill="{MUTED}" text-anchor="end">{int(35*i/4)}s</text>')
    coords = []
    for tok, sec in pts:
        px = tx0 + tw * (tok / 50000)
        py = tbase - th * (sec / 35)
        coords.append((px, py))
    s.append('<path d="M ' + " L ".join(f"{x:.0f} {y:.0f}" for x, y in coords) + f'" stroke="{GOLD}" stroke-width="2.5" fill="none"/>')
    for (px, py), (tok, sec) in zip(coords, pts):
        s.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="5" fill="{GOLD}"/>')
        lbl = f"{sec:.2f}s" if sec < 1 else f"{sec:.1f}s"
        s.append(f'<text x="{px:.0f}" y="{py-11:.0f}" font-family="{FONT}" font-size="10.5" font-weight="700" fill="{DARK}" text-anchor="middle">{lbl}</text>')
        s.append(f'<text x="{px:.0f}" y="{tbase+16:.0f}" font-family="{FONT}" font-size="10" fill="{MUTED}" text-anchor="middle">{tok//1000}K tok</text>')

    # --- footnote ---
    s.append(f'<text x="26" y="{H-40}" font-family="{FONT}" font-size="11.5" fill="{MUTED}">Loaded-context (137,944 tokens) prefill: 186 s (742 tok/s) · generation at full load: 29.5 tok/s · prefill 4K: 1992 tok/s</text>')
    s.append(f'<text x="26" y="{H-20}" font-family="{FONT}" font-size="11.5" fill="{MUTED}">Vision latency 2.9 s (median of 3) · VRAM free at idle: 551 MB · model load: 6.6 s (warm cache)</text>')
    save("chart11-final-performance.svg", s)


chart_final()
print("done")
