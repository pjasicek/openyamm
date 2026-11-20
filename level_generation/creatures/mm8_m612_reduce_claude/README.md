# MM8 Gog (`m612`, Smoke / Ember / Fire Gog) reduction (2026-10-19)

This follows the default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), including its MM8 batch lessons,
without a retexture. Scripts come from [mm8_m592_reduce_claude](../mm8_m592_reduce_claude/README.md): the ladder
with exact source weights, UV-based weights (`uv_weights.py`, `REA_WEIGHTS=component`), the floor-contact and
bounding-extreme LOD locks, `fix_lod_winding.py`, `carry_variants.py` and the tier viewer bake. New for this
creature:
- `make_groups.py`: Gog regions;
- `gog_close.py`: close-ups straight from GLBs;
- `uv_faceid.py` and `mask_fix.py`: the claw-base mask fix.

No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m612.glb`, identical to `mm8_m612_claude/export/`. It is
copied to `work/mm8_m612_source_pre_reduce.glb` as the rollback source. It has:
- one material (`Gog_A`, variants B/C) with a 2080x1024 body/head atlas;
- a region mask with the skin in R;
- a specular mask in the metal-rough map's red channel (64 skin, 255 keratin: horns, claws, spines, tail barb, teeth;
  128 tongue);
- the mesh node `Body` with **8 influences**. The m612 project measured up to 33.5 mm of drift at 4, so the ladder,
  the export and the LODs keep 8 (`REA_INFLUENCES=8`, `max_influences=8`);
- 9 clips at 60 Hz, no attachments and no effect meshes;
- shadow LODs that are copies of the colour LODs (no inset), rebuilt the same way.

## Ladder

The weld goes from 5,817 to 5 open edges. The mesh is one 8,879-face body plus 18 small pieces (1,120 faces):
- 12 teeth, a mouth cap, the tongue and a cap at the back of the head;
- 4 tail spines.

The head holds 35 % of the faces (3,518), the feet 1,400 and the hands about 900. The body is lean, at 2,450 faces
for the torso, legs, arms and tail. Limits are scaled to the 1.70 m height: p99 5.1 mm, max 25.5 mm.

`scripts/make_groups.py` sets the budgets:
- **kept exactly (1,835 faces):**
  - the head's small pieces;
  - the yellow eyes (base colour) and the lips (head faces within 1.5 cm of a tooth), each with one ring of
    neighbours;
  - the soles (faces below 2 cm);
- **groups:** 1 head skin (1,458), 2 horns (368), 3 claws (774), 4 hand and foot skin (2,440), 5 spines (tail spine
  pieces and keratin on the back, shoulders and tail, 674). The body takes the rest of the ladder budget.

| ladder | groups (head / horns / claws / hand-foot / spines) | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 9,999 | | | | |
| g1, nearest-face weights | 60 / 50 / 50 / 60 / 50 | 6,997 (70 %) | 5.89 / 25.8 | 0.988 | 0.995 | fail |
| u1, UV weights | 60 / 50 / 50 / 60 / 50 | 6,997 (70 %) | 5.66 / 24.2 | 0.988 | 0.995 | fail |
| u2 | 60 / 55 / 65 / 75 / 55 | 7,497 (75 %) | 4.33 / 24.5 | 0.992 | 0.996 | pass |
| u2 | 60 / 55 / 65 / 75 / 55 | 7,197 (72 %) | 5.45 / 24.5 | 0.988 | 0.994 | fail |
| u3 | 50 / 45 / 60 / 70 / 45 | 6,995 (70 %) | 5.03 / 24.5 | 0.989 | 0.995 | pass |
| u4 | 45 / 40 / 55 / 65 / 40 | 6,795 (68 %) | 5.43 / 24.7 | 0.989 | 0.995 | fail |
| **u5** | **60 / 45 / 60 / 70 / 45** | **7,147 (71 %)** | **4.96 / 24.5** | **0.990** | **0.995** | **pick** |

- **What sets the limit:** `region_error.py` puts the error first on the feet and hands when they go to 50-60 %
  (u1). With them at 60-70 %, it moves to the body (pelvis, thighs, upper arms): the body breaks below about 73 %
  of its faces (u2 at 72 %, where it gets 65 %).
- **Head 60 % instead of 50 % (u5 vs u3):** clay renders straight from the GLBs showed slight lumps behind the ears
  and blunter ear tips at 50 % (`review/close/` `r70_head_side_clay.png` against `r71h_head_side_clay.png`). That
  costs 150 triangles.
- **Max error:** the 24.5 mm max sits in Running and is the same at every step. `probe_max.py`'s fixed frames put
  the largest misses (10-12 mm) inside the open mouth and at the left claw and foot tips.
- **Weights:** the UV weights only trim the error a little (u1 against g1); they are kept anyway.
- **Close-ups** (`review/close/sheet_r70_tex.png` / `_clay.png`; source above, 70 % below; textured and clay, both
  from GLBs): eyes, teeth, tongue, lips, horns, ears, claws, toe claws, tail barb and dorsal spines read unchanged.
- **Normals:** the stored normals agree with smooth normals (median 3.4 deg) and there are no split normals, so the
  reduction uses plain smooth normals. Its clay renders match.
- **Texture drift at 71 %:** 5 faces over 40 (5.8 cm2): claw-base boundary faces on the left hand and two tail-spine
  faces. No drift lock.

## Build

The chain is:
1. `export_cand.py` (REA_NODE=Body, REA_CAND=Cand_71, REA_INFLUENCES=8; from `work/ladder_u5.blend`);
2. `swap_lod0.py`;
3. `floor_contacts.py` (Death/Dead, 21 points);
4. `build_lods.py`:
   - ratios 0.5 / 0.25 / 0.16. At the m612 project's 0.125, LOD3 came out at 875 triangles with thin arms and tail
     (`review/lods/`);
   - 8 influences;
   - floor contacts and the vertices within 2 cm of each bounding extreme protected;
5. `fix_lod_winding.py` (no repairs needed);
6. `carry_variants.py`;
7. `mask_fix.py` + `swap_mask.py` (see below).

The result is `export/mm8_m612.glb` at 9.5 MB (installed: 10.5 MB). It has the same nodes, skin, materials,
variants (on all 8 colour and shadow meshes), LOD extras and 9 clips as the installed model. The pre-mask-fix build is
`work/mm8_m612_r71_pre_maskfix.glb`.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 9,999 | 4,999 | 2,497 | 1,234 |
| reduced | **7,147** | 3,573 | 1,771 | 1,126 |

`lod_check.py` (`work/lod_check_{src,r71}.json`, REA_NODE=Body):
- **Bounds:** every LOD keeps the LOD0 bounds (height 1.700 m, tail reach 0.958 m). The front extreme is 1.9 mm
  shorter.
- **Floor:** every clip's lowest point equals the source's at every LOD (Walking -1.8 mm, Running -1.4 mm, Dead
  +2.0 mm). The installed LOD2/3 sank to -3.3 to -5.4 mm.
- **Stretched faces:** none at LOD0-2, and one at LOD3 in Death. The installed model had 7 at LOD1.
- **Winding:** `check_winding.py` finds 0 inverted closed parts.

`review/lods/sheet.png` compares installed and reduced at every LOD (standing, attack, corpse). The reduced LOD3 has
a slightly thinner tail and legs than the installed one.

## Texture check: claw-base mask spill, fixed locally

**Normals:** the installed model shades smooth, and so does the reduction.

**Head:** face, eyes, teeth, tongue, ears and horns match the installed model in all three tiers
(`review/close/sheet_tiers.png`). No fix needed.

**Body: a pre-existing region-mask spill, now fixed.** The gold, dotted keratin band is in the base colour at:
- each claw base and toe claw base;
- the heel spurs;
- the shoulder and back spine bases.

It carried the skin mask, so the tier ramp turned it pale yellow in tier A, pale blue / white in B and pink in C,
in the installed model too. The heel spurs are painted on skin-class faces (specular 64), so the specular map alone
does not find them.

`mask_fix.py` clears the mask (soft edge) on gold texels (hue 25-70 deg) and pale unsaturated texels in two places:
- around every non-head keratin face (two rings);
- on every hand and foot face.

The head is excluded, because its skin has yellow-green tones that must stay ramped. So are the pale belly plates.
22,442 texels inside faces change, and `swap_mask.py` replaces only the mask image; the base colour is unchanged.
Result (`review/close/sheet_maskfix.png`): the band is the painted gold in all three tiers. Tier A's claw bases
change from pale yellow to that gold.

## Viewer

`review/viewer/` uses the m612 project's viewer with its eight-weight skinning shader. It shows installed and reduced
(mask fix included) for each tier, baked by `viewer_variants.py`, with the native reference frames from
`mm8_m612_claude`.
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m612_reduce_claude check`: 54 clip
switches, no console errors.

## Status

Installed 2026-10-19 (user: "gog ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first).
`OPENYAMM_REGRESSION_FILTER=mm8_gog ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`: `mm8_gog_actor_models_keep_native_tiers_and_palm_fire` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m612_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce:
1. `REA_NODE=Body REA_GLB=<rollback source> blender -b -P import_source.py`;
2. `dump_mesh.py`, `face_bones.py`, `dump_weights.py`; extract the GLB images to `work/img0..3.png` (base colour,
   metal-rough, normal, region mask);
3. `make_groups.py`;
4. `REA_WEIGHTS=component REA_KEEP_FACES=work/keep.npy REA_GROUPS=work/groups.npy
   REA_GROUP_RATIOS=1:0.6,2:0.45,3:0.6,4:0.7,5:0.45 run_ladder.sh u5 0.715` (8 influences by default here);
5. `region_error.py`, `probe_max.py`, `texture_drift.py r71` (needs `work/basecolor.png` = img0), `gog_close.py`;
6. build as above;
7. `uv_faceid.py`, `mask_fix.py`, then `swap_mask.py work/mm8_m612_r71_pre_maskfix.glb work/mask_fixed.png
   export/mm8_m612.glb`;
8. `lod_check.py`, `lod_views.py`, `viewer_variants.py export/mm8_m612.glb r71` and
   `viewer_variants.py work/mm8_m612_source_pre_reduce.glb r100`.

## Gait rollout (2026-10-31)

[Gait rollout package h15](../gait_rollout_20261031/h15/README.md) appended `Walk2` (humanoid-set Armed Walk, 0.95 s,
stride 1.3858) to the installed `mm8_m612.glb`, bound only on MM7 AGog C (`walking: Walk2`; it wandered on Walking
at x0.62). Every other Gog tier keeps the user's walk-as-run; its chase now plays at the 2x cap (x2.08-2.70 asked,
see the package README). Rebuild: `gait_rollout_20261031/h15/scripts/rebuild.sh mm8_m612`. A far-LOD repair rerun or
re-export must re-graft that clip (copy the new source over `h15/work/mm8_m612_pre_gait.glb` and rebuild).
