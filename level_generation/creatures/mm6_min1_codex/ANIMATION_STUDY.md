# MM6 min1 — review round 1 motion

Attack uses local **Mixamo Great Sword Slash (2).fbx**, SHA-256 `26dfff746dafe5f536ec84a4b624d96ec61d5c61ab376d6d880589be177d5645`, through the bar1 source-frame/rest-delta retarget. Candidate studies are retained in review/round1/sources/. No raw library clip was copied or paid animation bought.
The old authored swing is superseded. The library motion supplies torso/weapon chamber, left preparation step, release, weight transfer, follow-through and recovery. Legs use planted, discrete approximately 20% source steps. Left lowest-sole lift reaches **8.906 cm**; the right foot stays planted. Smooth carrier/neck/elbow-pole fits clear the bull's wider body.
Right hand owns the axe; fixed shaft coordinates are R=0.70 m and L=0.35 m. The left hand never slides. Full palm frames, anatomical elbow planes and 60% forearm helper roll remove wrist flips. Smooth transported elbow poles replace per-frame pole searches. A 10% time stretch meets the acceleration gate.

| Role | Export duration | Provenance |
|---|---:|---|
| Standing | 2.000000 s | Local 2HandAxeIdle, native loose two-hand carry, flat soles. |
| Walking | 0.800000 s | Local 2HandAxeWalk, fitted to native bull body and axe. |
| Running | 0.600000 s | Fitted walk retimed to the native heavy trot. |
| Attack | 2.087500 s | Mixamo Great Sword Slash (2), fixed two-hand grip, left preparation step and fitted heavy swing. |
| Cast | 2.529167 s | Great Sword Slash (2) with an additional chamber hold before the spell release. |
| Hit | 0.500000 s | Local 2HandAxeGetHitF1, damped upper-body recoil with both hands on shaft. |
| Death | 1.600000 s | Local Death1 with native backward collapse, released axe and relaxed arms. |
| Dead | 1.000000 s | Final Death pose held. |
| Fidget | 2.000000 s | Local IdleAlert1 damped to native relaxed stance with both flat soles. |

Bake: 240 Hz, linear keys and sign-continuous quaternions. Actual sampled export durations are Attack 2.087500 s and Cast 2.529167 s. Cast adds a distinct 0.44 s chamber hold. Actual 120 Hz blade measurements: impact **1.075000 / 1.516667 s**, speed **12.779 / 12.771 m/s**, cutting-edge lead **0.7985 / 0.7981**, flat-normal share **0.1573 / 0.1568**.
Standing/Fidget soles use ankle rotation and leg IK, retaining idle body motion. Walking/Running feet point within 0.001° of travel. Walking lowest-sole peaks are **8.013 / 9.050 cm**, knees **63.51 / 63.13°** (slightly above the approximate 40–60° guideline). Running has a foot within 1 cm of the floor in **83.3%** of samples, using the fitted heavy trot.
Death retains the library-derived backward adaptation, releases after 1/6 s and ends in the held Dead pose. Native viewer anchors are approximate normalized phases, not identical timing. Runtime head look and role blending remain orchestrator checks.

## Review round 2

Accepted Attack spatial motion retained; early wind-up shortened by 20%; impact 0.947917 s.
Head/neck curves smoothed; rigid horn weights retained. Death now uses local Two Handed Sword Death:
single backward fall, axe release at 0.18 s, gravity drop and held terminal Dead pose.
Inspect Death at 0.1875, 0.375, 0.75, 1.5 and 2.4 s. Inspect the old Attack 34–39 phase after the timing shift.
Current shared-gate failures and missing head/neck/full-body/axe floor coverage are explicit in HANDOFF.md.
Historical custom gate passes are not evidence for this export. No game checks were run.
