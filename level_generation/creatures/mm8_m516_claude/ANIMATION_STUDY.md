# Thunder Lizard / Basilisk — native motion study

Source: all 170 m516 BMP hashes verified against ../mm8_m516/sources.json. Native action timing and frame names are recorded in references/native_actions.json. MM8 descriptor IDs 88–90 are Young Basilisk, Basilisk and Elder Basilisk; palettes 516/518/519. The three tiers share anatomy and timing. Native standing scale 1.0, collision height160/radius100, speeds220/240/260. These are ground creatures with melee paralyze/stone effects and no projectile or spell.

## Anatomy and rig choice
A slim dinosaur with a narrow muzzle, paired swept-back lateral frills, one midline crown/back spine row, short clawed forearms, powerful digitigrade hind legs, and a long tapering tail. Three fingers, three forward toes and a small rear dewclaw resolve native occlusion. No equipment. Fit hip, forward knee, backward hock, ankle and toe joints to the returned mesh, using the cockatrice local bird-leg IK method. Fit a multi-joint tail, torso, neck, jaw, arms and frills. The owned humanoid library cannot supply this anatomy; no paid humanoid rig or motion job is needed.

## Actions
- Standing: native sa is a held pose. Use a subtle breathing/head/tail loop with both feet planted.
- Walking: wa–wh, 1.0s. Alternating springy hind legs, torso lowered during travel, head stabilized against hip bob. Plant one foot while the other swings; place the hip toward the support foot and let the tail counter yaw/roll with delayed tip motion. Match stance sliding in the in-place clip to runtime stride length. Running is a separate faster fitted variation, not a human gait.
- Attack and Attack2: aa–ah, 1.0s. Crouch and gather, rear with open jaws and visible frills, drive the head forward/down, recover. Native impact clock remains 1.0s; any follow-through beyond impact is visual only. Feet anchor and tail counters the torso pitch.
- Hit: na–ne, 0.625s. Head/neck thrown back and sideways, one arm raised, then the head dips and shoulders twist; recover to standing. Preserve an asymmetric flinch.
- Death: na,nb,da–df, 1.0s. Recoil, rear and lose balance, legs fold, then fall sideways with tail trailing. Corpse is df, held. Fit the final side-lying mesh to the floor; head, limbs and tail must settle together.
- Fidget: fa–fe, 0.625s. Mouth opens, head rises, tongue/neck motion and small forearm/frill gestures, then settles. Feet remain planted.
- Cast binding may reuse Attack for this noncaster; do not add lightning or a new ability.

## Gates
Measure joints and anatomical weights on the actual mesh; inspect front/side/back, claws and mouth. Review all clips and extreme frames, ground clearance, jaw/frill/tail separation and loop seams. Quantify contact error and stance velocity, not just visual plausibility. Compare palette tiers against native ACT ramps. Verify exported GLB pose parity and reduced LODs, then native outdoor and indoor sprite/model pairs and actor regression. Artistic acceptance remains the user's.

## Attack correction from source frames

The ac front/rear views show a lifted left foot and head tilted back toward the creature's left, while the profile shows an almost upright rear. ae/af drive the head below the shoulders and across toward its right. Revision 02 adds the supporting-leg weight shift, taller head arc and diagonal follow-through. Authored anchors are retimed to 0/.18/.50/.68/.88/1.0/1.10/1.25 s so the strike retains the installed 1.0 s impact event; native frame times remain separately recorded in references/native_actions.json.
