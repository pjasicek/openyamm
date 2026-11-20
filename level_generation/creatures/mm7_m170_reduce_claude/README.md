# MM7 Cleric of the Moon (`m170`, Acolyte / Cleric / Priest of the Moon) reduction (2026-10-20)

User: "OK good, now reduce tris of the 5" (mm7 batch B). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) for an unbroken model ("No part to rebuild: skip the retexture"),
scripts copied from [`mm8_m460_reduce_claude/`](../mm8_m460_reduce_claude/README.md) (the MM8 Cleric). No retexture,
no Meshy credits. **Not installed; awaiting user review** (batch B: nothing is installed).

Source: [`../mm7_m170_claude/export/mm7_m170.glb`](../mm7_m170_claude/export/mm7_m170.glb) (after the 2026-10-20
review revision), copied to `work/mm7_m170_source_pre_reduce.glb` (rollback source). Body: one node `M170`, three
material variants (`M170_A/B/C`, `KHR_materials_variants` `m170_a/b/c`), merged head/body 2080x1024 atlas with a
region mask (R robe, G banners), 4 influences, eight clips. No attachment.

## Regions (`make_groups.py`)

Weld 6,777 -> 690 open edges, no coincident vertices with other weights. Height 1.648 m (rest mesh; 1.70 m with the
rods): limits p99 4.94 mm, max 24.7 mm. After the weld the body is Smart Topology's pieces.

| label | region | faces | ratio |
|---|---|---:|---|
| 1 | face skin (head atlas) | 2,124 | 45 % |
| 2 | hair | 396 | 45 % |
| 3 / 4 | left / right claw hand | 589 / 585 | 45 % |
| 5 | skirt | 848 | kept |
| 6 | robe top + bell sleeves | 1,299 | 75 % |
| 7 | gold helmet | 712 | 60 % |
| 8 | back crescent | 450 | 55 % |
| 9 | banners | 700 | kept |

Kept exactly (`work/keep_e.npy`, 4,006 faces):
- pieces of up to 250 faces: collar, eyes, beads, rope ends, medallion, brooches;
- the two back rods with hooks and beads (thin tubes);
- the skirt and the banners. At 80-85 % the skirt missed by 44 mm in Death and the banners by 25 mm in Cast, for
  about 100 faces each (`group_error.py`, ladders a/b);
- one spot-lock round (`spot_lock.py`, 12 mm) around the 28 visible dark/light flecks and the 12 drifted faces of
  ladder d. They were at the hair/neck/face sides behind the face, z 1.27-1.40.

## Ladder

| config | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| a: face/hair 60, hands 55, skirt/top/banners 85, helmet 80, crescent 75 | 7,681 | 2.92 / 38.0 | 0.997 | 0.996 | fail: skirt in Death |
| b: face/hair/hands 50, skirt/top/banners 80, helmet 70, crescent 65 | 7,125 | 3.75 / 39.4 | 0.995 | 0.995 | fail: skirt in Death |
| c: b + skirt and banners kept | 7,401 | 2.60 / 19.9 | 0.998 | 0.997 | pass |
| d: face/hair/hands 45, top 75, helmet 60, crescent 55 | 7,033 | 3.12 / 19.9 | 0.998 | 0.996 | pass; 13 + 15 visible flecks, 12 drifted faces |
| **e: d + fleck/drift spot locks** | **7,179** | **3.28 / 19.9** | **0.997** | **0.996** | **picked** |

- **Pick 73 %.** The worst point is the robe top in Death (19.9 mm). Per region at e (`group_error.py`, p99 / max mm):
  face 2.2 / 5.4, hair 9.1 / 16.4 (Cast), hands 3.5-3.7 / 5.7-9.1, robe top 5.6 / 19.9, helmet 4.3 / 5.6,
  crescent 3.9 / 5.1.
- **Close-ups** (`review/close/sheet_cd_{head,body}.png`, `sheet_e_head.png`, `sheet_e_hair.png`; source / r75 / r70,
  textured and clay):
  - face, helmet, collar, hair (also in Cast), claw hands, the Cast hands, crescent, rods, banners, Death and Attack
    all match;
  - the lips and the claw tips are slightly softer in clay.
- **Flecks at the pick:** `dark_slivers.py` (`REA_DARK_L=80 REA_DARK_N=4`) flags 9 dark and 15 light faces;
  `visible_only.py` keeps 6 and 7. All are on the neck and hair behind the face, and none shows in the close-ups.
  `texture_drift.py`: 0 faces over 40.

## Normals

Plain smooth. Rendered straight from the GLBs (`scripts/glb_close.py`, `review/glbclose/sheet.png`: face, hands,
torso, back, head back, chest), the source and the reduction shade the same.

## Build

`export_cand.py` (Cand_70 of `work/ladder_e.blend`, REA_NODE=M170, 4 influences as the source) ->
`swap_lod0.py ... M170` -> `build_lods.py`. That step uses the creature's own settings: `tools/build_actor_lods.py`
defaults 0.5 / 0.18 / 0.06, protecting LOD0 points within 1 cm of the floor in Death/Dead and the top 5 mm of the
crown (171 points). Then `shrink_shadow_lods.py` (from the source project) -> `carry_variants.py`:
`export/mm7_m170.glb`, 7.6 MB (source 8.2 MB). Textures, variants, region ramps, clips and node structure are the
source's. `check_winding.py`: 0 inverted closed parts.

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source | 9,883 | 4,930 | 1,757 | 570 |
| reduced | 7,179 | 3,577 | 1,272 | 407 |

`lod_check.py` (`work/lod_check_{src,r70}.json`):
- every LOD keeps the 1.700 m height and LOD0's lowest point in every clip (Death -73.7 mm, as the source);
- LOD3's rest width is 0.73 m against 0.81 m: the banner tips collapse at the farthest LOD;
- at most 1-2 faces stretch over 20x in any clip at LOD1-3 (the source has 0-1).

## Review

Viewer `review/viewer/`: source vs reduced per tier, with the tier ramps baked by `viewer_variants.py`.
http://127.0.0.1:8912/level_generation/creatures/mm7_m170_reduce_claude/review/viewer/

`tools/run_creature_review.py ... check`: 48 clip switches, no console errors. `review/shots/std_b_pair.png`: tier B,
source / reduced.

## Status

Not installed; awaiting user review. To use it, install `export/mm7_m170.glb` with the command in
[`../mm7_m170_claude/README.md`](../mm7_m170_claude/README.md) (same binding) and record it in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

Rollback: `work/mm7_m170_source_pre_reduce.glb` (= `../mm7_m170_claude/export/mm7_m170.glb`).

## Reproduce

1. **Import and dump:** `REA_NODE=M170 REA_GLB=<rollback source> import_source.py` -> `dump_mesh.py` ->
   `dump_faces.py` -> `make_groups.py`.
2. **Ladder d:** `keep_c` = `keep_base` + groups 5 and 9, then
   `REA_KEEP_FACES=work/keep_c.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.45,2:0.45,3:0.45,4:0.45,6:0.75,7:0.6,8:0.55 REA_HEIGHT_M=1.648 run_ladder.sh d 0.70`.
3. **Checks on d:** `dark_slivers.py r70` (dark and `REA_LIGHT=1`) -> `visible_only.py` -> `texture_drift.py`.
4. **Lock:** `spot_lock.py work/keep_c.npy work/keep_e.npy 0.012 $(cat work/spots_r70.txt)`.
5. **Ladder e:** the same ratios with `keep_e`, then the checks again, `group_error.py`, `close_human.py`,
   `close_sheet.py`.
6. **Build:** as above, then `lod_check.py`, `glb_close.py`,
   `viewer_variants.py <glb> r100|r73` and the manifest.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: corpse at -3.6; dying sinks to -3.9.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m170.glb export/mm7_m170.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m170.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h11](../gait_rollout_20261031/h11/README.md) appended `Walk2` (slower walk, wandering) and `Jog` (chase) to the installed
`assets_source/worlds/mm7/models/mm7_m170.glb` (library-loop legs, this model's own `Walking` arms, robe/cape chains
re-simulated on the new motion); existing clips are unchanged and the bindings are in
`../gait_rollout_20261031/h11/bindings.yml`. Rebuild: `level_generation/creatures/gait_rollout_20261031/h11/scripts/rebuild.sh m170`
(from `h11/work/mm7_m170_pre_gait.glb`). A far-LOD repair, head-bob, floor-fix or reduction rerun, or any re-export
of this model, must re-graft these clips (copy the new source over the pre-gait copy and rerun that rebuild, or graft
them with `claude_shared/graft_clips.py`).

## Anim fix (2026-11-11, MM6–MM8 audit)

Walk2 and Jog recomposed with a lower hidden-leg lift and a shorter jog stride: robe cloth bad 19.6 -> 13.8 % and
27.2 -> 12.2 %; strides 1.343 / 1.8. Details: [mm7_m170_animfix_claude](../mm7_m170_animfix_claude/README.md).
