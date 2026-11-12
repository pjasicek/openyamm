# Juggernaut m608: re-animated attack (attacks-2, 2026-11-11)

Audit fix stream ANIM.md part 4 (`audit_mm678_20261111/fixes/`). Identity `mm8:m608`, installed GLB
`assets_source/worlds/mm8/models/mm8_m608.glb`. Only the `Attack` clip changed; the 1.0 s impact, its palm glow and
every other binding are unchanged. Backup: `work/before_attacks/`.

## 2026-11-11: body and rollers layered onto the palm strike (own rig, authored)

The suggested donors (LoMM GOLEMSTONE HAttack, MM9 GIANT/TRELLBORG smash) are biped smashes; the native frames
(`m608Aa`-`Ah`, `review/native_attack.png`) show a different action: arms flung wide, flexed, brought together and a
burst between the palms. The installed clip already follows that with the arms, so it is kept and the body is
layered on with `attacks2_tools/author_clip.py` and `recipes/attack_v2.py`: the torso rears back 14° and turns
during the raise while the rollers roll it back 4.5 cm; at 0.82-0.97 s it pitches forward 24°, the head nods, and
it lunges 13 cm forward on its rollers into the palm strike; it rolls back by 1.25 s (length kept). Roller spin is
travel / radius (0.179 m), so they roll rather than slide, and the recipe's `FLOOR` lift raises Root wherever a
rough roller's corner would dip below the floor (up to 2.6 cm before the lift).

| Measure | Before | After |
|---|---|---|
| Motion ratio, score.py definition | 0.41 | **0.69** |
| Same ratio over the visible surface only | 0.63 | **0.92** |
| p90 reach (H) / moving share / peak speed (H/s), score.py | 0.207 / 0.193 / 2.32 | 0.326 / 0.504 / 3.26 |
| Bad share beyond Standing: hand / arm / head / spine (%) | 7.9 / 3.4 / 0.0 / 0.3 | 7.9 / 3.4 / 1.7 / 2.8 |
| Lowest point over the clip | 0 | 0 |

Why two ratios: 48 % of the GLB's rest surface is the 63 death fragments (`D_00`-`D_62`, parented to the rig root
and hidden at zero scale in every living clip). They never move, so the audit's moving share cannot exceed about
0.52 on this model whatever the attack does. Over the visible surface the attack passes the 0.75 gate; on the audit's
definition it stays at 0.69 for that reason alone. Moving hidden fragments to lift the number was not done.

Checks (`review/finish.txt`): winding 0; glb_diff only Attack channels; floor ok; gait 0 flagged; regression
every-binding 0 failed and `mm8_juggernaut_actor_models_keep_rollers_tiers_and_roles` passed; viewer no console
errors. Sheets: `review/attack_native_before_after.png`, `review/shots_v2.png` (viewer: rear back with arms up,
hunched palm strike with the glow).
