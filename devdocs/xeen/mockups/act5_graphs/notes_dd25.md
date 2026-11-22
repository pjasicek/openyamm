## DD-25 Bosco's Hall

D5 · town BLV · party 45 → 52 · no monsters · no chests · Q-D17 (Bosco gives the Northern Tower's key, takes the Chalice) · 3 services, 4 Grandmasters

![DD-25](act5_graphs/dd25.svg)

The source has no hall. Bosco the Dwarf King stands out on the Desert of Doom (dark maze0013, cell (1,8); aaze0013:13–17).
WORLD_DESIGN §5.2 and MAPS's D5 sheet give him "a dwarf hall dug into the highlands (small BLV)" with a smith, a tavern,
an Earth guild and two residences. A4's `source/towns/dd25.yml` names six doors (4701–4706). This is the first town BLV
among the graphs.

The graph shows 14 boxes: 8 rooms (about 12 sectors) and 6 house screens. A house screen is the MM6–MM8 house dialog
behind a clicked door face; it has no geometry. The floor is about 9.9 M units². There are 8 doors: the gate and the
throne hall's doors are two-leaf pairs, and the six house doors are clicked faces with no movers.

- **What it is.** A short underground street, one axis from the gate west into the crag:
  - the gate hall, with the Alehall's door first;
  - the great hall round its hearth;
  - the King's steps up to the throne hall, with the King's Hall door behind the dais.
  - Side ways: the Forge and the Mailwright side by side on the smiths' gallery (open at both ends: the loop); the
    Tinker on the burrow lane; one stair down to the Deep Guild of Earth.
- **Critical path.**
  1. The gate passage (`entrance:d5_bosco`, quiet). The gate hall, the great hall, the King's steps, the throne hall's
     two leaves.
  2. Bosco's door behind the dais (house 4704). His A3 topics give the key: started 113340, key 113341, autonote
     4570. Q-D17's hand-in takes the Chalice later (done 113343).
- **Way back.** Round the hearth, then out through the smiths' gallery past the Forge and the Mailwright to the gate.
- **Off the path.** Every dead end holds a door:
  - the Alehall: the gate hall's south wall, about 800 from the arrival;
  - the Tinker's Burrow: the burrow lane;
  - the Deep Guild of Earth: the guild hall at z −384, one stair down from the lane's west end. TOWN_FEEL puts guilds
    and temples apart or raised; "Deep" puts it below.
- **Loop (1).** Gate hall → great hall → smiths' gallery → gate hall.
- **Set piece.** The throne hall at z 128:
  - Bosco's empty throne on a three-step dais under his banner (`xdbosban`, once per face);
  - the long tasting table on the north wall, with its cups and the taster's stool;
  - braziers on the floor by the dais;
  - the King's Hall door behind the dais.

  This follows Stone City's Throne Room: an EnterHouse bound inside a walk-in hall (DECIDE 2). The great hall's round
  hearth (`7cdb`) is the town square. It is a dressing set piece, and the walking lines pass 512 clear on either side.
- **Size, argued.** There is no town-BLV precedent in the graphs:
  - **MAPS D5:** "dwarf hall, small BLV".
  - **WORLD_DESIGN §5.2:** 3 services, 2 residences plus the King.
  - **ROADMAP §5.5:** `towns.py` holds residences to §5's numbers. A4 counts the King's Hall as a third residence.
  - **TOWN_FEEL 5c (`--small`):**
    - Services 5–25 and residences 6–56. DD-25 has 3 and 3; WORLD_DESIGN's numbers win, and both are kept as "Town
      feel exceptions" lines in the map's NOTES.
    - Service-to-service median 854–2,424. Ours is about 2,300 (Alehall to Forge 2,290; Deep Guild to Forge about
      3,950).
    - The tavern among the first doors from the arrival (rank 0.05–0.33): the Alehall is the first.
    - Weapon and armour shops next to each other: the Forge and the Mailwright, 768 apart.
    - `town_feel.py` reads ODMs only; these rules are applied by hand.
  - **The shipped measure:** MM7 Stone City `7d24`'s town quarter. Its octagon of 2,176 has timber house fronts, the
    approach and the Throne Room behind (sectors 4, 5, 11, 12, 15, 27–29, 31–34). It holds 18 doors (9 services, 8
    residences, the Throne Room) in 12 sectors and 13.95 M units².
  - **Ours:** six doors and a walk-in throne hall in about 12 sectors and 9.9 M. That is inside S's figures (6–15
    sectors, 7–20 M, 3–8 doors) (DECIDE 1).
  - **Footprint:**
    - great hall 2,048 × 1,536 (vault 768);
    - throne hall 1,536 × 1,280;
    - Deep Guild hall 1,280 × 1,024;
    - smiths' gallery 2,048 × 512;
    - gate hall 768 × 1,024;
    - burrow lane 1,280 × 512;
    - King's steps 512 × 768;
    - guild stair 512 × 768;
    - gate passage 512 × 384.
- **Monsters and kill XP.** None: a town. The MAPS row DD-25 has "—" and maps.yml has `monsters: "0"`.
  - No kill XP, and nothing goes into Act V's kill budget.
  - No rest encounters: there is no hostile row to draw from (D-39), so resting is allowed and quiet. The Alehall sells
    food (D-29, price 20).
  - Peaceful dwarves stand in the halls, uncounted (DECIDE 3): two gate guards, two throne guards, four townsfolk.
- **Treasure.** None: no chests and no finds (maps.yml treasure "-"). The shops are the treasure: the Forge at
  quality 4, axes and maces. Q-D17's reward is A3's: 2 Energy Disks, 5,000 gold, 14,000 experience, award 457.
- **Lights and props** (lanes/README):
  - Light: sconces on the walls and pillars, two chandeliers hung from the great hall's vault, braziers standing on
    the throne hall's floor, the forge bay's glow inside its wall opening, lamps on the guild hall's floor. None on a
    leaf or in a doorway.
  - About 30 light sources (7d24 has 3.86 per M) and about 25 decorations (7d24 2.77 per M).
  - Props by the walls only:
    - a pair of ale barrels beside (not before) the Alehall's door;
    - an anvil beside the Forge's door;
    - benches along the great hall;
    - the guild hall's crystal vein.
  - Kept clear: 384 either side of every walking line and 256 before every door.
- **Original lines.**
  - aaze0013:13, "Bosco / The Dwarf King": his name and title.
  - :14, the seer and the Chalice: A3's opening topic and A4's greeting.
  - :15, "Please get the Chalice. I live in fear for my life.": the started state.
  - :16, "Oh, thank the Gods! ... I dub thee royal taste tester...": the hand-in, MAPS's original line. The +1,000,000
    experience is A3's 14,000.
  - :17, "Ah, the taste testers! Please, please, sit down and drink with me for awhile! My halls will always be open
    to you.": proposed for after `done` (DECIDE 5). A3 and A4 do not use it yet.
  - New lines (A3): the first arrival, "The hall rings with hammers. A dwarf at the gate looks you over, then your
    boots, and waves you in." (map qbit 117680); the well, "Cold and clean. The King had it tasted this morning."
- **Door to D5.** D5's `door:dd25` (`thing:bosco_door` at cell (60.7, 46.25), about (−1,690, 9,088)) is a 384 × 320
  doorway in the crag with two `t09a03a` leaves, mirrored. It is sealed with a message until DD-25 is built.
  - **Inside arrival:** `entrance:d5_bosco`, confirmed as D5 assumed it (D-37). It stands in the gate passage 256
    inside the leaves at (2,048, 0, 0) in the map's frame, facing west (1024), into the hall. The frame: great hall
    centred on 0, 0; the leaves in the east wall at x 2,304; z 0 = D5's sill. The leaves' inner face is the same
    mirrored `t09a03a` pair.
  - **Return:** the `exit` preset (D-24; the source has no "Leave" line) to D5's installed `entrance:dd25_door`
    (−512, 9,216, 2,688), facing 0 (east). That point is at the end of `link:bosco_lane` on the terrace, about 1,050
    east of the leaves, facing away. **It matches.** Keep it: D5's town-buffer figure (2,700) is measured from it.
    D5 changes only the door: drop the sealed message and add `into: {map: xeen_dd25.blv, arrival:
    entrance:d5_bosco}`.
- **Doors.** All six of A4's door ids are confirmed and drawn:

  | Door | House | Kind | Resident | Where |
  | --- | --- | --- | --- | --- |
  | `door:forge` | 4701 | weapon shop | Durgan, Axe GM | smiths' gallery |
  | `door:alehall` | 4702 | tavern | Brunna | gate hall |
  | `door:guild_earth` | 4703 | Earth guild | Stonebeard, Earth GM | Deep Guild hall |
  | `door:kings_hall` | 4704 | residence | Bosco | behind the throne |
  | `door:mailwright` | 4705 | residence | Hilde, Chain GM | smiths' gallery |
  | `door:tinker` | 4706 | residence | Gimble, Repair GM | burrow lane |

- **Hooks.** None. `quest_hooks.yml` names no hook on DD-25 (checked). Q-D17 lives in Bosco's topics (house 4704). The
  flavour topics are Brunna's, Stonebeard's and Gimble's (`npcs/flavour/dd25.yml`). `q-d17.tower_door` belongs to D5;
  `voice`, `chalice` and `oath` belong to DD-08. Map qbits: 117680 `dd25_arrived_once`; the rest of 117680–117719 is
  free.
- **Textures.** MM7 Stone City `7d24`'s town quarter (DECIDE 4), about 24 of S's 30, 1 new:
  - walls and vaults: dressed `cwb` walls under `cwb1` rock vaults;
  - floors: `7tfb1`, `cfb1`;
  - trim: the `trim1_32` frieze, `7trimd`/`7trimda`;
  - the six house fronts: `hdr1b`, `hdm2b`, `hdp1b`, `hdp1er` under `hhm1rf`. No Xeen map uses them; XD-09 took only
    7d24's rock;
  - the hearth: `7cdb`;
  - the throne hall's two leaves: `hdr1dl`/`hdr1dr`, each its own wing;
  - the gate: `t09a03a` mirrored (D-49);
  - signs: `sgweapon`, `7sgtvrn`, `sgearth`;
  - the well: `7wtrtyl`;
  - new: `xdbosban` (Bosco's banner, once per face).

  Distinct from XD-02 (6d05/6d09, the Cloudside dwarves), XD-03 (7d34/6d18), XD-09 (7d24's rock hub, the other face)
  and every D5 dungeon.

**DECIDE items** (options in the graph file; the proposed default first)

1. **Size.**
   - (a, proposed) About 12 sectors, 9.9 M units², 8 doors, one loop, a walk-in throne hall, the guild one stair down:
     inside S's figures.
   - (b) Stone City's octagon alone: six house fronts round one hall, about 6 sectors and 6 M, no loop.
   - (c) About 18 sectors and 15 M, with four closed dwarf house fronts to reach TOWN_FEEL's 6 residences.
   - Evidence: the 7d24 quarter (18 doors in 12 sectors and 14 M). Depends: A4's residence check, L1.
2. **The King's Hall.**
   - (a, proposed) A walk-in throne hall (the set piece) with `door:kings_hall` behind the dais. Stone City binds
     EnterHouse 216 inside its walk-in Throne Room. The throne stands empty, and Bosco is in the house screen.
   - (b) A house front on the great hall like the other five.
   - (c) As (a), plus Bosco as a placed talking actor on the throne (`monsters[].npc` 5401: a row from A2, a body from
     S).
3. **Townsfolk.**
   - (a, proposed) Eight peaceful dwarves standing, uncounted: four guards on the engine's Dwarf A rows (MM7's allied
     dwarves) and four on the Peasant Dwarf rows, none on a walking line.
   - (b) The four guards only.
   - (c) None.
   - Xeen has no peaceful dwarf row, and the characters block is full at 11923. Depends: A2, A4.
4. **Textures.**
   - (a, proposed) 7d24's town quarter, with the house fronts no map uses.
   - (b) MM8 Dark Dwarf Compound `d41` (grey and black, unused in Xeen), with 7d24's fronts for the doors (two
     sources).
   - (c) 6d09, XD-02's kin.
   - Depends: A6.
5. **aaze0013:17** ("My halls will always be open to you").
   - (a, proposed) Bosco's greeting once `q-d17.done` is set, if A4's format has a greeting by qbit; else (b).
   - (b) The first sentence of A3's done text.
   - (c) Not used.
6. **The Chalice on show.**
   - (a, proposed) From `q-d17.done`, a shipped goblet decoration on the tasting table (a stage by load event).
   - (b) Nothing.
7. **After the Voweless oath.**
   - (a, proposed) No change in the map: the King's Hall still opens, and his topic says "Get out."
   - (b) The throne hall's leaves refuse from `oath` on: "The guards cross their axes. The King will not see you."
8. **The well.**
   - (a, proposed) A plain well against the great hall's south wall, no boon. D5 already has the Fountain of Might and
     the Last Water.
   - (b) No well.
   - (c) +5 Earth resistance once per character.

**Requests to other lanes**
- **A1:** nothing. House doors, stages by qbit and two-leaf doors exist. `town_feel.py` has no BLV mode; the rules
  were applied by hand.
- **A2:** the Act V recount, DD-25 0 monsters. For 3 (a): friendly stand-ins on the engine's Dwarf A and Peasant Dwarf
  rows (placed, not counted). A row and a body only under 2 (c).
- **A3:**
  - Register map block 117680–117719.
  - Two map-local lines: the arrival and the well.
  - aaze0013:17 under 5.
  - ORIGINAL_LINES rows for aaze0013:13–17.
  - The oath line only under 7 (b).
- **A4:**
  - The six door ids are confirmed.
  - The residence count: WORLD_DESIGN's 2 plus the King's Hall, so `towns.py` should take 3 or count the King apart.
  - Place the townsfolk under 3 (a).
  - A greeting by qbit for 5 (a).
- **A6:**
  - On D5, `thing:bosco_door`: drop the sealed message and set `into` to `entrance:d5_bosco`. The outside point stays.
  - Add DD-25 (the 7d24 town quarter) to `dungeon_families.yml`.
  - Register `xdbosban` (proposed name).
- **AU:** optional distant hammering. The anvil ring and the tavern murmur are shipped.
- **S:** nothing under the defaults; the goblet and the dwarves are shipped.

**State and next steps.** The graph, the SVG and these notes were written on 2026-11-21 (A8 session 11, phase 5,
graphs only; nothing is built or installed). The render printed no warnings. The PNG
(`output/studio_cal/a8_s11/png/dd25.png`, headless Chrome) has been checked. Next: the decider answers the DECIDE
items, then L1.
