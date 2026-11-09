# MM8 Cyclops (`m520`, Cyclops / Cyclops Hunter / Cyclops Warrior) reduction (2026-10-18)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), no-retexture variant: no Meshy credits. Scripts
were copied from `mm8_m492_reduce_claude/` (coincident-vertex separation, exact source weights), with the humanoid
rules applied (per-region budgets, kept small pieces, shared gate runner). Not installed.

Source: the installed `assets_source/worlds/mm8/models/mm8_m520.glb`, identical to `mm8_m520_claude/export/`
(md5 `0bf02338…`), copied to `work/mm8_m520_source_pre_reduce.glb` (rollback source). One material (`Cyclops_A`, with
head and body merged into one 2080×1024 atlas, head set at u > 0.5), node `Cyclops`, 8 influences, 8 clips. The
boulder (`mm8_m520_boulder.glb`, 522 triangles) is light and unchanged.

## Budgets (`scripts/make_groups.py`, locks)

| Region | Faces | Treatment |
|---|---:|---|
| small pieces up to 250 faces (neck discs, fangs, arm band) | 812 | kept |
| finger-weighted faces (fitted boulder grip) | 1,361 | kept |
| loincloth and hip box (the m520 LOD builder's protected region) | ~1,000 | kept: jagged tips blunted from 66 % |
| eye, lids and brow (7.5 cm around the iris) | ~1,700 | kept: any head cut collapsed the upper lid and notched the iris |
| soles (faces reaching below 2 cm) | 381 | kept (gated model) |
| head set outside the eye | 6,149 | 40 % (30 % flattened the lips) |
| palm/back of hand | 867 | 60 % |
| boots (centre below 0.72 m) | 2,901 | 55 % (wrap folds flattened at a shared 40 %) |
| rest of the body | | ladder budget |

Locks found by checks:
- `error_lock.py`: 4 cm patches around source vertices over 20 mm in any clip. Lower-back skin weighted to
  B_L_UpperArm tore 39 mm in Running. A second spot was at the waist, 54 mm in Death:12.
- `drift_lock.py`, one round: base-colour drift.
- `dark_slivers.py` + `drift_lock.py`: dark texture slivers. A collapsed face spanning a UV-island edge samples the
  dark gutter. The median drift check passes these; they show as dark slashes on the back and elbow.
- `spot_lock.py`: two slashes found by eye, ray-picked in GLB renders (`pick_rest.py`).

## Ladder

Limits scaled to the 2.39 m height: p99 7.17 mm, max 35.85 mm. Final run (`work/selection_pick.json`):

| step | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| source | 17,917 | | | | |
| **65 %** | **11,645** | 6.64 / 29.98 (Death:12) | 0.994 | 0.992 | **pick** |

Earlier runs show where it stops. With the same locks, 64 % passed only barely (p99 7.10). Below about 62 % the
body's share falls under 40 %, and Death:12 tears at 54-55 mm.

## Normals: judge from GLBs only

The installed GLB has plain smooth normals (`normals_probe.py`: median 3.9° from area-weighted smooth normals). The
eye and face checks were first done on renders of `work/source.blend`, which turned out to be invalid.
`import_source.py` welds the mesh, and Blender stores custom normals relative to the default normals, so the weld
scrambles them. Those "source" renders show fake wrinkles and lumps (`review/close/`, `review/ladder*`: do not judge
shading from them).

The ladder therefore keeps plain smooth normals (`REA_NORMALS` is off by default). All visual review uses GLBs
imported directly (`glb_close.py`, `review/glbclose/`):
- `sheet_a.png`: no eye lock vs the eye lock;
- `sheet_pick_up.png`, `sheet_pick_lo.png` (four sides) and `sheet_pick_misc.png` (eye, face, hand, overhead throw,
  death) of the final export.

## Build and checks

`export_cand.py` -> `swap_lod0.py` -> `lods_trim.py` -> `mm8_m520_claude/scripts/fit_lod_soles.py` ->
`shrink_shadow_lods.py` (both run read-only from that project) -> `carry_variants.py`: `export/mm8_m520.glb`, 7.8 MB
(installed 9.1 MB).

`lods_trim.py` trims the accepted fitted LOD1-3 to 50 / 22 / 12.5 % of the new LOD0, the creature's own ratios, with
these locked:
- hands and fingers (fitted grip);
- soles below 6 cm;
- the loincloth box;
- vertices within 2 cm of each bounding extreme. An unlocked LOD3 grew 1.5 cm at the crown and lost 2.6 cm at the upper
  back.

The shared gates cap LOD1-3 at 55 / 25 / 13 % of LOD0, so the installed LODs could not be kept.

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| installed | 17,917 | 8,903 | 3,998 | 2,223 |
| reduced | 11,645 | 5,821 | 2,553 | 1,448 |

- Shared gate runner with the creature's `gates.json` (boulder unchanged): **PASS, 6,086 PASS / 140 INFO /
  136 N/A**, the same counts as the installed release (`work/gates/gates.md`).
- Open-cloth panel check (copy of the project's `cloth_surface_gates.py`, report here): PASS
  (`work/cloth_surface_gates.json`).
- `lod_check.py`: every LOD has the installed LOD's bounds and lowest point (0.2 mm), and no face stretches in any clip
  (`work/lod_check_r65.json`). There is no split seam (no coincident vertices with other weights).
- Viewer `review/viewer/` (installed vs reduced runtime GLBs; untinted, without the boulder):
  `tools/run_creature_review.py --project level_generation/creatures/mm8_m520_reduce_claude check` gives 16 clip switches
  and no console errors.

## Install (after user review)

```sh
python3 tools/install_model.py level_generation/creatures/mm8_m520_reduce_claude/export/mm8_m520.glb --world mm8
OPENYAMM_REGRESSION_FILTER=mm8_cyclops ./build/game/openyamm --headless-run-regression-suite actors
```

The regression case is `mm8_cyclops_actor_models_keep_tiers_and_boulder_release`. Rollback: install
`work/mm8_m520_source_pre_reduce.glb` the same way. Add the row to [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md).

## Reproduce

1. `import_source.py` (REA_NODE=Cyclops, REA_GLB=the rollback source), then `REA_PROTECT=B_Head dump_mesh.py` and a
   `vweights.npz` dump.
2. `small_pieces.py` -> `REA_EYE_R=0.075 make_groups.py` -> `error_lock.py` -> `drift_lock.py` / `dark_slivers.py` /
   `spot_lock.py` -> `work/keep_final5.npy`.
3. `REA_KEEP_FACES=work/keep_final5.npy REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.4,2:0.6,3:0.55
   run_ladder.sh pick 0.65`.
4. Build as above with targets `5820,2560,1450`.

## Retexture check (2026-10-18)

Report only: the user accepted this export as shown; `export/mm8_m520.glb` is unchanged and no credits were spent.
Judged only from GLBs imported directly (`scripts/retex_views.py`). Tiers are baked with the engine ramp rule
(`scripts/tier_bake.py`).

**Texture sets.**
- One material (`Cyclops_A/B/C` variants) on a 2080×1024 atlas: body half at 269 texels/m, head half at 842
  (reduced 268 / 829).
- Base colour, metal-rough, normal and region mask are byte-identical to the installed GLB.
- UVs are in range, with no zero-area or NaN faces, in both source and reduced.
- One region (R channel, 78,777 texels) carries the tier ramp: belt, wrist wraps, arm band, neck discs.

**Drift and dark slivers** (`scripts/texture_drift.py`, `scripts/sliver_regions.py`).
- Median drift: 7 faces over 40, p99 21.6.
- Strong dark slivers (8 or more of 48 samples darker than the source by over 60):
  - body: 5 faces on the back of the upper arms;
  - head set: 5 hair-strand faces of 0.2–0.5 cm²;
  - boots: 4 faces on the fur.
- None of these show in close-ups (`review/retex/sheet_spots.png`). The weaker 2-sample hits are high-contrast fur
  and skin pattern.

**Close-ups per tier, installed vs reduced.**
- Sheets: `review/retex/sheet_face.png`, `sheet_neck_torso.png`, `sheet_limbs.png`, `sheet_spots.png`.
- Face, eye, teeth, hair, torso, back, belt, loincloth and boots match.
- The neck below the chin uses the body set and is softer than the face, as installed.

**Existing defect (installed too, not from the reduction): region-mask spill onto arm skin.**
- A skin-coloured, fully masked blob above the left wrist wrap (back of the forearm, 920 texels) shows as an angular
  wrap-coloured patch: brown in A, blue in B, red in C.
- Wedges below both wraps on the backs of the hands do the same.
- The base colour there is plain skin; only the mask is wrong.

**Mask fix (user: "cyclops - if you can fix it cleanly do so"; applied 2026-10-18, not installed).**
`scripts/mask_fix.py`, with `scripts/texel_map.py` (per-texel face and rest position), changes only the region
mask. On the arms it clears masked texels that meet all of these:
- bright (luminance over 0.45);
- nearer the local unmasked bright skin than the dark wrap core in CIE Lab, and within dE 12 of the skin;
- connected to unmasked skin;
- not on a wrap face (faces with 15 % or more dark wrap-core texels keep every texel).

It also clears the forearm blob whole. Gutter texels follow their nearest surface texel, only where that one was
cleared. Result: 5,242 texels cleared, nothing outside the arms, no dark or mid-tone texel touched.

Earlier attempts and why they were dropped:
- Clearing every gutter texel near a cleared one, and treating the unmasked dark fur rims as skin, both left orange
  flecks on the right wrap's bottom fringe.
- Without the wrap-face rule, a tan notch opened in the left wrap's lower corner.
- A 30 % wrap-face threshold made the left wrap's edge ragged without removing more.

What remains: one tiny tinted tip at the front corner of the left wrap's lower edge, which reads as part of the
wrap.

Verification in all tiers:
- `review/retex/sheet_maskfix_wrists.png`: both wrists front, back and side, and the forearm.
- `review/retex/sheet_maskfix_other.png`: hands, arm band (untinted, as installed), neck discs, belt and
  loincloth front, back and side, and the back.
- `review/retex/sheet_maskfix_fringe.png`: fringe crops.

Export: `scripts/swap_mask.py` swapped only the region-mask image into `export/mm8_m520.glb`. The pre-fix export,
identical to the installed source, is kept as `work/mm8_m520_r65_pre_maskfix.glb`.
- Only that one buffer view differs.
- The JSON, all 1,172 accessors (mesh, LOD1-3, shadow LODs, skin, clips) and the other three maps are
  byte-identical.
- The viewer copy is updated, and the viewer check gives 16 switches with no errors. The viewer shows untinted base
  colour, so the tier evidence is in the sheets.

**Verdict.** Head set: no retexture. Body set: no retexture; the mask spill is fixed locally. No credits spent.

To install:
```sh
python3 tools/install_model.py level_generation/creatures/mm8_m520_reduce_claude/export/mm8_m520.glb --world mm8
OPENYAMM_REGRESSION_FILTER=mm8_cyclops ./build/game/openyamm --headless-run-regression-suite actors
```
Rollback to the accepted, installed reduction: install `work/mm8_m520_r65_pre_maskfix.glb`.

## Mask fix installed (2026-10-18)

User: "cyclops - if you can fix it cleanly do so". The region-mask-only fix (`scripts/mask_fix.py`, `swap_mask.py`;
sheets `review/retex/sheet_maskfix_*.png`) was installed with `tools/install_model.py --world mm8`; the Cyclops
regression passes again. Previous install (reduction without the fix): `work/mm8_m520_r65_pre_maskfix.glb`.
Rollback to the unreduced model: `work/mm8_m520_source_pre_reduce.glb`.

## Gait rollout (2026-10-31)

Package h19 of the [gait rollout](../gait_rollout_20261031/h19/README.md) appended new clips to the installed source
for Cyclops A/B/C: `Jog` (library Unarmed-Run-Forward legs and trunk on this model's `Running` arms, 0.84 s) and `Sprint` (Unarmed-Sprint, 0.70 s). Existing clips, meshes and skins are unchanged (binary prefix identical). Installed 2026-10-31
with `tools/install_model.py --world mm8`; bindings for the coordinator (`../gait_rollout_20261031/h19/bindings.yml`):
run: Jog, run_stride_length: 3.7053, sprint: Sprint, sprint_stride_length: 4.8166. `gait_gate.py` passed for every tier under Standard and MAW
(`../gait_rollout_20261031/h19/review/m520_gait_gate.txt`). Rebuild: `../gait_rollout_20261031/h19/scripts/rebuild.sh
m520` (from the pre-gait copy `../gait_rollout_20261031/h19/work/mm8_m520_pre_gait.glb`). A far-LOD repair, head-bob or
reduction rerun replaces the source without these clips: copy the new source over that pre-gait copy and rerun the
rebuild before installing. Rollback: install the pre-gait copy and drop the bindings.
