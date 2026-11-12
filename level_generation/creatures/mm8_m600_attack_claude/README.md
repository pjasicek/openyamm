# Nightmare m600: re-animated attack (attacks-2, 2026-11-11)

Audit fix stream ANIM.md part 4 (`audit_mm678_20261111/fixes/`). Identity `mm8:m600`, installed GLB
`assets_source/worlds/mm8/models/mm8_m600.glb`. Only the `Attack` clip changed; the 0.563 s impact and its jaw/neck
glows are unchanged. Backup: `work/before_attacks/`.

## 2026-11-11: authored rear-and-spew on the own rig

The brief suggested MM9 GOAT adapted to a horse; MM8's Nightmare is not a horse but a mass of eyes and two jaw necks
(`m600AA`-`Ah`, `review/native_attack.png`: the jaws gape and spew a green cloud), so no donor fits and the clip is
authored on the own 58-bone rig with `attacks2_tools/author_clip.py` and `recipes/attack_v3.py`, layered over the
installed clip. **The eye stalks are not touched**: the user approved their subtle twitch on 2026-10-18 after
rejecting larger eye motion (`mm8_m600_claude/README.md`, "Attack revision"). Added: the mass rears back 4° and slides
back 3.5 cm while both jaw necks coil back (0-0.36 s), then the necks whip forward and down (about 18° each over their
joints) and part slightly so the jaws stay apart, the mass heaves 6 cm forward into the spew (contact 0.563 s, kept),
a short decaying shudder while it spews, recover by 1.0 s (length kept). `FLOOR` keeps the slime base on the ground.

| Measure (score.py definition) | Before | After |
|---|---|---|
| Motion ratio vs MM9 "other" median | 0.24 | **0.87** |
| p90 reach (H) / moving share / peak speed (H/s) | 0.123 / 0.262 / 0.52 | 0.300 / 1.000 / 3.97 |
| Bad share beyond Standing: head / other (%) | 0.4 / 0.1 | 0.6 / 0.1 |
| Lowest point over the clip | 0 | 0 |

Iterations: v1 1.27 (necks far too fast), v2 0.88 (jaws touched each other at the strike), v3 0.87 (necks part).
Look first: the user asked for a subtle attack before; this one is bigger in the necks and body, not in the eyes.

Checks (`review/finish.txt`): winding 0; glb_diff only Attack channels; floor ok; gait 0 flagged; regression
every-binding 647 descriptors 0 failed (no Nightmare case in the actors suite); viewer no console errors. Sheets:
`review/attack_native_before_after.png`, `review/shots_v3.png`.
