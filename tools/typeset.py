"""Text -> SVG outline conversion (HarfBuzz shaping + fontTools outlines).

GitHub serves README SVGs with `default-src 'none'` and no font-src, so neither
webfonts nor base64-embedded fonts load. Converting type to outlines is the only
way to guarantee identical typography for every visitor.
"""
import io, os, urllib.request
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform
from fontTools.varLib import instancer
import uharfbuzz as hb

CACHE = os.path.join(os.path.dirname(__file__), ".fontcache")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0 Safari/537.36"

# latin subsets, resolved from the Google Fonts css2 API (OFL licensed)
SOURCES = {
    "anton": "https://fonts.gstatic.com/s/anton/v27/1Ptgg87LROyAm3Kz-C8.woff2",
    "inter": "https://fonts.gstatic.com/s/inter/v20/UcC73FwrK3iLTeHuS_nVMrMxCp50SjIa1ZL7.woff2",
    # Geist / Geist Mono are served as one static file per weight
    "geist-400": "https://fonts.gstatic.com/s/geist/v5/gyBhhwUxId8gMGYQMKR3pzfaWI_RnOM4nQ.ttf",
    "geist-500": "https://fonts.gstatic.com/s/geist/v5/gyBhhwUxId8gMGYQMKR3pzfaWI_RruM4nQ.ttf",
    "geist-600": "https://fonts.gstatic.com/s/geist/v5/gyBhhwUxId8gMGYQMKR3pzfaWI_RQuQ4nQ.ttf",
    "geist-700": "https://fonts.gstatic.com/s/geist/v5/gyBhhwUxId8gMGYQMKR3pzfaWI_Re-Q4nQ.ttf",
    "geistmono-400": "https://fonts.gstatic.com/s/geistmono/v6/or3yQ6H-1_WfwkMZI_qYPLs1a-t7PU0AbeE9KJ5T.ttf",
    "geistmono-500": "https://fonts.gstatic.com/s/geistmono/v6/or3yQ6H-1_WfwkMZI_qYPLs1a-t7PU0AbeEPKJ5T.ttf",
    "geistmono-600": "https://fonts.gstatic.com/s/geistmono/v6/or3yQ6H-1_WfwkMZI_qYPLs1a-t7PU0AbeHjL55T.ttf",
}


def _fetch(name):
    os.makedirs(CACHE, exist_ok=True)
    ext = os.path.splitext(SOURCES[name])[1]
    p = os.path.join(CACHE, name + ext)
    if not os.path.exists(p):
        req = urllib.request.Request(SOURCES[name], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r, open(p, "wb") as f:
            f.write(r.read())
    return p


def _num(v):
    return f"{round(v, 1):g}"


class Face:
    """One font at one weight, able to emit SVG path data for a string."""

    def __init__(self, name, wght=None, key=None):
        self.key = key or name[0]
        self._cache = {}
        font = TTFont(_fetch(name))
        if wght is not None and "fvar" in font:
            font = instancer.instantiateVariableFont(font, {"wght": wght}, inplace=False)
        font.flavor = None
        buf = io.BytesIO()
        font.save(buf)
        self.raw = buf.getvalue()
        self.font = TTFont(io.BytesIO(self.raw))
        self.glyphs = self.font.getGlyphSet()
        self.upem = self.font["head"].unitsPerEm
        self.hb = hb.Font(hb.Face(self.raw))
        self.order = self.font.getGlyphOrder()
        os_2 = self.font["OS/2"]
        self.cap = getattr(os_2, "sCapHeight", None) or int(self.upem * 0.72)

    def _shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        return list(zip(buf.glyph_infos, buf.glyph_positions))

    def measure(self, text, size, tracking=0.0):
        """Advance width in user units. `tracking` is in em (letter-spacing)."""
        units = sum(p.x_advance for _, p in self._shape(text))
        units += tracking * self.upem * max(len(text) - 1, 0)
        return units * size / self.upem

    def size_for_width(self, text, width, tracking=0.0):
        w100 = self.measure(text, 100.0, tracking)
        return 100.0 * width / w100 if w100 else 0.0

    def glyph_d(self, name):
        """Outline on a 1000-unit em, y-axis flipped, integer coordinates.

        Kept resolution-independent so one definition can be re-used at any size.
        """
        if name not in self._cache:
            k = 1000.0 / self.upem
            pen = SVGPathPen(self.glyphs, ntos=lambda v: "%d" % round(v))
            self.glyphs[name].draw(TransformPen(pen, Transform(k, 0, 0, -k, 0, 0)))
            self._cache[name] = pen.getCommands()
        return self._cache[name]

    def runs(self, text, size, tracking=0.0):
        """(glyph name, x, y) placements on the 1000-unit em, plus advance width.

        Positions are returned in em-thousandths so the caller can emit one
        scaled group of <use> references instead of repeating outline data.
        """
        k = 1000.0 / self.upem
        step = tracking * self.upem
        x, out = 0.0, []
        for info, pos in self._shape(text):
            name = self.order[info.codepoint]
            if self.glyph_d(name):
                out.append((name, round((x + pos.x_offset) * k), round(-pos.y_offset * k)))
            x += pos.x_advance + step
        return out, x * size / self.upem

    def path(self, text, size, tracking=0.0):
        """Path data with the baseline on y=0 and the string starting at x=0."""
        scale = size / self.upem
        step = tracking * self.upem
        x = 0.0
        out = []
        for info, pos in self._shape(text):
            name = self.order[info.codepoint]
            pen = SVGPathPen(self.glyphs, ntos=_num)
            tp = TransformPen(pen, Transform(scale, 0, 0, -scale,
                                             (x + pos.x_offset) * scale,
                                             -pos.y_offset * scale))
            self.glyphs[name].draw(tp)
            d = pen.getCommands()
            if d:
                out.append(d)
            x += pos.x_advance + step
        return " ".join(out), x * scale
