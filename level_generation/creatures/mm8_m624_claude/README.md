# MM8 Naga — m624

Completed 2026-10-18 for **Naga A/B/C**, monster IDs **169–171**: Naga, Naga Warrior and Naga Queen.
Technical completion and agent visual review are separate from user artistic acceptance in
[creature_3d_progress.json](creature_3d_progress.json).

[Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm8_m624_claude/review/viewer/) ·
[Packed Blender master](export/mm8_m624.blend) · [Portable assembly](export/mm8_m624_runtime_lod0.glb)

![Original sprites and models at matching cameras](review/ingame/comparison.jpg)

## Native identity and construction

The m624 sprites establish six arms, six different blades, a female torso, long brown hair, gold hoops,
cuffs and choker, a cream belly and brown-gold serpent scales. The native costume palettes are green,
blue-violet and dark red; all three tiers have the same frame scale. The original sprites remain unchanged.
[Native action inventory](references/native_actions.json), native sheets and five selected HD views preserve
this evidence. The generated side views have slight three-quarter yaw and serve as appearance guidance,
not metric joint templates. Hidden anatomy and fine facial detail are interpretations.

Meshy Smart Topology supplied the body. The three right hands were replaced with mirrored verified left
hands, with wrist cuts concealed beneath cuffs. The fitted rig has 121 bones: an articulated serpent chain,
torso/head, six independent arms with five articulated digits each, hair and rigid sword joints. Fingers
close around fitted handles; the six blades are separate static runtime attachments. They cannot bend with
skin deformation. Each pair uses a staggered attack phase to keep blades clear of the torso and other arms.
The final corpse retains one fixed pose.

| Property | Delivered value |
| --- | --- |
| Total colour LOD triangles, including swords | 14,737 / 7,366 / 3,680 / 1,833 |
| Body LOD0 | 12,785 triangles |
| Skin | 121 bones; maximum four normalized influences |
| Runtime materials | One merged body/head material per tier; shared rigid-weapon material |
| Maps | Body and head 1024² sets merged into 2080×1024 atlases; 128² weapon set |
| Palettes | Three region ramps on one geometry/rig/animation asset |
| Native calibration | 198 standing pixels × 1.199997 / 2.682440497 m |
| Runtime scale, all tiers | 88.575834680 world units/metre |
| Gameplay collision | Native height 160, radius 90; unchanged |
| Meshy expenditure | 25 of 100 credits: geometry 5, body texture 10, head texture 10 |

Body reduction protects hands, face and jewelry. The texture return omitted 12 interior/cut faces;
those faces receive an explicit nearest-surface bake in a reserved texture strip. Ordinary faces use matched
returned UVs. This exception is recorded in `work/body_uv_transfer.json`; it is not claimed as exact UV
carry-over for those 12 faces. The neck paint is blended across the material boundary, and the choker
continues across both atlases. Detached hair shards were removed while retaining the continuous hair shell.

Material classes distinguish skin/scales, matte hair/cloth, metal and eyes. The authored normal orientation
was checked before export. Native saturated gold is retained despite the material audit's dark-metal warning;
its indoor/outdoor appearance was inspected. The rigid weapons use steel blades, gold fittings and dark grips.
There are four colour and four shadow levels, with inset coarse shadow meshes.

## Motion and game binding

| Clip | Seconds | Behaviour |
| --- | ---: | --- |
| Standing | 3 | Restrained torso, hair and tail motion |
| Walk | 0.875 | Grounded serpent wave; 1.35 m stride |
| Running | 0.625 | Faster serpent wave; 1.75 m stride |
| Fidget | 2 | Small head/arm/tail adjustment |
| Attack | 1.75 | Left-back wind-up, right-front six-sword slash with staggered arm paths; impact at 1.0 s |
| Cast | 1.75 | Distinct inferred spell gesture; release at 1.0 s |
| Hit | 0.625 | Torso recoil and recovery |
| Death | 1.5 | Backward collapse with lower tail kept on the floor |
| Dead | 1 | Exact final death pose, held |

Native gait and hit timing are retained. Attack keeps the native one-second impact and adds visual recovery;
death/fidget are extended interpretations rather than frame-exact reconstructions. Cast is separately authored
for the native Blades spell. Both physical attack roles use Attack; the explicit cast role uses Cast, as required
by the existing runtime. Blade sockets support the release/glow events. Head look uses Neck/Head, limited to
22° yaw and 15° pitch. All keys are sampled at 24 fps with linear interpolation; the game needs no IK solver.

The first export used Blender curved interpolation. The final master and export use matching linear samples
and retain every baked key. Reimported body positions differ by less than 1 mm after the four-weight limit;
effect sockets agree within 0.003 mm, including subframes. [Export parity](review/export_parity.json).

## Installation and review

- The normal desktop build and focused `mm8_naga_actor_models_keep_six_weapons_palettes_and_motion`
  regression pass. It checks all three palettes, six correctly attached static swords, serpent/socket nodes,
  four colour levels, nine clip durations, native tier scales, bounded spell release and unchanged actor simulation state.
  [Build](review/build.log), [regression](review/regression.log).
- All nine clips pass half-frame contact checks against closed skin and torso query meshes. No blade/forearm
  penetration exceeded the 6 mm query tolerance. Maximum measured wrist swing is 45.19°, and Dead has no
  rotation drift. These sampled proximity checks supplement the visual review; they are not a continuous
  collision proof. [Blade checks](work/motion_gates.json), [limb checks](work/limb_contacts.json).
- The shared viewer passes all 27 tier/clip selections without browser errors. Normal and half-speed playback
  recordings, sampled playback sheets and close hand/head/tail views are retained in `review/playback/` and
  `review/close/`. Geometry and materials did not change during the final interpolation correction.
- Native OpenGL/NVIDIA captures cover New Sorpigal (`oute3.odm`) and Agar's Laboratory (`6d19.blv`), matching
  sprite/model cameras, forced LOD2, posed actions and ordinary hostile combat, hit, death and remains.
  [Run records](review/ingame/runs.json), [action overview](review/ingame/action-overview.jpg).
  Two outer indoor actors are partly hidden by columns; the centre actor supplies the clear indoor comparison,
  and all three palettes are visible outdoors.
- Installation uses `tools/install_model.py`: seven source GLBs and their cooked runtime models/textures.
  The Naga entries alone were added to the MM8 actor manifest. [Installation receipts](review/installation.json).

The native Blades projectile is also exercised explicitly from a spawned Naga in the outdoor review.
The final regression adds the launch-bound check; native captures retain the earlier pinned binary with the
same runtime code and assets. Only test coverage changed after that pin.

The review fixture hardlinks assets and detaches its two modified map scenes and manifest. Production maps
are unchanged. Captures use one pinned executable; mixed minimized/visible runs are not performance measurements.
The tour's direct console steps avoid timing-dependent SDL text focus. Two minimized Wayland launches
failed before asset loading; the visible retries passed. Android and Vulkan were not tested.
User artistic acceptance has not been recorded.

## Attack revision 2 — 2026-10-18

The user requested all six arms and swords to rise together with uneven timing, with the head and torso
leaning back, then release into a downward slash in front. The six wind-ups peak at 0.64–0.72 s and the
individual cuts finish at 0.96–1.07 s. The gameplay impact remains at 1.0 s, with recovery ending at 1.75 s.
The lower hands sweep outward during recovery to clear the middle fingers. Blades retain rigid construction.

[Normal playback](review/attack_r2/playback/Attack-1.webm) ·
[Half-speed playback](review/attack_r2/playback/Attack-0.5.webm) ·
[Close views](review/attack_r2/close/) · [Normal playback frames](review/attack_r2/normal.png)

The final 85 half-frame samples have no blade/complete-body or blade/blade surface intersections.
Closed skin/torso probes also pass, maximum wrist swing is 45.19°, and minimum sword clearance is 0.262 m.
The reimported Attack surface agrees with the master within 0.915 mm and blade sockets within 0.003 mm.
[Blade sweep check](review/attack_r2/swept_blades.json), [export parity](review/attack_r3/baseline/review/export_parity.json).

All eight other clips, every mesh attribute/index, material/image, rig node and the six static weapon files
are identical to revision 1. Actor bindings and production maps are unchanged.
[Scope check](review/attack_r2/scope_check.json). The previous master, exports and evidence are retained in
`review/attack_r2/baseline/`. The selected editable master, portable assembly, all runtime LODs, three viewer
tiers and installed body contain the revised Attack. No new Meshy credits were spent.

All 27 viewer selections and the focused Naga regression pass. Normal and half-speed recordings, front/side
close views and native posed/hostile-combat captures were reviewed indoors and outdoors using OpenGL/NVIDIA.
[Outdoor captures](review/attack_r2/native_out.jpg), [indoor captures](review/attack_r2/native_in.jpg),
[run records](review/attack_r2/runs.json), [regression](review/attack_r2/regression.log).
The indoor fixture's shared effect registry was detached and pinned to its original four imports after a
concurrent Wisp WIP import prevented initialization with the pinned binary. Production effects were untouched;
[fixture notes](review/attack_r2/fixture_refresh.json) retain both failed starts and the successful retry.
Android, Vulkan and performance were not rechecked. User artistic acceptance of this revision is not recorded.

To rebake this scoped revision, run `animate_naga.py --attack-only` on `work/textured_master.blend`, then
`export_asset.py`, `material_gate.py`, `build_lods.py`, `finish_runtime.py`, `viewer_tiers.py`, `setup_viewer.py`
and `install.py` through the existing guards/wrappers. `probe_naga.py --attack-only` (with/without `--limbs`),
`attack_review.py` and `export_parity.py` validate the revised motion. Viewer setup preserves existing feedback.

## Attack revision 3 — 2026-10-18

All six arms rise with the head and torso leaning toward her left and back, then cut down toward her right
and front. Slightly different arm heights, depth lanes, arcs and timing keep the motion coordinated without
mirroring the pairs. Anticipation peaks at 0.62–0.725 s, and individual slashes finish at 0.97–1.075 s.
The game impact stays at 1.0 s and recovery ends at 1.75 s. Stable elbow planes and continuous quaternion
signs remove the wrist flips; the first and last poses match the original resting pose within 0.001 mm.

[Open the viewer](http://127.0.0.1:8901/level_generation/creatures/mm8_m624_claude/review/viewer/) ·
[Normal playback](review/attack_r3/playback/Attack-1.webm) ·
[Half-speed playback](review/attack_r3/playback/Attack-0.5.webm) ·
[Close views](review/attack_r3/close/) · [Playback frames](review/attack_r3/normal.png)

The sweep check covers 169 poses at 96 Hz: no sword/sword, sword/body, sword/other-arm or free-arm
intersections. The original resting model already has touching skin at the attached R1/R2 shoulder caps;
these joins are retained and reported separately, restricted to upper-arm skin within 0.16 m of the shoulder.
Every raw contact remains in the report. This is sampled validation, not a continuous collision proof.
Maximum wrist swing is 44.46 degrees; both closed skin/torso probes pass with no contacts beyond their 6 mm
query tolerance. Minimum sword clearance is 0.278 m.
[Detailed sweep check](review/attack_r3/swept_blades.json), [body checks](review/attack_r3/motion_gates.json),
[limb checks](review/attack_r3/limb_contacts.json).

The reimported runtime Attack is checked at the same 169 times: body error is below 0.874 mm and blade
socket error below 0.003 mm. All eight other clips, mesh data, materials, images, rig nodes, inverse bind
matrices and six static sword files are identical to revision 2. Bindings and production maps are unchanged.
[Export parity](review/attack_r3/export_parity.json), [scope comparison](review/attack_r3/scope_check.json).
The retained master, portable assembly, runtime LODs, three viewer palettes and installed body all contain
this revision. The prior revision is preserved in `review/attack_r3/baseline/`. No new Meshy credits were spent.

All 27 viewer selections, 18 playback recordings and the focused Naga regression pass. The final poses and
ordinary hostile combat were visually checked indoors and outdoors on OpenGL/NVIDIA.
[Outdoor review](review/attack_r3/native_out.jpg), [indoor review](review/attack_r3/native_in.jpg),
[run records](review/attack_r3/runs.json), [regression](review/attack_r3/regression.log).
Native checks use the retained executable and the fixture's detached four-import effect registry;
[fixture details](review/attack_r3/fixture_refresh.json). Android, Vulkan and performance were not rechecked.
User artistic acceptance has not been recorded.

## Rebuilding the selected revision

Use the project lease and shared wrappers documented in the creature skill. Paid jobs and downloaded hashes
remain in the canonical progress record; rebuilding does not require another generation job.

1. Authoring: `prepare_naga.py`, `repair_hand.py`, `fit_anatomy.py`, `rig_naga.py`, `grip_naga.py`,
   `props_naga.py`, `animate_naga.py`.
2. UV/texture preparation: `texture_upload.py`, `transfer_body_uv.py`, `patch_maps.py`, `clean_hair.py`,
   `uv_raster.py`, `bake_ao.py`, `compose_texture.py`. Reuse the recorded body/head texture returns.
3. Delivery: `export_asset.py`, `material_gate.py`, `build_lods.py` (Blender), `finish_runtime.py`,
   `viewer_tiers.py`, `setup_viewer.py`, `export_audit.py`, `export_parity.py`, and both `probe_naga.py` modes.
4. Install with `install.py`. `deliver.py` is deliberately first-install-only; for revisions update the existing
   three Naga entries instead of appending duplicates. `prepare_reviews.py` and `action_tours.py` prepare the
   native capture fixture. Preserve user feedback before rebuilding the viewer setup.

Blender scripts run through `tools/run_creature_blender.sh`; ordinary Python mutations run through
`tools/creature_workspace.py run`. Selected outputs and hashes are in [review/artifacts.json](review/artifacts.json).
