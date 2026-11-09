# MM9 Eye family (mm9_eye) — 3D model, 2026-10-30

The floating MM9 beholder eye (`mm9/extracted/MODELS/MODELS/EVILEYETERROR.abc`, 74 joints: one body with a big eye
and a jaw, five eyestalks, eight hanging legs; 18 clips) for the MM9 world: Eye (9228, skin ORBUS1), Orbus (9229,
ORBUS2), Oculus (9230, ORBUS3), descriptors `MM9 Eye A|B|C`. Built on the MM9 rig-reuse route of
`../mm9_dfly_claude/` and `../mm9_lobber_claude/` (new HD Meshy mesh weighted to the original MM9 skeleton, the MM9
clips played with only the listed fixes). Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_eye.glb` (installed; cooked copy in `assets_dev`), skins `eye_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `# >>> mm9_eye_claude` (`bindings/actors_block.yml`), scale 100 (MONSTERS.txt Scale 1) |
| Triangles LOD0/1/2/3 | 6,118 / 3,059 / 1,082 / 349 |
| Texture (2026-10-30 pass) | 2K base colour on xatlas UVs: 55.1 % of the atlas, 214 islands, 1,679 texels per creature size (median). Hide: the approved paint and relief down to the pebble scale + the 4K Meshy paint's finest band; eyes: the texture pass |
| Skeleton | the MM9 one, names unchanged (`Box01` body, `Box02` jaw, legs `Box37...`, stalks `Box07/03/11/19/56...`) + `Socket_Eye` on `Box01` |
| Clips (30 fps) | Standing 2.67 (standair), Walking 2.67 (Fly), Running 1.77 (Fly x1.5), Fidget 2.67 (fidgetair1), AttackMelee 1.0 (HattackAir1), AttackRanged 1.2 (Rattack1, also the cast), Hit 1.37 (winceAir1), Death 2.5 (DieAir1 + fall1 + FallDown1), Dead 1.0 |
| Events | melee impact 0.471 s (MM9 `Rattack`), ranged/cast impact 0.33 s (MM9 `RangeAttack`), released from `Socket_Eye` (the big eye's front; MM9 socket `RangeAttack1`) |
| Floor | flier rule: hover +1.891 m baked in the living clips (lowest point = the HattackAir1 lunge), eased out over Death, corpse grounded; `floor_audit.py --world mm9` ok |
| Meshy credits | **25 / 35** (Smart Topology 5, retexture v1 10, 4K retexture v2 10 for the texture pass; backup account) |

## Route

0. **HD masters** (`references_hd/`, Codex via `claude_shared/codex_slot.sh`, two runs): inputs are renders of the MM9
   model with ORBUS1 (`mm9_views_tier1.png`, five views; `mm9_top_tier1.png`; the 256 skin x4). Brief
   `CODEX_BRIEF.md`; records `generation_runs.json`, `selected_views_review.png`. 1024x1536. Gate: five stalks, eight
   legs, one big eye with a toothed jaw; 03/04 sides correct (slightly oblique), accepted.
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`): body, big eyeball,
   eight separate legs, five stalks and five stalk eyeballs as separate pieces, teeth and brow bumps
   (`work/comps_v1_*.png`).
2. **Fit** (`scripts/fit_eye.py`, chains in `scripts/eye_cfg.py`): core (body, eyeball, small pieces) by scale +
   translation ICP onto the MM9 Box01/jaw vertices; legs and stalks by `fit_chain` (from the Lobber) onto their MM9
   chains, assigned by tip position (exact assignment); stalk eyeballs centred and sized on the MM9 eyeballs
   (`work/fit_v1_sheet.png`).
3. **Weights** (`scripts/rig_body.py`): nearest MM9 vertex label per chain, diffusion with the jaw held; MM9 eyelid
   (`Box70/71`) labels become `Box01` (our socket shell must not blink); the big eyeball rigid on `Box01`; each stalk
   eyeball rigid on its stalk's last bone (MM9 turns the small eyes on it); 4 influences.
4. **Reduce** (`scripts/reduce_body.py 0.35 0.45 0.55`: legs/stalks, pieces, core), **UV** (`uv_export.py eye`,
   core islands x1.8), **retexture** from 01/03/02/04 with our UVs (`requests/retexture_v1.json`).
5. **Clips** (`scripts/clips_mm9.py`, run by `build_export.py`): MM9 keys resampled as PCHIP curves at 30 fps; loop
   seams closed (standair 3.8 degrees, Fly 2.1 before; 0 after, Running too: sped-up loops use whole frames); Death
   stitched (DieAir1 -> fall1 45.7, fall1 -> FallDown1 48.8 degrees, each blended over 0.3 s); Dead = last pose.
6. **Textures** (`scripts/compose.py`): 2K graded base, 1K normal, 1K ORM. Regions R hide, G eyes (the eyeball
   pieces), B red flesh (socket rim, lips), A teeth (identity). MM9 side: eyes = the two painted eye discs of the
   skins, flesh = red hues, the rest hide. Tier A identity; B (blue-black hide, fiery eyes) and C (red scales,
   fiery eyes) take their MM9 skin's chroma by luminance percentile (`review/eye_texture_classes_tiers.png`).
7. **Roots** (`scripts/root_limbs.py`, 2026-10-30, after the UVs): legs stretched into the body shell, the Box06
   eyeball moved onto its stalk, stalk tips weighted to their eyeball bones (see the dated section below).
8. **Runtime** (`scripts/build_runtime.sh [--install]`): prepare -> LODs -> shadow shrink -> `region_variants.py`
   (specular 0, metallic 0) -> flier floor pass -> winding check (0 inverted).

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_eye_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python   # any python with pygltflib
for t in 1 2 3; do $V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/EVILEYETERROR.abc \
  $P/source/tier$t --id orbus$t --texture 0=mm9/extracted/SKINS/SKINS/ORBUS$t.dtx --scale 0.0256; done
$B $P/scripts/mm9_rig_source.py $P/source/tier1/orbus1.glb $P/work/mm9_eye_src.blend 0 0
$B $P/scripts/fit_eye.py $P/work/mm9_eye_src.blend $P/meshy/eye_smart_v1/model_urls_glb.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_body.py $P/work/fit_v1.blend $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.35 0.45 0.55
$B $P/scripts/uv_export.py $P/work/reduced_v1.blend eye $P/work/uv_v1.blend $P/texturing/eye_body_upload.glb
# (retexture_v1 was made on this upload)
$B $P/scripts/dump_uv3d.py $P/work/uv_v1.blend $P/work/uv3d_eye.npz Body
$B $P/scripts/dump_uv3d.py $P/source/tier1/orbus1.glb $P/work/uv3d_mm9_eye.npz d_evileye.mesh:1 d_eyelid.mesh:2 d_eyes.mesh:3 d_eyes01.mesh:4
$B $P/scripts/root_limbs.py $P/work/uv_v1.blend $P/work/roots_v1.blend $P/work/roots_v1.json
$B $P/scripts/bake_ao.py $P/work/roots_v1.blend Body $PWD/$P/textures/eye_ao_2k.png 0.03 2048
python3 $P/scripts/compose.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/eye_ao_2k.png $P/textures/eye_basecolor.png && python3 $P/scripts/compose.py
$B $P/scripts/build_export.py $P/work/roots_v1.blend $P/work/anim_v3.blend $P/export/mm9_eye_lod0.glb $P/work/clips_v3.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 $P/scripts/install_binding.py $P/bindings/actors_block.yml mm9_eye_claude
python3 $P/scripts/viewer_tiers.py && python3 $P/scripts/make_viewer_manifest.py r3_eye_roots_20261030 \
  "eye_a=Eye (Eye A)=$P/review/viewer/eye_a.glb" "eye_b=Orbus (Eye B)=$P/review/viewer/eye_b.glb" "eye_c=Oculus (Eye C)=$P/review/viewer/eye_c.glb"
```

## Checks (2026-10-30)

- Viewer `review/viewer/` (3 tiers x 9 clips): `tools/run_creature_review.py --project ... check` 0 errors (27
  switches); shots `review/viewer_shots_sheet.png`.
- Gates (`scripts/gates.py`, `review/gates.json`): loop seams 0; edge ratio p1/p99 per clip 0.83-0.88 / 1.13-1.78;
  extremes (max 7) are mouth-corner edges when MM9 opens the jaw (`scripts/stretch_where.py`: Box01/Box02 only).
- Floor audit `floor_audit.py --world mm9`: Eye A/B/C ok (28 bindings, 0 problems). Regression
  `mm9_actor_models_build_every_binding` (`--world mm9 --headless-run-regression-suite actors`): 28 descriptors on
  12 models, 0 failed. Winding: 0 inverted closed parts.
- In game (`tools/run_game.sh` minimized, private `--user-data` with `[startup] start_in_main_menu=false`,
  `immortal=true` and the one-shot `menu_input_tour_path`; tours `review/*_tour.yml`, shared with the Magreeb):
  `review/ingame_sheet.png` (Ravensford: static models playing the clips, spawned Eye/Orbus/Oculus actors casting
  at the party), `review/ingame_lindisfarne_sheet.png` (Lindisfarne: spawned Eyes firing their purple missiles at
  the party next to the map's own Magreebs). The fliers hover above the party camera, which a tour cannot pitch,
  so close in-game views of the Eyes were not captured; they are checked in the viewer. Wizard's Lab (the map's own
  Eyes) loaded the party outside its geometry (`review/ingame_maps_sheet.png`).

## Legs rooted in the body (2026-10-30)

User feedback "eye - not connected to the body": the leg roots hung in the air under the body.

- **Cause.** `fit_eye.py` maps each separate Meshy leg piece onto its MM9 chain starting at the chain's root joint, and
  the MM9 leg root joints (Box37, Box29, Box28, Box15, Box33, Box42, Box48, Box52) lie 1.6-12 cm outside our HD body
  shell (MM9's body is fuller underneath). Every leg began at its joint, so the bind pose had gaps of 0.5-10 cm and
  the clips up to 12.7 cm (AttackMelee). Separately, the stalks end at their eyeball bone's head while each eyeball is
  centred on MM9's eyeball vertices: the Box06 eyeball sat 14.3 cm from the Box03 stalk's open tip (3.6 cm gap at
  bind, 4.3 cm in Death). `claude_shared/detached_parts_audit.py` (new) measured 9 detached parts (8 legs, 1 eyeball).
- **Fix** (`scripts/root_limbs.py` on the UV blend, so UVs, retexture and textures stay valid; no Meshy spend):
  each leg's first segment (root cap to J1) is stretched along the root bone's axis until the cap is 3 cm (3 rod
  radii at least) inside the shell; J1 and the rest of the leg do not move, vertices move only along the axis (the
  rod keeps its section and UVs; first-segment stretch 1.08-1.29, `work/roots_v1.json`). The new root's weights blend
  from the leg's own to the body's weights at the entry point (barycentric; the front legs enter the jaw's underside,
  so they take its Box02 share), fully the body's from just inside the shell. The Box06 eyeball moves rigidly 9.6 cm
  onto its stalk tip (3 cm inside it, no rotation, same bone and motion); every stalk vertex within 3.5 cm of its
  eyeball blends to the eyeball bone. AO re-baked on the new geometry (contact shadow at the leg roots; textures
  change in about 1 % of texels, region mask and normal map unchanged; ramps differ only in the last digits).
- **Checks.** Detached-parts audit at 48 fps over every clip: 0 detached (was 9), legs rooted in every pose.
  Triangles unchanged (6,118 LOD0; LODs 3,059 / 1,082 / 349). Hover unchanged (+1.891 m). Winding 0 inverted;
  `run_creature_review.py check` 27 switches, 0 errors; `floor_audit.py --world mm9 --match 'MM9 Eye*'` 3 ok;
  flat-shading 0.00; regression `mm9_actor_models_build_every_binding` passed (the suite's 13 failures that day were
  MM6/MM8 cases from other in-progress work). Sheets: `review/rootfix_bind_before_after.png` (underside, front, 3/4, side close at bind),
  `review/rootfix_worstframes_before_after.png` (the old worst frames AttackMelee 0.167 s, Hit 0.767 s, close),
  `review/rootfix_clips_before_after.png` (widest leg spread per clip: AttackMelee 0.229, Hit 0.625/0.767,
  Walking 1.875, Death 1.5, Dead). The pre-fix export and textures are kept in `work/before_rootfix/`.

## Texture quality pass (2026-10-30)

`../claude_shared/TEXTURE_QUALITY_PASS.md`, brief `../claude_shared/MM9_TEXTURE_PASS_BRIEF.md`. Mesh, weights and clips are
unchanged: LOD0 triangles identical (0.0 m), skin weights identical at all 3,219 positions (max delta 0.0), clip keys identical
(delta 0), hover +1.8913, LODs 6,118 / 3,059 / 1,082 / 349. The leg root fix survives: the pass runs on `work/roots_v1.blend`,
its last vertex move. **10 Meshy credits** (4K retexture v2, backup account); creature total **25 / 35**.

- **UVs** (`scripts/uv_atlas_v2.py` on `work/roots_v1.blend`): xatlas charts, core x1.8 as before -> `work/uv_v2.blend`,
  upload `texturing/eye_body_upload_v2.glb`. `scripts/uv_gates.py`: 0 texels painted twice (239 before), 0 zero-area
  triangles. **Never re-run it: the paint is bound to this layout.**
- **Retexture v2** (`requests/retexture_v2.json`): same four HD masters, `meshy-7`, 4K, our UVs. `compose.py` downsamples
  each map once. Grade gentle (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`), AO re-baked.
- **Eye drift.** The fresh paint drew a grey fibred iris and veined sclera where the approved eye has a black disc and a ribbed
  cream ring of the same size and place, so tier A's eye went pale and the pupils shrank on every tier.
  `scripts/approved_on_new.py` resamples the approved colours onto the new layout (same mesh, same triangles);
  `scripts/match_approved.py` takes the approved low frequencies on the eyeball pieces and multiplies in the new paint's fine
  luminance (ratio softened ** 0.75, clipped 0.65-1.45), so the design stays, black stays black, and the fibres and veins are
  new. Tiers B and C still go fiery through the eye ramps, which read this luminance.
- **Tone drift.** Hide 7 % darker, mouth flesh 26 % darker, hide luminance sd 45.6 against 38.1: `match_approved.py` adds
  blur(approved - new) (sigma 20 texels, per region) and quantile-matches the hide's luminance to the approved one.
- **Copper patches on the backs of tiers B and C.** Cause: `mouth` is picked by hue, and reddish patches of the new paint took
  the mouth ramp (10 % of the approved hide). `compose.py` now limits `mouth` to within 4 texels of the approved mouth class.

| Measure (`texture_quality.py`, LOD0) | Before | After |
|---|---|---|
| Atlas use (2K) | 44.3 % | **55.1 %** |
| Equivalent fully used square | 1,364 px | 1,521 px |
| Texels per creature size p10 / p50 / p90 | 1,328 / 1,557 / 2,720 | **1,564 / 1,679 / 2,946** (+8 % median) |
| Density spread p90/p10 (core x1.8 by design) | 2.05 | 1.88 |
| Islands / surface on fragments | 448 / 5.5 % | 214 / **0.8 %** |
| UV stretch p90 (rest pose) | 1.45 | 1.08 |
| Fine detail, high-pass RMS inside the islands | 7.3 | 17.7 (x2.43) |
| Blotch band 4-16 px | 18.9 | 14.8 (x0.78) |
| Tier-A ramp error hide / eyes / mouth / teeth | 5.1 / 4.1 / 2.6 / 6.2 | 5.6 / 5.3 / 4.9 / 7.4 |
| Meshy source | 2K | 4K on 55 % (3,041 px equivalent) |

**Checks.** Winding 0 inverted; `run_creature_review.py check` 0 console errors, no failed switches (revision
`r4_eye_texpass_20261030`); floor audit 3/3 ok; gates loop seams 0, largest edge ratio unchanged (4.88 in AttackMelee);
flat-shading 0.00; `detached_parts_audit.py` 0 detached in any pose (38 components), so the leg roots stay rooted; regression `mm9_actor_models_build_every_binding` (`--world mm9`) passed, 65 descriptors on 31 models, 0 failed.

**Accepted from review-viewer shots:** `review/texpass_viewer_sheet.png` (tiers A/B/C, before | after, identical cameras;
shots in `review/texpass_viewer/`). The viewer's presets frame a standing humanoid, so `scripts/texpass_shots.py` passes fixed
cameras to the same `viewer_shots.mjs`. Density heatmaps on one scale (1,557 texels = green):
`review/texpass_20261030/heat_{before,after}_density.png`. No in-game run. Before state: `work/before_texpass/`.

**Known drift:** the hide read finer and smoother than the approved pebbled skin (fixed below, "Pebbled hide restored"). Eyeball
detail inside the black disc stays soft (the approved low frequencies carry it).

Rebuild from the existing paint, never the UV script:
```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_eye_claude
# one-time, already done, bound to the Meshy paint:
#   $B $P/scripts/uv_atlas_v2.py $P/work/roots_v1.blend $P/work/uv_v2.blend $P/texturing/eye_body_upload_v2.glb $P/work/uv_v2.json
#   python3 tools/creature_meshy.py --project $P --token $T submit --job eye_retexture_v2 --kind retexture \
#      --request requests/retexture_v2.json --credits 10      # then poll / download
$B $P/scripts/dump_uv3d.py $P/work/uv_v2.blend $P/work/uv3d_eye_v2.npz Body
$B $P/scripts/bake_ao.py $P/work/uv_v2.blend Body $PWD/$P/textures/eye_ao_2k.png 0.03 2048
python3 $P/scripts/approved_on_new.py eye work/uv3d_eye.npz work/uv3d_eye_v2.npz
python3 $P/scripts/compose.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/eye_ao_2k.png \
  --fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/eye_basecolor.png
rm $P/textures/eye_basecolor_graded_meshy.png   # match_approved.py keeps the fresh grade under this name
TOKEN=$T $P/scripts/rebuild_texpass.sh --install     # match_approved, compose, export, runtime, viewer tiers, shots
```

## Pebbled hide restored (2026-10-30)

The texture pass raised the atlas to 55 % but the hide lost the approved pebbles: fine stipple and long thin veins replaced the
rounded cells, and the relief went with them. **0 Meshy credits.** Mesh, rig and clips are byte-identical to the previous install
(all attributes of the 8 meshes, inverse bind matrices, all 1,998 clip samplers); the UV layout is untouched (55.1 %, spread 1.88,
fragments 0.8 %, stretch 1.08, same as the table above). Eye and teeth pieces are identical in base colour, normal, ORM, both mask
channels and all tier colours (0 of 496,866 base-colour texels changed, tier difference 0).

- **Where the pebbles are.** Only in the old paint. Luminance band energy of the hide, all on the new layout, and the correlation
  between the approved and the new paint: tone matching could not have brought them back, it keeps the new paint's detail.

| Band, texels (DoG sigma) | 0.7-1.4 | 1.4-2.8 | 2.8-5.6 | 5.6-11 | 11-22 | 22-44 |
|---|---|---|---|---|---|---|
| Approved | 3.69 | 8.05 | 10.96 | 9.11 | 6.49 | 5.55 |
| Texture pass (smooth) | 10.23 | 12.11 | 8.35 | 4.57 | 3.31 | 4.27 |
| **Restored** | 4.10 | 7.96 | 11.12 | 9.47 | 6.73 | 5.61 |
| Approved vs new paint, correlation | 0.02 | 0.05 | 0.10 | 0.18 | 0.40 | 0.54 |

- **Colour** (`scripts/restore_pebbles.py`, after `match_approved.py`, before `compose.py`): the approved base colour, resampled through
  the old UVs (`approved_on_new.py`), supplies everything down to sigma 0.5 texels, scaled by island density (about 1 on the core,
  which is twice as dense), plus 0.5 x the 4K paint's luminance above that, tinted by the approved colour; approved band below
  sigma 11 x 1.06, because resampling softened it a little. Inside each UV island, like the Basilisk's `match_tone.py`. The finest
  band therefore stays the 4K paint's (4.10 against 3.69), a small sharpness gain only: the fine detail of the texture pass is
  deliberately given up (10.23 -> 4.10), because that was the stipple.
- **Relief.** Colour alone looked flat and streaky: the 4K normal still drew stipple and veins. The approved normal map moves with
  the colour (`work/normal_pebbled_1k.png`, applied by `compose.py` outside the eye and teeth masks), below sigma 0.35, plus 0.5 x the
  4K normal above it. A tangent-space normal has to be turned with each chart. **Meshy's normal Y points down the image** (XY follow
  the paint's gradient at r -0.976 in image axes), so the rotation must be taken in image axes: in Blender's v-up frame the angle
  inverts and xatlas's 90 degree charts flip their relief (r -0.18, one chart +0.70). Corrected: r -0.955, every chart the same sign.
- **Regions from the final colours.** `compose.py` picks `mouth` from the final graded colours and no longer reads the approved class
  map. A plain threshold spread 227 pieces of the mouth ramp over the hide (pink on tier B), since hide hue sits next to the 18
  degree limit, so it uses hysteresis: seeds of at least 300 texels above 0.7, grown to 0.5 (7 pieces). `work/approved_classes_on_new.png`
  now only scores the result.
- **Eye and teeth ramps pinned** (`textures/eye_kept_ramps.json`, read by `compose.py`): their texels did not change, but a refit reads
  the gutter fringe and moved the tier colours (p99 8.5 levels).

| Tier colours at the same surface points | Approved | Texture pass | Restored |
|---|---|---|---|
| Tier A hide mean / sd | 147.1, 90.2, 50.0 / 36.2 | 144.5, 89.3, 48.7 / 36.4 | 146.6, 89.5, 50.1 / 36.8 |
| Tier B hide mean / sd | 28.1, 32.0, 49.2 / 14.1 | 27.8, 31.6, 48.6 / 14.2 | 27.7, 31.7, 48.8 / 14.3 |
| Tier C hide mean / sd | 102.5, 0.6, 0.2 / 8.2 | 101.7, 0.6, 0.2 / 8.8 | 101.4, 0.7, 0.1 / 8.0 |
| Tier-A ramp error hide / mouth | 5.1 / 2.6 | 5.6 / 4.9 | 5.15 / 2.54 |

**Known difference:** the few small pink flecks of the approved tier B top are gone, and the mouth region is about 18 % smaller than the
approved class map (18,693 against 22,671 texels at 1K, 90 % of its solid flesh covered): the hide stays clean, at the cost of
those flecks.

**Checks.** Winding 0 inverted; `check_viewer.mjs` and `run_creature_review.py check` 27 switches, 0 console errors, 0 failed (revision
`r5_eye_pebbles_20261030`); flat-shading 0.00; texture quality as above; regression `mm9_actor_models_build_every_binding` (`--world mm9`) passed, 66 descriptors on 32 models, 0 failed.

**Accepted from review-viewer shots:** `review/pebble_before_after_sheet.png` (tiers A/B/C x back, side, top, jaw, stalk; columns
approved | texture pass | restored, identical cameras; `scripts/pebble_shots.py`, `scripts/pebble_sheet.py`, shots in
`review/pebble_viewer/`, `review/viewer_approved` and `review/viewer_texpass` are symlinks to the backups). No in-game run. Before state:
`work/before_pebbles/`.

Rebuild: as the texture pass above. `scripts/rebuild_texpass.sh` now runs `restore_pebbles.py` after `match_approved.py`
and shoots `pebble_shots.py restored`; its defaults are the accepted values.

## Deviations and open points

- The MM9 eyelid (Box70) does not blink on our model: its vertices are relabelled to the body, because the HD socket
  rim is part of the body shell.
- The approved eye has a large black pupil and a brown ring instead of MM9's blue-grey iris (the texture pass keeps that
  design on its new paint, see above); tier B/C turn it into the MM9 fiery eye through the eye ramps.
- Standing floats 0.43 m above the floor (the flier hover is set by the lowest living point, the HattackAir1 lunge).
- Unused MM9 clips (Flap, HattackAir2, searchair, tauntair, winceAir2, the DieAir2 set, static_model1) are not
  exported. MM9 `lunge` events are not reproduced (clips in place).
- User artistic acceptance: accepted 2026-10-30 after the leg root fix ("eye - ok").
