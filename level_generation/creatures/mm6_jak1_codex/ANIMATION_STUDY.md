# Jackalman animation study — review round 2

Native motion remains the reference for identity and stance. The action clips now use local library momentum, with
retargeting and contact constraints. No paid animation was submitted. Native phase anchors are approximate.

| Clip | Seconds | Source and fit |
|---|---:|---|
| Standing | 3.000000 | Mixamo Standard Idle; retarget_mixamo rest-delta route; relaxed staff carry |
| Walking | 0.800000 | Humanoid ArmedWalk; planted gait, raised swing feet, periodic free-arm elbow pole |
| Attack | 2.512500 | 2Hand Staff / StaffAttack2, source frames 6–30, fixed two-handed shaft frame |
| Cast | 1.708333 | 2Hand Staff / StaffCastLAttack1, source frames 5–25, staff thrust and free-hand gesture |
| Hit | 0.500000 | UnarmedGetHitF1, 35% amplitude; carried staff and knees react |
| Death | 1.958333 | 2Hand Staff / StaffDeath1, full library fall; separate released staff |
| Dead | 1.000000 | Exact final Death pose held |
| Fidget | 3.287500 | Mixamo Standing Idle 02 Looking; planted stance and distributed arm twist |

Attack adds 0.4-second lead/out transitions around the selected source window before smoothness retiming. Cast adds
0.3-second transitions. Monotonic retiming preserves the fitted poses and shaft contacts; final durations are above.
The left foot makes a discrete 10 cm step with about 7 cm lift in Attack/Cast. The dominant hand controls the staff;
the off hand locks 29 cm up the shaft for the swing and opens before withdrawing. Relative grip rotation is zero.
The actual hook edge leads the target-facing blow at 0.989583333 s, tip speed 9.087852 m/s;
Cast launches from StaffTip at 0.927083333 s with forward-moving tip and target-facing staff axis.

Walking retains ArmedWalk. Its feet clear the floor by 8.5–8.6 cm; knees reach about 59°, stride
1.253289580 m. Run intentionally aliases Walking. A separate boundary audit found a free-arm elbow-pole
seam at about 35,000°/s². Circular pole filtering keeps the original hand path and leg motion, reducing the left-arm
seam to 2,307°/s²; the maximum across either arm at loop boundaries is 7,086°/s². Walking endpoint differences are
0.421 mm / 1.405°; Standing is 0.276 mm / 0.056°. The cyclic acceleration check passes the 20,000°/s² limit.

Death is StaffDeath1. Fingers release the staff early; a gravity/floor-constrained prop drop supplies secondary
motion only. The body fall, weight transfer and settling come from the library. Dead copies its exact final pose.
The corpse fits within 0.434 m above the floor. Upper-arm and forearm roll is distributed over twist helpers;
elbows flex about anatomical local −Z, and every clip is checked at 48 Hz, including Fidget.

Local source SHA-256: `2Hand Staff.glb` =
`68c00161969b7f5f9dec26e998ae297f2589b113e7318c88660242cc8bc1c7c1`;
Mixamo Standing = `cc21240bb83e5b16c67db1652a03a1c8935443f69ed1c4018aebc16bad43c743`;
Mixamo Fidget = `47a2a77fd0f2d91575b034e897745613454ba1136f3e1a0e35203999a2856aa0`.
Original library files remain in the ignored animation library; only retargeted role clips are exported.
`work/round2_sources.blend`, `work/round2_motion_sources.json` and `work/action_timing.json` preserve source windows,
retargeted probes and the timing map. The packed source and final GLBs are the current authoritative results.
