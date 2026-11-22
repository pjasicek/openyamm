## DD-05 Western Tower of Mok

D1 · M · party 35 → 39 · 25–45, the Cult Leader 45 · 45 · treasure 4 (hoard 5) · Q-D6, Hero / Priest of Light; Q-D20's
Pegasus

![DD-05](act4_graphs/dd05.svg)

The source's four-level round tower (dark maze0057–0060) as one BLV of four floors, 640 apart (L1 0, L2 640, L3 1280,
L4 1920; the chapel rises into the cone). The party enters at the **top** by the heretics' rope (D-9.3) and fights down
to the front door. As in the source, each pair of floors has two stairs in different places, so every floor is
crossed and every pair of floors closes a loop. 29 review rooms, about 33 sectors; four floors of about 2,900 across,
about 32 M units².

- **Monsters:** Mok Heretic 25 (22), Heretic Priest 35 (11), Heretic Lord 45 (3), the Cult Leader 45 (a boss row A2
  adds, 11223 proposed). Mok's own guardians, set by the heretics on the warded door and the fountains: Stone Golem 26
  (5), Iron Golem 40 (3). The source's order is kept: strongest at the top (L4 10, L3 12, L2 10, L1 13), with the hoist
  room quiet. Humble and Pious stand on a peaceful row (11224 proposed) and are not counted.
- **Path:** D1's rope; the hoist room (the window, the windlass, the heretics' bread: a storeroom); the bone gallery;
  the double doors into the heretics' altar (the Cult Leader, the key); the altar stair to L3's cloister, the fountains
  of cold and venom (+5 Water, +5 Body), the upper dormitory (T4); the west stair to L2's refectory, the fountains of
  fire and lightning (+5 Fire, +5 Air, two stone guardians), the lower dormitory; the east stair to L1's stair hall,
  the hall of alcoves (2 Energy Disks, the Pegasus), the novices' dormitory, the hall of the warded door (a Heretic
  Lord and three iron guardians), and the front door opened from inside with the key.
- **Off the path:** Pious's cell (L3) and Humble's cell (L2), each behind a door; the heretics' cells and the tapestry
  walk (a button opens a panel into the vestry, where the hoard chest T5 stands); the kitchen (T4); the guardians'
  gallery (T4); the mirror hall (the dead mirror). There are finds in the beds and in the three bone heaps.
- **Loops (5):** round the top floor through the vestry; the two stairs of each pair of floors (L4–L3, L3–L2, L2–L1);
  on the ground floor, the dormitory and the mirror hall each lead from the alcoves to the door.
- **States:** the rope (`rope_climbed`, D1's event); the tapestry button (two-state panel); the Cult Leader's death;
  the key on the altar, which opens the front door from inside (`q-d6.front_door`) or from outside on D1; each cleric's
  "Slay him anyway?" (no: spared and gone; yes: the source's kill line; the bed's line by a map variable).
- **Exits (the `exit` preset, D-24):**
  - The rope window in the hoist room, both ways. The inside arrival is `entrance:d1_rope`, a step inside the window
    facing south. The way out returns to D1's (-16896, 16896, 1600).
  - The front door in the door hall, both ways once `tower_opened`. The inside arrival is `entrance:d1_door`, facing
    north. The way out returns to D1's (-16896, 14848, 1600).
  - The source's "Exit the Great Western Tower?" is the preset's meaning.
- **Hooks (all placed):**
  - `q-d6.tower_rope`: D1's event; this map holds its arrival.
  - `q-d6.cult_leader` and `q-d6.tower_key`: the chapel.
  - `q-d6.pious` and `q-d6.humble`: the cells.
  - `q-d6.l1_alcoves` and `q-d20.pegasus`: the hall of alcoves.
  - `q-d6.front_door`: the door hall. `q-d6.front_door_outside` is D1's.
- **Textures:** the Towers of Mok family, MM8 Castle of Air d27, as DD-06. DD-05's accent is the heretics' chapel and
  vestry in MM8 Temple of the Sun d22 (pale marble, a gold-blue mosaic), as A6's `dungeon_families` assigns it. About
  24 of 45 textures, 1 new: `xmoktap`, Mok's sun tapestry daubed with the heretics' sign, placed once per face.
- **Keeping it apart from DD-07, its twin:** DD-05 has clerics, the pale chapel under the cone, the top entry with the
  hoist room, fountains on two floors and the Pegasus. DD-07 (A7) keeps its floating mages, the Jewel of Ages and the
  Griffin, and should take another accent than d22.
- **Dressing and lights:**
  - Containers stand by the walls; the hoist room and the kitchen are stores.
  - The refectory table stands beside the line between its doors, not on it.
  - The chapel's chandelier hangs on chains from the cone's ring beam. Braziers stand on the floor either side of the
    altar, clear of the aisle. Elsewhere there are wall sconces and lamps.
  - The chapel's double doors are two leaves. The front door is one leaf (D1's door is a 110-wide `hkm3dr`).
- **Lines:**
  - aaze0057: the exit, the mirror, the statuette, the discs, the beds.
  - aaze0058 and aaze0059: the fountains, Humble's and Pious's pleas, the kill and the bed lines.
  - aaze0060: the tapestry, the button, the bones.
  - Dreyfus's thanks (aaze0060:8) is A3's, in town.

**Kill XP against MAPS §0.** MAPS's row is a group: DD-05, DD-20 and DD-23, with 100 monsters, 24–45, and 30.5k. A
third would be 33 monsters and 10.2k, under the M band's floor of 45 (the source tower holds 30). The graph takes the
M floor:

- 45 monsters: 22 × 875 + 11 × 1,575 + 3 × 2,475 + the Leader 2,475 + 5 × 936 + 3 × 2,000 = 57,155.
- That is **14.29k per member**: +4 % on DD-05's share by count (45 of 100 is 13.7k), +40 % on a third.
- With DD-20 at its M floor (45) and DD-23 at 15–20, the group would come to 105–110 monsters and about 32–34k
  (+5–10 %). A2 recounts Act IV (open question 1).

**Outdoor door check (D1 L4, `briefs/d1/L4/`).** The two ways in match: the rope `door:dd05_rope` (event 121) and the
front door `door:dd05_front` (event 118). Both have return points, and the door is a single leaf facing south.

- **Window above the rope.** The rope is 2,240 high. Inside, L4's floor is at 1,920, so the hoist window's sill is
  about 2,000 and its head 2,240. A6 should make sure a window (`hkm3elw`) sits on the north face directly above the
  rope's top; the mid storey's `windows: alternate` may not put one there.
- **Arrow slits.** A3's climbing text passes arrow slits. The windowless 1,280 base could carry a column of slits
  above the rope (optional).
- **Rope return facing.** The return point faces 1536, toward the wall the party just climbed down. 512, away from
  the wall, is an option for A6.
- **Size.** The outside is 1,280 across and about 2,700 to the eaves. Inside is 2.3 times as wide (open question 6).

**Open questions** (options and recommendations in the graph file):
1. Count and XP: 45 monsters and 14.29k (proposed; the group comes to 105–110 and ~32–34k, A2 recounts), or 33 under
   the M band.
2. A second family: Mok's guardians as golems (proposed), or heretics only.
3. The Cult Leader as a new boss row at 45 (proposed), or the source's 55 counted later (D-1.2).
4. Humble and Pious: a peaceful row in cells behind doors, hidden by either answer (proposed), or bed events only.
5. The discs: the first disc alcove calls `q-d6.l1_alcoves` for both disks (proposed), or A3 splits the hook.
6. The inside larger than D1's tower (proposed, as DD-02 and DD-06), A6 widening the tower, or a cellar.

**Requests:**
- **A2:** the boss row "Cult Leader" (heretics 11223, 45, look C, hp_x 3) and a peaceful "Penitent Cleric" (11224, 25,
  its own faction) for Humble and Pious. If the golems stay, the heretics and the golems need no relation between them.
  Recount the DD-05+20+23 group.
- **A6:** the window above the rope (optional: arrow slits). Register `xmoktap` in `textures.yml`.
- **A3:** none needed for (a) of questions 4 and 5. The fountains' and bones' lines are for the ORIGINAL_LINES ledger.
