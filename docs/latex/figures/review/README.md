# Complete figure style review

`../../../..` is the repository root. From that directory:

```sh
./docs/latex/review_figures.py check
./docs/latex/review_figures.py build --dry-run
./docs/latex/review_figures.py build --yes
```

The output is `build/all-figures-review/comparison.pdf`: **83 comparison pages**
covering **71 numbered figures and 6 numbered tables**, including continuation
parts. Each page identifies the original printed and physical PDF page, its
representation, and whether visual approval is still pending.

## Source inputs

- `inventory.json`: canonical numbered-entry inventory and source references.
- `original-crops.json`: reproducible scan-crop recipes, for comparison only.
- `fig-*.tex`: native schematic fragments.
- `style.tex`: shared styles.
- `../tikz-preview/`: the canonical CPU and Ethernet-event prototypes.

The reference side uses 43 existing figure assets and 39 reference crops for
the other 34 numbered entries, including their continuation parts. Figure 6.3
has a complete crop including its
seven-line timing key; its older diagram-only asset remains unchanged.
Generated crops can be recreated from the original PDF using the retained
coordinates. They are not book-page reconstruction assets.
Each build regenerates every distinct reference crop, so changing the scan or
a crop recipe cannot silently reuse an obsolete cached image.

## Current proposal, not approval

The common schematic style uses regular body text, bold headings, approximately
1.2 pt frames and 1.3 pt connections, with slightly pointed rounded triangular
arrowheads. The CPU prototype retains its shifted shadow edges. Short
bidirectional links use shorter arrowheads to avoid collisions.

There are 31 native schematic previews. Existing native plots with verified
tabulated values, tables, code listings and displays remain editable. Multipart
listings use the page-aligned sources; Figure 7.4 has two parts on the same
original printed page 208.

The 14 retained quantitative raster previews are Figures 1.5, 3.4, 4.1–4.6,
4.8, 5.5, 6.4, 6.10, 7.5 and 9.2. Their comparison copies use 16 gray levels
with Floyd–Steinberg dithering and are explicitly labelled **not vector
reconstructions**. No unverified numerical curves have been invented.

The manifest records per-part output paths and protected input hashes. A
successful build, complete inventory or visual thumbnail review does not mean
the user has approved the style, nor establish character-perfect fidelity.
The existing book PDF and original source images are not overwritten.
