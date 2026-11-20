# MM7 Chain Fighter (`m222`, Conscript / Soldier / Fighter) reduction (2026-10-20)

User: "reduce tris on all 5" (the MM7 batch-A humanoids; this project is m222 only). Default route of
[RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture branch (texture-aware MeshLab ladder that keeps
UVs): the textures, region mask, three tier ramps, clips and the scimitar socket stay as exported. No Meshy credits.
**Nothing installed**, nothing written to `assets_dev/` or `assets_source/`, `../mm7_m222_claude/` untouched.

Source: `../mm7_m222_claude/export/mm7_m222.glb` (accepted 2026-10-20, not installed), copied to
`work/mm7_m222_source_pre_reduce.glb` (rollback source); the scimitar `mm7_m222_sword.glb` to
`work/mm7_m222_sword_source_pre_reduce.glb`. One merged body + head atlas material (`M222_A`, 2080x1024) with the
tier variants `M222_B` / `M222_C` (`KHR_materials_variants`, regions green cloth + hair), one `M222` node, 57 joints
(incl. the `Sword` socket), 4 influences at LOD0 and 8 slots at LOD1-3, inset shadow LODs. 1.706 m.

Scripts are copied from `../mm8_m432_reduce_claude/scripts/` (fixed parenting order in `reduce_ladder.py`, groups,
keep sets, `glb_close.py`, `grip_check.py`), `build_lods.py` from `../mm7_m162_reduce_claude/` (Death/Dead floor and
extreme locks) and `shrink_shadow_lods.py` from the source project. Blender runs go through `scripts/blend.sh`
(`tools/run_creature_blender.sh` with the lease token). New here: `m222_regions.py`, `m222_sets.py`,
`trim_faces.py`, `class_drift.py`, `region_error.py`, `label_view.py`, `compare_structure.py`, `reproduce.sh`.

## Where the triangles are

Weld 5,480 -> 464 open edges, no coincident vertices with other weights, no two-sided sheets (9,666 in and out).
The source build had already reduced the body once after weighting, so the cloth is thin.

| region | faces | treatment in the pick |
|---|---:|---|
| main piece, body texture set (torso, hair slab, legs, boots) | 2,543 | torso above 0.98 m 80 %, boots below 0.52 m 75 %, thighs/pelvis take the rest (50 %); soles (225, below 6 cm) kept |
| main piece, head texture set (face, ears, neck, hair top) | 2,089 | face front (1,242, incl. 823 painted-feature faces) kept; rest 48 % |
| arm shells (gauntlets, hands, fingers) | 2,767 | every face touching hand + finger weight > 0.3 kept (2,394); rest of the gauntlets 60 % |
| helmet (morion with crest) | 518 | 50 % |
| shoulder guard | 240 | 60 % |
| gold thigh panels | 420 | 75 % |
| neck trims | 178 | 80 % |
| small pieces <= 80 faces (28 belt links, eyes, gem) | 911 | kept |
| painted chest strap and green bands on the torso (`trim_faces.py`) | 491 | kept |

`review/labels/` shows the regions (`regions_*`), the first keep set (`sets_a_*`) and the painted trims (`trims_*`).

## Ladder

Limits for the 1.706 m height: p99 5.12 mm, max 25.59 mm (every 3rd frame of every clip), IoU >= 0.98, SSIM >= 0.93.

| config | change | triangles | p99 / max mm | IoU | SSIM | |
|---|---|---:|---|---|---|---|
| source | | 9,666 | | | | |
| a | hands, small, soles, face kept; sleeves 60, helmet 65, shoulder 60, panels 70, trims 80, head 70 %; body takes the rest | 7,904 | 5.09 / 24.75 | 0.987 | 0.989 | pass, barely |
| b | helmet 55, head 60, shoulder 50, panels 60, sleeves 75 % | 7,760 | 4.89 / 24.75 | 0.988 | 0.988 | pass; strap smeared, boot cuffs flattened, panel flecks |
| d | boots own group 70 %, body 58 % | 7,872 | 4.89 / 24.06 | 0.988 | 0.987 | pass; chest strap torn and smeared onto the chain mail (`review/glbclose/sheet_d.png`) |
| e | d + strap/green bands kept | 7,888 | 26.3 / 125 | 0.967 | 0.982 | fail: kept trims split the body into small islands |
| f | e + torso own group 80 %, boots 55 % | 7,978 | 5.92 / 25.0 | 0.988 | 0.989 | fail (thighs, calves in Death) |
| g | f, helmet/head 50, panels 55, boots 65 % | 7,928 | 4.89 / 19.04 | 0.990 | 0.989 | pass; skin fleck and tear on a gold panel |
| h | g, panels 75, boots 75 %, thighs 40 % | 8,024 | 5.03 / 19.04 | 0.991 | 0.991 | pass |
| i | h, torso 70 % | 8,054 | 4.80 / 25.55 | 0.989 | 0.990 | max at the limit (Attack) |
| **j** | **h, sleeves 60, trims 80, head 48 %, thighs 50 %** | **8,020** | **4.90 / 19.04** | **0.990** | **0.991** | **pick** |
| j | thighs 40 % | 7,962 | 5.50 / 19.04 | 0.989 | 0.990 | fail (p99) |

`region_error.py` (body split by dominant bone): the over-limit error sits in the thighs, calves, spine and clavicles
(Death/Dead lying frames); head, helmet, shoulder and panels add almost nothing, so their cut is limited by the close-ups,
not by the error.

**Why j:** the lowest step that passes and looks unchanged in textured and clay close-ups straight from the GLBs
(`review/glbclose/sheet_pick_head.png`, `sheet_pick_body.png`; tiers B/C `sheet_tiers_bc.png`): face, helmet and
crest, strap and buckle, green/blue/red bands, gold panels, both hands, boots, back, Attack and Death. The ~8,000
floor is set by what has to stay exact (5,299 faces: hands 2,394, face front 1,242, small pieces 911, painted trims
491, soles 225); the remaining 4,367 faces were cut to 2,721 (62 %). Steps under 8,000 either failed p99 or tore the
strap/panels.

Texture drift: `texture_drift.py` reads the high-frequency chain mail as drift everywhere (85+ faces over 40 even on
visually clean steps), so `class_drift.py` compares colour classes instead; its remaining flags sit on the thigh
fronts hidden behind the gold panels. No drift-lock round was run (the close-ups were clean; a lock would add faces).

## Build

`scripts/build_export.sh j Cand_83`: `export_cand.py` -> `swap_lod0.py` (into the rollback source: materials,
variants, region ramps, images, sockets, clips byte-identical) -> `build_lods.py` -> `shrink_shadow_lods.py` (inset
shadow LODs, as the source export) -> `carry_variants.py` -> `export/mm7_m222.glb` (7.6 MB; source 7.8 MB).
`compare_structure.py`: nodes, skins, materials, textures, images, extensions, animations (bytes) and mesh names/extras
the same as the source; `KHR_materials_variants` (3 tiers) on all 4 colour and 4 shadow primitives.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| source body | 9,666 | 4,830 | 1,729 | 569 |
| reduced body | **8,020** | 4,010 | 1,594 | 551 |
| scimitar (unchanged) | 558 | 278 | 100 | 32 |

LOD ratios 0.5 / 0.2 / 0.07 (the source's builder defaults 0.5 / 0.18 / 0.06 gave a 470-triangle LOD3 whose face and
arms fell apart; LOD2/3 now stay just under the source's counts rather than halving each level), up to 8 influences on
LOD1-3 like the source, protected points: bounding extremes (5 mm, includes the helmet crest) and LOD0 vertices within
4 mm of the floor in any Death/Dead frame (232 points).

## Checks

- **Grip** (`grip_check.py`): all 1,732 LOD0 vertices with hand + finger weight > 0.5 keep their bind positions
  (max 0.0005 mm) and weights, so the fitted scimitar fist and the open left hand are unchanged.
- **LODs** (`lod_check.py`, `work/lod_check_{src,red}.json`): every LOD keeps the LOD0 bounds and height exactly
  (1.6999 m; the source LOD3 was 1.2 cm lower) and the same lowest point in every clip (Standing -13.0 mm, Walking -16.5,
  Attack -13.6, Death -31.0, Dead +0.7, as the source LOD0); at most 1 stretched face (LOD1, as the source LOD1).
  `review/lods/sheet.png`: all LODs, standing, attack and head.
- **Winding** (`check_winding.py`): 0 inverted closed parts.
- **Viewer**: `review/viewer/` (source export r100 vs reduced r83, tiers A/B/C, all 8 clips; the unchanged scimitar
  added under the `Sword` node for review by `viewer_sword.py`); `tools/run_creature_review.py ... check`: 48 switches,
  no console errors. Shots: `review/shots/sheet_tiers.png` (Standing and the Attack blow, three tiers).

## Weapon

Left byte-identical (`export/mm7_m222_sword.glb` = the source attachment): 558 triangles, most of them in the 1.3 cm
grip and guard the fist is fitted to; a cut of the blade would save under ~200 triangles. Not worthwhile.

## For the user to look at

- Clay renders show the reduced shoulder guard's lower rim and the chest slightly more faceted; textured they read the
  same.
- LOD3 (551) has a flat face, as coarse as the source LOD3.
- Pre-existing in the source (unchanged): tier C tints the neck skin yellow and tier B orange (hair/cloth ramp spill
  over the skin, `sheet_tiers_bc.png`, both columns).
- The body sits at 8,020, 20 above the 8,000 aim; everything below needed cuts the close-ups rejected.

## Install later (not run)

Replaces the batch A export of `mm7_m222_claude/` (same nodes, clips, materials, variants and sword socket):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m222_reduce_claude/export/mm7_m222.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m222_reduce_claude/export/mm7_m222_sword.glb --world mm7
```

then the source project's `integration/actors.yml` binding as described in `../mm7_m222_claude/README.md`.
Rollback: `work/mm7_m222_source_pre_reduce.glb` (+ `_sword`).

Reproduce: `TOKEN=<lease> scripts/reproduce.sh` (import + weld, dumps, regions, sets j, ladder j at 0.83, export,
structure/grip/LOD checks, viewer). Note: `decimate_tex.py` names results by `int(ratio * 100)`, so two ladder ratios
with the same integer percentage overwrite each other; pick distinct ones.

## Clips updated (2026-10-20)

The source project's walk/run ankle twitch was fixed after this reduction (`../mm7_m222_claude/scripts/foot_level.py`). `scripts/transplant_clips.py` copied the re-exported clips into `export/mm7_m222.glb` and every `review/viewer/*.glb` (geometry, LODs, materials and variants unchanged), and `work/mm7_m222_source_pre_reduce.glb` is now that re-export. After any later re-export of the source, run `python3 scripts/transplant_clips.py ../mm7_m222_claude/export/mm7_m222.glb export/mm7_m222.glb export/mm7_m222.glb`.
The walk bob fix (`walk_bob.py`, same day) was carried over the same way.

**Accepted 2026-10-20**; installed 2026-10-20 from `../mm7_batches/BATCH_A_stage/` (listed in REDUCTION_LEDGER.md).
So was the Hit/Death foot-roll fix (flatness-weighted, smoothed roll; same day); the stage was rebuilt.

## Floor fix (2026-10-21, MM7 creature post-process)

[Creature post-process](../CREATURE_POSTPROCESS.md) step 2. Audit before: dying sinks to -3.4.
`claude_shared/floor/floor_fix.py work/floor_fix_base/mm7_m222.glb export/mm7_m222.glb --lift-joints Dead Death --lift-only 'B_Skirt*,Robe_*,…' --ground-death Death Dead`, then
`check_winding.py` (0 inverted) and `tools/install_model.py --world mm7`. Only animation samplers changed; the
pre-fix export is `work/floor_fix_base/mm7_m222.glb`, and the `.blend` master predates the fix (rerun the same operation
after any re-export).

## Gait rollout (2026-10-31)

Package [`gait_rollout_20261031/h07`](../gait_rollout_20261031/h07/README.md) appended Walk2 (humanoid set Armed-Walk, 0.88 s), Jog (Unarmed-Run-Forward, 0.72 s) and Sprint (Unarmed-Sprint, 0.58 s) to the installed
`assets_source/worlds/mm7/models/mm7_m222.glb` and installed it (existing clips, meshes, skins and materials
byte-identical). The sword arm is lifted (eased, up to 25 deg) in the half of the run loop where the right knee comes
through, so the blade clears the thigh. Bindings for the coordinator (`h07/bindings.yml`): walking: Walk2, stride_length 1.8373, run: Jog, run_stride_length 3.3105, sprint: Sprint, sprint_stride_length 4.3626. `Running` is kept in
the GLB but no longer bound for locomotion. Rebuild: `level_generation/creatures/gait_rollout_20261031/h07/scripts/rebuild.sh m222`
(from `h07/work/mm7_m222_pre_gait.glb`, the rollback source). A far-LOD repair rerun, a floor fix or any re-export of this
model must re-graft these clips: copy the new source over `h07/work/mm7_m222_pre_gait.glb` and rerun the rebuild, then
install with `tools/install_model.py`.
