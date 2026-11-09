# Native and library motion study — preparatory, not G1 completion

Native source: `../mm6_natf/native/` and `source/native_sources.original.json`. Actual restored animation is not used as motion authority.

| Role | Native sequence | Duration | Observed motion |
|---|---|---:|---|
| Standing | natfsta, 5 stored directions | 0.125 s hold | Upright, right arm down; shield loosely on left forearm; flat bare feet. |
| Walking | natfwaa–natfwaf, 5 directions | 0.750 s loop | Alternating narrow steps, shield comes forward; right blade travels with the arm. |
| Attack / attack2 | natfata0–natfatf0 | 0.750 s | Right arm opens, rises overhead, then sweeps down/forward while left shield guards; short advancing step and return. |
| Hit | natfwia0–natfwif0 | 0.750 s | Torso recoils backward, shield and right arm rise; recovers toward standing. |
| Death | natfdea0–natfdee0 | 0.625 s | Backward collapse, shield rotates above torso; ends supine/sideways. |
| Dead | natfdef0, bound through natfded | held | Both feet and body rest near the floor, shield down beside/under body. |
| Fidget | natffia0 twice, natffic0, natffid0, natffie0, natffif0 | 0.750 s | Small weight shift/breathing in the relaxed stance, not a taunt or drink. |

Each raw duration unit is 1/16 s; each listed image holds 2 units (125 ms). Fidget `natffid0` duplicates `natffic0`; `natffib0` exists but is unused. Actions use their native single view; standing/walking mirror stored views into eight directions.

The table name PeasantF4 is misleading: these are armed hostile Cannibal/Head Hunter/Witch Doctor variants. Witch Doctor (606) casts Deadly Swarm, 30% chance, Normal rank 2. It needs a distinct Cast clip. Both attack bindings use Attack, not Cast. There is no separate native casting action, so a restrained directed right-hand spell gesture is an inference. The blade looks attached along the right forearm, with fingers open in native standing/hit; do not force a sword fist before checking the mounting.

## Library preview results

`source/motion_candidates.json` contains exact local files, names and catalogue metadata. The existing bar1 preview/ROM scripts were copied locally, set to the source 30 fps before GLB import, and given a fixed per-clip camera covering all five sampled poses. One background Blender process, four threads; no source clip was purchased, copied or shipped. `review/source_clips_{front,left,three_quarter}.jpg` and 135 component renders show the source mannequin only. `work/rom.json` contains 86 stress poses across nine candidates; these are input ROM, not a final creature gate.

- **Attack:** DaggerAttackR2 is the better preliminary overhead-to-forward candidate. R3 folds the trunk farther forward. Both begin in a bent-knee guard and must be planted to native Standing, retaining about 20% source leg motion through discrete IK steps. Neither is selected for delivery until the real forearm blade's direction, cutting edge and contact path have been checked.
- **Cast:** ArmedCastRAttackHand1 reads as a right-hand thrust. Candidate only: plant the stance, hold the left shield, add lead-in so measured release is near 0.75 s. Source right wrist bend reaches 53.3 degrees and clavicle swing 40.5 degrees; re-pose/rig gates remain necessary.
- **Standing:** RelaxIdle is upright with relaxed arms and suitable as a starting reference. Final arms must accommodate the shield and right bracer without flared elbows; flat soles must be measured.
- **Walking:** RelaxWalkFemale3 has a hand-on-hip action and conspicuous hip sway. Reject its upper body for the armed character; compare ArmedWalk or a neutral Mixamo walk before choosing locomotion. Do not ship this source unchanged.
- **Running:** RelaxRunForward is upright but has clear airborne poses. Candidate requires the batch's low-flight/contact measurements; no run gate passes yet. Tier speeds are 220/250/280, so do not blindly alias run without checking scale and the 2.4 x scale threshold.
- **Fidget:** RelaxDrink1 is rejected: raises the right bracer toward the face and does not match native motion. A small Standing-based weight shift is the justified authored gap; no action clip has been authored.
- **Death:** RelaxLaydownLayDown is rejected: deliberate kneeling/prone laydown does not match the backward native fall. Next candidates are owned Mixamo Dying Backwards and suitable Dying variants; preview with retarget_mixamo.py before selection. Death must remain library-derived, with props and final corpse corrected locally.
- **Hit:** UnarmedGetHitF1 supplies useful recoil and fits under the native 0.75 s. Remove its boxing stance, ease from native standing and ensure both props move with the arms.

## Required later measurements

Use the actual fitted rig and final export at 48 Hz: anatomical elbow plane and <=5 degree hyperextension; upper-arm twist/palm direction; G4/G5 stretch; G6 signed-distance body/cloth/prop contacts; flat Standing/Fidget soles; Walking swing 8–12 cm with 40–60 degree mid-swing knees at human size; Running contact/flight; per-clip posture. Measure the blade blow while directed at the target, not from source name or the catalogue's impact hint. Preserve source rates, add wind-up instead of globally slowing clips. Nothing here certifies those gates.


## Final production selection (supersedes preliminary statuses above)

Standing = Mixamo Standard Idle; Walking = ArmedWalk; Running = RelaxRunForward; Attack = DaggerAttackR2; Cast = ArmedCastRAttackHand1; Hit = UnarmedGetHitF1; Death = Mixamo Dying Backwards; Dead = final Death hold; Fidget = small Standing-derived authored gap. Final gates, actual blade timing, full playback and per-clip posture are in HANDOFF.md and review/final/. Native runtime run aliases Walking. All library clips were reused without a purchase.

## Review round 3 supersedes Running and Attack

Running now uses local Mixamo Standard Run; RelaxRunForward is no longer an active source. The existing downward library attack is fitted to the requested diagonal cross-body path. See review/round3/provenance.json, running_jitter.json and HANDOFF.md for current evidence. Other roles are unchanged from round 2.
