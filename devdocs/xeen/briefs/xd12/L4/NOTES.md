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

**The ward by run (U-18, 2026-11-26):** `rules: {no_spells, no_monster_spells, solo_spells, solo_spell_damage_percent:
50}` write `allow_spellcasting: false`, `allow_monster_spellcasting: false`, `allow_spellcasting_solo: true` and
`solo_spell_damage_percent: 50`. A party run: nobody casts, the monsters included (they fight with their attacks). A solo
run: everyone casts, every spell at half damage (the solo character's spells, scrolls and wands, the monsters' and every
event spell, D-193). A lone mage otherwise had nothing to fight with in a main-quest tower (a player on Discord). The
arrival window has a solo state (D-191: `m21.arrival`, `evt.RulesetInfo().soloRun`): "Every spell you shape comes out at
half its strength, and so does every spell cast at you"; `playtest_solo_arrival.yml` checks it and a solo cast.

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

## Rebase, phase 0 (2026-11-20): placed sounds

The studio's `objects.yml sounds[]` (any .wav of the engine's audio) is used: ten ambient sounds, written by
`output/studio_cal/xd12/tools/dress.py` ("PLACED SOUNDS"), nothing else changed (a rerun of the generator before the
change gave the project unchanged; after it, `objects.yml` gains `sounds:` and `ids.lock.yml` their keys 1-10). Heard by
3D distance without occlusion, so each stands about mid-height in its room and its inner radius is under the floors'
768; the floors above and below hear it only faintly.

| Sound | Room | At (z built) | File | Radius / inner / volume | Play |
|---|---|---|---|---|---|
| `sound:forge_lava` | forge (works) | (0, 2848) over the lava channel, 928 | lava loop | 1500 / 640 / 0.8 | loop |
| `sound:smelter_pit` | smelter | (2496, 2496) over the pit, 928 | lava loop | 1000 / 300 / 0.5 | loop |
| `sound:clone_vats` | clone vats | (2496, -2496) between the vats, 2464 | bubbling cauldron01 | 1000 / 350 / 0.7 | loop |
| `sound:lightning_foot` | the Well | (0, 0) on the rune circle, 112 | 7sparks | 1600 / 400 / 0.8 | wait 4-10 s |
| `sound:lightning_high` | the Well | (0, 0), level with Darzog's floor, 2512 | 7sparks | 1400 / 400 / 0.7 | wait 5-12 s |
| `sound:cistern_drip` | cistern | (-768, -2496) over the water, -96 | drip02 | 900 / 250 / 0.5 | wait 3-9 s |
| `sound:wind_n/s/w/e` | the four roof terraces | (-1024, 2176), (1024, -2176), (-2176, 0), (1472, 0); 3328 | whistling wind | 2000 / 800 / 0.3 | loop |

The crackles and the drip are looping sounds with a `wait` (each plays once, then waits): the game applies a wait
only to a looping sound, and `loop: false` would play once per arrival.

Checks (files in `output/studio_cal/xd12/`): `validate` no issues (`sounds_validate.txt`); `build` only the nine
placed monsters' names (`sounds_build.txt`), the scene's `ambient_sounds` has the ten; `audit --reach --solve`
(`sounds_audit.txt`) and `solve` (`sounds_solve.txt`) the same as the build before the sounds, line for line (0
coplanar pairs, 60 handlers, five `ride.no_switch`). The older `audit.txt`/`solve.txt` (2026-11-16 00:49, before
pass two) say 59 handlers (before the hostility pass's load event) and 51 of 55; since pass two's balance the
solve reaches 52 (the south outside band, part of it: step 2 50, step 3 52, never reached 26, 27, 29). `fmt --check`
clean. Playtests **4 of 4** each (`run/sounds_four.out`: `playtest.yml` 124 steps, `playtest_b.yml` 98), played one
game at a time with the game's asset root **`assets_dev`** (the game built 2026-11-20 needs engine files the scratch
root `output/studio_play/xeen_root` of 2026-11-16 lacks: `solo_shop_stock.yml`); the studio's
validate/build/install/audit still use `output/studio_play/xeen_root`. The headless runner does not play ambient
sounds, so the runs show only that the scene loads and plays as before; nobody has heard the sounds yet (no pictures:
nothing to see). To hear: the forge, the Well's foot, Darzog's floor by the Well, the roof.

## Rebase, phase 0 (lane A8, 2026-11-20): the design part

What the move into the Xeen world (ROADMAP §6 phase 0, A8 step 3) applies, decided now; only the placed sounds are
built (above). The rest needs A1's world install (W5), A2's rows and A3's hook table.

**Monsters (MAPS §0: 30–48, Darzog 55, 80 monsters, 32.1k kill XP per member; MONSTERS_AND_ITEMS §2 Magic constructs
18/24/35, Wizards 36/45/60, Eyes 40/50/65).** Only the tiers inside the band are used. The Eyes' slot takes one or
two per marker (it was two or three), which brings the experience to the budget.

| Slot | Family, tier, level | Spawn points | Expected |
|---|---|---|---|
| 1 | Magic constructs C, Carnage Hand 35 (Darzog's hands; new model, `model_stand_in` until S makes it) | all 14 (gate floor 5, works 6, Darzog's floor 3), [2, 3] | 35 |
| 2 | Wizards A, Wizard 36 (his apprentices) | all 7 (library 5, quarters, portrait hall), [2, 3] | 17.5 |
| 3 | Eyes A, Floating Eye 40 (his watchers) | all 8 (Well, cistern, works, library 3, roof 2), **[1, 2]** | 12 |
| placed | The Chief Librarian: Wizards B 45 with his placed name (E14), no hit-point change; carries the library key | great library | 1 |
| placed | **Darzog's clone 45, boss row** ×6 (Darzog's look and name, ordinary hit points, Lightning Bolt) | his hall | 6 |
| placed | **Baron Darzog 55, boss row** (×3 hit points, about 1,400; Air spells) | his dais | 1 |
| placed | Crodo: a peaceful named actor (an old man; A2 row or an NPC actor), immobile | his cell | — |

72.5 hostiles, kill experience 129,000 for the party, **32.3k per member (+1 %)**; groups 2–4.

**Treasure** stays: Tres 4, chests at 4, Darzog's hoard at 5; lock 12, trap 6, perception 12, refill 336. The six
study books (+5, once per character, player bits 11230-11235) stay.

**Items and bits for A2 and A3:** the library key 12230 (the Chief Librarian's; stand-in MM7 High Sorcerer's Key
2112), the Skeleton Key 12100 (from XD-11, X2's range; the tower door outside tests it; stand-in MM7 1461); qbits
`m21_darzog_slain` 110500, `m21_crodo_freed` 110501, `library_door_opened` 110502; player bits 11230-11235 for the
books (A3: register them as the world's player bits). Crodo's words (M21) and the arrival message are quest text: A3's
hook text replaces them.

**Original lines** (for A3's ledger; aaze0059–0062): "Leave Darzog's Tower" (the tower door's title), "Book of Might"
... "+20 Might (permanent)" (rescaled to +5), Crodo's thanks and warning ("Thank you for rescuing me from Darzog's
clutches ... Xeen plans to summon an army from the Darkside to conquer our world."), "Crodo the Overseer".

**Studio words since the build:** `rules.no_spells` (in since merge 38; the hand-written overlay in `rules/` is unused),
bolster `LowerToEqual` (row 9140), `walls[].bands: false` (the outside band), placed engine sounds (built, above).
Doorway `floor` and model `turn` are outdoor words. Still wanted: the game's own refusal line for a no-spell map (it
says "underwater"; a game change for A1 and the user).

**Exits** checked against `briefs/x2/DOORS.md`: `exit:lake_island` → `xeen_x2.odm` (-15631, 3014, 768) facing east,
unchanged. `exit:clouds_of_xeen` stays one-way to MM7's Celeste only while the map is an MM7 stand-in; in the Xeen
world it is **sealed until X9 exists** (the cloud stair says the cloud will not bear the party yet, no exit).

**Textures:** 45 distinct face textures in the build (L cap 70), none new (`xwsky`, `xwcloudst`, `xwbrew` are XD-04's).

## Into the world (lane A8, 2026-11-20)

The map now belongs to the Xeen world: `world: xeen`, installed as `assets_dev/worlds/xeen/maps/xeen_xd12.blv` (with its
`.scene.yml`, `.studio.yml` and `events/maps/xeen_xd12.lua`) by `oymap install --root assets_dev` (the world's tables
unchanged: their hashes before and after the install match). Its map_stats (9140), bolster and slot rows are the
world's (A2's `source/map_rows.yml`); project.yml repeats the slots. The sections above that speak of MM7 stand-ins,
Celeste, the High Sorcerer's key or `m21_*` bits are the build's history.

**What changed** (generator `output/studio_cal/xd12/tools/`: `plan.py`, `dress.py`; `python3 emit.py L4`, `plan.py
L1|L2`, `emit.py L3`, `oymap fmt`, `oymap record --author agent:xeen-a8-xd12 --label "into the world"` on L1-L4; the
generator reproduced every level byte for byte before the change; L1-L3 changed only by the bits' names and "the
library key"):

| Thing | Before | Now |
|---|---|---|
| World, slots | `mm7`; Golem, Mage, Beholder | `xeen`; `Xeen Construct` (Dif 5, [2, 3]), `Xeen Wizard` (0, [2, 3]), `Xeen Eye` (0, **[1, 2]**), as map_rows.yml |
| Spawn tiers | b/c golems, b mages, a/b eyes | all 14 construct markers c (Carnage Hand 35, 11602), all 7 wizard markers a (Wizard 36, 11190), all 8 eye markers a (Floating Eye 40, 11570) |
| Baron Darzog | Archmage 294, `hp: 1200`, name | boss row 11194 (level 55, 1,404 hit points, the row's name): `hp` and `name` dropped |
| Six clones | Archmage 294, name "Darzog Clone" | boss row 11195 ("Darzog's Clone", 338 hit points): name dropped |
| Chief Librarian | Archmage 294, `hp: 600`, name | Sorcerer 11191 (the Wizards' B tier, 45), placed name kept (`hp` dropped). The build warns the name shows on the corpse only (no `place_mon.txt` row; outside the project): kept |
| Crodo | MM7 Sorcerer 292, peaceful, name | the world's character row 11900 (A2: peaceful, "Crodo", the Mage A look), peaceful, immobile, group 40; name dropped |
| Items | 2112, 1461 | library key 12230 (the Librarian's cabinet); Skeleton Key 12100 on `exit:lake_island`'s outside condition |
| Quest bits | `m21_darzog_slain`, `m21_crodo_freed` | `darzog_slain` 110500, `crodo_freed` 110501, `library_door_opened` 110502 (m21.yml's names); the books' player bits 11230-11235 unchanged |
| `exit:clouds_of_xeen` | to MM7's Celeste (7d25.blv) | removed (neighbour, plan entrance). The cloud stair's top step (event 9) says "The cloud thins to fog above the last step. It will not bear you yet." after Crodo, the old "Something holds it shut: Crodo would know what." before; Crodo's speech loses "The clouds above the roof will bear you now." Sealed until X9 exists |
| `exit:lake_island` | `xeen_x2.odm` (-15631, 3014, 768) east | unchanged |
| Relations | MM7 Golems/Mages hostile, Eyes apart from them | Xeen ids: 11600-11603, 11190-11196, 11570-11572 at 4 (long) toward the party, Crodo 11900 friendly (relations.yml's levels restated: the studio's check reads only hostile.txt); the Eyes kept from every construct, wizard and Crodo both ways (the world sets no feud; this keeps it so) |
| Text | "The High Sorcerer's key turns ..." | "The library key turns in the carved lock." |

`rules.no_spells`, bolster `LowerToEqual`, the ten placed sounds stay (`sound:clone_vats` moved with the vats to
(2656, -2656)). project.yml and objects.yml notes carry no stand-in wording (the note's sheet texture is still a
placeholder picture, as before).

**Hooks: none wired (blocker, A3).** `data_tables/quest_hooks.yml` has no `m21.*` hook: `source/quests/m21.yml` is
`status: outline`, and `tools/xeen/gen_quests.py` skips outlines, so no hook has a `call`. The map keeps its own texts
for the arrival window, Darzog's death window and Crodo's words (m21.yml's drafts differ from them); its bits are set
by the map's own effects. When A3 makes M21 full: an effect `{lua: 'XeenQuests.hook("m21.arrival")'}` in `evt:arrive`,
`m21.darzog` in `evt:darzog_dead`, `m21.crodo` in `evt:crodo` (and `else_effects`, a once-hook), `m21.library` in
`evt:library_stair`, `m21.cloud_stair` in `evt:cloud_stair` if it gets a call, each replacing the map's text for that
moment. Also for A3: m21.yml's `player_bits` name 11231 intellect, 11232 personality, 11233 endurance; the map (since
the build) uses 11231 endurance, 11232 intellect, 11233 personality (might 11230, speed 11234, accuracy 11235 agree):
the labels in m21.yml should follow the map.

**Dressing** (`formats/DRESSING.md`). Measured on the build before the moves (`xexport_before.json`) and after
(`xexport.json`): containers with `tools/measure_xd12.py` (XD-27's copy of A7's measure, `--objects`); every floor
prop and furniture platform 32 or more high against the walking lines with `tools/walk_lines.py` (new: lines between
every pair of a room's doorways and arches on one level, from the generator's openings, and from each to the start and
Darzog's disc; windows, rails, battlements, the Well's upper rims and the trapdoor holes are not ways through; radius
+ 64 for a decoration from decoration_data.txt, 64 for a platform's edge; hung and table-top props, the island's
backdrop and the trapdoors' bones, their tell, left out). `--targets` adds lines to chests, lecterns, the journal and
switches, stricter than DRESSING.md: listed in `walk_after_targets.txt` (20, all tables or candles beside the thing
walked to), not required.

- Before (`dress_before.txt`, `walk_before.txt`): containers 2 of 11 offending (the gate hall's keg 318 from the
  storeroom's doorway, the storeroom's second barrel 256 from the cistern's); walking lines 20 offenders: the Well's
  north-east brazier (on the east arch's line to the disc), the hall of hands' four outer south plinths (on the lines
  from the cloister arch to the side doors), two of the crypt's three south coffins (the third, not counted, stood in
  front of the stair doorway), the
  storeroom's two barrels (on the line between its doorways), the forge's two half-built hands and the west anvil, the
  scrap hall's fourth heap, the reading room's east table and the Book of Speed's lectern (on the line between the
  studies' doors), the great library's north-west bookcase and the Librarian's desk, the Study of the Arm's desk, the
  clone vats' north-west vat, Darzog's hall's south-east candelabrum.
- Moved (`dress.py`, each marked "dressing (2026-11-20)"): the Well's four braziers onto the octagon's slanted faces
  (±632, ±632); hall of hands' south row now three plinths (-1408, 2048), (0, 2240), (1408, 2048), statues as before
  on the even ones (two plinths removed); crypt: two coffins lying along the west wall, the north row and the
  sarcophagus as before, the skull pile to (-2944, 2768) (one coffin removed); storeroom barrels onto the two east
  crates (128 up); the gate hall's barrel pair 64 north; forge anvils along the lava channel (y 2656), the two hands
  into the south corners (±1344, 2048); scrap heap to (-2048, 2816); reading tables to the north half (y 2688, their
  candles with them), the Book of Speed's lectern to (-1536, 2816); great library: the north-west case is two cases
  against the north wall (-1408, -896), the desk to (768, -2752); the Study of the Arm's desk against the east wall
  (2944, -2112); the clone vats one block of four in the south-east corner; Darzog's east candelabra to (1152, 2880)
  and (896, 2816).
- After (`dress_after.txt`, `walk_after.txt`): containers 0 of 11 offending (to wall 64-158, storeroom barrels on the
  crates; to a portal min 345, to a door face min 264); walking lines 0. Groups: pairs in the gate hall (barrel and
  keg), the parts store (barrel and keg) and the storeroom (barrels on the crates), singles elsewhere; the storeroom's
  2 barrels, 2 sacks and 4 crates line its walls. Barrels, sacks and crates were already only in the gate hall,
  storeroom, cistern and parts store. Racks (assembly hall, guard hall), beds, the guard table, the dais chair, the
  banners and portraits (wall panels) passed as they stood.

**Checks** (all on `openyamm-studio/build-xeen/oymap`; files in `output/studio_cal/xd12/`):

- Check root `xroot` (`cp -al assets_dev`, then `tools/mk_studio_root.py`, XD-27's: the indoor validate/build read
  monster rows and items only from the engine tables). `validate` L3 and L4: no issues (`xvalidate.txt`). `fmt --check`
  L1-L4: clean.
- `build --assets xroot` (`xbuild.log`): 55 rooms, 3,663 faces, 145 portals, 31 doors, 71 lights, 29 spawns, 60
  events, 9 chests; one warning, the Librarian's name (above). No hostility warning.
- `audit --reach --solve` on the installed map, `--world xeen --assets assets_dev` (`xaudit.txt`, `xsolve.txt`): 0
  faces in one plane; 22 of 55 sectors on foot as the doors start, 52 with every door out of the way; five
  `ride.no_switch` (the trapdoors, as before); solve step 1 35 sectors, step 2 50 by `item 12230`, step 3 52 by `qbit
  110500` (the grille, the disc), step 4 the portrait; never reached 26, 27, 29 (the outside band, as the current build);
  one exit, `xeen_x2.odm at -15631, 3014, 768`.
- Playtests **4 of 4** each, one game at a time, exact PIDs, from `assets_dev` with `--world xeen --map xeen_xd12.blv`
  and `build-xeen/game/openyamm` (`xfour.sh`, `xfour.out`, logs `xrun/four_134259/`): `playtest.yml` 143 steps,
  `playtest_b.yml` 97, `playtest_hostility.yml` 40, all after the last dressing move.
  - `playtest.yml`: the Xeen rows at load (one 11194, six 11195, one 11191, one 11900, 20+ 11602, 10+ 11190, 6+ 11570,
    no 292-294, 278-279, 212); the arrival window by its text (`advance_runtime: {present_dialogs: true}`), the note,
    the key 12230 from the Librarian's cabinet, the Book of Accuracy, `library_door_opened`, Darzog's death window
    ("binding cracks like ice") and `darzog_slain`, the journal, the portrait, Crodo's window and `crodo_freed`, the
    disc; on the roof the cloud stair's step event runs (`pressure_plate_triggered` 9), clicked again it says "will not
    bear you yet", and the party stays on the roof with the three bits.
  - `playtest_b.yml`: the arrival window by its text, the call button, works gate and library door refusals, the Book of
    Might, the trapdoor and its winch, and the tower door's question ("Darzog's Tower", OK/Close).
  - `playtest_hostility.yml` (by hand, as XD-27's): 11602, 11190, 11570, 11191, 11194, 11195 none peaceful and each
    hostile; Crodo 11900 peaceful; no stand-in rows; Crodo, a Carnage Hand, a Floating Eye and a Wizard spawned side
    by side do not take each other on, the Wizard goes for the party.
- **Monsters at load** (six boots, `xrun/probe/counts.txt`, `run_counts.sh`): 73, 76, 80, 69, 71, 73 actors (mean
  73.7 with the 9 placed: 72.7 hostiles; design 72.5). Per kind (separate boots): Carnage Hand 33.8 (design 35),
  Wizard 17.3 (17.5), Floating Eye 13.5 (12). Kill experience (monster_data: 1575, 1656, 2000; Sorcerer 2475, Darzog
  3575, clones 2475): 33.8 x 1575 + 17.3 x 1656 + 13.5 x 2000 + 2475 + 3575 + 6 x 2475 = about 129,900 for the party,
  **32.5k per member against MAPS §0's 32.1k (+1 %)**, as the design's +1 %.
- Pictures (`xshots/`, sheets `xshots_s_1.jpg` to `_s_3.jpg`, tour `tools/shots_x.py`; `xshots2/`, `xshots2_s_1.jpg`;
  `tools/run_game.sh --isolated ... --binary build-xeen/game/openyamm --world xeen --map xeen_xd12.blv --assets
  assets_dev`): the gate hall and its barrel pair, the Well up to the sky and its braziers on the slanted faces (a
  Floating Eye drawn as the MM6 beholder), the hall of hands (a Carnage Hand as its stand-in model, Plane Guardian),
  the crypt, the storeroom (a barrel on a crate), the forge's anvils by the lava, the scrap hall, the reading room and
  a trapdoor with Wizards (the mm6 sorcerer model), the great library's aisle from the west door, the Study of the Arm,
  Darzog's hall with the Baron (health bar "Baron Darzog") on his dais and the six clones down the rug, the study, the
  clone vats, the portrait hall, the roof's cloud stair, down the Well, over the lake. Every prop that moved stands
  against its wall; the doorways and aisles are clear.

**Defects found:**

1. **Crodo is invisible** in the Xeen world (`xshots2/01`, `02`: his cell shows the stool and the bowl, no Crodo):
   descriptor `Xeen Crodo` (11900) has no binding in `worlds/xeen/models/actors.yml`, and `tools/xeen/standin_bindings.py`
   covers families and bosses, not `characters`. For S (and A2's tool): copy MM7's `Mage A` binding (`mm7_m274.glb`,
   skin `m274_a`). The playtests pass (the actor is there, peaceful, hidden after his words).
2. No `m21.*` hooks (M21 an outline) and m21.yml's player-bit labels (above): for A3.
3. As XD-27's: the indoor validate/build read rows only from the engine tables (the `xroot` workaround); the
   studio's hostility check reads only hostile.txt; a cloud-stair status line cannot be read by the next scenario step
   (asserted as a pressure plate, then clicked).

**Not tested, and why:**

- The way out onto X2: X2 is not installed in the Xeen world (A5's); `playtest_b.yml` ends at the tower door's
  question. When X2 is in the world, restore `select_topic: OK`, `advance_runtime: {follow_map_move: true}`, `assert:
  {map: xeen_x2.odm}`, the party at (-15631, 3014) radius 160, z 700-900. The Skeleton Key 12100 is tested by X2's door
  (the map's own condition is on the neighbour, checked statically).
- The fall from the keep and the four other trapdoors (as before); the cloud stair's way to X9 (sealed).
- The arrival and Darzog windows are now seen headless (`present_dialogs`); hook text, when A3 writes it, is not.

## Exit onto X2 and merge point 3 (lane A8, 2026-11-20)

**Studio checks against assets_dev** (A1's merge point 3, `openyamm-studio/build-xeen/oymap`): `validate` L3 and L4
`--assets assets_dev` no issues; `build <L4> --assets assets_dev` gave byte for byte the build with `xroot` (blv,
scene, Lua, build.json), so the check root `output/studio_cal/xd12/xroot` is deleted (no script used it; build
commands now name `--assets assets_dev`). No hostility warning either way: the studio reads `relations.yml`.
**Relations:** the four rows that restated the world's file (constructs, wizards and Eyes `long` toward the party,
Crodo friendly) are dropped from `tools/dress.py` (L4 regenerated, `oymap fmt`, `oymap record --label "exit onto X2,
merge point 3"`, revision `04d6d1626a9cc76046861d22e090934a`); the build stays quiet without them. The Eyes-apart rows
stay (the world's file sets no such rule). The build's Lua lost the 15 `evt.SetMonsterRelation(..., 0, ...)` lines and
nothing else (`build_assets_dev.txt`: 55 rooms, 3,663 faces, 31 doors, 29 spawns, 60 events, 9 chests; the
Librarian's name warning only), so it was installed again (`oymap install --root assets_dev`: the map's four files;
the world's data_tables hashes unchanged). `audit --reach --solve` on the installed blv `--world xeen` (`audit_mp3.txt`,
`solve_mp3.txt`): as before (0 faces in one plane; 22/52 of 55 sectors; five `ride.no_switch`; solve 52 of 55 by
12230 and 110500; exit `xeen_x2.odm at -15631, 3014, 768`). `fmt --check` L1-L4 clean.

**The way out.** X2's door is unchanged in A5's rebase (DOORS.md; X2's event 96 "Darzog's Tower"). `playtest_b.yml`
now confirms the tower door's question: `select_topic OK`, `follow_map_move`, `assert: {map: xeen_x2.odm}`, the party
at **(-15631, 3014), z 769** (radius 160). No arrival change.

**The way in** (`playtest_way_in.yml`, new): on the island at the arrival, 200 in front of the door facing it: without
the Skeleton Key X2's door refuses ("Whoever holds the key to it is not on this island.") and the party stays on X2;
with 12100 granted it loads the tower at its start (2752, 0, 0) with the arrival window.

**Playtests 4 of 4** (`xfour.sh`, `build-xeen/game/openyamm --asset-root assets_dev --world xeen`, `--map
xeen_xd12.blv` except the way in; one game at a time, exact PIDs): `playtest.yml` 143 (`xfour_mp3_main.out`, logs
`xrun/four_135725/`), `playtest_b.yml` 101, `playtest_hostility.yml` 40, `playtest_way_in.yml` 23 (`xfour_mp3.out`,
logs `xrun/four_135617/`), each **4 of 4**.

**Not asserted: "Spells do not work here".** A `status()` check after `cast_spell` found no status line (4 of 4 runs
failed on it, then removed): the scenario's `cast_spell` returns the refusal in the cast's result and posts no status
line, and the line the player sees comes from opening the spellbook (`GameplayScreenRuntime::openSpellbookOverlay`),
which no scenario step does. `cast_spell ... expect: refused` stays. For A1: a scenario step that opens the spellbook,
or `cast_spell` posting its failure text, would let the playtest assert the line.

## Hooks and dressing, D-7 (2026-11-20)

Touch-up by `agent:xeen-a8-touchup` (lane A8). Map changes all in the generator (`output/studio_cal/xd12/tools/dress.py`,
`plan.py`; copies before the change `dress_before_d7.py`, `plan_before_d7.py`); the generator reproduced L4 byte for byte
before the change; `python3 emit.py L4`, `oymap fmt`, `oymap record --author agent:xeen-a8-touchup --label "m21 hooks,
first-arrival window, D-7 dressing"` (revision `775837591d1c92f86ecc94ac4bdadfe4`). Built to
`output/studio_cal/xd12/build_d7`, installed with `oymap install --root assets_dev` (the map's four files).

**A3's m21 hooks** (`data_tables/quest_hooks.yml`, `source/quests/m21.yml`, now `status: full`):

| Event | Now | Dropped from the map |
|---|---|---|
| `evt:arrive` (one-shot timer) | `condition: {not: {qbit: arrived_once}}`, then `XeenQuests.hook("m21.arrival")` and `{qbit: arrived_once}` | its own arrival message |
| `evt:darzog_dead` (death timer) | the shake, then `m21.darzog` (sets `darzog_slain` 110500, the window); `opens: [door:disc_grille]` kept | its qbit and message |
| `evt:crodo` (step into the cell) | `m21.crodo` (once-hook: `crodo_freed` 110501, 35,000 experience each, autonote 4121 with the vault word 'laboratory', Crodo's words), then `hide_actors: 40` | its message, qbit, experience and the event's own `once` (so a later step into the cell gets the hook's else text, "Crodo's stool, and the marks of his chain on the wall.") |

`python3 tools/xeen/quests.py --open` no longer lists any m21 hook on XD-12 as unwired. It now reports
`XD-12: built qbit arrived_once (110503) is in no quest file`. **For A3:** register `arrived_once` 110503 in m21.yml.
`m21.library` and `m21.cloud_stair` have no `call` (the map sets `library_door_opened` and reads `crodo_freed` itself,
as before).

**First arrival only.** The arrival window opened on every entry and paused the monsters until it was closed. Now it opens once ever:
qbit `arrived_once` **110503** (free in 110500-110599; project.yml `qbits`).

**Dressing (D-7).** `oymap audit <installed blv> --world xeen --assets assets_dev` before: **6 errors / 20 warnings**
(listed in the brief: rock_01/11/21/31, scrap_2, trap2_bones_2; 20 island trees). After: **0 / 0**. Moved (each marked
"D-7 (2026-11-20)" in `dress.py`):

- The island bands' walking lines run from each band's corner opening (its arm end, 3328-3840 out) along the keep's
  wall to the windows. So the trees toward the arm end stand further out toward the bank's edge: by their place along the
  arm, -640 → 3632, 384 and 1024 → 3680, 1664 and 2432 → 3712 (they were 3536). The three toward the other end stay. The
  second rock of each band went from 3600 to 3712. Nothing removed. No tree is kept as an exception.
- `scrap_2` (trash heap) (-2880, 2240) → (-3000, 1990), the scrap hall's south-west corner.
- `trap2_bones_2` (the skull by the reading room's hatch): the hatch lies where the lines between the room's doors,
  arch, windows and the hatch hole cross. No place at its edge is clear, so the skull lies 300 south of the hatch's middle at
  (1296, 2176), the nearest clear place. The two bones (radius 16, below the audit's size) stay at the edge.

No "Dressing exceptions" are needed.

**Checks** (files in `output/studio_cal/xd12/`): `validate` no issues; `fmt --check` clean; `build`: 55 rooms, 3,663
faces, 31 doors, 29 spawns, 60 events, 9 chests. It warns about the Librarian's name, as before. It also gives a new warning,
"nothing tells the player on arrival why he is here": the studio's arrival check skips any timer event with a `condition`
(`IndoorLowering.cpp`, the `|| event["condition"]` skip before the `.hook(` test). That is a studio defect, for A1. The same
warning shows on XD-06, XD-21 and XD-27. `audit --reach --solve` (`audit_d7.txt`): 0 faces in one plane, 22/52 of 55 sectors,
five `ride.no_switch` (the trapdoors), no dressing finding. `solve_d7.txt` is identical to `solve_mp3.txt` (the qbit
set inside the hook did not change the solve).

**Playtests** (edited: `playtest.yml` asserts `arrived_once` after the arrival window, Crodo's window with "The vault's
word is 'laboratory'", at least 35,000 experience for member 0 from Crodo (logged 35,000) and autonote 4121;
`playtest_b.yml` asserts the hook's arrival text "Darzog's Tower. The Skeleton Key turns" (it asserted the map's old
"DARZOG'S TOWER"). Run from assets_dev in the Xeen world, one game at a time
(`/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/f070ad2b-085f-4ea8-986a-1b63e2657a52/scratchpad/d7/play_once.sh`, a scratch script; logs beside it in `run/`): `playtest.yml` 146 of 146, `playtest_b.yml` 101 of 101,
`playtest_hostility.yml` 40 of 40, `playtest_way_in.yml` 23 of 23, **each 1 of 1 so far** (the orchestrator's
handover stopped the work before the 4 of 4).

**Still open, next steps:**

1. Run every playtest **4 of 4**: `output/studio_cal/xd12/xfour.sh` (N=4; it writes `xrun/four_<time>/`).
2. Add a re-entry check of the first-arrival window to `playtest_way_in.yml`. After the arrival window, `close`, `execute_event: {id:
   41}`, `select_topic OK`, `follow_map_move` to X2, `set_pose` 200 in front of the door again, `press_interact`,
   `follow_map_move`, `assert: {map: xeen_xd12.blv}`, `advance_runtime: {seconds: 3, present_dialogs: true}`,
   `assert: {dialog: {active: false}}`. Also a step into Crodo's cell a second time in `playtest.yml`, asserting the else
   text "marks of his chain" and no new experience.
3. Pictures of the moved trees, rocks, heap and skull (a tour with `tools/shots_x.py`-style shots from the windows
   over the island's arms, the scrap hall's south-west corner and the reading room's hatch); none taken yet.
4. For A3: `arrived_once` 110503 into m21.yml. For A1: the studio's arrival check should count a conditioned timer.

## Session 3 (2026-11-20): 4 of 4, re-entry, Crodo's empty cell, pictures

Lane A8. `oymap audit <stem> --world xeen --assets assets_dev` (studio merge point 7) on the installed map: no dressing finding. A3 has registered `arrived_once` 110503 in m21.yml. Next steps (1)-(3) of the D-7 section are done.

- **Re-entry step** in `playtest_way_in.yml`: the arrival window shows once ("Every spell you reach for dies before it
  is shaped") and sets 110503; the party leaves by the tower door (event 41, OK) to the island, comes back with the
  Skeleton Key, and after 3 seconds no window is open. 37 steps.
- **Crodo's cell a second time** in `playtest.yml`: out to the bedchamber and back into the cell, the hook's else text
  ("Crodo's stool, and the marks of his chain on the wall.") and no new experience for member 0. 151 steps.
- **4 of 4** from assets_dev (`xfour.sh`, logs `output/studio_cal/xd12/xrun/four_152552/`): `playtest.yml` 151,
  `playtest_b.yml` 101, `playtest_hostility.yml` 40, `playtest_way_in.yml` 37 steps, each 4 of 4.
- **Pictures** of the moved props (`/home/pjasicek/github/OpenYAMM/output/studio_cal/a8_s3/props/xd12_sheet.jpg`, tour `/home/pjasicek/github/OpenYAMM/output/studio_cal/a8_s3/props/xd12.yml`): the north band's trees
  stand off the keep's wall, with the walk along the wall clear; the reading room's skull lies south of the hatch, clear
  of the doors and the reading tables. The scrap hall's heap (retake `/home/pjasicek/github/OpenYAMM/output/studio_cal/a8_s3/props/xd12b_sheet.jpg`, shot 1 from the east
  wall) lies in the south-west corner against the wall, clear of the arch and the walk across the hall.

## Merge point 10 (2026-11-20, lane A8 session 5): direct falls (D-24)

- **Rebuilt** with `openyamm-studio/build-xeen/oymap` (merge point 10) and installed into assets_dev by temp file and
  rename (`output/studio_cal/a8_s5/rebuild.sh xd12`, `install_stage.py`; build `output/studio_cal/xd12/b_172201`).
  The blv and scene are byte for byte as before; only the Lua changed: the four `evt:fall_*` step events now call
  `evt.MoveToMap(..., "xeen_x2.odm", {direct = true})`, so a fall from the keep lands on the island with no "leave?"
  window (D-24 fixes the window that asked after the fall). The tower door keeps the `exit` preset and its window.
- **The fall's line goes first** (`tools/dress.py`, copy before `dress_before_mp10.py`): the event's `text` runs after
  its effects and would come after the move, so it is now an effect `{text: ...}` before `{leave: exit:lake_island}`.
  The status line still does not show on X2: a status line set by an event that then changes map is lost (scenario
  `status()` is empty after the move). For A1 (it applies to any event that says something and then leaves: XD-07's
  throw too). The playtest logs it and does not assert it.
- **`playtest_fall.yml`** (new, 15 steps): the arrival window closed, the party dropped in the air east of the keep
  (5200, 0, 1100, over `room:out_e`), lands on `xeen_x2.odm` at (-15631, 3014, 769) by the tower door, no dialog
  open, still none two seconds later.
- **4 of 4** from assets_dev (`xfour.sh`, now five tests; logs `output/studio_cal/xd12/xrun/four_172221/`,
  `four_mp10.out`): `playtest.yml` 151, `playtest_b.yml` 101, `playtest_hostility.yml` 40, `playtest_way_in.yml` 37,
  `playtest_fall.yml` 15 steps, each 4 of 4, exit 0.
- `oymap record --label "merge point 10: the fall line before the direct leave"` (revision 947a3313...).
- Merge point 11 (oymap 17:26:09): rebuilt; the four files are byte for byte the installed ones, nothing reinstalled; the 4-of-4 runs above were on the merge point 11 game (17:10:53).

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/xd12/tools/dress.py`, copy before the
change `dress_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated, `oymap fmt`,
`oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- The forge's two braziers (`brzier00`, chained) hang from its ceiling (640 clear; height 492), their tops 2 into it.
- The Well's four braziers stood on the floor under 4,000 of open shaft, with nothing to hang from: now four fires of
  logs (`dec04`, a floor fixture with its own light) in the same places by the rune circle. (The Well's design card in
  `design.py` still says braziers; L1-L3 untouched.)

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/xd12/audit_lights.txt`): lights
  errors/warnings before **6/0 (ceiling_on_floor)**, after **0/0**; no dressing finding. **Light exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh xd12` (build `output/studio_cal/xd12/b_192522`), baked
  (`output/studio_cal/a8_s5/bake.sh xd12 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_xd12.yml`
  (new: XD-08's values)), `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from
  assets_dev, each 4 of 4** (xfour.sh; record `output/studio_cal/xd12/lights_post2.out`): playtest 4/4 (151 steps);
  playtest_b 4/4 (101 steps); playtest_hostility 4/4 (40 steps); playtest_way_in 4/4 (37 steps); playtest_fall 4/4 (15
  steps).
- **Pictures** `output/studio_cal/xd12/shots/lights_mp14/` (sheet `lights_mp14_sheet_1.jpg`), looked at: the forge's
  braziers hang under the ceiling in its south corners; the Well's log fires stand on the floor by the rune circle.

## Double doors (merge point 15, A8 session 6, 2026-11-20)

A1's door check (oymap 20:03:53) found the School of Sorcery's carved door `hhm1d2` (the right wing) tiled 2-3 times
across the folding doors `door:library_stair` (384 wide), `door:study_nw` and `door:study_sw` (256). All three are hinged
pairs now (`SOS_DOOR` in `tools/dress.py`, copy before `dress_before_doors.py`): `pictures` and `back_pictures`
`hhm1d` | `hhm1d2` (hhm1d is the left wing: its handles meet the other's in the middle). Audit `--reach --solve`: no
error; the five `ride.no_switch` warnings as before; 52 of 55 sectors as before. Recorded, installed, baked; tests 4 of
4 from assets_dev (151, 101, 40, 37, 15; `output/studio_cal/xd12/doors_post.out`). Pictures
`output/studio_cal/xd12/shots/doors_mp15_sheet.jpg` (looked at: one barn-style double door, handles in the middle).

## Session 7 batch (texture fit, sounds; lane A8, 2026-11-20)

By `agent:xeen-a8-xd12`. Changed in the generator only (`output/studio_cal/xd12/tools/geo.py` and `dress.py`; copies
before the change `geo_before_s7.py`, `dress_before_s7.py`); the generator reproduced the snapshot
(`output/studio_cal/a8_s7/snap/xd12/`) byte for byte first. `python3 emit.py L4`, `oymap fmt`, `oymap record` (entries
12 and 13), `INSTALL=1 a8_s5/rebuild.sh xd12`, baked by `a8_s5/lights/post.sh`.

- **The cloud stair** (23 errors: 18 `feature_cut`, 5 `feature_repeated`): `xwcloudst` (a picture of a whole cloud
  stairway, meant once) lay on every step's risers and tops. The five steps are now made of cloud: X8's seamless tiles,
  `xccloud` (cloud tops, 256 x 256) on the treads and `xccloudsd` (cloud sides, 256 x 256) on the risers and ends, one
  declared size each, as X8 lays them. `xwcloudst` is dropped: the stair's head is open sky with no wall to hang it on.
  The roof's bake left the cloud a smoky grey, so the stair has **its own pale light** (`light:cloud_stair`, over the
  middle step at 288, radius 640, [235, 240, 255]; a map light, no fixture). **Face textures: 47** in the build (L cap
  70; `xwcloudst` out, `xccloud` and `xccloudsd` in).
- **The tower's bed**: AU's `xeen_amb_tower` (chimes and sparkle) as `sound:tower_bed`, one source on the Well's axis
  at z 1488 (halfway up the halls), inner radius 2560 (the galleries and side rooms of every floor), outer 5120 (the
  corner rooms are about 4,450 away at most), volume 0.35; one source, so nothing stacks. The roof hears it faintly
  under its wind. Not heard yet (the headless runner plays no ambient sound).
- **The works gate's winch**: `evt:works_winch` (the assembly hall's lever) plays `xeen_winch` at the gate it raises,
  `evt.PlaySoundName("xeen_winch", 1856, 640, 960)` (the portcullis's middle). No playtest step: a sound cannot be
  asserted; the lever's step in `playtest.yml` runs the event.

**Audit** (`oymap audit --reach --solve`, `output/studio_cal/xd12/s7_audit.txt`): before 23 errors, 9 warnings
(`a8_s7/audit0/xd12.txt`); after **0 errors, 9 warnings** (the four kept below, the five `ride.no_switch`); 52 of 55
sectors, 60 handlers, as before.

**Tests** from assets_dev, each **4 of 4** on the final build (`output/studio_cal/xd12/s7_post2.out`, logs
`xrun/four_214203`): playtest 151 steps, playtest_b 101, playtest_hostility 40, playtest_way_in 37, playtest_fall 15
(also 4 of 4 on the build before the stair's light, `s7_post.out`).

**Pictures** `output/studio_cal/xd12/shots/s7/` (HUD off; `tour_s7.yml`), looked at: `01` the stair from its foot, five
white cloud steps against the battlements and sky, no seam; `02` from the side, the risers' cloud sides and the treads'
tops; `03` from the top step down the stair and across the roof to the Well's rim; `04` a low close view of the top
steps (the treads nearest the light run nearly white); `05` the works gate (the portcullis, closed). `first_take/` is
the build before the stair's light (the steps a dark smoke grey).

### Texture fit exceptions

- `textures.family_switch` faces 1586 (`cnb`) / 1602 (`xwsky`): the north roof's parapet at its east end meets the
  32-wide gap to the open air, whose faces are sky faces: the game draws the open sky there, not `xwsky`, so it reads
  as the parapet's end against the sky.
- `textures.family_switch` faces 1761 / 1793: the same at the south roof's east parapet (its south-east corner).
- `textures.family_switch` faces 1762 / 1797: the same at the south roof's parapet by the sky stair (y -1792).
- `textures.family_switch` faces 1779 / 1792: the same at the south roof's west parapet (its south-west corner).
- `ride.no_switch` lifts `trap1` to `trap5`: the five trapdoors, lifts that drop whoever steps on them; their winch
  levers are on the walls below by design (no switch at the top; the word asked for is `lifts[].trap: true`, "Words
  needed" 3).
- Lead, after the batch (session 7): XD-12 rebuilt with oymap 21:33:52 (merge point 17) and A2's `place_mon` table
  (410 Chief Librarian): the "named only on the corpse" warning is gone, no one-size warning; no L4 change. Installed,
  re-baked, tests from assets_dev 4 of 4 again (`s7_post17.out`, 20 runs). Merge point 17 also shows the fall's status
  line on X2 (the status set before `evt.MoveToMap`).

## A8 session 17 (2026-11-21): the cloud stair to X9, the dais points

A3's segment 83 BLOCKER and note (relayed by the third orchestrator). Generator `output/studio_cal/xd12/tools/`
(`plan.py`, `dress.py`; before: `plan_before_s17a8.py`, `dress_before_s17a8.py`), `python3 emit.py L4`, `oymap fmt`;
the generator reproduced L4 before the change.

- **The cloud stair leads to X9.** `exit:clouds_of_xeen` is back as a neighbour, now `xeen_x9.blv` at X9's
  `entrance:xd12_roof` ((0, -17920, 320) facing 512), one way, with the plan's `entrance:cloud_stair`. The top step
  (event 9, `m21.cloud_stair` reads `crodo_freed` 110501; the hook has no call): before Crodo is freed the status line
  "The cloud gives under your foot like fog. Something holds it shut: Crodo would know what."; after it the map's own
  Yes/No "Climb the cloud stair into the sky?" (D-66's rule for a roof exit into a BLV; no message before it, D-65),
  and Yes leaves at once. The old "It will not bear you yet." line is gone. The sections above that call the stair
  sealed are its history.
- **The Baron's dais** (1216-1664 x 2176-2816, 64 high, no step) is unchanged: `playtest.yml` no longer walks over it
  but round it by the 256 strip south of it: (1600, 2048), then (1744, 2144) in the gap by the bedchamber door (each
  asserted at 2304 within 8), and back the same way to (1500, 2048).
- `playtest.yml`'s roof: walking onto the top step opens the question; No keeps the party on the roof; a click and Yes
  moves to X9, asserted at (0, -17920) within 192, facing 512.

## Merge point 30 panels (A8 session 20, 2026-11-21)

Both flagged panels moved in `tools/dress.py` (before: `output/studio_cal/a8_s20/xd12_dress_before_s20.py`). The
bedchamber's tapestry `tap10` from the east wall, where window 29 cut its upper half, to the south wall (512 along, x
2432-2560). The portrait hall's third portrait stood wholly inside the state gallery's doorway (`open:state_portraits`,
along 1152-1664 of the north wall) and was never drawn: the six portraits now hang two east of that doorway (288, 736)
and four west of it (1936, 2352, 2768, 3184). The wall torches re-space round the panels by themselves (3 on that wall,
the nearest 144 from the doorway's jamb). Rebuilt with oymap 09:24, installed and baked; audit 0 errors / 5
`ride.no_switch` (as before).

## Session 21 (A8): AU's sounds

The room-filling beds `sound:tower_bed` take `pan: false` (D-48); the point sounds keep panning. Through the generator; installed 10:05, rebaked, tests 4 of 4 from assets_dev, audit 0 errors (lane log `A8.md`, "21st session").

## Session 23 (A8): the tapestry re-shot

Review row 39: session 20's `bed_tapestry` pose (2496, 2700) stood outside the L-shaped bedchamber, inside the wall.
Re-shot from inside the room (no map change): `output/studio_cal/a8_s23/shots/xd12_reshoot_sheet_1.jpg` (the tapestry
`tap10` whole on the south wall beside the sconce, from the window side, the bed and the east end).

## Session 24 (A8): merge point 35 tests

Rebuilt under oymap 12:46:47 for A1's room step tops (`evt:crodo`, `evt:darzog_hall_cue` on the rugs, `evt:roof`; only
the .blv changed), installed 17:15, baked, every test 4 of 4 from assets_dev on merge point 35; audit 0 / 5 (as
before).

## Session 25 (A8): a quiet arrival

A3 (session 32): in 12 of 19 probes of main-chain segment 37 a member was Paralyzed within 1.5 s of arriving by the
tower door. The cause was the Well's eye group (`spawn:well`, slot 3 Floating Eye 11570, at (-384, -384, 0)): the
arrival (2752, 0) faces west through the gate hall's arch (768 wide) and the cloister's arch into the Well (512 wide),
one straight line, and the eyes at the Well's foot (2,560 wander for a Med mover) shot along it from about 3,150. A
level-20 party standing at the arrival was Paralyzed after 2 s and dead or unconscious within 10 s
(`output/studio_cal/a8_s25/probe/before/`). With the group gone it was untouched for 40 s, 3 of 3.

- **Fix** (`tools/dress.py`, `tools/design.py`; before: `output/studio_cal/a8_s25/before/`): the group is now
  `spawn:cistern_w` at the cistern's west end (-1152, -2496), out of sight of the arrival; the cistern has the gate
  floor's two eye groups (plan.yml: the Well's population empty, the cistern's 2). Monster count unchanged (29 spawn
  points). The Well keeps the eyes that drift in from the floors above (works, library, roof).
- **Test:** `playtest_hostility.yml` opens with the quiet arrival (as XD-18's): the window closed, 15 s at the door
  not immortal, the party unchanged and still at (2752, 0).
- Probes after the install: the level-20 probe 3 of 3 untouched for 40 s (`probe/installed/`); A3's
  `stepcond_37_darzogs_door.yml` from assets_dev 3 of 3 passed with no Paralyzed member (`a8_s25/seg37/`; checkpoint 35
  now loads with two members DiseaseMedium, from before this map).
- Installed (build `output/studio_cal/xd12/b_183515`; against session 24's build only the .blv and the studio file differ; scene and map Lua are byte-identical),
  baked, `stale_bakes` 0; **every test 4 of 4 from assets_dev** (playtest 165, playtest_b 101, hostility 46, way_in 37,
  fall 15; `output/studio_cal/xd12/xrun/four_184107`); audit 0 errors / 5 `ride.no_switch` (as before). Recorded
  (`oymap record`, revision 12e644a3115cae0b252c965d527732cf).


## Session 26 (A8): status lines, the cloud stair's window, door pictures, the cistern's ladders, book tops

Edited in `tools/dress.py` (before: `output/studio_cal/a8_s26/before/xd12/`); `emit.py L4` reproduced the L4 first.
- **F13:** the six study books (`evt:book_accuracy`, `_endurance`, `_intellect`, `_might`, `_personality`, `_speed`;
  +5 once per character) showed the gain in a window (`message:`); now the studio's `text:` effect, a status line
  (`evt.StatusText(text, 6)`).
- **F16:** event 9 (`evt:cloud_stair`, the top step to X9) asked the map's own "Climb the cloud stair into the sky?"
  Yes/No before moving; now the `exit: exit:clouds_of_xeen` effect, the standard entrance window (OK moves, Close
  stays), under the same condition (crodo_freed 110501; before it the cloud's status line).
- **Door leaves (F12):** the nine plank doors (guardroom, storeroom, crypt, cells, smelter, quarters, Darzog's doors,
  bedchamber, study; events 19-23, 57-60) showed Gloaming's plank strip `7trimd` tiled over a folding leaf. They are now
  hinged pairs with the tower's own braced plank door pictures, the wing pair `hhm1d | hhm1d2` (twins, as the School of
  Sorcery's doors), each fitted to its leaf (`PLANK_DOOR`): 128 by 320 leaves, Darzog's doors 256 by 384. Each pair's
  second leaf is a new door (36-43); event numbers unchanged.
- **F14:** the cistern's water (2,048 by 512, 160 down) was a drop pocket: two iron-rung ladders (`ladder:cistern_n`
  at (-512, -2248) and `ladder:cistern_s` at (512, -2744), `bemv`, as XD-21's) climb onto the walk. check_drops 0.
- **F12d:** the six lecterns showed the bookcase picture `7t1books` on top; now `{texture: xnpbook, size: [128, 128],
  fit: true}` (`BOOK_TOP`; the deferred list named accuracy and personality, the other four are the same lectern).
- Tests: `playtest.yml` and `playtest_b.yml` check the books on the status line; `playtest.yml` takes the cloud stair's
  window (Close stays on the roof, then OK to X9) and Darzog's death as A3's `m21.darzog` status line ("Baron Darzog
  falls", was a window with older text).
- Installed 00:49 and baked; audit 0 errors / 5 warnings (`ride.no_switch`, as before), check_exits 0, check_drops 0;
  tests from assets_dev 4 of 4 (20 of 20: playtest, b, fall, hostility with the quiet arrival, way_in;
  `output/studio_cal/a8_s26/run/xd12/t005215`). Pictures (both door pairs, the cistern ladder):
  `output/studio_cal/a8_s26/sub1/shots/xd12/`.

## Session 29 (A8): MP42 rebuild

Rebuilt on oymap merge point 42 (2026-11-22 ~02:33). emit.py L4 reproduced the L4 unchanged; the build's chests were
already the 7gt002 kind. Seen in the chest pictures: the quarters' chest stood inside the west stair's doorway (x
-2240..-1984, 80 in from the north wall), so dress.py moves it to (-1984, -2880), a foot locker by the SE bed against
the east wall (two quarters wall torches moved with it, by the torch placer). Installed, baked; audit 0 errors / 5
warnings (ride.no_switch, as before), check_exits 0. playtest_way_in: X2's tower door now shows the standard entrance
window (X2 rebuilt 02:02, F16), so both entries from X2 answer it (OK) before the map move; the test failed at step
20 without that, not from this rebuild. Tests 4 of 4 (20 of 20: output/studio_cal/a8_s26/run/xd12/t023625 and
t023655). check_drops now reaches 350 floors (A7's stair fix; was 37) and lists two pockets: the forge's lava channel
(z 672, 96 down, no step or ladder out: an F14 site, open) and the island ground round the tower (left by exits
26-29, by design). Chest pictures: output/studio_cal/a8_s29/shots/xd12_chests.jpg and xd12_chests_rest.jpg
(quarters_new, quarters_door: the doorway now clear).

- 2026-11-22 fixup (fourth orchestrator, for A8; F14): the forge's lava channel (96 down) and the smelting pit (128
  down, which `check_drops.py` had missed: its rim's edge "landed" through the solid floor on the gate floor below; the
  check now refuses a drop through solid) got iron rungs as the cistern's: `ladder:forge_lava_w` (-1344, 2760) and
  `ladder:forge_lava_e` (1024, 2760) facing s, exits 104 south on the forge floor; `ladder:smelter_pit` (2496, 2736)
  facing n, exit (2496, 2848) (`dress.py`, backup `dress_before_fixup.py`). Installed 02:58, baked 02:59; audit 0
  errors, 7 warnings (5 `ride.no_switch` as before, 2 `geometry.coplanar`: the pit ladder's rail feet, 64 square units
  each, in the plane of face 818 under the lava); check_exits 0; check_drops: only the island ground (exits 26-29, by
  design); MAW reserve and check 0; tests 20/20 from assets_dev (`output/xeen_fixups/xd12/c025754`).

## Session 30 (A8): the disc and its grille in explicit states

A1 38th found that events 15, 16, 17 (and 56) moved the disc (mover 32) and its grille (door 13) as `Trigger` pairs,
so their phase hung on evt:darzog_dead having opened the grille first. A map reset (a rebuilt map resets the saved map
on entry; darzog_slain stays) moved them in the wrong phase: the grille shut in front of the party at the top of the
disc. Now (`dress.py`, backup `output/studio_cal/a8_s30/before/xd12/dress.py`): a map variable `disc_down` (6; 0 = up,
the start, so it resets with the doors) says where the disc is; disc up = grille open, disc down = grille shut, always
set explicitly. evt:disc (15) and evt:disc_call_bottom (16) are two-way by `disc_down` (the bottom button calls the
disc down and, from the disc, rides it up, as segment 83 and playtest.yml use it); evt:disc_call_top (17) only brings
it up (`closes: mover:disc`, `opens: door:disc_grille`); evt:disc_ride_top (56) only sends it down. New evt:disc_restore
(62, on every load) sets the disc and grille to what `disc_down` says (no-ops in a kept state): a reset map (disc up,
grille shut, darzog_slain kept) opens the grille, as DD-03's stage doors; a save from before this change (map state
kept: event scripts are not in the layout identity) with the disc down and the new variable 0 brings the disc up to its
rest (the explicit migration SAVED_MAP_STATE_IDENTITY.md asks for; the first version without it failed segment 83,
whose checkpoint has the disc down).
evt:darzog_dead waits while the disc is down (only possible after a reset, with a respawned Darzog). New
`playtest_reset.yml`: darzog_slain set on a fresh map, a load opens the grille, every button in turn, a load with the
disc down keeps the grille shut; it fails on the old map (`the load did not open the grille`). Installed 05:18 (only
.studio.yml and .lua changed: no bake; `stale_bakes --check` 0); audit 0 errors / 7 warnings (as before); check_exits
0; drops only the island ground; MAW reserve and check 0; key_npcs 0; tests 12/12 (6 playtests x 2,
`output/studio_cal/a8_s26/run/xd12/c051750`).
Main segments `run.py 81 83` and `run.py --reload 81 83` pass on it (A8 30th, `output/studio_cal/a8_s30/`).

## 2026-11-25, xeen-fb4-dungeon6: the sky stair's battlement ends, the library stair's marker

- `sky.low` faces 2056/2057 were the east battlement's reveals (in the keep wall's 256 thickness) drawn as sky down to
  the 256-deep sill at 3,184: a party that jumps onto the sill saw the below-horizon fog at its feet. `shell.py`
  `open:battlement_e`: the opening is 288 high over its sill with stone reveals and a sky lintel (a full-height stone
  reveal stood up as two bare posts 1,000 into the sky; captures `output/xeen_fb/p4_dungeon6/xd12/sheet.png` before,
  `sheet2.png` after). `check_parapet_gaps.py` 2 -> 0.
- D-132: `spawn:library_stair` (-2496, 0) -> (-2496, -512) (`dress.py`): its shooters had a thin shot over the
  library flight's edge at 1,952-1,984 (`check_ledge_shots.py` 2 errors, on HEAD's map too) -> 0.
- Audit 0 errors (9 warnings as before), drops only the island ground, 6/6 playtests; installed, baked, MAW reserve.

## 2026-11-26, xeen-fb5-dungeon-f76 (F76: p1-p4)

- p1/p2 "tree clipping through the wall": the island's great trees (7tree01, 7tree16: 1,280 high, crowns about 690
  as drawn) stood 208-384 out from the keep's wall and reached 40-1,050 through it into the gate floor's and the
  works' rooms. `dress.py`: only the small trees (6tree03/07/09/17), each its drawn crown (deco_footprint.py, grown by
  the height jitter) + 32 clear of the wall (`tree_clear`). `check_clipping.py deco.through` 12 -> 0.
- p3 "something wrong": the sky stair's risers and gallery sides took the room's wall (the sky): `geo.stair_hall`
  `solid=` (CNB for the sky stair). `sky.solid` 102 -> 0.
- p4 "something strange": the sky stair's west wall by roof_n and roof_s (768 each) stood as two low walls of no
  thickness between the gallery and the roof at one level. `shell.py`: `open:skystair_roof_nw` / `_sw` (full),
  `open:skystair_roof_e` 2,016 wide, two posts of keep stone (64 x 62, rise 160) on roof_e's side over the 16 of wall
  left at y +-1,024. `piece.free` 6 -> 2: the east battlement's stone reveals (2 end posts) kept
  (`tools/xeen/check_clipping.yml`, the sky-reveal trade-off of 2026-11-25).
- `check_body_fit.py`: Crodo (11900) in his secret cell (128-wide door) is penned on purpose: the prisoner stays there.
- Installed and baked 2026-11-26; audit 0 errors / 9 warnings (as before); 6/6 playtests from the stage; drops only
  the island ground; floor_cross 6 lids as before. Captures `output/xeen_fb/p5_dungeon/f76/after/xd12b/`.
