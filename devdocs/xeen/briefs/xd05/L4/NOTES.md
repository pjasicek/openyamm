# XD-05 Orc Caves, L4: notes

Built from L1-L3 with the Map Studio on 2026-11-13, one agent, under every rule of REBUILD_PROCEDURE.md. MM7 world as
stand-in (as XD-01 to XD-04).

State: `oymap validate` no issues; `audit`: 0 faces in one plane; build warnings only the placed monsters' names
(corpse only), three placeholders and the gate bar's ceiling note. 25 rooms, 26 sectors, all reached (solve: step 0
2 sectors, step 1 the palisade gate 24, step 2 boulder, cage gate, gate bar: 25 of 25). Playtests four of four each
(`output/studio_cal/xd05/four.out`: `playtest.yml` 96 steps, `playtest_back.yml` 47 steps), and once more on the play
root after install. Installed in `output/studio_play/xeen_root` (map, scene, Lua, map_stats row, 11 textures, 3 sounds).

Scratch: `output/studio_cal/xd05/` (`tools/gen.py` writes rooms/objects/wiring/project.yml: **the project files are
generated; edit gen.py and rerun `v.sh`**, not the YAML; `go.sh` build+install+one test; `four.sh`; `tour.sh`;
`root/` private hard-link root; `ref/` the Ogre Fortress looked at; `look1/` first look; `shots/` final pictures).

## Rooms and scale (`scale_bands.py`)

| Figure | XD-05 | shipped p25 / median | pct |
|---|---|---|---|
| bigger rooms (upper quarter) | 1.94 M | 1.06 / 1.64 M | 60 |
| largest room (Drum Hall, platform tops counted) | 16.1 M | 3.68 / 6.13 M | 75 |
| typical ceiling | 640 | 394 / 521 | 74 |
| taller rooms | 768 | 522 / 570 | 67 |
| doorway | 320 | 256 / 256 | 57 |

L3's 45 rooms became 25: the Drum Hall is one room (a U-shaped rock terrace platform 256 up, three flights of eight
32-steps, two buttresses, the scaffold a free-standing plank deck on six posts with rails, gangway a hanging flight),
the bat chimney one room (gallery of six wedge/landing platforms round three walls up 576), the back tunnel one
climbing section tunnel, the ledge one path room. Every main room was enlarged (cookfire 2,700x1,500, yards 2,560 wide,
hollows 2,400 long, den 1,400x1,350, pool 1,600x1,280).

## Set pieces as built

- **Three drums** (platforms: octagon drums, generated hide head `xodrumtp`, laced shell `xodrumsd`): click burns
  (`set_texture` to `xoburn`, a pulsing fire light, +250 xp), 4 s later charred (`xochar`, ember light); a second click
  says so. Third burnt: `war_drums_burned` 110050, +750 xp, message.
- **Drum layers**: three placed looping sounds (synthesised `xodrumgr/sg/sp.wav`, radius over the map); each burn sets
  `AmbientSound<n>`=2 and the beat stops; the Drum-Master's death stops the great drum's beat (playtests assert all).
- **Palisade**: log palisade (`xopalis`) with firing steps 192 up behind two thirds (parapet 64, open above), murder
  holes, two timber stairs; the gate = two hinged d12 plank leaves (`gkp103a/b`) on two openings beside a gate post,
  one click opens both.
- **Captive**: hollows step text (voice from the pit) → cage gate of lashed poles (`xopoles` cut-out, folds up) →
  a real climbable ladder → reaching Tam opens his message, sets `captive_freed` 110052, he vanishes.
- **Plunder cache**: drag-mark plates (`xodrag`) with a step text lead to a secret rock leaf "Boulder" (sinks).
- **Shaman's den**: hide curtain (non-solid panel, `xohide`), bone wall (`xobones`), green torches, cauldron, dais.
- **Back gate**: exit panel `xobackgt`; barred message until the bar (a mover beam in brackets) is lifted
  (`orc_back_gate_open` 110051).
- **Why here**: one-shot arrival message (the three drums and where, Tam; no task giver: Gunther's clause dropped 2026-11-21).

## Textures

One family: **MM8 Ogre Fortress (d12, "Ogre Raiding Fortress": a warband's cave lair)**: `gcav1flr` rock walls/roofs,
`gcav2flr` floors and the deep caves' walls, `gkp1flr` straw in the warren, `gkp1ceil` plank decks, `t66abc10a` posts,
`gkp103a/b` doors, `gkp1-bs1`/`t66flr2` hearth, `gstnlock` brackets, `gt002` chests, `wtrtyl` MM8 water (fluid bit).
Generated (`level_generation/textures_xeen`, specs `xo*`, Codex in d12's style): xopalis, xodrumtp, xodrumsd, xoburn,
xochar, xodaylt (the daylight exit view), xobones, xohide, xopoles, xobackgt, xodrag. Brief's cwb1/dirt1/bwood/cws1a
picks were dropped (mixed maps, two in no dungeon).

## Rules

Read: hover names on every clicked thing (drums, gate, cage gate, boulder, gate bar, exits, Chest); no silent clicks
(drums, cage gate, gate bar, barred exit all answer); no riddles; clues before need (arrival names the drums, step texts
for pit, drag marks, hall, den); no key items; water flows (shader liquid); monsters on walkable floors (bats in the
open shaft); 0 coplanar pairs; scale above median.

## Departures

Monsters: Goblin family for orcs, Spiders for snakes (MM7 has none), Goblin Lords for Drum-Master/shaman/guards (shaman
does not cast). No frenzy. Back tunnel has no flight of steps (path tunnels only ramp). Boulder sinks, not rolls.
Ladder hangs from the start (no drop animation). Ledge ~6,000 long (map grew). Terraces/scaffold drawn as real
platforms, so L3's "not drawable" notes are moot.

## Gaps

1. Drum-Master is a 40-hp Goblin Lord: `hp` ignored, names only on corpses (known). 2. No monster frenzy/buff word.
3. No destructible drums by fire spell (click only). 4. No indoor smoke/fog. 5. Sounds need a file in the root's
`worlds/mm7/audio` (installed by hand alongside textures). 6. No item-on-NPC talk; Tam is freed by a step event.

## Tool defects

- `oymap assets <name> --assets R` without `--world` finds nothing (`oymap assets cwb1 --assets assets_dev`).
- playtest `mapvar(name)` cannot read project-declared variables (XD-04's, still).
- arrival timer windows do show headless here and block `walk_to` (need `close_dialogs`), unlike XD-02's note.
- tour's `actor kill 0` did not remove the Drum-Master from shot 27 (index or command semantics).
- `install` with `xtex.py install` and no names installs every finished texture (trap).

## Pictures (`output/studio_cal/xd05/shots/`, captions.yml, plan.png, iso.png)

Best: 02 mouth daylight, 04 palisade gate open, 16 cage gate open with ladder, 24 Drum Hall from the entry, 28 great
drum burning. Weakest: 30/31 chimney (dark, rock reads flat), 34 back tunnel (bare). Monsters block several drum shots.

## Judgement

A solid optional Act I cave: the palisade under fire, the burning drums with their beats dropping out, the amphitheatre
with its scaffold and the chimney/ledge loop all work and read. Weak: one-texture rock gets monotonous in the deep
caves, the boss is weak, rooms are plain polygons without rough walls.

## Second pass: the user's walk (2026-11-13)

The user played the installed map ("otherwise good") and named four things. All fixed in `tools/gen.py` (backup of
the first pass: `output/studio_cal/xd05/pass2_backup/`). Pictures: before `output/studio_cal/xd05/walk2_before/`
(play root), after `walk2_after/` and `walk2_play/` (play root after install), stalactites `walk3b/`; sheets beside
them (`*_sheet.jpg`).

1. **Lamp lying on the ground** (inner yard, (299, 3337)): `brzier00` is a brazier basket with no stand or chain; it
   lay on the floor. The yard's one is now a campfire (`7dec02`) under its light; the other eight (firing steps, the
   hall's top terrace, the scaffold) are standing skull torches on poles (`torskul0`, a standing kind). Wall torches
   (`torch01` at the chimney and the back gate, `torch06` in the den) had no `height` and stood at the floor in front
   of the wall; now 160 up on the wall (shipped MM7 dungeons put torch01 133-189 over the floor: 7d10, 7d13, 7d16).
   No decoration in the map hangs or floats now.
2. **Stalactites; formations only in wide caverns** (the user, through the lead): MM7 has no stalactite art at run
   time (`stltite1-3` are MM6 sprites with no runtime picture and no model: placed, they draw nothing), so the 25
   stalactites are geometry: three stacked hanging rock octagons narrowing downward (radius 96-120, 272 long), the top
   one's `top_heights` following the sloping roof read from the first build. Rooms with formations: cave mouth,
   palisade cave (outer yard), inner yard, cookfire cave, Drum Hall, bat chimney, snake pool (stalactites; d12's other
   rock so they show against the roof), and stalagmites only in the pool, chimney and Drum Hall. Taken out of the
   back tunnel (three stalagmites that also blocked it); none in the run, hollows, ledge or other passages.
3. **Back gate**: the two `gstnlock` blocks (a keyhole picture: read as locks with no key) are now timber chocks of
   the bar's own wood (`t66abc10a`) under its ends; the gate's torches are on the wall at 160 beside the gate.
4. **Right-angle turn**: the back tunnel (Drum Hall north) bends in arcs of four segments (radius 256) at both bends
   and wanders slightly on its straight legs (14 path points, slopes at most 0.7). The upper ledge's jog at its north
   end is a diagonal stretch now. Left square: the ledge's last corner at the firing step's doorway (a ledge turning
   into a timber door) and the run's three rooms (straight legs joined by the bend's octagonal belly).

State: `validate` no issues; `audit --strict` 0 coplanar pairs, only info lines; playtests four of four each
(`playtest.yml` 96 steps, `playtest_back.yml` 47), once more on the play root after install.

Tool defects found: the build's "rests on nothing" check reads a block's top as one height, so a hanging block whose
top follows a sloping roof by `top_heights` is reported as hanging from nothing (25 warnings here, one per
stalactite); and a decoration kind whose art is missing at run time (`stltite1-3` in MM7) is placed without a word.

## Exits to Vertigo (2026-11-13)

`exit:x1_hills` (the mouth, evt:exit_x1 18) now leads to X1 (`xeen_x1.odm`): arrival [9216, 16643, 1376], facing 270
(south, downhill), in front of X1's cave mouth (`thing:orc_cave_mouth`, face at y 17043). Changed in `tools/gen.py`
(the project's neighbours and its notes line) and regenerated with `v.sh` (only project.yml changed). Unchanged:
`exit:x7_slopes` still goes to Emerald Island (X7). `playtest.yml` checks map and position on X1 after the mouth and
walks off downhill. X1's walk now goes in by the mouth and out by this exit.

Backup before the change: `output/studio_cal/xd05/exits_backup/`. Build `output/studio_cal/xd05/exits_build/` (against
`output/studio_play/xeen_root`); only the exit's `evt.MoveToMap` line changed in the built Lua (the .blv and scene are
byte-equal to the build of the backup). Installed in `xeen_root`. Arrival points were read from X1's build
(`output/studio_cal/x1/build/export.json`: the doorway models' faces; ground from its height map), 400 units in front of
the door face, clear of the doorway model, on open ground; the playtest walks off from there. Pictures of every arrival,
facing out and turned back to the door: `output/studio_cal/x1/exits_pics/sheet.jpg`. On first arrival on X1 from a
dungeon Mayor Gunther's errand window opens (X1's one-shot timer), as on a new game there.

## Hostility pass (2026-11-16)

The user found monsters peaceful to the party beside hostile ones of their kind and monsters fighting each other
(devdocs/xeen/ACT2_BUILD.md, "Hostility pass"). MMerge's `hostile.txt` decides a slot monster's relation to the party
and two kinds' to each other; the studio now warns of both (`oymap build`) and the map says its relations in objects.yml
`relations` (the build's load event `evt:studio_relations`). Written by `output/studio_cal/xd05/tools/gen.py`: the
Goblins, Bats and Spiders kept from Tam's kind (358), both ways (his captors and the pit's vermin are set on him by the
table, he on them). `playtest_hostility.yml` (written by `output/studio_cal/hostility/gen_hostility_tests.py`) checks
the slot and placed foes hostile, the peaceful ones peaceful and the map's kinds, spawned side by side near the party,
not taking each other on; it passes twice, as do the map's other playtests.

## Rebase, phase 0 (2026-11-20, lane A7)

The design part of the rebase (`devdocs/xeen/CHANGES_FOR_BUILT_MAPS.md` A1-A7 and XD05-1 to XD05-4; MAPS §0 row:
party 3 → 5, monsters 4-10, Drum-Master 12, 40 monsters, Tres 1). Still `world: mm7` on MM7 rows: the Xeen world,
its rows and its hooks do not exist yet (lanes A1, A2, A3 not started). Changed in `output/studio_cal/xd05/tools/gen.py`
(backup of the files before: `output/studio_cal/xd05/a7_backup/`), regenerated with `v.sh`.

| | Before | After |
|---|---|---|
| Monsters at load (spawn points × mean group + placed, `output/studio_cal/a7/count.py`) | 40 | 40 (MAPS: 40) |
| Levels | 3-10 (bats tier a, Giant Bat 3) | 4-10: the bats at tier b (Vampire Bat 6); orcs 4/6/10, serpents 5; Drum-Master 10 |
| Map treasure level | 1 | 1 |
| Chests | cache 2, shaman 2, hollows 1, pool 1 | the plunder cache 2 (the warband's hoard, the map's one chest a level up), the rest 1 |
| Distinct face textures | 24 | 24 (M cap 45) |
| Doors | 5 door records | 5 (below the M band's 6-16 already: nothing to trim) |

**Original lines** (MAPS §0, A5), all three in the map now:
- the drums ask the orc outposts' question: "You have found a war drum of the Orcs!  Destroy?" with `Destroy (Yes/No)?`
  (`aaze0019`, "observation post" made "war drum"); No leaves it beating ("You leave the drum as it is, for now.");
- a burnt drum's fire dies with "The drum collapses in a heap of ashes, smoke, and smoldering timber." (`aaze0019`,
  "outpost" made "drum"; status text four seconds after Yes);
- entering the sleeping hollows: "Crude furnishings and filthy bedding tell you that orcs have been living in this
  cave." (`aaze0022`, the orc cave F2), followed by Tam's voice from the pit.
For A3's ledger `devdocs/xeen/ORIGINAL_LINES.md` (it does not exist yet).

**Fixed on the way:** the current studio measures a platform in a sunken level from that level's floor (build warning on
the pool's second stalactite); the generator meant exactly that (its heights are read from the level floor -736), so
`project.yml` `migrated` gains `platform_in_sunken_level` and the stalactite stays where it was. `audit` flagged the pool
mushroom (`deco:pool_mushroom`) in the slope's doorway line: moved to [1980, 10150] on the west shore.

**Exits:** `exit:x1_hills` to X1 as before; `exit:x7_slopes` still leads to Emerald Island (X7 is built in phase 5;
the back gate stays barred until the bar is lifted, so a player meets it only at the end).

**Waiting on other lanes:** the Drum-Master's boss row at 12 and the Orc / Serpent / Bat families as Xeen rows (A2;
until then Goblin Lord 273 and MM7's Goblin, Spider and Bat families), the quest bits 110050-110052 registered in the
quest files (A3, Q-C21), `world: xeen` and the install into `assets_dev/worlds/xeen/maps/` (A1's W5), map card and
lighting.

**Checks** (root `output/studio_cal/a7/root`, scripts `output/studio_cal/xd05/a7_go.sh` and `a7_four.sh`):
`validate` no issues; build warnings only the placed monsters' names, three placeholders and the gate bar's ceiling note
(as before); `audit --reach --solve`: 0 coplanar pairs, no warning, 25 of 25 sectors reached in three steps, both exits;
`fmt --check` clean. Playtests four of four each (`output/studio_cal/xd05/a7_four.out`): `playtest.yml` 112 steps (now
answers No once and Yes at each drum), `playtest_back.yml` 47, `playtest_hostility.yml` 30 (its slot-only bat check
now looks for the tier-b Vampire Bats, 206). Pictures: `output/studio_cal/xd05/a7_shots/` (the 36 poses of
`shots.yml`, sheet `a7_shots_sheet.jpg`), looked at: the map as before; monsters still stand in front of several drum
shots. The drum question and the bedding line are message/status texts, checked by the playtest, not pictured.

**A3's hooks (2026-11-20, `source/quests/x1-tam.yml`):** `x1-tam.tam` (captive_freed 110052), `x1-tam.drums`
(war_drums_burned 110050) and `x1-tam.back_gate` (orc_back_gate_open 110051) carry the numbers this project already
uses, so `tools/xeen/quests.py --open` lists nothing open on XD-05. Their `XeenQuests.hook()` calls go in with the move
to `world: xeen` (the world's Lua does not load in `world: mm7`). Two texts to settle with A3: the hook's Tam ("A boy in a
cage ... gone up the tunnel") does not fit the built pit with its rope ladder (the map keeps its own line until then);
the hook's drum line is the one each burnt drum already shows here.

## Into the world (2026-11-20, lane A7)

The pilot of the move for the lane (A1 merge point 2: `--world xeen` loads the world's monster, item, map_stats and
quest tables). Changed in `output/studio_cal/xd05/tools/gen.py` (files before: `output/studio_cal/xd05/a7_backup_move/`):

- `world: xeen`. Slots by A2's slot names: 1 `Xeen Orc` (Orc 11030 5, Orc Archer 11031 7, Orc Guard 11032 10; the
  spawn points fix a or b), 2 `Xeen Bat` at tier b (Cave Bat 11301 6), 3 `Xeen Snake` (Giant Snake 11480 5).
- Placed: the Drum-Master is his boss row 11033 (12; `hp` and name dropped, the row is named), the shaman an Orc Guard
  11032 named "Orc Shaman" (Xeen's Orc Shaman row 11041 is the level-20 warband's), the two gate guards Orc Guards
  11032, Tam the engine peasant 358.
- `relations`: only Tam kept apart from the Orcs, Bats and Snakes (11030-11033, 11300-11302, 11480-11482), both ways;
  the families' hostility to the party is the world's `relations.yml`.
- The drum sounds `xodrumgr/sg/sp.wav` copied into `assets_dev/worlds/xeen/audio/` (the studio looks there for a
  `world: xeen` project; they lived only in the old play root).
- Installed with `openyamm-studio/build-xeen/oymap install --root assets_dev`: `assets_dev/worlds/xeen/maps/
  xeen_xd05.{blv,scene.yml,studio.yml}` and `events/maps/xeen_xd05.lua`. No table rows (A2's `map_rows.yml`).

**Studio defects met** (for A1): the indoor `validate`/`build` read monster numbers and descriptors only from the
root's engine tables, so a placed Xeen row is "no monster number 11033"; worked round with
`output/studio_cal/a7/root_xeen` (a hard-link copy of assets_dev whose engine monster_data and monster_descriptors carry
the world's rows appended: `output/studio_cal/a7/mk_studio_root.py`). The build's hostility check reads engine
`hostile.txt`, not the world's `relations.yml`, and warns that the Xeen Orcs, Cave Bats and Giant Snakes are friendly
to the party (they are hostile in the game by the world's relations).

**Game checks** (`build-xeen/game/openyamm --world xeen`, root `output/studio_cal/a7/root_xgame`: a hard-link copy of
assets_dev plus X1's stand-in files from the old play root and MM7's liquid-edge masks in `worlds/xeen`, because the
world's start map X1 is not in the world yet and the exit leads there): `playtest.yml` (112 steps) and `playtest_back.yml` (47) pass 4 of 4
(`output/studio_cal/xd05/a7_xfour.out`), the Drum-Master's and the guards' Xeen rows killed and the exit to X1 taken. `playtest_hostility.yml` (ids now Xeen) fails at its slot-kind step: the world's
map_stats row 9135 still names MM7's Goblin, Bat and Spider (A2's `source/map_rows.yml`), so the slots spawn MM7 kinds.
It passes once A2 writes the row with this map's slots (the lane's report gives them).

**Still open:** A2's map row (slots above; music, treasure 1 unchanged); X1 in the world (A5) for the exit's arrival
from assets_dev; A3's Tam text; `XeenQuests.hook()` calls for x1-tam's hooks; lighting bake; pictures in the world.

## Dressing rule (2026-11-20, lane A7)

The user's rule (`devdocs/xeen/formats/DRESSING.md`): no prop blocks a door, doorway or passage; containers by the walls,
in pairs, clumps only in storerooms. Checked with `output/studio_cal/a7/dressing/check_dressing.py` on the built map
(before: 14 findings, after: 2). Moved in `tools/gen.py` (before: `output/studio_cal/xd05/a7_backup_move/
gen_before_dressing.py`):

- outer yard: the two bones and the dead orc off the walk from the mouth to the palisade's side openings, to the side
  walls ([-1150, 1500], [1150, 1450], [1100, 1650]);
- inner yard: the barrel and keg from the west stair's foot to a pair on the west wall ([-1190, 3250], [-1190, 3370]);
- cookfire cave: the cask off the walk from the run to the hollows, onto the south wall ([-600, 5840]);
- plunder cache (a storeroom): the cask and the flour sack away from the boulder's opening, beside the barrel and the
  bags ([-4230, 5730], [-4170, 6230]);
- west firing step: the arrow barrel removed (the deck is 384 deep and every spot on it is within a doorway's clearance).

Left: the cookpot in the hearth ring in the middle of the cookfire cave (the room is built round it; the walk from the
Drum Hall ramp to the hollows passes the ring, 2,700 by 1,500 of floor round it). Checks after: validate, build, audit
(0 coplanar, 25 of 25 sectors), `fmt --check` clean; `playtest.yml` and `playtest_back.yml` 4 of 4 with `--world xeen`
(`output/studio_cal/xd05/a7_xfour2.out`); pictures `output/studio_cal/xd05/a7_dress_shots/` (sheet
`a7_dress_sheet.jpg`), looked at: the props stand by the walls, the yard's pair against its west wall.

## Sealed exits (2026-11-20, lane A7)

No exit of a Xeen map may lead to an MM7 map (the orchestrator). **The back gate to X7 (Mount Firestone's south slopes)
was sealed until X7 existed** (phase 5, lane A5; opened in the ninth session, below):

- before: `exit:x7` on the guardroom's north wall, neighbour `exit:x7_slopes` → `7out01.odm` (Emerald Island as a
  stand-in), open once the bar was lifted (`orc_back_gate_open` 110051);
- now: `panel:back_gate`, a wall panel with the same gate picture (`xobackgt`) and the hover name "Back gate". Barred:
  "The gate is barred from inside ..." (as before). Bar lifted: "The gate opens a hand's breadth and stops: a fresh
  rockfall has buried the path down Mount Firestone's slopes. There is no way out here for now." The bar, its quest
  bit and its hook (`x1-tam.back_gate`) work as before; `plan.yml` lost the `entrance:x7_back_gate` entrance and
  `project.yml` the neighbour. The built Lua has one `MoveToMap`, to `xeen_x1.odm`.
- **To open it when X7 exists:** in `tools/gen.py` put back an `exits` entry `exit:x7` on `room:back_gate`'s north wall
  (size [160, 320], surface `xobackgt`) in place of the panel, a project neighbour to X7's stem at the gully door A5
  gives, its `plan.yml` entrance, and make `evt:exit_x7` the `exit` preset again with the bar's qbit as its condition;
  `playtest_back.yml` then leaves by it again (its last steps now assert the rockfall message and that the party
  stays). Diff: `output/studio_cal/xd05/a7_backup_move/gen_before_seal.py`.

**Opened to X7 (2026-11-20, ninth session, lane A7):** X7 is installed (A5, 21:39). In L4 by hand (the generator is
stale; L4 is the source): `exit:x7` on `room:back_gate`'s north wall (160 x 320, `xobackgt` fitted) in place of the
panel; neighbour `exit:x7_gate` to `xeen_x7.odm` at X7's named arrival `entrance:xd05_gate` (11776, -18432, 2016)
facing west, before the log door at [88, 100]; `evt:exit_x7` the `exit` preset again with `orc_back_gate_open` 110051
as its condition (barred: a status line "The gate is barred from inside ..."); the plan entrance and the named arrival
`entrance:x7_gate` at (2176, 13184) on floor 320 facing south, for X7's door into the caves (A5). `playtest_back.yml`
now lifts the bar and leaves: the party lands at (11776, -18432, 2017). The rockfall message is gone.

The cache's flour sack is gone too (it stood inside the trash heap or by the boulder's opening wherever it went).

**Checks after the seal (2026-11-20), from `assets_dev` itself with `--world xeen`** (X1 is in the world now, A2's row
9135 carries the Xeen slots): validate, build, `audit --reach --solve` (0 coplanar, 25 of 25 sectors, no warning),
`fmt --check` clean, dressing check 2 findings (the hearth's cookpot, kept); `playtest.yml` 112 steps, `playtest_back.yml`
48, `playtest_hostility.yml` 30, each 4 of 4 (`output/studio_cal/xd05/a7_xfour3.out`). The hostility test now passes:
the slots spawn Xeen Orcs, Cave Bats and Giant Snakes, all hostile by the world's relations, none fighting another.

## Balance (2026-11-20, lane A7)

A2's count (`python3 tools/xeen/balance.py --detail`, the installed map) put XD-05 at 1.1k kill XP per member against
MAPS §0's 0.9k (1.21, over the 15 % gate): 15 Orc Archers (B) from six tier-b points were the excess. Four orc points
moved from tier b to a (`spawn:gate`, `cookfire_e`, `hall_s`, `hall_floor`; the cookfire's west group and the hall's
west terrace keep their archers): **1.0k, 1.08**, still 40 monsters (20 Orcs, 5 Orc Archers, 7.5 Cave Bats, 3 Giant
Snakes, 3 Orc Guards, the Drum-Master). The map card's slots are unchanged (the tiers are the spawn points'), so A2's row
9135 needs nothing. Reinstalled; all three playtests 4 of 4 again from `assets_dev` with `--world xeen`
(`output/studio_cal/xd05/a7_xfour4.out`). Before: `output/studio_cal/xd05/a7_backup_move/gen_before_balance.py`.

**A3's stuck walk (2026-11-20).** The playthrough chain's walk stuck 3-9 s at (700, 2853, 0) in the inner yard, turning
from the east stair's foot round the wall end at x 896 toward the gate. Two `dec03` barrels stood exactly there
([700, 2900], [600, 2930]); the dressing checker missed them because `dec03`'s hint names no barrel (it now also reads
the object's id). Moved to a pair on the yard's east wall ([1200, 3250], [1200, 3360]); the plunder cache's barrel
moved off the boulder's opening ([-4160, 5705]). Dressing check: 2 findings left (the hearth's cookpot). Reinstalled;
`oymap probe` from the stair foot to the gate road finds its route past the wall end; all three playtests 4 of 4 again
(`output/studio_cal/xd05/a7_xfour5.out`).

## Lighting bake (2026-11-20, lane A7)

Profile `tools/lighting/baked_indoors/profiles/xeen_xd05.yml` (16 units per texel, one 2048-wide page, 128 samples, 3
bounces, light size 24; direct 2.0, bounce 5.0, ambient 0.9, ceiling 1.5: one calibration for the five, set on XD-05
against the unbaked map). Baked with `bake_indoor.py --game-binary build-xeen/game/openyamm --sources
output/studio_cal/xd05/a7_bake/xeen_sources` (Blender 5.3 in one process under a 16 GB cap; scripts in
`output/studio_cal/xd05/a7_bake/scripts/`, passes kept in `output/studio_cal/xd05/a7_bake/bake/` for `--recompose`).
`--sources` is a staged root of the world's own x4 masters (links to `level_generation/textures_xeen/finished/`): the
bake needs a material for every face and the Xeen textures have no source in `assets_source/worlds/xeen/textures_x4/`
yet. Installed `xeen_xd05.lighting` and `.bake.json` (new file, then rename).

- Bake: 2048 x 907 (1.86 M texels), 1,966 charts for 2,215 of 2,249 faces (19 mover faces), 43 static lights; 58 s
  Cycles, 81 s in all; `xeen_xd05.lighting` 2.95 MB, `.bake.json` 760 bytes.
- Pictures `output/studio_cal/xd05/a7_bake/` (`baked/`, `unbaked/` with `--set video.lightmaps=false`, `compare.jpg`
  baked left): 59.2 baked against 63.5 unbaked (first take direct 1.4, bounce 4, ambient 0.8: 52.0, too dim round the
  fires). Palisade, cookfire cave, shaman's den, Drum Hall and the snake pool: pools of warm light at the torches and
  the fire, the palisade's timbers less flat; the den's green torches a little less saturated. The burning great drum (a
  pulsing light) shows over the bake as before. No black faces, seams or leaks seen.
- Switched lights (the bake keeps every BLV light as the map starts): The drums' fire lights are pulsing: fine. The
  ember lights `light:ember_*` are BLV lights off at start: not baked, so a charred drum's embers light the actors but
  not the walls. The fix is the map's: build an event-switched light as a pulsing light (constant pulse) as
  INDOOR_PULSING_LIGHTS.md says, then re-bake.
- Stale check: listed only for the world's own x4 masters (`worlds/xeen/textures_x4/*.png`), which have no home in
  `assets_source` yet; with them in a source root at that path it lists nothing (checked), so installing the finished
  masters there byte for byte clears it without a re-bake.
- Playtest (`playtest.yml`, `assets_dev`, `--world xeen`): passed (`output/studio_cal/xd05/a7_bake/playtest.out`).
- Re-bake after any rebuild of the map: `output/studio_cal/xd05/a7_bake/scripts/bake_one.sh 5`, then `install.py 5`.

## Hooks, switched lights and D-7 dressing (2026-11-20, lane A7, second session)

**Hooks.** `evt:tam` calls A3's `x1-tam.tam` (captive_freed, his words, 300 experience) and hides group 20; `evt:drums_all` calls `x1-tam.drums` (war_drums_burned, the words, 500 experience: it was the map's 750); each drum's own 250 stays the map's.

**Switched lights as steady pulsing lights.** A bake keeps every BLV light as the map starts (INDOOR_BAKED_LIGHTING.md, INDOOR_PULSING_LIGHTS.md "Switched lights"), so each light an event switches is now a scene light with `pulse: {intensity: [1, 1], frequency: 0.1}` (constant): it is not baked, and `lights_on` / `lights_off` switch it as before (`evt.SetLight` key 40000 + its ids.lock number). Script: `output/studio_cal/a7/hooks/pulse_lights.py`. Here: `light:ember_great`, `light:ember_signal`, `light:ember_spirit`.

**Dressing (D-7.1, A1's recalibrated audit of 14:41).** `oymap audit --world xeen --reach --solve` on the installed map (scratch root `output/studio_cal/a7/root_d7`, lane script `output/studio_cal/a7/xcycle.sh`; walking-line pushes by `output/studio_cal/a7/dressing/fix_lines.py` and `d7_moves.py`): no error left. Changes: `cook_keg` stood on a stalactite's top (z 568): on the floor by the south wall, a pair with the cask; `run_rock_1` off the run's line; `cook_trash` (between the cookfire cave's lines) removed.

### Dressing exceptions

- `cookfire`, `cookpot` (the cook's fire and pot, set pieces): 59 from the line between two of the cave's openings (faces 2009, 2010), by the cave wall, kept as the phase-0 pass kept them.
- `yard_brazier` (the yard's campfire, a set piece): the yard's centre fire, 18 from the line between two of its openings (faces 2035, 2037); the party walks round it.

## Merge point 9's `facing` warning (2026-11-20, lane lead A7, fourth session)

`deco:palisade_corpse` (Corpse04, a randomly turned model) lost its unused `facing: 180` in objects.yml (gen.py too;
note that `tools/gen.py` no longer reproduces objects.yml: the D-7 dressing fixes were made in the YAML). Rebuilt,
installed, re-baked; playtests in `output/studio_cal/a7/s4_facing_chain.out`.

## Build warnings (2026-11-20, merge point 11)

Lane A7's warnings pass (oymap of merge point 11). Build warnings 6 → 4. Edited in the L4 YAML (`tools/gen.py` no
longer reproduces the project, see above); before: `output/studio_cal/a7w/backup/xd05/`.

- **Built:** `placeholder:spits`: two 16-square timber posts on the hearth ring and a spit bar between them
  (`platform:spit`, 128-138 over the cave floor, `solid: false` so the fire is not set on its top and nothing stands
  on it); `deco:hearth_fire` pinned to the hearth top (`floor_height: -216`). `placeholder:spear_rack`: on the drum
  scaffold by its south rail ([-1232..-1072, 9864]): two uprights, a top and a foot bar, four spear shafts of
  staggered heights with fire-hardened points (tapered blocks), all in the scaffold's timber `t66abc10a` (no new
  texture; 24 distinct as before).
- **Placeholders kept:** `placeholder:cart_wheel` (plunder cache): needs a cart-wheel decoration model (a wheel leaning
  on a wall; a vertical disc cannot be built of the studio's upright blocks).
- **Kept:** the names "Orc Shaman" and "Tam" (corpse only until the world has a placed-monster name table); the gate
  bar's ceiling note (a bar nobody rides).
- Checks (root `output/studio_cal/a7w/root`, `output/studio_cal/a7w/wcycle.sh`): validate clean, audit `--reach
  --solve` as before (25 of 25 sectors, the three dressing exceptions above, 0 coplanar pairs); `playtest.yml`,
  `playtest_back.yml`, `playtest_hostility.yml` 4 of 4 each (`output/studio_cal/a7w/xd05_four.out`, logs
  `output/studio_cal/xd05/a7_xrun/`). Pictures before | after, lightmaps off:
  `output/studio_cal/a7w/shots/xd05/sheet.jpg`. Needs a re-bake after install (geometry changed).

## Lamp rule (2026-11-20, lane A7, sixth session)

A1's light check (`oymap audit`, `devdocs/xeen/formats/LIGHTS.md`) found 15 errors and 14 warnings; now none
(root `output/studio_cal/a7/root_lights`, build `output/studio_cal/xd05/a7_xbuild`, its 4 build warnings unchanged).
`torskul0` is a wall torch (bound `mount: wall`), not the standing kind the second pass took it for:
- On their walls, 160 over the floor: the mouth's pair (north wall either side of the passage, x ±320), the palisade's
  pair (its outer face either side of the gate, x ±320), the four along the Drum Hall's top terrace (south wall,
  `floor_height: -384`), the firing steps' two (east step: north wall at x 540; west step: west wall at y 2140).
- The buttress torches stood on the spurs' crowns, with no wall: now on the spurs' faces towards the bowl, 256 over the
  floor; their lights (`light:hall_buttress_e`, `_w`, 800 over the crown: in the rock over the roof) moved with them,
  440 over the floor in front of each torch.
- The two scaffold torches flanking the great drum are standing flambeaux (`flamb00`) on the deck where they stood.
- `light:palisade_w` stood over a stalactite's top (its height counted from there: z 1208, in the rock): now
  `floor_height: 0`, 320 over the yard as its east twin.

## Merge point 15 doors (2026-11-20, lane A7, seventh session)

- **`tools/gen.py` is stale** (it lacks A3's hooks, the lamp rule and later L4 edits): it now refuses to run. L4 is the
  source; edit it and `oymap fmt`. This session ran it once by mistake and restored L4 from `.oymap/last` (the rebuilt
  BLV, scene and Lua were byte-identical to the installed map, and the lock's hash matched the install's).
- **Palisade gate** (`doors.half_wing` on doors 3 and 4: each 192-wide leaf showed one wing of the gkp103a/b pair on its
  own, a 32 post between them): the two openings now meet over a 16-wide sliver of post (`along` 0.3646 and 0.6354 on
  the 768 wall; the studio wants 16 of wall between openings), so the two hinged leaves read as one gate's pair. Door
  numbers and events unchanged.
- **Cage gate** `xopoles` leaf `translucent: 1` (A1: its alpha is graded, so it speckled).
- Audit: no error; the three kept dressing warnings. Build warnings 4 (unchanged). Installed, re-baked; from
  `assets_dev`: `playtest` (112), `playtest_back` (48), `playtest_hostility` (30) 4 of 4 each
  (`output/studio_cal/a7/s7_mp15_chain.out`).

## Texture fit (2026-11-20, merge point 16, lane A7, eighth session)

- The three drums' heads `xodrumtp` at their size (a platform top ignores `fit`): `scale: 2` on the great drum, `1.5` on the signal and spirit drums, offsets so each head shows the picture once, whole (0.99 x 0.99).
- The hide curtain: `xohide` laid once over each side (`fit: true, uneven: true`, was 2 hides across), its ends and top in `xopoles`.
- Audit: no `textures.*` finding.

## Merge point 17 (2026-11-20, ninth session, lane A7)

- Rebuilt with the gate to X7 (above). Build warnings left: the cart-wheel placeholder, the bar's ceiling note, the
  `xopoles` squash on the shaman's den hide, and the names "Orc Shaman" and "Tam" with no place_mon rows (A2).
- AU's `xeen_fire_ignite` (A5's note: no event on X1 burns the drums): each drum's Yes plays it at the drum
  (`evt.PlaySoundName`, great (-960, 10304, -168), signal (1120, 2128, 256), spirit (-2912, 7200, -104)); installed
  with bake, 12/12 from `assets_dev` (`output/studio_cal/a7/s9_xd05` chain).

## Placed names (2026-11-20, tenth session, lane A7)

A2's world `place_mon` rows give the living monsters their names: Orc Shaman 414 and Tam 415 (`unique_name_index` in the
installed scene). Rebuilt with the merge point 18 oymap: build warnings 5 → 3 (the name warnings gone; the "Kept: corpse
only" lines above are history); installed with its bake; every playtest 4 of 4 from `assets_dev`
(`output/studio_cal/a7/s10_names_xd05.out`).

## Nineteenth session (2026-11-21, lane A7 lead)

- Merge point 27 (oymap 06:06:32): rebuilt; the peaceful-group load event now runs once per fill (map var
  `studio_peaceful_groups`), first of the load events. Only the generated Lua changed (BLV and scene byte for byte the
  installed ones; `output/studio_cal/a7/s19/`), so no rebake; installed 06:10:39; the studio file's revision caught up
  with the L4 (06:17:09); stale bakes 0. Audit
  from `assets_dev` 0 errors, the kept warnings (`output/studio_cal/a7/s19/audit/xd05.txt`); playtests 2 of 2 from
  `assets_dev` (`output/studio_cal/a7/s19/two_xd05.out`).

## Twentieth session (2026-11-21, lane A7 lead)

- `exit:x1_hills` names X1's `entrance:xd05_mouth` (9216, 16384, 1376) facing south (A5 moved it in front of the mouth; the raw point was 259 farther south; `direction` dropped). Edited in L4 `project.yml` (gen.py is stale). `playtest.yml` asserts the landing and facing (measured (9216, 16384, 1377) facing 1536). A5 regenerates X1's walk.
- Built into `output/studio_cal/a7/s20/xd05/` with the oymap of merge point 27: BLV and scene byte for byte the installed ones (no rebake; stale bakes 0); the Lua differs by the way out only. Lua and studio file installed 06:51:18. Audit from `assets_dev` 0 errors, the 3 kept warnings (`output/studio_cal/a7/s20/audit/xd05.txt`). **12/12 from `assets_dev`** (playtest 112, back 49, hostility 30; `output/studio_cal/a7/s20/four_xd05.out`).

## Twenty-fourth session (2026-11-21, lane A7 lead)

- Arrival line (event 1, `evt:arrive`): "Mayor Gunther asked you to silence them." dropped (A3's answer in
  `devdocs/xeen/lanes/G.md` item 10: nobody gives the drum task; the drums belong to X1-TAM, Oslo's quest). The line
  now reads "... every night orc raiders fall on another farm. The drums are in these caves: burn all three (...), and
  look for Tam, Oslo's boy, ...". L4 `wiring.yml` by hand (gen.py stale since the twentieth session; its `WHY` and the
  last drum's fallback line changed to match, the latter now "Oslo will want to hear of it." as A3's hook says).
- Built with the oymap of merge point 31 (`output/studio_cal/a7/s24/xd05/`): BLV and scene byte for byte the installed
  ones, so only the Lua (that one line) and the studio file were installed (16:35:39); no rebake. Audit from
  `assets_dev` 0 errors, the 3 kept warnings.

## D-89 cave shape, identity and name test (2026-11-22, lane A7 28th-29th sessions)

Shared pass `tools/xeen/cave_shape.py` (corners cut where no other room, object or numbered wall is near, `rough` walls,
floor points that rise and fall with everything standing pinned level, vaulted roofs), called from this map's generator
after L4 is written; `identity:` in project.yml. Metrics are `oymap metrics`' cave_shape (floor uneven share, ceiling
spread, rough wall share; the audit's numbers 0.30 / 80 / 0.18). `tools/xeen/check_identity.py <key>` checks the family
share and the shape of the installed map.

- Metrics before -> after (floor / ceiling spread / rough): 0.27 / 357 / 0.13 -> 0.33 / 386 / 0.20; family d12 95 %.
- Spec `output/studio_cal/a7/s29/xd05_caves.py` (the L4 is the source; gen.py is stale). The drum hall stays as built
  (its rough wall blocked a terrace walk; its bowl is later polish, orchestrator), the bat chimney and back gate keep
  their walls (a rough back gate covers its wall torch: oymap hangs `wall:` torches on the plan's wall, audit
  `lights.in_solid`); the gate passage and the upper ledge (a path, `path_rough`) carry the rough share. 12/12.
- Name test (arrival, first fight room, signature room), engine captures from `assets_dev` in
  `output/studio_cal/a7/s29/names/xd05/shots/`  (01-1_arrival.png, 02-2_palisade.png, 03-3_cookfire.png,
  04-4_drum_hall.png); all eight maps on one sheet `output/studio_cal/a7/s29/names/names_sheet.jpg`. Reads as named: the
  skull-hung mouth facing the palisade and its gate, orc archers on the firing steps, the cookfire cave under its skull
  totems, the drum hall seen from its rim with the orcs among the drums.

## The mouth's exit hidden behind rough rock (2026-11-23, agent:xeen-xd05-exit)

A player on Discord: "How do I leave the Orc Dungeon without going to Mount Firestone? Or is this intended?"

- **Cause.** The mouth's south wall is `rough` (step 192, depth 48: the D-89 cave pass). The studio hangs an `exits:`
  object 2 in front of the plan's wall line (face at y 2), while a rough wall's joints stand 10-37 into the room
  (faces 409-414 at y 0..37), so the black exit face `exit:x1` lay wholly behind `gcav1flr` rock: no black face was
  seen and no click or interact reached event 18. The back gate (`exit:x7`, no rough walls) was the only working way
  out. Evidence: `output/xeen_xd05_exit/shots_before/` (turned back at the arrival, at the mouth's inner end and from the
  outer yard: plain rock), and the new scenario failing before the fix ("facing the mouth, interact found event 0").
  The playtests never saw it: they leave by `execute_event: {id: 18}`.
- **Fix.** `room:cave_mouth` has a `walls: south` panel (offset 96, length 1088, its own `gcav1flr`) behind the exit:
  the studio builds a panelled stretch of a rough wall flat, so the exit now stands in front of flat rock (L4 by hand;
  the generator is stale). The same rule is in `tools/xeen/cave_shape.py` (`flat_behind_panels`) for every map.
- **Check.** `tools/xeen/check_exits.py` `exits.hidden` / `switches.hidden` on the built map; `playtest_mouth.yml`
  (new): from the back gate's guardroom (drums burnt, bar lifted: a party that came in from X7) on foot to the mouth,
  the palisade gate opened from inside by interact, then facing the mouth interact runs event 18 and the party lands
  on X1 at `entrance:xd05_mouth`.
- Measurements: audit 0 errors, 25 of 25 sectors; `check_drops` the prisoner pit only (its ladder, as before); all four
  playtests pass from the private root and from `assets_dev`. Before/after pictures:
  `output/xeen_xd05_exit/before_after.jpg`.
- **REQUEST to A1 (studio), the fix at its root:** in `openyamm-studio/core/IndoorLowering.cpp`, where a rough wall's
  solid pieces are broken into joints (`roughParts`, "A panel is flat also on a rough wall": `solidPieces`), treat the
  stretch of every `m_panels` object hung on that wall (exits, switches, levers placed by `panelOnWall`, and `wall:`
  decorations/torches) like a `walls[].panels` stretch: cut the piece at the object's `low - 32` and `high + 32` and
  build that piece flat. Then `cave_shape.flat_behind_panels` is redundant (harmless) and torches no longer sink into
  rough rock (`lights.in_solid`). Add an `oymap audit` error when a clicked face has another face looking the same way
  within 64 in front of it over half its area (the rule of `check_exits.py` `exits.hidden`). MM6-MM9: no change to their built maps (only
  rooms with `rough` change; check the MM9 projects for any). Test: a unit test building a rough room with an exit on its wall
  and asserting no face between the exit and the room's centre.

## D-104 dungeon campfires (2026-11-26, agent:xeen-fb5-dungeon2)

`deco:cookfire`, `deco:den_fire`, `deco:hollows_fire`: the outdoor campfire's event (food 1-3 once, a small ring for a character with Perception), `once: true`, added by `level_generation/projects/xeen/common/campfires.py` (run once on the L4, which is the source here). Fixtures without a click: `deco:hall_fire`, `deco:hearth_fire`, `deco:yard_brazier`. First held back by two faults outside the map (a false `check_drops` pocket at (-2398, 5374) z -480 and a stale X1 arrival window); installed with D-195 below.

D-195 (2026-11-26, agent:xeen-p6-dungeon): installed with the three campfire events and baked. Neither fault was in the map: `check_drops.py` now reads a sloping floor's height at the point (the pit ladder's `top_exit` stands on a sloping triangle, mean -208, plane -224), so the prisoner pit is joined by its ladder (0 pockets); `playtest.yml` and `playtest_mouth.yml` assert X1's arrival at z 1200-1360 (X1's ground 1280 at `entrance:xd05_mouth` since 3.4, ± 80 as X1's own round trip), and `project.yml`'s `arrival_hint` says 1280.
