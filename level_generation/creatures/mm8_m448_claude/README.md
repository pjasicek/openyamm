# MM8 Ratman — Claude humanoid production

Native family `m448`, descriptors 37–39: Ratman, Wererat and Greater Wererat. Production completed on 2026-10-15.
This is a separate 3D project; the existing `../mm8_m448/` sprite-restoration project is read-only reference.

## Selected deliverables

- [export/mm8_ratman.blend](export/mm8_ratman.blend): editable, packed body/head/sword master with all eight actions.
- [export/mm8_ratman.glb](export/mm8_ratman.glb): runtime body, three material variants, colour and shadow LODs.
- [export/mm8_ratman_sword.glb](export/mm8_ratman_sword.glb): separate rigid sword, attached to the `Sword` bone.
- `actors_ratman_binding.yml`: the three installed world-scoped bindings.
- [interactive viewer](http://127.0.0.1:8765/level_generation/creatures/mm8_m448_claude/review/viewer/): interactive tier/clip review, native source panel, exact-frame links.
- `creature_3d_progress.json`: canonical state, paid jobs, hashes, selected sources and completed checks.

Installed sources are `assets_source/worlds/mm8/models/mm8_ratman*.glb`; the installer cooks their runtime copies.
Do not copy an installed/cooked model back into this project.

## Source and appearance

165 native BMPs are recorded in `source/sources.json`. The standing visible height is 158 pixels, not its padded
256-pixel canvas. All three sprite scales are 1.0. The fitted standing body height is 1.469214 m, giving binding
scale 107.540462. Native palettes 449/450/451 change only the trousers: green, blue and maroon.

Five generated body masters, four head masters and an orthographic sword reference are preserved under
`references_hd/`, `references_head/` and `references_props/`, with prompts, inputs, selected revisions and hashes.
The model retains the hunched body, tapered rat muzzle, rounded ears, whiskers, two upper incisors, ragged grey
sleeveless shirt, leather pouch, shin wraps, three clawed toes, long tail and straight right-hand sword.
Four hand digits (three fingers and a thumb) are inferred from the partly occluded native hands.

Meshy expenditure: **35 credits** of the default 100-credit limit: body SmartTopology 5, head SmartTopology 5,
body auto-rig 5, body retexture 10, head retexture 10. No animation purchases. Originals and receipts remain in
`meshy/` and the canonical state. The selected rig is locally fitted, not the unmodified Meshy auto-rig.

## Geometry and animation

LOD0 has 14,759 triangles including the 136-triangle sword. Body LODs: 14,623 / 7,287 / 3,584 / 1,753;
sword LODs: 136 / 68 / 33 / 23. The main 6,900-triangle head surface is preserved. Reduction happens after
weighting; the first overprotected reduction was rejected for limb collapse. Duplicate faces were removed before
texture upload. The rig has fitted source frames, four influences per vertex, forearm/upper-arm twist helpers,
measured finger chains and an eight-bone tail. The tail settles beside the corpse.

| Role | Owned source | Duration | Adaptation |
|---|---|---:|---|
| Standing | Armed / ArmedIdle | 2.0 s | Native raised sword guard, hunched head, planted feet |
| Walking | Armed / ArmedWalk | 0.8 s | Forward weapon carry, tail sway; 1.53144 m measured stride |
| Running | Armed / ArmedRunForward | 0.8 s | Fixed-length leg fit, 5 cm pelvis bob; 3.43837 m measured stride |
| Attack | 1Hand / SwordAttackR1 | 1.63333 s | 0.83333 s lead-in; source slash stays at its own speed |
| Hit | Armed / ArmedGetHitF1 | 0.5 s | Ready-pose entry/recovery; below native 0.625 s limit |
| Fidget | Armed / ArmedIdleAlert1 | 2.0 s | Ready-pose entry/recovery |
| Death | Armed / ArmedDeath1 | 1.06667 s | Ready entry, controlled wrist, grounded collapse and falling tail |
| Dead | Final Death pose | 1.0 s | Exact held corpse |

The melee impact marker is 1.116667 s, within one 48 Hz frame of the native 1.125 s damage time. No gameplay
attack duration or damage logic is changed. Native attack slots both use Attack; there is no invented cast clip.
The sword edge is aligned with the tip's velocity at the measured impact. Native source timing is retained for
combat timing, while movement-driven 3D locomotion uses the selected source clips and measured strides.

## Textures

One 1K body set and one 1K head set merge losslessly into 2080×1024 runtime atlases with a 32-pixel gutter.
Only the trouser mask recolours; the head, fur, shirt, leather, teeth, claws and sword stay shared.
Material-class maps and AO are retained. AO grades the base colour; ORM red carries the per-class specular mask,
green roughness and blue metallic. Creature metallic is zero. Meshy normal maps are converted to glTF +Y by
`tools/prepare_actor_glb.py` before runtime processing.

Body UV transfer has unique face correspondence and maximum corner error below 0.001 mm. Head retexture preserves
our original UVs; 24,771 returned corners agree within 3e-8 UV units. Meshy omitted two very thin head triangles;
those retain their original UVs instead of taking a neighbouring triangle's chart. See `work/uv_transfer_*.json`.

## Verification and rebuild

`review/motion_gates.log`, `work/g4_ready.json`, `work/g6_contacts.json` and `review/export_parity.json` preserve the
numerical evidence. Maximum arm p99 stretch is 1.52×. The source attack itself has the measured fast 121.7° hand
step per 1/48 s; retargeting does not add a flip or slow the strike. No closed-body penetration is reported.
A few running hand/forearm samples come within 3 mm of open clothing/fur; close-up review is retained.
The viewer exercised all 24 tier/clip combinations, plus all eight actions at normal and quarter speed.
Export parity covers every clip, with dense fractional samples around impact; maximum surface error is 0.015 mm.

The reviewed intermediate is `work/rig_ready.blend`. `scripts/build_runtime.sh <lease-token>` rebuilds textures,
exports, normal convention, LODs, shadow meshes, variants, attachment split and head merge without paid calls.
Install the resulting body and sword with `tools/install_model.py ... --world mm8` after reviewing changes.
The earlier source-fit stages remain as project scripts and intermediate `.blend` files; do not restart Meshy jobs
when resuming material, animation or runtime work.

Desktop OpenGL 3.3 captures on the NVIDIA GPU (`0x10de`) verify the cooked runtime assets, all three tiers,
attachment and calibrated height. Outdoor pairs use New Sorpigal; indoor pairs use their native Smuggler's Cove
habitat. Identical camera/spawn setup and 0.05 simulation speed keep each comparison readable; AI-facing and gait
phases still vary. Normal-speed outdoor motion was also captured. Each successful run has a retained `run.json`
with binary/settings/save hashes and a concise capture log. The shared executable was rebuilt by concurrent
work between some runs; the reviewed Ratman source and cooked asset hashes stayed unchanged. These are visual checks, not performance benchmarks.

| Comparison | Model | Original sprite |
|---|---|---|
| New Sorpigal, all tiers | [3D](review/ingame/outdoor_3d/tiers.png) | [Sprite](review/ingame/outdoor_sprite/tiers.png) |
| Smuggler's Cove, all tiers | [3D](review/ingame/smugglers_3d/tiers.png) | [Sprite](review/ingame/smugglers_sprite/tiers.png) |
| Agar's Laboratory, front | [3D](review/ingame/indoor_3d/tiers.png) | Dynamic-spawn sprite setup did not render |

Agar's Laboratory initially omitted the dynamically introduced Ratman sprite family, including after a save/reload;
that failed setup is retained separately and is not counted as a successful sprite comparison. Smuggler's Cove
loads the family normally and supplies the completed indoor comparison. No sprite-loader changes were made.

The ordinary `openyamm` build passed. The Ratman actor regression checks all tiers, 158-unit height, sword node,
eight clips and unchanged simulation state. MM6 Goblin also passes. Full MM8-family results are retained in
[review/mm8_regression.log](review/mm8_regression.log); unrelated Pirate height and Centaur tier/socket expectations
failed during this run (five MM8 family cases passed, two failed). The headless model-test loader now loads authoritative monster frame families in addition
to the common table, matching the scale-reference data available to ordinary map loading.

The final prepared-normal viewer passed all 24 tier/clip switches without console errors. All eight motions were
played at normal and quarter speed; normal conversion does not change motion. Current face/hand captures are in
[review/viewer_final](review/viewer_final). Export/source contract checks pass, including normalized four-weight
skinning, palette masks, LOD budgets and exact installed-source hashes; cooked texture hashes are in
[review/installed_runtime.json](review/installed_runtime.json). After installation, run `scripts/verify_runtime.py --installed` under the workspace guard to recheck source identity.

Technical production is complete. User artistic acceptance is not recorded. Android was not tested; no Vulkan
build was run. The unrelated regression failures above remain outside this creature's changes.
