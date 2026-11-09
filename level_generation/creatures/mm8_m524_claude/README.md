# MM8 Serpentman · m524

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m524_reduce_claude/`](../mm8_m524_reduce_claude/README.md) (LOD0 10,618 -> 6,156). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m524_reduce_claude/work/`.

Built and installed on 2026-10-18 using the shared Claude non-humanoid workflow. Technical checks are complete;
artistic acceptance remains with the user. The snake tail supports an upright, unarmed attacking torso.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m524_claude/review/viewer/)
· [Editable, packed Blender master](export/mm8_m524.blend)
· [Runtime source GLB](export/mm8_m524.glb)
· [Native motion study](ANIMATION_STUDY.md)
· [Progress, provenance and receipts](creature_3d_progress.json)

The viewer provides all eight clips, frame stepping, slow playback, skeleton/wireframe, native source sheets and
frame-specific feedback. Its tier selector uses a common preview scale; the native game comparisons show the
actual tier sizes. Viewer copies bake the engine's region ramps for three.js; installed tiers share one texture set.

## Delivered asset

- 61 bones, at most four weights per vertex; 26-segment tail, spine, neck, jaw, articulated arms and three digits
  per hand. No held weapon, humanoid auto-rig, paid animation, invented spell or attack glow.
- Colour LODs: 10,618 / 5,308 / 1,907 / 613 triangles, plus matching shadow meshes. The shared reduction tool uses
  stronger far reductions than the general 50% guideline. Head and claws are protected in the initial reduction;
  the final coarse LOD is for distance. Each colour LOD has one atlas material primitive.
- Separate 1K body/head base colour, normal, packed occlusion/roughness/metallic and region maps; runtime combines
  each pair into a 2080×1024 atlas with padding. Three material variants share all four atlas images.
- `scripts/compose_textures.py` writes native-palette ramps and material-class maps. Classes follow the shared
  texture guide: skin 1, claws 4, teeth 5, eyes 6, mouth 7. Cycles AO is packed in R, roughness in G, metallic 0 in B;
  a gentle 0.35 AO grade retains the Meshy paint. Creature specular and metallic factor are 0 per the current guide.
  Meshy's downward-Y normals are converted once; the runtime preparation reports the resulting maps as upward-Y.
- Full-body and close head HD references, original Meshy responses and input hashes are retained. Meshy cost:
  geometry **5**, body texture **10**, head texture **10** = **25 credits**, with no unfinished jobs.

| Clip | Seconds | Behaviour |
|---|---:|---|
| Standing | 3.000 | Grounded idle, breathing and small arm motion |
| Walk | 1.125 | Travelling tail wave, stable upright torso |
| Running | 0.750 | Stronger travelling tail wave |
| Fidget | 0.625 | Small hand and torso shifts |
| Attack | 1.125 | Wind-up, forward strike at 0.750 s, recovery |
| Hit | 0.625 | Backward recoil and recovery |
| Death | 0.750 | Backward/right collapse beside the tail |
| Dead | 1.000 | Held final death pose |

These are smooth, locally authored interpretations of the original motion, not literal sprite-frame
reconstructions. The original attack is 0.875 s; the added recovery does not change gameplay damage timing.
The corpse retains the native-inspired arched head. Walk/run use a 3.2 m movement-driven stride to match the long
body wave. Cast and unused ranged roles alias Attack; native poison-melee combat rules are unchanged.

## Integration and comparisons

Installed source: `assets_source/worlds/mm8/models/mm8_m524.glb`; desktop cooked model and textures:
`assets_dev/worlds/mm8/models/`. Only the Serpentmen entries were added to the shared MM8 `actors.yml`.

| Descriptor | Monster ID | Native palette | World-units/metre |
|---|---:|---:|---:|
| Serpentmen A | 94 | 524 | 67.063780431 |
| Serpentmen B | 95 | 524 | 82.540335077 |
| Serpentmen C | 96 | 524 | 98.016889723 |

The three tiers deliberately share colours: the original differs in size, not palette. Scale is measured from
103 standing pixels × the native SFT scale (1.299988 / 1.599991 / 1.899994), divided by 1.996588369 m mean standing
height. Explicit scales also allow foreign-map summons whose B/C standing SFT families are not independently loaded.

| Camera | Original sprites | Final installed model |
|---|---|---|
| New Sorpigal outdoors | [Original](review/ingame/outdoor_sprites_locked/01-party.png) | [3D](review/ingame/outdoor_models_locked/01-party.png) |
| Agar's Laboratory indoors | [Original](review/ingame/indoor_sprites_locked/01-party.png) | [3D](review/ingame/indoor_models_locked/01-party.png) |

All four forced LODs were captured in both scenes. Pillars partially occlude the outer indoor tiers in both
original and 3D comparisons. These are engine-native readbacks on NVIDIA OpenGL through the authorized desktop
launcher. They are visual checks, not performance benchmarks.

`review/ingame/indoor_fixture.json` records an isolated hard-link asset fixture, with independent scene copies
that preload these foreign MM8 sprite families. Both production MM6 scene hashes were checked unchanged.
`scripts/prepare_indoor_fixture.py` reproduces the two-map fixture. Run records and logs are in
`review/ingame/records/`; screenshot/menu tour YAML files preserve cameras and inputs. Early unlocked-camera
captures are not selected evidence.

## Verification and corrections

- Development `openyamm` build passed. The added Serpentman headless regression checks all three bindings, all eight
  actor states, shared model identity, unchanged simulation state; delivery assertions also check tier scale ordering.
- Final wider MM8 run: six cases passed, including Serpentman, Wyvern, Crystal Walker, Gorgon, Troll and Couatl.
  Mercenary and Efreeti cases failed because those concurrently developed bindings were absent from `actors.yml`;
  these failures are outside this creature's changes. Exact results: `review/mm8_regressions.log`.
- Final browser check: 24 tier/clip combinations, no console errors or failed switches (`review/viewer_check.json`).
  All eight clips were recorded during playback at 1× and ½× (`review/playback/`), with timestamped frame samples
  inspected for support, silhouette, joint deformation and endpoints. Recordings are supplied for continuous human
  motion review; this does not assert user artistic approval.
- Final GLB reimport vs editable master: 72 poses, maximum surface discrepancy **0.041 mm**, maximum mouth-socket
  discrepancy **0.0013 mm**. Dense 96 Hz sampling stays above the plane by at least **3.3 mm**; loop endpoints match.
  See `review/export_parity.json`. World collision and damage volumes remain native.
- Frozen UV gate: zero body overlap pixels; two head edge-raster pixels. Density is about 2.26 px/cm on the body
  and 6.6 px/cm on the separately packed head at 1K. Texture-return UVs match exactly; Meshy's uniform model
  recentering/rescaling was verified and only maps were transferred to the animated master.
- Final winding check: no inverted closed parts. File/texture/binding assertions and provenance hashes are recorded
  in `review/delivery_validation.json`.

Corrections retained in the source: removed a duplicated digit per hand; repaired four accidental skin holes;
separated jaw/skull/teeth ownership; smoothed torso-tail weights; protected head/claws during reduction; corrected
UV-layer ownership before texturing; blended the full-body/head neck seam; limited shadow shrink at tiny fangs;
used measured explicit tier scales; corrected class labels and AO packing to the shared texture contract.

## Rebuild from the frozen master

Run project writes with the active creature-workspace lease. Blender scripts use `tools/run_creature_blender.sh`.
The selected input is **`work/anim_uv.blend`**; paid returns and UVs are already frozen. Do not rerun Meshy or replace
this animated input with a static texture return.

1. `scripts/bake_ao.py` in Blender, then `scripts/compose_textures.py` in Python.
2. `scripts/export_serpentman.py` in Blender → `export/mm8_m524_lod0.glb` and the packed editable master.
3. `tools/prepare_actor_glb.py` → `export/mm8_m524_runtime_lod0.glb`.
4. `scripts/build_lods.py` in Blender, then `scripts/finish_runtime.py` in Python.
5. `scripts/export_parity.py` in Blender, winding check, then `tools/install_model.py export/mm8_m524.glb --world mm8`.
6. `scripts/viewer_tiers.py`, `scripts/update_viewer_manifest.py`, then the approved `tools/run_creature_review.py`
   check/capture workflow. Refresh only this model and its referenced textures in an existing private fixture before
   repeating the native tours.

No Vulkan or Android build was run. Continuous human art/motion acceptance remains pending; browser lighting
is neutral review lighting, so use the native comparisons to judge game appearance.
