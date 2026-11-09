# Merchant native and motion study

Native ids 577/578/579, palettes 252/253/770. Standing is a held upright, arms hanging loose, wooden club suspended at right hip. Walking is six poses with alternating heel lift and small arm swing; stored views 0-4, mirrored 5-7. Attack/attack2 share six frontal poses: reach for club, draw beside hip, swing toward front, recover. Fidget is six near-identical frontal poses; preserve very subtle movement. Hit has six frontal recoil poses. Death has five front fall poses, separate prone corpse. Hidden sides and digits require modelling inference. Raw ticks divide by 16: Standing 0.125 s held; Walk/Attack/Hit/Fidget 0.75 s; Death 0.625 s native. Library Death may finish longer per runtime contract.

## G1 selection before modelling

Source mannequin renders are in review/g1 and review/g1_selected (front/side/three-quarter). Reject raw MaceAttackR1-R3 low guard and strong lunge. Reject Standing Torch Melee Attack 03 because the raised attacking arm is left, inconsistent with native right club. Select Standard Idle for upright Standing; ArmedWalk for Walking; Mixamo Jogging.fbx for Running (review round 1 replacement; fitted .8-second, 1.302 m stride = .84 m walking × engine 1.55); Sword And Shield Slash for right-handed Attack, planted and blended with ~20% discrete leg steps; UnarmedGetHitF1 planted for Hit, native duration; Standing Death Forward 02 for Death (library forward fall; left heel curl adapted below the tunic with source-knee IK and actual boot-floor contact), terminal Dead held; Standing Idle 03 Examine for Fidget attenuated strongly toward Standing, soles pinned, hands near thighs. No native spells, so animation.cast aliases Attack.

Clip timing remains source speed with lead-in/exit where needed, strike measured from actual club head trajectory after adaptation. Standing/Fidget use the hip-carried club, Attack draws it; handedness and grip are explicit. Hip-pouch part follows pelvis. Long closed tunic hem must be checked against legs at 48 Hz and driven by cloth chains if necessary.

## References and credits

HD generated body references reviewed for proportions, views, alpha and five fingers; back corrected to remove invented rear clasp. Skin and cloth colours will be measured against native palettes. Current official Meshy docs checked 2026-10-12: https://docs.meshy.ai/en/api/pricing, image-to-3d, rigging, retexture. Smart Topology meshy-t2 mesh-only 5 credits, rig 5, 2K retextures 10 each. No paid animation needed.

Review round 1: the earlier RelaxRunForward selection is rejected permanently. The current Running uses the local Mixamo jogging torso/arm cycle and the fitted planted stride. Club stays on the belt in Death and Dead.
