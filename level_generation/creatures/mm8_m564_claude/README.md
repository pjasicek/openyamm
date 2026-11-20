# MM8 Gorgon — m564

Production of the armoured bull (merged monster IDs 124–126), following the Claude quadruped / rat workflow.
The requested priorities are a compact body, clear cloven-hoof contacts, sculptural armour and a heavy bovine gait.
User artistic acceptance is not yet recorded.

## Selected deliverables

- `gorgon_master.blend`: editable 26-bone rig, eight actions, packed textures in glTF normal-map convention.
- `export/mm8_m564.glb`: portable runtime source, three native palette variants, four colour and shadow LODs.
- `review/viewer/`: shared review viewer with all tiers, native action references, exact-time feedback and playback.
- `creature_3d_progress.json`: canonical selections, source hashes, service receipts, corrections and delivery checks.

Source install: `assets_source/worlds/mm8/models/mm8_m564.glb`. Cooked runtime:
`assets_dev/worlds/mm8/models/mm8_m564.glb`, bound by the three Gorgon entries in the same directory's `actors.yml`.
Other creature entries belong to their respective sessions.

## Art and geometry

The 155 original native BMP frames were verified against the packed source inventory. Five original transparent
HD masters in `references_hd/` were generated from native references, then reviewed for anatomy and material identity.
The selected mesh is `smart_topology_v2` (Meshy T2.5): T2's first result softened the armour too much.
The local reduction retained 12,808 triangles; the next 11,527-triangle candidate exceeded the surface-error gate.
Four zero-area faces were removed at export, leaving **12,804 / 6,402 / 3,201 / 1,600 triangles** across colour LODs.
Every vertex has at most four normalized joint influences. Head, horns and hoof tips retain rigid ownership.

The body uses one 2K base-colour atlas plus 1K normal, metal/roughness and RGBA region-mask maps. The small bovine
head receives twice the body's UV density instead of a separate humanoid face set. Retexture preserved UVs and
normalized the returned static geometry uniformly; only maps were applied to our animated master. The service
omitted four zero-area faces and one tiny chart (0.003% surface area). That chart was filled from its nearest surface
colour/roughness with a neutral normal. Original downloads remain unchanged.

Armour plates, copper ridge/muzzle, horns/hooves and eyes are four recolour regions. Each tier's ramps are measured
independently from original palettes 565, 566 and 567. Runtime tiers share every texture. Viewer-only copies bake the
same ramps because three.js does not implement the engine material extras.

The armour uses 0.72 metallic for its oxidised surface. Horns and eyes remain dielectric. The current engine contract
uses metal/roughness red for a per-texel specular mask; the original baked AO is retained separately and also contributes
a mild crevice grade. `prepare_actor_glb.py` verified and converted Meshy's normal-map Y convention.

## Motion and native timing

| Role | Clip seconds | Behaviour |
| --- | ---: | --- |
| Standing | 2.0 | Grounded breathing and restrained head/tail motion |
| Walking | 1.0 | Four-beat lateral sequence, 62% support, 0.48 model-unit stride |
| Running | 0.75 | Heavier diagonal gait, 0.60 model-unit stride |
| Attack | 1.375 | Rear, drive the horns down at 0.875 s, recover |
| Hit | 0.625 | Native-duration recoil |
| Fidget | 0.625 | Native-duration head movement |
| Death | 0.75 | Native-inspired side collapse |
| Dead | 1.0 | Hold the final collapse pose |

This is locally authored 3D motion informed by native actions, not a claim of exact frame reconstruction.
Attack impact remains at the native 0.875-second gameplay event; recovery plays as follow-through. Only the neck/head
participate in upper-body follow-through while travelling, preserving hoof contacts. No spell or extra visual effect
was invented for the non-caster.

Scale is 100 native silhouette pixels × 1.399994 frame scale ÷ 0.43603515625 rest height = 321.07365196. All three
native tier scales match. Gait phase follows actual travel through matching binding strides; the initial 0.28 stride
was lengthened after runtime calibration showed it would cycle too quickly at native movement speeds.
The final gait also articulates the pastern joints toward the moving hips while preserving flat hoof contacts;
this keeps the body higher than the rejected long-stride pose. All tiers bind their measured scale explicitly.
A cross-world test exposed that referencing another tier's standing sprite added an unnecessary load dependency.

## Checks and review

- `work/dense_motion_checks.json`: half-frame samples of all clips, normalized skin, evaluated floor clearance and
  planted-hoof drift with forward movement included. Worst floor excursion is about 1.1 mm in model units; worst
  half-frame planted drift is 1.595 mm (about 0.51 game units at installed scale).
- `work/export_parity.json`: final GLB reimport against the packed master, five samples per clip. Keyed samples use
  a 0.02 mm tolerance; fractional samples allow 1 mm for Blender Bezier versus glTF linear interpolation. Maximum measured difference is 0.661 mm.
- `export/lods.json`: actual LOD counts and preservation of full-detail rig, clips and source samples.
- Winding check: no inverted closed parts. Head-material merge: one material already, no extra head draw.
- Viewer: all 24 tier/clip combinations load without browser errors. Recorded normal/half-speed playback is under
  `review/playback/`; direct comparisons and exact-time screenshots are in `review/shots/`.
  Agent review inspected the timed playback frames for every clip at both speeds, plus dense numerical samples;
  videos are retained for continuous human playback review.
- Focused engine regression: `mm8_gorgon_actor_models_keep_native_tiers_and_simulation` validates shared instances,
  hoof rig, eight actions and unchanged native simulation while presentation states change.
- Native GPU captures and sprite comparisons: `review/ingame/`, with isolated run records and original logs.

The source/rig, source native frames, HD references, rejected geometry pilot and short-stride checkpoint remain in the
project for reproducibility. No raw animation-library clips or external rig jobs were needed. Meshy usage: **20 credits**
(two 5-credit geometry jobs and one 10-credit retexture).

Use `tools/run_creature_review.py` for browser review and `tools/run_creature_blender.sh` for Blender scripts; writes
require the active creature lease. The viewer wrapper has one reusable saved approval across creature sessions.

## Native capture results and limits

All seven retained runs completed with exit 0 on the desktop OpenGL 3.3 / NVIDIA path. Captures compare the three
native sprite tiers and models in MM6 outdoor `oute3.odm` and indoor `6d19.blv`, using the MM8 bindings explicitly.
The indoor test asset copy declares three distant Gorgons so native sprite preload can serve debug summons.
The original scene hash remains unchanged. Full-speed moving comparisons and 0.05-speed forced LOD 0–3 captures
are separate; `render freeze` freezes culling, not actors, so the first moving LOD sequence is not used as evidence.

Combat images show the horn rear/strike, damage recoil and grounded side collapse. The final `dead.png` shows the
existing shared loot-satchel transition; the held corpse pose is also verified in the viewer and export check.
The focused regression passes with the final installed model. The normal desktop build passed before the final
asset-only gait revision; no engine rebuild was necessary for that revision.

- [Outdoor LODs](review/ingame/outdoor_lods.jpg), [indoor LODs](review/ingame/indoor_lods.jpg),
  [combat sequence](review/ingame/combat_sequence.jpg).
- [Normal walk video](review/playback/Walking-1.webm), [half-speed walk](review/playback/Walking-0.5.webm).
- [Delivery hashes and checks](review/delivery_checks.json).

Android and Vulkan were not run. These are visual/functional checks, not GPU performance measurements.
User artistic acceptance remains unrecorded; all selected assets and comparison evidence are available for review.
