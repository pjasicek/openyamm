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
