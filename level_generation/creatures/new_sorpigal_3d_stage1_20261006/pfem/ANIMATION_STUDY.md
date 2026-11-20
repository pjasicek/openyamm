# MM6 female town peasant, pfem; descriptors 595–597: complete native animation study

[All-action native overview](guides/animation_overview.png) · [Anatomy guide](ANATOMY_GUIDE.md) · [Structured motion specification](motion_spec.json) · [Native inventory](source_inventory.json)

The native image is evidence; the hidden 3D reconstruction is a constrained hypothesis. These are semantic targets to fit after the actual mesh/rig exists. They are not animation files or measured original joint angles.

## Coordinate, timing and confidence contract

**Native Pixels:** x right, y down, full shared native logical canvas; frame offsets/pivot preserved. Character right appears image LEFT in frontal view. Existing original 2D seeds have provenance/confidence; restored-only seeds are excluded.

**Body Space:** Semantic anatomical X = character right, Y = forward, Z = up. Angles describe anatomy, never executable bone-local Euler channels. Map to actual bind matrices only after geometry and rig return.

**Angle Signs:** Elbow/knee 0 = straight, positive flexion; shoulder abduction 0 = arm down, 90 = side horizontal; forward elevation positive toward/front and overhead, negative behind. Trunk tilt positive forward, negative backward relative WORLD upright; lying tilt belongs mainly to root orientation, not local spine. Yaw positive toward character right. Wrist flex positive palm toward forearm; forearm axial roll solved from palm normal rather than assigning a sign without a bind pose.

**Seed Uncertainty:** All 3D values are inferred INITIAL fitting seeds/ranges: shoulder ±20°, elbow/knee ±15°, trunk/yaw ±10°, pelvis height delta ±0.03H. Hidden skirt joints may need a wider search. Native silhouettes and all genuine views override seeds. Seeds are not automated pass/fail tolerances or recovered forces.

**Hands:** Palm normal AND extended finger direction are constraints. Finger curl is proximal-flexion range, fan is separation; thumb opposed for grip. Preserve fixed segment lengths. Forearm roll changes palm plane, wrist flex remains modest. Depth/roll unresolved by frontal-only art stays low-confidence.

**Support:** Incoming contact windows and support-side assignment are extrapolation unless a shoe/sole clearly establishes contact. Logical canvas bottom is not automatically floor. Solve shoe trajectories against fitted body floor, then inspect profile/back with stable root progression.

All raw frame lengths here are 2: **125 ms per entry**, using 62.5 ms per raw unit. Standing/corpse metadata is 125 ms but the pose holds for the state duration. Walk/fidget loop at 750 ms; once-actions recover to standing except death, which reaches separate corpse at 625 ms. Male hit is only 625 ms.

Attack and hit/death/fidget supply one frontal bitmap per pose reused for all directions. Only standing and walking supply five genuine views. Directions 5/6/7 are mirrors of 3/2/1 and cannot establish new depth. A 3D rig preserves anatomical handedness when turned; do not imitate a mirrored sprite by swapping weapon hands.

## Family priorities

- Walk starts LEFT incoming foot, then RIGHT at d; visible shoes/profile hem guide hidden leg fitting.
- Folded hands in standing/fidget remain two separate palms; knife only in attack, left never confidently grips it.
- Abdominal hit uses right arm across body and left elbow out/wrist hanging; do not copy male face guard.
- Kneeling death and prone corpse need two hidden legs plus hollow skirt; contacts/knees are low-confidence inference.

## Native playback coverage

| Action | Entries | Duration | Behavior |
| --- | --- | --- |
| standing | 1 | 125 ms | hold |
| walk | 6 | 750 ms | loop |
| attack | 6 | 750 ms | once |
| hit | 6 | 750 ms | once |
| death | 5 | 625 ms | once |
| corpse | 1 | 125 ms | hold |
| fidget | 6 | 750 ms | loop |

Unused artwork remains in the source inventory, not playback: pfemfib0.
Pixel-identical images/holds are retained exactly: {}.

## Standing

[Unannotated native contacts](source/standing_native.png) · [Existing original 2D landmark overlay](guides/standing_landmarks.png)

**Source views:** front, front-right, right, back-right, back. 5/6/7 mirror 3/2/1; not extra depth evidence.

**Motion spacing:** Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.

**End rule:** hold current pose indefinitely.

### a — 0 ms: held folded hands

**Native frames:** pfemsta0, pfemsta1, pfemsta2, pfemsta3, pfemsta4. Hold 125 ms. Two hands overlap in front below belt; upright bodice and long skirt, shoes separate.

**Main driver:** Quiet held stance, hands lightly contact.

**Right chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Left chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Trunk/hips:** Chest upright, shoulders relaxed, waist above skirt folds. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support; hidden hips/knees inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Face front, chin neutral.

**Prop/visibility:** No knife visible; two hands must remain anatomically separate.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: held folded hands → hold current pose indefinitely. Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Walk

[Unannotated native contacts](source/walk_native.png) · [Existing original 2D landmark overlay](guides/walk_landmarks.png)

**Source views:** front, front-right, right, back-right, back. 5/6/7 mirror 3/2/1; not extra depth evidence.

**Motion spacing:** Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**End rule:** loop to first pose at 750 ms, keeping velocity/contact continuity.

### a — 0 ms: incoming first foot

**Native frames:** pfemwaa0, pfemwaa1, pfemwaa2, pfemwaa3, pfemwaa4. Hold 125 ms. Front shows incoming shoe/sole and opposite trailing foot; profile separates stride depth. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates.

**Main driver:** Pelvis progression and incoming hip swing lead; opposite arm balances.

**Right chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -5°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Left leg reaches forward; heel/flat-foot contact WINDOW, not proven exact plant; other leg trails/toe-off. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates. Initial R/L knee flex 25/15° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: incoming first foot → first support/passing. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: first support/passing

**Native frames:** pfemwab0, pfemwab1, pfemwab2, pfemwab3, pfemwab4. Hold 125 ms. Feet approach passing alignment; profile trailing heel lifted. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates.

**Main driver:** First support leg accepts weight; opposite hip begins forward swing.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -2°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Left foot supports, right heel lifts/pass begins; support assignment fitted across all views. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates. Initial R/L knee flex 40/8° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: first support/passing → opposite knee lift. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: opposite knee lift

**Native frames:** pfemwac0, pfemwac1, pfemwac2, pfemwac3, pfemwac4. Hold 125 ms. Opposite knee/shoe forward/up, support leg straighter; profile confirms bent swing leg. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates.

**Main driver:** Swing hip/knee flex lifts foot; pelvis modestly rises over support.

**Right chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 5°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Left supports; right knee bends and shoe clears floor; do not plant lifted foot. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates. Initial R/L knee flex 60/8° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: opposite knee lift → opposite incoming foot. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: opposite incoming foot

**Native frames:** pfemwad0, pfemwad1, pfemwad2, pfemwad3, pfemwad4. Hold 125 ms. Opposite leg forward/sole showing; first leg trailing in profile. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates.

**Main driver:** Opposite hip completes swing, pelvis advances, arms reverse continuously.

**Right chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 5°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Right incoming heel/flat-foot contact WINDOW; left toe-off/trailing, avoid long double-foot pins. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates. Initial R/L knee flex 15/25° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: opposite incoming foot → opposite support/passing. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: opposite support/passing

**Native frames:** pfemwae0, pfemwae1, pfemwae2, pfemwae3, pfemwae4. Hold 125 ms. Feet close again, trailing first heel raised; body crosses support. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates.

**Main driver:** Opposite support accepts weight; first hip swings forward.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 2°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Right supports; left begins swing, lifted heel/toe-off fitted to side/back views. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates. Initial R/L knee flex 8/40° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: opposite support/passing → first knee lift/loop prep. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: first knee lift/loop prep

**Native frames:** pfemwaf0, pfemwaf1, pfemwaf2, pfemwaf3, pfemwaf4. Hold 125 ms. First leg lifted/bent, opposite support; profile resolves swing shoe behind/under knee. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates.

**Main driver:** First hip/knee flex and forward swing prepare next contact, opposite arm travels forward.

**Right chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -5°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Right supports, left foot clears; through final 125 ms extend toward left incoming contact without foot slide. Skirt hides knee centers; shoe visibility and genuine profile hem guide inference, not measured knee coordinates. Initial R/L knee flex 8/60° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: first knee lift/loop prep → loop to first pose at 750 ms, keeping velocity/contact continuity. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Attack

[Unannotated native contacts](source/attack_native.png) · [Existing original 2D landmark overlay](guides/attack_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**End rule:** return to native standing at 750 ms.

### a — 0 ms: knife ready

**Native frames:** pfemata0. Hold 125 ms. Right knife low at character right; left hand near waist, head/torso incline slightly.

**Main driver:** Right arm releases folded-hand rest; modest right-side preparation.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Upper arm lowers near ribs; elbow remains bent, wrist returns in front of belt/waist. Initial abduction/forward elevation/elbow flex ≈ 12/30/75°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Small side lean, bodice front. World trunk tilt 3°, rib yaw 3°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Shoes remain near standing positions; hidden knees soft. Initial R/L knee flex 10/10° (±15°; hidden knees uncertain).

**Head:** Look toward blade/target with slight chin down.

**Prop/visibility:** Separate right-hand dagger visible; folded rest hand contact released.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: knife ready → low draw. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: low draw

**Native frames:** pfematb0. Hold 125 ms. Right arm/blade back and outward; left hand near hip, elbow out; torso leans toward right.

**Main driver:** Right shoulder draws back, waist/hips provide small windup; left arm balances.

**Right chain:** Shoulder retracts and turns outward; elbow low, wrist drawn behind/outside hip without overstretching. Initial abduction/forward elevation/elbow flex ≈ 35/-25/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Upper arm abducts sideways; elbow high/out, forearm hangs down/forward; wrist below elbow. Initial abduction/forward elevation/elbow flex ≈ 60/20/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Ribcage turns right modestly; pelvis less, skirt begins lag. World trunk tilt 8°, rib yaw 15°, pelvis height delta -0.020H (all inferred centers).

**Support/legs:** Both shoes supported; inferred knees flex, no large lunge. Initial R/L knee flex 20/20° (±15°; hidden knees uncertain).

**Head:** Head angled down/right toward preparation.

**Prop/visibility:** Blade low/down at right side, fixed grip.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: low draw → foreshortened reach. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: foreshortened reach

**Native frames:** pfematc0. Hold 125 ms. Right forearm reaches toward viewer at belt/chest; left arm opens low to side.

**Main driver:** Clavicle advances and elbow opens; rib turn follows, skirt lags.

**Right chain:** Clavicle protracts; upper arm points toward viewer; elbow opens, forearm foreshortens, wrist ahead of torso. Initial abduction/forward elevation/elbow flex ≈ 20/75/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Chest begins turning left, pelvis closer to front. World trunk tilt 8°, rib yaw 0°, pelvis height delta -0.020H (all inferred centers).

**Support/legs:** Both feet support with small forward weight shift; knees hidden. Initial R/L knee flex 20/20° (±15°; hidden knees uncertain).

**Head:** Gaze toward reach, chin down slightly.

**Prop/visibility:** Short frontal wrist/blade projection means depth uncertainty, not shorter arm.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: foreshortened reach → cross-body sweep. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: cross-body sweep

**Native frames:** pfematd0. Hold 125 ms. Right arm extends character left at chest height, blade up/right in image; head/bodice turn left.

**Main driver:** Torso yaw and right shoulder sweep knife laterally, elbow opens to reach.

**Right chain:** Shoulder reaches across chest toward opposite side; elbow nearly opens; wrist traces lateral attack arc at chest/shoulder height. Initial abduction/forward elevation/elbow flex ≈ 25/80/20°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Quarter-turn left in ribs; waist less; skirt visibly twisted/full. World trunk tilt 8°, rib yaw -30°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Tiny shoe pivot allowed, no unobserved extra stride. Initial R/L knee flex 15/15° (±15°; hidden knees uncertain).

**Head:** Head turns/tilts with chest, eyes along reach.

**Prop/visibility:** Left hand stays out of blade arc, no second-hand grip.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: cross-body sweep → cross-body retraction. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: cross-body retraction

**Native frames:** pfemate0. Hold 125 ms. Right elbow folds, blade remains diagonal; torso/head still left, left hand low.

**Main driver:** Elbow retracts then torso slows; hem continues slight lag.

**Right chain:** Shoulder remains turned across body; elbow folds to retract wrist toward opposite chest, without crossing forearm through ribs. Initial abduction/forward elevation/elbow flex ≈ 20/55/75°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Left rib yaw held then unwinds, pelvis modest. World trunk tilt 6°, rib yaw -25°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Both shoes retain support, knee flex inferred. Initial R/L knee flex 10/10° (±15°; hidden knees uncertain).

**Head:** Head remains down/left, follows torso rather than snapping front.

**Prop/visibility:** Knife remains separate from forearm/bodice.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: cross-body retraction → hands toward waist. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: hands toward waist

**Native frames:** pfematf0. Hold 125 ms. Right blade/hand lowered in front; left hand approaches without proven grip; body upright/front.

**Main driver:** Right shoulder lowers, left arm returns toward folded-rest region.

**Right chain:** Upper arm lowers near ribs; elbow remains bent, wrist returns in front of belt/waist. Initial abduction/forward elevation/elbow flex ≈ 12/30/75°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Trunk/hips:** Torso re-centers, skirt untwists and settles. World trunk tilt 0°, rib yaw -3°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Shoes grounded, knees relax. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Head front, chin neutral.

**Prop/visibility:** Knife still visible; disappearance/rest hand contact occurs after 750 ms.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: hands toward waist → return to native standing at 750 ms. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Hit

[Unannotated native contacts](source/hit_native.png) · [Existing original 2D landmark overlay](guides/hit_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**End rule:** return to native standing at 750 ms.

### a — 0 ms: abdomen clutch

**Native frames:** pfemwia0. Hold 125 ms. Right forearm crosses abdomen; left hand low/front; chin bows.

**Main driver:** Abdominal fold starts, right arm guards midsection.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Ribs lean forward, waist lowers slightly. World trunk tilt 15°, rib yaw 0°, pelvis height delta -0.015H (all inferred centers).

**Support/legs:** Both shoes support; knee flex hidden under skirt. Initial R/L knee flex 15/15° (±15°; hidden knees uncertain).

**Head:** Chin down, head follows trunk.

**Prop/visibility:** Empty hands, no blade.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: abdomen clutch → fold with left elbow out. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: fold with left elbow out

**Native frames:** pfemwib0. Hold 125 ms. Deeper fold, right hand central; left elbow high/out, wrist hanging forward/down.

**Main driver:** Spine/hip flex deepens; left arm lifts elbow for balance.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Upper arm abducts sideways; elbow high/out, forearm hangs down/forward; wrist below elbow. Initial abduction/forward elevation/elbow flex ≈ 60/20/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Ribs fold over waist, shoulder asymmetry. World trunk tilt 30°, rib yaw 5°, pelvis height delta -0.055H (all inferred centers).

**Support/legs:** Infer knee flex from overall height, not a visible knee landmark. Initial R/L knee flex 35/35° (±15°; hidden knees uncertain).

**Head:** Head bows toward abdomen.

**Prop/visibility:** Left wrist flex modest; hanging hand does not imply broken wrist.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: fold with left elbow out → deepest abdominal recoil. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: deepest abdominal recoil

**Native frames:** pfemwic0. Hold 125 ms. Head low, right forearm across abdomen, left elbow high; skirt broadens.

**Main driver:** Hip/knee fold and trunk flex lower head; arms preserve guard shape.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Upper arm abducts sideways; elbow high/out, forearm hangs down/forward; wrist below elbow. Initial abduction/forward elevation/elbow flex ≈ 60/20/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Deep forward fold, body height reduced by joints/root rather than scaling. World trunk tilt 50°, rib yaw 5°, pelvis height delta -0.120H (all inferred centers).

**Support/legs:** Shoes remain at base; knees hidden, choose collision-free 50–80° fit. Initial R/L knee flex 60/60° (±15°; hidden knees uncertain).

**Head:** Head down, chin toward ribs, neck still full length.

**Prop/visibility:** Skirt bends/broadens independently of leg chains.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: deepest abdominal recoil → begin unfolding. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: begin unfolding

**Native frames:** pfemwid0. Hold 125 ms. Right forearm still at waist, left elbow/wrist still lifted/dangling; torso starts up.

**Main driver:** Knee extension starts under maintained abdominal guard.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Upper arm abducts sideways; elbow high/out, forearm hangs down/forward; wrist below elbow. Initial abduction/forward elevation/elbow flex ≈ 60/20/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Forward fold decreases, shoulder asymmetry retained. World trunk tilt 35°, rib yaw 3°, pelvis height delta -0.085H (all inferred centers).

**Support/legs:** Both supports, knees gradually extend below skirt. Initial R/L knee flex 45/45° (±15°; hidden knees uncertain).

**Head:** Head remains bowed, no premature gaze lift.

**Prop/visibility:** Hem lags rise, no instantaneous rigid skirt reset.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: begin unfolding → release arms. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: release arms

**Native frames:** pfemwie0. Hold 125 ms. Hands lower/separate, torso rises; head still partly bowed.

**Main driver:** Trunk unfolds and shoulders release guard after leg recovery.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Forward tilt reduces, shoulders descend. World trunk tilt 15°, rib yaw 0°, pelvis height delta -0.025H (all inferred centers).

**Support/legs:** Both shoes support, knees approach relaxed stance. Initial R/L knee flex 20/20° (±15°; hidden knees uncertain).

**Head:** Chin rises slowly.

**Prop/visibility:** No hand merge against skirt.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: release arms → upright recovery. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: upright recovery

**Native frames:** pfemwif0. Hold 125 ms. Nearly upright, hands low/front, head faces forward.

**Main driver:** Body settles; hands return toward folded rest during final interval.

**Right chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Chest upright, waist stable. World trunk tilt 2°, rib yaw 0°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Both supports, hidden knees softly bent. Initial R/L knee flex 8/8° (±15°; hidden knees uncertain).

**Head:** Face front.

**Prop/visibility:** Reconnect folded hands at 750 ms only with preserved finger clearance.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: upright recovery → return to native standing at 750 ms. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Death

[Unannotated native contacts](source/death_native.png) · [Existing original 2D landmark overlay](guides/death_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**End rule:** reach separate corpse at 625 ms; last death anchor remains at 500 ms.

### a — 0 ms: abdominal collapse starts

**Native frames:** pfemdea0. Hold 125 ms. Head bows, right forearm crosses waist, left elbow flares.

**Main driver:** Rib/hip flex initiates collapse.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Upper arm abducts sideways; elbow high/out, forearm hangs down/forward; wrist below elbow. Initial abduction/forward elevation/elbow flex ≈ 60/20/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Forward fold, waist slightly lowers. World trunk tilt 25°, rib yaw 3°, pelvis height delta -0.040H (all inferred centers).

**Support/legs:** Both shoes initially support; knees unseen. Initial R/L knee flex 25/25° (±15°; hidden knees uncertain).

**Head:** Head down toward chest.

**Prop/visibility:** No knife; skirt covers both legs.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: abdominal collapse starts → deep fold. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: deep fold

**Native frames:** pfemdeb0. Hold 125 ms. Head lower, right arm guards abdomen, left elbow up/out; skirt expands.

**Main driver:** Hip/knee flex lowers body while ribcage folds.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Upper arm abducts sideways; elbow high/out, forearm hangs down/forward; wrist below elbow. Initial abduction/forward elevation/elbow flex ≈ 60/20/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Strong forward bend, shoulders rounded. World trunk tilt 45°, rib yaw 3°, pelvis height delta -0.100H (all inferred centers).

**Support/legs:** Inferred knees flex; shoes need coherent contacts. Initial R/L knee flex 55/55° (±15°; hidden knees uncertain).

**Head:** Chin toward ribs; nape hair follows head.

**Prop/visibility:** Do not draw hidden knees as recovered evidence.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: deep fold → crouched buckle. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: crouched buckle

**Native frames:** pfemdec0. Hold 125 ms. Body shorter/wider, head low, left elbow out, skirt bulges over knees.

**Main driver:** Knees buckle toward kneeling; hip/root descends.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Upper arm abducts sideways; elbow high/out, forearm hangs down/forward; wrist below elbow. Initial abduction/forward elevation/elbow flex ≈ 60/20/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Root lowers as spine stays folded; retain torso volume. World trunk tilt 55°, rib yaw 0°, pelvis height delta -0.200H (all inferred centers).

**Support/legs:** Hidden knees may approach floor; exact side/phase unresolved. Initial R/L knee flex 90/90° (±15°; hidden knees uncertain).

**Head:** Head down, modest neck flex.

**Prop/visibility:** Skirt hem spreads, still a hollow cloth shell.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: crouched buckle → kneeling descent. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: kneeling descent

**Native frames:** pfemded0. Hold 125 ms. Low kneeling silhouette, right arm across lap, left hand moving down/front.

**Main driver:** Pelvis drops toward knees; shoulders send hands toward floor.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Shoulder reaches forward/down as torso lowers; elbow opens softly, wrist approaches floor without arm extension beyond length. Initial abduction/forward elevation/elbow flex ≈ 20/80/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Forward trunk, root low; no leg shortening. World trunk tilt 50°, rib yaw 0°, pelvis height delta -0.300H (all inferred centers).

**Support/legs:** Knee/floor supports inferred; feet shift under skirt collision constraints. Initial R/L knee flex 115/115° (±15°; hidden knees uncertain).

**Head:** Head follows forward fold.

**Prop/visibility:** Hem contacts floor and spreads around leg volumes.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: kneeling descent → hands to floor. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: hands to floor

**Native frames:** pfemdee0. Hold 125 ms. Both hands low toward ground ahead, head between arms, skirt spread wide.

**Main driver:** Shoulder/elbow reach catches forward descent; hips/root continue settling.

**Right chain:** Shoulder reaches forward/down as torso lowers; elbow opens softly, wrist approaches floor without arm extension beyond length. Initial abduction/forward elevation/elbow flex ≈ 20/80/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Left chain:** Shoulder reaches forward/down as torso lowers; elbow opens softly, wrist approaches floor without arm extension beyond length. Initial abduction/forward elevation/elbow flex ≈ 20/80/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Forward/down root orientation; transition toward prone remains. World trunk tilt 65°, rib yaw 0°, pelvis height delta -0.360H (all inferred centers).

**Support/legs:** Knees and palms can support briefly; hidden contact chosen as inference. Initial R/L knee flex 120/120° (±15°; hidden knees uncertain).

**Head:** Head near floor between hands, hair stays attached.

**Prop/visibility:** Palm normals down, fingertips forward; preserve wrist/forearm continuity.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: hands to floor → reach separate corpse at 625 ms; last death anchor remains at 500 ms. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs. Keep last observed pose at 500 ms and fit the hidden path to actual corpse at 625 ms; do not replace or skip either endpoint.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Corpse

[Unannotated native contacts](source/corpse_native.png) · [Existing original 2D landmark overlay](guides/corpse_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.

**End rule:** hold current pose indefinitely.

### a — 0 ms: held prone skirted remains

**Native frames:** pfemdef0. Hold 125 ms. Separate pfemdef0 is face-down low, arms forward/out; pale skirt spreads over legs.

**Main driver:** None; align death-to-corpse once, then hold.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Left chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Prone root near floor, body oriented to match diagonal native remains. World trunk tilt 90°, rib yaw -15°, pelvis height delta -0.420H (all inferred centers).

**Support/legs:** Chest/pelvis/forearms supported; leg arrangement occluded and inferred. Initial R/L knee flex 70/80° (±15°; hidden knees uncertain).

**Head:** Head near ground turned to visible native side, not a detached hair patch.

**Prop/visibility:** Dress covers two folded/extended leg chains; no added exposed legs.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: held prone skirted remains → hold current pose indefinitely. Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Fidget

[Unannotated native contacts](source/fidget_native.png) · [Existing original 2D landmark overlay](guides/fidget_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**End rule:** loop to first pose at 750 ms, keeping velocity/contact continuity.

### a — 0 ms: rest hold

**Native frames:** pfemfia0. Hold 125 ms. Playback repeats fia0 at 0 and 125 ms; fib0 is unused artwork.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Left chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Trunk/hips:** Chest upright, shoulders relaxed, waist above skirt folds. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support; hidden hips/knees inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No knife visible; two hands must remain anatomically separate.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–250 ms is a repeated native rest-pose hold. Do not add an intermediate gesture merely because playback has two entries.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: duplicate rest hold

**Native frames:** pfemfia0. Hold 125 ms. Playback repeats fia0 at 0 and 125 ms; fib0 is unused artwork. All supplied native views are pixel-identical to the 0 ms anchor; retain the same constrained pose.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Left chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Trunk/hips:** Chest upright, shoulders relaxed, waist above skirt folds. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support; hidden hips/knees inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No knife visible; two hands must remain anatomically separate.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 125–250 ms: duplicate rest hold → small face/head change. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable. Preserve identical source-pose constraints; no invented limb change between identical holds.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: small face/head change

**Native frames:** pfemfic0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Left chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Trunk/hips:** Chest upright, shoulders relaxed, waist above skirt folds. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support; hidden hips/knees inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No knife visible; two hands must remain anatomically separate.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 250–375 ms: small face/head change → held face variation. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: held face variation

**Native frames:** pfemfid0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Left chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Trunk/hips:** Chest upright, shoulders relaxed, waist above skirt folds. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support; hidden hips/knees inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No knife visible; two hands must remain anatomically separate.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 375–500 ms: held face variation → return expression. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: return expression

**Native frames:** pfemfie0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Left chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Trunk/hips:** Chest upright, shoulders relaxed, waist above skirt folds. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support; hidden hips/knees inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No knife visible; two hands must remain anatomically separate.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 500–625 ms: return expression → loop rest. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: loop rest

**Native frames:** pfemfif0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Left chain:** Upper arm close to ribs; elbow bends slightly outward, forearm diagonally inward to joined hands below belt. Initial abduction/forward elevation/elbow flex ≈ 15/20/40°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers diagonally down/inward, palm normal toward skirt/other hand; curl 15–35°, fan 0–8°, thumb slightly opposed. Retain two palms/digit sets and light contact without fused or interpenetrating hands.

**Trunk/hips:** Chest upright, shoulders relaxed, waist above skirt folds. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support; hidden hips/knees inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No knife visible; two hands must remain anatomically separate.

**Secondary surfaces:** Bodice follows ribcage; puff sleeves fold where shoulders rotate. Skirt is a separate hollow cloth surface with room for independent leg swing and kneeling; hem lags hips and broadens on collapse. Nape hair has restrained lag. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 625–750 ms: loop rest → loop to first pose at 750 ms, keeping velocity/contact continuity. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Rig and animation acceptance

Start with geometry comparison and the family stress poses in the anatomy guide. After receiving the rig, use stock walk/run only to diagnose weight collapse, crossed joints, arm-to-torso attachment and foot volumes. Then build native walking first, verify all five genuine views and the seam, repair weights, and construct the other six native states. Review every observed anchor and proposed midpoint, not only contact sheets.

A later review should retain native/3D side-by-side screenshots with the mismatched region highlighted, the time/view, cause (geometry, rig, weight, animation, prop or cloth) and fix/recheck evidence. Match camera and scale before declaring a shape defect. Do not tweak topology to conceal a wrong pose or retime the source to conceal failed interpolation. UVs and Meshy texturing follow accepted animation/deformation.

Numeric seeds and ambiguities are deliberately reviewable. Palms, hidden knees, contacts and corpse depth cannot be certified before a 3D model exists. No human artistic acceptance or model deformation pass is claimed here.
