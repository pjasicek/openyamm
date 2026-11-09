# Proposed MM6 BMonk integration coverage

Not executed: batch rule 4 reserves engine builds, regression runs and game launches for the orchestrator.

## Tier sizing case

Name: `mm6_bmonk_actor_model_tiers_share_one_size`.
Follow the existing `mm6_druidess_actor_model_tiers_share_one_size` case in
`game/outdoor/HeadlessOutdoorDiagnostics.cpp`; author the new case there during serialized integration.

- World: MM6. Map: `6d07.blv` (New Sorpigal temple).
- Summon merged monster IDs **583, 584, 585**, one of each, through the existing indoor scenario helper.
- Descriptors: `BMonk A`, `BMonk B`, `BMonk C`.
- Require valid posed model bounds after `WorldFxSystem::syncActorModels`.
- Require each upright height **162–198 game units**, target **179.899 units**.
- Require tier heights to agree within **1 game unit**.
- Require variants `mnk1_a`, `mnk1_b`, `mnk1_c` of the same model and animation/geometry payload.

## Role and timing checks

Require the nine named clips and both `Socket_Palm_Left` / `Socket_Palm_Right` nodes.
Walk and run both select Walking; Cast selects the distinct Cast clip.
Attack release is **0.716667 s** and Cast release **0.450000 s**, measured from fastest forward right-palm motion.
Hit is 0.5 s (within native 0.625 s), Death 2.433333 s; Dead holds its endpoint.
Check missile/effect origin at the right palm, including the native fire/air/water tier attacks.
No weapon, blade gate, weapon mesh or persistent fake spell geometry applies.

## Serialized game review

After installing `export/mm6_mnk1.glb` and merging `actors.yml`, run the existing MM6 actor regression suite
alongside this case. Capture all tiers beside their sprites indoors in `6d07.blv` and outdoors in `oute3.odm`.
Review front/side idle, walking cadence and floor contact, Attack/Cast with live projectiles, hit, full death and
held corpse. Check LOD transitions, shadows, night lighting and the shared cloth ramps.
The proposed stride 1.57 m targets the native 0.75 s cadence at the middle tier's speed 220 / scale 105.143;
real movement pacing and effects remain integration checks, not claims from the isolated viewer.
