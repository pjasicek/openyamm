# MM8 Serpentman m524 native motion study

Native frames and exact timing: `work/native_timing.json`; original sources in
`../mm7_mm8_packed_outline/session_mm8_04/mm8_m524/`. Descriptors 94–96.

Observed anatomy: broad snake head, two three-clawed arms, narrow upright torso, continuous thick
ground tail. Brown/tan patterned dorsal skin, pale belly scutes and pointed dorsal neck marking.
No held equipment. All tiers use palette 524; SFT scales 1.299988, 1.599991, 1.899994.

Standing holds the chest upright over the curved tail base. Walk is a nine-frame, 1.125 s travelling
wave along the ground tail; torso/head height stays stable, with small arm counter-motion.
Attack is seven frames over 0.875 s: arms spread, upper trunk rises and mouth opens widely,
then the torso/head folds forward and the hands gather across the belly before recovery.
Hit is five frames over 0.625 s: head and torso recoil backward, open hands lift, then recover.
Death is six frames over 0.75 s: the same backward recoil continues into a backward fall across
the tail, arms thrown up, then the trunk rolls into a compact ground corpse with the claws visible.
Dead holds the corpse. Fidget is five frames over 0.625 s: small hand opening and torso/tail shifts.

Route: local serpent centreline rig and native-derived arm/jaw choreography, following the snake
and Medusa examples. The local animation library was inspected; its biped foot motions do not
cover this anatomy. No humanoid auto-rig or paid animation is needed. Fit tail segment frames to
world up, fingers by connectivity and rigid claws to their terminal finger bone. Keep the skull
and upper fangs fixed while the jaw opens.

Inferences: hidden depth and full tail centreline, continuous interpolation between sprite holds,
neutral open-S modelling pose. The runtime pose may coil more than the modelling pose.
Gameplay: all tiers are poison melee attackers with no spell or ranged attack in monster_data.txt.
Cast may alias Attack; no invented spell effect or weapon. Attack timing follows the existing
MM8 gameplay clock; export an explicit impact marker if longer recovery is authored.

Required review: tail wave with grounded underside, no self-crossing; bend volume at the base,
neck and shoulders; all three fingers and rigid claws; jaw ownership; backward collapse contact;
normal and slow playback from delivered GLB, all tiers and indoor/outdoor size comparison.
