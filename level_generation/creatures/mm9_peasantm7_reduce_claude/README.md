# MM9 PeasantM7 (`mm9_peasantm7`, the human townsman, row 90) reduction: candidate a r60 (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk: relaxed keep
set, face exact), ledger row 90 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantm7` (owner
peasantm7-reduce-20261105); the creature's own `mm9:peasantm7` lease was free. Source: the installed
`assets_source/worlds/mm9/models/mm9_peasantm7.glb` (sha256 35e99c36e8e1, identical to `../mm9_peasantm7_claude/export/mm9_pm7.glb`),
copied to `before/` (the rollback source). No Meshy, no credits, no repaint. **Not installed.** `../mm9_peasantm7_claude/` was only
read (its `arm_hand_gate.py`, `jitter_gate.py`, `shrink_shadow_lods.py` and `work/mm9_pm7_clips.glb` run in place), and
`../mm9_peasantm7d_reduce_claude/` only read: every script here is a copy of PeasantM7d's (names changed to `PeasantM7`,
`PeasantM7_A/_B`, `PeasantM7Head_A/_B`, tiers `pm7_a`/`pm7_b`).

**Family note:** PeasantM7d (row 61, reduced to c r60 by `../mm9_peasantm7d_reduce_claude/`) is this body plus elf ears, boot-top and
belt linings and its own head paint, built and installed as its own GLB; this file was cut on its own with the same recipe (same part
layout, same skeleton). The two cuts are not shared vertices: each candidate keeps its own installed vertices.

| | LOD0 | body prim (tunic, breeches, boots, boot cuffs, studs/lacing/buckle) | head prim (face shell, eyes, mouth, hair, hands) | LOD1 | LOD2 | LOD3 | shadow LOD0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 7,313 | 3,610 | 3,703 | 3,656 | 1,314 | 438 | 7,313 |
| **a r60 (`export/mm9_peasantm7.glb` = `export/mm9_peasantm7_a60.glb`, sha256 70d0c3d97c59)** | **5,839 (-20.2 %)** | 2,864 | 2,975 | 2,918 | 1,049 | 348 | 5,839 |

Per group (free faces cut): hands 1,288 -> 772 (0.6, every finger kept; 110 graft/cuff faces exact), hair shell 708 -> 496 (0.7, open
hairline rim locked), breeches/boots/boot cuffs 1,314 -> 822 (0.6), tunic 791 -> 537 (the 5/7 mm distance and texture guards stop
it: r50 gave the identical mesh). Every vertex of the candidate is an installed vertex (positions, normals, UVs, joints, weights are
the installed bytes; only index buffers changed). Clips (13), skin, nodes, materials, region ramps, `KHR_materials_variants`, all 8
images identical (`same_clips.py`). Head part (face shell + neck 1,385, eyes 167, mouth 33) and every kept face present exactly
(`scripts/exact_head.py`, `review/exact_a60.txt`).

## Measured first: protected share
Parts (`scripts/analyze.py`): body prim = tunic with sleeves (1,488), breeches (726), two boots (397 / 385), two boot cuffs (166 / 165),
nine studs/lacing/buckle pieces (283), 3 zero-UV faces, no linings (`twins.py`: 0 pairs). Head prim = face shell (1,385, face, ears,
neck), hair shell (720), two MPFB hands (699 / 699), eyes (85 / 82), mouth (33). Keep set a (`scripts/make_sets_m7d.py a`, PeasantM7d's
set c settings plus `SMALLN=100` so the boot cuffs, which carry no linings here, are cut with the legs): head part, small pieces,
collar, graft junction and cuffs, soles, both boot feet below 10 cm + one ring (PeasantM7d's pre-screen streak fix), shoulder cloth,
cloth under the studs, hand contact (`hand_contact_dm2.py`, every clip at 24 Hz within 4 cm: 67 more) = **3,212 faces (43.9 %)**,
free 4,101; 15 % needed 27 % of the free part, so the run went ahead.

## Route
PeasantM7d's pose-aware half-edge collapse (`scripts/mpqem.py`): chart guard `MP_CHART=1`, texture guard over both tiers (body and head
tiers baked from each tier's region ramps with the engine rule, `scripts/tex_extract.py`; the head set has ramps here, unlike M7d)
and the region masks, texture weight 4, seam slides on the hands, scored over every clip (13) at 10 Hz, distance guard 5 mm (7 mm on
tunic and legs).

## Ladder (limits for 1.793 m: p99 <= 5.38 mm, max <= 26.9 mm, IoU >= .98, SSIM >= .93; `review/ladder_sheet_a.png`)
| ladder | change | LOD0 | p99 / max mm (worst) | IoU / SSIM | result |
|---|---|---:|---|---|---|
| **a** | **set a, hands .6, hair .7, legs .6, tunic r60 (r50 identical)** | **5,839 (-20.2 %)** | **4.60 / 11.6 (Dead:0)** | **.993 / .995** | **PASS, picked** |
One ladder: it passed at -20 % with every gate equal or within single-pixel noise, so no further ladder was run.

## Gates, installed -> a r60 (`scripts/gates.sh` with the creature's own arm/hand and jitter scripts; `review/gates_before/`, `review/gates_a60/`)
- **UV audit** (`../claude_shared/reduction_uv_audit.py`, `review/uv_audit_a60.json`): **0 escaping LOD0 faces in both primitives**.
  LOD1-3 escapes come from the LOD tool's decimate, near the installed file's own (body/head: LOD1 141/108 vs installed 118/96, LOD2
  124/142 vs 135/116, LOD3 45/94 vs 66/96).
- Arm and hand (`--outer-only`, 48 fps): equal in every clip (Fidget R 2.2 cm 10 -> 9 frames, Conv1 L 1.6 cm 24 -> 21, Conv5 L 2.1 cm
  23 -> 23; forearm Conv1 L 1.1 cm both); finger stretch maxima equal, minima within 0.06; wrists equal.
- Jitter vs MM9's untouched clips: identical output (the creature's 2 known fails, Conv1 L and Conv5 L, unchanged).
- Sleeve poke: 0 mm, 0 frames both (candidate vertices 79/88 -> 74/87).
- See-through (`scripts/see_through_gate.py`, every 3rd 30 fps frame of all 13 clips, 16 views; worst px installed -> a60, frames with
  holes): boot L 48 -> 40 (56 -> 58), boot R 19 -> 26 (55 -> 59; Running 6 az180: one-pixel slivers where the boot cuff meets the
  trousers at the back of the knee, `review/gates_a60/see_through_bootR_Running_6_az180_el00.png`), head 14 -> 17 (Death 15 az000, the
  installed crown sliver seen from below, as PeasantM7d), torso 19/19, trousers L 2 -> 5, trousers R 42 -> 36, sleeve L 4 -> 1,
  sleeve R 7 -> 4. Sum of zone maxima 156 -> 148: equal within single-pixel noise.
- Detached parts: 0 both. New advisory note on a60 (does not fail the audit): "root lift" of the R boot off the R boot cuff, 90th
  percentile 0.25 m in AttackMelee 9; the boot and cuff are both rigid on the calf and every vertex is installed, the boot vertices
  within 1 cm of the cuff stay 9.9 mm (installed 8.9) from it in every frame of every clip (`scripts/boot_cuff_gap.py`): bookkeeping of
  the audit's bind contacts on the coarser cuff, not a gap. Flat shading 0.00 both. Winding 0. Bone lengths: the installed 2 (MM9's
  hip slide). Texture quality: body atlas 55.7 % both, stretch p90 1.15 -> 1.18; head 41.2 % both, stretch 1.30 -> 1.29, fragments
  2.6 -> 3.4 %.
- LODs (`scripts/lod_check.py`, every frame of every clip; `scripts/build_lods.py`: ratios 0.5/0.18/0.06, 4 influences, soles/crown/
  corpse contact protected and snapped, 45 of 45 mapped): height 1.8052 m at every LOD; lowest point at LOD1-3 equal to LOD0 in every
  clip (installed LOD3 -0.83..+1.79 cm off LOD0, LOD2 up to +0.42 cm); 0 stretched faces at every LOD, both.

## Review
Viewer (installed and reduced, tiers pm7_a and pm7_b, all 13 clips; `run_creature_review.py check`: 52 switches, 0 failed, no console
errors, `review/viewer_check.txt`): http://127.0.0.1:8912/level_generation/creatures/mm9_peasantm7_reduce_claude/review/viewer/
Sheets read (installed left/above, a60 right/below): `review/sheet_face_a60.png` and `review/sheet_face_diff_a60.png` (front close-up,
3/4, profile, low 3/4, party, both tiers: face skin, ears and neck black in all ten diffs, only the hair shell differs),
`review/sheet_body_a60_a.png` (Standing front/3-4/back, Walking, Fidget, Death), `review/close_a60_a_{1,2,3}.png` (arms, tunic
front/back, Running, boots, Talk arms, shoulders from behind, Hit, L/R hand and cuffs, hair from behind above), `review/close_a60_b_4.png`
(sleeve, lacing and belt buckle, boot cuffs), `review/sets_a_body.png`, `review/ladder_sheet_a.png`,
`review/gates_a60/see_through_bootR_Running_6_az180_el00.png`. Generated, not opened: `review/sheet_body_a60_b.png`,
`review/close_a60_a_4.png`, `review/close_a60_b_{1,2,3}.png`, `review/sets_a_{head,hands}.png`.
Look at: the hand backs (0.6), the hair shell from the side (0.7, hairline locked), the boot cuffs from behind (cut here, kept exact on
no other peasant).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantm7_reduce_claude/before/mm9_peasantm7.glb REA_NODE=PeasantM7 $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py
$G scripts/hand_contact_dm2.py; cp work/hand_contact.npy work/hand_contact_0.04.npy
SMALLN=100 TW2=1 HALO_STRIP=0 HANDS=hand_contact_0.04.npy SHOULDER=1 SMALLC=0.01 FOOT=0.10 FOOT_RING=1 $G scripts/make_sets_m7d.py a
REA_HEIGHT_M=1.793 MP_DMAX_MM=5 MP_DMAX_GROUPS=0:7,3:7 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=a MP_GROUPS=1:0.6,2:0.7,3:0.6 scripts/run_mp.sh a 0.6,0.5
scripts/build_mp.sh mp_a_r60 export/mm9_peasantm7_a60.glb   # swap_mp -> build_lods -> creature's shrink_shadow_lods -> carry_variants -> fix_winding -> restore_materials
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantm7_a60.glb before/mm9_peasantm7.glb --json review/uv_audit_a60.json
$G scripts/exact_head.py export/mm9_peasantm7_a60.glb a
work/queue_a60.sh   # gates.sh installed + a60, see_through.sh installed + a60, lod_check.py installed + a60 (one Blender at a time)
for t in a b; do $G ../mm9_peasantm7d_claude/scripts/viewer_variant.py export/mm9_peasantm7_a60.glb work/viewer_red_a60_$t.glb pm7_$t; done
python3 scripts/make_viewer_manifest.py a60 "inst_a=..=work/viewer_inst_a.glb" "red_a=..=work/viewer_red_a60_a.glb" "inst_b=.." "red_b=.."
HEADUP=0,0.08,0.05 scripts/shots.sh "inst_a red_a inst_b red_b"; scripts/close_shots.sh "inst_a red_a inst_b red_b"
$G scripts/shot_sheets.py a60; $G scripts/face_diff_sheet.py a60; $G scripts/close_sheet.py a60 a c0,c1,c2,c3 review/close_a60_a_1.png  # ...
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantm7.glb` (0), `tools/install_model.py export/mm9_peasantm7.glb
--world mm9 --name mm9_peasantm7.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantm7_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantm7_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantm7.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (frames, gates and
viewer stills only); LOD1-3 and shadow meshes by eye (numbers only); orient/handedness gates (geometry orientation unchanged, every
vertex an installed one); tier B body sheet and most tier B close-ups (generated, not opened: tiers differ only in colours, the
geometry is shared).
