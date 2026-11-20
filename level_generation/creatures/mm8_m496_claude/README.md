# MM8 Fire Elemental — m496

Built and installed for all three tiers on 2026-10-18. **Appearance approval is pending.**
The prior approval covers the floating upper body and Djinn casting motion. The MM6 Fire Elemental supplies the
fire-effects technique, without treating its unapproved finished look as accepted.

[Interactive review](http://127.0.0.1:8912/level_generation/creatures/mm8_m496_claude/review/viewer/) ·
[Portable GLB](export/mm8_m496.glb) · [Packed Blender master](export/mm8_m496.blend) ·
[Canonical state and hashes](creature_3d_progress.json)

## Steady left hand follow-up — 2026-10-18

**User approved the flight correction with the steady left hand.** Finished appearance remains pending.

The leading left hand now keeps its orientation throughout Flying and Fast flight instead of rolling about 52°.
The shoulder cancels the inherited body pitch; the reach remains fixed while the body bobs and the legs move.
Other body joints and all seven non-travel motions are unchanged. Geometry, maps and skin weights are identical.
The prior revision is retained in `archive/pre_steady_left_hand/`.

All 674 gates, Blender reimport, 27 viewer combinations and the focused installed-model regression pass.
Current captures: [start](review/shots/steady_hand_start.png), [mid-cycle](review/shots/steady_hand_middle.png),
[side](review/shots/steady_hand_side.png). Full playback and native game captures below predate this follow-up;
no native visual rerun, Android or Vulkan checks were performed for it.

## Native flight correction — 2026-10-18

The user rejected the passive travel animation. **Flying** (`Walking`, 1.0 s) and **Fast flight** (`Running`, 0.8 s)
now use the native m496W silhouette: forward crouch, left fist reaching, right arm beside the body behind the hip,
right knee folded and the front/left leg moving up and down. The ordinary loop matches eight native 125 ms poses.
The viewer opens on Flying. The upright Standing hover and all non-travel motions retain their prior animation.

![Native views and corrected flight](review/native_flight/comparison.jpg)

`work/flight_preservation.json` verifies identical geometry, skin weights and maps, plus zero pose difference
across 17 samples of each of the seven unaffected clips, including casting. The reach is distributed through the
collarbone and arm; no skinning or appearance changes were needed. All 672 checks pass, including six explicit
flight checks per travel clip. Fresh OpenGL indoor/outdoor captures show eight phases from front, side and quarter;
normal/half-speed playback is refreshed. Older `review/ingame/` captures are the previous motion revision.

`scripts/revise_flight.py` reproduces this animation-only revision from the preserved `archive/pre_native_flight/`
master using `flight_pose` in `build_model.py`. Full builds use the same function. No Meshy work or engine changes.

![Three native-size tiers outdoors](review/ingame/outdoor_models/front.png)

The native m496 family has a red muscular full figure, pale yellow eyes, flame-wrapped limbs and crown,
a rising attack plume and an ash corpse. All 160 native frames were inventoried and hashed. Restored ×2 frames
provided the crown, palm plume and ash; the direct MM6 Fire tile provides the scrolling shell pattern.
No Meshy credits or image generation were used. Native legs and ash were retained; no Djinn costume or geometry
was copied. Source hashes are in `textures/provenance.json` and `work/djinn_motion.json`.

The model reuses the MPFB effect-body route and fitted Djinn rotations from MM8 Air. Its torso and complete
floating figure are skinned; fire envelopes, crown/limb fins and palm plumes follow the rig. The core is dark
red with baked shading/AO, while the blended unlit flame layer scrolls upward. Four shared maps serve all tiers.
The body atlas is 1040×1024: an isolated 16-pixel eye swatch beside the original 1024-square skin bake.
Effect UV repetition and the constant eye swatch are intentional; these unlit elemental materials use no PBR maps.

| Colour LOD | Total triangles |
| --- | ---: |
| 0 | 9,304 |
| 1 | 4,710 |
| 2 | 2,366 |
| 3 | 1,034 |

Only the opaque figure has the solid shadow LOD chain. There are no held props or clothing.
Descriptors 73–75 share palette 496, so no separate palette variants or recolour maps are needed. Scale is
95.5058209264; B/C use A as their native scale reference, retaining SFT scales 1.299988 / 1.75 / 2.0.
`work/calibration.json` matches the native 160-pixel standing silhouette to the mean full-detail Standing height.

Nine clips: Standing 3.0 s, Walking 1.0 s, Running 0.8 s, Attack/Cast 1.5 s, Hit 0.733333 s,
Fidget 2.4 s, Death 0.733333 s and Dead 1.0 s. The fitted release marker is 0.78 s; existing gameplay
owns the native combat clock. Both palms and eyes have sockets, and neck/head look remains enabled.
Death contracts the figure and flames into the native ash mound. Dead retains ash; the existing shared
corpse-to-loot transition subsequently dissolves rolled-loot corpses and displays a satchel.

Validation: ordinary build and focused engine regression passed; all 672 export/deformation checks passed;
independent Blender reimport matched 27 keyed/fractional samples within 0.000000897 m. The shared parity
helper was corrected to select the largest decoded mesh, matching its Blender selection: this model's first
mesh is Ash, whereas Body is largest. The viewer loaded all 27 tier/clip combinations without console errors.
Normal/half-speed recordings and sampled frames are in `review/playback/`. Native NVIDIA OpenGL captures
compare model/sprite tiers in New Sorpigal and Agar's laboratory, including LODs, live casting, hit and death.
Tours, run metadata and logs are retained beside the captures; production maps were never edited.
[Outdoor model/sprite comparison](review/outdoor_comparison.jpg) ·
[Wide indoor model/sprite comparison](review/indoor_wide_comparison.jpg).

Known visual limits: close views reveal the layered flame cards; there is no additive particle glow. The large native tiers
fill Agar's low room and leave close camera framing during flight; wider captures and the viewer cover them.
Artistic acceptance remains separate from these technical checks. Android, Vulkan, performance and unrelated
full-suite regressions were not tested.

Rebuild under this project's creature-workspace lease: Blender `scripts/build_figure.py`, then `retarget.py`;
system Python `make_textures.py`; Blender `build_model.py`; system Python `finish_runtime.py`; Blender
`audit_export.py` and `reimport_check.py`; system Python `make_viewer.py`. Use the reusable Blender and review
wrappers. Install `export/mm8_m496.glb` with `tools/install_model.py --world mm8`, then rerun the focused
`mm8_fire_elemental` actor regression and affected captures. `prepare_native.py` is initial bootstrap and resets
progress; do not rerun it on resume. Nothing was committed or repacked for Android/release.
