# MM6 Water Elemental native study

Identity: descriptors 532/533/534, ElemWater A/B/C; Water Beast, Water Spirit, Water Elemental. Native bitmaps wel; runtime groups wea/weB/weC. Native palettes 730/731/732. Native and restored 2D work remains unchanged in mm6_wel.

## Observed design

Sage-grey muscular male upper body, stern bearded face, curled gold-brown hair and beard, reddish bronze three-prong crown, upper-arm bands and bracers. Lower body is one green/gold scaled fish tail with two pale hip fins and a broad pale tail fluke. A three-prong trident is carried in the creature's right hand. Original profile walking exposes a long complete tail trailing behind; standing partially submerges this tail. No legs, no boots, no robe. A foam/waterline surrounds the base.

## Native motion

- Standing: one native frame, 0.1875 s nominal loop. Upright torso, right hand holds trident diagonally from lower-right to upper-left in body space; left hand relaxed. Add restrained breathing, hair/tail/fin motion without changing silhouette.
- Walking: six frames, 1.125 s. Tail elongates behind and undulates vertically, torso pitches slightly forward, weapon held forward/up. Keep root travel in gameplay; bind a measured model stride.
- Attack: six frames, 1.125 s. A ready; B draws trident upright to the right side; C torso arches back, left elbow lifts; D right arm reaches high/out, trident points outward/back as windup; E drives torso forward and swipes trident across to left/down; F recovers diagonal guard. Sweep stays in front of the body; preserve rigid weapon/right-hand grip. Native action2 aliases the same sequence.
- Cast: native uses attack artwork for Ice Bolt (30 percent chance, all tiers). Use a distinct runtime Cast role with the same recognizable windup, forward release from trident head socket, and recover. Gameplay timing remains native.
- Hit: six frames, 1.125 s. Backward recoil, right arm brings staff diagonally overhead, left palm rises, then recover.
- Fidget: six frames, 1.125 s. Small tail/body bob and guard adjustment. Author a larger but restrained 3-second idle variation.
- Death: six frames, 1.125 s. Torso rises/leans back, left arm opens, weapon becomes upright, body sinks into expanding foam until only crown/tail surface remains. SpriteDead is null: no corpse. Author complete sink by native end; Dead holds invisible below the surface.

## Owned motion selection before modelling

Previewed local humanoid-set SpearAttackR1/R3/R4 from front and side, plus UnarmedGetHitF2. Evidence: review/source_motion_sheet.jpg and full sampled joint rotations in work/source_motion.json, extremes in work/rom.json. Spear R1 is a thrust, R3 overhead/downward, R4 lateral from low guard; none matches the native one-hand wide high-to-low diagonal swing and merman stance. Author Attack/Cast from native wrist/weapon/body keys with continuous rig-space IK. Use the owned GetHitF2 torso recoil as a timing/magnitude source, adapted to a fixed merman tail and native raised-arm guard. No paid animation job needed.

## Reconstruction choices

Hidden submerged tail depth is inferred from walking profile. Body master uses a fully visible backward-curved tail for rigging; standing folds/submerges its lower curve. Tail fins retain native silhouette and can flex independently. Head has its own 1K texture set. Trident is a separate rigid prop fitted to measured fingers. Foam uses the existing alpha-cutout mesh route. Avoid biped auto-rig for this unsupported lower anatomy; source-frame upper-body rig plus a local tail chain.
