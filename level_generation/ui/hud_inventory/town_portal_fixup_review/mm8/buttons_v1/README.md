# MM8 destination buttons

Six matching hover textures are cut from the user-approved `attempt_03/townport.png` map. The normal crops
are exact background pixels; the hover copies apply warm light without moving, resizing or redrawing artwork.
No imagegen call is involved in this button revision. Acceptance publication and runtime deployment are pending.

Open the [interactive preview](http://127.0.0.1:8900/level_generation/ui/hud_inventory/town_portal_fixup_review/mm8/)
to hover, focus with Tab, and select any of the six destinations. Show all highlights or click areas for review.
The [comparison sheet](evidence/buttons.png) shows original hovers, exact map crops, new hovers and light masks.

| Destination | Runtime asset | Native rectangle x, y, width, height | x2 size |
| --- | --- | --- | --- |
| Alvar | `tp_alvar` | 269, 36, 55, 50 | 110 × 100 |
| Ravenshore | `tp_ravenshore` | 274, 174, 62, 43 | 124 × 86 |
| Baltazar's Lair | `tp_balthazarlair` | 14, 298, 63, 64 | 126 × 128 |
| Regna | `tp_regna` | 204, 348, 73, 46 | 146 × 92 |
| Shadowspire | `tp_shadowspire` | 444, 127, 76, 53 | 152 × 106 |
| Daggerwound islands | `tp_daggerwoundislands` | 460, 303, 61, 49 | 122 × 98 |

Names and positions come from the `townport` group in `town_portal_switch.txt`; missing width and height
values resolve to the native BMP dimensions. The six old table aliases are explicitly mapped to their runtime
names, following `GameplayUiRuntime::townPortalIconTextureName`. The Town Portal YAML supplies the 640 × 480 canvas.

The game draws the map as the normal state and overlays the destination texture while highlighted or pressed.
`default/` retains the exact normal crops; `hover/` contains the six proposed runtime PNGs. Both use opaque RGB
on the same canvas. `masks/` contains the eight-bit light fields. `original/` and `installed/` retain comparison
artwork, and `review_before/` preserves the previous background-only review page.

The warm screen-blend recipe matches the MM6 and accepted MM7 buttons. Each landmark has an elliptical core
and a wider halo. The outer four x2 pixels remain exactly equal to the background, with a smooth ten-pixel
fade inward. All geometric detail stays fixed; no blur, resampling or movement is applied to either state.

[prepare_buttons.py](../prepare_buttons.py) pins the approved background hash, reads native placements and
sizes, checks the accepted index, and writes [manifest.json](manifest.json). Validation checks exact crops,
export dimensions, unchanged borders, changes confined to the mask, exact reset after hover, and unchanged
runtime assets and ledger. It refuses to overwrite exports referenced by a later acceptance.

```sh
python3 -B level_generation/ui/hud_inventory/town_portal_fixup_review/mm8/prepare_buttons.py
```

The review page's `?verify=1` mode checks each exported hover against browser-rendered pixels, surrounding
map pixels, reset after pointer exit, logical hit rectangles, keyboard focus and click selection.
[Browser validation](browser_validation.json) records passing checks at x2 and native display sizes and
the inspected captures. The original, installed and corrected maps each use their matching button set;
the previous candidate and printed color reference are background comparisons only.
