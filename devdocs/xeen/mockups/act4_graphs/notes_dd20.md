## DD-20 Lakeside Coven and Sewer

D4 · M · party 35 → 39 · 25–45, the Head Witch 45 · 45 · treasure 4 (hoard 5) · Q-D22, Warlock; Q-D20's Dragon

![DD-20](act4_graphs/dd20.svg)

The source's Lakeside town (dark maze0033: the coven, the five prisoners, the cauldrons) and Lakeside Sewer (maze0034:
the stalkers, the statuette, two dead men's journals) as one BLV under D4's Lakeside. The map has three levels:

- the coven under the Guild (z 0, about 640 under the square);
- its cells half a storey lower (−256), so the Head Witch is "above them" as Naomi says;
- the sewer (−512), running east under the square to the shaft by the jetty and the lake's outfall.

There are three ways in, and each half leads to the other, so the riddle bars nothing. The map has 22 review rooms,
about 28 sectors, about 34 M units² (coven 12, cells 3, sewer 19), 12 doors and four cage fronts.

- **Monsters:**
  - The coven: Witch 32 (13) and Coven Witch 40 (4), the source's 18 witches of Lakeside. They are peaceful to
    members (`joined`) until the Head Witch dies (A2's relations).
  - The Head Witch 45: a coven boss row A2 adds, 11173 proposed. The source's Coven Leader is level 60, over the
    band. Her group is three.
  - Sewer stalkers: Sewer Stalker 25 (24) and Stalker Matriarch 35 (3). Five of the drain cross's eight are a hidden
    group that climbs out of the side drains on the first step (the journal's "they seem to come out of nowhere";
    D-18's method).
  - The Coven Mother 50 is over the band and stays on D4.
  - The four caged prisoners are peaceful named rows (11906–11909 proposed) and are not counted.
- **Rests:** sewer stalkers at Dif 5 (10 % Wererat 18, 50 % Stalker 25, 40 % Matriarch 35); the Wererat share is a
  named exception, D-46.
- **Path (right answer):**
  - The Guild's back stair down into the coven hall. The initiation cauldron stands two steps from the stair's foot,
    so a party can drink and join before a witch reaches it.
  - The double doors (two leaves, the Moon seal) to the witches' walk, the antechamber's wardens, and the Head
    Witch's room in the north-west corner: her death, her chest with the Necropolis pass, her mirror.
  - Back past the brewery to the hall, the gaoler's room, down to the cells, and the four cages: Camilla, Aretha,
    Isabella asleep, and Rhett at the drain door.
  - The drain stair to the slop pit, the drain cross (the ambush), the stalker warren, and the lake outfall.
  - The ledge to the Dragon's niche, with the dead man's bones two steps short of it.
  - Up the jetty shaft to D4.
- **Path (wrong answer):** the trapdoor drops the party into the sump under the square. From there: the main drain,
  the cross, the slop pit, up the drain stair to Rhett's cage first, the gaol, the hall, the walk and the Head Witch.
  The way out is by the Guild's stair, or back through the sewer to the shaft.
- **Off the path:**
  - The witches' dormitory (T4) and the coven store, a storeroom with the hatch bolt.
  - The brewery: three cauldrons, +2 Personality, Endurance and Speed once per character (D-4).
  - The gaoler's room (T4, the prisoners' confiscated things).
  - The cistern, the old pump room (T4), and the dead man's hideout (his journal, his pack).
  - The warren (T4).
- **Loops (3):**
  - Coven and sewer by the cells' drain door and by the store's hatch, once its bolt is drawn from above.
  - The Head Witch through her wardens or through the brewery and her private door.
  - The cross to the outfall by the warren or by the east drain past the jetty shaft.
- **States:**
  - `riddle_answered` (D4's) decides the arrival.
  - The initiation cauldron sets `joined` (Warlock for Great Druids; the coven turns friendly).
  - The Head Witch's death sets `head_witch_slain` (Naomi's stocks open on D4; the coven turns hostile again).
  - Her chest needs `joined` or her death.
  - Each cage opens once and its prisoner is hidden for good.
  - The store's hatch bolt is two-state (from below: "The hatch is bolted from above.").
  - The cross's ambush is a map variable, shown once and kept after reload.
- **Exits (the `exit` preset, D-24; map frame: origin under the Guild's centre, D4's axes, z 0 the coven floor):**

  | Inside arrival | Where (x, y, z), facing | D4 door | Out to |
  | --- | --- | --- | --- |
  | `entrance:d4_guild` | Foot of the Guild's back stair, (−640, 640, 0), north (512) | the Guild after `q-d22.guild_right`: A6's `door:dd20_guild`, or a back door (open question 4) | Exit preset at the stair's top landing, to `entrance:dd20_guild` (the square, facing east) or the back door's point |
  | `entrance:d4_trapdoor` | The sump, (1,280, 0, −512), east (0); one way | `q-d22.guild_wrong` at the Guild's double door: "Wrong! Begone fools!", then the map's move (direct, D-24) | none ("The trapdoor is shut fast above you.") |
  | `entrance:d4_shaft` | Ladder's foot, (2,816, 2,048, −512), west (1024) | `door:dd20_sewer`, the grate by the jetty's foot (69, 83), open from day one (D-36 (4)) | Exit preset up the ladder, to `entrance:dd20_shaft` (69, 83), facing north |

- **Hooks (all placed):**
  - The coven hall: `q-d22.initiation`.
  - The Head Witch's room: `q-d22.head_witch` and `q-d22.witch_chest`.
  - The cells: `q-d22.camilla`, `q-d22.aretha`, `q-d22.isabella` and `q-d22.rhett`.
  - The niche: `q-d20.dragon`.
  - This map holds the arrivals of `q-d22.guild_right` and `q-d22.guild_wrong`.
  - `q-d22.guild_door` and `q-d22.coven_gone` are D4's, listed only.
- **Textures:**
  - The sewer and cells are MM7 The Tidewater Caverns 7d17: wet rock, plank walks and the outfall pool (A6's
    `dungeon_families` sewers assignment for DD-20).
  - The coven is MM7 Temple of the Moon 7d06's dressed stone, the same assignment's accent. Its Moon seal is used as
    the walk's double doors, never laid in the floor as in XD-04.
  - The Guild's back stair is D4's t09 ashlar, matching the Guild outside.
  - About 27 of 45 textures, 0 new. The Head Witch's mirror reuses A6's `xkmirror` (D-37).
  - It is kept apart from XD-04 (no 7d12 laboratory; the wet lower half) and from the other sewers (6d03, 6d08,
    sewer.blv).
- **Dressing and lights:**
  - Cauldrons stand on hearths beside the walking lines. Broom racks, the gaolers' table and the dormitory beds stand
    by the walls. The store is a storeroom (`store: true`).
  - In the coven, an iron lamp hangs from the ceiling over the initiation cauldron, braziers stand on the floor by the
    double doors, and there are wall sconces and lamps elsewhere. Candles stand on the Head Witch's dresser.
  - In the sewer, daylight falls through two bolted street grates (ceiling lights, "Sewer Drain"), a lantern hangs on
    a hook at the shaft's foot, the outfall's light comes through the lake bars, and the sump, cistern and niche are
    dark.
- **Lines:**
  - aaze0033: the cages and the four prisoners' lines (Isabella's "(yawn)", the source's last), Naomi's (D4's), the
    cauldrons, the mirror's "You are the most beautiful one of all.", beds and shelf.
  - aaze0034: "Sewer Drain", "Alcove", both journal pages ("...still haven't a clue where that statuette is..." by the
    niche; "...witches won't find me under here..." in the hideout).
  - The riddle (aaze0033:4–8) is D4's, listed as context.
  - A3's cage order is kept: Isabella is third, Rhett fourth at the sewer end, since his line points down to the Dragon.

**Kill XP against MAPS §0.** MAPS's row is a group: DD-05, DD-20 and DD-23, with 100 monsters, 24–45, and 30.5k.
DD-05's graph took 45 monsters and 14.29k. A third for DD-20 would be about 33 monsters and 10k, under the M floor of 45.

- **The graph takes the M floor.** 45 monsters: 24 × 875 + 3 × 1,575 + 13 × 1,344 + 4 × 2,000 + the Head Witch
  2,475 = 53,672.
- **13.42k per member.** That is −2 % on DD-20's share by count (45 of 100 is 13.7k).
- **On the joined route** the witches are not fought: 6.43k.
- **The group (assumed).** With DD-23 at its S floor (15 monsters, about 5.3k, A7's), the group comes to 105
  monsters and about 33.0k, +8 % on 30.5k, inside ±10 %. A2 recounts Act IV.

**Outdoor door check (D4 L1, `briefs/d4/L1/`).**

- **The Guild.** D4 has one door on the Guild, 4651's carved double door at (63.5, 87), facing east. It is both the
  house and `door:dd20_guild`, but the arrival hint names two inside points (the stair and the trapdoor). The
  trapdoor needs no door of its own: it is `q-d22.guild_wrong`'s move to `entrance:d4_trapdoor`. The sump lies under
  the square just east of the double door. The back stair needs either a choice on the door or a back door (open
  question 4). For (b), A6 adds a single-leaf cellar door on the Guild's west wall near D4 (61.5, 87), with a return
  point outside it.
- **The jetty shaft.** `door:dd20_sewer` is still `listed_only`. D-36 (4) makes it real and open from day one, with
  "Climb down to the sewer?" as the preset's meaning. Its point (69, 83), facing north, matches `entrance:d4_shaft`.
  It sits 2,816 east and 2,048 north of the Guild in this map's frame.
- **Size.** The coven reaches beyond the Guild's 2,048 footprint, under the square and the houses to its west and
  north. The outfall sits under the jetty's root. All of it is underground, so nothing on D4 changes.
- **Street grates (optional).** The sewer's two bolted street grates could have plain grates on D4's square (no
  event, not POIs), as D1's for DD-01.

**Open questions** (options and recommendations in the graph file):
1. Count and XP: 45 monsters and 13.42k (proposed; the group comes to 105 and ~33.0k with DD-23 at 15), or about 33 under
   the M band.
2. The Head Witch as a new coven boss row 11173 at 45 (proposed), or the source's Coven Leader at 60 counted later.
3. The four prisoners as named peaceful rows in the cages, hidden when freed (proposed, as DD-09), or cage events only.
4. The Guild's two destinations: a back cellar door for the stair (proposed), or a choice on the double door after
   the right answer.
5. Joseph the Prayermaster: left out, his line to the ledger (proposed); a Meditation teacher (A4); or a flavour actor.
6. The brewery's three cauldrons at +2 Personality, Endurance and Speed once per character (proposed), or dressing.
7. The cross's ambush as a hidden group of five shown on the first step (proposed), or all visible.

**Requests:**
- **A2:**
  - The boss row "Head Witch" (coven 11173, 45, look C, hp_x 3, DrainSP).
  - Four named peaceful rows (Camilla the Captured, Aretha the Helpless, Isabella the Victim, Rhett the Wimp; the
    next free ids in 11900–11999, peasant stand-ins, immobile, friendly).
  - The +2 Personality, Endurance and Speed record.
  - Recount the DD-05+20+23 group.
- **A6 (D4):**
  - `door:dd20_sewer` made real.
  - The Guild's back door, or the door's choice (question 4).
  - The two arrival points above.
- **A3:**
  - Three player bits and texts for the brewery cauldrons (if question 6 holds).
  - `guild_right`'s text naming the back stair (if question 4 holds).
  - Joseph's line and the mirror's for the ORIGINAL_LINES ledger.
