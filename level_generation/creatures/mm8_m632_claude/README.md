# MM8 Dark Dwarf — m632

Created and installed through the shared Claude humanoid playbook. All three tiers, eight clips, the fitted crossbow,
textures and four detail levels are complete. User artistic acceptance is not yet recorded.

The [faster aim segment](review/fast_aim/README.md) is installed as `m632_v5_fast_aim`: old attack frames 44–60
play at 2.5x in the viewer and 2.1x after native timing synchronization in game. Release is now at clip time
1.05 seconds, with a 1.55-second total clip. It retains the earlier raise and feet corrections. Refresh the viewer.

[Open the animation review](http://localhost:8909/level_generation/creatures/mm8_m632_claude/review/viewer/)
· [Outdoor tiers](review/runtime/outdoor/model/outdoor_model_tiers.png)
· [Indoor tiers](review/runtime/indoor/model/indoor_model_tiers.png)
· [Native outdoor comparison](review/runtime/outdoor/sprite/outdoor_sprite_tiers.png)
· [Fall and corpse](review/native_death_sheet.jpg)

## Selected delivery

- Editable, packed master: [export/mm8_m632.blend](export/mm8_m632.blend).
- Body with native palette variants and colour/shadow LODs: [export/mm8_m632.glb](export/mm8_m632.glb).
- Rigid crossbow attachment: [export/mm8_m632_crossbow.glb](export/mm8_m632_crossbow.glb).
- Combined full-detail portable model: [export/mm8_m632_runtime_lod0.glb](export/mm8_m632_runtime_lod0.glb).
- Three portable, colour-baked review models: `review/viewer/mm8_m632_a.glb`, `_b.glb`, `_c.glb`.
- Canonical progress, selected hashes and paid receipts: [creature_3d_progress.json](creature_3d_progress.json).

The installed sources are `assets_source/worlds/mm8/models/mm8_m632{,_crossbow}.glb`. The cooker produced the
matching runtime GLBs and seven desktop textures under `assets_dev/worlds/mm8/models/`.
Bindings in `assets_dev/worlds/mm8/models/actors.yml` target descriptors Dark Dwarf A/B/C (175–177).
Native gameplay remains authoritative, including Missile=0 despite the visual crossbow.

## Native identity and materials

Native MM8 BMPs, SFT records and ACT palettes 633/634/635 are authoritative. The BMP embedded palette is a
placeholder. MM6's dwarf informed proportions/weighting only; it did not replace the Dark Dwarf design.

The model retains the short broad body, two helmet horns, spiked iron/bronze shoulders, dark skin, white beard,
single rear braid, round buckle, mail tabs and heavy boots. Native regions provide green/blue/red bracers,
silver/gold mail and purple/burgundy cloth. Head and hair colours are shared.

Selected references are in `references_hd/` and `references_head/`; the native inventory and sheets are in
`references_native/`. Meshy's body, head and crossbow texture returns are retained unchanged in `meshy/`.
Verified face/corner correspondence transferred the body and prop UVs; the head retained its unwrap.
One redundant overlapping skirt triangle discarded by Meshy was removed after proving its covering neighbour
was within 0.034 mm. Vertex positions, weights and the paid head UV layout were preserved.

Body/head maps are 1024² and the crossbow maps 512². Runtime body/head maps form a 2080×1024 atlas with a gutter.
Material ownership supplies binary metallic, roughness and specular masks. Normal-map green channels were corrected
from measured DirectX handedness. The returned brown rear hair was graded white. Dark native iron/bronze albedo
intentionally remains below bright clean-metal reference values; its readability was checked in the game.

## Rig, timing and size

59 bones; up to eight influences, supported by the current engine. Limiting to four moved late-death skin by
16.2 mm. Eight influences changed the dense sampled surfaces by at most 0.183 mm.
The review viewer reuses the existing eight-influence shader/weight restoration from the Lizard Archer viewer.

Fitted source frames, connected finger weights, forearm twist helpers and rigid pauldron helpers preserve the
short anatomy. The sleeve repair removes chest weights that previously stretched the inner sleeve during death.
The crossbow has separate trigger and angled support grips fitted to the actual thick hands.

| Clip | Seconds | Source and adaptation |
| --- | ---: | --- |
| Standing | 2.000 | Authored upright breathing, one-hand low carry |
| Walking | 0.800 | Local two-hand crossbow walk, refitted to low carry |
| Running | 0.733 | Mixamo Standard Run, fitted short legs and carried weapon |
| Attack | 1.550 | Native raise/aim/recoil; clip release at 1.050 s, then 0.5 s follow-through |
| Hit | 0.600 | Local front hit, within the native 0.625 s window |
| Death | 1.500 | Local crossbow death; turn and fall, hand releases before weapon drops clear |
| Dead | 1.000 | Exact Death endpoint held |
| Fidget | 1.250 | Native left-hand chest/beard gesture |

Native upright height is 166 pixels at SFT scale 1 for every tier. Measured model height is 1.400624287 m,
giving scale 118.5185788543. Walking/running strides are 0.632/2.343 m. Neck/head look limits are 25° yaw and
15° pitch. Attack and Attack2 use the same authored clip. Their 1.05 s clip marker is fitted to the unchanged
1.25 s native gameplay event; the fast aim segment remains 2.1x faster after this fit.

| Detail level | Body triangles | Crossbow triangles | Total |
| --- | ---: | ---: | ---: |
| 0 | 9,579 | 556 | 10,135 |
| 1 | 4,787 | 278 | 5,065 |
| 2 | 2,365 | 135 | 2,500 |
| 3 | 1,169 | 59 | 1,228 |

Horns, sole ends and weapon tips are protected during reduction. One 1.46-texel LOD1 UV overshoot was clamped
to the padded texture edge; level-zero UVs are unchanged. Forced-close lower-LOD images intentionally expose
their coarse distant geometry.

## Verification and limits

- Reduced arm stretch p99 ≤1.84; fingers ≤3.56; wrist swing ≤55.01°. Dense skin/weapon interior checks are clear
  across eight clips. The support-hand approach clears the previous soft beard-tip brush; the latest timing
  review records one brief 2.62 mm hand/prop contact, inspected in its linked grip close-up.
- Grounded soles stay within roughly ±0.8 cm; Running has intentional flight. The death's worst between-key
  floor penetration is 1.47 cm, inside the playbook's 2 cm band; the final corpse is within 0.1 mm of the floor.
- Export uses 120 Hz samples to preserve the fast aim. Forty Attack poses, including between-frame samples,
  match the master within 1.83 mm; seven poses per other clip remain within 0.044 mm.
  [Export parity](review/export_parity.json), [delivery checks](review/delivery_checks.json).
- All source/cooked colour and shadow levels have finite attributes, valid indices, nondegenerate triangles and
  normalized weights. Every runtime animation channel is identical to the full-detail export.
- Viewer checks pass all 24 tier/clip combinations with no console errors. Actual playback at 1× and ¼× covered
  all eight clips after enabling eight-weight skinning; front/side/quarter and textured hand close-ups were inspected.
- Normal desktop build and focused
  `mm8_dark_dwarf_actor_models_keep_tiers_crossbow_and_native_roles` regression passed. The test checks native size,
  shared tier assets, variants, attachment/look nodes, LODs, all clips and unchanged actor state.
- Native NVIDIA OpenGL/Wayland runs covered all tiers, walking, attack, hit, death and the loot transition indoors
  and outdoors, plus forced outdoor LODs. A quarter-speed outdoor run captured the final corpse before dissolution.
  The current engine replaces corpses with loot after a brief rest; the old `gameplay.corpses=keep` setting is no
  longer parsed. No engine changes were made for that behavior.
- **Indoor native sprite comparison unavailable:** console-spawned m632 sprites are invisible in Agar's Laboratory,
  matching the existing Wyvern limitation. The failed capture is retained; all three 3D actors render correctly.
  The outdoor sprite/model comparison uses the same camera and positions.
- The latest attack timing correction passed viewer, export, delivery, focused regression and native outdoor checks.
  Its indoor recheck remains blocked by EGL window-surface creation, as recorded in the previous revision.
- The full regression suite, Android and Vulkan were not run for this asset task. User artistic acceptance is separate.

## Reproduction

Claim the project with `tools/creature_workspace.py` before mutations. Use the guarded Blender/Meshy wrappers.
Five completed Meshy jobs consumed **40 credits** of the 100-credit limit; no job is pending.

Selected checkpoints: `work/motion_reduced.blend` (fitted motion), `work/master_uv.blend` (paid upload topology),
`work/textured_uv.blend` (verified transferred UVs), and the packed export master.
The final sequence is `compose_materials.py`, `export_runtime.py`, `prepare_runtime.py`, `verify_export.py`,
`build_lods.py`, `postprocess_runtime.py`, `viewer_tiers.py`, install both exports with `tools/install_model.py`,
then `validate_delivery.py`. `postprocess_runtime.py` applies the bounded LOD UV-edge correction before variants and attachment split.

For the feet/body correction, `revise_motion.py` updates Walking/Running/Attack. The subsequent timing-only
correction uses `revise_attack_timing.py` and `verify_attack_flow.py`, preserving the other seven clips.
`finish_foot_revision.py` verifies contact and deformation, then exports. `rebuild_final_mesh.py` remains the full pre-texture mesh/rig rebuild.
Do not regenerate the paid head unwrap casually: it is the correspondence contract for the returned texture.
`scripts/prepare_review.py` refreshes the viewer metadata from actual clip durations and file hashes.
The viewer uses the existing local three.js vendor files. Serve the repository root on port 8909; no external CDN
or service is required. Current captures, tours, run records and regression evidence are under `review/`.
