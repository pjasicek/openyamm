# MM7 Town Portal regeneration candidate

The user requested a cleaner repaint of `antagrich.png` while retaining the existing layout and feel.
This is a review candidate, with no acceptance or runtime installation.

Open the [comparison page](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm7/).
It shows the regenerated candidate, the current accepted artwork, the native original, and a before/after slider.
The size control offers the 640 × 480 game canvas and the 1280 × 960 x2 export as well as fitting the window.
This review covers the background; destination hover patches have not been revised for this candidate.

- [Candidate PNG](attempt_01/antagrich.png): 1280 × 960, opaque RGB.
- [Untouched generated master](attempt_01/raw.png): 1448 × 1086, 2.2625 samples per native pixel.
- [Exact submitted prompt](attempt_01/prompt.txt) and [tool arguments](attempt_01/tool_args.json).
- [Input copies and previous accepted record](attempt_01/inputs.json).
- [Generation and export provenance](attempt_01/generation.json), [review manifest](attempt_01/manifest.json).

The built-in imagegen tool repainted the current x2 artwork, using the native original as a second layout reference.
The complete frame, wood backdrop, coastline arrangement, road network, terrain regions, and six destination motifs
are retained. Small local contours and brushwork are newly drawn, not guaranteed to match source pixels.
The export is one uniform ImageMagick Lanczos downscale from the generated master, without sharpening or other grading.

The existing accepted index, canonical ledger, runtime background, and six runtime hover images are preserved.
The separate MM6 palette study remains pending a palette choice.
