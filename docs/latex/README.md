# LaTeX rebuild workspace

This folder contains a lightweight LaTeX scaffold for reconstructing
simulatingcomput00myro_1-1.pdf.

## Layout

- main.tex: entry point
- preamble.tex: shared packages and formatting
- chapters/: one file per chapter/section
- figures/: extracted images and diagrams
- ../../build/: generated output (ignored, in repo root)

## Build

- XeLaTeX/LuaLaTeX is used for system fonts. If a font is missing, the build
  falls back to TeX Gyre/Libertinus.

- latexmk (TeX Live):
  latexmk -xelatex -interaction=nonstopmode -file-line-error -outdir=../../build main.tex

- tectonic (bundled engine):
  tectonic -X compile main.tex --outdir ../../build

## Extraction helpers

- pdftotext (text extraction):
  pdftotext -layout -f 1 -l 5 ../simulatingcomput00myro_1-1.pdf ../../build/pages.txt

- pdfimages (figure extraction):
  pdfimages -png ../simulatingcomput00myro_1-1.pdf figures/page

- tesseract (OCR on images if the PDF is scanned):
  tesseract figures/page-000.png ../../build/page-000

- OCR (recommended, higher quality):
  just ocr-page page=15
  just ocr-range from=13 to=20
