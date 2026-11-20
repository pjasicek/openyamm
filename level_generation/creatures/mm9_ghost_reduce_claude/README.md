# MM9 Ghost (`mm9_ghost.glb`, Shadow / Apparition / Specter) triangle reduction, 2026-11-04

Batch row 50 of the MM9 reduction ([brief](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md),
[ledger](../REDUCTION_LEDGER.md)), prio 1 monster (relaxed keep set). No-retexture branch of the
[retopology playbook](../RETOPOLOGY_PLAYBOOK.md): textures, tiers, variants, clips, skin, sockets and nodes are the installed
file's bytes (`splice.py` reports nothing different outside the meshes); only geometry changes. No credits.
Lease `mm9reduce:ghost` (owner ghost-reduce-20261104), released at hand-off. `../mm9_ghost_claude/` was only read.
**Status: ready for review, not installed.**

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed (robe lining counted) | 11,166 | 5,459 | 1,900 | 720 |
| **candidate E r45 `export/mm9_ghost.glb`** (sha256 33ee8884b92d) | **8,430 (-24.5 %)** | 4,193 | 1,890 | 731 |

Rollback source: `before/mm9_ghost.glb` (sha256 801c07a3272b, identical to `../mm9_ghost_claude/export/mm9_ghost.glb`).
Viewer (installed and reduced for each tier; switching keeps clip time and camera; `run_creature_review.py check`: 78
switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_ghost_reduce_claude/review/viewer/

## What was cut and what was kept (LOD0, before the lining; the robe's lining is its faces again, so robe cuts count twice)

| part | installed | E r45 | |
|---|---:|---:|---|
| robe (lofted tube on the 8 chains; tatters are alpha) | 1,570 (+1,570 lining) | 750 (+750 lining) | free faces 1,241 -> 421 (34 %); hem, waist, belt rows and hand-contact faces kept |
| jacket cloth (torso, `Xspine*`/`XCENTER`) | 1,336 | 838 | free 906 -> 408 (45 %); belt and chest trims kept |
| sleeve and shoulder cloth (`Zarm*`) | 1,289 | 941 | 70 % of the free faces (at the ladder ratio the elbows erred 18-20 mm, ladder A); cuffs kept |
| linen (shirt, ruff, lace cuffs) | 995 | 827 | 75 % of the free faces; cuff lace within 3 cm of a hand kept |
| hands (MPFB, five fingers; split over the body and arm materials) | 1,178 | 1,096 | free faces at 65 % target, stopped at 85-88 % (no allowed collapse left); fingertips (every `*3` segment), the hand/sleeve junction (2 rings) and hand-to-hand faces exact |
| head (face, mouth, teeth, eye sockets, hair dome) | 3,228 | 3,228 | primitive byte-identical on LOD0-2 |
| collar bowl and dark patches (zero-UV), belt and trims (ornament mask), cuffs within 3 cm of a hand, hand-contact faces | | | kept exactly |

The head stays whole: its hair dome behind the face is ~450 already coarse faces (a 0.7 cut saves ~130 and steps the
silhouette), so the relaxed head cut was not worth it. LOD1 and LOD2 heads are spliced from the installed file; the LOD3 head
is rebuilt (306 triangles) because the installed one lost its crown (LOD3 height 1.378 m against 1.465 m).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`)

Prim class from the Highwayman's copy of the Banshee's `mpqem.py` (one plane quadric per pose, every clip at 10 Hz, 395 poses;
5-D position+UV rest quadric; no flip at rest or in any pose; texture guard). Every output corner is an existing vertex of the
Ghost's own pre-mirror, pre-lining runtime LOD0 (`../mm9_ghost_claude/export/mm9_ghost_runtime_lod0.glb`), so positions,
normals, UVs and weights are the installed bytes. The texture guard samples the shared base colour (RGB and alpha: the robe's
tatters and fades are alpha) and the region mask (the tier ramps follow it). The robe lining is not cut: `finish_blend.py`
rebuilds it from the reduced robe, as in the installed build. `build_cand.sh` swaps the index buffers into that runtime LOD0 and
runs the Ghost's runtime tail exactly (`build_lods.py` with per-material ratios and the hem and crown as protected points,
shadow shrink, tiers, eye glow, floor, mirror, `finish_blend.py`), then `splice.py`. Checked: the same chain fed the unreduced
LOD0 reproduces all 16 installed primitives byte for byte (`scripts/cmp_meshes.py`).

Keep set and groups: `scripts/make_sets.py` (env defaults are the picked set `e`); `scripts/hand_contact.py` (faces a hand comes
within 4 cm of, and hand faces within 1.5 cm of the other hand, every clip at 30 Hz except Death/Dead, where the Ghost shrinks
to a speck). `finish_blend.py` classifies robe faces by the highest chain-weighted vertex left in the buffer, so the faces on
that vertex are kept (a cut moved the threshold 3.8 mm and dropped the lining under 8 top-row faces in the first build).

## Ladder (Blender `reduce_ladder.py`, exact weights, error over every 3rd frame of every clip; limits for 1.465 m: p99 4.40, max 22.0 mm)

| run | change | LOD0 (with lining) | p99 / max mm | IoU / SSIM | |
|---|---|---:|---|---|---|
| A r60 / r50 / r40 | one ratio for jacket, robe and sleeves | 8,862 / 8,432 / 8,072 | 0.94/13.8, 0.06/20.5, 0.07/20.5 (Death, sleeves) | .997-.994 / .998-.996 | pass, max near the limit on the elbows |
| B r50 / r45 / r40 | sleeves 0.7, robe 0.85 x | | 1.16/11.4, 0.03/9.4, 0.05/11.8 | .997 / .997 | pass; jacket at r40 at its knee (2.0 mm worst collapse) |
| C r45 | B r45 with the robe at 0.34 | 8,138 (-27.1 %) | 1.44 / 11.5 | .997 / .997 | pass; gate: left fingertips 2.5 cm "inside" the coarser right thumb in AttackMelee |
| D r45 | C + hand contact kept | 8,330 | 1.36 / 11.5 | .997 / .997 | pass; same AttackMelee reading (the thumb tip at 36-50 %) |
| **E r45** | D + fingertip segments kept | **8,430 (-24.5 %)** | **1.24 / 11.5** (Aware) | **.998 / .997** | **pass, picked** |

Logs `work/mp_{A..E}.log`, `work/ladder_{A..E}.log`; sheets `review/ladder_sheet_{A..E}.png` (Blender, opaque).

## Gates, installed -> E r45 (the Ghost's own scripts, `scripts/gates.sh`; `review/gates_installed/`, `review/gates_Er45/`)

| Gate | Installed | E r45 |
|---|---|---|
| `check_winding.py` | 0 inverted | 0 inverted |
| `flat_shading_check.py` | body 0.07, arms/head 0.00 | body 0.01, arms/head 0.00 |
| `arm_hand_gate.py --exact --outer-only`, no head | 0 frames over 1 cm; AttackRanged L 1.0 cm; Death forearm 2.3 cm (1 frame, shrinking) | identical except Death forearm 2.4 cm (same frame); finger stretch p99/max equal or lower (Fidget2 R max 1.52 -> 1.38) |
| same, with the head | Fidget2 25 / 21 frames, AttackMelee 7 / 6 (hands in the floating head, MM9's gesture) | Fidget2 25 / 21, AttackMelee **9** / 6 (same 5.2 cm max; the hands are the installed vertices, the head is untouched) |
| `jitter_gate.py` | 0 fails | 0 fails (clips identical) |
| `wrist_gate.py` | hand to sleeve within 5.0 mm | identical in every clip |
| `collapse_gate.py`, face-frames | 3,694 | 1,877; worst-frame counts equal or lower in every region and clip (robe_front 20 -> 14, shoulder_L AttackMelee 14 -> 9) |
| `order_gate.py` (layer errors, per clip) | ArmL 5.9-9.6 %, ArmR 8.0-12.3 %, Head as before | within ±1 point of the installed in every clip; head pairs identical. Rest centres of all four primitives unchanged, so the engine's primitive order is the same |
| `detached_parts_audit.py --fps 24` | head (by design) and both hands (false alarm, see the Ghost README): 362 / 65 / 55 poses | 365 / 67 / 55 poses, same parts and worst values |
| `texture_quality.py` | body atlas 54.4 %, spread 1.04, stretch p90 1.06 | 54.4 %, spread 1.05, stretch p90 1.06; head unchanged |
| LODs (`lod_floor.py`, every clip at 30 Hz) | heights 1.4648 / 1.4648 / 1.4624 / **1.3777**; LOD2/3 lowest points up to 2 cm above LOD0 | 1.4648 / 1.4648 / 1.4647 / 1.4648; lowest point per clip equal to LOD0 at every LOD except LOD3 Hit2 -1.5 mm (still above the floor); no face stretched over 20 x |

## Sheets (viewer shots, installed | reduced | |difference| x 4; `scripts/sheets.sh`, read at full size by the builder)

- `review/sheets/face_{a,b,c}.png`: front close-up, 3/4, true profile, low 3/4, party distance, Taunt. The head has no
  difference pixels in any tier; only the jacket below differs (brocade texels).
- `review/sheets/body_{a,b,c}.png`: Standing front/3-4/back, Walking 3/4 and back, AttackMelee, Fidget2 back, Death.
- `review/sheets/detail_{b,c}.png`: chest front/back, belt and robe front/back, armpits in Fidget2 and AttackMelee, Walking
  robe, Fidget, both hands and cuffs up close, robe from below. Crops `crop_hands_b.png`, `crop_robe_b.png`.
- Earlier candidates' sheets: `review/sheets_Cr45/`, `review/sheets_Dr45/`.

## Build

```sh
cd level_generation/creatures/mm9_ghost_reduce_claude
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"
REA_NODE=Ghost REA_GLB=level_generation/creatures/mm9_ghost_claude/export/mm9_ghost_runtime_lod0.glb $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $BL -P scripts/faces_info.py; python3 scripts/tex_extract.py
scripts/cap.sh python3 -W ignore scripts/hand_contact.py; python3 scripts/make_sets.py e
SETS=e MP_GROUPS=1:0.65,3:0.75,4:0.34,5:0.7 scripts/run_mp.sh E 0.45      # mpqem -> ladder -> compare
SPLICE_KEEP=GhostHead SPLICE_KEEP_LODS=0,1,2 scripts/build_cand.sh Er45; cp export/mm9_ghost_Er45.glb export/mm9_ghost.glb
scripts/gates.sh export/mm9_ghost.glb work/build_Er45/mirrored.glb Er45; python3 scripts/lod_floor.py export/mm9_ghost.glb Er45
(cd ../mm9_ghost_claude && ../claude_shared/gltf_venv/bin/python ../mm9_ghost_reduce_claude/scripts/viewer_tiers.py ../mm9_ghost_reduce_claude/export/mm9_ghost.glb reduced)
scripts/sheets.sh reduced
```

On the user's OK: `check_winding.py export/mm9_ghost.glb` (0), `tools/install_model.py export/mm9_ghost.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, and the line in `../mm9_ghost_claude/README.md`: "LOD0 reduced post-install
on <date> by `mm9_ghost_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_ghost.glb`.

## What to look at

The robe in motion (Walking, Fidget, Death): it has a third of its triangles and bends over fewer rows; hem, waist and
tatters (alpha) are the installed ones. The jacket's brocade on the shoulders and back (larger triangles interpolate the
normal-map tangent frame differently: the difference images show texel noise, the side-by-sides read the same). The
elbows and armpits in Fidget2 and AttackMelee. The hands (65 %, fingertips exact) up close.

## Not checked

In game (not installed; the binding regression runs after install); motion at normal speed by eye (frames, gates and viewer
stills only); LOD1-3 by eye (numbers only); the Shadow tier's detail sheet (face and body sheets only); Android; a Ghost in
front of water fog or another blended effect; the triangle order inside the reduced blended primitives beyond `order_gate.py`.
