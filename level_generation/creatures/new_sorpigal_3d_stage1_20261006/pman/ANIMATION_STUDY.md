# MM6 male town peasant, pman; descriptors 607–609: complete native animation study

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

- Knife grip exists only in attack; compare shoulder-height cross-body reach, blade edge roll and free left guard.
- Hit has FIVE entries and returns to standing at 625 ms; unused wif0 must not become a sixth key.
- Deep hit guard: right forearm above brows, left open palm near face, right knee outward without leg stretch.
- Death is a side fall; separate corpse is prone. Explicitly fit the 500–625 ms transition instead of replacing death e.

## Native playback coverage

| Action | Entries | Duration | Behavior |
| --- | --- | --- |
| standing | 1 | 125 ms | hold |
| walk | 6 | 750 ms | loop |
| attack | 6 | 750 ms | once |
| hit | 5 | 625 ms | once |
| death | 5 | 625 ms | once |
| corpse | 1 | 125 ms | hold |
| fidget | 6 | 750 ms | loop |

Unused artwork remains in the source inventory, not playback: pmanfib0, pmanwif0.
Pixel-identical images/holds are retained exactly: {}.

## Standing

[Unannotated native contacts](source/standing_native.png) · [Existing original 2D landmark overlay](guides/standing_landmarks.png)

**Source views:** front, front-right, right, back-right, back. 5/6/7 mirror 3/2/1; not extra depth evidence.

**Motion spacing:** Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.

**End rule:** hold current pose indefinitely.

### a — 0 ms: held neutral

**Native frames:** pmansta0, pmansta1, pmansta2, pmansta3, pmansta4. Hold 125 ms. Both hands low in loose fists; feet apart, tunic/belt front, chin upright.

**Main driver:** No cyclic driver; quiet held stance.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Chest upright, shoulders modestly square. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes supported, knees almost straight but unlocked. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Face front, ordinary jaw relaxed.

**Prop/visibility:** No handheld knife visible.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: held neutral → hold current pose indefinitely. Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Walk

[Unannotated native contacts](source/walk_native.png) · [Existing original 2D landmark overlay](guides/walk_landmarks.png)

**Source views:** front, front-right, right, back-right, back. 5/6/7 mirror 3/2/1; not extra depth evidence.

**Motion spacing:** Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**End rule:** loop to first pose at 750 ms, keeping velocity/contact continuity.

### a — 0 ms: incoming first foot

**Native frames:** pmanwaa0, pmanwaa1, pmanwaa2, pmanwaa3, pmanwaa4. Hold 125 ms. Front shows incoming shoe/sole and opposite trailing foot; profile separates stride depth.

**Main driver:** Pelvis progression and incoming hip swing lead; opposite arm balances.

**Right chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -5°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Right leg reaches forward; heel/flat-foot contact WINDOW, not proven exact plant; other leg trails/toe-off. Initial R/L knee flex 15/25° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: incoming first foot → first support/passing. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: first support/passing

**Native frames:** pmanwab0, pmanwab1, pmanwab2, pmanwab3, pmanwab4. Hold 125 ms. Feet approach passing alignment; profile trailing heel lifted.

**Main driver:** First support leg accepts weight; opposite hip begins forward swing.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -2°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Right foot supports, left heel lifts/pass begins; support assignment fitted across all views. Initial R/L knee flex 8/40° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: first support/passing → opposite knee lift. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: opposite knee lift

**Native frames:** pmanwac0, pmanwac1, pmanwac2, pmanwac3, pmanwac4. Hold 125 ms. Opposite knee/shoe forward/up, support leg straighter; profile confirms bent swing leg.

**Main driver:** Swing hip/knee flex lifts foot; pelvis modestly rises over support.

**Right chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 5°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Right supports; left knee bends and shoe clears floor; do not plant lifted foot. Initial R/L knee flex 8/60° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: opposite knee lift → opposite incoming foot. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: opposite incoming foot

**Native frames:** pmanwad0, pmanwad1, pmanwad2, pmanwad3, pmanwad4. Hold 125 ms. Opposite leg forward/sole showing; first leg trailing in profile.

**Main driver:** Opposite hip completes swing, pelvis advances, arms reverse continuously.

**Right chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 5°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Left incoming heel/flat-foot contact WINDOW; right toe-off/trailing, avoid long double-foot pins. Initial R/L knee flex 25/15° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: opposite incoming foot → opposite support/passing. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: opposite support/passing

**Native frames:** pmanwae0, pmanwae1, pmanwae2, pmanwae3, pmanwae4. Hold 125 ms. Feet close again, trailing first heel raised; body crosses support.

**Main driver:** Opposite support accepts weight; first hip swings forward.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 2°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Left supports; right begins swing, lifted heel/toe-off fitted to side/back views. Initial R/L knee flex 40/8° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: opposite support/passing → first knee lift/loop prep. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: first knee lift/loop prep

**Native frames:** pmanwaf0, pmanwaf1, pmanwaf2, pmanwaf3, pmanwaf4. Hold 125 ms. First leg lifted/bent, opposite support; profile resolves swing shoe behind/under knee.

**Main driver:** First hip/knee flex and forward swing prepare next contact, opposite arm travels forward.

**Right chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -5°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Left supports, right foot clears; through final 125 ms extend toward right incoming contact without foot slide. Initial R/L knee flex 60/8° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** No knife; hands empty. Short arm swing opposes leg phase.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: first knee lift/loop prep → loop to first pose at 750 ms, keeping velocity/contact continuity. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Attack

[Unannotated native contacts](source/attack_native.png) · [Existing original 2D landmark overlay](guides/attack_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**End rule:** return to native standing at 750 ms.

### a — 0 ms: knife ready

**Native frames:** pmanata0. Hold 125 ms. Right knife low by thigh; left arm opens slightly, body front.

**Main driver:** Right hand acquires knife visibility and shoulder prepares.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Torso quiet, small forward readiness. World trunk tilt 2°, rib yaw 0°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Both shoes planted, no invented advance. Initial R/L knee flex 8/8° (±15°; hidden knees uncertain).

**Head:** Look toward target.

**Prop/visibility:** Knife at right side; separate rigid prop.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: knife ready → draw and left guard. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: draw and left guard

**Native frames:** pmanatb0. Hold 125 ms. Right blade drawn back/out low; left open palm rises toward face/chest; knees flex.

**Main driver:** Right shoulder retracts while pelvis lowers, left arm reaches as counterbalance.

**Right chain:** Shoulder retracts and turns outward; elbow low, wrist drawn behind/outside hip without overstretching. Initial abduction/forward elevation/elbow flex ≈ 35/-25/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Clavicle rotates upward; upper arm out/front; elbow opens, wrist near shoulder-height reach. Initial abduction/forward elevation/elbow flex ≈ 70/60/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Ribs wind toward character right slightly; pelvis less. World trunk tilt 5°, rib yaw 15°, pelvis height delta -0.030H (all inferred centers).

**Support/legs:** Both knees bend; stance width roughly retained. Initial R/L knee flex 25/30° (±15°; hidden knees uncertain).

**Head:** Chin down, eyes target below brow.

**Prop/visibility:** Blade low/outside right hip, grip does not open.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: draw and left guard → forward thrust passage. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: forward thrust passage

**Native frames:** pmanatc0. Hold 125 ms. Right forearm foreshortens toward viewer near belt/chest; left palm opens to side.

**Main driver:** Clavicle protraction starts reach; elbow opens, knife follows.

**Right chain:** Clavicle protracts; upper arm points toward viewer; elbow opens, forearm foreshortens, wrist ahead of torso. Initial abduction/forward elevation/elbow flex ≈ 20/75/40°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.

**Trunk/hips:** Ribs begin turning left, pelvis counters modestly. World trunk tilt 5°, rib yaw 0°, pelvis height delta -0.020H (all inferred centers).

**Support/legs:** Both feet support, knees begin extending. Initial R/L knee flex 20/20° (±15°; hidden knees uncertain).

**Head:** Gaze ahead, head follows shoulder gently.

**Prop/visibility:** Depth of blade inferred from short projected reach; no hand scaling.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: forward thrust passage → cross-body reach. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: cross-body reach

**Native frames:** pmanatd0. Hold 125 ms. Right arm extends across to character left at shoulder height; knife points diagonally up.

**Main driver:** Torso yaw and right shoulder carry lateral blade arc; elbow opens last.

**Right chain:** Shoulder reaches across chest toward opposite side; elbow nearly opens; wrist traces lateral attack arc at chest/shoulder height. Initial abduction/forward elevation/elbow flex ≈ 25/80/20°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Chest turns left, pelvis turns less, shoulders oblique. World trunk tilt 2°, rib yaw -30°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Left support can carry slightly more weight; minimal sole pivot inferred. Initial R/L knee flex 10/10° (±15°; hidden knees uncertain).

**Head:** Head turns with blade/chest, chin modestly tilted.

**Prop/visibility:** Blade tip upper-left body side (image right); fixed length/edge roll.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: cross-body reach → retract cross-body. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: retract cross-body

**Native frames:** pmanate0. Hold 125 ms. Right forearm folds across upper chest, blade up/diagonal; left low/back.

**Main driver:** Right elbow folds to decelerate distal reach, chest remains turned.

**Right chain:** Shoulder remains turned across body; elbow folds to retract wrist toward opposite chest, without crossing forearm through ribs. Initial abduction/forward elevation/elbow flex ≈ 20/55/75°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Yaw holds then starts returning, no new windup. World trunk tilt 0°, rib yaw -25°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Feet remain near original stance, soft knees. Initial R/L knee flex 8/8° (±15°; hidden knees uncertain).

**Head:** Head remains slightly left, target maintained.

**Prop/visibility:** Knife outside chest, keep wrist near neutral.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: retract cross-body → lower to waist. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: lower to waist

**Native frames:** pmanatf0. Hold 125 ms. Right hand/knife returns near waist/front, left arm down.

**Main driver:** Shoulder lowers after elbow recovery; body re-centers.

**Right chain:** Upper arm lowers near ribs; elbow remains bent, wrist returns in front of belt/waist. Initial abduction/forward elevation/elbow flex ≈ 12/30/75°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal inward toward knife handle; four fingers curl 70–95°, opposed thumb supports handle. Finger direction follows curled grip; blade is rigid extension of hand/socket. Forearm roll sets edge orientation; wrist near neutral, not snapped sideways.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Chest returns front, pelvis level. World trunk tilt 0°, rib yaw -5°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support, knees relax. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Head front.

**Prop/visibility:** Knife still visible here; disappearance belongs after attack at 750 ms.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: lower to waist → return to native standing at 750 ms. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Hit

[Unannotated native contacts](source/hit_native.png) · [Existing original 2D landmark overlay](guides/hit_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**End rule:** return to native standing at 625 ms.

### a — 0 ms: start protective fold

**Native frames:** pmanwia0. Hold 125 ms. Right hand rises to abdomen/chest, left low; head inclines.

**Main driver:** Abdominal fold starts, hands react afterward.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Small forward rib fold, shoulders round. World trunk tilt 10°, rib yaw 0°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Both feet support, knees start bending. Initial R/L knee flex 12/12° (±15°; hidden knees uncertain).

**Head:** Chin down toward chest.

**Prop/visibility:** No knife in native hit.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: start protective fold → forearm guard. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: forearm guard

**Native frames:** pmanwib0. Hold 125 ms. Right forearm crosses face; left palm opens in front at waist/chest.

**Main driver:** Shoulder hunch and elbow lift protect head while knees lower pelvis.

**Right chain:** Clavicle hunches; elbow out at shoulder height; forearm crosses brow, wrist passes outside face rather than through nose. Initial abduction/forward elevation/elbow flex ≈ 55/55/115°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward face/partly down, fingers extend sideways above brow with curl 15–40°; thumb outside face. Protect facial clearance; rotation comes from shoulder and forearm before wrist.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.

**Trunk/hips:** Forward fold, pelvis drops. World trunk tilt 20°, rib yaw 0°, pelvis height delta -0.060H (all inferred centers).

**Support/legs:** Both knees flex; right knee begins angling outward. Initial R/L knee flex 35/35° (±15°; hidden knees uncertain).

**Head:** Duck behind right forearm.

**Prop/visibility:** Hands clear nose/eyes and each other.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: forearm guard → deep squat guard. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: deep squat guard

**Native frames:** pmanwic0. Hold 125 ms. Lowest crouch, right forearm over eyes, left palm fanned beside face; right knee out.

**Main driver:** Hip/knee flex absorbs recoil; two arms make asymmetric guard.

**Right chain:** Clavicle hunches; elbow out at shoulder height; forearm crosses brow, wrist passes outside face rather than through nose. Initial abduction/forward elevation/elbow flex ≈ 55/55/115°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward face/partly down, fingers extend sideways above brow with curl 15–40°; thumb outside face. Protect facial clearance; rotation comes from shoulder and forearm before wrist.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Short deep fold, avoid shrinking torso. World trunk tilt 25°, rib yaw 3°, pelvis height delta -0.150H (all inferred centers).

**Support/legs:** Right knee flex/out, left knee also bent; both shoes near ground. Initial R/L knee flex 70/65° (±15°; hidden knees uncertain).

**Head:** Head down, shoulders raised protectively.

**Prop/visibility:** Right forearm above brow; left fingers independently open.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: deep squat guard → guard recovery. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: guard recovery

**Native frames:** pmanwid0. Hold 125 ms. Protected crouch persists but starts lifting; open left palm remains high.

**Main driver:** Knee extension begins below held guard, then elbows loosen.

**Right chain:** Clavicle hunches; elbow out at shoulder height; forearm crosses brow, wrist passes outside face rather than through nose. Initial abduction/forward elevation/elbow flex ≈ 55/55/115°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward face/partly down, fingers extend sideways above brow with curl 15–40°; thumb outside face. Protect facial clearance; rotation comes from shoulder and forearm before wrist.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Forward fold reduces slightly, pelvis starts up. World trunk tilt 20°, rib yaw 0°, pelvis height delta -0.120H (all inferred centers).

**Support/legs:** Both feet grounded, knee angles decrease a little. Initial R/L knee flex 60/55° (±15°; hidden knees uncertain).

**Head:** Chin stays low, eyes behind forearm.

**Prop/visibility:** Guard fingers/palms do not suddenly swap orientation.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: guard recovery → arms lower. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: arms lower

**Native frames:** pmanwie0. Hold 125 ms. Hands separate/lower to either side, chest lifts but still crouched.

**Main driver:** Legs restore height while arms release the guard.

**Right chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Ribs unfold and shoulders descend. World trunk tilt 8°, rib yaw 0°, pelvis height delta -0.035H (all inferred centers).

**Support/legs:** Both knees extend toward standing over final 125 ms. Initial R/L knee flex 25/25° (±15°; hidden knees uncertain).

**Head:** Face begins looking ahead.

**Prop/visibility:** Native unused pmanwif0 is excluded; standing boundary is 625 ms.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: arms lower → return to native standing at 625 ms. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Death

[Unannotated native contacts](source/death_native.png) · [Existing original 2D landmark overlay](guides/death_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**End rule:** reach separate corpse at 625 ms; last death anchor remains at 500 ms.

### a — 0 ms: defensive reaction

**Native frames:** pmandea0. Hold 125 ms. Right hand near chest, left low/front, head inclines.

**Main driver:** Torso fold and defensive arm reaction.

**Right chain:** Shoulder folds inward; elbow low, forearm crosses abdomen, wrist close to opposite waist. Initial abduction/forward elevation/elbow flex ≈ 15/30/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Chest folds slightly, pelvis lowers. World trunk tilt 10°, rib yaw 0°, pelvis height delta -0.015H (all inferred centers).

**Support/legs:** Both feet support briefly. Initial R/L knee flex 15/15° (±15°; hidden knees uncertain).

**Head:** Head down, gaze interrupted.

**Prop/visibility:** No weapon visible.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: defensive reaction → protected crouch. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: protected crouch

**Native frames:** pmandeb0. Hold 125 ms. Right forearm guards eyes, left palm near face; knees bent.

**Main driver:** Knee/hip flex lowers root while arms shield face.

**Right chain:** Clavicle hunches; elbow out at shoulder height; forearm crosses brow, wrist passes outside face rather than through nose. Initial abduction/forward elevation/elbow flex ≈ 55/55/115°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward face/partly down, fingers extend sideways above brow with curl 15–40°; thumb outside face. Protect facial clearance; rotation comes from shoulder and forearm before wrist.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Forward fold, shoulders hunch. World trunk tilt 25°, rib yaw 0°, pelvis height delta -0.140H (all inferred centers).

**Support/legs:** Deep knee bend; support about to fail. Initial R/L knee flex 65/65° (±15°; hidden knees uncertain).

**Head:** Head ducks behind forearm.

**Prop/visibility:** Hands clear facial features.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: protected crouch → side balance failure. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: side balance failure

**Native frames:** pmandec0. Hold 125 ms. Torso inclines character left (image right), right leg extends image left, left knee sinks.

**Main driver:** Root tilts toward left; left knee buckles, right leg opens as counterweight.

**Right chain:** Clavicle hunches; elbow out at shoulder height; forearm crosses brow, wrist passes outside face rather than through nose. Initial abduction/forward elevation/elbow flex ≈ 55/55/115°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward face/partly down, fingers extend sideways above brow with curl 15–40°; thumb outside face. Protect facial clearance; rotation comes from shoulder and forearm before wrist.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Forward/left side root tilt; maintain modest local spine bend. World trunk tilt 35°, rib yaw -10°, pelvis height delta -0.240H (all inferred centers).

**Support/legs:** Left knee drops; right shoe may slide/release. Do not pin both feet. Initial R/L knee flex 20/95° (±15°; hidden knees uncertain).

**Head:** Head follows fall, no neck swivel independent of torso.

**Prop/visibility:** No props; guard arms begin reaching out.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: side balance failure → side drop. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: side drop

**Native frames:** pmanded0. Hold 125 ms. Right leg long/out to image left, left leg folded below; arms flare by head as body falls.

**Main driver:** Root translation/roll carries collapse; left leg folds, arms reach.

**Right chain:** Shoulder opens as trunk falls; elbow mostly open, wrist out from body. Root rotation carries arm, not an impossible spine bend. Initial abduction/forward elevation/elbow flex ≈ 65/20/25°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Strong side tilt and forward pitch; torso lengths preserved. World trunk tilt 65°, rib yaw -15°, pelvis height delta -0.370H (all inferred centers).

**Support/legs:** Left knee/floor nearing contact, right foot no fixed pin. Initial R/L knee flex 15/110° (±15°; hidden knees uncertain).

**Head:** Head ahead of shoulder fall, neck flex restrained.

**Prop/visibility:** Hands/forearms should not cut through head on descent.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: side drop → side floor arrival. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: side floor arrival

**Native frames:** pmandee0. Hold 125 ms. Low side-lying body, one leg out; head to image right, arms low.

**Main driver:** Hip/side contact halts fall; hands and hem settle.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Left chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Root at floor; side orientation differs from native corpse. World trunk tilt 85°, rib yaw -20°, pelvis height delta -0.420H (all inferred centers).

**Support/legs:** Floor supports side/hip/leg, right leg partly extended. Initial R/L knee flex 30/100° (±15°; hidden knees uncertain).

**Head:** Head close to floor turned sideways, not detached.

**Prop/visibility:** Last pose must bridge to separate prone corpse at 625 ms.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: side floor arrival → reach separate corpse at 625 ms; last death anchor remains at 500 ms. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs. Keep last observed pose at 500 ms and fit the hidden path to actual corpse at 625 ms; do not replace or skip either endpoint.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Corpse

[Unannotated native contacts](source/corpse_native.png) · [Existing original 2D landmark overlay](guides/corpse_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.

**End rule:** hold current pose indefinitely.

### a — 0 ms: held prone remains

**Native frames:** pmandef0. Hold 125 ms. Face-down body with arms spread, legs apart; distinct pmandef0 from death e.

**Main driver:** No repeated motion; endpoint alignment must be solved once.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Left chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Prone floor root, torso flat and neck clear. World trunk tilt 90°, rib yaw 0°, pelvis height delta -0.420H (all inferred centers).

**Support/legs:** Chest/hips/limbs supported by floor; contact locations inferred. Initial R/L knee flex 20/20° (±15°; hidden knees uncertain).

**Head:** Face near floor, no breathing or raised gaze.

**Prop/visibility:** No knife/blood effect added.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: held prone remains → hold current pose indefinitely. Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Fidget

[Unannotated native contacts](source/fidget_native.png) · [Existing original 2D landmark overlay](guides/fidget_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**End rule:** loop to first pose at 750 ms, keeping velocity/contact continuity.

### a — 0 ms: rest hold

**Native frames:** pmanfia0. Hold 125 ms. Playback repeats fia0 at 0 and 125 ms; fib0 is unused artwork.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Chest upright, shoulders modestly square. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes supported, knees almost straight but unlocked. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No handheld knife visible.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–250 ms is a repeated native rest-pose hold. Do not add an intermediate gesture merely because playback has two entries.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: duplicate rest hold

**Native frames:** pmanfia0. Hold 125 ms. Playback repeats fia0 at 0 and 125 ms; fib0 is unused artwork. All supplied native views are pixel-identical to the 0 ms anchor; retain the same constrained pose.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Chest upright, shoulders modestly square. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes supported, knees almost straight but unlocked. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No handheld knife visible.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 125–250 ms: duplicate rest hold → small face/head change. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable. Preserve identical source-pose constraints; no invented limb change between identical holds.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: small face/head change

**Native frames:** pmanfic0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Chest upright, shoulders modestly square. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes supported, knees almost straight but unlocked. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No handheld knife visible.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 250–375 ms: small face/head change → held face variation. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: held face variation

**Native frames:** pmanfid0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Chest upright, shoulders modestly square. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes supported, knees almost straight but unlocked. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No handheld knife visible.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 375–500 ms: held face variation → return expression. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: return expression

**Native frames:** pmanfie0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Chest upright, shoulders modestly square. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes supported, knees almost straight but unlocked. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No handheld knife visible.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 500–625 ms: return expression → loop rest. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: loop rest

**Native frames:** pmanfif0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Chest upright, shoulders modestly square. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes supported, knees almost straight but unlocked. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** No handheld knife visible.

**Secondary surfaces:** Short tunic hem lags hip turn slightly; belt buckle stays on waist, cuffs follow upper arm and clear elbow. Trouser folds deform at knee without changing limb length. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 625–750 ms: loop rest → loop to first pose at 750 ms, keeping velocity/contact continuity. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Rig and animation acceptance

Start with geometry comparison and the family stress poses in the anatomy guide. After receiving the rig, use stock walk/run only to diagnose weight collapse, crossed joints, arm-to-torso attachment and foot volumes. Then build native walking first, verify all five genuine views and the seam, repair weights, and construct the other six native states. Review every observed anchor and proposed midpoint, not only contact sheets.

A later review should retain native/3D side-by-side screenshots with the mismatched region highlighted, the time/view, cause (geometry, rig, weight, animation, prop or cloth) and fix/recheck evidence. Match camera and scale before declaring a shape defect. Do not tweak topology to conceal a wrong pose or retime the source to conceal failed interpolation. UVs and Meshy texturing follow accepted animation/deformation.

Numeric seeds and ambiguities are deliberately reviewable. Palms, hidden knees, contacts and corpse depth cannot be certified before a 3D model exists. No human artistic acceptance or model deformation pass is claimed here.
