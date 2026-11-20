# Final natm animation study

Native source is the read-only ../mm6_natm project: 59 frames at 125 ms per frame. Standing and walking have five stored directions. The native attack is a raised one-handed spear thrust. The native death falls backward; the early forward-collapse candidate was rejected.

| Runtime role | Local library source | Duration |
|---|---|---:|
| Standing | Mixamo Standard Idle.fbx | 3.000000 s |
| Fidget | Mixamo Standing Idle 02 Looking.fbx | 3.208333 s |
| Walking | humanoid_set/Armed.glb, ArmedWalk | 0.958333 s |
| Running | humanoid_set/Relax.glb, RelaxRunForward | 0.729167 s |
| Attack | humanoid_set/1Hand.glb, SpearAttackR1 | 1.583333 s |
| Cast | humanoid_set/Armed.glb, ArmedCastLAttack1 | 1.583333 s |
| Hit | humanoid_set/Unarmed.glb, UnarmedGetHitF1 | 0.625000 s |
| Death | Mixamo Standing React Death Backward.fbx | 3.333333 s |
| Dead | Exact held Death endpoint | 0.041667 s |

G1 library mannequin sheets are in review/g1. G2 measurements are in work/proportions.json. The fitted rig keeps the source bone frames, measured segment lengths and anatomical elbow planes; helpers distribute deformation roll. Rest-delta Mixamo retargeting moves source forearm roll into the hand before the deformation helpers distribute it.

Standing/Fidget use planted soles and relaxed native carry. Walk/run foot placement follows measured sole geometry. Walking stride is 0.592592593 m; the engine's running multiplier 1.55 gives 0.918518519 m. Attack/Cast/Hit retain the library torso/arm motion, with planted leg adaptation, continuous elbow poles and fixed spear grip. Death uses the library backward reaction, with signed-contact panel adjustments. No paid library jobs or procedural replacement of the main action clips.

The fastest target-facing spear-tip interval is centered at 0.489583333 s. The left-palm spell release is 0.447916667 s. Cast is deliberately distinct for the Witch Doctor's Fire Bolt.

Final front/side/three-quarter sheets are in review/sheets; the three-tier review viewer is review/viewer/index.html. Review round 1 folds the feathers above the floor and adds 8 mm of smooth fall-only clearance for coarse body proxies. The shared runtime floor report now passes; see HANDOFF.md.
