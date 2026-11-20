# MM7 Town Portal map and matching buttons

The user approved the cleaner repaint of `antagrich.png` and requested matching destination buttons.
All six [new hover patches](buttons_v1/README.md) are ready for review. The accepted index and runtime installation
have not been changed; the background approval is recorded in the new button manifest.

Open the [comparison page](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm7/).
Hover or keyboard-focus any destination to highlight it; clicking previews a selection. The page also shows
the current accepted artwork, the native original, and a before/after slider, each using its corresponding buttons.
Use **Show all highlights** for a simultaneous comparison or **Show click areas** to inspect the original hit rectangles.
The size control offers the 640 × 480 game canvas and the 1280 × 960 x2 export as well as fitting the window.
New hover artwork uses exact x2 map crops with a feathered warm screen blend. Drawing coordinates and sizes match
the `Antagrich` group in `town_portal_switch.txt`; blank sizes come from the original button BMPs, as in the engine.

- [Candidate PNG](attempt_01/antagrich.png): 1280 × 960, opaque RGB.
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

The existing accepted index, canonical ledger, runtime background, and six runtime hover images are preserved.
The separate MM6 palette study remains pending a palette choice.

The original background-only manifest and captures remain historical evidence of the regeneration step.
The new button manifest records the user's subsequent background approval and the current review state.
