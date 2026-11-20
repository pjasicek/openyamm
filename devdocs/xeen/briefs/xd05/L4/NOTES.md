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
- **Why here**: one-shot arrival message (Mayor Gunther, the three drums and where, Tam).

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
