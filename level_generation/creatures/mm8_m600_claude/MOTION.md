# Nightmare m600 — anatomy and motion

Native authority: references_native/inventory.json and the labeled native sheets. Descriptors 151/152/153 are Nightmare A/B/C (Fear/Terror/Nightmare); palette 601 olive/red eyes, 602 violet/yellow eyes, 603 red/blue eyes. All native frame scales are 1.5. Physical melee only; no added missile or spell.

Anatomy: low elongated fleshy slime mound, two near-equal tall mouth stalks, a third mouth embedded in the front, five thin eye stalks, three embedded front eyes. Teeth remain rigid to their respective upper/lower mouth. No humanoid limbs, horse parts or equipment. Rear low lobes and wet folds are inferred from native stored back/profile images.

Native Standing, Attack, Death, Dead and Fidget reuse the front image for all directions. Walk and Hit have five genuine views with three mirrors. Unused stored standing views remain anatomy evidence, not unique action playback.

All native holds are 0.125 seconds. Walking: eight frames, 1.0 s; alternate neck sway with overlapping distal follow-through, a low rear-to-front body ripple, and continuously grounded skirt. Attack: eight frames, 1.0 s; mouth pods lift/brace then flare at 0.375–0.750 s and recover by 0.875 s. Flares are a local visual accent, not a projectile. Hit: five frames, 0.625 s; mouth pods gape and recoil with staggered small stalks. Death: na0, nb0, da0, db0, dc0, dd0, 0.750 s; stalks spread outward, curl down and settle in a compressed low mound. Dead: held xa0-like low heap. Fidget: five frames, 0.625 s, small mouth/eye movement. Standing: native held pose; authored subtle 3 s breathing/sway loop is an inference.

Implementation: local branched skeleton, curve/arc-length weights limited to each anatomical stalk, independent eye tips and jaw controls. Snake (mm6_cob_claude) informs distributed flexion; Ooze (mm6_ooz_claude) is provisional only and informs floor-anchored lump controls. The local animation library is humanoid/biped only; its clips cannot animate this anatomy. No paid rig or animation service.

Review gates: static likeness versus all five native views; pilot Walking and Attack at normal and half speed; then all clips, skin strain, floor contacts, mouth/eye clearance, held corpse, UV/texture parity, three palette tiers, all LODs and indoor/outdoor native/model captures. User artistic acceptance stays separate from technical completion.

Final portable collapse retracts stalk segments through explicit joint translations, preserving rigid pod/eye sizes. Body pooling uses the vertical local axis of floor-anchored lump bones; all deform bones retain normal scale inheritance. Eye1/Eye2 attach to the body, the other three small eye branches follow their measured lower mouth-stalk connections. Lower front jaw translation includes a 27 mm lift at the corpse pose to retain floor clearance. Final LODs protect the eye surfaces and iris UVs.

The front lip cage and all three embedded eye sockets share the rigid anatomical owners of their teeth/eyes, with soft boundary weights. This prevents the peristaltic body controls from pulling skin away during Attack.

User revision (2026-10-18): omit all baked attack flares/effects; the user will add FX separately. Attack keeps native timing and mouth/body motion, but the five eye stalks add staggered darts and rapid reversals with independent phase and smooth endpoint fades. Embedded eyes stay attached to their sockets. This overrides the native flare appearance described above.

Follow-up: the user judged the extra eye movement excessive. It is reduced to 20% amplitude with roughly half the reversal frequency, preserving only a subtle irregular twitch.
