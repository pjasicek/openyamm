# MM6 Ghost (`gst`)

Revision **v3**, updated 2026-10-13; installed and technically verified. User accepted the complete delivery, including the v3 robe colours, on 2026-10-13.

[Interactive review](http://192.168.1.130:8912/level_generation/creatures/mm6_gst_codex/review/viewer/?v=3)
includes Ghost, Evil Spirit and Specter, eight clips, slow playback and original sprite anchors.
The canonical resume record is [creature_3d_progress.json](creature_3d_progress.json).

## Selected delivery

- [Editable Blender source](export/mm6_gst.blend): packed textures, 77-bone rig and eight actions.
- [Portable runtime package](export/mm6_gst.glb): 17,143 triangles at LOD0, reduced 34.4% from 26,129.
  Colour/shadow LODs have 17,143 / 8,571 / 3,075 / 1,008 triangles; skinning retains eight influences.
- Body and head each retain their own 1024-square base colour, normal, ORM and region-mask maps in
  [textures](textures/). Runtime packing makes four 2080x1024 atlases without reducing texel density,
  with one primitive per colour LOD and three palette materials.
- Runtime/source installs are `assets_dev/worlds/mm6/models/mm6_gst.glb` and
  `assets_source/worlds/mm6/models/mm6_gst.glb`. Bindings are BGhost A/B/C, descriptors 547/548/549.

| Clip | Seconds | Behaviour |
| --- | ---: | --- |
| Standing | 3 | Floating idle and cloth movement |
| Walking | 1.4 | Gentle hovering travel |
| Running | 1 | Faster hovering travel |
| Attack | 1.4 | Rearward/rightward windup through frame 24; forward, left-down swipe through frame 56; settle by frame 84 |
| Hit | 0.75 | Prominent recoil based on the owned GetHitF2 upper-body source |
| Fidget | 3 | Larger shoulder, hand and shroud movement |
| Death | 1.8 | Cloth collapse into an upright-skull heap |
| Dead | 1 | Held grounded corpse |

All clips are baked at 60 Hz. The native creature has melee Dark damage; no weapon or separate cast
animation is required. The binding's `cast: Attack` and ranged aliases satisfy the existing binding
schema and do not add casting behaviour. Melee impact is at the measured claw-speed peak, 0.6375 s. Standing-based scale is
75.7268261, yaw is -1.570796327 radians, and the runtime stride is 2.05 before the existing 1.55 run
multiplier. Eye and palm sockets and neck/head look bones are included.

The original Ghost sprites carry the `Lit` flag. Runtime materials therefore use
`KHR_materials_unlit`, with subtle baked top-light and short-range AO preserving cloth/skull volume.
Normal/ORM maps and the original PBR nodes remain in the editable source, but dynamic PBR lighting
is intentionally bypassed for the native appearance. Existing eye FX turn off for Dying/Dead.

## Sources and resolved findings

Native frames, palette measurements and motion analysis are recorded in
[source/ANIMATION_STUDY.md](source/ANIMATION_STUDY.md). Selected body/head image references are in
[references_hd](references_hd/) and [references_head](references_head/). Hidden construction is inferred.
Meshy receipts and downloaded outputs remain in the canonical progress record: five completed jobs,
40 credits spent, no outstanding job. Selected textures use body_retexture_v1 and head_retexture_v2;
head_retexture_v1 was rejected for UV overlap. No raw animation-library clip is part of the export.

The final mesh has a dedicated skull, five skeletal digits per hand, a shorter hood/train, no legs or
feet, continuous cloth-panel weights and independent sleeve deformation. Fixed-length arm motion and
local cloth collapse avoid stretching hands during death. The selected reduction is
[review/reduction_uv/step_04.blend](review/reduction_uv/step_04.blend), documented in
[review/reduction/selection.json](review/reduction/selection.json). Earlier pilot, prone-death,
UV and reduction checkpoints are retained as history and must not replace the selected master.

The viewer uses the existing eight-influence shader adaptation so cloth deformation matches the
engine. A four-influence browser preview previously produced false spikes; final browser checks use
all eight influences. Tabard region masking and native light treatment were visually corrected before
recording the final viewer hashes.

## Feedback revision v2

The user's six annotated images are preserved under [review/feedback_v2](review/feedback_v2/).
Eye masks now cover the complete eye surfaces instead of selecting isolated green texels; constant native
palette colours remove pale centres and patchy highlights in all three tiers. No extra texture size or polygons.

Attack frames 0–24 lean behind-right; the torso and claw drive forward and left-down through frame 56.
The support hand crosses the chest with its palm aligned to the forearm. Both visible wrist bends stay below
45.13 degrees, and lower sleeves follow their joined robe seams during the stronger transfer. Recovery lasts
through frame 84 (1.4 s), avoiding a rushed return. The three binding impact markers use the measured claw-speed
peak of 0.6375 s; native gameplay attack timing is unchanged.

[Attack poses](review/feedback_v2/gst-v2-attack-contact.jpg),
[normal/slow playback](review/feedback_v2/playback/Attack.jpg) and
[native game captures](review/feedback_v2/gst-v2-game-contact.jpg) show the selected revision.
[Attack measurements](review/feedback_v2/attack_audit.json) and
[preservation checks](review/feedback_v2/preservation.json) record the correction. All mesh/LOD/UV/skin accessors
and the other seven clips' samples are exactly unchanged. Export parity and the full dense deformation audit
were rerun; viewer checks cover 24 tier/clip combinations and all eight clips at normal and quarter speed.
The focused Ghost actor regression passes. The two new native runs cover indoor/outdoor tiers, combat, hit
and death; full captures and run logs are in [revision game evidence](review/feedback_v2/game/).

The prior complete-production evidence below remains the baseline for unchanged inputs. The wider MM6 suite
was not rerun for this asset-only correction; its three known unrelated failures remain recorded. No new
Meshy job or engine build was needed. The original delivery is preserved in [review/revisions/v1](review/revisions/v1/).

## Palette revision v3

The user requested clearer blue and red robe colours after accepting the v2 eyes and motion.
Evil Spirit now uses a visible blue tabard, and Specter a deep crimson tabard. Lifted midtones retain
folds, holes and worn cloth detail. This user-directed saturation override affects only the B/C cloth
ramps; the original Ghost, white shroud, bone and eye regions retain their previous colours.
All tiers continue sharing the same textures and region masks.

[Variant comparison](review/palettes_v3/variants.jpg) and
[indoor](review/palettes_v3/game/indoor/tiers.png) /
[outdoor](review/palettes_v3/game/outdoor/tiers.png) native stills show the installed result.
The [preservation check](review/palettes_v3/preservation.json) confirms that the final GLB binary payload
is byte-identical to v2: geometry, UVs, skinning, all eight clips and embedded maps are unchanged.
Only the two cloth ramp arrays differ in its material JSON. Editable Blender files and standalone maps
also retain their hashes.

The [viewer check](review/palettes_v3/viewer.json) passed all 24 tier/clip combinations without errors;
[delivery validation](review/palettes_v3/delivery.json) passed against both installed packages.
[Native checks](review/palettes_v3/native_checks.json) completed indoors and outdoors on NVIDIA/OpenGL.
An initial EGL context startup failure occurred before asset loading; an unchanged retry passed.
No Meshy credits, rebuild or full motion/regression rerun was needed for this palette-only revision.
The accepted v2 baseline is preserved in [review/revisions/v2](review/revisions/v2/).

## Validation and evidence

- Ordinary desktop build passed: [build log](review/checks/build.log). No Vulkan build was run.
- Ghost actor regression: 1 passed, 0 failed. Wider MM6 actor suite: 52 passed, 3 failed.
  Mage, guard and ooze failures were already present in the earlier PeasantF2 run; they are unrelated
  to this asset. See [current results](review/checks/mm6_actor_regressions.log) and
  [prior baseline](review/checks/prior_mm6_actor_regressions.log).
- [Delivery checks](review/checks/delivery.json): final source/runtime hashes, LODs, 77 bones,
  eight clips, three variants and four embedded maps. Installation preserves every animation sample.
- [UV check](work/uv_gate.json): zero overlapping pixels on both 1K maps; measured regions exceed
  2 texels/cm. [Dense animation audit](review/animation_dense_reduced_audit.json): 120 Hz, minimum
  ground clearance 7.73 mm, maximum hand-edge stretch 1.2292 and maximum half-frame rotation 15.562 degrees.
- [Export reimport parity](review/export_parity.json): maximum surface deviation 0.059 mm and socket
  deviation 0.0024 mm across all eight clips.
- [Viewer check](review/checks/viewer.json): 24 tier/clip combinations, no console errors or failures.
  [Playback check](review/checks/playback.json) covers eight clips at 1x and 0.25x; its model hashes
  match their recorded revision manifest. [Loop check](review/checks/loops.json) confirms all four loop wraps.
  [Detail check](review/checks/details.json) covers back/side, skull, hands, attack and corpse views.
- [Playback evidence](review/playback/) contains 160 actual browser captures and eight contact sheets.
  [Final stills](review/final/) retain all three palettes and close-up views.
- [Same-camera game comparison](review/game/comparison.jpg) and 140 native captures under
  [review/game](review/game/) cover indoor/outdoor tier appearance, hovering, hit, death and corpse.
  Model runs also capture live combat. Logs identify OpenGL 3.3, NVIDIA vendor 0x10de and Wayland.
  The second hostile summon in the sprite-only runs was invisible, so those later sprite images do
  not validate native combat; the preserved original attack frames provide the motion reference.

## Resume/reproduce

Acquire a fresh `mm6:gst` lease with `tools/creature_workspace.py` before changing this project.
Use `tools/run_creature_blender.sh --token TOKEN <script>` for Blender scripts and the workspace
`run` guard for other writes. Do not reuse the released delivery token or resubmit completed Meshy jobs.

`work/textured_master.blend` is the selected animated mesh; `work/textured_master_full.blend` is the
full-resolution UV/master backup. `work/anim_v1.blend` and `work/rig_v1.blend` retain motion/rig sources.
For a necessary revision, use `refresh_actions.py` to update masters and `select_reduction.py` to select
the UV-safe reduction; `restore_actions.py` is historical and would restore an obsolete reduction.

The final packaging sequence is `compose_ghost.py`, `export_ghost.py`, the shared
`prepare_actor_glb.py` handoff, `viewer_tiers.py`, `update_viewer_manifest.py`, `build_lods.py` and
`finish_runtime.py`. Existing AO/shade data is retained; `bake_native_shade.py` and
`read_native_shade.py` reproduce it if geometry changes. `pack_editable.py`, called by export,
retains PBR nodes while selecting the native-lit output in the editable file.

For palette-only changes, reuse the current exported geometry and run only 
`compose_ghost.py`, `viewer_tiers.py`, `update_viewer_manifest.py` and `finish_runtime.py`.
The authoritative variant colours are `textures/gst_ramps.json`, authored by `compose_ghost.py`.

Reinstall the final GLB through `tools/install_model.py`; do not rerun `install_ghost.py`, whose
one-time binding append has already completed. Then rerun affected UV/animation/export checks,
`validate_delivery.py`, the viewer playback checks and relevant native captures.

No commit was made. Unrelated actors, gameplay and renderer behaviour were not changed.
