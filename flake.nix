{
  description = "Dev environment for simulating-computer-systems";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        # Bigger but includes latexmk and most packages out of the box.
        tex = pkgs.texlive.combined.scheme-full;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            tex
            pkgs.glibcLocales
            pkgs.tectonic
            pkgs.poppler_utils
            pkgs.tesseract
            pkgs.ghostscript
          ];
          LOCALE_ARCHIVE = "${pkgs.glibcLocales}/lib/locale/locale-archive";
          LANG = "en_US.UTF-8";
          LC_ALL = "en_US.UTF-8";
          shellHook = ''
            echo "LaTeX tools ready. See docs/latex/README.md"
          '';
        };
      });
}
