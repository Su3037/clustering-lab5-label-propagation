#!/usr/bin/env python3
"""Dark technical renderer for the Label Propagation film 邻居的颜色 (v3).

Cairo draws the vector frame, a blurred half-resolution layer adds glow, and
FFmpeg encodes. Every graph state, vote total and cut value is read from
data/film-v3.json, which scripts/build-film-v3.mjs produces by running
site/algorithm.js. Nothing shown as an algorithm result is invented here.

Timing and captions live in video/storyboard-v3.json; shot boundaries follow
measured onsets of the chosen track (video/music-cues-v2.json).

  python3 scripts/render_film_v3.py --stills          keyframes for every scene
  python3 scripts/render_film_v3.py                   full silent picture + VTT/transcript/chapters
  python3 scripts/render_film_v3.py --start 50 --end 70   render a range
  python3 scripts/render_film_v3.py --music FILE      also mux FILE (original speed, gain from storyboard)
"""
import argparse, json, math, subprocess, time
from pathlib import Path
import cairo
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'data/film-v3.json').read_text())
BOARD = json.loads((ROOT / 'video/storyboard-v3.json').read_text())
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
def nbrs(g_edges, node):
    return [(v if u == node else u, w) for u, v, w in g_edges if node in (u, v)]

GROUP = {lab: col for lab, col in zip(sorted(LP['metrics']['clusters'], key=lambda l: min(LP['metrics']['clusters'][l])), (TEAL, GOLD, BLUE))}

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
            ctx.set_source_rgba(*hexc(col, alpha * k)); ctx.new_sub_path(); ctx.arc(q[0], q[1], rr * z, 0, math.tau); ctx.fill()
    def ring(self, p, r, col, width, alpha=1, glow=0, screen=False, frac=1.0):
        z = 1 if screen else self.cam[2]; q = p if screen else self.w2s(p)
        for ctx, k in ((self.c, 1),) + (((self.g, glow),) if glow else ()):
            ctx.set_source_rgba(*hexc(col, alpha * k)); ctx.set_line_width(width * z)
            ctx.new_sub_path(); ctx.arc(q[0], q[1], r * z, -math.pi / 2, -math.pi / 2 + math.tau * frac); ctx.stroke()
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
        al = window(t, a, b, .3)
        if al > 0:
            fr.text(s, W / 2, 990, 40 if len(s) < 24 else 37, IVORY, al, anchor='c', spacing=1.5)

def chapter(fr, s, alpha=1):
    fr.text(s, 96, 92, 22, GOLD, alpha * .9, spacing=3)


# ---------------------------------------------------------------- shared views
CELL_W, CELL_H = 52, 28
HUES = ['#c99a6b', '#a3b26f', '#7fae9a', '#7f9fc4', '#a18bc0', '#c08aa6', '#c4a37a', '#8fb7b0']
def _label_colors():
    winners = sorted(LP['metrics']['clusters'], key=lambda l: min(LP['metrics']['clusters'][l]))
    cols = {}
    for i, n in enumerate(G24['nodes']):
        cols[n] = HUES[i % len(HUES)]
    for lab, c in zip(winners, (TEAL, GOLD, BLUE)): cols[lab] = c
    return cols, winners
LABCOL, WINNERS = _label_colors()
REGCOL = {'L': TEAL, 'M': GOLD, 'R': BLUE}
assert max(P24[n][0] for n in P24 if GEO_LAB[n] == 'L') < min(P24[n][0] for n in P24 if GEO_LAB[n] == 'M')
assert max(P24[n][0] for n in P24 if GEO_LAB[n] == 'M') < min(P24[n][0] for n in P24 if GEO_LAB[n] == 'R')

def clip(a, b, hw, hh):
    """Point where the segment a->b leaves the rectangle centred on a."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    k = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
    return (a[0] + dx * k, a[1] + dy * k)

def wire_ends(u, v, pos=None, hw=CELL_W / 2 + 3, hh=CELL_H / 2 + 3):
    pos = pos or P24; A, B = pos[u], pos[v]
    return clip(A, B, hw, hh), clip(B, A, hw, hh)

def cells24(fr, show=None, color=None, wire_col=None, wire_alpha=None, wire_grow=None, tag=None, tag_alpha=0,
            highlight=None, cell_alpha=None, glow_wire=None):
    """The 24-cell schematic. Every argument is a function of the node or edge so scenes stay declarative."""
    show = show or (lambda n: 1.0)
    for u, v, w in EDGES24:
        a = min(show(u), show(v))
        if a <= 0: continue
        p, q = wire_ends(u, v); g = wire_grow(u, v) if wire_grow else 1
        if g <= 0: continue
        q = (lerp(p[0], q[0], g), lerp(p[1], q[1], g))
        al = (wire_alpha(u, v, w) if wire_alpha else 1) * a
        col = wire_col(u, v, w) if wire_col else '#6f9da0'
        gl = glow_wire(u, v, w) if glow_wire else .18 * w / 6
        fr.line(p, q, col, .8 + w * .5, (.22 + w * .09) * al, glow=gl * al)
    for n, (x, y) in P24.items():
        a = show(n) * (cell_alpha(n) if cell_alpha else 1)
        if a <= 0: continue
        c = color(n) if color else '#9fbcbc'; hl = highlight == n
        fr.rect(x - CELL_W / 2, y - CELL_H / 2, CELL_W, CELL_H, fill='#0b2029', stroke=c, width=1.6 + hl * 1.2, alpha=a, r=3,
                glow=.5 * a if hl else 0)
        for side in (-1, 1):  # pins
            fr.line((x + side * CELL_W / 2, y - 6), (x + side * (CELL_W / 2 + 5), y - 6), c, 1.4, a * .8)
            fr.line((x + side * CELL_W / 2, y + 6), (x + side * (CELL_W / 2 + 5), y + 6), c, 1.4, a * .8)
        fr.text(n, x, y + 5.5, 14, IVORY, a * .92, anchor='c', screen=False, face='Noto Sans Mono CJK SC')
        if tag and tag_alpha > 0:
            lab = tag(n); tc = LABCOL.get(lab, IVORY)
            fr.rect(x - 24, y + 19, 48, 19, fill='#0b2029', stroke=tc, width=1, alpha=a * tag_alpha, r=3)
            fr.text(lab, x, y + 33, 12, tc, a * tag_alpha, anchor='c', screen=False, face='Noto Sans Mono CJK SC')

def hull(points):
    pts = sorted(set(points))
    if len(pts) < 3: return pts
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def group_hulls(fr, alpha, grow=1.0):
    """Each cell gets a soft halo in its group's colour; the groups read as regions without drawn borders."""
    if alpha <= 0: return
    for n, (x, y) in P24.items():
        col = LABCOL[LP['labels'][n]]
        fr.dot((x, y), 62 * grow, col, .05 * alpha, glow=.22 * alpha)

def _unused_hulls(fr, alpha, grow=1.0):
    for lab, members in LP['metrics']['clusters'].items():
        pts = []
        for n in members:
            x, y = P24[n]
            pts += [(x - 40, y - 30), (x + 40, y - 30), (x - 40, y + 44), (x + 40, y + 44)]
        h = hull(pts); col = LABCOL[lab]
        sc = [fr.w2s(p) for p in h]; cx = sum(p[0] for p in sc) / len(sc); cy = sum(p[1] for p in sc) / len(sc)
        sc = [(lerp(cx, p[0], grow), lerp(cy, p[1], grow)) for p in sc]
        for ctx, k in ((fr.c, 1), (fr.g, .6)):
            ctx.new_path()
            for i, p in enumerate(sc): (ctx.move_to if i == 0 else ctx.line_to)(*p)
            ctx.close_path(); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.set_source_rgba(*hexc(col, .05 * alpha * k)); ctx.fill_preserve()
            ctx.set_source_rgba(*hexc(col, .55 * alpha * k)); ctx.set_line_width(1.6); ctx.stroke()

def panel(fr, x, y, w, h, alpha, title=None):
    if alpha <= 0: return
    fr.rect(x, y, w, h, fill='#081a22', stroke=FAINT, width=1.2, alpha=.93 * alpha, r=8, screen=True)
    if title: fr.text(title, x + 30, y + 46, 21, MUTED, alpha, screen=True, spacing=2)

def ruler(fr, x, y0, alpha, glow=0):
    """A drafting ruler standing on the cut line."""
    if alpha <= 0: return
    fr.rect(x - 22, y0, 44, 700, fill='#1b2a2c', stroke=GOLD, width=1.4, alpha=alpha * .9, r=3, glow=glow)
    for i in range(0, 35):
        L = 14 if i % 5 == 0 else 7
        fr.line((x - 22, y0 + 10 + i * 20), (x - 22 + L, y0 + 10 + i * 20), GOLD, 1, alpha * .8)
        if i % 5 == 0: fr.text(str(i // 5), x + 9, y0 + 15 + i * 20, 11, GOLD, alpha * .8, screen=False)

# Teacher's graph: positions and the side each label badge sits on (away from the wires).
E5 = [['A', 'B', 5], ['A', 'C', 1], ['B', 'C', 4], ['C', 'D', 2], ['D', 'E', 5], ['C', 'E', 1]]
assert {(n['node'], n['weight']) for n in GOLD5['events'][2]['neighbors']} == {(v, w) for v, w in nbrs(E5, 'C')}
P5 = {'A': (330, 300), 'B': (650, 250), 'C': (540, 520), 'D': (850, 660), 'E': (370, 730)}
def badge_dir(n, pos, edges):
    vs = [pos[v] for v, _ in nbrs(edges, n)]
    if not vs: return (0, 1)
    mx = sum(p[0] for p in vs) / len(vs) - pos[n][0]; my = sum(p[1] for p in vs) / len(vs) - pos[n][1]
    L = math.hypot(mx, my) or 1; return (-mx / L, -my / L)

def graph5(fr, labels, alpha=1, pos=None, edges=None, active=None, cut=False, weight_override=None, label_mix=None,
           edge_alpha=None, names=True, r=36):
    pos = pos or P5; edges = edges or E5
    for u, v, w in edges:
        ww = weight_override(u, v, w) if weight_override else w
        crossing = labels[u] != labels[v]
        col = ROSE if (cut and crossing) else ('#7aa5a6' if active in (u, v) else '#3d5d64')
        ea = edge_alpha(u, v) if edge_alpha else 1
        p, q = pos[u], pos[v]
        fr.line(p, q, col, 1 + ww * .9, alpha * ea * (.95 if (cut and crossing) or active in (u, v) else .55),
                glow=.6 * alpha * ea if cut and crossing else 0)
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        fr.dot(m, 17, '#0a1c24', alpha * ea)
        fr.text(f'{ww:g}', m[0], m[1] + 6, 17, ROSE if (cut and crossing) else MUTED, alpha * ea, anchor='c', screen=False)
    for n, p in pos.items():
        lab = labels[n]; col = LABCOL5[lab]
        if label_mix and n in label_mix:
            old, k = label_mix[n]; col = LABCOL5[old] if k < .5 else col; lab = old if k < .5 else lab
        fr.dot(p, r, '#0b2029', alpha)
        fr.ring(p, r, col, 2.8, alpha, glow=.6 * alpha if n == active else 0)
        if names: fr.text(n, p[0], p[1] + 12, 33, IVORY, alpha, anchor='c', screen=False, face=SERIF)
        d = badge_dir(n, pos, edges); bx, by = p[0] + d[0] * (r + 34), p[1] + d[1] * (r + 26)
        fr.rect(bx - 40, by - 15, 80, 30, fill='#0b2029', stroke=col, width=1.2, alpha=alpha, r=4)
        fr.text(f'标签 {lab}', bx, by + 6, 16, col, alpha, anchor='c', screen=False)

LABCOL5 = {'A': '#d9b06c', 'B': TEAL, 'C': '#d58f62', 'D': BLUE, 'E': ROSE}

def vote_panel(fr, x, y, votes_order, filled, alpha, title, winner=None, hl=0, scale=46, slots=6):
    """Accumulator: one register per label; filled[label] is the running sum shown."""
    h = 110 + 96 * len(votes_order)
    panel(fr, x, y, 640, h, alpha, title)
    for i, lab in enumerate(votes_order):
        yy = y + 110 + i * 96; on = (lab == winner) * hl; col = LABCOL5.get(lab, LABCOL.get(lab, GOLD))
        fr.text(f'标签 {lab}', x + 30, yy + 9, 25, col, alpha, screen=True)
        fr.rect(x + 150, yy - 15, scale * slots, 30, fill='#11262f', alpha=alpha, r=4, screen=True)
        v = filled.get(lab, 0)
        if v: fr.rect(x + 150, yy - 15, min(scale * slots, scale * v), 30, fill=col, alpha=alpha * (.5 + .5 * on), r=4, screen=True, glow=.6 * on)
        fr.text(f'{v:g}', x + 150 + scale * slots + 34, yy + 12, 32, IVORY if on else MUTED, alpha, screen=True, bold=bool(on))

def tokens(fr, ev, t, t0, step, pos, node, dests, travel=.8):
    """Each neighbour sends its weight (in its label colour) to the node, then into the register.
    Returns the running sums that have landed by time t."""
    filled = {}
    order = sorted(ev['neighbors'], key=lambda d: d['node'])
    for i, nb in enumerate(order):
        a = t0 + i * step; k = (t - a) / travel
        if k >= 1: filled[nb['label']] = filled.get(nb['label'], 0) + nb['weight']; continue
        if k <= 0: continue
        src, mid, dst = pos[nb['node']], pos[node], dests[nb['label']]
        q = (lerp(src[0], mid[0], k * 2), lerp(src[1], mid[1], k * 2)) if k < .5 else \
            (lerp(mid[0], dst[0], (k - .5) * 2), lerp(mid[1], dst[1], (k - .5) * 2))
        fr.dot(q, 4 + nb['weight'] * .9, LABCOL5.get(nb['label'], LABCOL.get(nb['label'], GOLD)), 1, glow=1)
    return filled

# ---------------------------------------------------------------- scenes (t is absolute film time)
CUT_T = (5.69, 7.83)

def sc_ruler(fr, t):
    fr.set_cam(GC[0], GC[1], lerp(1.1, 1.0, ease(t / 10)))
    substrate(fr, ramp(t, 0, 1.5) * .9)
    land = {n: ramp(t, .6 + (int(n[1:]) % 8) * .09 + (int(n[1:]) // 8) * .7, 1.1 + (int(n[1:]) % 8) * .09 + (int(n[1:]) // 8) * .7) for n in P24}
    regions = ramp(t, 9.95, 10.6)
    cells24(fr, show=lambda n: land[n], wire_grow=lambda u, v: ramp(t, 3.57, 5.4),
            color=lambda n: REGCOL[GEO_LAB[n]] if regions > .5 else '#9fbcbc')
    for k, (x0, x1, col) in enumerate([(GC[0] - 640, CUTS_X[0], TEAL), (CUTS_X[0], CUTS_X[1], GOLD), (CUTS_X[1], GC[0] + 640, BLUE)]):
        fr.rect(x0, GC[1] - 360, x1 - x0, 690, fill=col, alpha=.045 * regions, r=0)
        fr.text(f'区域 {k + 1}', (x0 + x1) / 2, GC[1] - 330, 20, col, regions * .9, anchor='c', screen=False, spacing=4)
    # the ruler drops on two hits and leaves dashed cuts behind
    for i, (x, tt) in enumerate(zip(CUTS_X, CUT_T)):
        drawn = ramp(t, tt, tt + .35)
        if drawn > 0: fr.line((x, GC[1] - 360), (x, lerp(GC[1] - 360, GC[1] + 330, drawn)), IVORY, 1.6, .8, glow=.6, dash=[10, 9])
    rx = CUTS_X[0] if t < CUT_T[1] - .5 else lerp(CUTS_X[0], CUTS_X[1], ramp(t, CUT_T[1] - .5, CUT_T[1]))
    drop = ramp(t, 4.9, CUT_T[0]); lift = ramp(t, 9.6, 10.6)
    ruler(fr, rx, lerp(-900, GC[1] - 360, drop) - lift * 1200, ramp(t, 4.9, 5.2), glow=.3 * (abs(t - CUT_T[0]) < .2 or abs(t - CUT_T[1]) < .2))

def sc_silence(fr, t):
    fr.set_cam(lerp(GC[0], 960, ramp(t, 10.75, 11.6)), lerp(GC[1], 540, ramp(t, 10.75, 11.6)), 1.0)
    substrate(fr, .9)
    for x0, x1, col in [(GC[0] - 640, CUTS_X[0], TEAL), (CUTS_X[0], CUTS_X[1], GOLD), (CUTS_X[1], GC[0] + 640, BLUE)]:
        fr.rect(x0, GC[1] - 360, x1 - x0, 690, fill=col, alpha=.045, r=0)
    for x in CUTS_X: fr.line((x, GC[1] - 360), (x, GC[1] + 330), IVORY, 1.6, .55, dash=[10, 9])
    dim = ramp(t, 10.75, 11.4)
    cells24(fr, color=lambda n: REGCOL[GEO_LAB[n]], wire_alpha=lambda u, v, w: 1 - .7 * dim)
    px, py = 1440, 250; acc = 0; cnt = 0; n = len(CROSS)
    for i, (u, v, w) in enumerate(CROSS):
        t0 = 11.0 + 1.9 * i / n; k = ramp(t, t0, t0 + .3)  # lands before the caption's number is read
        if k <= 0: continue
        p, q = wire_ends(u, v)
        fr.line(p, q, GOLD, .8 + w * .45, .35 + .55 * k, glow=.35 * k)
        fly = ramp(t, t0 + .1, t0 + .7)
        if 0 < fly < 1:
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2); s = fr.w2s(m)
            fr.dot((lerp(s[0], px + 60, fly), lerp(s[1], py + 120, fly)), 3 + w * .6, GOLD, 1 - fly * .3, glow=.9, screen=True)
        if fly >= 1: acc += w; cnt += 1
    pa = ramp(t, 10.9, 11.5)
    panel(fr, px - 30, py - 70, 430, 330, pa, '尺子切开的连线')
    fr.text(str(acc), px, py + 92, 100, GOLD, pa, bold=True, screen=True, glow=.3 * pa)
    fr.text(f'权重之和 · {cnt} 条', px, py + 136, 20, MUTED, pa, screen=True)
    fr.rect(px, py + 172, 340, 10, fill='#14303a', alpha=pa, r=5, screen=True)
    fr.rect(px, py + 172, max(10, 340 * acc / TOTAL_W), 10, fill=GOLD, alpha=pa, r=5, screen=True)
    fr.text(f'全部连线权重 {TOTAL_W}', px, py + 216, 18, MUTED, pa * ramp(t, 13.4, 14), screen=True)
    fr.text(f'{round(100 * acc / TOTAL_W)}%', px + 340, py + 216, 18, GOLD, pa * ramp(t, 13.4, 14), anchor='r', screen=True)

FOCUS = 'N09'
def sc_idea(fr, t):
    f = P24[FOCUS]; push = ramp(t, 21.0, 26.0); back = ramp(t, 31.2, 33.6)
    z = lerp(lerp(1.0, 2.1, push), .8, back)
    fr.set_cam(lerp(lerp(960, f[0], push), GC[0], back), lerp(lerp(540, f[1], push), GC[1], back), z)
    substrate(fr, .9)
    gone = ramp(t, 17.41, 19.0)
    for i, x in enumerate(CUTS_X):  # the ruler's cuts break into pieces and fall away
        for j in range(18):
            y0 = GC[1] - 360 + j * 38; drift = gone * (40 + 30 * math.sin(j * 1.7 + i))
            fr.line((x + drift * .2 * (1 if j % 2 else -1), y0 + drift), (x + drift * .2 * (1 if j % 2 else -1), y0 + 19 + drift), IVORY, 1.6, .55 * (1 - gone))
    for x0, x1, col in [(GC[0] - 640, CUTS_X[0], TEAL), (CUTS_X[0], CUTS_X[1], GOLD), (CUTS_X[1], GC[0] + 640, BLUE)]:
        fr.rect(x0, GC[1] - 360, x1 - x0, 690, fill=col, alpha=.045 * (1 - gone), r=0)
    near = {v for v, _ in nbrs(EDGES24, FOCUS)}
    focus_on = ramp(t, 21.0, 22.0) * (1 - back)
    strongest = max(nbrs(EDGES24, FOCUS), key=lambda x: (x[1], [-ord(c) for c in x[0]]))
    best = ramp(t, 29.1, 29.8) * (1 - back)
    def wcol(u, v, w):
        if FOCUS in (u, v) and strongest[0] in (u, v) and best > 0: return GOLD
        return '#6f9da0'
    cells24(fr, color=lambda n: REGCOL[GEO_LAB[n]] if gone < .5 else ('#a9c4c4' if n in near or n == FOCUS else '#5d777c'),
            wire_alpha=lambda u, v, w: 1 - .7 * focus_on * (FOCUS not in (u, v)),
            wire_col=wcol, glow_wire=lambda u, v, w: .8 * best if (FOCUS in (u, v) and strongest[0] in (u, v)) else .18 * w / 6,
            highlight=FOCUS if focus_on > .3 else None,
            tag=lambda n: n, tag_alpha=ramp(t, 24.9, 25.8) * (1 - back))
    # each neighbour's current label travels inward along its wire
    for i, (v, w) in enumerate(sorted(nbrs(EDGES24, FOCUS))):
        t0 = 25.2 + i * .27; ph = (t - t0) / 1.4
        if ph > 0 and t < 29.1:
            q = ph % 1; p = P24[v]; fr.dot((lerp(p[0], f[0], q), lerp(p[1], f[1], q)), 2.6, LABCOL[v], .95, glow=.9)
    fr.ring(f, 36 + 3 * math.sin(t * 2.6), GOLD, 1.3, .7 * focus_on, glow=.6)
    if best > 0:
        fr.text(f'最强：{strongest[0]} · 权重 {strongest[1]}', f[0], f[1] + 66, 15, GOLD, best, anchor='c', screen=False)

def sc_title(fr, t):
    fr.set_cam(GC[0], GC[1], lerp(.8, .74, ramp(t, 32.03, 37.6)))
    substrate(fr, .5)
    k = ramp(t, 32.03, 33.0)
    cells24(fr, color=lambda n: '#3f5a60', wire_alpha=lambda u, v, w: 1 - .6 * k, cell_alpha=lambda n: 1 - .5 * k)
    a = ramp(t, 33.5, 34.17) * (1 - ramp(t, 37.0, 37.62))
    fr.rect(0, 390, W, 290, fill=BG, alpha=.75 * a, r=0, screen=True)
    # letters arrive one per sixteenth of the roll and lock on its last hit
    title = '邻居的颜色'
    for i, ch in enumerate(title):
        ti = 32.03 + i * .27; ci = ramp(t, ti, ti + .4)
        x = W / 2 + (i - 2) * 130
        fr.text(ch, x, 540 - 30 * (1 - ci), 104, IVORY, ci * (1 - ramp(t, 37.0, 37.62)), face=SERIF, anchor='c', glow=.25 * a)
    fr.line((W / 2 - 330 * a, 580), (W / 2 + 330 * a, 580), GOLD, 1.2, a * .9, screen=True, glow=.4 * a)
    fr.text('LABEL PROPAGATION  ·  标签传播聚类', W / 2, 632, 24, GOLD, a, anchor='c', spacing=3)

def sc_names(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .35)
    app = ramp(t, 37.62, 38.6)
    labels = {n: n for n in P5}
    graph5(fr, labels, app * (1 - .55 * ramp(t, 41.9, 42.5)))
    fr.text('老师的五节点图', 330, 175, 24, MUTED, app, screen=True, spacing=4)
    # identity vs label: a two-field register for C
    k = ramp(t, 41.88, 42.6); x, y = 1150, 330
    if k > 0:
        fr.line(fr.w2s(P5['C']), (x, y + 120), GOLD, 1, .5 * k, screen=True, dash=[4, 6])
        panel(fr, x, y, 560, 300, k, '单元 C 的存储')
        fr.text('名字', x + 40, y + 125, 24, MUTED, k, screen=True)
        fr.rect(x + 140, y + 92, 360, 50, fill='#0f242c', stroke=IVORY, width=1, alpha=k, r=5, screen=True)
        fr.text('C', x + 170, y + 128, 30, IVORY, k, screen=True, face=SERIF)
        fr.text('只读 · 永远不变', x + 480, y + 124, 16, MUTED, k, anchor='r', screen=True)
        fr.text('标签', x + 40, y + 215, 24, MUTED, k, screen=True)
        blink = .6 + .4 * math.sin(t * 6)
        fr.rect(x + 140, y + 182, 360, 50, fill='#0f242c', stroke=LABCOL5['C'], width=1.6, alpha=k, r=5, screen=True, glow=.4 * k * blink)
        fr.text('C', x + 170, y + 218, 30, LABCOL5['C'], k, screen=True, face=SERIF)
        fr.text('可写 · 会被改写', x + 480, y + 214, 16, LABCOL5['C'], k, anchor='r', screen=True)

WV = DATA['weightVote']
PW = {'A': (760, 520), 'B': (420, 330), 'C': (420, 710), 'D': (1100, 520)}
def sc_weights(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .35)
    app = ramp(t, 46.13, 46.9)
    labels = WV['labels']; edges = WV['graph']['edges']
    for u, v, w in edges:
        fr.line(PW[u], PW[v], '#6f9da0', 1 + w * 1.4, .7 * app)
        m = ((PW[u][0] + PW[v][0]) / 2, (PW[u][1] + PW[v][1]) / 2)
        fr.dot(m, 18, '#0a1c24', app); fr.text(str(w), m[0], m[1] + 7, 19, IVORY, app, anchor='c', screen=False)
    for n, p in PW.items():
        lab = labels[n]; col = LABCOL5[lab]
        fr.dot(p, 36, '#0b2029', app); fr.ring(p, 36, col, 2.8, app, glow=.5 * app * (n == 'A'))
        fr.text(n, p[0], p[1] + 12, 32, IVORY, app, anchor='c', screen=False, face=SERIF)
        if n != 'A':
            fr.text(f'标签 {lab}', p[0], p[1] + 66, 17, col, app, anchor='c', screen=False)
    # the heads count first, then the weights land on the fill (49.06-51.18)
    heads = ramp(t, 46.6, 47.2) * (1 - ramp(t, 48.6, 49.0))
    fr.text('按人头：B 两票，D 一票', 760, 360, 22, MUTED, heads, anchor='c', screen=False)
    regs = sorted(WV['votes']); x, y = 1260, 260
    dests = {lab: (x + 150 + 10, y + 110 + i * 96) for i, lab in enumerate(regs)}
    ev = {'neighbors': [{'node': n, 'label': labels[n], 'weight': w} for n, w in nbrs(edges, 'A')]}
    filled = tokens(fr, ev, t, 49.06, .53, PW, 'A', dests)
    win = max(WV['votes'], key=lambda l: (WV['votes'][l], [-ord(c) for c in l]))
    hl = ramp(t, 50.9, 51.18)
    panel(fr, x, y, 560, 110 + 96 * len(regs), ramp(t, 48.6, 49.1), 'A 收到的权重')
    for i, lab in enumerate(regs):
        yy = y + 110 + i * 96; a = ramp(t, 48.6, 49.1); on = (lab == win) * hl
        fr.text(f'标签 {lab}', x + 30, yy + 9, 25, LABCOL5[lab], a, screen=True)
        fr.rect(x + 150, yy - 15, 280, 30, fill='#11262f', alpha=a, r=4, screen=True)
        v = filled.get(lab, 0)
        if v: fr.rect(x + 150, yy - 15, 70 * v, 30, fill=LABCOL5[lab], alpha=a * (.5 + .5 * on), r=4, screen=True, glow=.6 * on)
        fr.text(str(v), x + 470, yy + 12, 32, IVORY if on else MUTED, a, screen=True, bold=bool(on))

G_EVENTS = GOLD5['events']
# round 1 schedule: (event index, start of tokens, commit time, step between neighbours)
R1 = [(0, 52.0, 54.9, .5), (1, 55.2, 58.3, .5), (2, 59.1, 63.15, .53), (3, 66.08, 67.0, .2), (4, 67.13, 68.0, .2)]
def labels_at(events, t, sched, start):
    lab = dict(start)
    for idx, a, commit, _ in sched:
        if t >= commit: lab = dict(events[idx]['labels'])
    return lab

def order_strip(fr, x, y, order, current, done, alpha, title):
    fr.text(title, x, y - 28, 18, MUTED, alpha, screen=True, spacing=2)
    for i, n in enumerate(order):
        cx = x + i * 64; on = n == current
        fr.rect(cx, y, 50, 50, fill='#0f242c', stroke=GOLD if on else (TEAL if n in done else FAINT), width=1.6, alpha=alpha, r=6, screen=True, glow=.5 * on * alpha)
        fr.text(n, cx + 25, y + 35, 26, IVORY if on or n in done else MUTED, alpha, anchor='c', screen=True, face=SERIF)

def sc_round1(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .35)
    start = {n: n for n in P5}
    lab = labels_at(G_EVENTS, t, R1, start)
    cur = None; nxt = [x[1] for x in R1[1:]] + [68.2]
    for (idx, a, commit, step), until in zip(R1, nxt):
        if a - .3 <= t < until - .05: cur = (idx, a, commit, step, until)
    node = G_EVENTS[cur[0]]['node'] if cur else None
    mix = {}
    if cur and t >= cur[2]:
        ev = G_EVENTS[cur[0]]; mix[ev['node']] = (ev['old'], ramp(t, cur[2], cur[2] + .3))
    graph5(fr, lab, 1, active=node, label_mix=mix)
    done = [G_EVENTS[i]['node'] for i, a, c, s in R1 if t >= c]
    order_strip(fr, 1180, 170, list('ABCDE'), node, done, 1, '第 1 轮 · 访问顺序')
    changes = sum(1 for i, a, c, s in R1 if t >= c and G_EVENTS[i]['changed'])
    fr.text(f'本轮改变：{changes}', 1180 + 5 * 64 + 30, 205, 20, GOLD, 1, screen=True)
    if cur:
        ev = G_EVENTS[cur[0]]; regs = sorted(ev['votes']); x, y = 1180, 300
        dests = {l: (x + 160, y + 110 + i * 96) for i, l in enumerate(regs)}
        filled = tokens(fr, ev, t, cur[1], cur[3], P5, ev['node'], dests, travel=.8 if cur[3] > .3 else .5)
        hl = ramp(t, cur[2] - .5, cur[2])
        a = ramp(t, cur[1] - .3, cur[1]) * (1 - ramp(t, cur[4] - .3, cur[4] - .05))
        vote_panel(fr, x, y, regs, filled, a, f'{ev["node"]} 的邻居，按标签累加', ev['label'], hl, scale=36)
        if t >= cur[2]:
            msg = f'{ev["node"]}：{ev["old"]} → {ev["label"]}' if ev['changed'] else f'{ev["node"]} 保持 {ev["label"]}'
            fr.text(msg, x + 30, y + 110 + 96 * len(regs) + 40, 28, LABCOL5[ev['label']], a, screen=True)
        if ev['changed'] and t >= cur[2]:
            k = ramp(t, cur[2], cur[2] + .6); fr.ring(P5[ev['node']], 40 + 30 * k, LABCOL5[ev['label']], 2, 1 - k, glow=1)

def sc_round2(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .35)
    lab = dict(GOLD5['labels']); r2 = [e for e in G_EVENTS if e['round'] == 2]
    i = int(clamp((t - 68.6) / .85, 0, len(r2) - 1e-6)) if t < 72.9 else None
    node = r2[i]['node'] if i is not None else None
    graph5(fr, lab, 1, active=node)
    if node: fr.ring(P5[node], 46, GOLD, 1.2, .8, frac=((t - 68.6) / .85) % 1)
    done = [e['node'] for j, e in enumerate(r2) if i is None or j < i]
    order_strip(fr, 1180, 170, list('ABCDE'), node, done, 1, '第 2 轮 · 访问顺序')
    ch = sum(e['changed'] for e in r2)
    fr.text(f'本轮改变：{ch if i is None else sum(e["changed"] for e in r2[:i])}', 1180 + 5 * 64 + 30, 205, 20, GOLD, 1, screen=True)
    k = ramp(t, 72.5, 73.0)
    panel(fr, 1180, 330, 520, 250, k, '停止条件')
    fr.text('整轮零变化', 1210, 450, 44, TEAL, k, screen=True, glow=.3 * k)
    fr.text(f'稳定 · 共 {GOLD5["rounds"]} 轮', 1210, 520, 26, IVORY, k, screen=True)
    assert ch == 0 and GOLD5['status'] == 'stable'

PS, PA = DATA['pairSync'], DATA['pairAsync']
PP = {'A': (650, 540), 'B': (1270, 540)}
def pair(fr, labels, alpha, active=None, ring=None):
    fr.line(PP['A'], PP['B'], '#6f9da0', 2, .7 * alpha)
    fr.dot(((PP['A'][0] + PP['B'][0]) / 2, 540), 17, '#0a1c24', alpha); fr.text('1', 960, 547, 18, MUTED, alpha, anchor='c', screen=False)
    for n, p in PP.items():
        col = LABCOL5[labels[n]]
        fr.dot(p, 70, '#0b2029', alpha); fr.ring(p, 70, col, 3.2, alpha, glow=.6 * alpha * (n == active))
        fr.text(n, p[0], p[1] + 22, 62, IVORY, alpha, anchor='c', screen=False, face=SERIF)
        fr.text(f'标签 {labels[n]}', p[0], p[1] + 120, 28, col, alpha, anchor='c', screen=False)

def sc_sync(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .35)
    if t < 85.3:
        # synchronous: both read the snapshot, both commit together; one round per beat during the fill
        beats = [80.6, 82.0, 83.36, 84.16, 84.95]
        n = sum(t >= b for b in beats)
        states = [{'A': 'A', 'B': 'B'}] + [dict(e['labels']) for e in PS['events'] if e['roundEnd']]
        lab = states[n % 2] if n else states[0]
        assert states[2] == states[0]  # the engine saw the start state again: a cycle of period 2
        a = ramp(t, 76.6, 77.4) * (1 - ramp(t, 85.0, 85.3))
        pair(fr, lab, a)
        sa = ramp(t, 80.2, 80.6) * a
        panel(fr, 760, 170, 400, 120, sa, None)
        fr.text('同时更新 · 读旧快照', 960, 215, 22, MUTED, sa, anchor='c', screen=True)
        fr.text(f'快照  A={lab["A"]}  B={lab["B"]}', 960, 262, 24, IVORY, sa, anchor='c', screen=True)
        for b in beats:
            k = ramp(t, b - .25, b)
            if 0 < k < 1:
                for s, d in (('A', 'B'), ('B', 'A')):
                    fr.dot((lerp(PP[s][0], PP[d][0], k), 540), 6, LABCOL5[lab[s]], 1, glow=1)
        fr.text(f'第 {min(n, PS["rounds"])} 轮' if n <= PS['rounds'] else '回到起点，再来一遍……', 960, 760, 26, GOLD, sa * (n > 0), anchor='c', screen=False)
        if PS['status'] == 'cycle':
            fr.text(f'状态重复：循环，周期 {PS["events"][-1].get("period", 2)}', 960, 810, 22, ROSE, ramp(t, 83.4, 83.8) * a, anchor='c', screen=False)
    else:
        # asynchronous: A then B; B already sees A's new label
        e1, e2 = PA['events'][0], PA['events'][1]
        k1 = ramp(t, 85.9, 86.4); k2 = ramp(t, 87.0, 87.5)
        lab = {'A': e1['label'] if k1 > .5 else 'A', 'B': 'B'}
        a = ramp(t, 85.3, 85.7) * (1 - ramp(t, 88.7, 89.0))
        pair(fr, lab, a, active='A' if t < 86.6 else 'B')
        if 0 < k1 < 1: fr.dot((lerp(PP['B'][0], PP['A'][0], k1), 540), 6, LABCOL5['B'], 1, glow=1)
        if 0 < k2 < 1: fr.dot((lerp(PP['A'][0], PP['B'][0], k2), 540), 6, LABCOL5[lab['A']], 1, glow=1)
        fr.text('轮流更新 · 读最新标签', 960, 230, 22, MUTED, a, anchor='c', screen=True)
        fr.text(f'{PA["labels"]["A"]}/{PA["labels"]["B"]} · 稳定', 960, 790, 30, TEAL, a * ramp(t, 87.6, 88.0), anchor='c', screen=False)

SCD = DATA['strongCD']
def sc_cut(fr, t):
    fr.set_cam(lerp(960, 960, 0), 540, 1.0); substrate(fr, .35)
    strong = ramp(t, 97.3, 98.0)
    final = GOLD5['labels'] if t < 98.6 else SCD['labels']
    mix = {}
    if t >= 98.6:
        for n in final:
            if GOLD5['labels'][n] != final[n]: mix[n] = (GOLD5['labels'][n], ramp(t, 98.6, 99.0))
    wo = lambda u, v, w: (round(lerp(2, 10, strong)) if (u, v) == ('C', 'D') else w)
    graph5(fr, final, 1, cut=t >= 89.2, weight_override=wo, label_mix=mix)
    run_w = (lambda u, v, w: w) if t < 98.6 else (lambda u, v, w: 10 if (u, v) == ('C', 'D') else w)  # weights of the run whose result is shown
    m = final; ce = [(u, v, run_w(u, v, w)) for u, v, w in E5 if m[u] != m[v]]
    k = ramp(t, 89.2, 89.8); x, y = 1180, 260
    cut_now = GOLD5['metrics']['cut'] if t < 98.6 else SCD['metrics']['cut']
    assert sum(w for _, _, w in ce) == cut_now
    panel(fr, x, y, 560, 120 + 70 * len(ce) + 120, k, '被切开的边')
    for i, (u, v, w) in enumerate(ce):
        a = ramp(t, 89.4 + i * .6, 90.0 + i * .6) if t < 98.6 else ramp(t, 98.8 + i * .4, 99.2 + i * .4)
        fr.text(f'{u}–{v}', x + 40, y + 120 + i * 70, 30, ROSE, a, screen=True)
        fr.text(f'{w}', x + 480, y + 120 + i * 70, 32, IVORY, a, anchor='r', screen=True)
    yy = y + 120 + 70 * len(ce) - 20
    s = ramp(t, 93.1, 93.6) if t < 98.6 else ramp(t, 99.8, 100.3)
    fr.line((x + 40, yy), (x + 500, yy), MUTED, 1, s, screen=True)
    fr.text('cutsize', x + 40, yy + 60, 28, MUTED, s, screen=True)
    fr.text(str(cut_now), x + 480, yy + 66, 52, GOLD, s, anchor='r', screen=True, bold=True, glow=.3 * s)
    fr.text(f'{len(ce)} 条边，权重和 {cut_now}', x + 40, yy + 110, 18, MUTED, s, screen=True)
    if t >= 98.6: fr.text('这个例子里，边界移到了 C 的另一侧', 540, 860 - 20, 18, MUTED, ramp(t, 99.5, 100), anchor='c', screen=False)

LP_EV = LP['events']
def payoff_schedule():
    """Event i of the real run happens at time s[i]; round 1 slow, rounds 2-4 fast, round 5 a scan."""
    s = []
    for e in LP_EV:
        r, i = e['round'], e['index']
        if r == 1: s.append(105.8 + 4.1 * i / 24)
        elif r < LP['rounds']: s.append(110.1 + 4.0 * ((r - 2) * 24 + i) / (24 * (LP['rounds'] - 2)))
        else: s.append(114.3 + 2.7 * i / 24)
    return s
PAY_T = payoff_schedule()

def sc_payoff(fr, t):
    fr.set_cam(lerp(960, GC[0] + 160, ramp(t, 102.5, 104)), GC[1], 1.0); substrate(fr, .9)
    done = [i for i, s in enumerate(PAY_T) if t >= s]
    lab = dict(LP_EV[done[-1]]['labels']) if done else {n: n for n in P24}
    cur = LP_EV[done[-1]] if done and t < PAY_T[-1] + .2 else None
    final = ramp(t, 117.14, 118.0)
    same = lambda u, v: lab[u] == lab[v]
    cells24(fr, color=lambda n: LABCOL[lab[n]], tag=lambda n: lab[n], tag_alpha=ramp(t, 102.8, 103.6),
            wire_col=lambda u, v, w: LABCOL[lab[u]] if same(u, v) else '#4a5d63',
            wire_alpha=lambda u, v, w: (1.0 if same(u, v) else .45 - .2 * final),
            highlight=cur['node'] if cur else None)
    if cur and cur['changed'] and t - PAY_T[done[-1]] < .3:
        fr.ring(P24[cur['node']], 30 + 60 * (t - PAY_T[done[-1]]), LABCOL[cur['label']], 1.6, 1 - (t - PAY_T[done[-1]]) / .3, glow=.8)
    for u, v, w in LP['metrics']['cutEdges']:
        if final > 0:
            p, q = wire_ends(u, v); fr.line(p, q, ROSE, 1 + w * .5, .9 * final, glow=.8 * final)
    group_hulls(fr, final, lerp(.85, 1, final))
    cut = LP_EV[done[-1]]['metrics']['cut'] if done else DATA['initialCut']
    rnd = LP_EV[done[-1]]['round'] if done else 0
    px, py = 1440, 230; pa = ramp(t, 103.0, 103.8)
    panel(fr, px - 30, py - 70, 430, 420, pa, '被切开的权重')
    fr.text(str(cut), px, py + 92, 100, ROSE if final > .5 else IVORY, pa, bold=True, screen=True, glow=.3 * pa * final)
    fr.text(f'第 {rnd} 轮' + (' · 零变化，停止' if final > .3 else ''), px, py + 136, 20, MUTED, pa, screen=True)
    for i, (name, val, col) in enumerate([('标签传播', cut, ROSE), ('尺子', GEO['metrics']['cut'], GOLD)]):
        yy = py + 196 + i * 58; a = pa * (1 if i == 0 else final)
        fr.text(name, px, yy, 18, MUTED, a, screen=True)
        fr.rect(px + 90, yy - 15, 260 * val / TOTAL_W, 18, fill=col, alpha=a, r=3, screen=True)
        fr.text(str(val), px + 100 + 260 * val / TOTAL_W, yy, 18, col, a, screen=True)

def sc_limits(fr, t):
    fr.set_cam(960, 540, 1.0); substrate(fr, .35)
    # 119.27-123.3: the result recedes; 123.5: what it does not promise
    a1 = ramp(t, 119.27, 120.2) * (1 - ramp(t, 127.2, 127.7))
    if a1 > 0:
        k0 = ramp(t, 121.0, 123.4); fr.set_cam(lerp(GC[0] + 160, GC[0] + 560, k0), GC[1], lerp(1.0, .62, k0))
        cells24(fr, color=lambda n: LABCOL[LP['labels'][n]], cell_alpha=lambda n: a1, wire_alpha=lambda u, v, w: a1 * .7)
        fr.set_cam(960, 540, 1.0)
        k = ramp(t, 123.5, 124.2) * a1
        for i, (head, body, ok) in enumerate([
            (f'这里恰好 {LP["metrics"]["count"]} 组，各 {LP["metrics"]["sizes"][0]} 个', '没有参数能指定“分 3 组”', False),
            (f'老师的图：{GOLD5["metrics"]["count"]} 组，{" + ".join(map(str, GOLD5["metrics"]["sizes"]))} 个', '大小不保证均衡', False)]):
            x = 1150; y = 280 + i * 230
            panel(fr, x, y, 600, 180, k * ramp(t, 123.5 + i * .8, 124.2 + i * .8))
            kk = k * ramp(t, 123.5 + i * .8, 124.2 + i * .8)
            fr.text(head, x + 30, y + 70, 28, IVORY, kk, screen=True)
            fr.text(body, x + 30, y + 130, 22, ROSE, kk, screen=True)
    # 127.7-131.1: same graph, two visiting orders (both real runs)
    a2 = ramp(t, 127.7, 128.4) * (1 - ramp(t, 130.9, 131.3))
    if a2 > 0:
        rv = DATA['reverse']
        for j, (res, name) in enumerate([(GOLD5, 'A → E'), (rv, 'E → A')]):
            off = -420 if j == 0 else 420
            pos = {n: (960 + off + (p[0] - 590) * .62, 540 + (p[1] - 490) * .62) for n, p in P5.items()}
            graph5(fr, res['labels'], a2, pos=pos, r=28)
            fr.text(f'顺序 {name} · {res["rounds"]} 轮', 960 + off, 200, 26, GOLD, a2, anchor='c', screen=False)
        groups = lambda r: sorted(sorted(v) for v in r['metrics']['clusters'].values())
        same = groups(GOLD5) == groups(rv)
        fr.text('名字不同，这个例子里分组相同' if same else '分组不同', 960, 800, 22, TEAL, a2, anchor='c', screen=False)
    # 131.3-136.9: where it sits in chip design
    a3 = ramp(t, 131.24, 131.9) * (1 - ramp(t, 136.6, 137.0))
    if a3 > 0:
        stages = [('分组线索', '标签传播', TEAL), ('面积与均衡', '约束', GOLD), ('时序', '约束', GOLD), ('布局与布线', '拥塞', GOLD)]
        for i, (a, b, col) in enumerate(stages):
            x = 200 + i * 400; y = 440; k = a3 * ramp(t, 131.4 + i * .35, 131.9 + i * .35) if i < 1 else a3 * ramp(t, 134.16 + (i - 1) * .4, 134.6 + (i - 1) * .4)
            fr.rect(x, y, 300, 130, fill='#0d222a', stroke=col, width=1.6, alpha=k, r=8, screen=True, glow=.4 * k * (i == 0))
            fr.text(a, x + 150, y + 60, 28, IVORY, k, anchor='c', screen=True)
            fr.text(b, x + 150, y + 100, 18, col, k, anchor='c', screen=True)
            if i: fr.line((x - 100, y + 65), (x - 8, y + 65), MUTED, 1.4, k, screen=True)
        q = ((t - 134.16) / 2.4) % 1
        if t > 134.16: fr.dot((200 + 300 + q * 1100, 505), 5, TEAL, a3, glow=1, screen=True)

def sc_ending(fr, t):
    # 136.16-144.6: one more look at the rule, calm
    a1 = ramp(t, 136.6, 137.6) * (1 - ramp(t, 144.2, 144.8))
    if a1 > 0:
        fr.set_cam(P5['C'][0] + 120, P5['C'][1] - 40, lerp(1.25, 1.45, ramp(t, 136.6, 144.6))); substrate(fr, .3 * a1)
        ev = G_EVENTS[2]
        graph5(fr, ev['before'], a1, active='C')
        for i, nb in enumerate(sorted(ev['neighbors'], key=lambda d: d['node'])):
            ph = ((t - 137.0) / 2.6 + i * .25) % 1
            p = P5[nb['node']]; fr.dot((lerp(p[0], P5['C'][0], ph), lerp(p[1], P5['C'][1], ph)), 3 + nb['weight'] * .7,
                                       LABCOL5[nb['label']], a1 * math.sin(math.pi * ph), glow=1)
    # 144.8-170.5: the grown result; colours are read along wires; the ruler's ghost; the lone cell
    a2 = ramp(t, 144.6, 145.8)
    if a2 > 0:
        pan = ramp(t, 161.4, 163.6); back = ramp(t, 165.6, 169.5)
        fr.set_cam(lerp(lerp(GC[0], GC[0] + 40, ramp(t, 144.6, 161)), 1520, pan * (1 - back)) + back * 160,
                   GC[1], lerp(lerp(1.0, 1.06, ramp(t, 144.6, 161)), .78, back)); substrate(fr, .8 * a2)
        lab = LP['labels']; dim = 1 - .55 * ramp(t, 161.4, 163.0) * (1 - back * .5)
        cells24(fr, color=lambda n: LABCOL[lab[n]], cell_alpha=lambda n: a2 * dim,
                wire_col=lambda u, v, w: LABCOL[lab[u]] if lab[u] == lab[v] else '#4a5d63',
                wire_alpha=lambda u, v, w: a2 * dim * (1 if lab[u] == lab[v] else .4))
        # pulses travel both ways along strong intra-group wires
        for j, (u, v, w) in enumerate(EDGES24):
            if lab[u] != lab[v] or w < 4: continue
            ph = ((t - 145) / 3.2 + j * .137) % 1; s, d = (u, v) if j % 2 else (v, u)
            p, q = wire_ends(s, d)
            fr.dot((lerp(p[0], q[0], ph), lerp(p[1], q[1], ph)), 2.4, LABCOL[lab[s]], a2 * dim * math.sin(math.pi * ph) * ramp(t, 149.1, 150), glow=.9)
        g = ramp(t, 153.3, 154.0) * (1 - ramp(t, 156.4, 157.6))
        for x in CUTS_X: ruler(fr, x, GC[1] - 360, g * .55)
        for x in CUTS_X:
            for jj in range(18):
                y0 = GC[1] - 360 + jj * 38; dr = ramp(t, 156.4, 157.6) * (40 + 30 * math.sin(jj * 1.7))
                fr.line((x, y0 + dr), (x, y0 + 19 + dr), IVORY, 1.4, .5 * g if t < 156.4 else .5 * (1 - ramp(t, 156.4, 157.6)))
        group_hulls(fr, ramp(t, 157.6, 159.2) * dim * a2, lerp(.6, 1, ramp(t, 157.6, 159.6)))
        # the lone cell, kept apart: its own label forever (the engine's isolated node E)
        lone = ramp(t, 161.6, 162.6)
        if lone > 0:
            iso = DATA['island']; x, y = 1660, GC[1] - 10; col = LABCOL5[iso['labels']['E']]
            assert iso['labels']['E'] == 'E' and not nbrs(DATA['islandGraph']['edges'], 'E')
            fr.rect(x - CELL_W / 2, y - CELL_H / 2, CELL_W, CELL_H, fill='#0b2029', stroke=col, width=2, alpha=lone, r=3,
                    glow=.4 * lone * (.6 + .4 * math.sin(t * 2)))
            fr.text('E', x, y + 6, 15, IVORY, lone, anchor='c', screen=False, face='Noto Sans Mono CJK SC')
            fr.text('没有连接 · 标签始终是 E', x, y + 56, 20, col, lone * (1 - back), anchor='c', screen=False)

def sc_credits(fr, t):
    fr.set_cam(960, 540, 1.0)
    a = ramp(t, 170.6, 171.6) * (1 - ramp(t, 187.6, 189.6))
    fr.text('邻居的颜色', W / 2, 330, 72, IVORY, a, face=SERIF, anchor='c', spacing=12, glow=.2 * a)
    fr.text('LABEL PROPAGATION  ·  CLUSTERING LAB 05', W / 2, 390, 20, GOLD, a, anchor='c', spacing=3)
    k = ramp(t, 176.4, 177.4) * a
    lines = [('画面、代码与算法复现', 'Su3037 · Clustering Lab 05（MIT / CC BY）'),
             ('音乐', 'We Never (Remix)（若如初见） · Hi Noise / 秋成'),
             ('', '第三方录音，原速使用，不在本项目许可范围内'),
             ('数据', '图中所有标签、票数、轮数与 cutsize 均由项目算法实际运行得出'),
             ('', '24 单元电路为虚构教学图，不是真实网表')]
    for i, (h, b) in enumerate(lines):
        y = 520 + i * 52
        if h: fr.text(h, W / 2 - 40, y, 20, MUTED, k, anchor='r', screen=True)
        fr.text(b, W / 2, y, 20, IVORY if h else MUTED, k, screen=True)

SCENE_FN = {'ruler': sc_ruler, 'silence': sc_silence, 'idea': sc_idea, 'title': sc_title, 'names': sc_names, 'weights': sc_weights,
            'round1': sc_round1, 'round2': sc_round2, 'sync': sc_sync, 'cut': sc_cut, 'payoff': sc_payoff, 'limits': sc_limits,
            'ending': sc_ending, 'credits': sc_credits}
SCENES = BOARD['scenes']; TOTAL = BOARD['duration']
FILL = dict(geo=GEO['metrics']['cut'], lp=LP['metrics']['cut'], rounds=LP['rounds'], total=TOTAL_W)
CAPS = [[a, b, c.format(**FILL)] for a, b, c in BOARD['captions']]

def scene_at(t):
    for s in SCENES:
        if s['start'] <= t < s['end']: return s
    return SCENES[-1]

def render(t):
    fr = Frame(); backdrop(fr); s = scene_at(t)
    SCENE_FN[s['id']](fr, t)
    fr.set_cam(960, 540, 1.0)
    # chapter tag fades only when the chapter text changes
    prev = [x for x in SCENES if x['end'] <= s['start']]
    fresh = not prev or prev[-1]['chapter'] != s['chapter']
    ca = (ramp(t, s['start'], s['start'] + .6) if fresh else 1) * (1 - ramp(t, 186, 188))
    if s['id'] not in ('title', 'credits'): chapter(fr, s['chapter'], ca)
    caption(fr, t, CAPS)
    img = fr.finish()
    fade = ramp(t, 0, .6) * (1 - ramp(t, TOTAL - 1.6, TOTAL))
    if fade < 1: img = (img.astype(np.float32) * fade).astype(np.uint8)
    return img

def stamp(t):
    return f'{int(t) // 3600:02}:{int(t) // 60 % 60:02}:{int(t) % 60:02}.{round((t % 1) * 1000):03}'

def write_materials(out_media):
    vtt = ['WEBVTT', '']
    for a, b, c in CAPS: vtt += [f'{stamp(a)} --> {stamp(b)}', c, '']
    (out_media / 'neighbors-v3.zh.vtt').write_text('\n'.join(vtt), encoding='utf-8')
    chapters = []
    for s in SCENES:
        if not chapters or chapters[-1]['title'] != s['chapter']: chapters.append({'start': s['start'], 'title': s['chapter'], 'id': s['id']})
    (out_media / 'chapters-v3.json').write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding='utf-8')
    md = ['# 邻居的颜色（v3）分镜与字幕', '', f'成片 {TOTAL} 秒，1920×1080，30 fps，无配音。音乐：We Never (Remix)（若如初见）· Hi Noise / 秋成，原速。', '']
    for s in SCENES:
        md += [f'## {stamp(s["start"])} {s["chapter"]}', f'画面：{s["beat"]}', '']
        md += [f'- {stamp(a)} {c}' for a, b, c in CAPS if s['start'] <= a < s['end']]
        md.append('')
    (ROOT / 'video/transcript-v3.md').write_text('\n'.join(md), encoding='utf-8')

KEYS = [2.5, 6.0, 9.0, 13.5, 16.5, 19.0, 27.0, 30.5, 35.5, 40.0, 44.0, 47.5, 50.8, 53.5, 57.0, 61.5, 64.5, 67.6, 70.5, 74.5,
        81.0, 84.5, 87.8, 91.0, 95.0, 100.5, 104.0, 108.0, 112.0, 118.5, 122.0, 125.5, 129.5, 135.5, 139.0, 147.0, 152.0, 155.5,
        159.5, 163.5, 168.5, 174.0, 180.0]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--stills', action='store_true'); ap.add_argument('--music')
    ap.add_argument('--start', type=float, default=0.0); ap.add_argument('--end', type=float, default=None)
    ap.add_argument('--out', default=str(ROOT / 'build/private/film-v3'))
    args = ap.parse_args(); out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    write_materials(out)
    if args.stills:
        for tt in KEYS: Image.fromarray(render(tt)).save(out / f'key-{tt:06.1f}.jpg', quality=92)
        return
    end = args.end if args.end is not None else TOTAL
    pic = out / f'picture-{args.start:g}-{end:g}.mp4'
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', f'{W}x{H}',
           '-framerate', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', str(pic)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); t0 = time.time()
    f0, f1 = round(args.start * FPS), round(end * FPS)
    for i in range(f0, f1):
        p.stdin.write(render(i / FPS).tobytes())
        if i % 300 == 0: print(f'frame {i}/{f1} {time.time() - t0:.0f}s', flush=True)
    p.stdin.close()
    if p.wait(): raise SystemExit('ffmpeg failed')
    print(pic)
    if args.music:
        g = BOARD['music']['gain']; dur = (f1 - f0) / FPS
        af = f'atrim=start={args.start}:duration={dur},asetpts=PTS-STARTPTS,volume={g},afade=t=out:st={dur - 1.6}:d=1.6'
        final = out / 'neighbors-v3.mp4'
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(pic), '-i', args.music, '-filter_complex', f'[1:a]{af}[a]',
                        '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(final)], check=True)
        print(final)

if __name__ == '__main__':
    main()
