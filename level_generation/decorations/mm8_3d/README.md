# MM8 decorations in 3D

Static 3D replacements for every visible decoration in the MM8 maps (161 types: 7,160 outdoor placements on 11
outdoor maps, 969 in 26 dungeons). All models are engine content (`assets_source/engine/models/`, installed with
`tools/install_model.py --engine`), so any world can bind them. Bindings: `assets_dev/worlds/mm8/models/decorations.yml`
(outdoor) and `indoor_decorations.yml` (dungeons). Builder brief: `BRIEF.md`. Inventory: `inventory.json`
(`scripts/inventory.py`).

## Shared models

- MM6 models, the same native images: `dec56` (729 dungeon torches) and `torch01` use `mm6_deco_torch01`; `rock01`,
  `rock02`, `rock03`, `rock04`, `rock06` and `rock10` use the MM6 boulders; `dec25` and `dec04` the MM6 campfire and
  log fire. Bound 2026-10-15; every MM8 dungeon torch mounts on its wall.
- MM7 art (the same native images under other names), split with the MM7 project (2026-10-15):
  - built by the MM7 project: beacon fires `dec40`-`dec43` (MM7 `dec60`-`dec63`) and magic pedestals `dec45`-`dec55`
    (MM7 `dec65`-`dec75`);
  - built here as `mm7_deco_*`: cauldron `dec26` (MM7 `7dec03`), trash heap `dec23` (`7dec01`), goblet `dec35`
    (`7dec48`) and fruit bowl `dec28` (`7dec08`).
- Coloured flame atlases from the MM7 project: `../shared_flames/`.

## Batches

| Folder | Contents | Placements |
|---|---|---|
| `palms/` | palms `tree01`-`tree09` | 742 |
| `trees_broadleaf/` | `tree10`-`tree13`, `tree18`, `tree25`, `tree31`, `tree59`, `tree60a`, `tree61a`, `tree62a` | ~1,800 |
| `trees_other/` | pines `tree29`/`tree30`, dead `tree28`, `tree14`-`tree17`, `tree19`-`tree21`, `tree62c`, `tree63b` | ~1,350 |
| `rocks/` | 30 new rock types, tar rocks `rock61`/`rock62`, rune stones `rock65`/`rock68`/`rock69` | ~1,000 |
| `plants/` | flowers, ferns, shrubs, corn, cacti, stumps, tumbleweed, lily pads (`plant*`) | 1,297 |
| `props/` | skeleton `dec05`, bones `dec29`/`dec21`, carrion `dec22`, barrel `dec03`, rune posts `dec13`-`dec17`, elf statue `dec01`, tableware, and the four `mm7_deco_*` models | ~680 |
| `animated/` | lantern `dec07`, chandeliers `dec08`/`dec27`, candlestick `dec02`, standing torch `dec06`, campfire `dec24`, bell buoy `dec30`, Plane of Air orb `dec57`, seaweed `dec58`, coral `dec59` | ~690 |

Order: pilot Dagger Wound Island (`out01`, the start map) first, then the remaining outdoor maps, dungeons and the
elemental planes. Each batch ends with the coordinator's bindings and in-game captures (no re-bake needed, see
Status). At the end, the MM8 decoration sprites are retired as in
`../../MM6_2D_RETIREMENT.md`.

## Status (done 2026-10-16)

- Coverage: every visible MM8 decoration placement is bound to a 3D model, 7,160/7,160 outdoor
  (`decorations.yml`) and 969/969 dungeon (`indoor_decorations.yml`); decorations regression suite passes.
- Batches (each batch folder's README has its models, bindings, sources and compromises):
  - `props/`: all 19, the four `mm7_deco_*` included (MM7 binds them too). Bone pile `dec29` reads thin and carcass
    `dec21` lumpy (polish candidates, small and few).
  - `animated/`: all 10 (inside-out faces fixed; compromises in its README).
  - `palms/`: all nine `mm8_deco_tree01`-`tree09`, one shared atlas.
  - `trees_broadleaf/`: all 11 (tree25/tree13 crown-shape compromises).
  - `trees_other/`: all 12; the desert and gorge trees (tree14/15/16/19/20/21) on trunks traced from the sprites.
  - `rocks/`: all 33 (tar rocks with raised tar ropes; rune stones with plants).
  - `plants/`: all 44 types (plant08 reuses plant02).
  - Shared: MM6 torches, boulders and fires; the MM7 project's beacons `dec40`-`dec43` and pedestals `dec44`-`dec55`
    (`mm7_deco_dec60`-`dec75`, MM7 number = MM8 number + 20).
- Stat barrels (`dec03`): coloured liquid overlays by barrel state (`worlds/mm8/models/decoration_overlays.yml`,
  `mm8_deco_barrel_liquid_<colour>`, built by `props/scripts/build_liquids.py`), checked in `review/ingame/out01_barrels/`.
- Manifests move to engine scope (2026-10-16, MM7 session `openyamm-08` does the move and the
  `InteractiveDecorationRules.cpp` bare-name fix, dec01/dec32 matching MM8 statue/bowls): do not edit
  `worlds/mm8/models/*.yml` after the move; add entries to `engine/models/*.yml`.
- Hanging fixtures (`dec07`, `dec08`, `dec27`): the native sprites overlap the ceiling by a per-map amount, so the
  indoor bindings carry per-map `z_offset`s that bring each chain to its ceiling (d24 -56, d06 -32, d27 -31, d09/d06
  `dec27` -39, d40 0).
- Face orientation: every installed model passes `animated/scripts/check_winding.py` (the BRIEF requires it); Blender
  review renders draw back faces the engine culls.
- Bakes: no re-bake is needed for decoration changes. The MM8 (and MM6) bake profiles leave `decoration_shadows`
  off, so the baked lighting does not depend on decoration models; the game casts their shadows at runtime.
- In-game checks (`review/ingame/`): `d13_torches/`, `d24_lanterns_hood/`, `d40_chandeliers2/`, `out01_first/`,
  `out01_plants_close2/`, `out04_props/`, `out06_props/`, `out07_broadleaf/` (about 840 fps, desktop GPU),
  `elema_3d/` and `elemw_3d/` (same cameras as `review/native_ingame/`). Tour `position` is the party's feet; the eye
  is higher, so a target lands below the crosshair.
- Sprites retired: the 369 restored sprites in `assets_dev/engine/decorations_x2/` (29 MB) that only bound MM8
  placements showed are archived in `assets_legacy/decorations_x2_mm8_20261016/` (git-ignored; list in
  `retire_candidates.json`). The MM7 session then archived the remaining bound-only sprites of every world to
  `assets_legacy/decorations_x2_20261016/` (`../scripts/retire_decoration_sprites.py`). Maps load with no
  missing-texture errors and draw no decoration sprites.
- Engine note from the palm contrast pass: sky reflection and specular ignore the vertex-colour occlusion, so glossy
  foliage lifts its dark interior (palms kept gloss at 0.06-0.15 for that reason).
- Engine extras for lights (2026-10-16, `engine/models/ModelAsset.h`, unit-tested): `openyamm_billboard: "card"`,
  `openyamm_additive`, `openyamm_flicker`; static blended primitives draw after opaque and alpha-tested ones (flames
  no longer hidden behind foliage without ambient occlusion).
- Quality pass (user-approved 2026-10-16, done):
  - Triangles: every tree reduced to about 3,000 at LOD0 (desert and gorge trees about 3,800). The MM8 LOD0 sum over
    all placements fell from 20.5 M to 15.1 M (out07 7.5 M to 4.8 M, out03 3.5 M to 2.3 M). The out07 forest frame
    went from 374 k triangles at about 840 fps to 331 k at about 1,117 fps (desktop GPU, same cameras,
    `review/ingame/out07_reduced/`).
  - Colour: palms (contrast pass, luminance spread about doubled, `review/ingame/out01_palms_contrast/`),
    broadleaf and other trees (sunlit lift), darker pines (`review/ingame/out03_pines2/`).
  - Crowns: maples tree62c/tree63b and tree17 on traced skeletons with open crowns; ragged desert pads.
  - Rocks: native shading transfer on all 33; sprite cracks and veins projected on rock07/16/24/33.
  - Props: bone pile, carcass and carrion rebuilt with Meshy (90 credits).
  - Lights: additive card candle flames, ragged torch head, broad campfire blaze with sparks, flicker, per-card
    phase (`review/ingame/d40_lights/`, `out02_lights2/`).
  - The bark UV axis bug from the MM6 tree pipeline is fixed in the MM8 tree builders (furrows along the limbs).
- Leaf overdraw pass (user-approved 2026-10-16; MM8 done): leaves were about half the GPU frame in the out07 forest
  (0.45 of 0.90 ms). Engine: opaque parts of foliage models in the depth prepass first, batches nearest first
  (`engine/render/MODEL_RENDERING.md` "Foliage depth order"). Assets: layer gate (target 2.5-3 layers per covered
  pixel at LOD0/LOD1, about 2 at LOD2), inner crown shells, fewer cards. Palms within target (thinned LOD2);
  trees_other (desert trees 8-11 -> about 3 layers) and trees_broadleaf (4.4-6 -> about 2.5-3.2; open crowns and the
  willow 3.4-3.9) done. Leaf shading: the leaf shader variant skips the normal map and sky reflection. Frozen out07
  view: 0.90-0.93 -> about 0.80 ms GPU per frame; leaves about 0.34 ms (depth prepass 0.12, shading 0.22). MM6 trees
  (4-12 layers) got the same pass in `../mm6_trees_overdraw/`: all 19 done, LOD0 2.6-3.8 layers, under-crown carve,
  checked in New Sorpigal (`../mm6_trees_overdraw/review/ingame_oute3/`).
- Black crown fix (2026-10-16, done): the contrast and overdraw passes had baked near-black leaf vertex colours and
  inner shells (COLOR_0 0.02-0.05). Palms: leaf floor 0.2 of the tint, ground bounce on undersides. Broadleaf and
  other trees: shells textured from their own leaf atlas at about 0.3-0.5, leaf floor 0.15-0.17, pines on their own
  darker needle atlas. Every tree now gates an under-crown view (2 m up by the trunk, 60 degrees up) and a low
  three-quarter view. In game from below: `review/ingame/out01_palm_hearts/`, `out03_pines4/`, `out07_under/`.
  Android cooks are user-only (`tools/cook_android.sh`).
