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
    cd {{latex_dir}} && latexmk -pdf -interaction=nonstopmode -file-line-error -outdir=../../{{build_dir}} -g main.tex

build-tectonic:
    mkdir -p {{build_dir}}
    cd {{latex_dir}} && tectonic -X compile main.tex --outdir ../../{{build_dir}}

clean-latex:
    rm -rf {{build_dir}} {{latex_dir}}/.latexmk

extract-text from='1' to='5':
    mkdir -p {{build_dir}}
    pdftotext -layout -f {{from}} -l {{to}} {{pdf}} {{build_dir}}/pages-{{from}}-{{to}}.txt

extract-images:
    mkdir -p {{figures_dir}}
    pdfimages -png {{pdf}} {{figures_dir}}/page

ocr image out_base:
    mkdir -p {{build_dir}}
    tesseract {{image}} {{build_dir}}/{{out_base}}
