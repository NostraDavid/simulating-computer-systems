#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "click==8.5.0", "pydantic==2.14.2", "pytest==9.2.0",
#   "pytest-cov==7.1.0", "structlog==26.1.0",
# ]
# ///
"""Build an auditable, comparison-only figure review without changing book sources."""

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess as sp
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import click
import pytest
import structlog as sl
import structlog.stdlib as log
from pydantic import BaseModel, ConfigDict

logger = log.get_logger(__name__)
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "build/all-figures-review"
LATEX = ROOT / "docs/latex"
SOURCE_PDF = ROOT / "simulatingcomput00myro_1-1.pdf"
INPUTS = LATEX / "figures/review"


class Entry(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    kind: str
    chapter: int
    number: int
    caption_tex: str
    source_tex: str
    line_start: int
    line_end: int
    representation: list[str]
    type: str
    assets: list[str]
    original_pdf_pages: list[int]
    original_printed_pages: list[int]
    comparison_sources: list[dict[str, object]] = []


class Crop(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    printed_page: int
    source_pdf_page: int
    image_path: str
    source_render_dimensions_px: tuple[int, int]
    crop_xyxy_px: tuple[int, int, int, int]


class InputError(Exception):
    pass


def strip_commands(text: str) -> str:
    """Remove caption and label commands, including balanced nested braces."""
    pattern = re.compile(r"\\(?:caption|label)\s*\{")
    while match := pattern.search(text):
        depth = 1
        index = match.end()
        while index < len(text) and depth:
            if text[index] == "{" and (index == 0 or text[index - 1] != "\\"):
                depth += 1
            elif text[index] == "}" and (index == 0 or text[index - 1] != "\\"):
                depth -= 1
            index += 1
        if depth:
            raise InputError("Unbalanced caption or label")
        text = text[: match.start()] + text[index:]
    return text


def safe_path(path: str, base: Path = ROOT) -> Path:
    result = (base / path).resolve()
    if not result.is_relative_to(ROOT.resolve()):
        raise InputError(f"Path escapes repository: {path}")
    return result


def inventory() -> list[Entry]:
    data = json.loads((INPUTS / "inventory.json").read_text(encoding="utf-8"))
    entries = [Entry.model_validate(e) for e in data["entries"]]
    ids = [e.id for e in entries]
    if (
        len(entries) != 77
        or len(set(ids)) != 77
        or sum(e.kind == "figure" for e in entries) != 71
        or sum(e.kind == "table" for e in entries) != 6
    ):
        raise InputError("Inventory must contain 71 unique figures and 6 unique tables")
    recipes = crop_recipes()
    for e in entries:
        if (
            e.id != f"{e.kind} {e.chapter}.{e.number}"
            or not e.original_pdf_pages
            or len(e.original_pdf_pages) != len(e.original_printed_pages)
        ):
            raise InputError(f"Invalid inventory entry: {e.id}")
        safe_path(e.source_tex)
        for p in e.assets:
            safe_path(p, LATEX)
        for s in e.comparison_sources:
            path = safe_path(str(s["path"]))
            if s.get("kind") == "original_crop":
                recipe = recipes.get(str(s["path"]))
                if (
                    recipe is None
                    or recipe.id != e.id
                    or recipe.source_pdf_page != s.get("source_pdf_page")
                    or recipe.printed_page != s.get("printed_page")
                ):
                    raise InputError(f"Missing or mismatched crop recipe: {e.id}")
            elif not path.is_file():
                raise InputError(f"Missing comparison asset: {path}")
    return entries


def crop_recipes() -> dict[str, Crop]:
    data = json.loads((INPUTS / "original-crops.json").read_text(encoding="utf-8"))
    recipes: dict[str, Crop] = {}
    for value in data["crops"]:
        crop = Crop.model_validate(value)
        path = safe_path(crop.image_path)
        width, height = crop.source_render_dimensions_px
        left, top, right, bottom = crop.crop_xyxy_px
        if (
            not path.is_relative_to((OUT / "originals").resolve())
            or crop.image_path in recipes
            or crop.source_pdf_page < 1
            or not (0 <= left < right <= width and 0 <= top < bottom <= height)
        ):
            raise InputError(f"Invalid crop recipe: {crop.image_path}")
        recipes[crop.image_path] = crop
    return recipes


def render_crop(crop: Crop, destination: Path) -> None:
    """Regenerate one reference in isolation; reject unexpected page dimensions."""
    with tempfile.TemporaryDirectory(prefix="review-crop-") as tmp:
        prefix = Path(tmp) / "page"
        result = run(
            [
                "pdftoppm",
                "-f",
                str(crop.source_pdf_page),
                "-l",
                str(crop.source_pdf_page),
                "-singlefile",
                "-scale-to",
                "2000",
                "-png",
                str(SOURCE_PDF),
                str(prefix),
            ]
        )
        if result.returncode:
            raise InputError(
                f"Cannot render source page {crop.source_pdf_page}: {result.stderr}"
            )
        page = prefix.with_suffix(".png")
        dimensions = run(["magick", "identify", "-format", "%w %h", str(page)])
        expected = " ".join(map(str, crop.source_render_dimensions_px))
        if dimensions.returncode or dimensions.stdout.strip() != expected:
            raise InputError(
                f"Unexpected render dimensions for {crop.id}: {dimensions.stdout.strip()!r}, expected {expected}"
            )
        left, top, right, bottom = crop.crop_xyxy_px
        image = Path(tmp) / "crop.png"
        result = run(
            [
                "magick",
                str(page),
                "-crop",
                f"{right - left}x{bottom - top}+{left}+{top}",
                "+repage",
                str(image),
            ]
        )
        if result.returncode:
            raise InputError(f"Cannot crop {crop.id}: {result.stderr}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(image, destination)


def run(
    args: list[str], cwd: Path = ROOT, timeout: int = 180
) -> sp.CompletedProcess[str]:
    return sp.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )


def protected_hashes() -> dict[str, str]:
    files = (
        list((LATEX / "chapters").glob("*.tex"))
        + list((LATEX / "page-aligned/chapters").glob("*.tex"))
        + [INPUTS / "inventory.json", INPUTS / "original-crops.json"]
        + [
            LATEX / "main.tex",
            LATEX / "preamble.tex",
            ROOT / "Justfile",
            SOURCE_PDF,
            ROOT / "build/simulating-computer-systems.pdf",
        ]
        + list((LATEX / "figures").rglob("*.png"))
    )
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
        if p.is_file()
    }


def extract(e: Entry) -> list[str]:
    lines = (
        safe_path(e.source_tex).read_text(encoding="utf-8").splitlines(keepends=True)
    )
    text = "".join(lines[e.line_start - 1 : e.line_end])
    # Continuation floats are deliberately outside the inventory block boundaries.
    if e.id in ("figure 2.2", "figure 5.4"):
        tail = "".join(lines[e.line_end :])
        match = re.search(
            r"\\addtocounter\{figure\}\{-1\}.*?\\end\{figure\}", tail, re.DOTALL
        )
        if match:
            text += match.group()
    blocks = re.findall(
        r"\\begin\{(verbatim|lstlisting)\}(?:\[[^\]]*\])?(.*?)\\end\{\1\}",
        text,
        re.DOTALL,
    )
    if blocks:
        return ["\\begin{verbatim}" + body + "\\end{verbatim}" for _, body in blocks]
    text = re.sub(r"\\begin\{(?:figure|table)\}(?:\[[^]]*\])?", "", text)
    text = re.sub(r"\\end\{(?:figure|table)\}", "", text)
    return [strip_commands(text)]


def tex_escape(text: str) -> str:
    return "".join(
        {
            "\\": r"\textbackslash{}",
            "{": r"\{",
            "}": r"\}",
            "$": r"\$",
            "&": r"\&",
            "%": r"\%",
            "_": r"\_",
            "#": r"\#",
            "^": r"\textasciicircum{}",
            "~": r"\textasciitilde{}",
        }.get(c, c)
        for c in text
    )


def slug(e: Entry) -> str:
    return f"{e.kind}-{e.chapter}-{e.number}"


ALIGNED_PAGES = {
    "figure 2.2": [(44, 1), (45, 1)],
    "figure 5.4": [(138, 1), (139, 1)],
    "figure 6.9": [(178, 1), (179, 1), (180, 1), (181, 1)],
    "figure 7.4": [(208, 2)],
}


def aligned_parts(e: Entry) -> list[str] | None:
    """Use only uniquely caption-matched figures within verified page blocks."""
    wanted = ALIGNED_PAGES.get(e.id)
    if wanted is None or [page for page, _ in wanted] != e.original_printed_pages:
        return None
    path = LATEX / "page-aligned/chapters" / Path(e.source_tex).name
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    pages = list(re.finditer(r"\\OriginalPage\{(\d+)\}", text))
    result: list[str] = []
    for number, count in wanted:
        matches = [i for i, match in enumerate(pages) if int(match.group(1)) == number]
        if len(matches) != 1:
            return None
        index = matches[0]
        block = text[
            pages[index].end() : pages[index + 1].start()
            if index + 1 < len(pages)
            else len(text)
        ]
        figures = re.findall(
            r"\\begin\{figure\}(?:\[[^]]*\])?.*?\\end\{figure\}", block, re.DOTALL
        )
        figures = [
            figure
            for figure in figures
            if re.search(r"\\caption\*?\{", figure)
            and e.caption_tex in figure[figure.rfind("\\caption") :]
        ]
        if len(figures) != 1:
            return None
        listings = re.findall(
            r"\\begin\{(verbatim|lstlisting)\}(?:\[[^\]]*\])?(.*?)\\end\{\1\}",
            figures[0],
            re.DOTALL,
        )
        if len(listings) != count:
            return None
        result.extend(
            "\\begin{verbatim}" + body + "\\end{verbatim}" for _, body in listings
        )
    return result


def source_parts(e: Entry) -> list[str]:
    aligned = aligned_parts(e)
    if aligned is not None:
        return aligned
    blocks = extract(e)
    n = len(e.original_pdf_pages)
    if (
        len(blocks) == 1
        and n > 1
        and blocks[0].startswith("\\begin{verbatim}")
        and blocks[0].endswith("\\end{verbatim}")
    ):
        body = (
            blocks[0][len("\\begin{verbatim}") : -len("\\end{verbatim}")]
            .strip("\n")
            .splitlines()
        )
        return [
            "\\begin{verbatim}\n"
            + "\n".join(body[i * len(body) // n : (i + 1) * len(body) // n])
            + "\n\\end{verbatim}"
            for i in range(n)
        ]
    return blocks


def latex_header() -> str:
    return r"""\documentclass[border=3pt,varwidth=15cm]{standalone}
\usepackage{fontspec,graphicx,tikz,pgfplots,booktabs,amsmath,amssymb,listings,multicol,xcolor}
\usetikzlibrary{calc,patterns,patterns.meta,arrows.meta,positioning,decorations.pathreplacing,decorations.text,shapes.geometric}
\pgfplotsset{compat=1.18}
\setmainfont{TeX Gyre Heros}\setsansfont{TeX Gyre Heros}\setmonofont{TeX Gyre Cursor}
\newfontfamily\axisfont{TeX Gyre Heros}
\input{figures/review/style.tex}
\begin{document}
"""


def make_plan(entries: list[Entry]) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    for e in entries:
        aligned = aligned_parts(e)
        parts = aligned if aligned is not None else source_parts(e)
        count = max(len(parts), len(e.original_pdf_pages))
        for i in range(count):
            page_index = min(i, len(e.original_pdf_pages) - 1)
            references = e.comparison_sources
            ref = references[min(i, len(references) - 1)] if references else {}
            plan.append(
                {
                    "id": e.id,
                    "part": i + 1,
                    "parts": count,
                    "entry": e,
                    "body": parts[i] if i < len(parts) else "",
                    "source_pdf_page": e.original_pdf_pages[page_index],
                    "printed_page": e.original_printed_pages[page_index],
                    "reference": ref,
                    "listing_boundary_note": "original-page-aligned listing"
                    if aligned is not None
                    else "new continuous listing segment; boundaries not original"
                    if len(parts) > 1
                    and i < len(parts)
                    and parts[i].startswith("\\begin{verbatim}")
                    else None,
                }
            )
    return plan


def figure_fragment(e: Entry) -> Path | None:
    if e.kind != "figure":
        return None
    approved = {"figure 5.9": "cpu-elements", "figure 6.6": "model-events"}
    if e.id in approved:
        return LATEX / f"figures/tikz-preview/{approved[e.id]}.tex"
    return LATEX / f"figures/review/fig-{e.chapter}-{e.number}.tex"


def compile_part(item: dict[str, object]) -> None:
    e = item["entry"]
    assert isinstance(e, Entry)
    number = int(str(item["part"]))
    name = f"{slug(e)}-part-{number}"
    rendered = OUT / "rendered"
    fragment = figure_fragment(e)
    status = "native vector/text"
    if e.id == "figure 3.1":
        status = "native inline TikZ; approval pending user review"
    body = str(item["body"])
    if fragment is not None and fragment.is_file():
        body = r"\input{" + fragment.relative_to(LATEX).as_posix() + "}"
        status = "vector fragment; visual review pending"
        if e.id == "figure 6.3":
            fragment_text = fragment.read_text(encoding="utf-8")
            if all(f"t{n} --" in fragment_text for n in range(1, 8)):
                status = "native TikZ including timing key; visual review pending"
            else:
                status = "pending: native TikZ timing key incomplete"
    elif e.assets:
        status = (
            "raster preview 16 grayscale FS; not vector reconstruction"
            if e.type == "plot"
            else "pending vector reconstruction; raster preview"
        )
        asset = safe_path(e.assets[0], LATEX)
        gray = rendered / f"{name}-gray.png"
        preview = rendered / f"{name}-preview.png"
        result = run(["magick", str(asset), "-colorspace", "gray", str(gray)])
        if result.returncode == 0:
            result = run(
                ["pngquant", "--force", "--output", str(preview), "16", str(gray)]
            )
        if result.returncode == 0:
            run(["oxipng", "-q", "-o", "2", str(preview)])
            body = (
                r"\includegraphics[width=14cm,keepaspectratio]{"
                + preview.as_posix()
                + "}"
            )
        else:
            body = ""
    if not body:
        item.update(status="pending: no extractable new content", rendered=None)
        return
    wrapper = rendered / f"{name}.tex"
    wrapper.write_text(latex_header() + body + "\n\\end{document}\n", encoding="utf-8")
    result = run(
        [
            "direnv",
            "exec",
            str(ROOT),
            "latexmk",
            "-xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-outdir={rendered}",
            str(wrapper),
        ],
        cwd=LATEX,
    )
    pdf = rendered / f"{name}.pdf"
    if result.returncode or not pdf.is_file():
        (rendered / f"{name}.error.txt").write_text(
            result.stdout[-12000:] + result.stderr[-4000:], encoding="utf-8"
        )
        item.update(status="pending: standalone compilation failed", rendered=None)
    else:
        item.update(status=status, rendered=str(pdf.relative_to(ROOT)))


def refresh_crop(path: Path, recipe: Crop, refreshed: set[Path]) -> None:
    """Render once per build, even when an older output already exists."""
    if path not in refreshed:
        render_crop(recipe, path)
        refreshed.add(path)


def build(
    entries: list[Entry], plan: list[dict[str, object]], before: dict[str, str]
) -> None:
    (OUT / "rendered").mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(compile_part, plan))
    recipes = crop_recipes()
    refreshed: set[Path] = set()
    pages = []
    for item in plan:
        e = item["entry"]
        assert isinstance(e, Entry)
        ref = item["reference"]
        assert isinstance(ref, dict)
        path = safe_path(str(ref.get("path", ""))) if ref.get("path") else None
        ref_label = str(ref.get("kind", "original page fallback"))
        if path and ref.get("kind") == "original_crop":
            recipe = recipes.get(str(ref["path"]))
            if recipe is None:
                raise InputError(f"Missing crop recipe: {ref['path']}")
            refresh_crop(path, recipe, refreshed)
        if not path or not path.is_file():
            path = OUT / "rendered" / f"original-page-{item['source_pdf_page']}.png"
            if path not in refreshed:
                r = run(
                    [
                        "pdftoppm",
                        "-f",
                        str(item["source_pdf_page"]),
                        "-l",
                        str(item["source_pdf_page"]),
                        "-singlefile",
                        "-scale-to",
                        "2000",
                        "-png",
                        str(SOURCE_PDF),
                        str(path.with_suffix("")),
                    ]
                )
                if r.returncode:
                    raise InputError("Could not render original page")
                refreshed.add(path)
            ref_label = "original full page fallback (comparison only)"
        item["reference_used"] = str(path.relative_to(ROOT))
        item["reference_label"] = ref_label
        if item.get("listing_boundary_note"):
            item["status"] = (
                str(item["status"]) + "; " + str(item["listing_boundary_note"])
            )
        new = item.get("rendered")
        new_tex = (
            r"\includegraphics[width=\linewidth,height=0.70\textheight,keepaspectratio]{"
            + safe_path(str(new)).as_posix()
            + "}"
            if new
            else r"\fbox{\parbox{.8\linewidth}{Pending: standalone reconstruction unavailable}}"
        )
        pages.append(
            r"\noindent\textbf{"
            + tex_escape(e.id.title())
            + f" -- part {item['part']}/{item['parts']}"
            + r"}\quad "
            + tex_escape(e.caption_tex)
            + r"\\"
            + "\n"
            + tex_escape(
                f"Printed page {item['printed_page']}; PDF page {item['source_pdf_page']}. New: {item['status']}"
            )
            + r"\par\medskip"
            + "\n"
            + r"\noindent\begin{minipage}[t]{.49\textwidth}\centering\textbf{Original: "
            + tex_escape(ref_label)
            + r"}\par\medskip\includegraphics[width=\linewidth,height=0.70\textheight,keepaspectratio]{"
            + path.as_posix()
            + r"}\end{minipage}\hfill\begin{minipage}[t]{.49\textwidth}\centering\textbf{New}\par\medskip "
            + new_tex
            + r"\end{minipage}\clearpage"
        )
    document = (
        r"""\documentclass[landscape]{article}
\usepackage[margin=1cm]{geometry}\usepackage{fontspec,graphicx}\setmainfont{TeX Gyre Heros}\pagestyle{empty}
\begin{document}
"""
        + "\n".join(pages)
        + "\n\\end{document}\n"
    )
    (OUT / "builder-comparison.tex").write_text(document, encoding="utf-8")
    r = run(
        [
            "direnv",
            "exec",
            str(ROOT),
            "latexmk",
            "-xelatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-outdir={OUT}",
            str(OUT / "builder-comparison.tex"),
        ],
        cwd=LATEX,
        timeout=600,
    )
    if r.returncode:
        raise InputError("Comparison compilation failed: " + r.stdout[-3000:])
    after = protected_hashes()
    if before != after:
        raise InputError("Protected source hashes changed during build")
    shutil.copyfile(OUT / "builder-comparison.pdf", OUT / "comparison.pdf")
    serial = [
        {k: v for k, v in item.items() if k not in ("entry", "body", "reference")}
        for item in plan
    ]
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "numbered_entries": len(entries),
                "comparison_pages": len(serial),
                "source_hashes_sha256": before,
                "entries": serial,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


@click.group()
def cli() -> None:
    """Create a comparison-only review of every numbered figure and table."""
    sl.configure(
        processors=[
            sl.processors.TimeStamper(fmt="iso", utc=True),
            sl.processors.add_log_level,
            sl.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=sl.make_filtering_bound_logger("debug"),
        logger_factory=sl.PrintLoggerFactory(file=sys.stderr),
    )


@cli.command()
def check() -> None:
    """Check inputs and runtime tools without writing files."""
    try:
        entries = inventory()
        make_plan(entries)
        for name in ("direnv", "magick", "pngquant", "oxipng", "pdftoppm", "pdfinfo"):
            if not shutil.which(name):
                raise InputError(f"Missing executable: {name}")
        if not SOURCE_PDF.is_file():
            raise InputError("Missing original PDF")
        r = run(["direnv", "exec", str(ROOT), "latexmk", "-v"])
        if r.returncode:
            raise InputError("latexmk unavailable through direnv")
    except (InputError, OSError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo("ok")


@cli.command(name="build")
@click.option(
    "--dry-run", is_flag=True, help="Validate and show the plan without writing."
)
@click.option(
    "--yes", is_flag=True, help="Confirm replacement of generated review files."
)
def build_command(dry_run: bool, yes: bool) -> None:
    """Build generated wrappers, manifest, and comparison PDF."""
    try:
        before = protected_hashes()
        entries = inventory()
        plan = make_plan(entries)
        if dry_run:
            click.echo(
                f"Would render {len(plan)} parts for {len(entries)} entries in {OUT}"
            )
            return
        if not yes:
            click.confirm("Replace generated review artifacts?", abort=True)
        build(entries, plan, before)
        click.echo(f"Built {len(plan)} comparison pages for {len(entries)} entries")
    except (InputError, OSError, ValueError, sp.TimeoutExpired) as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command(name="unit-test")
def unit_test() -> None:
    """Run inline tests with branch coverage."""
    with tempfile.TemporaryDirectory(prefix="python-cli-coverage-") as directory:
        coverage_config = Path(directory) / ".coveragerc"
        coverage_config.write_text(
            os.linesep.join(
                (
                    "[run]",
                    "patch = subprocess",
                    "include =",
                    f"    {Path(__file__).resolve().as_posix()}",
                    "",
                )
            ),
            encoding="utf-8",
        )
        previous_coverage_file = os.environ.get("COVERAGE_FILE")
        os.environ["COVERAGE_FILE"] = str(Path(directory) / ".coverage")
        pytest_output = io.StringIO()
        try:
            with contextlib.redirect_stdout(pytest_output):
                result = pytest.main(
                    [
                        "-q",
                        "-p",
                        "no:cacheprovider",
                        "--cov",
                        "--cov-branch",
                        "--cov-config",
                        str(coverage_config),
                        "--cov-report=term-missing",
                        __file__,
                    ]
                )
        finally:
            if previous_coverage_file is None:
                os.environ.pop("COVERAGE_FILE", None)
            else:
                os.environ["COVERAGE_FILE"] = previous_coverage_file
        lines = pytest_output.getvalue().splitlines()
        lines = [
            line
            for line in lines
            if not (
                line.startswith("=")
                and line.endswith("=")
                and " tests coverage " in line
            )
            and not (
                line.startswith("_")
                and line.endswith("_")
                and " coverage: platform " in line
            )
        ]
        click.echo("\n".join(lines))
        raise SystemExit(result)


def test_safe_path() -> None:
    with pytest.raises(InputError):
        safe_path("../../etc/passwd")


def test_nested_caption() -> None:
    assert (
        strip_commands(r"hello \caption{A \emph{nested} caption} world")
        == "hello  world"
    )


def test_inventory_coverage() -> None:
    entries = inventory()
    plan = make_plan(entries)
    assert len(entries) == 77
    assert {str(i["id"]) for i in plan} == {e.id for e in entries}
    assert all(str(i["body"]) for i in plan)


def test_tables_never_select_figure_fragments() -> None:
    entries = {e.id: e for e in inventory()}
    for name in ("table 5.1", "table 6.1"):
        assert figure_fragment(entries[name]) is None
        assert r"\begin{tabular}" in source_parts(entries[name])[0]
    assert figure_fragment(entries["figure 5.1"]) is not None
    assert "2.734" in source_parts(entries["table 5.1"])[0]
    assert ".280" in source_parts(entries["table 6.1"])[0]


def test_native_listing_parts_preserve_code() -> None:
    entries = {e.id: e for e in inventory()}
    for name, first, second in (
        ("figure 2.2", "#include <smpl.h>", "case 3:"),
        ("figure 5.4", "#include <smpl.h>", "begin_cycle()"),
    ):
        parts = source_parts(entries[name])
        assert len(parts) == 2
        assert first in parts[0] and second in parts[1]
        assert all(
            part.startswith("\\begin{verbatim}\n") and part.endswith("\\end{verbatim}")
            for part in parts
        )
        assert all(
            "\\begin{lstlisting}" not in part and "minipage" not in part
            for part in parts
        )


def test_protects_existing_book_pdf() -> None:
    assert "build/simulating-computer-systems.pdf" in protected_hashes()


def test_crop_regeneration_in_isolation(tmp_path: Path) -> None:
    crop = next(iter(crop_recipes().values()))
    target = tmp_path / "reference.png"
    render_crop(crop, target)
    left, top, right, bottom = crop.crop_xyxy_px
    result = run(["magick", "identify", "-format", "%w %h", str(target)])
    assert result.returncode == 0
    assert result.stdout == f"{right - left} {bottom - top}"


def test_existing_crop_is_refreshed_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    crop = next(iter(crop_recipes().values()))
    target = tmp_path / "existing.png"
    target.write_bytes(b"stale")
    calls: list[Crop] = []

    def fake_render(recipe: Crop, destination: Path) -> None:
        calls.append(recipe)
        destination.write_bytes(b"fresh")

    monkeypatch.setattr(sys.modules[__name__], "render_crop", fake_render)
    refreshed: set[Path] = set()
    refresh_crop(target, crop, refreshed)
    refresh_crop(target, crop, refreshed)
    assert calls == [crop]
    assert target.read_bytes() == b"fresh"


def test_crop_rejects_dimension_mismatch(tmp_path: Path) -> None:
    crop = next(iter(crop_recipes().values())).model_copy(
        update={"source_render_dimensions_px": (1, 1)}
    )
    target = tmp_path / "must-not-exist.png"
    with pytest.raises(InputError, match="Unexpected render dimensions"):
        render_crop(crop, target)
    assert not target.exists()


def test_figure_6_3_uses_complete_reference() -> None:
    entry = next(e for e in inventory() if e.id == "figure 6.3")
    ref = entry.comparison_sources[0]
    assert ref["kind"] == "original_crop"
    recipe = crop_recipes()[str(ref["path"])]
    assert recipe.source_pdf_page == 185
    assert recipe.crop_xyxy_px == (100, 189, 1234, 956)


def test_aligned_page_selection_and_fallback() -> None:
    entries = {e.id: e for e in inventory()}
    plan = make_plan(list(entries.values()))
    for name, starts, pages in (
        ("figure 2.2", ["1  #include", "20 main()"], [44, 45]),
        ("figure 5.4", ["#include", "/*--------------  EVENT 1"], [138, 139]),
        (
            "figure 6.9",
            ["#include", "main()", "Defer(stn)", "InitBackoff(stn)"],
            [178, 179, 180, 181],
        ),
        (
            "figure 7.4",
            ["Simulation Output Analysis Definition", "central server model"],
            [208, 208],
        ),
    ):
        selected = [p for p in plan if p["id"] == name]
        assert [p["printed_page"] for p in selected] == pages
        assert all(
            start in str(part["body"])
            for start, part in zip(starts, selected, strict=True)
        )
        assert all(
            p["listing_boundary_note"] == "original-page-aligned listing"
            for p in selected
        )
    bad = entries["figure 6.9"].model_copy(update={"caption_tex": "wrong caption"})
    assert aligned_parts(bad) is None
    assert all(
        p["listing_boundary_note"]
        == "new continuous listing segment; boundaries not original"
        for p in make_plan([bad])
    )


def test_dry_run() -> None:
    from click.testing import CliRunner

    result = CliRunner().invoke(cli, ["build", "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "77 entries" in result.output


if __name__ == "__main__":
    cli()
