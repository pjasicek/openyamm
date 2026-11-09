# MM9 Ram (`mm9_ram`) reduction: candidate b55 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) and
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md), ledger row 80 of
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:ram` (owner ram-reduce-20261105); the creature's own
`mm9:ram` lease was free. Source: the installed `assets_source/worlds/mm9/models/mm9_ram.glb` (sha256 8e07f14b96b1, identical
to `../mm9_ram_claude/export/mm9_ram.glb`), copied to `before/` (the rollback source). No Meshy, no credits, no repaint.
**Not installed.** `../mm9_ram_claude/`, `../mm9_sheep_claude/` and `../mm9_cow_reduce_claude/` were only read.

| | LOD0 | body (Ram_A) | horns (RamHorn) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 8,074 | 6,370 | 1,704 | 4,036 | 1,452 | 484 |
| **b55 (`export/mm9_ram.glb`, sha256 81f39f49965f)** | **6,686 (-17.2 %)** | 4,982 | 1,704 (exact) | 3,342 | 1,202 | 400 |

Every vertex of the candidate is an installed vertex: positions, normals, UVs, joints and weights are the installed bytes (only
the body's index buffer changed; the horn primitive keeps its accessors). Clips (12), skin, nodes, materials (region mask and
ramps), `KHR_materials_variants` (one tier, `ram_a`) and all 7 images: byte-identical (`scripts/same_clips.py`).

## Body already cut at the build
The ram's body is the sheep's (`../mm9_sheep_claude/`), which `reduce_body.py` decimated at the build: body ratio 0.014, head
0.08 (327k -> 6,122 + mouth cavity). Body edges are about 38 mm, head edges about 15 mm. The horns are procedural sweeps
(`horn_geom.py`, 36 stations x 12 sides). The sheep's installed body (`mm9_sheep.glb`, row 97) is byte-identical to Ram_A
(positions, UVs, joints, weights and indices), so this cut's Ram_A index buffer (`work/mp_b_r55.npz`, key `Ram_A`) can be
applied to the sheep unchanged (6,370 -> 4,982) if the orchestrator wants the family consistent; that keeps the horn-contact faces
exact on the sheep too, which it does not need.

## Measured first: protected share 61.8 %
`scripts/ram_sets.py a`: exact = both horns (1,704, RamHorn kept whole), the whole head (head-weighted skin > 0.5: face skin,
eyes, muzzle, nostrils, mouth cavity, ears; 2,584 faces, grown 2 rings = 2,726; the ram's head has no wool: it is all region G
head skin and B pink), the horn contact (body faces within 2 cm of a horn vertex: 518), hooves plus one ring (560) and soles
(within 2 cm of the floor: 194). 4,990 of 8,074 exact; free 3,084 (body wool, legs, tail). -15 % needed 39 % of the free faces.

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Cow's copy)
Scored over every clip at 10 Hz plus a position+UV rest quadric; only removes vertices. Texture guard on the region mask (G, B, A)
and the shared base colour, chart guard (12 samples) on. Limits for the 1.100 m GLB height (body 0.98 m, horn top 1.094 m):
p99 <= 3.30 mm, max <= 16.5 mm (ladder a's compare ran first with Blender's 1.162 m dimension, re-run at 1.10; same verdicts).

| ladder | step | LOD0 | p99 / max mm (worst) | IoU / SSIM | |
|---|---|---:|---|---|---|
| a | r80 / r70 / r60 | 7,456 / 7,148 / 6,840 | 1.46/12.5, 2.23/12.5, 2.90/14.6 (AttackMelee) | .9978/.9977 at r60 | pass / pass / pass |
| b | **r55** / r50 / r45 | **6,686** / 6,532 / 6,378 | **3.30/13.4 (AttackMelee)**, 3.83/14.3, 4.63/17.5 (Fidget) | .9966/.9972 at r55 | **PASS, picked** / fail / fail |

r55 sits on the p99 limit (3.30 = 3.30); r60 (6,840, -15.3 %, `work/mp_a_r60.npz`) is the fallback with margin if the reviewer
prefers it. Two ladders used.

## Gates, installed -> b55 (`scripts/gates.sh`: the ram project's own gates; `review/gates_before/`, `review/gates_b55/`, `review/gates_compare_b55.txt`)
- UV chart audit (hard gate, `review/uv_audit_b55.json`): LOD0 0 escaping faces in both primitives. LOD1 body 131 (installed 118),
  LOD2 135 (144), LOD3 38 (99); horn LODs as installed.
- Hoof floor contact (`extra_clip_gates.py`, every clip): floor min/max identical in every clip except Death max 7.2 -> 7.5 cm
  (a lifted frame in the fall, not contact). LODs (`scripts/lod_check.py`, every frame, `review/lod_table_b55.txt`): every LOD's
  lowest point per clip now equals LOD0's (installed LOD2/LOD3 floated up to +0.2 cm or sank up to -1.1 cm); top 1.094 m at every
  LOD; stretched faces 1 -> 1 (LOD0, as installed), 0 at LOD1-3.
- Fold-over face-frames (the sheep's `fold_measure.py`): total 45,601 -> 38,890; per clip lower or equal except Fidget 7,104 -> 7,108.
- Edge stretch (`gates.py`): p99 up slightly in every clip (larger faces; Death2 4.17 -> 4.31, Fidget 2.82 -> 2.97), max equal or
  lower (Hit2 15.3 -> 10.6). Bone ratio identical. Loop seams unchanged (clips byte-identical).
- Jitter p99: Walking 27.95 -> 33.66 mm/f2, others +0-3 %. A sample-set change: `scripts/jitter_subset.py`
  (`review/jitter_subset_b55.txt`) shows every candidate vertex moves exactly like its installed vertex (difference 0) and the
  maximum over vertices is identical (Walking 58.44 = 58.44); the reduction dropped low-motion body vertices (5,025 -> 4,331).
- Body-in-body pairs (worst frame): Standing 24 -> 29, Dead 20 -> 28, Running 20 -> 24, Walking 25 = 25; Fidget 59 -> 48, Hit 76 -> 71,
  Death 114 -> 105. `scripts/bib_detail.py` at a fixed search radius: the extra pairs are in the armpit/groin creases (XCENTER vs
  the leg pivots, Xback vs Xfleg, tail vs hind leg), where the installed model already intersects; head/neck pairs unchanged.
- Detached 0 (3 components), flat shading 0.00 / 0.00, winding 0, texture quality: atlas and density unchanged, body stretch p90
  1.11 -> 1.13. No see-through fix, arms or held props on this model.

## Review
Viewer (installed and reduced, 12 clips): http://127.0.0.1:8912/level_generation/creatures/mm9_ram_reduce_claude/review/viewer/
`run_creature_review.py check`: 24 switches (2 models x 12 clips), 0 failed, 0 console errors.
Sheets read (full size): `review/sheet_face_b55.png` (front close-up, 3/4, true profile, low 3/4, party; installed over reduced),
`review/sheet_face_diff_b55.png` (|installed - reduced| x4: face, eyes, ears, horns black; only the chest/shoulder wool differs),
`review/sheet_body_b55_a.png` (Standing front/3-4/below, Walking, Running, Death), `review/body2_b55.png` (Standing back,
AttackMelee side, Fidget, Hit), `review/close_b55_1.png` (neck/chest side, head from above-front, AttackMelee worst frame side,
belly from below), `review/close_b55_2.png` (rump, front and hind legs with hooves, tail), `review/ladder_sheet_{a,b}.png`.
No visible change found. Look at: the front and hind leg outline at close range (`close_b55_2` h0/k0: a slightly harder knee
corner), the belly line under the flank in AttackMelee (`close_b55_1` m0).

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G="../claude_shared/gltf_venv/bin/python -W ignore"
REA_GLB=level_generation/creatures/mm9_ram_reduce_claude/before/mm9_ram.glb REA_NODE=Ram $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/ram_sets.py a
SETS=a REA_HEIGHT_M=1.10 MP_GROUPS= scripts/run_mp.sh b 0.45,0.5,0.55     # mpqem -> reduce_ladder -> compare
scripts/build_cand.sh b_r55; cp export/cand_b_r55/mm9_ram.glb export/mm9_ram.glb   # swap_mp, LODs, shadow fix, variants, UV audit
scripts/gates.sh export/mm9_ram.glb b55; python3 scripts/gate_compare_ram.py b55
REA_NODE=Ram $BL -P scripts/lod_check.py -- $PWD/export/mm9_ram.glb b55; python3 scripts/lod_table.py installed b55
$G scripts/viewer_tiers.py before/mm9_ram.glb inst; $G scripts/viewer_tiers.py export/mm9_ram.glb red
python3 scripts/make_viewer_manifest.py b55 "inst_a=Installed (8,074)=review/viewer/inst_a.glb" "red_a=Reduced b55 (6,686)=review/viewer/red_a.glb"
scripts/shots.sh; python3 scripts/shot_sheets.py b55; python3 scripts/face_diff_sheet.py b55
```
Install (on the OK only): `check_winding.py export/mm9_ram.glb` (0), `tools/install_model.py export/mm9_ram.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, `floor_audit.py --world mm9`, and add to `../mm9_ram_claude/README.md`:
"LOD0 reduced post-install on <date> by `mm9_ram_reduce_claude`; a rebuild from this project must re-run that reduction".
Rollback: `before/mm9_ram.glb`.

## Not checked
In game (not installed; binding regression and floor audit run after install); motion at normal speed by eye (stills, numbers
and the viewer check only); LOD1-3 and shadow meshes by eye (numbers only); the orientation, symmetry, stance and stride gates
(they read only the clips and bones, which are byte-identical); indoor light; Android. Several scripts in `scripts/` are
Cow/Imp/Gezzampt copies this route did not use (`cow_sets.py`, `close_shots.sh`, `upper_shots.sh`, `gate_compare.py`, `export_cand.py`).
