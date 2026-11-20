# MM6 Town Portal palette study

The user approved the darker Kreegan, then requested a more muted map palette **before deployment**.
Publication and installation are held while this study is reviewed. The accepted runtime map remains the
earlier gargoyle revision; neither the live index nor its installed images changed during this study.

[Open the muted preview](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/?color=35).
The slider runs from 0 to 100 percent color strength. Presets are **Current 100%**, **Muted 35%** (default),
and **Faded 15%**. The Original tab displays the original native artwork without grading. The Current color
tab displays the approved darker Kreegan artwork without grading. Earlier revisions remain under the
collapsible history. Moving the slider selects Muted preview; the chosen value is retained in the page URL.

This is an interactive canvas color adjustment. No image generation, drawing edits, resampling, source-PNG
modification, acceptance publication, or installation is performed. The map, detailed ink, and darker Kreegan
come directly from `../kreegan_revision_v5/tpenroth.png`.

The deterministic recipe is recorded in [manifest.json](manifest.json) and the page's `data.js`:

- Work on the existing encoded RGB bytes, leaving alpha unchanged.
- Luminance is `0.2126 R + 0.7152 G + 0.0722 B`.
- Normalize warm-gray RGB factors `[1.05, 1, 0.9]` by their weighted luminance.
- At strength `s`, output each channel as `round(s * channel + (1-s) * luminance * warmFactor)`,
  clamped to 0–255. A strength of 100 is an exact bypass.
- Apply the same pointwise transform to the background and every destination highlight. Dimensions,
  canvas coordinates, and hit areas remain unchanged. This ensures the unchanged patch borders still match.

The browser caches only the current color setting's images and clears that cache when the slider changes.
The `?verify=1&color=35` check covers 54 hover states: all six destinations across five ungraded comparison
versions and at color strengths 0, 15, 35, and 100. It compares separately graded background/patch compositing
against grading the fully composited frame, checks changes remain within the destination, resets the map,
and verifies logical hit areas and keyboard selection.

`browser_35.png` and `browser_15.png` retain the visible previews; `validation.json` records the results and
hashes. `review_before/` preserves the page before adding these controls. When a palette is selected, its exact
recipe should be baked into a new map and six matching hover exports before acceptance and deployment.
