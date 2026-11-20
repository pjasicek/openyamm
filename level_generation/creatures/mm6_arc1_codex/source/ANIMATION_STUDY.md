## Review round 5

Native side: forward tip +18 degrees, string ABOVE the limbs. Wrist/grip offsets 5.86%/7.94% of height. Shooting has fixed flat ankle anchors and reach-constrained pelvis. HANDOFF.md records memory tradeoff and unresolved gates.

> Review round 4 supersedes the carry/rest pose below. See [current handoff](../HANDOFF.md); shared runtime gates remain FAIL.

# Native and selected source motion

## Review round 2 — authoritative update

Standing/Fidget retain the accepted native relaxed pose and flat soles. The carry hand now closes on the grip;
the bow stays vertical and string-inward, with an outward arm sweep during Attack/Hit/Death transitions.
Walking uses the local humanoid source timing, aligned feet and a 9 cm swing; measured stride is
1.02417324 m. Running aliases Walking.

Attack remains the local Mixamo draw/recoil shot. Cast is now an exact copy under a distinct exported name:
release 1.200 s at Socket_Arrow_Release for both. This supersedes every earlier palm-cast choice in this historical
study. No new library action was purchased. Death remains the local humanoid death clip with fitted equipment clearance.

## Historical study (superseded where noted)

Native arc1 is female. The left hand holds the bow; the right retrieves an arrow over the right shoulder,
nocks/draws, releases and lowers. Timing is raw units × 8/128: Attack/Attack2 19 = **1.1875 s**, Hit 10 =
**0.625 s**, Walk 18 = **1.125 s**, Death 13 = **0.8125 s**, Fidget 12 = **0.75 s**. Descriptors 475–477 and
speeds 140/150/160 are from the mounted merged engine tables. Native standing target is 256 px × 0.699997.

Before Meshy modelling, G1 previews rendered the owned library on the source manikin from front, side and
three-quarter (`review/g1_*.jpg`, `g1_mixamo_*.jpg`). Selected sources are `anim_library/humanoid_set/2Hand Bow.glb`
Idle, Walk, GetHitF1, Death1 and Boost1, plus stored Mixamo Standing Draw Arrow and Standing Aim Recoil.
BowAttack1 was rejected as a melee swipe; the longer Shooting Arrow was studied but not used.
`work/rom.json` is the later formal numeric source-ROM report; it was not the pre-modelling visual gate.

Review round 1 supersedes the combat Idle/Boost selections: Standing is now an authored native measured rest
with calm breathing (2 s); Fidget is a relaxed glance and weight shift (2 s), with planted soles. Walking (0.8 s)
retains the source stride and now carries the bow at the side with relaxed arms and rest boundary blends.
Attack still combines Draw/Recoil, preserving the full-draw pose and 1.200 s release in its 1.73333 s duration.
Cast still releases from the right palm at 1.100 s in a 1.5 s clip. Attack/Cast/Hit return to rest, while Death
starts at rest and finishes in Dead. Hit remains 0.5 s with an added forward head reaction for quiver clearance;
Death 1.03333 s and Dead 1 s. No additional library animation was purchased. The review sheets use actual GLB seconds.

`review/delivery_validation.json`, `review/trace_export.json` and `review/release_gate.json` record final checks.
Native timings remain gameplay-owned; the orchestrator must check the listed longer follow-through clips in game.

