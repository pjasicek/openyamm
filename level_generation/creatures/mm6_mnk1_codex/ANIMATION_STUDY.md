# Native observations and G1 selection

Authority: `../mm6_mnk1/native/`, native sheets in `../mm6_mnk1/references/`, inventory descriptor records.
Descriptors/monster ids 583 BMonk A (Novice Monk), 584 BMonk B (Initiate Monk), 585 BMonk C (Master Monk).
Palettes 774 brown / 775 navy / 776 red; native scale 0.699997. Speeds 200 / 220 / 240.
All tiers use elemental ranged attacks and separate spells: Fire Bolt / Lightning Bolt / IceBolt.
No weapons. Green light in native attack frames is effect evidence, not permanent mesh geometry.

Native standing: upright, arms folded at chest with hands concealed in sleeves. Walking: short measured steps,
arms held folded. Fidget: subtle hood turn/weight shift, arms still folded. Hit: brief torso recoil, left arm raises,
then returns. Attack: hands emerge and meet at belt, separate and rise near shoulders, then push forward and return.
Death: hands raise, body tips forward, knees buckle, prone body with arms forward; robe covers the legs.
Raw action lengths: walk/attack/fidget 12 ticks (0.75 s); hit/death 10 ticks (0.625 s).

## Local source choices (before modelling)

G1 rendered front, side and three-quarter on the set mannequin: `review/g1_*` and candidate sheets.
Source library inspected; no purchased animations. `source/clip_selection.json` is the exact local mapping.
Standing/Walking/Running use the upright Relax set, with native folded arm pose to be authored and short robe-safe
steps. Fidget reuses upright idle body motion with a native hood glance, not a drinking or combat taunt.
Attack uses Unarmed Cast Dual Attack 2 (two palms push forward); Cast uses Dual Attack 3 (asymmetric gathering,
forward release). Dual AOE2 and Summon1 were rejected for overhead arms absent from native sprites.
Hit is Unarmed Get Hit F1, limited to native duration. Death is Relax Laydown LayDown (kneel then prone), adapted
at the end to native straight covered legs. Dead holds the final death pose.

Unarmed sources have boxing stance/lunge. Plant on Standing, preserve about 20% of leg/pelvis movement as discrete
small IK steps, correct trunk yaw and ease from/to native idle. Check actual hand release speed for impact timing.
Professional motion keeps its original rate (30 fps); fit release near native 0.75 s, do not globally time-squeeze.
The source ROM is in `work/rom.json`; final source refresh and final-export gates must include the selected Cast3.
Source selection is complete; final creature posture, deformation and release gates are still pending.


## Final handoff corrections

Running uses Walking; the original RelaxRunForward G1 candidate was rejected because the native creature has no separate run and its speeds remain below the run threshold. Attack is 1.266667 s including the folded lead-in; Cast 1 s, Hit 0.5 s, Death 2.433333 s after expanding only the fast authored palm-unfold intervals. Dead was recreated from the complete final Death pose. Standing/Fidget retain folded arms with partly visible hands, an explicit artistic departure from the hidden native hands. All current gate results and review links are in README.md.
