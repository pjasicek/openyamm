# Native and selected motion

Native source: read-only ../mm6_kni/native and inventory.json; indexed BMPs were not available in the current mounted source. Native PNG colours and ACT palettes were used. 59 unique images. Descriptors KnightPlate A/B/C = 565/566/567; palettes 760/761/762; frame scales 0.799988/0.899994/1.049988.

Standing has one held frame in directions 0–4, mirrored for 5–7. Walk has six frames, two ticks each = 0.75 s, five stored views plus mirrors. Attack/attack2 share six frontal frames with Image1 view reuse, two ticks each = 0.75 s; hit and fidget likewise. Death has five frames = 0.625 s; sixth image is held corpse. These reused frontal views provide no extra depth evidence.

Native attack lifts the right-hand curved blade, chambers across/behind the shoulder, slashes through the front and settles at waist carry. Left hand counterbalances; small weight shift, no large lunge. Native weapon has a broad curved edge, short notches/spines near its root, warm grip and cool pommel. Black mane trails on the rear.

G1 uses the local mannequin with source frames and sword stand-in. Selected: Standard Idle (Standing); ArmedWalk (Walking); RelaxRunForward (Running); Sword And Shield Slash (Attack and native-alias ranged Attack); UnarmedGetHitF1 (Hit); ArmedDeath1 (Death); Standing Taunt Battlecry (initial Fidget candidate, rejected for armour contact). Final Fidget: Standing Idle 02 Looking. Mixamo uses rest-delta copy, forearm roll to hand. Source views are review/g1_{front,left,three_quarter}.jpg, with posture samples in review/g1/posture.json. Rig stress extremes in work/rom.json.

Adaptations required on final body: ease one-shots from/to Standing; standing plant plus 20 percent leg/pelvis motion with discrete IK steps for Attack/Fidget; measured forward-facing blade speed establishes impact near native 0.75 s; Hit remains at most 0.75 s; Dead holds final Death pose. Native attack2 is a Dark ranged attack, not a separate spell cast; share Attack as native does, with SwordTip. Keep Running because table speed rises 250/300/350.

Observed: armour and mane, native carry/slash intent, palette regions and timings. Inferred: unseen armour rear connections and full 3D blade arc; local professional clips supply the motion between observed poses. Generated body references omit only the separately required sword.

Final measurements and the actual selected assets are recorded in README.md and HANDOFF.md.
