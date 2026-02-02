# Simulating Computer Systems

Workspace for reconstructing `simulatingcomput00myro_1-1.pdf` into editable LaTeX,
plus a small Python project scaffold.

## Quick start

- Enter dev shell (Nix):
  - `just dev`
- Build LaTeX (latexmk):
  - `just build-latex`
- Build LaTeX (tectonic):
  - `just build-tectonic`

## Layout

- `docs/latex/`: LaTeX project (entry: `main.tex`)
- `docs/latex/chapters/`: Chapter files (one per chapter/section)
- `docs/latex/figures/`: Extracted images/figures
- `docs/latex/build/`: Build output (ignored)
- `src/`, `tests/`: Python project scaffold

## Extraction helpers

- Text extraction (first 5 pages):
  - `just extract-text`
- Image extraction:
  - `just extract-images`
- OCR a single image:
  - `just ocr image=docs/latex/figures/page-000.png out_base=page-000`

## Notes

- If `tectonic` cannot find a package, use `latexmk` (TeX Live full) for
  maximum compatibility.
- The dev shell includes `poppler_utils` (pdftotext/pdfimages) and `tesseract`
  for OCR.
