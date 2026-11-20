# MM6 New Sorpigal Guard A, gua; descriptor 553, palette 748; lieutenant/captain 554–555 are variants: complete native animation study

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

- The weapon is a HALBERD, never a sword/shield. Side view establishes full shaft length.
- Walk starts LEFT incoming foot (frontal image right), with RIGHT incoming at d; c raises right shoe, f raises left. Confirm against all genuine views.
- Attack b/e narrow blade projection is orientation/foreshortening; retain rigid blade and continuous forearm roll.
- Left hand closes lower shaft during attack c–f, then releases into right-only carry; finite grip separation mandatory.
- Hit left palm rises above helmet; death is backward buckle into curled side/back remains, not peasant prone fall.

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

Unused artwork remains in the source inventory, not playback: none.
Pixel-identical images/holds are retained exactly: {}.

## Standing

[Unannotated native contacts](source/standing_native.png) · [Existing original 2D landmark overlay](guides/standing_landmarks.png)

**Source views:** front, front-right, right, back-right, back. 5/6/7 mirror 3/2/1; not extra depth evidence.

**Motion spacing:** Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.

**End rule:** hold current pose indefinitely.

### a — 0 ms: held carry

**Native frames:** guastaa0, guastaa1, guastaa2, guastaa3, guastaa4. Hold 125 ms. Right hand low, blade foreshortened front; genuine side shows long shaft across hip, left arm down.

**Main driver:** Quiet one-handed carry, no cyclic soldier flourish.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Torso upright, helmet forward, shoulders level. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support, knees relaxed. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Face/helmet front; no required jaw animation.

**Prop/visibility:** Polearm low near horizontal in side view; frontal blade size is projection.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: held carry → hold current pose indefinitely. Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Walk

[Unannotated native contacts](source/walk_native.png) · [Existing original 2D landmark overlay](guides/walk_landmarks.png)

**Source views:** front, front-right, right, back-right, back. 5/6/7 mirror 3/2/1; not extra depth evidence.

**Motion spacing:** Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**End rule:** loop to first pose at 750 ms, keeping velocity/contact continuity.

### a — 0 ms: incoming first foot

**Native frames:** guawala0, guawala1, guawala2, guawala3, guawala4. Hold 125 ms. Front shows incoming shoe/sole and opposite trailing foot; profile separates stride depth.

**Main driver:** Pelvis progression and incoming hip swing lead; opposite arm balances.

**Right chain:** Shoulder advances with forearm; elbow bends low, wrist rises in front of waist; polearm blade sweeps forward/up. Initial abduction/forward elevation/elbow flex ≈ 15/40/45°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -5°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Left leg reaches forward; heel/flat-foot contact WINDOW, not proven exact plant; other leg trails/toe-off. Initial R/L knee flex 25/15° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Blade forward/up in profile (~25–40° upward projected shaft); right hand ahead.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: incoming first foot → first support/passing. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: first support/passing

**Native frames:** guawalb0, guawalb1, guawalb2, guawalb3, guawalb4. Hold 125 ms. Feet approach passing alignment; profile trailing heel lifted.

**Main driver:** First support leg accepts weight; opposite hip begins forward swing.

**Right chain:** Shoulder advances with forearm; elbow bends low, wrist rises in front of waist; polearm blade sweeps forward/up. Initial abduction/forward elevation/elbow flex ≈ 15/40/45°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -2°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Left foot supports, right heel lifts/pass begins; support assignment fitted across all views. Initial R/L knee flex 40/8° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Blade still forward/up, right hand remains near waist-front.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: first support/passing → opposite knee lift. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: opposite knee lift

**Native frames:** guawalc0, guawalc1, guawalc2, guawalc3, guawalc4. Hold 125 ms. Opposite knee/shoe forward/up, support leg straighter; profile confirms bent swing leg.

**Main driver:** Swing hip/knee flex lifts foot; pelvis modestly rises over support.

**Right chain:** Upper arm lowers near ribs; elbow remains bent, wrist returns in front of belt/waist. Initial abduction/forward elevation/elbow flex ≈ 12/30/75°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 5°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Left supports; right knee bends and shoe clears floor; do not plant lifted foot. Initial R/L knee flex 60/8° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Blade/shaft lowers toward near-horizontal; right elbow softens.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: opposite knee lift → opposite incoming foot. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: opposite incoming foot

**Native frames:** guawald0, guawald1, guawald2, guawald3, guawald4. Hold 125 ms. Opposite leg forward/sole showing; first leg trailing in profile.

**Main driver:** Opposite hip completes swing, pelvis advances, arms reverse continuously.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 5°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Right incoming heel/flat-foot contact WINDOW; left toe-off/trailing, avoid long double-foot pins. Initial R/L knee flex 15/25° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Shaft near horizontal through low hip, blade ahead/down.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: opposite incoming foot → opposite support/passing. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: opposite support/passing

**Native frames:** guawale0, guawale1, guawale2, guawale3, guawale4. Hold 125 ms. Feet close again, trailing first heel raised; body crosses support.

**Main driver:** Opposite support accepts weight; first hip swings forward.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 2°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Right supports; left begins swing, lifted heel/toe-off fitted to side/back views. Initial R/L knee flex 8/40° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Blade slopes down/front, shaft rear end rises; right forearm roll keeps grip.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: opposite support/passing → first knee lift/loop prep. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: first knee lift/loop prep

**Native frames:** guawalf0, guawalf1, guawalf2, guawalf3, guawalf4. Hold 125 ms. First leg lifted/bent, opposite support; profile resolves swing shoe behind/under knee.

**Main driver:** First hip/knee flex and forward swing prepare next contact, opposite arm travels forward.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -5°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Right supports, left foot clears; through final 125 ms extend toward left incoming contact without foot slide. Initial R/L knee flex 8/60° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Shaft near horizontal again, ready to lift through loop seam.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: first knee lift/loop prep → loop to first pose at 750 ms, keeping velocity/contact continuity. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Attack

[Unannotated native contacts](source/attack_native.png) · [Existing original 2D landmark overlay](guides/attack_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**End rule:** return to native standing at 750 ms.

### a — 0 ms: upright preparation

**Native frames:** guaatka0. Hold 125 ms. Right shaft upright, right elbow bent, left hand still down.

**Main driver:** Right shoulder raises polearm, small knee readiness.

**Right chain:** Clavicle lifts; elbow out and bent, wrist chest/shoulder high; shaft rises beside body. Initial abduction/forward elevation/elbow flex ≈ 35/55/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Chest front, no large crouch. World trunk tilt 0°, rib yaw 0°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Both shoes near original stance. Initial R/L knee flex 8/8° (±15°; hidden knees uncertain).

**Head:** Helmet faces target, chin neutral.

**Prop/visibility:** Blade high outside right shoulder, left not gripping yet.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: upright preparation → rotate and invite second grip. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: rotate and invite second grip

**Native frames:** guaatkb0. Hold 125 ms. Shaft diagonal high at right; blade edge narrow/foreshortened, left hand reaches front.

**Main driver:** Right forearm rolls shaft while left elbow brings palm toward lower grip.

**Right chain:** Right shoulder rotates up/back; elbow out, wrist near temple/shoulder; blade above and outside head. Initial abduction/forward elevation/elbow flex ≈ 50/75/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Left clavicle advances; elbow folded near ribs, wrist reaches lower part of same shaft across chest/waist. Initial abduction/forward elevation/elbow flex ≈ 20/50/90°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Modest shoulder counterturn, pelvis quiet. World trunk tilt 2°, rib yaw 10°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Both supports; soft knees. Initial R/L knee flex 10/10° (±15°; hidden knees uncertain).

**Head:** Gaze ahead, helmet clear of blade.

**Prop/visibility:** Thin blade projection needs axial roll/depth; blade geometry must remain fixed.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: rotate and invite second grip → two-hand raised ready. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: two-hand raised ready

**Native frames:** guaatkc0. Hold 125 ms. Broad blade above/right side; right grip high, left hand visibly at lower shaft across front.

**Main driver:** Right shoulder sets high arc, left palm closes to guide same rigid shaft.

**Right chain:** Right shoulder rotates up/back; elbow out, wrist near temple/shoulder; blade above and outside head. Initial abduction/forward elevation/elbow flex ≈ 50/75/105°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Left clavicle advances; elbow folded near ribs, wrist reaches lower part of same shaft across chest/waist. Initial abduction/forward elevation/elbow flex ≈ 20/50/90°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Left palm normal toward same shaft, fingers encircle lower grip station, opposed thumb; finger curl 65–95°. Maintain finite grip spacing and align forearm roll to shaft; do not weld hands together.

**Trunk/hips:** Ribs slightly turned right, left clavicle forward. World trunk tilt 3°, rib yaw 12°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Both feet support; minor opposing hip yaw. Initial R/L knee flex 12/12° (±15°; hidden knees uncertain).

**Head:** Head forward, no neck twist compensating wrong arm reach.

**Prop/visibility:** Right upper and left lower grip stations separated; blade rolls broadside.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: two-hand raised ready → diagonal downstroke. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: diagonal downstroke

**Native frames:** guaatkd0. Hold 125 ms. Blade passes down at image left, right hand pushes across, left pulls lower shaft near left hip.

**Main driver:** Proximal right-shoulder descent plus left-elbow pull accelerate polearm head.

**Right chain:** Upper arm drives down/across; elbow opens toward lower chest, wrist moves through centerline while remaining on shaft. Initial abduction/forward elevation/elbow flex ≈ 15/45/45°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Left elbow draws back/down; forearm guides lower shaft toward left hip, complementing right-hand push. Initial abduction/forward elevation/elbow flex ≈ 10/30/70°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Left palm normal toward same shaft, fingers encircle lower grip station, opposed thumb; finger curl 65–95°. Maintain finite grip spacing and align forearm roll to shaft; do not weld hands together.

**Trunk/hips:** Small forward/left rib turn, pelvis counterbalances; native trunk motion modest. World trunk tilt 8°, rib yaw -10°, pelvis height delta -0.015H (all inferred centers).

**Support/legs:** Both supports with small sole pivot inferred; no added large step. Initial R/L knee flex 15/15° (±15°; hidden knees uncertain).

**Head:** Eyes toward swing, helmet pitch slightly down.

**Prop/visibility:** Shaft diagonal across torso, both grips constrain identical rigid object.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: diagonal downstroke → low passage/foreshortening. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: low passage/foreshortening

**Native frames:** guaatke0. Hold 125 ms. Both hands low near waist, blade becomes narrow, shaft projection short.

**Main driver:** Arms decelerate sweep through low arc; forearm roll turns blade edge/depth.

**Right chain:** Upper arm lowers near ribs; elbow remains bent, wrist returns in front of belt/waist. Initial abduction/forward elevation/elbow flex ≈ 12/30/75°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Left elbow draws back/down; forearm guides lower shaft toward left hip, complementing right-hand push. Initial abduction/forward elevation/elbow flex ≈ 10/30/70°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Left palm normal toward same shaft, fingers encircle lower grip station, opposed thumb; finger curl 65–95°. Maintain finite grip spacing and align forearm roll to shaft; do not weld hands together.

**Trunk/hips:** Torso re-centers slightly, shoulders lowered. World trunk tilt 4°, rib yaw -5°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Both feet support, knees relax. Initial R/L knee flex 10/10° (±15°; hidden knees uncertain).

**Head:** Head front/down a little, follows force path.

**Prop/visibility:** Fit axial roll and toward/away depth; never shrink or delete blade.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: low passage/foreshortening → cross-chest recovery. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: cross-chest recovery

**Native frames:** guaatkf0. Hold 125 ms. Polearm lies across chest diagonally, left hand still at lower station; right forearm bent.

**Main driver:** Right elbow folds upward; left guides shaft, then releases into standing carry after this anchor.

**Right chain:** Right elbow folds and lifts in front of chest; wrist brings shaft across upper torso for recovery. Initial abduction/forward elevation/elbow flex ≈ 25/55/100°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Left clavicle advances; elbow folded near ribs, wrist reaches lower part of same shaft across chest/waist. Initial abduction/forward elevation/elbow flex ≈ 20/50/90°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Left palm normal toward same shaft, fingers encircle lower grip station, opposed thumb; finger curl 65–95°. Maintain finite grip spacing and align forearm roll to shaft; do not weld hands together.

**Trunk/hips:** Torso front, arms clear mail/coif. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support, standing height returning. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Helmet/gaze front.

**Prop/visibility:** At 750 ms return to low one-handed carry; left grip-release curve is inferred.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: cross-chest recovery → return to native standing at 750 ms. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Hit

[Unannotated native contacts](source/hit_native.png) · [Existing original 2D landmark overlay](guides/hit_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**End rule:** return to native standing at 750 ms.

### a — 0 ms: baseline reaction

**Native frames:** guawina0. Hold 125 ms. Low right carry, left down, body near standing.

**Main driver:** Start rib recoil without immediate weapon teleport.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Chest near upright, tiny preparatory recoil. World trunk tilt -2°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both shoes support. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Helmet front.

**Prop/visibility:** Shaft begins rise from actual carry angle.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: baseline reaction → open-left recoil. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: open-left recoil

**Native frames:** guawinb0. Hold 125 ms. Right blade/shaft rises diagonally; left hand opens low/front, head starts up.

**Main driver:** Ribcage recoils, right shoulder lifts weapon away, left opens to balance.

**Right chain:** Clavicle lifts; elbow out and bent, wrist chest/shoulder high; shaft rises beside body. Initial abduction/forward elevation/elbow flex ≈ 35/55/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Short backward tilt, pelvis stabilizes. World trunk tilt -8°, rib yaw 0°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Knees soften; no recovered heel-lift timing. Initial R/L knee flex 10/10° (±15°; hidden knees uncertain).

**Head:** Chin/helmet lifts slightly.

**Prop/visibility:** Blade outside right shoulder, right grip persistent.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: open-left recoil → head back/palm out. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: head back/palm out

**Native frames:** guawinc0. Hold 125 ms. Head/chest lean back, left palm out at chest, right weapon high to side.

**Main driver:** Upper-trunk recoil extends neck slightly while free arm catches balance.

**Right chain:** Clavicle rotates upward; upper arm out/front; elbow opens, wrist near shoulder-height reach. Initial abduction/forward elevation/elbow flex ≈ 70/60/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle rotates upward; upper arm out/front; elbow opens, wrist near shoulder-height reach. Initial abduction/forward elevation/elbow flex ≈ 70/60/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Back tilt moderate, no stretched abdomen. World trunk tilt -15°, rib yaw 0°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Both supports provisionally retained; hip shift small. Initial R/L knee flex 12/12° (±15°; hidden knees uncertain).

**Head:** Helmet pitches back, eye opening upward.

**Prop/visibility:** Weapon vertical/diagonal outside body, no accidental left grip.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: head back/palm out → left hand overhead. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: left hand overhead

**Native frames:** guawind0. Hold 125 ms. Maximum recoil, left palm above head, right shaft upright at side.

**Main driver:** Left shoulder elevates from balance reaction; ribs/head reach backward extreme.

**Right chain:** Clavicle lifts; elbow out and bent, wrist chest/shoulder high; shaft rises beside body. Initial abduction/forward elevation/elbow flex ≈ 35/55/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Shoulder elevates with clavicle/scapula; elbow out/up, forearm above brow, wrist follows overhead arc. Initial abduction/forward elevation/elbow flex ≈ 65/120/95°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Back tilt peaks; pelvis stays below support. World trunk tilt -20°, rib yaw 0°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Soft knees, choose smallest contact change compatible with silhouette. Initial R/L knee flex 15/15° (±15°; hidden knees uncertain).

**Head:** Helmet back, nasal bar remains rigid to skull.

**Prop/visibility:** Left fingers up/fanned, no sword/weapon in left hand.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: left hand overhead → recover left reach. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: recover left reach

**Native frames:** guawine0. Hold 125 ms. Head front again, left arm forward near shoulder level, right shaft drops diagonally.

**Main driver:** Trunk recovers first; left arm descends through forward reach rather than straight teleport.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle rotates upward; upper arm out/front; elbow opens, wrist near shoulder-height reach. Initial abduction/forward elevation/elbow flex ≈ 70/60/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Back tilt reduces, shoulders descend. World trunk tilt -5°, rib yaw 0°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Both feet support, knees extend gently. Initial R/L knee flex 8/8° (±15°; hidden knees uncertain).

**Head:** Helmet/gaze front.

**Prop/visibility:** Right blade/shaft rotates low with same grip; left palm rotates downward.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: recover left reach → carry restoration. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: carry restoration

**Native frames:** guawinf0. Hold 125 ms. Both arms low, helmet front, weapon near low carry.

**Main driver:** Shoulders settle after trunk recovery.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Upright, no residual body bounce required. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both supports relaxed. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Head front.

**Prop/visibility:** Return to standing low shaft at 750 ms.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: carry restoration → return to native standing at 750 ms. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Death

[Unannotated native contacts](source/death_native.png) · [Existing original 2D landmark overlay](guides/death_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**End rule:** reach separate corpse at 625 ms; last death anchor remains at 500 ms.

### a — 0 ms: face reaction

**Native frames:** guadtha0. Hold 125 ms. Left palm near face, right shaft up with edge-on blade; body near upright.

**Main driver:** Head/rib recoil and protective left hand lift.

**Right chain:** Clavicle lifts; elbow out and bent, wrist chest/shoulder high; shaft rises beside body. Initial abduction/forward elevation/elbow flex ≈ 35/55/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal toward face/partly down, fingers extend sideways above brow with curl 15–40°; thumb outside face. Protect facial clearance; rotation comes from shoulder and forearm before wrist.

**Trunk/hips:** Small back tilt. World trunk tilt -5°, rib yaw 0°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Both feet support briefly, knees loosen. Initial R/L knee flex 10/10° (±15°; hidden knees uncertain).

**Head:** Chin lifts behind left palm.

**Prop/visibility:** Right blade edge-on projection, not a different pole.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: face reaction → cover face/back sway. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: cover face/back sway

**Native frames:** guadthb0. Hold 125 ms. Left hand covers face, right weapon upright/out; knees soften.

**Main driver:** Ribs recoil while left elbow maintains face guard.

**Right chain:** Clavicle lifts; elbow out and bent, wrist chest/shoulder high; shaft rises beside body. Initial abduction/forward elevation/elbow flex ≈ 35/55/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal toward face/partly down, fingers extend sideways above brow with curl 15–40°; thumb outside face. Protect facial clearance; rotation comes from shoulder and forearm before wrist.

**Trunk/hips:** Back sway with minor side yaw. World trunk tilt -15°, rib yaw 5°, pelvis height delta -0.030H (all inferred centers).

**Support/legs:** Both feet support but knees buckling. Initial R/L knee flex 20/20° (±15°; hidden knees uncertain).

**Head:** Helmet tilted away from hand, no palm clipping nasal bar.

**Prop/visibility:** Shaft stays outside right side.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: cover face/back sway → balance failure. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: balance failure

**Native frames:** guadthc0. Hold 125 ms. Left palm rises beside head, torso/head back, right hand/weapon out.

**Main driver:** Whole-body back tilt leaves support; left arm opens upward.

**Right chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Shoulder elevates with clavicle/scapula; elbow out/up, forearm above brow, wrist follows overhead arc. Initial abduction/forward elevation/elbow flex ≈ 65/120/95°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Root backward tilt increases; local spine small. World trunk tilt -30°, rib yaw 8°, pelvis height delta -0.100H (all inferred centers).

**Support/legs:** Knees start deeper buckle, feet may pivot/release. Initial R/L knee flex 35/35° (±15°; hidden knees uncertain).

**Head:** Head follows fall, coif bends only at neck.

**Prop/visibility:** Weapon remains in right grip, no planted staff assumption.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: balance failure → backward drop. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: backward drop

**Native frames:** guadthd0. Hold 125 ms. Body low/back, knees strongly bent, left hand above head, right shaft toward floor.

**Main driver:** Root descends/rotates; knees fold, arms lag upward/out.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Shoulder elevates with clavicle/scapula; elbow out/up, forearm above brow, wrist follows overhead arc. Initial abduction/forward elevation/elbow flex ≈ 65/120/95°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Whole trunk tilts back/side, pelvis drops. World trunk tilt -55°, rib yaw 10°, pelvis height delta -0.270H (all inferred centers).

**Support/legs:** Knees flex, soles/feet may roll; neither both feet fixed. Initial R/L knee flex 85/85° (±15°; hidden knees uncertain).

**Head:** Helmet/head follows body, chin position partly occluded.

**Prop/visibility:** Right shaft approaches floor outside legs; collision checks required.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: backward drop → curled floor arrival. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: curled floor arrival

**Native frames:** guadthe0. Hold 125 ms. Body low on side/back, legs drawn, left hand still up; right weapon out on floor.

**Main driver:** Hip/back floor contact halts fall; left arm and knees lag.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Shoulder opens as trunk falls; elbow mostly open, wrist out from body. Root rotation carries arm, not an impossible spine bend. Initial abduction/forward elevation/elbow flex ≈ 65/20/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Root low, side/back orientation; full supine direction not certain. World trunk tilt -80°, rib yaw 20°, pelvis height delta -0.400H (all inferred centers).

**Support/legs:** Back/side/hip floor support, knees strongly flexed. Initial R/L knee flex 110/110° (±15°; hidden knees uncertain).

**Head:** Helmet beside torso, neck clear under coif.

**Prop/visibility:** Weapon low/outside body, fixed right grip or collision-fitted contact.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: curled floor arrival → reach separate corpse at 625 ms; last death anchor remains at 500 ms. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs. Keep last observed pose at 500 ms and fit the hidden path to actual corpse at 625 ms; do not replace or skip either endpoint.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Corpse

[Unannotated native contacts](source/corpse_native.png) · [Existing original 2D landmark overlay](guides/corpse_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.

**End rule:** hold current pose indefinitely.

### a — 0 ms: held curled remains

**Native frames:** guadthf0. Hold 125 ms. Separate guadthf0 is curled on side/back, arm/shaft stretches out on floor, knees drawn.

**Main driver:** None after final settling; held remains.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Match side/back silhouette; exact belly orientation occluded. World trunk tilt -85°, rib yaw 25°, pelvis height delta -0.420H (all inferred centers).

**Support/legs:** Side/back/hips floor supports, feet tucked by bent knees. Initial R/L knee flex 115/115° (±15°; hidden knees uncertain).

**Head:** Helmet at native side of body, coif/neck not merged with chest.

**Prop/visibility:** Polearm lies along floor outside corpse, shaft/blade unchanged.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: held curled remains → hold current pose indefinitely. Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Fidget

[Unannotated native contacts](source/fidget_native.png) · [Existing original 2D landmark overlay](guides/fidget_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**End rule:** loop to first pose at 750 ms, keeping velocity/contact continuity.

### a — 0 ms: low carry start

**Native frames:** guafida0. Hold 125 ms. Blade broad/low at right, left arm down; torso/feet near standing.

**Main driver:** Small right-wrist/forearm repositioning, not body attack.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Torso quiet, belt height fixed. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both feet held. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Helmet forward.

**Prop/visibility:** Shaft low/diagonal across hip; right grip fixed.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: low carry start → roll shaft. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: roll shaft

**Native frames:** guafidb0. Hold 125 ms. Shaft end points down toward image left, blade narrows at waist, body unchanged.

**Main driver:** Right forearm rolls and elbow adjusts slightly, blade projection changes.

**Right chain:** Upper arm lowers near ribs; elbow remains bent, wrist returns in front of belt/waist. Initial abduction/forward elevation/elbow flex ≈ 12/30/75°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Ribs/pelvis quiet. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both feet held, no gait shift. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Helmet front, tiny glance only if needed to fit pixels.

**Prop/visibility:** Shaft tilts, blade edge-on inferred; no blade morph.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 125–250 ms: roll shaft → near-horizontal adjustment. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: near-horizontal adjustment

**Native frames:** guafidc0. Hold 125 ms. Blade head small/foreshortened at right waist, shaft low, left still down.

**Main driver:** Right grip rotation continues, elbow brings shaft nearer carry.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Torso held, shoulders minimally move. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both feet held. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Head quiet.

**Prop/visibility:** Horizontal/depth angle fitted with same long shaft.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 250–375 ms: near-horizontal adjustment → reverse toward carry. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: reverse toward carry

**Native frames:** guafidd0. Hold 125 ms. Low blade/shaft returns; left hand starts toward waist.

**Main driver:** Right forearm reverses roll; left elbow bends slightly as secondary response.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Torso held; no whole-body oscillation. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both feet held. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Helmet front.

**Prop/visibility:** Blade broadens again; left near-contact not confirmed grip.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 375–500 ms: reverse toward carry → free-hand approach. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: free-hand approach

**Native frames:** guafide0. Hold 125 ms. Left hand approaches shaft near belt, right blade broad at low side.

**Main driver:** Left shoulder/elbow reach in response to right adjustment.

**Right chain:** Upper arm lowers near ribs; elbow remains bent, wrist returns in front of belt/waist. Initial abduction/forward elevation/elbow flex ≈ 12/30/75°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Left clavicle advances; elbow folded near ribs, wrist reaches lower part of same shaft across chest/waist. Initial abduction/forward elevation/elbow flex ≈ 20/50/90°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight. Possible shaft approach/touch, not an observed firm grip; do not curl all digits around wood automatically.

**Trunk/hips:** Ribs quiet, belt height fixed. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both feet held. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Head tiny downward glance only if native fit requires.

**Prop/visibility:** Left hand may touch/hover; do not assert firm two-hand grip.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 500–625 ms: free-hand approach → release/loop carry. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: release/loop carry

**Native frames:** guafidf0. Hold 125 ms. Low right carry returns, left hand lowers, body close to first frame.

**Main driver:** Left arm releases, right grip settles into loop seam.

**Right chain:** Upper arm hangs near ribs; elbow nearly straight, wrist at thigh/low hip; rigid polearm supported by right grip. Initial abduction/forward elevation/elbow flex ≈ 5/0/15°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward wood shaft, fingers curved around it (65–95°), opposed thumb closes grip. Wrist stays within about ±15° flex; use forearm rotation to roll blade, not a wrist kink or blade morph.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Torso held. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both feet held. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Helmet front.

**Prop/visibility:** Blend to start carry at 750 ms without changing grip station.

**Secondary surfaces:** Mail hauberk behaves as one flexible garment surface, belt follows pelvis, coif follows skull with small neck compliance; helmet and nasal bar are rigid. Blue sleeves deform at shoulders/elbows, not as rigid plate. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 625–750 ms: release/loop carry → loop to first pose at 750 ms, keeping velocity/contact continuity. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Rig and animation acceptance

Start with geometry comparison and the family stress poses in the anatomy guide. After receiving the rig, use stock walk/run only to diagnose weight collapse, crossed joints, arm-to-torso attachment and foot volumes. Then build native walking first, verify all five genuine views and the seam, repair weights, and construct the other six native states. Review every observed anchor and proposed midpoint, not only contact sheets.

A later review should retain native/3D side-by-side screenshots with the mismatched region highlighted, the time/view, cause (geometry, rig, weight, animation, prop or cloth) and fix/recheck evidence. Match camera and scale before declaring a shape defect. Do not tweak topology to conceal a wrong pose or retime the source to conceal failed interpolation. UVs and Meshy texturing follow accepted animation/deformation.

Numeric seeds and ambiguities are deliberately reviewable. Palms, hidden knees, contacts and corpse depth cannot be certified before a 3D model exists. No human artistic acceptance or model deformation pass is claimed here.
