# MM9 Lich King (`mm9_lichking`) reduction: candidate f2 r55 ready for review (2026-11-05)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) and the standing
[townsfolk agent brief](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md), ledger row 6 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) (prio 3 unique boss; user 2026-11-05 "do all"). Lease `mm9reduce:lichking` (owner
lichking-reduce-20261105, released at hand-off); the creature's own `mm9:lichking` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_lichking.glb` (sha256 63b5d59578bb, identical to `../mm9_lichking_claude/export/`), copied to
`before/` (the rollback source) by the deferred first visit on 2026-11-04. No Meshy, no credits, no repaint. **Not installed.**
`../mm9_lichking_claude/` (approved) was only read; its gate scripts run with that folder as working directory (grip_gate reads its
`work/rig.json`) and write only here.

| | LOD0 | body prim | skull (face) | staff + caps | staff skull | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 14,991 | 11,060 | 3,000 | 492 | 439 | 7,493 | 2,696 | 897 |
| **f2 r55 (`export/mm9_lichking.glb` = `export/mm9_lichking_mp_f2_r55.glb`, sha256 79dc89523036)** | **12,163 (-18.9 %)** | 8,232 | 3,000 | 492 | 439 | 6,078 | 2,187 | 726 |

Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the installed bytes; only index
buffers changed). Clips (21), skin, nodes (sockets `LHand1`, `RHand1`, `u1`), materials (the skull's and staff skull's emissive eye
glow and pulse), region ramps, the `lichking` variant and all 12 images: byte-identical (`same_clips.py`). The skull, staff and
staff-skull primitives keep the installed index buffers; crown, collar, upper arms, the coat's inner surface and the shoulder plates
keep every installed triangle.

## Measured first: protected share
Part labels: `scripts/glb_parts.py` (the deferred visit's mapping of `../mm9_lichking_claude/work/uv_tex.npz` onto the GLB, every
face to 5e-8 m). Boss extras kept exact: skull 3,000 (the face), staff skull 439 (eye glow), staff 260 with crown cap 84 and tube caps
148 (already a low procedural prop; the caps are the see-through fixes), crown 846, collar 178 (neck seam): 33 % of LOD0. The final
set f (`scripts/make_sets_lk.py`) also keeps the grip contact (285 R-hand faces within 8 mm of the staff: the r19 staff-in-palm
solve), the hand/bracer junction (148), soles (132), contact faces (1,042: body faces within 3 cm of a hand or bracer and coat/tabard
faces within 1.5 cm of a trouser or boot in any pose of any clip at 10 Hz, `scripts/contact_lk.py`), the upper arms (796), the coat's
inner surface (684) and the shoulder plates (412 torso faces with two or more corners dominated by a Clavicle/UpperArm bone): 56 %.

Not rebuilt: the staff is already a 260-face procedural cylinder; the buckle and medallions are flattened reliefs skinned to the
torso and painted on the body atlas (a low-poly rebuild with a projection bake would repaint body-atlas texels, which the no-repaint
rule forbids), so they are cut by the same guarded collapse as the cloth. The coat's inner surface is the inside of Meshy's closed
coat shell, not an offset twin of the outer faces, so it cannot be re-emitted from an outer cut; cut on its own (sets a-c) it raised
the see-through gate's back-face views into the coat (torso inside 14,577 -> 17,737 px), so it is kept exact.

| part (body prim) | installed | f2 r55 | |
|---|---:|---:|---|
| coat / torso outer | 2,110 | 1,561 | 0.55 of the free faces; shoulder plates and contact faces kept |
| hands (every finger) | 1,500 | 1,072 | 0.6 of the free faces (grip contact and cuff kept) |
| boots | 1,568 | 1,040 | 0.6 above the soles |
| trousers | 832 | 490 | 0.55 |
| tabard | 668 | 500 | 0.55 (leg contact kept) |
| buckle + medallions + knee medals | 1,298 | 658 | 0.5 |
| bracers | 340 | 238 | 0.7 |
| collar wings | 240 | 168 | 0.7 |
| crown, collar, upper arms, coat inner surface | 2,504 | 2,504 | exact |

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantF3 copy)
Scored over 347 poses (every clip at 10 Hz) plus a position+UV rest quadric, texture weight 4 (`MP_W5`); texture guard over the
toned body colour (region ramps applied), the head image and the region mask (`scripts/tex_extract.py`; refuse > 100 any sample /
> 45 mean); the Mummy's chart guard at 12 samples (`MP_CHART=1`) and the Skeleton fix pass's audit chart test inside every collapse
(`MP_AUDIT=1`: `reduction_uv_audit.Charts`, off and cross at zero tolerance); seam slides on the hands (`MP_SEAM_GROUPS=1`).
`MP_NSPREAD` (a corner-normal spread guard, tried in pass e) is in the script but off: at 45 deg it blocked the cheap collapses and
the fixed targets then took 20 mm ones.

## Ladders and fix passes (limits for 1.599 m: p99 <= 4.80 mm, max <= 24.0 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| run | set / groups (hands, bracers, inner, trousers, boots, upper arms, tabard, reliefs, wings) | step | LOD0 | p99 / max mm | result |
|---|---|---|---:|---|---|
| ladder a | a / .65 .75 .6 .6 .65 .7 .7 .6 .8 | r70 / r60 / r50 | 11,777 / 11,567 / 11,355 | 2.81/15.3, 3.25/15.3, 3.99/21.1 | pass; a r50 built: arm/hand Resurrect R forearm 1.2 -> 1.8 cm, Death3 R hand 4 -> 6 frames > 1 cm, cloth AttackMelee coat-on-leg 2.8 -> 3.1 cm |
| ladder b | a / .6 .65 .5 .5 .55 .6 .55 .5 .65 | r50 / r40 | 10,629 / 10,427 | 4.80/21.1, 8.62/35.2 | fail / fail (chest, thighs, upper arms, coat) |
| ladder c | c (+ contact) / .6 .7 .55 .55 .6 .65 .55 .5 .7 | r60 / r50 | 11,497 / 11,333 | 3.62/15.7, 4.36/21.1 | pass; c r50 built: gates fixed except see-through (sleeve holes 3,561 -> 3,891 px, torso inside 14,577 -> 17,737 px), jitter 8 -> 9 (Hit L shoulder skin), a blue sheen on the shoulder plate in Running |
| fix d | d (c + upper arms, inner surface exact) | r50 | 11,895 | 3.93/21.1 | pass; torso inside back to 14,818 px, jitter 8; sleeve holes and the sheen unchanged |
| fix e | d + `MP_NSPREAD=45` | r50 | 12,151 | (not measured: worst collapse 20 mm) | dropped |
| fix f | f (d + shoulder plates exact) | r50 | 12,101 | 4.02/29.6 (ResurrectSpell:12) | fail (the torso's fixed share fell on fewer faces) |
| **fix f2** | f, torso ratio | r60 / **r55** | 12,223 / **12,163** | 3.06/15.7, **3.35/16.1 (Death2:33)** | pass / **PASS, picked** (IoU .9967, SSIM .9956) |

(A first start of ladder a without the audit chart test was stopped before its first step and rerun with it.)

## Gates, installed -> f2 r55 (the creature's own gate set, `scripts/gates.sh`; `review/gates_installed/`, `review/gates_f55/`; `scripts/gate_compare.py installed f55`)
- **UV chart audit** (`reduction_uv_audit.py`, `review/uv_audit_f55.json`): LOD0 0 escaping faces in every primitive (off 0, cross 0).
  Body LOD1/2/3 148 / 189 / 110 (installed 119 / 213 / 131; Blender's LOD decimate; LOD0 is the gate).
- Collapse (`collapse_gate.py`): face-frames 18,514 -> 13,012; every clip's worst region within 1 face or lower (AttackMelee torso
  51 -> 22, Taunt torso 25 -> 9, Death2 strip 113 -> 90).
- Cloth (`cloth_gate2.py`): coat-on-leg frames 54 -> 44 over all clips (Running 7 -> 5 at 4.9 cm, Hit 11 -> 10, Death2 15 -> 12 at
  7.2 cm), tabard 18 = 18, coat-on-torso 24 -> 22; no clip deeper beyond 0.1 cm (Hit 3.7 -> 3.8 cm).
- Grip (`grip_gate.py --mirrored`): identical in every clip (joint-to-axis 1.76 cm, 0 skin inside, wrap 203 deg, fingertips 129 deg,
  thumb 45 deg) except the palm gap p10 0.53 -> 0.49 cm (closer).
- Staff (`staff_gate.py`, `head_gate.py`): frames with the staff behind the body skin 192 -> 189; staff in the head hull unchanged
  (AttackRanged 2.1 cm, Hit 0.5 cm).
- Arm/hand (`--outer-only`, 48 fps): equal in every clip except the falls of Death (L forearm 5.6 -> 5.7 cm) and Death3 (L forearm
  5.5 -> 5.9 cm, worst frame 20 -> 22; R hand 2.4 -> 2.6 cm, 4 -> 5 frames > 1 cm, i.e. Death's installed numbers); Hit R hand 0.3 -> 0.0.
- Jitter (against the creature's uncorrected-clip `work/coat.glb`): 8 = 8 fails (the installed ones). Bone lengths 0 of 19 (both).
  Winding 0 inverted (both).
- Detached parts (`detached_parts_audit.py`): 91 components both; detached in some pose 9 -> 7 (the R hand and the R-side staff
  piece no longer part in Death; skull/crown pieces 1.3 cm and staff pieces identical); tabard (XPanelF2) 0.71 -> 0.75 cm in
  Fidget2/Search 1.83 s, 20 = 20 poses. Root lifts: the trouser halves in Death3 30.1 / 27.6 -> 7.9 cm; new: R hand off the R forearm
  3.05 cm (90th percentile of its bind contact, over fewer vertices) in Death frame 24, the fall where the installed hand parted
  0.82 cm.
- Flat shading body 0.02 -> 0.01 (head, staff, staff skull equal). Texture quality body: atlas 55.3 % both, stretch p90 1.09 -> 1.11,
  fragments 0.0 -> 0.1 %, spread 2.62 -> 2.63; head and staff identical.
- See-through (`scripts/see_through.sh`: PeasantF3's `see_through_gate.py`, every clip at 10 fps, 16 views; stands in for the
  creature's tube_gate.py; hole px max / sum over clips): sleeve L 627 / 3,561 -> 633 / 3,607, sleeve R 768 / 4,835 -> 773 / 5,133
  (+30-45 px in Walking, Backpedal, Running, AttackMelee: the armpit wedge under the open coat that the installed model already
  shows, `review/see_sleeveR_pair_f55.png`), torso 927 / 9,310 -> 933 / 9,181, collar 65 -> 58, head 4 = 4, trousers equal, boots
  10 / 8 -> 19 / 11 px in the Death falls (frames with any boot hole 143 / 174 -> 62 / 44). Back-face views into the coat ("inside",
  not holes) 14,577 -> 14,996 px (c r50 with the inner surface cut: 17,737).
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: tool ratios 0.5 / 0.18 / 0.06, 4 influences,
  soles, top and corpse contact protected, each point snapped to the imported vertex): height 1.605 m at every LOD (installed LOD2 /
  LOD3 1.602 / 1.601), rest on the floor at every LOD (installed LOD1 -0.2 mm, LOD3 +0.4 mm); per-clip lowest points of LOD1-3 equal
  LOD0's (installed LOD3 Dead2 +0.9 cm, Walking -0.1 against LOD0's -0.6 cm); stretched faces LOD0 38 -> 33, LOD1-3 0.

## Review
Viewer (installed and reduced, one tier, all 21 clips; `run_creature_review.py check`: 42 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_lichking_reduce_claude/review/viewer/
Sheets read (full size): `review/sheet_face_f55.png` (front close-up, 3/4, true profile, low 3/4, party) and
`review/sheet_face_diff_f55.png` (skull, crown and shoulder plates black in all five; differences on the collar wings and the chest),
`review/sheet_body_f55_a.png` (Standing front/3-4/back, Walking, AttackMelee, Death), `review/close_f55_1.png` (arms, coat front and
back, Running), `review/close_f55_2.png` (boots, AttackRanged, shoulders from behind, Hit), `review/close_f55_hands.png` (R hand on the
staff from outside and below, L hand, L bracer), `review/close_f55_details.png` (chest medallions and buckle, tabard and knee medals,
back medallions, boots front), `review/c3_full_f55.png` (Running shoulder, full frame: the c/d sheen is gone),
`review/ladder_sheet_{a,c,f2}.png`; the earlier candidates' sheets (`*_a50*`, `*_c50*`, `*_d50*`) are kept.

Look at: the chest medallions and buckle (the flattest parts, cut to about 40 %; identical in the close-ups), the collar wings (0.7),
the coat hem swinging in Running and Walking.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_lichking_reduce_claude/before/mm9_lichking.glb REA_NODE=LichKing $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/glb_parts.py; $G scripts/tex_extract.py
scripts/cap.sh $G scripts/contact_lk.py c; SHOULDER=1 CONTACT=c KEEP_PARTS=uarms,inner $G scripts/make_sets_lk.py f
MP_AUDIT=1 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=f MP_GROUPS=1:0.6,2:0.7,3:0.55,4:0.55,5:0.6,6:0.65,7:0.55,8:0.5,9:0.7 scripts/run_mp.sh f2 0.6,0.55
scripts/build_mp.sh mp_f2_r55 && cp export/mm9_lichking_mp_f2_r55.glb export/mm9_lichking.glb
$G ../claude_shared/reduction_uv_audit.py export/mm9_lichking.glb before/mm9_lichking.glb --json review/uv_audit_f55.json
scripts/gates.sh before/mm9_lichking.glb installed; scripts/gates.sh export/mm9_lichking.glb f55; python3 scripts/gate_compare.py installed f55
scripts/see_through.sh before/mm9_lichking.glb installed; scripts/see_through.sh export/mm9_lichking.glb f55
REA_NODE=LichKing $BL -P scripts/lod_check.py -- $PWD/export/mm9_lichking.glb f55
$G scripts/viewer_tiers.py before/mm9_lichking.glb inst; $G scripts/viewer_tiers.py export/mm9_lichking.glb red_f55
$G scripts/make_viewer_manifest.py f55 "inst_a=Lich King installed=work/viewer_inst.glb" "red_a=Lich King reduced f r55=work/viewer_red_f55.glb"
scripts/shots.sh; scripts/close_shots.sh; $G scripts/shot_sheets.py f55; $G scripts/face_diff_sheet.py f55; $G scripts/close_sheet.py f55 a <shots> <png>
```
`scripts_wyrdold/` holds the deferred visit's unused Wyrd copies. Install (orchestrator, on the OK): `check_winding.py
export/mm9_lichking.glb` (0), `tools/install_model.py export/mm9_lichking.glb --world mm9`, the `mm9_actor_models_build_every_binding`
regression, and add to `../mm9_lichking_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_lichking_reduce_claude`; a
rebuild from this project must re-run that reduction". Rollback: `before/mm9_lichking.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (gates, frames and
viewer stills only); LOD1-3 and the shadow meshes by eye (numbers only); the cast glow at `palm_left` / `staff_head` (sockets and
emissive materials are byte-identical); tube_gate.py (needs the raw rig vertex order; the rims are open boundaries, locked by the
collapse, and the see-through gate stands in).
