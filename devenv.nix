{
  pkgs,
  lib,
  ...
}: let
  systemTools =
    import (builtins.fetchurl {
      url = "https://raw.githubusercontent.com/NostraDavid/nixcfg/cb2423e55f4a7ee010d33a649ddf0488338baa42/nix/system-tools.nix";
      sha256 = "7d2abe646d9389e296c5e1cafa0b63dd52e9821c58037d9dd8faef90124104e2";
    })
    pkgs;
in {
  cachix.enable = false;

  env = {
    PYTHONNOUSERSITE = "1";
    LD_LIBRARY_PATH = lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib pkgs.zlib];
    UV_PYTHON = "3.12";
    UV_PYTHON_PREFERENCE = "only-system";
    UV_PYTHON_DOWNLOADS = "never";
  };
  enterShell =
    (systemTools [
      "just"
      {
        attr = "uv";
        series = "0";
        also = ["uvx"];
      }
      "python312"
      "tectonic"
      {
        attr = "poppler-utils";
        command = "pdftotext";
        versionArgs = ["-v"];
        also = ["pdftoppm" "pdfimages"];
      }
      {
        attr = "tesseract";
        check = ''"$1" --list-langs 2>/dev/null | grep -Fx eng >/dev/null'';
      }
      {
        attr = "imagemagick";
        command = "magick";
        versionArgs = ["-version"];
      }
      "unpaper"
      {
        attr = "ghostscript";
        command = "gs";
      }
    ])
    + ''
      if ! (command -v latexmk >/dev/null && command -v xelatex >/dev/null && kpsewhich -engine=xetex xelatex.fmt >/dev/null && for f in fontspec microtype footmisc geometry graphicx caption indentfirst titlesec tikz pgfplots booktabs amsmath amssymb listings multicol hyperref xcolor fancyhdr; do kpsewhich "$f.sty" >/dev/null || exit 1; done); then
        ${(systemTools [
        {
          attr = "texlive.combined.scheme-full";
          command = "latexmk";
          versionArgs = ["-v"];
        }
      ])}
      fi
    ''
    + ''
      unset PYTHONPATH PYTHONHOME _PYTHON_SYSCONFIGDATA_NAME
    '';
}
