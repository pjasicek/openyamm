# MM7 Harpy (`m262`, Harpy / Harpy Hag / Harpy Queen) reduction (2026-10-20)

User request after batch G: "reduce tris count for all 5". Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part needed rebuilding, so the textures,
region mask, tier ramps, rig and clips stay as exported. No Meshy credits. Scripts copied from
`mm7_m162_reduce_claude/` (ladder, UV weights, LODs, LOD check, viewer), `mm6_wwf_reduce_claude/` (`drift_lock.py`)
and `mm6_hrp_reduce_claude/` (`find_doubles.py`); the gates `g4_weights.py`, `g5_hand_stretch.py`, `g6_contacts.py`
are copies from `mm7_m262_claude/scripts/`. Batch G rules: nothing installed, nothing in `assets_dev/` or
`assets_source/`, `mm7_m262_claude/` untouched. Every Blender/Python step runs memory-capped (`scripts/cap.sh`).

Source: `../mm7_m262_claude/export/mm7_m262.glb` (not installed), copied to `work/mm7_m262_source_pre_reduce.glb`
(rollback source), knife `work/mm7_m262_sword_source_pre_reduce.glb`. One material `M262_A` (body and head merged
into a 2080x1024 atlas), tier variants `M262_B` / `M262_C` (two regions: flight feathers, bracer/bodice metal).

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch G export (body) | 9,590 | 4,789 | 1,718 | 565 |
| **reduced (body)** | **7,312** | 3,652 | 1,603 | 918 |
| knife attachment | 700 (unchanged) | | | |

Body -24 %; with the knife 10,290 -> 8,012 (-22 %). The aim of 25-35 % was not reached without changing features:
about a third of the mesh cannot be cut (below).

## Pieces and budgets (`make_groups.py`)

101 pieces: one skin piece (head, torso, arms, thighs), two hands of ~900 faces each, two legs with talons, two
bracers, two wing sheets, two eyes, the long hair (12 pieces in the head texture set) and ~80 feather cards on the
wings and tail.

- **Kept exactly:** every feather card (1,809 faces: decimated at 75 % they collapsed into slivers, p99 11 mm), the
  front of the face (923 faces: any cut, even 88 %, notched the lips and chin), eyes and small fittings, the bracers
  (thin painted rims).
- **Own ratios:** fingers 55 %, hand backs 50 %, hair 70 %, scalp under the hair 50 %, talons and feet 70 %,
  feathered thighs/shins 75 %, wing sheets 75 % (at 60 % the wing sheets carried the worst error and some drift).
- **Rest (torso, arms):** fills the remaining budget.

## Ladder (REA_HEIGHT_M 2.0: p99 <= 6 mm, max <= 30 mm)

| step | config | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a | cards 75 %, hair 60 %, wings 55 % | 7,194 | 11.0 / 59.4 | 0.971 | 0.986 | fail (cards, hair) |
| b | cards kept, hair 80 % | 7,670 | 5.6 / 31.3 | 0.989 | 0.995 | fail (legs) |
| d | + legs 75 %, fingers 65 %, face 75 % | 7,282 | 5.47 / 23.8 | 0.990 | 0.996 | pass, lips notched |
| f | face 88 % | 7,284 | 5.94 / 26.3 | 0.987 | 0.994 | pass, lips notched |
| g | face front kept exactly, wings 60 % | 7,408 | 5.82 / 25.0 | 0.988 | 0.994 | pass, wing drift |
| h | g + drift lock | 7,504 | 6.0 / 25.9 | 0.988 | 0.994 | drift moved (as the playbook warns) |
| **i2** | **g with wings 75 %** | **7,312** | **5.62 / 24.2** | **0.990** | **0.996** | **picked** (r75 fails 6.25 / 29.6) |

Close-ups (source vs picked): `review/close/sheet_i76a_tex.png`, `sheet_i76b_tex.png` (+ `_clay`): face front,
three-quarter and profile, hair from behind, both hands, the knife fist in the attack, chest, both talons and the
kick, legs, wings front and back, wing roots, tail, Attack, Hit, Death. From the GLBs: `review/glbclose/sheet_r76_*.png`.
No feature changed. Texture drift (`texture_drift.py r76`): 10 wing-sheet faces over 40 (p99 25), not visible.

## Build

`TOKEN=<lease> REA_FLOOR_M=0.03 scripts/build_export.sh ladder_i2.blend Cand_76`: `export_cand.py` -> `swap_lod0.py`
(into the rollback source: materials, variants, ramps, clips unchanged) -> `build_lods.py` (0.5 / 0.22 / 0.08,
bounding extremes and every vertex within 3 cm of the floor in Death/Dead protected: with 4 mm the LOD3 corpse sank
11.7 cm) -> `shrink_shadow_lods.py` -> `carry_variants.py`; the knife is copied unchanged.

## Gates (gate copies of both GLBs, `gate_import.py` + `gate_attrs.py` for the master's garment/finger labels)

| gate | source | reduced |
|---|---|---|
| G4 arm stretch p99 (Attack, Walking, Hit, Death) | <= 1.89 | <= 1.84 |
| G5 hand stretch right / left | 2.38 / 1.69 | 2.38 / 1.62 |
| G6 contacts | Death: knife 0.5 cm, right hand 3.4 cm (known) | the same |
| LOD check: lowest point Dead (LOD0-3) | 1.0 / 1.0 / 0.9 / 1.5 cm | 1.0 / 1.0 / 1.0 / -1.1 cm |
| LOD check: stretched faces, bounds | 0, 2.23 m | 0, 2.23 m |
| winding (body, knife) | 0 | 0 |

The Death fall reaches 64 cm under the floor in the source too (a wing tip during the fall, unchanged). Blade gate:
the knife and the rig are unchanged, so its edge share is the batch G result.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m262_reduce_claude/review/viewer/`: batch G export (r100) and
reduced (r76, default) for tiers A, B and C, body only (the knife is the attachment). `run_creature_review.py check`:
30 switches, no console errors.

## For the user to review

- 24 % off the body, short of the 25-35 % aim: feather cards, the face front and the fingers' grip keep ~3,300
  triangles exact.
- LOD3 is 918 triangles (was 565): the floor protection for the corpse costs ~350.
- Shading: the reduced mesh uses plain smooth normals; the chin crease reads a little stronger in untextured views.

## Install (installed 2026-10-21)

Replaces the batch G export of `mm7_m262_claude/` (same binding, nodes, materials and clips; knife unchanged):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m262_reduce_claude/export/mm7_m262.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m262_reduce_claude/export/mm7_m262_sword.glb --world mm7
```

Rollback: `work/mm7_m262_source_pre_reduce.glb`.

Reproduce: `import_source.py` (REA_GLB, REA_NODE=M262), `dump_mesh.py`, `dump_faces.py`, `dump_weights.py`,
`make_groups.py`, the variant masks (`groups_g.npy`, `keep_g.npy`: face front exact, scalp group 8, fingers group 7),
`REA_WEIGHTS=component REA_KEEP_FACES=work/keep_g.npy REA_GROUPS=work/groups_g.npy REA_GROUP_RATIOS=1:0.7,2:0.5,3:0.7,4:0.75,6:0.75,7:0.55,8:0.5 scripts/run_ladder.sh i2 0.76,0.75,0.74`,
`close_m262.py`, `pair_sheet.py`, `texture_drift.py`, `build_export.sh`, `lod_check.py`, `glb_close.py`, gates,
`viewer_tiers.py` (r100, r76), `viewer_manifest.py`.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -70.4; living lowest at +2.6 (suggested hover -0.023936).
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m262.glb export/mm7_m262.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --hover -0.023936 Death Dead --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m262.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).
