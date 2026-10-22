{
  pkgs,
  lib,
  ...
}: {
  cachix.enable = false;
  packages = with pkgs; [
    just
    uv
    python312
    texlive.combined.scheme-full
    tectonic
    poppler-utils
    tesseract
    imagemagick
    unpaper
    ghostscript
  ];
  env = {
    PYTHONNOUSERSITE = "1";
    LD_LIBRARY_PATH = lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib pkgs.zlib];
    UV_PYTHON = "3.12";
    UV_PYTHON_PREFERENCE = "only-system";
    UV_PYTHON_DOWNLOADS = "never";
  };
  enterShell = ''
    unset PYTHONPATH PYTHONHOME _PYTHON_SYSCONFIGDATA_NAME
  '';
}
