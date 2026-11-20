# MM8 Water Elemental · m500

Claude-playbook production for the solid fish-serpent Water Elemental, with a grounded lower body, webbed hands,
a separate two-palm cast and the native backward-arched corpse. Technical delivery is complete; user artistic
acceptance is not recorded.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m500_claude/review/viewer/)
· [Packed editable master](export/mm8_m500.blend)
· [Runtime source GLB](export/mm8_m500.glb)
· [Native motion study](MOTION_STUDY.md)
· [Progress and generation receipts](creature_3d_progress.json)

## Asset and source interpretation

The native creature has continuous scales, ventral scutes, fish lips, gills, yellow eyes and medial fins; it is not
an animated water shell. The non-humanoid rig route therefore uses a solid Meshy body. Original sprites and gameplay
tables remain unchanged. The five generated body views and four close head views are retained with prompts and hashes.
The continuous flat ventral chest and five webbed digits are reconstruction choices, not recovered hidden anatomy.

The selected mesh combines the first geometry job's long body with the second job's single-crest head. The caudal
fan was turned into the sagittal plane, the neck joined, and a floating fragment removed. The fitted rig has **79 bones**:
26 tail segments, seven spine controls, neck/head/jaw, articulated arms, five three-joint digits per hand and fin controls.
Weights use at most four influences. No equipment, humanoid auto-rig or paid animation was needed.

The final colour LODs contain **10,530 / 5,263 / 1,893 / 630 triangles**, with matching shadow meshes. The shared
runtime reducer uses stronger far reductions than the general 50% guideline. The head, hands and important fins
were protected during the initial bent-pose reduction. Runtime merges body/head into one material primitive per LOD.

Body and head each have a separate 1K base colour, normal, material-response and region map. Runtime combines each
pair into a padded **2080×1024** atlas; all three tiers share four images. MR.R carries the per-texel specular mask,
MR.G roughness and MR.B zero metallic. A gentle baked-AO grade is in base colour. Meshy's downward-Y normal maps
were converted once. The runtime uses `openyamm_specular=1` and its mask; Blender's unsupported KHR specular extension
is removed from the game export. Viewer copies bake palette ramps for three.js and are not installed as tier textures.

Native palettes are **501 / 502 / 501**: A/C share blue colours, B is greener. Scale, pearl ventral and muted fin regions
are graded from native pixel samples while preserving generated surface detail. Golden eyes keep their paint.
Meshy consumed **30 / 100 credits**: two geometry jobs at 5 each, body/head retexture at 10 each. All jobs finished.

## Motion and integration

| Clip | Seconds | Behaviour |
|---|---:|---|
| Standing | 3.000 | Supported idle with restrained breathing and fin motion |
| Walk | 1.125 | Travelling lower-body wave |
| Running | 0.750 | Stronger, faster tail wave |
| Fidget | 0.750 | Small head, torso and hand shifts |
| Attack | 1.375 | Native arm flare, forward strike, recovery |
| Cast | 1.375 | Anticipation, both palms forward, recovery |
| Hit | 0.750 | Backward recoil |
| Death | 0.625 | Backward arch with the medial sail folded |
| Dead | 1.000 | Held death endpoint |

Motion is locally authored smooth 3D interpretation. The owned `UnarmedCastDualAttack2` clip supplied the caster
gesture study at its actual one-second duration, not a humanoid retarget. Attack/Cast release at **0.875 s**; the game
fits that lead-in to its native one-second action and retains half a second of recovery. Gameplay timing is unchanged.
The native death/corpse has only an active front view; the unused side death study supplied additional depth evidence.

Only descriptors **Water Elemental A/B/C**, monster IDs **76/77/78**, bind this model. Native aliases m501/m502/m503
resolve to m500 frames; unrelated zcat descriptors are not bound. Native spells remain Ice Bolt, Acid Burst and Ice Blast.
Both palms charge and the projectile leaves their midpoint. The regression checks the separate Cast selection and
actual projectile origin. Mouth, left-palm and right-palm sockets survive export. Head look is limited to 20° yaw/10° pitch.

| Tier | Scale (world units/metre) | Native standing height |
|---|---:|---:|
| A | 89.766106239 | 180.398524 |
| B | 114.248216702 | 229.599016 |
| C | 142.810882924 | 287.000000 |

Scale uses 164 visible standing pixels × native SFT scale, divided by 2.009650764 m mean standing height. The transparent
256-pixel canvas is not used. Walk/run strides are 2.5065/1.671 m, calibrated against tier A's native 200-unit movement speed.
Source: `assets_source/worlds/mm8/models/mm8_m500.glb`; cooked desktop model/textures and bindings are in
`assets_dev/worlds/mm8/models/`. Native collision and combat data remain authoritative.

## Verification and corrections

- Final UV gate: two body raster-edge overlap pixels, zero head overlap pixels; density about 2.26 px/cm body and
  7.78–7.79 px/cm head. The body paint's atlas includes the unused full-head footprint; final head uses its own atlas.
- Paid texture returns matched all upload triangles and UVs exactly after verifying Meshy's uniform recenter/scale.
  Only maps were applied to the animated master. A later small brow correction uses a continuous chart in unused atlas space.
- The close head review found three inward-facing overlapping pockets. Forty-one local faces were replaced by
  fourteen manifold triangles without moving surrounding vertices; all other UVs remain unchanged. Before/after clay
  images and `work/brow_repair.json` retain the evidence. The new 96×64 chart projects nearby original blue paint
  with a maximum 3.43 mm sample distance, avoiding triangular paint seams; the UV gate and final head close-up pass.
- Forearm-fin weights and dorsal-sail connectivity were repaired before motion expansion. The backward death arc and
  folded sail avoid lifting the whole tail to compensate for a buried head/fin.
- Export preserves fractional animation keys, removes Blender's one-frame start offset and checks all nine durations.
  Dense 96 Hz samples stay at least 4.3 mm above the plane; loop endpoints match. Final reimport checks 81 poses and all
  three sockets; see `review/export_parity.json`. The repaired brow faces point outward and retain manifold boundary edges.
- Browser checks cover all 27 tier/clip combinations. `review/playback/` contains real-time recordings at 1× and ½×,
  with timestamped samples inspected for support, silhouettes, joints and endpoints. This is agent review, not user acceptance.

The ordinary `openyamm` build and focused Water Elemental regression pass. The wider MM8 actor run is **29 passed,
2 failed**, in Triton and Cyclops binding/presentation checks; their assets and checks were not changed by this task.
[Delivery validation](review/delivery_validation.json) records installed hashes, exact clip durations and these results.

Native NVIDIA/OpenGL 3.3 captures compare the same model/sprite cameras at MM6 `oute3.odm` and `6d19.blv`, using a
private preload fixture. Production maps are unchanged. All three tiers, all four LODs and close materials were
inspected. The far LODs intentionally lose face/finger detail; forced close shots expose their simplified ventral UVs.
Static screenshot tours freeze simulation, so their attempted death shots were excluded from selected evidence.
Separate live native input replays show the backward death transition, followed by the shared runtime **loot satchels**;
the held `Dead` pose remains in the model/viewer. No corpse-policy changes were made.

| Review | Model | Original sprite | Live death / remains |
|---|---|---|---|
| Outdoor | [tiers](review/ingame/outdoor_models/01-party.png) | [native](review/ingame/outdoor_sprites/01-party.png) | [death](review/ingame/outdoor_live/dying.png) · [remains](review/ingame/outdoor_live/corpse.png) |
| Indoor | [tiers](review/ingame/indoor_models/01-party.png) | [native](review/ingame/indoor_sprites/01-party.png) | [death](review/ingame/indoor_live/dying.png) · [remains](review/ingame/indoor_live/corpse.png) |

[Run records](review/ingame/runs.json) · [27 viewer switches](review/viewer_check.json) · [Playback review](review/playback_review.json)

The 18 playback recordings precede only the final continuous brow UV/map correction; geometry, weights, rig and
motion are unchanged. Final head/hand shots and all-nine-clip export parity cover the updated deliverable.

## Rebuild

Claim the project before rebuilding, then use its lease with the existing guarded Blender/Meshy/review wrappers. The selected frozen animated
input is **`work/anim_uv_brow.blend`**; `work/anim_uv.blend` preserves the paid-upload topology. Do not replace either
with a static Meshy return or rerun generation merely to resume.

1. `repair_brow.py` reproduces the local mesh correction and continuous UV patch; then `compose_textures.py`
   uses retained maps/rasters and runs `project_brow_texture.py` to paint that patch.
2. `export_water.py` writes the packed master and LOD0, preserving fractional keys and normalizing clip start times.
3. `prepare_actor_glb.py`, `scripts/build_lods.py`, then `scripts/finish_runtime.py` produce the merged game GLB.
4. `scripts/final_checks.py` verifies export parity and final UVs, and refreshes owned caster source-rate evidence.
5. `tools/install_model.py export/mm8_m500.glb --world mm8` installs and cooks the desktop asset.
6. `viewer_tiers.py` and `update_viewer_manifest.py` refresh the shared review viewer. The native fixture preloads this
   family in isolated MM6 outdoor/indoor scenes; refresh its model/textures after reinstalling, because install is atomic.

No Vulkan or Android build is part of this delivery. Native GPU captures are visual checks, not performance benchmarks.

## Texture quality pass (2026-10-31) - current installed textures

User request after `../claude_shared/TEXTURE_QUALITY_PASS.md` ran over all MM6-MM8 monsters: the Water Elemental was
one of the first three redone (MM8 `mm8_m500`, MM7 copy `mm7_m210`). Sharper textures only: mesh, rig, weights, clips
(Cast v2), LOD geometry, sockets, materials, variants and bindings are the installed ones.

**Route.** The pass edits the installed GLB (the reduction and far-LOD repair output, backed up in
`work/before_texpass/`), not an older project export: `scripts/texpass_diff.py` confirms that only UVs, images and
ramps changed (node/mesh/material/clip/variant lists, clip and skin data, and positions, normals, joints and weights of
every mesh per triangle corner are identical).
- `texpass_uv_prep.py` welds the installed LOD0 by position, separately for the head-set faces (u > 0.5 of the old
  2080x1024 atlas) and the body, so the 2,002 old islands no longer constrain the charts and no chart crosses the
  head/body line. `texpass_uv.py` (Blender, `claude_shared/uv_atlas.py`): xatlas charts, merged small charts, head
  2.5x denser, fast packer sweep (`fine=250 steps=0`: 53.4 %; brute force 51.5 %, `max_cost=4` also 53.4 %), one
  2048 square -> `texpass/uv_layout.npz` and the uploads `texturing/m500_{body,head}_upload_tp.glb`
  (hashes in `texpass/layout_hashes.txt`). Never re-run: the paid maps belong to this exact layout.
- **One atlas, not two sets again.** The material is one primitive per LOD with three variants; two sets would mean a
  second material per tier and new bindings. The head still gets its own paint: the head-set faces alone were
  retextured with the four close head views on the same UVs (`requests/head_retexture_tp.json`), the whole body with
  the four HD masters (`requests/body_retexture_tp.json`), both `meshy-7`, 4K, our UVs (returns verified by
  `texpass_verify_return.py`: identical UV triangles, uniform rescale only). Head charts take the body paint below the
  gills and the head paint above (the production crossfade, 1.54-1.66 m), so the head/body chart seam joins two
  body-paint texels. Head density 7.0 -> 11.3 px/cm, body 2.2 -> 4.5 px/cm.
- `texpass_raster.py` (per-texel surface data, old UV at each point), `texpass_ao.py` (4 cm AO on the new UVs),
  `texpass_compose.py`: colour and normal 4K -> 2K once (Lanczos; Meshy normals measured +y down and flipped), the
  production grade (0.15 AO multiply; the recipe's gentle grade adds local contrast this skin never had), 1K
  metal/roughness (production specular/roughness classes) and 1K region mask. Regions use the production hue test;
  fins are limited to the approved fins (4 texels at 2K), approved-masked texels the test leaves out keep their region.
  A first version limited every region to the approved mask: the new paint's ventral edge follows the HD masters, and
  the white texels outside the approved ventral turned bright cyan under the scale ramp.
- **Ramps** keep the production method (native palette 501/502 targets x gains, median at the target) with a contrast
  pin: the 4K paint spreads each region's luminance wider around its median (fins and palms 1.30 against 0.94), so the
  slope is scaled by k (scales 0.825, ventral 0.942, fins 0.726) to the approved spread
  (`colour = target * (1 + k * (lum / mid - 1))`).
- `texpass_build.py`: LOD0 and its identical shadow take the new UVs (9,384 -> 9,753 vertices); LOD1 and the shadow
  LODs (moved vertices) take the UV of each corner's closest facing LOD0 point, one chart per triangle with a linear
  extension across seams; LOD2/LOD3 keep their repaired geometry and UVs and get their maps transferred again from
  the new LOD0 with `lod_repair_claude`'s `transfer_textures.transfer` (512 / 256 px).

| `texture_quality.py`, LOD0 | Before | After |
|---|---|---|
| Texture | 2080x1024 (body and head squares) | 2048x2048 |
| Atlas use | 30.6 % | **53.4 %** (target 55; this layout's packing limit) |
| Density p10 / p50 / p90 (texels per creature size) | 631 / 738 / 784 | **1,429 / 1,477 / 1,588** (x2.0) |
| Spread p90/p10 | 1.24 | 1.11 |
| Islands / fragments | 2,002 / 34.1 % | 94 / 0.1 % |
| Stretch p90 | 1.65 | 1.16 |
| Zero-area UV triangles | 0 | 0 |
| Meshy source | 2 x 2K on 1K sets | 2 x 4K on the 2K atlas |

Runtime maps: colour and normal 2048, metal/roughness and mask 1024 (were all 2080x1024), about the same GPU memory.

**Checks.** Tone (`texpass_tone.py`, engine tier colour at the same surface points): medians within 3 levels on scales
and fins, ventral 9 levels darker (190 -> 181), luminance spread and 4-16 px band equal to the approved within a few
percent, every tier. LOD1 colour against LOD0 (`texpass_lod1_check.py`): mean 6.1 levels, 6.8 % over 24 (installed
11.9 / 14.8 %). Far-LOD switch audit (`lod_repair_claude/scripts/audit.sh`, `texpass/lod_audit/scores.tsv`): LOD2
4.2 % / 13.7, LOD3 6.1 % / 10.4, as installed. Winding 0 inverted; flat shading 0.00; `detached_parts_audit.py` 0 (as
before); floor audit Water Elemental A-C ok; `mm8_water_elemental_actor_models_keep_tiers_and_palm_cast` and
`mm6_mm7_mm8_actor_models_build_every_binding` pass; viewer `check` 54 switches, 0 errors (the native anchor images
under `mm7_mm8_packed_outline/` are missing, as before this pass). No in-game run.
Sheets (review viewer, identical cameras, before | after): `review/texpass/texpass_sheet_{a,b,c}.png` (full front,
3/4, side, head front/3/4/side, torso, Cast hands, back fins, tail). Viewer `review/viewer/` (revision
`texpass-20261031-r3`, ids `before_a..c`, `after_a..c`; page from `../mm8_m480_texpass_claude/review/viewer/`).

**Visible changes and drift.** Scales, ventral plates, diamond spots, fins and eyes read sharp where the approved paint
was blotchy; colours and contrast match per tier. The 4K paint follows the HD masters more closely: the dark diamond
spots are more distinct, the palms carry a fine reticulated pattern, the ventral edge is straighter, and the tail's
belly edge has a few scattered pale scales (Meshy's light scales next to the belly).

**Meshy: 20 credits** (body and head retexture, 10 each, backup account). Installed with
`tools/install_model.py texpass/export/mm8_m500.glb --world mm8`.

Rebuild (no paid step): `texpass_raster.py texpass/uv_layout.npz 2048 1024` -> `texpass_ao.py` (via
`tools/run_creature_blender.sh`) -> `texpass_compose.py` -> `texpass_build.py texpass/uv_layout.npz
texpass/export/mm8_m500.glb` -> `texpass_viewer.py review/viewer <revision> work/before_texpass/mm8_m500.glb before
"Installed (before)" texpass/export/mm8_m500.glb after "Texture pass"`. Then the MM7 copy
(`../mm7_m210_claude/scripts/tier_ramps.py`, `build_glb.py`). Rollback: install `work/before_texpass/mm8_m500.glb`.

**Eye correction (2026-11-01, r4, installed).** User review: the 4K head paint drew thin, off-centre slit pupils (a
walleyed look) and lost the dark iris rim. `texpass_compose.py` now carries the approved paint at the same surface
points within 2.5 mm of the approved yellow eye texels, feathered over a further 2.5 mm, with a flat normal there
(12,844 texels at 2K); the rest is unchanged (ramps within 0.0002). `texpass_diff.py` against r3: only UVs, images
and ramps; winding 0. Rebuilt the MM7 copy (ramps within 0.001) and installed both; the Water Elemental and
every-binding regressions pass, viewer `check` 54 switches with no model errors. r3 kept as
`texpass/export/mm8_m500_r3_offcentre_eyes.glb`. Viewer revision `texpass-20261101-r4-eyes`; close-ups
`review/shots/z_{before,after}_a_{front,quarter}.png`. Meshy: 0 credits.
