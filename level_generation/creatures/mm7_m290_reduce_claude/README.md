# MM7 Monk (`m290`, Monk / Initiate / Master) reduction (2026-10-20)

User: "OK good, now reduce tris of the 5" (the five MM7 batch B casters). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) for an unbroken model ("No part to rebuild: skip the
retexture"); scripts from [`../mm8_m460_reduce_claude/`](../mm8_m460_reduce_claude/README.md) (the MM8 Cleric).
No retexture, no Meshy credits. **Not installed; awaiting user review** (the Monk itself is not installed either,
batch B rule).

Source: the production export `../mm7_m290_claude/export/mm7_m290.glb` (revision 2026-10-20: face_forward, hands hidden
in the sleeves, `flatten_feet.py` sandals on the floor, Attack = Unarmed Cast R Attack 1 with `smooth_bones.py`),
copied to `work/mm7_m290_source_pre_reduce.glb` (rollback; sha256 `4f275ee8…`). The ladder ran on an earlier export
(`1932c743…`): same mesh, UVs, textures and rest pose, only the clips differ; the pick was rebuilt on each new source
without a new ladder (see Rebuild). Body:
one node `M290`, one primitive, three material variants (`M290_A/B/C`), merged head/body 2080x1024 atlas with a robe
region mask, eight clips including the hand-bone scale channels.

## Regions (`make_groups_m290.py`)

Weld 6,475 -> 173 open edges, no coincident vertices with other weights. The GLB carries no part labels:
`work/face_labels.npz` takes each face's garment and piece from the production master
(`../mm7_m290_claude/work/rig_v6.blend`, same rest geometry, matched by face centre within 0.001 mm).
`head_visible.py` splits the head piece by visibility (a ray from the face escapes the rest mesh): 1,152 of its
2,341 faces can be seen, the rest are the back of the head and the cropped hair inside the hood.

| label | region | faces | ratio |
|---|---|---:|---|
| 1 | visible face (face, ears, neck front) | 1,152 | 60 % |
| 2 | hidden head (back of the head, hair inside the hood) | 1,189 | 30 % |
| 3 | hands (rigid; shrunk into the sleeves while folded) | 659 | 50 % |
| 4 | hood, cowl, top and wide sleeves | 4,132 | 82 % |
| 5 | robe skirt | 1,300 | 92 % |
| 6 | shins and sandals | 899 | kept |

Kept exactly (`work/keep_f.npy`, 2,254 faces):
- the eyes (332) and the rope's knotted ends (600; thin tubes);
- the painted pale strips on the robe (hood lining edge, rope band at the waist: region mask R < 0.5);
- the shins and sandals: at 50 % the shins missed by 30-40 mm in Death, where they show below the robe;
- the skirt's hem band (below 12 cm);
- one error lock (`err_lock.py`, 15 mm, 2 cm, from Cand_77 of ladder b: shoulder, armpit, forearm and skirt points
  in Death and Cast);
- two spot locks (`spot_lock.py`, 2 cm): a drifted face on the forehead beside the hood lining and a dark sliver on
  the rope band at the back.

## Ladder

Limits for 1.70 m: p99 5.1 mm, max 25.5 mm, IoU >= 0.98, SSIM >= 0.93.

| config | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| a: face 65, hidden head 35, hands 55, hood 80, skirt 85, shins 50 | 6,975 | 5.73 / 47.1 | 0.997 | 0.995 | fail: shins 40 mm in Death, skirt |
| b: shins kept, hood 85, skirt 92 | 7,301 | 3.67 / 46.6 | 0.998 | 0.996 | fail: skirt max in Death |
| c: b + error lock | 7,311 | 3.55 / 23.0 | 0.998 | 0.996 | pass |
| d: face 60, hidden 30, hands 50, hood 78, skirt 88 | 6,905 | 4.80 / 47.1 | 0.996 | 0.995 | fail: skirt in Death |
| e: face 60, hidden 30, hands 50, hood 82, skirt 92 | 7,071 | 4.43 / 23.0 | 0.998 | 0.996 | pass; one visible drift, one visible sliver |
| **f: e + two spot locks** | **7,081** | **4.53 / 23.0** | **0.998** | **0.996** | **picked** |

- **Per region** (`group_error.py`, Cand_75 of f): face p99 1.4 / max 2.3 mm; hidden head 7.5 / 11.0 (inside the
  hood); hands 5.2 / 6.6; hood and sleeves 4.7 / 22.4 (Hit); skirt 5.5 / 19.1 (Death). The skirt and hood errors sit
  in the robe chains of Death and Hit, where the source cloth itself stretches.
- **Flecks:** `texture_drift.py` 32 faces over 40, `dark_slivers.py` (`REA_DARK_L=80 REA_DARK_N=4`) 51 faces; after
  `visible_only.py` 0 and 0 visible (all on the hidden head and inner robe).
- **Close-ups** (`close_monk.py`, `review/close/sheet_f_{a,b}.png`, source / r75, textured and clay): face in the
  hood, hood tip and back, cowl, folded arms (Standing, Walking), sleeves in Attack and Cast, both hands, rope, hem,
  sandals, back and Death match. The face is a little softer around the eyes in clay.
- **Shading** straight from the GLBs (`glb_close.py`, `review/glbclose/sheet.png`): the same as the source.

## Build

`export_cand.py` (Cand_75 of `work/ladder_f.blend`, REA_NODE=M290, 4 influences as the source LOD0) -> `swap_lod0.py
... M290` -> `build_lods.py` (the Monk's own settings: `tools/build_actor_lods.py` defaults 0.5 / 0.18 / 0.06, 8
influences; protected points: LOD0 vertices within 1 cm of the floor in any Death/Dead frame, the top 5 mm and the hood
tip, 246 points) -> `MESH=M290 ../mm7_m290_claude/scripts/shrink_shadow_lods.py` (as the production chain) ->
`carry_variants.py`: `export/mm7_m290.glb` (sha256 `fb53d693…`), 7.6 MB (source 8.3 MB). Textures, variants, region ramps, clips, sockets and
node structure are the source's; every animation sampler's input and output bytes are identical (the hand scale
channels included: Standing 0.03, Attack 0.03-1.0). `check_winding.py`: 0 inverted closed parts.

| body | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source | 9,331 | 4,665 | 1,679 | 555 |
| reduced | 7,081 | 3,540 | 1,273 | 422 |

`lod_check.py` (`work/lod_check_{src,r75}.json`): every LOD keeps the 1.70 m height; per-clip lowest points equal the
source's at LOD0 (Attack -3.1 mm, Standing -3.2, Walking -6.1, Death -22.3 vs -21.0); stretched faces over 20x: 0 at
LOD0-1, 1-2 per clip at LOD2-3 (the source's LOD2 has the same). Before the source's `flatten_feet.py` fix the Attack's
lowest point was -89.6 mm (sandals under the floor), in the source and the reduction alike.

## Review

Viewer `review/viewer/` (source vs reduced per tier, ramps baked by `viewer_variants.py`):
http://127.0.0.1:8912/level_generation/creatures/mm7_m290_reduce_claude/review/viewer/.
`tools/run_creature_review.py ... check`: 48 clip switches, no console errors (after the second rebuild, revision reduce-3). `review/shots/std_b_pair.png`: tier B
source / reduced.

## Rebuild on the new source (2026-10-20)

The production Monk's clips changed after the ladder (`flatten_feet.py`: sandals 3.5-8.7 cm under the floor; mesh,
UVs, textures and hand scale channels unchanged). The same pick (Cand_75 of `work/ladder_f.blend`) was rebuilt on the new
source: `export_cand.py` -> `swap_lod0.py` -> `build_lods.py` (264 protected points) -> `shrink_shadow_lods.py` ->
`carry_variants.py`. Every animation sampler is byte-identical to the new source (hand scale: Standing/Walking 0.03,
Attack 0.03-1.0 on both hands); `check_winding.py` 0; `lod_check.py` as above; viewer GLBs rebuilt.

Second rebuild (same day, after user review of the source): Attack became Unarmed Cast R Attack 1 (1.267 s, impact
0.483 s) and the spine, neck and head are smoothed in Attack and Cast (`smooth_bones.py`); mesh, UVs and textures
unchanged. Same pick and chain (267 protected points); animation samplers byte-identical to the new source, hand scale
unchanged (Standing/Walking 0.03, Attack 0.03-1.0); `check_winding.py` 0; every LOD keeps 1.70 m, Attack's lowest point
-3.1 mm at LOD0 as the source.

## Status

Not installed; awaiting user review. To adopt it, install `export/mm7_m290.glb` in place of the production export
(command and binding in `../mm7_m290_claude/README.md`; the binding is unchanged). Rollback source:
`work/mm7_m290_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_NODE=M290, REA_GLB=the rollback source) -> `dump_mesh.py` -> `dump_faces.py` ->
label transfer from `rig_v6.blend` (`work/src_labels.npz` -> `work/face_labels.npz`) -> `head_visible.py` ->
`make_groups_m290.py` -> keep_b = keep_base + group 6 -> ladder b (`REA_KEEP_FACES=work/keep_b.npy
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.65,2:0.35,3:0.55,4:0.85,5:0.92 REA_HEIGHT_M=1.70 run_ladder.sh b 0.77`) ->
`REA_CAND=Cand_77 REA_ERR_MM=15 REA_LOCK_R=0.02 err_lock.py -- work/keep_b.npy work/keep_c.npy` -> `spot_lock.py
work/keep_c.npy work/keep_f.npy 0.02 -0.036,-0.125,1.579 0.01,0.057,1.045` -> ladder f (`REA_KEEP_FACES=work/keep_f.npy
REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.6,2:0.3,3:0.5,4:0.82,5:0.92 REA_HEIGHT_M=1.70 run_ladder.sh f 0.75`) ->
checks (`texture_drift.py`, `dark_slivers.py`, `visible_only.py`, `group_error.py`, `close_monk.py`, `close_sheet.py`)
-> build as above -> `lod_check.py`, `glb_close.py` -> `viewer_variants.py` (r100 source, r75 reduced).

## Gait rollout (2026-10-31)

Package h08 of [the gait rollout](../gait_rollout_20261031/README.md) appended `Jog` (humanoid set Armed-Run-Forward,
0.80 s, stride 2.6533) and `Sprint` (Unarmed-Sprint, 0.60 s, 3.4373), robe-safe (low swing, arms kept folded) with the
robe simulated on the new motion (a numpy port of `../mm7_m290_claude/scripts/robe_sim.py`), to the installed
`mm7_m290.glb` (existing clips byte-identical) and installed it. Bindings for the coordinator: `run: Jog`,
`run_stride_length: 2.6533`, `sprint: Sprint`, `sprint_stride_length: 3.4373` (the walk-as-run `run: Walking` is
replaced: the Monk's chase, 3.65-4.38 u/s, is a run pace) (`../gait_rollout_20261031/h08/bindings.yml`). Rebuild:
`../gait_rollout_20261031/h08/scripts/rebuild.sh m290`; details and gates in
[the package README](../gait_rollout_20261031/h08/README.md). A far-LOD repair rerun or any re-export of this model
must re-graft these clips (rerun that rebuild on the new source).

## Anim fix (2026-11-11, MM6–MM8 audit)

Jog and Sprint recomposed with shorter, quicker strides and narrower robe leg capsules: cloth bad 33.2 -> 15.4 % and
33.7 -> 18.0 %; strides 2.2145 / 2.6915. Details: [mm7_m290_animfix_claude](../mm7_m290_animfix_claude/README.md).
