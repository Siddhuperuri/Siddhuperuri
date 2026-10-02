"""Set type as SVG outlines.

GitHub serves README images with `default-src 'none'`, so a font can never load inside
an SVG. Instead the glyphs are drawn once, here, as paths: the pixels are the portfolio's
typefaces (Geist, Geist Mono, Anton) and nothing has to be installed to see them.

Shaping is HarfBuzz, so kerning is the font's own. Outlines come from fontTools.
Standard text is pooled (each glyph defined once, placed with <use>); text that carries
a gradient is baked to absolute coordinates so the gradient runs across the whole line.
"""
import io
import os

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")


def num(v):
    """Compact number: one decimal at most, no trailing zeros."""
    s = ("%.1f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Face:
    def __init__(self, key, filename):
        self.key = key
        tt = TTFont(os.path.join(FONT_DIR, filename))
        self.upem = tt["head"].unitsPerEm
        self.cap = tt["OS/2"].sCapHeight / self.upem
        self.glyphs = tt.getGlyphSet()
        self.order = tt.getGlyphOrder()
        buf = io.BytesIO()
        tt.flavor = None
        tt.save(buf)
        self._hb = hb.Font(hb.Face(hb.Blob(buf.getvalue())))
        self._shaped = {}

    def shape(self, s):
        """[(glyph name, advance, x offset, y offset)] in font units, kerning applied."""
        if s not in self._shaped:
            b = hb.Buffer()
            b.add_str(s)
            b.guess_segment_properties()
            hb.shape(self._hb, b, {"kern": True, "liga": False, "calt": False})
            if any(i.codepoint == 0 for i in b.glyph_infos):
                raise ValueError("%s has no glyph for a character in %r" % (self.key, s))
            self._shaped[s] = [
                (self.order[i.codepoint], p.x_advance, p.x_offset, p.y_offset)
                for i, p in zip(b.glyph_infos, b.glyph_positions)
            ]
        return self._shaped[s]

    def width(self, s, size, track=0.0):
        """Advance width in px, with letter-spacing `track` (em) after every glyph."""
        k = size / self.upem
        runs = self.shape(s)
        return sum(a for _, a, _, _ in runs) * k + track * size * len(runs)

    def wrap(self, s, size, max_width, track=0.0):
        """Word wrap, balanced: same line count as greedy, but no one-word last line."""
        lines = self._greedy(s, size, max_width, track)
        if len(lines) < 2:
            return lines
        best, w = lines, max_width
        while w > max_width * 0.72:
            w -= 6
            trial = self._greedy(s, size, w, track)
            if len(trial) != len(lines):
                break
            if self.width(trial[-1], size, track) > self.width(best[-1], size, track):
                best = trial
            if len(trial[-1].split()) >= 3 and self.width(trial[-1], size, track) > 0.4 * max_width:
                best = trial
                break
        return best

    def _greedy(self, s, size, max_width, track=0.0):
        """Greedy fill. A no-break space (U+00A0) in the copy keeps its words on one line."""
        lines, cur = [], ""
        for word in s.split(" "):
            trial = word if not cur else cur + " " + word
            if cur and self.width(trial.replace("\u00a0", " "), size, track) > max_width:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return [ln.replace("\u00a0", " ") for ln in lines]

    def path(self, name):
        pen = SVGPathPen(self.glyphs, ntos=num)
        self.glyphs[name].draw(pen)
        return pen.getCommands()

    def baked(self, s, x, y, size, track=0.0):
        """One absolute-coordinate path for the whole string, baseline at (x, y)."""
        k = size / self.upem
        pen = SVGPathPen(None, ntos=num)
        cx = x
        for name, adv, dx, dy in self.shape(s):
            self.glyphs[name].draw(TransformPen(pen, (k, 0, 0, -k, cx + dx * k, y - dy * k)))
            cx += adv * k + track * size
        return pen.getCommands()


FACES = {
    "sans": Face("s", "geist-latin-400-normal.woff"),
    "mono": Face("m", "geist-mono-latin-400-normal.woff"),
    "display": Face("d", "anton-latin-400-normal.woff"),
}


class Svg:
    """A single image: defs pool, gradients, and body, written out as one document."""

    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self._glyphs = {}      # id -> path data (pooled outlines)
        self._grads = []       # <linearGradient>/<radialGradient> strings
        self.body = []
        self._gid = 0

    # ---- primitives -------------------------------------------------------------
    def add(self, markup):
        self.body.append(markup)

    def rect(self, x, y, w, h, fill, opacity=None):
        o = "" if opacity is None else ' fill-opacity="%s"' % num(opacity)
        self.add('<rect x="%s" y="%s" width="%s" height="%s" fill="%s"%s/>'
                 % (num(x), num(y), num(w), num(h), fill, o))

    def hline(self, y, x1, x2, color, opacity=1.0, width=1):
        # Offset by half a pixel so a 1px rule lands on one pixel row, not two.
        self.add('<path d="M%s %sH%s" stroke="%s" stroke-opacity="%s" stroke-width="%s" fill="none"/>'
                 % (num(x1), num(y + 0.5), num(x2), color, num(opacity), num(width)))

    def gradient(self, stops, x1, y1, x2, y2):
        """Vertical-or-any linear gradient in user space. stops: [(offset, color)]."""
        self._gid += 1
        gid = "g%d" % self._gid
        st = "".join('<stop offset="%s" stop-color="%s"/>' % (num(o), c) for o, c in stops)
        self._grads.append('<linearGradient id="%s" gradientUnits="userSpaceOnUse" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>'
                           % (gid, num(x1), num(y1), num(x2), num(y2), st))
        return "url(#%s)" % gid

    def radial(self, cx, cy, r, color, opacity):
        self._gid += 1
        gid = "g%d" % self._gid
        self._grads.append('<radialGradient id="%s" gradientUnits="userSpaceOnUse" cx="%s" cy="%s" r="%s">'
                           '<stop offset="0" stop-color="%s" stop-opacity="%s"/>'
                           '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
                           % (gid, num(cx), num(cy), num(r), color, num(opacity), color))
        return "url(#%s)" % gid

    # ---- type -------------------------------------------------------------------
    def text(self, face, s, x, y, size, fill, track=0.0, anchor="start", opacity=None, bake=False, skew=0.0):
        """Draw `s` with its baseline at y. Returns the advance width. anchor: start|middle|end.

        fill may be a colour or a gradient reference. Gradients need bake=True so they are
        resolved in image space; plain colours are pooled. skew is degrees of faux italic.
        """
        f = FACES[face]
        w = f.width(s, size, track) - track * size  # no trailing space when aligning
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        o = "" if opacity is None else ' fill-opacity="%s"' % num(opacity)
        wrap_open = wrap_close = ""
        if skew:
            wrap_open = '<g transform="translate(%s %s) skewX(%s) translate(%s %s)">' % (
                num(x), num(y), num(-skew), num(-x), num(-y))
            wrap_close = "</g>"
        if bake:
            self.add('%s<path d="%s" fill="%s"%s/>%s' % (wrap_open, f.baked(s, x, y, size, track), fill, o, wrap_close))
            return w
        k = size / f.upem
        uses, cx = [], x
        for name, adv, dx, dy in f.shape(s):
            gid = "%s%d" % (f.key, f.order.index(name))
            if gid not in self._glyphs:
                self._glyphs[gid] = f.path(name)
            uses.append('<use href="#%s" transform="translate(%s %s) scale(%s -%s)"/>'
                        % (gid, num(cx + dx * k), num(y - dy * k), "%.5f" % k, "%.5f" % k))
            cx += adv * k + track * size
        self.add('%s<g fill="%s"%s>%s</g>%s' % (wrap_open, fill, o, "".join(uses), wrap_close))
        return w

    # ---- icons ------------------------------------------------------------------
    def arrow(self, x, y, size, color):
        """The portfolio's up-right arrow (12x12 viewBox: M2 10 L10 2 M4 2 H10 V8). (x,y) = top-left."""
        k = size / 12.0
        self.add('<path d="M%s %sL%s %sM%s %sH%s V%s" transform="translate(%s %s) scale(%s)" '
                 'stroke="%s" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                 % ("2", "10", "10", "2", "4", "2", "10", "8", num(x), num(y), "%.4f" % k, color))

    def globe(self, cx, cy, r, color):
        """The hero HUD's circled-plus mark."""
        self.add('<g fill="none" stroke="%s" stroke-width="1.1"><circle cx="%s" cy="%s" r="%s"/>'
                 '<path d="M%s %sH%s M%s %sV%s"/></g>'
                 % (color, num(cx), num(cy), num(r), num(cx - r), num(cy), num(cx + r), num(cx), num(cy - r), num(cy + r)))

    # ---- output -----------------------------------------------------------------
    def render(self):
        defs = "".join('<path id="%s" d="%s"/>' % (i, d) for i, d in sorted(self._glyphs.items()))
        defs += "".join(self._grads)
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s" role="img">'
                '<title>%s</title><defs>%s</defs>%s</svg>\n'
                % (num(self.w), num(self.h), num(self.w), num(self.h), _esc(self.label), defs, "".join(self.body)))


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
