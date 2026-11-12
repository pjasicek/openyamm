# Salamander m568: re-animated attack (attacks-2, 2026-11-11)

Audit fix stream ANIM.md part 4 (`audit_mm678_20261111/fixes/`). Identity `mm8:m568`, installed GLB
`assets_source/worlds/mm8/models/mm8_m568.glb`. Only the `Attack` clip changed; `Cast`, the bindings and the 1.0 s
impact (melee and ranged) are unchanged. Backup of the claimed GLB and the actors.yml entries: `work/before_attacks/`.

## 2026-11-11: body layered onto the polearm chop (own rig, authored)

No donor (no MM9 or LoMM serpent-bodied humanoid with a polearm). The installed clip already carries the native
action (gather the polearm overhead 0-0.8 s, chop forward and down at 1.0 s, recover) but only the arms moved. The
body is layered on with `attacks2_tools/author_clip.py` and `recipes/attack_v1.py`: during the gather the column leans
back 20° and winds 25° to its right (the native frames turn the torso toward the pole), the tail tip lifts and curls;
at 0.84-1.0 s the column whips forward 35° and unwinds, lunging 0.25 m, the head counter-pitches to stay on target,
the tail lashes; recover by 1.333 s (length kept). The Polearm node is animated under Root, not under a hand, so the
recipe's `FOLLOW: Polearm -> B_Spine2` keeps it where the installed clip had it relative to the chest (the arms are
not changed): grip offset to both hands changes by at most 2.3 mm (resampling). Polearm tip reaches forward-low at
0.97-1.0 s, so the 1.0 s impact stays.

| Measure (score.py definition) | Before | After |
|---|---|---|
| Motion ratio vs MM9 "other" median | 0.36 | **0.89** |
| p90 reach (H) / moving share / peak speed (H/s) | 0.117 / 0.474 / 1.33 | 0.304 / 1.000 / 4.21 |
| Bad share beyond Standing: hand / arm / spine (%) | 0.4 / 6.5 / 2.2 | 0.4 / 6.4 / 2.2 |
| Hand vertices inside the body | 0 % | 0 % |
| Lowest point over the clip | +1.2 mm | +1.2 mm |

The left upper arm's 40 % hotspot at 1.23 s is the installed clip's (unchanged, red in the sheet).

Checks (`review/finish.txt`): winding 0 inverted; glb_diff only the Attack channels; floor 3 bindings ok; gait 0
flagged; regression every-binding 647 descriptors 0 failed and `mm8_salamander_actor_models_keep_native_tiers_and_polearm`
passed; viewer check no console errors (polearm attachment loaded). Sheets: `review/attack_native_before_after.png`,
`review/shots_v1.png` (viewer, with the polearm).
