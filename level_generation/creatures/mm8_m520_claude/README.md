# MM8 Cyclops — m520

> **Installed model reduced (2026-10-18):** the installed runtime is now the triangle reduction from [`../mm8_m520_reduce_claude/`](../mm8_m520_reduce_claude/README.md) (LOD0 17,917 -> 11,645). This project's own exports and master remain the unreduced production; the rollback source is `../mm8_m520_reduce_claude/work/mm8_m520_source_pre_reduce.glb`.


Complete Claude-playbook production, installed on 2026-10-18. The Cyclops, Cyclops Hunter and Cyclops Warrior
share a fitted rig and eight actions, with native brown/blue/red trim. Dedicated face references and a separate
head modelling pass preserve the single green eye, heavy brow, broad jaw, bald crown and dark side/back hair.
Technical checks and agent visual review are complete; user artistic acceptance remains separate.

## Review and deliverables

- [Interactive viewer](http://127.0.0.1:8912/level_generation/creatures/mm8_m520_claude/review/viewer/): revision
  `m520_review_01`, all three tiers and eight clips, native reference frames and playback controls.
- [Face close-up](review/shots/final_face.png), [profile](review/shots/final_profile.png),
  [two-hand grip](review/shots/final_grip.png), [overhead hold](review/shots/final_overhead.png).
- [Outdoor comparison](review/ingame/outdoor_comparison.jpg), [indoor comparison](review/ingame/indoor_comparison.jpg),
  [outdoor combat](review/ingame/outdoor_combat.jpg), [indoor combat](review/ingame/indoor_combat.jpg).
- Editable packed master: [mm8_m520.blend](export/mm8_m520.blend).
- Portable body [mm8_m520.glb](export/mm8_m520.glb) and attachment [mm8_m520_boulder.glb](export/mm8_m520_boulder.glb),
  with embedded maps. Composed source PBR maps and palette ramps are in `textures/`.
- [Canonical state](creature_3d_progress.json) retains selected inputs, hashes, corrections, Meshy receipts and
  runtime installation. Rejected candidates remain available as provenance, not selected production inputs.

## Identity, scale and motion

`native/inventory.json` records 162 original BMP hashes, 120 used frames, SFT timing, five view groups and
palettes 521/522/523. Monster IDs 91–93 bind Cyclops A/B/C. The original stand is 203 pixels at SFT scale 1.5:
304.5 game units. The exported standing height is 2.388724 m and the binding scale is 127.473914.
Original sprites and monster gameplay tables are unchanged.

Five selected full-body views are in `references_hd/`; four dedicated facial views in `references_head/`.
The native outfit includes three round neck discs, wrist wraps, a right upper-arm band, belt/loincloth and
wrapped fur boots. Region ramps change trim while retaining skin, hair and neutral equipment colours.

The source-frame rig has 57 bones including four twist helpers and the temporary boulder node. Local library
clips provide Standing, Walking, Running, Attack, Hit, Death, Dead and Fidget. The throw is fitted to the native
both-hand pickup, chest hold and overhead release. The stone is visible from 0.28 seconds until the 1.0-second
release, then disappears for the existing gameplay projectile. Walking/running strides are 2.644152/2.623366 m.
No paid animation was needed. Clips retain their authored speeds; attack impact and native gameplay timing
remain separate. The final skin uses at most eight influences per vertex; limiting tiny weights removed at most
0.702% before renormalization.

## Mesh, materials and LOD decisions

| Mesh | LOD0 | LOD1 | LOD2 | LOD3 |
| --- | ---: | ---: | ---: | ---: |
| Body, including head | 17,917 | 8,903 | 3,998 | 2,223 |
| Temporary boulder | 522 | 260 | 114 | 66 |

The 8,093-triangle near head keeps the detailed eye, lips and brow. Distant material budgets reduce the head
more strongly to retain the large shoulder and boot silhouettes. Hands, stone contact patches and the open
loincloth/hip boundary have protected geometry. The combined last LOD is 12.4% of LOD0; `gates.json` records a
13% ceiling instead of the usual 10% to retain these contacts. Colour and shadow LODs use the same animation;
shadow insets preserve soles, hands and the garment boundary. Reduced soles stay inside the original footprint.

The head and body merge into one 2080×1024 runtime atlas; the stone uses 512-pixel maps. Material masks keep
skin/leather rough, the discs moderately reflective and the eye wet. The UV report is `work/uv_gate.json`.
The body has no collapsed or overlapping UV triangles; head overlap is 0.001408 of measured coverage.

## Validation evidence

- [Final shared gates](work/gates_release/gates.md): **6,086 PASS, 140 INFO, 136 N/A, zero failures** across
  every clip and all colour/shadow LODs. The report is bound to the exported GLB hash.
- [Open cloth check](work/cloth_surface_gates.json): **64 PASS**, maximum measured outward crossing 0 mm,
  sampled at 48 Hz. This fused open loincloth is checked as outward panels with the playbook's 45-degree
  proximity cone and same-face covered-side rest baseline; it is not treated as a closed skirt volume.
- Viewer loading/switching passed all 24 tier/clip combinations. Sixteen normal/half-speed recordings and
  their sampled frames are in `review/playback/`; all eight frame sequences were visually inspected, including
  in-between grip, floor contact, fall and held-dead poses. Close head, hand and overhead views were inspected.
- Ordinary development build passed. Cyclops tier/attachment/release regression passed on the final installed
  export; MM6 Ogre and MM8 Troll regressions passed. Logs are in `review/validation/`.
- The shared LOD fixture passed protected-contact position/skin, UV-seam closure, influence-limit and
  per-material budget checks. Defaults for other callers are unchanged.
- Native desktop captures used NVIDIA (`vendor=0x10de`), OpenGL 3.3 and Wayland. Matching model/sprite cameras
  cover outdoor `oute3.odm` and indoor `6d19.blv`, three tiers and forced LOD0–3. Both combat runs show lift,
  release, recovery, fall and the existing loot satchel. Run records, logs, tours and full PNGs are preserved
  under `review/ingame/`. These are visual checks, not a performance benchmark.

The indoor fixture only adds distant immobile Cyclops actors to preload native sprite families for debug
summons. Its scene copy breaks the hard link before writing; the production map hash is preserved in
`review/ingame/indoor_fixture.json`.

Runtime/source models are installed under `assets_dev/worlds/mm8/models/` and `assets_source/worlds/mm8/models/`.
The three bindings are in `assets_dev/worlds/mm8/models/actors.yml`; runtime maps use the existing desktop cook.
An existing shared-manifest omission blocked model validation: Skeleton Archer A/B/C had Walking but no Running
clip or required run mapping. Their explicit `run: Walking` and matching walk stride were added, following the
existing shared-manifest pattern. No Skeleton Archer art was changed.

Android and Vulkan were not tested. User artistic approval is not implied by the completed technical review.

## Reproduction

Project mutations require a fresh ownership lease from `tools/creature_workspace.py`; use the Blender/review
wrappers with its token. All **100/100 Meshy credits** were consumed and downloaded; no further paid jobs are
needed. Keep the selected geometry and local motion sources recorded in the canonical state.

1. `scripts/finish_motion.py`: source-frame motions, fitted soles, two-hand IK/finger contact and twist baking.
2. `scripts/export_review.py`: final weights, UV/material export, packed master, height/stride calibration.
3. `tools/prepare_actor_glb.py`: prepare `export/mm8_m520_lod0.glb` as `export/mm8_m520_runtime_lod0.glb`.
4. `scripts/build_lods.py` in Blender, then `scripts/finish_runtime.py` in ordinary Python: contact-preserving
   LODs, soles, shadow insets, region variants, attachment split, head atlas and browser tier exports.
5. Shared `claude_shared/gates/run_gates.sh` with `gates.json`, plus `scripts/cloth_surface_gates.py` in Blender.
   Run the existing viewer checks/playback and `tools/install_model.py` for each changed portable GLB.
6. Repeat affected runtime regressions and native visual captures. Refresh the indoor fixture after installation:
   its hard-linked models otherwise retain the old file when the cooker atomically replaces a runtime GLB.

`boulder_mesh.py` repairs the generated stone to a closed outward surface. Finger fitting uses volume intersection
against that irregular surface. `fit_skin.py` blends phalanges; `fit_shoulder_weights.py` smooths shoulder weights
and enforces the engine's eight-influence limit. Temporary diagnostic scripts are archived separately from these
selected production steps.
