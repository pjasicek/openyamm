# MM9 Cow (`mm9_cow`, Cow / Brown Cow) reduction: ready for review, 2026-11-05

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 71 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:cow` (owner cow-reduce-20261105); `mm9:cow` was free.
Source: the installed `assets_source/worlds/mm9/models/mm9_cow.glb` (sha256 c4f66a1c0477, identical to
`../mm9_cow_claude/export/mm9_cow.glb`), copied to `before/` (rollback). `../mm9_cow_claude/` was only read. No Meshy, no credits.
Not installed.

**Result: candidate c74, LOD0 8,544 -> 7,164 (-16.2 %), LOD1-3 4,272 / 1,536 / 512 -> 3,582 / 1,288 / 426.**
`export/cand_c_r74/mm9_cow.glb` (sha256 357780a36e77). Every output vertex is an installed one (half-edge collapse, index
buffer swap): positions, UVs, normals, weights, clips, skin, images, materials, ramps and both tiers byte-identical
(`same_clips.py`).

## Note: the body was already decimated at the build
`../mm9_cow_claude/scripts/reduce_mod.py` cut the 200k-quad solid body to about 7k with a Decimate modifier; the head was left
denser (14-19 mm edges against 50-70 mm on the body). The head bones (Xheadpiv, Xhead, Xjawpiv, ears) weight 4,538 of the 8,544
faces, so most of the gain had to come from the dense upper neck behind the ears, not from the body.

## Keep set (`scripts/cow_sets.py`; animal reading of the face rule)
Exact: the head in front of z 0.85 (the ears' roots lie at z 0.83-0.93, the eyes at 0.995, the muzzle tip at 1.25) = eyes, lids,
muzzle, nostrils, lips, the 682-face mouth cavity, poll and every ear face, plus two rings (3,758); the eyeballs (188), the four
teats (316), hooves plus one ring (392, rigid on the foot bones), soles within 3 cm of the floor, and 32 faces round the two
worst-error spots of ladder b (belly midline above the udder, top of the neck; `scripts/err_lock.py`). Protected share 54.8 %.
Cut: the head-weighted upper neck behind z 0.85 (784 -> 234, ratio 0.3), the body, legs and tail tube (2,858 -> 2,114, 0.74),
the tail tassel (216 -> 130, 0.6).

## Ladders (`scripts/mpqem.py`: Terror copy + the Imp's chart guard, texture guard on the region mask G/B/A and the base colour,
W5 3; limits for the 1.53 m standing height p99 <= 4.59 mm, max <= 22.95 mm; `work/selection_{a,b,c}.json`,
`review/ladder_sheet_{a,b,c}.png`)
| set | groups | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | face to z 0.80; neck .5, tassel .6, teats .7, MAXW 0.1 | r80 / r70 / r60 | 7,516 (-12.0 %) / 7,228 / 6,940 | 3.11/19.2, 4.61/34.7 (Standup2:21), 6.28/34.7 | .998/.999 | pass / fail / fail |
| b | face to z 0.85, teats exact; neck .35, tassel .6, MAXW 1.0 | r78 / r74 / r70 | 7,312 (-14.4 %) / 7,196 / 7,080 | 3.62/19.2, 4.22/23.04 (Tipover2:33), 4.78/23.04 | .997/.999 | pass / fail (max +0.09) / fail |
| c | b + error lock (2 spots, 32 faces); neck .3 | **r74** / r72 / r70 | **7,164 (-16.2 %)** / 7,108 / 7,050 | **4.41/17.7** (Standup:6), 4.62/17.7, 4.99/17.7 | .997/.999 | **pass** / fail / fail |
Error at a r70 (`err_by_bone.py`): rump XbackC 0.49 % of samples over the limit, back Xback max 34.7 mm; head bones under 0.01 %.

## Candidate build (`scripts/build_cand.sh c_r74`)
`swap_mp.py` (LOD0 index buffer) -> `build_lods.py` (the snap-fixed Lesser Demon/Terror builder, the tool's 0.5/0.18/0.06 as the
cow was built; protected: soles, top, tassel and ear tips, hoof extremes, axis extremes, corpse contact of Death/Death2/Dead;
79 of 79 points snapped, worst 2.8e-7 m) -> `shrink_shadow_lods.py` (the cow's own) -> `carry_variants.py`. Clips unchanged, so
the floor pass is not re-run.
- UV chart audit (`review/uv_audit_c_r74.json`): **LOD0 0 escaping**; LOD1/2/3 129/217/98 against the installed 102/206/141
  (Blender decimate's own baseline).
- LODs (`review/lod_table_c74.txt`, `scripts/lod_check.py` every frame of every clip): top 1.539 m at every LOD; LOD0's lowest
  point identical to the installed in all 15 clips; LOD1-3 now follow LOD0 (installed LOD2 sank 0.5 cm in Standing/Fidget/Hit,
  LOD3 0.7 cm in Dead/Death); worst new drift Walking LOD2/3 +0.12 cm. Stretched faces 0 at every LOD.

## Gates (`scripts/gates.sh`, `review/gates_before/`, `review/gates_c74/`, `review/gates_compare_c74.txt`)
Installed -> c74 (the cow project's gates: gates.py, extra_clip_gates.py on all 15 clips, fold_measure.py, detached parts, flat
shading, texture quality, winding, same_clips):
- Floor (hoof contact): lowest/highest point per frame identical in all 15 clips (e.g. Standing 0.0/0.0, Walking -0.0/2.4,
  Standup -1.7/12.3 cm as installed); LOD0 lowest point per clip identical to 0.01 cm (`lod_table_c74.txt`).
- Jitter p99 (mm/f2): within +-3 % per clip, most lower (Running 361.4 -> 359.4, Tipover2 285.0 -> 277.3); highest rise Hit
  86.5 -> 88.7. Bone ratio identical (clips unchanged).
- Body in body (pairs): single-pair noise (+1 to +3 in Walking, Fidget, Hit, Dead, Fidget3, Tipover), fewer in Running 57 -> 44,
  Death 70 -> 55, Standup 67 -> 59, Tipover2 78 -> 72.
- Edge stretch: min/max identical in every clip, p99 within 0.06 (Standup2 2.068 -> 2.127, Death 2.145 -> 2.204); loop seams 0.
- Folds (`fold_measure.py`): total over-threshold 139,037 -> 128,796; neck 641 -> 705 (fewer, larger faces), hips/tail 34,353
  -> 29,826, head 122,288 -> 122,223.
- Detached: 0 in every pose (as installed); tassel root shallow note 6.7 mm -> 3.7 mm.
- Flat shading 0.02 = 0.02; texture quality atlas 59.9 %, spread 1.19, stretch p90 1.08 -> 1.09; winding 0 inverted; clips, skin,
  nodes, materials, images byte-identical.
The cow has no arms, hands, held props, sleeves or see-through fix, so those gates do not apply.

## Review
Viewer (installed and reduced, both tiers, 15 clips):
http://127.0.0.1:8912/level_generation/creatures/mm9_cow_reduce_claude/review/viewer/
`run_creature_review.py check`: 60 switches (4 models x 15 clips), 0 failed, 0 console errors.
Sheets read at full size: `review/sheet_face_c74.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers, installed
over reduced), `review/face_diff_a_c74.png` (|installed - reduced| x4, tier A: eyes, muzzle, nostrils, mouth, ears black; only
the neck behind the head and its silhouette differ), `review/neck_patch_c74_a.png` (2x crop of the patch border on the cut neck:
painting intact, shading slightly smoother), `review/sheet_body_c74_{a,b}.png` (Standing front/3-4/back, Walking, Running,
Death), `review/sheet_close_c74_{a,b}.png` (neck side/above-behind/Fidget, udder, rump, Standup2 rump, hooves),
`review/tassel_c74_a.png`. Face numbers: `review/face_diff_c74.txt` (centre box >8: 0.03-0.60 %, the max 207 is the viewer's
label text). No visible change at party distance. Look at: the upper neck (crest line, 0.3) and the root of the tail tassel
(0.6: one tip at the join instead of two in the 0.6 m close-up).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_cow_reduce_claude/before/mm9_cow.glb REA_NODE=Cow $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py
TASSEL_GROUP=2 TEAT_GROUP=3 $G scripts/cow_sets.py a
SETS=a MP_SEAM_GROUPS=0,1 MP_W5=3 MP_GROUPS=1:0.5,2:0.6,3:0.7 REA_HEIGHT_M=1.53 scripts/run_mp.sh a 0.8,0.7,0.6
FACE_Z=0.85 TASSEL_GROUP=2 $G scripts/cow_sets.py b
SETS=b MP_SEAM_GROUPS=0,1 MP_W5=3 MP_MAXW=1.0 MP_GROUPS=1:0.35,2:0.6 REA_HEIGHT_M=1.53 scripts/run_mp.sh b 0.78,0.74,0.7
$G -c "import numpy as np; np.save('work/keep_zero.npy', np.zeros(8544, bool))"
REA_BLEND=ladder_b.blend REA_CAND=Cand_74 REA_ERR_MM=18 REA_LOCK_R=0.04 $BL -P scripts/err_lock.py -- work/keep_zero.npy work/keep_extra_err74.npy
FACE_Z=0.85 TASSEL_GROUP=2 $G scripts/cow_sets.py c err74
SETS=c MP_SEAM_GROUPS=0,1 MP_W5=3 MP_MAXW=1.0 MP_GROUPS=1:0.3,2:0.6 REA_HEIGHT_M=1.53 scripts/run_mp.sh c 0.74,0.72,0.7
scripts/build_cand.sh c_r74
scripts/gates.sh before/mm9_cow.glb before; scripts/gates.sh export/cand_c_r74/mm9_cow.glb c74; python3 scripts/gate_compare.py c74
REA_NODE=Cow $BL -P scripts/lod_check.py -- $PWD/before/mm9_cow.glb installed   # and the candidate as c74; python3 scripts/lod_table.py installed c74
$G scripts/viewer_tiers.py before/mm9_cow.glb inst; $G scripts/viewer_tiers.py export/cand_c_r74/mm9_cow.glb red   # then make_viewer_manifest.py
scripts/shots.sh; python3 scripts/shot_sheets.py c74
```
Install (orchestrator, after the pre-screen): `check_winding.py export/cand_c_r74/mm9_cow.glb` (0), copy it to
`export/mm9_cow.glb`, `tools/install_model.py export/mm9_cow.glb --world mm9`, the `mm9_actor_models_build_every_binding`
regression, `floor_audit.py --world mm9` (Cow, Brown Cow), and add to `../mm9_cow_claude/README.md`: "LOD0 reduced post-install
on <date> by `mm9_cow_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_cow.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); tier B's tassel close-up (tier A read; B shares the mesh);
the head/orientation and gait gates of the creature project (they read only the clips, which are byte-identical).
