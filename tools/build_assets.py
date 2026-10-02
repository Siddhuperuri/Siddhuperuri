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
        missing = sorted({c for c in s if c.upper() not in S.G})
        if missing:
            raise ValueError("no glyph for %r in %r" % ("".join(missing), s))
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


def stage_sketch(doc, ch, x, y, C, seed, weight=1.7, passes=3, wobble=1.0, cls=""):
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
            a1 = (0.010 + 0.005 * p) * C * wobble
            sx, sy = rng.gauss(0, 0.006 * C * wobble), rng.gauss(0, 0.006 * C * wobble)
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
    k = min(1.0, C / 96.0)
    pops = (("t", total / 0.95 * density, 0.020, t["fg"], max(1.5, 2.5 * k)),
            ("l", total / 4.2 * density, 0.065, t["fg50"], max(1.3, 2.0 * k)))
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
    doc.add('<path%s d="%s" stroke="%s" stroke-width="%s"/>'
            % (' class="%s fn"' % cls if cls else "", "".join(d), t["fg34"], num(max(1.2, 1.8 * k))))


def stage_lattice(doc, ch, x, y, C, cell, half, origin, cls="", empties=True, fill=True):
    """LATTICE - the letter quantised into computed cells on a shared grid."""
    t, g = doc.t, S.G[ch]
    polys = [S.stroke_points(st) for st in g["s"]]
    ox, oy = origin
    pad = half + cell
    i0, i1 = math.floor((x - pad - ox) / cell), math.ceil((x + g["w"] * C + pad - ox) / cell)
    j0, j1 = math.floor((y - C - pad - oy) / cell), math.ceil((y + pad - oy) / cell)
    full, empty, s = [], [], cell * 0.81
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
        doc.add('<path%s d="%s" stroke="%s" stroke-width="1.6"/>'
                % ("" if fill else ' class="%s"' % cls, "".join(empty), t["fg20"]))
    if fill:
        doc.add('<path%s d="%s" fill="%s"/>' % (' class="%s"' % cls if cls else "", "".join(full),
                                              t["fg"]))


def stage_design(doc, ch, x, y, C, weight=2.6, cls="", construction=True, strokes=True):
    """DESIGN - the exact geometry of the letter, with construction and survey ticks."""
    t, g = doc.t, S.G[ch]
    to = _to_screen(x, y, C)
    n = 7 * min(1.0, C / 96.0)
    if construction:
        cons, nodes, seen = [], [], set()
        for st in g["s"]:
            for pc in st:
                if pc[0] == "A":
                    _, cx, cy, rx, ry, a0, a1 = pc
                    X, Y = to(cx, cy)
                    cons.append('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"/>'
                                % (num(X), num(Y), num(rx * C), num(ry * C)))
                    c = n * 5 / 7        # half the centre cross: 5 at full size
                    nodes.append("M%s %sh%sM%s %sv%s" % (num(X - c), num(Y), num(2 * c),
                                                          num(X), num(Y - c), num(2 * c)))
                else:
                    for p in pc[1]:
                        key = (round(p[0], 3), round(p[1], 3))
                        if key in seen:
                            continue
                        seen.add(key)
                        X, Y = to(*p)
                        nodes.append("M%s %sh%sv%sh-%sz" % (num(X - n / 2), num(Y - n / 2),
                                                            num(n), num(n), num(n)))
        doc.add('<g%s stroke="%s">%s</g>' % (' class="%s c"' % cls if cls else "", t["fg20"], "".join(cons)),
                '<path%s d="%s" stroke="%s"/>' % (' class="%s c"' % cls if cls else "",
                                                 "".join(nodes), t["fg50"]))
    if not strokes:
        return
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
NAME = "JAI SAI SIDDHARTHA"
# The name resolves as it is read. JAI is sketched, SAI inferred; SIDDHARTHA is kept
# whole, and it is where the last three layers add up: a computed grid behind it,
# construction geometry around it, the measured letter on top.
PARTS = [((0, 3), "01", "SKETCHES", "TRACE"), ((4, 7), "02", "INFERS", "FIELD"),
         ((8, 18), "03 – 05", "COMPUTES · ARRANGES · MEASURES", "LATTICE · DESIGN · INSTRUMENT")]
DOOR = 13


def hero(t):
    H, track, pad, cap = 410, 0.22, 10, 206
    part = {i: k for k, ((a, b), *_) in enumerate(PARTS) for i in range(a, b)}
    # a measured letter is inset by its own stroke, so it is 0.87w + 0.13 wide
    widths = [0.87 * S.G[ch]["w"] + 0.13 if part.get(i) == 2 else S.G[ch]["w"]
              for i, ch in enumerate(NAME)]
    C = (CW - 2 * pad) / (sum(widths) + track * (len(NAME) - 1))
    base, wm = cap + C, 0.13 * C
    xs, x = [], M + pad
    for w in widths:
        xs.append(x)
        x += (w + track) * C
    span = [(xs[a], xs[b - 1] + widths[b - 1] * C) for (a, b), *_ in PARTS]

    doc = Doc(t, H, "Jai Sai Siddhartha",
              "The name JAI SAI SIDDHARTHA on one line, resolving as it is read: JAI sketched by "
              "hand, SAI inferred as a cloud of points, and SIDDHARTHA whole and measured, over a "
              "computed grid and inside its construction geometry, with dimension lines. An ember "
              "sits in the A that SIDDHA and ARTHA share.")
    doc.add(crops(t, W, H))

    # frame: metadata, rules, the instrument lines the name sits on
    doc.text("PL. I", M, 62, 11, t["fg"], cls="rv")
    doc.text("PERURI JAI SAI SIDDHARTHA", M + 66, 62, 11, t["fg72"], cls="rv")
    doc.text("FIVE LAYERS · ONE VANTAGE", R, 62, 11, t["fg50"], anchor="end", cls="rv")
    doc.add(hline(M, R, 84, t["fg20"], extra=' class="ln" pathLength="1"'))
    cuts = [M] + [(span[k][1] + span[k + 1][0]) / 2 for k in range(len(PARTS) - 1)] + [R]
    for cx in cuts:
        doc.add(vline(cx, 164, base + 50, t["fg12"], extra=' class="ln" pathLength="1"'))
    for (_, n, verb, layer), (a, b) in zip(PARTS, span):
        mid = (a + b) / 2
        nw, vw = S.text_width(n) * 10, S.text_width(verb) * 12
        left = mid - (nw + 8 + vw) / 2
        doc.text(n, left, 128, 10, t["fg50"], cls="rv")
        doc.text(verb, left + nw + 8, 128, 12, t["fg"], weight=1.4, cls="rv")
        doc.text(layer, mid, 147, 8, t["fg50"], anchor="middle", cls="rv")
    for yy, lab in ((cap, "1"), (base, "0")):
        doc.add(hline(M, R, yy, t["fg20"], extra=' class="ln" pathLength="1"'))
        doc.text(lab, M - 12, yy + 4, 8, t["fg50"], anchor="end", cls="rv")
    doc.add(hline(M, R, cap + C / 2, t["fg7"], extra=' stroke-dasharray="2 6"'))

    # the name, resolving as it is read
    for i, ch in enumerate(NAME):
        if ch == " ":
            continue
        k, x = part[i], xs[i]
        if k == 0:
            stage_sketch(doc, ch, x, base, C, 11 + i, weight=1.35, wobble=1.9, cls="s1")
        elif k == 1:
            stage_field(doc, ch, x, base, C, 11 + i, cls="s2")
        else:
            # computed, arranged and measured, in one place
            stage_lattice(doc, ch, x, base, C, C / 11, 0.07 * C, (M, cap), cls="s3", fill=False)
            stage_design(doc, ch, x + wm / 2, base - wm / 2, C - wm, cls="s4", strokes=False)
            stage_measure(doc, ch, x, base, C, wm, cls="s5")

    # instrument: true measurements of the resolved word, in cap heights
    a, b = span[2]
    dim_h(doc, a, b, cap - 16, "%.2f" % ((b - a) / C), ext_from=cap - 4)
    hx = xs[16]
    doc.add(hline(hx, hx + wm, base + 15, t["fg50"]),
            vline(hx, base + 8, base + 22, t["fg50"]), vline(hx + wm, base + 8, base + 22, t["fg50"]))
    doc.text("%.2f" % (wm / C), hx + wm + 7, base + 19, 8, t["fg72"])
    dim_v(doc, b + 14, cap, base, "1.00", cap=8)
    doc.add(reg(t, R - 6, cap - 36, 4.5), reg(t, R - 6, base + 36, 4.5))

    # the door: SIDDHA + ARTHA share one A, and the ember waits in its counter
    # The A's anchor is the incentre of its counter; the ring is sized to the circle
    # that fits inside the drawn counter (inradius 0.19 of the skeleton, less half a stroke).
    ga, sk = S.G["A"], C - wm
    ex, ey = xs[DOOR] + wm / 2 + ga["anchor"][0] * sk, base - wm / 2 - ga["anchor"][1] * sk
    fit = 0.19 * sk - wm / 2
    doc.add('<circle class="em" cx="%s" cy="%s" r="%s" fill="%s"/>' % (num(ex), num(ey), num(fit * 0.45), t["ember"]),
            '<circle class="er" cx="%s" cy="%s" r="%s" stroke="%s"/>' % (num(ex), num(ey), num(fit - 1), t["ember"]))
    doc.text("↑ SIDDHA + ARTHA SHARE THIS A", ex - 4, base + 38, 9, t["fg72"], cls="rv")

    doc.add(hline(M, R, H - 60, t["fg20"], extra=' class="ln" pathLength="1"'))
    doc.text("THE NAME IS WHAT THE PARTS ADD UP TO", M, H - 28, 11, t["fg72"], cls="rv")
    doc.text("INDIA · UTC +05:30", R, H - 28, 11, t["fg50"], anchor="end", cls="rv")

    # one-shot reveal, in the order a letter becomes: sketched, inferred, computed,
    # arranged, measured. The hero is above the fold, so it is seen while it plays.
    motion(doc, DRAW + EMBER + SHIMMER + (
        "@keyframes up{from{opacity:0;transform:translateY(6px)}}"
        ".ln{animation:dw 1s %(e)s both}"
        ".rv{animation:fi .8s %(e)s .1s both}"
        ".s1{animation:dw 1.1s %(e)s both}.s1.p0{animation-delay:.25s}"
        ".s1.p1{animation-delay:.4s}.s1.p2{animation-delay:.55s}"
        ".s2.ft{animation:fi 1s ease-out .95s both}"
        ".s2.fn{animation:fi 1s ease-out .55s both,shn 3.4s ease-in-out 2.6s infinite alternate}"
        ".s2.fl{animation:fi 1s ease-out .75s both,shl 4.8s ease-in-out 2.6s infinite alternate}"
        ".s3{animation:fi .6s steps(4) 1.2s both}"
        ".s4.c{animation:fi .8s ease 1.5s both}"
        ".s5{animation:up .7s %(e)s 1.9s both}"
        ".em{animation:fi .6s ease 2.6s both}"
        ".er{animation-delay:3.2s}" % {"e": EASE}))
    return doc.svg()


# Loops below the fold rest for most of each cycle: stillness is the artwork's first law.
# Every static state is the complete image, so prefers-reduced-motion loses nothing.
REDRAW = ("@keyframes rd{0%{stroke-dasharray:1;stroke-dashoffset:1;opacity:1}"
          "18%{stroke-dasharray:1;stroke-dashoffset:0}18.1%,90%{stroke-dasharray:none;opacity:1}"
          "97%{opacity:0}97.1%,100%{stroke-dasharray:1;stroke-dashoffset:1;opacity:0}}")
SHIMMER = "@keyframes shn{from{opacity:1}to{opacity:.25}}@keyframes shl{from{opacity:1}to{opacity:.55}}"
NUDGE = ("@keyframes nd{0%,62%,100%{transform:translate(0,0)}76%{transform:translate(5px,0)}}"
         ".nd{animation:nd 3.6s ease-in-out infinite}"
         "@keyframes ndd{0%,62%,100%{transform:translate(0,0)}76%{transform:translate(0,4px)}}"
         ".ndd{animation:ndd 3.6s ease-in-out infinite}")


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


def word(doc, text, x, y, C, stage, seed=1, track=0.3, cls="", **kw):
    """A word drawn at one stage of resolution. Returns its width."""
    lay, w = S.text_layout(text, track)
    for n, (g, gx, ch) in enumerate(lay):
        if not g["s"]:
            continue
        X = x + gx * C
        if stage == "sketch":
            stage_sketch(doc, ch, X, y, C, seed + n, weight=kw.get("weight", 1.6),
                         passes=kw.get("passes", 3), cls=cls)
        elif stage == "field":
            stage_field(doc, ch, X, y, C, seed + n, density=kw.get("density", 1.0), cls=cls)
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


def arrow(doc, x1, y1, x2, y2, c, w=1.2, head=6, dash="", extra=""):
    a = math.atan2(y2 - y1, x2 - x1)
    hx1, hy1 = x2 - head * math.cos(a - 0.45), y2 - head * math.sin(a - 0.45)
    hx2, hy2 = x2 - head * math.cos(a + 0.45), y2 - head * math.sin(a + 0.45)
    doc.add('<path d="M%s %sL%s %s" stroke="%s" stroke-width="%s"%s%s/>'
            % (num(x1), num(y1), num(x2), num(y2), c, num(w),
               ' stroke-dasharray="%s"' % dash if dash else "", extra),
            '<path d="M%s %sL%s %sL%s %s" stroke="%s" stroke-width="%s"%s/>'
            % (num(hx1), num(hy1), num(x2), num(y2), num(hx2), num(hy2), c, num(w), extra))


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
    for sx, _ in depth[1:]:
        doc.add('<circle class="hit" cx="%s" cy="%s" r="5.5" stroke="%s" fill="%s"/>'
                % (num(sx), num(vy + u * k * (sx - vx)), t["fg72"], t["fg"]))
    # in motion the eye swings about the nearest mark until its ray is V*'s ray; then
    # every sheet's mark lies on it, and they light. Then it drifts off again.
    doc.add('<g class="eye">',
            line(ox, oy, far + 14, m0 + sl * (far + 14 - s0), t["fg72"], 1, ' stroke-dasharray="3 4"'),
            '<circle cx="%s" cy="%s" r="3.5" stroke="%s"/>' % (num(ox), num(oy), t["fg72"]), '</g>')
    swing = math.degrees(math.atan2(m0 - vy, s0 - vx) - math.atan2(m0 - oy, s0 - ox))
    motion(doc, "@keyframes eye{0%%,24%%{transform:rotate(0)}44%%,74%%{transform:rotate(%.3fdeg)}"
                "92%%,100%%{transform:rotate(0)}}"
                ".eye{transform-box:view-box;transform-origin:%spx %spx;"
                "animation:eye 11s cubic-bezier(.45,0,.3,1) infinite}"
                "@keyframes hit{0%%,43%%{fill-opacity:0}50%%,71%%{fill-opacity:1}78%%,100%%{fill-opacity:0}}"
                ".hit{fill-opacity:0;animation:hit 11s ease infinite}" % (swing, num(s0), num(m0)))
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
ORBIT_BUILT = 7


def orbit(t):
    H = 470
    doc = Doc(t, H, "ORBIT, a knowledge and document platform",
              "Plate III. The title ORBIT, drawn as exact construction geometry: public code, "
              "still in development and not production-ready. A pipeline of seven stages: parse, "
              "normalize, chunk, embed, index, retrieval and chat are all implemented and drawn "
              "solid. An ember pulse runs through the stages and stops at chat. "
              "Below, the dependency direction enforced in CI: composition, api, application "
              "and infrastructure, domain, core.")
    frame(doc, "PL. III", "ORBIT — KNOWLEDGE AND DOCUMENT PLATFORM", "IN DEVELOPMENT · PUBLIC")
    word(doc, "ORBIT", M, 214, 96, "design", weight=2.6)
    doc.text("ARRANGED: PUBLIC CODE, UNFINISHED", M, 256, 9, t["fg50"])
    doc.text("M0–M7 IMPLEMENTED", M, 312, 11, t["fg72"])
    doc.text("NOT PRODUCTION-READY: ITS README SAYS SO", M, 336, 11, t["fg72"])
    doc.text("24 ARCHITECTURE DECISION RECORDS", M, 360, 11, t["fg72"])
    doc.text("FASTAPI · NEXT.JS · POSTGRESQL + PGVECTOR", M, 404, 10, t["fg50"])
    doc.text("CELERY · REDIS · MINIO · DOCKER", M, 424, 10, t["fg50"])

    # pipeline: the pulse reaches index; retrieval and chat remain unlit
    x0, x1, py = 560, R - 20, 178
    step = (x1 - x0) / (len(ORBIT_STAGES) - 1)
    xs = [x0 + i * step for i in range(len(ORBIT_STAGES))]
    doc.text("FROM DOCUMENT TO CITED ANSWER", x0, 128, 9, t["fg50"])
    doc.add(hline(x0, xs[ORBIT_BUILT - 1], py, t["fg"], 1.6))
    if ORBIT_BUILT < len(ORBIT_STAGES):
        doc.add(hline(xs[ORBIT_BUILT - 1], x1, py, t["fg34"], 1.4, ' stroke-dasharray="4 6"'))
    for i, (x, name) in enumerate(zip(xs, ORBIT_STAGES)):
        built = i < ORBIT_BUILT
        if built:
            doc.add('<rect x="%s" y="%s" width="10" height="10" fill="%s"/>' % (num(x - 5), num(py - 5), t["fg"]))
        else:
            doc.add('<rect x="%s" y="%s" width="10" height="10" fill="%s" stroke="%s" '
                    'stroke-dasharray="2 2"/>' % (num(x - 5), num(py - 5), t["bg"], t["fg50"]))
        doc.text(name, x, py - 20 if i % 2 == 0 else py + 32, 9, t["fg"] if built else t["fg50"],
                 anchor="middle")
    if ORBIT_BUILT < len(ORBIT_STAGES):
        doc.text("NOT BUILT YET", (xs[ORBIT_BUILT] + xs[-1]) / 2, py + 66, 9, t["fg50"], anchor="middle")
        doc.add(hline(xs[ORBIT_BUILT] - 6, xs[-1] + 6, py + 50, t["fg20"]))
    else:
        doc.text("ALL SEVEN STAGES IMPLEMENTED", (x0 + x1) / 2, py + 66, 9, t["fg50"], anchor="middle")
        doc.add(hline(x0 - 6, x1 + 6, py + 50, t["fg20"]))
    span = xs[ORBIT_BUILT - 1] - x0
    # at rest the ember marks the frontier (the last built stage); in motion it runs there and dies
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
    da = ' class="da d%d" pathLength="1"'
    arrow(doc, 560 + ww("COMPOSITION") + 10, dy, 706, dy, t["fg50"], extra=da % 0)
    arrow(doc, 716 + ww("API") + 10, dy - 4, 822, dy - 30, t["fg50"], extra=da % 1)
    arrow(doc, 716 + ww("API") + 10, dy + 4, 822, dy + 30, t["fg50"], extra=da % 1)
    arrow(doc, 832 + ww("APPLICATION") + 10, dy - 30, 1030, dy - 4, t["fg50"], extra=da % 2)
    arrow(doc, 832 + ww("INFRASTRUCTURE") + 10, dy + 30, 1030, dy + 4, t["fg50"], extra=da % 2)
    arrow(doc, 1040 + ww("DOMAIN") + 10, dy, 1140, dy, t["fg50"], extra=da % 3)
    # imports may only flow one way: the arrows redraw in that order
    motion(doc, "@keyframes da{0%,5%{stroke-dasharray:1;stroke-dashoffset:1}"
                "13%{stroke-dasharray:1;stroke-dashoffset:0}13.1%,100%{stroke-dasharray:none}}"
                ".da{animation:da 8s cubic-bezier(.4,0,.2,1) infinite both}"
                ".d1{animation-delay:.4s}.d2{animation-delay:.8s}.d3{animation-delay:1.2s}")
    doc.text("×", 880, dy + 5, 12, t["fg72"], weight=1.4)
    doc.text("DEPENDENCY DIRECTION · ENFORCED IN CI", 560, 408, 9, t["fg50"])
    doc.text("APPLICATION × INFRASTRUCTURE: NEITHER MAY IMPORT THE OTHER", 560, 428, 9, t["fg50"])
    return doc.svg()


# ----------------------------------------------------------- PL. IV  HELIOS
def helios(t):
    H = 470
    doc = Doc(t, H, "HELIOS, solar energy intelligence",
              "Plate IV. The title HELIOS, drawn as exact construction geometry: public code, "
              "still in development. A schematic day of solar irradiance: a clear-sky curve, a dashed modelled "
              "forecast, a hatched band for the calibrated prediction interval, and observed "
              "points. Facts: physics plus machine learning, XGBoost with hold-out R-squared 0.856, "
              "calibrated prediction intervals.")
    frame(doc, "PL. IV", "HELIOS — SOLAR ENERGY INTELLIGENCE", "IN DEVELOPMENT · PUBLIC")
    word(doc, "HELIOS", M, 214, 96, "design", weight=2.6)
    doc.text("ARRANGED: PUBLIC CODE, UNFINISHED", M, 256, 9, t["fg50"])
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
            '<path class="fc" d="M%s" stroke="%s" stroke-width="2" stroke-dasharray="7 5"/>'
            % (pts(fc), t["fg"]))
    rng = random.Random(7)
    # observations arrive through the day, in the order they are made
    for i in range(27):
        h = 6.6 + i * 0.42
        v = min(clear(h), max(0.0, fc(h) + rng.gauss(0, band(h) * 0.5)))
        doc.add('<path class="ob" style="animation-delay:%.2fs" d="M%s %sh0" stroke="%s" '
                'stroke-width="4.6"/>' % (0.4 + i * 0.3, num(hx(h)), num(hy(v)), t["fg72"]))
    motion(doc, SHIMMER + ".sh.fn{animation:shn 3.4s ease-in-out infinite alternate}"
                ".sh.fl{animation:shl 4.8s ease-in-out infinite alternate}"
                "@keyframes fc{to{stroke-dashoffset:-24}}.fc{animation:fc 2.4s linear infinite}"
                "@keyframes ob{0%{opacity:0}3%,84%{opacity:1}92%,100%{opacity:0}}"
                ".ob{animation:ob 14s ease infinite both}")
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


# ---------------------------------------------------------- PL. V  VIGIL-88
def vigil(t):
    H = 470
    doc = Doc(t, H, "VIGIL-88, incident detection that reasons across time",
              "Plate V. The title VIGIL-88, drawn as exact construction geometry: public code, "
              "a P0 foundation, nothing detected yet. Three lanes along one time axis. Capture: "
              "frames arrive one after another, each a solid mark. Detector: a null detector "
              "answers every frame with an empty ring. Evidence: a dashed line toward a candidate "
              "event and an incident, drawn dashed because neither exists yet. An ember marks the "
              "latest frame. A frame is evidence, not a verdict.")
    frame(doc, "PL. V", "VIGIL-88 — INCIDENT DETECTION ACROSS TIME", "P0 FOUNDATION · PUBLIC")
    word(doc, "VIGIL-88", M, 214, 70, "design", weight=2.2)
    doc.text("ARRANGED: PUBLIC CODE, UNFINISHED", M, 256, 9, t["fg50"])
    doc.text("P0 FOUNDATION BUILT", M, 312, 11, t["fg72"])
    doc.text("NOTHING IS DETECTED YET", M, 336, 11, t["fg72"])
    doc.text("TEN ARCHITECTURE DOCUMENTS", M, 360, 11, t["fg72"])
    doc.text("PYTHON · PYDANTIC · OPENCV", M, 404, 10, t["fg50"])
    doc.text("UV · MYPY · IMPORT-LINTER", M, 424, 10, t["fg50"])

    # one time axis, three lanes: what arrives, what answers it, what is not built yet
    x0, x1 = 560, R - 20
    n = 28
    xn = x0 + 0.66 * (x1 - x0)                       # "now": the latest frame
    xs = [x0 + i * (xn - x0) / (n - 1) for i in range(n)]
    ya, yb, yc = 176, 246, 348

    doc.text("CAPTURE · TIMESTAMPED FRAMES", x0, 128, 9, t["fg50"])
    for i, x in enumerate(xs):
        doc.add('<path class="vt" style="animation-delay:%.2fs" d="M%s %sV%s" stroke="%s" '
                'stroke-width="2.2" stroke-linecap="butt"/>'
                % (0.3 + i * 0.3, num(x), ya, ya - 26, t["fg"]))
    doc.add(hline(x0, xn, ya + 6, t["fg34"]))

    doc.text("NULL DETECTOR · VALID, EMPTY OUTPUT", x0, 216, 9, t["fg50"])
    for i, x in enumerate(xs):
        doc.add('<circle class="vn" style="animation-delay:%.2fs" cx="%s" cy="%s" r="3.2" stroke="%s"/>'
                % (0.45 + i * 0.3, num(x), yb, t["fg50"]))

    doc.text("EVIDENCE → CANDIDATE EVENT → INCIDENT", x0, 296, 9, t["fg50"])
    doc.add('<path class="vf" d="M%s %sH%s" stroke="%s" stroke-width="1.4" stroke-dasharray="4 6"/>'
            % (num(x0), yc, num(x1), t["fg34"]))
    cand = x0 + 0.72 * (x1 - x0)
    for x, name, above in ((cand, "CANDIDATE EVENT", True), (x1, "INCIDENT", False)):
        doc.add('<rect x="%s" y="%s" width="10" height="10" fill="%s" stroke="%s" stroke-dasharray="2 2"/>'
                % (num(x - 5), yc - 5, t["bg"], t["fg50"]))
        doc.text(name, x if above else R, yc - 20 if above else yc + 32, 9, t["fg50"],
                 anchor="middle" if above else "end")
    doc.add(hline(cand - 6, x1 + 6, yc + 50, t["fg20"]))
    doc.text("NOT BUILT YET", (cand + x1) / 2, yc + 66, 9, t["fg50"], anchor="middle")

    # the one curious thing: the latest frame, and what a frame is
    ember(doc, xn, ya - 13, 4.5, 11)
    doc.text("A FRAME IS EVIDENCE,", xn + 22, ya - 12, 9, t["fg72"])
    doc.text("NOT A VERDICT.", xn + 22, ya + 4, 9, t["fg72"])
    doc.text("NOW", xn, 128, 8, t["fg72"], anchor="middle")
    doc.add(vline(xn, 134, 142, t["fg50"]))

    # frames arrive in order and each is answered with an empty ring; the dashed
    # line flows but nothing in it ever accumulates, because nothing is detected
    motion(doc, "@keyframes vt{0%{opacity:0}3%,84%{opacity:1}92%,100%{opacity:0}}"
                ".vt{animation:vt 12s ease infinite both}"
                "@keyframes vn{0%{opacity:0}3%,84%{opacity:1}92%,100%{opacity:0}}"
                ".vn{animation:vn 12s ease infinite both}"
                "@keyframes vf{to{stroke-dashoffset:-20}}.vf{animation:vf 2.4s linear infinite}")
    return doc.svg()


# ----------------------------------------------------------- PL. VI  NOT YET
OPEN = [("SPECTRA", "MULTIMODAL AI / COMPUTER VISION"),
        ("SYNCHRO", "DISTRIBUTED SYSTEMS / REAL-TIME"),
        ("AETHER", "CREATIVE COMPUTING / WEBGL")]


def not_yet(t):
    H = 470
    doc = Doc(t, H, "Not yet: SPECTRA, SYNCHRO, AETHER",
              "Plate VI. Three names drawn only as sketches, because nothing public exists for "
              "them yet: SPECTRA, multimodal AI and computer vision; SYNCHRO, distributed systems "
              "and real-time; AETHER, creative computing and WebGL. Each has a dashed mark of its "
              "question. There is no ember and no ground: nothing here is lit, or printed, yet.",
              ground=False)
    frame(doc, "PL. VI", "NOT YET", "NOTHING RESOLVES PAST THE EVIDENCE FOR IT")
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
                arrow(doc, x + 50, yy, lx - 18, yy, c, 1, 5, "3 5", extra=' class="mv"')
            doc.add(vline(lx, my - 58, my + 58, t["fg50"], 1, dash))
        elif name == "SYNCHRO":    # three clocks, never quite in phase
            lx = x + 250
            cid = doc.nid("k")
            doc.defs.append('<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="120"/></clipPath>'
                            % (cid, num(x - 1), num(my - 60), num(lx - 12 - x)))
            for j, off in enumerate((0, 7, 15)):
                yy = my - 36 + j * 36
                doc.add(hline(x, lx - 12, yy, c, 1, dash))
                # each clock runs at its own rate, so they never come into phase
                doc.add('<g clip-path="url(#%s)"><path class="ck ck%d" d="%s" stroke="%s" '
                        'stroke-width="1.4"/></g>' % (cid, j, "".join(
                            "M%s %sv-10" % (num(x + off + q * 30), num(yy + 5))
                            for q in range(-1, int((lx - 24 - x - off) / 30) + 1)), t["fg50"]))
            doc.add(vline(lx, my - 58, my + 58, t["fg50"], 1, dash))
            doc.text("?", lx + 12, my + 6, 16, t["fg50"], weight=1.4)
        else:                      # a sphere that is still only its construction
            cx, r = x + 110, 56
            doc.add('<circle cx="%s" cy="%s" r="%s" stroke="%s"%s/>' % (num(cx), my, r, c, dash))
            for n, q in enumerate((0.35, 0.72)):
                doc.add('<ellipse class="mer" style="transform-origin:%spx %spx;animation-delay:-%ss" '
                        'cx="%s" cy="%s" rx="%s" ry="%s" stroke="%s"%s/>'
                        % (num(cx), my, 3.5 * n + 1, num(cx), my, num(r * q), r, c, dash),
                        '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" stroke="%s"%s/>'
                        % (num(cx), my, r, num(r * q), c, dash))
    doc.text("EVERY NAME ON THESE PLATES IS DRAWN ONLY AS FAR AS ITS EVIDENCE GOES", M, H - 34, 9,
             t["fg50"])
    motion(doc, "@keyframes mv{to{stroke-dashoffset:-16}}.mv{animation:mv 1.4s linear infinite}"
                "@keyframes ck{to{transform:translateX(30px)}}.ck{animation:ck 3s linear infinite}"
                ".ck1{animation-duration:3.35s}.ck2{animation-duration:3.8s}"
                "@keyframes mer{0%{transform:scaleX(1)}50%{transform:scaleX(-1)}100%{transform:scaleX(1)}}"
                ".mer{transform-box:view-box;animation:mer 7s linear infinite}")
    return doc.svg()


# ------------------------------------------------------------- PL. VII  card
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
    ("VIGIL-88", {"PYTHON"}),
    ("THIS PROFILE", {"PYTHON", "SVG", "GH ACTIONS"}),
    ("GRAVITY PLAYGROUND", {"JAVASCRIPT", "HTML + CSS"}),
    ("TRAVELEASE", {"JAVASCRIPT", "HTML + CSS"}),
    ("PETPONKS", {"FIGMA", "FRAMER"}),
    ("SPECTRA", set()), ("SYNCHRO", set()), ("AETHER", set()),
]


def card(t):
    H = 684
    doc = Doc(t, H, "The stack, as a punched card",
              "Plate VII. A punched card: one row per work, one column per tool, grouped by the "
              "five verbs. A hole means the tool is in that work. " + " ".join(
                  "%s: %s." % (w.title(), ", ".join(sorted(s)) if s else "no holes yet")
                  for w, s in WORKS))
    frame(doc, "PL. VII", "THE STACK, PUNCHED", "A HOLE MEANS THE TOOL IS IN THE WORK")
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
    row_y = [rows_y0 + r * rh + rh / 2 + (30 if not used else 0) for r, (_, used) in enumerate(WORKS)]
    y_top, y_bot = row_y[0], row_y[-1]
    halos = []
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
            ring = "".join("M%s %sh%sv%sh-%sz" % (num(x - hole_w / 2 - 3), num(y - hole_h / 2 - 3),
                                                   hole_w + 6, hole_h + 6, hole_w + 6)
                           for x, (_, _, tool) in zip(colx, cols) if tool in used)
            # the moment the reader passes this row, as a share of the 9 s cycle
            at = 9 * (0.04 + 0.62 * (y - y_top) / (y_bot - y_top))
            halos.append('<path class="hl" style="animation-delay:%.2fs" d="%s" stroke="%s"/>'
                         % (at, ring, t["fg"]))
    doc.add(*halos)
    doc.add('<path class="scn" d="M%s %sH%s" stroke="%s" stroke-width="1.5"/>'
            % (num(cx0 + 16), num(y_top), num(cx1 - 10), t["fg50"]))
    motion(doc, "@keyframes scn{0%%{opacity:0;transform:translateY(0)}4%%{opacity:1;transform:translateY(0)}"
                "66%%{opacity:1;transform:translateY(%spx)}72%%,100%%{opacity:0;transform:translateY(%spx)}}"
                ".scn{opacity:0;animation:scn 9s linear infinite}"
                "@keyframes hl{0%%{opacity:0}1.5%%{opacity:1}10%%,100%%{opacity:0}}"
                ".hl{opacity:0;animation:hl 9s ease-out infinite both}"
                % (num(y_bot - y_top), num(y_bot - y_top)))
    # the corner cut says which way up the card goes; it is the only warm mark here
    doc.add('<path class="er" d="M%s %sL%s %s" stroke="%s" stroke-width="2"/>'
            % (num(cx0), num(cy0 + 26), num(cx0 + 26), num(cy0), t["ember"]))
    motion(doc, EMBER)
    doc.text("WORKS × TOOLS", cx0 + 22, cy1 - 14, 8, t["fg50"])
    doc.text("SIDDHUPERURI · 2026", cx1 - 16, cy1 - 14, 8, t["fg50"], anchor="end")
    return doc.svg()


# ------------------------------------------------------------ PL. VIII trace
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
              "Plate VIII. Every day of the last year as one mark on a line, from %s to %s. "
              "Days with public contributions rise from the line. %d contributions on %d days."
              % (fmt(days[0][0]), fmt(days[-1][0]), total, active))
    frame(doc, "PL. VIII", "TRACE — PUBLIC CONTRIBUTIONS, LAST 52 WEEKS",
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
    # a curtain of ground with a pen at its edge draws back across the year, then rests
    cw = x1 + 32 - (x0 - 6)
    doc.add('<g class="cur"><rect x="%s" y="%s" width="%s" height="162" fill="%s"/>%s</g>'
            % (num(x0 - 6), base - 154, num(cw), t["bg"], vline(x0 - 6, base - 154, base + 8, t["fg50"])))
    motion(doc, "@keyframes cur{0%%{transform:translateX(0)}62%%,100%%{transform:translateX(%spx)}}"
                ".cur{transform:translateX(%spx);animation:cur 12s cubic-bezier(.3,0,.7,1) infinite both}"
                % (num(cw + 120), num(cw + 120)))
    doc.text("TODAY", x1 + 16, base + 34, 8, t["fg72"], anchor="middle")
    doc.text("%d CONTRIBUTIONS" % total, M, 128, 20, t["fg"], weight=1.7)
    doc.text("ON %d DAYS OF %d" % (active, len(days)), M, 156, 11, t["fg72"])
    doc.text("A MARK FOR EVERY DAY. THE QUIET ONES STAY ON THE LINE.", M, H - 34, 9, t["fg50"])
    return doc.svg()


# ------------------------------------------------------------ PL. IX  end
SENTENCE = ["JACK OF ALL, MASTER OF NONE,", "BUT OFTEN TIMES BETTER", "THAN MASTER OF ONE."]


def end(t):
    H = 470
    doc = Doc(t, H, "Jack of all, master of none, but often times better than master of one",
              "Plate IX, the last. The sentence 'Jack of all, master of none, but often times "
              "better than master of one', left as a sketch: it never reaches the last stage. "
              "An ember waits below it. The wish is at the bottom of the well.")
    frame(doc, "PL. IX", "THE EDGE", "END OF PLATES")
    C = 40
    doc.add('<g class="sw">')
    for i, ln in enumerate(SENTENCE):
        w = S.text_width(ln, 0.3) * C
        word(doc, ln, (W - w) / 2, 168 + i * 74, C, "sketch", seed=300 + i * 40, weight=1.5, passes=2,
             cls="rd l%d" % i)
    doc.add("</g>")
    ember(doc, W / 2, 360, 5, 12)
    doc.text("THE WISH IS AT THE BOTTOM OF THE WELL", W / 2, 398, 9, t["fg50"], anchor="middle")
    doc.add(hline(M, R, H - 58, t["fg20"]))
    doc.text("SIDDHARTHA / 2026", M, H - 30, 11, t["fg72"])
    doc.text("SET IN ITS OWN ALPHABET · NO FONT FILES", R, H - 30, 11, t["fg50"], anchor="end")
    # the room breathes, very slowly
    motion(doc, "@keyframes sw{from{transform:translateX(-5px)}to{transform:translateX(5px)}}"
                ".sw{animation:sw 11s ease-in-out infinite alternate}" + REDRAW +
                ".rd{animation:rd 16s ease-in-out infinite both}.l1{animation-delay:.7s}"
                ".l2{animation-delay:1.4s}")
    return doc.svg()


# -------------------------------------------------------------------- labels
# The words between the plates, set in the same alphabet. Labels have no ground:
# they are printed on the page, not on a plate, and share the plates' 72 margin so
# plate and label sit on one grid. Each label's full wording is also its alt text.
LC = M + 360            # the label's text column


def wrap_caps(text, cap, width, track=0.32):
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if cur and S.text_width(trial, track) * cap > width:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def rich(doc, segs, x, y, cap, anchor="start", weight=None):
    """One line of type in several tones: [(text, colour[, class]), ...]."""
    gap = (S.G[" "]["w"] + 2 * 0.32) * cap        # a word space between segments
    widths = [S.text_width(sg[0]) * cap for sg in segs]
    total = sum(widths) + gap * (len(segs) - 1)
    x -= total / 2 if anchor == "middle" else 0
    for sg, w in zip(segs, widths):
        doc.text(sg[0], x, y, cap, sg[1], weight=weight, cls=sg[2] if len(sg) > 2 else "")
        x += w + gap


def text_arrow(doc, s, x, y, cap, color, weight=None, cls="lr"):
    """A run whose trailing arrow nudges toward where it points."""
    if s[-1] not in "→↓":
        return doc.text(s, x, y, cap, color, weight=weight, cls=cls)
    w = doc.text(s[:-1].rstrip(), x, y, cap, color, weight=weight, cls=cls)
    doc.add('<g class="%s">' % ("ndd" if s[-1] == "↓" else "nd"))
    doc.text(s[-1], x + w + (S.G[" "]["w"] + 0.64) * cap, y, cap, color, weight=weight, cls=cls)
    doc.add("</g>")
    motion(doc, NUDGE)
    return w


LABELS = {
    "artwork": dict(
        pl="PL. II", name="SIDDHARTHA", kind="INTERACTIVE ARTWORK", stage="2026 · MEASURED",
        body="AN ARTWORK ABOUT A PERSON, AND THE SOURCE OF EVERY DRAWING ON THIS PAGE. THE NAME "
             "IS FIVE SHEETS OF LIGHT AT FIVE DEPTHS; FROM EXACTLY ONE POINT THEY ADD UP TO A WORD. "
             "ONE CONTINUOUS WORLD IN FOUR PARTS, AND IT CAN BE PULLED OUT OF ITS OWN WINDOW.",
        rows=[("MADE WITH", "HTML, CSS, JAVASCRIPT · THREE.JS, VENDORED, FOR THREE MOMENTS"),
              ("WITHOUT", "A FRAMEWORK, A BUILD STEP, FONT FILES OR NETWORK REQUESTS"),
              ("SOURCE", "SIDDHUPERURI/MIRACLE →")]),
    "orbit": dict(
        pl="PL. III", name="ORBIT", kind="KNOWLEDGE AND DOCUMENT PLATFORM", stage="2026 · ARRANGED",
        body="UPLOAD DOCUMENTS INTO A WORKSPACE AND ASK QUESTIONS ANSWERED FROM THEIR CONTENTS, "
             "CITED TO THE EXACT PASSAGE. IDENTITY, WORKSPACES, UPLOAD, THE ASYNCHRONOUS PIPELINE, "
             "RETRIEVAL AND GROUNDED ANSWERING ARE IMPLEMENTED; IT IS NOT PRODUCTION-READY. A "
             "MODULAR MONOLITH WHOSE LAYERING FAILS THE BUILD IF IT IS BROKEN.",
        rows=[("MADE WITH", "PYTHON, FASTAPI, CELERY · NEXT.JS, REACT, TYPESCRIPT, TAILWIND"),
              ("STORES", "POSTGRESQL + PGVECTOR · REDIS · MINIO"),
              ("SHIPS WITH", "DOCKER · GITHUB ACTIONS · 24 DECISION RECORDS"),
              ("SOURCE", "SIDDHUPERURI/ORBIT →")]),
    "helios": dict(
        pl="PL. IV", name="HELIOS", kind="SOLAR ENERGY INTELLIGENCE", stage="2026 · ARRANGED",
        body="PHYSICS AND MACHINE LEARNING FOR SOLAR FORECASTING, WITH CALIBRATED PREDICTION "
             "INTERVALS: A FORECAST THAT SAYS HOW SURE IT IS. TWO INTERFACES OVER ONE ENGINE, A "
             "ONE-SECOND CALCULATOR AND A FOURTEEN-VIEW ANALYSIS CONSOLE.",
        rows=[("MODEL", "XGBOOST · HOLD-OUT R² 0.856"),
              ("MADE WITH", "PYTHON, FASTAPI, SCIKIT-LEARN · NEXT.JS"),
              ("THE CURVE", "A SCHEMATIC, NOT ITS DATA"),
              ("SOURCE", "SIDDHUPERURI/HELIOS →")]),
    "vigil-88": dict(
        pl="PL. V", name="VIGIL-88", kind="INCIDENT DETECTION ACROSS TIME", stage="2026 · ARRANGED",
        body="A COMPUTER-VISION PLATFORM THAT REASONS ACROSS TIME: A FRAME IS EVIDENCE, NOT A "
             "VERDICT. THE P0 FOUNDATION IS BUILT; NOTHING IS DETECTED YET, AND ITS README SAYS SO. "
             "LOCAL-FIRST, WITH NO FACIAL RECOGNITION OR IDENTITY PROFILING.",
        rows=[("MADE WITH", "PYTHON, PYDANTIC · OPENCV, FOR CAPTURE"),
              ("HOLDS", "LAYERED IMPORTS, A PURE DOMAIN LAYER AND ONE CLOCK MODULE, CHECKED BY MACHINE"),
              ("NOT YET", "DETECTION, TRACKING, EVENTS, INCIDENTS, ALERTS, A CONSOLE"),
              ("SOURCE", "SIDDHUPERURI/VIGIL-88 →")]),
    "not-yet": dict(
        pl="PL. VI", name="NOT YET", kind="SPECTRA · SYNCHRO · AETHER", stage="SKETCHED",
        body="NAMED, NOT BUILT, AND NOT YET PRINTED AS PLATES. EACH HOLDS A QUESTION INSTEAD OF "
             "A DESCRIPTION.",
        rows=[("SPECTRA", "WHAT DOES A MACHINE NOTICE, MISS OR MISTAKE WHEN IT LOOKS?"),
              ("SYNCHRO", "WHAT DO STATE, LATENCY AND COORDINATION FEEL LIKE WHEN SYSTEMS MOVE "
                          "TOGETHER?"),
              ("AETHER", "WHAT HAPPENS WHEN WEBGL, GENERATIVE SYSTEMS AND SPATIAL INTERFACES "
                         "BECOME AN ATMOSPHERE?")]),
    "card": dict(
        pl="PL. VII", name="THE STACK", kind="PUNCHED", stage="WORKS × TOOLS",
        body="ROWS ARE WORKS, COLUMNS ARE TOOLS, AND A HOLE IS ONLY PUNCHED WHERE THE WORK'S "
             "REPOSITORY OR RECORD SHOWS THE TOOL.",
        rows=[("ALSO IN HAND", "PHOTOSHOP, ILLUSTRATOR, LIGHTROOM, CANVA, PYTORCH, REACT THREE "
                               "FIBER, GSAP, JAVA, C. NO PUBLIC WORK TO SHOW FOR THEM YET."),
              ("EARLIER", "GRAVITY PLAYGROUND, A CUSTOM PHYSICS ENGINE · TRAVELEASE, A "
                          "LOCATION-BASED TREASURE HUNT · PETPONKS, IDENTITY AND WIREFRAMES")]),
    "trace": dict(
        pl="PL. VIII", name="TRACE", kind="LAST 52 WEEKS", stage="REDRAWN DAILY",
        body="REDRAWN EACH MORNING FROM THE GITHUB API BY A WORKFLOW IN THIS REPOSITORY, NOT BY "
             "A STATS SERVICE. THE NUMBERS ARE THE API'S, UNROUNDED.",
        rows=[("SOURCE", "GITHUB GRAPHQL API · CONTRIBUTION CALENDAR"),
              ("WORKFLOW", ".GITHUB/WORKFLOWS/TRACE.YML · 06:47 IST")]),
}


def label(t, key):
    d = LABELS[key]
    doc = Doc(t, 0, "%s: %s" % (d["name"].title(), d["kind"].lower()), d["body"].capitalize(),
              ground=False)
    doc.add(hline(M, R, 8, t["fg20"], extra=' class="ln" pathLength="1"'))
    doc.text(d["pl"], M, 40, 10, t["fg50"], cls="lr")
    ly = 72
    doc.text(d["name"], M, ly, 21, t["fg"], weight=2, cls="lr")
    ly += 28
    for ln in wrap_caps(d["kind"], 11, LC - M - 48):
        doc.text(ln, M, ly, 11, t["fg72"], cls="lr")
        ly += 19
    doc.text(d["stage"], M, ly + 6, 10, t["fg50"], cls="lr")
    ry = 72
    for ln in wrap_caps(d["body"], 15, R - LC):
        doc.text(ln, LC, ry, 15, t["fg72"], weight=1.45, cls="lr")
        ry += 27
    ry += 14
    kw = 150
    for k, v in d["rows"]:
        doc.text(k, LC, ry, 9, t["fg50"], cls="lr")
        for ln in wrap_caps(v, 11, R - LC - kw):
            text_arrow(doc, ln, LC + kw, ry, 11, t["fg72"])
            ry += 20
        ry += 6
    doc.h = int(max(ly + 6, ry - 6) + 22)
    # the label is set as the page arrives: its rule draws, its words appear
    motion(doc, DRAW + ".ln{animation:dw 1.2s cubic-bezier(.2,.7,.1,1) both}"
                ".lr{animation:fi 1s ease .25s both}")
    return doc.svg()


def statement(t):
    """The words under the hero, and a key to the stages the plates are drawn at."""
    fg, dim = t["fg"], t["fg50"]
    doc = Doc(t, 0, "Jai Sai Siddhartha Peruri",
              "Jai Sai Siddhartha Peruri, computer science, India. A hand sketches it. A model "
              "infers it. A grid computes it. A layout arranges it. An instrument measures it. "
              "From one place, they add up to a name. I study computer science and work in all "
              "five: drawing, models, code, interfaces, systems. Each name on the plates below is "
              "drawn only as far as its evidence goes: sketched, named with no code yet; inferred, "
              "built but not yet public; arranged, public but unfinished; measured, public and "
              "running.", ground=False)
    cx, y = W / 2, 34
    rich(doc, [("JAI SAI SIDDHARTHA PERURI", fg), ("·", dim), ("COMPUTER SCIENCE", t["fg72"]),
               ("·", dim), ("INDIA", t["fg72"])], cx, y, 12, "middle")
    y += 78
    for segs in ([("A HAND", dim), ("SKETCHES", fg, "v v0"), ("IT. A MODEL", dim),
                  ("INFERS", fg, "v v1"), ("IT. A GRID", dim), ("COMPUTES", fg, "v v2"), ("IT.", dim)],
                 [("A LAYOUT", dim), ("ARRANGES", fg, "v v3"), ("IT. AN INSTRUMENT", dim),
                  ("MEASURES", fg, "v v4"), ("IT.", dim)],
                 [("FROM ONE PLACE, THEY ADD UP TO A NAME.", fg)]):
        rich(doc, segs, cx, y, 17, "middle", weight=1.55)
        y += 36
    y += 30
    doc.text("I STUDY COMPUTER SCIENCE AND WORK IN ALL FIVE:", cx, y, 14, t["fg72"], anchor="middle")
    doc.text("DRAWING, MODELS, CODE, INTERFACES, SYSTEMS.", cx, y + 27, 14, t["fg72"],
             anchor="middle")
    y += 92
    doc.add(hline(cx - 150, cx + 150, y - 30, t["fg20"]))
    doc.text("EACH NAME ON THE PLATES BELOW IS DRAWN ONLY AS FAR AS ITS EVIDENCE GOES", cx, y, 10,
             dim, anchor="middle")
    y += 34
    key = [("sketch", "SKETCHED", "NAMED, NO CODE YET"), ("field", "INFERRED", "BUILT, NOT YET PUBLIC"),
           ("design", "ARRANGED", "PUBLIC, UNFINISHED"), ("measure", "MEASURED", "PUBLIC, AND IT RUNS")]
    C, step = 34, 250
    for i, (stage, name, means) in enumerate(key):
        ix = cx + (i - 1.5) * step
        gx = ix - 76
        if stage == "sketch":
            stage_sketch(doc, "A", gx, y + C, C, 5, weight=1.2, wobble=2.2, cls="rd")
        elif stage == "field":
            stage_field(doc, "A", gx, y + C, C, 6, density=1.5, cls="sh")
        elif stage == "design":
            stage_design(doc, "A", gx, y + C, C, weight=1.4, cls="kd")
        else:
            stage_measure(doc, "A", gx, y + C, C, 0.13 * C)
        doc.text(name, ix - 24, y + 14, 11, fg)
        doc.text(means, ix - 24, y + 33, 9, dim)
    doc.h = int(y + C + 26)
    motion(doc, "@keyframes vv{0%%,9%%,100%%{stroke:%s}3.5%%{stroke:%s}}"
                ".v{animation:vv 10s ease-in-out infinite}.v1{animation-delay:1.1s}"
                ".v2{animation-delay:2.2s}.v3{animation-delay:3.3s}.v4{animation-delay:4.4s}"
                % (fg, t["ember"]) + REDRAW + SHIMMER +
                ".rd{animation:rd 12s ease-in-out infinite both}"
                ".sh.fn{animation:shn 3.4s ease-in-out infinite alternate}"
                ".sh.fl{animation:shl 4.8s ease-in-out infinite alternate}"
                ".kd{animation:rd 12s ease-in-out 1.2s infinite both}.kd.c{animation:none}")
    return doc.svg()


def end_label(t):
    doc = Doc(t, 0, "Colophon",
              "The last sentence of SIDDHARTHA, left as a sketch: nothing measures it. There is "
              "one more, at the bottom of the well. Plates drawn by tools/build_assets.py in the "
              "artwork's own stroke alphabet. No font files, no scripts, no third-party services; "
              "light and dark printed from one source.", ground=False)
    cx = W / 2
    doc.text("THE LAST SENTENCE OF SIDDHARTHA, LEFT AS A SKETCH: NOTHING MEASURES IT.", cx, 40, 13,
             t["fg72"], anchor="middle", cls="lr")
    doc.text("THERE IS ONE MORE, AT THE BOTTOM OF THE WELL.", cx, 64, 13, t["fg72"], anchor="middle",
             cls="lr")
    doc.add(hline(cx - 60, cx + 60, 100, t["fg20"]))
    doc.text("PLATES DRAWN BY TOOLS/BUILD_ASSETS.PY IN THE ARTWORK'S OWN STROKE ALPHABET", cx, 132, 9,
             t["fg50"], anchor="middle", cls="lr")
    doc.text("NO FONT FILES · NO SCRIPTS · NO THIRD-PARTY SERVICES · LIGHT AND DARK FROM ONE SOURCE",
             cx, 152, 9, t["fg50"], anchor="middle", cls="lr")
    doc.h = 176
    motion(doc, DRAW + ".lr{animation:fi 1.2s ease .2s both}")
    return doc.svg()


LINKS = {"artwork": ("THE ARTWORK →", "The artwork"), "linkedin": ("LINKEDIN →", "LinkedIn"),
         "portfolio": ("PORTFOLIO →", "Portfolio"), "behance": ("BEHANCE →", "Behance"), "card-text": ("READ THE CARD AS TEXT ↓", "Read the card as text")}


def link(t, key):
    (text, title), cap = LINKS[key], 12
    w = S.text_width(text) * cap
    doc = Doc(t, 38, title, "Link: " + title, w=int(w + 12), ground=False)
    text_arrow(doc, text, 5, 20, cap, t["fg"], weight=1.45, cls="")
    doc.add(hline(5, 5 + w, 28, t["fg34"]))
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
              ("vigil-88", vigil), ("not-yet", not_yet), ("card", card), ("trace", lambda t: trace(t, data)),
              ("end", end)]
    plates += [("labels/" + k, lambda t, k=k: label(t, k)) for k in LABELS]
    plates += [("labels/statement", statement), ("labels/end", end_label)]
    plates += [("labels/link-" + k, lambda t, k=k: link(t, k)) for k in LINKS]
    only = [a for a in argv if not a.startswith("--")]
    total = 0
    os.makedirs(os.path.join(OUT, "labels"), exist_ok=True)
    for t in THEMES:
        for name, fn in plates:
            if only and name not in only and name.split("/")[0] not in only:
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
