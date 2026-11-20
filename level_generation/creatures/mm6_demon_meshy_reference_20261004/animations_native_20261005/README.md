# MM6 demon: remaining native animations

Implemented on the delivered **Attack revision 3** mesh and repaired rig. Open [the review](index.html)
to compare original sprite holds with actual GLB renders, select Front/Profile, scrub every 48 fps sample,
play at full/half/quarter speed, or inspect each native anchor. The page also links all six GIFs and plates.

- [Editable Blender project](mm6_demon_native_animations.blend)
- [Complete animated GLB](mm6_demon_native_animations.glb)
- [Six-state overview](overview.jpg)
- [Native animation plan](../animation_study/index.html)
- [Numerical validation](validation.json) and [browser validation](browser_validation.json)

## Clips

| Clip | Native group | Duration | Playback |
| --- | --- | --- | --- |
| `Standing` | `danstda` | 125 ms metadata | One held pose; no invented idle cycle |
| `Walk_Native` | `danwalka` | 1125 ms | A–F, holds 125 / 187.5 / 250 / 125 / 187.5 / 250 ms; closes at frame 54 |
| `Hit` | `danwnca0` | 750 ms | A B C D C B; hold B at the end, outgoing Standing blend is external |
| `Fidget` | `danfgta` | 625 ms | A B C D C; hold C at the end, outgoing Standing blend is external |
| `Death` | `dandtha0` | 1250 ms | Upright disintegration A–I; H/I keep their 187.5 ms intervals |
| `Ash_Remains` | `m498x` → `m496xa` | 125 ms metadata | Separate ash mound, held indefinitely |

`Attack` (750 ms), `Walking` (1041.667 ms) and `Running` (666.667 ms) remain in both downloads.
Their mesh motion and animation curves are identical to revision 3. `Walk_Native` is the new native-timed
walk; it does not replace the preserved Meshy `Walking` clip. Attack2 uses Attack; the original family
does not contain a separate running animation. The descriptor excludes the stored F/B fidget alias.

## Walk corrections and tail

The native hand close-ups show changing claw silhouettes, including some occlusion. Walk articulates
the proximal fingers, changes their fan/curl and carries modest thumb motion; the hard claw tips remain
rigid. The native head close-ups show subtle tilt and eye changes. Authored yaw is ±2.5°, with restrained
pitch/roll; exact yaw cannot be recovered uniquely from the sprites.

The tail retains an arch behind the hips and a hanging distal curve. Five articulated segments use
50 / −45 / −25 / −25 / 10 degree bend controls, with small phased lag during Walk. The front-view tip
follows the native landmarks while depth is inferred behind the hips. Hit D raises the curved tail
toward screen right at waist height. Bone_020 retains its local transform to protect the belly/root.
Feet use fixed-length leg solves and whole-foot pitch; talons are not curled to imitate sole exposure.

## Death and remains

Death has 630 genuinely three-dimensional warm/dark tetrahedral fragments and nine native-envelope
morph targets. Warm/dark placement comes from the aligned A–I source pixels. Depth, individual fragment
shape and continuous motion are authored interpretations. This is a portable faceted effect rather
than a recovered flame simulation. The body remains intact in skeletal scale until it disappears
inside the plume at D, frame 18 / 375 ms. All 85 bones keep unit scale.

Binary presentation is carried by a separate `Demon_Body_Visibility` parent. The separate ash object
is visible only during `Ash_Remains`; it uses the native 1.75 / 0.699997 scale ratio. Death holds its low
I plume through the native endpoint. The caller selects Ash Remains afterward; no extra fade or corpse
transition has been inserted into the native clip duration.

GLB uses standard morph-weight animation and explicit STEP presentation-node scales. Every clip resets
body/ash visibility and plume weights. `normalize_export.py` writes the actual evaluated Death morph
samples and constant visibility states because Blender's NLA export dropped constant scales, sampled
STEP keys as LINEAR, and cached the shared Death KEY slot at one frame. It leaves the skeleton unchanged.
Export restores authored object transforms after sampling the singular visibility state.

## Editable project and reproduction

The project opens with Walk selected at frame zero. In Blender's Text Editor, choose the embedded
`SELECT_ANIMATION.py`, change `CLIP`, and Run Script. Space plays the selected action. One-shot actions
should be stopped at their endpoint or blended by the eventual caller; Blender's timeline playback
wraps if left running. All clips are also named NLA tracks, including synchronized effect/presentation
tracks on their respective owners.

The live authoring scene is `MM6_Demon_Native_Animations`; previous live scenes and revision packages
were preserved. `initialize.py` appends revision 3 once. `motion.py` reconstructs/bakes skeletal poses,
`prepare_effect_sources.py` prepares the native pixel arrays, and `effects.py` authors the portable effect.
The checkpoint, baked pose arrays and source hashes support further edits without touching revision 3.

The reusable runner has a saved command-prefix approval:

```sh
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_20261005/export_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_20261005/validate_package.py
tools/run_creature_blender.sh level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_20261005/render_previews.py
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/animations_native_20261005/build_review.py
```

Runner logs go to `/tmp/openyamm-creature-blender-<script>.log`. The approval covers Python scripts under
`level_generation/creatures/`; approval persistence is managed by the client. Blender's GLB importer puts
NLA strips at frame one, so export checks/previews select the imported actions directly to compare the
native sample-zero timeline correctly.

## Validation and scope

Validation checks the actual delivered project and an independent GLB reimport: 7899 body vertices,
15686 triangles, 85 joints, identical bind matrices/weights/topology, unchanged previous action curves,
dense quarter-frame floor clearance, rigid feet/claw tips, noncollapsed faces, unit bone scales,
curved tails, exact Walk closure, all nine clip durations and effect/visibility resets across transitions.
The browser check covers 396 frame/direction states, 28 anchor clicks, exact native source pixels,
all preview images, one-shot Death stopping, Walk closure and the separate Ash selection.

Four hundred actual GLB poses cover all new 48 fps front/profile samples and each native oblique anchor.
The preserved v3 body has no texture or UVs; clay review material and new effect/ash materials are supplied.
Appearance acceptance remains the user's review. Engine installation/rendering changes and gameplay
transitions are outside this asset-authoring package.

Source descriptor/BMP/palette verification is recorded in the [native audit](../animation_study/native_reference_audit.json).
The unused `dmnfgtf0` BMP was unavailable; its existing RGBA alias was checked and is not played.
