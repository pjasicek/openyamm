# MM6 Red / Blue / Gold Dragon — cdr1

Selected revision **v7-palette-depth** is installed and ready for user review. Red and blue now have deeper midtones and stronger scale contrast, with modestly richer red and a gentler wing correction. The user accepted v6 motion; all its animations and geometry are retained. Artistic acceptance of the v7 colour adjustment is pending.

- **Burning death (2026-10-13):** engine burn effect like the Flying Drake's, see "Burning death" below.
- Merged monster IDs: **514 / 515 / 516**; descriptors **DragonCover A / B / C**.
- Viewer: http://192.168.1.130:8912/level_generation/creatures/mm6_cdr1_claude/review/viewer/?v=palette_v7
- Editable packed master: [export/mm6_cdr1.blend](export/mm6_cdr1.blend).
- Portable/runtime source: [export/mm6_cdr1.glb](export/mm6_cdr1.glb), installed through `tools/install_model.py` to `assets_source/worlds/mm6/models/mm6_cdr1.glb` and its runtime copy under `assets_dev`.
- **13,185 authored LOD0 triangles**, reduced from 16,646. Runtime backface splitting adds 119 required reverse faces: **13,304 runtime LOD0 triangles**. Colour LODs before/after backface splitting: 13,185/7,603/4,001/2,654 and 13,304/7,707/4,233/2,869. Thin wings retain the selected geometry across LODs.
- Meshy **35 of 100 credits**: 5 geometry, 10 each for body/head/wings retexture. No animation purchases.
- Three separate 2K PBR sets, RGBA region masks and native palette ramps 698/699/700. Viewer-only tier images are baked for three.js; the installed asset shares one texture set.

## Red / blue palette depth v7 — 2026-10-13

The restored ×2 palette 698/699 comparison confirmed lighter body midtones in the model, lower red saturation and already similar blue saturation. Six material ramp fields now deepen red/blue body and head midtones, increase contrast through existing scale detail, and restore highlights toward the top of the range. Only the red hide receives an explicit saturation increase (1.075 in linear colour about luminance). The wings use a much gentler correction (at most 9% linear-luminance attenuation, protected at the dark and bright ends; red chroma 1.025). Belly ramps are adjusted more gently than hide. These are ramp parameters, not final screen brightness percentages.

The comparison uses the same current viewer lighting and cameras, with native/restored colours as a guide. Coloured-hide median L* differences in front/profile flight fall from about 9–10 points to **0.9–2.3 points**; Attack differences are below one point. These regional statistics include different model/sprite proportions and baked/native lighting; they do not imply identical pixels or lighting.

[Front before / reference / after](review/palette_v7/comparison_front.jpg) · [Side before / reference / after](review/palette_v7/comparison_right.jpg) · [Measurements](review/palette_v7/comparison_metrics.json) · [Preservation](review/palette_v7/preservation.json) · [Native outdoor capture](review/palette_v7/ingame/01-tiers_front.png).

The runtime/source GLB changes only red/blue `openyamm_region_ramps`: its entire binary chunk, including mesh/UV/skin/animation and every shared image, is unchanged. Gold materials and viewer pixels are verified identical. The packed `.blend` and ungraded intermediate exports stay unchanged; `textures/cdr1_ramps.json` is the editable runtime palette source. Viewer colours are rebaked through the existing tier helper and checked for retained geometry, animations and all non-colour maps. No image generation, Meshy spending, model rebuild or animation changes were needed.

All 27 viewer tier/clip switches and both focused dragon family/burn regressions pass. New outdoor front/quarter captures were inspected on NVIDIA OpenGL 3.3 / Wayland. Indoor captures and the broader suite were not repeated. The original input-tour capture encountered changed console behaviour; the successful engine-native screenshot tour and run record are saved in `review/palette_v7/ingame/`.

Reproduce with `scripts/grade_palette_v7.py` under the creature lease, then the standard `tools/install_model.py export/mm6_cdr1.glb --world mm6`. The grade always starts from `work/before_palette_v7/`, so reruns do not accumulate darkening. That directory retains the v6 ramps, export, viewer and progress. [Delivery hashes](review/palette_v7/delivery_hashes.json).

## Wing fold and head entry v6 — 2026-10-13

The middle-wing peak bend is reduced from 88.8° to **44.4°**, with **26.6°** at the distal joint. The wings retain the attack fold with a broader arc instead of the hooked bend reported at frame 23. Attack/Cast start in the same local pose as Standing frame 0; the head turns sideways during the first 0.15 s, so the preparation remains visible after the 0.125 s incoming blend. The existing body dip, recovery, 1 s clip duration and **0.75 s impact** are retained.

Only Attack/Cast animation data changed. Geometry, UVs, maps, materials, skin, all LODs and the other seven clips are fingerprint-checked unchanged in the production GLBs. The editable master and all three viewer tiers are updated, and the standard installer refreshed source/runtime assets.

[Before/after wing fold](review/motion_v6/wing_comparison.jpg) · [Playback samples](review/motion_v6/attack_playback.jpg) · [Deformation/export checks](review/motion_v6/checks.json) · [Entry checks](review/motion_v6/entry_checks.json) · [Preservation](review/motion_v6/preservation.json) · [Delivery hashes](review/motion_v6/delivery_hashes.json).

Checks passed: dense 96 Hz deformation/tooth checks; nine-sample export parity for every clip (maximum error 0.012 mm); all 27 viewer tier/clip switches; Attack playback at 1× and 0.25×; the two focused dragon family/burn regressions. A simulation of the engine's frozen outgoing-pose crossfade samples 408 poses across 24 Standing/Walking entries, with no floor penetration or quaternion flips. This simulation is not a live gameplay transition capture. Native game captures and the broader suite were not repeated for this scoped repair; v5 captures below are historical. The retained model anatomy and membrane proportions still differ from the painted reference.

The existing motion scripts now produce v6: `scripts/motion_v5.py` → `export_motion_v5.py` → `check_motion_v5.py` → `check_attack_entry.py` → `publish_motion_v5.py`, followed by `tools/install_model.py export/mm6_cdr1.glb --world mm6`. Their filenames are retained; the current baseline is `work/before_motion_v6/export/mm6_cdr1.blend`. Original v5 scripts, exports, viewer and progress are preserved under `work/before_motion_v6/`. Use the creature lease/wrappers for writes.

## Native motion v5 — 2026-10-13

- Attack/Cast start with a sideways head and raised narrow-V wings, sweep down through native pose D at 0.375 s, then rise with the head turned to the opposite side. The jaw stays readable through the neck dip. Outer wings articulate into a curved downstroke rather than remaining flat and broad.
- The bend is distributed through Spine1/Spine2 and the three neck controls. Root and rear-foot height vary by only **0.02173 m** through the attack. Living clips have real clearance above the ground; the lowest surface is no longer pinned to it every frame.
- Standing and Walking share identical flight poses and elevation over 0.75 s. Running compresses the same cycle to 0.625 s; Fidget uses two cycles plus a head glance over 1.5 s. Attack/Cast last 1 s, including 0.25 s recovery. Their binding marker is 0.75 s, preserving the native 0.75 s gameplay action and six 0.125 s source anchors. The incoming blend is 0.125 s. Hit, Death and Dead retain their original seconds and animation samples.
- All mesh attributes, LOD geometry, skin data, maps/materials and the three retained clips are checked unchanged in the five production exports. No Meshy credits or geometry changes. The master is now authored at 48 fps; the viewer defaults to that frame scale and includes all six restored reference poses.

[Attack versus restored ×2](review/motion_v5/Attack_comparison.jpg) · [Flight versus restored ×2](review/motion_v5/Standing_comparison.jpg) · [Validation](review/motion_v5/checks.json) · [Preservation](review/motion_v5/preservation.json) · [Delivery hashes](review/motion_v5/delivery_hashes.json).

Dense 96 Hz sampling of the six changed clips checks floor clearance, bone scale/translation, quaternion steps, loop closure and upper/lower tooth intersections; rear-foot stability and matching Standing/Walking are asserted. Teeth remain rigid within 0.0004 mm. Nine samples of every clip survive isolated GLB reimport within 0.012 mm. Actual browser playback at 1×/0.25× and all 27 tier/clip switches pass. The ordinary build and the focused dragon family and shared burn-death regressions pass. Native NVIDIA/OpenGL/Wayland model/sprite captures are under `review/motion_v5/ingame/`.

The first shared-manifest check was blocked by a concurrently edited Wyrm remains material. It was corrected externally; the final checks use the normal shared manifest. No Wyrm or material-loader edits were made here. Indoor pillars and ceiling partly obscure the wings, so neutral front/profile/quarter views provide the unobstructed deformation review. Live sprite/model screenshots share camera and scale but differ in AI pose/time. The retained model's anatomy and membrane proportions still differ from the painted silhouette; this is a smooth reconstruction of the main pose sequence, not a pixel-exact replacement of the billboards.

Historical v5 used `work/before_motion_v5/`; its source scripts are archived under `work/before_motion_v6/scripts/`. Current reproduction is described in v6 above. Do not run older repair scripts over the selected revision out of order.

## Burning death — 2026-10-13

As the native frames (`review/burn/native_death.jpg`): the outline catches at once, the whole dragon turns to fire,
and the fire shape collapses to the ground before it dies out. `actors.yml` binds `death_effect: {type: burn, ...}`
(start 0.05 s, end 1.75 s, fire width 0.45, yellow-orange fire); the engine effect is described in
`engine/render/MODEL_RENDERING.md`, "Burning creatures". Nothing remains: the corpse draws nothing and the loot
satchel, if any, takes its place.

- **Burn maps:** `textures/cdr1_{body,head,wings}_burn.png` are baked straight from the runtime GLB by the shared
  `claude_shared/bake_burn_maps.py`, which uses the installed UVs, including the teeth and ivory repairs. The head,
  wing rims (fold-back edges of the closed membranes) and tail tip ignite, and the wings burn at half cost. Separate
  pieces (teeth, claws, horns) burn with the surface nearest them. Statistics are in `review/burn/burn_maps.json`.
  `finish_runtime.py` and `export_scales.py` embed the maps with `claude_shared/burn_maps.py` before the tier variants.
- **Death clip:** `scripts/animate_death.py` rewrites only Death (2.4 s, 58 frames) and Dead in
  `export/mm6_cdr1.blend`. The sequence is a roaring recoil, a short airborne thrash (2.8 Hz wing beats, lashing tail,
  jerking bank and yaw), then a collapse flat to the ground (belly down, wings spread low, head and tail down). Lift is
  one smooth envelope over the floor clearance, so there is no bounce. Root height sinks steadily from 0.92 to 0.50 m;
  peak chest speed is 0.75 m/s.
- **Transplant:** `scripts/transplant_death.py` copies just these two animations into the selected, LOD0, LOD and
  shadow exports. Every mesh, skin and other-clip accessor is checked byte-identical (`review/burn/transplant.json`).
  Pre-burn exports and master: `work/before_burn/`. The v5 web viewer now carries these updated skeletal clips; the engine supplies the burn effect.
- **Checks:** `mm6_drake_and_dragon_actor_model_burn_death` and `mm6_dragon_actor_model_tiers_and_clips` pass.
  Native NVIDIA OpenGL capture at 0.1× game speed: `review/burn/ingame_death.jpg` and `ingame_death_closeups.jpg`.
  No indoor capture.

## Scale definition v4 — accepted

User requested slightly more visible scale texture/normal detail after accepting v3. The body/head hide now has darker local grooves (up to 13.93%, about 3–4% average hide darkening) and 22% stronger tangent-normal XY detail. Palette ramps, region masks, roughness/specular maps, wing textures and protected ivory texels are unchanged. Geometry, UVs, skin and animation accessor bytes are identical to v3; the existing LOD counts are retained. No Meshy credits were spent.

[Body comparison](review/scales_v4/torso_comparison.jpg) and [head comparison](review/scales_v4/head_comparison.jpg), accepted v3 on the left, v4 on the right. Red close-ups were inspected under matching viewer lighting; all 27 tier/clip switches and the focused dragon runtime regression passed. Native close-ups were not repeated. Accepted v3 maps and exports are preserved in `work/before_scales_v4/`. Reproduce with `enhance_scales.py`, `export_scales.py`, `pack_scales.py` and the standard installer.

## Ivory correction v3

The user accepted the v2 teeth and requested the same clean ivory on hand/foot claws, ankle spurs, head horns and wing spurs. Corrected the local base colour, roughness/specular classification and all tier masks. A few horn faces shared UV space with red body surfaces; their ivory interiors now use padded, subtly varied enamel swatches in free space in the same three 2K atlases. No new material or texture set was added. Existing gold dorsal spines retain their original colour.

The selected mesh positions, faces, skin weights and sampled bone poses are exactly unchanged ([check](review/ivory_v3/parity.json)); LOD0 stays at 13,185 authored / 13,304 runtime triangles. Export reimport and all 27 viewer tier/clip switches passed, as did the focused dragon actor regression. Close-ups: [horns](review/ivory_v3/horns.png), [hands](review/ivory_v3/claws.png), [feet](review/ivory_v3/feet.png), [wing spurs](review/ivory_v3/wing.png). No Meshy credits were spent. Native close-ups and the broad regression suite were not repeated for this scoped correction.

Reproduction starts from `work/before_ivory_v3/`: `ivory_uv_raster.py` → `repair_ivory.py` → `ivory_tiles.py` → `repair_ivory_uv.py` (exports the selected master), followed by normal preparation, `final_checks_lods.py`, `finish_runtime.py`, `viewer_tiers.py` and the normal installer. Reviewed 3D selection seeds and atlas tile coordinates are retained under `work/`; these are creature-specific selections. Earlier captures below are historical.

## Teeth correction v2

The user approved the overall model and requested sharp, simple teeth and removal of red texture bleed. Replaced 27 malformed tooth islands (820 triangles) with 24 closed, slightly curved fangs at 22 triangles each (528 total). Upper teeth follow Head rigidly, lower teeth follow Jaw. Their roots are seated below the gum surface. The rest of the geometry, motion and body/wing maps are retained.

A padded unused patch in the existing 2K head atlas contains warm-root/ivory-tip enamel with its own roughness and neutral normal. The region mask is zero there, so every palette retains ivory teeth. Local gum texture/normal cleanup removes leftover enamel contamination. No new material slot, texture set or Meshy job was needed; spending stays 35/100 credits.

The [tooth check](review/teeth_v2/motion_check.json) samples every clip at half-frame steps: 549 poses, no upper/lower tooth surface intersections, rigid shape error below 0.0004 mm. Export reimport, all 27 viewer tier/clip combinations and the focused dragon actor regression passed. Normal/slow attack playback and mouth close-ups were reviewed. [Standing close-up](review/teeth_v2/viewer_stand.png), [neutral quarter view](review/teeth_v2/quarter.png). Native captures below predate this scoped repair; no engine change or repeat of the broad regression suite was needed. Earlier source/maps are retained in `work/before_teeth_v2/`. The reduction ladder below is historical; v2 subtracts 292 triangles from its selected mesh.

## Appearance and motion

Five full-body HD references plus a head close-up retain the native heavy torso, substantial four limbs, swept horns, gold underside and broad membranous wings. Geometry repairs removed stretched bridge triangles and rebuilt the damaged half from the sound half. The continuous body/head surface retains separate material density. Original downloads, prompts, hashes, uploads and UV-return correspondence are retained.

36-bone rig with articulated jaw, three neck controls, nine tail controls, separate wing/limb chains and Socket_Mouth. Current durations and attack timing are listed under v5 above; Hit remains 1.125 s, Death 58/24 s and Dead 1 s. These are authored native-informed motions, not frame-exact native reconstructions. Dead holds the last Death pose; the burn itself is the engine effect.

## Reduction and checks

Protected 10% ladder: 16,646 → 14,974 → **13,477** → rejected 13,003. The last attempt could not reach its target without protected areas and visibly folded both wing membranes. The previous step was retained. See [selection](review/reduction/selection.json) and its before/after renders. Face, claws and UV seams were protected; weights are normalized with at most four influences.

Isolated export reimport matched five samples of every clip within 0.013 mm. Loop endpoints match; Dead is static. Actual browser playback was exercised at 1× and 0.25× and sampled frames inspected. The final viewer passed all 27 tier/clip combinations without console errors. Native game captures compare models and sprites indoors and outdoors on OpenGL 3.3/NVIDIA under Wayland. See [review](review/) and [delivery hashes](review/delivery_hashes.json).

Ordinary openyamm build and `mm6_dragon_actor_model_tiers_and_clips` passed. The MM6 actor regression run finished **55 passed / 3 failed**: mage colour-ramp, guard merged-material and ooze specular-skin checks. Those assets were not changed by this task. The broader unfiltered actor suite encountered DWI/map-state failures and `std::bad_alloc`; it is not a clean pass. The first indoor console tours lost SDL text input after model loading; engine-native screenshot tours produced the final comparison successfully.

Scale is 230.636368 world units per model unit, fitted to mean opaque front-flight area at native scale 1.299988. Tiers use their native scale ratios. Native silhouette timing and provenance are in [review/native_motion.json](review/native_motion.json).

## Historical death handoff

[Death handoff](integration/DEATH_HANDOFF.md) records the original division of work. It is superseded by the completed burning-death implementation above. Motion v5 preserves its geometry, maps, Death/Dead clips and runtime effect settings.
