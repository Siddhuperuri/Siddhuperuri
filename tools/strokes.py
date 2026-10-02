"""The stroke alphabet of SIDDHARTHA, ported from Siddhuperuri/miracle (js/glyphs.js).

Every letter is a handful of strokes on a cap-height-1 grid, y up. Arcs are real
elliptical arcs; nothing here is a font file. Free stroke ends can carry a short
perpendicular survey tick, so the alphabet reads as an engineer's drawing of
letters. The artwork builds its world from these strokes, and every plate in this
profile is drawn with the same ones.

Additions to the artwork's set (x * ( ) superscript-2, em dash and arrows) follow
its rules: straight strokes and true arcs only.
"""
import math

RAD = math.pi / 180
TICK = 0.1


# ------------------------------------------------------------------ stroke DSL
def L(*v):
    """Polyline from a flat x, y list."""
    return ("L", [(v[i], v[i + 1]) for i in range(0, len(v), 2)])


def A(cx, cy, rx, ry, a0, a1):
    """Elliptical arc in degrees, counter-clockwise positive (y up)."""
    return ("A", cx, cy, rx, ry, a0, a1)


def P(*pieces):
    """Several pieces drawn as one continuous stroke."""
    return ("P", list(pieces))


G = {}


def _def(ch, w, strokes, anchor=None):
    G[ch] = dict(w=w, s=[s[1] if s[0] == "P" else [s] for s in strokes], anchor=anchor)


# capitals
_def("A", 0.84, [L(0, 0, 0.42, 1, 0.84, 0), L(0.134, 0.32, 0.706, 0.32)], (0.42, 0.51))
_def("B", 0.62, [L(0, 0, 0, 1),
                 P(L(0, 1, 0.3, 1), A(0.3, 0.75, 0.28, 0.25, 90, -90), L(0.3, 0.5, 0, 0.5)),
                 P(L(0, 0.5, 0.34, 0.5), A(0.34, 0.25, 0.28, 0.25, 90, -90), L(0.34, 0, 0, 0))])
_def("C", 0.82, [A(0.46, 0.5, 0.46, 0.5, 40, 320)])
_def("D", 0.82, [P(L(0, 0, 0, 1, 0.38, 1), A(0.38, 0.5, 0.44, 0.5, 90, -90), L(0.38, 0, 0, 0))])
_def("E", 0.58, [L(0.58, 1, 0, 1, 0, 0, 0.58, 0), L(0, 0.5, 0.48, 0.5)])
_def("F", 0.58, [L(0.58, 1, 0, 1, 0, 0), L(0, 0.55, 0.48, 0.55)])
_def("G", 0.92, [P(A(0.46, 0.5, 0.46, 0.5, 40, 360), L(0.5, 0.5))])
_def("H", 0.72, [L(0, 0, 0, 1), L(0.72, 0, 0.72, 1), L(0, 0.5, 0.72, 0.5)])
_def("I", 0.4, [L(0.2, 0, 0.2, 1), L(0, 1, 0.4, 1), L(0, 0, 0.4, 0)])
_def("J", 0.5, [P(L(0.5, 1, 0.5, 0.32), A(0.25, 0.32, 0.25, 0.32, 0, -180))])
_def("K", 0.68, [L(0, 0, 0, 1), L(0.64, 1, 0, 0.4), L(0.18, 0.58, 0.68, 0)])
_def("L", 0.54, [L(0, 1, 0, 0, 0.54, 0)])
_def("M", 0.8, [L(0, 0, 0, 1, 0.4, 0.36, 0.8, 1, 0.8, 0)])
_def("N", 0.7, [L(0, 0, 0, 1, 0.7, 0, 0.7, 1)])
_def("O", 0.92, [A(0.46, 0.5, 0.46, 0.5, 90, 450)])
_def("P", 0.6, [L(0, 0, 0, 1),
                P(L(0, 1, 0.3, 1), A(0.3, 0.72, 0.3, 0.28, 90, -90), L(0.3, 0.44, 0, 0.44))])
_def("Q", 0.92, [A(0.46, 0.5, 0.46, 0.5, 90, 450), L(0.56, 0.22, 0.9, -0.1)])
_def("R", 0.72, [L(0, 0, 0, 1),
                 P(L(0, 1, 0.36, 1), A(0.36, 0.75, 0.3, 0.25, 90, -90), L(0.36, 0.5, 0, 0.5)),
                 L(0.3, 0.5, 0.72, 0)])
_def("S", 0.6, [P(A(0.3, 0.75, 0.3, 0.25, 25, 270), A(0.3, 0.25, 0.3, 0.25, 90, -155))])
_def("T", 0.8, [L(0, 1, 0.8, 1), L(0.4, 1, 0.4, 0)])
_def("U", 0.72, [P(L(0, 1, 0, 0.42), A(0.36, 0.42, 0.36, 0.42, 180, 360), L(0.72, 0.42, 0.72, 1))])
_def("V", 0.8, [L(0, 1, 0.4, 0, 0.8, 1)])
_def("W", 1.0, [L(0, 1, 0.22, 0, 0.5, 0.62, 0.78, 0, 1, 1)])
_def("X", 0.7, [L(0, 0, 0.7, 1), L(0, 1, 0.7, 0)])
_def("Y", 0.72, [L(0, 1, 0.36, 0.5, 0.72, 1), L(0.36, 0.5, 0.36, 0)])
_def("Z", 0.66, [L(0, 1, 0.66, 1, 0, 0, 0.66, 0)])

# numerals: chamfered, instrument-like
_def("0", 0.5, [L(0.1, 0, 0.4, 0, 0.5, 0.1, 0.5, 0.9, 0.4, 1, 0.1, 1, 0, 0.9, 0, 0.1, 0.1, 0)])
_def("1", 0.4, [L(0.06, 0.78, 0.28, 1, 0.28, 0)])
_def("2", 0.5, [L(0, 0.9, 0.1, 1, 0.4, 1, 0.5, 0.9, 0.5, 0.62, 0, 0, 0.5, 0)])
_def("3", 0.5, [L(0, 0.9, 0.1, 1, 0.4, 1, 0.5, 0.9, 0.5, 0.6, 0.4, 0.5, 0.16, 0.5),
                L(0.4, 0.5, 0.5, 0.4, 0.5, 0.1, 0.4, 0, 0.1, 0, 0, 0.1)])
_def("4", 0.5, [L(0.4, 0, 0.4, 1, 0, 0.34, 0.5, 0.34)])
_def("5", 0.5, [L(0.5, 1, 0.04, 1, 0, 0.56, 0.4, 0.6, 0.5, 0.5, 0.5, 0.1, 0.4, 0, 0.1, 0, 0, 0.1)])
_def("6", 0.5, [L(0.46, 1, 0.1, 1, 0, 0.9, 0, 0.1, 0.1, 0, 0.4, 0, 0.5, 0.1, 0.5, 0.44, 0.4, 0.54,
                  0, 0.54)])
_def("7", 0.5, [L(0, 1, 0.5, 1, 0.16, 0)])
_def("8", 0.5, [L(0.1, 0.5, 0, 0.6, 0, 0.9, 0.1, 1, 0.4, 1, 0.5, 0.9, 0.5, 0.6, 0.4, 0.5, 0.1, 0.5,
                  0, 0.4, 0, 0.1, 0.1, 0, 0.4, 0, 0.5, 0.1, 0.5, 0.4, 0.4, 0.5)])
_def("9", 0.5, [L(0.04, 0, 0.4, 0, 0.5, 0.1, 0.5, 0.9, 0.4, 1, 0.1, 1, 0, 0.9, 0, 0.56, 0.1, 0.46,
                  0.5, 0.46)])

# marks
_def(".", 0.12, [L(0.06, 0, 0.06, 0.09)])
_def(",", 0.12, [L(0.08, 0.09, 0.04, -0.08)])
_def("-", 0.42, [L(0, 0.5, 0.42, 0.5)])
_def(":", 0.12, [L(0.06, 0.06, 0.06, 0.15), L(0.06, 0.6, 0.06, 0.69)])
_def("/", 0.42, [L(0, 0, 0.42, 1)])
_def("+", 0.5, [L(0, 0.5, 0.5, 0.5), L(0.25, 0.25, 0.25, 0.75)])
_def("·", 0.12, [L(0.06, 0.5, 0.06, 0.58)])
_def("→", 0.9, [L(0, 0.5, 0.9, 0.5), L(0.7, 0.72, 0.9, 0.5, 0.7, 0.28)])
_def("?", 0.5, [P(A(0.25, 0.74, 0.25, 0.26, 170, -70), L(0.25, 0.44, 0.25, 0.3)),
                L(0.25, 0, 0.25, 0.09)])
_def("!", 0.12, [L(0.06, 1, 0.06, 0.3), L(0.06, 0, 0.06, 0.09)])
_def("'", 0.12, [L(0.06, 1, 0.06, 0.72)])
_def(";", 0.12, [L(0.06, 0.6, 0.06, 0.69), L(0.08, 0.09, 0.04, -0.08)])
_def(" ", 0.5, [])

# additions for the plates
_def("×", 0.46, [L(0.02, 0.24, 0.44, 0.66), L(0.02, 0.66, 0.44, 0.24)])
_def("*", 0.4, [L(0.2, 0.62, 0.2, 0.98), L(0.044, 0.71, 0.356, 0.89), L(0.044, 0.89, 0.356, 0.71)])
_def("(", 0.3, [A(0.34, 0.5, 0.3, 0.62, 125, 235)])
_def(")", 0.3, [A(-0.04, 0.5, 0.3, 0.62, 55, -55)])
_def("²", 0.28, [L(0, 0.93, 0.05, 1, 0.21, 1, 0.26, 0.93, 0.26, 0.8, 0, 0.5, 0.27, 0.5)])
_def("—", 0.9, [L(0, 0.5, 0.9, 0.5)])
_def("–", 0.56, [L(0, 0.5, 0.56, 0.5)])
_def("←", 0.9, [L(0.9, 0.5, 0, 0.5), L(0.2, 0.72, 0, 0.5, 0.2, 0.28)])
_def("↑", 0.5, [L(0.25, 0, 0.25, 0.9), L(0.03, 0.68, 0.25, 0.9, 0.47, 0.68)])
_def("↓", 0.5, [L(0.25, 0.9, 0.25, 0), L(0.03, 0.22, 0.25, 0, 0.47, 0.22)])
_def("=", 0.42, [L(0, 0.36, 0.42, 0.36), L(0, 0.64, 0.42, 0.64)])
_def("_", 0.5, [L(0, -0.08, 0.5, -0.08)])


# ------------------------------------------------------------------- geometry
def arc_point(cx, cy, rx, ry, a):
    return (cx + rx * math.cos(a * RAD), cy + ry * math.sin(a * RAD))


def piece_points(pc):
    if pc[0] == "L":
        return list(pc[1])
    _, cx, cy, rx, ry, a0, a1 = pc
    n = max(4, math.ceil(abs(a1 - a0) / 6))
    return [arc_point(cx, cy, rx, ry, a0 + (a1 - a0) * i / n) for i in range(n + 1)]


def _same(p, q, eps=1e-6):
    return abs(p[0] - q[0]) < eps and abs(p[1] - q[1]) < eps


def stroke_points(stroke):
    """A stroke (list of pieces) as one polyline, duplicate joints dropped."""
    out = []
    for pc in stroke:
        for p in piece_points(pc):
            if out and _same(out[-1], p):
                continue
            out.append(p)
    return out


def dist_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2 if l2 else 0.0
    t = max(0.0, min(1.0, t))
    qx, qy = a[0] + dx * t - p[0], a[1] + dy * t - p[1]
    return math.hypot(qx, qy)


def free_ends(strokes):
    """{(stroke index, 0 = start | 1 = end)} for every end that touches no other stroke."""
    polys = [stroke_points(s) for s in strokes]
    out = set()
    for si, pts in enumerate(polys):
        n = len(pts)
        if n < 2 or _same(pts[0], pts[-1]):
            continue
        for end in (0, 1):
            e, adj = (pts[-1], n - 2) if end else (pts[0], 0)
            joined = any(dist_seg(e, q[k], q[k + 1]) < 0.012
                         for sj, q in enumerate(polys) for k in range(len(q) - 1)
                         if not (sj == si and k == adj))
            if not joined:
                out.add((si, end))
    return out


def ticks_for(strokes):
    """Survey ticks on every free stroke end, perpendicular to the stroke, axis-aligned."""
    polys = [stroke_points(s) for s in strokes]
    out = []
    for si, end in sorted(free_ends(strokes)):
        pts = polys[si]
        e, nb = (pts[-1], pts[-2]) if end else (pts[0], pts[1])
        tx, ty = e[0] - nb[0], e[1] - nb[1]
        dx, dy = (1, 0) if abs(ty) >= abs(tx) else (0, 1)
        out.append(((e[0] - dx * TICK / 2, e[1] - dy * TICK / 2),
                    (e[0] + dx * TICK / 2, e[1] + dy * TICK / 2)))
    return out


def resample(pts, ds):
    """Polyline resampled to ~uniform spacing ds; returns (x, y, tangent_x, tangent_y)."""
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    total = cum[-1]
    if total < 1e-9:
        return [(pts[0][0], pts[0][1], 1.0, 0.0)]
    count = max(1, round(total / ds))
    out, j = [], 1
    for i in range(count + 1):
        d = total * i / count
        while j < len(pts) - 1 and cum[j] < d:
            j += 1
        seg = (cum[j] - cum[j - 1]) or 1.0
        u = (d - cum[j - 1]) / seg
        ax, ay = pts[j - 1]
        bx, by = pts[j]
        tl = math.hypot(bx - ax, by - ay) or 1.0
        out.append((ax + (bx - ax) * u, ay + (by - ay) * u, (bx - ax) / tl, (by - ay) / tl))
    return out


def length(pts):
    return sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
               for i in range(1, len(pts)))


# ----------------------------------------------------------------- SVG output
def num(v):
    s = "%.1f" % v
    s = s.rstrip("0").rstrip(".") if "." in s else s
    return "0" if s in ("-0", "") else s


def stroke_d(stroke, ox, oy, s):
    """SVG path data for one stroke placed with its baseline origin at (ox, oy), cap height s.

    Arcs stay arcs: each is emitted as SVG elliptical-arc commands (split so no
    single command sweeps more than 120 degrees), which keeps the geometry exact.
    """
    X = lambda x: num(ox + x * s)
    Y = lambda y: num(oy - y * s)
    d, cur = [], None
    for pc in stroke:
        if pc[0] == "L":
            for p in pc[1]:
                if cur is None:
                    d.append("M%s %s" % (X(p[0]), Y(p[1])))
                elif not _same(cur, p):
                    d.append("L%s %s" % (X(p[0]), Y(p[1])))
                cur = p
            continue
        _, cx, cy, rx, ry, a0, a1 = pc
        p0 = arc_point(cx, cy, rx, ry, a0)
        if cur is None:
            d.append("M%s %s" % (X(p0[0]), Y(p0[1])))
        elif not _same(cur, p0):
            d.append("L%s %s" % (X(p0[0]), Y(p0[1])))
        n = max(1, math.ceil(abs(a1 - a0) / 120))
        sweep = 0 if a1 > a0 else 1          # y is flipped on screen
        for i in range(1, n + 1):
            p = arc_point(cx, cy, rx, ry, a0 + (a1 - a0) * i / n)
            d.append("A%s %s 0 0 %d %s %s" % (num(rx * s), num(ry * s), sweep, X(p[0]), Y(p[1])))
        cur = arc_point(cx, cy, rx, ry, a1)
    return "".join(d)


def glyph(ch):
    return G.get(ch.upper(), G[" "])


def text_layout(text, track=0.3):
    """[(glyph, x)] on the cap-height-1 grid, and the total advance width."""
    x, out = 0.0, []
    for i, ch in enumerate(text):
        g = glyph(ch)
        out.append((g, x, ch.upper() if ch.upper() in G else " "))
        x += g["w"] + track
    return out, max(0.0, x - track) if text else 0.0


def text_width(text, track=0.3):
    return text_layout(text, track)[1]
