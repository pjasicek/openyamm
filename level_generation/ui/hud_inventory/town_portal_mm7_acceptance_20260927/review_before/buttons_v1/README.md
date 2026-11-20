# MM7 destination button review

The user approved the regenerated map, then requested the corresponding city buttons. These six hover textures
are derived from that exact map; no new imagegen call or geometric transform is involved.

Open the [interactive preview](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm7/)
to hover, focus, and select destinations. All destinations are enabled for review.
Default and highlighted crops are also visible in the [comparison sheet](evidence/buttons.png).

| Destination | Asset | Native rectangle x, y, width, height | x2 size |
| --- | --- | --- | --- |
| Castle Harmondale | `tpharmon` | 346, 271, 96, 66 | 192 × 132 |
| Tularean Forest | `tpavli` | 424, 126, 78, 66 | 156 × 132 |
| City of Steadwick | `tpwarl` | 211, 243, 82, 78 | 164 × 156 |
| Nighon | `tpisl` | 496, 311, 86, 80 | 172 × 160 |
| Celeste | `tpheav` | 502, 44, 80, 80 | 160 × 160 |
| The Pit | `tpdeja` | 58, 364, 88, 70 | 176 × 140 |

The game normally draws the map itself, then overlays the relevant hover texture while hovered or pressed.
`default/` retains exact normal-state crops for review and future provenance; `hover/` contains the six prospective
runtime exports. Both use opaque RGB on the same canvas. `masks/` holds the feathered light fields.
`original/` and `installed/` retain comparison artwork; `review_before/` preserves the previous background-only page.

The treatment matches the MM6 button recipe: a landmark-centered elliptical core and wider halo, screen-blended
with warm light. Mask radii fit each MM7 landmark. A four-pixel x2 border stays exactly equal to the background,
with a smooth ten-pixel fade inward. No pixels are moved, resized, blurred, or independently repainted.

[prepare_buttons.py](../prepare_buttons.py) reads the actual destination table and original BMP dimensions,
pins the approved map hash, checks current acceptance records, and writes [manifest.json](manifest.json).
It checks exact map crops, export sizes, unchanged borders, changes confined to the mask, exact restoration after
hover, and unchanged runtime/ledger files. It refuses to overwrite this work if it becomes accepted.

```sh
python3 -B level_generation/ui/hud_inventory/town_portal_fixup_review/mm7/prepare_buttons.py
```

The page's `?verify=1` mode checks all six new hover patches against the actual browser-rendered pixels,
unchanged surrounding map, exact reset after pointer exit, logical hit rectangles, keyboard focus, and selection.
[Browser validation](browser_validation.json) records the inspected captures and checks.

The background is user-approved; the six buttons are review candidates. No accepted ledger records or runtime
assets were changed by this preparation step.
