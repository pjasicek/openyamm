# Town Portal background revisions

The current [Kreegan revision](mm6/kreegan_revision_v4/README.md) replaces the gargoyle with the actual
restored MM6 side-frame silhouette in the Titan's sepia stencil style. Its mask is taken directly from
`wdmflya2`; the repaired terrain and all six destination highlights are preserved. This version is ready for review.

The MM6 map `engine--icons--tpenroth.bmp` and its six destination hover patches are
[accepted and installed](../town_portal_acceptance_20260927/README.md) under the user's explicit approval.
That installed revision contains the gargoyle. The canonical ledger and current accepted index point to immutable
copies of those seven reviewed exports;
the runtime files in `assets_dev/engine/icons_x2/` match them exactly.

Open [the comparison page](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/)
to hover all six destinations, preview selection, and switch between the Kreegan revision, the installed gargoyle,
earlier installed art, and the original. Each mode uses its corresponding destination patches.
The hover rectangles come from the MM6 group of `assets_dev/engine/data_tables/town_portal_switch.txt`;
blank width/height fields resolve to the archived button's native dimensions, as in the game.

The user requested regeneration with `test_img/2050.png` supplying four label corrections:
Eel Infested Waters, Bootleg Bay, Misty Islands, and Mire of the Damned.
`test_img/2051.png` supplies the regional terrain context from assembled game minimaps.
The original parchment composition remains the layout reference. The previous generated background
supplies a finish reference only; its malformed labels and overly green western terrain are corrected.

- [Accepted map at x2](../town_portal_acceptance_20260927/accepted/engine/icons_x2/tpenroth.png):
  1280 × 960, logical size 640 × 480.
- [New Kreegan candidate](mm6/kreegan_revision_v4/tpenroth.png) and [its provenance](mm6/kreegan_revision_v4/manifest.json).
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
unchanged borders, and current accepted runtime hashes. The review page's `?verify=1` mode checks 24 hover states
across its four comparison modes, exact exported pixels, reset behavior, logical hit rectangles, keyboard focus,
and selection. Desktop/narrow captures are retained in `mm6/buttons_v1/evidence/`.
The original manifests and `validation.json` retain their pre-publication status as historical evidence.
[acceptance.json](acceptance.json) records the current installed status; the acceptance folder owns the
receipts and installation validation. Engine code and placement tables remain unchanged.
