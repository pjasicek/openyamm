# MM6 natf — review round 5: Attack

Attack follow-through corrected and verified. The right arm extends down/across with reduced forearm twist and a neutral wrist; shoulder volume is preserved through pose correction. Original frame 56 elbow bend changes from 112.22° to 46.86°. Mesh, weights, textures, slim skirt and the other eight animations are unchanged.

Wind-up (original frames 0–27) and recovery (64–end) run at **1.3× speed**; strike timing stays at 1×. Attack now lasts **1.833333 s**, with measured impact **0.572916667 s**. All three staged actor tiers are updated.

Shared gates, bindings and viewer checks pass: 7,640 PASS, no failures, 27 tier/clip switches and 18 complete normal/quarter-speed playbacks. Equipped triangle counts remain **14,419 / 5,719 / 3,797 / 3,007**.

- [HANDOFF](HANDOFF.md): exact files, hashes, timing and integration instructions.
- [Arm comparison](review/round5/arm_comparison.jpg), [Attack sheet](review/final/Attack.jpg), [browser close-up phase](review/viewer_attack_arm_56.png), [viewer](review/viewer/index.html).
- [Shared gates](review/round5/gates_final/gates.md), [preservation](review/round5/preservation.json), [final verification](review/round5/final_verification.json).
- [Actor blocks](integration/actors.yml), [round 4 checkpoint](review/round5/before/HANDOFF.md), [costume adaptation and prompts](references_hd/ADAPTATION.md).

**30/100 credits total; zero this round.** No commit, installation, game launch or build. The orchestrator installs through tools/install_model.py and merges the Attack impact values. The existing round 4 accepted-look texture exception remains in effect.
