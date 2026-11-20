# MM9 Trellborg (`mm9_trellborg`, Trellborg / Kin / Ancient) LOD0 reduction: candidate m81 ready for review (2026-11-04)

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 relaxed keep set),
ledger row 43 of "MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:trellborg` (owner
trellborg-reduce-20261104). No-retexture branch of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md) on the installed r10
(`assets_source/worlds/mm9/models/mm9_trellborg.glb`, sha256 793190d6c9c8, identical to `../mm9_trellborg_claude/export/mm9_trellborg.glb`;
copied to `before/`, the rollback source). No Meshy, no credits. **Not installed.** The creature project `../mm9_trellborg_claude/` was
only read (its gates run from there on our GLBs; output written here).

| | LOD0 | body set (skin, fists, cuffs) | head set (face, hair, tusks) | club | LOD1 | LOD2 | LOD3 | LOD3 height |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| installed | 12,305 | 6,425 | 5,304 | 576 | 6,150 | 2,209 | 734 | 2.316 m (LOD0 2.326) |
| **m81 (`export/mm9_trellborg.glb`, sha256 9b1a6320aaa5)** | **9,781 (-20.5 %)** | 4,911 | 4,478 | 392 | 4,888 | 1,754 | 583 | 2.325 m (= LOD0) |

Clips, skin, nodes, materials, `KHR_materials_variants` and all 17 images are byte-identical to the installed file (`scripts/same_clips.py`).
Face: all 3,242 kept face/neck/ear/tusk triangles are in the candidate with the same positions, UVs, normals and weights (max 4.9e-7 m,
weights 6e-8; `scripts/face_identity.py`); fixed-camera GLB renders change no face pixel (`review/sheet_face_pixel_diff.png`: only hair
and body pixels differ).

## Protected share (measured first)
Labels (`scripts/labels.py`, `skin_split.py`, `hand_thick.py`) from the creature's final rest mesh (`../mm9_trellborg_claude/work/final_c.blend`,
`scripts/dump_final.py`, exact centroid match): body skin 4,235, fists 1,518, cuffs 672, face box 2,776 (the creature's own `reduce_trell.py`
face box: eyes, brows, nose, mouth, lips, ears, jaw, chin, beard), hair 2,040, head-set skin outside the box 328 (by tier A's paint: nape, neck,
ear backs), tusks 160, club 576. Kept share with the relaxed set: 52 % (6,422 faces). The skin is one closed piece (body, head and fists).

## What is kept and what is cut (configuration m)
- **Exact:** face box, head-set skin clusters (>= 8 faces; 64 speckle faces inside the hair go with the hair), tusks, the neck seam (head-set
  faces within 2 rings of the body material), **both fists whole** (fingers, palms, backs, grip contact, graft junction: palm/back at 0.65
  showed a crease and facets on the back of the right hand, `review/sheet_hands_tex.png`, and the user had already rejected these hands
  once), **both cuffs** (decimated at 0.5-0.6 they kinked, `review/sheet_hands_clay.png`), soles (lowest 2 cm), 4 posed-miss spots
  (`err_lock.py`: mid-back in Death2, upper arms), the faces touching the installed corpse's floor contact in Death/Death2/Dead
  (`floor_keep.py`), 9 left-elbow/shoulder spots that collapsed in Standing/Taunt (`collapse_lock.py` on candidate k81).
- **Hair** (reg 5 + speckles, 2,062 faces): 0.6, judged in the front close-up and at party distance (no holes, no steps).
- **Body skin** (torso, arms, legs): the ladder budget (about 60 % at r81).
- **Club rebuilt** (`scripts/club_rebuild.py`, 576 -> 392): make_club.py's own lathe minus two collinear stations, 10 sides instead of 14 on
  the old corner radius, make_club's own cylinder UVs (u linear in the angle, v linear in t), so the club maps stay unchanged and no bake is
  needed; the six nails byte for byte; the affine placement fitted from `work/club.npz` (residual < 1e-6); normals angle-weighted per vertex
  with the u seam unmerged, as installed (selftest 0.02 deg). Radius scale 1.025 (same mid-face radius) put the club 4.6 mm under the floor
  in Death; 1.0 gives 1.2 mm (installed 0.0).
- **Texture weight 8** (`REA_TEXW=8`, MeshLab `extratcoordw`, default 1): the three tiers' fine paint (strap rims, studs, greave mail, fur)
  drifted at the default weight: a jog in the left shoulder strap rim, a dark streak above the right knee and a wavy band in the right
  greave's mail (f81, `review/sheet_fh_tex.png`, `review/sheet_jk_tex.png`). Weight 3 and 8 halve the drifted faces at the same count;
  a global drift lock (e) and a leg-only lock (h) moved the drift elsewhere instead. **Lesson for the batch:** try `REA_TEXW` 3-8 before
  drift locks on painted multi-tier bodies.
- Normals: source vertices keep the installed normal, new ones Blender's export normal (`fix_normals.py`, as the Clan Soldier).
- LODs (`scripts/build_lods.py`, tools/build_actor_lods.py ratios 0.5/0.18/0.06, 4 influences) with protected points: the hair tops
  (3 cm under the top: the default LOD3 lost 2.4 cm), soles, and the floor contact of Death/Death2/Dead (`death_floor_pts.py`; LOD2 went
  1 cm under the floor in Death2 without it).

## Ladder (`scripts/run_ladder.sh`; 2.27 m: p99 <= 6.81 mm, max <= 34.05 mm)

| config | change | step | LOD0 | p99 / max mm | drift faces > 40 (dense, worst tier) | verdict |
|---|---|---|---:|---|---|---|
| a | hair .7, palm/back .65, cuffs .6 | r80 | 9,841 (club kept) | 5.40 / 29.0 | | pass; cuff kinks, crease on the right hand's back |
| b | hair .6, palm/back .6, cuffs .5 | r78 | 9,595 | 5.64 / 29.0 | | pass; same |
| c | fists and cuffs exact, hair .6 | r82 / r81 | 10,089 / 9,965 | 4.7 / 29.0, fail at r81 (Death2 37 mm, mid-back) | | |
| d | c + error lock | r80 / r78 | 9,843 / 9,595 | 5.26 / 27.0, 5.97 / 27.0 | 54 / 110 | r78 dark flecks on the shoulder and chest |
| e | d + drift lock (2 cm) | r81-r79 | | fail (max 39-41 mm) | 51-84 | dropped |
| f | d + floor contact | r81 | 9,965 | 5.08 / 27.0 | 50 | knee streak, greave mail wave, strap rim jog |
| g | f + calves .8 / .7 | r81 | 9,965 | 5.57 / 27.0 | 82-86 | dropped |
| h | f + leg drift lock | r82 / r81 | 10,089 / 9,965 | 5.15 / 27.0 | 51 / 65 | greave fixed, new shoulder scratch |
| j | f, texture weight 3 | r82 / r81 / r80 | | 5.17 / 5.50 / 5.75 | 22 / 33 / 42 | |
| k | f, texture weight 8 | r81 / r80 | 9,965 | 5.72 / 27.0; r80 fails | 22 / 24 | clean; one left-elbow face collapses in Standing (20 face-frames) |
| **m** | k + elbow/shoulder collapse lock | **r81** | **9,965** (+ club rebuild = **9,781**) | **5.78 / 27.0, IoU .993, SSIM .996** | 31 (noise floor 5) | **picked** |

Drift numbers: `scripts/drift2.py` (source sampled every 1.5 mm; the copied `texture_drift.py` compares with 12 random samples per face and
reads the fine paint as drift).

## Gates, installed -> m81 (`scripts/gates.sh`: the creature's own gates on the runtime GLBs; `review/gates_before/`, `review/gates_m81/`)

| Gate | installed | m81 |
|---|---|---|
| Arm/hand (`--outer-only --exact`, 48 fps) | Fidget2 L 6.0 cm (76 f), R 4.5 (121 f), forearm R 4.8; R hand 1.8 cm in every clip (the hidden webbing against the club); Fidget3 L hand 0.6 / forearm 1.4 | identical maxima and frame counts; Fidget3 L hand 0.3 / forearm **1.5** (+0.1, 0 frames over 1 cm); finger stretch max 3.71 -> 2.32 |
| Club in skin (24 fps) | Fidget2 0.2 cm, else 0.0 | identical |
| Grip (`grip_gate.py`, every clip) | inside 1.9 cm, 305 vs; wraps; rigid 0.0 | identical file |
| Wrist / cuff (`wrist_gate.py`) | open edges 13 / 9; hand through cuff 12.64 / 10.39 cm; neck ratio .81 / .94 | identical except L extra edge length 1.93 -> 1.95 cm, L neck ratio .94 -> .96 |
| Jitter (vs `trell_clips0c.glb`) | 10 fails (Walking, Running, Death, Death2 both sides: the clips; AttackMelee2 R 2.0, Hit2 R 2.29) | **9 fails** (AttackMelee2 R 2.0 -> 1.35 passes; Hit2 L 1.67 -> 1.39; the clip-driven fails within 0.3 except Death R 22.17 -> 20.08) |
| Collapse face-frames (all clips) | 3,412 | **2,425**; no clip higher (Standing 0 / 0, Taunt 57 -> 45, Aware 98 -> 77, Dead 465 -> 341) |
| Detached | 14 components, 0 detached | 14, 0 detached; informational root lift now also listed for the left cuff (0.8 cm, 90th pct) |
| Bone lengths, winding, handedness, orient | 0 / 0 / right / as installed | identical |
| Flat shading | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 |
| Texture quality | body 59.8 % stretch p90 1.25; head 55.8 % 1.23 | body 59.7 % 1.30; head 55.5 % 1.30 |
| LODs (`lod_check.py`, every frame) | heights 2.326 / 2.324 / 2.323 / 2.316 m; Death2 lowest -0.2 / -0.2 / -0.1 / -2.6 cm; Dead LOD3 -0.7 cm | 2.325 at every LOD; Death -0.12 cm (club, was -0.07), Death2 -0.16 / -0.16 / -0.16 / -0.68 cm; stretched faces 1/0/0/0 -> 0/0/0/0 |

Jitter note: on earlier candidates the Hit2 L shoulder-skin term read 2.46 (d80) and 2.08 (k81) against the creature's reference (a new
fail); per vertex (`scripts/skin_jitter_where.py`) the excess is the clip's (7.70 installed, 7.72 reduced at the same frame over the whole
shoulder) and the 95th percentile moves with the vertex population. Like-for-like (`ref_swap.py`: the same mesh with the reference clips)
d80 had 10 -> 9 fails; not repeated on m81, which passes Hit2 L directly.

## Review
- Viewer (installed and m81 per tier, all 18 clips):
  http://127.0.0.1:8912/level_generation/creatures/mm9_trellborg_reduce_claude/review/viewer/
  (`run_creature_review.py check`: 108 switches, 0 failed, 0 console errors).
- Sheets read (all in `review/`): `sheet_viewer_face_{a,b,c}.png` and `sheet_viewer_body_{a,b,c}.png` (viewer: face front, 3/4, profile,
  low 3/4, party; body front, 3/4, back, Walking, AttackMelee), `sheet_face_pixel_diff.png`, `sheet_hands_m81_tex.png`,
  `sheet_body_m81_tex.png`, `sheet_body_m81_clay.png`, `sheet_km_tex.png`, `sheet_km2_tex.png` (knees, greaves, chest, shoulders, back,
  hips: installed / k81 / m81), and the earlier configs' sheets named above.
- What to look at: the hair crown in the front close-up (0.6: the top outline is a little more angular, tier C most), the shoulder strap
  rims of tier A, the greaves of A and C, the club (10-sided) at the pommel end.

## Install (not run; on the user's OK)
`check_winding.py export/mm9_trellborg.glb` (0), `tools/install_model.py export/mm9_trellborg.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, `floor_audit.py --world mm9 --match 'MM9 Trellborg*'`, then add to
`../mm9_trellborg_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_trellborg_reduce_claude`; a rebuild from this project must
re-run that reduction". Rollback: `before/mm9_trellborg.glb`.

## Reproduce (project folder)
`REA_GLB=level_generation/creatures/mm9_trellborg_reduce_claude/before/mm9_trellborg.glb REA_NODE=Trellborg` blender `import_source.py`
(0 coincident pairs, 98 open edges: cuff joins) -> `dump_mesh.py` -> `dump_weights.py` -> `dump_final.py` -> `labels.py` -> `skin_split.py`
-> `hand_labels.py` -> `hand_thick.py` -> `make_sets.py a` -> keep_c = keep_a + palm/back + cuffs (groups_c: hair only) -> ladder c ->
`err_lock.py` (Cand_80, 25 mm, 3 cm) -> keep_d -> `floor_keep.py` -> keep_f -> ladder k (`REA_TEXW=8`) -> `build_export.sh` ->
`creature_gates/collapse_gate.py` -> `collapse_lock.py <coll npz> elbow_L,shoulder_L` -> keep_m ->
`REA_TEXW=8 REA_HEIGHT_M=2.27 REA_WEIGHTS=component REA_KEEP_FACES=work/keep_m.npy REA_GROUPS=work/groups_c.npy REA_GROUP_RATIOS=1:0.6
run_ladder.sh m 0.81` -> `REA_BLEND=ladder_m.blend CLUB=1 build_export.sh Cand_81 trell_m81` (export_cand, floor = source's lowest point ->
swap_lod0 -> fix_normals, club restored -> club_rebuild -> death_floor_pts -> build_lods -> shrink_shadow_lods -> carry_variants ->
fix_winding -> check_winding); `viewer_tiers.py`, `make_viewer_manifest.py`, `shots.sh`, `shot_sheet.py`, `gates.sh`, `lod_check.py`,
`face_identity.py`, `same_clips.py`, `glb_close.py`.

## Not checked / not done
- In game; motion at normal speed (frames and gates only); the shadow meshes by eye; LOD1-3 by eye (numbers only).
- The jitter like-for-like run on m81 (done on d80 only); `skin_jitter_area.py` on m81.
- Tier B and C only in viewer shots (Blender close-ups are tier A).
- The cuffs and fists are unchanged, so their known faults (README of the creature: hand leaving the cuff up to 12.6 cm) remain.
