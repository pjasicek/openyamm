# MM8 Bedraggled Human (`m620`, Bedraggled Human A/B/C) reduction (2026-10-19)

User: "pick 5 more to do" (next batch after the Ether Knight). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), including its MM8 batch lessons. No retexture, no Meshy credits.
Not installed; awaiting user review.

Source: the installed `assets_source/worlds/mm8/models/mm8_m620.glb`, identical to `mm8_m620_claude/export/`
(head revision `m620_solid_hair_v3`), copied to `work/mm8_m620_source_pre_reduce.glb` (rollback source). One
material (`Bedraggled_A`, three tier variants), merged head/body 4128x2048 atlas (body left, head right, u > 0.505),
node `Bedraggled`, up to 8 influences, 6 clips, no attachments. Scripts come from `mm8_m424_reduce_claude/`
(parent-transform fix, exact source weights), with `lod_check.py` and `glb_close.py` from `mm8_m604_reduce_claude/`.

**Head decision.** `mm8_m620_claude/README.md` calls the 15,004-triangle budget a deliberate exception for the
requested facial detail. The user then said the head may be cut too ("it is not THAT important"). The face is
therefore reduced gently like any other face. The eyes and lips are kept exactly, and the result is judged on
textured close-ups.

## Regions (`make_groups.py`, `face_keep.py`)

Weld 12,206 -> 3,966 open edges (ragged vest and trouser edges, hair strands); no coincident vertices with other
weights. 115 pieces: the head/body skin piece (8,167 faces), trousers, vest, the hair_v3 volume (1,248), boots,
cuffs, and 107 small pieces (hair strands, waist cords).

| label | faces | picked ratio |
|---|---:|---|
| 1 head skin (head-atlas faces: face, ears, scalp, neck) | 4,844 | 55 % |
| 2 hair_v3 volume | 1,248 | 50 % |
| 3 left hand, 4 right hand (hand/finger bones) | 615 / 626 | 50 % each |
| 0 rest (vest, torso, trousers, boots) | 6,983 | remaining budget |

Kept exactly (`work/keep_f.npy`, 1,007 faces): pieces of up to 80 faces (588: hair strands over the scalp, cords),
the soles (faces below 1.5 cm, 99), the eyes (245 faces within 1.4 cm of each eye centre) and the lips (74). The eye
and lip centres come from the base colour: the darkest iris/lash faces and the reddest lip faces of the face.

## Ladder (limits for the 1.70 m height: p99 5.1 mm, max 25.5 mm)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a: head 65, hair 60, hands 55 | 65 % | 9,750 | 3.97 / 17.4 | 0.990 | 0.993 | pass |
| a | 60 % | 9,000 | 5.16 / 19.1 | 0.985 | 0.989 | fail: the body starves |
| b: head 60, hair 50, hands 50 | 62 / 58 % | 9,300 / 8,700 | 4.03 / 17.4, 4.93 / 17.4 | 0.989 / 0.986 | 0.993 / 0.990 | pass; 58 % has a vest fleck |
| c: head 50, hair 50, hands 50 | 60 / 55 % | 9,000 / 8,250 | 3.86 / 17.4, 4.88 / 17.4 | 0.991 / 0.986 | 0.993 / 0.990 | pass; eyes blur in the texture |
| d: face 65, rest of head 40 | 60 % | 9,410 | 4.49 / 17.8 | 0.986 | 0.992 | pass; 56 % fails (p99 5.42) |
| e: face 65, rest of head 50 | 58 % | 8,910 | 5.15 / 17.8 | 0.983 | 0.989 | fail |
| **f: eyes and lips kept, head 55, hair 50, hands 50** | **60 %** | **9,000** | **4.31 / 17.4** | **0.989** | **0.992** | **picked** |
| f | 58 % | 8,700 | 4.78 / 17.4 | 0.986 | 0.990 | pass; vest fleck under the left armpit |
| g = f + one drift-lock round | 60 / 58 % | 9,000 / 8,700 | 4.58 / 17.4, 5.11 / 19.1 | 0.987 / 0.985 | 0.991 / 0.989 | 58 % fails, and the fleck stays |

- **The body sets the floor.** Collapses along the ragged vest and trouser edges are capped by their open
  boundaries, so below about 58 % the vest edges and shoulders take the error.
- **Splitting the face from the rest of the head costs more than it saves** (d, e). The whole head at one ratio lets
  MeshLab spend collapses on the scalp under the hair.
- **Eyes and lips:** at a 50 % head (c), the irises and lid lines smeared in the texture. Kept exactly (f), they match
  the source (`review/close/sheet_f_face.png`).
- **58 % vs 60 %:** at 58 %, a ragged vest tip below the left armpit shows as a green fleck from the front, in f and
  g (`review/close/sheet_fg_torso.png`). 60 % is clean.
- **Texture drift** (`texture_drift.py r60`): 7 faces over 40, all large faces on the trousers and vest; close-ups
  match. A one-round lock (g) did not remove the fleck and raised p99, so no lock.
- **Close-ups:** face, hair, ears, back of the head (`review/close/sheet_f60_head.png`), body
  (`sheet_f_body.png`, `sheet_f60_limbs.png`, `sheet_f60_larm.png`). One known nit: the tight left-forearm crop
  (`lcuff`) shows a few-pixel orange sliver at the elbow, invisible in the wider `larm` view.

## Normals: the head is not plain smooth

The installed body shades with plain smooth normals, but the separately modelled head carries custom normals. On the
kept eye and lip faces, where the geometry is identical, the reduction's smooth normals differed from the installed
ones by 22-28 deg (median). In clay renders straight from the GLBs (`review/glbclose/sheet_head_normals.png`), the
smooth head lost the lid, lip, brow and stubble creases. `head_normals.py` gives every head-atlas vertex of the
reduced LOD0 the source normal interpolated at its UV (the head charts do not overlap): 6,457 vertices by UV and 134
by nearest source vertex. It reads the source GLB directly, never the welded `source.blend` (see the playbook's
normals lesson). The shading now matches the source (`review/glbclose/sheet.png`); body normals stay smooth, as in the
source (0.4 deg median difference at shared vertices). The LOD builder rebuilds LOD1-3 with smooth normals, as the
installed build did.

## Build

`export_cand.py` (Cand_60 of `work/ladder_f.blend`, REA_INFLUENCES=8) -> `swap_lod0.py` -> `head_normals.py` ->
`build_lods.py` -> `mm8_m620_claude/scripts/shrink_shadow_lods.py` -> `carry_variants.py`:
`export/mm8_m620.glb`, 11.3 MB (installed 12.9 MB).

`build_lods.py` uses ratios 0.5 / 0.25 / 0.17, with protected points: LOD0 vertices within 1 cm of the floor in any
Death/Dead frame and within 5 mm of each bounding extreme (225 points). The installed build's 0.125 for LOD3 left
1,089 triangles from the smaller LOD0, and the figure collapsed to a thin spike with the arms gone
(`review/lods/sheet_lod3_ratio.png`). At 0.17 (1,494) it holds, close to the installed LOD3.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 15,004 | 7,484 | 3,713 | 1,838 |
| reduced | **9,000** | 4,467 | 2,214 | 1,494 |

Checks:
- **`lod_check.py`** (REA_NODE=Bedraggled): every LOD keeps the 1.700 m height and 1.154 m width. The lowest point
  in every clip equals the source LOD0's: Walking 0.1 mm, Death 1.1 mm. The installed LOD2/LOD3 went 5 mm under the
  floor in Death.
- **Stretched faces:** none at LOD1-3. LOD0 has one in Dead/Death/Walking, as the installed LOD0 does.
- **`review/lods/sheet.png`:** every LOD at rest and in Hit.
- **`check_winding.py`:** 0 inverted closed parts.
- **`normal_map_convention.py --check`:** unchanged.
- **Unchanged from the source:** the six clips, the three palette variants on all 8 colour/shadow meshes, and
  `B_R_Finger42`.

## Retexture check

- **Texture set:** base colour, metal-rough, normal and region mask are byte-identical to the installed ones, and the
  reduction keeps UVs.
- **Head vs body skin:** linear luminance median 0.241 face, 0.252 neck, 0.266 hands, 0.262 torso; no unify step
  needed.
- **Tiers B and C:** close-ups match the installed (`review/glbclose/sheet_tiers_bc.png`). The skin-coloured tears in
  the vest are painted that way in every tier.
- **Verdict:** no retexture for either half; no local fix. No credits spent.

## Review

Viewer `review/viewer/` (installed vs reduced for each tier, tiers baked by `viewer_variants.py`), opening on tier A
reduced: http://127.0.0.1:8912/level_generation/creatures/mm8_m620_reduce_claude/review/viewer/.
`tools/run_creature_review.py ... check`: 36 clip switches, no console errors.

## Status

Installed 2026-10-19 (user: "bedragled human ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_bedraggled_human ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_bedraggled_human_actor_models_keep_civilian_roles` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m620_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce: `import_source.py` (REA_NODE=Bedraggled, REA_GLB=the rollback source) -> `dump_mesh.py` -> `dump_faces.py`
-> `REA_FACE_Y=-9 make_groups.py` -> `face_keep.py work/keep_base.npy work/keep_f.npy` -> `REA_KEEP_FACES=work/keep_f.npy
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.55,2:0.5,3:0.5,4:0.5 run_ladder.sh f 0.6` -> close-ups
(`close_human.py`, `CLOSE_TAG=f`), `texture_drift.py r60` -> build as above (`head_normals.py
work/mm8_m620_source_pre_reduce.glb work/pick_lod0.glb work/pick_lod0.glb` after `swap_lod0.py`) -> `lod_check.py`,
`lod_views.py`, `glb_close.py`, `viewer_variants.py` for both GLBs.

## Gait rollout (2026-10-31)

The installed source `assets_source/worlds/mm8/models/mm8_m620.glb` now also carries `Walk2` (humanoid set Relax-Walk-Forward, 1.15 s, stride 1.2096) for wandering at 1.10; `Walking` stays its run (flight at 2.19 is a walking pace).
Appended by [package h17](../gait_rollout_20261031/h17/README.md) on the installed source (existing clips, meshes, LODs
and variants byte-identical); pre-gait copy and rollback: `../gait_rollout_20261031/h17/work/mm8_m620_pre_gait.glb`.
Bindings are in `../gait_rollout_20261031/h17/bindings.yml` (applied by the rollout coordinator). Rebuild:
`../gait_rollout_20261031/h17/scripts/rebuild.sh m620`. A far-LOD repair, head-bob or reduction rerun that rewrites
this source must re-graft these clips (copy the new source over the pre-gait copy and rebuild, or
`claude_shared/graft_clips.py`).
