import subprocess

import pytest


@pytest.mark.parametrize("recipe, args", [("ocr-page", ["1"]), ("ocr-range", ["1", "2"])])
def test_ocr_recipes_are_valid_shell(recipe, args):
    rendered = subprocess.run(
        ["just", "--dry-run", recipe, *args], capture_output=True, text=True, check=True
    )
    subprocess.run(["bash", "-n"], input=rendered.stderr, text=True, check=True)
