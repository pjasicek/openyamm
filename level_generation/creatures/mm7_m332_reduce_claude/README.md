# MM7 Peasant Elf Male (`m332`) reduction (2026-10-20)

User: "OK reduce tris count now" (the five MM7 batch-J peasants; this project is m332 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: texture-aware MeshLab ladder that keeps the
UVs, so the textures, the nine looks (`KHR_materials_variants`) and the region ramps stay valid. No Meshy credits.
**Not installed** (batch J: the user installs later). Scripts start from `../mm7_m410_reduce_claude/scripts/` (paths,
node `Elf`, height; the Thief's own piece/set scripts replaced by `m332_pieces.py`, `m332_sets.py`).

[Review viewer](review/viewer/index.html) (source vs reduced, all nine looks, six clips)

## Source

`../mm7_m332_claude/export/mm7_m332.glb` (after the 2026-10-20 walk and ankle fix; sha256 783f49be...), copied to
`work/mm7_m332_source_pre_reduce.glb` (rollback source, byte-identical). One merged body + head atlas material per look
(`Elf_A1`…`Elf_C3`, 2080x1024, region mask R tights, G hair), node `Elf`, 56 joints, shadow LODs, clips Standing,
Walking, Hit, Death, Dead, Fidget. Bind height 1.7517 m (ladder limits p99 5.26 mm, max 26.3 mm; IoU >= 0.98,
SSIM >= 0.93). Weld (identical weights only): 6,192 -> 392 open edges, no coincident vertices with other weights,
11,070 triangles in and out.

## Where the triangles are (`scripts/m332_pieces.py`: the production master's Smart Topology `piece` attribute, mapped by rest position, max 0.0008 mm)

| piece | faces | |
|---|---:|---|
| skin shell (body, head with painted hair, bracers, shoes) | 4,700 | tights 1,054 (mask R), painted hair 322 (mask G), soles 343 |
| hands L / R (separate shells; a sixth finger was removed and capped in the build) | 1,251 / 1,190 | kept exactly |
| vest | 799 | |
| dagger and sheath (6 pieces) | 682 | kept exactly except the 216-face hilt piece |
| vest studs (9) / lacing crosses (8) | 624 / 606 | kept exactly |
| ponytail | 499 | |
| belt / buckle / right arm band / eyes | 399 / 78 / 118 / 124 | kept exactly |

## Keep set and groups (`scripts/m332_sets.py` + patches, pick = set `i`)

Kept exactly (`work/keep_i.npy`, 6,804 faces): both hands (every face touching a vertex with hand + finger weight > 0.3,
the capped finger stump included), studs, lacing, belt, buckle, the dagger pieces except the hilt, the arm band, the
eyes, the soles (skin faces below 6 cm), the visible face front (eyes, nose, mouth: head skin seen in some view, in front
of y = -6 cm, |x| < 7.5 cm, above z 1.48; 760 faces), every skin face on a painted region edge (mask R or G between 0.1
and 0.9: the tights' waist and ankle edges, the hairline; 90 faces), the skin never seen from outside (under the vest,
belt and band: 366 faces; decimated it poked through the vest back as pink chips), one drift-lock round (3 cm around
the drifted faces of the e ladder) and 2.5-3 cm patches (`patch_keep.py`, mirrored) at both vest armholes (dark marks)
and at the torso sides under the armholes plus the waist interior (source vertices with clavicle weight low on the
torso, 28 mm apart in the Death fall).

| group | faces | ratio |
|---|---:|---|
| 1 visible head sides and back (ears, painted hair) | 695 | 45 % |
| 2 hidden head skin | 162 | 55 % |
| 3 vest (outside the patches) | 580 | 62 % |
| 4 ponytail | 499 | 50 % |
| 5 tights | 1,044 | 55 % |
| 7 dagger hilt piece | 216 | 60 % |
| free (bare arms, chest V, neck, bracers, shoe uppers) | 1,070 | 60 % |

## Ladder (`review/ladder_sheet_<config>.png`)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 11,070 | | | | |
| a: hidden body skin 35 % | r84-r81 | 9,460-9,118 | 4.85-6.6 / 26.7 | 0.992-0.988 | | fail (max: interior torso skin under the vest, 24 mm even in Standing) |
| b: hidden skin 70 %, hidden head 60 % | r86 / r84 / r83 | 9,568 / 9,340 / 9,226 | 3.98 / 4.87 / 5.69 | 0.992-0.988 | 0.997-0.994 | pass to r84 |
| c: head sides 45 %, ponytail 50 %, vest 62 %, tights 55 % | r82 / r81 | 9,176 / 9,062 | 4.84 / 5.15 | 0.991 / 0.990 | 0.995 | pass |
| d: harder head and vest | r82 | 9,118 | 5.58 | | | fail |
| e: c + dagger hilt 60 % | r81 / r80 | 9,088 / 8,974 | 4.84 / 5.16 | 0.991 / 0.990 | 0.995 | pass; yellow and dark flecks on the vest (drift 12 faces, 39.5 cm2 visible) |
| f: e + drift lock | r82 | 9,140 | 5.04 / 23.9 | 0.991 | 0.995 | pass; dark marks at both vest armholes |
| g: f + armhole patches | r82 | 9,202 | 5.00 / 28.4 | | | fail (max: torso side under the right armhole, Death) |
| h: g + torso-side patches | r82 | 9,190 | 4.97 / 24.2 | 0.991 | 0.995 | pass; pink skin chips through the vest back (hidden skin cut) |
| **i: h + hidden body skin kept** | **r83** | **9,284** | **4.79 / 20.5** | **0.9905** | **0.9949** | **pick** |
| j: i with vest 70 %, tights 65 % | r84 | 9,328 | 4.92 / 18.6 | 0.991 | 0.995 | pass; no fewer slivers, more visible drift |

The pick is the lowest configuration that passes the ladder and looks like the source in the textured and clay
close-ups. Texture drift (`texture_drift.py` + `drift_visible.py i_r83`, visible faces): 8 faces over 40 (14.8 cm2),
two over 3 cm2 (on the back of the right upper arm, 8.4 and 13.6 cm2); one small skin-coloured chip remains on the
vest back. Slivers and long faces (`sliver_vis.sh i_r83`): 30 new slivers (2.5-7 cm long, 0.6-4 mm high; most on the
vest shoulders, head sides and hidden head skin) and 6 new long faces (vest shoulders 13 cm, thigh fronts 17-24 cm,
ratio 3-4); none shows in the close-ups or the viewer.

## Build

`REA_KEPT_NORMALS=1 cand_glb.sh i Cand_83 kn` (source GLB normals on the unchanged source faces and kept smooth
vertices, computed smooth normals elsewhere) -> `work/i83_lod0.glb` -> `REA_CAP_Z=1.72 cap_points.py` (head-top points)
and `REA_NODE=Elf floor_points.py` (24 Dead/Death floor contacts) -> `REA_LOD_RATIOS=0.5,0.21,0.07 build_lods.py`
(`tools/build_actor_lods.py`, 37 protected points) -> `../mm7_m332_claude/scripts/shrink_shadow_lods.py`
(`MESH_NODE=Elf`; shadow LODs inset up to 15 mm) -> `carry_variants.py` (7 primitives) -> `check_winding.py`
(0 inverted closed parts): `export/mm7_m332.glb`, 7.50 MB (source 7.78 MB).

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 11,070 | 5,533 | 1,989 | 654 |
| reduced body | **9,284** | **4,641** | **1,949** | **640** |

Checks:
- `compare_glb.py`: nodes, skin, materials and extras, images, all six clips and the variants identical to the source;
  `KHR_materials_variants` on all 8 colour/shadow primitives. `DIFFERENCES none`.
- `grip_check.py` (`work/grip_check.log`): all 1,819 hand vertices keep their bind positions (max 0.0008 mm) and weights.
  `kept_check.py` (`work/kept_check.log`): belt, buckle, arm band, studs, lacing and eyes unchanged (<= 0.0004 mm, no
  weight differences).
- `lod_check.py`: lowest point per clip within the source's at every LOD (LOD0 Dead +4.7 vs +0.8 mm, LOD3 Dead +0.7 mm);
  top 1.7537 m at every LOD (source 1.750); one LOD2 face stretches over 20x in Dead, Death, Hit and Walking (also at
  LOD2 ratios 0.20 and 0.23; source LOD2 none); LOD renders `review/lods/sheet.png` (source vs reduced per level).
- Close-ups straight from the GLBs, source vs candidates, textured and clay (`glb_close.py`, `glb_sheet.py`):
  `review/glbclose/sheet_i83_a.png` (head side/back, ponytail, torso, back, vest, arm, elbow back),
  `sheet_e_head.png`, `sheet_e_body.png`, `sheet_e_legs.png`, `sheet_f_head.png`, `sheet_f_body.png`,
  `sheet_h82_a.png` (the flecks each correction removed).
- Viewer (`viewer_variants.py`, `viewer_manifest.py`): `python3 tools/run_creature_review.py --project
  level_generation/creatures/mm7_m332_reduce_claude check`: 108 switches (9 looks x source/reduced x 6 clips), no
  console errors; viewer shots of looks A3, B2, C3 (`review/shots_tiers.png`).

## Open points for review

- The cut is modest (-16 %): 61 % of the mesh is kept exactly (hands 2,441, studs, lacing, dagger, belt, the face
  front, hidden skin). Cutting the hands or the studs and lacing would need a different route (they taper at any cut).
- Slivers on the vest shoulders and long faces on the thigh fronts (see Ladder): not visible in the close-ups.
- One small skin chip on the vest back and two drifted faces on the back of the right upper arm.
- The viewer's head focus is framed for a 1.8 m body (top of the head only); the head close-ups are in `review/glbclose/`.

## Install (not run; user decision)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m332_reduce_claude/export/mm7_m332.glb --world mm7
```

then the binding from `../mm7_m332_claude/README.md` (unchanged by this reduction) and a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row. Rollback: install `work/mm7_m332_source_pre_reduce.glb` the same way.

## Reproduce

`REA_GLB=<abs path of work/mm7_m332_source_pre_reduce.glb> REA_NODE=Elf import_source.py` -> `dump_mesh.py`,
`dump_groups.py`, `extract_basecolor.py work/mm7_m332_source_pre_reduce.glb` -> `dump_master_pieces.py` ->
`m332_pieces.py` -> `visibility.py -0.01 1.76` (copy to `work/visible_all.npy`) and `REA_MIN_PIX=6 visibility.py 1.40
1.76` (`work/visible_head.npy`) -> `m332_sets.py a` -> sheath hilt to group 7 (`keep_e`, `groups_e`) -> `run_ladder.sh e e
"1:0.45,2:0.55,3:0.62,4:0.5,5:0.55,6:0.6,7:0.6" 0.75,0.65` -> `drift_lock.py work/keep_e.npy work/keep_f.npy e_r81
e_r80` -> `REA_PATCH_R=0.025 patch_keep.py work/keep_f.npy work/keep_g.npy` (armholes, mirrored: 0.175,-0.104,1.314
0.177,-0.104,1.371 0.197,-0.053,1.425 0.196,0.082,1.357) -> `REA_PATCH_R=0.03 patch_keep.py work/keep_g.npy
work/keep_h.npy` (±0.157,-0.086,1.217 ±0.165,-0.051,1.196 -0.005,0.002,1.111) -> keep_i = keep_h | group 6 ->
`TOKEN=<lease> run_ladder.sh i i "1:0.45,2:0.55,3:0.62,4:0.5,5:0.55,7:0.6" 0.7,0.6,0.5` -> build as above. Blender
scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`); `decimate_tex.py` uses the batch's MeshLab venv.

## Installed (2026-10-20)

User: "OK accept all, to assets_source, assets_dev". `check_winding.py` 0 inverted closed parts; installed with
`tools/install_model.py ... --world mm7` (sources in `assets_source/worlds/mm7/models/` equal the exports; cooked
runtime copies in `assets_dev/worlds/mm7/models/`). Nine `actors.yml` bindings added to
`assets_dev/worlds/mm7/models/actors.yml` from the production README's template (descriptor -> palette -> skin from
`../mm7_m332/variants.json` and the ramps file); every skin, clip, look node and attachment checked against both GLBs.
Boot check: `7out02.odm` (Harmondale) with spawned peasants of all five batch J models, 185 outdoor actors textured,
no missing models and no errors in the log (`output/batchJ_boot/`). Ledger row added to `../REDUCTION_LEDGER.md`.

## Gait rollout (2026-10-31)

Package [h13](../gait_rollout_20261031/h13/README.md) appended one clip to the installed source
`assets_source/worlds/mm7/models/mm7_m332.glb` (every existing clip, mesh, skin and material byte-identical): `Jog`
(humanoid set Unarmed-Run-Forward legs; arms from Walking; 0.76 s), bound for the peasants' flight (Wimps flee at 2x Spd in both rulesets) as `run: Jog`,
`run_stride_length: 2.5024` (the package's `bindings.yml`, applied by the coordinator). Walking stays the wander clip.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h13/scripts/rebuild.sh m332`, then
`python3 tools/install_model.py level_generation/creatures/gait_rollout_20261031/h13/export/mm7_m332.glb --world mm7
--name mm7_m332.glb`. A far-LOD repair, head-bob or reduction rerun that re-exports this model must re-graft the Jog: copy
the new source over `h13/work/mm7_m332_pre_gait.glb` and rerun the rebuild.
