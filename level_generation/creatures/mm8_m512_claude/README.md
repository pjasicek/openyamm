# MM8 Dire Wolf — Claude 3D production

Delivered 2026-10-15 using the shared [non-humanoid playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md).
Native family **m512**, descriptors **Dire Wolf A/B/C**, palette **512**. All three tiers share their
colouring; their original difference is size. Technical checks and agent visual review are complete.
User artistic acceptance has not been recorded.

## Review and files

- [Interactive review](http://127.0.0.1:8901/level_generation/creatures/mm8_m512_claude/review/viewer/):
  three sizes, eight clips, five native views, time/frame controls and normal/slow playback.
- [Portable GLB](export/mm8_wolf.glb), [packed editable Blender master](export/mm8_wolf.blend).
- [Installation receipt and hashes](delivery.json), [canonical progress](creature_3d_progress.json).
- [HD reference sheet](references_hd/selected_views_review.png), [native standing views](native/standing_sheet.png).

The viewer uses preview GLBs with the runtime colour ramp baked into their shared appearance. The installed
asset uses one shared texture set and three material variants. Preview files are not runtime sources.

## Native game comparison

Identical spawn positions and camera settings, native sprites on the left and final models on the right.
Each folder also contains approach, combat, hit, death and corpse captures, launch settings and logs.

| Place | Native sprites | Final 3D |
| --- | --- | --- |
| New Sorpigal | [Standing tiers](review/ingame/outdoor_sprite/tiers.png) | [Standing tiers](review/ingame/outdoor_model/tiers.png) |
| New Sorpigal | [Corpses](review/ingame/outdoor_sprite/corpses.png) | [Corpses](review/ingame/outdoor_model/corpses.png) |
| Agar's Laboratory | [Standing tiers](review/ingame/indoor_sprite/tiers.png) | [Standing tiers](review/ingame/indoor_model/tiers.png) |
| Agar's Laboratory | [Corpses](review/ingame/indoor_sprite/corpses.png) | [Corpses](review/ingame/indoor_model/corpses.png) |

Outdoor camera: `(-3718.493, 3245.946, 1)`, yaw `3.359`, pitch `-13.751°`.
Indoor camera: `(1672.832, -2938.578, -46.896)`, yaw `3.132`, pitch `-14.868°`.
Captures use the authorized desktop launcher and native engine readback: OpenGL 3.3, NVIDIA, Wayland, 1600×900.
They are visual checks, not a GPU performance benchmark.

Agar's Laboratory does not preload this MM8 sprite family for debug spawns. Its native comparison therefore
uses an isolated asset fixture with the three wolf frame groups appended to the common frame table.
The fixture keeps the original map, textures, camera and actors. No production map or sprite table was edited.
`scripts/prepare_sprite_fixture.py` recreates that fixture and snapshots only the three wolf model bindings,
so concurrent creature installations cannot invalidate the comparison. The fixture is temporary.

The final [Dire Wolf Den capture](review/ingame/wolf_den/native_placed_wolves.png) shows native placed wolves
using the normal MM8 asset root and automatic model-manifest selection, without a manifest override.

## Model and materials

The complete wolf body includes its muzzle, lower jaw, teeth, ears, four paws/claws, hackles and bushy tail.
There is no carried equipment. A fitted 24-bone quadruped rig uses at most four influences per vertex.
The retained first reduction step preserves the silhouette and muzzle; the next step lost too much surface detail.
[Reduction evidence](review/reduction/selected.json) records that choice.

| Colour LOD | Triangles | Shadow LOD triangles |
| --- | ---: | ---: |
| 0 | 14,201 | 14,201 |
| 1 | 7,100 | 7,100 |
| 2 | 3,550 | 3,550 |
| 3 | 1,767 | 1,767 |

One 2048² albedo and 1024² normal, metallic/roughness and region-mask maps serve every tier. Head UV density
is 2.5 times the body density. Native palette samples establish the fur and green eyes. AO is composed into
albedo; the MR red channel also retains it, but runtime specular is disabled. Metallic is zero. Fur roughness
is 0.84, with separate eye, teeth, claw, nose and mouth classes. The normal-map green convention was measured
and corrected. [Texture correspondence](work/texture_correspondence.json) verifies exact returned UVs and
normalised surface correspondence before map transfer to the retained animated mesh.

Native standing alpha height is 79 pixels. A's native scale is 2.0, giving 158 world units. The measured model
height gives binding scales **237.39035345 / 272.99748212 / 320.47662107** (ratios 1 / 1.149994 / 1.3499985).
Explicit native-derived scales avoid depending on which sprite families a map has loaded.
See [calibration](work/scale_calibration.json).

## Motion

| Clip | Seconds | Notes |
| --- | ---: | --- |
| Standing | 2.000 | Loop; low ready posture, restrained breathing and tail motion |
| Walking | 1.000 | Loop; native period, planted diagonal gait, stride 0.34 m |
| Running | 0.625 | Loop; faster procedural gait, stride 0.48 m |
| Attack | 1.125 | Leaping bite (2026-10-18, `../mm8_wolf_reduce_claude/scripts/attack_v2.py`, replaces the rising lunge of `animate_wolf.py`): crouch, rear-up, leap, bite in the air at the native 0.875 s impact, front-first landing |
| Hit | 0.625 | Native-duration rear/recoil |
| Death | 0.625 | Native-duration rear, roll and limb settling |
| Dead | 1.000 | Static loop matching the death endpoint |
| Fidget | 0.625 | Native-duration alert motion |

These are smooth, native-inspired 3D motions, not exact sprite-frame reconstructions. Running is an adaptation
of the native walking action. The two native attack slots share the bite; this creature has no cast or missile
socket requirement. Runtime head look uses Neck1/Head within 30° yaw and 20° pitch.

The correction record covers the low initial crouch, jaw hinge/weights, mane ownership during foreleg movement,
front-view lower-jaw straightening and final corpse settling. A final native-game comparison prompted the corpse
repair; the upper legs now fold down during the last 0.325 seconds of collapse.

## Verification and limits

- [Actual final GLB checks](work/runtime_export_checks.json): all eight clips and all eight colour/shadow meshes
  sampled at 96 Hz; finite skinning, loops, stretch and floor tolerance passed. No degenerate triangles.
- [Authoring/export parity](work/export_parity.json): all clips and fractional frames; maximum error under
  0.000004 m. [Empty-scene Blender reimport](work/reimport.json): 24 bones and all eight actions present.
- [Viewer checks](review/viewer_check.json): all 24 tier/clip switches passed, no console errors.
- Live browser playback was sampled at 1× and 0.25×. The complete textured pass is preserved in
  `review/textured_playback_before_jaw_repair`; affected jaw clips were revisited in
  `review/textured_playback_after_jaw_repair`, and corrected Death/Dead in `review/pilot_playback`.
  These are timed samples of real playback, not a continuous video recording.
- Ordinary `openyamm` build passed. The new
  `mm8_wolf_actor_models_keep_native_sizes_and_roles` regression passed with the installed assets in the isolated
  wolf-binding fixture. It checks shared asset/variants, LODs, clip timing, native size ratios and unchanged
  simulation state. The fixture's common frame table was restored before this regression, so the headless
  loader reads normal family definitions. [Isolated result](review/checks/isolated-regression.log).
  The same wolf test subsequently [passed with the normal MM8 assets](review/checks/current-regression.log).
- The broad actor suite did **not** pass in the current checkout: Dagger Wound actor/map assumptions failed
  after earlier map-switching tests, followed by `std::bad_alloc`. Isolated DWI checks passed 3/4; the remaining
  peasant friendliness assertion still failed. The grounding test passed alone. Later full-manifest checks
  were interrupted by concurrently installed creature bindings/assets. The final MM8-family run completed
  **5 passed / 2 failed**: wolf, ratman, dark elf, lizardman and smuggler passed; pirate standing height and centaur
  tier/socket checks failed. [Final MM8 result](review/checks/mm8-final-regression.log). Earlier logs are in
  [review/checks](review/checks). Those families were not edited as part of this wolf.
- Android and Vulkan were not tested. No renderer changes or original sprite edits were made for this wolf.

The native sprite's coarse projection cannot uniquely determine hidden anatomy. The model preserves the crouch,
heavy hackles, pale legs, green eyes and raised tail while adding inferred detail. Final artistic judgement
belongs to the user; agent technical completion does not record artistic approval.

## Provenance and reproduction

Meshy consumed **15 of the 100-credit project limit**: 5 for Smart Topology (`smart_topology_v1`) and 10 for the
original-UV 2K retexture (`retexture_v1`). Requests, downloaded originals and hashes are preserved in the canonical
progress record and `meshy/`. Five selected HD references and all generation returns remain in `references_hd/`.
The original native inventory is in [source_inventory.json](native/source_inventory.json).

The selected geometry chain is `rig_v1.blend` → `anim_v1.blend` → reduction step 1 → `wolf_uv_master.blend` →
`repair_jaw.py` → `wolf_uv_repaired.blend` → `settle_corpse.py` → `wolf_uv_settled.blend`.
The original UV upload and Meshy returns remain unchanged. `export_wolf.py` starts from the settled master;
`build_runtime.py` adds LODs, shadow correction and material variants; `prepare_delivery.py` refreshes the viewer
and validates or appends only this family's bindings. Run project mutations through the ownership wrapper, and
Blender scripts through `tools/run_creature_blender.sh` with a newly claimed project token.

Installation uses `tools/install_model.py export/mm8_wolf.glb --world mm8` from the repository root with the
project path included. Its source is `assets_source/worlds/mm8/models/mm8_wolf.glb`; the current installer cooks
that source into `assets_dev/worlds/mm8/models/mm8_wolf.glb` and shared runtime texture files. Do not edit or
copy the cooked model back into the source. Runtime bindings are in `assets_dev/worlds/mm8/models/actors.yml`.

No changes were staged or committed.
