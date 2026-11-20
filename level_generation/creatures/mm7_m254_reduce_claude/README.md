# MM7 Golem (`m254`, Bronze / Brass / Gold Golem) reduction (2026-10-20)

User: "do the tri reduction on all 5" (the five MM7 batch-I creatures; this project is m254 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch: a texture-aware MeshLab ladder that keeps
the UVs, so the textures, the two-channel region mask, the three tier variants (`KHR_materials_variants`
`m254_a/b/c`) and the ramps stay valid. **No Meshy credits** (70 were available). **Not installed** (batch rule).

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m254_reduce_claude/review/viewer/index.html)
(source vs reduced, tiers A/B/C, all eight clips, native reference frames)

**Result: LOD0 10,051 -> 8,043 triangles (-20 %).** Face, crown, nemes, collar, horns, eyes, studs and soles are
unchanged; the over-dense hands (2,783 faces, never reduced by the source build) carry most of the cut.

## Source

`../mm7_m254_claude/export/mm7_m254.glb` (sha256 `517bfffe...8408`), copied to `work/mm7_m254_source_pre_reduce.glb`
(rollback source). One mesh node `Golem` (skinned humanoid, 56 joints), one merged body + head atlas material
`Golem_A` (2080x1024; head set u > 0.51) with variants `Golem_B/C`, shadow LODs, 8 clips. Rest top 1.700 m (crown
rim, 258.9 units at the binding scale 152.29). Weld: 6,083 -> 545 open edges, no coincident vertices with other
weights, 10,051 triangles in and out (no two-sided sheets). Ladder limits for 1.70 m: p99 5.1 mm, max 25.5 mm,
IoU >= 0.98, SSIM >= 0.93. Scripts copied from `../mm7_m414_reduce_claude/scripts/` (Titan, the same humanoid
pipeline), `dark_slivers.py` from `../mm7_m278_reduce_claude/`, the gate scripts and `shrink_shadow_lods.py` /
`clamp_lod_uv.py` from the source project.

## Where the triangles are (`scripts/m254_pieces.py`, `review/labels/pieces.png`)

| piece | faces | |
|---|---:|---|
| body skin (closed cast-metal shell) | 4,953 | 2,783 of them hands and fingers, 407 soles |
| face / neck skin (head texture set) | 1,646 | 1,123 visible, 523 under the nemes, crown and beard (`scripts/visibility.py`) |
| collar studs (24 pieces) | 480 | |
| loincloth (striped shendyt) | 449 | |
| crown (striped modius, the model's top) | 415 | |
| cuffs (wrists, ankles) | 400 | |
| collar | 399 | |
| nemes (striped) | 322 | |
| belt | 252 | |
| horns / horn sockets | 222 / 174 | |
| beard (striped) | 172 | |
| eyes / ear studs | 103 / 64 | |

The body was already reduced once in the source build (15.6k -> 10.05k with head and hands protected), so the torso,
arms and legs are lean: at 70 % the free body reached 6.1 mm rest p99 (ladder a).

## Region budgets (pick `l`, `scripts/m254_sets.py`)

| region | source faces | ratio | out |
|---|---:|---|---:|
| **kept exactly** (3,825): visible face 1,123 + 1-ring, soles 407, collar 399 (at 80 % its back creased and the studs sank in Attack, `review/glbclose/sheet_nemes_attack.png`), crown 415 and nemes 322 (stripe drift / 21-23 mm Attack error at 80-85 %), horns 222, eyes 103, ear studs 64, collar studs 480, patches below | 3,825 | 100 % | 3,825 |
| 1 head skin one ring around the visible face | 297 | 80 % asked; a one-ring strip has only fixed border vertices, so nothing collapses | 297 |
| 2 hidden head skin (scalp under nemes and crown) | 152 | 60 % (40 %: 10-16 mm rest error) | 90 |
| 3 loincloth | 412 | 85 % | 350 |
| 7 belt | 209 | 80 % | 167 |
| 8 beard | 172 | 85 % | 146 |
| 9 horn sockets | 174 | 75 % | 130 |
| 10 cuffs | 371 | 85 % | 315 |
| 11 hands and fingers (body-skin faces touching hand + finger weight > 0.3), fingertips excluded | 1,922 | 45 % | 864 |
| 12 fingertips (distal phalanges, weight > 0.3) | 857 | 70 % (at 40-55 % with the rest the tips went pointed) | 599 |
| 0 free body (torso, arms, legs) | 1,660 | ladder budget: 76 % at the pick | 1,260 |
| **total** | **10,051** | | **8,043** |

Patches (`patch_keep.py`, with X mirrors; `drift_lock.py`): left upper-arm back (0.302, 0.021, 1.21) and the cheek
face it pushed into (0.064, -0.026, 1.56), 3-4 cm (the arm-into-torso probe went 2.9 -> 5.2 cm in Attack without
them); armpits (+-0.226, 0.01, 1.12), 4.5 cm (the G4 maximum rose 4.02 -> 4.39 there); one drift-lock round on the
combined base colour, region mask and dark-sliver hits of `i r77` (2.5 cm); the left hip under the belt edge
(0.132, 0.025, 0.959), 3 cm (a region-mask fleck, drift 107).

## Ladder (`work/selection_<config>.json`, `review/ladder_sheet_<config>.png`)

| config | step | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 10,051 | | | | |
| a: hands kept, hidden head 40 %, free 70-60 % | r87 | 8,863 | 5.42 / 24.49 | 0.992 | 0.990 | fail (p99) |
| b: hands kept, hidden head 60 %, gentle garments, free 85-75 % | r89 | 9,075 | 4.54 / 23.26 | 0.993 | 0.992 | pass |
| c: b + hands 70 % | r82 | 8,327 | 4.18 / 23.26 | 0.993 | 0.993 | pass |
| d: hands 55 % / 40 % | r77 / r73 | 7,821 / 7,493 | 4.66 / 23.26, 4.37 / 23.26 | 0.993 | 0.992 | pass; fingertips pointed (`sheet_fingers_cmp.png`) |
| e: hands 45 %, fingertips 70 % | r77 | 7,845 | 4.39 / 23.26 | 0.994 | 0.992 | pass; arm into neck 5.2 cm (gate) |
| f/g: e + arm, cheek and armpit patches | r77 | 7,863 | 4.41 / 23.26 | 0.993 | 0.992 | pass; collar back creased in Attack |
| h/i: g + collar, then nemes kept | r77 | 7,885 | 4.60 / 18.52 | 0.995 | 0.993 | pass; mask drift 7 faces (crown, loincloth, forehead) |
| i2: free 68-60 % | r76 | 7,783 | 5.07 / 27.77 | 0.993 | 0.992 | fail |
| j/k: + drift lock, crown kept | r78 | 7,965 | 4.71 / 20.83 | 0.994 | 0.992 | pass; hip mask fleck |
| **l: k + hip patch** | **r79** | **8,043** | **4.51 / 18.52** | **0.995** | **0.993** | **pick** (r78 7,977 passes too but drifts on the chest under the collar edge) |

Texture checks on the pick (`texture_drift.py` on the 2K base colour and on the region mask, `dark_slivers.py`
`REA_DARK_L=80 REA_DARK_N=4`): base colour 0 faces over 40; region mask 2 faces over 40 (26 cm2, the loincloth's side
edges at 85 %; not visible in the tier B/C close-ups, `review/glbclose/sheet_l79_tiers.png`); 0 dark slivers.

## Humanoid gates (`scripts/gates.sh`, `review/gates_src.txt` vs `review/gates_l79.txt`)

The source project's gate scripts (`gate_*.py`, copies) run on a gate scene built from each runtime GLB by
`gate_blend.py` (same import, weld and closed-skin label for both), so source and reduced are measured the same way.
The source GLB reproduces `../mm7_m254_claude/review/gates_final.txt` (rig_v5.blend) within the 4-influence export
(G5 Attack L 4.07x vs 4.35x).

| gate (every clip) | source | reduced |
|---|---|---|
| G4 arm stretch max (R / L) | Attack 4.02 / 3.61, Death 3.88 / 3.80, Fidget 3.54 / 3.25, Hit 2.63 / 2.77, Running 2.85 / 2.44, Standing 1.64 / 1.68, Walking 1.45 / 1.50 | Attack 4.02 / 3.61, Death 3.88 / 3.80, Fidget 3.54 / 3.25, Hit 2.65 / 2.77, Running 2.85 / 2.44, Standing 1.64 / 1.68, Walking 1.46 / 1.38 |
| G4 arm stretch p99, arm edges only (R / L) | Attack 3.41 / 3.30, Death 3.17 / 2.94, Fidget 3.03 / 2.97, Hit 2.22 / 2.03, Running 2.37 / 2.36, Standing 1.33 / 1.33, Walking 1.29 / 1.33 | Attack 3.56 / 3.33, Death 3.38 / 2.98, Fidget 3.18 / 3.02, Hit 2.48 / 2.04, Running 2.44 / 2.37, Standing 1.36 / 1.35, Walking 1.31 / 1.34 |
| G4 edges over 2.5x (worst frame, R / L) | Attack 11 / 9, Death 9 / 9, Fidget 10 / 7 | Attack 13 / 9, Death 10 / 9, Fidget 11 / 7 |
| G5 hand stretch max (R / L) | Standing 1.82 / 1.99, Walking 1.65 / 1.50, Running 2.20 / 2.38, Attack 2.93 / 4.07, Hit 2.32 / 2.11, Death 2.20 / 2.19, Fidget 2.65 / 2.44 | Standing 1.79 / 1.65, Walking 1.39 / 1.27, Running 2.16 / 1.93, Attack 2.80 / 2.42, Hit 2.21 / 1.80, Death 1.86 / 1.74, Fidget 2.59 / 2.17 |
| G6 contacts | Standing L hand 1.6 cm; Attack fists 1.8 / 1.7 cm, L forearm 0.6 cm; other clips 0 | Standing 1.5 cm; Attack 1.6 / 1.6 cm, 0.6 cm; other clips 0 |
| arms into the torso | Attack L upper arm 2.9 cm (frames 15-17), else 0 | identical |
| soles, flat feet | | identical lines (feet and soles kept exactly) |

The plain G4 p99 of the source gate rises (Attack R 2.65 -> 3.30) only because the reduced hands have fewer edges in
the arm selection: the same shoulder-band edges (under the collar, the source's known overhead clavicle stretch) make
up a larger share. The arm-only p99 (+0.02 to +0.26), the maxima (equal) and the count of edges over 2.5x (+0 to +2)
are the like-for-like numbers.

## Build (`scripts/build_reduced.sh`, reproduces `export/mm7_m254.glb` byte for byte)

`cand_glb.sh l Cand_79 kn` (`kept_normals.py`: the source GLB's normals on unchanged faces and kept vertices ->
`export_cand.py` -> `swap_lod0.py` onto the source) -> `spike_points.py` (28 points: crown rim per 15-degree sector,
horn tips and outermost horn points) and `floor_points.py` (24 Dead/Death floor contacts) -> `build_lods.py`
(`tools/build_actor_lods.py`, 8 influence slots as the source, ratios 0.5 / 0.2 / 0.075, 52 protected points) ->
`shrink_shadow_lods.py` (the source project's inset) -> `carry_variants.py` (7 primitives) -> `clamp_lod_uv.py`
(nothing to clamp) -> `check_winding.py` (0 inverted closed parts) -> `compare_glb.py`: nodes, skin, inverse binds,
materials and extras (region mask, ramps, specular), images, textures, samplers, all 8 clips, mesh extras and the
variants extension identical to the source ("DIFFERENCES none"); variants on all 8 colour/shadow primitives.

| | LOD0 | LOD1 | LOD2 | LOD3 | file |
|---|---:|---:|---:|---:|---:|
| source | 10,051 | 5,024 | 1,808 | 598 | 8.50 MB |
| reduced | **8,043** | 4,021 | 1,605 | 600 | 8.17 MB |

Shadow LODs match the colour LOD counts. The file shrinks little: the atlases are most of it.

Checks:
- `height_check.py` (`work/height_check.log`): crown top 1.7000 m and horn tips 1.6872 m at LOD0-1; LOD2/3 crown
  1.7021 m (+0.3 units). The source LOD3 crown dropped to 1.6866 m (-2 units).
- `lod_check.py` (`work/lod_check_{src,final}.json`, every frame of every clip, every LOD): no face stretches over
  20x anywhere; rest bounds equal the source; lowest points equal the source LOD0 in every clip (Death -32.2 mm as
  the source) except Dead +1.0 mm (source -0.1 mm); the source LOD3 floated 4.8-5.6 mm in Standing, Attack, Fidget
  and Dead, the reduced LOD3 1.2-2.4 mm.
- `review/lods/sheet.png` (`lod_views.py`): source vs reduced LOD0-3 standing, Attack raise and head; the reduced LOD3
  keeps the crown rim the source LOD3 flattened.

## Close-ups (straight from the GLBs, `scripts/glb_close.py`, `glb_sheet.py`; textured and clay)

- `review/glbclose/sheet_l79_head.png`: face front, three-quarter, side, back, crown from above, beard, collar, nemes
  and collar in Attack (front and side) — identical to the source.
- `review/glbclose/sheet_l79_hands.png`: both hands, finger close-ups, fists overhead, clasped fists at the blow,
  Fidget fist.
- `review/glbclose/sheet_l79_body.png`: torso, back, loincloth front/back/side, cuffs, feet, knees, Attack, Death,
  Dead from below.
- `review/glbclose/sheet_l79_tiers.png`: tiers B and C (viewer GLBs) at the head, loincloth (four sides), beard, crown.
- Rejected rounds: `sheet_fingers_cmp.png` (hands at 70 / 55 / 40 %), `sheet_fingers_e.png` (fingertip group),
  `sheet_nemes_attack.png` (collar at 80 %: creased back, sunken studs).
- Viewer shots: `review/shots/sheet_tiers.png` (tier B source / reduced, tier C reduced: Standing, Walking, Attack).

## Viewer

`review/viewer/` (source r100 vs reduced r79 for tiers A/B/C; `viewer_variants.py` bakes the ramps with the engine
rule; `viewer_manifest.py` plus the source viewer's native anchor frames). `python3 tools/run_creature_review.py
--project level_generation/creatures/mm7_m254_reduce_claude check`: 48 switches (6 models x 8 clips), no console
errors, failed [].
http://127.0.0.1:8912/level_generation/creatures/mm7_m254_reduce_claude/review/viewer/index.html

## For the user to review

- **Hands at 45 % with fingertips at 70 %** (2,783 -> 1,463 faces): the shapes, fists and the clasp are kept, but in
  clay close-ups the curled left thumb tip and the back of the clenched fist are slightly more faceted
  (`sheet_l79_hands.png`, `hand_l` and `fist_zoom`). Textured at game distance they read the same. A gentler cut
  (config c, hands 70 %, 8,327 triangles) is the fallback.
- The arm stretch under the collar in the overhead smash is the source's (same maxima); two more edges pass 2.5x.
- The saving is 20 %: about half the mesh is kept exactly (visible face, crown, nemes, collar, ornaments, studs), and
  the lean body fails the max error below about 76 %.

## Install later (not run)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m254_reduce_claude/export/mm7_m254.glb --world mm7
```

The `actors.yml` binding in `../mm7_m254_claude/README.md` (and `actors_m254_binding.yml`) is unchanged: same file
name, node, materials, skins `m254_a/b/c`, clips, scale 152.29 and look nodes. Add a
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md) row when installed. Rollback: install
`work/mm7_m254_source_pre_reduce.glb` the same way. If the source project re-exports its clips later, carry them over
with `scripts/transplant_clips.py` (as in the m406 / m230 reductions).

## Reproduce

Blender scripts run through `scripts/bl.sh` (lease wrapper, `TOKEN`); the MeshLab venv path is in `run_ladder.sh`.
1. `REA_GLB=<abs work/mm7_m254_source_pre_reduce.glb> REA_NODE=Golem bl.sh import_source.py`, `bl.sh dump_mesh.py`,
   `bl.sh dump_groups.py`, `extract_basecolor.py work/mm7_m254_source_pre_reduce.glb`, `m254_pieces.py`,
   `REA_MIN_PIX=6 visibility.py 1.25 1.75` (copy to `work/visible_head.npy`);
2. patches: `REA_PATCH_R=0.04 patch_keep.py - work/patch_f.npy 0.302,0.021,1.21`, `REA_PATCH_R=0.03 patch_keep.py
   work/patch_f.npy work/patch_f.npy 0.064,-0.026,1.56`, `REA_PATCH_R=0.045 patch_keep.py work/patch_f.npy
   work/patch_g.npy -0.226,0.01,1.12`; drift lock `REA_LOCK_R=0.025 drift_lock.py work/patch_g.npy work/patch_j.npy
   i_r77` (on the max of the base, mask and sliver maps of config i); `REA_PATCH_R=0.03 patch_keep.py
   work/patch_j.npy work/patch_l.npy 0.132,0.025,0.959`;
3. `M254_KEEP=4,5,6 M254_HAND_GROUP=1 M254_TIP_GROUP=1 M254_EXTRA_KEEP=work/patch_l.npy m254_sets.py l`;
4. `run_ladder.sh l l "1:0.8,2:0.6,3:0.85,7:0.8,8:0.85,9:0.75,10:0.85,11:0.45,12:0.7" 0.76,0.72`;
5. `texture_drift.py l_r79`, `dark_slivers.py l_r79` and `texture_drift.py` with `work/regionmask.png` as
   `work/basecolor.png` (mask drift);
6. `build_reduced.sh`; checks `gates.sh <glb> <label>`, `height_check.py`, `REA_NODE=Golem lod_check.py`,
   `lod_views.py`, `glb_close.py`, `viewer_variants.py`, `viewer_manifest.py "MM7 Golem" r79 10051 8043`.
   `armtorso_where.py` and `stretch_where.py` locate gate hits (rest positions for patches).

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -5.6.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m254.glb export/mm7_m254.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m254.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [h10](../gait_rollout_20261031/h10/README.md) appended `Walk2` (heavy slow Armed-Walk, 1.10 s, stride 1.1923) and `Sprint` (0.68 s, stride 3.1567) to the installed `assets_source/worlds/mm7/models/mm7_m254.glb`
(existing clips, meshes, skins and materials byte-identical; pre-gait copy `../gait_rollout_20261031/h10/work/mm7_m254_pre_gait.glb`)
and installed it; the bindings (`walking: Walk2`, `sprint: Sprint`; `Walking` stays the walk-as-run) are applied by the rollout coordinator from `h10/bindings.yml`. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h10/scripts/rebuild.sh m254`. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds this source must keep or re-graft these clips (copy the new source over the pre-gait copy
and rebuild).
