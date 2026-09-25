"""Build the profile's SVG asset system (light + dark).

Design system
-------------
Derived from the shipped tokens of the Portfolio2 site so the profile and the
portfolio read as one identity.

Grid      1280 canvas, 72 margin, 12 columns
Type      Anton (display) / Geist (text) / Geist Mono (labels), all outlined
Colour    ink + paper + one red accent; cyan is a status signal only
Motion    CSS only; loops are slow and semantic; all off under reduced-motion
"""
import math
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
    # dark values are Portfolio2's --ink-* / --paper-* / --red-500 / rule alphas
    "dark": dict(paper="#0A0A0A", panel="#101010", panel2="#151515",
                 rule="#2C2C2C", rule_soft="#1C1C1C", rule_strong="#454545",
                 ink="#F5F5F5", ink2="#9A9A9A", ink3="#6F6F6F",
                 accent="#FF3D2E", signal="#1CE0C4", dot="#FFFFFF", dot_a=".13",
                 glow="#1B1B1B", card="#F5F5F5", card_fg="#0A0A0A", card_dim="#7A7A7A"),
    "light": dict(paper="#F7F7F5", panel="#FFFFFF", panel2="#EFEFEC",
                  rule="#D9D9D4", rule_soft="#E9E9E5", rule_strong="#BDBDB6",
                  ink="#0A0A0A", ink2="#5A5A5A", ink3="#8A8A8A",
                  accent="#D92C22", signal="#0E9F8B", dot="#000000", dot_a=".14",
                  glow="#E6E6E1", card="#0A0A0A", card_fg="#F5F5F5", card_dim="#8A8A8A"),
}

ANTON = Face("anton", key="a")
SANS = {w: Face("geist-%d" % w, key="s%d" % (w // 100)) for w in (400, 500, 600, 700)}
MONO = {w: Face("geistmono-%d" % w, key="m%d" % (w // 100)) for w in (400, 500, 600)}

# Every distinct letterform is defined once per document and re-used with <use>,
# which keeps files small even though all type is outlined.
POOL = {}


def pool_reset():
    POOL.clear()


def pool_defs():
    return "".join('<path id="%s" d="%s"/>' % (gid, d) for gid, d in POOL.values())


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
        uses.append('<use href="#%s" x="%d"%s/>'
                    % (POOL[key][0], gx, ' y="%d"' % gy if gy else ""))
    return ('<g transform="translate(%g,%g) scale(%.6f)" fill="%s">%s</g>'
            % (x, y, size / 1000.0, fill, "".join(uses)), w)


def T(*a, **k):
    return txt(*a, **k)[0]


def eyebrow(s, x, y, fill, size=16, anchor="start", tracking=.14, weight=500):
    """Mono uppercase label - the 'technical journal' voice."""
    return T(MONO[weight], s, x, y, size, fill, tracking, anchor=anchor)


def hline(x1, x2, y, stroke, w=1, cls=""):
    return '<path%s d="M%g %gH%g" stroke="%s" stroke-width="%g"/>' % (
        ' class="%s"' % cls if cls else "", x1, y, x2, stroke, w)


def vline(x, y1, y2, stroke, w=1, cls=""):
    return '<path%s d="M%g %gV%g" stroke="%s" stroke-width="%g"/>' % (
        ' class="%s"' % cls if cls else "", x, y1, y2, stroke, w)


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


def ring_mark(cx, cy, r, t, dot=None):
    """Ring + dot: the mark from the WebGL portfolio's loader, in the accent."""
    return ('<circle cx="%g" cy="%g" r="%g" stroke="%s" stroke-width="1.6"/>'
            '<circle cx="%g" cy="%g" r="%g" fill="%s"/>'
            % (cx, cy, r, t["accent"], cx, cy, r * .38, dot or t["ink"]))


def asterisk(cx, cy, r, color, w=1.7):
    return "".join('<path d="M%.2f %.2fL%.2f %.2f" stroke="%s" stroke-width="%g" '
                   'stroke-linecap="round"/>'
                   % (cx - r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a)),
                      cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)),
                      color, w) for a in (90, 30, -30))


def globe_plus(cx, cy, r, color):
    """The circled plus that precedes the timezone readout (not in Geist)."""
    return ('<circle cx="%g" cy="%g" r="%g" stroke="%s" stroke-width="1.5"/>'
            '<path d="M%g %gH%g M%g %gV%g" stroke="%s" stroke-width="1.5"/>'
            % (cx, cy, r, color, cx - r, cy, cx + r, cx, cy - r, cy + r, color))


def glint(cx, cy, arm, color, cls=""):
    """Pinched four-arm star - the glint printed on Portfolio2's badge."""
    k = .17
    d = ("M0 %g C0 %g %g 0 %g 0 C%g 0 0 %g 0 %g C0 %g %g 0 %g 0 C%g 0 0 %g 0 %g Z"
         % (-arm, -arm * k, arm * k, arm, arm * k, arm * k, arm, arm * k, -arm * k,
            -arm, -arm * k, -arm * k, -arm))
    return '<path%s transform="translate(%g,%g)" d="%s" fill="%s"/>' % (
        ' class="%s"' % cls if cls else "", cx, cy, d, color)


# ------------------------------------------------------------------- motion
# GitHub serves README SVGs with `style-src 'unsafe-inline'`, so inline CSS
# animation runs inside the <img>; script and webfonts stay blocked. Above the
# fold plays once then settles; below the fold loops slowly, because a one-shot
# would have finished before it is scrolled into view. All of it is dropped
# under prefers-reduced-motion, leaving the static composition.
def anim(css):
    return ("<style>%s@media(prefers-reduced-motion:reduce){"
            "*{animation:none!important}.rv{opacity:1!important}"
            ".dr{stroke-dashoffset:0!important}.fl{opacity:1!important}}</style>" % css)


def wrap_g(cls, *parts):
    """Plain group (no transform attribute) so CSS transforms are free to animate."""
    return '<g class="%s">%s</g>' % (cls, "".join(parts))


def doc(w, h, t, body, title, desc="", style="", defs=""):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d" fill="none" role="img" aria-label="%s">'
            '<title>%s</title><desc>%s</desc>%s<defs>%s%s</defs>'
            '<rect width="%d" height="%d" fill="%s"/>%s</svg>'
            % (w, h, w, h, esc(title), esc(title), esc(desc), style, defs, pool_defs(),
               w, h, t["paper"], body))


def write(name, svg):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return os.path.getsize(path)


def dot_field(t, x, y, w, h, cx, cy, rx, ry):
    """CSS-grade dot texture, faded out toward the edges (Portfolio2's --texture-dot)."""
    defs = ('<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            '<circle cx="1.5" cy="1.5" r="1.1" fill="%s" fill-opacity="%s"/></pattern>'
            '<radialGradient id="df" cx="%g" cy="%g" r="1" gradientUnits="userSpaceOnUse" '
            'gradientTransform="translate(%g %g) scale(%g %g) translate(%g %g)">'
            '<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/>'
            '</radialGradient><mask id="dm"><rect x="%g" y="%g" width="%g" height="%g" '
            'fill="url(#df)"/></mask>'
            % (t["dot"], t["dot_a"], 0, 0, cx, cy, rx, ry, 0, 0, x, y, w, h))
    return defs, '<rect x="%g" y="%g" width="%g" height="%g" fill="url(#dots)" mask="url(#dm)"/>' % (
        x, y, w, h)


# --------------------------------------------------------------------- hero
ROLE = "Product-minded visual designer and creative front-end builder."
STATEMENT = ("I use visual systems, interaction, and working prototypes to make digital "
             "ideas clearer, more useful, and more memorable.")

HERO_CSS = (
    "@keyframes rv{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}"
    "@keyframes up{from{opacity:0;transform:translateY(30px)}to{opacity:1;transform:none}}"
    "@keyframes dr{to{stroke-dashoffset:0}}"
    "@keyframes swing{0%{transform:rotate(11deg)}14%{transform:rotate(-8deg)}"
    "28%{transform:rotate(5.5deg)}42%{transform:rotate(-3.5deg)}56%{transform:rotate(2.2deg)}"
    "70%{transform:rotate(-1.2deg)}85%{transform:rotate(.5deg)}100%{transform:rotate(0)}}"
    "@keyframes sway{0%,100%{transform:rotate(0)}25%{transform:rotate(1.1deg)}"
    "75%{transform:rotate(-1.1deg)}}"
    "@keyframes tw{0%,100%{opacity:.35;transform:scale(.8)}50%{opacity:1;transform:scale(1)}}"
    ".rv{opacity:0;animation:rv .8s cubic-bezier(.16,1,.3,1) both}"
    ".up{animation-name:up;animation-duration:1s}"
    ".dr{stroke-dasharray:@CW@;stroke-dashoffset:@CW@;"
    "animation:dr 1.2s cubic-bezier(.16,1,.3,1) both}"
    ".d1{animation-delay:.05s}.d2{animation-delay:.2s}.d3{animation-delay:.35s}"
    ".d4{animation-delay:.5s}.d5{animation-delay:.65s}"
    ".sw{transform-origin:@BX@px 0px;transform-box:view-box;"
    "animation:swing 5.5s cubic-bezier(.3,0,.3,1) .3s both,sway 9s ease-in-out 5.8s infinite}"
    ".gl{transform-box:fill-box;transform-origin:center;animation:tw 4.5s ease-in-out infinite}"
)


def hero(t):
    pool_reset()
    h = 800
    bx = 968                                    # badge centre line; clear of the HUD label
    s = [column_grid(t, h), crops(t, h)]

    ddefs, dots = dot_field(t, 760, 66, 448, 650, bx, 400, 270, 300)
    gdef = ('<radialGradient id="spot" cx="%d" cy="400" r="300" gradientUnits="userSpaceOnUse">'
            '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s" stop-opacity="0"/>'
            '</radialGradient>' % (bx, t["glow"], t["glow"]))
    s.append('<rect x="700" y="66" width="508" height="650" fill="url(#spot)"/>')
    s.append(dots)

    # HUD row
    s.append(wrap_g("rv d1", ring_mark(M + 10, 41, 10, t),
                    eyebrow("SIDDHARTHA PERURI", M + 34, 46, t["ink2"]),
                    eyebrow("PROFILE  /  2026", R, 46, t["ink3"], anchor="end")))
    s.append(hline(M, R, 66, t["rule"], cls="dr"))

    # name, set to a fixed measure on the left
    left = 690
    size = ANTON.size_for_width("SIDDHARTHA", left)
    cap = ANTON.cap * size / ANTON.upem
    y1 = 120 + cap
    y2 = y1 + cap * 1.1
    s.append(wrap_g("rv d2", eyebrow("01 — PROFILE", M, 104, t["accent"], 15, weight=600)))
    s.append(wrap_g("rv up d2", T(ANTON, "SIDDHARTHA", M, y1, size, t["ink"])))
    s.append(wrap_g("rv up d3", T(ANTON, "PERURI", M, y2, size, t["ink"])))

    ry = y2 + 44
    s.append(hline(M, M + left, ry, t["rule"], cls="dr d3"))
    role = block(SANS[600], ROLE, M, ry + 58, 30, 40, left - 30, t["ink"], -.005)
    s.append(wrap_g("rv d4", role))
    ny = ry + 58 + 40 * len(wrap(SANS[600], ROLE, 30, left - 30, -.005)) + 14
    s.append(wrap_g("rv d4", block(SANS[400], STATEMENT, M, ny, 20, 30, left - 60,
                                   t["ink2"])))

    # bottom HUD
    s.append(hline(M, R, 716, t["rule"], cls="dr d4"))
    s.append(wrap_g("rv d5",
                    eyebrow("DESIGN BY", M, 758, t["ink3"], 14),
                    eyebrow("SIDDHARTHA", M + 108, 758, t["ink"], 14, weight=600),
                    globe_plus(M + 8, 780, 7, t["ink3"]),
                    eyebrow("INDIA  ·  IST +05:30", M + 24, 785, t["ink2"], 14),
                    eyebrow("B.TECH CSE  ·  2027", R, 758, t["ink3"], 14, anchor="end"),
                    eyebrow("VISUAL DESIGN  ·  FRONT-END  ·  AI", R, 785, t["ink2"],
                            14, anchor="end")))

    # scaled about the pivot so the swing origin stays on the lanyard's top edge
    s.append('<g transform="translate(%d,0) scale(1.08) translate(%d,0)">%s</g>'
             % (bx, -bx, _badge(t, bx)))
    css = HERO_CSS.replace("@CW@", str(CW)).replace("@BX@", str(bx))
    return doc(W, h, t, "".join(s), "Siddhartha Peruri — visual designer and front-end builder",
               "Product-minded visual designer and creative front-end builder.",
               anim(css), ddefs + gdef)


def _badge(t, cx):
    """Hanging ID badge: lanyard from the top edge, clip, vinyl sleeve, printed card."""
    sw = 300
    sx, sy, sh = cx - sw / 2, 236, 404
    card_x, card_y, card_w, card_h = cx - 136, sy + 30, 272, 362
    ink, dim = t["card_fg"], t["card_dim"]
    p = []
    # lanyard, stitched
    p.append('<rect x="%g" y="0" width="28" height="200" fill="%s"/>' % (cx - 14, t["accent"]))
    p.append('<path d="M%g 0V200" stroke="%s" stroke-width="1.2" stroke-dasharray="6 6" '
             'stroke-opacity=".55"/>' % (cx, t["paper"]))
    # clip
    p.append('<rect x="%g" y="196" width="44" height="44" rx="8" fill="%s" stroke="%s"/>'
             % (cx - 22, t["panel2"], t["rule_strong"]))
    p.append('<rect x="%g" y="206" width="20" height="10" rx="5" fill="%s"/>' % (cx - 10, t["paper"]))
    # sleeve + slot
    p.append('<rect x="%g" y="%g" width="%d" height="%d" rx="24" fill="%s" stroke="%s" '
             'stroke-width="1.4"/>' % (sx, sy, sw, sh, t["panel2"], t["rule_strong"]))
    p.append('<rect x="%g" y="%g" width="64" height="9" rx="4.5" fill="%s"/>'
             % (cx - 32, sy + 12, t["paper"]))
    # card
    p.append('<rect x="%g" y="%g" width="%d" height="%d" rx="12" fill="%s"/>'
             % (card_x, card_y, card_w, card_h, t["card"]))
    pad = 22
    tx, tw = card_x + pad, card_w - 2 * pad
    p.append(eyebrow("ID  001", tx, card_y + 38, dim, 13, weight=600))
    p.append(ring_mark(card_x + card_w - pad - 8, card_y + 32, 8, t, dot=ink))
    # two words, each fitted flush to the measure
    s1 = ANTON.size_for_width("DESIGN", tw)
    c1 = ANTON.cap * s1 / ANTON.upem
    s2 = ANTON.size_for_width("BUILD", tw)
    c2 = ANTON.cap * s2 / ANTON.upem
    b1 = card_y + 64 + c1
    b2 = b1 + 16 + c2
    p.append(T(ANTON, "DESIGN", tx, b1, s1, ink))
    p.append(T(ANTON, "BUILD", tx, b2, s2, ink))
    p.append(glint(tx + tw - 26, b1 + 8, 30, t["accent"], "gl"))
    fy = card_y + card_h - 30
    p.append(hline(tx, tx + tw, fy - 44, dim, 1))
    p.append(eyebrow("SIDDHARTHA PERURI", tx, fy - 14, ink, 13, weight=600))
    p.append(eyebrow("CSE  ·  2027", tx, fy + 6, dim, 12))
    return wrap_g("sw", "".join(p))


# ------------------------------------------------------------------ marquee
SKILLS = ["UI/UX design", "Website design", "Visual design", "Branding", "Logo design",
          "Wireframing", "Figma", "Framer", "Photoshop", "Illustrator", "Lightroom",
          "Canva", "HTML", "CSS", "JavaScript", "TypeScript", "Next.js", "Three.js",
          "Python", "Java", "FastAPI", "PyTorch"]


def marquee(t):
    pool_reset()
    h = 168
    size, gap, sep = 27, 56, 14
    s = [hline(0, W, 0.5, t["rule"]), hline(0, W, h - 0.5, t["rule"])]
    s.append(eyebrow("TOOLS  &  CRAFT", W / 2, 44, t["ink3"], 14, anchor="middle"))

    def run(x0):
        x, out = x0, []
        for name in SKILLS:
            out.append(asterisk(x + sep / 2, 104, sep / 2, t["ink3"]))
            x += sep + 16
            part, w = txt(SANS[400], name, x, 113, size, t["ink"], -.01)
            out.append(part)
            x += w + gap
        return "".join(out), x - x0

    first, span = run(0)
    second, _ = run(span)
    s.append('<g clip-path="url(#mq)"><g class="mq">%s%s</g></g>' % (first, second))
    fade = ('<linearGradient id="fl" x1="0" x2="1"><stop offset="0" stop-color="%s"/>'
            '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="fr" x1="1" x2="0"><stop offset="0" stop-color="%s"/>'
            '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient>'
            '<clipPath id="mq"><rect x="0" y="66" width="%d" height="72"/></clipPath>'
            % (t["paper"], t["paper"], t["paper"], t["paper"], W))
    s.append('<rect x="0" y="66" width="180" height="72" fill="url(#fl)"/>')
    s.append('<rect x="%d" y="66" width="180" height="72" fill="url(#fr)"/>' % (W - 180))
    css = ("@keyframes mq{to{transform:translateX(-@S@px)}}"
           ".mq{animation:mq 90s linear infinite}").replace("@S@", "%d" % round(span))
    return doc(W, h, t, "".join(s), "Tools and craft",
               "Design, tooling and build skills.", anim(css), fade)


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
    h = 462
    s = [crops(t, h)]
    s.append(eyebrow("CAPABILITIES", M, 46, t["ink2"]))
    s.append(eyebrow("FOUR DISCIPLINES  ·  ONE PRACTICE", R, 46, t["ink3"], anchor="end"))
    s.append(hline(M, R, 66, t["rule"]))
    step = CW / 4.0
    for i, (num, title, items) in enumerate(DISCIPLINES):
        x = M + i * step
        if i:
            s.append(vline(x - 16, 66, 404, t["rule"]))
        s.append(eyebrow(num, x, 112, t["accent"], 15, weight=600))
        s.append(T(ANTON, title, x, 162, 38, t["ink"]))
        s.append(hline(x, x + step - 40, 186, t["rule"]))
        for j, item in enumerate(items):
            s.append(T(SANS[400], item, x, 222 + j * 31, 21, t["ink2"]))
    s.append(hline(M, R, 404, t["rule"]))
    s.append(T(SANS[500], "Design and engineering treated as one discipline, not two.",
               M, 438, 20, t["ink2"]))
    return doc(W, h, t, "".join(s), "Capabilities",
               "Design, engineering, intelligence and creative technology.")


# -------------------------------------------------------------------- cards
def motif_orbit(t, cx, cy):
    p = ['<circle cx="%d" cy="%d" r="%d" stroke="%s" stroke-width="1"/>'
         % (cx, cy, r, t["rule_strong"]) for r in (34, 58, 82)]
    p.append('<circle cx="%d" cy="%d" r="7" fill="%s"/>' % (cx, cy, t["accent"]))
    p.append('<circle class="orb" cx="%d" cy="%d" r="5" fill="%s"/>' % (cx + 58, cy, t["ink3"]))
    return "".join(p)


def motif_sun(t, cx, cy):
    p = []
    for i in range(12):
        a = math.radians(i * 30)
        p.append('<path d="M%.1f %.1f L%.1f %.1f" stroke="%s" stroke-width="1"/>'
                 % (cx + 46 * math.cos(a), cy + 46 * math.sin(a),
                    cx + 82 * math.cos(a), cy + 82 * math.sin(a), t["rule_strong"]))
    return ('<g class="ray">%s</g><circle cx="%d" cy="%d" r="34" stroke="%s" stroke-width="1"/>'
            '<circle cx="%d" cy="%d" r="13" fill="%s"/>'
            % ("".join(p), cx, cy, t["rule_strong"], cx, cy, t["accent"]))


def motif_wave(t, cx, cy):
    p = []
    for i in range(6):
        y = cy - 50 + i * 20
        p.append('<path d="M%d %d C%d %d, %d %d, %d %d" stroke="%s" stroke-width="1"/>'
                 % (cx - 84, y, cx - 42, y - 22 + i * 3, cx + 42, y + 22 - i * 3,
                    cx + 84, y, t["rule_strong"]))
    return ('<g class="wv">%s</g><circle cx="%d" cy="%d" r="6" fill="%s"/>'
            % ("".join(p), cx, cy, t["accent"]))


def motif_spectrum(t, cx, cy):
    return "".join('<rect class="bar b%d" x="%d" y="%d" width="10" height="%d" fill="%s"/>'
                   % (i, cx - 84 + i * 26, cy + 50 - bh, bh,
                      t["accent"] if i == 3 else t["rule_strong"])
                   for i, bh in enumerate([26, 54, 38, 82, 46, 68, 30]))


PROJECTS = [
    dict(num="01", name="ORBIT", kicker="INTELLIGENT KNOWLEDGE PLATFORM", live=True,
         status="IN DEVELOPMENT",
         desc="Full-stack RAG platform — documents are chunked, embedded into "
              "pgvector, and retrieved to ground answers in cited sources.",
         tags=["FASTAPI", "PGVECTOR", "RAG"], motif=motif_orbit),
    dict(num="02", name="HELIOS", kicker="SOLAR ENERGY INTELLIGENCE", live=True,
         status="IN DEVELOPMENT",
         desc="Physics and ML engine for solar forecasting, behind a one-second "
              "calculator and a fourteen-view analysis console.",
         tags=["FASTAPI", "SCIKIT-LEARN", "NEXT.JS"], motif=motif_sun),
    dict(num="03", name="SPECTRA", kicker="MULTIMODAL PERCEPTION", live=False,
         status="PLANNED",
         desc="Multimodal AI system exploring how models reason across images, text and "
              "structured signals together.",
         tags=["AI", "VISION", "MULTIMODAL"], motif=motif_spectrum),
    dict(num="04", name="AETHER", kicker="CREATIVE COMPUTING", live=False,
         status="PLANNED",
         desc="Experimental WebGL work — shaders, real-time 3D and expressive "
              "interfaces built for the browser.",
         tags=["WEBGL", "R3F", "SHADERS"], motif=motif_wave),
]

CARD_CSS = (
    "@keyframes sp{to{transform:rotate(360deg)}}"
    "@keyframes dft{from{transform:translateX(-6px)}to{transform:translateX(6px)}}"
    "@keyframes shm{0%,100%{opacity:.45}50%{opacity:1}}"
    "@keyframes pl{0%,100%{opacity:1}50%{opacity:.25}}"
    ".orb,.ray{transform-origin:502px 150px;transform-box:view-box}"
    ".orb{animation:sp 20s linear infinite}"
    ".ray{animation:sp 90s linear infinite}"
    ".wv{animation:dft 11s ease-in-out infinite alternate}"
    ".bar{animation:shm 6s ease-in-out infinite}"
    ".pl{animation:pl 2.4s ease-in-out infinite}"
    ".b0{animation-delay:0s}.b1{animation-delay:.3s}.b2{animation-delay:.6s}"
    ".b3{animation-delay:.9s}.b4{animation-delay:1.2s}.b5{animation-delay:1.5s}"
    ".b6{animation-delay:1.8s}")


def card(t, p):
    pool_reset()
    w, h, pad = 640, 420, 40
    s = ['<rect x="0.5" y="0.5" width="%d" height="%d" fill="%s" stroke="%s"/>'
         % (w - 1, h - 1, t["panel"], t["rule"])]
    s.append(p["motif"](t, w - 138, 150))
    s.append(eyebrow(p["num"], pad, 74, t["accent"], 15, weight=600))
    if p["live"]:
        s.append('<circle class="pl" cx="%d" cy="69" r="4.5" fill="%s"/>' % (pad + 50, t["signal"]))
    else:
        s.append('<circle cx="%d" cy="69" r="4" stroke="%s" stroke-width="1.3"/>'
                 % (pad + 50, t["ink3"]))
    s.append(eyebrow(p["status"], pad + 66, 74, t["ink3"], 15))
    s.append(T(ANTON, p["name"], pad, 190, 78, t["ink"]))
    s.append(eyebrow(p["kicker"], pad, 226, t["ink2"], 15, weight=500, tracking=.1))
    s.append(block(SANS[400], p["desc"], pad, 272, 21, 30, 470, t["ink2"]))
    s.append(hline(pad, w - pad, 356, t["rule"]))
    x = pad
    for i, tag in enumerate(p["tags"]):
        part, tw = txt(MONO[600], tag, x, 391, 15, t["ink2"], .12)
        s.append(part)
        x += tw + 24
        if i < len(p["tags"]) - 1:
            s.append(vline(x - 13, 379, 395, t["rule"]))
    return doc(w, h, t, "".join(s), p["name"] + " — " + p["kicker"].title(), p["desc"],
               anim(CARD_CSS))


# ---------------------------------------------------------------------- now
PIPELINE = ["DATA", "PHYSICS", "MODEL", "INTERVALS", "DECISION"]


def arrow(x, y, c, size=9):
    return ('<path d="M%g %gh%d m-3.5 -3.5 3.5 3.5 -3.5 3.5" stroke="%s" '
            'stroke-width="1.4" fill="none"/>' % (x, y, size, c))


def now(t):
    pool_reset()
    h = 358
    s = [crops(t, h)]
    s.append('<circle class="pl" cx="%d" cy="41" r="5.5" fill="%s"/>' % (M + 6, t["signal"]))
    s.append(eyebrow("CURRENTLY BUILDING", M + 24, 46, t["accent"], weight=600))
    s.append(eyebrow("2026", R, 46, t["ink3"], anchor="end"))
    s.append(hline(M, R, 66, t["rule"]))

    s.append(T(ANTON, "HELIOS", M, 188, 116, t["ink"]))
    ow = ANTON.measure("HELIOS", 116)
    s.append('<rect x="%d" y="206" width="%g" height="4" fill="%s"/>' % (M, ow, t["accent"]))
    s.append(block(SANS[400],
                   "Two interfaces over one physics-and-ML engine: a one-second "
                   "calculator, and a console for analysis.", M, 250, 21, 31, 420, t["ink2"]))

    cx = M + 520
    s.append(eyebrow("SYSTEM FLOW", cx, 118, t["ink3"], 14))
    s.append(hline(cx, R, 140, t["rule"]))
    x = cx
    for i, name in enumerate(PIPELINE):
        part, tw = txt(MONO[600], name, x, 178, 17, t["ink"], .08)
        s.append(wrap_g("fl f%d" % i, part))
        x += tw + 14
        if i < len(PIPELINE) - 1:
            s.append(arrow(x, 172, t["ink3"]))
            x += 23
    s.append(hline(cx, R, 206, t["rule"]))
    for i, (k, v) in enumerate([("STACK", "FastAPI · scikit-learn · Next.js"),
                                ("MODEL", "XGBoost · hold-out R² 0.856"),
                                ("FOCUS", "Calibrated intervals, no leakage")]):
        y = 244 + i * 30
        s.append(eyebrow(k, cx, y, t["ink3"], 14, weight=600))
        s.append(T(SANS[400], v, cx + 100, y, 20, t["ink2"]))
    css = ("@keyframes fl{0%,22%,100%{opacity:.45}8%{opacity:1}}"
           "@keyframes pl{0%,100%{opacity:1}50%{opacity:.25}}"
           ".fl{opacity:.45;animation:fl 7s ease-in-out infinite}"
           ".pl{animation:pl 2.4s ease-in-out infinite}"
           ".f0{animation-delay:0s}.f1{animation-delay:.55s}.f2{animation-delay:1.1s}"
           ".f3{animation-delay:1.65s}.f4{animation-delay:2.2s}")
    return doc(W, h, t, "".join(s), "Currently building HELIOS",
               "HELIOS — solar energy intelligence platform in development.", anim(css))


# ------------------------------------------------------------------ process
STEPS = [
    ("01", "Understand the signal",
     "Frame the user, context, constraint, and success condition before choosing a "
     "visual direction."),
    ("02", "Make the system visible",
     "Turn the strongest idea into a simple information structure, flow, or interaction "
     "model."),
    ("03", "Test through making",
     "Prototype early so pacing, usability, and visual hierarchy can be evaluated in motion."),
    ("04", "Polish what people feel",
     "Refine the details that shape trust: clarity, state changes, accessibility, and "
     "performance."),
]


def process(t):
    pool_reset()
    h = 452
    s = [crops(t, h)]
    s.append(eyebrow("PROCESS", M, 46, t["ink2"]))
    s.append(eyebrow("FOUR STEPS  ·  IN ORDER", R, 46, t["ink3"], anchor="end"))
    s.append(hline(M, R, 66, t["rule"]))
    ly = 122
    s.append(hline(M, R, ly, t["rule_strong"]))
    step = CW / 4.0
    for i, (num, title, detail) in enumerate(STEPS):
        x = M + i * step
        s.append('<circle cx="%g" cy="%d" r="6" fill="%s" stroke="%s" stroke-width="1.5"/>'
                 % (x + 6, ly, t["paper"], t["accent"]))
        s.append(eyebrow(num, x, 176, t["accent"], 15, weight=600))
        s.append(block(SANS[600], title, x, 214, 25, 32, step - 40, t["ink"], -.01))
        n = len(wrap(SANS[600], title, 25, step - 40, -.01))
        s.append(block(SANS[400], detail, x, 214 + 32 * n + 14, 18, 27, step - 44, t["ink2"]))
    s.append('<circle class="tv" cx="%d" cy="%d" r="4" fill="%s"/>' % (M, ly, t["accent"]))
    css = ("@keyframes tv{0%{transform:translateX(0);opacity:0}6%{opacity:1}"
           "94%{opacity:1}100%{transform:translateX(@L@px);opacity:0}}"
           ".tv{animation:tv 12s cubic-bezier(.45,0,.55,1) infinite}").replace("@L@", str(CW))
    return doc(W, h, t, "".join(s), "Process",
               "Understand the signal, make the system visible, test through making, "
               "polish what people feel.", anim(css))


# ------------------------------------------------------------------- footer
def footer(t):
    pool_reset()
    h = 292
    s = [column_grid(t, h), crops(t, h)]
    s.append(hline(M, R, 48, t["rule"]))
    size = ANTON.size_for_width("DESIGN × TECHNOLOGY", CW)
    s.append(T(ANTON, "DESIGN × TECHNOLOGY", M, 190, size, t["ink"]))
    s.append(hline(M, R, 222, t["rule"]))
    s.append(ring_mark(M + 10, 251, 10, t))
    s.append(eyebrow("SIDDHARTHA PERURI", M + 34, 256, t["ink2"]))
    s.append(eyebrow("CSE  ·  2027", R, 256, t["ink3"], anchor="end"))
    return doc(W, h, t, "".join(s), "Design × technology")


# --------------------------------------------------------------------- main
def main():
    total = 0
    for name, t in THEMES.items():
        files = {"hero-%s.svg" % name: hero(t),
                 "marquee-%s.svg" % name: marquee(t),
                 "matrix-%s.svg" % name: matrix(t),
                 "now-%s.svg" % name: now(t),
                 "process-%s.svg" % name: process(t),
                 "footer-%s.svg" % name: footer(t)}
        for p in PROJECTS:
            files["card-%s-%s.svg" % (p["name"].lower().replace("-", ""), name)] = card(t, p)
        for fn, svg in sorted(files.items()):
            size = write(fn, svg)
            total += size
            print("  %-28s %7d B" % (fn, size))
    print("\ntotal %d bytes" % total)


if __name__ == "__main__":
    main()
