# Simulating Computer Systems

Workspace for reconstructing `simulatingcomput00myro_1-1.pdf` into editable LaTeX,
plus Python queueing simulations.

## Quick start

- Load the Nix, devenv, and direnv environment:
  - `direnv allow`, then `just setup`
  - `just dev` opens the environment without direnv.
- Build LaTeX (latexmk):
  - `just build-latex`
- Build LaTeX (tectonic):
  - `just build-tectonic`

## Layout

- `docs/latex/`: LaTeX project (entry: `main.tex`)
- `docs/latex/chapters/`: Chapter files (one per chapter/section)
- `docs/latex/figures/`: Extracted images/figures
- `docs/latex/build/`: Build output (ignored)
- `src/`, `tests/`: Python simulations and tests

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

## Python development

`just run` starts the single-server queue simulation from `scs.sim1`.
`just check` runs its tests and the installed CLI. `just update` refreshes the
Nix and Python dependency locks.

The extraction and OCR recipes require the original PDF in the repository root
as `simulatingcomput00myro_1-1.pdf`. That input is not included in this checkout.
