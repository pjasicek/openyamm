# PC01 fitted restoration: contained outline

Reprocessed 2026-09-24 from the retained generated master, without new generation.
The user allows a thinner doll so existing equipment can cover it; exact mask equality is no longer required.

[Interactive equipment fitting](../../../../index.html?doll=1&trial=1&art=candidate) ·
[Pose and mask comparison](review.html) · [Measured provenance](manifest.json)

One shared `pc01bod` supplies every pose. `pc01lhu`, `pc01rhd`, `pc01rhu`, and `pc01rhb`
are separate limb/grip layers, retaining original 2× canvases, cut lines, and table coordinates.
The shield hand `pc01lho` remains original. Equipment selection and coordinates are unchanged.

`process.py` maps the complete retained raw sheet to native coordinates. It smooths each assembled
native silhouette inward at 4× working resolution, intersects it with generated alpha, then exports
at 2× and splits at original part boundaries. Working resolution adds no generated detail.
Near-opaque generated interiors are normalized to opaque; faint red fringe is discarded and edge RGB
comes from opaque generated pixels. No original RGB or blue-black boot backing is copied.

All five parts and the three assembled poses have **zero visible pixels outside their native masks**.
At alpha >= 128 the assembled restored area is about 92% of the original, including removal of boot
backing. This is not a uniform 8% body shrink. Body and limb attachment coordinates have not moved.
`comparison_*.png` places the previous exact-mask extraction left and this revision right.
`mask_*.png` shows restored coverage green and original-only coverage blue-gray.

This improves extraction and contours, not texture detail. Internal generated features can still differ
from the original, and containment alone does not prove every armor, glove, boot, or weapon fits.
Review the actual item combinations. Enlarging a 2× export beyond its intended size still reveals pixels.
The original master and previous extraction are preserved in `../mask_locked_20260924/`.

Status: **visual review pending**, not canonically accepted or installed.
Rebuild using `python3 level_generation/ui/hud_inventory/paperdoll_review/identity_workflow/prepared/doll_01/contained_20260924/process.py` from the repository root.
