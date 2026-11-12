# Water Elemental m500 (and MM7 m210): re-animated attack (attacks-2, 2026-11-11)

Audit fix stream ANIM.md part 4 (`audit_mm678_20261111/fixes/`). Identities `mm8:m500` and `mm7:m210` (shared
layout: the MM7 GLB is built from the MM8 one by `mm7_m210_claude/scripts/build_glb.py`, binary chunk identical, own
MM7 palettes). Only the `Attack` clip changed; `Cast`, the 0.875 s impact and the palm glows are unchanged.
Backups: `work/before_attacks/` here and in `../mm7_m210_attack_claude/work/before_attacks/` (also the old
`mm7_m210_claude/export/` file, which was identical to the installed MM7 GLB).

## 2026-11-11: authored surge and strike on the own rig

No donor: an effect body (water column with a fish tail, the brief's "author a bigger surge and strike"). The native
frames (`m500aa`-`ah`, `review/native_attack.png`) show the arms flaring wide, the body drawing back and both palms
thrust forward into the burst. Layered over the installed clip (its palms-forward push kept) with
`attacks2_tools/author_clip.py` and `recipes/attack_v4.py`: wind-up 0-0.62 s (column leans back 22°, arms flare up
and out, head back, the tail coils and the caudal fin rises), surge 0.66-0.875 s (column whips forward 28°, lunges
0.3 m and lifts 3.5 cm so the belly clears the floor, palms driven forward), contact 0.875 s (palms 1.10 m in front,
kept), hold, recover by 1.375 s (length kept: the Water Elemental regression pins it).

| Measure (score.py definition) | Before | After |
|---|---|---|
| Motion ratio vs MM9 "other" median | 0.19 | **0.81** |
| p90 reach (H) / moving share / peak speed (H/s) | 0.073 / 0.162 / 1.10 | 0.279 / 1.000 / 3.35 |
| Bad share beyond Standing: hand / arm / head (%) | 6.7 / 6.2 / 0.4 | 6.7 / 6.0 / 0.9 |
| Lowest point over the clip | 0 | 0 |

Iterations: v1 0.85 (arm 11.4 % beyond Standing from an added forward arm swing; belly 3.4 cm under the floor),
v2 (floor fixed by the lift and a gentler lower spine), v3 (no added arm swing, smaller flare), v4 (gentler head
counter-pitch: head 5.0 -> 0.9 %).

Checks (`review/finish.txt` here and in `mm7_m210_attack_claude/review/finish.txt`): winding 0; glb_diff only the
Attack channels (MM8 install and the rebuilt MM7 copy); floor 3 + 3 bindings ok; gait 0 flagged; regression
every-binding 647 descriptors 0 failed, `mm8_water_elemental_actor_models_keep_tiers_and_palm_cast` and
`mm6_water_elemental_actor_tiers_trident_and_native_scale` passed; viewer no console errors (both). Sheets:
`review/attack_native_before_after.png`, `review/shots_v4.png`.
