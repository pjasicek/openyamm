# MM6 Kreegan side stencil revision

The user requested replacing the accepted gargoyle with the actual winged Kreegan side silhouette,
in the same sepia stencil style as the Titan. This new map is a review candidate; the accepted gargoyle
map and all six destination highlights remain installed.

[Review in context](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/)
or open [the x2 map](tpenroth.png) and [the creature comparison](comparison.png).

The shape comes from restored MM6 frame `wdmflya2`, extracted directly from its atlas.
The [source reference](attempt_01/inputs/kreegan_reference.png) shows the raised bat wing, horned head,
long reaching arms, separated claw fingers, and bent legs. `inputs.json` records the exact atlas, crop, and hashes.

The built-in imagegen tool produced a separate transparent sepia layer from that reference and the existing
Titan's ink treatment. [The exact prompt](attempt_01/prompt.txt), arguments, input references, and raw return
are retained. The generated outline is approximate, so the final stencil uses the **original side-frame alpha**.
Its generated ink is registered to the original source canvas; nearest-solid RGB extension fills small contour
differences, and a narrow brown interior outline follows the actual source edge. Both the original silhouette
and all gaps remain fixed during the uniform reduction to 60 × 100 master pixels.

The new layer sits at master position (182, 342), smaller than the Titan and dragon. It is composited over the
previously repaired clean [terrain layer](../creature_fixup_v3/terrain.png), which already has no gargoyle.
Every terrain pixel outside the old and new creature silhouettes is unchanged. The final map is exported once
with Lanczos to 1280 × 960, retaining logical 640 × 480 placement.

`stencil_source.png`, `stencil.png`, `silhouette_mask.png`, and `master.png` retain editable components.
[manifest.json](manifest.json) and [validation.json](validation.json) verify the silhouette mask, confined changes,
unchanged Titan/dragon/labels, all six exact destination crops, and unchanged runtime files. The accepted hover
exports are reused byte for byte because none of their map regions changed. `review_before/` retains the page
state from before this new revision.

Recompose this candidate from the repository root:

```sh
python3 -B level_generation/ui/hud_inventory/town_portal_fixup_review/mm6/kreegan_revision_v4/compose.py
```

Future acceptance should publish the new map as a new receipt, preserving the earlier accepted gargoyle version.
The six hover exports already match this candidate and need no image changes.
