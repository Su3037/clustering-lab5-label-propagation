#!/usr/bin/env python3
"""Dark technical renderer for the Label Propagation film (review cut).

Cairo draws the vector frame, a blurred half-resolution layer adds glow, and
FFmpeg encodes. Every graph state, vote total and cut value is read from
data/film-v3.json, which scripts/build-film-v3.mjs produces by running
site/algorithm.js. Nothing shown as an algorithm result is invented here.

  python3 scripts/render_film_v3.py --stills      keyframes only
  python3 scripts/render_film_v3.py               review cut (silent picture)
  python3 scripts/render_film_v3.py --music FILE  review cut muxed with FILE
"""
import argparse, json, math, subprocess, time
from pathlib import Path
import cairo
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/film-v3.json').read_text())
G24, LP, GEO, GOLD5 = DATA['graph'], DATA['lp'], DATA['geometric'], DATA['golden']
W, H, FPS = 1920, 1080, 30

def hexc(c, a=1.0):
    return (int(c[1:3], 16) / 255, int(c[3:5], 16) / 255, int(c[5:7], 16) / 255, a)
BG, BG2 = '#061219', '#0b1f29'
IVORY, MUTED, FAINT = '#eeeadd', '#8fa3a3', '#2a4048'
GOLD, TEAL, BLUE, ROSE = '#ddbd78', '#76cbb5', '#86a9e0', '#d99a9a'
SANS, SERIF = 'Noto Sans CJK SC', 'Noto Serif CJK SC'

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def ramp(t, a, b): return ease((t - a) / (b - a)) if b > a else float(t >= a)
def window(t, a, b, fade=.45): return ramp(t, a, a + fade) * (1 - ramp(t, b - fade, b))
def lerp(a, b, t): return a + (b - a) * t

# ---------------------------------------------------------------- data views
POS = {n: tuple(p) for n, p in G24['positions'].items()}
_xs = [p[0] for p in POS.values()]; _ys = [p[1] for p in POS.values()]
def _fit(box):
    x0, y0, x1, y1 = box; sx = (x1 - x0) / (max(_xs) - min(_xs)); sy = (y1 - y0) / (max(_ys) - min(_ys)); s = min(sx, sy)
    ox = x0 + ((x1 - x0) - s * (max(_xs) - min(_xs))) / 2; oy = y0 + ((y1 - y0) - s * (max(_ys) - min(_ys))) / 2
    return {n: (ox + (x - min(_xs)) * s, oy + (y - min(_ys)) * s) for n, (x, y) in POS.items()}
P24 = _fit((140, 215, 1240, 800))
EDGES24 = G24['edges']
GEO_LAB = GEO['labels']
CROSS = sorted([e for e in EDGES24 if GEO_LAB[e[0]] != GEO_LAB[e[1]]], key=lambda e: (P24[e[0]][1] + P24[e[1]][1]))
assert sum(e[2] for e in CROSS) == GEO['metrics']['cut']
TOTAL_W = GEO['metrics']['totalWeight']
# Column boundaries of the positional split, in screen space.
def _bound(a, b):
    ra = max(P24[n][0] for n in P24 if GEO_LAB[n] == a); lb = min(P24[n][0] for n in P24 if GEO_LAB[n] == b)
    return (ra + lb) / 2
GC = ((min(p[0] for p in P24.values()) + max(p[0] for p in P24.values())) / 2,
      (min(p[1] for p in P24.values()) + max(p[1] for p in P24.values())) / 2 + 30)
CUTS_X = [_bound('L', 'M'), _bound('M', 'R')]
FOCUS = 'N09'  # a cell whose wires reach across a positional boundary
def nbrs(g_edges, node):
    return [(v if u == node else u, w) for u, v, w in g_edges if node in (u, v)]

GROUP = {lab: col for lab, col in zip(sorted(LP['metrics']['clusters'], key=lambda l: min(LP['metrics']['clusters'][l])), (TEAL, GOLD, BLUE))}
GOLD_EVENT = next(e for e in GOLD5['events'] if e['node'] == 'C' and e['round'] == 1)
P5 = {'A': (330, 300), 'B': (640, 250), 'C': (530, 540), 'D': (860, 650), 'E': (360, 760)}
LCOL = {'A': '#d9b06c', 'B': TEAL, 'C': '#d58f62', 'D': BLUE, 'E': ROSE}

# ---------------------------------------------------------------- frame
class Frame:
    def __init__(self):
        self.s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); self.c = cairo.Context(self.s)
        self.gs = cairo.ImageSurface(cairo.FORMAT_ARGB32, W // 2, H // 2); self.g = cairo.Context(self.gs)
        self.g.scale(.5, .5)
        self.cam = (0.0, 0.0, 1.0)  # translation x, y and zoom around screen center
    # camera
    def set_cam(self, cx, cy, z):
        self.cam = (cx, cy, z)
    def w2s(self, p):
        cx, cy, z = self.cam; return ((p[0] - cx) * z + W / 2, (p[1] - cy) * z + H / 2)
    # primitives (all coordinates in world space unless screen=True)
    def line(self, a, b, col, width, alpha=1, glow=0, screen=False, dash=None):
        z = 1 if screen else self.cam[2]; a, b = (a, b) if screen else (self.w2s(a), self.w2s(b))
        for ctx, k in ((self.c, 1),) + (((self.g, glow),) if glow else ()):
            ctx.set_source_rgba(*hexc(col, alpha * k)); ctx.set_line_width(width * z * (2.2 if ctx is self.g else 1))
            ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_dash(dash or [])
            ctx.move_to(*a); ctx.line_to(*b); ctx.stroke(); ctx.set_dash([])
    def dot(self, p, r, col, alpha=1, glow=0, screen=False):
        z = 1 if screen else self.cam[2]; q = p if screen else self.w2s(p)
        for ctx, k, rr in ((self.c, 1, r),) + (((self.g, glow, r * 2.2),) if glow else ()):
            ctx.set_source_rgba(*hexc(col, alpha * k)); ctx.arc(q[0], q[1], rr * z, 0, math.tau); ctx.fill()
    def ring(self, p, r, col, width, alpha=1, glow=0, screen=False, frac=1.0):
        z = 1 if screen else self.cam[2]; q = p if screen else self.w2s(p)
        for ctx, k in ((self.c, 1),) + (((self.g, glow),) if glow else ()):
            ctx.set_source_rgba(*hexc(col, alpha * k)); ctx.set_line_width(width * z)
            ctx.arc(q[0], q[1], r * z, -math.pi / 2, -math.pi / 2 + math.tau * frac); ctx.stroke()
    def rect(self, x, y, w, h, fill=None, stroke=None, width=1.5, alpha=1, r=4, screen=False, glow=0):
        z = 1 if screen else self.cam[2]; (x, y) = (x, y) if screen else self.w2s((x, y)); w, h, r = w * z, h * z, r * z
        for ctx, k in ((self.c, 1),) + (((self.g, glow),) if glow else ()):
            ctx.new_sub_path(); ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
            ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi); ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); ctx.close_path()
            if fill: ctx.set_source_rgba(*hexc(fill, alpha * k)); ctx.fill_preserve() if stroke else ctx.fill()
            if stroke: ctx.set_source_rgba(*hexc(stroke, alpha * k)); ctx.set_line_width(width * z); ctx.stroke()
    def text(self, s, x, y, size, col=IVORY, alpha=1, face=SANS, bold=False, anchor='l', screen=True, glow=0, spacing=0):
        if alpha <= 0.003: return
        z = 1 if screen else self.cam[2]; (x, y) = (x, y) if screen else self.w2s((x, y))
        for ctx, k in ((self.c, 1),) + (((self.g, glow),) if glow else ()):
            ctx.select_font_face(face, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
            ctx.set_font_size(size * z); ext = ctx.text_extents(s)
            width = ext.x_advance + spacing * z * max(0, len(s) - 1)
            ox = {'l': 0, 'c': -width / 2, 'r': -width}[anchor]
            ctx.set_source_rgba(*hexc(col, alpha * k))
            if spacing:
                cx = x + ox
                for ch in s:
                    ctx.move_to(cx, y); ctx.show_text(ch); cx += ctx.text_extents(ch).x_advance + spacing * z
            else:
                ctx.move_to(x + ox, y); ctx.show_text(s)
    def finish(self):
        glow = Image.frombuffer('RGBA', (W // 2, H // 2), bytes(self.gs.get_data()), 'raw', 'BGRA', 0, 1)
        glow = glow.filter(ImageFilter.GaussianBlur(7)).resize((W, H), Image.Resampling.BILINEAR)
        base = np.frombuffer(self.s.get_data(), np.uint8).reshape(H, W, 4)[:, :, 2::-1].astype(np.uint16)
        g = np.asarray(glow, np.uint16)[:, :, :3]
        return np.minimum(base + g, 255).astype(np.uint8)

_BACK = None
def backdrop(fr):
    global _BACK
    if _BACK is None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
        grad = cairo.RadialGradient(W * .42, H * .42, 80, W * .5, H * .5, W * .75)
        grad.add_color_stop_rgb(0, *hexc(BG2)[:3]); grad.add_color_stop_rgb(1, *hexc(BG)[:3]); c.set_source(grad); c.paint()
        _BACK = surf
    fr.c.set_source_surface(_BACK); fr.c.paint()

def substrate(fr, alpha):
    """Fine placement grid that moves with the camera: rows of standard-cell sites."""
    if alpha <= 0: return
    for i in range(-2, 40):
        y = 120 + i * 28
        fr.line((-400, y), (2300, y), '#173039', .8, alpha * (.55 if i % 5 else 1))
    for j in range(-10, 60):
        x = j * 56
        for i in range(-2, 40, 5):
            fr.dot((x, 120 + i * 28), 1.3, '#2b4a52', alpha)

_SHADE = None
def caption(fr, t, lines):
    global _SHADE
    if _SHADE is None:
        _SHADE = cairo.LinearGradient(0, 860, 0, 1080)
        _SHADE.add_color_stop_rgba(0, *hexc(BG, 0)); _SHADE.add_color_stop_rgba(.35, *hexc(BG, .82)); _SHADE.add_color_stop_rgba(1, *hexc(BG, .9))
    fr.c.set_source(_SHADE); fr.c.rectangle(0, 860, W, 220); fr.c.fill()
    for a, b, s in lines:
        al = window(t, a, b, .35)
        if al > 0:
            fr.text(s, W / 2, 985, 40, IVORY, al, anchor='c', spacing=1.5)
    fr.line((W / 2 - 520, 928), (W / 2 + 520, 928), FAINT, 1, .8, screen=True)

def chapter(fr, s, alpha=1):
    fr.text(s, 96, 92, 22, GOLD, alpha * .9, spacing=3)

# ---------------------------------------------------------------- 24-cell schematic
def draw_cells(fr, t, appear=1.0, labels=None, colors=None, tag_alpha=0.0, wire=1.0, wire_alpha=None,
               region=None, region_alpha=0, highlight=None, dim=0.0):
    ordered = sorted(P24, key=lambda n: math.hypot(P24[n][0] - 690, P24[n][1] - 500))
    shown = {n: ease(appear * 1.6 - i / len(ordered) * .6) for i, n in enumerate(ordered)}
    for u, v, w in EDGES24:
        a = min(shown[u], shown[v]) * wire
        if a <= 0: continue
        A, B = P24[u], P24[v]; mid = (lerp(A[0], B[0], a), lerp(A[1], B[1], a))
        al = (wire_alpha(u, v, w) if wire_alpha else 1)
        col = '#5e8d92' if not colors else (colors[u] if colors[u] == colors[v] else '#4a5d63')
        fr.line(A, mid, col, .7 + w * .48, (.18 + w * .085) * al, glow=.25 * al * (w / 6))
    for n, p in P24.items():
        a = shown[n]
        if a <= 0: continue
        c = colors[n] if colors else '#9fbcbc'
        hl = highlight == n
        fr.rect(p[0] - 17, p[1] - 12, 34, 24, fill='#0c222b', stroke=c, width=1.6 + hl, alpha=a * (1 - dim * .6),
                r=3, glow=.4 * a if hl else 0)
        fr.dot((p[0] - 9, p[1]), 2.4, c, a * (1 - dim * .5))
        fr.text(n, p[0] + 4, p[1] + 5, 12, IVORY, a * .85 * (1 - dim * .5), anchor='c', screen=False, face='Noto Sans Mono CJK SC')
        if tag_alpha > 0 and labels:
            fr.text(labels[n], p[0], p[1] + 34, 13, c, a * tag_alpha, anchor='c', screen=False)

# ---------------------------------------------------------------- shots
def shot_cells(fr, t):
    fr.set_cam(*GC, lerp(1.08, 1.0, ease(t / 8)))
    substrate(fr, ramp(t, 0, 2) * .9)
    draw_cells(fr, t, appear=ramp(t, .2, 3.2), wire=ramp(t, 2.6, 6.0))
    chapter(fr, '序 · 一张电路图', ramp(t, .5, 1.5))
    caption(fr, t, [(.8, 4.4, '这里有 24 个电路单元，和它们之间的连线。'), (4.6, 9.7, '线越亮，两个单元之间的连接越强。')])

def shot_split(fr, t):
    fr.set_cam(*GC, 1.0)
    substrate(fr, .9)
    sweep = ramp(t, 2.2, 3.6)
    tint = ramp(t, 3.4, 4.4)
    for k, (x0, x1, col) in enumerate([(80, CUTS_X[0], TEAL), (CUTS_X[0], CUTS_X[1], GOLD), (CUTS_X[1], 1320, BLUE)]):
        fr.rect(x0, 170, x1 - x0, 660, fill=col, alpha=.045 * tint, r=0)
        fr.text(f'区域 {k + 1} · 8 个单元', (x0 + x1) / 2, 160, 19, col, tint * .9, anchor='c', screen=False)
    for x in CUTS_X:
        fr.line((x, 170), (x, lerp(170, 830, sweep)), IVORY, 1.6, .75 * (sweep > 0), glow=.5, dash=[10, 9])
    cols = {n: {'L': TEAL, 'M': GOLD, 'R': BLUE}[GEO_LAB[n]] for n in P24} if tint > .5 else None
    draw_cells(fr, t, colors=cols)
    chapter(fr, '序 · 一张电路图')
    caption(fr, t, [(0, 2.6, '要把它们分成三组：按位置分，还是按连接分？'), (2.8, 5.8, '最省事的办法：按位置，整整齐齐切成三块。')])

def shot_cost(fr, t):
    k = ease(t / 1.2); fr.set_cam(lerp(GC[0], 960, k), lerp(GC[1], 540, k), 1.0)
    substrate(fr, .9)
    cols = {n: {'L': TEAL, 'M': GOLD, 'R': BLUE}[GEO_LAB[n]] for n in P24}
    for k, (x0, x1, col) in enumerate([(80, CUTS_X[0], TEAL), (CUTS_X[0], CUTS_X[1], GOLD), (CUTS_X[1], 1320, BLUE)]):
        fr.rect(x0, 170, x1 - x0, 660, fill=col, alpha=.045, r=0)
    for x in CUTS_X:
        fr.line((x, 170), (x, 830), IVORY, 1.6, .55, dash=[10, 9])
    dim = ramp(t, .2, 1.2)
    draw_cells(fr, t, colors=cols, wire_alpha=lambda u, v, w: 1 - .75 * dim)
    # crossing wires ignite one by one and pour their weight into the accumulator
    span = 4.6; n = len(CROSS); acc = 0; count = 0
    px, py = 1420, 300
    for i, (u, v, w) in enumerate(CROSS):
        t0 = .8 + span * i / n; k = ramp(t, t0, t0 + .35)
        if k <= 0: continue
        A, B = P24[u], P24[v]
        fr.line(A, B, GOLD, .8 + w * .45, .35 + .55 * k, glow=.3 * k)
        # weight token flying to the panel
        fly = ramp(t, t0 + .1, t0 + .75)
        if 0 < fly < 1:
            m = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2); q = (lerp(m[0], px + 40, fly), lerp(m[1], py + 150, fly))
            fr.dot(q, 3 + w * .6, GOLD, 1 - fly * .3, glow=.9)
        if fly >= 1: acc += w; count += 1
    pa = ramp(t, .4, 1.2)
    fr.rect(px - 30, py - 70, 420, 400, fill='#081a22', stroke=FAINT, width=1.2, alpha=.92 * pa, r=8, screen=True)
    fr.text('被切开的连接', px, py - 22, 22, MUTED, pa, screen=True, spacing=2)
    fr.text(str(acc), px, py + 80, 96, GOLD, pa, face=SANS, bold=True, screen=True, glow=.35 * pa)
    fr.text(f'权重之和 · {count} 条连线', px, py + 124, 20, MUTED, pa, screen=True)
    # bar: share of all wiring weight that the tidy split severs
    bw = 340; fr.rect(px, py + 168, bw, 12, fill='#14303a', alpha=pa, r=6, screen=True)
    fr.rect(px, py + 168, max(12, bw * acc / TOTAL_W), 12, fill=GOLD, alpha=pa, r=6, screen=True, glow=.3)
    fr.text(f'全部连线权重 {TOTAL_W}', px, py + 214, 18, MUTED, pa * ramp(t, 5.6, 6.4), screen=True)
    fr.text(f'切掉了 {round(100 * acc / TOTAL_W)}%', px + bw, py + 214, 18, GOLD, pa * ramp(t, 5.6, 6.4), anchor='r', screen=True)
    chapter(fr, '序 · 一张电路图')
    caption(fr, t, [(.3, 5.6, '可是，被这两刀切开的连线，一条条亮了起来。'),
                    (5.8, 8.8, '图纸很整齐，联系紧密的单元却被拆散了。')])

def shot_ask(fr, t):
    f = P24[FOCUS]; push = ease(t / 5.2)
    fr.set_cam(lerp(960, f[0], push), lerp(540, f[1], push), lerp(1.0, 2.15, push))
    substrate(fr, .9)
    lines_out = 1 - ramp(t, 0, 1.2)
    for x in CUTS_X:
        fr.line((x, 170), (x, 830), IVORY, 1.6, .55 * lines_out, dash=[10, 9])
    near = {v for v, _ in nbrs(EDGES24, FOCUS)}
    cols = {n: ('#9fbcbc' if n in near or n == FOCUS else '#3f5a60') for n in P24}
    draw_cells(fr, t, colors=cols, highlight=FOCUS,
               wire_alpha=lambda u, v, w: 1.0 if FOCUS in (u, v) else .25)
    # each neighbour's current label travels inward along its wire
    for i, (v, w) in enumerate(sorted(nbrs(EDGES24, FOCUS))):
        p = P24[v]; t0 = 2.4 + i * .18; k = ramp(t, t0, t0 + .5)
        fr.rect(p[0] - 19, p[1] + 17, 38, 18, fill='#0c222b', stroke=TEAL, width=1, alpha=k, r=3)
        fr.text(v, p[0], p[1] + 30, 11, TEAL, k, anchor='c', screen=False)
        trav = (t - t0 - .4) / 1.6
        if 0 < trav:
            q = trav % 1; pos = (lerp(p[0], f[0], q), lerp(p[1], f[1], q))
            fr.dot(pos, 2.4, TEAL, .9 * (1 - ramp(t, 6.2, 6.8)), glow=.9)
    fr.ring(f, 30 + 3 * math.sin(t * 2.4), GOLD, 1.3, .7 * ramp(t, 1.2, 2), glow=.6)
    chapter(fr, '序 · 换一个问题')
    caption(fr, t, [(.3, 3.4, '换个问题：先不画边界。'), (3.6, 7.0, '如果每个单元只看邻居此刻的标签，会怎样？')])

def shot_title(fr, t):
    k = 1 - ramp(t, 0, 1.4)
    f = P24[FOCUS]; fr.set_cam(lerp(f[0], GC[0], ease(t / 2)), lerp(f[1], GC[1], ease(t / 2)), lerp(2.15, .9, ease(t / 2.4)))
    substrate(fr, .9 * k + .25)
    draw_cells(fr, t, colors={n: '#3a555c' for n in P24}, dim=.6 + .4 * (1 - k), wire_alpha=lambda u, v, w: .5)
    a = ramp(t, 1.4, 2.3) * (1 - ramp(t, 5.0, 5.59))
    fr.rect(0, 380, W, 300, fill=BG, alpha=.72 * a, r=0, screen=True)
    fr.text('邻居的颜色', W / 2, 520, 104, IVORY, a, face=SERIF, anchor='c', glow=.25 * a, spacing=18)
    fr.line((W / 2 - 170, 566), (W / 2 + 170, 566), GOLD, 1.2, a * .8, screen=True)
    fr.text('LABEL PROPAGATION  ·  标签传播聚类', W / 2, 616, 24, GOLD, a, anchor='c', spacing=3)

def shot_vote(fr, t):
    e = GOLD_EVENT; before, votes = e['before'], e['votes']
    fr.set_cam(960, 540, 1.0)
    substrate(fr, .5 * ramp(t, 0, .8))
    app = ramp(t, 0, .9)
    edges5 = GOLD5['events'][0]['neighbors']  # unused; graph edges come from neighbours of each event
    E5 = [['A', 'B', 5], ['A', 'C', 1], ['B', 'C', 4], ['C', 'D', 2], ['D', 'E', 5], ['C', 'E', 1]]
    into_c = {n['node']: n for n in e['neighbors']}
    # check the drawn graph matches the engine's neighbours for C
    assert {(n, d['weight']) for n, d in into_c.items()} == {(v, w) for v, w in nbrs(E5, 'C')}
    commit = ramp(t, 4.26, 4.9)
    lab = dict(before);
    for u, v, w in E5:
        act = 'C' in (u, v)
        fr.line(P5[u], P5[v], '#6f9a9c' if act else '#35525a', 1 + w * .9, app * (.75 if act else .4))
        m = ((P5[u][0] + P5[v][0]) / 2, (P5[u][1] + P5[v][1]) / 2)
        fr.dot(m, 15, '#0b1d25', app); fr.text(str(w), m[0], m[1] + 6, 17, MUTED, app, anchor='c', screen=False)
    # accumulator: one register per label present among C's neighbours
    regs = sorted(votes); bx, by = 1180, 380
    fr.rect(bx - 40, by - 100, 700, 120 + 112 * len(regs), fill='#081a22', stroke=FAINT, width=1.2, alpha=.92 * app, r=8, screen=False)
    fr.text('C 的邻居，按当前标签累加边权', bx, by - 50, 22, MUTED, app, screen=False, spacing=1)
    filled = {r: 0 for r in regs}
    order = sorted(e['neighbors'], key=lambda d: 'ABCDE'.index(d['node']))
    for i, nb in enumerate(order):
        t0 = .53 + i * .5313; k = ramp(t, t0, t0 + .9)  # arrivals fall on the beat grid
        src = P5[nb['node']]; ri = regs.index(nb['label']); dst = (bx + 90 + filled[nb['label']] * 46, by + 30 + ri * 112)
        if 0 < k < 1:
            mid = (lerp(src[0], P5['C'][0], min(1, k * 2)), lerp(src[1], P5['C'][1], min(1, k * 2)))
            q = mid if k < .5 else (lerp(P5['C'][0], dst[0], (k - .5) * 2), lerp(P5['C'][1], dst[1], (k - .5) * 2))
            fr.dot(q, 4 + nb['weight'] * .8, LCOL[nb['label']], 1, glow=1)
        if k >= 1: filled[nb['label']] += nb['weight']
    win = max(votes, key=lambda r: (votes[r], [-ord(c) for c in r]))
    assert win == e['label']
    for ri, r in enumerate(regs):
        y = by + 30 + ri * 112; hl = ramp(t, 3.4, 3.9) * (r == win)
        fr.text(f'标签 {r}', bx, y + 9, 26, LCOL[r], app, screen=False)
        fr.rect(bx + 90, y - 14, 46 * 6, 30, fill='#11262f', alpha=app, r=4, screen=False)
        if filled[r]: fr.rect(bx + 90, y - 14, 46 * filled[r], 30, fill=LCOL[r], alpha=app * (.55 + .45 * hl), r=4, screen=False, glow=.6 * hl)
        fr.text(str(filled[r]), bx + 90 + 46 * 6 + 30, y + 11, 32, IVORY if hl else MUTED, app, screen=False, bold=bool(hl))
    # nodes: identity stays, label register commits
    for n, p in P5.items():
        l = lab[n]; col = LCOL[l]
        if n == 'C': col = LCOL['C'] if commit < .5 else LCOL[e['label']]
        fr.dot(p, 34, '#0c222b', app); fr.ring(p, 34, col, 2.6, app, glow=.5 * (n == 'C'))
        fr.text(n, p[0], p[1] + 12, 32, IVORY, app, anchor='c', screen=False, face=SERIF)
        shown = (e['label'] if commit > .5 else l) if n == 'C' else l
        fr.rect(p[0] - 42, p[1] + 46, 84, 28, fill='#0c222b', stroke=col, width=1.2, alpha=app, r=4, screen=False)
        fr.text(f'标签 {shown}', p[0], p[1] + 66, 16, col, app, anchor='c', screen=False)
    if commit > 0:
        fr.ring(P5['C'], 44 + 26 * commit, LCOL[e['label']], 2, (1 - commit) * .9, glow=1)
    fr.ring(P5['C'], 46, GOLD, 1.2, app * .6 * (1 - commit), frac=ramp(t, .4, 1.2))
    chapter(fr, '01 · 局部规则', app)
    caption(fr, t, [(.3, 3.9, 'C 把邻居按此刻的标签分组，把边权加在一起。'),
                    (4.1, 6.9, f'B 共 {votes["B"]}，最大。名字仍是 C，标签改写为 B。')])

def shot_result(fr, t):
    """Wide result keyframe: the real LP run on the 24-cell graph."""
    labels = LP['labels']; fr.set_cam(960, 540, 1.0); substrate(fr, .9)
    cols = {n: GROUP.get(labels[n], IVORY) for n in P24}
    draw_cells(fr, t, colors=cols, labels=labels, tag_alpha=1)
    for u, v, w in LP['metrics']['cutEdges']:
        fr.line(P24[u], P24[v], ROSE, 1 + w * .5, .9, glow=.8)
    px, py = 1420, 300
    fr.rect(px - 30, py - 70, 420, 330, fill='#081a22', stroke=FAINT, width=1.2, alpha=.92, r=8, screen=True)
    fr.text('标签传播的结果', px, py - 22, 22, MUTED, 1, screen=True, spacing=2)
    fr.text(str(LP['metrics']['cut']), px, py + 80, 96, ROSE, 1, bold=True, screen=True, glow=.3)
    fr.text(f'被切开的权重 · 原来是 {GEO["metrics"]["cut"]}', px, py + 124, 20, MUTED, 1, screen=True)
    fr.text(f'{LP["metrics"]["count"]} 组 · 每组 {"/".join(map(str, LP["metrics"]["sizes"]))} 个', px, py + 180, 20, IVORY, 1, screen=True)
    fr.text(f'第 {LP["rounds"]} 轮零变化，停止', px, py + 216, 20, TEAL, 1, screen=True)
    chapter(fr, '03 · 回到电路图')
    caption(fr, t, [(0, 99, '没有人画边界，三组单元自己浮现出来。')])

# Shot boundaries sit on measured strong onsets of the chosen track (video/music-cues-v2.json):
# 9.95, 15.9 (grid), 24.85, 32.03 (start of the drum roll), 37.62. The title lands as the roll ends (~34.2).
SHOTS = [('cells', 9.95, shot_cells), ('split', 5.95, shot_split), ('cost', 8.95, shot_cost),
         ('ask', 7.18, shot_ask), ('title', 5.59, shot_title), ('vote', 7.0, shot_vote)]
TOTAL = sum(d for _, d, _ in SHOTS)

def render(t, only=None):
    fr = Frame(); backdrop(fr)
    if only:
        fn = dict((n, f) for n, _, f in SHOTS + [('result', 6, shot_result)])[only]; fn(fr, t)
    else:
        a = 0
        for name, d, fn in SHOTS:
            if t < a + d or name == SHOTS[-1][0]:
                fn(fr, t - a)
                # short dip between shots that change concept
                edge = min(t - a, a + d - t)
                break
            a += d
    img = fr.finish()
    if not only:
        fade = ramp(t, 0, .8) * (1 - ramp(t, TOTAL - 1.0, TOTAL))
        if fade < 1: img = (img.astype(np.float32) * fade).astype(np.uint8)
    return img

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stills', action='store_true'); ap.add_argument('--music')
    ap.add_argument('--music-start', type=float, default=0.0); ap.add_argument('--gain', type=float, default=.45)
    ap.add_argument('--out', default=str(ROOT / 'build/private/review-v3'))
    args = ap.parse_args(); out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    keys = [('cells', 7.0), ('split', 5.0), ('cost', 7.4), ('ask', 6.0), ('title', 3.4), ('vote', 3.0), ('vote', 6.0), ('result', 3)]
    for i, (name, tt) in enumerate(keys):
        Image.fromarray(render(tt, name)).save(out / f'key-{i + 1:02}-{name}.jpg', quality=93)
    if args.stills: return
    pic = out / 'review-picture.mp4'
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', f'{W}x{H}',
           '-framerate', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', str(pic)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time(); n = round(TOTAL * FPS)
    for i in range(n):
        p.stdin.write(render(i / FPS).tobytes())
        if i % 150 == 0: print(f'frame {i}/{n} {time.time() - t0:.0f}s', flush=True)
    p.stdin.close()
    if p.wait(): raise SystemExit('ffmpeg failed')
    final = out / 'review-cut.mp4'
    if args.music:
        af = f'atrim=start={args.music_start}:duration={TOTAL},asetpts=PTS-STARTPTS,volume={args.gain},afade=t=in:d=.6,afade=t=out:st={TOTAL - 1.8}:d=1.8'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(pic), '-i', args.music, '-filter_complex', f'[1:a]{af}[a]',
                        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(final)], check=True)
    else:
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(pic), '-c', 'copy', '-movflags', '+faststart', str(final)], check=True)
    print(final, f'{TOTAL:.1f}s')

if __name__ == '__main__':
    main()
