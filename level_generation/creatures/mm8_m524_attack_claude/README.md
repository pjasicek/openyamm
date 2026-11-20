# Serpentmen m524: re-animated attack (attacks-2, 2026-11-11)

Audit fix stream ANIM.md part 4 (`audit_mm678_20261111/fixes/`). Identity `mm8:m524`, installed GLB
`assets_source/worlds/mm8/models/mm8_m524.glb`. Only the `Attack` clip and the `attack_melee` impact changed.
Backup of the claimed GLB and the actors.yml entries: `work/before_attacks/`.

## 2026-11-11: authored rear-and-strike on the own rig

No donor (no MM9 or LoMM serpent-bodied humanoid). The clip is authored on the model's own 61-bone rig with
`audit_mm678_20261111/fixes/attacks2_tools/author_clip.py` and `recipes/attack_v4.py` (the installed one), layered
over the old Attack (its finger curl kept). Clip length kept at 1.125 s, so the game's attack timing is unchanged.

Following the native frames `m524Aa`-`Ag` (`review/native_attack.png`): wind-up 0-0.36 s (column leans back 30°,
arms spread wide, head back, jaw opens, tail curls and its tip lifts), strike 0.38-0.56 s (column whips forward and
down 67°, lunges 0.3 m along +Z, arms and claws reach forward, jaw wide), contact **0.56 s** (mouth socket 1.10 m in
front, `scripts`: `attacks2_tools/track.py`), hold low, recover to the start pose by 1.125 s. The tail answers with a
lateral wave running to the tip. `actors.yml` `events.attack_melee.impact` 0.75 -> 0.56 (A, B, C).

| Measure (score.py definition) | Before | After |
|---|---|---|
| Motion ratio vs MM9 "other" median | 0.26 | **0.93** |
| p90 reach (H) / moving share / peak speed (H/s) | 0.112 / 0.315 / 0.74 | 0.332 / 1.000 / 4.43 |
| Bad share beyond Standing: arm / head / spine / tail (%) | 0.8 / 0.6 / 0.0 / 0.0 | 2.9 / 3.6 / 1.5 / 0.0 |
| Hand vertices inside the body | 0 % | 0 % |
| Lowest point over the clip | +3.3 mm | +3.3 mm |

Head 3.6 % is the throat skin stretched by the open jaw (kept at 30° after v3's 40° gave 4.9 %). Iterations: v1
ratio 1.23 (tail wave far too large), v2 1.01, v3 0.94, v4 0.93 (gentler jaw, neck and arm spread).

Checks (`review/finish.txt`): winding 0 inverted; glb_diff only the Attack channels; floor 3 bindings ok; gait
Standard and MAW 0 flagged (unchanged clips); regression `mm6_mm7_mm8_actor_models_build_every_binding` 647
descriptors 0 failed and `mm8_serpentman_actor_models_keep_native_tiers_and_simulation` passed; viewer check no
console errors. Sheets: `review/attack_native_before_after.png` (native front and side, before, after with bad
triangles red), `review/shots_v3.png` (viewer shots of the same motion), `review/v3_hands.png`, `review/v3_head.png`.
Viewer: `review/viewer/` (before and after per tier).
