# MM9 Hanndl the Gate Keeper (`mm9_hanndl`, row 58) reduction: candidate d7 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (relaxed keep set, face exact; user
2026-11-05 "do all": prio-3 uniques reduced too), ledger row 58 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:hanndl` (owner hanndl-reduce-20261105); the creature's own `mm9:hanndl` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_hanndl.glb` (sha256 99c719f1bf9c, identical to `../mm9_hanndl_claude/v2/export/mm9_hanndl.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_hanndl_claude/` was only read
(its `arm_hand_gate.py`, `jitter_gate.py`, `sleeve_poke_gate.py`, `shrink_shadow_lods.py`, `fix_winding.py` and
`v2/work/mm9_hanndl_clips.glb` run in place; its `see_through_gate.py` copied here so it runs under this lease).

**Family note (Annud, row 70):** Hanndl is Annud's approved PeasantM6 body (same MM9 skeleton, weights and clip choice) with the
sleeves narrowed onto the forearms, the forearm stubs tucked, its own neck cap / collar / belt-rim linings and its own paint
(`../mm9_hanndl_claude/README.md`). The two GLBs share the body topology but not the vertex data (moved sleeve and stub vertices,
extra lining faces, different textures), so this cut cannot be dropped onto `mm9_annud.glb`; Annud is reduced on its own (separate
row). Every script here takes the node/prim names as the only creature-specific part and can be reused for Annud.

| | LOD0 | body prim (tunic, legs/boots, collar loops, tassels, linings) | head set (face shell, hair, hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 10,060 | 5,005 | 5,055 | 5,027 | 1,804 | 594 |
| **d7 (`export/mm9_hanndl.glb` = `export/mm9_hanndl_d7.glb`, sha256 f6b3c2034e1e)** | **8,574 (-14.8 %)** | 4,445 | 4,129 | 4,284 | 1,537 | 504 |

Per group (free faces cut): hands 1,473 -> 1,025 (0.6, distal finger faces exact), hair shell 999 -> 599 (0.6, hairline exact),
scalp under the hair 173 -> 95, tunic/skirt/upper trousers 991 -> 733, forearm sleeves 302 -> 232, boots above 10 cm and calves
449 -> 277, linings 722 -> 662 (re-emitted from the cut outer faces). Every vertex of the candidate is an installed vertex (positions,
normals, UVs, joints, weights are the installed bytes; only index buffers changed; `scripts/exact_head.py`: every kept face present).
Clips (27), skin, nodes, materials, all 6 images identical (`review/gates_d7/same_clips.txt`).

## Measured first: protected share
`scripts/analyze.py`, `scripts/twins.py` (593 paired one-texel linings + 129 mapped by vertex; 581 unpaired one-texel body faces),
`scripts/head_survey.py` (head-shell faces under the hair shell by a ray along the face normal). Set a (`scripts/make_sets_hanndl.py`,
PeasantDM2's set c3 logic): face shell exact except the scalp/back of the skull under the hair (1,887 of 2,060 exact: face, ears,
neck, painted beard, neck seam), hairline (hair within 12 mm of its rim or of the open skin), collar loops and tassels (small
pieces), shoulder cloth, the whole fitted sleeve (cuff from the hand piece's stub), soles, rim strips + unmapped linings with a 6 mm
halo, hand-contact faces (every clip at 24 Hz within 4 cm) = 48.8 % protected; 15 % needed about a third of the free part, so the
ladders ran. The final set d7 protects 53.6 %.

## Route
PeasantDM2's pose-aware half-edge collapse (`scripts/mpqem.py`; Hanndl: one tier, texture guard over the two colour images), linings
re-emitted from their twins with one shared texel per face, Mummy chart guard `MP_CHART=1` plus **the audit's own chart test per
collapse** (`MP_AUDIT=1`, ported from PeasantM2d), texture weight 4, seam slides on the hands, scored over 1,084 poses (all 27 clips
at 10 Hz), distance guard 5 mm (tunic/legs 9 mm, forearm sleeves 4 mm).

## Ladders (limits for 1.78 m: p99 <= 5.34 mm, max <= 26.7 mm, IoU >= .98, SSIM >= .93)
| ladder | change | LOD0 | result |
|---|---|---:|---|
| a / b | set a; b = hair and scalp 0.6, legs 0.5 | 8,482 / 8,364 (-15.7 / -16.9 %) | gates on a60 equal or better; viewer close-ups of b60: R boot toe profile and vamp seam shading changed, R ring fingertip cut to a dark-ended prism, L thumbnail stretched |
| c (+ c2, c3) | b + both boot feet below 10 cm + one ring exact; c2/c3 hand guard 2.5 / 3.5 mm | 8,526 / 8,722 / 8,608 | the guard alone did not keep the ring fingertip (`review/hands_guard_compare.png`) |
| d (fixes d3-d7) | c + distal finger faces exact, cuff measured from the wrist (forearm sleeve cut at 0.6, 4 mm guard), tunic/legs guard 9 mm, scalp 0.4; d6 hands back at 5 mm; **d7 = d6 + cloth below the belt front exact** | d6 8,552, **d7 8,574 (-14.8 %)** | d6's lining gate rose 2.95 -> 9.5 mm (belt-rim lining behind the tassels); d7 restores it. **d7 picked**: p99 3.76 / max 12.86 mm (Running:21), IoU .9946, SSIM .996 (`review/ladder_sheet_d7.png`) |
d3/d4 tried a one-texel stub group (the hand stubs inside the sleeves); no stub collapse passes the seam locks, dropped.

## Gates, installed -> d7 (`scripts/gates.sh`: the creature's own scripts; `review/gates_before/`, `review/gates_d7/`)
- **UV audit** (`review/uv_audit_d7.json`, `.txt`): **0 escaping LOD0 faces in both primitives.** LOD1-3 (Blender decimate) body
  90 / 95 / 46, head 227 / 204 / 106 vs installed 88 / 99 / 49, 200 / 160 / 105 (`review/uv_audit_installed.txt`).
- Arm and hand (`--outer-only --exact`, 48 fps, all 27 clips): equal or better in every clip (Talk L forearm 3.7 -> 3.2 cm, Hanndl04
  L forearm 1.4 -> 0 cm; Talk R hand 3.2 cm / 26 frames both, MM9's conv2 hand); finger stretch maxima equal or lower (Death R
  1.65 -> 1.39, Dead R 1.65 -> 1.34), minima within -0.05; 19 chains per hand. `scripts/finger_check.py`: all 30 finger joints keep
  their vertices, fingertip reach within 1.2 mm (four mid-segment boundary vertices moved, tips exact).
- Jitter vs `../mm9_hanndl_claude/v2/work/mm9_hanndl_clips.glb`: identical output, the creature's 8 known fails (incl. Hit R shoulder
  skin) unchanged.
- Sleeve poke: identical per clip and side (rest 0 mm; Fidget R 7.7 mm / 6 f and AttackMelee L 1.2 mm / 9 f as installed).
- Linings (`scripts/lining_gate.py`, 32 faces): largest outward distance equal in every clip (Standing 2.95, Talk 7.15, Death 7.68 mm);
  most vertices > 0.5 mm per clip equal or +1..3 (Walking 27 -> 30, Running 34 -> 36). d6 without the belt-front keep: 2.95 -> 9.5 mm.
- Detached parts: the R hand part opens up to 2.05 cm in 8 of 3,161 poses (installed 2.49 cm, 16 poses); same notes otherwise.
  Flat shading 0.00 both. Winding 0. Bone lengths 12 checked, 0 stretching. Texture quality: body atlas 59.4 % both, stretch p90
  1.14 -> 1.16; head 40.9 % both, fragments 1.1 % both.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: ratios 0.5/0.18/0.06, 4 influences, soles/crown/
  corpse contact protected and snapped, 42 of 42 mapped; `review/lod_check_summary.txt`): height 1.7965 m at every LOD; lowest point
  of LOD1-3 equal to LOD0 in every clip (installed LOD3 -1.85..+1.04 cm, LOD2 up to +0.58 cm); 0 stretched faces at any LOD, both.

## Review
Viewer (installed and reduced, every clip; one tier): http://127.0.0.1:8912/level_generation/creatures/mm9_hanndl_reduce_claude/review/viewer/
(`run_creature_review.py check`: 54 switches, 0 failed, no console errors, `review/viewer_check.txt`).
Sheets read (installed left/above, d7 right/below): `review/sheet_face_d7.png`, `review/sheet_face_diff_d7.png` (front close-up, 3/4,
profile, low 3/4, party: face skin, beard, ears and neck black in all five diffs, only the hair shell and the party view's tunic
differ), `review/sheet_body_d7_a.png` (Standing front/3-4/back, Walking, Fidget, Death), `review/close_d7_{1..7}.png` (arms and
torso, skirt front/back, Running, boots, Fidget, shoulders from behind, AttackMelee, Talk, hair from behind above, Death, belt,
boots front, collar/necklace, R and L fingers from outside, front and behind), `review/close_d6_beltlining.png`,
`review/crop_hair_f2_b60.png`, `review/hands_d6_compare.png`, `review/crop_bootR_c4_d6.png`, `review/sets_d7_*.png`.
Look at: the R ring finger's middle joint from outside (a soft facet where the cut middle phalanx meets the exact tip), the R boot shaft
from the side (the painted seam reads a little more clearly), the hair from behind (0.6, a few more shading facets, outline the same).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_hanndl_reduce_claude/before/mm9_hanndl.glb REA_NODE=Hanndl $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_survey.py
R=0.04 $G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
TW2=1 HALO_STRIP=0 HANDS=hand_contact_0.04.npy SHOULDER=1 FOOT=0.10 FOOT_RING=1 CUFF_HAND=1 FOREARM=0.25 TIPS=2 BELTFRONT=1 \
  $G scripts/make_sets_hanndl.py d7
work/run_d7.sh            # MP_PFX=d7_ MP_DMAX_MM=5 MP_DMAX_GROUPS=0:9,3:9,5:4 MP_CHART=1 MP_AUDIT=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=d7 MP_GROUPS=1:0.6,2:0.6,3:0.5,5:0.6,6:0.4, ratio 0.6
work/queue3.sh <pid>      # ladder evaluation (run_mp.sh MP_SKIP=1), build_mp.sh mp_d7_r60 (swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants -> creature's fix_winding -> restore_materials), lod_check x2, gates.sh, see_through.sh
$G ../claude_shared/reduction_uv_audit.py export/mm9_hanndl.glb before/mm9_hanndl.glb --json review/uv_audit_d7.json
python3 scripts/make_viewer_manifest.py d7 "inst_a=Installed (10,060)=before/mm9_hanndl.glb" "red_a=Reduced d7 (8,574)=export/mm9_hanndl.glb"
scripts/shots.sh red_a; scripts/close_shots_hanndl.sh red_a; scripts/finger_shots.sh red_a; $G scripts/shot_sheets.py d7; $G scripts/face_diff_sheet.py d7
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_hanndl.glb` (0), `tools/install_model.py export/mm9_hanndl.glb
--world mm9 --name mm9_hanndl.glb`, the `mm9_actor_models_build_every_binding` regression, and add to `../mm9_hanndl_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_hanndl_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_hanndl.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and viewer
stills only); LOD1-3 and shadow meshes by eye (numbers only); the scene clips' close-ups (only Standing, Walking, Running, Fidget, Talk,
AttackMelee, Death were framed; the gates cover all 27 clips).
