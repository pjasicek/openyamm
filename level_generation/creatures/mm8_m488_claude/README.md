# MM8 Minotaur Peasant — m488

Production is technically complete. The rigged model is installed for all three native tiers. Meshy spend: **30 / 100 credits**.
The user's exception applies only to this run: front and/or three-quarter HD masters suffice, with extra head
views optional. Both Meshy texture jobs used the selected front references. Hidden anatomy is an interpretation.
Technical production is complete. The user accepted this delivered revision on 2026-10-18: “good accepted”.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m488_claude/review/viewer/) ·
[Portable GLB](export/mm8_m488.glb) · [Textured Blender master](work/m488_textured_master.blend) ·
[Canonical progress](creature_3d_progress.json)

![Final front](review/shots/final_front.png)

## Selected production assets

- Editable geometry, rig, UVs and actions: [uv_master.blend](work/uv_master.blend).
- Installed authoring source: `assets_source/worlds/mm8/models/mm8_m488.glb`.
- Cooked model and textures: `assets_dev/worlds/mm8/models/mm8_m488.glb` and its external `.oytex` maps.
- Runtime bindings: descriptors 67–69 in `assets_dev/worlds/mm8/models/actors.yml`;
  variants `m488_a`, `m488_b`, `m488_c` reproduce the native green, purple and red wraps.
- Four colour LODs and four shadow LODs: **9,486 / 4,740 / 2,369 / 1,183 triangles**.
  Each colour LOD has one merged primitive. The rig has 108 bones and at most four normalized influences.
- Four shared 2080×1024 atlases contain 1K body and head regions separated by a 32-pixel gutter:
  base colour, normal, specular/roughness/metallic and palette-region mask. Metallic is zero;
  fur and cloth remain matte. Runtime normals use glTF +Y. Cloth alone changes between tiers.

Native identity is bitmap family m488, sprite groups m489/m490/m491 and palettes 489–491.
Short horns, bovine ears, black cloven hooves, tan wrist bands and rope belt follow the native references.
No weapon, exposed tail or cast role is required. The independent source-frame rig does not copy the MM6
Minotaur's unresolved rig or weights; its anatomy and the Ogre's accepted movement were reference evidence.

## Motion and modelling

| Clip | Seconds | Adaptation |
| --- | ---: | --- |
| Standing | 2 | Relaxed local source motion |
| Walking | 1 | Measured stride 2.1503 m |
| Running | 0.7333 | Measured stride 1.9944 m |
| Attack | 1.9 | Forward unarmed punch; impact at 1.0 s |
| Hit | 0.5 | Unarmed recoil |
| Fidget | 3.9 | Relaxed talk gesture |
| Death | 1.5 | Unarmed fall with filtered neck/head locals |
| Dead | 1 | Held final fall pose |

Professional local clips were selected and reviewed before modelling. Native Attack/Attack2 alias Walking;
these are adapted 3D actions, not reconstructions of unused A bitmap frames. Native movement speeds and AI
remain unchanged. Standing height is calibrated to 206.399 game units with scale 97.8354446. The run threshold
is 234.805 game units/s, so tier A walks and tiers B/C run at full speed. Collision remains radius 60, height 160.

The wrap is separated from the body, hidden pelvis/thighs are closed, and five digits are fitted per hand.
Forty-eight garment surface controls clear the moving legs while the waist follows the skin. All eight clips
passed half-frame body/garment contact checks. Arm edge p99 peaks at 1.825×; the hand gate peaks at 3.51×
against the approximate 4.5× limit. Continuous wrist roll is shared between forearm and hand, each below 87.33°;
wrist swing stays below 58.01°. Finger closure is fitted to the bovine hand using the source grip axis and palm
normal, rather than claiming identical mannequin finger directions. Running hem stretch peaks at 4.82× and
was reviewed separately from the arm/hand gates. Floor checks remain within 2 cm, including the fall.

The final fall correction smooths neck/head local rotations without changing endpoints or duration.
The largest sampled head step falls from 56.2° to 19.8°. Reimported GLB surface error is below 0.027 mm
across all eight clips. See [motion measurements](review/animation/measurements.json),
[hand adaptation](review/hand_adaptation.json), [wrist gates](review/wrist_gates.json),
[fall correction log](review/death_neck_finish.log) and [export parity](work/export_parity.json).

Meshy omitted four small body faces from its UV return. Original geometry was preserved and their UVs resolved
from exact surviving corners; coincident-face reuse is recorded in the [UV transfer receipt](review/uv_transfer_UVMap.json).
The rear upper-body markings were corrected against the native black mantle. A local neck blend joins body
and head paint; a global brightness ratio was deliberately not applied to heterogeneous black-and-white fur.

## Validation and review

The ordinary development build passed. The focused Minotaur case and **all 51 MM8 actor regression cases**
passed; [logs](review/regression/mm8-actors.log) include binding, roles and unchanged simulation checks.
[Static validation](review/static_audit.json) confirms valid UV triangles, normalized skinning, all roles and LODs,
and unchanged hashes for all 155 original sprite inputs. The browser passed 24 tier/clip switches without errors;
all eight actions were reviewed at normal and half speed, with retained [playback evidence](review/playback/playback.json).

Native indoor/outdoor comparisons use isolated copies of MM6 `6d19` and `oute3`, preloading the MM8 sprite family.
Original maps and behavior files are unchanged. Captures show native/model scale, palettes, gait, recoil, collapse,
satchel replacement and forced LOD3. The attack presentation fixture uses a fixed staged actor and a temporary
script because the native peasant flees; production AI is not altered. Final delivery details and exact asset hashes
are in [delivery checks](review/delivery_checks.json).

Native captures use the pinned ordinary OpenGL build on the desktop NVIDIA GPU. They are visual checks,
not performance measurements. Android and Vulkan were not tested.

## Provenance and reproduction

[Native views](reference/native_contact.png) · [Native palettes](reference/native_tiers.png) ·
[Native timing](reference/native_summary.json) · [Selected motions](review/motion/selection.json) ·
[Front master](references_hd/01_front.png) · [Head front](references_head/01_front.png)

The canonical progress file preserves the reference waiver, generation job IDs, spending and selected revisions.
Use the project workspace lease and guarded Blender/Meshy wrappers for future edits. `scripts/build_runtime.sh`
records the export sequence from the selected UV master; run its Blender wrapper directly with the approved
permissions if a sandboxed nested queue cannot start Blender. Viewer tier GLBs bake the same native palette ramps
for portable review; the installed model uses shared maps and runtime variants.
