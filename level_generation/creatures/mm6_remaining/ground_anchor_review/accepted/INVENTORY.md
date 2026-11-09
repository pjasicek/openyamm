# Accepted MM6 anchor inventory

Reproduce: `python3 level_generation/creatures/mm6_remaining/accepted_anchor_audit.py`.

Checked 49 originally accepted families, 2848 frame records. 34 now await placement reacceptance. 11 unfinished redo families excluded.

## Findings

Current repair progress and artifact-bound visual decisions: [placement_queue.json](placement_queue.json).
- Acceptance hash failures: 12. Visible atlas/master mismatches: 0. 0 frames differ only in fully transparent RGB, which is not an anchor defect.
- 0 frames in 0 families have reference-centering errors [] in logical X/Y pixels. The native source is centered with integer division when its width has opposite parity to the shared canvas. This can add a half-pixel animation step; mirrored views reverse the sign. See `mm6_remaining/prepare_configured.py:57`. The correct reference offset is fractional; at 2x export it is representable as one physical pixel. Do not repair accepted art automatically without checking the registration and atlas together.
- 32 families have multiple native BMP sizes. Originals did not universally share a fixed canvas. Their center/bottom actor anchor must be retained when mapping them into the shared logical canvas.
- 857 frames exceed 2 logical pixels in bottom-silhouette difference. This is a review queue, not proven foot-placement defects. Airborne poses, effects, weapons and changed anatomy affect bounds.
- Animation/scale metadata mismatches against original staged manifests: 0. This is an offline asset audit; no GPU playback or installed-package certification was performed.
- 2256 frames have saved secondary residual evidence; 592 do not have it in the supported fields. Existing visual reviews may contain additional evidence. Neither group is newly certified by this audit.

## Visual checks performed on 2026-09-22

The following are initial diagnostic findings, before the repairs tracked in placement_queue.json. Static images only, not watched playback. These do not certify every pose.

- Cockatrice `cktwlkb4`, before repair: head/dorsal registration holds while the feet are approximately 28.6 logical pixels too high. The neighboring `cktwlka4` sole is close, so the sequence changes leg/body proportions. Translation alone cannot align both head and feet. Revisit anatomical scale/pose registration and the selected artwork, then inspect the full walk-4 sequence. [Marked contact](../../../mm6_ckt/redo_2x/review/walk_4_redo_01_registered_contact.png).
- Cobra `cobwald2`: the reported 133.7-pixel contact X residual marks different positions along the continuous snake body. It is not evidence for a 133.7-pixel translation. Use the same identifiable anatomical point in both images. [Marked contact](../../../mm6_cob/redo_2x/review/walk_2_redo_02_registered_contact.png).
- PeasantF4 `natfded0`: the native sole candidate lies under the prone torso while the restored point lies by a foot. The reported 75.6-pixel X error is invalid correspondence; pelvis and actual matching feet need separate annotation. [Marked contact](../../../mm6_natf/redo_2x/review/death_corpse_redo_01_registered_contact.png).
- Cleric attack A-D: inspected native-size head/neck/sole contacts. These provide useful local evidence, but do not establish the other actions or subpixel equality. [Marked contact](../../../mm6_cle/redo_2x/review/placement_attack_0_00.png).

## Required before strict placement acceptance

Preserve the native per-frame actor origin, including half pixels. Verify a motion-appropriate anchor and an independently identified anatomical feature on every pose at native size or larger. Review frame-to-frame residual changes, loops, action transitions, mirrored views and sheet boundaries. Do not flatten intentional native bobbing or lifted feet. Fix whole-frame translation only when both features agree; incompatible residuals require a scale/anatomy correction. Apply any correction equally to base/masks and re-export, checking crop reconstruction and acceptance hashes. Use timed playback for remaining motion uncertainty. Existing accepted status is not proof of exact motion.

## Family inventory

Positive bottom delta means restored artwork extends lower than native, in native logical pixels. The 2 px cutoff is triage only, not an acceptance tolerance. Silhouette bounds can follow weapons, wings or effects. Secondary residuals are recorded evidence, not a fresh anatomical measurement. No family is certified pixel-perfect by this audit.

| Family | Frames | Native sizes | Geometry errors | Bottom delta min/max | >2 px frames | Secondary evidence frames | Secondary max abs px |
|---|---:|---:|---:|---:|---:|---:|---:|
| BArcher A | 58 | 1 | 0 | 0.00 / 0.00 | 0 | 0 | missing |
| Barbarian A | 57 | 33 | 0 | 0.00 / 0.00 | 0 | 0 | missing |
| BBat A | 78 | 53 | 0 | -34.00 / 9.50 | 33 | 78 | 14.56 |
| BBeholder A | 48 | 9 | 0 | -25.50 / 15.00 | 46 | 48 | 19.88 |
| Bloodsucker A | 78 | 1 | 0 | -15.00 / 31.50 | 57 | 78 | 25.37 |
| Cleric A | 59 | 1 | 0 | -6.50 / 5.50 | 16 | 59 | 7.46 |
| Cobra A | 59 | 3 | 0 | -17.00 / 18.00 | 17 | 59 | 20.00 |
| Cockatrice A | 59 | 44 | 0 | -16.50 / 16.50 | 21 | 59 | 29.00 |
| DemonFly A | 54 | 2 | 0 | -13.00 / 6.50 | 17 | 49 | 28.42 |
| Demon A | 67 | 15 | 0 | -4.50 / 4.50 | 16 | 61 | 33.35 |
| DragonCave A | 59 | 14 | 0 | -7.50 / 9.50 | 29 | 58 | 28.96 |
| BDragonFly A | 78 | 18 | 0 | -28.50 / 19.50 | 61 | 78 | 24.12 |
| DragonLand A | 59 | 1 | 0 | -5.50 / 3.50 | 8 | 59 | 22.45 |
| Druidess A | 59 | 3 | 0 | -7.50 / 5.00 | 21 | 59 | 32.48 |
| BDwarf A | 59 | 3 | 0 | -10.00 / 4.00 | 21 | 59 | 32.92 |
| ElemAir A | 24 | 1 | 0 | -30.00 / 3.00 | 18 | 24 | 25.32 |
| ElemEarth A | 59 | 1 | 0 | -1.00 / 1.50 | 0 | 58 | 17.75 |
| ElemFire A | 47 | 1 | 0 | -17.00 / 7.50 | 28 | 47 | 19.75 |
| FighterChain A | 59 | 25 | 0 | -10.00 / 5.50 | 23 | 53 | 24.00 |
| FighterLeath A | 59 | 13 | 0 | -11.00 / 6.50 | 24 | 58 | 32.22 |
| BGenie A | 60 | 1 | 0 | -19.00 / 7.00 | 26 | 56 | 23.09 |
| BGhost A | 48 | 1 | 0 | -14.50 / 13.00 | 29 | 18 | 5.75 |
| BGoblin A | 59 | 1 | 0 | -2.00 / 0.00 | 0 | 0 | missing |
| Guard A | 59 | 37 | 0 | -10.50 / 8.00 | 21 | 59 | 22.44 |
| Jackalman A | 59 | 9 | 0 | -7.00 / 5.50 | 20 | 59 | 40.31 |
| KnightPlate A | 59 | 13 | 0 | -7.50 / 1.50 | 17 | 59 | 24.70 |
| BLich A | 59 | 1 | 0 | -6.50 / 9.00 | 21 | 59 | 42.38 |
| BMedusa A | 59 | 3 | 0 | -12.00 / 4.50 | 14 | 59 | 19.21 |
| Merchant A | 58 | 27 | 0 | -0.50 / 0.00 | 0 | 0 | missing |
| BMonk A | 57 | 2 | 0 | -0.50 / 0.00 | 0 | 0 | missing |
| Nobleman A | 71 | 20 | 0 | -11.00 / 5.00 | 19 | 71 | 25.55 |
| BOoze A | 54 | 5 | 0 | -2.00 / 1.50 | 0 | 47 | 14.49 |
| Ogre A | 60 | 1 | 0 | -0.50 / 0.00 | 0 | 0 | missing |
| PeasantF1 A | 59 | 19 | 0 | -9.00 / 6.50 | 24 | 53 | 44.54 |
| PeasantF2 A | 59 | 1 | 0 | -6.50 / 8.50 | 24 | 59 | 33.35 |
| PeasantF3 A | 59 | 2 | 0 | -3.50 / 4.50 | 11 | 59 | 24.49 |
| PeasantF4 A | 59 | 34 | 0 | -19.00 / 4.00 | 29 | 57 | 37.46 |
| PeasantM1 A | 59 | 36 | 0 | -8.50 / 13.00 | 24 | 59 | 47.46 |
| PeasantM2 A | 59 | 43 | 0 | -12.00 / 11.50 | 14 | 59 | 54.78 |
| PeasantM3 A | 59 | 1 | 0 | -13.50 / 8.50 | 26 | 59 | 28.78 |
| PeasantM4 A | 59 | 16 | 0 | -7.50 / 6.50 | 13 | 59 | 18.11 |
| BRat A | 59 | 1 | 0 | -0.50 / 0.00 | 0 | 0 | missing |
| BRobot A | 54 | 12 | 0 | -30.00 / 5.50 | 7 | 53 | 15.05 |
| Skeleton A | 59 | 3 | 0 | -0.50 / 0.00 | 0 | 58 | 33.75 |
| Sorcerer A | 59 | 8 | 0 | -10.50 / 5.00 | 29 | 59 | 26.38 |
| BSpider A | 58 | 25 | 0 | -0.50 / 0.00 | 0 | 0 | missing |
| BThief A | 59 | 1 | 0 | -6.50 / 11.50 | 22 | 59 | 15.63 |
| Werewolf A | 63 | 1 | 0 | -1.50 / 0.00 | 0 | 8 | 7.35 |
| zDemonQueen | 24 | 10 | 0 | -14.50 / 8.50 | 11 | 24 | 15.19 |

Detailed frame flags, manifest hashes, acceptance hash checks and action/view residual ranges: [audit.json](audit.json).

Excluded unfinished redo families: DragonCover A, ElemWater A, BGargoyle A, BHarpy A, BHydra A, LizardArch A, BMinotaur A, SeaSerpent A, BTitan A, zReactor, Cactus A.
