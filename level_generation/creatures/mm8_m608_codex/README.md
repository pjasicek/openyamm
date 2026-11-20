# MM8 Juggernaut — m608

Completed production model for Charger, Juggernaut and Demolisher (monster IDs 157–159).
Technical delivery is complete; the user approved the corrected shoulder revision on 2026-10-18.

- [Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m608_codex/review/viewer/)
- [Portable animated GLB](export/mm8_m608.glb) and [packed editable Blender scene](export/mm8_m608.blend)
- [Outdoor model](review/ingame/out_models/front.png) / [native sprite](review/ingame/out_sprites/front.png)
- [Indoor model](review/ingame/in_models/front.png) / [native sprite](review/ingame/in_sprites/front.png)
- [Native melee attack](review/ingame/attack_overview.png) / [hit, death and loot transition](review/ingame/death_overview.png)
- [Stationary outdoor LOD2](review/ingame/out_lod/lod2.png) / [indoor LOD2](review/ingame/in_lod/lod2.png)
- [Face](review/shots/head.png), [strike](review/shots/strike.png), [rubble](review/shots/dead.png)
- [Normal playback overview](review/playback/overview-1.png) / [half speed](review/playback/overview-0.5.png)

## Moving shoulder correction — 2026-10-18

The previous stretch repair incorrectly kept the front shoulder caps and socket stones attached to the chest.
The user rejected that revision because the shoulders stopped moving. The crease cut now includes each complete
front cap, and both caps and socket stones follow their upper-arm bones. Ribs stay separate, so raising the arms
does not pull them into sheets. New closed joint surfaces use continuous stone UVs from the existing atlas.
Arm trajectories, timing, rollers and combat bindings are unchanged. All dependent fragments, clips, exports,
colour/shadow LODs and runtime assets were rebuilt and installed without paid generation.

- [Rest](review/shots/moving_shoulders_rest.png) / [raised arms](review/shots/moving_shoulders_up.png) /
  [back](review/shots/moving_shoulders_back.png) / [side](review/shots/moving_shoulders_side.png)
- Recorded [attack](review/shoulder_motion_v3/Attack-recorded-sequence.jpg),
  [hit](review/shoulder_motion_v3/Hit-recorded-sequence.jpg) and
  [death](review/shoulder_motion_v3/Death-recorded-sequence.jpg) frame sequences
- [Native attack sequence](review/shoulder_motion_v3/native-attack-sequence.jpg) /
  [indoor tiers](review/shoulder_motion_v3/ingame/in_lod/front.png) /
  [indoor LOD2](review/shoulder_motion_v3/ingame/in_lod/lod2.png)

The shoulder regression checks 316 poses, pure upper-arm ownership, rigid cap edge lengths and actual movement
relative to the chest. Peak cap travel is 8.6–8.9 cm during attack and 9.6–9.9 cm during hit at 1 m asset height;
cap edge-length error stays below 0.0005%. No face mixes arm and torso influences. The wider shoulder/elbow region
stays below 2.27× edge stretch, with remaining blending at the elbows. Export surface parity, 657 floor samples,
all 18 colour/shadow meshes and all 21 browser tier/clip combinations pass. Fourteen recordings were refreshed;
agent review inspected actual recorded frame sequences, without claiming real-time video viewing.

The focused Juggernaut regression now passes against the current production manifest:
[log](review/shoulder_motion_v3/production_regression.log). Native outdoor combat and indoor tiers/LOD2 were
checked with the installed model. [Run records](review/shoulder_motion_v3/ingame/runs.json) identify its hash and
the game binaries. The earlier Naga validation blocker is no longer present in this focused run.

Current source SHA-256: `81986d80055f5f63dabff989485c4a1eb2764f4df2b9aa420cbebec9fabdcf7d`.
The rejected v2 export and construction checkpoints remain in `work/shoulder_motion_v3/before/`.
Earlier stretch evidence remains in `review/shoulders/`; original sprite comparisons and the wider regression
below are historical. The user approved this follow-up on 2026-10-18 ("good").

## Design and sources

The native study is [references_hd/native_study.png](references_hd/native_study.png), with exact source frames,
palettes and action durations in [CODEX_BRIEF.md](references_hd/CODEX_BRIEF.md), [native inputs](references_hd/native_inputs.json)
and [the source inventory](../mm8_m608/sources.json). Grey stone, the skull-like face, two hands, a coloured waist
band and three distinct rough rollers define the creature. The torso floats above the rollers, as in the sprites.
There are no legs, axles or caterpillar tracks.

Five selected HD body views and four head views guided geometry and texturing. Slightly oblique side references
are recorded as such; no invented rear animation evidence is claimed. Attack, hit, death and fidget are
front-authored native actions reused across viewing directions. Image-generation prompts and hashes are in
`references_hd/generation_runs.json` and `references_head/generation_runs.json`. Rejected views and the superseded
head texture are retained. Meshy received HD references and neutral fitted meshes, not native sprite images.

Meshy cost: **35 credits** (5 geometry + 10 body texture + 20 head texture across two attempts), against the
100-credit production limit. All job IDs, inputs, downloads and receipts are in `creature_3d_progress.json`.
The chosen jobs are `smart_topology_v1`, `body_texture_v1`, and `head_texture_v2`.

## Rig and motion

The fitted rig has 78 bones, at most four normalized influences per vertex, rigid rollers and 63 rigid death
fragments. The local analytic arm rig reuses the existing creature posing helper. No purchased animations were
needed. Broad stone hands remain rigid; the visible native gestures come from the shoulders, elbows and wrists.

| Role | Clip | Duration | Behavior |
| --- | --- | --- | --- |
| Idle | Standing | 2 s | Very small upper-body movement; closed loop |
| Move/run | Walking | 1 s | One full roller revolution; closed loop |
| Melee | Attack | 1.25 s | Raised arms, forward palm strike, impact at native 1.0 s, then recovery |
| Damage | Hit | 1.125 s | Native raised-arm recoil and recovery |
| Fidget | Fidget | 0.625 s | Small head and wrist movement |
| Dying | Death | 0.75 s | Recoil, fragment release at 0.25 s, rubble settlement |
| Corpse | Dead | 1/48 s | Held rubble pose with the tier's waist band |

All clips are sampled at 48 fps, with quaternion continuity and exported linear interpolation. The melee flash
is a brief local blended mesh between the palms, not a gameplay projectile. The family has no ranged or cast
behavior; combat tables were not changed.

The rough rollers rotate as solid objects, with vertical support evaluated from their actual contours. Their
radial scale is 94%, maintaining at least **0.0185 m** clearance below the band across 97 roll samples. The
locomotion stride is **1.11 m per revolution**, based on the fitted roller circumferences; the engine advances
it by travelled distance. Exported subframes keep the rollers above the floor. This authored rolling contact
uses the existing actor root placement; it does not add individual wheel suspension or terrain physics.

Standing height is 1 m in the asset. Native standing alpha height is 199 pixels at scale 2, giving the shared
runtime scale **398** for all three tiers. The dead pile's height is **0.301508 m**, matching the native
60/199 corpse-to-standing ratio. The band stays among the stone fragments rather than disappearing.

## Materials and detail levels

Body and head were textured separately, preserving their UVs, then merged into one 2080×1024 atlas with a gutter.
Stone is opaque grey rock: roughness 0.86, metallic 0, specular mask 0.12. The band uses roughness 0.44,
metallic 0.62 and specular mask 0.80. AO is applied mildly to the colour map. Measured DirectX normal maps were
converted to the glTF convention; the final embedded map passes the convention check. Pale-yellow eyes are
separate unlit geometry. Only the short melee flash is blended and double-sided.

The three belt palettes follow native palettes 609/610/611 through shared region ramps (`m608_a/b/c`).
Geometry, animation and textures are shared by all tiers. Browser preview copies bake those same ramps because
the review viewer does not implement the engine's custom region material; these copies are never installed.

| Mesh | LOD0 | LOD1 | LOD2 | LOD3 |
| --- | ---: | ---: | ---: | ---: |
| Living body | 6,221 | 3,110 | 1,554 | 763 |
| Rubble | 2,854 | 1,426 | 706 | 325 |

Matching shadow LODs are included. The tiny eyes (92 triangles) and flash (152 triangles) retain their geometry.
Living body and rubble use collapsed-mesh visibility channels so the unused representation does not draw.
Only the flash needs two-sided surfaces. After decimation, 23 body-LOD faces and their shadow counterparts
needed their inherited normals recalculated; `fix_lod_normals.py` isolates those corners without changing
positions, weights, UVs or animation. The final audit finds no degenerate triangles, collapsed UV triangles or
face/vertex-normal reversals in any of the 18 colour/shadow meshes.

## Integration and verification

Installed with `tools/install_model.py`; hashes and byte sizes are in [integration/install_receipt.json](integration/install_receipt.json).
Source: `assets_source/worlds/mm8/models/mm8_m608.glb`. Cooked runtime: `assets_dev/worlds/mm8/models/mm8_m608.glb`.
The three descriptor bindings were appended to `assets_dev/worlds/mm8/models/actors.yml`; a project copy is in
[integration/actors.yml](integration/actors.yml). Existing descriptors and native sprites were preserved.

Validation records:

- `work/export_audit.json`: actual GLB surfaces match the Blender scene within 0.000033 m; 657 subframe floor
  samples; closed idle/walk loops, held corpse, unique node names, normalized weights and three rigid rollers.
- `work/contact_audit.json`: roller clearance, floor support and native corpse-height calibration.
- `work/static_audit.json`: all colour/shadow LOD geometry, UVs and normal-map convention.
- `review/shoulder_motion_v3/viewer_check.json`: all 21 tier/clip combinations load without browser errors.
- `review/playback/`: 14 real viewer recordings at 1× and 0.5×, with consecutive captured frames and readouts.
  Agent review inspected those frame sequences, the face, both hands, the impact and the settled rubble.
- Ordinary `openyamm` build passed. Focused Juggernaut binding regression passed after final installation.
  It checks shared ownership, all tiers, scale, bones, sockets, role clips and unchanged simulation state.
- MM8 actor regression: **40 passed, 1 failed**. The separate Naga case reports
  `Naga sword or serpent rig missing`; this creature task does not modify that asset or test.
- Native OpenGL 3.3/NVIDIA Wayland captures compare all three tiers against sprites at the same cameras in
  New Sorpigal (`oute3.odm`) and Agar's Laboratory (`6d19.blv`), including forced LOD2 views. The isolated fixture
  only adds sprite-preload actors; production map hashes remain unchanged. Native combat captures also verify the palm flash, damage response, fragment collapse and ordinary loot-bag
  transition. Run records are retained alongside the captures. These are visual checks, not performance benchmarks.

The refreshed recordings, moving-shoulder close-ups and `review/shoulder_motion_v3/ingame/` captures use the current
revision. The older `review/shoulders/` evidence describes the superseded first repair. Earlier overview sheets and the original `review/ingame/` captures remain historical comparisons.

Android and Vulkan were not built or tested. The user approved the current shoulder revision on 2026-10-18.

## Working files

`creature_3d_progress.json` is the canonical state. `work/rig_uv.blend`, `rig_complete.blend`, `animated.blend`
retain fitted construction stages; the packed exported `.blend` is the editable delivery. Scripts in `scripts/`
cover source inspection, fitting, texture composition, motion, export, verification and installation.
Run project mutations through `tools/creature_workspace.py` with an acquired lease, and Blender through
`tools/run_creature_blender.sh`. `build.py` assembles the selected animated scene, prepares runtime coordinates,
generates LODs, applies variants/material merging, corrects LOD normals, validates and refreshes the viewer.

To reproduce the shoulder correction, run `scripts/repair_shoulders.py` from its recorded pre-correction
checkpoint, then `rubble.py`, `animate.py` and `build.py`. The build runs `shoulder_audit.py` before export.
The repair preserves original surface UVs and assigns existing stone texture samples to the new closed surfaces.
