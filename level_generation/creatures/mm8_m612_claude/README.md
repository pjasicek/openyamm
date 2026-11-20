# MM8 Gog — m612

> **Installed model reduced (2026-10-19):** the installed model is now the reduction from [`../mm8_m612_reduce_claude/`](../mm8_m612_reduce_claude/README.md) (LOD0 9,999 -> 7,147). This project's exports and master remain the unreduced production; the rollback source is in `../mm8_m612_reduce_claude/work/`.

> **Walk as run (2026-10-22):** at the user's request every tier binds `run: Walking`, `run_stride_length: 1.832`
> (the walk's measured stride), as do the MM7 AGog tiers. With pursuit at 1.75x (same day) chasing plays the walk at
> 1.8-2.4x (the run played at 2.3-3.1x at the old 2x); the `Running` clip stays in the GLB. A longer-striding chase
> walk would bring the rate into the 0.75-1.5 window.

Complete shared Claude humanoid-playbook production, 2026-10-18. Compact, wingless demon with three head horns,
pointed ears, ribbed abdomen, central dorsal spines, clawed hands/feet and an articulated barbed tail.
Technical and agent visual review are complete; user artistic acceptance remains separate.

## Deliverables

- [Interactive review](http://127.0.0.1:8765/level_generation/creatures/mm8_m612_claude/review/viewer/): three tiers,
  nine clips, frame scrubbing, normal/slow playback and native references. Uses the existing shared viewer template.
- [Editable packed master](export/gog_master.blend): source-frame rig, final animation and body/head PBR maps.
- [Portable green GLB](review/viewer/gog_a.glb), [blue GLB](review/viewer/gog_b.glb),
  [red GLB](review/viewer/gog_c.glb): standard baked-colour review exports, all clips and eight skin influences.
- [Engine source GLB](export/mm8_m612.glb): one mesh/material per colour draw, shared images, region ramps,
  colour/shadow LODs and sockets. Runtime colours use the engine's region-ramp extension.
- Installed source: `assets_source/worlds/mm8/models/mm8_m612.glb`.
  Cooked desktop model: `assets_dev/worlds/mm8/models/mm8_m612.glb`, with external cooked texture sidecars.
  Bindings: `assets_dev/worlds/mm8/models/actors.yml`, Gog A/B/C only.
- [Final receipt and hashes](delivery.json), [canonical progress](creature_3d_progress.json).

## Native identity and scale

| Monster | Descriptor | Skin | Native palette | Model scale | Standing height, game units |
|---|---|---|---|---|---|
| 160 Smoke Gog | Gog A | gog_a | PAL613 | 85.979254 | 146.5167 |
| 161 Ember Gog | Gog B | gog_b | PAL614 | 103.279160 | 175.9974 |
| 162 Fire Gog | Gog C | gog_c | PAL615 | 129.100886 | 220 |

Scale is the 220-pixel native standing silhouette times the sprite-frame scale, divided by the measured
1.704093648 m standing pose. Native frame scales are 0.665985, 0.799988 and 1.0. Yaw offset is -pi/2.
Native movement, combat stats, fire missiles/spells and death explosions remain owned by existing gameplay data.
No wings, equipment, new gameplay rules or renderer changes were added.

## Mesh, rig and materials

The final mesh has 9,999 triangles / 5,039 connected vertices before UV splitting. Colour and shadow detail levels
contain 9,999 / 4,999 / 2,497 / 1,234 triangles. Sixty bones comprise 46 fitted humanoid source-frame bones,
10 tail segments and four upper-arm/forearm twist bones. Hands have three fingers and an opposed thumb;
the original sprite pixels do not resolve an exact digit count. Horns, teeth, eyes and tail barb retain rigid weighting.
Both palms and both eyes have measured socket nodes. Gameplay uses the right palm for fire release and a limited
neck/head look chain (25 degrees yaw, 15 pitch).

Eight influences are intentional: reducing to four displaced the posed surface by up to 33.5 mm. The review viewer
has the small eight-weight shader extension required to match the engine. Production glTF samples at 60 Hz;
30 Hz export lost half-frame poses by up to 108 mm and was rejected. Final maximum checked export error is 5.25 mm.

Body and head were textured separately from the selected HD references. Meshy's returned body UVs were transferred
by checked face correspondence; head texturing retained the dedicated head UVs. Two 1K sets are packed without
rescaling into 2080 x 1024 atlases with a 32-pixel gutter. One shared base colour, normal, metallic/roughness/specular
map and RGBA region mask serve all tiers. Native palette ramps affect skin while preserving horns, claws, teeth
and eyes. The baked-colour portable copies are review aids; installed tiers share one texture set.

Skin is nonmetallic with roughness around 0.8 and specular mask 0.25. Keratin, teeth and eyes have separate
material classes. ORM red is the engine's specular mask; ambient occlusion is already graded into colour.
Both Meshy normal maps were measured as opposite convention and corrected once; preparation confirmed +0.68/+0.60
correlations. The UV audit found no zero-area geometry or UV triangles and 0.0612% overlapping interior texels
at atlas resolution. Face, neck seam, back, claw roots and moving joints were inspected in textured renders.

## Motion and timing

| Clip | Seconds | Source / purpose |
|---|---|---|
| Standing | 2.0 | Authored upright breathing, relaxed open claws |
| Walking | 0.8 | Local humanoid set, ArmedWalk |
| Running | 0.733333 | Local Mixamo Standard Run; fitted source ankle path and arm clearance |
| Attack | 1.766667 | ArmedCastRAttackHand1, charge lead-in and forceful outward release |
| Cast | 1.766667 | Same native attack/cast gesture |
| Hit | 0.75 | UnarmedGetHitF1 with recovery fitted inside native duration |
| Death | 1.3 | UnarmedDeath1 with supported floor/tail settling |
| Dead | 1.0 | Held final Death pose |
| Fidget | 1.5 | Authored wary head turn and chest movement |

Attack/Cast release is exactly 1.0 s, matching the native action. Follow-through lasts another 0.766667 s,
within the native recovery window. Walking/running use measured planted-foot strides 1.599956 / 1.456359 m.
These are adapted 3D performances, not reconstructions of every native sprite pose. Source fast fall motion is
retained; outgoing animation blends remain the shared runtime's responsibility.

## Evidence

- [Rig/surface gate](work/deformation_final.json), [contacts](work/contacts_final.json),
  [final Hit deformation](work/deformation_hit_final.json), [final Hit contacts](work/contacts_hit_final.json).
  All clips were sampled at half frames. No confirmed limb/tail penetration deeper than 2 mm remained.
  Worst arm edge p99 is 2.11x, near the playbook's approximate 2x guide; worst hand edge ratio is 4.44x.
  Curved claws were judged from their measured geometry and actual deformation, not a straight-finger rest-angle rule.
- [Reimport/export parity](work/export_parity.json), [UV audit](work/uv_audit.json),
  [material audit](work/material_report.json), [package assertions](work/package_check.json).
- `review/animation_textured/`: front, side and three-quarter static sequences.
  `review/playback/{a,b,c}/`: recorded actual browser playback at 1x and 0.25x for every clip.
  `review/playback/hit_{a,b,c}/`: final 0.75-second Hit playback at both rates.
  [Preservation check](work/hit_preservation.json) proves the last timing correction changed only Hit;
  the other eight clips, all LOD geometry, bind matrices and images are byte-identical.
- Shared viewer checker: all 27 tier/clip combinations loaded; no browser errors.
- Ordinary `openyamm` build passed. New regression
  `mm8_gog_actor_models_keep_native_tiers_and_palm_fire` passed: tier heights, shared asset/skins, LODs, nine clip
  durations, unchanged simulation state and each tier's right-palm Fire Bolt/Fireball origin.
  Existing `mm6_demon_actor_models_keep_simulation_and_death_rules` regression also passed.
- `review/ingame/`: matching-camera sprite/model comparisons in MM6 New Sorpigal and 6d19,
  forced LOD2 captures and final posed/live combat captures. Native rendering used OpenGL 3.3 on NVIDIA
  (vendor 0x10de), SDL Wayland. These are visual checks, not performance benchmarks.
  Fixture scenes only preload the foreign native sprite families; production maps are unchanged.

## Corrections and provenance

Smart Topology generated the body; Meshy rigging supplied joint/weight estimates. Local source-frame fitting,
digit fitting, tail/twist bones and animation repairs supplied the final rig. Eighteen duplicated flanking back
spines were removed, the central row retained, a five-edge shoulder hole closed and the tail thinned with a smooth
root blend. Geodesic digit weights, shoulder diffusion, pure-rotation tail baking, running hand clearance and
floor correction resolved the observed defects. A 0.017-second excess in Hit recovery was corrected without
changing its initial reaction or any other clip.

Paid jobs: Smart Topology 5 + rig estimate 5 + body texture 10 + head texture 10 = **30 Meshy credits**.
No paid animation jobs. Original downloads, prompts, selected/rejected HD returns and hashes remain under
`meshy/`, `references_hd/`, `references_head/` and the canonical progress record.

## Reproduction from retained checkpoints

Claim this creature with `tools/creature_workspace.py` before changing it. Run project writes under that token;
use `tools/run_creature_blender.sh --token TOKEN scripts/<step>.py` with each script's full project-relative path.
Do not resubmit the four completed Meshy jobs.

1. `work/textured_uv.blend` is the final geometry/UV/animation checkpoint. `scripts/compose_textures.py` rebuilds
   native material classes/ramps from the retained PBR returns. `scripts/export_textured.py` creates the packed
   master, portable tier GLBs and `export/gog_runtime_lod0_raw.glb` at 60 Hz.
2. `tools/prepare_actor_glb.py <raw> export/gog_prepared.glb`, then Blender `scripts/lods.py` and ordinary Python
   `scripts/package.py` produce `export/mm8_m612.glb`. `scripts/uv_audit.py` checks its final layout.
3. Install with `python3 tools/install_model.py <project>/export/mm8_m612.glb --world mm8`.
   Never copy the cooked runtime model back over the project or source export.
4. Build `cmake --build build --target openyamm -j25`, then
   `OPENYAMM_REGRESSION_FILTER=mm8_gog ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`.
5. `scripts/prepare_reviews.py` creates a fresh isolated asset fixture and native comparison tours.
   Launch records and requested settings are retained in `review/ingame/launch_records/`.
   `debug.actor_models=false` selects sprites; `video.actor_models` is not the correct setting.

Earlier experimental scripts and checkpoints are retained for provenance and are not an instruction to replay
rejected repairs. `scripts/finish_rig.py` includes the final Hit timing fix when rebuilding from pre-UV motion.

Android and Vulkan were not tested. User artistic approval is pending; no commit or staging operation was performed.
