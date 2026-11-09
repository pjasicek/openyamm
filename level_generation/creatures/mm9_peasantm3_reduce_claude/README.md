# MM9 PeasantM3 (`mm9_peasantm3`, townsman, tiers pm3_a / pm3_b) reduction: candidate e r50 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and
[REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 55 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm3` (owner
peasantm3-reduce-20261105); the creature's own `mm9:peasantm3` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm3.glb` (sha256 52fcf7133249, identical to `../mm9_peasantm3_claude/export/mm9_pm3.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm3_claude/` was only
read (its build-default master `work/neck_v5.blend` opened read-only for the head/hand/lined labels; its gate scripts run in place).

**Family:** PeasantM3 is its own body (the creature README's `meshcmp.py`: torso p90 3.9-5.7 cm against every built male body; only
the head is close to PeasantM7's). It shares nothing with PeasantM2/M2d, so `../mm9_peasantm2d_reduce_claude/` and
`../mm9_peasantm2_reduce_claude/` were not needed as sources (M2d's tier-aware texture guard and viewer scripts were copied).

| | LOD0 | body prim (cloth, linings, boots, belt, brooch) | head set (face shell, hair, MPFB hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 10,639 | 7,252 | 3,387 | 5,317 | 1,912 | 524 |
| **e r50 (`export/mm9_peasantm3.glb`, sha256 dec84a772801)** | **9,003 (-15.4 %)** | 6,282 | 2,721 | 4,499 | 1,617 | 472 |

(LOD3 counts are after the creature's `shrink_shadow_lods.py DROP_LINING_LODS=3`, which drops the one-texel linings from LOD3, as
installed.) Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes;
only index buffers changed; `scripts/exact_face.py`). Clips (10), skin, nodes, materials, region ramps, `KHR_materials_variants`, all
9 images: identical (`review/gates_e50/same_clips.txt`; `tools/build_actor_lods.py` writes the material JSON in normalised form,
`scripts/restore_materials.py` copies the installed JSON back). Face shell (face, ears, scalp, neck, mouth caps: 1,435) and the
brooch (380): every installed triangle present exactly, so the face renders pixel-identical in both tiers
(`review/sheet_face_diff_e50.png`: the face is black in all five views of A and B; only the hair shell and collar shading differ).

## Measured first: protected share
Components and labels from the GLB itself (`scripts/glb_parts_dm4.py`, centroid match to `neck_v5.blend` at 0.0 mm) and lining pairs
from `scripts/twins_dm4.py` (PeasantDM4's: the creature lined with the same `rim_lining.py` + an own-paint `twin_shell.py`): 2,672
lining faces paired with their outer cloth (1,102 one-texel + 1,570 painted twins, residual 0.00 mm), 482 rim strips and 152
unpaired twin faces kept exact. Face shell + brooch + rim strips + small pieces = 30 % of LOD0 (set a); linings 24 % are re-emitted
from the cut cloth. A 15 % cut was in reach, so the ladder ran.

Keep set (`scripts/make_sets_pm3.py e`, final 47 % exact incl. kept pairs): whole face shell; hairline (hair within 12 mm of its
rim); hand forearm stubs (graft junction); brooch (component 8); belt and strap/buckle whole (components 7, 9) and every body face
within 3 cm of them (`work/belt_points.npy`); shoulder cloth (faces touching a Clavicle/UpperArm-dominated vertex,
`work/keep_shoulder.npy`); soles; collar within 12 mm of the head set; rim strips, unpaired twins and painted faces within 6 mm of
them; small pieces; two locks (`work/open_lock_b.npy` 12 mm: a non-manifold collar edge that opened in ladder a;
`work/arm_lock_c.npy` 4 cm: L hip/armpit faces the arm gate's L forearm read itself inside of in b60).
Groups: hands + fingers 0.6 (seam slides, every finger kept), hair 0.65, legs (boots, breeches cuffs below 0.48 m) 0.5, cloth at the
ladder ratio; every group stops at the 1.0 mm per-collapse error cap (`MP_MAXRMS`, PeasantDM4's), which binds before the ratio.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`)
PeasantDM4's copy (per-band lining corner maps, error cap) with node PeasantM3, the texture guard over both tiers
(`scripts/tex_extract.py`: tone x each tier's region ramps + region mask; both head images), the Mummy chart guard (`MP_CHART=1`,
12 subdivisions), **the audit's own chart test inside each collapse** (`MP_AUDIT=1`, PeasantM2d's), texture weight 4. Scored over 198
poses (every clip at 10 Hz) plus a position+UV rest quadric.

## Ladders (limits for 1.80 m: p99 <= 5.4 mm, max <= 27.0 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | set / change | LOD0 | p99 / max mm (worst) | result |
|---|---|---:|---|---|
| a | a; r60 = r50 (error cap binds) | 8,561 | 4.03 / 18.0 (Death:12) | fail: open edges 500 -> 501 (a collar non-manifold edge) |
| b | a + collar lock | 8,589 (-19.3 %) | 4.02 / 18.0 | PASS; built `export/mm9_peasantm3_b60.glb`: UV audit 0, but jitter AttackMelee R shoulder skin 0.24 -> 7.3 mm/f2 FAIL, arm gate L forearm Fidget 0 -> 5.1 cm, Talk 0.1 -> 4.9, and the belt's back edge read jagged (`review/crop_belt_back_b60.png`) |
| c / d | b + belt whole + shoulder cloth + L arm lock; d also cuts the brooch 0.6, hair 0.65 | 8,941 / 8,825 | 3.47 / 16.8 (Cower:9) | PASS / PASS; d's brooch swirls shift in close-ups (`review/close_d50_a_brooch.png`) for 116 triangles: brooch kept; the belt edge was still jagged in d (`review/crop_belt_back_d50.png`): the tunic above the belt, not the belt |
| **e** | **c + cloth within 3 cm of the belt kept, hair 0.65, legs 0.5** | **9,003 (-15.4 %)** | **3.42 / 16.8 (Cower:9)** | **PASS, picked** (IoU .9956, SSIM .9961); belt edge as installed (`review/crop_belt_back_e50.png`) |

## UV chart audit (hard gate)
`review/uv_audit_mm9_peasantm3.json` (`.txt`): **0 escaping LOD0 faces in both primitives**. LOD1-3 (Blender decimate) body 205 / 178 /
83, head 108 / 106 / 58 vs installed 180 / 182 / 92, 79 / 106 / 69.

## Gates, installed -> e r50 (`scripts/gates.sh`: the creature's own scripts, read in place; `review/gates_before/`, `review/gates_e50/`)
- Arm/hand (`--outer-only --exact`, 48 fps): equal or better in every clip: Talk R hand 1.9 cm (9 f) -> 1.3 cm (6 f), Fidget L hand
  0.8 -> 0.2 cm, Fidget R forearm 5.9 -> 5.8 cm (installed value, the forearm in the tunic flank), L forearm AttackMelee 1.8 / Death 1.4
  equal; finger stretch within +-0.02 of installed (maxima equal or lower); 19 chains per hand.
- Jitter vs `../mm9_peasantm3_claude/work/mm9_pm3_clips.glb`: identical output, 0 fails (b60 failed AttackMelee R shoulder skin on the
  thinner p95 sample; the shoulder cloth is kept since c).
- Sleeve poke: identical per clip and side; rest 0 mm both (one candidate vertex fewer per side: a cut forearm-sleeve vertex).
- Detached: same parts and flags (11 shallow/root-lift lines, same values; L calf pieces 324 -> 284 and 487 -> 357 tris).
- Flat shading 0.00 both. Winding 0. Bone lengths: L thigh 11-13 % as installed (MM9's hip slide). Texture quality: body atlas 61.3 %
  as installed; head 38.1 -> 38.0 %, fragments 3.3 -> 4.2 %, stretch p90 1.40 -> 1.41.
- Lining through cloth (`scripts/lining_gate.py`, PeasantDM4's, relative check): most lining vertices out per frame within +-6 of
  installed; max outward distance rose (Standing 5.8 -> 15.3 mm, Dead 15.7 -> 3.1): the new worst is one skirt-twin vertex at the front
  hem (rest 0.139, 0.843, 0.095) measured against a different layer's face 2.6 cm away (`scripts/lining_probe.py`); close-ups of
  that spot in Standing, Walking and from below show nothing through the cloth (`review/close_e50_a_hemslit.png`).
- See-through (`scripts/see_through.sh`: the creature's `see_through_gate.py` as its README ran it, every 3rd 30 fps frame of every clip
  + Running 12, 16 views, 3 mm px; worst hole px installed -> e50): collar 6 -> 4, head 4 -> 3, torso 9 -> 9 (same frame and view,
  Hit 6 az045), sleeve L 1 -> 0, sleeve R 0, boots 0, trousers L 1 -> 1, R 3 -> 3; frames with any hole collar 112 -> 133, torso
  43 -> 48, head 120 -> 118, others equal (single-pixel silhouette slivers at that size).
- LODs (`scripts/lod_check.py`, every frame of every clip; `work/lod_check_{installed,e50}.json`), built by `scripts/build_lods.py`
  (tool defaults 0.5/0.18/0.06, 4 influences; soles, crown and corpse contact protected, snapped to the imported vertices): height
  1.8048 m at every LOD (installed LOD1-3 1.8065 / 1.8033 / 1.7889); every clip's lowest point at LOD1 equal to LOD0, LOD2/3 within
  0.3 cm (Death -0.72 vs -0.45 cm); installed LOD3 floated 1.1-2.7 cm in every living clip; 0 stretched faces.

## Review
Viewer (installed and reduced, both tiers, all 10 clips; `run_creature_review.py check`: 40 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm3_reduce_claude/review/viewer/
Sheets read (full size): `review/sheet_face_e50.png` (front close-up, 3/4, true profile, low 3/4, party; both tiers),
`review/sheet_face_diff_e50.png`, `review/crop_hair_profile_e50_{a,b}.png`, `review/sheet_body_e50_b.png` (Standing front/3-4/back,
Walking, Talk, Death), `review/close_e50_b_hands.png` (both hands outside and front: every finger, slightly more faceted tips),
`review/close_e50_a_3.png` (shoulders from behind, Hit, hem slits), `review/close_e50_b_2.png` (Running skirt, boots, Talk arms),
`review/close_e50_a_hemslit.png`, `review/crop_belt_back_e50.png`; for earlier steps `review/sheet_face_b60.png`,
`review/sheet_face_diff_b60.png`, `review/sheet_body_b60_{a,b}.png`, `review/close_b60_a_{hands,hands2,details,1,2}.png`,
`review/close_d50_a_brooch.png`, `review/crop_belt_back_{b60,d50}.png`, `review/ladder_sheet_a.png`, `review/sets_a_{body,head,hands}.png`.
Not opened for e50: `review/sheet_body_e50_a.png`, `review/close_e50_a_{1,2,details,hands}.png`, `review/close_e50_b_{1,3,details}.png`
(the same geometry as b in those areas or read on b60).
Look at: the fingertips (hands 0.6), the hair shell from behind (0.65, hairline exact), the boots and breeches cuffs (0.5).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="../claude_shared/gltf_venv/bin/python -W ignore"
REA_GLB=level_generation/creatures/mm9_peasantm3_reduce_claude/before/mm9_peasantm3.glb REA_NODE=PeasantM3 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $BL -P scripts/dump_blend_parts.py -- $PWD/../mm9_peasantm3_claude/work/neck_v5.blend
$G scripts/glb_parts_dm4.py; $G scripts/twins_dm4.py; $G scripts/tex_extract.py; $G scripts/keep_shoulder.py   # + belt_points.npy (README)
KEEP_COMPS=7,9 EXTRA=work/keep_shoulder.npy BLOCKS=work/open_lock_b.npy:0.012,work/arm_lock_c.npy:0.04,work/belt_points.npy:0.03 $G scripts/make_sets_pm3.py e
MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 MP_MAXRMS=1.0 SETS=e MP_GROUPS=1:0.6,2:0.65,4:0.5 scripts/run_mp.sh e 0.5
scripts/build_mp.sh mp_e_r50 export/mm9_peasantm3.glb   # swap_mp -> build_lods (protected, snapped) -> shrink_shadow_lods (DROP_LINING_LODS=3) -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm3.glb before/mm9_peasantm3.glb --json review/uv_audit_mm9_peasantm3.json
$G scripts/exact_face.py export/mm9_peasantm3.glb; scripts/gates.sh export/mm9_peasantm3.glb e50; scripts/see_through.sh export/mm9_peasantm3.glb e50
REA_NODE=PeasantM3 $BL -P scripts/lod_check.py -- $PWD/export/mm9_peasantm3.glb e50
$G scripts/viewer_tiers.py export/mm9_peasantm3.glb red   # installed: viewer_tiers.py before/mm9_peasantm3.glb inst
$G scripts/make_viewer_manifest.py e50 inst_a=..=work/viewer_inst_th_a.glb red_a=..=work/viewer_red_th_a.glb inst_b=.. red_b=..
HEADUP=0,0.08,0.05 scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py e50; $G scripts/face_diff_sheet.py e50
```
`work/belt_points.npy` = the rest positions of every vertex of body components 7 and 9 (belt, strap/buckle).
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm3.glb` (0), `tools/install_model.py export/mm9_peasantm3.glb
--world mm9`, the `mm9_actor_models_build_every_binding` regression, floor audit, and add to `../mm9_peasantm3_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_peasantm3_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_peasantm3.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills, gates and
viewer only); LOD1-3 and shadow meshes by eye (numbers only); the eye/mouth close-ups at the user's zoom (the face triangles are the
installed ones and the five-view face diff is black).
