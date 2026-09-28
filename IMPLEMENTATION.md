# Profile build notes

The README is a catalogue of eight plates. Every plate is drawn by
`tools/build_assets.py`; nothing in `assets/` is edited by hand. Change the
source, then rebuild.

## Rebuild

```
python tools/build_assets.py                 # all plates, trace from tools/trace.json
GH_TOKEN=$(gh auth token) python tools/build_assets.py --fetch   # refresh the trace data too
python tools/build_assets.py hero orbit      # only the named plates
```

Standard library only: no pip install, no font download.

## The system

**Type.** Every letter is drawn with the stroke alphabet of
[SIDDHARTHA](https://github.com/Siddhuperuri/miracle), ported from its
`js/glyphs.js` into `tools/strokes.py`: strokes on a cap-height-1 grid, true
arcs, survey ticks on free ends. GitHub serves README images with
`default-src 'none'`, so fonts never load inside an SVG. A typeface made of
geometry sidesteps that, and it is the same alphabet the artwork is built from.
Micro-type is pooled: each glyph is defined once in `<defs>` and placed with `<use>`.

**Colour.** Ground, paper, ember: the artwork's palette. Paper is the only text
colour. Ember marks the one curious thing on each plate: the shared A, V\*, the
frontier of ORBIT's pipeline, the width of HELIOS's interval, the card's corner cut,
today. PL. V has no ember, because nothing on it is lit yet.

**Stages.** The artwork's five layers are the page's grammar. The hero shows all
five: `sketch` (trace), `field` (inferred cloud), `lattice` (computed cells),
`design` (construction geometry), `measure` (instrument). A project's name is drawn
only as far as its evidence goes:

| Stage | Means | Now |
|---|---|---|
| measured | public, and it runs | SIDDHARTHA |
| arranged | public, unfinished | ORBIT |
| inferred | built, not yet public | HELIOS |
| sketched | named, no code yet | SPECTRA, SYNCHRO, AETHER |

When that changes, change the stage in the plate function and the legend line in
the README. HELIOS going public, for example, means `word(..., "design")` in
`helios()`, plus a link and the new stage in its caption.

**Grid.** 1280 wide, 72 margin; the hero's five columns (227 px) set the rhythm.
Every plate shares `frame()`: crop marks, plate number, title, rule at y=84.

## Motion

CSS animation runs inside the `<img>`, because the same CSP allows inline styles.
Script does not. Everything stops under `prefers-reduced-motion`, and each plate is
designed so its static state is the meaningful one.

- **Hero:** a one-shot reveal in the order a letter becomes: sketched, inferred,
  computed, arranged, measured. Then the ember starts to breathe.
- **ORBIT:** the ember pulse runs through the five built stages and dies at index.
  At rest it sits on index, the frontier.
- **Last plate:** the sentence sways very slowly ("the room breathes").
- Every ember ring breathes. Nothing else moves.

## Trace

`.github/workflows/trace.yml` runs daily. It fetches the contribution calendar
from the GraphQL API with the workflow's own `GITHUB_TOKEN`, rewrites
`tools/trace.json` and the two trace plates, and commits only if they changed.
Run it by hand from the Actions tab, or locally with `--fetch`. No third-party
stats service is involved, and the numbers on the plate are exactly the API's.

## Editing content

| What | Where in `tools/build_assets.py` |
|---|---|
| Palette | `BASE` |
| Hero columns, verbs | `STAGES`, `ROWS`, `hero()` |
| The artwork plate | `artwork()` |
| ORBIT pipeline, what is built | `ORBIT_STAGES`, `ORBIT_BUILT` |
| HELIOS facts, schematic | `helios()` |
| Unbuilt projects | `OPEN` |
| The punched card | `TOOLS` (columns), `WORKS` (rows, with the tools each is made with) |
| Closing sentence | `SENTENCE` |

The card's rows must stay evidence: a tool goes in a work's set only if that
work's repository or record shows it. Tools without a public work are listed in
the README caption under the card instead.

## Sources for the facts on the page

- ORBIT: the repository README (M0–M4 built, retrieval and chat not yet, 24 ADRs,
  import-linter contracts) and `web/package.json`.
- SIDDHARTHA: the `miracle` README (five layers, V\*, four modules, no framework,
  runs from `file://`).
- HELIOS: author-supplied (XGBoost, hold-out R² 0.856, calibrated intervals, a
  one-second calculator and a fourteen-view console). The chart is a schematic.
- Gravity Playground, Travelease, PETPONKS, and the tool list: the portfolio brief
  and the artwork's content record.
- Links: the LinkedIn and Behance accounts listed on the GitHub profile.

## Publish

The profile README is `Siddhuperuri/Siddhuperuri` on the default branch. After the
first push, run the `trace` workflow once from the Actions tab to confirm it can
write. The workflow commits to `main`, so pull before pushing local changes.
