# XD-12 Darzog's Tower, L4: notes

A new dungeon (no original) built with the Map Studio from its own brief by one agent, 2026-11-15/16, following
`devdocs/xeen/ACT2_BUILD.md`: L1 the floors and the vertical spine, L2 the rooms and connections, L3 the geometry, L4
the contents. Cloudside's first **L** set piece (MAPS.md section 0 and "Dungeons"), story step **M21** (QUESTS.md).
Key `xd12`, map `xeen_xd12.blv`, map_stats 9140, qbits 110500-110502 (of 110500-110599), item 12230 (of 12230-12299).

**State.** `oymap validate` no issues on L1-L4, `fmt --check` clean. The build's only warnings are the placed
monsters' names (shown on corpses only: Baron Darzog, his clones, the Chief Librarian, Crodo). `oymap audit`: no
faces in one plane (0 pairs), 51 of 55 sectors reached (the 4 not reached are the open-air band outside the keep,
never walked by design), five `ride.no_switch` warnings for the trapdoors (below). `oymap solve`: step 0 24 sectors,
step 1 (doors, the works gate's winch) 35, step 2 (the High Sorcerer's key 2112) 49, step 3 (qbit 110500, Darzog
dead) 51; nothing stranded. Playtests **4 of 4** each on the final build (`output/studio_cal/xd12/run/final7_four.out`, after merge 38's words:
`playtest.yml` 124 steps, `playtest_b.yml` 98 steps; the earlier passes `pass1_four.out`, `final_four.out` .. `final5_four.out` likewise).

**Scratch** `output/studio_cal/xd12/`: `tools/` the generator (`geo.py` the frame and helpers, `shell.py` the rooms and
openings, `design.py` the plan's spaces, `plan.py` the plans and project cards, `dress.py` furniture, objects and
wiring, `emit.py` writes a level: `python3 emit.py L3|L4`, `python3 plan.py L1|L2`); `go.sh` builds, installs into
`mount/` and plays one test (`go.sh playtest_b.yml <log> x2` plays in `mount_x2/`, this map
plus X2's current build, for the exits); `four.sh` the four runs of both; `mount_x2.sh`; `rules/` the old no-magic scene
overlay (unused since merge 38); `shots2/` the final pictures (34, HUD off, `tour_final2.yml`), `shots/`, `shots_a/`, `shots_b/`, `shots_l3/`
earlier takes; `sheet_*.jpg` contact sheets; `renders/` plan and iso; `ref/` the shipped maps measured; `metrics.json`,
`solve.txt`, `audit.txt`, `things.txt`, `scale_bands.txt`.
**What was scripted:** every project file of L1-L4 except the playtests and these notes is written by the generator in
`output/studio_cal/xd12/tools/`; no hand edit was made that a rerun would lose (each run recorded with `oymap record`).
The generator stays the source until someone edits the project by hand; then retire it (note it here).

## Pass two (the lead's review of `shots2`, 2026-11-16)

1. **The trapdoors' tell** (13 read as a rug or a stain): every hatch now **sags 32 below the floor** (its lift stops
   32 short) in a **broken rim of red rubble** (the hole's sides, the School of Sorcery's cfb1, seen as a dark lip all
   round), and **bones and a skull** of someone who did not mind the flags lie at its edge (dec29, 7dec20). The cracked
   flags stay on the hatch. Shipped worlds have no cracked-flag texture that reads better than 7d14's c1t1fl (searched:
   crack, broke, rubble, ruin, hole, pit); small debris models are outdoor boulders in a dungeon (tried, removed).
   All five checked: `shots6/01`-`06` (reading room, north walk, west walk, Study of the Arm, Study of the Mind, close).
   The party steps down onto it; the drop and the winch play as before (playtest_b: raised again it stands at 1504).
2. **The roof's views**: the battlements' sill is 64 (was 96); **a railed stone balcony** (320 x 384, rails 48) hangs
   out over the lake from the middle of the south battlement, and **a railed stone pier** (the overlook, 448 out) runs
   from the Well's west rim over the shaft. From the balcony the lake fills the view down to the haze (the outside
   band now reaches 16,384: `shots6/07`, `08`); over the ordinary battlements beside a merlon (`09`); from the overlook
   down and across the Well, its storeys, the disc and the red light of Darzog's floor (`10`, `11`); the rim from the
   roof (`12`). Taken from where a party stands (the camera 36 from the rail).
3. **Merlons**: blocks along every battlement (`13`, `14`, `16`: crenellated parapets round the whole roof).
4. Found while looking: the sky stair's stone ceiling and wall tops above the roof stood as a dark frame against the
   sky; it is open to the sky now (theme `theme:sky_stair`; `15`, `17`, `18`).

Monsters, mechanisms, wiring and the critical path are unchanged; both playtests 4 of 4 (`final6_four.out`).

## Merge 38's words (2026-11-16)

- `project.yml rules: {no_spells: true}`: the build writes the scene's `runtime_restrictions: {allow_spellcasting:
  false}` itself. The hand-written overlay is gone from `go.sh` and both scratch mounts (kept, unused, in
  `output/studio_cal/xd12/rules/` as a record); the playtest's `cast_spell` is still refused.
- `map_stats.bolster: LowerToEqual`: `oymap install` writes the 9140 row of `bolster_maps.txt` (A4 of
  CHANGES_FOR_BUILT_MAPS; checked in the mount).
- The outside band's lake-side walls are `surface` sky with `bands: false` (they were a whole-wall sky panel over the
  stone band); the same look (`shots7/`).
- Rebuilt, installed; both playtests 4 of 4 (`final7_four.out`).

## The tower

A square keep 6,144 across (interior -3072..3072) on Lake Darzog's island, round **the Well**: an octagonal shaft
1,792 across from the gate floor (0) to the open sky (4,224), with a column of Darzog's lightning (five pulsing
blue-white lights) up its axis from a rune circle at its foot. Four floors 768 apart (rooms 640 high, 128 floors) and a
battlemented roof at 3072. Each floor is a double ring: four galleries in a pinwheel round the Well (arches into it on
the gate floor, railed windows above, Darzog's disc landing on his floor), and outside them four side rooms and four
corner rooms. **The stairs are two-storey halls** (rooms stack since S7): one long flight up the outer wall to a
hanging gallery at the upper floor, alternating **west (0-768), east (768-1536), west (1536-2304), east (2304-roof,
open to the sky)**, so every floor is crossed. Outside the keep a band of open air (`room:out_*`) holds the island's
grass and trees, a muddy bank and Lake Darzog out to the haze, under the open sky (`atmosphere.yml open_sky`, preset
fair, view outdoor): seen from the windows (slits on the gate floor, windows above, tall windows in the stair halls)
and from the battlements; a fall from the keep lands there and leaves for X2.

| Floor | Rooms (sectors) | What |
|---|---|---|
| Gate (0), Castle Gloaming's keep stone, orange torches | gate hall (arrival, the tower door), 4 cloister walks, hall of hands (10 plinths, statues of hands), guardroom ($), storeroom ($), cistern (sunken water), cells, crypt (coffins, a sarcophagus $), west stair hall (12) | carnage hands, eyes; quiet arrival |
| The works (768), Gloaming's red rock and lava | 4 walks, forge of the hands (lava channel, anvils, half-built hands), assembly hall (racks, **the works gate's winch**), smelter (lava pit, $), scrap hall, parts store, apprentices' quarters ($), east stair hall behind **the works gate** (11) | the hands' factory |
| The library (1536), the School of Sorcery's stone, books and candle sconces | 4 reading walks (**the warning note**), reading room (Book of Speed), great library (bookcase rows, **the Chief Librarian and his cabinet with the High Sorcerer's key**, Book of Accuracy, a bookcase $), 4 studies (Might, Endurance, Intellect, Personality), library stair hall behind **the locked library door** (11) | the six study books, **five trapdoors** |
| Darzog's floor (2304), Gloaming's state rooms, red torches | 4 state galleries (**the disc's grille**), **Darzog's hall** (inlaid rug, coffered roof, dais and chair, banners, Darzog and six clones), Darzog's study (**journal**, hoard $5), bedchamber (**the portrait**), **Crodo's cell** (secret), clone vats (green brew), guard hall ($), portrait hall (Gloaming's portraits, tapestry, banners), sky stair (12) | M21 |
| Roof (3072) | 4 terrace parts round the Well's rim, the **cloud stair** (exit to X9) | the vista, down the Well and over the lake |
| The Well, 4 bands of open air outside | (5) | the spine; the backdrop |

55 sectors (51 walked + 4 outside; the lake balcony stands in the south one). Floor area: **150.5 M units² walked**
(`metrics --reach` walkable area; band 120-200) and 1,199 M with the outside band (since pass two a backdrop of grass,
bank and lake out to 16,384, the view distance, that nobody walks: see "Words needed"). Height range 3,392 of floors (-160 to 3,232), 4,224 to the sky. 15 doors (31 door records with
leaves, lifts, mover and switches), 9 chests, 2 secret faces (the portrait), 266 light sources (1.8 per walked
M), 328 decorations (40 of them trees and rocks on the island).

## Monsters (MM7 stand-ins, as XD-01 to XD-05)

`world: mm7` at L4 (L1-L3 say `xeen`). The slots are the three families MM7's own wizard maps use (Clanker's
Laboratory: Beholder, Gog, Golem; Castle Lambent: Mage, Angel, Golem):

| Brief (Xeen family) | Stand-in | Levels | Spawn points (tier) |
|---|---|---|---|
| Slot 1 Magic constructs (Carnage Hand 35) | MM7 Golem: Brass Golem (b), Gold Golem (c) | 35, 50 | 11 b (gate floor 5, works 6), 3 c (Darzog's floor) |
| Slot 2 Wizards (Darzog's apprentices) | MM7 Mage: Wizard (b) | 35 | 7 b (library 5, quarters, portrait hall) |
| Slot 3 Eyes (Darzog's watchers) | MM7 Beholder: Floating Eye (a), Gazer (b) | 30, 40 | 3 a (Well, cistern, works), 5 b (library 3, roof 2) |
| Darzog's clones (45) | 6 Archmages (294, Mage C) placed, group 31 | 50 | placed in his hall |
| **Baron Darzog** (boss 55) | Archmage (294) placed, `hp: 1200` (three times), name | 50 | on his dais, group 30 |
| The Chief Librarian | Archmage (294) placed, `hp: 600`, name | 50 | by his cabinet, group 21 |
| Crodo | Sorcerer (292, Mage A: an old bearded man in robes), peaceful, immobile, group 40 | | in his cell |

Map card `[2, 3]` per spawn point: 29 points, about **72** spawned, plus 8 placed hostiles = **about 80 with Darzog**
(band 70-80 plus the boss). 1.5 per walked sector. The clones wear Darzog's face (the same Archmage): the Baron is the
one on the dais. Kill experience at these stand-ins is about 151k for the party (38k each) against MAPS section 0's
32.1k each: 18 % over, from the C-tier 50s standing in for 45-48 (the lead's act count should see it).

## Loot and the six books

Treasure level 4 (map card `Tres 4`, Castle Gloaming's and Castle Lambent's), lock 12, trap 6, perception 12, refill 336
(Gloaming's row). Chests at level 4: guardroom (400 gold), storeroom (250), the crypt's sarcophagus, smelter, quarters,
the great library's bookcase (a Cabinet), the guard hall (600), the Chief Librarian's cabinet (the **High Sorcerer's
key 2112** standing in for the library key 12230, and one roll); **Darzog's hoard** at level 5 (one step up: 1,500
gold and three rolls).

**The six study books** (the source's "Book of Might ... +20 Might (permanent)", aaze0060, rescaled): a lectern each,
title "Book of Might" etc., **+5 to the reader's base stat, once per character** (player bits 11230-11235): Might
(Study of the Arm, south-east), Endurance (Study of the Body, south-west), Intellect (Study of the Mind, north-west),
Personality (Study of the Voice, north-east), Speed (the reading room's west end), Accuracy (the great library's
east end). A second read says "You have already learned what the book of might can teach." Playtested: Accuracy and
Might, both refuse a second read.

## Mechanisms, and the trapdoors' tells

- **The works gate** (east walk to the east stair hall): an iron portcullis (c1d1). Clicked while down: a message
  window, the chains run south, the winch must be in the assembly hall. **The winch** (a lever on the assembly hall's
  west wall) raises it (map var `works_gate_up`).
- **The library stair door** (carved hhm1d2): locked; without the key a message names the Chief Librarian's cabinet
  in the great library, south of the Well. The key opens it for good (qbit 110502).
- **Five trapdoors** (the source's pit floors on its L2): each a hatch 256 square in a library floor, plugged by a lift
  in the works room below raised flush with the floor (a lift rises through an `in: floor` hole). **Tells:** the hatch
  is the School of Sorcery's **cracked flags (c1t1fl) in a floor of whole flags** (a dark square, plain at a glance:
  `shots2/13`, `15`), and **the apprentice's note** pinned opposite the doorway where the east stair arrives ("MIND
  THE CRACKED FLAGS. The Master's hatches drop you straight down to the works, and the hands down there are not
  friendly. Walk round them. -- Wil") is read before any of them. Stepping on one drops it (speed 900) with the party
  768 to the works, among hands; **a winch lever** on the nearest wall below raises it again, and the party standing
  on it rides back up (played: trap3, down and up, and down again on purpose as a quick way to the works). Where:
  north reading walk, reading room (east end), west reading walk (on the way to the library door: the walks round
  it), Study of the Arm (before the Book of Might), Study of the Mind.
- **Darzog's disc**: a mover (a stone slab 384 square, the summoning circle on its top) on the Well's north face
  between Darzog's floor (its rest) and the gate floor, behind **a black grille**. While Darzog lives the disc, its
  grille and both call buttons give a message ("It answers to Darzog alone while he lives"); his death opens the grille
  (the disc is up). Then clicking the disc, the button on the Well's wall beside the landing, the call button in the
  north state gallery or the one in the Well at the bottom (beside the north arch) moves it and its grille together.
  The way down after Crodo, and back up.
- **Darzog's portrait** (Gloaming's cnbport-3, a secret door, pulses for Perception): while he lives a message, an old
  man's face behind the painted eyes, the frame held by his spell; after his death it slides up on Crodo's cell.
- **The cloud stair**: five steps of cloud on the north roof; the top step leaves for X9 once Crodo is freed; before,
  "The cloud gives under your foot like fog. Something holds it shut: Crodo would know what."
- Plank doors (Gloaming's 7trimd, folding sideways) on the guardroom, storeroom, crypt, cells, smelter, quarters,
  Darzog's study and bedchamber; Darzog's doors two leaves; the studies' carved doors (hhm1d2).

## How M21 plays

1. Arrival (one-shot message window): "DARZOG'S TOWER. The Skeleton Key turns, and the door that has been sealed since
   Crodo vanished swings in ... Artemus was right to suspect the Baron: somewhere above, Crodo still lives. And the air
   itself is wrong. Every spell you reach for dies before it is shaped: Darzog's ward stills all magic in this tower but
   his own. Here you fight with steel. The stairs climb the west and east halls in turn; the Baron keeps the top floor."
   (No Roland spoiler before Crodo; Artemus' suspicion of Darzog is M6's.)
2. The gate floor, the west stair, the works; the works gate's winch; the east stair; the library: the note, the books,
   the trapdoors, the Chief Librarian's key; the library stair.
3. Darzog's floor: the hall's cue ("Seven figures in the Baron's robes turn as one. 'Which of us,' they ask together,
   'will you kill first?'"); his death sets **m21_darzog_slain (110500)**, shakes the tower, opens the disc's grille,
   with a message window. His journal in the study names the portrait.
4. The portrait opens on the cell; stepping in, Crodo speaks (a message window) the source's own lines (aaze0061:
   "Thank you for rescuing me from Darzog's clutches. I didn't know that someone else had received my message. Xeen's
   hideout is just above us in the clouds. You will need the sword the adventurers were working on in the dungeon of
   Newcastle to defeat Lord Xeen ... You must make haste. Xeen plans to summon an army from the Darkside to conquer our
   world.") with M21's reveal added: "Prince Roland" is Lord Xeen, an undead general of a greater master; ask Artemus
   for leave to dig (M22). Sets **m21_crodo_freed (110501)**, 35,000 experience each (the act's quest rule), and Crodo
   spends the one small spell Darzog's fading ward allows him on going home (he vanishes).
5. Down by the disc and out by the tower door (X2), or up the sky stair and the cloud stair (X9).

Original lines used (aaze0059-0062): "Leave Darzog's Tower" (the tower door's title), "Book of Might" ... "+20 Might
(permanent)" (rescaled to +5), Crodo's thanks and warning above, "Crodo the Overseer". The source's "old rope ladder
hanging above the rusty cage" became the trapdoors' winches.

## No magic (the map flag)

`project.yml rules: {no_spells: true}` (the studio's word since merge 38): the build writes the scene's
`runtime_restrictions: {allow_spellcasting: false}` (MM7's Shoals rule, OY-350: spellbook, quick spells and scrolls
read from the packs refused). Played: the playtest's `cast_spell` (Torch Light) is refused. The arrival message says
so in the world's voice. **But the game's refusal says "You can't do that while underwater"**
(`PartySpellSystem::UnderwaterText`, and "You can not do that while you are underwater!" for scrolls in
`InventoryItemUseRuntime.cpp`): in a dry tower that line is wrong, and only a game change can give the restriction its
own line (for example "Darzog's ward stills your spell."); for the user's decision (no game code changed here). Before
merge 38 a hand-written scene overlay did this (`output/studio_cal/xd12/rules/`, now unused).

## Measured against shipped large castles and towers

`oymap metrics --reach` (`ref/*.metrics.json`), `scale_bands.py`:

| Map | Sectors | Floor M (walked) | Height range | Doors | Chests | Spawn pts | Light src | Decor | Monster slots |
|---|---|---|---|---|---|---|---|---|---|
| **XD-12 Darzog's Tower** | 55 (51 walked) | 1,199 with the backdrop (**150.5**) | 3,392 (sky 4,224) | 15 (31 records) | 9 | 29 + 9 placed | 266 | 328 | Golem, Mage, Beholder |
| MM7 Castle Gloaming (d03) | 48 | 175.5 (76) | 4,920 | 0 (records only) | 6 | 26 | 264 | 236 | Lich, Vampire, Necromancer |
| MM7 Castle Lambent (7d30) | 28 | 108.0 (90) | 1,416 | 13 | 8 | 24 | 149 | 127 | Mage, Angel, Golem |
| MM7 Castle Harmondale (7d29) | 71 | 92.4 (80) | 3,712 | 27 | 10 | 29 | 218 | 261 | Rat, Goblin, Bat |
| MM7 Clanker's Laboratory (7d12) | 25 | 14.3 (11) | 1,320 | 17 | 14 | 16 | 66 | 37 | Beholder, Gog, Golem |
| MM7 School of Sorcery (7d14) | 17 | 16.8 (13) | 703 | 16 | 2 | 19 | 15 | 2 | Mage, Golem |
| MM6 Castle Alamos (cd1) | 180 | 173.5 (153) | 2,256 | 13 | 14 | 152 | 785 | 429 | Sorcerer, Barbarian, ElemAir |
| MM6 Castle Darkmoor (cd2) | 194 | 599.7 (534) | 1,860 | 12 | 1 | 132 | 332 | 415 | BLich, BBeholder, Ogre |
| MM8 Castle of Air (d27) | 17 | 28.4 (22) | 2,008 | 11 | 11 | 22 | 115 | 52 | Air Elemental |

Room sizes (`scale_bands.py`, all sectors): bigger rooms 4.6 M (shipped median 1.64 M, percentile 88), typical ceiling
640 (74), taller rooms 800 (74), doorways 384 (61); the largest room is an outside band (78.6 M); the largest walked
room is the north roof (11.7 M), then the stair halls and side rooms (4.1 M each). Like Gloaming in sectors, walked
area per sector (2.96 M against Gloaming's 1.6-3.7 M), light sources per walked area (1.8 against 1.5) and spawn
points (29 against 26); taller in its spine than any shipped tower but Gloaming. Monsters stay at the adopted 80
(shipped L 120-180: HANDOFF "not reconciled").

Texture families (`texture_use.py --project`): the keep from **MM7 Castle Gloaming** (cnb, cwb1, cwb, ckb, t4s1fl,
tfb03, cfb1, lava, 7trimd/7trimda, the rug tfb1r4i, portraits cnbport-1..4, banners necro-a/b, tapestry tap10),
the library from **MM7 the School of Sorcery** (twb2, 7tfb1, tfb2, 7t1s2b, 7t1books, 7t1books1, 7t1cabs, c1t1fl, td1,
c1d1, hhm1d2, t2bedsht), the island from the Hall under the Hill's grass and dirt (7grastyl, 7dirt1) and 7wtrtyl
water; XD-04's generated xwsky (sky faces' picture), xwcloudst (the cloud stair) and xwbrew (the clone vats). Lights:
Gloaming's torch02 (orange lanterns) below and its torch07 (red) on Darzog's floor, so the tower reddens toward the
Baron; candle sconces (scon100) with their own light objects in the library, chandeliers (dec27), candlesticks.

## Playtests (4 of 4)

- `playtest.yml` (124 steps, level-33 party of four, immortal): the arrival event; **spells refused**; the gate floor,
  the west stair to the works; the winch raises the works gate; the east stair; the note (window); the Chief Librarian
  dead, the key from his cabinet; the Book of Accuracy works once; round the west walk's trapdoor (asserted unmoved),
  the library door opens to the key; the library stair; Darzog's doors, the hall's cue, Darzog and the clones dead
  (actors 7 and 0), qbit 110500, the grille open; his study door, the journal (window), his hoard; the bedchamber, the
  portrait opens, Crodo's words (window, "Lord Xeen"), qbit 110501, Crodo gone; onto the disc, ridden down (z 0), off
  north, the bottom button sends it up and calls it down, ridden up again (z 2304); the sky stair, the roof's cue, the
  cloud stair leaves for X9's stand-in (MM7 Celeste 7d25.blv) with the three qbits.
- `playtest_b.yml` (98 steps, in `mount_x2`): the guardroom door and chest; the disc's call button refuses while
  Darzog lives (window) and the disc stays; the works gate refuses before its winch (window), the winch; the Study of
  the Arm round its trapdoor (unmoved), the Book of Might works once; the library door refuses without the key (window);
  **the west walk's trapdoor drops the party to the works (z 768, the hatch down), its winch raises it with the party
  (z 1536)**, taken again on purpose, the west stair down to the gate hall, **out by the tower door to X2** at
  (-15631, 3014) on the island.
- Not played: the fall from the keep into the outside band (the step events `evt:fall_*`, leave to X2) -- a party
  cannot be dropped out of a window by the harness; the other four trapdoors (the same words as trap3).

## Pictures (looked at)

`output/studio_cal/xd12/shots2/` (34, HUD off; sheets `sheet_g1.jpg` .. `sheet_g4.jpg`) and, for pass two,
`shots6/` (18: the five trapdoors, the balcony, the overlook, the merlons, the sky stair; sheets `sheet_k1.jpg` ..
`sheet_k3.jpg`). Best:
`03-well-up-to-the-sky.png` (the Well from its foot: four storeys of windows, the disc at the top, the sky),
`28-roof-down-the-well.png` (3,000 down the Well from the roof's thin rim to the arches), `17-darzogs-hall.png` (six
identical Archmages and the Baron on his dais down the rug), `14-great-library.png`, `10-works-window-down-the-well.png`,
`30-forge-window.png` (a tree and the lake through a works window), `27`/`33` (over the battlements: the lake a dark band
under the haze), `20-the-portrait.png`, `21-crodos-cell.png`.
What I judged and changed after looking: Gloaming's torch07 lit everything blood red (orange torch02 below, red kept
for Darzog's floor); the battlements' 256-thick wall top hid the lake and the Well's 128 rim hid the shaft (the roof now
overhangs to 32 of the open air and 16 of the Well); the outer walls of the outside band showed as stone (bands
override a wall's `surface`: panels of sky instead); Air Warlocks as Darzog were women (Archmages now); the disc's sides
took the Well's sky (a mover now); a bed blocked the bedchamber's door; a peasant youth as Crodo (a Sorcerer now).
Weakest: the roof is still a broad flat terrace; the cloud stair reads as blue-marbled
steps; the gate floor's slits show only sky; the rug is pale; the stair halls are long and plain.

## Words needed (and the workaround used)

1. ~~A map's runtime restrictions (no spells)~~: given by merge 38 (`rules: {no_spells: true}`), used.
2. **A backdrop room** (seen, never walked: the island and lake round the keep): `rooms[].backdrop: true`, left out of
   floor area, reach and solve, and allowed to have levels that touch its walls. Workaround: four ordinary rooms whose
   floor is `floor_points` with a `floor_surfaces` region of water (a sunken level may not touch a wall), counted in the
   metrics (1,199 M with them, 150.5 M walked).
3. **A trap lift** (a hatch that drops whoever steps on it, MM-style): `lifts[].trap: true` so that `audit` does not
   call it a ride without a switch at its top (five `ride.no_switch` warnings), or a `doors[].kind: trapdoor` on an
   `in: floor` opening (a leaf that swings down). Workaround: a lift in the room below, raised flush, with a step event.
4. **A lift's own top and side surfaces**: a lift takes one `surface` (its top); its sides take the room's wall, which in
   the Well is the sky. Workaround: Darzog's disc is a mover.
5. **A hover name on a stepped thing** (the cloud stair's top step: `oymap things` lists it without one).
6. **A placed monster's living name and hit points** (Darzog, the Librarian: the scene carries `hp` 1200/600, the
   health bar shows the kind's 400): the boss rows of PRODUCTION E14.
7. **Battlements**: merlons along a parapet opening (`openings[].merlons: {width, gap, height}`). Workaround since
   pass two: platforms 128 x 32, 160 high, every 384 on the roof's side of each battlement (on the south parapet block,
   96 on its 64).
8. **A parapet as part of an opening that can be broken by a way through** (a doorway in a battlement, sill 0, beside
   parapets with a sill): side by side openings leave a wall stub between them that rises to the room's top (seen
   from afar as a post). Workaround: the south battlement and the Well's west rim are one opening each with sill 0,
   their parapet a block of the roof (64 high) broken where the balcony and the overlook begin.

## Tool defects

1. **Two wiring events with one id pass `validate` and build as one handler**: `evt:guardroom` (a chest) and
   `evt:guardroom` (a door) became one event with both sources (`oymap things` showed the chest's faces under the door's
   event); found by `things`, fixed here by renaming. `validate` should refuse a duplicated event id.
2. ~~A wall's `surface` does not override the room's `bands`~~ (merge 38: `walls[].bands: false`, used) (rooms.yml `walls[].surface`: "another surface for the
   whole wall"): the outside band's walls kept their stone band; panels over the whole wall work.
3. The headless runner opens no window from a timer (known, XD-05): the arrival and Darzog's death are asserted by their
   variable and qbit.
4. `loot_chest(n)` in `play_lua` takes the chest's **event** number, not its container index (an easy mix-up: the
   first run read the Book of Might instead of a chest).

## Exits

- `exit:lake_island` -> `xeen_x2.odm` at **(-15631, 3014, 768), facing east** (X2's `devdocs/xeen/briefs/x2/DOORS.md`,
  updated after X2's first build), from the tower door (event 41) and from a fall into the outside band (events 26-29).
  Played into X2's current build. **X2's `door:xd12` should arrive at this map's start: (2752, 0, 0) facing west
  (180)** in the gate hall, inside the tower door.
- `exit:clouds_of_xeen` -> **placeholder**: X9 is not built; MM7's Celeste (`7d25.blv`, a city on the clouds) at
  (-2432, -1472, 1) stands in. One line to change when X9 exists.

## What the user should look at when playing

- The first room: the gate hall's arch, the cloister, the Well and its lightning straight ahead; walk to the rune
  circle and look up.
- Every window: the lake and the island's trees; the roof's battlements and the Well's rim (look down).
- The library's cracked flags: are they a fair tell at a glance? (the note says so before the first one); step on one.
- Darzog's hall: seven identical Archmages; the Baron on the dais. Then the journal, the portrait, Crodo's words.
- The disc down the Well after Darzog; the cloud stair after Crodo.
- That no spell works anywhere, scrolls included; the refusal still says "underwater" (a game text to change).
- The colour: orange below, red on Darzog's floor.

Textures to generate (stand-ins in place): a pinned parchment note 64 x 128 (now the white sheet t2bedsht at 0.5); cloud
steps (now xwcloudst); a mirror is not needed (the portrait is Gloaming's own).

## Hostility pass (2026-11-16)

The user found monsters peaceful to the party beside hostile ones of their kind and monsters fighting each other
(devdocs/xeen/ACT2_BUILD.md, "Hostility pass"). MMerge's `hostile.txt` decides a slot monster's relation to the party
and two kinds' to each other; the studio now warns of both (`oymap build`) and the map says its relations in objects.yml
`relations` (the build's load event `evt:studio_relations`). Written by `output/studio_cal/xd12/tools/dress.py`: the
Golems (277-279) and the Wizards and Archmages (293, 294) the party's foes (not the Sorcerer 292: Crodo is one), and the
Eyes (211-213) kept from the Golems and from every Mage, Crodo too, both ways (the table: Eye toward Golem 4, Golem
toward Eye 1, Eye and Mage 4). `playtest_hostility.yml` (written by
`output/studio_cal/hostility/gen_hostility_tests.py`) checks the slot and placed foes hostile, the peaceful ones
peaceful and the map's kinds, spawned side by side near the party, not taking each other on; it passes twice, as do the
map's other playtests.
