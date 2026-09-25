# Profile build notes

The README is assembled from generated SVG plates. Nothing is hand-edited in
`assets/` — change the source and rebuild.

## Rebuild

```
pip install fonttools brotli uharfbuzz
python tools/build_assets.py
```

`tools/typeset.py` fetches Anton, Geist and Geist Mono (OFL, cached in `tools/.fontcache/`,
git-ignored) and converts every string to outlines. `tools/build_assets.py`
holds the design tokens, grid and compositions, and writes a light and a dark
variant of each plate.

## Where the look comes from

The palette, type and motifs follow the shipped tokens of the Portfolio2 site so
the profile and the portfolio read as one identity: ink `#0A0A0A`, paper
`#F5F5F5`, red `#FF3D2E`, hairline rules, Geist + Geist Mono + Anton, mono
eyebrows. The hanging badge, skills marquee, IST readout, role line, statement
and four process steps are all taken from it. The ring-and-dot mark comes from
the WebGL portfolio's loader; its cyan survives only as a *status* signal (the
pulsing dot on in-development work), never as a second brand colour.

Note: Portfolio2's `DESIGN_LANGUAGE.md` still says amber; its token file says
red. The token file is the one followed here.

## Why type is outlined

GitHub serves README images with `Content-Security-Policy: default-src 'none'`
and no `font-src`. Webfonts do not load, and neither do base64 `@font-face`
rules embedded in the SVG — both silently fall back to the visitor's default
font. Outlines are the only way to guarantee the typography renders as designed.
A glyph pool (`<defs>` + `<use>`) keeps the files small despite this.

## Motion

CSS animation inside the SVG runs on GitHub — the same CSP that blocks fonts
allows `style-src 'unsafe-inline'`. Script does not run, and SMIL is avoided
because it ignores `prefers-reduced-motion`.

- **Hero** plays a one-shot staged reveal (rules draw on, type rises) and the
  ID badge swings in on its lanyard, settling over ~5s into a barely-there sway.
- **Marquee** scrolls the tool list slowly (90s per pass).
- **Cards and the Helios panel** loop slowly instead, because a one-shot would
  finish long before the reader scrolls to them. The loops are semantic — a dot
  orbiting ORBIT's rings, Helios's rays turning once every 90s, the pipeline
  lighting up step by step — never decoration for its own sake.
- Every animation is disabled under `prefers-reduced-motion: reduce`, and the
  static end state is what renders.

Keyframes live next to the composition that uses them: `hero()` for the reveal,
`CARD_CSS` for the motifs, `now()` for the pipeline. To strip motion entirely,
make `anim()` return `""`.

## Editing content

| What | Where in `tools/build_assets.py` |
|---|---|
| Colours, accent | `THEMES` |
| Capability columns | `DISCIPLINES` |
| Project cards | `PROJECTS` (and the `motif_*` functions) |
| Helios panel | `now()` |
| Name, role, statement | `hero()`, `ROLE`, `STATEMENT` |
| Badge | `_badge()` |
| Tool list | `SKILLS` (marquee) |
| Process steps | `STEPS` |

Canvas is 1280 wide with a 72 margin and a 12-column grid; cards are 640×420.

## Before publishing

Replace in `README.md`:

```
YOUR_PORTFOLIO_URL
YOUR_LINKEDIN_URL
YOUR_BEHANCE_URL
YOUR_EMAIL
```

Project cards are deliberately unlinked — those repos do not exist yet. To link
one once it does, wrap its `<picture>` block:

```html
<a href="https://github.com/Siddhuperuri/helios"><picture>...</picture></a>
```

## Publish

The profile README is `Siddhuperuri/Siddhuperuri` on the default branch.

```
git add -A && git commit -m "Rebuild profile as a generated design system" && git push
```
