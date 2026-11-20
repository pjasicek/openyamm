# MM6 Flying Demon: production study

This derivative preserves the selected walking-demon rig repairs but uses the Flying Demon native descriptors 499–501.
Standing, Walk and Fidget alias the same 0.750-second flight cycle; Attack and Attack2 alias one 0.750-second action. Hit lasts 0.750 seconds, Death 0.875 seconds, and the ash is held.

## Anatomy

- Wiry purple A / ochre B / dark-red C skin, grey segmented chest and abdomen.
- Large scalloped bat wings attach behind the shoulders separately from the arms.
- Curved ivory head horns, pale shoulder/forearm spikes and long curved talons.
- Small bright eyes: A cyan-blue, B amber, C orange; narrow hanging feet; no harness, clasp or visible tail in any stored view.
- Three long claw fingers dominate frontal sprites; obscured additional digits are not recoverable.

## Reconstruction choices

- Reuse the repaired demon face, jaw hinge, independent digits and forearm twist distribution.
- Remove connected tail at its attachment and close the local stump; remove clasp and raised harness profile.
- Slim arm/thigh/foot surfaces around their existing bind axes; retain chain lengths and joint centres.
- Retain four long fingers plus a thumb from the repaired source rig as an explicit obscured-depth inference. Native fronts clearly show three dominant long fingers; the additional finger is not recovered anatomy or a user-accepted deviation.
- Build curved struts and scalloped membranes with separate shoulder/elbow/finger wing controls.

## Flight

- 0.000s / frame 0: High-V wings; forearms hang; feet dangle. Begin recovery into the broad power stroke.
- 0.125s / frame 6: Wings spread widest near horizontal; chest lifts slightly; fingers loosely curled.
- 0.250s / frame 12: Downstroke: tips slope down/back, wings narrow in projection; body counters upward.
- 0.375s / frame 18: Lowest folded wing projection; legs trail, hands stay below waist, shoulders remain free.
- 0.500s / frame 24: Recovery stroke: elbows/wrists fold before the membrane rises, no walking foot contact.
- 0.625s / frame 30: High-V recovery into A; small body drop and delayed hanging feet complete the cycle.

## Attack

- 0.000s / frame 0: Ready in flight: wings high; both hands low; head watches target.
- 0.125s / frame 6: Windup: right fingers extend, right forearm opens; left hand stays partly hooked.
- 0.250s / frame 12: Both arms spread below shoulders, torso banks left; right claw sweeps outward, legs trail.
- 0.375s / frame 18: Right claw extends low/wide while left forearm rises beside chest; counter-rotation provides force.
- 0.500s / frame 24: Right claw crosses chest in a continuous inward/downward rake; left hand lowers and opens.
- 0.625s / frame 30: Both hands fall below waist, fingers curl; chest unwinds and wings recover toward flight A.

## Hit

- 0.000s / frame 0: Airborne ready pose before the impact; not a grounded brace.
- 0.125s / frame 6: Chest recoils, elbows spread, one wing banks higher; head starts tipping back.
- 0.250s / frame 12: Largest recoil: head back, arms wide/up; viewer-left wing high, viewer-right wing low; raised foot shows the sole toward the front.
- 0.375s / frame 18: Shoulders drop, torso starts recovery; unequal feet and wing tips lag behind the chest.
- 0.500s / frame 24: Arms settle below waist, fingers partially hook; head reorients toward the attacker.
- 0.625s / frame 30: Near-ready recovery; bank settles without a foot plant.

## Death

- 0.000s / frame 0: Airborne body visible; blue-white wisps start at shoulders/chest.
- 0.125s / frame 6: Upper chest brightens; arms rise as the chest recoils; wings still visible.
- 0.250s / frame 12: Peak recoil: arms spread, one leg kicks, bright central plume obscures chest.
- 0.375s / frame 18: Hands lower around the pelvis and wings droop while the plume obscures the chest. Body and wing surfaces remain present until source E at 0.500 s.
- 0.500s / frame 24: Body and both wings are absent; only the tall blue-white effect remains.
- 0.625s / frame 30: Effect contracts; no hidden skeletal recovery or falling intact body.
- 0.750s / frame 36: Tiny blue remnant fades to empty; next state is the shared static ash asset.

## Ash_Remains

One held low ash pile; five stored native views, no animated collapse. Presentation scale follows the native ash descriptor.


Depth and continuous motion are extrapolations. Source anchors are evidence, not permission to stretch bones to guessed screen coordinates. Palm roll uses a continuous forearm/palm orientation; fingers open during the outward windup and hook through the inward rake. Chest rotation initiates the rake and its opposite arm balances it. Wings have their own phase and fold during recovery. Body bob and delayed ankle motion keep the creature airborne.

Native contact sheets: `review/native_*.jpg`. Machine-readable timing and anatomy: `motion_study.json`. Appearance crop provenance: `references/provenance.json`.

The final authored values for all 89 joints at every source anchor are in [POSE_GUIDE.md](POSE_GUIDE.md) and [pose_manifest.json](pose_manifest.json). All digit, wrist/twist, elbow, shoulder, torso, head, leg, ankle and wing rotations are recorded. These are the selected extrapolation; hidden depth remains inferred.
