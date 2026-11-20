# MM7 Vampire (`m422`, Minion Vampire / Vampire / Elder Vampire) reduction (2026-10-21)

User request (batch F): "handle batch F ... check if they had their tris reduced". The Vampire had not been
(LOD0 10,329). Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: no part
needed rebuilding, so the textures, region mask, tier ramps, rig and clips stay as exported. No Meshy credits. Scripts
copied from `mm7_m262_reduce_claude/` (ladder, component/UV weights, export chain, LOD build, LOD check, viewer) and
`mm7_m426_reduce_claude/` (visibility, per-region error, drift/fleck checks, close-ups); the gates `gates.py`,
`cloth_gates.py`, `armpit_stretch.py`, `accessory_gap.py`, `sole_probe.py`, `visible_backfaces.py`, `worst_edges.py`
(with `cfg.py`, `armik.py`) are copies from `mm7_m422_claude/scripts/`. Batch rules: nothing installed, nothing in
`assets_dev/` or `assets_source/`, `mm7_m422_claude/` untouched. Every Blender/Python step runs memory-capped
(`scripts/cap.sh`).

Source: `../mm7_m422_claude/export/mm7_m422.glb`, the body retexture v2 export of 2026-10-20 17:37 (README "Body
retexture v2"; sha256 `a9b85be7…`, the hash the source README lists), copied to `work/mm7_m422_source_pre_reduce.glb`
(rollback source). One node `M422`, one merged material `M422_A` (body + head atlas 2080x1024), tier variants
`M422_B` / `M422_C` (three regions: coat, cape + collar, hair), 126 joints, clips Standing, Walking, Attack, Hit, Death,
Dead, Fidget. No attachments (unarmed).

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| batch F export | 10,329 | 5,163 | 1,844 | 606 |
| **reduced** | **8,093** | 4,045 | 1,442 | 688 |

LOD0 -21.6 % (LOD1 -22 %, LOD2 -22 %). The aim of 25-35 % was **not** reached without visible damage; see "Why not
25 %" below. `export/mm7_m422.glb` sha256 `69b734b976e75b3b712ecbb40811a593a547d0757474320ccc6ee6f15477f0f0`, 7.0 MB.

## Regions (`make_groups.py`)

Each source face takes the production master's `piece`/`garment` (`master_labels.py`: `../mm7_m422_claude/work/
rig_v6.blend` read only, matched by centroid, < 0.002 mm), its classes from the source's runtime maps at its UVs and
its rest-pose visibility (`vis_faces.py`, 8,409 of 10,329 visible). Weld: 7,031 -> 571 open edges, 6 coincident
vertices with other weights kept apart.

| label | region | free faces | ratio |
|---|---|---:|---|
| 1 | face and head skin, visible | 1,494 | 70 % |
| 2 | head skin hidden (under the hair, inside the collar) | 545 | 45 % |
| 3 | hair (head set) | 900 | 50 % |
| 4 | hands (rigid open claws) | 1,046 | 60 % |
| 5 | coat skirt (robe chains) | 692 | 80 % |
| 6 | cape (sheet chains) | 686 | 80 % |
| 7 | stand-up collar | 298 | 80 % |
| 8 | trousers and boots, visible | 397 | 80 % |
| 9 | trousers hidden in the skirt | 264 | 70 % |
| 10 | coat top and sleeves | 811 | 75 % |

Kept exactly (`work/keep_g.npy`, 3,501 faces):
- every piece of up to 250 faces (1,480): eyes, belt buckle, jabot, neck ornament and all 13 clasps (they copy the
  coat skin and must keep their seats);
- gold texels on the coat, skirt, cape and collar (886): placket, cuffs, hem bands, collar and cape edges, belt;
- the mouth with the painted fang tips (2.5 cm around the lips, 314);
- the soles (below 6 cm, 238), the skirt hem band (below 36 cm) and cape hem band (below 47 cm);
- the front belt band with both belt-end flaps (z 0.90-1.08 m, front, 263; unchanged, still an open item of the
  source);
- the armpit band (coat top, |x| 0.14-0.30 m, z 1.22-1.42 m, 238: the inner part of the source's own
  `reduce_protect_box`; the armpit stretch gate is borderline);
- one drift-lock round (`drift_lock.py`, 3 cm): 305 more faces around visible texture drift (inner skirt back at
  the vent), dark slivers (temples) and light flecks (left cuff).

## Ladder (REA_HEIGHT_M 1.70: p99 <= 5.1 mm, max <= 25.5 mm)

| step | config | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| a | face 70, hidden head 35, hands 55, legs 60/40, cloth 75-80 | 8,047 | 8.85 / 76.3 | 0.997 | 0.996 | fail: hidden trousers 76 mm in Death |
| b | face 50, hands 45, legs 80/70, cloth 85 | 7,741 | 4.13 / 21.8 | 0.997 | 0.996 | pass, but a crease from the lip corner, jagged eye rims, blocky claw tips |
| c2 | face 55 + eye sockets and 3 cm mouth kept, hands 60 | 8,139 | 4.16 / 21.8 | 0.997 | 0.996 | pass, cheek crease remains |
| d | face 70 | 8,301 | 4.15 / 21.8 | 0.997 | 0.996 | pass, face matches the source |
| e | d without socket lock, hair 50, cloth 80, coat 75 | 7,977 | 4.64 / 21.8 | 0.997 | 0.996 | pass; 14 visible drift faces, 19 visible dark slivers |
| f | e with skirt/cape/coat 70, collar 65 | 7,757 | 5.72 / 33.5 | 0.996 | 0.996 | fail: cape 34 mm, skirt in Death |
| **g** | **e + one drift lock** | **8,093** | **4.45 / 21.8** | **0.997** | **0.996** | **picked** (Cand_77 of `work/ladder_g.blend`) |

Per region for g (`group_error.py`, every 4th frame of every clip): face p99 1.1 mm, hidden head 6.0, hair 5.2, hands
3.8, skirt 7.0 (max 18 in Death), cape 6.4 (max 22 in Death), collar 8.9 (the collar's inner face at the neck in Death,
hidden), trousers 4.8 / 9.8, coat top 6.2. After the lock: no flagged visible face over 3 cm2 (drift 5 faces 3.7 cm2,
dark 16 faces 21 cm2 at the eyelids and hairline, light 6 faces 2.9 cm2, all sub-3 cm2); the source has none.

Close-ups (source vs pick; textured and clay, `close_human.py` on the ladder blends; `pair_sheet.py`):
`review/close/sheet_e77_{1..4}_{tex,clay}.png` (face, mouth, hair, collar, both claws front/back, the raised claw,
cuffs, shoulders, placket and clasps, belt, armpit front/back/side at the raised-arm frame, Attack, Hit, cape side and
back, hems, feet, Walking, Death, Dead, Fidget), `sheet_g77_collar_*.png` (collar, cuffs after the lock),
`sheet_b75_*` / `sheet_c77_face_*` / `sheet_d78_face_*` (the rejected face cuts). Straight from the GLBs
(`glb_close.py`): `review/glbclose/sheet_r77_{tex,clay}.png`, tiers A and C side by side
`review/glbclose/sheet_tiers_tex.png`. No feature changed: face, painted fang tips, eyes, clasps, buckle, belt flaps,
trims and hems are identical; claws match.

## Why not 25 %

- 3,500 faces (34 %) are kept exactly: clasps, buckle, eyes, ornaments, gold trims, mouth, soles, hems, belt flaps,
  armpit band and the drift lock.
- The cloth was already reduced by the source build (`creature.json` `reduce`; median edges 29 mm coat top, 47 mm
  cape, 49 mm skirt): at 70 % (ladder f) the cape missed by 34 mm and the step failed. At 80 % it passes.
- The face is dense (7 mm edges) but any cut below 70 % creased the cheek and lip corner (ladders b, c2).
- What remains possible: the eyes as a group at about 60 % (-150; they are mostly hidden spheres but the brief says
  keep small pieces), gold trims as their own group (playbook: painted trims fail when decimated alone). Not done.

## Build

`TOKEN=<lease> REA_FLOOR_M=0.01 scripts/build_export.sh ladder_g.blend Cand_77`: `export_cand.py` (4 influences as the
source LOD0) -> `swap_lod0.py` (into the rollback source: materials, variants, region ramps, clips unchanged) ->
`build_lods.py` (the source chain's `tools/build_actor_lods.py` ratios 0.5 / 0.18 / 0.06, 8 influences; bounding
extremes and every vertex within 1 cm of the floor in Death/Dead protected, 609 points: with 4 mm the LOD3 corpse sank
9.4 cm in Dead; with 3 cm LOD3 stayed at 1,264) -> `shrink_shadow_lods.py` (MESH=M422, the source chain's) ->
`carry_variants.py`.

Same node names, materials (byte-equal JSON), `KHR_materials_variants` on all eight primitives, mesh extras
(`openyamm_lods`, `openyamm_shadow_lods`), skin joints and inverse binds, images, and every animation sampler
byte-identical to the source. So the staged binding `../mm7_m422_claude/actors_m422_binding.yml` applies unchanged.

## Gates (gate copies of both GLBs: `run_gates.sh` = `gate_import.py` + `gate_attrs.py` with the master's garment/piece labels, then the source project's gates)

| gate | source | reduced |
|---|---|---|
| G4 arm stretch p99 (worst: Death L / Attack R) | 2.37 / 2.38 | 2.26 / 2.32 |
| G5 hand stretch max | <= 1.05 | <= 1.03 |
| G6 hands inside the body | 0 every clip | 0 every clip |
| armpit stretch R p99 / max at the raised-arm frame (Attack 21.5) | 2.56 / 3.54 | 2.50 / 3.49 |
| armpit stretch Fidget R / Death L p99 | 2.43 / 2.43 | 2.20 / 2.41 |
| coat (skirt) poke: Walking / Attack / Death | 15 v, 10 cm / 2 v, 0.56 cm / 4 v, 1.36 cm | 13 v, 10 cm / 2 v, 0.20 cm / 4 v, 1.43 cm |
| cape poke: Attack / Hit / Death | 7 / 4 / 1 | 7 / 3 / 1 |
| skirt / cape stretch p99, Walking | 1.29 / 1.23 | 1.31 / 1.22 |
| skirt / cape stretch p99, Death | 2.22 / 2.22 | 2.34 / 2.07 |
| clasp/buckle seat drift (worst, Death) | 10.2 mm | 10.2 mm (identical every clip) |
| soles (Standing / Walking / Attack lowest foot) | -0.2 / -0.3 / -0.8 cm | the same |
| visible back faces, Walking front / quarter | 18-39 / 23-34 cm2 | identical (belt flaps) |
| LOD check: lowest point Dead LOD0-3 | -2.5 / -2.5 / -2.1 / -2.1 cm | -2.5 / -2.5 / -2.5 / -2.5 cm |
| LOD check: Death lowest LOD0 (fall, both) | -9.9 cm | -9.9 cm every LOD |
| LOD check: stretched faces over 20x per clip | <= 2 | <= 1 |
| LOD check: rest bounds | 0.98 x 0.61 x 1.70 m | the same at every LOD |
| `check_winding.py` | 0 | 0 inverted closed parts |

The armpit/arm maxima rise on single edges of the hidden inner coat layer (rest x 0.07-0.14, y ~0, inside the torso;
`worst_edges.py`): Death L max 3.85 -> 4.77, Hit L arm max 2.43 -> 3.34. Their openings (9.3 cm) equal the source's.

## Viewer

`http://127.0.0.1:8912/level_generation/creatures/mm7_m422_reduce_claude/review/viewer/`: batch F export (r100) and
reduced (r77, default tier B) for tiers A, B and C (`viewer_tiers.py` bakes the region ramps; `viewer_manifest.py`).
`python3 tools/run_creature_review.py --project level_generation/creatures/mm7_m422_reduce_claude check`: 42 clip
switches, no console errors.

## For the user to review

- 21.6 % off LOD0 (10,329 -> 8,093), short of the 25-35 % aim (above).
- LOD3 is 688 triangles (was 606): the floor protection for the corpse costs ~80.
- Shading: the reduced mesh uses plain smooth normals; the source GLB has faceted patches (sleeves, armpit, hair), so
  the clay reads smoother; textured views match. The back of the hair reads a little rounder in clay (hair at 50 %).
- Unchanged from the source: the belt-end flaps, the walking calf at the back hem, the Death cape crumple.

## Install (not run)

Replaces the batch F export of `mm7_m422_claude/` (same nodes, materials, variants and clips; no attachments):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m422_reduce_claude/export/mm7_m422.glb --world mm7
```

Binding: add `level_generation/creatures/mm7_m422_claude/actors_m422_binding.yml` (Vampire A/B/C, scale 119.3,
impact 0.975 s) to `assets_dev/worlds/mm7/models/actors.yml`, as the source README says; it applies unchanged.
Rollback: `work/mm7_m422_source_pre_reduce.glb` (= the source export, sha256 `a9b85be7…`).

Reproduce: `import_source.py` (REA_NODE=M422, REA_GLB=the rollback source), `dump_mesh.py`, `dump_faces.py`,
`dump_weights.py`, `master_labels.py`, `vis_faces.py`, `MOUTH_R=0.025 EYE_R=0 make_groups.py` (-> `keep_e.npy`),
ladder e (`REA_WEIGHTS=component REA_KEEP_FACES=work/keep_e.npy REA_GROUPS=work/groups.npy
REA_GROUP_RATIOS=1:0.7,2:0.45,3:0.5,4:0.6,5:0.8,6:0.8,7:0.7,8:0.8,9:0.7,10:0.75 REA_HEIGHT_M=1.70 run_ladder.sh e 0.77`;
every region has its own ratio, so the ladder ratio only names the candidate; `decimate_tex.py` skips the empty free
part), `texture_drift.py`, `dark_slivers.py` (dark and `REA_LIGHT=1`, `REA_DARK_L=80 REA_DARK_N=4`), `visible_only.py`
each, combined into `drift_r77.npy`, `drift_lock.py work/keep_e.npy work/keep_g.npy r77`, ladder g (same ratios with
`keep_g.npy`, label g), `group_error.py`, `close_human.py`, `pair_sheet.py`, `build_export.sh` as above,
`lod_check.py`, `check_winding.py`, `run_gates.sh <glb> <tag>`, `glb_close.py`, `viewer_tiers.py` (r100, r77),
`viewer_manifest.py`. The MeshLab venv is `VENV` in `run_ladder.sh` (pymeshlab, numpy, scipy).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: corpse at -3.0; dying sinks to -7.1.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m422.glb export/mm7_m422.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m422.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package h08 of [the gait rollout](../gait_rollout_20261031/README.md) appended `Jog` (humanoid set Armed-Run-Forward,
0.80 s, stride 2.6121) and `Sprint` (Unarmed-Sprint, 0.60 s, 3.2033), robe-safe (low swing) with the coat skirt and
cape simulated on the new motion (a numpy port of `../mm7_m422_claude/scripts/robe_sim.py`), to the installed
`mm7_m422.glb` (existing clips byte-identical) and installed it. Bindings for the coordinator: `run: Jog`,
`run_stride_length: 2.6121`, `sprint: Sprint`, `sprint_stride_length: 3.2033`
(`../gait_rollout_20261031/h08/bindings.yml`). Rebuild: `../gait_rollout_20261031/h08/scripts/rebuild.sh m422`;
details and gates in [the package README](../gait_rollout_20261031/h08/README.md). A far-LOD repair rerun or any
re-export of this model must re-graft these clips (rerun that rebuild on the new source).
