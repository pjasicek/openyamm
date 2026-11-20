# MM9 Skraelos (`mm9_skraelos`, row 257) LOD0 reduction (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md); ledger row 29 of "MM9 reduction"
in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) (prio 3 unique; user 2026-11-05 "do all": uniques reduced too, faces exact).
Lease `mm9reduce:skraelos` (skraelos-reduce-20261105); the creature's own `mm9:skraelos` lease was free. No Meshy, no credits.
**Status: candidate d r52 ready for review, not installed** (c r52 superseded after the orchestrator pre-screen, see below). The creature project `../mm9_skraelos_claude/` was only read.

Source: the installed `assets_source/worlds/mm9/models/mm9_skraelos.glb` (r14 "real hold", sha256 d001ce5546bc, = the creature's
`export/mm9_skraelos.glb`), copied to `before/mm9_skraelos.glb` (the rollback source). Candidate: `export/mm9_skraelos.glb`
(= `work/cand_d52.glb`, sha256 9664caedb828).

| | LOD0 | Skraelos (body) | SkraelosHead | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 13,012 | 8,263 | 4,749 | 6,502 | 2,282 | 755 |
| c r52 (superseded) | 10,754 (-17.4 %) | 6,005 | 4,749 (exact) | 5,373 | 1,856 | 614 |
| **d r52** | **10,952 (-15.8 %)** | 6,203 | 4,749 (exact) | 5,471 | 1,892 | 626 |

Per part: robe + tabard 3,878 -> 2,250 (489 kept: cuffs, collar, hand/prop/necklace contact), hood 1,038 -> 744 (rim + skull edge
kept), bone hands 2,300 -> 2,102 (only the eight palm/metacarpal pieces of 57-104 faces cut, 611 -> 413; every finger bone piece of
up to 40 faces and every grip-contact face exact), necklace cord 975 -> 837 (fangs closed pieces, barely cut), skull / cowl / cap,
staff, held skull and pendant exact.

## d r52: both hands exact (orchestrator pre-screen of c r52, 2026-11-05)
The pre-screen of `review/close_hands_c52.png` found a palm/metacarpal bone beside the held skull turned into a pointed blade (c2, c3) and
a couple more pointed tips: all eight cut pieces are now exact too (`TIP=1000 make_sets_sk.py d`; `SETS=d MP_GROUPS=2:0.6,3:0.7
run_mp.sh d 0.52`; `build_mp.sh mp_d_r52 work/cand_d52.glb`). Robe, hood and necklace are c r52's cut; the hands are the installed
2,300 faces. Ladder r52: 10,952, p99 3.75 / max 18.48 mm (ResurrectSpell), IoU .9967, SSIM .9966, pass. UV audit
(`review/uv_audit_d52.json`): **LOD0 0**; LOD1-3 body 141/133/35 (installed 99/142/85), head 46/81/26 (44/81/24). `face_exact.py`: all
7,914 kept faces (both hands, skull, props) present. Re-run gates (`review/gates_d52/`): arm/hand identical to the installed file in
every clip; held skull 0; staff Death 3.6 cm in 1 of 45 frames (= installed); detached parts 0 (installed 1; the 24-tri robe piece 5.1 mm, concealed from every direction; root-lift/shallow lines as installed: separate bone pieces by design). `close_hands_d52.png` (c0-c3,
read): the hands are the installed ones. Viewer now installed vs d r52 (check: 18 switches, 0 failed, 0 console errors). The other gates,
see-through, face/body sheets and LOD checks below were run on c r52 (same robe/hood/necklace cut); not re-run on d.

## Route
The pose-aware half-edge collapse (`scripts/mpqem.py`, the Scholar's copy, node Skraelos) on the installed GLB's own vertices: every
output corner is an installed vertex, so positions, UVs, normals, joints and weights are the installed bytes; only index buffers
change. Each collapse is scored over every clip at 10 Hz plus a 5-D position/UV quadric (`MP_W5=4`), refused on a flip at rest or in
any pose, when its UV triangle leaves the source charts (`MP_CHART=1`) or fails the UV audit's chart test (`MP_AUDIT=1`), or when its
faces sample colours, ORM or ember glow the source lacks there (`tex_extract.py`: base colour, ORM, emission mask). No linings: the
cloth material is doubleSided (the creature's r6+ choice), so nothing is re-emitted.

Sets (`scripts/glb_parts.py` labels from `../mm9_skraelos_claude/work/uv_ln_tex.npz`, matched exactly: 0 mm; `scripts/contact_sk.py`
posed distances over every 2nd frame of every clip; `TIP=40 scripts/make_sets_sk.py c`):
- **Exact:** the skull (cranium, jaw, teeth, ember eyes = the emission; 3,096), cowl neck tube and inner cap; the staff (736), held
  skull with its socket fills (738) and pendant (179); hood open boundary + 1 ring and hood within 15 mm of the skull; cloth within
  12 mm of the skull/cowl (collar); hand faces within 8 mm of the staff or the held skull in any pose (grip, 155); hand bone pieces
  of up to 40 faces (every finger bone); cloth within 2 cm of a hand in any pose (cuffs, hand-on-robe), within 2 cm of the staff or
  held skull (prop gate), within 6 mm of the necklace. Protected 7,303 of 13,012 (56 %).
- **Own ratios:** hand palm/metacarpal pieces 0.65 (stops at 0.68), hood 0.6, necklace 0.7 (stops at 0.86).
- **Robe + tabard** (3,389 free faces): the ladder ratio.

The staff was not rebuilt: it is one 736-face piece on the head texture set beside the skull's charts, and a rebuild with a
projection bake would rewrite head-set texels for about 4 %.

## Ladders (limits for 1.70 m: p99 <= 5.1 mm, max <= 25.5 mm, IoU >= 0.98, SSIM >= 0.93)
| ladder | groups | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | every hand piece 0.65, hood 0.7, necklace 0.7 | r60 / r50 / r45 | 10,672 / 10,332 / 10,164 | 4.14/12.3, 5.12/25.3, 6.59/31.1 | .997/.997 at r60 | r60 pass, r50 r45 fail |
| b | as a | r57 / r54 / r52 | 10,570 / 10,468 / 10,400 | 4.41/14.0, 4.62/14.8, 4.88/18.5 | .996/.997 at r52 | all pass; **b r52 rejected by eye**: the 14-36-face finger bones turned into shards and blades (`review/close_hands_b52.png`) |
| **c** | hand pieces of up to 40 faces exact, the rest 0.65; hood 0.6; necklace 0.7 | r53 / **r52** / r50 | 10,788 / **10,754** / 10,686 | 3.94/14.8, **4.04/18.5 (ResurrectSpell)**, 4.43/25.3 | **.996 / .997** | all pass; **r52 picked**: r50's max 25.28 mm sits 0.2 mm under the limit for 68 fewer faces |

Three ladders (the cap); the robe is at its limit near r50 (ResurrectSpell and Hit sleeves/hem), so further steps would not move it.

## Checks
- **UV audit** (`review/uv_audit_c52.json`): **LOD0 0 escaping faces** in Skraelos and SkraelosHead. LOD1-3 (Blender decimate as
  installed): body 148/136/36 vs the installed 99/142/85, head 46/81/26 vs 44/81/24.
- **Face exact** (`scripts/face_exact.py`): all 3,096 skull faces, all 1,653 prop faces and all 7,303 kept faces present byte for byte.
- `same_clips.py`: clips, skin, nodes and images identical; materials differ only by an explicit `emissiveTexture.texCoord: 0` (the
  default), so jitter and bone lengths are unchanged.

Gates, installed -> c r52 (`scripts/gates.sh` with the creature's own scripts; `review/gates_inst/`, `review/gates_c52/`):

| gate | installed | c r52 |
|---|---|---|
| arm/hand `--outer-only --exact` | 0 frames > 1 cm in every clip | identical (finger stretch max equal or lower) |
| prop gate | held skull 0; staff 0 except Death 3.6 cm in 1 of 45 frames | held skull 0; staff 0 except Death **1.6 cm** in 1 of 45 |
| collapse face-frames | Standing 960 .. Talk 4,601 | lower in every clip (Standing 738, Talk 2,973, Death 1,533) |
| detached parts | 1 (24-tri robe piece xbk_rt_a3, 8.3 mm in 1 of 856 poses) | 0 (the same piece 5.1 mm, concealed from every direction) |
| see-through (`double=1 step=6`) | torso <= 1 px (8 frames), sleeve L <= 2 (72), head/collar/sleeve R 0 | torso <= 1 (8), sleeve L <= 2 (70), head/collar/sleeve R 0 |
| winding / flat | 0 / 0.00, 0.00 | 0 / 0.00, 0.00 |
| texture quality body / head | 64.2 %, stretch p90 1.05 / 64.6 %, 1.38 | 64.2 %, 1.07 / unchanged |
| bone length | FHP L Calf (library keys) | identical |
| LODs (`scripts/build_lods.py`, soles, hood top and corpse contact protected, snapped; body single-sided for the LOD build, then `double_body.py` as `build_runtime_sk.sh`) | LOD3 1.733 m, 1.2-2.4 cm below its LOD0 in every clip, +1.8 in Dead | every LOD 1.703 m; lowest point per clip equal to LOD0 at every LOD; stretched faces 0 (`work/lod_check_{inst,c52}.json`) |

## Review
- Viewer (installed and c r52, all 9 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_skraelos_reduce_claude/review/viewer/
  (`run_creature_review.py check`: 18 switches, 0 failed, 0 console errors).
- Sheets read at full size: `review/sheet_face_c52.png` (front close-up, 3/4, profile, low 3/4, party), `review/sheet_face_diff_c52.png`
  (skull black in every view; differences only on hood shading), `review/pair_f1_c52.png`, `review/pair_f2_c52.png`,
  `review/sheet_body_c52_a.png` (Standing front/3-4/back, Walking, Fidget, Death, ResurrectSpell, Running),
  `review/close_hands_c52.png` (both hands with staff grip and held skull), `review/close_skull_necklace_staff_c52.png` (left hand
  from below, necklace + pendant, staff head, cuffs from below), `review/close_hood_hem_tabard_c52.png`, `review/ladder_sheet_{a,b,c}.png`;
  rejected b r52: `review/close_hands_b52.png`, `review/sheet_face_b52.png`. Seen: one left-hand bone near the skull's crown is a
  little more pointed in the front close-up; otherwise no visible change.

## Build
`REA_GLB=.../before/mm9_skraelos.glb REA_NODE=Skraelos` `import_source.py` + `dump_mesh.py` (Blender) -> `glb_parts.py` ->
`tex_extract.py` -> `contact_sk.py` -> `TIP=40 make_sets_sk.py c` -> `SETS=c MP_GROUPS=1:0.65,2:0.6,3:0.7 scripts/run_mp.sh c
0.53,0.52,0.50` -> `scripts/build_mp.sh mp_c_r52 work/cand_c52.glb` (swap_mp -> single_body -> build_lods -> skeleton warrior's
shrink_shadow_lods -> carry_variants -> the creature's fix_winding and double_body -> check_winding) -> `reduction_uv_audit.py` ->
`face_exact.py` -> `gates.sh` / `see_through.sh` / `lod_check.py` -> `viewer_tiers.py`, `make_viewer_manifest.py`, `shots.sh`
(`review_specs.py`), `shot_sheets.py`, `face_diff_sheet.py`, `close_sheet.py`.

## Install (not run; on the orchestrator's / user's OK)
`check_winding.py export/mm9_skraelos.glb` (0), `tools/install_model.py export/mm9_skraelos.glb --world mm9`, the binding regression,
`floor_audit.py --world mm9 --match 'MM9 257*'`, and in `../mm9_skraelos_claude/README.md`: "LOD0 reduced post-install on <date> by
`mm9_skraelos_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_skraelos.glb`.

## Not checked
In game; motion at normal speed by eye (frames, gates and viewer stills only); LOD1-3 close up by eye (numbers only); the binding
regression and floor audit (after install); the jitter gate (clips byte-identical).
