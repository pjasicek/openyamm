# MM8 Unicorn (mm8_m544): anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md), part 3. Production:
[mm8_m544_claude](../mm8_m544_claude/README.md). Before: `work/before_anim/mm8_m544.glb` and `actors_mm8.yml`.

## Hit read as Standing

**Audit:** Hit and Standing were near-duplicates (0.016 H RMS): the procedural hit (`animate_unicorn.py` `action('Hit')`:
head -12°, yaw -9°, 1.5 cm travel) moved 3 % of the body (p90 0.033 H). **Fix:**
`../audit_mm678_20261111/fixes/anim_tools/scale_keys.py work/before_anim/mm8_m544.glb export/mm8_m544.glb --clip Hit
--joints 'Neck1,Neck2,Head,Tail*' --factor 4 --ref Hit`: the same wince four times larger on the neck, head and tail
(head tosses about 48° up and 36° aside, then dips); body and legs untouched, so the hooves stay planted (hoof height
range 0 over the clip). Amplifying every joint (x2.5–3) bent the stance legs (arm 25 %, leg 19 % bad): rejected.

| Hit | Before | After |
|---|---|---|
| amp p90 (H) / peak speed (H/s) / moving share | 0.033 / 0.43 / 0.5 % | 0.089 / 1.42 / 21 % |
| bad: head / spine / arm / leg | 0.3 / 1.9 / 3.5 / 2.8 | 6.1 / 3.1 / 3.5 / 2.8 |

Checks (`review/finish.txt`): winding 0; only Hit samplers changed; floor and gait audits clean; every-binding
regression PASS; viewer check clean. Sheet `review/hit_viewer_before_after.png` (top installed; 0.15 s the toss).

## Attack and Cast are one clip: kept

The native `attack2` (cast/shoot) frames are byte-identical to the `attack` frames (`../mm8_m544_claude/native/
attack_side.png` vs `attack2_side.png`), so the Unicorn has no separate cast in the original; Cast stays the Attack.
