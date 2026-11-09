# Proposed integration checks — not run in this batch

Primary case: `mm6_lich_actor_model_tiers_share_the_native_height` in the existing actors regression suite.
Load world `mm6`, indoor map `6d19.blv` (Agar's Laboratory). Summon monster IDs **568, 569, 570**
(`BLich A`, `BLich B`, `BLich C`) at the same floor height, with enough separation for their casting hands.
Resolve the common `worlds/mm6/models/mm6_lch.glb` and skins `lch_a`, `lch_b`, `lch_c`.

Expected standing geometry height: **190–210 world units** for each tier, with differences between tiers below
**0.1 units**. The source target is 285 opaque sprite pixels × 0.699997 = 199.499 units;
scale 111.6 maps the measured Standing height (1.783–1.788 m) to 199.0–199.5 units.
Walking height should stay in **190–210 units**. Collision dimensions and gameplay stats stay authoritative in
monster data; these are visual bounds, not a request to alter collision.

Assert eight clips, all three skins, four color LODs and four shadow LODs, and finite evaluated poses.
Play Standing, Walking, Attack, Cast, Hit, Death, Dead and Fidget. Hit finishes at 0.733 s before the native 0.75 s
cutoff. Death lasts 1.3 s; verify the engine finishes it before holding Dead. Fidget lasts 1.4 s and uses the
existing follow-through path. Native speeds 180/200/220 remain below the 267.84 run threshold.
Check stride_length 1.284 while moving, all tiers at equal size, no unexpected foot sliding or floor penetration.

Additional case: `mm6_lich_actor_casts_use_the_authored_palm_sockets`.
A and B have Dispel Magic; C has no table spell, but still uses the common model clips. Verify ranged release
at authored Attack 0.729 s from `Socket_Palm_Right`, and spell release at authored Cast 0.625 s from
`Socket_Palm_Left`. Native wind-up remains gameplay-owned. Verify the shared hand FX uses the palm aliases.
Check that the neck/head look follows the party while standing and stops during Death/Dead.

For native GPU comparison, capture the three tiers beside their native sprites indoors in `6d19.blv` and
outdoors in `oute3.odm`, using the existing actor-model comparison workflow. Include close face/hands,
cast release, corpse, near/far color LODs and all shadow qualities. Check native palette brightness under actual
engine lighting: the web viewer uses three.js lighting and bakes review-only tier colors.

After copying only the staged GLB and merging `actors.yml`, run the existing actor suite and the above focused
cases. Batch rules prohibited this session from installing, building, launching the game or running that suite.
