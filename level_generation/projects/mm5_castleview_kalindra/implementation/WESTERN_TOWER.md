# Great Western Tower: two separate access routes

The source-backed [layout](../layout.json) retains the keyed ground entrance at Area A3 cell 4,9 and Dreyfus's
roof-first access problem. The tower's existing 1536-square reservation stays at (-17664,14592), pad Z800.
It uses the Garrote fortified material family, with original geometry and no imported BModel vertices.

The main shaft is 1344×1408, with an ordinary 128×256 east-facing ground door. Sparse upper barred apertures,
closed projected stone courses and a crenellated crown distinguish it from Ellinger's narrow pitched octagon.
The terrace is 2432 above the pad. Lowering the earlier 2560 terrace proposal leaves space for a full-height upper
door and its small pitched cover while retaining the 2816 maximum above the pad. The low parapet is 128 above
the walking surface; taller merlons reach the crown. The upper doorway faces a clear terrace, not an exterior stair.

| Identity | Position / height | Current behavior |
| --- | --- | --- |
| `mm5:sw/western/entrance` | (-16928,14592,800), facing east | Separate named status stub; no key/pass requirement or missing BLV load |
| `mm5:sw/western/roof_entrance` | (-17792,14400,3232), facing east | Separate named status stub; future upper BLV access |
| `mm5:sw/western/ground_return` | (-16672,14592,800) | Inactive future return marker in semantic source |
| `mm5:sw/western/skyroad_roof` | (-17440,14720,3232) | Inactive future Skyroad arrival / upper BLV return marker on the terrace |

The already-recorded named mirror destination remains (-16128,14592); it is distinct from the roof arrival.
The [extracted transfer inventory](../../mm5_world_feasibility/inventory.json) records both original pairs:
Area A3 (map 3,4,9) → Western Tower level 1 (map 57,11,8), using quest item 40; the return leads to A3 (5,9).
Skyroad A3 (map 91,4,9) → Western Tower level 4 (map 60,11,8), whose return leads to Skyroad A3 (4,9).
Those future destinations are preserved in [the source route record](western_routes.json); no source key code,
numeric map alias or reward is activated by the current placeholders.
There is no exterior staircase or automatic teleport that bypasses the future Skyroad route. Roof review uses a
placed test party because the connecting Skyroad and tower BLVs are deliberately outside this environment milestone.
Dreyfus, obedient/heretical clerics, statuette retrieval and quest state remain source/interior records, not outdoor actors.

## Authoritative sources and review

[prepare_architecture.py](../prepare_architecture.py) owns the shaft, elevated roof house, two venue positions and
future arrival markers. [author_watchtower.py](../author_watchtower.py) authors the original shaft, terrace and
battlements. The shared project author now accepts explicit component bases and venue depth/height, allowing the
upper door to sit on its actual facade. All previously exported 215 OBJ files remained byte-identical after this change.
Ground road/frontage and scenery-approach calculations exclude elevated venues.

Inspected the first [oblique](../review/western_v1/western_oblique.png), eye and roof renders. The roof originally
used wall masonry on its walking face, producing an inappropriate repeated stripe. Replaced it with Garrote's
calibrated `t32a05b` paving. The repeated [roof view](../review/western_v2/western_roof.png) shows the corrected
floor and full upper doorway. The [distant eye view](../review/western_v2/western_eye.png) shows the full tower;
the first eye camera was too close to include both base and crown. These are actual-heightfield Blender views with
neutral terrain material, not native lighting or foliage acceptance.

Source edge sampling finds Z800 under the whole main shell footprint, against a skirt bottom Z736. Native
`02dc021bf89239949fcced91728068a604f9de568d2be1492adaad7e24fba59b` contains the four tower models.
The [native geometry check](../review/western_v2/native_geometry.json) verifies both door quads and event bindings,
the Z3232 upward terrace face, 36 approach-support samples and the elevated house's embedded skirt. The main shell
also passes the normal native-terrain foundation audit. The elevated house is intentionally excluded from that
ground-only audit.

Actually inspected the [ground click](../review/gameplay/mm5_western_ground_v1_click.png),
[roof arrival](../review/gameplay/mm5_western_roof_v1_arrival.png),
[roof click after walking forward](../review/gameplay/mm5_western_roof_v1_click.png),
[restored roof view](../review/gameplay/mm5_western_roof_v1_restored.png), and
[road approach](../review/gameplay/mm5_western_context_v1.png).
The two clicks show their distinct named stubs. Ordinary roof movement and F9/F10 preserve the supported position;
decoded saves show unchanged map, gold, food, health and inventories. The
[review record](../review/western_v2/native_review.json) retains image/native/binary hashes and save evidence.
The surrounding regional scenery and Dreyfus's nearby refuge remain unfinished. The starting-save checkpoint
has been [refreshed to this native map](../review/playtest/start_western.json).
