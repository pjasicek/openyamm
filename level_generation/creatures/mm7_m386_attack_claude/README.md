# Robot m386: re-animated attack (attacks-2, 2026-11-11)

Audit fix stream ANIM.md part 4 (`audit_mm678_20261111/fixes/`). Identity `mm7:m386`, installed GLB
`assets_source/worlds/mm7/models/mm7_m386.glb`. Only the `Attack` clip changed; the 0.441 s impact, the muzzle charge
glow and release, and every other binding are unchanged. Backup: `work/before_attacks/`.

## 2026-11-11: whole-body gun shot on the own rig

The brief suggested a whole-body tail strike, but the native attack (`m386aa`-`ag`, `review/native_attack.png`) is a
gun shot and the user's design for v2 says "attack = shot with the gun" (`mm7_m386_v2_claude/README.md`); melee and
ranged both play it. So the action stays a shot and the body joins it, authored with `attacks2_tools/author_clip.py`
and `recipes/attack_v3.py` over the installed clip (gun swing, charge, 3.5 cm barrel slide-back, jaw snap, re-stow
kept): the chassis braces (drops 7 mm, the spikes' retraction limit, leans in 3.5°), the scorpion tail cocks up over
the back and the neck stretches to aim; from the shot at 0.44 s the recoil throws the chassis 7.5 cm back and 8°
nose-up, the head snaps back and the tail whips over and across; it settles with a small wobble by 0.875 s (length
kept). The spike tips stay where the installed clip plants them: the recipe's `POST` re-aims each sleeve at its tip
and slides the spike along it (the walk's own leg mechanism), clamped to the slide range of the installed living
clips (local y -0.127 ... -0.004). Every recoil key starts at 0.44 s, so the muzzle is where the shot leaves it.

| Measure (score.py definition) | Before | After |
|---|---|---|
| Motion ratio vs MM9 "other" median | 0.22 | **0.76** |
| p90 reach (H) / moving share / peak speed (H/s) | 0.077 / 0.231 / 1.15 | 0.185 / 0.953 / 4.18 |
| Bad share beyond Standing (all regions) | <= 0.1 % | <= 0.1 % (rigid parts) |
| Lowest point over the clip | -0.2 mm | -0.2 mm |

Iterations: v1 (spike tip read on the wrong end of the rod: a spike ended 6 cm under the floor; then a 2 cm brace hit
the retraction limit, -8.6 mm), v1 fixed 0.74, v2 0.77 (stronger recoil), v3 0.76 (recoil starts at the shot).

Checks (`review/finish.txt`): winding 0; glb_diff only Attack channels; floor 3 bindings ok; gait 0 flagged;
regression every-binding 647 descriptors 0 failed (no Robot case in the actors suite); viewer no console errors.
Sheets: `review/attack_native_before_after.png`, `review/shots_v3.png` (brace with the gun level, recoil).
