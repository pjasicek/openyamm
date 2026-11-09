# MM9 Nosferatu (`mm9_nosferatu.glb`) triangle reduction, 2026-11-04

Batch row 37 of the MM9 reduction ([brief](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md),
[ledger](../REDUCTION_LEDGER.md)), prio 1 monster (47 placed on 17 maps). No-retexture branch of the
[retopology playbook](../RETOPOLOGY_PLAYBOOK.md): textures, tiers, variants, clips, skin, sockets and nodes are the installed
file's bytes (`scripts/same_clips.py`); only geometry changes. No credits. Lease `mm9reduce:nosferatu`
(owner nosferatu-reduce-20261104). **Status: ready for review, not installed.** `../mm9_nosferatu_claude/` was only read.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 12,529 (body 7,875 + head 4,654) | 6,262 | 2,473 | 1,526 |
| **candidate `export/mm9_nosferatu.glb` (G50)** | **9,983** (body 5,329 + head 4,654), **-20.3 %** | 4,989 | 2,016 | 1,374 |

Rollback source: `before/mm9_nosferatu.glb` (sha256 46bf22497bb9..., identical to `../mm9_nosferatu_claude/export/mm9_nosferatu.glb`).
Candidate sha256 e9b4b2095338. Viewer (installed and reduced per tier, clip time and camera kept on switch):
http://127.0.0.1:8912/level_generation/creatures/mm9_nosferatu_reduce_claude/review/viewer/ (`run_creature_review.py check`:
102 switches, 0 failed, 0 console errors).

## What was cut and what was kept (per part of the body primitive, `scripts/glb_parts.py` from the creature's `uv_tex.npz`, exact match)

| part | installed | G50 | |
|---|---:|---:|---|
| robe (outer bell, lattice cloth) | 2,160 | 868 | 40 % of free faces; hem, waist and the UV seam locked |
| robe lining (one texel) | 660 | 330 | 50 %, UV checks off (zero UV area); hem ring locked |
| torso | 1,098 | 872 | collar above y 1.58 (322) and hand-contact faces (154) kept, the rest 67.5 % |
| sleeves | 968 | 716 | hand-contact faces (192) kept, the rest 67.5 % |
| hands with claws | 1,498 | 1,052 | 65 %, every finger and claw; faces within 1.2 cm of the other hand kept (224) |
| head set (face, ears, eyes, teeth, plug) | 4,654 | 4,654 | primitive byte-identical on every LOD (LOD1-3 heads spliced from the installed file, `head_splice.py`) |
| neck lining, trims, belt, buckle, pendant, cuffs, sleeve lining | 1,491 | 1,491 | kept exactly (belt at 70 % showed p99 8 mm on the strap) |

Route: `scripts/mpqem.py` (copied from the Banshee reduction, the brief's route for cloth that bends in motion): half-edge
collapse scored over 257 poses (every clip at 10 Hz) plus a position+UV rest quadric. Every output vertex is an installed
vertex, so positions, normals, UVs and skin weights are the installed bytes; no weight transfer. Keep sets:
`hand_contact.py` (faces of robe/torso/sleeves within 4 cm of a hand in any frame, mirrored; hand faces within 1.2 cm of the
other hand) and `collar_keep.py`. `swap_inst.py` writes the new index buffers into the installed GLB.

## Ladder (Blender `reduce_ladder.py`, exact weights, error over every 3rd frame of every clip; limits for 1.741 m: p99 5.22, max 26.1 mm)

| run | robe / torso / sleeves / hands | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---|---:|---|---|---|
| A r60 | 1036 / 658 / 580 / 1168 | 9,941 | 4.04 / 21.4 | .997 / .996 | pass |
| A r50 | 864 / 548 / 484 / 974 | 9,265 | 7.07 / 25.1 | .994 / .993 | fail (hand depth Fidget 1.2 -> 3.5 cm too) |
| A r40, r35 | | 8,769 / 8,645 | 10.8-11.7 / 52.7 | | fail |
| B r55 / r50 / r45 | torso, sleeves 74/68/61 % | 9,999 / 9,625 / 9,261 | 3.64 / 4.38 / 5.66 | | pass / pass / fail |
| C r50 / r45 / r40 | robe cut harder | 9,695 / 9,319 / 9,039 | 4.55 / 5.91 / 7.05 | | pass / fail / fail |
| D r50 | hand contact kept, torso/sleeves 60 % | 9,539 | 5.87 / 25.1 | | fail |
| E r50 | B + hand contact, belt kept | 9,823 | 4.66 / 25.1 | | pass (collar shading changed beside the chin) |
| F r50 | E + collar kept | 9,905 | 4.52 / 25.1 | | pass (right hand 1.1 cm into the left in AttackRanged) |
| **G r50** | F + hand-to-hand faces kept | **9,983** | **4.56 / 25.1** (Death2) | .997 / .995 | **pass, picked** |

The robe stops near 860 faces: below it (C r45, robe 728) the bell's p99 rises past the limit in Death/Death2/Resurrect,
where the lattice lays it on the floor. Logs: `work/run{A..G}.out`, sheets `review/ladder_sheet_{A..G}.png`.

## Gates, installed -> G50 (`scripts/gates.sh`: the Nosferatu's own gate scripts; `review/gates_installed/`, `review/gates_g50/`)
- Clips, skin, nodes, materials, variants, images byte-identical (`same_clips.py`), so jitter, bone length and head orientation are unchanged.
- Arm/hand (`--outer-only --exact`): hand depth equal in every clip (Fidget L 1.2 -> 1.1 cm, 7 -> 4 frames; Taunt 1.4 cm, 6 -> 4
  frames; AttackRanged L 2.1 / R 0.1 cm; Resurrect R 2.9 cm 47 -> 46 frames); forearm equal (4.9 cm AttackRanged R);
  finger stretch lower (p99 1.83 -> 1.68, max 4.55 -> 3.61).
- Cloth: hands and sleeves through the robe 0 in every clip, as before. Lining past the robe: Death 36 -> 39 frames, 2.9 -> 3.3 cm;
  Death2 62 -> 58 frames (8.0 cm); Resurrect 15.6 -> 15.0 cm; Dead 2.3 -> 0.3 cm (inner wall on the floor, from inside the tube).
- Collapse: face-frames 31,894 -> 16,871; worst counts equal or lower in every region except AttackMelee groin 0 -> 1.
- Detached parts 3 -> 2 (one Resurrect frame each, as before). Winding 0 inverted. Flat shading 0.02 -> 0.01 body, 0.00 head.
- Texture quality: atlas 62.1 % unchanged, stretch p90 1.12 -> 1.13; head unchanged.
- LODs (`lod_floor.py`, every clip at 30 Hz): heights 1.9397-1.9402 m (installed 1.9396-1.9399), faces stretched over 20x as
  installed (LOD2/3: one each in Fidget2, AttackMelee, Hit). Lowest point: LOD0 identical per clip; standing clips at LOD2/3
  no lower than installed; **LOD3 in Death goes 1.7 cm under the floor at its lowest frame (installed 0.3 cm)**.

## Sheets (viewer shots, installed | reduced | |difference| x 4; `scripts/sheets.sh`)
Read: `review/sheets/face_{a,b,c}.png` (front, 3/4, profile, low 3/4, party distance, AttackMelee): the face, ears, teeth and
collar have no difference pixels in any tier; the party shot differs only on the sleeve and hand. `review/sheets/body_b.png`
(Standing front/3-4/back, Walking, AttackRanged, Fidget, Death) and `review/sheets/detail_b.png` (chest, back, robe front and
back, Fidget hand on the robe, AttackRanged hands, Running, Hit2, Death2, Dead): no visible change; gold bands stay straight.
Written, not read by me: `body_a.png`, `body_c.png`, `detail_c.png`.

## Build
```sh
cd level_generation/creatures/mm9_nosferatu_reduce_claude
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_NODE=Nosferatu REA_GLB=level_generation/creatures/mm9_nosferatu_reduce_claude/before/mm9_nosferatu.glb $BL -P scripts/import_source.py
REA_PROTECT=Head $BL -P scripts/dump_mesh.py; $BL -P scripts/faces_info.py
G=../claude_shared/gltf_venv/bin/python; $G scripts/glb_parts.py; $G scripts/hand_contact.py; $G scripts/collar_keep.py
MP_KEEP=keep_e2.npy scripts/run_mp.sh G 0.5 robe:0.8,torso:1.35,sleeves:1.35,hands:1.3,belt:2; cp work/mp_r50.npz work/mp_G50.npz
scripts/build_cand.sh G50 export/mm9_nosferatu.glb   # swap_inst -> build_actor_lods (default, 4 influences) -> shrink_shadow_lods -> carry_variants -> head_splice -> fix_winding -> checks
```
On install: `check_winding.py`, `tools/install_model.py export/mm9_nosferatu.glb --world mm9`, the binding regression, and the
line in `../mm9_nosferatu_claude/README.md` that a rebuild must re-run this reduction.

## Not checked
In game (not installed; the binding regression runs after install); motion at normal speed (frames and gates only); LOD1-3 and
shadow meshes by eye; the dark tiers' body and detail sheets by eye (written, not read); Android; indoor light.
