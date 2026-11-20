# MM6 Thug, Ruffian and Brigand

Created and installed 2026-10-11 using the current [Claude humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md).
Native identity `mm6:fgt`, descriptors **FighterLeath A/B/C**, IDs **538/539/540**, palettes **733/734/735**.
Technical production and agent visual review are complete. The user accepted revision 2's right shoulder repair.

> **Walk as run (2026-10-22):** the user found the head bobbing too much while running and asked for a walk instead.
> The `Running` clip moves the head 0.24 m vertically (17 % of head height; the walk 0.036 m). All tiers now bind
> `run: Walking`, `run_stride_length: 1.602` (the walk's measured stride); with pursuit at 1.75x chasing plays the
> walk at 1.4-1.7x. The `Running` clip stays in the GLB.

Revision 3 applies the subsequently requested selective native contrast pass; its artistic acceptance is pending.

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm6_fgt_claude/review/viewer/index.html) ·
[Editable Blender file](export/mm6_fgt.blend) · [Portable Thug GLB](review/viewer/mm6_fgt_a.glb) ·
[Animation study](ANIMATION_STUDY.md) · [Canonical progress and receipts](creature_3d_progress.json)

![3D and original sprite presentation, outdoors and indoors](review/ingame/tiers_3d_vs_sprite.png)

The paired captures use the same cameras and spawn commands. The summon helper adjusts placement, so these are
colour/appearance comparisons, not pixel-aligned scale measurements. The binding regression independently checks
all three model heights against the native standing height. Full captures and console spawn proof are retained.

## Triangle reduction (installed 2026-10-14)

The installed body and mace are the reduced models from [mm6_fgt_reduce_claude](../mm6_fgt_reduce_claude/README.md):
body 9,305 -> 6,871 (face, eyes, skirt strips and belt pieces unchanged), mace 2,232 -> 974; same textures, tiers and
clips. The counts under Delivered below describe the pre-reduction model (rollback sources are in that project).

## Delivered

- Runtime: `assets_dev/worlds/mm6/models/mm6_fgt.glb` and `mm6_fgt_mace.glb`; bindings in that folder's `actors.yml`.
  Local copies and hashes are in [export/runtime_validation.json](export/runtime_validation.json).
- Body, five-finger gloves, studded leather, steel pauldrons and copper caps, boots, left-hip sheathed blade and
  scarf tail. The locally modelled spiked mace attaches to `Mace`, releases during Death and rests beside the corpse.
- 11,537 triangles including the 2,232-triangle mace. Combined colour LODs: 11,537 / 5,767 / 2,064 / 662.
  Source-frame humanoid rig: 52 library bones, four twist bones and Mace. Body and attachment together are 9.3 MB.
- Body 1K and head 1K maps, merged for runtime into four 2080×1024 atlases. Three skins share every image.
  RGBA mask channels: fabric, leather, copper, skin. Each tier uses its own native palette; shader ramps retain
  the generated texture's smooth value detail. Specular mask is MR.R under the current engine contract;
  roughness is MR.G, metallic is zero. AO is retained separately and baked lightly into body colour.
- Packed editable `export/mm6_fgt.blend` displays final Thug colours and glTF-convention normals. The unchanged rig/UV
  master is `work/rig_revision2.blend`; the refreshed textured assembly is `work/thug_final.blend`.
  The three viewer GLBs are portable baked-colour previews; runtime uses shared masks/ramps.

## User revision 3 — selective native contrast

The accepted shoulder repair, face, hair, mace and all motion are preserved. `scripts/compose_fgt.py` uses the
measurement/coordinate helpers from `claude_shared/native_shading.py` on native front and back standing frames.
It applies a 30% median-normalised height profile only to the leather torso, feathered in physical space across
UV seams. The resulting colour multiplier is 0.960–1.090. Steel plates take 40% of the native midtone-to-highlight
contrast, with the 90th-percentile brightness retained: median sRGB-grey luminance 0.461 → 0.403.
These are texture measurements, not rendered brightness targets. No whole-body lighting bake or ramp replacement.

Only `fgt_basecolor_1k.png` changed. Head, mace, normal/roughness maps, region masks and all tier ramps remain
byte-identical. The prepared exports were updated by image-buffer replacement, retaining all geometry, UVs,
skinning and **1,368 animation channels** exactly; the installed mace GLB is also byte-identical. Evidence:
[export preservation](review/revision3/export_preservation.json), [measurement](review/revision3/native_contrast.json).

[Viewer before/after](review/revision3/browser_comparison.png) ·
[Native indoor/outdoor before/after](review/revision3/native_comparison.png) ·
[Native attack](review/revision3/ingame/combat/combat_7.png) ·
[Persistent corpse](review/revision3/ingame/combat/corpse.png)

The native A/B uses both revisions in one game boot per location, toggled at the identical Standing time and
position; this isolates the subtle material change from actor wandering. These body-only diagnostic instances
omit the separate mace. Normal actor captures include all three tiers, attacks, the fall and dropped weapons.
The final combat run sets `gameplay.corpses=keep` only in its isolated settings. All captures use NVIDIA/OpenGL.
The viewer passes 24 tier/clip combinations, with normal/quarter-speed playback checked, and the focused Thug
regression passes. Changes remain deliberately modest, including when the torso lies down.

Reproduce with ordinary Python `scripts/compose_fgt.py`, `scripts/refresh_contrast_exports.py`,
`scripts/finalize_runtime.py`, then Blender `scripts/refresh_contrast_authoring.py`. Use the project lease wrappers.
The image refresh reuses the accepted prepared LODs; a full rebuild still reads current textures through
`scripts/export_runtime.py`. Accepted revision 2 exports/maps are retained in `review/revision3/before/`.
For the fixed-pose tours, temporarily mount `before/export/mm6_fgt.glb` as
`assets_dev/worlds/mm6/models/mm6_fgt_contrast_before.glb`, then remove that comparison copy after capture.
**Zero additional credits; 40 / 100 total.** No engine or binding changes. Android and Vulkan were not tested.

## User revision 2 — right shoulder

The copper pad and steel collar had different attachments, so a fit in Standing alone missed intersections during
motion. Both right shoulder surfaces now inherit the underlying shoulder/chest deformation. The steel rim has
up to 8 mm forward and 4 mm rearward clearance; the copper pad is recessed 10 mm down the arm. The left shoulder,
hair, mace, UVs and topology are preserved. All **1,368 animation channels are byte-identical** to revision 1.

The dedicated [shoulder gate](review/revision2/export_shoulder_gate.json) checks actual triangle crossings,
including between authored frames: **zero crossings in 1,798 samples at 192 Hz across all eight clips**, in both
the authoring master and exported GLB. Generic contact gates had excluded the arm's own shoulder equipment.
Skin/trim contact counts in the diagnostic report are separate from the pad/steel crossing assertion.

[Standing frame 41](review/revision2/browser/stand41.png) · [Walking frame 30](review/revision2/browser/walk30.png) ·
[Attack from above](review/revision2/browser/attack_mid.png) · [Native combat](review/revision2/ingame/combat/combat_7.png)

The viewer passes all 24 tier/clip combinations and normal/quarter-speed playback. The focused Thug regression
passes. New NVIDIA/OpenGL captures cover outdoors, indoors, combat, death and the persistent corpse. The existing
body/mace/skirt contact and source-speed gates pass; head/shoulder depth is at most 7.3 mm briefly during Death
(within the playbook's approximately 1 cm limit), and zero in the other clips. No animation correction was needed.

Reproduce from revision 1 with Blender `scripts/right_shoulder_repair.py`, then `scripts/revision2_checks.py`.
Run the existing prepare step, Blender `scripts/export_shoulder_gate.py` and `scripts/revision2_exports.py`, then
ordinary Python `scripts/finalize_runtime.py`. Selected exports, LODs, all three viewer tiers and installed assets
have been refreshed. This revision used **zero Meshy credits**; total spending remains **40 / 100**.

## User revision 1 — 2026-10-11

The right shoulder's motion fit below was incomplete and is superseded by revision 2. Hair and mace refinements remain selected.

The steel rims now fit the upper pads in the standing pose. Their original weights remain intact so the chest
collar stays stable in motion; a small neck correction clears the revised plate during the fall. The long cheek
hair strips were shortened and tapered. The morningstar now has a rounded head, finer spikes and collars, and a
separate detailed metal/leather PBR atlas. Its original fitted grip and release trajectory are unchanged.

[Shoulders](review/revision1/browser/shoulders.png) · [Hair](review/revision1/browser/hair.png) ·
[Morningstar](review/revision1/browser/mace.png) · [Runtime combat](review/revision1/ingame/combat/combat_4.png)

All eight deformation checks and the exported source-speed trace pass. The viewer loads all 24 tier/clip pairs
and plays all eight roles at normal and quarter speed. The focused Thug regression passes; new native outdoor,
indoor, combat, release and corpse captures are in `review/revision1/ingame/`. Comparison of 1,368 animation
channels found only the small Death neck-rotation correction; the other channels match the prior delivery.
The revised weapon uses 2,232 triangles; total LOD0 is 11,537, with combined LODs 5,768 / 2,064 / 663.
The weapon has its own 1K atlas; the earlier body-atlas mace swatches are no longer used.

To reproduce this revision after the original body/head UV transfer, run Blender `scripts/revision_rebuild.py`,
then `scripts/compose_mace.py` under ordinary Python, followed by the existing export/prepare/LOD/finalize chain
and `scripts/pack_authoring.py`. The paid mace return is retained under `meshy/mace_retexture_v1/`; no new paid
submission is needed. `work/rig_textured.blend` remains the pre-revision input. User screenshots and the old
textured master/export are retained under `review/revision1/`.

## Motion and timing

| Role | Seconds | Basis |
|---|---:|---|
| Standing | 2.0 | ArmedIdle, upright native legs and lowered guard |
| Walking | 0.8 | ArmedWalk; measured stride 0.93 m |
| Running | 0.8 | ArmedRunForward |
| Attack | 1.2 | SwordAttackR3 backhand, 0.4 s ready lead, native mace |
| Hit | 0.5 | ArmedGetHitF1 with eased start/end |
| Death | 1.533 | ArmedKnockdown1 backward fall, mace release at frame 8 |
| Dead | 1.0 | Final supine pose and released mace held |
| Fidget | 1.5 | Authored native weight shift and head glance |

All keys are at 30 fps. Attack impact is **0.783 s** against a native 0.75 s action: wind-up stretch 0.958×;
follow-through uses the existing engine path. Spine twist is softly limited to 45 degrees. Neck/head look uses
60° yaw and 35° pitch. Scale **122.8** comes from 261 visible pixels × 0.8 / 1.7 m. This family has no spell or
projectile; attack_melee and attack_ranged use the same native Attack. `animation.cast` aliases Attack solely for
the shared binding schema; there is no invented Cast action.

## Gates and corrections

| Gate | Evidence/result |
|---|---|
| G1 source motion | Library mace attacks were overhead; R3 matches the crossed-hand backhand. Backward knockdown replaced the forward death. ROM refreshed for selected clips. |
| G2 proportions | Arm lengths 1.02/1.05× source; wider hips 1.41×. Warning recorded in `work/proportions.json`. |
| G3 joints/frames | Meshy joint estimate plus fitted arm rings, fitted hands and connectivity-cut fingers. Source frame error 0; initial weight transfer distance 0 mm. |
| G4 weights | Attack arm stretch p99 ≤1.75×; torso/armour weights corrected, twists above bracers; each closed tasset has one L/R thigh mixture. |
| G5 grip | Source grip axis with solved fingers and thumb base. Worst hand edge stretch 4.33×; textured close-ups of both hands reviewed from exported GLB. |
| G6 contacts | All eight clips: no measured body/mace intersections and no outward tasset crossing. Head/shoulder maximum 7.3 mm during Death after revision 2; zero pad/steel crossings at 192 Hz. Export trace at 1/48 s: zero source-speed flags. |
| G7 textures/export | Body and head UV transfer both 0.0 mm, no corner mismatch. Eight clips × three viewer tiers load without errors. All eight play at normal and quarter speed. |
| Runtime | Ordinary build passes; Thug regression passes; real NVIDIA/OpenGL desktop review outdoors, indoors, combat, death and persistent corpse. |

The contact gates account for open boundary edges and the outward surface of the Thug's closed leather strips;
the previous generic skirt check falsely counted the inner face of a closed strip as penetration in the bind pose.
The physical corrections were made in weights/rest geometry, then the full rig chain was replayed. A 6 mm tasset
clearance and a 10° sheath tuck eliminated the remaining contacts. The exported hit transition needed a six-frame
ease to stay within the source-speed gate. Logs are in [review/evidence](review/evidence).

The first palette grade exaggerated the sprites' baked shadows into mottled facial skin and leather. Final ramps
use native hue/brightness with the generated texture's smooth shading. Pale projection on the thin sideburn shells
was corrected to match the hair. Region masks are padded into UV gutters before feathering; mace swatches have
zero masks. Material class maps and the ungraded Meshy returns remain available.

## Checks and evidence

- `cmake --build build --target openyamm -j25`: passed.
- `OPENYAMM_REGRESSION_FILTER=mm6_ ./build/game/openyamm --world mm6 --headless-run-regression-suite actors`:
  **31 passed, 1 failed**. `mm6_thug_actor_model_tiers_and_mace` passes. The unrelated
  `mm6_ogr_actor_models_bind_all_tiers` fails on **Demon A: actor ranged hand element/effect not found**;
  that case configures the shared manifest without first loading the named-effect library. No engine change
  was made to hide or repair that unrelated test failure.
- [Viewer playback checks](review/browser/playback_review.json): eight roles, normal/quarter speed;
  final viewer audit: 24 tier/clip combinations, zero console errors.
- Both installed normal maps pass `normal_map_convention.py --check` (merged body/head +0.48, mace +0.97).
  Runtime validation checks finite positions, valid indices, nondegenerate triangles, all roles, LODs and skins.
- [Outdoor](review/ingame/frozen_outdoor_3d/tiers.png), [indoor](review/ingame/frozen_indoor_3d/tiers.png),
  [combat](review/ingame/combat/combat_4.png), [mace release](review/ingame/combat/death_early.png),
  [corpse](review/ingame/combat/corpse.png). Full run logs, camera/settings records and GPU identity are under
  `review/ingame/runs/`. Indoor lighting is intentionally dim; both sprite and 3D comparisons show that lighting.

## Reproduction and cost

Claim this creature before mutations using `tools/creature_workspace.py`; use the returned token with the existing
Meshy/Blender wrappers. All original inputs and paid returns are retained; a rebuild does not need new Meshy jobs.

1. `scripts/replay_sheath.py`: cleanup, source-frame rig, weights/fingers, clip timing, mace, contact gates,
   source ROM/proportions and clay export/trace. `texture_ready.py` also creates the texture-upload split.
2. `scripts/transfer_and_bake.py`: transfer the retained body/head UV returns, rasterise semantic regions and bake
   body-only AO. The head is a separate occluder so its own UV layout cannot overwrite body AO texels.
3. `scripts/compose_fgt.py`, then Blender `scripts/export_runtime.py`; run `tools/prepare_actor_glb.py` on
   `export/mm6_fgt_lod0.glb` to produce `export/mm6_fgt_runtime_lod0.glb`.
4. Blender `scripts/build_lods.py`, then `scripts/finalize_runtime.py`: shadow correction, three region variants,
   mace attachment split, head material merge, integrity validation, install and viewer copies. Finally
   `scripts/pack_authoring.py` packs the editable tier-A Blender file.
5. Re-run affected gates after changes; use the saved input tours for the normal desktop launcher.

**Meshy spend: 40 / 100 credits** — Smart Topology 5, rig estimate/weights 5, body retexture 10, head retexture 10, revised mace retexture 10.
One unsupported request was rejected before a task was created and cost zero. No paid library animations;
all motion came from the local humanoid library. Complete requests, hashes and receipts are in the canonical JSON.

The short scarf tail follows the torso; it has no cloth simulation. Unseen depth and some motion are inferred
from the native sprites, as described in the animation study. Android and Vulkan were not tested. No commit made.

## Gait rollout (2026-10-31)

Package h01 of the [gait rollout](../gait_rollout_20261031/README.md) appended `Sprint` (humanoid set Unarmed-Sprint,
0.57 s, stride 3.7784; arms and mace from `Running`, aligned to `Walking`) to the installed `mm6_fgt.glb` for MAW's
chase. Standard keeps the walk at every speed (`run: Walking`, the user's choice above). Existing clips untouched;
bindings for the coordinator in `../gait_rollout_20261031/h01/bindings.yml`. Details, gates and doubts:
[h01 README](../gait_rollout_20261031/h01/README.md). Rebuild: `../gait_rollout_20261031/h01/scripts/rebuild.sh fgt`.
A far-LOD repair rerun (or any other rebuild of this source) must re-graft the clip: copy the new source over
`h01/work/mm6_fgt_pre_gait.glb` and rerun that command, then install its export.
