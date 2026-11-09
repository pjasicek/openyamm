# MM8 Crystal Walker — m596

> **Installed model replaced (2026-10-19):** the installed Crystal Walker is now the v2 rebuild from [`../mm8_m596_v2_claude/`](../mm8_m596_v2_claude/README.md) (Meshy Smart Topology body with an authored gem-cut head, 5,590 triangles at LOD0, skinned, new clips). This rigid-part model is superseded; its source is kept as the rollback `../mm8_m596_v2_claude/work/mm8_m596_source_pre_v2.glb`.

Completed 2026-10-18: native-derived rigid crystal creature, installed for Crystal Walker, Crystal Sentry and
Crystal Guardian (monster IDs 148–150). Technical and agent visual review are complete. User artistic acceptance
has not been recorded.

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm8_m596_claude/review/viewer/) ·
[Editable Blender master](work/crystal_walker.blend) · [Portable GLB](export/mm8_m596.glb) ·
[Canonical progress and hashes](creature_3d_progress.json)

![Native sprites and installed models, same cameras](review/ingame/comparison.jpg)

## Construction and source decisions

The original `mm8_m596` palette-596 frames establish the pink/mauve mineral, broad shoulders, narrow waist,
flattened wedge head, backward crystal crown, long arms, three hooked claws per hand and broad prism feet.
The [source inventory](sources/native_summary.json) and action contact sheets preserve that evidence.
Five [HD views](references_hd/selected_views_review.png) support appearance decisions; original sprite proportions
override the generated views' slightly elongated head. Prompts, hashes and selected/rejected results are in
[generation_runs.json](references_hd/generation_runs.json).

This uses Reactor's locally authored rigid-part route. The body is made of closed crystal sections with overlaps
at joints. Every vertex has exactly one weight of 1.0; every triangle belongs to one bone. There are no stretch
tracks or blended crystal surfaces. Crown and claws are integral rigid pieces. No equipment is missing, and no
Meshy jobs or credits were used. Human mocap was considered but is unsuitable for this mechanical native gait.

| Property | Delivered value |
| --- | --- |
| Rig | 18 bones; Root, hips/waist/chest, neck/head, paired arms/hands and legs/feet |
| Colour LODs | 1,216 / 916 / 664 triangles, authored as closed sections |
| Shadow LODs | Merged chains matching each authored level |
| Material | One opaque nonmetallic crystal material; roughness 0.32, specular 0.6 |
| Texture | 2048² authored mineral swatches; 350 texels/metre; face seams follow hard edges |
| Material classes | 1024² class-11 crystal map, retained as authoring evidence |
| Native scale | 191-pixel upright silhouette / 1.877637-metre model = 101.723614 world units/metre |
| Tier factors | 1 / 1.299988 / 1.599991; all share native palette 596 |

LODs preserve the crown, curved claws and closed joints. At this small base budget, approximately 25–28% reduction
per level preserves those structures better than halving every level. There is no unnecessary tier recolouring,
separate head material, normal-map detail or transparent refraction layer.

## Motion and runtime binding

| Clip | Seconds | Intent |
| --- | ---: | --- |
| Standing | 1.5 | Restrained rigid idle |
| Walking | 1.0 | Native eight-frame gait intent; planted soles, 0.90-metre stride |
| Running | 0.75 | Faster rigid gait; 1.30-metre stride |
| Attack | 1.5 | Raised right claw, downward sweep, recovery |
| Cast | 1.5 | Paired raised hands; optional existing cast role |
| Hit | 0.791667 | Recoil shorter than the native 0.8125-second action |
| Fidget | 0.625 | Head and wrist motion |
| Death | 1.0 | Intact backward fall, spread hands touching the floor |
| Dead | 1.0 | Held final corpse pose |

The attack/release event is at **0.833333 seconds**, during the forward claw sweep; gameplay timing is unchanged.
Animation keys are at 24 fps with linear, quaternion-continuous interpolation. Leg IK is baked into ordinary bones;
the runtime needs no IK solver. Palm sockets use the hand bones, upper-body overlay starts at Waist, and head look
uses Neck/Head with 25° yaw and 15° pitch limits. Native binding names are `Crystal Walker A/B/C`.

The three bindings use explicit measured scales. A first attempt with `scale_reference` required native foreign
sprite frames to be loaded on MM6 test maps; explicit scales remove that dependency while retaining native sizes.
The [installed binding snapshot](review/installed_bindings.json) contains only this family.

Installed paths:

- Source: `assets_source/worlds/mm8/models/mm8_m596.glb` — identical to the portable export.
- Cooked runtime: `assets_dev/worlds/mm8/models/mm8_m596.glb`, with cooker-managed texture data.
- Bindings: `assets_dev/worlds/mm8/models/actors.yml`; other families and original sprites are preserved.

## Validation and visual evidence

- Ordinary `openyamm` build succeeded. The focused MM8 actor regression passes: three native-sized tiers, one
  shared model, required clips, rigid influences in all LODs and unchanged actor identity/HP/position/timing.
  [Regression log](review/actor_regression.log).
- Delivered GLB reimport matches the animated Blender master to less than one micron. All nine clips pass
  half-frame rigidity, hand/torso intersection, floor and loop checks. [Export audit](work/export_audit.json).
  All six colour/shadow meshes pass one-bone-per-facet checks. [LOD audit](work/all_lod_rigidity.json).
  The existing closed-part winding check reports zero inverted components.
- Existing viewer check passed all **27 tier/clip combinations**, with zero console errors. Actual browser
  playback at 1× and 0.5× is preserved as 18 WebMs plus timestamped samples in
  [playback.json](review/playback/playback.json). The [slow attack filmstrip](review/playback/attack-video-half-speed.jpg)
  includes the intermediate sweep poses.
- Five successful isolated native runs used **OpenGL 3.3 on NVIDIA, Wayland**. All three tiers were inspected
  against sprites at the same cameras in New Sorpigal (`oute3.odm`) and the Temple of Baa (`6d19.blv`), including
  forced LOD2. Debug-model action poses cover all clips; an ordinary hostile actor approaches, attacks, takes the
  damage command, dies backward and enters the existing loot-satchel transition.
  [Run records](review/ingame/runs.json), [action overview](review/ingame/action-overview.jpg).

The isolated hardlink fixture adds native sprite preload declarations to copied maps, for foreign-monster sprite
comparison. It does not modify production maps. Captures use live actors, so their exact poses and wandering
positions can differ despite identical cameras and initial spawn positions. The first cropped/scale-reference
attempts remain under `review/ingame/out_models_initial` and `out_models_close`; the selected comparisons are
`out_models`, `out_sprites`, `in_models` and `in_sprites`.

Measured interpolation floor undershoot is below 2 mm in locomotion and 6.3 mm during the fall. These are below
the 15 mm export gate and were visually checked. This is a visual correctness review, not a performance benchmark.
Vulkan and Android were not tested. Artistic acceptance remains separate from the completed technical delivery.

## Reproduce or revise

Claim `mm8:m596` at this top-level project with `tools/creature_workspace.py` before writing. Retain the returned
token as `CREATURE_3D_TOKEN`. Use the existing ownership guard for ordinary writes and the Blender wrapper directly
for Blender operations; do not nest those wrappers.

The production sequence is:

1. `scripts/make_texture.py` under the workspace guard. Its deterministic recipe matches the delivered pixels.
2. `tools/run_creature_blender.sh --token "$CREATURE_3D_TOKEN" level_generation/creatures/mm8_m596_claude/scripts/build.py`
3. Under the guard, run `python3 tools/prepare_actor_glb.py` with `export/mm8_m596_lod0.glb` as input and
   `export/mm8_m596_runtime_lod0.glb` as output (both relative to this project).
4. Run `scripts/author_lods.py`, then `scripts/audit.py`, through the Blender wrapper. The latter checks the actual
   assembled export against the retained `.blend`.
5. Under the guard, run `python3 tools/install_model.py level_generation/creatures/mm8_m596_claude/export/mm8_m596.glb --world mm8`,
   then `scripts/deliver.py` from repository root to update the three bindings and existing viewer.
6. Run the focused regression from repository root:

   ```sh
   OPENYAMM_REGRESSION_FILTER=mm8_crystal_walker ./build/game/openyamm --world mm8 --headless-run-regression-suite actors
   ```

7. Run `claude_shared/check_viewer.mjs` against the URL above. `scripts/viewer_playback.mjs` accepts that URL and an
   output directory. Review normal/slow motion after any geometry or animation change.
8. `scripts/prepare_reviews.py` creates an isolated fixture and tier comparison tours. Existing complete launch
   arguments are in each selected `review/ingame/*/run.json`; `actions.yml` preserves the action/combat tour.
   Re-run the affected native checks after a visual or binding change, update the canonical record, then release
   the creature lease.

No commits or staging operations were performed.

Material (2026-10-19): the installed model now has the gem-crystal material from [`../mm8_crystal_material_claude/`](../mm8_crystal_material_claude/README.md) (gloss and per-facet colour; rollback there).
