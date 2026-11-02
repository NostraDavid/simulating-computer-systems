# Printed-page-aligned review edition

This separate, editable proof covers printed pages **1–292** of the book.
Original physical PDF pages 23–314 correspond to those printed pages. It does
not include covers, Roman-numbered preliminaries, archive wrappers or endpapers.
The existing `build/simulating-computer-systems.pdf` remains unchanged.

## Outputs

- `build/all-figures-review/comparison.pdf`: every numbered figure and table,
  original versus reconstruction, including continuation parts.
- `build/page-aligned/simulating-computer-systems-page-aligned.pdf`: the
  editable 292-page body proof.
- `build/page-layout-review/comparison.pdf`: 292 original/proof page pairs.
- The adjacent figure manifest and page audit document representation types,
  source pages and machine-generated review signals.

Paths above are relative to the repository root. Review PDFs intentionally
include scanned reference material on the original side. The editable book
proof must not read or embed original scanned pages.

## Build

From the repository root, with the existing project environment available:

```sh
direnv exec . bash -c 'cd docs/latex && latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -jobname=simulating-computer-systems-page-aligned -outdir=../../build/page-aligned page-aligned/main.tex'
./docs/latex/review_figures.py check
./docs/latex/review_figures.py build --yes
```

For the page comparison, prepare original-page review renders once, then build:

```sh
./docs/latex/review_pages.py prepare-original --yes
./docs/latex/review_pages.py check
./docs/latex/review_pages.py build --yes
```

Do not repeat `prepare-original` when its validated render cache already exists.
Both review scripts have read-only `check` and mutation-free `--dry-run` modes.
Their executable uv shebangs use isolated, pinned script dependencies; do not
replace the project's Python environment to run them.

## Pagination contract

Every source-page boundary is explicit:

```tex
\OriginalPage{7}{1.2\quad Representing Work}
\noindent necessarily have to be Poisson: ...
```

The macro clears the preceding page and checks the actual counter. It never
resets folios to conceal an overflow. The combined entry point also checks the
end of printed page 292. Chapter sources contain no page-counter resets.
Page 7's header and opening text are a specific regression check.

## What is and is not verified

The combined proof has 292 consecutive pages. Its build recorder excludes the
original scan; text, equations, tables and code remain editable. All proof
pages have been rendered for a thumbnail layout inspection, and extracted
words stay inside page rectangles. These checks do **not** establish exact
transcription, identical within-page line wrapping or pixel-level equivalence.

The trial geometry is 6.25 × 9 inches with TeX Gyre Schola body text. Fonts,
spacing, diagram proportions and some within-page placements differ from the
scan. In particular, the page 8 sampling diagrams remain visual review items.
Roman front matter remains outside this proof.

The figure comparison includes 71 figures and 6 tables. Schematics use native
TikZ, while 14 quantitative plots retain explicitly labelled 16-gray
Floyd–Steinberg raster previews. No unverified curve data has been invented.
The page-aligned proof still contains a mixture of existing figure assets and
canonical redraws: visual approval is not implied by inclusion in either PDF.

The page audit uses OCR, text anchors, bounding boxes and token overlap as
heuristics. Missing selectable labels in raster figures, formula extraction,
multi-column indexes and OCR errors can trigger warnings without omitted book
content. Conversely, a high overlap score cannot prove content order or symbol
accuracy. Use the paired pages for human review before approving a 1:1 edition.
