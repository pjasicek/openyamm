# Proposed integration regression

Case: **mm6_chain_fighter_actor_models_and_equipment**.

Use the existing MM6 actor-model regression setup in
game/outdoor/HeadlessOutdoorDiagnostics.cpp (the adjacent
mm6_thug_actor_model_tiers_and_mace case is the structural reference).

1. Load MM6 **6d07.blv**, initialize the indoor scenario, and record the initial actor count.
2. Summon native monster ids **535, 536, 537**, one of each.
3. Load sprite frames, effects and the merged actors.yml; sync posed actor models.
4. Require all three model bounds to be valid. Standing height must be **212–233 game units**;
   tier B/C must differ from A by at most **1 unit**. Native visual target is **222.298518**.
5. Find the three mm6_figc.glb instances. Require material variants **1, 2, 3**, each present once.
6. Require Standing, Walking, Running, Attack, Hit, Fidget, Death and Dead clips.
7. Require exactly two attachments: mm6_figc_axe.glb on **Axe**, and mm6_figc_shield.glb on **Shield**.
   Each attachment must inherit its parent's material variant.
8. Verify four colour LODs on body and both props, and four body shadow LODs.
9. Verify the melee impact event is **0.715 s**, inside Attack's 1.5 s interval.
10. Pose Death and Dead: attachment nodes must follow the recorded drop and remain outside the corpse.
    The sheathed left-hip sword belongs to the body and must remain with the pelvis.

Do not change native collision/gameplay dimensions. Sprite-visible height is the calibration reference.
The model ground offset is -1.512415 game units. The worst sampled 3D floor deviation after that offset
is approximately -0.972 game units during Running; use a two-unit visual floor tolerance.

After the focused regression, the orchestrator should run the affected MM6 actor suite and serial
indoor/outdoor visual checks (6d07.blv and oute3.odm). Capture all three tiers beside native sprites,
standing and moving, actual melee impact, hit, death/corpse, head look and LOD transitions.
The staged 45-degree yaw / 25-degree pitch look limits and 1.2-m stride need this runtime check.

This is a proposed test, not a claim that it has run. Batch rules prohibit this production session
from installing assets, modifying tests, building or launching the game.
