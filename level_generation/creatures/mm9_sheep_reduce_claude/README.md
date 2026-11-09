# MM9 Sheep (`mm9_sheep`) reduction: the Ram's b55 body cut, ready for review (2026-11-05)

Orchestrator request (2026-11-05, after the Ram b55 install): apply the Ram's body cut to the Sheep so the family stays consistent;
head exact; ledger row 97 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:sheep` (owner sheep-reduce-20261105);
`mm9:sheep` was free. Source: the installed `assets_source/worlds/mm9/models/mm9_sheep.glb` (sha256 9993ee7b51d0, identical to
`../mm9_sheep_claude/export/mm9_sheep.glb`), copied to `before/` (rollback). No Meshy, no repaint. **Not installed.**

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 6,370 | 3,184 | 1,146 | 382 |
| **b55 = the Ram's cut (`export/mm9_sheep.glb`, sha256 9d0074ff3b61)** | **4,982 (-21.8 %)** | 2,490 | 896 | 298 |
| alternative r60 = the Ram's ladder-a r60 cut (`export/cand_ram_a_r60/mm9_sheep.glb`, sha256 c0f37d2f91ad) | 5,136 (-19.4 %) | 2,568 | 924 | 308 |

## Route: no new ladder
`scripts/from_ram_cut.py` first proves the Sheep_A primitive byte-identical to the Ram's Ram_A (positions, normals, UVs, joints,
weights and indices), then writes the Ram's b r55 triangles (`../mm9_ram_reduce_claude/work/mp_b_r55.npz`, key Ram_A) as
`work/mp_ram_b_r55.npz` (key Sheep_A); `scripts/build_cand.sh ram_b_r55` swaps the index buffer (every vertex an installed one),
builds LODs with the snap-fixed builder (`scripts/build_lods.py`, the Ram's copy without the horn block: soles, top, ear and tail
tips, hoof extremes, corpse contact; 116 of 116 points snapped), shrinks the shadow LODs (the sheep project's margins), carries the
`sheep_a` variant and runs the UV audit. The sheep's LOD body counts equal the Ram's body LODs (same builder, same body).
**Horn-contact faces:** kept exact as on the Ram (518 neck/poll faces). Dropping them needs a new ladder and would break the
family cut, so they stay.

## Stop rule on the sheep's own height: r55 is over it, r60 passes
The Ram's ladder judged the cut at the Ram's height (1.10 m with horns): p99 3.30 / max 13.4 mm against 3.30 / 16.5. The sheep stands
0.983 m (p99 limit 2.95, max 14.74). `scripts/surface_error.py` (reduce_ladder.py's two-way posed error in Python, every 3rd frame at
24 fps of every clip; it reproduces the Ram ladder's max 13.43 mm at AttackMelee:9):
- b55 (Ram cut): p99 **3.29** mm, max 13.43 (AttackMelee:9) -> **over the sheep's p99 limit by 12 %**;
- r60: p99 2.89, max 14.64 -> pass (max close to the limit); r70: p99 2.22, max 12.48 -> pass.
The sheets below show no visible change at b55. The orchestrator picks: b55 (family-identical to the installed Ram) or r60 (passes
the sheep's own stop rule; gates and UV audit run, no sheets or viewer).

## Gates, installed -> b55 (`scripts/gates.sh`; `review/gates_before/`, `review/gates_b55/`, `review/gates_compare_b55.txt`)
- UV chart audit (`review/uv_audit_ram_b_r55.json`): LOD0 0 escaping. LOD1 131 (installed 118), LOD2 135 (144), LOD3 38 (99).
  r60: LOD0 0 escaping (`review/uv_audit_ram_a_r60.json`).
- Hoof floor contact (`extra_clip_gates.py`): floor min/max identical in every standing/moving clip. **Dead: the corpse lies
  0.15 cm above the floor (installed 0.00)**; the contact vertex is cut (on the Ram the horn touches, so it did not show there). Same at
  r60. 0.15 world-scale cm is far inside `floor_audit.py`'s 2.5-unit tolerance; LODs (`review/lod_table_b55.txt`): every LOD's lowest
  point per clip equals LOD0's (installed LOD2/3 differed by up to 0.3 cm), top 0.983 m at every LOD.
- Fold-over face-frames: 45,601 -> 38,890 (r60: 39,629); per clip lower or equal except Fidget 7,104 -> 7,108.
- Jitter p99 up (Walking 35.6 -> 42.5 mm/f2): a vertex-sample change; `review/jitter_subset_b55.txt` shows every candidate vertex
  moves exactly like its installed vertex and the maximum over vertices is identical (Walking 58.44 = 58.44).
- Body-in-body worst frame: Standing 24 -> 29, Dead 14 -> 22, Death 27 -> 33, Death2 25 -> 30, Running 20 -> 24, Hit 24 -> 28;
  Fidget 59 -> 48, Walking 26 -> 25. `review/bib_detail_b55.txt` (fixed search radius): the extra pairs are in the armpit, groin
  and tail-root creases (XCENTER vs leg pivots, Xback vs Xfleg, tail vs hind leg), where the installed model intersects already.
- Edge stretch p99 up slightly, max equal or lower; detached 0 (1 component), flat 0.00, winding 0, texture stretch p90 1.11 -> 1.13;
  clips, skin, materials, variant and images byte-identical.

## Review
Viewer (installed and reduced b55, 12 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_sheep_reduce_claude/review/viewer/
`run_creature_review.py check`: 24 switches, 0 failed, 0 console errors.
Sheets read (full size): `review/sheet_face_b55.png` + `review/sheet_face_diff_b55.png` (face, eyes, ears, muzzle black in the diff;
only neck/shoulder wool differs), `review/sheet_body_b55_a.png` (Standing front/3-4/back, Walking, Running, Death),
`review/body2_b55.png` (Dead side, AttackMelee side, Fidget, Hit), `review/close_b55_1.png` (neck side, head from above-front,
AttackMelee worst frame, belly), `review/close_b55_2.png` (rump, front and hind legs and hooves, tail). No visible change found.
Look at: the throat-to-chest outline in profile (`close_b55_1` n0, a slightly straighter line) and the leg outlines (`close_b55_2`).

## Build (project folder)
```sh
G="../claude_shared/gltf_venv/bin/python -W ignore"; BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
$G scripts/from_ram_cut.py; scripts/build_cand.sh ram_b_r55; cp export/cand_ram_b_r55/mm9_sheep.glb export/mm9_sheep.glb
scripts/gates.sh before/mm9_sheep.glb before; scripts/gates.sh export/mm9_sheep.glb b55; python3 scripts/gate_compare.py b55
REA_NODE=Sheep $BL -P scripts/lod_check.py -- $PWD/export/mm9_sheep.glb b55; python3 scripts/lod_table.py installed b55
$G scripts/surface_error.py before/mm9_sheep.glb export/mm9_sheep.glb 0.983
$G scripts/viewer_tiers.py before/mm9_sheep.glb inst; $G scripts/viewer_tiers.py export/mm9_sheep.glb red   # + make_viewer_manifest.py
scripts/shots.sh; python3 scripts/shot_sheets.py b55; python3 scripts/face_diff_sheet.py b55
```
Install (on the OK only): `check_winding.py` (0), `tools/install_model.py export/mm9_sheep.glb --world mm9` (or the r60 file), the
binding regression, `floor_audit.py --world mm9`, and the line "LOD0 reduced post-install on <date> by `mm9_sheep_reduce_claude`; a
rebuild from this project must re-run that reduction" in `../mm9_sheep_claude/README.md`. Rollback: `before/mm9_sheep.glb`.

## Not checked
In game; motion at normal speed by eye; LOD1-3 and shadow meshes by eye; r60 by eye (numbers only); orientation/stance/stride gates
(clip-only, byte-identical clips); indoor light; Android.
