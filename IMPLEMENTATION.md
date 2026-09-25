# Profile build notes

The README is assembled from generated SVG plates. Nothing is hand-edited in
`assets/` — change the source and rebuild.

## Rebuild

```
pip install fonttools brotli uharfbuzz
python tools/build_assets.py
```

`tools/typeset.py` fetches Anton + Inter (OFL, cached in `tools/.fontcache/`,
git-ignored) and converts every string to outlines. `tools/build_assets.py`
holds the design tokens, grid and compositions, and writes a light and a dark
variant of each plate.

## Why type is outlined

GitHub serves README images with `Content-Security-Policy: default-src 'none'`
and no `font-src`. Webfonts do not load, and neither do base64 `@font-face`
rules embedded in the SVG — both silently fall back to the visitor's default
font. Outlines are the only way to guarantee the typography renders as designed.
A glyph pool (`<defs>` + `<use>`) keeps the files small despite this.

## Editing content

| What | Where in `tools/build_assets.py` |
|---|---|
| Colours, accent | `THEMES` |
| Capability columns | `DISCIPLINES` |
| Project cards | `PROJECTS` (and the `motif_*` functions) |
| Helios panel | `now()` |
| Name, strapline, tags | `hero()` |

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
