"""Build the profile's SVG asset system (light + dark).

Design system
-------------
Grid      1280 canvas, 72 margin, 12 columns
Type      Anton (display) / Inter (text), converted to outlines
Colour    ink + paper + a single accent; no gradients
Spacing   4 / 8 / 16 / 24 / 32 scale
"""
import os
import sys
import html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from typeset import Face

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
W, M = 1280, 72
CW = W - 2 * M
R = W - M

THEMES = {
    "dark": dict(paper="#08080A", panel="#0E0E11", rule="#232329", rule_soft="#161619",
                 ink="#F5F5F6", ink2="#9A9AA3", ink3="#5C5C65", accent="#FF4A1C"),
    "light": dict(paper="#FBFBF9", panel="#FFFFFF", rule="#DEDED8", rule_soft="#EDEDE8",
                  ink="#0A0A0B", ink2="#61616A", ink3="#9695A0", accent="#E03A0C"),
}

ANTON = Face("anton", key="a")
INTER = {w: Face("inter", w, key="i%d" % (w // 100)) for w in (400, 500, 600, 700)}

# Glyphs used by the document currently being built: every distinct letterform is
# defined once in <defs> and referenced with <use>, which keeps these files small
# even though all type is outlined.
POOL = {}


def pool_reset():
    POOL.clear()


def pool_defs():
    if not POOL:
        return ""
    return "<defs>%s</defs>" % "".join(
        '<path id="%s" d="%s"/>' % (gid, d) for gid, d in POOL.values())


# ---------------------------------------------------------------- primitives
def esc(s):
    return html.escape(s, quote=True)


def txt(face, s, x, y, size, fill, tracking=0.0, anchor="start"):
    runs, w = face.runs(s, size, tracking)
    if not runs:
        return "", w
    if anchor == "end":
        x -= w
    elif anchor == "middle":
        x -= w / 2
    uses = []
    for name, gx, gy in runs:
        key = (face.key, name)
        if key not in POOL:
            POOL[key] = ("%s%d" % (face.key, len(POOL)), face.glyph_d(name))
        gid = POOL[key][0]
        uses.append('<use href="#%s" x="%d"%s/>'
                    % (gid, gx, ' y="%d"' % gy if gy else ""))
    return ('<g transform="translate(%g,%g) scale(%s)" fill="%s">%s</g>'
            % (x, y, "%.6f" % (size / 1000.0), fill, "".join(uses)), w)


def T(*a, **k):
    return txt(*a, **k)[0]


def hline(x1, x2, y, stroke, w=1):
    return '<path d="M%g %gH%g" stroke="%s" stroke-width="%g"/>' % (x1, y, x2, stroke, w)


def vline(x, y1, y2, stroke, w=1):
    return '<path d="M%g %gV%g" stroke="%s" stroke-width="%g"/>' % (x, y1, y2, stroke, w)


def wrap(face, text, size, width, tracking=0.0):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if not cur or face.measure(trial, size, tracking) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def block(face, text, x, y, size, leading, width, fill, tracking=0.0):
    return "".join(T(face, ln, x, y + i * leading, size, fill, tracking)
                   for i, ln in enumerate(wrap(face, text, size, width, tracking)))


def column_grid(t, h, cols=12):
    step = CW / cols
    return "".join(vline(M + i * step, 0, h, t["rule_soft"]) for i in range(cols + 1))


def crops(t, h, size=14, off=28):
    parts = []
    for x, y in ((off, off), (W - off, off), (off, h - off), (W - off, h - off)):
        parts.append(hline(x - size / 2.0, x + size / 2.0, y, t["rule"]))
        parts.append(vline(x, y - size / 2.0, y + size / 2.0, t["rule"]))
    return "".join(parts)


def doc(h, t, body, title, desc=""):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" fill="none" role="img" aria-label="%s">'
            '<title>%s</title><desc>%s</desc>'
            '%s<rect width="%d" height="%d" fill="%s"/>%s</svg>'
            % (W, h, W, h, esc(title), esc(title), esc(desc), pool_defs(),
               W, h, t["paper"], body))


def write(name, svg):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return os.path.getsize(path)


# --------------------------------------------------------------------- hero
def hero(t):
    pool_reset()
    h = 748
    s = [column_grid(t, h), crops(t, h)]

    s.append('<rect x="%d" y="34" width="14" height="14" fill="%s"/>' % (M, t["accent"]))
    s.append(T(INTER[600], "CREATIVE TECHNOLOGY", M + 26, 46, 19, t["ink2"], .16))
    s.append(T(INTER[500], "INDIA  ·  UTC +05:30", R, 46, 19, t["ink3"], .16, anchor="end"))
    s.append(hline(M, R, 66, t["rule"]))

    # name set to the full measure; the positioning line hangs off the same baseline
    size = ANTON.size_for_width("SIDDHARTHA", CW)
    s.append(T(ANTON, "SIDDHARTHA", M, 292, size, t["ink"]))
    s.append(T(ANTON, "PERURI", M, 498, size, t["ink"]))
    s.append(T(INTER[700], "DESIGN × TECHNOLOGY", R, 498, 23, t["accent"], .12,
               anchor="end"))

    s.append(hline(M, R, 546, t["rule"]))
    s.append(block(INTER[400],
                   "I design and build digital products end to end — visual systems, "
                   "interfaces, full-stack applications, AI, and interactive 3D.",
                   M, 594, 27, 38, CW, t["ink2"]))

    s.append(hline(M, R, 668, t["rule"]))
    tags = ["VISUAL DESIGN", "UI / UX", "FULL-STACK", "AI / ML", "COMPUTER VISION", "WEBGL"]
    x = M
    for i, tag in enumerate(tags):
        part, tw = txt(INTER[600], tag, x, 706, 18, t["ink2"], .16)
        s.append(part)
        x += tw + 26
        if i < len(tags) - 1:
            s.append(vline(x - 15, 694, 710, t["rule"]))
    return doc(h, t, "".join(s), "Siddhartha Peruri — design × technology",
               "Creative technologist working across visual design, engineering, "
               "AI and interactive 3D.")


# ------------------------------------------------------------------- matrix
DISCIPLINES = [
    ("01", "DESIGN", ["Visual identity", "Branding", "Digital design", "UI / UX",
                      "Typography", "Art direction"]),
    ("02", "ENGINEERING", ["Full-stack", "Web applications", "APIs", "Databases",
                           "Architecture", "Systems"]),
    ("03", "INTELLIGENCE", ["AI / ML", "Computer vision", "Deep learning",
                            "Multimodal AI", "LLM applications", "Prediction systems"]),
    ("04", "CREATIVE TECH", ["WebGL", "Three.js / R3F", "Shaders", "Motion",
                             "Interaction", "Real-time 3D"]),
]


def matrix(t):
    pool_reset()
    h = 452
    s = [crops(t, h)]
    s.append(T(INTER[600], "CAPABILITIES", M, 46, 19, t["ink2"], .16))
    s.append(T(INTER[500], "FOUR DISCIPLINES  ·  ONE PRACTICE", R, 46, 19, t["ink3"],
               .16, anchor="end"))
    s.append(hline(M, R, 66, t["rule"]))
    step = CW / 4.0
    for i, (num, title, items) in enumerate(DISCIPLINES):
        x = M + i * step
        if i:
            s.append(vline(x - 16, 66, 396, t["rule"]))
        s.append(T(INTER[700], num, x, 108, 18, t["accent"], .12))
        s.append(T(ANTON, title, x, 158, 38, t["ink"]))
        s.append(hline(x, x + step - 40, 182, t["rule"]))
        for j, item in enumerate(items):
            s.append(T(INTER[400], item, x, 216 + j * 30, 21, t["ink2"]))
    s.append(hline(M, R, 396, t["rule"]))
    s.append(T(INTER[500], "Design and engineering treated as one discipline, not two.",
               M, 428, 20, t["ink2"]))
    return doc(h, t, "".join(s), "Capabilities",
               "Design, engineering, intelligence and creative technology.")


# -------------------------------------------------------------------- cards
def motif_orbit(t, cx, cy):
    p = ['<circle cx="%d" cy="%d" r="%d" stroke="%s" stroke-width="1"/>'
         % (cx, cy, r, t["rule"]) for r in (34, 58, 82)]
    p.append('<circle cx="%d" cy="%d" r="7" fill="%s"/>' % (cx, cy, t["accent"]))
    p.append('<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (cx + 58, cy, t["ink3"]))
    return "".join(p)


def motif_sun(t, cx, cy):
    import math
    p = []
    for i in range(12):
        a = math.radians(i * 30)
        x1, y1 = cx + 46 * math.cos(a), cy + 46 * math.sin(a)
        x2, y2 = cx + 82 * math.cos(a), cy + 82 * math.sin(a)
        p.append('<path d="M%.1f %.1f L%.1f %.1f" stroke="%s" stroke-width="1"/>'
                 % (x1, y1, x2, y2, t["rule"]))
    p.append('<circle cx="%d" cy="%d" r="34" stroke="%s" stroke-width="1"/>'
             % (cx, cy, t["rule"]))
    p.append('<circle cx="%d" cy="%d" r="13" fill="%s"/>' % (cx, cy, t["accent"]))
    return "".join(p)


def motif_wave(t, cx, cy):
    p = []
    for i in range(6):
        y = cy - 50 + i * 20
        p.append('<path d="M%d %d C%d %d, %d %d, %d %d" stroke="%s" stroke-width="1"/>'
                 % (cx - 84, y, cx - 42, y - 22 + i * 3, cx + 42, y + 22 - i * 3,
                    cx + 84, y, t["rule"]))
    p.append('<circle cx="%d" cy="%d" r="6" fill="%s"/>' % (cx, cy, t["accent"]))
    return "".join(p)


def motif_spectrum(t, cx, cy):
    p = []
    for i, bh in enumerate([26, 54, 38, 82, 46, 68, 30]):
        p.append('<rect x="%d" y="%d" width="10" height="%d" fill="%s"/>'
                 % (cx - 84 + i * 26, cy + 50 - bh, bh, t["accent"] if i == 3 else t["rule"]))
    return "".join(p)


PROJECTS = [
    dict(num="01", name="ORBIT", kicker="INTELLIGENT KNOWLEDGE PLATFORM",
         status="IN DEVELOPMENT",
         desc="Full-stack RAG platform — documents are chunked, embedded into "
              "pgvector, and retrieved to ground answers in cited sources.",
         tags=["FASTAPI", "PGVECTOR", "RAG"], motif=motif_orbit),
    dict(num="02", name="HELIOS", kicker="SOLAR ENERGY INTELLIGENCE",
         status="IN DEVELOPMENT",
         desc="Physics and ML engine for solar forecasting, behind a one-second "
              "calculator and a fourteen-view analysis console.",
         tags=["FASTAPI", "SCIKIT-LEARN", "NEXT.JS"], motif=motif_sun),
    dict(num="03", name="SPECTRA", kicker="MULTIMODAL PERCEPTION", status="PLANNED",
         desc="Multimodal AI system exploring how models reason across images, text and "
              "structured signals together.",
         tags=["AI", "VISION", "MULTIMODAL"], motif=motif_spectrum),
    dict(num="04", name="AETHER", kicker="CREATIVE COMPUTING", status="PLANNED",
         desc="Experimental WebGL work — shaders, real-time 3D and expressive "
              "interfaces built for the browser.",
         tags=["WEBGL", "R3F", "SHADERS"], motif=motif_wave),
]


def card(t, p):
    pool_reset()
    w, h, pad = 640, 420, 40
    s = ['<rect x="0.5" y="0.5" width="%d" height="%d" fill="%s" stroke="%s"/>'
         % (w - 1, h - 1, t["panel"], t["rule"])]
    s.append(p["motif"](t, w - 138, 150))
    s.append(T(INTER[700], p["num"], pad, 74, 19, t["accent"], .12))
    s.append(T(INTER[500], p["status"], pad + 44, 74, 19, t["ink3"], .16))
    s.append(T(ANTON, p["name"], pad, 190, 78, t["ink"]))
    s.append(T(INTER[600], p["kicker"], pad, 224, 20, t["ink2"], .1))
    s.append(block(INTER[400], p["desc"], pad, 274, 22, 31, 470, t["ink2"]))
    s.append(hline(pad, w - pad, 346, t["rule"]))
    x = pad
    for i, tag in enumerate(p["tags"]):
        part, tw = txt(INTER[600], tag, x, 382, 18, t["ink2"], .16)
        s.append(part)
        x += tw + 24
        if i < len(p["tags"]) - 1:
            s.append(vline(x - 13, 370, 386, t["rule"]))
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" fill="none" role="img" aria-label="%s">'
            '<title>%s</title><desc>%s</desc>'
            '%s<rect width="%d" height="%d" fill="%s"/>%s</svg>'
            % (w, h, w, h, esc(p["name"] + " — " + p["kicker"].title()),
               esc(p["name"]), esc(p["desc"]), pool_defs(),
               w, h, t["paper"], "".join(s)))


# ---------------------------------------------------------------------- now
PIPELINE = ["DATA", "PHYSICS", "MODEL", "INTERVALS", "DECISION"]


def arrow(x, y, c, size=9):
    return ('<path d="M%g %gh%d m-3.5 -3.5 3.5 3.5 -3.5 3.5" stroke="%s" '
            'stroke-width="1.4" fill="none"/>' % (x, y, size, c))


def now(t):
    pool_reset()
    h = 358
    s = [crops(t, h)]
    s.append('<rect x="%d" y="34" width="14" height="14" fill="%s"/>' % (M, t["accent"]))
    s.append(T(INTER[600], "CURRENTLY BUILDING", M + 26, 46, 19, t["accent"], .16))
    s.append(T(INTER[500], "2026", R, 46, 19, t["ink3"], .16, anchor="end"))
    s.append(hline(M, R, 66, t["rule"]))

    s.append(T(ANTON, "HELIOS", M, 188, 116, t["ink"]))
    ow = ANTON.measure("HELIOS", 116)
    s.append('<rect x="%d" y="206" width="%g" height="4" fill="%s"/>' % (M, ow, t["accent"]))
    s.append(block(INTER[400],
                   "Two interfaces over one physics-and-ML engine: a one-second "
                   "calculator, and a console for analysis.", M, 248, 22, 31, 420, t["ink2"]))

    cx = M + 520
    s.append(T(INTER[600], "SYSTEM FLOW", cx, 120, 18, t["ink3"], .16))
    s.append(hline(cx, R, 140, t["rule"]))
    x = cx
    for i, name in enumerate(PIPELINE):
        part, tw = txt(INTER[600], name, x, 178, 19, t["ink"] if i == 0 else t["ink2"], .1)
        s.append(part)
        x += tw + 14
        if i < len(PIPELINE) - 1:
            s.append(arrow(x, 172, t["ink3"]))
            x += 23
    s.append(hline(cx, R, 206, t["rule"]))
    for i, (k, v) in enumerate([("STACK", "FastAPI · scikit-learn · Next.js"),
                                ("MODEL", "XGBoost · hold-out R² 0.856"),
                                ("FOCUS", "Calibrated intervals, no leakage")]):
        y = 242 + i * 30
        s.append(T(INTER[600], k, cx, y, 17, t["ink3"], .16))
        s.append(T(INTER[400], v, cx + 96, y, 20, t["ink2"]))
    return doc(h, t, "".join(s), "Currently building HELIOS",
               "HELIOS — solar energy intelligence platform in development.")


# ------------------------------------------------------------------- footer
def footer(t):
    pool_reset()
    h = 292
    s = [column_grid(t, h), crops(t, h)]
    s.append(hline(M, R, 48, t["rule"]))
    size = ANTON.size_for_width("DESIGN × TECHNOLOGY", CW)
    s.append(T(ANTON, "DESIGN × TECHNOLOGY", M, 190, size, t["ink"]))
    s.append(hline(M, R, 222, t["rule"]))
    s.append(T(INTER[600], "SIDDHARTHA PERURI", M, 256, 19, t["ink2"], .16))
    s.append(T(INTER[500], "BUILT, NOT TEMPLATED", R, 256, 19, t["ink3"], .16, anchor="end"))
    return doc(h, t, "".join(s), "Design × technology")


# --------------------------------------------------------------------- main
def main():
    total = 0
    for name, t in THEMES.items():
        files = {"hero-%s.svg" % name: hero(t),
                 "matrix-%s.svg" % name: matrix(t),
                 "now-%s.svg" % name: now(t),
                 "footer-%s.svg" % name: footer(t)}
        for p in PROJECTS:
            key = p["name"].lower().replace("-", "")
            files["card-%s-%s.svg" % (key, name)] = card(t, p)
        for fn, svg in sorted(files.items()):
            size = write(fn, svg)
            total += size
            print("  %-28s %7d B" % (fn, size))
    print("\ntotal %d bytes" % total)


if __name__ == "__main__":
    main()
