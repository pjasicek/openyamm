# Builder brief: MM7 decorations in 3D (2026-10-15)

The common brief for every builder of this project. Plan and status: `README.md` (this folder). MM6 precedent:
`../MM6_3D_DECORATIONS_IMPLEMENTATION_PLAN.md`, `../mm6_dungeons_3d/BRIEF.md` (read it: its conventions and its
"Revision 2" rules apply here too). Engine and model contract: `engine/render/MODEL_RENDERING.md`,
`engine/models/ModelAsset.h` (material extras). Mesh rules: `level_generation/GAME_ASSET_MODELLING_GUIDELINES.md`.

## Goal

Static 3D replacements (glTF) for MM7 decoration sprites, matching the native sprite in silhouette, proportions and
colour, drawn by the engine's static instanced model path. Decoration models of every world are engine content, so
they can be bound by any world: MM7, MM8 and future worlds.

## Inputs

- `inventory.json` (this folder; regenerate with `scripts/inventory.py`): every decoration placed in the MM7 maps with
  - `count`, `outdoor`, `indoor` and `maps`;
  - `frames`, `loop` (1/16 s units) and `textures` (one per frame);
  - the restored x2 first frame `x2`, in `assets_dev/engine/decorations_x2/`. The other frames are in that folder's
    `manifest.json`, by texture name;
  - `logical` size and DSFT `scale`;
  - `height` (the sprite frame in world units), `art_height` (its opaque art) and `art_bottom` (empty frame below
    the art; hanging cages have some).
  The native bitmaps are `assets_dev/_legacy/sprites_original/<texture>.bmp` (palette colours, key-colour
  background).
- **Model height.** The engine scales a model so that its bounds height equals the binding height. Suggest
  `art_height` as the binding height unless the model's bounds differ from the art. A flame card that rises above
  the art counts in the bounds.
- Units: Blender metres, 81.7 map units per metre (`../mm6_dungeons_3d/scripts/dungeon_lib.py` `units()`).

## Reuse the MM6 pipelines

Read the README of the matching MM6 pipeline before building, and reuse its scripts. Import them, or copy them into
your folder and adapt them. Do not edit files in MM6 folders.

| Content | MM6 pipeline |
|---|---|
| Rocks | `../mm6_new_sorpigal_3d/rocks/` (`rocks.json`, `build.sh`); `../mm6_new_sorpigal_3d/README.md` "Build" (Poly Haven scans: decimate, dome unwrap, bake, LODs, grading to the sprite) |
| Trees | `../mm6_new_sorpigal_3d/trees/` (`README.md`, species configs in `species/`, `build.sh`: Sapling, leaf atlases, clump cards, impostor LOD3; `DEAD_TREES.md`: branch generator for bare trees; `add_fruit.py` for fruit pairs) |
| Flowers | `../mm6_new_sorpigal_3d/flowers/` |
| Cacti and succulents | `../mm6_new_sorpigal_3d/succulents/`; desert palms and agaves: `../mm6_new_sorpigal_3d/desert/` |
| Props and fire | `../mm6_new_sorpigal_3d/props/` (`props_lib`, `flame_material()`), `../mm6_dungeons_3d/fire/`, `../mm6_dungeons_3d/torches/` |
| Dungeon dressing | `../mm6_dungeons_3d/containers/`, `bones/`, `hanging/` (swinging cages), `crystals/` (pulse), `leftovers/` |
| Flames | `../mm6_dungeons_3d/textures/FLAMES.md` (card recipe). Coloured flame atlases (red, purple, green, blue, white besides the orange `flame02`): `../shared_flames/` |

## Conventions (as in MM6)

- **Model layout.** Blender Z is up (the glTF export makes it Y up).
  - The base centre sits on the ground at the origin.
  - One mesh node, with LODs linked by `tools/link_static_model_lods.py`.
  - COLOR_0 on every primitive.
- **Animation.** A natively animated sprite (`frames` > 1) needs a model animation: `openyamm_flipbook`
  (flames), `openyamm_uv_scroll`, `openyamm_flutter`, `openyamm_wind`, `openyamm_pulse` (glows), or a binding
  `swing`. Otherwise the binding says `still: true`; state the reason in your report.
- **Fixtures.**
  - Wall fixtures: the back toward Blender +y, with a `_free` variant (`mount: wall`, `free_model`).
  - Hanging fixtures: the bounds top is the swing pivot.
  - Flames: camera-facing cards on the flame axis.
- **Colour.**
  - Outdoor models are lit by the sun and the baked light. Grade their albedo to the sprite's measured colour under
    review lighting (see the rock grading in `../mm6_new_sorpigal_3d/README.md`).
  - Dungeon models are lit like the sprite they replace. Tint them through COLOR_0 to the sprite's measured mean
    colour, and do not brighten dark dungeon sprites.
- **Surfaces.** Use real PBR sets (Poly Haven CC0: `https://api.polyhaven.com/files/<asset>`), your own procedural
  textures, or the textures of the MM6 projects. Flat colours on slabs were rejected in MM6.
  `level_generation/creatures/NATIVE_SHADING_TRANSFER.md` helps where a model reads flat next to its sprite.
- **Licences.** Use only CC0, CC-BY or our own work, and record every source and licence in your README. No paid
  packs. No Meshy, Codex or other paid generation jobs; ask the orchestrator if you think one is needed.

## Triangle budgets

The user asked us to be mindful of triangle counts. Spend triangles on the silhouette, avoid micro and sliver
triangles, and keep LOD steps fitted to how they look on screen, not to fixed ratios. A later reduction pass
(`../mm6_reduce_pilot/`) may trim further.

| Content | LOD0 ceiling | LOD chain |
|---|---|---|
| Trees, 100+ placements | 6000, alpha leaf cards included (MM6 trees: 7–8k) | down to an impostor (LOD3), `lod_pixels` as MM6 trees |
| Trees, fewer placements | 7000 | as above |
| Rocks | 1500 | 3–4 levels down to about 100 |
| Flowers, ferns and plants | 1500 | 3 levels down to 100–300 |
| Props with 50+ placements | 300–1500 | 3–4 levels down to 100–300 |
| Props with fewer placements | 1500–4000 | as above |
| One-off props | up to 6000 | as above |

## Rules

- Work only in your own folder `level_generation/decorations/mm7_3d/<batch>/` (scripts, textures, work, review,
  README.md). Read anything; edit nothing outside your folder.
- Install only through `tools/install_model.py <export.glb> --engine --name mm7_deco_<name>.glb`.
  - Use only names that do not exist yet in `assets_source/engine/models/`; you may reinstall your own.
  - Never touch the `mm6_deco_*` or `mm8_deco_*` models. Another session builds the MM8 decorations and the shared
    cauldron, trash heap, glass and fruit bowl.
  - The tool cooks the runtime copy and serialises installs between sessions.
  - Before every install, run `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py <glb>` until it
    reports `inverted closed parts: 0`. The engine culls the back faces of single-sided materials, but Blender review
    renders do not, so an inside-out part only shows in game.
- Do not edit the binding manifests (`engine/models/decorations.yml`, `indoor_decorations.yml`,
  `decoration_overlays.yml`); the orchestrator binds.
- Do not bake, build the engine, run the game, run Vulkan builds or make git commits. Run Blender headless
  (`blender --background`), never the live Blender over MCP.
- **Review.** Make a sheet with the native sprite or x2 frame next to LOD0 front, three-quarter and side renders and
  the LODs, saved in your `review/`. Iterate until silhouette, proportions and colour read like the sprite.
  Once a model is bound, the gallery also shows it next to its sprite. Build it with
  `python3 level_generation/decorations/review/build_gallery.py --world mm7`, then open
  `http://127.0.0.1:8901/level_generation/decorations/review/viewer/?world=mm7` (screenshots with `shoot_gallery.mjs`;
  see `../mm6_dungeons_3d/BRIEF.md`, Revision 2).
- **Documentation.** Document your models in your README.md: sources and licences, triangles per LOD, compromises
  and rebuild commands.

## Report

Your final message is the report. Per model, give:
- the installed GLB (`engine/models/mm7_deco_<name>.glb`) and the decoration names it serves;
- LOD triangles and file size;
- the suggested binding YAML (`name`, `model`, `height`, `height_jitter`, `yaw`, `lod_pixels`, `mount`,
  `free_model`, `swing`, `still`, `z_offset`) and whether it is outdoor or indoor;
- the review sheet path;
- compromises.
