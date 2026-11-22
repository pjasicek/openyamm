## DD-14 Castle Blackfang

D4 · M (large) · party 39 → 42 · 36–58, Count Blackfang 70 · 70 · treasure 4 (hoard 5) · Story M27

![DD-14](act4_graphs/dd14.svg)

The source's three castle levels and dungeon (dark maze0045–0048) as one BLV of four floors, 640 apart. In the source
the griffin sets the party down on level 1 and the Count waits at the top. A3's M27 makes it a descent:

- **L1, the walls (z 1280):** the griffin lands here, on the wall walk.
- **L2, the upper floor (z 640).**
- **L3, the ground floor (z 0):** the castle's ground floor on the crag top, with the Count's hall and an open-sky
  courtyard.
- **The dungeon (z −640):** cut into the crag, opened by the Count's death.

Four ranges stand round the open courtyard, with a tower at each corner. The keep is the north range. In all there are
33 review rooms, about 42 sectors and about 42 M units². The outer face is 3,584 × 3,072, inside the 4,096 × 3,328
castle on D4's crag.

- **Monsters (70):**
  - Vampires 40 (39) and Vampire Lords 50 (10), the rows DD-03's Act IV floor uses.
  - Count Blackfang 70 (11294) with three Royal Vampires 58, a row A2 adds (11295 proposed, the source's D79).
  - Gargoyle Sentinels 38 (10) and Overlords 45 (2) on the open walks and the courtyard. These are D4's Magic
    Mountain family. The walls belong to the gargoyles; the vampires keep indoors.
  - Five Octopods 50 in the black cistern, as in the source's dungeon.
  - Five of the 70 sleep in coffins: they are placed hidden and rise when their coffin is opened (D-18; counted at
    load).
  - By floor: L1 17, L2 20, L3 19, the dungeon 14. The landing is quiet (D-11.3).
  - The Queen (5001) is a talking actor in her cell and is not counted.
- **Path:**
  - The griffin's landing on the south wall, with coffins in rows, lids ajar, and the adventurer's bones and notes.
  - The south-west tower and its stair down to L2.
  - L2: the sleeping hall's six coffins (three sleepers), the Countess's rooms, and the keep's upper hall.
  - The grand stair down to L3's stair hall, then the Count's hall: the Count and his three Royal Vampires.
  - His death (`m27.blackfang`) lifts the black iron bar on the dungeon stair.
  - The dungeon: the gaolers' stair, the pillared undercroft (the source's twelve pillars), the cells, and the
    Queen's cell at the far end.
- **Off the path:**
  - The gong in the north-west tower opens a panel on L2 into the Count's study (T4, his ledger).
  - The bat roost at the keep's top (T4).
  - The family crypt behind the Count's hall. Its four named coffins are Dutchess, Countess, Count and Lady
    Blackfang; two sleepers rise, and the Count's own coffin holds the hoard (T5).
  - The question room (T4).
  - The black cistern, with the octopods and a chest on its far ledge (T4).
  - The trapped east walk: every second flagstone is a fire plate.
  - Finds: the long gallery's portraits (none has a reflection), the black chapel, the library's lineage, the kitchen,
    and the cask cellar (a store).
- **Loops (7):**
  - the wall walk;
  - L2's ring;
  - down one corner tower and up the other;
  - the keep door and the great hall into the Count's hall;
  - the grand stair and the back stair;
  - in the dungeon, through the question room or the undercroft;
  - once the trapdoor is unbolted from below, the ladder shaft up to the cask cellar, which closes the dungeon onto
    the ground floor.
- **The way back up:** cells, ladder, cellar, kitchen, then the courtyard. The courtyard stair's gate is unbarred from
  below and leads to the landing: a short return once the castle is cleared.
- **States:** all two-state.
  - `m25.done`: the flight in.
  - The gong: the study's panel.
  - The Count's death: the stair's bar (`blackfang_slain`, kept on reload).
  - The courtyard gate's bar, lifted from below.
  - The trapdoor's bolt, drawn from below.
  - One map variable per coffin.
  - The Queen's `queen_found`, `crown` and `done`. On `done` the map hides her.
- **Exits:**
  - **`entrance:griffin_walls`** at (0, −1152, 1280), facing north (512) over the courtyard, on the south wall walk's
    middle stretch. It is the arrival from D6's `m25.flight`, and under open question 1 also from D4's gate. On the way
    out (question 1 (a)), Ambrose by his griffin asks "Are you ready to leave this awful place, friends?" and sets the
    party down beside D4's gatehouse.
  - **The Queen's cell after `done`:** `m27.ambrose_return` moves everyone to D1's `kalindra_gate` (one way).
  - **The bat roost's roof trapdoor:** bolted in Act IV, for the D7 lane (open question 7).
- **Hooks (all placed):**
  - `m25.flight`: D6's event; this map holds its arrival.
  - `m27.landing`: the first arrival.
  - `m27.blackfang`: the Count's hall.
  - `m27.dungeon_stair`: the bar.
  - `m27.queen_cell` and `m27.ambrose_return`: the Queen's cell.
  - `m25.blackfang_gate` and `m25.bat_storm` are D4's.
- **Textures:**
  - The halls are MM7 Castle Navan 7d32, A6's `castles` assignment.
  - The crypt, the coffin niches, the dungeon and the cistern are MM7 Zokarr's Tomb 7d13.
  - The walks and tower tops use D4's towers kit (hkm3, hkm2, the skull frieze, xtslate), so they match the outside.
  - Every double door is DD-03's arched oak pair `chb1dl`/`chb1dr`: the chapel, the great hall, the keep door and the
    Count's hall, each as two leaves. Single iron doors in the dungeon are `t5d1`.
  - About 33 of 45 textures, 1 new: `xbfcrest`, Blackfang's arms, placed once over the throne and once in the great
    hall.
- **Dressing and lights:**
  - Coffins stand against the parapet, leaving 384 clear on the walk. Barrels stand in pairs in the kitchen; the cask
    cellar is a store.
  - The great hall's table stands beside the line between its doors, not on it.
  - Chandeliers hang on chains in the keep's upper hall, the great hall and the Count's hall.
  - Candelabra stand on the floor by the throne and the chapel altar, clear of the aisle. Braziers stand on the floor
    in the crypt.
  - Torches are in brackets on tower walls along the open walks, never on a parapet in mid-air.
  - The Queen's cell has no light inside it; a torch hangs outside its door.
- **Lines:**
  - aaze0045: Ambrose's "awful place", the two adventurers' notes (coffins, floor traps, "The Count's magic keeps us
    from descending"), the gong.
  - aaze0046 and aaze0047: the coffins, the wind at the stair, Zarkon's diary at the ladder's foot (Kloikus and the
    hands through the wall), the rat-eaten diary, the four crypt names.
  - aaze0048: the Queen (A3's topic adapts it).
  - aaze0021:3 and :9: D4's gate before and after M25.

**Kill XP against MAPS §0.**

- The calculation: 10 × 1,824 + 2 × 2,475 + 39 × 2,000 + 10 × 3,000 + 3 × 3,944 + 5 × 3,000 + 5,600 = 163,622.
- That is **40.91k per member** against MAPS's 39.2k: **+4.4 %**.
- The Count is counted in Act IV, because M27 asks for the kill (D-1.2).
- Without the Royal Vampire row (question 2 (b)), the total is 40.20k (+2.6 %).

**Outdoor door check (D4 L1, `briefs/d4/L1/`).**

- **Gate:** the castle has **no door on D4**. The squat gatehouse at the crag's west foot (78, 53), at
  `entrance:blackfang_gate` (79, 54), is a double gate that never opens (`m25.blackfang_gate`, "There seems to be no
  way in."). It has no inside in DD-14; no postern stair is drawn. D4's `scripted:blackfang` (`listed_only`) matches
  that.
- **Arrival from D6:** A6's `m25.flight` event moves the party to `xeen_dd14.blv` at (0, −1152, 1280), facing 512. That
  point may shift by up to a few hundred units at L1, inside the landing's clear middle.
- **If question 1 (a) is taken, D4 needs two things:**
  - A set-down point `entrance:dd14_griffin` on the north-shore track beside the gatehouse. Proposed: cell (76, 54),
    facing west (1024), down the track to Lakeside.
  - A second state on the gate's click after `m25.done`: "Would you like my griffin to fly you inside?" (aaze0021:9),
    which moves the party to `entrance:griffin_walls`.
- **The outside's south wall:** it is the one seen from the jetty, so it should read as a crenellated walk. The landing
  is its middle stretch.

**Open questions** (options and recommendations in the graph file):

1. The way out between the Queen and the crown. Proposed: Ambrose waits on the landing and flies both ways from D4's
   gatehouse, as the source does. The alternatives are a postern stair to the gate opened from inside, or spells only.
2. The band's top: a new Royal Vampire 58 for the Count's guards (proposed), or Vampire Lords 50.
3. A second family: D4's gargoyles on the walls (proposed), or vampires only.
4. The cistern's octopods: stationary in deep water (proposed), indoor swimmers if A1's water facts cover BLVs, or
   Vampire Lords instead.
5. Sleepers after the Count's death: they still rise when their coffin is opened; the slamming lids are flavour
   (proposed).
6. The dungeon stair's refusal: the source's "A force like wind pushes you back … You are unable to descend."
   (proposed), or A3's text reworded. A3's text has the Count "above", but he is on the same floor.
7. The keep's roof: a bolted trapdoor drawn now for D7 (proposed), or none.

**Requests:**

- **A2:** the Royal Vampire row (vampires 11295, 58, look C, Curse). Add DD-14's 70 to the Act IV count.
- **A3:** for question 1 (a):
  - m25.flight's text: Ambrose waits on the walls.
  - A hook for D4's flight in.
  - An Ambrose topic or event on the landing.
  
  Also:
  - Question 6's fail text.
  - Call `m27.ambrose_return` from the crown topic's `do`, as m25.flight is called from Ambrose's topic.
  - The study's ledger line: "Received from Lord Xeen's man: one queen, crowned. Crown kept by her people. No
    matter."
- **A4:** Ambrose (5512) shown on the landing after `m25.done`, if 1 (a) uses an actor.
- **A6:** for question 1 (a), D4's set-down point and the gate's second state. Give the D6 event its target. Register
  `xbfcrest`.
