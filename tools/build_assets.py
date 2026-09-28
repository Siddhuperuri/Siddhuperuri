"""Draw the profile's plates (light + dark) from one source.

System
------
Canvas    1280 wide, 72 margin; the hero's five columns set the grid for the rest
Type      the stroke alphabet of SIDDHARTHA (tools/strokes.py); no font files
Colour    ground, paper, ember - the artwork's palette. Paper is the only text
          colour. Ember marks the one curious thing on each plate, and only that.
Stages    every word is drawn at one of five stages of resolution, the artwork's
          five layers: sketched (trace), inferred (field), computed (lattice),
          arranged (design), measured (instrument). A project's name is drawn only
          as far as its evidence goes.

    python tools/build_assets.py            # all plates, trace from tools/trace.json
    python tools/build_assets.py --fetch    # refresh tools/trace.json first (needs a token)
"""
import datetime as dt
import html
import json
import math
import os
import random
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strokes as S  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets")
TRACE_JSON = os.path.join(HERE, "trace.json")
LOGIN = "Siddhuperuri"

W, M = 1280, 72
CW = W - 2 * M
R = W - M
COL = CW / 5.0

BASE = {
    "dark": dict(bg="#0A0908", fg="#E9E2D3", ember="#FF5C24"),
    "light": dict(bg="#EFEBE3", fg="#14110E", ember="#E0461A"),
}


def _mix(a, b, t):
    """a over b at weight t, as a solid hex colour (no alpha, so plates stay flat)."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(x * t + y * (1 - t)) for x, y in zip(pa, pb))


def theme(name):
    t = dict(BASE[name], name=name)
    for k in (72, 50, 34, 20, 12, 7):
        t["fg%d" % k] = _mix(t["fg"], t["bg"], k / 100.0)
    return t


THEMES = [theme("dark"), theme("light")]
num = S.num


# ----------------------------------------------------------------- document
class Doc:
    """One plate: a glyph pool for micro-type, CSS for motion, and the drawing."""

    def __init__(self, t, h, title, desc, w=W, ground=True):
        self.t, self.w, self.h, self.ground = t, w, h, ground
        self.title, self.desc = title, desc
        self.pool, self.defs, self.body, self.css = {}, [], [], []
        self.uid = 0

    def add(self, *parts):
        self.body.extend(p for p in parts if p)

    def nid(self, stem):
        self.uid += 1
        return "%s%d" % (stem, self.uid)

    def _glyph(self, ch):
        if ch not in self.pool:
            gid = "g%d" % len(self.pool)
            d = "".join(S.stroke_d(st, 0, 0, 100) for st in S.G[ch]["s"])
            self.pool[ch] = gid
            self.defs.append('<path id="%s" d="%s"/>' % (gid, d))
        return self.pool[ch]

    def text(self, s, x, y, cap, color, weight=None, track=0.32, anchor="start", cls=""):
        """Micro-type: a run of pooled glyphs with its baseline at y. Returns the width."""
        lay, w = S.text_layout(s, track)
        width = w * cap
        if anchor == "end":
            x -= width
        elif anchor == "middle":
            x -= width / 2
        k = cap / 100.0
        sw = weight if weight is not None else max(1.05, cap * 0.1)
        uses = "".join('<use href="#%s" x="%s"/>' % (self._glyph(ch), num(gx * 100))
                       for g, gx, ch in lay if g["s"])
        self.add('<g%s transform="translate(%s %s) scale(%s)" stroke="%s" stroke-width="%s">%s</g>'
                 % (' class="%s"' % cls if cls else "", num(x), num(y), "%.5g" % k, color,
                    "%.4g" % (sw / k), uses))
        return width

    def svg(self):
        css = "".join(dict.fromkeys(self.css))
        if css:
            css = ("<style>%s@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
                   "</style>" % css)
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
                'fill="none" stroke-linecap="round" stroke-linejoin="round" role="img" '
                'aria-labelledby="t d"><title id="t">%s</title><desc id="d">%s</desc>%s'
                '<defs>%s</defs>%s%s</svg>'
                % (self.w, self.h, self.w, self.h, esc(self.title), esc(self.desc), css,
                   "".join(self.defs),
                   '<rect width="%d" height="%d" fill="%s"/>' % (self.w, self.h, self.t["bg"])
                   if self.ground else "", "".join(self.body)))


def esc(s):
    return html.escape(s, quote=True)


# ---------------------------------------------------------------- primitives
def hline(x1, x2, y, c, w=1, extra=""):
    return '<path d="M%s %sH%s" stroke="%s" stroke-width="%s"%s/>' % (num(x1), num(y), num(x2), c,
                                                                     num(w), extra)


def vline(x, y1, y2, c, w=1, extra=""):
    return '<path d="M%s %sV%s" stroke="%s" stroke-width="%s"%s/>' % (num(x), num(y1), num(y2), c,
                                                                     num(w), extra)


def line(x1, y1, x2, y2, c, w=1, extra=""):
    return '<path d="M%s %sL%s %s" stroke="%s" stroke-width="%s"%s/>' % (
        num(x1), num(y1), num(x2), num(y2), c, num(w), extra)


def crops(t, w, h, size=14, off=24):
    """Crop marks at the four corners of the plate."""
    d = []
    for x, y, sx, sy in ((off, off, 1, 1), (w - off, off, -1, 1),
                         (off, h - off, 1, -1), (w - off, h - off, -1, -1)):
        d.append("M%s %sh%s M%s %sv%s" % (num(x - sx * 4), num(y), num(sx * size),
                                         num(x), num(y - sy * 4), num(sy * size)))
    return '<path d="%s" stroke="%s" stroke-width="1"/>' % ("".join(d), t["fg34"])


def reg(t, x, y, r=6, c=None):
    """A registration mark: circle and cross."""
    c = c or t["fg50"]
    return ('<circle cx="%s" cy="%s" r="%s" stroke="%s"/><path d="M%s %sh%s M%s %sv%s" stroke="%s"/>'
            % (num(x), num(y), num(r), c, num(x - r * 1.7), num(y), num(r * 3.4),
               num(x), num(y - r * 1.7), num(r * 3.4), c))


def dim_h(doc, x1, x2, y, label, ext_from=None, cap=9):
    """Horizontal dimension line with end ticks and a centred label above it."""
    t = doc.t
    parts = [hline(x1, x2, y, t["fg50"]),
             line(x1 - 4, y + 4, x1 + 4, y - 4, t["fg50"]), line(x2 - 4, y + 4, x2 + 4, y - 4, t["fg50"])]
    if ext_from is not None:
        parts += [vline(x1, ext_from, y - 6, t["fg20"]), vline(x2, ext_from, y - 6, t["fg20"])]
    doc.add(*parts)
    doc.text(label, (x1 + x2) / 2, y - 7, cap, t["fg72"], anchor="middle")


def dim_v(doc, x, y1, y2, label, cap=9, side=1):
    t = doc.t
    doc.add(vline(x, y1, y2, t["fg50"]),
            line(x - 4, y1 + 4, x + 4, y1 - 4, t["fg50"]), line(x - 4, y2 + 4, x + 4, y2 - 4, t["fg50"]))
    lw = S.text_width(label) * cap
    doc.text(label, x + side * 9 - (lw if side < 0 else 0), (y1 + y2) / 2 + cap / 2, cap, t["fg72"])


def motion(doc, css):
    doc.css.append(css)


EASE = "cubic-bezier(.2,.7,.1,1)"
DRAW = ("@keyframes dw{0%{stroke-dasharray:1;stroke-dashoffset:1}"
        "99%{stroke-dasharray:1;stroke-dashoffset:0}100%{stroke-dasharray:none}}"
        "@keyframes fi{from{opacity:0}}")


# -------------------------------------------------------------------- stages
# Each stage draws one letter with its baseline-left at (x, y) and cap height C.
def _to_screen(x, y, C):
    return lambda gx, gy: (x + gx * C, y - gy * C)


def stage_sketch(doc, ch, x, y, C, seed, weight=1.7, passes=3, cls=""):
    """TRACE - loose hand passes with overshoot. The piece's first, nearest layer."""
    t, g, rng = doc.t, S.G[ch], random.Random(seed)
    free = S.free_ends(g["s"])
    alphas = (t["fg"], t["fg50"], t["fg34"])
    for p in range(passes):
        d = []
        for si, st in enumerate(g["s"]):
            pts = S.stroke_points(st)
            rs = S.resample(pts, 6.0 / C)
            lam1, lam2 = rng.uniform(0.7, 1.1), rng.uniform(0.22, 0.34)
            ph1, ph2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
            a1 = (0.010 + 0.005 * p) * C
            sx, sy = rng.gauss(0, 0.006 * C), rng.gauss(0, 0.006 * C)
            s_acc, prev, out = 0.0, None, []
            for px, py, tx, ty in rs:
                if prev:
                    s_acc += math.hypot(px - prev[0], py - prev[1])
                prev = (px, py)
                n = (a1 * math.sin(2 * math.pi * s_acc / lam1 + ph1)
                     + 0.4 * a1 * math.sin(2 * math.pi * s_acc / lam2 + ph2))
                X, Y = x + px * C + sx, y - py * C + sy
                out.append((X - ty * n, Y - tx * n))   # normal (-ty, tx), y flipped
            # overshoot at free ends: the hand runs past where the stroke should stop
            if (si, 0) in free:
                e = rng.uniform(0.02, 0.06) * C
                tx, ty = rs[0][2], rs[0][3]
                out.insert(0, (out[0][0] - tx * e, out[0][1] + ty * e))
            if (si, 1) in free:
                e = rng.uniform(0.02, 0.06) * C
                tx, ty = rs[-1][2], rs[-1][3]
                out.append((out[-1][0] + tx * e, out[-1][1] - ty * e))
            d.append("M" + "L".join("%s %s" % (num(a), num(b)) for a, b in out))
        doc.add('<path%s d="%s" stroke="%s" stroke-width="%s" pathLength="1"/>'
                % (' class="%s p%d"' % (cls, p) if cls else "", "".join(d), alphas[p],
                   num(weight * (1 - 0.18 * p))))


def stage_field(doc, ch, x, y, C, seed, density=1.0, cls=""):
    """FIELD - a probability cloud that denoises onto the stroke."""
    t, g, rng = doc.t, S.G[ch], random.Random(seed)
    samples = []
    for st in g["s"]:
        samples += S.resample(S.stroke_points(st), 0.004)
    total = sum(S.length(S.stroke_points(st)) for st in g["s"]) * C
    pops = (("t", total / 0.95 * density, 0.020, t["fg"], 2.5),
            ("l", total / 4.2 * density, 0.065, t["fg50"], 2.0))
    for key, n, sigma, col, dia in pops:
        d = []
        for _ in range(int(n)):
            px, py, tx, ty = samples[rng.randrange(len(samples))]
            o, a = rng.gauss(0, sigma), rng.gauss(0, sigma * 0.5)
            gx, gy = px - ty * o + tx * a, py + tx * o + ty * a
            d.append("M%s %sh0" % (num(x + gx * C), num(y - gy * C)))
        doc.add('<path%s d="%s" stroke="%s" stroke-width="%s"/>'
                % (' class="%s f%s"' % (cls, key) if cls else "", "".join(d), col, num(dia)))
    # the undenoised remainder: uniform noise across the letter's box
    d, gw = [], g["w"]
    for _ in range(int(55 * density)):
        d.append("M%s %sh0" % (num(x + rng.uniform(-0.12, gw + 0.12) * C),
                               num(y - rng.uniform(-0.08, 1.08) * C)))
    doc.add('<path%s d="%s" stroke="%s" stroke-width="1.8"/>'
            % (' class="%s fn"' % cls if cls else "", "".join(d), t["fg34"]))


def stage_lattice(doc, ch, x, y, C, cell, half, origin, cls="", empties=True):
    """LATTICE - the letter quantised into computed cells on a shared grid."""
    t, g = doc.t, S.G[ch]
    polys = [S.stroke_points(st) for st in g["s"]]
    ox, oy = origin
    pad = half + cell
    i0, i1 = math.floor((x - pad - ox) / cell), math.ceil((x + g["w"] * C + pad - ox) / cell)
    j0, j1 = math.floor((y - C - pad - oy) / cell), math.ceil((y + pad - oy) / cell)
    full, empty, s = [], [], cell - 2.2
    for i in range(i0, i1):
        for j in range(j0, j1):
            cx, cy = ox + (i + 0.5) * cell, oy + (j + 0.5) * cell
            p = ((cx - x) / C, (y - cy) / C)
            dmin = min(S.dist_seg(p, q[k], q[k + 1]) for q in polys for k in range(len(q) - 1))
            if not (y - C < cy < y):
                continue
            if dmin * C <= half:
                full.append("M%s %sh%sv%sh-%sz" % (num(cx - s / 2), num(cy - s / 2), num(s), num(s), num(s)))
            elif empties and -0.02 <= p[0] <= g["w"] + 0.02 and -0.02 <= p[1] <= 1.02:
                empty.append("M%s %sh0" % (num(cx), num(cy)))
    if empty:
        doc.add('<path d="%s" stroke="%s" stroke-width="1.6"/>' % ("".join(empty), t["fg20"]))
    doc.add('<path%s d="%s" fill="%s"/>' % (' class="%s"' % cls if cls else "", "".join(full), t["fg"]))


def stage_design(doc, ch, x, y, C, weight=2.6, cls="", construction=True):
    """DESIGN - the exact geometry of the letter, with construction and survey ticks."""
    t, g = doc.t, S.G[ch]
    to = _to_screen(x, y, C)
    if construction:
        cons, nodes, seen = [], [], set()
        for st in g["s"]:
            for pc in st:
                if pc[0] == "A":
                    _, cx, cy, rx, ry, a0, a1 = pc
                    X, Y = to(cx, cy)
                    cons.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"/>'
                                % (num(X), num(Y), num(rx * C), num(ry * C)))
                    nodes.append("M%s %sh10M%s %sv10" % (num(X - 5), num(Y), num(X), num(Y - 5)))
                else:
                    for p in pc[1]:
                        key = (round(p[0], 3), round(p[1], 3))
                        if key in seen:
                            continue
                        seen.add(key)
                        X, Y = to(*p)
                        nodes.append("M%s %sh7v7h-7z" % (num(X - 3.5), num(Y - 3.5)))
        doc.add('<g%s stroke="%s">%s</g>' % (' class="%s c"' % cls if cls else "", t["fg20"], "".join(cons)),
                '<path%s d="%s" stroke="%s"/>' % (' class="%s c"' % cls if cls else "",
                                                 "".join(nodes), t["fg50"]))
    d = "".join(S.stroke_d(st, x, y, C) for st in g["s"])
    for a, b in S.ticks_for(g["s"]):
        (ax, ay), (bx, by) = to(*a), to(*b)
        d += "M%s %sL%s %s" % (num(ax), num(ay), num(bx), num(by))
    doc.add('<path%s d="%s" stroke="%s" stroke-width="%s" pathLength="1"/>'
            % (' class="%s"' % cls if cls else "", d, t["fg"], num(weight)))


def stage_measure(doc, ch, x, y, C, weight, cls=""):
    """INSTRUMENT - the resolved letter, exact to its cap line and baseline."""
    t, g = doc.t, S.G[ch]
    s = C - weight
    ox, oy = x + weight / 2, y - weight / 2
    free = S.free_ends(g["s"])
    d = []
    for si, st in enumerate(g["s"]):
        st = list(st)
        pts = S.stroke_points(st)
        # free ends that meet the cap line or baseline run past it and are cut flush
        for end in (0, 1):
            if (si, end) not in free:
                continue
            a, b = (pts[1], pts[0]) if end == 0 else (pts[-2], pts[-1])
            tx, ty = b[0] - a[0], b[1] - a[1]
            tl = math.hypot(tx, ty) or 1
            tx, ty = tx / tl, ty / tl
            if abs(ty) < 0.3:
                continue
            e = weight / s
            q = (b[0] + tx * e, b[1] + ty * e)
            if end == 0:
                st.insert(0, ("L", [q, b]))
            else:
                st.append(("L", [b, q]))
        d.append(S.stroke_d(st, ox, oy, s))
    cid = doc.nid("m")
    doc.defs.append('<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s"/></clipPath>'
                    % (cid, num(x - weight), num(y - C), num(g["w"] * s + 3 * weight), num(C)))
    doc.add('<g clip-path="url(#%s)"><path%s d="%s" stroke="%s" stroke-width="%s" '
            'stroke-linecap="butt" stroke-linejoin="miter"/></g>'
            % (cid, ' class="%s"' % cls if cls else "", "".join(d), t["fg"], num(weight)))


def measured_width(ch, C, weight):
    return S.G[ch]["w"] * (C - weight) + weight


# ---------------------------------------------------------------------- hero
STAGES = [("01", "SKETCHES", "TRACE"), ("02", "INFERS", "FIELD"), ("03", "COMPUTES", "LATTICE"),
          ("04", "ARRANGES", "DESIGN"), ("05", "MEASURES", "INSTRUMENT")]
ROWS = ["SIDDH", "ARTHA"]


def hero(t):
    C, H = 188, 792
    caps = (206, 486)                     # cap line of each row
    doc = Doc(t, H, "Siddhartha Peruri",
              "The name SIDDHARTHA set in two rows, SIDDH over ARTHA, split at the A that SIDDHA "
              "and ARTHA share. Each of the five columns draws its two letters a different way: "
              "sketched by hand, inferred as a cloud of points, computed as a lattice of cells, "
              "arranged as exact construction geometry, and measured as solid strokes with "
              "dimension lines. An ember sits in the counter of the shared A.")
    doc.add(crops(t, W, H))

    # frame: metadata, rules, the instrument lines every row sits on
    doc.text("PL. I", M, 62, 11, t["fg"], cls="rv")
    doc.text("SIDDHARTHA PERURI", M + 66, 62, 11, t["fg72"], cls="rv")
    doc.text("FIVE LAYERS · ONE VANTAGE", R, 62, 11, t["fg50"], anchor="end", cls="rv")
    doc.add(hline(M, R, 84, t["fg20"], extra=' class="ln" pathLength="1"'))
    for i in range(6):
        doc.add(vline(M + i * COL, 96, 700, t["fg12"], extra=' class="ln" pathLength="1"'))
    for i, (n, verb, layer) in enumerate(STAGES):
        cx = M + i * COL + 16
        doc.text(n, cx, 126, 10, t["fg50"], cls="rv")
        doc.text(verb, cx + 26, 126, 13, t["fg"], weight=1.45, cls="rv")
        doc.text(layer, cx + 26, 148, 9, t["fg50"], cls="rv")
    for cap in caps:
        for yy, lab in ((cap, "1"), (cap + C, "0")):
            doc.add(hline(M, R, yy, t["fg20"], extra=' class="ln" pathLength="1"'))
            doc.text(lab, M - 12, yy + 4, 8, t["fg50"], anchor="end", cls="rv")
        doc.add(hline(M, R, cap + C / 2, t["fg7"], extra=' stroke-dasharray="2 6"'))

    # the name, one stage per column
    for r, word in enumerate(ROWS):
        base = caps[r] + C
        for i, ch in enumerate(word):
            g = S.G[ch]
            col_cx = M + (i + 0.5) * COL
            seed = 11 + r * 5 + i
            if i == 4:
                wm = 25
                x = col_cx - measured_width(ch, C, wm) / 2
                stage_measure(doc, ch, x, base, C, wm, cls="s5")
                continue
            x = col_cx - g["w"] * C / 2
            if i == 0:
                stage_sketch(doc, ch, x, base, C, seed, cls="s1")
            elif i == 1:
                stage_field(doc, ch, x, base, C, seed, cls="s2")
            elif i == 2:
                stage_lattice(doc, ch, x, base, C, C / 16, 12.5, (M, caps[r]), cls="s3")
            elif i == 3:
                stage_design(doc, ch, x, base, C, cls="s4")

    # instrument: true measurements of the measured column (cap-height units)
    wm = 25
    hx = M + 4.5 * COL - measured_width("H", C, wm) / 2
    hw = measured_width("H", C, wm)
    dim_h(doc, hx, hx + hw, caps[0] - 20, "%.2f" % (hw / C), ext_from=caps[0] - 4)
    doc.add(line(hx, caps[0] + C + 16, hx + wm, caps[0] + C + 16, t["fg50"]),
            vline(hx, caps[0] + C + 6, caps[0] + C + 22, t["fg50"]),
            vline(hx + wm, caps[0] + C + 6, caps[0] + C + 22, t["fg50"]))
    doc.text("%.2f" % (wm / C), hx + wm + 8, caps[0] + C + 20, 9, t["fg72"])
    ax = M + 4.5 * COL + measured_width("A", C, wm) / 2
    dim_v(doc, ax + 16, caps[1], caps[1] + C, "1.00")
    doc.add(reg(t, R - 14, caps[0] - 34, 5), reg(t, R - 14, caps[1] + C + 34, 5))

    # the door: SIDDHA + ARTHA share one A, and the ember waits in its counter
    ga = S.G["A"]
    door_x = M + 0.5 * COL - ga["w"] * C / 2
    ex, ey = door_x + ga["anchor"][0] * C, caps[1] + C - 0.53 * C
    doc.add('<circle class="em" cx="%s" cy="%s" r="7" fill="%s"/>' % (num(ex), num(ey), t["ember"]),
            '<circle class="er" cx="%s" cy="%s" r="15" stroke="%s"/>' % (num(ex), num(ey), t["ember"]))
    doc.text("↑ SIDDHA + ARTHA SHARE THIS A", door_x, caps[1] + C + 34, 9, t["fg72"], cls="rv")

    doc.add(hline(M, R, 720, t["fg20"], extra=' class="ln" pathLength="1"'))
    doc.text("THE NAME IS WHAT THE PARTS ADD UP TO", M, 752, 11, t["fg72"], cls="rv")
    doc.text("INDIA · UTC +05:30", R, 752, 11, t["fg50"], anchor="end", cls="rv")

    # one-shot reveal, in the order a letter becomes: sketched, inferred, computed,
    # arranged, measured. The hero is above the fold, so it is seen while it plays.
    motion(doc, DRAW + EMBER + (
        "@keyframes up{from{opacity:0;transform:translateY(8px)}}"
        ".ln{animation:dw 1s %(e)s both}"
        ".rv{animation:fi .8s %(e)s .1s both}"
        ".s1{animation:dw 1.1s %(e)s both}.s1.p0{animation-delay:.25s}"
        ".s1.p1{animation-delay:.4s}.s1.p2{animation-delay:.55s}"
        ".s2{animation:fi 1s ease-out both}.s2.fn{animation-delay:.55s}"
        ".s2.fl{animation-delay:.75s}.s2.ft{animation-delay:.95s}"
        ".s3{animation:fi .5s steps(4) 1.3s both}"
        ".s4{animation:dw 1s %(e)s 1.55s both}.s4.c{animation:fi 1s ease 1.45s both}"
        ".s5{animation:up .7s %(e)s 2s both}"
        ".em{animation:fi .6s ease 2.6s both}"
        ".er{animation-delay:3.2s}" % {"e": EASE}))
    return doc.svg()


# ------------------------------------------------------------ plate helpers
# The ember breathes wherever it appears: the one thing on a plate that is alive.
EMBER = ("@keyframes br{0%,100%{opacity:.2}50%{opacity:.85}}"
         ".er{animation:br 4.8s ease-in-out infinite both}")


def frame(doc, pl, left, right, rule=84):
    t = doc.t
    doc.add(crops(t, doc.w, doc.h))
    pw = doc.text(pl, M, 62, 11, t["fg"])
    doc.text(left, M + pw + 22, 62, 11, t["fg72"])
    if right:
        doc.text(right, R, 62, 11, t["fg50"], anchor="end")
    doc.add(hline(M, R, rule, t["fg20"]))


def ember(doc, x, y, r=6, ring=14):
    t = doc.t
    doc.add('<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (num(x), num(y), num(r), t["ember"]),
            '<circle class="er" cx="%s" cy="%s" r="%s" stroke="%s"/>'
            % (num(x), num(y), num(ring), t["ember"]))
    motion(doc, EMBER)


def word(doc, text, x, y, C, stage, seed=1, track=0.3, **kw):
    """A word drawn at one stage of resolution. Returns its width."""
    lay, w = S.text_layout(text, track)
    for n, (g, gx, ch) in enumerate(lay):
        if not g["s"]:
            continue
        X = x + gx * C
        if stage == "sketch":
            stage_sketch(doc, ch, X, y, C, seed + n, weight=kw.get("weight", 1.6),
                         passes=kw.get("passes", 3))
        elif stage == "field":
            stage_field(doc, ch, X, y, C, seed + n, density=kw.get("density", 1.0))
        elif stage == "lattice":
            stage_lattice(doc, ch, X, y, C, C / 12, C * 0.075, (x, y - C), empties=False)
        elif stage == "design":
            stage_design(doc, ch, X, y, C, weight=kw.get("weight", 2.4))
        elif stage == "measure":
            stage_measure(doc, ch, X, y, C, kw.get("weight", C * 0.13))
    return w * C


def rtext(doc, s, x, y, cap, color, **kw):
    """Micro-type rotated to read upward, its baseline start at (x, y)."""
    doc.add('<g transform="rotate(-90 %s %s)">' % (num(x), num(y)))
    doc.text(s, x, y, cap, color, **kw)
    doc.add("</g>")


def arrow(doc, x1, y1, x2, y2, c, w=1.2, head=6, dash=""):
    a = math.atan2(y2 - y1, x2 - x1)
    hx1, hy1 = x2 - head * math.cos(a - 0.45), y2 - head * math.sin(a - 0.45)
    hx2, hy2 = x2 - head * math.cos(a + 0.45), y2 - head * math.sin(a + 0.45)
    doc.add('<path d="M%s %sL%s %s" stroke="%s" stroke-width="%s"%s/>'
            % (num(x1), num(y1), num(x2), num(y2), c, num(w),
               ' stroke-dasharray="%s"' % dash if dash else ""),
            '<path d="M%s %sL%s %sL%s %s" stroke="%s" stroke-width="%s"/>'
            % (num(hx1), num(hy1), num(x2), num(y2), num(hx2), num(hy2), c, num(w)))


# ------------------------------------------------------ PL. II  the artwork
def artwork(t):
    H = 470
    doc = Doc(t, H, "SIDDHARTHA, an interactive artwork",
              "Plate II. The title SIDDHARTHA, drawn measured. Beside it, a side view of the "
              "artwork's mechanism: five sheets of light at five depths, and rays from one "
              "viewpoint, V-star, that pass through the same point on every sheet. From a second, "
              "displaced viewpoint the same points no longer line up. The law of the piece: "
              "stillness resolves, motion scatters, attention pulls.")
    frame(doc, "PL. II", "SIDDHARTHA — AN INTERACTIVE ARTWORK ABOUT A PERSON",
          "SIDDHUPERURI/MIRACLE")
    word(doc, "SIDDHARTHA", M, 190, 44, "measure", weight=6)
    doc.text("MEASURED: PUBLIC, AND IT RUNS", M, 226, 9, t["fg50"])
    doc.text("HTML · CSS · JAVASCRIPT", M, 270, 11, t["fg72"])
    doc.text("NO FRAMEWORK · NO BUILD STEP · NO FONT FILES", M, 292, 11, t["fg50"])
    for i, law in enumerate(("STILLNESS RESOLVES.", "MOTION SCATTERS.", "ATTENTION PULLS.")):
        doc.text(law, M, 350 + i * 30, 15, t["fg"] if i == 0 else t["fg72"], weight=1.6)
    doc.text("THE ONE LAW OF ITS WORLD", M, 432, 9, t["fg50"])

    # the vantage: five sheets at five depths, seen edge-on from the side
    vx, vy = 660, 292
    depth = [(820, "TRACE"), (902, "FIELD"), (984, "LATTICE"), (1066, "DESIGN"), (1150, "INSTRUMENT")]
    k = 0.26
    us = (-0.9, -0.55, -0.2, 0.12, 0.44, 0.8)
    far = depth[-1][0]
    for u in us:
        doc.add(line(vx, vy, far, vy + u * k * (far - vx), t["fg34"], 0.9))
    for i, (sx, name) in enumerate(depth):
        h = k * (sx - vx)
        doc.add(vline(sx, vy - h - 8, vy + h + 8, t["fg50"] if i else t["fg72"], 1.2))
        ticks = "".join("M%s %sh-8" % (num(sx + 4), num(vy + u * h)) for u in us)
        doc.add('<path d="%s" stroke="%s" stroke-width="2.2"/>' % (ticks, t["fg"]))
        doc.text(name, sx, vy - h - 18, 8, t["fg50"], anchor="middle")
    # a displaced eye, just off V*: its ray through a mark on the nearest sheet misses
    # that mark on every sheet behind it, by more the deeper the sheet
    ox, oy = vx + 4, vy + 30
    u, s0 = us[4], depth[0][0]
    m0 = vy + u * k * (s0 - vx)
    sl = (m0 - oy) / (s0 - ox)
    doc.add(line(ox, oy, far + 14, m0 + sl * (far + 14 - s0), t["fg72"], 1,
                 ' stroke-dasharray="3 4"'))
    for sx, _ in depth[1:]:
        doc.add('<circle cx="%s" cy="%s" r="5.5" stroke="%s"/>'
                % (num(sx), num(vy + u * k * (sx - vx)), t["fg72"]))
    doc.add('<circle cx="%s" cy="%s" r="3.5" stroke="%s"/>' % (num(ox), num(oy), t["fg72"]))
    doc.text("MOVE: THEY SLIDE APART", ox + 6, oy + 30, 9, t["fg72"])
    ember(doc, vx, vy, 6, 14)
    doc.text("V*", vx - 24, vy + 5, 12, t["fg"], anchor="end")
    doc.text("STAND STILL HERE:", vx - 24, vy + 34, 9, t["fg72"], anchor="end")
    doc.text("THEY ADD UP TO A WORD", vx - 24, vy + 52, 9, t["fg72"], anchor="end")
    doc.text("NEAREST", depth[0][0], 112, 8, t["fg50"], anchor="middle")
    doc.text("FARTHEST", far, 112, 8, t["fg50"], anchor="middle")
    arrow(doc, depth[0][0] + 34, 108, far - 46, 108, t["fg34"], 1, 5)
    return doc.svg()


# ------------------------------------------------------------ PL. III  ORBIT
ORBIT_STAGES = ["PARSE", "NORMALIZE", "CHUNK", "EMBED", "INDEX", "RETRIEVAL", "CHAT"]
ORBIT_BUILT = 5


def orbit(t):
    H = 470
    doc = Doc(t, H, "ORBIT, a knowledge and document platform",
              "Plate III. The title ORBIT, drawn as exact construction geometry: public code, "
              "still in development. A pipeline of seven stages: parse, normalize, chunk, embed "
              "and index are built and drawn solid; retrieval and chat do not exist yet and are "
              "drawn dashed. An ember pulse runs through the built stages and stops at index. "
              "Below, the dependency direction enforced in CI: composition, api, application "
              "and infrastructure, domain, core.")
    frame(doc, "PL. III", "ORBIT — KNOWLEDGE AND DOCUMENT PLATFORM", "IN DEVELOPMENT · PUBLIC")
    word(doc, "ORBIT", M, 214, 96, "design", weight=2.6)
    doc.text("ARRANGED: PUBLIC CODE, UNFINISHED", M, 256, 9, t["fg50"])
    doc.text("M0–M4 BUILT", M, 336, 11, t["fg72"])
    doc.text("24 ARCHITECTURE DECISION RECORDS", M, 360, 11, t["fg72"])
    doc.text("FASTAPI · NEXT.JS · POSTGRESQL + PGVECTOR", M, 404, 10, t["fg50"])
    doc.text("CELERY · REDIS · MINIO · DOCKER", M, 424, 10, t["fg50"])

    # pipeline: the pulse reaches index; retrieval and chat remain unlit
    x0, x1, py = 560, R - 20, 178
    step = (x1 - x0) / (len(ORBIT_STAGES) - 1)
    xs = [x0 + i * step for i in range(len(ORBIT_STAGES))]
    doc.text("PROCESSING PIPELINE", x0, 128, 9, t["fg50"])
    doc.add(hline(x0, xs[ORBIT_BUILT - 1], py, t["fg"], 1.6),
            hline(xs[ORBIT_BUILT - 1], x1, py, t["fg34"], 1.4, ' stroke-dasharray="4 6"'))
    for i, (x, name) in enumerate(zip(xs, ORBIT_STAGES)):
        built = i < ORBIT_BUILT
        if built:
            doc.add('<rect x="%s" y="%s" width="10" height="10" fill="%s"/>' % (num(x - 5), num(py - 5), t["fg"]))
        else:
            doc.add('<rect x="%s" y="%s" width="10" height="10" fill="%s" stroke="%s" '
                    'stroke-dasharray="2 2"/>' % (num(x - 5), num(py - 5), t["bg"], t["fg50"]))
        doc.text(name, x, py - 20 if i % 2 == 0 else py + 32, 9, t["fg"] if built else t["fg50"],
                 anchor="middle")
    doc.text("NOT BUILT YET", (xs[ORBIT_BUILT] + xs[-1]) / 2, py + 66, 9, t["fg50"], anchor="middle")
    doc.add(hline(xs[ORBIT_BUILT] - 6, xs[-1] + 6, py + 50, t["fg20"]))
    span = xs[ORBIT_BUILT - 1] - x0
    # at rest the ember marks the frontier (index); in motion it runs there and dies
    doc.add('<circle class="pu" cx="%s" cy="%s" r="5" fill="%s"/>'
            % (num(xs[ORBIT_BUILT - 1]), num(py), t["ember"]))
    motion(doc, "@keyframes pu{0%%{transform:translateX(-%spx);opacity:0}8%%{opacity:1}"
                "70%%{transform:translateX(0);opacity:1}82%%,100%%{transform:translateX(14px);opacity:0}}"
                ".pu{animation:pu 5.5s cubic-bezier(.45,0,.4,1) infinite}" % num(span))

    # dependency direction, enforced in CI by import-linter
    dy = 330
    nodes = {"COMPOSITION": (560, dy), "API": (716, dy), "APPLICATION": (832, dy - 34),
             "INFRASTRUCTURE": (832, dy + 34), "DOMAIN": (1040, dy), "CORE": (1150, dy)}
    for name, (x, y) in nodes.items():
        doc.text(name, x, y + 4, 10, t["fg"])
    ww = lambda n: S.text_width(n) * 10
    arrow(doc, 560 + ww("COMPOSITION") + 10, dy, 706, dy, t["fg50"])
    arrow(doc, 716 + ww("API") + 10, dy - 4, 822, dy - 30, t["fg50"])
    arrow(doc, 716 + ww("API") + 10, dy + 4, 822, dy + 30, t["fg50"])
    arrow(doc, 832 + ww("APPLICATION") + 10, dy - 30, 1030, dy - 4, t["fg50"])
    arrow(doc, 832 + ww("INFRASTRUCTURE") + 10, dy + 30, 1030, dy + 4, t["fg50"])
    arrow(doc, 1040 + ww("DOMAIN") + 10, dy, 1140, dy, t["fg50"])
    doc.text("×", 880, dy + 5, 12, t["fg72"], weight=1.4)
    doc.text("DEPENDENCY DIRECTION · ENFORCED IN CI", 560, 408, 9, t["fg50"])
    doc.text("APPLICATION × INFRASTRUCTURE: NEITHER MAY IMPORT THE OTHER", 560, 428, 9, t["fg50"])
    return doc.svg()


# ----------------------------------------------------------- PL. IV  HELIOS
def helios(t):
    H = 470
    doc = Doc(t, H, "HELIOS, solar energy intelligence",
              "Plate IV. The title HELIOS, drawn as a cloud of points: the work exists but is not "
              "public. A schematic day of solar irradiance: a clear-sky curve, a dashed modelled "
              "forecast, a hatched band for the calibrated prediction interval, and observed "
              "points. Facts: physics plus machine learning, XGBoost with hold-out R-squared 0.856, "
              "calibrated prediction intervals.")
    frame(doc, "PL. IV", "HELIOS — SOLAR ENERGY INTELLIGENCE", "IN DEVELOPMENT · NOT PUBLIC")
    word(doc, "HELIOS", M, 214, 96, "field", seed=40, density=1.1)
    doc.text("INFERRED: EXISTS, NOT YET PUBLIC", M, 256, 9, t["fg50"])
    facts = ["PHYSICS + MACHINE LEARNING", "XGBOOST · HOLD-OUT R² 0.856",
             "CALIBRATED PREDICTION INTERVALS", "ONE-SECOND CALCULATOR", "FOURTEEN-VIEW CONSOLE"]
    for i, f in enumerate(facts):
        doc.text(f, M, 314 + i * 24, 11, t["fg72"] if i < 3 else t["fg50"])

    # a schematic day: clear sky, forecast, interval, observations
    cx0, cx1, top, base = 616, R, 128, 392
    hx = lambda h: cx0 + (h - 5) / 15.0 * (cx1 - cx0)
    hy = lambda v: base - v * (base - top)
    clear = lambda h: max(0.0, math.sin(math.pi * (h - 6) / 12.0)) ** 1.25 if 6 <= h <= 18 else 0.0
    kt = lambda h: 0.80 + 0.12 * math.sin(h * 1.7) - 0.16 * math.exp(-((h - 14.2) / 0.9) ** 2)
    fc = lambda h: clear(h) * kt(h)
    band = lambda h: 0.03 + 0.11 * clear(h)
    hs = [6 + i * 0.1 for i in range(121)]
    pts = lambda f: " ".join("%s %s" % (num(hx(h)), num(hy(f(h)))) for h in hs)
    upper = [(hx(h), hy(min(clear(h), fc(h) + band(h)))) for h in hs]
    lower = [(hx(h), hy(max(0.0, fc(h) - band(h)))) for h in reversed(hs)]
    poly = "M" + "L".join("%s %s" % (num(a), num(b)) for a, b in upper + lower) + "Z"
    cid = doc.nid("b")
    doc.defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, poly))
    hatch = "".join("M%s %sl-160 160" % (num(x), num(top)) for x in range(int(cx0), int(cx1) + 200, 9))
    doc.add(hline(cx0, cx1, base, t["fg50"]),
            '<g clip-path="url(#%s)"><path d="%s" stroke="%s"/></g>' % (cid, hatch, t["fg34"]),
            '<path d="%s" stroke="%s" stroke-width=".8"/>' % (poly, t["fg34"]),
            '<path d="M%s" stroke="%s" stroke-width="1.2"/>' % (pts(clear), t["fg50"]),
            '<path d="M%s" stroke="%s" stroke-width="2" stroke-dasharray="7 5"/>' % (pts(fc), t["fg"]))
    rng = random.Random(7)
    obs = []
    for i in range(27):
        h = 6.6 + i * 0.42
        v = min(clear(h), max(0.0, fc(h) + rng.gauss(0, band(h) * 0.5)))
        obs.append("M%s %sh0" % (num(hx(h)), num(hy(v))))
    doc.add('<path d="%s" stroke="%s" stroke-width="4.6"/>' % ("".join(obs), t["fg72"]))
    for h in range(6, 20, 3):
        doc.add(vline(hx(h), base, base + 6, t["fg50"]))
        doc.text("%02d:00" % h, hx(h), base + 24, 8, t["fg50"], anchor="middle")
    # the one curious thing: how wide the interval is at this hour
    ch = 13.0
    ux, uy, ly = hx(ch), hy(min(clear(ch), fc(ch) + band(ch))), hy(fc(ch) - band(ch))
    doc.add(vline(ux, top - 6, base, t["ember"], 1),
            hline(ux - 7, ux + 7, uy, t["ember"], 1.6), hline(ux - 7, ux + 7, ly, t["ember"], 1.6))
    ember(doc, ux, hy(fc(ch)), 4.5, 11)
    doc.text("INTERVAL AT 13:00", ux + 14, top + 4, 8, t["fg72"])
    doc.text("SCHEMATIC — FORM, NOT DATA", cx1, 128 - 22, 8, t["fg50"], anchor="end")
    legend = [("CLEAR SKY", t["fg50"], ""), ("FORECAST", t["fg"], "7 5"), ("OBSERVED", None, ""),
              ("INTERVAL", None, "")]
    lx = cx0
    for name, c, dash in legend:
        if name == "OBSERVED":
            doc.add('<path d="M%s %sh0" stroke="%s" stroke-width="4.6"/>' % (num(lx + 4), 438, t["fg72"]))
            lx += 16
        elif name == "INTERVAL":
            doc.add('<path d="M%s 444l8 -10M%s 444l8 -10" stroke="%s"/>' % (num(lx), num(lx + 6), t["fg50"]))
            lx += 20
        else:
            doc.add(hline(lx, lx + 22, 438, c, 1.6, ' stroke-dasharray="%s"' % dash if dash else ""))
            lx += 30
        lx += doc.text(name, lx, 442, 8, t["fg50"]) + 28
    return doc.svg()


# ----------------------------------------------------------- PL. V  NOT YET
OPEN = [("SPECTRA", "MULTIMODAL AI / COMPUTER VISION"),
        ("SYNCHRO", "DISTRIBUTED SYSTEMS / REAL-TIME"),
        ("AETHER", "CREATIVE COMPUTING / WEBGL")]


def not_yet(t):
    H = 470
    doc = Doc(t, H, "Not yet: SPECTRA, SYNCHRO, AETHER",
              "Plate V. Three names drawn only as sketches, because nothing public exists for "
              "them yet: SPECTRA, multimodal AI and computer vision; SYNCHRO, distributed systems "
              "and real-time; AETHER, creative computing and WebGL. Each has a dashed mark of its "
              "question. There is no ember and no ground: nothing here is lit, or printed, yet.",
              ground=False)
    frame(doc, "PL. V", "NOT YET", "NOTHING RESOLVES PAST THE EVIDENCE FOR IT")
    third = CW / 3.0
    dash = ' stroke-dasharray="3 5"'
    for i, (name, kind) in enumerate(OPEN):
        x = M + i * third
        if i:
            doc.add(vline(x - 18, 108, H - 60, t["fg12"]))
        word(doc, name, x, 196, 50, "sketch", seed=90 + i * 13, weight=1.5, passes=2)
        doc.text(kind, x, 236, 10, t["fg72"])
        doc.text("SKETCHED: NAMED, NO CODE YET", x, 258, 8, t["fg50"])
        c, my = t["fg34"], 346
        if name == "SPECTRA":      # an image, a text and a signal approach a line and stop short
            lx = x + 250
            ic = t["fg50"]
            doc.add('<rect x="%s" y="%s" width="34" height="26" stroke="%s"/>' % (num(x), my - 53, ic),
                    '<path d="M%s %sl9 -10 7 6 6 -5 10 10" stroke="%s"/>' % (num(x + 1), my - 29, ic),
                    '<path d="M%s %sh34M%s %sh34M%s %sh20" stroke="%s"/>'
                    % (num(x), my - 8, num(x), my, num(x), my + 8, ic),
                    '<path d="M%s %s' % (num(x), my + 42) + "".join(
                        "L%s %s" % (num(x + j * 1.7), num(my + 42 - 8 * math.sin(j * 0.45))) for j in range(21))
                    + '" stroke="%s"/>' % ic)
            for yy in (my - 40, my, my + 42):
                arrow(doc, x + 50, yy, lx - 18, yy, c, 1, 5, "3 5")
            doc.add(vline(lx, my - 58, my + 58, t["fg50"], 1, dash))
        elif name == "SYNCHRO":    # three clocks, never quite in phase
            lx = x + 250
            for j, off in enumerate((0, 7, 15)):
                yy = my - 36 + j * 36
                doc.add(hline(x, lx - 12, yy, c, 1, dash))
                doc.add('<path d="%s" stroke="%s" stroke-width="1.4"/>' % (
                    "".join("M%s %sv-10" % (num(x + off + q * 30), num(yy + 5))
                            for q in range(int((lx - 24 - x - off) / 30) + 1)), t["fg50"]))
            doc.add(vline(lx, my - 58, my + 58, t["fg50"], 1, dash))
            doc.text("?", lx + 12, my + 6, 16, t["fg50"], weight=1.4)
        else:                      # a sphere that is still only its construction
            cx, r = x + 110, 56
            doc.add('<circle cx="%s" cy="%s" r="%s" stroke="%s"%s/>' % (num(cx), my, r, c, dash))
            for q in (0.35, 0.72):
                doc.add('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" stroke="%s"%s/>'
                        % (num(cx), my, num(r * q), r, c, dash),
                        '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" stroke="%s"%s/>'
                        % (num(cx), my, r, num(r * q), c, dash))
    doc.text("EVERY NAME ON THESE PLATES IS DRAWN ONLY AS FAR AS ITS EVIDENCE GOES", M, H - 34, 9,
             t["fg50"])
    return doc.svg()


# -------------------------------------------------------------- PL. VI  card
TOOLS = [
    ("01", "SKETCHES", ["FIGMA", "FRAMER"]),
    ("02", "INFERS", ["SCIKIT-LEARN", "XGBOOST", "EMBEDDINGS", "PGVECTOR"]),
    ("03", "COMPUTES", ["PYTHON", "TYPESCRIPT", "JAVASCRIPT", "CELERY"]),
    ("04", "ARRANGES", ["NEXT.JS", "TAILWIND", "HTML + CSS", "THREE.JS", "SVG"]),
    ("05", "MEASURES", ["FASTAPI", "POSTGRESQL", "REDIS", "MINIO", "DOCKER", "GH ACTIONS"]),
]
# work -> tools it is made with, as its repository or record shows
WORKS = [
    ("SIDDHARTHA", {"JAVASCRIPT", "HTML + CSS", "THREE.JS"}),
    ("ORBIT", {"PYTHON", "TYPESCRIPT", "CELERY", "EMBEDDINGS", "PGVECTOR", "NEXT.JS", "TAILWIND",
               "FASTAPI", "POSTGRESQL", "REDIS", "MINIO", "DOCKER", "GH ACTIONS"}),
    ("HELIOS", {"PYTHON", "SCIKIT-LEARN", "XGBOOST", "NEXT.JS", "FASTAPI"}),
    ("THIS PROFILE", {"PYTHON", "SVG", "GH ACTIONS"}),
    ("GRAVITY PLAYGROUND", {"JAVASCRIPT", "HTML + CSS"}),
    ("TRAVELEASE", {"JAVASCRIPT", "HTML + CSS"}),
    ("PETPONKS", {"FIGMA", "FRAMER"}),
    ("SPECTRA", set()), ("SYNCHRO", set()), ("AETHER", set()),
]


def card(t):
    H = 660
    doc = Doc(t, H, "The stack, as a punched card",
              "Plate VI. A punched card: one row per work, one column per tool, grouped by the "
              "five verbs. A hole means the tool is in that work. " + " ".join(
                  "%s: %s." % (w.title(), ", ".join(sorted(s)) if s else "no holes yet")
                  for w, s in WORKS))
    frame(doc, "PL. VI", "THE STACK, PUNCHED", "A HOLE MEANS THE TOOL IS IN THE WORK")
    cols = [(n, verb, tool) for n, verb, tools in TOOLS for tool in tools]
    cx0, cy0, cx1, cy1 = M, 112, R, H - 44
    lab_w = 212
    step = (cx1 - cx0 - lab_w - 20) / len(cols)
    colx = [cx0 + lab_w + (i + 0.5) * step for i in range(len(cols))]
    rows_y0, rh = 318, 23
    card_path = "M%s %sH%sV%sH%sV%sZ" % (num(cx0 + 26), num(cy0), num(cx1), num(cy1), num(cx0),
                                        num(cy0 + 26))
    doc.add('<path d="%s" fill="%s" stroke="%s"/>' % (card_path, t["fg7"], t["fg20"]))
    # band headers
    i = 0
    for n, verb, tools in TOOLS:
        a, b = colx[i] - step / 2 + 3, colx[i + len(tools) - 1] + step / 2 - 3
        doc.text(n, a, 132, 9, t["fg50"])
        doc.text(verb, a, 150, 9, t["fg"])
        doc.add(hline(a, b, 160, t["fg50"]))
        i += len(tools)
    for x, (n, verb, tool) in zip(colx, cols):
        rtext(doc, tool, x + 4, 290, 9, t["fg72"])
        doc.text("%d" % (cols.index((n, verb, tool)) + 1), x, 306, 7, t["fg34"], anchor="middle")
    hole_w, hole_h = 9, 15
    for r, (work, used) in enumerate(WORKS):
        open_ = not used
        y = rows_y0 + r * rh + rh / 2 + (30 if open_ else 0)
        if open_ and WORKS[r - 1][1]:
            doc.text("NOT YET PUNCHED", cx0 + 22, y - rh / 2 - 9, 8, t["fg50"])
        doc.text(work, cx0 + 22, y + 4, 10, t["fg50"] if open_ else t["fg"])
        if r and not (open_ and WORKS[r - 1][1]):
            doc.add(hline(cx0 + 22, cx1 - 16, y - rh / 2, t["fg12"]))
        holes, dots = [], []
        for x, (_, _, tool) in zip(colx, cols):
            if tool in used:
                holes.append("M%s %sh%sv%sh-%sz" % (num(x - hole_w / 2), num(y - hole_h / 2), hole_w,
                                                    hole_h, hole_w))
            else:
                dots.append("M%s %sh0" % (num(x), num(y)))
        if dots:
            doc.add('<path d="%s" stroke="%s" stroke-width="1.6"/>' % ("".join(dots), t["fg20"]))
        if holes:
            doc.add('<path d="%s" fill="%s"/>' % ("".join(holes), t["fg"]))
    # the corner cut says which way up the card goes; it is the only warm mark here
    doc.add('<path d="M%s %sL%s %s" stroke="%s" stroke-width="2"/>'
            % (num(cx0), num(cy0 + 26), num(cx0 + 26), num(cy0), t["ember"]))
    doc.text("WORKS × TOOLS", cx0 + 22, cy1 - 14, 8, t["fg50"])
    doc.text("SIDDHUPERURI · 2026", cx1 - 16, cy1 - 14, 8, t["fg50"], anchor="end")
    return doc.svg()


# ------------------------------------------------------------ PL. VII trace
def fetch_trace(token):
    q = ('query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{'
         'totalContributions weeks{contributionDays{date contributionCount}}}}}}')
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"l": LOGIN}}).encode(),
        headers={"Authorization": "bearer " + token, "User-Agent": LOGIN + "-profile"})
    with urllib.request.urlopen(req, timeout=30) as r:
        cal = json.load(r)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [[d["date"], d["contributionCount"]] for w in cal["weeks"] for d in w["contributionDays"]]
    data = {"login": LOGIN, "source": "GitHub GraphQL API, contributionCalendar",
            "fetched": dt.date.today().isoformat(), "days": days}
    with open(TRACE_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=0)
        f.write("\n")
    return data


def trace(t, data):
    H = 330
    days = data["days"]
    counts = [c for _, c in days]
    total, active = sum(counts), sum(1 for c in counts if c)
    cmax = max(counts) or 1
    fmt = lambda iso: ".".join(reversed(iso.split("-")))
    doc = Doc(t, H, "Trace: public contributions, last 52 weeks",
              "Plate VII. Every day of the last year as one mark on a line, from %s to %s. "
              "Days with public contributions rise from the line. %d contributions on %d days."
              % (fmt(days[0][0]), fmt(days[-1][0]), total, active))
    frame(doc, "PL. VII", "TRACE — PUBLIC CONTRIBUTIONS, LAST 52 WEEKS",
          "GITHUB API · %s" % fmt(data["fetched"]))
    base, x0, x1 = 236, M, R - 30
    step = (x1 - x0) / (len(days) - 1)
    quiet, marks = [], []
    first = None
    for i, (iso, c) in enumerate(days):
        x = x0 + i * step
        if c:
            first = first if first is not None else (x, iso)
            marks.append("M%s %sV%s" % (num(x), base, num(base - 12 - 104 * math.sqrt(c / cmax))))
        else:
            quiet.append("M%s %sh0" % (num(x), base))
        d = dt.date.fromisoformat(iso)
        if d.day == 1:
            doc.add(vline(x, base + 8, base + 16, t["fg50"]))
            doc.text(d.strftime("%b").upper() + (" %d" % d.year if d.month == 1 else ""),
                     x, base + 34, 8, t["fg50"])
    doc.add('<path d="%s" stroke="%s" stroke-width="1.5"/>' % ("".join(quiet), t["fg34"]))
    if marks:
        doc.add('<path d="%s" stroke="%s" stroke-width="2.2" stroke-linecap="butt"/>'
                % ("".join(marks), t["fg"]))
    if first:
        fx, iso = first
        side = -1 if fx > W / 2 else 1
        doc.add(hline(fx + side * 8, fx + side * 30, base - 60, t["fg50"]))
        doc.text("FIRST ACTIVE DAY " + fmt(iso), fx + side * 38, base - 56, 9, t["fg72"],
                 anchor="end" if side < 0 else "start")
    ember(doc, x1 + 16, base, 4.5, 10)
    doc.text("TODAY", x1 + 16, base + 34, 8, t["fg72"], anchor="middle")
    doc.text("%d CONTRIBUTIONS" % total, M, 128, 20, t["fg"], weight=1.7)
    doc.text("ON %d DAYS OF %d" % (active, len(days)), M, 156, 11, t["fg72"])
    doc.text("A MARK FOR EVERY DAY. THE QUIET ONES STAY ON THE LINE.", M, H - 34, 9, t["fg50"])
    return doc.svg()


# ------------------------------------------------------------ PL. VIII end
SENTENCE = ["JACK OF ALL, MASTER OF NONE,", "BUT OFTEN TIMES BETTER", "THAN MASTER OF ONE."]


def end(t):
    H = 470
    doc = Doc(t, H, "Jack of all, master of none, but often times better than master of one",
              "Plate VIII, the last. The sentence 'Jack of all, master of none, but often times "
              "better than master of one', left as a sketch: it never reaches the last stage. "
              "An ember waits below it. The wish is at the bottom of the well.")
    frame(doc, "PL. VIII", "THE EDGE", "END OF PLATES")
    C = 40
    doc.add('<g class="sw">')
    for i, ln in enumerate(SENTENCE):
        w = S.text_width(ln, 0.3) * C
        word(doc, ln, (W - w) / 2, 168 + i * 74, C, "sketch", seed=300 + i * 40, weight=1.5, passes=2)
    doc.add("</g>")
    ember(doc, W / 2, 360, 5, 12)
    doc.text("THE WISH IS AT THE BOTTOM OF THE WELL", W / 2, 398, 9, t["fg50"], anchor="middle")
    doc.add(hline(M, R, H - 58, t["fg20"]))
    doc.text("SIDDHARTHA / 2026", M, H - 30, 11, t["fg72"])
    doc.text("SET IN ITS OWN ALPHABET · NO FONT FILES", R, H - 30, 11, t["fg50"], anchor="end")
    # the room breathes, very slowly
    motion(doc, "@keyframes sw{from{transform:translateX(-5px)}to{transform:translateX(5px)}}"
                ".sw{animation:sw 11s ease-in-out infinite alternate}")
    return doc.svg()


# ---------------------------------------------------------------------- main
def load_trace(fetch):
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if fetch:
        if not token:
            sys.exit("--fetch needs GITHUB_TOKEN or GH_TOKEN")
        return fetch_trace(token)
    with open(TRACE_JSON, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    data = load_trace("--fetch" in argv)
    plates = [("hero", hero), ("artwork", artwork), ("orbit", orbit), ("helios", helios),
              ("not-yet", not_yet), ("card", card), ("trace", lambda t: trace(t, data)),
              ("end", end)]
    only = [a for a in argv if not a.startswith("--")]
    total = 0
    os.makedirs(OUT, exist_ok=True)
    for t in THEMES:
        for name, fn in plates:
            if only and name not in only:
                continue
            path = os.path.join(OUT, "%s-%s.svg" % (name, t["name"]))
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(fn(t))
            size = os.path.getsize(path)
            total += size
            print("  %-22s %7d B" % (os.path.basename(path), size))
    print("\ntotal %d bytes" % total)


if __name__ == "__main__":
    main(sys.argv[1:])
