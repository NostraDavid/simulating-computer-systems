#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "click==8.5.0",
#   "orjson==3.11.7",
#   "pymupdf==1.27.2.2",
#   "pytest==9.2.0",
#   "pytest-cov==7.1.0",
#   "structlog==26.1.0",
# ]
# ///
"""Build an explicitly heuristic, page-paired review of the complete book."""

import contextlib
import hashlib
import io
import os
import re
import shutil
import subprocess as sp
import sys
import tempfile
from collections import Counter
from pathlib import Path

import click
import fitz
import orjson as json
import pytest
import structlog as sl
import structlog.stdlib as log

logger = log.get_logger(__name__)

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = ROOT / "simulatingcomput00myro_1-1.pdf"
PROOF = ROOT / "build/page-aligned/simulating-computer-systems-page-aligned.pdf"
OLD = ROOT / "build/simulating-computer-systems.pdf"
OUT = ROOT / "build/page-layout-review"
COUNT = 292


def configure_logging() -> None:
    sl.configure(
        processors=[
            sl.processors.TimeStamper(fmt="iso", utc=True),
            sl.processors.add_log_level,
            sl.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=sl.make_filtering_bound_logger("debug"),
        logger_factory=sl.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=False,
    )


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_pdf(path: Path, count: int) -> None:
    if not path.is_file() or path.is_symlink():
        raise click.ClickException(f"Missing or unsafe PDF: {path}")
    with fitz.open(path) as doc:
        if len(doc) != count:
            raise click.ClickException(
                f"{path}: expected {count} pages, found {len(doc)}"
            )


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def extract(page: fitz.Page, n: int) -> dict:
    rect = page.rect
    lines = []
    for block in page.get_text("dict")["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            text = " ".join(span["text"] for span in line["spans"]).strip()
            if text:
                lines.append((text, line["bbox"]))
    lines.sort(key=lambda item: (item[1][1], item[1][0]))
    # OCR commonly emits one block per word; coalesce same-baseline fragments.
    grouped = []
    for text, box in lines:
        if grouped and abs(box[1] - grouped[-1][1][1]) < rect.height * 0.003:
            grouped[-1][0].append((box[0], text))
            old = grouped[-1][1]
            grouped[-1][1] = [
                min(old[0], box[0]),
                min(old[1], box[1]),
                max(old[2], box[2]),
                max(old[3], box[3]),
            ]
        else:
            grouped.append([[(box[0], text)], list(box)])
    lines = [(" ".join(t for _, t in sorted(parts)), box) for parts, box in grouped]
    top = [t for t, b in lines if b[1] / rect.height < 0.08]
    bottom = [t for t, b in lines if b[3] / rect.height > 0.90]
    body = [
        (t, b)
        for t, b in lines
        if b[1] / rect.height >= 0.08 and b[3] / rect.height <= 0.90
    ]
    # If there is no obvious header, retain all but the extreme edge rather than invent text.
    if not body:
        body = lines
    box = None
    if body:
        box = [
            round(min(b[0] for _, b in body) / rect.width, 4),
            round(min(b[1] for _, b in body) / rect.height, 4),
            round(max(b[2] for _, b in body) / rect.width, 4),
            round(max(b[3] for _, b in body) / rect.height, 4),
        ]
    return {
        "page_size_points": [rect.width, rect.height],
        "header_candidates": top,
        "footer_candidates": bottom,
        "folio_candidate_found": bool(
            re.search(rf"(?<!\d){n}(?!\d)", " ".join(top + bottom))
        ),
        "first_body_anchor": body[0][0] if body else None,
        "last_body_anchor": body[-1][0] if body else None,
        "normalized_body_bbox": box,
        "body_text": " ".join(t for t, _ in body),
        "text_line_count": len(lines),
        "image_count": len(page.get_images()),
        "vector_drawing_count": len(page.get_drawings()),
    }


def overlap(a: str, b: str) -> float | None:
    x, y = Counter(tokens(a)), Counter(tokens(b))
    return round(sum((x & y).values()) / sum(x.values()), 3) if x else None


def audit_page(original: dict, proof: dict, n: int) -> dict:
    coverage = overlap(original["body_text"], proof["body_text"])
    first = overlap(
        original["first_body_anchor"] or "", proof["first_body_anchor"] or ""
    )
    last = overlap(original["last_body_anchor"] or "", proof["last_body_anchor"] or "")
    flags = []
    if not original["folio_candidate_found"] or not proof["folio_candidate_found"]:
        flags.append("folio not detected; inspect")
    if coverage is None or coverage < 0.65:
        flags.append("low OCR/text bag coverage")
    if min(original["text_line_count"], proof["text_line_count"]) < 8:
        flags.append("sparse text / possible figure or code")
    if (
        original["image_count"] > 1
        or proof["image_count"]
        or proof["vector_drawing_count"] > 5
    ):
        flags.append("figure or drawing; visual review")
    if first is None or first < 0.5 or last is None or last < 0.5:
        flags.append("weak first/last anchor agreement")
    if n == 7:
        for name, data in (("original", original), ("proof", proof)):
            header = " ".join(data["header_candidates"]).lower()
            first_line = (data["first_body_anchor"] or "").lower()
            if not all(word in header for word in ("1.2", "representing", "work")):
                flags.append(f"{name} page 7 header regression: inspect")
            if "necessarily have to be poisson:" not in first_line:
                flags.append(f"{name} page 7 first body regression: inspect")
    for data in (original, proof):
        data.pop("body_text")
    return {
        "printed_page": n,
        "original_physical_page": n + 22,
        "proof_physical_page": n,
        "original": original,
        "proof": proof,
        "first_anchor_token_coverage": first,
        "last_anchor_token_coverage": last,
        "body_bag_coverage": coverage,
        "flags": flags,
        "status": "automated signals only; human review required",
    }


def protect() -> dict[str, str | None]:
    return {str(p): digest(p) if p.is_file() else None for p in (ORIGINAL, OLD)}


def prepare(dry_run: bool) -> None:
    validate_pdf(ORIGINAL, 320)
    if not shutil.which("pdftoppm"):
        raise click.ClickException("pdftoppm is required")
    if dry_run:
        click.echo(
            f"Would render original physical pages 23–314 into {OUT / 'original'}"
        )
        return
    before = protect()
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=OUT, prefix=".prepare-") as temp:
        tmp = Path(temp) / "images"
        tmp.mkdir()
        sp.run(
            [
                "pdftoppm",
                "-f",
                "23",
                "-l",
                "314",
                "-scale-to",
                "1700",
                "-jpeg",
                "-jpegopt",
                "quality=85",
                str(ORIGINAL),
                str(tmp / "page"),
            ],
            check=True,
            timeout=3600,
        )
        files = sorted(tmp.glob("page-*.jpg"))
        expected = [f"page-{n:03d}.jpg" for n in range(23, 315)]
        if [p.name for p in files] != expected:
            raise click.ClickException("Unexpected original page render sequence")
        manifest = {
            "source_sha256": before[str(ORIGINAL)],
            "physical_pages": [23, 314],
            "long_side_pixels": 1700,
            "jpeg_quality": 85,
        }
        (tmp / "manifest.json").write_bytes(
            json.dumps(manifest, option=json.OPT_INDENT_2)
        )
        dest = OUT / "original"
        if dest.exists():
            raise click.ClickException(
                f"{dest} already exists; preserve it rather than overwrite"
            )
        tmp.rename(dest)
    if protect() != before:
        raise click.ClickException("Protected PDF changed during preparation")
    click.echo(f"Prepared 292 original images in {OUT / 'original'}")


def plan() -> list[Path]:
    validate_pdf(ORIGINAL, 320)
    validate_pdf(PROOF, COUNT)
    folder = OUT / "original"
    manifest_path = folder / "manifest.json"
    if not manifest_path.is_file():
        raise click.ClickException("Run prepare-original --yes first")
    manifest = json.loads(manifest_path.read_bytes())
    if manifest.get("source_sha256") != digest(ORIGINAL):
        raise click.ClickException("Prepared images do not match the original PDF")
    images = sorted(folder.glob("page-*.jpg"))
    if [p.name for p in images] != [
        f"page-{n:03d}.jpg" for n in range(23, 23 + COUNT)
    ] or any(p.is_symlink() for p in images):
        raise click.ClickException(
            "Missing, unexpected, or unsafe original page images"
        )
    return images


def build(dry_run: bool) -> None:
    images = plan()
    if dry_run:
        click.echo(
            f"Would compare 292 ordered pages and write comparison.pdf, audit.json, audit.md in {OUT}"
        )
        return
    before = protect()
    proof_hash = digest(PROOF)
    rows = []
    result = fitz.open()
    with fitz.open(ORIGINAL) as original, fitz.open(PROOF) as proof:
        for i, image in enumerate(images):
            n = i + 1
            a = extract(original[i + 22], n)
            b = extract(proof[i], n)
            row = audit_page(a, b, n)
            rows.append(row)
            page = result.new_page(width=1224, height=792)
            page.insert_text(
                (28, 25), f"Original physical {n + 22} / printed {n}", fontsize=13
            )
            page.insert_text(
                (625, 25), f"Editable proof physical {n} / printed {n}", fontsize=13
            )
            page.insert_text(
                (28, 45), "Automated QA only; human visual review required.", fontsize=9
            )
            label = (
                "; ".join(row["flags"]) or "No heuristic warnings; not certification"
            )
            for size in (8, 7, 6, 5):
                if (
                    page.insert_textbox(
                        fitz.Rect(625, 32, 1194, 60), label, fontsize=size
                    )
                    >= 0
                ):
                    break
            else:
                raise click.ClickException(f"Page {n} warning label does not fit")
            left = fitz.Rect(28, 65, 599, 765)
            right = fitz.Rect(625, 65, 1196, 765)
            page.draw_rect(left, color=(0.5, 0.5, 0.5), width=0.5)
            page.draw_rect(right, color=(0.5, 0.5, 0.5), width=0.5)
            page.insert_image(left, filename=str(image), keep_proportion=True)
            page.show_pdf_page(right, proof, i, keep_proportion=True)
    with tempfile.TemporaryDirectory(dir=OUT, prefix=".build-") as temp:
        tmp = Path(temp)
        result.save(tmp / "comparison.pdf", deflate=True, garbage=3)
        result.close()
        validate_pdf(tmp / "comparison.pdf", COUNT)
        audit = {
            "status": "automated signals only; human visual review required",
            "original_sha256": before[str(ORIGINAL)],
            "proof_sha256": proof_hash,
            "old_book_sha256": before[str(OLD)],
            "pages": rows,
        }
        (tmp / "audit.json").write_bytes(json.dumps(audit, option=json.OPT_INDENT_2))
        warning_count = sum(bool(row["flags"]) for row in rows)
        md = [
            "# Page layout review",
            "",
            f"**Coverage:** {COUNT} ordered page pairs; {warning_count} pages have heuristic warnings. This is not content equivalence or pixel certification; human review is required.",
            "",
            "Original scans and editable vector proof use different page geometry and typesetting. Panels preserve aspect ratio; matching panel frames do not imply matching source MediaBoxes. Original OCR, first/last anchors, folios, text ordering, code, math and figures may be misread; bag coverage ignores order and is not a completeness proof. Labels embedded in proof images are not extracted as text; low coverage on figure pages does not establish missing content. Review flags are prompts, not verdicts.",
            "",
            "| Printed | Original physical | Proof physical | Folios found (orig/proof) | Body bag coverage | First/last anchor coverage | Warnings |",
            "|---:|---:|---:|:---:|---:|:---:|---|",
        ]
        for r in rows:
            md.append(
                f"| {r['printed_page']} | {r['original_physical_page']} | {r['proof_physical_page']} | {r['original']['folio_candidate_found']} / {r['proof']['folio_candidate_found']} | {r['body_bag_coverage']} | {r['first_anchor_token_coverage']} / {r['last_anchor_token_coverage']} | {'; '.join(r['flags']) or 'none (not certified)'} |"
            )
        (tmp / "audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        if protect() != before or digest(PROOF) != proof_hash:
            raise click.ClickException(
                "Input or protected PDF changed during build; outputs not installed"
            )
        for name in ("comparison.pdf", "audit.json", "audit.md"):
            (tmp / name).replace(OUT / name)
    click.echo(f"Built {OUT / 'comparison.pdf'} and audit files")


@click.group()
def cli() -> None:
    """Prepare and build a 292-page paired layout review."""
    configure_logging()


@cli.command()
def check() -> None:
    """Check readiness for the final build without changing files."""
    plan()
    click.echo("ok")


@cli.command("prepare-original")
@click.option("--dry-run", is_flag=True)
@click.option("--yes", is_flag=True, help="Confirm rendering to the review directory.")
def prepare_command(dry_run: bool, yes: bool) -> None:
    """Render original pages independently of the editable proof."""
    if not dry_run and not yes:
        click.confirm("Render 292 original pages?", abort=True)
    prepare(dry_run)


@cli.command("build")
@click.option("--dry-run", is_flag=True)
@click.option("--yes", is_flag=True, help="Confirm replacing review outputs.")
def build_command(dry_run: bool, yes: bool) -> None:
    """Build the full comparison and machine-readable audit."""
    if not dry_run and not yes:
        click.confirm("Write or replace comparison and audit outputs?", abort=True)
    build(dry_run)


def compact_pytest_output(output: str) -> str:
    lines = []
    for line in output.splitlines():
        if line.startswith("=") and line.endswith("=") and " tests coverage " in line:
            continue
        if (
            line.startswith("_")
            and line.endswith("_")
            and " coverage: platform " in line
        ):
            continue
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


@click.command(name="unit-test")
def _embedded_unit_test_command() -> None:
    """Run embedded tests with isolated coverage output."""
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
                        "--cov",
                        "--cov-branch",
                        "--cov-config",
                        str(coverage_config),
                        "--cov-report=term-missing",
                        "-p",
                        "no:cacheprovider",
                        __file__,
                        "-q",
                    ]
                )
        finally:
            if previous_coverage_file is None:
                os.environ.pop("COVERAGE_FILE", None)
            else:
                os.environ["COVERAGE_FILE"] = previous_coverage_file
    click.echo(compact_pytest_output(pytest_output.getvalue()), nl=False)
    raise SystemExit(result)


cli.add_command(_embedded_unit_test_command)


def test_token_coverage() -> None:
    assert overlap("a a b", "a b") == 0.667
    assert overlap("", "x") is None


def test_synthetic_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original_path = tmp_path / "original.pdf"
    proof_path = tmp_path / "proof.pdf"
    output = tmp_path / "review"
    images = output / "original"
    images.mkdir(parents=True)
    source = fitz.open()
    for _ in range(320):
        source.new_page(width=200, height=300).insert_text((20, 50), "example body")
    source.save(original_path)
    source.close()
    proof = fitz.open()
    proof.new_page(width=200, height=300).insert_text((20, 50), "example body")
    proof.save(proof_path)
    proof[0].get_pixmap().save(images / "page-023.jpg")
    proof.close()
    (images / "manifest.json").write_bytes(
        json.dumps({"source_sha256": digest(original_path)})
    )
    monkeypatch.setattr(__import__(__name__), "ORIGINAL", original_path)
    monkeypatch.setattr(__import__(__name__), "PROOF", proof_path)
    monkeypatch.setattr(__import__(__name__), "OLD", tmp_path / "absent.pdf")
    monkeypatch.setattr(__import__(__name__), "OUT", output)
    monkeypatch.setattr(__import__(__name__), "COUNT", 1)
    build(True)
    assert not (output / "comparison.pdf").exists()
    build(False)
    with fitz.open(output / "comparison.pdf") as result:
        assert len(result) == 1 and result[0].rect.width > result[0].rect.height
    assert len(json.loads((output / "audit.json").read_bytes())["pages"]) == 1


def test_regression_seven() -> None:
    validate_pdf(ORIGINAL, 320)
    with fitz.open(ORIGINAL) as doc:
        page = doc[28]
        text = " ".join(page.get_text().split())
        assert "1.2" in text and "Representing" in text and "Work" in text
        assert "necessarily have to be Poisson:" in text
        data = extract(page, 7)
        assert "representing" in " ".join(data["header_candidates"]).lower()
        assert "necessarily have to be poisson:" in data["first_body_anchor"].lower()
    validate_pdf(PROOF, COUNT)
    with fitz.open(PROOF) as doc:
        data = extract(doc[6], 7)
        assert "1.2 representing work" in " ".join(data["header_candidates"]).lower()
        assert "necessarily have to be poisson:" in data["first_body_anchor"].lower()


if __name__ == "__main__":
    cli()
