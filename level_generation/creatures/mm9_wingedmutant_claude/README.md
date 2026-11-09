# MM9 Winged Mutant family (mm9_wingedmutant) — 3D model, 2026-10-30

The MM9 harpy (`mm9/extracted/MODELS/MODELS/WINGEDMUTANT.abc`, 87 joints, 16 clips: a winged woman-bird with no arms,
raptor legs and a whip tail) for the MM9 world: Winged Oddity (MONSTERS.txt 159, skin WINGEDMUTANT1, `MM9 Winged
Mutant A`), Winged Mutant (160, WINGEDMUTANT2, `B`), Winged Aberration (161, WINGEDMUTANT3, `C`). Built on the MM9
rig-reuse route of `../mm9_dfly_claude/` and `../mm9_lobber_claude/`: a new HD Meshy mesh weighted to the ORIGINAL
MM9 skeleton, the MM9 clips played with only the listed fixes. Progress, hashes and receipts:
`creature_3d_progress.json`. Shared route scripts with `../mm9_greaterdemon_claude/` (`fit_mm9.py`, `rig_mm9.py`,
`fix_winding.py`, `clips_mm9.py`).

The wings are the arms (no hands or fingers), so this is not a humanoid-hand body.

## Texture quality pass (2026-10-30) - current maps

`../claude_shared/TEXTURE_QUALITY_PASS.md`. The user approved the reworked model and clips; mesh, rig, weights,
clips, sockets, hover and the head's look are unchanged, only UVs and texture maps changed. **10 Meshy credits**
(body retexture v2, backup account); creature total **40 / 40**.

- **Measured cause.** The recipe's ranking (24.9 %) predates the rework. On the installed rework the body/wing
  texture used **8.1 %** of its 2K atlas: the v1 Smart UV layout of the whole asymmetric body, of which symmetrize.py
  kept only the +x half's islands and the graft dropped the old head's (x3) islands. Equivalent 585 px, 9.4 % of the
  surface on fragments. The 1K head set (Smart UV, 810 islands) used 20.1 % with 24.9 % fragments, while Meshy's head
  return is 2K: the downsample to 1K threw away half of its paint.
- **Body/wing UVs** (`scripts/uv_texpass.py` on `work/head_v3.blend` -> `work/uv_texpass.blend`): non-head n-gons
  triangulated mirror-consistently (`scripts/texpass_mesh.py`), `claude_shared/uv_atlas.py` on the +x half only
  (head excluded, one density, 2 px margin, 2048), every -x face given its mirror twin's UVs, so both halves still
  share texels (worst mirror match 0.8 um). Upload `texturing/wmut_body_upload_v2.glb`: whole body incl. head, the -x
  half and the head collapsed to one UV point (zero area), so Meshy paints only the +x half at the full atlas.
- **Retexture v2** (`requests/retexture_v2.json`): same four HD masters, `meshy-7`, **4K**, our UVs; the returned GLB
  keeps the layout (same UV area; one zero-area sliver dropped). `compose.py` now reads it: colour 4K -> 2K Lanczos once,
  normal 4K -> 1K, AO re-baked on the new UVs (`textures/wmut_ao_2k_v2.png`), regions `work/regions_body_v2.npz`.
- **Grade** gentle (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`): on a feather and a
  membrane crop the default grade blurred the fine pebbling; gentle keeps it, and its region means stay nearest v1
  (skin 55/77/88 vs v1 64/82/95, feathers 27/35/51 vs 25/31/44). Body ramps refitted: tier A errors skin 4.0,
  feathers 3.0 levels (v1 4.3 / 2.8). The wing channel was then matched to the approved wing, see the next point.
- **Wing tone (user correction, same day).** The first pass read lighter and more pebbled than the approved wing. Measured
  on the wing surface as the game shows it (`scripts/wing_tone.py`: area-weighted samples, tier ramps applied), the mean
  had barely moved; the contrast had (tier A luminance sd 60 vs approved 40, linear p95 0.60 vs 0.30), and tiers B/C
  had lost hue (B 122/27/25 vs 133/5/0). Two steps, no Meshy job, no layout change:
  `scripts/wing_grain.py` scales the wing-region log-luminance detail finer than 12 texels by 0.625 (twice the approved
  amplitude at the same surface scale, kept at 1.25x; edges stay in place, hue untouched) ->
  `textures/wmut_basecolor_graded_wing.png`, read by `compose_head.py`; `wing_tone.py --write` fits each tier's wing ramp
  by quantile matching to the approved wing -> `textures/wmut_wing_tone.json`, read by `compose.py`.
  Result on the wing surface, approved -> now: A 63/80/92 sd 40.1 -> 63/80/92 sd 39.8, B 133/5/0 sd 17.5 -> 133/5/0
  sd 17.4, C 115/70/0 sd 38.4 -> 115/70/0 sd 38.2. Fine detail stays 2.3x the approved (0.74 vs 0.32 relative to the
  mean). The bright rim along the approved membrane's lower edge belonged to the old paint and is not reproduced.
  Accepted from review-viewer shots, not Blender: `review/wing_tone_sheet.png` (tiers A/B/C, approved | new, side and
  close wing; shots `review/shots/wt_*`, made with the approved GLBs temporarily in the manifest).
- **Head set, same paint** (no credits): `scripts/head_uv_texpass.py` re-lays HeadUV with `uv_atlas.py` (1024, 2 px),
  the triangles the old layout made dense (face skin, eyes, teeth: 5.6 % of the head surface) kept 4.55x denser as
  measured on it; `scripts/resample_head.py` carries Meshy's 2K head maps from the old HeadUV into the new one
  (bicubic, gutters extrapolated from the nearest triangle, the +y-down tangent normals rotated per triangle by the
  orthogonal part of the old -> new UV map) -> `work/head_relayout/`, which `compose_head.py` now reads. The approved
  face colours are pinned (`textures/wmut_head_pin.json`: the rework's skin-luminance match and its Wmut_Head ramps),
  so the head looks the same in every tier; only the neck seam blends to the new body's neck colour.
- **Rebuild:** `TOKEN=<lease> scripts/rebuild_v3.sh [--install]` (graft -> symmetrize -> `transfer_texpass_uv.py`
  copies UVMap and HeadUV from `work/uv_texpass2.blend`, worst vertex match 1 um -> back faces -> head set -> export ->
  runtime -> viewer tiers). One-time texture steps, in order, on `work/uv_texpass.blend`: `dump_regions.py ...
  regions_body_v2.npz Body`, `bake_ao.py ... Body textures/wmut_ao_2k_v2.png 0.03 2048`, `compose.py`, the gentle
  grade on `textures/wmut_basecolor.png`, `compose.py` again; `head_uv_texpass.py` (-> `uv_texpass2.blend`) and
  `resample_head.py`; after a first `rebuild_v3.sh`: `wing_grain.py`, `compose_head.py head_v6.npz`,
  `wing_tone.py --write`, `compose.py`, then `rebuild_v3.sh --install` again. Never re-run the two UV scripts: xatlas packs differently per run and the paint is bound to them.

| `texture_quality.py` (LOD0) | Body + wings `Wmut_A` (2K) before | after | Head `Wmut_Head_A` (1K) before | after |
|---|---|---|---|---|
| Atlas use | 8.1 % | **52.3 %** | 20.1 % | **47.4 %** |
| Equivalent fully used square | 585 px | **1,481 px** (x2.53) | 459 px | **705 px** (x1.54) |
| Density p10 / p50 / p90 | 1,010 / 1,118 / 1,194 | 2,744 / 2,809 / 2,932 | 105 / 115 / 124 | 168 / 175 / 185 |
| Spread p90/p10 | 1.18 | 1.07 | 1.19 | 1.10 |
| Islands / surface on fragments | 625 / 9.4 % | 214 / 0.5 % | 810 / 24.9 % | 306 / 6.8 % |
| Stretch p90 | 1.42 | 1.15 | 1.54 | 1.25 |
| Meshy source | 2K, Smart UV | 4K on the new UVs | 2K (same paint) | 2K (same paint) |

(Head density is per head size; mirrored halves count once in the body atlas.) The 55 % target is missed narrowly
(52.3 %): the wing membranes are two large charts with jagged spar edges. The head layout misses it too (47.4 %;
17 hair locks), and its paint still carries the blotches Meshy painted on the old fragments, since it was not
repainted.

LOD0 positions, triangle count (12,599: one zero-area sliver in the symmetry plane is no longer doubled), clips,
`Socket_Mouth` and hover +0.5565 match the rework install; LOD1-3 keep their triangle counts. **Checks:** winding 0
inverted (`fix_winding.py` flipped 0); `run_creature_review.py check` 0 errors, 27 switches (manifest
`r5_wmut_wingtone_20261030`); flat-shading check 0.00 on every material; floor audit 3/3 ok; detached-parts audit
0 detached in any pose (31 components, as before; run before the wing-tone step, which changes no geometry); regression
`mm9_actor_models_build_every_binding` (`--world mm9`) 53 descriptors on 23 models, 0
failed. No in-game run. Sheets (identical cameras, `scripts/texpass_views.py` + `review/texpass_shots.json`,
`scripts/texpass_sheet.py`): `review/texpass_closeups_sheet.png` (tier A: face, face 3/4, body, wing),
`review/texpass_tiers_sheet.png` (tiers A/B/C: 3/4 and face). Before state (GLBs, viewer, textures):
`work/before_texpass/`.

## Rework 2026-10-30 (after the user's review) - current

User review of v1: "1) i dont think its symetrical? 2) the case [face] needs a separate texture 3) the face anatomy
looks bad, check the chin". Before/after sheets: `review/wmut_rework_20261030_head.png` (head at bind pose, front,
3/4, both profiles; tiers A/B/C), `review/wmut_rework_20261030_clips.png` (face in AttackMelee 0.40 s, AttackRanged
0.23 s, Hit, Fidget), `review/wmut_rework_20261030_body.png` (full body front/back, tiers). Diagnosis renders:
`review/v2_diag/` (`stages*.png`: raw Meshy / fit / reduced heads; `mm9head_row.png`: MM9's own head).

1. **Symmetry.** MM9's model is exactly symmetric about x = 0 (median/p90 0.00 %). v1 was not: vertex-to-mirrored-vertex
   median 1.21 %, p90 3.22 %, max 7.93 % of the model size (surface distance 0.84 / 3.18 / 7.88 %): the tail meandered
   up to 4.7 cm off the plane, the front hair strands and four hair bits sat on one side only, the face sat 5.5 cm
   off the plane, and the two wings and legs were fitted differently. `scripts/symmetrize.py` straightens the tail's
   centre line onto the plane, keeps the +x half (closer to the MM9 surface: wing 3.6 vs 3.9 cm, leg 2.2 vs 2.5 cm),
   mirrors it with its UVs (both halves share the kept half's texels; the engine's derivative tangent frame handles the
   mirrored normal map) and moves the mirrored weights to the mirror bones (found by rest position: `Ywing*01` <->
   `Ywing*`, `Bip01 L/R`, `Xhairrit` <-> `Xhairleft`, foot claws); seam vertices (bisect twins within 0.1 mm welded)
   take the average of both sides' weights. MM9's hair (three `Xhair` chains) is symmetric, and so is ours now.
   **After: median 0.00 %, p90 0.00 %, max 0.00 %** (`scripts/measure_symmetry.py`, LOD0 rest pose, both metrics).
2. **Face anatomy - cause.** Not the fit and not the weights: MM9 has no jaw bone (the face is rigid on `Bip01 Head`;
   no clip opens the mouth), and the fit only rotated the head rigidly (3.9 degrees). The cause was Meshy's raw head
   from the full-body Smart Topology, where the face was about 40 px in the master: a small, narrow head 5.5 cm off the
   plane, bump eyes without sockets, a small open mouth hole, and no jaw line (the chin slopes straight into the
   throat). The retexture then painted the lips and the pale throat as one long wedge under the mouth, which read as
   the long pointed chin and the tongue plate. The reduction (0.75 on the head) only added faceting (`stages.png`).
   **Fix (option c):** a Codex HD head turnaround (`references_head/`, brief `CODEX_BRIEF.md`, inputs: MM9 head renders
   `mm9_head_views.png`, head crops of the approved body masters, the MM9 skin; four views, records
   `generation_runs.json`, `selected_views_review.png`), a head-only Smart Topology from `00_three_quarter.png`
   (`requests/head_smart_v1.json`, 5 credits: real eye sockets, a defined jaw line, a short chin, modelled lips, two
   eyes and ten teeth as separate pieces, 17 hair locks), grafted by `scripts/graft_head.py` (`graft_config.json`):
   - the old head shell above a neck plane (normal = MM9 Neck -> Head line, 1 cm below Bip01 Neck), the old hair cap,
     strands and bits removed;
   - the new head kept MM9's orientation (its up on the MM9 head's up, so it looks down as MM9's head does in the bind
     pose; Meshy's thrust-forward neck is cut just under the jaw), scaled to 22 cm chin to crown, made symmetric (the
     camera-side half mirrored), decimated per part with a symmetric collapse (skin 0.7, hair 0.35, teeth 0.5);
   - the hair locks below ear level turned 17 degrees forward (80 % of the head's down-look), so they hang down the back;
   - the body's neck tapered over 6 cm onto the head's neck ring (radius 8.2 -> 6.6 cm, centred on the plane) and the
     two rings bridged;
   - weights: neck skin blends from the body ring's weights to `Bip01 Head` up to the jaw (with a `Bip01 Neck1`
     share), eyes and teeth rigid on the head, hair from the nearest ORIGINAL MM9 head/hair vertex (`Bip01 Head` or an
     `Xhair` joint), smoothed along each lock (a first try with the old Meshy hair's weights mixed `Spine2` into the
     locks: edge stretch p99 3.6 in Hit; now 1.72).
   `Socket_Mouth` now sits 2 cm in front of the teeth. The mouth keeps its modelled snarl in every clip; there is no
   jaw motion to tear (close-ups of AttackMelee 0.40 s and AttackRanged 0.23 s in the clips sheet).
3. **Separate face texture.** I read "the case" as "the face". `scripts/head_uv.py`: own UV layer `HeadUV` for the
   grafted head (skin shell by Smart UV at 75 degrees, hair at 88 degrees, face/eyes/teeth islands 4.5x the hair's
   texel density), exported upright as `texturing/wmut_head_upload.glb`; Meshy head-only retexture from the four head
   views (`requests/head_retexture_v1.json`, 10 credits, backup account). `scripts/compose_head.py`: 1K head set
   (`textures/wmut_head_basecolor.png`, `_normal_1k`, `_metal_rough_1k` with R 255 (no head AO bake), `_region_mask`,
   `_material_classes`: 1 skin, 2 hair, 5 tooth, 6 eye); the head skin luminance matched to the body skin (5th-95th
   percentile) so the head reuses the body's skin and hair ramps (`textures/wmut_ramps_v2.json`: Wmut, Wmut_Wing and
   Wmut_Head share them; eyes and teeth in no channel); the neck seam fades into the body's feathered neck over 3.5 cm
   on the head and 7 cm on the body (`textures/wmut_basecolor_graded_v2.png`, `wmut_region_mask_v2.png`; the old
   texels there held a pale smear beside the old off-centre face). Tiers B/C recolour the face (head sheet).
   The body base colour stays 2K (as Yrsa's approved v2; the doc's 1K body would halve the wing detail).

Meshy credits for the rework: **15** (head Smart Topology 5, head retexture 10; backup account); creature total
**30**. Triangles LOD0/1/2/3 **12,600 / 6,297 / 2,262 / 861** (LOD0: body 1,796, wings 4,068 with 1,978 back faces,
head 6,736 = skin/neck about 3,000, hair about 3,100, eyes and teeth about 600). Flier hover is now +0.5565 (the
rule's lowest living point moved with the mirrored leg and tail). Checks: `run_creature_review.py check` 0 errors, 27
switches; gates `review/gates_v2.json` p1/p99 0.53-0.68 / 1.37-2.06 (v1 0.40-0.69 / 1.43-2.17), extremes 0.05-8.0
on single wing-membrane edges as before, loop seams 0; floor audit `--world mm9 --match "MM9 Winged Mutant*"` 3/3 ok;
winding 0 inverted closed parts; flat-shading check 0.00 flat on every material; `--headless-validate-actor-models`
(`--world mm9`) accepts all three descriptors (it refuses the three MM9 Dagrell descriptors, another project's model).
No in-game run for the rework. `actors.yml` unchanged.

Rework rebuild (after the v1 steps up to `uv_v1.blend`; `head_v1.blend` = `sym_v1` + `head_uv.py 4.5 75 88`, whose
HeadUV the paid retexture was painted on and which `transfer_headuv.py` carries to every rebuild):
`TOKEN=<lease> level_generation/creatures/mm9_wingedmutant_claude/scripts/rebuild_v2.sh [--install]` (graft ->
symmetrize -> HeadUV transfer -> wing back faces -> `dump_head.py` -> `compose_head.py` -> `build_export.py` ->
`build_runtime.sh` (ramps `wmut_ramps_v2.json`) -> `viewer_tiers.py`), then
`python3 scripts/make_viewer_manifest.py r3_wmut_v2_20261030 ...` as below.

## v1 (2026-10-30, superseded where the rework says so)


| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_wingedmutant.glb` (installed; cooked copy in `assets_dev`), skins `wmut_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Winged Mutant A/B/C`, scale 100 (= MM9 size, MONSTERS.txt Scale 1) |
| Triangles LOD0/1/2/3 | rework: 12,600 / 6,297 / 2,262 / 861 (see the rework section); v1: 9,156 / 4,574 / 1,643 / 697 (LOD0: body 6,974 + 2,182 back faces of the open wing membranes) |
| Materials | `Wmut` (body), `Wmut_Wing` (membranes, same maps; kept thin by the shadow shrink) and, since the rework, `Wmut_Head` (1K head set); per tier `_A/_B/_C` |
| Skeleton | the MM9 one, 87 joints, names unchanged (`Bip01 Pelvis/Spine*/Neck*/Head`, hair locks `Xhair*`, wing chains `Yw*`, `Xtail*`, raptor legs `Bip01 L/R Thigh/Calf/Foot` + claws) + `Socket_Mouth` on `Bip01 Head` |
| Clips (30 fps) | Standing 0.53 (StandAir), Walking 0.4 (Flap), Running 0.33 (Flap ×1.25), Fidget 1.2 (FidgetAir1), AttackMelee 0.7 (HAttackAir1), AttackRanged 0.6 (RAttack1, also the cast), Hit 0.6 (WinceAir1), Death 2.0 (dieair1 + fall1 + falldown1), Dead 1.0 |
| Events | melee impact 0.404 s (MM9 `Rattack` in HAttackAir1), ranged/cast impact 0.233 s (MM9 `RangeAttack`), released from `Socket_Mouth` |
| Gait | stride 1.28, run stride 2.99 model units (MM9 walk 125 / fly 350 units/s × 0.0256 per wing beat) |
| Floor | flier rule: hover +0.5565 since the rework (v1 +0.6399) baked in the living clips, eased out over Death; corpse grounded; `floor_audit.py --world mm9` 3/3 ok |
| Meshy credits | **40 / 40** (v1: Smart Topology 5, retexture 10; rework: head Smart Topology 5, head retexture 10; texture pass: body retexture v2 10; backup account) |

## Route

0. **HD masters** (`references_hd/`, Codex via `claude_shared/codex_slot.sh`, two runs): renders of the MM9 model
   with the tier-1 skin (`mm9_views_tier1.png`, `mm9_top_tier1.png`, skin ×4). Brief `CODEX_BRIEF.md` (the chest is
   covered by dark feathers, as on the MM9 skin), records `generation_runs.json`, `selected_views_review.png`.
   1536×1024. Gate: no arms; two bat wings with bony spars spread in the MM9 frontal V; pale-blue female face, black
   swept-back hair; indigo feathered torso and thighs; scaly raptor feet; diamond-tipped tail; sides correct.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/body_smart_v1.json`).
2. **Fit** (`scripts/fit_mm9.py`, `scripts/fit_config.json`): height scale, yaw search (Meshy returned it turned
   −15°), scale+translation ICP, then joint-pivoted segment rotations (head, three segments per wing, two tail,
   thigh/calf/foot) blended by diffused labels. Meshy's wings lie in the MM9 wing plane, so they are kept.
3. **Weights** (`scripts/rig_mm9.py`): barycentric bones of the nearest MM9 surface point (own side), diffused;
   small pieces rigid; 4 influences.
4. **Reduce** (`scripts/reduce_body.py 0.4 0.5 0.75`, head = `Bip01 Head`, `Bip01 Neck1`), **UV**
   (`scripts/uv_export.py`, head islands ×3), **retexture** from 01/03/02/04 (`requests/retexture_v1.json`).
5. **Back faces** (`scripts/add_backfaces.py`, after the UVs): each membrane is one open Meshy sheet (about 160
   boundary edges per wing, `scripts/wing_topology.py`), which the engine culls from behind (first in-game run,
   `../mm9_greaterdemon_claude/review/ingame_isle/m12_harpy_face.png`); open wing components get a copy with the
   same weights and UVs, flipped, 2 mm behind.
6. **Clips** (`scripts/clips_mm9.py` via `scripts/build_export.py`): MM9 key poses as PCHIP curves at 30 fps, loop
   seams closed (StandAir 3.0° before), loops end on an exact frame (rate nudged < 3 %), Death joins blended (5.1°,
   1.1°), Running = Flap ×1.25, Dead = last pose.
7. **Textures** (`scripts/compose.py`, regions from bones: `scripts/dump_regions.py`): 2K base graded once, 1K
   normal, 1K ORM; mask R skin (face, lower legs, feet, tail), G feathers (torso, thighs), B wing membrane, A hair
   (the `Xhair` locks and the dark scalp texels of the head). Ramps: tier A identity; B/C take the chroma of their own
   MM9 skin by luminance percentile, brightness by the MM9 tier/A ratio (`textures/wmut_ramps.json`,
   `review/wmut_texture_classes_tiers.png`).
8. **Runtime** (`scripts/build_runtime.sh`): prepare → LODs → shadow shrink (membranes kept) → `region_variants.py`
   (specular 0, metallic 0) → flier hover → corpse grounding → `fix_winding.py` → winding check 0.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_wingedmutant_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python
for t in 1 2 3; do $V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/WINGEDMUTANT.abc \
  $P/source/tier$t --id wmut$t --texture 0=mm9/extracted/SKINS/SKINS/WINGEDMUTANT$t.dtx --scale 0.0256; done
$B $P/scripts/mm9_rig_source.py $P/source/tier1/wmut1.glb $PWD/$P/work/mm9_wmut_ground.blend 0 0.85
$B $P/scripts/fit_mm9.py $PWD/$P/work/mm9_wmut_ground.blend $P/meshy/body_smart_v1/model_urls_glb.glb $P/scripts/fit_config.json $PWD/$P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_mm9.py $PWD/$P/work/fit_v1.blend $P/scripts/rig_config.json $PWD/$P/work/rig_v1.blend $P/work/rig_v1.json
export HEAD_BONES="Bip01 Head,Bip01 Neck1"
$B $P/scripts/reduce_body.py $PWD/$P/work/rig_v1.blend $PWD/$P/work/reduced_v1.blend $P/work/reduced_v1.json 0.4 0.5 0.75
HEAD_FACTOR=3.0 $B $P/scripts/uv_export.py $PWD/$P/work/reduced_v1.blend $PWD/$P/work/uv_v1.blend $PWD/$P/texturing/wmut_body_upload.glb
# (retexture_v1 was made on this upload)
$B $P/scripts/add_backfaces.py $PWD/$P/work/uv_v1.blend $PWD/$P/work/uv_v2.blend 0.002
$B $P/scripts/dump_regions.py $PWD/$P/work/uv_v1.blend $PWD/$P/work/regions_body.npz Body
$B $P/scripts/dump_regions.py $PWD/$P/source/tier1/wmut1.glb $PWD/$P/work/regions_mm9.npz tailed
$B $P/scripts/bake_ao.py $PWD/$P/work/uv_v1.blend Body $PWD/$P/textures/wmut_ao_2k.png 0.03 2048
python3 $P/scripts/compose.py && python3 level_generation/creatures/claude_shared/grade_basecolor.py --ao $P/textures/wmut_ao_2k.png $P/textures/wmut_basecolor.png && python3 $P/scripts/compose.py
$B $P/scripts/build_export.py $PWD/$P/work/uv_v2.blend $PWD/$P/work/anim_v2.blend $PWD/$P/export/mm9_wingedmutant_lod0.glb $P/work/clips_v2.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
python3 $P/scripts/viewer_tiers.py && (cd $P && python3 scripts/make_viewer_manifest.py r2_wmut_20261030 \
  "wmut_a=Winged Oddity (A)=review/viewer/wmut_a.glb" "wmut_b=Winged Mutant (B)=review/viewer/wmut_b.glb" "wmut_c=Winged Aberration (C)=review/viewer/wmut_c.glb")
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (3 tiers × 9 clips): `tools/run_creature_review.py --project ... check` 0 errors, 27
  switches; shots `review/shots/`, `review/viewer_shots_tiers.png`; Blender renders of every clip
  `review/anim_textured_sheet.png`.
- Gates (`scripts/gates.py`, `review/gates.json`, 60 Hz): loop seams 0; edge ratio p1/p99 0.40–0.69 / 1.43–2.17;
  extremes (0.03–7.6) on single wing-membrane edges where the MM9 flap moves the spar pivots apart (MM9 stretches
  its own membrane the same way).
- Floor audit `--world mm9`: 3/3 ok. Winding: 0 inverted closed parts.
- Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 48 descriptors on 19 models, 0 failed
  (2026-10-30 01:47).
- In game (Ravensford `bootcamp.odm`, minimized, private `--user-data`; tour `review/ingame_tour.yml`, the
  demon's tour `../mm9_greaterdemon_claude/review/ingame_tour.yml` also spawns all three tiers as actors):
  `review/ingame/w01_all.png` (static harpy with closed membranes and readable face next to the demon),
  `review/ingame_sheet.png` (orbits, melee contact, cast release, hit, flap, fall, corpse),
  `../mm9_greaterdemon_claude/review/ingame/a01_spawned.png`–`a05` (tiers A blue, B red, C gold as live actors
  attacking the party). The narrow valley clips some orbit cameras.

## Deviations and open points

- Wing membranes are two-sided by an offset copy (+2,182 triangles at LOD0) rather than a re-modelled closed leaf.
- Winged Aberration's MM9 skin paints silver armour plates on the torso; the ramps recolour our feathers to its
  dark grey-brown plumage and gold skin/wings but do not add a plate pattern (as the Fire Dragonfly's flame marks).
- v1 had no separate head set (×3 face islands in the 2K atlas); the rework adds the 1K head set and a grafted head.
- Unused MM9 clips (TauntAir, HattackAir2, WinceAir2, dieair2/fall2/falldown2, static_model) are not exported; clips
  are in place. MM9's own `Mouth` (Spine2) and `RangeAttack` (a foot claw) sockets are replaced by `Socket_Mouth` at
  the lips.
- MM9 Walking for a flier is its Flap (the body tilted forward in flight); MM9 has no walk.
- User artistic acceptance: accepted 2026-10-30 after the symmetry/head rework ("winged mutant - ok").


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_wingedmutant_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_wingedmutant_reduce_claude/before/`.


**2026-11-04 later: the reduction was rolled back** (installed source = `mm9_wingedmutant_reduce_claude/before/`): the UV audit (`claude_shared/reduction_uv_audit.py`) found reduced faces whose UVs left the painted charts, visible in close-up. A fixed reduction may be reinstalled later; see the ledger.
