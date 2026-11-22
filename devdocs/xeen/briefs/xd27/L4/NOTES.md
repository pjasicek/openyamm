# XD-27 Ogre Lair, L4: notes

Built 2026-11-15/16 with the Map Studio, one agent (key `xd27`), from this brief's L1-L3, under
`devdocs/xeen/ACT2_BUILD.md` and `devdocs/map_studio/REBUILD_PROCEDURE.md`. MM7 world as stand-in (as XD-01 to XD-05).
Map `xeen_xd27.blv`, map_stats 9138, qbits 110340-110341 (of 110340-110379), item 12170 (of 12170-12189).

State: `oymap validate` no issues (L1-L4); `fmt --check` clean; build warnings only the five placeholders, the placed
monsters' names (corpse only) and one liquid note (below); `audit`: 0 faces in one plane, 12 of 13 sectors on foot (the
13th is the gorge, a backdrop the party only falls into); `solve`: step 0 eleven sectors, step 1 the larder with the
Chieftain's key (`note: item 641 is carried by the monster Ogre Chieftain ... reached`), no dead handler. Playtests
four of four each, twice (`output/studio_cal/xd27/run/four_002750/` and, on the final build, `four_003356/`; after relinking to X2's final arrival, `four_010826/`; with merge 38's bolster row, engine sounds and `bands: false`, `four_015019/`; `four.out`): `playtest.yml` 91 steps, `playtest_fall.yml`
33 steps.

Scratch: `output/studio_cal/xd27/` (`tools/gen.py` + `tools/gen_objects.py` write L4's rooms/objects/wiring/project and
L3's rooms: **the project files are generated; edit the scripts and run `v.sh`**, not the YAML; `tools/make_l2.py`,
`tools/make_l3.py` wrote L2/L3's plan and project; `go.sh <playtest> <log>` builds, installs and plays one test;
`four.sh`; `tour.sh <shot list> <name>`; `tools/play_mount.py` merges this mount with X2's scratch build;
`root/` a private hard-link root (no longer used since merge 38: builds read `xeen_root` with `--mount`);
`mount/` the install; `mount_play/` mount + X2; `ref/` the shipped caves measured).

## What the party comes for (Q-C23)

Captain Nystor (X2) is losing boats to ogres who throw boulders from the river bluffs "because they like the sound of
crunching wood and screaming men". The lair is a brown beast cave in a river bluff west of the north river (X2's
door:xd27). On entering, a window quotes Nystor and says the Chieftain throws from a ledge high over the river. The
quest bit is `ogre_lair_destroyed` 110340, set at the Chieftain's seat after he is dead, with the source's own lines
("You have found an Ogre lair.  Destroy?" / "You break everything you can find in the lair."). Nystor's reward (the boat
route upriver) is X2's. A second bit, `ogre_boulders_dumped` 110341, is set when the party sends the ogres' boulder heap
into the river (optional; X2 may use it to clear the boulders at the crossings).

## Layout (13 rooms, 13 sectors, 19.5 M units² as `oymap metrics` measures)

| Room | M units² | What it is |
|---|---|---|
| Cave mouth | 1.19 | Arrival; daylight exit to X2 (south); the log gate in its north wall, barred from inside; the midden crack in its west wall. Safe |
| Midden crack | 0.83 | A fissure climbing 192 north-west, floored with the ogres' refuse; dogs |
| Bone den | 1.85 | Sleeping heaps of hides and bones; two ogre groups asleep; a bundle (chest) |
| Feast cave | 3.87 | Signature room: a round cave with the cooking pit sunk in its middle (fire, great cauldron), rock benches, bone heaps; the bone den's terrace and six steps; every way meets here |
| Gate yard | 1.22 | Behind the gate: the bar on two forked posts (lifted from inside only), the guards' fire |
| Kennel | 0.86 | Side cave behind a hurdle of stakes with a gap; dogs |
| Chieftain's den | 1.59 | One step up; his seat of boulders on a dais, oars and a sail of Nystor's boats as trophies; the larder's plank door |
| Chieftain's larder | 0.72 | Locked (his key); a meat beam, casks, sacks, a carcass on a spit stand, the boats' cargo: the hoard |
| Quarry ramp | 0.48 | Ramp up 384 |
| Boulder quarry | 2.03 | Rubble slope, boulder heaps, a campfire; ogres at work |
| Boulder chute | 0.60 | A plank trough with timber kerbs falling 256 east; the boulder trap halfway |
| Throwing ledge | 1.63 | Set piece: a shelf open east over the gorge (parapet 80); the Chieftain and three throwers; the boulder heap on a timber rack at the head of a slide cut south into the rock |
| River gorge | 1.54 | The view (backdrop): flowing water 448 below the ledge, the far cliff, the hills and the sky; a party that goes over the parapet falls in and is washed out at the mouth |

One loop: mouth, midden, bone den, feast cave, gate yard, gate, mouth (the gate opens once the bar is lifted inside).
Footprint 17 x 15 cells.

**Set piece (MAPS gives none):** the ogres' boulder works over the river: the quarry where they break the boulders,
the chute they roll them down, and the throwing ledge open over the gorge, where the heap waits on a timber rack. A
click on the rack knocks its cross-beam out; the heap (two movers) rolls into the slide and vanishes into the rock, the
cave shakes, a window says the river swallowed it. With the feast cave's cooking pit and the Chieftain's larder (MM8's
Cyclops Larder is the shipped model of a brute's larder of loot) it gives the lair three readable places.

## Monsters (MM7 stand-ins), levels 14-20 in the band 12-20

| Xeen | Stand-in | Level | Where |
|---|---|---|---|
| Ogres (slot 1, tier a) | MM6 Ogre (592, model mm6_ogr) | 15 | bone den x2, feast east, gate yard, quarry: groups of 2-3 |
| Ogres (slot 1, tier b) | MM6 Ogre Raider (593) | 20 | feast north: 2-3 |
| The ogres' dogs (slot 2, tier b) | MM8 Dire Wolf (86) | 14 | midden, kennel: 2-3 |
| The ogres' shamans (slot 3) | MM8 Ogre Mage Apprentice (106, Fire Bolt) | 20 | feast pit, Chieftain's den: 1-2 |
| Ogre Chieftain (placed) | Ogre Raider (593) named | 20 | the ledge; carries the larder key |
| Boulder Throwers (placed, 3) | Ogre (592) named | 15 | the ledge |

Measured at load (nine boots): 23, 28, 28, 27, 28, 25, 27, 27, 28 monsters (mean 26.8; MAPS 28, band 15-30); 10 spawn
points, 4 placed. Expected kill XP about 11,400, 2.85k per member (MAPS §0 2.5k, +14 %: more of the band's top than the
formula's A + 0.3 (C - A)). All draw as 3D models (the ogres with their swords, the wolves, the cloaked ogre mages). No
boss row (MAPS names none). Monster names show on corpses only (no `place_mon.txt` row).

## Loot and mechanisms

Map card: treasure level 2, lock 4, trap 2 (the MM8 Dire Wolf Den's 4/2), bolster LowerToEqual. Chests (MM8 `gt002`): bone den bundle (TL 2,
2 items, 150 gold), Chieftain's chest (TL 2, 3 items), larder strongbox (TL 3, the hoard one step up, 3 items, 800
gold), larder cargo chest (TL 2, 2 items, 300 gold). Experience events: Chieftain dead 500, rack 1,000, lair 2,000.

| Thing | Built as | Hover | Says when it cannot work |
|---|---|---|---|
| Log gate | hinged leaf of d08's planks; `side` events (mouth / gate yard) | Log gate | from the mouth: barred, and the reek from the crack in the west wall; from inside: lift the bar first |
| Gate bar | mover beam on two timber posts, rises 256 | Gate bar | a second click: the bar is up |
| Larder door | hinged leaf of d08's door planks (`t68a13mm`), needs item 641 | Larder door | the Chieftain keeps its key on his belt, on the ledge beyond the quarry |
| Boulder rack | mover cross-beam (drops) + two heap movers (roll 800 into the slide) | Boulder rack | a second click: broken, the boulders are in the river |
| Ogre lair | the seat (platform), question Yes/No | Ogre lair | while the Chieftain lives: break it now and his band piles it up again |
| Chute trap | invisible plate halfway down the chute: 30 damage, camera shake, status line; once | - | - |
| The fall | step on the gorge's water: 20 damage, teleport to the mouth; a timer then says what happened | - | - |

Clues before need: the arrival window (why, the Chieftain on a ledge over the river); the gate's message (the crack);
the midden's step line; the feast terrace line; the ledge's step line (the heap on its rack, the Chieftain); the
Chieftain's death line (the key on his belt); the larder door's message. No riddles: the only question is a yes/no.

## Measured against shipped S caves

| | XD-27 | d08 Dire Wolf Den | d43 Ancient Troll Home | d14 Cyclops Larder |
|---|---|---|---|---|
| Sectors (metrics) | 13 | 14 | 12 | 16 |
| Floor area, M units² | 19.5 | 14.7 | 17.7 | 19.6 |
| Spawn points / placed | 10 / 4 | 13 / 1 | 14 / 0 | 16 / 0 |
| Chests | 4 | 1 | 4 | 4 |
| Doors (with movers) | 6 | 1 | 0 | 10 |
| Loops | 1 | 0 | 0 | 1 |
| Upper-quarter room (scale_bands) | 1.75 M, pct 53 | 1.51 M, pct 46 | 1.72 M, pct 51 | 1.87 M, pct 57 |
| Largest room | 4.41 M, pct 35 | 2.89 M, pct 14 | 3.62 M, pct 22 | 4.93 M, pct 39 |
| Typical ceiling | 704, pct 83 | 802, pct 91 | 522, pct 50 | 778, pct 88 |
| Typical doorway | 384, pct 61 | 440 | 448 | 320 |

Inside S (at most 15 sectors and 20 M units²); main rooms at the shipped median (1.64 M) or above, nothing below the
shipped 25th percentile. Decorations: 94 (4.8 per M units²), more than MM8's caves carry (d43 2.3, d12 1.1), as XD-05.

## Textures

One family for the den and the works: **MM8 Dire Wolf Den (d08, a small brown beast cave)**: `gcav1wal` rock on walls
and roofs, `gcav1flr` floor, its timber `t68a10a` (planks, posts, the gate), `t68a11` (beams, the bars, the kerbs),
`t68a13mm` (its door's middle: the larder door), `t68a13a` (canvas: the sail), `gt002` chests. The gorge outside:
d08's rock as the cliffs, MM8's water `wtrtyl` (shader liquid, fluid bit), MM7's sky `7plansky1` as Celeste (7d25)
lays it indoors, and the Xeen hills picture `xodaylt` generated for XD-05 (its lower part, as the land beyond the
river; also the mouth's exit). `texture_use.py --project` flags none from no dungeon except `xodaylt` (generated).
XD-05 (also an orc/ogre cave) took MM8's Ogre Fortress (d12); this lair takes d08 so the two read apart.

Textures and models to generate (stand-ins now): a torn sail with a painted boat's eye (the den's trophy; now plain
canvas); a river-gorge panorama for the gorge's far wall (the far bank, the river bending away, hills; now XD-05's
meadow hills, whose path reads oddly as a far bank); a boulder-pile texture for the heap (now d08's floor rock at half
scale, which reads as grey blocks); models for the placeholders: spits over the pit, the boat's figurehead, hanging
carcasses, a log trough, a boulder sledge.

## Original lines (`reference/mm4_5_world_of_xeen/unpacked/text/xeen/aaze0010.txt.json`, Clouds C2)

- "You have found an Ogre lair.  Destroy?" (line 0): the seat's question.
- "You break everything you can find in the lair." (line 1): its answer.
- Captain Nystor: "Those Ogres are ruining me!  For months they have been throwing boulders at the boats that ply the
  waters around here.  Three of my ships have gone to the bottom in as many months because the Ogres like the sound of
  crunching wood and screaming men." (line 23): quoted in the arrival window.
- For X2's Nystor (not used here): "The Ogres aren't gone yet.  I think their base of operation is in the hills to the
  Southwest of here." (24) and "Thank you for getting rid of the Ogres.  Here is your reward." (25).

## Exit link

`exit:x2_hills` leads to `xeen_x2.odm` at X2's **final** outside arrival for door:xd27 (-20992, 17155, 1248), facing
south (270 / 1536), in front of X2's door at (-20992, 17555, 1216) (devdocs/xeen/briefs/x2/DOORS.md; relinked when X2
was finished, replacing the provisional (-20480, 17152, 1152)). **The link is final.** The playtest walks it onto X2's
final build (`output/studio_cal/x2/mount`, merged into `mount_play` by `tools/play_mount.py`, since the game takes one
`--extra-mount`) and asserts the position (radius 160, z 1150-1350). X2's door:xd27 needs no arrival of its own: this
map's start is (0, 448, 0) facing north.

## Words needed (and the workaround used)

1. **A boulder that rolls through rooms** (the chute trap, the heap into the river): a mover must stay in its room, so
   the trap is a step event (damage, shake, a status line) with no boulder seen, and the heap rolls into a slot in the
   ledge's own outline and into its end wall.
2. **Decorations riding a mover**: boulder models cannot stand on the heap, so the heap is two octagon blocks.
3. **A view out of a cave** (a backdrop word: sky, far bank, water as one panorama): the gorge is a room with bands
   (rock, hills, sky) and a sky roof; its corners show.
4. **A message after an in-map teleport**: the game closes the event window on a same-map MoveToMap
   (`closeTransientGameplayUiForMapMove`), so a message before the teleport is lost; the fall sets a variable and a
   timer says what happened.
5. **Living names for placed monsters** without editing `place_mon.txt` (the Ogre Chieftain shows as Ogre Raider).
6. ~~A bolster row~~: done with merge 38 (S8g): `map_stats.bolster: LowerToEqual`; the install writes row 9138 of
   `bolster_maps.txt` (`9138 Ogre Lair 2 LowerToEqual`).
7. ~~Engine sounds~~: done with merge 38: `rushing water loop` and `7campfire` come from `engine/audio`; the copies in
   the mount were removed, and `v.sh`/`go.sh` validate and build against `xeen_root` with `--mount`.

## Tool defects

- `fit: true` on an exit's surface tiles the picture 5 x 5 (face u 0-1280 on a 256-texel texture; XD-05's older build
  of the same surface has u 0-256). Worked round with `scale: 4`.
- (Fixed in merge 38) `walls[].surface` did not override the room's `bands`: the gorge's west wall now says
  `bands: false` (it was a full-length panel). `validate` and `build` now take `--mount` (the private `root/` is no
  longer used).
- Scenario: `assert: {map_transition_requested: ...}` records nothing for an event's MoveToMap (only boundaries and
  routes trace), so an exit to a map that is not installed cannot be checked by the request; `movement_segment` with
  `actor_ai: false` runs no floor events (the fall needs `actor_ai: true`); timer windows are not opened headless.
- The liquid note "1 of 2 faces with `liquid` or `flow` ... not found" names no face; the gorge's water face carries the
  fluid bit and the shader draws it.
- The tour's `actor kill <radius>` left some monsters standing in front of the camera (shots 11, 12, 16).

## Pictures (`output/studio_cal/xd27/shots/`, sheets `shots_s_1.jpg` to `shots_s_7.jpg`; `look4/` the gate and bar)

Looked at: the mouth with the daylight exit and the barred gate between skull piles and skull torches; the midden;
the bone den with sleepers and fire; the feast cave from the terrace (the pit, the cauldron, an ogre mage at it); the
gate and its bar before and after lifting (`look4/01`, `02`) and open from the mouth (`look4/03`); the kennel through
its hurdle; the Chieftain's den (seat, sail); the larder door and the larder inside (barrels, crate, the carcass on its
spit stand, the beam); the quarry; the chute with daylight at its end; the ledge with the Chieftain and the throwers
against the gorge; the rack and heap before and after; the water seen over the parapet. Judged: the den and the
works read as one warm brown beast cave; the ogres stand and fight as 3D models; the chute's daylight and the ledge
are the best moments. Weak: the gorge is a box (its corners and the hills picture's join show), the heap reads as grey
stone blocks rather than boulders, the sail as a plain sheet, the ledge's floor is pale in daylight.

## What the user should look at when playing

- The ledge and the gorge: does the view read as a river gorge, and is the parapet (80) low enough to look down at the
  water and high enough not to step over? A jump goes over it (into the river, washed out at the mouth).
- The barred gate and the midden crack: is the way in obvious from the gate's message?
- The heap and the rack: does knocking out the cross-beam read as the heap rolling away (it slides into the slot)?
- Fights: ogres 15 in groups of 2-3, Ogre Raiders 20 round the pit, Fire Bolt mages; a party of level 10-12.
- The Chieftain's seat after he is dead (Yes breaks the seat, oars and sail).

## Hostility pass (2026-11-16)

The user found monsters peaceful to the party beside hostile ones of their kind and monsters fighting each other
(devdocs/xeen/ACT2_BUILD.md, "Hostility pass"). MMerge's `hostile.txt` decides a slot monster's relation to the party
and two kinds' to each other; the studio now warns of both (`oymap build`) and the map says its relations in objects.yml
`relations` (the build's load event `evt:studio_relations`). Nothing to change: the Ogres, Dire Wolves and Ogre Mages
are the party's foes by the table and not set on each other. `playtest_hostility.yml` (written by
`output/studio_cal/hostility/gen_hostility_tests.py`) checks the slot and placed foes hostile, the peaceful ones
peaceful and the map's kinds, spawned side by side near the party, not taking each other on; it passes twice, as do the
map's other playtests.

## Rebase, phase 0 (lane A8, 2026-11-20): the design part

What the move into the Xeen world (ROADMAP §6 phase 0, A8 step 3) applies, decided now. Nothing is rebuilt yet: the
map already has its engine sounds and bolster row, and the rest needs A1's world install (W5), A2's rows and A3's hooks.

**Monsters (MAPS §0: 12–20, 28 monsters, 2.5k kill XP per member; MONSTERS_AND_ITEMS §2 Ogres 18/22/30, Wolves and
cats 16/22/28).** At the Xeen families' levels 28 monsters give 3.2k per member (+27 %), so the lair holds **22**
(S band 15–30): the feast cave's north marker and the bone den's east marker go, the gate yard's guards become dogs,
and slot 3 (the shamans) becomes the Ogres' B tier.

| Slot | Family, tier, level | Where | Expected |
|---|---|---|---|
| 1 | Ogres A 18 | den_w, feast_e, quarry ([2, 3]), plus the three placed Boulder Throwers | 10.5 |
| 2 | Wolves and cats A, Dark Wolf 16 (the ogres' dogs) | midden, kennel, yard ([2, 3]) | 7.5 |
| 3 | Ogres B 22 (the shamans by the cauldron and the Chieftain's) | feast_pit, chief ([1, 2]) | 3 |
| placed | **Ogre Chieftain 24, boss row** (×3 hit points, about 390), carries the larder key | the throwing ledge | 1 |

22 monsters, kill experience 11,300 for the party, **2.8k per member (+13 %)**; groups 2–3. MAPS §0's band says 12–20:
the Ogres' A tier is 18 and B 22, the Chieftain 24 (2.4 × the arriving party of 10, inside "bosses 2–3 ×").

**Treasure** stays: Tres 2; chests at 2, the larder strongbox (the hoard) at 3; lock 4, trap 2.

**Items and bits for A2 and A3:** the Chieftain's larder key 12170 (stand-in MM8 Ogre Key 641); qbits
`ogre_lair_destroyed` 110340 (Q-C23), `ogre_boulders_dumped` 110341 (optional; X2 may read it). The arrival window's
Nystor quote is quest text (A3's hook text replaces it).

**Original lines** (for A3's ledger; aaze0010, Clouds C2): "You have found an Ogre lair.  Destroy?" (0), "You break
everything you can find in the lair." (1), Captain Nystor's "Those Ogres are ruining me! ..." (23, the arrival window).

**Studio words since the build:** engine sounds (river, fire: in), bolster `LowerToEqual` (row 9138: in),
`walls[].bands: false` (the gorge's west wall: in). `no_spells`, doorway `floor`, model `turn` do not apply.

**Exit** checked against `briefs/x2/DOORS.md`: `exit:x2_hills` → `xeen_x2.odm` (-20992, 17155, 1248) facing south,
unchanged.

**Textures:** 14 distinct face textures in the build (S cap 30), none new (`xodaylt` is XD-05's).

## Into the world (lane A8, 2026-11-20)

The map now belongs to the Xeen world: `world: xeen`, installed as `assets_dev/worlds/xeen/maps/xeen_xd27.blv` (with
its `.scene.yml`, `.studio.yml` and `events/maps/xeen_xd27.lua`) by `oymap install --root assets_dev`. Its map_stats
(9138), bolster and slot rows are the world's (A2's `source/map_rows.yml`); project.yml repeats the slots. The sections
above that speak of MM7 stand-ins are the build's history.

**What changed** (in `output/studio_cal/xd27/tools/gen.py` and `gen_objects.py`, regenerated by `v.sh`):

| Thing | Before | Now |
|---|---|---|
| Slots | MM6 Ogre, MM8 Dire Wolf, MM8 Ogre Mage | `Xeen Ogre` (Dif 0), `Xeen Wolf` (0), `Xeen Ogre` (2), as map_rows.yml |
| Spawns | 10 markers | 8: den_e and feast_n gone; slot 1 tier a (Ogre 18, 11060) at den_w, feast_e, quarry; slot 2 tier a (Dark Wolf 16, 11410) at midden, kennel, yard; slot 3 tier b (Ogre Brute 22, 11061) at feast_pit, chief |
| Ogre Chieftain | Ogre Raider 593 with a name | boss row 11063 (level 24, 390 hit points), name kept, carries the larder key |
| Boulder Throwers | Ogre 592 | Ogre 11060, names kept |
| Larder key | MM8 Ogre Key 641 | the world's item 12170 |
| Quest bits | 110340, 110341 | unchanged, named as q-c23.yml (`ogre_lair_destroyed`, `ogre_boulders_dumped`) |
| Relations | none (hostile.txt) | objects.yml `relations`: ogres 11060-11064 at 4 (long), wolves 11410-11412 at 3 (medium) toward the party: the world's `relations.yml` levels restated, because the studio's hostility check reads only `engine/data_tables/hostile.txt` |

**A3's hooks** (`data_tables/quest_hooks.yml`, from `source/quests/q-c23.yml`), called from `lua:` effects (the studio has
no `hook:` word yet); the map's own text for those moments is gone:

| Event | Calls | What the hook does |
|---|---|---|
| `evt:arrive` (1, one-shot timer) | `XeenQuests.hook("q-c23.arrival")` | the arrival window (replaces the Nystor quote) |
| `evt:rack` (18) | `q-c23.rack` in effects and in else_effects | sets `ogre_boulders_dumped` and says so; a second click says "An empty rack." (the map keeps the movers, shake and 1,000 experience) |
| `evt:lair` (14) | `q-c23.chieftain` after the Yes | sets `ogre_lair_destroyed` and says "You break everything you can find in the lair." (the map keeps the source's question, the 2,000 experience and the seat, oars and sail coming down) |

Map-local lines stay (gate, bar, larder door, step lines, the fall, the Chieftain's death line).

**Monsters at load** (six boots, `output/studio_cal/xd27/xrun/probe/counts.txt`): 22, 22, 21, 22, 24, 22 (mean 22.2;
design 22, S band 15-30). Per kind (separate boots): Ogre 10.8 (with the three throwers), Ogre Brute 3.0, Dark Wolf 7.2,
the Chieftain 1. Kill experience (monster_data XP: 504, 704, 416, 816): 10.8 x 504 + 3.0 x 704 + 7.2 x 416 + 816 =
about 11,370 for the party, **2.84k per member against MAPS §0's 2.5k (+14 %)**, as the design's +13 %.

**Dressing** (the user's rule of 2026-11-20, `formats/DRESSING.md`). Checked every decoration and the furniture
platforms: containers with A7's measure (`tools/measure_xd27.py`, a copy of `output/studio_cal/a7/dressing/measure.py`
that maps a studio build's entity ids to their decorations, since the original keys on decoration names and finds none
in a studio map), every floor prop against the walking lines of its room (`tools/walk_lines.py`: lines between the
room's openings, the start, the chests, the seat and the rack; the prop's radius + 64; lines across the cooking pit left
out), and the pictures.

- Before (`dress_before.txt`): 4 of 14 containers broke the numbers (feast barrel 115 from the ramp's doorway, the
  feast cask and keg 187 and 144 from the kennel's, larder barrel 288 from the larder door's portal); 28 props stood
  on walking lines (`walk_before.txt`): the mouth's west skull pile, west torch, two bones and the drowned boatman in
  the triangle start / crack / gate; all six midden props on the fissure's centreline; the bone den's keg, a bed heap
  and two bones; the feast cave's barrel, keg, ramp torch and a bones; the Chieftain's two skull piles and two torches
  across the line to the larder door; the larder's barrel and carcass on the lines to its chests; the ramp's bones and
  rock; a quarry rock; and the larder's wall torch hung in the doorway itself.
- Moved: all of those, to the walls and corners (midden props 130-145 off the centreline, the boatman and bones to the
  mouth's east side, the skull pile and torch to its south-west corner by the daylight; the feast barrel and cask as a
  pair against the north-east wall, the keg alone by the south-west wall; the Chieftain's torches onto the dais beside
  the seat, his skull piles behind it; the larder torch to the east wall north of the door, its barrel to the north
  side, the carcass under the west end of the meat beam). Furniture: the feast cave's south and north benches
  shortened from 512 to 320 so the lines gate yard → Chieftain's den and steps / kennel → ramp pass clear. Nothing
  removed. Pictures after the moves: `output/studio_cal/xd27/xshots2/` (sheets `xshots2_s_1.jpg`, `_s_2.jpg`; tour
  `tools/shots_x2.py`): every moved prop against its wall, the doorways and lanes clear.
- After (`dress_after.txt`, `tools/walk_lines.py` 0 offenders): containers 0 of 14 offending; barrels to wall median
  96 (max 215), to a portal min 343, to a door face min 345; groups: 7 singles and 2 pairs, the larder (a storeroom)
  holds 4 barrels, 1 cask and 3 sacks along its walls.

**Checks** (all on `openyamm-studio/build-xeen/oymap`; validate and build against `output/studio_cal/xd27/xroot`, see
the tool defects):

- `validate` L3 and L4: no issues (`v.sh`). `fmt --check`: clean.
- `build` (`xbuild.log`): the five placeholders, the four placed monsters' names (corpse only), the liquid note (all
  known), and two new: "evt:rack ... does nothing the player sees" and "nothing tells the player on arrival why he is
  here", both because the studio does not see a message inside a `lua:` hook call. No hostility warnings.
- `audit --reach --solve` on the installed map with `--assets assets_dev` (`xaudit.txt`, `xsolve.txt`): 0 faces in one
  plane, 11 of 13 sectors on foot as the doors start, 12 with every door out of the way (the gorge, sector 6, the
  backdrop); solve step 1 the larder by `item 12170`, "carried by the monster Ogre Chieftain ... reached"; exit
  `xeen_x2.odm at -20992, 17155, 1248` direction 1536; no dead handler (`state.never_read` for map_var 8, the falls
  counter, is information only).
- Playtests 4 of 4 each, one game at a time, from `assets_dev` with `--world xeen --map xeen_xd27.blv`
  (`xfour.sh`, `xfour.out`, logs `xrun/four_<time>/`): `playtest.yml` 101 steps, `playtest_fall.yml` 33,
  `playtest_hostility.yml` 26; again after the dressing moves (`xrun/four_131955/`).
  - `playtest.yml` now asserts the Xeen rows at load (one 11063, three or more 11060, Dark Wolves, Ogre Brutes, no
    592/593/86/106), the three hooks' windows by their text (`assert: {dialog: {text_contains}}`; the arrival's opens
    with `advance_runtime: {present_dialogs: true}`), both quest bits, the key 12170 from the Chieftain's corpse, and
    ends at the exit's question "Do you wish to leave Ogre Lair?".
  - `playtest_hostility.yml` checks 11060-11063 and 11410-11412: none peaceful, 11060, 11061, 11063 and 11410 hostile;
    Ogre, Dark Wolf and Ogre Brute spawned side by side do not take each other on.
- Pictures (`output/studio_cal/xd27/xshots/`, sheets `xshots_s_1.jpg`, `xshots_s_2.jpg`; tour `tools/shots_x.py`, the
  wrapper with `--binary build-xeen/game/openyamm`): ogres, Ogre Brutes, Dark Wolves and the Chieftain draw as 3D models
  (the ogres with mm6_ogr, the wolves the MM8 wolf), the exit's hills picture (`xodaylt`, now in the world's
  `textures_x2`/`textures_x4`), the gorge's sky, water and hills, every decoration and the heap. Wrong as before: the
  Chieftain looks like his ogres (A2's rows share the model; data, not this map's), the gorge's corners show, the heap
  reads as grey blocks, the sail as a plain sheet, `actor kill` in a tour leaves an ogre standing (shot 13).

**Not tested, and why:**

- **The way out onto X2.** X2 is not installed in the Xeen world (A5's). Confirming the exit makes the runner load
  `xeen_x2.odm`, which fails ("Failed to load initial map asset for xeen_x2.odm"; `select_topic` always follows the
  move, so no assert after it runs). The playtest ends at the exit's question; the destination is checked only
  statically (`solve`'s exit line, the generated `evt.MoveToMap` in `events/maps/xeen_xd27.lua`). When X2 is in the
  world: restore the old ending (`select_topic: OK`, `advance_runtime: {follow_map_move: true}`, `assert: {map:
  xeen_x2.odm}`, the party position radius 160, z 1150-1350).
- **A new Xeen game from the start.** The world's start map `xeen_x1.odm` is not installed either, and a new game loads
  it before the scenario's `start_map` ("Failed to load initial map asset for xeen_x1.odm", "could not load headless
  gameplay data"). Every run passes the game's own `--map xeen_xd27.blv`, which makes the lair the initial map; no
  extra mount, no copied maps.
- The arrival window is seen headless now (`present_dialogs`), but the build still warns of it (above).

**Tool and world defects found:**

1. The indoor `oymap validate`/`build` read monster rows and items only from `engine/data_tables/` (no world
   `tableContributions`; the outdoor build uses `readWorldTable`): `oymap validate devdocs/xeen/briefs/xd27/L4 --assets
   assets_dev` gives "there is no monster number 11063 in monster_data.txt" (and 11060, and item 12170). Worked round
   as A7 did for XD-05: `output/studio_cal/xd27/xroot` (`cp -al assets_dev`, then `tools/mk_studio_root.py` writes the
   engine monster_data, monster_descriptors and items with the world's rows appended as new files); the built map is
   the same. Remake the root after A2 regenerates the tables (the root's world files are hard links, the generator
   replaces them). For A1.
2. The studio's hostility check reads only `hostile.txt`, not the world's `relations.yml`, so a Xeen slot warns as
   "friendly to the party"; the map restates the world's levels in `relations` (above). For A1.
3. The studio does not count a `lua:` hook call as something the player sees (two build warnings above); a `hook:`
   word (QUESTS_FORMAT §7) would let it. For A1.
4. `tools/run_game.sh --isolated` uses `build/game/openyamm`, which cannot resolve a `worlds/xeen` map ("cannot resolve
   map world for xeen_xd27.blv"); pass `--binary $PWD/build-xeen/game/openyamm`.
5. A7's `output/studio_cal/a7/dressing/measure.py` finds no props in a studio-built map (entities carry the object id,
   not the decoration name); `tools/measure_xd27.py --objects <objects.yml>` maps them. For A7.

**Recipe for the next maps (XD-06, XD-12)**, from this move:

1. Generators: `world: xeen`; `map_stats.slots` with map_rows.yml's slot names (`Xeen <Family>`, the family's slot
   name from A2.md's table) and its tiers; each spawn's `tier` letter picks the row (a/b/c = the family's A/B/C ids);
   placed monsters by row id (boss rows), keep `name`, drop `hp`; `items:` the world's ids; qbits as the quest files
   name them.
2. Hooks: for each `quest_hooks.yml` hook on the map with `call:`, an effect `{lua: 'XeenQuests.hook("<name>")'}` in
   the event, with the map's own text for that moment removed; a once-hook's second click calls it again from
   `else_effects` for its else text.
3. Relations: restate `relations.yml`'s levels for the map's families toward the party (numbers 0-4; long 4, medium 3)
   so the build is quiet; add a feud row only if the world sets one.
4. Check root: `cp -al assets_dev output/studio_cal/<key>/xroot` and `tools/mk_studio_root.py` (copy XD-27's);
   `validate` and `build --assets <xroot> --out <work>/build`; `oymap install <L4> --build <work>/build --root
   assets_dev`; `audit --reach`/`solve` on `assets_dev/worlds/xeen/maps/<stem>.blv --world xeen --assets assets_dev`.
5. Playtests: `world: xeen`; run with `build-xeen/game/openyamm --asset-root assets_dev --world xeen --map <stem>
   --user-data <scratch> --headless-run-scenario ...` (copy `xfour.sh`); stand-in ids replaced by the rows; hook windows
   asserted with `assert: {dialog: {active: true, text_contains: ...}}` (`advance_runtime: {present_dialogs: true}` for
   a timer's window); an exit onto a map not yet in the world ends at its question. XD-12's cloud stair stays sealed.
6. Dressing: `measure_xd27.py <export> --objects <objects.yml>` for containers and a `walk_lines.py` with the map's
   own lines; move offenders in the generators; playtests again.
7. Tour: `./tools/run_game.sh --isolated <name> --binary $PWD/build-xeen/game/openyamm --world xeen --map <stem>
   --assets $PWD/assets_dev --set debug.screenshot_tour_path=<abs tour.yml>`.

## Exit onto X2 and merge point 3 (lane A8, 2026-11-20)

X2 is in the world (A5) and build-xeen's binaries are A1's merge point 3. This replaces "Not tested" above, tool
defects 1 and 2 of "Into the world", and steps 3 and 4 of its recipe (no relations restated, no check root).

- **Doors:** A5's rebased X2 build (`output/studio_cal/x2/build_w`, `tools/doors.py`) still puts door:xd27's mouth at
  -20992, 17555, 1216 and the outside arrival at **-20992, 17155, 1248** facing south, as DOORS.md. The map's exit
  needed no change.
- **Studio against assets_dev** (no check root): `validate` L3 and L4 no issues (`validate_assets.txt`); `build`
  byte-identical to the `xroot` build. Then `relations` dropped from `tools/gen_objects.py` (they only restated the
  world's `relations.yml`): `v.sh` regenerates L3/L4 with `objects.yml` changed only there (`oymap record`, entry 3,
  "relations dropped", revision `d57e9a425a70442eac81c0381af947a9`); `build` (`build_assets.txt`) 13 rooms, 876 faces,
  6 doors, 8 spawns, **19 events** (the `evt:studio_relations` load handler gone), 4 chests; no hostility warning; the
  same known warnings as `xbuild.log` (five placeholders, four placed names, `evt:rack`, arrival message, liquid). The
  blv, scene and walk unchanged, the Lua changed, so reinstalled (`oymap install --root assets_dev`: the blv,
  `.scene.yml`, `.studio.yml` and `events/maps/xeen_xd27.lua`). `audit --world xeen --reach --solve`
  (`audit_mp3.txt`) as `xaudit.txt` but for the handler count; `solve` (`solve_mp3.txt`) identical to `xsolve.txt`:
  exit `xeen_x2.odm at -20992, 17155, 1248` (1536). `fmt --check` L3, L4 clean.
- **Check root dropped:** `v.sh` uses `--assets assets_dev`; `output/studio_cal/xd27/xroot` deleted
  (`tools/mk_studio_root.py` no longer called).
- **Exit:** `playtest.yml` (107 steps) now takes the exit's OK at the mouth, asserts `map: xeen_x2.odm` and the party
  within 160 of (-20992, 17155) at z 1150-1350, and walks 455 south down the bluff.
- **Way in:** `playtest_in.yml` (9 steps, new): a new game on X2 (`--map xeen_x2.odm`), set down 280 in front of the
  cave mouth facing it; "Enter the Ogre Lair" (open, no bit or item) leads to `xeen_xd27.blv` at its start (asserted
  within 128 of 0, 448).
- **Runs** (`xfour.sh`, `xfour_mp3.out`, logs `xrun/four_135548/`), one game at a time, `build-xeen/game/openyamm
  --asset-root assets_dev --world xeen`: `playtest.yml` 107 of 107 **4 of 4**, `playtest_fall.yml` 33 of 33 **4 of 4**,
  `playtest_hostility.yml` 26 of 26 **4 of 4** (now on the world's `relations.yml` alone), `playtest_in.yml` 9 of 9
  **4 of 4**.


## Hooks and dressing, D-7 (2026-11-20)

Touch-up by `agent:xeen-a8-touchup` (lane A8). Changes in `output/studio_cal/xd27/tools/gen_objects.py` and `gen.py`
(copies before: `gen_objects_before_d7.py`, `gen_before_d7.py`). The generator reproduced L3 and L4 byte for byte before the
change. `v.sh`, `oymap record --author agent:xeen-a8-touchup`: L4 "first-arrival window, D-7 dressing" (revision
`20f44e2a2e9c86a4855beef7aed1ecae`), L3 "the larder a storeroom (D-7)" (`d420297120f87dd7a4f462532c89aca7`). L3's record also
picked up two earlier unrecorded generator changes, `room:feast_cave` platforms and `room:gorge` walls (a previous `v.sh` run;
L3's files did not change in this run beyond `store`). Built to `output/studio_cal/xd27/build_d7` and installed with
`--root assets_dev` (the map's four files; the world's data_tables hashes unchanged).

- **First arrival only:** `evt:arrive` now has `condition: {not: {qbit: arrived_once}}` and sets `arrived_once`
  **110342** (free in 110340-110379) after `q-c23.arrival`. The window had opened on every entry. **For A3:** register it in
  q-c23.yml (`tools/xeen/quests.py` reports "XD-27: built qbit arrived_once (110342) is in no quest file").
- **Dressing:** `oymap audit --world xeen` before **1 error / 1 warning**: `midden_skull` 49 from the walking line of
  the midden crack (sector 9), and a clump of 4 containers in the larder (sector 8). Fixes: the larder is the Chieftain's
  storeroom, so `rooms.yml` `room:larder` has `store: true` (gen.py; L3 and L4). The skull went to (-1964, 1624) by the
  crack's west wall (a first try at (-1936, 1712) gave `thing.in_doorway` before the bone den's opening). After: **0 / 0**,
  and no `thing.in_doorway`. No "Dressing exceptions" are needed.
- **Checks** (`output/studio_cal/xd27/`): `validate` L3/L4 no issues; `fmt --check` clean; `build`: 13 rooms, 876 faces,
  6 doors, 8 spawns, 19 events, 4 chests, with the known warnings. The arrival warning is now there because the studio skips a
  conditioned timer, a defect for A1 (see XD-12's notes). `audit --reach --solve` (`audit_d7.txt`): 0 faces in one plane, 11/12 of
  13 sectors, no findings. `solve_d7.txt` is identical to `solve_mp3.txt`.
- **Playtests** (unchanged files; from assets_dev in the Xeen world, one game at a time, `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/f070ad2b-085f-4ea8-986a-1b63e2657a52/scratchpad/d7/play_once.sh`, logs
  `/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/f070ad2b-085f-4ea8-986a-1b63e2657a52/scratchpad/d7/run/`): `playtest.yml` 107 of 107, `playtest_fall.yml` 33 of 33, `playtest_hostility.yml` 26 of 26,
  `playtest_in.yml` 9 of 9, **each 1 of 1** (the orchestrator's handover stopped the work before the 4 of 4).

**Still open, next steps:** (1) `output/studio_cal/xd27/xfour.sh` for **4 of 4** of all four playtests. (2) A re-entry
step proving the window shows only once: in `playtest_in.yml`, after entering, leave by the mouth (OK, follow the
move to X2), enter again, `advance_runtime: {seconds: 3, present_dialogs: true}`, `assert: {dialog: {active: false}}`.
(3) A picture of the skull's new place in the midden crack (not taken). (4) A3: register 110342.

## Session 3 (2026-11-20): 4 of 4, re-entry, picture

Lane A8. `oymap audit <stem> --world xeen --assets assets_dev` (studio merge point 7) on the installed map: no dressing finding. A3 has registered `arrived_once` 110342 in q-c23.yml. Next steps (1)-(3) of the D-7 section are done.

- **Re-entry step** in `playtest_in.yml`: the window ("The ogres' lair, in the river bluff.") shows once and sets
  110342; the party leaves by the mouth (event 8, OK), comes back through X2's door, and no window opens. 25 steps.
- **4 of 4** from assets_dev (`xfour.sh`, logs `output/studio_cal/xd27/xrun/four_152006/`): `playtest.yml` 107,
  `playtest_fall.yml` 33, `playtest_hostility.yml` 26, `playtest_in.yml` 25 steps, each 4 of 4.
- **Picture** (`/home/pjasicek/github/OpenYAMM/output/studio_cal/a8_s3/props/xd27_sheet.jpg`): the skull lies against the midden crack's west wall, off the walk to the
  bone den.

## Light audit (merge point 14)

By `agent:xeen-a8-lights` (lane A8), 2026-11-20, on A1's light-fixture audit (`devdocs/xeen/formats/LIGHTS.md`,
`output/xeen_a1/lights_xeen.txt`). Changed in the generator (`output/studio_cal/xd27/tools/gen_objects.py`, copy before
the change `gen_objects_before_lights.py`; the generator reproduced the project byte for byte first), L4 regenerated,
`oymap fmt`, `oymap record --author agent:xeen-a8-lights --label "lights audit (merge point 14)"`.

- MM6's skull torch (`torskul0`) is a wall fixture; all eleven stood on the floor (six away from any wall, drawn as the
  free model). Each now hangs on the nearest wall of its old place, 160 over the floor (`wall` = outline edge, `along`):
  mouth 2, feast cave 3, Chieftain's den 2 (on the north wall behind the seat, either side), quarry 2, throwing ledge 2.
  The cave walls are rough (faces bulge up to 40 in or out mid-edge), so each `along` was tried against `oymap audit
  --lights-measure` and kept where the wall lies 0-18 from the torch's middle.
- The quarry's first torch first went over the rubble slope against the north-west wall, its bracket buried in the
  rubble (seen in the pictures): moved east of the slope (edge 6 at 0.15), rebuilt, re-baked and retested.

- **Audit** (`oymap audit --reach --solve` on the installed map, `output/studio_cal/xd27/audit_lights.txt`): lights
  errors/warnings before **7/11 (7 wall_missing, 11 wall_height)**, after **0/0**; no dressing finding. **Light
  exceptions:** none.
- **Installed** by `INSTALL=1 output/studio_cal/a8_s5/rebuild.sh xd27` (build `output/studio_cal/xd27/b_195746`), baked
  (`output/studio_cal/a8_s5/bake.sh xd27 assets_dev`, profile `tools/lighting/baked_indoors/profiles/xeen_xd27.yml`
  (new: XD-08's values)), `tools/lighting/stale_bakes.py --check` lists none of the lane's maps. **Playtests from
  assets_dev, each 4 of 4** (`xfour.sh`, on the final build; record `output/studio_cal/xd27/lights_post2.out`; the first
  build's run `lights_post.out` passed too): playtest 4/4 (107 steps); playtest_fall 4/4 (33 steps); playtest_hostility
  4/4 (26 steps); playtest_in 4/4 (25 steps).
- **Pictures** `output/studio_cal/xd27/shots/lights_mp14/` (sheets `lights_mp14_sheet_1.jpg`, `_2.jpg`) and
  `lights_mp14_c/` (the quarry's first torch after its move), looked at: all eleven skull torches on the cave walls,
  brackets showing, about head height.

## Session 7 batch (texture fit: the gorge's far view, merge points 16 and 17)

By `agent:xeen-a8-xd27` (lane A8). Changed in `output/studio_cal/xd27/tools/gen.py` only (copy before:
`gen_before_s7.py`; the unchanged generators reproduced the installed L4 byte for byte first). `v.sh`, `oymap fmt`,
`oymap record` entries 7 and 8 (revision `b6c6a1a8ac0d8d6b0927ecb30455d473`).

- **What was wrong:** the gorge's middle band laid `xodaylt` (A6's hills picture, `kind: picture`, 256 x 128) at scale
  8.2 round three far walls in different planes (960, 1600, 960 x 704): the picture cut over each (45, 66, 45 %), the
  box's corners showing through the view (3 `feature_cut` errors).
- **Now:** the gorge has no bands. North, south and west walls are d08's rock from the water to the roof (cliffs either
  side of the view); the east (far) wall is rock up to 552 above the water (the far cliff, its top about 100 over the
  ledge's floor) with one wall panel over its whole length: `xodaylt` once across (scale 6.25: 256 texels over 1,600)
  at its own proportions, its lower three quarters (rows 32-128, 600 high: the hills, the path, the rocks; the pale sky
  above them left out). The roof came down from 1408 to 832 so the picture meets the sky roof at the corner (the
  opening's top is 808). A first try laid the whole picture stretched once (`fit`, 1600 x 800): its own pale sky showed
  as a white field under the blue roof (`shots/s7/`), so it is cropped. `uneven: true` on the surface: the build
  otherwise warns of a picture at 0.16 of its density (a backdrop stretched on purpose). Sizes: `xodaylt` [256, 128]
  everywhere (the gorge and the exit), so no merge-17 warning; the build log (`b_221843.build.log`) has only the known
  12 warnings (placeholders, placed names, two corpse `facing`s, liquid).
- **Audit** (`oymap audit --reach --solve`, `audit_s7.txt`): before 3 errors, 4 warnings (`audit0/xd27.txt`); after
  **0 errors, 2 warnings**, both kept below. Face 380 measures `copies 1 x 0.75 whole 1 x 0.74`. Reach and solve as
  before (11/12 of 13 sectors; the gorge is the backdrop).
- **Installed** (`INSTALL=1 rebuild.sh xd27`, build `b_221843`), baked straight after, `stale_bakes.py`: none of the
  lane's maps. **Playtests from assets_dev, each 4 of 4** (`s7_post.out`, logs `xrun/four_222010/`): playtest 107
  steps, playtest_fall 33, playtest_hostility 26, playtest_in 25. (The `fit` try passed 4 of 4 too: `four_221334/`.)
- **Pictures** `output/studio_cal/xd27/shots/s7b/` (sheet `shots/s7b_sheet.jpg`; before: `xshots/12-12-ledge-gorge-view.png`):
  from the back of the ledge, the parapet (down and up), both ends of the ledge and the chute's end: one view of the
  hills framed by rock cliffs, the sky roof above; a thin pale haze strip at the picture's top meets the blue roof.
  Still weak: the gorge stays a box seen from close by, the haze/roof line; `actor kill` left ogres standing.
- **For A6:** a river-gorge panorama for indoor gorges (the far bank, the river bending away, hills; sky that meets
  `7plansky1` or none at the top), as asked in "Textures" above; `xodaylt` is XD-05's meadow with a path.

## Session 8: A6's river-gorge panorama

Lane lead (A8 session 8). `tools/gen.py` (copy before: `gen_before_s8.py`; the unchanged generators reproduced L3/L4
byte for byte, snapshot `output/studio_cal/xd27/s8_snap/`): the gorge's far-wall panel (1600 x 600) now lays A6's
`xogorge` (512 x 256) once (`fit: true`, `uneven: true`), in place of `xodaylt` at scale 6.25 offset [0, 32]; the exit
keeps `xodaylt`. Audit (oymap 23:02:35, `audit_s8.txt`): 0 errors, 1 warning (face 68/713 below; face 380's
`feature_border` is gone); face 380 measures copies 1 x 1, whole 1 x 1. Recorded (`a53103fd`), installed
(`b_230930`, 12 known build warnings, no size warning), baked 23:1x, `stale_bakes` none. **Not yet done:** the tour
(`output/studio_cal/a8_s8/tour_xd27.yml`) and the tests 4 of 4 from assets_dev (`a8_s8/queue_polish1.sh`).

**Session 9 (lane lead):** done. Tour `output/studio_cal/xd27/shots/s8/` (3 shots; sheet `output/studio_cal/a8_s9/
xd27_s8.jpg`): the panorama reads once, whole, as a river gorge beyond the rock rim. Tests from assets_dev 4 of 4
(playtest 107, playtest_fall 33, playtest_hostility 26, playtest_in 25 steps; `output/studio_cal/xd27/xrun/four_232539`).

### Texture fit exceptions

- `textures.feature_border` face 380 (`xodaylt` over `gcav1wal`, 109 apart): the far cliff's top edge against the
  hills beyond the river; a cliff against a far view is meant to stand apart.
- `textures.family_switch` face 68 (`gcav1wal`) and 713 (`t68a13a`, 109 apart): the torn sail (canvas, a wall panel)
  hung as a trophy on the Chieftain's rock wall; it is meant to read apart (a painted sail picture is a stand-in
  request above).

## Session 26 (A8): status lines in the playtest

No map change. `playtest.yml`: the boulder rack (`q-c23.rack`, step 64) and the Chieftain's den (`q-c23.chieftain`,
step 83) now show their texts on the status line (D-90); the steps that required a window to close (`if not close()
then error`) are gone, the status checks before them stay. Tests 16 of 16 from assets_dev
(`output/studio_cal/a8_s26/run/xd27/t004827`); the check build matched assets_dev (audit 0 / 1, check_exits 0,
check_drops 0).
