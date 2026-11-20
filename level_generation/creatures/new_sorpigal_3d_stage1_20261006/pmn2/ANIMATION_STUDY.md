# MM6 staff-carrying mage, pmn2; Apprentice/Journeyman/Mage descriptors 610–612: complete native animation study

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

- Keep right staff grip in every state; compare shaft direction/ends across all five genuine walk views.
- Overhead c/d left-hand support is ambiguous: choose collision-free palm contact/hover from projected fingers and record choice.
- Beard, mantle and bracers clear forehead/shaft during overhead passage; free left palm opens in b/e.
- Hit lifts left knee; do not force both feet to ground. Death ends supine, staff low at side.

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

Unused artwork remains in the source inventory, not playback: pmn2fib0.
Pixel-identical images/holds are retained exactly: {"pmn2fif0": "pmn2fia0", "pmn2fie0": "pmn2fib0", "pmn2fid0": "pmn2fic0"}.

## Standing

[Unannotated native contacts](source/standing_native.png) · [Existing original 2D landmark overlay](guides/standing_landmarks.png)

**Source views:** front, front-right, right, back-right, back. 5/6/7 mirror 3/2/1; not extra depth evidence.

**Motion spacing:** Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.

**End rule:** hold current pose indefinitely.

### a — 0 ms: held ready

**Native frames:** pmn2sta0, pmn2sta1, pmn2sta2, pmn2sta3, pmn2sta4. Hold 125 ms. Upright staff at character right; left hand below hip, feet apart, beard faces front.

**Main driver:** Quiet torso supports right elbow and shaft, no breathing cycle.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Broad chest upright; shoulders level. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both boots apparently supported; knees soft, exact depth inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Face forward, chin neutral; no compulsory jaw motion.

**Prop/visibility:** Staff upright, upper end above right shoulder; tip near floor, not evidence of cane weight.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: held ready → hold current pose indefinitely. Hold indefinitely. Do not turn a single native pose into an invented breathing or weight-shift cycle.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Walk

[Unannotated native contacts](source/walk_native.png) · [Existing original 2D landmark overlay](guides/walk_landmarks.png)

**Source views:** front, front-right, right, back-right, back. 5/6/7 mirror 3/2/1; not extra depth evidence.

**Motion spacing:** Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**End rule:** loop to first pose at 750 ms, keeping velocity/contact continuity.

### a — 0 ms: incoming first foot

**Native frames:** pmn2waa0, pmn2waa1, pmn2waa2, pmn2waa3, pmn2waa4. Hold 125 ms. Front shows incoming shoe/sole and opposite trailing foot; profile separates stride depth.

**Main driver:** Pelvis progression and incoming hip swing lead; opposite arm balances.

**Right chain:** Shoulder retracts; elbow beside waist, wrist near abdomen; grip remains continuous as shaft trails. Initial abduction/forward elevation/elbow flex ≈ 20/-5/100°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -5°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Right leg reaches forward; heel/flat-foot contact WINDOW, not proven exact plant; other leg trails/toe-off. Initial R/L knee flex 15/25° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Staff hand trails waist, shaft sweeps back in right profile.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: incoming first foot → first support/passing. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: first support/passing

**Native frames:** pmn2wab0, pmn2wab1, pmn2wab2, pmn2wab3, pmn2wab4. Hold 125 ms. Feet approach passing alignment; profile trailing heel lifted.

**Main driver:** First support leg accepts weight; opposite hip begins forward swing.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -2°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Right foot supports, left heel lifts/pass begins; support assignment fitted across all views. Initial R/L knee flex 8/40° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Staff hand rises, lower shaft slants back in profile.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: first support/passing → opposite knee lift. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: opposite knee lift

**Native frames:** pmn2wac0, pmn2wac1, pmn2wac2, pmn2wac3, pmn2wac4. Hold 125 ms. Opposite knee/shoe forward/up, support leg straighter; profile confirms bent swing leg.

**Main driver:** Swing hip/knee flex lifts foot; pelvis modestly rises over support.

**Right chain:** Shoulder advances, elbow opens toward target, wrist ahead of chest; keep full upper-arm/forearm lengths. Initial abduction/forward elevation/elbow flex ≈ 20/45/45°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 5°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Right supports; left knee bends and shoe clears floor; do not plant lifted foot. Initial R/L knee flex 8/60° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Staff nearly upright ahead, right elbow opens and hand reaches chest height.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: opposite knee lift → opposite incoming foot. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: opposite incoming foot

**Native frames:** pmn2wad0, pmn2wad1, pmn2wad2, pmn2wad3, pmn2wad4. Hold 125 ms. Opposite leg forward/sole showing; first leg trailing in profile.

**Main driver:** Opposite hip completes swing, pelvis advances, arms reverse continuously.

**Right chain:** Shoulder advances, elbow opens toward target, wrist ahead of chest; keep full upper-arm/forearm lengths. Initial abduction/forward elevation/elbow flex ≈ 20/45/45°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 5°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Left incoming heel/flat-foot contact WINDOW; right toe-off/trailing, avoid long double-foot pins. Initial R/L knee flex 25/15° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Staff still ahead but slopes forward; grip height starts lowering.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: opposite incoming foot → opposite support/passing. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: opposite support/passing

**Native frames:** pmn2wae0, pmn2wae1, pmn2wae2, pmn2wae3, pmn2wae4. Hold 125 ms. Feet close again, trailing first heel raised; body crosses support.

**Main driver:** Opposite support accepts weight; first hip swings forward.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw 2°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Left supports; right begins swing, lifted heel/toe-off fitted to side/back views. Initial R/L knee flex 40/8° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Staff approaches upright/carry, right elbow folds.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: opposite support/passing → first knee lift/loop prep. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: first knee lift/loop prep

**Native frames:** pmn2waf0, pmn2waf1, pmn2waf2, pmn2waf3, pmn2waf4. Hold 125 ms. First leg lifted/bent, opposite support; profile resolves swing shoe behind/under knee.

**Main driver:** First hip/knee flex and forward swing prepare next contact, opposite arm travels forward.

**Right chain:** Shoulder retracts; elbow beside waist, wrist near abdomen; grip remains continuous as shaft trails. Initial abduction/forward elevation/elbow flex ≈ 20/-5/100°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle advances slightly; upper arm reaches forward low, elbow soft, wrist ahead of hip. Initial abduction/forward elevation/elbow flex ≈ 8/22/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Pelvis yaw about ±4–8° with step, ribcage counters slightly; restrained forward lean and bob, no torso scaling. World trunk tilt 3°, rib yaw -5°, pelvis height delta +0.005H (all inferred centers).

**Support/legs:** Left supports, right foot clears; through final 125 ms extend toward right incoming contact without foot slide. Initial R/L knee flex 60/8° (±15°; hidden knees uncertain).

**Head:** Head looks along travel, small pitch compensation; crown bob follows pelvis rather than separate head bounce.

**Prop/visibility:** Staff retracts/back, shaft tip sweeps behind; no repetitive cane plant.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: first knee lift/loop prep → loop to first pose at 750 ms, keeping velocity/contact continuity. Continuous periodic spline/quaternion motion; no easing to a stop at every 125 ms anchor. Contacts are windows: fit heel-to-flat then toe-off from genuine profile/back views, use fixed-length chains. Match opposing arms/shaft, modest pelvis bob and root speed to stride. Inspect 62.5 ms midpoints and 687.5/750 ms loop seam.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Attack

[Unannotated native contacts](source/attack_native.png) · [Existing original 2D landmark overlay](guides/attack_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**End rule:** return to native standing at 750 ms.

### a — 0 ms: ready/open

**Native frames:** pmn2ata0. Hold 125 ms. Right staff extends out, left fingers open near hip; feet remain broadly spaced.

**Main driver:** Small knee softening and right-shoulder preparation.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Chest front, pelvis quiet. World trunk tilt 3°, rib yaw 0°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Both feet support; begin small knee bend. Initial R/L knee flex 10/10° (±15°; hidden knees uncertain).

**Head:** Eyes toward target, chin slightly down.

**Prop/visibility:** Staff near vertical; right grip continuous.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: ready/open → draw and free-hand lift. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: draw and free-hand lift

**Native frames:** pmn2atb0. Hold 125 ms. Right hand near temple with staff strongly foreshortened; left palm rises in front of shoulder.

**Main driver:** Knees lower pelvis while right shoulder draws shaft back; left palm counters toward target.

**Right chain:** Clavicle rises; elbow out below shoulder; forearm folds up beside temple, wrist clear of face. Initial abduction/forward elevation/elbow flex ≈ 55/60/120°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Shoulder raises forward/out; elbow bends below hand, wrist beside face/chest as open protective palm. Initial abduction/forward elevation/elbow flex ≈ 40/65/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal forward (+Y), fingers upward/outward along hand, fan 10–20°, curl 0–15°; thumb spread. Adjust forearm roll for palm plane; wrist within ±15°.

**Trunk/hips:** Ribs hunch slightly; no large backward step. World trunk tilt 8°, rib yaw 8°, pelvis height delta -0.030H (all inferred centers).

**Support/legs:** Feet stay spaced; knees bend together. Initial R/L knee flex 25/25° (±15°; hidden knees uncertain).

**Head:** Chin down, gaze under brows.

**Prop/visibility:** Shaft depth/axial angle uncertain; keep length, fit end projection.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: draw and free-hand lift → overhead brace. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: overhead brace

**Native frames:** pmn2atc0. Hold 125 ms. Staff diagonal above brow; both forearms raised, crouch visible.

**Main driver:** Clavicles elevate and elbows guide staff overhead; knee flex makes clearance.

**Right chain:** Shoulder elevates with clavicle/scapula; elbow out/up, forearm above brow, wrist follows overhead arc. Initial abduction/forward elevation/elbow flex ≈ 65/120/95°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm raises beside head; elbow points outward, forearm almost upright; wrist approaches overhead shaft. Initial abduction/forward elevation/elbow flex ≈ 55/110/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Overhead hand lies close to shaft. Native pixels do not resolve a closed grip: begin with supporting palm normal up/toward wood, fingers partly curled 20–60°, thumb separated. Test supporting-contact and near-contact fits; do not invent a firm second grip without matching the silhouette.

**Trunk/hips:** Trunk slightly forward, shoulders raised; pelvis lowered. World trunk tilt 12°, rib yaw 5°, pelvis height delta -0.050H (all inferred centers).

**Support/legs:** Both knees flex; apparent contact retained unless side fit requires small pivot. Initial R/L knee flex 35/35° (±15°; hidden knees uncertain).

**Head:** Duck chin under shaft, eyes still target.

**Prop/visibility:** Diagonal in frontal plane; left support/contact unresolved, shaft never cuts skull.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: overhead brace → horizontal overhead passage. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: horizontal overhead passage

**Native frames:** pmn2atd0. Hold 125 ms. Staff nearly horizontal across eyes, hands high; lowest guarded posture.

**Main driver:** Right elbow/forearm carries a continuous overhead arc; left forearm accompanies near shaft.

**Right chain:** Shoulder elevates with clavicle/scapula; elbow out/up, forearm above brow, wrist follows overhead arc. Initial abduction/forward elevation/elbow flex ≈ 65/120/95°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm raises beside head; elbow points outward, forearm almost upright; wrist approaches overhead shaft. Initial abduction/forward elevation/elbow flex ≈ 55/110/100°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Overhead hand lies close to shaft. Native pixels do not resolve a closed grip: begin with supporting palm normal up/toward wood, fingers partly curled 20–60°, thumb separated. Test supporting-contact and near-contact fits; do not invent a firm second grip without matching the silhouette.

**Trunk/hips:** Deepest short crouch; avoid separate torso bounce. World trunk tilt 15°, rib yaw 0°, pelvis height delta -0.060H (all inferred centers).

**Support/legs:** Both feet close to original standing positions; knee flex peaks. Initial R/L knee flex 40/40° (±15°; hidden knees uncertain).

**Head:** Brow under staff, head dips, beard clear of forearms.

**Prop/visibility:** Horizontal projection at brow; avoid interpreting this as a ground slam.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: horizontal overhead passage → release across body. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: release across body

**Native frames:** pmn2ate0. Hold 125 ms. Staff diagonal across chest; left open palm reaches character left, head/shoulders turn that way.

**Main driver:** Right shoulder lowers/rotates shaft; left arm opens as opposing balance, knees extend.

**Right chain:** Clavicle rises; elbow out below shoulder; forearm folds up beside temple, wrist clear of face. Initial abduction/forward elevation/elbow flex ≈ 55/60/120°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle rotates upward; upper arm out/front; elbow opens, wrist near shoulder-height reach. Initial abduction/forward elevation/elbow flex ≈ 70/60/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.

**Trunk/hips:** Ribcage turns character left, pelvis turns less; rising. World trunk tilt 5°, rib yaw -20°, pelvis height delta -0.025H (all inferred centers).

**Support/legs:** Both feet support, slight sole pivot inferred. Initial R/L knee flex 20/20° (±15°; hidden knees uncertain).

**Head:** Head turns left modestly with chest, no independent spin.

**Prop/visibility:** Diagonal down across chest; right grip fixed, free left clears arc.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: release across body → restore upright staff. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: restore upright staff

**Native frames:** pmn2atf0. Hold 125 ms. Staff upright again, left arm low/out, body near ready.

**Main driver:** Right elbow lowers to ready; free arm settles last.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Chest returns front and upright. World trunk tilt 0°, rib yaw -3°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Knees relax toward standing, boots remain grounded. Initial R/L knee flex 8/8° (±15°; hidden knees uncertain).

**Head:** Face returns front, beard settles.

**Prop/visibility:** Upright right-hand carry; recovery ends at 750 ms.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: restore upright staff → return to native standing at 750 ms. Preparatory a→b is slower; b→c accelerates toward reach/overhead lift; c→d and d→e form the continuous fastest passage, with no stop at d. e→f decelerates/retracts; final f→standing interval restores rest. Review 187.5, 312.5, 437.5 and 687.5 ms subkeys. These are proposed checks, not recovered impacts; no damage-event time is inferred.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Hit

[Unannotated native contacts](source/hit_native.png) · [Existing original 2D landmark overlay](guides/hit_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**End rule:** return to native standing at 750 ms.

### a — 0 ms: recoil begins

**Native frames:** pmn2wia0. Hold 125 ms. Chin lifts, ribs recoil; right staff arm out, left knee starts lifting.

**Main driver:** Upper trunk recoils first, hip counterbalance retains support.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Short backward rib tilt, pelvis mostly below trunk. World trunk tilt -10°, rib yaw 0°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Right boot carries more weight; left heel/contact uncertain. Initial R/L knee flex 5/20° (±15°; hidden knees uncertain).

**Head:** Chin up/back, gaze briefly above target.

**Prop/visibility:** Staff tips away with arm, does not detach.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: recoil begins → recoil and lifted knee. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: recoil and lifted knee

**Native frames:** pmn2wib0. Hold 125 ms. Staff diagonal outward, head tilted back/side; left knee visibly raised.

**Main driver:** Rib recoil and left hip flex; right arm widens for balance.

**Right chain:** Clavicle rotates upward; upper arm out/front; elbow opens, wrist near shoulder-height reach. Initial abduction/forward elevation/elbow flex ≈ 70/60/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Shoulder travels back; elbow stays low beside ribs; wrist trails hip, away from clothing. Initial abduction/forward elevation/elbow flex ≈ 8/-18/20°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point/curl into palm (proximal curl 50–80°, tips flex), palm normal inward/back, thumb outside index rather than buried. Keep fist silhouette but preserve separate digits.

**Trunk/hips:** Back/side lean restrained; right shoulder pulled out. World trunk tilt -18°, rib yaw 8°, pelvis height delta -0.010H (all inferred centers).

**Support/legs:** Right support, left knee/foot in swing; no left-foot pin. Initial R/L knee flex 8/50° (±15°; hidden knees uncertain).

**Head:** Head up and sideways, neck not elongated.

**Prop/visibility:** Shaft diagonal away from body, tip sweep stays clear of boot.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: recoil and lifted knee → fold staff near face. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: fold staff near face

**Native frames:** pmn2wic0. Hold 125 ms. Right staff near face, left knee still raised; left arm begins opening.

**Main driver:** Right elbow folds as trunk changes from recoil toward crouch.

**Right chain:** Clavicle rises; elbow out below shoulder; forearm folds up beside temple, wrist clear of face. Initial abduction/forward elevation/elbow flex ≈ 55/60/120°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Backward lean reduces, rib yaw slight. World trunk tilt -3°, rib yaw -5°, pelvis height delta -0.025H (all inferred centers).

**Support/legs:** Right supports; left leg begins lowering. Initial R/L knee flex 15/40° (±15°; hidden knees uncertain).

**Head:** Head tilts away from right hand, chin begins descending.

**Prop/visibility:** Staff near vertical beside face; bracer/nose clearance.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: fold staff near face → low forward recovery. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: low forward recovery

**Native frames:** pmn2wid0. Hold 125 ms. Head/chest low, left hand opens outward, boots near floor.

**Main driver:** Hip/knee flex absorbs recoil; arms balance the fold.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal down (−Z), fingers forward/down along reach, fan 8–18°, curl 0–20°; thumb separated. Pronation travels through forearm, wrist softly extended for contact.

**Trunk/hips:** Forward fold with lower pelvis. World trunk tilt 20°, rib yaw 0°, pelvis height delta -0.050H (all inferred centers).

**Support/legs:** Left lands softly; both knees bend, no sudden leg-length change. Initial R/L knee flex 35/35° (±15°; hidden knees uncertain).

**Head:** Chin down, head follows chest.

**Prop/visibility:** Shaft leans slightly; tip may approach floor without automatic plant.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: low forward recovery → rise. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: rise

**Native frames:** pmn2wie0. Hold 125 ms. Body rises, head still down, staff upright, left hand lowers.

**Main driver:** Knee extension raises pelvis before full head recovery.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Ribs unfold, shoulders descend. World trunk tilt 10°, rib yaw 0°, pelvis height delta -0.025H (all inferred centers).

**Support/legs:** Both boots support, knees extend gradually. Initial R/L knee flex 20/20° (±15°; hidden knees uncertain).

**Head:** Head still modestly bowed.

**Prop/visibility:** Staff upright; grip never resets.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: rise → ready restoration. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: ready restoration

**Native frames:** pmn2wif0. Hold 125 ms. Head/front shoulders return, staff vertical, left arm lower/out.

**Main driver:** Torso/head recover after legs; left hand settles.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Upright, slight residual hand widening. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both feet supported, soft knees. Initial R/L knee flex 8/8° (±15°; hidden knees uncertain).

**Head:** Face forward, chin neutral.

**Prop/visibility:** Return to standing at 750 ms.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 625–750 ms: ready restoration → return to native standing at 750 ms. Start recoil promptly, peak body/guard deformation in b→d, then recover through remaining anchors. Preserve order of torso/legs/arms and avoid sinusoidal symmetric recoil. Review every 62.5 ms midpoint, facial/hand clearance and final standing boundary.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Death

[Unannotated native contacts](source/death_native.png) · [Existing original 2D landmark overlay](guides/death_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**End rule:** reach separate corpse at 625 ms; last death anchor remains at 500 ms.

### a — 0 ms: backward recoil

**Native frames:** pmn2dea0. Hold 125 ms. Chin up, staff upright/out; left knee rises as balance breaks.

**Main driver:** Ribs/head recoil while right hip briefly supports.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Back tilt begins; pelvis below ribs. World trunk tilt -10°, rib yaw 0°, pelvis height delta -0.005H (all inferred centers).

**Support/legs:** Right support predominates, left foot lifting. Initial R/L knee flex 10/25° (±15°; hidden knees uncertain).

**Head:** Chin up, no neck stretch.

**Prop/visibility:** Staff upright outside right shoulder.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 0–125 ms: backward recoil → lose support. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: lose support

**Native frames:** pmn2deb0. Hold 125 ms. Chest arches back, right staff raised diagonally, free hand opens.

**Main driver:** Center of mass leaves support; root begins fall while knees buckle.

**Right chain:** Clavicle rotates upward; upper arm out/front; elbow opens, wrist near shoulder-height reach. Initial abduction/forward elevation/elbow flex ≈ 70/60/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Upper arm opens away from torso; elbow soft, wrist out and forward as a counterweight. Initial abduction/forward elevation/elbow flex ≈ 40/25/45°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.

**Trunk/hips:** Whole-body backward tilt increases; local spine modest. World trunk tilt -30°, rib yaw 5°, pelvis height delta -0.080H (all inferred centers).

**Support/legs:** Right foot may pivot; left remains loose, neither both feet pinned. Initial R/L knee flex 25/45° (±15°; hidden knees uncertain).

**Head:** Head follows backfall, face upward.

**Prop/visibility:** Staff rotates with right grip, no brace planted.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 125–250 ms: lose support → fall back. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: fall back

**Native frames:** pmn2dec0. Hold 125 ms. Torso approaches horizontal above ground, knees draw, left palm open to side.

**Main driver:** Root falls backward; arms spread, knees flex to preserve leg lengths.

**Right chain:** Shoulder opens as trunk falls; elbow mostly open, wrist out from body. Root rotation carries arm, not an impossible spine bend. Initial abduction/forward elevation/elbow flex ≈ 65/20/25°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Shoulder opens as trunk falls; elbow mostly open, wrist out from body. Root rotation carries arm, not an impossible spine bend. Initial abduction/forward elevation/elbow flex ≈ 65/20/25°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.

**Trunk/hips:** Root rotation drives near-horizontal trunk; do not bend spine 70°. World trunk tilt -65°, rib yaw 8°, pelvis height delta -0.250H (all inferred centers).

**Support/legs:** Foot contacts release/roll as body drops; occluded depth inferred. Initial R/L knee flex 45/65° (±15°; hidden knees uncertain).

**Head:** Head follows torso, face up.

**Prop/visibility:** Shaft near horizontal outside body, fixed grip retained.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 250–375 ms: fall back → floor arrival. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: floor arrival

**Native frames:** pmn2ded0. Hold 125 ms. Body supine, two boot soles toward viewer; free hand by head, staff at ground left.

**Main driver:** Back/hips arrive at floor, small limb/cloth lag.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.

**Trunk/hips:** Trunk horizontal, pelvis low; floor contacts collision fitted. World trunk tilt -90°, rib yaw 10°, pelvis height delta -0.400H (all inferred centers).

**Support/legs:** Boots separate, knees partly bent; support now back/hips/limbs. Initial R/L knee flex 35/45° (±15°; hidden knees uncertain).

**Head:** Head depth obscured by mantle/body; choose clear neck pose.

**Prop/visibility:** Staff rests low to side, does not pass through ground.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 375–500 ms: floor arrival → settle. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: settle

**Native frames:** pmn2dee0. Hold 125 ms. Nearly same supine silhouette; boot spacing and hand near head remain.

**Main driver:** Small settling after impact, no additional roll or flourish.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.

**Trunk/hips:** Keep floor body silhouette; damp residual rotation. World trunk tilt -90°, rib yaw 10°, pelvis height delta -0.400H (all inferred centers).

**Support/legs:** Back/hips rest, boots settle without sliding. Initial R/L knee flex 35/45° (±15°; hidden knees uncertain).

**Head:** Head held with only inferred settling.

**Prop/visibility:** Shaft stays low/grounded by same grip.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Follow actual body acceleration with small delay; do not let secondary motion change the native limb silhouette or prop grip.

**Next interval:** 500–625 ms: settle → reach separate corpse at 625 ms; last death anchor remains at 500 ms. Collapse accelerates as support fails; root translation/rotation and knee fold carry motion, never squash/scale the actor. Floor arrival decelerates, limbs/cloth settle. Review 187.5, 312.5, 437.5, 562.5 and 625 ms. The final 125 ms must connect death e to the separate corpse, using explicitly inferred collision-free root roll and arm arcs. Keep last observed pose at 500 ms and fit the hidden path to actual corpse at 625 ms; do not replace or skip either endpoint.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Corpse

[Unannotated native contacts](source/corpse_native.png) · [Existing original 2D landmark overlay](guides/corpse_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.

**End rule:** hold current pose indefinitely.

### a — 0 ms: held supine remains

**Native frames:** pmn2def0. Hold 125 ms. Native pmn2def0 lies supine with separated boots, free hand near head, staff low to side.

**Main driver:** None; static remains rather than animated breathing.

**Right chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Arm rests out from trunk; elbow/wrist settle near floor. Occluded depth must be chosen from collision-free anatomy. Initial abduction/forward elevation/elbow flex ≈ 65/0/30°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Palm normal up (+Z, with modest forward component), fingers extend outward/forward, fan 10–20°, curl 0–20°; thumb abducted/opposed. Supinate forearm; do not obtain palm-up with extreme wrist bend.

**Trunk/hips:** Match corpse silhouette, root/pelvis low. World trunk tilt -90°, rib yaw 10°, pelvis height delta -0.400H (all inferred centers).

**Support/legs:** Floor-supported back/hips/limbs; hidden contacts inferred. Initial R/L knee flex 35/45° (±15°; hidden knees uncertain).

**Head:** Head near ground, maintain beard/mantle clearance.

**Prop/visibility:** Shaft remains fixed and floor-clear; no spontaneous release.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–125 ms: held supine remains → hold current pose indefinitely. Hold indefinitely at native remains. No twitch, breathing, fading, extra blood or disappearance has source evidence here.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Fidget

[Unannotated native contacts](source/fidget_native.png) · [Existing original 2D landmark overlay](guides/fidget_landmarks.png)

**Source views:** front. Image1: frontal bitmap reused for every angle.

**Motion spacing:** Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**End rule:** loop to first pose at 750 ms, keeping velocity/contact continuity.

### a — 0 ms: rest hold

**Native frames:** pmn2fia0. Hold 125 ms. Playback repeats fia0 at 0 and 125 ms; fib0 is unused artwork.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Broad chest upright; shoulders level. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both boots apparently supported; knees soft, exact depth inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** Staff upright, upper end above right shoulder; tip near floor, not evidence of cane weight.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 0–250 ms is a repeated native rest-pose hold. Do not add an intermediate gesture merely because playback has two entries.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### b — 125 ms: duplicate rest hold

**Native frames:** pmn2fia0. Hold 125 ms. Playback repeats fia0 at 0 and 125 ms; fib0 is unused artwork. All supplied native views are pixel-identical to the 0 ms anchor; retain the same constrained pose.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Broad chest upright; shoulders level. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both boots apparently supported; knees soft, exact depth inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** Staff upright, upper end above right shoulder; tip near floor, not evidence of cane weight.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 125–250 ms: duplicate rest hold → small face/head change. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable. Preserve identical source-pose constraints; no invented limb change between identical holds.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### c — 250 ms: small face/head change

**Native frames:** pmn2fic0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Broad chest upright; shoulders level. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both boots apparently supported; knees soft, exact depth inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** Staff upright, upper end above right shoulder; tip near floor, not evidence of cane weight.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 250–375 ms: small face/head change → held face variation. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### d — 375 ms: held face variation

**Native frames:** pmn2fid0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest. All supplied native views are pixel-identical to the 250 ms anchor; retain the same constrained pose.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Broad chest upright; shoulders level. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both boots apparently supported; knees soft, exact depth inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** Staff upright, upper end above right shoulder; tip near floor, not evidence of cane weight.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 375–500 ms: held face variation → return expression. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable. Preserve identical source-pose constraints; no invented limb change between identical holds.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### e — 500 ms: return expression

**Native frames:** pmn2fie0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Broad chest upright; shoulders level. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both boots apparently supported; knees soft, exact depth inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** Staff upright, upper end above right shoulder; tip near floor, not evidence of cane weight.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 500–625 ms: return expression → loop rest. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

### f — 625 ms: loop rest

**Native frames:** pmn2fif0. Hold 125 ms. Small native head/face silhouette change; arms, belt, feet and clothing remain almost identical to rest. All supplied native views are pixel-identical to the 0 ms anchor; retain the same constrained pose.

**Main driver:** Only subtle head/face variation; no hand gesture or mandatory breathing.

**Right chain:** Upper arm low/out, elbow below hand; forearm forward to waist/lower chest; wrist aligned to shaft. Initial abduction/forward elevation/elbow flex ≈ 25/20/90°; ±20/20/15° fitting ranges.

**Right palm/fingers:** Palm normal toward shaft; fingers wrap tangentially around wood (curl 65–95°), thumb opposed across index. Wrist nearly straight; forearm roll follows shaft axis. Fixed grip offset, no sliding or changing shaft length.

**Left chain:** Clavicle quiet; upper arm beside ribs, elbow points back/out slightly, wrist below hip. Initial abduction/forward elevation/elbow flex ≈ 5/0/10°; ±20/20/15° fitting ranges.

**Left palm/fingers:** Fingers point down along hand, modest proximal curl 15–35°, fan 0–8°; palm normal inward toward thigh/body, thumb relaxed away from index. Forearm roll subtle; wrist nearly straight.

**Trunk/hips:** Broad chest upright; shoulders level. World trunk tilt 0°, rib yaw 0°, pelvis height delta +0.000H (all inferred centers).

**Support/legs:** Both boots apparently supported; knees soft, exact depth inferred. Initial R/L knee flex 5/5° (±15°; hidden knees uncertain).

**Head:** Fit actual crown/eyes/beard/nape pixels; allow only a small ~0–5° head turn/tilt as inference, not a large look-around. Jaw/expression movement is unresolved.

**Prop/visibility:** Staff upright, upper end above right shoulder; tip near floor, not evidence of cane weight.

**Secondary surfaces:** Mantle remains short and follows shoulders with small delayed hem motion; rope knot fixed to waist, rope tips and pouches lag hip acceleration by a little. Boots/bracers remain firm while joints flex at their ends. Lag is quiet here; do not invent cloth flutter or hair cycles.

**Next interval:** 625–750 ms: loop rest → loop to first pose at 750 ms, keeping velocity/contact continuity. Preserve repeated-pose holds exactly; subtle changes can interpolate, but do not manufacture six independent gestures. Guard shaft/hand roll is continuous and subdued. Match 750 ms loop seam and keep support/whole-body pose stable. Preserve identical source-pose constraints; no invented limb change between identical holds.

**Verify:** Exact native silhouette and available matching views, palm/finger directions, fixed limb/prop lengths, shoe contact, head/arm/cloth clearance and half-interval arc. Original 2D seeds are retained in JSON where present; empty seeds mean unmeasured. Restored-only transferred seeds are excluded.

## Rig and animation acceptance

Start with geometry comparison and the family stress poses in the anatomy guide. After receiving the rig, use stock walk/run only to diagnose weight collapse, crossed joints, arm-to-torso attachment and foot volumes. Then build native walking first, verify all five genuine views and the seam, repair weights, and construct the other six native states. Review every observed anchor and proposed midpoint, not only contact sheets.

A later review should retain native/3D side-by-side screenshots with the mismatched region highlighted, the time/view, cause (geometry, rig, weight, animation, prop or cloth) and fix/recheck evidence. Match camera and scale before declaring a shape defect. Do not tweak topology to conceal a wrong pose or retime the source to conceal failed interpolation. UVs and Meshy texturing follow accepted animation/deformation.

Numeric seeds and ambiguities are deliberately reviewable. Palms, hidden knees, contacts and corpse depth cannot be certified before a 3D model exists. No human artistic acceptance or model deformation pass is claimed here.
