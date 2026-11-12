# Wyrm (DragonLand) mm6_wyrm: re-animated attack (attacks-2, 2026-11-11)

Audit fix stream ANIM.md part 4 (`audit_mm678_20261111/fixes/`). Identity `mm6:wyrm`, installed GLB
`assets_source/worlds/mm6/models/mm6_wyrm.glb`. Only the `Attack` clip changed; the 0.626 s impact (melee and the
ranged jaw glow), the remains attachment and every other binding are unchanged. Backup: `work/before_attacks/`.

## 2026-11-11: authored rear-and-lunge bite on the own rig

The MM9 Dragon is excluded by the user and MM9 BASILISK is six-legged with a frilled body, so the attack is authored
on the own 31-joint quadruped rig with `attacks2_tools/author_clip.py` and `recipes/attack_v7.py`, layered over the
installed clip (its jaw and head keys kept). Native `drr1at a`-`e` (`review/native_attack.png`, front view only): the
head rears high, the jaws open, then the bite/breath flash and settle. Wind-up 0-0.45 s: the body sits back 2 cm,
the neck coils up and back over the shoulders, the tail lifts and fans to one side. Strike 0.45-0.62 s: the body
lunges 6 cm and the chest drops, the neck shoots forward and down, the tail whips across; contact 0.626 s (kept);
recover by 1.0 s (length kept). The paws step with the lunge through two-bone IK (hind 4 cm, front 5.8 cm, lifted
1-2 cm on the way): with all four paws planted the legs folded (arm 13 %, leg 5.8 % beyond Standing, v1-v4).

| Measure (score.py definition) | Before | After |
|---|---|---|
| Motion ratio vs MM9 "other" median | 0.27 | **0.78** |
| p90 reach (H) / moving share / peak speed (H/s) | 0.103 / 0.225 / 1.51 | 0.233 / 0.845 / 4.33 |
| Bad share beyond Standing: arm / leg / head (%) | 5.4 / 0.5 / 0.6 | 8.4 / 1.5 / 0.7 |
| Lowest point over the clip | -0.6 mm | -1.6 mm (1.5 game units at scale 972; floor audit ok) |

The arm region (front legs) is 3 points worse than before: a band at the front elbows while the chest rises and at
the strike (`review/v7_all.png`, red). Under the brief's 12 % limit, but it is the place to look first.

Checks (`review/finish.txt`): winding 0; glb_diff only Attack channels; floor 3 bindings ok; gait 0 flagged;
regression every-binding 647 descriptors 0 failed and `mm6_wyrm_actor_model_tiers_and_clips` passed; viewer no
console errors (remains attachment loaded). Sheets: `review/attack_native_before_after.png`, `review/v7_all.png`,
`review/shots_v7.png` (the viewer's body focus crops the head at the strike).
