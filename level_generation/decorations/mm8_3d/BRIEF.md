# Builder brief: MM8 decorations in 3D (2026-10-15)

The common brief for every builder of this project. Plan and status: `README.md` (this folder). The MM6 projects are
the reference: `../mm6_new_sorpigal_3d/` (outdoor: trees, desert palms, flowers, succulents, rocks, props) and
`../mm6_dungeons_3d/` (dungeons: torches, fire, containers, crystals, hanging). Their `BRIEF.md` and READMEs hold
the lessons; read the README of the pipeline you reuse before starting. Engine and model contract:
`engine/render/MODEL_RENDERING.md`, `engine/models/ModelAsset.h` (material extras), and
`level_generation/GAME_ASSET_MODELLING_GUIDELINES.md` (every mesh).

## Goal

Static 3D replacements (glTF) for MM8 decoration sprites, matching the native sprite in silhouette, proportions and
colour, drawn by the engine's static instanced model path. Authentic to the original look and feel, but pretty:
real PBR surfaces, good shading, and for natively animated sprites a convincing animation from the existing cheap
material extras (no expensive effects).

## Inputs

- `inventory.json` (this folder, from `scripts/inventory.py`): every decoration placed in the MM8 maps, with its
  placements per map, frames and loop (`anim`, 1/16 s units), frame textures, restored x2 files (`files`, in
  `assets_dev/engine/decorations_x2/`), the native image's opaque size (`opaque_size`, pixels), DSFT `scale`, and
  `height` = the binding height in map units (opaque pixel height x scale). `width` likewise. Native bitmaps:
  `assets_dev/_legacy/sprites_original/<texture>.bmp` (case-insensitive; palette index 0 is transparent).
- `units()` in `../mm6_dungeons_3d/scripts/dungeon_lib.py`: 81.7 map units per metre. The engine scales a model so
  its bounds height is the binding height, so proportions matter, not absolute size.
- MM8 trees are large: about 1,000 map units (12 m) for most species.

## Conventions

- Model: Blender Z up (glTF export makes it Y up), base centre on the ground at the origin, one mesh node with LODs
  linked by `tools/link_static_model_lods.py`, COLOR_0 on every primitive (vertex occlusion times a per-material
  tint). Foliage: the MM6 tree/desert contracts (alpha-tested cards cut to their texels with
  `tools/cut_foliage_cards.py`, `openyamm_wind`, `openyamm_translucency`, low `openyamm_specular`, camera-facing
  impostor at the last LOD).
- Colour: match the native sprite's measured mean colour per part (tint through COLOR_0). Outdoor models are lit by
  the sun and the baked lighting; compare in review renders under neutral light.
- Animation: a natively animated sprite (`frames` > 1) needs one of `openyamm_flipbook` (fire: the shared Unity Labs
  flame flipbooks, `../mm6_dungeons_3d/textures/FLAMES.md`), `openyamm_uv_scroll`, `openyamm_flutter`,
  `openyamm_wind`, `openyamm_pulse` or a `swing` binding, or the binding says `still: true` with a reason.
- Lights (2026-10-16 engine extras, `engine/models/ModelAsset.h`): `openyamm_billboard: "card"` turns each primitive
  about its own centre toward the camera (off-axis flame cards; one primitive per card), `openyamm_additive: true` on
  a BLEND material adds its glow and fades with fog (halos), `openyamm_flicker: [amplitude, changes per second]` is a
  random flicker instead of the sine pulse (fire).
- Fixtures: wall mounts as in the MM6 brief (back toward Blender +y, `_free` variant); hanging fixtures pivot at the
  bounds top (`swing`).
- Budgets: as low as the silhouette allows (`GAME_ASSET_MODELLING_GUIDELINES.md`): hundreds of placements
  300-1500 LOD0 triangles (trees up to about 6,000; the MM6 trees used 6-8k, aim lower where the crown allows);
  tens 1500-4000; one-offs up to 6000. Three or four LODs. A later reduction pass may trim further, but do not
  spend triangles the silhouette does not need.

## Sources and licences

Only CC0 or CC-BY (with attribution recorded) or our own procedural work may be installed. Poly Haven
(`https://api.polyhaven.com/files/<asset>`), ambientCG and the MM6 projects' textures and generators (import or
copy them into your folder; never edit the MM6 projects). The OpenMW free asset library
(`https://github.com/Kon-tiki-ship/openmw-free-asset-library`) may be used only for entries whose catalogue licence is
CC0 or CC-BY, never "Generic / Commonplace" or unspecified ones, and only when a model is a near-perfect fit. No
paid generation unless your batch says so. Record every source and licence in your README.

## Rules

- Work only in your own folder `level_generation/decorations/mm8_3d/<batch>/` (scripts, textures, work, review,
  README.md). Import or copy helpers from the MM6 projects; do not edit files outside your folder.
- Install with `python3 tools/install_model.py <your export.glb> --engine --name mm8_deco_<name>.glb` (MM8-only art)
  or `--name mm7_deco_<name>.glb` (art shared with MM7, where your batch says so). It writes the source to
  `assets_source/engine/models/` and cooks the runtime copy into `assets_dev/engine/models/`. Never copy into
  `assets_dev` or `assets_source` directly, never install over an `mm6_deco_*` model or another batch's model, and
  never call `tools/cook_models.py` yourself. Do not start an Android cook.
- Do not edit the decoration manifests (since 2026-10-16 `assets_dev/engine/models/decorations.yml`,
  `indoor_decorations.yml`, `decoration_overlays.yml`), do not bake, do not build the engine, do not run the
  game (the coordinator does in-game checks), no Vulkan builds, no git commands that change state. Other sessions
  work in this repository.
- Run Blender headless (`blender --background`); keep at most two Blender processes of your own at a time.
- Review every model against its sprite: a sheet with the native x2 sprite next to LOD0 front, three-quarter and side
  renders, and the LODs, saved in your folder's `review/`. Iterate until silhouette, proportions and colour read
  like the sprite. Look at the sheets yourself (Read the PNG) before reporting.
- Face orientation: the engine culls back faces of single-sided materials; Blender's review renders draw them, so an
  inside-out surface only shows in game. Before every install run `python3 animated/scripts/check_winding.py <glb>`
  (0 inverted closed parts), and render reviews with backface culling, including a view from below for open shells.

## Report

Per model: the installed GLB path, LOD triangles, file size, the suggested binding (YAML: name, model, height,
height_jitter, z_offset, yaw, mount, free_model, swing, still, lod_pixels), the review sheet path, and compromises.
Keep your README.md current with the same information.
