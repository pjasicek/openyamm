# MM8 Serpentman (`m524`, Serpentman / Elder / Warrior) reduction (2026-10-19)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) (with its MM8 batch lessons), no-retexture
branch. Scripts come from [mm8_m552_reduce_claude](../mm8_m552_reduce_claude/README.md) (parent-transform-fixed
`reduce_ladder.py`, exact source weights, coincident-vertex handling, floor contacts, tier viewer), with
`lod_check.py`, `face_bones.py`, `make_groups.py` and `region_error.py` from
[mm8_m604_reduce_claude](../mm8_m604_reduce_claude/README.md). No Meshy credits.

Source: the installed `assets_source/worlds/mm8/models/mm8_m524.glb`, byte-identical to `../mm8_m524_claude/export/`,
copied to `work/mm8_m524_source_pre_reduce.glb` (the rollback source). It has one `Body` node with 61 joints and
4 influences. There is one atlas material (body at x 0, head at x 1056 of 2080) with variants B and C, and no
attachments. The three tiers share colours, as in the native palette 524.

## Ladder

The weld takes 13,512 open edges down to 13. There are no coincident vertices with other weights: the lips are
fused, so the m492 split-seam handling has nothing to do. The mesh has one 9,397-face body piece and 24 tooth pieces
of 16-134 faces. The 134-face piece is the long front fang. Limits are scaled to the 2.0 m height (p99 6 mm, max
30 mm).

Faces by dominant bone (`face_bones.py`):
- head and jaw: 4,646;
- hands and digits: 3,900, about 650 faces per three-claw hand;
- spine, neck and arms: 1,546;
- tail: 511, already coarse over 3.5 m.

A plain uniform cut (`uni`) failed at 60 %: max 31.4 mm at the tail root in Death. A first grouped run (`ga`) left
too little for the body and failed: the arms and spine took 49 %, giving 217-292 vertices over 4 mm
(`region_error.py`, which now skips the ladder's own `ReduceProtect` group).

`make_groups.py` sets the final budgets:
- **Kept exactly (1,523 faces):** the tooth and fang pieces, plus the eye faces (class 6) and teeth on the head surface
  (class 5) with one ring of neighbours. Classes come from the creature's material-class maps placed like the runtime
  atlas.
- **Head and jaw:** group 1.
- **Hands and digits:** group 2.
- **Tail:** group 3, kept at 100 %.
- **Spine, neck and arms:** the remainder.

| run | head / hands / tail | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| source | | | 10,618 | | | | |
| uni | uniform | 70 % | 7,432 | 2.16 / 24.1 | 0.999 | 0.998 | pass |
| uni | uniform | 60 % | 6,370 | 2.99 / 31.4 | 0.997 | 0.998 | fail (max) |
| gc | 0.55 / 0.40 / 1.0 | 62 % | 6,634 | 2.80 / 24.1 | 0.998 | 0.998 | pass |
| **ge** | **0.50 / 0.35 / 1.0** | **57 %** | **6,156** | **3.33 / 24.1** | **0.998** | **0.998** | **pick** |
| ge | 0.50 / 0.35 / 1.0 | 55 % | 5,838 | 5.52 / 27.3 | 0.994 | 0.996 | pass (p99 near limit) |
| ge | 0.50 / 0.35 / 1.0 | 52 % | 5,520 | 9.57 / 45.3 | 0.990 | 0.991 | fail |

At the pick, the remainder keeps about 77 %. The fixed 24.1 mm max is the tail-root fold of the Dead pose, the same in
every passing step. Checks at 57 %:
- `stretch_check.py`: no face stretches in any clip.
- `texture_drift.py`: 5 faces over 40 (12.5 cm2).
- `dark_slivers.py`: 37 faces. The largest sit on the kept tail and hands, the method's noise floor on banded scales.

Close-ups (`work/source.blend` columns show the weld's custom-normal noise, so judge their clay from the GLB sheet
below):
- `review/close/sheet_head.png`: head front and side, mouth, open-mouth interior with teeth;
- `review/close/sheet_body.png`: torso front and back;
- `review/close/sheet_hands.png`: claws, palm, tail tip (source / 62 % / 57 %).

## Build

`export_cand.py` (Cand_57, `REA_NODE=Body`) -> `swap_lod0.py ... Body` -> `floor_contacts.py`
(`REA_FLOOR_EPS=0.012`, every clip: 7 tail-underside points) -> `build_lods.py` -> `shrink_shadow_lods.py` (the m524
project's, margins 4 / 7 / 12 mm) -> `carry_variants.py`. Result: `export/mm8_m524.glb`, 7.7 MB (installed 8.6 MB),
8 clips, 3 variants on all 8 colour and shadow meshes, region ramps unchanged.

`build_lods.py` protects the floor contacts and the 356 vertices within 2 cm of each bounding extreme. The installed
model used the tool defaults 0.5 / 0.18 / 0.06. On the new LOD0 those gave a 346-triangle LOD3 with an angular tail
and stick arms (`review/lods/sheet_006.png`). The LODs therefore use 0.5 / 0.25 / 0.10, which keeps the installed
far counts.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 10,618 | 5,308 | 1,907 | 613 |
| reduced | **6,156** | **3,078** | **1,529** | **591** |

`work/lod_check_{src,r57}.json` (`REA_NODE=Body lod_check.py`):
- every reduced LOD keeps the LOD0 bounds (2.0 m high, 3.83 m long, 2.01 m wide), where the installed LOD3 lost 1.9 cm
  of length;
- the lowest point in every clip is 3.3 mm at every LOD (installed LOD2/3: 7-31 mm, floating);
- no face stretches.

`review/lods/sheet.png` shows all LODs, installed above reduced, at rest, at the strike and dead.
`check_winding.py`: 0 inverted closed parts.

## Normals and retexture check

Verdict: **no retexture and no local fix needed**. No credits.
- **Shading:** judged only from GLBs imported directly (`glb_close.py`, `review/glbclose/sheet.png`, installed vs
  57 %, textured and clay). The installed model shades smooth, and so does the reduction. The reduction is a little
  softer at the nostrils and brow ridge. Teeth, fang, eyes and tongue are unchanged.
- **Tiers** (`review/glbclose/sheet_tiers.png`, viewer GLBs with the region ramps baked in): head, mouth, hand,
  torso, back and tail match in all three tiers. The tiers share colours by design.
- **Small source fleck:** a white fleck on the back of the right hand is in the installed texture. It is not caused
  by the reduction, which makes it less visible, and it is too small to need a fix.

## Viewer

`review/viewer/`: three tiers, installed vs 57 % (region ramps baked per tier by `viewer_variants.py`), all 8 clips
with the native references of the m524 project, opening on the reduced tier A Attack.
`python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m524_reduce_claude check`: 48 clip
switches, no console errors.

## Status

Installed 2026-10-19 (user: "serpentman ok"). `check_winding.py`: 0 inverted closed parts. Installed with
`tools/install_model.py ... --world mm8` (the rollback source matched the installed GLB byte for byte first);
`OPENYAMM_REGRESSION_FILTER=mm8_serpentman ./build/game/openyamm --world mm8 --headless-run-regression-suite actors`:
`mm8_serpentman_actor_models_keep_native_tiers_and_simulation` passes (`review/regression.log`). Recorded in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).
Rollback: install `work/mm8_m524_source_pre_reduce.glb` with `tools/install_model.py --world mm8`.

Reproduce:
1. `REA_NODE=Body REA_GLB=<rollback source> import_source.py`;
2. `dump_mesh.py`, `small_pieces.py`, `face_bones.py`, `make_groups.py`;
3. `REA_KEEP_FACES=work/keep.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.5,2:0.35,3:1.0 run_ladder.sh ge
   0.58,0.55,0.52`;
4. checks: `close_ladder.py`, `close_sheet.py`, `texture_drift.py r57`, `dark_slivers.py r57`, `stretch_check.py`;
5. the build above;
6. `lod_check.py`, `LOD_ORTHO=4.6 LOD_CENTRE=0,1.4,0.9 lod_views.py`, `glb_close.py`, `viewer_variants.py`.
