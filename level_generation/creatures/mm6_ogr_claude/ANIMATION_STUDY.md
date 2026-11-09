# Ogre selected motion — revision 03

The user chose Running A, Attack A, Fidget A and current Hit conditional on valid transitions. These replace only the corresponding three roles; the accepted head/model and five other clips remain unchanged.

| Role | Duration | Selected source |
|---|---:|---|
| Running | 25/30 s | `mixamo_library/Running (5).fbx`, fitted weighted run (A). |
| Attack | 68/30 s | `mixamo_library/Standing Melee Attack Downward.fbx`, overhead chop (A). |
| Hit | 0.5 s | Retained `Armed.glb:ArmedGetHitF1`. |
| Fidget | 3.2 s | `mixamo_library/Neck Stretching.fbx` (A). |

Source hashes and the original comparison choices remain in `review/motion_options/sources.json`. Neutral standing calibration, measured palm/grip axes, fixed-length bones, grounded support foot and the accepted grip/cloth/twist fitting are preserved. Weighted Running uses 12 degrees of right-arm clearance and 10 degrees of outward wrist tilt. Its source loop differs by 0.51 degrees at the endpoint; the last three frames now close that seam. No new acting was authored.

The chop's blade reaches its forward downward strike at frame 26 (0.866666667 s); `revision_03/checks/attack_tip.json` records the measured path. All Ogre melee bindings use this impact. The engine fits that wind-up to the native 0.75 s attack (15.6% timing difference) and plays the remaining 1.4 s follow-through at source speed, interruptible by Hit/death/a new action. Fidget can finish after its native action length while standing. Gameplay clocks and damage timing are unchanged.

Current Hit runs for 0.5 s and holds until the native 0.75 s state ends. The real game-path regression checks entry at 0/30/60 ms and exit at 0/60/120 ms against displayed/expected local poses from Standing, Running, Attack and Fidget. It passes with the installed GLB; the lower reaction pose remains part of the chosen clip. Death and teleport transitions retain the engine's immediate behavior.

The source clips and production model share bone names/rest transforms. Only animation streams were replaced in the existing export/runtime/viewer GLBs; the retained Hit and appearance buffers are byte-identical. Current checks and screenshots are under `revision_03/`. Running/Walking selection and distance-driven gait remain governed by existing game speed rules; choosing Running does not replace Walking.

## Historical revision 02 study


The user's 2026-10-11 feedback supersedes the original authored Standing, Fidget and Death. All four requested replacements come from the local humanoid library; no animation service credits were spent. Source previews, hashes and decisions are in `revision_02/motion/selection.json` and the neighbouring contact sheets. The previous delivery remains under `revision_02/previous/`.

Native authority remains `../mm6_ogr/inventory.json` and `../mm6_ogr/references/`. Native walk/attack/hit/death/fidget have six 0.125-second holds; Standing and Dead are held frames. The user selected library choreography for this revision, so Death now falls backwards instead of matching the native forward corpse.

| Role | Duration | Selected source and fitting |
|---|---:|---|
| Standing / idle | 2.0 s | `Relax.glb:RelaxIdle`, upright library breathing; fitted sole height. |
| Walking | 0.8 s | Retained `Armed.glb:ArmedWalk`; original proportion compensation and 1.25 m stride. |
| Running | 0.8 s | `Relax.glb:RelaxRunForward`, selected for its upright torso instead of the rejected hunched Armed run; loop closed over the last four source frames. |
| Attack | 1.2 s | Retained `1Hand.glb:SwordAttackR6`, including the existing 0.4 s ready lead and 0.683 s impact; replacement head fitted for clearance. |
| Hit | 0.5 s | Retained `Armed.glb:ArmedGetHitF1`. |
| Fidget | 2.0 s | `Armed.glb:ArmedIdleAlert1`, library look-around. |
| Death | 1.3 s | `Unarmed.glb:UnarmedDeath1`, library backward fall. ArmedDeath1 was also fitted and rejected for shoulder/head clashes. |
| Dead | 1.0 s | Held final pose of the selected Death, including the sword. |

Source timing and body choreography are retained. Fitting consists of world-rotation retargeting on measured source-frame bones, the existing arm proportion allowance, solved fingers around the retained sword, twist distribution, floor clearance, head/neck offsets and a constant 30-degree Death wrist roll for blade clearance. The cloth retains leg-following weights and uses a measured rest-shape correction; no replacement body acting was authored.

`revision_02/motion/dense_clearance.json` checks 48 Hz subframes: maximum head/shoulder depth 6.56 mm and cloth depth 0.40 mm. The exported curved sword has no detected body penetration. Source-relative rotation traces have zero flags; all eight roles completed normal and quarter-speed playback. Export validation checks closed Standing/Walking/Running/Dead endpoints and unchanged animation samples through LOD/variant/attachment processing. These samples do not prove every possible runtime blend or head-look combination.

The bindings retain cast/ranged aliases to Attack without adding gameplay capabilities. With `gameplay.corpses=keep`, the library corpse stays visible; the normal corpse replacement setting remains available. Native runtime evidence and the focused Ogre binding regression are recorded in `revision_02/runtime/` and `revision_02/checks/`.
