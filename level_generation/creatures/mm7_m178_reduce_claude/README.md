# MM7 Devil (`m178`, Devil Worker / Devil Warrior / Devil Captain) reduction (2026-10-21)

User request (batch F): "handle batch F ... check if they had their tris reduced". The Devil had not (LOD0 9,977).
Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding,
so the textures, region mask, tier ramps, rig and clips stay as exported. No Meshy credits. Scripts copied from
`mm7_m234_reduce_claude/` (ladder, UV weights, LODs, LOD check, close-ups, viewer) and `mm7_m262_reduce_claude/`
(`find_doubles.py`, `drift_lock.py`); the gates `g6_contacts.py`, `stretch_all.py`, `sole_probe.py`, `head_bob.py`
and `shrink_shadow_lods.py` are copies from `mm7_m178_claude/scripts/`. Batch rules: nothing installed, nothing in
`assets_dev/` or `assets_source/`, `mm7_m178_claude/` untouched. Every Blender/Python step runs memory-capped
(`scripts/cap.sh`).

Source: `../mm7_m178_claude/export/mm7_m178.glb` (2026-10-20 13:59, after the "Feet and walk fix" and "Attack feet"
reviews; `export_info.json` names the intermediate `mm7_m178_lod0.glb` of the same build, the final file is the LOD +
variant + head-merged `mm7_m178.glb`), sha256 `17e2bcc1…`, copied to `work/mm7_m178_source_pre_reduce.glb` (rollback
source). One node `Devil`, one material `Devil_A` (body + head merged into a 2080x1024 atlas) with the tier variants
`Devil_B` / `Devil_C` (two regions: hide, slate plates), 8 clips. The origin stays where the source export put it
(between the Standing soles and the pelvis, 0.626 m behind the working frame): the candidate is swapped into the
source GLB, so node transforms, inverse bind matrices and clips are byte-identical.

`import_source.py` (REA_NODE=Devil): weld 6,499 -> 69 open edges, 0 coincident vertices with other weights; no
two-sided reversed copies (`find_doubles.py`: 0), all 9,977 triangles kept. Rest height 1.70 m (limits p99 5.1 mm,
max 25.5 mm).

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch F export | 9,977 | 4,988 | 1,782 | 579 |
| **reduced** (`export/mm7_m178.glb`) | **6,981** (-30 %) | 3,489 | 1,802 | 575 |

`export/mm7_m178.glb`, 7.6 MB, sha256 `78d564d99fd1b7c8f58e05e403422aaf75a43bda38191fce3927395125b07592`. Nodes,
materials (with region mask and ramps), textures, images, skins, inverse bind matrices, `KHR_materials_variants`
(`m178_a/b/c` on all 8 colour and shadow primitives) and all 8 clips are identical to the source (checked JSON and
binary). The LODs use 4 influences (the source LOD1-3 had 8), as the other reduced MM7 models. No attachments (the
Devil is unarmed).

## Pieces and budgets (`make_groups.py`, `spikes.py`, masks in `review/masks/sheet_g2.png`, `sheet_s1.png`)

One closed skin (9,000 faces) and 22 small pieces (977 faces: 8 tooth pieces, 2 eyes, 12 tail spikes).

- **Kept exactly** (`work/keep_front.npy`, 2,387 faces): every small piece (teeth, eyes, tail spikes), the soles
  (301 faces with all vertices within 3 cm of the floor: the levelled feet stand on them) and the face front (1,109
  head-set faces in front of y = -0.15 below z = 1.58: brow, eyes, nose, lips, chin).
- **Own ratios (pick g):** head back, ears and horns (head texture set) 55 %, clawed hands 60 %, feet and toes 65 %,
  tail 60 %.
- **Rest (torso, arms, legs and their skin spikes):** the remaining budget (about 54 %).

Spikes (44 found with the source project's own thickness rule, `spikes.py`: horns, skull/shoulder/back/forearm
spikes, toe claws, heel spurs) were tried as their own group and kept exactly (configs b, c, d): both did worse. A
spike decimated alone with a fixed border lost more than in the shared cut, where the quadric error keeps the tips
anyway, and locking them pushed the cut onto the hands and thighs (p99 6.5-7.5 mm at r72).

## Ladder (REA_HEIGHT_M 1.70: p99 <= 5.1 mm, max <= 25.5 mm; IoU >= 0.98, SSIM >= 0.93)

| config | groups | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---|---:|---|---|---|---|
| a | head 60, hands 55, feet 70, tail 70 % | r75 / r72 | 7,481 / 7,181 | 4.52 / 16.1, 4.75 / 16.1 | 0.987 / 0.984 | 0.995 / 0.994 | pass |
| a | | r70 | 6,981 | 5.05 / 21.8 | 0.983 | 0.993 | pass |
| a | | r69 / r67 | 6,883 / 6,683 | 5.20 / 21.8, 5.58 / 23.8 | 0.983 / 0.980 | | fail |
| b | a + spikes 80 % | r72 | 7,179 | 5.47 / 24.9 | 0.983 | 0.992 | fail |
| c | a + spikes kept | r72 | 7,179 | 6.48 / 30.3 | 0.984 | 0.992 | fail |
| d | a + spikes 65 % | r75 | 7,479 | 6.24 / 27.3 | 0.983 | 0.993 | fail |
| e | hands 50, feet 65, tail 60 % | r72 / r70 | 7,181 / 6,981 | 5.12 / 16.1, 5.21 / 16.1 | 0.985 / 0.983 | | fail (p99) |
| f | a + error lock (19 posed misses > 10 mm, 2.5 cm) | r70 | 6,981 | 5.16 / 20.5 | 0.982 | 0.993 | fail (the lock moved the error) |
| g | head 55, hands 60, feet 65, tail 60 % | r72 | 7,181 | 4.69 / 16.1 | 0.984 | 0.994 | pass |
| **g** | | **r70** | **6,981** | **4.93 / 21.8** | **0.983** | **0.993** | **picked** (lowest passing step) |
| g | | r68 | 6,781 | 5.25 / 21.8 | 0.981 | 0.992 | fail |

The 21.8 mm maximum (Running) is one calf spike behind the right leg at a single posed frame; at rest and in the
close-ups the spike reads as the source's. Close-ups (source | r72 | r70, Eevee textured and clay):
`review/close/sheet_g1_*.png` (face front, three-quarter, profile and mouth, horns from above, head and shoulder
spikes from behind, chest, arm spikes), `sheet_g2_*.png` (legs, heel spurs, hips, tail root, tail, Attack, Running,
Death), `sheet_g3_*.png` (both clawed hands, the claws at the blow, both feet). Straight from the GLBs (own smooth
normals): `review/glbclose/sheet_r70_a_tex.png`, `sheet_r70_a_clay.png` and tiers B and C `sheet_r70_bc_tex.png`.
No feature changed: horns, spikes, teeth, claws, heel spurs and tail spikes keep their length; the fingers are
slightly more angular in untextured close-ups.
Texture drift (`texture_drift.py r70`): 1 face over 40 (2.8 cm², p99 16.7). Dark slivers (`dark_slivers.py r70`):
52 small faces (1.5-6.6 cm²) at the bases of the forearm spikes and one neck spike; the close-ups at 25 cm framing
show the spike bases a little blotchier, nothing at viewing distance, so no drift-lock round.

## Build

`REA_EXT_M=0.001 REA_FLOOR_FROM=0.6 REA_FLOOR_M=0.004 scripts/build_export.sh Cand_70` (with `work/ladder.blend` =
`work/ladder_g.blend`): `export_cand.py` (9 new sole vertices up to 0.6 mm under the floor lifted onto it) ->
`swap_lod0.py` (into the rollback source) -> `build_lods.py` (0.5 / 0.26 / 0.085; protected: the extreme vertices
within 1 mm of the bounds and the floor contact within 4 mm of the last 40 % of Death and of Dead, 148 points) ->
`shrink_shadow_lods.py` (the source project's margins) -> `carry_variants.py` (7 primitives).
The batch-default LOD locks (5 mm extreme bands, Standing soles, 1-3 cm floor) held 400-800 points for a 575-triangle
LOD3, and the collapse then built head-to-body sheets (`review/lods/` first round, caught in the textured LOD views,
not by the LOD check); the leaner lock gives LOD1-3 that match the source's (`review/lods/lod_sheet.png`: source and
reduced LOD0-3, Standing three-quarter, the Attack blow, head and right hand).

## Gates (GLB gate copies of source and reduced, `scripts/gates.sh` -> `work/gates_final.txt`)

| gate | source | reduced |
|---|---|---|
| G4 stretch p99, arm / leg / trunk / tail (all clips) | <= 1.77 / 1.44 / 1.58 / 1.35 | <= 1.75 / 1.40 / 1.62 / 1.46 |
| G4 stretch max (all clips) | 2.93 (Death upper arm) | 2.93 (the same) |
| G5 hands (rigid, wrist band) max | 2.0 (Attack) | 2.0 |
| G6 contacts, worst depth cm | Run 4.1, Attack 4.2 / 3.9, Hit 2.4, Death 6.0 | Run 4.2, Attack 3.9 / 3.8, Hit 2.1, Death 5.9 |
| Soles: Standing / Attack / Fidget / Hit | -0.0..0.0 / -0.1..0.1 / -0.0..0.0 / -0.2..0.1 cm | identical |
| Soles: Walking / Running | -0.8..1.0 / -1.3..3.1 cm | identical |
| Stance sole roll Standing / Walking / Running | L 0.2, R -0.2..-0.1 / L 2.6..9.4, R -18.2..8.6 / L -5.3..11.4, R -27.3..11.0 deg | L 0.2, R -0.2 / L 2.6..9.4, R -18.3..8.5 / L -5.3..11.4, R -26.4..11.0 deg |
| LOD check: lowest point Dead (LOD0-3) | -0.1 / -0.1 / -0.1 / +0.5 cm | -0.1 / -0.1 / -0.1 / -0.1 cm |
| LOD check: lowest point Death (LOD0-3) | -2.1 / -2.2 / -2.5 / -2.9 cm | -1.8 / -1.8 / -1.8 / -1.8 cm |
| LOD check: stretched faces (any LOD, any clip) | 1 (LOD1) | 0 |
| LOD check: rest bounds | 1.30 x 1.70 x 1.70 m at every LOD | the same at every LOD |
| winding (`check_winding.py`) | 0 inverted | 0 inverted |

The gate copies are imported from GLB at 24 fps, so frame numbers differ from the source project's 30 fps gate runs;
both columns use the same import. The garment labels (0 skin, 1 teeth/eyes, 2 tail spikes) are rebuilt on each gate
copy (`gate_attrs.py`), because the master's rest frame is the working frame before the origin shift. Jerk is a
bone-only gate and the clips are unchanged, so it was not re-run.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m178_reduce_claude/review/viewer/`: batch F export (r100) and
the reduction (r70, default), tiers A, B and C (ramps baked by `viewer_tiers.py`), the source project's clips.
`python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m178_reduce_claude check`: 48 clip
switches, no console errors.

## For the user to review

- 30 % off LOD0 (9,977 -> 6,981), at the upper end of the aim; the face front, teeth, eyes, tail spikes and soles are
  exact.
- The fingers are a little more angular than before in untextured close-ups (hands at 60 %); textured they read the same.
- The forearm spike bases have a few slightly blotchy texels at very close range (dark-sliver check, 52 small faces).
- LOD3 keeps the batch F budget (575); its tail spikes vanish as in the source LOD3.

## Install (not run)

Replaces the batch F export of `mm7_m178_claude/` (same nodes, materials, variants and clips; no attachments):

```sh
python3 level_generation/decorations/mm8_3d/animated/scripts/check_winding.py level_generation/creatures/mm7_m178_reduce_claude/export/mm7_m178.glb
python3 tools/install_model.py level_generation/creatures/mm7_m178_reduce_claude/export/mm7_m178.glb --world mm7
```

The `actors.yml` binding is the source project's staged
[`../mm7_m178_claude/actors_m178_binding.yml`](../mm7_m178_claude/actors_m178_binding.yml) (descriptors Devil A/B/C,
`worlds/mm7/models/mm7_m178.glb`, scale 107.9, strides 1.878 / 2.063, blow 0.750 s, `claw_r` socket on `B_R_Hand`):
it applies unchanged, add it to `assets_dev/worlds/mm7/models/actors.yml` as that README describes. Rollback:
`work/mm7_m178_source_pre_reduce.glb` (identical to the batch F export).

Reproduce: `find_doubles.py`, `import_source.py` (REA_GLB=…/work/mm7_m178_source_pre_reduce.glb, REA_NODE=Devil),
`dump_mesh.py`, `dump_faces.py`, `dump_weights.py`, `make_groups.py`, `spikes.py` (for configs b-d),
`REA_WEIGHTS=component REA_KEEP_FACES=work/keep_front.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.55,2:0.6,3:0.65,6:0.6 scripts/run_ladder.sh g 0.72,0.70,0.68`, `close_m178.py -- ladder_g.blend
Cand_72,Cand_70`, `pair_sheet.py`, `texture_drift.py r70`, `dark_slivers.py r70`, `cp work/ladder_g.blend
work/ladder.blend`, the build above, `lod_check.py` (REA_NODE=Devil) on both GLBs, `lod_views.py -- source,reduced`,
`gates.sh`, `glb_close.py`, `viewer_tiers.py <glb> r100|r70`, `viewer_manifest.py`.

## Knee fix rebuild (2026-10-21)

The source export was rebuilt with the attack knee fix (`../mm7_m178_claude/README.md`, "Knee fix") and copied to
`work/mm7_m178_source_pre_reduce.glb`; the build above was rerun unchanged and installed. Only Attack differs.
Previous files: `work/mm7_m178_source_pre_reduce_prekneefix.glb`, `work/mm7_m178_reduced_prekneefix.glb`.

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h12`](../gait_rollout_20261031/h12/README.md) appended Walk2 (Mixamo Mutant Walking, the
`Walking` source, at a brisker 1.0 s loop) and Jog (humanoid set Unarmed-Run-Forward legs, 0.68 s, arms and tail from
`Running`) to the installed `assets_source/worlds/mm7/models/mm7_m178.glb` and installed it (existing clips, meshes,
skins and materials byte-identical). Bindings (`h12/bindings.yml`): walking: Walk2, stride_length 2.1506, run: Jog,
run_stride_length 2.9536. `Walking` and `Running` stay in the GLB, no longer bound for locomotion.
Rebuild: `level_generation/creatures/gait_rollout_20261031/h12/scripts/rebuild.sh m178` (from `h12/work/mm7_m178_pre_gait.glb`, the
rollback source). A far-LOD repair rerun, a floor fix or any re-export of this model must re-graft these clips: copy the
new source over `h12/work/mm7_m178_pre_gait.glb` and rerun the rebuild, then install with `tools/install_model.py`.
