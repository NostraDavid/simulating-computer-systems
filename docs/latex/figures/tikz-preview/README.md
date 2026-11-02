# TikZ figure previews

Preview-only vector reconstructions of Figure 5.9 (Major CPU Elements) and
Figure 6.6 (*ether* Simulation Model Events). The existing chapter includes,
source PNGs, and built book are deliberately unchanged.

`cpu-elements.tex` and `model-events.tex` are reusable `tikzpicture` fragments.
Their labels, event descriptions, and directed connections come from the
corresponding original figure crops. Typography and geometry are re-typeset,
not pixel-identical tracings of scan defects. The required TikZ libraries are
already loaded by the book's preamble.

The current styling uses regular-weight text for body labels, descriptions,
and pipeline letters, with bold headings for contrast. Both are real font
faces; no synthetic font stroking is used. The CPU's top/right shadow
edges are 3.2 pt, increased from the initial 2 pt, and shifted 0.6 mm right
and 0.6 mm up behind opaque white foreground frames. The frames themselves
stay in place. Frames and internal rules are 1.2 pt; connections are 1.2 pt
in the CPU and 1.3 pt in the event diagram. Arrow tips are broader, rounded
triangles: 8 by 7 pt in the CPU and 4 by 3.5 mm in the event diagram. The crossing
bridge has additional white clearance so the thicker lines do not suggest a
junction. Geometry, wording, and connection directions are unchanged by these
style adjustments.

The CPU drawing has five arrowed segments (one path is split by the data-fetch
buffer). The event drawing has eleven directed connections, including the
TransmitFrame self-loop: 1->1, 1->2, 2->3, 3->4, 3->5, 3->6, 4->1, 4->6,
5->1, 5->2, and 6->3. The 6->3 return bridge crosses the two outgoing paths
without joining them.

## Rebuild the previews

From the repository root, using the existing project environment:

```sh
mkdir -p build/tikz-preview
direnv exec . bash -eu -c '
  cd docs/latex
  latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error \
    -jobname=cpu-elements -outdir=../../build/tikz-preview \
    figures/tikz-preview/cpu-elements-preview.tex
  latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error \
    -jobname=model-events -outdir=../../build/tikz-preview \
    figures/tikz-preview/model-events-preview.tex
  latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error \
    -jobname=comparison -outdir=../../build/tikz-preview \
    figures/tikz-preview/compare.tex
'
```

The standalone PDFs contain vector paths and selectable text, not embedded
figure images. The two-page comparison intentionally embeds the original PNG
on the left and the new vector PDF on the right. Standalone PDF file sizes
include font subsets; they do not predict the final book's size reduction.

## Verified preview results

| Figure | Original PNG | Standalone vector PDF |
| --- | ---: | ---: |
| CPU elements | 77,420 bytes | 6,262 bytes |
| Model events | 516,865 bytes | 9,810 bytes |

Both standalone PDFs have zero raster images. Their extracted words and
operators match manual reference transcriptions, and an independent visual
review checked all labels, event text, arrow directions, the self-loop, and
the crossing bridge. The standalone drawings and both comparison pages were
rendered and visually inspected. No overfull boxes, missing glyphs, or words
outside the PDF page were found. SHA-256 checks confirm that both source PNGs
and the existing book PDF remain unchanged. Detailed measurements are in
`build/tikz-preview/verification.json`.

The selected 16-grayscale/Floyd-Steinberg treatment for remaining raster figures
is a separate step; it is not applied by this preview.
