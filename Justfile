set shell := ["bash", "-eu", "-o", "pipefail", "-c"]
set dotenv-load := false

pdf := "simulatingcomput00myro_1-1.pdf"
latex_dir := "docs/latex"
build_dir := "build"
figures_dir := "docs/latex/figures"

default:
    @just --list

dev:
    nix develop --no-warn-dirty --unset-env-var LC_ALL --unset-env-var LANG --unset-env-var LANGUAGE

build-latex:
    mkdir -p {{build_dir}}
    mkdir -p {{build_dir}}/chapters
    cd {{latex_dir}} && latexmk -xelatex -interaction=nonstopmode -file-line-error -outdir=../../{{build_dir}} -g main.tex

build-tectonic:
    mkdir -p {{build_dir}}
    cd {{latex_dir}} && tectonic -X compile main.tex --outdir ../../{{build_dir}}

watch-latex:
    mkdir -p {{build_dir}} {{build_dir}}/chapters
    cd {{latex_dir}} && latexmk -xelatex -interaction=nonstopmode -file-line-error -outdir=../../{{build_dir}} -pvc -g main.tex

clean-latex:
    rm -rf {{build_dir}} {{latex_dir}}/.latexmk

extract-text from='1' to='5':
    mkdir -p {{build_dir}}
    pdftotext -layout -f {{from}} -l {{to}} {{pdf}} {{build_dir}}/pages-{{from}}-{{to}}.txt

extract-images:
    mkdir -p {{figures_dir}}
    pdfimages -png {{pdf}} {{figures_dir}}/page

ocr-page page dpi='400' psm='6':
    mkdir -p {{build_dir}}/ocr
    pp=$(printf "%03d" {{page}}); \
      pdftoppm -f {{page}} -l {{page}} -r {{dpi}} -png {{pdf}} {{build_dir}}/ocr/page; \
      if command -v magick >/dev/null; then \
        magick {{build_dir}}/ocr/page-$${pp}.png -colorspace Gray -deskew 40% -normalize -sharpen 0x1 {{build_dir}}/ocr/page-$${pp}-clean.png; \
        tesseract {{build_dir}}/ocr/page-$${pp}-clean.png {{build_dir}}/ocr/page-$${pp} -l eng --oem 1 --psm {{psm}} -c preserve_interword_spaces=1; \
      else \
        tesseract {{build_dir}}/ocr/page-$${pp}.png {{build_dir}}/ocr/page-$${pp} -l eng --oem 1 --psm {{psm}} -c preserve_interword_spaces=1; \
      fi

ocr-range from to dpi='400' psm='6':
    mkdir -p {{build_dir}}/ocr
    for p in $(seq {{from}} {{to}}); do \
      pp=$$(printf "%03d" $$p); \
      pdftoppm -f $$p -l $$p -r {{dpi}} -png {{pdf}} {{build_dir}}/ocr/page; \
      if command -v magick >/dev/null; then \
        magick {{build_dir}}/ocr/page-$$pp.png -colorspace Gray -deskew 40% -normalize -sharpen 0x1 {{build_dir}}/ocr/page-$$pp-clean.png; \
        tesseract {{build_dir}}/ocr/page-$$pp-clean.png {{build_dir}}/ocr/page-$$pp -l eng --oem 1 --psm {{psm}} -c preserve_interword_spaces=1; \
      else \
        tesseract {{build_dir}}/ocr/page-$$pp.png {{build_dir}}/ocr/page-$$pp -l eng --oem 1 --psm {{psm}} -c preserve_interword_spaces=1; \
      fi; \
    done

ocr image out_base:
    mkdir -p {{build_dir}}
    tesseract {{image}} {{build_dir}}/{{out_base}}
