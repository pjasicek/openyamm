# MM6 Flying Drake — reduced geometry v7


## Accepted mild scale detail — 2026-10-13 (v9)

Applied the user-selected mild preview to all three tiers. Body hide normals use 1.20× tangent XY strength;
head hide uses 1.10×. Existing scale grooves receive restrained darkening (average hide: body 2.84%, head 1.94%).
Gold plates, ivory, eyes/mouth, wing textures, roughness, region ramps and burn maps are unchanged. No Meshy spend.

The current **v8 engine-burn** model is the baseline: 36 joints, Death 2 seconds, no flame cards or remains mesh.
Authored colour LODs remain **14,488 / 8,182 / 4,083 / 2,560** triangles; processed runtime LODs including backface
copies remain **14,977 / 8,489 / 4,361 / 2,639**. Every non-image buffer and all model metadata are preserved.
Only four image buffers differ in both the project GLBs and installed runtime copy.

Updated the packed editable master, portable LOD0, intermediate LOD/shadow exports, installed source/runtime and
main viewer. All three viewer tiers match the approved preview's embedded images exactly. Checks: 27 tier/clip
switches without browser errors; both focused Drake tier/clip and burn-death regressions passed. No new native GPU
capture or engine changes. Web Death displays motion only; surface burning/fire remain engine effects.
Evidence: `review/scales_v9/`. The prior version is preserved in `work/before_scales_v9/`.

Reproduce from that checkpoint with `scripts/enhance_scales.py` → `scripts/export_scales.py`, then
`scripts/pack_scales.py` in Blender, viewer tier/manifest scripts and `tools/install_model.py`.
The canonical progress record contains current selected hashes and acceptance.

Flame / Frost / Energy Drake, merged IDs **508–510**, descriptors `BDragonFly A/B/C`.
Claude non-humanoid workflow. v6 anatomy accepted; v7 reduction delivered for review; v8 replaces the skeletal death
with the engine burn effect (awaiting review).

[Web viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_drg1_claude/review/viewer/) — three tiers, nine clips,
frame stepping and normal/slow playback. Refresh an existing tab to load v7.

Reusable lessons from this session: [Dragon and drake 3D creation](../CLAUDE_QUADRUPED_PLAYBOOK.md#dragon-and-drake-3d-creation-mm6-flying-drake-lessons).

## Engine burn death — 2026-10-13 (v8)

The death now uses the shared engine burn (`death_effect: {type: burn, ...}` in `actors.yml`; engine description in
`engine/render/MODEL_RENDERING.md`, "Burning creatures"). As in the native frames, the outline catches first (wing
edges, head, tail tip). The skin chars ahead of a glowing front and burns inward, the membranes fastest. Burnt
surface stays a shape of fire for a moment, with flames and embers rising from the burning band, and a fire light.
Nothing remains: the user judged separate charred remains not worth it, since the corpse sinks and leaves the loot satchel.

`prepare_burn.py` (from the v7 source; `work/checkpoint_v7/` keeps it) removed the 804-triangle remains, the
1,792-vertex flame cards and their 64 card bones plus `Remains`. It bakes `textures/drg1_{body,head,wings}_burn.png`
(1K: red = surface distance from the ignition points, wing faces at half cost, broad noise, equalised by area,
plus fine noise; green = crack pattern). `finish_runtime.py` embeds them with `claude_shared/burn_maps.py` before
the tier variants. `animate_drake.py` makes the Drake burn in the air, as the native one does (Death 2.0 s, 48 frames, no bone
shrinking). It shows a roaring recoil, then a frantic airborne thrash: 3.2 Hz irregular wing beats, a lashing tail,
jerking bank and yaw and a slight lift. The wings then give out and the body sags under the fire. Every Death and Dead
frame stays above the floor: the hanging wings lift it slightly instead of dipping below, and there is no ground
impact, which would happen mostly after the body has burnt away. Capture: `review/burn_v8/ingame_air_death.jpg`.
The hover lift is one smooth envelope (running maximum, then moving average, 8 frames), not per-frame floor
anchoring, which bounced the body 0.52–1.17 m with every wing downstroke. Dead holds Death's final lift. Measured:
peak chest speed 5.8 → 0.9 m/s, acceleration 103 → 7.6 m/s².

**Transitions (2026-10-13).** Forward flight (walk/run) and the upright hover (stand, attack, hit, death) move the head
0.9 m and the root 0.6 m. The default 0.12 s linear blend (none into death) made the Drake snap upright. The engine
now eases every blend, and the Drake's bindings set `blend_seconds: 0.4` and `death_blend_seconds: 0.3`: peak head
speed about 3.4 m/s, close to the attack clip's own 3.5 m/s. Body LODs 14,488 / 8,182 / 4,083 / 2,560 (v7 minus the remains); no flame mesh.

Reproduction: `prepare_burn.py` → `animate_drake.py` → `refresh_selected.py` → `build_lods.py` (all in Blender) →
`finish_runtime.py` → `tools/install_model.py`. Checks: `mm6_flying_drake_actor_model_burn_death` and the tiers case
(actors suite) pass. Inspected native NVIDIA OpenGL captures at 0.1× game speed: `review/burn_v8/ingame_burn_early.jpg`
and `ingame_burn_late.jpg`. They show charring from the edges, burn-through, the fire silhouette, embers, and an empty,
unpickable spot afterwards. Not yet done: indoor capture, and web viewer refresh (it shows clips only, not the
engine burn).

## Iterative triangle reduction — 2026-10-13 (v7)

Started from the accepted v6 anatomy/weights, preserving that master in `work/checkpoint_v6/`. Applied the shared
protected 10% reduction ladder, comparing every candidate with the original baseline in fixed textured cameras and
nine deformed clips before advancing. Head, claw/foot and UV-seam vertices receive protection.

| Trial | Body triangles | Result |
| --- | ---: | --- |
| Accepted v6 baseline | 16,992 | Preserved |
| Step 1, target 90% | 15,292 | Selected: textured shape and junctions hold up |
| Step 2, target 81% | 14,596 actual (13,764 rounded target) | Rejected: wing strips/tears and pinched belly/tail |

The second trial could not reach its requested count under the protection constraints. It visibly collapsed wing
membranes, exceeded 0.21 m maximum deformed-surface error and penetrated the floor by ~18 mm in Attack/Cast.
Stopped at this first failing step. Step 1 saves **1,700 body triangles (10%)**, retains the repaired hip junction,
head/claws and wing outline, and stays within the existing floor tolerance across sampled clips. Its 99th-percentile
surface error is at most 2.42 mm, with a local maximum of 17.34 mm around the upper body; these flagged areas were
inspected in textured closeups. Passing means no unacceptable visual loss in these checks, not identical geometry
or a mathematical minimum. No Meshy credits or new textures were used.

**Current authored body LODs:** 15,292 / 8,584 / 4,221 / 2,599. Unchanged separate flames: 896 triangles;
**total authored LOD0: 16,188**. Runtime body counts including backface copies: 15,781 / 8,891 / 4,499 / 2,678.

Evidence: `review/reduction_v7/selection.json`, per-step measurements and paired screenshots, selected normal/slow
playback samples, 27 tier/clip checks, export parity, installed-contract validation and focused Drake regression
(1 pass / 0 fail). All nine animation channels remain exactly equal to v6. Inspected a native outdoor Flame Drake
capture on NVIDIA OpenGL 3.3. No new indoor run or broad regression suite; prior low-ceiling and death issues remain.
[Comparison viewer](http://127.0.0.1:8901/level_generation/creatures/mm6_drg1_claude/review/reduction_v7_viewer/?model=step_01)
retains v6 and both trials; it uses the same source textures for every candidate, before viewer palette baking.

Current reproduction: `reduce_step.py` reads `review/reduction_v7/next_step.json` and the preserved v6 master;
it saves candidates, including failed diagnostics, without installing them. Only selected `step_01.blend` was copied
to `work/reduced_v7_source.blend` and `work/anim_repaired.blend`, then passed through `refresh_selected.py`,
`build_lods.py`, `finish_runtime.py`, viewer tier/manifest generation, installer and delivery/export validators.
`animate_drake.py` now reads the reduced source for later animation edits. Historical geometry-preservation validators
for v5/v6 predate this topology change; use the current reduction reports and export/delivery checks for v7.

## Tail-to-torso junction repair — 2026-10-13 (v6)

The accepted larger limbs exposed central belly/tail vertices incorrectly following the hind-leg bones. Upright leg
rotation and length scaling pulled that skin into a sharp folded ridge. Corrected 201 local vertex weights: central/high
skin follows the spine/tail, with a smooth transition into the thighs. Reapplied the same accepted limb enlargement using
these corrected weights, removing its accidental effect on that central skin. No Meshy spend or texture replacement.

Verified unchanged geometry/weights outside this local repair, topology, UVs, materials and head/neck. All nine clips
pass half-frame finite/floor checks and GLB export parity. All 27 viewer combinations and the focused Drake regression
pass. Inspected front/quarter/rear and attack closeups plus normal/slow playback samples. Evidence: `review/tailjoin_v6/`.
No new native GPU capture for this local repair; the v5 native capture remains, and the newly installed asset passes its
LOD/material/animation contract. The larger limbs and v6 junction appearance are user-accepted (2026-10-13).

Historical v6 reproduction: `repair_tailjoin.py` (from preserved v4 geometry) → `animate_drake.py` → `refresh_selected.py` →
`build_lods.py` → `finish_runtime.py` → `viewer_tiers.py` → `update_viewer_manifest.py` → installer →
`check_tailjoin.py`, `export_parity.py`, `validate_delivery.py` and viewer checks. `work/checkpoint_v5/` preserves v5.
The previously documented death/timing and indoor ceiling limitations remain separate work.

## Limb proportion revision — 2026-10-13 (v5)

Compared the restored native front, quarter and side hover frames. Enlarged the existing limb mesh: upper segments
use 1.55× radial thickness, lower segments 1.65×, and hands/feet 1.70× width / 1.35× length, blended into their roots by
existing skin weights. Upright forelimbs no longer have the previous 0.75× pose shrink. The result has fuller thighs,
forearms and larger clawed extremities while retaining the approved upright/forward-flight split.

Head/upper-neck rest geometry, all UVs, topology, material indices and weights are verified unchanged. Existing separate
2K textures remain usable in closeups. No new Meshy job, credits or LOD0 triangles. The previous version is preserved at
`work/checkpoint_v4/`. The selected authored body remains 16,992 triangles; flames add 896, for 17,888 total.

Validation: half-frame checks across all nine clips, Blender/export parity, installed animation/texture/LOD checks,
27 viewer tier/clip switches, normal/slow playback with captured-sample visual review, and the focused Drake regression
(1 pass / 0 fail), plus an inspected native outdoor Flame Drake capture on NVIDIA OpenGL 3.3.
Evidence: `review/limbs_v5/`. The multi-spawn tour lost SDL text input after its first spawn; a single-spawn tour
succeeded. Three-tier coverage is from the viewer. Artistic acceptance of these proportions is pending.
The previously documented death effect/timing and low-ceiling limitations remain separate work.

Historical v5 reproduction: `enlarge_limbs.py` (from v4 checkpoint) → `animate_drake.py` → `refresh_selected.py` →
`build_lods.py` → `finish_runtime.py` → `viewer_tiers.py` → `update_viewer_manifest.py` → installer →
`check_limbs.py`, `export_parity.py`, `validate_delivery.py` and viewer/native checks.

## Flight correction and death assessment — 2026-10-13

Walking and Running now match every animation channel of the previous forward-flight v2 exactly. Standing, Fidget,
Attack, Cast, Hit, Death and Dead remain byte-equivalent in channel values to v3. Upright idle is retained.
The latest corrected hip/shoulder weights and approved geometry/textures remain. No Meshy credits or triangles were added.
Viewer body focus now follows the upright/forward pose when switching clips.

Validation: `review/flight_v4/clip_preservation.json`, normal/slow locomotion playback, all 27 tier/clip combinations,
installed geometry/animation contract, focused Drake regression (1 pass / 0 fail). This scoped two-clip restore did not
repeat GPU captures; earlier v2 flight and v3 upright native captures remain. No engine code changed this turn.

### Death findings and recommendation

Inspected both native and aligned restored frames: `review/flight_v4/restored_death_study.jpg`.
The actual native sequence selects **a, b, c, d, f**, 187.5 ms each = **0.9375 s**, then corpse h.
Artwork e and g exists but is not selected by the current native frame table; the comparison sheet shows all eight.

The original keeps a recognizable curled silhouette while flame-edged holes consume wings and skin, then shows a fiery
outline and embers, and finally a small charred remnant. Current bone shrinking plus attached flame cards cannot match that
surface erosion. Existing `death_effect: disintegration` is an 80-particle mist/smoke burst, not a mesh-burning effect.
The current 1.5-second authored clip also exceeds native Dying: `WorldFxSystem` skips longer-clip continuation when
`binding.disintegrates`, allowing an early jump to Dead. This is a confirmed timing problem, not merely an art preference.

**Recommended next implementation:** preserve model recoil/curl/wing folding; add per-instance burn progress for skinned
materials, with stable surface erosion and a glowing edge, plus bounded flame/ember particles. Exclude charred remains
from burning and keep the cutout consistent in colour, depth and shadow rendering. Reuse existing particle infrastructure.
Use one death clock; preferably fit this Drake to native 0.9375 s, or explicitly allow the visual tail to finish without
changing AI/loot timing. Remove the skeletal-shrink substitute and card-frame bones when the engine effect replaces them.

Existing placement coverage is a static/stand-in screen-door fade, not an animated mesh burn boundary. Skinned draw paths
also pass zero material time, so the static decoration flipbook support is not a drop-in solution. This needs shared
renderer/actor-FX work, not a new Meshy model. A native/restored death billboard handoff is another option, but keeps the
single-view appearance and would need explicit model-to-sprite transition support.

**This turn assessed death only; its animation/effects and timing were not changed.** Exact source findings and proposed
scope are retained in `review/flight_v4/death_study.json`. `work/checkpoint_v3/` preserves the all-upright revision.

## Upright revision — 2026-10-13

The user approved the head and head/neck join and requested the original sprite's upright silhouette.
The existing model is retained: rest geometry, UVs, material assignments and upper-neck/head weights are verified unchanged.
The torso now pitches back 56 degrees, the neck and wing plane compensate, forelimbs tuck close to the chest at 75% scale,
and hanging hind legs have longer upper/lower segments (1.45× / 1.25× local bone length). The tail curls sideways at the tip.
This pose is applied consistently to all nine clips; timings, breath socket and burning/remains choreography remain.

Upright motion exposed tail-base vertices incorrectly assigned to hind-leg bones and shoulder skin assigned to neck bones.
`prepare_upright.py` repairs those weights on the preserved v2 checkpoint before `animate_drake.py`; no new mesh was generated.
The selected triangle count remains unchanged. **No additional Meshy credits** were used (90/100 total).

New front-flight area is 0.6386418 m². The same native-area calibration yields **scale 348.995968**, replacing 382.290943;
tier scaling stays native. The focused regression's height range now covers the taller upright silhouette (560–630 units).
Verification is in `review/upright/`: all clips at normal/slow speed, 27 tier/clip switches without browser errors, half-frame
floor/preservation checks, export parity, installed-contract check, focused actor regression and native GPU captures.
Ordinary OpenGL build and focused actor regression passed. The broader actor suite was not rerun.
Outdoor captures show the whole upright silhouette. **Indoor limitation:** at native-area scale the upright head and upper
wings intersect the low Agar laboratory ceiling. Death flames/remains work, but this is not a clean indoor silhouette pass.
No collision-system or per-map scaling changes were made. Posture/proportions await user artistic acceptance.

Historical v3 reproduction: `prepare_upright.py` → `animate_drake.py` → `refresh_selected.py` → `build_lods.py` →
`finish_runtime.py` → `viewer_tiers.py` → `update_viewer_manifest.py` → installer → validators.
`work/checkpoint_v2/` preserves the previous accepted head/neck and pre-upright delivery.

## Earlier repairs (v2)


Removed 21 disconnected Meshy sliver tips at the chest/forelegs and five failed forearm fins, then closed local holes.
The overlapping neck stubs were cut away and replaced with a connected, weighted loft. The lower head neck now shares
continuous body UV coverage; this follows the shared Hydra head-graft method rather than hiding an intersecting collar.

The original Meshy textures were 2K but v1 composition/export reduced them to 1K. Dedicated body/neck and wing close
references now guide new 4K body/wing returns; the final model uses **three separate 2K PBR sets** for body, head and wings,
plus 2K region masks. Head source remains 2K. Body/head skin and gold were matched; good membrane detail is transferred to
both wing surfaces. Meshy painted an unwanted mouth on the cut neck; continuous lower-neck detail replaces that patch.
Original returns remain unchanged under `meshy/`.

Death now spreads animated orange flames across the head, wings, torso and tail. Wings, limbs and tail burn away in stages
before the small charred horned remains settle. These flames are included in the viewer and game; existing game
`disintegration` sparks remain additive. The implementation uses animated transparent flame cards and skeletal contraction,
not a per-pixel dissolve shader or exact native-frame reproduction. It adds no renderer code.

## Selected delivery

- `export/mm6_drg1.blend`: selected packed editable master, including repaired motion and materials.
- `export/mm6_drg1_runtime_lod0.glb`: portable animated LOD0.
- `export/mm6_drg1.glb`: runtime source with three palette variants, four colour LODs and shadow LODs.
- `assets_source/worlds/mm6/models/mm6_drg1.glb`: authoritative installed source.
- `assets_dev/worlds/mm6/models/mm6_drg1.glb`: processed runtime copy from `tools/install_model.py`.
- `textures/drg1_ramps.json`: native palettes 692/693/694; body/head/wings remain separate.

Current authored body LODs: **14,488 / 8,182 / 4,083 / 2,560 triangles**; runtime counts including backface copies:
**14,977 / 8,489 / 4,361 / 2,639**. 36 joints, three separate 2K PBR sets and three 1K burn maps. No flame-card mesh.

Historical v2 reduction (superseded by the v7 ladder above): 18,881 → 16,992 passed; the next 15,293 step increased maximum deformed-surface error
from 3.92 to 8.96 mm in Attack and 4.84 to 15.51 mm in Death. Retained the first step; this is a conservative tested result,
not a mathematical minimum. Reports and preview renders are in `review/reduction/`.

Meshy consumed **90 / 100 credits**, including **40** for this repair. v2 body/wing textures were superseded by the selected
v3 returns; all receipts are preserved in `creature_3d_progress.json`. No more jobs are pending.

## Motion and game contract

Standing 1.125 s, Walking 1 s, Running 0.8333 s, Fidget 2 s, Attack/Cast 1.5 s, Hit 0.9167 s,
Death 2 s, Dead 1 s hold. Walking/running are in-place flight. Attack/Cast share the breath-release gesture.
Mouth socket `Socket_Mouth`, gameplay impact 0.9375 s. Scale 348.995968 uses the upright revision’s native flight-silhouette calibration;
B/C inherit native 2.7/2.8 versus A 2.5 tier scaling. Actor bindings remain in `assets_dev/worlds/mm6/models/actors.yml`.

## Earlier v2 verification

- All three tiers × nine clips: 27 viewer switches, zero browser errors.
- All nine clips played at 1× and ¼× with advancement checks and sampled visual review, including closeups and late Death.
  This is not continuous human video review. Evidence: `review/repair_v2/viewer/`.
- Isolated GLB reimport agrees with the Blender master across all clips and dense attack subframes: body maximum error
  below 0.000090 m; mouth socket and flame surfaces below 0.000001 m. See `review/export_parity.json`.
- Installed LODs, maps, weights, palette variants, flame material and preserved animation samples pass `review/delivery.json`.
- Focused native Drake actor regression: **1 pass / 0 fail** (`review/repair_v2/checks/regression.json`).
- NVIDIA OpenGL 3.3 desktop captures: all tiers outdoors (`oute3.odm`), green indoors (`6d19.blv`), alive, burning and remains.
  See `review/repair_v2/{outdoor,indoor}/`. First indoor tour lost console text input after spawning; removing an unnecessary
  count command allowed the complete rerun to pass. No game-code workaround was made.
- v1 fixed-camera native sprite comparisons remain in `review/ingame/`. Its broader MM6 actor suite recorded 51 pass / 3
  pre-existing unrelated mage/guard/ooze failures. That broader suite was not repeated for this asset-only repair.

Small pale shoulder markings remain in the generated skin texture. Appearance and the authored burning choreography remain
subject to user review. No engine changes, Vulkan builds or commits were made for this repair.

## Earlier v2 reproduction and checkpoints

`work/checkpoint_v1/` preserves the rejected delivery. Selected source/master hashes are in the canonical progress record.
Scripts target explicit revision checkpoints; do not run every historical script indiscriminately.

Repair geometry/UVs: `repair_drake.py` → `repair_uploads.py`.
Flames and motion: `add_death_flames.py` → `animate_drake.py`.
Retained Meshy UV/map transfer and bake: `repair_texture_uv.py` → `uv_raster.py` → `bake_ao.py` → `compose_drake.py`.
Full export/reduction: `export_drake.py` → `reduce_step.py`; selected refresh: `refresh_selected.py`.
Runtime: `build_lods.py` → `finish_runtime.py` → `viewer_tiers.py` → `update_viewer_manifest.py` → installer.
Then `export_parity.py`, `validate_delivery.py`, shared viewer check and native captures.
The selected packed master is authoritative; intermediate full exports predate the final membrane texture transfer.
Flame source, alpha-edge treatment and atlas settings are recorded in `work/death_flames.json`.
