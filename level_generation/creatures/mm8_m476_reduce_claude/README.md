# MM8 Troll (`m476`, Troll A/B/C: Clubman / Warrior / Chieftain) + skull club reduction (2026-10-18)

Default route of [RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md), including its split-seam and MM8 batch lessons;
scripts copied from `mm8_m492_reduce_claude/` (parent-transform fix) plus the Nightmare's UV weights and the Cyclops's
dark-sliver check. No Meshy credits. **Not installed** (awaiting user review).

Sources: the installed `assets_source/worlds/mm8/models/mm8_m476.glb` and `mm8_m476_club.glb`, identical to
`mm8_m476_claude/export/`; copies in `work/mm8_m476{,_club}_source_pre_reduce.glb` (rollback sources). No gate config
in the creature project. All shading was judged from GLBs imported directly (`scripts/glb_views.py`), never from the
welded `work/source.blend`; the reduced meshes keep plain smooth normals (the installed body and club shade the same).

## Result

| | LOD0 | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|
| body installed | 11,738 | 5,865 | 2,087 | 646 |
| body reduced | **8,802** | 4,395 | 1,549 | 472 |
| club installed | 3,087 | 1,543 | 555 | 185 |
| club reduced | **1,575** | 555 | 185 | — |

Body + club LOD0: 14,825 -> 10,377 (-30 %). Body LODs use the creature's own ratios (`tools/build_actor_lods.py`
defaults 0.5 / 0.18 / 0.06, 8 influences); the club keeps its old LOD2/LOD3 as LOD1/LOD2 (the old LOD1, 1,543, was no
longer coarser than the new LOD0 and was dropped). Exports: `export/mm8_m476.glb` (5.99 MB, installed 6.2 MB),
`export/mm8_m476_club.glb` (3.86 MB, installed 4.0 MB). Clips byte-identical; three tier variants on all 8 body
meshes and all club LODs; check_winding 0 inverted closed parts on both.

## Body: per-region ladder

- Kept exactly (3,760 faces): small separate pieces up to 160 faces (eyes, mouth piece, teeth, ~40 hair locks; 1,826),
  left-hand finger faces (the fitted club grip; 727), soles (below 6 cm; 244), 3 cm patches around 41 source vertices
  with idiosyncratic weights that the transfer missed by over 15 mm (`err_lock.py`; chest/armpit/back, e.g. a
  chest vertex weighted to the right upper arm), the face skin within 1.5 cm of the mouth and teeth (`lip_keep.py`),
  and one drift-lock round around the strong dark slivers.
- Groups: face/head skin (head texture set) 70 %, hands 50 %, rest at the ladder ratio.
- Weights: UV-based (`REA_WEIGHTS=component`, `uv_weights.py` from the Nightmare); max error 18.0 -> 12.3 mm
  against the nearest-face transfer.

| ladder (limits p99 5.1 mm, max 25.5 mm) | triangles | p99 / max mm | IoU | SSIM | |
|---|---:|---|---|---|---|
| first ladder, face 70 % | 8,684 | 4.18 / 29.5 | 0.996 | 0.993 | fail (weights) |
| face 60 %, UV weights | 8,330 | 4.29 / 12.3 | 0.995 | 0.992 | pass, rejected visually |
| **face 70 % + lips + lock** | **8,802** | 4.63 / 12.5 | 0.995 | 0.992 | **pick** (lowest passing) |
| same, 74 % | 8,684 | 5.25 / 16.3 | 0.994 | 0.991 | fail (p99) |

Face at 60 % flattened the brow and folded the right mouth corner so a tooth corner showed (`review/glb/sheet_pick_face.png`);
at 70 % with the lip zone kept, mouth, teeth and brow match (`sheet_r75_face.png`). The remaining body error sits in
the baggy trousers and shoulders. Body, hands, grip, boots, the attack wind-up from below and Death match in clay and
textured (`review/glb/grid_r75_body_{clay,tex}.png`). No split seams (no coincident vertex pairs); no face stretches
in any clip at any LOD; every LOD keeps the source bounds and floor clearance (`work/lod_check_{src,r75}.json`).

## Club

Pieces: skull with horns (2,177), wrapped grip end (549), collar (189), thin shaft (172). The grip end and the shaft
are kept exactly (the fist's grip faces, 293 within 2.5 cm of the left hand, lie in the grip end); collar 50 %; skull
ladder. Club-space two-way error at 51 %: p99 4.52, max 11.16 mm; 44 % rounded the horn tips and collapsed an eye
socket (`review/glb/sheet_club.png`). Normals transferred from the unwelded source club. Scripts: `club_dump.py`,
`club_prep.py`, `club_build.py`, `club_swap.py` (`REA_LOD_BELOW=0.6`).

## Retexture check

- **Texture sets:** one shared 2080x1024 atlas (body half 1K, head half 1K) plus the club's own 1K set. UVs are
  carried by the texture-aware collapse; images byte-identical except the base-colour fix below.
- **Drift:** 4 faces over 40 (22 cm2, vest shoulder edges), p99 14.0; no visible change.
- **Dark slivers** (Cyclops test, 5 or more of 48 samples): 17 faces before the lock (boot straps and rivets, a
  shoulder trim, back hem, scalp under the hair), 5 after one lock round (back hem/boots, invisible in close-ups);
  `review/spots/grid_dark5{,_lock}.png`.
- **Head vs body:** face skin and hand/forearm skin match (linear luminance median 0.253 vs 0.267, same hue); the
  collar hides the neck junction.
- **Existing Meshy fault, fixed locally:** the black hair locks carried yellow-green skin-coloured specks (12.5 % of
  their samples); the native sprites show a plain black crest. `scripts/hair_fix.py` recolours the bright texels used
  only by hair-lock triangles (and their 2 px gutter) to the hair's median dark colour, rank-scaled; 29,071 texels,
  the 380 texels shared with other faces untouched. `swap_base.py` swaps only the base-colour image.
  All tiers: `review/glb/sheet_hair.png`. Pre-fix export: `work/mm8_m476_r75_pre_hairfix.glb`.
- **Verdict:** no Meshy retexture for any set (body, head, club). The hair locks' shard-like geometry is the
  installed model's and was not changed.

## Flat feet (round 2, 2026-10-18)

User review: "feet not on ground but angled" (wide idle stance, both boots rolled onto an edge). The installed model
and the reduction measure the same (clips byte-identical), so it predates the reduction. Measured on the skinned lower
boot (`scripts/flatten_feet_ik.py --measure`; the heel sole vertices are about half calf-weighted, so a rigid
foot-space sole misses them): planted-frame sole tilt mean / max (deg), spread of the bottom 2 cm band (cm, about 2
is flat), lowest point (cm) — `work/feet_installed.json` vs `work/feet_after.json`:

| clip | foot | before tilt | before spread | before lowest | after tilt | after spread | after lowest |
|---|---|---|---:|---|---|---:|---|
| Standing | L | 11.8 / 12.9 | 7.36 | 0.29..0.30 | 0.0 / 0.0 | 2.46 | 0.0 |
| Standing | R | 7.9 / 8.8 | 5.57 | 0.30 | 0.0 / 0.0 | 2.44 | 0.0 |
| Fidget | L | 11.3 / 13.0 | 7.04 | 0.0..2.84 | 0.2 / 3.2 | 2.43 | 0.0..2.62 |
| Fidget | R | 8.0 / 11.0 | 5.62 | 0.0..1.07 | 0.0 / 0.0 | 2.31 | 0.0 |
| Hit | L | 9.4 / 11.7 | 5.84 | 0.0..2.85 | 0.4 / 1.6 | 2.21 | 0.0..2.53 |
| Hit | R | 9.6 / 10.5 | 6.18 | 0.0..2.29 | 2.4 / 7.0 | 3.34 | 0.0..2.77 |
| Attack | L | 10.6 / 11.4 | 6.40 | 0.97..2.78 | 0.2 / 1.9 | 2.16 | 0.0..2.75 |
| Attack | R | 9.8 / 13.6 | 6.43 | -0.17..0.28 | 0.0 / 0.0 | 2.16 | 0.0 |
| Walking | L | 15.2 / 23.9 | 10.07 | 0.0..2.41 | 10.4 / 15.8 | 7.05 | 0.0..1.69 |
| Walking | R | 11.6 / 22.6 | 7.44 | -0.10..2.26 | 7.8 / 14.9 | 5.27 | -0.07..1.85 |

`flatten_feet_ik.py` (after the MM6 Knight's `flatten_feet.py`): per planted frame the foot rolls flat about the sole
point it stands on (Standing, Fidget, Hit, Attack: roll and pitch), a two-bone IK on thigh and calf moves the ankle
there and puts the lowest skinned boot point on the floor, and the foot turns further until the skinned sole plane is
level. Planted weights (full below 3 cm, none above 8 cm; IK none above 5 cm) are smoothed over time, and per frame
only as much of the correction is used as keeps the knee bent at least 25 deg (min-filtered, smoothed). Only the six
leg rotation channels of those five clips change; pelvis, root motion, arms (club bone identical in every frame),
Running, Death and Dead are untouched.
- Walking keeps part of its toe-up heel contact: the clip lands on the heel with the toe 20 deg up for about a third
  of the cycle on a nearly straight leg; flattening it fully locked the knees straight (the ankle cannot reach the
  floor without lowering the pelvis), so it is levelled as far as the knee limit allows (16-19 frames limited).
- Knees straighten 3-10 deg in the stance clips (minimum flex 50-55 deg, crouch kept); per-frame rotation steps stay
  near the source's (largest: Hit right calf 12.3 -> 17.5 deg, Walking calves 17-18 -> 20-22 deg).
- Floor per LOD: lowest point in every clip within 0.55 cm below to 1.2 cm above the floor (installed: within 0.68 cm
  below); no stretched faces; bounds unchanged.
- Renders (floor at 0, Standing 0, Fidget 30, Hit 3, Attack 20, Walking 6 and 18, front and side):
  `review/feet/grid_feet_tex.png` (installed | fixed), `grid_feet_clay.png` (before | after).
Pre-fix export: `work/mm8_m476_r75_pre_feet.glb`. No shared gate config exists for this creature.

## Viewer

`review/viewer/`: installed vs reduced for each tier, the club merged under the `Club` bone for review only
(`merge_club.py`, `viewer_variants.py`); `python3 tools/run_creature_review.py --project
level_generation/creatures/mm8_m476_reduce_claude check`: 48 switches, no console errors.

## Install (after user review)

```sh
python3 tools/install_model.py level_generation/creatures/mm8_m476_reduce_claude/export/mm8_m476.glb --world mm8
python3 tools/install_model.py level_generation/creatures/mm8_m476_reduce_claude/export/mm8_m476_club.glb --world mm8
OPENYAMM_REGRESSION_FILTER=mm8_troll ./build/game/openyamm --world mm6 --headless-run-regression-suite actors
```

The case is `mm8_troll_actor_models_keep_native_tiers_and_club` (`game/outdoor/HeadlessOutdoorDiagnostics.cpp`); the
creature README runs it with `--world mm6`. Rollback: install `work/mm8_m476_source_pre_reduce.glb` and
`work/mm8_m476_club_source_pre_reduce.glb` the same way.

## Reproduce

`import_source.py` (REA_NODE=Troll, REA_GLB=the rollback source) -> `dump_mesh.py` -> `dump_bones.py` -> piece labels
(`work/piece.npy`) -> `make_groups.py` -> `dump_weights.py` -> first ladder -> `err_lock.py` -> `lip_keep.py` ->
`REA_WEIGHTS=component REA_KEEP_FACES=... REA_GROUPS=work/groups.npy REA_GROUP_RATIOS=1:0.7,2:0.5 run_ladder.sh`
-> `dark_slivers.py` + `drift_lock.py` -> final ladder (`work/ladder_lock.blend`, copy to `work/ladder.blend`) ->
`export_cand.py` (Cand_75) -> `swap_lod0.py` -> `build_lods.py` -> `carry_variants.py` -> `hair_fix.py` +
`swap_base.py` -> `flatten_feet_ik.py <in> <out> Standing:full,Fidget:full,Hit:full,Attack:full,Walking:walk`
(checks: `feet_deltas.py`, `knee_curve.py`, `lod_check.py`); club as above.


## Installed (2026-10-18)

User: "ok troll good". `check_winding.py`: 0 inverted closed parts (body and club). Installed both with
`tools/install_model.py ... --world mm8`; `OPENYAMM_REGRESSION_FILTER=mm8_troll ./build/game/openyamm --world mm6
--headless-run-regression-suite actors`: `mm8_troll_actor_models_keep_native_tiers_and_club` and
`mm8_troll_peasant_actor_models_keep_native_tiers_and_bone_club` pass. Recorded in
[REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Rollback: install `work/mm8_m476_source_pre_reduce.glb` and
`work/mm8_m476_club_source_pre_reduce.glb`.

## Gait rollout (2026-10-31)

New locomotion clips: `Walk2` (humanoid set Armed-Walk, 0.90 s, stride 1.3097) for wandering, `Jog`
(Unarmed-Run-Forward, 0.76 s, 2.244) for Standard's chase and `Sprint` (Unarmed-Sprint, 0.64 s, 3.5221) for MAW's chase;
arms and club from `Running`. Package [h20](../gait_rollout_20261031/h20/README.md) appended them to the installed
source (`assets_source/worlds/mm8/models/mm8_m476.glb`; existing clips, meshes, skins and materials byte-identical;
pre-gait copy `../gait_rollout_20261031/h20/work/mm8_m476_pre_gait.glb`) and installed it; the bindings are in
`../gait_rollout_20261031/h20/bindings.yml` for the rollout coordinator. Rebuild:
`level_generation/creatures/gait_rollout_20261031/h20/scripts/rebuild.sh m476`. A far-LOD repair, head-bob, reduction or
texture rerun that rebuilds this source must keep or re-graft these clips (copy the new source over the pre-gait copy
and rebuild).
