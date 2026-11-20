# MM7 Warlock (m426): attack from an MM9 donor (attacks stream, 2026-11-11)

Part 4 of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md): the Warlock's attack slot played its
Cast (a planted wand raise, motion ratio 0.27 against the MM9 median). It now plays a new `Attack` clip retargeted
from **MM9 EVILSORCERER `AttackRanged`**. Cast is unchanged and stays the spell clip. Pilot of the donor route for the
`attacks-1` agent; tools in [`../audit_mm678_20261111/fixes/attack_tools/`](../audit_mm678_20261111/fixes/attack_tools/).

## Intent

The native attack (`7m427a`, 7 frames x 125 ms, contact frame 5) coils low, swings the wand overhead in a big arc,
rises onto the toes and flings the spell forward. The donor raises both arms overhead (wand high, as native `ae`),
then drives the whole body forward into a two-handed throw toward the target, and recovers. Native strip:
`review/native_attack.png`.

## Route (`job_attack.json`, `attack_tools/donor_attack.py`, no Blender)

- World-rotation change copy from the donor's clip start onto our Standing frame 0 (every `B_*` trunk, arm and leg
  bone; facing from hips and toes, turn 3°), pelvis travel x 0.925 (leg-length ratio), ankles by two-bone IK to the
  donor's ankle travel. Fingers, wand and sockets keep their Standing locals.
- Timing: 1.33 s (donor 1.7 s); donor release 0.833 s mapped to 0.65 s.
- `gains.lift 0.5`: the donor's crouch dropped the pelvis 25 cm and piled the floor-length gown on the floor.
- Wrist swing soft-limited at 58° (the donor's palm push bent the wrists 83/96°).
- Upper arms swung 14° outward/forward over 0–0.3 s: the donor's crossed-arm gather put the left hand 1.7 cm into
  the chest for one frame.
- Twist bones re-derived (0.6 of the hand roll, -0.5 of the upper arm's roll), checked against the baked Cast (0.4°).
- Gown: the h11 numpy robe sim (`gait_rollout_20261031/h11/scripts/cloth_sim.py`, `work/m426_chains.json`) on the
  clip padded with 0.7 s of Standing, hung toward the **Standing** robe shape, capsules sized on that shape, no bend
  limit, chain floor 0.8 cm (the sim's own rest, 6 cm floor and 9 cm leg capsules held the hem up to 56 cm away from
  Standing; `floor_out` left a chain caught after the crouch), then `hem_floor` 3 mm (hem dipped 4.3 cm at the crouch).
- Release measured, not guessed: `Socket_Staff_Head` reaches 95 % of its back-to-front travel at **0.533 s**
  (native contact 0.625 s: the wind-up plays 15 % slower, inside the ±20 % rule).

## Results (installed 2026-11-11)

| | Before (Cast in the attack slot) | After (Attack) |
|---|---|---|
| Motion ratio (score.py) | 0.27 | **0.86** |
| p90 reach / moving share / peak speed | 0.098 / 0.325 / 1.09 | 0.307 / 0.986 / 3.74 |
| Deformation beyond Standing (worst region) | cloth 7.5 | spine 11.5, cloth 13.2, arm 8.8 |
| Wrist swing / twist (L, R) | 83°/148° (twist flip in Cast) | 58°/35°, 58°/10° |
| Hand or forearm in body | 0 | 0 (arm_hand_gate, 48 fps) |
| Floor (lowest point) | -0.5 cm | -0.5 cm (= Standing) |

Bindings (Warlock A/B/C): `clips.attack_melee`/`attack_ranged` Cast -> Attack, `events.attack_melee.impact` and
`attack_ranged.impact` 0.844 -> 0.533 (glow and release sockets unchanged). Checks (`review/finish.txt`): winding 0,
glb_diff only the added clip, floor audit 0 problems, every-binding regression PASS (647 descriptors), viewer check
no console errors. Viewer shots: `review/attack_viewer_sheet.png`, viewer `review/viewer/` (before = the old Cast in
the attack slot). Rollback: `work/before_attacks/mm7_m426.glb` and `work/before_attacks/actors_entries.yml`.
Credits: 0.

## Neck ring removed (2026-11-12)

User: "warlock - remove this ring from her geometry". The loose gold loop in front of the throat, just under the chin
(the Smart Topology "neck ring" piece, y 1.337-1.375 m, z 0.088-0.116 m), read as a stray choker. `scripts/remove_chin_ring.py`
drops every welded component lying wholly in that box and rewrites the index accessors in place (vertices kept,
unreferenced): LOD0 133, LOD1 43, LOD2 12 triangles, the same in each shadow mesh; LOD3 has no ring piece (0).
Chest necklace, earrings, clips, materials and bindings unchanged. Flat render `work/before_ring/flat_compare.png`,
viewer `work/before_ring/before_viewer.png` / `after_viewer.png`. Checks: winding 0, every-binding regression PASS
(647 descriptors). Rollback: `python3 tools/install_model.py
level_generation/creatures/mm7_m426_attacks_claude/work/before_ring/mm7_m426.glb --world mm7`.
