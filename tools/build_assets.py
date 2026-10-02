"""Draw the profile (images and README) from one source: the portfolio's design system.

    python tools/build_assets.py

System, from siddhartha-portfolio (styles/design-tokens.css and its components)
-------------------------------------------------------------------------------
Ground    ink-950 #0a0a0a. The portfolio is dark-only, so these images are too.
Type      Geist for reading and headings (weight 400, tracking -0.035em), Geist Mono for
          the small uppercase labels (tracking 0.14em), Anton for the condensed masthead.
Colour    paper on ink, one accent: signal red #ff3d2e, used for state and emphasis only.
Shape     radius 0, hairline rules (white at 8% and 14%), `[ 02 / 03 ]` section registers.
Index     the Selected Work idea: no cards, no thumbnails. A numbered row per project,
          its name large, its context small and right-aligned, its summary beneath.
Voice     evidence-led. Nothing is claimed that the repository does not show.

The portfolio's hero HUD reads "DESIGN BY SIDDHARTHA". This profile is the other half
of the same sentence: BUILT BY SIDDHARTHA.

Everything here is outlined type (tools/typeset.py), so no font loads on GitHub.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from typeset import FACES, Svg  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "assets")

# ---- tokens (styles/design-tokens.css) -----------------------------------------------
INK = "#0a0a0a"
PAPER_100, PAPER_200, PAPER_300, PAPER_400 = "#f5f5f5", "#d1d1d1", "#9a9a9a", "#6f6f6f"
WHITE = "#ffffff"
RED = "#ff3d2e"
HAIRLINE, RULE = 0.08, 0.14          # white at 8% and 14%
TRACK_EYEBROW = 0.14                 # --tracking-eyebrow
TRACK_HEADING = -0.035               # --tracking-heading
TRACK_DISPLAY = -0.05                # --tracking-display
TRACK_MASTHEAD = -0.025              # the condensed masthead

# ---- grid: GitHub's README column is ~888px, so 1 unit is about 1 css px -------------
W, M, GUT = 900, 40, 20
COL = (W - 2 * M - 11 * GUT) / 12.0


def col_x(n):
    """Left edge of 1-based column n."""
    return M + (n - 1) * (COL + GUT)


def span_w(k):
    return k * COL + (k - 1) * GUT


# ---- content (every fact below is from the named repository) -------------------------
PORTFOLIO = "https://siddhartha-portfolio-nine.vercel.app"
LINKEDIN = "https://www.linkedin.com/in/siddharthaperuri"
BEHANCE = "https://www.behance.net/siddharperuri"

STATEMENT = ("I use visual systems, interaction, and working prototypes to make digital ideas "
             "clearer, more useful, and more memorable.")  # content/profile.ts

PROJECTS = [
    dict(
        name="HELIOS", context="SOLAR FORECASTING",
        href="https://github.com/Siddhuperuri/helios",
        summary=("Solar forecasting that says how sure it is: XGBoost at R²\u00a00.856 on a held-out week, "
                 "with calibrated prediction intervals. A plain-language calculator for anyone deciding, "
                 "a fourteen-view console for anyone checking."),
        tools=["PYTHON", "FASTAPI", "SCIKIT-LEARN", "XGBOOST", "NEXT.JS"],
    ),
    dict(
        name="ORBIT", context="KNOWLEDGE PLATFORM",
        href="https://github.com/Siddhuperuri/orbit",
        summary=("Ask your documents questions, with citations to the exact passage. In\u00a0development: "
                 "the ingestion pipeline is built, chat is not. Layering is enforced in CI, "
                 "with 24 recorded decisions."),
        tools=["PYTHON", "FASTAPI", "CELERY", "POSTGRESQL", "PGVECTOR", "NEXT.JS"],
    ),
    dict(
        name="SIDDHARTHA", context="INTERACTIVE ARTWORK",
        href="https://github.com/Siddhuperuri/miracle",
        summary=("An artwork about a person: five layers of light that add up to a word from exactly "
                 "one place. No framework, no build step, no backend."),
        tools=["HTML", "CSS", "JAVASCRIPT", "THREE.JS"],
    ),
    dict(
        name="VIGIL-88", context="COMPUTER VISION",
        href="https://github.com/Siddhuperuri/vigil-88",
        summary=("Incident detection that reasons across time: a frame is evidence, not a verdict. "
                 "P0\u00a0foundation only. Nothing is detected yet, and the README says so."),
        tools=["PYTHON", "PYDANTIC", "OPENCV"],
    ),
]

ELSEWHERE = [
    dict(name="Portfolio", host="SIDDHARTHA-PORTFOLIO-NINE.VERCEL.APP", href=PORTFOLIO, lead=True,
         summary=("Design, identity and interactive work: Gravity Playground, Travelease, PETPONKS, "
                  "Creative Design Collection.")),
    dict(name="LinkedIn", host="LINKEDIN.COM/IN/SIDDHARTHAPERURI", href=LINKEDIN),
    dict(name="Behance", host="BEHANCE.NET/SIDDHARPERURI", href=BEHANCE),
]


# ---- shared pieces ---------------------------------------------------------------------
def register(svg, index, total, label, y=32):
    """The portfolio's `[ 02 / 09 ]  LABEL` bar: counter left, label centred, mono."""
    svg.text("mono", "[ %02d / %02d ]" % (index, total), M, y, 12, PAPER_300, TRACK_EYEBROW)
    svg.text("mono", label, W / 2.0, y, 12, PAPER_200, TRACK_EYEBROW, anchor="middle")


def two_tone(svg, lines, x, y, size, lead):
    """Heading in the portfolio's two-tone: first line paper-100, the rest paper-400."""
    for n, s in enumerate(lines):
        svg.text("sans", s, x, y + n * lead, size, PAPER_100 if n == 0 else PAPER_400, TRACK_HEADING)


def tools_line(svg, items, x, y, size=11):
    """Mono labels separated by space, as the portfolio sets them (no bullets)."""
    for t in items:
        w = svg.text("mono", t, x, y, size, PAPER_300, TRACK_EYEBROW)
        x += w + 20


def cap(face, size):
    return FACES[face].cap * size


# ---- panels ------------------------------------------------------------------------------
def hero():
    # Layout first, so the image is exactly as tall as its content.
    display = FACES["display"]
    f2 = (W - 2 * M - 80) / display.width("SIDDHARTHA", 1.0, TRACK_MASTHEAD)   # second line sets the measure
    f1 = f2 * 0.9                                                              # the portfolio sets line one smaller
    base1 = 128 + cap("display", f1)
    base2 = base1 + 18 + cap("display", f2)
    hud = base2 + 58                                                           # first HUD baseline
    lines = FACES["sans"].wrap(STATEMENT, 14.5, 470)
    H = round(max(hud + 44, hud - 17 + len(lines) * 22 + 36))

    svg = Svg(W, H, "Jai Sai Siddhartha")
    svg.rect(0, 0, W, H, INK)
    # A pool of light behind the name, as the portfolio lights its stage.
    svg.add('<rect width="%d" height="%d" fill="%s"/>' % (W, H, svg.radial(W / 2.0, base2 - cap("display", f2) / 2.0, 440, WHITE, 0.07)))

    register(svg, 1, 3, "PROFILE")
    svg.hline(56, 0, W, WHITE, HAIRLINE)

    # Red tag (the portfolio's "About" tag).
    tag = "ENGINEERING"
    tw = FACES["mono"].width(tag, 10, TRACK_EYEBROW) - TRACK_EYEBROW * 10
    svg.rect(M, 80, tw + 16, 22, RED)
    svg.text("mono", tag, M + 8, 95, 10, INK, TRACK_EYEBROW)

    # Masthead: two condensed lines, centred; the second italic and dimmer.
    g1 = svg.gradient([(0, "#ffffff"), (0.48, "#d8d8d8"), (1, "#6f6f6f")], 0, base1 - cap("display", f1), 0, base1)
    svg.text("display", "JAI SAI", W / 2.0, base1, f1, g1, TRACK_MASTHEAD, anchor="middle", bake=True)
    g2 = svg.gradient([(0, "#c9c9c9"), (0.45, "#8d8d8d"), (1, "#4a4a4a")], 0, base2 - cap("display", f2), 0, base2)
    svg.text("display", "SIDDHARTHA", W / 2.0, base2, f2, g2, TRACK_MASTHEAD, anchor="middle", bake=True, skew=10)

    # HUD, bottom left. The portfolio says DESIGN BY SIDDHARTHA; this is the other half.
    x = M + svg.text("mono", "BUILT BY ", M, hud, 11, PAPER_300, TRACK_EYEBROW) + 11 * TRACK_EYEBROW
    svg.text("mono", "SIDDHARTHA", x, hud, 11, PAPER_100, TRACK_EYEBROW)
    x = M + svg.text("mono", "IN", M, hud + 18, 11, PAPER_300, TRACK_EYEBROW) + 14
    svg.globe(x + 5.5, hud + 14.5, 5.5, PAPER_300)
    svg.text("mono", "IST", x + 19, hud + 18, 11, PAPER_300, TRACK_EYEBROW)

    # Statement, bottom right, set as the portfolio sets its positioning line.
    for n, line in enumerate(lines):
        svg.text("sans", line, W - M, hud - 4 + n * 22, 14.5, PAPER_200, anchor="end")

    alt = "Jai Sai Siddhartha. Engineering profile. Built by Siddhartha, in India. " + STATEMENT
    return svg, alt


def work_header():
    svg = Svg(W, 220, "Selected work")
    svg.rect(0, 0, W, 220, INK)
    svg.hline(0, 0, W, WHITE, HAIRLINE)
    register(svg, 2, 3, "SELECTED WORK")
    two_tone(svg, ["Four systems,", "built in the open."], M, 118, 46, 50)
    intro = "Public repositories. Each README is specific about what exists today and what does not."
    for n, s in enumerate(FACES["sans"].wrap(intro, 14.5, span_w(4))):
        svg.text("sans", s, col_x(9), 98 + n * 22, 14.5, PAPER_200)
    alt = "Selected work. Four systems, built in the open. " + intro
    return svg, alt


def project_row(p, n, lead, first):
    title_size, sum_size, sum_lead = 52, 15.5, 24
    lines = FACES["sans"].wrap(p["summary"], sum_size, span_w(9))
    y0 = 40 + cap("sans", title_size)
    sy = y0 + 36
    ty = sy + (len(lines) - 1) * sum_lead + 34
    H = round(ty + 36)
    svg = Svg(W, H, p["name"])
    svg.rect(0, 0, W, H, INK)
    if lead:
        svg.rect(0, 0, W, H, WHITE, 0.02)
        svg.rect(0, 0, 2, H, RED)
    if first:
        svg.hline(0, 0, W, WHITE, RULE)
    svg.hline(H - 1, 0, W, WHITE, RULE)

    svg.text("mono", "%02d" % n, M, y0, 11, PAPER_300, TRACK_EYEBROW)
    svg.text("sans", p["name"], col_x(2), y0, title_size, PAPER_100, TRACK_HEADING)
    arrow_c = RED if lead else PAPER_300
    svg.arrow(W - M - 12, y0 - 11, 12, arrow_c)
    svg.text("mono", p["context"], W - M - 26, y0, 11, PAPER_300, TRACK_EYEBROW, anchor="end")
    for i, s in enumerate(lines):
        svg.text("sans", s, col_x(2), sy + i * sum_lead, sum_size, PAPER_200)
    tools_line(svg, p["tools"], col_x(2), ty)
    alt = "%02d. %s. %s. %s Made with %s." % (n, p["name"], p["context"].capitalize(), p["summary"],
                                              ", ".join(_tool_case(t) for t in p["tools"]))
    return svg, alt


_TOOL_CASE = {"NEXT.JS": "Next.js", "THREE.JS": "three.js", "HTML": "HTML", "CSS": "CSS", "JAVASCRIPT": "JavaScript",
              "FASTAPI": "FastAPI", "PGVECTOR": "pgvector", "OPENCV": "OpenCV", "POSTGRESQL": "PostgreSQL",
              "SCIKIT-LEARN": "scikit-learn", "XGBOOST": "XGBoost", "PYDANTIC": "Pydantic", "PYTHON": "Python",
              "CELERY": "Celery"}


def _tool_case(t):
    return _TOOL_CASE.get(t, t.title())


def link_row(e, n, first):
    """A smaller index row. The first one also carries the section's register, so that no
    image is ever shorter than a line of text (a short image leaves a gap in its line box)."""
    title_size, sum_size = 34, 15.5
    lines = FACES["sans"].wrap(e["summary"], sum_size, span_w(9)) if e.get("summary") else []
    top = 48 if first else 0                      # height of the register bar
    y0 = top + 36 + cap("sans", title_size)
    H = round(y0 + 34 + (24 * len(lines) + 4 if lines else 0))
    svg = Svg(W, H, e["name"])
    svg.rect(0, 0, W, H, INK)
    if first:
        svg.hline(0, 0, W, WHITE, HAIRLINE)
        register(svg, 3, 3, "ELSEWHERE")
    if e.get("lead"):
        svg.rect(0, top, W, H - top, WHITE, 0.02)
        svg.rect(0, top, 2, H - top, RED)
    if first:
        svg.hline(top, 0, W, WHITE, RULE)
    svg.hline(H - 1, 0, W, WHITE, RULE)
    svg.text("sans", e["name"], col_x(2), y0, title_size, PAPER_100, TRACK_HEADING)
    svg.arrow(W - M - 12, y0 - 11, 12, RED if e.get("lead") else PAPER_300)
    svg.text("mono", e["host"], W - M - 26, y0, 11, PAPER_300, TRACK_EYEBROW, anchor="end")
    for i, s in enumerate(lines):
        svg.text("sans", s, col_x(2), y0 + 34 + i * 24, sum_size, PAPER_200)
    alt = "%s%s. %s%s" % ("Elsewhere. " if first else "", e["name"],
                                (e["summary"] + " ") if e.get("summary") else "", e["host"].lower())
    return svg, alt


def closing():
    H = 250
    svg = Svg(W, H, "Built by Siddhartha")
    ground = svg.gradient([(0, "#edeae4"), (0.26, "#dedad3"), (0.48, "#c9c3ba"), (0.72, "#d99a7f"),
                           (0.88, "#fb6a4a"), (1, RED)], 0, 0, 0, H)
    svg.add('<rect width="%d" height="%d" fill="%s"/>' % (W, H, ground))

    # "© BUILT BY SIDDHARTHA": the footer's masthead, with the verb changed.
    parts = [("©", False), ("BUILT BY", False), ("SIDDHARTHA", True)]
    gap_em = 0.28
    f = FACES["display"]

    def total(size):
        return sum(f.width(s, size, TRACK_MASTHEAD) - TRACK_MASTHEAD * size for s, _ in parts) + gap_em * size * (len(parts) - 1)

    size = (W - 2 * M) / total(1.0)
    base = 54 + cap("display", size)
    ink = svg.gradient([(0, "#0a0a0a"), (0.52, "#1f1f1f"), (1, "#7a7a7a")], 0, base - cap("display", size), 0, base)
    x = (W - total(size)) / 2.0
    for s, italic in parts:
        w = svg.text("display", s, x, base, size, ink, TRACK_MASTHEAD, bake=True, skew=10 if italic else 0)
        x += w + gap_em * size

    ly = H - 34
    svg.text("mono", "© PERURI JAI SAI SIDDHARTHA", M, ly, 10, "#0a0a0a", TRACK_EYEBROW, opacity=0.88)
    svg.text("mono", "SET IN GEIST & ANTON", W / 2.0, ly, 10, "#0a0a0a", TRACK_EYEBROW, anchor="middle", opacity=0.88)
    svg.text("mono", "DRAWN FROM THE PORTFOLIO'S TOKENS", W - M, ly, 10, "#0a0a0a", TRACK_EYEBROW, anchor="end", opacity=0.88)
    alt = ("© Built by Siddhartha. Peruri Jai Sai Siddhartha. Set in Geist and Anton, "
           "drawn from the portfolio's design tokens.")
    return svg, alt


# ---- build ---------------------------------------------------------------------------------
def build():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".svg"):
            os.remove(os.path.join(OUT, f))

    items = []   # (file, alt, href)

    def emit(name, made, href=None):
        svg, alt = made
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg.render())
        items.append((name, alt, href))

    emit("hero.svg", hero(), PORTFOLIO)
    emit("work.svg", work_header())
    for n, p in enumerate(PROJECTS, 1):
        slug = p["name"].lower()
        emit("work-%s.svg" % slug, project_row(p, n, lead=(n == 1), first=(n == 1)), p["href"])
    for n, e in enumerate(ELSEWHERE, 1):
        emit("elsewhere-%s.svg" % e["name"].lower(), link_row(e, n, first=(n == 1)), e["href"])
    emit("closing.svg", closing(), PORTFOLIO)

    write_readme(items)
    for name, _, _ in items:
        print("%-28s %6.1f KB" % (name, os.path.getsize(os.path.join(OUT, name)) / 1024.0))


def write_readme(items):
    out = ["<!--",
           "  Every image on this page is drawn by tools/build_assets.py from the portfolio's design",
           "  tokens, and so is this file. Edit the source and rebuild; do not edit the SVGs or this README.",
           "-->", ""]
    for name, alt, href in items:
        img = '<img src="./assets/%s" alt="%s" width="100%%" align="top">' % (name, _attr(alt))
        out.append('<a href="%s">%s</a><br>' % (href, img) if href else img + "<br>")
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")


def _attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    build()
