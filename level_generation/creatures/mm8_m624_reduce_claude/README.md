# MM8 Naga (`m624`, Naga / Naga Warrior / Naga Queen) reduction (2026-10-18)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: the installed textures,
three palette variants and region ramps stay valid. No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m624.glb` (identical to `mm8_m624_claude/export/`,
attack revision 3), copied to `work/mm8_m624_source_pre_reduce.glb` (rollback source). One merged body + head atlas
material, one `Body` node, 121 bones, 4 influences. The six swords (`mm8_m624_l1` ... `r3`) are separate installed
attachments and are not touched.

## Where the triangles are

The m624 build already reduced the body once (its README: "Body reduction protects hands, face and jewelry"), so
what is left is mostly protected detail. Of 12,785 triangles: six hands with fingers 4,139 (32 %), head 3,011 (face
1,885 of it), twelve cuffs/arm bands 1,170, eyes and earrings 355, tail 1,748, arms 975, torso 1,085, long hair 563.

Per-region tests (one region cut, everything else kept; `work/selection_only_*.json`):

| region | ratio | p99 / max mm | result |
|---|---|---|---|
| tail | 75 % | 4.4 / 57.4 | fail: the coil bends facet and the scale pattern smears (`work/coil.png`) |
| arms | 75 % | 2.2 / 33.8 | fail at the elbows |
| long hair | 75 % | 3.5 / 42.2 | fail at strand tips |
| torso | 60 % | in the combined run | pointed breasts, navel smeared (`review/close/sheet_c_body.png`) |
| head outside the face | 55 % | 2.7 / 11.0 | pass |
| face skin | 65 % | 0.9 / 2.2 | geometric pass, but the lips change shape (`review/close/sheet_c_head.png`): painted features kept |
| cuffs / arm bands | 65 % | 2.6 / 10.5 | pass, rings unchanged in close-ups |

## Picked configuration

`scripts/naga_sets_d.py`. Kept exactly: the six hands and fingers (fitted sword grips), tail, arms, long hair, eyes,
earrings, torso gold trims (bikini edges, choker), and the face's painted features (lips, eye make-up, brows: the
non-skin faces of the face plus two rings). Cut: head outside the face 55 %, face skin 65 %, cuffs 65 %, torso skin
80 %. Limits for the 2.24 m bind height: p99 6.71 mm, max 33.57 mm.

| step | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 12,785 | | | | |
| d: torso 90 % | 11,659 | 3.32 / 11.46 | 0.9989 | 0.9982 | pass |
| **d: torso 80 %** | **11,563** | 3.57 / 11.55 | 0.9988 | 0.9979 | **pick** |
| c: torso 60 % (+ whole face 65 %) | 10,953 | 4.91 / 23.32 | 0.9982 | 0.9970 | pass, rejected visually |
| c: torso 50 % | 10,857 | 6.57 / 30.75 | 0.9980 | 0.9959 | pass, rejected visually |

Texture drift (`texture_drift.py r90`): one face over 40 (1.5 cm²), p99 12.4. Close-ups straight from the GLBs
(file normals, `scripts/glb_close.py`): `review/glbclose/sheet_tex.png`, `sheet_clay.png`. Face, torso, cuffs, hands
and back match; the lips are marginally softer.

## Fixes in the copied scripts

- `reduce_ladder.py` set the candidate's world matrix before parenting it to the rig. The Naga's rig has its own
  transform, so every candidate sat 41.8 mm off the source (p99 41 mm at every step). Parent first, then copy the
  local matrices.
- `normal_weights.py` (`REA_NORMAL_WEIGHTS=1`): new vertices take their weights from the nearest source surface
  point whose normal agrees. Added for touching tail coils; with exact weights for source vertices it changed little
  here, but it is the safer transfer for coiled bodies.

## Build

`export_cand.py` (Cand_90) -> `swap_lod0.py` -> `build_lods.py` (as the m624 project: 0.5 / 0.25 / 0.125, 4
influences, body only) -> `mm8_m624_claude/scripts/shrink_shadow_lods.py` (inset shadow LODs, as installed) ->
`carry_variants.py`: `export/mm8_m624.glb`, 8.42 MB (installed 8.51 MB), 9 clips, three palette variants on all 8
colour/shadow meshes; nodes, materials, images, animations and extras match the installed file.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,785 | 6,390 | 3,192 | 1,592 |
| reduced | 11,563 | 5,778 | 2,888 | 1,439 |

- `scripts/grip_check.py`: all 3,151 LOD0 hand vertices keep their bind positions (max 0.0008 mm) and weights, so
  the sword grips are unchanged at LOD0. LOD1-3 hands come from the same builder as the installed LODs.
- `work/lod_check_{src,r90}.json`: every LOD keeps the source bounds (within 1 mm) and the same floor contact in
  every frame of every clip (LOD2/3 dip 1 / 8 mm, as installed); no face stretches over 20x in any clip.
  `review/lods/sheet.png` compares all LODs.
- Viewer: `review/viewer/` (installed vs reduced, three palettes, swords not shown);
  `tools/run_creature_review.py ... check`: 54 switches, no console errors.

## Open issues

- The saving is small (9.6 % at LOD0) because the remaining triangles are the protected hands (a third of the
  mesh) and face. A real cut needs the hands reduced and the grips refitted.
- The hair shell has holes at the back of the head in the source (visible in `review/glbclose/sheet_clay.png`,
  `head_back`); unchanged by this reduction.

## Status

Installed 2026-10-18 after user review ("OK") with `tools/install_model.py --world mm8 export/mm8_m624.glb`.
`OPENYAMM_REGRESSION_FILTER=mm8_naga_actor_models ./build/game/openyamm --headless-run-regression-suite actors`:
`mm8_naga_actor_models_keep_six_weapons_palettes_and_motion` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m624_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Body, REA_GLB=the rollback source) -> `dump_mesh.py`, `dump_groups.py` ->
`REA_SMALL=130 small_pieces.py` -> `face_classes.py` -> `naga_sets.py` -> `naga_sets_d.py 0.9,0.8` ->
`REA_NORMAL_WEIGHTS=1 REA_KEEP_FACES=work/keep_d.npy REA_GROUPS=work/groups_d.npy
REA_GROUP_RATIOS=1:0.55,7:0.65,8:0.65 run_ladder.sh d 0.9121,0.9046` -> `close_ladder.py`, `texture_drift.py r90` ->
build as above -> `grip_check.py`, `lod_check.py`, `lod_views.py`, `glb_close.py`, `viewer_variants.py`,
`viewer_manifest.py`.
