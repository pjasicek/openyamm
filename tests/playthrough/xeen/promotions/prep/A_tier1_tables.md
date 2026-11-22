# Prep: block A, the tier-1 promoters the main chain already finished (segments 01, 03, 05)

No quest is replayed: each segment starts from a copy of the main checkpoint right after the hand-in (README, Blocks).

| Promoter | Start | Talk (how the main chain opens it) | Promote topic (quest file) | Shown when |
| --- | --- | --- | --- | --- |
| Old Valia 4044 (X1, cottage 4040) | main 09 (X1 at her door) | placed (7552, -4332, 625, yaw 1.5708), the door clicked (09) | Crusaders (t1-a.yml) | m4.done, promotable crusade |
| Barok 4151 (X2, hut 4095) | main 17 (X2) | X2 event 1 (17) | Promotion (t1-b.yml) | q-c2.done 110204, promotable pendant |
| Danulf 4154 (X2, ring of stones) | main 17 | placed (-3277, -8909, 1044, yaw -2.16), actor 51 (17) | Patriarch (q-c17.yml) | q-c17.done, promotable elf |
| Princess Roxanne 4404 (XD-07 east tower, house 4204) | main 21 (X4 outside the gate) | the castle walked as 21 (gate, portcullis event 40, the hall north to (0, 5376), the tower door event 19 / door 5, the stair), event 42 | Rogues (t1-e.yml) | q-c3.done 112061, promotable tiara |

Route note (05): from the hall at (0, 3300) the planner now leads east along y 3300 into a wall; the walk goes north
to (0, 5376) first (`plan: false`), then east to the tower door.

The topics are offered only while a member is eligible (`show: promotable`), so "nobody left" is the label's absence.
