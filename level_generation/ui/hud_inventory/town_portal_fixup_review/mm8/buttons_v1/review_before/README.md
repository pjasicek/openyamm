# MM8 colored Town Portal candidate — detail revision

The user supplied `test_img/2063.png`, a colored, labeled Jadame map, and requested a combined x2 restoration
without labels. The current [candidate](attempt_03/townport.png) also corrects the five details marked in
`test_img/2064.png`: the skeletal dragon, vampire, centaur, Earth portal color, and Ravenshore crystal.

Open the [comparison page](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm8/)
for the corrected image, previous candidate, installed artwork, native original, color reference, and a
before/after slider comparing the five corrections.
Game-size and x2-size controls are available. The color-reference tab fits the entire reference without stretching it.
This is a background review candidate; new destination hover patches have not been prepared or deployed.

- [x2 export](attempt_03/townport.png): 1280 × 960, opaque RGB; logical canvas 640 × 480.
- [Untouched generated master](attempt_03/raw.png): 1448 × 1086, 2.2625 samples per native pixel.
- Exact built-in imagegen prompts: [five detail corrections](attempt_02/prompt.txt), then
  [creature size refinement](attempt_03/prompt.txt). Tool arguments are retained beside each prompt.
- [Retained creature and annotation references](attempt_02/inputs.json), [export provenance](attempt_03/generation.json),
  and [review manifest](attempt_03/manifest.json).

The Bone Dragon uses restored `mm8_m616/redo_2x` frame `m616wa1_616`; the vampire uses restored
`mm8_m468/redo_2x` frame `m468sa0_469`. The centaur uses native MM8 `m532sa1.bmp`, decoded as an RGB PNG.
These are identity references for small painted map figures, not changes to the creature restoration packages.
The first correction pass made the creatures too large. Its master remains in `attempt_02`; `attempt_03`
reduces them to miniature map scale and is the displayed candidate.

The lower-right Earth gateway now has warm brown/ochre tones. The blue feature at Ravenshore is the crystal
gateway to the Plane Between Planes, confirmed by the original MM8 event text in
`reference/mmext-scripts/Decompiled_Scripts/mm8/txt/Global.txt`, line 7258. It now has solid angular mineral
facets instead of waterfall-like streaks. All other layout features remain visually aligned; generated edits
are not a guarantee of identical pixels outside these details.

The initial `attempt_01` used three references: the existing x2 screen for its label-free composition, the
user's colored map for palette and decorative identities, and the native original for original layout and motifs.
The repaint distinguishes green woodland, tan desert, red-brown canyon cliffs, dark eastern terrain, blue sea,
and the four elemental portal colors. The western red dragon replaces the misleading pale statue-like figure
in the previous restoration. Place names, gateway captions, the title, scan folds, and other lettering are omitted.
The original ragged parchment, wooden backing, unlettered compass rose, major geography, and six destination
motifs remain recognizable. Local contours and brushwork are redrawn rather than guaranteed pixel-identical.

The raw image was uniformly downscaled once with ImageMagick Lanczos, with no further grading or sharpening.
The current accepted index, ledger, MM6/MM7/MM8 runtime map files, MM8 hover images, and Town Portal layout
files remain unchanged. [validation.json](attempt_03/validation.json) records the checks and browser evidence.

MM8's table aliases are resolved in `GameplayUiRuntime::townPortalIconTextureName`:
`TPHarmndy` → `tp_alvar`, `TPelf` → `tp_ravenshore`, `TPWarlock` → `tp_balthazarlair`,
`TPIsland` → `tp_regna`, `TPHeaven` → `tp_shadowspire`, `TPhell` → `tp_daggerwoundislands`.
Use those runtime names if matching buttons are prepared after background review.
