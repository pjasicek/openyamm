# MM9 PeasantM7d (`mm9_peasantm7d`, the elf townsman, row 61) reduction: candidate c r60 ready for review (2026-11-05; lease released)

**Fix pass c (orchestrator pre-screen, 2026-11-05):** b60 looked the same except a dark diagonal streak on the R boot above the sole at
close range (`review/crop_boot_toe_b60_d.png`). Set c = set b + every boot face with centroid below 10 cm (sole, toe, vamp; both boots by
height, so symmetric: 189 L / 181 R) plus one ring kept exact (`FOOT=0.10 FOOT_RING=1`). The streak is gone in both tiers
(`review/crop_boot_toe_c60.png`: installed | b60 | c60, D and C; `review/close_c60_{d,c}_boots.png`). c r60: **8,012 (-16.8 %)**,
LOD1-3 4,004 / 1,439 / 480, shadow LOD0 6,786; ladder p99 3.84 / max 13.0 mm, IoU .995, SSIM .995 PASS; UV audit 0 LOD0 escaping faces
(`review/uv_audit_c60.json`); head part and every kept face exact (`review/exact_c60.txt`); gates (`review/gates_c60/`) identical to b60's
below in every number (arm/hand, jitter 0 fails with shoulder skin = installed, sleeve poke 0, lining per clip, detached 0, winding 0,
bones 0, flat 0.00, texture quality, see-through per zone, LOD heights 1.8052 m and LOD floor = LOD0); viewer check 40 switches, 0 failed.
Candidate `export/mm9_peasantm7d.glb` = `export/mm9_peasantm7d_c60.glb` (sha256 e70afcb7e42c); the b60 export is deleted. The b sections
below stay as the record; the build adds `FOOT=0.10 FOOT_RING=1` to make_sets and uses SETS=c, label c, `mp_c_r60`.

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 61 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm7d` (owner
peasantm7d-reduce-20261105); the creature's own `mm9:peasantm7d` lease (and `mm9:peasantm7`) was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm7d.glb` (sha256 07e75223bfe1, identical to `../mm9_peasantm7d_claude/export/mm9_pm7d.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm7d_claude/` was only read
(its gate scripts, `shrink_shadow_lods.py`, `viewer_variant.py` and `work/mm9_pm7d_clips.glb` run in place).

**Family note:** PeasantM7d is PeasantM7's body (`mm9_peasantm7.glb`, ledger row 90, 7,313; the creature README: body identical
to 0.2 cm) plus two elf ears (588), boot-top and belt linings (1,729) and its own head paints, built and installed as its own GLB.
Only `mm9_peasantm7d.glb` was reduced here. PeasantM7 has no linings and no ears, so its free share is smaller (body built at 0.42,
head shell + hands ~3.7k); it can reuse these scripts (same part layout, same skeleton), but this cut is not carried over to it.

| | LOD0 | body prim (tunic, breeches, boots, cuffs, studs, linings) | head prim (face shell, ears, eyes, mouth, hair, hands) | LOD1 | LOD2 | LOD3 | shadow LOD0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 9,630 | 5,339 | 4,291 | 4,813 | 1,733 | 577 | 8,080 |
| b r60 (superseded, export deleted) | 7,822 (-18.8 %) | 4,263 | 3,559 | 3,909 | 1,406 | 468 | 6,626 |
| **c r60 (`export/mm9_peasantm7d.glb`, sha256 e70afcb7e42c)** | **8,012 (-16.8 %)** | 4,453 | 3,559 | 4,004 | 1,439 | 480 | 6,786 |

Per group (free faces cut): hands 1,288 -> 772 (0.6, every finger kept; 110 graft/cuff faces exact), hair shell 720 -> 504 (0.7, open
hairline rim locked), breeches/boots/cuffs 1,487 -> 969, tunic 752 -> 548 (the guards stop it), body linings 1,120 -> 766 (re-emitted
from the cut outer faces). Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are the
installed bytes; only index buffers changed). Clips (10), skin, nodes, materials, region ramps, `KHR_materials_variants`, all 9 images:
identical (`same_clips.py`). Head part (face shell + neck 1,385, elf ears 588, eyes 167, mouth 33) and every kept face: present exactly
(all corner attributes, `scripts/exact_head.py`, `review/exact_b60.txt`).

## Measured first: protected share
Parts (`scripts/analyze.py`): body prim = tunic with sleeves (1,804), breeches (1,250), two boots (609 / 589), two boot cuffs (404 / 400),
nine studs/lacing/buckle pieces (283); 1,550 of its faces are one-texel linings or rim strips (the creature's `linings.sh`). Head prim =
the face shell (1,385: face, neck, a little scalp; the hair shell is the scalp: only 96 shell faces lie under the hair, ray test), the
hair shell (720), two MPFB hands (699 / 699), two procedural elf ears (294 / 294), eyes (85 / 82), mouth (33).
The whole head part is exact (2,173, 22.6 %). Keep set b: 4,503 faces (46.8 %) incl. linings of kept faces; ~15 % was reachable from the
hands, hair and the lined breeches/boots, so the run went ahead.

Keep set b (`scripts/make_sets_m7d.py b`, env `TW2=1 HALO_STRIP=0 HANDS=hand_contact_0.04.npy SHOULDER=1 SMALLC=0.01`): head part whole;
small pieces (studs, lacing, buckle); collar (tunic within 1 cm of the head prim); graft junction and cuffs (within 1.5 / 4 cm of a hand
vertex); soles; rim strips, loose linings and their 6 mm halo; lining pairs that both carry UVs; hand contact (every non-hand face a hand
comes within 4 cm of in any clip at 24 Hz, `hand_contact_dm2.py`: 31 more); the shoulder cloth (tunic faces with a Clavicle/UpperArm
dominated vertex: 427); the cloth under the studs (tunic within 1 cm of a small piece: 38).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, PeasantDM2's copy)
Chart guard `MP_CHART=1`, texture guard over both tiers (D, C) and the region mask (`scripts/tex_extract.py`; the sleeve channel A folded
into the mask's third channel), texture weight 4, seam slides on the hands, scored over every clip at 10 Hz, distance guard 5 mm (7 mm on
tunic and legs, `MP_DMAX_GROUPS=0:7,3:7`; PeasantDM2's 3.5/5 mm scaled to 1.79 m), linings re-emitted from `work/twins.npz`
(`twins.py`, with the one-texel-per-face rule).

## Ladders (limits for 1.793 m: p99 <= 5.38 mm, max <= 26.9 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_<label>.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| a | set a (no shoulder or stud keep), hands .6, hair .7, legs .6, tunic r60 (r50 identical: guards stop the tunic) | 7,672 (-20.3 %) | 4.63 / 13.0 (Dead:0) | .993 / .993 | ladder pass; built a60: UV audit 0, but jitter shoulder skin AttackMelee L 0.24 -> 1.48, R 0.45 -> 1.94 mm/f2 (limit 2.0) and a new detached 1-triangle collar stud (tunic under it cut, 4.4-5.6 mm gap in 562 of 572 poses). Export deleted |
| b | a + shoulder cloth + cloth under the studs kept | 7,822 (-18.8 %) | 4.26 / 13.0 (Dead:0) | .994 / .995 | PASS; every gate equal or within single-pixel noise; pre-screen: R boot streak |
| **c** | **b + boot soles/toes/vamps (below 10 cm) + one ring exact (fix of b, same ratios)** | **8,012 (-16.8 %)** | **3.84 / 13.0 (Dead:0)** | **.995 / .995** | **PASS, picked; gates = b's; streak gone** |

## Gates, installed -> b r60 (`scripts/gates.sh` with the creature's own gate scripts; `review/gates_before/`, `review/gates_b60/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_b60.json`): **0 escaping LOD0 faces in both primitives**.
  LOD1-3 escapes come from the LOD tool's decimate, near the installed file's own (body/head: LOD1 174/87 vs installed 137/84, LOD2
  138/136 vs 137/113, LOD3 51/107 vs 66/99).
- Arm and hand (`--outer-only`, 48 fps): equal in every clip (Fidget R 2.2 cm, MM9's chin scratch, 10 -> 9 frames); forearms 0; finger
  stretch maxima equal, minima within 0.05; wrists equal.
- Jitter vs MM9's untouched clips: 0 fails both; shoulder skin identical in every clip (shoulder cloth kept since b).
- Sleeve poke: 0 mm, 0 frames both (candidate vertices 79/88 -> 74/87: hand vertices removed).
- Linings (`scripts/lining_gate.py`): body prim max outward equal or lower per clip (Walking 2.94 -> 2.73, Cower 2.38 -> 2.02 mm);
  head prim 3.08 -> 3.38 mm (5 -> 6 vertices; the ears' / eyes' twin vertices are the installed ones, the nearest outer surface is the cut hair).
- See-through (creature's `see_through_gate.py`, every 3rd 30 fps frame, 16 views; worst px, installed -> b60, same frames and views):
  torso 19/19 (120 -> 119 frames), head 14 -> 17 (Death 15 az000: the installed crown sliver seen from below, `review/st_pair_head_Death_15_az000_el00.png`),
  boot R 10 -> 12, boot L 4 -> 2, trousers R 8/8, trousers L 0 -> 1, sleeve R 7 -> 8, sleeve L 4 -> 1. Equal within single-pixel noise.
- Detached parts: 0 both (a60 had 1); notes only (root lift / shallow on the boots, breeches and hair as installed).
  Flat shading 0.00 both. Winding 0. Bone lengths 12 checked, 0 stretching. Texture quality: body atlas 55.7 % both, stretch p90 1.13 -> 1.15;
  head 43.7 % both, stretch 1.31 -> 1.30, fragments 2.5 -> 3.3 %.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: tool ratios 0.5/0.18/0.06, 4 influences, soles/crown/
  corpse contact protected and snapped, 45 of 45 mapped): height 1.8052 m at every LOD; lowest point at LOD1-3 equal to LOD0 in every clip
  (LOD2 Dead/Death -0.26/-0.37 vs -0.0/-0.21 cm); installed LOD3 floated +0.8..+1.2 cm (Standing 1.15) and LOD2 up to +0.42 cm. 0 stretched
  faces at every LOD, both. Logs `work/lod_check_{installed,b60}.{json,log}`.

## Review
Viewer (installed and reduced, both tiers, all 10 clips; `run_creature_review.py check`: 40 switches, 0 failed, no console errors,
`review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm7d_reduce_claude/review/viewer/
Sheets read (installed left/above, b60 right/below): `review/sheet_face_b60.png` and `review/sheet_face_diff_b60.png` (front close-up,
3/4, profile, low 3/4, party; both tiers: face skin, ears and neck black in all ten diffs, only the hair shell differs),
`review/sheet_body_b60_c.png` (Standing front/3-4/back, Walking, Fidget, Death), `review/sheet_body_a60_d.png`, `review/close_b60_d_{1,2,3,4}.png`
(arms, tunic front/back, Running, boots, Talk arms, shoulders from behind, Hit, L/R hand and cuffs, hair from behind above, sleeve, lacing
and belt buckle, boot cuffs), `review/close_b60_c_2.png`, `review/close_b60_fingers_d.png` (both hands with fingertips, Fidget belt),
`review/crop_boot_toe_b60_d.png`, `review/ladder_sheet_a.png`, `review/sets_a_{body,head}.png`, `review/st_pair_head_Death_15_az000_el00.png`.
Generated, not opened: `review/sheet_body_b60_d.png`, `review/close_b60_c_{1,3,4}.png`.
Look at: the boot toes (fixed in c: `review/crop_boot_toe_c60.png`), the hand backs (0.6: a few flatter planes in the shading, outline and fingers the same),
the hair shell from the side (0.7, hairline locked).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantm7d_reduce_claude/before/mm9_peasantm7d.glb REA_NODE=PeasantM7d $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py
$G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
TW2=1 HALO_STRIP=0 HANDS=hand_contact_0.04.npy SHOULDER=1 SMALLC=0.01 $G scripts/make_sets_m7d.py b
REA_HEIGHT_M=1.793 MP_DMAX_MM=5 MP_DMAX_GROUPS=0:7,3:7 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=b MP_GROUPS=1:0.6,2:0.7,3:0.6 scripts/run_mp.sh b 0.6
scripts/build_mp.sh mp_b_r60 export/mm9_peasantm7d_b60.glb   # swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm7d_b60.glb before/mm9_peasantm7d.glb --json review/uv_audit_b60.json
$G scripts/exact_head.py export/mm9_peasantm7d_b60.glb b
work/queue_b60.sh   # gates.sh, see_through.sh, lod_check.py installed + b60 (one Blender at a time)
for t in d c; do $G ../mm9_peasantm7d_claude/scripts/viewer_variant.py export/mm9_peasantm7d_b60.glb work/viewer_red_th_$t.glb pm7d_$t; done
python3 scripts/make_viewer_manifest.py b60 "inst_d=..=work/viewer_inst_th_d.glb" "red_d=..=work/viewer_red_th_d.glb" "inst_c=.." "red_c=.."
HEADUP=0,0.08,0.05 scripts/shots.sh "inst_d red_d inst_c red_c"; scripts/close_shots.sh; $G scripts/shot_sheets.py b60; $G scripts/face_diff_sheet.py b60
$G scripts/close_sheet.py b60 d c0,c1,c2,c3 review/close_b60_d_1.png   # ... _2 .. _4, tier c
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm7d.glb` (0), `tools/install_model.py export/mm9_peasantm7d.glb
--world mm9 --name mm9_peasantm7d.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantm7d_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantm7d_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantm7d.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); orient/handedness gates (geometry orientation unchanged, every
vertex an installed one); the C tier's fingertip close-up (tier C differs from D only in colours, the geometry is shared).
