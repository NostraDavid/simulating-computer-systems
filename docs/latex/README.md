# LaTeX rebuild workspace

This folder rebuilds `simulatingcomput00myro_1-1.pdf` from editable LaTeX text,
mathematics, tables, source code, and individual figures. It must not include
complete scan pages or the original PDF in the output.

## Layout

- main.tex: rebuilt book entry point
- preamble.tex: shared packages and formatting
- chapters/: editable chapter files
- listings/: transcribed original C source files
- figures/: extracted images and diagrams
- ../../build/: generated output (ignored, in repo root)

## Build

- Run the following from `docs/latex`, with the project environment loaded.
- The build uses only the chapter sources and figure assets in this folder;
  the original PDF is needed only for extraction and verification.
- XeLaTeX is used, with TeX Gyre/Libertinus font fallbacks.

- latexmk (TeX Live):
  latexmk -xelatex -interaction=nonstopmode -file-line-error -jobname=simulating-computer-systems -outdir=../../build main.tex

- tectonic (bundled engine):
  tectonic -X compile main.tex --outdir ../../build
  mv ../../build/main.pdf ../../build/simulating-computer-systems.pdf

Both commands produce `../../build/simulating-computer-systems.pdf`.
The rebuilt book has its own pagination. Original index references must be
distinguished from the rebuilt page numbers.

See [reconstruction status](RECONSTRUCTION.md) for coverage and verification.

## Original-page and figure review

A separate [printed-page-aligned proof](page-aligned/README.md) covers printed
pages 1–292, alongside complete figure/table and page-layout comparisons. These
are review outputs, not a claim of pixel-identical typography, and do not replace
the existing book PDF. The original scan appears only in comparison artifacts.

## Extraction helpers

- pdftotext (text extraction):
  pdftotext -layout -f 1 -l 5 ../../simulatingcomput00myro_1-1.pdf ../../build/pages.txt

- pdfimages (figure extraction):
  pdfimages -png ../../simulatingcomput00myro_1-1.pdf figures/page

- tesseract (OCR on images if the PDF is scanned):
  tesseract figures/page-000.png ../../build/page-000

- OCR (recommended, higher quality):
  just ocr-page 15 72
  just ocr-range 13 20 72

The supplied scan has unusually large PDF page dimensions. For inspection and
figure extraction, prefer `pdftoppm -scale-to 2400`; do not render it at an
ordinary print-resolution DPI without accounting for those dimensions.
