# New Sorpigal 3D decorations — rock, barrel and tree (2026-10-07, tree v2 2026-10-08)

Static 3D replacements for the MM6 New Sorpigal decoration sprites `6rock01` (image `rok1`, 41 placements),
`bigbarel` (4 placements), built from Poly Haven CC0 scans, and `6tree01` (213 placements, built with Sapling Tree
Gen: see [tree01/README.md](tree01/README.md)). All three are bound in `assets_dev/worlds/mm6/models/decorations.yml`
for `oute3.odm` and drawn in game.

Living trees for other MM6 maps (2026-10-09, not bound yet): `6tree07`, `6tree13`, `6tree14`, `6tree17` (autumn),
`6tree18` (dark conifer), `cac25` (desert tree with rosette pads), `swptree2` (tall swamp cypress) and the snow
conifers `snotre01`, `snotre03`, `snotre05` ([trees/README.md](trees/README.md)) →
`assets_dev/worlds/mm6/models/mm6_deco_{tree07,tree13,tree14,tree17,tree18,cac25,swptree2,snotre01,snotre03,snotre05}.glb`.

Desert palms for other MM6 maps (2026-10-09, not bound yet; procedural, painted atlases, impostor LOD3): `6tree21`
fan palm, `cac19` banana plant, `cac18` banana clump, `cac24` dragon tree, `cac17` yucca clump, `cac23` tall yucca
clump, `cac3` agave ([desert/README.md](desert/README.md)) →
`assets_dev/worlds/mm6/models/mm6_deco_{tree21,cac19,cac18,cac24,cac17,cac23,cac3}.glb`.

Flowers and rocks for other MM6 maps (2026-10-09, Misty Islands, Silver Cove, Castle Ironfist, Eel Infested
Waters; not bound yet): `6flower06` rose bush and `6flower08` sunflower clump ([flowers/README.md](flowers/README.md)),
`6rock07` and `6rock14` scan rocks ([rocks/README.md](rocks/README.md)) →
`assets_dev/worlds/mm6/models/mm6_deco_{flower06,flower08,rock07,rock14}.glb`.
Eight more scan rocks (2026-10-09, not bound yet): `6rock03`, `6rock04`, `6rock05`, `6rock06`, `6rock08`, `6rock09`,
`6rock12`, `6rock13` ([rocks/README.md](rocks/README.md)) → `mm6_deco_rock{03,04,05,06,08,09,12,13}.glb`.

Dead trees (2026-10-09, not bound yet): bare snags `6tree28` and `6tree27`, dark shrub `6tree29`, gnarled green swamp
tree `swptree4` and cut stump `stump5a`, from a procedural branch generator with twig cards and impostors
([trees/DEAD_TREES.md](trees/DEAD_TREES.md)) →
`assets_dev/worlds/mm6/models/mm6_deco_{tree28,tree27,tree29,swptree4,stump5a}.glb`.

Succulents for the MM6 desert maps (2026-10-09, not bound yet): procedural cacti `cac8` (golden barrel), `cac5`,
`cac16`, prickly pears `cac7`, `cac10`, `cac15`, silver sage on rock `cac27` and dry weeds `snoweed1`
([succulents/README.md](succulents/README.md)) → `assets_dev/worlds/mm6/models/mm6_deco_<id>.glb`.

outd2 props (2026-10-09, not bound yet): `ped06` marble pedestal, `foodbowl`, `smlbarel` keg and the impaled corpses
`corpse04/05/06/16` (posed MM6 peasant models on bloody stakes) in `props/` ([props/README.md](props/README.md),
[corpse sheet](props/review/corpses_compare.png)) → `assets_dev/worlds/mm6/models/mm6_deco_{pedestal,foodbowl,keg,
corpse04,corpse05,corpse06,corpse16}.glb`.

## In game

Four more maps (2026-10-09): Misty Islands (`oute2`), Silver Cove (`outd1`), Castle Ironfist (`outd3`) and Eel Infested
Waters (`oute1`) are fully 3D decoration-wise: every visible decoration on them (155 / 517 / 269 / 171 placements) and
on New Sorpigal (476) is a model. New models: trees `6tree10`, `6tree15`, `6tree25`, `swptree1` (swamp cypress:
flat foliage tiers, hanging moss) and `swptree3` (banyan with aerial roots) in `trees/`; flowers `6flower06` (rose
bush) and `6flower08` (sunflowers) in `flowers/`; rocks `6rock07` and `6rock14` in `rocks/`; campfire `cmpfyr00`,
burning rock `brnrock0`, flag `fla1__01` and skull pile `sklplrev` in `props/`. Bindings in
`assets_dev/worlds/mm6/models/decorations.yml` (heights = native sprite pixels × DSFT scale, like the existing
ones); the five maps are re-baked with the 3D casters (`tools/lighting/bake_outdoor.py`, under a minute each).
Captures: [Misty Islands](review_ingame/four_maps_20261009/misty_islands.png) ·
[Silver Cove](review_ingame/four_maps_20261009/silver_cove.png) ·
[Eel Infested Waters](review_ingame/four_maps_20261009/eel_infested_waters.png) ·
[Castle Ironfist cypresses](review_ingame/four_maps_20261009/castle_ironfist_cypress.png) ·
[campfire, burning rock, banyan, flag](review_ingame/four_maps_20261009/props_and_swamp_trees.png) ·
[sword stone v2](review_ingame/swordstone_v2.png).
- Cost (world frozen, all decorations on vs off; other sessions' games ran during some runs): Eel Infested Waters
  GPU 311 → 474 µs; Silver Cove about +35 µs GPU.
- Open: the Castle Ironfist flag stands on the castle tower (invisible from the ground, like New Sorpigal's); some
  `swptree1` placements stand in water, as in the original map.


All decorations (2026-10-08): every New Sorpigal decoration except the ship (replaced in the map) is now 3D:
flowers (`flowers/`), cauldrons, fountains, sword in the stone (+ pulled state), buoy, surf rocks and flag (`props/`).
[Flowers](review_ingame/flowers.png) · [fountain, sword, buoy, cauldron](review_ingame/props_fountain_sword_buoy.png) ·
[cauldron fire](review_ingame/props_cauldron_fire.png) · [surf rock](review_ingame/props_surfrock_b.png) ·
[hover outline](review_ingame/hover_outline.png).
- Engine: material extras `openyamm_uv_scroll` (fountain water, foam), `openyamm_flipbook` (cauldron fire),
  `openyamm_flutter` (flag cloth); hover outline on modelled decorations; SetSprite swaps to the sword-less stone.
- Fountain square GPU: 483–507 µs in 3D vs 517 µs with sprites.
- Open: `searka01` stands inside the hull of the ship that replaced the map's original one, so it renders black
  (no baked light inside the hull) — move or remove that decoration in the map
  ([capture](review_ingame/props_surfrock_a_inside_ship.png)). The flag on the tower roof is barely visible from the
  ground, as before. Gazania heads read a little more yellow than the sprite's orange.


All trees (2026-10-08): every New Sorpigal tree species is 3D (`trees/`, one species-configured pipeline):
[species](review_ingame/all_trees_species.png) · [red tree, 6tree01](review_ingame/all_trees_red_and_tree01.png) ·
[roadside](review_ingame/all_trees_roadside.png) · [hill](review_ingame/all_trees_hill.png) ·
[walk clip](review_ingame/all_trees_walk.mp4) ([sheet](review_ingame/all_trees_walk_sheet.png)).
Field view, 1600×900, NVIDIA: GPU 436 µs with sprites → ~660 µs with all trees, CPU world render unchanged
(~240–255 µs), 230k triangles. Texture memory 921 → 1,125 MB: identical images are shared across models, the far
maps are 512²; each species still has its own graded bark colour, leaf atlas and far maps (~22 MB). GPU texture
compression is the next memory step. The food-tree pair (tree06a → 6tree06 on picking) swaps to the same tree
without fruit (regression `mm6_decoration_models_map_new_sorpigal`).


Tree v2 (2026-10-08): [field](review_ingame/tree01_v2_field.png) · [roadside](review_ingame/tree01_v2_roadside.png) ·
[under the crown, both sides](review_ingame/tree01_v2_under_crown.png) · [walk clip](review_ingame/tree01_v2_walk.mp4)
([sheet](review_ingame/tree01_v2_walk_sheet.png); switch close-ups: [impostor](review_ingame/tree01_v2_impostor_switch.png),
[LOD2→1](review_ingame/tree01_v2_lod2_switch.png)) · [rocks](review_ingame/rocks.png). v1 captures: `review_ingame/v1/`.

- The engine draws every placement of one model with one instanced draw per LOD primitive
  (`Engine::ModelStaticGroup`, `ModelRenderer::renderStatic`); the decoration keeps its collision, events, picking
  and SetSprite switches (a switched decoration shows the new sprite instead of the model). Water reflections keep
  the sprites.
- Trees: real-scale leaf sprays in ~90 clumps with baked canopy occlusion (`COLOR_0`), light through leaves
  (`openyamm_translucency`), reduced leaf specular (`openyamm_specular` 0.1; v1 leaves seen edge-on against the sun
  turned near-white: [v1 sheen](review_ingame/v1/tree01_v1_sheen.png)), wind, clump cards at LOD2, a camera-facing
  impostor at LOD3 below 160 px (`lod_pixels: [500, 250, 160]`), and a 0.3 s dithered crossfade between levels.
- LOD consistency (Eevee, per level vs the previous): mean colour within 2.6/255, coverage within 3.3 %; in the walk
  clip the switches are not visible.
- Cost (field of `6tree01` next to the party, 1600×900, NVIDIA): CPU world render unchanged from the sprites
  (~250 µs), GPU 445–490 µs with sprites → 560–568 µs with v2; see `output/performance/actor_models_20261007/README.md`.
- Open: small dark star shapes where leaves converge at spray centres; less contrast than the sprite (its gaps are
  black, ours show sky); sun shadows on the ground are faint in captures.

## Choice

- Rock: `namaqualand_boulder_04` from the +270° side reads like the sprite (a rounded wedge rising to one side);
  `_03` was too blocky and flat-topped, `rock_07`/`rock_09` too dark and slabby, `stone_01` pink. Its orange-rust
  albedo is graded to the sprite's sandy tan (saturation 0.5, linear gain 1.67 / 1.34 / 0.68): lit mean in the
  review render 144/122/90 vs sprite 147/119/80. Thumbnails of all candidates: `source_thumbs/`.
- Barrel: `wine_barrel_01` (upright wooden barrel, iron hoops); `barrel_03` is a blue oil drum. Wood graded toward
  the sprite's amber (saturation 1.5, gain 1.2 / 1.0 / 0.32; metal texels keep the scanned iron colour).

## Build

```bash
cd level_generation/decorations/mm6_new_sorpigal_3d
blender --background --python scripts/build_prop.py -- rock      # or barrel; settings in scripts/props.json
blender --background --python scripts/review_render.py -- rock rock/work/rock_export.glb 0
python3 scripts/review_sheet.py rock rok1 2400 960 290 96        # sprite_compare / lods / turntable sheets
python3 ../../../tools/link_static_model_lods.py rock/work/rock_export.glb rock/work/rock_linked.glb
install -m 0664 rock/work/rock_linked.glb ../../../assets_dev/worlds/mm6/models/mm6_deco_rock01.glb
python3 scripts/validate_glb.py ../../../assets_dev/worlds/mm6/models/mm6_deco_rock01.glb 2500 1000 300 100
```

`scripts/build_prop.py` (see its docstring):
- **rock (decimate):** merged scan → collapse to 2400 → dome unwrap (one seam round the flat underside, minimum
  stretch; Smart UV islands smeared visibly under LOD collapse) → LOD1–3 collapsed from LOD0 with its UVs.
- **barrel (lathe):** the scan's staves and hoops are separate shells that crack under decimation, so every LOD is a
  lathed proxy of the scan's radial profile (40×14 / 24×9 / 14×6 rings with the top chime recessed 3.6 cm to the
  lid; LOD3 10×3 with a flat top). One UV layout function for all LODs (side strip + lid and base discs).
- **stat barrel liquids (2026-10-12):** `barrel/scripts/build_liquids.py` writes seven glossy discs (red Might, yellow
  Accuracy, blue Personality, orange Intellect, green Endurance, purple Speed, white Luck) in the barrel's asset
  space. `worlds/mm6/models/decoration_overlays.yml` shows one by barrel state; drinking
  (state 0) removes it. Install each with `tools/install_model.py <glb> --engine`.
  v2 (2026-10-13/14, player feedback that the colours were too sharp, then the user's requests): muted colours,
  pale foam speckle with small bubbles after MM9's `liquid-*.dtx`, a slow `openyamm_uv_scroll` drift and a glossy
  surface (roughness 0.1, specular 0.6) about 7 % of the barrel's height below the rim (`SURFACE_Y` 0.81), so a
  barrel reads full without filling to the brim and, drunk, empty. The clear liquid blends at 50 % opacity (`ALPHA`),
  so the dark staves show faintly through it; foam and bubbles are opaque.
- **open barrel (2026-10-14, `rim.open` in `props.json`):** LOD0–2 have no lid. `open_top` in `build_prop.py` adds,
  after the bake, an inner wall following the bulge (a hoop-free band of the side strip, v 0.535–0.6, stretched
  along the grain) and a floor on the lid planks, darkened with depth by COLOR_0; the lid-plank texels get a low
  `openyamm_specular_mask` value so the floor does not reflect the sky. LOD3 keeps its flat top. Rebuild with
  `build_prop.py -- barrel`, `link_static_model_lods.py`, then `tools/install_model.py
  barrel/work/barrel_linked.glb --engine --name mm6_deco_barrel.glb`; re-bake `oute2` and `oute3` lighting.
- Optional `rocks.json`/`props.json` keys: `scale`, `peak` (surf rocks), `parts` (extra scans joined before the
  bake; LOD0 then comes from a 6 mm voxel remesh of the union) and `ground_band` (lower each level's base band onto
  the ground after decimation), `grade.contrast` (luma power about the mean, for flat-albedo scans) and
  `roughness_min` (roughness floor for glossy scans); absent keys leave a build unchanged.
- Bakes from the full scan (Cycles, selected to active): normal (scan normal map included), base colour, roughness,
  metal and AO (from the ARM map), 16 px margins.

## Review

`rock/review/` and `barrel/review/`: `sprite_compare.png` (native | enhanced | 3D LOD0), `lods.png`, `turntable.png`;
`barrel/review/top_views.png` (55° views of all LODs of both props).

## Known compromises

- Rock LOD3 (96 tris) shows a small texture smear at one base corner, where collapsed faces cross the underside
  seam; it is only used below ~80 px. LOD bases sit 6–16 mm above y = 0 (scan bottom collapsed upward).
- The barrel scan has six thin hoops and a bung; the sprite has three thick riveted hoops. Same object, different
  hoop style. LOD3's flat top samples the lid disc up to the outer radius (a lighter rim ring at < 80 px).
- Lit-colour matching used Eevee review lighting, not the engine's; check the in-game look once bound.
