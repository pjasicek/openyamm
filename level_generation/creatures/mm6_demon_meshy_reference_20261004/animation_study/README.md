# MM6 demon — plans for the remaining native animations

[Interactive native/guide study](index.html) · [Machine-readable plan](animation_motion_spec.json) ·
[All 198 sample instructions](planned_frames.csv) · [Native audit](native_reference_audit.json).

This is an animation plan, following the format of the [Attack study](../attack_study/index.html).
No new Blender actions, effects, GLB exports or gameplay installation were made. The existing
[Attack revision 3](../attack_animation_v3/README.md), repaired rig and supplied locomotion are preserved.

## Native inventory and exact timing

Demon A is descriptor **502**, body palette **688**. Demon B/C use the same pose inventory with palettes
687/686. Descriptor bindings, frame order, timing and directional flags come from the preserved native
bindings in `mm6_dmn/sources.json` / `manifest.json`, cross-checked against
`assets_dev/engine/data_tables/monster_descriptors.txt`, `rendering/sprite_frame_data_common.yml`, and
`rendering/sprite_frames/monsters/m498.yml` for ash.

Each raw timing unit is eight 128-Hz ticks: **62.5 ms**, or exactly three samples at **48 fps**.
Anchors occur at frame-start times. The last observed pose occupies its full final hold. A smooth plan
interpolates toward the next anchor during each interval; that motion is inferred, whereas native playback
holds bitmaps. Endpoints are included for authoring; omit the duplicate endpoint when exporting loop sprites.

| Action / native group | Native order | Holds (ms) | Duration / 48-fps anchors | End behavior |
| --- | --- | --- | --- | --- |
| Standing / `danstda` | A | 125 | Static; metadata 125 ms / 0, endpoint 6 | Constant ready pose |
| Walk / `danwalka` | A B C D E F | 125, 187.5, 250, 125, 187.5, 250 | 1125 ms / 0, 6, 15, 27, 33, 42; endpoint 54 | F→A closes the loop |
| Hit / `danwnca0` | A B C D E(C) F(B) | Six × 125 | 750 ms / 0, 6, 12, 18, 24, 30; endpoint 36 | Hold B, then outgoing Standing blend |
| Fidget / `danfgta` | A B C D E(C) | Five × 125 | 625 ms / 0, 6, 12, 18, 24; endpoint 30 | Hold C, then outgoing Standing blend |
| Death / `dandtha0` | A B C D E F G H I | Seven × 125, two × 187.5 | 1250 ms / 0, 6, 12, 18, 24, 30, 36, 42, 51; endpoint 60 | Hold I, then separate ash |
| Remains / `m498x` → `m496xa` | A | Metadata 125 | Static / 0, endpoint 6 | Hold ash indefinitely |

Standing and Walk have five stored views: front, front three-quarter, profile, rear three-quarter and back.
Octants 5/6/7 mirror stored 3/2/1. Hit, Fidget and Death use `Image1`: one actual frontal view reused around
the actor. Ash has five stored images, but all five have identical RGBA pixels. Neither directional reuse
nor identical ash images supplies additional 3D motion evidence.

Attack2 aliases the completed Attack. There is **no native Running group** in this descriptor. The existing
Meshy Walking (50/48 s) and Running (32/48 s) are preserved presets with previous rig corrections, not exact
reconstructions of the 1125-ms native Walk. Author a separate `Walk_Native` action later; replacing either
supplied clip or deriving a faster run is a separate decision.

## Observed motion and proposed reconstruction

The page provides observed notes, movement instructions, support cautions and exact anchor jumps for every
native pose. JSON/CSV expand them to 198 sample states across the six plans, including static endpoints.

**Standing:** match the low long arms, hooked claws, small snarl, upright torso, broad stance and hanging tail
against all five stored directions. This is one held pose. Breathing, jaw cycling and tail swaying are optional
new animation, not present in the native standing group.

**Walk:** right and left strides alternate. Front A/B show the right foot lifted/forward, C the left trailing
foot raised; D/E reverse the forward side, F raises the right trailing foot. Profile confirms long stride
depth and bent trailing knees. The head/clasp are lower at B/E and higher at C/F. Low arms counter-swing;
the tail changes sides behind the legs. Fit all five directions at the same time positions. The 250-ms F
interval must continue into A, rather than become an endpoint pause. Exact stance intervals, ankle roll,
root speed and hidden heel contact require 3D fitting; these sprites do not measure forward travel.

**Hit:** hands rise B, then C opens the right arm down/out and raises the left forearm. D raises the left
hand above the shoulder, opens the right hand outward, tips the head back and extends the tail toward screen
right. The left foot visibly changes orientation/height while the right remains low. E and F repeat C and B
exactly. Do not lock both feet based on Attack's support rules, invent a large traveling knockback, or append
standing A inside the native duration.

**Fidget:** a restrained body dip, mouth opening and symmetrical outward hand gesture. D has the lowest
head/clasp and widest open hands. E repeats C. The stored `dmnfgtf0` equals B, but the descriptor never plays
it; adding F would incorrectly make this action 750 rather than 625 ms. Its outgoing recovery belongs after
the observed duration. No clear step or large turn is evidenced.

**Death:** the upright demon ignites around the feet, a warm plume climbs its legs, and C shows the last clear
upper body: backward head tilt, raised left hand and open right arm. D/E retain partial dark limb silhouettes
inside the plume; F/G no longer show a complete body. H and I reduce the plume to low remnants. This is
disintegration, not a fall into a prone corpse. Occlusion does not recover hidden joint positions or prove
when every hidden surface vanished. The plan separates visible A–C skeletal motion from subsequent body
visibility, warm plume, dark fragments and ash. Bright warm-colour envelope boxes are approximate segmentation
excluding the visible face area, not exact flame alpha or a recovered simulation. The later full-height plume
is retained; dim warm shading and dark fragments are outside this colour-only guide.

**Ash remains:** keep the body absent and use a separate dark ash asset/pose. `m498x` references `m496xa`
with fixed palette **496**, scale **1.75** and **Center**; the living/death body uses scale **0.699997**.
The study's common asset canvas does not reproduce those runtime scale/anchor semantics. Do not size the
ash by stretching a demon skeleton or assume its bottom-aligned study image defines its world placement.

## Rig authoring and deformation review plan

Start from the v3 `.blend` on a new isolated scene/package. Preserve rest coordinates, connectivity, weights,
bind matrices and current Attack/Walking/Running curves. The model remains untextured and has no source UV layer.
It has four long claws plus a thumb per hand, while native frontal art exposes three plus thumb; pose the
existing anatomy without deleting digits or pretending this difference has been resolved.

1. Fit Standing against the five native views using one model scale and one camera per view, held fixed
   across each animation. Retain the corrected left-palm classifier based on actual claw-hook direction.
2. Fit source anchors before interpolating. Use `mixamorig:Hips`, Spine/Spine1/Spine2, Head, each
   Shoulder/Arm/ForeArm/Hand and UpLeg/Leg/Foot chain. Preserve the six `Demon_*_ForearmTwist*` helpers,
   repaired jaw hinge `Bone_025`, tail chain and rigid claw/foot weights. Never open the jaw through skull motion.
3. Solve fixed-length limbs with persistent elbow/knee poles and shortest continuous quaternion paths.
   Match palm normals from real hand/claw geometry, not a near-zero axis component. Distribute forearm
   twist; do not force every gesture to a front-facing palm. Inspect hands, all five supplied digits per hand,
   shoulders, elbows, knees, feet, jaw, head and tail independently.
4. For Walk, fit sagittal stride/contact from profile as well as front side alternation. Retain rigid talons;
   accommodate the source's lifted foot and trailing ankle orientation without reviving preset toe curl or
   uncontrolled planted-foot roll. Root/body bob must be solved through actual contact and fixed-length legs.
5. Review every keyed pose and dense subframes, especially raised Hit D, open Fidget D, Walk B/C/E/F and
   F→A. Planned quarter-frame sweeps are 217 Walk, 145 Hit, 121 Fidget and 241 Death times. Inspect front,
   both profiles, back and both three-quarter views; check upper-face rigidity, claw spacing, rigid tip edges,
   limb/core volume, body clearance, sole support and tail intersections. Numerical checks complement visual review.
6. Treat Death as skeletal motion plus a separate effect/visibility deliverable. An eventual portable GLB
   skeletal clip cannot alone express Blender particle systems or guarantee disappearance/ash switching.
   Choose and explicitly declare the target effect representation when authoring is requested; inspect the
   effect in the actual delivery format, including all nine anchors and death-to-ash transition.
7. Check exact durations, constant Standing/ash holds, Walk's loop seam and one-shot endpoints. Reimport
   the actual export and compare evaluated mesh motion. Record local technical/visual review separately
   from user artistic acceptance. Engine installation is separate work.

The joint traces on the page are approximate image estimates (roughly ±8 px). Profile near/far traces do not
claim anatomical identities for hidden limbs. Landmarks disappear when occluded; no bones are invented within
the death plume. Curved claws, broader hands/feet, tail blade and other supplied proportions remain limitations.
The source canvas bottom is not an independently visible floor plane, so exact ground-contact proofs require
the eventual 3D geometry.

## Source and study validation

The study uses untouched native RGBA images from `mm6_dmn/native/`, aligned on the original 354×330 canvas
with pivot [177,330]. No enhanced art or AI-generated frames supply pose evidence. All 60 descriptor-referenced
remaining source BMP hashes match `sources.json`; decoding with the recorded palette and index-zero alpha,
then applying native offsets, reproduces those PNGs exactly. Demon BMPs come from the preserved MMerge source;
ash BMPs use their recorded existing source paths. The unused Fidget F original BMP is absent: its recorded
historical hash was not rechecked, and its PNG is verified only as an exact alias of B. This limitation does
not affect the five-frame playback sequence.

`native_*_aligned.png` contact sheets contain every stored view of the referenced actions at the same scale,
without fitting each image independently. Native direction mirrors are visible in the interactive page.
`native_reference_audit.json` records per-file hashes, original-source checks, palette, offset and alpha bounds.
The plan JSON records hashes of the untouched v3 Blender/GLB/review and previous Attack study page.

Rebuild the study with:

```sh
python3 level_generation/creatures/mm6_demon_meshy_reference_20261004/animation_study/build_study.py
node level_generation/creatures/mm6_demon_meshy_reference_20261004/animation_study/check_review.mjs
```

The builder performs source/timing/alias checks before writing the self-contained `index.html`, JSON, CSV and
contact sheets. `viewer.html` is its editable template. Browser validation checks source holds, mirrors,
endpoints, anchor controls, playback and small-screen layout; it does not validate any future 3D animation.
