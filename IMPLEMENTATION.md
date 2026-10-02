# Profile build notes

The README is a catalogue of nine plates. Every plate is drawn by
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
frontier of ORBIT's pipeline, the width of HELIOS's interval, VIGIL-88's latest frame,
the card's corner cut, today. PL. VI has no ember, because nothing on it is lit yet.

**Stages.** The artwork's five layers are the page's grammar. The hero shows all
five: `sketch` (trace), `field` (inferred cloud), `lattice` (computed cells),
`design` (construction geometry), `measure` (instrument). A project's name is drawn
only as far as its evidence goes:

| Stage | Means | Now |
|---|---|---|
| measured | public, and it runs | SIDDHARTHA |
| arranged | public, unfinished | ORBIT, HELIOS, VIGIL-88 |
| inferred | built, not yet public | none |
| sketched | named, no code yet | SPECTRA, SYNCHRO, AETHER |

When that changes, change the stage in the plate function and the legend line in
the README. HELIOS going public, for example, meant `word(..., "design")` in
`helios()`, plus a link and the new stage in its caption.

**Grid.** 1280 wide, 72 margin. The hero sets JAI SAI SIDDHARTHA on one line,
resolving as it is read: JAI sketched, SAI inferred, and SIDDHARTHA kept whole as
the place where computed, arranged and measured add up. The ember sits at the
incentre of the A that SIDDHA and ARTHA share.
Every plate shares `frame()`: crop marks, plate number, title, rule at y=84.

**Labels.** The words between the plates are set in the same alphabet, in
`assets/labels/`: wall labels with no ground (printed on the page, not on a plate),
aligned to the plates' 72 margin so plate and label share one grid. Each label's
full wording is its alt text. In the README every label is a single-line
`<p><picture>…</picture></p>`, linked labels as `<p><a><picture>…</picture></a></p>`.
Keep them on one line: a line that starts `<a…><picture>` and continues is not an
HTML block to CommonMark, and GitHub splits the picture apart. Whitespace beside a
full-width image also adds an empty line box.

## Motion

CSS animation runs inside the `<img>`, because GitHub's CSP allows inline styles.
Script does not. Every plate and label moves, and every motion says something about
its content. Loops below the fold rest for most of each cycle (stillness is the
artwork's first law). Everything stops under `prefers-reduced-motion`, and each
static state is the complete image: no scan bar, no curtain, every observation shown.

| Where | Motion | What it says |
|---|---|---|
| Hero | one-shot reveal: JAI drawn, SAI gathers, SIDDHARTHA's grid, construction and letters arrive; SAI then keeps shimmering | the name becoming; inference is probabilistic |
| II artwork | the displaced eye swings about the nearest mark onto V\*; every sheet's mark lands on its ray and lights; it drifts off | stillness resolves, motion scatters |
| III ORBIT | the ember runs the seven stages and dies at chat; dependency arrows redraw in the one allowed direction | what exists, and the rule that holds it |
| IV HELIOS | observations arrive through the day, a gap marking now; the dashed forecast flows; the title cloud shimmers | a forecast meeting its data |
| V VIGIL-88 | frames arrive one by one; each is answered by an empty ring; the dashed evidence line flows and nothing in it accumulates | a detector that returns nothing, and a verdict not yet reached |
| VI not yet | streams advance and stop short of the line; three clocks run at different rates; the sphere turns | intentions, not yet resolved |
| VII card | a reader scans the rows; light passes through each row's holes as it goes | a hole is where light gets through |
| VIII trace | a pen redraws the year to today, then rests | the record, replayed |
| IX end | the hand keeps redrawing the sentence; the room sways | it never reaches the last stage |
| Statement | the five verbs light in reading order; the key's A performs each stage | the grammar of the page |
| Labels, links | rules draw and words set as they arrive; arrows nudge toward their links | where to go next |

The ember breathes wherever it appears. Keyframes live next to the plate that uses
them; the shared ones are `DRAW`, `EMBER`, `REDRAW`, `SHIMMER` and `NUDGE`.

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
| Hero name and its parts | `NAME`, `PARTS`, `hero()` |
| The artwork plate | `artwork()` |
| ORBIT pipeline, what is built | `ORBIT_STAGES`, `ORBIT_BUILT` |
| HELIOS facts, schematic | `helios()` |
| VIGIL-88 lanes and facts | `vigil()` |
| Unbuilt projects | `OPEN` |
| The punched card | `TOOLS` (columns), `WORKS` (rows, with the tools each is made with) |
| Closing sentence | `SENTENCE` |
| Label wording | `LABELS`, `statement()`, `end_label()`, `LINKS` (then the matching alt text in README.md) |

The card's rows must stay evidence: a tool goes in a work's set only if that
work's repository or record shows it. Tools without a public work are listed in
the README caption under the card instead.

## Sources for the facts on the page

- ORBIT: the repository README roadmap (M0–M7 implemented, not production-ready, 24
  ADRs, import-linter contracts), `docs/decisions/0022` and
  `backend/src/orbit/application/{retrieval,answering}` for retrieval and grounded
  answering, and `web/package.json`. The README header and its M6 row still say
  chat is not started; the code and ADR say it is implemented, and the plate follows
  them. Not run end to end by whoever drew this.
- SIDDHARTHA: the `miracle` README (five layers, V\*, four modules, no framework,
  runs from `file://`).
- VIGIL-88: its README, `docs/LIMITATIONS.md` (P0 foundation, nothing detected yet),
  `docs/architecture/` (ten documents) and `pyproject.toml`.
- HELIOS: author-supplied (XGBoost, hold-out R² 0.856, calibrated intervals, a
  one-second calculator and a fourteen-view console). The chart is a schematic.
- Gravity Playground, Travelease, PETPONKS, and the tool list: the portfolio brief
  and the artwork's content record.
- Links: the LinkedIn and Behance accounts listed on the GitHub profile.

## Publish

The profile README is `Siddhuperuri/Siddhuperuri` on the default branch. After the
first push, run the `trace` workflow once from the Actions tab to confirm it can
write. The workflow commits to `main`, so pull before pushing local changes.
