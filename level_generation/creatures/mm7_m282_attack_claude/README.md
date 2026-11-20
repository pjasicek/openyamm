# Medusa m282: re-animated attack (attacks-2, 2026-11-11)

Audit fix stream ANIM.md part 4 (`audit_mm678_20261111/fixes/`). Identity `mm7:m282`, installed GLB
`assets_source/worlds/mm7/models/mm7_m282.glb`. Only the `Attack` clip changed; the 1.0 s release (melee and ranged),
the bow and arrow attachments and every other binding are unchanged. Backup: `work/before_attacks/`.

## 2026-11-11: body layered onto the archery draw (own rig, authored)

The brief suggested an MM9 caster's upper body; the native action (`m282aa`-`ah`, `review/native_attack.png`) is an
archery shot (the monster's missile is Arrow; Cast reuses Attack), which the installed clip already draws with the
arms, bow string and arrow. A caster's arms would change the action, so the arms are kept and the body is layered on
with `attacks2_tools/author_clip.py` and `recipes/attack_v3.py`: she leans back as she reaches overhead for the arrow
(0-0.35 s), leans 15° and glides 16 cm forward into the draw (to 0.92 s), recoils at the loose (1.0 s) with the head
snapping back, and recovers by 1.5 s (length kept). The 3 m tail sweeps with the draw and a delayed wave, its rattle
end stays raised (as in every native frame) and shakes after the shot (a decaying 12 Hz rattle, 0.94-1.34 s; it adds
nothing to the ratio). The `Arrow` bone is keyed under the armature root, so the recipe's `FOLLOW: Arrow -> Spine2`
keeps it where the installed clip had it on the chest (arrow-to-right-hand offset changes by at most 1.9 mm). The
follower handles the arrow's zero-scale parked frames.

| Measure (score.py definition) | Before | After |
|---|---|---|
| Motion ratio vs MM9 "other" median | 0.28 | **0.78** |
| p90 reach (H) / moving share / peak speed (H/s) | 0.118 / 0.306 / 1.03 | 0.235 / 0.956 / 3.73 |
| Bad share beyond Standing: hand / arm / tail (%) | 5.6 / 1.0 / -0.4 | 5.6 / 1.0 / 0.4 |
| Lowest point over the clip | 0 | 0 |

Iterations: v1 0.61 (10 cm glide, the long tail's middle did not reach 0.05 H = 15 cm), v2 0.71 (wider tail
sweep), v3 0.78 (16 cm glide). Archery is a restrained action by nature; the gate is met with the glide and tail.

Checks (`review/finish.txt`): winding 0; glb_diff only Attack channels; floor ok; gait 0 flagged; regression
every-binding 0 failed and `mm6_medusa_actor_model_tiers_follow_sprite_scales` passed; viewer no console errors (bow
and arrow attachments loaded). Sheets: `review/attack_native_before_after.png`, `review/shots_v3.png` (viewer with
bow and arrow: reach, draw, loose, recoil).
