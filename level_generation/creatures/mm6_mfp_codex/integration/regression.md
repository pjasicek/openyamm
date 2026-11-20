# Orchestrator integration and regression — review round 3

Install export/mm6_mfp.glb and export/mm6_mfp_knife.glb with tools/install_model.py --world mm6. The installer writes accepted assets_source models and runtime copies; never copy exports directly into assets_dev. Merge the three staged descriptors.

Test mm6_mfp_peasantf3_codex_review3 on oute3.odm and 6d19.blv; summon 601/602/603. Standing height 177.099241 world units ±5%; tiers agree within .1. Scale 107.495710585, yaw −π/2, walk stride .9 m, Running stride 1.395 m. Ordinary speeds 200/220/240 and boosted running.

Attack retains the cut through .666667 s, ends 1.125 s; impact remains .65625 s for melee/ranged/cast. Check edge-leading contact, direct hand-at-side recovery and return to Standing, no slow tail. Noncasters alias cast to Attack. Knife visible during Attack only.

Inspect clean face, neck seam, midriff/arms, crisp sari and green/red/blue blouse tiers. Check larger shared atlas support, memory and performance on desktop/Android. Inspect four LOD/shadow switches at 700/550/220/88 px for seams, specular noise, mip bleeding.

All eight clips: Hit waist/skirt clearance, seated Attack grip, UnarmedRunForward2 arm swing with planted stride (no RelaxRunForward), upright rest, flat soles, visible walk lift, hands, braid/skirt, fall and held corpse. Check head look and disabled look during Death/Dead.

Run ordinary actor-registry, save/load, indoor/outdoor and unaffected-descriptor regressions. This session did not build/launch/install the game.

Review round 3: install only the revised body; knife and actors.yml are unchanged. Verify Death lasts 2.144444444 s, with old frame 100 at 1.666666667 s, and transitions to the unchanged Dead pose without a pop. Appearance and all other clips were accepted; this delivery only changes Death timing.
