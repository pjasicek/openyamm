# MM7 Town Portal map and matching buttons

Latest: [2026-10-04 original-reference corrections](details_20261004/README.md).
The comparison page now previews the corrected Pit emblem, Steadwick approach and Nighon steps with matching
destination highlights. This is a new review candidate; the accepted installation described below is preserved.

The user accepted the cleaner repaint of `antagrich.png` and all six matching destination buttons, and requested
deployment. All seven images are [accepted and installed](../../town_portal_mm7_acceptance_20260927/README.md)
in `assets_dev/engine/icons_x2/`. [acceptance.json](acceptance.json) records this workspace's current status.

Open the [comparison page](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm7/).
Hover or keyboard-focus any destination to highlight it; clicking previews a selection. The page also shows
the previous installed artwork, the native original, and a before/after slider, each using its corresponding buttons.
The default Accepted view reads the immutable accepted exports directly.
Use **Show all highlights** for a simultaneous comparison or **Show click areas** to inspect the original hit rectangles.
The size control offers the 640 × 480 game canvas and the 1280 × 960 x2 export as well as fitting the window.
New hover artwork uses exact x2 map crops with a feathered warm screen blend. Drawing coordinates and sizes match
the `Antagrich` group in `town_portal_switch.txt`; blank sizes come from the original button BMPs, as in the engine.

- [Accepted map](../../town_portal_mm7_acceptance_20260927/accepted/engine/icons_x2/antagrich.png):
  1280 × 960, opaque RGB; identical to the [reviewed PNG](attempt_01/antagrich.png).
- [Untouched generated master](attempt_01/raw.png): 1448 × 1086, 2.2625 samples per native pixel.
- [Exact submitted prompt](attempt_01/prompt.txt) and [tool arguments](attempt_01/tool_args.json).
- [Input copies and previous accepted record](attempt_01/inputs.json).
- [Generation and export provenance](attempt_01/generation.json), [review manifest](attempt_01/manifest.json).
- [Six button pairs and masks](buttons_v1/), [button provenance](buttons_v1/manifest.json),
  [visual comparison](buttons_v1/evidence/buttons.png), and [browser validation](buttons_v1/browser_validation.json).

The built-in imagegen tool repainted the current x2 artwork, using the native original as a second layout reference.
The complete frame, wood backdrop, coastline arrangement, road network, terrain regions, and six destination motifs
are retained. Small local contours and brushwork are newly drawn, not guaranteed to match source pixels.
The export is one uniform ImageMagick Lanczos downscale from the generated master, without sharpening or other grading.

The current accepted index and canonical ledger point to the new seven-image revision. Older accepted exports
and original sources remain preserved. The separate MM6 palette study remains pending a palette choice.

The original background-only manifest and captures remain historical evidence of the regeneration step.
The button manifest and browser validation retain their pre-acceptance state as historical evidence.
The acceptance folder owns the approval receipts, installation manifest, and final validation.
