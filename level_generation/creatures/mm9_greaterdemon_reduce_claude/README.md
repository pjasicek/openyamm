# MM9 Greater Demon (`mm9_greaterdemon`, MM9 Demon B) LOD0 reduction: fix-pass candidate j85 ready for review (2026-11-04)

## Fix pass (2026-11-04, after the rollback): chart guard, UV audit 0
h85 was installed and rolled back with the batch: `claude_shared/reduction_uv_audit.py` found 3 LOD0 membrane faces off the
painted charts (off 0.33-0.64, up to 14.6 texels, colour error up to 8.2; light wedges in `review/close_h85_escapes.png`).
They were all **re-emitted lining faces**, not collapses: in 3 places the two sheets of the solidified shell are triangulated on
opposite quad diagonals, so the twin of an outer face is not a lining face and crosses the chart border. Changes
(`scripts/mpqem.py`, lease owner greaterdemon-reduce-fix-20261104):
- the Imp's chart guard (`MP_CHART=1`, on by default in `run_mp.sh`): a collapse is refused when any of 91 samples of a new
  face's UV triangle, or of its re-emitted lining twin, lies off the source charts (2048 raster, dilated 2 texels);
- the outer faces on a mismatched diagonal (3) are frozen (all vertices locked) and their quads re-emitted as the original
  lining faces; `MP_W5` exposes the texture weight (left at 1.0);
- `build_lods.py` snaps the protected points to the imported vertices (the brief's LOD-protection trap; 12 of 12 mapped).
Ladder j (set h, wing bones 0.55, membrane 0.5): r85 8,418 p99 11.42 / max 32.0 mm, IoU .9954, SSIM .9919 PASS (r80 8,330
fail). The chart guard refused nothing in the collapses: the cut sheet, skin and wing bones were already on their charts.
**j85 = `export/mm9_greaterdemon.glb` (= `_j85.glb`, sha256 3ae0fcadcb0b), LOD 8,418 / 4,158 / 1,378 / 369.**
- UV audit (`review/uv_audit.json`): LOD0 0 escaping faces in all three primitives; LOD1-3 at the source LODs' own baseline
  (body 151/156/49 vs 132/156/69, membrane 5/15/18 vs 2/3/25, heads 72/79/12 vs 72/81/14: Blender's decimate).
- Gates (`review/gates_j85/`) equal to h85's below: edge min/max no worse, lowest point per clip identical, detached 12 = 12,
  wing attachment worst 4.24 = 4.24 cm, winding/bone 0, LOD bounds kept, LOD3 floor -0.56 cm (installed -0.36).
- Sheets read: `review/close_j85_escapes.png` and `review/close_h85_escapes.png` (the three former escape sites from both sides
  of the shell in the bind pose plus the whole left membrane front and back: the h85 wedges are gone in j85),
  `review/close_j85_heads.png` (heads identical), `review/close_j85_body.png` (no visible change). One skin, so one tier.
- Viewer (installed vs j85): http://127.0.0.1:8912/level_generation/creatures/mm9_greaterdemon_reduce_claude/review/viewer/
  (38 switches, 0 console errors).

The first pass follows (its candidate h85 has the same counts and gates).

Batch: [REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-1 monster,
relaxed keep set), ledger row 59 of "MM9 reduction" in [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease
`mm9reduce:greaterdemon` (greaterdemon-reduce-20261104). No-retexture branch of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)
on the installed `assets_source/worlds/mm9/models/mm9_greaterdemon.glb` (sha256 32d3d7a6a229, identical to
`../mm9_greaterdemon_claude/export/mm9_greaterdemon.glb`), copied to `before/` (the rollback source). The creature project was
only read. **Not installed. No Meshy credits.**

| | LOD0 | body `GreaterDemon` (skin, spikes, wing bones) | membrane `GreaterDemon_Wing` | heads `GreaterDemonHead` | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| installed | 9,988 | 5,136 | 1,648 | 3,204 | 4,945 | 1,665 | 460 |
| **h85** (`export/mm9_greaterdemon.glb` = `_h85.glb`, sha256 f5a36e78feff) | **8,418 (-15.7 %)** | 4,270 | 944 | 3,204 (byte-identical) | 4,158 | 1,378 | 369 |

Every LOD0 vertex is an installed vertex (position, normal, UV, joints, weights: the installed bytes; only index buffers
changed). The head primitive keeps its accessors. Clips, skin, nodes, materials and all 6 images are byte-identical
(`same_clips.py`: SAME). One skin, no tiers, no variants.

## Measured first: protected share
`scripts/analyse.py`: the head primitive (main head skin 1,461 with face, eyes, mouth, teeth; both snake arm heads 399 each
with jaws, tongues and teeth; 74 horn and head-spike pieces, 945) is 32 % of LOD0 and stays whole. On the body the 88 spikes,
claws and nails are already minimal pieces (6-57 faces) and stay; the skin (2,145 in two pieces) was already cut to 0.45 at
the build. What can go: the skin a little, the wing bones (1,520: smooth 8/6-sided tubes) and the membrane shell (2 x 352
faces per wing sheet + 240 rim faces). Protected share in h85: 62 % (kept 5,500 + the second membrane sheet 704, which is
re-emitted from the cut sheet).

## Route: pose-aware half-edge collapse (`scripts/mpqem.py`, the Highwayman/Troglodyte copy)
Scored over every clip at 10 Hz plus a position+UV rest quadric; only removes vertices; texture guard on the base colour of
each material (`tex_extract.py`). Greater Demon changes:
- **Membrane = solidified 8 mm shell** (`membrane_layers.py`): rim faces (an edge of ~8 mm) kept; per wing one sheet is cut
  and the other is re-emitted as the reversed faces of its twins (8 mm along the cut sheet's normal, residual max 1.44 mm),
  with the twin copy taken from the lining chart all three corners share; outer vertices whose twin lies on a lining chart
  border (24) are locked. Lining UV flips 0. Sheets cannot cross because both follow the same collapse.
- Sets (`gd_sets.py`): group 0 skin (ladder ratio), group 2 wing bones, group 3 membrane sheet; kept: small non-wing pieces,
  neck and wrist seams (3 cm round the head primitive), soles, the wing attachment (`anchor_keep.py`: wing-bone faces with body
  weights = buried root, and skin within 5 cm of the root and the membrane's body line), spike roots (`spike_keep.py`: skin
  within 2 cm of any spike vertex; f90 had parted two elbow spikes by 1.0-1.2 cm) and (`spike_keep2.py`) skin within 5 cm of
  the left elbow spike and the back spike that still parted in g85.

## Ladder (REA_HEIGHT_M 3.85: p99 <= 11.55 mm, max <= 57.75 mm; every clip, every 3rd frame, both ways; `review/ladder_sheet_<set>.png`)
| set | groups (wing bones, membrane) | skin step | LOD0 | p99 / max mm | IoU / SSIM | |
|---|---|---|---:|---|---|---|
| a | 0.6, 0.6 | r70 / r55 | 8,206 / 8,044 | 15.25/55.4, 26.7/94.0 | .992/.989, .982/.983 | fail (skin) |
| b | + root keep; 0.5, 0.5 | r85 / r80 | 8,350 / 8,252 | 12.96/64.2, 14.28/64.2 | .993/.991 | fail (Xwing knuckle 64 mm) |
| c | + knuckles kept (493 faces); 0.5, 0.45 | r85 / r80 | 8,576 / 8,478 | 11.43/60.5, 12.62/60.5 | .996/.992 | fail (membrane near the root) |
| e | b; 0.55, 0.55 | r90 / r85 | 8,548 / 8,450 | 10.86/33.0, 11.47/33.0 | .995/.992 | pass / pass |
| f | b; 0.55, 0.5 | r95 / r90 | 8,580 / 8,480 | 9.96/32.0, 11.03/33.0 | .995/.992 | pass / pass (f90 built: 2 spikes parted) |
| g | f + spike roots | r90 / r85 | 8,500 / 8,410 | 10.93/32.0, 11.42/32.0 | .995/.992 | pass / pass (g85 built: elbow spike parted) |
| **h** | g + two spike patches | **r85** / r80 | **8,418** / 8,330 | **11.42 / 32.0** / 12.42/55.4 | **.995 / .992** | **PASS, picked** / fail |

Error of the removed vertices in h85 (`err_regions.py`, every clip at 5 Hz): skin (134 removed) p50 8.1 / p99 25 / max 32 mm;
wing bones (303) p50 7.3 / p99 20 / max 29 mm; membrane (357) p50 2.2 / p99 14 / max 39 mm. Cut: skin 1,736 -> 1,474 free
faces, wing bones 1,344 -> 738, membrane sheets 704 -> 352 (+ the re-emitted twin sheet 704 -> 352).

## Gates, installed -> h85 (`scripts/gates.sh`: the creature's own gates.py, clip_heights.py and a GLB version of its wing
attachment measure, plus the shared checks; `review/gates_before/`, `review/gates_h85/`)
- Edge stretch (`gates.py`, every clip at 60 Hz): min and max no worse in any clip; p99 up by 0.01-0.05 in 8 clips (a
  percentile effect of fewer, larger faces); lowest point per clip identical (`clip_heights.py` identical in all 19 clips).
- Detached parts: 12 -> 12. The back spike on XspineB (2.1 cm, 2 poses) no longer parts; new: the elbow spike on Xaelbowpiv
  9.6 mm in 5 poses of Spawn only; the XspineA spike 1.15 cm as installed; the membrane shells (always "detached" from the body
  cluster, worst 1.22 / 0.95 m as installed) count 32 / 41 poses (installed 25 / 27).
- Wing attachment (`wing_gap.py` + `wing_gap_compare.py`; the creature's wing_review.py needs its master blend): the 110
  anchors that stay attached in the installed model: worst 4.24 cm both, anchors over 1 cm 39 = 39, largest change 0.95 cm.
- Bone lengths 0 stretching, winding 0 inverted, flat shading body 0.01 = 0.01, membrane 0.25 -> 0.23, heads 0.00;
  texture quality body atlas 55.0 % unchanged, stretch p90 1.08 -> 1.09, heads unchanged.
- LODs (`lod_check.py`, every frame of every clip; built by `build_lods.py` = tools/build_actor_lods.py defaults with floor,
  corpse-contact and rest-extreme points protected): rest bounds identical to LOD0 at every LOD (installed LOD2/LOD3 had lost
  up to 16 cm of wing tip width and 9.5 cm at the bottom); faces stretched > 20x: 0 at every LOD (installed LOD2 2); lowest
  point LOD1 -0.88 cm (installed -0.85), LOD2 -2.61 = -2.61, LOD3 -0.56 cm (installed -0.36).

## Review
- Viewer (installed and h85 side by side, 19 clips; `run_creature_review.py check`: 38 switches, 0 console errors):
  http://127.0.0.1:8912/level_generation/creatures/mm9_greaterdemon_reduce_claude/review/viewer/
- Sheets read (installed | h85 textured, clay, |diff| x4; Blender renders straight from the GLBs, `glb_close.py`):
  `review/close_h85_heads.png` (main head front/3-4/profile, both arm heads: the heads are the same; differences only on the
  body and spikes behind them), `review/close_h85_wings.png` (wing root, knuckles, tip, front, back 3/4, flap down and up,
  flap side), `review/close_h85_body.png` (front, 3/4, back, chest, left arm, legs, tail, Walking, AttackMelee, Death, Dead);
  and of f90 the same three `review/close_f90_*.png`. No visible change found at these distances.
- Look at: the wing bones (the tubes are cut to 55 % between the knuckles: smooth-shaded, a little less round up close), the
  membrane shading in the flap poses (half of the interior vertices are gone; billow kept within a few mm), the shoulders
  and thighs (larger skin triangles).

## Install (not run; on the user's OK)
`check_winding.py export/mm9_greaterdemon.glb` (0), `tools/install_model.py export/mm9_greaterdemon.glb --world mm9`, the
`mm9_actor_models_build_every_binding` regression and `floor_audit.py --world mm9` for MM9 Demon B, then add to
`../mm9_greaterdemon_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_greaterdemon_reduce_claude`; a rebuild
from this project must re-run that reduction". Rollback: `before/mm9_greaterdemon.glb`.

## Reproduce (project folder; Blender and Python under `scripts/cap.sh`)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
(cd ../../.. && REA_GLB=level_generation/creatures/mm9_greaterdemon_reduce_claude/before/mm9_greaterdemon.glb REA_NODE=GreaterDemon \
  level_generation/creatures/mm9_greaterdemon_reduce_claude/scripts/cap.sh /snap/bin/blender --background --factory-startup \
  --threads 4 -P level_generation/creatures/mm9_greaterdemon_reduce_claude/scripts/import_source.py)
$BL -P scripts/dump_mesh.py; $G scripts/tex_extract.py; $G scripts/analyse.py; $G scripts/gd_sets.py a
$G scripts/anchor_keep.py 0.05; $G scripts/spike_keep.py 0.02; $G scripts/spike_keep2.py 0.05; $G scripts/gd_sets.py h anchor spike spike2
SETS=h MP_GROUPS=2:0.55,3:0.5 scripts/run_mp.sh h 0.85,0.8      # mpqem -> reduce_ladder -> compare_ladder
scripts/build_mp.sh mp_h_r85 export/mm9_greaterdemon_h85.glb      # swap_mp -> build_lods -> shrink_shadow_lods -> fix_winding -> checks
scripts/gates.sh export/mm9_greaterdemon_h85.glb h85; python3 scripts/wing_gap_compare.py review/gates_before/wing_gap.json review/gates_h85/wing_gap.json
$BL -P scripts/glb_close.py -- inst=before/mm9_greaterdemon.glb,h85=export/mm9_greaterdemon_h85.glb; $G scripts/close_sheet.py inst h85 review/close_h85_body.png <spots>
python3 scripts/make_viewer_manifest.py <rev> "inst=Installed=before/mm9_greaterdemon.glb" "red=Reduced=export/mm9_greaterdemon_h85.glb"
```

## Not checked
In game; the binding regression and floor audit (after install); motion at speed by eye (stills and numbers only); the
wing-bone tubes in an extreme close-up (my wing close-up cameras framed the shoulder more than the tube); LOD1-3 and the shadow
meshes by eye (numbers only); the creature's own wing_review.py on a blend (replaced by the GLB measure above, whose anchor
set is derived from weights, not the build's 'anchor' attribute); Android.
