# Town Portal background revisions

The latest [MM8](mm8/details_20261004/README.md) and [MM7](mm7/details_20261004/README.md)
detail corrections follow the user's marked images from 2026-10-04 and the original artwork.
Both backgrounds and all twelve matching destination highlights are now
[accepted and installed](../town_portal_acceptance_20261004/README.md) in `assets_dev/engine/icons_x2/`.
Both comparison pages show those exact accepted exports. Previous artwork remains in its historical folders.

The [MM8 colored candidate](mm8/README.md) combines the original label-free Town Portal layout with the colors
and illustrations of `test_img/2063.png`, with the five creature/gateway corrections from `2064.png`.
Its [comparison page](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm8/)
includes the previous candidate, original and color reference, plus all six matching destination buttons
with interactive hover. The MM8 map and buttons are prepared for review and have not been deployed.

The [MM7 regeneration](mm7/README.md) and all six matching destination buttons are
[accepted and installed](../town_portal_mm7_acceptance_20260927/README.md). The
[interactive comparison page](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm7/)
reads those exact accepted exports, with previous/original views, a before/after slider, and registered hover highlights.

The current [palette study](mm6/palette_study_v6/README.md) previews reduced color strength, with a slider,
35% and 15% presets, and a direct original-map comparison. The user requested this study before deployment;
the ledger and runtime remain at the earlier gargoyle acceptance. The darker Kreegan drawing has been approved
and is the fixed source for these color previews.

The [darker Kreegan revision](mm6/kreegan_revision_v5/README.md) uses stronger, nearly black ink to
match the Titan and dragon. It keeps the exact drawing and alpha from the
[side-silhouette revision](mm6/kreegan_revision_v4/README.md), whose mask comes directly from restored frame
`wdmflya2`. Its repaired terrain and all six destination highlights are preserved in the color study.

The MM6 map `engine--icons--tpenroth.bmp` and its six destination hover patches are
[accepted and installed](../town_portal_acceptance_20260927/README.md) under the user's explicit approval.
That installed revision contains the gargoyle. The canonical ledger and current accepted index point to immutable
copies of those seven reviewed exports;
the runtime files in `assets_dev/engine/icons_x2/` match them exactly.

Open [the comparison page](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/)
to adjust color strength, hover all six destinations, and compare the muted preview, current color, and original.
The darker/lighter Kreegan revisions, installed gargoyle, and earlier installed artwork remain available.
Each mode uses its corresponding destination patches; color changes affect both background and hover together.
The hover rectangles come from the MM6 group of `assets_dev/engine/data_tables/town_portal_switch.txt`;
blank width/height fields resolve to the archived button's native dimensions, as in the game.

The user requested regeneration with `test_img/2050.png` supplying four label corrections:
Eel Infested Waters, Bootleg Bay, Misty Islands, and Mire of the Damned.
`test_img/2051.png` supplies the regional terrain context from assembled game minimaps.
The original parchment composition remains the layout reference. The previous generated background
supplies a finish reference only; its malformed labels and overly green western terrain are corrected.

- [Accepted map at x2](../town_portal_acceptance_20260927/accepted/engine/icons_x2/tpenroth.png):
  1280 × 960, logical size 640 × 480.
- [New darker Kreegan candidate](mm6/kreegan_revision_v5/tpenroth.png)
  and [its provenance](mm6/kreegan_revision_v5/manifest.json).
- [Localized master](mm6/creature_fixup_v3/master.png): 1448 × 1086, 2.2625 samples per native pixel.
- [Current provenance](mm6/creature_fixup_v3/manifest.json) and [first map provenance](mm6/attempt_01/manifest.json).
- [Button provenance and validation](mm6/buttons_v1/manifest.json), [normal crops](mm6/buttons_v1/default/),
  [hover exports](mm6/buttons_v1/hover/), [masks](mm6/buttons_v1/masks/), and
  [original/new comparison](mm6/buttons_v1/evidence/buttons.png).

The map artwork was generated with the built-in imagegen tool. The user subsequently corrected two decorative
figures: a Titan on the southern desert peninsula and, finally, a small HOMM2 gargoyle above Paradise Valley.
The gargoyle's reduced size and simplified sepia stencil treatment follow the Titan's style. Its authoritative
silhouette reference is `test_img/2053.png`. After accepting it, the user requested the current Kreegan revision
using the actual creature's side silhouette.

Exact submitted prompts remain under [attempt 01](mm6/attempt_01/prompt.txt),
[02](mm6/attempt_02/prompt.txt), [03](mm6/attempt_03/prompt.txt), [04](mm6/attempt_04/prompt.txt),
[05](mm6/attempt_05/prompt.txt), [06](mm6/attempt_06/prompt.txt), and [07](mm6/attempt_07/prompt.txt),
alongside raw generated returns and inputs.
Attempt 02 supplies the Titan. Attempts 03–04 retain the superseded smaller Kreegan and a stray-mark cleanup.
Attempts 05–06 establish the HOMM2 gargoyle silhouette, size, and simplified ink treatment.
Attempt 07 repairs the blurred terrain called out in `test_img/2054.png`. The surrounding ground is restored
directly from the first approved map. A crisp generated clean plate removes the original creature's old footprint.
The current gargoyle is extracted from its existing pixels and placed over that terrain without rescaling,
recoloring, or redrawing. The [terrain layer](mm6/creature_fixup_v3/terrain.png),
[gargoyle RGBA layer](mm6/creature_fixup_v3/gargoyle.png), and [before/after detail](mm6/creature_fixup_v3/comparison.png)
are retained separately; only the creature edge is antialiased, with no broad smooth backing patch.

The final localized masters preserve the original approved map's pixels outside the two creature neighborhoods.
No destination patch overlaps those neighborhoods. The final gargoyle revision also preserves the prior Titan
pixel-for-pixel. Exports are uniform ImageMagick Lanczos downscales to 1280 × 960. All map images are opaque RGB.

The six hover states use deterministic processing only. Each default is an exact rectangle cut from the final map,
and its hover uses a warm screen blend through a settlement-centered feathered mask. There is no resampling,
geometry change, or independent redraw. A four-pixel border remains exactly equal to the background, eliminating
rectangular seams. Native positions and all six export sizes are unchanged. The game draws these opaque patches
only while hovered or pressed; normal-state crops are retained for review and provenance.

The following commands record the pre-acceptance preparation sequence. They now refuse to overwrite this
accepted revision; copy the work to a new revision before making future artwork changes.

```sh
python3 -B level_generation/ui/hud_inventory/town_portal_fixup_review/mm6/prepare_creature_fixup.py
python3 -B level_generation/ui/hud_inventory/town_portal_fixup_review/mm6/prepare_gargoyle.py
python3 -B level_generation/ui/hud_inventory/town_portal_fixup_review/mm6/prepare_ground.py
python3 -B level_generation/ui/hud_inventory/town_portal_fixup_review/prepare_buttons.py
```

Preparation asserts unchanged pixels outside each repair, exact map crops, mask confinement, native sizes,
unchanged borders, and current accepted runtime hashes. The current palette page's `?verify=1` mode checks
54 hover states across color strengths and comparison modes, exact compositing, reset behavior, logical hit
rectangles, keyboard focus, and selection. Earlier checks and captures remain in their original revision folders.
The original manifests and `validation.json` retain their pre-publication status as historical evidence.
[acceptance.json](acceptance.json) records the current installed status; the acceptance folder owns the
receipts and installation validation. Engine code and placement tables remain unchanged.
