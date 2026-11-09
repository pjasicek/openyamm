# Builder brief: MM6 dungeon decorations in 3D (2026-10-09)

The common brief for every builder of this project. Plan: `../MM6_3D_DECORATIONS_IMPLEMENTATION_PLAN.md` (Part C).
Engine and model contract: `engine/render/MODEL_RENDERING.md`, `engine/models/ModelAsset.h` (material extras).

## Goal

Static 3D replacements (glTF) for MM6 dungeon (BLV) decoration sprites, matching the native sprite in silhouette,
proportions and colour, drawn by the engine's static instanced model path with the sprite's own light.

## Inputs

- `inventory.json` (this folder): every decoration placed in the 51 MM6 dungeons with its count, native frame count
  and loop (`anim`, 1/16 s units), first frame texture (`tex`), restored x2 file (`file`, in
  `assets_dev/engine/decorations_x2/`), logical size (`logical`) and DSFT frame scale (`scale`).
  World height in map units = logical height x scale (round it). Frames of an animated sprite: its `sprite` entry in
  `assets_dev/engine/rendering/sprite_frame_data_common.yml` (texture names; x2 files are `<texture>_p<palette>.png`).
- Reference: the pilot `scripts/build_torch.py` (wall torch: lit, unlit and
  free-standing variants), `scripts/make_flames.py` (native flame flipbook atlas), `scripts/finish.py`.
- Helpers: `scripts/dungeon_lib.py` (outdoor `props_lib` with this project's textures first; `units()` converts map
  units to Blender metres, 81.7 units per metre). Outdoor props textures (read only):
  `../mm6_new_sorpigal_3d/props/textures/` (wood, iron, logs, stone, bone, skull, embers, steel, bronze, gold, marble,
  cloth, leather, kegwood, hoop, pewter, campstone, basalt, granite, ...). Their generator is
  `../mm6_new_sorpigal_3d/props/scripts/make_textures.py` (do not edit it; write your own generator in your folder).

## Conventions

- Model: Blender Z up (glTF export makes it Y up), base centre on the ground at the origin, one mesh node with LODs
  linked by `tools/link_static_model_lods.py` (`scripts/finish.py` does it), COLOR_0 on every primitive (vertex
  occlusion times a per-material tint). The engine scales the model so its bounds height is the binding height, so
  model proportions matter, not absolute size; build in metres with `units()` from the native sprite measurements.
- Colour: indoor models are lit exactly like the sprite they replace (a self-lit flame sprite at one). Tint each
  material through COLOR_0 so its displayed colour matches the native sprite's measured mean colour (see
  `TINTS` in `build_torch.py`: linear multiplier = linear(native sRGB) / linear(texture mean)). Native dungeon
  sprites are painted dark; do not brighten them.
- Flames: a camera-facing card (`openyamm_billboard: true`) in the model's x/up plane (Blender xz plane at y = 0),
  texture coordinates 0..1 over one frame; `openyamm_flipbook: [columns, rows, fps]` over an atlas of the native
  flame frames cut out above the fixture (copy `make_flames.py`'s approach into your folder; fps from the native
  loop). Material Flame: BLEND, double-sided, unlit (finish table `FLAME`). The card turns about the vertical axis
  through the model origin and keeps only its offset across the model, so put the flame axis at x = y = 0.
- Wall fixtures (torches, sconces): `mount: wall`. The fixture's back (wall plate) toward Blender +y (glTF -z), the
  flame axis at the origin; also build a `_free` variant without the wall plate/arm for placements with no wall in
  reach (`free_model`).
- Hanging fixtures (cages, chandelier): the bounds top is the swing pivot (the ceiling chain end); `swing` swings
  the model about the asset x axis through it.
- Glow: `openyamm_pulse: [amplitude, period seconds]` scales a material's emission (finish `emissive`), out of step
  per placement. Water: `openyamm_uv_scroll`. Cloth: `openyamm_flutter`.
- A natively animated sprite (frames > 1 in `inventory.json`) needs one of these animations, or the binding says
  `still: true` (state why in your report). The regression `decoration_models_keep_native_animation` checks it.
- Budgets by placement count: hundreds of placements 300-1500 LOD0 triangles; tens 1500-4000; one-offs up to 6000;
  LOD chain of three or four levels down to 100-300.

## Rules

- Work only in your own folder `level_generation/decorations/mm6_dungeons_3d/<batch>/` (scripts, textures, work,
  review, README.md). You may import `../scripts/dungeon_lib.py`; do not edit files outside your folder.
- Install new models only as `assets_dev/worlds/mm6/models/mm6_deco_<name>.glb` (0664), names that do not exist yet.
  Never modify an existing installed GLB (outdoor bakes depend on their bytes).
- Do not edit `decorations.yml` or `indoor_decorations.yml`, do not bake, do not build the engine, do not run the
  game, no Vulkan builds, no git commits. Other sessions work in this repository.
- Review every model against its sprite: a sheet with the native sprite next to LOD0 front, three-quarter and side
  renders (Blender, flame cards excepted) and the LODs, saved in your folder's `review/`. Iterate until silhouette,
  proportions and colour read like the sprite.
- Document your models in your folder's README.md (sources and licences, budgets, compromises).

## Report

Per model: the installed GLB path, LOD triangles, file size, the suggested binding (YAML: name, model, height,
mount, free_model, swing, still, z_offset, yaw), the review sheet path, and compromises.

## Revision 2 (user review in the gallery, 2026-10-09)

The user reviewed the models next to their sprites in the gallery
(`http://127.0.0.1:8901/level_generation/decorations/review/viewer/`). Rules for every revision:

- **Real surfaces, not flat colours.** Procedural tileable noise read as "solid colours on slabs", with no
  roughness. Use real PBR texture sets: CC0 Poly Haven textures (`https://api.polyhaven.com/files/<asset>` lists the
  maps, downloadable without an account) for wood, bark, iron, rusty metal, stone, burlap and fabric, charcoal or
  embers, lava rock. Use base colour, normal and roughness (packed as glTF metallic-roughness: G roughness, B metal).
  Or use Meshy texturing where the brief says so. Record every source and licence in the README.
- **Native shading where it helps.** `level_generation/creatures/NATIVE_SHADING_TRANSFER.md` and
  `claude_shared/native_shading.py` move a sprite's painted light (bright tops, dark undersides, saturated palette)
  onto a texture. Use them where the model reads flat next to its sprite.
- **Authentic shapes.** Skulls and skeletons must read like the sprite's: proper skull anatomy, rib cages, limbs.
  Ask the user before stylising.
- **Meshy route** (when the brief says so): HD masters by Codex first, following
  `level_generation/creatures/CLAUDE_HD_MASTER_REFERENCES.md` (never send Meshy a sprite or x2 frame). Then Smart
  Topology and a Meshy retexture via `tools/run_creature_meshy.sh` / `tools/creature_meshy.py` with a project state
  file and a credit budget. Static props need no rig.
- **Re-baking is not blocking.** An outdoor model may now be reinstalled: stale outdoor bakes still load and are
  noted (`tools/lighting/stale_bakes.py`). Rebuild only your own models and report which maps need a re-bake.
- **Check in the gallery.** After installing, run `python3 level_generation/decorations/review/build_gallery.py`, then
  `node level_generation/decorations/review/shoot_gallery.mjs http://127.0.0.1:8901/level_generation/decorations/review/viewer/
  <out> <item ids> side` (item ids look like `outdoor:ckfyr00` or `dungeon:bag01`; see `viewer/manifest.json`).
  Compare the screenshots with the sprite next to the model, and iterate before reporting. Keep your before and after
  screenshots in your folder's `review/`.
