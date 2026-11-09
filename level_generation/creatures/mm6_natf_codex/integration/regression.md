# Proposed native integration regression — orchestrator-owned

Case: `mm6_natf_actor_model_tiers_follow_sprite_scales`.

Use outdoor Bootleg Bay `outd2.odm` and indoor Temple of Tsantsa `6t3.blv`. Summon merged ids **604, 605, 606** (PeasantF4 A/B/C) at separated clear points. Merge the exact blocks in `actors.yml` and install only the three final GLBs listed in HANDOFF.md.

Assert the complete MM6 registry configures, all tiers obtain bounds and distinct variants, and model presentation preserves actor HP, positions and action timers. Standing body height should be **175–179 game units**, centred on native **177.099241** (253 px × 0.699997); tier ratios within 2%. Binding scale is **107.886252682**, from measured standing body height **1.641536680 m**. Do not calibrate from descriptor height 158, the attack envelope or the corpse.

Exercise Standing, Walking, Hit, Fidget, Attack, Cast, Death and Dead at all distances. Check attached `ForearmBlade` and `LeafShield`, all four body/prop LODs and body shadow LODs, planted rest soles, skirt containment, dull grey blade, grey/olive/red equipment and stable brown skin. Running is retained as a separately validated review clip; runtime `animation.run` aliases Walking to retain the native single walking gait. Stride length is **1.199315995 m**.

Attack melee/ranged impact **0.614583333 s**; no melee launch socket. Distinct Cast for the Witch Doctor, impact **0.833333333 s**, launch node `B_R_Hand`. Check missile/spell launch, recovery pacing, attachments through the backward fall and Death/Dead continuity. Inspect close/middle/far transitions and indoor/outdoor lighting against the native sprite family.

Staged `check_bindings.py` passes with no BAD lines; receipt: `../review/final/check_bindings.txt`. No native build, game launch, regression execution, installation or actors registry merge was performed by this production session. These remain the orchestrator's batch steps.

## Review round 2 integration focus

Install all three refreshed runtime GLBs and merge the staged actor impact times (0.78125 s for all tiers). Check overhead anticipation/right-foot step/downward crouch, strong Hit recoil, moving shield arm in every active role, visible Fidget, immediate Death and shield release at 0.12 s/settle at 0.45 s. Dead should hold the grounded fall with the shield beside it. Inspect both habitats, all palettes and LOD transitions. Browser/shared gates pass; native execution remains delegated.

## Review round 3

Install accepted exports through tools/install_model.py and merge the staged YAML: run now selects Running, all melee/ranged impacts are 0.6979166666666666 s. Verify a smooth running head/pelvis cycle, especially frames 7→8, and the upper-right to lower-left slash with head/torso follow-through. Stride setting is unchanged. This session performed no native game launch or build.
