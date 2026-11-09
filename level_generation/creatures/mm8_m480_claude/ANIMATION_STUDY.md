# MM8 m480 Troll peasant

Native source: 160 original indexed BMPs, palette 481; family tiers 61–63 use palettes 481–483.
Inventory and original holds: `references_native/source_inventory.json`. Native standing is 125 ms;
walk and both attack descriptor slots reuse the 1 s walk. Hit 625 ms, death 750 ms (includes two recoil
frames), fidget 625 ms, corpse held. Unused m480a frames show a right-hand cross-body club sweep;
they have no authoritative playback timing. Native fidget raises the meat bone to the mouth, then lowers it.

Observed identity: long tapered arms, modest chest, projecting belly, forward head and mildly bent legs;
brown olive skin, grey mottled back and outer shoulders, swept brown crown crest, pointed ears,
small pale teeth, long pale hand claws, green ragged wrap, bare feet. Three fingers plus thumb and
three toes are the selected reconstruction of the legible digit tips. Bone club is required, separate
from the unarmed modelling pose; no armor or Ogre sword is carried over.

Selected local sources and hashes: `review/motion/selected_sources.json`; original-source mannequin
previews: `review/motion/`; 74 stress poses and measured extremes: `work/rom.json`.
Standing RelaxIdle, Walking ArmedWalk, Running weighted Mixamo Running (5), Attack SwordAttackR6,
Hit ArmedGetHitF1, Death UnarmedDeath1, Dead final death hold, Fidget RelaxDrink1 adapted to biting
or inspecting the bone. Source durations/rates retained. These are animation adaptations, not native
frame recovery. Mixamo backhand is rejected as an exaggerated long multi-phase swing. Mace clips
bend too deeply for the native gesture. The compact SwordAttackR6 starts across the chest and has a
clear one-hand sweep suitable for a blunt club. Native descriptor timing stays unchanged.

Fit checks: independently measure belly/spine, shoulder/elbow/wrist and hip/knee centers; long arm
lengths cannot be inherited from the Ogre. Hands use mesh knuckles and connected finger regions.
Run elbow flexion reaches ~116 degrees, so the club and free hand need explicit belly clearance.
Attack source upper-arm twist reaches 116.9 degrees and wrist bend 63.5 degrees: distribute twist and
correct the fitted wrist below 60 degrees; validate all clips and source extremes after weights.
Fidget must bring meat to the mouth without bone penetrating the head; use fitted hand targets.
Backward fall matches native direction; preserve real floor contact and hold a stable corpse.

HD image generation: built-in imagegen, actual unresized returns and prompts in
`references_hd/generation_runs.json`; input/native provenance in `references_native/`.
`00_three_quarter.png` is the selected Meshy body input; other body and head views guide construction.
All views are generated interpretations. Original native sprites remain identity and palette authority.

Full scope: body and bone club, fitted rig, eight roles, textures and three palette tiers, editable
blend and portable GLB, runtime LODs/attachments, binding, regression, indoor/outdoor GPU checks.
No user artistic acceptance is recorded. Production is in progress.
