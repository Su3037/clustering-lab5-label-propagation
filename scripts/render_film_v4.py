#!/usr/bin/env python3
"""圈子从哪里来 (film v4): everyday contacts -> the same problem in chips -> label propagation, layer by layer.

Builds on the drawing toolkit and engine-backed scenes in render_film_v3.py. Scenes reused from v3 are
time-remapped with piecewise-linear knots so their accents land on this film's music phrases.
Timing, chapters and bilingual captions live in video/storyboard-v4.json. Every label, vote, round count and
cutsize is read from data/film-v3.json, produced by scripts/build-film-v3.mjs running site/algorithm.js.

  python3 scripts/render_film_v4.py --stills
  python3 scripts/render_film_v4.py --start 0 --end 95
"""
import argparse, importlib.util, json, math, subprocess, time
from pathlib import Path
import cairo
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('v3', ROOT / 'scripts/render_film_v3.py')
v3 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(v3)
from_v3 = ('Frame backdrop substrate panel ruler cells24 graph5 wire_ends nbrs clamp ease ramp window lerp hexc '
           'W H FPS IVORY MUTED FAINT GOLD TEAL BLUE ROSE BG SANS SERIF P24 GC LP GEO TOTAL_W LABCOL LABCOL5 CELL_W CELL_H DATA').split()
globals().update({k: getattr(v3, k) for k in from_v3})
BOARD = json.loads((ROOT / 'video/storyboard-v4.json').read_text())
SOC = DATA['social']; SG = SOC['graph']; SRUN = SOC['run']
MONO = 'Noto Sans Mono CJK SC'

def remap(fn, knots):
    """Call a v3 scene with time warped through (new_t, old_t) knots, clamped at the ends."""
    def run(fr, t):
        if t <= knots[0][0]: return fn(fr, knots[0][1])
        for (a, x), (b, y) in zip(knots, knots[1:]):
            if t <= b: return fn(fr, x + (y - x) * (t - a) / (b - a))
        return fn(fr, knots[-1][1])
    return run

# ---------------------------------------------------------------- contacts graph helpers
WIN = sorted(SRUN['metrics']['clusters'], key=lambda l: min(SRUN['metrics']['clusters'][l]))
SCOL = {n: v3.HUES[i % len(v3.HUES)] for i, n in enumerate(SG['nodes'])}
for lab, c in zip(WIN, (TEAL, GOLD, BLUE)): SCOL[lab] = c
SEV = SRUN['events']

def contacts(fr, t, show=None, pos_mix=0.0, labels=None, edge_alpha=1.0, name_alpha=1.0, focus=None, dim=0.0):
    sc, ga = SOC['scatter'], SOC['gather']
    pos = {n: (lerp(sc[n][0], ga[n][0], pos_mix), lerp(sc[n][1], ga[n][1], pos_mix)) for n in SG['nodes']}
    # slow breathing so the picture is never frozen
    pos = {n: (x + 3 * math.sin(t * .7 + i), y + 3 * math.cos(t * .6 + i * 1.3)) for i, (n, (x, y)) in enumerate(pos.items())}
    show = show or (lambda n: 1.0)
    for u, v, w in SG['edges']:
        a = min(show(u), show(v)) * edge_alpha
        if a <= 0: continue
        same = labels and labels[u] == labels[v]
        col = SCOL[labels[u]] if same else '#6f9da0'
        fr.line(pos[u], pos[v], col, .6 + w * .45, (.12 + w * .08) * a * (1 - dim * (focus not in (u, v))), glow=.12 * a * w / 6)
    for n in SG['nodes']:
        a = show(n) * (1 - dim * .7 * (n != focus))
        if a <= 0: continue
        col = SCOL[labels[n]] if labels else '#a9c4c4'
        fr.dot(pos[n], 9, '#0b2029', a); fr.ring(pos[n], 9, col, 2, a, glow=.5 * a * (n == focus))
        fr.text(SOC['names'][n], pos[n][0], pos[n][1] - 16, 15, IVORY, a * name_alpha, anchor='c', screen=False)
    return pos

def social_labels_at(t, t0, t1):
    """Real run replayed between t0 and t1: event i commits at an evenly spaced time."""
    lab = {n: n for n in SG['nodes']}
    k = int(clamp((t - t0) / (t1 - t0)) * len(SEV))
    if k: lab = dict(SEV[k - 1]['labels'])
    return lab, k

# ---------------------------------------------------------------- frame furniture: five zones
_SH = None
def captions(fr, t):
    global _SH
    if _SH is None:
        _SH = cairo.LinearGradient(0, 860, 0, 1080)
        _SH.add_color_stop_rgba(0, *hexc(BG, 0)); _SH.add_color_stop_rgba(.35, *hexc(BG, .85)); _SH.add_color_stop_rgba(1, *hexc(BG, .92))
    fr.c.set_source(_SH); fr.c.rectangle(0, 860, W, 220); fr.c.fill()
    for a, b, zh, en in CAPS:
        al = window(t, a, b, .35)
        if al <= 0: continue
        fr.text(zh, W / 2, 978, 44 if len(zh) < 22 else 40, IVORY, al, anchor='c', bold=True, spacing=1)
        fr.c.select_font_face(SANS, cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL); fr.c.set_font_size(24)
        ext = fr.c.text_extents(en); fr.c.set_source_rgba(*hexc(MUTED, al)); fr.c.move_to(W / 2 - ext.x_advance / 2, 1024); fr.c.show_text(en)

def furniture(fr, t, s):
    fr.text('Su3037 · Clustering Lab 05', 64, 64, 16, MUTED, .75, spacing=1)
    if s['chapter']:
        prev = [x for x in SCENES if x['end'] <= s['start'] and x['chapter']]
        fresh = not prev or prev[-1]['chapter'] != s['chapter']
        a = ramp(t, s['start'], s['start'] + .8) if fresh else 1
        fr.text(s['chapter'], W / 2, 70, 22, GOLD, a * .95, anchor='c', spacing=4)

def note(fr, t, a, b, s, col=MUTED):
    """Annotation band: short, factual side notes just above the subtitles."""
    al = window(t, a, b, .4)
    if al > 0: fr.text(s, W / 2, 858, 19, col, al, anchor='c', spacing=1)

# ---------------------------------------------------------------- part one scenes
def sc_contacts(fr, t):
    fr.set_cam(960, 540, lerp(1.04, 1.0, ramp(t, 0, 17))); substrate(fr, .25)
    hits = [1.44, 3.57, 5.69, 7.83, 9.95]
    order = SG['nodes']
    def fly(n):  # names leave the list in five batches, one per hit
        b = hits[min(4, order.index(n) * 5 // len(order))]; return ramp(t, b, b + .6)
    lst = ramp(t, .2, 1.2) * (1 - ramp(t, 10.5, 12.0))
    panel(fr, 70, 150, 300, 640, lst, '通讯录')
    for i, n in enumerate(order[:14]):
        y = 240 + i * 38
        fr.text(SOC['names'][n], 100, y, 20, IVORY, lst * (1 - fly(n)), screen=True)
        fr.line((100, y + 12), (340, y + 12), FAINT, 1, lst * .6, screen=True)
    contacts(fr, t, show=fly, edge_alpha=ramp(t, 10.9, 16.5))
    note(fr, t, 11.0, 17.3, '线越粗越亮：联系越频繁（虚构的通讯录）')

def sc_title4(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .25)
    contacts(fr, t, edge_alpha=1 - .6 * ramp(t, 16.9, 17.6), name_alpha=.5, dim=.5)
    a = ramp(t, 16.9, 17.41) * (1 - ramp(t, 24.2, 24.85))
    fr.rect(0, 380, W, 300, fill=BG, alpha=.8 * a, r=0, screen=True)
    for i, ch in enumerate(BOARD['title']):
        ci = ramp(t, 16.9 + i * .1, 17.41 + i * .1)
        fr.text(ch, W / 2 + (i - (len(BOARD['title']) - 1) / 2) * 130, 545 - 24 * (1 - ci), 104, GOLD, ci * a, face=SERIF, anchor='c', glow=.3 * a)
    fr.line((W / 2 - 360 * a, 585), (W / 2 + 360 * a, 585), GOLD, 1.2, a * .8, screen=True)
    fr.text(BOARD['titleEn'] + '  ·  LABEL PROPAGATION', W / 2, 636, 22, IVORY, a * ramp(t, 17.8, 18.6), anchor='c', spacing=3)

def sc_community(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .25)
    contacts(fr, t)
    # a small schematic of the goal, clearly marked as a sketch
    k = ramp(t, 25.0, 26.0); x, y = 1650, 710
    panel(fr, x - 170, y - 150, 340, 260, k)
    fr.text('示意', x + 140, y - 112, 15, MUTED, k, anchor='r', screen=True)
    cl = [(x - 80, y), (x + 80, y)]
    for cx, cy in cl:
        pts = [(cx + 38 * math.cos(a), cy + 38 * math.sin(a)) for a in [i * math.tau / 5 for i in range(5)]]
        for i in range(5):
            for j in range(i + 1, 5): fr.line(pts[i], pts[j], TEAL, 1.6, .8 * k, screen=True)
        for p in pts: fr.dot(p, 5, TEAL, k, screen=True)
    fr.line((x - 42, y), (x + 42, y), GOLD, 1, .8 * k, screen=True, dash=[4, 4])
    fr.text('圈内：紧', x - 80, y + 78, 17, TEAL, k, anchor='c', screen=True)
    fr.text('圈间：少', x + 80, y + 78, 17, GOLD, k, anchor='c', screen=True)

def sc_history(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .25)
    lab, k = social_labels_at(t, 38.8, 48.6)
    gather = ramp(t, 49.06, 51.0)
    cur = SEV[k - 1]['node'] if 0 < k < len(SEV) else None
    contacts(fr, t, labels=lab, pos_mix=gather, focus=cur)
    c = ramp(t, 34.3, 35.2); slide = ramp(t, 38.3, 39.3)
    x, y = lerp(560, 80, slide), lerp(380, 100, slide); s = lerp(1.0, .62, slide)
    fr.rect(x, y, 800 * s, 200 * s, fill='#0b1d25', stroke=GOLD, width=1.2, alpha=.95 * c, r=6, screen=True)
    fr.text('Raghavan · Albert · Kumara', x + 30 * s, y + 52 * s, 26 * s, GOLD, c, screen=True)
    fr.text('Near linear time algorithm to detect community', x + 30 * s, y + 100 * s, 22 * s, IVORY, c, screen=True)
    fr.text('structures in large-scale networks', x + 30 * s, y + 132 * s, 22 * s, IVORY, c, screen=True)
    fr.text('Physical Review E 76, 036106 · 2007', x + 30 * s, y + 172 * s, 18 * s, MUTED, c, screen=True)
    rnd = SEV[k - 1]['round'] if k else 0
    fr.text(f'第 {rnd} 轮', 90, 270, 20, GOLD, ramp(t, 39, 39.5) * (1 - gather), screen=True)
    note(fr, t, 49.3, 51.1, '颜色由算法得出；位置按结果重新排列，只为看清')

DIE = 620
def die_cells():
    rnd = np.random.default_rng(7); out = []
    for r in range(34):
        y = -DIE / 2 + 30 + r * 17; x = -DIE / 2 + 30
        while x < DIE / 2 - 40:
            w = float(rnd.integers(6, 22)); out.append((x, y, w)); x += w + 3
    return out
DIE_CELLS = die_cells()
def sc_chip(fr, t):
    fade = ramp(t, 51.18, 53.0)
    if fade < 1:
        fr.set_cam(960, 540, lerp(1.0, .6, fade)); contacts(fr, t, labels=dict(SRUN['labels']), pos_mix=1.0, edge_alpha=1 - fade, name_alpha=1 - fade, show=lambda n: 1 - fade)
    z = lerp(.6, 1.0, ease(ramp(t, 55.0, 60.0))); cx, cy = 0, 60 / z
    fr.set_cam(cx, cy, z); a = ramp(t, 52.0, 53.6)
    fr.rect(-DIE / 2 - 40, -DIE / 2 - 40, DIE + 80, DIE + 80, fill='#0a1a21', stroke='#3c5a60', width=1.4, alpha=a, r=6)
    for i in range(16):  # pad ring
        for side in range(4):
            p = -DIE / 2 + 20 + i * (DIE - 40) / 15
            q = {0: (p, -DIE / 2 - 28), 1: (p, DIE / 2 + 22), 2: (-DIE / 2 - 28, p), 3: (DIE / 2 + 22, p)}[side]
            fr.rect(q[0] - 5, q[1] - 3, 10, 6, fill=GOLD, alpha=.6 * a, r=1)
    for x, y, w in DIE_CELLS: fr.rect(x, y, w, 11, fill='#16323a', stroke='#2f5960', width=.6, alpha=a, r=1)
    for i in range(40):  # a few routed nets, drawn as L-shapes
        x0, y0, w0 = DIE_CELLS[(i * 97) % len(DIE_CELLS)]; x1, y1, w1 = DIE_CELLS[(i * 211 + 50) % len(DIE_CELLS)]
        k = ramp(t, 54.0 + i * .05, 55.0 + i * .05)
        fr.line((x0, y0 + 5), (x1, y0 + 5), TEAL, .8, .35 * a * k); fr.line((x1, y0 + 5), (x1, y1 + 5), TEAL, .8, .35 * a * k)
    part = ramp(t, 59.8, 61.0) * (1 - ramp(t, 66.5, 68.0))
    for xx in (-DIE / 6, DIE / 6): fr.line((xx, -DIE / 2 - 10), (xx, DIE / 2 + 10), GOLD, 1.6, .9 * part, glow=.5 * part, dash=[8, 6])
    fr.set_cam(960, 540, 1.0)
    note(fr, t, 53.0, 67.9, '示意图，不是真实芯片版图')

def sc_wires(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .3)
    a = ramp(t, 68.2, 69.2)
    blocks = [(300, 300, 520, 360, TEAL), (1100, 300, 520, 360, BLUE)]
    for x, y, w, h, c in blocks:
        fr.rect(x, y, w, h, fill='#0b1d25', stroke=c, width=1.4, alpha=a, r=8, screen=True)
    fr.text('块 1', 320, 290, 18, TEAL, a, screen=True); fr.text('块 2', 1120, 290, 18, BLUE, a, screen=True)
    cells = {'a': (420, 420), 'b': (620, 430), 'c': (520, 560), 'd': (1230, 450), 'e': (1440, 560)}
    for n, (x, y) in cells.items():
        fr.rect(x - 26, y - 14, 52, 28, fill='#0b2029', stroke=IVORY, width=1.4, alpha=a, r=3, screen=True)
    short = ramp(t, 68.4, 69.4); long_ = ramp(t, 72.6, 73.6)
    fr.line(cells['a'], cells['b'], TEAL, 2.4, .9 * short, screen=True)
    path = [cells['c'], (900, 560), (900, 700), (1440, 700), cells['e']]
    for p, q in zip(path, path[1:]): fr.line(p, q, GOLD, 2.4, .9 * long_, screen=True)
    # signals: the short hop repeats quickly; the long one crawls (a qualitative sketch, no timing claimed)
    if short > .5:
        k = ((t - 69.4) / .7) % 1; fr.dot((lerp(420, 620, k), lerp(420, 430, k)), 6, TEAL, 1, glow=1, screen=True)
    if long_ > .5 and t > 76.8:
        L = [math.dist(p, q) for p, q in zip(path, path[1:])]; tot = sum(L); d = ((t - 76.8) / 3.6) % 1 * tot
        for (p, q), l in zip(zip(path, path[1:]), L):
            if d <= l: fr.dot((lerp(p[0], q[0], d / l), lerp(p[1], q[1], d / l)), 6, GOLD, 1, glow=1, screen=True); break
            d -= l
    k = ramp(t, 76.8, 77.6)
    fr.text('短线：快', 520, 760, 22, TEAL, k, anchor='c', screen=True)
    fr.text('长线：慢、耗电、占布线资源', 1170, 760, 22, GOLD, k, anchor='c', screen=True)
    note(fr, t, 69.0, 85.0, '示意：信号速度只作定性比较')

ruler_combo = lambda fr, t: (v3.sc_ruler if t < 10.75 else v3.sc_silence)(fr, t)
sc_ruler4 = remap(ruler_combo, [(85.22, .4), (89.6, 4.9), (91.4, 5.69), (93.0, 7.83), (93.8, 10.2), (97.6, 13.4), (98.2, 15.4), (102.5, 17.3)])

def sc_count(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .25)
    from math import factorial as f
    n8 = f(24) // (f(8) ** 3 * 6); digits = math.floor(1e6 * math.log10(3) - math.log10(6)) + 1
    # 102.5-106.7: a brute-force search flickers through random three-way splits of the 24 cells
    b = ramp(t, 102.6, 103.4) * (1 - ramp(t, 106.2, 106.8))
    if b > 0:
        fr.set_cam(GC[0], GC[1] + 40, .7)
        rnd = np.random.default_rng(int(t * 8)); pick = {n: (TEAL, GOLD, BLUE)[int(rnd.integers(3))] for n in P24}
        cells24(fr, color=lambda n: pick[n], cell_alpha=lambda n: b, wire_alpha=lambda u, v, w: b * (.8 if pick[u] == pick[v] else .25))
        fr.set_cam(960, 540, 1.0)
        fr.text(f'第 {int(max(0, t - 102.6) * 8) + 1:,} 种分法', 960, 800, 22, GOLD, b, anchor='c', screen=True, face=MONO)
    k1 = ramp(t, 106.9, 109.6)
    panel(fr, 260, 250, 1400, 170, ramp(t, 106.7, 107.3))
    fr.text('24 个单元，平分成三组（每组 8 个）', 300, 300, 22, MUTED, ramp(t, 106.7, 107.3), screen=True)
    fr.text(f'{int(n8 * k1):,}', 300, 385, 64, GOLD, ramp(t, 106.7, 107.3), screen=True, bold=True)
    fr.text('= 24! / (8!³ · 3!)', 1620, 385, 26, MUTED, ramp(t, 108.8, 109.6), anchor='r', screen=True)
    k2 = ramp(t, 111.1, 111.8)
    panel(fr, 260, 470, 1400, 170, k2)
    fr.text('1,000,000 个单元，分成三组（大小不限）', 300, 520, 22, MUTED, k2, screen=True)
    fr.text(f'一个 {digits:,} 位的数', 300, 605, 56, ROSE, k2, screen=True, bold=True)
    fr.text('≈ 3^1,000,000 / 6', 1620, 605, 26, MUTED, k2, anchor='r', screen=True)
    k3 = ramp(t, 115.3, 116.0)
    fr.text(f'每秒试 10 亿种：24 个单元约 {n8 / 1e9:.1f} 秒；一百万个单元，需要约 10^{digits - 1 - 9:,} 秒', 960, 720, 22, IVORY, k3, anchor='c', screen=True)
    fr.text('宇宙的年龄约 4 × 10^17 秒', 960, 765, 20, MUTED, ramp(t, 116.8, 117.4), anchor='c', screen=True)

sc_rule4_base = remap(v3.sc_idea, [(119.27, 19.0), (124.0, 24.9), (128.0, 29.1), (136.16, 34.0)])
def sc_rule4(fr, t):
    sc_rule4_base(fr, t)
    fr.set_cam(960, 540, 1.0)
    a = ramp(t, 132.1, 133.0) * (1 - ramp(t, 135.6, 136.16))
    fr.rect(0, 430, W, 200, fill=BG, alpha=.75 * a, r=0, screen=True)
    fr.text('标签传播', W / 2, 540, 80, GOLD, a, face=SERIF, anchor='c', spacing=14, glow=.3 * a)
    fr.text('LABEL PROPAGATION', W / 2, 595, 22, IVORY, a, anchor='c', spacing=4)

QS = ['“最强”怎么算？', '谁先更新？', '什么时候停？', '它一定会停吗？', '平票怎么办？', '分得好不好？']
def sc_questions(fr, t):
    fr.set_cam(GC[0], GC[1], lerp(.8, .7, ramp(t, 136.16, 170.6))); substrate(fr, .3)
    cells24(fr, color=lambda n: '#3f5a60', wire_alpha=lambda u, v, w: .45, cell_alpha=lambda n: .5)
    fr.set_cam(960, 540, 1.0)
    k = ramp(t, 136.6, 137.6) * (1 - ramp(t, 168.5, 170.4))
    panel(fr, 560, 200, 800, 520, k, '一句话规则，留下的问题')
    times = [141.4, 143.6, 146.4, 148.6, 151.0, 152.6]
    for i, (q, tt) in enumerate(zip(QS, times)):
        a = k * ramp(t, tt, tt + .6)
        fr.text(f'{i + 1:02d}', 610, 300 + i * 66, 22, GOLD, a, screen=True, face=MONO)
        fr.text(q, 680, 300 + i * 66, 30, IVORY, a, screen=True)

LAYERS = ['标签', '怎样算最强', '一次更新', '一整轮', '何时停止', '同时还是轮流', '分得好不好', '回到芯片', '它做不到的事']
def sc_interlude(fr, t):
    fr.set_cam(960, 540, 1.0)
    a = ramp(t, 170.8, 172.4) * (1 - ramp(t, 188.6, 189.8))
    fr.text('下篇', W / 2, 250, 64, GOLD, a, face=SERIF, anchor='c', spacing=20, glow=.3 * a)
    fr.text('拆开这条规则  ·  PART TWO', W / 2, 305, 22, IVORY, a, anchor='c', spacing=3)
    for i, s in enumerate(LAYERS):
        b = a * ramp(t, 173.0 + i * .9, 173.6 + i * .9)
        x = W / 2 + (i % 3 - 1) * 340; y = 430 + (i // 3) * 100
        fr.text(f'第 {i + 1} 层', x, y, 18, GOLD, b, screen=True, anchor='c')
        fr.text(s, x, y + 38, 28, IVORY, b, screen=True, anchor='c')

# ---------------------------------------------------------------- part two scenes (v3 scenes, remapped)
sc_names4 = remap(v3.sc_names, [(189.82, 37.3), (191.0, 37.9), (200.6, 41.88), (207.23, 46.0)])
sc_weights4 = remap(v3.sc_weights, [(207.23, 46.13), (211.6, 46.9), (216.0, 49.06), (221.0, 51.0), (221.85, 51.17)])
sc_update4 = remap(v3.sc_round1, [(227.44, 58.82), (232.2, 59.1), (236.6, 61.2), (239.6, 63.15), (241.0, 64.2)])
sc_round14 = remap(v3.sc_round1, [(241.0, 51.0), (245.6, 55.1), (249.8, 59.0), (253.6, 66.0), (258.02, 68.19)])
sc_round24 = remap(v3.sc_round2, [(258.02, 68.2), (266.4, 72.6), (275.04, 76.5)])
sc_sync4 = remap(v3.sc_sync, [(275.04, 76.6), (279.6, 80.2), (287.8, 85.25), (288.0, 85.35), (292.32, 89.0)])
sc_cut4 = remap(v3.sc_cut, [(292.32, 89.0), (301.0, 93.1), (305.2, 97.3), (307.4, 98.6), (309.09, 100.2)])
sc_payoff4 = remap(v3.sc_payoff, [(309.09, 102.5), (325.98, 119.27)])
sc_limits4 = remap(v3.sc_limits, [(325.98, 119.27), (330.4, 123.4), (334.3, 127.2), (334.8, 127.75), (338.6, 130.8), (339.0, 131.3), (343.02, 136.4)])

def sc_formula(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .3)
    hits = [222.03, 222.3, 222.56, 223.36, 223.9]
    def put(txt, x, y, size, col, h, anchor='l', face=SERIF):
        a = ramp(t, h, h + .3); fr.text(txt, x, y, size, col, a, screen=True, face=face, glow=.25 * a, anchor=anchor); return a
    put('新标签(v)', 470, 500, 58, IVORY, hits[0])
    put('=', 790, 500, 58, MUTED, hits[1])
    put('argmax', 850, 500, 58, GOLD, hits[2]); put('L', 940, 548, 30, TEAL, hits[2], anchor='c')
    put('Σ', 1130, 506, 76, GOLD, hits[3], anchor='c'); put('u ∈ N(v), 标签(u) = L', 1130, 560, 22, TEAL, hits[3], anchor='c', face=SANS)
    put('w(u, v)', 1205, 500, 58, IVORY, hits[4])
    a = ramp(t, 224.17, 224.8)
    fr.text('对每个候选标签 L：把带着 L 的邻居 u 的边权相加，取和最大的 L', 960, 650, 22, IVORY, a, anchor='c', screen=True)
    fr.text('平票时，课堂规则取字典序最小的标签', 960, 700, 22, MUTED, ramp(t, 225.0, 225.6), anchor='c', screen=True)

def coarse_layout():
    cl = LP['metrics']['clusters']; cen = {}
    for lab, ms in cl.items():
        cen[lab] = (sum(P24[m][0] for m in ms) / len(ms), sum(P24[m][1] for m in ms) / len(ms))
    pair = {}
    for u, v, w in LP['metrics']['cutEdges']:
        k = tuple(sorted((LP['labels'][u], LP['labels'][v]))); pair[k] = pair.get(k, 0) + w
    return cen, pair
CEN, SUPER = coarse_layout()
def sc_eda(fr, t):
    k = ramp(t, 343.6, 347.0)
    fr.set_cam(GC[0], GC[1], 1.0); substrate(fr, .5)
    lab = LP['labels']
    # cells slide into their cluster's centre; internal wires vanish; crossing wires merge (sums from the real result)
    for u, v, w in v3.EDGES24:
        p = [lerp(P24[x][0], CEN[lab[x]][0], k) for x in (u, v)]; q = [lerp(P24[x][1], CEN[lab[x]][1], k) for x in (u, v)]
        same = lab[u] == lab[v]
        fr.line((p[0], q[0]), (p[1], q[1]), LABCOL[lab[u]] if same else ROSE, .8 + w * .4, (.5 if same else .9) * (1 - k if same else 1))
    for n in P24:
        x, y = lerp(P24[n][0], CEN[lab[n]][0], k), lerp(P24[n][1], CEN[lab[n]][1], k)
        fr.rect(x - 26, y - 14, 52, 28, fill='#0b2029', stroke=LABCOL[lab[n]], width=1.4, alpha=1 - k * .9, r=3)
    for labl, (x, y) in CEN.items():
        fr.dot((x, y), 44 * k, '#0b2029', k); fr.ring((x, y), 44, LABCOL[labl], 2.6, k, glow=.5 * k)
        fr.text(f'{len(LP["metrics"]["clusters"][labl])} 个单元', x, y + 7, 18, IVORY, k, anchor='c', screen=False)
    for (a, b), w in SUPER.items():
        m = ((CEN[a][0] + CEN[b][0]) / 2, (CEN[a][1] + CEN[b][1]) / 2)
        fr.text(f'权重 {w}', m[0] + 30, m[1], 18, ROSE, ramp(t, 347.0, 347.6), screen=False)
    fr.set_cam(960, 540, 1.0)
    steps = ['聚类', '粗化：小图', '划分', '布局与布线']
    for i, s in enumerate(steps):
        a = ramp(t, 347.4 + i * .5, 347.9 + i * .5); x = 560 + i * 260
        fr.rect(x - 100, 770, 200, 48, fill='#0d222a', stroke=TEAL if i < 2 else GOLD, width=1.2, alpha=a, r=6, screen=True)
        fr.text(s, x, 802, 20, IVORY, a, anchor='c', screen=True)
        if i: fr.line((x - 160, 794), (x - 102, 794), MUTED, 1.2, a, screen=True)

def sc_return(fr, t):
    a = ramp(t, 351.4, 352.6); substrate(fr, .25)
    z = .68; fr.set_cam(975 - (480 - 960) / z, 420 - (480 - 540) / z, z)
    contacts(fr, t, labels=dict(SRUN['labels']), pos_mix=1.0, show=lambda n: a, name_alpha=.0)
    z = .66; fr.set_cam(690 - (1440 - 960) / z, 507 - (500 - 540) / z, z)
    cells24(fr, color=lambda n: LABCOL[LP['labels'][n]], cell_alpha=lambda n: a, wire_alpha=lambda u, v, w: a * (1 if LP['labels'][u] == LP['labels'][v] else .3),
            wire_col=lambda u, v, w: LABCOL[LP['labels'][u]] if LP['labels'][u] == LP['labels'][v] else '#4a5d63')
    fr.set_cam(960, 540, 1.0)
    fr.text('通讯录', 480, 180, 22, MUTED, a, anchor='c', screen=True, spacing=2); fr.text('芯片', 1440, 180, 22, MUTED, a, anchor='c', screen=True, spacing=2)
    fr.text('=', 960, 500, 64, GOLD, ramp(t, 352.4, 353.2), anchor='c', screen=True, glow=.4)

def sc_credits4(fr, t):
    fr.set_cam(960, 540, 1.0)
    a = ramp(t, 360.6, 361.6) * (1 - ramp(t, 377.4, 379.4))
    fr.text(BOARD['title'], W / 2, 300, 68, GOLD, a, face=SERIF, anchor='c', spacing=12, glow=.2 * a)
    fr.text(BOARD['titleEn'] + '  ·  CLUSTERING LAB 05', W / 2, 352, 20, IVORY, a, anchor='c', spacing=3)
    k = ramp(t, 366.4, 367.4) * a
    lines = [('参考文献', 'U. N. Raghavan, R. Albert, S. Kumara. Phys. Rev. E 76, 036106 (2007)'),
             ('画面、代码与算法复现', 'Su3037 · Clustering Lab 05（MIT / CC BY）'),
             ('音乐', 'We Never (Remix)（若如初见） · Hi Noise / 秋成 · 原速播放两遍'),
             ('', '第三方录音，不在本项目许可范围内'),
             ('数据', '所有标签、票数、轮数与 cutsize 均由项目算法实际运行得出'),
             ('', '通讯录与 24 单元电路均为虚构教学图')]
    for i, (h, b) in enumerate(lines):
        y = 470 + i * 50
        if h: fr.text(h, W / 2 - 330, y, 19, MUTED, k, anchor='r', screen=True)
        fr.text(b, W / 2 - 300, y, 19, IVORY if h else MUTED, k, screen=True)

SCENE_FN = {'contacts': sc_contacts, 'title': sc_title4, 'community': sc_community, 'history': sc_history, 'chip': sc_chip,
            'wires': sc_wires, 'ruler': sc_ruler4, 'count': sc_count, 'rule': sc_rule4, 'questions': sc_questions,
            'interlude': sc_interlude, 'names': sc_names4, 'weights': sc_weights4, 'formula': sc_formula, 'update': sc_update4,
            'round1': sc_round14, 'round2': sc_round24, 'sync': sc_sync4, 'cut': sc_cut4, 'payoff': sc_payoff4,
            'limits': sc_limits4, 'eda': sc_eda, 'return': sc_return, 'credits': sc_credits4}
SCENES = BOARD['scenes']; TOTAL = BOARD['duration']
FILL = dict(geo=GEO['metrics']['cut'], lp=LP['metrics']['cut'], rounds=LP['rounds'], total=TOTAL_W)
CAPS = [[a, b, zh.format(**FILL), en.format(**FILL)] for a, b, zh, en in BOARD['captions']]

def scene_at(t):
    for s in SCENES:
        if s['start'] <= t < s['end']: return s
    return SCENES[-1]

def render(t):
    fr = Frame(); backdrop(fr); s = scene_at(t)
    SCENE_FN[s['id']](fr, t)
    fr.set_cam(960, 540, 1.0)
    furniture(fr, t, s); captions(fr, t)
    img = fr.finish()
    fade = ramp(t, 0, .6) * (1 - ramp(t, TOTAL - 1.6, TOTAL))
    # a short dip to black between the two parts
    fade *= 1 - .85 * window(t, 188.9, 190.6, .8)
    if fade < 1: img = (img.astype(np.float32) * fade).astype(np.uint8)
    return img

def stamp(t):
    return f'{int(t) // 3600:02}:{int(t) // 60 % 60:02}:{int(t) % 60:02}.{round((t % 1) * 1000):03}'

def write_materials(out):
    zh = ['WEBVTT', '']; en = ['WEBVTT', '']
    for a, b, c, e in CAPS:
        zh += [f'{stamp(a)} --> {stamp(b)}', c, '']; en += [f'{stamp(a)} --> {stamp(b)}', e, '']
    (out / 'film-v4.zh.vtt').write_text('\n'.join(zh), encoding='utf-8'); (out / 'film-v4.en.vtt').write_text('\n'.join(en), encoding='utf-8')
    ch = []
    for s in SCENES:
        if s['chapter'] and (not ch or ch[-1]['title'] != s['chapter']): ch.append({'start': s['start'], 'title': s['chapter'], 'id': s['id']})
    (out / 'chapters-v4.json').write_text(json.dumps(ch, ensure_ascii=False, indent=2), encoding='utf-8')
    md = [f'# {BOARD["title"]}（v4）分镜与双语字幕', '', f'成片 {TOTAL} 秒，1920×1080，30 fps，无配音。', '']
    for s in SCENES:
        md += [f'## {stamp(s["start"])} {s["chapter"] or s["id"]}', f'画面：{s["beat"]}', '']
        md += [f'- {stamp(a)} {c}  \n  *{e}*' for a, b, c, e in CAPS if s['start'] <= a < s['end']]
        md.append('')
    (ROOT / 'video/transcript-v4.md').write_text('\n'.join(md), encoding='utf-8')

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stills', action='store_true')
    ap.add_argument('--start', type=float, default=0.0); ap.add_argument('--end', type=float, default=None)
    ap.add_argument('--every', type=float, default=0, help='with --stills: one still every N seconds')
    ap.add_argument('--out', default=str(ROOT / 'build/private/film-v4'))
    args = ap.parse_args(); out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    write_materials(out)
    if args.stills:
        ts = np.arange(args.start + 1, args.end or TOTAL, args.every) if args.every else [(s['start'] + s['end']) / 2 for s in SCENES]
        for tt in ts: Image.fromarray(render(float(tt))).save(out / f'key-{float(tt):06.1f}.jpg', quality=90)
        return
    end = args.end if args.end is not None else TOTAL
    pic = out / f'picture-{args.start:g}-{end:g}.mp4'
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', f'{W}x{H}',
           '-framerate', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', str(pic)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time()
    for i in range(round(args.start * FPS), round(end * FPS)):
        p.stdin.write(render(i / FPS).tobytes())
        if i % 300 == 0: print(f'frame {i} {time.time() - t0:.0f}s', flush=True)
    p.stdin.close()
    if p.wait(): raise SystemExit('ffmpeg failed')
    print(pic)

if __name__ == '__main__':
    main()
