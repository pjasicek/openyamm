# Xeen: the next five maps (started 2026-11-15, the Map Studio lead)

The user (2026-11-15): "pick 5 which you want and do them, with this agentic flow with the studio". The lead picked
X2 and its four dungeons, so the hub joins Vertigo Meadows by the river road and its dungeons are whole:

| Map | Code | Kind | File | map_stats | qbits | items | Party (MAPS §0) |
|---|---|---|---|---|---|---|---|
| Rivercity and Lake Darzog | X2 | outdoor hub | `xeen_x2.odm` | 9136 | 110200-110299 | 12100-12149 | 7 → 11 |
| Robbers' Den | XD-21 | S, under the bridge | `xeen_xd21.blv` | 9137 | 110300-110339 | 12150-12169 | 9 → 11 |
| Ogre Lair | XD-27 | S | `xeen_xd27.blv` | 9138 | 110340-110379 | 12170-12189 | 10 → 12 |
| Temple of Yak | XD-06 | M, the fairy woods' south end | `xeen_xd06.blv` | 9139 | 110400-110469 | 12190-12229 | 14 → 16 |
| Darzog's Tower | XD-12 | L, the lake island | `xeen_xd12.blv` | 9140 | 110500-110599 | 12230-12299 | 30 → 48, Darzog 55 |

Why these: X2 is the next map of the progression (MAPS §0) and the hub every later Cloudside map joins; its four
dungeons are the only ones it holds, so X2 plays complete. Darzog's Tower is Cloudside's first L set piece and the
lake island's point; it comes late in the story (M21) but stands on X2.

## For every map agent

Read first: `devdocs/xeen/README.md` (the decisions of 2026-11-13 and 2026-11-14), `HANDOFF.md` section 0,
`WORLD_DESIGN.md` (sections on towns, services, visual identity, Fly), `MAPS.md` (section 0's row, the map's sheet or
dungeon row, "Original lines by dungeon", layout sketches), `QUESTS.md` (the quests the map carries),
`MONSTERS_AND_ITEMS.md` (density, treasure, the MM7 stand-in rule), `CHANGES_FOR_BUILT_MAPS.md` (what the built maps
got wrong: do it right from the start), `devdocs/map_studio/HANDOFF_LEAD.md` sections 2 and 5 (the user's
preferences and the rules), `openyamm-studio/README.md`, and the procedure for the kind:
`devdocs/map_studio/REBUILD_PROCEDURE.md` (indoor) or `OUTDOOR_REBUILD_PROCEDURE.md` and `TOWN_FEEL.md` (outdoor).

Models to follow: the dungeons `devdocs/xeen/briefs/xd01`-`xd05` (L1 to L4, each L4's NOTES.md) with their work
folders `output/studio_cal/xd0N/`; the outdoor map `devdocs/xeen/briefs/x1/L4` (NOTES.md) with
`output/studio_cal/x1/tools/` (gen.py, town.py, dress.py, gen_walk.py, gen_tour.py) and `output/studio_cal/x1/v.sh`.

The route: briefs `devdocs/xeen/briefs/<key>/L1`, `L2`, `L3` (plan, then rooms or sketch; each level a complete,
valid project folder; `ids.lock.yml` only in L4), then `L4` (objects, wiring, atmosphere, playtest, NOTES.md). Work
files and generator scripts in `output/studio_cal/<key>/`. Keys: `x2`, `xd21`, `xd27`, `xd06`, `xd12`.

Rules of the design:
- No riddles the game does not answer (README); combat, mechanisms and loot, MM6-MM8 style; one texture family per
  area; short original MM4/MM5 lines may be quoted.
- Size and counts by MAPS: S at most 15 sectors and 20 M units², 15-30 monsters; M 20-45 sectors, 45-75 monsters;
  L 50-75 sectors, about 70-80 monsters plus the boss; monster levels, groups and treasure level from section 0.
- MM7's world stands in (`world: mm7`), as for X1 and XD-01 to XD-05: Xeen families map to MM7 monsters and house
  rows as those maps did (see their NOTES.md). Music by number (E10).
- Measure against shipped maps of the same class (calibration metrics, `oymap compare` where it applies, the town
  feel and building shots for X2); never invent a number the shipped maps can give.

Links between the maps: X2 owns the outdoor doors. The X2 agent writes, early, each dungeon door's position and its
outside arrival point into `devdocs/xeen/briefs/x2/L4/project.yml` `neighbours` (`door:xd21`, `door:xd27`,
`door:xd06`, `door:xd12`) and the matching note in `devdocs/xeen/briefs/x2/DOORS.md`. A dungeon agent points its exits
at `xeen_x2.odm` with those arrivals; until they exist it uses a placeholder arrival and says so in NOTES.md (the lead
links them at the end). X2 also takes over the Temple of Yak from X1: the X2 agent changes X1's project only to drop
X1's `door:xd06` and point X1's west road at X2 (and nothing else in X1), then rebuilds X1 and runs X1's playtest.

Tools: use `openyamm-studio/build/oymap` (the lead's merged build; it may be replaced by a newer merge while you work,
always backward compatible). Never build the studio and never edit `openyamm-studio/` (six S8 agents are changing
it); a word the studio lacks goes into NOTES.md under "Words needed", with the workaround used. The game is
`build/game/openyamm` (never rebuild it). Install into your own scratch mount (`oymap install <L4> --build <build>
--mount output/studio_cal/<key>/mount --assets output/studio_play/xeen_root`) and play with
`SDL_AUDIODRIVER=dummy ./build/game/openyamm --asset-root "$PWD/output/studio_play/xeen_root" --extra-mount
"$PWD/output/studio_cal/<key>/mount" --world mm7 --user-data <scratch> --headless-run-scenario <abs playtest.yml>`.
Never write into `assets_dev` or `output/studio_play/xeen_root` (the lead installs there). Screenshots: AGENTS.md
"Native Game Visual Checks" (`./tools/run_game.sh --isolated <unique> ... --assets <xeen_root> --extra-mount <mount>`,
tours for many poses); look at them yourself before you call a map done.

Done when: the L4 builds clean (validate, build, audit, solve: every key and lever reachable, no dead handlers);
the playtest walks start to goal through every mechanism, 4 of 4 runs for a dungeon, 2 of 2 for an outdoor map;
the counts and sizes are inside the bands; the pictures are looked at; NOTES.md says what was built, the
measurements, the words needed, and what the user should look at when playing.

General rules: never git add/commit/stash/restore/reset; no Vulkan; `rm` only with literal paths after `ls`, as its
own command; wait on exact PIDs, never `pgrep -f`; at most two game processes at once per agent; no game or studio
code changes; never copy OpenEnroth or mm_mapview2 code. Do not edit `devdocs/map_studio/` records or AGENTS.md;
do update this world's `MAPS.md` rows for your map only if a measured fact proves them wrong (with a correction note).
Your final message is your report (you cannot write report files).

## Record

(The lead adds each map's result here.)

### XD-21 Robbers' Den (agent done 2026-11-16 ~01:40; not installed in xeen_root yet)

11 rooms and sectors, 19.7 M units² (MM7 S: 6/8/18 sectors, 6/12/19 M units²), 28 monsters (MM7 Thief, Fighter Leather
and Master Thief stand-ins, levels 12-18), 3 trapped chests, 10 door records, 1 loop, 9 secret faces. Inside the
bridge's south abutment: the quay cellar with a culvert grate (looks a dead end), a secret block found by a footprints
step text or Perception, a tripwire crawl, the dicing and bunk rooms (a loose brick purse), the undercroft set piece (a
mill race 512 wide between grates, the robbers' plank bridge run out by a winch lever, giving the loop), the sluice
catwalk, the fence's store (Ring of Keys or Disarm Traps 3), dart slabs stopped by a catch lever the boss's ledger
names, the iron vault door (Ring of Keys) and the tiara (stand-in MM7 Noble Crown 900) in the level-3 strongbox. Q-C3
from the arrival message; T1-E rewarded by Roxanne at Castle Burlock (XD-07, not built). Textures: MM7 Erathian Sewers
family. Playtest 4/4 (99 steps) ending on X2's quay through a combined mount (`output/studio_cal/xd21/tools/exitmount.py`).
Generators `output/studio_cal/xd21/tools/{plan,gen}.py`, rebuilt by `v.sh`. Words needed: the studio refuses sounds
from `engine/audio` that the game plays (worked round with a private hard-link root `output/studio_cal/xd21/root`);
sunken areas cannot touch room walls; wall panels cannot start below the floor; hinged doors cannot tile a picture;
no bolster row from install. Game: a placed monster's own hit points ignored and its name shown only on the corpse
(the boss is a plain Master Thief until a monster_data row exists); no transition trace for event exits. For the user to
look at: whether the secret block is findable without Perception, the winch route, the darts' fairness, the weak boss,
the lighting.

### XD-27 Ogre Lair (agent done 2026-11-16 ~02:30; not installed in xeen_root yet)

13 rooms and sectors, 19.5 M units² (MM8's Dire Wolf Den 14/14.7, Ancient Troll Home 12/17.7, Cyclops Larder 16/19.6);
monsters 23-28 over nine boots (MM6 Ogre 15 and Ogre Raider 20, MM8 Dire Wolf 14 and Ogre Mage Apprentice 20; the
Ogre Chieftain with the larder key and three throwers placed on the ledge); 4 chests (the larder hoard level 3). Set
piece designed (MAPS had none): the ogres' boulder works (quarry, plank chute with a boulder trap, the heap on a timber
rack at the throwing ledge open over the river gorge; clicking the rack dumps it; jumping the parapet drops the party in
the river, washed out at the mouth). The log gate barred from inside (its message points to the midden crack; lifting
the bar makes the loop). Q-C23: Nystor's arrival quote; the source's "You have found an Ogre lair. Destroy?" at the
Chieftain's seat sets `ogre_lair_destroyed` 110340. One texture family (the Dire Wolf Den's rock and timber). Playtests
`playtest.yml` (91 steps, out onto X2) and `playtest_fall.yml` (33) 4/4 each. Generators `output/studio_cal/xd27/tools/
{gen,gen_objects}.py`. Exit: X2's provisional arrival (-20480, 17152, 1152) from DOORS.md; update when X2 is final.
Words needed: a boulder rolling through rooms, decorations riding a mover, a sky backdrop out of a cave, a message after
an in-map teleport, living names for placed monsters, a bolster row (the lead adds `LowerToEqual` for 9138), engine
sounds; tool defects: `fit: true` tiles an exit picture 5x5, a wall's surface does not override the room's bands,
`validate`/`build` take no `--mount`. Weak spots: the gorge view box shows its corners and reuses XD-05's meadow picture;
the heap reads as stone blocks; a plain sail.

### XD-06 Temple of Yak (agent done 2026-11-16 ~03:10 after one lead review pass; not installed in xeen_root yet)

25 rooms and sectors, 50.4 M units² (M band; MM7 d04 Temple of Baa 31 sectors, 33 M units²), three loops: the temple
above (porch, narthex, the pillared Nave of Yak with the idol, two chapels, dormitory with a hidden cell, refectory,
library, vestry, treasury) and the undercroft 768 below (crypt, ossuary, the Yak Pool between two banks, lich crypt,
the octagonal sanctum, reliquary, the Master's cell and his stair back to the vestry). Textures: MM7 d04 (temple) and
Barrow I (crypts). Set piece: the treasury gate's two timber bars sunk by two MM7 push buttons (west chapel, library),
each pressed button's plaque turns dark and each press says so; the causeway of three sunken blocks worked by three
buttons at the pool's edge (1: blocks 1+2, 2: 2+3, 3: 3; answer 1 and 3; every state undoable); the pool that sickens
(teal bubbling water, green pulse, bones, a stench line; wading diseases the party; the Yak Pool basin +2 Endurance
once per character, disease every time); the Elixir under the reliquary slab that rises when the Yak Master dies.
Monsters about 50 (MM7 Cleric of the Moon, Skeleton Lord, Lich, Necromancer; the Yak Master a Speaker for the Dead 35,
680 hp). M10: Mirabeth's Yak Stone opens X2's door (qbit 110101); six Megacredits (stand-in 1438) and the Elixir (1431).
Playtests `playtest.yml` (121 steps) and `playtest_exit.yml` (onto X2 at -1024, -17584, 930) 4/4 each. The lead's review
(levers unseen, bars unreadable, red light everywhere, bare Master's quarters) led to MM7 push buttons, iron-banded
bars, orange `torch01` light with red only in the nave and sanctum, and a furnished cell and stair (measured on d04).
Words needed: boss rows and live names, a bolster row, engine sounds, folding doors with scaled pictures, a lever
backplate, more than one extra mount; tool faults: the tour's `actor kill` and an `actor_visible` check on the boss.

### X2 Rivercity and Lake Darzog (agent done 2026-11-16 ~03:40; not installed in xeen_root yet)

Rivercity across the Great River on stone quays (640) under two terraced halves (1024), a level four-arch bridge, jogged
streets, promenades and two squares, one timber-and-grey style; 13 services on MM7 house rows (Rivercity Smithing 10,
Armoury 49, Witch's Cauldron 86, The Bubbling Flask 118, the bank 287, Bull's Tavern 241, Street Fightin' 1572, Pray N
Pay 312, guilds of Body 165, Mind 159, Spirit 153, Royal Steeds 462, Nystor's Dock 486), 30 enterable residences on
Erathia's rows 910-945 (the skill row: Arnold's Gym 945, Martial Training 923, Lindon's Temps 929), 18 townsfolk, 8
guards. Lake Darzog with the tower on its wooded island (Medin's jetty, a boat after the dragons), ogre country with the
north river's gorge, farmland with ranger camps and the Shrine of Electricity, the fairy woods (Danulf's ring, Tito's
chapel, the Sage's Fountain) darkening into a bog with the Temple of Yak; the south rim (900 cliff, Ligono). About 45
POIs, 6 chests; about 136 hostiles in 6 areas (Will o' Wisps for sprites, Archers/Bowmen for rangers, Ogre Raiders at
the crossings, three Young Dragons 60 over the lake). Town feel 0 of 59 figures outside the shipped ranges. Walk 2/2
(407 steps: services, the bridge, all four dungeons, the X1 round trip, Nystor's boat to X1). X1: `door:xd06` removed,
`edge:west` to X2; X1's walk 4/4. DOORS.md holds the final doors (all moved after the provisional values; XD-21, XD-06
and XD-27 sent back to relink). Studio defects found: east-west travel inverted (confirmed by the lead in
`OutdoorInstall.cpp` against `MapStats.cpp`; S8g fixes it and undoes the workaround), `install --mount` copying tables
from the asset root, no doorway `floor`, models cannot be turned, `ruin` z-fighting, the `grant_item` setup shortcut
(game). Weak: Bridge Square an empty dirt plaza; the town grass-heavy from above.

**Compact town and the land to the edge (2026-11-16, after the user's play: "the city way way too much stretched ...
check erathia or top left region of alvar"; "the trees suddenly are 'cut off' when the party map bounds end").**
Measured first: `openyamm-studio/calibration/town_feel.py` gained twelve density figures (new lines only; ranges from
the thirteen shipped towns): buildings per 100 cells of footprint, built share, wall-to-wall and middle-to-middle gaps,
extent per building, street width house to house, the largest open circle (the square), farthest service, service
pair median, core radius. Old X2 was dense house to house (gap 384, Steadwick 398) but spread: services 10,504 apart
(median of pairs; shipped 2,909-8,789; Steadwick 6,595, Alvar 4,574), core radius 7,174 (2,626-6,552), built share
0.20 (0.21-0.37), an empty 11-cell river band between the halves. `tools/gen.py` now: the north half 4 cells nearer
(the river between the quays narrowed to water nodes 51-55, the north terrace edge 46.5 to 48.5), 49 town houses in
rows half a cell apart along a main street 1.5 cells between house fronts (jogging at its two lanes), the guild row
and the skill row on the south bank's riverside row, Bridge Square paved (a 16-high court of Steadwick's plaza stone)
with a tiered fountain, the mirror, three stalls, the bank, alchemist and tavern round it, four warehouses on the south
quay; 51 town plots (61), the 13 services, 30 residences, the bridge (four arches, now 9.5 cells), the quays, the
dock at the east end, the edges and their starts kept. Town feel 0 of 71 out (service pairs 8,658, core 6,242, 9.3
buildings per 100 cells, gap 368, street 928). The dungeon doors did not move (DOORS.md stands; no exit to relink).
The scatter stopped at the party's square: 950 decorations, none past 23,008. Now 323 trees and rocks stand on the
rim's ridges to the map's edge (nine bands, the road valleys and the north river's gorge left open), and the west and
east ridges end in a 1,100 shelf before the world rim instead of a 2,700 cut. Walk 2/2. After the lead's review the
south too: heath knolls along the rim, heath west and east of the dark end, trees and shrubs along the whole cliff
lip, sea stacks below (the water stays the stars); and the hostility pass's X2 patch (Archers 202-204 hostile to the
party) applied by hand. Built with the lead's oymap (merge 40), no hostility warning; walk 2/2 and
`playtest_hostility.yml` 2/2 from the scratch root with the current X1. Details: `x2/L4/NOTES.md`
"Compact town" and `output/studio_cal/x2/town2/`.

### XD-12 Darzog's Tower (agent done 2026-11-16 ~04:20 after one lead review pass; not installed in xeen_root yet)

A square keep 6,144 across round the Well (an octagonal shaft open to the sky, Darzog's lightning up its middle): the
gate floor (0), the works (768: forge with a lava channel, the works-gate winch), the library (1536), Darzog's floor
(2304: his hall, study, bedchamber, Crodo's secret cell behind the portrait, clone vats) and the battlemented roof (3072)
with the cloud stair; stair halls alternate west and east. 55 sectors (52 reached), 150.5 M units² walked (the lake band
round the keep is backdrop, never walked; the studio has no backdrop room). Against Castle Gloaming (48 sectors, 76 M)
and eight more shipped castles in NOTES. About 80 monsters (Brass and Gold Golems, Wizards, Floating Eyes and Gazers:
Clanker's Laboratory's and Castle Lambent's families); Darzog and six clones as Archmages (Darzog's 1,200 hp in the scene,
400 in the game: boss row needed). Treasure level 4, the hoard 5; six study books (+5 each, once per character). Five
trapdoors drop 768 into the works (the tell after the lead's review: a hatch sagging 32 inside a dark broken rim with a
victim's bones; the apprentice's note "MIND THE CRACKED FLAGS" read first; a winch below raises each). M21: the key, the
fight among the clones, the portrait and Crodo's cell (the Roland reveal there only; qbits 110500-110501). Roof after the
review: parapet 64, merlons as blocks every 384, a balcony over the lake, a pier over the Well. No-magic: the game supports
it, the studio cannot write it (S8g adds a word); for now the hand-written overlay
`output/studio_cal/xd12/rules/xeen_xd12_rules.scene.yml` must be installed beside the map; the game's refusal says "You
can't do that while underwater" (game text). Playtests `playtest.yml` 124 and `playtest_b.yml` 98 steps, 4/4 each; exit
`exit:lake_island` to X2 (-15631, 3014, 768) facing east, played; `exit:clouds_of_xeen` stands in with MM7's Celeste
until X9 exists. Pictures `output/studio_cal/xd12/shots6/` (sheets `sheet_k1-3.jpg`).

### Installed (2026-11-16 02:44, the lead; `output/studio_lead/xeen_install/`)

X1 (with X2's change and S8e's falls), X2, XD-21, XD-27, XD-06 and XD-12 built with the merged studio (merge 38/39)
against `output/studio_play/xeen_root` and installed there with `oymap install --root` (writes beside and renames: the
hard-link root is safe), X1's and X2's terrain materials by `calibration/outdoor_materials.py --root`; the root's
tables and X1's old files backed up in `backup_20261116_0244/`. Rows: map_stats 9130-9140; bolster `LowerToEqual` for
9136-9140; travel X1 west to X2 (arrival `left`, X2's east start, 3 days), X2 east to X1 (`right`, X1's west start), X2
west to Erathia (stand-in for X3), X2 north to 7out13 (stand-in for X4). Every Xeen playtest from the root with no extra
mount, two runs each: 36 of 36 pass (X1, X2, XD-01 to XD-06, XD-12, XD-21, XD-27). Launch commands in
`output/studio_play/PLAY.md`.

## Hostility pass (2026-11-16)

The user played the installed maps: "half the mobs were hostile to party while some were not and some even fought each
other (e.g. golems vs evil eyes)"; on X2 "some archers were hostile to party some were friendly".

**Cause.** A monster placed one by one (`objects.yml monsters`, `sketch.yml actors`) with `hostile: true` gets the
Aggressor bit and is hostile whatever the table says; a monster spawned from map_stats' three slots gets no bit, so its
relation to the party is MMerge's `engine/data_tables/hostile.txt` (`MonsterTable::getRelationToParty`,
`m_relations[0][(id - 1) / 3 + 1]`; between monsters `m_relations[target][actor]`). Many MM7 stand-ins are friendly (0)
to the party there: Archer, Fighter Leather (Robber, Raider, Bandit), Cleric Moon, Lich, Golem, Mage, Dwarf. And the
table sets some of a map's kinds on each other: Beholder on Golem 4 and Golem on Beholder 1, Beholder and Mage 4 each way
(XD-12), Dragonfly on Goblin, Skeleton and Rat 3 (X1, XD-01), Dwarf on Spider and Troglodyte 2 (XD-02, XD-03). So X2's
slot Archers were peaceful beside its placed (hostile) ranger camps, XD-12's slot Golems and Wizards peaceful while the
Eyes hunted them, XD-04's and XD-06's slot clerics and XD-06's Liches and XD-21's Raiders peaceful. The game sets a
monster's relation to the party by its kind, one row per tier number (`evt.SetMonsterRelation(<id>, 0, n)`; a group
toward the party does nothing), and between monsters by kind or group.

**Studio** (`openyamm-studio/`, build dir `build-hostility/`):
- `core/MonsterRelations.{h,cpp}` (new): one reader of a `relations` list (the indoor code moved there), its event lines,
  and the hostility check. `core/TableNames.{h,cpp}` (new): the named-row lookup the indoor lowering had as a member
  (`namedRow` now asks it; messages unchanged), shared with the outdoor reader.
- Outdoors: `sketch.yml relations`, the same schema and words as objects.yml's (both `$ref` common.schema.json
  `$defs/relations`), set by the same build event `evt:studio_relations` on entering the map (`core/OutdoorThings.cpp`;
  without an asset root left out with a warning, as placed actors are).
- The check (`oymap build` warnings, indoor `Lowering::warnMonsterHostility`, outdoor `warnOutdoorMonsterHostility`):
  (a) a slot whose spawning tiers hostile.txt has friendly to the party and no relation toward the party names, with the
  row to add (`{of: [ids], toward: party, relation: hostile}`, or `friendly` to say peaceful is meant); (b) placed
  monsters without `hostile` friendly to the party beside hostile ones of their kind; (c) two kinds both hostile to the
  party that hostile.txt sets on each other with no relation of the project between them (not within one group), with
  the rows that keep them apart (`{of: [...], toward: <id>, relation: friendly, both_ways: true}`, or `hostile` to say a
  fight is meant); (d) a group's relation toward the party (does nothing in the game). Kinds of a `map_stats.reference`
  row's own slots are left as shipped, so the 16 rebuilds of shipped maps stay quiet. The build reads `hostile.txt`
  and `map_stats.txt` with `monster_data.txt` (`LoweringOptions::relationTableText`, `mapStatsTableText`; none: no check).
- Unit cases: `tests/MonsterRelationsTests.cpp` (reader, slots from the reference row, the four warnings),
  `OutdoorTests.cpp` (outdoor relations), `CoreTests.cpp` (the indoor build's warning). All 455 cases pass.
- `output/studio_lead/g/oldnew.sh` (the lead's `build/oymap` against `build-hostility/oymap`, run before the briefs
  changed): the 16 calibration projects of devdocs/map_studio and XD-05, XD-27 byte-identical, the other nine Xeen
  projects different only in build.json's new warnings (the findings below); 247 of 247 shipped maps identical.
  No recorded expected answer holds build warnings, so nothing was re-recorded.

**Maps** (each generator changed and rerun, then `oymap fmt`; the regenerated files differ from before only by
`relations`; ids.lock.yml gains `evt:studio_relations`):

| Map | Source | Made hostile to the party | Kept apart (friendly, both ways unless said) | Peaceful kept |
|---|---|---|---|---|
| X1 | `x1/tools/gen.py` | (all foes hostile by the table) | Dragonflies 226-228 from Goblins 271-273 and Skeletons 397-399 | townsfolk, guards |
| X2 | patch, not applied (below) | Archers 202-204 | none set on each other | townsfolk, guards |
| XD-01 | objects.yml (`hostility/add_relations.py`) | (by the table) | Dragonflies from Rats 385-387 | |
| XD-02, XD-03 | objects.yml (`add_relations.py`); wiring's Lua `evt:clan_hostile` dropped (`drop_clan_lua.py`) | Dwarves 229-231 | Dwarves from Spiders 400-402 and Troglodytes 412-414 | |
| XD-04 | objects.yml (`add_relations.py`) | Moon clerics 214-216 | bats 205-207 toward the caged children 430, 433, 439, 442 (one way) | the children |
| XD-05 | `xd05/tools/gen.py` | (by the table) | Goblins, Bats, Spiders from Tam's kind 358 | Tam |
| XD-06 | `xd06/tools/gen.py` | Moon clerics, Liches 289-291 | none set on each other | |
| XD-12 | `xd12/tools/dress.py` | Golems 277-279, Wizard 293, Archmage 294 (not Sorcerer 292: Crodo) | Eyes 211-213 from Golems and from Mages 292-294 | Crodo, the Sorcerer in the library |
| XD-21 | `xd21/tools/gen.py` | Fighter Leather 256-258 | none | |
| XD-27 | unchanged | (by the table) | none | |

XD-01 to XD-04's project files are their own source (their generators are retired), so the edits are scripts in
`output/studio_cal/hostility/` run once; each map's NOTES.md has a "Hostility pass" paragraph. All ten build with no
hostility warning.

**X2** (another agent is reshaping its town in `output/studio_cal/x2/tools/` at the same time): not applied. The patch is
`output/studio_cal/hostility/x2_hostility.patch` (applies to the live `gen.py` and `gen_walk.py` as of 07:30, `patch
-p0` from the repository root): `gen.py` gains `relations = [{'of': [202, 203, 204], 'toward': 'party', 'relation':
'hostile'}]` after the lone wanderers and `'relations': relations` in the sketch; `gen_walk.py`'s walk to X1's west edge
gains `'clear_hostiles': 3000` (X1's slot monsters no longer fight each other, so the ones at the road's end stood in
the party's way: X2's playtest failed there twice, passes twice with it). X2's hostility scenario waits in
`output/studio_cal/hostility/scenarios/x2_playtest_hostility.yml` (to copy to `devdocs/xeen/briefs/x2/L4/`). Tested on
the current brief plus the relations (`output/studio_cal/hostility/proto/x2`).

**Game checks** (`build/game/openyamm` headless, scratch root `output/studio_cal/hostility/root`, a hard-link copy of
`output/studio_play/xeen_root` with every map rebuilt and installed by `oymap install --root`, X1's and X2's materials
by `outdoor_materials.py --root`): each map's `playtest_hostility.yml` (written by
`output/studio_cal/hostility/gen_hostility_tests.py`) enters with the map's own playtest party and asserts that no
actor of any foe kind is peaceful, that a slot-only kind and a placed kind are present and hostile, that the peaceful
kinds stay peaceful, then spawns the map's kinds the table sets on each other (and the peaceful ones' kinds) 96 apart
some 500 to 1,500 from the party (a monster takes the nearest of its foes; far from the party it does not think at all,
so a spot out of reach proves nothing) and runs 12 seconds: no actor of the map may take another as its target (AI
trace), none of them is hurt, and the last one spawned took the party (it was thinking). Results:
- every map's hostility scenario passes twice on the final builds; every other Xeen playtest passes twice (x1 388 steps, xd01
  131 + 14, xd02 200, xd03 181 + 46, xd04 174 + 77, xd05 98 + 47, xd06 121 + 12, xd12 124 + 98, xd21 99, xd27 91 + 33);
  X2's playtest passes twice with the `gen_walk.py` change (407), fails at X1's west edge without it;
- against the old play root the scenarios fail where the user saw it: XD-12 28 peaceful Brass Golems and Eyes, Golems
  and Wizards taking each other at once; X2 34 peaceful Archers; XD-04, XD-06, XD-21 peaceful slot clerics and Raiders;
  X1, XD-01, XD-02, XD-03 their kinds fighting. (XD-02 and XD-03 already had their Dwarves hostile by the Lua event.)
  XD-05's Tam check passes against the old root too: the spawned goblins, bats and spiders took the party, not the
  peasant, so the game did not show the table's 1-2 toward a peasant there; the rows stay as the map's word.

**For the game (not changed, needs the user's yes):** indoors a group made peaceful wins over a relation row toward the
party (`IndoorWorldRuntime` applies the rows, then the group requests), outdoors the row wins (`OutdoorWorldRuntime`:
group requests, then rows); a group as the left side toward the party is never read (both runtimes look the party's
rows up by kind only), which the studio now warns of.
