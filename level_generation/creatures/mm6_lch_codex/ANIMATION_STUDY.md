# Native motion and selected local sources

Native metadata: ../mm6_lch/sources.json. A/B/C descriptors 568/569/570, palettes 763/764/765.
All native frame scales 0.699997; Standing 300px canvas (content height measured at final scale step).
Action raw ticks: standing 2, walk 12, attack/attack2 12, hit 12, death 10, corpse 2, fidget 12.
Native 16 ticks/second gives attack and hit 0.75s. The attack e frame is lit and both palms spread forward.

G1 library candidates were rendered on the source mannequin from front, side and three-quarter BEFORE modelling.
Selected: RelaxIdle -> Standing; RelaxWalkForward -> Walking; UnarmedCastDualAttack2 -> Attack; UnarmedCastDualAttack1 -> Cast; UnarmedGetHitF1 -> Hit; UnarmedDeath1 -> Death; final death pose -> Dead;
RelaxDrink1 -> Fidget (open hand, touching crown rather than holding a cup). Run will reuse Walking if speeds stay
below the engine threshold. No weapon and no blade gates apply.

Adaptation: the Unarmed set crouches and staggers. Plant its pelvis/legs on Standing, preserve upper-body source
motion with yaw correction, add about 20% leg motion as discrete IK steps, and ease from/to Standing. Keep source
speed, shift wind-up near the native 0.75s, measure palm release for events. Relax sources remain upright; damp any
excess sway. Open skeleton hands should retain their finger geometry and only modest finger curl. Backward death
matches the native direction; the crown stays attached on this pass (the native briefly detaches it).

Final Hit fits 0.733 s: 4-frame entry, 13-frame sampled source, 5-frame return; arms at 70% excursion.
Fidget has six-frame entry and return. Cast fingers hold the open Standing pose. Shoulder cloth follows Clavicle,
not UpperArm: the initial upper-arm attachment entered the skull during Cast.
