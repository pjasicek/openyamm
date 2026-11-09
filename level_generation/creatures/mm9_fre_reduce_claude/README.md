# MM9 Fre (`mm9_fre`, row 256, the goddess; one skin) reduction: candidate c r50 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 113 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) (prio 3 unique; user approved r78 on 2026-11-05, then "do all"). Lease `mm9reduce:fre`
(owner fre-reduce-20261105); the creature's own `mm9:fre` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_fre.glb`
(r78, sha256 4b30f56d7f7e, = `../mm9_fre_claude/export/`), copied to `before/` (the rollback source). No Meshy, no credits, no repaint.
**Not installed.** `../mm9_fre_claude/` and `../mm9_peasantf4_reduce_claude/` were only read (their scripts run read-only).

| | LOD0 | body (Fre) | head set (FreHead) | braid (FreHair) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed r78 | 14,596 | 9,404 | 4,733 | 459 | 7,263 | 2,611 | 867 |
| **c r50 (`export/mm9_fre.glb`, sha256 e364c77b4327)** | **12,284 (-15.8 %)** | 7,208 | 4,733 (installed triangles) | 343 | 6,111 | 2,198 | 790 |

Every LOD0 vertex is an installed vertex (positions, normals, UVs, joints, weights byte-identical; only index buffers change). Clips, skin,
nodes, materials (FreHair doubleSided, specular extras) and all 9 images are the installed bytes (`scripts/same_clips.py`). The whole new
head primitive (face, eyes, lids, circlet paint, the hair bob, r72's neck band and the bridge) keeps its installed accessors untouched.

## What is kept, what is cut (`scripts/make_sets_fre.py`)
Fre's body primitive is PeasantF4's body: the same 6,657 vertices on F4's paid UV layout (matched exactly by UV; 474 UV-shared vertices,
the sleeve-tube lining twins and coincident seams, assigned per UV group by position/normal/weights), 9,401 of 9,404 faces matched to F4's
faces. So the body takes PeasantF4's accepted reduction sets (`../mm9_peasantf4_reduce_claude/work/glb_sets_f.npz`, its m7 pick) unchanged:
kept exactly the sleeve-tube rim strips and caps, the job-8 bodice hole fills, the placket column, F4's painted trims, F1's short sleeves,
F1's hidden skirt lining, the soles, small pieces; the sleeve-tube lining (240) re-emitted from the cut outer tube through F4's twin map
(-> 160). Fre's own additions: the 3 unmatched body faces kept; body faces within 5 cm of the braid kept (100, 30 of them otherwise cut:
the braid's holder at bind, see ladder c); the head primitive kept whole. Protected share 48.5 % (+ the lining).
Groups (pose-aware `scripts/mpqem.py`, F4's ratios): hands 0.6 (every finger kept: collapses refuse to flip in any pose), skirt 0.7, sleeve
tube outer 0.8, legs 0.6, shoulders 0.7, MPFB arm 0.75, bodice 0.5 (stalls at 277 of 507), braid tube 0.75.
`mpqem.py` is F4's copy with node Fre, the texture guard on Fre's own base colours (pf_body_final, nh_braid_base; refuse > 100 any sample /
> 45 mean), texture weight W5 = 4, the Mummy's chart guard and the audit's own chart test (`reduction_uv_audit.Charts`) inside each collapse.

## Ladders (height 1.765 m: p99 <= 5.30 mm, max <= 26.5 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_{a,c}.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a r50 (= r40) | F4's sets and ratios, braid 0.75 | 12,254 (-16.0 %) | 2.26 / 21.8 (Hit:39) | .998 / .997 | PASS; gates equal or better, but `detached_parts_audit` lists a new advisory "root lift" 8.4 cm on the braid |
| b r50 | a with the braid kept whole | 12,370 (-15.3 %) | (not rendered; body = a) | | root lift still there: the braid's lift comes from the cut dress behind it, not from the braid |
| **c r50** | a + body faces within 5 cm of the braid kept | **12,284 (-15.8 %)** | **2.04 / 21.8 (Hit:39)** | **.998 / .997** | **PASS, picked: the braid roots on the dress as installed (no root lift)** |
Why the root lift: installed, the braid touches the dress behind it with most of its vertices, so the audit gives it no root to track; on a's
chordal back the contact fell under half and the swing off the back in Talk/Death read as a lift. Hair poke and the sheets showed nothing.

## Gates, installed -> c r50 (`review/gates_before/`, `review/gates_c50/`, `review/gates_compare_c50.txt`)
Jitter not re-run: clips byte-identical. Fre's `nh_poke.py` runs as `scripts/nh_poke_rt.py` (labels through the installed vertices).
- **UV audit** (`claude_shared/reduction_uv_audit.py`, `review/uv_audit_c50.{json,txt}`): **LOD0 0 escaping faces** (body, head, braid).
  LOD1-3 (Blender's decimate in the LOD tool): body 113 / 139 / 22, head 46 / 77 / 35, braid 15 / 12 / 4 against the installed LODs'
  107 / 138 / 98, 49 / 71 / 39, 12 / 17 / 12.
- Hair poke (neck, dress, braid through the new hair): 0.0 mm, 0 frames > 2 mm in all 11 clips, identical.
- Arm/hand (`--outer-only --exact`): 0 frames > 1 cm in every clip, hand/forearm maxima identical (Cower forearm 2.4 cm as installed);
  finger-stretch p99 up by at most 0.07, maxima equal or lower (Fidget L 2.03 -> 1.54, Talk R 2.40 -> 2.27, Conv1 R 2.35 -> 2.23).
- Robe identical; F1 short-sleeve poke identical (0 mm).
- Collapse face-frames 17,227 -> 13,546, lower in every clip; single-frame region rises: Walking armpit R 1 -> 2, Fidget elbow R 0 -> 2,
  Death neck 8 -> 11.
- Flat 0.00 / 0.00 / 0.00, bone lengths 0 stretching, winding 0, texture quality equal (body stretch p90 1.08 -> 1.09, braid 1.72 -> 1.74).
- Detached: the same 2 legs by design, same worst gaps (20.7 / 12.2 cm), detached in more poses (763 -> 828, 780 -> 784 of 838); no root lift.
- See-through (Fre's `see_through_gate.py`, every clip, 16 views; hole max px, level / party 20 deg): head 211 / 23 = 211 / 23, collar
  996 / 20 = 996 / 20, torso 1597 / 26 -> 1511 / 26, sleeve L 2004 / 8 -> 1988 / 8, sleeve R 4 = 4, boots 0 = 0, unattributed 1 = 1 px
  (50 -> 51 frames). The worst cases are still Death/Dead from the feet up the hollow dress, as installed.
- LODs (`lod_check.py`, every frame of every clip): top 0.832 at every LOD (installed LOD3 0.834), Standing -0.2 cm, Dead 0.0 and
  Death -1.5..-1.6 cm at every LOD (installed LOD3 Standing +0.24, Dead +0.15, Death -1.86 cm); faces stretched > 20x per LOD 2 / 1 / 1 / 2
  (installed 10 / 5 / 5 / 5).

## Review
Viewer (installed vs reduced; `run_creature_review.py check` 22 switches, 0 failed, 0 console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_fre_reduce_claude/review/viewer/
Sheets (installed above reduced, read at full size): `review/sheet_face_c50.png` (front close-up, 3/4, both profiles, low 3/4, Talk, back of
head, back 3/4, party) with `review/diff_face_c50.png` (per-shot differences x4: black on the whole head in every view; only the braid edge,
the collar and the viewer's label differ), `review/sheet_body_c50_a.png` (Standing front/3-4/back, Walking, Talk, Death),
`review/sheet_back_c50_a.png`, `review/sheet_arms_c50_a.png`, `review/sheet_close_c50_a.png` (hands both sides 3/4 and side, Talk hand,
hem, skirt panel), full-size crops `review/hands_full_a50.png`, `review/braid_full_a50.png` (a = c on hands and braid).
What to look at: the back of the hands (one soft crease differs, every finger kept), the braid's outline from behind (slightly straighter
edges, same plait paint and gold band), the feather collar's top edge behind the neck.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_fre_reduce_claude/before/mm9_fre.glb REA_NODE=Fre $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py
NEAR_BRAID=0.05 $G scripts/make_sets_fre.py c
SETS=c MP_W5=4 MP_TEX_MAX=100 MP_TEX_MEAN=45 MP_GROUPS=1:0.6,3:0.7,4:0.8,5:1.0,6:0.6,7:0.7,8:0.75,9:0.75 scripts/cap.sh $G scripts/mpqem.py before/mm9_fre.glb 0.5
cp work/mp_r50.npz work/mp_c_r50.npz; scripts/build_mp.sh mp_c_r50 export/mm9_fre.glb      # (work/queue_c.sh: ladder record, audit, gates)
scripts/gates.sh export/mm9_fre.glb review/gates_<tag>; scripts/see_lod.sh export/mm9_fre.glb review/gates_<tag>; python3 scripts/gate_compare.py <tag>
scripts/shots.sh; python3 scripts/shot_sheets.py <tag>
```
`build_mp.sh`: swap_mp -> FreHair doubleSided off (`single_hair.py`; the LOD tool merges the shadow mesh over one face culling, as Fre's own
build ran the LODs before `double_hair_fre.py`) -> `build_lods.py` (snapped protected points: soles, crown, corpse contact) ->
shrink_shadow_lods -> `double_hair_fre.py` -> Fre's `fix_winding.py` -> check_winding.

Install (on the orchestrator's / user's OK only): `check_winding.py export/mm9_fre.glb` (0), `tools/install_model.py export/mm9_fre.glb
--world mm9`, the binding regression, and add to `../mm9_fre_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_fre_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_fre.glb`.

## Not checked
In game; motion at normal speed by eye (viewer stills of Standing, Walking, Talk, Death and numeric gates only); LOD1-3 and shadow meshes
by eye (numbers only); see-through/LOD check of ladder a (stopped; c replaced it); the binding regression (orchestrator, after install).
