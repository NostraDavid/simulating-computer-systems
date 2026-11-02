# Reconstruction status

The goal is an actually rebuilt, smaller PDF: editable LaTeX prose, equations,
tables, and C listings, with vector drawings or individual figure assets.
Embedding complete scanned pages or the original PDF is not a reconstruction
and is not an accepted fallback.

## Build

`just build-latex` produces `build/simulating-computer-systems.pdf` from
`docs/latex/main.tex`. The build must not read the original scan or a normalized
copy of it. The source PDF is only a transcription and checking reference.

## Accuracy

All nine chapters, the appendix, bibliography, and indexes are present as
typeset text and individual figures. Similar text length, successful
compilation, or a small output file does not establish character-perfect
accuracy. Unresolved text and code must be identified, not replaced by invented
content or silently omitted.

The rebuilt book has different pagination. Preserved index references identify
original book pages and must not be represented as rebuilt-page references.

## Coverage and verification

- Chapters 1-4 retain their existing text reconstruction. All 29 figures and
  four tables were compared with the original; incorrect diagrams, graph
  curves, report values, and table values were corrected. Some figures use
  individually cropped source artwork rather than a speculative vector redraw.
  Paragraph-level OCR alignment across all 128 source pages also identified
  and restored the inverse-CDF explanation, a replication instruction, two
  batch-means paragraphs, and two footnotes; a queued-return identifier was
  corrected against the original.
- Chapters 5-9 were transcribed through all 129 source PDF pages, 151-279.
  Independent normalized OCR-token alignment across those pages found no
  omitted prose paragraph or project section. Equations, numerical displays,
  and code were visually sampled; this is not a symbol-by-symbol certification.
- The appendix contains the actual original C text: `smpl.c` (622 lines),
  `rand.c` (167), `smpl.h` (21), and `stat.c` (44), included with
  `\lstinputlisting`, not page images.
- All 106 bibliography entries were transcribed and independently compared in
  order with the source. The author index contains 131 top-level entries and
  the subject index 176. Their original page references are explicitly labelled.
- The publisher's series page and back-cover text are re-typeset. The author
  portrait is a small separate photograph. Blank/library endpapers, borrowing
  stamps, and the library barcode on source pages 316-319 are not book content
  and are not embedded.
- The build recorder is checked by `just build-latex`: reading the original PDF
  or its former normalized copy makes the recipe fail. Neither is a build
  dependency. The earlier facsimile/hybrid outputs and scan-inclusion build
  machinery were removed.

## Verified build result

The rebuilt PDF has 251 pages and is 10,369,933 bytes (about 10.4 MB), compared
with 291,335,974 bytes for the supplied scan: 96.4 percent smaller. It contains
typeset text and 45 individual images, not one scanned image per book page.

The XeLaTeX build succeeds with no undefined references, missing glyphs,
overfull boxes, or oversized floats. Text bounding-box checks found no words
outside the page. All pages were rendered for a thumbnail layout inspection,
with selected listings, graphs, table guides, indexes, and covers also checked
at higher resolution. C listing quotes remain literal ASCII characters when
extracted from the PDF.

The original scan is unchanged. Tectonic is an alternative build recipe but
was not re-verified in this run.

## Remaining limitations

- The indexes preserve original pagination; remapping them to the rebuilt
  pagination remains separate work.
- The opening parenthesis after `return` in `dly()` in the source listing on PDF
  page 201 is unclear. The syntactically consistent reading is retained and
  marked in a source comment.
- Apparent errors printed in the original code and bibliography are preserved
  and annotated, not silently modernized. The original `smpl.c` is not directly
  compatible with current GCC because of its static `stdout` initializers and
  old declaration rules. The other listings pass the documented GNU89 syntax
  checks, but that does not establish portability or runtime correctness.
- Figure assets are a mixture of vector drawings and cropped raster artwork;
  this is not an all-vector recreation. OCR alignment and sampled visual checks
  do not replace a complete human proofread.
