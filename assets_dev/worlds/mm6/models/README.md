# MM6 demon 3D trial

The [material touch-up](../../../../level_generation/creatures/mm6_demon_meshy_reference_20261004/materials_20261006/README.md)
is the selected master/export. It strengthens the existing A/B/C pigments and separates rough skin, matte
leather and smoother bone/claws. The heavier brow and taller mouth from the
[expression revision](../../../../level_generation/creatures/mm6_demon_meshy_reference_20261004/expression_20261006/README.md)
are retained. The original [variant revision](../../../../level_generation/creatures/mm6_demon_meshy_reference_20261004/variants_20261006/README.md)
records the Meshy sources and verified UV correspondence. No new Meshy generation was needed.
`actors.yml` binds Demon A/B/C to the same GLB with `skin: demon_a/demon_b/demon_c`.
Their native Devil Spawn/Worker/Warrior table IDs and stats remain distinct. Separate irises
select salmon/red/amber colors and keep black pupils; eye particles use the corresponding `eye_color`.
All clips and color/shadow LOD geometry are retained. Since the
[region migration](../../../../level_generation/creatures/mm6_demon_meshy_reference_20261004/regions_20261008/README.md)
(2026-10-08) all three skins share A's body textures plus a skin/harness region mask and per-tier colour ramps,
so the former B/C textures (about 64 MiB of RGBA8 GPU memory) are gone. The editable master is `materials_20261006/mm6_demon_materials_master.blend`.

A's reviewed model scale is the size reference. B/C declare `scale_reference: Demon A`, so the shared loader
uses the standing sprite-frame table ratios (0.75 / 0.699997 and 0.799988 / 0.699997) once during binding setup.
B is approximately 7% larger than A and C approximately 14% larger. Model/shadow/socket transforms and attached
FX sizes use the resulting scale; runtime height changes and Shrink still compose with it. Gameplay collision
dimensions remain the native table values. The crowd diagnostic keeps its deliberately uniform demon size.

The [animation/socket continuation](../../../../level_generation/creatures/mm6_demon_meshy_reference_20261004/animation_controller_20261006/README.md)
adds smooth turning, 120 ms pose transitions, distance-driven walk/run gait, conditional upper-body action layering,
a two-handed Fire Bolt cast and named eye/palm sockets with bounded shared FX. The selected editable master and
portable export's animation source lives in the [higher attack windup revision](../../../../level_generation/creatures/mm6_demon_meshy_reference_20261004/attack_windup_20261006/README.md).
It raises the active hand above the head before the strike. The other clips and all colour/shadow LOD geometry are retained.

The renderer follow-up is documented in the [shared 3D creature rendering plan](../../../../devdocs/CREATURE_3D_RENDERING_PLAN.md).
The current model rendering architecture (asset contract, head merge, held-item attachments, instanced creatures,
variants such as the boss mage) is described in [3D model rendering](../../../../engine/render/MODEL_RENDERING.md).
Material lighting, animated sunlight mesh shadows, and shared sky reflections are implemented and validated on
the native NVIDIA/OpenGL desktop. The plan links the visual, gameplay, lifecycle and performance evidence.

Run `./tools/run_demon_3d_test.sh` from the repository root. It creates a private New Sorpigal save,
spawns seven hostile demons in the grass south of town: three **Devil Spawn / Demon A** (ID **502**),
two **Devil Worker / Demon B** (ID **503**) and two **Devil Warrior / Demon C** (ID **504**).
An automatic console sequence adds B/C beside the original A group and closes the console;
wait a few seconds for that sequence to finish. The game stays open for review. Add `--seconds 20` for automatic exit.
The isolated party is immortal and sunlight shadows are enabled. Close the window to end the test;
normal saves and settings are untouched. Add `--set video.shadows=false` for a shadow comparison.

The appearance binding is opt-in via the launch-only setting `debug.actor_models=true`.
`actors.yml` matches the existing descriptor and maps the eight native animation states to GLB clips.
Locomotion uses the user-selected Meshy `Walking` and `Running` clips according to movement speed,
with gait driven by travelled distance. Both the demon and crowd bindings use this selection.
Melee and ordinary ranged attacks use `Attack`; actual spell actions use the added `Cast_FireBolt` gesture,
retimed to the native action clock. The optional `animation` binding declares stride, mask root and socket names.
The ordinary fire missile uses a short MM9 sprite trail on the right palm; melee does not emit hand FX.
The two-handed spell charge uses a round radial glow, bright core and rising embers through shared particle
batches indoors and outdoors. Hand fire is half the enlarged review size; spell charge is twice its round review size.
Attack windup follows the current sensed target through shared AI yaw and smooth model facing.

For a whole-map crowd test, run `./tools/run_sorpigal_demon_crowd.sh`. It copies the ordinary desktop settings,
uses 1600×900, replaces the presentation of every MM6 goblin and mage/magician tier in New Sorpigal with
the full-size animated demon, and logs FPS for 30 seconds after ten seconds of warmup. All original actor
positions, table identities, stats and AI remain active. Peasants retain their normal appearance.
Shadows, filtering, asset quality, water and VSync retain their standard settings; add `--seconds 0` for
interactive review, or `--set video.shadows=true` for a separate shadow test.

The test selects `sorpigal_demon_crowd.yml` through the launch-only, package-relative setting
`debug.actor_models_manifest`. Without that override, model bindings use the world's ordinary `actors.yml`.
The test changes private settings/saves only. The launcher's `run.json`, `measurement.log` and `game.log`
contain FPS, GPU frame timings and rendering resource counters; see [desktop runs](../../../../tools/RUN_GAME.md).
The [229-actor stress-test report](../../../../output/performance/sorpigal_demon_crowd_20261005/REPORT.md)
records the initial failure: roughly 7 FPS versus 1,958 with sprites, with CPU pose updates dominating and
transient-buffer exhaustion dropping mesh/HUD draws. The shared renderer now uses eight-influence GPU skinning,
conservative animation bounds before bone evaluation, camera/shadow culling, and reusable morph buffers.
The [fixed crowd report](../../../../output/performance/sorpigal_demon_crowd_fix_20261005/REPORT.md) preserves
the first GPU-path measurements and restored HUD, but its joint-input bug left the meshes in their bind pose.
The [animation correction](../../../../output/demon_animation_fix_20261006/REPORT.md) records live pose review
and fresh same-save measurements: 1,572 FPS with correctly animated demons versus 2,010 FPS with sprites.
The [subsequent performance study](../../../../output/performance/demon_renderer_budget_20261006/REPORT.md)
measures the wide and crowded cameras, compares OpenMW's work-avoidance techniques, and defines targets
before LOD work. Its faster diagnostic builds are separate from the normal game.
The [production CPU fixes](../../../../output/performance/demon_cpu_fix_20261006/REPORT.md) remove the runtime
plume mesh, use a bounded particle burst, and retain exact posed picking without full CPU vertex/normal deformation.

Actors retain their table stats, Demon kind, spells, sound ids, hostility, collision cylinders, AI,
pathfinding, combat impact timing, turn-based behavior and save data. Models are derived presentation
instances, rebuilt from actor state after load and cleared on map changes. Model sampling uses the
actor's 128-Hz animation clock and does not advance its own simulation. Shrink follows the same visual
multiplier as sprites. Mouse picking uses the posed model bounds; health bars and hover outlines retain
the existing actor identity and colors. Actor height overrides scale the model consistently with sprites.
`death_effect: disintegration` emits one burst of at most 80 camera-facing particles on entering Dying.
The existing particle system updates at 30 Hz, culls and batches the burst with other effects, and caps the
whole world at 4,096 particles. The burst adds at most two shared material batches, with no PBR, morphs,
picking or shadow submissions. It expires within the death clip and resumes at the actor's death clock after load.
The portable authoring GLB retains its standalone plume, hidden outside Death. `NoCorpse` still hides
the demon when the native death timer ends, so no permanent lootable ash is added.

Clip changes blend with an eased (smoothstep) weight over 0.12 s (0.06 s into a hit, none into death). A model whose
clips change pose a lot sets `animation.blend_seconds` (every change except into dying) and
`animation.death_blend_seconds` (into the death clip): the Flying Drake uses 0.4 s and 0.3 s between its forward flight
and upright hover, which move its head about half its height.

`death_effect: {type: burn, ...}` (the Flying Drake and the red/blue/gold dragons) burns the body away along per-material burn maps
(`engine/render/MODEL_RENDERING.md`, "Burning creatures"). Times are seconds from the start of dying: `start` is when
the first texels begin to char and `end` when the last have burnt through; `char_width`, `edge_width` and `fire_width`
are in burn-map units (the fire lingers that much longer as a silhouette of flame). `color` is linear RGB times
`brightness`; `flames_per_second` and `flame_size` (world units at the reference scale) set the flames rising from the
burning band (`FxRecipes::spawnActorBurnFlame`), and `light` a fire light that swells and dies with the burn. The death
clip plays to its end even after the native death length. The burnt-out corpse draws nothing and cannot be picked;
its loot satchel, if any, appears as the body comes to rest. Every skinned material needs an uncooked burn map, or the
binding is rejected.

The shared binding path works indoors and outdoors. Worlds without `models/actors.yml` keep their
existing appearance and load no model assets. Rendering uses GPU skinning with all eight available
influence slots. Picking rejects rays against the motion envelope and current conservative pose first, then
computes the exact posed AABB from positions only, cached until the animation or placement changes.
Full CPU deformation remains available for other geometry consumers and authored morph models. Integer joint attributes must
match unsigned integer shader inputs in both the material and sunlight-shadow programs. The 2026-10-06
fix corrects the previous float declarations that made OpenGL draw the animated actors in their bind pose.
Run `python3 tools/check_model_shadow_variants.py build/runtime/shaders/glsl` after a shader rebuild.
Mesh LOD selection uses projected size with hysteresis, four reviewed geometry levels and independent shadow detail.
Rendering uses linear-colour GGX metallic/roughness shading, normal maps, emissive factors, scene depth,
filtered mip chains, outdoor sun/sky probes and selected local lights, room lights indoors, outdoor fog,
sunlight self/ground shadows and roughness-filtered sky reflections. Indoor environment response follows room
ambient illumination; it does not show an exterior sky. Outdoor baked maps require explicit model sunlight
probes (v4+) and direct-only receiver pages for mesh shadows (v5). All 42 installed classic outdoor bakes are v5.
The original rig and material source remain under
`level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_fixed_20261005/`.
Use the selected `variants_20261006/` master/export for further work. Its original cast/socket
merge follows the preparation below and retains the existing colour and shadow LOD payload.

Prepare the level-zero runtime GLB before generating the lower levels (Pillow is required):

```sh
python3 tools/prepare_actor_glb.py \
  level_generation/creatures/mm6_demon_meshy_reference_20261004/texturing_fixed_20261005/mm6_demon_textured.glb \
  /tmp/mm6_demon_lod0.glb --omit-mesh-node Demon_Death_Plume
```

The embedded JPEG maps are transcoded to PNG for the existing runtime decoder. The standalone plume mesh,
its weight channels and orphaned binary data are omitted because the shared particle system owns that effect.
Body/ash geometry, UVs, skin weights, inverse binds and all nine clips' remaining animation samples are preserved.
Run `python3 tools/test_prepare_actor_glb.py` to check retained geometry and animation byte parity.
The renderer uploads complete colour-space-aware mip chains and respects supported glTF sampler settings.

For additional live spawns, open the debug console and use:

```text
actor spawn 502 3 -9728 -11919 161
actor count 502
actor spawn 503 1 -9528 -11919 161
actor spawn 504 1 -9328 -11919 161
```

Checks:

```sh
cmake --build build --target openyamm openyamm_unit_tests -j25
./build/tests/openyamm_unit_tests --test-case='*actor AI*,*ModelAnimation*,*launch directives*'
OPENYAMM_REGRESSION_FILTER=mm6_demon_actor_models \
  ./build/game/openyamm --world mm6 --headless-run-regression-suite actors
```

The native review capture is `output/demon_3d_review/three-demons.png`.

Validated on 2026-10-05: desktop build, 67 focused unit cases (614 assertions), outdoor factory/hit/death/restore/reset
and indoor binding checks, four existing indoor/outdoor crowding checks, and an OpenGL 3.3 native NVIDIA run.
The three-model synchronization took roughly 1.8–1.9 ms per frame in this short run; this is a prototype observation,
not a crowd-performance guarantee. The original source GLB had SHA-256
`efcca759e86c6f5c19c787e2356d3cb9480353b68a3d8a051b154b3cffd322b2`.
The original runtime GLB had SHA-256 `2336f851ff1a3533e214aed6c5ccedef33d2d9d77295ef06dd832a4fdc03b340`.

Material tuning subsequently set body metallic to zero and iris/pupil roughness to 0.22/0.18. The GLB binary chunk,
base colour and normal images, geometry, bind, morphs and animation accessors are unchanged. Backups, current hashes,
and the tuning record are in `output/creature_3d_rendering_review/material_tuning/`. The editable Blender masters and
material authoring script include the same changes. Retained material-pass captures are in
`output/creature_3d_rendering_review/pass1_tuned/tour/`.

The completed renderer review includes a [face close-up](../../../../output/creature_3d_rendering_review/head_detail/tour/01-head-front.png),
day/shade/night/torch/spell/indoor captures, native-clock pose review, live combat/turn mode, MM6/MM7/MM8 map
transitions, resize/fullscreen and resource cleanup. The latest focused run passes 152 cases / 68,446 assertions;
the two demon regressions also pass. One unrelated Ravenshore stairs check is excluded because a concurrent map
event edit invalidates its bake dependency; dependency validation is still enforced.

The [controlled performance report](../../../../output/creature_3d_rendering_review/performance/report.json) records
three models at GPU 1.471 / 1.712 ms p50/p95 and six at 2.479 / 3.012 ms on an RTX 3060 Ti at 1600×900,
VSync off. These are medians of stable one-second window percentiles. Three and six share texture/target storage;
Those earlier measurements used CPU skinning; the crowd fix above supersedes that rendering path.
Those earlier captures also recorded about one second of first-use model/mip/environment preparation;
the current loading render prewarms the reflection data and retains it across visibility changes.
Sky reflections cover the sky only; indoor point-light shadows and local reflection probes are deferred.

### Runtime LODs and shadow quality — 2026-10-06

The optimized export has colour levels of 16,474 / 8,237 / 2,980 / 1,019 triangles. One node, rig, material
set and animation set serve every level. Picking retains exact full-detail bounds. Projected bounds diameter,
viewport height and projection focal length select colour detail, with ten percent hysteresis. Dedicated
shadow meshes combine the four opaque body sections into one draw per cascade and select detail in shadow texels.
The source Blender master and portable GLB remain full detail; the selected runtime deliverable is
`level_generation/creatures/mm6_demon_meshy_reference_20261004/runtime_lods_20261006/mm6_demon_lods.glb`.

Settings → Video includes **Scale distant creature detail** and **Creature shadows**. The INI equivalents are
`video.model_lods=true`, the existing master `video.shadows`, and `video.model_shadow_quality`:

| Quality | Value | Two shared map resolutions | Near / far coverage radii | Filtering |
| --- | ---: | --- | --- | --- |
| Off | 0 | No shadow targets or submissions | — | — |
| Low | 1 | 512² each | 512 / 1,536 units | One depth comparison |
| Medium | 2 | 1,024² each | 768 / 3,072 units | 3×3 filtered comparisons |
| High | 3 | 2,048² each | 1,024 / 4,096 units | 3×3 filtered comparisons |

Medium is the default quality when shadows are enabled; the existing master switch still defaults off.
Quality controls sunlight self-shadowing and shadows on terrain/buildings together. Map resources are shared,
retained across visibility changes, and released when disabled or no model instances remain. Reflection resources
likewise belong to the scene's model consumers; the loading render prewarms them even when creatures are offscreen.
`debug.model_lod=-1` selects automatic detail; values 0–3 force colour levels for asset review only and are not saved.

To regenerate all levels from the authored source, prepare an original runtime GLB with the command above,
then use isolated background Blender:

```sh
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python tools/build_actor_lods.py -- /tmp/mm6_demon_lod0.glb \
  level_generation/creatures/mm6_demon_meshy_reference_20261004/runtime_lods_20261006/mm6_demon_lods.glb \
  --mesh-node Demon_Native_Mesh
python3 tools/test_build_actor_lods.py
```

Review the generated levels before copying the selected GLB into this runtime directory. The loader reads
`openyamm_lods` and `openyamm_shadow_lods` mesh extras, rejects bad references, and validates all levels against
the node's skin. LOD meshes are not additional scene nodes. Alpha-masked meshes without dedicated opaque shadow
LODs keep their ordinary per-material shadow submissions.

Measurements and native review are recorded in
[the LOD/shadow report](../../../../output/performance/demon_lod_shadow_20261006/REPORT.md).

## MM6 female peasant — 2026-10-06

`actors.yml` also binds `PeasantF1 A`, `PeasantF1 B` and `Peasantf1 C` (595–597) to `mm6_pfem.glb` with skins
`pfem_a/b/c` (native palettes 786/787/788). Geometry is Meshy Smart Topology, cleaned before rigging; the rig is
a fitted Mixamo skeleton with fingers plus skirt/braid/knife chains; skirt and braid secondary motion is baked
from simulation; texture is a Meshy four-view retexture on our UVs with scripted repairs.
LODs 11,806 / 5,901 / 2,124 / 705 triangles, 92 joints, one double-sided material, seven clips at native timing.
Source, scripts, review sheets and known flaws:
[the pfem project](../../../../level_generation/creatures/mm6_pfem_claude/README.md).
Run `./tools/run_pfem_3d_test.sh`; regression `OPENYAMM_REGRESSION_FILTER=mm6_pfem_actor_models`.
`pfem_sprite_compare.yml` is a review-only manifest (`debug.actor_models_manifest`) that binds only tier A so
the B/C peasants keep their native sprites for side-by-side comparison.

## MM6 male peasant — 2026-10-06

`actors.yml` binds `PeasantM1 A/B/C` (607–609) to `mm6_pman.glb` with skins `pman_a/b/c` (palettes 798/799/800;
only the tunic colour changes). Meshy Smart Topology base cleaned to 7,985 triangles (LODs 3,989 / 1,433 / 475),
fitted Mixamo rig with fingers and forearm twist, seven native-timed clips. Details:
[the pman project](../../../../level_generation/creatures/mm6_pman_claude/README.md).
Regression `OPENYAMM_REGRESSION_FILTER=mm6_pman_actor_models`; `./tools/run_pfem_3d_town.sh` shows both families.

## Decoration models — 2026-10-07

`decorations.yml` replaces decoration sprites with static 3D models, matched by decoration name (the file's header
lists the keys: `model`, `height` = the native sprite's world height, `height_jitter`, `yaw`, `z_offset`,
`lod_pixels`, `maps`). It binds New Sorpigal's `6tree01`, `6rock01` and `bigbarel`
(`level_generation/decorations/mm6_new_sorpigal_3d/`). The decoration keeps its native collision, events, picking
and picking; the sprite a decoration currently shows selects its model, so an event SetSprite to another bound
decoration moves the placement to that model (picked food tree), and one to an unbound sprite draws that sprite. Water
reflections omit model-bound decorations, as they omit model actors, until models are drawn into the reflection pass.

Asset contract: glTF Y-up metres, origin at the bottom centre, static meshes only (no skin or animation). Export LOD
objects as `Name`, `Name_LOD1`..`_LOD3` with identical transforms and run `python3 tools/link_static_model_lods.py
in.glb out.glb` (tests: `python3 tools/test_link_static_model_lods.py`), which writes `openyamm_lods` and removes the
LOD nodes. Material extras:

- `openyamm_wind`: sway amplitude in model units at the model's top, growing with height²; per-placement phase.
- `openyamm_billboard`: the mesh is one quad in the model's x/up plane; it turns about the vertical axis to face the
  camera (far impostor) and casts no sun shadow.
- `openyamm_translucency` (0..1): sunlight through thin leaves, strongest when looking toward the sun.
- `openyamm_uv_scroll` [du, dv]: texture coordinates move by this many units per second (repeat-wrapped).
- `openyamm_flipbook` [columns, rows, fps]: the mesh's 0..1 texture coordinates show one atlas cell, frames left to
  right then top to bottom, looping with a per-placement phase.
- `openyamm_flutter` (model units): cloth vertices move along their normal by amplitude × COLOR_0 alpha × a wave
  travelling along texture coordinate u (also in the sun-shadow pass).
- Hovered modelled decorations get the context-action outline (an inflated unlit shell behind the model).
- `openyamm_specular` (0..1, default 1): scales sun, point-light and sky specular. Leaf cards use 0.1: seen edge-on
  and lit from behind, full Fresnel specular turns them near-white.

Vertex colour (`COLOR_0`, linear) multiplies the base colour, as in glTF; foliage uses it for baked canopy
occlusion. The wind phase follows the placement's position, so gusts roll across a stand of trees. A colour LOD change
crossfades for 0.3 s: both levels draw with a complementary 4×4 ordered dither (instance data carries the fade), so
the switch shows no pop; the first sight of a placement and forced review LODs (`debug.model_lod`) do not fade.
Walk clip for judging switches in motion: `python3 level_generation/decorations/mm6_new_sorpigal_3d/scripts/walk_clip.py
<out_dir>` (MP4 and contact sheet).

Rendering (`Engine::ModelStaticGroup`, `ModelRenderer::renderStatic`): per placement culling and LOD with
hysteresis, one instanced submit per LOD primitive for all placements (affine matrix, ambient/sun scale from the
baked probe sampled once, point light and wind phase per instance), nearest placements first. Alpha-tested materials
get a depth-only prepass with the same program, then an equal-depth shaded pass, so overlapping leaf cards are shaded
once. Static groups also cast into the creature sun-shadow cascades. Regression:
`mm6_decoration_models_map_new_sorpigal` (maps suite).

## Harpy (MM6)

`mm6_hrp.glb` binds IDs 556–558 (`BHarpy A/B/C`). It retains separate body, head and wing PBR sets,
three native feather palettes, nine clips and four colour/shadow LODs. Full-detail colour geometry is 13,534 triangles after protected reduction.
See [the source project](../../../../level_generation/creatures/mm6_hrp_claude/README.md) for editable assets,
credit provenance, validation and the review viewer.
