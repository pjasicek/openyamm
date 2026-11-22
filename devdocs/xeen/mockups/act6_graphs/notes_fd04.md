## FD-04 Dragon Tower and the Dungeon of Death

X7 · M · party 62 → 66 · 65–90, Energy Dragon 100 · 60 · treasure 6 · Q-F1 (Alister's egg, the roof to the Dragon
Clouds) and Q-F2 (the Dungeon of Death, the Lord Xeen Machine), optional finale

![FD-04](act6_graphs/fd04.svg)

The source's Dragon Tower (dark mazes 117–120, aazex117–120) and Dungeon of Death (121–124, aazex121–124) as one BLV.
The tower has four round floors above X7's crag top: z 0, 1,280, 2,560 and 3,840, where z 0 is 2,600. The Dungeon of
Death, Sandro's old home, has three floors under it: z −1,024, −1,792 and −2,560. The two halves meet at Sandro's door
in the gate hall's floor. It has 32 review rooms, about 42 sectors, about 58 M units² and 11 doors.

- **What it is.** The black tower on the crag at the rim.
  - **The tower.** A druid named Alister in the gate hall wants a dragon egg. Dead adventurers' notes say he is a
    fraud and hint at the Eye's answer. The nest on floor 2 holds the eggs. The crown's Energy Dragon keeps the roof
    stair to X9's Dragon Clouds.
  - **The dungeon.** Below, Sandro's key opens his old home: a walk-in crossword, a ballroom and game rooms full of
    liches, four Shrines of Evil, the gongs, and the Lord Xeen Machine to destroy.
- **Critical path, Q-F1.**
  1. The gate hall (`entrance:x7_gate`, quiet, Alister).
  2. The spiral stair, walked: first landing, ring hall, second landing, the nest (the egg).
  3. Back down to Alister. Or on up: the third landing, the high hall, the crown (Energy Dragon), the roof stair,
     and out to X9.
- **Critical path, Q-F2.**
  1. The gate hall and Sandro's door (`q-f2.door`, item 12354).
  2. The crossword (twelve clues), the descent, the welcome hall and the ballroom.
  3. Either game room and its shrine gallery to the Throne of the Dead (Sandro's note), then the bone stair.
  4. The gong hall: four gongs, then the lever raises the iron shutter.
  5. Maintenance, then the machine (`q-f2.machine`).
- **Off the path.** These rooms lie off the critical path:
  - The scorched hall (the old stable, a find).
  - The bone alcove (two notes) and the old dormitory (a chest).
  - The hatchery, and the last climber (a note, the Endurance potion, a chest).
  - The Wyrm's gallery (Ashkaroth's door) and the tome room (the Tome, a chest).
  - Do Not Disturb (coffins, a chest).
  - The fountain and the control room (the terminal).
- **Loops (5).**
  - Floor 1: into the ring hall from the landing or through the dormitory.
  - Floor 2: the nest directly or through the hatchery.
  - Floor 3: to the crown through the high hall or along the Wyrm's gallery.
  - Sandro's halls: a ring from the ballroom through either game room and its shrine gallery to the thrones.
  - The machine floor: from maintenance directly or through the control room.
- **Set pieces (4).**
  - The nest: a round hall round a bowl of black rock with three warm eggs.
  - The crown: the top hall under the cone roof, light from its vent, with the Energy Dragon.
  - The crossword: a hall floored with pale and black tiles (`xfgrid`), clue plaques round the walls, and each solved
    word lighting across the floor (a hidden `xfword` strip shown, with a pulsing light under it).
  - The Lord Xeen Machine: a black and brass engine fed by four elemental cores, each with a terminal.
- **Dragons and their floors (D-32).**
  - **Low openings.** The spiral stair and every opening between a dragon hall and a landing, alcove or gallery is 256
    wide and 288 high, and so is the crown's low door to the roof stair. The bodies are 487 high for the cloud
    dragons and 500 for the dark ones, so each floor keeps its own dragons. The arrival from X9 is quiet.
  - **Size.** The inside is larger than X7's shell (1,024 across, 2,048 high, DECIDE 8): round floors about 3,072
    across, halls 1,152 high, and the crown 2,048 to the cone's apex.
  - **The dungeon.** Liches are 180, Doom Knights 152 and Autobots 228 tall: rooms 512–768 high, the machine hall
    1,024.
- **Monsters and kill XP.**
  - **Tower (26).** Acid Dragon 66 × 6, Fire Dragon 75 × 8, Frost Dragon 85 × 6, Phase Dragon 90 × 5 and the Energy
    Dragon 100 (11653, boss row). The Phase Dragons are the Dragon Clouds' dragons, come down under the roof.
  - **Dungeon (34).** Lich Lord 65 × 10, Power Lich 75 × 6, Skeletal Lich 85 × 8 (the source's L2 liches), Doom
    Knight 75 × 4 (the two thrones' and the control room's guard) and Autobot 75 × 6 (the source's L3 robots).
  - XP: **100.22k per member** (400,896 / 4) against MAPS's 96.8k (+3.5 %). The tower is 46.39k and the dungeon
    53.84k.
  - Floor counts: floor 0 2, floor 1 6, floor 2 10, floor 3 8 (with the Energy Dragon), floor −1 2, floor −2 20 and
    floor −3 12.
  - Groups of 1–3. Quiet rooms (D-11.3): the gate hall (Alister is peaceful) and the roof stair. Also quiet: the
    landings, the alcoves, the Wyrm's gallery, the descent, the crypt, the fountain and the bone stair.
  - Not used: Screamer 58 and Annihilator 62 are under the band (DECIDE 1 (b)); Vampire King (DECIDE 13).
  - The machine's guards: two Autobots, two Power Liches and two Skeletal Liches in its hall, with two Doom Knights in
    the control room.
  - Rest encounters 0 (DECIDE 10).
- **Treasure.** Five chests at T6: the old dormitory, the last climber, the tome room, Do Not Disturb and the gong
  hall. Opening the gong hall's chest before the shutter is up silences the gongs, the source's "Touch any treasure
  and you'll have to start over!".
- **Original lines.** These are used as follows:
  - aazex117:0–4: Alister and the tower's exit ("Exit Dragon Tower?", the exit preset's meaning).
  - aazex118:0–5: beds, bones, the two notes ("I don't trust that druid guy …", "… forever, or really, really big").
  - aazex119:2–7: the potion "+40 end. perm" (rescaled to +2), and the notes on the crystal balls and "The eye of
    the Dragon holds the Silver Key Card." (A3 renames the card to Q-F1's reward).
  - aazex120:1–5: the Tome of Great Experience, its "You learn nothing new from the Tome", the bed and the chest.
  - aazex121:1–2, :7–8: the descent's refusal and reward, and Wrong!/Correct!. Twelve of the clues :11–188 are kept
    (DECIDE 4).
  - aazex122:0–5, :7–18, :24: signs, coffins, the thrones, the four shrines and Sandro's note.
  - aazex123:0–5: the gongs, the lever and the voice, the fountain.
  - aazex124:0–13: the machine's question, the core terminals, the papers, the Goober terminal, the room signs.
  - dark/aazex128:0 "Descend into Dragon Tower?": X9's way down (A5).
- **Door to X7.** A5's `thing:fd04_gate` (`door:fd04`) at [29, 31.62] has two leaves 384 × 448 on the crag top. The
  gate is at (−17920, 16578, 2600), facing south.
  - **Inside arrival proposed:** `entrance:x7_gate`, about 256 inside the leaves, facing north (512).
  - **Return:** the exit preset to X7's `entrance:fd04_door` (29, 32) = (−17920, 16384, 2592), facing south (1536).
  - The tower's key is DECIDE 2.
- **Roof to X9 (the Dragon Clouds).**
  - **Out:** the roof stair's hatch is the exit preset to X9's `entrance:fd04_roof` (`roof:fd04` in X9's
    project.yml). Its point is (20864, 18304) at floor 2,048 in plan.yml and NOTES, facing south, but objects.yml
    marks [20352, 17280]: A5 confirms one.
  - **Back:** X9's way down is a stair in the dragon-head rock ("Descend into Dragon Tower?", aazex128:0) to this map's
    `entrance:x9_clouds`, on the roof stair's top step facing down the stair.
  - **On X9 (A5, with A3's Q-F1):** the Eye of the Dragon's riddle ("What is the secret of the Dragon?", answer
    Infinity; the source's "Die fools!" as event damage) and its artifact. Also the four Ancient Books of the Dragon
    with the runes IN/FI/NI/TY, the three crystal balls (Mind, Past, Future: rescaled, never lethal), the Well of
    Fantastic Skill and the Dragon Power Crystals, rescaled (D-4).
  - **In the tower:** the clues to the riddle: the two dead adventurers' notes and the "eye of the Dragon" note.
- **The halves' join.** Sandro's door is a black iron door in the gate hall's cellar well, over the stair down.
  - `q-f2.door` with item 12354 opens it for good (118130). The key is kept.
  - Without the key the party sees a clear refusal that names it (A3, for example "A black iron door with Sandro's
    mark, a skull with a keyhole for an eye. It answers only to his key.").
  - From below it always opens.
- **Hooks (none exist yet; proposed for A3's q-f1.yml and q-f2.yml).**

  | Hook | Room | What it does |
  | --- | --- | --- |
  | `q-f1.alister` | gate hall | Alister's topics (a placed talking monster, `monsters[].npc`); takes the Dragon Egg and pays; sets Alister gone (118147) |
  | `q-f1.note_fraud`, `q-f1.note_forever` | bone alcove | the two notes |
  | `q-f1.egg` | the nest | gives the Dragon Egg once (118146) |
  | `q-f1.note_eye`, `q-f1.endurance` | the last climber | the note; +2 Endurance once per character (a player bit) |
  | `q-f1.tome` | tome room | fixed experience once per character |
  | `q-f2.door` | gate hall | needs 12354 |
  | `q-f2.crossword` | the crossword, the descent | twelve prompts; all twelve set 118143 and the descent's reward |
  | `q-f2.shrine_minor`, `q-f2.shrine_lesser` | Shrines of Lesser Evil | destructibles' questions and `on_destroyed`, experience |
  | `q-f2.shrine_great`, `q-f2.shrine_ultimate` | Shrines of Great Evil | the same; the Ultimate's ejection (118148, DECIDE 5) |
  | `q-f2.note` | Throne of the Dead | Sandro's note |
  | `q-f2.machine` | the machine | Q-F2 done, 118145 |

  The gongs, the lever, the voice, the fountain, the coffins, the thrones, the terminals and the papers are
  map-local lines.

  Ashkaroth (5703) is behind `door:wyrm_hall` (house 4853) in the Wyrm's gallery on floor 3, flavour only.

  Map qbits:

  | Qbit | Meaning |
  | --- | --- |
  | 118130 | Sandro's door open |
  | 118131–118142 | the twelve words |
  | 118143 | the crossword done (the descent open) |
  | 118144 | the iron shutter up |
  | 118145 | the machine broken |
  | 118146 | the egg taken |
  | 118147 | Alister gone |
  | 118148 | the Ultimate shrine broken |
  | 118149 | free |

  The gongs are map variables.
- **Textures.** None is assigned (DECIDE 7). Proposed, one shipped family per area:
  - **The tower:** MM6 Hall of the Fire Lord 6d04 (`vlcwl2`, `vlcwl2b`, `vlcwl4`, `vlcwl4b`, `vlcflore`, `vlcflord`,
    `vlcflorc`, `vlctrm4`, `vlctrm6`, `vlctrm8`, `vlcdora`, `vlcdorb`). It is the black vlc block of X7's shell
    (`vlcwl3a`) and unused in Xeen.
  - **Sandro's halls and the crossword:** MM8 Necromancers' Guild d19 (`gnecwal1`, `gnecwal2`, `gnecwal3`, `gnecflr`,
    `gnecstpf`, `gnecstpt`, `gnecclg2`, `gn_mtl03`, `tws1h`, `tws1f`, `t1books1`, `t1beds2`, `trim9_32`).
  - **The machine floor:** MM6 Control Center sci-fi.blv (`swll4dk`, `swll5dk`, `swfloor2b`, `swceilf`, `swr2dk`,
    `swdoora`, `swgirder`, `trekscrn`), with XD-19's four core textures on the cores.
  - **New:** two (`xfgrid`, `xfword`). About 36 of 45.
  - Music 13, map id 9182.

**DECIDE items (FD-04)** (options in the graph file; the proposed default first)

1. **Count and mix.** (a) Tower 26 dragons, dungeon 34 (liches, Doom Knights, Autobots), 100.22k (+3.5 %). (b) Four
   Lich Lords swapped for a new demons tier D "Screamer" 80 (the source's), 102.55k (+5.9 %). (c) The tower in the
   Dragon Clouds' rows only.
2. **The tower's door key.** (a) A new "Key to the Dragon Tower" in FD-01 Alamar Depths (A8, the source's place), which
   X7's `door:fd04` needs. (b) No key: X7's door asks and opens. (c) The key in XD-18's King's hoard.
3. **The join.** (a) Sandro's black door in the gate hall's cellar well: item 12354, open for good, the key kept, a
   refusal naming it. (b) The same, the key taken.
4. **The crossword.** (a) Twelve of the source's clues whose answers the main path names: Scepter, Vampire, Kalindra,
   Corak, Alamar, Necropolis, Sandcaster, Darkstone, Castleview, Sphinx, Mirror, Xeen. The twelve gate the descent
   and pay fixed experience. (b) The same, optional. (c) Dropped.
5. **The Shrine of Ultimate Evil.** (a) A tell in its question. Yes brings camera shake, fire damage about 20 % (never
   lethal) and `{exit: x7}` to `entrance:fd04_door` with the source's line; no experience; it stays broken.
   (b) It refuses, dressing. (c) The source's death.
6. **Alister and the egg.** (a) He takes it, pays fixed experience, "Now I'll just drink this egg potion and...". He
   is gone on the next load, and a small lizard sits in his alcove. (b) He becomes a Fire Dragon and fights.
   (c) The egg can also go back to the nest.
7. **Textures.** (a) 6d04 tower, d19 halls, the sci-fi machine floor, two new. (b) 7d28 tower, cd2 halls.
   (c) 7d37 for the ballroom and game rooms.
8. **The inside and the dragons.** (a) Larger than the shell (D-39 Q6): floors about 3,072 across, 1,280 apart, every
   opening off a dragon hall 288 high, and a headless check. (b) Shell-sized: no dragon fits.
9. **Looks.** (a) Own recolour skins for the Energy Dragon, the Power Lich and the Skeletal Lich. A2 moves 11284 and
   11285 from bosses to ordinary tiers. (b) Shared skins.
10. **Rest encounters (9182).** (a) 0: Alister is peaceful, and the liches' slot rolls tiers under the band. (b) 10 %
    cloud dragons at Dif 5.
11. **Rewards (D-4).** (a) +2 Endurance once per character. The Tome, the crossword, three shrines and the machine pay
    fixed experience inside A3's optional budget. (b) Drop the Tome's and the shrines' experience.
12. **The main terminal.** (a) No prompt: "Main Terminal. ACCESS DENIED." and the Goober lines, nothing implying a
    code. (b) The source's prompt, every answer wrong.
13. **The vampires.** (a) The coffins stay shut: flavour and a chest. (b) A new tier "Vampire King" 90 × 2 that wakes
    at the crypt's chest (about +2.1k).

**Requests to other lanes**

- **A2:**
  - Items: the Dragon Egg (Q-F1) and the Key to the Dragon Tower (DECIDE 2 (a)).
  - Rows: Alister's peaceful placed-only row (for example 11922, a male druid body, friendly, stand, NoArena, not
    counted, made unkillable by the map's load event as D-52).
  - Rows: 11284 Power Lich and 11285 Skeletal Lich as ordinary tiers (DECIDE 9).
  - FD-04 in the `where` of the dark dragons, liches, robots and dark knights.
  - Row 9182, encounter 0.
  - The Act VI recount (60, 100.22k), and the +2 Endurance device in the ledger.
  - Only for the (b) options: Screamer 80 (11635) and Vampire King 90 (11296).
- **A3:**
  - Write `q-f1.yml` and `q-f2.yml` with the hooks above (names, rooms, bits, texts, experience inside the optional
    budget), and Q-F1's X9 hooks (`q-f1.eye`, `q-f1.runes`) with A5.
  - Lines: the twelve crossword prompts with answers and spelling variants; the Ultimate shrine's tell; the gongs'
    reset line; the terminal's lines; Sandro's door's refusal.
  - ORIGINAL_LINES rows for aazex117–124 and aazex128:0.
  - X7's tower-door hook if DECIDE 2 (a).
- **A4:** an NPC id for Alister (for example 5705) in `towns/fd04.yml`: house none, placed in the gate hall's west
  alcove. Confirm `door:wyrm_hall` on floor 3's gallery.
- **A5:**
  - X7: `door:fd04` into `entrance:x7_gate`, with the key check if DECIDE 2 (a).
  - X9: the roof link to FD-04's `entrance:x9_clouds`, one confirmed point for `entrance:fd04_roof`, and the Dragon
    Clouds' Q-F1 content (the Eye, the runes, the balls, the well, the crystals, its dragons) with A3.
- **A8:** the Key to the Dragon Tower placed in FD-01 Alamar Depths (DECIDE 2 (a); the source's (13,3)).
- **A6:** the FD-04 lines in `towers.yml` / `dungeon_families.yml` (6d04, d19, the sci-fi machine floor); register
  `xfgrid` and `xfword`.
- **S:** own recolour skins for the Energy Dragon, the Power Lich and the Skeletal Lich; Alister's body (a recoloured
  shipped druid, no Meshy).
- **AU:** nothing required (a shipped gong, an engine hum and an explosion).
- **A1:** nothing. Every word used exists: destructibles with `on_destroyed`, text prompts, step plates, hidden
  decorations shown, camera shake, `{exit: x7}`, `monsters[].npc`, house doors, named arrivals.

**State and next steps.** The graph, the SVG and these notes are written (lane A7's graph sub-agent, 2026-11-21,
sixteenth session). The render printed no overlap. The PNG from headless Chrome
(`output/studio_cal/a7/phase6_graphs/fd04.png`) was looked at. Nothing is built or installed. Next: the decider
answers the DECIDE items, then L1.
