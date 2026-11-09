# MM9 Basilisk family (mm9_basilisk) — 3D model, 2026-10-30

The six-legged frilled MM9 lizard (`mm9/extracted/MODELS/MODELS/BASILISK.abc`, 107 joints: six legs with a thumb and
four two-bone toes each, tail, neck frill, jaw) for the MM9 world: Basilisk (150), Fibrase Basilisk (151), King
Basilisk (152) (`tools/mm9_import_discovery/mm9_monster_families.yml`). Built on the MM9 rig-reuse route of
`../mm9_dfly_claude/` and `../mm9_lobber_claude/` (new HD Meshy mesh weighted to the original MM9 skeleton, the MM9
clips played with only the listed fixes). Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_basilisk.glb` (installed; cooked copy in `assets_dev`), skins `basilisk_a`, `basilisk_c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`: MM9 Basilisk A and B → `basilisk_a`, C → `basilisk_c`; scale 100 (MONSTERS.txt `Scale` 1) |
| Triangles LOD0/1/2/3 | 8,132 / 4,065 / 1,441 / 462 (six legs with 30 toes and claws, frill plates, teeth) |
| Clips (30 fps) | Standing 2.0 (Stand), Walking 1.3 (Walk), Running 0.6 (Run), Fidget 1.5 (Fidget1), AttackMelee 1.2 (HAttack1), AttackRanged 2.5 (RAttack1, also the cast), Hit 1.2 (Wince1), Death 2.0 (Die1: rears up, flips onto its back), Dead 1.0 |
| Events | melee impact 0.666 s (MM9 `bite`), ranged/cast impact 0.694 s (MM9 `rangeattack`), released from `Socket_Mouth` (on `Xhead`) |
| Gait | stride 0.47 (walk), 0.65 (run): fore-aft travel of the wrists (`scripts/gait_measure.py`) |
| Texture (2026-10-30 pass) | 2K base colour: 4K Meshy detail on the approved colours, xatlas UVs: 57.6 % of the atlas, 255 islands, 1,452 texels per creature size (median) |
| Meshy credits | **25 / 35** (Smart Topology 5, retexture v1 10, 4K retexture v2 10 for the texture pass; backup account) |

## Decisions

- **Tiers.** MONSTERS.txt gives the Basilisk and the Fibrase Basilisk the same skin (`basilisk.dtx`), so both bind
  `basilisk_a` (the HD look, identity ramps); the King Basilisk (`basilisk2.dtx`: blue-black body, blue head) is
  `basilisk_c`. Two regions (hue families on our texture): red (frill, mouth) and scales (everything else).
- **Death** is MM9 Die1 as authored (the lizard rears up and turns onto its back); the floor pass grounds the corpse.

## Route

0. **HD masters** (`references_hd/`, Codex): renders of the MM9 model with its tier-1 skin (`mm9_views_tier1.png`,
   five views; `mm9_top_tier1.png`; skin ×4), brief `CODEX_BRIEF.md`. 00 (run 1) accepted with a frill of two plates
   per side and three crown horns. Run 2 was cut off by "model at capacity" after 01/03/04 (recovered from the Codex
   session's images); the one corrective back view (run 3) is still elevated (`selected_views_review.png`); it was
   used for the retexture anyway (`02_back_v1_elevated.png` is the first attempt).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/basilisk_smart_v1.json`): one-piece body with
   all six legs and the frill, separate teeth/eyes/claws (`work/meshy_sheet.png`).
2. **Rig source** (`scripts/mm9_rig_source.py`, lift 0.5807: the MM9 feet on the floor), **global fit**
   (`scripts/align.py`: similarity ICP, yaw only), **part fit** (`scripts/fit_basilisk.py`): y-map of the body axis
   through the leg junctions, head translation ICP, the six legs posed onto the MM9 leg chains by segment skinning
   (feet only translate, so they stay flat, soles on the MM9 floor), tail droop matched. Overlays
   `work/fit_sheet.png`, solid `work/fitsolid_zoom.png`.
3. **Weights** (`scripts/rig_basilisk.py`): nearest MM9 vertex label per chain (legs only from their own bones), toes
   by connectivity (Meshy toe tips matched to the five MM9 toes by direction around the foot; distal/proximal toe
   bone by distance from the tip), diffusion with jaw and toe labels held, small pieces rigid, 4 influences.
4. **Reduce** (`scripts/reduce_body.py 0.5 0.5 0.7`), **UV** (`scripts/uv_export.py`: Smart UV, head islands ×2),
   **retexture** from 01/03/02/04 with our UVs (`requests/basilisk_retexture_v1.json`).
5. **Clips** (`scripts/clips_mm9.py` via `scripts/build_export.py`): MM9 key poses as PCHIP curves at 30 fps, loop
   seams closed (Walk 7.9°, Run 13.8° on toe bones before), the frames span each source duration exactly.
6. **Textures** (`scripts/compose.py basilisk`): 2K graded base (`grade_basecolor.py`, AO `bake_ao.py`), 1K normal,
   1K ORM; region mask + ramps (`textures/basilisk_ramps.json`, `review/basilisk_texture_classes_tiers.png`).
7. **Runtime** (`scripts/build_runtime.sh basilisk`): prepare → LODs → shadow shrink → `region_variants.py`
   (specular 0, metallic 0) → floor pass → winding check (0 inverted). Install `tools/install_model.py --world mm9`;
   binding by `scripts/bind_actors.py work/binding.yml ...` under the shared `mm9_actors_yml.lock`.

## Rebuild

The current maps come from the texture pass: replace the uv_export/retexture_v1/compose lines with the block at the end
of "Texture quality pass" below. The v1 steps here are what `work/before_texpass/` was built from.

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_basilisk_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
C=tools/mm9_import_discovery/convert_abc_model.py; M=mm9/extracted/MODELS/MODELS; S=mm9/extracted/SKINS/SKINS
$V $C $M/BASILISK.abc $P/source/basilisk1 --id basilisk1 --texture 0=$S/BASILISK.dtx --scale 0.0256
$V $C $M/BASILISK.abc $P/source/basilisk2 --id basilisk2 --texture 0=$S/BASILISK2.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/basilisk1/basilisk1.glb $P/work/mm9_basilisk_ground.blend 0 0.5807
$B $P/scripts/align.py $P/work/mm9_basilisk_ground.blend $P/meshy/basilisk_smart_v1/model_urls_glb.glb $P/work/align_v1.blend $P/work/align al
$B $P/scripts/fit_basilisk.py $P/work/align_v1.blend $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_basilisk.py $P/work/fit_v1.blend $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.5 0.5 0.7
$B $P/scripts/uv_export.py $P/work/reduced_v1.blend basilisk $P/work/uv_v1.blend $P/texturing/basilisk_body_upload.glb
# (retexture_v1 was made on this upload)
$B $P/scripts/dump_uv3d.py $P/work/uv_v1.blend $P/work/uv3d_basilisk.npz Body
$B $P/scripts/dump_uv3d.py $P/source/basilisk1/basilisk1.glb $P/work/uv3d_mm9_basilisk.npz body.mesh:1 leg.mesh:1 leg01.mesh:1 leg02.mesh:1 leg03.mesh:1 leg04.mesh:1 leg05.mesh:1
$B $P/scripts/bake_ao.py $P/work/uv_v1.blend Body $PWD/$P/textures/basilisk_ao_2k.png 0.03 2048
python3 $P/scripts/compose.py basilisk && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/basilisk_ao_2k.png $P/textures/basilisk_basecolor.png && python3 $P/scripts/compose.py basilisk
$B $P/scripts/build_export.py $P/work/uv_v1.blend basilisk $P/work/anim_v1.blend $P/export/mm9_basilisk_lod0.glb $P/work/clips_v1.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh basilisk --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 $P/scripts/bind_actors.py $P/work/binding.yml "MM9 Basilisk A" "MM9 Basilisk B" "MM9 Basilisk C"
python3 $P/scripts/viewer_tiers.py basilisk && python3 $P/scripts/make_viewer_manifest.py r1_basilisk_20261030 \
  "basilisk_a=Basilisk / Fibrase Basilisk (A, B)=$P/review/viewer/basilisk_a.glb" "basilisk_c=King Basilisk (C)=$P/review/viewer/basilisk_c.glb"
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (2 tiers × 9 clips, three.js from `../mm6_goblin/review_20261006/vendor/`):
  `tools/run_creature_review.py check` 0 console errors, 18 switches, 0 failed; shots `review/shots/`,
  `review/viewer_shots_sheet.png`.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 per clip 0.63–0.75 / 1.2–2.3
  (in the Lobber's range); extremes (min 0.015, max 6.5) on small toe and frill edges when MM9 curls the toes.
- Floor audit `floor_audit.py --world mm9`: 40/40 bindings ok. Regression `mm9_actor_models_build_every_binding`
  (`--world mm9`): 40 descriptors on 16 models, 0 failed. Winding: 0 inverted closed parts.
- In game (Ravensford `bootcamp.odm`, `tools/run_game.sh` minimized, private `--user-data` folder whose settings.ini
  has `start_map_file=bootcamp.odm`, `immortal=true` and the one-shot `menu_input_tour_path`):
  `review/ingame_basilisk_sheet.png` (tour `review/ingame_tour2.yml`: static models standing, walking, attacking,
  running, hit, Death onto the back and the corpse on the slope; spawned Fibrase and King Basilisk actors attacking
  the party, the King's death and loot satchel) and `review/ingame_sheet.png` (tour `review/ingame_tour.yml`, shared
  with the Terror; its static basilisk stood inside the rock wall, so only the Terror models show there).

## Deviations and open points

- 02_back master elevated (Codex capacity error, one correction used); the retexture still reads correctly on the back.
- Unused MM9 clips (Aware, Fidget2, Search, Taunt, Wince2, Die2, static_model1) are not exported; the MM9 `lunge`
  and Die1 `Velocity` events are not reproduced (clips are in place).
- Meshy's legs are tucked closer to the body than MM9's sprawl: the upper segments are stretched up to 2.5× onto the
  MM9 chains (`work/fit_v1.json` `seg_stretch`). Toe azimuth matching cost 30–65° per toe on average.
- The Fibrase Basilisk looks identical to the Basilisk (as in MM9: same skin).
- User artistic acceptance: accepted 2026-10-30 ("basilisk - ok").

## Texture quality pass (2026-10-30)

User: approved model and animations, "the magreeb texture treatment". Recipe `../claude_shared/TEXTURE_QUALITY_PASS.md`.
Mesh, rig, weights, clips, sockets, binding and the approved colours are unchanged; UVs and texture maps changed.
**10 Meshy credits** (retexture v2, backup account), creature total **25 / 35**. Before state: `work/before_texpass/`.

| Measure (`texture_quality.py`, LOD0) | Before | After |
|---|---|---|
| Atlas use (2K) | 35.1 % | **57.6 %** |
| Equivalent fully used square | 1,213 px | **1,554 px** |
| Texels per creature size p10 / p50 / p90 | 1,058 / 1,182 / 2,200 | **1,401 / 1,452 / 2,873** (body +23 %, head +31 % linear) |
| Density spread p90/p10 | 2.08 | 2.05 (the head's deliberate x2; body p50/p10 1.04) |
| Islands / surface on fragments | 895 / 7.6 % | **255 / 0.3 %** |
| UV stretch p90 (rest pose) | 1.46 | **1.17** |
| Zero-area UV triangles | - | 0 |
| Meshy source | 2K on 36 % | 4K on 57.6 % (3,107 px equivalent) |

**Sharpness in the review viewer** (same cameras, luminance RMS of the 1-3 px band on the creature, before -> after):
tier A leg x1.35, flank x1.28, frill x1.30, back x1.16, head x1.10-1.16; tier C the same within 0.08. The band in the
atlas itself stays about equal (RMS 22.3 -> 21.7) on 23 % more texels per surface, so it sits on a finer surface scale.

**Keeping the look: the main work of this pass.** The gentle-graded 4K paint alone was a different creature: pale,
cracked-mud scales with black outlines (legs luminance sd 42 -> 64, p5 33 -> 6), amber dotted frill instead of the
red-orange rays, red back patches and the red snout mostly gone (`work/texpass_iterations/g1_*`). Tone curves alone
fixed the means, not the pattern (`m8_*`). `scripts/match_tone.py` does, in order:
1. **Tone:** per region, one curve per sRGB channel maps the new distribution onto the approved one, at the same
   area-weighted surface points through each layout's UVs (1.5 M points; both layouts share the triangle order).
2. **Bands:** the approved graded paint is resampled onto the new layout, and each UV island takes the approved colour
   below a mask-normalised Gaussian (scales 4 texels, red 1.8; scaled by the island's density so the head gets the same
   surface scale) plus the new paint's *luminance* detail above it, tinted by the approved colour, x0.8 (red x0.7).
   Per island so colour never bleeds across the atlas. RGB detail left olive horn tips and yellow frill specks.
   The red band is narrow because the frill's rays are finer than the mottling and belong to the approved look; at 8
   texels the rays turned into a dotted mesh. Palette and pattern are the approved paint's, sharpness the 4K paint's.
3. **Mask on the shipped colours** (`compose.py`): the ramps replace colour by luminance per region, so hue classes from
   the raw paint sent amber specks and an olive tip through the wrong ramp. Classes now use the matched paint; inside
   mostly red islands a texel the raw paint saw as red stays red. This also removes the approved frill's pale fragment
   blotches, the one deliberate difference from the approved paint (they were the old layout's defect).

Zone means and luminance sd, approved -> final (`scripts/paint_compare.py`, same surface points, tier textures as shown):

| Zone (share of surface) | Tier A mean | A lum sd | Tier C mean | C lum sd |
|---|---|---|---|---|
| Frill (10.7 %) | 86/44/23 -> 86/44/22 | 43.4 -> 41.3 | 54/32/35 -> 54/32/37 | 33.5 -> 31.6 |
| Mouth, head red (9.0 %) | 98/50/27 -> 98/50/25 | 49.5 -> 44.9 | 61/37/40 -> 62/36/41 | 37.4 -> 34.1 |
| Back and flank (31.7 %) | 131/112/55 -> 130/112/53 | 58.0 -> 57.8 | 76/72/77 -> 75/71/79 | 39.5 -> 39.4 |
| Legs and tail (40.6 %) | 117/100/47 -> 117/100/46 | 42.2 -> 45.6 | 66/63/72 -> 66/63/74 | 28.9 -> 31.2 |
| Head scales (4.5 %) | 110/93/43 -> 111/92/42 | 42.9 -> 43.5 | 63/59/68 -> 63/58/70 | 29.7 -> 30.1 |

Ramp errors, tier A / C: red 10.5 / 0.5, scales 3.0 / 0.3 levels (approved 10.5 / 0.5, 4.6 / 0.35). In viewer shots the
creature's mean colour stays within 2 levels per shot and luminance sd within 2 on both tiers.

**Remaining differences** (`review/texpass_before_after_sheet.png`): the scales read as a fine dark net where the
approved paint had soft blobs, which can look a little paler although the measured tone is the same; faint dark bars on
the palate, only seen with the mouth wide open; the frill's rays are a little dotted up close.

**Checks.** Clips: every animation key identical to the approved GLB (worst difference 0), same nodes and transforms, same
8,132 triangles. Winding 0 inverted; flat-shading check 0.00; `detached_parts_audit.py` 0 detached; viewer `check`
0 console errors, 18 switches, 0 failed; floor audit the three Basilisk bindings ok (`--world mm9`: 61 bindings, 1
problem, not a Basilisk); regression `mm9_actor_models_build_every_binding` (`--world mm9`) 65 descriptors on 31 models,
0 failed. The rest of the `actors` suite: passed 179, failed 13, all named MM6/MM8 tier or native-map tests with no
mention of the Basilisk (`work/regression.log`); not investigated, and this pass changed no engine code or other model.
Normal map stronger than v1 (xy RMS 0.09 -> 0.12), roughness about the same.
Accepted from review-viewer shots: `review/texpass_before_after_sheet.png` (head, mouth, frill, back, flank, legs, tiers
A and C), `review/texpass_body_sheet.png` (full body, tail), `review/texpass_density_heatmap_sheet.png` (UV space, one
scale). Cameras: `scripts/texpass_shots.sh`; the viewer's focus presets are scaled to the Basilisk in `review/viewer/review.js`
(arms front leg, shoulders frill, skirt flank, feet hind leg). No in-game run.

**Rebuild of the maps** (after `reduced_v1` / `uv_v1`; never re-run `uv_atlas_v2.py`: the paint is bound to its layout):

```sh
$B $P/scripts/uv_atlas_v2.py $P/work/uv_v1.blend $P/work/uv_v2.blend $P/texturing/basilisk_body_upload_v2.glb $P/work/uv_v2.json
python3 tools/creature_meshy.py --project $P --token $T submit --job basilisk_retexture_v2 --kind retexture \
  --request requests/basilisk_retexture_v2.json --credits 10      # then poll / download
$B $P/scripts/dump_uv3d.py $P/work/uv_v2.blend $P/work/uv3d_basilisk_v2.npz Body
$B $P/scripts/bake_ao.py $P/work/uv_v2.blend Body $PWD/$P/textures/basilisk_ao_2k.png 0.03 2048
# with no textures/basilisk_basecolor_graded.png present:
python3 $P/scripts/compose.py basilisk && cp $P/textures/basilisk_region_mask.png $P/work/region_mask_paint.png
python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/basilisk_ao_2k.png --fine 1.0 --local 0.3 --ao-strength 0.5 \
  --contrast 1.06 --saturation 1.15 $P/textures/basilisk_basecolor.png
mv $P/textures/basilisk_basecolor_graded.png $P/textures/basilisk_basecolor_gentle.png
python3 $P/scripts/match_tone.py $P/textures/basilisk_basecolor_gentle.png $P/textures/basilisk_basecolor_graded.png
$P/scripts/texpass_rebuild.sh $T --install       # compose, export, runtime, install, viewer tiers and manifest
```
`match_tone.py` reads the approved paint and mask from `work/before_texpass/textures/` and `work/uv3d_basilisk.npz`: keep them.
