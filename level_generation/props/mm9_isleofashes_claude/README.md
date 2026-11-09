# MM9 Isle of Ashes props as 3D decorations (2026-10-29)

The props of MM9's Isle of Ashes, converted from their original LithTech ABC models into OpenYAMM 3D decorations for
the remade map ([MM9 rework plan](../../../devdocs/mm9_rework/PLAN.md), Geometry route step 3;
[map project](../../projects/mm9r_isleofashes/README.md)). The terrain and the buildings are another session's work.
No paid services: textures are the MM9 skins enlarged x4 with Lanczos (a stopgap: the Codex x4 pass replaces them; props built
before 2026-10-30 used Real-ESRGAN), the flames the shared
CC0 Unity Labs flipbook (`../../decorations/mm6_dungeons_3d/textures/FLAMES.md`).

## Outputs

- 16 models installed with `tools/install_model.py --world mm9`: sources `assets_source/worlds/mm9/models/mm9_deco_*.glb`,
  cooked runtime copies `assets_dev/engine/models/`. All pass `check_winding.py` (0 inverted closed parts).
- `../../projects/mm9r_isleofashes/props.json`: 59 placements (34 props, 25 trees) in the remade map's frame.
- `non_props.json`: the objects that are not decorations here (chests, doors, destructible walls, effects, helpers).
- `../../projects/mm9r_isleofashes/review/props_sheet.png`: contact sheet (LOD0 front, three-quarter, side,
  behind-above, below; LOD1 and LOD2 three-quarter; back faces culled as in the engine).
- The decorations are MM9 world content (`../../../devdocs/WORLD_DECORATION_CONTRIBUTIONS.md`): rows 2001-2017 in
  `assets_dev/worlds/mm9/data_tables/decoration_data.txt` (decoration_list_id 2000-2016), sprites 24801-24817 in
  `worlds/mm9/rendering/sprite_frame_data_world_decorations.yml`, bindings in `worlds/mm9/models/decorations.yml`;
  `scripts/tables.py` prints new ones and `--apply` appends them.

| Model | Source ABC (skin) | Placements | LOD triangles | Binding height | Notes |
|---|---|---|---|---|---|
| `mm9_deco_book` | BOOK (BOOK) | 1 | 252 | 30.8 | closed bind pose; the object's pitch/roll baked in (lies tilted on the lectern) |
| `mm9_deco_coatrack` | COATRACK1 | 1 | 410 / 204 / 102 | 92.3 | wall mounted (MM9 position kept) |
| `mm9_deco_cookpot` | COOKPOT | 1 | 285 / 143 | 145.2 | cut-out chain (MASK); flame cards at its FireNode; light 160 |
| `mm9_deco_cot` | BED_COT | 1 | 84 | 81.6 (x1.2) | |
| `mm9_deco_dresser` | DRESSER (DRESSERPLAIN) | 1 | 20 | 141.5 | |
| `mm9_deco_logsburning` | LOGSBURNING | 1 | 126 | 79.9 (x0.75) | three flame cards (MM9's Fire object on it); light 256 |
| `mm9_deco_podium` | PODIUM03 | 1 | 160 | 136.7 | lectern under the book |
| `mm9_deco_roundtable` | TABLEROUND4 | 1 | 90 | 92.4 | |
| `mm9_deco_shipwreck` | VIKINGSHIP-WRECK (VIKINGSHIP) | 1 | 723 / 361 / 179 | 1407.5 | MM9's slow "Rocking" clip dropped (static) |
| `mm9_deco_skull` | GIBS/SKELETON/BIP01 HEAD (SKELETON1) | 2 | 102 | 18.5 (x0.7) | |
| `mm9_deco_statstone` | STATSTONE (STATSTONERED) | 1 | 326 / 152 / 80 | 220.7 | orb on its own material: glow pulse + slow texture scroll for MM9's "Rotate" |
| `mm9_deco_stonedebris02` | DEBRIS/STONEDEBRIS02 (LUMBERSTONEDEBRIS) | 5 + 4 | 32 | 59.0 / 88.4 (x1.5) | two decorations, one model |
| `mm9_deco_stonedebris03` | DEBRIS/STONEDEBRIS03 | 8 | 64 | 50.6 | |
| `mm9_deco_stool` | STOOL03 | 2 | 56 | 118.5 | |
| `mm9_deco_vikingship` | VIKINGSHIP | 2 | 842 / 421 / 210 | 995.5 | |
| `mm9_deco_well` | WELL | 1 | 350 / 175 / 87 | 255.3 | |

Binding height = model height x the MM9 object's Scale (the engine scales a model to its binding height and an ODM
entity has no scale), so a prop placed at two scales is two decorations (`mm9_stonedebris02_x150`). Decoration
names are `mm9_<prop>`; each binding uses `yaw: facing`.

## Route (`scripts/`)

1. `inventory_raw.py`: the raw DAT objects -> `work/raw_objects_compact.json`.
2. `convert_all.sh`: `tools/mm9_import_discovery/convert_abc_model.py` (venv `work/venv` with pygltflib) per model,
   rigid export (the book: full, its pages are skinned), LOD 0 and each native ABC LOD -> `work/raw/<prop>/`.
   Also the two trees for reference (not installed). Binding origins: `work/binding_origins.json` (from the
   transcoder's `abc_static_model_placement_info`).
3. `textures.py`: Lanczos x4 with 16 wrapped pixels of padding (seamless tiles), colour bled under transparent texels,
   unsharp 0.7 px -> `textures/`.
   `orb_texture.py`: the stat stone's red block cropped and mirrored into a horizontal tile.
4. `build.py` (Blender, `blib.py`): asset frame (below), clean (weld, degenerate and duplicate faces, one-triangle
   pieces such as the cookpot's fire socket), faces wound to agree with the ABC's authored normals, open pieces
   (sails, ropes, chains, cloth, thin planks) on a double-sided copy of the material, closed pieces single-sided,
   normals smooth within 40 degrees (hard beyond), COLOR_0 vertex occlusion, base centre at the origin. LODs only
   from 1000 triangles (guidelines: skip LODs for simple assets): about 50 % / 25 %, the native ABC LOD when its
   count is near, else a collapse decimation; the cookpot keeps one LOD (a 25 % pot collapses).
5. `finish.py [--install]`: alpha modes, double-sided, unlit flame (`openyamm_billboard: "card"`, which turns a flame
   about its own centre and keeps an off-axis torch's flame on its head; `openyamm_flipbook [16, 4, 30]`), orb extras (`openyamm_pulse [0.35, 2.5]`, `openyamm_uv_scroll [0.04, 0]`, emissive), LOD linking
   (`tools/link_static_model_lods.py`), checks (COLOR_0, base on the ground, decreasing LODs, `check_winding.py`),
   then `tools/install_model.py --world mm9`.
6. `review.py` (Blender) and `contact_sheet.sh`: review renders and the sheet.
7. `tables.py`: decoration variants -> `work/decorations_plan.json`; prints (or `--apply`: appends) the MM9 world's
   rows, sprites and bindings (existing names keep their numbers).
8. `placements.py`: `props.json`, with an end-to-end check per placement; `non_props.json` from `non_props.py`.

Rebuild everything:

```sh
cd level_generation/props/mm9_isleofashes_claude
python3 scripts/inventory_raw.py && scripts/convert_all.sh
python3 scripts/textures.py && python3 scripts/orb_texture.py
blender --background --python scripts/build.py
python3 scripts/finish.py --install
blender --background --python scripts/review.py && scripts/contact_sheet.sh
python3 scripts/tables.py            # --apply appends new decorations to the MM9 world files
python3 scripts/placements.py && python3 scripts/non_props.py
```

## Frames and the placement check

The raw GLB holds the ABC model space x 2.56 in LithTech axes. The old isle's transcoder bakes a prop at
`OpenYAMM = Rz(-yaw_LT) * Scale * swap(model + binding origin) * 2.56 + swap(Pos) * 2.56` with `swap(x, y, z) =
(x, z, y)`, plus a floor drop for MoveToFloor objects (`check_bake_fit.py` matches every baked BModel to under one
unit). The engine maps an asset's Blender `(x, y, z)` to OpenYAMM `(-x, -y, z)` at yaw 0, so the asset is the raw
import mirrored in X (faces reversed). `placements.py` places each finished LOD0 the way the engine does (glTF to
OpenYAMM, binding height / bounds height, facing, entity position) and compares it with the old baked BModel of the
same object: median vertex distance 0.3 to 1.2 units for all 34 props.

## props.json

Per entry: `source_object`, `source_name`, `source_model`, `decoration`, `decoration_list_id` (row number - 1),
`x`, `y`, `z` (the asset origin: base centre), `yaw_degrees` (the entity facing; 0 faces +Y), `scale` (relative to
the decoration's binding height: 1.0 for props, the tree scale for trees), `snap_to_ground`, plus
`base_above_mm9_terrain`, `base_above_remade_ground`, `keep_z_reason`, `interactive` and, for trees,
`target_height`. Prop ids are marked `decoration_list_id_provisional`; the name is the stable key.

- `snap_to_ground: true` (28: the 25 trees, the stat stone, the well, the cookpot): the prop stands on MM9's own
  terrain surface (within 6 units of the terrain polygons the conversion reads), so it should follow the remade
  height map (which differs from it by up to about 120 units here).
- `false`, keep z (31): the castle rubble (MoveToFloor, dropped onto the castle top in the old bake), the bunker's
  book and lectern, the hut furniture (cot, dresser, table, stools on the hut floor 10 units above the terrain; the
  log pile at terrain level beside the table), the coat rack (wall), the boats (afloat, keel at -121) and the wreck
  (sunk, base -501), and the two skulls (MM9 puts them 240-300 units over the terrain: on a rock or ledge; check
  when the structures are in).
- The hut stools are MoveToFloor 0 with Pos on the floor; the old bake centred them on Pos (half sunk), so their
  base is put at Pos (on the floor the cot and table drop to).
- `interactive`: StatStone (500), WellMMIX (770) and Cookpot (773) are MM9 gameplay classes; their events are the
  map session's.
- Left out: object 561, a second log pile at scale 0.7 inside 766 (each had its own Fire object).

## Trees

The MM9 trees are not converted (plan: vegetation from the MM6-MM8 set). `TREE05` (a tiered pine with a bare trunk
foot, `TREESPR5`) maps to MM8's wide pine `tree29` (row 512, id 511, binding 976); `TREE06` (a dense conical spruce,
`TREESPR6`) to MM8's spruce `tree30` (row 515, id 514, binding 1000). Target height = the MM9 tree's whole height
(ABC 497.6 / 386.8 LithTech units x 2.56: 1274 / 990) x the object's Scale; trees stand on their Pos.

| MM9 | Decoration | Placements | MM9 scales -> `scale` |
|---|---|---|---|
| Tree05 | `tree29` | 10 | 1.0 -> 1.305 (2), 1.3 -> 1.697 (8) |
| Tree06 | `tree30` | 15 | 1.0 -> 0.99 (9), 1.2 -> 1.188 (2), 1.3 -> 1.287, 1.4 -> 1.386 (2), 1.5 -> 1.485 |

An ODM entity has no scale, so `tree29`/`tree30` draw at their binding height (+-12 % jitter) unless the map
session adds MM9 tree variants (rows bound to the same models at these heights, as `tables.py` does for props).
The MM9 trees are taller than MM8's (1656 for the common Tree05 x 1.3).

## Non-props (`non_props.json`)

Chests: TreasureChest 475, 476, 772 (Chest1.ABC; baked as `MM9_chest_*`). Doors: RotatingDoor 498/499 (bunker),
769 (hut), Door 6 (`Terrain3`). Destructible walls: 7 (`FortWall0`), 520 (`FortWall`). World objects 482 (Ocean),
519, 757-759. Effects and helpers: Fire 562/765, Shooter 479/480, HidingPlace 79, ScriptObjects 483, 497, 568-572,
EarthQuake 2, Triggers 5, ExitTriggers 2, StartPoints 3, Lights 21, InvisibleBrush 20, PerceptionBrush 3. No pickup
objects on this map.

## Decoration ids (resolved 2026-10-29)

Appending the rows to the engine table (674-690) would have broken Hesper's stage, which asserts that the engine
table ends at 673. The rows are therefore MM9 world content in the world's own range 2001-2999
(`../../../devdocs/WORLD_DECORATION_CONTRIBUTIONS.md`); the engine merges them after its rows while MM9 is the active
world. `props.json` still carries the older provisional ids (`decoration_list_id`, from `placements.py`); the isle
conversion resolves every prop by name from the merged table, so the map stores 2000-2016.

## Deviations and compromises

- Textures are the native 128-256 px skins x4 (512-1024), no normal or roughness maps (roughness 0.85, metallic
  0); one texel density per prop as authored. Shipwreck and longship share the VikingShip skin (each GLB embeds it).
- The book is 252 triangles without LODs (one small placement); the cot, stool, dresser, table, podium, logs, skull
  and debris (20-160 triangles) have no LODs.
- The statstone's sphere rotation and the wreck's rocking are not reproduced as motion (no part rotation in the
  static path); the orb scrolls its texture and pulses instead.
- Collision (rows): MM9 Solid props get radius = half the smaller footprint side and the model height; the others
  0 (walk through), as MM9's Solid 0.


## Bone-display ball removed (2026-10-31)

Blender 5's glTF importer adds an `Icosphere` bone-display mesh (42 vertices, 80 triangles, 2.4 cm) to every skinned
(`full`) import, and the isle's `blib.import_raw` took every imported mesh, so the ball stayed in the decoration (Tasar
Academy found it). Removed from `book` 252        -> 172 triangles (LOD0 / LOD1 / LOD2). `scripts/blib.py` now has an
opt-in flag `SKIP_BONE_SHAPES` (passed to the importer as `disable_bone_shape`); this project's `build.py` sets it. The
ball sat just past the book's spine and had moved its base centre 1.585 units along x; the build keeps that frame
(`frame_x`, `blib.BOOK_BALL_FRAME_X_M`) so the book placements of every map stay valid (geometry otherwise identical).
Rebuilt, checked (`finish.py`, check_winding.py: 0 inverted closed parts) and reinstalled with `install_model.py
--engine`; the replaced GLBs and scripts are in `work/backup_propfix_20261031/`. No MM9 bake depends on decoration
models (stale_bakes.py lists none).


## Scrambled normals repaired (2026-11-06)

Every MM9 decoration built on `blib.import_raw` (all 32 props projects) shipped unrelated per-corner normals: the glTF
importer's custom normals rode through the bmesh round trip as a plain `custom_normal` corner attribute, encoded
against corner spaces that the X mirror, the face reversal, `clean()`'s weld and the triangulation then changed, and
they overrode `smooth()` on export. Each triangle of a flat panel shaded differently: a hard light/dark diagonal across
cabinet doors, bookcases and beds in game (Klusos House's star cabinet, `cabinet05`), on both indoor lighting paths.
Measured with the seam metric below: 480 of 569 installed `mm9_deco_*` models had seams over 2 % of their area, the
MM6-MM8 decorations none.

- `blib.import_raw` now removes the attribute after `to_mesh` (the authored normals still decide the winding), so
  `smooth()` gives normals from the geometry, smooth within 40 degrees.
- `scripts/renormal.py` rebuilt the normals of the installed models in place, without a rebuild (their x4 skins were
  swapped in afterwards): per mesh, corners round a welded position share the corner-angle weighted normal of the faces
  joined by smooth edges (two faces, consistent winding, within 40 degrees), Blender's rule; vertices split where
  needed, every other attribute, image and extra byte-exact. Checked against Blender's own smooth-by-angle on three
  models (0.00 degrees difference on every corner). `renormal.py check <glb>...` prints the seam share (area on an
  edge between near-coplanar faces whose normals differ by over 20 degrees) before and after; `install` writes
  `work/renormal/` and runs `tools/install_model.py --world mm9`.
