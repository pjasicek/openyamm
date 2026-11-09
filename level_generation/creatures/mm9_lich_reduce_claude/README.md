# MM9 Lich (`mm9_lich.glb`, Lich / Power Lich) triangle reduction, 2026-11-04

Batch row 62 of the MM9 reduction ([brief](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md),
[ledger](../REDUCTION_LEDGER.md)), prio 1 monster (relaxed keep set). No-retexture branch of the
[retopology playbook](../RETOPOLOGY_PLAYBOOK.md): textures, tiers, variants, clips, skin, nodes and images are the installed
bytes (`scripts/same_clips.py`); only index buffers change, every vertex is an installed vertex. No credits.
Lease `mm9reduce:lich` (owner lich-reduce-20261104), released at hand-off. `../mm9_lich_claude/` (approved, frozen) was only read.
**Status: ready for review, not installed.**

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 9,601 | 4,798 | 1,725 | 573 |
| **candidate E r80 `export/mm9_lich.glb`** (sha256 006f423b9843) | **7,983 (-16.9 %)** | 3,990 | 1,433 | 476 |

Rollback source: `before/mm9_lich.glb` (sha256 ddf1889fe680, identical to `assets_source/worlds/mm9/models/mm9_lich.glb` and
`../mm9_lich_claude/export/mm9_lich.glb`).
Viewer (installed and reduced, both tiers; `run_creature_review.py check`: 80 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_lich_reduce_claude/review/viewer/

## Why only -17 %

The Lich was built light: `prep_v2.py` already decimated every part to a budget (cloak 7,507 -> 2,250, robe 999 -> 759, hands
1,528 -> 660 each), and the skull (3,000, the face: sockets, teeth, jaw) stays exact, which is 31 % of LOD0. On the coarse cloth
every further collapse costs real shape: one ratio of 0.7 on sleeves, cape and pants (ladder A) already failed (p99 8.0 mm, sleeve
and pants folds 10-25 mm off at rest). The ladder's stop rule therefore lands at r80; the robe is the cheap part (it and its lining
both halve at 2-3 mm error).

| part (LOD0) | installed | E r80 | |
|---|---:|---:|---|
| cloak (sleeves, cape, hood) | 2,250 | 1,800 | sleeves/cape at the ladder ratio 0.8, hood 0.8 |
| robe + its lining | 759 + 759 | 413 + 413 | 0.5; lining re-emitted from the reduced robe |
| hands (bony, five fingers) | 1,319 | 1,079 | target 0.65, stopped at 71 % (no allowed collapse left); every finger, the wrist opening (2 rings), hand-to-hand contact (8 mm) exact |
| boots | 640 | 532 | 0.75 above the soles (faces within 1.5 cm of the floor exact); flare lining 58 -> 54 |
| belt | 239 | 191 | 0.8 under the texture guard |
| pants | 280 | 240 | ladder ratio; faces the resting fingertips touch kept |
| hood lining | 180 | 144 | re-emitted |
| skull, neck bones (69), medallion (48) | 3,117 | 3,117 | byte-identical |

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, Highwayman copy)

`mpqem.py` scores each collapse over 312 poses (every clip at 10 Hz) plus a position+UV rest quadric, refuses flips at rest and in
any pose, and refuses collapses whose new faces sample colours the source does not have there in either tier (texture guard on
`../mm9_lich_claude/work/tier_lich_{a,b}_Lich.png`, the tier base colours `region_variants.py` bakes). Changes for the Lich:
- part labels from the rigged master (`dump_final_parts.py` on `../mm9_lich_claude/work/rig_final.blend`), carried to the GLB by
  `glb_parts.py` (mirror and floor offset fitted; every face matched to 6e-8 m);
- linings (prep_v2's 4 mm inner copies of hood, robe and boot flares, reversed, **on their own UV charts**): not cut; each surviving
  lined outer face re-emits its lining face from the twin vertices. Lining charts are split by seams of their own, so a twin
  position can hold two lining GLB vertices: the lining face takes the chart of the source face it came from, and outer vertices
  whose twin lies on a lining seam are locked. (The first build, D r80, chose a chart per corner and smeared lining UVs across
  the atlas: lining UV area 0.015 -> 0.45. Fixed in E; with no cut the chain reproduces the installed 6,601 faces exactly.)
- keep set and groups: `make_sets.py` (SOLE=0.015) and `hand_contact.py` (body faces within 4 cm of a hand in any non-corpse pose,
  the own sleeve excluded; hand faces within 8 mm of the other hand: AttackMelee and Resurrect clasp them).

`build_mp.sh` swaps the index buffers into the installed GLB, rebuilds LOD1-3 with `tools/build_actor_lods.py` (default ratios,
4 influences, as the Lich was built) with floor, crown and corpse-contact points protected and snapped to the imported vertices
(`build_lods.py`), then the Lich's own `shrink_shadow_lods.py`, `carry_variants.py`, `fix_winding.py` (0 flipped).

## Ladder (Blender `reduce_ladder.py`, exact weights, error over every 3rd frame of every clip; limits for 1.857 m: p99 5.57, max 27.9 mm)

| run | groups (hands, hood, robe, boots, belt) | step | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| A | .65 / .7 / .7 / .65 / .8 | r70 / r60 | 7,949 / 7,795 | 8.03/30.4, 9.91/49.1 | .991 / .991 | fail |
| B | .65 / .8 / .55 / .75 / .8 | r85 / r80 / r75 | 8,165 / 8,051 / 7,937 | 4.24/20.1, 4.96/20.7, 6.11/30.4 | .995 / .995 | pass / pass / fail |
| C | robe .4 | r85 / r80 | 7,957 / 7,843 | 6.0/21.5, 6.59/21.5 | .994 | fail (robe 11 mm) |
| D | robe .5 | r85 / r80 | 8,097 / 7,983 | 4.41/20.1, 5.09/20.7 | .995 | pass (lining UVs wrong, superseded) |
| **E** | as D, lining charts fixed | r85 / **r80** / r75 | 8,097 / **7,983** / 7,869 | 4.41/20.1, **5.09/20.7** (AttackMelee), 6.15/30.4 | **.995 / .995** | pass / **PASS, picked** / fail |

Logs `work/mp_{A..E}.log`, `work/compare_{A..E}.log`; sheets `review/ladder_sheet_{A..E}.png`. `scripts/rest_err.py` gives the
rest-pose error per part of a step.

## Gates, installed -> E r80 (`scripts/gates.sh`: the Lich's own `arm_hand_gate.py --exact`, `jitter_gate.py`, `sleeve_gate.py` 12 fps front/below; `review/gates_installed/`, `review/gates_Er80/`)

| Gate | Installed | E r80 |
|---|---|---|
| `check_winding.py` | 0 inverted | 0 inverted |
| `flat_shading_check.py` | 0.00 / 0.00 | 0.00 / 0.00 |
| arm/hand (48 fps, every clip) | hand depths: Fidget/ResurrectSpell R 5.5 cm 19 f, Taunt 3.8/5.3, AttackMelee L 2.3 | identical hand depths and frame counts in every clip; forearm equal or lower except AttackMelee R 3.2 -> 3.4, Hit2 L 1.3 -> 1.4 cm; finger stretch max equal (2.98 Resurrect) |
| jitter | 6 fails (AttackMelee, Death, Resurrect, both sides) | the same 6 (clips identical); shoulder-skin p95 is over the remaining vertices, so it moves: AttackRanged L 0.18 -> 1.92 (limit 2.0), Death L 3.44 -> 2.13 |
| sleeve see-through (every clip, front/below) | worst 23 px (Dead2), sum 205 | worst 24 px, sum 207 (Dead2 L +1, Running L +1); poke 0 = 0 |
| `detached_parts_audit.py --fps 24` | 0 detached, 21 components | 0 detached, 21 components |
| `texture_quality.py` body | atlas 56.8 %, spread 2.6, stretch p90 1.28 | atlas 56.8 % (uv sum 56.8 %), spread 2.61, stretch p90 1.31; skull unchanged |
| bone lengths | 12 stretching (clips) | identical (clips identical) |
| LODs (`lod_check.py`, every frame; `scripts/lod_compare.py installed Er80`) | heights 1.851 / 1.851 / 1.852 / 1.852; LOD1-3 rest 0.14 / 0.34 / 0.88 cm above the floor | 1.851 at every LOD, rest on the floor at every LOD; per-clip lowest point now follows LOD0 (installed LOD3 floated 0.7-2.1 cm in Dead/Dead2/Standing and sank 3.5 cm in Death); one LOD2 face stretches > 20 x in 6 clips (a sliver; installed 0, its LOD0 Death2 1 -> 0) |

## Sheets (viewer shots, read by the builder)

- `review/sheet_face_Er80.png`: front close-up, 3/4, profile (the hood), low 3/4, party; both tiers, installed over reduced. The skull
  has no difference pixels (`review/sheet_face_diff_Er80.png`, `review/shots/diff_*`); the differences are on the hood rim and shoulders.
- `review/sheet_body_Er80_{a,b}_{1,2}.png`: Standing front/3-4/back, Walking 3/4 and back, AttackMelee, Death, Fidget and Resurrect
  arms, Running.
- `review/sheet_close_Er80_{a,b}_{1,2}.png`: hands front and 3/4, robe back in Walking, robe front, sleeves in Fidget2, boots,
  shoulders from behind in AttackRanged, robe side in Running.
- Gate tiles: `review/gates_*/sleeve_gate_*.png`.

## Build (project folder)

```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_lich_reduce_claude/before/mm9_lich.glb REA_NODE=Lich $BL -P scripts/import_source.py
$BL -P scripts/dump_mesh.py; $BL -P scripts/dump_final_parts.py; $G scripts/glb_parts.py
scripts/cap.sh $G scripts/hand_contact.py; SOLE=0.015 $G scripts/make_sets.py a
MP_GROUPS=1:0.65,2:0.8,3:0.5,4:0.75,5:0.8 SETS=a scripts/run_mp.sh E 0.85,0.8,0.75     # mpqem -> ladder -> compare
scripts/build_mp.sh mp_E_r80 && cp export/mm9_lich_mp_E_r80.glb export/mm9_lich.glb
scripts/gates.sh before/mm9_lich.glb installed; scripts/gates.sh export/mm9_lich.glb Er80
python3 scripts/sleeve_compare.py review/gates_installed/sleeve.json review/gates_Er80/sleeve.json; python3 scripts/lod_compare.py installed Er80
$G scripts/viewer_tiers.py before/mm9_lich.glb inst; $G scripts/viewer_tiers.py export/mm9_lich.glb red
$G scripts/make_viewer_manifest.py Er80 "inst_a=Lich installed=review/viewer/inst_a.glb" "red_a=Lich reduced E r80=review/viewer/red_a.glb" \
  "inst_b=Power Lich installed=review/viewer/inst_b.glb" "red_b=Power Lich reduced E r80=review/viewer/red_b.glb"
scripts/shots.sh; $G scripts/shot_sheets.py Er80; scripts/close_shots.sh; $G scripts/pair_close.py Er80
```

On the user's OK: `check_winding.py export/mm9_lich.glb` (0), `tools/install_model.py export/mm9_lich.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression, and the line in `../mm9_lich_claude/README.md`: "LOD0 reduced post-install on
<date> by `mm9_lich_reduce_claude`; a rebuild from this project must re-run that reduction". Rollback: `before/mm9_lich.glb`.

## What to look at

The sleeves and cape in motion (Fidget2, AttackMelee, Walking): 80 % of their faces on an already coarse cloth; the folds read the
same in the viewer but bend over fewer rows. The robe (half its faces) swinging in Walking and Running: the hem tatters are the
installed vertices. The bony hands up close (71 % of the free hand faces, every finger kept). The hood rim at the face (hood cut
to 80 %; the skull itself is byte-identical).

## Not checked

In game (not installed; the binding regression runs after install); motion at normal speed by eye (frames, gates and viewer stills
only); LOD1-3 and the shadow meshes by eye (numbers only); the LOD2 sliver face; `floor_audit.py` (it reads installed bindings);
Android. Deeper cuts (cranium behind the face under the hood, ~half the skull's 3,000) were not tried: the brief keeps the skull
face exact and the cranium is one surface with it.
