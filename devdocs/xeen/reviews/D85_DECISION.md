# D-85: X2 Danulf's ring — sprites swarm the quest giver (2026-11-21, fourth orchestrator's decider)

Found by A3-promo 6th (promotion segment 03, `output/a3promo_s7/s6_probe03.log`): at Danulf's ring the party is cursed and
stoned within 2–16 s by sprite groups 3,000–5,200 away (X2's Medusa Sprites (Stone) and Killer Sprites (Curse); Dark
Sprites are D2's).

DECISION: Change the map. The ring stays in the hostile sprite woods, but A5 moves the six sprite spawn markers in range
of the ring so every marker is at least 5,888 from Danulf (−3686, −9523): monster missile range 5,120
(`GameplayActorAiSystem.cpp`) plus 768, the distance D-54 used for the lake dragons. Markers move, none are removed; each
keeps its slot (slot 1, Xeen Sprite) and group size, so X2's count and kill XP stay the same. No peaceful zone (the
engine has none), no peaceful court sprites (against Q-C17, new rows, XP), no leash (works only on immobile placed
actors; does not hold a flyer that sees the party), the ring is not moved (built geometry, ids, bake).

WHY: six groups (12–18 sprites) in missile range on load wipe a level 7–11 party on arrival. MM4 put Danulf at C3 (14,5)
near Rivercity and the crazed sprites and wand at D4 (8,14) (`research/MM4_CLOUDS_CONTENT.md`): giver and danger apart.
D-11.1 (Ebenezer's camp 5,000–6,500), D-23 (Graalg's parley fire) and D-54 (5,888) already keep givers clear.

WHO ACTS:
- A5 (X2 `gen.py` woods markers), suggested targets (or nearby dry ground meeting D-14):

  | Marker | Now (x, y) | Distance now | Target (x, y) | Cell | After |
  |---|---|---|---|---|---|
  | 5 | (−6304, −7904) | 3,078 | (−9500, −7800) | [45.4, 79.2] | ≈6,060 |
  | 2 (nest guard) | (−6560, −10976) | 3,220 | (−9400, −11200) | [45.6, 85.9] | ≈5,950 |
  | 19 | (−2176, −12832) | 3,637 | (−1800, −15200) | [60.5, 93.7] | ≈5,980 |
  | 3 (nest guard) | (−7392, −10624) | 3,866 | (−9000, −12600) | [46.4, 88.6] | ≈6,140 |
  | 7 | (1024, −8672) | 4,786 | (2400, −9000) | [68.7, 81.6] | ≈6,110 |
  | 6 | (1440, −8832) | 5,172 | (2300, −7800) | [68.5, 79.2] | ≈6,230 |

  Checks: no hostile marker or placed hostile within 5,888 of Danulf; the nest [49, 87] keeps three guard markers within
  ~1,800; the road from the woods fork [63, 73] to the ring passes at most one group (D-23); same marker count and slots.
  Rebuild with bake. New `playtest_danulf_ring.yml`: fresh load, pose at the ring, no clear; first 5 s no member gains
  a condition; interact with actor 51, dialogue opens; 2/2 plus X2's walk and hostility tests. One line in L4 NOTES.
- A5 and A6: measure every outdoor talking quest giver on their maps against the same rule (`measure.py`); fix any
  marker inside 5,120 with a small move, no decider; report 5,120–5,888 as warnings; a giver meant to stand in a fight
  needs a decider row.
- A2: no recount; rerun `balance.py` on the rebuilt X2 and confirm Act II stays 1.08.
- A3-promo: rerun 03 both modes; lower its ring clear from 9,000 to 3,000 only if 3/3 each way.
- A3 / A3-side: rerun main 17 and `q-c17_faery_wand.yml` (keep their 3,000 clears) and the nest step.
- G: no change; after the rebuild check the inline map still shows Danulf and the nest.

REVERSIBLE: yes — six marker coordinates in `gen.py` and a rebuild.
